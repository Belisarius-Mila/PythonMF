import copy
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from unittest.mock import Mock, patch

from app.science_news import ScienceNews, digest
from app.science_news_manual import run_manual
from tests.test_science_news import packet, answer


class ManualTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = ScienceNews(Path(self.temp.name) / 'news')
        self.packet = packet()
        self.packet['candidates'][0]['published_at'] = '2026-11-11T12:00:00+00:00'
        self.args = dict(request_id='manual-user-fixture', week_start='2026-11-09',
                         packet=self.packet, confirmed=True)
        self.policy = patch('app.science_news_manual.policy').start()
        self.model = patch('app.science_news_manual.call_model', return_value=answer()).start()
        self.addCleanup(patch.stopall)

    def run_issue(self, **changes):
        return run_manual(self.store, **{**self.args, **changes})

    def test_confirmation_period_and_candidate_bounds_fail_before_writes(self):
        for changes in ({'confirmed': False}, {'week_start': '2026-11-10'},
                        {'week_start': '2099-01-05'}, {'week_start': '2026-11-02'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.run_issue(**changes)
            self.assertFalse(self.store.root.exists())
        self.model.assert_not_called()

    def test_new_issue_preserves_unknown_weekly_and_replay_never_pays_again(self):
        old = {'state': 'delivery_unknown', 'reserved_credits': 15}
        with self.store.transaction() as state:
            state['jobs']['editor_20261113'] = copy.deepcopy(old)
        first = self.run_issue()
        self.assertEqual(first['state'], 'published')
        self.assertEqual(self.run_issue()['state'], 'already_published')
        self.model.assert_called_once()
        state = self.store._read()
        self.assertEqual(state['jobs']['editor_20261113'], old)
        self.assertEqual(self.store.overview()['pending_count'], 1)
        self.assertFalse(any(k.startswith('weekly_') for k in state['jobs']))
        changed = copy.deepcopy(self.packet)
        changed['candidates'][0]['title'] = 'Different source'
        with self.assertRaises(ValueError): self.run_issue(packet=changed)
        self.model.assert_called_once()

    def test_publication_failure_replays_saved_answer_without_second_model(self):
        with patch.object(self.store, 'publish', side_effect=OSError('disk unavailable')):
            self.assertEqual(self.run_issue()['state'], 'attention')
        self.assertEqual(self.run_issue()['state'], 'published')
        self.model.assert_called_once()

    def test_invalid_answer_cannot_publish_or_trigger_another_paid_attempt(self):
        self.model.return_value = {'items': [{'invented': True}]}
        self.assertEqual(self.run_issue()['state'], 'attention')
        self.assertEqual(self.run_issue()['state'], 'attention')
        self.assertFalse(self.store._read()['issues'])
        self.model.assert_called_once()

    def test_same_request_during_collection_is_not_sent_twice(self):
        entered, release = Event(), Event()
        def review(*args):
            entered.set()
            if not release.wait(3): raise TimeoutError()
            return answer()
        self.model.side_effect = review
        with ThreadPoolExecutor(2) as pool:
            pending = pool.submit(self.run_issue)
            try:
                self.assertTrue(entered.wait(2))
                self.assertEqual(self.run_issue()['state'], 'preparing')
            finally: release.set()
            self.assertEqual(pending.result()['state'], 'published')
        self.model.assert_called_once()

    def test_known_source_is_not_resurrected_or_sent_to_model(self):
        source = self.packet['candidates'][0]
        from app.science_news_runner import grounded_items
        self.store.publish('previous', grounded_items(answer(), self.packet, []),
                           available_at=source['published_at'])
        result = self.run_issue()
        self.assertEqual(result['item_count'], 0)
        self.model.assert_not_called()

    def test_unknown_result_reuses_original_model_key_and_payload(self):
        # The real guarded adapter's recovery must never create a second turn.
        from app.science_news_model import call_model
        from tests.test_science_news_model import Client, BINDING, SELECTED
        import json
        self.store.root.mkdir()
        (self.store.root / 'activation.json').write_text(json.dumps({
            'enabled': True, 'approval_ref': 'fixture-approval', 'max_job_credits': 100,
            'max_month_credits': 200, 'activated_at': '2026-11-09T09:00:00+01:00'}))
        for method, value in [('load_role', BINDING), ('resolve_role', SELECTED), ('assert_current', SELECTED)]:
            patch('app.science_news_model.agent_roles.' + method, return_value=value).start()
        client = Client(fail=True)
        factory = Mock(return_value=client)
        self.model.side_effect = lambda *a: call_model(*a, client_factory=factory)
        self.assertEqual(self.run_issue()['state'], 'attention')
        before = self.store._read()
        model_key = next(k for k in before['jobs'] if k.startswith('editor_manual_'))
        self.assertEqual(self.run_issue()['state'], 'attention')
        self.assertEqual(sum(m == 'turn/start' for m, _ in client.inner.calls), 1)
        self.assertEqual(self.store._read()['jobs'][model_key]['reserved_credits'], 100)
        self.assertFalse(self.store._read()['issues'])


if __name__ == '__main__':
    unittest.main()
