import copy
from dataclasses import replace
from datetime import date,datetime
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from zoneinfo import ZoneInfo
from unittest.mock import patch

from app import recovery_guide_consolidation as c
from app import recovery_guide_maintainer as m
from app import recovery_guide_quality as q
from app.recovery_guide_sources import Source,Snapshot,digest,canonical_json
from tests.test_recovery_guide import consolidated_answer,USAGE

ORIGINAL='''OBNOVA SAMANTHY NA NOVÉM MACU
Nejnovější update dokumentu z 01112026

1. OBNOVA MACU
==============
Python a soukromá data. Nic nemaž.

Záloha 20261018_210658: 90833 souborů.

2. IPHONE A ICLOUD
==================
Tailscale a iPhone ověř na zařízení.
'''
GUIDANCE='Zálohu vybírej podle dokončeného manifestu.'

def snapshot(text=ORIGINAL):
    return Snapshot('a'*40,Source('original_guide',digest(text),text,'previous_version'),
        (Source('memory/current.md',digest(GUIDANCE),GUIDANCE,'documented_not_live'),))

def evidence():return [{'source':'memory/current.md','quote':GUIDANCE}]


class Consolidation(unittest.TestCase):
    def setUp(self):
        self.snap=snapshot();self.req=c.prepare(self.snap,[],date(2026,11,8))

    def answer(self):return consolidated_answer(self.req.payload)

    def integrated(self):
        result=self.answer()
        result['sections']['c01'][1]={'action':'retire','block':2,'reason':'Starý konkrétní snapshot je zastaralá poznámka.','evidence':evidence()}
        result['sections']['c01'].append({'action':'insert','text':GUIDANCE,'status':'documented','evidence':evidence()})
        return result

    def validate(self,answer):return c.validate(answer,self.snap,self.req)

    def test_single_current_document_retires_obsolete_snapshot_without_copying_whole_guide(self):
        result=self.validate(self.integrated());text=result['candidate']
        self.assertEqual(text.count(c.STAMP),1);self.assertIn(c.STAMP+'08112026',text)
        self.assertNotIn('01112026',text);self.assertNotIn('20261018_210658',text)
        self.assertIn('Python a soukromá data. Nic nemaž.',text);self.assertIn(GUIDANCE,text)
        self.assertEqual(len(q._headings(text)),2)
        self.assertEqual(result['publication'],'not_authorized')
        self.assertEqual(result['semantic_acceptance'],'required')
        self.assertTrue(any(r['action']=='retire' for r in result['change_audit']))
        self.assertLess(len(canonical_json(self.integrated())),len(self.req.envelope)+500)

    def test_two_weeks_do_not_stack_dates_supplements_or_unverified_prefixes(self):
        first=self.integrated();first['sections']['c01'][-1]['status']='unverified'
        one=self.validate(first)['candidate'];snap=snapshot(one)
        req=c.prepare(snap,[],date(2026,11,15));two=c.validate(consolidated_answer(req.payload),snap,req)['candidate']
        self.assertIn(c.STAMP+'15112026',two);self.assertNotIn('08112026',two)
        self.assertEqual(two.count(c.STAMP),1);self.assertEqual(two.count('[Neověřeno]'),1)
        self.assertEqual(two.count(GUIDANCE),1);self.assertNotIn('DOPLNĚNÍ',two)

    def test_rewrite_replaces_old_setting_in_its_chapter_without_an_appendix(self):
        text='Tailscale a iPhone potřebují nové přihlášení.'
        doc=Source('memory/mobile.md',digest(text),text,'documented_not_live')
        snap=replace(self.snap,sources=(*self.snap.sources,doc));req=c.prepare(snap,[],date(2026,11,8))
        a=self.integrated();a['request_id']=req.payload['request_id']
        a['sections']['c02'][0]={'action':'rewrite','blocks':[1],'text':text,'status':'documented',
            'evidence':[{'source':doc.path,'quote':text}]}
        result=c.validate(a,snap,req)['candidate']
        self.assertIn(text,result);self.assertNotIn('Tailscale a iPhone ověř na zařízení.',result)
        self.assertGreater(result.index(text),result.index('2. IPHONE A ICLOUD'))

    def test_obsolete_statistics_cannot_be_reintroduced_as_a_new_note(self):
        a=self.integrated();a['sections']['c01'][-1]['text']='Záloha obsahovala 90833 souborů.'
        with self.assertRaisesRegex(q.QualityError,'obsolete_backup_statistics'):self.validate(a)

    def test_keep_cannot_retain_old_snapshot(self):
        with self.assertRaisesRegex(q.QualityError,'fixed_backup_snapshot'):self.validate(self.answer())

    def test_model_cannot_control_revision_date(self):
        a=self.integrated();a['revision_date']='2099-01-01'
        with self.assertRaisesRegex(q.QualityError,'response_shape'):self.validate(a)

    def test_duplicate_revision_in_new_text_is_rejected(self):
        a=self.integrated();a['sections']['c01'][-1]['text']=c.STAMP+'08112026'
        with self.assertRaisesRegex(q.QualityError,'duplicate_revision'):self.validate(a)

    def test_appendix_heading_rejected_even_with_valid_citations(self):
        for label in ('DOPLNĚNÍ 1 — změny','Dodatek k návodu'):
            a=self.integrated();a['sections']['c01'][-1]['text']=label+'\n'+GUIDANCE
            with self.subTest(label=label),self.assertRaisesRegex(q.QualityError,'appendix_layer'):self.validate(a)

    def test_missing_section_or_legacy_paragraph_format_cannot_bypass_contract(self):
        a=self.integrated();del a['sections']['c02']
        for value in (a,{'paragraphs':[]}):
            with self.subTest(value=value),self.assertRaisesRegex(q.QualityError,'response_shape'):self.validate(value)

    def test_missing_or_duplicate_block_accounting_is_rejected(self):
        a=self.integrated();a['sections']['c01'].pop(0)
        with self.assertRaisesRegex(q.QualityError,'unaccounted_original_block'):self.validate(a)
        a=self.integrated();a['sections']['c01'].append({'action':'keep','block':1})
        with self.assertRaisesRegex(q.QualityError,'duplicate_block_coverage'):self.validate(a)

    def test_unknown_nonintegral_and_bool_block_ids_are_rejected(self):
        for bad in (9999,True,1.5,'1',float('inf')):
            a=self.integrated();a['sections']['c01'][0]['block']=bad
            with self.subTest(bad=bad),self.assertRaisesRegex(q.QualityError,'unknown_block'):self.validate(a)
        a=self.integrated();a['sections']['c01'][0]['block']=1.0
        self.assertIn(GUIDANCE,self.validate(a)['candidate'])

    def test_operational_safety_block_cannot_be_retired(self):
        a=self.integrated();a['sections']['c01'][0]={'action':'retire','block':1,'reason':'Úklid.','evidence':evidence()}
        with self.assertRaisesRegex(q.QualityError,'operational_block_retired'):self.validate(a)

    def test_rewrite_cannot_drop_safety_control(self):
        a=self.integrated();a['sections']['c01'][0]={'action':'rewrite','blocks':[1],'text':'Python a soukromá data.',
            'status':'documented','evidence':evidence()}
        with self.assertRaisesRegex(q.QualityError,'safety_control_lost'):self.validate(a)

    def test_changed_text_retirement_and_schema_require_nonempty_evidence(self):
        for n in (1,2):
            a=self.integrated();a['sections']['c01'][n]['evidence']=[]
            with self.subTest(action=n),self.assertRaisesRegex(q.QualityError,'missing_retirement_evidence|missing_evidence'):self.validate(a)

    def test_new_commands_and_uncited_paths_still_fail_core_gate(self):
        for text,code in [('git status','unregistered_command'),('Použij /invented/path','uncited_technical_literal')]:
            a=self.integrated();a['sections']['c01'][-1]['text']=text
            with self.subTest(text=text),self.assertRaisesRegex(q.QualityError,code):self.validate(a)

    def test_secrets_historical_as_current_and_live_claims_remain_blocked(self):
        for text,code in [('sk-'+'A'*30,'unsafe_text'),('Dnes je iPhone živě ověřen.','unproven_live_claim')]:
            a=self.integrated();a['sections']['c01'][-1]['text']=text
            with self.subTest(text=text),self.assertRaisesRegex(q.QualityError,code):self.validate(a)
        snap=replace(self.snap,sources=(replace(self.snap.sources[0],authority='historical_or_mixed'),))
        req=c.prepare(snap,[],date(2026,11,8));a=self.integrated();a['request_id']=req.payload['request_id']
        with self.assertRaisesRegex(q.QualityError,'history_as_current'):c.validate(a,snap,req)

    def test_protected_command_block_cannot_be_replaced_by_short_summary(self):
        snap=snapshot(ORIGINAL.replace('Python a soukromá data. Nic nemaž.','    python scripts/check.py'))
        req=c.prepare(snap,[],date(2026,11,8));a=consolidated_answer(req.payload)
        a['sections']['c01'][0]={'action':'rewrite','blocks':[1],'text':GUIDANCE,'status':'documented','evidence':evidence()}
        with self.assertRaisesRegex(q.QualityError,'protected_procedure_lost'):c.validate(a,snap,req)

    def test_topic_cannot_disappear_under_short_rewrite(self):
        a=self.integrated();a['sections']['c02'][0]={'action':'rewrite','blocks':[1],'text':GUIDANCE,'status':'documented','evidence':evidence()}
        with self.assertRaisesRegex(q.QualityError,'topic_lost_'):self.validate(a)

    def test_reordering_and_nested_or_duplicate_chapters_are_rejected(self):
        a=self.integrated();a['sections']['c01'][:2]=list(reversed(a['sections']['c01'][:2]))
        with self.assertRaisesRegex(q.QualityError,'reordered_original_blocks'):self.validate(a)
        a=self.integrated();a['sections']['c01'][-1]['text']='3. NOVÁ KAPITOLA\n'+GUIDANCE
        with self.assertRaisesRegex(q.QualityError,'nested_chapter_heading'):self.validate(a)

    def test_request_mutation_and_response_replay_from_other_week_are_rejected(self):
        other=c.prepare(self.snap,[],date(2026,11,15))
        with self.assertRaisesRegex(q.QualityError,'response_request_changed'):c.validate(self.integrated(),self.snap,other)
        payload=self.req.payload;payload['guide_layout']['sections'][1]['heading']='HACK'
        with self.assertRaisesRegex(q.QualityError,'request_changed'):c.schema(payload)
        bad=c.Request(canonical_json(payload))
        with self.assertRaisesRegex(q.QualityError,'request_binding_changed'):c.validate(self.integrated(),self.snap,bad)

    def test_legacy_gate_still_refuses_truncating_historical_chapter(self):
        text1=ORIGINAL[ORIGINAL.index('1. OBNOVA'):ORIGINAL.index('Záloha 20261018')].strip()
        text2=ORIGINAL[ORIGINAL.index('2. IPHONE'):].strip()
        answer={'paragraphs':[{'text':t,'status':'unchanged','evidence':[]} for t in (text1,text2)]}
        with self.assertRaisesRegex(q.QualityError,'chapter_content_lost'):q.validate(answer,self.snap)

    def test_negative_paid_generation_prohibition_is_not_an_activation(self):
        text=ORIGINAL.replace('Záloha 20261018_210658: 90833 souborů.',
            'Samotná knihovna nepovoluje nový placený hlasový pokus.')
        snap=snapshot(text);req=c.prepare(snap,[],date(2026,11,8))
        self.assertIn('nepovoluje',c.validate(consolidated_answer(req.payload),snap,req)['candidate'])
        # Closed legacy policy is not reinterpreted by this new contract.
        with self.assertRaisesRegex(q.QualityError,'retired_voice_reference'):
            q.validate({'paragraphs':[{'text':text,'status':'unchanged','evidence':[]}]},snap)

    def test_retired_identifiers_and_positive_activation_still_fail(self):
        for text in ('Zapni placený hlasový rozhovor.','Povol placený hlasový rozhovor.','Spusť read_only_voice'):
            a=self.integrated();a['sections']['c01'][-1]['text']=text
            with self.subTest(text=text),self.assertRaisesRegex(q.QualityError,'retired_voice_reference'):self.validate(a)

    def test_model_status_prefix_cannot_accumulate_across_weeks(self):
        a=self.integrated();a['sections']['c01'][-1]['text']='[Neověřeno]\n'+GUIDANCE
        with self.assertRaisesRegex(q.QualityError,'model_status_prefix'):self.validate(a)

    @unittest.skipUnless(importlib.util.find_spec('jsonschema'),'independent oracle unavailable')
    def test_independent_schema_accepts_valid_plan_and_rejects_empty_evidence(self):
        from jsonschema import Draft202012Validator
        schema=c.schema(self.req.payload);Draft202012Validator.check_schema(schema)
        validator=Draft202012Validator(schema);validator.validate(self.integrated())
        bad=self.integrated();bad['sections']['c01'][-1]['evidence']=[]
        self.assertTrue(list(validator.iter_errors(bad)))
        bad=self.integrated();bad['sections']['c01'][0]['block']=True
        self.assertTrue(list(validator.iter_errors(bad)))


class WeeklyController(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.state=Path(temp.name)/'state'
        self.calls=[];self.snap=snapshot();self.now=datetime(2026,11,8,10,tzinfo=ZoneInfo('Europe/Prague'))

    def call(self,payload,kind):
        self.calls.append((payload,kind))
        if kind=='inspect':answer={'covered':[{'source':s['path'],'quote':s['text']} for s in payload['sources']],'notes':GUIDANCE}
        else:
            answer=consolidated_answer(payload)
            for section in payload['guide_layout']['sections']:
                retired=False
                for i,block in enumerate(section['blocks']):
                    if block['id'] in section['retirable']:
                        answer['sections'][section['id']][i]={'action':'retire','block':block['id'],
                            'reason':'Zastaralá zálohovací statistika.','evidence':evidence()};retired=True
                if retired:answer['sections'][section['id']].append({'action':'insert','text':GUIDANCE,
                    'status':'documented','evidence':evidence()})
        return {'answer':answer,'usage':USAGE}

    def run_job(self,**kwargs):
        args=dict(state_dir=self.state,now=self.now,limits=m.Limits(40000,2000,8,50,100,60),count_tokens=len,
            call=self.call,approved_snapshot=self.snap.sha256,assert_sources=lambda:True,confirmed=True)
        args.update(kwargs);return m.run(self.snap,**args)

    def test_real_controller_enforces_policy_and_persists_separate_audit(self):
        result=self.run_job();self.assertEqual(result['state'],'review');self.assertEqual(result['format_contract'],c.VERSION)
        text=(self.state/'2026-W45-candidate.txt').read_text()
        self.assertIn(c.STAMP+'08112026',text);self.assertNotIn('20261018_210658',text)
        self.assertTrue((self.state/'2026-W45-consolidation-audit.json').exists())
        self.assertEqual(self.run_job()['state'],'review');self.assertEqual(len(self.calls),2)

    def test_two_scheduled_weeks_start_from_last_result_without_stacking(self):
        first=self.run_job();self.assertEqual(first['state'],'review')
        text=(self.state/'2026-W45-candidate.txt').read_text()
        self.snap=replace(self.snap,original=replace(self.snap.original,text=text,sha256=digest(text)))
        self.now=datetime(2026,11,15,10,tzinfo=ZoneInfo('Europe/Prague'))
        second=self.run_job();self.assertEqual(second['state'],'review')
        result=(self.state/'2026-W46-candidate.txt').read_text()
        self.assertEqual(result.count(c.STAMP),1);self.assertIn('15112026',result)
        self.assertNotIn('08112026',result);self.assertEqual(result.count(GUIDANCE),1)
        self.assertEqual(len(self.calls),4)

    def test_invalid_second_phase_is_durable_and_never_retried(self):
        original=self.call
        def bad(payload,kind):
            response=original(payload,kind)
            if kind=='synthesize':response['answer']['sections']['c01'][-1]['text']='DOPLNĚNÍ\n'+GUIDANCE
            return response
        result=self.run_job(call=bad);self.assertEqual(result['state'],'attention')
        self.assertEqual(result['quality_issue'],'consolidation_appendix_layer')
        self.run_job(call=bad);self.assertEqual(len(self.calls),2)
        self.assertFalse((self.state/'2026-W45-candidate.txt').exists())

    def test_source_drift_stops_without_retry_or_publication(self):
        checks=iter([True,True,False]);r=self.run_job(assert_sources=lambda:next(checks))
        self.assertEqual(r['state'],'attention');self.assertEqual(len(self.calls),1)

    def test_existing_legacy_receipt_is_read_only_not_upgraded_or_reexecuted(self):
        self.state.mkdir();old={'state':'attention','model_calls':1,'format_contract':'legacy'}
        path=self.state/'2026-W45.json';path.write_text(json.dumps(old));before=path.read_bytes()
        result=self.run_job();self.assertEqual(result['format_contract'],'legacy')
        self.assertEqual(path.read_bytes(),before);self.assertFalse(self.calls)


if __name__=='__main__':unittest.main()
