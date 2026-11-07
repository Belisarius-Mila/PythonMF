from dataclasses import asdict
from datetime import datetime
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app import recovery_guide_receipt_recovery as rr
from app import recovery_guide_full_pilot as f
from app import recovery_guide_maintainer as m
from app.recovery_guide_sources import canonical_json, digest
from app.release_usage import estimate_standard_credits
from tests.test_recovery_guide import snapshot, answer, USAGE


class Client:
    def __enter__(self):return self
    def __exit__(self,*_):pass


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.snap=snapshot()
        self.original=self.root/'original.txt';self.original.write_text(self.snap.original.text)
        self.enterContext(patch.object(f,'STATE',self.root))
        self.enterContext(patch.object(f,'ORIGINAL',self.original))
        self.head=self.enterContext(patch.object(f,'_head',return_value=self.snap.head))
        self.enterContext(patch.object(f,'_code',return_value={'code':'same'}))
        self.enterContext(patch.object(f,'_calibration',return_value={'sha256':'calib'}))
        self.enterContext(patch.object(f.calibration,'_protocol',return_value={'version':'test'}))
        self.enterContext(patch.object(f.calibration,'_runtime',return_value={'socket':'same'}))
        self.factory=self.enterContext(patch.object(f.calibration,'_client',side_effect=Client))
        self.enterContext(patch.object(f,'_tokenizer',side_effect=lambda script,data,**kw:len(data)))
        self.payload={'original':asdict(self.snap.original),'sources':[asdict(s) for s in self.snap.sources]}
        self.value={'covered':[{'source':self.snap.original.path,'quote':self.snap.original.text}]+[
            {'source':s.path,'quote':s.text} for s in self.snap.sources],'notes':'Dokumentace, nikoli živý audit.'}
        self.packet={'request_id':f.REQUEST,'project_only':False,'snapshot':asdict(self.snap),
            'implementation':{'code':'same'},'calibration':{'sha256':'calib'},'protocol':{'version':'test'},
            'runtime':{'socket':'same'},'measurements':{'reference_counts':{},'planned_calls':2,
                'shards':[{'payload_sha256':digest(canonical_json(self.payload)),
                    'source_paths':[s.path for s in self.snap.sources]}],
                'limits':dict(input_tokens=100000,output_tokens=1000,inspection_output_tokens=1000,
                              max_calls=8,run_credits=50,month_credits=50,seconds=60)}}
        self.parent=digest(canonical_json(self.packet))
        self.write('packet.json',{'packet':self.packet,'approval_digest':self.parent})
        requested='2026-11-07T18:00:00+00:00';self.slot=m.weekly_slot(datetime.fromisoformat(requested))
        self.write('attempt.json',{'state':'attention','approval_digest':self.parent,'slot':self.slot})
        self.cost=estimate_standard_credits(m.MODEL,USAGE)
        self.status={'state':'attention','slot':self.slot,'model_calls':1,'completed_calls':1,
                     'coverage':0,'credits':self.cost,'turns':[{'state':'received'}]}
        self.write('controller/'+self.slot+'.json',self.status)
        self.receipt={'delivered':True,'status':'completed','turn_started_confirmed':True,
            'user_item_count':1,'client_message_id':f.REQUEST+'-1','thread_id':'thread-1','turn_id':'turn-1',
            'thread_token_usage':USAGE,'duration_ms':10,'requested_at':requested,'answer':json.dumps(self.value)}
        self.raw={'state':'completed','phase':'inspect','unexpected_item_types':[],
                  'payload_sha256':digest(canonical_json(self.payload)),'receipt':self.receipt}
        self.write('turns/01.json',self.raw)
        self.sdk=[]
        outer=self
        class Reviewer:
            def __init__(self,*_):self.calls=0
            def __call__(self,payload,kind):
                outer.assertEqual(self.calls,1)  # Phase 1 must NEVER reach SDK again.
                outer.assertEqual(kind,'synthesize')
                outer.sdk.append(kind);self.calls+=1
                return {'answer':answer(),'usage':USAGE}
        self.enterContext(patch.object(f,'Reviewer',Reviewer))

    def write(self,name,value):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(value))

    def resume(self,card=None):
        card=card or rr.prepare()
        return rr.resume(approved_digest=card['approval_digest'])

    def test_prepare_is_nonpaid_immutable_and_keeps_old_receipt_and_budget(self):
        before=(self.root/'turns/01.json').read_bytes()
        card=rr.prepare()
        self.assertEqual(card,rr.prepare())
        self.assertEqual(card['known_standard_credits'],self.cost)
        self.assertEqual(card['remaining_sdk_turns'],1)
        self.assertEqual(card['accepted_existing_sources'],2)
        self.assertEqual(card['total_credit_limit'],50)
        self.assertEqual(before,(self.root/'turns/01.json').read_bytes())
        self.assertFalse(self.sdk);self.assertEqual(self.factory.call_count,0)

    def test_resume_reuses_first_receipt_and_only_calls_remaining_step(self):
        before=(self.root/'turns/01.json').read_bytes();old=(self.root/'attempt.json').read_bytes()
        card=rr.prepare();r=self.resume(card)
        self.assertEqual(r['state'],'review')
        self.assertEqual(r['coverage'],2)
        self.assertEqual(r['model_calls'],2)  # Logical steps, first one was local replay.
        self.assertEqual(r['credits'],self.cost*2)  # First cost once, not charged twice.
        self.assertEqual(self.sdk,['synthesize'])
        self.assertEqual(before,(self.root/'turns/01.json').read_bytes())
        self.assertEqual(old,(self.root/'attempt.json').read_bytes())
        self.assertTrue(self.resume(card)['replayed_receipt'])
        self.assertEqual(self.sdk,['synthesize'])
        self.assertEqual(f.run(approved_digest=self.parent)['state'],'attention')
        with self.assertRaises(ValueError):f.prepare(refresh=True)

    def test_missing_or_wrong_checkpoint_never_connects(self):
        rr.prepare()
        with self.assertRaises(ValueError):rr.resume(approved_digest='yes')
        self.assertEqual(self.factory.call_count,0);self.assertFalse(self.sdk)

    def test_failed_or_uncertain_delivery_cannot_be_recovered(self):
        self.raw['state']='delivery_unknown';self.write('turns/01.json',self.raw)
        with self.assertRaises(ValueError):rr.prepare()
        self.assertFalse(self.sdk)

    def test_unknown_usage_cannot_be_recovered(self):
        self.raw['receipt']['thread_token_usage']=None;self.write('turns/01.json',self.raw)
        with self.assertRaises(ValueError):rr.prepare()

    def test_second_sdk_turn_disqualifies_this_narrow_recovery(self):
        self.write('turns/02.json',{'state':'delivery_unknown'})
        with self.assertRaises(ValueError):rr.prepare()

    def test_unknown_source_or_nonexact_quote_is_not_repaired(self):
        self.value['covered'][1]['quote']='Invented quotation'
        self.raw['receipt']['answer']=json.dumps(self.value);self.write('turns/01.json',self.raw)
        with self.assertRaises(ValueError):rr.prepare()

    def test_outstanding_tool_item_prevents_recovery(self):
        self.raw['unexpected_item_types']=['commandExecution'];self.write('turns/01.json',self.raw)
        with self.assertRaises(ValueError):rr.prepare()

    def test_runtime_failure_uses_one_recovery_marker_and_never_retries(self):
        card=rr.prepare()
        with patch.object(f.calibration,'_runtime',return_value={'socket':'changed'}):r=self.resume(card)
        self.assertEqual(r['state'],'attention')
        self.assertFalse(self.sdk)
        self.assertTrue(self.resume(card)['replayed_receipt'])
        self.assertEqual(self.factory.call_count,1)

    def test_source_change_or_modified_saved_receipt_blocks_before_resume(self):
        card=rr.prepare();self.head.return_value='b'*40
        with self.assertRaises(ValueError):self.resume(card)
        self.head.return_value=self.snap.head
        self.raw['receipt']['answer']='different';self.write('turns/01.json',self.raw)
        with self.assertRaises(ValueError):self.resume(card)
        self.assertEqual(self.factory.call_count,0)

    def test_pause_deducts_known_first_turn_processing_from_remaining_time(self):
        rr.prepare()
        raw=json.loads((self.root/'receipt-recovery.json').read_text())
        self.assertEqual(raw['repair']['packet']['measurements']['limits']['seconds'],59)


class NormalizationTests(unittest.TestCase):
    def setUp(self):
        s=snapshot();self.payload={'original':asdict(s.original),'sources':[asdict(x) for x in s.sources]}
        self.answer={'covered':[{'source':x['path'],'quote':x['text']} for x in
            [self.payload['original'],*self.payload['sources']]],'notes':'Unmodified notes.'}

    def test_only_redundant_original_row_is_removed_without_mutating_raw(self):
        before=copy.deepcopy(self.answer);new,proof=f.normalize_inspection(self.answer,self.payload)
        self.assertEqual(self.answer,before)
        self.assertEqual(new['covered'],before['covered'][1:])
        self.assertEqual(new['notes'],before['notes'])
        self.assertEqual(proof['kept_sources'],2)

    def test_missing_duplicate_or_inexact_rows_remain_errors(self):
        for kind in ('missing','duplicate_original','bad_original','bad_doc','unknown','extra_key'):
            a=copy.deepcopy(self.answer)
            if kind=='missing':a['covered'].pop()
            elif kind=='duplicate_original':a['covered'].append(a['covered'][0])
            elif kind=='bad_original':a['covered'][0]['quote']='Wrong'
            elif kind=='bad_doc':a['covered'][1]['quote']='Wrong'
            elif kind=='unknown':a['covered'][1]['source']='unknown'
            else:a['covered'][1]['extra']='not allowed'
            with self.subTest(kind=kind):
                unchanged,proof=f.normalize_inspection(a,self.payload)
                self.assertIsNone(proof);self.assertEqual(unchanged,a)


if __name__=='__main__':unittest.main()
