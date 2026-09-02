from __future__ import annotations

import json
import struct
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROTOTYPE_ROOT = PROJECT_ROOT / "docs" / "scene04_harry_guard_prototype"
MIRROR_ROOT = PROJECT_ROOT / "MatysekANJ" / "web_mmtx" / "scene04_harry_guard_prototype"
GLOSSARY_SLUGS = {
    "answer",
    "badger",
    "believe",
    "catch",
    "chase",
    "chicken",
    "closed",
    "come_closer",
    "dig",
    "eat",
    "fence",
    "fox",
    "gate",
    "little_animals",
    "own",
    "question",
    "rabbit",
    "sheep",
    "squirrel",
    "trust",
    "under",
    "yard",
}


def load_audio_manifest() -> dict[str, object]:
    source = (PROTOTYPE_ROOT / "audio_manifest.js").read_text(encoding="utf-8")
    prefix = "window.SCENE04_AUDIO_MANIFEST = "
    if not source.startswith(prefix) or not source.endswith(";\n"):
        raise AssertionError("audio_manifest.js nemá očekávaný formát")
    return json.loads(source[len(prefix):-2])


class MmtxHarryGuardPrototypeTests(unittest.TestCase):
    def test_scene_is_integrated_and_has_all_assets(self) -> None:
        expected = {
            "index.html",
            "styles.css",
            "script.js",
            "audio_manifest.js",
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
        styles = (PROTOTYPE_ROOT / "styles.css").read_text(encoding="utf-8")
        self.assertIn('id="languageButton"', html)
        self.assertIn('id="backButton"', html)
        self.assertIn('id="repeatButton"', html)
        self.assertIn('id="nextButton"', html)
        self.assertIn('id="dictionaryButton"', html)
        self.assertIn('id="dictionaryPanel"', html)
        self.assertIn('id="dictionaryList"', html)
        self.assertIn('id="sceneImage"', html)
        self.assertIn('id="yesButton"', html)
        self.assertIn('id="noButton"', html)
        self.assertIn('src="harry_benji_prototype_01.png"', html)
        self.assertIn('styles.css?v=20260902scene05link1', html)
        self.assertIn('href="../scene05_log_bridge/index.html"', html)
        self.assertIn('audio_manifest.js?v=20260829fixed1', html)
        self.assertIn('script.js?v=20260829fixed1', html)
        self.assertNotIn("PROTOTYP", html)
        self.assertNotIn("MMTX prototyp", html)
        self.assertIn("Five interviews complete", html)
        self.assertIn("Pět výslechů je dokončených.", html)
        target_style = styles.split(".hotspot.target {", 1)[1].split("}", 1)[0]
        self.assertIn("z-index: 2;", target_style)
        self.assertIn(".dictionary-panel {", styles)
        self.assertIn(".dictionary-list {", styles)
        self.assertIn(".dictionary-item {", styles)
        self.assertIn(".next-button {", styles)
        self.assertIn(".back-button {", styles)

        production_script = (
            PROJECT_ROOT / "docs" / "scene03_journey_to_the_lake" / "script.js"
        ).read_text(encoding="utf-8")
        production_html = (
            PROJECT_ROOT / "docs" / "scene03_journey_to_the_lake" / "index.html"
        ).read_text(encoding="utf-8")
        self.assertIn("audio_manifest.js?v=20260829fixed1", production_html)
        self.assertIn("script.js?v=20260829fixed1", production_html)
        quick_advance = production_script.split(
            "function quickAdvanceScene()", 1
        )[1].split("function isQuickSkipCornerClick", 1)[0]
        self.assertIn("if (isDirectScene04Shortcut())", quick_advance)
        self.assertLess(
            quick_advance.index("if (isDirectScene04Shortcut())"),
            quick_advance.index("if (state.sceneState === SCENE_STATES.waitingAudio)"),
        )
        shortcut = production_script.split(
            "function isDirectScene04Shortcut()", 1
        )[1].split("function handleRepeat", 1)[0]
        self.assertIn('state.phase === "3a"', shortcut)
        self.assertIn("state.sceneState === SCENE_STATES.complete", shortcut)
        self.assertIn('"Pokračovat k Harrymu"', production_script)
        self.assertIn(
            'window.location.href = "../scene04_harry_guard_prototype/index.html";',
            production_script,
        )

        scene_script = (PROTOTYPE_ROOT / "script.js").read_text(encoding="utf-8")
        self.assertIn('const backButton = document.getElementById("backButton")', scene_script)
        self.assertIn(
            'window.location.href = "../scene03_journey_to_the_lake/index.html";',
            scene_script,
        )
        self.assertIn('backButton.addEventListener("click", goBack)', scene_script)

    def test_production_scene_mirror_is_byte_identical(self) -> None:
        docs_files = {
            path.relative_to(PROTOTYPE_ROOT)
            for path in PROTOTYPE_ROOT.rglob("*")
            if path.is_file()
        }
        mirror_files = {
            path.relative_to(MIRROR_ROOT)
            for path in MIRROR_ROOT.rglob("*")
            if path.is_file()
        }
        self.assertEqual(mirror_files, docs_files)
        for relative_path in sorted(docs_files):
            with self.subTest(path=str(relative_path)):
                self.assertEqual(
                    (MIRROR_ROOT / relative_path).read_bytes(),
                    (PROTOTYPE_ROOT / relative_path).read_bytes(),
                )

    def test_every_spoken_line_has_a_fixed_mp3_asset(self) -> None:
        manifest = load_audio_manifest()
        self.assertEqual(manifest["schemaVersion"], 1)
        self.assertEqual(manifest["version"], "20260829fixed1")
        self.assertEqual(
            manifest["stats"],
            {"dialogueCombinations": 46, "vocabularyItems": 22, "audioReferences": 136},
        )

        dialogue = manifest["dialogue"]
        self.assertEqual(len(dialogue["en"]), 68)
        self.assertEqual(len(dialogue["cs"]), 68)
        for character_id in ("harry", "benji", "bunny", "sunny", "fiona", "bruno"):
            self.assertIn(f"{character_id}::Not me.", dialogue["en"])
            self.assertIn(f"{character_id}::Já ne.", dialogue["cs"])

        referenced = set(dialogue["en"].values()) | set(dialogue["cs"].values())
        self.assertEqual(len(referenced), 136)
        expected_extras = {
            "scene04_benji_f5_candidate_hello_we_are_friendly_en.mp3",
            "scene04_benji_f5_candidate_no_i_do_not_chase_sheep_en.mp3",
        }
        actual = {
            path.relative_to(PROTOTYPE_ROOT).as_posix()
            for path in (PROTOTYPE_ROOT / "audio").rglob("*.mp3")
        }
        self.assertEqual(
            actual,
            referenced | {f"audio/english/{filename}" for filename in expected_extras},
        )
        for relative_path in referenced:
            audio = (PROTOTYPE_ROOT / relative_path).read_bytes()
            self.assertGreaterEqual(len(audio), 1000)
            self.assertIn(audio[:2], {b"\xff\xf3", b"\xff\xfb", b"ID"})

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
            '"My name is Harry, and I guard this gate!"',
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
            '"Now, what about the squirrel?"',
            '"Who is the squirrel?"',
            '"Hello! I am Sunny."',
            '"Do you want to eat the nuts from my tree?"',
            '"No. I have my own nuts."',
            '"I want to go to the lake with my friends."',
            '"Good answer, Sunny. But I have more questions."',
            '"And what about the fox?"',
            '"Who is the fox?"',
            '"Hi. I am Fiona."',
            '"Do you want to catch a chicken in my yard?"',
            '"No. I do not catch chickens."',
            '"Good answer, Fiona. But I have one more question."',
            '"One more! What about the badger?"',
            '"Who is the badger?"',
            '"Hello. I am Bruno."',
            '"Do you want to dig under my fence?"',
            '"No. I do not dig under fences."',
            '"Good answer, Bruno. I believe you."',
            '"OK, now you can continue. The gate is open for you, friends!"',
            "async function repeatLast()",
            "function waitForNext(flowId)",
            "function advanceDialogue()",
            "async function playSequence(entries, flowId)",
            "async function advanceToScene(sceneId, entries, flowId)",
            'choosingBruno ? "bruno" : "benji"',
            "STAGES.chooseFionaYesNo",
            "STAGES.chooseBrunoYesNo",
            "STAGES.chooseSunnyYesNo",
            "function updateRepeatAvailability()",
            "STAGES.complete",
            "const AUDIO_MANIFEST = window.SCENE04_AUDIO_MANIFEST",
            "function audioKey(characterId, text)",
            "function fixedAudioFor(text, lang, characterId)",
            "const VOCABULARY = Object.freeze([",
            'src: "harry_interrogation_bunny_01.png"',
            'src: "harry_interrogation_sunny_01.png"',
            'src: "harry_interrogation_fiona_01.png"',
            'src: "harry_interrogation_bruno_02.png"',
            "const SCENE_HOTSPOTS = Object.freeze({",
            "function setSceneImage(sceneId)",
            "function primeSceneImages()",
            "async function speakText(text, lang, characterId)",
            "return playFixedAudio(fixedAudio, text.length)",
            "function primeFixedAudio()",
            "primeFixedAudio();",
            "primeSceneImages();",
            "fixedAudioCache",
            "function renderDictionary()",
            "async function playVocabularyItem(item)",
            "function toggleDictionary()",
            "function updateDictionaryAvailability()",
            'dictionaryButton.addEventListener("click", toggleDictionary)',
            'nextButton.addEventListener("click", advanceDialogue)',
            "...Object.values(AUDIO_MANIFEST.dialogue?.en || {})",
            "...Object.values(AUDIO_MANIFEST.dialogue?.cs || {})",
        ):
            self.assertIn(expected, script)

        vocabulary_block = script.split(
            "const VOCABULARY = Object.freeze([", 1
        )[1].split("].map((item)", 1)[0]
        expected_vocabulary = {
            "come closer": "přijít blíž",
            "chase": "honit",
            "sheep": "ovce",
            "little animals": "malá zvířátka",
            "trust": "důvěřovat",
            "rabbit": "králík",
            "eat": "jíst",
            "own": "vlastní",
            "gate": "branka",
            "closed": "zavřený",
            "squirrel": "veverka",
            "question": "otázka",
            "answer": "odpověď",
            "fox": "liška",
            "catch": "chytit",
            "chicken": "slepice",
            "yard": "dvorek",
            "badger": "jezevec",
            "dig": "hrabat",
            "under": "pod",
            "fence": "plot",
            "believe": "věřit",
        }
        self.assertEqual(vocabulary_block.count("{ en:"), len(expected_vocabulary))
        for english, czech in expected_vocabulary.items():
            self.assertIn(f'en: "{english}"', vocabulary_block)
            self.assertIn(f'cz: "{czech}"', vocabulary_block)
        for previously_practised in (
            "map",
            "carrot",
            "nuts",
            "garden",
            "tree",
            "friendly",
            "lake",
            "friends",
        ):
            self.assertNotIn(f'en: "{previously_practised}"', vocabulary_block)
        for slug in GLOSSARY_SLUGS:
            self.assertIn(f'file: "{slug}"', vocabulary_block)

        dictionary_playback = script.split(
            "async function playVocabularyItem(item)", 1
        )[1].split("function toggleDictionary()", 1)[0]
        self.assertIn('await speakText(item.en, "en", "dictionary")', dictionary_playback)
        self.assertIn('if (isBilingual()) await speakText(item.cz, "cs", "dictionary")', dictionary_playback)
        dictionary_availability = script.split(
            "function updateDictionaryAvailability()", 1
        )[1].split("function updateDictionaryLanguageUi()", 1)[0]
        self.assertIn("state.stage === STAGES.complete", dictionary_availability)
        self.assertIn('dictionaryButton.classList.toggle("hidden", !isComplete)', dictionary_availability)

        self.assertIn('await speakText(entry.textEn, "en", entry.characterId)', script)
        self.assertIn('if (isBilingual()) await speakText(entry.textCz, "cs", entry.characterId)', script)
        self.assertNotIn("speechSynthesis", script)
        self.assertNotIn("SpeechSynthesisUtterance", script)
        self.assertNotIn("item.audio", script)
        choose_no_body = script.split("async function chooseNo()", 1)[1].split(
            "async function repeatLast()", 1
        )[0]
        self.assertIn("[lines.noChase, lines.helper, lines.trust]", choose_no_body)
        self.assertIn(
            'advanceToScene("bunny", [lines.rabbitIntro, lines.rabbitPrompt], flowId)',
            choose_no_body,
        )
        self.assertIn("lines.ownCarrots", choose_no_body)
        self.assertIn("lines.lakeOnly", choose_no_body)
        self.assertIn("lines.bunnyAccepted", choose_no_body)
        self.assertIn(
            'advanceToScene("sunny", [lines.squirrelIntro, lines.squirrelPrompt], flowId)',
            choose_no_body,
        )
        self.assertIn("lines.ownNuts", choose_no_body)
        self.assertIn("lines.lakeWithFriends", choose_no_body)
        self.assertIn("lines.sunnyAccepted", choose_no_body)
        self.assertIn(
            'advanceToScene("fiona", [lines.foxIntro, lines.foxPrompt], flowId)',
            choose_no_body,
        )
        self.assertIn("lines.noChickens", choose_no_body)
        self.assertIn("lines.fionaLakeWithFriends", choose_no_body)
        self.assertIn("lines.fionaAccepted", choose_no_body)
        self.assertIn(
            'advanceToScene("bruno", [lines.badgerIntro, lines.badgerPrompt], flowId)',
            choose_no_body,
        )
        self.assertIn("lines.noDigging", choose_no_body)
        self.assertIn("lines.brunoLakeWithFriends", choose_no_body)
        self.assertIn("lines.brunoAccepted", choose_no_body)
        self.assertIn("lines.gateOpened", choose_no_body)
        self.assertLess(
            choose_no_body.index("lines.brunoAccepted"),
            choose_no_body.index("lines.gateOpened"),
        )
        self.assertGreaterEqual(choose_no_body.count("await playSequence("), 5)
        self.assertIn("setStage(STAGES.chooseBunny)", choose_no_body)
        self.assertIn("if (questioningBunny)", choose_no_body)
        self.assertIn("if (questioningSunny)", choose_no_body)
        self.assertIn("if (questioningFiona)", choose_no_body)
        self.assertIn("if (questioningBruno)", choose_no_body)
        repeat_body = script.split("async function repeatLast()", 1)[1].split(
            "function toggleLanguage()", 1
        )[0]
        self.assertNotIn("chooseYes()", repeat_body)
        self.assertNotIn("chooseNo()", repeat_body)
        self.assertIn("const entry = state.currentEntry || state.lastRepeatable", repeat_body)
        self.assertIn("const flowId = state.flowId", repeat_body)
        self.assertNotIn("++state.flowId", repeat_body)
        self.assertIn(
            "const nextWasAvailable = Boolean(nextResolve && !nextButton.disabled)",
            repeat_body,
        )
        self.assertIn("if (nextWasAvailable) nextButton.disabled = true", repeat_body)
        self.assertIn("if (!resumeEntry)", repeat_body)
        self.assertIn("nextButton.disabled = false", repeat_body)

        repeat_availability = script.split(
            "function updateRepeatAvailability()", 1
        )[1].split("function closeDictionary()", 1)[0]
        self.assertIn("const visibleEntry = state.currentEntry", repeat_availability)
        self.assertIn("state.isSpeakingEntry", repeat_availability)
        self.assertIn("state.isRepeating", repeat_availability)

        play_entry = script.split("async function playEntry(", 1)[1].split(
            "function waitForNext(flowId)", 1
        )[0]
        self.assertIn("state.isSpeakingEntry = true", play_entry)
        self.assertIn("state.isSpeakingEntry = false", play_entry)
        self.assertGreaterEqual(play_entry.count("updateRepeatAvailability()"), 2)


if __name__ == "__main__":
    unittest.main()
