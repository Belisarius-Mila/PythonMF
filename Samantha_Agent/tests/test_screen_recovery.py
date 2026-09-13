from dataclasses import replace
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock, patch
from urllib.parse import urlparse, parse_qs

from app.screen_recovery import ScreenRecovery, open_vscode
from scripts.cockpit_quality_gate import node_binary
from tests import test_screen_sessions
from tests.test_cockpit_http_security import running_cockpit_server, request_json


class ScreenRecoveryTests(unittest.TestCase):
    def setUp(self):
        fixture = test_screen_sessions.ScreenSessionsTests()
        fixture.setUp()
        self.fixture = fixture
        self.screens = fixture.controller
        self.now = 1.0
        self.opened = []
        self.recovery = ScreenRecovery(self.screens, opener=self.opened.append,
                                       available=lambda: True, clock=lambda: self.now)

    def payload(self, **extra):
        row = self.screens.status()["sessions"][0]
        return {"pid": row["pid"], "identity": row["attach_identity"], "confirmed": True, **extra}

    def ticket(self):
        return parse_qs(urlparse(self.opened[-1]).query)["ticket"][0]

    def test_live_codex_reconnect_allowed_without_allowing_stop(self):
        f = self.fixture
        f.rows.append(replace(f.child, pid=44, ppid=43, command="/vendor/bin/codex"))
        row = self.screens.status()["sessions"][0]
        self.assertFalse(row["can_stop"])
        self.assertTrue(row["can_attach"])
        self.assertTrue(self.recovery.request(self.payload(), 8770)["ok"])
        self.assertEqual(self.recovery.claim({"ticket": self.ticket()}), {"ok": True, "socket": "42.test"})
        self.assertFalse(f.quits or f.signals)

    def test_takeover_requires_explicit_confirmation(self):
        self.fixture.screens[0]["state"] = "Attached"
        self.assertFalse(self.recovery.request(self.payload(), 8770)["ok"])
        self.assertFalse(self.opened)
        self.assertTrue(self.recovery.request(self.payload(takeover=True), 8770)["ok"])

    def test_cancel_missing_extension_and_invalid_identity_never_open(self):
        for payload in (self.payload(confirmed=False), self.payload(pid=True), self.payload(identity="0" * 64)):
            self.assertFalse(self.recovery.request(payload, 8770)["ok"])
        self.recovery.available = lambda: False
        self.assertFalse(self.recovery.request(self.payload(), 8770)["ok"])
        self.assertFalse(self.opened)

    def test_services_foreign_users_labels_and_unsafe_socket_rejected(self):
        f = self.fixture
        for command in ("/vendor/bin/codex app-server", "python /project/scripts/cockpit_server.py"):
            f.rows = [f.target, replace(f.child, command=command)]
            self.assertFalse(self.recovery.request(self.payload(), 8770)["ok"])
        f.rows = [f.target, replace(f.child, uid=502)]
        self.assertFalse(self.recovery.request(self.payload(), 8770)["ok"])
        f.rows = [f.target, f.child]
        self.screens.labels = lambda: {"ttys014": {"protected": True}}
        self.assertFalse(self.recovery.request(self.payload(), 8770)["ok"])
        self.screens.labels = lambda: {}
        f.screens[0]["socket"] = "42.test;bad"
        self.assertFalse(self.recovery.request(self.payload(), 8770)["ok"])
        self.assertFalse(self.opened)

    def test_changed_identity_or_new_service_before_claim_rejected(self):
        f = self.fixture
        for change in ("pid_reuse", "attached", "service", "gone"):
            with self.subTest(change=change):
                self.setUp()
                f = self.fixture
                self.recovery.request(self.payload(), 8770)
                if change == "pid_reuse": f.rows[0] = replace(f.target, started="different")
                if change == "attached": f.screens[0]["state"] = "Attached"
                if change == "service": f.rows.append(replace(f.child, pid=44, command="codex app-server"))
                if change == "gone": f.screens = []
                self.assertFalse(self.recovery.claim({"ticket": self.ticket()})["ok"])

    def test_normal_child_job_changes_do_not_invalidate_recovery(self):
        f = self.fixture
        self.recovery.request(self.payload(), 8770)
        f.rows.append(replace(f.child, pid=44, command="python script.py"))
        self.assertTrue(self.recovery.claim({"ticket": self.ticket()})["ok"])

    def test_duplicate_request_expiry_and_one_use_ticket(self):
        self.recovery.request(self.payload(), 8770)
        self.assertEqual(self.recovery.request(self.payload(), 8770)["status"], "pending")
        self.assertEqual(len(self.opened), 1)
        ticket = self.ticket()
        self.assertTrue(self.recovery.claim({"ticket": ticket})["ok"])
        self.assertFalse(self.recovery.claim({"ticket": ticket})["ok"])
        self.now += 91
        self.recovery.request(self.payload(), 8770)
        self.assertEqual(len(self.opened), 2)
        self.now += 91
        self.assertFalse(self.recovery.claim({"ticket": self.ticket()})["ok"])

    def test_failed_desktop_open_is_redacted_and_not_retried(self):
        self.recovery.opener = Mock(side_effect=OSError("private detail"))
        result = self.recovery.request(self.payload(), 8770)
        self.assertFalse(result["ok"])
        self.assertNotIn("private detail", str(result))
        self.assertEqual(self.recovery.opener.call_count, 1)
        self.assertFalse(self.recovery._pending)

    def test_macos_dispatch_uses_fixed_application_and_argv(self):
        with patch("app.screen_recovery.subprocess.run") as run:
            open_vscode("vscode://samantha-local.screen-recovery/attach", "/project")
        code = "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
        self.assertEqual(run.call_args_list[0].args[0], [code, "/project"])
        self.assertEqual(run.call_args.args[0], [code, "--open-url", "vscode://samantha-local.screen-recovery/attach"])
        self.assertNotIn("shell", run.call_args.kwargs)

    def test_http_attach_claim_and_cross_origin_protection(self):
        with patch("app.cockpit.SCREEN_RECOVERY", self.recovery), running_cockpit_server() as (host, port, _):
            headers = {"Content-Type": "application/json", "Origin": "https://example.org"}
            code, _, _ = request_json(host, port, "POST", "/api/screen/sessions/attach", body=json.dumps(self.payload()), headers=headers)
            self.assertEqual(code, 403)
            self.assertFalse(self.opened)
            headers["Origin"] = f"http://{host}:{port}"
            _, data, _ = request_json(host, port, "POST", "/api/screen/sessions/attach", body=json.dumps(self.payload()), headers=headers)
            self.assertTrue(data["ok"])
            self.assertIn(f"port={port}&", self.opened[0])
            _, data, _ = request_json(host, port, "POST", "/api/screen/sessions/claim", body=json.dumps({"ticket": self.ticket()}), headers=headers)
            self.assertEqual(data, {"ok": True, "socket": "42.test"})

    def test_vscode_extension_contract(self):
        result = subprocess.run([node_binary(), "--test", "tests/screen_recovery_extension.test.cjs"],
                                cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
