from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.iphone_shortcuts import (
    REQUEST_CONFIRMATION_PHRASE,
    format_iphone_shortcuts_status,
    prepare_iphone_shortcut_request,
)


class IPhoneShortcutsTests(unittest.TestCase):
    def test_status_is_read_only_and_reports_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            requests_dir = root / "requests"
            output_dir = root / "Shortcuts Playground"

            text = format_iphone_shortcuts_status(
                output_dir=output_dir,
                requests_dir=requests_dir,
                shortcuts_cli="/usr/bin/shortcuts",
                codex_cli="/usr/local/bin/codex",
                playground_paths=(root / "shortcuts-playground-plugin",),
            )

            self.assertIn("iPhone Shortcuts Playground Status", text)
            self.assertIn("Apple shortcuts CLI: yes", text)
            self.assertIn("Codex CLI: yes", text)
            self.assertIn("Shortcuts Playground plugin detected: yes", text)
            self.assertIn("Status is read-only", text)
            self.assertFalse(requests_dir.exists())

    def test_prepare_shortcut_request_preview_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            requests_dir = Path(temp_dir) / "requests"

            text = prepare_iphone_shortcut_request(
                name="Vecerni rezim",
                purpose="Zapni Soustredeni a ztlum displej.",
                requests_dir=requests_dir,
            )

            self.assertIn("preview only", text)
            self.assertIn(REQUEST_CONFIRMATION_PHRASE, text)
            self.assertIn("Vecerni rezim", text)
            self.assertFalse(requests_dir.exists())

    def test_prepare_shortcut_request_confirmed_writes_private_draft(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            requests_dir = Path(temp_dir) / "requests"

            text = prepare_iphone_shortcut_request(
                name="Večerní režim",
                purpose="Zapni Soustředění a ztlum displej.",
                details="Použij české popisky.",
                user_confirmed=True,
                confirmation_text=REQUEST_CONFIRMATION_PHRASE,
                requests_dir=requests_dir,
            )

            files = tuple(requests_dir.glob("*.md"))
            self.assertEqual(len(files), 1)
            saved = files[0].read_text(encoding="utf-8")
            self.assertIn("Status: request saved", text)
            self.assertIn("Večerní režim", saved)
            self.assertIn("Zapni Soustředění", saved)
            self.assertIn("Použij české popisky", saved)


if __name__ == "__main__":
    unittest.main()
