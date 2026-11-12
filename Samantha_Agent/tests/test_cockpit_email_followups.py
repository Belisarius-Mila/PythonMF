from __future__ import annotations

from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer
import copy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app import cockpit
from app.cockpit_email_followups import email_followups_action, email_followups_overview
from app.email.continuous_agent import ContinuousEmailAgent
from app.email.followups import EmailFollowups
from app.work_repository import WorkRepositoryError
from tests.test_continuous_email_agent import FakeSource, observed, proposal


class EmailFollowupsHTTPTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.worker = ContinuousEmailAgent(Path(temp.name) / "agent")
        self.message = observed()
        self.worker.cycle(FakeSource([self.message]), lambda _: proposal())
        self.now = datetime(2026, 11, 11, tzinfo=timezone.utc)
        self.service = EmailFollowups(self.worker, clock=lambda: self.now)
        for name, callback in [
            ("email_followups_action", lambda data: email_followups_action(data, service=self.service)),
            ("email_followups_overview", lambda query: email_followups_overview(query, service=self.service)),
        ]:
            patcher = patch("app.cockpit." + name, side_effect=callback)
            self.addCleanup(patcher.stop)
            patcher.start()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), cockpit.CockpitServer().make_handler())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.shutdown)
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def shutdown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def test_explicit_source_verification_requires_confirmation_and_reads_back_same_operation(self):
        _, first, _ = self.request(payload=self.command())
        value = first["followup"]
        command = {"action":"verify_source", "id":value["id"], "expected_revision":value["revision"],
                   "operation_id":"verify-source-http-0001", "confirmed":False}
        before = self.worker.repository.path.read_bytes()
        self.assertEqual(self.request(payload=command)[0], 400)
        self.assertEqual(self.worker.repository.path.read_bytes(), before)
        command["confirmed"] = True
        with patch("app.email.continuous_source.IMAPAgentSource.read_item", side_effect=AssertionError("Cached headers suffice")):
            code, result, _ = self.request(payload=command)
            self.assertEqual(code, 200)
            self.assertEqual(result["followup"]["source"]["thread_binding"], "verified_headers")
            self.assertTrue(self.request(payload=command)[1]["idempotent_replay"])

    def test_related_detail_is_scoped_cached_and_not_a_general_item_reader(self):
        from tests.test_email_followup_monitor import mail
        _, first, _ = self.request(payload=self.command())
        value = first["followup"]
        self.worker._update(lambda d:d["followups"].update(monitor={"version":1,"enabled":True}))
        response = mail("2", "reply@example.test", "test@example.test", sender="sender@example.test",
                        recipient="recipient@example.test")
        self.worker.cycle(FakeSource([response]), lambda _: proposal().model_copy(update={"important":False}))
        before = self.worker.repository.path.read_bytes()
        path = "/api/email-agent/followups?id=" + value["id"] + "&item_id=" + response.item_id
        code, detail, _ = self.request(path)
        self.assertEqual(code, 200)
        self.assertIn("PRIVATE FULL BODY", detail["source_message"]["body_text"])
        self.assertEqual(self.worker.repository.path.read_bytes(), before)
        self.assertEqual(self.request(path.replace(response.item_id, "f"*64))[0], 404)
        self.assertEqual(self.request(path + "&item_id=" + response.item_id)[0], 400)

    def prepare_suggestion(self, *, new_sender=False):
        from app.email.continuous_agent import EmailAssessment
        from app.email.followup_assessment import assess
        from tests.test_email_followup_monitor import mail
        from tests.test_email_followup_assessment import candidate
        _, first, _ = self.request(payload=self.command())
        self.worker._update(lambda d:d["followups"].update(monitor={"version":1,"enabled":True}))
        response=mail("2","reply@example.test","test@example.test",
            sender="new@example.test" if new_sender else "sender@example.test",
            recipient="recipient@example.test",body="Prosím doplňte míry.")
        def propose(observed):
            if not observed.followup_context:return proposal()
            return EmailAssessment(proposal(),None,assess(observed,candidate(observed),model="synthetic"))
        self.worker.cycle(FakeSource([response]),propose)
        return self.service.overview({"id":first["followup"]["id"]})["followup"],response

    def test_review_proposal_through_http_has_exact_confirmation_and_keeps_lifecycle(self):
        value,_=self.prepare_suggestion()
        command={"action":"accept_suggestion","id":value["id"],"expected_revision":value["revision"],
                 "suggestion_id":value["suggestion"]["attempt_id"],"confirmed":False,"operation_id":"accept-http-0001"}
        before=self.worker.repository.path.read_bytes()
        self.assertEqual(self.request(payload=command)[0],400)
        self.assertEqual(self.worker.repository.path.read_bytes(),before)
        command["confirmed"]=True
        code,result,_=self.request(payload=command)
        self.assertEqual(code,200);self.assertEqual(result["followup"]["state"],"active")
        self.assertEqual(result["followup"]["goal"],value["goal"])
        self.assertEqual(result["followup"]["next_step"],"Změřit a dodat míry.")
        self.assertTrue(self.request(payload=command)[1]["idempotent_replay"])

    def test_http_binding_resolution_is_local_scoped_and_does_not_reassess(self):
        value,message=self.prepare_suggestion(new_sender=True)
        command={"action":"resolve_binding","id":value["id"],"expected_revision":value["revision"],
            "item_id":message.item_id,"source_digest":message.content_digest,"decision":"accept",
            "confirmed":True,"operation_id":"bind-http-0001"}
        before=copy.deepcopy(self.worker.status()["sources"])
        with patch("app.email.codex_proposer.CodexEmailProposer.__call__",side_effect=AssertionError("No new model")), \
             patch("app.email.continuous_source.IMAPAgentSource.scan",side_effect=AssertionError("No IMAP")):
            code,result,_=self.request(payload=command)
        self.assertEqual(code,200);self.assertEqual(result["followup"]["state"],"active")
        self.assertIn(message.item_id,result["followup"]["observations"]["items"])
        self.assertEqual(before,self.worker.status()["sources"])
        self.assertNotIn("followup_attempt",self.worker.status()["items"][message.item_id])

    def test_http_decision_foreign_origin_stale_revision_and_extra_root_are_rejected(self):
        value,_=self.prepare_suggestion()
        command={"action":"reject_suggestion","id":value["id"],"expected_revision":value["revision"],
                 "suggestion_id":value["suggestion"]["attempt_id"],"confirmed":True,"operation_id":"reject-http-0001"}
        before=self.worker.repository.path.read_bytes()
        self.assertEqual(self.request(payload=command,origin="https://foreign.invalid")[0],403)
        self.assertEqual(self.request(payload={**command,"root":"/tmp"})[0],400)
        self.assertEqual(self.request(payload={**command,"action":[]})[0],400)
        self.assertEqual(self.request(payload={**command,"expected_revision":1})[0],409)
        self.assertEqual(self.worker.repository.path.read_bytes(),before)

    def request(self, path="/api/email-agent/followups", payload=None, *, origin=None):
        data = None if payload is None else json.dumps(payload).encode()
        headers = {"Origin": self.base if origin is None else origin}
        if data is not None:
            headers["Content-Type"] = "application/json"
        try:
            response = urlopen(Request(self.base + path, data=data, headers=headers), timeout=5)
        except HTTPError as exc:
            response = exc
        with response:
            return response.status, json.loads(response.read()), dict(response.headers)

    def command(self):
        return {"action": "create", "source_item_id": self.message.item_id, "operation_id": "http-create-0001",
                "fields": {"title": "Nabídka", "goal": "Získat nabídku", "next_step": "Čekáme",
                           "waiting_on": "other", "check_at": (self.now + timedelta(days=3)).isoformat()}}

    def test_full_manual_http_lifecycle_and_read_only_projection(self):
        code, result, _ = self.request(payload=self.command())
        self.assertEqual(code, 200)
        value = result["followup"]
        code, result, headers = self.request()
        self.assertEqual(code, 200)
        self.assertEqual(result["active"][0]["id"], value["id"])
        self.assertFalse(result["capabilities"]["automatic_monitoring"])
        self.assertIn("no-store", headers["Cache-Control"])
        before = self.worker.repository.path.read_bytes()
        code, result, _ = self.request("/api/email-agent/followups?id=" + value["id"])
        self.assertEqual(code, 200)
        self.assertEqual(result["followup"], value)
        self.assertEqual(self.worker.repository.path.read_bytes(), before)
        fields = {**self.command()["fields"], "next_step": "Je řada na mně", "waiting_on": "me"}
        _, result, _ = self.request(payload={"action": "update", "id": value["id"],
            "expected_revision": 1, "operation_id": "http-update-0001", "fields": fields})
        self.assertEqual(result["followup"]["revision"], 2)
        _, result, _ = self.request(payload={"action": "set_state", "id": value["id"],
            "expected_revision": 2, "operation_id": "http-complete-0001", "state": "completed"})
        self.assertEqual(result["followup"]["state"], "completed")
        _, result, _ = self.request(payload={"action": "set_state", "id": value["id"],
            "expected_revision": 3, "operation_id": "http-reopen-0001", "state": "active"})
        self.assertEqual(result["followup"]["id"], value["id"])
        self.assertEqual(result["followup"]["generation"], 3)

    def test_http_timeout_replay_and_stale_revision_conflict(self):
        _, first, _ = self.request(payload=self.command())
        _, second, _ = self.request(payload=self.command())
        self.assertTrue(second["idempotent_replay"])
        self.assertEqual(first["followup"]["id"], second["followup"]["id"])
        value = first["followup"]
        command = {"action": "set_state", "id": value["id"], "expected_revision": 1,
                   "operation_id": "http-complete-0001", "state": "completed"}
        self.request(payload=command)
        code, result, _ = self.request(payload={**command, "operation_id": "http-complete-0002"})
        self.assertEqual(code, 409)
        self.assertEqual(result["error"], "conflict")
        code, _, _ = self.request("/api/email-agent/followups?id=" + "f" * 32)
        self.assertEqual(code, 404)

    def test_explicit_http_detail_shows_cached_source_after_card_is_dismissed(self):
        _, result, _ = self.request(payload=self.command())
        value = result["followup"]
        self.worker.dismiss([self.message.item_id], action="dismiss")
        before = self.worker.repository.path.read_bytes()
        code, detail, headers = self.request("/api/email-agent/followups?id=" + value["id"])
        self.assertEqual(code, 200)
        self.assertEqual(detail["source_message"]["body_text"].strip(), "Celá zpráva.")
        self.assertIn("no-store", headers["Cache-Control"])
        self.assertEqual(self.worker.repository.path.read_bytes(), before)

    def test_bad_queries_payloads_and_foreign_origin_never_write(self):
        before = self.worker.repository.path.read_bytes()
        for path in ["/api/email-agent/followups?root=/tmp", "/api/email-agent/followups?id=x&id=y",
                     "/api/email-agent/followups?id="]:
            self.assertEqual(self.request(path)[0], 400)
        self.assertEqual(self.request(payload={**self.command(), "root": "/tmp"})[0], 400)
        self.assertEqual(self.request("/api/email-agent/followups?id=x", payload=self.command())[0], 400)
        with patch("app.cockpit.email_followups_action") as action:
            self.assertEqual(self.request(payload=self.command(), origin="https://foreign.example")[0], 403)
            action.assert_not_called()
        self.assertEqual(self.worker.repository.path.read_bytes(), before)

    def test_unavailable_store_is_not_reported_as_empty_or_successful(self):
        with patch.object(self.service.repository, "read", side_effect=WorkRepositoryError("PRIVATE")):
            code, result, _ = self.request()
            self.assertEqual(code, 503)
            self.assertFalse(result["ok"])
            self.assertNotIn("PRIVATE", json.dumps(result))

    def test_mutation_is_registered_as_a_private_manual_action(self):
        from app.capabilities.registry import get_capability
        records = [v for v in cockpit.COCKPIT_POST_ACTIONS if v["path"] == "/api/email-agent/followups"]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["risk"], "private_write")
        self.assertEqual(records[0]["handler_name"], "email_followups_action")
        self.assertTrue(get_capability("email_followups_read").is_read_only)
        self.assertTrue(get_capability("email_followups_write").requires_confirmation)
