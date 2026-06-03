from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.reminders.query_tools import (
    list_open_reminders_text,
    mark_reminder_done_text,
    show_reminder_detail_text,
)
from app.reminders.store import load_reminders_store


class ReminderQueryToolsTests(unittest.TestCase):
    def test_list_open_reminders_returns_open_and_not_done(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_store(
                Path(temp_dir),
                [
                    _reminder("open-id", "open"),
                    _reminder("done-id", "done"),
                ],
            )

            result = list_open_reminders_text(path=path)

            self.assertIn("open-id", result)
            self.assertNotIn("done-id", result)
            self.assertIn("source_type: email", result)

    def test_list_open_reminders_can_exclude_later_future(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_store(
                Path(temp_dir),
                [
                    _reminder("soon-id", "open", due_date="2026-05-25"),
                    _reminder("future-id", "open", due_date="2026-06-10"),
                ],
            )

            result = list_open_reminders_text(
                include_future=False,
                path=path,
                today="2026-05-19",
            )

            self.assertIn("soon-id", result)
            self.assertNotIn("future-id", result)

    def test_show_reminder_detail_returns_safe_detail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_store(Path(temp_dir), [_reminder("detail-id", "open")])

            result = show_reminder_detail_text("detail-id", path=path)

            self.assertIn("Detail pripominky:", result)
            self.assertIn("detail-id", result)
            self.assertIn("source_uid: fake-uid", result)
            self.assertIn("samostatne potvrzeni UID", result)
            self.assertIn("partner.example|2", result)
            self.assertIn("nabidka.pdf|application/pdf|1234", result)

    def test_mark_reminder_done_without_confirmation_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_store(Path(temp_dir), [_reminder("mark-id", "open")])

            result = mark_reminder_done_text(
                "mark-id",
                user_confirmed=False,
                confirmation_text="",
                path=path,
            )
            store = load_reminders_store(path)

            self.assertIn("nic nezapisuji", result)
            self.assertEqual(store["reminders"][0]["status"], "open")

    def test_mark_reminder_done_after_confirmation_changes_only_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_store(
                Path(temp_dir),
                [
                    _reminder("mark-id", "open"),
                    _reminder("other-id", "open"),
                ],
            )

            result = mark_reminder_done_text(
                "mark-id",
                user_confirmed=True,
                confirmation_text="Potvrzuji, oznac mark-id jako hotove.",
                path=path,
            )
            store = load_reminders_store(path)

            self.assertIn("Oznaceno jako hotove: mark-id", result)
            self.assertEqual(store["reminders"][0]["status"], "done")
            self.assertEqual(store["reminders"][0]["title"], "Objednat prohlidku fotovoltaiky")
            self.assertEqual(store["reminders"][1]["status"], "open")

    def test_mark_reminder_done_confirmation_matches_id_case_insensitively(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_store(Path(temp_dir), [_reminder("Mark-ID", "open")])

            result = mark_reminder_done_text(
                "Mark-ID",
                user_confirmed=True,
                confirmation_text="Potvrzuji, oznac mark-id jako hotove.",
                path=path,
            )
            store = load_reminders_store(path)

            self.assertIn("Oznaceno jako hotove: Mark-ID", result)
            self.assertEqual(store["reminders"][0]["status"], "done")

    def test_missing_id_returns_safe_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_store(Path(temp_dir), [_reminder("existing-id", "open")])

            result = mark_reminder_done_text(
                "missing-id",
                user_confirmed=True,
                confirmation_text="Potvrzuji, oznac missing-id jako hotove.",
                path=path,
            )
            store = load_reminders_store(path)

            self.assertIn("Pripominka nenalezena: missing-id", result)
            self.assertEqual(store["reminders"][0]["status"], "open")

    def test_outputs_do_not_include_full_urls_or_unredacted_emails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_store(
                Path(temp_dir),
                [
                    _reminder(
                        "unsafe-id",
                        "open",
                        title="Proverit https://example.com/private servis@example.com",
                        notes="Kontakt https://example.com a servis@example.com",
                    )
                ],
            )

            listed = list_open_reminders_text(path=path)
            detail = show_reminder_detail_text("unsafe-id", path=path)
            marked = mark_reminder_done_text(
                "unsafe-id",
                user_confirmed=True,
                confirmation_text="Potvrzuji, oznac unsafe-id jako hotove.",
                path=path,
            )
            combined = "\n".join([listed, detail, marked])

            self.assertNotIn("https://", combined)
            self.assertNotIn("servis@example.com", combined)
            self.assertIn("[URL redigovano]", combined)
            self.assertIn("[e-mail redigovan]", combined)


def _write_store(temp_dir: Path, reminders: list[dict[str, object]]) -> Path:
    path = temp_dir / "reminders.json"
    path.write_text(json.dumps({"reminders": reminders}), encoding="utf-8")
    return path


def _reminder(
    reminder_id: str,
    status: str,
    due_date: str = "2026-07-31",
    title: str = "Objednat prohlidku fotovoltaiky",
    notes: str = "Bezpecne redigovane poznamky.",
) -> dict[str, object]:
    return {
        "id": reminder_id,
        "title": title,
        "notes": notes,
        "due_date": due_date,
        "priority": "low",
        "status": status,
        "source": {
            "type": "email",
            "uid": "fake-uid",
            "date": "Tue, 5 May 2026 14:02:22 +0000",
            "sender": "NIBE servis <[e-mail redigovan]>",
        },
        "links": [{"domain": "partner.example", "count": 2}],
        "attachments": [
            {
                "filename": "nabidka.pdf",
                "content_type": "application/pdf",
                "size_bytes": 1234,
                "part_id": "2",
                "disposition": "attachment",
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
