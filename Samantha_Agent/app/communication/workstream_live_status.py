"""Build one redacted read-only live status for a canonical workstream.

The builder is deliberately side-effect free.  It receives snapshots collected
by existing authorities and returns only allowlisted operational evidence.  It
does not read or write Git, deployment receipts, session files, handoffs, or
TVBCP documents and it never reconnects a runtime.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any


LIVE_STATUS_SCHEMA_VERSION = 1
MAX_SAFE_COUNT = 1_000_000
_CODE_STAMP_RE = re.compile(r"[0-9a-f]{16}")
_FULL_HEAD_RE = re.compile(r"[0-9a-f]{40}")
_SHORT_HEAD_RE = re.compile(r"[0-9a-f]{7,40}")
_WORKSTREAM_ID_RE = re.compile(r"[a-z][a-z0-9_-]{1,63}")
_WORKSPACE_RELATIONS = frozenset(
    {"aligned", "local_ahead", "source_ahead", "diverged"}
)
_REMOTE_STATES = {
    "aligned": "aligned",
    "fast_forward_available": "origin_ahead",
    "local_ahead": "local_ahead",
    "ready": "local_ahead",
    "diverged": "diverged",
}
_OVERALL_STATES = frozenset(
    {"current", "current_runtime_disconnected", "attention_required", "unverified"}
)
_MAIN_STATES = frozenset(
    {
        "aligned",
        "dirty",
        "origin_ahead",
        "local_ahead",
        "diverged",
        "origin_unverified",
        "unverified",
    }
)
_DEPLOYMENT_STATES = frozenset(
    {
        "verified_current",
        "pending_restart",
        "verified_other_main",
        "code_mismatch",
        "current_head_server_unverified",
        "unavailable",
        "unverified",
    }
)
_WORKSPACE_STATES = frozenset(
    {"aligned_clean", "attention_required", "unverified"}
)
_RUNTIME_STATES = frozenset(
    {
        "connected",
        "disconnected",
        "unreachable",
        "busy",
        "delivery_uncertain",
        "unverified",
    }
)


def _safe_count(value: object) -> int:
    try:
        count = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return min(MAX_SAFE_COUNT, max(0, count))


def _safe_full_head(value: object) -> str:
    candidate = str(value or "").strip().casefold()
    return candidate if _FULL_HEAD_RE.fullmatch(candidate) else ""


def _safe_deployment_head(value: object) -> str:
    candidate = str(value or "").strip().casefold()
    return candidate if _SHORT_HEAD_RE.fullmatch(candidate) else ""


def _safe_code_stamp(value: object) -> str:
    candidate = str(value or "").strip().casefold()
    return candidate if _CODE_STAMP_RE.fullmatch(candidate) else ""


def _safe_timestamp(value: object) -> str:
    candidate = str(value or "").strip()
    try:
        parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError:
        return ""
    if parsed.tzinfo is None:
        return ""
    return parsed.isoformat()


def _safe_mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _safe_state(value: object, allowed: frozenset[str]) -> str:
    candidate = str(value or "").strip()
    return candidate if candidate in allowed else "unverified"


def _safe_bool_text(value: object) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return "unknown"


def _main_status(
    source: Mapping[str, Any],
    remote: Mapping[str, Any],
) -> dict[str, Any]:
    branch = str(source.get("source_branch") or "").strip()
    head = _safe_full_head(source.get("source_head"))
    pending_count = _safe_count(source.get("source_pending_changes"))
    origin_head = _safe_full_head(remote.get("origin_head"))
    remote_local_head = _safe_full_head(remote.get("local_head"))
    remote_state = str(remote.get("state") or "").strip()
    remote_proof = bool(
        remote.get("read_only") is True
        and remote.get("writes_performed") is False
        and remote_local_head
        and origin_head
        and remote_local_head == head
        and remote_state in _REMOTE_STATES
    )

    if branch != "main" or not head:
        state = "unverified"
    elif pending_count:
        state = "dirty"
    elif not remote_proof:
        state = "origin_unverified"
    else:
        state = _REMOTE_STATES[remote_state]
    return {
        "state": state,
        "branch": branch if branch == "main" else "unknown",
        "head_short": head[:12],
        "origin_short": origin_head[:12] if remote_proof else "",
        "pending_change_count": pending_count,
        "origin_evidence_read_only": remote_proof,
    }


def _workspace_status(
    snapshots: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    relation_counts = {relation: 0 for relation in sorted(_WORKSPACE_RELATIONS)}
    dirty_count = 0
    unsafe_count = 0
    local_commit_count = 0
    source_pending_change_count = 0
    for snapshot in snapshots:
        relation = str(snapshot.get("workspace_relation") or "").strip()
        unsafe = False
        if relation in relation_counts:
            relation_counts[relation] += 1
        else:
            unsafe = True
        dirty = bool(snapshot.get("dirty"))
        dirty_count += int(dirty)
        local_commit_count += _safe_count(snapshot.get("local_commit_count"))
        source_pending_change_count = max(
            source_pending_change_count,
            _safe_count(snapshot.get("source_pending_changes")),
        )
        if (
            snapshot.get("ok") is not True
            or snapshot.get("prepared") is not True
            or snapshot.get("project_ready") is not True
            or bool(snapshot.get("remotes"))
            or bool(snapshot.get("has_remotes"))
            or bool(snapshot.get("local_checkpoint_ahead"))
            or bool(snapshot.get("local_checkpoint_preserved"))
        ):
            unsafe = True
        unsafe_count += int(unsafe)

    count = len(snapshots)
    aligned_count = relation_counts["aligned"]
    state = (
        "aligned_clean"
        if (
            count > 0
            and aligned_count == count
            and dirty_count == 0
            and unsafe_count == 0
            and local_commit_count == 0
        )
        else ("unverified" if count == 0 else "attention_required")
    )
    return {
        "state": state,
        "count": count,
        "aligned_count": aligned_count,
        "dirty_count": dirty_count,
        "unsafe_count": unsafe_count,
        "local_commit_count": min(MAX_SAFE_COUNT, local_commit_count),
        "source_pending_change_count": source_pending_change_count,
        "relation_counts": relation_counts,
    }


def _has_current_uncertain_delivery(session: Mapping[str, Any]) -> bool:
    messages = session.get("messages")
    if not isinstance(messages, Sequence) or isinstance(messages, (str, bytes)):
        return False
    for raw in reversed(messages):
        item = _safe_mapping(raw)
        status = str(item.get("status") or "").strip()
        if status == "completed":
            return False
        if (
            status in {"pending", "delivery_unknown"}
            or item.get("recovery_required") is True
        ):
            return True
    return False


def _runtime_status(
    runtime: Mapping[str, Any],
    session: Mapping[str, Any],
) -> dict[str, Any]:
    reachable_known = isinstance(runtime.get("reachable"), bool)
    reachable = runtime.get("reachable") is True
    connected_known = isinstance(session.get("connected"), bool)
    connected = session.get("connected") is True
    turn_busy = bool(session.get("turn_busy") or session.get("active_turn"))
    delivery_uncertain = _has_current_uncertain_delivery(session)

    if not reachable_known or not connected_known:
        state = "unverified"
    elif delivery_uncertain:
        state = "delivery_uncertain"
    elif turn_busy:
        state = "busy"
    elif not reachable:
        state = "unreachable"
    elif connected:
        state = "connected"
    else:
        state = "disconnected"
    return {
        "state": state,
        "reachable": reachable if reachable_known else None,
        "connected": connected if connected_known else None,
        "turn_busy": turn_busy,
        "delivery_uncertain": delivery_uncertain,
    }


def _deployment_status(
    deployment: Mapping[str, Any],
    server: Mapping[str, Any],
    *,
    current_head_short: str,
) -> dict[str, Any]:
    raw_state = str(deployment.get("state") or "").strip()
    deployment_head = _safe_deployment_head(
        deployment.get("main_head") or deployment.get("main_short")
    )
    gate = _safe_mapping(deployment.get("gate"))
    smoke = _safe_mapping(deployment.get("smoke"))
    gate_mode = str(
        deployment.get("gate_mode") or gate.get("mode") or "full"
    ).strip()
    test_count = _safe_count(
        deployment.get("test_count") or gate.get("test_count")
    )
    smoke_count = _safe_count(
        deployment.get("smoke_count") or smoke.get("check_count")
    )
    gate_passed = bool(
        deployment.get("gate_passed") is True or gate.get("passed") is True
    )
    smoke_passed = bool(
        deployment.get("smoke_passed") is True or smoke.get("passed") is True
    )
    deployed_at = _safe_timestamp(deployment.get("deployed_at"))
    expected_stamp = _safe_code_stamp(deployment.get("expected_code_stamp"))
    observed_stamp = _safe_code_stamp(server.get("code_stamp"))
    gate_evidence_valid = bool(
        (gate_mode == "full" and test_count > 0)
        or (gate_mode == "quick" and test_count == 0)
    )
    head_matches = bool(
        deployment_head
        and current_head_short
        and (
            current_head_short.startswith(deployment_head)
            or deployment_head.startswith(current_head_short)
        )
    )

    if not deployment:
        state = "unavailable"
    elif raw_state == "pending_restart":
        state = (
            "pending_restart"
            if deployment_head and gate_evidence_valid
            else "unverified"
        )
    elif (
        raw_state != "deployed"
        or not deployment_head
        or not deployed_at
        or not gate_passed
        or not smoke_passed
        or not gate_evidence_valid
        or smoke_count <= 0
    ):
        state = "unverified"
    elif not head_matches:
        state = "verified_other_main"
    elif not expected_stamp or not observed_stamp:
        state = "current_head_server_unverified"
    elif expected_stamp != observed_stamp:
        state = "code_mismatch"
    else:
        state = "verified_current"
    return {
        "state": state,
        "main_short": deployment_head[:12],
        "deployed_at": deployed_at,
        "test_count": test_count,
        "gate_mode": gate_mode if gate_mode in {"full", "quick"} else "unknown",
        "smoke_count": smoke_count,
        "current_head": head_matches,
        "code_stamp_verified": state == "verified_current",
    }


def _overall_state(
    *,
    main_state: str,
    workspace_state: str,
    deployment_state: str,
    runtime_state: str,
) -> str:
    if main_state in {"unverified", "origin_unverified"}:
        return "unverified"
    if workspace_state == "unverified":
        return "unverified"
    if deployment_state in {
        "unavailable",
        "unverified",
        "current_head_server_unverified",
    }:
        return "unverified"
    if runtime_state == "unverified":
        return "unverified"
    if main_state in {"dirty", "local_ahead", "origin_ahead", "diverged"}:
        return "attention_required"
    if workspace_state == "attention_required":
        return "attention_required"
    if deployment_state in {
        "pending_restart",
        "verified_other_main",
        "code_mismatch",
    }:
        return "attention_required"
    if runtime_state in {"delivery_uncertain", "busy"}:
        return "attention_required"
    if (
        main_state != "aligned"
        or workspace_state != "aligned_clean"
        or deployment_state != "verified_current"
    ):
        return "unverified"
    if runtime_state == "connected":
        return "current"
    return "current_runtime_disconnected"


def build_workstream_live_status(
    *,
    workstream_id: str,
    observed_at: str,
    source_snapshot: Mapping[str, Any],
    remote_snapshot: Mapping[str, Any],
    workspace_snapshots: Sequence[Mapping[str, Any]],
    deployment_snapshot: Mapping[str, Any] | None = None,
    runtime_snapshot: Mapping[str, Any] | None = None,
    session_snapshot: Mapping[str, Any] | None = None,
    server_snapshot: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return one side-effect-free, redacted operational evidence snapshot."""

    clean_workstream_id = str(workstream_id or "").strip().casefold()
    if not _WORKSTREAM_ID_RE.fullmatch(clean_workstream_id):
        clean_workstream_id = "unknown"
    clean_observed_at = _safe_timestamp(observed_at)
    main = _main_status(
        _safe_mapping(source_snapshot),
        _safe_mapping(remote_snapshot),
    )
    workspaces = _workspace_status(
        tuple(_safe_mapping(item) for item in workspace_snapshots)
    )
    runtime = _runtime_status(
        _safe_mapping(runtime_snapshot),
        _safe_mapping(session_snapshot),
    )
    deployment = _deployment_status(
        _safe_mapping(deployment_snapshot),
        _safe_mapping(server_snapshot),
        current_head_short=str(main.get("head_short") or ""),
    )
    overall_state = _overall_state(
        main_state=str(main["state"]),
        workspace_state=str(workspaces["state"]),
        deployment_state=str(deployment["state"]),
        runtime_state=str(runtime["state"]),
    )
    if clean_workstream_id == "unknown" or not clean_observed_at:
        overall_state = "unverified"
    return {
        "schema_version": LIVE_STATUS_SCHEMA_VERSION,
        "read_only": True,
        "writes_performed": False,
        "state": overall_state,
        "observed_at": clean_observed_at,
        "workstream_id": clean_workstream_id,
        "main": main,
        "deployment": deployment,
        "workspaces": workspaces,
        "runtime": runtime,
    }


def workstream_live_status_model_block(live_status: object) -> str:
    """Serialize only the redacted schema into one compact model-input block."""

    value = _safe_mapping(live_status)
    clean_workstream_id = str(value.get("workstream_id") or "").strip().casefold()
    valid = bool(
        value.get("schema_version") == LIVE_STATUS_SCHEMA_VERSION
        and value.get("read_only") is True
        and value.get("writes_performed") is False
        and _WORKSTREAM_ID_RE.fullmatch(clean_workstream_id)
    )
    if not valid:
        clean_workstream_id = "unknown"
        value = {}

    main = _safe_mapping(value.get("main"))
    deployment = _safe_mapping(value.get("deployment"))
    workspaces = _safe_mapping(value.get("workspaces"))
    runtime = _safe_mapping(value.get("runtime"))
    overall_state = _safe_state(value.get("state"), _OVERALL_STATES)
    main_state = _safe_state(main.get("state"), _MAIN_STATES)
    deployment_state = _safe_state(
        deployment.get("state"),
        _DEPLOYMENT_STATES,
    )
    workspace_state = _safe_state(
        workspaces.get("state"),
        _WORKSPACE_STATES,
    )
    runtime_state = _safe_state(runtime.get("state"), _RUNTIME_STATES)
    return "\n".join(
        (
            "[WORKSTREAM_LIVE_STATUS]",
            f"schema_version={LIVE_STATUS_SCHEMA_VERSION}",
            "read_only=true",
            "writes_performed=false",
            f"state={overall_state}",
            f"workstream_id={clean_workstream_id}",
            f"main_state={main_state}",
            f"main_head={_safe_deployment_head(main.get('head_short')) or 'unknown'}",
            f"origin_head={_safe_deployment_head(main.get('origin_short')) or 'unknown'}",
            f"deployment_state={deployment_state}",
            f"deployment_main={_safe_deployment_head(deployment.get('main_short')) or 'unknown'}",
            f"deployment_test_count={_safe_count(deployment.get('test_count'))}",
            f"deployment_smoke_count={_safe_count(deployment.get('smoke_count'))}",
            f"deployment_code_stamp_verified={_safe_bool_text(deployment.get('code_stamp_verified'))}",
            f"workspaces_state={workspace_state}",
            f"workspace_count={_safe_count(workspaces.get('count'))}",
            f"aligned_workspace_count={_safe_count(workspaces.get('aligned_count'))}",
            f"dirty_workspace_count={_safe_count(workspaces.get('dirty_count'))}",
            f"runtime_state={runtime_state}",
            f"runtime_reachable={_safe_bool_text(runtime.get('reachable'))}",
            f"runtime_connected={_safe_bool_text(runtime.get('connected'))}",
            f"turn_busy={_safe_bool_text(runtime.get('turn_busy'))}",
            f"delivery_uncertain={_safe_bool_text(runtime.get('delivery_uncertain'))}",
            "[/WORKSTREAM_LIVE_STATUS]",
        )
    )
