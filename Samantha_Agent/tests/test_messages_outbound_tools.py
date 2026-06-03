from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from app.messages.outbound import (
    MACOS_MESSAGES_EPOCH,
    MessageDeliveryStatus,
    read_latest_outbound_message_status,
    resolve_message_recipient,
    send_via_messages_app,
    send_confirmed_sms_rcs_text,
)


class MessagesOutboundToolsTests(unittest.TestCase):
    def test_requires_explicit_confirmation_before_sender_is_called(self) -> None:
        called = False

        def sender(phone: str, text: str, service: str) -> None:
            nonlocal called
            called = True

        with tempfile.TemporaryDirectory() as temp_dir:
            result = send_confirmed_sms_rcs_text(
                contact_name="Karolina",
                message_text="Test",
                user_confirmed=False,
                confirmation_text="",
                contacts_path=_contacts_path(Path(temp_dir)),
                sender=sender,
            )

        self.assertFalse(called)
        self.assertIn("chybi samostatne potvrzeni", result)

    def test_confirmed_send_reports_delivered_status(self) -> None:
        calls: list[tuple[str, str, str]] = []

        def sender(phone: str, text: str, service: str) -> None:
            calls.append((phone, text, service))

        def verifier(
            phone: str,
            sent_after_ns: int,
            db_path: Path,
            attempts: int,
            interval: float,
        ) -> MessageDeliveryStatus:
            return MessageDeliveryStatus(
                status="delivered",
                service="RCS",
                is_sent=1,
                is_delivered=1,
                error=0,
                date="2026-05-28T14:35:00+02:00",
                handle=phone,
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            result = send_confirmed_sms_rcs_text(
                contact_name="Karolina",
                message_text="Test zprava",
                user_confirmed=True,
                confirmation_text="Potvrzuji, odeslat SMS/RCS kontaktu Karolina: Test zprava",
                contacts_path=_contacts_path(Path(temp_dir)),
                sender=sender,
                verifier=verifier,
            )

        self.assertEqual(calls, [("+420777111222", "Test zprava", "SMS")])
        self.assertIn("delivered", result)
        self.assertIn("is_sent: 1", result)
        self.assertIn("is_delivered: 1", result)
        self.assertIn("error: 0", result)
        self.assertNotIn("+420777111222", result)

    def test_resolves_contact_alias_from_private_contacts_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            recipient = resolve_message_recipient(
                contact_name="karolína",
                contacts_path=_contacts_path(Path(temp_dir)),
            )

        self.assertEqual(recipient.display_name, "Karolina Cossement")
        self.assertEqual(recipient.phone, "+420777111222")

    def test_reads_failed_status_from_messages_database(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "chat.db"
            sent_after_ns = _create_messages_db_with_row(db_path, error=4)

            result = read_latest_outbound_message_status(
                phone="+420777111222",
                sent_after_ns=sent_after_ns,
                db_path=db_path,
            )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error, 4)
        self.assertEqual(result.is_sent, 0)
        self.assertEqual(result.is_delivered, 0)

    def test_messages_app_is_activated_before_applescript_send(self) -> None:
        with patch("app.messages.outbound.subprocess.run") as run:
            send_via_messages_app("+420777111222", "Test zprava", "SMS")

        self.assertEqual(len(run.call_args_list), 2)
        self.assertEqual(
            run.call_args_list[0].args[0],
            ["osascript", "-e", 'tell application "Messages" to activate'],
        )
        self.assertEqual(run.call_args_list[1].args[0][0:2], ["osascript", "-e"])
        self.assertEqual(run.call_args_list[1].args[0][-3:], ["+420777111222", "Test zprava", "SMS"])


def _contacts_path(root: Path) -> Path:
    path = root / "family_contacts.json"
    path.write_text(
        json.dumps(
            {
                "contacts": [
                    {
                        "name": "Karolina Cossement",
                        "aliases": ["Karolina", "Karolína"],
                        "phone": "+420777111222",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return path


def _create_messages_db_with_row(db_path: Path, error: int = 0) -> int:
    sent_at = int(
        (datetime(2026, 5, 28, 12, 35, tzinfo=timezone.utc) - MACOS_MESSAGES_EPOCH)
        .total_seconds()
        * 1_000_000_000
    )
    before = sent_at - 1_000_000_000
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT)")
        conn.execute(
            """
            CREATE TABLE message (
                date INTEGER,
                handle_id INTEGER,
                service TEXT,
                is_from_me INTEGER,
                is_sent INTEGER,
                is_delivered INTEGER,
                error INTEGER
            )
            """
        )
        conn.execute("INSERT INTO handle (ROWID, id) VALUES (1, '+420777111222')")
        conn.execute(
            """
            INSERT INTO message (
                date, handle_id, service, is_from_me, is_sent, is_delivered, error
            ) VALUES (?, 1, 'SMS', 1, 0, 0, ?)
            """,
            (sent_at, error),
        )
    return before


if __name__ == "__main__":
    unittest.main()
