"""Small transactional repository contract for local JSON work stores."""

from __future__ import annotations

import copy
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from app.file_persistence import atomic_replace_text_under_external_lock, exclusive_file_lock


REPOSITORY_META_KEY = "_repository"
REPOSITORY_SCHEMA_VERSION = 1
MAX_IDEMPOTENCY_RECORDS = 256
MAX_OUTBOX_LEASE_SECONDS = 3600
MAX_OUTBOX_RETRY_SECONDS = 86400


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


@dataclass(frozen=True)
class OutboxLease:
    event_id: str
    topic: str
    aggregate_id: str
    payload: dict[str, Any]
    lease_owner: str
    lease_token: str
    lease_expires_at: str
    attempts: int


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
            _write_repository_document_under_lock(self.path, updated)
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

    def lease_outbox(
        self,
        *,
        lease_owner: str,
        limit: int = 1,
        lease_seconds: int = 30,
        now: datetime | str | None = None,
        timeout: float = 10.0,
    ) -> list[OutboxLease]:
        owner = lease_owner.strip()
        if not owner or len(owner) > 120:
            raise WorkRepositoryError("Outbox lease_owner is missing or too long.")
        if limit < 1 or limit > 100:
            raise WorkRepositoryError("Outbox lease limit must be between 1 and 100.")
        if lease_seconds < 1 or lease_seconds > MAX_OUTBOX_LEASE_SECONDS:
            raise WorkRepositoryError("Outbox lease_seconds is outside the safe range.")
        now_value = _coerce_datetime(now)
        expires_at = _format_datetime(now_value + timedelta(seconds=lease_seconds))
        leased: list[OutboxLease] = []
        with exclusive_file_lock(self.path, timeout=timeout):
            document = self.read()
            metadata = _repository_metadata(document)
            for record in metadata["outbox"]:
                if len(leased) >= limit:
                    break
                if not _outbox_record_is_available(record, now_value):
                    continue
                attempts = _outbox_attempts(record) + 1
                lease_token = uuid.uuid4().hex
                record.update({
                    "status": "leased",
                    "lease_owner": owner,
                    "lease_token": lease_token,
                    "lease_expires_at": expires_at,
                    "attempts": attempts,
                })
                record.pop("last_retry_lease_token", None)
                leased.append(_lease_from_record(record))
            if leased:
                document[REPOSITORY_META_KEY] = metadata
                _write_repository_document_under_lock(self.path, document)
        return leased

    def acknowledge_outbox(
        self,
        *,
        event_id: str,
        lease_token: str,
        now: datetime | str | None = None,
        timeout: float = 10.0,
    ) -> bool:
        now_value = _coerce_datetime(now)
        with exclusive_file_lock(self.path, timeout=timeout):
            document = self.read()
            metadata = _repository_metadata(document)
            existing = _find_outbox_record(metadata["outbox"], event_id)
            if (
                existing is not None
                and str(existing.get("status", "")) == "delivered"
                and str(existing.get("delivered_lease_token", "")) == lease_token.strip()
            ):
                return True
            record = _leased_outbox_record(
                metadata["outbox"], event_id=event_id, lease_token=lease_token, now=now_value
            )
            if record is None:
                return False
            record["delivered_lease_token"] = lease_token.strip()
            record["status"] = "delivered"
            record["delivered_at"] = _format_datetime(now_value)
            _clear_outbox_lease(record)
            _trim_idempotency(metadata["idempotency"], metadata["outbox"])
            document[REPOSITORY_META_KEY] = metadata
            _write_repository_document_under_lock(self.path, document)
            return True

    def retry_outbox(
        self,
        *,
        event_id: str,
        lease_token: str,
        retry_after_seconds: int,
        error_code: str = "",
        now: datetime | str | None = None,
        timeout: float = 10.0,
    ) -> bool:
        if retry_after_seconds < 0 or retry_after_seconds > MAX_OUTBOX_RETRY_SECONDS:
            raise WorkRepositoryError("Outbox retry delay is outside the safe range.")
        safe_error_code = error_code.strip()
        if safe_error_code and (
            len(safe_error_code) > 100 or re.fullmatch(r"[A-Za-z0-9_.:-]+", safe_error_code) is None
        ):
            raise WorkRepositoryError("Outbox error_code must be a short technical code.")
        now_value = _coerce_datetime(now)
        with exclusive_file_lock(self.path, timeout=timeout):
            document = self.read()
            metadata = _repository_metadata(document)
            existing = _find_outbox_record(metadata["outbox"], event_id)
            if (
                existing is not None
                and str(existing.get("status", "")) == "pending"
                and str(existing.get("last_retry_lease_token", "")) == lease_token.strip()
            ):
                return True
            record = _leased_outbox_record(
                metadata["outbox"], event_id=event_id, lease_token=lease_token, now=now_value
            )
            if record is None:
                return False
            record["status"] = "pending"
            record["available_at"] = _format_datetime(now_value + timedelta(seconds=retry_after_seconds))
            record["last_retry_lease_token"] = lease_token.strip()
            if safe_error_code:
                record["last_error_code"] = safe_error_code
            else:
                record.pop("last_error_code", None)
            _clear_outbox_lease(record)
            document[REPOSITORY_META_KEY] = metadata
            _write_repository_document_under_lock(self.path, document)
            return True


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
        if str(record.get("status", "")) in {"pending", "leased"}
    }
    removable = []
    for operation_id, record in records.items():
        event_ids = record.get("outbox_event_ids", []) if isinstance(record, dict) else []
        if not pending_event_ids.intersection(str(value) for value in event_ids):
            removable.append(operation_id)
    while len(records) > MAX_IDEMPOTENCY_RECORDS and removable:
        records.pop(removable.pop(0), None)


def _outbox_record_is_available(record: Mapping[str, Any], now: datetime) -> bool:
    status = str(record.get("status", ""))
    if status == "pending":
        available_at = str(record.get("available_at", "")).strip()
        return not available_at or _parse_datetime(available_at) <= now
    if status == "leased":
        expires_at = str(record.get("lease_expires_at", "")).strip()
        if not expires_at:
            raise WorkRepositoryError("Leased outbox record has no lease_expires_at.")
        return _parse_datetime(expires_at) <= now
    if status == "delivered":
        return False
    raise WorkRepositoryError(f"Unsupported outbox status: {status}")


def _outbox_attempts(record: Mapping[str, Any]) -> int:
    value = record.get("attempts", 0)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise WorkRepositoryError("Outbox attempts must be a non-negative integer.")
    return value


def _lease_from_record(record: Mapping[str, Any]) -> OutboxLease:
    payload = record.get("payload", {})
    if not isinstance(payload, dict):
        raise WorkRepositoryError("Outbox payload must be an object.")
    return OutboxLease(
        event_id=str(record.get("event_id", "")),
        topic=str(record.get("topic", "")),
        aggregate_id=str(record.get("aggregate_id", "")),
        payload=copy.deepcopy(payload),
        lease_owner=str(record.get("lease_owner", "")),
        lease_token=str(record.get("lease_token", "")),
        lease_expires_at=str(record.get("lease_expires_at", "")),
        attempts=_outbox_attempts(record),
    )


def _leased_outbox_record(
    records: list[dict[str, Any]], *, event_id: str, lease_token: str, now: datetime
) -> dict[str, Any] | None:
    safe_event_id = event_id.strip()
    safe_token = lease_token.strip()
    if not safe_event_id or not safe_token:
        return None
    for record in records:
        if str(record.get("event_id", "")) != safe_event_id:
            continue
        if str(record.get("status", "")) != "leased":
            return None
        if str(record.get("lease_token", "")) != safe_token:
            return None
        expires_at = str(record.get("lease_expires_at", "")).strip()
        if not expires_at or _parse_datetime(expires_at) <= now:
            return None
        return record
    return None


def _find_outbox_record(records: list[dict[str, Any]], event_id: str) -> dict[str, Any] | None:
    safe_event_id = event_id.strip()
    if not safe_event_id:
        return None
    for record in records:
        if str(record.get("event_id", "")) == safe_event_id:
            return record
    return None


def _clear_outbox_lease(record: dict[str, Any]) -> None:
    record.pop("lease_owner", None)
    record.pop("lease_token", None)
    record.pop("lease_expires_at", None)


def _write_repository_document_under_lock(path: Path, document: Mapping[str, Any]) -> None:
    serialized = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    atomic_replace_text_under_external_lock(path, serialized)


def _coerce_datetime(value: datetime | str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, str):
        return _parse_datetime(value)
    if value.tzinfo is None:
        raise WorkRepositoryError("Outbox timestamps must include a timezone.")
    return value.astimezone(timezone.utc)


def _parse_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise WorkRepositoryError("Outbox timestamp is invalid.") from exc
    if parsed.tzinfo is None:
        raise WorkRepositoryError("Outbox timestamps must include a timezone.")
    return parsed.astimezone(timezone.utc)


def _format_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
