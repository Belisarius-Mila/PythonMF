from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import app_paths


class AppPathsTests(unittest.TestCase):
    def test_mutable_runtime_files_use_application_support_in_source_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            resources = root / "resources"
            support = root / "support"
            resources.mkdir()
            (resources / "user_item_prefs.csv").write_text("prefs-seed\n", encoding="utf-8")
            (resources / "progress.json").write_text('{"seed": true}\n', encoding="utf-8")

            with (
                patch.object(app_paths, "_resource_base_dir", return_value=resources),
                patch.object(app_paths, "_app_support_dir", return_value=support),
            ):
                prefs_path = app_paths.resolve_prefs_path()
                progress_path = app_paths.resolve_progress_path()

            self.assertEqual(prefs_path, support / "user_item_prefs.csv")
            self.assertEqual(progress_path, support / "progress.json")
            self.assertEqual(prefs_path.read_text(encoding="utf-8"), "prefs-seed\n")
            self.assertEqual(progress_path.read_text(encoding="utf-8"), '{"seed": true}\n')

    def test_existing_application_support_file_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            resources = root / "resources"
            support = root / "support"
            resources.mkdir()
            support.mkdir()
            (resources / "progress.json").write_text('{"source": true}\n', encoding="utf-8")
            target = support / "progress.json"
            target.write_text('{"current": true}\n', encoding="utf-8")

            with (
                patch.object(app_paths, "_resource_base_dir", return_value=resources),
                patch.object(app_paths, "_app_support_dir", return_value=support),
            ):
                resolved = app_paths.resolve_progress_path()

            self.assertEqual(resolved, target)
            self.assertEqual(target.read_text(encoding="utf-8"), '{"current": true}\n')


if __name__ == "__main__":
    unittest.main()
