from dataclasses import asdict
import copy
import json
import unittest
from unittest.mock import patch

from app import recovery_guide_anchor_exact_worker as w
from app import recovery_guide_anchor_exact_plan as plan
from app import recovery_guide_anchor_protocol as protocol
from app.recovery_guide_anchors import AnchorError
from app.recovery_guide_sources import canonical_json, digest
from tests.test_recovery_guide_anchor_full_plan import snapshot, MODULE


class ExactWorker(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(plan.old.reference, 'tokenizer_identity', return_value={'fixture': True}))
        self.snap = snapshot()
        self.frozen = {'snapshot': asdict(self.snap), 'measurements': plan.measure(self.snap, MODULE)}
        self.req = w.perform('request', self.frozen, index=1, module=MODULE)
        wire = protocol.Request(self.req['wire'])
        self.raw = canonical_json({'request_id': wire.payload['request_id'],
            'covered': {s['source_id']: 1 for s in wire.payload['data']['sources']}, 'findings': []})
        self.history = [{**{k: self.req[k] for k in ('inner','wire','reference_index_sha256')}, 'raw': self.raw}]

    def call(self, action, **kwargs):
        return w.perform(action, self.frozen, module=MODULE, **kwargs)

    def test_audit_recalculates_all_numbers_and_exact_request_hashes(self):
        self.assertTrue(self.call('audit')['plan_recalculated'])
        r = self.call('validate', index=1, raw=self.raw)
        self.assertEqual(r['covered'], 2)
        self.assertEqual(r['response_sha256'], digest(self.raw))
        self.frozen['measurements']['proposed_credit_acceptance'] += 10
        with self.assertRaisesRegex(AnchorError, 'recalculation'):
            self.call('audit')

    def test_each_planned_identity_is_independently_required(self):
        row = self.frozen['measurements']['batches'][0]
        for key in ('schema_sha256', 'reference_index_sha256', 'wire_request_sha256'):
            original = row[key]; row[key] = '0'*64
            with self.subTest(key=key), self.assertRaisesRegex(AnchorError, 'request_changed'):
                self.call('request', index=1)
            row[key] = original

    def test_exact_synthesis_preserves_original_and_no_publishing(self):
        req = self.call('request', index=2, history=self.history)
        wire = protocol.Request(req['wire'])
        raw = canonical_json({'request_id': wire.payload['request_id'], 'paragraphs': [
            {'text': self.snap.original.text, 'status': 'unchanged', 'evidence': []}]})
        checked = self.call('validate', index=2, history=self.history, raw=raw)
        self.assertEqual(checked['candidate'], self.snap.original.text)
        self.assertEqual(checked['candidate_sha256'], digest(self.snap.original.text))
        self.assertFalse(checked['publication_authorized'])
        self.assertFalse(checked['application_inventory_complete'])

    def test_incomplete_history_and_changed_bindings_stop_before_synthesis(self):
        with self.assertRaisesRegex(AnchorError, 'history_incomplete'):
            self.call('request', index=2, history=[])
        for key in ('inner','wire','reference_index_sha256'):
            rows = copy.deepcopy(self.history); rows[0][key] = 'changed'
            with self.subTest(key=key), self.assertRaisesRegex(AnchorError, 'history_binding'):
                self.call('request', index=2, history=rows)

    def test_raw_replies_cannot_be_rebound_or_legacy_decoded_twice(self):
        for change in ({'request_id':'other'}, {'covered':{'d0001':'l1','d0002':'l1'}}):
            raw = json.loads(self.raw); raw.update(change)
            rows = copy.deepcopy(self.history); rows[0]['raw'] = canonical_json(raw)
            with self.subTest(change=change), self.assertRaises(AnchorError):
                self.call('request', index=2, history=rows)
        self.assertEqual(self.history[0]['raw'], self.raw)

    def test_invalid_phase_and_tokenizer_never_generate_extra_request(self):
        for index in (0,3,True,-1):
            with self.subTest(index=index), self.assertRaisesRegex(AnchorError, 'phase_outside'):
                self.call('request', index=index)
        self.frozen['measurements']['tokenizer'] = {'changed':True}
        with self.assertRaisesRegex(AnchorError, 'tokenizer_changed'):
            self.call('audit')

    def test_unexpected_worker_errors_are_redacted(self):
        with patch.object(w,'perform',side_effect=RuntimeError('SECRET_WORKER')):
            result = w.dispatch({'action':'audit','frozen':self.frozen})
        self.assertEqual(result, {'ok':False,'code':'RuntimeError'})


if __name__ == '__main__':
    unittest.main()
