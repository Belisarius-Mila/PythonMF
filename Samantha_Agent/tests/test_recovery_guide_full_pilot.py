from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app import recovery_guide_full_pilot as f
from app import recovery_guide_costing as costing
from app import recovery_guide_maintainer as m
from app.recovery_guide_sources import canonical_json, digest
from tests.test_recovery_guide import snapshot, answer, USAGE


class Client:
    def __enter__(self):
        return self
    def __exit__(self, *_):
        pass


class FullPilotTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.original = self.root / 'original.txt'
        self.snap = snapshot()
        self.original.write_text(self.snap.original.text)
        self.now = datetime(2026, 11, 7, 18, tzinfo=timezone.utc)
        self.calls = []
        self.enterContext(patch.object(f, 'STATE', self.root / 'private'))
        self.enterContext(patch.object(f, 'ORIGINAL', self.original))
        self.head = self.enterContext(patch.object(f, '_head', return_value=self.snap.head))
        self.enterContext(patch.object(f, '_code', return_value={'code':'a'}))
        self.enterContext(patch.object(f, '_calibration', return_value={'sha256':'b'}))
        self.enterContext(patch.object(f, 'collect_revision', return_value=self.snap))
        self.enterContext(patch.object(f.calibration, '_protocol', return_value={'version':'test'}))
        self.enterContext(patch.object(f.calibration, '_runtime', return_value={'server_version':'0.163.0','socket':'test'}))
        self.factory = self.enterContext(patch.object(f.calibration, '_client', side_effect=Client))
        self.enterContext(patch.object(f, '_tokenizer', side_effect=lambda script,data,**kw:len(data)))
        self.measurement = {'reference_counts':{}, 'planning_standard_credits_with_margin':1.0,
            'limits':dict(input_tokens=100000,
            output_tokens=1000,inspection_output_tokens=1000,max_calls=8,run_credits=50,month_credits=50,seconds=60)}
        self.enterContext(patch.object(f, '_measure', return_value=self.measurement))
        self.reviewer = self.enterContext(patch.object(f, 'Reviewer', return_value=self.call))

    def call(self, payload, kind):
        self.calls.append(kind)
        marker = json.loads((f.STATE/'controller'/f'{m.weekly_slot(self.now)}.json').read_text())
        self.assertEqual(marker['state'],'in_flight')
        value = ({'covered':[{'source':s['path'],'quote':s['text']} for s in payload['sources']],
                  'notes':'Dokumentace není živý audit.'} if kind=='inspect' else answer())
        return {'answer':value,'usage':USAGE}

    def prepare(self):
        return f.prepare()

    def run_trial(self, card=None, **kw):
        card = card or self.prepare()
        return f.run(approved_digest=card['approval_digest'], now=self.now, **kw)

    def test_nonpaid_packet_is_immutable_redacted_and_not_approval(self):
        card = self.prepare()
        self.assertEqual(card,self.prepare())
        self.assertEqual(self.factory.call_count,1)
        self.assertNotIn('socket',card['runtime'])
        self.assertNotIn('reference_counts',card['measurements'])
        self.assertEqual(card['model_turns_started'],0)
        self.assertFalse(card['production_writes'])
        self.assertFalse(card['application_scope_approved'])
        self.assertEqual((f.STATE/'packet.json').stat().st_mode & 0o777,0o600)
        self.assertFalse(self.calls)

    def test_wrong_approval_or_mutated_packet_never_connects(self):
        card=self.prepare()
        with self.assertRaises(ValueError):
            f.run(approved_digest='yes')
        path=f.STATE/'packet.json'; x=json.loads(path.read_text());x['packet']['model']='another-model'
        path.write_text(json.dumps(x))
        with self.assertRaises(ValueError):
            self.run_trial(card)
        self.assertEqual(self.factory.call_count,1)

    def test_full_synthetic_controller_and_repeat_next_week_use_same_receipt(self):
        card=self.prepare();r=self.run_trial(card)
        self.assertEqual(r['state'],'review')
        self.assertEqual(self.calls,['inspect','synthesize'])
        self.assertEqual(r['coverage'],2)
        self.assertEqual(r['publication'],'not_authorized')
        self.now+=timedelta(days=14)
        again=self.run_trial(card)
        self.assertTrue(again['replayed_receipt'])
        self.assertEqual(again['slot'],r['slot'])
        self.assertEqual(self.calls,['inspect','synthesize'])
        self.assertEqual(self.factory.call_count,2)

    def test_unknown_first_call_stops_without_synthesis_or_retry(self):
        def fail(*_):
            self.calls.append('unknown')
            raise TimeoutError('PRIVATE_ERROR')
        self.reviewer.return_value=fail
        card=self.prepare();r=self.run_trial(card)
        self.assertEqual(r['state'],'attention')
        self.assertEqual(r['model_calls'],1)
        self.assertNotIn('PRIVATE_ERROR',json.dumps(r))
        self.assertTrue(self.run_trial(card)['replayed_receipt'])
        self.assertEqual(self.calls,['unknown'])

    def test_process_death_preserves_marker_and_never_restarts(self):
        self.reviewer.return_value=lambda *_:(_ for _ in ()).throw(KeyboardInterrupt())
        card=self.prepare()
        with self.assertRaises(KeyboardInterrupt):
            self.run_trial(card)
        r=self.run_trial(card)
        self.assertEqual(r['state'],'in_flight')
        self.assertTrue(r['replayed_receipt'])

    def test_changed_main_or_original_before_first_send_needs_new_review(self):
        card=self.prepare();self.head.return_value='b'*40
        with self.assertRaises(ValueError):
            self.run_trial(card)
        self.assertFalse((f.STATE/'attempt.json').exists())
        self.head.return_value=self.snap.head;self.original.write_text('Changed')
        with self.assertRaises(ValueError):
            self.run_trial(card)
        self.assertFalse(self.calls)

    def test_scope_cannot_be_silently_replaced_during_prepare(self):
        self.prepare()
        with self.assertRaises(ValueError):
            f.prepare(project_only=True)

    def test_runtime_drift_reserves_slot_but_makes_no_model_call(self):
        card=self.prepare()
        with patch.object(f.calibration,'_runtime',return_value={'server_version':'new'}):
            r=self.run_trial(card)
        self.assertEqual(r['state'],'attention')
        self.assertFalse(self.calls)
        self.assertTrue(self.run_trial(card)['replayed_receipt'])

    def test_missing_telemetry_stops_before_synthesis(self):
        self.reviewer.return_value=lambda *_:{'answer':{},'usage':None}
        r=self.run_trial()
        self.assertEqual(r['state'],'attention')
        self.assertEqual(r['model_calls'],1)

    def test_refresh_preserves_original_and_budget_without_any_paid_attempt(self):
        card=self.prepare();before=(f.STATE/'packet.json').read_bytes()
        self.measurement['limits']['run_credits']=100
        updated=f.prepare(refresh=True)
        self.assertEqual((f.STATE/'packet.json').read_bytes(),before)
        self.assertEqual(updated['supersedes_approval_digest'],card['approval_digest'])
        self.assertEqual(updated['measurements']['limits']['run_credits'],50)
        self.assertTrue((f.STATE/'revisions'/(updated['approval_digest']+'.json')).is_file())
        self.assertFalse((f.STATE/'attempt.json').exists())
        self.assertFalse(self.calls)

    def test_refreshed_packet_needs_its_own_approval_and_shares_one_job(self):
        card=self.prepare();updated=f.prepare(refresh=True)
        with self.assertRaises(ValueError):f.run(approved_digest='0'*64)
        r=self.run_trial(updated)
        self.assertEqual(r['state'],'review')
        self.assertTrue(self.run_trial(updated)['replayed_receipt'])
        with self.assertRaisesRegex(ValueError,'already_reserved'):
            self.run_trial(card)
        self.assertEqual(self.calls,['inspect','synthesize'])

    def test_refresh_after_reserved_attempt_is_refused_without_connection(self):
        self.prepare();before=self.factory.call_count
        (f.STATE/'attempt.json').write_text('{"state":"reserved"}')
        with self.assertRaisesRegex(ValueError,'refresh_after_attempt'):
            f.prepare(refresh=True)
        self.assertEqual(self.factory.call_count,before)

    def test_refresh_also_refuses_orphaned_controller_marker(self):
        self.prepare()
        (f.STATE/'controller').mkdir()
        with self.assertRaisesRegex(ValueError,'refresh_after_attempt'):
            f.prepare(refresh=True)
        self.assertFalse(self.calls)

    def test_refresh_cannot_silently_expand_previous_budget(self):
        self.prepare();self.measurement['planning_standard_credits_with_margin']=51
        with self.assertRaisesRegex(ValueError,'previous_budget'):
            f.prepare(refresh=True)
        self.assertFalse((f.STATE/'revisions').exists())
        self.assertFalse(self.calls)

    def test_revision_symlink_cannot_substitute_an_approved_packet(self):
        self.prepare();folder=f.STATE/'revisions';folder.mkdir()
        (folder/('0'*64+'.json')).symlink_to(f.STATE/'packet.json')
        with self.assertRaisesRegex(ValueError,'unknown_approved_packet'):
            f.run(approved_digest='0'*64)
        self.assertFalse(self.calls)


class Wire:
    def __init__(self,context):
        self.context=context
        self.calls=[]
        self.permissions={'type':'readOnly','networkAccess':False}
    def request(self,method,params):
        self.calls.append((method,params))
        return ({'thread':{'id':'own'},'model':m.MODEL,'cwd':str(self.context),
            'approvalPolicy':'never','sandbox':self.permissions} if method=='thread/start' else {'turn':{'id':'turn'}})
    def receive(self,*_,**__):
        return {'params':{'turn':{'items':[{'type':'commandExecution'}]}}}


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.context=Path('/tmp/full-pilot-test').resolve()
        self.wire=Wire(self.context);self.before=[]
        self.payload={'original':'one','sources':[]};self.schema=m.INSPECT_SCHEMA
        self.guard=f.StandardTransport(self.wire,self.context,self.payload,self.schema,self.before.append)
        self.start={'cwd':str(self.context),'model':m.MODEL,'approvalPolicy':'never','sandbox':'read-only',
            'ephemeral':True,'baseInstructions':m.INSTRUCTIONS,'developerInstructions':m.INSTRUCTIONS,'config':{}}
        self.turn={'threadId':'own','model':m.MODEL,'effort':'medium','approvalPolicy':'never',
            'outputSchema':self.schema,'input':[{'type':'text','text':canonical_json(self.payload)}],
            'sandboxPolicy':{'type':'readOnly','networkAccess':False}}

    def test_standard_per_turn_only_and_one_new_thread(self):
        self.guard.request('thread/start',self.start)
        self.guard.request('turn/start',self.turn)
        self.assertEqual(self.before,['own'])
        p=self.wire.calls[-1][1]
        self.assertEqual(p['serviceTierForTurn'],'default')
        self.assertNotIn('serviceTier',p)
        for n in f.calibration.DISABLED_FEATURES:
            self.assertFalse(self.wire.calls[0][1]['config']['features.'+n])
        with self.assertRaises(ValueError):self.guard.request('turn/start',self.turn)
        with self.assertRaises(ValueError):self.guard.request('thread/start',self.start)

    def test_effective_permission_escalation_prevents_turn(self):
        self.wire.permissions={'type':'dangerFullAccess'}
        with self.assertRaises(ValueError):self.guard.request('thread/start',self.start)
        self.assertFalse(self.before)

    def test_modified_model_payload_schema_effort_or_permission_never_send(self):
        self.guard.request('thread/start',self.start)
        for key,value in [('model','wrong'),('input',[]),('outputSchema',{}),('effort','low'),
                          ('approvalPolicy','on-request'),('sandboxPolicy',{}),('threadId','foreign'),('serviceTier','default')]:
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.guard.request('turn/start',{**self.turn,key:value})
        self.assertEqual(len(self.wire.calls),1)

    def test_unexpected_tool_item_and_forbidden_rpc_are_observable(self):
        self.guard.receive(lambda _:True)
        self.assertEqual(self.guard.unexpected_items,{'commandExecution'})
        for method in ('thread/resume','config/write','command/exec'):
            with self.assertRaises(ValueError):self.guard.request(method,{})


class CostTests(unittest.TestCase):
    def test_unproven_margin_is_explicit_not_an_exact_tokenizer_mapping(self):
        fake=SimpleNamespace(get_encoding=lambda _:SimpleNamespace(encode_ordinary=lambda t:list(t)),
                             encoding_for_model=lambda _:(_ for _ in ()).throw(KeyError()))
        r=costing.measure(snapshot(),module=fake)
        self.assertFalse(r['model_tokenization_verified'])
        self.assertFalse(r['margin_is_proven_upper_bound'])
        self.assertFalse(r['hard_billing_cap'])
        self.assertGreater(r['planning_standard_credits_with_margin'],r['baseline_reference_credits'])
        self.assertGreaterEqual(r['limits']['run_credits'],r['planning_standard_credits_with_margin'])
        self.assertEqual(r['planned_calls'],2)


class ReviewerTests(unittest.TestCase):
    def setUp(self):
        from dataclasses import asdict
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve()
        self.enterContext(patch.object(f,'STATE',self.root))
        self.enterContext(patch.object(f,'_current',return_value=True))
        self.enterContext(patch.object(f.calibration,'_runtime',return_value={'socket':'same'}))
        self.enterContext(patch.object(f.calibration,'_socket',return_value='same'))
        self.snap=snapshot()
        self.payload={'original':asdict(self.snap.original),'sources':[asdict(s) for s in self.snap.sources]}
        self.packet={'runtime':{'socket':'same'},'snapshot':asdict(self.snap),
            'measurements':{'shards':[{'payload_sha256':digest(canonical_json(self.payload))}]}}
        self.wire=Wire(self.root/'context/1')
        original=self.wire.request
        def request(method,params):
            if method=='skills/list':return {'data':[{'skills':[],'errors':[]}]}
            if method=='turn/start':
                journal=json.loads((self.root/'turns/01.json').read_text())
                self.assertEqual(journal['state'],'delivery_unknown')
            return original(method,params)
        self.wire.request=request
        outer=self
        class SimClient:
            transport=outer.wire
            def read_effective_config(self,**_):return {'mcp_servers':{}}
            def start_thread(self,**kwargs):
                reply=self.transport.request('thread/start',{'cwd':str(kwargs['cwd']),
                    'model':kwargs['model'],'approvalPolicy':kwargs['approval_policy'],
                    'sandbox':kwargs['sandbox'],'ephemeral':kwargs['ephemeral'],
                    'baseInstructions':kwargs['base_instructions'],'developerInstructions':kwargs['developer_instructions'],
                    'config':kwargs['config_overrides']})
                return reply['thread']['id']
            def send_text(self,**kwargs):
                self.transport.request('turn/start',{'threadId':kwargs['thread_id'],'model':kwargs['model'],
                    'effort':kwargs['effort'],'approvalPolicy':kwargs['approval_policy'],
                    'outputSchema':kwargs['output_schema'],'input':[{'type':'text','text':kwargs['text']}],
                    'sandboxPolicy':kwargs['sandbox_policy']})
                if outer.failure:raise TimeoutError('PRIVATE_DETAIL')
                receipt={'answer':outer.answer,'thread_token_usage':USAGE,'delivered':True,'duration_ms':10}
                return SimpleNamespace(**receipt,as_dict=lambda:receipt)
        self.client=SimClient();self.answer='not-json';self.failure=False
        self.reviewer=f.Reviewer(self.client,self.packet)

    def test_bad_json_preserves_known_usage_and_original_transport(self):
        response=self.reviewer(self.payload,'inspect')
        self.assertIsNone(response['answer'])
        self.assertEqual(response['usage'],USAGE)
        journal=json.loads((self.root/'turns/01.json').read_text())
        self.assertEqual(journal['state'],'completed')
        self.assertEqual(journal['receipt']['thread_token_usage'],USAGE)
        self.assertIs(self.client.transport,self.wire)

    def test_timeout_keeps_turn_identity_and_unknown_marker(self):
        self.failure=True
        with self.assertRaises(TimeoutError):self.reviewer(self.payload,'inspect')
        journal=json.loads((self.root/'turns/01.json').read_text())
        self.assertEqual(journal['state'],'delivery_unknown')
        self.assertEqual(journal['turn_id'],'turn')
        self.assertEqual(journal['thread_id'],'own')
        self.assertIs(self.client.transport,self.wire)

    def test_payload_and_phase_mismatch_never_start_thread(self):
        for payload,kind in [({},'inspect'),(self.payload,'synthesize')]:
            with self.assertRaises(ValueError):self.reviewer(payload,kind)
        self.assertFalse(self.wire.calls)

    def test_source_drift_before_wire_prevents_send(self):
        with patch.object(f,'_current',side_effect=[True,False]):
            with self.assertRaises(ValueError):self.reviewer(self.payload,'inspect')
        self.assertFalse(any(m=='turn/start' for m,_ in self.wire.calls))


if __name__=='__main__':
    unittest.main()
