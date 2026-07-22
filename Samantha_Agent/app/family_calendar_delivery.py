"""Pure delivery state machine for family-calendar notifications."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass, replace
from enum import Enum


REQUIRED_RECIPIENT_COUNT = 4


class NotificationOffset(str, Enum):
    D2 = "D-2"
    D1 = "D-1"


class DeliveryState(str, Enum):
    SENDING = "sending"
    SMTP_ACCEPTED = "smtp_accepted"
    NOT_SENT = "not_sent"
    PARTIAL = "partial"
    DELIVERY_UNKNOWN = "delivery_unknown"


class RecipientDeliveryState(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    NOT_SENT = "not_sent"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class RecipientDelivery:
    recipient_id: str
    state: RecipientDeliveryState


@dataclass(frozen=True)
class DeliveryRecord:
    event_key: str
    offset: NotificationOffset
    operation_id: str
    state: DeliveryState
    recipients: tuple[RecipientDelivery, ...]


@dataclass(frozen=True)
class DeliveryPlan:
    event_key: str
    offset: NotificationOffset
    operation_id: str
    eligible: bool
    reason: str


def plan_delivery(
    *,
    event_key: str,
    offset: NotificationOffset | str,
    records: Collection[DeliveryRecord] = (),
) -> DeliveryPlan:
    """Plan D-2 or fail-closed D-1 delivery without changing any state."""

    clean_event_key = _clean_event_key(event_key)
    clean_offset = _coerce_offset(offset)
    operation_id = delivery_operation_id(clean_event_key, clean_offset)
    matching = [record for record in records if record.operation_id == operation_id]
    if matching:
        return DeliveryPlan(
            event_key=clean_event_key,
            offset=clean_offset,
            operation_id=operation_id,
            eligible=False,
            reason="already_recorded",
        )

    if clean_offset is NotificationOffset.D2:
        return DeliveryPlan(
            event_key=clean_event_key,
            offset=clean_offset,
            operation_id=operation_id,
            eligible=True,
            reason="scheduled_d2",
        )

    d2_operation_id = delivery_operation_id(clean_event_key, NotificationOffset.D2)
    d2_records = [record for record in records if record.operation_id == d2_operation_id]
    if not d2_records:
        return DeliveryPlan(
            event_key=clean_event_key,
            offset=clean_offset,
            operation_id=operation_id,
            eligible=True,
            reason="catch_up_d1_missing_d2",
        )
    if len(d2_records) == 1 and d2_records[0].state is DeliveryState.NOT_SENT:
        return DeliveryPlan(
            event_key=clean_event_key,
            offset=clean_offset,
            operation_id=operation_id,
            eligible=True,
            reason="catch_up_d1_after_not_sent",
        )
    return DeliveryPlan(
        event_key=clean_event_key,
        offset=clean_offset,
        operation_id=operation_id,
        eligible=False,
        reason="d1_blocked_by_d2",
    )


def begin_delivery(
    plan: DeliveryPlan,
    *,
    recipient_ids: Sequence[str],
) -> DeliveryRecord:
    """Create the durable-before-network `sending` state for an eligible plan."""

    if not plan.eligible:
        raise ValueError("Delivery cannot begin from an ineligible plan.")
    expected_operation_id = delivery_operation_id(plan.event_key, plan.offset)
    if plan.operation_id != expected_operation_id:
        raise ValueError("Delivery plan has an inconsistent operation id.")
    clean_recipient_ids = _clean_recipient_ids(recipient_ids)
    return DeliveryRecord(
        event_key=plan.event_key,
        offset=plan.offset,
        operation_id=plan.operation_id,
        state=DeliveryState.SENDING,
        recipients=tuple(
            RecipientDelivery(recipient_id, RecipientDeliveryState.PENDING)
            for recipient_id in clean_recipient_ids
        ),
    )


def complete_delivery(
    record: DeliveryRecord,
    *,
    accepted_recipient_ids: Collection[str] = (),
    not_sent_recipient_ids: Collection[str] = (),
    unknown_recipient_ids: Collection[str] = (),
) -> DeliveryRecord:
    """Finish one sending attempt from a complete per-recipient outcome."""

    _require_sending(record)
    expected_ids = tuple(recipient.recipient_id for recipient in record.recipients)
    accepted = _clean_outcome_ids(accepted_recipient_ids, field="accepted")
    not_sent = _clean_outcome_ids(not_sent_recipient_ids, field="not_sent")
    unknown = _clean_outcome_ids(unknown_recipient_ids, field="unknown")
    groups = (accepted, not_sent, unknown)
    if any(
        left.intersection(right)
        for index, left in enumerate(groups)
        for right in groups[index + 1 :]
    ):
        raise ValueError("A recipient cannot have more than one delivery outcome.")
    if accepted.union(not_sent, unknown) != set(expected_ids):
        raise ValueError("Delivery outcome must cover exactly the configured recipients.")

    if unknown:
        state = DeliveryState.DELIVERY_UNKNOWN
    elif accepted and not_sent:
        state = DeliveryState.PARTIAL
    elif accepted:
        state = DeliveryState.SMTP_ACCEPTED
    else:
        state = DeliveryState.NOT_SENT

    recipient_states = []
    for recipient_id in expected_ids:
        if recipient_id in accepted:
            recipient_state = RecipientDeliveryState.ACCEPTED
        elif recipient_id in not_sent:
            recipient_state = RecipientDeliveryState.NOT_SENT
        else:
            recipient_state = RecipientDeliveryState.UNKNOWN
        recipient_states.append(RecipientDelivery(recipient_id, recipient_state))
    return replace(record, state=state, recipients=tuple(recipient_states))


def mark_interrupted_delivery(record: DeliveryRecord) -> DeliveryRecord:
    """Fail closed after a crash: an unfinished network attempt is unknown."""

    _require_sending(record)
    return replace(
        record,
        state=DeliveryState.DELIVERY_UNKNOWN,
        recipients=tuple(
            RecipientDelivery(recipient.recipient_id, RecipientDeliveryState.UNKNOWN)
            for recipient in record.recipients
        ),
    )


def delivery_operation_id(event_key: str, offset: NotificationOffset | str) -> str:
    clean_event_key = _clean_event_key(event_key)
    clean_offset = _coerce_offset(offset)
    return f"{clean_event_key}:{clean_offset.value}"


def _clean_event_key(value: str) -> str:
    clean_value = str(value or "").strip()
    if not clean_value or "\r" in clean_value or "\n" in clean_value:
        raise ValueError("Delivery event key must be a non-empty single line.")
    return clean_value


def _coerce_offset(value: NotificationOffset | str) -> NotificationOffset:
    try:
        return value if isinstance(value, NotificationOffset) else NotificationOffset(str(value))
    except ValueError as exc:
        raise ValueError("Delivery offset must be D-2 or D-1.") from exc


def _clean_recipient_ids(values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or len(values) != REQUIRED_RECIPIENT_COUNT:
        raise ValueError("Delivery requires exactly four recipient ids.")
    cleaned = tuple(str(value or "").strip() for value in values)
    if any(not value or "\r" in value or "\n" in value for value in cleaned):
        raise ValueError("Recipient ids must be non-empty single lines.")
    if len({value.casefold() for value in cleaned}) != REQUIRED_RECIPIENT_COUNT:
        raise ValueError("Delivery requires four distinct recipient ids.")
    return cleaned


def _clean_outcome_ids(values: Collection[str], *, field: str) -> set[str]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"Delivery {field} outcome must be a collection of recipient ids.")
    cleaned = {str(value or "").strip() for value in values}
    if "" in cleaned:
        raise ValueError(f"Delivery {field} outcome contains an empty recipient id.")
    return cleaned


def _require_sending(record: DeliveryRecord) -> None:
    if record.state is not DeliveryState.SENDING:
        raise ValueError("Only a sending delivery can be completed.")
