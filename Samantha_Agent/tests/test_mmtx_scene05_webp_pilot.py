from __future__ import annotations

import unittest
from pathlib import Path

from PIL import Image


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DOCS_SCENE = REPOSITORY_ROOT / "docs" / "scene05_log_bridge"
MIRROR_SCENE = REPOSITORY_ROOT / "MatysekANJ" / "web_mmtx" / "scene05_log_bridge"
EXPECTED_SIZE = (1672, 941)


class MmtxScene05WebpPilotTests(unittest.TestCase):
    def test_webp_candidates_keep_full_scene_dimensions(self) -> None:
        for filename in ("scene05_stream_base_q90.webp", "scene05_stream_base_q85.webp"):
            with Image.open(DOCS_SCENE / filename) as image:
                self.assertEqual(image.size, EXPECTED_SIZE)
                self.assertEqual(image.format, "WEBP")

    def test_webp_candidates_are_smaller_without_replacing_png(self) -> None:
        source = DOCS_SCENE / "scene05_stream_base.png"
        q90 = DOCS_SCENE / "scene05_stream_base_q90.webp"
        q85 = DOCS_SCENE / "scene05_stream_base_q85.webp"

        self.assertTrue(source.exists())
        self.assertLess(q90.stat().st_size, source.stat().st_size)
        self.assertLess(q85.stat().st_size, q90.stat().st_size)

    def test_docs_and_source_mirror_are_identical(self) -> None:
        for filename in (
            "scene05_stream_base_q90.webp",
            "scene05_stream_base_q85.webp",
            "webp_quality_pilot.html",
        ):
            self.assertEqual(
                (DOCS_SCENE / filename).read_bytes(),
                (MIRROR_SCENE / filename).read_bytes(),
            )

    def test_comparison_page_links_all_three_variants(self) -> None:
        page = (DOCS_SCENE / "webp_quality_pilot.html").read_text(encoding="utf-8")
        self.assertIn("scene05_stream_base.png", page)
        self.assertIn("scene05_stream_base_q90.webp", page)
        self.assertIn("scene05_stream_base_q85.webp", page)
        self.assertIn("1672 × 941", page)

    def test_q90_is_recorded_as_the_selected_production_quality(self) -> None:
        page = (DOCS_SCENE / "webp_quality_pilot.html").read_text(encoding="utf-8")

        self.assertIn("Vybraná produkční kvalita je WebP q90", page)
        self.assertIn(
            '<button type="button" data-index="1" aria-pressed="true">',
            page,
        )
        self.assertIn(
            '<img id="scene" src="scene05_stream_base_q90.webp"',
            page,
        )
        self.assertIn("let selected = 1;", page)

    def test_scene_page_uses_approved_bridge_supports_and_final_webp(self) -> None:
        page = (DOCS_SCENE / "index.html").read_text(encoding="utf-8")

        self.assertIn(
            '<source srcset="scene05_log_bridge_supports.webp" type="image/webp">',
            page,
        )
        self.assertIn('href="scene05_log_bridge_supports.webp"', page)
        self.assertIn('src="scene05_log_bridge_supports.webp"', page)
        self.assertIn('src="scene05_log_bridge_crooked_trees.webp"', page)
        self.assertIn('data-scene-state="bridge-supports"', page)
        self.assertIn('width="1672"', page)
        self.assertIn('height="941"', page)
        self.assertNotIn("scene05_stream_base_q90.webp", page)
        self.assertNotIn('src="scene05_stream_base.png"', page)
        self.assertNotIn("scene05_stream_base_q85.webp", page)

    def test_scene_page_is_standalone_and_keeps_story_flow_unwired(self) -> None:
        page = (DOCS_SCENE / "index.html").read_text(encoding="utf-8")

        self.assertIn("Scene 5 · The Log Bridge", page)
        self.assertIn("Scéna 5 · Most z klád", page)
        self.assertIn('../scene04_harry_guard_prototype/index.html', page)

        scene_four_script = (
            REPOSITORY_ROOT
            / "docs"
            / "scene04_harry_guard_prototype"
            / "script.js"
        ).read_text(encoding="utf-8")
        self.assertNotIn("scene05_log_bridge", scene_four_script)

    def test_scene_page_and_styles_match_source_mirror(self) -> None:
        for filename in ("index.html", "styles.css"):
            self.assertEqual(
                (DOCS_SCENE / filename).read_bytes(),
                (MIRROR_SCENE / filename).read_bytes(),
            )

    def test_first_story_image_preserves_source_and_production_dimensions(self) -> None:
        source = DOCS_SCENE / "assets" / "scene05_arrival_logan_01_source.png"
        production_png = DOCS_SCENE / "scene05_arrival_logan_01.png"
        production_webp = DOCS_SCENE / "scene05_arrival_logan_01_q90.webp"

        with Image.open(source) as image:
            self.assertEqual(image.size, (1671, 941))
            self.assertEqual(image.format, "PNG")

        for path, expected_format in (
            (production_png, "PNG"),
            (production_webp, "WEBP"),
        ):
            with Image.open(path) as image:
                self.assertEqual(image.size, EXPECTED_SIZE)
                self.assertEqual(image.format, expected_format)

        self.assertLess(production_webp.stat().st_size, production_png.stat().st_size)

    def test_first_story_image_matches_source_mirror(self) -> None:
        for filename in (
            "assets/scene05_arrival_logan_01_source.png",
            "scene05_arrival_logan_01.png",
            "scene05_arrival_logan_01_q90.webp",
        ):
            self.assertEqual(
                (DOCS_SCENE / filename).read_bytes(),
                (MIRROR_SCENE / filename).read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
