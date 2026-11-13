"""Owned LaunchAgent preview/activation. Never controls watched services."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import plistlib
import subprocess

from app.agent_supervisor import AgentSupervisor, PROJECT, ROOT
from app.file_persistence import atomic_write_text, atomic_create_text, exclusive_file_lock

LABEL = "com.miloslavfalta.samantha.agent-supervisor"
CONFIRMATION = "Potvrzuji globální brzdu: rozumím riziku a chci pokračovat."
SOURCES = ("app/agent_supervisor.py", "app/agent_supervisor_probes.py",
           "app/agent_supervisor_service.py", "scripts/agent_supervisor.py")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


class SupervisorService:
    def __init__(self, *, project=PROJECT, root=ROOT, agents=None, runner=subprocess.run):
        self.project, self.root = Path(project).resolve(), Path(root)
        self.target = (Path(agents) if agents else Path.home() / "Library/LaunchAgents") / (LABEL + ".plist")
        self.runner = runner
        self.receipt = self.root / "installation.json"

    def preview(self):
        if not (self.project / ".venv/bin/python").is_file():
            raise ValueError("Chybí projektový Python.")
        manifest = {name: hashlib.sha256((self.project / name).read_bytes()).hexdigest() for name in SOURCES}
        definition = {"Label": LABEL, "ProgramArguments": [str(self.project / ".venv/bin/python"),
            str(self.project / "scripts/agent_supervisor.py"), "tick"],
            "WorkingDirectory": str(self.project), "StartInterval": 120, "RunAtLoad": True,
            "ProcessType": "Background", "EnvironmentVariables": {"PYTHONDONTWRITEBYTECODE": "1",
                "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/opt/homebrew/bin", "TZ": "Europe/Prague"},
            "StandardOutPath": str(self.root / "scheduler.stdout.log"),
            "StandardErrorPath": str(self.root / "scheduler.stderr.log")}
        # Custom roots are for offline tests only, never a silently misdirected service.
        if self.root.resolve() != ROOT.resolve():
            definition["ProgramArguments"] += ["--root", str(self.root.resolve())]
        plan = {"version": 1, "manifest": manifest, "definition": definition}
        return {**plan, "digest": digest(plan), "installed": False,
                "confirmation": CONFIRMATION, "notifications_enabled": False}

    def status(self):
        receipt = {}
        if self.receipt.exists():
            receipt = json.loads(self.receipt.read_text())
        present = self.target.exists()
        owned = (present and not self.target.is_symlink() and
            hashlib.sha256(self.target.read_bytes()).hexdigest() == receipt.get("plist_sha256"))
        result = self.runner(["/bin/launchctl", "print", f"gui/{os.getuid()}/{LABEL}"],
            capture_output=True, text=True, timeout=3, check=False)
        return {"installed": present, "owned": bool(owned), "loaded": result.returncode == 0,
                "installation_state": receipt.get("state", "not_installed")}

    def install(self, *, approved_digest, confirmation):
        if confirmation != CONFIRMATION:
            raise ValueError("Instalace vyžaduje přesnou globální větu.")
        with exclusive_file_lock(self.root / "installation", timeout=0):
            # A prior requested bootstrap is never sent again, even on uncertainty.
            if self.receipt.exists():
                return {"ok": False, "status": "existing_receipt", **self.status()}
            if self.target.exists() or self.target.is_symlink():
                raise ValueError("Cizí nebo neověřený LaunchAgent se nepřepisuje.")
            plan = self.preview()
            if approved_digest != plan["digest"]:
                raise ValueError("Zdroj dohledu se od schváleného náhledu změnil.")
            # An installation itself cannot authorize notifications or reuse secret hooks.
            supervisor = AgentSupervisor(self.root)
            if supervisor.config()["enabled"] or supervisor.config()["notifications_enabled"]:
                raise ValueError("Před první instalací musí být dohled a oznámení vypnuté.")
            raw = plistlib.dumps(plan["definition"]).decode()
            receipt = {"version": 1, "digest": plan["digest"], "state": "prepared",
                       "plist_sha256": hashlib.sha256(raw.encode()).hexdigest()}
            atomic_write_text(self.receipt, json.dumps(receipt))
            self.target.parent.mkdir(parents=True, exist_ok=True)
            atomic_create_text(self.target, raw)
            receipt["state"] = "bootstrap_requested"
            atomic_write_text(self.receipt, json.dumps(receipt))
            try:
                result = self.runner(["/bin/launchctl", "bootstrap", f"gui/{os.getuid()}", str(self.target)],
                    capture_output=True, text=True, timeout=10, check=False)
                if result.returncode:
                    raise OSError("bootstrap")
                live = self.status()
                if not live["owned"] or not live["loaded"]:
                    raise OSError("verification")
                supervisor.configure(enabled=True, confirmed=True)
                receipt["state"] = "installed"
            except Exception:
                receipt["state"] = "uncertain"
            atomic_write_text(self.receipt, json.dumps(receipt))
            return {"ok": receipt["state"] == "installed", "status": receipt["state"],
                    "notifications_enabled": False}
