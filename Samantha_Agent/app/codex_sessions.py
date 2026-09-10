"""Inspect terminal Codex processes and stop only a freshly confirmed identity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import os
from pathlib import Path
import secrets
import shlex
import signal
import subprocess
import threading
import time

from scripts.codex_session_report import format_age, load_labels, parse_etime


ROOT = Path(__file__).resolve().parents[2]
PS_COMMAND = ["/bin/ps", "-axo", "pid=,ppid=,uid=,tty=,lstart=,etime=,command="]


@dataclass(frozen=True)
class Process:
    pid: int
    ppid: int
    uid: int
    tty: str
    started: str
    age: int
    command: str

    @property
    def argv(self):
        try:
            return shlex.split(self.command)
        except ValueError:
            return []

    @property
    def is_codex(self):
        return bool(self.argv and Path(self.argv[0]).name == "codex")

    @property
    def is_terminal(self):
        return (self.is_codex and self.tty not in ("", "??", "?", "-")
                and not {"app-server", "mcp-server", "exec", "review"}.intersection(self.argv[1:]))


def read_processes():
    result = subprocess.run(PS_COMMAND, capture_output=True, text=True, timeout=4, check=True)
    rows = []
    for line in result.stdout.splitlines():
        parts = line.split(None, 10)
        if len(parts) != 11:
            continue
        rows.append(Process(int(parts[0]), int(parts[1]), int(parts[2]), parts[3],
                            " ".join(parts[4:9]), parse_etime(parts[9]), parts[10]))
    return rows


def process_cwd(pid):
    result = subprocess.run(["/usr/sbin/lsof", "-nP", "-a", "-p", str(pid), "-d", "cwd", "-Fn"],
                            capture_output=True, text=True, timeout=3, check=False)
    if result.returncode == 0:
        return next((line[1:] for line in result.stdout.splitlines() if line.startswith("n")), "")
    return ""


def process_executable(pid):
    result = subprocess.run(["/bin/ps", "-p", str(pid), "-o", "comm="],
                            capture_output=True, text=True, timeout=3, check=True)
    return result.stdout.strip()


class CodexSessionController:
    def __init__(self, *, root=ROOT, processes=read_processes, cwd=process_cwd,
                 labels=load_labels, executable=process_executable, signal_process=os.kill, own_pid=None, uid=None,
                 wait_seconds=2.0):
        self.root = Path(root).resolve()
        self.processes, self.cwd, self.labels = processes, cwd, labels
        self.executable = executable
        self.signal_process = signal_process
        self.own_pid = os.getpid() if own_pid is None else own_pid
        self.uid = os.getuid() if uid is None else uid
        self.wait_seconds = wait_seconds
        self._key = secrets.token_bytes(32)
        self._lock = threading.Lock()
        self._stopping = set()

    def _ancestors(self, processes):
        parents = {p.pid: p.ppid for p in processes}
        result = {self.own_pid}
        pid = parents.get(self.own_pid)
        while pid and pid not in result:
            result.add(pid)
            pid = parents.get(pid)
        return result

    def _row(self, p, processes):
        cwd = self.cwd(p.pid)
        executable = self.executable(p.pid)
        directory = Path(cwd).resolve() if cwd else None
        # Codex --cd selects the project without necessarily changing OS cwd.
        for index, arg in enumerate(p.argv[1:], start=1):
            selected = None
            if arg in ("-C", "--cd"):
                selected = p.argv[index + 1] if index + 1 < len(p.argv) else ""
            elif arg.startswith("--cd="):
                selected = arg.split("=", 1)[1]
            elif arg.startswith("-C") and len(arg) > 2:
                selected = arg[2:]
            if selected is not None:
                if not selected or not cwd:
                    directory = None
                    break
                selected_path = Path(selected).expanduser()
                directory = (selected_path if selected_path.is_absolute() else Path(cwd) / selected_path).resolve()
        in_project = directory is not None and directory.is_relative_to(self.root)
        label = self.labels().get(p.tty, {})
        reason = ""
        if not p.is_terminal or Path(executable).name != "codex":
            reason = "Podpůrná služba není terminálová relace."
        elif p.uid != self.uid:
            reason = "Proces patří jinému uživateli."
        elif p.pid in self._ancestors(processes):
            reason = "Tato relace spustila správce; je chráněná."
        elif label.get("protected"):
            reason = "Relace má ochranný štítek."
        elif not in_project:
            reason = "Pracovní adresář není ověřený v PythonMF."
        identity = f"{p.pid}|{p.ppid}|{p.uid}|{p.tty}|{p.started}|{p.command}|{cwd}|{executable}"
        token = hmac.new(self._key, identity.encode(), hashlib.sha256).hexdigest()
        return {"pid": p.pid, "tty": p.tty, "started": p.started,
                "age": format_age(p.age), "age_seconds": p.age,
                "label": str(label.get("label") or "Terminálový Codex"),
                "project": "PythonMF" if in_project else "Neověřený / jiný adresář",
                "can_stop": not reason, "protected_reason": reason,
                "identity": token, "force_available": token in self._stopping}

    def status(self):
        try:
            processes = self.processes()
            sessions = [self._row(p, processes) for p in processes if p.is_terminal and p.uid == self.uid]
            return {"ok": True, "generated_at": datetime.now(timezone.utc).isoformat(),
                    "sessions": sessions,
                    "protected_services": sum(p.is_codex and not p.is_terminal for p in processes),
                    "message": "Běžící proces nemusí právě odpovídat ani být zaseknutý."}
        except (OSError, ValueError, subprocess.SubprocessError):
            return {"ok": False, "sessions": [], "message": "Přehled procesů se nepodařilo ověřit. Obnov jej."}

    def stop(self, payload):
        if payload.get("confirmed") is not True:
            return {"ok": False, "message": "Ukončení vybrané relace musíš potvrdit."}
        pid, identity = payload.get("pid"), payload.get("identity")
        if type(pid) is not int or pid <= 1 or not isinstance(identity, str) or len(identity) != 64:
            return {"ok": False, "message": "Chybí platná identita vybrané relace. Obnov přehled."}
        force = payload.get("force") is True
        with self._lock:
            try:
                # Repeat immediately before signaling: process, owner, cwd and protection may change.
                for _ in range(2):
                    processes = self.processes()
                    p = next((p for p in processes if p.pid == pid), None)
                    if p is None:
                        return {"ok": True, "status": "already_stopped", "message": "Relace už neběží."}
                    row = self._row(p, processes)
                    if not row["can_stop"] or not hmac.compare_digest(row["identity"], identity):
                        return {"ok": False, "message": "Relace se změnila nebo je chráněná. Obnov přehled."}
                if force and identity not in self._stopping:
                    return {"ok": False, "message": "Nejdřív použij běžné ukončení relace."}
                self.signal_process(pid, signal.SIGKILL if force else signal.SIGTERM)
                self._stopping.add(identity)
                deadline = time.monotonic() + self.wait_seconds
                while True:
                    current = next((item for item in self.processes() if item.pid == pid), None)
                    if current is None or current.started != p.started or current.command != p.command:
                        self._stopping.discard(identity)
                        return {"ok": True, "status": "stopped", "message": f"Codex na {p.tty} byl ukončen. Screen i soubory zůstaly zachované."}
                    if time.monotonic() >= deadline:
                        return {"ok": False, "status": "still_running", "force_available": not force,
                                "message": "Relace zatím běží. Obnov přehled; pokud nereaguje, můžeš potvrdit vynucené ukončení."}
                    time.sleep(0.15)
            except ProcessLookupError:
                return {"ok": True, "status": "already_stopped", "message": "Relace už neběží."}
            except (OSError, ValueError, subprocess.SubprocessError):
                return {"ok": False, "message": "Ukončení se nepodařilo ověřit. Obnov přehled před dalším krokem."}
