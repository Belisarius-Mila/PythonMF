from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from app.email.activity_state import load_email_activity_state
from app.email.archive_models import EmailArchiveSource
from app.email.archive_tools import (
    archive_email_by_uid_text,
    has_explicit_archive_confirmation,
)
from app.email.models import EmailAttachmentMeta


class EmailArchiveToolsTests(unittest.TestCase):
    def test_without_confirmation_provider_is_not_called(self) -> None:
        def fail_provider() -> object:
            raise AssertionError("Provider must not be called without confirmation")

        result = archive_email_by_uid_text(
            uid="13964",
            user_confirmed=False,
            confirmation_text="",
            provider_factory=fail_provider,
        )

        self.assertIn("provider nevolam", result)

    def test_confirmation_must_contain_uid_and_archive_consent(self) -> None:
        self.assertFalse(
            has_explicit_archive_confirmation(
                uid="13964",
                confirmation_text="Potvrzuji kompletni archivaci do EmailArchiveVault.",
            )
        )
        self.assertFalse(
            has_explicit_archive_confirmation(
                uid="13964",
                confirmation_text="Potvrzuji precteni e-mailu UID 13964.",
            )
        )
        self.assertTrue(
            has_explicit_archive_confirmation(
                uid="13964",
                confirmation_text=(
                    "Potvrzuji, ze chci kompletni archivaci e-mailu UID 13964 "
                    "do EmailArchiveVault."
                ),
            )
        )

    def test_confirmed_archive_saves_to_temp_directory_and_records_activity(self) -> None:
        fake_provider = _FakeArchiveProvider()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archive_directory = root / "archive"
            activity_path = root / "activity_state.json"

            result = archive_email_by_uid_text(
                uid="13964",
                user_confirmed=True,
                confirmation_text=_confirmation(),
                provider_factory=lambda: fake_provider,
                archive_directory=archive_directory,
                activity_state_path=activity_path,
            )
            state = load_email_activity_state(activity_path)

            self.assertEqual(fake_provider.calls, [("13964", 50000)])
            self.assertIn("Archive ID: email-13964-canva-security-change", result)
            self.assertIn("metadata.json", result)
            self.assertIn("body.txt", result)
            self.assertIn("body.html", result)
            self.assertIn("links.json", result)
            self.assertIn("attachments/attachments.json", result)
            self.assertIn("original.eml", result)
            self.assertEqual(state.last_archive_at, date.today().isoformat())
            self.assertEqual(len([path for path in archive_directory.iterdir() if path.is_dir()]), 1)

    def test_output_does_not_include_body_full_urls_or_unredacted_emails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = archive_email_by_uid_text(
                uid="13964",
                user_confirmed=True,
                confirmation_text=_confirmation(),
                provider_factory=_FakeArchiveProvider,
                archive_directory=Path(temp_dir) / "archive",
                activity_state_path=Path(temp_dir) / "activity_state.json",
            )

            self.assertNotIn("PRIVATE BODY MUST NOT LEAK", result)
            self.assertNotIn("https://", result)
            self.assertNotIn("http://", result)
            self.assertNotIn("security@canva.example", result)
            self.assertNotIn("www.canva.com", result)
            self.assertNotIn("tracking.example", result)

    def test_duplicate_archive_is_not_added(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archive_directory = root / "archive"
            activity_path = root / "activity_state.json"

            first = archive_email_by_uid_text(
                uid="13964",
                user_confirmed=True,
                confirmation_text=_confirmation(),
                provider_factory=_FakeArchiveProvider,
                archive_directory=archive_directory,
                activity_state_path=activity_path,
            )
            second = archive_email_by_uid_text(
                uid="13964",
                user_confirmed=True,
                confirmation_text=_confirmation(),
                provider_factory=_FakeArchiveProvider,
                archive_directory=archive_directory,
                activity_state_path=activity_path,
            )

            self.assertIn("Stav: ulozeno", first)
            self.assertIn("Stav: uz existuje", second)
            self.assertEqual(len([path for path in archive_directory.iterdir() if path.is_dir()]), 1)


class _FakeArchiveProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def read_archive_source_by_uid(self, uid: str, max_chars: int) -> EmailArchiveSource:
        self.calls.append((uid, max_chars))
        return _archive_source(uid=uid)


def _confirmation() -> str:
    return (
        "Potvrzuji, ze chci kompletni archivaci e-mailu UID 13964 "
        "do EmailArchiveVault."
    )


def _archive_source(uid: str = "13964") -> EmailArchiveSource:
    return EmailArchiveSource(
        uid=uid,
        date="Sat, 16 May 2026 22:17:33 +0000",
        sender="Canva <security@canva.example>",
        subject="Canva security change",
        body_text=(
            "PRIVATE BODY MUST NOT LEAK. "
            "Open https://www.canva.com/settings/login-and-security "
            "and http://tracking.example/pixel"
        ),
        body_html='<a href="https://www.canva.com/policies/privacy-policy/">privacy</a>',
        links=(
            "https://www.canva.com/settings/login-and-security",
            "https://www.canva.com/policies/privacy-policy/",
            "http://tracking.example/pixel",
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
        message_id="<fake@example>",
        provider="fake",
    )


if __name__ == "__main__":
    unittest.main()
