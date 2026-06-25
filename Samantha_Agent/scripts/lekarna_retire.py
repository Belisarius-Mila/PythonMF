from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.lekarna.service import (  # noqa: E402
    RETIRE_CONFIRMATION_PHRASE,
    format_domaci_lek_retire_preview,
    format_retire_domaci_lek,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview or soft-retire one home pharmacy item.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    preview_parser = subparsers.add_parser("preview", help="Show the planned soft-retire change.")
    preview_parser.add_argument("--query", required=True, help="Medicine name or a precise part of it.")
    preview_parser.add_argument("--reason", default="", help="Optional reason, e.g. spotrebovano.")

    apply_parser = subparsers.add_parser("apply", help="Apply the soft-retire change after confirmation.")
    apply_parser.add_argument("--query", required=True, help="Medicine name or a precise part of it.")
    apply_parser.add_argument("--reason", default="", help="Optional reason, e.g. spotrebovano.")
    apply_parser.add_argument(
        "--confirm",
        required=True,
        help=f"Required confirmation text containing: {RETIRE_CONFIRMATION_PHRASE}",
    )

    args = parser.parse_args()
    if args.command == "preview":
        print(format_domaci_lek_retire_preview(query=args.query, reason=args.reason))
        return 0

    print(
        format_retire_domaci_lek(
            query=args.query,
            reason=args.reason,
            user_confirmed=True,
            confirmation_text=args.confirm,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
