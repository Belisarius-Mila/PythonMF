from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.knowledge_inbox import (
    COPY_CONFIRMATION_PHRASE,
    copy_downloads_to_knowledge_inbox,
    downloads_inventory,
    ensure_knowledge_inbox_dirs,
    format_downloads_inventory,
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

    def test_downloads_inventory_lists_metadata_without_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            downloads_dir = Path(temp_dir) / "Downloads"
            downloads_dir.mkdir()
            (downloads_dir / "chat_export.json").write_text("SECRET_CONTENT", encoding="utf-8")
            (downloads_dir / "nested").mkdir()
            (downloads_dir / "nested" / "ignored.txt").write_text("ignored", encoding="utf-8")

            items = downloads_inventory(downloads_dir=downloads_dir)
            text = format_downloads_inventory(downloads_dir=downloads_dir)

        self.assertEqual(len(items), 1)
        self.assertIn("chat_export.json", text)
        self.assertIn("Reads content: no", text)
        self.assertIn("folders are omitted", text)
        self.assertNotIn("SECRET_CONTENT", text)
        self.assertNotIn("ignored.txt", text)

    def test_downloads_copy_preview_requires_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            downloads_dir = Path(temp_dir) / "Downloads"
            inbox_root = Path(temp_dir) / "knowledge_inbox"
            downloads_dir.mkdir()
            (downloads_dir / "archive.zip").write_bytes(b"private bytes")

            text = copy_downloads_to_knowledge_inbox(
                "archive.zip",
                downloads_dir=downloads_dir,
                inbox_root=inbox_root,
            )

            self.assertIn("preview only", text)
            self.assertIn(COPY_CONFIRMATION_PHRASE, text)
            self.assertFalse((inbox_root / "incoming").exists())
            self.assertFalse((inbox_root / "incoming" / "archive.zip").exists())

    def test_downloads_copy_confirmed_does_not_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            downloads_dir = Path(temp_dir) / "Downloads"
            inbox_root = Path(temp_dir) / "knowledge_inbox"
            downloads_dir.mkdir()
            ensure_knowledge_inbox_dirs(inbox_root)
            (downloads_dir / "archive.zip").write_bytes(b"new bytes")
            (inbox_root / "incoming" / "archive.zip").write_bytes(b"old bytes")

            text = copy_downloads_to_knowledge_inbox(
                "archive.zip",
                user_confirmed=True,
                confirmation_text=COPY_CONFIRMATION_PHRASE,
                downloads_dir=downloads_dir,
                inbox_root=inbox_root,
            )

            self.assertIn("Status: copied", text)
            self.assertEqual((inbox_root / "incoming" / "archive.zip").read_bytes(), b"old bytes")
            self.assertEqual((inbox_root / "incoming" / "archive_2.zip").read_bytes(), b"new bytes")

    def test_downloads_copy_rejects_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            downloads_dir = Path(temp_dir) / "Downloads"
            inbox_root = Path(temp_dir) / "knowledge_inbox"
            downloads_dir.mkdir()
            (Path(temp_dir) / "secret.txt").write_text("secret", encoding="utf-8")

            text = copy_downloads_to_knowledge_inbox(
                "../secret.txt",
                user_confirmed=True,
                confirmation_text=COPY_CONFIRMATION_PHRASE,
                downloads_dir=downloads_dir,
                inbox_root=inbox_root,
            )

            self.assertIn("Status: blocked", text)
            self.assertFalse((inbox_root / "incoming" / "secret.txt").exists())


if __name__ == "__main__":
    unittest.main()
