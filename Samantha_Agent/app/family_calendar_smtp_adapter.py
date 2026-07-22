"""SMTP outcome adapter with an injected client and no connection management."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol

from app.family_calendar_delivery import (
    DeliveryRecord,
    DeliveryState,
    RecipientDeliveryState,
)
from app.family_calendar_delivery_config import (
    CANONICAL_RECIPIENT_IDS,
    EMAIL_ADDRESS_RE,
)
from app.family_calendar_delivery_coordinator import DeliveryTransportOutcome
from app.family_calendar_delivery_message import (
    DeliveryEnvelopeRecipient,
    FamilyCalendarDeliveryEnvelope,
)


@dataclass(frozen=True, repr=False)
class SMTPClientResult:
    """Known SMTP refusal result returned by an injected client."""

    refused_addresses: tuple[str, ...] = ()

    def __repr__(self) -> str:
        return f"SMTPClientResult(refused_count={len(self.refused_addresses)}, redacted=True)"


class SMTPClient(Protocol):
    def send_message(
        self,
        message: EmailMessage,
        *,
        from_addr: str,
        to_addrs: Sequence[str],
    ) -> SMTPClientResult: ...


@dataclass(frozen=True, repr=False)
class FamilyCalendarSMTPTransport:
    envelope: FamilyCalendarDeliveryEnvelope
    sender_address: str
    client: SMTPClient

    def __call__(self, record: DeliveryRecord) -> DeliveryTransportOutcome:
        return send_family_calendar_envelope_via_smtp(
            record,
            envelope=self.envelope,
            sender_address=self.sender_address,
            client=self.client,
        )

    def __repr__(self) -> str:
        return (
            "FamilyCalendarSMTPTransport("
            f"offset={self.envelope.offset.value!r}, "
            f"recipient_count={len(self.envelope.recipients)}, redacted=True)"
        )


def build_family_calendar_smtp_transport(
    *,
    envelope: FamilyCalendarDeliveryEnvelope,
    sender_address: str,
    client: SMTPClient,
) -> FamilyCalendarSMTPTransport:
    """Build a validated, redacted transport callable for the coordinator."""

    _validate_envelope(envelope)
    clean_sender = _validate_address(sender_address, field="sender")
    if not callable(getattr(client, "send_message", None)):
        raise ValueError("SMTP client must provide send_message.")
    return FamilyCalendarSMTPTransport(
        envelope=envelope,
        sender_address=clean_sender,
        client=client,
    )


def send_family_calendar_envelope_via_smtp(
    record: DeliveryRecord,
    *,
    envelope: FamilyCalendarDeliveryEnvelope,
    sender_address: str,
    client: SMTPClient,
) -> DeliveryTransportOutcome:
    """Send one validated envelope through an injected client and redact its outcome."""

    recipients = _validate_attempt(record, envelope)
    clean_sender = _validate_address(sender_address, field="sender")
    message = _build_message(envelope, sender_address=clean_sender, recipients=recipients)
    recipient_ids = tuple(recipient.recipient_id for recipient in recipients)
    addresses = tuple(recipient.address for recipient in recipients)

    try:
        result = client.send_message(
            message,
            from_addr=clean_sender,
            to_addrs=addresses,
        )
        return _map_client_result(result, recipients=recipients)
    except Exception:  # noqa: BLE001 - SMTP is the untrusted external-effect boundary.
        return DeliveryTransportOutcome(unknown_recipient_ids=recipient_ids)


def _validate_attempt(
    record: DeliveryRecord,
    envelope: FamilyCalendarDeliveryEnvelope,
) -> tuple[DeliveryEnvelopeRecipient, ...]:
    if not isinstance(record, DeliveryRecord) or record.state is not DeliveryState.SENDING:
        raise ValueError("SMTP adapter requires a sending delivery record.")
    recipients = _validate_envelope(envelope)
    if record.event_key != envelope.event_key or record.offset is not envelope.offset:
        raise ValueError("SMTP delivery record does not match its envelope.")

    expected_ids = tuple(CANONICAL_RECIPIENT_IDS)
    record_recipient_ids = tuple(recipient.recipient_id for recipient in record.recipients)
    if record_recipient_ids != expected_ids or any(
        recipient.state is not RecipientDeliveryState.PENDING for recipient in record.recipients
    ):
        raise ValueError("SMTP delivery record has invalid recipient state.")
    return recipients


def _validate_envelope(
    envelope: FamilyCalendarDeliveryEnvelope,
) -> tuple[DeliveryEnvelopeRecipient, ...]:
    if not isinstance(envelope, FamilyCalendarDeliveryEnvelope):
        raise ValueError("SMTP adapter requires a delivery envelope.")
    if len(envelope.recipients) != len(CANONICAL_RECIPIENT_IDS):
        raise ValueError("SMTP adapter requires exactly four envelope recipients.")

    normalized_addresses: set[str] = set()
    envelope_recipient_ids = []
    for recipient in envelope.recipients:
        if not isinstance(recipient, DeliveryEnvelopeRecipient):
            raise ValueError("SMTP envelope recipient has an invalid shape.")
        if recipient.recipient_id not in CANONICAL_RECIPIENT_IDS:
            raise ValueError("SMTP envelope has an invalid recipient identity.")
        _validate_address(recipient.address, field="recipient")
        normalized_address = recipient.address.casefold()
        if normalized_address in normalized_addresses:
            raise ValueError("SMTP envelope has duplicate recipient addresses.")
        normalized_addresses.add(normalized_address)
        envelope_recipient_ids.append(recipient.recipient_id)

    expected_ids = tuple(CANONICAL_RECIPIENT_IDS)
    if tuple(envelope_recipient_ids) != expected_ids:
        raise ValueError("SMTP envelope recipients are not in canonical order.")
    _validate_message_content(envelope)
    return envelope.recipients


def _validate_message_content(envelope: FamilyCalendarDeliveryEnvelope) -> None:
    subject = envelope.subject
    if (
        not isinstance(subject, str)
        or not subject
        or subject != subject.strip()
        or "\r" in subject
        or "\n" in subject
    ):
        raise ValueError("SMTP envelope subject is invalid.")
    if not isinstance(envelope.body, str) or not envelope.body:
        raise ValueError("SMTP envelope body is invalid.")


def _validate_address(value: str, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or "\r" in value
        or "\n" in value
        or len(value) > 320
        or EMAIL_ADDRESS_RE.fullmatch(value) is None
    ):
        raise ValueError(f"SMTP {field} address is invalid.")
    return value


def _build_message(
    envelope: FamilyCalendarDeliveryEnvelope,
    *,
    sender_address: str,
    recipients: Sequence[DeliveryEnvelopeRecipient],
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender_address
    message["To"] = ", ".join(recipient.address for recipient in recipients)
    message["Subject"] = envelope.subject
    message.set_content(envelope.body)
    return message


def _map_client_result(
    result: SMTPClientResult,
    *,
    recipients: Sequence[DeliveryEnvelopeRecipient],
) -> DeliveryTransportOutcome:
    if not isinstance(result, SMTPClientResult):
        raise ValueError("SMTP client returned an invalid result.")
    values = result.refused_addresses
    if isinstance(values, (str, bytes)):
        raise ValueError("SMTP client returned invalid refused recipients.")
    refused_addresses = tuple(values)
    normalized_refused = set()
    known_addresses = {recipient.address.casefold() for recipient in recipients}
    for address in refused_addresses:
        clean_address = _validate_address(address, field="refused recipient")
        normalized = clean_address.casefold()
        if normalized in normalized_refused or normalized not in known_addresses:
            raise ValueError("SMTP client returned invalid refused recipients.")
        normalized_refused.add(normalized)

    accepted_ids = tuple(
        recipient.recipient_id
        for recipient in recipients
        if recipient.address.casefold() not in normalized_refused
    )
    not_sent_ids = tuple(
        recipient.recipient_id
        for recipient in recipients
        if recipient.address.casefold() in normalized_refused
    )
    return DeliveryTransportOutcome(
        accepted_recipient_ids=accepted_ids,
        not_sent_recipient_ids=not_sent_ids,
    )
