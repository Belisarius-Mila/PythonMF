from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
import unittest
from unittest.mock import patch

from app.email.calendar_draft import CalendarDraftService
from app.email.calendar_proposal import empty_fields, simple_defaults, edit_simple, validate_fields
from tests import test_email_calendar_review as review_tests


class FakeWriter:
    def __init__(self, root): self.root=root; self.calls=[]; self.result='saved_verified'; self.after=None
    def check_build(self): pass
    def execute_event(self,event,*,recover=False,confirmed=False):
        assert confirmed
        self.calls.append((deepcopy(event),recover))
        if self.after:self.after()
        if self.result=='raise':raise TimeoutError('after possible write')
        return {'status':self.result,'event':{'event_id':'synthetic',**event}}


class CalendarWriteTests(unittest.TestCase):
    setUp=review_tests.CalendarReviewTests.setUp
    state=review_tests.CalendarReviewTests.state
    review=review_tests.CalendarReviewTests.review
    event=review_tests.CalendarReviewTests.event

    def writer(self):
        self.service.writer=FakeWriter(Path(self.temp.name)/'writer')
        return self.service.writer

    def write(self,view=None,**changes):
        view=view or self.state()
        return self.service.execute({'action':'write','id':self.mail.item_id,'expected_revision':view['draft']['revision'],
            'review_fingerprint':(view.get('review') or {}).get('fingerprint',''),'confirmed':True,**changes})

    def edit(self,**changes):
        view=self.state();f=view['draft']['fields']
        values={'title':f['title'],'start':f['date']+'T'+f['start_time'],'kind':'meeting','location':f['location'],**changes}
        return self.service.execute({'action':'save_simple','id':self.mail.item_id,'expected_revision':view['draft']['revision'],'values':values})

    def test_click_creates_exact_event_and_alarms_once_even_after_restart(self):
        writer=self.writer();before=self.worker.status();view=self.review();result=self.write(view)
        self.assertEqual(result['write']['state'],'verified');self.assertTrue(result['calendar_writes'])
        event,recover=writer.calls[0];self.assertFalse(recover)
        self.assertEqual(event['calendar_id'],'a');self.assertEqual(event['reminders'],[1440,60])
        self.assertEqual(event['time_zone'],'Europe/Prague')
        self.write(view);self.assertEqual(len(writer.calls),1)
        restarted=CalendarDraftService(self.worker,calendar=self.calendar,writer=writer,clock=lambda:self.now)
        self.service=restarted;self.write(view);self.assertEqual(len(writer.calls),1)
        self.assertEqual(self.worker.status(),before);self.assertEqual(self.driver.calls,1)

    def test_unconfirmed_wrong_revision_and_extra_fields_cannot_write(self):
        writer=self.writer();view=self.review()
        for changes in ({'confirmed':False},{'expected_revision':99},{'extra':True}):
            with self.assertRaises(ValueError):self.write(view,**changes)
        self.assertEqual(writer.calls,[])

    def test_missing_or_changed_preview_requires_fresh_click(self):
        writer=self.writer();result=self.write();self.assertIsNone(result['write']);self.assertEqual(writer.calls,[])
        self.pilot.events=[self.event()]
        result=self.write(result);self.assertIsNone(result['write']);self.assertEqual(len(result['review']['conflicts']),1)
        self.write(result);self.assertEqual(len(writer.calls),1)

    def test_changed_target_does_not_reuse_consent(self):
        writer=self.writer();view=self.review()
        with self.calendar._lock():
            data=self.calendar._load();data['revision']+=1;self.pilot._write(self.calendar.path,data)
        self.assertIsNone(self.write(view)['write']);self.assertEqual(writer.calls,[])

    def test_uncertain_result_and_restart_only_recover_never_create_again(self):
        writer=self.writer();writer.result='raise';view=self.review();result=self.write(view)
        self.assertEqual(result['write']['state'],'unknown')
        op=writer.calls[0][0]['operation_id'];writer.result='saved_verified'
        self.service=CalendarDraftService(self.worker,calendar=self.calendar,writer=writer,clock=lambda:self.now)
        result=self.write(view);self.assertEqual(result['write']['state'],'verified')
        self.assertEqual([r for _,r in writer.calls],[False,True]);self.assertEqual(writer.calls[1][0]['operation_id'],op)

    def test_unresolved_recovery_cannot_create_or_allow_edits(self):
        writer=self.writer();writer.result='write_unknown';view=self.review()
        self.write(view);self.write(view)
        self.assertEqual([r for _,r in writer.calls],[False,True])
        with self.assertRaises(ValueError):self.edit(title='Another event')

    def test_verified_event_cannot_be_edited_into_another_create(self):
        self.writer();self.write(self.review())
        with self.assertRaises(ValueError):self.edit(title='Another event')

    def test_proven_permission_rejection_allows_new_explicit_confirmation(self):
        writer=self.writer();writer.result='authorization_required';view=self.review()
        self.assertEqual(self.write(view)['write']['state'],'blocked')
        writer.result='saved_verified';self.assertEqual(self.write(self.state())['write']['state'],'verified')
        self.assertEqual(len(writer.calls),2)

    def test_draft_change_during_native_read_prevents_write(self):
        writer=self.writer();view=self.review()
        self.pilot.on_read=lambda:self.edit(location='Changed concurrently')
        with self.assertRaises(ValueError):self.write(view)
        self.assertEqual(writer.calls,[])

    def test_pending_claim_blocks_edit_inside_write(self):
        writer=self.writer();errors=[]
        def callback():
            try:self.edit(title='Concurrent')
            except ValueError:errors.append(True)
        writer.after=callback;self.write(self.review());self.assertEqual(errors,[True])

    def test_simple_edits_autosave_with_revision_and_keep_explicit_duration(self):
        self.writer();self.edit(start='2026-11-12T11:00',location='')
        view=self.state();f=view['draft']['fields']
        self.assertEqual((f['date'],f['end_date'],f['end_time']),('2026-11-12','2026-11-12','12:00'))
        self.assertEqual(view['draft']['reminders'],[1440,60]);self.assertEqual(f['location'],'')
        self.edit(kind='all_day',start='2026-11-13')
        self.assertEqual(self.state()['draft']['fields']['end_date'],'2026-11-14')

    def test_date_only_deadline_uses_one_all_day_calendar_event(self):
        writer=self.writer();self.edit(kind='task_deadline',start='2026-11-11')
        self.write(self.review());event=writer.calls[0][0]
        self.assertTrue(event['all_day'])
        self.assertEqual(datetime.fromisoformat(event['end'])-datetime.fromisoformat(event['start']),timedelta(days=1))

    def test_deadline_is_a_minute_event_without_attendees_or_mail_send(self):
        writer=self.writer();self.edit(kind='task_deadline');self.write(self.review())
        event=writer.calls[0][0]
        self.assertEqual(datetime.fromisoformat(event['end'])-datetime.fromisoformat(event['start']),timedelta(minutes=1))
        self.assertNotIn('attendees',event)


class SimpleCalendarTimeTests(unittest.TestCase):
    def fields(self,**changes):
        return {**empty_fields(),'title':'Test','date':'2026-11-11','start_time':'10:00',**changes}

    def test_missing_end_and_timezone_default_to_hour_and_prague(self):
        f,_=simple_defaults(self.fields());self.assertEqual((f['time_zone'],f['end_time']),('Europe/Prague','11:00'))
        self.assertEqual(validate_fields(f)[0],[])

    def test_explicit_different_end_wins_over_hour(self):
        f,_=simple_defaults(self.fields(end_time='12:30'))
        self.assertEqual((f['end_time'],f['duration_minutes']),('12:30','150'))
        moved=edit_simple({'fields':f},{'title':'Test','start':'2026-11-12T11:00','kind':'meeting','location':''})
        self.assertEqual((moved['end_date'],moved['end_time']),('2026-11-12','13:30'))

    def test_explicit_duration_and_cross_midnight_end_are_preserved(self):
        f,_=simple_defaults(self.fields(start_time='23:30',duration_minutes='120'))
        self.assertEqual((f['end_date'],f['end_time']),('2026-11-12','01:30'))
        f,_=simple_defaults(self.fields(start_time='23:30',end_date='2026-11-12',end_time='03:00'))
        self.assertEqual(f['duration_minutes'],'210')

    def test_default_hour_is_elapsed_time_at_dst_boundary(self):
        f,_=simple_defaults(self.fields(date='2027-03-28',start_time='01:30'))
        self.assertEqual(f['end_time'],'03:30');self.assertEqual(f['duration_minutes'],'60')
        self.assertEqual(validate_fields(f)[0],[])

    def test_gap_fold_and_inverted_explicit_end_are_not_silently_fixed(self):
        for changes in ({'date':'2027-03-28','start_time':'02:30'},{'date':'2027-10-31','start_time':'02:30'},{'end_time':'09:00'}):
            f,_=simple_defaults(self.fields(**changes));self.assertTrue(validate_fields(f)[0])

    def test_explicit_timezone_wins_and_location_optional(self):
        f,_=simple_defaults(self.fields(time_zone='America/New_York',location=''))
        self.assertEqual(f['time_zone'],'America/New_York');self.assertEqual(validate_fields(f)[0],[])

    def test_multiday_all_day_end_survives_title_edit_and_date_shift(self):
        f,_=simple_defaults(self.fields(all_day=True,start_time='',end_date='2026-11-14'))
        values={'title':'Nový název','start':'2026-11-11','kind':'all_day','location':''}
        self.assertEqual(edit_simple({'fields':f},values)['end_date'],'2026-11-14')
        self.assertEqual(edit_simple({'fields':f},{**values,'start':'2026-11-20'})['end_date'],'2026-11-23')
