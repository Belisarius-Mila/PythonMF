from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = PROJECT_ROOT / "docs"
MIRROR_ROOT = PROJECT_ROOT / "MatysekANJ" / "web_mmtx"
BUILDER_PATH = PROJECT_ROOT / "MatysekANJ" / "build_scene01_audio.py"


def load_audio_manifest() -> dict[str, object]:
    source = (DOCS_ROOT / "scene01_audio_manifest.js").read_text(encoding="utf-8")
    prefix = "window.SCENE01_AUDIO_MANIFEST = "
    if not source.startswith(prefix) or not source.endswith(";\n"):
        raise AssertionError("scene01_audio_manifest.js nemá očekávaný formát")
    return json.loads(source[len(prefix):-2])


def load_builder():
    spec = importlib.util.spec_from_file_location("mmtx_scene01_audio_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("Nelze načíst build_scene01_audio.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def manifest_paths(manifest: dict[str, object]) -> set[str]:
    paths: set[str] = set()
    for language_entries in manifest["dialogue"].values():
        for value in language_entries.values():
            if isinstance(value, list):
                paths.update(value)
            else:
                paths.add(value)
    return paths


class MmtxScene01AudioTests(unittest.TestCase):
    def test_clearing_scene_loads_manifest_before_current_script(self) -> None:
        html = (DOCS_ROOT / "index.html").read_text(encoding="utf-8")
        script = (DOCS_ROOT / "script_intro_v2.js").read_text(encoding="utf-8")

        self.assertIn('scene01_audio_manifest.js?v=20260829fixed1', html)
        self.assertIn('script_intro_v2.js?v=20260829fixed1', html)
        self.assertLess(html.index("scene01_audio_manifest.js"), html.index("script_intro_v2.js"))
        self.assertIn("window.SCENE01_AUDIO_MANIFEST", script)
        self.assertIn("function clearingAudioSources", script)
        self.assertIn("function playClearingFixedAudio", script)
        self.assertIn("clearingAudioManifest.dialogue?.[lang]?.[key]", script)

    def test_clearing_runtime_has_no_system_voice_calls(self) -> None:
        script = (DOCS_ROOT / "script_intro_v2.js").read_text(encoding="utf-8")
        clearing_runtime = script.split(
            "function createClearingDictionaryPanel()", 1
        )[1].split("async function runOwlGarden", 1)[0]

        self.assertNotIn("speakEnglishLine", clearing_runtime)
        self.assertNotIn("speakCzechLine", clearing_runtime)
        self.assertNotIn("SpeechSynthesisUtterance", clearing_runtime)
        self.assertNotIn("item.audioEn", clearing_runtime)
        self.assertGreaterEqual(clearing_runtime.count("playClearingFixedAudio"), 10)

    def test_manifest_covers_49_fixed_audio_files(self) -> None:
        manifest = load_audio_manifest()
        self.assertEqual(manifest["schemaVersion"], 1)
        self.assertEqual(manifest["version"], "20260829fixed1")
        self.assertEqual(manifest["rate"], "-10%")
        self.assertEqual(
            manifest["stats"],
            {
                "dialogueLines": 11,
                "uiEnglish": 6,
                "uiCzech": 3,
                "vocabularyItems": 8,
                "audioReferences": 47,
                "audioFiles": 49,
                "preservedEnglishFiles": 13,
            },
        )
        self.assertEqual(len(manifest["dialogue"]["en"]), 25)
        self.assertEqual(len(manifest["dialogue"]["cs"]), 22)
        self.assertEqual(manifest["voices"]["cs-CZ-VlastaNeural"]["label"], "Vlasta")
        self.assertEqual(manifest["voices"]["en-US-JennyNeural"]["label"], "Jenny")

        paths = manifest_paths(manifest)
        self.assertEqual(len(paths), 49)
        self.assertEqual(sum("/english/" in path for path in paths), 27)
        self.assertEqual(sum("/czech/" in path for path in paths), 22)
        for relative_path in sorted(paths):
            with self.subTest(path=relative_path):
                audio = (DOCS_ROOT / relative_path).read_bytes()
                self.assertGreaterEqual(len(audio), 1000)
                self.assertIn(audio[:2], {b"\xff\xf3", b"\xff\xfb", b"ID"})

    def test_expected_dialogue_ui_and_dictionary_entries_are_present(self) -> None:
        dialogue = load_audio_manifest()["dialogue"]
        expected = {
            "en": {
                "benji::Hello. I am Benji.",
                "bunny::Hello. I am Bunny.",
                "bruno::We are going to the lake.",
                "fiona::Now we are all friends!",
                "ui::Tap Benji.",
                "ui::Great. Open the door or run again.",
                "dictionary-lake::lake",
            },
            "cs": {
                "benji::Ahoj! Já jsem Benji.",
                "bunny::Ahoj. Já jsem Bunny.",
                "bruno::Jdeme k jezeru.",
                "fiona::Teď jsme všichni kamarádi!",
                "ui::Dveřmi vstoupíš do další scény nebo si přehraj vše znovu.",
                "dictionary-lake::jezero",
            },
        }
        for language, keys in expected.items():
            for key in keys:
                with self.subTest(language=language, key=key):
                    self.assertIn(key, dialogue[language])

        self.assertEqual(
            dialogue["en"]["benji::Hello. I am Benji."],
            [
                "audio/english/benji_bunny_01_benji_hello_en.mp3",
                "audio/english/benji_bunny_03_benji_i_am_benji_en.mp3",
            ],
        )

    def test_docs_and_mirror_are_identical_for_scene01_assets(self) -> None:
        manifest = load_audio_manifest()
        relative_paths = manifest_paths(manifest) | {
            "index.html",
            "script_intro_v2.js",
            "scene01_audio_manifest.js",
        }
        for relative_path in sorted(relative_paths):
            with self.subTest(path=relative_path):
                self.assertEqual(
                    (DOCS_ROOT / relative_path).read_bytes(),
                    (MIRROR_ROOT / relative_path).read_bytes(),
                )

    def test_reproducible_builder_reports_complete_without_generation(self) -> None:
        builder = load_builder()
        result = builder.build(apply=False)
        self.assertEqual(
            result,
            {
                "generated": 0,
                "existing": 49,
                "missing": 0,
                "references": 47,
                "files": 49,
            },
        )
        builder.verify()

    def test_clearing_door_still_opens_scene02(self) -> None:
        script = (DOCS_ROOT / "script_intro_v2.js").read_text(encoding="utf-8")
        self.assertIn(
            'window.location.href = "scene02_sunnys_lost_nuts/index.html";',
            script,
        )


if __name__ == "__main__":
    unittest.main()
