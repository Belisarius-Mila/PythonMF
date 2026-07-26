#!/usr/bin/env python3
"""Launchd-facing dispatcher for the configured family-calendar mode."""

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


if __name__ == "__main__":
    raise SystemExit(main())
