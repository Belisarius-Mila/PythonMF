"""Read-only preview of loading and rolling back the family-calendar LaunchAgent."""

from __future__ import annotations

import hashlib
import os
import plistlib
import shutil
import stat
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.family_calendar_delivery_config import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    DeliveryConfigMode,
    load_family_calendar_delivery_config,
)
from app.family_calendar_delivery_readiness import (
    DEFAULT_FAMILY_CALENDAR_PLANNER_PATH,
    DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
    FAMILY_CALENDAR_PLANNER_LABEL,
    MAX_PLANNER_BYTES,
    _planner_document_matches,
)


_PLAN_VERSION = b"family-calendar-launchctl-preview-v1"
ExecutableLocator = Callable[[str], str | None]


@dataclass(frozen=True, repr=False)
class FamilyCalendarLaunchctlPreview:
    status: str
    issues: tuple[str, ...]
    launchctl_path: Path | None
    planner_path: Path
    domain_target: str
    service_target: str
    fingerprint: str | None

    def __repr__(self) -> str:
        return (
            "FamilyCalendarLaunchctlPreview("
            f"status={self.status!r}, issue_count={len(self.issues)}, "
            "redacted=True)"
        )

    def operation_document(self) -> dict[str, object] | None:
        if (
            self.status != "preview"
            or self.launchctl_path is None
            or self.fingerprint is None
        ):
            return None
        launchctl = str(self.launchctl_path)
        planner = str(self.planner_path)
        return {
            "bootstrap": [
                launchctl,
                "bootstrap",
                self.domain_target,
                planner,
            ],
            "verify_loaded": [
                launchctl,
                "print",
                self.service_target,
            ],
            "rollback": [
                launchctl,
                "bootout",
                self.service_target,
            ],
            "verify_unloaded": [
                launchctl,
                "print",
                self.service_target,
            ],
        }

    def safe_document(self) -> dict[str, object]:
        return {
            "status": self.status,
            "issues": list(self.issues),
            "config_mode": "dry_run" if self.status == "preview" else "unknown",
            "planner_label": FAMILY_CALENDAR_PLANNER_LABEL,
            "planner_path": (
                str(self.planner_path) if self.status == "preview" else None
            ),
            "domain_target": (
                self.domain_target if self.status == "preview" else None
            ),
            "service_target": (
                self.service_target if self.status == "preview" else None
            ),
            "run_at_load": False if self.status == "preview" else None,
            "operation": self.operation_document(),
            "plan_fingerprint": self.fingerprint,
            "current_load_state_probed": False,
            "apply_available": False,
            "separate_confirmation_required_for_load": True,
            "writes_performed": False,
            "launchctl_called": False,
            "secret_read": False,
            "transport_called": False,
            "redacted": True,
        }


def build_family_calendar_launchctl_preview(
    *,
    config_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    planner_path: Path = DEFAULT_FAMILY_CALENDAR_PLANNER_PATH,
    planner_runner_path: Path = DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
    executable_locator: ExecutableLocator = shutil.which,
) -> FamilyCalendarLaunchctlPreview:
    """Return exact future commands without invoking ``launchctl`` or writing."""

    config = Path(config_path).expanduser()
    planner = Path(planner_path).expanduser()
    runner = Path(planner_runner_path).expanduser()
    uid = os.getuid()
    domain_target = f"gui/{uid}"
    service_target = f"{domain_target}/{FAMILY_CALENDAR_PLANNER_LABEL}"
    issues: list[str] = []

    launchctl, launchctl_issue = _inspect_launchctl(executable_locator)
    if launchctl_issue:
        issues.append(launchctl_issue)

    config_digest: bytes | None = None
    try:
        config_digest_before = _file_digest(config)
        delivery_config = load_family_calendar_delivery_config(config)
        config_digest_after = _file_digest(config)
    except Exception:  # noqa: BLE001 - private configuration stays redacted.
        issues.append("configuration_invalid")
    else:
        if config_digest_before != config_digest_after:
            issues.append("configuration_changed_during_preview")
        elif delivery_config.mode is not DeliveryConfigMode.DRY_RUN:
            issues.append("configuration_not_dry_run")
        else:
            config_digest = config_digest_after

    planner_bytes, planner_issues = _inspect_planner(
        planner_path=planner,
        planner_runner_path=runner,
    )
    issues.extend(planner_issues)

    fingerprint = None
    if not issues and launchctl is not None and planner_bytes is not None:
        if config_digest is None:
            issues.append("configuration_invalid")
        else:
            fingerprint = _plan_fingerprint(
                launchctl_path=launchctl,
                planner_path=planner,
                planner_bytes=planner_bytes,
                config_digest=config_digest,
                uid=uid,
            )

    return FamilyCalendarLaunchctlPreview(
        status="preview" if not issues else "invalid",
        issues=tuple(issues),
        launchctl_path=launchctl,
        planner_path=planner,
        domain_target=domain_target,
        service_target=service_target,
        fingerprint=fingerprint,
    )


def _inspect_launchctl(
    executable_locator: ExecutableLocator,
) -> tuple[Path | None, str | None]:
    raw = executable_locator("launchctl")
    if not raw:
        return None, "launchctl_unavailable"
    path = Path(raw).expanduser()
    try:
        if (
            not path.is_absolute()
            or path.is_symlink()
            or not path.is_file()
            or not os.access(path, os.X_OK)
        ):
            return None, "launchctl_unsafe"
        path_stat = path.stat()
        if (
            path_stat.st_uid not in {0, os.getuid()}
            or stat.S_IMODE(path_stat.st_mode) & 0o022
        ):
            return None, "launchctl_unsafe"
    except OSError:
        return None, "launchctl_probe_failed"
    return path, None


def _inspect_planner(
    *,
    planner_path: Path,
    planner_runner_path: Path,
) -> tuple[bytes | None, tuple[str, ...]]:
    issues: list[str] = []
    if not planner_path.is_absolute():
        return None, ("planner_path_not_absolute",)
    if planner_path.name != f"{FAMILY_CALENDAR_PLANNER_LABEL}.plist":
        return None, ("planner_name_not_canonical",)
    try:
        parent = planner_path.parent
        if (
            parent.is_symlink()
            or not parent.is_dir()
            or parent.stat().st_uid != os.getuid()
            or stat.S_IMODE(parent.stat().st_mode) & 0o022
        ):
            issues.append("planner_parent_unsafe")
        if planner_path.is_symlink() or not planner_path.is_file():
            issues.append("planner_not_installed")
            return None, tuple(issues)
        planner_stat = planner_path.stat()
        if planner_stat.st_uid != os.getuid():
            issues.append("planner_owner_invalid")
        if stat.S_IMODE(planner_stat.st_mode) != 0o600:
            issues.append("planner_mode_invalid")
        if planner_stat.st_size > MAX_PLANNER_BYTES:
            issues.append("planner_too_large")
        if issues:
            return None, tuple(issues)
        planner_bytes = planner_path.read_bytes()
        raw = plistlib.loads(planner_bytes)
    except Exception:  # noqa: BLE001 - filesystem details stay redacted.
        return None, ("planner_invalid",)

    if not _planner_document_matches(raw, planner_runner_path):
        issues.append("planner_contract_mismatch")
    if not isinstance(raw, dict) or raw.get("RunAtLoad") is not False:
        issues.append("planner_run_at_load_invalid")
    if not isinstance(raw, dict) or raw.get("ProcessType") != "Background":
        issues.append("planner_process_type_invalid")
    return (
        planner_bytes if not issues else None,
        tuple(issues),
    )


def _plan_fingerprint(
    *,
    launchctl_path: Path,
    planner_path: Path,
    planner_bytes: bytes,
    config_digest: bytes,
    uid: int,
) -> str:
    digest = hashlib.sha256()
    for value in (
        _PLAN_VERSION,
        str(launchctl_path).encode("utf-8"),
        str(planner_path).encode("utf-8"),
        planner_bytes,
        config_digest,
        str(uid).encode("ascii"),
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
