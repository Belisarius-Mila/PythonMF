#!/usr/bin/env python3
"""Print a redacted, read-only readiness audit for calendar automation."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TextIO


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.family_calendar_delivery_config import (  # noqa: E402
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
)
from app.family_calendar_delivery_readiness import (  # noqa: E402
    DEFAULT_FAMILY_CALENDAR_PLANNER_PATH,
    DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
    FamilyCalendarDeliveryReadinessResult,
    inspect_family_calendar_delivery_readiness,
)
from app.family_calendar_delivery_store import (  # noqa: E402
    DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
)


ReadinessRunner = Callable[..., FamilyCalendarDeliveryReadinessResult]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect family-calendar automation prerequisites without writes, "
            "secret reads, or sending."
        ),
    )
    parser.add_argument("--config-path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--state-path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--planner-path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--planner-runner-path", type=Path, help=argparse.SUPPRESS)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    output: TextIO | None = None,
    readiness_runner: ReadinessRunner = inspect_family_calendar_delivery_readiness,
) -> int:
    stream = sys.stdout if output is None else output
    arguments = build_parser().parse_args(argv)
    result = readiness_runner(
        config_path=arguments.config_path
        or DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
        state_path=arguments.state_path or DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
        planner_path=arguments.planner_path
        or DEFAULT_FAMILY_CALENDAR_PLANNER_PATH,
        planner_runner_path=arguments.planner_runner_path
        or DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
    )
    print(
        json.dumps(result.safe_document(), ensure_ascii=False, sort_keys=True),
        file=stream,
    )
    return 0 if result.ready_to_enable else 1


if __name__ == "__main__":
    raise SystemExit(main())
