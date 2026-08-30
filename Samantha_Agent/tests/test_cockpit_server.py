from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.cockpit_server import load_cockpit_environment


class CockpitServerEnvironmentTests(unittest.TestCase):
    def test_loads_missing_value_from_local_dotenv(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("SAMANTHA_TEST_COCKPIT_ENV=from-dotenv\n", encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True):
                loaded = load_cockpit_environment(env_path)

                self.assertTrue(loaded)
                self.assertEqual(os.environ["SAMANTHA_TEST_COCKPIT_ENV"], "from-dotenv")

    def test_preserves_process_environment_value(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("SAMANTHA_TEST_COCKPIT_ENV=from-dotenv\n", encoding="utf-8")
            with patch.dict(
                os.environ,
                {"SAMANTHA_TEST_COCKPIT_ENV": "from-process"},
                clear=False,
            ):
                loaded = load_cockpit_environment(env_path)

                self.assertTrue(loaded)
                self.assertEqual(os.environ["SAMANTHA_TEST_COCKPIT_ENV"], "from-process")


if __name__ == "__main__":
    unittest.main()
