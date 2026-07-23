#!/usr/bin/env python3
"""Preview or explicitly create the dry-run family-calendar LaunchAgent plist."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence, TextIO


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.family_calendar_delivery_config import (  # noqa: E402
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
)
from app.family_calendar_delivery_planner_install import (  # noqa: E402
    FamilyCalendarPlannerInstallError,
    apply_family_calendar_planner_install,
    plan_family_calendar_planner_install,
)
from app.family_calendar_delivery_planner_preview import (  # noqa: E402
    DEFAULT_FAMILY_CALENDAR_PLANNER_HOUR,
    DEFAULT_FAMILY_CALENDAR_PLANNER_MINUTE,
    DEFAULT_FAMILY_CALENDAR_PLANNER_PYTHON_PATH,
)
from app.family_calendar_delivery_readiness import (  # noqa: E402
    DEFAULT_FAMILY_CALENDAR_PLANNER_PATH,
    DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Preview or explicitly create the family-calendar dry-run plist "
            "without loading it."
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
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirmation", default="")
    parser.add_argument("--expected-fingerprint", default="")
    parser.add_argument("--target-path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--config-path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--python-path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--runner-path", type=Path, help=argparse.SUPPRESS)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    output: TextIO | None = None,
) -> int:
    stream = sys.stdout if output is None else output
    arguments = build_parser().parse_args(argv)
    target_path = arguments.target_path or DEFAULT_FAMILY_CALENDAR_PLANNER_PATH
    plan = None
    try:
        plan = plan_family_calendar_planner_install(
            target_path=target_path,
            config_path=(
                arguments.config_path
                or DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH
            ),
            python_path=(
                arguments.python_path
                or DEFAULT_FAMILY_CALENDAR_PLANNER_PYTHON_PATH
            ),
            runner_path=(
                arguments.runner_path
                or DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH
            ),
            hour=arguments.hour,
            minute=arguments.minute,
        )
        if not arguments.apply:
            print(
                json.dumps(plan.safe_document(), ensure_ascii=False, sort_keys=True),
                file=stream,
            )
            return 0
        result = apply_family_calendar_planner_install(
            plan,
            confirmation=arguments.confirmation,
            expected_fingerprint=arguments.expected_fingerprint,
        )
    except FamilyCalendarPlannerInstallError:
        writes_performed = bool(
            arguments.apply
            and plan is not None
            and plan.target_path.is_file()
            and not plan.target_path.is_symlink()
        )
        print(
            json.dumps(
                {
                    "status": "failed",
                    "writes_performed": writes_performed,
                    "install_called": arguments.apply,
                    "launchctl_called": False,
                    "secret_read": False,
                    "transport_called": False,
                    "redacted": True,
                },
                sort_keys=True,
            ),
            file=stream,
        )
        return 1
    print(
        json.dumps(result.safe_document(), ensure_ascii=False, sort_keys=True),
        file=stream,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
