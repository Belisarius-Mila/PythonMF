#!/usr/bin/env python3
"""Read-only report of Adam Voice terminal bridge readiness."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.cockpit import adam_voice_bridge_status


def main() -> int:
    status = adam_voice_bridge_status()
    warnings = status.get("warnings") or []
    print("Adam Voice bridge readiness:")
    print(f"- stav: {status.get('status')}")
    print(f"- cíl markeru: {status.get('marked_tty') or 'nezjištěno'}")
    print(f"- aktivní Codex TTY: {', '.join(status.get('codex_ttys') or []) or 'žádné'}")
    print(f"- screen: {status.get('screen_status')} ({status.get('screen_message')})")
    if warnings:
        print("- varování:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("- varování: žádné")
    print(f"- shrnutí: {status.get('message')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
