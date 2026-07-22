from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from app.family_calendar import FamilyEvent
from app.family_calendar_delivery import DeliveryState
from app.family_calendar_delivery_config import DeliveryRecipientConfig
from app.family_calendar_delivery_coordinator import coordinate_delivery_attempt
from app.family_calendar_delivery_message import build_family_calendar_delivery_envelope
from app.family_calendar_delivery_store import load_delivery_records
from app.family_calendar_smtp_adapter import (
    SMTPClientResult,
    build_family_calendar_smtp_transport,
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
    def __init__(
        self,
        *,
        result: SMTPClientResult | None = None,
        error: Exception | None = None,
        state_path: Path | None = None,
    ):
        self.result = result
        self.error = error
        self.state_path = state_path
        self.calls = 0
        self.observed_states: list[DeliveryState] = []

    def send_message(self, _message, *, from_addr, to_addrs):
        self.calls += 1
        if self.state_path is not None:
            records = load_delivery_records(self.state_path)
            self.observed_states.append(records[0].state)
        if self.error is not None:
            raise self.error
        return self.result


class FamilyCalendarDeliveryIntegrationTests(unittest.TestCase):
    def test_coordinator_persists_all_known_smtp_outcomes(self) -> None:
        cases = (
            (SMTPClientResult(), "smtp_accepted", DeliveryState.SMTP_ACCEPTED),
            (
                SMTPClientResult(refused_addresses=ADDRESSES),
                "not_sent",
                DeliveryState.NOT_SENT,
            ),
            (
                SMTPClientResult(refused_addresses=(ADDRESSES[1], ADDRESSES[3])),
                "partial",
                DeliveryState.PARTIAL,
            ),
        )

        for client_result, expected_status, expected_state in cases:
            with self.subTest(expected_status=expected_status):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    state_path, worker_path = _paths(Path(temp_dir))
                    client = FakeSMTPClient(result=client_result, state_path=state_path)
                    transport = _transport(client)

                    result = _coordinate(transport, state_path, worker_path)
                    stored = load_delivery_records(state_path)

                self.assertEqual(result.status, expected_status)
                self.assertTrue(result.transport_called)
                self.assertEqual(client.calls, 1)
                self.assertEqual(client.observed_states, [DeliveryState.SENDING])
                self.assertEqual(stored, (result.record,))
                self.assertEqual(stored[0].state, expected_state)

    def test_client_exception_persists_unknown_without_exposing_private_error(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            state_path, worker_path = _paths(Path(temp_dir))
            client = FakeSMTPClient(
                error=RuntimeError("timeout for private@example.invalid"),
                state_path=state_path,
            )
            transport = _transport(client)

            result = _coordinate(transport, state_path, worker_path)
            stored = load_delivery_records(state_path)

        self.assertEqual(result.status, "delivery_unknown")
        self.assertTrue(result.transport_called)
        self.assertEqual(client.calls, 1)
        self.assertEqual(client.observed_states, [DeliveryState.SENDING])
        self.assertEqual(stored[0].state, DeliveryState.DELIVERY_UNKNOWN)
        self.assertNotIn("@", repr(result))
        self.assertNotIn("private", repr(result).casefold())

    def test_terminal_result_is_idempotent_and_does_not_call_client_twice(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            state_path, worker_path = _paths(Path(temp_dir))
            client = FakeSMTPClient(result=SMTPClientResult())
            transport = _transport(client)

            first = _coordinate(transport, state_path, worker_path)
            second = _coordinate(transport, state_path, worker_path)
            stored = load_delivery_records(state_path)

        self.assertEqual(first.status, "smtp_accepted")
        self.assertEqual(second.status, "skipped")
        self.assertFalse(second.transport_called)
        self.assertEqual(second.plan.reason, "already_recorded")
        self.assertEqual(client.calls, 1)
        self.assertEqual(len(stored), 1)

    def test_transport_factory_is_redacted_and_rejects_static_errors_early(self) -> None:
        envelope = _envelope()
        client = FakeSMTPClient(result=SMTPClientResult())

        transport = build_family_calendar_smtp_transport(
            envelope=envelope,
            sender_address=SENDER_ADDRESS,
            client=client,
        )

        visible = repr(transport)
        self.assertIn("recipient_count=4", visible)
        self.assertNotIn("@", visible)
        for private_value in (*ADDRESSES, SENDER_ADDRESS, envelope.event_key, envelope.subject):
            self.assertNotIn(private_value, visible)

        private_sender = "private@example.invalid\r\nBcc: hidden@example.invalid"
        with self.assertRaises(ValueError) as raised:
            build_family_calendar_smtp_transport(
                envelope=envelope,
                sender_address=private_sender,
                client=client,
            )
        self.assertNotIn("@", str(raised.exception))
        self.assertEqual(client.calls, 0)

        with self.assertRaisesRegex(ValueError, "send_message"):
            build_family_calendar_smtp_transport(
                envelope=envelope,
                sender_address=SENDER_ADDRESS,
                client=object(),
            )


def _coordinate(transport, state_path: Path, worker_path: Path):
    envelope = transport.envelope
    return coordinate_delivery_attempt(
        event_key=envelope.event_key,
        offset=envelope.offset,
        recipient_ids=RECIPIENT_IDS,
        transport=transport,
        state_path=state_path,
        worker_path=worker_path,
    )


def _transport(client: FakeSMTPClient):
    return build_family_calendar_smtp_transport(
        envelope=_envelope(),
        sender_address=SENDER_ADDRESS,
        client=client,
    )


def _envelope():
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
    return build_family_calendar_delivery_envelope(
        event,
        recipients=tuple(
            DeliveryRecipientConfig(recipient_id, address)
            for recipient_id, address in zip(RECIPIENT_IDS, ADDRESSES, strict=True)
        ),
    )


def _paths(root: Path) -> tuple[Path, Path]:
    private_dir = root / "family"
    return private_dir / "delivery_state.json", private_dir / "delivery_worker"


if __name__ == "__main__":
    unittest.main()
