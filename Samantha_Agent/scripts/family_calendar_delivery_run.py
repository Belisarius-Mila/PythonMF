#!/usr/bin/env python3
"""Launchd-facing dispatcher for the configured family-calendar mode."""

from __future__ import annotations

import argparse
import json
import io
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TextIO


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.family_calendar_delivery_config import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    DeliveryConfigMode,
    FamilyCalendarDeliveryConfig,
    load_family_calendar_delivery_config,
)
from scripts.family_calendar_delivery_automatic import main as automatic_main
from scripts.family_calendar_delivery_dry_run import main as operational_dry_run_main


ModeMain = Callable[..., int]
ConfigLoader = Callable[[Path], FamilyCalendarDeliveryConfig]


def main(
    argv: Sequence[str] | None = None,
    *,
    output: TextIO | None = None,
    dry_run_main: ModeMain = operational_dry_run_main,
    enabled_main: ModeMain = automatic_main,
    config_loader: ConfigLoader = load_family_calendar_delivery_config,
) -> int:
    """Dispatch without reading Keychain or constructing SMTP outside enabled mode."""

    stream = sys.stdout if output is None else output
    try:
        arguments = _mode_parser().parse_known_args(argv)[0]
        config = config_loader(
            arguments.config_path or DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH
        )
    except (Exception, SystemExit):  # noqa: BLE001 - details stay redacted.
        print(
            json.dumps({"status": "config_error", "redacted": True}, sort_keys=True),
            file=stream,
        )
        return 1
    if config.mode is DeliveryConfigMode.DRY_RUN:
        return dry_run_main(argv, output=stream)
    if config.mode is DeliveryConfigMode.ENABLED:
        return enabled_main(argv, output=stream)
    print(
        json.dumps(
            {
                "status": "disabled",
                "recipient_count": len(config.recipients),
                "keychain_read": False,
                "transport_called": False,
                "redacted": True,
            },
            sort_keys=True,
        ),
        file=stream,
    )
    return 0


def _mode_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-path", type=Path)
    return parser


def scheduled_main(argv=None, *, output=None, email_runner=main, sms_runner=None):
    """Keep SMS independent of email errors; custom/replay arguments never send SMS."""
    args = list(sys.argv[1:] if argv is None else argv)
    if args:
        return email_runner(args, output=output)
    from app.family_calendar_sms import run_calendar_sms
    try:
        sms = (sms_runner or run_calendar_sms)()
    except Exception:
        sms = {'status': 'unverified', 'redacted': True}
    captured = io.StringIO()
    try:
        code = email_runner(args, output=captured)
        result = json.loads(captured.getvalue())
        if not isinstance(result, dict):
            raise ValueError()
    except Exception:
        code, result = 1, {'status': 'runtime_error', 'redacted': True}
    print(json.dumps({**result, 'sms': sms}, ensure_ascii=False), file=output or sys.stdout)
    return code


if __name__ == "__main__":
    raise SystemExit(scheduled_main())
