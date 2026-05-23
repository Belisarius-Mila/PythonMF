from __future__ import annotations

import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(PROJECT_ROOT))

from app.knowledge_inbox import (  # noqa: E402
    COPY_CONFIRMATION_PHRASE,
    copy_downloads_to_knowledge_inbox,
    format_downloads_inventory,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List Downloads files or copy selected files into the private knowledge inbox."
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List safe metadata for top-level files in Downloads.",
    )
    parser.add_argument(
        "--copy",
        nargs="*",
        help="One or more Downloads file names to preview or copy.",
    )
    parser.add_argument(
        "--confirm",
        default="",
        help=f"Confirmation text. Required for copying: {COPY_CONFIRMATION_PHRASE}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.copy:
        print(
            copy_downloads_to_knowledge_inbox(
                "\n".join(args.copy),
                user_confirmed=bool(args.confirm),
                confirmation_text=args.confirm,
            )
        )
        return

    print(format_downloads_inventory())


if __name__ == "__main__":
    main()
