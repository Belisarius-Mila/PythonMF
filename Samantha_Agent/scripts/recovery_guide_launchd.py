#!/usr/bin/env python3
"""Print a proposed LaunchAgent. Never installs, loads or starts a service."""
from __future__ import annotations

from pathlib import Path
import argparse
import json
import os
import plistlib
import subprocess
import sys


def launch_agent(project: Path) -> dict:
    project = project.resolve(strict=True)
    python = project / ".venv/bin/python"
    script = project / "scripts/recovery_guide.py"
    if not python.is_file() or not os.access(python,os.X_OK) or not script.is_file():
        raise ValueError("Chybí absolutní Python nebo vstupní skript.")
    return {"Label": "com.samantha.recovery-guide",
            "ProgramArguments": [str(python), str(script), "tick"],
            "WorkingDirectory": str(project),
            "EnvironmentVariables": {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "OPENAI_AGENTS_DISABLE_TRACING": "1"},
            # A cheap deterministic tick supports login/restart catch-up and DST.
            # The controller selects one due Prague slot; no model polling.
            "StartInterval": 900, "RunAtLoad": True, "ProcessType": "Background",
            "Umask": 0o077,
            "StandardOutPath": str(project / "logs/recovery_guide.out.log"),
            "StandardErrorPath": str(project / "logs/recovery_guide.err.log")}


def check_environment(project: Path) -> dict:
    spec=launch_agent(project)
    # Runs only one read-only CLI status with the proposed minimal PATH. This
    # is not launchctl, a daemon, authentication proof or a model invocation.
    result=subprocess.run([*spec["ProgramArguments"][:2],"status"],cwd=spec["WorkingDirectory"],
        env=spec["EnvironmentVariables"],text=True,capture_output=True,timeout=20,check=True)
    status=json.loads(result.stdout)
    return {"state":"cli_environment_verified","cli_state":status["state"],"minimal_path_tested":True,
            "launchd_session_verified":False,"authentication_verified":False,
            "service_installed":False,"model_calls":0,"writes":False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-environment",action="store_true")
    args=parser.parse_args(argv)
    project=Path(__file__).resolve().parents[1]
    if args.check_environment:
        print(json.dumps(check_environment(project),ensure_ascii=False,indent=2))
    else:
        sys.stdout.buffer.write(plistlib.dumps(launch_agent(project)))
    return 0


if __name__ == "__main__":raise SystemExit(main())
