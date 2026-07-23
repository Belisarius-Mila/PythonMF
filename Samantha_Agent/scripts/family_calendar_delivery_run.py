#!/usr/bin/env python3
"""Launchd-facing family-calendar runner restricted to operational dry-run."""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TextIO


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.family_calendar_delivery_dry_run import main as operational_dry_run_main


DryRunMain = Callable[..., int]


def main(
    argv: Sequence[str] | None = None,
    *,
    output: TextIO | None = None,
    dry_run_main: DryRunMain = operational_dry_run_main,
) -> int:
    """Run only the redacted, non-sending operational dry-run."""

    return dry_run_main(argv, output=output)


if __name__ == "__main__":
    raise SystemExit(main())
