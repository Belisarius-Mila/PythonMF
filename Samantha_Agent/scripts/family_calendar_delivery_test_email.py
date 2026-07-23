#!/usr/bin/env python3
"""Preview or exactly confirm one shared iCloud family-calendar test email."""

from __future__ import annotations

import argparse
import getpass
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TextIO


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.family_calendar_delivery_config import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
)
from app.family_calendar_delivery_test_email import (
    FAMILY_CALENDAR_TEST_EMAIL_CONFIRMATION,
    FamilyCalendarTestEmailError,
    assert_family_calendar_test_email_plan_current,
    plan_family_calendar_test_email,
    require_family_calendar_test_email_confirmation,
    send_family_calendar_test_email,
)
from app.family_calendar_icloud_smtp_client import SMTPFactory, TLSContextFactory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview one family-calendar test email; send only after exact confirmation.",
    )
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--config-path", type=Path, help=argparse.SUPPRESS)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    secret_reader: Callable[[str], str] | None = None,
    confirmation_reader: Callable[[str], str] | None = None,
    smtp_factory: SMTPFactory | None = None,
    tls_context_factory: TLSContextFactory | None = None,
    output: TextIO | None = None,
) -> int:
    stream = sys.stdout if output is None else output
    read_secret = getpass.getpass if secret_reader is None else secret_reader
    read_confirmation = input if confirmation_reader is None else confirmation_reader
    arguments = build_parser().parse_args(argv)
    try:
        plan = plan_family_calendar_test_email(
            config_path=(
                arguments.config_path
                or DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH
            ),
        )
        print(json.dumps(plan.safe_document(), sort_keys=True), file=stream)
        if not arguments.send:
            return 0
        confirmation = read_confirmation(
            "Pro jeden společný testovací e-mail napiš přesně "
            f"{FAMILY_CALENDAR_TEST_EMAIL_CONFIRMATION}: "
        )
        require_family_calendar_test_email_confirmation(confirmation)
        assert_family_calendar_test_email_plan_current(plan)
        app_password = read_secret("iCloud app-specific heslo (skrytě): ")
        result = send_family_calendar_test_email(
            plan,
            confirmation=confirmation,
            app_password=app_password,
            smtp_factory=smtp_factory,
            tls_context_factory=tls_context_factory,
        )
    except (FamilyCalendarTestEmailError, EOFError, KeyboardInterrupt):
        print(
            json.dumps({"status": "failed", "redacted": True}, sort_keys=True),
            file=stream,
        )
        return 1
    print(json.dumps(result.safe_document(), sort_keys=True), file=stream)
    return 0 if result.status == "sent" else 1


if __name__ == "__main__":
    raise SystemExit(main())
