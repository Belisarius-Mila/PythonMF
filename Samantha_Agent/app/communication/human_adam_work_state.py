"""Read-only HA-01 projection. Source receipts remain the execution authority.

Revisions are content fingerprints, not ordered event cursors. IDs here are
stable view references, not new jobs. No I/O, clock, mutation or raw tool text.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_SCOPE = re.compile(r"[a-z][a-z0-9_-]{1,63}\Z")
_HEX = re.compile(r"[0-9a-f]{12}(?:[0-9a-f]{28})?\Z")
_COMPLETION_ACTIVE = {"queued", "running", "retry_waiting", "receipt_accepted"}
_COMPLETION_DONE = {"completed", "checkpoint_completed", "no_changes_completed"}
_COMPLETION_ERRORS = {"failed", "checkpoint_failed", "turn_failed", "receipt_missing",
                      "receipt_invalid", "delivery_uncertain", "attention_required", "integration_deferred"}
_RELEASE_ACTIVE = {"queued", "running"}
_RELEASE_DONE = {"completed", "dry_run_completed"}
_COMPLETION_STATES = _COMPLETION_ACTIVE | _COMPLETION_DONE | _COMPLETION_ERRORS | {"turn_started", "unverified", "none"}


def _map(value: object) -> Mapping:
    return value if isinstance(value, Mapping) else {}


def _id(value: object) -> str:
    return value if isinstance(value, str) and _ID.fullmatch(value) else ""


def _time(value: object) -> str:
    if not isinstance(value, str):
        return ""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc).isoformat() if parsed.tzinfo else ""
    except (ValueError, OverflowError):
        return ""


def _reference(kind: str, scope: str, thread: str, request: str) -> str:
    digest = hashlib.sha256(json.dumps([kind, scope, thread, request]).encode()).hexdigest()[:24]
    return f"{kind}:{digest}"


def build_human_adam_work_state(
    *, workstream_id: str, observed_at: str, session_snapshot: object = None,
    runtime_snapshot: object = None, completion_snapshot: object = None,
    completion_job_snapshot: object = None, release_snapshot: object = None,
    snapshot_consistent: bool = True, source_errors: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Project allowlisted facts; historical/foreign records cannot become a turn.

    Completion snapshots include the source record's client_message_id, added by
    the owning manager. Publication verification is accepted only from a scoped
    receipt with its exact target, never from a generic Cockpit deployment.
    """
    observed = _time(observed_at)
    scope = workstream_id if isinstance(workstream_id, str) and _SCOPE.fullmatch(workstream_id) else ""
    session, runtime = _map(session_snapshot), _map(runtime_snapshot)
    thread = _id(session.get("thread_id"))
    messages = session.get("messages")
    rows = [m for m in messages if isinstance(m, Mapping) and m.get("thread_id") == thread] if isinstance(messages, list) and thread else []
    latest = rows[-1] if rows else {}
    raw_message_state = latest.get("status")
    message_state = raw_message_state if isinstance(raw_message_state, str) else "unverified"
    latest_id = _id(latest.get("client_message_id"))
    latest_at = _time(latest.get("received_at"))
    incidents: list[dict[str, str]] = []
    history: list[dict[str, Any]] = []

    def incident(source: str, code: str) -> None:
        incidents.append({"source": source, "code": code})

    def operation(kind: str, request: str, state: str, updated: object, *, thread_id: str = "") -> dict[str, Any]:
        return {"operation_id": _reference(kind, scope, thread_id, request), "kind": kind,
                "state": state, "updated_at": _time(updated), "source_id": request,
                "client_request_id": request if kind != "publication" else None,
                "parent_operation_id": None}

    if runtime.get("reachable") is False:
        connection = "unreachable"
    elif runtime.get("reachable") is True and session.get("connected") is True:
        connection = "connected"
    elif runtime.get("reachable") is True and session.get("connected") is False:
        connection = "disconnected"
    else:
        connection = "unverified"
    model: dict[str, Any] = {"state": "idle", "operation": None}
    active = _map(session.get("active_turn"))
    active_id = _id(active.get("client_message_id"))
    if session.get("turn_busy") is True:
        started = _time(active.get("started_at"))
        if (active_id and latest_id == active_id and message_state == "pending"
                and latest_at and started and latest_at <= started <= observed):
            model = {"state": "running", "operation": operation("model", active_id, "awaiting_result",
                      session.get("updated_at"), thread_id=thread)}
            model["operation"]["started_at"] = _time(active.get("started_at"))
        else:
            model["state"] = "unverified"
            incident("model", "active_request_mismatch")
    elif (message_state in {"pending", "delivery_unknown"}
          or latest.get("recovery_required") is True
          or message_state == "completed" and latest.get("delivery_confirmed") is not True):
        model["state"] = "unverified"
        incident("model", "delivery_uncertain")
    elif latest_id:
        state = "completed" if message_state == "completed" and latest.get("delivery_confirmed") is True else "unverified"
        history.append(operation("model", latest_id, state, latest.get("completed_at"), thread_id=thread))
        if state == "unverified":
            model["state"] = "unverified"
            incident("model", "delivery_uncertain")

    completion: dict[str, Any] = {"state": "none", "operation": None}
    record, job = _map(completion_snapshot), _map(completion_job_snapshot)
    record_scoped = record.get("workstream_id") == scope and record.get("server_authoritative") is True and record.get("schema_version") == 1
    job_scoped = job.get("workstream_id") == scope
    candidates = ([record] if record_scoped else []) + ([job] if job_scoped else [])
    completion_source = max(candidates, key=lambda item: _time(item.get("updated_at")), default={})
    raw_state = completion_source.get("state")
    state = raw_state if isinstance(raw_state, str) and raw_state in _COMPLETION_STATES else "unverified"
    request = _id(completion_source.get("client_message_id"))
    updated = _time(completion_source.get("updated_at"))
    correlated = bool(latest_id and request == latest_id and latest_at and updated and latest_at <= updated <= observed)
    if request and completion_source:
        op = operation("completion", request, state, updated)
        if correlated:
            op["parent_operation_id"] = _reference("model", scope, thread, request)
        if state in _COMPLETION_ACTIVE and correlated and message_state == "completed" and latest.get("delivery_confirmed") is True:
            completion = {"state": "verifying", "operation": op}
        else:
            history.append(op)
            if state in _COMPLETION_ACTIVE:
                incident("completion", "completion_not_current")
            elif state in _COMPLETION_ERRORS and correlated:
                incident("completion", "completion_attention")
    elif record_scoped and record.get("state") == "unverified":
        incident("completion", "completion_unverified")

    publication: dict[str, Any] = {"state": "none", "operation": None, "outcome": "unverified"}
    release = _map(release_snapshot)
    release_scoped = bool(scope and release.get("workstream_id") == scope)
    if release_scoped:
        job_id = _id(release.get("job_id"))
        raw_release_state = release.get("state")
        release_state = raw_release_state if isinstance(raw_release_state, str) and raw_release_state in _RELEASE_ACTIVE | _RELEASE_DONE | {"attention"} else "unverified"
        created, updated_release = _time(release.get("created_at")), _time(release.get("updated_at"))
        raw_target = release.get("deployment_target")
        target = raw_target if isinstance(raw_target, str) else ""
        if job_id and created and updated_release and created <= updated_release <= observed and target in {"cockpit", "github_pages"}:
            op = operation("publication", job_id, release_state, updated_release)
            op["job_id"] = job_id
            op["deployment_target"] = target
            op["reported_active"] = release_state in _RELEASE_ACTIVE and release.get("active") is True
            # Receipt state is not a worker heartbeat or proof of live execution.
            op["liveness"] = "not_checked"
            publication["operation"] = op
            boundary = latest_at or _time(session.get("updated_at"))
            current = bool(op["reported_active"] and boundary and created >= boundary)
            publication["state"] = "reported_active" if current else "recorded"
            if not current:
                history.append(op)
            verification = _map(release.get("verification"))
            head = verification.get("main_head")
            target_short = release.get("target_short")
            exact_head = bool(isinstance(head, str) and _HEX.fullmatch(head) and len(head) == 40
                              and isinstance(target_short, str) and len(target_short) == 12
                              and head.startswith(target_short))
            verified = release.get("dry_run") is False and verification.get("state") == "deployed" and exact_head and verification.get("deployment_target") == target
            if target == "github_pages":
                verified = verified and type(verification.get("deployment_id")) is int and verification["deployment_id"] > 0 and verification.get("smoke_http_status") == 200
            else:
                verified = verified and verification.get("smoke_count") == 5
            if verified and release.get("dry_run") is False:
                publication["outcome"] = "deployment_verified"
                publication["verified_head"] = head
            elif release.get("dry_run") is True and release_state == "dry_run_completed":
                publication["outcome"] = "dry_run_completed"
            if release_state == "attention":
                incident("publication", "receipt_attention_verified_deployment" if verified else "receipt_attention")
            elif release_state in _RELEASE_ACTIVE and not current:
                incident("publication", "publication_not_current")
            elif release_state in _RELEASE_DONE and publication["outcome"] == "unverified":
                incident("publication", "publication_evidence_missing")
            elif release_state == "unverified":
                incident("publication", "publication_invalid")
        else:
            publication["state"] = "unverified"
            incident("publication", "publication_invalid")

    for source in ("session", "completion", "publication"):
        if source in source_errors:
            incident(source, "source_unavailable")
    if "session" in source_errors:
        model = {"state": "unverified", "operation": None}
    consistent = bool(snapshot_consistent is True and scope and observed)
    if not consistent:
        connection = "unverified"
        model = {"state": "unverified", "operation": None}
        completion = {"state": "unverified", "operation": None}
        publication = {"state": "unverified", "operation": None, "outcome": "unverified"}
        history = []
        incidents = [{"source": "scope", "code": "snapshot_changed"}]
    current_op = None
    if model["state"] == "running":
        summary_state, current_op = "running", model["operation"]
    elif not consistent or model["state"] == "unverified":
        summary_state = "unverified"
    elif completion["state"] == "verifying":
        summary_state, current_op = "verifying", completion["operation"]
    elif publication["state"] == "reported_active":
        summary_state, current_op = "publication_reported", publication["operation"]
    elif any(source in source_errors for source in ("session", "completion", "publication")):
        summary_state = "unverified"
    else:
        summary_state = {"connected": "ready", "disconnected": "disconnected"}.get(connection, "unavailable")
    summary = {"state": summary_state,
               "operation_id": current_op["operation_id"] if current_op else None}
    generation = session.get("connection_generation", 0)
    generation = generation if type(generation) is int and 0 <= generation <= 1_000_000 else 0
    result = {"schema_version": 1, "read_only": True, "writes_performed": False,
              "scope": {"workstream_id": scope or "unknown", "thread_id": thread if consistent else "",
                        "connection_generation": generation if consistent else 0},
              "observed_at": observed, "consistent": consistent, "connection": {"state": connection},
              "model": model, "completion": completion, "publication": publication,
              "history": history, "incidents": incidents, "summary": summary,
              "source_versions": {"session": _time(session.get("updated_at")) if consistent else "",
                                  "completion": updated if consistent and completion_source else "",
                                  "publication": _time(release.get("updated_at")) if consistent and release_scoped else ""},
              "actions": {"refresh_status": True, "inspect_work": True, "steer": False, "interrupt": False}}
    result["revision"] = hashlib.sha256(json.dumps({k: v for k, v in result.items() if k != "observed_at"}, sort_keys=True).encode()).hexdigest()
    return result
