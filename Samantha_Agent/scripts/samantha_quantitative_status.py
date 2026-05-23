#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.quantitative_status import format_samantha_quantitative_status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Samantha aggregate quantitative status.")
    parser.add_argument(
        "--save",
        action="store_true",
        help="append one aggregate JSONL metric row to data/metrics/samantha_quantitative_status.jsonl",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(format_samantha_quantitative_status(save=args.save))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
