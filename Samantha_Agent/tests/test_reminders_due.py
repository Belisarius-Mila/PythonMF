from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app import samantha_agent
from app.reminders.due import format_active_due_reminders, load_active_due_reminders


class RemindersDueTests(unittest.TestCase):
    def test_overdue_reminder_is_returned_and_formatted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_store(Path(temp_dir), [_reminder("overdue", "2026-05-18")])

            grouped = load_active_due_reminders(path=path, today="2026-05-19")
            formatted = format_active_due_reminders(path=path, today="2026-05-19")

            self.assertEqual([item.id for item in grouped["overdue"]], ["overdue"])
            self.assertIn("Prosle:", formatted)
            self.assertIn("overdue", formatted)

    def test_due_today_reminder_is_returned(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_store(Path(temp_dir), [_reminder("today", "2026-05-19")])

            grouped = load_active_due_reminders(path=path, today="2026-05-19")
            formatted = format_active_due_reminders(path=path, today="2026-05-19")

            self.assertEqual([item.id for item in grouped["due_today"]], ["today"])
            self.assertIn("Dnes:", formatted)
            self.assertIn("today", formatted)

    def test_due_within_14_days_is_returned(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_store(Path(temp_dir), [_reminder("soon", "2026-06-02")])

            grouped = load_active_due_reminders(path=path, today="2026-05-19")
            formatted = format_active_due_reminders(path=path, today="2026-05-19")

            self.assertEqual([item.id for item in grouped["due_soon"]], ["soon"])
            self.assertIn("Do 14 dnu:", formatted)
            self.assertIn("soon", formatted)

    def test_due_after_15_days_is_not_returned(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_store(Path(temp_dir), [_reminder("later", "2026-06-03")])

            grouped = load_active_due_reminders(path=path, today="2026-05-19")
            formatted = format_active_due_reminders(path=path, today="2026-05-19")

            self.assertEqual(grouped["overdue"], [])
            self.assertEqual(grouped["due_today"], [])
            self.assertEqual(grouped["due_soon"], [])
            self.assertNotIn("later", formatted)

    def test_closed_and_done_reminders_are_not_returned(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_store(
                Path(temp_dir),
                [
                    _reminder("closed", "2026-05-18", status="closed"),
                    _reminder("done", "2026-05-19", status="done"),
                ],
            )

            grouped = load_active_due_reminders(path=path, today="2026-05-19")
            formatted = format_active_due_reminders(path=path, today="2026-05-19")

            self.assertEqual(grouped["overdue"], [])
            self.assertEqual(grouped["due_today"], [])
            self.assertEqual(grouped["due_soon"], [])
            self.assertNotIn("closed", formatted)
            self.assertNotIn("done", formatted)

    def test_formatted_output_does_not_include_full_urls_or_unredacted_emails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_store(
                Path(temp_dir),
                [
                    _reminder(
                        "unsafe",
                        "2026-05-19",
                        title="Proverit https://example.com/private servis@example.com",
                    )
                ],
            )

            formatted = format_active_due_reminders(path=path, today="2026-05-19")

            self.assertNotIn("https://", formatted)
            self.assertNotIn("servis@example.com", formatted)
            self.assertIn("[URL redigovano]", formatted)
            self.assertIn("[e-mail redigovan]", formatted)

    def test_email_source_notice_requires_separate_uid_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_store(Path(temp_dir), [_reminder("email-source", "2026-05-19")])

            formatted = format_active_due_reminders(path=path, today="2026-05-19")

            self.assertIn("zdrojovy e-mail UID fake-uid", formatted)
            self.assertIn("samostatne potvrzeni UID", formatted)

    def test_load_memory_appends_active_reminders_section(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir)
            (memory_dir / "note.md").write_text("Bezpecna memory poznamka.", encoding="utf-8")
            original_formatter = samantha_agent.format_active_due_reminders
            samantha_agent.format_active_due_reminders = lambda: "AKTIVNI PRIPOMINKY:\n- Test"
            try:
                memory_text = samantha_agent.load_memory(memory_dir=memory_dir)
            finally:
                samantha_agent.format_active_due_reminders = original_formatter

            self.assertIn("Bezpecna memory poznamka.", memory_text)
            self.assertIn("AKTIVNI PRIPOMINKY:", memory_text)


def _write_store(temp_dir: Path, reminders: list[dict[str, object]]) -> Path:
    path = temp_dir / "reminders.json"
    path.write_text(json.dumps({"reminders": reminders}), encoding="utf-8")
    return path


def _reminder(
    reminder_id: str,
    due_date: str,
    status: str = "open",
    title: str = "Objednat prohlidku fotovoltaiky",
) -> dict[str, object]:
    return {
        "id": reminder_id,
        "title": title,
        "notes": "Bezpecne redigovane poznamky.",
        "due_date": due_date,
        "priority": "low",
        "status": status,
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
