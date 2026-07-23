from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path

from app.family_calendar_delivery_planner_preview import (
    build_family_calendar_planner_preview,
)
from app.family_calendar_delivery_readiness import (
    FAMILY_CALENDAR_PLANNER_LABEL,
    _planner_document_matches,
)
from scripts.family_calendar_delivery_planner_preview import main


class FamilyCalendarPlannerPreviewTests(unittest.TestCase):
    def test_valid_preview_matches_readiness_contract_without_writes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _preview_paths(Path(temp_dir))
            _write_executable(paths["python"])
            _write_runner(paths["runner"])
            before_python = paths["python"].read_bytes()
            before_runner = paths["runner"].read_bytes()

            result = build_family_calendar_planner_preview(
                python_path=paths["python"],
                runner_path=paths["runner"],
                hour=8,
                minute=15,
            )

            configuration = result.launchd_document()
            self.assertEqual(result.status, "preview")
            self.assertEqual(result.issues, ())
            self.assertIsNotNone(configuration)
            self.assertEqual(configuration["Label"], FAMILY_CALENDAR_PLANNER_LABEL)
            self.assertEqual(
                configuration["StartCalendarInterval"],
                {"Hour": 8, "Minute": 15},
            )
            self.assertFalse(configuration["RunAtLoad"])
            self.assertEqual(configuration["ProcessType"], "Background")
            self.assertTrue(_planner_document_matches(configuration, paths["runner"]))
            self.assertFalse(result.writes_performed)
            self.assertFalse(result.install_called)
            self.assertFalse(result.launchctl_called)
            self.assertFalse(result.secret_read)
            self.assertFalse(result.transport_called)
            self.assertFalse(paths["planner"].exists())
            self.assertEqual(paths["python"].read_bytes(), before_python)
            self.assertEqual(paths["runner"].read_bytes(), before_runner)

    def test_invalid_schedule_or_unsafe_paths_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _preview_paths(Path(temp_dir))
            _write_executable(paths["python"])
            _write_runner(paths["runner"])
            paths["runner"].chmod(0o666)

            result = build_family_calendar_planner_preview(
                python_path=paths["python"],
                runner_path=paths["runner"],
                hour=24,
                minute=-1,
            )

            self.assertEqual(result.status, "invalid")
            self.assertIsNone(result.launchd_document())
            self.assertEqual(
                set(result.issues),
                {
                    "schedule_hour_invalid",
                    "schedule_minute_invalid",
                    "runner_path_unsafe",
                },
            )
            self.assertFalse(paths["planner"].exists())

    def test_safe_virtualenv_symlink_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _preview_paths(Path(temp_dir))
            target = Path(temp_dir) / "framework" / "python"
            _write_executable(target)
            target.chmod(0o775)
            paths["python"].parent.mkdir(parents=True, mode=0o700)
            paths["python"].symlink_to(target)
            _write_runner(paths["runner"])

            result = build_family_calendar_planner_preview(
                python_path=paths["python"],
                runner_path=paths["runner"],
            )

            self.assertEqual(result.status, "preview")
            self.assertEqual(result.issues, ())

    def test_cli_prints_configuration_but_cannot_install_it(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _preview_paths(Path(temp_dir))
            _write_executable(paths["python"])
            _write_runner(paths["runner"])
            output = io.StringIO()

            exit_code = main(
                [
                    "--hour",
                    "7",
                    "--minute",
                    "30",
                    "--python-path",
                    str(paths["python"]),
                    "--runner-path",
                    str(paths["runner"]),
                ],
                output=output,
            )

            document = json.loads(output.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(document["status"], "preview")
            self.assertEqual(
                document["configuration"]["ProgramArguments"],
                [str(paths["python"]), str(paths["runner"])],
            )
            self.assertEqual(
                document["configuration"]["StartCalendarInterval"],
                {"Hour": 7, "Minute": 30},
            )
            self.assertFalse(document["writes_performed"])
            self.assertFalse(document["install_called"])
            self.assertFalse(document["launchctl_called"])
            self.assertFalse(document["secret_read"])
            self.assertFalse(document["transport_called"])
            self.assertTrue(document["redacted"])
            self.assertFalse(paths["planner"].exists())


def _preview_paths(root: Path) -> dict[str, Path]:
    return {
        "python": root / "venv" / "bin" / "python",
        "runner": root / "project" / "family_calendar_delivery_run.py",
        "planner": root / "Library" / "LaunchAgents" / "family-calendar.plist",
    }


def _write_executable(path: Path) -> None:
    path.parent.mkdir(parents=True, mode=0o700)
    path.write_text("#!/bin/sh\n", encoding="utf-8")
    path.chmod(0o700)


def _write_runner(path: Path) -> None:
    path.parent.mkdir(parents=True, mode=0o700)
    path.write_text("# safe runner\n", encoding="utf-8")
    path.chmod(0o600)


if __name__ == "__main__":
    unittest.main()
