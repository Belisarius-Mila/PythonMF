from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.email.archive_models import EmailArchiveSource
from app.email.archive_query_tools import (
    has_explicit_archive_link_confirmation,
    list_email_archives_text,
    show_email_archive_links_text,
    show_email_archive_summary_text,
)
from app.email.archive_service import save_email_archive
from app.email.models import EmailAttachmentMeta


class EmailArchiveQueryToolsTests(unittest.TestCase):
    def test_list_email_archives_returns_safe_list(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            result = save_email_archive(_archive_source(), directory=directory)

            output = list_email_archives_text(directory=directory)

            self.assertIn(result.archive_id, output)
            self.assertIn("13964", output)
            self.assertIn("Canva security change", output)
            self.assertIn("[e-mail redigovan]", output)
            _assert_safe_archive_output(self, output)

    def test_show_email_archive_summary_returns_safe_detail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            result = save_email_archive(_archive_source(), directory=directory)

            output = show_email_archive_summary_text(result.archive_id, directory=directory)

            self.assertIn("Archive ID:", output)
            self.assertIn("metadata.json", output)
            self.assertIn("body.txt", output)
            self.assertIn("links.json", output)
            self.assertIn("www.canva.com: 2", output)
            self.assertIn("security.pdf | application/pdf | 1234 B | saved=ne", output)
            self.assertIn("Plne URL zobrazi jen samostatne potvrzeny", output)
            _assert_safe_archive_output(self, output)

    def test_show_email_archive_links_without_confirmation_does_not_show_links(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            result = save_email_archive(_archive_source(), directory=directory)

            output = show_email_archive_links_text(result.archive_id, directory=directory)

            self.assertIn("potrebuji samostatne potvrzeni", output)
            _assert_safe_archive_output(self, output)

    def test_show_email_archive_links_requires_uid_or_archive_id_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            result = save_email_archive(_archive_source(), directory=directory)

            self.assertFalse(
                has_explicit_archive_link_confirmation(
                    archive_id=result.archive_id,
                    uid="13964",
                    confirmation_text="Potvrzuji, ze chci zobrazit plne odkazy z archivu Canva.",
                )
            )
            self.assertTrue(
                has_explicit_archive_link_confirmation(
                    archive_id=result.archive_id,
                    uid="13964",
                    confirmation_text="Potvrzuji, ze chci zobrazit plne odkazy z archivu UID 13964.",
                )
            )
            self.assertTrue(
                has_explicit_archive_link_confirmation(
                    archive_id=result.archive_id,
                    uid="13964",
                    confirmation_text=f"Souhlasim se zobrazenim URL z archivu {result.archive_id}.",
                )
            )

    def test_show_email_archive_links_after_confirmation_outputs_full_urls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            result = save_email_archive(_archive_source(), directory=directory)

            output = show_email_archive_links_text(
                "13964",
                user_confirmed=True,
                confirmation_text=(
                    "Potvrzuji, ze chci zobrazit plne odkazy z archivu UID 13964."
                ),
                directory=directory,
            )

            self.assertIn("https://www.canva.com/settings/login-and-security", output)
            self.assertIn("https://www.canva.com/policies/privacy-policy/", output)
            self.assertIn("nebyly otevreny", output)
            self.assertNotIn("Passkey authentication was added", output)
            self.assertNotIn("security@canva.example", output)

    def test_archive_resolution_by_unique_subject_fragment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            save_email_archive(_archive_source(), directory=directory)

            output = show_email_archive_summary_text("Canva", directory=directory)

            self.assertIn("Canva security change", output)
            _assert_safe_archive_output(self, output)

    def test_ambiguous_archive_resolution_requests_specific_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            save_email_archive(
                _archive_source(uid="13964", subject="Canva security change"),
                directory=directory,
            )
            save_email_archive(
                _archive_source(uid="13965", subject="Canva login alert"),
                directory=directory,
            )

            output = show_email_archive_summary_text("Canva", directory=directory)

            self.assertIn("Nalezeno vice archivu", output)
            self.assertIn("email-13964-canva-security-change", output)
            self.assertIn("email-13965-canva-login-alert", output)
            _assert_safe_archive_output(self, output)


def _archive_source(
    uid: str = "13964",
    subject: str = "Canva security change",
) -> EmailArchiveSource:
    return EmailArchiveSource(
        uid=uid,
        date="Sat, 16 May 2026 22:17:33 +0000",
        sender="Canva <security@canva.example>",
        subject=subject,
        body_text=(
            "Passkey authentication was added. "
            "Open https://www.canva.com/settings/login-and-security"
        ),
        body_html=(
            '<p>Security change</p><a href="https://www.canva.com/policies/privacy-policy/">'
            "privacy</a>"
        ),
        links=(
            "https://www.canva.com/settings/login-and-security",
            "https://www.canva.com/policies/privacy-policy/",
        ),
        attachments=(
            EmailAttachmentMeta(
                filename="security.pdf",
                content_type="application/pdf",
                size_bytes=1234,
                part_id="2",
                content_id="cid-1",
                disposition="attachment",
            ),
        ),
        original_eml=b"From: Canva <security@canva.example>\n\nRaw body",
        message_id="<fake-13964@example>",
        mailbox="INBOX",
        provider="fake",
    )


def _assert_safe_archive_output(
    testcase: unittest.TestCase,
    output: str,
) -> None:
    testcase.assertNotIn("http://", output)
    testcase.assertNotIn("https://", output)
    testcase.assertNotIn("security@canva.example", output)
    testcase.assertNotIn("Passkey authentication was added", output)


if __name__ == "__main__":
    unittest.main()
