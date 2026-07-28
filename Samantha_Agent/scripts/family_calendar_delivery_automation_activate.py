#!/usr/bin/env python3
"""Preview or exactly confirm family-calendar automation activation."""

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

from app.family_calendar_delivery_automation_activation import (  # noqa: E402
    FamilyCalendarAutomationActivationError,
    apply_family_calendar_automation_activation,
    plan_family_calendar_automation_activation,
)
from app.family_calendar_delivery_config import (  # noqa: E402
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
)
from app.family_calendar_delivery_launchctl_preview import (  # noqa: E402
    ExecutableLocator,
)
from app.family_calendar_delivery_readiness import (  # noqa: E402
    DEFAULT_FAMILY_CALENDAR_PLANNER_PATH,
    DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
    CommandStatusRunner,
)
from app.family_calendar_delivery_store import (  # noqa: E402
    DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Preview or exactly confirm the fail-closed dry-run-to-enabled "
            "family-calendar activation."
        ),
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--global-confirmation", default="")
    parser.add_argument("--confirmation", default="")
    parser.add_argument("--expected-fingerprint", default="")
    parser.add_argument("--config-path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--state-path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--planner-path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--planner-runner-path", type=Path, help=argparse.SUPPRESS)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    command_runner: CommandStatusRunner | None = None,
    executable_locator: ExecutableLocator | None = None,
    output: TextIO | None = None,
) -> int:
    stream = sys.stdout if output is None else output
    arguments = build_parser().parse_args(argv)
    plan_kwargs = {
        "config_path": (
            arguments.config_path
            or DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH
        ),
        "state_path": (
            arguments.state_path or DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH
        ),
        "planner_path": (
            arguments.planner_path or DEFAULT_FAMILY_CALENDAR_PLANNER_PATH
        ),
        "planner_runner_path": (
            arguments.planner_runner_path
            or DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH
        ),
    }
    if command_runner is not None:
        plan_kwargs["command_runner"] = command_runner
    if executable_locator is not None:
        plan_kwargs["executable_locator"] = executable_locator
    try:
        plan = plan_family_calendar_automation_activation(**plan_kwargs)
    except FamilyCalendarAutomationActivationError as exc:
        print(json.dumps(exc.safe_document(), sort_keys=True), file=stream)
        return 1

    print(
        json.dumps(plan.safe_document(), ensure_ascii=False, sort_keys=True),
        file=stream,
    )
    if not arguments.apply:
        return 0

    apply_kwargs = {
        "global_confirmation": arguments.global_confirmation,
        "confirmation": arguments.confirmation,
        "expected_fingerprint": arguments.expected_fingerprint,
    }
    if command_runner is not None:
        apply_kwargs["command_runner"] = command_runner
    if executable_locator is not None:
        apply_kwargs["executable_locator"] = executable_locator
    try:
        result = apply_family_calendar_automation_activation(
            plan,
            **apply_kwargs,
        )
    except FamilyCalendarAutomationActivationError as exc:
        print(json.dumps(exc.safe_document(), sort_keys=True), file=stream)
        return 1
    print(
        json.dumps(result.safe_document(), ensure_ascii=False, sort_keys=True),
        file=stream,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
