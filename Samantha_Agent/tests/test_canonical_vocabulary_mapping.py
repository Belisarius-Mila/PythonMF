from __future__ import annotations

import csv
import importlib.util
import json
import re
import sys
import types
import unicodedata
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
MAPPING_PATH = ROOT / "Pict" / "mapping.json"
PICT_PATH = ROOT / "Pict"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def normalize_image_stem(text: str) -> str:
    value = (text or "").strip().casefold()
    value = "".join(
        char
        for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", "", value)


def alphabetic_key(text: str) -> tuple[str, str, str]:
    return normalize_image_stem(text), text.casefold(), text


def normalize_mapping_key(text: str) -> str:
    value = unicodedata.normalize("NFC", (text or "").strip().casefold())
    return "".join(char for char in value if char.isalnum())


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CanonicalVocabularyMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mapping = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
        cls.image_stems = {
            normalize_image_stem(path.stem)
            for path in PICT_PATH.iterdir()
            if path.is_file() and path.suffix.casefold() in IMAGE_EXTENSIONS
        }

    def test_mapping_is_alphabetical_and_has_required_semantic_repairs(self) -> None:
        keys = list(self.mapping)
        self.assertEqual(keys, sorted(keys, key=alphabetic_key))
        self.assertEqual(self.mapping["těší mě"], "meet")
        self.assertEqual(self.mapping["pocházím"], "fromwhere")
        self.assertEqual(self.mapping["byt"], "apartment")
        self.assertEqual(self.mapping["být"], "tobe")

    def test_mapping_values_have_local_picture_files(self) -> None:
        missing = sorted(
            {
                value
                for value in self.mapping.values()
                if normalize_image_stem(value) not in self.image_stems
            }
        )
        self.assertEqual(missing, [])

    def test_active_foreign_terms_are_not_mapping_keys(self) -> None:
        czech_terms: set[str] = set()
        foreign_terms: set[str] = set()
        sources = (
            (ROOT / "VocabularyFR.csv", "FR"),
            (ROOT / "VocabularyFR" / "VocabularyFR.csv", "FR"),
            (ROOT / "VocabularyIT" / "VocabularyIT.csv", "IT"),
        )
        for path, language in sources:
            with path.open(encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    foreign_terms.add(normalize_mapping_key(row.get(language, "")))
                    czech_terms.add(normalize_mapping_key(row.get("CZ", "")))
        mapping_keys = {normalize_mapping_key(key) for key in self.mapping}
        forbidden = (foreign_terms - czech_terms) & mapping_keys
        self.assertEqual(forbidden, set())

    def test_desktop_resolvers_distinguish_byt_and_byt_with_accent(self) -> None:
        for language, relative_path, source_column in (
            ("fr", Path("VocabularyFR/vocab_trainer_fr.py"), "FR"),
            ("it", Path("VocabularyIT/vocab_trainer_it.py"), "IT"),
        ):
            module = load_module(f"canonical_{language}_trainer", ROOT / relative_path)
            trainer = module.VocabularyTrainerApp.__new__(module.VocabularyTrainerApp)
            trainer.picture_stems = self.image_stems
            trainer.synonym_image_map = {}
            trainer.synonym_image_folded_map = {}
            trainer.blocked_image_terms = set()
            trainer._mapping_file_candidates = lambda: [str(MAPPING_PATH)]
            if language == "it":
                trainer._blocklist_file_candidates = lambda: []
            trainer._load_external_mapping()
            self.assertEqual(
                trainer._choose_picture_stem({source_column: "", "CZ": "byt"}),
                "apartment",
            )
            self.assertEqual(
                trainer._choose_picture_stem({source_column: "", "CZ": "být"}),
                "tobe",
            )

    def test_pythonista_resolvers_distinguish_byt_and_byt_with_accent(self) -> None:
        ui_module = types.ModuleType("ui")
        ui_module.View = type("View", (), {})
        speech_module = types.ModuleType("speech")
        sync_module = types.ModuleType("datafresh_sync")
        sync_module.refresh_files_from_icloud = lambda *args, **kwargs: None
        sync_module.DATAFRESH_API_VERSION = 2
        sync_module.datafresh_status_text = lambda *args, **kwargs: ""
        sync_module.refresh_result_succeeded = lambda *args, **kwargs: False
        modules = {
            "ui": ui_module,
            "speech": speech_module,
            "datafresh_sync": sync_module,
        }
        for index, relative_path in enumerate(
            (
                Path("MBSoft/AppFR.py"),
                Path("MBSoft/AppIT.py"),
                Path("MBSoft/JanaIphoneFR/AppFR.py"),
            )
        ):
            with patch.dict(sys.modules, modules):
                module = load_module(f"canonical_pythonista_{index}", ROOT / relative_path)
            trainer = module.VocabTrainer.__new__(module.VocabTrainer)
            trainer.image_folded_map = {}
            trainer.image_alias_map = {}
            trainer._picture_folders = lambda: [PICT_PATH]
            trainer.image_map = trainer._load_image_map()
            source_column = "IT" if relative_path.name == "AppIT.py" else "FR"
            self.assertEqual(
                trainer._image_base_name_for_word({source_column: "", "CZ": "byt"}),
                "apartment",
            )
            self.assertEqual(
                trainer._image_base_name_for_word({source_column: "", "CZ": "být"}),
                "tobe",
            )


if __name__ == "__main__":
    unittest.main()
