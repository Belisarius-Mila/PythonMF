"""Confirmed dry-run-to-enabled activation with fail-closed rollback."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.family_calendar_delivery_automation_preview import (
    FAMILY_CALENDAR_AUTOMATION_CONFIRMATION,
    FamilyCalendarAutomationPreview,
    build_family_calendar_automation_preview,
)
from app.family_calendar_delivery_config import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    DeliveryConfigMode,
    FamilyCalendarDeliveryConfig,
    load_family_calendar_delivery_config,
    parse_family_calendar_delivery_config_document,
)
from app.family_calendar_delivery_launchctl_load import (
    GLOBAL_SAFETY_BRAKE_CONFIRMATION,
    LAUNCHCTL_SERVICE_NOT_FOUND_EXIT,
)
from app.family_calendar_delivery_launchctl_preview import ExecutableLocator
from app.family_calendar_delivery_readiness import (
    DEFAULT_FAMILY_CALENDAR_PLANNER_PATH,
    DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
    CommandStatusRunner,
    inspect_family_calendar_delivery_readiness,
)
from app.family_calendar_delivery_store import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
)
from app.file_persistence import (
    atomic_replace_text_under_external_lock,
    exclusive_file_lock,
    lock_path_for,
)


@dataclass(frozen=True)
class _ConfigSnapshot:
    payload: bytes
    digest: str
    raw: dict[str, Any]
    config: FamilyCalendarDeliveryConfig


class FamilyCalendarAutomationActivationError(RuntimeError):
    """Redacted activation failure with explicit rollback evidence."""

    def __init__(
        self,
        message: str,
        *,
        stage: str,
        mutation_attempted: bool = False,
        runtime_state: str = "loaded",
        config_mode: str = "dry_run",
        config_write_attempted: bool = False,
        config_write_confirmed: bool = False,
        rollback_attempted: bool = False,
        rollback_confirmed: bool = False,
    ) -> None:
        super().__init__(message)
        self.stage = stage
        self.mutation_attempted = bool(mutation_attempted)
        self.runtime_state = (
            runtime_state
            if runtime_state in {"loaded", "unloaded", "unknown"}
            else "unknown"
        )
        self.config_mode = (
            config_mode
            if config_mode in {"dry_run", "enabled", "unknown"}
            else "unknown"
        )
        self.config_write_attempted = bool(config_write_attempted)
        self.config_write_confirmed = bool(config_write_confirmed)
        self.rollback_attempted = bool(rollback_attempted)
        self.rollback_confirmed = bool(rollback_confirmed)

    def safe_document(self) -> dict[str, object]:
        return {
            "status": "failed",
            "failure_stage": self.stage,
            "runtime_state": self.runtime_state,
            "config_mode": self.config_mode,
            "config_write_attempted": self.config_write_attempted,
            "config_write_confirmed": self.config_write_confirmed,
            "rollback_attempted": self.rollback_attempted,
            "rollback_confirmed": self.rollback_confirmed,
            "manual_audit_required": (
                self.mutation_attempted and not self.rollback_confirmed
            ),
            "retry_safe": not self.mutation_attempted,
            "writes_performed": self.mutation_attempted,
            "launchctl_called": True,
            "launchctl_mutation_called": self.mutation_attempted,
            "secret_read": False,
            "transport_called": False,
            "redacted": True,
        }


@dataclass(frozen=True, repr=False)
class FamilyCalendarAutomationActivationPlan:
    config_path: Path
    state_path: Path
    planner_path: Path
    planner_runner_path: Path
    launchctl_path: Path
    domain_target: str
    service_target: str
    fingerprint: str
    source_snapshot: _ConfigSnapshot
    target_payload: bytes
    target_digest: str
    target_config: FamilyCalendarDeliveryConfig
    preview: FamilyCalendarAutomationPreview

    def __repr__(self) -> str:
        return (
            "FamilyCalendarAutomationActivationPlan("
            f"status='preview', fingerprint={self.fingerprint[:12]!r}, "
            "from_mode='dry_run', to_mode='enabled', redacted=True)"
        )

    def print_command(self) -> tuple[str, ...]:
        return (str(self.launchctl_path), "print", self.service_target)

    def unload_command(self) -> tuple[str, ...]:
        return (str(self.launchctl_path), "bootout", self.service_target)

    def load_command(self) -> tuple[str, ...]:
        return (
            str(self.launchctl_path),
            "bootstrap",
            self.domain_target,
            str(self.planner_path),
        )

    def safe_document(self) -> dict[str, object]:
        document = self.preview.safe_document()
        document["activation_implementation_available"] = True
        document["apply_available"] = True
        document["automatic_sending_enabled"] = False
        document["writes_performed"] = False
        document["launchctl_mutation_called"] = False
        document["secret_read"] = False
        document["transport_called"] = False
        return document


@dataclass(frozen=True, repr=False)
class FamilyCalendarAutomationActivationResult:
    fingerprint: str
    recipient_count: int

    def __repr__(self) -> str:
        return (
            "FamilyCalendarAutomationActivationResult("
            "status='activated', config_mode='enabled', "
            f"recipient_count={self.recipient_count}, redacted=True)"
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "status": "activated",
            "config_mode": "enabled",
            "recipient_count": self.recipient_count,
            "runtime_state": "loaded",
            "planner_loaded": True,
            "ready": True,
            "automatic_sending_enabled": True,
            "plan_fingerprint": self.fingerprint,
            "rollback_attempted": False,
            "rollback_confirmed": False,
            "writes_performed": True,
            "launchctl_called": True,
            "launchctl_mutation_called": True,
            "secret_read": False,
            "transport_called": False,
            "redacted": True,
        }


@dataclass(frozen=True)
class _RollbackOutcome:
    attempted: bool
    confirmed: bool
    runtime_state: str
    config_mode: str


@dataclass(frozen=True)
class _ConfigWriteOutcome:
    failure_stage: str | None
    attempted: bool
    confirmed: bool


def plan_family_calendar_automation_activation(
    *,
    config_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    state_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
    planner_path: Path = DEFAULT_FAMILY_CALENDAR_PLANNER_PATH,
    planner_runner_path: Path = DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
    command_runner: CommandStatusRunner | None = None,
    executable_locator: ExecutableLocator = shutil.which,
) -> FamilyCalendarAutomationActivationPlan:
    """Return a stable, read-only activation plan over exact private inputs."""

    config = Path(config_path).expanduser()
    state = Path(state_path).expanduser()
    planner = Path(planner_path).expanduser()
    runner = Path(planner_runner_path).expanduser()
    source_before = _read_config_snapshot(config)
    preview = build_family_calendar_automation_preview(
        config_path=config,
        state_path=state,
        planner_path=planner,
        planner_runner_path=runner,
        command_runner=command_runner,
        executable_locator=executable_locator,
    )
    source_after = _read_config_snapshot(config)
    launchctl_preview = preview.launchctl_preview
    if (
        source_before is None
        or source_after is None
        or source_before.digest != source_after.digest
        or source_before.config != source_after.config
        or source_after.config.mode is not DeliveryConfigMode.DRY_RUN
        or preview.status != "preview"
        or preview.issues
        or preview.implementation_blockers
        or preview.plan_fingerprint is None
        or launchctl_preview.launchctl_path is None
        or launchctl_preview.fingerprint is None
    ):
        raise FamilyCalendarAutomationActivationError(
            "Family-calendar automation activation inputs are not ready.",
            stage="preview",
        )

    target_raw = dict(source_after.raw)
    target_raw["mode"] = DeliveryConfigMode.ENABLED.value
    target_config_failed = False
    try:
        target_config = parse_family_calendar_delivery_config_document(target_raw)
        target_payload = (
            json.dumps(
                target_raw,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
    except Exception:  # noqa: BLE001 - private configuration remains redacted.
        target_config_failed = True
    if target_config_failed:
        raise FamilyCalendarAutomationActivationError(
            "Family-calendar automation target configuration is invalid.",
            stage="preview",
        )
    return FamilyCalendarAutomationActivationPlan(
        config_path=config,
        state_path=state,
        planner_path=planner,
        planner_runner_path=runner,
        launchctl_path=launchctl_preview.launchctl_path,
        domain_target=launchctl_preview.domain_target,
        service_target=launchctl_preview.service_target,
        fingerprint=preview.plan_fingerprint,
        source_snapshot=source_after,
        target_payload=target_payload,
        target_digest=_digest(target_payload),
        target_config=target_config,
        preview=preview,
    )


def apply_family_calendar_automation_activation(
    plan: FamilyCalendarAutomationActivationPlan,
    *,
    global_confirmation: str,
    confirmation: str,
    expected_fingerprint: str,
    command_runner: CommandStatusRunner | None = None,
    executable_locator: ExecutableLocator = shutil.which,
    lock_timeout: float = 10.0,
) -> FamilyCalendarAutomationActivationResult:
    """Activate unchanged inputs, or restore dry-run with verified planner state."""

    if not isinstance(plan, FamilyCalendarAutomationActivationPlan):
        raise FamilyCalendarAutomationActivationError(
            "A validated family-calendar automation activation plan is required.",
            stage="plan_recheck",
        )
    if global_confirmation != GLOBAL_SAFETY_BRAKE_CONFIRMATION:
        raise FamilyCalendarAutomationActivationError(
            "Exact global safety confirmation is required.",
            stage="global_confirmation",
        )
    if confirmation != FAMILY_CALENDAR_AUTOMATION_CONFIRMATION:
        raise FamilyCalendarAutomationActivationError(
            "Exact family-calendar automation confirmation is required.",
            stage="confirmation",
        )
    if expected_fingerprint != plan.fingerprint:
        raise FamilyCalendarAutomationActivationError(
            "Family-calendar automation fingerprint does not match.",
            stage="fingerprint",
        )

    run_status = command_runner or _run_command_status
    current_failed = False
    try:
        current = plan_family_calendar_automation_activation(
            config_path=plan.config_path,
            state_path=plan.state_path,
            planner_path=plan.planner_path,
            planner_runner_path=plan.planner_runner_path,
            command_runner=run_status,
            executable_locator=executable_locator,
        )
    except FamilyCalendarAutomationActivationError:
        current_failed = True
    if current_failed or not _plans_match(plan, current):
        raise FamilyCalendarAutomationActivationError(
            "Family-calendar automation inputs changed after preview.",
            stage="plan_recheck",
        )

    _run_mutation(current.unload_command(), run_status)
    runtime_state = _probe_runtime_state(current, run_status)
    if runtime_state != "unloaded":
        rollback = _rollback_activation(
            current,
            command_runner=run_status,
            executable_locator=executable_locator,
            lock_timeout=lock_timeout,
        )
        raise FamilyCalendarAutomationActivationError(
            "Family-calendar planner could not be safely unloaded.",
            stage="unload_verification",
            mutation_attempted=True,
            runtime_state=rollback.runtime_state,
            config_mode=rollback.config_mode,
            rollback_attempted=rollback.attempted,
            rollback_confirmed=rollback.confirmed,
        )

    config_write = _write_enabled_configuration(
        current,
        command_runner=run_status,
        lock_timeout=lock_timeout,
    )
    if config_write.failure_stage is not None:
        rollback = _rollback_activation(
            current,
            command_runner=run_status,
            executable_locator=executable_locator,
            lock_timeout=lock_timeout,
        )
        raise FamilyCalendarAutomationActivationError(
            "Family-calendar enabled configuration could not be verified.",
            stage=config_write.failure_stage,
            mutation_attempted=True,
            runtime_state=rollback.runtime_state,
            config_mode=rollback.config_mode,
            config_write_attempted=config_write.attempted,
            config_write_confirmed=config_write.confirmed,
            rollback_attempted=rollback.attempted,
            rollback_confirmed=rollback.confirmed,
        )

    _run_mutation(current.load_command(), run_status)
    runtime_state = _probe_runtime_state(current, run_status)
    readiness = None
    if runtime_state == "loaded":
        readiness = inspect_family_calendar_delivery_readiness(
            config_path=current.config_path,
            state_path=current.state_path,
            planner_path=current.planner_path,
            planner_runner_path=current.planner_runner_path,
            command_runner=run_status,
            executable_locator=executable_locator,
        )
    if (
        runtime_state == "loaded"
        and readiness is not None
        and readiness.status == "active"
        and readiness.ready_to_enable
        and readiness.automation_active
        and readiness.config_mode == DeliveryConfigMode.ENABLED.value
        and not readiness.writes_performed
        and not readiness.secret_read
        and not readiness.transport_called
    ):
        return FamilyCalendarAutomationActivationResult(
            fingerprint=current.fingerprint,
            recipient_count=readiness.recipient_count,
        )

    rollback = _rollback_activation(
        current,
        command_runner=run_status,
        executable_locator=executable_locator,
        lock_timeout=lock_timeout,
    )
    raise FamilyCalendarAutomationActivationError(
        "Family-calendar automation activation could not be verified.",
        stage=(
            "load_verification"
            if runtime_state != "loaded"
            else "readiness_verification"
        ),
        mutation_attempted=True,
        runtime_state=rollback.runtime_state,
        config_mode=rollback.config_mode,
        config_write_attempted=True,
        config_write_confirmed=True,
        rollback_attempted=rollback.attempted,
        rollback_confirmed=rollback.confirmed,
    )


def _plans_match(
    expected: FamilyCalendarAutomationActivationPlan,
    current: FamilyCalendarAutomationActivationPlan,
) -> bool:
    return (
        current.fingerprint == expected.fingerprint
        and current.source_snapshot.digest == expected.source_snapshot.digest
        and current.source_snapshot.config == expected.source_snapshot.config
        and current.target_digest == expected.target_digest
        and current.target_config == expected.target_config
        and current.launchctl_path == expected.launchctl_path
        and current.domain_target == expected.domain_target
        and current.service_target == expected.service_target
    )


def _write_enabled_configuration(
    plan: FamilyCalendarAutomationActivationPlan,
    *,
    command_runner: CommandStatusRunner,
    lock_timeout: float,
) -> _ConfigWriteOutcome:
    failure: str | None = None
    attempted = False
    confirmed = False
    try:
        with exclusive_file_lock(plan.config_path, timeout=lock_timeout):
            lock_path_for(plan.config_path).chmod(0o600)
            current = _read_config_snapshot(plan.config_path)
            if (
                current is None
                or current.digest != plan.source_snapshot.digest
                or current.config != plan.source_snapshot.config
            ):
                failure = "configuration_recheck"
            elif _probe_runtime_state(plan, command_runner) != "unloaded":
                failure = "runtime_recheck"
            else:
                attempted = True
                atomic_replace_text_under_external_lock(
                    plan.config_path,
                    plan.target_payload.decode("utf-8"),
                )
                plan.config_path.chmod(0o600)
                plan.config_path.parent.chmod(0o700)
                enabled = _read_config_snapshot(plan.config_path)
                if (
                    enabled is None
                    or enabled.digest != plan.target_digest
                    or enabled.config != plan.target_config
                ):
                    failure = "configuration_verification"
                else:
                    confirmed = True
                    if _probe_runtime_state(plan, command_runner) != "unloaded":
                        failure = "runtime_verification"
    except Exception:  # noqa: BLE001 - persistence details stay redacted.
        failure = "configuration_write"
    return _ConfigWriteOutcome(failure, attempted, confirmed)


def _rollback_activation(
    plan: FamilyCalendarAutomationActivationPlan,
    *,
    command_runner: CommandStatusRunner,
    executable_locator: ExecutableLocator,
    lock_timeout: float,
) -> _RollbackOutcome:
    _run_mutation(plan.unload_command(), command_runner)
    runtime_state = _probe_runtime_state(plan, command_runner)
    if runtime_state != "unloaded":
        return _RollbackOutcome(True, False, runtime_state, _config_mode(plan))
    if not _restore_dry_run_configuration(plan, lock_timeout=lock_timeout):
        return _RollbackOutcome(True, False, "unloaded", _config_mode(plan))

    _run_mutation(plan.load_command(), command_runner)
    runtime_state = _probe_runtime_state(plan, command_runner)
    if runtime_state != "loaded":
        return _RollbackOutcome(True, False, runtime_state, "dry_run")
    restored_failed = False
    try:
        restored = plan_family_calendar_automation_activation(
            config_path=plan.config_path,
            state_path=plan.state_path,
            planner_path=plan.planner_path,
            planner_runner_path=plan.planner_runner_path,
            command_runner=command_runner,
            executable_locator=executable_locator,
        )
    except FamilyCalendarAutomationActivationError:
        restored_failed = True
    confirmed = (
        not restored_failed
        and restored.fingerprint == plan.fingerprint
        and restored.source_snapshot.digest == plan.source_snapshot.digest
    )
    return _RollbackOutcome(True, confirmed, "loaded", "dry_run")


def _restore_dry_run_configuration(
    plan: FamilyCalendarAutomationActivationPlan,
    *,
    lock_timeout: float,
) -> bool:
    restored = False
    try:
        with exclusive_file_lock(plan.config_path, timeout=lock_timeout):
            lock_path_for(plan.config_path).chmod(0o600)
            current = _read_config_snapshot(plan.config_path)
            if current is None:
                return False
            if (
                current.digest == plan.source_snapshot.digest
                and current.config == plan.source_snapshot.config
            ):
                restored = True
            elif (
                current.digest == plan.target_digest
                and current.config == plan.target_config
            ):
                atomic_replace_text_under_external_lock(
                    plan.config_path,
                    plan.source_snapshot.payload.decode("utf-8"),
                )
                plan.config_path.chmod(0o600)
                plan.config_path.parent.chmod(0o700)
                restored = True
            if restored:
                verified = _read_config_snapshot(plan.config_path)
                restored = bool(
                    verified is not None
                    and verified.digest == plan.source_snapshot.digest
                    and verified.config == plan.source_snapshot.config
                )
    except Exception:  # noqa: BLE001 - rollback details stay redacted.
        return False
    return restored


def _read_config_snapshot(path: Path) -> _ConfigSnapshot | None:
    target = Path(path)
    try:
        before = target.read_bytes()
        config = load_family_calendar_delivery_config(target)
        after = target.read_bytes()
        raw = json.loads(after.decode("utf-8"))
    except Exception:  # noqa: BLE001 - private configuration stays redacted.
        return None
    if before != after or not isinstance(raw, dict):
        return None
    return _ConfigSnapshot(
        payload=after,
        digest=_digest(after),
        raw=raw,
        config=config,
    )


def _config_mode(plan: FamilyCalendarAutomationActivationPlan) -> str:
    snapshot = _read_config_snapshot(plan.config_path)
    if snapshot is None:
        return "unknown"
    if snapshot.config.mode is DeliveryConfigMode.DRY_RUN:
        return "dry_run"
    if snapshot.config.mode is DeliveryConfigMode.ENABLED:
        return "enabled"
    return "unknown"


def _probe_runtime_state(
    plan: FamilyCalendarAutomationActivationPlan,
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
    except Exception:  # noqa: BLE001 - verified state is authoritative.
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


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
