from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_SCENE = PROJECT_ROOT / "docs" / "scene05_log_bridge"
MIRROR_SCENE = PROJECT_ROOT / "MatysekANJ" / "web_mmtx" / "scene05_log_bridge"
GLOSSARY = {
    "bridge": "most",
    "stream": "potok",
    "wide": "široký",
    "get across": "dostat se na druhou stranu",
    "log": "kláda",
    "strong": "pevný",
    "ready": "hotový",
    "safe": "bezpečný",
    "jump": "skákat",
    "scared": "bát se",
    "heavy": "těžký",
    "one step at a time": "krok za krokem",
    "lamp": "lampa",
    "do not worry": "neboj se",
    "save": "zachránit",
    "you are welcome": "není zač",
}

def load_manifest() -> dict[str, object]:
    source = (DOCS_SCENE / "audio_manifest.js").read_text(encoding="utf-8")
    prefix = "window.SCENE05_AUDIO_MANIFEST = "
    if not source.startswith(prefix) or not source.endswith(";\n"):
        raise AssertionError("audio_manifest.js nemá očekávaný formát")
    return json.loads(source[len(prefix):-2])

class MmtxScene05FirstInteractionTests(unittest.TestCase):
    def test_opening_and_completed_bridge_use_approved_images(self) -> None:
        html = (DOCS_SCENE / "index.html").read_text(encoding="utf-8")
        self.assertIn('srcset="scene05_log_bridge_supports_smooth_q90.webp"', html)
        self.assertIn('src="scene05_log_bridge_supports_smooth_q90.webp"', html)
        self.assertIn('id="finalScene"', html)
        self.assertIn('src="scene05_log_bridge_complete_smooth_q90.webp"', html)
        self.assertIn('src="scene05_benji_across_smooth_q90.webp"', html)
        self.assertIn('src="scene05_benji_sunny_across_smooth_q90.webp"', html)
        self.assertIn('src="scene05_fiona_across_smooth_q90.webp"', html)
        self.assertIn('src="scene05_bruno_bunny_crossing_smooth_q90.webp"', html)
        self.assertIn('src="scene05_lamp_falling_smooth_q90.webp"', html)
        self.assertIn('src="scene05_lamp_rescued_smooth_q90.webp"', html)
        self.assertIn('data-scene-state="bridge-supports"', html)
        for legacy_filename in (
            "scene05_log_bridge_supports.webp",
            "scene05_log_bridge_crooked_trees.webp",
            "scene05_benji_across_q90.webp",
            "scene05_benji_sunny_across_q90.webp",
        ):
            self.assertNotIn(legacy_filename, html)

    def test_bridge_images_and_log_sprites_keep_production_contract(self) -> None:
        for filename in (
            "scene05_log_bridge_supports_smooth_q90.webp",
            "scene05_log_bridge_complete_smooth_q90.webp",
            "scene05_benji_across_smooth_q90.webp",
            "scene05_benji_sunny_across_smooth_q90.webp",
            "scene05_fiona_across_smooth_q90.webp",
            "scene05_bruno_bunny_crossing_smooth_q90.webp",
            "scene05_lamp_falling_smooth_q90.webp",
            "scene05_lamp_rescued_smooth_q90.webp",
            "scene05_friends_farewell_smooth_q90.webp",
        ):
            with Image.open(DOCS_SCENE / filename) as image:
                self.assertEqual(image.size, (1672, 941))
                self.assertEqual(image.format, "WEBP")
        for filename in ("scene05_log_sprite_a.webp", "scene05_log_sprite_b.webp"):
            with Image.open(DOCS_SCENE / filename) as image:
                self.assertEqual(image.format, "WEBP")
                self.assertIn("A", image.getbands())

    def test_controls_and_three_log_interaction_are_present(self) -> None:
        html = (DOCS_SCENE / "index.html").read_text(encoding="utf-8")
        for element_id in (
            "languageButton", "repeatButton", "nextButton", "audioGate", "speechBubble",
            "taskPrompt", "taskIcon", "logsLayer", "benjiTarget", "sunnyTarget", "fionaTarget",
            "brunoTarget", "loganTarget", "completeBanner",
            "dictionaryButton", "dictionaryPanel", "dictionaryList",
        ):
            self.assertIn(f'id="{element_id}"', html)
        self.assertEqual(html.count('data-log="'), 3)
        self.assertEqual(html.count('class="log-sprite"'), 3)
        self.assertIn("Bridge crossing complete!", html)
        self.assertIn("Přechod přes most je dokončený!", html)
        self.assertIn("📖", html)
        self.assertIn("New words", html)
        self.assertIn("Nová slovíčka", html)

    def test_dialogue_contract_steps_one_sentence_at_a_time(self) -> None:
        script = (DOCS_SCENE / "script.js").read_text(encoding="utf-8")
        for text in (
            "Oh no! The old bridge is gone.", "The stream is too wide.", "How can we get across?",
            "Hello, friends! My name is Logan.", "I can help you.", "I have three strong logs.",
            "Help Logan. Tap the three logs.", "One log.", "Two logs.", "Three logs!", "Great! The bridge is ready.",
            "Who wants to go first?", "I will go first.", "Tap Benji and help him cross.",
            "I did it! The bridge is safe.", "My turn! I can jump.",
            "Tap Sunny. Help her jump across.", "One, two, three!", "Oh no... I am scared.",
            "The bridge is safe, Bunny!", "Watch me, Bunny.", "Tap Fiona and help her cross.",
            "I crossed the bridge safely!", "My bag is too heavy.", "I can help you.",
            "Give me your bag.", "Thank you, Bruno.", "Tap Bruno. Help Bunny cross.",
            "One step at a time, Bunny.", "Oh no, my lamp!", "Do not worry. I can get it.",
            "Tap Logan and save the lamp.", "Here is your lamp, Bruno.", "Thank you, Logan!",
            "You are welcome, friends.", "To the lake!",
        ):
            self.assertIn(f'"{text}"', script)
        self.assertIn("state.lineIndex += 1", script)
        self.assertIn("repeatCurrent", script)
        self.assertIn("state.placedLogs += 1", script)
        self.assertIn("button.animate(flightFrames(button, index)", script)
        self.assertIn('finalScene.classList.add("visible")', script)
        self.assertIn('scene.dataset.sceneState = "bridge-complete"', script)
        self.assertIn('revealStoryState(benjiAcrossScene, "benji-across")', script)
        self.assertIn('revealStoryState(sunnyAcrossScene, "benji-sunny-across")', script)
        self.assertIn("crossWithBenji", script)
        self.assertIn("crossWithSunny", script)
        self.assertIn('revealStoryState(fionaAcrossScene, "fiona-across")', script)
        self.assertIn('revealStoryState(brunoBunnyCrossingScene, "bruno-bunny-crossing")', script)
        self.assertIn('revealStoryState(lampFallingScene, "lamp-falling")', script)
        self.assertIn('revealStoryState(lampRescuedScene, "lamp-rescued")', script)
        self.assertIn("crossWithFiona", script)
        self.assertIn("crossWithBruno", script)
        self.assertIn("rescueLampWithLogan", script)
        self.assertIn('matchMedia("(prefers-reduced-motion: reduce)")', script)
        self.assertNotIn("speechSynthesis", script)
        self.assertNotIn("SpeechSynthesisUtterance", script)

    def test_dictionary_opens_only_after_completion_and_uses_local_audio(self) -> None:
        script = (DOCS_SCENE / "script.js").read_text(encoding="utf-8")
        css = (DOCS_SCENE / "interaction.css").read_text(encoding="utf-8")
        for text_en, text_cz in GLOSSARY.items():
            self.assertIn(f'en: "{text_en}"', script)
            self.assertIn(f'cz: "{text_cz}"', script)
        self.assertIn('const dictionaryAvailable = state.stage === "complete";', script)
        self.assertIn("renderDictionary", script)
        self.assertIn("playVocabularyItem", script)
        self.assertIn('vocabularyAudioPath(item, "en")', script)
        self.assertIn('vocabularyAudioPath(item, "cs")', script)
        self.assertIn(".dictionary-panel", css)
        self.assertIn(".dictionary-list", css)
        self.assertIn(".dictionary-item", css)

    def test_smooth_scene_images_preserve_png_sources_and_q90_webp_outputs(self) -> None:
        for stem in (
            "scene05_log_bridge_supports_smooth",
            "scene05_log_bridge_complete_smooth",
            "scene05_benji_across_smooth",
            "scene05_benji_sunny_across_smooth",
            "scene05_fiona_across_smooth",
            "scene05_bruno_bunny_crossing_smooth",
            "scene05_lamp_falling_smooth",
            "scene05_lamp_rescued_smooth",
        ):
            source = DOCS_SCENE / "assets" / f"{stem}_source.png"
            production = DOCS_SCENE / f"{stem}_q90.webp"
            with Image.open(source) as image:
                self.assertEqual(image.size, (1672, 941))
                self.assertEqual(image.format, "PNG")
            with Image.open(production) as image:
                self.assertEqual(image.size, (1672, 941))
                self.assertEqual(image.format, "WEBP")
            self.assertLess(production.stat().st_size, source.stat().st_size)

    def test_logs_use_real_alpha_sprites_instead_of_css_cylinders(self) -> None:
        css = (DOCS_SCENE / "interaction.css").read_text(encoding="utf-8")
        self.assertIn(".log-sprite", css)
        self.assertIn("drop-shadow", css)
        self.assertNotIn("repeating-linear-gradient", css)
        self.assertNotIn("repeating-radial-gradient", css)

    def test_manifest_covers_every_spoken_line_with_fixed_mp3(self) -> None:
        manifest = load_manifest()
        self.assertEqual(manifest["schemaVersion"], 1)
        self.assertEqual(manifest["version"], "20260907dictionary1")
        self.assertEqual(
            manifest["stats"],
            {"dialogueLines": 36, "vocabularyItems": 16, "audioReferences": 104},
        )
        dialogue = manifest["dialogue"]
        self.assertEqual(len(dialogue["en"]), 52)
        self.assertEqual(len(dialogue["cs"]), 52)
        for text_en, text_cz in GLOSSARY.items():
            self.assertIn(f"dictionary::{text_en}", dialogue["en"])
            self.assertIn(f"dictionary::{text_cz}", dialogue["cs"])
        referenced = set(dialogue["en"].values()) | set(dialogue["cs"].values())
        self.assertEqual(len(referenced), 104)
        for relative_path in referenced:
            audio = (DOCS_SCENE / relative_path).read_bytes()
            self.assertGreaterEqual(len(audio), 1000)
            self.assertIn(audio[:2], {b"\xff\xf3", b"\xff\xfb", b"ID"})

    def test_audio_builder_verifies_dialogue_and_dictionary_assets(self) -> None:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "MatysekANJ" / "build_scene05_audio.py"), "--check"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("104 pevných stop", result.stdout)

    def test_docs_and_source_mirror_are_byte_identical(self) -> None:
        docs_files = {path.relative_to(DOCS_SCENE) for path in DOCS_SCENE.rglob("*") if path.is_file()}
        mirror_files = {path.relative_to(MIRROR_SCENE) for path in MIRROR_SCENE.rglob("*") if path.is_file()}
        self.assertEqual(docs_files, mirror_files)
        for relative_path in sorted(docs_files):
            with self.subTest(path=str(relative_path)):
                self.assertEqual((DOCS_SCENE / relative_path).read_bytes(), (MIRROR_SCENE / relative_path).read_bytes())

    def test_scene_four_connects_to_completed_scene_five(self) -> None:
        scene_four_html = (PROJECT_ROOT / "docs" / "scene04_harry_guard_prototype" / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="../scene05_log_bridge/index.html"', scene_four_html)
        self.assertIn("Pokračuj k mostu z klád.", scene_four_html)

if __name__ == "__main__":
    unittest.main()
