from __future__ import annotations

import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
VOCABULARY_DIR = ROOT / "VocabularyFR"
if str(VOCABULARY_DIR) not in sys.path:
    sys.path.insert(0, str(VOCABULARY_DIR))

from vocabulary_csv_store import (  # noqa: E402
    VOCABULARY_FIELDNAMES,
    VocabularyCsvConflictError,
    read_csv_document,
    save_csv_atomic,
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


trainer = load_module(
    "vocabularyfr_safe_csv_runtime",
    VOCABULARY_DIR / "vocab_trainer_fr.py",
)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class VocabularyCsvStoreTests(unittest.TestCase):
    def test_atomic_save_creates_verified_backup_and_updates_snapshot(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "VocabularyFR.csv"
            backup_dir = root / "backups"
            write_csv(csv_path, ["FR", "CZ"], [{"FR": "bonjour", "CZ": "ahoj"}])
            original = csv_path.read_bytes()
            document = read_csv_document(csv_path)

            result = save_csv_atomic(
                csv_path,
                [{"FR": "salut", "CZ": "nazdar"}],
                fieldnames=document.fieldnames,
                expected_snapshot=document.snapshot,
                backup_dir=backup_dir,
                create_backup=True,
            )

            self.assertIsNotNone(result.backup_path)
            self.assertEqual(result.backup_path.read_bytes(), original)
            self.assertEqual(result.snapshot, read_csv_document(csv_path).snapshot)
            self.assertEqual(read_csv_document(csv_path).rows[0]["FR"], "salut")

    def test_external_change_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "VocabularyFR.csv"
            backup_dir = root / "backups"
            write_csv(csv_path, ["FR", "CZ"], [{"FR": "un", "CZ": "jedna"}])
            document = read_csv_document(csv_path)
            write_csv(csv_path, ["FR", "CZ"], [{"FR": "deux", "CZ": "dva"}])
            external_content = csv_path.read_bytes()

            with self.assertRaises(VocabularyCsvConflictError):
                save_csv_atomic(
                    csv_path,
                    [{"FR": "trois", "CZ": "tři"}],
                    fieldnames=document.fieldnames,
                    expected_snapshot=document.snapshot,
                    backup_dir=backup_dir,
                    create_backup=True,
                )

            self.assertEqual(csv_path.read_bytes(), external_content)
            self.assertFalse(backup_dir.exists())

    def test_empty_rows_are_saved_as_valid_header_only_csv(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            csv_path = Path(temp_dir) / "VocabularyFR.csv"
            write_csv(csv_path, list(VOCABULARY_FIELDNAMES), [{"FR": "fin"}])
            document = read_csv_document(csv_path)

            save_csv_atomic(
                csv_path,
                [],
                fieldnames=document.fieldnames,
                expected_snapshot=document.snapshot,
            )

            saved = read_csv_document(csv_path)
            self.assertEqual(saved.fieldnames, VOCABULARY_FIELDNAMES)
            self.assertEqual(saved.rows, ())

    def test_trainer_preserves_unknown_columns_and_only_backs_up_once_per_session(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "VocabularyFR.csv"
            backup_dir = root / "backups"
            fieldnames = [*VOCABULARY_FIELDNAMES, "FutureColumn"]
            write_csv(
                csv_path,
                fieldnames,
                [
                    {
                        "FR": "bonjour",
                        "CZ": "ahoj",
                        "Order": "7",
                        "Sentence": "Bonjour, Jana.",
                        "SentenceT": "Ahoj, Jano.",
                        "L": "ne",
                        "HT": "ne",
                        "gender_fr": "",
                        "FutureColumn": "keep-me",
                    }
                ],
            )

            app = trainer.VocabularyTrainerApp.__new__(trainer.VocabularyTrainerApp)
            app.csv_path = str(csv_path)
            app.csv_fieldnames = tuple(VOCABULARY_FIELDNAMES)
            app.csv_snapshot = None
            app.csv_session_backup_created = False
            app.csv_write_blocked_reason = ""
            app.csv_backup_dir = str(backup_dir)
            app.rows = app._load_csv()

            self.assertEqual(app.rows[0]["FutureColumn"], "keep-me")
            app.rows[0]["CZ"] = "dobrý den"
            app._write_rows(app.rows)
            app.rows[0]["CZ"] = "nazdar"
            app._write_rows(app.rows)

            saved = read_csv_document(csv_path)
            self.assertEqual(saved.rows[0]["FutureColumn"], "keep-me")
            self.assertEqual(saved.rows[0]["CZ"], "nazdar")
            self.assertEqual(len(list(backup_dir.glob("*.csv"))), 1)

    def test_trainer_blocks_further_saves_after_external_conflict(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "VocabularyFR.csv"
            write_csv(csv_path, ["FR", "CZ"], [{"FR": "un", "CZ": "jedna"}])

            app = trainer.VocabularyTrainerApp.__new__(trainer.VocabularyTrainerApp)
            app.csv_path = str(csv_path)
            app.csv_fieldnames = tuple(VOCABULARY_FIELDNAMES)
            app.csv_snapshot = None
            app.csv_session_backup_created = False
            app.csv_write_blocked_reason = ""
            app.csv_backup_dir = str(root / "backups")
            app.rows = app._load_csv()
            write_csv(csv_path, ["FR", "CZ"], [{"FR": "deux", "CZ": "dva"}])

            with patch.object(trainer.messagebox, "showerror") as showerror:
                self.assertFalse(app._save_csv())
                self.assertFalse(app._save_csv())

            self.assertEqual(showerror.call_count, 1)
            self.assertTrue(app.csv_write_blocked_reason)
            self.assertEqual(read_csv_document(csv_path).rows[0]["FR"], "deux")


if __name__ == "__main__":
    unittest.main()
