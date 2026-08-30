from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = PROJECT_ROOT / "docs"
MIRROR_ROOT = PROJECT_ROOT / "MatysekANJ" / "web_mmtx"
BUILDER_PATH = PROJECT_ROOT / "MatysekANJ" / "build_forest_school_audio.py"


def load_audio_manifest() -> dict[str, object]:
    source = (DOCS_ROOT / "forest_school_audio_manifest.js").read_text(encoding="utf-8")
    prefix = "window.FOREST_SCHOOL_AUDIO_MANIFEST = "
    if not source.startswith(prefix) or not source.endswith(";\n"):
        raise AssertionError("forest_school_audio_manifest.js nemá očekávaný formát")
    return json.loads(source[len(prefix):-2])


def load_builder():
    spec = importlib.util.spec_from_file_location("mmtx_forest_school_audio_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("Nelze načíst build_forest_school_audio.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MmtxForestSchoolAudioTests(unittest.TestCase):
    def test_page_loads_forest_school_manifest_before_current_script(self) -> None:
        html = (DOCS_ROOT / "index.html").read_text(encoding="utf-8")
        script = (DOCS_ROOT / "script_intro_v2.js").read_text(encoding="utf-8")

        self.assertIn('forest_school_audio_manifest.js?v=20260830fixed1', html)
        self.assertIn('script_intro_v2.js?v=20260830fixed1', html)
        self.assertLess(html.index("forest_school_audio_manifest.js"), html.index("script_intro_v2.js"))
        self.assertIn("window.FOREST_SCHOOL_AUDIO_MANIFEST", script)
        self.assertIn("function forestSchoolAudioSource", script)
        self.assertIn("function playForestSchoolFixedAudio", script)

    def test_forest_school_runtime_does_not_use_system_voice(self) -> None:
        script = (DOCS_ROOT / "script_intro_v2.js").read_text(encoding="utf-8")
        forest_runtime = script.split("async function speakForestSchoolOwlLine", 1)[1].split(
            "async function playBenjiBunnyHelp", 1
        )[0]
        answer_runtime = script.split("async function handleForestSchoolAnswer", 1)[1].split(
            "function debugSkipOwlGarden", 1
        )[0]

        for runtime in (forest_runtime, answer_runtime):
            self.assertNotIn("speakEnglishLine", runtime)
            self.assertNotIn("speakCzechLine", runtime)
            self.assertNotIn("SpeechSynthesisUtterance", runtime)
        self.assertGreaterEqual(forest_runtime.count("playForestSchoolFixedAudio"), 10)
        self.assertIn('playForestSchoolFixedAudio(answerYes ? "yes" : "no", "en", "answer")', answer_runtime)

    def test_manifest_covers_all_forest_school_audio(self) -> None:
        manifest = load_audio_manifest()
        self.assertEqual(manifest["schemaVersion"], 1)
        self.assertEqual(manifest["version"], "20260830fixed1")
        self.assertEqual(manifest["rate"], "-10%")
        self.assertEqual(
            manifest["stats"],
            {
                "lessons": 12,
                "objects": 60,
                "audioReferences": 204,
                "audioFiles": 203,
                "englishFiles": 141,
                "czechFiles": 62,
                "preservedExistingFiles": 13,
            },
        )
        dialogue = manifest["dialogue"]
        self.assertEqual(len(dialogue["en"]), 141)
        self.assertEqual(len(dialogue["cs"]), 63)
        self.assertEqual(manifest["voices"]["cs-CZ-VlastaNeural"]["label"], "Vlasta")
        self.assertEqual(manifest["voices"]["en-US-JennyNeural"]["label"], "Jenny")

        paths = set(dialogue["en"].values()) | set(dialogue["cs"].values())
        self.assertEqual(len(paths), 203)
        self.assertEqual(sum("/english/" in path for path in paths), 141)
        self.assertEqual(sum("/czech/" in path for path in paths), 62)
        for relative_path in sorted(paths):
            with self.subTest(path=relative_path):
                audio = (DOCS_ROOT / relative_path).read_bytes()
                self.assertGreaterEqual(len(audio), 1000)
                self.assertIn(audio[:2], {b"\xff\xf3", b"\xff\xfb", b"ID"})

    def test_every_lesson_word_translation_and_question_is_manifested(self) -> None:
        builder = load_builder()
        manifest = load_audio_manifest()["dialogue"]
        for lesson in builder.parse_lessons():
            self.assertIn(f"owl::{lesson.title}", manifest["en"])
            for item in lesson.objects:
                self.assertIn(f"word-{item.word}::{item.word}", manifest["en"])
                self.assertIn(f"owl::Is this a {item.word}?", manifest["en"])
                self.assertIn(f"word-{item.word}::{item.translation}", manifest["cs"])

    def test_benji_demo_uses_preserved_no_answer(self) -> None:
        script = (DOCS_ROOT / "script_intro_v2.js").read_text(encoding="utf-8")
        demo = script.split("async function runForestSchoolDemo", 1)[1].split(
            "async function runForestSchool", 1
        )[0]
        self.assertIn('speakForestSchoolBenjiLine("No, it isn\'t.")', demo)
        self.assertIn("setForestSchoolQuestion(benjiObject, wrongForestSchoolQuestionWord(benjiObject.word))", demo)
        self.assertIn("flashForestSchoolDemoAnswer(false, sequenceId)", demo)
        self.assertNotIn('speakForestSchoolBenjiLine("Yes, it is.")', demo)

    def test_docs_and_project_mirror_are_identical(self) -> None:
        manifest = load_audio_manifest()
        paths = set(manifest["dialogue"]["en"].values()) | set(manifest["dialogue"]["cs"].values())
        paths.update({"index.html", "script_intro_v2.js", "forest_school_audio_manifest.js"})
        for relative_path in sorted(paths):
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
            {"generated": 0, "existing": 203, "missing": 0, "references": 204, "files": 203},
        )
        builder.verify()


if __name__ == "__main__":
    unittest.main()
