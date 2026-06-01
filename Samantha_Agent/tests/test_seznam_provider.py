from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.email.config import (
    EmailConfigError,
    SEZNAM_IMAP_HOST,
    SEZNAM_IMAP_PORT,
    load_seznam_mail_config,
)
from app.email.seznam_provider import (
    SeznamEmailProviderError,
    _message_data_to_email_message,
    _validate_uid,
)


class SeznamConfigTests(unittest.TestCase):
    def test_load_seznam_mail_config_from_env_path(self) -> None:
        env_path = _write_temp_env(
            "SEZNAM_MAIL_ADDRESS=user@example.com\n"
            "SEZNAM_MAIL_PASSWORD=secret-password\n"
        )

        with patch.dict(os.environ, {}, clear=True):
            config = load_seznam_mail_config(env_path=env_path)

        self.assertEqual(config.address, "user@example.com")
        self.assertEqual(config.password, "secret-password")
        self.assertEqual(config.host, SEZNAM_IMAP_HOST)
        self.assertEqual(config.port, SEZNAM_IMAP_PORT)

    def test_load_seznam_mail_config_requires_address_and_password(self) -> None:
        env_path = _write_temp_env("SEZNAM_MAIL_ADDRESS=user@example.com\n")

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(EmailConfigError):
                load_seznam_mail_config(env_path=env_path)


class SeznamProviderParserTests(unittest.TestCase):
    def test_message_data_to_email_message_extracts_text_header_and_attachment(self) -> None:
        raw_message = (
            b"From: Pojistovna <kontakt@example.com>\r\n"
            b"Date: Fri, 22 May 2026 08:30:00 +0200\r\n"
            b"Subject: =?utf-8?q?Pojisteni_auta?=\r\n"
            b"MIME-Version: 1.0\r\n"
            b"Content-Type: multipart/mixed; boundary=\"outer\"\r\n"
            b"\r\n"
            b"--outer\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n"
            b"\r\n"
            b"Dobr\xc3\xbd den,\r\n"
            b"posilame potvrzeni.\r\n"
            b"--outer\r\n"
            b"Content-Type: application/pdf; name=\"potvrzeni.pdf\"\r\n"
            b"Content-Disposition: attachment; filename=\"potvrzeni.pdf\"\r\n"
            b"\r\n"
            b"PDFDATA\r\n"
            b"--outer--\r\n"
        )

        message = _message_data_to_email_message(
            uid="123",
            message_data=[(b"1 (RFC822.SIZE 1000 BODY[] {1000}", raw_message)],
            max_chars=1_000,
        )

        self.assertEqual(message.header.internal_id, "123")
        self.assertEqual(message.header.sender, "Pojistovna <kontakt@example.com>")
        self.assertEqual(message.header.subject, "Pojisteni auta")
        self.assertIn("Dobr", message.body_text)
        self.assertIn("posilame potvrzeni.", message.body_text)
        self.assertFalse(message.truncated)
        self.assertEqual(len(message.attachments), 1)
        self.assertEqual(message.attachments[0].filename, "potvrzeni.pdf")
        self.assertEqual(message.attachments[0].content_type, "application/pdf")
        self.assertEqual(message.attachments[0].disposition, "attachment")

    def test_message_data_to_email_message_uses_html_fallback_and_truncates(self) -> None:
        raw_message = (
            b"From: Sender <sender@example.com>\r\n"
            b"Subject: HTML only\r\n"
            b"MIME-Version: 1.0\r\n"
            b"Content-Type: text/html; charset=utf-8\r\n"
            b"\r\n"
            b"<html><body><p>1234567890</p></body></html>\r\n"
        )

        message = _message_data_to_email_message(
            uid="456",
            message_data=[(b"1 (RFC822.SIZE 500 BODY[] {500}", raw_message)],
            max_chars=5,
        )

        self.assertEqual(message.body_text, "12345")
        self.assertTrue(message.truncated)

    def test_message_data_to_email_message_rejects_too_large_message(self) -> None:
        raw_message = b"From: Sender <sender@example.com>\r\nSubject: Big\r\n\r\nBody"

        with self.assertRaises(SeznamEmailProviderError):
            _message_data_to_email_message(
                uid="789",
                message_data=[
                    (b"1 (RFC822.SIZE 2000001 BODY[] {2000001}", raw_message)
                ],
                max_chars=1_000,
            )

    def test_message_data_to_email_message_allows_larger_explicit_limit(self) -> None:
        raw_message = b"From: Sender <sender@example.com>\r\nSubject: Big selected\r\n\r\nBody"

        message = _message_data_to_email_message(
            uid="789",
            message_data=[
                (b"1 (RFC822.SIZE 2000001 BODY[] {2000001}", raw_message)
            ],
            max_chars=1_000,
            max_message_bytes=25_000_000,
        )

        self.assertEqual(message.header.subject, "Big selected")
        self.assertEqual(message.body_text, "Body")

    def test_validate_uid_requires_digits(self) -> None:
        self.assertEqual(_validate_uid(" 123 "), "123")
        with self.assertRaises(SeznamEmailProviderError):
            _validate_uid("123:456")


def _write_temp_env(content: str) -> Path:
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False)
    with handle:
        handle.write(content)
    return Path(handle.name)


if __name__ == "__main__":
    unittest.main()
