from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.quick_notes import list_quick_notes_text, show_quick_note_detail_text, sync_quick_notes_index


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


if __name__ == "__main__":
    unittest.main()
