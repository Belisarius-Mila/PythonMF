from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from app.calendar_access_pilot import CalendarAccessPilot
from app.calendar_overview import CalendarOverview, CalendarOverviewError, CalendarSelectionConflict


class FakePilot(CalendarAccessPilot):
    def __init__(self, root, clock):
        super().__init__(root)
        self.clock = clock
        self.calls = []
        self.fail = False
        self.auth = 'full_access'
        self.rows = [{'id':'a','title':'Soukromý <kalendář>','source_title':'iCloud','writable':True},
                     {'id':'b','title':'Jen čtení','source_title':'Other','writable':False}]
        self.extra = {}

    def read_overview(self, ids, *, confirmed=False):
        assert confirmed
        self.calls.append(list(ids))
        if self.fail:
            raise subprocess.TimeoutExpired('synthetic', 1)
        now = self.clock()
        result = {'calendar_writes':False,'calendar_ids':ids,'start':now.isoformat(),
                  'end':(now+timedelta(days=30)).isoformat(),'observed_at':now.isoformat(),
                  'status':'overview_read','authorization':self.auth,'calendars':deepcopy(self.rows),
                  'events':[], 'missing_calendar_ids': sorted(set(ids)-{r['id'] for r in self.rows}),
                  'truncated':False}
        if 'a' in ids:
            result['events']=[{'calendar_id':'a','title':'<img src=x onerror=alert(1)>',
                'start':now.isoformat(),'end':(now+timedelta(hours=1)).isoformat(),
                'all_day':False,'timezone':'Europe/Prague','start_day':now.date().isoformat(),
                'end_day':now.date().isoformat(),'notes':'MUST NOT ESCAPE'}]
        result.update(self.extra)
        return result


class CalendarOverviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.now=datetime(2026,11,7,12,tzinfo=timezone.utc)
        self.root=Path(self.temp.name).resolve()/'private'
        self.pilot=FakePilot(self.root,lambda:self.now)
        self.store=CalendarOverview(self.pilot,clock=lambda:self.now)

    def select(self, ids=None, target='a', revision=0):
        return self.store.execute({'action':'save_selection','confirmed':True,'expected_revision':revision,
            'read_calendar_ids':ids if ids is not None else ['a'],'target_calendar_id':target})

    def ready(self):
        self.store.refresh(confirmed=True); self.select()
        return self.store.refresh(confirmed=True)

    def test_get_is_side_effect_free_and_default_selection_is_empty(self):
        state=self.store.snapshot()
        self.assertFalse(self.root.exists()); self.assertEqual(self.pilot.calls,[])
        self.assertEqual(state['read_calendar_ids'],[]); self.assertEqual(state['target_calendar_id'],'')
        self.assertFalse(state['ready'])

    def test_inventory_reads_no_events_until_exact_user_selection(self):
        state=self.store.refresh(confirmed=True)
        self.assertEqual(self.pilot.calls,[[]]); self.assertEqual(state['events'],[])
        self.assertTrue(state['can_select']); self.assertFalse(state['ready'])
        state=self.select(); self.assertFalse(state['ready'])
        state=self.store.refresh(confirmed=True)
        self.assertEqual(self.pilot.calls,[[],['a']]); self.assertTrue(state['ready'])
        self.assertEqual(len(state['events']),1)
        self.assertNotIn('MUST NOT ESCAPE',json.dumps(state))
        event=deepcopy(state['events'][0]); event['timezone']='GMT+0100'
        self.pilot.extra={'events':[event]}
        self.assertTrue(self.store.refresh(confirmed=True)['ready'])

    def test_selection_survives_restart_but_old_event_cache_does_not_match_new_selection(self):
        self.ready(); state=self.select(ids=['b'],target='',revision=1)
        restarted=CalendarOverview(self.pilot,clock=lambda:self.now).snapshot()
        self.assertEqual(restarted['read_calendar_ids'],['b']); self.assertEqual(restarted['events'],[])
        self.assertFalse(state['ready'])

    def test_stale_revision_cannot_overwrite_another_selection(self):
        self.ready()
        before=self.store.path.read_bytes()
        with self.assertRaises(CalendarSelectionConflict): self.select(ids=['b'])
        self.assertEqual(self.store.path.read_bytes(),before)

    def test_unknown_duplicate_and_nonwritable_targets_are_rejected(self):
        self.store.refresh(confirmed=True)
        for ids,target in [(['unknown'],'a'),(['a','a'],'a'),(['a'],'b'),(['a'],'unknown')]:
            with self.subTest(ids=ids,target=target),self.assertRaises(CalendarOverviewError):
                self.select(ids=ids,target=target)
        self.assertEqual(self.store.snapshot()['revision'],0)

    def test_empty_selection_is_explicit_and_never_reads_all(self):
        self.ready(); self.select(ids=[],target='',revision=1)
        state=self.store.refresh(confirmed=True)
        self.assertEqual(self.pilot.calls[-1],[]); self.assertFalse(state['ready']); self.assertEqual(state['events'],[])

    def test_stale_or_failed_inventory_cannot_authorize_a_selection(self):
        self.store.refresh(confirmed=True); self.now+=timedelta(minutes=16)
        with self.assertRaises(CalendarOverviewError): self.select()
        self.pilot.fail=True; self.store.refresh(confirmed=True)
        with self.assertRaises(CalendarOverviewError): self.select()

    def test_stale_snapshot_does_not_claim_current_coverage(self):
        self.ready(); self.now+=timedelta(minutes=16)
        state=self.store.snapshot()
        self.assertFalse(state['ready']); self.assertEqual(state['status'],'refresh_required')
        self.assertEqual(len(state['events']),1)

    def test_revoked_access_or_timeout_invalidate_previous_success(self):
        for mode in ('authorization','timeout'):
            with self.subTest(mode=mode):
                self.pilot.fail=False; self.pilot.auth='full_access'
                if self.store.snapshot()['revision']==0: self.ready()
                else: self.store.refresh(confirmed=True)
                if mode=='authorization': self.pilot.auth='denied'
                else: self.pilot.fail=True
                state=self.store.refresh(confirmed=True)
                self.assertFalse(state['ready']); self.assertFalse(state['can_select'])
                self.assertEqual(state['status'],'authorization_required' if mode=='authorization' else 'source_unavailable')

    def test_missing_selected_calendar_does_not_become_empty_available_period(self):
        self.ready(); self.pilot.rows=[self.pilot.rows[1]]
        self.pilot.extra={'events':[]}
        state=self.store.refresh(confirmed=True)
        self.assertEqual(state['status'],'missing_calendars'); self.assertFalse(state['ready'])
        self.assertEqual(state['missing_calendar_ids'],['a'])

    def test_truncated_or_malformed_native_result_is_not_ready(self):
        self.ready()
        cases=[{'truncated':True}, {'events':[None]}, {'calendar_ids':['b']},
               {'events':[{'start':'2026-11-01'}]}, {'start':'2026-01-01T00:00:00Z'},
               {'calendars':[None]}, {'calendar_writes':True}, {'missing_calendar_ids':['foreign']}]
        for patch in cases:
            with self.subTest(patch=patch):
                self.pilot.extra=patch; state=self.store.refresh(confirmed=True)
                self.assertFalse(state['ready'])

    def test_user_confirmation_and_exact_payload_are_required(self):
        for payload in ({'action':'refresh'}, {'action':'refresh','confirmed':False},
                        {'action':'refresh','confirmed':True,'unexpected':1}, {'action':'write','confirmed':True}):
            with self.assertRaises(CalendarOverviewError): self.store.execute(payload)
        self.assertEqual(self.pilot.calls,[])

    def test_private_storage_symlink_is_rejected(self):
        self.ready(); self.store.path.rename(self.root/'saved.json'); self.store.path.symlink_to(self.root/'saved.json')
        with self.assertRaises(Exception): self.store.snapshot()
