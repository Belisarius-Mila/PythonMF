from dataclasses import replace
import signal
import unittest
from unittest.mock import Mock, patch

from app.codex_sessions import CodexSessionController, Process
from tests.test_cockpit_http_security import running_cockpit_server, request_json


class CodexSessionsTests(unittest.TestCase):
    def setUp(self):
        self.target = Process(42, 2, 501, "ttys014", "Thu Sep 10 08:00:00 2026", 50,
                              "/vendor/bin/codex -C /project/Samantha_Agent")
        self.rows = [self.target]
        self.signals = []
        self.controller = CodexSessionController(
            root="/project", processes=lambda: list(self.rows), cwd=lambda _: "/home/user",
            executable=lambda _: "/vendor/bin/codex", labels=lambda: {},
            own_pid=90, uid=501, signal_process=self.kill, wait_seconds=0,
        )

    def kill(self, pid, sig):
        self.signals.append((pid, sig))
        self.rows = [p for p in self.rows if p.pid != pid]

    def payload(self, **extra):
        row = self.controller.status()["sessions"][0]
        return {"pid": row["pid"], "identity": row["identity"], "confirmed": True, **extra}

    def test_report_excludes_wrappers_and_services_and_redacts_arguments(self):
        self.rows += [replace(self.target, pid=43, command="node /usr/bin/codex"),
                      replace(self.target, pid=44, command="screen -r samantha_codex"),
                      replace(self.target, pid=45, command="/bin/zsh scripts/samantha_codex.sh"),
                      replace(self.target, pid=46, command="/vendor/bin/codex app-server"),
                      replace(self.target, pid=47, command="/vendor/bin/codex-code-mode-host")]
        self.rows[0] = replace(self.target, command=self.target.command + " 'private prompt'")
        data = self.controller.status()
        self.assertEqual([s["pid"] for s in data["sessions"]], [42])
        self.assertNotIn("private prompt", str(data))
        self.assertEqual(data["protected_services"], 1)
        self.assertTrue(data["sessions"][0]["can_stop"])

    def test_cli_cd_is_resolved_against_os_cwd_and_must_be_in_project(self):
        for args, expected in [("--cd=/project", True), ("-C/project", True),
                               ("-C ..", True), ("-C /elsewhere", False), ("-C", False)]:
            with self.subTest(args=args):
                self.controller.cwd = lambda _: "/project/child"
                self.rows = [replace(self.target, command="/vendor/bin/codex " + args)]
                self.assertEqual(self.controller.status()["sessions"][0]["can_stop"], expected)

    def test_stop_requires_confirmation_and_identity(self):
        for payload in ({"pid": 42}, self.payload(confirmed=False), self.payload(identity="0" * 64)):
            self.assertFalse(self.controller.stop(payload)["ok"])
        self.assertEqual(self.signals, [])

    def test_stop_only_selected_process(self):
        self.rows.append(replace(self.target, pid=43, tty="ttys015"))
        self.assertTrue(self.controller.stop(self.payload())["ok"])
        self.assertEqual(self.signals, [(42, signal.SIGTERM)])
        self.assertEqual([p.pid for p in self.rows], [43])

    def test_pid_reuse_after_preview_is_rejected(self):
        payload = self.payload()
        self.rows = [replace(self.target, started="Thu Sep 10 09:00:00 2026")]
        self.assertFalse(self.controller.stop(payload)["ok"])
        self.assertFalse(self.signals)

    def test_pid_change_immediately_before_signal_is_rejected(self):
        payload = self.payload()
        self.controller.processes = Mock(side_effect=[self.rows, [replace(self.target, ppid=99)]])
        self.assertFalse(self.controller.stop(payload)["ok"])
        self.assertFalse(self.signals)

    def test_protection_change_after_preview_is_rejected(self):
        payload = self.payload()
        self.controller.labels = lambda: {"ttys014": {"protected": True}}
        self.assertFalse(self.controller.stop(payload)["ok"])
        self.assertFalse(self.signals)

    def test_server_ancestors_are_protected(self):
        self.rows.append(replace(self.target, pid=90, ppid=42, command="python server.py"))
        self.assertFalse(self.controller.status()["sessions"][0]["can_stop"])
        self.assertFalse(self.controller.stop(self.payload())["ok"])
        self.assertFalse(self.signals)

    def test_foreign_uid_unknown_cwd_and_spoofed_executable_are_rejected(self):
        payload = self.payload()
        self.rows = [replace(self.target, uid=502)]
        self.assertFalse(self.controller.stop(payload)["ok"])
        self.rows = [self.target]
        self.controller.cwd = lambda _: ""
        self.assertFalse(self.controller.stop(payload)["ok"])
        self.controller.cwd = lambda _: "/home/user"
        self.controller.executable = lambda _: "/bin/sleep"
        self.assertFalse(self.controller.stop(payload)["ok"])
        self.assertFalse(self.signals)

    def test_force_requires_previous_attempt_and_same_identity(self):
        payload = self.payload(force=True)
        self.assertFalse(self.controller.stop(payload)["ok"])
        self.controller.signal_process = lambda pid, sig: self.signals.append((pid, sig))
        result = self.controller.stop(self.payload())
        self.assertEqual(result["status"], "still_running")
        self.assertTrue(self.controller.status()["sessions"][0]["force_available"])
        self.controller.signal_process = self.kill
        self.assertTrue(self.controller.stop(payload)["ok"])
        self.assertEqual(self.signals, [(42, signal.SIGTERM), (42, signal.SIGKILL)])

    def test_disappeared_process_does_not_signal_anything(self):
        payload = self.payload()
        self.rows = []
        self.assertEqual(self.controller.stop(payload)["status"], "already_stopped")
        self.assertFalse(self.signals)

    def test_unavailable_process_report_fails_closed(self):
        self.controller.processes = Mock(side_effect=OSError("unavailable"))
        self.assertFalse(self.controller.status()["ok"])

    def test_http_get_and_confirmed_stop_use_registered_controller(self):
        import json
        with patch("app.cockpit.CODEX_SESSIONS", self.controller), running_cockpit_server() as (host, port, _):
            code, data, _ = request_json(host, port, "GET", "/api/codex/sessions")
            self.assertEqual(code, 200)
            self.assertEqual(data["sessions"][0]["pid"], 42)
            code, data, _ = request_json(host, port, "POST", "/api/codex/sessions/stop",
                                         body=json.dumps(self.payload()),
                                         headers={"Origin": f"http://{host}:{port}", "Content-Type": "application/json"})
            self.assertEqual(code, 200)
            self.assertTrue(data["ok"])
            self.assertEqual(self.signals, [(42, signal.SIGTERM)])

    def test_http_cross_origin_stop_is_rejected_before_signaling(self):
        import json
        with patch("app.cockpit.CODEX_SESSIONS", self.controller), running_cockpit_server() as (host, port, _):
            code, _, _ = request_json(host, port, "POST", "/api/codex/sessions/stop",
                                      body=json.dumps(self.payload()),
                                      headers={"Origin": "https://example.org", "Content-Type": "application/json"})
            self.assertEqual(code, 403)
            self.assertFalse(self.signals)


if __name__ == "__main__":
    unittest.main()
