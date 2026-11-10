from html.parser import HTMLParser
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[2]


class CompletionLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_banner = False
        self.banner_hidden = False
        self.links = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if attrs.get("id") == "completeBanner":
            self.in_banner = True
            self.banner_hidden = "hidden" in attrs.get("class", "").split()
        if self.in_banner and tag == "a":
            self.links.append(attrs.get("href", ""))

    def handle_endtag(self, tag):
        if self.in_banner and tag == "div":
            self.in_banner = False


class Scene06OpeningLinkTests(unittest.TestCase):
    def test_scene_five_completion_leads_to_the_real_new_scene(self):
        for relative in ("docs", "MatysekANJ/web_mmtx"):
            scene = REPO / relative / "scene05_log_bridge"
            parser = CompletionLinks()
            parser.feed((scene / "index.html").read_text())
            self.assertTrue(parser.banner_hidden)
            self.assertEqual(parser.links, ["../scene06_lake_arrival/index.html"])
            target = (scene / parser.links[0]).resolve()
            self.assertTrue(target.is_file())
            self.assertIn("arrival_side_view.webp", target.read_text())
            # Removed invisible early shortcut stays removed; only completed bridge leads on.
            self.assertNotIn('class="scene-quick-skip"', (scene / "index.html").read_text())

    def test_entry_markup_and_styles_match_in_both_mirrors(self):
        for name in ("index.html", "interaction.css"):
            self.assertEqual((REPO / "docs/scene05_log_bridge" / name).read_bytes(),
                             (REPO / "MatysekANJ/web_mmtx/scene05_log_bridge" / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
