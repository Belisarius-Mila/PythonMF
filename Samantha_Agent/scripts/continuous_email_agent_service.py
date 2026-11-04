#!/usr/bin/env python3
"""Registered lifecycle entry for the owned hourly email service."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.email.service_control import EmailServiceController


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "install", "status", "pause", "resume", "verify-restart"))
    parser.add_argument("--confirmation", default="")
    parser.add_argument("--confirmed", action="store_true")
    args = parser.parse_args()
    controller = EmailServiceController()
    try:
        if args.action == "install":
            digest = json.loads(controller.plan_path.read_text())["digest"]
            result = controller.install(confirmation=args.confirmation, plan_digest=digest)
        elif args.action == "verify-restart":
            result = controller.verify_restart(confirmation=args.confirmation)
        elif args.action in {"pause", "resume"}:
            result = getattr(controller, args.action)(confirmed=args.confirmed)
        else:
            result = getattr(controller, args.action)()
    except Exception as exc:
        print(json.dumps({"ok": False, "error_type": type(exc).__name__,
                          "message": "Operace služby se nedokončila; zkontroluj připravený plán a její stav."}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
