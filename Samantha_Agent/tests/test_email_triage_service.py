from __future__ import annotations

import unittest

from app.email.models import EmailAttachmentMeta, EmailHeader, EmailMessage
from app.email.triage_service import triage_email_messages


class EmailTriageServiceTests(unittest.TestCase):
    def test_nibe_like_email_is_action_deadline_candidate(self) -> None:
        result = triage_email_messages([_nibe_message()])

        item = result.all_items[0]
        self.assertTrue(item.has_action)
        self.assertTrue(item.has_deadline)
        self.assertEqual(item.priority, "high")
        self.assertEqual(item.category, "deadline")
        self.assertEqual(result.case_candidates[0].uid, "fake-nibe")
        self.assertIn("Objednat prohlidku fotovoltaiky", item.reminder_draft.title)
        self.assertEqual(item.reminder_draft.due_date, "2026-07-31")

    def test_plain_newsletter_is_low_priority(self) -> None:
        result = triage_email_messages([_newsletter_message()])

        item = result.all_items[0]
        self.assertTrue(item.is_newsletter)
        self.assertFalse(item.has_deadline)
        self.assertFalse(item.has_action)
        self.assertEqual(item.priority, "low")
        self.assertEqual(item.category, "newsletter")
        self.assertEqual(result.case_candidates, ())
        self.assertEqual(result.newsletter_emails[0].uid, "fake-newsletter")

    def test_invoice_due_email_is_deadline_action_candidate(self) -> None:
        result = triage_email_messages([_invoice_message()])

        item = result.all_items[0]
        self.assertTrue(item.has_deadline)
        self.assertTrue(item.has_action)
        self.assertEqual(item.priority, "high")
        self.assertIn("30.5.2026", item.deadline_texts)
        self.assertEqual(result.deadline_emails[0].uid, "fake-invoice")
        self.assertEqual(result.action_emails[0].uid, "fake-invoice")
        self.assertEqual(result.case_candidates[0].uid, "fake-invoice")


def _nibe_message() -> EmailMessage:
    return EmailMessage(
        header=EmailHeader(
            internal_id="fake-nibe",
            date="Tue, 5 May 2026 14:02:22 +0000",
            sender="NIBE servis <servis@nibe.example>",
            subject="NIBE nabidka prohlidky fotovoltaiky po sezone",
        ),
        body_text=(
            "Nabizime preventivni prohlidku fotovoltaiky. "
            "Objednejte prohlidku idealne do konce cervence 2026 pres portal "
            "https://partner.example/prohlidka. Kontakt servis@nibe.example. "
            "PRIVATE BODY TAIL MUST NOT LEAK."
        ),
        truncated=False,
        attachments=(
            EmailAttachmentMeta(
                filename="cenik.pdf",
                content_type="application/pdf",
                size_bytes=1234,
                part_id="2",
                content_id="",
                disposition="attachment",
            ),
        ),
    )


def _newsletter_message() -> EmailMessage:
    return EmailMessage(
        header=EmailHeader(
            internal_id="fake-newsletter",
            date="Tue, 5 May 2026 15:00:00 +0000",
            sender="Shop <shop@example.com>",
            subject="Newsletter: sleva a marketingova akce",
        ),
        body_text=(
            "Newsletter se slevou. Marketingova akce tohoto tydne. "
            "Odhlasit se muzete zde https://shop.example/unsubscribe."
        ),
        truncated=False,
    )


def _invoice_message() -> EmailMessage:
    return EmailMessage(
        header=EmailHeader(
            internal_id="fake-invoice",
            date="Tue, 5 May 2026 16:00:00 +0000",
            sender="Fakturace <billing@example.com>",
            subject="Faktura se splatnosti",
        ),
        body_text=(
            "Posilame fakturu. Splatnost 30.5.2026. "
            "Prosim zaplatit bankovnim prevodem."
        ),
        truncated=False,
    )


if __name__ == "__main__":
    unittest.main()
