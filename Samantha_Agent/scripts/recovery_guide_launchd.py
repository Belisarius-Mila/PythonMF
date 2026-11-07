#!/usr/bin/env python3
"""Print a proposed LaunchAgent. Never installs, loads or starts a service."""
from __future__ import annotations

from pathlib import Path
import plistlib
import sys


def launch_agent(project: Path) -> dict:
    project = project.resolve(strict=True)
    python = project / ".venv/bin/python"
    script = project / "scripts/recovery_guide.py"
    if not python.is_file() or not script.is_file():
        raise ValueError("Chybí absolutní Python nebo vstupní skript.")
    return {"Label": "com.samantha.recovery-guide",
            "ProgramArguments": [str(python), str(script), "tick"],
            "WorkingDirectory": str(project),
            "EnvironmentVariables": {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "OPENAI_AGENTS_DISABLE_TRACING": "1"},
            # A cheap deterministic tick supports login/restart catch-up and DST.
            # The controller selects one due Prague slot; no model polling.
            "StartInterval": 900, "RunAtLoad": True, "ProcessType": "Background",
            "StandardOutPath": str(project / "logs/recovery_guide.out.log"),
            "StandardErrorPath": str(project / "logs/recovery_guide.err.log")}


if __name__ == "__main__":
    sys.stdout.buffer.write(plistlib.dumps(launch_agent(Path(__file__).resolve().parents[1])))
