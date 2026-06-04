from __future__ import annotations

import unittest

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


if __name__ == "__main__":
    unittest.main()
