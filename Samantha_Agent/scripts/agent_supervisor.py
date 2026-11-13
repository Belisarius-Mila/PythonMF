#!/usr/bin/env python3
"""Registered local supervisor diagnostics and opt-in one-shot worker."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.agent_supervisor import AgentSupervisor, ROOT
from app.agent_supervisor_service import SupervisorService


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("status", "check", "tick", "service-preview"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--confirmed", action="store_true")
    args = parser.parse_args(argv)
    supervisor = AgentSupervisor(args.root)
    try:
        if args.command == "service-preview":
            result = SupervisorService(root=args.root).preview()
        elif args.command == "status":
            result = supervisor.status()
        else:
            result = supervisor.check(confirmed=args.confirmed, scheduled=args.command == "tick")
    except Exception:
        # Never serialize errors that might contain secret hooks or raw process data.
        result = {"ok": False, "status": "unavailable", "message": "Stav dohledu nelze potvrdit."}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok", args.command == "service-preview") else 1


if __name__ == "__main__":
    raise SystemExit(main())
