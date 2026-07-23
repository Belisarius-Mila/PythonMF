"""Two-step, create-only Keychain setup for family-calendar SMTP credentials."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from app.family_calendar_delivery_config import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    DeliveryConfigMode,
    load_family_calendar_delivery_config,
)
from app.family_calendar_delivery_readiness import (
    FAMILY_CALENDAR_KEYCHAIN_ACCOUNT,
    FAMILY_CALENDAR_KEYCHAIN_SERVICE,
)


FAMILY_CALENDAR_KEYCHAIN_LABEL = "Samantha Rodinný kalendář SMTP"
FAMILY_CALENDAR_KEYCHAIN_SETUP_CONFIRMATION = (
    "STORE_FAMILY_CALENDAR_APP_PASSWORD_IN_KEYCHAIN"
)
_PLAN_VERSION = b"family-calendar-keychain-setup-v1"

CommandStatusRunner = Callable[[Sequence[str]], int]
InteractiveCommandRunner = Callable[[Sequence[str]], int]
ExecutableLocator = Callable[[str], str | None]


class FamilyCalendarKeychainSetupError(RuntimeError):
    """Raised when the Keychain item cannot be planned or created safely."""

    def __init__(
        self,
        message: str,
        *,
        stage: str = "preview",
        write_attempted: bool = False,
    ) -> None:
        super().__init__(message)
        self.stage = str(stage)
        self.write_attempted = bool(write_attempted)


@dataclass(frozen=True, repr=False)
class FamilyCalendarKeychainSetupPlan:
    security_path: Path
    config_path: Path
    config_digest: bytes
    fingerprint: str

    def __repr__(self) -> str:
        return (
            "FamilyCalendarKeychainSetupPlan("
            f"status='preview', fingerprint={self.fingerprint[:12]!r}, "
            "create_only=True, redacted=True)"
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "status": "preview",
            "service": FAMILY_CALENDAR_KEYCHAIN_SERVICE,
            "account": FAMILY_CALENDAR_KEYCHAIN_ACCOUNT,
            "label": FAMILY_CALENDAR_KEYCHAIN_LABEL,
            "config_mode": "dry_run",
            "smtp_provider": "icloud",
            "create_only": True,
            "confirmation_required": True,
            "required_confirmation": (
                FAMILY_CALENDAR_KEYCHAIN_SETUP_CONFIRMATION
            ),
            "password_input": "hidden_security_prompt",
            "secret_passed_in_arguments": False,
            "plan_fingerprint": self.fingerprint,
            "writes_performed": False,
            "keychain_write_called": False,
            "launchctl_called": False,
            "transport_called": False,
            "redacted": True,
        }


@dataclass(frozen=True, repr=False)
class FamilyCalendarKeychainSetupResult:
    fingerprint: str

    def __repr__(self) -> str:
        return (
            "FamilyCalendarKeychainSetupResult("
            f"status='created', fingerprint={self.fingerprint[:12]!r}, "
            "redacted=True)"
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "status": "created",
            "service": FAMILY_CALENDAR_KEYCHAIN_SERVICE,
            "account": FAMILY_CALENDAR_KEYCHAIN_ACCOUNT,
            "label": FAMILY_CALENDAR_KEYCHAIN_LABEL,
            "create_only": True,
            "credential_reference_present": True,
            "password_input": "hidden_security_prompt",
            "secret_passed_in_arguments": False,
            "secret_output": False,
            "plan_fingerprint": self.fingerprint,
            "writes_performed": True,
            "keychain_write_called": True,
            "launchctl_called": False,
            "transport_called": False,
            "redacted": True,
        }


def plan_family_calendar_keychain_setup(
    *,
    config_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    command_runner: CommandStatusRunner | None = None,
    executable_locator: ExecutableLocator = shutil.which,
) -> FamilyCalendarKeychainSetupPlan:
    """Return a redacted no-write plan for one missing Keychain reference."""

    run_status = command_runner or _run_command_status
    target_config = Path(config_path)
    security_path = _security_executable(executable_locator)
    try:
        digest_before = _file_digest(target_config)
        config = load_family_calendar_delivery_config(target_config)
        digest_after = _file_digest(target_config)
    except Exception as exc:  # noqa: BLE001 - private configuration stays redacted.
        raise FamilyCalendarKeychainSetupError(
            "Family-calendar Keychain setup configuration is unavailable."
        ) from exc
    if digest_before != digest_after:
        raise FamilyCalendarKeychainSetupError(
            "Family-calendar configuration changed during Keychain preview."
        )
    if config.mode is not DeliveryConfigMode.DRY_RUN:
        raise FamilyCalendarKeychainSetupError(
            "Family-calendar Keychain setup requires dry-run configuration."
        )
    if config.smtp_provider != "icloud":
        raise FamilyCalendarKeychainSetupError(
            "Family-calendar Keychain setup requires the iCloud SMTP provider."
        )
    status = _credential_reference_status(
        security_path=security_path,
        command_runner=run_status,
    )
    if status == 0:
        raise FamilyCalendarKeychainSetupError(
            "Family-calendar Keychain reference already exists."
        )
    if status != 44:
        raise FamilyCalendarKeychainSetupError(
            "Family-calendar Keychain reference cannot be checked safely."
        )
    fingerprint = _plan_fingerprint(
        security_path=security_path,
        config_digest=digest_after,
    )
    return FamilyCalendarKeychainSetupPlan(
        security_path=security_path,
        config_path=target_config,
        config_digest=digest_after,
        fingerprint=fingerprint,
    )


def apply_family_calendar_keychain_setup(
    plan: FamilyCalendarKeychainSetupPlan,
    *,
    confirmation: str,
    command_runner: CommandStatusRunner | None = None,
    credential_writer: InteractiveCommandRunner | None = None,
    executable_locator: ExecutableLocator = shutil.which,
) -> FamilyCalendarKeychainSetupResult:
    """Prompt through ``security`` and create one unchanged Keychain item."""

    if not isinstance(plan, FamilyCalendarKeychainSetupPlan):
        raise FamilyCalendarKeychainSetupError(
            "A validated family-calendar Keychain plan is required.",
            stage="plan_recheck",
        )
    if confirmation != FAMILY_CALENDAR_KEYCHAIN_SETUP_CONFIRMATION:
        raise FamilyCalendarKeychainSetupError(
            "Exact family-calendar Keychain confirmation is required.",
            stage="confirmation",
        )
    run_status = command_runner or _run_command_status
    write_credential = credential_writer or _run_interactive_keychain_write
    try:
        current = plan_family_calendar_keychain_setup(
            config_path=plan.config_path,
            command_runner=run_status,
            executable_locator=executable_locator,
        )
    except FamilyCalendarKeychainSetupError as exc:
        raise FamilyCalendarKeychainSetupError(
            "Family-calendar Keychain setup inputs changed after preview.",
            stage="plan_recheck",
        ) from exc
    if (
        current.fingerprint != plan.fingerprint
        or current.security_path != plan.security_path
        or current.config_digest != plan.config_digest
    ):
        raise FamilyCalendarKeychainSetupError(
            "Family-calendar Keychain setup fingerprint changed after preview.",
            stage="plan_recheck",
        )
    command = (
        str(current.security_path),
        "add-generic-password",
        "-s",
        FAMILY_CALENDAR_KEYCHAIN_SERVICE,
        "-a",
        FAMILY_CALENDAR_KEYCHAIN_ACCOUNT,
        "-l",
        FAMILY_CALENDAR_KEYCHAIN_LABEL,
        "-w",
    )
    try:
        write_status = int(write_credential(command))
    except Exception as exc:  # noqa: BLE001 - credential details stay outside output.
        raise FamilyCalendarKeychainSetupError(
            "Family-calendar Keychain write outcome is unknown.",
            stage="keychain_write",
            write_attempted=True,
        ) from exc
    if write_status != 0:
        raise FamilyCalendarKeychainSetupError(
            "Family-calendar Keychain write was not confirmed.",
            stage="keychain_write",
            write_attempted=True,
        )
    if (
        _credential_reference_status(
            security_path=current.security_path,
            command_runner=run_status,
        )
        != 0
    ):
        raise FamilyCalendarKeychainSetupError(
            "Family-calendar Keychain reference could not be verified.",
            stage="verification",
            write_attempted=True,
        )
    return FamilyCalendarKeychainSetupResult(fingerprint=current.fingerprint)


def _security_executable(executable_locator: ExecutableLocator) -> Path:
    raw = executable_locator("security")
    if not raw:
        raise FamilyCalendarKeychainSetupError(
            "macOS security CLI is unavailable."
        )
    path = Path(raw).expanduser().resolve()
    if not path.is_absolute() or not path.is_file() or not os.access(path, os.X_OK):
        raise FamilyCalendarKeychainSetupError(
            "macOS security CLI is unsafe."
        )
    return path


def _credential_reference_status(
    *,
    security_path: Path,
    command_runner: CommandStatusRunner,
) -> int:
    return int(
        command_runner(
            (
                str(security_path),
                "find-generic-password",
                "-s",
                FAMILY_CALENDAR_KEYCHAIN_SERVICE,
                "-a",
                FAMILY_CALENDAR_KEYCHAIN_ACCOUNT,
            )
        )
    )


def _plan_fingerprint(*, security_path: Path, config_digest: bytes) -> str:
    digest = hashlib.sha256()
    for value in (
        _PLAN_VERSION,
        str(security_path).encode("utf-8"),
        FAMILY_CALENDAR_KEYCHAIN_SERVICE.encode("utf-8"),
        FAMILY_CALENDAR_KEYCHAIN_ACCOUNT.encode("utf-8"),
        FAMILY_CALENDAR_KEYCHAIN_LABEL.encode("utf-8"),
        config_digest,
    ):
        digest.update(len(value).to_bytes(8, "big"))
        digest.update(value)
    return digest.hexdigest()


def _file_digest(path: Path) -> bytes:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.digest()


def _run_command_status(argv: Sequence[str]) -> int:
    completed = subprocess.run(
        tuple(argv),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=5,
    )
    return int(completed.returncode)


def _run_interactive_keychain_write(argv: Sequence[str]) -> int:
    completed = subprocess.run(
        tuple(argv),
        stdout=subprocess.DEVNULL,
        check=False,
    )
    return int(completed.returncode)
