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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("status", "preview", "import", "tick", "service-preview"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--editor-reviewed", action="store_true")
    args = parser.parse_args(argv)
    store = ScienceNews(args.root)
    now = datetime.now(timezone.utc)
    try:
        if args.command == "status":
            result = store.overview()
        elif args.command == "service-preview":
            project = Path(__file__).resolve().parents[1]
            definition = {"Label": "com.samantha.science-news",
                "ProgramArguments": [str(project / ".venv/bin/python"), str(Path(__file__).resolve()), "tick"],
                "WorkingDirectory": str(project), "StartInterval": 60, "RunAtLoad": True,
                "StandardOutPath": str(store.root / "scheduler.stdout.log"),
                "StandardErrorPath": str(store.root / "scheduler.stderr.log")}
            result = {"ok": True, "installed": False, "schedule": "Friday 08:00 prepare / 09:00 publish Europe/Prague",
                "plist": plistlib.dumps(definition).decode()}
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
            result = tick(store, now, activated_at=datetime.fromisoformat(approved["activated_at"]),
                reviewer=lambda packet: call_model(store, "editor_" + packet["collected_at"][:10].replace("-", ""),
                    packet, INSTRUCTIONS, SCHEMA))
    except (OSError, ValueError, TypeError, KeyError) as error:
        result = {"ok": False, "state": "blocked", "message": str(error)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", result.get("complete", False)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
