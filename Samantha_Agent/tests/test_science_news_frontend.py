import subprocess
import unittest
from pathlib import Path
from scripts.cockpit_quality_gate import node_binary
from app.cockpit_frontend import COCKPIT_HTML


class FrontendTests(unittest.TestCase):
    def test_science_news_browser_contract(self):
        result=subprocess.run([node_binary(),'--test',str(Path(__file__).with_name('science_news_frontend.test.cjs'))],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_header_library_and_reduced_motion(self):
        self.assertLess(COCKPIT_HTML.index('id="scienceNewsBtn"'),COCKPIT_HTML.index('</header>'))
        self.assertIn('id="scienceNewsSection"',COCKPIT_HTML)
        self.assertIn('prefers-reduced-motion: reduce',COCKPIT_HTML)
        self.assertIn('ScienceNews',COCKPIT_HTML)
