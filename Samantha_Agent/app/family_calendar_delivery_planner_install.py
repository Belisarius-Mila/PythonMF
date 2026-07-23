"""Two-step create-only installation gate for the family-calendar LaunchAgent."""

from __future__ import annotations

import hashlib
import os
import plistlib
import stat
from dataclasses import dataclass
from pathlib import Path

from app.family_calendar_delivery_config import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    DeliveryConfigMode,
    load_family_calendar_delivery_config,
)
from app.family_calendar_delivery_planner_preview import (
    DEFAULT_FAMILY_CALENDAR_PLANNER_HOUR,
    DEFAULT_FAMILY_CALENDAR_PLANNER_MINUTE,
    DEFAULT_FAMILY_CALENDAR_PLANNER_PYTHON_PATH,
    build_family_calendar_planner_preview,
)
from app.family_calendar_delivery_readiness import (
    DEFAULT_FAMILY_CALENDAR_PLANNER_PATH,
    DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
    FAMILY_CALENDAR_PLANNER_LABEL,
)
from app.file_persistence import FilePersistenceError, atomic_create_text


FAMILY_CALENDAR_PLANNER_INSTALL_CONFIRMATION = (
    "INSTALL_FAMILY_CALENDAR_DRY_RUN_PLANNER"
)
FAMILY_CALENDAR_PLANNER_FILE_MODE = 0o600


class FamilyCalendarPlannerInstallError(RuntimeError):
    """Raised when a planner cannot be previewed or created safely."""


@dataclass(frozen=True, repr=False)
class FamilyCalendarPlannerInstallPlan:
    target_path: Path
    config_path: Path
    python_path: Path
    runner_path: Path
    hour: int
    minute: int
    configuration: dict[str, object]
    plist_text: str
    fingerprint: str

    def __repr__(self) -> str:
        return (
            "FamilyCalendarPlannerInstallPlan("
            f"status='preview', fingerprint={self.fingerprint[:12]!r}, "
            "config_mode='dry_run', redacted=True)"
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "status": "preview",
            "configuration": self.configuration,
            "target_path": str(self.target_path),
            "file_mode": "0600",
            "create_only": True,
            "config_mode": "dry_run",
            "confirmation_required": True,
            "required_confirmation": (
                FAMILY_CALENDAR_PLANNER_INSTALL_CONFIRMATION
            ),
            "plan_fingerprint": self.fingerprint,
            "writes_performed": False,
            "install_called": False,
            "launchctl_called": False,
            "secret_read": False,
            "transport_called": False,
            "redacted": True,
        }


@dataclass(frozen=True, repr=False)
class FamilyCalendarPlannerInstallResult:
    target_path: Path
    fingerprint: str

    def __repr__(self) -> str:
        return (
            "FamilyCalendarPlannerInstallResult("
            f"status='installed', fingerprint={self.fingerprint[:12]!r}, "
            "redacted=True)"
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "status": "installed",
            "target_path": str(self.target_path),
            "file_mode": "0600",
            "create_only": True,
            "config_mode": "dry_run",
            "plan_fingerprint": self.fingerprint,
            "writes_performed": True,
            "install_called": True,
            "launchctl_called": False,
            "secret_read": False,
            "transport_called": False,
            "redacted": True,
        }


def plan_family_calendar_planner_install(
    *,
    target_path: Path = DEFAULT_FAMILY_CALENDAR_PLANNER_PATH,
    config_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    python_path: Path = DEFAULT_FAMILY_CALENDAR_PLANNER_PYTHON_PATH,
    runner_path: Path = DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
    hour: int = DEFAULT_FAMILY_CALENDAR_PLANNER_HOUR,
    minute: int = DEFAULT_FAMILY_CALENDAR_PLANNER_MINUTE,
) -> FamilyCalendarPlannerInstallPlan:
    """Return an exact no-write plan for one create-only dry-run plist."""

    target = Path(target_path).expanduser()
    config = Path(config_path).expanduser()
    python = Path(python_path).expanduser()
    runner = Path(runner_path).expanduser()
    try:
        preview = build_family_calendar_planner_preview(
            python_path=python,
            runner_path=runner,
            hour=hour,
            minute=minute,
        )
        configuration = preview.launchd_document()
        if preview.status != "preview" or configuration is None:
            raise FamilyCalendarPlannerInstallError(
                "Planner configuration preview is invalid."
            )
        delivery_config = load_family_calendar_delivery_config(config)
        if delivery_config.mode is not DeliveryConfigMode.DRY_RUN:
            raise FamilyCalendarPlannerInstallError(
                "Family-calendar delivery configuration is not dry-run."
            )
        _assert_create_only_target(target)
        plist_bytes = plistlib.dumps(
            configuration,
            fmt=plistlib.FMT_XML,
            sort_keys=True,
        )
        plist_text = plist_bytes.decode("utf-8")
        fingerprint = _planner_fingerprint(
            target_path=target,
            plist_bytes=plist_bytes,
            python_path=python,
            runner_path=runner,
        )
    except FamilyCalendarPlannerInstallError:
        raise
    except Exception as exc:  # noqa: BLE001 - private config details stay redacted.
        raise FamilyCalendarPlannerInstallError(
            "Family-calendar planner installation cannot be planned safely."
        ) from exc
    return FamilyCalendarPlannerInstallPlan(
        target_path=target,
        config_path=config,
        python_path=python,
        runner_path=runner,
        hour=hour,
        minute=minute,
        configuration=configuration,
        plist_text=plist_text,
        fingerprint=fingerprint,
    )


def apply_family_calendar_planner_install(
    plan: FamilyCalendarPlannerInstallPlan,
    *,
    confirmation: str,
    expected_fingerprint: str,
) -> FamilyCalendarPlannerInstallResult:
    """Atomically create one unchanged dry-run plist after exact confirmation."""

    if not isinstance(plan, FamilyCalendarPlannerInstallPlan):
        raise FamilyCalendarPlannerInstallError(
            "A validated planner installation plan is required."
        )
    if confirmation != FAMILY_CALENDAR_PLANNER_INSTALL_CONFIRMATION:
        raise FamilyCalendarPlannerInstallError(
            "Exact planner installation confirmation is required."
        )
    if expected_fingerprint != plan.fingerprint:
        raise FamilyCalendarPlannerInstallError(
            "Planner installation fingerprint does not match the preview."
        )
    current = plan_family_calendar_planner_install(
        target_path=plan.target_path,
        config_path=plan.config_path,
        python_path=plan.python_path,
        runner_path=plan.runner_path,
        hour=plan.hour,
        minute=plan.minute,
    )
    if current.fingerprint != plan.fingerprint:
        raise FamilyCalendarPlannerInstallError(
            "Planner installation inputs changed after preview."
        )
    try:
        atomic_create_text(
            current.target_path,
            current.plist_text,
            mode=FAMILY_CALENDAR_PLANNER_FILE_MODE,
        )
        _verify_created_planner(current)
    except (OSError, UnicodeError, ValueError, FilePersistenceError) as exc:
        raise FamilyCalendarPlannerInstallError(
            "Family-calendar planner installation failed safely."
        ) from exc
    return FamilyCalendarPlannerInstallResult(
        target_path=current.target_path,
        fingerprint=current.fingerprint,
    )


def _assert_create_only_target(path: Path) -> None:
    if not path.is_absolute():
        raise FamilyCalendarPlannerInstallError(
            "Planner target path must be absolute."
        )
    if path.name != f"{FAMILY_CALENDAR_PLANNER_LABEL}.plist":
        raise FamilyCalendarPlannerInstallError(
            "Planner target name is not canonical."
        )
    parent = path.parent
    if parent.is_symlink() or not parent.is_dir():
        raise FamilyCalendarPlannerInstallError(
            "Planner target directory is unavailable or linked."
        )
    parent_stat = parent.stat()
    if parent_stat.st_uid != os.getuid():
        raise FamilyCalendarPlannerInstallError(
            "Planner target directory has an unexpected owner."
        )
    if stat.S_IMODE(parent_stat.st_mode) & 0o022:
        raise FamilyCalendarPlannerInstallError(
            "Planner target directory is writable by other users."
        )
    if path.is_symlink() or path.exists():
        raise FamilyCalendarPlannerInstallError(
            "Planner target already exists; create-only installation refused."
        )


def _planner_fingerprint(
    *,
    target_path: Path,
    plist_bytes: bytes,
    python_path: Path,
    runner_path: Path,
) -> str:
    digest = hashlib.sha256()
    for value in (
        b"family-calendar-planner-install-v1",
        str(target_path).encode("utf-8"),
        plist_bytes,
        _file_digest(python_path),
        _file_digest(runner_path),
    ):
        digest.update(len(value).to_bytes(8, "big"))
        digest.update(value)
    return digest.hexdigest()


def _file_digest(path: Path) -> bytes:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.digest()


def _verify_created_planner(plan: FamilyCalendarPlannerInstallPlan) -> None:
    target = plan.target_path
    if target.is_symlink() or not target.is_file():
        raise FamilyCalendarPlannerInstallError(
            "Created planner is missing or linked."
        )
    target_stat = target.stat()
    if target_stat.st_uid != os.getuid():
        raise FamilyCalendarPlannerInstallError(
            "Created planner has an unexpected owner."
        )
    if stat.S_IMODE(target_stat.st_mode) != FAMILY_CALENDAR_PLANNER_FILE_MODE:
        raise FamilyCalendarPlannerInstallError(
            "Created planner has unsafe permissions."
        )
    payload = target.read_bytes()
    if payload != plan.plist_text.encode("utf-8"):
        raise FamilyCalendarPlannerInstallError(
            "Created planner does not match its preview."
        )
    if plistlib.loads(payload) != plan.configuration:
        raise FamilyCalendarPlannerInstallError(
            "Created planner failed plist verification."
        )
