#!/usr/bin/env python3
"""Dedicated private-network control for the physical Camino C02b T047 test."""

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


DEFAULT_STATE_ROOT = PROJECT_ROOT / "data" / "private" / "camino" / "c02b_t047"


def config() -> shared.ControlConfig:
    return shared.ControlConfig(state_root=DEFAULT_STATE_ROOT, test_label="T047")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "copy-token", "status", "stop"))
    args = parser.parse_args(argv)
    selected = config()
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
