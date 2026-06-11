#!/usr/bin/env python3
"""Attach an image to a private knowledge archive entry."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.article_archive import (
    ATTACHMENT_CONFIRMATION_PHRASE,
    DEFAULT_ARCHIVE_ROOT,
    attach_article_image,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Attach an image to an archived knowledge entry.")
    parser.add_argument("--article-id", required=True, help="Knowledge archive item ID.")
    parser.add_argument("--image", required=True, type=Path, help="Path to JPG/PNG/WEBP/HEIC image.")
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument("--label", default="Ručně psaný recept", help="Attachment label.")
    parser.add_argument("--role", default="handwritten_recipe_scan", help="Attachment role.")
    parser.add_argument("--note", default="", help="Optional attachment note.")
    parser.add_argument("--tag", action="append", default=[], help="Optional tag to add to the entry.")
    parser.add_argument(
        "--confirm",
        default="",
        help=f"Required confirmation text containing: {ATTACHMENT_CONFIRMATION_PHRASE}",
    )
    args = parser.parse_args()

    try:
        result = attach_article_image(
            article_id=args.article_id,
            image_path=args.image,
            archive_root=args.archive_root,
            label=args.label,
            role=args.role,
            note=args.note,
            tags=[str(tag).strip() for tag in args.tag if str(tag).strip()],
            user_confirmed=True,
            confirmation_text=args.confirm,
        )
    except (OSError, ValueError) as exc:
        print(f"Attach failed: {exc}", file=sys.stderr)
        return 1

    item = result["item"]
    attachment = result["attachment"]
    print("Attached image:")
    print(f"- article_id: {item['id']}")
    print(f"- title: {item.get('title') or item.get('one_line_title', '')}")
    print(f"- attachment_id: {attachment['id']}")
    print(f"- label: {attachment.get('label', '')}")
    print(f"- attachments: {item.get('attachment_count', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
