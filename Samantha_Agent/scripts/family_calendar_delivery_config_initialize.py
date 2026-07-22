#!/usr/bin/env python3
"""Interactively create a disabled private family-calendar delivery config."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import stat
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import TextIO


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.family_calendar_delivery_config import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
)
from app.family_calendar_delivery_config_initializer import (
    DELIVERY_CONFIG_INITIALIZATION_CONFIRMATION,
    DeliveryConfigInitializationError,
    apply_family_calendar_delivery_config_initialization,
    assert_family_calendar_delivery_config_can_be_initialized,
    plan_family_calendar_delivery_config_initialization,
)


SENDER_ENVIRONMENT_KEYS = {
    "icloud": "ICLOUD_MAIL_ADDRESS",
    "seznam": "SEZNAM_MAIL_ADDRESS",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a disabled private family-calendar delivery config.",
    )
    parser.add_argument("--provider", choices=tuple(SENDER_ENVIRONMENT_KEYS), required=True)
    parser.add_argument("--path", type=Path, help=argparse.SUPPRESS)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    environment: Mapping[str, str] | None = None,
    local_environment_path: Path | None = None,
    secret_reader: Callable[[str], str] | None = None,
    confirmation_reader: Callable[[str], str] | None = None,
    output: TextIO | None = None,
) -> int:
    stream = sys.stdout if output is None else output
    read_secret = getpass.getpass if secret_reader is None else secret_reader
    read_confirmation = input if confirmation_reader is None else confirmation_reader
    arguments = build_parser().parse_args(argv)
    path = (
        DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH
        if arguments.path is None
        else arguments.path
    )
    source_environment = os.environ if environment is None else environment
    try:
        assert_family_calendar_delivery_config_can_be_initialized(path=path)
        sender_key = SENDER_ENVIRONMENT_KEYS[arguments.provider]
        sender_address = source_environment.get(sender_key, "")
        if environment is None and (
            not isinstance(sender_address, str) or not sender_address.strip()
        ):
            sender_address = _read_private_environment_value(
                PROJECT_ROOT / ".env"
                if local_environment_path is None
                else Path(local_environment_path),
                sender_key,
            )
        if not isinstance(sender_address, str) or not sender_address.strip():
            raise DeliveryConfigInitializationError(
                "The local sender address required for initialization is unavailable."
            )
        recipient_addresses = _read_recipient_addresses(read_secret)
        plan = plan_family_calendar_delivery_config_initialization(
            smtp_provider=arguments.provider,
            sender_address=sender_address.strip(),
            recipient_addresses=recipient_addresses,
            path=path,
        )
        print(json.dumps(plan.safe_document(), sort_keys=True), file=stream)
        confirmation = read_confirmation(
            f"Pro vytvoření napiš přesně {DELIVERY_CONFIG_INITIALIZATION_CONFIRMATION}: "
        )
        result = apply_family_calendar_delivery_config_initialization(
            plan,
            confirmation=confirmation,
        )
    except (DeliveryConfigInitializationError, EOFError, KeyboardInterrupt):
        print(
            json.dumps({"status": "failed", "redacted": True}, sort_keys=True),
            file=stream,
        )
        return 1
    print(json.dumps(result.safe_document(), sort_keys=True), file=stream)
    return 0


def _read_private_environment_value(path: Path, key: str) -> str:
    """Read one exact value from a private dotenv file without exporting it."""

    target = Path(path)
    file_descriptor: int | None = None
    try:
        open_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            file_descriptor = os.open(target, open_flags)
        except FileNotFoundError:
            return ""
        file_status = os.fstat(file_descriptor)
        if not stat.S_ISREG(file_status.st_mode):
            raise DeliveryConfigInitializationError(
                "The local sender environment source is unsafe."
            )
        mode = stat.S_IMODE(file_status.st_mode)
        if mode & 0o077 or not mode & stat.S_IRUSR:
            raise DeliveryConfigInitializationError(
                "The local sender environment source is unsafe."
            )
        matches: list[str] = []
        with os.fdopen(file_descriptor, "r", encoding="utf-8") as handle:
            file_descriptor = None
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("export "):
                    line = line[len("export ") :].lstrip()
                name, separator, raw_value = line.partition("=")
                if separator and name.strip() == key:
                    matches.append(_private_environment_scalar(raw_value))
    except DeliveryConfigInitializationError:
        raise
    except (OSError, UnicodeError) as exc:
        raise DeliveryConfigInitializationError(
            "The local sender environment source is unavailable."
        ) from exc
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
    if len(matches) > 1:
        raise DeliveryConfigInitializationError(
            "The local sender environment source is ambiguous."
        )
    return matches[0] if matches else ""


def _private_environment_scalar(raw_value: str) -> str:
    value = str(raw_value).strip()
    if not value:
        return ""
    if value[0] in {"'", '"'}:
        quote = value[0]
        if len(value) < 2 or value[-1] != quote:
            raise DeliveryConfigInitializationError(
                "The local sender environment source is invalid."
            )
        return value[1:-1]
    return value.split(" #", 1)[0].strip()


def _read_recipient_addresses(
    secret_reader: Callable[[str], str],
) -> tuple[str, str, str, str]:
    addresses: list[str] = []
    for index in range(1, 5):
        first = secret_reader(f"Adresa příjemce {index} (skrytě): ")
        second = secret_reader(f"Zopakuj adresu příjemce {index} (skrytě): ")
        if first != second:
            raise DeliveryConfigInitializationError(
                "Repeated local recipient address does not match."
            )
        addresses.append(first)
    return (addresses[0], addresses[1], addresses[2], addresses[3])


if __name__ == "__main__":
    raise SystemExit(main())
