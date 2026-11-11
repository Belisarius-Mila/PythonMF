"""Approval contract without a paid turn or real private media."""
from __future__ import annotations

import copy
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.interior_ai import CodexInteriorDriver, InteriorAI
from app.interior_atelier import AtelierConflict, AtelierError
from app.interior_brief import BRIEF_PROTOCOL, CHAT_RESPONSE_SCHEMA, parse_chat_answer
from tests import test_interior_ai as fixtures


class InteriorBriefTests(unittest.TestCase):
    setUp = fixtures.InteriorAITests.setUp
    action = fixtures.InteriorAITests.action
    payload = fixtures.InteriorAITests.payload
    jobs = fixtures.InteriorAITests.jobs

    def brief(self):
        return self.ai.status(self.project, self.room)['brief']

    def request(self, **values):
        return self.payload(expected_revision=self.brief()['revision'], brief_protocol=BRIEF_PROTOCOL, **values)

    def propose(self, **values):
        brief = {'title':'Koupelna – světlý obklad', 'changes': 'Vyměň obklad', 'preserve': 'Dveře', 'unresolved': ['Přesun vany zatím nerozhodnutý.'], **values}
        self.driver.answer = json.dumps({'answer': 'Připravil jsem souhrn ke kontrole.', 'brief': brief})
        payload = self.request()
        self.ai.start(payload)
        self.queue.pop()()
        return brief

    def image_request(self, **values):
        return self.request(mode='image', brief_token=self.brief()['token'], **values)

    def test_chat_proposes_cumulative_brief_and_image_approves_exact_snapshot(self):
        self.action('add_note', project_id=self.project, room_id=self.room, base_id='base', text='Starší úvaha o bourání.')
        proposed = self.propose()
        view = self.brief()
        self.assertEqual({key: view[key] for key in proposed}, proposed)
        self.assertTrue(view['can_generate'])
        self.assertEqual(view['revision'], 2)
        self.assertEqual(self.driver.calls[0][0]['context']['current_brief']['preserve'], 'Dveře')
        self.driver.with_image = True
        payload = self.image_request(message='UNTRUSTED old contradictory message')
        self.ai.start(payload)
        self.queue.pop()()
        job = self.driver.calls[-1][0]
        self.assertEqual(job['context']['approved_brief'], {k:v for k,v in proposed.items() if k!='title'})
        self.assertEqual(job['context']['question'], proposed['changes'])
        self.assertEqual(job['context']['history'], [])
        self.assertEqual(job['context']['notes'], [])
        self.assertNotIn('Starší úvaha', str(job['context']))
        self.assertNotIn('UNTRUSTED', str(job['context']))
        variant = self.store.state(self.project, self.room)['room']['variants'][self.jobs()[-1]['variant_id']]
        self.assertEqual(variant['brief_unresolved'], proposed['unresolved'])
        self.assertEqual(variant['prompt'], proposed['changes'])
        self.assertTrue(self.ai.start(payload)['replayed'])
        self.assertEqual(len(self.driver.calls), 2)

    def test_changed_notes_reject_old_approval_before_preparing_any_turn(self):
        self.propose()
        old = self.image_request()
        self.action('add_note', project_id=self.project, room_id=self.room, base_id='base', text='Nová poznámka.')
        with self.assertRaises(AtelierConflict): self.ai.start(old)
        self.assertTrue(self.brief()['stale'])
        with self.assertRaises(AtelierError): self.ai.start(self.image_request())
        self.assertEqual(len(self.driver.calls), 1)
        self.assertEqual(self.queue, [])

    def test_working_image_drawing_and_revision_are_bound_to_approval(self):
        self.propose()
        old = self.image_request()
        draft = self.store.state(self.project, self.room)['draft']
        draft.pop('revision')
        draft['annotations'] = [[[0.1, 0.1], [0.2, 0.2]]]
        self.action('save_draft', project_id=self.project, room_id=self.room, base_id='base', expected_revision=2, draft=draft)
        with self.assertRaises(AtelierConflict): self.ai.start(old)
        self.assertFalse(self.brief()['can_generate'])
        self.assertEqual(self.brief()['drawing_count'], 1)

    def test_identical_save_keeps_proposal_but_invalidates_old_token(self):
        self.propose()
        old = self.image_request()
        draft = self.store.state(self.project, self.room)['draft']
        draft.pop('revision')
        self.action('save_draft', project_id=self.project, room_id=self.room, base_id='base', expected_revision=2, draft=draft)
        self.assertTrue(self.brief()['can_generate'])
        self.assertNotEqual(self.brief()['token'], old['brief_token'])
        with self.assertRaises(AtelierConflict): self.ai.start(old)
        self.ai.start(self.image_request())
        self.assertEqual(len(self.queue), 1)

    def test_late_chat_cannot_overwrite_a_newer_saved_draft(self):
        self.driver.answer = json.dumps({'answer':'Návrh.', 'brief':{'title':'Koupelna – změna obkladu','changes':'AI změna','preserve':'Dveře','unresolved':[]}})
        self.ai.start(self.request())
        draft = copy.deepcopy(self.draft); draft.update(title='Novější místní práce',prompt='Novější vlastní zadání')
        self.action('save_draft', project_id=self.project, room_id=self.room, base_id='base', expected_revision=1, draft=draft)
        self.queue.pop()()
        actual = self.store.state(self.project, self.room)['draft']
        self.assertEqual(actual['title'], 'Novější místní práce')
        self.assertEqual(actual['prompt'], 'Novější vlastní zadání')
        self.assertTrue(self.brief()['stale'])
        self.assertFalse(self.brief()['can_generate'])

    def test_pending_and_unknown_new_question_block_previous_brief_without_retry(self):
        self.propose()
        self.driver.fail = True
        payload = self.request(message='Co kdybychom přesunuli vanu?')
        self.ai.start(payload)
        self.assertFalse(self.brief()['can_generate'])
        self.queue.pop()()
        self.assertEqual(self.jobs()[-1]['status'], 'delivery_unknown')
        self.assertFalse(self.brief()['can_generate'])
        self.assertTrue(self.ai.start(payload)['replayed'])
        self.assertEqual(len(self.driver.calls), 2)
        self.assertEqual(self.queue, [])

    def test_invalid_structured_answer_preserves_saved_draft_and_blocks_image(self):
        self.driver.answer = 'Unstructured response'
        self.ai.start(self.request()); self.queue.pop()()
        self.assertTrue(self.jobs()[-1]['brief_error'])
        self.assertEqual(self.store.state(self.project, self.room)['draft']['prompt'], self.draft['prompt'])
        self.assertFalse(self.brief()['can_generate'])
        self.assertEqual(len(self.driver.calls), 1)

    def test_later_same_timestamp_chat_wins_and_fixed_change_is_visible(self):
        self.propose()
        self.propose(changes='Ponech obklad', preserve='Dveře i okno', unresolved=[])
        self.assertEqual(self.brief()['changes'], 'Ponech obklad')
        self.assertEqual(self.brief()['unresolved'], [])
        self.assertTrue(self.brief()['fixed_changed'])

    def test_human_variant_keeps_unresolved_questions(self):
        expected = self.propose()
        result = self.action('create_variant', project_id=self.project, room_id=self.room, base_id='base', expected_revision=2)
        variant = self.store.state(self.project, self.room)['room']['variants'][result['variant_id']]
        self.assertEqual(variant['brief_unresolved'], expected['unresolved'])

    def test_legacy_snapshot_remains_reviewable_but_new_legacy_requests_are_rejected_in_production(self):
        self.assertTrue(self.brief()['can_generate'])
        service = InteriorAI(self.store, driver=self.driver, launcher=self.queue.append)
        with self.assertRaises(AtelierError): service.start(self.payload())
        legacy = self.payload(); self.ai.start(legacy)
        self.assertTrue(service.start(legacy)['replayed'])
        self.assertEqual(len(self.queue), 1)

    def test_schema_rejects_extra_keys_and_invalid_unresolved(self):
        for value in ('{"answer":"ok","brief":{}}', '{"answer":"ok","brief":{"changes":"x","preserve":"","unresolved":"x"}}'):
            with self.assertRaises(AtelierError): parse_chat_answer(value)
        self.assertFalse(CHAT_RESPONSE_SCHEMA['additionalProperties'])

    def test_driver_sends_structured_chat_and_keeps_image_tool_on_explicit_image_turn_only(self):
        calls, threads = [], []
        selected = self.driver.selection()
        class Client:
            def __enter__(self): return self
            def __exit__(self, *_): return False
            def list_models(self): return []
            def read_effective_config(self, **_): return {"mcp_servers": {}, "permissions": {}}
            def start_thread(self, **options): threads.append(options); return "synthetic"
            def send_text(self, **options):
                calls.append(options)
                return SimpleNamespace(delivered=True, answer='{}', generated_images=[], as_dict=lambda: {})
        driver = CodexInteriorDriver(client_factory=Client)
        source = self.store.root / 'synthetic.png'; source.write_bytes(fixtures.image_bytes())
        with patch('app.interior_ai.selected_role', return_value=selected), patch('app.interior_ai.agent_roles.assert_current', return_value=selected):
            for mode in ('chat', 'image'):
                driver({'id':'test', 'mode':mode, 'brief_protocol':BRIEF_PROTOCOL,
                        'selection':selected, 'context':{'mode':mode}}, [source], lambda _:None)
        self.assertEqual(calls[0]['output_schema'], CHAT_RESPONSE_SCHEMA)
        self.assertNotIn('output_schema', calls[1])
        self.assertFalse(threads[0]['config_overrides']['features']['image_generation'])
        self.assertTrue(threads[1]['config_overrides']['features']['image_generation'])
        self.assertIn('Pouhý dotaz', threads[0]['developer_instructions'])
        self.assertIn('approved_brief', threads[1]['developer_instructions'])
        self.assertEqual(len(calls), 2)
