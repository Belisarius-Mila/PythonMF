#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.email.text_search_tools import search_email_text_year_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only fulltextove hledani v iCloud e-mailech za jeden rok."
    )
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--term", action="append", required=True)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--confirm", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(
        search_email_text_year_text(
            terms=args.term,
            year=args.year,
            limit=args.limit,
            user_confirmed=bool(args.confirm),
            confirmation_text=args.confirm,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
