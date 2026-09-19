#!/usr/bin/env python3
"""Isolated private-network control for Camino C02b T048 and T049."""

from __future__ import annotations

import argparse
import subprocess
import sys
import urllib.error
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import camino_c02b_t043_control as shared


TEST_LABELS = ("T048", "T049")


def config(test_label: str) -> shared.ControlConfig:
    if test_label not in TEST_LABELS:
        raise shared.ControlError("unsupported Camino C02b physical test")
    return shared.ControlConfig(
        state_root=PROJECT_ROOT / "data" / "private" / "camino" / f"c02b_{test_label.lower()}",
        test_label=test_label,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("test_label", choices=TEST_LABELS)
    parser.add_argument("action", choices=("start", "copy-token", "status", "stop"))
    args = parser.parse_args(argv)
    selected = config(args.test_label)
    try:
        if args.action == "start":
            result = shared.start(selected)
        elif args.action == "copy-token":
            result = shared.copy_token(selected)
        elif args.action == "status":
            result = shared.status(selected)
        else:
            result = shared.stop(selected)
    except (shared.ControlError, OSError, subprocess.SubprocessError, urllib.error.URLError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
