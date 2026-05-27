from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.email.models import EmailAttachmentMeta, EmailHeader, EmailMessage, EmailMessageBatch, EmailSkippedMessage
from app.email.triage_tools import (
    has_explicit_triage_confirmation,
    run_email_triage_session_text,
    run_unified_email_triage_session_text,
)
from app.email.triage_service import triage_email_messages


class EmailTriageToolsTests(unittest.TestCase):
    def test_without_confirmation_provider_is_called_with_default_safe_policy(self) -> None:
        fake_provider = _FakeProvider()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_email_triage_session_text(
                days=7,
                limit=10,
                max_chars_per_email=1500,
                user_confirmed=False,
                confirmation_text="",
                provider_factory=lambda: fake_provider,
                activity_state_path=Path(temp_dir) / "activity_state.json",
            )

        self.assertEqual(fake_provider.calls, [(7, 10, 1500)])
        self.assertIn("Email Triage Session: poslednich 7 dni", result)
        self.assertIn("Bezpecnost: provider byl pouzit read-only", result)

    def test_legacy_require_confirmation_mode_does_not_call_provider_without_confirmation(self) -> None:
        def fail_provider() -> object:
            raise AssertionError("Provider must not be called without confirmation")

        result = run_email_triage_session_text(
            days=7,
            user_confirmed=False,
            confirmation_text="",
            require_confirmation=True,
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
        self.assertIn("Souhrn:", result)
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

    def test_provider_can_skip_unreadable_messages_and_continue(self) -> None:
        result = run_email_triage_session_text(
            days=7,
            limit=10,
            max_chars_per_email=1500,
            provider_factory=_ProviderWithOneUnreadableMessage,
        )

        self.assertIn("Email Triage Session: poslednich 7 dni", result)
        self.assertIn("UID: fake-newsletter", result)

    def test_unified_triage_includes_sources_spam_and_skipped_large_messages(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_unified_email_triage_session_text(
                days=7,
                limit_per_folder=10,
                max_chars_per_email=1500,
                include_spam=True,
                icloud_provider_factory=lambda: _UnifiedProvider(
                    messages=[_message_with_source("icloud-inbox", "iCloud", "INBOX")],
                    skipped=[
                        EmailSkippedMessage(
                            header=EmailHeader(
                                internal_id="icloud-big",
                                date="Tue, 5 May 2026 16:00:00 +0000",
                                sender="Big <big@example.com>",
                                subject="Velka zprava",
                                source="iCloud",
                                folder="Junk",
                            ),
                            reason="too_large",
                        )
                    ],
                ),
                seznam_provider_factory=lambda: _UnifiedProvider(
                    messages=[_message_with_source("seznam-spam", "Seznam", "Spam")]
                ),
                activity_state_path=Path(temp_dir) / "activity_state.json",
            )

        self.assertIn("Unified Email Triage Session: poslednich 7 dni", result)
        self.assertIn("Zdroj: iCloud / INBOX", result)
        self.assertIn("Zdroj: Seznam / Spam", result)
        self.assertIn("Preskocene velke/necitene zpravy:", result)
        self.assertIn("UID: icloud-big", result)
        self.assertIn("Duvod: too_large", result)
        self.assertIn("Spam slozky: zahrnuty", result)

    def test_scoring_prioritizes_insurance_and_lowers_marketing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_unified_email_triage_session_text(
                days=2,
                limit_per_folder=10,
                include_spam=True,
                icloud_provider_factory=lambda: _UnifiedProvider(
                    messages=[
                        _message_with_subject(
                            uid="insurance",
                            source="Seznam",
                            folder="INBOX",
                            subject="Předpis pojistné smlouvy č. 123",
                            body="Prosime uhradit pojistne do 30. 6. 2026.",
                        ),
                        _message_with_subject(
                            uid="marketing",
                            source="iCloud",
                            folder="Junk",
                            subject="Opakované výlety? Ušetřete 30 %",
                            body="Newsletterova sleva a marketingova akce.",
                        ),
                    ]
                ),
                seznam_provider_factory=lambda: _UnifiedProvider(messages=[]),
                activity_state_path=Path(temp_dir) / "activity_state.json",
            )

        self.assertIn("UID: insurance", result)
        self.assertIn("Priorita: high", result)
        self.assertIn("UID: marketing", result)
        marketing_index = result.index("UID: marketing")
        self.assertIn("Priorita: low", result[marketing_index:marketing_index + 300])

    def test_scoring_buckets_common_real_world_mail_types(self) -> None:
        messages = [
            _message_with_subject(
                uid="cpp",
                source="Seznam",
                folder="INBOX",
                subject="Predpis pojistne smlouvy c. 123",
                body="Prosime uhradit pojistne do 30. 6. 2026.",
            ),
            _message_with_subject(
                uid="generali",
                source="iCloud",
                folder="INBOX",
                subject="Overeni prihlaseni do klientske zony",
                body="Vas ucet je pouzivan, zkontrolujte prihlasovaci kod.",
            ),
            _message_with_subject(
                uid="balikovna",
                source="iCloud",
                folder="INBOX",
                subject="Balikovna: zasilka je pripravena k vyzvednuti",
                body="Balik je pripraven k vyzvednuti.",
            ),
            _message_with_subject(
                uid="trh-knih",
                source="iCloud",
                folder="INBOX",
                subject="Trh knih: Den deti a knizni tipy",
                body="Newsletter, sleva a akce. Objednat muzete online.",
            ),
            _message_with_subject(
                uid="axa-junk",
                source="iCloud",
                folder="Junk",
                subject="AXA: cestovni pojisteni se slevou",
                body="Marketingova akce na cestovni pojisteni. Odhlasit newsletter.",
            ),
            _message_with_subject(
                uid="politika",
                source="Seznam",
                folder="INBOX",
                subject="Pozvanka na politickou konferenci",
                body="Pozvanka, superdebata a politicky newsletter.",
            ),
            _message_with_subject(
                uid="apple-password",
                source="iCloud",
                folder="INBOX",
                subject="Pro vas ucet Apple bylo vygenerovano heslo pro konkretni aplikaci",
                body="Pokud jste heslo negenerovali, zkontrolujte zabezpeceni uctu.",
            ),
            _message_with_subject(
                uid="client-zone",
                source="iCloud",
                folder="INBOX",
                subject="Pristupy do klientske zony",
                body="Informace k pristupum do klientske zony.",
            ),
        ]

        result = triage_email_messages(messages)
        by_uid = {item.uid: item for item in result.all_items}

        self.assertEqual(by_uid["cpp"].priority, "high")
        self.assertEqual(by_uid["generali"].priority, "high")
        self.assertNotIn(by_uid["generali"], result.newsletter_emails)
        self.assertEqual(by_uid["balikovna"].priority, "normal")
        self.assertEqual(by_uid["trh-knih"].priority, "low")
        self.assertFalse(by_uid["trh-knih"].has_action)
        self.assertEqual(by_uid["axa-junk"].priority, "low")
        self.assertEqual(by_uid["axa-junk"].category, "spam")
        self.assertEqual(by_uid["politika"].priority, "low")
        self.assertEqual(by_uid["apple-password"].priority, "high")
        self.assertEqual(by_uid["client-zone"].priority, "high")

    def test_triage_report_has_summary_and_detailed_high_items_without_duplicate_case_section(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_unified_email_triage_session_text(
                days=2,
                limit_per_folder=10,
                include_spam=True,
                icloud_provider_factory=lambda: _UnifiedProvider(
                    messages=[
                        _message_with_subject(
                            uid="invoice",
                            source="iCloud",
                            folder="INBOX",
                            subject="Faktura za objednavku 123",
                            body="V priloze posilame fakturu a doklad k objednavce.",
                        ),
                        _message_with_subject(
                            uid="newsletter",
                            source="iCloud",
                            folder="INBOX",
                            subject="Newsletter: knizni novinky",
                            body="Newsletter a marketing.",
                        ),
                    ]
                ),
                seznam_provider_factory=lambda: _UnifiedProvider(messages=[]),
                activity_state_path=Path(temp_dir) / "activity_state.json",
            )

        self.assertIn("Souhrn:", result)
        self.assertIn("High priorita:", result)
        self.assertIn("UID: invoice | Datum:", result)
        self.assertIn("Normal priorita:", result)
        self.assertIn("Low priorita - inbox/newslettery:", result)
        self.assertIn("Shrnuti:", result)
        self.assertIn("Kategorie: important", result)
        self.assertNotIn("\nCase kandidati:\n", result)

    def test_high_security_email_does_not_get_low_priority_next_step_from_footer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_unified_email_triage_session_text(
                days=2,
                limit_per_folder=10,
                include_spam=True,
                icloud_provider_factory=lambda: _UnifiedProvider(
                    messages=[
                        _message_with_subject(
                            uid="apple-password",
                            source="iCloud",
                            folder="INBOX",
                            subject="Pro vas ucet Apple bylo vygenerovano heslo pro konkretni aplikaci",
                            body="Marketing preference footer. Bezpecnostni upozorneni k uctu.",
                        )
                    ]
                ),
                seznam_provider_factory=lambda: _UnifiedProvider(messages=[]),
                activity_state_path=Path(temp_dir) / "activity_state.json",
            )

        item_index = result.index("UID: apple-password")
        item_block = result[item_index:item_index + 800]
        self.assertIn("Priorita: high", item_block)
        self.assertIn("Zkontrolovat dulezity e-mail", item_block)
        self.assertNotIn("Pouze informativni / nizka priorita", item_block)

    def test_low_priority_sections_are_capped_in_chat_report(self) -> None:
        low_messages = [
            _message_with_subject(
                uid=f"newsletter-{index}",
                source="iCloud",
                folder="INBOX",
                subject=f"Newsletter {index}",
                body="Newsletter a marketing.",
            )
            for index in range(25)
        ]
        spam_messages = [
            _message_with_subject(
                uid=f"spam-{index}",
                source="Seznam",
                folder="spam",
                subject=f"Spam {index}",
                body="Spam newsletter.",
            )
            for index in range(18)
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_unified_email_triage_session_text(
                days=2,
                limit_per_folder=50,
                include_spam=True,
                icloud_provider_factory=lambda: _UnifiedProvider(messages=low_messages),
                seznam_provider_factory=lambda: _UnifiedProvider(messages=spam_messages),
                activity_state_path=Path(temp_dir) / "activity_state.json",
            )

        self.assertIn("Low/newsletter/spam: 43", result)
        self.assertIn("dalsich 5 nizkoprioritnich polozek skryto", result)
        self.assertIn("dalsich 3 nizkoprioritnich polozek skryto", result)
        self.assertIn("UID: newsletter-19 | Datum:", result)
        self.assertNotIn("UID: newsletter-20 | Datum:", result)
        self.assertIn("UID: spam-14 | Datum:", result)
        self.assertNotIn("UID: spam-15 | Datum:", result)


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


class _ProviderWithOneUnreadableMessage:
    def list_recent_messages(
        self,
        days: int,
        limit: int,
        max_chars: int,
    ) -> list[EmailMessage]:
        return [_newsletter_message()]


class _UnifiedProvider:
    def __init__(
        self,
        messages: list[EmailMessage],
        skipped: list[EmailSkippedMessage] | None = None,
    ) -> None:
        self._batch = EmailMessageBatch(
            messages=tuple(messages),
            skipped=tuple(skipped or []),
        )

    def list_recent_messages_with_skipped(
        self,
        days: int,
        limit: int,
        max_chars: int,
        include_spam: bool,
    ) -> EmailMessageBatch:
        return self._batch


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


def _message_with_source(uid: str, source: str, folder: str) -> EmailMessage:
    return EmailMessage(
        header=EmailHeader(
            internal_id=uid,
            date="Tue, 5 May 2026 15:00:00 +0000",
            sender=f"{source} <source@example.com>",
            subject="Objednat kontrolu do konce tydne",
            source=source,
            folder=folder,
        ),
        body_text="Prosim objednat kontrolu do konce tydne.",
        truncated=False,
    )


def _message_with_subject(
    uid: str,
    source: str,
    folder: str,
    subject: str,
    body: str,
) -> EmailMessage:
    return EmailMessage(
        header=EmailHeader(
            internal_id=uid,
            date="Tue, 5 May 2026 15:00:00 +0000",
            sender=f"{source} <source@example.com>",
            subject=subject,
            source=source,
            folder=folder,
        ),
        body_text=body,
        truncated=False,
    )


if __name__ == "__main__":
    unittest.main()
