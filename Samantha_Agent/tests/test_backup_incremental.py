from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.backup.incremental import run_backup


class BackupIncrementalTests(unittest.TestCase):
    def test_execute_skips_venv_globs_and_uses_completed_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "PythonMF"
            backup_root = root / "backup"
            home = root / "home"
            source.mkdir()
            (source / "Samantha_Agent").mkdir()
            (source / "Samantha_Agent" / ".venv_f5tts2").mkdir()
            (source / "Samantha_Agent" / ".venv_f5tts2" / "ignored.py").write_text("skip\n", encoding="utf-8")
            keep = source / "Samantha_Agent" / "keep.txt"
            keep.write_text("keep\n", encoding="utf-8")

            incomplete = backup_root / "snapshots" / "20260603_120000"
            incomplete.mkdir(parents=True)
            previous = backup_root / "snapshots" / "20260602_120000"
            previous_file = previous / "PythonMF" / "Samantha_Agent" / "keep.txt"
            previous_file.parent.mkdir(parents=True)
            previous_file.write_text("keep\n", encoding="utf-8")
            os.utime(previous_file, (keep.stat().st_atime, keep.stat().st_mtime))
            (previous / "backup_manifest.txt").write_text("complete\n", encoding="utf-8")

            with (
                patch("app.backup.incremental.Path.home", return_value=home),
                patch("app.backup.incremental.record_backup_completed"),
            ):
                output = run_backup(
                    mode="execute",
                    profile="safe",
                    backup_root=backup_root,
                    source_root=source,
                    timestamp="20260603_130000",
                    progress_every=0,
                )

            snapshot = backup_root / "snapshots" / "20260603_130000"
            copied = snapshot / "PythonMF" / "Samantha_Agent" / "keep.txt"
            ignored = snapshot / "PythonMF" / "Samantha_Agent" / ".venv_f5tts2" / "ignored.py"

            self.assertIn("Previous snapshot: " + str(previous), output)
            self.assertTrue((snapshot / "backup_manifest.txt").exists())
            self.assertTrue(copied.exists())
            self.assertFalse(ignored.exists())
            self.assertEqual(copied.stat().st_ino, previous_file.stat().st_ino)

    def test_dry_run_does_not_create_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "PythonMF"
            backup_root = root / "backup"
            home = root / "home"
            source.mkdir()
            (source / "file.txt").write_text("x\n", encoding="utf-8")

            with patch("app.backup.incremental.Path.home", return_value=home):
                output = run_backup(
                    mode="dry-run",
                    profile="safe",
                    backup_root=backup_root,
                    source_root=source,
                    timestamp="20260603_130000",
                    progress_every=0,
                )

            self.assertIn("Dry-run hotov", output)
            self.assertFalse((backup_root / "snapshots").exists())


if __name__ == "__main__":
    unittest.main()
