from copy import deepcopy
from datetime import datetime,timedelta,timezone
from pathlib import Path
import json
import tempfile
import unittest
from app.calendar_overview import CalendarOverview
from app.calendar_agenda import CalendarAgenda, WrittenKinds, event_key
from tests.test_calendar_overview import FakePilot


class CalendarAgendaTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.now=datetime(2026,11,7,12,tzinfo=timezone.utc)
        self.pilot=FakePilot(self.root/'calendar',lambda:self.now)
        self.overview=CalendarOverview(self.pilot,clock=lambda:self.now);self.callbacks=[];self.hints={}
        self.agenda=CalendarAgenda(self.overview,launcher=self.callbacks.append,written_kinds=lambda:(self.hints,False))

    def prepare(self):
        self.overview.refresh(confirmed=True)
        self.overview.save_selection({'action':'save_selection','confirmed':True,'expected_revision':0,'read_calendar_ids':['a'],'target_calendar_id':'a'})
        self.overview.refresh(confirmed=True)
        return self.agenda.snapshot()

    def events(self,rows):
        data=self.overview._load();data['events']=rows;self.pilot._write(self.overview.path,data)

    def event(self,**changes):
        return {'calendar_id':'a','title':'Schůzka','start':(self.now+timedelta(days=1)).isoformat(),
                'end':(self.now+timedelta(days=1,hours=1)).isoformat(),'all_day':False,'timezone':'Europe/Prague',
                'start_day':'2026-11-08','end_day':'2026-11-08',**changes}

    def label(self,row,kind='task_deadline',**changes):
        view=self.agenda.snapshot()
        return self.agenda.execute({'action':'set_kind','key':row['key'],'kind':kind,'expected_selection_revision':view['selection_revision'],
            'expected_labels_revision':view['labels_revision'],'confirmed':True,**changes})

    def test_status_never_initializes_storage_or_queries_native_calendar(self):
        before=list(self.pilot.calls);v=self.agenda.snapshot()
        self.assertEqual(v['selected_count'],0);self.assertFalse(self.pilot.root.exists());self.assertEqual(self.pilot.calls,before)
        self.agenda.request_refresh();self.assertEqual(self.callbacks,[])

    def test_background_request_returns_cache_and_reuses_one_cross_instance_claim(self):
        self.prepare();calls=len(self.pilot.calls)
        v=self.agenda.request_refresh();self.assertTrue(v['refreshing']);self.assertEqual(len(self.pilot.calls),calls)
        other=CalendarAgenda(self.overview,launcher=self.callbacks.append,written_kinds=lambda:({},False))
        self.agenda.request_refresh();other.request_refresh();self.assertEqual(len(self.callbacks),1)
        self.callbacks.pop()();self.assertTrue(self.agenda.snapshot()['fresh']);self.assertFalse(self.agenda.snapshot()['refreshing'])
        other.request_refresh();self.assertEqual(self.callbacks,[])

    def test_refresh_after_cooldown_and_changed_selection_are_allowed(self):
        self.prepare();self.agenda.request_refresh();self.callbacks.pop()()
        self.now+=timedelta(seconds=61);self.agenda.request_refresh();self.assertEqual(len(self.callbacks),1);self.callbacks.pop()()
        d=self.overview._load();d['revision']+=1;self.pilot._write(self.overview.path,d)
        self.agenda.request_refresh();self.assertEqual(len(self.callbacks),1)

    def test_failed_native_read_preserves_old_items_but_marks_them_unverified(self):
        old=self.prepare()['meetings'];self.pilot.fail=True
        self.agenda.request_refresh();self.callbacks.pop()()
        v=self.agenda.snapshot();self.assertFalse(v['fresh']);self.assertEqual(v['status'],'source_unavailable')
        self.assertEqual([e['key'] for e in v['meetings']],[e['key'] for e in old]);self.assertFalse(v['meetings'][0]['can_classify'])
        self.agenda.request_refresh();self.assertEqual(self.callbacks,[])

    def test_exception_before_overview_updates_also_invalidates_fresh_banner(self):
        self.prepare()
        self.overview.refresh=lambda **kwargs:(_ for _ in ()).throw(RuntimeError())
        self.agenda.request_refresh();self.callbacks.pop()()
        self.assertFalse(self.agenda.snapshot()['fresh'])

    def test_thirty_day_window_excludes_finished_and_far_events_keeps_ongoing(self):
        self.prepare();current=self.event(start=(self.now-timedelta(hours=1)).isoformat(),end=(self.now+timedelta(hours=1)).isoformat())
        finished=self.event(title='Hotovo',end=self.now.isoformat());far=self.event(title='Později',start=(self.now+timedelta(days=30)).isoformat(),end=(self.now+timedelta(days=31)).isoformat())
        self.events([far,finished,current]);v=self.agenda.snapshot();self.assertEqual(len(v['meetings']),1);self.assertEqual(v['meetings'][0]['title'],'Schůzka')

    def test_known_types_and_user_override_split_lists_without_calendar_writes(self):
        self.prepare();event=self.event();self.events([event]);self.hints[event_key(event)]='task_deadline'
        v=self.agenda.snapshot();self.assertEqual(len(v['deadlines']),1);self.assertEqual(v['deadlines'][0]['type_source'],'samantha')
        before=self.overview.path.read_bytes();calls=len(self.pilot.calls)
        v=self.label(v['deadlines'][0],'meeting');self.assertEqual(v['meetings'][0]['type_source'],'display')
        self.assertFalse(v['calendar_writes']);self.assertEqual(self.overview.path.read_bytes(),before);self.assertEqual(len(self.pilot.calls),calls)
        self.assertEqual(len(self.label(v['meetings'][0],'auto')['deadlines']),1)

    def test_unknown_one_minute_event_is_not_guessed_to_be_deadline(self):
        self.prepare();self.events([self.event(end=(self.now+timedelta(days=1,minutes=1)).isoformat())])
        v=self.agenda.snapshot();self.assertEqual(v['deadlines'],[]);self.assertEqual(v['meetings'][0]['kind'],'event')

    def test_changed_title_or_time_does_not_inherit_annotation(self):
        v=self.prepare();self.label(v['meetings'][0]);old=self.overview._load()['events'][0]
        self.events([{**old,'title':'Změněný obsah'}]);v=self.agenda.snapshot();self.assertEqual(v['deadlines'],[])

    def test_duplicate_content_is_never_automatically_or_individually_classified(self):
        self.prepare();e=self.event();self.hints[event_key(e)]='task_deadline';self.events([e,deepcopy(e)])
        v=self.agenda.snapshot();self.assertEqual(v['deadlines'],[]);self.assertFalse(v['meetings'][0]['can_classify'])
        with self.assertRaises(ValueError):self.label(v['meetings'][0])

    def test_wrong_revision_selection_key_or_consent_cannot_change_labels(self):
        v=self.prepare();row=v['meetings'][0]
        for changes in ({'confirmed':False},{'expected_labels_revision':99},{'expected_selection_revision':99},{'key':'0'*64}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):self.label(row,**changes)
        self.assertFalse(self.agenda.labels_path.exists())

    def test_stale_and_missing_selection_do_not_display_false_empty_success(self):
        self.prepare();self.now+=timedelta(minutes=16)
        self.assertFalse(self.agenda.snapshot()['fresh'])
        with self.assertRaises(ValueError):self.label(self.agenda.snapshot()['meetings'][0])
        d=self.overview._load();d.update(revision=2,read_calendar_ids=['b']);self.pilot._write(self.overview.path,d)
        self.assertEqual(self.agenda.snapshot()['meetings'],[])

    def test_annotations_survive_restart_and_do_not_affect_native_selection(self):
        view=self.prepare();self.label(view['meetings'][0])
        other=CalendarAgenda(self.overview,written_kinds=lambda:({},False))
        self.assertEqual(len(other.snapshot()['deadlines']),1);self.assertEqual(self.overview.snapshot()['read_calendar_ids'],['a'])

    def test_corrupt_type_store_warns_and_never_overwrites_it(self):
        self.prepare();self.agenda.labels_path.write_text('broken')
        v=self.agenda.snapshot();self.assertTrue(v['classification_partial']);self.assertFalse(v['meetings'][0]['can_classify'])
        with self.assertRaises(ValueError):self.label(v['meetings'][0])
        self.assertEqual(self.agenda.labels_path.read_text(),'broken')

    def test_written_receipt_hints_only_use_verified_records_and_detect_ambiguity(self):
        email=self.root/'email.json';manual=self.root/'manual';manual.mkdir()
        e=self.event();entry={'write':{'state':'verified','verified_event':e},'draft':{'fields':{'kind':'task_deadline'}}}
        email.write_text(json.dumps({'items':{'one':entry}}))
        loader=WrittenKinds(email,manual);hints,partial=loader();self.assertEqual(hints[event_key(e)],'task_deadline');self.assertFalse(partial)
        d=manual/'one';d.mkdir();(d/'proposal.json').write_text(json.dumps({'fields':{'kind':'meeting'}}));(d/'write.json').write_text(json.dumps(entry['write']))
        self.assertEqual(loader()[0],{})
        email.write_text('broken');self.assertTrue(loader()[1])

    def test_event_key_canonicalizes_offsets_but_changes_with_calendar_or_content(self):
        e=self.event();offset={**e,'start':'2026-11-08T13:00:00+01:00','end':'2026-11-08T14:00:00+01:00'}
        self.assertEqual(event_key(e),event_key(offset))
        self.assertNotEqual(event_key(e),event_key({**e,'calendar_id':'b'}))
