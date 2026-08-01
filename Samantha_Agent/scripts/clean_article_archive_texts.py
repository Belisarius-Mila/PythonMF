#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.article_archive import (
    CLEANUP_CONFIRMATION_PHRASE,
    DEFAULT_ARCHIVE_ROOT,
    article_text_cleanup_report,
    cleanup_article_text,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Najde a volitelně vyčistí balast v uložených článcích Knihovny.")
    parser.add_argument(
        "--category",
        default="science",
        help="Kategorie článků: science, health_info, recipes, ai_tools, travel_places, other, all.",
    )
    parser.add_argument("--apply", action="store_true", help="Přepsat kandidáty čistou extrakcí ze source.html.")
    parser.add_argument("--confirm", default="", help=f"Potvrzovací věta pro --apply: {CLEANUP_CONFIRMATION_PHRASE}")
    parser.add_argument("--min-removed-chars", type=int, default=1000)
    parser.add_argument("--max-cleaned-ratio", type=float, default=0.85)
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument("--json", action="store_true", help="Vypsat strojově čitelný JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = article_text_cleanup_report(
        category=args.category,
        archive_root=args.archive_root,
        min_removed_chars=args.min_removed_chars,
        max_cleaned_ratio=args.max_cleaned_ratio,
    )
    candidates = [item for item in report["items"] if item["needs_cleanup"]]
    applied = []
    if args.apply:
        if CLEANUP_CONFIRMATION_PHRASE.casefold() not in args.confirm.casefold():
            raise SystemExit(f"--apply vyžaduje --confirm '{CLEANUP_CONFIRMATION_PHRASE}'")
        for item in candidates:
            applied.append(
                cleanup_article_text(
                    article_id=item["id"],
                    archive_root=args.archive_root,
                    user_confirmed=True,
                    confirmation_text=args.confirm,
                )
            )
    output = {
        "ok": True,
        "category": report["category"],
        "count": report["count"],
        "candidate_count": len(candidates),
        "candidates": candidates,
        "applied_count": len(applied),
        "applied": applied,
    }
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"Kategorie: {output['category']}")
        print(f"Zkontrolováno: {output['count']}")
        print(f"Kandidáti k čištění: {output['candidate_count']}")
        for item in candidates:
            print(
                "- "
                f"{item['id']} | {item['old_chars']} -> {item['new_chars']} znaků "
                f"(minus {item['removed_chars']}, ratio {item['cleaned_ratio']}, markery {item['marker_count']})"
            )
        if applied:
            print(f"Aplikováno: {len(applied)}")
            for item in applied:
                print(f"- {item['item_id']} | minus {item['removed_chars']} | záloha {item['backup_file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
