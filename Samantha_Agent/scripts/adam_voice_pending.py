#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.speech.adam_voice_mode import ADAM_PENDING_COMMAND_PATH, load_pending_for_adam


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Zobrazí hlasový pokyn čekající na převzetí Adamem v Codexu.")
    parser.add_argument("--path", type=Path, default=ADAM_PENDING_COMMAND_PATH)
    parser.add_argument("--json", action="store_true", help="Vypsat celý záznam jako JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    pending = load_pending_for_adam(path=args.path)
    if args.json:
        print(json.dumps(pending, ensure_ascii=False, indent=2))
        return 0 if pending.get("ok") else 1

    print("ADAM VOICE PENDING")
    print(f"- pending: {str(bool(pending.get('pending'))).lower()}")
    print(f"- status: {pending.get('status') or 'unknown'}")
    print(f"- reason: {pending.get('reason') or '-'}")
    print(f"- created_at: {pending.get('created_at') or '-'}")
    print("")
    print("TEXT:")
    print(str(pending.get("text") or pending.get("message") or "Žádný hlasový pokyn nečeká na Adama."))
    return 0 if pending.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
