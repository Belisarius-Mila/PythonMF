from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

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
            code = 5 if self.bootstrap_fails else 0
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
