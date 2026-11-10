import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.science_news import ScienceNews
from app.science_news_model import ROLE, OneTurn, call_model

SELECTED={'role':ROLE,'model':'gpt-6.1-sol','reasoning_effort':'medium','policy_digest':'a'*64}
BINDING={'policy_digest':'a'*64,'approved_models':[{'model':'gpt-6.1-sol'}]}


class Inner:
    def __init__(self):self.calls=[]
    def request(self,method,params):
        self.calls.append((method,params))
        if method=='account/read':return {'account':{'type':'chatgpt'}}
        if method=='skills/list':return {'data':[{'skills':[],'errors':[]}]}
        if method=='thread/start':return {'thread':{'id':'thread'},'model':SELECTED['model'],'cwd':params['cwd'],
            'approvalPolicy':'never','sandbox':{'type':'readOnly','networkAccess':False}}
        return {'turn':{'id':'turn'}}
    def receive(self,predicate,**kwargs):return {'method':'item/completed','params':{'item':{'type':'commandExecution'}}}


class Client:
    def __init__(self,fail=False):self.inner=Inner();self.transport=self.inner;self.fail=fail
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def list_models(self,**kwargs):return []
    def read_effective_config(self,**kwargs):return {'mcp_servers':{}}
    def start_thread(self,**kwargs):
        params={'cwd':str(kwargs['cwd'].resolve()),'model':kwargs['model'],'ephemeral':True,
            'approvalPolicy':kwargs['approval_policy'],'sandbox':kwargs['sandbox'],
            'baseInstructions':kwargs['base_instructions'],'developerInstructions':kwargs['developer_instructions'],
            'config':kwargs['config_overrides']}
        return self.transport.request('thread/start',params)['thread']['id']
    def send_text(self,**kwargs):
        self.transport.request('turn/start',{'threadId':kwargs['thread_id'],'model':kwargs['model'],
            'effort':kwargs['effort'],'approvalPolicy':kwargs['approval_policy'],
            'sandboxPolicy':kwargs['sandbox_policy'],'outputSchema':kwargs['output_schema'],
            'input':[{'type':'text','text':kwargs['text']}]})
        if self.fail:raise TimeoutError('response lost')
        return SimpleNamespace(answer='{"items":[]}',delivered=True,thread_id='thread',thread_token_usage={'input_tokens':10,'cached_input_tokens':0,
            'output_tokens':20,'reasoning_output_tokens':0,'total_tokens':30})


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=ScienceNews(Path(self.temp.name)/'news')
        self.store.root.mkdir()
        (self.store.root/'activation.json').write_text(json.dumps({'enabled':True,'approval_ref':'fixture-approval',
            'max_job_credits':100,'max_month_credits':200,'activated_at':'2026-11-09T09:00:00+01:00'}))
        for target,value in [('load_role',BINDING),('resolve_role',SELECTED),('assert_current',SELECTED)]:
            mocked=patch('app.science_news_model.agent_roles.'+target,return_value=value)
            mocked.start();self.addCleanup(mocked.stop)

    def test_one_guarded_standard_turn_on_shared_client_and_cached_result(self):
        client=Client();factory=Mock(return_value=client)
        result=call_model(self.store,'fixture',{'source':'text'},'instructions',{},client_factory=factory)
        self.assertEqual(result,{'items':[]})
        self.assertEqual(call_model(self.store,'fixture',{'source':'text'},'instructions',{},client_factory=factory),result)
        self.assertEqual(factory.call_count,1)
        turns=[p for m,p in client.inner.calls if m=='turn/start']
        self.assertEqual(len(turns),1);self.assertEqual(turns[0]['serviceTierForTurn'],'default')
        self.assertEqual(turns[0]['sandboxPolicy'],{'type':'readOnly','networkAccess':False})
        start=next(p for m,p in client.inner.calls if m=='thread/start')
        self.assertFalse(start['config']['features.shell_tool'])
        self.assertFalse(start['config']['features.apps'])
        self.assertEqual(start['config']['web_search'],'disabled')
        self.assertEqual(self.store._read()['jobs']['fixture']['state'],'completed')

    def test_uncertain_result_blocks_same_job_across_restarts(self):
        factory=Mock(return_value=Client(fail=True))
        with self.assertRaises(TimeoutError):call_model(self.store,'fixture',{},'instructions',{},client_factory=factory)
        with self.assertRaises(ValueError):call_model(ScienceNews(self.store.root),'fixture',{},'instructions',{},client_factory=factory)
        self.assertEqual(factory.call_count,1)
        self.assertEqual(self.store._read()['jobs']['fixture']['state'],'delivery_unknown')

    def test_monthly_reservation_and_input_estimate_stop_before_client(self):
        with self.store.transaction() as state:
            from datetime import datetime
            from zoneinfo import ZoneInfo
            state['jobs']['old']={'state':'delivery_unknown','month':datetime.now(ZoneInfo('Europe/Prague')).strftime('%Y-%m'),'reserved_credits':200}
        factory=Mock()
        with self.assertRaises(ValueError):call_model(self.store,'new',{},'instructions',{},client_factory=factory)
        factory.assert_not_called()

    def test_raw_answer_survives_bad_usage_without_second_call(self):
        client=Client()
        original=client.send_text
        def bad(**kwargs):
            result=original(**kwargs);result.thread_token_usage=None;return result
        client.send_text=bad
        with self.assertRaises(ValueError):call_model(self.store,'fixture',{},'instructions',{},client_factory=Mock(return_value=client))
        job=self.store._read()['jobs']['fixture']
        self.assertEqual(job['state'],'delivery_unknown');self.assertEqual(job['raw_answer'],'{"items":[]}')

    def test_completed_job_charges_actual_usage_and_releases_unused_reservation(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        with self.store.transaction() as state:
            state['jobs']['old']={'state':'completed','month':datetime.now(ZoneInfo('Europe/Prague')).strftime('%Y-%m'),
                'reserved_credits':200,'estimated_credits':10}
        factory=Mock(return_value=Client())
        self.assertEqual(call_model(self.store,'new',{},'instructions',{},client_factory=factory),{'items':[]})
        self.assertEqual(factory.call_count,1)

    def test_invalid_completed_usage_keeps_full_reservation(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        with self.store.transaction() as state:
            state['jobs']['old']={'state':'completed','month':datetime.now(ZoneInfo('Europe/Prague')).strftime('%Y-%m'),
                'reserved_credits':200,'estimated_credits':-1}
        factory=Mock()
        with self.assertRaises(ValueError):call_model(self.store,'new',{},'instructions',{},client_factory=factory)
        factory.assert_not_called()

    def test_api_key_account_stops_before_thread_and_does_not_retry(self):
        client=Client()
        client.inner.request=Mock(return_value={'account':{'type':'apiKey'}})
        factory=Mock(return_value=client)
        with self.assertRaises(ValueError):call_model(self.store,'new',{},'instructions',{},client_factory=factory)
        self.assertEqual(client.inner.request.call_count,1)
        self.assertEqual(client.inner.request.call_args.args[0],'account/read')
        with self.assertRaises(ValueError):call_model(self.store,'new',{},'instructions',{},client_factory=factory)
        self.assertEqual(factory.call_count,1)

    def test_transport_rejects_second_turn_broader_permissions_and_tools(self):
        context=Path(self.temp.name).resolve();inner=Inner()
        guard=OneTurn(inner,context,SELECTED,'instructions','payload',{})
        start={'cwd':str(context),'model':SELECTED['model'],'ephemeral':True,'sandbox':'read-only','approvalPolicy':'never',
            'baseInstructions':'instructions','developerInstructions':'instructions'}
        guard.request('thread/start',start)
        turn={'threadId':'thread','model':SELECTED['model'],'effort':'medium','approvalPolicy':'never',
            'sandboxPolicy':{'type':'readOnly','networkAccess':False},'input':[{'type':'text','text':'payload'}],'outputSchema':{}}
        with self.assertRaises(ValueError):guard.request('turn/start',{**turn,'sandboxPolicy':{'type':'dangerFullAccess'}})
        guard.request('turn/start',turn)
        with self.assertRaises(ValueError):guard.request('turn/start',turn)
        with self.assertRaises(ValueError):guard.receive(lambda _:True)
        with self.assertRaises(ValueError):guard.request('thread/resume',{})

    def test_unverified_delivery_never_accepts_parseable_answer(self):
        client=Client();original=client.send_text
        def undelivered(**kwargs):
            receipt=original(**kwargs);receipt.delivered=False;return receipt
        client.send_text=undelivered
        with self.assertRaises(ValueError):call_model(self.store,'fixture',{},'instructions',{},client_factory=Mock(return_value=client))
        job=self.store._read()['jobs']['fixture']
        self.assertEqual(job['state'],'delivery_unknown');self.assertIn('raw_answer',job)
