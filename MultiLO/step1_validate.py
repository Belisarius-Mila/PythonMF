"""Step 1 runner: load and validate MultiLO CSV data."""

from __future__ import annotations

from pathlib import Path
import sys

from data_layer import load_data, summarize


def main() -> int:
    base_dir = Path(__file__).resolve().parent
    bundle = load_data(base_dir)

    print("=== MultiLO Step 1 Validation ===")
    print(summarize(bundle))
    print()

    if bundle.validation.warnings:
        print("Warnings:")
        for msg in bundle.validation.warnings:
            print(f"  - {msg}")
        print()

    if bundle.validation.errors:
        print("Errors:")
        for msg in bundle.validation.errors:
            print(f"  - {msg}")
        return 1

    print("Validation OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
