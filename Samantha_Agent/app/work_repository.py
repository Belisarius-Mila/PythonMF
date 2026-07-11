"""Small transactional repository contract for local JSON work stores."""

from __future__ import annotations

import copy
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from app.file_persistence import atomic_replace_text_under_external_lock, exclusive_file_lock


REPOSITORY_META_KEY = "_repository"
REPOSITORY_SCHEMA_VERSION = 1
MAX_IDEMPOTENCY_RECORDS = 256


class WorkRepositoryError(RuntimeError):
    """Raised when a repository document or transaction is invalid."""


@dataclass(frozen=True)
class OutboxEvent:
    topic: str
    aggregate_id: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    event_id: str = ""
    created_at: str = ""

    def as_pending_record(self) -> dict[str, Any]:
        topic = self.topic.strip()
        aggregate_id = self.aggregate_id.strip()
        if not topic or not aggregate_id:
            raise WorkRepositoryError("Outbox event requires topic and aggregate_id.")
        return {
            "event_id": self.event_id.strip() or uuid.uuid4().hex,
            "topic": topic,
            "aggregate_id": aggregate_id,
            "payload": copy.deepcopy(dict(self.payload)),
            "created_at": self.created_at.strip() or _utc_now(),
            "status": "pending",
        }


@dataclass(frozen=True)
class RepositoryMutation:
    document: Mapping[str, Any]
    result: Mapping[str, Any] = field(default_factory=dict)
    changed: bool = True
    outbox: tuple[OutboxEvent, ...] = ()


@dataclass(frozen=True)
class RepositoryResult:
    result: dict[str, Any]
    changed: bool
    idempotent_replay: bool
    outbox_event_ids: tuple[str, ...] = ()


class JsonWorkRepository:
    """Atomically mutate one JSON object, including idempotency and outbox metadata."""

    def __init__(self, path: Path, *, default: Mapping[str, Any] | None = None) -> None:
        self.path = Path(path)
        self.default = copy.deepcopy(dict(default or {}))

    def read(self) -> dict[str, Any]:
        if not self.path.exists():
            return copy.deepcopy(self.default)
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise WorkRepositoryError(f"Cannot read repository JSON: {self.path.name}") from exc
        if not isinstance(payload, dict):
            raise WorkRepositoryError(f"Repository JSON must be an object: {self.path.name}")
        return payload

    def transact(
        self,
        updater: Callable[[dict[str, Any]], RepositoryMutation],
        *,
        operation_id: str = "",
        timeout: float = 10.0,
    ) -> RepositoryResult:
        operation_key = operation_id.strip()
        if len(operation_key) > 200:
            raise WorkRepositoryError("Repository operation_id is too long.")
        with exclusive_file_lock(self.path, timeout=timeout):
            current = self.read()
            metadata = _repository_metadata(current)
            idempotency = metadata["idempotency"]
            if operation_key and operation_key in idempotency:
                stored = idempotency[operation_key]
                if not isinstance(stored, dict):
                    raise WorkRepositoryError("Repository idempotency record is invalid.")
                stored_result = stored.get("result", {})
                event_ids = stored.get("outbox_event_ids", [])
                return RepositoryResult(
                    result=copy.deepcopy(stored_result if isinstance(stored_result, dict) else {}),
                    changed=False,
                    idempotent_replay=True,
                    outbox_event_ids=tuple(str(value) for value in event_ids if str(value).strip()),
                )

            mutation = updater(copy.deepcopy(current))
            if not isinstance(mutation, RepositoryMutation):
                raise WorkRepositoryError("Repository updater must return RepositoryMutation.")
            updated = copy.deepcopy(dict(mutation.document))
            result = copy.deepcopy(dict(mutation.result))
            if not mutation.changed and not mutation.outbox:
                return RepositoryResult(result=result, changed=False, idempotent_replay=False)

            # Repository metadata belongs to this transaction layer, not to the
            # domain updater. Preserve the current ledger even if the updater
            # builds a fresh domain document.
            updated_metadata = copy.deepcopy(metadata)
            outbox_records = updated_metadata["outbox"]
            new_event_ids: list[str] = []
            for event in mutation.outbox:
                record = event.as_pending_record()
                event_id = str(record["event_id"])
                if any(str(existing.get("event_id", "")) == event_id for existing in outbox_records):
                    raise WorkRepositoryError(f"Duplicate outbox event_id: {event_id}")
                outbox_records.append(record)
                new_event_ids.append(event_id)

            if operation_key:
                updated_metadata["idempotency"][operation_key] = {
                    "completed_at": _utc_now(),
                    "result": result,
                    "outbox_event_ids": new_event_ids,
                }
                _trim_idempotency(updated_metadata["idempotency"], outbox_records)
            updated[REPOSITORY_META_KEY] = updated_metadata
            serialized = json.dumps(updated, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            atomic_replace_text_under_external_lock(self.path, serialized)
            return RepositoryResult(
                result=result,
                changed=True,
                idempotent_replay=False,
                outbox_event_ids=tuple(new_event_ids),
            )

    def pending_outbox(self) -> list[dict[str, Any]]:
        metadata = _repository_metadata(self.read())
        return [
            copy.deepcopy(record)
            for record in metadata["outbox"]
            if str(record.get("status", "")) == "pending"
        ]


def _repository_metadata(document: Mapping[str, Any]) -> dict[str, Any]:
    raw = document.get(REPOSITORY_META_KEY, {})
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise WorkRepositoryError("Repository metadata must be an object.")
    schema_version = raw.get("schema_version", REPOSITORY_SCHEMA_VERSION)
    if schema_version != REPOSITORY_SCHEMA_VERSION:
        raise WorkRepositoryError(f"Unsupported repository schema version: {schema_version}")
    idempotency = raw.get("idempotency", {})
    outbox = raw.get("outbox", [])
    if not isinstance(idempotency, dict) or not isinstance(outbox, list):
        raise WorkRepositoryError("Repository metadata collections are invalid.")
    if not all(isinstance(record, dict) for record in outbox):
        raise WorkRepositoryError("Repository outbox records must be objects.")
    return {
        "schema_version": REPOSITORY_SCHEMA_VERSION,
        "idempotency": copy.deepcopy(idempotency),
        "outbox": copy.deepcopy(outbox),
    }


def _trim_idempotency(records: dict[str, Any], outbox: list[dict[str, Any]]) -> None:
    pending_event_ids = {
        str(record.get("event_id", ""))
        for record in outbox
        if str(record.get("status", "")) == "pending"
    }
    removable = []
    for operation_id, record in records.items():
        event_ids = record.get("outbox_event_ids", []) if isinstance(record, dict) else []
        if not pending_event_ids.intersection(str(value) for value in event_ids):
            removable.append(operation_id)
    while len(records) > MAX_IDEMPOTENCY_RECORDS and removable:
        records.pop(removable.pop(0), None)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
