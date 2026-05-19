from __future__ import annotations

import unittest

from app.email.icloud_provider import _message_data_to_archive_source


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


if __name__ == "__main__":
    unittest.main()
