#!/usr/bin/env python3
"""Preview or explicitly enable family-calendar delivery dry-run mode."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence, TextIO


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.family_calendar_delivery_config import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
)
from app.family_calendar_delivery_config_transition import (
    DeliveryConfigTransitionError,
    apply_family_calendar_delivery_config_dry_run,
    plan_family_calendar_delivery_config_dry_run,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely enable family-calendar delivery dry-run mode.",
    )
    parser.add_argument("--path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirmation", default="")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    output: TextIO | None = None,
) -> int:
    stream = sys.stdout if output is None else output
    arguments = build_parser().parse_args(argv)
    path = (
        DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH
        if arguments.path is None
        else arguments.path
    )
    try:
        plan = plan_family_calendar_delivery_config_dry_run(path=path)
        if not arguments.apply:
            print(json.dumps(plan.safe_document(), sort_keys=True), file=stream)
            return 0
        result = apply_family_calendar_delivery_config_dry_run(
            plan,
            confirmation=arguments.confirmation,
        )
    except DeliveryConfigTransitionError:
        print(
            json.dumps({"status": "failed", "redacted": True}, sort_keys=True),
            file=stream,
        )
        return 1
    print(json.dumps(result.safe_document(), sort_keys=True), file=stream)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
