from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PYTHONMF_ROOT = Path(__file__).resolve().parents[2]
SYNC_PATH = PYTHONMF_ROOT / "MBSoft" / "JanaIphoneFR" / "datafresh_sync.py"
APP_PATH = PYTHONMF_ROOT / "MBSoft" / "JanaIphoneFR" / "AppFR.py"

SPEC = importlib.util.spec_from_file_location("jana_datafresh_sync_under_test", SYNC_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Janin datafresh_sync.py nelze načíst pro test.")
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)


class JanaDataFreshSyncTests(unittest.TestCase):
    def test_fast_roots_include_dynamic_ios_file_provider(self) -> None:
        appgroup_root = "/private/var/mobile/Containers/Shared/AppGroup"
        group = f"{appgroup_root}/SYNTHETIC-GROUP"
        provider_root = f"{group}/File Provider Storage"
        provider = f"{provider_root}/iCloud"
        existing = {appgroup_root, group, provider_root, provider}

        def fake_listdir(path: str) -> list[str]:
            if path == appgroup_root:
                return ["SYNTHETIC-GROUP"]
            if path == provider_root:
                return ["iCloud"]
            return []

        with (
            patch.object(SYNC.os.path, "isdir", side_effect=lambda path: path in existing),
            patch.object(SYNC.os, "listdir", side_effect=fake_listdir),
        ):
            roots = SYNC._icloud_root_candidates(fast=True)

        self.assertIn(provider, roots)
        self.assertIn(f"{provider}/PythonMF", roots)

    def test_complete_canonical_csv_beats_stale_pinned_copy(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            local_dir = root / "app"
            local = local_dir / "VocabularyFR.csv"
            pinned = root / "old" / "PythonMF" / "VocabularyFR" / "VocabularyFR.csv"
            canonical = (
                root
                / "provider"
                / "PythonMF"
                / "VocabularyFR"
                / "VocabularyFR.csv"
            )
            self._write_vocab(local, 367)
            self._write_vocab(pinned, 367)
            self._write_vocab(canonical, 383)

            with patch.object(
                SYNC,
                "_find_source_file",
                return_value=(str(canonical), ["synthetic-provider"]),
            ):
                result = SYNC.refresh_files_from_icloud(
                    local_dir=str(local_dir),
                    filenames=["VocabularyFR.csv"],
                    app_dir_hints=("PythonMF/VocabularyFR",),
                    source_overrides={"VocabularyFR.csv": str(pinned)},
                    strict=True,
                    allow_recursive=False,
                    fast=True,
                    max_attempts=1,
                    required_csv_columns={"VocabularyFR.csv": ("FR", "CZ")},
                )

            loaded_rows = self._row_count(local)

        self.assertEqual(result["updated"], ["VocabularyFR.csv"])
        self.assertEqual(result["source_rows"]["VocabularyFR.csv"], 383)
        self.assertEqual(result["local_rows"]["VocabularyFR.csv"], 383)
        self.assertEqual(result["ignored_overrides"], ["VocabularyFR.csv"])
        self.assertEqual(loaded_rows, 383)
        self.assertEqual(
            SYNC.datafresh_status_text(result, "VocabularyFR.csv", loaded_rows),
            "✓ Aktualizovano: 383 slovicek (zdroj 383)",
        )

    def test_fast_exact_lookup_finds_csv_inside_provider_root(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            provider = Path(temp_dir) / "File Provider Storage" / "iCloud"
            source = (
                provider
                / "PythonMF"
                / "VocabularyFR"
                / "VocabularyFR.csv"
            )
            self._write_vocab(source, 383)
            with patch.object(
                SYNC,
                "_icloud_root_candidates",
                return_value=[str(provider)],
            ):
                found, roots = SYNC._find_source_file(
                    "VocabularyFR.csv",
                    ("PythonMF/VocabularyFR",),
                    local_dir=str(Path(temp_dir) / "app"),
                    strict=True,
                    allow_recursive=False,
                    fast=True,
                )

        self.assertEqual(found, str(source))
        self.assertEqual(roots, [str(provider)])

    def test_missing_source_keeps_local_rows_and_reports_failure(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            local_dir = Path(temp_dir) / "app"
            local = local_dir / "VocabularyFR.csv"
            self._write_vocab(local, 367)
            with patch.object(
                SYNC,
                "_find_source_file",
                return_value=(None, ["synthetic-provider"]),
            ):
                result = SYNC.refresh_files_from_icloud(
                    local_dir=str(local_dir),
                    filenames=["VocabularyFR.csv"],
                    app_dir_hints=("PythonMF/VocabularyFR",),
                    strict=True,
                    allow_recursive=False,
                    fast=True,
                    max_attempts=1,
                    required_csv_columns={"VocabularyFR.csv": ("FR", "CZ")},
                )

            status = SYNC.datafresh_status_text(
                result,
                "VocabularyFR.csv",
                self._row_count(local),
            )

        self.assertEqual(result["missing"], ["VocabularyFR.csv"])
        self.assertEqual(result["local_rows"]["VocabularyFR.csv"], 367)
        self.assertTrue(status.startswith("✗ DataFresh nenasel"))
        self.assertNotIn("Hotovo", status)

    def test_invalid_csv_does_not_overwrite_valid_local_copy(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            local_dir = root / "app"
            local = local_dir / "VocabularyFR.csv"
            source = root / "provider" / "VocabularyFR.csv"
            self._write_vocab(local, 367)
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("wrong,columns\nx,y\n", encoding="utf-8")
            before = local.read_bytes()

            with patch.object(
                SYNC,
                "_find_source_file",
                return_value=(str(source), ["synthetic-provider"]),
            ):
                result = SYNC.refresh_files_from_icloud(
                    local_dir=str(local_dir),
                    filenames=["VocabularyFR.csv"],
                    app_dir_hints=("PythonMF/VocabularyFR",),
                    strict=True,
                    allow_recursive=False,
                    fast=True,
                    max_attempts=1,
                    required_csv_columns={"VocabularyFR.csv": ("FR", "CZ")},
                )

            after = local.read_bytes()

        self.assertEqual(result["updated"], [])
        self.assertTrue(result["failed"])
        self.assertEqual(after, before)

    def test_identical_complete_csv_is_reported_as_current(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            local_dir = root / "app"
            local = local_dir / "VocabularyFR.csv"
            source = root / "provider" / "VocabularyFR.csv"
            self._write_vocab(local, 383)
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(local.read_bytes())

            with patch.object(
                SYNC,
                "_find_source_file",
                return_value=(str(source), ["synthetic-provider"]),
            ):
                result = SYNC.refresh_files_from_icloud(
                    local_dir=str(local_dir),
                    filenames=["VocabularyFR.csv"],
                    app_dir_hints=("PythonMF/VocabularyFR",),
                    strict=True,
                    allow_recursive=False,
                    fast=True,
                    max_attempts=1,
                    required_csv_columns={"VocabularyFR.csv": ("FR", "CZ")},
                )

        self.assertEqual(result["unchanged"], ["VocabularyFR.csv"])
        self.assertEqual(
            SYNC.datafresh_status_text(result, "VocabularyFR.csv", 383),
            "✓ Aktualni: 383 slovicek (zdroj 383)",
        )

    def test_appfr_uses_versioned_truthful_datafresh_contract(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")

        self.assertNotIn("MIN_EXPECTED_VOCAB_ROWS", source)
        self.assertIn("VOCAB_REQUIRED_COLUMNS = ('FR', 'CZ')", source)
        self.assertIn("required_csv_columns={", source)
        self.assertIn("datafresh_status_text(", source)
        self.assertIn("Nahraj spolu s AppFR.py také nový datafresh_sync.py.", source)
        self.assertIn("self._notify('DataFresh', self.lbl_stats.text)", source)
        self.assertNotIn("f'✓ {status}: {total} slovicek'", source)

    @staticmethod
    def _write_vocab(path: Path, rows: int) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "FR",
                    "CZ",
                    "Order",
                    "Sentence",
                    "SentenceT",
                    "L",
                    "HT",
                    "gender_fr",
                ],
            )
            writer.writeheader()
            for index in range(rows):
                writer.writerow(
                    {
                        "FR": f"mot-{index}",
                        "CZ": f"slovo-{index}",
                        "Order": index + 1,
                        "Sentence": "",
                        "SentenceT": "",
                        "L": "",
                        "HT": "",
                        "gender_fr": "",
                    }
                )

    @staticmethod
    def _row_count(path: Path) -> int:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return len(list(csv.DictReader(handle)))


if __name__ == "__main__":
    unittest.main()
