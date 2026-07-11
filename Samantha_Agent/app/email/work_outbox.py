"""Non-destructive technical audit consumer for the first email outbox pilot."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.email.work_repository import EMAIL_WORK_DECISION_TOPIC
from app.work_repository import JsonWorkRepository, RepositoryMutation, WorkRepositoryError


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EMAIL_WORK_DECISIONS_PATH = (
    PROJECT_ROOT / "data" / "private" / "email_session_handoffs" / "email_processing_decisions.json"
)
DEFAULT_EMAIL_WORK_AUDIT_PATH = (
    PROJECT_ROOT / "data" / "private" / "email_session_handoffs" / "email_work_outbox_audit.json"
)
EMAIL_WORK_AUDIT_ACTIONS = {"process", "ignore", "trash_requested", "clear"}


def process_email_work_audit_once(
    *,
    decisions_path: Path = DEFAULT_EMAIL_WORK_DECISIONS_PATH,
    audit_path: Path = DEFAULT_EMAIL_WORK_AUDIT_PATH,
    worker_id: str = "email-work-audit-pilot",
    now: datetime | str | None = None,
    lease_seconds: int = 30,
) -> dict[str, Any]:
    source = JsonWorkRepository(decisions_path, default={"decisions": {}})
    leases = source.lease_outbox(
        lease_owner=worker_id,
        limit=1,
        lease_seconds=lease_seconds,
        now=now,
    )
    if not leases:
        return {"ok": True, "status": "idle", "leased": 0, "audited": 0, "acked": 0, "retried": 0}

    lease = leases[0]
    validation_error = _validate_email_work_audit_lease(lease.topic, lease.aggregate_id, lease.payload)
    if validation_error:
        retried = source.retry_outbox(
            event_id=lease.event_id,
            lease_token=lease.lease_token,
            retry_after_seconds=60,
            error_code=validation_error,
            now=now,
        )
        return {
            "ok": False,
            "status": "retry_scheduled" if retried else "lease_lost",
            "leased": 1,
            "audited": 0,
            "acked": 0,
            "retried": int(retried),
        }

    action = str(lease.payload["action"])
    audit_repository = JsonWorkRepository(audit_path, default={"events": {}})
    try:
        audit_result = audit_repository.transact(
            lambda document: _record_audit_event(
                document,
                event_id=lease.event_id,
                aggregate_id=lease.aggregate_id,
                action=action,
                attempt=lease.attempts,
                processed_at=_format_now(now),
            ),
            operation_id=f"email-work-audit:{lease.event_id}",
        )
    except (OSError, WorkRepositoryError, TypeError, ValueError):
        retried = source.retry_outbox(
            event_id=lease.event_id,
            lease_token=lease.lease_token,
            retry_after_seconds=60,
            error_code="audit_write_failed",
            now=now,
        )
        return {
            "ok": False,
            "status": "retry_scheduled" if retried else "lease_lost",
            "leased": 1,
            "audited": 0,
            "acked": 0,
            "retried": int(retried),
        }

    acked = source.acknowledge_outbox(
        event_id=lease.event_id,
        lease_token=lease.lease_token,
        now=now,
    )
    return {
        "ok": acked,
        "status": "audited" if acked else "lease_lost_after_audit",
        "leased": 1,
        "audited": int(audit_result.changed or audit_result.idempotent_replay),
        "acked": int(acked),
        "retried": 0,
    }


def read_email_work_audit_count(path: Path = DEFAULT_EMAIL_WORK_AUDIT_PATH) -> int:
    try:
        document = JsonWorkRepository(path, default={"events": {}}).read()
    except WorkRepositoryError:
        return 0
    events = document.get("events", {})
    return len(events) if isinstance(events, dict) else 0


def _record_audit_event(
    document: dict[str, Any],
    *,
    event_id: str,
    aggregate_id: str,
    action: str,
    attempt: int,
    processed_at: str,
) -> RepositoryMutation:
    raw_events = document.get("events", {})
    if not isinstance(raw_events, dict):
        raise WorkRepositoryError("Email work audit events must be an object.")
    if event_id in raw_events:
        return RepositoryMutation(
            document=document,
            result={"event_id": event_id},
            changed=False,
        )
    events = copy.deepcopy(raw_events)
    events[event_id] = {
        "event_id": event_id,
        "aggregate_id": aggregate_id,
        "action": action,
        "attempt": attempt,
        "processed_at": processed_at,
    }
    updated = dict(document)
    updated["events"] = events
    return RepositoryMutation(document=updated, result={"event_id": event_id})


def _validate_email_work_audit_lease(topic: str, aggregate_id: str, payload: dict[str, Any]) -> str:
    if topic != EMAIL_WORK_DECISION_TOPIC:
        return "unsupported_topic"
    if not aggregate_id.startswith("emailwork-"):
        return "invalid_aggregate"
    if set(payload) != {"action"} or str(payload.get("action", "")) not in EMAIL_WORK_AUDIT_ACTIONS:
        return "invalid_payload"
    return ""


def _format_now(value: datetime | str | None) -> str:
    if isinstance(value, str):
        return value
    resolved = value or datetime.now(timezone.utc)
    return resolved.astimezone(timezone.utc).replace(microsecond=0).isoformat()
