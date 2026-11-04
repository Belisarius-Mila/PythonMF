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
from app.cockpit_email_agent import email_agent_dismiss_action, email_agent_edit_action, email_agent_overview
from app.cockpit_frontend import EMAIL_AGENT_HTML
from app.email.continuous_agent import ContinuousEmailAgent
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

    def test_new_page_keeps_content_as_text_and_contains_no_send_or_delete_mailbox_endpoint(self):
        self.assertIn("textContent", EMAIL_AGENT_HTML)
        self.assertNotIn("innerHTML", EMAIL_AGENT_HTML)
        self.assertIn("Smazat z Cockpitu", EMAIL_AGENT_HTML)
        self.assertNotIn("/api/email-processing/purge-trash", EMAIL_AGENT_HTML)
        self.assertNotIn("/api/email-agent/send", EMAIL_AGENT_HTML)

    def test_editor_polling_dismissal_and_confirmed_archive_frontend(self):
        result = subprocess.run([node_binary(), str(Path(__file__).with_name("email_agent_frontend.test.cjs"))],
                                capture_output=True, text=True, timeout=20, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
