#!/usr/bin/env python3
"""Registered service diagnostics and opt-in bounded tick; never installs itself."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.email.continuous_agent import ContinuousEmailAgent
from app.email.service import ServiceSettings, launch_agent_preview, readiness, run_service_check
from app.email.pushcut import pushcut_status


def main() -> int:
    parser = argparse.ArgumentParser(description="Průběžný e-mailový agent: stav, příprava a omezený cyklus.")
    parser.add_argument("command", choices=("status", "synthetic-test", "readiness", "service-preview", "tick"))
    args = parser.parse_args()
    if args.command == "synthetic-test":
        return subprocess.run(
            [sys.executable, "-m", "unittest", "tests.test_continuous_email_agent", "tests.test_hourly_email_agent", "tests.test_cockpit_email_agent", "tests.test_agent_reply", "tests.test_email_agent_service", "tests.test_email_pushcut", "-q"],
            cwd=PROJECT_ROOT, check=False,
        ).returncode
    if args.command == "service-preview":
        print(json.dumps({"installation_performed": False, "preview_only": True, "launch_agent": launch_agent_preview(),
                          "settings_template": ServiceSettings().model_dump()}, ensure_ascii=False))
        return 0
    if args.command in {"readiness", "tick"}:
        try:
            result = readiness() if args.command == "readiness" else run_service_check()
        except Exception as exc:
            print(json.dumps({"ok": False, "error_type": type(exc).__name__,
                              "message": "Cyklus nelze spustit; ověř konfiguraci a připravenost služby."}, ensure_ascii=False))
            return 1
        print(json.dumps(result, ensure_ascii=False))
        return 1 if result.get("status") == "failed" else 0
    from app.email.service_control import EmailServiceController
    state = ContinuousEmailAgent().status()
    print(json.dumps({
        "activation": EmailServiceController().status(),
        "items": dict(Counter(item["status"] for item in state["items"].values())),
        "sources": [{"health": item.get("health", "unchecked"), "checked_at": item.get("checked_at", "")}
                    for item in state["sources"].values()],
        "schedule": state.get("schedule", {}),
        "service": state.get("service", {}),
        "pushcut": pushcut_status(),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
