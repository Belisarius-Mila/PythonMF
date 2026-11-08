from dataclasses import asdict,replace
import json
import unittest
from unittest.mock import patch

from app import recovery_guide_anchor_full_worker as w
from app import recovery_guide_anchor_full_plan as plan
from app import recovery_guide_anchor_protocol as protocol
from app.recovery_guide_sources import canonical_json,digest,Source
from app.recovery_guide_anchors import Catalogue,AnchorError
from app.recovery_guide_quality import QualityError
from tests.test_recovery_guide_anchor_full_plan import snapshot,ENC,MODULE,response


class Worker(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(plan.reference,'tokenizer_identity',return_value={'fixture':True}))
        self.snap=snapshot();self.freeze(self.snap)

    def freeze(self,snap):
        self.snap=snap;self.cat=Catalogue(snap)
        self.frozen={'snapshot':asdict(snap),'measurements':plan.measure(snap,MODULE)}
        self.request=w.perform('request',self.frozen,index=1,module=MODULE)
        self.inner=protocol.Request(self.request['inner'])
        paths=self.frozen['measurements']['batches'][0]['source_paths']
        self.raw=response(self.cat,self.inner,paths)
        self.history=[{'inner':self.inner.envelope_json,'raw':self.raw}]

    def test_exact_recalculation_and_generated_requests(self):
        self.assertTrue(w.perform('audit',self.frozen,module=MODULE)['plan_recalculated'])
        row=self.frozen['measurements']['batches'][0]
        self.assertEqual(protocol.Request(self.request['wire']).sha256,row['wire_request_sha256'])
        checked=w.perform('validate',self.frozen,index=1,raw=self.raw,module=MODULE)
        self.assertEqual(checked['covered'],2);self.assertEqual(checked['response_sha256'],digest(self.raw))

    def test_tampered_planning_numbers_are_not_execution_approval(self):
        self.frozen['measurements']['proposed_credit_acceptance']+=10
        with self.assertRaisesRegex(AnchorError,'recalculation'):
            w.perform('audit',self.frozen,module=MODULE)

    def test_request_hash_and_tokenizer_identity_are_strict(self):
        self.frozen['measurements']['batches'][0]['wire_request_sha256']='0'*64
        with self.assertRaisesRegex(AnchorError,'request_changed'):
            w.perform('request',self.frozen,index=1,module=MODULE)
        self.frozen['measurements']['tokenizer']={'changed':True}
        with self.assertRaisesRegex(AnchorError,'tokenizer_changed'):
            w.perform('audit',self.frozen,module=MODULE)

    def test_complete_synthesis_is_generated_from_exact_accepted_history(self):
        req=w.perform('request',self.frozen,index=2,history=self.history,module=MODULE)
        inner=protocol.Request(req['inner'])
        answer=canonical_json({'request_id':inner.payload['request_id'],'paragraphs':[
            {'text':self.snap.original.text,'status':'unchanged','evidence':[]}]})
        result=w.perform('validate',self.frozen,index=2,history=self.history,raw=answer,module=MODULE)
        self.assertEqual(result['candidate_sha256'],digest(self.snap.original.text))
        self.assertFalse(result['publication_authorized']);self.assertFalse(result['application_inventory_complete'])

    def test_missing_or_changed_history_is_never_summarized_or_dropped(self):
        with self.assertRaisesRegex(AnchorError,'history_incomplete'):
            w.perform('request',self.frozen,index=2,history=[],module=MODULE)
        self.history[0]['inner']='changed'
        with self.assertRaisesRegex(AnchorError,'history_binding_changed'):
            w.perform('request',self.frozen,index=2,history=self.history,module=MODULE)

    def test_new_command_with_exact_evidence_still_requires_registered_allowlist(self):
        first=self.snap.sources[0];text=first.text+'git status\n'
        self.freeze(replace(self.snap,sources=(replace(first,text=text,sha256=digest(text)),self.snap.sources[1])))
        data=json.loads(self.raw);sid=self.cat.document_ids[0]
        data['findings']=[{'text':'Příkaz v dokumentaci.','evidence':[{'source_id':sid,'anchor_id':'l3'}]}]
        self.history[0]['raw']=canonical_json(data)
        req=w.perform('request',self.frozen,index=2,history=self.history,module=MODULE)
        inner=protocol.Request(req['inner'])
        answer=canonical_json({'request_id':inner.payload['request_id'],'paragraphs':[
            {'text':self.snap.original.text,'status':'unchanged','evidence':[]},
            {'text':'git status','status':'unverified','evidence':data['findings'][0]['evidence']}]})
        with self.assertRaisesRegex(QualityError,'unregistered_command'):
            w.perform('validate',self.frozen,index=2,history=self.history,raw=answer,module=MODULE)

    def test_final_original_reference_cannot_bypass_bounded_citation_policy(self):
        text=self.snap.original.text+'\n'+'x'*1000+'\n'
        self.freeze(replace(self.snap,original=replace(self.snap.original,text=text,sha256=digest(text))))
        req=w.perform('request',self.frozen,index=2,history=self.history,module=MODULE)
        inner=protocol.Request(req['inner']);aid=self.frozen['measurements']['blocked_anchor_ids'][self.cat.original_id][-1]
        raw=canonical_json({'request_id':inner.payload['request_id'],'paragraphs':[
            {'text':text,'status':'unchanged','evidence':[]},
            {'text':'Neověřená poznámka.','status':'unverified',
             'evidence':[{'source_id':self.cat.original_id,'anchor_id':aid}]}]})
        with self.assertRaisesRegex(AnchorError,'final_citation'):
            w.perform('validate',self.frozen,index=2,history=self.history,raw=raw,module=MODULE)

    def test_invalid_phase_indices_are_not_an_extra_request(self):
        for index in (0,3,True,-1):
            with self.subTest(index=index),self.assertRaisesRegex(AnchorError,'phase_outside'):
                w.perform('request',self.frozen,index=index,module=MODULE)

    def test_dispatch_does_not_echo_unexpected_error_or_source_content(self):
        with patch.object(w,'perform',side_effect=RuntimeError('SECRET_WORKER')):
            result=w.dispatch({'action':'audit','frozen':self.frozen})
        self.assertEqual(result,{'ok':False,'code':'RuntimeError'})
        self.assertNotIn('SECRET_WORKER',canonical_json(result))


if __name__=='__main__':unittest.main()
