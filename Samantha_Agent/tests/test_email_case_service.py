from __future__ import annotations

import unittest

from app.email.case_service import build_email_case_draft, format_email_case_draft
from app.email.case_tools import build_email_case_from_uid_text
from app.email.icloud_provider import _html_to_text, _normalize_body_text
from app.email.link_tools import show_email_case_links_text
from app.email.models import EmailAttachmentMeta, EmailHeader, EmailMessage
from app.email.safety import has_explicit_link_confirmation, has_explicit_read_confirmation
from app.email.tools import _format_email_headers


class EmailCaseServiceTests(unittest.TestCase):
    def test_build_case_redacts_addresses_and_extracts_core_fields(self) -> None:
        message = EmailMessage(
            header=EmailHeader(
                internal_id="12345",
                date="Tue, 19 May 2026 08:00:00 +0200",
                sender="Sender <sender@example.com>",
                subject="Urgent invoice deadline",
            ),
            body_text=(
                "Please review this invoice by 20.5.2026.\n"
                "Contact sender@example.com for details.\n"
                "Payment link: https://example.com/pay."
            ),
            truncated=False,
            attachments=(
                EmailAttachmentMeta(
                    filename="invoice.pdf",
                    content_type="application/pdf",
                    size_bytes=1234,
                    part_id="2",
                    content_id="",
                    disposition="attachment",
                ),
            ),
        )

        case = build_email_case_draft(message)

        self.assertEqual(case.uid, "12345")
        self.assertEqual(case.email_type, "transactional")
        self.assertEqual(case.priority, "high")
        self.assertIsNotNone(case.deadline)
        self.assertEqual(case.deadline.raw_text, "20.5.2026")
        self.assertEqual(len(case.links), 1)
        self.assertEqual(case.links[0].url, "https://example.com/pay")
        self.assertEqual(len(case.attachments), 1)
        self.assertEqual(case.attachments[0].filename, "invoice.pdf")
        self.assertIn("[e-mail redigovan]", case.summary_redacted)
        self.assertNotIn("sender@example.com", case.summary_redacted)

    def test_format_case_mentions_safety_boundaries(self) -> None:
        message = EmailMessage(
            header=EmailHeader(
                internal_id="7",
                date="Tue, 19 May 2026 09:00:00 +0200",
                sender="No Reply <noreply@example.com>",
                subject="Status update",
            ),
            body_text="Informacni zprava bez akce.",
            truncated=True,
        )

        formatted = format_email_case_draft(build_email_case_draft(message))

        self.assertIn("UID: 7", formatted)
        self.assertIn("Prilohy metadata:\n- Nenalezeny", formatted)
        self.assertIn("odpoved nebyla odeslana", formatted)
        self.assertIn("nic nebylo ulozeno do memory", formatted)
        self.assertIn("telo bylo zkraceno", formatted)

    def test_css_decimal_is_not_deadline(self) -> None:
        message = EmailMessage(
            header=EmailHeader(
                internal_id="55",
                date="Tue, 19 May 2026 11:00:00 +0200",
                sender="Shop <shop@example.com>",
                subject="Newsletter",
            ),
            body_text="background-color: rgba(244, 244, 245, 0.8); Nabidka tydne.",
            truncated=False,
        )

        case = build_email_case_draft(message)

        self.assertIsNone(case.deadline)

    def test_newsletter_summary_omits_urls_and_reply_is_not_suggested(self) -> None:
        message = EmailMessage(
            header=EmailHeader(
                internal_id="99",
                date="Tue, 19 May 2026 12:00:00 +0200",
                sender="Shop <shop@example.com>",
                subject="Newsletter: letni nabidka",
            ),
            body_text=(
                "Zobrazit online verzi https://click.example.com/a "
                "Letni nabidka sportovniho vybaveni. "
                "Muj ucet https://click.example.com/b "
                "Odhlasit https://click.example.com/unsubscribe"
            ),
            truncated=False,
        )

        case = build_email_case_draft(message)

        self.assertEqual(case.email_type, "newsletter")
        self.assertNotIn("https://", case.summary_redacted)
        self.assertIn("Letni nabidka sportovniho vybaveni", case.summary_redacted)
        self.assertIn("odpoved se nenavrhuje", case.reply_draft)
        self.assertEqual(case.links[0].label, "click.example.com")

        formatted = format_email_case_draft(case)
        self.assertIn("- click.example.com: 3 odkazu", formatted)
        self.assertIn("Plne URL nezobrazuji automaticky", formatted)
        self.assertNotIn("https://click.example.com/a", formatted)


class EmailHtmlParsingTests(unittest.TestCase):
    def test_html_parser_ignores_style_and_keeps_links_as_metadata_source(self) -> None:
        html = """
        <html>
          <head><style>.x { color: rgba(1, 2, 3, 0.8); }</style></head>
          <body><a href="https://example.com/path">Open</a> Visible text</body>
        </html>
        """

        text = _html_to_text(html)

        self.assertNotIn("rgba", text)
        self.assertIn("https://example.com/path", text)
        self.assertIn("Visible text", text)

    def test_normalize_body_removes_invisible_filler_characters(self) -> None:
        text = _normalize_body_text("Ahoj\u034f\u200c\ufeff   svete")

        self.assertEqual(text, "Ahoj svete")


class EmailSafetyTests(unittest.TestCase):
    def test_confirmation_requires_uid_and_confirmation_word(self) -> None:
        self.assertTrue(
            has_explicit_read_confirmation(
                uid="12345",
                confirmation_text="Ano, potvrzuji precti UID 12345.",
            )
        )
        self.assertFalse(
            has_explicit_read_confirmation(
                uid="12345",
                confirmation_text="Ano, precti ten email.",
            )
        )
        self.assertFalse(
            has_explicit_read_confirmation(
                uid="12345",
                confirmation_text="UID 12345",
            )
        )

    def test_link_confirmation_requires_uid_confirmation_and_link_request(self) -> None:
        self.assertTrue(
            has_explicit_link_confirmation(
                uid="12345",
                confirmation_text="Ano, potvrzuji zobraz plne URL z UID 12345.",
            )
        )
        self.assertFalse(
            has_explicit_link_confirmation(
                uid="12345",
                confirmation_text="Ano, potvrzuji precti UID 12345.",
            )
        )
        self.assertFalse(
            has_explicit_link_confirmation(
                uid="12345",
                confirmation_text="Ano, zobraz plne URL.",
            )
        )


class EmailHeaderToolTests(unittest.TestCase):
    def test_header_format_redacts_sender_email_address(self) -> None:
        formatted = _format_email_headers(
            [
                EmailHeader(
                    internal_id="12345",
                    date="Tue, 19 May 2026 10:00:00 +0200",
                    sender="Sender <sender@example.com>",
                    subject="Hello",
                )
            ]
        )

        self.assertIn("UID: 12345", formatted)
        self.assertIn("Sender <[e-mail redigovan]>", formatted)
        self.assertNotIn("sender@example.com", formatted)


class EmailCaseToolTests(unittest.TestCase):
    def test_tool_gate_does_not_call_provider_without_confirmation(self) -> None:
        def fail_provider() -> object:
            raise AssertionError("Provider must not be called without confirmation")

        result = build_email_case_from_uid_text(
            uid="12345",
            user_confirmed=False,
            confirmation_text="",
            provider_factory=fail_provider,
        )

        self.assertIn("Nejdrive potrebuji vyslovne potvrzeni", result)
        self.assertIn("UID 12345", result)

    def test_tool_uses_provider_after_confirmation(self) -> None:
        class FakeProvider:
            def read_message_by_uid(self, uid: str, max_chars: int) -> EmailMessage:
                self.uid = uid
                self.max_chars = max_chars
                return EmailMessage(
                    header=EmailHeader(
                        internal_id=uid,
                        date="Tue, 19 May 2026 10:00:00 +0200",
                        sender="Sender <sender@example.com>",
                        subject="Please confirm",
                    ),
                    body_text="Please confirm by tomorrow.",
                    truncated=False,
                )

        result = build_email_case_from_uid_text(
            uid="12345",
            user_confirmed=True,
            confirmation_text="Ano, potvrzuji precti UID 12345.",
            provider_factory=FakeProvider,
        )

        self.assertIn("UID: 12345", result)
        self.assertIn("Akcni kroky:", result)
        self.assertIn("odpoved nebyla odeslana", result)


class EmailLinkToolTests(unittest.TestCase):
    def test_link_tool_gate_does_not_call_provider_without_confirmation(self) -> None:
        def fail_provider() -> object:
            raise AssertionError("Provider must not be called without confirmation")

        result = show_email_case_links_text(
            uid="12345",
            user_confirmed=False,
            confirmation_text="",
            provider_factory=fail_provider,
        )

        self.assertIn("Nejdrive potrebuji vyslovne potvrzeni", result)
        self.assertIn("UID 12345", result)
        self.assertIn("URL", result)

    def test_link_tool_lists_full_urls_after_confirmation(self) -> None:
        class FakeProvider:
            def read_message_by_uid(self, uid: str, max_chars: int) -> EmailMessage:
                return EmailMessage(
                    header=EmailHeader(
                        internal_id=uid,
                        date="Tue, 19 May 2026 10:00:00 +0200",
                        sender="Sender <sender@example.com>",
                        subject="Links",
                    ),
                    body_text=(
                        "Open https://example.com/a and "
                        "https://example.com/b?x=1."
                    ),
                    truncated=False,
                )

        result = show_email_case_links_text(
            uid="12345",
            user_confirmed=True,
            confirmation_text="Ano, potvrzuji zobraz plne URL z UID 12345.",
            provider_factory=FakeProvider,
        )

        self.assertIn("UID: 12345", result)
        self.assertIn("1. https://example.com/a", result)
        self.assertIn("2. https://example.com/b?x=1", result)
        self.assertIn("odkazy nebyly otevreny", result)


if __name__ == "__main__":
    unittest.main()
