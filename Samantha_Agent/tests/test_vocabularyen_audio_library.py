from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VOCABULARY_DIR = REPO_ROOT / "VocabularyEN"
if str(VOCABULARY_DIR) not in sys.path:
    sys.path.insert(0, str(VOCABULARY_DIR))
BUILDER_PATH = VOCABULARY_DIR / "build_vocabulary_en_audio.py"
SPEC = importlib.util.spec_from_file_location("vocabularyen_audio_library", BUILDER_PATH)
assert SPEC is not None and SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


class VocabularyEnAudioLibraryTests(unittest.TestCase):
    def test_selected_voices_and_spoken_text_normalization_are_canonical(self) -> None:
        self.assertEqual(builder.VOICES["en"]["id"], "en-US-AriaNeural")
        self.assertEqual(builder.VOICES["cz"]["id"], "cs-CZ-VlastaNeural")
        self.assertEqual(builder.RATE, "-10%")
        self.assertEqual(builder.normalize_spoken_text("a glass (of water)"), "a glass of water")
        self.assertEqual(
            builder.normalize_spoken_text("pravý, správný, doprava"),
            "pravý. správný. doprava",
        )

    def test_builder_generates_only_unique_missing_assets_and_verifies_coverage(self) -> None:
        items = [
            {"id": 1, "en": "hello", "cz": "ahoj"},
            {"id": 2, "en": "hello", "cz": "dobrý den, ahoj"},
        ]
        calls: list[tuple[str, str, str]] = []

        def fake_synthesize(text: str, *, voice: str, rate: str) -> bytes:
            calls.append((text, voice, rate))
            return b"ID3" + (f"{voice}|{rate}|{text}".encode("utf-8") * 80)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "data").mkdir()
            (root / "data" / "vocabulary-en.json").write_text(
                json.dumps({"items": items}), encoding="utf-8"
            )
            csv_path = root / "VocabularyEN.csv"
            csv_path.write_text(
                "EN,CZ,Order\nhello,ahoj,1\nhello,\"dobrý den, ahoj\",2\n",
                encoding="utf-8",
            )

            first = builder.build_library(root, synthesize=fake_synthesize, csv_path=csv_path)
            second = builder.build_library(root, synthesize=fake_synthesize, csv_path=csv_path)
            verified = builder.verify_library(root, csv_path)

            self.assertEqual(first["generated"], 3)
            self.assertEqual(first["assets"], 3)
            self.assertEqual(second["generated"], 0)
            self.assertEqual(second["skipped"], 3)
            self.assertEqual(len(calls), 3)
            self.assertEqual(verified, {"items": 2, "references": 4, "assets": 3})

    def test_builder_refuses_stale_web_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "data").mkdir()
            (root / "data" / "vocabulary-en.json").write_text(
                json.dumps({"items": [{"id": 1, "en": "wrong", "cz": "ahoj"}]}),
                encoding="utf-8",
            )
            csv_path = root / "VocabularyEN.csv"
            csv_path.write_text("EN,CZ,Order\nhello,ahoj,1\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Nejprve spusť"):
                builder.build_library(root, synthesize=lambda *_args, **_kwargs: b"", csv_path=csv_path)

    def test_production_web_uses_mp3_manifest_without_system_speech_fallback(self) -> None:
        html = (REPO_ROOT / "docs" / "vocabulary-en" / "index.html").read_text(encoding="utf-8")
        javascript = (REPO_ROOT / "docs" / "vocabulary-en" / "app.js").read_text(encoding="utf-8")

        self.assertIn("data-audio-url", html)
        self.assertIn("vocabulary-en-audio.json", javascript)
        self.assertIn("new Audio", javascript)
        self.assertNotIn("speechSynthesis", javascript)
        self.assertNotIn("SpeechSynthesisUtterance", javascript)

    def test_committed_production_library_covers_current_vocabulary(self) -> None:
        verified = builder.verify_library()
        manifest = json.loads(
            (REPO_ROOT / "docs" / "data" / "vocabulary-en-audio.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(verified, {"items": 306, "references": 612, "assets": 608})
        self.assertEqual(manifest["voices"]["en"]["label"], "Aria")
        self.assertEqual(manifest["voices"]["cz"]["label"], "Vlasta")


if __name__ == "__main__":
    unittest.main()
