from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import plistlib
import tempfile
import unittest
from unittest.mock import Mock, patch

from app.communication.agent_roles import AgentRoleError, EMAIL_ROLE, load_role
from app.email.continuous_agent import ContinuousEmailAgent
from app.email.hourly_agent import HourlyEmailScheduler
from app.email.service import ServiceSettings, approved_selection, launch_agent_preview, readiness, service_tick, run_service_check
from app.file_persistence import exclusive_file_lock
from tests.test_continuous_email_agent import FakeSource, observed, proposal


class EmailServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.worker = ContinuousEmailAgent(self.root / "state")
        self.path = self.root / "service.json"
        self.now = datetime.fromisoformat("2026-11-04T07:00:00+01:00")
        self.source = FakeSource([observed(str(uid)) for uid in range(1, 4)])
        self.source.baseline_cursor = lambda: {"uidvalidity": "10", "after_uid": 0}
        self.selection = {"role": EMAIL_ROLE, "model": "synthetic-model", "reasoning_effort": "high"}
        self.model = Mock(side_effect=lambda _: proposal())
        self.select = Mock(return_value=self.selection)
        self.factory = Mock(return_value=self.model)
        self.validate = Mock()

    def configure(self, **updates):
        settings = {**ServiceSettings().model_dump(), "enabled": True, "providers": ["icloud"], **updates}
        self.path.write_text(json.dumps(settings), encoding="utf-8")

    def initialize(self):
        HourlyEmailScheduler(self.worker).initialize_from_now([self.source])

    def tick(self, **kwargs):
        return service_tick(settings_path=self.path, worker=self.worker, now=kwargs.pop("now", self.now),
                            source_factory=lambda _: self.source, select_model=self.select,
                            selection_validator=self.validate, proposer_factory=self.factory, **kwargs)

    def test_disabled_or_night_never_contacts_source_model_or_creates_state(self):
        self.configure(enabled=False)
        self.assertEqual(self.tick()["status"], "disabled")
        self.configure()
        self.assertEqual(self.tick(now=self.now.replace(hour=23))["status"], "outside_hours")
        self.select.assert_not_called()
        self.assertEqual(self.source.calls, [])
        self.assertFalse(self.worker.root.exists())

    def test_default_processes_more_than_twenty_messages_without_daily_cap(self):
        self.configure()
        self.source.messages = [observed(str(uid)) for uid in range(1, 22)]
        self.initialize()
        self.assertIsNone(ServiceSettings().max_assessments_per_day)
        self.assertEqual(self.tick()["proposals"], 20)
        self.assertEqual(self.tick()["proposals"], 1)
        self.assertEqual(self.model.call_count, 21)

    def test_heartbeat_failure_is_redacted_and_persistent(self):
        def fail(**kwargs):
            raise RuntimeError("sensitive synthetic text")
        result = run_service_check(worker=self.worker, tick=fail)
        health = (self.worker.root / "service_health.json").read_text()
        self.assertEqual(result["status"], "failed")
        self.assertNotIn("sensitive", health)
        self.assertIn("finished_at", health)

    def test_idle_check_does_not_rewrite_mail_state(self):
        self.initialize()
        path = self.worker.root / "state.json"
        before = path.stat().st_mtime_ns
        result = run_service_check(worker=self.worker, tick=lambda **kwargs: {"status": "outside_hours"})
        self.assertEqual(result["status"], "outside_hours")
        self.assertEqual(before, path.stat().st_mtime_ns)

    def test_missing_baseline_does_not_read_history_or_call_model(self):
        self.configure()
        self.assertEqual(self.tick()["status"], "needs_initialization")
        self.select.assert_not_called()
        self.assertEqual(self.source.calls, [])

    def test_daily_attempt_cap_survives_restart_and_defers_without_failed_cards(self):
        self.configure(max_assessments_per_day=2)
        self.initialize()
        self.assertEqual(self.tick()["proposals"], 2)
        self.worker = ContinuousEmailAgent(self.worker.root)
        self.assertEqual(self.tick()["status"], "paused")
        self.assertEqual(self.worker.status()["sources"][self.source.key]["after_uid"], 2)
        self.assertEqual(len(self.worker.status()["items"]), 2)
        self.assertEqual(self.model.call_count, 2)
        result = self.tick(now=self.now.replace(day=5))
        self.assertEqual(result["proposals"], 1)
        self.assertEqual(self.model.call_count, 3)

    def test_uncertain_model_counts_once_and_is_never_retried(self):
        self.configure(max_assessments_per_day=1)
        self.initialize()
        self.model.side_effect = TimeoutError("synthetic interruption")
        self.tick()
        state = self.worker.status()
        self.assertEqual(next(iter(state["items"].values()))["status"], "analysis_failed")
        self.assertEqual(state["service"]["daily_attempts"]["2026-11-04"], 1)
        self.tick(now=self.now.replace(day=5))
        self.assertEqual(self.model.call_count, 2)
        self.assertEqual(self.model.call_args.args[0].source.uid, "2")

    def test_runtime_pause_during_first_model_leaves_next_uid_untouched(self):
        self.configure()
        self.initialize()
        def pause(_):
            self.configure(enabled=False)
            return proposal()
        self.model.side_effect = pause
        self.assertEqual(self.tick()["status"], "incomplete")
        self.assertEqual(self.model.call_count, 1)
        self.assertEqual(self.worker.status()["sources"][self.source.key]["after_uid"], 1)
        self.configure()
        self.model.side_effect = lambda _: proposal()
        self.assertEqual(self.tick()["proposals"], 2)

    def test_completed_hour_does_not_contact_model_catalog_or_repeat(self):
        self.configure()
        self.initialize()
        self.assertEqual(self.tick()["status"], "completed")
        self.assertEqual(self.tick()["status"], "already_completed")
        self.assertEqual(self.select.call_count, 1)
        self.assertEqual(self.model.call_count, 3)

    def test_concurrent_service_skips_without_any_model_call(self):
        self.configure()
        self.initialize()
        with exclusive_file_lock(self.worker.root / "service", timeout=0):
            self.assertEqual(self.tick()["status"], "busy")
        self.select.assert_not_called()

    def test_role_rejection_stops_before_reading_bodies_or_spending(self):
        self.configure()
        self.initialize()
        self.select.side_effect = AgentRoleError("unapproved")
        with self.assertRaises(AgentRoleError): self.tick()
        self.assertEqual(self.source.calls, [])
        self.model.assert_not_called()

    def test_provider_change_during_turn_stops_before_next_email(self):
        self.configure()
        self.initialize()
        def change_sources(_):
            self.configure(providers=["seznam"])
            return proposal()
        self.model.side_effect = change_sources
        self.assertEqual(self.tick()["status"], "incomplete")
        self.assertEqual(self.model.call_count, 1)
        self.assertEqual(self.worker.status()["sources"][self.source.key]["after_uid"], 1)

    def test_readiness_is_redacted_local_only_and_does_not_create_storage(self):
        result = readiness(settings_path=self.path, worker=self.worker, source_factory=lambda _: self.source,
                           role_loader=Mock(side_effect=AgentRoleError("unapproved")), socket_path=self.root / "absent")
        self.assertFalse(result["ready"])
        self.assertIn("email_role_not_approved", result["blockers"])
        self.assertNotIn("sender@example", json.dumps(result))
        self.assertEqual(self.source.calls, [])
        self.assertFalse(self.worker.root.exists())

    def test_bad_settings_fail_before_initialization_or_any_model(self):
        for changes in ({"enabled": "yes"}, {"max_assessments_per_day": 0},
                        {"providers": ["icloud", "icloud"]}, {"model": "unapproved"}):
            self.configure(**changes)
            with self.assertRaises(ValueError): self.tick()
        self.select.assert_not_called()
        self.assertFalse(self.worker.root.exists())

    def test_launch_agent_preview_is_parseable_keeps_venv_and_has_no_install_side_effect(self):
        spec = launch_agent_preview(project=self.root)
        self.assertEqual(plistlib.loads(plistlib.dumps(spec)), spec)
        self.assertEqual(spec["ProgramArguments"][0], str(self.root.resolve() / ".venv/bin/python"))
        self.assertEqual(spec["ProgramArguments"][-1], "tick")
        self.assertEqual(list(self.root.iterdir()), [])

    def test_new_role_is_recognized_but_not_activated_by_this_development(self):
        policy = self.root / "roles.json"
        policy.write_text('{"schema":1,"roles":{}}', encoding="utf-8")
        with self.assertRaises(AgentRoleError): load_role(policy, role=EMAIL_ROLE)

    def test_missing_role_blocks_even_catalog_connection(self):
        with patch("app.email.service.load_role", side_effect=AgentRoleError("not approved")), patch(
            "app.email.service.CodexAppServerClient"
        ) as client, patch("app.email.service.LocalAppServerProcessController") as runtime:
            with self.assertRaises(AgentRoleError): approved_selection()
        client.assert_not_called()
        runtime.assert_not_called()

    def test_approved_selection_starts_dependency_before_catalog_without_chat_turn(self):
        order = Mock()
        with patch("app.email.service.load_role"), patch(
            "app.email.service.LocalAppServerProcessController"
        ) as runtime, patch("app.email.service.CodexAppServerClient") as client, patch(
            "app.email.service.resolve_role", return_value={**self.selection, "fallback": False}
        ):
            order.attach_mock(runtime.return_value.start, "start")
            order.attach_mock(client, "client")
            result = approved_selection()
        runtime.return_value.start.assert_called_once_with()
        self.assertEqual(order.mock_calls[0][0], "start")
        self.assertEqual(result["model"], "synthetic-model")
        peer = client.return_value.__enter__.return_value
        peer.list_models.assert_called_once_with()
        peer.start_thread.assert_not_called()
        peer.start_turn.assert_not_called()

    def test_unavailable_dependency_fails_before_catalog_and_is_not_restarted(self):
        from app.codex_appserver import AppServerError
        with patch("app.email.service.load_role"), patch(
            "app.email.service.LocalAppServerProcessController"
        ) as runtime, patch("app.email.service.CodexAppServerClient") as client:
            runtime.return_value.start.side_effect = AppServerError("existing socket unavailable")
            with self.assertRaises(AppServerError): approved_selection()
        runtime.return_value.start.assert_called_once_with()
        client.assert_not_called()

    def test_catalog_failure_does_not_restart_dependency_or_retry_catalog(self):
        from app.codex_appserver import AppServerError
        with patch("app.email.service.load_role"), patch(
            "app.email.service.LocalAppServerProcessController"
        ) as runtime, patch("app.email.service.CodexAppServerClient") as client:
            peer = client.return_value.__enter__.return_value
            peer.list_models.side_effect = AppServerError("catalog unavailable")
            with self.assertRaises(AppServerError): approved_selection()
        runtime.return_value.start.assert_called_once_with()
        peer.list_models.assert_called_once_with()
        peer.start_turn.assert_not_called()

    def test_reserved_attempt_is_on_disk_before_model_and_does_not_disappear_on_error(self):
        self.configure(max_assessments_per_day=1)
        self.initialize()
        def uncertain(_):
            on_disk = ContinuousEmailAgent(self.worker.root).status()
            self.assertEqual(on_disk["service"]["daily_attempts"]["2026-11-04"], 1)
            raise TimeoutError("unknown")
        self.model.side_effect = uncertain
        self.tick()
        self.assertEqual(self.tick()["status"], "paused")
        self.assertEqual(self.model.call_count, 1)


if __name__ == "__main__":
    unittest.main()
