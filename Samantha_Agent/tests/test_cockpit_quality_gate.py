from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.cockpit_quality_gate import (
    ARCHITECTURE_BASELINES,
    COMPILE_PATHS,
    PROJECT_ROOT,
    TEST_MODULES,
    SourceMetrics,
    architecture_messages,
    source_metrics,
)


class CockpitQualityGateTests(unittest.TestCase):
    def test_source_metrics_counts_only_top_level_definitions(self) -> None:
        source = """class Example:
    def nested_method(self):
        return True

def first():
    return 1

async def second():
    return 2
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "sample.py"
            path.write_text(source, encoding="utf-8")

            metrics = source_metrics(path)

        self.assertEqual(metrics, SourceMetrics(lines=9, functions=2, classes=1))

    def test_quality_gate_manifest_paths_and_modules_are_unique(self) -> None:
        self.assertEqual(len(COMPILE_PATHS), len(set(COMPILE_PATHS)))
        self.assertEqual(len(TEST_MODULES), len(set(TEST_MODULES)))
        for relative_path in COMPILE_PATHS:
            self.assertTrue((PROJECT_ROOT / relative_path).is_file(), relative_path)
        self.assertIn("tests.test_cockpit", TEST_MODULES)
        self.assertIn("tests.test_adam_voice_mode", TEST_MODULES)
        self.assertIn("tests.test_cockpit_quality_gate", TEST_MODULES)

    def test_architecture_baselines_are_informational_and_reported(self) -> None:
        messages = architecture_messages()

        self.assertEqual(len(ARCHITECTURE_BASELINES), 2)
        self.assertTrue(any("app/cockpit.py" in message for message in messages))
        self.assertTrue(any("app/speech/adam_voice_mode.py" in message for message in messages))


if __name__ == "__main__":
    unittest.main()
