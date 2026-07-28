"""Read-only preview of family-calendar automation activation."""

from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from app.family_calendar_delivery_config import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    DELIVERY_CONFIG_SCHEMA_VERSION,
    DeliveryConfigMode,
)
from app.family_calendar_delivery_launchctl_load import (
    GLOBAL_SAFETY_BRAKE_CONFIRMATION,
)
from app.family_calendar_delivery_launchctl_preview import (
    ExecutableLocator,
    FamilyCalendarLaunchctlPreview,
    build_family_calendar_launchctl_preview,
)
from app.family_calendar_delivery_readiness import (
    DEFAULT_FAMILY_CALENDAR_PLANNER_PATH,
    DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
    CommandStatusRunner,
    FamilyCalendarDeliveryReadinessResult,
    inspect_family_calendar_delivery_readiness,
)
from app.family_calendar_delivery_store import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
)


FAMILY_CALENDAR_AUTOMATION_CONFIRMATION = (
    "ENABLE_FAMILY_CALENDAR_AUTOMATIC_DELIVERY"
)
FAMILY_CALENDAR_AUTOMATION_TARGET_MODE = "enabled"
_PLAN_VERSION = b"family-calendar-automation-preview-v1"
_UNCHANGED_CONFIG_FIELDS = (
    "schema_version",
    "smtp_provider",
    "sender_address",
    "recipients",
)


@dataclass(frozen=True, repr=False)
class FamilyCalendarAutomationPreview:
    """A redacted plan that does not itself mutate state or deliver email."""

    status: str
    issues: tuple[str, ...]
    warnings: tuple[str, ...]
    implementation_blockers: tuple[str, ...]
    current_mode: str
    recipient_count: int
    plan_fingerprint: str | None
    readiness: FamilyCalendarDeliveryReadinessResult
    launchctl_preview: FamilyCalendarLaunchctlPreview

    def __repr__(self) -> str:
        return (
            "FamilyCalendarAutomationPreview("
            f"status={self.status!r}, issue_count={len(self.issues)}, "
            f"warning_count={len(self.warnings)}, redacted=True)"
        )

    def operation_document(self) -> dict[str, object] | None:
        launchctl_operation = self.launchctl_preview.operation_document()
        if (
            self.status != "preview"
            or self.plan_fingerprint is None
            or launchctl_operation is None
        ):
            return None
        mode_change = {
            "field": "mode",
            "from": DeliveryConfigMode.DRY_RUN.value,
            "to": FAMILY_CALENDAR_AUTOMATION_TARGET_MODE,
        }
        return {
            "sequence": [
                {
                    "step": 1,
                    "action": "revalidate_plan_fingerprint_and_prerequisites",
                    "effect": "read_only",
                },
                {
                    "step": 2,
                    "action": "unload_planner",
                    "effect": "runtime_mutation",
                    "command": launchctl_operation["rollback"],
                },
                {
                    "step": 3,
                    "action": "verify_planner_unloaded",
                    "effect": "read_only",
                    "command": launchctl_operation["verify_unloaded"],
                },
                {
                    "step": 4,
                    "action": "atomic_replace_configuration_mode",
                    "effect": "private_config_write",
                    "change": mode_change,
                    "required_file_mode": "0600",
                    "continue_only_if_planner_unloaded": True,
                },
                {
                    "step": 5,
                    "action": "verify_enabled_configuration",
                    "effect": "read_only",
                },
                {
                    "step": 6,
                    "action": "load_planner",
                    "effect": "runtime_mutation",
                    "command": launchctl_operation["bootstrap"],
                    "continue_only_if_enabled_configuration_verified": True,
                },
                {
                    "step": 7,
                    "action": "verify_planner_loaded_and_ready",
                    "effect": "read_only",
                    "command": launchctl_operation["verify_loaded"],
                },
            ],
            "rollback": {
                "trigger": "any_failure_after_planner_unload",
                "sequence": [
                    {
                        "action": "ensure_planner_unloaded",
                        "command": launchctl_operation["rollback"],
                    },
                    {
                        "action": "verify_planner_unloaded",
                        "command": launchctl_operation["verify_unloaded"],
                    },
                    {
                        "action": "atomically_restore_dry_run_configuration",
                        "required_file_mode": "0600",
                        "continue_only_if_planner_unloaded": True,
                    },
                    {"action": "verify_dry_run_configuration"},
                    {
                        "action": "load_planner",
                        "command": launchctl_operation["bootstrap"],
                    },
                    {
                        "action": "verify_planner_loaded",
                        "command": launchctl_operation["verify_loaded"],
                    },
                ],
                "fail_closed_state": (
                    "planner_unloaded_with_configuration_requiring_manual_audit"
                ),
            },
        }

    def safe_document(self) -> dict[str, object]:
        readiness_document = self.readiness.safe_document()
        target_mode_supported = hasattr(DeliveryConfigMode, "ENABLED")
        prerequisite_checks = [
            check
            for check in readiness_document["checks"]
            if check["name"] != "automatic_mode"
        ]
        return {
            "status": self.status,
            "issues": list(self.issues),
            "warnings": list(self.warnings),
            "current_configuration": {
                "schema": DELIVERY_CONFIG_SCHEMA_VERSION,
                "mode": self.current_mode,
                "recipient_count": self.recipient_count,
            },
            "target_configuration": {
                "schema": DELIVERY_CONFIG_SCHEMA_VERSION,
                "mode": FAMILY_CALENDAR_AUTOMATION_TARGET_MODE,
                "only_changed_field": "mode",
                "unchanged_fields": list(_UNCHANGED_CONFIG_FIELDS),
            },
            "operational_prerequisites_ready": (
                self.status == "preview"
            ),
            "prerequisite_checks": prerequisite_checks,
            "implementation_blockers": list(self.implementation_blockers),
            "operation": self.operation_document(),
            "idempotency_contract": {
                "operation_identity": "event_key_plus_notification_offset",
                "persist_sending_before_transport": True,
                "existing_operation_blocks_duplicate": True,
                "single_worker_required": True,
            },
            "delivery_contract": {
                "notification_offsets": ["D-2", "D-1"],
                "recipient_count_required": 4,
                "d2_requires_missing_operation": True,
                "d1_allowed_when_d2_missing_or_not_sent": True,
                "d1_blocked_after_any_other_d2_outcome": True,
                "transport_requires_enabled_mode": True,
                "transport_requires_eligible_candidate": True,
                "transport_requires_worker_lock": True,
                "transport_requires_persisted_sending_state": True,
            },
            "recovery_contract": {
                "sending_blocks_activation": True,
                "delivery_unknown_blocks_activation": True,
                "partial_requires_manual_review_before_retry": True,
                "interrupted_send_becomes_delivery_unknown": True,
                "automatic_retry_after_unknown_mutation": False,
                "automatic_retry_after_any_activation_mutation": False,
            },
            "plan_fingerprint": self.plan_fingerprint,
            "global_confirmation_required": True,
            "required_global_confirmation": GLOBAL_SAFETY_BRAKE_CONFIRMATION,
            "confirmation_required": True,
            "required_confirmation": FAMILY_CALENDAR_AUTOMATION_CONFIRMATION,
            "target_mode_supported_by_runtime": target_mode_supported,
            "activation_implementation_available": True,
            "apply_available": True,
            "automatic_sending_enabled": False,
            "current_load_state_probed": True,
            "writes_performed": False,
            "launchctl_mutation_called": False,
            "secret_read": False,
            "transport_called": False,
            "redacted": True,
        }


def build_family_calendar_automation_preview(
    *,
    config_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    state_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
    planner_path: Path = DEFAULT_FAMILY_CALENDAR_PLANNER_PATH,
    planner_runner_path: Path = DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
    command_runner: CommandStatusRunner | None = None,
    executable_locator: ExecutableLocator = shutil.which,
) -> FamilyCalendarAutomationPreview:
    """Inspect and describe activation without writes, secrets, or transport."""

    config = Path(config_path).expanduser()
    state = Path(state_path).expanduser()
    planner = Path(planner_path).expanduser()
    runner = Path(planner_runner_path).expanduser()
    launch_before = build_family_calendar_launchctl_preview(
        config_path=config,
        planner_path=planner,
        planner_runner_path=runner,
        executable_locator=executable_locator,
    )
    readiness_kwargs = {
        "config_path": config,
        "state_path": state,
        "planner_path": planner,
        "planner_runner_path": runner,
        "executable_locator": executable_locator,
    }
    if command_runner is not None:
        readiness_kwargs["command_runner"] = command_runner
    readiness = inspect_family_calendar_delivery_readiness(**readiness_kwargs)
    launch_after = build_family_calendar_launchctl_preview(
        config_path=config,
        planner_path=planner,
        planner_runner_path=runner,
        executable_locator=executable_locator,
    )

    issues: list[str] = []
    if launch_before.status != "preview":
        issues.extend(
            f"launchctl_preview_{issue}" for issue in launch_before.issues
        )
    if launch_after.status != "preview":
        issues.extend(
            f"launchctl_preview_{issue}" for issue in launch_after.issues
        )
    if (
        launch_before.fingerprint is None
        or launch_after.fingerprint is None
        or launch_before.fingerprint != launch_after.fingerprint
    ):
        issues.append("inputs_changed_during_preview")
    implementation_blockers = tuple(
        dict.fromkeys(
            check.code
            for check in readiness.checks
            if check.name == "automatic_mode" and check.blocking
        )
    )
    issues.extend(
        check.code
        for check in readiness.checks
        if check.name != "automatic_mode" and check.blocking
    )
    if readiness.config_mode != DeliveryConfigMode.DRY_RUN.value:
        issues.append("configuration_not_dry_run")
    if readiness.automation_active:
        issues.append("automation_already_active")
    if (
        readiness.writes_performed
        or readiness.secret_read
        or readiness.transport_called
    ):
        issues.append("readiness_not_read_only")
    warnings = tuple(
        dict.fromkeys(
            check.code
            for check in readiness.checks
            if check.status == "warning"
        )
    )
    unique_issues = tuple(dict.fromkeys(issues))

    fingerprint = None
    if not unique_issues and launch_before.fingerprint is not None:
        fingerprint = _plan_fingerprint(
            launchctl_fingerprint=launch_before.fingerprint,
            readiness=readiness,
        )
    return FamilyCalendarAutomationPreview(
        status="preview" if not unique_issues else "blocked",
        issues=unique_issues,
        warnings=warnings,
        implementation_blockers=implementation_blockers,
        current_mode=readiness.config_mode,
        recipient_count=readiness.recipient_count,
        plan_fingerprint=fingerprint,
        readiness=readiness,
        launchctl_preview=launch_before,
    )


def _plan_fingerprint(
    *,
    launchctl_fingerprint: str,
    readiness: FamilyCalendarDeliveryReadinessResult,
) -> str:
    readiness_bytes = json.dumps(
        readiness.safe_document(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    digest = hashlib.sha256()
    for value in (
        _PLAN_VERSION,
        launchctl_fingerprint.encode("ascii"),
        readiness_bytes,
        FAMILY_CALENDAR_AUTOMATION_TARGET_MODE.encode("ascii"),
        FAMILY_CALENDAR_AUTOMATION_CONFIRMATION.encode("ascii"),
    ):
        digest.update(len(value).to_bytes(8, "big"))
        digest.update(value)
    return digest.hexdigest()
