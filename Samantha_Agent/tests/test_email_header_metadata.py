from __future__ import annotations

import unittest

from app.email.icloud_provider import _first_bytes_payload as icloud_first_bytes_payload
from app.email.seznam_provider import _first_bytes_payload as seznam_first_bytes_payload
from app.email.header_metadata import extract_attachment_metadata_from_bodystructure


class EmailHeaderMetadataTests(unittest.TestCase):
    def test_extracts_pdf_attachment_from_bodystructure_without_body_payload(self) -> None:
        message_data = [
            (
                b'1 (RFC822.SIZE 999 BODYSTRUCTURE (("TEXT" "PLAIN" ("CHARSET" "utf-8") NIL NIL "7bit" 20 1)'
                b'("APPLICATION" "PDF" ("NAME" "smlouva.pdf") NIL NIL "base64" 300000 NIL '
                b'("ATTACHMENT" ("FILENAME" "smlouva.pdf")) NIL) "MIXED") '
                b'BODY[HEADER.FIELDS (DATE FROM SUBJECT)] {100}',
                b"From: Sender <sender@example.com>\r\nSubject: Smlouva\r\n",
            )
        ]

        attachments = extract_attachment_metadata_from_bodystructure(message_data)

        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].filename, "smlouva.pdf")
        self.assertEqual(attachments[0].content_type, "application/pdf")
        self.assertEqual(attachments[0].size_bytes, 300000)
        self.assertEqual(attachments[0].disposition, "attachment")

    def test_header_payload_helpers_skip_non_header_literals(self) -> None:
        message_data = [
            (
                b'1 (RFC822.SIZE 999 BODYSTRUCTURE ("TEXT" "PLAIN" NIL NIL NIL "7bit" 52 1) {52}',
                b"Plain text body without header fields.\r\nStill not a header.",
            ),
            (
                b'1 (BODY[HEADER.FIELDS (DATE FROM SUBJECT)] {128}',
                b"Date: Fri, 12 Jun 2026 22:41:06 +0200\r\n"
                b"From: Miloslav Falta <mila@example.invalid>\r\n"
                b"Subject: =?utf-8?Q?=C4=8CEZ_smlouva?=\r\n\r\n",
            ),
        ]

        self.assertIn(b"Subject:", icloud_first_bytes_payload(message_data) or b"")
        self.assertIn(b"Subject:", seznam_first_bytes_payload(message_data) or b"")

    def test_extracts_attachment_from_split_bodystructure_literal(self) -> None:
        filename = b"utf-8''Dohoda_o_u%CC%81prave%CC%8C_smlouvy.pdf"
        message_data = [
            (
                b'6292 (UID 14438 RFC822.SIZE 433187 BODYSTRUCTURE (("application" "pdf" '
                b'("NAME" "=?utf-8?Q?Dohoda_o_u=CC=81prave=CC=8C_smlouvy=2Epdf?=") '
                b'NIL NIL "base64" 428050 NIL ("INLINE" ("FILENAME*" {'
                + str(len(filename)).encode("ascii")
                + b"}",
                filename,
            ),
            (
                b')) NIL NIL)("text" "plain" ("CHARSET" "us-ascii") NIL NIL "7bit" 2 1 '
                b'NIL NIL NIL NIL) "mixed" ("BOUNDARY" "Apple-Mail=_test") NIL NIL NIL) '
                b"BODY[HEADER.FIELDS (DATE FROM SUBJECT)] {64}",
                b"Date: Fri, 12 Jun 2026 22:41:06 +0200\r\nSubject: Test\r\n\r\n",
            ),
        ]

        attachments = extract_attachment_metadata_from_bodystructure(message_data)

        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].filename, "Dohoda_o_úpravě_smlouvy.pdf")
        self.assertEqual(attachments[0].content_type, "application/pdf")
        self.assertEqual(attachments[0].size_bytes, 428050)
        self.assertEqual(attachments[0].disposition, "inline")


if __name__ == "__main__":
    unittest.main()
