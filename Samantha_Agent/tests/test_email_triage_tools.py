from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.email.models import EmailAttachmentMeta, EmailHeader, EmailMessage
from app.email.triage_tools import (
    has_explicit_triage_confirmation,
    run_email_triage_session_text,
)


class EmailTriageToolsTests(unittest.TestCase):
    def test_without_confirmation_provider_is_not_called(self) -> None:
        def fail_provider() -> object:
            raise AssertionError("Provider must not be called without confirmation")

        result = run_email_triage_session_text(
            days=7,
            user_confirmed=False,
            confirmation_text="",
            provider_factory=fail_provider,
        )

        self.assertIn("Bez toho provider nevolam", result)

    def test_confirmation_must_contain_denials(self) -> None:
        self.assertFalse(
            has_explicit_triage_confirmation(
                days=7,
                confirmation_text=(
                    "Potvrzuji Email Triage za poslednich 7 dni. "
                    "Souhlasim se ctenim hlavicek a tel kandidatnich e-mailu."
                ),
            )
        )

    def test_confirmation_accepts_current_czech_denial_wording(self) -> None:
        self.assertTrue(
            has_explicit_triage_confirmation(
                days=7,
                confirmation_text=(
                    "Potvrzuji Email Triage za posledních 7 dní.\n"
                    "Souhlasím se čtením hlaviček a omezeně těl kandidátních "
                    "e-mailů za posledních 7 dní.\n"
                    "Neotevírej odkazy. Nestahuj přílohy. Nic neodesílej. "
                    "Nemaž e-maily. Nepřesouvej e-maily. "
                    "Neoznačuj e-maily jako přečtené."
                ),
            )
        )

    def test_confirmed_session_uses_fake_provider_messages(self) -> None:
        fake_provider = _FakeProvider()
        with tempfile.TemporaryDirectory() as temp_dir:
            activity_state_path = Path(temp_dir) / "activity_state.json"

            result = run_email_triage_session_text(
                days=7,
                limit=10,
                max_chars_per_email=1500,
                user_confirmed=True,
                confirmation_text=_confirmation(),
                provider_factory=lambda: fake_provider,
                activity_state_path=activity_state_path,
            )

        self.assertEqual(fake_provider.calls, [(7, 10, 1500)])
        self.assertIn("Email Triage Session: poslednich 7 dni", result)
        self.assertIn("UID: fake-nibe", result)
        self.assertIn("UID: fake-newsletter", result)
        self.assertIn("Case kandidati:", result)

    def test_output_does_not_include_body_full_urls_or_unredacted_emails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_email_triage_session_text(
                days=7,
                limit=10,
                max_chars_per_email=1500,
                user_confirmed=True,
                confirmation_text=_confirmation(),
                provider_factory=_FakeProvider,
                activity_state_path=Path(temp_dir) / "activity_state.json",
            )

        self.assertNotIn("https://", result)
        self.assertNotIn("servis@nibe.example", result)
        self.assertNotIn("PRIVATE BODY TAIL MUST NOT LEAK", result)
        self.assertIn("[e-mail redigovan]", result)

    def test_tool_does_not_write_to_vault_reminders_or_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            before = set(temp_path.iterdir())

            run_email_triage_session_text(
                days=7,
                limit=10,
                max_chars_per_email=1500,
                user_confirmed=True,
                confirmation_text=_confirmation(),
                provider_factory=_FakeProvider,
                activity_state_path=temp_path / "activity_state.json",
            )

            after = set(temp_path.iterdir())
            self.assertEqual(after - before, {temp_path / "activity_state.json"})


class _FakeProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[int, int, int]] = []

    def list_recent_messages(
        self,
        days: int,
        limit: int,
        max_chars: int,
    ) -> list[EmailMessage]:
        self.calls.append((days, limit, max_chars))
        return [_nibe_message(), _newsletter_message()]


def _confirmation() -> str:
    return (
        "Potvrzuji Email Triage za poslednich 7 dni. "
        "Souhlasim se ctenim hlavicek a tel kandidatnich e-mailu. "
        "Zakazuji neotevirat odkazy, nestahovat prilohy, nic neodesilat, "
        "nemazat, nepresouvat a neoznacovat jako prectene."
    )


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


if __name__ == "__main__":
    unittest.main()
