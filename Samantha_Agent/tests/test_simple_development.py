"""Bounded one-turn proposals never edit the caller before explicit acceptance."""
from contextlib import ExitStack
import fcntl
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app import simple_development as engine

ORIGINAL = 'def normalize_label(text: str) -> str:\n    cleaned = text.strip()\n    return cleaned\n'
REPLACEMENT = ORIGINAL.replace('return cleaned', 'return cleaned.lower()')
USAGE = {'input_tokens': 100, 'cached_input_tokens': 0, 'output_tokens': 100, 'reasoning_output_tokens': 0, 'total_tokens': 200}


class FakeClient:
    def __init__(self):
        self.transport = self
        self.commands = []
        self.turns = []
        self.usage = dict(USAGE)
        self.answer = {'function_source': REPLACEMENT, 'summary': 'Normalizace malými písmeny.'}
        self.results = [ {'exitCode': 1, 'stdout': '', 'stderr': 'FAIL: test_label\nRan 1 test in 0.001s\n\nFAILED (failures=1)\n'},
                         {'exitCode': 0, 'stdout': '', 'stderr': 'Ran 1 test in 0.001s\n\nOK\n'} ]
        self.callback = None
        self.real_tests = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def list_models(self, **kwargs):
        return [{'model': 'gpt-6.1-sol', 'supportedReasoningEfforts': [{'reasoningEffort': 'low'}]}]

    def request(self, method, params):
        if method != 'command/exec':
            raise AssertionError(method)
        self.commands.append(params)
        if self.real_tests:
            result = subprocess.run(params['command'], cwd=params['cwd'], env={**os.environ, **params['env']}, capture_output=True, text=True)
            return {'exitCode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
        result = self.results[len(self.commands) - 1]
        if isinstance(result, Exception):
            raise result
        return result

    def send_text(self, **kwargs):
        self.turns.append(kwargs)
        if self.callback:
            self.callback()
        return SimpleNamespace(answer=json.dumps(self.answer), thread_token_usage=self.usage)


class SimpleDevelopmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.root = self.base / 'project'
        (self.root / 'app').mkdir(parents=True)
        (self.root / 'tests').mkdir()
        self.source = self.root / 'app/text_helpers.py'
        self.source.write_text('# before\n' + ORIGINAL + '\n# after\nVALUE = 1\n')
        (self.root / 'app/__init__.py').write_text('')
        (self.root / 'tests/__init__.py').write_text('')
        (self.root / 'tests/test_text_helpers.py').write_text('import unittest\nfrom app.text_helpers import normalize_label\n\nclass LabelTests(unittest.TestCase):\n    def test_label(self):\n        self.assertEqual(normalize_label("  HELLO  "), "hello")\n')
        self.git('init', '-q')
        self.commit()
        self.store = self.base / 'private'
        self.roles_path = self.base / 'roles.json'
        self.policy = {'schema': 1, 'roles': {'simple_developer': {'label': 'Small safe developer', 'preferred_model': 'gpt-6.1-sol', 'approved_models': [ {'model': 'gpt-6.1-sol', 'reasoning_effort': 'low', 'cost_review': 'Reviewed numeric price', 'dry_run_evidence': 'Synthetic dry run passed'} ]}}}
        self.roles_path.write_text(json.dumps(self.policy))
        self.request = {'goal': 'Převeď výstup na malá písmena.', 'path': 'app/text_helpers.py', 'function': 'normalize_label', 'test_modules': ['tests.test_text_helpers']}
        self.client = FakeClient()
        stack = self.enterContext(ExitStack())
        stack.enter_context(patch.object(engine.roles, 'DEVELOPMENT_ROLE', 'simple_developer', create=True))
        stack.enter_context(patch.object(engine.roles, 'KNOWN_ROLES', engine.roles.KNOWN_ROLES | {'simple_developer'}))
        self.thread = stack.enter_context(patch.object(engine.routine_tasks, 'start_data_only_thread', create=True, return_value={'thread_id': 'isolated-thread', 'disabled_skills': 0}))

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], capture_output=True, check=True).stdout

    def commit(self):
        self.git('add', 'app', 'tests')
        self.git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture')

    def run_job(self, **kwargs):
        return engine.run(self.request, root=self.root, confirmed=True, roles_path=self.roles_path, store_root=self.store, client_factory=lambda: self.client, **kwargs)

    def accept(self, result, **kwargs):
        return engine.accept(result['job_id'], result['candidate_digest'], root=self.root, confirmed=True, store_root=self.store, roles_path=self.roles_path, **kwargs)

    def test_routing_and_confirmation_do_not_create_model_client(self):
        def forbidden():
            raise AssertionError('model called')
        for request in (dict(self.request, extra=True), dict(self.request, path='app/cockpit.py'), dict(self.request, function='missing')):
            result = engine.run(request, root=self.root, confirmed=True, client_factory=forbidden)
            self.assertEqual(result['action'], 'return_to_adam')
        result = engine.run(self.request, root=self.root, client_factory=forbidden)
        self.assertEqual(result['action'], 'confirmation_required')
        self.source.write_text('def normalize_label(text: str) -> str:\n    return text\n')
        self.commit()
        self.assertEqual(engine.preview(self.request, root=self.root)['action'], 'return_to_adam')
        self.assertFalse(self.store.exists())

    def test_ready_changes_only_isolated_source_and_has_small_model_payload(self):
        before = self.source.read_bytes()
        result = self.run_job()
        self.assertEqual(result['state'], 'ready_for_review', result)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(result['baseline']['exit_code'], 1)
        self.assertEqual(result['after']['test_count'], 1)
        job = self.store / result['job_id']
        self.assertEqual((job / 'workspace/app/text_helpers.py').read_text(), before.decode().replace(ORIGINAL, REPLACEMENT))
        self.assertEqual((job / 'receipt.json').stat().st_mode & 0o777, 0o600)
        payload = json.loads(self.client.turns[0]['text'])
        self.assertEqual(set(payload), {'goal', 'original_function', 'test_modules'})
        self.assertNotIn('# before', payload['original_function'])
        for command in self.client.commands:
            self.assertEqual(command['timeoutMs'], 30000)
            self.assertFalse(command['sandboxPolicy']['networkAccess'])
            self.assertNotEqual(command['cwd'], str(self.root))
            self.assertNotIn(str(self.root), command['sandboxPolicy']['writableRoots'])
        self.assertNotIn('stderr', json.dumps(result))

    def test_real_unittest_baseline_failure_and_after_success(self):
        self.client.real_tests = True
        result = self.run_job()
        self.assertEqual(result['state'], 'ready_for_review', result)
        self.assertEqual(result['baseline']['exit_code'], 1)
        self.assertEqual(result['after']['exit_code'], 0)

    def test_existing_receipt_prevents_another_turn_or_test(self):
        first = self.run_job()
        second = self.run_job()
        self.assertEqual(first, second)
        self.assertEqual(len(self.client.turns), 1)
        self.assertEqual(len(self.client.commands), 2)

    def test_environment_or_missing_tests_stops_before_model(self):
        for response in ({'exitCode': 1, 'stderr': 'ERROR: tests.test_missing\nRan 1 test in 0.001s\nFAILED (errors=1)\n'}, {'exitCode': 0, 'stdout': 'Ran 0 tests in 0.001s\nOK\n'}, ValueError('unsupported timeout')):
            with self.subTest(response=response):
                self.client.results[0] = response
                # Each fixture gets its own retained job store; never erase old jobs.
                self.store = self.base / ('private' + str(len(list(self.base.glob('private*')))))
                result = self.run_job()
                self.assertEqual(result['state'], 'attention')
                self.assertEqual(len(self.client.turns), 0)
                count = len(self.client.commands)
                self.run_job()
                self.assertEqual(len(self.client.commands), count)
                self.client.commands.clear()

    def test_failing_after_tests_prevent_readiness(self):
        self.client.results[1] = self.client.results[0]
        result = self.run_job()
        self.assertEqual(result['state'], 'attention')
        self.assertEqual(result['after']['exit_code'], 1)
        before = self.source.read_bytes()
        self.assertEqual(self.accept(result)['state'], 'attention')
        self.assertEqual(self.source.read_bytes(), before)

    def test_missing_and_excess_usage_are_retained_without_retry(self):
        for usage in (None, dict(USAGE, input_tokens=30000, total_tokens=30100), dict(USAGE, output_tokens=20000, total_tokens=20100)):
            with self.subTest(usage=usage):
                self.store = self.base / ('usage' + str(len(list(self.base.glob('usage*')))))
                self.client.usage = usage
                result = self.run_job()
                self.assertEqual(result['state'], 'attention')
                self.assertIn('model_usage', result)
                self.assertIn('estimated_credits', result)
                before = len(self.client.turns)
                self.run_job()
                self.assertEqual(len(self.client.turns), before)
                self.client.commands.clear()

    def test_role_drift_during_turn_and_after_ready(self):
        def drift():
            self.policy['roles']['simple_developer']['label'] += ' changed'
            self.roles_path.write_text(json.dumps(self.policy))
        self.client.callback = drift
        result = self.run_job()
        self.assertEqual(result['state'], 'attention')
        self.client.callback = None
        self.store = self.base / 'other-store'
        self.client.commands.clear()
        result = self.run_job()
        self.assertEqual(result['state'], 'ready_for_review')
        drift()
        self.assertEqual(self.accept(result)['state'], 'attention')
        self.assertIn('return cleaned\n', self.source.read_text())

    def test_source_drift_during_turn_retains_usage_and_does_not_overwrite(self):
        self.client.callback = lambda: self.source.write_text(self.source.read_text() + '# external change\n')
        result = self.run_job()
        self.assertEqual(result['state'], 'attention')
        self.assertEqual(result['model_usage'], USAGE)
        self.assertTrue(self.source.read_text().endswith('# external change\n'))

    def test_accept_exact_change_mode_and_idempotence(self):
        before = self.source.read_text()
        mode = self.source.stat().st_mode
        result = self.run_job()
        self.assertEqual(self.accept(result)['state'], 'applied')
        self.assertEqual(self.source.read_text(), before.replace(ORIGINAL, REPLACEMENT))
        self.assertEqual(self.source.stat().st_mode, mode)
        self.assertEqual(self.accept(result)['state'], 'applied')
        self.assertEqual(len(self.client.turns), 1)
        self.source.write_text(self.source.read_text() + '# later\n')
        self.assertEqual(self.accept(result)['state'], 'attention')
        self.assertTrue(self.source.read_text().endswith('# later\n'))

    def test_mismatched_digest_wrong_root_and_missing_confirmation(self):
        result = self.run_job()
        before = self.source.read_bytes()
        common = {'root': self.root, 'store_root': self.store, 'roles_path': self.roles_path}
        self.assertEqual(engine.accept(result['job_id'], result['candidate_digest'], **common)['state'], 'not_applied')
        self.assertEqual(engine.accept(result['job_id'], '0' * 64, confirmed=True, **common)['state'], 'attention')
        common['root'] = self.base
        self.assertEqual(engine.accept(result['job_id'], result['candidate_digest'], confirmed=True, **common)['state'], 'attention')
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(engine.accept('../bad', 'x', confirmed=True, root=self.root)['state'], 'attention')

    def test_source_or_head_drift_after_proposal_does_not_overwrite(self):
        result = self.run_job()
        self.source.write_text(self.source.read_text() + '# changed\n')
        before = self.source.read_bytes()
        self.assertEqual(self.accept(result)['state'], 'attention')
        self.assertEqual(self.source.read_bytes(), before)
        self.commit()
        self.assertEqual(self.accept(result)['state'], 'attention')

    def test_candidate_and_receipt_diff_tampering_rejected(self):
        result = self.run_job()
        job = self.store / result['job_id']
        before = self.source.read_bytes()
        (job / 'candidate.py').write_text('arbitrary')
        self.assertEqual(self.accept(result)['state'], 'attention')
        self.assertEqual(self.source.read_bytes(), before)
        (job / 'candidate.py').write_text(before.decode().replace(ORIGINAL, REPLACEMENT))
        receipt = json.loads((job / 'receipt.json').read_text())
        receipt['diff'] += 'tampered'
        (job / 'receipt.json').write_text(json.dumps(receipt))
        self.assertEqual(self.accept(result)['state'], 'attention')
        self.assertEqual(self.source.read_bytes(), before)

    def test_unsafe_answer_or_extra_work_stops_at_one_turn(self):
        self.client.answer['function_source'] = REPLACEMENT + '\nVALUE = 2\n'
        result = self.run_job()
        self.assertEqual(result['state'], 'attention')
        self.assertEqual(len(self.client.commands), 1)
        self.run_job()
        self.assertEqual(len(self.client.turns), 1)

    def test_symlink_anywhere_in_committed_copy_is_rejected(self):
        (self.root / 'app/link.py').symlink_to('text_helpers.py')
        self.commit()
        result = self.run_job()
        self.assertEqual(result['state'], 'attention')
        self.assertEqual(len(self.client.turns), 0)
        self.assertEqual(len(self.client.commands), 0)

    def test_after_tests_cannot_silently_change_test_sources(self):
        original_request = self.client.request
        def request(method, params):
            response = original_request(method, params)
            if len(self.client.commands) == 2:
                (Path(params['cwd']) / 'tests/test_text_helpers.py').write_text('# changed test\n')
            return response
        with patch.object(self.client, 'request', side_effect=request):
            result = self.run_job()
        self.assertEqual(result['state'], 'attention')
        self.assertIn('assertEqual', (self.root / 'tests/test_text_helpers.py').read_text())

    def test_locked_job_does_not_repeat_the_model_turn(self):
        result = self.run_job()
        with (self.store / result['job_id'] / 'job.lock').open('rb') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self.run_job()['state'], 'attention')
        self.assertEqual(len(self.client.turns), 1)
        self.assertEqual(len(self.client.commands), 2)

    def test_nested_project_root_archive(self):
        # Put a second valid project under this repository, as in PythonMF.
        nested = self.root / 'Samantha_Agent'
        for relative in ('app/__init__.py', 'app/text_helpers.py', 'tests/__init__.py', 'tests/test_text_helpers.py'):
            target = nested / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((self.root / relative).read_bytes())
        self.git('add', 'Samantha_Agent')
        self.git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'nested')
        result = engine.run(self.request, root=nested, confirmed=True, store_root=self.store, roles_path=self.roles_path, client_factory=lambda: self.client)
        self.assertEqual(result['state'], 'ready_for_review', result)
        self.assertTrue((self.store / result['job_id'] / 'workspace/app/text_helpers.py').is_file())


if __name__ == '__main__':
    unittest.main()
