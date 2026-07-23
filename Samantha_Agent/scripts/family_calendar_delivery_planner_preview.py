#!/usr/bin/env python3
"""Print a read-only preview of the future family-calendar LaunchAgent."""

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

from app.family_calendar_delivery_planner_preview import (  # noqa: E402
    DEFAULT_FAMILY_CALENDAR_PLANNER_HOUR,
    DEFAULT_FAMILY_CALENDAR_PLANNER_MINUTE,
    DEFAULT_FAMILY_CALENDAR_PLANNER_PYTHON_PATH,
    FamilyCalendarPlannerPreview,
    build_family_calendar_planner_preview,
)
from app.family_calendar_delivery_readiness import (  # noqa: E402
    DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
)


PreviewBuilder = Callable[..., FamilyCalendarPlannerPreview]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Preview the future family-calendar LaunchAgent without writing, "
            "installing, loading, reading secrets, or sending."
        ),
    )
    parser.add_argument(
        "--hour",
        type=int,
        default=DEFAULT_FAMILY_CALENDAR_PLANNER_HOUR,
    )
    parser.add_argument(
        "--minute",
        type=int,
        default=DEFAULT_FAMILY_CALENDAR_PLANNER_MINUTE,
    )
    parser.add_argument("--python-path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--runner-path", type=Path, help=argparse.SUPPRESS)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    output: TextIO | None = None,
    preview_builder: PreviewBuilder = build_family_calendar_planner_preview,
) -> int:
    stream = sys.stdout if output is None else output
    arguments = build_parser().parse_args(argv)
    result = preview_builder(
        python_path=arguments.python_path
        or DEFAULT_FAMILY_CALENDAR_PLANNER_PYTHON_PATH,
        runner_path=arguments.runner_path
        or DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
        hour=arguments.hour,
        minute=arguments.minute,
    )
    print(
        json.dumps(result.safe_document(), ensure_ascii=False, sort_keys=True),
        file=stream,
    )
    return 0 if result.status == "preview" else 1


if __name__ == "__main__":
    raise SystemExit(main())
