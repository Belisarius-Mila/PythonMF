from __future__ import annotations

import json
import tempfile
import unittest
from email import message_from_bytes
from pathlib import Path

from app.email.archive_models import EmailArchiveSource
from app.email.config import OutgoingMailConfig
from app.email.outbound_tools import (
    prepare_forward_email_by_uid_text,
    send_prepared_email_draft_text,
)
from app.email.outbound import SentCopyResult


class EmailOutboundToolsTests(unittest.TestCase):
    def test_prepare_requires_explicit_confirmation_before_provider_call(self) -> None:
        def failing_provider() -> object:
            raise AssertionError("provider must not be called without confirmation")

        result = prepare_forward_email_by_uid_text(
            provider="icloud",
            uid="123",
            recipient_email="target@example.com",
            user_confirmed=False,
            confirmation_text="",
            provider_factory=failing_provider,
            smtp_config_loader=_smtp_config,
        )

        self.assertIn("potvrzeni", result)
        self.assertIn("Bez toho e-mail nectu", result)

    def test_prepare_creates_local_draft_without_sending(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = prepare_forward_email_by_uid_text(
                provider="icloud",
                uid="123",
                recipient_email="target@example.com",
                note="Prosím o kontrolu.",
                user_confirmed=True,
                confirmation_text="Přepošli UID 123 na target@example.com přes icloud.",
                draft_dir=Path(temp_dir),
                provider_factory=lambda: _Provider(),
                smtp_config_loader=_smtp_config,
            )

            self.assertIn("Draft ID:", result)
            self.assertIn("nebyl odeslan", result)
            draft_id = _draft_id_from_result(result)
            metadata = json.loads((Path(temp_dir) / draft_id / "metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["status"], "draft")
            self.assertEqual(metadata["recipient"], "target@example.com")
            self.assertTrue(metadata["contains_original_eml"])

            raw = (Path(temp_dir) / draft_id / "forward.eml").read_bytes()
            message = message_from_bytes(raw)
            self.assertEqual(message["To"], "target@example.com")
            self.assertEqual(message["Subject"], "Fwd: Faktura Volvo V40")

    def test_send_requires_confirmation_and_then_uses_smtp(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prepare = prepare_forward_email_by_uid_text(
                provider="icloud",
                uid="123",
                recipient_email="target@example.com",
                user_confirmed=True,
                confirmation_text="Přepošli UID 123 na target@example.com přes icloud.",
                draft_dir=Path(temp_dir),
                provider_factory=lambda: _Provider(),
                smtp_config_loader=_smtp_config,
            )
            draft_id = _draft_id_from_result(prepare)

            smtp = _FakeSMTP()
            denied = send_prepared_email_draft_text(
                draft_id=draft_id,
                user_confirmed=False,
                confirmation_text="",
                draft_dir=Path(temp_dir),
                smtp_config_loader=_smtp_config,
                smtp_factory=lambda *args, **kwargs: smtp,
                sent_copy_saver=_sent_copy_saved,
            )
            self.assertIn("Odeslani bylo odmitnuto", denied)
            self.assertEqual(len(smtp.sent_messages), 0)

            sent = send_prepared_email_draft_text(
                draft_id=draft_id,
                user_confirmed=True,
                confirmation_text=f"Potvrzuji, odeslat draft {draft_id} na target@example.com.",
                draft_dir=Path(temp_dir),
                smtp_config_loader=_smtp_config,
                smtp_factory=lambda *args, **kwargs: smtp,
                sent_copy_saver=_sent_copy_saved,
            )

            self.assertIn("Odeslano", sent)
            self.assertIn("Kopie v odeslanych: ulozena (icloud: Sent Messages)", sent)
            self.assertEqual(len(smtp.sent_messages), 1)
            metadata = json.loads((Path(temp_dir) / draft_id / "metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["status"], "sent")
            self.assertEqual(metadata["delivery_status"], "smtp_sent")
            self.assertEqual(metadata["sent_copy_status"], "saved")
            self.assertEqual(metadata["sent_copy_provider"], "icloud")
            self.assertEqual(metadata["sent_copy_folder"], "Sent Messages")


class _Provider:
    def read_archive_source_by_uid(self, uid: str, max_chars: int) -> EmailArchiveSource:
        raw = (
            b"From: Sender <sender@example.com>\r\n"
            b"To: Mila <mila@example.com>\r\n"
            b"Subject: Faktura Volvo V40\r\n"
            b"Date: Tue, 26 May 2026 10:00:00 +0200\r\n"
            b"\r\n"
            b"Servisni faktura."
        )
        return EmailArchiveSource(
            uid=uid,
            date="Tue, 26 May 2026 10:00:00 +0200",
            sender="Sender <sender@example.com>",
            subject="Faktura Volvo V40",
            body_text="Servisni faktura.",
            original_eml=raw,
            provider="icloud",
        )


class _FakeSMTP:
    def __init__(self) -> None:
        self.sent_messages: list[object] = []
        self.logged_in = False

    def __enter__(self) -> "_FakeSMTP":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def starttls(self) -> None:
        return None

    def login(self, address: str, password: str) -> None:
        self.logged_in = (address, password) == ("sender@example.com", "secret")

    def send_message(self, message: object) -> None:
        self.sent_messages.append(message)


def _smtp_config(provider: str) -> OutgoingMailConfig:
    return OutgoingMailConfig(
        address="sender@example.com",
        password="secret",
        host="smtp.example.com",
        port=587,
        security="starttls",
        provider=provider,
    )


def _sent_copy_saved(
    message_bytes: bytes,
    smtp_config: OutgoingMailConfig,
    sent_timestamp: object,
) -> SentCopyResult:
    return SentCopyResult(
        status="saved",
        provider="icloud",
        folder="Sent Messages",
        detail="test saver",
    )


def _draft_id_from_result(result: str) -> str:
    for line in result.splitlines():
        if line.startswith("- Draft ID: "):
            return line.split(": ", 1)[1].strip()
    raise AssertionError(f"draft id not found in result: {result}")


if __name__ == "__main__":
    unittest.main()
