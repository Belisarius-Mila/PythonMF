from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.knowledge_inbox import (
    ensure_knowledge_inbox_dirs,
    format_knowledge_inbox_inventory,
    knowledge_inbox_inventory,
)


class KnowledgeInboxTests(unittest.TestCase):
    def test_knowledge_inbox_inventory_lists_metadata_without_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            inbox_root = Path(temp_dir) / "knowledge_inbox"
            ensure_knowledge_inbox_dirs(inbox_root)
            (inbox_root / "incoming" / "archive.json").write_text("SECRET_CONTENT", encoding="utf-8")
            (inbox_root / "notes" / "local.txt").write_text("note", encoding="utf-8")

            items = knowledge_inbox_inventory(inbox_root=inbox_root)
            text = format_knowledge_inbox_inventory(inbox_root=inbox_root)

        self.assertEqual(len(items), 2)
        self.assertIn("archive.json", text)
        self.assertIn("local.txt", text)
        self.assertIn("Reads content: no", text)
        self.assertNotIn("SECRET_CONTENT", text)

    def test_knowledge_inbox_inventory_handles_empty_folders(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            inbox_root = Path(temp_dir) / "knowledge_inbox"
            ensure_knowledge_inbox_dirs(inbox_root)

            text = format_knowledge_inbox_inventory(inbox_root=inbox_root)

        self.assertIn("Files: 0", text)
        self.assertIn("| - | - | - | 0 B | - |", text)


if __name__ == "__main__":
    unittest.main()
