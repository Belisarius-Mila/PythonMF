"""Title generation shares the existing chat; image approval and recovery stay pinned."""
from __future__ import annotations

import base64
import copy
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.interior_ai import CodexInteriorDriver
from app.interior_atelier import AtelierConflict, AtelierError
from app.interior_brief import BRIEF_PROTOCOL, CHAT_RESPONSE_SCHEMA, NAMED_CHAT_RESPONSE_SCHEMA, parse_chat_answer
from app.interior_titles import TITLE_PROTOCOL, unique_proposal_title
from tests import test_interior_ai as fixtures
from tests import test_interior_brief as briefs


class InteriorTitleTests(unittest.TestCase):
    setUp = fixtures.InteriorAITests.setUp
    action = fixtures.InteriorAITests.action
    payload = fixtures.InteriorAITests.payload
    jobs = fixtures.InteriorAITests.jobs
    brief = briefs.InteriorBriefTests.brief
    request = briefs.InteriorBriefTests.request
    propose = briefs.InteriorBriefTests.propose
    image_request = briefs.InteriorBriefTests.image_request

    def save_title(self, title):
        draft=self.store.state(self.project,self.room)['draft'];rev=draft.pop('revision');draft['title']=title
        return self.action('save_draft',project_id=self.project,room_id=self.room,base_id='base',expected_revision=rev,draft=draft)

    def variants(self):return self.store.state(self.project,self.room)['room']['variants']

    def test_name_arrives_in_same_chat_and_new_media_share_that_title(self):
        self.propose(title='Koupelna – vana v rohu u okna')
        self.assertEqual(len(self.driver.calls),1)
        self.assertEqual(self.brief()['title'],'Koupelna – vana v rohu u okna')
        self.driver.with_image=True;payload=self.image_request();self.ai.start(payload);self.queue.pop()()
        job=self.driver.calls[-1][0];variant=self.variants()[self.jobs()[-1]['variant_id']]
        self.assertEqual(job['context']['proposal_title'],variant['title'])
        self.assertEqual(variant['title'],'Koupelna – vana v rohu u okna')
        source=self.store.state(self.project,self.room)['room']['sources'][variant['image_source_id']]
        self.assertEqual(source['title'],variant['title'])
        self.assertTrue(self.ai.start(payload)['replayed']);self.assertEqual(len(self.driver.calls),2)

    def test_manual_rename_keeps_brief_ready_and_invalidates_old_image_approval(self):
        self.propose();old=self.image_request();before=len(self.driver.calls)
        self.save_title('Koupelna – moje upravená vana')
        self.assertTrue(self.brief()['can_generate']);self.assertFalse(self.brief()['stale'])
        self.assertEqual(self.brief()['title'],'Koupelna – moje upravená vana')
        with self.assertRaises(AtelierConflict):self.ai.start(old)
        self.assertEqual(len(self.driver.calls),before)
        self.ai.start(self.image_request());self.assertEqual(len(self.queue),1)

    def test_manual_name_saved_while_architect_works_is_not_overwritten(self):
        self.driver.answer=json.dumps({'answer':'Návrh.', 'brief':{'title':'Koupelna – AI název','changes':'Nový obklad','preserve':'Dveře','unresolved':[]}})
        self.ai.start(self.request());self.save_title('Můj vlastní název');self.queue.pop()()
        self.assertEqual(self.brief()['title'],'Můj vlastní název')
        self.assertEqual(self.brief()['changes'],'Nový obklad');self.assertTrue(self.brief()['can_generate'])

    def test_duplicate_names_use_numbers_without_changing_existing_variants_or_media(self):
        self.propose(title='Koupelna – vana u okna');self.driver.with_image=True
        self.ai.start(self.image_request());self.queue.pop()()
        original=copy.deepcopy(self.store.state(self.project,self.room)['room'])
        self.assertEqual(self.brief()['title'],'Koupelna – vana u okna · 2')
        self.ai.start(self.image_request());self.queue.pop()()
        values=list(self.variants().values())
        self.assertCountEqual([v['title'] for v in values],['Koupelna – vana u okna','Koupelna – vana u okna · 2'])
        now=self.store.state(self.project,self.room)['room']
        for key,value in original['variants'].items():self.assertEqual(now['variants'][key],value)
        for key,value in original['sources'].items():self.assertEqual(now['sources'][key],value)
        self.assertEqual(self.brief()['title'],'Koupelna – vana u okna · 3')

    def test_multiple_outputs_in_one_turn_have_distinct_descriptive_titles(self):
        self.propose(title='Koupelna – světlý obklad')
        self.driver.outputs=[{'result':base64.b64encode(fixtures.image_bytes((640+i,420))).decode()} for i in range(2)]
        self.ai.start(self.image_request());self.queue.pop()()
        self.assertCountEqual([v['title'] for v in self.variants().values()],['Koupelna – světlý obklad','Koupelna – světlý obklad · 2'])
        self.assertEqual(len(self.driver.calls),2)

    def test_recovery_uses_original_approved_name_despite_later_draft_changes(self):
        self.propose(title='Koupelna – vana v rohu');self.driver.with_image=True
        payload=self.image_request()
        with patch.object(self.ai,'_complete_result',side_effect=OSError('Interrupted metadata write')):
            job=self.ai.start(payload)['request_id'];self.queue.pop()()
        self.assertEqual(self.jobs()[-1]['status'],'result_ready')
        self.save_title('Jiný budoucí název')
        self.ai.recover(self.project,self.room,job)
        self.assertEqual(next(iter(self.variants().values()))['title'],'Koupelna – vana v rohu')
        self.ai.recover(self.project,self.room,job)
        self.assertEqual(len(self.variants()),1);self.assertEqual(len(self.driver.calls),2)
        self.assertEqual(self.store.state(self.project,self.room)['draft']['title'],'Jiný budoucí název')

    def test_legacy_chat_result_remains_readable_and_name_only_edit_needs_no_new_chat(self):
        self.driver.answer=json.dumps({'answer':'Historický souhrn.', 'brief':{'changes':'Vyměň obklad','preserve':'Dveře','unresolved':[]}})
        self.ai.start(self.request())
        # A historical journal has neither naming metadata nor a title in its JSON.
        def legacy(state):
            room=state['projects'][self.project]['rooms'][self.room];job=next(iter(room['ai_requests'].values()))
            job.pop('title_protocol');from app.interior_brief import brief_basis
            job['brief_basis']=brief_basis(room,'base',self.store._draft(room,'base'))
            from app.work_repository import RepositoryMutation
            return RepositoryMutation(state)
        self.store.repository.transact(legacy);self.queue.pop()()
        self.assertTrue(self.brief()['can_generate']);self.save_title('Koupelna – vlastní název')
        self.assertTrue(self.brief()['can_generate']);self.assertEqual(len(self.driver.calls),1)

    def test_historical_image_journal_preserves_old_name_on_recovery(self):
        self.driver.with_image=True
        job=self.ai.start(self.payload(mode='image'))['request_id'];self.queue.pop()()
        title=next(iter(self.variants().values()))['title'];self.save_title('New name')
        self.ai.recover(self.project,self.room,job)
        self.assertEqual(next(iter(self.variants().values()))['title'],title)

    def test_named_schema_requires_title_at_every_object_and_old_schema_is_unchanged(self):
        def check(schema):
            if schema.get('type')=='object':
                self.assertFalse(schema['additionalProperties'])
                self.assertEqual(set(schema['required']),set(schema['properties']))
                for child in schema['properties'].values():check(child)
            if schema.get('type')=='array':check(schema['items'])
        check(NAMED_CHAT_RESPONSE_SCHEMA)
        self.assertNotIn('title',CHAT_RESPONSE_SCHEMA['properties']['brief']['properties'])
        plain={'answer':'A','brief':{'changes':'Obklad','preserve':'','unresolved':[]}}
        self.assertEqual(parse_chat_answer(json.dumps(plain))[1]['changes'],'Obklad')
        with self.assertRaises(AtelierError):parse_chat_answer(json.dumps(plain),named=True)
        for title in ('','x'*121,123):
            with self.subTest(title=title),self.assertRaises(AtelierError):
                parse_chat_answer(json.dumps({'answer':'A','brief':{**plain['brief'],'title':title}}),named=True)

    def test_named_driver_has_one_turn_with_title_schema_and_no_image_schema(self):
        selected=self.driver.selection();calls=[];threads=[]
        class Client:
            def __enter__(self):return self
            def __exit__(self,*_):return False
            def list_models(self):return []
            def read_effective_config(self,**_):return {'permissions':{},'mcp_servers':{}}
            def start_thread(self,**options):threads.append(options);return 'synthetic'
            def send_text(self,**options):calls.append(options);return SimpleNamespace(delivered=True,answer='{}',generated_images=[],as_dict=lambda:{})
        driver=CodexInteriorDriver(client_factory=Client);path=self.store.root/'input.png';path.write_bytes(fixtures.image_bytes())
        with patch('app.interior_ai.selected_role',return_value=selected),patch('app.interior_ai.agent_roles.assert_current',return_value=selected):
            driver({'id':'named','mode':'chat','brief_protocol':BRIEF_PROTOCOL,'title_protocol':TITLE_PROTOCOL,'selection':selected,'context':{}},[path],lambda _:None)
        self.assertEqual(len(calls),1);self.assertEqual(calls[0]['output_schema'],NAMED_CHAT_RESPONSE_SCHEMA)
        self.assertIn('hlavní schválená změna',threads[0]['developer_instructions'])

    def test_local_fallback_is_visible_and_long_collisions_stay_within_title_limit(self):
        self.save_title('')
        self.assertTrue(self.brief()['title'].startswith('Room A – '));self.assertTrue(self.brief()['can_generate'])
        title='K'*120;room={'variants':{'one':{'title':title},'two':{'title':title[:116]+' · 2'}}}
        value=unique_proposal_title(room,title)
        self.assertLessEqual(len(value),120);self.assertTrue(value.endswith(' · 3'))
        room={'variants':{'one':{'title':'Koupelna – vana'}}}
        self.assertEqual(unique_proposal_title(room,'KOUPelna – vana'),'KOUPelna – vana · 2')

    def test_two_prepared_jobs_resolve_name_collision_inside_completion_transaction(self):
        parents=[]
        for index in (1,2):
            self.save_title(f'Parent {index}')
            rev=self.store.state(self.project,self.room)['draft']['revision']
            parent=self.action('create_variant',project_id=self.project,room_id=self.room,base_id='base',expected_revision=rev)['variant_id']
            draft=self.store.state(self.project,self.room,parent)['draft'];draft.pop('revision');draft['title']='Koupelna – vana u okna'
            self.action('save_draft',project_id=self.project,room_id=self.room,base_id=parent,expected_revision=0,draft=draft)
            parents.append(parent)
        for parent in parents:
            brief=self.ai.status(self.project,self.room,parent)['brief']
            self.ai.start(self.payload(mode='image',base_id=parent,expected_revision=1,brief_protocol=BRIEF_PROTOCOL,brief_token=brief['token']))
        self.driver.with_image=True
        self.queue.pop(0)();self.queue.pop(0)()
        names=[v['title'] for v in self.variants().values() if v['kind']=='ai_proposal']
        self.assertCountEqual(names,['Koupelna – vana u okna','Koupelna – vana u okna · 2'])
        self.assertEqual(len(self.driver.calls),2)
