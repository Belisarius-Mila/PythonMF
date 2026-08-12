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
        }
        self.assertEqual({path.name for path in PROTOTYPE_ROOT.iterdir()}, expected)

        html = (PROTOTYPE_ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="languageButton"', html)
        self.assertIn('id="repeatButton"', html)
        self.assertIn('id="yesButton"', html)
        self.assertIn('id="noButton"', html)
        self.assertIn('src="harry_benji_prototype_01.png"', html)

        production_script = (
            PROJECT_ROOT / "docs" / "scene03_journey_to_the_lake" / "script.js"
        ).read_text(encoding="utf-8")
        self.assertNotIn("scene04_harry_guard_prototype", production_script)

    def test_image_has_canonical_scene_dimensions(self) -> None:
        image = PROTOTYPE_ROOT / "harry_benji_prototype_01.png"
        with image.open("rb") as handle:
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
            "async function repeatLast()",
            'characterId !== "benji"',
            "state.stage !== STAGES.chooseYesNo",
            "function updateRepeatAvailability()",
            "STAGES.complete",
        ):
            self.assertIn(expected, script)

        self.assertIn('await speakText(entry.textEn, "en", entry.characterId)', script)
        self.assertIn('if (isBilingual()) await speakText(entry.textCz, "cs", entry.characterId)', script)
        repeat_body = script.split("async function repeatLast()", 1)[1].split(
            "function toggleLanguage()", 1
        )[0]
        self.assertNotIn("chooseYes()", repeat_body)
        self.assertNotIn("chooseNo()", repeat_body)
        self.assertIn("if (!state.lastRepeatable || repeatButton.disabled) return", repeat_body)


if __name__ == "__main__":
    unittest.main()
