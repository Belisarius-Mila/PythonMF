from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = REPO_ROOT / "VocabularyEN" / "build_audio_casting.py"
SPEC = importlib.util.spec_from_file_location("vocabularyen_audio_casting", BUILDER_PATH)
assert SPEC is not None and SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


class VocabularyEnAudioCastingTests(unittest.TestCase):
    def test_casting_source_matches_current_vocabulary_csv(self) -> None:
        items = builder.load_casting_items()

        self.assertEqual(len(items), 10)
        self.assertEqual(len({item.item_id for item in items}), len(items))
        self.assertEqual(items[0].display_en, "a glass (of water)")
        self.assertEqual(items[-1].display_en, "squirrel")
        self.assertEqual(items[0].speak_en, "a glass of water")
        self.assertEqual(items[5].speak_cz, "pravý. Správný. Doprava.")

    def test_builder_creates_complete_deterministic_casting_and_skips_existing(self) -> None:
        calls: list[tuple[str, str, str]] = []

        def fake_synthesize(text: str, *, voice: str, rate: str) -> bytes:
            calls.append((text, voice, rate))
            return b"ID3" + (f"{voice}|{rate}|{text}".encode("utf-8") * 40)

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            first = builder.build_casting(output, synthesize=fake_synthesize)
            manifest_bytes = (output / "casting.json").read_bytes()
            second = builder.build_casting(output, synthesize=fake_synthesize)

            self.assertEqual(first, {"generated": 40, "skipped": 0, "total": 40})
            self.assertEqual(second, {"generated": 0, "skipped": 40, "total": 40})
            self.assertEqual(len(calls), 40)
            self.assertEqual((output / "casting.json").read_bytes(), manifest_bytes)

            manifest = json.loads(manifest_bytes)
            self.assertEqual(manifest["schemaVersion"], 1)
            self.assertEqual(manifest["rate"], "-10%")
            self.assertEqual(len(manifest["voices"]), 4)
            self.assertEqual(len(manifest["items"]), 10)
            paths = [
                output / relative
                for per_voice in manifest["audio"].values()
                for relative in per_voice.values()
            ]
            self.assertEqual(len(paths), 40)
            self.assertTrue(all(path.is_file() and path.stat().st_size >= 512 for path in paths))

    def test_casting_page_is_local_and_does_not_use_browser_speech(self) -> None:
        casting_dir = REPO_ROOT / "VocabularyEN" / "audio_casting"
        html = (casting_dir / "index.html").read_text(encoding="utf-8")
        javascript = (casting_dir / "app.js").read_text(encoding="utf-8")

        self.assertIn("casting.json", javascript)
        self.assertIn("localStorage", javascript)
        self.assertIn("nikam výsledek neodesílá", html)
        self.assertNotIn("speechSynthesis", javascript)
        self.assertNotIn("fetch(\"http", javascript)

    def test_generated_casting_contains_all_mp3_assets(self) -> None:
        casting_dir = REPO_ROOT / "VocabularyEN" / "audio_casting"
        manifest = json.loads((casting_dir / "casting.json").read_text(encoding="utf-8"))
        paths = [
            casting_dir / relative
            for per_voice in manifest["audio"].values()
            for relative in per_voice.values()
        ]

        self.assertEqual(len(paths), 40)
        self.assertEqual(len(set(paths)), 40)
        for path in paths:
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 1000)

    def test_registered_capability_is_the_expected_audio_generator(self) -> None:
        synthesizer = builder.registered_synthesizer()

        self.assertEqual(
            f"{synthesizer.__module__}.{synthesizer.__name__}",
            builder.CAPABILITY_TOOL,
        )


if __name__ == "__main__":
    unittest.main()
