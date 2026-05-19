from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from app.email.models import EmailAttachmentMeta, EmailHeader, EmailMessage
from app.email.work_session_models import (
    BUILD_ACTION_CASE,
    BUILD_REMINDER_DRAFT,
    DELETE_EMAIL,
    DOWNLOAD_ATTACHMENTS,
    MARK_READ,
    MOVE_EMAIL,
    OPEN_URLS,
    READ_BODY,
    SAVE_FULL_BODY_TO_MEMORY,
    SEND_EMAIL,
    SHOW_ATTACHMENT_METADATA,
    SHOW_FULL_URLS,
)
from app.email.work_session_service import (
    build_email_work_session_result,
    create_email_work_session,
    format_email_work_session_result,
)


class EmailWorkSessionServiceTests(unittest.TestCase):
    def test_session_is_not_created_without_correct_confirmation(self) -> None:
        with self.assertRaisesRegex(ValueError, "Email Work Session"):
            create_email_work_session(
                uid="fake-13849",
                allowed_actions={READ_BODY},
                confirmation_text="Potvrzuji cteni tela UID fake-13849.",
            )

    def test_confirmation_must_contain_uid(self) -> None:
        with self.assertRaisesRegex(ValueError, "UID"):
            create_email_work_session(
                uid="fake-13849",
                allowed_actions={READ_BODY},
                confirmation_text=(
                    "Potvrzuji Email Work Session. Povolene akce: read_body. "
                    "Zakazuji neotevirat odkazy, nestahovat prilohy a nic neodesilat."
                ),
            )

    def test_confirmation_must_contain_explicit_denials(self) -> None:
        with self.assertRaisesRegex(ValueError, "open_urls"):
            create_email_work_session(
                uid="fake-13849",
                allowed_actions={READ_BODY},
                confirmation_text=(
                    "Potvrzuji Email Work Session pro UID fake-13849. "
                    "Povolene akce: read_body."
                ),
            )

    def test_show_full_urls_allows_full_urls_in_output(self) -> None:
        session = _session({READ_BODY, BUILD_ACTION_CASE, SHOW_FULL_URLS})
        result = build_email_work_session_result(_nibe_message(), session)
        formatted = format_email_work_session_result(result)

        self.assertIn("https://partner.example/prohlidka", result.full_urls)
        self.assertIn("https://partner.example/prohlidka", formatted)
        self.assertIn("https://mail.example/newsletter", formatted)

    def test_without_show_full_urls_only_domains_metadata_are_output(self) -> None:
        session = _session({READ_BODY, BUILD_ACTION_CASE, BUILD_REMINDER_DRAFT})
        result = build_email_work_session_result(_nibe_message(), session)
        formatted = format_email_work_session_result(result)

        self.assertEqual(result.full_urls, ())
        self.assertIn("partner.example: 1 odkaz", formatted)
        self.assertNotIn("https://partner.example/prohlidka", formatted)
        self.assertNotIn("https://mail.example/newsletter", formatted)

    def test_attachments_are_metadata_only(self) -> None:
        session = _session({READ_BODY, SHOW_ATTACHMENT_METADATA})
        result = build_email_work_session_result(_nibe_message(), session)
        formatted = format_email_work_session_result(result)

        self.assertEqual(result.attachment_metadata[0].filename, "cenik-prohlidky.pdf")
        self.assertIn("cenik-prohlidky.pdf | application/pdf | 3456 B | part_id=2", formatted)
        self.assertNotIn("ATTACHMENT_BINARY_CONTENT", formatted)

    def test_formatted_output_does_not_contain_full_email_body(self) -> None:
        message = _nibe_message()
        session = _session({READ_BODY, BUILD_ACTION_CASE, BUILD_REMINDER_DRAFT})
        result = build_email_work_session_result(message, session)
        formatted = format_email_work_session_result(result)

        self.assertNotIn(message.body_text, formatted)
        self.assertNotIn("servis@nibe.example", formatted)
        self.assertNotIn("INTERNAL FULL BODY SHOULD NOT LEAK", formatted)

    def test_service_does_not_write_to_disk(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            before = set(Path(temp_dir).iterdir())
            session = _session({READ_BODY, BUILD_ACTION_CASE})

            build_email_work_session_result(_nibe_message(), session)
            format_email_work_session_result(
                build_email_work_session_result(_nibe_message(), session)
            )

            after = set(Path(temp_dir).iterdir())
            self.assertEqual(before, after)

    def test_nibe_like_email_builds_action_case_and_reminder_draft(self) -> None:
        session = _session(
            {
                READ_BODY,
                BUILD_ACTION_CASE,
                BUILD_REMINDER_DRAFT,
                SHOW_ATTACHMENT_METADATA,
            }
        )

        result = build_email_work_session_result(_nibe_message(), session)
        formatted = format_email_work_session_result(result)

        self.assertEqual(result.uid, "fake-13849")
        self.assertIn("Objednat prohlidku fotovoltaiky", result.action_case_text)
        self.assertEqual(result.reminder_draft.title, "Objednat prohlidku fotovoltaiky")
        self.assertEqual(result.reminder_draft.due_date, "2026-07-31")
        self.assertIn("Safe reminder draft:", formatted)
        self.assertIn("nevolala IMAP/provider", result.safety_note)
        self.assertIn("URL nebyly otevreny", result.safety_note)
        self.assertIn("prilohy nebyly stazeny", result.safety_note)


def _session(allowed_actions: set[str]):
    return create_email_work_session(
        uid="fake-13849",
        allowed_actions=allowed_actions,
        denied_actions={
            OPEN_URLS,
            DOWNLOAD_ATTACHMENTS,
            SEND_EMAIL,
            DELETE_EMAIL,
            MOVE_EMAIL,
            MARK_READ,
            SAVE_FULL_BODY_TO_MEMORY,
        },
        confirmation_text=(
            "Potvrzuji Email Work Session pro UID fake-13849. "
            "Povolene akce: read_body, build_action_case, show_full_urls, "
            "build_reminder_draft, show_attachment_metadata. "
            "Zakazuji neotevirat odkazy, nestahovat prilohy a nic neodesilat."
        ),
        created_at=datetime(2026, 5, 19, 12, 0, 0),
    )


def _nibe_message() -> EmailMessage:
    return EmailMessage(
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
            "INTERNAL FULL BODY SHOULD NOT LEAK."
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


if __name__ == "__main__":
    unittest.main()
