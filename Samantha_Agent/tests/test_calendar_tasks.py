from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from app.calendar_tasks import CalendarTasks
from app.calendar_agenda import WrittenKinds, event_key
from app.calendar_overview import CalendarOverview
from app.file_persistence import FileLockTimeoutError
from tests.test_calendar_overview import FakePilot


class TaskWriter:
    def __init__(self):
        self.calls = []
        self.results = []
        self.on_call = None
        self.build_missing = False

    def check_build(self):
        if self.build_missing:
            raise ValueError('Nejdřív povol zápis na Macu.')

    def execute_event(self, event, *, recover=False, confirmed=False):
        assert confirmed
        self.calls.append((deepcopy(event), recover))
        if self.on_call:
            self.on_call(event, recover)
        result = self.results.pop(0) if self.results else 'saved_verified'
        if result == 'raise':
            raise TimeoutError('synthetic possible save')
        return {'status': result, 'calendar_writes': result == 'saved_verified' and not recover,
                'event': {**event, 'event_id': 'synthetic'}}


class CalendarTaskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.now = datetime(2026, 11, 8, 12, tzinfo=timezone.utc)
        self.pilot = FakePilot(self.root/'calendar', lambda:self.now)
        self.calendar = CalendarOverview(self.pilot, clock=lambda:self.now)
        self.writer = TaskWriter()
        self.service = CalendarTasks(self.root/'tasks', calendar=self.calendar, writer=self.writer, clock=lambda:self.now)

    def prepare(self):
        self.calendar.refresh(confirmed=True)
        self.calendar.save_selection({'action':'save_selection','confirmed':True,'expected_revision':0,
                                      'read_calendar_ids':['a'],'target_calendar_id':'a'})

    def payload(self, **changes):
        return {'action':'create','request_id':'a'*32,'title':'Vyzvednout balík, pošta, vzít doklad',
                'date':'2026-11-09','time':'09:00','expected_selection_revision':1,
                'expected_target_calendar_id':'a','confirmed':True, **changes}

    def test_context_and_status_do_not_query_native_or_create_storage(self):
        context=self.service.context()
        self.assertFalse(context['ready']);self.assertEqual(context['default_time'],'09:00')
        self.assertEqual(self.service.status('a'*32)['state'],'not_found')
        self.assertFalse(self.service.root.exists());self.assertEqual(self.pilot.calls,[])
        self.assertEqual(self.writer.calls,[])

    def test_one_click_creates_exact_task_time_and_alarms_without_extra_calendar_read(self):
        self.prepare();calls=list(self.pilot.calls)
        result=self.service.execute(self.payload())
        self.assertEqual(result['state'],'verified');self.assertEqual(self.pilot.calls,calls)
        event,recover=self.writer.calls[0]
        self.assertFalse(recover);self.assertEqual(event['title'],self.payload()['title'])
        self.assertEqual(event['start'],'2026-11-09T08:00:00+00:00')
        self.assertEqual(event['end'],'2026-11-09T08:01:00+00:00')
        self.assertEqual(event['reminders'],[1440,60]);self.assertEqual(event['time_zone'],'Europe/Prague')
        self.assertEqual(event['location'],'');self.assertFalse(event['all_day'])

    def test_user_time_overrides_default_and_dst_resolves_real_summer_offset(self):
        self.prepare()
        self.service.execute(self.payload(date='2027-06-12',time='17:35'))
        self.assertEqual(self.writer.calls[0][0]['start'],'2027-06-12T15:35:00+00:00')

    def test_retry_and_restart_never_create_verified_task_twice(self):
        self.prepare();self.service.execute(self.payload())
        other=CalendarTasks(self.service.root,calendar=self.calendar,writer=self.writer,clock=lambda:self.now)
        self.assertEqual(other.execute(self.payload())['state'],'verified')
        self.assertEqual(other.recover('a'*32)['state'],'verified');self.assertEqual(len(self.writer.calls),1)

    def test_native_uncertainty_gets_one_read_only_verification_with_same_operation(self):
        self.prepare();self.writer.results=['write_unknown','saved_verified']
        result=self.service.execute(self.payload())
        self.assertEqual(result['state'],'verified')
        self.assertEqual([r for _,r in self.writer.calls],[False,True])
        self.assertEqual(self.writer.calls[0][0],self.writer.calls[1][0])

    def test_persistent_unknown_only_allows_read_only_recovery_even_after_restart(self):
        self.prepare();self.writer.results=['raise','write_unknown','write_unknown','saved_verified']
        result=self.service.execute(self.payload());self.assertEqual(result['state'],'unknown')
        self.service=CalendarTasks(self.service.root,calendar=self.calendar,writer=self.writer,clock=lambda:self.now)
        self.assertEqual(self.service.execute(self.payload())['state'],'unknown')
        self.assertEqual(len(self.writer.calls),2)
        self.assertEqual(self.service.recover('a'*32)['state'],'unknown')
        self.now+=timedelta(days=10)
        self.assertEqual(self.service.recover('a'*32)['state'],'verified')
        self.assertEqual([r for _,r in self.writer.calls],[False,True,True,True])

    def test_recovery_permission_rejection_does_not_claim_original_task_was_not_created(self):
        self.prepare();self.writer.results=['raise','authorization_required']
        self.assertEqual(self.service.execute(self.payload())['state'],'unknown')
        self.assertEqual([r for _,r in self.writer.calls],[False,True])

    def test_durable_pending_record_exists_before_native_call_and_is_recoverable_after_crash(self):
        self.prepare()
        def observe(event,recover):
            state=self.service.status('a'*32)
            self.assertEqual(state['state'],'pending')
            saved=json.loads((self.service.root/('a'*32)/'state.json').read_text())
            self.assertEqual(saved['write']['event'],event)
        self.writer.on_call=observe
        self.service.execute(self.payload())
        path=self.service.root/('a'*32)/'state.json'
        record=json.loads(path.read_text());record['write']['state']='pending';record['write'].pop('verified_event')
        path.write_text(json.dumps(record));self.writer.on_call=None
        self.service.execute(self.payload());self.assertEqual(len(self.writer.calls),1)
        self.service.recover('a'*32);self.assertTrue(self.writer.calls[-1][1])

    def test_concurrent_duplicate_submission_is_status_only_while_first_call_runs(self):
        self.prepare();entered=threading.Event();release=threading.Event();results=[]
        self.writer.on_call=lambda event,recover:(entered.set(),release.wait(3))
        thread=threading.Thread(target=lambda:results.append(self.service.execute(self.payload())))
        thread.start();self.assertTrue(entered.wait(2))
        try:self.assertEqual(self.service.execute(self.payload())['state'],'pending')
        finally:release.set();thread.join(4)
        self.assertFalse(thread.is_alive());self.assertEqual(len(self.writer.calls),1)
        self.assertEqual(results[0]['state'],'verified')

    def test_wrong_target_or_revision_is_known_blocked_without_native_call(self):
        self.prepare()
        for i,changes in enumerate(({'expected_selection_revision':0},{'expected_target_calendar_id':'b'})):
            result=self.service.execute(self.payload(request_id=str(i)*32,**changes))
            self.assertEqual(result['state'],'blocked')
        self.assertEqual(self.writer.calls,[])

    def test_missing_destination_or_build_never_invokes_writer(self):
        self.assertEqual(self.service.execute(self.payload())['state'],'blocked')
        self.prepare();self.writer.build_missing=True
        self.assertEqual(self.service.execute(self.payload(request_id='b'*32))['state'],'blocked')
        self.assertEqual(self.writer.calls,[])

    def test_past_invalid_and_ambiguous_dates_are_blocked_and_allow_editing(self):
        self.prepare()
        for i,values in enumerate(({'date':'2026-11-08','time':'09:00'}, {'date':'2027-02-30'},
                                   {'date':'2027-03-28','time':'02:30'}, {'date':'2027-10-31','time':'02:30'},
                                   {'date':'2050-01-01'})):
            with self.subTest(values=values):
                result=self.service.execute(self.payload(request_id=str(i)*32,**values))
                self.assertEqual(result['state'],'blocked')
        self.assertEqual(self.writer.calls,[])

    def test_bad_shapes_ids_consent_and_overview_length_limit_never_write(self):
        self.prepare()
        for change in ({'confirmed':False},{'request_id':'../bad'},{'title':'x'*401},
                       {'title':' '*400+'x'}, {'title':'x\x00y'}, {'time':'9:00'}, {'extra':True}):
            with self.subTest(change=change),self.assertRaises(ValueError):self.service.execute(self.payload(**change))
        self.assertEqual(self.writer.calls,[])
        self.assertFalse(self.service.root.exists())

    def test_same_identity_cannot_be_edited_into_a_second_event(self):
        self.prepare();self.service.execute(self.payload())
        with self.assertRaises(ValueError):self.service.execute(self.payload(title='Jiný text'))
        self.assertEqual(len(self.writer.calls),1)

    def test_explicit_retry_after_proven_native_rejection_uses_same_operation(self):
        self.prepare();self.writer.results=['authorization_required','saved_verified']
        self.assertEqual(self.service.execute(self.payload())['state'],'blocked')
        self.assertEqual(self.service.execute(self.payload())['state'],'verified')
        self.assertEqual([r for _,r in self.writer.calls],[False,False])
        self.assertEqual(self.writer.calls[0][0],self.writer.calls[1][0])

    def test_selection_is_locked_during_save_and_dashboard_callback_runs_after_release(self):
        self.prepare()
        def during(event,recover):
            with self.assertRaises(FileLockTimeoutError):
                with self.calendar._lock():pass
        def after():
            with self.calendar._lock():pass
        self.writer.on_call=during;self.service.on_saved=after
        self.assertEqual(self.service.execute(self.payload())['state'],'verified')

    def test_dashboard_failure_cannot_undo_verified_write(self):
        self.prepare();self.service.on_saved=lambda:(_ for _ in ()).throw(RuntimeError())
        self.assertEqual(self.service.execute(self.payload())['state'],'verified')
        self.assertEqual(len(self.writer.calls),1)

    def test_duplicate_confirmed_request_does_not_refresh_dashboard_again(self):
        self.prepare();calls=[];self.service.on_saved=lambda:calls.append(True)
        self.service.execute(self.payload());self.service.execute(self.payload());self.service.recover('a'*32)
        self.assertEqual(calls,[True])

    def test_corrupt_or_symlinked_record_never_leads_to_new_write(self):
        self.prepare();self.service.execute(self.payload())
        path=self.service.root/('a'*32)/'state.json';path.write_text('broken')
        with self.assertRaises(ValueError):self.service.execute(self.payload())
        other=self.root/'elsewhere';other.mkdir()
        (self.service.root/('b'*32)).symlink_to(other,target_is_directory=True)
        with self.assertRaises(ValueError):self.service.execute(self.payload(request_id='b'*32))
        self.assertEqual(len(self.writer.calls),1)

    def test_task_receipt_classifies_exact_verified_event_without_guessing(self):
        self.prepare();self.service.execute(self.payload())
        loader=WrittenKinds(self.root/'empty-email.json',self.root/'manual',task_root=self.service.root)
        hints,partial=loader();self.assertFalse(partial)
        self.assertEqual(hints[event_key(self.writer.calls[0][0])],'task_deadline')
        self.assertNotIn(event_key({**self.writer.calls[0][0],'title':'Změněno'}),hints)

    def test_status_or_missing_recovery_never_initializes_private_store(self):
        self.assertEqual(self.service.execute({'action':'recover','request_id':'b'*32,'confirmed':True})['state'],'not_found')
        self.assertFalse(self.service.root.exists());self.assertEqual(self.writer.calls,[])
