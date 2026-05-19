from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.backup.restore_tools import (
    has_explicit_restore_confirmation,
    list_backup_snapshots_text,
    preview_backup_restore_text,
    restore_path_from_backup_text,
)


class BackupRestoreToolsTests(unittest.TestCase):
    def test_list_backup_snapshots_returns_safe_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SamanthaBackups"
            _write_snapshot(root, "20260519_120000", {"VocabularyFR/VocabularyFR.csv": "un\n"})

            result = list_backup_snapshots_text(backup_root=str(root))

            self.assertIn("20260519_120000", result)
            self.assertIn("profile=recovery", result)
            self.assertIn("nic neobnovuje", result)

    def test_preview_rejects_unsafe_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SamanthaBackups"
            _write_snapshot(root, "20260519_120000", {"safe.txt": "safe"})

            absolute = preview_backup_restore_text(
                "/Users/mila/Desktop/secret.txt",
                backup_root=str(root),
            )
            parent = preview_backup_restore_text("../secret.txt", backup_root=str(root))

            self.assertIn("relativni", absolute)
            self.assertIn("..", parent)

    def test_preview_reports_source_and_target_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SamanthaBackups"
            local_root = Path(temp_dir) / "PythonMF"
            _write_snapshot(root, "20260519_120000", {"VocabularyFR/VocabularyFR.csv": "backup\n"})
            (local_root / "VocabularyFR").mkdir(parents=True)
            (local_root / "VocabularyFR" / "VocabularyFR.csv").write_text(
                "current\n",
                encoding="utf-8",
            )

            result = preview_backup_restore_text(
                "VocabularyFR/VocabularyFR.csv",
                backup_root=str(root),
                local_root=local_root,
            )

            self.assertIn("Nahled obnovy", result)
            self.assertIn("zdroj existuje: ano", result)
            self.assertIn("cil existuje: ano", result)
            self.assertEqual(
                (local_root / "VocabularyFR" / "VocabularyFR.csv").read_text(encoding="utf-8"),
                "current\n",
            )

    def test_restore_requires_explicit_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SamanthaBackups"
            local_root = Path(temp_dir) / "PythonMF"
            _write_snapshot(root, "20260519_120000", {"VocabularyFR/VocabularyFR.csv": "backup\n"})

            result = restore_path_from_backup_text(
                "VocabularyFR/VocabularyFR.csv",
                backup_root=str(root),
                local_root=local_root,
                user_confirmed=False,
                confirmation_text="",
            )

            self.assertIn("Bez potvrzeni", result)
            self.assertFalse((local_root / "VocabularyFR" / "VocabularyFR.csv").exists())

    def test_restore_file_backs_up_existing_target_first(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SamanthaBackups"
            local_root = Path(temp_dir) / "PythonMF"
            _write_snapshot(root, "20260519_120000", {"VocabularyFR/VocabularyFR.csv": "backup\n"})
            target = local_root / "VocabularyFR" / "VocabularyFR.csv"
            target.parent.mkdir(parents=True)
            target.write_text("broken\n", encoding="utf-8")

            result = restore_path_from_backup_text(
                "VocabularyFR/VocabularyFR.csv",
                snapshot="20260519_120000",
                backup_root=str(root),
                local_root=local_root,
                user_confirmed=True,
                confirmation_text=(
                    "Potvrzuji obnovu VocabularyFR/VocabularyFR.csv "
                    "ze snapshotu 20260519_120000."
                ),
            )

            backups = list(target.parent.glob("VocabularyFR.csv.before_restore_*"))
            self.assertIn("Obnova ze zalohy dokoncena", result)
            self.assertEqual(target.read_text(encoding="utf-8"), "backup\n")
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), "broken\n")

    def test_restore_sensitive_path_requires_sensitive_confirmation_word(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SamanthaBackups"
            local_root = Path(temp_dir) / "PythonMF"
            _write_snapshot(root, "20260519_120000", {".env": "SECRET=value\n"})

            rejected = restore_path_from_backup_text(
                ".env",
                snapshot="latest",
                backup_root=str(root),
                local_root=local_root,
                user_confirmed=True,
                confirmation_text="Potvrzuji obnovu .env ze snapshotu latest.",
            )
            accepted = restore_path_from_backup_text(
                ".env",
                snapshot="latest",
                backup_root=str(root),
                local_root=local_root,
                user_confirmed=True,
                confirmation_text=(
                    "Potvrzuji obnovu .env ze snapshotu latest. "
                    "Potvrzuji citlive recovery."
                ),
            )

            self.assertIn("citlivou recovery", rejected)
            self.assertIn("Obnova ze zalohy dokoncena", accepted)
            self.assertEqual((local_root / ".env").read_text(encoding="utf-8"), "SECRET=value\n")

    def test_restore_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SamanthaBackups"
            local_root = Path(temp_dir) / "PythonMF"
            _write_snapshot(
                root,
                "20260519_120000",
                {
                    "VocabularyFR/VocabularyFR.csv": "backup\n",
                    "VocabularyFR/VerbeFR.csv": "verbs\n",
                },
            )

            result = restore_path_from_backup_text(
                "VocabularyFR",
                snapshot="latest",
                backup_root=str(root),
                local_root=local_root,
                user_confirmed=True,
                confirmation_text="Potvrzuji obnovu VocabularyFR ze snapshotu latest.",
            )

            self.assertIn("Obnova ze zalohy dokoncena", result)
            self.assertEqual(
                (local_root / "VocabularyFR" / "VocabularyFR.csv").read_text(encoding="utf-8"),
                "backup\n",
            )
            self.assertEqual(
                (local_root / "VocabularyFR" / "VerbeFR.csv").read_text(encoding="utf-8"),
                "verbs\n",
            )

    def test_confirmation_requires_path_snapshot_and_restore_words(self) -> None:
        self.assertFalse(
            has_explicit_restore_confirmation(
                "VocabularyFR/VocabularyFR.csv",
                "20260519_120000",
                "Potvrzuji soubor.",
            )
        )
        self.assertTrue(
            has_explicit_restore_confirmation(
                "VocabularyFR/VocabularyFR.csv",
                "20260519_120000",
                "Potvrzuji obnovu VocabularyFR/VocabularyFR.csv ze snapshotu 20260519_120000.",
            )
        )


def _write_snapshot(root: Path, snapshot_id: str, files: dict[str, str]) -> Path:
    snapshot = root / "snapshots" / snapshot_id
    pythonmf = snapshot / "PythonMF"
    pythonmf.mkdir(parents=True)
    (snapshot / "backup_manifest.txt").write_text(
        "Created at: Tue May 19 12:00:00 2026\n"
        "Profile: recovery\n"
        f"Target: {pythonmf}\n",
        encoding="utf-8",
    )
    for relative_path, text in files.items():
        path = pythonmf / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return snapshot


if __name__ == "__main__":
    unittest.main()
