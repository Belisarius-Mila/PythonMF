import importlib.util
import json
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

    def test_hour_window_allows_delayed_same_day_run(self):
        now = datetime(2026, 5, 23, 21, 59, tzinfo=daily_3am.PRAGUE_TZ)

        self.assertTrue(daily_3am.is_within_hour_window(now, 17, 5))

    def test_hour_window_rejects_after_tolerance(self):
        now = datetime(2026, 5, 23, 22, 1, tzinfo=daily_3am.PRAGUE_TZ)

        self.assertFalse(daily_3am.is_within_hour_window(now, 17, 5))

    def test_hour_window_handles_midnight_wrap(self):
        now = datetime(2026, 5, 24, 2, 30, tzinfo=daily_3am.PRAGUE_TZ)

        self.assertTrue(daily_3am.is_within_hour_window(now, 22, 5))

    def test_time_gate_requires_complete_window_args(self):
        args = daily_3am.parse_args(["--window-start-hour", "17"])

        with self.assertRaises(ValueError):
            daily_3am.validate_time_gate_args(args)

    def test_colors_numbers_owl_task_generates_one_off_audio(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            project_dir = repo_root / "Samantha_Agent"
            app_dir = repo_root / "ColorsAndNumbers" / "web_colors_numbers"
            project_dir.mkdir()
            app_dir.mkdir(parents=True)
            script_path = app_dir / "app.js"
            script_path.write_text('const owlAudio = new Audio("old.mp3?v=1");\n', encoding="utf-8")
            config_path = project_dir / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "date": "2026-05-23",
                        "text_cs": "Test text",
                        "audio_src": "owl_230526.mp3?v=20260523a",
                        "output_relative_path": "../ColorsAndNumbers/web_colors_numbers/owl_230526.mp3",
                        "script_relative_path": "../ColorsAndNumbers/web_colors_numbers/app.js",
                        "voice": "cs-CZ-AntoninNeural",
                        "rate": "-10%",
                    }
                ),
                encoding="utf-8",
            )
            context = daily_3am.DailyContext(
                project_dir=project_dir,
                log_file=project_dir / "logs" / "daily_3am.log",
                state_dir=project_dir / "data" / "daily_3am",
                run_date="2026-05-23",
                started_at=datetime.now(daily_3am.PRAGUE_TZ).isoformat(),
                dry_run=False,
                force=False,
            )

            result = daily_3am.run_colors_numbers_owl_task(
                context,
                config_path=config_path,
                speech_csv_path=project_dir / "missing_owl_speech.csv",
                audio_generator=lambda text, output, voice, rate: output.write_bytes(b"mp3"),
            )

            self.assertEqual(result["status"], "completed")
            self.assertEqual((app_dir / "owl_230526.mp3").read_bytes(), b"mp3")
            self.assertIn('new Audio("owl_230526.mp3?v=20260523a")', script_path.read_text(encoding="utf-8"))
            self.assertEqual(
                result["changed_files"],
                [
                    "ColorsAndNumbers/web_colors_numbers/owl_230526.mp3",
                    "ColorsAndNumbers/web_colors_numbers/app.js",
                ],
            )

    def test_colors_numbers_owl_task_skips_other_dates(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "Samantha_Agent"
            project_dir.mkdir()
            config_path = project_dir / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "date": "2026-05-23",
                        "text_cs": "Test text",
                        "audio_src": "owl_230526.mp3?v=20260523a",
                        "output_relative_path": "../ColorsAndNumbers/web_colors_numbers/owl_230526.mp3",
                        "script_relative_path": "../ColorsAndNumbers/web_colors_numbers/app.js",
                        "voice": "cs-CZ-AntoninNeural",
                        "rate": "-10%",
                    }
                ),
                encoding="utf-8",
            )
            context = daily_3am.DailyContext(
                project_dir=project_dir,
                log_file=project_dir / "logs" / "daily_3am.log",
                state_dir=project_dir / "data" / "daily_3am",
                run_date="2026-05-22",
                started_at=datetime.now(daily_3am.PRAGUE_TZ).isoformat(),
                dry_run=False,
                force=False,
            )

            result = daily_3am.run_colors_numbers_owl_task(
                context,
                config_path=config_path,
                speech_csv_path=project_dir / "missing_owl_speech.csv",
                audio_generator=lambda text, output, voice, rate: output.write_bytes(b"mp3"),
            )

            self.assertEqual(result["status"], "skipped")
            self.assertEqual(result["scheduled_date"], "2026-05-23")

    def test_colors_numbers_owl_task_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            project_dir = repo_root / "Samantha_Agent"
            app_dir = repo_root / "ColorsAndNumbers" / "web_colors_numbers"
            project_dir.mkdir()
            app_dir.mkdir(parents=True)
            script_path = app_dir / "app.js"
            script_path.write_text('const owlAudio = new Audio("old.mp3?v=1");\n', encoding="utf-8")
            config_path = project_dir / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "date": "2026-05-23",
                        "text_cs": "Test text",
                        "audio_src": "owl_230526.mp3?v=20260523a",
                        "output_relative_path": "../ColorsAndNumbers/web_colors_numbers/owl_230526.mp3",
                        "script_relative_path": "../ColorsAndNumbers/web_colors_numbers/app.js",
                        "voice": "cs-CZ-AntoninNeural",
                        "rate": "-10%",
                    }
                ),
                encoding="utf-8",
            )
            context = daily_3am.DailyContext(
                project_dir=project_dir,
                log_file=project_dir / "logs" / "daily_3am.log",
                state_dir=project_dir / "data" / "daily_3am",
                run_date="2026-05-23",
                started_at=datetime.now(daily_3am.PRAGUE_TZ).isoformat(),
                dry_run=True,
                force=False,
            )

            result = daily_3am.run_colors_numbers_owl_task(
                context,
                config_path=config_path,
                speech_csv_path=project_dir / "missing_owl_speech.csv",
                audio_generator=lambda text, output, voice, rate: output.write_bytes(b"mp3"),
            )

            self.assertEqual(result["status"], "planned")
            self.assertFalse((app_dir / "owl_230526.mp3").exists())
            self.assertIn("old.mp3?v=1", script_path.read_text(encoding="utf-8"))

    def test_colors_numbers_owl_task_generates_daily_csv_audio(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            project_dir = repo_root / "Samantha_Agent"
            app_dir = repo_root / "ColorsAndNumbers" / "web_colors_numbers"
            docs_dir = repo_root / "docs" / "colors-numbers"
            project_dir.mkdir()
            app_dir.mkdir(parents=True)
            docs_dir.mkdir(parents=True)
            for script_path in (app_dir / "app.js", docs_dir / "app.js"):
                script_path.write_text('const owlAudio = new Audio("old.mp3?v=1");\n', encoding="utf-8")
            csv_path = project_dir / "OwlSpeech.csv"
            csv_path.write_text(
                "\n".join(
                    [
                        "date,part_a,part_b,part_c,full_text",
                        '2026-05-28,A,B,C,"Daily test text"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            context = daily_3am.DailyContext(
                project_dir=project_dir,
                log_file=project_dir / "logs" / "daily_3am.log",
                state_dir=project_dir / "data" / "daily_3am",
                run_date="2026-05-28",
                started_at=datetime.now(daily_3am.PRAGUE_TZ).isoformat(),
                dry_run=False,
                force=False,
            )

            result = daily_3am.run_colors_numbers_owl_task(
                context,
                speech_csv_path=csv_path,
                audio_generator=lambda text, output, voice, rate: output.write_bytes(
                    f"{text}|{voice}|{rate}".encode("utf-8")
                ),
            )

            self.assertEqual(result["status"], "completed")
            self.assertEqual((app_dir / "owl_280526.mp3").read_bytes(), (docs_dir / "owl_280526.mp3").read_bytes())
            self.assertIn('new Audio("owl_280526.mp3?v=20260528a")', (app_dir / "app.js").read_text(encoding="utf-8"))
            self.assertIn('new Audio("owl_280526.mp3?v=20260528a")', (docs_dir / "app.js").read_text(encoding="utf-8"))
            self.assertEqual(
                result["changed_files"],
                [
                    "ColorsAndNumbers/web_colors_numbers/owl_280526.mp3",
                    "docs/colors-numbers/owl_280526.mp3",
                    "ColorsAndNumbers/web_colors_numbers/app.js",
                    "docs/colors-numbers/app.js",
                ],
            )


if __name__ == "__main__":
    unittest.main()
