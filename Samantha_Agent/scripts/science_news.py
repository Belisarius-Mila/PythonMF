#!/usr/bin/env python3
"""Registered ScienceNews status/preview/import/tick. Never installs a service."""
from __future__ import annotations

import argparse
import json
import plistlib
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.science_news import ROOT, ScienceNews
from app.science_news_sources import collect
from app.science_news_runner import tick, INSTRUCTIONS, SCHEMA
from app.science_news_model import call_model, policy
from app.science_news_recovery import recover_model_result, close_interrupted_issue


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("status", "preview", "import", "tick", "service-preview", "close-interrupted"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--editor-reviewed", action="store_true")
    parser.add_argument('--issue-key')
    parser.add_argument('--expected-fingerprint')
    parser.add_argument('--request-id')
    parser.add_argument('--confirmed', action='store_true')
    args = parser.parse_args(argv)
    store = ScienceNews(args.root)
    now = datetime.now(timezone.utc)
    try:
        if args.command == "status":
            from app.cockpit_science_news import science_news_overview
            result = science_news_overview(store=store)
        elif args.command == "service-preview":
            project = Path(__file__).resolve().parents[1]
            definition = {"Label": "com.samantha.science-news",
                "ProgramArguments": [str(project / ".venv/bin/python"), str(Path(__file__).resolve()), "tick"],
                "WorkingDirectory": str(project), "StartInterval": 60, "RunAtLoad": True,
                "StandardOutPath": str(store.root / "scheduler.stdout.log"),
                "StandardErrorPath": str(store.root / "scheduler.stderr.log")}
            result = {"ok": True, "installed": False, "schedule": "Friday 08:00 prepare / 09:00 publish Europe/Prague",
                "plist": plistlib.dumps(definition).decode()}
        elif args.command == 'close-interrupted':
            result = close_interrupted_issue(store, args.issue_key or '',
                expected_fingerprint=args.expected_fingerprint,request_id=args.request_id,confirmed=args.confirmed)
        elif args.command == "preview":
            result = collect(now)
        elif args.command == "import":
            if not args.input or not args.editor_reviewed:
                raise ValueError("Import vyžaduje redakčně zkontrolované vydání a --editor-reviewed.")
            document = json.loads(args.input.read_text())
            result = store.publish(document["issue_id"], document["items"],
                available_at=document["available_at"], source_health=document.get("source_health"))
        else:
            approved = policy(store)  # Inactive returns before creating any job.
            def review(packet):
                return call_model(store, "editor_" + packet['collected_at'][:10].replace('-', ''), packet, INSTRUCTIONS, SCHEMA)
            def recover(packet):
                key = "editor_" + packet['collected_at'][:10].replace('-', '')
                # The guarded adapter reserves the job BEFORE any model RPC.
                # Absence therefore proves that the first request was not made.
                if key not in store._read()['jobs']:
                    return review(packet)
                return recover_model_result(store, key, packet, INSTRUCTIONS, SCHEMA)
            result = tick(store, now, activated_at=datetime.fromisoformat(approved["activated_at"]),
                          reviewer=review, recoverer=recover)
    except (OSError, ValueError, TypeError, KeyError) as error:
        result = {"ok": False, "state": "blocked", "message": str(error)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", result.get("complete", False)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
