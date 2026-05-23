#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.health_check import format_samantha_health_check


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run read-only Samantha infrastructure health check.")
    parser.add_argument(
        "--mode",
        choices=("quick", "full"),
        default="quick",
        help="quick is concise; full shows all warnings and pending items.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(format_samantha_health_check(mode=args.mode))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
