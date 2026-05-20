import importlib.util
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "daily_3am.py"
SPEC = importlib.util.spec_from_file_location("daily_3am", SCRIPT_PATH)
daily_3am = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["daily_3am"] = daily_3am
SPEC.loader.exec_module(daily_3am)


class Daily3AmTests(unittest.TestCase):
    def test_first_run_marks_day_completed_and_second_run_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            log_file = project_dir / "logs" / "daily_3am.log"
            state_dir = project_dir / "data" / "daily_3am"

            first = daily_3am.main(
                [
                    "--project-dir",
                    str(project_dir),
                    "--log-file",
                    str(log_file),
                    "--state-dir",
                    str(state_dir),
                    "--run-date",
                    "2026-05-20",
                ]
            )
            second = daily_3am.main(
                [
                    "--project-dir",
                    str(project_dir),
                    "--log-file",
                    str(log_file),
                    "--state-dir",
                    str(state_dir),
                    "--run-date",
                    "2026-05-20",
                ]
            )

            self.assertEqual(first, daily_3am.EXIT_OK)
            self.assertEqual(second, daily_3am.EXIT_OK)
            state = daily_3am.read_state(state_dir / "2026-05-20.json")
            self.assertEqual(state["status"], "completed")
            self.assertTrue(log_file.exists())

    def test_lock_refuses_parallel_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            context = daily_3am.DailyContext(
                project_dir=project_dir,
                log_file=project_dir / "logs" / "daily_3am.log",
                state_dir=project_dir / "data" / "daily_3am",
                run_date="2026-05-20",
                started_at=datetime.now(daily_3am.PRAGUE_TZ).isoformat(),
                dry_run=False,
                force=False,
            )
            daily_3am.setup_logging(context.log_file)

            with daily_3am.FileLock(context.state_dir / "daily_3am.lock"):
                result = daily_3am.main(
                    [
                        "--project-dir",
                        str(project_dir),
                        "--log-file",
                        str(context.log_file),
                        "--state-dir",
                        str(context.state_dir),
                        "--run-date",
                        "2026-05-20",
                    ]
                )

            self.assertEqual(result, daily_3am.EXIT_ALREADY_RUNNING)

    def test_dry_run_does_not_mark_day_completed(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            state_dir = project_dir / "data" / "daily_3am"
            result = daily_3am.main(
                [
                    "--project-dir",
                    str(project_dir),
                    "--log-file",
                    str(project_dir / "logs" / "daily_3am.log"),
                    "--state-dir",
                    str(state_dir),
                    "--run-date",
                    "2026-05-20",
                    "--dry-run",
                ]
            )

            self.assertEqual(result, daily_3am.EXIT_OK)
            self.assertFalse((state_dir / "2026-05-20.json").exists())

    def test_invalid_run_date_returns_setup_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            result = daily_3am.main(
                [
                    "--project-dir",
                    str(project_dir),
                    "--run-date",
                    "20-05-2026",
                ]
            )

            self.assertEqual(result, daily_3am.EXIT_SETUP_ERROR)


if __name__ == "__main__":
    unittest.main()
