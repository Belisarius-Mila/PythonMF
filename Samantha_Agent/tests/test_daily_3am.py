import importlib.util
import json
import sys
import tempfile
import unittest
from contextlib import nullcontext
from datetime import datetime
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "daily_3am.py"
WORKFLOW_PATH = (
    Path(__file__).resolve().parents[2]
    / ".github"
    / "workflows"
    / "samantha-daily-3am.yml"
)
SPEC = importlib.util.spec_from_file_location("daily_3am", SCRIPT_PATH)
daily_3am = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["daily_3am"] = daily_3am
SPEC.loader.exec_module(daily_3am)


class Daily3AmTests(unittest.TestCase):
    def test_github_workflow_deploys_pages_without_writing_main(self):
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("contents: read", workflow)
        self.assertIn("pages: write", workflow)
        self.assertIn("id-token: write", workflow)
        self.assertIn("actions/configure-pages@v5", workflow)
        self.assertIn("actions/upload-pages-artifact@v4", workflow)
        self.assertIn("actions/deploy-pages@v4", workflow)
        self.assertIn("path: ./docs", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertNotIn("git add", workflow)
        self.assertNotIn("git commit", workflow)
        self.assertNotIn("git push", workflow)
        self.assertIn("python scripts/daily_3am.py --publish-owl", workflow)
        self.assertNotIn("--window-start-hour", workflow)
        self.assertNotIn("continue-on-error", workflow)
        self.assertLess(workflow.index("--publish-owl"), workflow.index("actions/upload-pages-artifact"))
        self.assertIn("needs: build-pages", workflow)
        self.assertEqual(workflow, (SCRIPT_PATH.parents[1] / '.github/workflows/samantha-daily-3am.yml').read_text())

    def publication_fixture(self, root):
        project = root / 'Samantha_Agent'
        (project / 'config').mkdir(parents=True)
        (project / 'config/OwlSpeech.csv').write_text('date,full_text\n2026-09-29,Exact daily text\ndefault,Fallback\n')
        for directory in daily_3am.COLORS_NUMBERS_ALLOWED_DIRS:
            target = root / directory
            target.mkdir(parents=True)
            (target / 'app.js').write_text('const owlAudio = new Audio("old.mp3?v=1");\n')
            (target / 'index.html').write_text('<html><script src="app.js?v=old"></script></html>')
        now = datetime(2026, 9, 29, 8, 13, tzinfo=daily_3am.PRAGUE_TZ)
        context = daily_3am.build_context(daily_3am.parse_args(['--project-dir',str(project),'--publish-owl']), now)
        return context, now

    def test_publication_runs_late_despite_completed_state_and_busts_both_caches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context, now = self.publication_fixture(root)
            daily_3am.mark_completed(context, {'tasks': []})
            calls = []
            def generate(text, output, voice, rate):
                calls.append(text)
                output.write_bytes(b'ID3' + bytes([len(calls)]) * 200)
            index_versions = []
            for _ in range(2):
                self.assertEqual(daily_3am.run_owl_publication(context, audio_generator=generate, clock=lambda:now),0)
                scripts = [(root/d/'app.js').read_text() for d in daily_3am.COLORS_NUMBERS_ALLOWED_DIRS]
                self.assertEqual(scripts[0], scripts[1])
                self.assertRegex(scripts[0], r'owl_290926\.mp3\?v=20260929a-[0-9a-f]{12}')
                index_versions.append((root/daily_3am.DOCS_COLORS_NUMBERS_APP_DIR/'index.html').read_text())
                self.assertNotIn('app.js?v=old', index_versions[-1])
            self.assertEqual(calls,['Exact daily text','Exact daily text'])
            self.assertNotEqual(index_versions[0], index_versions[1])

    def test_publication_rejects_missing_text_invalid_audio_and_old_selector(self):
        for failure in ('missing_csv','missing_row','empty','not_mp3','old_selector','duplicate_selector','missing_index'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                context,now=self.publication_fixture(root)
                csv=context.project_dir/'config/OwlSpeech.csv'
                if failure=='missing_csv': csv.rename(csv.with_suffix('.saved'))
                if failure=='missing_row': csv.write_text('date,full_text\n2026-09-28,Yesterday\n')
                target=root/daily_3am.DOCS_COLORS_NUMBERS_APP_DIR
                if failure=='duplicate_selector':
                    with (target/'app.js').open('a') as stream: stream.write('const owlAudio = new Audio("extra.mp3");')
                if failure=='missing_index': (target/'index.html').write_text('<html>No script</html>')
                def generate(text,output,voice,rate):
                    output.write_bytes(b'' if failure=='empty' else b'not audio'*100 if failure=='not_mp3' else b'ID3'+b'x'*200)
                with patch.object(daily_3am,'update_owl_audio_source',return_value=False) if failure=='old_selector' else nullcontext():
                    with self.assertRaises(daily_3am.DailyTaskError):
                        daily_3am.run_owl_publication(context,audio_generator=generate,clock=lambda:now)

    def test_publication_fails_on_tts_error_midnight_and_forbidden_modes(self):
        with tempfile.TemporaryDirectory() as tmp:
            context,now=self.publication_fixture(Path(tmp))
            with self.assertRaises(daily_3am.DailyTaskError), patch.object(daily_3am,'generate_mp3',side_effect=daily_3am.DailyTaskError('TTS failed')):
                daily_3am.run_owl_publication(context,clock=lambda:now)
            moments=iter([now,now.replace(day=30)])
            with self.assertRaises(daily_3am.DailyTaskError):
                daily_3am.run_owl_publication(context,clock=lambda:next(moments),
                    audio_generator=lambda text,output,voice,rate:output.write_bytes(b'ID3'+b'x'*200))
        for extra in (['--dry-run'],['--local-preview'],['--run-date','2026-09-28'],
                      ['--only-at-hour','3'],['--window-start-hour','3','--window-hours','5']):
            with self.subTest(extra=extra),self.assertRaises(ValueError):
                daily_3am.validate_time_gate_args(daily_3am.parse_args(['--publish-owl',*extra]))

    def test_publication_cli_failure_is_not_a_successful_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            project=Path(tmp)/'Samantha_Agent'
            project.mkdir()
            self.assertEqual(daily_3am.main(['--project-dir',str(project),'--publish-owl']),daily_3am.EXIT_TASK_ERROR)

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

    def test_local_preview_rejects_dry_run_and_schedule_gate(self):
        for argv in (
            ["--local-preview", "--dry-run"],
            ["--local-preview", "--only-at-hour", "3"],
            ["--local-preview", "--window-start-hour", "3", "--window-hours", "5"],
        ):
            with self.subTest(argv=argv):
                args = daily_3am.parse_args(argv)
                with self.assertRaises(ValueError):
                    daily_3am.validate_time_gate_args(args)

    def test_local_preview_only_writes_ignored_preview_and_no_daily_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            project_dir = repo_root / "Samantha_Agent"
            state_dir = project_dir / "data" / "daily_3am"
            config_dir = project_dir / "config"
            app_dir = repo_root / "ColorsAndNumbers" / "web_colors_numbers"
            docs_dir = repo_root / "docs" / "colors-numbers"
            config_dir.mkdir(parents=True)
            app_dir.mkdir(parents=True)
            docs_dir.mkdir(parents=True)
            csv_path = config_dir / "OwlSpeech.csv"
            csv_path.write_text(
                "\n".join(
                    [
                        "date,part_a,part_b,part_c,full_text",
                        '2026-05-28,A,B,C,"Preview text"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            public_scripts = (app_dir / "app.js", docs_dir / "app.js")
            for script_path in public_scripts:
                script_path.write_text(
                    'const owlAudio = new Audio("published.mp3?v=1");\n',
                    encoding="utf-8",
                )

            def fake_generate(text, output, voice, rate):
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(f"{text}|{voice}|{rate}".encode("utf-8"))

            with patch.object(daily_3am, "generate_mp3", side_effect=fake_generate):
                result = daily_3am.main(
                    [
                        "--project-dir",
                        str(project_dir),
                        "--state-dir",
                        str(state_dir),
                        "--log-file",
                        str(project_dir / "logs" / "daily_3am.log"),
                        "--run-date",
                        "2026-05-28",
                        "--local-preview",
                    ]
                )

            preview_path = state_dir / "previews" / "owl_280526.mp3"
            self.assertEqual(result, daily_3am.EXIT_OK)
            self.assertIn(b"Preview text", preview_path.read_bytes())
            self.assertFalse((state_dir / "2026-05-28.json").exists())
            self.assertFalse((app_dir / "owl_280526.mp3").exists())
            self.assertFalse((docs_dir / "owl_280526.mp3").exists())
            for script_path in public_scripts:
                self.assertEqual(
                    script_path.read_text(encoding="utf-8"),
                    'const owlAudio = new Audio("published.mp3?v=1");\n',
                )

    def test_local_preview_replaces_only_its_task_owned_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "Samantha_Agent"
            state_dir = project_dir / "data" / "daily_3am"
            config_dir = project_dir / "config"
            config_dir.mkdir(parents=True)
            csv_path = config_dir / "OwlSpeech.csv"
            csv_path.write_text(
                "\n".join(
                    [
                        "date,part_a,part_b,part_c,full_text",
                        '2026-05-28,A,B,C,"Replacement preview"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            context = daily_3am.DailyContext(
                project_dir=project_dir,
                log_file=project_dir / "logs" / "daily_3am.log",
                state_dir=state_dir,
                run_date="2026-05-28",
                started_at=datetime.now(daily_3am.PRAGUE_TZ).isoformat(),
                dry_run=False,
                force=False,
            )
            preview_path = state_dir / "previews" / "owl_280526.mp3"
            preview_path.parent.mkdir(parents=True)
            preview_path.write_bytes(b"old preview")

            result = daily_3am.run_colors_numbers_owl_local_preview(
                context,
                audio_generator=lambda text, output, voice, rate: output.write_bytes(
                    text.encode("utf-8")
                ),
            )

            self.assertEqual(result["status"], "completed")
            self.assertFalse(result["public_files_changed"])
            self.assertFalse(result["daily_state_changed"])
            self.assertEqual(preview_path.read_bytes(), b"Replacement preview")

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

    def test_colors_numbers_owl_task_force_regenerates_existing_daily_audio(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            project_dir = repo_root / "Samantha_Agent"
            app_dir = repo_root / "ColorsAndNumbers" / "web_colors_numbers"
            docs_dir = repo_root / "docs" / "colors-numbers"
            project_dir.mkdir()
            app_dir.mkdir(parents=True)
            docs_dir.mkdir(parents=True)
            audio_src = "owl_280526.mp3?v=20260528a"
            for target_dir in (app_dir, docs_dir):
                (target_dir / "app.js").write_text(
                    f'const owlAudio = new Audio("{audio_src}");\n',
                    encoding="utf-8",
                )
                (target_dir / "owl_280526.mp3").write_bytes(b"old")
            csv_path = project_dir / "OwlSpeech.csv"
            csv_path.write_text(
                "\n".join(
                    [
                        "date,part_a,part_b,part_c,full_text",
                        '2026-05-28,A,B,C,"Replacement text"',
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
                force=True,
            )

            result = daily_3am.run_colors_numbers_owl_task(
                context,
                speech_csv_path=csv_path,
                audio_generator=lambda text, output, voice, rate: output.write_bytes(text.encode("utf-8")),
            )

            self.assertEqual(result["status"], "completed")
            self.assertEqual((app_dir / "owl_280526.mp3").read_bytes(), b"Replacement text")
            self.assertEqual((docs_dir / "owl_280526.mp3").read_bytes(), b"Replacement text")
            self.assertEqual(
                result["changed_files"],
                [
                    "ColorsAndNumbers/web_colors_numbers/owl_280526.mp3",
                    "docs/colors-numbers/owl_280526.mp3",
                ],
            )

    def test_default_owl_speech_repeats_when_date_has_no_own_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            project_dir = repo_root / "Samantha_Agent"
            app_dir = repo_root / "ColorsAndNumbers" / "web_colors_numbers"
            docs_dir = repo_root / "docs" / "colors-numbers"
            project_dir.mkdir()
            app_dir.mkdir(parents=True)
            docs_dir.mkdir(parents=True)
            for script_path in (app_dir / "app.js", docs_dir / "app.js"):
                script_path.write_text(
                    'const owlAudio = new Audio("old.mp3?v=1");\n',
                    encoding="utf-8",
                )
            csv_path = project_dir / "OwlSpeech.csv"
            csv_path.write_text(
                "\n".join(
                    [
                        "date,part_a,part_b,part_c,full_text",
                        'default,,,,"Repeated default"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            context = daily_3am.DailyContext(
                project_dir=project_dir,
                log_file=project_dir / "logs" / "daily_3am.log",
                state_dir=project_dir / "data" / "daily_3am",
                run_date="2026-09-21",
                started_at=datetime.now(daily_3am.PRAGUE_TZ).isoformat(),
                dry_run=False,
                force=False,
            )

            result = daily_3am.run_colors_numbers_owl_task(
                context,
                speech_csv_path=csv_path,
                audio_generator=lambda text, output, voice, rate: output.write_bytes(
                    text.encode("utf-8")
                ),
            )

            self.assertEqual(result["status"], "completed")
            self.assertEqual((app_dir / "owl_210926.mp3").read_bytes(), b"Repeated default")
            self.assertEqual(
                (docs_dir / "owl_210926.mp3").read_bytes(), b"Repeated default"
            )
            self.assertIn(
                'new Audio("owl_210926.mp3?v=20260921a")',
                (docs_dir / "app.js").read_text(encoding="utf-8"),
            )

    def test_exact_owl_speech_overrides_default_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "OwlSpeech.csv"
            csv_path.write_text(
                "\n".join(
                    [
                        "date,part_a,part_b,part_c,full_text",
                        'default,,,,"Repeated default"',
                        '2026-09-21,,,,"Prepared for today"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            row = daily_3am.find_owl_speech_row(csv_path, "2026-09-21")

            self.assertIsNotNone(row)
            self.assertEqual(row["full_text"], "Prepared for today")


if __name__ == "__main__":
    unittest.main()
