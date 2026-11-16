import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.science_news import ScienceNews, digest
from app.science_news_runner import tick, PRAGUE, INSTRUCTIONS, SCHEMA
from app.science_news_recovery import recover_model_result, close_interrupted_issue, weekly_status
from app.science_news_model import call_model
from tests.test_science_news import packet, answer
from tests.test_science_news_model import Client, BINDING, SELECTED

NOW = datetime(2026,11,13,10,tzinfo=PRAGUE)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=ScienceNews(Path(self.temp.name)/'news',Path(self.temp.name)/'archive')
        self.store.root.mkdir()
        self.approved={'enabled':True,'approval_ref':'fixture-approval','max_job_credits':100,
                       'max_month_credits':200,'activated_at':'2026-11-09T09:00:00+01:00'}
        (self.store.root/'activation.json').write_text(json.dumps(self.approved))
        for method,value in [('load_role',BINDING),('resolve_role',SELECTED),('assert_current',SELECTED)]:
            p=patch('app.science_news_model.agent_roles.'+method,return_value=value);p.start();self.addCleanup(p.stop)

    def test_persistent_thread_and_sdk_receipt_saved_before_disconnect_failure(self):
        class ExitFailure(Client):
            def __exit__(self,*_):raise OSError('disconnect after delivery')
        client=ExitFailure();factory=Mock(return_value=client)
        result=call_model(self.store,'editor_fixture',{},'instructions',{},client_factory=factory)
        self.assertEqual(result,{'items':[]})
        start=next(p for m,p in client.inner.calls if m=='thread/start')
        self.assertIs(start['ephemeral'],False)
        job=self.store._read()['jobs']['editor_fixture']
        self.assertTrue(job['receipt']['delivered']);self.assertTrue(job['persistent'])
        self.assertEqual(job['turn_id'],'turn')
        self.assertEqual(call_model(self.store,'editor_fixture',{},'instructions',{},client_factory=factory),result)
        self.assertEqual(factory.call_count,1)

    def frozen_model(self, *, usage=True):
        job={'state':'delivery_unknown','fingerprint':digest({'payload':{},'instructions':'instructions','schema':{},'policy':self.approved}),
             'persistent':True,'thread_id':'original-thread','turn_id':'original-turn','client_message_id':'original-client',
             'executor':SELECTED,'reserved_credits':100,'month':'2026-11'}
        if usage:job['observed_usage']={'input_tokens':10,'cached_input_tokens':0,'output_tokens':20,'reasoning_output_tokens':0,'total_tokens':30}
        with self.store.transaction() as state:state['jobs']['editor_fixture']=job
        return job

    def history(self, *, change=None):
        turn={'id':'original-turn','status':'completed','items':[
            {'type':'userMessage','clientId':'original-client'},
            {'type':'agentMessage','id':'answer','phase':'final_answer','text':'{"items":[]}'}]}
        if change:change(turn)
        calls=[]
        class Reader:
            def __enter__(self):return self
            def __exit__(self,*_):pass
            def resume_thread(self,thread,**kw):
                calls.append(('resume',thread));self.assertion=kw
                assert thread=='original-thread' and kw['sandbox']=='read-only' and kw['approval_policy']=='never'
            @property
            def transport(self):return self
            def request(self,method,params):
                calls.append((method,params))
                assert method=='thread/turns/list' and params['threadId']=='original-thread' and params['limit']==2
                return {'data':[turn]}
        return Mock(return_value=Reader()),calls

    def test_provably_unstarted_preflight_resumes_first_request_without_double_reservation(self):
        class Offline(Client):
            def __enter__(self):raise OSError('shared socket unavailable before thread start')
        live=Client();factory=Mock(side_effect=[Offline(),live])
        with self.assertRaises(OSError):call_model(self.store,'editor_fixture',{},'instructions',{},client_factory=factory)
        first=self.store._read()['jobs']['editor_fixture']
        self.assertEqual(first['phase'],'preflight');self.assertNotIn('thread_id',first)
        result=recover_model_result(self.store,'editor_fixture',{},'instructions',{},client_factory=factory)
        self.assertEqual(result,{'items':[]});self.assertEqual(factory.call_count,2)
        final=self.store._read()['jobs']['editor_fixture']
        self.assertEqual(final['preflight_count'],2);self.assertEqual(final['reserved_credits'],100)
        self.assertEqual(final['started_at'],first['started_at'])
        self.assertEqual(sum(m=='turn/start' for m,_ in live.inner.calls),1)

    def test_two_callers_cannot_both_restart_a_preflight(self):
        from threading import Event
        entered=Event();release=Event()
        class Waiting(Client):
            def read_effective_config(self,**kwargs):
                entered.set();release.wait(2);return {'mcp_servers':{}}
        factory=Mock(return_value=Waiting())
        with ThreadPoolExecutor(2) as pool:
            first=pool.submit(call_model,self.store,'editor_fixture',{},'instructions',{},client_factory=factory)
            self.assertTrue(entered.wait(2))
            with self.assertRaises(ValueError):call_model(self.store,'editor_fixture',{},'instructions',{},client_factory=factory)
            release.set();self.assertEqual(first.result(),{'items':[]})
        self.assertEqual(factory.call_count,1)

    def test_original_completed_turn_recovers_without_new_thread_or_turn(self):
        self.frozen_model();factory,calls=self.history()
        self.assertEqual(recover_model_result(self.store,'editor_fixture',{},'instructions',{},client_factory=factory),{'items':[]})
        self.assertEqual([c[0] for c in calls],['resume','thread/turns/list'])
        self.assertEqual(self.store._read()['jobs']['editor_fixture']['state'],'completed')

    def test_other_turn_input_tools_or_incomplete_status_are_rejected(self):
        changes=[lambda t:t.update(id='other-turn'),lambda t:t.update(status='inProgress'),
                 lambda t:t['items'][0].update(clientId='other-client'),
                 lambda t:t['items'].append({'type':'commandExecution'})]
        for change in changes:
            with self.subTest(change=change):
                self.frozen_model();factory,_=self.history(change=change)
                with self.assertRaises(ValueError):recover_model_result(self.store,'editor_fixture',{},'instructions',{},client_factory=factory)
                self.assertEqual(self.store._read()['jobs']['editor_fixture']['state'],'delivery_unknown')

    def test_missing_usage_preserves_answer_and_full_reservation(self):
        self.frozen_model(usage=False);factory,_=self.history()
        with self.assertRaises(ValueError):recover_model_result(self.store,'editor_fixture',{},'instructions',{},client_factory=factory)
        job=self.store._read()['jobs']['editor_fixture']
        self.assertEqual(job['raw_answer'],'{"items":[]}');self.assertEqual(job['reserved_credits'],100)
        self.assertEqual(job['state'],'delivery_unknown')

    def test_rejected_tool_output_stays_blocked_before_any_recovery_client(self):
        class ToolClient(Client):
            def send_text(self,**kw):
                super().send_text(**kw)
                self.transport.receive(lambda _:True)
        factory=Mock(return_value=ToolClient())
        with self.assertRaises(ValueError):call_model(self.store,'editor_fixture',{},'instructions',{},client_factory=factory)
        self.assertTrue(self.store._read()['jobs']['editor_fixture']['guard_rejected'])
        with self.assertRaises(ValueError):recover_model_result(self.store,'editor_fixture',{},'instructions',{},client_factory=factory)
        self.assertEqual(factory.call_count,1)

    def test_streamed_reasoning_and_text_deltas_never_rewrite_the_packet(self):
        from app.science_news_recovery import record_event
        with patch.object(self.store,'transaction',side_effect=AssertionError('unnecessary packet rewrite')):
            for method in ('item/agentMessage/delta','item/reasoning/textDelta','item/started'):
                record_event(self.store,'unused',{'method':method,'params':{}})

    def test_counter_reset_invalidates_recovery_even_after_later_valid_usage(self):
        from app.science_news_recovery import record_event
        self.frozen_model()
        def observe(count):
            total={'inputTokens':count,'cachedInputTokens':0,'outputTokens':20,'reasoningOutputTokens':0,'totalTokens':count+20}
            record_event(self.store,'editor_fixture',{'method':'thread/tokenUsage/updated',
                'params':{'threadId':'original-thread','tokenUsage':{'total':total}}})
        observe(5);observe(100)
        job=self.store._read()['jobs']['editor_fixture']
        self.assertTrue(job['usage_invalid']);self.assertIsNone(job['observed_usage'])
        self.frozen_model()
        record_event(self.store,'editor_fixture',{'method':'thread/tokenUsage/updated',
            'params':{'threadId':'original-thread','tokenUsage':None}})
        observe(100)
        self.assertTrue(self.store._read()['jobs']['editor_fixture']['usage_invalid'])
        reader,_=self.history()
        with self.assertRaises(ValueError):recover_model_result(self.store,'editor_fixture',{},'instructions',{},client_factory=reader)
        self.assertEqual(self.store._read()['jobs']['editor_fixture']['state'],'delivery_unknown')

    def test_legacy_unknown_never_opens_a_client(self):
        with self.store.transaction() as state:
            state['jobs']['old']={'state':'delivery_unknown','fingerprint':digest({'payload':{},'instructions':'instructions','schema':{},'policy':self.approved}),
                                  'reserved_credits':100,'month':'2026-11','thread_id':'lost-ephemeral'}
        factory=Mock()
        with self.assertRaises(ValueError):recover_model_result(self.store,'old',{},'instructions',{},client_factory=factory)
        factory.assert_not_called()

    def frozen_week(self):
        frozen=packet();frozen['follows']=[];frozen['collected_at']='2026-11-13T08:04:00+01:00'
        with self.store.transaction() as state:
            state['jobs']['weekly_20261113']={'state':'attention','due':NOW.replace(hour=9).isoformat(),
                                            'packet':frozen,'packet_digest':digest(frozen)}
        return frozen

    def test_weekly_resumes_original_result_with_no_collection_or_review(self):
        self.frozen_week();reviewer=Mock(side_effect=AssertionError('no paid retry'));collector=Mock(side_effect=AssertionError('no new packet'))
        result=tick(self.store,NOW,reviewer=reviewer,collector=collector,recoverer=Mock(return_value=answer()))
        self.assertEqual(result['state'],'published');reviewer.assert_not_called();collector.assert_not_called()
        self.assertEqual(self.store.overview()['pending_count'],1)

    def test_raw_editorial_answer_survives_validation_publication_restart(self):
        frozen=self.frozen_week()
        with self.store.transaction() as state:state['jobs']['weekly_20261113']['raw_answer']=answer()
        real=self.store.publish;calls=[]
        def interrupted(*a,**kw):
            value=real(*a,**kw);calls.append(value)
            if len(calls)==1:raise OSError('after persisted publication')
            return value
        self.store.publish=interrupted
        reviewer=Mock(side_effect=AssertionError());recoverer=Mock(side_effect=AssertionError())
        self.assertEqual(tick(self.store,NOW,reviewer=reviewer,recoverer=recoverer)['state'],'attention')
        self.assertEqual(tick(self.store,NOW,reviewer=reviewer,recoverer=recoverer)['state'],'published')
        self.assertEqual(len(self.store._read()['issues']),1);reviewer.assert_not_called();recoverer.assert_not_called()

    def test_parallel_ticks_use_one_collector_and_model_attempt(self):
        from threading import Event
        entered=Event();release=Event();calls=[]
        def reviewer(_):entered.set();release.wait(2);calls.append(1);return answer()
        with ThreadPoolExecutor(2) as pool:
            first=pool.submit(tick,self.store,NOW,reviewer=reviewer,collector=lambda _:packet())
            self.assertTrue(entered.wait(2))
            second=tick(self.store,NOW,reviewer=reviewer,collector=lambda _:self.fail('second collector'))
            self.assertEqual(second['state'],'preparing');release.set();self.assertEqual(first.result()['state'],'published')
        self.assertEqual(len(calls),1)

    def test_explicit_close_preserves_unknown_budget_and_payload_and_unblocks_next_week(self):
        self.frozen_week()
        with self.store.transaction() as state:state['jobs']['editor_20261113']={'state':'delivery_unknown','reserved_credits':100}
        old=self.store._read();fp=digest(old['jobs']['weekly_20261113'])
        with self.assertRaises(ValueError):close_interrupted_issue(self.store,'weekly_20261113',expected_fingerprint=fp,request_id='approved-request')
        close_interrupted_issue(self.store,'weekly_20261113',expected_fingerprint=fp,request_id='approved-request',confirmed=True)
        state=self.store._read()
        self.assertEqual(state['jobs']['editor_20261113'],old['jobs']['editor_20261113'])
        self.assertEqual(state['jobs']['weekly_20261113']['packet'],old['jobs']['weekly_20261113']['packet'])
        self.assertTrue(weekly_status(self.store,now=NOW)['attention'])
        reviewer=Mock(side_effect=AssertionError('closed issue must never retry'))
        self.assertEqual(tick(self.store,NOW,reviewer=reviewer)['state'],'closed_without_output')
        reviewer.assert_not_called()
        fresh=tick(self.store,NOW+timedelta(days=7),reviewer=Mock(return_value=answer()),collector=lambda _:packet())
        self.assertEqual(fresh['state'],'published')

    def test_missing_week_or_stale_worker_is_visible_even_with_older_published_issue(self):
        with self.store.transaction() as state:state['jobs']['weekly_20261106']={'state':'published'}
        before=self.store.path.read_bytes()
        status=weekly_status(self.store,now=NOW)
        self.assertEqual(status['state'],'overdue');self.assertTrue(status['attention'])
        self.assertEqual(before,self.store.path.read_bytes())
        with self.store.transaction() as state:
            state['jobs']['weekly_20261113']={'state':'prepared'}
        self.assertEqual(weekly_status(self.store,now=NOW)['state'],'overdue')
        self.frozen_week();self.assertEqual(weekly_status(self.store,now=NOW)['state'],'attention')

    def test_old_completed_model_result_recovers_before_a_new_week_without_paid_review(self):
        frozen=self.frozen_week()
        model_key='editor_'+frozen['collected_at'][:10].replace('-','')
        fingerprint=digest({'payload':frozen,'instructions':INSTRUCTIONS,'schema':SCHEMA,'policy':self.approved})
        with self.store.transaction() as state:
            state['jobs'][model_key]={'state':'completed','fingerprint':fingerprint,'answer':answer()}
        reviewer=Mock(side_effect=AssertionError('no old or new paid call during recovery'))
        result=tick(self.store,NOW+timedelta(days=7),reviewer=reviewer,recoverer=Mock(),collector=Mock())
        self.assertEqual(result['state'],'published');reviewer.assert_not_called()
        self.assertEqual(self.store._read()['jobs']['weekly_20261113']['state'],'published')

    def test_changed_packet_is_not_recovered_or_republished(self):
        self.frozen_week()
        with self.store.transaction() as state:state['jobs']['weekly_20261113']['packet']['extra']='tampered'
        recovery=Mock(side_effect=AssertionError('no retrieval after tampering'))
        self.assertEqual(tick(self.store,NOW,reviewer=Mock(),recoverer=recovery)['state'],'attention')
        recovery.assert_not_called()

if __name__=='__main__':unittest.main()
