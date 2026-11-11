from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from scripts.cockpit_quality_gate import node_binary

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
MIRROR = ROOT / "MatysekANJ" / "web_mmtx"


class MmtxFriendsControlsTests(unittest.TestCase):
    def test_sentence_player_modes_cancellation_and_full_game_flow(self):
        # Exercise the same restricted PATH as the release service.
        with mock.patch.dict(os.environ, {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin"}):
            node = node_binary()
        result = subprocess.run(
            [node, str(Path(__file__).with_name("mmtx_friends_controls.js"))],
            capture_output=True, text=True, timeout=30, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("four chapters and game actions: OK", result.stdout)

    def test_player_is_loaded_before_the_story_and_both_web_roots_match(self):
        html = (DOCS / "index.html").read_text()
        self.assertLess(html.index('src="friends_player.js?'), html.index('src="script_intro_v2.js?'))
        for name in ("index.html", "script_intro_v2.js", "styles_intro_v2.css", "friends_player.js"):
            self.assertEqual((DOCS / name).read_bytes(), (MIRROR / name).read_bytes(), name)
        for element in ("friendsPlayer", "friendsLanguage", "friendsNext", "friendsRepeat", "friendsCzech"):
            self.assertIn(f'id="{element}"', html)


if __name__ == "__main__":
    unittest.main()
