from __future__ import annotations

import json
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_SCENE = PROJECT_ROOT / "docs" / "scene05_log_bridge"
MIRROR_SCENE = PROJECT_ROOT / "MatysekANJ" / "web_mmtx" / "scene05_log_bridge"

def load_manifest() -> dict[str, object]:
    source = (DOCS_SCENE / "audio_manifest.js").read_text(encoding="utf-8")
    prefix = "window.SCENE05_AUDIO_MANIFEST = "
    if not source.startswith(prefix) or not source.endswith(";\n"):
        raise AssertionError("audio_manifest.js nemá očekávaný formát")
    return json.loads(source[len(prefix):-2])

class MmtxScene05FirstInteractionTests(unittest.TestCase):
    def test_opening_uses_approved_q90_story_image(self) -> None:
        html = (DOCS_SCENE / "index.html").read_text(encoding="utf-8")
        self.assertIn('srcset="scene05_arrival_logan_01_q90.webp"', html)
        self.assertIn('src="scene05_arrival_logan_01.png"', html)
        self.assertNotIn("scene05_stream_base_q85.webp", html)

    def test_controls_and_three_log_interaction_are_present(self) -> None:
        html = (DOCS_SCENE / "index.html").read_text(encoding="utf-8")
        for element_id in ("languageButton", "repeatButton", "nextButton", "audioGate", "speechBubble", "taskPrompt", "logsLayer", "completeBanner"):
            self.assertIn(f'id="{element_id}"', html)
        self.assertEqual(html.count('data-log="'), 3)
        self.assertIn("The bridge is ready!", html)
        self.assertIn("Most je hotový!", html)

    def test_dialogue_contract_steps_one_sentence_at_a_time(self) -> None:
        script = (DOCS_SCENE / "script.js").read_text(encoding="utf-8")
        for text in (
            "Oh no! The old bridge is gone.", "The stream is too wide.", "How can we get across?",
            "Hello, friends! My name is Logan.", "I can help you.", "I have three strong logs.",
            "Help Logan. Tap the three logs.", "One log.", "Two logs.", "Three logs!", "Great! The bridge is ready.",
        ):
            self.assertIn(f'"{text}"', script)
        self.assertIn("state.lineIndex += 1", script)
        self.assertIn("repeatCurrent", script)
        self.assertIn("state.placedLogs += 1", script)
        self.assertNotIn("speechSynthesis", script)
        self.assertNotIn("SpeechSynthesisUtterance", script)

    def test_manifest_covers_every_spoken_line_with_fixed_mp3(self) -> None:
        manifest = load_manifest()
        self.assertEqual(manifest["schemaVersion"], 1)
        self.assertEqual(manifest["version"], "20260831intro1")
        self.assertEqual(manifest["stats"], {"dialogueLines": 11, "audioReferences": 22})
        dialogue = manifest["dialogue"]
        self.assertEqual(len(dialogue["en"]), 11)
        self.assertEqual(len(dialogue["cs"]), 11)
        referenced = set(dialogue["en"].values()) | set(dialogue["cs"].values())
        self.assertEqual(len(referenced), 22)
        for relative_path in referenced:
            audio = (DOCS_SCENE / relative_path).read_bytes()
            self.assertGreaterEqual(len(audio), 1000)
            self.assertIn(audio[:2], {b"\xff\xf3", b"\xff\xfb", b"ID"})

    def test_docs_and_source_mirror_are_byte_identical(self) -> None:
        docs_files = {path.relative_to(DOCS_SCENE) for path in DOCS_SCENE.rglob("*") if path.is_file()}
        mirror_files = {path.relative_to(MIRROR_SCENE) for path in MIRROR_SCENE.rglob("*") if path.is_file()}
        self.assertEqual(docs_files, mirror_files)
        for relative_path in sorted(docs_files):
            with self.subTest(path=str(relative_path)):
                self.assertEqual((DOCS_SCENE / relative_path).read_bytes(), (MIRROR_SCENE / relative_path).read_bytes())

    def test_scene_four_is_not_connected_to_incomplete_scene_five(self) -> None:
        scene_four_script = (PROJECT_ROOT / "docs" / "scene04_harry_guard_prototype" / "script.js").read_text(encoding="utf-8")
        self.assertNotIn("scene05_log_bridge", scene_four_script)

if __name__ == "__main__":
    unittest.main()
