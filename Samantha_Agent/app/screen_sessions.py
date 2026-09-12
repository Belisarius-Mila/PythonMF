"""List owned GNU screen sessions and close only a freshly confirmed identity."""

from datetime import datetime, timezone
import hashlib
import hmac
from pathlib import Path
import pwd
import re
import signal
import subprocess
import time

from app.codex_sessions import CodexSessionController
from scripts.codex_session_report import format_age


def parse_screen_list(output):
    rows = []
    for line in output.splitlines():
        match = re.fullmatch(r"\s*(\d+)\.([^\s/]+)\s+(?:\([^\n]*\)\s+)?\((Attached|Detached)\)\s*", line)
        if match:
            pid, name, state = match.groups()
            rows.append({"pid": int(pid), "name": name, "socket": f"{pid}.{name}", "state": state})
    return rows


def read_screen_sessions():
    result = subprocess.run(["/usr/bin/screen", "-ls"], capture_output=True, text=True, timeout=4)
    rows = parse_screen_list(result.stdout)
    if not rows and not (result.returncode == 0 or "No Sockets found" in result.stdout):
        raise OSError("Screen inventory unavailable")
    return rows


def quit_screen(socket):
    return subprocess.run(["/usr/bin/screen", "-S", socket, "-X", "quit"],
                          capture_output=True, timeout=3, check=False)


class ScreenSessionController(CodexSessionController):
    def __init__(self, *, screens=read_screen_sessions, quit_session=quit_screen, username=None, **kwargs):
        super().__init__(**kwargs)
        self.screens, self.quit_session = screens, quit_session
        self.username = pwd.getpwuid(self.uid).pw_name if username is None else username

    def _owned_login_wrapper(self, child, screen_pid):
        # macOS screen launches /usr/bin/login as root for this user's PTY.
        # This is not permission to terminate arbitrary root descendants.
        return (child.uid == 0 and child.ppid == screen_pid
                and bool(child.argv) and Path(child.argv[0]).name == "login"
                and child.argv[1:3] == ["-pflq", self.username]
                and self.executable(child.pid) in ("login", "/usr/bin/login"))

    @staticmethod
    def _descendants(pid, processes):
        ids = {pid}
        while True:
            updated = ids | {p.pid for p in processes if p.ppid in ids}
            if updated == ids:
                return [p for p in processes if p.pid in ids and p.pid != pid]
            ids = updated

    def _screen_row(self, screen, p, processes):
        children = self._descendants(p.pid, processes)
        cwd, executable = self.cwd(p.pid), self.executable(p.pid)
        in_project = bool(cwd and Path(cwd).resolve().is_relative_to(self.root))
        labels = self.labels()
        reason = ""
        if not p.argv or Path(p.argv[0]).name.lower() != "screen" or Path(executable).name.lower() != "screen":
            reason = "Proces screenu není ověřený."
        elif p.uid != self.uid:
            reason = "Screen patří jinému uživateli."
        elif p.pid in self._ancestors(processes):
            reason = "Screen obsahuje tohoto správce; je chráněný."
        elif any(c.is_codex for c in children):
            reason = "Uvnitř běží Codex nebo jeho služba. Nejprve ukonči příslušný Codex."
        elif any((c.uid != self.uid and not self._owned_login_wrapper(c, p.pid))
                 or labels.get(c.tty, {}).get("protected")
                 or any(Path(a).name in ("cockpit_server.py", "cockpit_launchd_runner.py") for a in c.argv)
                 for c in [p, *children]):
            reason = "Screen obsahuje chráněný proces nebo službu."
        elif not in_project:
            reason = "Pracovní adresář screenu není ověřený v PythonMF."
        # Bind the entire observed membership, not only a reusable PID or name.
        members = sorted((c.pid, c.ppid, c.uid, c.tty, c.started, c.command) for c in children)
        identity = repr((screen, p.pid, p.ppid, p.uid, p.tty, p.started, p.command, cwd, executable, members))
        token = hmac.new(self._key, identity.encode(), hashlib.sha256).hexdigest()
        return {"pid": p.pid, "name": screen["name"], "socket": screen["socket"],
                "state": screen["state"], "started": p.started, "age": format_age(p.age),
                "process_count": len(children), "codex_count": sum(c.is_terminal for c in children),
                "project": "PythonMF" if in_project else "Neověřený / jiný adresář",
                "can_stop": not reason, "protected_reason": reason, "identity": token,
                "force_available": token in self._stopping}

    def status(self):
        try:
            processes = self.processes()
            by_pid = {p.pid: p for p in processes}
            sessions = [self._screen_row(s, by_pid[s["pid"]], processes) for s in self.screens()
                        if s["pid"] in by_pid and by_pid[s["pid"]].uid == self.uid]
            return {"ok": True, "generated_at": datetime.now(timezone.utc).isoformat(), "sessions": sessions}
        except (OSError, ValueError, subprocess.SubprocessError):
            return {"ok": False, "sessions": [], "message": "Přehled screenů nelze ověřit. Obnov jej."}

    def stop(self, payload):
        if payload.get("confirmed") is not True:
            return {"ok": False, "message": "Uzavření vybraného screenu musíš potvrdit."}
        pid, identity = payload.get("pid"), payload.get("identity")
        if type(pid) is not int or pid <= 1 or not isinstance(identity, str) or len(identity) != 64:
            return {"ok": False, "message": "Chybí platná identita screenu. Obnov přehled."}
        force = payload.get("force") is True
        with self._lock:
            try:
                for _ in range(2):
                    processes = self.processes()
                    p = next((p for p in processes if p.pid == pid), None)
                    if p is None:
                        return {"ok": True, "status": "already_stopped", "message": "Screen už neběží."}
                    screen = next((s for s in self.screens() if s["pid"] == pid), None)
                    if screen is None:
                        return {"ok": False, "message": "Screen není v ověřeném seznamu. Obnov přehled."}
                    row = self._screen_row(screen, p, processes)
                    if not row["can_stop"] or not hmac.compare_digest(row["identity"], identity):
                        return {"ok": False, "message": "Screen nebo procesy uvnitř se změnily, případně jsou chráněné. Obnov přehled."}
                if force and identity not in self._stopping:
                    return {"ok": False, "message": "Nejdřív použij běžné uzavření screenu."}
                if force:
                    self.signal_process(pid, signal.SIGKILL)
                else:
                    try:
                        self.quit_session(screen["socket"])
                    except subprocess.TimeoutExpired:
                        pass  # Never retry or escalate without another explicit confirmation.
                self._stopping.add(identity)
                deadline = time.monotonic() + self.wait_seconds
                while True:
                    current = next((c for c in self.processes() if c.pid == pid), None)
                    if current is None or current.started != p.started or current.command != p.command:
                        self._stopping.discard(identity)
                        message = "Screen byl uzavřen. Soubory zůstaly zachované."
                        if force:
                            message += " Procesy uvnitř mohly zůstat běžet; zkontroluj přehled relací."
                        return {"ok": True, "status": "stopped", "message": message}
                    if time.monotonic() >= deadline:
                        return {"ok": False, "status": "still_running", "force_available": not force,
                                "message": "Screen zatím běží. Obnov přehled; vynucené uzavření vyžaduje další potvrzení."}
                    time.sleep(0.15)
            except ProcessLookupError:
                return {"ok": True, "status": "already_stopped", "message": "Screen už neběží."}
            except (OSError, ValueError, subprocess.SubprocessError):
                return {"ok": False, "message": "Uzavření se nepodařilo ověřit. Obnov přehled."}
