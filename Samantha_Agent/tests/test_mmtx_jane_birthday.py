from __future__ import annotations

import hashlib
import struct
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = PROJECT_ROOT / "docs"
MIRROR_ROOT = PROJECT_ROOT / "MatysekANJ" / "web_mmtx"
JANE_SCENE = DOCS_ROOT / "scene_jane_birthday"
JANE_MIRROR = MIRROR_ROOT / "scene_jane_birthday"
KATE_SCENE = DOCS_ROOT / "scene_kate_birthday"


class MmtxJaneBirthdayTests(unittest.TestCase):
    def test_jane_scene_and_project_mirror_are_identical(self) -> None:
        docs_files = {
            path.relative_to(JANE_SCENE) for path in JANE_SCENE.rglob("*") if path.is_file()
        }
        mirror_files = {
            path.relative_to(JANE_MIRROR) for path in JANE_MIRROR.rglob("*") if path.is_file()
        }
        self.assertEqual(docs_files, mirror_files)
        self.assertEqual(len(docs_files), 27)

        for relative in docs_files:
            with self.subTest(relative=str(relative)):
                self.assertEqual(
                    (JANE_SCENE / relative).read_bytes(),
                    (JANE_MIRROR / relative).read_bytes(),
                )

        for filename in ("index.html", "script_intro_v2.js", "styles_intro_v2.css"):
            with self.subTest(filename=filename):
                self.assertEqual(
                    (DOCS_ROOT / filename).read_bytes(),
                    (MIRROR_ROOT / filename).read_bytes(),
                )

    def test_jane_portal_is_available_from_the_forest_crossroads(self) -> None:
        html = (DOCS_ROOT / "index.html").read_text(encoding="utf-8")
        script = (DOCS_ROOT / "script_intro_v2.js").read_text(encoding="utf-8")
        styles = (DOCS_ROOT / "styles_intro_v2.css").read_text(encoding="utf-8")

        self.assertIn('id="janeBirthdayPortalButton"', html)
        self.assertIn('aria-label="Jane birthday"', html)
        self.assertIn("Jane<br>birthday", html)
        self.assertIn("styles_intro_v2.css?v=20260825jane1", html)
        self.assertIn("script_intro_v2.js?v=20260825jane1", html)
        self.assertIn('window.location.href = "scene_jane_birthday/index.html"', script)
        self.assertIn("janeBirthdayPortalButton.classList.toggle", script)
        self.assertIn("janeBirthdayPortalButton.addEventListener", script)
        self.assertIn(".jane-birthday-portal {", styles)
        self.assertIn(".jane-birthday-portal-label {", styles)

    def test_jane_dialogue_contains_the_approved_wishes(self) -> None:
        script = (JANE_SCENE / "script.js").read_text(encoding="utf-8")
        html = (JANE_SCENE / "index.html").read_text(encoding="utf-8")
        readme = (JANE_SCENE / "README.md").read_text(encoding="utf-8")
        svg = (JANE_SCENE / "jane_birthday_clearing.svg").read_text(encoding="utf-8")

        expected_text = (
            "Jane, today is your birthday. I wish you good health and lots of energy.",
            "I wish you happiness and many reasons to smile.",
            "I wish you good friends and many happy adventures.",
            "I wish you a lovely party full of laughter.",
            "I wish you beautiful dreams that come true.",
            "Jane, today is your special day.",
            "Your forest friends are here for you.",
            "Jane, dnes máš narozeniny. Přeji ti hodně zdraví a energie.",
            "Přeji ti štěstí a mnoho důvodů k úsměvu.",
            "Přeji ti dobré kamarády a mnoho veselých dobrodružství.",
            "Přeji ti krásnou oslavu plnou smíchu.",
            "Přeji ti krásné sny, které se splní.",
        )
        for phrase in expected_text:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, script)

        for text in (script, html, readme, svg):
            self.assertNotIn("Kate", text)
        self.assertIn("Jane - birthday", html)
        self.assertIn("Happy birthday, Jane!", html)
        self.assertIn('src="jane_birthday_clearing.png?v=20260825a"', html)
        self.assertIn("`džejn`", readme)
        self.assertIn("Jane birthday forest clearing", svg)
        self.assertIn(">Jane</text>", svg)

    def test_jane_audio_set_is_complete_and_valid(self) -> None:
        expected_english = {
            f"jane_birthday_{index:02d}_{slug}_{kind}_en.mp3"
            for index, slug, kind in (
                (1, "benji", "hello"),
                (2, "benji", "wish"),
                (3, "bunny", "hello"),
                (4, "bunny", "wish"),
                (5, "bruno", "hello"),
                (6, "bruno", "wish"),
                (7, "fiona", "hello"),
                (8, "fiona", "wish"),
                (9, "sunny", "hello"),
                (10, "sunny", "wish"),
            )
        } | {"jane_birthday_11_song_en.mp3"}
        expected_czech = {
            f"jane_birthday_{index:02d}_{slug}_{kind}_cz.mp3"
            for index, slug, kind in (
                (1, "benji", "hello"),
                (2, "benji", "wish"),
                (3, "bunny", "hello"),
                (4, "bunny", "wish"),
                (5, "bruno", "hello"),
                (6, "bruno", "wish"),
                (7, "fiona", "hello"),
                (8, "fiona", "wish"),
                (9, "sunny", "hello"),
                (10, "sunny", "wish"),
            )
        }
        english_root = JANE_SCENE / "audio" / "english"
        czech_root = JANE_SCENE / "audio" / "czech"
        self.assertEqual({path.name for path in english_root.iterdir()}, expected_english)
        self.assertEqual({path.name for path in czech_root.iterdir()}, expected_czech)

        for audio in [*english_root.iterdir(), *czech_root.iterdir()]:
            with self.subTest(audio=audio.name):
                payload = audio.read_bytes()
                self.assertGreater(len(payload), 8000)
                self.assertTrue(
                    payload.startswith(b"ID3")
                    or payload[:2] in {b"\xff\xf3", b"\xff\xfb"}
                )

    def test_unchanged_hello_tracks_are_reused_from_kate(self) -> None:
        for language, suffix in (("english", "en"), ("czech", "cz")):
            for index, speaker in ((1, "benji"), (3, "bunny"), (5, "bruno"), (7, "fiona"), (9, "sunny")):
                jane = JANE_SCENE / "audio" / language / (
                    f"jane_birthday_{index:02d}_{speaker}_hello_{suffix}.mp3"
                )
                kate = KATE_SCENE / "audio" / language / (
                    f"kate_birthday_{index:02d}_{speaker}_hello_{suffix}.mp3"
                )
                with self.subTest(language=language, speaker=speaker):
                    self.assertEqual(
                        hashlib.sha256(jane.read_bytes()).digest(),
                        hashlib.sha256(kate.read_bytes()).digest(),
                    )

    def test_scene_image_has_canonical_dimensions(self) -> None:
        image = JANE_SCENE / "jane_birthday_clearing.png"
        with image.open("rb") as handle:
            self.assertEqual(handle.read(8), b"\x89PNG\r\n\x1a\n")
            chunk_length = struct.unpack(">I", handle.read(4))[0]
            self.assertEqual(handle.read(4), b"IHDR")
            width, height = struct.unpack(">II", handle.read(8))
        self.assertEqual(chunk_length, 13)
        self.assertEqual((width, height), (1672, 941))


if __name__ == "__main__":
    unittest.main()
