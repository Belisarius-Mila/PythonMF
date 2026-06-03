from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.backup.run_tools import run_project_backup_text


class BackupRunToolsTests(unittest.TestCase):
    def test_execute_requires_mounted_target_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            script = Path(temp_dir) / "backup_samantha.command"
            script.write_text("#!/bin/zsh\nexit 0\n", encoding="utf-8")

            result = run_project_backup_text(
                mode="execute",
                profile="safe",
                target=str(Path(temp_dir) / "missing" / "SamanthaBackups"),
                script_path=script,
            )

            self.assertIn("neni pripojeny cilovy svazek", result)

    def test_recovery_rejects_non_secure_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            script = Path(temp_dir) / "backup_samantha.command"
            script.write_text("#!/bin/zsh\nexit 0\n", encoding="utf-8")

            result = run_project_backup_text(
                mode="execute",
                profile="recovery",
                target=str(Path(temp_dir) / "SamanthaBackups"),
                script_path=script,
            )

            self.assertIn("recovery profil", result)
            self.assertIn("SamanthaSecureBackup", result)

    def test_dry_run_calls_script_and_returns_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SamanthaBackups"
            root.mkdir()
            script = Path(temp_dir) / "backup_samantha.command"
            script.write_text(
                "#!/bin/zsh\n"
                "printf 'fake backup mode=%s profile=%s target=%s\\n' \"$1\" \"$3\" \"$5\"\n",
                encoding="utf-8",
            )
            script.chmod(0o755)

            result = run_project_backup_text(
                mode="dry-run",
                profile="safe",
                target=str(root),
                script_path=script,
            )

            self.assertIn("Dry-run zalohy dokoncen", result)
            self.assertIn("fake backup mode=--dry-run profile=safe", result)

    def test_python_backup_script_runs_through_python_bin(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SamanthaBackups"
            root.mkdir()
            script = Path(temp_dir) / "backup_samantha_python.py"
            script.write_text(
                "import sys\n"
                "print('python backup argv=' + ' '.join(sys.argv[1:]))\n",
                encoding="utf-8",
            )

            result = run_project_backup_text(
                mode="dry-run",
                profile="safe",
                target=str(root),
                script_path=script,
                python_bin=Path(__import__("sys").executable),
            )

            self.assertIn("Dry-run zalohy dokoncen", result)
            self.assertIn("python backup argv=--dry-run --profile safe", result)


if __name__ == "__main__":
    unittest.main()
