#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.quick_notes import list_quick_notes_text, quick_notes_action_status_text, show_quick_note_detail_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List or inspect Samantha quick notes from iCloud Shortcuts inbox.")
    parser.add_argument("--detail", type=int, help="Show detail for a numbered note.")
    parser.add_argument("--limit", type=int, default=30, help="Maximum number of notes in list output.")
    parser.add_argument("--status", action="store_true", help="Show action inbox with automatic pre-classification.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.detail is not None:
        print(show_quick_note_detail_text(note_number=args.detail))
        return 0
    if args.status:
        print(quick_notes_action_status_text(limit=args.limit))
        return 0
    print(list_quick_notes_text(limit=args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
