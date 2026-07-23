"""Read-only readiness audit for future family-calendar automation."""

from __future__ import annotations

import json
import os
import plistlib
import shutil
import stat
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from app.family_calendar_delivery import DeliveryState
from app.family_calendar_delivery_config import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    DeliveryConfigMode,
    load_family_calendar_delivery_config,
)
from app.family_calendar_delivery_store import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
    load_delivery_records,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FAMILY_CALENDAR_PLANNER_LABEL = "com.miloslavfalta.samantha.family-calendar"
FAMILY_CALENDAR_KEYCHAIN_SERVICE = "com.miloslavfalta.samantha.family-calendar.smtp"
FAMILY_CALENDAR_KEYCHAIN_ACCOUNT = "smtp-app-password"
DEFAULT_FAMILY_CALENDAR_PLANNER_PATH = (
    Path.home()
    / "Library"
    / "LaunchAgents"
    / f"{FAMILY_CALENDAR_PLANNER_LABEL}.plist"
)
DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH = (
    PROJECT_ROOT / "scripts" / "family_calendar_delivery_run.py"
)
MAX_PLANNER_BYTES = 64_000


@dataclass(frozen=True)
class ReadinessCheck:
    name: str
    status: str
    code: str
    blocking: bool

    def safe_document(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status,
            "code": self.code,
            "blocking": self.blocking,
        }


@dataclass(frozen=True, repr=False)
class FamilyCalendarDeliveryReadinessResult:
    status: str
    ready_to_enable: bool
    automation_active: bool
    checks: tuple[ReadinessCheck, ...]
    config_mode: str
    recipient_count: int
    record_count: int
    sending_count: int
    delivery_unknown_count: int
    partial_count: int
    writes_performed: bool = False
    secret_read: bool = False
    transport_called: bool = False

    def __repr__(self) -> str:
        return (
            "FamilyCalendarDeliveryReadinessResult("
            f"status={self.status!r}, ready_to_enable={self.ready_to_enable!r}, "
            f"automation_active={self.automation_active!r}, "
            f"blocking_count={sum(check.blocking for check in self.checks)}, "
            f"record_count={self.record_count}, redacted=True)"
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "status": self.status,
            "ready_to_enable": self.ready_to_enable,
            "automation_active": self.automation_active,
            "blocking_count": sum(check.blocking for check in self.checks),
            "checks": [check.safe_document() for check in self.checks],
            "config_mode": self.config_mode,
            "recipient_count": self.recipient_count,
            "record_count": self.record_count,
            "sending_count": self.sending_count,
            "delivery_unknown_count": self.delivery_unknown_count,
            "partial_count": self.partial_count,
            "writes_performed": self.writes_performed,
            "secret_read": self.secret_read,
            "transport_called": self.transport_called,
            "redacted": True,
        }


CommandStatusRunner = Callable[[Sequence[str]], int]
ExecutableLocator = Callable[[str], str | None]
AutomaticModeProbe = Callable[[], bool]


def inspect_family_calendar_delivery_readiness(
    *,
    config_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    state_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
    planner_path: Path = DEFAULT_FAMILY_CALENDAR_PLANNER_PATH,
    planner_runner_path: Path = DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
    command_runner: CommandStatusRunner | None = None,
    executable_locator: ExecutableLocator = shutil.which,
    automatic_mode_probe: AutomaticModeProbe | None = None,
) -> FamilyCalendarDeliveryReadinessResult:
    """Inspect automation prerequisites without writes, secrets, or transport."""

    run_status = command_runner or _run_command_status
    mode_probe = automatic_mode_probe or _automatic_mode_available
    checks: list[ReadinessCheck] = []

    config = None
    config_mode = "unknown"
    recipient_count = 0
    try:
        config = load_family_calendar_delivery_config(Path(config_path))
    except Exception:  # noqa: BLE001 - private configuration details stay redacted.
        checks.append(_blocked("configuration", "configuration_invalid"))
    else:
        config_mode = config.mode.value
        recipient_count = len(config.recipients)
        checks.append(_ok("configuration", "configuration_valid"))
        enabled_mode = getattr(DeliveryConfigMode, "ENABLED", None)
        if config.mode is DeliveryConfigMode.DRY_RUN or (
            enabled_mode is not None and config.mode is enabled_mode
        ):
            checks.append(_ok("current_mode", "configuration_phase_ready"))
        else:
            checks.append(_blocked("current_mode", "configuration_not_dry_run"))

    automatic_mode_available = False
    try:
        automatic_mode_available = bool(mode_probe())
    except Exception:  # noqa: BLE001 - a probe failure remains a redacted blocker.
        checks.append(_blocked("automatic_mode", "automatic_mode_probe_failed"))
    else:
        checks.append(
            _ok("automatic_mode", "automatic_mode_available")
            if automatic_mode_available
            else _blocked("automatic_mode", "automatic_mode_unavailable")
        )

    checks.append(
        _inspect_planner(
            planner_path=Path(planner_path),
            planner_runner_path=Path(planner_runner_path),
            command_runner=run_status,
            executable_locator=executable_locator,
        )
    )

    if config is None:
        checks.append(_blocked("keychain", "keychain_check_blocked_by_configuration"))
    else:
        checks.append(
            _inspect_keychain(
                command_runner=run_status,
                executable_locator=executable_locator,
            )
        )

    (
        state_checks,
        record_count,
        sending_count,
        delivery_unknown_count,
        partial_count,
    ) = _inspect_state_store(Path(state_path))
    checks.extend(state_checks)

    ready_to_enable = not any(check.blocking for check in checks)
    enabled_mode = getattr(DeliveryConfigMode, "ENABLED", None)
    automation_active = bool(
        automatic_mode_available
        and config is not None
        and enabled_mode is not None
        and config.mode is enabled_mode
    )
    status = (
        "active"
        if automation_active and ready_to_enable
        else "ready_to_enable"
        if ready_to_enable
        else "not_ready"
    )
    return FamilyCalendarDeliveryReadinessResult(
        status=status,
        ready_to_enable=ready_to_enable,
        automation_active=automation_active,
        checks=tuple(checks),
        config_mode=config_mode,
        recipient_count=recipient_count,
        record_count=record_count,
        sending_count=sending_count,
        delivery_unknown_count=delivery_unknown_count,
        partial_count=partial_count,
    )


def format_family_calendar_delivery_readiness() -> str:
    """Return the redacted readiness document used by Samantha and the CLI."""

    result = inspect_family_calendar_delivery_readiness()
    return json.dumps(result.safe_document(), ensure_ascii=False, sort_keys=True)


def _inspect_planner(
    *,
    planner_path: Path,
    planner_runner_path: Path,
    command_runner: CommandStatusRunner,
    executable_locator: ExecutableLocator,
) -> ReadinessCheck:
    try:
        if (
            planner_runner_path.is_symlink()
            or not planner_runner_path.is_file()
        ):
            return _blocked("planner", "planner_runner_missing")
        if stat.S_IMODE(planner_runner_path.stat().st_mode) & 0o022:
            return _blocked("planner", "planner_runner_unsafe")
        if planner_path.is_symlink() or not planner_path.is_file():
            return _blocked("planner", "planner_not_installed")
        planner_stat = planner_path.stat()
        if (
            planner_stat.st_size > MAX_PLANNER_BYTES
            or stat.S_IMODE(planner_stat.st_mode) & 0o022
        ):
            return _blocked("planner", "planner_invalid")
        raw = plistlib.loads(planner_path.read_bytes())
        if not _planner_document_matches(raw, planner_runner_path):
            return _blocked("planner", "planner_invalid")
        launchctl = executable_locator("launchctl")
        if not launchctl:
            return _blocked("planner", "launchctl_unavailable")
        domain = f"gui/{os.getuid()}/{FAMILY_CALENDAR_PLANNER_LABEL}"
        if command_runner((launchctl, "print", domain)) != 0:
            return _blocked("planner", "planner_not_loaded")
    except Exception:  # noqa: BLE001 - filesystem/process details stay redacted.
        return _blocked("planner", "planner_probe_failed")
    return _ok("planner", "planner_ready")


def _planner_document_matches(raw: object, runner_path: Path) -> bool:
    if not isinstance(raw, dict):
        return False
    if raw.get("Label") != FAMILY_CALENDAR_PLANNER_LABEL:
        return False
    arguments = raw.get("ProgramArguments")
    if (
        not isinstance(arguments, list)
        or len(arguments) != 2
        or any(not isinstance(value, str) or not value for value in arguments)
    ):
        return False
    interpreter = Path(arguments[0]).expanduser()
    if (
        not interpreter.is_absolute()
        or not interpreter.is_file()
        or not os.access(interpreter, os.X_OK)
    ):
        return False
    expected_runner = str(runner_path.resolve())
    if str(Path(arguments[1]).expanduser().resolve()) != expected_runner:
        return False
    interval = raw.get("StartCalendarInterval")
    if not isinstance(interval, dict):
        return False
    hour = interval.get("Hour")
    minute = interval.get("Minute")
    return (
        type(hour) is int
        and 0 <= hour <= 23
        and type(minute) is int
        and 0 <= minute <= 59
    )


def _inspect_keychain(
    *,
    command_runner: CommandStatusRunner,
    executable_locator: ExecutableLocator,
) -> ReadinessCheck:
    security = executable_locator("security")
    if not security:
        return _blocked("keychain", "keychain_cli_unavailable")
    try:
        status = command_runner(
            (
                security,
                "find-generic-password",
                "-s",
                FAMILY_CALENDAR_KEYCHAIN_SERVICE,
                "-a",
                FAMILY_CALENDAR_KEYCHAIN_ACCOUNT,
            )
        )
    except Exception:  # noqa: BLE001 - Keychain details stay redacted.
        return _blocked("keychain", "keychain_probe_failed")
    if status == 0:
        return _ok("keychain", "credential_reference_present")
    if status == 44:
        return _blocked("keychain", "credential_reference_missing")
    return _blocked("keychain", "credential_reference_unavailable")


def _inspect_state_store(
    state_path: Path,
) -> tuple[tuple[ReadinessCheck, ...], int, int, int, int]:
    if not state_path.exists():
        if not _private_writable_directory(state_path.parent):
            return (
                (_blocked("state_store", "state_store_parent_unsafe"),),
                0,
                0,
                0,
                0,
            )
        return (
            (
                _ok("state_store", "state_store_empty"),
                _ok("recovery", "no_blocking_delivery_state"),
            ),
            0,
            0,
            0,
            0,
        )

    try:
        records = load_delivery_records(state_path)
    except Exception:  # noqa: BLE001 - private store details stay redacted.
        return (
            (_blocked("state_store", "state_store_invalid"),),
            0,
            0,
            0,
            0,
        )

    sending_count = sum(record.state is DeliveryState.SENDING for record in records)
    delivery_unknown_count = sum(
        record.state is DeliveryState.DELIVERY_UNKNOWN for record in records
    )
    partial_count = sum(record.state is DeliveryState.PARTIAL for record in records)
    checks = [_ok("state_store", "state_store_valid")]
    if sending_count:
        checks.append(_blocked("recovery", "interrupted_delivery_present"))
    elif delivery_unknown_count:
        checks.append(_blocked("recovery", "delivery_unknown_present"))
    else:
        checks.append(_ok("recovery", "no_blocking_delivery_state"))
    if partial_count:
        checks.append(
            ReadinessCheck(
                name="delivery_review",
                status="warning",
                code="partial_delivery_present",
                blocking=False,
            )
        )
    return (
        tuple(checks),
        len(records),
        sending_count,
        delivery_unknown_count,
        partial_count,
    )


def _private_writable_directory(path: Path) -> bool:
    try:
        return (
            not path.is_symlink()
            and path.is_dir()
            and stat.S_IMODE(path.stat().st_mode) == 0o700
            and os.access(path, os.W_OK)
        )
    except OSError:
        return False


def _automatic_mode_available() -> bool:
    return hasattr(DeliveryConfigMode, "ENABLED")


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


def _ok(name: str, code: str) -> ReadinessCheck:
    return ReadinessCheck(name=name, status="ok", code=code, blocking=False)


def _blocked(name: str, code: str) -> ReadinessCheck:
    return ReadinessCheck(name=name, status="blocked", code=code, blocking=True)
