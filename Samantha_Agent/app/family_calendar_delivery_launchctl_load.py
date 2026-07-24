"""Confirmed, fail-closed loading gate for the dry-run family-calendar planner."""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from app.family_calendar_delivery_config import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
)
from app.family_calendar_delivery_launchctl_preview import (
    ExecutableLocator,
    build_family_calendar_launchctl_preview,
)
from app.family_calendar_delivery_readiness import (
    DEFAULT_FAMILY_CALENDAR_PLANNER_PATH,
    DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
)


FAMILY_CALENDAR_LAUNCHCTL_LOAD_CONFIRMATION = (
    "LOAD_FAMILY_CALENDAR_DRY_RUN_PLANNER"
)
GLOBAL_SAFETY_BRAKE_CONFIRMATION = (
    "Potvrzuji globální brzdu: rozumím riziku a chci pokračovat."
)
LAUNCHCTL_SERVICE_NOT_FOUND_EXIT = 113

CommandStatusRunner = Callable[[Sequence[str]], int]


class FamilyCalendarLaunchctlLoadError(RuntimeError):
    """Raised when the planner cannot be loaded with a known safe outcome."""

    def __init__(
        self,
        message: str,
        *,
        stage: str = "preview",
        mutation_attempted: bool = False,
        runtime_state: str = "unknown",
        rollback_attempted: bool = False,
        rollback_confirmed: bool = False,
        bootstrap_exit_status: str = "not_called",
    ) -> None:
        super().__init__(message)
        self.stage = stage
        self.mutation_attempted = bool(mutation_attempted)
        self.runtime_state = (
            runtime_state
            if runtime_state in {"loaded", "unloaded", "unknown"}
            else "unknown"
        )
        self.rollback_attempted = bool(rollback_attempted)
        self.rollback_confirmed = bool(rollback_confirmed)
        self.bootstrap_exit_status = (
            bootstrap_exit_status
            if bootstrap_exit_status in {
                "not_called",
                "zero",
                "nonzero",
                "unknown",
            }
            else "unknown"
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "status": "failed",
            "failure_stage": self.stage,
            "runtime_state": self.runtime_state,
            "bootstrap_exit_status": self.bootstrap_exit_status,
            "rollback_attempted": self.rollback_attempted,
            "rollback_confirmed": self.rollback_confirmed,
            "retry_safe": not self.mutation_attempted,
            "writes_performed": self.mutation_attempted,
            "launchctl_called": True,
            "launchctl_mutation_called": self.mutation_attempted,
            "secret_read": False,
            "transport_called": False,
            "redacted": True,
        }


@dataclass(frozen=True, repr=False)
class FamilyCalendarLaunchctlLoadPlan:
    config_path: Path
    planner_path: Path
    planner_runner_path: Path
    launchctl_path: Path
    domain_target: str
    service_target: str
    fingerprint: str

    def __repr__(self) -> str:
        return (
            "FamilyCalendarLaunchctlLoadPlan("
            f"status='preview', fingerprint={self.fingerprint[:12]!r}, "
            "runtime_state='unloaded', redacted=True)"
        )

    def print_command(self) -> tuple[str, ...]:
        return (
            str(self.launchctl_path),
            "print",
            self.service_target,
        )

    def bootstrap_command(self) -> tuple[str, ...]:
        return (
            str(self.launchctl_path),
            "bootstrap",
            self.domain_target,
            str(self.planner_path),
        )

    def rollback_command(self) -> tuple[str, ...]:
        return (
            str(self.launchctl_path),
            "bootout",
            self.service_target,
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "status": "preview",
            "config_mode": "dry_run",
            "runtime_state": "unloaded",
            "operation": {
                "bootstrap": list(self.bootstrap_command()),
                "verify_loaded": list(self.print_command()),
                "rollback": list(self.rollback_command()),
                "verify_unloaded": list(self.print_command()),
            },
            "plan_fingerprint": self.fingerprint,
            "global_confirmation_required": True,
            "required_global_confirmation": GLOBAL_SAFETY_BRAKE_CONFIRMATION,
            "confirmation_required": True,
            "required_confirmation": (
                FAMILY_CALENDAR_LAUNCHCTL_LOAD_CONFIRMATION
            ),
            "current_load_state_probed": True,
            "writes_performed": False,
            "launchctl_called": True,
            "launchctl_probe_called": True,
            "launchctl_mutation_called": False,
            "bootstrap_called": False,
            "rollback_called": False,
            "secret_read": False,
            "transport_called": False,
            "redacted": True,
        }


@dataclass(frozen=True, repr=False)
class FamilyCalendarLaunchctlLoadResult:
    fingerprint: str
    bootstrap_exit_status: str

    def __repr__(self) -> str:
        return (
            "FamilyCalendarLaunchctlLoadResult("
            f"status='loaded', fingerprint={self.fingerprint[:12]!r}, "
            "runtime_state='loaded', redacted=True)"
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "status": "loaded",
            "config_mode": "dry_run",
            "runtime_state": "loaded",
            "planner_loaded": True,
            "automatic_sending_enabled": False,
            "plan_fingerprint": self.fingerprint,
            "bootstrap_exit_status": self.bootstrap_exit_status,
            "rollback_attempted": False,
            "rollback_confirmed": False,
            "writes_performed": True,
            "launchctl_called": True,
            "launchctl_probe_called": True,
            "launchctl_mutation_called": True,
            "bootstrap_called": True,
            "rollback_called": False,
            "secret_read": False,
            "transport_called": False,
            "redacted": True,
        }


def plan_family_calendar_launchctl_load(
    *,
    config_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    planner_path: Path = DEFAULT_FAMILY_CALENDAR_PLANNER_PATH,
    planner_runner_path: Path = DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
    command_runner: CommandStatusRunner | None = None,
    executable_locator: ExecutableLocator = shutil.which,
) -> FamilyCalendarLaunchctlLoadPlan:
    """Return a load plan only when exact inputs are safe and unloaded."""

    run_status = command_runner or _run_command_status
    config = Path(config_path).expanduser()
    planner = Path(planner_path).expanduser()
    runner = Path(planner_runner_path).expanduser()
    preview = build_family_calendar_launchctl_preview(
        config_path=config,
        planner_path=planner,
        planner_runner_path=runner,
        executable_locator=executable_locator,
    )
    if (
        preview.status != "preview"
        or preview.launchctl_path is None
        or preview.fingerprint is None
    ):
        raise FamilyCalendarLaunchctlLoadError(
            "Family-calendar launchctl inputs are not safe.",
            stage="preview",
        )
    plan = FamilyCalendarLaunchctlLoadPlan(
        config_path=config,
        planner_path=planner,
        planner_runner_path=runner,
        launchctl_path=preview.launchctl_path,
        domain_target=preview.domain_target,
        service_target=preview.service_target,
        fingerprint=preview.fingerprint,
    )
    runtime_state = _probe_runtime_state(plan, run_status)
    if runtime_state == "loaded":
        raise FamilyCalendarLaunchctlLoadError(
            "Family-calendar planner is already loaded.",
            stage="state_probe",
            runtime_state="loaded",
        )
    if runtime_state != "unloaded":
        raise FamilyCalendarLaunchctlLoadError(
            "Family-calendar planner load state is unknown.",
            stage="state_probe",
            runtime_state="unknown",
        )
    return plan


def apply_family_calendar_launchctl_load(
    plan: FamilyCalendarLaunchctlLoadPlan,
    *,
    global_confirmation: str,
    confirmation: str,
    expected_fingerprint: str,
    command_runner: CommandStatusRunner | None = None,
    executable_locator: ExecutableLocator = shutil.which,
) -> FamilyCalendarLaunchctlLoadResult:
    """Load an unchanged dry-run planner and verify or roll back its state."""

    if not isinstance(plan, FamilyCalendarLaunchctlLoadPlan):
        raise FamilyCalendarLaunchctlLoadError(
            "A validated family-calendar launchctl plan is required.",
            stage="plan_recheck",
        )
    if global_confirmation != GLOBAL_SAFETY_BRAKE_CONFIRMATION:
        raise FamilyCalendarLaunchctlLoadError(
            "Exact global safety confirmation is required.",
            stage="global_confirmation",
            runtime_state="unloaded",
        )
    if confirmation != FAMILY_CALENDAR_LAUNCHCTL_LOAD_CONFIRMATION:
        raise FamilyCalendarLaunchctlLoadError(
            "Exact family-calendar launchctl confirmation is required.",
            stage="confirmation",
            runtime_state="unloaded",
        )
    if expected_fingerprint != plan.fingerprint:
        raise FamilyCalendarLaunchctlLoadError(
            "Family-calendar launchctl fingerprint does not match.",
            stage="fingerprint",
            runtime_state="unloaded",
        )

    run_status = command_runner or _run_command_status
    try:
        current = plan_family_calendar_launchctl_load(
            config_path=plan.config_path,
            planner_path=plan.planner_path,
            planner_runner_path=plan.planner_runner_path,
            command_runner=run_status,
            executable_locator=executable_locator,
        )
    except FamilyCalendarLaunchctlLoadError as exc:
        raise FamilyCalendarLaunchctlLoadError(
            "Family-calendar launchctl inputs changed after preview.",
            stage="plan_recheck",
            runtime_state=exc.runtime_state,
        ) from exc
    if (
        current.fingerprint != plan.fingerprint
        or current.launchctl_path != plan.launchctl_path
        or current.domain_target != plan.domain_target
        or current.service_target != plan.service_target
    ):
        raise FamilyCalendarLaunchctlLoadError(
            "Family-calendar launchctl plan changed after preview.",
            stage="plan_recheck",
            runtime_state="unloaded",
        )

    bootstrap_exit_status = _run_mutation(
        current.bootstrap_command(),
        run_status,
    )
    runtime_state = _probe_runtime_state(current, run_status)
    if runtime_state == "loaded":
        return FamilyCalendarLaunchctlLoadResult(
            fingerprint=current.fingerprint,
            bootstrap_exit_status=bootstrap_exit_status,
        )
    if runtime_state == "unloaded":
        raise FamilyCalendarLaunchctlLoadError(
            "Family-calendar planner was not loaded.",
            stage=(
                "verification"
                if bootstrap_exit_status == "zero"
                else "bootstrap"
            ),
            mutation_attempted=True,
            runtime_state="unloaded",
            bootstrap_exit_status=bootstrap_exit_status,
        )

    _run_mutation(current.rollback_command(), run_status)
    rollback_state = _probe_runtime_state(current, run_status)
    if rollback_state == "unloaded":
        raise FamilyCalendarLaunchctlLoadError(
            "Family-calendar planner load could not be verified; rollback succeeded.",
            stage="verification",
            mutation_attempted=True,
            runtime_state="unloaded",
            rollback_attempted=True,
            rollback_confirmed=True,
            bootstrap_exit_status=bootstrap_exit_status,
        )
    raise FamilyCalendarLaunchctlLoadError(
        "Family-calendar planner load and rollback state are not safely resolved.",
        stage="rollback",
        mutation_attempted=True,
        runtime_state=rollback_state,
        rollback_attempted=True,
        rollback_confirmed=False,
        bootstrap_exit_status=bootstrap_exit_status,
    )


def _probe_runtime_state(
    plan: FamilyCalendarLaunchctlLoadPlan,
    command_runner: CommandStatusRunner,
) -> str:
    try:
        status = int(command_runner(plan.print_command()))
    except Exception:  # noqa: BLE001 - process details stay redacted.
        return "unknown"
    if status == 0:
        return "loaded"
    if status == LAUNCHCTL_SERVICE_NOT_FOUND_EXIT:
        return "unloaded"
    return "unknown"


def _run_mutation(
    command: Sequence[str],
    command_runner: CommandStatusRunner,
) -> str:
    try:
        status = int(command_runner(tuple(command)))
    except Exception:  # noqa: BLE001 - runtime outcome is verified separately.
        return "unknown"
    return "zero" if status == 0 else "nonzero"


def _run_command_status(argv: Sequence[str]) -> int:
    completed = subprocess.run(
        tuple(argv),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=10,
    )
    return int(completed.returncode)
