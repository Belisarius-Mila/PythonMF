#!/usr/bin/env python3
"""Prepare or explicitly install the independent autosave LaunchAgent."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from scripts.start_autosave import start_autosave, stop_owned_workers

LABEL = "com.miloslavfalta.samantha.autosave"
CONFIRMATION = "Potvrzuji globální brzdu: rozumím riziku a chci pokračovat."


def launch_agent(project: Path = PROJECT_ROOT) -> dict:
    return {
        "Label": LABEL,
        "ProgramArguments": ["/bin/zsh", str(project / "scripts/autosave_codex_session.sh"), "--watch"],
        "WorkingDirectory": str(project),
        "EnvironmentVariables": {
            "SAMANTHA_PROJECT_DIR": str(project),
            "SAMANTHA_AUTOSAVE_AUTO_CLEANUP": "0",
            "SAMANTHA_AUTOSAVE_SECONDS": "600",
            "SAMANTHA_AUTOSAVE_HISTORY_SECONDS": "3600",
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        },
        "RunAtLoad": True,
        "KeepAlive": True,
        "ThrottleInterval": 10,
        "ProcessType": "Background",
        "StandardOutPath": str(project / "logs/autosave_launchd.out.log"),
        "StandardErrorPath": str(project / "logs/autosave_launchd.err.log"),
    }


def prepare(*, project: Path = PROJECT_ROOT, agents: Path | None = None) -> dict:
    agents = agents or Path.home() / "Library/LaunchAgents"
    target = agents / (LABEL + ".plist")
    if target.is_symlink():
        raise ValueError("Refusing a symlink LaunchAgent")
    spec = launch_agent(project)
    if target.exists():
        current = plistlib.loads(target.read_bytes())
        if current.get("Label") != LABEL or current.get("ProgramArguments") != spec["ProgramArguments"]:
            raise ValueError("Existing LaunchAgent is not owned by this autosave")
    preview = project / "data/autosave_service" / target.name
    preview.parent.mkdir(parents=True, exist_ok=True)
    preview.write_bytes(plistlib.dumps(spec))
    return {"ok": True, "label": LABEL, "preview": str(preview), "target": str(target),
            "automatic_cleanup": False, "run_at_login": True, "restart_after_failure": True}


def install(*, confirmation: str, project: Path = PROJECT_ROOT, agents: Path | None = None,
            runner=subprocess.run, stop_worker=stop_owned_workers, recover=start_autosave) -> dict:
    if confirmation.strip() != CONFIRMATION:
        raise ValueError("Missing exact global safety confirmation")
    plan = prepare(project=project, agents=agents)
    target = Path(plan["target"])
    domain = f"gui/{os.getuid()}"
    job = domain + "/" + LABEL
    def run(argv, *, check=True):
        result = runner(argv, capture_output=True, text=True, check=False, timeout=30)
        if check and result.returncode:
            raise RuntimeError("Autosave launchctl operation failed")
        return result
    loaded = run(["/bin/launchctl", "print", job], check=False).returncode == 0
    if loaded and not target.exists():
        raise ValueError("Loaded autosave job has no owned definition")
    try:
        if loaded:
            run(["/bin/launchctl", "bootout", job])
        target.parent.mkdir(parents=True, exist_ok=True)
        staged = target.parent / (".autosave-" + uuid4().hex)
        with staged.open("xb") as handle:
            os.chmod(staged, 0o600)
            handle.write(plistlib.dumps(launch_agent(project)))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(staged, target)
        run(["/bin/launchctl", "bootstrap", domain, str(target)])
        # The job is registered before the old detached worker is retired.
        stop_worker()
        run(["/bin/launchctl", "enable", job])
        run(["/bin/launchctl", "kickstart", "-k", job])
    except Exception:
        recover()
        raise
    return {"ok": True, "installed": True, "label": LABEL, "automatic_cleanup": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "install"))
    parser.add_argument("--confirmation", default="")
    args = parser.parse_args()
    try:
        result = prepare() if args.action == "prepare" else install(confirmation=args.confirmation)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
