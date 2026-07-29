#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.memory_truth_audit import (
    format_memory_truth_audit,
    memory_truth_audit_json,
    run_memory_truth_audit,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run deterministic read-only truth audit of all Samantha workstreams."
        )
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Print a human report or machine-readable JSON to stdout.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_memory_truth_audit()
    output = (
        memory_truth_audit_json(result)
        if args.format == "json"
        else format_memory_truth_audit(result)
    )
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
