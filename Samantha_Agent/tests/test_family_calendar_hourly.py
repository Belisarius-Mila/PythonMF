from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
import json
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch, Mock
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from app.family_calendar_delivery import NotificationOffset, DeliveryState, begin_delivery, complete_delivery, plan_delivery
from app.family_calendar_delivery_store import begin_stored_delivery, complete_stored_delivery, load_delivery_records, recover_interrupted_deliveries
from app.family_calendar_delivery_coordinator import coordinate_delivery_attempt, DeliveryTransportOutcome
from app.family_calendar_delivery_automatic import run_family_calendar_automatic_delivery
from app.family_calendar_delivery_readiness import FAMILY_CALENDAR_PLANNER_LABEL, _planner_document_matches
from app.family_calendar_delivery_hourly import preview_hourly_schedule, apply_hourly_schedule, HOURLY_CONFIRMATION, GLOBAL_CONFIRMATION
from app.family_calendar_delivery_config import DeliveryConfigMode
from app.family_calendar_smtp_adapter import SMTPClientResult
from tests.test_family_calendar_delivery_automatic import _private_paths, _write_people, _write_config, FakeSMTPClient, PRIVATE_SECRET

IDS = ('recipient-1', 'recipient-2', 'recipient-3', 'recipient-4')
EVENT = 'person-synthetic:birthday:2026-12-19'


class HourlyDeliveryTests(unittest.TestCase):
    def test_definite_failure_gets_new_persistent_attempt_and_acceptance_stops_all_offsets(self):
        with tempfile.TemporaryDirectory(dir="/private/tmp") as d:
            path = Path(d) / 'state.json'
            a = begin_stored_delivery(event_key=EVENT, offset='D-2', recipient_ids=IDS, path=path)
            complete_stored_delivery(operation_id=a.record.operation_id, not_sent_recipient_ids=IDS, path=path)
            b = begin_stored_delivery(event_key=EVENT, offset='D-2', recipient_ids=IDS, path=path)
            self.assertTrue(b.started)
            self.assertNotEqual(a.record.operation_id, b.record.operation_id)
            self.assertEqual(b.record.attempt, 1)
            complete_stored_delivery(operation_id=b.record.operation_id, accepted_recipient_ids=IDS, path=path)
            records = load_delivery_records(path)
            self.assertEqual(len(records), 2)
            self.assertIs(records[0].state, DeliveryState.NOT_SENT)
            for offset in NotificationOffset:
                self.assertFalse(plan_delivery(event_key=EVENT, offset=offset, records=records).eligible)
            raw = json.loads(path.read_text())
            self.assertNotIn('attempt', raw['records'][a.record.operation_id])
            self.assertEqual(raw['records'][b.record.operation_id]['attempt'], 1)

    def test_event_day_catches_missing_or_definitely_unsent_only(self):
        self.assertTrue(plan_delivery(event_key=EVENT, offset='D-0').eligible)
        sending = begin_delivery(plan_delivery(event_key=EVENT, offset='D-1'), recipient_ids=IDS)
        outcomes = [sending, complete_delivery(sending, accepted_recipient_ids=IDS),
                    complete_delivery(sending, accepted_recipient_ids=IDS[:1], not_sent_recipient_ids=IDS[1:]),
                    complete_delivery(sending, unknown_recipient_ids=IDS)]
        for record in outcomes:
            self.assertFalse(plan_delivery(event_key=EVENT, offset='D-0', records=(record,)).eligible)
        record = complete_delivery(sending, not_sent_recipient_ids=IDS)
        self.assertTrue(plan_delivery(event_key=EVENT, offset='D-0', records=(record,)).eligible)

    def test_retry_crash_recovers_unknown_and_prevents_further_attempt(self):
        with tempfile.TemporaryDirectory(dir="/private/tmp") as d:
            path = Path(d) / 'state.json'
            a = begin_stored_delivery(event_key=EVENT, offset='D-1', recipient_ids=IDS, path=path)
            complete_stored_delivery(operation_id=a.record.operation_id, not_sent_recipient_ids=IDS, path=path)
            b = begin_stored_delivery(event_key=EVENT, offset='D-1', recipient_ids=IDS, path=path)
            recover_interrupted_deliveries(path)
            records = load_delivery_records(path)
            self.assertEqual(len(records), 2)
            self.assertTrue(any(r.operation_id == b.record.operation_id and r.state is DeliveryState.DELIVERY_UNKNOWN for r in records))
            self.assertFalse(plan_delivery(event_key=EVENT, offset='D-1', records=records).eligible)
            self.assertFalse(plan_delivery(event_key=EVENT, offset='D-0', records=records).eligible)

    def test_concurrent_hourly_runs_have_one_transport(self):
        with tempfile.TemporaryDirectory(dir="/private/tmp") as d:
            calls = []
            def transport(record):
                calls.append(record.operation_id)
                return DeliveryTransportOutcome(accepted_recipient_ids=IDS)
            def run(_):
                return coordinate_delivery_attempt(event_key=EVENT, offset='D-0', recipient_ids=IDS,
                    state_path=Path(d)/'state.json', worker_path=Path(d)/'worker.json', transport=transport)
            with ThreadPoolExecutor(2) as pool:
                results = list(pool.map(run, range(2)))
            self.assertEqual(len(calls), 1)
            self.assertEqual(sorted(r.status for r in results), ['skipped', 'smtp_accepted'])

    def test_retries_are_bounded_and_old_failures_do_not_block_next_day(self):
        records = []
        for attempt in range(24):
            p = plan_delivery(event_key=EVENT, offset='D-2', records=records)
            self.assertTrue(p.eligible)
            self.assertEqual(p.attempt, attempt)
            records.append(complete_delivery(begin_delivery(p, recipient_ids=IDS), not_sent_recipient_ids=IDS))
        self.assertFalse(plan_delivery(event_key=EVENT, offset='D-2', records=records).eligible)
        self.assertTrue(plan_delivery(event_key=EVENT, offset='D-1', records=records).eligible)

    def test_real_event_day_run_then_hourly_recheck_avoids_credential_and_transport(self):
        with tempfile.TemporaryDirectory(dir="/private/tmp") as d:
            paths = _private_paths(Path(d)); _write_people(paths[0]); _write_config(paths[1], mode='enabled')
            client = FakeSMTPClient(SMTPClientResult())
            kw = dict(today=date(2026,12,18), hourly_policy=True, people_path=paths[0], config_path=paths[1],
                      state_path=paths[2], worker_path=paths[3], credential_reader=lambda: PRIVATE_SECRET,
                      smtp_client_factory=lambda *_: client)
            first = run_family_calendar_automatic_delivery(**kw)
            self.assertEqual(first.d0_count, 1)
            self.assertEqual(first.accepted_count, 2)
            with patch.dict(kw, credential_reader=lambda: self.fail('completed events must not read credentials')):
                second = run_family_calendar_automatic_delivery(**kw)
            self.assertEqual(second.skipped_count, 2)
            self.assertFalse(second.keychain_read)
            third = run_family_calendar_automatic_delivery(**{**kw, 'today':date(2026,12,19)})
            self.assertEqual(third.attempted_count, 0)
            self.assertEqual(client.calls, 2)
            records = load_delivery_records(paths[2])
            self.assertTrue(any(r.offset is NotificationOffset.D0 for r in records))

    def test_offline_after_wake_is_retried_and_then_stops_after_acceptance(self):
        from app.family_calendar_icloud_smtp_client import ICloudSMTPClient
        from tests.test_family_calendar_icloud_smtp_client import FakeSMTPSession
        with tempfile.TemporaryDirectory(dir="/private/tmp") as d:
            paths = _private_paths(Path(d)); _write_people(paths[0]); _write_config(paths[1], mode='enabled')
            offline = True
            sends = []
            def smtp_factory(*args, **kwargs):
                if offline:
                    raise OSError('synthetic no network')
                session = FakeSMTPSession(); sends.append(session)
                return session
            kw = dict(today=date(2026,12,18), hourly_policy=True, people_path=paths[0], config_path=paths[1],
                      state_path=paths[2], worker_path=paths[3], credential_reader=lambda: PRIVATE_SECRET,
                      smtp_client_factory=lambda user,password:ICloudSMTPClient(user,password,smtp_factory))
            first = run_family_calendar_automatic_delivery(**kw)
            self.assertEqual(first.not_sent_count, 2)
            self.assertEqual(first.delivery_unknown_count, 0)
            offline = False
            second = run_family_calendar_automatic_delivery(**kw)
            self.assertEqual(second.accepted_count, 2)
            third = run_family_calendar_automatic_delivery(**kw)
            self.assertEqual(third.attempted_count, 0)
            records = load_delivery_records(paths[2])
            self.assertEqual(len(records), 4)
            self.assertEqual(sum(r.attempt == 1 for r in records), 2)
            self.assertEqual(len(sends), 2)

    def test_before_eight_does_not_read_credential_or_recover_state(self):
        with tempfile.TemporaryDirectory(dir="/private/tmp") as d:
            paths = _private_paths(Path(d)); _write_people(paths[0]); _write_config(paths[1], mode='enabled')
            result = run_family_calendar_automatic_delivery(now=datetime(2026,12,18,7,59,tzinfo=ZoneInfo('Europe/Prague')),
                people_path=paths[0], config_path=paths[1], state_path=paths[2], worker_path=paths[3],
                credential_reader=lambda: self.fail('night credential access'),
                runtime_recovery=lambda **_: self.fail('night recovery'))
            self.assertEqual(result.attempted_count, 0)
            self.assertFalse(paths[2].exists())

    def test_legacy_runner_does_not_enable_event_day_without_activation(self):
        with tempfile.TemporaryDirectory(dir="/private/tmp") as d:
            paths = _private_paths(Path(d)); _write_people(paths[0]); _write_config(paths[1], mode='enabled')
            client = FakeSMTPClient(SMTPClientResult())
            result = run_family_calendar_automatic_delivery(today=date(2026,12,19), hourly_policy=False,
                people_path=paths[0], config_path=paths[1], state_path=paths[2], worker_path=paths[3],
                credential_reader=lambda: self.fail('inactive D-0 accessed credential'), smtp_client_factory=lambda *_:client)
            self.assertEqual(result.candidate_count, 0)
            self.assertEqual(client.calls, 0)


class HourlyScheduleTests(unittest.TestCase):
    def fixture(self, directory):
        root=Path(directory); interpreter=root/'python';interpreter.write_text('');interpreter.chmod(0o700)
        runner=root/'runner.py';runner.write_text('')
        planner=root/(FAMILY_CALENDAR_PLANNER_LABEL+'.plist')
        doc={'Label':FAMILY_CALENDAR_PLANNER_LABEL,'ProgramArguments':[str(interpreter),str(runner)],
             'StartCalendarInterval':{'Hour':8,'Minute':0},'RunAtLoad':False,'ProcessType':'Background'}
        planner.write_bytes(plistlib.dumps(doc));planner.chmod(0o600)
        return root,planner,runner

    def test_preview_and_transition_keep_existing_paths_and_config(self):
        with tempfile.TemporaryDirectory(dir="/private/tmp") as d:
            root,planner,runner=self.fixture(d); before=planner.read_bytes()
            plan=preview_hourly_schedule(planner_path=planner,runner_path=runner)
            self.assertEqual(planner.read_bytes(),before)
            calls=[];loaded=True
            def command(*args):
                nonlocal loaded
                calls.append(args)
                if args[0]=='bootout':loaded=False
                elif args[0]=='bootstrap':loaded=True
                return subprocess.CompletedProcess(args,0 if loaded or args[0]!='print' else 113,b'',b'')
            with patch('app.family_calendar_delivery_hourly.load_family_calendar_delivery_config',return_value=SimpleNamespace(mode=DeliveryConfigMode.ENABLED)):
                result=apply_hourly_schedule(fingerprint=plan['fingerprint'],confirmation=HOURLY_CONFIRMATION,
                    global_confirmation=GLOBAL_CONFIRMATION,planner_path=planner,runner_path=runner,
                    worker_path=root/'worker.json',store_root=root/'receipts',command=command,runtime_ready=lambda:True)
            self.assertEqual(result['state'],'completed')
            doc=plistlib.loads(planner.read_bytes());self.assertEqual(len(doc['StartCalendarInterval']),16)
            self.assertTrue(doc['RunAtLoad']);self.assertTrue(_planner_document_matches(doc,runner))
            self.assertTrue((root/'receipts/policy.json').exists())
            self.assertEqual([c[0] for c in calls],['print','bootout','print','bootstrap','print'])

    def test_changed_plan_and_old_runtime_stop_before_mutation(self):
        with tempfile.TemporaryDirectory(dir="/private/tmp") as d:
            root,planner,runner=self.fixture(d);plan=preview_hourly_schedule(planner_path=planner,runner_path=runner)
            kw=dict(confirmation=HOURLY_CONFIRMATION,global_confirmation=GLOBAL_CONFIRMATION,planner_path=planner,
                    runner_path=runner,worker_path=root/'worker.json',store_root=root/'receipts',
                    command=lambda *_:self.fail('unexpected system call'))
            with self.assertRaises(ValueError):apply_hourly_schedule(fingerprint=plan['fingerprint'],runtime_ready=lambda:False,**kw)
            planner.write_bytes(planner.read_bytes()+b'\n')
            with self.assertRaises(ValueError):apply_hourly_schedule(fingerprint=plan['fingerprint'],runtime_ready=lambda:True,**kw)

    def test_uncertain_bootstrap_is_not_repeated(self):
        with tempfile.TemporaryDirectory(dir="/private/tmp") as d:
            root,planner,runner=self.fixture(d);plan=preview_hourly_schedule(planner_path=planner,runner_path=runner)
            calls=[];loaded=True
            def command(*args):
                nonlocal loaded
                calls.append(args[0])
                if args[0]=='bootout':loaded=False
                if args[0]=='bootstrap':raise TimeoutError()
                return subprocess.CompletedProcess(args,0 if loaded or args[0]!='print' else 113)
            kw=dict(fingerprint=plan['fingerprint'],confirmation=HOURLY_CONFIRMATION,global_confirmation=GLOBAL_CONFIRMATION,
                    planner_path=planner,runner_path=runner,worker_path=root/'worker.json',store_root=root/'receipts',
                    command=command,runtime_ready=lambda:True)
            with patch('app.family_calendar_delivery_hourly.load_family_calendar_delivery_config',return_value=SimpleNamespace(mode=DeliveryConfigMode.ENABLED)):
                result=apply_hourly_schedule(**kw)
                self.assertEqual(result['state'],'attention')
                with self.assertRaises(ValueError):apply_hourly_schedule(**kw)
            self.assertEqual(calls.count('bootstrap'),1)
            self.assertTrue((root/'receipts/policy.json').exists())

class PersonalCalendarSMSTests(unittest.TestCase):
    def setUp(self):
        from datetime import datetime
        from app.family_calendar import save_family_person
        from app.family_calendar_sms import CalendarSMS, TZ
        self.temp=tempfile.TemporaryDirectory(dir='/private/tmp');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.now=datetime(2026,12,18,9,tzinfo=TZ)
        self.people=self.root/'calendar/people.json'
        save_family_person(display_name='Testovací osoba', relation='příbuzná', birth_date='1990-12-18',
            name_day='12-18', path=self.people, today=self.now.date())
        from app.family_calendar_sms_transport import SMSOutcome
        class Adapter:
            def __init__(self):self.calls=[];self.preflight_calls=0;self.offline=False;self.fail=False
            def preflight(self):
                self.preflight_calls+=1
                if self.offline:raise OSError('synthetic unavailable')
                return 5
            def send(self,phone,text,anchor):
                self.calls.append((phone,text,anchor))
                if self.fail:raise OSError('synthetic lost reply')
                return SMSOutcome('sent',6)
        self.adapter=Adapter()
        self.service=CalendarSMS(self.root/'sms',people_path=self.people,adapter=self.adapter,clock=lambda:self.now)
        self.service.prepare(phone='+420700000001',salutation='paní Příkladová')

    def active(self):
        from app.family_calendar_sms import policy,digest
        from app.file_persistence import atomic_write_json
        value=self.service._config();value.update(enabled=True,authorization=digest(policy(value)))
        atomic_write_json(self.service.config_path,value)

    def test_disabled_preview_is_private_read_only_and_create_never_overwrites(self):
        before=self.service.repo.path.read_bytes();view=self.service.preview();status=self.service.tick()
        self.assertFalse(view['enabled']);self.assertFalse(view['test_verified']);self.assertEqual(view['today_count'],2)
        self.assertFalse(status['transport_called']);self.assertEqual(self.adapter.calls,[])
        self.assertEqual(self.service.repo.path.read_bytes(),before)
        text=json.dumps([view,status]);self.assertNotIn('700000001',text);self.assertNotIn('Příkladová',text);self.assertNotIn('Testovací',text)
        with self.assertRaises(ValueError):self.service.prepare(phone='+420700000002',salutation='jiná osoba')

    def test_nine_oclock_both_event_types_and_later_checks_send_only_once(self):
        self.active();self.now=self.now.replace(hour=8,minute=59)
        self.assertEqual(self.service.tick()['status'],'before_09');self.assertEqual(self.adapter.preflight_calls,0)
        self.now=self.now.replace(hour=9,minute=0);self.assertTrue(self.service.tick()['transport_called'])
        self.assertEqual(len(self.adapter.calls),2)
        texts=[v[1] for v in self.adapter.calls]
        self.assertIn('Speciálně pro Vás paní Příkladová: Dnes má narozeniny Testovací osoba (příbuzná).',texts)
        self.assertTrue(any('Dnes má svátek' in t for t in texts))
        before=self.service.repo.path.read_bytes();self.now=self.now.replace(hour=16)
        self.assertFalse(self.service.tick()['transport_called']);self.assertEqual(len(self.adapter.calls),2)
        self.assertEqual(before,self.service.repo.path.read_bytes())

    def test_sleep_catchup_same_day_but_not_yesterday_or_next_year_duplicates(self):
        self.active();self.now=self.now.replace(hour=17);self.service.tick();self.assertEqual(len(self.adapter.calls),2)
        self.now=self.now.replace(day=19);self.service.tick();self.assertEqual(len(self.adapter.calls),2)
        self.now=self.now.replace(year=2027,day=18);self.service.tick();self.assertEqual(len(self.adapter.calls),4)

    def test_prague_time_and_reminders_opt_out(self):
        from datetime import timezone
        self.active();self.now=self.now.astimezone(timezone.utc).replace(hour=7,minute=59)
        self.assertEqual(self.service.tick()['status'],'before_09')
        self.now=self.now.replace(hour=8,minute=0);self.service.tick();self.assertEqual(len(self.adapter.calls),2)
        from app.family_calendar import save_family_person,load_family_people
        person=load_family_people(self.people)[0]
        save_family_person(person_id=person.person_id,display_name=person.display_name,birth_date='1990-12-18',
            name_day='12-18',reminders_enabled=False,path=self.people,today=self.now.date())
        self.now=self.now.replace(year=2027);self.service.tick();self.assertEqual(len(self.adapter.calls),2)

    def test_midnight_during_preflight_cannot_send_yesterdays_event(self):
        from datetime import timedelta
        self.active();self.now=self.now.replace(hour=23,minute=59)
        def wake_late():self.now+=timedelta(minutes=2);return 5
        self.adapter.preflight=wake_late
        self.assertFalse(self.service.tick()['transport_called']);self.assertEqual(self.adapter.calls,[])

    def test_summer_timezone_uses_prague_nine_and_naive_time_is_unverified(self):
        from datetime import timezone
        from app.family_calendar import save_family_person,load_family_people
        person=load_family_people(self.people)[0]
        save_family_person(person_id=person.person_id,display_name=person.display_name,birth_date='1990-06-18',
            name_day='06-18',path=self.people,today=self.now.date())
        self.active();self.now=self.now.replace(month=6,hour=7,tzinfo=timezone.utc)
        self.service.tick();self.assertEqual(len(self.adapter.calls),2)
        self.now=self.now.replace(tzinfo=None)
        self.assertEqual(self.service.tick()['status'],'unverified')

    def test_sleep_during_intent_write_does_not_start_yesterdays_sms(self):
        from datetime import timedelta
        self.active();self.now=self.now.replace(hour=23,minute=59)
        original=self.service.repo.transact
        def wake_late(*args,**kwargs):
            result=original(*args,**kwargs)
            self.now+=timedelta(minutes=2)
            return result
        with patch.object(self.service.repo,'transact',side_effect=wake_late):
            result=self.service.tick()
        self.assertFalse(result['transport_called']);self.assertTrue(result['writes_performed'])
        self.assertEqual(self.adapter.calls,[])
        self.assertEqual(self.service.status()['counts']['not_sent'],1)

    def test_clock_rollback_before_nine_cancels_intent_without_false_send_claim(self):
        self.active();original=self.service.repo.transact;calls=0
        def rollback(*args,**kwargs):
            nonlocal calls
            calls+=1
            if calls==2:raise OSError('synthetic cancellation write failure')
            result=original(*args,**kwargs);self.now=self.now.replace(hour=8)
            return result
        with patch.object(self.service.repo,'transact',side_effect=rollback):
            result=self.service.tick()
        self.assertEqual(result['status'],'unverified');self.assertFalse(result['transport_called'])
        self.assertEqual(self.adapter.calls,[])
        self.assertEqual(self.service.status()['counts']['sending'],1)

    def test_proven_preflight_failure_can_retry_after_an_hour_only(self):
        from datetime import timedelta
        self.active();self.adapter.offline=True
        first=self.service.tick();self.assertFalse(first['transport_called']);self.assertTrue(first['writes_performed'])
        self.assertEqual(first['attention_count'],2)
        self.assertEqual(self.adapter.preflight_calls,2)
        self.now+=timedelta(minutes=30);self.service.tick();self.assertEqual(self.adapter.preflight_calls,2)
        self.adapter.offline=False;self.now+=timedelta(minutes=31);self.service.tick();self.assertEqual(len(self.adapter.calls),2)

    def test_lost_reply_and_restart_never_repeat_an_uncertain_sms(self):
        from app.family_calendar_sms import CalendarSMS
        self.active();self.adapter.fail=True
        self.assertTrue(self.service.tick()['transport_called']);self.assertEqual(len(self.adapter.calls),2)
        self.assertEqual(self.service.status()['attention_count'],2)
        again=CalendarSMS(self.service.root,people_path=self.people,adapter=self.adapter,clock=lambda:self.now)
        again.tick();self.assertEqual(len(self.adapter.calls),2)

    def test_crash_after_intent_stays_sending_and_is_not_replayed(self):
        self.active()
        def crash(*args):self.adapter.calls.append(args);raise SystemExit('synthetic process crash')
        self.adapter.send=crash
        with self.assertRaises(SystemExit):self.service.tick()
        self.assertEqual(self.service.status()['counts']['sending'],1)
        # Recheck skips the first record. A different event may still be attempted.
        from app.family_calendar_sms_transport import SMSOutcome
        self.adapter.send=lambda *args:SMSOutcome('sent',6)
        self.service.tick();self.assertEqual(len(self.adapter.calls),1)
        self.assertEqual(self.service.status()['counts']['sending'],1)

    def test_completion_storage_failure_is_unknown_and_cannot_resend(self):
        self.active();original=self.service.repo.transact;calls=0
        def write(*args,**kwargs):
            nonlocal calls
            calls+=1
            if calls==2:raise OSError('synthetic write failure after send')
            return original(*args,**kwargs)
        with patch.object(self.service.repo,'transact',side_effect=write):result=self.service.tick()
        self.assertEqual(result['status'],'unverified');self.assertTrue(result['transport_called'])
        self.assertEqual(self.service.status()['counts']['sending'],1)
        self.assertEqual(len(self.adapter.calls),1)
        self.service.tick();self.assertEqual(len(self.adapter.calls),2)
        self.service.tick();self.assertEqual(len(self.adapter.calls),2)

    def test_failed_intent_and_corrupt_or_missing_history_never_send_or_overwrite(self):
        self.active()
        with patch.object(self.service.repo,'transact',side_effect=OSError('synthetic before intent')):
            self.assertEqual(self.service.tick()['status'],'unverified')
        self.assertEqual(self.adapter.calls,[])
        self.service.repo.path.write_text('{broken')
        self.assertEqual(self.service.tick()['status'],'unverified');self.assertEqual(self.service.repo.path.read_text(),'{broken')
        self.assertEqual(self.adapter.calls,[])
        self.service.repo.path.rename(self.service.root/'preserved-history.json')
        self.assertEqual(self.service.tick()['status'],'unverified');self.assertEqual(self.adapter.calls,[])

    def test_changed_private_policy_invalidates_durable_consent(self):
        from app.file_persistence import atomic_write_json
        self.active();config=self.service._config();config['phone']='+420700000002'
        atomic_write_json(self.service.config_path,config)
        self.assertEqual(self.service.tick()['status'],'unverified');self.assertEqual(self.adapter.calls,[])

    def test_exact_test_and_enable_are_separate_and_test_replay_is_inert(self):
        from app.family_calendar_sms import TEST_CONFIRMATION,ENABLE_CONFIRMATION
        fingerprint=self.service.preview()['fingerprint']
        with self.assertRaises(ValueError):self.service.test(fingerprint=fingerprint,confirmation='',request_id='test-id-001')
        with self.assertRaises(ValueError):self.service.enable(fingerprint=fingerprint,confirmation=ENABLE_CONFIRMATION)
        self.assertEqual(self.adapter.calls,[])
        for _ in range(2):self.service.test(fingerprint=fingerprint,confirmation=TEST_CONFIRMATION,request_id='test-id-001')
        self.assertEqual(len(self.adapter.calls),1);self.assertFalse(self.service.status()['enabled'])
        with patch('app.family_calendar_delivery_hourly.hourly_schedule_active',return_value=True),patch('app.communication.luna_release.http_call',side_effect=[{'ready':True,'expected_code_stamp':'same'},{'server':{'code_stamp':'same'}}]):
            self.assertTrue(self.service.enable(fingerprint=fingerprint,confirmation=ENABLE_CONFIRMATION)['enabled'])
        self.assertEqual(len(self.adapter.calls),1)
        self.service.disable(confirmed=True);self.assertFalse(self.service.status()['enabled'])

    def test_uncertain_test_cannot_be_repeated_by_changing_request_id(self):
        from app.family_calendar_sms import TEST_CONFIRMATION,ENABLE_CONFIRMATION
        self.adapter.fail=True;fp=self.service.preview()['fingerprint']
        self.service.test(fingerprint=fp,confirmation=TEST_CONFIRMATION,request_id='test-unknown-001')
        with self.assertRaises(ValueError):self.service.test(fingerprint=fp,confirmation=TEST_CONFIRMATION,request_id='test-unknown-002')
        with self.assertRaises(ValueError):self.service.enable(fingerprint=fp,confirmation=ENABLE_CONFIRMATION)
        self.assertEqual(len(self.adapter.calls),1)

    def test_concurrent_ticks_have_a_single_owner(self):
        import threading
        from app.family_calendar_sms import CalendarSMS
        from app.family_calendar_sms_transport import SMSOutcome
        self.active();entered=threading.Event();release=threading.Event()
        def sending(*args):
            self.adapter.calls.append(args);entered.set();release.wait(3);return SMSOutcome('sent',6)
        self.adapter.send=sending
        with ThreadPoolExecutor(2) as pool:
            future=pool.submit(self.service.tick);self.assertTrue(entered.wait(3))
            other=CalendarSMS(self.service.root,people_path=self.people,adapter=self.adapter,clock=lambda:self.now)
            self.assertEqual(other.tick()['status'],'busy');release.set();future.result()
        self.assertEqual(len(self.adapter.calls),2)

    def test_original_test_can_be_verified_without_another_send(self):
        from app.family_calendar_sms import TEST_CONFIRMATION
        from app.family_calendar_sms_transport import SMSOutcome
        fp=self.service.preview()['fingerprint'];self.adapter.fail=True
        self.service.test(fingerprint=fp,confirmation=TEST_CONFIRMATION,request_id='original-test-001')
        self.adapter.verify=Mock(return_value=SMSOutcome('delivered',6,'RCS'))
        with self.assertRaises(ValueError):
            self.service.verify_test(fingerprint='changed',request_id='original-test-001',confirmed=True)
        result=self.service.verify_test(fingerprint=fp,request_id='original-test-001',confirmed=True)
        self.assertFalse(result['transport_called']);self.assertEqual(result['counts']['delivered'],1)
        self.assertTrue(self.service.preview()['test_verified'])
        self.service.verify_test(fingerprint=fp,request_id='original-test-001',confirmed=True)
        self.adapter.verify.assert_called_once()
        self.service.test(fingerprint=fp,confirmation=TEST_CONFIRMATION,request_id='original-test-001')
        self.assertEqual(len(self.adapter.calls),1)
        self.assertFalse(self.service.status()['enabled'])

    def test_owned_dispatch_runs_sms_even_if_email_fails_and_never_on_replay_arguments(self):
        import io
        from scripts.family_calendar_delivery_run import scheduled_main
        sms=Mock(return_value={'status':'disabled','transport_called':False})
        def email(*args,**kwargs):raise OSError('synthetic email error')
        output=io.StringIO();self.assertEqual(scheduled_main([],email_runner=email,sms_runner=sms,output=output),1)
        self.assertEqual(json.loads(output.getvalue())['sms']['status'],'disabled');sms.assert_called_once()
        sms.reset_mock()
        self.assertEqual(scheduled_main(['--today','2020-01-01'],email_runner=lambda *a,**k:7,sms_runner=sms,output=io.StringIO()),7)
        sms.assert_not_called()

    def test_registered_agent_tools_return_json_and_never_repeat_uncertain_test(self):
        import asyncio
        from agents.tool_context import ToolContext
        from app.samantha_agent import family_calendar_sms_status,family_calendar_sms_preview,family_calendar_sms_control
        from app.family_calendar_sms import SMSAttemptError
        with patch('app.family_calendar_sms.CalendarSMS') as factory:
            service=factory.return_value
            service.status.return_value={'status':'disabled'}
            service.preview.return_value={'enabled':False,'fingerprint':'synthetic'}
            service.test.return_value={'status':'disabled','transport_called':True}
            service.enable.return_value={'status':'active'}
            service.disable.return_value={'status':'disabled'}
            service.verify_test.return_value={'status':'disabled','transport_called':False}
            for tool,args in [(family_calendar_sms_status,{}),(family_calendar_sms_preview,{}),
                              *[(family_calendar_sms_control,{'action':a}) for a in ('test','enable','disable','verify')]]:
                context=ToolContext(context=None,tool_name=tool.name,tool_call_id='synthetic-call',tool_arguments=json.dumps(args))
                value=json.loads(asyncio.run(tool.on_invoke_tool(context,json.dumps(args))))
                self.assertIsInstance(value,dict)
            service.test.assert_called_once()
            service.test.side_effect=SMSAttemptError('PRIVATE',transport_called=False)
            value=json.loads(asyncio.run(family_calendar_sms_control.on_invoke_tool(context,json.dumps({'action':'test'}))))
            self.assertEqual(value['status'],'unverified');self.assertFalse(value['transport_called'])
            self.assertNotIn('PRIVATE',json.dumps(value))


if __name__=='__main__':unittest.main()
