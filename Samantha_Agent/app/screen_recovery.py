"""One-use local handoff from Cockpit to the narrowly scoped VS Code extension."""

import json
from pathlib import Path
import secrets
import subprocess
import threading
import time

from app.codex_sessions import ROOT


EXTENSION_ID = "samantha-local.screen-recovery"
EXTENSION_VERSION = "0.1.0"


def extension_installed():
    for path in (Path.home() / ".vscode/extensions").glob(f"{EXTENSION_ID}-{EXTENSION_VERSION}*/package.json"):
        try:
            package = json.loads(path.read_text())
            if (package.get("publisher") == "samantha-local"
                    and package.get("name") == "screen-recovery"
                    and package.get("version") == EXTENSION_VERSION):
                return True
        except (OSError, ValueError):
            continue
    return False


def open_vscode(uri, project_root=ROOT):
    code = "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
    # URI delivery alone does not guarantee a VS Code window exists. Opening
    # this folder reuses its window or creates one, without replacing another.
    subprocess.run([code, str(project_root)], capture_output=True, timeout=12, check=True)
    subprocess.run([code, "--open-url", uri], capture_output=True, timeout=12, check=True)


class ScreenRecovery:
    def __init__(self, screens, *, opener=None, available=extension_installed, clock=time.monotonic):
        self.screens, self.available, self.clock = screens, available, clock
        self.opener = opener or (lambda uri: open_vscode(uri, screens.root))
        self._pending = {}
        self._lock = threading.Lock()

    def request(self, payload, port):
        if payload.get("confirmed") is not True:
            return {"ok": False, "message": "Potvrď obnovení vybraného screenu ve VS Code na Macu."}
        if not self.available():
            return {"ok": False, "message": "Na Macu chybí doplněk Samantha Screen Recovery pro VS Code. Obnova nebyla spuštěna."}
        if type(port) is not int or not 1 <= port <= 65535:
            return {"ok": False, "message": "Adresa místního Cockpitu není platná."}
        ticket = None
        try:
            with self._lock:
                now = self.clock()
                self._pending = {k: v for k, v in self._pending.items() if v["expires"] > now}
                row = self.screens.verify_attach(payload.get("pid"), payload.get("identity"))
                if row["state"] == "Attached" and payload.get("takeover") is not True:
                    return {"ok": False, "message": "Screen je připojený jinde. Potvrď převzetí připojení."}
                if any(v["pid"] == row["pid"] for v in self._pending.values()):
                    return {"ok": True, "status": "pending", "message": "Požadavek už čeká ve VS Code na Macu. Zkontroluj jeho okno."}
                ticket = secrets.token_hex(32)
                self._pending[ticket] = {"pid": row["pid"], "identity": row["attach_identity"],
                                         "expires": now + 90, "claimed": False}
            # No lock across desktop dispatch: VS Code may redeem immediately.
            self.opener(f"vscode://{EXTENSION_ID}/attach?port={port}&ticket={ticket}")
            return {"ok": True, "status": "requested",
                    "message": "Požadavek předán VS Code na Macu. Připojení ověř v otevřeném terminálu."}
        except (OSError, ValueError, subprocess.SubprocessError):
            if ticket:
                with self._lock:
                    self._pending.pop(ticket, None)
            return {"ok": False, "message": "Screen se změnil nebo VS Code nešlo otevřít. Obnov přehled a zkontroluj VS Code; požadavek se automaticky neopakuje."}

    def claim(self, payload):
        ticket = payload.get("ticket")
        if not isinstance(ticket, str) or len(ticket) != 64:
            return {"ok": False, "message": "Neplatný požadavek obnovy."}
        try:
            with self._lock:
                request = self._pending.get(ticket)
                if not request or request["claimed"] or request["expires"] <= self.clock():
                    return {"ok": False, "message": "Požadavek vypršel nebo už byl použit. Obnov přehled v Cockpitu."}
                request["claimed"] = True
                row = self.screens.verify_attach(request["pid"], request["identity"])
                return {"ok": True, "socket": row["socket"]}
        except (OSError, ValueError, subprocess.SubprocessError):
            return {"ok": False, "message": "Screen už není bezpečně dostupný. Obnov přehled v Cockpitu."}
