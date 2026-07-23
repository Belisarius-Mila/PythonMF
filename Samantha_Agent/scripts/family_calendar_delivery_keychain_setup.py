#!/usr/bin/env python3
"""Preview or explicitly create the family-calendar Keychain reference."""

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
from app.family_calendar_delivery_keychain_setup import (  # noqa: E402
    FAMILY_CALENDAR_KEYCHAIN_SETUP_CONFIRMATION,
    CommandStatusRunner,
    ExecutableLocator,
    FamilyCalendarKeychainSetupError,
    InteractiveCommandRunner,
    apply_family_calendar_keychain_setup,
    plan_family_calendar_keychain_setup,
)


SAFE_FAILURE_STAGES = frozenset(
    {
        "preview",
        "confirmation_input",
        "confirmation",
        "plan_recheck",
        "keychain_write",
        "verification",
    }
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Preview or explicitly create the family-calendar Keychain "
            "credential reference without exposing the password."
        ),
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--config-path", type=Path, help=argparse.SUPPRESS)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    confirmation_reader: Callable[[str], str] | None = None,
    command_runner: CommandStatusRunner | None = None,
    credential_writer: InteractiveCommandRunner | None = None,
    executable_locator: ExecutableLocator | None = None,
    output: TextIO | None = None,
) -> int:
    stream = sys.stdout if output is None else output
    read_confirmation = input if confirmation_reader is None else confirmation_reader
    arguments = build_parser().parse_args(argv)
    plan_kwargs = {
        "config_path": (
            arguments.config_path
            or DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH
        ),
    }
    if command_runner is not None:
        plan_kwargs["command_runner"] = command_runner
    if executable_locator is not None:
        plan_kwargs["executable_locator"] = executable_locator
    try:
        plan = plan_family_calendar_keychain_setup(**plan_kwargs)
    except FamilyCalendarKeychainSetupError as exc:
        return _print_failure(
            stream,
            stage=exc.stage,
            write_attempted=exc.write_attempted,
        )
    print(json.dumps(plan.safe_document(), ensure_ascii=False, sort_keys=True), file=stream)
    if not arguments.apply:
        return 0
    try:
        confirmation = read_confirmation(
            "Pro create-only uložení app-specific hesla napiš přesně "
            f"{FAMILY_CALENDAR_KEYCHAIN_SETUP_CONFIRMATION}: "
        )
    except (EOFError, KeyboardInterrupt):
        return _print_failure(
            stream,
            stage="confirmation_input",
            write_attempted=False,
        )
    apply_kwargs = {
        "confirmation": confirmation,
    }
    if command_runner is not None:
        apply_kwargs["command_runner"] = command_runner
    if credential_writer is not None:
        apply_kwargs["credential_writer"] = credential_writer
    if executable_locator is not None:
        apply_kwargs["executable_locator"] = executable_locator
    try:
        result = apply_family_calendar_keychain_setup(plan, **apply_kwargs)
    except FamilyCalendarKeychainSetupError as exc:
        return _print_failure(
            stream,
            stage=exc.stage,
            write_attempted=exc.write_attempted,
        )
    print(json.dumps(result.safe_document(), ensure_ascii=False, sort_keys=True), file=stream)
    return 0


def _print_failure(
    stream: TextIO,
    *,
    stage: str,
    write_attempted: bool,
) -> int:
    safe_stage = stage if stage in SAFE_FAILURE_STAGES else "keychain_write"
    print(
        json.dumps(
            {
                "status": "failed",
                "failure_stage": safe_stage,
                "write_attempted": bool(write_attempted),
                "write_outcome_unknown": bool(write_attempted),
                "retry_safe": not bool(write_attempted),
                "secret_output": False,
                "launchctl_called": False,
                "transport_called": False,
                "redacted": True,
            },
            sort_keys=True,
        ),
        file=stream,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
