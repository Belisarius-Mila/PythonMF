#!/usr/bin/env python3
"""Archive manually provided text as a private knowledge entry."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.article_archive import DEFAULT_ARCHIVE_ROOT, archive_text_entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive pasted or file-based text as a knowledge entry.")
    parser.add_argument("--title", default="", help="Entry title. If omitted, the first text line is used.")
    parser.add_argument("--text-file", type=Path, help="UTF-8 text file to archive. If omitted, stdin is used.")
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument(
        "--category",
        default="other",
        help="Entry category: recipes, science, health_info, ai_tools, travel_places, or other.",
    )
    parser.add_argument("--tag", action="append", default=[], help="Optional tag. Can be used repeatedly.")
    parser.add_argument("--source-label", default="Vložený text", help="Human-readable source label.")
    parser.add_argument("--source-note", default="", help="Optional source note.")
    args = parser.parse_args()

    try:
        if args.text_file is not None:
            text = args.text_file.read_text(encoding="utf-8")
        else:
            text = sys.stdin.read()
        result = archive_text_entry(
            title=args.title,
            text=text,
            category=args.category,
            tags=[str(tag).strip() for tag in args.tag if str(tag).strip()],
            source_label=args.source_label,
            source_note=args.source_note,
            archive_root=args.archive_root,
        )
    except (OSError, ValueError) as exc:
        print(f"Archive failed: {exc}", file=sys.stderr)
        return 1

    item = result["item"]
    print("Archived text entry:")
    print(f"- id: {item['id']}")
    print(f"- title: {item.get('title') or item.get('one_line_title', '')}")
    print(f"- category: {item.get('category', '')}")
    print(f"- source: {item.get('source_label', '')}")
    print(f"- chars: {item.get('text_chars', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
