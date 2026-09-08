from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "VocabularyFR"))
from jana_launcher import portable_arguments  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "jana_bundle_builder", ROOT / "Samantha_Agent/scripts/build_jana_vocabularyfr_bundle.py"
)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class JanaBundleTests(unittest.TestCase):
    def test_portable_app_selects_only_its_adjacent_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "Janin slovník"
            folder.mkdir()
            for name in builder.DATA:
                (folder / name).write_text("data")
            exe = folder / "VocabularyFR.app/Contents/MacOS/VocabularyFR"
            self.assertEqual(portable_arguments(exe, []), ["--data-dir", str(folder)])

    def test_missing_data_does_not_create_or_migrate_anything(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            with self.assertRaisesRegex(ValueError, "Chybí"):
                portable_arguments(folder / "VocabularyFR.app/Contents/MacOS/VocabularyFR", [])
            self.assertEqual(list(folder.iterdir()), [])

    def test_explicit_data_dir_remains_explicit(self):
        for args in (["--data-dir", "/tmp/test data"], ["--data-dir=/tmp/test data"]):
            self.assertEqual(portable_arguments("/unused", args), args)

    def test_symlink_data_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for name in builder.DATA:
                (folder / name).symlink_to(sys.executable)
            with self.assertRaisesRegex(ValueError, "Chybí"):
                portable_arguments(folder / "VocabularyFR.app/Contents/MacOS/VocabularyFR", [])

    def test_build_refuses_existing_output_without_changing_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            marker = folder / "keep.txt"
            marker.write_text("original")
            with self.assertRaisesRegex(ValueError, "existuje"):
                builder.validate_request({"input_dir": tmp, "output_dir": tmp, "python": sys.executable})
            self.assertEqual(marker.read_text(), "original")

    def test_build_refuses_incomplete_sentences_before_creating_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for name in builder.DATA:
                (folder / name).write_text("FR,CZ,Sentence,SentenceT\nbonjour,ahoj,,\n")
            with self.assertRaisesRegex(ValueError, "věty"):
                builder.validate_request({"input_dir": tmp, "output_dir": str(folder / "new"),
                                          "python": sys.executable})
            self.assertFalse((folder / "new").exists())


if __name__ == "__main__":
    unittest.main()
