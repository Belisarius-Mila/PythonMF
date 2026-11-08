import copy
from dataclasses import replace
import json
from pathlib import Path
import socket
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app import recovery_guide_anchor_exact_pilot as p
from app import recovery_guide_anchor_exact_plan as plan
from app import recovery_guide_anchor_exact_worker as worker
from app import recovery_guide_anchor_protocol as protocol
from app.recovery_guide_sources import canonical_json,digest
from app.codex_appserver import CodexAppServerClient,CodexVersion,AppServerTimeout,AppServerRpcError
from app.recovery_guide_anchors import AnchorError
from tests.test_recovery_guide_anchor_full_plan import snapshot,source,ENC,MODULE
from tests.test_recovery_guide_trial import Wire as BaseWire


class Wire(BaseWire):
    def __init__(self,path):
        super().__init__(path)
        self.turns=self.threads=0;self.bad=None;self.reuse=False

    def request(self,method,params):
        if method=='thread/start':
            self.threads+=1;reply=super().request(method,params)
            reply['thread']['id']='thread-'+str(1 if self.reuse else self.threads)
            return reply
        if method!='turn/start':return super().request(method,params)
        self.calls.append((method,copy.deepcopy(params)));self.turns+=1
        record=json.loads((p.STATE/'turns'/f'{self.turns:02d}.json').read_text())
        job=json.loads((p.STATE/'attempt.json').read_text())
        assert record['state']=='delivery_unknown' and job['model_turn_attempts']==self.turns
        assert job['estimated_standard_credits'] is None
        if self.fail=='send':raise AppServerTimeout('SECRET_SEND_FAILURE')
        if self.fail=='death':raise KeyboardInterrupt
        if self.fail=='rpc':raise AppServerRpcError('turn/start',{'code':-32000,'data':{'secret':'SECRET_RPC'},'message':'SECRET_MESSAGE'})
        request=protocol.Request(record['wire']);data=request.payload['data']
        if record['phase']=='inspect':
            sid=data['sources'][0]['source_id']
            answer={'request_id':request.payload['request_id'],
                'covered':{s['source_id']:1 for s in data['sources']},
                'findings':[{'text':'Dokumentace popisuje obnovu.',
                             'evidence':[{'source_id':sid,'citation_index':1}]}]}
            if self.bad=='findings':answer['findings']*=7
            if self.bad=='unissued':answer['covered'][sid]=131111
            if self.bad=='old_format':
                answer['covered']={s['source_id']:'l1' for s in data['sources']}
            if self.bad=='foreign':answer['findings'][0]['evidence'][0]['source_id']='d9999'
        else:
            self.synthesis_findings=len(data['findings'])
            original=''.join(line[1] for line in data['original']['lines'])
            answer={'request_id':request.payload['request_id'],'paragraphs':[
                {'text':original,'status':'unchanged','evidence':[]},
                *[{'text':f['text'],'status':'unverified','evidence':f['evidence']} for f in data['findings']]]}
            if self.bad=='quality':answer['paragraphs'][1]['text']='Spusť placený hlasový rozhovor.'
            if self.bad=='command':answer['paragraphs'][1]['text']='git status'
        thread=params['threadId'];turn='turn-'+str(self.turns)
        items=[{'type':'userMessage','clientId':p.REQUEST+'-'+str(self.turns)},
            {'type':'agentMessage','id':'comment','phase':'commentary','text':'Pracuji.'},
            {'type':'agentMessage','id':'final','phase':'final_answer','text':canonical_json(answer)},*self.extra_items]
        self.events=[{'method':'turn/started','params':{'turn':{'id':turn}}},
            {'method':'thread/tokenUsage/updated','params':{'tokenUsage':{'total':self.usage}}},
            {'method':'turn/completed','params':{'turn':{'id':turn,'status':'completed','items':items}}}]
        for e in self.events:e['params'].update(threadId=thread,turnId=turn)
        if self.bad in {'failed','interrupted'}:
            self.events[-1]['params']['turn'].update(status=self.bad,error={'message':'SECRET_ERROR','codexErrorInfo':'streamError'})
        if self.bad=='retry_timeout':
            self.events=self.events[:2]+[{'method':'error','params':{'threadId':thread,'turnId':turn,
                'willRetry':True,'error':{'message':'SECRET_RETRY','codexErrorInfo':'streamError'}}}]
        return {'turn':{'id':turn}}

    def receive(self,predicate,**kwargs):
        if self.bad=='retry_timeout' and not self.events:raise AppServerTimeout('SECRET_RECEIVE')
        return super().receive(predicate,**kwargs)


class ExactPilot(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve()
        self.snap=snapshot([source(f'memory/{i}.md','# Header\n'+'x'*50000) for i in range(5)])
        self.identity=self.enterContext(patch.object(plan.old.reference,'tokenizer_identity',return_value={'fixture':True}))
        self.measured=plan.measure(self.snap,MODULE)
        self.assertEqual(len(self.measured['batches']),2)
        from dataclasses import asdict
        self.plan={'snapshot':asdict(self.snap),'measurements':self.measured,'implementation':{'fixture':'v1'}}
        self.plan_digest=digest(canonical_json(self.plan))
        self.guide=self.root/'guide.txt';self.guide.write_text(self.snap.original.text)
        self.enterContext(patch.object(p,'STATE',self.root/'state'))
        self.enterContext(patch.object(plan.old,'ORIGINAL',self.guide))
        self.enterContext(patch.object(plan.old.old,'_head',return_value=self.snap.head))
        self.enterContext(patch.object(plan,'_code',return_value={'fixture':'v1'}))
        self.enterContext(patch.object(p,'_code',return_value={'adapter':'v1'}))
        self.enterContext(patch.object(p,'_load_plan',return_value=self.plan))
        self.enterContext(patch.object(p.calibration,'_protocol',return_value={'version':p.calibration.PEER}))
        self.offline=self.enterContext(patch.object(p,'_offline',side_effect=self.worker))
        self.sock=socket.socket(socket.AF_UNIX);self.addCleanup(self.sock.close)
        path=self.root/'rpc.sock';self.sock.bind(str(path));self.wire=Wire(path)
        self.factories=0;self.duration=None

    def worker(self,action,frozen,**kwargs):
        return worker.perform(action,frozen,module=MODULE,**kwargs)

    def factory(self):
        self.factories+=1;client=CodexAppServerClient.__new__(CodexAppServerClient)
        client.transport=self.wire;client.server_version=CodexVersion.parse('codex-cli '+self.wire.version)
        client.version=SimpleNamespace(raw='0.166.0')
        if self.duration:
            original=client.send_text
            def send(**kwargs):
                result=original(**kwargs)
                ms=self.duration(self.wire.turns)
                return replace(result,duration_ms=ms) if ms is not None else result
            client.send_text=send
        return client

    def prepare(self,**kwargs):
        return p.prepare(plan_digest=self.plan_digest,client_factory=self.factory,**kwargs)

    def run_trial(self,card=None):
        return p.run(approved_digest=(card or self.prepare())['approval_digest'],client_factory=self.factory)

    def test_new_executor_is_not_the_closed_job(self):
        from app import recovery_guide_anchor_full_pilot as closed
        self.assertNotEqual(p.STATE,closed.STATE)
        self.assertNotEqual(p.REQUEST,closed.REQUEST)
        self.assertEqual(self.prepare()['protocol_version'],'source_citation_index_v1')

    def test_unissued_index_fails_closed_after_one_receipt(self):
        a=self.prepare();self.wire.bad='unissued';r=self.run_trial(a)
        self.assertFalse(r['accepted']);self.assertEqual(self.wire.turns,1)
        self.assertEqual(r['reason'],'exact_reference_outside_domain')
        self.assertEqual(self.run_trial(a),r);self.assertEqual(self.factories,2)
        raw=json.loads((p.STATE/'turns/01.json').read_text())
        self.assertIn('131111',raw['receipt']['answer'])

    def test_old_wire_format_has_no_automatic_fallback(self):
        self.wire.bad='old_format';r=self.run_trial()
        self.assertFalse(r['accepted']);self.assertEqual(self.wire.turns,1)

    def test_foreign_source_cannot_enter_synthesis(self):
        self.wire.bad='foreign';r=self.run_trial()
        self.assertFalse(r['accepted']);self.assertEqual(self.wire.turns,1)

    def test_persisted_wire_domain_hashes_match_real_requests(self):
        self.assertTrue(self.run_trial()['accepted'])
        for path in (p.STATE/'turns').glob('*.json'):
            row=json.loads(path.read_text());wire=protocol.Request(row['wire'])
            self.assertEqual(row['reference_index_sha256'],wire.payload['reference_index_sha256'])
            self.assertEqual(row['wire_request_sha256'],wire.sha256)
            self.assertNotIn('anchor_id',canonical_json(wire.schema))

    def test_prepare_is_nonpaid_private_immutable_and_redacted(self):
        a=self.prepare();self.assertEqual(a,self.prepare());self.assertEqual(self.factories,1)
        self.assertEqual(self.wire.threads,0);self.assertEqual(a['measurements']['planned_model_calls'],3)
        for secret in ('SECRET_ACCOUNT','PRIVATE_CONFIG',str(self.root),'"socket"'):
            self.assertNotIn(secret,canonical_json(a))
        self.assertEqual((p.STATE/'packet.json').stat().st_mode & 0o777,0o600)
        self.assertFalse(a['publication_authorized']);self.assertTrue(a['frozen_inputs_current'])
        self.assertTrue(a['execution_adapter_implemented']);self.assertEqual(a['new_command_allowlist'],[])

    def test_status_never_creates_state_or_connects(self):
        self.assertEqual(p.status()['state'],'not_started');self.assertFalse(p.STATE.exists())
        self.assertEqual(self.factories,0)
        a=self.prepare();self.assertEqual(p.status()['state'],'not_started')
        r=self.run_trial(a);self.assertEqual(p.status(),r);self.assertEqual(self.factories,2)

    def test_all_batches_then_complete_synthesis_use_one_connection_and_standard(self):
        r=self.run_trial();self.assertTrue(r['accepted']);self.assertEqual(r['state'],'exact_index_candidate_validated')
        self.assertEqual(r['model_turn_attempts'],3);self.assertEqual(r['accepted_inspection_batches'],2)
        self.assertEqual(r['completed_receipts'],3);self.assertEqual(r['estimated_standard_credits'],.06)
        self.assertEqual(self.wire.synthesis_findings,2);self.assertEqual(self.factories,2)
        turns=[v for m,v in self.wire.calls if m=='turn/start']
        self.assertEqual(len({v['threadId'] for v in turns}),3)
        for v in turns:
            self.assertEqual(v['serviceTierForTurn'],'default');self.assertNotIn('serviceTier',v)
            self.assertEqual(v['effort'],'medium');self.assertEqual(v['approvalPolicy'],'never')
            self.assertEqual(v['sandboxPolicy'],{'type':'readOnly','networkAccess':False})
        self.assertEqual(digest((p.STATE/'candidate.txt').read_text()),r['candidate_sha256'])
        self.assertEqual(self.guide.read_text(),self.snap.original.text);self.assertFalse(r['publication_authorized'])

    def test_replay_never_reconnects_or_resumes(self):
        a=self.prepare();r=self.run_trial(a);self.assertEqual(self.run_trial(a),r)
        self.assertEqual(self.factories,2);self.assertEqual(self.wire.turns,3)

    def test_wrong_or_tampered_card_never_connects(self):
        a=self.prepare()
        for bad in ('','yes','0'*64):
            with self.assertRaises(ValueError):p.run(approved_digest=bad,client_factory=self.factory)
        env=json.loads((p.STATE/'packet.json').read_text());env['packet']['model']='other'
        (p.STATE/'packet.json').write_text(json.dumps(env))
        with self.assertRaises(ValueError):self.run_trial(a)
        self.assertEqual(self.factories,1);self.assertFalse((p.STATE/'attempt.json').exists())

    def test_source_or_code_drift_blocks_before_job_reservation(self):
        a=self.prepare()
        with patch.object(p,'_code',return_value={}):
            with self.assertRaises(ValueError):self.run_trial(a)
        self.guide.write_text('changed')
        with self.assertRaises(ValueError):self.run_trial(a)
        self.assertFalse((p.STATE/'attempt.json').exists())

    def test_socket_replacement_stops_before_thread(self):
        a=self.prepare();other=socket.socket(socket.AF_UNIX);self.addCleanup(other.close)
        path=self.root/'other.sock';other.bind(str(path));self.wire.socket_path=path
        r=self.run_trial(a);self.assertFalse(r['accepted']);self.assertEqual(self.wire.threads,0)

    def test_source_drift_after_thread_start_stops_before_send(self):
        a=self.prepare();original=self.wire.request
        def request(method,params):
            result=original(method,params)
            if method=='thread/start':self.guide.write_text('changed')
            return result
        self.wire.request=request;r=self.run_trial(a)
        self.assertFalse(r['accepted']);self.assertEqual(self.wire.turns,0)

    def test_unknown_send_preserves_marker_and_never_retries(self):
        a=self.prepare();self.wire.fail='send';r=self.run_trial(a)
        self.assertEqual(r['state'],'attention');self.assertIsNone(r['estimated_standard_credits'])
        self.assertEqual(r['known_standard_credits'],0);self.assertEqual(self.run_trial(a),r)
        self.assertEqual(self.wire.turns,1);self.assertNotIn('SECRET_SEND_FAILURE',canonical_json(r))

    def test_rpc_error_data_remains_private_and_never_authorizes_retry(self):
        a=self.prepare();self.wire.fail='rpc';r=self.run_trial(a)
        self.assertFalse(r['accepted']);self.assertEqual(self.wire.turns,1);self.assertEqual(self.run_trial(a),r)
        raw=json.loads((p.STATE/'turns/01.json').read_text())
        self.assertEqual(raw['structured_error']['code'],-32000)
        self.assertIn('SECRET_RPC',canonical_json(raw));self.assertNotIn('SECRET',canonical_json(r))

    def test_terminal_failure_preserves_usage_and_structured_error_without_retry(self):
        a=self.prepare();self.wire.bad='failed';r=self.run_trial(a)
        self.assertFalse(r['accepted']);self.assertEqual(self.wire.turns,1);self.assertEqual(self.run_trial(a),r)
        self.assertEqual(r['known_standard_credits'],.02);self.assertEqual(r['terminal_receipts'],1)
        raw=json.loads((p.STATE/'turns/01.json').read_text())
        self.assertEqual(raw['terminal_status'],'failed');self.assertFalse(raw['delivery_unknown'])
        self.assertIn('SECRET_ERROR',canonical_json(raw));self.assertNotIn('SECRET_ERROR',canonical_json(r))

    def test_terminal_interruption_never_starts_another_phase(self):
        self.wire.bad='interrupted';r=self.run_trial()
        self.assertEqual(r['state'],'attention');self.assertEqual(self.wire.turns,1)
        self.assertEqual(r['estimated_standard_credits'],.02)

    def test_retry_notification_and_partial_usage_never_authorize_resend_or_final_cost(self):
        a=self.prepare();self.wire.bad='retry_timeout';r=self.run_trial(a)
        self.assertEqual(r['state'],'attention');self.assertEqual(self.wire.turns,1)
        self.assertIsNone(r['estimated_standard_credits']);self.assertEqual(self.run_trial(a),r)
        raw=json.loads((p.STATE/'turns/01.json').read_text())
        self.assertTrue(raw['structured_error']['will_retry']);self.assertIsNotNone(raw['last_observed_usage'])
        self.assertNotIn('SECRET_RETRY',canonical_json(r))

    def test_process_death_after_wire_never_resumes(self):
        a=self.prepare();self.wire.fail='death'
        with self.assertRaises(KeyboardInterrupt):self.run_trial(a)
        r=self.run_trial(a);self.assertEqual(r['state'],'in_flight');self.assertIsNone(r['estimated_standard_credits'])
        self.assertEqual(self.wire.turns,1);self.assertEqual(self.factories,2)

    def test_process_death_between_batches_keeps_first_receipt_and_no_new_action(self):
        a=self.prepare();original=self.worker
        def call(action,frozen,**kwargs):
            if action=='request' and kwargs.get('index')==2:raise KeyboardInterrupt
            return original(action,frozen,**kwargs)
        self.offline.side_effect=call
        with self.assertRaises(KeyboardInterrupt):self.run_trial(a)
        r=self.run_trial(a);self.assertEqual(self.wire.turns,1);self.assertEqual(r['known_standard_credits'],.02)
        self.assertEqual(r['accepted_inspection_batches'],1);self.assertEqual(self.factories,2)

    def test_bad_findings_stop_before_second_paid_turn(self):
        self.wire.bad='findings';r=self.run_trial()
        self.assertFalse(r['accepted']);self.assertEqual(self.wire.turns,1)
        self.assertEqual(r['estimated_standard_credits'],.02)

    def test_synthesis_quality_failure_preserves_three_receipts_and_no_candidate(self):
        self.wire.bad='quality';r=self.run_trial()
        self.assertFalse(r['accepted']);self.assertEqual(self.wire.turns,3)
        self.assertEqual(r['estimated_standard_credits'],.06);self.assertFalse((p.STATE/'candidate.txt').exists())

    def test_unchanged_command_gate_is_not_silently_relaxed(self):
        self.wire.bad='command';r=self.run_trial()
        self.assertFalse(r['accepted']);self.assertEqual(self.wire.turns,3)
        self.assertFalse((p.STATE/'candidate.txt').exists())

    def test_synthesis_400_seconds_is_allowed_only_by_new_900_second_plan(self):
        self.duration=lambda index:400240 if index==3 else None
        self.assertTrue(self.run_trial()['accepted'])

    def test_synthesis_over_900_seconds_is_rejected_and_cost_preserved(self):
        self.duration=lambda index:900001 if index==3 else None
        r=self.run_trial();self.assertFalse(r['accepted']);self.assertEqual(r['estimated_standard_credits'],.06)

    def test_inspection_over_300_seconds_stops_immediately(self):
        self.duration=lambda index:300001
        r=self.run_trial();self.assertFalse(r['accepted']);self.assertEqual(self.wire.turns,1)

    def test_tokenizer_drift_stops_before_thread(self):
        a=self.prepare();original=self.worker
        def call(action,frozen,**kwargs):
            data=original(action,frozen,**kwargs)
            if action=='request':data['tokenizer']={'changed':True}
            return data
        self.offline.side_effect=call;r=self.run_trial(a)
        self.assertFalse(r['accepted']);self.assertEqual(self.wire.threads,0)

    def test_missing_synthesis_history_stops_before_last_thread(self):
        a=self.prepare();original=self.worker
        def call(action,frozen,**kwargs):
            if action=='request' and kwargs.get('index')==3:kwargs['history']=kwargs['history'][:1]
            return original(action,frozen,**kwargs)
        self.offline.side_effect=call;r=self.run_trial(a)
        self.assertFalse(r['accepted']);self.assertEqual(self.wire.turns,2)
        self.assertEqual(r['known_standard_credits'],.04)

    def test_total_time_exhaustion_stops_before_new_thread(self):
        a=self.prepare()
        values=iter([0,7000,7001])
        with patch.object(p,'time',SimpleNamespace(monotonic=lambda:next(values))):r=self.run_trial(a)
        self.assertFalse(r['accepted']);self.assertEqual(self.wire.threads,0)

    def test_insufficient_remaining_reserve_stops_before_new_thread(self):
        a=self.prepare()
        with patch.object(p,'_phase_limits',side_effect=lambda packet,index:('inspect',10**9,4096)):
            r=self.run_trial(a)
        self.assertFalse(r['accepted']);self.assertEqual(self.wire.threads,0)

    def test_missing_usage_is_unknown_and_does_not_start_next_phase(self):
        self.wire.usage=None;r=self.run_trial()
        self.assertIsNone(r['estimated_standard_credits']);self.assertEqual(self.wire.turns,1)

    def test_over_output_usage_is_saved_even_when_rejected(self):
        self.wire.usage.update(outputTokens=50000,totalTokens=50100)
        r=self.run_trial();self.assertEqual(self.wire.turns,1)
        self.assertGreater(r['known_standard_credits'],12);self.assertFalse(r['accepted'])

    def test_unexpected_tool_event_stops_with_numeric_known_receipt(self):
        self.wire.extra_items=[{'type':'commandExecution','id':'unexpected'}]
        r=self.run_trial();self.assertFalse(r['accepted']);self.assertEqual(self.wire.turns,1)
        self.assertEqual(r['estimated_standard_credits'],.02)

    def test_server_cannot_reuse_previous_thread_for_next_phase(self):
        self.wire.reuse=True;r=self.run_trial()
        self.assertFalse(r['accepted']);self.assertEqual(self.wire.turns,1);self.assertEqual(self.wire.threads,2)
        self.assertEqual(r['estimated_standard_credits'],.02)

    def test_pre_wire_marker_failure_sends_no_model_action(self):
        a=self.prepare();original=p.atomic_write_json
        def save(path,value,**kwargs):
            if value.get('state')=='delivery_unknown':raise OSError('SECRET_DISK')
            return original(path,value,**kwargs)
        with patch.object(p,'atomic_write_json',side_effect=save):r=self.run_trial(a)
        self.assertEqual(self.wire.turns,0);self.assertFalse(r['accepted']);self.assertEqual(self.run_trial(a),r)

    def test_pre_attempt_refresh_is_immutable_but_attempt_cannot_be_reset(self):
        a=self.prepare();b=self.prepare(refresh=True)
        self.assertNotEqual(a['approval_digest'],b['approval_digest'])
        self.assertEqual(json.loads((p.STATE/'packet.json').read_text())['approval_digest'],a['approval_digest'])
        self.assertTrue(self.run_trial(b)['accepted'])
        with self.assertRaises(ValueError):self.prepare(refresh=True)
        with self.assertRaises(ValueError):self.run_trial(a)

    def test_changed_plan_requires_explicit_nonpaid_refresh(self):
        self.prepare()
        with self.assertRaises(ValueError):p.prepare(plan_digest='f'*64,client_factory=self.factory)
        self.assertEqual(self.factories,1)

    def test_symlinked_artifacts_are_refused(self):
        self.prepare();(p.STATE/'attempt.json').symlink_to(self.root/'outside')
        with self.assertRaises(ValueError):self.run_trial()

    def test_plan_recalculation_drift_prevents_card(self):
        self.offline.side_effect=AnchorError('exact_pilot_plan_changed')
        with self.assertRaises(ValueError):self.prepare()
        self.assertFalse((p.STATE/'packet.json').exists());self.assertEqual(self.factories,0)


if __name__=='__main__':unittest.main()
