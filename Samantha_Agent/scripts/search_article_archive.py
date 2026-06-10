#!/usr/bin/env python3
"""Full-text search in the private article archive."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.article_archive import DEFAULT_ARCHIVE_ROOT, search_articles


def main() -> int:
    parser = argparse.ArgumentParser(description="Search private archived article text.")
    parser.add_argument("query")
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument("--category", default="all", help="recipes, science, other, or all.")
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()

    data = search_articles(
        query=args.query,
        category=args.category,
        archive_root=args.archive_root,
        limit=args.limit,
    )
    results = data.get("items", [])
    if not results:
        print("No article archive matches.")
        return 1
    for index, item in enumerate(results, start=1):
        print(f"{index}. {item.get('one_line_title') or item.get('title', '')}")
        print(f"   id: {item.get('id', '')}")
        print(f"   category: {item.get('category_label', '')}")
        print(f"   score: {item.get('score', '')}")
        print(f"   url: {item.get('canonical_url') or item.get('source_url', '')}")
        print(f"   snippet: {item.get('snippet', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
