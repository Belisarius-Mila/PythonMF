from __future__ import annotations

import tempfile
import time
import unittest
import os
from pathlib import Path

from scripts.git_safety_check import StagedFile, check_staged, format_report, path_is_blocked
from scripts.system_quick_check import CheckLine, autosave_line, format_morning_sentence


class GitSafetyCheckTests(unittest.TestCase):
    def test_blocks_private_autosave_and_env_paths(self) -> None:
        self.assertEqual(path_is_blocked("Samantha_Agent/data/private/documents/index.json"), "data/private")
        self.assertEqual(path_is_blocked("Samantha_Agent/data/session_autosave/latest_info.txt"), "data/session_autosave")
        self.assertEqual(path_is_blocked("Samantha_Agent/.env"), "env file")

    def test_format_report_marks_clean_staged_set(self) -> None:
        report = format_report([StagedFile(status="M", path="Samantha_Agent/app/cockpit.py")], [], [])

        self.assertIn("staged files: 1", report)
        self.assertIn("no blocked", report)
        self.assertIn("no large", report)

    def test_check_staged_warns_for_binary_media(self) -> None:
        errors, warnings = check_staged(
            [StagedFile(status="A", path="docs/colors-numbers/owl.mp3")],
            large_file_bytes=5_000_000,
        )

        self.assertEqual(errors, [])
        self.assertIn("binary/media staged file: docs/colors-numbers/owl.mp3", warnings)


class SystemQuickCheckTests(unittest.TestCase):
    def test_format_morning_sentence_summarizes_ok_state(self) -> None:
        sentence = format_morning_sentence(
            [
                CheckLine("git", True, "clean"),
                CheckLine("backup", True, "ok"),
                CheckLine("cockpit", True, "ok"),
            ]
        )

        self.assertIn("Samantha je vzhůru", sentence)
        self.assertIn("git je čistý", sentence)

    def test_format_morning_sentence_lists_warnings(self) -> None:
        sentence = format_morning_sentence(
            [
                CheckLine("git", False, "dirty"),
                CheckLine("backup", True, "ok"),
                CheckLine("cockpit", True, "ok"),
            ]
        )

        self.assertIn("zkontrolovat: git", sentence)

    def test_autosave_line_reports_recent_file_ok(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "latest_info.txt"
            path.write_text("Saved at: test\n", encoding="utf-8")

            line = autosave_line(path=path, warn_minutes=20)

        self.assertTrue(line.ok)
        self.assertEqual(line.name, "autosave")

    def test_autosave_line_warns_for_stale_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "latest_info.txt"
            path.write_text("Saved at: old\n", encoding="utf-8")
            old = time.time() - 3600
            os.utime(path, (old, old))

            line = autosave_line(path=path, warn_minutes=20)

        self.assertFalse(line.ok)
        self.assertIn("warn > 20", line.message)


if __name__ == "__main__":
    unittest.main()
