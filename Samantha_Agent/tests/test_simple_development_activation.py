"""Bootstrap must not break the still-running single-role release parser."""
from contextlib import ExitStack
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from app import simple_development_activation as activation
from app.communication import agent_roles as roles
from tests.test_simple_development import FakeClient


class SimpleDevelopmentActivationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root = self.base / 'canonical'
        self.root.mkdir()
        self.config = self.root / 'config/agent_roles.json'
        self.config.parent.mkdir()
        self.document = {'schema': 1, 'roles': {'release_executor': {
            'label': 'Reviewed release executor', 'preferred_model': 'gpt-6-luna',
            'approved_models': [{'model': 'gpt-6-luna', 'reasoning_effort': 'high',
                                 'cost_review': 'Reviewed budget role', 'dry_run_evidence': 'Real release dry run'}]}}}
        self.config.write_text(json.dumps(self.document))
        for command in (['init', '-q'], ['add', 'config'], ['-c', 'user.name=Test',
                        '-c', 'user.email=test@invalid', '-c', 'core.hooksPath=/dev/null',
                        '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture'], ['branch', '-M', 'main']):
            subprocess.run(['git', '-C', str(self.root), *command], capture_output=True, check=True)
        self.store = self.base / 'probes'
        self.client = FakeClient()
        self.client.real_tests = True
        self.client.answer = {'function_source': 'def normalize_label(value):\n    text = str(value)\n    parts = text.split()\n    text = " ".join(parts)\n    return text.casefold()\n', 'summary': 'Sjednocení mezer a velikosti písmen.'}
        stack = self.enterContext(ExitStack())
        stack.enter_context(patch.object(activation, 'PROJECT_ROOT', self.root))
        stack.enter_context(patch.object(activation, 'STORE', self.store))
        stack.enter_context(patch.object(activation.development.routine_tasks, 'start_data_only_thread', return_value={'thread_id': 'isolated', 'disabled_skills': 0}))
        self.runtime = stack.enter_context(patch.object(activation, 'http_call', return_value={
            'ok': True, 'protocol': 1, 'role_schema': 2, 'role': roles.DEVELOPMENT_ROLE, 'enabled': False}))

    def accepted_probe(self):
        result = activation.probe_candidate('gpt-6.1-sol', 'low', cost_review='Reviewed numeric candidate price',
                                             confirmed=True, client_factory=lambda: self.client)
        self.assertEqual(result['state'], 'ready_for_review', result)
        accepted = activation.accept_probe(result['probe_id'], result['candidate_digest'], confirmed=True)
        self.assertEqual(accepted['state'], 'applied', accepted)
        return result['probe_id']

    def test_probe_requires_confirmation_without_provider_or_files(self):
        result = activation.probe_candidate('gpt-6.1-sol', 'low', cost_review='Reviewed candidate', client_factory=lambda: self.fail('provider'))
        self.assertEqual(result['state'], 'not_started')
        self.assertFalse(self.store.exists())

    def test_complete_probe_and_activation_preserve_release_role(self):
        probe = self.accepted_probe()
        self.assertEqual(json.loads(self.config.read_bytes()), self.document)
        plan = activation.activation_plan(probe)
        self.assertEqual(plan['state'], 'ready', plan)
        self.assertEqual(activation.activate(plan)['state'], 'not_applied')
        self.assertEqual(activation.activate(plan, confirmed=True)['state'], 'activated_locally')
        updated = json.loads(self.config.read_bytes())
        self.assertEqual(updated['roles']['release_executor'], self.document['roles']['release_executor'])
        roles.load_role(self.config, role=roles.DEVELOPMENT_ROLE)
        self.assertEqual(activation.activation_plan(probe)['state'], 'active')
        self.assertEqual(len(self.client.turns), 1)

    def test_old_runtime_cannot_receive_new_central_role(self):
        probe = self.accepted_probe()
        before = self.config.read_bytes()
        self.runtime.return_value = {'ok': False, 'message': 'Unknown route'}
        plan = activation.activation_plan(probe)
        self.assertEqual(plan['state'], 'blocked')
        self.assertEqual(activation.activate(plan, confirmed=True)['state'], 'blocked')
        self.assertEqual(self.config.read_bytes(), before)

    def test_replacement_requires_explicit_plan_and_preserves_release(self):
        probe = self.accepted_probe()
        document = json.loads(self.config.read_bytes())
        document['roles'][roles.DEVELOPMENT_ROLE] = {
            'label': 'Previous approved developer', 'preferred_model': 'gpt-6-luna',
            'approved_models': [{'model': 'gpt-6-luna', 'reasoning_effort': 'high',
                                 'cost_review': 'Previous price review', 'dry_run_evidence': 'Previous real probe'}]}
        self.config.write_text(json.dumps(document))
        subprocess.run(['git', '-C', str(self.root), 'add', 'config/agent_roles.json'], check=True, capture_output=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Test', '-c', 'user.email=test@invalid',
                        '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Previous role'], check=True, capture_output=True)
        self.assertEqual(activation.activation_plan(probe)['state'], 'blocked')
        plan = activation.activation_plan(probe, replace_existing=True)
        self.assertEqual(plan['state'], 'ready', plan)
        self.assertTrue(plan['replace_existing'])
        self.assertEqual(activation.activate(plan, confirmed=True)['state'], 'activated_locally')
        updated = json.loads(self.config.read_bytes())
        self.assertEqual(updated['roles']['release_executor'], self.document['roles']['release_executor'])
        self.assertEqual(updated['roles'][roles.DEVELOPMENT_ROLE]['preferred_model'], 'gpt-6.1-sol')

    def test_stale_plan_and_changed_proof_cannot_activate(self):
        probe = self.accepted_probe()
        plan = activation.activation_plan(probe)
        path = self.store / probe / 'proof.json'
        proof = json.loads(path.read_bytes())
        proof['binding']['preferred_model'] = 'unreviewed'
        path.write_text(json.dumps(proof))
        self.assertEqual(activation.activate(plan, confirmed=True)['state'], 'blocked')
        self.assertNotIn(roles.DEVELOPMENT_ROLE, json.loads(self.config.read_bytes())['roles'])

    def test_dirty_main_and_changed_release_policy_block_activation(self):
        probe = self.accepted_probe()
        (self.root / 'unrelated').write_text('WIP')
        self.assertEqual(activation.activation_plan(probe)['state'], 'blocked')
        changed = json.loads(self.config.read_bytes())
        changed['roles']['release_executor']['label'] = 'Different release policy'
        self.config.write_text(json.dumps(changed))
        self.assertEqual(activation.activation_plan(probe)['state'], 'blocked')

    def test_unaccepted_probe_is_not_activation_evidence(self):
        result = activation.probe_candidate('gpt-6.1-sol', 'low', cost_review='Reviewed numeric candidate price',
                                             confirmed=True, client_factory=lambda: self.client)
        self.assertEqual(activation.activation_plan(result['probe_id'])['state'], 'blocked')

    def test_changed_fixture_or_missing_proof_blocks_activation(self):
        probe = self.accepted_probe()
        (self.store / probe / 'fixture/app/labels.py').write_text('tampered')
        self.assertEqual(activation.activation_plan(probe)['state'], 'blocked')
        self.assertEqual(activation.activation_plan('../escape')['state'], 'blocked')


if __name__ == '__main__':
    unittest.main()
