from __future__ import annotations

from app.capabilities.models import (
    AuditPolicy,
    CapabilityRecord,
    ConfirmationPolicy,
    MobilePolicy,
    RiskLevel,
    VoicePolicy,
)


CAPABILITIES: tuple[CapabilityRecord, ...] = (
    CapabilityRecord(
        capability_id="git_safety_check",
        label="Git staged safety check",
        risk=RiskLevel.READ_ONLY,
        reads=(
            "git staged file list",
            "branch guard state",
            "memory/infrastructure/git_branch_archive.md",
        ),
        writes=(),
        requires_confirmation=False,
        voice_allowed=VoicePolicy.ALLOWED,
        mobile_allowed=MobilePolicy.ALLOWED,
        audit=AuditPolicy.SAFE_SUMMARY,
        tool="scripts/git_safety_check.py",
        notes="Checks staged content and branch risk before commit.",
    ),
    CapabilityRecord(
        capability_id="work_context_guard",
        label="Work context guard",
        risk=RiskLevel.READ_ONLY,
        reads=(
            "git status",
            "branch guard state",
            "merge/rebase/cherry-pick/revert markers",
        ),
        writes=(),
        requires_confirmation=False,
        voice_allowed=VoicePolicy.ALLOWED,
        mobile_allowed=MobilePolicy.ALLOWED,
        audit=AuditPolicy.SAFE_SUMMARY,
        tool="scripts/work_context_guard.py",
        notes="Read-only guard before switching topics or starting a new session.",
    ),
    CapabilityRecord(
        capability_id="git_push_main_after_guard",
        label="Routine push to origin main after green guard",
        risk=RiskLevel.GIT_PUBLISH,
        reads=(
            "git branch and upstream state",
            "git working tree state",
            "last commit file list",
        ),
        writes=("git push origin main",),
        requires_confirmation=False,
        voice_allowed=VoicePolicy.ALLOWED,
        mobile_allowed=MobilePolicy.ALLOWED,
        audit=AuditPolicy.SAFE_SUMMARY,
        tool="scripts/git_push_guard.py + git push origin main",
        notes="Allowed without another question only after git_push_guard.py reports routine push allowed.",
        metadata={"requires_green_guard": "true", "allowed_remote": "origin", "allowed_branch": "main"},
    ),
    CapabilityRecord(
        capability_id="quick_notes_action_status",
        label="Quick Notes action inbox",
        risk=RiskLevel.READ_ONLY,
        reads=(
            "data/private/quick_notes metadata",
            "selected quick note text summaries",
        ),
        writes=(),
        requires_confirmation=False,
        voice_allowed=VoicePolicy.ALLOWED,
        mobile_allowed=MobilePolicy.ALLOWED,
        audit=AuditPolicy.SAFE_SUMMARY,
        tool="quick_notes_action_status",
        notes="Read-only overview for choosing later confirmed actions.",
    ),
    CapabilityRecord(
        capability_id="send_prepared_email_draft",
        label="Send prepared email draft",
        risk=RiskLevel.EXTERNAL_SEND,
        reads=("local outbox draft",),
        writes=("SMTP send", "best-effort Sent copy"),
        requires_confirmation=True,
        confirmation_policy=ConfirmationPolicy.EXACT_CURRENT_MESSAGE,
        voice_allowed=VoicePolicy.APPROVAL_ONLY,
        mobile_allowed=MobilePolicy.APPROVAL_CARD,
        audit=AuditPolicy.REDACTED,
        tool="send_prepared_email_draft",
        notes="External send remains gated by exact confirmation.",
    ),
)


def all_capabilities() -> tuple[CapabilityRecord, ...]:
    return CAPABILITIES


def capability_map() -> dict[str, CapabilityRecord]:
    return {item.capability_id: item for item in CAPABILITIES}


def get_capability(capability_id: str) -> CapabilityRecord:
    normalized = capability_id.strip()
    try:
        return capability_map()[normalized]
    except KeyError as exc:
        raise KeyError(f"unknown capability_id: {capability_id!r}") from exc


def validate_registry(records: tuple[CapabilityRecord, ...] = CAPABILITIES) -> tuple[str, ...]:
    errors: list[str] = []
    seen: set[str] = set()
    for record in records:
        if record.capability_id in seen:
            errors.append(f"duplicate capability_id: {record.capability_id}")
        seen.add(record.capability_id)
        if record.capability_id == "git_push_main_after_guard":
            if record.risk != RiskLevel.GIT_PUBLISH:
                errors.append("git_push_main_after_guard must use git_publish risk")
            if record.metadata.get("requires_green_guard") != "true":
                errors.append("git_push_main_after_guard must require a green guard")
        if record.risk == RiskLevel.EXTERNAL_SEND:
            if record.confirmation_policy != ConfirmationPolicy.EXACT_CURRENT_MESSAGE:
                errors.append(f"{record.capability_id} external_send must use exact_current_message")
            if record.audit == AuditPolicy.FULL_LOCAL:
                errors.append(f"{record.capability_id} external_send cannot use full_local audit")
    return tuple(errors)
