from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date
from email.message import EmailMessage
from unittest.mock import patch

from app.family_calendar import FamilyEvent
from app.family_calendar_delivery import begin_delivery, plan_delivery
from app.family_calendar_delivery_config import DeliveryRecipientConfig
from app.family_calendar_delivery_message import build_family_calendar_delivery_envelope
from app.family_calendar_smtp_adapter import (
    SMTPClientResult,
    send_family_calendar_envelope_via_smtp,
)


ADDRESSES = (
    "one@example.invalid",
    "two@example.invalid",
    "three@example.invalid",
    "four@example.invalid",
)
RECIPIENT_IDS = ("recipient-1", "recipient-2", "recipient-3", "recipient-4")
SENDER_ADDRESS = "sender@example.invalid"


class FakeSMTPClient:
    def __init__(self, result: SMTPClientResult | None = None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.calls = 0
        self.message: EmailMessage | None = None
        self.from_addr = ""
        self.to_addrs: tuple[str, ...] = ()

    def send_message(self, message, *, from_addr, to_addrs):
        self.calls += 1
        self.message = message
        self.from_addr = from_addr
        self.to_addrs = tuple(to_addrs)
        if self.error is not None:
            raise self.error
        return self.result


class FamilyCalendarSMTPAdapterTests(unittest.TestCase):
    def test_all_recipients_accepted_in_one_shared_message(self) -> None:
        record, envelope = _attempt()
        client = FakeSMTPClient(SMTPClientResult())

        outcome = send_family_calendar_envelope_via_smtp(
            record,
            envelope=envelope,
            sender_address=SENDER_ADDRESS,
            client=client,
        )

        self.assertEqual(outcome.accepted_recipient_ids, RECIPIENT_IDS)
        self.assertEqual(outcome.not_sent_recipient_ids, ())
        self.assertEqual(outcome.unknown_recipient_ids, ())
        self.assertEqual(client.calls, 1)
        self.assertEqual(client.from_addr, SENDER_ADDRESS)
        self.assertEqual(client.to_addrs, ADDRESSES)
        self.assertIsNotNone(client.message)
        self.assertEqual(client.message["From"], SENDER_ADDRESS)
        self.assertEqual(client.message["To"], ", ".join(ADDRESSES))
        self.assertEqual(client.message["Subject"], envelope.subject)
        self.assertEqual(client.message.get_content().rstrip("\n"), envelope.body)

    def test_all_recipients_refused_are_known_not_sent(self) -> None:
        record, envelope = _attempt()
        client = FakeSMTPClient(SMTPClientResult(refused_addresses=ADDRESSES))

        outcome = send_family_calendar_envelope_via_smtp(
            record,
            envelope=envelope,
            sender_address=SENDER_ADDRESS,
            client=client,
        )

        self.assertEqual(outcome.accepted_recipient_ids, ())
        self.assertEqual(outcome.not_sent_recipient_ids, RECIPIENT_IDS)
        self.assertEqual(outcome.unknown_recipient_ids, ())

    def test_partial_refusal_maps_addresses_to_technical_ids_in_memory(self) -> None:
        record, envelope = _attempt()
        client = FakeSMTPClient(
            SMTPClientResult(refused_addresses=(ADDRESSES[1].upper(), ADDRESSES[3]))
        )

        outcome = send_family_calendar_envelope_via_smtp(
            record,
            envelope=envelope,
            sender_address=SENDER_ADDRESS,
            client=client,
        )

        self.assertEqual(outcome.accepted_recipient_ids, ("recipient-1", "recipient-3"))
        self.assertEqual(outcome.not_sent_recipient_ids, ("recipient-2", "recipient-4"))
        self.assertEqual(outcome.unknown_recipient_ids, ())
        visible = f"{outcome!r} {client.result!r}"
        self.assertNotIn("@", visible)
        for address in ADDRESSES:
            self.assertNotIn(address, visible)

    def test_client_exception_is_unknown_for_all_without_logging_private_error(self) -> None:
        record, envelope = _attempt()
        private_error = RuntimeError("timeout for private@example.invalid")
        client = FakeSMTPClient(error=private_error)

        with patch("logging.Logger._log") as log_call:
            outcome = send_family_calendar_envelope_via_smtp(
                record,
                envelope=envelope,
                sender_address=SENDER_ADDRESS,
                client=client,
            )

        self.assertEqual(outcome.accepted_recipient_ids, ())
        self.assertEqual(outcome.not_sent_recipient_ids, ())
        self.assertEqual(outcome.unknown_recipient_ids, RECIPIENT_IDS)
        self.assertEqual(client.calls, 1)
        log_call.assert_not_called()
        self.assertNotIn("@", repr(outcome))

    def test_invalid_client_result_fails_closed_as_unknown(self) -> None:
        record, envelope = _attempt()
        invalid_results = (
            None,
            SMTPClientResult(refused_addresses=("unknown@example.invalid",)),
            SMTPClientResult(refused_addresses=(ADDRESSES[0], ADDRESSES[0].upper())),
        )

        for invalid_result in invalid_results:
            with self.subTest(result=invalid_result):
                client = FakeSMTPClient(invalid_result)
                outcome = send_family_calendar_envelope_via_smtp(
                    record,
                    envelope=envelope,
                    sender_address=SENDER_ADDRESS,
                    client=client,
                )
                self.assertEqual(outcome.unknown_recipient_ids, RECIPIENT_IDS)
                self.assertEqual(outcome.accepted_recipient_ids, ())
                self.assertEqual(outcome.not_sent_recipient_ids, ())

    def test_invalid_sender_or_mismatched_record_never_calls_client(self) -> None:
        record, envelope = _attempt()
        client = FakeSMTPClient(SMTPClientResult())
        private_sender = "private@example.invalid\r\nBcc: hidden@example.invalid"

        with self.assertRaises(ValueError) as raised:
            send_family_calendar_envelope_via_smtp(
                record,
                envelope=envelope,
                sender_address=private_sender,
                client=client,
            )
        self.assertNotIn("@", str(raised.exception))
        self.assertEqual(client.calls, 0)

        mismatched = replace(record, event_key="person-other:birthday:2026-12-19")
        with self.assertRaisesRegex(ValueError, "does not match"):
            send_family_calendar_envelope_via_smtp(
                mismatched,
                envelope=envelope,
                sender_address=SENDER_ADDRESS,
                client=client,
            )
        self.assertEqual(client.calls, 0)


def _attempt():
    event = FamilyEvent(
        event_key="person-example:birthday:2026-12-19",
        person_id="person-example",
        display_name="Alena",
        relation="teta",
        event_type="birthday",
        event_label="narozeniny",
        event_date=date(2026, 12, 19),
        days_until=2,
        age=46,
        notification_due=True,
        catch_up=False,
    )
    envelope = build_family_calendar_delivery_envelope(
        event,
        recipients=tuple(
            DeliveryRecipientConfig(recipient_id, address)
            for recipient_id, address in zip(RECIPIENT_IDS, ADDRESSES, strict=True)
        ),
    )
    plan = plan_delivery(event_key=event.event_key, offset="D-2")
    record = begin_delivery(plan, recipient_ids=RECIPIENT_IDS)
    return record, envelope


if __name__ == "__main__":
    unittest.main()
