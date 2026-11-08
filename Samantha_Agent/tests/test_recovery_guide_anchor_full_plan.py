from dataclasses import replace
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app import recovery_guide_anchor_full_plan as p
from app import recovery_guide_anchor_protocol as protocol
from app.recovery_guide_anchors import Catalogue, AnchorError
from app.recovery_guide_sources import Snapshot, Source, canonical_json, digest
from tests.test_recovery_guide import ORIGINAL


ENC = SimpleNamespace(encode_ordinary=lambda text:list(text.encode('utf-8')))
MODULE = SimpleNamespace(get_encoding=lambda _:ENC)


def source(path,text):
    return Source(path,digest(text),text,'documented_not_live')


def snapshot(sources=None):
    return Snapshot('a'*40,Source('original_guide',digest(ORIGINAL),ORIGINAL,'previous_version'),
        tuple(sources or [source('memory/a.md','# A\nKrátká citace.\n'),
                          source('memory/b.md','# B\nJiná citace.\n')]))


def response(cat,req,paths,findings=None):
    return canonical_json({'request_id':req.payload['request_id'],
        'covered':{cat.source_id(path):'l1' for path in paths},'findings':findings or []})


class FullPlan(unittest.TestCase):
    def measure(self,snap=None):
        with patch.object(p.reference,'tokenizer_identity',return_value={'fixture':True}):
            return p.measure(snap or snapshot(),MODULE)

    def test_complete_texts_and_schema_and_two_instructions_are_counted(self):
        snap=snapshot();r=self.measure(snap);cat=Catalogue(snap)
        self.assertEqual(r['source_count'],2);self.assertEqual(r['coverage_planned'],1)
        self.assertFalse(r['execution_adapter_implemented']);self.assertEqual(r['model_calls_started'],0)
        self.assertEqual(r['planned_syntheses'],1);self.assertEqual(r['planned_model_calls'],2)
        row=r['batches'][0];inner,wire=p.inspection(cat,row['source_paths'],r['blocked_anchor_ids'])
        count=len((p.INSTRUCTIONS+p.INSTRUCTIONS+canonical_json(wire.payload)+canonical_json(wire.schema)).encode())
        self.assertEqual(row['reference_input_tokens'],count)
        for s in wire.payload['anchor_request']['data']['sources']:
            self.assertEqual(''.join(line[1] for line in s['lines']),cat.source(s['source_id']).text)
        self.assertEqual(row['wire_request_sha256'],wire.sha256)

    def test_long_citation_is_explicitly_blocked_but_its_complete_text_is_kept(self):
        snap=snapshot([source('memory/a.md','# Header\n'+'x'*5000+'\n')]);cat=Catalogue(snap)
        r=self.measure(snap);sid=cat.document_ids[0]
        self.assertIn('l2',r['blocked_anchor_ids'][sid]);self.assertEqual(r['blocked_anchor_count'],1)
        inner,wire=p.inspection(cat,['memory/a.md'],r['blocked_anchor_ids'])
        self.assertEqual(len(wire.payload['anchor_request']['data']['sources'][0]['lines'][1][1]),5001)
        bad=json.loads(response(cat,inner,['memory/a.md']));bad['covered'][sid]='l2'
        with self.assertRaisesRegex(AnchorError,'citation_reservation'):
            p.validate_inspection(cat,inner,canonical_json(bad),ENC)

    def test_source_without_any_eligible_citation_is_unsupported_not_skipped(self):
        with self.assertRaisesRegex(AnchorError,'no_bounded_citation'):
            self.measure(snapshot([source('memory/a.md','x'*5000)]))

    def test_oversized_single_document_is_not_truncated_or_split(self):
        with self.assertRaisesRegex(AnchorError,'single_document'):
            self.measure(snapshot([source('memory/a.md','# Header\n'+'x'*250000)]))

    def test_multiple_batches_cover_every_document_exactly_once(self):
        snap=snapshot([source(f'memory/{i}.md','# Header\n'+'x'*50000) for i in range(5)])
        r=self.measure(snap);paths=[path for row in r['batches'] for path in row['source_paths']]
        self.assertGreater(r['planned_inspections'],1)
        self.assertEqual(len(paths),len(set(paths)));self.assertEqual(set(paths),{s.path for s in snap.sources})
        self.assertTrue(all(row['input_acceptance_tokens']<=p.MAX_INPUT for row in r['batches']))

    def test_synthesis_has_distinct_measured_time_and_not_a_retroactive_exception(self):
        r=self.measure()
        self.assertEqual(r['phase_seconds'],{'inspect':300,'synthesize':900})
        self.assertGreater(r['time_basis']['output_scaled_seconds_with_25_percent_margin'],400.240)
        self.assertLess(r['time_basis']['output_scaled_seconds_with_25_percent_margin'],900)
        self.assertEqual(r['run_seconds_acceptance'],r['planned_inspections']*300+900)
        self.assertFalse(r['hard_billing_output_or_wallclock_cap'])

    def test_budget_includes_full_output_and_synthesis_input_reservation(self):
        r=self.measure()
        total=sum(row['input_acceptance_tokens'] for row in r['batches'])+r['synthesis_input_acceptance_tokens']
        self.assertEqual(total,r['input_acceptance_tokens_total'])
        expected=(total*50+r['output_acceptance_tokens_total']*250)/1e6
        self.assertEqual(r['planning_standard_credits_no_cache'],round(expected,8))
        self.assertGreaterEqual(r['proposed_credit_acceptance'],expected)
        self.assertGreaterEqual(r['synthesis_reference_reservation'],r['synthesis_fixture_actual_reference_tokens'])

    def test_schema_narrowing_does_not_modify_original_protocol_request(self):
        cat=Catalogue(snapshot());inner,wire=p.inspection(cat,['memory/a.md'],{})
        self.assertEqual(wire.schema['properties']['findings']['maxItems'],6)
        self.assertEqual(inner.schema['properties']['findings']['maxItems'],100)
        wire.payload['citation_limits'].clear()
        self.assertTrue(wire.payload['citation_limits'])

    def test_findings_count_token_or_reference_excess_is_rejected_without_clipping(self):
        cat=Catalogue(snapshot());inner,_=p.inspection(cat,['memory/a.md'],{})
        sid=cat.document_ids[0];ref={'source_id':sid,'anchor_id':'l1'}
        for findings in ([{'text':'claim','evidence':[ref]}]*7,
                         [{'text':'x'*1100,'evidence':[ref]}],
                         [{'text':'claim','evidence':[ref,{'source_id':sid,'anchor_id':'l2'},
                          {'source_id':cat.original_id,'anchor_id':'l1'}]}]):
            raw=response(cat,inner,['memory/a.md'],findings)
            with self.assertRaises(ValueError):p.validate_inspection(cat,inner,raw,ENC)

    def test_synthesis_keeps_every_finding_and_requires_complete_coverage(self):
        snap=snapshot();cat=Catalogue(snap);paths=[s.path for s in snap.sources]
        inner,_=p.inspection(cat,paths,{})
        findings=[{'text':'claim','evidence':[{'source_id':cat.document_ids[0],'anchor_id':'l1'}]}]
        raw=response(cat,inner,paths,findings)
        synth,wire,_=p.synthesis(cat,iter([(inner,raw)]),{},ENC,p.MAX_INPUT)
        self.assertEqual(synth.payload['data']['findings'],findings)
        self.assertEqual(len(synth.payload['data']['evidence_catalogue']),2)
        self.assertEqual(wire.payload['anchor_request']['data']['findings'],findings)
        small,_=p.inspection(cat,paths[:1],{})
        with self.assertRaisesRegex(AnchorError,'incomplete'):
            p.synthesis(cat,[(small,response(cat,small,paths[:1]))],{},ENC,p.MAX_INPUT)

    def test_late_synthesis_input_failure_never_drops_findings_to_fit(self):
        snap=snapshot();cat=Catalogue(snap);paths=[s.path for s in snap.sources]
        inner,_=p.inspection(cat,paths,{})
        with self.assertRaisesRegex(AnchorError,'synthesis_reservation'):
            p.synthesis(cat,[(inner,response(cat,inner,paths))],{},ENC,10)

    def test_schema_source_limit_cannot_silently_make_a_partial_plan(self):
        snap=snapshot([source(f'memory/{i}.md','# H') for i in range(protocol.MAX_SCHEMA_SOURCES)])
        with self.assertRaisesRegex(AnchorError,'source_count_unsupported'):self.measure(snap)

    def test_unsupported_synthesis_bound_is_reported_before_any_execution(self):
        with patch.object(p,'ROW_TOKENS',200000),self.assertRaisesRegex(AnchorError,'synthesis_bound'):
            self.measure()


class Preparation(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name).resolve();self.guide=self.root/'guide.txt';self.guide.write_text(ORIGINAL)
        self.enterContext(patch.object(p,'STATE',self.root/'state'))
        self.enterContext(patch.object(p,'ORIGINAL',self.guide))
        self.head=self.enterContext(patch.object(p.old,'_head',return_value='a'*40))
        self.enterContext(patch.object(p,'collect_revision',return_value=snapshot()))
        self.enterContext(patch.object(p,'_code',return_value={'fixture':'v1'}))
        self.measure=self.enterContext(patch.object(p.old,'_tokenizer',return_value={'blocked_anchor_ids':{},'state':'nonpaid_plan_ready_execution_adapter_required'}))
        self.runtime=self.enterContext(patch('app.recovery_guide_preflight.runtime_observation',return_value={'state':'unavailable','model_calls':0}))

    def test_preparation_is_immutable_private_plan_not_paid_approval(self):
        a=p.prepare();b=p.prepare();self.assertEqual(a,b);self.assertEqual(self.measure.call_count,1)
        self.assertFalse(a['paid_execution_available']);self.assertFalse(a['paid_execution_approval_requested'])
        self.assertTrue(a['frozen_inputs_current'])
        self.assertNotIn('approval_digest',a);self.assertFalse(hasattr(p,'run'))
        self.assertEqual((p.STATE/'plan.json').stat().st_mode & 0o777,0o600)
        self.assertNotIn('text',a['snapshot']['sources'][0]);self.assertNotIn('implementation',a)
        self.assertEqual({x.name for x in p.STATE.iterdir()},{'plan.json','job.lock'})

    def test_new_nonpaid_revision_preserves_previous_plan(self):
        a=p.prepare();b=p.prepare(refresh=True)
        self.assertNotEqual(a['plan_digest'],b['plan_digest'])
        self.assertEqual(json.loads((p.STATE/'plan.json').read_text())['plan_digest'],a['plan_digest'])
        self.assertTrue((p.STATE/'revisions'/(b['plan_digest']+'.json')).exists())

    def test_source_ref_drift_leaves_no_plan_and_does_not_retry(self):
        self.head.side_effect=['a'*40,'b'*40]
        with self.assertRaisesRegex(AnchorError,'inputs_changed'):p.prepare()
        self.assertFalse((p.STATE/'plan.json').exists());self.assertEqual(self.measure.call_count,1)

    def test_old_plan_read_is_explicitly_stale_after_guide_change(self):
        p.prepare();self.guide.write_text('changed');b=p.prepare()
        self.assertFalse(b['frozen_inputs_current']);self.assertFalse(b['paid_execution_available'])
        self.assertEqual(self.measure.call_count,1)

    def test_private_state_and_alias_guards(self):
        p.STATE.mkdir(mode=0o755)
        with self.assertRaisesRegex(AnchorError,'not_private'):p.prepare()
        p.STATE.chmod(0o700);(p.STATE/'plan.json').symlink_to(self.root/'elsewhere')
        with self.assertRaisesRegex(AnchorError,'artifact_alias'):p.prepare()


if __name__=='__main__':unittest.main()
