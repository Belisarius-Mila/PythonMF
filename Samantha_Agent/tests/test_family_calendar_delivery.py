from __future__ import annotations

import unittest

from app.family_calendar_delivery import (
    DeliveryState,
    NotificationOffset,
    RecipientDeliveryState,
    begin_delivery,
    complete_delivery,
    mark_interrupted_delivery,
    plan_delivery,
)


EVENT_KEY = "person-example:birthday:2026-12-19"
RECIPIENT_IDS = ("recipient-1", "recipient-2", "recipient-3", "recipient-4")


class FamilyCalendarDeliveryTests(unittest.TestCase):
    def test_d2_plan_begins_with_four_pending_recipients(self) -> None:
        plan = plan_delivery(event_key=EVENT_KEY, offset=NotificationOffset.D2)

        record = begin_delivery(plan, recipient_ids=RECIPIENT_IDS)

        self.assertTrue(plan.eligible)
        self.assertEqual(plan.reason, "scheduled_d2")
        self.assertEqual(plan.operation_id, f"{EVENT_KEY}:D-2")
        self.assertEqual(record.state, DeliveryState.SENDING)
        self.assertEqual(
            [recipient.state for recipient in record.recipients],
            [RecipientDeliveryState.PENDING] * 4,
        )

    def test_d1_is_eligible_when_d2_was_missed(self) -> None:
        plan = plan_delivery(event_key=EVENT_KEY, offset=NotificationOffset.D1)

        self.assertTrue(plan.eligible)
        self.assertEqual(plan.reason, "catch_up_d1_missing_d2")

    def test_d1_is_eligible_only_after_definite_not_sent_d2(self) -> None:
        d2 = _begin(NotificationOffset.D2)
        not_sent = complete_delivery(d2, not_sent_recipient_ids=RECIPIENT_IDS)

        plan = plan_delivery(
            event_key=EVENT_KEY,
            offset=NotificationOffset.D1,
            records=(not_sent,),
        )

        self.assertEqual(not_sent.state, DeliveryState.NOT_SENT)
        self.assertTrue(plan.eligible)
        self.assertEqual(plan.reason, "catch_up_d1_after_not_sent")

    def test_d1_is_blocked_by_any_non_not_sent_d2_state(self) -> None:
        sending = _begin(NotificationOffset.D2)
        records = {
            DeliveryState.SENDING: sending,
            DeliveryState.SMTP_ACCEPTED: complete_delivery(
                sending,
                accepted_recipient_ids=RECIPIENT_IDS,
            ),
            DeliveryState.PARTIAL: complete_delivery(
                sending,
                accepted_recipient_ids=RECIPIENT_IDS[:2],
                not_sent_recipient_ids=RECIPIENT_IDS[2:],
            ),
            DeliveryState.DELIVERY_UNKNOWN: complete_delivery(
                sending,
                unknown_recipient_ids=RECIPIENT_IDS,
            ),
        }

        for state, record in records.items():
            with self.subTest(state=state):
                plan = plan_delivery(
                    event_key=EVENT_KEY,
                    offset=NotificationOffset.D1,
                    records=(record,),
                )

                self.assertFalse(plan.eligible)
                self.assertEqual(plan.reason, "d1_blocked_by_d2")

    def test_repeated_operation_is_an_idempotent_no_op(self) -> None:
        existing = _begin(NotificationOffset.D2)

        replay = plan_delivery(
            event_key=EVENT_KEY,
            offset=NotificationOffset.D2,
            records=(existing,),
        )

        self.assertFalse(replay.eligible)
        self.assertEqual(replay.operation_id, existing.operation_id)
        self.assertEqual(replay.reason, "already_recorded")
        with self.assertRaisesRegex(ValueError, "ineligible"):
            begin_delivery(replay, recipient_ids=RECIPIENT_IDS)

    def test_begin_requires_four_distinct_recipient_ids(self) -> None:
        plan = plan_delivery(event_key=EVENT_KEY, offset=NotificationOffset.D2)

        with self.assertRaisesRegex(ValueError, "exactly four"):
            begin_delivery(plan, recipient_ids=RECIPIENT_IDS[:3])
        with self.assertRaisesRegex(ValueError, "four distinct"):
            begin_delivery(
                plan,
                recipient_ids=("recipient-1", "recipient-2", "recipient-3", "RECIPIENT-3"),
            )

    def test_partial_acceptance_is_tracked_per_recipient(self) -> None:
        result = complete_delivery(
            _begin(NotificationOffset.D2),
            accepted_recipient_ids=RECIPIENT_IDS[:2],
            not_sent_recipient_ids=RECIPIENT_IDS[2:],
        )

        self.assertEqual(result.state, DeliveryState.PARTIAL)
        self.assertEqual(
            {recipient.recipient_id: recipient.state for recipient in result.recipients},
            {
                "recipient-1": RecipientDeliveryState.ACCEPTED,
                "recipient-2": RecipientDeliveryState.ACCEPTED,
                "recipient-3": RecipientDeliveryState.NOT_SENT,
                "recipient-4": RecipientDeliveryState.NOT_SENT,
            },
        )

    def test_unknown_outcome_is_fail_closed_per_recipient(self) -> None:
        result = complete_delivery(
            _begin(NotificationOffset.D2),
            accepted_recipient_ids=("recipient-1",),
            unknown_recipient_ids=RECIPIENT_IDS[1:],
        )

        self.assertEqual(result.state, DeliveryState.DELIVERY_UNKNOWN)
        self.assertEqual(result.recipients[0].state, RecipientDeliveryState.ACCEPTED)
        self.assertTrue(
            all(
                recipient.state is RecipientDeliveryState.UNKNOWN
                for recipient in result.recipients[1:]
            )
        )

    def test_crash_in_sending_becomes_unknown_and_is_not_retried(self) -> None:
        interrupted = mark_interrupted_delivery(_begin(NotificationOffset.D2))

        d2_replay = plan_delivery(
            event_key=EVENT_KEY,
            offset=NotificationOffset.D2,
            records=(interrupted,),
        )
        d1_catch_up = plan_delivery(
            event_key=EVENT_KEY,
            offset=NotificationOffset.D1,
            records=(interrupted,),
        )

        self.assertEqual(interrupted.state, DeliveryState.DELIVERY_UNKNOWN)
        self.assertTrue(
            all(
                recipient.state is RecipientDeliveryState.UNKNOWN
                for recipient in interrupted.recipients
            )
        )
        self.assertFalse(d2_replay.eligible)
        self.assertEqual(d2_replay.reason, "already_recorded")
        self.assertFalse(d1_catch_up.eligible)
        self.assertEqual(d1_catch_up.reason, "d1_blocked_by_d2")

    def test_outcome_must_cover_exactly_the_four_configured_recipients(self) -> None:
        record = _begin(NotificationOffset.D2)

        with self.assertRaisesRegex(ValueError, "exactly the configured recipients"):
            complete_delivery(record, accepted_recipient_ids=RECIPIENT_IDS[:3])
        with self.assertRaisesRegex(ValueError, "more than one delivery outcome"):
            complete_delivery(
                record,
                accepted_recipient_ids=RECIPIENT_IDS,
                not_sent_recipient_ids=("recipient-4",),
            )


def _begin(offset: NotificationOffset):
    return begin_delivery(
        plan_delivery(event_key=EVENT_KEY, offset=offset),
        recipient_ids=RECIPIENT_IDS,
    )


if __name__ == "__main__":
    unittest.main()
