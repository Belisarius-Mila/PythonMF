#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.tvbcp import append_tvbcp_entry, start_tvbcp, tvbcp_status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Správa dočasného VoiceBridge pracovního protokolu.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="Založit TVBCP bez přepsání existujícího protokolu.")
    start.add_argument("--title", required=True)

    append = subparsers.add_parser("append", help="Přidat stručný strukturovaný záznam.")
    append.add_argument("--discussed", default="")
    append.add_argument("--conclusion", default="")
    append.add_argument("--open-question", default="")
    append.add_argument("--next-step", default="")

    subparsers.add_parser("status", help="Vypsat pouze technický stav bez obsahu.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "start":
            result = start_tvbcp(title=args.title)
        elif args.command == "append":
            result = append_tvbcp_entry(
                discussed=args.discussed,
                conclusion=args.conclusion,
                open_question=args.open_question,
                next_step=args.next_step,
            )
        else:
            status = tvbcp_status()
            result = {key: status[key] for key in ("ok", "active", "updated_at", "chars")}
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "message": str(exc)}, ensure_ascii=False))
        return 1
    printable = {key: str(value) if isinstance(value, Path) else value for key, value in result.items()}
    print(json.dumps(printable, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
