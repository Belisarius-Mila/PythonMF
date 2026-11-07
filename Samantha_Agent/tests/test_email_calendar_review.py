from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import subprocess
import unittest

from app.calendar_overview import CalendarOverview
from app.email.calendar_draft import CalendarDraftService
from app.email.calendar_proposal import derive_fields, empty_fields, validate_fields
from app.email.continuous_agent import ContinuousEmailAgent
from tests.test_calendar_overview import FakePilot
from tests.test_continuous_email_agent import FakeSource, proposal
from tests.test_email_calendar_draft import Driver, message


class BoundedPilot(FakePilot):
    def __init__(self, root, clock):
        super().__init__(root, clock)
        self.events = []
        self.intervals = []
        self.on_read = None

    def read_overview(self, ids, *, confirmed=False, start=None, end=None):
        result = super().read_overview(ids, confirmed=confirmed)
        if start is not None:
            self.intervals.append((start, end))
            result.update(start=start.isoformat(), end=end.isoformat(), events=deepcopy(self.events))
            result.update(self.extra)
            if self.on_read: self.on_read()
        return result


class CalendarReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.now = datetime(2026, 11, 7, 12, tzinfo=timezone.utc)
        root = Path(self.temp.name)
        self.pilot = BoundedPilot(root/'calendar', lambda:self.now)
        self.calendar = CalendarOverview(self.pilot, clock=lambda:self.now)
        self.calendar.refresh(confirmed=True)
        self.calendar.save_selection({'action':'save_selection','confirmed':True,'expected_revision':0,
                                      'read_calendar_ids':['a'],'target_calendar_id':'a'})
        self.worker = ContinuousEmailAgent(root/'mail')
        self.mail = message(); self.worker.cycle(FakeSource([self.mail]), lambda _:proposal())
        self.driver = Driver()
        class Source:
            def read_item(inner, card): return self.mail
        self.service = CalendarDraftService(self.worker, source_factory=lambda *_:Source(), driver=self.driver,
            launcher=lambda callback:callback(), calendar=self.calendar, clock=lambda:self.now)
        self.service.execute({'action':'prepare','id':self.mail.item_id,'request_id':'calendar-review-test',
                              'expected_content_digest':self.mail.content_digest,'confirmed':True})

    def state(self): return self.service.status(self.mail.item_id)
    def review(self): return self.service.execute({'action':'review','id':self.mail.item_id,'expected_revision':self.state()['draft']['revision'],'confirmed':True})
    def confirm(self, view, **changes):
        return self.service.execute({'action':'confirm','id':self.mail.item_id,'expected_revision':0,
            'review_id':view['review']['review_id'],'acknowledged':True,'accept_conflicts':False,**changes})
    def save(self, **changes):
        view = self.state()
        return self.service.execute({'action':'save','id':self.mail.item_id,'expected_revision':view['draft']['revision'],
                                     'fields':{**view['draft']['fields'],**changes}})
    def event(self, start='2026-11-11T09:30:00+00:00', end='2026-11-11T10:30:00+00:00', **changes):
        return {'calendar_id':'a','title':'Soukromá schůzka','start':start,'end':end,'all_day':False,
                'timezone':'Europe/Prague','start_day':'2026-11-11','end_day':'2026-11-11',**changes}

    def test_defaults_and_derived_fields_preserve_user_choices_and_survive_restart(self):
        draft = self.state()['draft']
        self.assertEqual(draft['fields']['end_date'],'2026-11-11')
        self.assertEqual(draft['fields']['duration_minutes'],'60')
        self.assertEqual(draft['evidence']['duration_minutes']['origin'],'calculated')
        self.assertEqual(draft['reminders'],[1440,60])
        fields={**draft['fields'],'start_time':'09:15','end_time':'11:00'}
        self.service.execute({'action':'save','id':self.mail.item_id,'expected_revision':0,'fields':fields,'reminders':[60]})
        restarted=CalendarDraftService(self.worker, calendar=self.calendar, clock=lambda:self.now)
        self.assertEqual(restarted.status(self.mail.item_id)['draft']['fields']['duration_minutes'],'105')
        self.assertEqual(restarted.status(self.mail.item_id)['draft']['reminders'],[60])
        self.save(date='2026-11-12')
        self.assertEqual(self.state()['draft']['fields']['end_date'],'2026-11-12')
        self.save(end_date='2026-11-13')
        self.save(date='2026-11-10')
        self.assertEqual(self.state()['draft']['fields']['end_date'],'2026-11-13')

    def test_legacy_draft_defaults_are_read_only_and_explicit_disable_is_preserved(self):
        def old(document): document['items'][self.mail.item_id]['draft'].pop('reminders')
        self.service._mutate(old)
        before=self.service.repository.read()
        self.assertEqual(self.state()['draft']['reminders'],[1440,60])
        self.assertEqual(self.service.repository.read(),before)
        self.service.execute({'action':'save','id':self.mail.item_id,'expected_revision':0,'fields':self.state()['draft']['fields'],'reminders':[]})
        self.assertEqual(self.review()['review']['alerts'],[])

    def test_invalid_reminder_values_fail_before_persistence(self):
        for value in ([True],[1],[60,60],'60',[1440,60,1]):
            before=self.service.repository.read()
            with self.assertRaises(ValueError):
                self.service.execute({'action':'save','id':self.mail.item_id,'expected_revision':0,'fields':self.state()['draft']['fields'],'reminders':value})
            self.assertEqual(self.service.repository.read(),before)

    def test_fresh_bounded_preview_shows_alerts_target_and_exact_overlap_without_model(self):
        before=self.worker.status()
        self.pilot.events=[self.event()]
        view=self.review(); r=view['review']
        self.assertTrue(r['valid']); self.assertEqual(r['target']['id'],'a')
        self.assertEqual(r['alerts'][0]['at'],'2026-11-10T10:00:00+01:00')
        self.assertEqual(r['alerts'][1]['at'],'2026-11-11T09:00:00+01:00')
        self.assertEqual(len(r['conflicts']),1); self.assertFalse(r['calendar_writes'])
        self.assertEqual((self.pilot.intervals[0][1]-self.pilot.intervals[0][0]).total_seconds(),3600)
        self.assertEqual(self.driver.calls,1); self.assertEqual(self.worker.status(),before)

    def test_clear_interval_and_all_day_overlap_are_distinguished(self):
        # A real bounded helper excludes non-overlapping rows altogether.
        self.pilot.events=[]
        self.assertEqual(self.review()['review']['conflicts'],[])
        self.pilot.events=[self.event(start='2026-11-10T23:00:00Z',end='2026-11-11T23:00:00Z',all_day=True,end_day='2026-11-12')]
        self.assertTrue(self.review()['review']['conflicts'][0]['all_day'])

    def test_confirmation_requires_acknowledgment_and_conflict_acceptance_and_reloads(self):
        self.pilot.events=[self.event()]; view=self.review()
        with self.assertRaises(ValueError): self.confirm(view,acknowledged=False)
        with self.assertRaises(ValueError): self.confirm(view)
        result=self.confirm(view,accept_conflicts=True)
        self.assertIsNotNone(result['confirmation']); self.assertFalse(result['confirmation']['calendar_writes'])
        self.assertEqual(len(self.pilot.intervals),2); self.assertEqual(self.driver.calls,1)
        restarted=CalendarDraftService(self.worker, calendar=self.calendar, clock=lambda:self.now)
        self.assertIsNotNone(restarted.status(self.mail.item_id)['confirmation'])

    def test_expiry_during_fresh_read_requires_another_human_confirmation(self):
        view=self.review(); self.now+=timedelta(minutes=4,seconds=59)
        self.pilot.on_read=lambda:setattr(self,'now',self.now+timedelta(seconds=2))
        result=self.confirm(view)
        self.assertIsNone(result['confirmation']); self.assertTrue(result['review']['valid'])

    def test_changed_conflicts_require_new_preview_and_new_acceptance(self):
        view=self.review(); self.pilot.events=[self.event()]
        result=self.confirm(view)
        self.assertIsNone(result['confirmation']); self.assertEqual(len(result['review']['conflicts']),1)
        self.assertIn('změnily',result['message'])
        with self.assertRaises(ValueError): self.confirm(view)
        self.assertIsNotNone(self.confirm(result,accept_conflicts=True)['confirmation'])

    def test_edit_or_changed_selection_or_expiry_invalidates_prior_confirmation(self):
        view=self.confirm(self.review())
        self.assertIsNotNone(view['confirmation'])
        self.now+=timedelta(minutes=6)
        self.assertFalse(self.state()['review']['valid']); self.assertIsNone(self.state()['confirmation'])
        with self.assertRaises(ValueError): self.confirm(view)
        view=self.review()
        self.calendar.save_selection({'action':'save_selection','confirmed':True,'expected_revision':1,'read_calendar_ids':['b'],'target_calendar_id':'a'})
        self.assertFalse(self.state()['review']['valid'])
        with self.assertRaises(ValueError): self.confirm(view)
        self.save(location='Nové místo')
        self.assertIsNone(self.state()['review']); self.assertIsNone(self.state()['confirmation'])

    def test_changed_draft_during_read_cannot_receive_an_old_confirmation(self):
        self.pilot.on_read=lambda:self.save(location='Změna v druhém okně')
        with self.assertRaises(ValueError): self.review()
        self.assertIsNone(self.state()['review'])

    def test_changed_selection_during_read_cannot_receive_an_old_confirmation(self):
        self.pilot.on_read=lambda:self.calendar.save_selection({'action':'save_selection','confirmed':True,
            'expected_revision':1,'read_calendar_ids':['b'],'target_calendar_id':'a'})
        # Simulate another writer after the native read has released the selection lock.
        original=self.calendar.review_interval
        def changed(*args,**kwargs):
            callback=self.pilot.on_read; self.pilot.on_read=None
            result=original(*args,**kwargs); callback(); return result
        self.calendar.review_interval=changed
        with self.assertRaises(ValueError):self.review()
        self.assertIsNone(self.state()['review'])

    def test_failed_read_revoked_access_incomplete_scope_or_target_blocks_confirmation(self):
        for mode in ('failure','denied','truncated','missing','wrong_range','readonly'):
            self.pilot.extra={};self.pilot.fail=False;self.pilot.auth='full_access';self.pilot.rows[0]['writable']=True
            view=self.review()
            if mode=='failure': self.pilot.fail=True
            if mode=='denied': self.pilot.auth='denied'
            if mode=='truncated': self.pilot.extra={'truncated':True}
            if mode=='missing': self.pilot.extra={'missing_calendar_ids':['a']}
            if mode=='wrong_range': self.pilot.extra={'end':'2026-11-11T10:01:00Z'}
            if mode=='readonly': self.pilot.rows[0]['writable']=False
            with self.subTest(mode=mode),self.assertRaises((ValueError,subprocess.TimeoutExpired)): self.confirm(view)
            self.assertIsNone(self.state()['confirmation']);self.assertFalse(self.state()['review']['valid'])

    def test_incomplete_or_manual_draft_is_not_confirmable(self):
        for changes in ({'date':''},{'start_time':''},{'kind':'manual_required'}):
            self.save(**changes)
            with self.assertRaises(ValueError):
                self.service.execute({'action':'review','id':self.mail.item_id,'expected_revision':self.state()['draft']['revision'],'confirmed':True})

    def test_deadline_checks_point_and_does_not_invent_meeting_duration(self):
        view=self.save(kind='task_deadline',end_date='',end_time='',duration_minutes='')
        result=self.service.execute({'action':'review','id':self.mail.item_id,'expected_revision':1,'confirmed':True})
        self.assertTrue(result['review']['deadline_is_point'])
        self.assertEqual(result['review']['fields']['duration_minutes'],'')
        self.assertEqual((self.pilot.intervals[-1][1]-self.pilot.intervals[-1][0]).total_seconds(),1)


class DerivedCalendarTimeTests(unittest.TestCase):
    def fields(self, **changes):
        return {**empty_fields(),'title':'Test','date':'2026-11-11','start_time':'10:00','end_time':'11:00','time_zone':'Europe/Prague',**changes}

    def test_duration_uses_real_elapsed_time_at_dst_and_rejects_ambiguous_times(self):
        fields,_=derive_fields(self.fields(date='2026-03-29',start_time='01:30',end_time='03:30'))
        self.assertEqual(fields['duration_minutes'],'60')
        fields,_=derive_fields(self.fields(date='2026-10-25',start_time='01:30',end_time='03:30'))
        self.assertEqual(fields['duration_minutes'],'180')
        for day in ('2026-03-29','2026-10-25'):
            fields,_=derive_fields(self.fields(date=day,start_time='02:30',duration_minutes='60'))
            self.assertEqual(fields['duration_minutes'],''); self.assertIsNone(validate_fields(fields)[1])

    def test_midnight_requires_explicit_later_date_and_all_day_defaults_are_exclusive(self):
        fields,_=derive_fields(self.fields(start_time='23:30',end_time='00:30'))
        self.assertTrue(validate_fields(fields)[0]); self.assertEqual(fields['duration_minutes'],'')
        fields,_=derive_fields({**fields,'end_date':'2026-11-12'})
        self.assertEqual(fields['duration_minutes'],'60')
        fields,_=derive_fields(self.fields(all_day=True,start_time='',end_time=''))
        self.assertEqual(fields['end_date'],'2026-11-12'); self.assertIsNotNone(validate_fields(fields)[1])

    def test_duration_only_computes_actual_end_day_without_overriding_explicit_day(self):
        fields,_=derive_fields(self.fields(start_time='23:30',end_time='',duration_minutes='120'))
        self.assertEqual(fields['end_date'],'2026-11-12'); self.assertIsNotNone(validate_fields(fields)[1])
        fields,_=derive_fields(self.fields(start_time='23:30',end_time='',duration_minutes='120',end_date='2026-11-13'))
        self.assertTrue(validate_fields(fields)[0])
