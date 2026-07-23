"""Read-only preview of a future family-calendar LaunchAgent configuration."""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path

from app.family_calendar_delivery_readiness import (
    DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
    FAMILY_CALENDAR_PLANNER_LABEL,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FAMILY_CALENDAR_PLANNER_PYTHON_PATH = (
    PROJECT_ROOT / ".venv" / "bin" / "python"
)
DEFAULT_FAMILY_CALENDAR_PLANNER_HOUR = 8
DEFAULT_FAMILY_CALENDAR_PLANNER_MINUTE = 0


@dataclass(frozen=True, repr=False)
class FamilyCalendarPlannerPreview:
    status: str
    python_path: Path
    runner_path: Path
    hour: int
    minute: int
    issues: tuple[str, ...]
    writes_performed: bool = False
    install_called: bool = False
    launchctl_called: bool = False
    secret_read: bool = False
    transport_called: bool = False

    def __repr__(self) -> str:
        return (
            "FamilyCalendarPlannerPreview("
            f"status={self.status!r}, issue_count={len(self.issues)}, "
            "redacted=True)"
        )

    def launchd_document(self) -> dict[str, object] | None:
        if self.status != "preview":
            return None
        return {
            "Label": FAMILY_CALENDAR_PLANNER_LABEL,
            "ProgramArguments": [
                str(self.python_path),
                str(self.runner_path),
            ],
            "StartCalendarInterval": {
                "Hour": self.hour,
                "Minute": self.minute,
            },
            "RunAtLoad": False,
            "ProcessType": "Background",
        }

    def safe_document(self) -> dict[str, object]:
        return {
            "status": self.status,
            "configuration": self.launchd_document(),
            "issues": list(self.issues),
            "writes_performed": self.writes_performed,
            "install_called": self.install_called,
            "launchctl_called": self.launchctl_called,
            "secret_read": self.secret_read,
            "transport_called": self.transport_called,
            "redacted": True,
        }


def build_family_calendar_planner_preview(
    *,
    python_path: Path = DEFAULT_FAMILY_CALENDAR_PLANNER_PYTHON_PATH,
    runner_path: Path = DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
    hour: int = DEFAULT_FAMILY_CALENDAR_PLANNER_HOUR,
    minute: int = DEFAULT_FAMILY_CALENDAR_PLANNER_MINUTE,
) -> FamilyCalendarPlannerPreview:
    """Validate and preview a LaunchAgent document without writing or loading it."""

    python = Path(python_path).expanduser()
    runner = Path(runner_path).expanduser()
    issues: list[str] = []

    if type(hour) is not int or not 0 <= hour <= 23:
        issues.append("schedule_hour_invalid")
    if type(minute) is not int or not 0 <= minute <= 59:
        issues.append("schedule_minute_invalid")
    issues.extend(_inspect_python_path(python))
    issues.extend(_inspect_runner_path(runner))

    return FamilyCalendarPlannerPreview(
        status="preview" if not issues else "invalid",
        python_path=python,
        runner_path=runner,
        hour=hour,
        minute=minute,
        issues=tuple(issues),
    )


def _inspect_python_path(path: Path) -> tuple[str, ...]:
    if not path.is_absolute():
        return ("python_path_not_absolute",)
    try:
        if not path.is_file():
            return ("python_path_missing",)
        if not os.access(path, os.X_OK):
            return ("python_path_not_executable",)
        path_mode = path.lstat().st_mode if path.is_symlink() else path.stat().st_mode
        if (
            stat.S_IMODE(path_mode) & 0o022
            or stat.S_IMODE(path.parent.stat().st_mode) & 0o022
        ):
            return ("python_path_unsafe",)
    except OSError:
        return ("python_path_probe_failed",)
    return ()


def _inspect_runner_path(path: Path) -> tuple[str, ...]:
    if not path.is_absolute():
        return ("runner_path_not_absolute",)
    try:
        if path.is_symlink() or not path.is_file():
            return ("runner_path_missing",)
        if stat.S_IMODE(path.stat().st_mode) & 0o022:
            return ("runner_path_unsafe",)
    except OSError:
        return ("runner_path_probe_failed",)
    return ()
