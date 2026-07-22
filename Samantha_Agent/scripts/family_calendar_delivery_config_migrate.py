#!/usr/bin/env python3
"""Preview or explicitly apply the private family-calendar config migration."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TextIO


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.family_calendar_delivery_config_migration_runner import (
    LocalDeliveryConfigMigrationRunnerError,
    run_local_family_calendar_delivery_config_migration,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely preview the family-calendar delivery-config migration.",
    )
    parser.add_argument("--path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirmation", default="")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    environment: Mapping[str, str] | None = None,
    output: TextIO | None = None,
) -> int:
    stream = sys.stdout if output is None else output
    arguments = build_parser().parse_args(argv)
    options: dict[str, object] = {
        "apply": arguments.apply,
        "confirmation": arguments.confirmation,
        "environment": environment,
    }
    if arguments.path is not None:
        options["path"] = arguments.path
    try:
        result = run_local_family_calendar_delivery_config_migration(**options)
    except LocalDeliveryConfigMigrationRunnerError:
        print(
            json.dumps({"status": "failed", "redacted": True}, sort_keys=True),
            file=stream,
        )
        return 1
    print(json.dumps(result.safe_document(), sort_keys=True), file=stream)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
