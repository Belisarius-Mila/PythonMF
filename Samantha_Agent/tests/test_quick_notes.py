from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from app.file_persistence import lock_path_for
from app.quick_notes import (
    classify_quick_note_text,
    list_quick_notes_text,
    quick_notes_action_status_text,
    show_quick_note_detail_text,
    sync_quick_notes_index,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class QuickNotesTests(unittest.TestCase):
    def test_list_assigns_stable_numbers_and_safe_snippets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inbox = root / "Samantha Inbox"
            inbox.mkdir()
            index_path = root / "private" / "index.json"
            note = inbox / "samantha_note_2026-05-23_22-30-00.md"
            note.write_text(
                "# Samantha inbox\n\nDatum: 2026-05-23 22:30:00\n\nPoznámka:\nZ poznámky udělat tool.\n",
                encoding="utf-8",
            )

            first = list_quick_notes_text(inbox_dir=inbox, index_path=index_path)
            second = list_quick_notes_text(inbox_dir=inbox, index_path=index_path)

            self.assertIn("1. [inbox] 2026-05-23 22:30:00 - Z poznámky udělat tool.", first)
            self.assertIn("show_quick_note_detail(note_number=1)", first)
            self.assertIn("1. [inbox]", second)
            data = json.loads(index_path.read_text(encoding="utf-8"))
            self.assertEqual(data["notes"][0]["note_number"], 1)
            self.assertTrue(lock_path_for(index_path).exists())

    def test_detail_returns_full_note_for_number(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inbox = root / "Samantha Inbox"
            inbox.mkdir()
            index_path = root / "private" / "index.json"
            (inbox / "note.md").write_text(
                "# Samantha inbox\n\nDatum: 2026-05-23 22:31:00\n\nPoznamka:\nDetail textu.\n",
                encoding="utf-8",
            )

            sync_quick_notes_index(inbox_dir=inbox, index_path=index_path)
            detail = show_quick_note_detail_text(note_number=1, inbox_dir=inbox, index_path=index_path)

            self.assertIn("Samantha quick note #1", detail)
            self.assertIn("Detail textu.", detail)
            self.assertIn(str(inbox / "note.md"), detail)

    def test_missing_inbox_is_readable_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            text = list_quick_notes_text(
                inbox_dir=root / "missing",
                index_path=root / "private" / "index.json",
            )

            self.assertIn("zatim neexistuje", text)

    def test_rule_based_preclassification_detects_candidates(self) -> None:
        reminder = classify_quick_note_text("Připomeň mi v pondělí zavolat do servisu.")
        tool = classify_quick_note_text("Udělat nový report pro Quick Notes v Cockpitu.")
        sensitive = classify_quick_note_text("Pošli e-mail a smaž staré PDF.")

        self.assertEqual(reminder.kind, "reminder_candidate")
        self.assertEqual(reminder.confidence, "high")
        self.assertEqual(tool.kind, "tool_candidate")
        self.assertEqual(sensitive.kind, "sensitive_action")
        self.assertTrue(sensitive.sensitive)
        self.assertEqual(sensitive.risk, "high")

    def test_action_status_shows_preclassified_notes_without_source_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inbox = root / "Samantha Inbox"
            inbox.mkdir()
            index_path = root / "private" / "index.json"
            (inbox / "reminder.md").write_text(
                "# Samantha inbox\n\nDatum: 2026-06-19 08:00:00\n\nPoznámka:\nPřipomeň mi zítra zavolat do servisu.\n",
                encoding="utf-8",
            )
            (inbox / "sensitive.md").write_text(
                "# Samantha inbox\n\nDatum: 2026-06-19 08:05:00\n\nPoznámka:\nSmaž staré PDF ze složky Downloads.\n",
                encoding="utf-8",
            )

            text = quick_notes_action_status_text(inbox_dir=inbox, index_path=index_path)

            self.assertIn("Quick Notes akční inbox", text)
            self.assertIn("QN #2 - citlivá akce", text)
            self.assertIn("Riziko: high", text)
            self.assertIn("QN #1 - připomínka", text)
            self.assertNotIn(str(inbox), text.split("QN #2", 1)[1])

    def test_two_processes_merge_quick_notes_with_unique_stable_numbers(self) -> None:
        script = """
import sys
import time
from pathlib import Path
from app.quick_notes import sync_quick_notes_index

inbox = Path(sys.argv[1])
index_path = Path(sys.argv[2])
start_path = Path(sys.argv[3])
while not start_path.exists():
    time.sleep(0.01)
sync_quick_notes_index(inbox_dir=inbox, index_path=index_path)
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inboxes = (root / "inbox-a", root / "inbox-b")
            for worker, inbox in zip(("a", "b"), inboxes, strict=True):
                inbox.mkdir()
                for index in range(20):
                    (inbox / f"note-{worker}-{index:02d}.md").write_text(
                        "# Samantha inbox\n\n"
                        f"Datum: 2026-07-10 12:{index:02d}:00\n\n"
                        f"Poznámka:\nBezpečná poznámka {worker}-{index}.\n",
                        encoding="utf-8",
                    )
            index_path = root / "private" / "quick_notes" / "index.json"
            start_path = root / "start"
            processes = [
                subprocess.Popen(
                    [sys.executable, "-c", script, str(inbox), str(index_path), str(start_path)],
                    cwd=PROJECT_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for inbox in inboxes
            ]
            start_path.write_text("start\n", encoding="utf-8")
            outputs = [process.communicate(timeout=20) for process in processes]
            for process, (_stdout, stderr) in zip(processes, outputs, strict=True):
                self.assertEqual(process.returncode, 0, stderr)
            records = json.loads(index_path.read_text(encoding="utf-8"))["notes"]

        self.assertEqual(len(records), 40)
        self.assertEqual({item["note_number"] for item in records}, set(range(1, 41)))
        self.assertEqual(len({item["source_path"] for item in records}), 40)


if __name__ == "__main__":
    unittest.main()
