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
    CapabilityRecord(
        capability_id="send_confirmed_sms_rcs",
        label="Send confirmed SMS/RCS",
        risk=RiskLevel.EXTERNAL_SEND,
        reads=("local contacts metadata", "local Messages delivery status database"),
        writes=("macOS Messages send",),
        requires_confirmation=True,
        confirmation_policy=ConfirmationPolicy.EXACT_CURRENT_MESSAGE,
        voice_allowed=VoicePolicy.APPROVAL_ONLY,
        mobile_allowed=MobilePolicy.APPROVAL_CARD,
        audit=AuditPolicy.REDACTED,
        tool="send_confirmed_sms_rcs",
        notes="Sends one SMS/RCS only after explicit current-message confirmation and verifies local delivery state.",
    ),
    CapabilityRecord(
        capability_id="archive_email_by_uid",
        label="Archive one email by UID",
        risk=RiskLevel.LOCAL_WRITE,
        reads=("confirmed iCloud Mail message by UID",),
        writes=("data/private EmailArchiveVault", "email activity state"),
        requires_confirmation=True,
        confirmation_policy=ConfirmationPolicy.EXACT_CURRENT_MESSAGE,
        voice_allowed=VoicePolicy.APPROVAL_ONLY,
        mobile_allowed=MobilePolicy.APPROVAL_CARD,
        audit=AuditPolicy.REDACTED,
        tool="archive_email_by_uid",
        notes="Provider is read-only; stores a local sensitive archive only after UID-specific confirmation.",
    ),
    CapabilityRecord(
        capability_id="save_selected_email_cases_from_uids",
        label="Save selected email cases from UIDs",
        risk=RiskLevel.LOCAL_WRITE,
        reads=("confirmed iCloud Mail messages by UID",),
        writes=("data/private EmailCaseVault case records",),
        requires_confirmation=True,
        confirmation_policy=ConfirmationPolicy.EXACT_CURRENT_MESSAGE,
        voice_allowed=VoicePolicy.APPROVAL_ONLY,
        mobile_allowed=MobilePolicy.APPROVAL_CARD,
        audit=AuditPolicy.REDACTED,
        tool="save_selected_email_cases_from_uids",
        notes="Reads selected emails and writes local case summaries only after all UIDs are confirmed.",
    ),
    CapabilityRecord(
        capability_id="prepare_forward_email_by_uid",
        label="Prepare local email forward draft",
        risk=RiskLevel.LOCAL_WRITE,
        reads=("confirmed source email by provider and UID", "local SMTP config metadata"),
        writes=("local outbox draft",),
        requires_confirmation=True,
        confirmation_policy=ConfirmationPolicy.EXACT_CURRENT_MESSAGE,
        voice_allowed=VoicePolicy.APPROVAL_ONLY,
        mobile_allowed=MobilePolicy.APPROVAL_CARD,
        audit=AuditPolicy.REDACTED,
        tool="prepare_forward_email_by_uid",
        notes="Prepares a local draft only; sending remains a separate external_send capability.",
    ),
    CapabilityRecord(
        capability_id="mark_reminder_done",
        label="Mark reminder done",
        risk=RiskLevel.LOCAL_WRITE,
        reads=("data/reminders/reminders.json selected reminder",),
        writes=("data/reminders/reminders.json reminder status",),
        requires_confirmation=True,
        confirmation_policy=ConfirmationPolicy.EXACT_CURRENT_MESSAGE,
        voice_allowed=VoicePolicy.APPROVAL_ONLY,
        mobile_allowed=MobilePolicy.APPROVAL_CARD,
        audit=AuditPolicy.SAFE_SUMMARY,
        tool="mark_reminder_done",
        notes="Changes only one local reminder status after explicit id-specific confirmation.",
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
