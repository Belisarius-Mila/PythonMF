from __future__ import annotations

import unittest

from app.email.action_case_service import (
    build_email_action_case,
    format_email_action_case,
    reminder_draft_to_dict,
)
from app.email.action_case_tools import build_email_action_case_from_uid_text
from app.email.models import EmailAttachmentMeta, EmailHeader, EmailMessage


class EmailActionCaseServiceTests(unittest.TestCase):
    def test_nibe_like_photovoltaic_email_becomes_reminder_draft(self) -> None:
        message = EmailMessage(
            header=EmailHeader(
                internal_id="fake-13849",
                date="Tue, 5 May 2026 14:02:22 +0000",
                sender="NIBE servis <servis@nibe.example>",
                subject="NIBE nabidka prohlidky fotovoltaiky po sezone",
            ),
            body_text=(
                "Nezobrazuje se vam e-mail spravne? Kliknete sem "
                "https://mail.example/newsletter.\n"
                "Vazeny zakazniku, nabizime preventivni prohlidku fotovoltaiky "
                "po topne sezone. Objednejte prohlidku idealne do konce cervence "
                "2026 pres portal https://partner.example/prohlidka.\n"
                "Kontakt: servis@nibe.example.\n"
                "INTERNAL FULL BODY SHOULD NOT LEAK INTO ACTION CASE OUTPUT."
            ),
            truncated=False,
            attachments=(
                EmailAttachmentMeta(
                    filename="cenik-prohlidky.pdf",
                    content_type="application/pdf",
                    size_bytes=3456,
                    part_id="2",
                    content_id="",
                    disposition="attachment",
                ),
            ),
        )

        case = build_email_action_case(message)
        formatted = format_email_action_case(case)
        reminder = reminder_draft_to_dict(case.reminder_draft)

        self.assertEqual(case.uid, "fake-13849")
        self.assertEqual(case.sender, "NIBE servis <[e-mail redigovan]>")
        self.assertEqual(case.recommended_due_date, "2026-07-31")
        self.assertIn("Objednat prohlidku fotovoltaiky.", case.action_items)
        self.assertEqual(case.reminder_draft.title, "Objednat prohlidku fotovoltaiky")
        self.assertEqual(reminder["due_date"], "2026-07-31")
        self.assertEqual(reminder["source"]["sender"], "NIBE servis <[e-mail redigovan]>")
        self.assertEqual(case.attachments[0].filename, "cenik-prohlidky.pdf")
        self.assertEqual(case.link_domains[0].domain, "mail.example")
        self.assertEqual(case.link_domains[1].domain, "partner.example")

        self.assertNotIn("https://mail.example/newsletter", formatted)
        self.assertNotIn("https://partner.example/prohlidka", formatted)
        self.assertNotIn("servis@nibe.example", formatted)
        self.assertNotIn("INTERNAL FULL BODY SHOULD NOT LEAK", formatted)
        self.assertIn("Odkazy metadata:", formatted)
        self.assertIn("Prilohy metadata:", formatted)
        self.assertIn("nic nebylo odeslano", formatted)
        self.assertIn("reminders JSON", formatted)

    def test_plain_email_without_actions_does_not_invent_due_date(self) -> None:
        message = EmailMessage(
            header=EmailHeader(
                internal_id="fake-info",
                date="Tue, 5 May 2026 14:02:22 +0000",
                sender="Info <info@example.com>",
                subject="Informacni zprava",
            ),
            body_text="Pouze informacni zprava bez terminu a bez ukolu.",
            truncated=False,
        )

        case = build_email_action_case(message)

        self.assertEqual(case.recommended_due_date, "")
        self.assertEqual(case.action_items, ())
        self.assertEqual(case.reminder_draft.due_date, "")
        self.assertEqual(case.reminder_draft.priority, "low")


class EmailActionCaseToolTests(unittest.TestCase):
    def test_tool_gate_does_not_call_provider_without_confirmation(self) -> None:
        def fail_provider() -> object:
            raise AssertionError("Provider must not be called without confirmation")

        result = build_email_action_case_from_uid_text(
            uid="fake-uid",
            user_confirmed=False,
            confirmation_text="",
            provider_factory=fail_provider,
        )

        self.assertIn("Nejdrive potrebuji vyslovne potvrzeni", result)
        self.assertIn("UID fake-uid", result)

    def test_tool_reads_one_confirmed_uid_and_returns_safe_action_case(self) -> None:
        class FakeProvider:
            def read_message_by_uid(self, uid: str, max_chars: int) -> EmailMessage:
                self.uid = uid
                self.max_chars = max_chars
                return EmailMessage(
                    header=EmailHeader(
                        internal_id=uid,
                        date="Tue, 5 May 2026 14:02:22 +0000",
                        sender="NIBE servis <servis@nibe.example>",
                        subject="NIBE nabidka prohlidky fotovoltaiky",
                    ),
                    body_text=(
                        "Objednejte prohlidku fotovoltaiky do konce cervence 2026. "
                        "Portal https://partner.example/prohlidka. "
                        "Kontakt servis@nibe.example. "
                        "PRIVATE BODY TAIL MUST NOT LEAK."
                    ),
                    truncated=False,
                )

        result = build_email_action_case_from_uid_text(
            uid="fake-13849",
            user_confirmed=True,
            confirmation_text=(
                "Potvrzuji, ze chci precist telo e-mailu UID fake-13849 "
                "a vytvorit navrh ukolu."
            ),
            provider_factory=FakeProvider,
        )

        self.assertIn("UID: fake-13849", result)
        self.assertIn("Navrh ukolu do reminders JSON:", result)
        self.assertIn("Objednat prohlidku fotovoltaiky", result)
        self.assertIn("Due date: 2026-07-31", result)
        self.assertIn("partner.example: 1 odkaz", result)
        self.assertNotIn("https://partner.example/prohlidka", result)
        self.assertNotIn("servis@nibe.example", result)
        self.assertNotIn("PRIVATE BODY TAIL MUST NOT LEAK", result)
        self.assertIn("nic nebylo odeslano", result)
        self.assertIn("ani ulozeno do memory nebo reminders JSON", result)


if __name__ == "__main__":
    unittest.main()
