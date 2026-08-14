from __future__ import annotations

import struct
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROTOTYPE_ROOT = PROJECT_ROOT / "docs" / "scene04_harry_guard_prototype"


class MmtxHarryGuardPrototypeTests(unittest.TestCase):
    def test_prototype_is_standalone_and_has_all_assets(self) -> None:
        expected = {
            "index.html",
            "styles.css",
            "script.js",
            "harry_benji_prototype_01.png",
            "harry_interrogation_benji_01.png",
            "harry_interrogation_bruno_01.png",
            "harry_interrogation_bruno_02.png",
            "harry_interrogation_bunny_01.png",
            "harry_interrogation_fiona_01.png",
            "harry_interrogation_sunny_01.png",
            "audio",
        }
        self.assertEqual({path.name for path in PROTOTYPE_ROOT.iterdir()}, expected)

        html = (PROTOTYPE_ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="languageButton"', html)
        self.assertIn('id="repeatButton"', html)
        self.assertIn('id="sceneImage"', html)
        self.assertIn('id="yesButton"', html)
        self.assertIn('id="noButton"', html)
        self.assertIn('src="harry_benji_prototype_01.png"', html)
        self.assertIn('script.js?v=20260814a', html)
        self.assertIn("Two interviews complete", html)
        self.assertIn("Dva výslechy jsou dokončené.", html)

        production_script = (
            PROJECT_ROOT / "docs" / "scene03_journey_to_the_lake" / "script.js"
        ).read_text(encoding="utf-8")
        self.assertNotIn("scene04_harry_guard_prototype", production_script)

    def test_benji_and_bunny_have_fixed_voice_mp3_assets(self) -> None:
        audio_root = PROTOTYPE_ROOT / "audio" / "english"
        expected = {
            "scene04_benji_f5_candidate_hello_we_are_friendly_en.mp3",
            "scene04_benji_f5_candidate_no_i_do_not_chase_sheep_en.mp3",
            "scene04_benji_hello_we_are_friendly_en.mp3",
            "scene04_benji_i_have_a_map_en.mp3",
            "scene04_benji_no_i_do_not_chase_sheep_en.mp3",
            "scene04_benji_i_help_little_animals_en.mp3",
            "scene04_bunny_not_me_en.mp3",
            "scene04_bunny_i_am_bunny_en.mp3",
            "scene04_bunny_no_i_have_my_own_carrots_en.mp3",
            "scene04_bunny_i_only_want_to_go_to_the_lake_en.mp3",
        }
        self.assertEqual({path.name for path in audio_root.iterdir()}, expected)
        for filename in expected:
            audio = (audio_root / filename).read_bytes()
            self.assertGreater(len(audio), 8000)
            self.assertEqual(audio[:2], b"\xff\xf3")

    def test_image_has_canonical_scene_dimensions(self) -> None:
        expected_images = {
            "harry_benji_prototype_01.png",
            "harry_interrogation_benji_01.png",
            "harry_interrogation_bruno_01.png",
            "harry_interrogation_bruno_02.png",
            "harry_interrogation_bunny_01.png",
            "harry_interrogation_fiona_01.png",
            "harry_interrogation_sunny_01.png",
        }
        for filename in expected_images:
            image = PROTOTYPE_ROOT / filename
            with self.subTest(filename=filename), image.open("rb") as handle:
                self.assertEqual(handle.read(8), b"\x89PNG\r\n\x1a\n")
                chunk_length = struct.unpack(">I", handle.read(4))[0]
                self.assertEqual(handle.read(4), b"IHDR")
                width, height = struct.unpack(">II", handle.read(8))
                self.assertEqual(chunk_length, 13)
                self.assertEqual((width, height), (1672, 941))

    def test_dialogue_and_interaction_contract_is_explicit(self) -> None:
        script = (PROTOTYPE_ROOT / "script.js").read_text(encoding="utf-8")
        for expected in (
            'english: "en"',
            'bilingual: "en-cz"',
            '"mmtx-language-mode"',
            '"Stop! Do not come closer!"',
            '"Who has the map?"',
            '"I have a map."',
            '"Do you want to chase my sheep?"',
            '"No. I do not chase sheep."',
            '"I help little animals."',
            '"Hmm. Maybe I can trust you."',
            '"Wait! What about the rabbit?"',
            '"Who is the rabbit?"',
            '"I am Bunny."',
            '"Do you want to eat the carrots in my garden?"',
            '"No. I have my own carrots."',
            '"I only want to go to the lake."',
            '"Good answer, Bunny. But the gate stays closed."',
            "async function repeatLast()",
            'targetCharacterId = choosingBunny ? "bunny" : "benji"',
            "state.stage !== STAGES.chooseYesNo",
            "state.stage !== STAGES.chooseBunnyYesNo",
            "function updateRepeatAvailability()",
            "STAGES.complete",
            'const BENJI_AUDIO_VERSION = "20260813a"',
            'const BUNNY_AUDIO_VERSION = "20260813a"',
            'src: "harry_interrogation_bunny_01.png"',
            "const SCENE_HOTSPOTS = Object.freeze({",
            "function setSceneImage(sceneId)",
            "function primeSceneImages()",
            "async function speakText(text, lang, characterId)",
            "await playFixedAudio(fixedAudio, text.length)",
            "function primeFixedAudio()",
            "primeFixedAudio();",
            "primeSceneImages();",
            "fixedAudioCache",
        ):
            self.assertIn(expected, script)

        for audio_file in (
            "scene04_benji_hello_we_are_friendly_en.mp3",
            "scene04_benji_i_have_a_map_en.mp3",
            "scene04_benji_no_i_do_not_chase_sheep_en.mp3",
            "scene04_benji_i_help_little_animals_en.mp3",
            "scene04_bunny_not_me_en.mp3",
            "scene04_bunny_i_am_bunny_en.mp3",
            "scene04_bunny_no_i_have_my_own_carrots_en.mp3",
            "scene04_bunny_i_only_want_to_go_to_the_lake_en.mp3",
        ):
            self.assertIn(audio_file, script)

        self.assertIn('await speakText(entry.textEn, "en", entry.characterId)', script)
        self.assertIn('if (isBilingual()) await speakText(entry.textCz, "cs", entry.characterId)', script)
        benji_voice_profile = script.split(
            "const BENJI_ENGLISH_VOICE_ORDER = [", 1
        )[1].split("];", 1)[0]
        expected_order = ["andrew", "evan", "alex", "aaron", "daniel"]
        positions = [benji_voice_profile.index(f'"{name}"') for name in expected_order]
        self.assertEqual(positions, sorted(positions))
        for female_fallback in ("samantha", "ava", "fable"):
            self.assertNotIn(female_fallback, benji_voice_profile)
        self.assertIn(
            'if (lang === "en" && characterId === "benji" && !voice)',
            script,
        )
        bunny_voice_profile = script.split(
            "const BUNNY_ENGLISH_VOICE_ORDER = [", 1
        )[1].split("];", 1)[0]
        self.assertLess(
            bunny_voice_profile.index('"ana"'),
            bunny_voice_profile.index('"samantha"'),
        )
        choose_no_body = script.split("async function chooseNo()", 1)[1].split(
            "async function repeatLast()", 1
        )[0]
        self.assertIn("[lines.noChase, lines.helper, lines.trust]", choose_no_body)
        self.assertIn("setSceneImage(\"bunny\")", choose_no_body)
        self.assertIn("[lines.rabbitIntro, lines.rabbitPrompt]", choose_no_body)
        self.assertLess(
            choose_no_body.index('setSceneImage("bunny")'),
            choose_no_body.index("[lines.rabbitIntro, lines.rabbitPrompt]"),
        )
        self.assertIn(
            "[lines.ownCarrots, lines.lakeOnly, lines.bunnyAccepted]",
            choose_no_body,
        )
        self.assertIn("setStage(STAGES.chooseBunny)", choose_no_body)
        self.assertIn("if (questioningBunny)", choose_no_body)
        repeat_body = script.split("async function repeatLast()", 1)[1].split(
            "function toggleLanguage()", 1
        )[0]
        self.assertNotIn("chooseYes()", repeat_body)
        self.assertNotIn("chooseNo()", repeat_body)
        self.assertIn("if (!state.lastRepeatable || repeatButton.disabled) return", repeat_body)


if __name__ == "__main__":
    unittest.main()
