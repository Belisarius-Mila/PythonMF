from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


installer = load_module(
    "vocabularyfr_jana_remote_installer",
    ROOT / "VocabularyFR" / "install_jana_remote.py",
)
trainer = load_module(
    "vocabularyfr_runtime_paths",
    ROOT / "VocabularyFR" / "vocab_trainer_fr.py",
)


class VocabularyFRRuntimePathTests(unittest.TestCase):
    def test_explicit_runtime_paths_are_used_without_changing_defaults(self) -> None:
        self.assertEqual(
            trainer.resolve_csv_path("~/JanaData"),
            str(Path("~/JanaData").expanduser().resolve() / "VocabularyFR.csv"),
        )
        arguments = trainer.parse_runtime_arguments(
            ["--data-dir", "/tmp/data", "--pict-dir", "/tmp/pict"]
        )
        self.assertEqual(arguments.data_dir, "/tmp/data")
        self.assertEqual(arguments.pict_dir, "/tmp/pict")

        app = trainer.VocabularyTrainerApp.__new__(trainer.VocabularyTrainerApp)
        app.csv_path = "/tmp/data/VocabularyFR.csv"
        app.pict_dir = "/tmp/pict"
        self.assertEqual(app._build_picture_base_dirs()[0], "/tmp/pict")


class VocabularyFRJanaInstallTests(unittest.TestCase):
    def test_preview_is_redacted_validated_and_write_free(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = self._prepare(Path(temp_dir))
            plan = self._plan(paths)
            document = plan.safe_document()

            self.assertEqual(document["status"], "preview")
            self.assertEqual(document["vocabulary_rows"], 2)
            self.assertEqual(document["complete_sentence_pairs"], 2)
            self.assertEqual(document["picture_files"], 1)
            self.assertEqual(document["picture_mapping_missing_images"], 0)
            self.assertTrue(document["create_only"])
            self.assertFalse(document["writes_performed"])
            self.assertEqual(document["required_confirmation"], installer.INSTALL_CONFIRMATION)
            self.assertEqual(len(document["plan_fingerprint"]), 64)
            self.assertNotIn(temp_dir, json.dumps(document))
            self.assertNotIn("jana-test", json.dumps(document))
            self.assertNotIn(temp_dir, repr(plan))
            self.assertFalse(paths["shared_root"].exists())
            self.assertFalse(paths["data_dir"].exists())
            self.assertFalse(paths["launcher"].exists())

    def test_apply_is_create_only_and_uses_separate_data_and_picture_paths(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = self._prepare(Path(temp_dir))
            plan = self._plan(paths)
            result = installer.apply_vocabularyfr_install(
                plan,
                confirmation=installer.INSTALL_CONFIRMATION,
                expected_fingerprint=plan.fingerprint,
            )

            self.assertEqual(result.safe_document()["status"], "installed")
            self.assertEqual(
                (paths["data_dir"] / "VocabularyFR.csv").read_bytes(),
                paths["vocabulary_csv"].read_bytes(),
            )
            self.assertTrue((paths["shared_root"] / "Pict" / "a.png").is_file())
            self.assertEqual(
                (paths["shared_root"] / "app" / "vocabulary_csv_store.py").read_bytes(),
                paths["csv_store"].read_bytes(),
            )
            launcher = paths["launcher"].read_text(encoding="utf-8")
            self.assertIn("--data-dir", launcher)
            self.assertIn(str(paths["data_dir"]), launcher)
            self.assertIn("--pict-dir", launcher)
            self.assertIn(str(paths["shared_root"] / "Pict"), launcher)
            self.assertEqual(
                stat.S_IMODE((paths["data_dir"] / "VocabularyFR.csv").stat().st_mode),
                0o600,
            )
            self.assertEqual(stat.S_IMODE(paths["launcher"].stat().st_mode), 0o700)
            self.assertEqual(
                stat.S_IMODE((paths["shared_root"] / "Pict" / "a.png").stat().st_mode),
                0o644,
            )

    def test_wrong_confirmation_or_fingerprint_writes_nothing(self) -> None:
        for confirmation, fingerprint in (
            ("yes", None),
            (installer.INSTALL_CONFIRMATION, "0" * 64),
        ):
            with self.subTest(confirmation=confirmation, fingerprint=fingerprint):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    paths = self._prepare(Path(temp_dir))
                    plan = self._plan(paths)
                    with self.assertRaises(installer.VocabularyFRInstallError):
                        installer.apply_vocabularyfr_install(
                            plan,
                            confirmation=confirmation,
                            expected_fingerprint=fingerprint or plan.fingerprint,
                        )
                    self.assertFalse(paths["shared_root"].exists())
                    self.assertFalse(paths["data_dir"].exists())
                    self.assertFalse(paths["launcher"].exists())

    def test_changed_source_after_preview_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = self._prepare(Path(temp_dir))
            plan = self._plan(paths)
            paths["trainer"].write_text("# changed\n", encoding="utf-8")

            with self.assertRaisesRegex(
                installer.VocabularyFRInstallError,
                "changed",
            ):
                installer.apply_vocabularyfr_install(
                    plan,
                    confirmation=installer.INSTALL_CONFIRMATION,
                    expected_fingerprint=plan.fingerprint,
                )
            self.assertFalse(paths["shared_root"].exists())
            self.assertFalse(paths["data_dir"].exists())

    def test_incomplete_jana_sentences_or_existing_target_fail_closed(self) -> None:
        for case in ("sentences", "target"):
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    paths = self._prepare(Path(temp_dir))
                    if case == "sentences":
                        self._write_vocabulary(paths["vocabulary_csv"], sentence_t="")
                    else:
                        paths["shared_root"].mkdir()
                    with self.assertRaises(installer.VocabularyFRInstallError):
                        self._plan(paths)
                    self.assertFalse(paths["data_dir"].exists())
                    self.assertFalse(paths["launcher"].exists())

    def test_missing_mapped_image_is_reported_without_exposing_word_data(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = self._prepare(Path(temp_dir))
            (paths["pict_dir"] / "mapping.json").write_text(
                json.dumps({"private-word": "missing-image"}),
                encoding="utf-8",
            )
            document = self._plan(paths).safe_document()

            self.assertEqual(document["picture_mapping_missing_images"], 1)
            self.assertNotIn("private-word", json.dumps(document))
            self.assertNotIn("missing-image", json.dumps(document))

    def test_cli_failure_is_redacted(self) -> None:
        output = io.StringIO()
        with patch.object(installer.pwd, "getpwnam", side_effect=KeyError):
            exit_code = installer.main(
                [
                    "--jana-user",
                    "private-account-name",
                    "--source-csv",
                    "/private/source/path.csv",
                ],
                output=output,
            )

        document = json.loads(output.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertEqual(document["status"], "failed")
        self.assertFalse(document["writes_performed"])
        self.assertNotIn("private-account-name", output.getvalue())
        self.assertNotIn("/private/source/path.csv", output.getvalue())

    def _prepare(self, root: Path) -> dict[str, Path]:
        sources = root / "sources"
        pict_dir = sources / "Pict"
        home = root / "Users" / "jana"
        shared_parent = root / "Shared"
        sources.mkdir()
        pict_dir.mkdir()
        home.mkdir(parents=True)
        shared_parent.mkdir()

        python = sources / "python3"
        python.write_text("#!/bin/sh\n", encoding="utf-8")
        python.chmod(0o755)
        trainer_path = sources / "vocab_trainer_fr.py"
        trainer_path.write_text("# trainer\n", encoding="utf-8")
        csv_store = sources / "vocabulary_csv_store.py"
        csv_store.write_text("# CSV store\n", encoding="utf-8")
        vocabulary_csv = sources / "current.csv"
        self._write_vocabulary(vocabulary_csv)
        verbe_csv = sources / "VerbeFR.csv"
        self._write_csv(verbe_csv, ["InfFR", "InfCZ"], [["être", "být"]])
        pict_csv = sources / "FR_Pict.csv"
        self._write_csv(pict_csv, ["FRP", "CZP", "ENP"], [["un", "jeden", "one"]])
        male_fox = sources / "MaleFox.PNG"
        female_fox = sources / "FemaleFox.PNG"
        male_fox.write_bytes(b"male")
        female_fox.write_bytes(b"female")
        (pict_dir / "a.png").write_bytes(b"image")
        (pict_dir / "mapping.json").write_text(
            json.dumps({"jeden": "a"}),
            encoding="utf-8",
        )
        return {
            "home": home,
            "shared_root": shared_parent / "VocabularyFR",
            "data_dir": home / "Library" / "Application Support" / "VocabularyFR",
            "launcher": home / "Desktop" / "VocabularyFR.command",
            "python": python,
            "trainer": trainer_path,
            "csv_store": csv_store,
            "vocabulary_csv": vocabulary_csv,
            "verbe_csv": verbe_csv,
            "pict_csv": pict_csv,
            "male_fox": male_fox,
            "female_fox": female_fox,
            "pict_dir": pict_dir,
        }

    def _plan(self, paths: dict[str, Path]):
        uid = max(os.getuid(), 1)
        gid = max(os.getgid(), 0)
        return installer.plan_vocabularyfr_install(
            account_name="jana-test",
            account_uid=uid,
            account_gid=gid,
            jana_home=paths["home"],
            shared_root=paths["shared_root"],
            python_path=paths["python"],
            sources=installer.InstallSources(
                trainer=paths["trainer"],
                csv_store=paths["csv_store"],
                vocabulary_csv=paths["vocabulary_csv"],
                verbe_csv=paths["verbe_csv"],
                pict_csv=paths["pict_csv"],
                male_fox=paths["male_fox"],
                female_fox=paths["female_fox"],
                pict_dir=paths["pict_dir"],
            ),
        )

    def _write_vocabulary(self, path: Path, *, sentence_t: str = "Překlad.") -> None:
        fieldnames = ["FR", "CZ", "Order", "Sentence", "SentenceT", "L", "HT", "gender_fr"]
        rows = [
            ["un", "jeden", "1", "Une phrase.", sentence_t, "ne", "ne", "m"],
            ["deux", "dva", "2", "Deux phrases.", sentence_t, "ne", "ne", ""],
        ]
        self._write_csv(path, fieldnames, rows)

    @staticmethod
    def _write_csv(path: Path, fieldnames: list[str], rows: list[list[str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(fieldnames)
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
