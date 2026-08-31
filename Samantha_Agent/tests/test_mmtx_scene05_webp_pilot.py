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


if __name__ == "__main__":
    unittest.main()
