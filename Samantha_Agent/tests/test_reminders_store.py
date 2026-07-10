from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.email.action_case_models import (
    ActionCaseAttachmentMeta,
    ActionCaseLinkDomain,
    ReminderDraft,
    ReminderSource,
)
from app.reminders.store import load_reminders_store, save_reminder_draft
from app.file_persistence import lock_path_for


PROJECT_ROOT = Path(__file__).resolve().parents[1]


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
            self.assertTrue(lock_path_for(path).exists())

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

            with patch("app.file_persistence.os.replace", side_effect=OSError("must not replace")):
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

    def test_two_processes_add_reminders_without_lost_updates(self) -> None:
        script = """
import sys
import time
from pathlib import Path
from app.reminders.store import save_reminder_draft

path = Path(sys.argv[1])
start_path = Path(sys.argv[2])
worker = sys.argv[3]
while not start_path.exists():
    time.sleep(0.01)
for index in range(20):
    reminder_id = f"{worker}-{index}"
    save_reminder_draft(
        {
            "id": reminder_id,
            "title": f"Bezpečný test {reminder_id}",
            "notes": "Bezpečné redigované poznámky.",
            "due_date": "2026-07-31",
            "priority": "low",
            "status": "open",
            "source": {"type": "test", "uid": reminder_id, "date": "2026-07-10", "sender": "redigováno"},
        },
        path=path,
    )
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            path = root / "reminders.json"
            start_path = root / "start"
            processes = [
                subprocess.Popen(
                    [sys.executable, "-c", script, str(path), str(start_path), worker],
                    cwd=PROJECT_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for worker in ("a", "b")
            ]
            start_path.write_text("start\n", encoding="utf-8")
            outputs = [process.communicate(timeout=20) for process in processes]
            for process, (_stdout, stderr) in zip(processes, outputs, strict=True):
                self.assertEqual(process.returncode, 0, stderr)
            store = load_reminders_store(path)

        self.assertEqual(len(store["reminders"]), 40)
        self.assertEqual(
            {item["id"] for item in store["reminders"]},
            {f"{worker}-{index}" for worker in ("a", "b") for index in range(20)},
        )

    def test_two_processes_create_same_reminder_exactly_once(self) -> None:
        script = """
import json
import sys
import time
from pathlib import Path
from app.reminders.store import save_reminder_draft

path = Path(sys.argv[1])
start_path = Path(sys.argv[2])
while not start_path.exists():
    time.sleep(0.01)
result = save_reminder_draft(
    {
        "id": "same-id",
        "title": "Bezpečný test",
        "notes": "Bezpečné redigované poznámky.",
        "due_date": "2026-07-31",
        "priority": "low",
        "status": "open",
        "source": {"type": "test", "uid": "same-id", "date": "2026-07-10", "sender": "redigováno"},
    },
    path=path,
)
print(json.dumps({"created": result.created}))
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            path = root / "reminders.json"
            start_path = root / "start"
            processes = [
                subprocess.Popen(
                    [sys.executable, "-c", script, str(path), str(start_path)],
                    cwd=PROJECT_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for _ in range(2)
            ]
            start_path.write_text("start\n", encoding="utf-8")
            outputs = [process.communicate(timeout=20) for process in processes]
            results = []
            for process, (stdout, stderr) in zip(processes, outputs, strict=True):
                self.assertEqual(process.returncode, 0, stderr)
                results.append(json.loads(stdout))
            store = load_reminders_store(path)

        self.assertEqual(sum(1 for result in results if result["created"]), 1)
        self.assertEqual([item["id"] for item in store["reminders"]], ["same-id"])


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
