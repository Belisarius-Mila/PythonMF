from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from app.email.archive_models import EmailArchiveSource
from app.email.archive_service import (
    email_message_to_archive_source,
    save_email_archive,
)
from app.email.models import EmailAttachmentMeta, EmailHeader, EmailMessage


class EmailArchiveServiceTests(unittest.TestCase):
    def test_saves_archive_files_to_explicit_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            source = _archive_source()

            result = save_email_archive(
                source,
                directory=directory,
                archived_at=_fixed_time(),
            )

            self.assertTrue(result.created)
            self.assertTrue(result.path.is_dir())
            self.assertEqual(result.path.parent, directory)
            self.assertTrue((result.path / "metadata.json").exists())
            self.assertTrue((result.path / "body.txt").exists())
            self.assertTrue((result.path / "body.html").exists())
            self.assertTrue((result.path / "links.json").exists())
            self.assertTrue((result.path / "attachments" / "attachments.json").exists())
            self.assertTrue((result.path / "original.eml").exists())

    def test_metadata_json_contains_archive_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = save_email_archive(
                _archive_source(),
                directory=Path(temp_dir),
                archived_at=_fixed_time(),
            )
            metadata = _read_json(result.path / "metadata.json")

            self.assertEqual(metadata["uid"], "fake-13964")
            self.assertEqual(metadata["subject"], "Canva security change")
            self.assertEqual(metadata["from"], "Canva <security@canva.example>")
            self.assertEqual(metadata["message_id"], "<fake-13964@example>")
            self.assertEqual(metadata["archived_at"], "2026-05-19T12:00:00+00:00")
            self.assertTrue(metadata["body_text_saved"])
            self.assertTrue(metadata["body_html_saved"])
            self.assertTrue(metadata["original_eml_saved"])
            self.assertEqual(metadata["attachments_count"], 1)
            self.assertEqual(metadata["links_count"], 2)
            self.assertTrue(metadata["safety_flags"]["local_sensitive_archive"])
            self.assertTrue(metadata["safety_flags"]["do_not_commit"])

    def test_body_html_is_optional(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _archive_source(body_html="")
            result = save_email_archive(source, directory=Path(temp_dir))
            metadata = _read_json(result.path / "metadata.json")

            self.assertTrue((result.path / "body.txt").exists())
            self.assertFalse((result.path / "body.html").exists())
            self.assertFalse(metadata["body_html_saved"])

    def test_links_json_contains_full_urls_without_opening_them(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = save_email_archive(_archive_source(), directory=Path(temp_dir))
            links = _read_json(result.path / "links.json")

            urls = [item["url"] for item in links["links"]]
            self.assertEqual(
                urls,
                [
                    "https://www.canva.com/settings/login-and-security",
                    "https://www.canva.com/policies/privacy-policy/",
                ],
            )
            self.assertEqual(links["links"][0]["domain"], "www.canva.com")

    def test_attachment_files_are_not_saved_only_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = save_email_archive(_archive_source(), directory=Path(temp_dir))
            attachment_dir = result.path / "attachments"
            attachments = _read_json(attachment_dir / "attachments.json")

            self.assertEqual(len(attachments["attachments"]), 1)
            self.assertEqual(attachments["attachments"][0]["filename"], "security.pdf")
            self.assertFalse(attachments["attachments"][0]["saved"])
            self.assertEqual(
                sorted(path.name for path in attachment_dir.iterdir()),
                ["attachments.json"],
            )

    def test_original_eml_is_saved_only_when_passed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with_original = save_email_archive(_archive_source(), directory=Path(temp_dir) / "one")
            without_original = save_email_archive(
                _archive_source(uid="fake-2", original_eml=None),
                directory=Path(temp_dir) / "two",
            )

            self.assertEqual(
                (with_original.path / "original.eml").read_bytes(),
                b"From: Canva <security@canva.example>\n\nRaw body",
            )
            self.assertFalse((without_original.path / "original.eml").exists())

    def test_duplicate_archive_is_not_added(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            first = save_email_archive(_archive_source(), directory=directory)
            second = save_email_archive(_archive_source(), directory=directory)

            self.assertTrue(first.created)
            self.assertFalse(second.created)
            self.assertEqual(first.path, second.path)
            self.assertIn("duplicita nebyla pridana", second.message)
            self.assertEqual(len(list(directory.iterdir())), 1)

    def test_email_message_helper_extracts_links_from_text_and_html(self) -> None:
        message = EmailMessage(
            header=EmailHeader(
                internal_id="fake-message",
                date="Tue, 19 May 2026 12:00:00 +0000",
                sender="Sender <sender@example.com>",
                subject="Subject",
            ),
            body_text="Text link https://example.com/text",
            truncated=False,
        )

        source = email_message_to_archive_source(
            message,
            body_html='<a href="https://example.com/html">link</a>',
            original_eml=b"raw",
            message_id="<id@example.com>",
            provider="fake",
        )

        self.assertEqual(source.uid, "fake-message")
        self.assertEqual(
            source.links,
            ("https://example.com/text", "https://example.com/html"),
        )
        self.assertEqual(source.original_eml, b"raw")
        self.assertEqual(source.message_id, "<id@example.com>")
        self.assertEqual(source.provider, "fake")


def _archive_source(
    uid: str = "fake-13964",
    body_html: str = (
        '<p>Security change</p><a href="https://www.canva.com/policies/privacy-policy/">'
        "privacy</a>"
    ),
    original_eml: bytes | None = b"From: Canva <security@canva.example>\n\nRaw body",
) -> EmailArchiveSource:
    return EmailArchiveSource(
        uid=uid,
        date="Sat, 16 May 2026 22:17:33 +0000",
        sender="Canva <security@canva.example>",
        subject="Canva security change",
        body_text=(
            "Passkey authentication was added. "
            "Open https://www.canva.com/settings/login-and-security"
        ),
        body_html=body_html,
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
        original_eml=original_eml,
        message_id="<fake-13964@example>",
        mailbox="INBOX",
        provider="fake",
    )


def _fixed_time() -> datetime:
    return datetime(2026, 5, 19, 12, 0, 0, tzinfo=timezone.utc)


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
