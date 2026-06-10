#!/usr/bin/env python3
"""Read an archived article, preferring the live URL when it is reachable."""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.article_archive import DEFAULT_ARCHIVE_ROOT, get_article, load_article_registry, search_articles


def resolve_article_id(selector: str, archive_root: Path) -> str:
    for item in load_article_registry(archive_root):
        if selector == item.id:
            return item.id
    results = search_articles(query=selector, category="all", archive_root=archive_root, limit=1).get("items", [])
    if results:
        return str(results[0].get("id", ""))
    return ""


def live_url_is_available(url: str, timeout: float) -> bool:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "SamanthaAgentArticleArchive/1.0 (+local personal archive)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Range": "bytes=0-4095",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return int(getattr(response, "status", 200)) < 400
    except (OSError, urllib.error.URLError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Read one article from the private archive.")
    parser.add_argument("selector", help="Article id or search query.")
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--offline", action="store_true", help="Skip the live URL check and print local text.")
    parser.add_argument("--max-chars", type=int, default=4000)
    args = parser.parse_args()

    article_id = resolve_article_id(args.selector, args.archive_root)
    if not article_id:
        print("No matching archived article.", file=sys.stderr)
        return 1
    data = get_article(article_id=article_id, archive_root=args.archive_root, max_chars=args.max_chars)
    if not data.get("ok"):
        print(data.get("message") or "No matching archived article.", file=sys.stderr)
        return 1

    item = data.get("item", {})
    url = str(item.get("canonical_url") or item.get("source_url") or "")
    print(f"Title: {item.get('one_line_title') or item.get('title', '')}")
    print(f"ID: {item.get('id', '')}")
    if url:
        print(f"URL: {url}")

    if url and not args.offline and live_url_is_available(url, args.timeout):
        print("Status: live URL is available")
        print("Local fallback: available in private article archive")
        return 0

    print("Status: using local text fallback")
    print()
    print(data.get("text", ""))
    if data.get("truncated"):
        print("\n[Zkráceno]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
