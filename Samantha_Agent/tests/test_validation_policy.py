from __future__ import annotations

import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from app.communication import validation_policy as policy
from app.communication.checkpoint_quality_gate import HumanAdamGateError, run_checkpoint_quality_gate
from app.communication.human_adam_workspace import HumanAdamWorkspaceManager


def git(repo, *args):
    return subprocess.check_output([policy.GIT_EXECUTABLE, "-C", str(repo), *args], stderr=subprocess.DEVNULL).decode().strip()


class ValidationPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name) / "repo"
        self.repo.mkdir()
        subprocess.run([policy.GIT_EXECUTABLE, "init", "-b", "main", str(self.repo)],
                       capture_output=True, check=True)
        git(self.repo, "config", "user.name", "Synthetic validator")
        git(self.repo, "config", "user.email", "validator@example.invalid")
        self.project = self.repo / "Samantha_Agent"
        self.write("scripts/cockpit_quality_gate.py", "# synthetic gate\n")
        self.write("app/frontend/cockpit/styles.css", "body { color: black; }\n")
        for name in (*policy.DOC_TESTS, *policy.FRONTEND_TESTS):
            self.write(name.replace(".", "/") + ".py", "# synthetic module\n")
        self.commit()
        self.base = git(self.repo, "rev-parse", "HEAD")
        self.workspace = HumanAdamWorkspaceManager(source_repo=self.repo, workspace_root=self.repo)
        self.store = policy.ValidationReceiptStore(self.repo)
        self.environment = patch.object(policy, "environment_fingerprint", return_value="synthetic-env")
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.calls = []

    def write(self, relative, text):
        path = self.project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def commit(self):
        git(self.repo, "add", "--all", "--", "Samantha_Agent")
        git(self.repo, "commit", "-m", "Synthetic input")

    def runner(self, command, **kwargs):
        self.calls.append(command)
        return subprocess.CompletedProcess(command, 0, "Ran 12 tests\nOK\nCockpit quality gate: OK\n", "")

    def run_gate(self, **kwargs):
        return run_checkpoint_quality_gate(workspace=self.workspace, runner=self.runner,
                                           log_path=Path(self.temporary.name) / "gate.log",
                                           validation_base=self.base, **kwargs)

    def certify_baseline(self):
        inputs = policy.capture_inputs(self.repo)
        return self.store.record(inputs, policy.ValidationPlan("full"), test_count=100, duration_seconds=5)

    def test_known_docs_and_frontend_have_fixed_dependency_tests(self):
        result = policy.select_validation_plan(["Samantha_Agent/memory/reports/example.md",
                                                "Samantha_Agent/app/frontend/cockpit/library_travel.js"])
        self.assertEqual(result.mode, "targeted")
        self.assertEqual(set(result.modules), set(policy.DOC_TESTS + policy.FRONTEND_TESTS))

    def test_sensitive_unknown_empty_and_policy_changes_require_full(self):
        for name in ("app/backup/incremental.py", "app/file_persistence.py", "app/email/service.py",
                     "app/calendar_writer.py", "config/agent_roles.json", "requirements.txt", "AGENTS.md",
                     "app/communication/validation_policy.py", "app/unknown.py", "tests/new_test.py"):
            with self.subTest(path=name):
                plan = policy.select_validation_plan(["Samantha_Agent/" + name,
                                                      "Samantha_Agent/app/frontend/cockpit/styles.css"])
                self.assertEqual(plan.mode, "full")
        self.assertEqual(policy.select_validation_plan([]).mode, "full")
        self.assertEqual(policy.select_validation_plan(["../styles.css"]).mode, "full")

    def test_first_targeted_change_requires_verified_baseline(self):
        self.write("app/frontend/cockpit/styles.css", "body { color: blue; }\n")
        result = self.run_gate()
        self.assertEqual(result.mode, "full")
        self.assertNotIn("--test-modules", self.calls[0])

    def test_targeted_gate_uses_program_modules_and_protects_complete_batch(self):
        self.certify_baseline()
        self.write("app/frontend/cockpit/styles.css", "body { color: blue; }\n")
        result = self.run_gate()
        self.assertEqual(result.mode, "targeted")
        self.assertEqual(self.calls[0][-len(policy.FRONTEND_TESTS):], list(sorted(policy.FRONTEND_TESTS)))
        self.write("app/backup/synthetic.py", "VALUE = 1\n")
        self.assertEqual(self.run_gate().mode, "full")

    def test_identical_pass_is_reused_and_bound_after_local_commit(self):
        self.write("app/new_code.py", "VALUE = 1\n")
        first = self.run_gate()
        self.assertFalse(first.reused)
        self.commit()
        second = self.run_gate()
        self.assertTrue(second.reused)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(second.test_count, 12)
        inputs = policy.capture_inputs(self.repo)
        self.assertIsNotNone(self.store.baseline(inputs.head, inputs.environment))

    def test_skip_flag_cannot_authorize_a_static_only_gate(self):
        result = self.run_gate(skip_unit_tests=True)
        self.assertEqual(result.mode, "full")
        self.assertGreater(result.test_count, 0)
        self.assertNotIn("--skip-unit-tests", self.calls[0])

    def test_checkpoint_journals_do_not_repeat_previously_passed_code_tests(self):
        self.write("app/new_code.py", "VALUE = 1\n")
        self.assertEqual(self.run_gate().mode, "full")
        self.write("memory/handoffs/workstreams/example.md", "Synthetic checkpoint receipt\n")
        self.commit()
        result = self.run_gate()
        self.assertEqual(result.mode, "targeted")
        self.assertEqual(self.calls[-1][-len(policy.DOC_TESTS):], list(sorted(policy.DOC_TESTS)))
        self.assertTrue(self.run_gate().reused)
        self.write("app/new_code.py", "VALUE = 2\n")
        self.assertEqual(self.run_gate().mode, "full")

    def test_deployment_of_already_validated_targeted_commit_reuses_proof(self):
        self.certify_baseline()
        self.write("app/frontend/cockpit/styles.css", "body { color: blue; }\n")
        self.commit()
        first = self.run_gate()
        head = git(self.repo, "rev-parse", "HEAD")
        result = run_checkpoint_quality_gate(workspace=self.workspace, runner=self.runner,
                  log_path=Path(self.temporary.name) / "deploy.log", validation_base=head, skip_unit_tests=True)
        self.assertEqual(first.mode, "targeted")
        self.assertTrue(result.reused)
        self.assertEqual(result.mode, "targeted")
        self.assertEqual(len(self.calls), 1)

    def test_missing_targeted_module_falls_back_to_full(self):
        self.certify_baseline()
        self.write("app/frontend/cockpit/styles.css", "body { color: blue; }\n")
        (self.project / (policy.FRONTEND_TESTS[0].replace(".", "/") + ".py")).unlink()
        self.assertEqual(self.run_gate().mode, "full")

    def test_byte_change_invalidates_receipt_even_when_size_and_mtime_match(self):
        self.run_gate()
        path = self.project / "app/frontend/cockpit/styles.css"
        before = path.stat()
        path.write_bytes(path.read_bytes().replace(b"black", b"white"))
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        result = self.run_gate()
        self.assertFalse(result.reused)
        self.assertEqual(len(self.calls), 2)

    def test_committing_a_tested_deletion_preserves_the_content_receipt(self):
        path = self.write("app/deleted_code.py", "VALUE = 1\n")
        self.commit()
        self.base = git(self.repo, "rev-parse", "HEAD")
        path.unlink()
        first = self.run_gate()
        self.commit()
        result = self.run_gate()
        self.assertEqual(first.mode, "full")
        self.assertTrue(result.reused)
        self.assertEqual(result.receipt_id, first.receipt_id)
        self.assertEqual(len(self.calls), 1)

    def test_environment_and_policy_changes_invalidate_receipt(self):
        self.run_gate()
        with patch.object(policy, "environment_fingerprint", return_value="different-dependencies"):
            self.assertFalse(self.run_gate().reused)
        with patch.object(policy, "POLICY_VERSION", "synthetic-policy-v2"):
            self.assertFalse(self.run_gate().reused)
        self.assertEqual(len(self.calls), 3)

    def test_tampered_receipt_cannot_be_used(self):
        self.run_gate()
        inputs = policy.capture_inputs(self.repo)
        path = self.store.root / ("full-" + inputs.digest + ".json")
        receipt = json.loads(path.read_text())
        receipt["body"]["test_count"] = 999999
        path.write_text(json.dumps(receipt))
        self.assertIsNone(self.store.find(inputs, policy.ValidationPlan("full")))

    def test_stale_loaded_policy_cannot_reuse_new_receipts(self):
        self.run_gate()
        with patch.object(policy, "_LOADED_POLICY_SOURCE", "synthetic-stale-source"):
            result = self.run_gate()
        self.assertEqual(result.mode, "full")
        self.assertFalse(result.reused)
        self.assertEqual(len(self.calls), 2)

    def test_receipt_expiry_and_targeted_chain_do_not_extend_full_baseline(self):
        now = [100.0]
        store = policy.ValidationReceiptStore(self.repo, clock=lambda: now[0])
        inputs = policy.capture_inputs(self.repo)
        baseline = store.record(inputs, policy.ValidationPlan("full"), test_count=5, duration_seconds=1)
        now[0] += policy.MAX_RECEIPT_AGE_SECONDS - 1
        plan = policy.select_validation_plan(["Samantha_Agent/memory/reports/example.md"])
        store.record(inputs, plan, test_count=2, duration_seconds=1, baseline=baseline)
        now[0] += 2
        self.assertIsNone(store.find(inputs, plan, allow_bound=True))

    def test_changed_inputs_during_gate_cannot_receive_receipt(self):
        def changing(command, **kwargs):
            self.write("app/changed_during_test.py", "VALUE = 1\n")
            return self.runner(command, **kwargs)
        with self.assertRaises(HumanAdamGateError):
            run_checkpoint_quality_gate(workspace=self.workspace, runner=changing,
              log_path=Path(self.temporary.name) / "gate.log", validation_base=self.base)
        self.assertIsNone(self.store.find(policy.capture_inputs(self.repo), policy.ValidationPlan("full")))

    def test_failed_and_zero_test_runs_cannot_receive_receipt(self):
        for output, code in (("FAILED\n", 1), ("Cockpit quality gate: OK\n", 0)):
            with self.subTest(output=output), self.assertRaises(HumanAdamGateError):
                run_checkpoint_quality_gate(workspace=self.workspace,
                  runner=lambda *a, **kw: subprocess.CompletedProcess([], code, output, ""),
                  log_path=Path(self.temporary.name) / "gate.log", validation_base=self.base)
        self.assertFalse((self.store.root / "receipt-key").exists())

    def test_lost_input_verification_after_full_gate_blocks_success(self):
        inputs = policy.capture_inputs(self.repo)
        with patch("app.communication.checkpoint_quality_gate.capture_inputs",
                   side_effect=[inputs, policy.ValidationPolicyError("Synthetic unreadable input")]):
            with self.assertRaises(HumanAdamGateError):
                self.run_gate()
        self.assertFalse((self.store.root / "receipt-key").exists())

    def test_rename_exposes_old_sensitive_path_and_new_name(self):
        path = self.write("app/backup/original.py", "VALUE = 1\n")
        self.commit()
        old = git(self.repo, "rev-parse", "HEAD")
        path.rename(path.with_name("new.py"))
        _, paths = policy.changed_paths(self.repo, old)
        self.assertIn("Samantha_Agent/app/backup/original.py", paths)
        self.assertIn("Samantha_Agent/app/backup/new.py", paths)
        self.assertEqual(policy.select_validation_plan(paths).mode, "full")

    def test_shared_key_creation_and_atomic_receipts_survive_concurrent_writers(self):
        inputs = policy.capture_inputs(self.repo)
        def write(number):
            return self.store.record(inputs, policy.ValidationPlan("full"), test_count=number, duration_seconds=1)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            list(executor.map(write, (1, 2)))
        body = self.store.find(inputs, policy.ValidationPlan("full"))
        self.assertIn(body["test_count"], (1, 2))
        self.assertEqual(len((self.store.root / "receipt-key").read_bytes()), 32)
        self.assertEqual((self.store.root / "receipt-key").stat().st_mode & 0o777, 0o600)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")

    def test_main_and_profile_clone_share_attested_identical_bytes(self):
        self.run_gate()
        clone = Path(self.temporary.name) / "profile"
        subprocess.run([policy.GIT_EXECUTABLE, "clone", str(self.repo), str(clone)], capture_output=True, check=True)
        workspace = HumanAdamWorkspaceManager(source_repo=self.repo, workspace_root=clone)
        result = run_checkpoint_quality_gate(workspace=workspace, runner=self.runner,
                    log_path=Path(self.temporary.name) / "profile.log", validation_base=self.base)
        self.assertTrue(result.reused)
        self.assertEqual(len(self.calls), 1)

    def test_timeout_preserves_partial_output_without_signing_success(self):
        def timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired(args[0], 1, output=b"Synthetic partial test progress")
        log = Path(self.temporary.name) / "timeout.log"
        with self.assertRaises(HumanAdamGateError) as error:
            run_checkpoint_quality_gate(workspace=self.workspace, runner=timeout, log_path=log,
                                        validation_base=self.base)
        self.assertEqual(error.exception.failure_type, "gate_timeout")
        self.assertIn("Synthetic partial test progress", log.read_text())
        self.assertFalse((self.store.root / "receipt-key").exists())


if __name__ == "__main__":
    unittest.main()
