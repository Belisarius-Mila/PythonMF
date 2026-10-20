"""Portal delegation cannot broaden an existing one-turn development grant."""
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from app import simple_development_portal as portal


class SimpleDevelopmentPortalTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.session = {'connected': True, 'turn_busy': True, 'thread_id': 'thread',
                        'active_turn': {'client_message_id': 'message'}}
        self.service = SimpleNamespace(workspace=SimpleNamespace(project_root=self.root / 'workspace',
                                                                 canonical_private_root=self.root / 'private'),
                                       hub=SimpleNamespace(snapshot=lambda: self.session))
        self.manager = SimpleNamespace(active_workstream_id='project-cockpit', active_service=self.service)
        self.engine = SimpleNamespace(preview=Mock(return_value={'action': 'delegate'}),
                                      run=Mock(return_value={'state': 'ready_for_review', 'job_id': 'job', 'candidate_digest': 'digest'}),
                                      accept=Mock(return_value={'state': 'applied', 'job_id': 'job', 'candidate_digest': 'digest'}))
        self.bridge = portal.PortalDelegation(engine=self.engine)
        self.enterContext(patch.object(portal.roles, 'load_role', return_value={}))
        self.ticket = self.bridge.issue(manager=self.manager, service=self.service,
                                         workstream_id='project-cockpit', client_message_id='message', writable=True)
        self.addCleanup(lambda: self.bridge.revoke(self.ticket))

    def dispatch(self, operation='run', **data):
        return self.bridge.dispatch({'token': self.ticket['token'], 'operation': operation, **data}, manager=self.manager)

    def test_read_only_or_missing_role_never_issues_a_channel(self):
        self.assertEqual(portal.PortalDelegation().issue(manager=self.manager, service=self.service,
            workstream_id='project-cockpit', client_message_id='message', writable=False), '')
        with patch.object(portal.roles, 'load_role', side_effect=portal.roles.AgentRoleError('inactive')):
            self.assertEqual(portal.PortalDelegation().issue(manager=self.manager, service=self.service,
                workstream_id='project-cockpit', client_message_id='message', writable=True), '')

    def test_server_derives_root_and_limits_to_one_model_task(self):
        first = self.dispatch(task={'goal': 'first'})
        self.assertEqual(first['state'], 'ready_for_review')
        self.assertEqual(self.dispatch(task={'goal': 'first'}), first)
        self.assertEqual(self.dispatch(task={'goal': 'other'})['state'], 'blocked')
        self.engine.run.assert_called_once_with({'goal': 'first'}, root=(self.root / 'workspace'), confirmed=True)
        self.assertEqual(self.dispatch('accept', job_id='foreign', candidate_digest='digest')['state'], 'blocked')
        self.engine.accept.assert_not_called()
        self.assertEqual(self.dispatch('accept', job_id='job', candidate_digest='digest')['state'], 'applied')

    def test_explicit_multifile_route_uses_luna_engine_and_same_acceptance(self):
        self.bridge._engine = portal.development
        task = {'kind': 'explicit_project_change', 'explicit_luna': True}
        with patch.object(portal.luna_development, 'preview', self.engine.preview), \
                patch.object(portal.luna_development, 'run', self.engine.run), \
                patch.object(portal.luna_development, 'accept', self.engine.accept):
            self.assertEqual(self.dispatch('preview', task=task)['action'], 'delegate')
            self.assertEqual(self.dispatch(task=task)['state'], 'ready_for_review')
            self.assertEqual(self.dispatch('accept', job_id='job', candidate_digest='digest')['state'], 'applied')
        self.engine.run.assert_called_once_with(task, root=self.root / 'workspace', confirmed=True)
        self.engine.accept.assert_called_once_with('job', 'digest', root=self.root / 'workspace', confirmed=True)

    def test_changed_thread_workstream_or_read_only_turn_blocks_before_engine(self):
        for field, value in [('thread_id', 'other'), ('turn_busy', False), ('active_turn', {'client_message_id': 'readonly'})]:
            original = self.session[field]
            self.session[field] = value
            self.assertEqual(self.dispatch(task={})['state'], 'blocked')
            self.session[field] = original
        self.manager.active_workstream_id = 'other'
        self.assertEqual(self.dispatch(task={})['state'], 'blocked')
        self.engine.run.assert_not_called()

    def test_extra_root_model_or_roles_fields_are_not_accepted(self):
        for field in ['root', 'model', 'roles_path', 'confirmed']:
            self.assertEqual(self.dispatch(task={}, **{field: 'override'})['state'], 'blocked')
        self.engine.run.assert_not_called()

    def test_expired_or_wrong_token_does_not_run(self):
        self.assertEqual(self.bridge.dispatch({'token': 'wrong', 'operation': 'run', 'task': {}}, manager=self.manager)['state'], 'blocked')
        self.bridge.revoke(self.ticket)
        self.assertEqual(self.dispatch(task={})['state'], 'blocked')
        self.engine.run.assert_not_called()

    def test_file_channel_returns_receipts_without_network_or_model_polling(self):
        result = portal.request('run', **self.ticket, task={'goal': 'first'})
        self.assertEqual(result['state'], 'ready_for_review')
        self.assertEqual(portal.request('run', **self.ticket, task={'goal': 'first'}), result)
        accepted = portal.request('accept', **self.ticket, job_id='job', candidate_digest='digest')
        self.assertEqual(accepted['state'], 'applied')
        self.engine.run.assert_called_once()
        self.bridge.revoke(self.ticket)
        self.assertEqual(portal.request('preview', **self.ticket, task={})['state'], 'blocked')

    def test_interrupted_task_is_not_automatically_repeated(self):
        self.engine.run.side_effect = RuntimeError('interrupted')
        self.assertEqual(self.dispatch(task={})['state'], 'blocked')
        self.assertEqual(self.dispatch(task={})['state'], 'attention')
        self.engine.run.assert_called_once()


if __name__ == '__main__':
    unittest.main()
