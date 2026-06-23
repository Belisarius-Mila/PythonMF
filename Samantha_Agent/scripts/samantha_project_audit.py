#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.project_audit_report import format_samantha_project_audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run git-safe Samantha project/tool/layer audit.")
    parser.add_argument(
        "--mode",
        choices=("quick", "full"),
        default="quick",
        help="quick is concise; full includes more active projects and warnings.",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="write a git-safe report to memory/reports/.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(format_samantha_project_audit(mode=args.mode, save=args.save), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
