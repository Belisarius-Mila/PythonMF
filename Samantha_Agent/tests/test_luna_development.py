"""Explicit multi-file Luna work retains source, authorization and test boundaries."""
import json
from unittest.mock import patch
import unittest

from app import luna_development as engine
from tests import test_simple_development as fixtures

ORIGINAL, REPLACEMENT = fixtures.ORIGINAL, fixtures.REPLACEMENT


class LunaDevelopmentTests(unittest.TestCase):
    def setUp(self):
        fixtures.SimpleDevelopmentTests.setUp(self)
        (self.root / 'app/view.js').write_text('const label = "OLD";\n')
        self.commit()
        self.policy['roles']['simple_developer']['preferred_model'] = 'gpt-6-luna'
        candidate = self.policy['roles']['simple_developer']['approved_models'][0]
        candidate.update(model='gpt-6-luna', reasoning_effort='high')
        self.roles_path.write_text(json.dumps(self.policy))
        self.client.list_models = lambda **kw: [{'model': 'gpt-6-luna', 'supportedReasoningEfforts': [{'reasoningEffort': 'high'}]}]
        self.client.answer = {'summary': 'Úprava Pythonu a JavaScriptu.', 'changes': [
            {'path': 'app/text_helpers.py', 'old': ORIGINAL, 'new': REPLACEMENT},
            {'path': 'app/view.js', 'old': '"OLD"', 'new': '"NEW"'}]}
        self.request = {'kind': engine.KIND, 'explicit_luna': True, 'request_id': 'explicit-test-001',
                        'goal': 'Převeď výstup na malá písmena a uprav popisek JavaScriptu.',
                        'files': {'app/text_helpers.py': [[1, 7]], 'app/view.js': [[1, 1]]},
                        'context': {}, 'test_modules': ['tests.test_text_helpers']}

    git = fixtures.SimpleDevelopmentTests.git
    commit = fixtures.SimpleDevelopmentTests.commit

    def run_job(self):
        return engine.run(self.request, root=self.root, confirmed=True, roles_path=self.roles_path,
                          store_root=self.store, client_factory=lambda: self.client)

    def accept(self, result):
        return engine.accept(result['job_id'], result['candidate_digest'], root=self.root, confirmed=True,
                             store_root=self.store, roles_path=self.roles_path)

    def test_actual_tests_and_reviewed_multifile_acceptance(self):
        self.client.real_tests = True
        before = self.source.read_bytes()
        result = self.run_job()
        self.assertEqual(result['state'], 'ready_for_review', result)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(result['baseline']['exit_code'], 1)
        self.assertEqual(result['after']['exit_code'], 0)
        self.assertEqual(len(self.client.turns), 1)
        self.assertEqual(self.accept(result)['state'], 'applied')
        self.assertIn('return cleaned.lower()', self.source.read_text())
        self.assertEqual((self.root / 'app/view.js').read_text(), 'const label = "NEW";\n')
        self.assertEqual(self.accept(result)['state'], 'applied')
        for command in self.client.commands:
            self.assertFalse(command['sandboxPolicy']['networkAccess'])
            self.assertNotIn(str(self.root), command['sandboxPolicy']['writableRoots'])

    def test_no_implicit_delegation_or_private_paths(self):
        for change in ({'explicit_luna': False}, {'files': {'../escape.py': [[1, 2]]}},
                       {'files': {'data/private/key.txt': [[1, 2]]}},
                       {'files': {'config/agent_roles.json': []}},
                       {'files': {'tests/test_text_helpers.py': [[1, 7]]}},
                       {'context': {'app/untracked.py': [[1, 1]]}}):
            with self.subTest(change=change):
                result = engine.preview({**self.request, **change}, root=self.root)
                self.assertEqual(result['action'], 'blocked', result)
        self.assertFalse(self.store.exists())
        self.assertEqual(engine.run(self.request, root=self.root)['state'], 'not_started')

    def test_explicit_luna_refuses_sol_without_a_model_turn(self):
        self.policy['roles']['simple_developer']['preferred_model'] = 'gpt-6.1-sol'
        self.policy['roles']['simple_developer']['approved_models'][0]['model'] = 'gpt-6.1-sol'
        self.roles_path.write_text(json.dumps(self.policy))
        self.client.list_models = lambda **kw: [{'model': 'gpt-6.1-sol', 'supportedReasoningEfforts': [{'reasoningEffort': 'high'}]}]
        self.assertEqual(self.run_job()['state'], 'attention')
        self.assertEqual(len(self.client.turns), 0)
        self.assertEqual(len(self.client.commands), 0)

    def test_one_receipt_never_repeats_the_turn(self):
        first = self.run_job()
        self.assertEqual(self.run_job(), first)
        self.assertEqual(len(self.client.turns), 1)
        self.assertEqual(len(self.client.commands), 2)

    def test_environment_failure_stops_before_model(self):
        self.client.results[0] = {'exitCode': 1, 'stderr': 'ERROR: missing\nRan 1 test in 0.1s\nFAILED (errors=1)\n'}
        self.assertEqual(self.run_job()['state'], 'attention')
        self.assertEqual(len(self.client.turns), 0)
        self.run_job()
        self.assertEqual(len(self.client.commands), 1)

    def test_guard_failure_and_out_of_scope_edits_are_not_accepted(self):
        self.client.answer['changes'][0]['path'] = 'tests/test_text_helpers.py'
        result = self.run_job()
        self.assertEqual(result['state'], 'attention')
        self.assertNotIn('lower()', self.source.read_text())

    def test_changes_must_be_unique_and_inside_supplied_sections(self):
        task = engine.prepare(self.root, self.request)
        originals = {n: (self.root / n).read_bytes() for n in task['sources']}
        for change in ({'path': 'app/view.js', 'old': '', 'new': 'x'},
                       {'path': 'app/text_helpers.py', 'old': 'missing', 'new': 'x'}):
            with self.assertRaises(ValueError):
                engine.build_candidates(task, {'summary': 'Invalid', 'changes': [change]}, originals)
        self.request['files']['app/text_helpers.py'] = [[1, 1]]
        task = engine.prepare(self.root, self.request)
        with self.assertRaises(ValueError):
            engine.build_candidates(task, self.client.answer, originals)
        overlapping = {'summary': 'Overlap', 'changes': [self.client.answer['changes'][1]] * 2}
        with self.assertRaises(ValueError):
            engine.build_candidates(task, overlapping, originals)

    def test_new_files_only_when_explicitly_declared_and_reviewed(self):
        self.request['files']['app/new.js'] = []
        self.client.answer['changes'].append({'path': 'app/new.js', 'old': '', 'new': 'const value = 1;\n'})
        result = self.run_job()
        self.assertEqual(result['state'], 'ready_for_review', result)
        self.assertFalse((self.root / 'app/new.js').exists())
        self.assertEqual(self.accept(result)['state'], 'applied')
        self.assertEqual((self.root / 'app/new.js').read_text(), 'const value = 1;\n')

    def test_source_or_candidate_drift_prevents_any_write(self):
        result = self.run_job()
        self.source.write_text('User work\n')
        self.assertEqual(self.accept(result)['state'], 'attention')
        self.assertEqual((self.root / 'app/view.js').read_text(), 'const label = "OLD";\n')

    def test_tampered_candidate_or_role_prevents_acceptance(self):
        result = self.run_job()
        path = self.store / result['job_id'] / 'candidates.json'
        path.write_text(json.dumps({'app/view.js': 'unsafe'}))
        self.assertEqual(self.accept(result)['state'], 'attention')
        self.assertNotIn('lower()', self.source.read_text())

    def test_partial_io_failure_is_journaled_and_not_retried(self):
        result = self.run_job()
        original = engine.atomic_replace_text_under_external_lock
        count = 0
        def fail_second(path, data):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError('disk full')
            return original(path, data)
        with patch.object(engine, 'atomic_replace_text_under_external_lock', side_effect=fail_second):
            self.assertEqual(self.accept(result)['state'], 'attention')
        saved = json.loads((self.store / result['job_id'] / 'receipt.json').read_bytes())
        self.assertEqual(saved['state'], 'applying')
        self.assertEqual(self.accept(result)['state'], 'attention')
        self.assertEqual((self.root / 'app/view.js').read_text(), 'const label = "OLD";\n')


if __name__ == '__main__':
    unittest.main()
