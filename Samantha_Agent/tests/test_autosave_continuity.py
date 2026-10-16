from __future__ import annotations

import json
import os
from pathlib import Path
import plistlib
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

from scripts.autosave_snapshot import save_snapshot, select_source
from scripts.autosave_launchd import CONFIRMATION, LABEL, install, launch_agent, prepare
from scripts.autosave_status import autosave_status
from app.workflows.commands import preview_workflow_command_text, run_workflow_command_text
from scripts.start_autosave import stop_owned_workers
from types import SimpleNamespace


class AutosaveContinuityTests(unittest.TestCase):
    def fixture(self, directory):
        root = Path(directory)
        project = root / "project"
        sessions = root / "sessions"
        output = project / "data/session_autosave"
        project.mkdir()
        sessions.mkdir()
        source = sessions / "rollout-current.jsonl"
        return project, sessions, output, source

    def write_source(self, source, project, text="visible"):
        rows = [
            {"type": "session_meta", "payload": {"cwd": str(project)}},
            {"type": "response_item", "payload": {"type": "message", "role": "user",
                "content": [{"type": "input_text", "text": text}]}},
            {"type": "event_msg", "payload": {"type": "user_message", "message": text}},
            {"type": "response_item", "payload": {"type": "message", "role": "assistant",
                "content": [{"type": "output_text", "text": "saved answer"}]}},
            {"type": "response_item", "payload": {"type": "message", "role": "assistant",
                "channel": "analysis", "content": [{"type": "output_text", "text": "hidden analysis"}]}},
            {"type": "response_item", "payload": {"type": "message", "role": "system",
                "content": [{"type": "input_text", "text": "system fixture"}]}},
        ]
        source.write_text("".join(json.dumps(row) + "\n" for row in rows) + '{"partial":')

    def test_current_messages_are_readable_without_internal_records_or_partial_tail(self):
        with tempfile.TemporaryDirectory() as tmp:
            project, sessions, output, source = self.fixture(tmp)
            self.write_source(source, project)
            self.assertTrue(save_snapshot(project=project, sessions=sessions, output=output))
            readable = (output / "latest_session.txt").read_text()
            self.assertEqual(readable.count("visible"), 1)
            self.assertIn("saved answer", readable)
            self.assertNotIn("hidden analysis", readable)
            self.assertNotIn("system fixture", readable)
            for line in (output / "latest_session.jsonl").read_text().splitlines():
                json.loads(line)
            self.assertEqual((output / "latest_session.jsonl").stat().st_mode & 0o777, 0o600)

    def test_newer_foreign_project_does_not_replace_project_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            project, sessions, output, source = self.fixture(tmp)
            self.write_source(source, project)
            foreign = sessions / "rollout-other.jsonl"
            self.write_source(foreign, Path(tmp) / "unrelated", "foreign text")
            future = time.time() + 30
            os.utime(foreign, (future, future))
            self.assertEqual(select_source(sessions, project), source)

    def test_missing_source_keeps_last_good_files_and_reports_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            project, sessions, output, source = self.fixture(tmp)
            output.mkdir(parents=True)
            for name in ("latest_session.jsonl", "latest_session.txt", "latest_info.txt"):
                (output / name).write_text("last good")
            self.assertFalse(save_snapshot(project=project, sessions=sessions, output=output))
            self.assertEqual((output / "latest_session.jsonl").read_text(), "last good")
            status = autosave_status(latest_info_path=output / "latest_info.txt")
            self.assertEqual(status.last_error, "source_unavailable")

    def test_failure_between_publications_preserves_previous_pair_and_retry_recovers(self):
        with tempfile.TemporaryDirectory() as tmp:
            project, sessions, output, source = self.fixture(tmp)
            self.write_source(source, project, "first")
            save_snapshot(project=project, sessions=sessions, output=output)
            old_raw = (output / "latest_session.jsonl").read_bytes()
            old_text = (output / "latest_session.txt").read_bytes()
            self.write_source(source, project, "second")
            replace = os.replace
            def fail_text(src, dst):
                if Path(dst).name == "latest_session.txt":
                    raise OSError("synthetic disk failure")
                return replace(src, dst)
            with patch("scripts.autosave_snapshot.os.replace", side_effect=fail_text):
                with self.assertRaises(OSError):
                    save_snapshot(project=project, sessions=sessions, output=output)
            self.assertEqual((output / "previous_session.jsonl").read_bytes(), old_raw)
            self.assertEqual((output / "previous_session.txt").read_bytes(), old_text)
            self.assertEqual(json.loads((output / "last_attempt.json").read_text())["ok"], False)
            self.assertTrue(save_snapshot(project=project, sessions=sessions, output=output))
            self.assertIn("second", (output / "latest_session.txt").read_text())
            self.assertTrue(json.loads((output / "last_attempt.json").read_text())["ok"])

    def test_no_cleanup_mode_preserves_every_existing_history_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            project, sessions, output, source = self.fixture(tmp)
            output.mkdir(parents=True)
            protected = output / "session_20000101_000000.jsonl"
            protected.write_text("old original")
            os.utime(protected, (1, 1))
            self.write_source(source, project)
            save_snapshot(project=project, sessions=sessions, output=output, keep=1)
            self.assertEqual(protected.read_text(), "old original")
            self.assertIn("vypnuta", (output / "latest_info.txt").read_text())

    def test_launch_agent_is_independent_and_recovers_after_failure(self):
        spec = launch_agent()
        self.assertTrue(spec["KeepAlive"])
        self.assertTrue(spec["RunAtLoad"])
        self.assertEqual(spec["EnvironmentVariables"]["SAMANTHA_AUTOSAVE_AUTO_CLEANUP"], "0")
        self.assertEqual(spec["EnvironmentVariables"]["SAMANTHA_AUTOSAVE_SECONDS"], "600")

    def test_stop_never_signals_a_foreign_process(self):
        with patch("scripts.start_autosave.autosave_status", return_value=SimpleNamespace(watcher_pids=(123,))), \
                patch("scripts.start_autosave.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "other process", "")), \
                patch("scripts.start_autosave.os.kill") as kill:
            with self.assertRaises(RuntimeError):
                stop_owned_workers()
            kill.assert_not_called()

    def test_prepare_changes_only_project_preview_and_rejects_foreign_definition(self):
        with tempfile.TemporaryDirectory() as tmp:
            project, sessions, output, source = self.fixture(tmp)
            agents = Path(tmp) / "LaunchAgents"
            plan = prepare(project=project, agents=agents)
            self.assertTrue(Path(plan["preview"]).exists())
            self.assertFalse(agents.exists())
            agents.mkdir()
            foreign = agents / (LABEL + ".plist")
            foreign.write_bytes(plistlib.dumps({"Label": LABEL, "ProgramArguments": ["foreign"]}))
            with self.assertRaises(ValueError):
                prepare(project=project, agents=agents)
            self.assertEqual(plistlib.loads(foreign.read_bytes())["ProgramArguments"], ["foreign"])

    def test_install_requires_exact_confirmation_before_system_operation(self):
        with patch("scripts.autosave_launchd.prepare") as prepared:
            with self.assertRaises(ValueError):
                install(confirmation="ano")
            prepared.assert_not_called()

    def test_install_bootstraps_before_retiring_temporary_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            project, sessions, output, source = self.fixture(tmp)
            events = []
            def run(argv, **kwargs):
                events.append(argv[1])
                return subprocess.CompletedProcess(argv, 1 if argv[1] == "print" else 0, "", "")
            result = install(confirmation=CONFIRMATION, project=project, agents=Path(tmp) / "agents",
                             runner=run, stop_worker=lambda: events.append("stop-worker"))
            self.assertTrue(result["installed"])
            self.assertLess(events.index("bootstrap"), events.index("stop-worker"))
            self.assertIn("kickstart", events)

    def test_install_failure_restores_detached_saving_without_stopping_it_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            project, sessions, output, source = self.fixture(tmp)
            def run(argv, **kwargs):
                return subprocess.CompletedProcess(argv, 1, "", "synthetic failure")
            with patch("scripts.autosave_launchd.start_autosave") as unused:
                recover = unittest.mock.Mock()
                stop = unittest.mock.Mock()
                with self.assertRaises(RuntimeError):
                    install(confirmation=CONFIRMATION, project=project, agents=Path(tmp) / "agents",
                            runner=run, stop_worker=stop, recover=recover)
                stop.assert_not_called()
                recover.assert_called_once()

    def test_workflow_cannot_turn_simple_approval_into_global_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            pending = Path(tmp) / "pending.json"
            preview_workflow_command_text(command_id="install_autosave_service", pending_path=pending)
            for text, should_run in (("ano", False), (CONFIRMATION, True)):
                with patch("app.workflows.commands.subprocess.run") as runner:
                    runner.return_value = subprocess.CompletedProcess([], 0, "test only", "")
                    run_workflow_command_text(command_id="install_autosave_service", user_confirmed=True,
                                              confirmation_text=text, pending_path=pending, runner=runner)
                    self.assertEqual(runner.called, should_run)


if __name__ == "__main__":
    unittest.main()
