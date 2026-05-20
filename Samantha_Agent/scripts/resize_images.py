from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.media import (
    IMAGE_RESIZE_CONFIRMATION_PHRASE,
    format_apply_image_resize,
    format_preview_image_resize,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preview or apply safe image resizing.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("preview", "apply"):
        subparser = subparsers.add_parser(name)
        subparser.add_argument("--path", default="", help="Image file or directory inside Samantha_Agent.")
        subparser.add_argument("--project", default="", help="Known preset, e.g. lekarna.")
        subparser.add_argument("--target-kb", type=int, default=0, help="Target size per image in kB.")
        subparser.add_argument("--recursive", action="store_true", help="Include nested folders.")
        if name == "apply":
            subparser.add_argument(
                "--confirm",
                default="",
                help=f"Must contain: {IMAGE_RESIZE_CONFIRMATION_PHRASE}",
            )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "preview":
        print(
            format_preview_image_resize(
                path=args.path,
                project=args.project,
                target_kb=args.target_kb,
                recursive=args.recursive,
            )
        )
        return 0

    print(
        format_apply_image_resize(
            path=args.path,
            project=args.project,
            target_kb=args.target_kb,
            recursive=args.recursive,
            user_confirmed=bool(args.confirm),
            confirmation_text=args.confirm,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
