from __future__ import annotations

import unittest
from unittest.mock import patch

from app.email.config import ICloudMailConfig
from app.email.icloud_provider import (
    ICloudReadOnlyEmailProvider,
    _message_data_to_archive_source,
)


class ICloudArchiveProviderParserTests(unittest.TestCase):
    def test_message_data_to_archive_source_extracts_archive_fields(self) -> None:
        raw_message = (
            b"From: Canva <security@canva.example>\r\n"
            b"Date: Sat, 16 May 2026 22:17:33 +0000\r\n"
            b"Subject: Canva security change\r\n"
            b"Message-ID: <fake@example>\r\n"
            b"MIME-Version: 1.0\r\n"
            b"Content-Type: multipart/mixed; boundary=\"outer\"\r\n"
            b"\r\n"
            b"--outer\r\n"
            b"Content-Type: multipart/alternative; boundary=\"alt\"\r\n"
            b"\r\n"
            b"--alt\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n"
            b"\r\n"
            b"Plain body https://example.com/plain\r\n"
            b"--alt\r\n"
            b"Content-Type: text/html; charset=utf-8\r\n"
            b"\r\n"
            b"<html><body><a href=\"https://example.com/html\">HTML link</a></body></html>\r\n"
            b"--alt--\r\n"
            b"--outer\r\n"
            b"Content-Type: application/pdf; name=\"security.pdf\"\r\n"
            b"Content-Disposition: attachment; filename=\"security.pdf\"\r\n"
            b"\r\n"
            b"PDFDATA\r\n"
            b"--outer--\r\n"
        )
        message_data = [(b"1 (RFC822.SIZE 999 BODY[] {999}", raw_message)]

        source = _message_data_to_archive_source(
            uid="13964",
            message_data=message_data,
            max_chars=50_000,
        )

        self.assertEqual(source.uid, "13964")
        self.assertEqual(source.sender, "Canva <security@canva.example>")
        self.assertEqual(source.subject, "Canva security change")
        self.assertEqual(source.message_id, "<fake@example>")
        self.assertEqual(source.provider, "icloud")
        self.assertEqual(source.original_eml, raw_message)
        self.assertIn("Plain body", source.body_text)
        self.assertIn("https://example.com/html", source.body_html)
        self.assertEqual(
            source.links,
            ("https://example.com/plain", "https://example.com/html"),
        )
        self.assertEqual(len(source.attachments), 1)
        self.assertEqual(source.attachments[0].filename, "security.pdf")
        self.assertEqual(source.attachments[0].content_type, "application/pdf")

    def test_message_data_to_archive_source_truncates_text_and_html(self) -> None:
        raw_message = (
            b"From: Sender <sender@example.com>\r\n"
            b"Subject: Long\r\n"
            b"MIME-Version: 1.0\r\n"
            b"Content-Type: multipart/alternative; boundary=\"alt\"\r\n"
            b"\r\n"
            b"--alt\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n"
            b"\r\n"
            b"1234567890\r\n"
            b"--alt\r\n"
            b"Content-Type: text/html; charset=utf-8\r\n"
            b"\r\n"
            b"<p>1234567890</p>\r\n"
            b"--alt--\r\n"
        )

        source = _message_data_to_archive_source(
            uid="1",
            message_data=[(b"1 (RFC822.SIZE 500 BODY[] {500}", raw_message)],
            max_chars=5,
        )

        self.assertEqual(source.body_text, "12345")
        self.assertEqual(source.body_html, "<p>12")


class ICloudTrashPurgeTests(unittest.TestCase):
    def test_permanent_delete_quotes_spaced_trash_mailbox(self) -> None:
        imap = _FakeTrashPurgeImap()
        provider = ICloudReadOnlyEmailProvider(
            ICloudMailConfig(
                address="user@example.com",
                app_password="secret",
            )
        )

        with patch("app.email.icloud_provider.imaplib.IMAP4_SSL", return_value=imap):
            provider.permanently_delete_message_from_trash(
                message_id="<message@example.com>",
                trash_folder="Deleted Messages",
            )

        self.assertEqual(imap.select_calls, [('"Deleted Messages"', False)])
        self.assertIn(
            ("SEARCH", None, "HEADER", "MESSAGE-ID", '"<message@example.com>"'),
            imap.uid_calls,
        )
        self.assertIn(("STORE", b"77", "+FLAGS.SILENT", r"(\Deleted)"), imap.uid_calls)
        self.assertEqual(imap.expunge_calls, [("EXPUNGE", b"77")])


class _FakeTrashPurgeImap:
    def __init__(self) -> None:
        self.select_calls: list[tuple[str, bool]] = []
        self.uid_calls: list[tuple[object, ...]] = []
        self.expunge_calls: list[tuple[object, ...]] = []

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def login(self, _address: str, _password: str):
        return "OK", []

    def select(self, folder: str, readonly: bool = False):
        self.select_calls.append((folder, readonly))
        if folder != '"Deleted Messages"':
            raise AssertionError(f"Spaced mailbox was not quoted: {folder}")
        return "OK", [b"1"]

    def uid(self, command: str, *args):
        self.uid_calls.append((command, *args))
        if command == "SEARCH":
            return "OK", [b"77"]
        if command == "STORE":
            return "OK", []
        if command == "EXPUNGE":
            self.expunge_calls.append((command, *args))
            return "OK", []
        raise AssertionError((command, args))


if __name__ == "__main__":
    unittest.main()
