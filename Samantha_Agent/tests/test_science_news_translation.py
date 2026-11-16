import copy
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from pathlib import Path
from unittest.mock import Mock, patch

from app.science_news import ScienceNews, identity
from app.science_news_model import call_model, monthly_charged, ScienceBudgetError
from app.science_news_translation import split_source, translate_study, budget_preview, authorize_budget
from tests.test_science_news import item
from tests.test_science_news_model import Client, BINDING, SELECTED


class FullStudyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.store = ScienceNews(Path(self.temp.name) / 'news')
        self.store.root.mkdir()
        self.approved = {'enabled': True, 'approval_ref': 'fixture-approval',
            'max_job_credits': 15, 'max_month_credits': 100, 'activated_at': '2026-11-09T09:00:00+01:00'}
        (self.store.root / 'activation.json').write_text(json.dumps(self.approved))
        self.source = ('First section of the whole study including its methods.\n' * 900)
        raw = item(source_text=self.source, translation_permission='user-provided')
        self.store.publish('fixture', [raw], available_at=raw['published_at'])
        self.item = self.store.item(identity(raw))
        self.key = 'translation_' + self.item['id']
        for method, value in [('load_role', BINDING), ('resolve_role', SELECTED), ('assert_current', SELECTED)]:
            p = patch('app.science_news_model.agent_roles.' + method, return_value=value)
            p.start(); self.addCleanup(p.stop)
        p = patch('app.science_news_translation.load_role', return_value=BINDING)
        p.start(); self.addCleanup(p.stop)
        self.clients = []
        class Translator(Client):
            def send_text(inner, **kwargs):
                result = super().send_text(**kwargs)
                payload = json.loads(kwargs['text'])
                result.answer = json.dumps({'complete': True,
                    'translation': 'Český text. ' * (len(payload['source_text']) // 12)})
                return result
        def factory():
            client = Translator(); self.clients.append(client); return client
        self.factory = Mock(side_effect=factory)
        self.model = lambda *a, **kw: call_model(*a, client_factory=self.factory, **kw)

    def calls(self):
        return sum(m == 'turn/start' for c in self.clients for m, _ in c.inner.calls)

    def run_study(self, model=None):
        return translate_study(self.store, self.item, model=model or self.model)

    def test_split_preserves_every_character_and_orders_all_sections(self):
        for source in (self.source, 'x' * 55001, ('word ' * 21000)):
            parts = split_source(source)
            self.assertEqual(''.join(parts), source)
            self.assertTrue(all(0 < len(p) <= 20000 for p in parts))

    def test_complete_study_and_actual_cost_are_assembled_once(self):
        self.run_study()
        state = self.store._read(); parent = state['jobs'][self.key]
        count = len(split_source(self.source))
        self.assertEqual(parent['state'], 'completed'); self.assertEqual(self.calls(), count)
        self.assertEqual(parent['completed_parts'], count)
        self.assertEqual(monthly_charged(state, parent['month']), parent['estimated_credits'])
        self.assertIn('translation', self.store.item(self.item['id']))
        self.run_study()
        self.assertEqual(self.calls(), count)

    def test_lost_worker_result_reuses_the_original_completed_part(self):
        first = True
        def disconnect(*a, **kw):
            nonlocal first
            result = self.model(*a, **kw)
            if first:
                first = False
                raise OSError('worker stopped after persisted model receipt')
            return result
        with self.assertRaises(OSError): self.run_study(model=disconnect)
        self.assertEqual(self.calls(), 1)
        self.assertNotIn('translation', self.store.item(self.item['id']))
        self.run_study()
        self.assertEqual(self.calls(), len(split_source(self.source)))
        self.assertEqual(self.store._read()['jobs'][self.key]['state'], 'completed')

    def test_unknown_part_never_starts_later_parts_or_a_second_paid_turn(self):
        original = self.factory.side_effect
        count = 0
        def factory():
            nonlocal count
            c = original(); count += 1
            if count == 2: c.fail = True
            return c
        self.factory.side_effect = factory
        with self.assertRaises(TimeoutError): self.run_study()
        before = self.store._read(); parent = before['jobs'][self.key]
        self.assertEqual(parent['completed_parts'], 1)
        self.assertEqual(self.calls(), 2)
        self.assertEqual(monthly_charged(before, parent['month']), 15)
        with self.assertRaises(ValueError): self.run_study()
        self.assertEqual(self.calls(), 2)
        after = self.store._read()
        self.assertNotIn(parent['part_keys'][2], after['jobs'])
        self.assertNotIn('translation', self.store.item(self.item['id']))
        self.assertEqual(monthly_charged(after, parent['month']), 15)

    def test_shared_credit_limit_stops_before_an_unaffordable_next_part(self):
        original = self.factory.side_effect
        def factory():
            client = original()
            send = client.send_text
            def expensive(**kw):
                result = send(**kw)
                result.thread_token_usage = {'input_tokens': 40000, 'cached_input_tokens': 0,
                    'output_tokens': 16000, 'reasoning_output_tokens': 0, 'total_tokens': 56000}
                return result
            client.send_text = expensive
            return client
        self.factory.side_effect = factory
        with self.assertRaises(ScienceBudgetError): self.run_study()
        self.assertEqual(self.calls(), 2)
        state = self.store._read(); parent = state['jobs'][self.key]
        self.assertEqual(parent['completed_parts'], 2)
        self.assertEqual(monthly_charged(state, parent['month']), 15)
        self.assertNotIn('translation', self.store.item(self.item['id']))

    def test_revoked_source_permission_stops_before_more_paid_work(self):
        def revoke(*a, **kw):
            result = self.model(*a, **kw)
            with self.store.transaction() as state:
                state['items'][self.item['id']]['translation_permission'] = 'unverified'
            return result
        with self.assertRaises(ValueError): self.run_study(model=revoke)
        self.assertEqual(self.calls(), 1)
        self.assertNotIn('translation', self.store.item(self.item['id']))

    def test_monthly_budget_failure_makes_no_model_call_and_can_be_rechecked(self):
        with self.store.transaction() as state:
            from datetime import datetime
            from app.science_news_runner import PRAGUE
            state['jobs']['other_unknown'] = {'state': 'delivery_unknown', 'reserved_credits': 90,
                'month': datetime.now(PRAGUE).strftime('%Y-%m')}
        with self.assertRaises(ScienceBudgetError): self.run_study()
        self.assertEqual(self.calls(), 0)
        parent = self.store._read()['jobs'][self.key]
        self.assertEqual(parent['reserved_credits'], 0)
        self.assertEqual(parent['state'], 'attention')
        with self.store.transaction() as state:
            state['jobs']['other_unknown'].update(state='completed', estimated_credits=10)
        self.run_study()
        self.assertEqual(self.store._read()['jobs'][self.key]['state'], 'completed')

    def test_concurrent_resume_observes_the_same_worker_without_changing_its_state(self):
        from app.science_news_translation import TranslationBusy
        entered, release = Event(), Event()
        original = self.factory.side_effect
        def factory():
            client = original()
            def wait(**kw):
                entered.set()
                if not release.wait(3): raise TimeoutError()
                return {'mcp_servers': {}}
            client.read_effective_config = wait
            return client
        self.factory.side_effect = factory
        with ThreadPoolExecutor(2) as pool:
            running = pool.submit(self.run_study)
            try:
                self.assertTrue(entered.wait(2))
                with self.assertRaises(TranslationBusy):self.run_study()
                self.assertEqual(self.store._read()['jobs'][self.key]['state'], 'running')
            finally:release.set()
            running.result()
        self.assertEqual(self.calls(), len(split_source(self.source)))

    def test_explicit_post_assembles_study_and_status_read_never_starts_work(self):
        from app.cockpit_science_news import science_news_translate_action, science_news_translation_status
        class InlineThread:
            def __init__(inner, *, target, daemon):inner.target = target
            def start(inner):inner.target()
        real = translate_study
        with patch('app.cockpit_science_news.threading.Thread', InlineThread), \
                patch('app.science_news_translation.translate_study', side_effect=lambda s,i:real(s,i,model=self.model)):
            result = science_news_translate_action({'item_id':self.item['id']},store=self.store)
        self.assertTrue(result['ok'])
        count = self.calls()
        status = science_news_translation_status(self.item['id'], store=self.store)
        self.assertEqual(status['state'], 'completed')
        self.assertEqual(count, len(split_source(self.source)))
        self.assertEqual(self.calls(), count)

    def test_legacy_uncertain_translation_is_preserved(self):
        old = {'state': 'delivery_unknown', 'reserved_credits': 15}
        with self.store.transaction() as state:
            state['jobs']['model_translation_' + self.item['id']] = copy.deepcopy(old)
        with self.assertRaises(ValueError): self.run_study()
        self.assertEqual(self.calls(), 0)
        self.assertEqual(self.store._read()['jobs']['model_translation_' + self.item['id']], old)

    def test_group_cannot_be_forged_to_avoid_monthly_reservation(self):
        with self.assertRaises(ValueError):
            call_model(self.store, 'unreserved_part', {'source_text': 'public'}, 'instructions', {},
                       budget_group='missing_group', client_factory=self.factory)
        self.assertEqual(self.calls(), 0)
        self.factory.assert_not_called()

    def interrupted_after_verified_part(self):
        def stopped(*a,**kw):
            self.model(*a,**kw)
            raise OSError('stopped after original completed receipt')
        with self.assertRaises(OSError):self.run_study(model=stopped)

    def test_budget_change_requires_exact_explicit_consent_and_sends_no_model_request(self):
        self.interrupted_after_verified_part()
        preview=budget_preview(self.store,item_id=self.item['id'],limit=20)
        self.assertEqual(preview['old_limit'],15);self.assertEqual(preview['verified_parts'],1)
        args={'item_id':self.item['id'],'limit':20,'expected_digest':preview['proposal_digest'],'request_id':'budget-fixture-request'}
        with self.assertRaises(ValueError):authorize_budget(self.store,**args)
        with self.assertRaises(ValueError):authorize_budget(self.store,**{**args,'expected_digest':'0'*64},confirmed=True)
        self.assertEqual(self.store._read()['jobs'][self.key]['reserved_credits'],15)
        self.assertTrue(authorize_budget(self.store,**args,confirmed=True)['ok'])
        self.assertTrue(authorize_budget(self.store,**args,confirmed=True)['replayed'])
        self.assertEqual(self.store._read()['jobs'][self.key]['reserved_credits'],20)
        self.assertEqual(self.calls(),1)

    def test_budget_proposal_rejects_unknown_parts_and_insufficient_monthly_capacity(self):
        self.interrupted_after_verified_part()
        with self.store.transaction() as state:
            parent=state['jobs'][self.key]
            state['jobs']['other_unknown']={'state':'delivery_unknown','month':parent['month'],'reserved_credits':85}
        with self.assertRaises(ScienceBudgetError):budget_preview(self.store,item_id=self.item['id'],limit=20)
        with self.store.transaction() as state:
            state['jobs']['other_unknown'].update(state='completed',estimated_credits=0)
            first=state['jobs'][state['jobs'][self.key]['part_keys'][0]]
            first['state']='delivery_unknown'
        with self.assertRaises(ValueError):budget_preview(self.store,item_id=self.item['id'],limit=20)
        self.assertEqual(self.calls(),1)

    def test_authorized_study_budget_completes_original_parts_without_changing_default_limit(self):
        original=self.factory.side_effect
        def factory():
            client=original();send=client.send_text
            def expensive(**kw):
                result=send(**kw)
                result.thread_token_usage={'input_tokens':40000,'cached_input_tokens':0,'output_tokens':16000,
                    'reasoning_output_tokens':0,'total_tokens':56000}
                return result
            client.send_text=expensive;return client
        self.factory.side_effect=factory
        with self.assertRaises(ScienceBudgetError):self.run_study()
        self.assertEqual(self.calls(),2)
        proposal=budget_preview(self.store,item_id=self.item['id'],limit=20)
        authorize_budget(self.store,item_id=self.item['id'],limit=20,expected_digest=proposal['proposal_digest'],
                         request_id='approved-budget-for-fixture',confirmed=True)
        self.run_study()
        state=self.store._read();parent=state['jobs'][self.key]
        self.assertEqual(parent['state'],'completed');self.assertEqual(self.calls(),3)
        self.assertEqual(parent['estimated_credits'],18)
        self.assertEqual(monthly_charged(state,parent['month']),18)
        self.assertEqual(json.loads((self.store.root/'activation.json').read_text())['max_job_credits'],15)

    def test_short_tail_uses_a_tighter_pinned_ceiling_and_finishes_within_approved_total(self):
        source=self.source[:41000]
        with self.store.transaction() as state:state['items'][self.item['id']]['source_text']=source
        self.item=self.store.item(self.item['id']);original=self.factory.side_effect
        def factory():
            client=original();send=client.send_text
            def measured(**kw):
                result=send(**kw);part=json.loads(kw['text'])['part_index']
                tokens=(80000,16000) if part<3 else (10000,2000)
                result.thread_token_usage={'input_tokens':tokens[0],'cached_input_tokens':0,'output_tokens':tokens[1],
                    'reasoning_output_tokens':0,'total_tokens':sum(tokens)}
                return result
            client.send_text=measured;return client
        self.factory.side_effect=factory;self.interrupted_after_verified_part()
        proposal=budget_preview(self.store,item_id=self.item['id'],limit=20)
        authorize_budget(self.store,item_id=self.item['id'],limit=20,expected_digest=proposal['proposal_digest'],
                         request_id='study-budget-short-tail-fixture',confirmed=True)
        self.run_study()
        state=self.store._read();parent=state['jobs'][self.key]
        self.assertEqual(parent['state'],'completed');self.assertEqual(parent['estimated_credits'],17)
        self.assertEqual(parent['reserved_credits'],20);self.assertEqual(self.calls(),3)
        tail=state['jobs'][parent['part_keys'][-1]]
        self.assertEqual(tail['output_limit'],4096);self.assertEqual(tail['credit_limit'],4)


if __name__ == '__main__': unittest.main()
