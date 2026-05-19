from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.email.case_vault_tools import (
    has_explicit_save_cases_confirmation,
    save_selected_email_cases_from_uids_text,
)
from app.email.models import EmailAttachmentMeta, EmailHeader, EmailMessage


class EmailCaseVaultToolsTests(unittest.TestCase):
    def test_without_confirmation_provider_is_not_called(self) -> None:
        def fail_provider() -> object:
            raise AssertionError("Provider must not be called without confirmation")

        result = save_selected_email_cases_from_uids_text(
            uids=["fake-nibe"],
            user_confirmed=False,
            confirmation_text="",
            provider_factory=fail_provider,
        )

        self.assertIn("provider nevolam", result)

    def test_confirmation_must_contain_all_uids(self) -> None:
        self.assertFalse(
            has_explicit_save_cases_confirmation(
                uids=["fake-nibe", "fake-apple"],
                confirmation_text=(
                    "Potvrzuji, uloz UID fake-nibe jako case do EmailCaseVault."
                ),
            )
        )
        self.assertTrue(
            has_explicit_save_cases_confirmation(
                uids=["fake-nibe", "fake-apple"],
                confirmation_text=(
                    "Potvrzuji, uloz UID fake-nibe a fake-apple jako case do "
                    "EmailCaseVault."
                ),
            )
        )

    def test_confirmed_session_uses_fake_provider_messages(self) -> None:
        fake_provider = _FakeProvider()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = save_selected_email_cases_from_uids_text(
                uids=["fake-nibe", "fake-apple"],
                user_confirmed=True,
                confirmation_text=_confirmation(),
                provider_factory=lambda: fake_provider,
                vault_directory=Path(temp_dir),
            )

        self.assertEqual(
            fake_provider.calls,
            [("fake-nibe", 3000), ("fake-apple", 3000)],
        )
        self.assertIn("Souhrn: ulozeno 2, duplicity 0", result)

    def test_saves_safe_cases_to_temp_vault(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            result = save_selected_email_cases_from_uids_text(
                uids=["fake-nibe", "fake-apple"],
                user_confirmed=True,
                confirmation_text=_confirmation(),
                provider_factory=_FakeProvider,
                vault_directory=directory,
            )
            case_files = sorted(path for path in directory.glob("*.json") if path.name != "index.json")
            raw = "\n".join(path.read_text(encoding="utf-8") for path in case_files)
            index = json.loads((directory / "index.json").read_text(encoding="utf-8"))

            self.assertIn("Souhrn: ulozeno 2, duplicity 0", result)
            self.assertEqual(len(case_files), 2)
            self.assertEqual(len(index["cases"]), 2)
            self.assertNotIn("PRIVATE BODY TAIL MUST NOT LEAK", raw)
            self.assertNotIn("https://", raw)
            self.assertNotIn("servis@nibe.example", raw)
            self.assertNotIn("security@apple.example", raw)

    def test_duplicate_cases_are_not_added(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            first = save_selected_email_cases_from_uids_text(
                uids=["fake-nibe"],
                user_confirmed=True,
                confirmation_text=_confirmation(uid_text="fake-nibe"),
                provider_factory=_FakeProvider,
                vault_directory=directory,
            )
            second = save_selected_email_cases_from_uids_text(
                uids=["fake-nibe"],
                user_confirmed=True,
                confirmation_text=_confirmation(uid_text="fake-nibe"),
                provider_factory=_FakeProvider,
                vault_directory=directory,
            )
            index = json.loads((directory / "index.json").read_text(encoding="utf-8"))

            self.assertIn("Souhrn: ulozeno 1, duplicity 0", first)
            self.assertIn("Souhrn: ulozeno 0, duplicity 1", second)
            self.assertEqual(len(index["cases"]), 1)

    def test_output_does_not_include_body_full_urls_or_unredacted_emails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = save_selected_email_cases_from_uids_text(
                uids=["fake-nibe", "fake-apple"],
                user_confirmed=True,
                confirmation_text=_confirmation(),
                provider_factory=_FakeProvider,
                vault_directory=Path(temp_dir),
            )

            self.assertNotIn("PRIVATE BODY TAIL MUST NOT LEAK", result)
            self.assertNotIn("https://", result)
            self.assertNotIn("servis@nibe.example", result)
            self.assertNotIn("security@apple.example", result)

    def test_tool_does_not_write_to_memory_or_reminders(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            vault_directory = root / "cases"

            save_selected_email_cases_from_uids_text(
                uids=["fake-nibe"],
                user_confirmed=True,
                confirmation_text=_confirmation(uid_text="fake-nibe"),
                provider_factory=_FakeProvider,
                vault_directory=vault_directory,
            )

            self.assertTrue(vault_directory.exists())
            self.assertFalse((root / "memory").exists())
            self.assertFalse((root / "reminders").exists())


class _FakeProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def read_message_by_uid(self, uid: str, max_chars: int) -> EmailMessage:
        self.calls.append((uid, max_chars))
        messages = {
            "fake-nibe": _nibe_message(),
            "fake-apple": _apple_message(),
        }
        return messages[uid]


def _confirmation(uid_text: str = "fake-nibe a fake-apple") -> str:
    return (
        "Potvrzuji, uloz UID "
        f"{uid_text} jako case do EmailCaseVault. "
        "Neotevirej odkazy, nestahuj prilohy a nic neposilej."
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
            "Objednejte prohlidku fotovoltaiky do konce cervence 2026. "
            "Portal https://partner.example/prohlidka. "
            "Kontakt servis@nibe.example. "
            "PRIVATE BODY TAIL MUST NOT LEAK."
        ),
        truncated=False,
        attachments=(
            EmailAttachmentMeta(
                filename="nabidka.pdf",
                content_type="application/pdf",
                size_bytes=1234,
                part_id="2",
                content_id="",
                disposition="attachment",
            ),
        ),
    )


def _apple_message() -> EmailMessage:
    return EmailMessage(
        header=EmailHeader(
            internal_id="fake-apple",
            date="Mon, 18 May 2026 08:59:52 +0000 (GMT)",
            sender="Apple <security@apple.example>",
            subject="Pro vas ucet Apple bylo vygenerovano heslo pro konkretni aplikaci",
        ),
        body_text=(
            "Bylo vygenerovano heslo pro konkretni aplikaci Samantha Agent. "
            "Pokud jste tuto zmenu neprovedli, zmente si heslo na "
            "https://account.apple.example/security. "
            "Kontakt security@apple.example. "
            "PRIVATE BODY TAIL MUST NOT LEAK."
        ),
        truncated=False,
    )


if __name__ == "__main__":
    unittest.main()
