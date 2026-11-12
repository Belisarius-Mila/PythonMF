from __future__ import annotations

import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
import subprocess
import sys
from unittest.mock import patch

from app.communication.human_adam_work import (
    WorkController, WorkStore, WorkReservation, WorkConflict, WorkError,
    normalized_request, operation_id, MAX_EVENTS,
)
from app.communication.session_hub import SessionBusyError
from app.file_persistence import atomic_write_json


class WorkTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.store = WorkStore(self.root / "work")
        self.payload = normalized_request({"text": "PRIVATE accepted instruction", "client_message_id": "request-0001"})
        self.scope = {"workstream_id": "project-a", "profile_id": "human_adam",
                      "thread_id": "thread-a", "connection_generation": 1}
        self.session = self.root / "session.json"

    def admit(self, owner="owner-a"):
        return self.store.admit(self.payload, self.scope, owner, session_path=self.session)[0]

    def test_absent_lookup_is_inert(self):
        self.assertEqual(self.store.recent("project-a"), [])
        self.assertIsNone(self.store.load(operation_id("project-a", "request-0001")))
        self.assertFalse((self.root / "work").exists())

    def test_acceptance_has_durable_identity_and_no_private_projection(self):
        record = self.admit()
        again, created = self.store.admit(self.payload, self.scope, "owner-b", session_path=self.session)
        self.assertFalse(created)
        self.assertEqual(record["operation_id"], again["operation_id"])
        self.assertEqual(again["owner_generation"], "owner-a")
        public = self.store.public(again, owned=False)
        self.assertEqual(public["lifecycle_state"], "unverified")
        self.assertEqual(public["delivery_state"], "not_started")
        self.assertNotIn("PRIVATE", json.dumps(public))
        self.assertNotIn(str(self.root), json.dumps(public))
        self.assertFalse(public["capabilities"]["replay"])

    def test_changed_text_or_authorization_never_reuses_identity(self):
        record = self.admit()
        before = self.store.repository(record["operation_id"]).path.read_bytes()
        for change in ({"text": "different"}, {"write_intent": True}):
            with self.assertRaises(WorkConflict):
                self.store.admit({**self.payload, **change}, self.scope, "owner-a", session_path=self.session)
        self.assertEqual(before, self.store.repository(record["operation_id"]).path.read_bytes())

    def test_cursor_gap_and_future_cursor_require_resync(self):
        record = self.admit(); identity = record["operation_id"]
        for _ in range(MAX_EVENTS + 10):
            self.store.change(identity, "owner-a", "tool_started")
        current = self.store.load(identity)
        self.assertEqual(len(current["events"]), MAX_EVENTS)
        for cursor in (1, current["revision"] + 1):
            view = self.store.public(current, cursor=cursor, owned=True)
            self.assertTrue(view["resync_required"]); self.assertEqual(view["events"], [])
        view = self.store.public(current, cursor=current["revision"] - 1, owned=True)
        self.assertFalse(view["resync_required"]); self.assertEqual(len(view["events"]), 1)

    def test_terminal_is_absorbing_and_wire_replay_or_foreign_generation_is_ignored(self):
        identity = self.admit()["operation_id"]
        first = self.store.change(identity, "owner-a", "tool_started", wire=("wire-a", 7))
        for wire in (("wire-a", 7), ("wire-a", 6), ("wire-b", 8)):
            self.assertEqual(first["revision"], self.store.change(identity, "owner-a", "tool_started", wire=wire)["revision"])
        with self.assertRaises(WorkConflict):
            self.store.change(identity, "other-owner", "model_started")
        done = self.store.change(identity, "owner-a", "finished", fields={"lifecycle_state": "completed", "delivery_state": "confirmed"})
        late = self.store.change(identity, "owner-a", "late", fields={"lifecycle_state": "running"})
        self.assertEqual(done, late)
        self.assertNotIn("_accepted_input", done)

    def controller_fixture(self, *, completion_reader=None):
        controller = WorkController(self.root / "work", completion_reader=completion_reader)
        self.addCleanup(controller.close)
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(lambda: [h.thread.join(3) for h in list(controller._handles.values()) if h.thread])
        self.addCleanup(release.set)
        calls, released = [], []
        def execute(observer):
            # Store/barrier precedes the simulated only model call.
            observer.dispatching(); observer.accepted("turn-a")
            calls.append(1); entered.set(); release.wait(3)
            entry = {"client_message_id": "request-0001", "thread_id": "thread-a", "turn_id": "turn-a",
                     "status": "completed", "delivery_confirmed": True, "answer": "PRIVATE final"}
            atomic_write_json(self.session, {"messages": [entry]})
            return {"ok": True, "entry": entry}
        def reserve():
            return WorkReservation(self.scope, self.session, execute, lambda: released.append(1))
        return controller, reserve, entered, release, calls, released

    def test_reload_lookup_and_two_clients_share_one_worker_and_one_dispatch(self):
        c, reserve, entered, release, calls, released = self.controller_fixture()
        response = c.submit("project-a", self.payload, reserve)
        self.assertTrue(entered.wait(2)); identity = response["operations"][0]["operation_id"]
        duplicate = c.submit("project-a", self.payload, lambda: self.fail("must not reserve again"))
        self.assertEqual(identity, duplicate["operations"][0]["operation_id"])
        self.assertTrue(duplicate["duplicate_prevented"])
        fresh_reader = WorkController(self.root / "work")
        self.assertEqual(fresh_reader.view("project-a", client_message_id="request-0001")["operations"][0]["operation_id"], identity)
        with self.assertRaises(SessionBusyError):
            fresh_reader.submit("project-b", {**self.payload, "client_message_id": "request-0002"}, reserve)
        release.set()
        result = c.submit("project-a", self.payload, reserve, wait=True)
        self.assertTrue(result["ok"]); self.assertEqual(len(calls), 1); self.assertEqual(released, [1])

    def test_read_only_restart_recovery_uses_existing_proof_and_never_dispatches(self):
        c, reserve, entered, release, calls, _ = self.controller_fixture()
        response = c.submit("project-a", self.payload, reserve)
        self.assertTrue(entered.wait(2)); identity = response["operations"][0]["operation_id"]
        other = WorkController(self.root / "work")
        with self.assertRaises(SessionBusyError):
            other.recover("project-a", identity)
        release.set(); c.submit("project-a", self.payload, reserve, wait=True)
        before = self.store.repository(identity).path.read_bytes()
        self.assertEqual(other.recover("project-a", identity)["operations"][0]["lifecycle_state"], "completed")
        self.assertEqual(before, self.store.repository(identity).path.read_bytes()); self.assertEqual(calls, [1])

    def test_restart_before_dispatch_is_proven_not_started_without_replaying(self):
        record = self.admit()
        c = WorkController(self.root / "work")
        view = c.recover("project-a", record["operation_id"])["operations"][0]
        self.assertEqual(view["lifecycle_state"], "not_dispatched")
        self.assertEqual(view["delivery_state"], "not_started")
        duplicate = c.submit("project-a", self.payload, lambda: self.fail("no restart dispatch"))
        self.assertEqual(duplicate["operations"][0]["operation_id"], record["operation_id"])

    def test_restart_after_dispatch_without_source_stays_unverified(self):
        record = self.admit(); identity = record["operation_id"]
        self.store.change(identity, "owner-a", "dispatch", fields={"lifecycle_state": "running", "_dispatch_started": True})
        c = WorkController(self.root / "work")
        first = c.view("project-a", identity=identity)["operations"][0]
        self.assertEqual(first["lifecycle_state"], "unverified")
        restored = c.recover("project-a", identity)["operations"][0]
        self.assertEqual(restored["lifecycle_state"], "unverified")
        with self.assertRaises(WorkError):
            c.view("project-b", identity=identity)

    def test_recovery_needs_exact_canonical_identity_and_delivery_proof(self):
        identity = self.admit()["operation_id"]
        self.store.change(identity, "owner-a", "dispatch", fields={"lifecycle_state": "running", "_dispatch_started": True,
                                                                   "turn_id": "turn-a"})
        c = WorkController(self.root / "work")
        entry = {"client_message_id": "request-0001", "thread_id": "thread-a", "turn_id": "turn-a",
                 "status": "completed", "delivery_confirmed": True}
        for bad in ({"client_message_id": "other"}, {"thread_id": "other"}, {"turn_id": "other"}, {"delivery_confirmed": False}):
            atomic_write_json(self.session, {"messages": [{**entry, **bad}]})
            self.assertEqual(c.recover("project-a", identity)["operations"][0]["lifecycle_state"], "unverified")
        atomic_write_json(self.session, {"messages": [entry]})
        self.assertEqual(c.recover("project-a", identity)["operations"][0]["lifecycle_state"], "completed")

    def test_model_completion_does_not_hide_running_server_completion(self):
        completion = {"kind": "completion", "job_id": "exact-job", "state": "running"}
        c, reserve, entered, release, _, _ = self.controller_fixture(completion_reader=lambda _: dict(completion))
        result = c.submit("project-a", self.payload, reserve); self.assertTrue(entered.wait(2)); release.set()
        c.submit("project-a", self.payload, reserve, wait=True)
        identity = result["operations"][0]["operation_id"]
        view = c.view("project-a", identity=identity)["operations"][0]
        self.assertEqual(view["lifecycle_state"], "awaiting_completion"); self.assertEqual(view["delivery_state"], "confirmed")
        completion["state"] = "completed"
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline and c.view("project-a", identity=identity)["operations"][0]["lifecycle_state"] != "completed":
            time.sleep(.01)
        self.assertEqual(c.view("project-a", identity=identity)["operations"][0]["lifecycle_state"], "completed")

    def test_acceptance_write_failure_cannot_dispatch(self):
        c, reserve, _, _, calls, released = self.controller_fixture()
        with patch.object(c.store.index, "transact", side_effect=OSError("PRIVATE storage")):
            with self.assertRaises(OSError):
                c.submit("project-a", self.payload, reserve)
        self.assertEqual(calls, []); self.assertEqual(released, [1])
        # Durable first record survives an index-write failure and prevents replay.
        result = c.submit("project-a", self.payload, lambda: self.fail("no new intent"))
        self.assertTrue(result["duplicate_prevented"])

    def test_missing_completion_telemetry_does_not_erase_delivered_answer(self):
        def unavailable(_):
            raise OSError("PRIVATE unavailable completion")
        c, reserve, entered, release, _, _ = self.controller_fixture(completion_reader=unavailable)
        response = c.submit("project-a", self.payload, reserve); self.assertTrue(entered.wait(2)); release.set()
        result = c.submit("project-a", self.payload, reserve, wait=True)
        self.assertTrue(result["entry"]["delivery_confirmed"])
        view = c.view("project-a", identity=response["operations"][0]["operation_id"])["operations"][0]
        self.assertEqual(view["delivery_state"], "confirmed")
        self.assertEqual(view["lifecycle_state"], "unverified")

    def test_observer_buffers_only_safe_metadata_until_exact_ack(self):
        from types import SimpleNamespace
        from app.communication.human_adam_work_observer import WorkObserver
        identity = self.admit()["operation_id"]
        observer = WorkObserver(self.store, identity, "owner-a")
        def event(turn, seq):
            return SimpleNamespace(params={"item": {"type": "commandExecution", "command": "TOOL_SECRET",
                                                    "output": "RAW_REASONING"}}, kind="item_started",
                                   method="item/started", thread_id="thread-a", turn_id=turn,
                                   generation="wire-a", received_sequence=seq)
        observer._event(event("other-turn", 1)); observer._event(event("turn-a", 2))
        self.assertEqual(self.store.load(identity)["revision"], 1)
        observer.dispatching(); observer.accepted("turn-a")
        observer._event(event("turn-a", 3)); observer._event(event("turn-a", 3))
        current = self.store.load(identity)
        self.assertEqual([e["kind"] for e in current["events"]].count("tool_started"), 2)
        self.assertNotIn("TOOL_SECRET", json.dumps(current)); self.assertNotIn("RAW_REASONING", json.dumps(current))
        observer.close()
        before = self.store.load(identity)["revision"]
        observer._event(event("turn-a", 4))
        self.assertEqual(self.store.load(identity)["revision"], before)

    def test_shutdown_and_read_projections_never_dispatch(self):
        c, reserve, entered, release, calls, _ = self.controller_fixture()
        result = c.submit("project-a", self.payload, reserve); self.assertTrue(entered.wait(2))
        c.close()
        with self.assertRaises(WorkError):
            c.submit("project-a", {**self.payload, "client_message_id": "request-0002"}, reserve)
        self.assertEqual(c.view("project-a", identity=result["operations"][0]["operation_id"])["operations"][0]["lifecycle_state"], "unverified")
        release.set(); self.assertEqual(calls, [1])

    def test_worker_launch_failure_releases_guards_and_never_hangs_on_duplicate(self):
        c, reserve, _, _, calls, released = self.controller_fixture()
        with patch('threading.Thread.start', side_effect=RuntimeError('synthetic worker unavailable')):
            with self.assertRaises(RuntimeError): c.submit('project-a', self.payload, reserve)
        identity=operation_id('project-a','request-0001')
        self.assertEqual(calls,[]);self.assertEqual(released,[1])
        self.assertEqual(c.recover('project-a',identity)['operations'][0]['lifecycle_state'],'not_dispatched')
        from app.communication.session_hub import SessionDeliveryUnknownError
        with self.assertRaises(SessionDeliveryUnknownError):
            c.submit('project-a',self.payload,reserve,wait=True)

    def test_process_crash_after_dispatch_keeps_original_identity_without_replay(self):
        source='''
import sys,threading
from pathlib import Path
from app.communication.human_adam_work import WorkController,WorkReservation
root=Path(sys.argv[1]);c=WorkController(root/'work')
def execute(observer):
    observer.dispatching();observer.accepted('turn-a')
    (root/'model-call-count').write_text('1')
    print('READY',flush=True);threading.Event().wait()
scope={'workstream_id':'project-a','profile_id':'human_adam','thread_id':'thread-a','connection_generation':1}
c.submit('project-a',{'text':'PRIVATE accepted instruction','client_message_id':'request-0001'},lambda:WorkReservation(scope,root/'session.json',execute,lambda:None))
threading.Event().wait()
'''
        process=subprocess.Popen([sys.executable,'-u','-c',source,str(self.root)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        def cleanup():
            if process.poll() is None:process.terminate();process.wait(5)
            process.stdout.close();process.stderr.close()
        self.addCleanup(cleanup)
        import select
        self.assertTrue(select.select([process.stdout],[],[],5)[0])
        self.assertEqual(process.stdout.readline().strip(),'READY')
        process.terminate();process.wait(5)
        restarted=WorkController(self.root/'work')
        identity=operation_id('project-a','request-0001')
        restored=restarted.recover('project-a',identity)
        self.assertEqual(restored['operations'][0]['lifecycle_state'],'unverified')
        restarted.submit('project-a',self.payload,lambda:self.fail('no replay after process crash'))
        self.assertEqual((self.root/'model-call-count').read_text(),'1')

    def test_recent_compaction_keeps_durable_identity_and_prunes_private_input(self):
        ids=[]
        with patch('app.communication.human_adam_work.MAX_RECENT',2):
            for n in range(3):
                payload={**self.payload,'client_message_id':f'request-000{n}'}
                record,_=self.store.admit(payload,self.scope,'owner-a',session_path=self.session)
                ids.append(record['operation_id'])
                self.store.change(ids[-1],'owner-a','finished',fields={'lifecycle_state':'not_dispatched'})
            self.assertEqual(len(self.store.recent('project-a')),2)
        old=self.store.load(ids[0]);self.assertNotIn('_accepted_input',old)
        replay,created=self.store.admit({**self.payload,'client_message_id':'request-0000'},self.scope,'owner-b',session_path=self.session)
        self.assertFalse(created);self.assertEqual(replay['operation_id'],ids[0])

    def test_new_server_build_does_not_turn_readback_into_new_intent(self):
        record=self.admit()
        again,created=self.store.admit({**self.payload,'observed_code_stamp':'new-server-build'},self.scope,'owner-b',session_path=self.session)
        self.assertFalse(created);self.assertEqual(again['operation_id'],record['operation_id'])

    def test_gap_marker_requests_one_resync_then_allows_same_cursor_to_continue(self):
        identity=self.admit()['operation_id']
        changed=self.store.change(identity,'owner-a','event_gap',fields={'event_gap':True})
        before=self.store.public(changed,cursor=1,owned=True)
        self.assertTrue(before['resync_required'])
        current=self.store.public(changed,cursor=changed['revision'],owned=True)
        self.assertFalse(current['resync_required']);self.assertEqual(current['events'],[])

    def test_missing_storage_or_corrupt_record_cannot_be_empty_success(self):
        identity=self.admit()['operation_id'];path=self.store.repository(identity).path
        record=json.loads(path.read_text());record['scope']['thread_id']={'raw':'PRIVATE'}
        path.write_text(json.dumps(record))
        from app.communication.human_adam_work import WorkUnavailable
        with self.assertRaises(WorkUnavailable):self.store.load(identity)

    def test_recovery_declares_projection_write_but_next_read_is_inert(self):
        record=self.admit();c=WorkController(self.root/'work')
        recovered=c.recover('project-a',record['operation_id'])
        self.assertTrue(recovered['writes_performed']);self.assertFalse(recovered['recovery']['redispatched'])
        before=self.store.repository(record['operation_id']).path.read_bytes()
        self.assertFalse(c.view('project-a',identity=record['operation_id'])['writes_performed'])
        self.assertEqual(before,self.store.repository(record['operation_id']).path.read_bytes())

    def test_changed_thread_is_rejected_before_subscription_or_dispatch(self):
        from unittest.mock import Mock
        from app.communication.human_adam_work_observer import WorkObserver
        identity=self.admit()['operation_id'];client=Mock()
        observer=WorkObserver(self.store,identity,'owner-a')
        with self.assertRaises(WorkConflict):
            with observer.attach(client,'other-thread'):self.fail('must not reach dispatch')
        client.subscribe_events.assert_not_called()
        self.assertFalse(self.store.load(identity)['_dispatch_started'])

    def test_shutdown_wakes_legacy_waiter_without_cancelling_or_replaying_model(self):
        from app.communication.session_hub import SessionDeliveryUnknownError
        c,reserve,entered,release,calls,_=self.controller_fixture()
        errors=[]
        def caller():
            try:c.submit('project-a',self.payload,reserve,wait=True)
            except Exception as error:errors.append(error)
        waiter=threading.Thread(target=caller);waiter.start();self.assertTrue(entered.wait(2))
        c.close();waiter.join(1)
        self.assertFalse(waiter.is_alive());self.assertIsInstance(errors[0],SessionDeliveryUnknownError)
        self.assertEqual(calls,[1]);release.set()

    def test_later_child_job_cannot_replace_the_original_completion_reference(self):
        completion={'kind':'completion','job_id':'original-job','state':'running'}
        c,reserve,entered,release,calls,_=self.controller_fixture(completion_reader=lambda _:dict(completion))
        result=c.submit('project-a',self.payload,reserve);self.assertTrue(entered.wait(2));release.set()
        c.submit('project-a',self.payload,reserve,wait=True)
        identity=result['operations'][0]['operation_id']
        completion.update(job_id='foreign-replacement',state='completed')
        c._handles[identity].thread.join(2)
        view=c.view('project-a',identity=identity)['operations'][0]
        self.assertEqual(view['completion']['job_id'],'original-job')
        self.assertEqual(view['lifecycle_state'],'unverified');self.assertEqual(calls,[1])
