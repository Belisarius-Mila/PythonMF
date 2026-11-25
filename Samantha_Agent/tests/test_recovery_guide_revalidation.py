import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app import recovery_guide_revalidation as r
from app.recovery_guide_runtime_config import RuntimeConfig
from app.recovery_guide_sources import canonical_json,digest

class Counter:
    def __init__(self,config):pass
    def __call__(self,text):return len(text)//4
    def close(self):pass

class Revalidation(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.configpath=self.root/'activation.json'
        self.original={'enabled':True,'limits':{'input_tokens':240000,'run_credits':200,'month_credits':1000},'schedule':{'enabled':True,'hour':9,'role_policy_digest':'d'*64},'runtime_evidence':{'server_version':'old','input_tokens':240000,'protocol_sha256':'a'*64,'reference':'old proof'},'unchanged':'keep this'}
        self.configpath.write_text(canonical_json(self.original));self.configpath.chmod(0o600)
        self.observed={'server_version':'new','protocol_sha256':'a'*64,'socket':{'identity':'same'},'role_policy_digest':'d'*64}
        self.turns=0;self.fail=False;self.factory_calls=0;self.request='revalidation-test-one-01'
        for name,value in [('STATE',self.root/'state'),('_implementation',lambda:{'code':'v1'}),('owned_configuration',self.owned),('_observe',lambda client,config:self.observed),('_socket',lambda client:self.observed['socket']),('IsolatedCounter',Counter)]:self.enterContext(patch.object(r,name,value))
        self.enterContext(patch('app.routine_tasks.start_data_only_thread',return_value={'thread_id':'one'}))
    def owned(self):
        return RuntimeConfig(self.configpath,canonical_json(json.loads(self.configpath.read_text())),self.root,self.root),'agent'
    def client(self):
        self.factory_calls+=1;owner=self
        class Client:
            transport=object()
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def send_text(self,**kwargs):
                owner.turns+=1;self.transport.before_send('one')
                receipt=json.loads((r.STATE/owner.request/'receipt.json').read_text());owner.assertEqual(receipt['state'],'delivery_unknown')
                if owner.fail:raise TimeoutError('uncertain')
                plan=json.loads((r.STATE/owner.request/'plan.json').read_text())['plan'];answer=json.dumps(plan['expected_answer'])
                return SimpleNamespace(delivered=True,answer=answer,thread_token_usage={'input_tokens':160000,'cached_input_tokens':0,'output_tokens':40,'reasoning_output_tokens':0,'total_tokens':160040},as_dict=lambda:{'delivered':True,'answer':answer})
        return Client()
    def prepare(self):return r.prepare(request_id=self.request,client_factory=self.client)
    def runprobe(self,card):return r.run(request_id=self.request,approved_digest=card['digest'],confirmed=True,client_factory=self.client)
    def test_prepare_is_inert_stable_and_bounded(self):
        card=self.prepare();self.assertEqual(self.turns,0);self.assertEqual(self.configpath.read_text(),canonical_json(self.original));self.assertEqual(self.prepare(),card)
        self.assertLessEqual(card['plan']['input_reservation_tokens'],240000);self.assertEqual(card['plan']['acceptance_standard_credits'],15)
    def test_wrong_digest_and_missing_confirmation_never_start_model(self):
        card=self.prepare()
        for options in ({'approved_digest':'f'*64,'confirmed':True},{'approved_digest':card['digest'],'confirmed':False}):
            with self.assertRaises(ValueError):r.run(request_id=self.request,client_factory=self.client,**options)
        self.assertEqual(self.turns,0)
    def test_verified_probe_replays_receipt_and_accept_changes_only_runtime_evidence(self):
        card=self.prepare();first=self.runprobe(card);self.assertEqual(first['state'],'verified');self.assertEqual(self.runprobe(card),first);self.assertEqual(self.turns,1)
        with patch.object(r.configuration,'validate_payload',side_effect=lambda v:v):
            accepted=r.accept(request_id=self.request,approved_digest=card['digest'],confirmed=True,client_factory=self.client)
            self.assertEqual(accepted['state'],'accepted');self.assertEqual(r.accept(request_id=self.request,approved_digest=card['digest'],confirmed=True,client_factory=self.client)['state'],'accepted')
        after=json.loads(self.configpath.read_text());self.assertEqual({k:v for k,v in after.items() if k!='runtime_evidence'},{k:v for k,v in self.original.items() if k!='runtime_evidence'})
        self.assertEqual(after['runtime_evidence']['server_version'],'new');self.assertEqual(self.turns,1)
    def test_uncertain_delivery_is_not_retried_and_cannot_be_accepted(self):
        card=self.prepare();self.fail=True;one=self.runprobe(card);self.assertTrue(one['delivery_unknown']);self.fail=False
        self.assertEqual(self.runprobe(card),one);self.assertEqual(self.turns,1)
        with self.assertRaises(ValueError):r.accept(request_id=self.request,approved_digest=card['digest'],confirmed=True)
        self.assertEqual(json.loads(self.configpath.read_text()),self.original)
    def test_changed_activation_and_payload_stop_before_model(self):
        card=self.prepare();payload=r.STATE/self.request/'payload.json';payload.write_text('{}')
        with self.assertRaises(ValueError):self.runprobe(card)
        self.assertEqual(self.turns,0)
    def test_changed_code_stops_before_model(self):
        card=self.prepare()
        with patch.object(r,'_implementation',return_value={'code':'different'}):
            with self.assertRaises(ValueError):self.runprobe(card)
        self.assertEqual(self.turns,0)
    def test_changed_runtime_returns_attention_without_turn_and_never_retries(self):
        card=self.prepare();self.observed={**self.observed,'server_version':'different'}
        self.assertEqual(self.runprobe(card)['state'],'attention');self.assertEqual(self.runprobe(card)['state'],'attention');self.assertEqual(self.turns,0)
    def test_foreign_activation_edit_after_probe_is_not_overwritten(self):
        card=self.prepare();self.runprobe(card);changed={**self.original,'unchanged':'foreign edit'};self.configpath.write_text(canonical_json(changed))
        with self.assertRaises(ValueError):r.accept(request_id=self.request,approved_digest=card['digest'],confirmed=True)
        self.assertEqual(json.loads(self.configpath.read_text()),changed)
    def test_exact_optional_budget_refresh_preserves_monthly_limit_and_other_settings(self):
        budget={'run_credits':250,'inspection_output_tokens':3000,'month_credits':1000}
        with patch.object(r,'_budget_plan',return_value=budget):
            card=r.prepare(request_id=self.request,client_factory=self.client,refresh_budget=True)
        self.assertEqual(card['plan']['budget_refresh'],budget)
        with patch.object(r,'_assert_budget') as guard:
            self.runprobe(card)
            with patch.object(r.configuration,'validate_payload',side_effect=lambda v:v):
                r.accept(request_id=self.request,approved_digest=card['digest'],confirmed=True,client_factory=self.client)
            self.assertEqual(guard.call_count,2)
        after=json.loads(self.configpath.read_text());self.assertEqual(after['limits']['run_credits'],250);self.assertEqual(after['schedule']['run_credits'],250)
        self.assertEqual(after['limits']['month_credits'],1000);self.assertEqual(after['limits']['inspection_output_tokens'],3000);self.assertEqual(after['unchanged'],'keep this')
    def test_changed_budget_sources_block_before_paid_turn(self):
        card=self.prepare()
        with patch.object(r,'_assert_budget',side_effect=ValueError('source changed')):
            with self.assertRaises(ValueError):self.runprobe(card)
        self.assertEqual(self.turns,0)

    def test_existing_request_cannot_silently_change_budget_scope(self):
        self.prepare()
        with self.assertRaises(ValueError):r.prepare(request_id=self.request,refresh_budget=True,client_factory=self.client)
        self.assertEqual(self.turns,0)

    def test_alias_state_is_refused(self):
        destination=self.root/'outside';destination.mkdir();r.STATE.symlink_to(destination,target_is_directory=True)
        with self.assertRaises(ValueError):self.prepare()
