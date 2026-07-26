"""Redacted runtime reader for the family-calendar SMTP Keychain secret."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

from app.family_calendar_delivery_readiness import (
    FAMILY_CALENDAR_KEYCHAIN_ACCOUNT,
    FAMILY_CALENDAR_KEYCHAIN_SERVICE,
)


class FamilyCalendarKeychainError(RuntimeError):
    """Raised when the runtime credential cannot be read safely."""


CommandOutputRunner = Callable[[Sequence[str]], tuple[int, str]]
ExecutableLocator = Callable[[str], str | None]


def read_family_calendar_app_password(
    *,
    command_runner: CommandOutputRunner | None = None,
    executable_locator: ExecutableLocator = shutil.which,
) -> str:
    """Read the fixed Keychain item without exposing its value in arguments or errors."""

    locator_failed = False
    try:
        security_path = _security_executable(executable_locator)
    except FamilyCalendarKeychainError:
        raise
    except Exception:  # noqa: BLE001 - locator details must stay redacted.
        locator_failed = True
        security_path = None
    if locator_failed or security_path is None:
        raise FamilyCalendarKeychainError("macOS security CLI is unavailable.")
    runner = command_runner or _run_command_output
    argv = (
        str(security_path),
        "find-generic-password",
        "-w",
        "-s",
        FAMILY_CALENDAR_KEYCHAIN_SERVICE,
        "-a",
        FAMILY_CALENDAR_KEYCHAIN_ACCOUNT,
    )
    command_failed = False
    result: object = None
    try:
        result = runner(argv)
    except Exception:  # noqa: BLE001 - command details must stay redacted.
        command_failed = True
    if command_failed:
        raise FamilyCalendarKeychainError(
            "Family-calendar SMTP credential could not be read safely."
        )
    if (
        not isinstance(result, tuple)
        or len(result) != 2
        or type(result[0]) is not int
        or not isinstance(result[1], str)
    ):
        raise FamilyCalendarKeychainError(
            "Family-calendar SMTP credential could not be read safely."
        )
    return_code, stdout = result
    if return_code != 0:
        raise FamilyCalendarKeychainError(
            "Family-calendar SMTP credential is unavailable."
        )

    secret = stdout.rstrip("\r\n")
    if (
        not secret
        or secret != secret.strip()
        or "\r" in secret
        or "\n" in secret
    ):
        raise FamilyCalendarKeychainError(
            "Family-calendar SMTP credential is invalid."
        )
    return secret


def _security_executable(executable_locator: ExecutableLocator) -> Path:
    raw = executable_locator("security")
    if not raw:
        raise FamilyCalendarKeychainError("macOS security CLI is unavailable.")
    path = Path(raw).expanduser().resolve()
    if not path.is_absolute() or not path.is_file() or not os.access(path, os.X_OK):
        raise FamilyCalendarKeychainError("macOS security CLI is unsafe.")
    return path


def _run_command_output(argv: Sequence[str]) -> tuple[int, str]:
    completed = subprocess.run(
        tuple(argv),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
        text=True,
        timeout=10,
    )
    return int(completed.returncode), completed.stdout
