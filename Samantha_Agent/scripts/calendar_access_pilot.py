#!/usr/bin/env python3
"""Explicit read-only EventKit pilot; no calendar mutations or permanent service."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.calendar_access_pilot import CalendarAccessPilot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "status", "authorize", "probe", "service-probe"))
    parser.add_argument("--confirmed", action="store_true")
    args = parser.parse_args()
    pilot = CalendarAccessPilot()
    try:
        if args.action == "status":
            result = pilot.status()
        elif args.action in {"build", "authorize"}:
            result = getattr(pilot, args.action)(confirmed=args.confirmed)
        else:
            result = pilot.probe(confirmed=args.confirmed, service=args.action == "service-probe")
    except Exception as exc:
        print(json.dumps({"ok": False, "error_type": type(exc).__name__, "automatic_retry": False}))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
