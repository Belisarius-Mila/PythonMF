#!/usr/bin/env python3
"""Archive a web article URL as private searchable plain text."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.article_archive import (
    DEFAULT_ARCHIVE_ROOT,
    archive_url,
    extract_article,
    write_article_archive,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive one article URL as private searchable text.")
    parser.add_argument("url", nargs="?", help="Article URL to fetch.")
    parser.add_argument("--html-file", type=Path, help="Use an already downloaded HTML file instead of fetching URL.")
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument(
        "--category",
        default="other",
        help="Article category: recipes, science, health_info, ai_tools, travel_places, or other.",
    )
    parser.add_argument("--tag", action="append", default=[], help="Optional tag. Can be used repeatedly.")
    parser.add_argument("--timeout", type=float, default=25.0)
    args = parser.parse_args()

    tags = [str(tag).strip() for tag in args.tag if str(tag).strip()]
    try:
        if args.html_file is not None:
            if not args.url:
                raise ValueError("URL is required when --html-file is used, so metadata has a real source URL.")
            html_bytes = args.html_file.read_bytes()
            article = extract_article(html_bytes, args.url)
            metadata = write_article_archive(
                source_url=args.url,
                html_bytes=html_bytes,
                article=article,
                archive_root=args.archive_root,
                now=datetime.now(timezone.utc).replace(microsecond=0),
                category=args.category,
                tags=tags,
            )
            item = metadata
        else:
            if not args.url:
                raise ValueError("URL is required unless --html-file is used.")
            result = archive_url(
                url=args.url,
                category=args.category,
                tags=tags,
                archive_root=args.archive_root,
                timeout=args.timeout,
            )
            item = result["item"]
    except OSError as exc:
        print(f"Archive failed: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Archive failed: {exc}", file=sys.stderr)
        return 1

    print("Archived article:")
    print(f"- id: {item['id']}")
    print(f"- title: {item.get('title') or item.get('one_line_title', '')}")
    print(f"- category: {item.get('category', '')}")
    print(f"- chars: {item.get('text_chars', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
