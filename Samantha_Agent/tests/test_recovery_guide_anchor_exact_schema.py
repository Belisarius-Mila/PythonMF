from dataclasses import replace,FrozenInstanceError
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app import recovery_guide_anchor_exact_schema as e
from app import recovery_guide_anchor_exact_plan as p
from app import recovery_guide_anchor_protocol as core
from app.recovery_guide_anchors import Catalogue,AnchorError
from app.recovery_guide_quality import QualityError
from app.recovery_guide_sources import canonical_json,digest
from tests.test_recovery_guide_anchor_full_plan import snapshot,source,ENC,MODULE


class ExactSchema(unittest.TestCase):
    def setUp(self):
        self.snap=snapshot([source('memory/a.md','# A\n\nshort\n'+'x'*1000+'\n'),
                            source('memory/b.md','# B\nfirst\nsecond\n')])
        self.cat=Catalogue(self.snap);self.paths=[s.path for s in self.snap.sources]
        self.blocked,_,_=p.old._index(self.cat,ENC)
        self.bundle=e.inspection(self.cat,self.paths,self.blocked)
        self.a,self.b=self.cat.document_ids

    def value(self,bundle=None,findings=None):
        bundle=bundle or self.bundle
        return {'request_id':bundle.wire.payload['request_id'],
            'covered':{sid:1 for sid in json.loads(bundle.inner.envelope_json)['scope']},
            'findings':findings or []}

    def raw(self,**kwargs):return canonical_json(self.value(**kwargs))

    def synth(self,findings=None):
        return e.synthesis(self.cat,[(self.bundle,self.raw(findings=findings))],self.blocked,ENC,10**9)

    def test_complete_text_including_blank_and_blocked_lines_stays_unchanged(self):
        for source in [self.bundle.wire.payload['data']['original'],*self.bundle.wire.payload['data']['sources']]:
            self.assertEqual(''.join(line[1] for line in source['lines']),self.cat.source(source['source_id']).text)
        a=self.bundle.wire.payload['data']['sources'][0]
        self.assertEqual([line[0] for line in a['lines']],[1,None,2,None])
        self.assertEqual(self.bundle.index.anchor(self.a,2),'l3')

    def test_unissued_blank_long_or_foreign_pair_cannot_be_decoded(self):
        for sid,index in [(self.a,131111),(self.a,3),(self.a,0),('foreign',1),(self.a,'l131111'),
                          (self.a,True),(self.a,1.5),(self.a,float('inf'))]:
            with self.subTest(sid=sid,index=index),self.assertRaises(AnchorError):self.bundle.index.anchor(sid,index)

    def test_json_integer_semantics_accept_1_point_0_but_never_string_or_bool(self):
        value=self.value();value['covered'][self.a]=1.0
        checked=e.resolve_inspection(self.cat,self.bundle,canonical_json(value),ENC)
        self.assertEqual(json.loads(checked['core_response'])['covered'][self.a],'l1')
        for bad in ('1',True):
            value['covered'][self.a]=bad
            with self.assertRaises(AnchorError):e.decode(self.cat,self.bundle,canonical_json(value))

    def test_domain_and_bundle_are_immutable_and_wire_properties_are_copies(self):
        with self.assertRaises(FrozenInstanceError):self.bundle.phase='changed'
        with self.assertRaises(TypeError):self.bundle.index.sources[self.a]=('l999',)
        before=self.bundle.wire.sha256;self.bundle.wire.schema.clear();self.bundle.wire.payload.clear()
        self.assertEqual(self.bundle.wire.sha256,before)

    def test_wrong_request_or_index_revision_rejects_response(self):
        value=self.value();value['request_id']='0'*64
        with self.assertRaisesRegex(AnchorError,'request_changed'):e.decode(self.cat,self.bundle,canonical_json(value))
        changed=Catalogue(replace(self.snap,head='b'*40))
        with self.assertRaisesRegex(AnchorError,'catalogue_changed'):e.decode(changed,self.bundle,self.raw())

    def test_tampered_wire_cannot_rename_or_loosen_domains(self):
        data=json.loads(self.bundle.wire.envelope_json)
        data['schema']['properties']['covered']['properties'][self.a]['maximum']=131111
        bad=replace(self.bundle,wire=core.Request(canonical_json(data)))
        with self.assertRaisesRegex(AnchorError,'wire_changed'):e.decode(self.cat,bad,self.raw())

    def test_no_legacy_anchor_fallback_extra_fields_or_missing_coverage(self):
        for mode in ('legacy','extra','missing','duplicate'):
            data=self.value()
            if mode=='legacy':data['findings']=[{'text':'claim','evidence':[{'source_id':self.a,'anchor_id':'l1'}]}]
            elif mode=='extra':data['quote']='invented'
            elif mode=='missing':data['covered'].pop(self.a)
            else:
                raw=canonical_json(data).replace('"'+self.a+'":1','"'+self.a+'":1,"'+self.a+'":1')
                with self.assertRaises(AnchorError):e.decode(self.cat,self.bundle,raw)
                continue
            with self.subTest(mode=mode),self.assertRaises(AnchorError):e.decode(self.cat,self.bundle,canonical_json(data))

    def test_source_specific_maximum_is_not_a_global_cross_product(self):
        self.assertEqual(len(self.bundle.index.sources[self.a]),2)
        self.assertEqual(len(self.bundle.index.sources[self.b]),3)
        data=self.value(findings=[{'text':'claim','evidence':[{'source_id':self.a,'citation_index':3}]}])
        with self.assertRaises(AnchorError):e.resolve_inspection(self.cat,self.bundle,canonical_json(data),ENC)

    def test_synthesis_reindexes_only_forwarded_document_evidence(self):
        findings=[{'text':'claim','evidence':[{'source_id':self.b,'citation_index':3}]}]
        bundle=self.synth(findings)
        # Coverage forwarded l1, finding forwarded l3; final indices are 1,2.
        self.assertEqual(bundle.index.sources[self.b],('l1','l3'))
        self.assertEqual(bundle.index.anchor(self.b,2),'l3')
        self.assertNotIn((self.b,'l2'),bundle.index.reverse)
        self.assertEqual(bundle.wire.payload['data']['findings'][0]['evidence'][0]['citation_index'],2)

    def test_synthesis_needs_all_documents_and_keeps_every_finding(self):
        small=e.inspection(self.cat,self.paths[:1],self.blocked)
        with self.assertRaisesRegex(AnchorError,'incomplete'):
            e.synthesis(self.cat,[(small,self.raw(bundle=small))],self.blocked,ENC,10**9)
        findings=[{'text':'claim','evidence':[{'source_id':self.a,'citation_index':2}]}]
        self.assertEqual(len(self.synth(findings).wire.payload['data']['findings']),1)

    def test_old_quality_and_budget_gates_remain_active(self):
        bundle=self.synth()
        raw=canonical_json({'request_id':bundle.wire.payload['request_id'],'paragraphs':[
            {'text':self.snap.original.text,'status':'unchanged','evidence':[]}]})
        self.assertEqual(e.validate_synthesis(self.cat,bundle,raw,self.snap,ENC),self.snap.original.text)
        with self.assertRaisesRegex(AnchorError,'input_exceeded'):
            e.synthesis(self.cat,[(self.bundle,self.raw())],self.blocked,ENC,1)
        data=self.value(findings=[{'text':'x'*1500,'evidence':[{'source_id':self.a,'citation_index':1}]}])
        with self.assertRaises(AnchorError):e.resolve_inspection(self.cat,self.bundle,canonical_json(data),ENC)

    def test_exact_resolver_does_not_change_quote_case_whitespace_or_source(self):
        data=self.value();data['covered'][self.a]=2
        result=e.resolve_inspection(self.cat,self.bundle,canonical_json(data),ENC)
        self.assertEqual(result['result']['legacy']['covered'][0],{'source':'memory/a.md','quote':'short'})

    def test_many_valid_anchors_do_not_consume_enum_limit(self):
        snap=snapshot([source('memory/a.md','line\n'*2001)]);cat=Catalogue(snap)
        bundle=e.inspection(cat,['memory/a.md'],{})
        self.assertEqual(len(bundle.index.sources[cat.document_ids[0]]),2001)
        self.assertEqual(e.schema_stats(bundle.wire.schema)['enum_values'],3)
        with self.assertRaises(AnchorError):e.ReferenceIndex(cat,{cat.document_ids[0]:('l99999',)})

    def test_new_command_with_matching_evidence_is_still_blocked(self):
        text='# A\ngit status\n';first=source('memory/a.md',text)
        snap=snapshot([first]);cat=Catalogue(snap);bundle=e.inspection(cat,[first.path],{})
        raw=canonical_json({'request_id':bundle.wire.payload['request_id'],'covered':{cat.document_ids[0]:1},
            'findings':[{'text':'Příkaz.','evidence':[{'source_id':cat.document_ids[0],'citation_index':2}]}]})
        synth=e.synthesis(cat,[(bundle,raw)],{},ENC,10**9)
        answer=canonical_json({'request_id':synth.wire.payload['request_id'],'paragraphs':[
            {'text':snap.original.text,'status':'unchanged','evidence':[]},
            {'text':'git status','status':'unverified','evidence':[{'source_id':cat.document_ids[0],'citation_index':2}]}]})
        with self.assertRaisesRegex(QualityError,'unregistered_command'):
            e.validate_synthesis(cat,synth,answer,snap,ENC)

    def test_equal_length_domains_share_a_schema_branch_without_losing_pair_binding(self):
        snap=snapshot([source('memory/a.md','# A'),source('memory/b.md','# B')]);cat=Catalogue(snap)
        bundle=e.inspection(cat,[s.path for s in snap.sources],{})
        branches=bundle.wire.schema['$defs']['reference']['anyOf']
        self.assertTrue(any(set(b['properties']['source_id']['enum'])==set(cat.document_ids) for b in branches))
        self.assertLessEqual(e.schema_stats(bundle.wire.schema)['enum_values'],len(cat.document_ids)+2)

    @unittest.skipUnless(importlib.util.find_spec('jsonschema'),'optional independent JSON Schema oracle unavailable')
    def test_independent_jsonschema_oracle_accepts_exact_domain_and_rejects_regression(self):
        from jsonschema import Draft202012Validator
        schema=self.bundle.wire.schema;Draft202012Validator.check_schema(schema);validator=Draft202012Validator(schema)
        validator.validate(self.value())
        for bad in ('l131111',131111,0,3,True,'1'):
            data=self.value();data['covered'][self.a]=bad
            self.assertFalse(validator.is_valid(data),bad)
        for sid,anchors in self.bundle.index.sources.items():
            for i in range(1,len(anchors)+1):
                data=self.value(findings=[{'text':'claim','evidence':[{'source_id':sid,'citation_index':i}]}])
                self.assertTrue(validator.is_valid(data))
        data=self.value(findings=[{'text':'claim','evidence':[{'source_id':self.a,'citation_index':3}]}])
        self.assertFalse(validator.is_valid(data))

    def test_documented_schema_limits_and_no_regex_approximation(self):
        stats=e.schema_stats(self.bundle.wire.schema)
        self.assertLessEqual(stats['object_properties'],5000);self.assertLessEqual(stats['max_depth'],10)
        self.assertNotIn('pattern',canonical_json(self.bundle.wire.schema))
        bad=self.bundle.wire.schema;bad['properties']['many']={'type':'string','enum':['x'+str(i) for i in range(1001)]}
        bad['required'].append('many')
        with self.assertRaises(AnchorError):e.schema_stats(bad)


class ExactPlan(unittest.TestCase):
    def test_new_full_reservation_includes_new_schema_and_all_texts(self):
        with patch.object(p.old.reference,'tokenizer_identity',return_value={'fixture':True}):r=p.measure(snapshot(),MODULE)
        self.assertEqual(r['source_count'],2);self.assertEqual(r['planned_model_calls'],2)
        self.assertTrue(r['all_source_texts_preserved']);self.assertTrue(r['execution_adapter_integrated'])
        self.assertEqual(r['synthesis_output_acceptance_tokens'],32000)
        self.assertFalse(r['provider_acceptance_live_verified']);self.assertEqual(r['model_calls'],0)
        self.assertGreaterEqual(r['synthesis_reference_reservation'],r['synthesis_fixture_actual_reference_tokens'])
        self.assertGreaterEqual(r['proposed_credit_acceptance'],r['planning_standard_credits_no_cache'])

    def test_preparation_writes_only_immutable_private_nonpaid_plan(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();guide=root/'guide';guide.write_text(snapshot().original.text)
            with patch.object(p,'STATE',root/'state'),patch.object(p.old,'ORIGINAL',guide),\
                 patch.object(p.old.old,'_head',return_value='a'*40),\
                 patch.object(p,'collect_revision',return_value=snapshot()),\
                 patch.object(p,'_code',return_value={}),\
                 patch.object(p.old.old,'_tokenizer',return_value={'blocked_anchor_ids':{}}) as count:
                a=p.prepare();self.assertEqual(a,p.prepare());self.assertEqual(count.call_count,1)
                self.assertFalse(a['paid_execution_available']);self.assertTrue(a['frozen_inputs_current'])
                self.assertNotIn('approval_digest',a);self.assertFalse(hasattr(p,'run'))
                b=p.prepare(refresh=True);self.assertNotEqual(a['plan_digest'],b['plan_digest'])
                self.assertEqual((p.STATE/'plan.json').stat().st_mode & 0o777,0o600)
                guide.write_text('changed');self.assertFalse(p.prepare()['frozen_inputs_current'])


if __name__=='__main__':unittest.main()
