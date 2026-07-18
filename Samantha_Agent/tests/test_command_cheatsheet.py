from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.command_cheatsheet import load_command_cheatsheet


class CommandCheatsheetTests(unittest.TestCase):
    def test_project_cheatsheet_has_four_read_only_groups(self) -> None:
        result = load_command_cheatsheet()

        self.assertTrue(result["ok"])
        self.assertEqual(len(result["sections"]), 4)
        self.assertEqual(
            [section["title"] for section in result["sections"]],
            [
                "Adam a zachovaná terminálová relace",
                "Cockpit",
                "Git, záloha a diagnostika",
                "Co bez Adama raději nepoužívat",
            ],
        )
        commands = [
            item["command"]
            for section in result["sections"]
            for item in section["items"]
        ]
        self.assertIn("screen -d -r samantha_codex", commands)
        self.assertIn("git status --short --branch", commands)
        self.assertNotIn("`", "".join(commands))
        self.assertIn("nelze z Cockpitu spustit ani upravit", result["message"])

    def test_missing_or_unrecognized_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            missing = load_command_cheatsheet(root / "missing.md")
            empty_path = root / "empty.md"
            empty_path.write_text("# Bez tabulky\n", encoding="utf-8")
            empty = load_command_cheatsheet(empty_path)

        self.assertFalse(missing["ok"])
        self.assertEqual(missing["sections"], [])
        self.assertFalse(empty["ok"])
        self.assertEqual(empty["sections"], [])

    def test_loader_returns_text_not_html_actions(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "commands.md"
            path.write_text(
                "# Tahák\n\n## Skupina\n\n"
                "| Příkaz | Stručné vysvětlení |\n"
                "| --- | --- |\n"
                "| `<script>alert(1)</script>` | Jen text. |\n",
                encoding="utf-8",
            )

            result = load_command_cheatsheet(path)

        self.assertTrue(result["ok"])
        self.assertEqual(result["sections"][0]["items"][0]["command"], "<script>alert(1)</script>")
        self.assertNotIn("html", result)
        self.assertNotIn("action", result)


if __name__ == "__main__":
    unittest.main()
