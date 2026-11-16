from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
import json
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch
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

if __name__=='__main__':unittest.main()
