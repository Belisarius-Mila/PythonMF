#!/usr/bin/env python3
"""Validate the iCloud SMTP envelope, then RSET without issuing DATA."""

from __future__ import annotations

import argparse
import getpass
import json
import smtplib
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
    FamilyCalendarTestEmailError,
    plan_family_calendar_test_email,
)
from app.family_calendar_icloud_smtp_client import (
    ICloudSMTPClient,
    ICloudSMTPClientError,
    ICloudSMTPDiagnosticCategory,
    SMTPFactory,
    TLSContextFactory,
    create_icloud_tls_context,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate iCloud SMTP MAIL FROM and four RCPT TO commands, "
            "then RSET without DATA or message content."
        ),
    )
    parser.add_argument("--config-path", type=Path, help=argparse.SUPPRESS)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    secret_reader: Callable[[str], str] | None = None,
    smtp_factory: SMTPFactory | None = None,
    tls_context_factory: TLSContextFactory | None = None,
    output: TextIO | None = None,
) -> int:
    stream = sys.stdout if output is None else output
    read_secret = getpass.getpass if secret_reader is None else secret_reader
    arguments = build_parser().parse_args(argv)
    try:
        plan = plan_family_calendar_test_email(
            config_path=(
                arguments.config_path
                or DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH
            ),
        )
    except FamilyCalendarTestEmailError:
        return _print_failure(stream, category="CONFIGURATION_FAILED")
    try:
        app_password = read_secret("iCloud app-specific heslo (skrytě): ")
    except (EOFError, KeyboardInterrupt):
        return _print_failure(stream, category="CREDENTIAL_INPUT_FAILED")
    try:
        client = ICloudSMTPClient(
            username=plan.config.sender_address,
            app_password=app_password,
            smtp_factory=smtplib.SMTP if smtp_factory is None else smtp_factory,
            tls_context_factory=(
                create_icloud_tls_context
                if tls_context_factory is None
                else tls_context_factory
            ),
        )
    except ICloudSMTPClientError:
        return _print_failure(stream, category="CREDENTIAL_VALIDATION_FAILED")
    try:
        result = client.diagnose_envelope(
            from_addr=plan.config.sender_address,
            to_addrs=tuple(
                recipient.address for recipient in plan.config.recipients
            ),
        )
    except ICloudSMTPClientError:
        return _print_failure(stream, category="ENVELOPE_VALIDATION_FAILED")
    print(json.dumps(result.safe_document(), sort_keys=True), file=stream)
    return 0 if result.succeeded else 1


def _print_failure(stream: TextIO, *, category: str) -> int:
    safe_categories = {
        "CONFIGURATION_FAILED",
        "CREDENTIAL_INPUT_FAILED",
        "CREDENTIAL_VALIDATION_FAILED",
        "ENVELOPE_VALIDATION_FAILED",
    }
    if category not in safe_categories:
        category = ICloudSMTPDiagnosticCategory.OTHER_REDACTED.value
    print(
        json.dumps(
            {
                "accepted_recipient_count": 0,
                "category": category,
                "data_called": False,
                "recipient_count": 4,
                "redacted": True,
                "rejected_recipient_count": 0,
                "rset_ok": None,
                "send_called": False,
                "session_close_ok": None,
                "status": "diagnostic",
                "unknown_recipient_count": 4,
            },
            sort_keys=True,
        ),
        file=stream,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
