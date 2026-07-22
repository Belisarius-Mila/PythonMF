from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date

from app.family_calendar import FamilyEvent
from app.family_calendar_delivery import NotificationOffset
from app.family_calendar_delivery_config import DeliveryRecipientConfig
from app.family_calendar_delivery_message import build_family_calendar_delivery_envelope


ADDRESSES = (
    "one@example.invalid",
    "two@example.invalid",
    "three@example.invalid",
    "four@example.invalid",
)
RECIPIENT_IDS = ("recipient-1", "recipient-2", "recipient-3", "recipient-4")


class FamilyCalendarDeliveryMessageTests(unittest.TestCase):
    def test_builds_one_d2_birthday_envelope_for_four_canonical_recipients(self) -> None:
        envelope = build_family_calendar_delivery_envelope(
            _event(days_until=2, age=46, catch_up=False),
            recipients=_recipients(reverse=True),
        )

        self.assertEqual(envelope.offset, NotificationOffset.D2)
        self.assertEqual(
            tuple(recipient.recipient_id for recipient in envelope.recipients),
            RECIPIENT_IDS,
        )
        self.assertEqual(
            tuple(recipient.address for recipient in envelope.recipients),
            ADDRESSES,
        )
        self.assertIn("Alena – narozeniny", envelope.subject)
        self.assertIn("Rodinný kalendář – upozornění D-2", envelope.body)
        self.assertNotIn("náhled", envelope.body.casefold())
        self.assertIn("Za 2 dny má Alena (teta) narozeniny.", envelope.body)
        self.assertIn("Věk v den události: 46 let.", envelope.body)

    def test_builds_one_d1_name_day_envelope_without_age(self) -> None:
        event = replace(
            _event(days_until=1, age=None, catch_up=True),
            event_type="name_day",
            event_label="svátek",
        )

        envelope = build_family_calendar_delivery_envelope(event, recipients=_recipients())

        self.assertEqual(envelope.offset, NotificationOffset.D1)
        self.assertIn("Zítra má Alena (teta) svátek.", envelope.body)
        self.assertNotIn("Věk v den události", envelope.body)

    def test_rejects_wrong_count_and_noncanonical_or_duplicate_identities(self) -> None:
        invalid_sets = (
            _recipients()[:3],
            (
                *_recipients()[:3],
                DeliveryRecipientConfig("recipient-5", "five@example.invalid"),
            ),
            (
                *_recipients()[:3],
                DeliveryRecipientConfig("recipient-3", "five@example.invalid"),
            ),
        )

        for recipients in invalid_sets:
            with self.subTest(recipients=recipients):
                with self.assertRaises(ValueError):
                    build_family_calendar_delivery_envelope(
                        _event(),
                        recipients=recipients,
                    )

    def test_rejects_duplicate_addresses_and_header_injection_without_echoing_them(self) -> None:
        duplicate_addresses = list(_recipients())
        duplicate_addresses[3] = DeliveryRecipientConfig(
            "recipient-4",
            "ONE@EXAMPLE.INVALID",
        )
        private_injection = "private@example.invalid\r\nBcc: hidden@example.invalid"
        injected_address = list(_recipients())
        injected_address[0] = DeliveryRecipientConfig("recipient-1", private_injection)

        for recipients in (duplicate_addresses, injected_address):
            with self.subTest(recipients=recipients):
                with self.assertRaises(ValueError) as raised:
                    build_family_calendar_delivery_envelope(
                        _event(),
                        recipients=recipients,
                    )
                self.assertNotIn("@", str(raised.exception))
                self.assertNotIn("private", str(raised.exception))

        private_name = "Private\r\nBcc: hidden@example.invalid"
        with self.assertRaises(ValueError) as raised:
            build_family_calendar_delivery_envelope(
                replace(_event(), display_name=private_name),
                recipients=_recipients(),
            )
        self.assertNotIn("@", str(raised.exception))
        self.assertNotIn("Private", str(raised.exception))

    def test_repr_redacts_addresses_event_and_message_content(self) -> None:
        envelope = build_family_calendar_delivery_envelope(
            _event(),
            recipients=_recipients(),
        )

        visible = f"{envelope!r} {envelope.recipients!r}"
        self.assertIn("recipient_count=4", visible)
        self.assertNotIn("@", visible)
        for private_value in (*ADDRESSES, *RECIPIENT_IDS, "person-example", "Alena", "narozeniny"):
            self.assertNotIn(private_value, visible)


def _event(
    *,
    days_until: int = 2,
    age: int | None = 46,
    catch_up: bool = False,
) -> FamilyEvent:
    return FamilyEvent(
        event_key="person-example:birthday:2026-12-19",
        person_id="person-example",
        display_name="Alena",
        relation="teta",
        event_type="birthday",
        event_label="narozeniny",
        event_date=date(2026, 12, 19),
        days_until=days_until,
        age=age,
        notification_due=True,
        catch_up=catch_up,
    )


def _recipients(*, reverse: bool = False) -> tuple[DeliveryRecipientConfig, ...]:
    recipients = tuple(
        DeliveryRecipientConfig(recipient_id, address)
        for recipient_id, address in zip(RECIPIENT_IDS, ADDRESSES, strict=True)
    )
    return tuple(reversed(recipients)) if reverse else recipients
