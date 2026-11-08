import copy
from dataclasses import replace
import json
from pathlib import Path
import socket
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app import recovery_guide_anchor_trial as t
from app import recovery_guide_anchor_costing as c
from app import recovery_guide_anchor_protocol as p
from app.recovery_guide_anchors import Catalogue
from app.recovery_guide_sources import Snapshot, Source, canonical_json, digest
from app.codex_appserver import CodexAppServerClient, CodexVersion, AppServerTimeout
from tests.test_recovery_guide import ORIGINAL
from tests.test_recovery_guide_trial import Wire as BaseWire


def snapshot():
    return Snapshot('a'*40, Source('original_guide', digest(ORIGINAL), ORIGINAL, 'previous_version'),
        tuple(Source(path, digest('# Doc\n'+quote+'\n'), '# Doc\n'+quote+'\n', 'documented_not_live')
              for path, quote in c.CASES.items()))


class Wire(BaseWire):
    def __init__(self, path):
        super().__init__(path)
        self.turns = self.threads = 0
        self.bad = None

    def request(self, method, params):
        if method == 'thread/start':
            self.threads += 1
            reply = super().request(method, params)
            reply['thread']['id'] = 'test-thread-'+str(self.threads)
            return reply
        if method != 'turn/start':
            return super().request(method, params)
        self.calls.append((method, copy.deepcopy(params)))
        self.turns += 1
        job = json.loads((t.STATE/'attempt.json').read_text())
        raw = json.loads((t.STATE/'turns'/f'{self.turns:02d}.json').read_text())
        assert job['model_turn_attempts'] == self.turns and job['state'] == 'in_flight'
        assert raw['state'] == 'delivery_unknown'
        if self.fail == 'send':
            raise AppServerTimeout('SECRET_TIMEOUT')
        if self.fail == 'death':
            raise KeyboardInterrupt
        cat = Catalogue(snapshot()); request = p.Request(raw['request'])
        if self.turns == 1:
            answer = json.loads(c.fixture(cat, request))
            if self.bad == 'quote': answer['quote'] = 'invented'
            if self.bad == 'long': answer['findings'][0]['text'] = 'x'*1501
            if self.bad == 'header': answer['covered'][cat.document_ids[0]] = 'l1'
            if self.bad == 'missing': answer['findings'].pop()
        else:
            answer = {'request_id': request.payload['request_id'], 'paragraphs': [
                {'text': ORIGINAL.strip(), 'status': 'unchanged', 'evidence': []},
                *[{'text': 'Zkušební neověřený odstavec.', 'status': 'unverified',
                   'evidence': [{'source_id': sid, 'anchor_id': aid}]} for sid, aid in c.expected_pairs(cat)]]}
            if self.bad == 'original': answer['paragraphs'][0]['text'] += ' Změna.'
            if self.bad == 'status': answer['paragraphs'][1]['status'] = 'documented'
        thread = params['threadId']; turn = 'turn-'+str(self.turns)
        items = [{'type': 'userMessage', 'clientId': t.REQUEST+'-'+str(self.turns)},
            {'type': 'agentMessage', 'id': 'comment', 'phase': 'commentary', 'text': 'Pracuji.'},
            {'type': 'agentMessage', 'id': 'final', 'phase': 'final_answer', 'text': json.dumps(answer)}]
        items.extend(self.extra_items)
        self.events = [
            {'method': 'turn/started', 'params': {'turn': {'id': turn}}},
            {'method': 'thread/tokenUsage/updated', 'params': {'tokenUsage': {'total': self.usage}}},
            {'method': 'turn/completed', 'params': {'turn': {'id': turn, 'status': 'completed', 'items': items}}}]
        for event in self.events:
            event['params'].update(threadId=thread, turnId=turn)
        return {'turn': {'id': turn}}


class Trial(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve(); self.snap = snapshot()
        self.sock = socket.socket(socket.AF_UNIX); self.addCleanup(self.sock.close)
        path = self.root/'rpc.sock'; self.sock.bind(str(path)); self.wire = Wire(path)
        self.guide = self.root/'guide.txt'; self.guide.write_text(ORIGINAL)
        self.enterContext(patch.object(t, 'STATE', self.root/'state'))
        self.enterContext(patch.object(t, 'ORIGINAL', self.guide))
        self.enterContext(patch.object(t, '_head', return_value=self.snap.head))
        self.enterContext(patch.object(t, '_snapshot', return_value=self.snap))
        self.enterContext(patch.object(t, '_code', return_value={'fixture': 'v1'}))
        self.enterContext(patch.object(t.calibration, '_protocol', return_value={'version': t.calibration.PEER}))
        self.measured = {'tokenizer': {'fixture': True}, 'input_acceptance_tokens': {'inspect': 11000, 'synthesize': 11000},
            'output_acceptance_tokens': c.OUTPUT_LIMITS, 'acceptance_standard_credits': 10,
            'inspect_request_sha256': p.inspection_request(Catalogue(self.snap), tuple(c.CASES)).sha256}
        self.enterContext(patch.object(t, '_measure', side_effect=lambda _: copy.deepcopy(self.measured)))
        self.count = self.enterContext(patch.object(t, '_count_request', return_value={'tokens': 100, 'tokenizer': {'fixture': True}}))
        self.factories = 0

    def factory(self):
        self.factories += 1
        client = CodexAppServerClient.__new__(CodexAppServerClient)
        client.transport = self.wire
        client.server_version = CodexVersion.parse('codex-cli '+self.wire.version)
        client.version = SimpleNamespace(raw='0.166.0')
        return client

    def prepare(self, **kwargs):
        return t.prepare(client_factory=self.factory, **kwargs)

    def run_trial(self, card=None):
        return t.run(approved_digest=(card or self.prepare())['approval_digest'], client_factory=self.factory)

    def test_nonpaid_immutable_card_redacts_sources_socket_account_and_config(self):
        a = self.prepare(); self.assertEqual(a, self.prepare())
        self.assertEqual(self.factories, 1); self.assertEqual(self.wire.threads, 0)
        public = json.dumps(a)
        for secret in ('SECRET_ACCOUNT', 'PRIVATE_CONFIG', str(self.root), 'socket'):
            self.assertNotIn(secret, public)
        self.assertFalse(a['full_corpus_review']); self.assertEqual(a['max_turns'], 2)
        self.assertEqual((t.STATE/'packet.json').stat().st_mode & 0o777, 0o600)

    def test_two_fresh_threads_one_connection_standard_per_turn_and_exact_schema(self):
        r = self.run_trial(); self.assertEqual(r['state'], 'small_trial_passed')
        self.assertEqual(r['model_turn_attempts'], 2); self.assertEqual(self.factories, 2)
        turns = [v for m,v in self.wire.calls if m=='turn/start']
        self.assertEqual(len(turns), 2)
        for turn in turns:
            self.assertEqual(turn['serviceTierForTurn'], 'default'); self.assertNotIn('serviceTier', turn)
            self.assertEqual(turn['sandboxPolicy'], {'type':'readOnly','networkAccess':False})
            self.assertNotIn('quote', canonical_json(turn['outputSchema']))
        threads = [v for m,v in self.wire.calls if m=='thread/start']
        self.assertNotEqual(turns[0]['threadId'], turns[1]['threadId'])
        self.assertTrue(all(v['ephemeral'] and v['baseInstructions']==c.INSTRUCTIONS for v in threads))
        self.assertTrue(all(v['config']['features.shell_tool'] is False for v in threads))
        self.assertFalse(r['publication_authorized']); self.assertFalse(r['full_corpus_review'])
        self.assertEqual(r['estimated_standard_credits'], .04)

    def test_wrong_or_tampered_approval_never_connects(self):
        a=self.prepare()
        for bad in ('','yes','0'*64):
            with self.assertRaises(ValueError):t.run(approved_digest=bad,client_factory=self.factory)
        saved=json.loads((t.STATE/'packet.json').read_text());saved['packet']['max_turns']=99
        (t.STATE/'packet.json').write_text(json.dumps(saved))
        with self.assertRaises(ValueError):self.run_trial(a)
        self.assertEqual(self.factories,1);self.assertFalse((t.STATE/'attempt.json').exists())

    def test_replay_after_pass_never_reconnects_or_creates_guide(self):
        a=self.prepare();r=self.run_trial(a);self.assertEqual(self.run_trial(a),r)
        self.assertEqual(self.factories,2);self.assertEqual(self.wire.turns,2)
        self.assertEqual(self.guide.read_text(),ORIGINAL)
        self.assertFalse(list(t.STATE.glob('*.txt')))

    def test_timeout_is_unknown_and_never_retried(self):
        a=self.prepare();self.wire.fail='send';r=self.run_trial(a)
        self.assertEqual(r['state'],'attention');self.assertIsNone(r['estimated_standard_credits'])
        self.assertEqual(self.run_trial(a),r);self.assertEqual(self.wire.turns,1)
        raw=json.loads((t.STATE/'turns/01.json').read_text())
        self.assertTrue(raw['delivery_unknown']);self.assertNotIn('SECRET_TIMEOUT',json.dumps(r))

    def test_process_death_before_receipt_never_starts_again(self):
        a=self.prepare()
        with patch.object(t,'_turn',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):self.run_trial(a)
        r=self.run_trial(a);self.assertEqual(r['state'],'in_flight');self.assertEqual(self.wire.turns,0)
        self.assertEqual(self.factories,2)

    def test_process_death_after_wire_leaves_unknown_marker_and_never_resends(self):
        a=self.prepare();self.wire.fail='death'
        with self.assertRaises(KeyboardInterrupt):self.run_trial(a)
        r=self.run_trial(a);self.assertEqual(r['state'],'in_flight')
        self.assertEqual(r['model_turn_attempts'],1);self.assertEqual(self.wire.turns,1)
        self.assertIsNone(r['estimated_standard_credits'])
        self.assertEqual(json.loads((t.STATE/'turns/01.json').read_text())['state'],'delivery_unknown')

    def test_main_guide_or_code_drift_blocks_before_reserving(self):
        a=self.prepare()
        for target,value in [('_head','b'*40),('_code',{})]:
            with patch.object(t,target,return_value=value),self.assertRaises(ValueError):self.run_trial(a)
        self.guide.write_text('changed')
        with self.assertRaises(ValueError):self.run_trial(a)
        self.assertFalse((t.STATE/'attempt.json').exists());self.assertEqual(self.factories,1)

    def test_runtime_socket_or_permission_drift_stops_before_paid_turn(self):
        a=self.prepare();self.wire.permissions={'type':'dangerFullAccess'}
        r=self.run_trial(a);self.assertEqual(r['state'],'attention');self.assertEqual(self.wire.turns,0)
        self.assertEqual(r['model_turn_attempts'],0)

    def test_reference_drift_or_excess_stops_before_thread(self):
        a=self.prepare();self.count.return_value={'tokens':1000000,'tokenizer':{'fixture':True}}
        r=self.run_trial(a);self.assertEqual(r['state'],'attention');self.assertEqual(self.wire.threads,0)

    def test_tokenizer_identity_change_stops_before_thread(self):
        a=self.prepare();self.count.return_value={'tokens':100,'tokenizer':{'fixture':'changed'}}
        r=self.run_trial(a);self.assertEqual(r['state'],'attention');self.assertEqual(self.wire.threads,0)

    def test_source_changes_between_thread_and_turn_prevent_send(self):
        a=self.prepare();original=self.wire.request
        def request(method,params):
            result=original(method,params)
            if method=='thread/start':self.guide.write_text('changed')
            return result
        self.wire.request=request;r=self.run_trial(a)
        self.assertEqual(r['state'],'attention');self.assertEqual(self.wire.turns,0)

    def test_second_phase_failure_keeps_known_first_cost_and_never_repeats_it(self):
        a=self.prepare();self.count.side_effect=[{'tokens':100,'tokenizer':{'fixture':True}},OSError('SECRET')]
        r=self.run_trial(a);self.assertEqual(r['state'],'attention');self.assertEqual(self.wire.turns,1)
        self.assertEqual(r['estimated_standard_credits'],.02)
        self.assertEqual(self.run_trial(a),r);self.assertEqual(self.factories,2)

    def test_guard_refuses_resume_other_rpc_or_second_thread_and_foreign_turn(self):
        from app.recovery_guide_anchor_transport import StandardTurn
        request=p.inspection_request(Catalogue(self.snap),tuple(c.CASES))
        guard=StandardTurn(self.wire,context=self.root/'context',request=request,
            instructions=c.INSTRUCTIONS,before_send=lambda _:None)
        for method in ('thread/resume','thread/read','thread/archive','config/write','command/exec'):
            with self.subTest(method=method),self.assertRaises(ValueError):guard.request(method,{})
        guard.start_attempted=True
        with self.assertRaises(ValueError):guard.request('thread/start',{})
        guard.thread_id='own'
        with self.assertRaises(ValueError):guard.request('turn/start',{'threadId':'foreign'})
        guard.attempted=True
        with self.assertRaises(ValueError):guard.request('turn/start',{'threadId':'own'})

    def test_socket_replacement_prevents_thread_start(self):
        a=self.prepare();other=socket.socket(socket.AF_UNIX);self.addCleanup(other.close)
        path=self.root/'other.sock';other.bind(str(path));self.wire.socket_path=path
        r=self.run_trial(a);self.assertEqual(r['state'],'attention');self.assertEqual(self.wire.threads,0)

    def test_unknown_usage_stops_after_one_and_preserves_raw(self):
        self.wire.usage=None;r=self.run_trial()
        self.assertEqual(r['state'],'attention');self.assertIsNone(r['estimated_standard_credits'])
        self.assertEqual(self.wire.turns,1)
        self.assertTrue(json.loads((t.STATE/'turns/01.json').read_text())['receipt']['delivered'])

    def test_over_acceptance_cost_is_preserved(self):
        self.wire.usage.update(inputTokens=20000,totalTokens=20060)
        r=self.run_trial();self.assertEqual(r['state'],'attention')
        self.assertGreater(r['estimated_standard_credits'],1);self.assertEqual(self.wire.turns,1)

    def test_tool_event_stops_even_with_valid_structured_answer(self):
        self.wire.extra_items=[{'type':'commandExecution','id':'tool'}]
        r=self.run_trial();self.assertEqual(r['state'],'attention');self.assertEqual(self.wire.turns,1)

    def test_bad_case_coverage_or_model_quote_stops_before_synthesis(self):
        self.wire.bad='header';r=self.run_trial();self.assertEqual(r['state'],'attention')
        self.assertEqual(self.wire.turns,1);self.assertEqual(r['estimated_standard_credits'],.02)

    def test_small_scope_stricter_than_generic_inspection(self):
        cat=Catalogue(self.snap);req=p.inspection_request(cat,tuple(c.CASES))
        for mode in ('missing','long','extra','wrong'):
            data=json.loads(c.fixture(cat,req))
            if mode=='missing':data['findings'].pop()
            elif mode=='long':data['findings'][0]['text']='x'*1501
            elif mode=='extra':data['quote']='invented'
            else:data['covered'][cat.document_ids[0]]='l1'
            with self.subTest(mode=mode),self.assertRaises(ValueError):t._inspect(cat,req,canonical_json(data))

    def test_synthesis_cannot_change_original_or_promote_fixture_to_live_fact(self):
        self.wire.bad='original';r=self.run_trial()
        self.assertEqual(r['state'],'attention');self.assertEqual(self.wire.turns,2)
        self.assertEqual(r['estimated_standard_credits'],.04)

    def test_new_card_requires_explicit_pre_attempt_refresh_and_cannot_reset_job(self):
        a=self.prepare();b=self.prepare(refresh=True)
        self.assertNotEqual(a['approval_digest'],b['approval_digest'])
        self.assertTrue((t.STATE/'revisions'/(b['approval_digest']+'.json')).exists())
        r=self.run_trial(b);self.assertTrue(r['accepted'])
        with self.assertRaises(ValueError):self.prepare(refresh=True)
        with self.assertRaises(ValueError):self.run_trial(a)

    def test_symlinked_artifact_is_refused(self):
        self.prepare();(t.STATE/'attempt.json').symlink_to(self.root/'elsewhere')
        with self.assertRaises(ValueError):self.run_trial()

    def test_marker_failure_sends_no_turn(self):
        a=self.prepare();original=t.atomic_write_json
        def save(path,value,**kwargs):
            if value.get('state')=='delivery_unknown':raise OSError('SECRET_DISK')
            return original(path,value,**kwargs)
        with patch.object(t,'atomic_write_json',side_effect=save):r=self.run_trial(a)
        self.assertEqual(r['state'],'attention');self.assertEqual(self.wire.turns,0)
        self.assertEqual(self.run_trial(a),r)


class Pricing(unittest.TestCase):
    def test_reference_allowance_counts_whole_input_schema_instructions_and_synthesis(self):
        module=SimpleNamespace(get_encoding=lambda _:SimpleNamespace(encode_ordinary=lambda x:list(x.encode())))
        with patch.object(c,'tokenizer_identity',return_value={'fixture':True}):r=c.measure(snapshot(),module)
        self.assertEqual(r['planned_calls'],2);self.assertFalse(r['hard_billing_or_output_cap'])
        self.assertGreater(r['input_acceptance_tokens']['synthesize'],r['reference_input_tokens']['synthesize_fixture'])
        self.assertGreater(r['planning_standard_credits_no_cache'],sum(c.OUTPUT_LIMITS.values())*250/1e6)
        self.assertTrue(r['synthesis_request_is_dynamic']);self.assertFalse(r['margin_proven_for_sol'])

    def test_missing_or_ambiguous_regression_source_is_explicitly_unsupported(self):
        s=snapshot();cat=Catalogue(replace(s,sources=(replace(s.sources[0],text='changed',sha256=digest('changed')),s.sources[1])))
        with self.assertRaisesRegex(ValueError,'case_source_changed'):c.expected_pairs(cat)


if __name__=='__main__':unittest.main()
