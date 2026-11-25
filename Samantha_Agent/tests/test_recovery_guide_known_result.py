from pathlib import Path
from tempfile import TemporaryDirectory
from dataclasses import asdict,replace
from types import SimpleNamespace
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
import json,unittest,copy
from app import recovery_guide_known_result as k,recovery_guide_maintainer as m,recovery_guide_inspection as w
from app.recovery_guide_sources import canonical_json,digest
from app.release_usage import estimate_standard_credits
from app.file_persistence import atomic_write_json
from tests.test_recovery_guide import snapshot,consolidated_answer,USAGE

class Wire(unittest.TestCase):
    def setUp(self):
        s=snapshot();self.payload={'original':asdict(s.original),'sources':[asdict(x) for x in s.sources]}
    def test_compact_indices_restore_full_exact_paths_without_truncating_input(self):
        value=w.wire(self.payload);self.assertEqual(value['sources'][0]['text'],self.payload['sources'][0]['text']);self.assertNotIn('i',self.payload['sources'][0])
        answer={'covered':[{'i':i,'q':row['text']} for i,row in enumerate(value['sources'])],'notes':'material finding'}
        normalized=w.normalize(answer,self.payload);self.assertEqual([r['source'] for r in normalized['covered']],[r['path'] for r in self.payload['sources']])
    def test_exact_integral_json_number_is_accepted_without_rounding(self):
        result=w.normalize({'covered':[{'i':float(i),'q':row['text']} for i,row in enumerate(self.payload['sources'])],'notes':''},self.payload)
        self.assertEqual(len(result['covered']),2)
        with self.assertRaises(ValueError):w.normalize({'covered':[{'i':0.5,'q':'Codex'}],'notes':''},self.payload)
    def test_wrong_duplicate_missing_indices_and_invented_quotes_rejected(self):
        for covered in ([{'i':-1,'q':'x'}],[{'i':False,'q':'x'}],[{'i':0,'q':'invented'}],[{'i':0,'q':'Codex'},{'i':0,'q':'Codex'}],[]):
            with self.assertRaises(ValueError):w.normalize({'covered':covered,'notes':''},self.payload)
    def test_only_exact_redundant_original_is_removed(self):
        rows=[{'source':r['path'],'quote':r['text']} for r in self.payload['sources']];original={'source':self.payload['original']['path'],'quote':self.payload['original']['text']}
        result=w.normalize_known({'covered':[original,*rows],'notes':'keep all notes'},self.payload)
        self.assertEqual(result,{'covered':rows,'notes':'keep all notes'})
        for invalid in ([original,original,*rows],[original,*rows[:-1]],[{'source':'foreign','quote':'x'},*rows]):
            with self.assertRaises(ValueError):w.normalize_known({'covered':invalid,'notes':''},self.payload)

class Continuation(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.snap=snapshot();self.calls=[]
        payload={'original':asdict(self.snap.original),'sources':[asdict(self.snap.sources[0])]}
        self.usage={'input_tokens':100,'cached_input_tokens':0,'output_tokens':120,'reasoning_output_tokens':0,'total_tokens':220}
        self.known={'payload':payload,'response':{'answer':{'covered':[{'source':self.snap.sources[0].path,'quote':self.snap.sources[0].text}],'notes':'all known notes'},'usage':self.usage},'credits':estimate_standard_credits(m.MODEL,self.usage),'maximum_known_credits':1,'delivery_confirmed':True,'raw_sha256':'a'*64}
        self.limits=m.Limits(30000,1000,8,50,100,60,inspection_output_tokens=100)
    def call(self,payload,kind):
        self.calls.append(kind)
        if kind=='inspect':
            self.assertEqual([r['path'] for r in payload['sources']],[self.snap.sources[1].path])
            answer={'covered':[{'source':r['path'],'quote':r['text']} for r in payload['sources']],'notes':'new finding'}
        else:
            self.assertIn('all known notes',canonical_json(payload));answer=consolidated_answer(payload)
        return {'answer':answer,'usage':USAGE}
    def run_known(self,known=None):
        return m.run(self.snap,state_dir=self.root/'controller',now=datetime(2026,11,8,10,tzinfo=ZoneInfo('Europe/Prague')),limits=self.limits,count_tokens=len,call=self.call,approved_snapshot=self.snap.sha256,assert_sources=lambda:True,confirmed=True,known_first=self.known if known is None else known)
    def test_known_measured_over_reserve_is_replayed_locally_with_exact_cost(self):
        result=self.run_known();self.assertEqual(result['state'],'review');self.assertEqual(result['coverage'],2)
        self.assertEqual(self.calls,['inspect','synthesize']);self.assertEqual(result['model_calls'],3);self.assertEqual(result['turns'][0]['origin'],'existing_completed_receipt')
        self.assertAlmostEqual(result['credits'],self.known['credits']+2*estimate_standard_credits(m.MODEL,USAGE));self.assertEqual(self.run_known()['state'],'review');self.assertEqual(len(self.calls),2)
    def test_unproven_wrong_prefix_or_unacceptable_known_cost_never_starts_model(self):
        for field,value in [('delivery_confirmed',False),('maximum_known_credits',0.00001)]:
            known=copy.deepcopy(self.known);known[field]=value
            with self.assertRaises(ValueError):self.run_known(known)
        known=copy.deepcopy(self.known);known['payload']['sources'][0]['text']='changed'
        with self.assertRaises(ValueError):self.run_known(known)
        self.assertEqual(self.calls,[])
    def test_unknown_future_delivery_is_never_retried_on_replay(self):
        self.call=lambda *args:(_ for _ in ()).throw(TimeoutError('unknown future delivery'))
        first=self.run_known();self.assertEqual(first['state'],'attention');self.assertEqual(first['completed_calls'],1)
        second=self.run_known();self.assertEqual(second['model_calls'],2);self.assertTrue(second['replayed_receipt'])

class OriginalProof(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.rid='recovery-2026-W47';self.folder=self.root/'analysis'/self.rid
        for name in ('raw','transport','controller'):(self.folder/name).mkdir(parents=True)
        (self.root/'schedule').mkdir();self.snap=snapshot();payload={'original':asdict(self.snap.original),'sources':[asdict(self.snap.sources[0])]};self.payload=payload
        self.usage={'input_tokens':100,'cached_input_tokens':0,'output_tokens':120,'reasoning_output_tokens':0,'total_tokens':220};self.cost=estimate_standard_credits(m.MODEL,self.usage)
        self.answer={'covered':[{'source':self.snap.original.path,'quote':self.snap.original.text},{'source':self.snap.sources[0].path,'quote':self.snap.sources[0].text}],'notes':'keep notes'}
        self.job={'state':'attention','request_id':self.rid,'slot':'2026-W47','identity_sha256':'b'*64,'snapshot_sha256':self.snap.sha256}
        atomic_write_json(self.root/'schedule'/(self.rid+'.json'),self.job)
        atomic_write_json(self.folder/'packet.json',{'snapshot':asdict(self.snap),'job_identity':'b'*64})
        atomic_write_json(self.folder/'controller/2026-W47.json',{'state':'attention','model_calls':1,'completed_calls':1,'coverage':0,'credits':self.cost,'turns':[{'phase':'inspect','state':'received','payload_sha256':digest(canonical_json(payload))}]})
        atomic_write_json(self.folder/'raw/001.json',{'state':'received_unreviewed','phase':'inspect','response':{'answer':self.answer,'usage':self.usage}})
        self.receipt={'delivered':True,'status':'completed','turn_started_confirmed':True,'user_item_count':1,'turn_id':'t','thread_id':'thread','client_message_id':self.rid+'-1','thread_token_usage':self.usage,'answer':json.dumps(self.answer),'duration_ms':1000}
        self.transport={'phase':'inspect','state':'received_unreviewed','unexpected_item_types':[],'receipt':self.receipt};self.save_transport()
        self.cfg=SimpleNamespace(root=self.root,payload={'limits':{'input_tokens':30000,'output_tokens':1000,'inspection_output_tokens':100,'seconds':60}})
    def save_transport(self):atomic_write_json(self.folder/'transport/001.json',self.transport)
    def known(self):return k._known(self.cfg,self.rid,len)
    def test_proven_original_is_preserved_and_normalized_without_extra_model_call(self):
        before=(self.folder/'raw/001.json').read_bytes();_,_,_,proof=self.known();self.assertEqual(len(proof['response']['answer']['covered']),1);self.assertEqual(proof['credits'],self.cost);self.assertEqual((self.folder/'raw/001.json').read_bytes(),before)
    def test_failed_unknown_delivery_or_missing_telemetry_is_refused(self):
        for field,value in [('delivered',False),('status','interrupted'),('turn_started_confirmed',False),('thread_id',None),('duration_ms',-1),('client_message_id','foreign')]:
            original=self.receipt[field];self.receipt[field]=value;self.save_transport()
            with self.assertRaises(ValueError):self.known()
            self.receipt[field]=original
        self.save_transport();self.receipt['thread_token_usage']=None;self.save_transport()
        with self.assertRaises(ValueError):self.known()
    def test_other_paid_turn_or_changed_payload_refused(self):
        atomic_write_json(self.folder/'raw/002.json',{'anything':'preserve'})
        with self.assertRaises(ValueError):self.known()
    def test_symlink_artifact_is_refused(self):
        old=self.folder/'raw/001.json';other=self.folder/'raw/saved.json';old.rename(other);old.symlink_to(other)
        with self.assertRaises(ValueError):self.known()

class PublicationContinuation(unittest.TestCase):
    def setUp(self):
        from tests.test_recovery_guide_runtime import ProductionIntegration
        from tests import test_recovery_guide_quality as facts
        from app.recovery_guide_runtime import RecoveryRuntime
        from app.recovery_guide_scheduler import SchedulerPolicy,WeeklyScheduler,ANALYSIS_READY
        from app.recovery_guide_publication import PublicationStore
        self.h=ProductionIntegration(methodName='runTest');self.h.setUp();self.addCleanup(self.h.doCleanups);h=self.h
        h.configuration.value['limits']['inspection_output_tokens']=10;h.cfg=h.configuration.save();h.policy=SchedulerPolicy(**h.cfg.payload['schedule'])
        h.scheduler=WeeklyScheduler(h.cfg.root/'schedule',sandbox_root=h.cfg.root,policy=h.policy,mode='production',activation=h.cfg)
        h.store=PublicationStore(h.cfg.root/'publication',sandbox_root=h.cfg.root,destinations=h.cfg.destinations,mode='production',activation=h.cfg)
        h.runtime=RecoveryRuntime(scheduler=h.scheduler,publication=h.store,limits=m.Limits(**h.cfg.payload['limits']),bootstrap=h.bootstrap,bootstrap_sha256=digest(h.bootstrap.read_bytes()),snapshot_provider=h.snapshot,count_tokens=len,call_factory=h.factory,readiness=lambda:{x:True for x in ANALYSIS_READY},assert_snapshot=lambda snap,path:True,cloud_audit=lambda path:__import__('tests.test_recovery_guide',fromlist=['CLOUD']).CLOUD if h.cloud else {**__import__('tests.test_recovery_guide',fromlist=['CLOUD']).CLOUD,'uploaded':False},assert_activation=h.cfg.guard)
        h.runtime.automatic_profile=lambda snap,day:(facts.dossier(facts.context(snap)),replace(facts.context(snap),checked_on=day))
        job=h.runtime.tick(h.now);self.assertEqual(job['state'],'attention');self.rid=job['request_id'];self.original=h.cfg.root/'analysis'/self.rid
        packet=json.loads((self.original/'packet.json').read_text());snap=k.hydrate(packet['snapshot']);raw=json.loads((self.original/'raw/001.json').read_text());self.oldraw=(self.original/'raw/001.json').read_bytes();self.oldresult=(self.original/'result.json').read_bytes();self.oldjob=(h.cfg.root/'schedule'/(self.rid+'.json')).read_bytes()
        known={'payload':{'original':asdict(snap.original),'sources':[asdict(x) for x in snap.sources]},'response':raw['response'],'credits':estimate_standard_credits(m.MODEL,USAGE),'maximum_known_credits':5,'delivery_confirmed':True,'raw_sha256':digest(self.oldraw)}
        self.recovery=h.cfg.root/'known-result'/self.rid;self.controller=self.recovery/self.rid/'controller'
        result=m.run(snap,state_dir=self.controller,now=h.now,limits=m.Limits(**h.cfg.payload['limits']),count_tokens=len,call=h.call,approved_snapshot=snap.sha256,assert_sources=lambda:True,confirmed=True,known_first=known)
        self.assertEqual(result['state'],'review');atomic_write_json(self.recovery/self.rid/'result.json',result)
        self.head='f'*40;self.impl={'code':'frozen'}
        plan={'implementation':self.impl,'activation_sha256':h.cfg.sha256,'source_head':self.head,'job_sha256':digest(self.oldjob),'original_result_sha256':digest(self.oldresult)};binding=digest(canonical_json(plan));atomic_write_json(self.recovery/'plan.json',{'plan':plan,'digest':binding});atomic_write_json(self.recovery/'attempt.json',{'state':'review','plan_digest':binding})
        self.enterContext(patch.object(k,'owned_configuration',return_value=(h.cfg,'agent')))
        self.enterContext(patch.object(k,'build',return_value=(h.runtime,SimpleNamespace(close=lambda:None))))
        self.enterContext(patch.object(k,'implementation',return_value=self.impl))
        self.enterContext(patch.object(k.subprocess,'check_output',return_value=self.head+'\n'))
        accept=h.store.accept;self.enterContext(patch.object(h.store,'accept',side_effect=lambda *a,**kw:accept(*a,now=h.now,**kw)))
        reviewed=k.prepare_publication(request_id=self.rid);self.binding=reviewed['binding_sha256'];self.modelcalls=len(h.calls)
    def publish(self):return k.publish(request_id=self.rid,confirmed_binding=self.binding,confirmed=True)
    def test_full_same_job_delivery_preserves_originals_and_never_calls_model(self):
        result=self.publish();self.assertEqual(result['state'],'completed');self.assertEqual(len(self.h.calls),self.modelcalls)
        self.assertEqual((self.original/'raw/001.json').read_bytes(),self.oldraw);self.assertEqual((self.recovery/'original-result.json').read_bytes(),self.oldresult)
        self.assertEqual((self.recovery/'original-job.json').read_bytes(),self.oldjob)
        self.assertEqual(self.h.targets[0].read_bytes(),self.h.targets[1].read_bytes());self.assertEqual(len(self.h.scheduler._jobs()),1)
        self.assertEqual(self.publish()['state'],'completed');self.assertEqual(len(self.h.calls),self.modelcalls)
    def test_lost_post_reconcile_receipt_resumes_only_delivery(self):
        original=self.h.scheduler.reconcile_analysis;calls=[]
        def lost(*args,**kwargs):
            calls.append(1);original(*args,**kwargs);raise OSError('receipt lost after attachment')
        with patch.object(self.h.scheduler,'reconcile_analysis',side_effect=lost):
            with self.assertRaises(OSError):self.publish()
        self.assertEqual(self.publish()['state'],'completed');self.assertEqual(calls,[1]);self.assertEqual(len(self.h.calls),self.modelcalls)
    def test_pending_cloud_reconciles_same_job_after_calendar_moves(self):
        self.h.cloud=False;self.assertEqual(self.publish()['state'],'pending_icloud')
        self.h.cloud=True;self.assertEqual(self.publish()['state'],'completed');self.assertEqual(len(self.h.calls),self.modelcalls);self.assertEqual(len(self.h.scheduler._jobs()),1)
    def test_changed_binding_and_foreign_receipt_do_not_publish(self):
        with self.assertRaises(ValueError):k.publish(request_id=self.rid,confirmed_binding='bad',confirmed=True)
        (self.original/'result.json').write_text('{}')
        with self.assertRaises(ValueError):self.publish()
        self.assertFalse(self.h.targets[0].exists());self.assertEqual(len(self.h.calls),self.modelcalls)

class OwnedCodeUpdate(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.source=self.root/'source';self.active=self.root/'active';self.state=self.active/'state';(self.state/'schedule').mkdir(parents=True)
        self.rid='recovery-2026-W47';self.head='a'*40;atomic_write_json(self.state/'schedule'/(self.rid+'.json'),{'state':'completed'})
        self.names=('app/recovery_guide_sources.py','app/recovery_guide_inspection.py','app/recovery_guide_maintainer.py','app/recovery_guide_runtime_live.py','app/recovery_guide_anchor_transport.py','tests/test_recovery_guide_runtime.py')
        for name in self.names:
            s=self.source/name;s.parent.mkdir(parents=True,exist_ok=True);s.write_text('reviewed '+name)
            if 'inspection.py' not in name:
                t=self.active/name;t.parent.mkdir(parents=True,exist_ok=True);t.write_text('original '+name)
        self.foreign=self.active/'unrelated.txt';self.foreign.write_text('foreign work must remain')
        self.cfg=SimpleNamespace(root=self.state,project=self.active);self.dirty=set()
        self.enterContext(patch.object(k,'ROOT',self.source));self.enterContext(patch.object(k,'owned_configuration',return_value=(self.cfg,'agent')))
        def git(args,**kwargs):
            if args[1]=='rev-parse':return self.head+'\n'
            if args[1]=='status':return ' M '+args[-1] if args[-1] in self.dirty else ''
            if args[1]=='show':return (self.source/args[-1].split(':Samantha_Agent/')[1]).read_bytes()
            raise AssertionError(args)
        self.enterContext(patch.object(k.subprocess,'check_output',side_effect=git))
    def apply(self,**extra):
        options={'request_id':self.rid,'expected_main_head':self.head,'confirmed':True};options.update(extra);return k.apply_owned_code(**options)
    def test_only_whitelist_changes_and_exact_before_images_survive_replay(self):
        result=self.apply();self.assertEqual(result['state'],'completed');self.assertEqual(self.foreign.read_text(),'foreign work must remain')
        for row in result['files']:
            self.assertEqual((self.active/row['path']).read_bytes(),(self.source/row['path']).read_bytes())
            if row['before_sha256'] is not None:self.assertEqual(digest((self.state/'owned-code'/self.head/'before'/row['path']).read_bytes()),row['before_sha256'])
        self.assertEqual(self.apply(),result)
    def test_dirty_owned_destination_or_missing_confirmation_never_overwritten(self):
        with self.assertRaises(ValueError):self.apply(confirmed=False)
        name=self.names[0];self.dirty.add(name)
        with self.assertRaises(ValueError):self.apply()
        self.assertEqual((self.active/name).read_text(),'original '+name)
    def test_partial_known_update_resumes_without_overwriting_foreign_changes(self):
        from app.file_persistence import atomic_write_text
        count=[]
        def fail(path,value,*args,**kwargs):
            if Path(path)==self.active/self.names[2]:raise OSError('copy interrupted')
            count.append(str(path));return atomic_write_text(path,value,*args,**kwargs)
        with patch('app.file_persistence.atomic_write_text',side_effect=fail):
            with self.assertRaises(OSError):self.apply()
        self.dirty.update(self.names[:2]);self.assertEqual(self.apply()['state'],'completed');self.assertEqual(self.foreign.read_text(),'foreign work must remain')
    def test_active_model_job_blocks_code_update(self):
        atomic_write_json(self.state/'schedule/recovery-2026-W46.json',{'state':'analysis_in_flight'})
        with self.assertRaises(ValueError):self.apply()
        self.assertEqual((self.active/self.names[0]).read_text(),'original '+self.names[0])

class SourceAlias(unittest.TestCase):
    def test_only_code_head_change_with_identical_documents_is_allowed(self):
        snap=snapshot();cfg=SimpleNamespace(guard=lambda:None);runtime=SimpleNamespace(snapshot_provider=lambda path:replace(snap,head='b'*40))
        with patch.object(k.subprocess,'check_output',return_value='b'*40+'\n'):
            self.assertTrue(k._current(runtime,snap,Path('/guide'),'b'*40,cfg))
            changed=replace(snap.sources[0],text='changed',sha256=digest('changed'));runtime.snapshot_provider=lambda path:replace(snap,head='b'*40,sources=(changed,*snap.sources[1:]))
            self.assertFalse(k._current(runtime,snap,Path('/guide'),'b'*40,cfg))
            self.assertFalse(k._current(runtime,snap,Path('/guide'),'c'*40,cfg))

class AttemptReplay(unittest.TestCase):
    def test_unknown_or_completed_continuation_marker_never_starts_another_turn(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();rid='recovery-2026-W47';(root/'schedule').mkdir();recovery=root/'known-result'/rid;recovery.mkdir(parents=True)
            cfg=SimpleNamespace(root=root);plan={};binding=digest(canonical_json(plan));atomic_write_json(recovery/'plan.json',{'plan':plan,'digest':binding})
            for state in ('reserved','attention','review','completed'):
                marker={'state':state,'original':'preserve'};atomic_write_json(recovery/'attempt.json',marker)
                with patch.object(k,'owned_configuration',return_value=(cfg,'agent')),patch.object(k,'build',return_value=(object(),SimpleNamespace(close=lambda:None))),patch.object(k,'_known',side_effect=AssertionError('must not reenter model setup')),patch.object(k,'live_calls',side_effect=AssertionError('no provider retry')):
                    self.assertEqual(k.run(request_id=rid,approved_digest=binding,confirmed=True),marker)
                    with self.assertRaises(ValueError):k.run(request_id=rid,approved_digest='bad',confirmed=True)


class ReceivedPrefix(OriginalProof):
    def setUp(self):
        super().setUp();self.base=self.root/'known-result'/self.rid;self.directory=self.base/self.rid;self.target=self.base/'received-prefix'
        (self.directory/'controller').mkdir(parents=True);(self.directory/'transport').mkdir();self.target.mkdir()
        payload={'original':asdict(self.snap.original),'sources':[asdict(self.snap.sources[1])]}
        self.second={'covered':[{'i':0,'q':'provider paraphrase'}],'notes':'preserve complete notes'}
        usage={**self.usage,'output_tokens':50,'total_tokens':150}
        receipt={**self.receipt,'client_message_id':self.rid+'-2','answer':json.dumps(self.second),'thread_token_usage':usage}
        self.path=self.directory/'transport/002.json';atomic_write_json(self.path,{'state':'received_unreviewed','phase':'inspect','unexpected_item_types':[],'receipt':receipt})
        plan={'inspection_source_counts':[1,1],'limits':self.cfg.payload['limits'],'snapshot_sha256':self.snap.sha256,'known_raw_sha256':digest((self.folder/'raw/001.json').read_bytes())}
        binding=digest(canonical_json(plan));atomic_write_json(self.base/'plan.json',{'plan':plan,'digest':binding});atomic_write_json(self.base/'attempt.json',{'state':'attention','plan_digest':binding})
        atomic_write_json(self.directory/'controller/2026-W47.json',{'state':'attention','snapshot_sha256':self.snap.sha256,'credits':self.cost,'model_calls':2,'completed_calls':1,'coverage':1,'turns':[{}, {'state':'in_flight','payload_sha256':digest(canonical_json(payload))}]})
        self.answer={'covered':[{'source':self.snap.sources[1].path,'quote':self.snap.sources[1].text}],'notes':self.second['notes']};self.save_review()
    def save_review(self):atomic_write_json(self.target/'reviewed-second.json',{'transport_sha256':digest(self.path.read_bytes()),'answer':self.answer})
    def prefix(self):return k._prefix(self.cfg,self.rid,len,'received')
    def test_complete_second_receipt_reuses_exact_usage_and_records_editorial_quotes(self):
        before=self.path.read_bytes();proofs=self.prefix()[3];self.assertEqual(len(proofs),2);self.assertEqual(proofs[1]['response']['answer'],self.answer);self.assertEqual(self.path.read_bytes(),before)
    def test_unknown_extra_transport_or_changed_notes_refuse_all_new_model_work(self):
        self.answer['notes']='changed finding';self.save_review()
        with self.assertRaises(ValueError):self.prefix()
        self.answer['notes']=self.second['notes'];self.save_review();atomic_write_json(self.directory/'transport/003.json',{'state':'delivery_unknown'})
        with self.assertRaises(ValueError):self.prefix()
    def test_failed_second_receipt_cannot_be_editorially_accepted(self):
        value=json.loads(self.path.read_text());value['receipt']['delivered']=False;atomic_write_json(self.path,value);self.save_review()
        with self.assertRaises(ValueError):self.prefix()

class MultipleKnown(Continuation):
    def test_two_known_prefix_turns_preserve_separate_costs_and_no_inspection_rpc(self):
        second=copy.deepcopy(self.known);second['payload']['sources']=[asdict(self.snap.sources[1])];second['response']['answer']['covered']=[{'source':self.snap.sources[1].path,'quote':self.snap.sources[1].text}]
        result=self.run_known([self.known,second]);self.assertEqual(result['state'],'review');self.assertEqual(self.calls,['synthesize']);self.assertEqual(result['model_calls'],3)
        self.assertAlmostEqual(result['credits'],2*self.known['credits']+estimate_standard_credits(m.MODEL,USAGE))
        self.assertEqual(result['turns'][1]['origin'],'existing_completed_receipt')

class BoundSchema(Wire):
    def test_every_index_is_bound_to_one_exact_provided_quote(self):
        schema=w.schema(self.payload);choices=schema['properties']['covered']['items']['anyOf']
        for i,choice in enumerate(choices):
            self.assertEqual(choice['properties']['i']['enum'],[i]);quote=choice['properties']['q']['enum'][0];self.assertIn(quote,self.payload['sources'][i]['text']);self.assertEqual(w.wire(self.payload)['sources'][i]['citation'],quote)


class SafeLiterals(unittest.TestCase):
    def test_exact_anchors_avoid_backend_quote_and_newline_rejection(self):
        for text in ['# Project Registry\n\nRegistr projektu a dat', '"Quoted title"\nnext line', '\n  \n# One two three four five six seven', '"\r\n  only exact source text  "']:
            value=w.anchor(text);self.assertTrue(value);self.assertIn(value,text);self.assertFalse(any(c in value for c in '\r\n"'))
        with self.assertRaises(ValueError):w.anchor('"\n\r"')
