#!/usr/bin/env python3
"""Run today's family-calendar delivery validation without sending or state I/O."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Sequence, TextIO


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.family_calendar import DEFAULT_FAMILY_CALENDAR_PATH
from app.family_calendar_delivery_config import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
)
from app.family_calendar_delivery_coordinator import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_WORKER_PATH,
)
from app.family_calendar_delivery_dry_run import (
    run_family_calendar_operational_dry_run,
)
from app.family_calendar_delivery_store import DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate today's family-calendar delivery without sending.",
    )
    parser.add_argument("--today", default="")
    parser.add_argument("--people-path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--config-path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--state-path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--worker-path", type=Path, help=argparse.SUPPRESS)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    output: TextIO | None = None,
) -> int:
    stream = sys.stdout if output is None else output
    arguments = build_parser().parse_args(argv)
    try:
        today = date.fromisoformat(arguments.today) if arguments.today else date.today()
    except ValueError:
        print(
            json.dumps({"status": "input_error", "redacted": True}, sort_keys=True),
            file=stream,
        )
        return 1
    result = run_family_calendar_operational_dry_run(
        today=today,
        people_path=arguments.people_path or DEFAULT_FAMILY_CALENDAR_PATH,
        config_path=(
            arguments.config_path or DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH
        ),
        state_path=arguments.state_path or DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
        worker_path=(
            arguments.worker_path or DEFAULT_FAMILY_CALENDAR_DELIVERY_WORKER_PATH
        ),
    )
    print(json.dumps(result.safe_document(), sort_keys=True), file=stream)
    return 0 if result.status == "dry_run" else 1


if __name__ == "__main__":
    raise SystemExit(main())
