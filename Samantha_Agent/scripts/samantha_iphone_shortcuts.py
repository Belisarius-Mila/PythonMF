from __future__ import annotations

import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(PROJECT_ROOT))

from app.iphone_shortcuts import (  # noqa: E402
    REQUEST_CONFIRMATION_PHRASE,
    format_iphone_shortcuts_status,
    prepare_iphone_shortcut_request,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect iPhone Shortcuts Playground readiness or prepare a private shortcut request."
    )
    parser.add_argument("--status", action="store_true", help="Show read-only readiness status.")
    parser.add_argument("--name", default="", help="Shortcut name for request preparation.")
    parser.add_argument("--purpose", default="", help="What the shortcut should do.")
    parser.add_argument("--details", default="", help="Optional extra requirements.")
    parser.add_argument(
        "--confirm",
        default="",
        help=f"Confirmation text. Required for writing a request: {REQUEST_CONFIRMATION_PHRASE}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.name or args.purpose or args.details:
        print(
            prepare_iphone_shortcut_request(
                name=args.name,
                purpose=args.purpose,
                details=args.details,
                user_confirmed=bool(args.confirm),
                confirmation_text=args.confirm,
            )
        )
        return

    print(format_iphone_shortcuts_status())


if __name__ == "__main__":
    main()
