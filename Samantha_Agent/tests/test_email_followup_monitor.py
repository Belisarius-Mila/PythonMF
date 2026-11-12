from __future__ import annotations

import copy
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from app.email.continuous_agent import ContinuousEmailAgent
from app.email.continuous_source import ObservedEmail
from app.email.followup_matching import header_evidence
from app.email.followup_monitor import EmailFollowupMonitor, next_slot
from app.email.followups import EmailFollowups, FollowupConflict, FollowupError
from app.email.hourly_agent import HourlyEmailScheduler, hourly_slot
from app.email.icloud_provider import _message_data_to_archive_source
from app.email.service import ServiceSettings, service_tick
from app.work_repository import JsonWorkRepository, RepositoryMutation
from tests.test_continuous_email_agent import FakeSource, proposal


def mail(uid="1", identity="root@example.test", parent="", references=(), *,
         sender="supplier@example.test", recipient="me@example.test", subject="Nabídka",
         account="account-a", validity="10", extra="", body="PRIVATE FULL BODY"):
    headers = ["From: " + sender, "To: " + recipient, "Subject: " + subject]
    if identity:
        headers.append("Message-ID: <" + identity + ">")
    if parent:
        headers.append("In-Reply-To: <" + parent + ">")
    if references:
        headers.append("References: " + " ".join("<" + v + ">" for v in references))
    raw = ("\r\n".join(headers) + "\r\n" + extra + "\r\n" + body).encode()
    source = _message_data_to_archive_source(uid, [(b"", raw)], None, max_message_bytes=len(raw))
    return ObservedEmail(account, validity, replace(source, provider="icloud"))


class FollowupHeaderTests(unittest.TestCase):
    def test_normalization_preserves_local_case_folds_domain_and_never_copies_body(self):
        value = header_evidence(mail(identity="AbC@EXAMPLE.TEST").source.original_eml)
        self.assertTrue(value["verified"])
        self.assertEqual(value["message_id"], "<AbC@example.test>")
        self.assertNotIn("PRIVATE FULL BODY", json.dumps(value))

    def test_missing_duplicate_malformed_and_oversized_ids_are_unverified(self):
        samples = [mail(identity=""), mail(extra="Message-ID: <other@example.test>\r\n"),
                   mail(identity="bad value@example.test"), mail(identity="x" * 66000 + "@example.test")]
        for sample in samples:
            with self.subTest(size=len(sample.source.original_eml)):
                self.assertFalse(header_evidence(sample.source.original_eml)["verified"])

    def test_multiple_senders_and_missing_recipients_cannot_establish_participants(self):
        self.assertFalse(header_evidence(mail(sender="a@example.test, b@example.test").source.original_eml)["verified"])
        self.assertFalse(header_evidence(mail(recipient="").source.original_eml)["verified"])

    def test_available_slot_respects_night_rounding_and_prague_dst(self):
        samples = {"2026-11-12T13:30:00+00:00": "2026-11-12T14:00:00+00:00",
                   "2026-11-12T21:30:00+00:00": "2026-11-13T06:00:00+00:00",
                   "2026-03-28T22:30:00+00:00": "2026-03-29T05:00:00+00:00",
                   "2026-10-24T21:30:00+00:00": "2026-10-25T06:00:00+00:00"}
        for start, expected in samples.items():
            self.assertEqual(next_slot(datetime.fromisoformat(start)).isoformat(), expected)


class FollowupMonitorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.worker = ContinuousEmailAgent(self.root / "agent")
        self.now = datetime(2026, 11, 12, 9, tzinfo=timezone.utc)
        clock = patch("app.email.continuous_agent._now", side_effect=lambda: self.now.isoformat())
        clock.start(); self.addCleanup(clock.stop)
        self.original = mail()
        self.ingest(self.original)
        self.manual = EmailFollowups(self.worker, clock=lambda: self.now)
        self.case = self.create(self.original)
        self.worker._update(lambda d: d["followups"].update(monitor={"version": 1, "enabled": True}))
        self.monitor = EmailFollowupMonitor(self.worker)

    def ingest(self, message, proposer=None):
        source = FakeSource([message]); source.key = message.account
        with patch("app.email.continuous_agent._now", side_effect=lambda: self.now.isoformat()):
            return self.worker.cycle(source, proposer or (lambda _: proposal()), cycle_at=self.now)

    def create(self, message, operation="create-root-0001"):
        return EmailFollowups(self.worker, clock=lambda: self.now).execute({"action": "create",
            "operation_id": operation, "source_item_id": message.item_id,
            "fields": {"title": "Získat nabídku", "goal": "Dostat úplný podklad", "next_step": "Čekáme",
                       "waiting_on": "other", "check_at": (self.now + timedelta(hours=1)).isoformat()}})["followup"]

    def value(self, identity=None):
        return self.manual.overview({"id": identity or self.case["id"]})["followup"]

    def due(self):
        self.now += timedelta(hours=2)

    def scan_empty(self):
        source = FakeSource([])
        return HourlyEmailScheduler(self.worker).tick([source], lambda _: self.fail("No new model"), now=self.now)

    def tick_service(self, **settings):
        path = self.root / "service.json"
        path.write_text(json.dumps({**ServiceSettings().model_dump(), "enabled": True,
                                   "providers": ["icloud"], **settings}))
        self.source = FakeSource([])
        self.select = Mock(return_value={"model": "fake", "reasoning_effort": "high"})
        return service_tick(settings_path=path, worker=self.worker, now=self.now,
            source_factory=lambda _: self.source, select_model=self.select,
            selection_validator=lambda *_a, **_kw: None,
            proposer_factory=lambda *_a, **_kw: lambda _: self.fail("No message to assess"))

    def test_disabled_default_is_inert_and_does_not_create_storage(self):
        worker = ContinuousEmailAgent(self.root / "absent")
        self.assertEqual(EmailFollowupMonitor(worker).check(now=self.now)["status"], "not_connected")
        self.assertFalse(worker.root.exists())
        self.worker._update(lambda d: d["followups"]["monitor"].update(enabled=False))
        before = self.worker.repository.path.read_bytes()
        self.ingest(mail("2", "disabled@example.test", "root@example.test"))
        self.assertNotIn("observations", self.value())
        self.assertFalse(self.manual.overview()["capabilities"]["automatic_monitoring"])

    def test_reply_with_changed_subject_is_admitted_before_failed_model_and_survives_filtering(self):
        response = mail("2", "reply@example.test", "root@example.test", subject="Jiný předmět")
        def failed(_):
            value = self.value()
            self.assertIn(response.item_id, value["observations"]["items"])
            raise TimeoutError("PRIVATE FAILURE")
        self.ingest(response, failed)
        value = self.value()
        self.assertIn(response.item_id, value["observations"]["items"])
        self.assertEqual(self.worker.status()["items"][response.item_id]["status"], "analysis_failed")
        self.assertEqual({k:value[k] for k in ("goal", "next_step", "waiting_on", "check_at", "state")},
                         {k:self.case[k] for k in ("goal", "next_step", "waiting_on", "check_at", "state")})
        self.assertNotIn("PRIVATE FULL BODY", json.dumps(value))
        detail = self.manual.overview({"id":value["id"], "item_id":response.item_id})
        self.assertIn("PRIVATE FULL BODY", detail["source_message"]["body_text"])

    def test_related_low_importance_body_stays_in_original_item_not_in_followup(self):
        response = mail("2", "reply@example.test", "root@example.test")
        self.ingest(response, lambda _: proposal().model_copy(update={"important":False}))
        self.assertEqual(self.worker.status()["items"][response.item_id]["status"], "hourly_summary")
        self.assertIn(response.item_id, self.value()["observations"]["items"])
        self.assertNotIn("PRIVATE FULL BODY", json.dumps(self.worker.status()["followups"]))
        self.assertTrue(self.manual.overview({"id":self.case["id"], "item_id":response.item_id})["source_message"])

    def test_subject_only_missing_id_new_participant_and_conflicting_parent_are_manual(self):
        samples = [mail("2", "unrelated@example.test"), mail("2", "", "root@example.test"),
                   mail("2", "reply@example.test", "root@example.test", sender="new@example.test"),
                   mail("2", "reply@example.test", "other@example.test", ("root@example.test",))]
        original = self.worker.repository.path.read_bytes()
        for response in samples:
            with self.subTest(response=response.source.sender):
                self.worker.repository.path.write_bytes(original)
                self.ingest(response)
                value = self.value()
                self.assertFalse(value["observations"]["items"])
                self.assertIn(response.item_id, value["observations"]["reviews"])

    def test_another_account_with_same_uid_and_ids_never_links(self):
        self.ingest(mail("2", "reply@example.test", "root@example.test", account="account-b"))
        self.assertNotIn("observations", self.value())

    def test_duplicate_message_id_is_manual_even_with_exact_parent(self):
        self.ingest(mail("2", "root@example.test", "root@example.test"))
        value = self.value()
        self.assertFalse(value["observations"]["items"])
        self.assertEqual(next(iter(value["observations"]["reviews"].values()))["decision"], "duplicate_message_id")

    def test_references_to_two_matters_do_not_merge_them(self):
        other = mail("2", "other@example.test", subject="Druhá věc")
        self.ingest(other); second = self.create(other, "create-other-0001")
        response = mail("3", "reply@example.test", references=("root@example.test", "other@example.test"))
        self.ingest(response)
        for identity in (self.case["id"], second["id"]):
            value = self.value(identity)
            self.assertIn(response.item_id, value["observations"]["reviews"])
            self.assertFalse(value["observations"]["items"])

    def test_reply_chain_uses_previously_bound_child_id(self):
        self.ingest(mail("2", "first@example.test", "root@example.test"))
        self.ingest(mail("3", "second@example.test", "first@example.test", subject="Další téma"))
        self.assertEqual(len(self.value()["observations"]["items"]), 2)

    def test_references_to_active_and_closed_matters_stay_manual_without_reopening(self):
        other=mail("2","other@example.test",subject="Druhá věc")
        self.ingest(other);second=self.create(other,"create-other-0001")
        done=self.manual.execute({"action":"set_state","id":second["id"],"expected_revision":second["revision"],
            "operation_id":"complete-other-0001","state":"completed"})["followup"]
        response=mail("3","reply@example.test",references=("root@example.test","other@example.test"))
        self.ingest(response)
        self.assertEqual(self.value()["observations"]["reviews"][response.item_id]["decision"],"ambiguous_thread")
        self.assertEqual(self.value(second["id"])["revision"],done["revision"])

    def test_linked_message_cannot_create_a_duplicate_matter(self):
        response = mail("2", "reply@example.test", "root@example.test")
        self.ingest(response)
        with self.assertRaises(FollowupConflict):
            self.create(response, "create-duplicate-0001")

    def test_related_detail_cannot_read_an_unrelated_or_replaced_source(self):
        response = mail("2", "reply@example.test", "root@example.test")
        self.ingest(response)
        with self.assertRaises(FollowupError):
            self.manual.overview({"id":self.case["id"], "item_id":"f"*64})
        self.worker._update(lambda d:d["items"][response.item_id].update(content_digest="0"*64))
        self.assertIsNone(self.manual.overview({"id":self.case["id"], "item_id":response.item_id})["source_message"])

    def test_empty_inbox_due_check_and_restart_preserve_one_notice(self):
        self.due(); self.scan_empty()
        self.assertEqual(self.monitor.check(now=self.now)["checked"], 1)
        first = self.value()
        self.assertEqual(first["tracking"]["status"], "due_no_observed_reply")
        before = self.worker.repository.path.read_bytes()
        self.assertEqual(EmailFollowupMonitor(ContinuousEmailAgent(self.worker.root)).check(now=self.now)["checked"], 0)
        self.assertEqual(self.worker.repository.path.read_bytes(), before)
        self.now += timedelta(hours=1); self.scan_empty(); self.monitor.check(now=self.now)
        self.assertEqual(self.value()["tracking"]["notice"]["id"], first["tracking"]["notice"]["id"])

    def test_two_monitor_instances_commit_one_check_and_one_notice(self):
        self.due(); self.scan_empty()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:EmailFollowupMonitor(ContinuousEmailAgent(self.worker.root)).check(now=self.now),range(2)))
        self.assertEqual(sum(r["checked"] for r in results),1)
        self.assertEqual(len([h for h in self.value()["history"] if h["action"]=="monitor_check"]),1)

    def test_fact_is_not_replayed_after_generic_operation_cache_is_evicted(self):
        response=mail("2","r@example.test","root@example.test");self.ingest(response)
        for i in range(260):
            self.worker.repository.transact(lambda d:RepositoryMutation(d,{}),operation_id=f"generic-op-{i}")
        self.ingest(response,lambda _:self.fail("No repeated model"))
        self.assertEqual(len(self.value()["observations"]["items"]),1)
        self.assertEqual(len([h for h in self.value()["history"] if h["action"]=="related_message"]),1)

    def test_completed_mail_slot_does_not_skip_new_followup_check_or_run_model(self):
        self.due(); self.scan_empty()
        result = self.tick_service()
        self.assertEqual(result["status"], "already_completed")
        self.assertEqual(result["followups"]["checked"], 1)
        self.select.assert_not_called(); self.assertEqual(self.source.calls, [])
        self.assertEqual(self.value()["tracking"]["status"], "due_no_observed_reply")

    def test_service_finishes_due_check_with_zero_new_mail_and_no_model_assessment(self):
        self.due()
        result=self.tick_service()
        self.assertEqual(result["status"],"completed")
        self.assertEqual(result["proposals"],0)
        self.assertEqual(result["followups"]["checked"],1)
        self.assertEqual(self.value()["tracking"]["status"],"due_no_observed_reply")

    def test_slow_assessment_cannot_shift_source_snapshot_past_deadline(self):
        self.now+=timedelta(minutes=45)
        other=mail("2","other@example.test",subject="Nesouvisející téma")
        def slow(_):
            self.now+=timedelta(minutes=30)
            return proposal()
        HourlyEmailScheduler(self.worker).tick([FakeSource([other])],slow,now=self.now)
        self.monitor.check(now=self.now)
        self.assertEqual(self.value()["tracking"]["status"],"source_unverified")
        self.assertLess(datetime.fromisoformat(self.worker.status()["sources"]["account-a"]["followup_scan"]["as_of"]),
                        datetime.fromisoformat(self.case["check_at"]))

    def test_stale_error_backlog_epoch_and_earlier_scan_never_claim_absence(self):
        self.due(); self.scan_empty()
        baseline = self.worker.repository.path.read_bytes()
        variants = [("stale", lambda d:d["sources"]["account-a"]["followup_scan"].update(as_of=(self.now-timedelta(hours=2)).isoformat())),
                    ("error", lambda d:d["sources"]["account-a"].update(health="error")),
                    ("backlog", lambda d:d["sources"]["account-a"]["followup_scan"].update(status="incomplete")),
                    ("epoch", lambda d:d["sources"]["account-a"]["followup_scan"].update(uidvalidity="11")),
                    ("before_due", lambda d:d["sources"]["account-a"]["followup_scan"].update(as_of=self.case["created_at"]))]
        for name, mutate in variants:
            with self.subTest(name=name):
                self.worker.repository.path.write_bytes(baseline); self.worker._update(mutate)
                self.monitor.check(now=self.now)
                self.assertEqual(self.value()["tracking"]["status"], "source_unverified")

    def test_paused_and_disabled_service_run_date_check_without_a_model_or_scan(self):
        self.due(); self.scan_empty()
        self.worker._update(lambda d:d["schedule"].pop("completed_slot"))
        self.worker._update(lambda d:d.setdefault("service", {}).update(daily_attempts={self.now.date().isoformat():1}))
        self.assertEqual(self.tick_service(max_assessments_per_day=1)["status"], "paused")
        self.select.assert_not_called(); self.assertEqual(self.source.calls, [])
        self.assertEqual(self.value()["tracking"]["reason"], "service_paused")
        self.tick_service(enabled=False)
        self.assertEqual(self.value()["tracking"]["reason"], "service_disabled")

    def test_source_or_model_setup_error_marks_check_unverified_without_replaying_mail(self):
        self.due(); self.scan_empty(); self.worker._update(lambda d:d["schedule"].pop("completed_slot"))
        path=self.root/'service.json';path.write_text(json.dumps({**ServiceSettings().model_dump(),"enabled":True,"providers":["icloud"]}))
        select=Mock(side_effect=RuntimeError("PRIVATE model error"))
        with self.assertRaises(RuntimeError):
            service_tick(settings_path=path,worker=self.worker,now=self.now,source_factory=lambda _:FakeSource([]),select_model=select)
        self.assertEqual(self.value()["tracking"]["reason"],"model_unavailable")
        with self.assertRaises(RuntimeError):
            service_tick(settings_path=path,worker=self.worker,now=self.now,source_factory=Mock(side_effect=RuntimeError("PRIVATE source error")))
        self.assertEqual(self.value()["tracking"]["reason"],"source_unavailable")
        self.assertNotIn("PRIVATE",json.dumps(self.worker.status()["followups"]))

    def test_backlog_proof_is_incomplete_and_catchup_does_not_repeat_assessment(self):
        self.due()
        responses = [mail(str(i), f"r{i}@example.test", "root@example.test") for i in (2,3)]
        source = FakeSource(responses); seen=[]
        scheduler = HourlyEmailScheduler(self.worker)
        first=scheduler.tick([source],lambda v:(seen.append(v.source.uid) or proposal()),now=self.now,batch_size=1,max_batches=1)
        self.assertEqual(first["status"], "incomplete"); self.monitor.check(now=self.now)
        self.assertEqual(self.value()["tracking"]["status"], "source_unverified")
        scheduler.tick([source],lambda v:(seen.append(v.source.uid) or proposal()),now=self.now,batch_size=10,max_batches=1)
        self.monitor.check(now=self.now)
        self.assertEqual(self.value()["tracking"]["status"], "related_message")
        self.assertEqual(seen,["2","3"])

    def test_manual_completion_blocks_late_messages_and_reopen_does_not_replay_old_signals(self):
        self.ingest(mail("2", "r@example.test", "root@example.test"))
        value=self.value()
        done=self.manual.execute({"action":"set_state","id":value["id"],"expected_revision":value["revision"],
            "operation_id":"complete-root-0001","state":"completed"})["followup"]
        self.ingest(mail("3", "late@example.test", "root@example.test"))
        self.assertEqual(self.value()["revision"],done["revision"])
        self.manual.execute({"action":"set_state","id":value["id"],"expected_revision":done["revision"],
            "operation_id":"reopen-root-0001","state":"active","check_at":(self.now+timedelta(days=1)).isoformat()})
        self.scan_empty(); self.monitor.check(now=self.now)
        value=self.value(); self.assertEqual(value["tracking"]["notice"]["item_ids"],[])
        self.assertEqual(value["tracking"]["status"],"waiting")

    def test_completion_during_model_cannot_be_reversed_by_late_assessment(self):
        def complete(_):
            value=self.value()
            self.manual.execute({"action":"set_state","id":value["id"],"expected_revision":value["revision"],
                "operation_id":"complete-during-model","state":"completed"})
            return proposal()
        self.ingest(mail("2","r@example.test","root@example.test"),complete)
        value=self.value();self.monitor.check(now=self.now)
        self.assertEqual(self.value()["state"],"completed")
        self.assertEqual(self.value()["revision"],value["revision"])

    def test_night_is_inert_and_restart_catches_up_once_without_replaying_slots(self):
        self.due(); before=self.worker.repository.path.read_bytes()
        night=self.now.replace(hour=23)
        self.assertEqual(self.monitor.check(now=night)["status"],"outside_hours")
        self.assertEqual(self.worker.repository.path.read_bytes(),before)
        self.now=(self.now+timedelta(days=3)).replace(hour=7)
        self.scan_empty(); self.monitor.check(now=self.now)
        self.assertEqual(len([h for h in self.value()["history"] if h["action"]=="monitor_check"]),1)

    def test_failed_atomic_admission_never_advances_uid_or_calls_model(self):
        response=mail("2","r@example.test","root@example.test"); model=Mock(return_value=proposal())
        cursor=copy.deepcopy(self.worker.status()["sources"]["account-a"])
        with patch("app.email.followup_monitor.admit_observation",side_effect=OSError("private")):
            with self.assertRaises(OSError): self.ingest(response,model)
        model.assert_not_called();self.assertNotIn(response.item_id,self.worker.status()["items"])
        self.assertEqual(self.worker.status()["sources"]["account-a"]["after_uid"],cursor["after_uid"])
        self.ingest(response,model);self.ingest(response,model)
        self.assertEqual(model.call_count,1)
        self.assertEqual(len(self.value()["observations"]["items"]),1)

    def test_running_claim_requires_fresh_compatible_worker_and_survives_rollback_honestly(self):
        self.scan_empty();self.monitor.check(now=self.now)
        self.assertFalse(self.manual.overview()["capabilities"]["automatic_monitoring"])
        health=JsonWorkRepository(self.worker.root/'service_health.json')
        health.transact(lambda _:RepositoryMutation({"followup_monitor_version":1,"status":"completed","finished_at":self.now.isoformat()}))
        self.assertTrue(self.manual.overview()["capabilities"]["automatic_monitoring"])
        before=self.worker.repository.path.read_bytes();self.manual.overview()
        self.assertEqual(self.worker.repository.path.read_bytes(),before)
        health.transact(lambda _:RepositoryMutation({"finished_at":self.now.isoformat()}))
        self.assertFalse(self.manual.overview()["capabilities"]["automatic_monitoring"])

    def test_paused_failed_night_or_missing_heartbeat_status_cannot_claim_running(self):
        self.scan_empty();self.monitor.check(now=self.now)
        health=JsonWorkRepository(self.worker.root/'service_health.json')
        for status in (None,"disabled","paused","failed","outside_hours","busy","needs_initialization"):
            health.transact(lambda _,s=status:RepositoryMutation({"followup_monitor_version":1,"status":s,"finished_at":self.now.isoformat()}))
            self.assertFalse(self.manual.overview()["capabilities"]["automatic_monitoring"],status)
        for status in ("completed","already_completed","incomplete"):
            health.transact(lambda _,s=status:RepositoryMutation({"followup_monitor_version":1,"status":s,"finished_at":self.now.isoformat()}))
            self.assertTrue(self.manual.overview()["capabilities"]["automatic_monitoring"],status)

    def test_explicit_old_source_verification_is_exact_idempotent_and_preserves_business_state(self):
        self.worker._update(lambda d:d["items"][self.original.item_id].pop("thread_evidence"))
        before=copy.deepcopy(self.worker.status());reader=Mock(return_value=SimpleNamespace(read_item=lambda _:self.original))
        self.manual.source_factory=reader
        command={"action":"verify_source","id":self.case["id"],"expected_revision":self.case["revision"],
                 "operation_id":"verify-original-0001","confirmed":True}
        result=self.manual.execute(command);self.assertEqual(result["followup"]["source"]["thread_binding"],"verified_headers")
        self.assertTrue(self.manual.execute(command)["idempotent_replay"]);self.assertEqual(reader.call_count,1)
        self.assertEqual(before["sources"],self.worker.status()["sources"])
        self.assertEqual(before["items"][self.original.item_id]["proposal"],self.worker.status()["items"][self.original.item_id]["proposal"])

    def test_wrong_digest_and_late_source_read_cannot_modify_or_reopen_matter(self):
        self.worker._update(lambda d:d["items"][self.original.item_id].pop("thread_evidence"))
        command={"action":"verify_source","id":self.case["id"],"expected_revision":self.case["revision"],
                 "operation_id":"verify-original-0001","confirmed":True}
        self.manual.source_factory=lambda _:SimpleNamespace(read_item=lambda _:mail(body="different"))
        before=self.worker.repository.path.read_bytes()
        with self.assertRaises(FollowupError):self.manual.execute(command)
        self.assertEqual(self.worker.repository.path.read_bytes(),before)
        def late(_):
            self.manual.execute({"action":"set_state","id":self.case["id"],"expected_revision":self.case["revision"],
                "operation_id":"complete-during-read","state":"completed"})
            return self.original
        self.manual.source_factory=lambda _:SimpleNamespace(read_item=late)
        with self.assertRaises(FollowupConflict):self.manual.execute(command)
        self.assertEqual(self.value()["state"],"completed")
        self.assertNotIn("thread_evidence",self.worker.status()["items"][self.original.item_id])

    def test_verification_rejects_epoch_change_and_does_not_expose_provider_error(self):
        import imaplib
        self.worker._update(lambda d:d["items"][self.original.item_id].pop("thread_evidence"))
        command={"action":"verify_source","id":self.case["id"],"expected_revision":self.case["revision"],
                 "operation_id":"verify-original-0001","confirmed":True}
        self.manual.source_factory=lambda _:SimpleNamespace(read_item=lambda _:replace(self.original,uidvalidity="11"))
        before=self.worker.repository.path.read_bytes()
        with self.assertRaises(FollowupError):self.manual.execute(command)
        self.assertEqual(self.worker.repository.path.read_bytes(),before)
        self.manual.source_factory=lambda _:SimpleNamespace(read_item=Mock(side_effect=imaplib.IMAP4.error("PRIVATE PROVIDER ERROR")))
        with self.assertRaises(FollowupError) as error:self.manual.execute(command)
        self.assertNotIn("PRIVATE",str(error.exception))
        self.assertEqual(self.worker.repository.path.read_bytes(),before)


if __name__ == "__main__":
    unittest.main()
