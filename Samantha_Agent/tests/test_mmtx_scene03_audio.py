from __future__ import annotations

import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCENE_ROOT = PROJECT_ROOT / "docs" / "scene03_journey_to_the_lake"
MIRROR_ROOT = PROJECT_ROOT / "MatysekANJ" / "web_mmtx" / "scene03_journey_to_the_lake"
BUILDER_PATH = PROJECT_ROOT / "MatysekANJ" / "build_scene03_audio.py"


def load_audio_manifest() -> dict[str, object]:
    source = (SCENE_ROOT / "audio_manifest.js").read_text(encoding="utf-8")
    prefix = "window.SCENE03_AUDIO_MANIFEST = "
    if not source.startswith(prefix) or not source.endswith(";\n"):
        raise AssertionError("audio_manifest.js nemá očekávaný formát")
    return json.loads(source[len(prefix):-2])


def load_builder():
    spec = importlib.util.spec_from_file_location("mmtx_scene03_audio_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("Nelze načíst build_scene03_audio.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MmtxScene03AudioTests(unittest.TestCase):
    def test_scene_uses_only_fixed_manifest_audio(self) -> None:
        html = (SCENE_ROOT / "index.html").read_text(encoding="utf-8")
        script = (SCENE_ROOT / "script.js").read_text(encoding="utf-8")

        self.assertIn('audio_manifest.js?v=20260829fixed1', html)
        self.assertIn('script.js?v=20260829fixed1', html)
        self.assertLess(html.index("audio_manifest.js"), html.index("script.js"))
        self.assertIn("window.SCENE03_AUDIO_MANIFEST", script)
        self.assertIn("function fixedAudioPath", script)
        self.assertIn("audioManifest.dialogue?.[lang]?.[key]", script)
        self.assertNotIn("speechSynthesis", script)
        self.assertNotIn("SpeechSynthesisUtterance", script)
        self.assertNotIn("sharedVoices", script)
        self.assertNotIn("line.audio", script)
        self.assertNotIn("audioForLine", script)

    def test_manifest_covers_all_168_preserved_and_generated_tracks(self) -> None:
        manifest = load_audio_manifest()
        self.assertEqual(manifest["schemaVersion"], 1)
        self.assertEqual(manifest["version"], "20260829fixed1")
        self.assertEqual(manifest["rate"], "-10%")
        self.assertEqual(
            manifest["stats"],
            {
                "dialogueLines": 39,
                "uiEnglish": 12,
                "uiCzech": 7,
                "vocabularyItems": 35,
                "activeAudioReferences": 167,
                "preservedLegacyAssets": 1,
                "totalAudioFiles": 168,
            },
        )
        dialogue = manifest["dialogue"]
        self.assertEqual(len(dialogue["en"]), 86)
        self.assertEqual(len(dialogue["cs"]), 81)
        self.assertEqual(manifest["voices"]["cs-CZ-VlastaNeural"]["label"], "Vlasta")

        referenced = set(dialogue["en"].values()) | set(dialogue["cs"].values())
        preserved = set(manifest["preservedLegacy"])
        self.assertEqual(len(referenced), 167)
        self.assertEqual(len(preserved), 1)
        actual = {
            path.relative_to(SCENE_ROOT).as_posix()
            for path in (SCENE_ROOT / "audio").rglob("*.mp3")
        }
        self.assertEqual(actual, referenced | preserved)
        self.assertEqual(sum(path.startswith("audio/english/") for path in actual), 87)
        self.assertEqual(sum(path.startswith("audio/czech/") for path in actual), 81)

        for relative_path in sorted(actual):
            with self.subTest(path=relative_path):
                audio = (SCENE_ROOT / relative_path).read_bytes()
                self.assertGreaterEqual(len(audio), 1000)
                self.assertIn(audio[:2], {b"\xff\xf3", b"\xff\xfb", b"ID"})

    def test_dialogue_prompts_and_dictionary_entries_are_present(self) -> None:
        manifest = load_audio_manifest()["dialogue"]
        expected = {
            "en": {
                "benji::Look! Two paths.",
                "crow::Caw! Go left!",
                "horse::Careful! A dog lives there.",
                "fiona::I know! Sunny, jump on the handle!",
                "ui::Who knows how to get water?",
                "ui::Try Fiona!",
                "dictionary-live::live",
                "dictionary-path::path",
            },
            "cs": {
                "benji::Podívej! Dvě cesty.",
                "crow::Krá krá! Jděte vlevo!",
                "horse::Opatrně! Bydlí tam pes.",
                "fiona::Já vím! Sunny, skoč na páku!",
                "ui::Klikni na některého kamaráda, aby řekl, zda ví, jak dostat vodu.",
                "ui::Slovníček. Klepni na slovo a uslyšíš ho anglicky.",
                "dictionary-way::cesta",
                "dictionary-path::cesta",
            },
        }
        for language, keys in expected.items():
            for key in keys:
                with self.subTest(language=language, key=key):
                    self.assertIn(key, manifest[language])

    def test_every_spoken_source_text_has_exactly_one_manifest_entry(self) -> None:
        script = (SCENE_ROOT / "script.js").read_text(encoding="utf-8")
        manifest = load_audio_manifest()["dialogue"]
        line_matches = re.findall(
            r'\b(?:line|lineData)\("([^"]+)", "([^"]*)", "([^"]*)"',
            script,
        )
        vocabulary = re.findall(
            r'\{ en: "([^"]+)", cz: "([^"]+)", emoji:',
            script,
        )
        ui_english = set()
        for property_name in ("promptEn", "wrongHintEn", "hintAfterMistakesEn"):
            ui_english.update(
                re.findall(rf'{property_name}: "([^"]+)"', script)
            )
        ui_english.add("Try again.")
        ui_czech = set(re.findall(r'promptCz: "([^"]+)"', script))
        ui_czech.add(
            re.search(r'mainHelp: "([^"]+)"', script).group(1)
        )
        ui_czech.add("Slovníček. Klepni na slovo a uslyšíš ho anglicky.")

        expected_en = {f"{speaker}::{text_en}" for speaker, text_en, _ in line_matches}
        expected_cs = {f"{speaker}::{text_cz}" for speaker, _, text_cz in line_matches}
        expected_en.update(f"ui::{text}" for text in ui_english)
        expected_cs.update(f"ui::{text}" for text in ui_czech)
        expected_en.update(
            f"dictionary-{text_en}::{text_en}" for text_en, _ in vocabulary
        )
        expected_cs.update(
            f"dictionary-{text_en}::{text_cz}" for text_en, text_cz in vocabulary
        )

        self.assertEqual(set(manifest["en"]), expected_en)
        self.assertEqual(set(manifest["cs"]), expected_cs)

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
        self.assertEqual(
            result,
            {
                "generated": 0,
                "existing": 167,
                "missing": 0,
                "active": 167,
                "preservedLegacy": 1,
                "totalFiles": 168,
            },
        )
        builder.verify()

    def test_story_navigation_to_harry_is_preserved(self) -> None:
        script = (SCENE_ROOT / "script.js").read_text(encoding="utf-8")
        self.assertIn('../scene04_harry_guard_prototype/index.html', script)
        self.assertIn("function goToNextScene()", script)


if __name__ == "__main__":
    unittest.main()
