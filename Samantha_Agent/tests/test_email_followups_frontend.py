"""Frozen UI acceptance contract for the registered Luna development task."""
from pathlib import Path
import subprocess
import unittest

from scripts.cockpit_quality_gate import node_binary


class EmailFollowupsFrontendTests(unittest.TestCase):
    def test_manual_followup_ui_contract(self):
        result = subprocess.run([node_binary(), str(Path(__file__).with_name("email_followups_frontend.test.cjs"))],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
