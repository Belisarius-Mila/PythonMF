from __future__ import annotations

import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from app.communication import validation_policy as policy
from app.communication.validation_domains import CORE_TESTS, modules_for_scopes
from scripts.cockpit_quality_gate import TEST_MODULES
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
        for name in {*policy.DOC_TESTS, *policy.FRONTEND_TESTS, *CORE_TESTS,
                     *modules_for_scopes({'calendar'},TEST_MODULES)}:
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
        self.assertTrue(set(policy.DOC_TESTS + CORE_TESTS).issubset(result.modules))
        self.assertIn('tests.test_library_photos',result.modules)

    def test_sensitive_unknown_empty_and_policy_changes_use_contract_suites(self):
        for name in ("app/backup/incremental.py", "app/file_persistence.py", "app/email/service.py",
                     "config/agent_roles.json", "requirements.txt", "AGENTS.md",
                     "app/communication/validation_policy.py", "app/unknown.py", "tests/new_test.py"):
            with self.subTest(path=name):
                plan = policy.select_validation_plan(["Samantha_Agent/" + name,
                                                      "Samantha_Agent/app/frontend/cockpit/styles.css"])
                self.assertEqual(plan.mode, "targeted")
                self.assertTrue(plan.modules)
        self.assertEqual(policy.select_validation_plan([]).mode, "targeted")
        with self.assertRaises(policy.ValidationPolicyError):
            policy.select_validation_plan(["../styles.css"])

    def test_first_targeted_change_never_requires_a_full_baseline(self):
        self.write("app/frontend/cockpit/styles.css", "body { color: blue; }\n")
        result = self.run_gate()
        self.assertEqual(result.mode, "targeted")
        self.assertIn("--test-modules", self.calls[0])

    def test_full_suite_runs_only_when_explicit_and_never_reuses_a_focused_receipt(self):
        self.run_gate()
        self.calls.clear()
        for _ in range(2):
            result=self.run_gate(full_suite=True)
            self.assertEqual(result.mode,'full')
            self.assertFalse(result.reused)
        self.assertEqual(len(self.calls),2)
        self.assertTrue(all('--test-modules' not in command for command in self.calls))

    def test_expired_receipt_runs_focused_tests_without_full_baseline(self):
        self.run_gate()
        with patch.object(policy,'MAX_RECEIPT_AGE_SECONDS',-1):
            result=self.run_gate()
        self.assertEqual(result.mode,'targeted')
        self.assertFalse(result.reused)

    def test_a_narrow_attestation_cannot_skip_other_pending_domain_checks(self):
        self.write('app/calendar_writer.py','VALUE = 1\n')
        self.write('memory/reports/synthetic.md','documentation\n')
        inputs=policy.capture_inputs(self.repo)
        docs=policy.select_validation_plan(['Samantha_Agent/memory/reports/synthetic.md'])
        self.store.record(inputs,docs,test_count=10,duration_seconds=1)
        result=self.run_gate()
        self.assertFalse(result.reused)
        self.assertIn('tests.test_calendar_writer',self.calls[-1])

    def test_unchanged_files_reuse_hashes_but_same_size_mtime_writes_invalidate_them(self):
        policy._input_hash.cache_clear()
        with patch.object(policy,'_file_hash',wraps=policy._file_hash) as hashed:
            first=policy.capture_inputs(self.repo)
            calls=hashed.call_count
            self.assertEqual(policy.capture_inputs(self.repo),first)
            self.assertEqual(hashed.call_count,calls)
            path=self.project/'app/frontend/cockpit/styles.css';info=path.stat()
            path.write_bytes(path.read_bytes().replace(b'black',b'white'))
            os.utime(path,ns=(info.st_atime_ns,info.st_mtime_ns))
            self.assertNotEqual(policy.capture_inputs(self.repo).digest,first.digest)
            self.assertGreater(hashed.call_count,calls)

    def test_targeted_gate_uses_program_modules_and_protects_complete_batch(self):
        self.certify_baseline()
        self.write("app/frontend/cockpit/styles.css", "body { color: blue; }\n")
        result = self.run_gate()
        self.assertEqual(result.mode, "targeted")
        selected=self.calls[0][self.calls[0].index('--test-modules')+1:]
        self.assertTrue(set(CORE_TESTS).issubset(selected))
        self.assertIn('tests.test_library_photos',selected)
        self.write("app/backup/synthetic.py", "VALUE = 1\n")
        self.assertEqual(self.run_gate().mode, "targeted")
        self.assertIn('tests.test_backup_incremental',self.calls[-1])

    def test_scoped_calendar_edit_and_new_source_keep_write_tests_without_full(self):
        self.write('app/calendar_writer.py','VALUE = 1\n')
        self.commit()
        self.base=git(self.repo,'rev-parse','HEAD')
        self.certify_baseline()
        self.write('app/calendar_writer.py','VALUE = 2\n')
        self.assertEqual(self.run_gate().mode,'targeted')
        self.assertIn('tests.test_email_calendar_write',self.calls[-1])
        self.write('app/calendar_unreviewed_new.py','VALUE = 3\n')
        self.assertEqual(self.run_gate().mode,'targeted')
        self.assertIn('tests.test_email_calendar_write',self.calls[-1])

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
        self.assertEqual(result.mode, "targeted")
        self.assertGreater(result.test_count, 0)
        self.assertNotIn("--skip-unit-tests", self.calls[0])

    def test_checkpoint_journals_do_not_repeat_previously_passed_code_tests(self):
        self.write("app/new_code.py", "VALUE = 1\n")
        self.assertEqual(self.run_gate().mode, "targeted")
        self.write("memory/handoffs/workstreams/example.md", "Synthetic checkpoint receipt\n")
        self.commit()
        result = self.run_gate()
        self.assertEqual(result.mode, "targeted")
        self.assertEqual(set(self.calls[-1][self.calls[-1].index('--test-modules')+1:]),set(policy.DOC_TESTS+CORE_TESTS))
        self.assertTrue(self.run_gate().reused)
        self.write("app/new_code.py", "VALUE = 2\n")
        self.assertEqual(self.run_gate().mode, "targeted")

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

    def test_missing_targeted_module_fails_instead_of_running_full(self):
        self.certify_baseline()
        self.write("app/frontend/cockpit/styles.css", "body { color: blue; }\n")
        (self.project / (policy.FRONTEND_TESTS[0].replace(".", "/") + ".py")).unlink()
        def missing_module(command, **kwargs):
            self.assertIn('--test-modules',command)
            self.assertIn(policy.FRONTEND_TESTS[0],command)
            return subprocess.CompletedProcess(command,1,'ImportError: missing test module','')
        with self.assertRaises(HumanAdamGateError):
            run_checkpoint_quality_gate(workspace=self.workspace,runner=missing_module,
                log_path=Path(self.temporary.name)/'missing.log',validation_base=self.base)

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
        self.assertEqual(first.mode, "targeted")
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
        plan=policy.select_validation_plan([])
        path = self.store.root / (plan.recipe + "-" + inputs.digest + ".json")
        receipt = json.loads(path.read_text())
        receipt["body"]["test_count"] = 999999
        path.write_text(json.dumps(receipt))
        self.assertIsNone(self.store.find(inputs, plan))

    def test_stale_loaded_policy_cannot_reuse_new_receipts(self):
        self.run_gate()
        with patch.object(policy, "_LOADED_POLICY_SOURCE", "synthetic-stale-source"):
            with self.assertRaises(HumanAdamGateError):
                self.run_gate()
        self.assertEqual(len(self.calls), 1)

    def test_targeted_receipt_uses_its_own_freshness_without_a_full_baseline_clock(self):
        now = [100.0]
        store = policy.ValidationReceiptStore(self.repo, clock=lambda: now[0])
        inputs = policy.capture_inputs(self.repo)
        baseline = store.record(inputs, policy.ValidationPlan("full"), test_count=5, duration_seconds=1)
        now[0] += policy.MAX_RECEIPT_AGE_SECONDS - 1
        plan = policy.select_validation_plan(["Samantha_Agent/memory/reports/example.md"])
        store.record(inputs, plan, test_count=2, duration_seconds=1, baseline=baseline)
        now[0] += 2
        self.assertIsNotNone(store.find(inputs, plan, allow_bound=True))
        now[0] += policy.MAX_RECEIPT_AGE_SECONDS
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
        self.assertEqual(policy.select_validation_plan(paths).mode, "targeted")

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

    def test_commit_private_clone_push_and_deploy_use_one_test_run(self):
        self.write('app/new_code.py', 'VALUE = 1\n')
        (self.project/'scripts/cockpit_quality_gate.py').chmod(0o755)
        first = self.run_gate()
        self.commit()
        clone = Path(self.temporary.name)/'private-profile'
        subprocess.run([policy.GIT_EXECUTABLE, 'clone', str(self.repo), str(clone)],
                       capture_output=True, check=True)
        for path in clone.rglob('*'):
            if path.is_file() and '.git' not in path.relative_to(clone).parts:
                path.chmod(0o700 if path.stat().st_mode & 0o100 else 0o600)
        workspace = HumanAdamWorkspaceManager(source_repo=self.repo, workspace_root=clone)
        pushed = run_checkpoint_quality_gate(workspace=workspace, runner=self.runner,
            log_path=Path(self.temporary.name)/'push.log', validation_base=self.base)
        deployed = run_checkpoint_quality_gate(workspace=workspace, runner=self.runner,
            log_path=Path(self.temporary.name)/'deploy.log', validation_base=git(clone,'rev-parse','HEAD'))
        self.assertTrue(pushed.reused)
        self.assertTrue(deployed.reused)
        self.assertEqual(pushed.receipt_id, first.receipt_id)
        self.assertEqual(len(self.calls), 1)

    def test_owner_permission_changes_still_invalidate_receipts(self):
        path = self.project/'app/frontend/cockpit/styles.css'
        self.run_gate()
        for mode in (0o744, 0o444):
            path.chmod(mode)
            self.assertFalse(self.run_gate().reused)
        self.assertEqual(len(self.calls), 3)

    def test_gate_runs_with_the_environment_used_for_its_fingerprint(self):
        parent = dict(os.environ)
        def runner(command, **kwargs):
            self.assertEqual(kwargs['env'], policy.validation_environment())
            self.assertEqual(kwargs['env']['PYTHONPATH'], '.')
            self.assertEqual(kwargs['env']['LC_ALL'], 'C')
            return self.runner(command, **kwargs)
        run_checkpoint_quality_gate(workspace=self.workspace, runner=runner,
            log_path=Path(self.temporary.name)/'environment.log', validation_base=self.base)
        self.assertEqual(dict(os.environ), parent)

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


class ValidationEnvironmentTests(unittest.TestCase):
    def test_canonical_child_imports_the_tested_project_instead_of_editor_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            project=Path(temporary)/'project'; project.mkdir()
            editor=Path(temporary)/'editor'; editor.mkdir()
            (project/'synthetic_validation_input.py').write_text("VALUE = 'tested-project'\n")
            (editor/'synthetic_validation_input.py').write_text("VALUE = 'editor-override'\n")
            with patch.dict(os.environ, {'PYTHONPATH':str(editor),'LC_ALL':'cs_CZ.UTF-8'}):
                result=subprocess.run([sys.executable,'-c',
                    'import os, synthetic_validation_input as p; print(p.VALUE, os.environ["LC_ALL"])'],
                    cwd=project, env=policy.validation_environment(), capture_output=True,text=True,check=True)
            self.assertEqual(result.stdout.strip(),'tested-project C')

    def test_terminal_and_launchd_fingerprint_the_same_test_environment(self):
        with patch.dict(os.environ, {'PATH':'/usr/bin:/bin:/usr/sbin:/sbin',
                'PYTHONPATH':'', 'PYTHONHASHSEED':'', 'PYTHONWARNINGS':'',
                'LANG':'', 'LC_ALL':'', 'TZ':''}):
            server = policy.environment_fingerprint()
        with patch.dict(os.environ, {'PATH':'/nonexistent-terminal/bin:/usr/bin',
                'PYTHONPATH':'/nonexistent/editor-imports', 'PYTHONHASHSEED':'random',
                'PYTHONWARNINGS':'ignore', 'LANG':'cs_CZ.UTF-8', 'LC_ALL':'cs_CZ.UTF-8',
                'TZ':'Europe/Prague'}):
            self.assertEqual(policy.environment_fingerprint(), server)

    def test_explicit_toolchain_change_still_invalidates_environment(self):
        with tempfile.TemporaryDirectory() as temporary:
            executables=[]
            for name in ('node-before','node-after'):
                path=Path(temporary)/name
                path.write_text('#!/bin/sh\nexit 0\n')
                path.chmod(0o700)
                executables.append(str(path))
            with patch.dict(os.environ, {'NODE_BINARY':executables[0]}):
                before=policy.environment_fingerprint()
            with patch.dict(os.environ, {'NODE_BINARY':executables[1]}):
                self.assertNotEqual(policy.environment_fingerprint(),before)


if __name__ == "__main__":
    unittest.main()
