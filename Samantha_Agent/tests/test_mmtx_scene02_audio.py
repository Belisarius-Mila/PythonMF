from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCENE_ROOT = PROJECT_ROOT / "docs" / "scene02_sunnys_lost_nuts"
MIRROR_ROOT = PROJECT_ROOT / "MatysekANJ" / "web_mmtx" / "scene02_sunnys_lost_nuts"
BUILDER_PATH = PROJECT_ROOT / "MatysekANJ" / "build_scene02_audio.py"


def load_audio_manifest() -> dict[str, object]:
    source = (SCENE_ROOT / "audio_manifest.js").read_text(encoding="utf-8")
    prefix = "window.SCENE02_AUDIO_MANIFEST = "
    if not source.startswith(prefix) or not source.endswith(";\n"):
        raise AssertionError("audio_manifest.js nemá očekávaný formát")
    return json.loads(source[len(prefix):-2])


def load_builder():
    spec = importlib.util.spec_from_file_location("mmtx_scene02_audio_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("Nelze načíst build_scene02_audio.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MmtxScene02AudioTests(unittest.TestCase):
    def test_scene_uses_only_fixed_manifest_audio(self) -> None:
        html = (SCENE_ROOT / "index.html").read_text(encoding="utf-8")
        script = (SCENE_ROOT / "script.js").read_text(encoding="utf-8")

        self.assertIn('audio_manifest.js?v=20260829fixed1', html)
        self.assertIn('script.js?v=20260829fixed1', html)
        self.assertLess(html.index("audio_manifest.js"), html.index("script.js"))
        self.assertIn("window.SCENE02_AUDIO_MANIFEST", script)
        self.assertIn("function fixedAudioPath", script)
        self.assertIn("audioManifest.dialogue?.[lang]?.[key]", script)
        self.assertNotIn("speechSynthesis", script)
        self.assertNotIn("SpeechSynthesisUtterance", script)
        self.assertNotIn("preferredVoice", script)
        self.assertNotIn("item.audio", script)
        self.assertNotIn("line.audio", script)

    def test_manifest_covers_all_55_fixed_tracks(self) -> None:
        manifest = load_audio_manifest()
        self.assertEqual(manifest["schemaVersion"], 1)
        self.assertEqual(manifest["version"], "20260829fixed1")
        self.assertEqual(manifest["rate"], "-10%")
        self.assertEqual(
            manifest["stats"],
            {"dialogueLines": 9, "vocabularyItems": 12, "audioReferences": 55},
        )
        dialogue = manifest["dialogue"]
        self.assertEqual(len(dialogue["en"]), 28)
        self.assertEqual(len(dialogue["cs"]), 27)
        self.assertEqual(manifest["voices"]["cs-CZ-VlastaNeural"]["label"], "Vlasta")

        referenced = set(dialogue["en"].values()) | set(dialogue["cs"].values())
        self.assertEqual(len(referenced), 55)
        actual = {
            path.relative_to(SCENE_ROOT).as_posix()
            for path in (SCENE_ROOT / "audio").rglob("*.mp3")
        }
        self.assertEqual(actual, referenced)

        for relative_path in sorted(referenced):
            with self.subTest(path=relative_path):
                audio = (SCENE_ROOT / relative_path).read_bytes()
                self.assertGreaterEqual(len(audio), 1000)
                self.assertIn(audio[:2], {b"\xff\xf3", b"\xff\xfb", b"ID"})

    def test_expected_dialogue_and_vocabulary_entries_are_present(self) -> None:
        manifest = load_audio_manifest()["dialogue"]
        expected = {
            "en": {
                "sunny::Oh no! I don't have my nuts!",
                "fiona::Benji, do you have nuts?",
                "benji::No. I have a map.",
                "fiona::Bunny, do you have nuts?",
                "bunny::No. I have a carrot.",
                "bruno::Wait a second. I have a bag.",
                "bruno::It is big. Look inside, friends!",
                "sunny::My nuts! I am so happy!",
                "fiona::Good. Now we are ready.",
                "dictionary::ready",
                "dictionary::wait",
                "dictionary::happy",
            },
            "cs": {
                "sunny::Ach ne! Nemám svoje oříšky!",
                "fiona::Benji, máš oříšky?",
                "benji::Ne. Mám mapu.",
                "fiona::Bunny, máš oříšky?",
                "bunny::Ne. Mám mrkev.",
                "bruno::Počkejte chvilku. Mám brašnu.",
                "bruno::Je velká. Podívejte se dovnitř, kamarádi!",
                "sunny::Moje oříšky! Mám takovou radost!",
                "fiona::Dobře. Teď jsme připraveni.",
                "dictionary::připravený",
                "dictionary::počkat",
                "dictionary::šťastný",
            },
        }
        for language, keys in expected.items():
            for key in keys:
                with self.subTest(language=language, key=key):
                    self.assertIn(key, manifest[language])

    def test_docs_and_project_mirror_are_byte_identical(self) -> None:
        docs_files = {
            path.relative_to(SCENE_ROOT) for path in SCENE_ROOT.rglob("*") if path.is_file()
        }
        mirror_files = {
            path.relative_to(MIRROR_ROOT) for path in MIRROR_ROOT.rglob("*") if path.is_file()
        }
        self.assertEqual(docs_files, mirror_files)
        for relative_path in sorted(docs_files):
            with self.subTest(path=str(relative_path)):
                self.assertEqual(
                    (SCENE_ROOT / relative_path).read_bytes(),
                    (MIRROR_ROOT / relative_path).read_bytes(),
                )

    def test_reproducible_builder_reports_complete_without_generation(self) -> None:
        builder = load_builder()
        result = builder.build(apply=False)
        self.assertEqual(result, {"generated": 0, "existing": 55, "missing": 0, "total": 55})
        builder.verify()


if __name__ == "__main__":
    unittest.main()
