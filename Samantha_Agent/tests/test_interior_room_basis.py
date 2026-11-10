"""Shared plan persistence, frozen AI input and complete source removal."""
from __future__ import annotations

import base64
import copy
import json
import unittest
import uuid

from app.interior_atelier import AtelierConflict, AtelierError, InteriorAtelier
from app.interior_cleanup import DELETE_CONFIRMATION
from app.interior_room_basis import room_basis
from tests import test_interior_ai as fixtures
from tests import test_interior_brief as briefs


class InteriorRoomBasisTests(unittest.TestCase):
    setUp = fixtures.InteriorAITests.setUp
    action = fixtures.InteriorAITests.action
    payload = fixtures.InteriorAITests.payload
    jobs = fixtures.InteriorAITests.jobs
    brief = briefs.InteriorBriefTests.brief
    request = briefs.InteriorBriefTests.request
    propose = briefs.InteriorBriefTests.propose
    image_request = briefs.InteriorBriefTests.image_request

    def plan(self, n=0, room=None):
        return self.action('add_source', project_id=self.project, room_id=room or self.room, title='Floor plan', kind='plan',
            data=base64.b64encode(fixtures.image_bytes((610+n,420))).decode())['asset_id']

    def save_basis(self, plan='', measurements='300 x 220 cm; výška 250 cm.', revision=0, **extra):
        return self.action('save_room_basis', project_id=self.project, room_id=self.room,
            expected_basis_revision=revision, plan_source_id=plan, measurements=measurements, **extra)

    def test_optional_legacy_basis_reads_without_migration(self):
        before=self.store.path.read_bytes()
        self.assertEqual(self.store.state(self.project,self.room)['room']['room_basis'],
                         {'plan_source_id':'','measurements':'','revision':0})
        self.assertEqual(before,self.store.path.read_bytes())
        self.assertTrue(self.brief()['can_generate'])

    def test_one_basis_is_shared_by_variants_and_survives_restart_without_touching_drafts(self):
        variant=self.action('create_variant',project_id=self.project,room_id=self.room,base_id='base',expected_revision=1)['variant_id']
        before=copy.deepcopy(self.store.state(self.project,self.room)['draft'])
        plan=self.plan();self.save_basis(plan)
        restarted=InteriorAtelier(self.store.root)
        a=restarted.state(self.project,self.room)['room']['room_basis']
        b=restarted.state(self.project,self.room,variant)['room']['room_basis']
        self.assertEqual(a,b);self.assertEqual(a['plan_source_id'],plan)
        self.assertEqual(a['revision'],1);self.assertEqual(before,restarted.state(self.project,self.room)['draft'])

    def test_exact_replay_and_stale_or_foreign_input(self):
        plan=self.plan()
        payload={'action':'save_room_basis','request_id':uuid.uuid4().hex,'project_id':self.project,'room_id':self.room,
                 'expected_basis_revision':0,'plan_source_id':plan,'measurements':'300 cm'}
        self.store.execute(payload)
        self.assertTrue(InteriorAtelier(self.store.root).execute(payload)['replayed'])
        with self.assertRaises(AtelierConflict):self.save_basis(plan,revision=0)
        with self.assertRaises(AtelierConflict):self.store.execute({**payload,'measurements':'500 cm'})
        other=self.action('create_room',project_id=self.project,title='Other')['room_id']
        foreign=self.plan(1,other)
        for invalid in (foreign,self.asset,[],True):
            with self.subTest(value=invalid),self.assertRaises(AtelierError):self.save_basis(invalid,revision=1)
        with self.assertRaises(AtelierError):self.save_basis(plan,measurements='x'*6001,revision=1)
        with self.assertRaises(AtelierConflict):self.save_basis(plan,revision=True)
        self.assertEqual(self.store.state(self.project,other)['room']['room_basis']['revision'],0)

    def test_replace_and_unset_never_remove_sources_or_bytes(self):
        first,second=self.plan(),self.plan(1);self.save_basis(first)
        before={p.name:p.read_bytes() for p in (self.store.root/'objects').iterdir()}
        self.save_basis(second,revision=1)
        self.save_basis('',revision=2)
        state=self.store.state(self.project,self.room)
        self.assertIn(first,state['room']['sources']);self.assertIn(second,state['room']['sources'])
        self.assertEqual(before,{p.name:p.read_bytes() for p in (self.store.root/'objects').iterdir()})
        self.assertEqual(state['room']['room_basis']['revision'],3)
        self.assertEqual(self.save_basis('',revision=3)['basis_revision'],3,'An identical save is not a new geometry revision')

    def test_plan_and_measurements_automatically_reach_chat_without_variant_selection(self):
        plan=self.plan();self.save_basis(plan)
        self.propose()
        job,paths=self.driver.calls[-1]
        self.assertEqual(job['context']['room_basis']['measurements'],'300 x 220 cm; výška 250 cm.')
        self.assertEqual(job['context']['room_basis']['plan_image_number'],2)
        self.assertTrue(job['context']['images'][1]['room_plan'])
        self.assertTrue(job['context']['images'][0]['working_image'])
        self.assertEqual(len(paths),2)
        self.assertNotIn(plan,job['context']['draft']['source_ids'])
        self.assertEqual(self.brief()['source_count'],2)

    def test_image_snapshot_uses_same_basis_without_history_and_deduplicates_selected_plan(self):
        plan=self.plan();self.save_basis(plan)
        draft={**self.draft,'source_ids':[self.asset,plan]}
        self.action('save_draft',project_id=self.project,room_id=self.room,base_id='base',expected_revision=1,draft=draft)
        self.driver.with_image=True
        self.ai.start(self.image_request());self.queue.pop()()
        job,paths=self.driver.calls[-1]
        self.assertEqual(len(paths),2)
        self.assertEqual(job['context']['room_basis']['plan_source_id'],plan)
        self.assertEqual(job['context']['history'],[]);self.assertEqual(job['context']['notes'],[])

    def test_room_basis_invalidates_prepared_summary_and_old_approval(self):
        self.propose()
        old=self.image_request()
        self.save_basis(self.plan())
        self.assertTrue(self.brief()['stale']);self.assertFalse(self.brief()['can_generate'])
        with self.assertRaises(AtelierConflict):self.ai.start(old)
        self.propose()
        self.assertTrue(self.brief()['can_generate'])
        self.save_basis(self.brief()['room_basis']['plan_source_id'],measurements='Jiná míra 310 cm',revision=1)
        self.assertTrue(self.brief()['stale'])

    def test_an_active_request_blocks_changing_basis_and_plan_deletion_for_entire_room(self):
        plan=self.plan();self.save_basis(plan)
        self.ai.start(self.request())
        with self.assertRaises(AtelierConflict):self.save_basis('',revision=1)
        with self.assertRaises(AtelierConflict):self.store.deletion_preview(self.project,self.room,plan)
        self.assertEqual(len(self.queue),1);self.assertEqual(self.driver.calls,[])

    def test_automatic_plan_counts_towards_image_limit_before_any_paid_turn(self):
        self.save_basis(self.plan())
        ids=[self.asset]+[self.action('add_source',project_id=self.project,room_id=self.room,title='Reference',kind='inspiration',
            data=base64.b64encode(fixtures.image_bytes((650+i,440))).decode())['asset_id'] for i in range(5)]
        self.action('save_draft',project_id=self.project,room_id=self.room,base_id='base',expected_revision=1,draft={**self.draft,'source_ids':ids})
        self.assertEqual(self.brief()['source_count'],7);self.assertFalse(self.brief()['can_generate'])
        with self.assertRaises(AtelierError):self.ai.start(self.request())
        self.assertEqual(self.driver.calls,[]);self.assertEqual(self.queue,[])

    def test_confirmed_plan_removal_detaches_room_and_cleans_automatic_snapshots(self):
        plan=self.plan();self.save_basis(plan);self.propose()
        job_id=self.jobs()[-1]['id'];folder=self.store.root/'ai_inputs'/job_id
        self.assertTrue(folder.exists())
        preview=self.store.deletion_preview(self.project,self.room,plan)
        self.assertTrue(preview['room_plan'])
        self.action('delete_source',project_id=self.project,room_id=self.room,asset_id=plan,plan_token=preview['plan_token'],confirmation=DELETE_CONFIRMATION)
        basis=self.store.state(self.project,self.room)['room']['room_basis']
        self.assertEqual(basis['plan_source_id'],'');self.assertEqual(basis['revision'],2)
        self.assertEqual(basis['measurements'],'300 x 220 cm; výška 250 cm.')
        self.assertFalse(folder.exists());self.assertTrue(self.ai.recover(self.project,self.room,job_id)['source_deleted'])
        self.assertTrue(self.brief()['stale']);self.assertEqual(len(self.driver.calls),1)

    def test_other_room_plan_cannot_leak_into_chat(self):
        other=self.action('create_room',project_id=self.project,title='Other')['room_id']
        plan=self.plan(1,other)
        self.action('save_room_basis',project_id=self.project,room_id=other,expected_basis_revision=0,
                    plan_source_id=plan,measurements='FOREIGN_ROOM_PRIVATE_DIMENSION')
        self.propose()
        self.assertNotIn('FOREIGN_ROOM',str(self.driver.calls[-1][0]['context']))
        self.assertEqual(self.driver.calls[-1][0]['image_count'],1)
