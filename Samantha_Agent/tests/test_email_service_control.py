from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock

from app.communication.agent_roles import EMAIL_ROLE, load_role
from app.email.continuous_source import MailboxEpochChanged
from app.email.pushcut import PushcutNotifier
from app.email.service import load_settings
from app.email.service_control import CONFIRMATION, EmailServiceController
from app.file_persistence import exclusive_file_lock, FileLockTimeoutError


class Source:
    def __init__(self, provider):
        self.key = provider
        self.validity = "10"

    def baseline_cursor(self):
        return {"uidvalidity": self.validity, "after_uid": 500}


class ServiceControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        repository = (base / "repository").resolve()
        self.project = repository / "Samantha_Agent"
        self.project.mkdir(parents=True)
        for path, content in {
            ".gitignore": "data/\n.venv/\n.env\n",
            ".env": "SYNTHETIC=private-test-value\n",
            "app/example.py": "value = 1\n",
            "scripts/continuous_email_agent.py": "print('synthetic')\n",
            "config/agent_roles.json": json.dumps({"schema": 1, "roles": {EMAIL_ROLE: {
                "label": "Synthetic email role", "preferred_model": "synthetic-model",
                "approved_models": [{"model": "synthetic-model", "reasoning_effort": "high",
                    "cost_review": "Synthetic reviewed cost", "dry_run_evidence": "Synthetic accepted proof"}]}}}),
        }.items():
            target = self.project / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        python = self.project / ".venv/bin/python"
        python.parent.mkdir(parents=True)
        python.symlink_to(sys.executable)
        subprocess.run(["git", "-C", str(repository), "init", "-b", "main"], check=True, capture_output=True)
        self.git("add", ".gitignore", "app", "scripts", "config")
        self.git("-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.test", "commit", "-m", "fixture")
        self.loaded = False
        self.bootstrap_fails = False
        self.bootstrap_failures = 0
        self.system_calls = []
        self.sources = {name: Source(name) for name in ("icloud", "seznam")}
        role = load_role(self.project / "config/agent_roles.json", role=EMAIL_ROLE)
        self.selected = {"model": "synthetic-model", "reasoning_effort": "high", "fallback": False,
                         "policy_digest": role["policy_digest"]}
        self.control = EmailServiceController(project=self.project, root=self.project / "data/private/agent",
            support=base / "support", agents=base / "LaunchAgents", runner=self.runner,
            selector=lambda: self.selected, source_factory=self.sources.__getitem__)
        notifier = PushcutNotifier(self.control.worker, sender=lambda _: {"status": "accepted"})
        notifier.configure(webhook_url="https://api.pushcut.io/synthetic/notifications/Test",
                           cockpit_url="https://synthetic.example.test/emails-to-resolve/", enabled=True)
        notifier.test(request_id="synthetic-setup", confirmed=True)
        self.control.worker._update(lambda d: d["sources"].__setitem__("icloud", {"uidvalidity": "10", "after_uid": 42}))

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.project), *args], check=True, capture_output=True)

    def runner(self, argv, **kwargs):
        if argv[0] != "/bin/launchctl":
            return subprocess.run(argv, **kwargs)
        self.system_calls.append(argv[1:])
        code = 0
        if argv[1] == "print":
            code = 0 if self.loaded else 113
        elif argv[1] == "bootstrap":
            code = 5 if self.bootstrap_fails or self.bootstrap_failures else 0
            self.bootstrap_failures = max(0, self.bootstrap_failures - 1)
            self.loaded = not code
        elif argv[1] == "bootout":
            self.loaded = False
        return subprocess.CompletedProcess(argv, code, "", "")

    def prepare(self):
        self.plan = self.control.prepare()
        return self.plan

    def install(self, verifier=None):
        return self.control.install(confirmation=CONFIRMATION, plan_digest=self.plan["plan_digest"],
            verifier=verifier or (lambda started: {"started_at": started, "status": "outside_hours"}))

    def test_enabled_service_is_rejected_before_bootstrapping_runtime(self):
        self.control.settings_path.write_text(json.dumps({"enabled": True}))
        self.control.selector = Mock()
        with self.assertRaisesRegex(ValueError, "pozastav"):
            self.control.prepare()
        self.control.selector.assert_not_called()
        self.assertFalse(self.control.plan_path.exists())

    def test_prepare_is_project_only_and_does_not_copy_credentials(self):
        self.prepare()
        plan = json.loads(self.control.plan_path.read_text())
        stage = Path(plan["stage"])
        self.assertTrue(stage.is_relative_to(self.project))
        self.assertTrue((stage / ".env").is_symlink())
        self.assertNotIn("private-test-value", json.dumps(plan))
        self.assertFalse(self.control.target.exists())
        self.assertFalse(self.control.support.exists())
        self.assertEqual(self.system_calls, [])
        self.assertFalse(load_settings(self.control.settings_path).enabled)

    def test_exact_phrase_required_before_any_change(self):
        self.prepare()
        with self.assertRaises(ValueError):
            self.control.install(confirmation="ano", plan_digest=self.plan["plan_digest"])
        self.assertEqual(self.system_calls, [])
        self.assertEqual(set(self.control.worker.status()["sources"]), {"icloud"})

    def test_install_preserves_cursor_and_freezes_code(self):
        self.prepare()
        self.assertTrue(self.install()["installed"])
        state = self.control.worker.status()
        self.assertEqual(state["sources"]["icloud"]["after_uid"], 42)
        self.assertEqual(state["sources"]["seznam"]["after_uid"], 500)
        self.assertTrue(self.control.status()["owned"])
        self.assertTrue(load_settings(self.control.settings_path).enabled)
        (self.project / "app/example.py").write_text("value = 2\n")
        self.assertEqual((Path(self.plan["runtime"]) / "app/example.py").read_text(), "value = 1\n")
        self.assertEqual(os.readlink(Path(self.plan["runtime"]) / "data/private"), str(self.project / "data/private"))

    def test_existing_job_is_never_overwritten(self):
        self.prepare()
        self.control.target.parent.mkdir()
        self.control.target.write_text("foreign")
        with self.assertRaises(ValueError): self.install()
        self.assertEqual(self.control.target.read_text(), "foreign")
        self.assertFalse(self.control.support.exists())

    def test_dirty_source_blocks_install(self):
        self.prepare()
        (self.project / "app/example.py").write_text("changed\n")
        with self.assertRaises(ValueError): self.install()
        self.assertEqual(self.system_calls, [])

    def test_staged_modification_or_extra_code_blocks_install(self):
        self.prepare()
        plan = json.loads(self.control.plan_path.read_text())
        (Path(plan["stage"]) / "extra.py").write_text("print('unexpected')")
        with self.assertRaises(ValueError): self.install()
        self.assertEqual(self.system_calls, [])

    def test_changed_mailbox_epoch_stops_before_system_writes(self):
        self.prepare()
        self.sources["icloud"].validity = "11"
        with self.assertRaises(MailboxEpochChanged): self.install()
        self.assertFalse(self.control.support.exists())
        self.assertEqual(self.control.worker.status()["sources"]["icloud"]["after_uid"], 42)

    def test_launch_failure_disables_preserving_data_and_runtime(self):
        self.prepare()
        self.bootstrap_fails = True
        with self.assertRaises(RuntimeError): self.install()
        self.assertFalse(load_settings(self.control.settings_path).enabled)
        self.assertFalse(self.loaded)
        self.assertTrue(Path(self.plan["runtime"]).exists())
        self.assertEqual(json.loads(self.control.receipt_path.read_text())["status"], "failed_disabled")

    def test_first_check_failure_disables_job(self):
        self.prepare()
        def fail(started): raise RuntimeError("synthetic first check failure")
        with self.assertRaises(RuntimeError): self.install(verifier=fail)
        self.assertFalse(self.loaded)
        self.assertFalse(load_settings(self.control.settings_path).enabled)

    def test_pause_resume_and_restart_affect_only_owned_job(self):
        self.prepare()
        self.install()
        self.control.pause(confirmed=True)
        self.assertFalse(load_settings(self.control.settings_path).enabled)
        self.control.resume(confirmed=True)
        self.assertTrue(load_settings(self.control.settings_path).enabled)
        result = self.control.verify_restart(confirmation=CONFIRMATION,
            verifier=lambda started: {"started_at": started, "status": "outside_hours"})
        self.assertTrue(result["restart_verified"])
        self.assertTrue(all(self.control.job in call or str(self.control.target) in call for call in self.system_calls))

    def test_restart_never_interrupts_running_assessment(self):
        self.prepare()
        self.install()
        with exclusive_file_lock(self.control.root / "service_check", timeout=0):
            with self.assertRaises(FileLockTimeoutError):
                self.control.verify_restart(confirmation=CONFIRMATION)
        self.assertTrue(self.loaded)
        self.assertTrue(load_settings(self.control.settings_path).enabled)

    def test_restart_failure_disables_processing(self):
        self.prepare()
        self.install()
        self.bootstrap_fails = True
        with self.assertRaises(RuntimeError): self.control.verify_restart(confirmation=CONFIRMATION)
        self.assertFalse(load_settings(self.control.settings_path).enabled)

    def test_wait_check_accepts_only_fresh_operational_result(self):
        path = self.control.root / "service_health.json"
        path.write_text(json.dumps({"started_at": "2026-11-05T00:01:00+00:00", "status": "outside_hours"}))
        self.assertEqual(self.control._wait_check("2026-11-05T00:00:00+00:00")["status"], "outside_hours")
        path.write_text(json.dumps({"started_at": "2026-11-05T00:01:00+00:00", "status": "failed"}))
        with self.assertRaises(RuntimeError): self.control._wait_check("2026-11-05T00:00:00+00:00")

    def prepare_upgrade(self):
        self.prepare()
        self.install()
        self.old_plan = self.plan
        self.old_receipt = json.loads(self.control.receipt_path.read_text())
        self.old_plist = self.control.target.read_bytes()
        self.old_state = self.control.worker.status()
        self.control.pause(confirmed=True)
        (self.project / "app/example.py").write_text("value = 2\n")
        self.git("add", "app/example.py")
        self.git("-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.test", "commit", "-m", "upgrade fixture")
        self.prepare()

    def upgrade(self, verifier=None, confirmation=CONFIRMATION):
        return self.control.upgrade(confirmation=confirmation, plan_digest=self.plan["plan_digest"],
            verifier=verifier or (lambda started: {"started_at": started, "status": "already_completed"}))

    def test_upgrade_retains_old_release_and_all_business_state(self):
        self.prepare_upgrade()
        result = self.upgrade()
        self.assertTrue(result["upgraded"])
        self.assertEqual(result["previous_source_head"], self.old_plan["source_head"])
        self.assertEqual(self.control.worker.status(), self.old_state)
        self.assertEqual((Path(self.old_plan["runtime"]) / "app/example.py").read_text(), "value = 1\n")
        self.assertEqual((Path(self.plan["runtime"]) / "app/example.py").read_text(), "value = 2\n")
        self.assertTrue(self.control.status()["owned"])
        self.assertTrue(self.control.status()["loaded"])
        self.assertTrue(self.control.status()["enabled"])
        self.assertEqual(self.control.status()["source_head"], self.plan["source_head"])
        self.assertEqual(len(list((self.control.root / "service_backups").glob("*.json"))), 1)

    def test_upgrade_requires_exact_phrase_and_paused_service(self):
        self.prepare_upgrade()
        with self.assertRaises(ValueError): self.upgrade(confirmation="ano")
        settings = json.loads(self.control.settings_path.read_text())
        settings["enabled"] = True
        self.control.settings_path.write_text(json.dumps(settings))
        with self.assertRaises(ValueError): self.upgrade()
        self.assertEqual(self.control.target.read_bytes(), self.old_plist)

    def test_upgrade_never_interrupts_active_worker_or_copies_system_files(self):
        self.prepare_upgrade()
        with exclusive_file_lock(self.control.root / "service_check", timeout=0):
            with self.assertRaises(FileLockTimeoutError): self.upgrade()
        self.assertFalse(Path(self.plan["runtime"]).exists())
        self.assertTrue(self.loaded)
        self.assertEqual(self.control.target.read_bytes(), self.old_plist)

    def test_upgrade_refuses_foreign_plist(self):
        self.prepare_upgrade()
        self.control.target.write_text("foreign")
        with self.assertRaises(ValueError): self.upgrade()
        self.assertEqual(self.control.target.read_text(), "foreign")
        self.assertFalse(Path(self.plan["runtime"]).exists())

    def test_upgrade_bootstrap_failure_restores_old_job_paused(self):
        self.prepare_upgrade()
        self.bootstrap_failures = 1
        with self.assertRaises(RuntimeError): self.upgrade()
        self.assertEqual(self.control.target.read_bytes(), self.old_plist)
        status = self.control.status()
        self.assertTrue(status["owned"] and status["loaded"])
        self.assertFalse(status["enabled"])
        self.assertEqual(status["source_head"], self.old_receipt["source_head"])
        self.assertEqual(self.control.worker.status(), self.old_state)
        self.assertTrue(Path(self.plan["runtime"]).exists())

    def test_upgrade_first_check_failure_restores_old_job_paused(self):
        self.prepare_upgrade()
        def fail(started): raise RuntimeError("synthetic startup failure")
        with self.assertRaises(RuntimeError): self.upgrade(verifier=fail)
        self.assertEqual(self.control.target.read_bytes(), self.old_plist)
        self.assertTrue(self.control.status()["loaded"])
        self.assertFalse(self.control.status()["enabled"])
        self.assertEqual(self.control.worker.status(), self.old_state)

    def test_upgrade_rollback_preserves_foreign_edit(self):
        self.prepare_upgrade()
        def edit_then_fail(started):
            self.control.target.write_text("manual edit during startup")
            raise RuntimeError("synthetic failure")
        with self.assertRaises(ValueError): self.upgrade(verifier=edit_then_fail)
        self.assertEqual(self.control.target.read_text(), "manual edit during startup")
        self.assertFalse(load_settings(self.control.settings_path).enabled)

    def test_upgrade_refuses_same_head(self):
        self.prepare()
        self.install()
        self.control.pause(confirmed=True)
        self.prepare()
        with self.assertRaises(ValueError): self.upgrade()
        self.assertTrue(self.control.status()["owned"])

    def followup_install(self):
        for name in ("service.py", "followup_monitor.py", "followup_assessment.py", "codex_proposer.py"):
            path = self.project / "app/email" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("SYNTHETIC_FEATURE_VERSION = 1\n")
        self.git("add", "app/email")
        self.git("-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.test", "commit", "-m", "synthetic follow-up support")
        self.prepare()
        self.install()
        return self.plan["source_head"]

    def test_followup_enable_preserves_business_state_and_is_idempotent(self):
        head = self.followup_install()
        before = self.control.worker.status()
        settings = self.control.settings_path.read_bytes()
        self.control.selector = Mock(side_effect=AssertionError("must not start a model"))
        calls = len(self.system_calls)
        result = self.control.configure_followups(enabled=True, confirmed=True, expected_source_head=head)
        after = self.control.worker.status()
        for key in before:
            if key != "_repository": self.assertEqual(before[key], after[key])
        self.assertTrue(after["followups"]["monitor"]["enabled"])
        self.assertEqual(after["followups"]["monitor"]["last_run_at"], "")
        self.assertFalse(result["worker_verified"] or result["model_started"])
        self.assertEqual(self.control.settings_path.read_bytes(), settings)
        self.assertEqual(self.system_calls[calls:], [["print", self.control.job]])
        snapshot = self.control.worker.repository.path.read_bytes()
        self.assertFalse(self.control.configure_followups(enabled=True, confirmed=True, expected_source_head=head)["changed"])
        self.assertEqual(snapshot, self.control.worker.repository.path.read_bytes())
        self.control.selector.assert_not_called()

    def test_followup_enable_requires_exact_confirmation_and_head(self):
        head = self.followup_install()
        before = self.control.worker.repository.path.read_bytes()
        for args in ({"enabled": True, "confirmed": False, "expected_source_head": head},
                     {"enabled": 1, "confirmed": True, "expected_source_head": head},
                     {"enabled": True, "confirmed": True, "expected_source_head": "0" * 40}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                self.control.configure_followups(**args)
        self.assertEqual(before, self.control.worker.repository.path.read_bytes())

    def test_followup_enable_refuses_old_runtime_without_support(self):
        self.prepare(); self.install()
        before = self.control.worker.repository.path.read_bytes()
        with self.assertRaises((ValueError, OSError)):
            self.control.configure_followups(enabled=True, confirmed=True, expected_source_head=self.plan["source_head"])
        self.assertEqual(before, self.control.worker.repository.path.read_bytes())

    def test_followup_enable_refuses_changed_runtime_or_foreign_job(self):
        head = self.followup_install()
        path = Path(self.plan["runtime"]) / "app/email/service.py"
        original = path.read_bytes(); path.write_text("foreign code")
        with self.assertRaises(ValueError):
            self.control.configure_followups(enabled=True, confirmed=True, expected_source_head=head)
        path.write_bytes(original)
        self.control.target.write_text("foreign plist")
        with self.assertRaises(ValueError):
            self.control.configure_followups(enabled=True, confirmed=True, expected_source_head=head)
        self.assertNotIn("followups", self.control.worker.status())

    def test_followup_enable_refuses_paused_or_unloaded_service(self):
        head = self.followup_install()
        self.control.pause(confirmed=True)
        with self.assertRaises(ValueError):
            self.control.configure_followups(enabled=True, confirmed=True, expected_source_head=head)
        self.control.resume(confirmed=True)
        self.loaded = False
        with self.assertRaises(ValueError):
            self.control.configure_followups(enabled=True, confirmed=True, expected_source_head=head)

    def test_followup_change_refuses_busy_worker_without_writing(self):
        head = self.followup_install()
        before = self.control.worker.repository.path.read_bytes()
        with exclusive_file_lock(self.control.root / "service_check", timeout=0):
            with self.assertRaises(FileLockTimeoutError):
                self.control.configure_followups(enabled=True, confirmed=True, expected_source_head=head)
        self.assertEqual(before, self.control.worker.repository.path.read_bytes())

    def test_followup_disable_available_when_runtime_needs_repair(self):
        head = self.followup_install()
        self.control.configure_followups(enabled=True, confirmed=True, expected_source_head=head)
        self.control.target.write_text("foreign plist")
        self.loaded = False
        self.assertTrue(self.control.configure_followups(enabled=False, confirmed=True, expected_source_head=head)["changed"])
        self.assertFalse(self.control.worker.status()["followups"]["monitor"]["enabled"])

    def test_followup_reenable_same_hour_waits_for_and_records_a_new_worker_check(self):
        from datetime import datetime, timezone
        from app.email.followup_monitor import EmailFollowupMonitor
        head = self.followup_install()
        now = datetime(2026, 11, 12, 13, 30, tzinfo=timezone.utc)
        self.control.configure_followups(enabled=True, confirmed=True, expected_source_head=head)
        monitor = EmailFollowupMonitor(self.control.worker)
        monitor.check(now=now)
        self.control.configure_followups(enabled=False, confirmed=True, expected_source_head=head)
        self.control.configure_followups(enabled=True, confirmed=True, expected_source_head=head)
        self.assertEqual(self.control.worker.status()["followups"]["monitor"]["last_run_at"], "")
        monitor.check(now=now)
        self.assertEqual(self.control.worker.status()["followups"]["monitor"]["last_run_at"], now.isoformat())
