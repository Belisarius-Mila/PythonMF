from __future__ import annotations

import json
import tempfile
import threading
import subprocess
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen

from app import cockpit
from app.cockpit_email_agent import (email_agent_dismiss_action, email_agent_edit_action, email_agent_overview,
                                   email_agent_prepare_reply_action, email_agent_send_reply_action,
                                   email_agent_remember_importance_action, email_agent_forget_importance_action)
from app.cockpit_email_agent import email_agent_remember_visibility_action, email_agent_forget_visibility_action
from app.cockpit_frontend import EMAIL_AGENT_HTML
from app.email.continuous_agent import ContinuousEmailAgent
from app.email.pushcut import PushcutNotifier
from app.cockpit_email_agent import email_agent_pushcut_configure_action, email_agent_pushcut_test_action
from tests.test_continuous_email_agent import FakeSource, observed, proposal
from scripts.cockpit_quality_gate import node_binary


class EmailAgentHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.worker = ContinuousEmailAgent(Path(self.temp.name) / "agent")
        self.message = observed(body="Complete body visible in the important card")
        self.worker.cycle(FakeSource([self.message]), lambda _: proposal())
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), cockpit.CockpitServer().make_handler())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.shutdown)
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def shutdown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def request(self, path, payload=None):
        headers = {"Origin": self.base}
        data = None if payload is None else json.dumps(payload).encode()
        if data is not None: headers["Content-Type"] = "application/json"
        with urlopen(Request(self.base + path, data=data, headers=headers), timeout=5) as response:
            return response.status, response.read(), dict(response.headers)

    def test_page_and_overview_use_http_and_show_full_body(self):
        status, body, headers = self.request("/emails-to-resolve/")
        self.assertEqual(status, 200)
        self.assertIn("E-maily k řešení", body.decode())
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        with patch("app.cockpit.email_agent_overview", side_effect=lambda: email_agent_overview(worker=self.worker)):
            _, body, _ = self.request("/api/email-agent/overview")
        self.assertEqual(json.loads(body)["cards"][0]["message"]["body_text"], "Complete body visible in the important card")

    def test_dismiss_post_only_updates_local_worker(self):
        with patch("app.cockpit.email_agent_dismiss_action", side_effect=lambda data: email_agent_dismiss_action(data, worker=self.worker)):
            _, body, _ = self.request("/api/email-agent/dismiss", {"ids": [self.message.item_id]})
        self.assertTrue(json.loads(body)["ok"])
        self.assertEqual(email_agent_overview(worker=self.worker)["cards"], [])
        self.assertEqual(self.worker.status()["sources"]["account-a"]["after_uid"], 1)

    def test_edit_post_keeps_final_subject_and_answer(self):
        card = email_agent_overview(worker=self.worker)["cards"][0]
        value = {**card["proposal"], "reply_subject": "My subject", "reply_draft": "My final answer"}
        with patch("app.cockpit.email_agent_edit_action", side_effect=lambda data: email_agent_edit_action(data, worker=self.worker)):
            _, body, _ = self.request("/api/email-agent/edit", {"id": card["id"], "proposal": value,
                                                               "expected_digest": card["proposal_digest"]})
        self.assertTrue(json.loads(body)["ok"])
        self.assertEqual(email_agent_overview(worker=self.worker)["cards"][0]["proposal"]["reply_draft"], "My final answer")

    def test_remember_importance_post_uses_stored_header_and_keeps_current_card(self):
        before = self.worker.status()["items"][self.message.item_id]
        with patch("app.cockpit.email_agent_remember_importance_action", side_effect=lambda data: email_agent_remember_importance_action(data, worker=self.worker)):
            _, raw, _ = self.request("/api/email-agent/remember-importance", {"id": self.message.item_id,
                "sender": "other@example.test", "subject": "untrusted replacement"})
        self.assertTrue(json.loads(raw)["ok"])
        view = email_agent_overview(worker=self.worker)
        self.assertEqual(len(view["cards"]), 1)
        self.assertEqual(self.worker.status()["items"][self.message.item_id], before)
        self.assertEqual(view["importance_preferences"][0]["sender"], "sender@example.test")
        self.assertEqual(view["importance_preferences"][0]["subject"], self.message.source.subject)
        self.assertNotIn("account", view["importance_preferences"][0])

    def test_hourly_messages_expose_only_headers_and_accept_individual_preference(self):
        message = observed("2", body="PRIVATE LOW BODY", subject="Novinky pro čtenáře")
        low = proposal().model_copy(update={"important": False, "reply_draft": ""})
        self.worker.cycle(FakeSource([message]), lambda _: low)
        view = email_agent_overview(worker=self.worker)
        row = view["hours"][0]
        self.assertEqual(row["messages"], [{"id": message.item_id, "text": row["text"].split(": ", 1)[1]}])
        self.assertNotIn("PRIVATE LOW BODY", json.dumps(row))
        before = self.worker.status()
        with patch("app.cockpit.email_agent_remember_importance_action", side_effect=lambda data: email_agent_remember_importance_action(data, worker=self.worker)):
            _, raw, _ = self.request("/api/email-agent/remember-importance", {"id": message.item_id})
        self.assertTrue(json.loads(raw)["ok"])
        self.assertEqual(self.worker.status()["items"], before["items"])
        self.assertEqual(self.worker.status()["sources"], before["sources"])
        self.assertEqual(email_agent_overview(worker=self.worker)["hours"], view["hours"])

    def test_forget_importance_post_removes_hint_without_touching_mail_or_card(self):
        key = self.worker.remember_low_importance(self.message.item_id)
        before = self.worker.status()["items"]
        with patch("app.cockpit.email_agent_forget_importance_action", side_effect=lambda data: email_agent_forget_importance_action(data, worker=self.worker)):
            _, raw, _ = self.request("/api/email-agent/forget-importance", {"id": key})
        self.assertTrue(json.loads(raw)["ok"])
        self.assertEqual(email_agent_overview(worker=self.worker)["importance_preferences"], [])
        self.assertEqual(self.worker.status()["items"], before)

    def test_visibility_http_hides_only_low_message_and_forget_restores_it(self):
        low = observed("2", subject="Pravidelná nabídka produktů")
        self.worker.cycle(FakeSource([low]), lambda _: proposal().model_copy(update={"important": False}))
        before = self.worker.status()
        with patch("app.cockpit.email_agent_remember_visibility_action", side_effect=lambda data: email_agent_remember_visibility_action(data, worker=self.worker)):
            _, raw, _ = self.request("/api/email-agent/remember-visibility", {"id": low.item_id,
                "sender": "untrusted@example.test", "subject": "untrusted"})
        key = json.loads(raw)["preference_id"]
        view = email_agent_overview(worker=self.worker)
        self.assertEqual(view["hours"], [])
        self.assertEqual(len(view["cards"]), 1)
        self.assertEqual(view["visibility_preferences"], [{"id": key, "sender": "sender@example.test", "subject": low.source.subject}])
        self.assertEqual(self.worker.status()["items"], before["items"])
        self.assertEqual(self.worker.status()["sources"], before["sources"])
        with patch("app.cockpit.email_agent_forget_visibility_action", side_effect=lambda data: email_agent_forget_visibility_action(data, worker=self.worker)):
            _, raw, _ = self.request("/api/email-agent/forget-visibility", {"id": key})
        self.assertTrue(json.loads(raw)["ok"])
        self.assertEqual(email_agent_overview(worker=self.worker)["hours"][0]["ids"], [low.item_id])

    def test_invalid_visibility_action_cannot_create_a_rule_from_important_card(self):
        self.assertFalse(email_agent_remember_visibility_action({"id": self.message.item_id}, worker=self.worker)["ok"])
        self.assertFalse(email_agent_remember_visibility_action({"id": "missing"}, worker=self.worker)["ok"])
        self.assertFalse(email_agent_forget_visibility_action({"id": "missing"}, worker=self.worker)["ok"])
        self.assertNotIn("visibility_preferences", self.worker.status())

    def test_visibility_http_accepts_a_decoded_comma_display_name(self):
        low = observed("2", sender="Jan Novák, Klub dětí <news@example.test>")
        self.worker.cycle(FakeSource([low]), lambda _: proposal().model_copy(update={"important": False}))
        with patch("app.cockpit.email_agent_remember_visibility_action", side_effect=lambda data: email_agent_remember_visibility_action(data, worker=self.worker)):
            status, raw, _ = self.request("/api/email-agent/remember-visibility", {"id": low.item_id})
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(raw)["ok"])
        view = email_agent_overview(worker=self.worker)
        self.assertEqual(view["hours"], [])
        self.assertEqual(len(view["cards"]), 1)
        self.assertEqual(view["visibility_preferences"][0]["sender"], "news@example.test")

    def test_invalid_preference_item_is_rejected_without_creating_a_rule(self):
        self.assertFalse(email_agent_remember_importance_action({"id": "missing"}, worker=self.worker)["ok"])
        self.assertFalse(email_agent_forget_importance_action({"id": "missing"}, worker=self.worker)["ok"])
        self.assertNotIn("importance_preferences", self.worker.status())

    def test_new_page_keeps_content_as_text_and_cannot_delete_mailbox_messages(self):
        self.assertIn("textContent", EMAIL_AGENT_HTML)
        self.assertNotIn("innerHTML", EMAIL_AGENT_HTML)
        self.assertIn("Smazat z Cockpitu", EMAIL_AGENT_HTML)
        self.assertNotIn("/api/email-processing/purge-trash", EMAIL_AGENT_HTML)
        self.assertIn("/api/email-agent/send-reply", EMAIL_AGENT_HTML)
        self.assertIn("Opravdu odeslat odpověď", EMAIL_AGENT_HTML)

    def test_pushcut_setup_and_explicit_test_over_http_never_return_webhook(self):
        calls=[]
        notifier=PushcutNotifier(self.worker,sender=lambda url: calls.append(url) or {"status":"accepted"})
        with patch("app.cockpit.email_agent_pushcut_configure_action",side_effect=lambda data: email_agent_pushcut_configure_action(data,notifier=notifier)):
            _, raw, _ = self.request("/api/email-agent/pushcut/configure",{
                "webhook_url":"https://api.pushcut.io/http-test-secret/notifications/SamanthaEmail",
                "cockpit_url":"https://synthetic.example.test/emails-to-resolve/","enabled":False})
        self.assertTrue(json.loads(raw)["pushcut"]["configured"])
        self.assertNotIn(b"http-test-secret",raw)
        with patch("app.cockpit.email_agent_pushcut_test_action",side_effect=lambda data: email_agent_pushcut_test_action(data,notifier=notifier)):
            _, raw, _ = self.request("/api/email-agent/pushcut/test",{"request_id":"http_test_01","confirmed":True})
        self.assertEqual(json.loads(raw)["status"],"accepted")
        self.assertEqual(len(calls),1)

    def test_editor_polling_double_send_confirmation_and_archive_frontend(self):
        result = subprocess.run([node_binary(), str(Path(__file__).with_name("email_agent_frontend.test.cjs"))],
                                capture_output=True, text=True, timeout=20, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_reply_preparation_and_second_confirmation_routes_over_http(self):
        calls = []
        class Service:
            def prepare(self, item_id, **kwargs):
                calls.append(("prepare", item_id, kwargs))
                return {"recipient": "sender@example.test", "confirmation_token": "test-token", "confirmation_digest": "test-digest"}
            def send(self, item_id, **kwargs):
                calls.append(("send", item_id, kwargs))
                return {"status": "smtp_sent"}
        service = Service()
        with patch("app.cockpit.email_agent_prepare_reply_action", side_effect=lambda data: email_agent_prepare_reply_action(data, service=service)):
            _, raw, _ = self.request("/api/email-agent/prepare-reply", {"id": self.message.item_id, "expected_digest": "current"})
        prepared = json.loads(raw)["prepared"]
        self.assertEqual(len(calls), 1)
        with patch("app.cockpit.email_agent_send_reply_action", side_effect=lambda data: email_agent_send_reply_action(data, service=service)):
            _, raw, _ = self.request("/api/email-agent/send-reply", {"id": self.message.item_id, "confirmed": True,
                                                                    "confirmation_token": prepared["confirmation_token"],
                                                                    "confirmation_digest": prepared["confirmation_digest"]})
        self.assertEqual(json.loads(raw)["receipt"]["status"], "smtp_sent")
        self.assertEqual(calls[-1][2]["confirmed"], True)


if __name__ == "__main__":
    unittest.main()
