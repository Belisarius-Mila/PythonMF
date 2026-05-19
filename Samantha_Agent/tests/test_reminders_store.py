from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.email.action_case_models import (
    ActionCaseAttachmentMeta,
    ActionCaseLinkDomain,
    ReminderDraft,
    ReminderSource,
)
from app.reminders.store import load_reminders_store, save_reminder_draft


class RemindersStoreTests(unittest.TestCase):
    def test_creates_new_reminders_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "nested" / "reminders.json"
            reminder = _safe_reminder("email-test-create")

            result = save_reminder_draft(reminder, path=path)

            self.assertTrue(result.created)
            self.assertTrue(path.exists())
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(len(data["reminders"]), 1)
            self.assertEqual(data["reminders"][0]["id"], "email-test-create")

    def test_adds_task_to_existing_store(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "reminders.json"
            save_reminder_draft(_safe_reminder("first"), path=path)

            result = save_reminder_draft(_safe_reminder("second"), path=path)
            store = load_reminders_store(path)

            self.assertTrue(result.created)
            self.assertEqual([item["id"] for item in store["reminders"]], ["first", "second"])

    def test_does_not_add_duplicate_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "reminders.json"
            save_reminder_draft(_safe_reminder("same-id"), path=path)

            result = save_reminder_draft(_safe_reminder("same-id"), path=path)
            store = load_reminders_store(path)

            self.assertFalse(result.created)
            self.assertIn("duplicita nebyla pridana", result.message)
            self.assertEqual(len(store["reminders"]), 1)

    def test_rejects_full_urls_and_unredacted_emails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "reminders.json"
            unsafe_url = _safe_reminder_dict("unsafe-url")
            unsafe_url["notes"] = "Podrobnosti jsou na https://example.com/private"
            unsafe_email = _safe_reminder_dict("unsafe-email")
            unsafe_email["source"]["sender"] = "NIBE <servis@example.com>"

            with self.assertRaisesRegex(ValueError, "plne URL"):
                save_reminder_draft(unsafe_url, path=path)
            with self.assertRaisesRegex(ValueError, "e-mailovou adresu"):
                save_reminder_draft(unsafe_email, path=path)

            self.assertFalse(path.exists())

    def test_saves_only_safe_domains_and_attachment_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "reminders.json"
            reminder = _safe_reminder("safe-content")

            save_reminder_draft(reminder, path=path)

            raw = path.read_text(encoding="utf-8")
            self.assertIn("partner.example", raw)
            self.assertIn("cenik.pdf", raw)
            self.assertNotIn("https://", raw)
            self.assertNotIn("servis@nibe.example", raw)


def _safe_reminder(reminder_id: str) -> ReminderDraft:
    return ReminderDraft(
        id=reminder_id,
        title="Objednat prohlidku fotovoltaiky",
        notes=(
            "Nabidka doporucuje objednat preventivni prohlidku. "
            "Dalsi krok: objednat termin."
        ),
        due_date="2026-07-31",
        priority="low",
        status="open",
        source=ReminderSource(
            type="email",
            uid="fake-uid",
            date="Tue, 5 May 2026 14:02:22 +0000",
            sender="NIBE servis <[e-mail redigovan]>",
        ),
        links=(ActionCaseLinkDomain(domain="partner.example", count=2),),
        attachments=(
            ActionCaseAttachmentMeta(
                filename="cenik.pdf",
                content_type="application/pdf",
                size_bytes=1234,
                part_id="2",
                disposition="attachment",
            ),
        ),
    )


def _safe_reminder_dict(reminder_id: str) -> dict[str, object]:
    return {
        "id": reminder_id,
        "title": "Objednat prohlidku fotovoltaiky",
        "notes": "Bezpecne redigovane poznamky.",
        "due_date": "2026-07-31",
        "priority": "low",
        "status": "open",
        "source": {
            "type": "email",
            "uid": "fake-uid",
            "date": "Tue, 5 May 2026 14:02:22 +0000",
            "sender": "NIBE servis <[e-mail redigovan]>",
        },
        "links": [{"domain": "partner.example", "count": 1}],
        "attachments": [],
    }


if __name__ == "__main__":
    unittest.main()
