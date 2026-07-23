#!/usr/bin/env python3
"""Print a read-only launchctl bootstrap and rollback preview."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.family_calendar_delivery_config import (  # noqa: E402
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
)
from app.family_calendar_delivery_launchctl_preview import (  # noqa: E402
    ExecutableLocator,
    build_family_calendar_launchctl_preview,
)
from app.family_calendar_delivery_readiness import (  # noqa: E402
    DEFAULT_FAMILY_CALENDAR_PLANNER_PATH,
    DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Preview exact family-calendar launchctl bootstrap, verification, "
            "and rollback commands without executing them."
        ),
    )
    parser.add_argument("--config-path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--planner-path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--planner-runner-path", type=Path, help=argparse.SUPPRESS)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    executable_locator: ExecutableLocator | None = None,
    output: TextIO | None = None,
) -> int:
    stream = sys.stdout if output is None else output
    arguments = build_parser().parse_args(argv)
    kwargs = {
        "config_path": (
            arguments.config_path
            or DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH
        ),
        "planner_path": (
            arguments.planner_path or DEFAULT_FAMILY_CALENDAR_PLANNER_PATH
        ),
        "planner_runner_path": (
            arguments.planner_runner_path
            or DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH
        ),
    }
    if executable_locator is not None:
        kwargs["executable_locator"] = executable_locator
    result = build_family_calendar_launchctl_preview(**kwargs)
    print(
        json.dumps(result.safe_document(), ensure_ascii=False, sort_keys=True),
        file=stream,
    )
    return 0 if result.status == "preview" else 1


if __name__ == "__main__":
    raise SystemExit(main())
