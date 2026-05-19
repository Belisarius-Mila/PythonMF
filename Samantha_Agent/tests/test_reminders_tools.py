from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.reminders.store import load_reminders_store
from app.reminders.tools import (
    has_explicit_reminder_save_confirmation,
    save_email_action_case_reminder_text,
)


class ReminderToolsTests(unittest.TestCase):
    def test_confirmation_requires_id_save_and_reminder_words(self) -> None:
        self.assertTrue(
            has_explicit_reminder_save_confirmation(
                reminder_id="email-test",
                confirmation_text="Potvrzuji, uloz pripominku email-test.",
            )
        )
        self.assertFalse(
            has_explicit_reminder_save_confirmation(
                reminder_id="email-test",
                confirmation_text="Potvrzuji, uloz tu pripominku.",
            )
        )
        self.assertFalse(
            has_explicit_reminder_save_confirmation(
                reminder_id="email-test",
                confirmation_text="Potvrzuji email-test.",
            )
        )

    def test_tool_does_not_write_without_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "reminders.json"

            result = _save(path=path, user_confirmed=False, confirmation_text="")

            self.assertIn("nic nezapisuji", result)
            self.assertFalse(path.exists())

    def test_tool_saves_safe_reminder_after_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "reminders.json"

            result = _save(
                path=path,
                user_confirmed=True,
                confirmation_text="Potvrzuji, uloz pripominku email-test.",
            )
            store = load_reminders_store(path)

            self.assertIn("Ulozeno: email-test", result)
            self.assertEqual(len(store["reminders"]), 1)
            self.assertEqual(store["reminders"][0]["id"], "email-test")
            self.assertEqual(store["reminders"][0]["links"][0]["domain"], "partner.example")
            self.assertNotIn("https://", path.read_text(encoding="utf-8"))
            self.assertNotIn("servis@nibe.example", path.read_text(encoding="utf-8"))

    def test_tool_does_not_add_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "reminders.json"
            confirmation = "Potvrzuji, uloz pripominku email-test."
            _save(path=path, user_confirmed=True, confirmation_text=confirmation)

            result = _save(path=path, user_confirmed=True, confirmation_text=confirmation)
            store = load_reminders_store(path)

            self.assertIn("duplicita nebyla pridana", result)
            self.assertEqual(len(store["reminders"]), 1)

    def test_tool_rejects_full_urls_and_unredacted_emails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "reminders.json"
            confirmation = "Potvrzuji, uloz pripominku email-test."

            unsafe_url = _save(
                path=path,
                user_confirmed=True,
                confirmation_text=confirmation,
                notes="Podrobnosti jsou na https://example.com/private",
            )
            unsafe_email = _save(
                path=path,
                user_confirmed=True,
                confirmation_text=confirmation,
                source_sender="NIBE <servis@nibe.example>",
            )

            self.assertIn("odmitnuto", unsafe_url)
            self.assertIn("plne URL", unsafe_url)
            self.assertIn("odmitnuto", unsafe_email)
            self.assertIn("e-mailovou adresu", unsafe_email)
            self.assertFalse(path.exists())


def _save(
    path: Path,
    user_confirmed: bool,
    confirmation_text: str,
    notes: str = "Bezpecne redigovane poznamky.",
    source_sender: str = "NIBE servis <[e-mail redigovan]>",
) -> str:
    return save_email_action_case_reminder_text(
        id="email-test",
        title="Objednat prohlidku fotovoltaiky",
        notes=notes,
        due_date="2026-07-31",
        priority="low",
        status="open",
        source_type="email",
        source_uid="fake-uid",
        source_date="Tue, 5 May 2026 14:02:22 +0000",
        source_sender=source_sender,
        link_domains=["partner.example|2"],
        attachments=["cenik.pdf|application/pdf|1234|2|attachment"],
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
        path=path,
    )


if __name__ == "__main__":
    unittest.main()
