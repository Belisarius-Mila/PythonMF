"""Durable server truth for the last Human–Adam development completion.

The model receipt is only a request to finish one writable turn.  This private
store records what the server actually did with that request and exposes only a
small redacted status to the UI and to the next model turn.
"""

from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from app.codex_appserver import AppServerError
from app.file_persistence import FilePersistenceError, atomic_write_json


COMPLETION_STATUS_SCHEMA = 1
TURN_STARTED = "turn_started"
DELIVERY_UNCERTAIN = "delivery_uncertain"
TURN_FAILED = "turn_failed"
RECEIPT_MISSING = "receipt_missing"
RECEIPT_INVALID = "receipt_invalid"
RECEIPT_ACCEPTED = "receipt_accepted"
INTEGRATION_DEFERRED = "integration_deferred"
CHECKPOINT_FAILED = "checkpoint_failed"
CHECKPOINT_COMPLETED = "checkpoint_completed"
ATTENTION_REQUIRED = "attention_required"
UNVERIFIED = "unverified"
NO_COMPLETION = "none"

_RECORD_STATES = frozenset(
    {
        TURN_STARTED,
        DELIVERY_UNCERTAIN,
        TURN_FAILED,
        RECEIPT_MISSING,
        RECEIPT_INVALID,
        RECEIPT_ACCEPTED,
        INTEGRATION_DEFERRED,
        CHECKPOINT_FAILED,
        CHECKPOINT_COMPLETED,
    }
)
_PUBLIC_STATES = _RECORD_STATES | {
    ATTENTION_REQUIRED,
    UNVERIFIED,
    NO_COMPLETION,
}
_FAILURE_CODES = frozenset(
    {
        "",
        "delivery_uncertain",
        "turn_failed",
        "metadata_missing",
        "metadata_invalid",
        "integration_deferred",
        "checkpoint_failed",
    }
)
_HEAD_RE = re.compile(r"[0-9a-f]{40}")
_WORKSTREAM_ID_RE = re.compile(r"[a-z][a-z0-9_-]{1,63}")
_CLIENT_MESSAGE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{7,127}")
MAX_SAFE_COUNT = 1_000_000


class HumanAdamCompletionStatusError(AppServerError):
    """Raised when the private completion status cannot be trusted."""


@dataclass(frozen=True)
class HumanAdamCompletionRecord:
    state: str
    workstream_id: str
    client_message_id: str
    base_head: str
    checkpoint_head: str
    failure_code: str
    answer_persisted: bool | None
    remote_push_deferred: bool
    pending_remote_commit_count: int
    created_at: str
    updated_at: str


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _validated_timestamp(value: object, *, label: str) -> str:
    text = str(value or "").strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HumanAdamCompletionStatusError(
            f"Stav dokončení nemá platný čas {label}."
        ) from exc
    if parsed.tzinfo is None:
        raise HumanAdamCompletionStatusError(
            f"Stav dokončení nemá časovou zónu {label}."
        )
    return parsed.isoformat()


def _safe_count(value: object) -> int:
    try:
        count = int(value or 0)
    except (TypeError, ValueError) as exc:
        raise HumanAdamCompletionStatusError(
            "Stav dokončení má neplatný počet čekajících commitů."
        ) from exc
    if count < 0 or count > MAX_SAFE_COUNT:
        raise HumanAdamCompletionStatusError(
            "Stav dokončení má neplatný počet čekajících commitů."
        )
    return count


def _validated_record(raw: object) -> HumanAdamCompletionRecord:
    required = {
        "state",
        "workstream_id",
        "client_message_id",
        "base_head",
        "checkpoint_head",
        "failure_code",
        "answer_persisted",
        "remote_push_deferred",
        "pending_remote_commit_count",
        "created_at",
        "updated_at",
    }
    if not isinstance(raw, dict) or set(raw) != required:
        raise HumanAdamCompletionStatusError(
            "Private stav dokončení má neznámé schéma."
        )
    state = str(raw.get("state") or "").strip()
    workstream_id = str(raw.get("workstream_id") or "").strip().casefold()
    client_message_id = str(raw.get("client_message_id") or "").strip()
    base_head = str(raw.get("base_head") or "").strip().casefold()
    checkpoint_head = str(raw.get("checkpoint_head") or "").strip().casefold()
    failure_code = str(raw.get("failure_code") or "").strip()
    answer_persisted = raw.get("answer_persisted")
    remote_push_deferred = raw.get("remote_push_deferred")
    pending_count = _safe_count(raw.get("pending_remote_commit_count"))
    created_at = _validated_timestamp(raw.get("created_at"), label="zahájení")
    updated_at = _validated_timestamp(raw.get("updated_at"), label="aktualizace")
    if (
        state not in _RECORD_STATES
        or not _WORKSTREAM_ID_RE.fullmatch(workstream_id)
        or not _CLIENT_MESSAGE_ID_RE.fullmatch(client_message_id)
        or not _HEAD_RE.fullmatch(base_head)
        or (checkpoint_head and not _HEAD_RE.fullmatch(checkpoint_head))
        or failure_code not in _FAILURE_CODES
        or (
            answer_persisted is not None
            and not isinstance(answer_persisted, bool)
        )
        or not isinstance(remote_push_deferred, bool)
        or (state == CHECKPOINT_COMPLETED and not checkpoint_head)
        or (state != CHECKPOINT_COMPLETED and checkpoint_head)
    ):
        raise HumanAdamCompletionStatusError(
            "Private stav dokončení má neplatné údaje."
        )
    return HumanAdamCompletionRecord(
        state=state,
        workstream_id=workstream_id,
        client_message_id=client_message_id,
        base_head=base_head,
        checkpoint_head=checkpoint_head,
        failure_code=failure_code,
        answer_persisted=answer_persisted,
        remote_push_deferred=remote_push_deferred,
        pending_remote_commit_count=pending_count,
        created_at=created_at,
        updated_at=updated_at,
    )


class HumanAdamCompletionStatusStore:
    """Persist one redacted completion record per canonical workstream."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.RLock()

    def _load_records(self) -> dict[str, HumanAdamCompletionRecord]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise HumanAdamCompletionStatusError(
                "Private stav dokončení nelze bezpečně načíst."
            ) from exc
        if (
            not isinstance(raw, dict)
            or set(raw) != {"schema_version", "records"}
            or raw.get("schema_version") != COMPLETION_STATUS_SCHEMA
            or not isinstance(raw.get("records"), dict)
        ):
            raise HumanAdamCompletionStatusError(
                "Private stav dokončení má neznámé schéma."
            )
        records: dict[str, HumanAdamCompletionRecord] = {}
        for key, value in raw["records"].items():
            record = _validated_record(value)
            if key != record.workstream_id or key in records:
                raise HumanAdamCompletionStatusError(
                    "Private stav dokončení má neplatnou vazbu pracovního proudu."
                )
            records[key] = record
        return records

    def _write_records(
        self,
        records: Mapping[str, HumanAdamCompletionRecord],
    ) -> None:
        payload = {
            "schema_version": COMPLETION_STATUS_SCHEMA,
            "records": {
                key: asdict(records[key])
                for key in sorted(records)
            },
        }
        try:
            atomic_write_json(
                self.path,
                payload,
                ensure_ascii=False,
                indent=2,
            )
            os.chmod(self.path, 0o600)
        except (FilePersistenceError, OSError) as exc:
            raise HumanAdamCompletionStatusError(
                "Private stav dokončení nelze bezpečně uložit."
            ) from exc

    def load(self, *, workstream_id: str) -> HumanAdamCompletionRecord | None:
        clean_id = str(workstream_id or "").strip().casefold()
        if not _WORKSTREAM_ID_RE.fullmatch(clean_id):
            raise HumanAdamCompletionStatusError(
                "Stav dokončení odkazuje na neplatný pracovní proud."
            )
        with self._lock:
            return self._load_records().get(clean_id)

    def begin(
        self,
        *,
        workstream_id: str,
        client_message_id: str,
        base_head: str,
        now_factory: Any = _now,
    ) -> HumanAdamCompletionRecord:
        clean_id = str(workstream_id or "").strip().casefold()
        clean_message_id = str(client_message_id or "").strip()
        clean_head = str(base_head or "").strip().casefold()
        if (
            not _WORKSTREAM_ID_RE.fullmatch(clean_id)
            or not _CLIENT_MESSAGE_ID_RE.fullmatch(clean_message_id)
            or not _HEAD_RE.fullmatch(clean_head)
        ):
            raise HumanAdamCompletionStatusError(
                "Serverový stav dokončení nelze pro tento zapisovací tah zahájit."
            )
        with self._lock:
            records = self._load_records()
            existing = records.get(clean_id)
            if (
                existing is not None
                and existing.client_message_id == clean_message_id
            ):
                if existing.base_head != clean_head:
                    raise HumanAdamCompletionStatusError(
                        "Opakovaný identifikátor tahu neodpovídá původnímu Git základu."
                    )
                return existing
            if (
                existing is not None
                and existing.state
                in {TURN_STARTED, RECEIPT_ACCEPTED, DELIVERY_UNCERTAIN}
            ):
                raise HumanAdamCompletionStatusError(
                    "Předchozí serverový stav dokončení není uzavřený; "
                    "nový zapisovací tah zůstává zablokovaný."
                )
            created_at = _validated_timestamp(now_factory(), label="zahájení")
            record = HumanAdamCompletionRecord(
                state=TURN_STARTED,
                workstream_id=clean_id,
                client_message_id=clean_message_id,
                base_head=clean_head,
                checkpoint_head="",
                failure_code="",
                answer_persisted=None,
                remote_push_deferred=False,
                pending_remote_commit_count=0,
                created_at=created_at,
                updated_at=created_at,
            )
            records[clean_id] = record
            self._write_records(records)
            return record

    def update(
        self,
        *,
        workstream_id: str,
        client_message_id: str,
        state: str,
        checkpoint_head: str = "",
        failure_code: str = "",
        answer_persisted: bool | None = None,
        remote_push_deferred: bool = False,
        pending_remote_commit_count: int = 0,
        now_factory: Any = _now,
    ) -> HumanAdamCompletionRecord:
        clean_id = str(workstream_id or "").strip().casefold()
        clean_message_id = str(client_message_id or "").strip()
        clean_checkpoint = str(checkpoint_head or "").strip().casefold()
        if (
            state not in _RECORD_STATES
            or failure_code not in _FAILURE_CODES
            or (
                answer_persisted is not None
                and not isinstance(answer_persisted, bool)
            )
            or not isinstance(remote_push_deferred, bool)
            or (state == CHECKPOINT_COMPLETED and not _HEAD_RE.fullmatch(clean_checkpoint))
            or (state != CHECKPOINT_COMPLETED and clean_checkpoint)
        ):
            raise HumanAdamCompletionStatusError(
                "Serverový stav dokončení má neplatnou aktualizaci."
            )
        pending_count = _safe_count(pending_remote_commit_count)
        with self._lock:
            records = self._load_records()
            existing = records.get(clean_id)
            if (
                existing is None
                or existing.client_message_id != clean_message_id
            ):
                raise HumanAdamCompletionStatusError(
                    "Serverový stav dokončení neodpovídá aktivnímu tahu."
                )
            record = HumanAdamCompletionRecord(
                state=state,
                workstream_id=existing.workstream_id,
                client_message_id=existing.client_message_id,
                base_head=existing.base_head,
                checkpoint_head=clean_checkpoint,
                failure_code=failure_code,
                answer_persisted=answer_persisted,
                remote_push_deferred=remote_push_deferred,
                pending_remote_commit_count=pending_count,
                created_at=existing.created_at,
                updated_at=_validated_timestamp(
                    now_factory(),
                    label="aktualizace",
                ),
            )
            records[clean_id] = record
            self._write_records(records)
            return record


def public_completion_status(
    *,
    record: HumanAdamCompletionRecord | None,
    observed_at: str,
    source_snapshot: Mapping[str, Any],
    deployment_snapshot: Mapping[str, Any] | None,
    checkpoint_reachable: bool | None,
    server_operation_active: bool = False,
) -> dict[str, Any]:
    """Return one allowlisted status verified against current Git/workspace."""

    clean_observed_at = _validated_timestamp(observed_at, label="pozorování")
    if record is None:
        return {
            "schema_version": COMPLETION_STATUS_SCHEMA,
            "server_authoritative": True,
            "state": NO_COMPLETION,
            "record_state": NO_COMPLETION,
            "workstream_id": "",
            "checkpoint_short": "",
            "current_main_short": "",
            "git_verified": False,
            "workspace_verified": False,
            "answer_persisted": None,
            "remote_push_deferred": False,
            "pending_remote_commit_count": 0,
            "deployment_state": "unknown",
            "failure_code": "",
            "observed_at": clean_observed_at,
            "updated_at": "",
        }

    source_head = str(source_snapshot.get("source_head") or "").strip().casefold()
    current_main_short = source_head[:12] if _HEAD_RE.fullmatch(source_head) else ""
    workspace_verified = bool(
        source_snapshot.get("ok") is True
        and source_snapshot.get("prepared") is True
        and source_snapshot.get("dirty") is False
        and int(source_snapshot.get("source_pending_changes") or 0) == 0
        and source_snapshot.get("workspace_relation") in {"aligned", "source_ahead"}
    )
    git_verified = bool(
        record.state == CHECKPOINT_COMPLETED
        and checkpoint_reachable is True
        and current_main_short
    )
    state = record.state
    if (
        record.state in {TURN_STARTED, RECEIPT_ACCEPTED}
        and not server_operation_active
    ):
        state = ATTENTION_REQUIRED
    if record.state == CHECKPOINT_COMPLETED and not (
        git_verified and workspace_verified
    ):
        state = ATTENTION_REQUIRED

    deployment = deployment_snapshot if isinstance(deployment_snapshot, Mapping) else {}
    deployed_short = str(deployment.get("main_short") or "").strip().casefold()
    checkpoint_short = record.checkpoint_head[:12]
    deployment_state = "unknown"
    if record.state == CHECKPOINT_COMPLETED:
        deployment_state = (
            "verified_current"
            if (
                git_verified
                and deployed_short
                and deployed_short in {checkpoint_short, current_main_short}
            )
            else "pending"
        )
    return {
        "schema_version": COMPLETION_STATUS_SCHEMA,
        "server_authoritative": True,
        "state": state if state in _PUBLIC_STATES else UNVERIFIED,
        "record_state": record.state,
        "workstream_id": record.workstream_id,
        "checkpoint_short": checkpoint_short,
        "current_main_short": current_main_short,
        "git_verified": git_verified,
        "workspace_verified": workspace_verified,
        "answer_persisted": record.answer_persisted,
        "remote_push_deferred": record.remote_push_deferred,
        "pending_remote_commit_count": record.pending_remote_commit_count,
        "deployment_state": deployment_state,
        "failure_code": record.failure_code,
        "observed_at": clean_observed_at,
        "updated_at": record.updated_at,
    }


def completion_status_model_block(status: object) -> str:
    """Serialize the server result into a compact next-turn model contract."""

    value = status if isinstance(status, Mapping) else {}
    state = str(value.get("state") or "").strip()
    if (
        value.get("schema_version") != COMPLETION_STATUS_SCHEMA
        or value.get("server_authoritative") is not True
        or state not in _PUBLIC_STATES
    ):
        value = {}
        state = UNVERIFIED

    def bool_text(raw: object) -> str:
        if raw is True:
            return "true"
        if raw is False:
            return "false"
        return "unknown"

    checkpoint = str(value.get("checkpoint_short") or "").strip().casefold()
    current_main = str(value.get("current_main_short") or "").strip().casefold()
    workstream_id = str(value.get("workstream_id") or "").strip().casefold()
    deployment_state = str(value.get("deployment_state") or "unknown").strip()
    return "\n".join(
        (
            "[LAST_STEP_COMPLETION]",
            f"schema_version={COMPLETION_STATUS_SCHEMA}",
            "server_authoritative=true",
            f"state={state}",
            f"workstream_id={workstream_id if _WORKSTREAM_ID_RE.fullmatch(workstream_id) else 'unknown'}",
            f"checkpoint={checkpoint if re.fullmatch(r'[0-9a-f]{12}', checkpoint) else 'unknown'}",
            f"current_main={current_main if re.fullmatch(r'[0-9a-f]{12}', current_main) else 'unknown'}",
            f"git_verified={bool_text(value.get('git_verified'))}",
            f"workspace_verified={bool_text(value.get('workspace_verified'))}",
            f"answer_persisted={bool_text(value.get('answer_persisted'))}",
            f"deployment_state={deployment_state if deployment_state in {'unknown', 'pending', 'verified_current'} else 'unknown'}",
            f"pending_remote_commit_count={_safe_count(value.get('pending_remote_commit_count'))}",
            "rule=A model receipt only requests completion; this server block is the authority for its actual result.",
            "rule=When state=checkpoint_completed, explicitly acknowledge the verified checkpoint if asked whether the previous development finished.",
            "rule=When state is failed, missing, uncertain or attention_required, do not claim completion.",
            "[/LAST_STEP_COMPLETION]",
        )
    )
