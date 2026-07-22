"""Pure shared-message envelope for family-calendar delivery."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.family_calendar import FamilyEvent, build_notification_message
from app.family_calendar_delivery import NotificationOffset
from app.family_calendar_delivery_config import (
    CANONICAL_RECIPIENT_IDS,
    EMAIL_ADDRESS_RE,
    DeliveryRecipientConfig,
)


@dataclass(frozen=True, repr=False)
class DeliveryEnvelopeRecipient:
    recipient_id: str
    address: str

    def __repr__(self) -> str:
        return "DeliveryEnvelopeRecipient(redacted=True)"


@dataclass(frozen=True, repr=False)
class FamilyCalendarDeliveryEnvelope:
    event_key: str
    offset: NotificationOffset
    recipients: tuple[DeliveryEnvelopeRecipient, ...]
    subject: str
    body: str

    def __repr__(self) -> str:
        return (
            "FamilyCalendarDeliveryEnvelope("
            f"offset={self.offset.value!r}, recipient_count={len(self.recipients)}, redacted=True)"
        )


def build_family_calendar_delivery_envelope(
    event: FamilyEvent,
    *,
    recipients: Sequence[DeliveryRecipientConfig],
) -> FamilyCalendarDeliveryEnvelope:
    """Build one in-memory message for exactly four canonical recipients."""

    clean_recipients = _validate_recipients(recipients)
    message = build_notification_message(event)
    return FamilyCalendarDeliveryEnvelope(
        event_key=event.event_key,
        offset=NotificationOffset(message["notification_offset"]),
        recipients=clean_recipients,
        subject=message["subject"],
        body=message["body"],
    )


def _validate_recipients(
    recipients: Sequence[DeliveryRecipientConfig],
) -> tuple[DeliveryEnvelopeRecipient, ...]:
    if isinstance(recipients, (str, bytes)) or len(recipients) != len(
        CANONICAL_RECIPIENT_IDS
    ):
        raise ValueError("Delivery envelope requires exactly four recipients.")

    recipients_by_id: dict[str, DeliveryEnvelopeRecipient] = {}
    normalized_addresses: set[str] = set()
    for recipient in recipients:
        if not isinstance(recipient, DeliveryRecipientConfig):
            raise ValueError("Delivery envelope recipient has an invalid shape.")
        recipient_id = recipient.recipient_id
        address = recipient.address
        if recipient_id not in CANONICAL_RECIPIENT_IDS or recipient_id in recipients_by_id:
            raise ValueError("Delivery envelope has invalid recipient identities.")
        if (
            not isinstance(address, str)
            or not address
            or address != address.strip()
            or "\r" in address
            or "\n" in address
            or len(address) > 320
            or EMAIL_ADDRESS_RE.fullmatch(address) is None
        ):
            raise ValueError("Delivery envelope has an invalid recipient address.")
        normalized_address = address.casefold()
        if normalized_address in normalized_addresses:
            raise ValueError("Delivery envelope has duplicate recipient addresses.")
        recipients_by_id[recipient_id] = DeliveryEnvelopeRecipient(recipient_id, address)
        normalized_addresses.add(normalized_address)

    if set(recipients_by_id) != set(CANONICAL_RECIPIENT_IDS):
        raise ValueError("Delivery envelope requires canonical recipient identities.")
    return tuple(recipients_by_id[recipient_id] for recipient_id in CANONICAL_RECIPIENT_IDS)
