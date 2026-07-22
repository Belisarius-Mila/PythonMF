"""Atomic private persistence for family-calendar delivery records."""

from __future__ import annotations

import json
import stat
from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from app.family_calendar_delivery import (
    DeliveryPlan,
    DeliveryRecord,
    DeliveryState,
    NotificationOffset,
    RecipientDelivery,
    RecipientDeliveryState,
    begin_delivery,
    complete_delivery,
    mark_interrupted_delivery,
    plan_delivery,
)
from app.file_persistence import FilePersistenceError, lock_path_for, update_json_file


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH = (
    PROJECT_ROOT / "data" / "private" / "family_calendar" / "delivery_state.json"
)
DELIVERY_STORE_SCHEMA_VERSION = 1


class DeliveryStoreError(RuntimeError):
    """Raised when private delivery state cannot be trusted or persisted."""


@dataclass(frozen=True)
class DeliveryStoreBeginResult:
    plan: DeliveryPlan
    record: DeliveryRecord | None
    started: bool


ResultT = TypeVar("ResultT")
StoreUpdater = Callable[
    [dict[str, DeliveryRecord]],
    tuple[dict[str, DeliveryRecord], ResultT],
]


def load_delivery_records(
    path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
) -> tuple[DeliveryRecord, ...]:
    """Load validated records without creating or repairing a missing store."""

    target = Path(path)
    if not target.exists():
        return ()
    try:
        _assert_private_target(target)
        raw = json.loads(target.read_text(encoding="utf-8"))
        records = _records_from_document(raw)
    except DeliveryStoreError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise DeliveryStoreError("Family-calendar delivery store cannot be trusted.") from exc
    return tuple(records[operation_id] for operation_id in sorted(records))


def begin_stored_delivery(
    *,
    event_key: str,
    offset: NotificationOffset | str,
    recipient_ids: Sequence[str],
    path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
) -> DeliveryStoreBeginResult:
    """Atomically plan and persist `sending` before any future network call."""

    validation_plan = plan_delivery(event_key=event_key, offset=offset)
    begin_delivery(validation_plan, recipient_ids=recipient_ids)

    def update(
        records: dict[str, DeliveryRecord],
    ) -> tuple[dict[str, DeliveryRecord], DeliveryStoreBeginResult]:
        plan = plan_delivery(event_key=event_key, offset=offset, records=records.values())
        if not plan.eligible:
            return records, DeliveryStoreBeginResult(
                plan=plan,
                record=records.get(plan.operation_id),
                started=False,
            )
        record = begin_delivery(plan, recipient_ids=recipient_ids)
        updated = dict(records)
        updated[record.operation_id] = record
        return updated, DeliveryStoreBeginResult(plan=plan, record=record, started=True)

    return _update_store(Path(path), update)


def complete_stored_delivery(
    *,
    operation_id: str,
    accepted_recipient_ids: Collection[str] = (),
    not_sent_recipient_ids: Collection[str] = (),
    unknown_recipient_ids: Collection[str] = (),
    path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
) -> DeliveryRecord:
    """Atomically complete exactly one currently `sending` delivery."""

    safe_operation_id = _clean_operation_id(operation_id)

    def update(
        records: dict[str, DeliveryRecord],
    ) -> tuple[dict[str, DeliveryRecord], DeliveryRecord]:
        record = records.get(safe_operation_id)
        if record is None:
            raise DeliveryStoreError("Delivery operation does not exist in the private store.")
        try:
            completed = complete_delivery(
                record,
                accepted_recipient_ids=accepted_recipient_ids,
                not_sent_recipient_ids=not_sent_recipient_ids,
                unknown_recipient_ids=unknown_recipient_ids,
            )
        except ValueError as exc:
            raise DeliveryStoreError("Stored delivery cannot be completed from its current state.") from exc
        updated = dict(records)
        updated[safe_operation_id] = completed
        return updated, completed

    return _update_store(Path(path), update)


def recover_interrupted_deliveries(
    path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
) -> tuple[DeliveryRecord, ...]:
    """Mark unfinished sends unknown when the caller guarantees no worker is active."""

    target = Path(path)
    if not target.exists():
        return ()

    def update(
        records: dict[str, DeliveryRecord],
    ) -> tuple[dict[str, DeliveryRecord], tuple[DeliveryRecord, ...]]:
        updated = dict(records)
        recovered = []
        for operation_id in sorted(records):
            record = records[operation_id]
            if record.state is not DeliveryState.SENDING:
                continue
            interrupted = mark_interrupted_delivery(record)
            updated[operation_id] = interrupted
            recovered.append(interrupted)
        return updated, tuple(recovered)

    return _update_store(target, update)


def _update_store(path: Path, updater: StoreUpdater[ResultT]) -> ResultT:
    target = Path(path)
    result: ResultT | None = None

    def update_document(raw: Any) -> dict[str, Any]:
        nonlocal result
        records = _records_from_document(raw)
        updated_records, result = updater(records)
        return _store_payload(updated_records)

    try:
        _prepare_private_target(target)
        update_json_file(
            target,
            update_document,
            default={"schema_version": DELIVERY_STORE_SCHEMA_VERSION, "records": {}},
            sort_keys=True,
        )
        _harden_private_target(target)
    except DeliveryStoreError:
        _harden_private_target_best_effort(target)
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, FilePersistenceError, TypeError, ValueError) as exc:
        _harden_private_target_best_effort(target)
        raise DeliveryStoreError("Family-calendar delivery store update failed safely.") from exc
    if result is None:  # pragma: no cover - defensive invariant.
        raise DeliveryStoreError("Family-calendar delivery store returned no transaction result.")
    return result


def _records_from_document(raw: Any) -> dict[str, DeliveryRecord]:
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "records"}:
        raise DeliveryStoreError("Delivery store must contain schema_version and records.")
    if raw.get("schema_version") != DELIVERY_STORE_SCHEMA_VERSION:
        raise DeliveryStoreError("Unsupported family-calendar delivery store schema.")
    raw_records = raw.get("records")
    if not isinstance(raw_records, dict):
        raise DeliveryStoreError("Delivery store records must be an object.")
    records = {}
    for operation_id, payload in raw_records.items():
        if not isinstance(operation_id, str):
            raise DeliveryStoreError("Delivery store operation ids must be strings.")
        record = _record_from_payload(operation_id, payload)
        records[operation_id] = record
    return records


def _record_from_payload(operation_id: str, raw: Any) -> DeliveryRecord:
    expected_fields = {"event_key", "offset", "operation_id", "state", "recipients"}
    if not isinstance(raw, dict) or set(raw) != expected_fields:
        raise DeliveryStoreError("Stored delivery record has an invalid shape.")
    event_key = _required_string(raw.get("event_key"), field="event_key")
    stored_operation_id = _required_string(raw.get("operation_id"), field="operation_id")
    if operation_id != stored_operation_id:
        raise DeliveryStoreError("Stored delivery operation id does not match its record key.")
    try:
        offset = NotificationOffset(_required_string(raw.get("offset"), field="offset"))
        state = DeliveryState(_required_string(raw.get("state"), field="state"))
    except ValueError as exc:
        raise DeliveryStoreError("Stored delivery record contains an unknown state.") from exc

    raw_recipients = raw.get("recipients")
    if not isinstance(raw_recipients, list):
        raise DeliveryStoreError("Stored delivery recipients must be a list.")
    recipients = []
    for raw_recipient in raw_recipients:
        if not isinstance(raw_recipient, dict) or set(raw_recipient) != {"recipient_id", "state"}:
            raise DeliveryStoreError("Stored recipient delivery has an invalid shape.")
        recipient_id = _required_string(raw_recipient.get("recipient_id"), field="recipient_id")
        try:
            recipient_state = RecipientDeliveryState(
                _required_string(raw_recipient.get("state"), field="recipient_state")
            )
        except ValueError as exc:
            raise DeliveryStoreError("Stored recipient delivery has an unknown state.") from exc
        recipients.append(RecipientDelivery(recipient_id, recipient_state))

    plan = DeliveryPlan(
        event_key=event_key,
        offset=offset,
        operation_id=stored_operation_id,
        eligible=True,
        reason="restore_from_private_store",
    )
    try:
        sending = begin_delivery(
            plan,
            recipient_ids=tuple(recipient.recipient_id for recipient in recipients),
        )
        if state is DeliveryState.SENDING:
            restored = sending
        else:
            restored = complete_delivery(
                sending,
                accepted_recipient_ids=tuple(
                    recipient.recipient_id
                    for recipient in recipients
                    if recipient.state is RecipientDeliveryState.ACCEPTED
                ),
                not_sent_recipient_ids=tuple(
                    recipient.recipient_id
                    for recipient in recipients
                    if recipient.state is RecipientDeliveryState.NOT_SENT
                ),
                unknown_recipient_ids=tuple(
                    recipient.recipient_id
                    for recipient in recipients
                    if recipient.state is RecipientDeliveryState.UNKNOWN
                ),
            )
    except ValueError as exc:
        raise DeliveryStoreError("Stored delivery record violates the state machine.") from exc
    if restored.state is not state or restored.recipients != tuple(recipients):
        raise DeliveryStoreError("Stored delivery record has inconsistent recipient states.")
    return restored


def _store_payload(records: dict[str, DeliveryRecord]) -> dict[str, Any]:
    return {
        "schema_version": DELIVERY_STORE_SCHEMA_VERSION,
        "records": {
            operation_id: _record_payload(records[operation_id])
            for operation_id in sorted(records)
        },
    }


def _record_payload(record: DeliveryRecord) -> dict[str, Any]:
    return {
        "event_key": record.event_key,
        "offset": record.offset.value,
        "operation_id": record.operation_id,
        "state": record.state.value,
        "recipients": [
            {"recipient_id": recipient.recipient_id, "state": recipient.state.value}
            for recipient in record.recipients
        ],
    }


def _required_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DeliveryStoreError(f"Stored delivery {field} must be a non-empty trimmed string.")
    if "\r" in value or "\n" in value:
        raise DeliveryStoreError(f"Stored delivery {field} must be a single line.")
    return value


def _clean_operation_id(value: str) -> str:
    safe_value = str(value or "").strip()
    if not safe_value or "\r" in safe_value or "\n" in safe_value:
        raise ValueError("Delivery operation id must be a non-empty single line.")
    return safe_value


def _prepare_private_target(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.parent.chmod(0o700)
    if path.exists():
        path.chmod(0o600)
    lock_path = lock_path_for(path)
    if lock_path.exists():
        lock_path.chmod(0o600)


def _harden_private_target(path: Path) -> None:
    path.parent.chmod(0o700)
    if path.exists():
        path.chmod(0o600)
    lock_path = lock_path_for(path)
    if lock_path.exists():
        lock_path.chmod(0o600)
    _assert_private_target(path)


def _harden_private_target_best_effort(path: Path) -> None:
    try:
        _harden_private_target(path)
    except (OSError, DeliveryStoreError):
        return


def _assert_private_target(path: Path) -> None:
    if stat.S_IMODE(path.parent.stat().st_mode) != 0o700:
        raise DeliveryStoreError("Delivery store directory does not have private permissions.")
    if path.exists() and stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise DeliveryStoreError("Delivery store does not have private permissions.")
    lock_path = lock_path_for(path)
    if lock_path.exists() and stat.S_IMODE(lock_path.stat().st_mode) != 0o600:
        raise DeliveryStoreError("Delivery store lock does not have private permissions.")
