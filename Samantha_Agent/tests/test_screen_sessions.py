from dataclasses import replace
import json
import signal
import subprocess
import unittest
from unittest.mock import Mock, patch

from app.codex_sessions import Process
from app.screen_sessions import ScreenSessionController, parse_screen_list, read_screen_sessions, quit_screen
from tests.test_cockpit_http_security import running_cockpit_server, request_json


class ScreenSessionsTests(unittest.TestCase):
    def setUp(self):
        self.target = Process(42, 1, 501, "??", "Sat Sep 12 08:00:00 2026", 50, "SCREEN -S test")
        self.child = Process(43, 42, 501, "ttys014", "Sat Sep 12 08:00:01 2026", 49, "/bin/zsh")
        self.rows = [self.target, self.child]
        self.screens = [{"pid": 42, "name": "test", "socket": "42.test", "state": "Detached"}]
        self.quits, self.signals = [], []
        self.controller = ScreenSessionController(
            root="/project", processes=lambda: list(self.rows), cwd=lambda _: "/project",
            executable=lambda _: "SCREEN", labels=lambda: {}, own_pid=90, uid=501,
            username="mila",
            screens=lambda: list(self.screens), quit_session=self.quit, signal_process=self.kill, wait_seconds=0)

    def quit(self, socket):
        self.quits.append(socket)
        self.rows = [p for p in self.rows if p.pid not in (42, 43)]

    def kill(self, pid, sig):
        self.signals.append((pid, sig))
        self.rows = [p for p in self.rows if p.pid != pid]

    def payload(self, **extra):
        row = self.controller.status()["sessions"][0]
        return {"pid": row["pid"], "identity": row["identity"], "confirmed": True, **extra}

    def test_parse_mac_and_linux_lists_ignores_dead_and_headers(self):
        output = "There are screens on:\n\t42.test\t(Detached)\n\t44.samantha_codex (09/12/26 08:00:00) (Attached)\n\t55.dead (Dead ???)\n2 Sockets in /private/path."
        self.assertEqual([s["socket"] for s in parse_screen_list(output)], ["42.test", "44.samantha_codex"])
        with patch("app.screen_sessions.subprocess.run", return_value=Mock(stdout="No Sockets found in /private/path.\n", returncode=1)):
            self.assertEqual(read_screen_sessions(), [])
        with patch("app.screen_sessions.subprocess.run", return_value=Mock(stdout="unavailable", returncode=1)):
            self.assertRaises(OSError, read_screen_sessions)

    def test_quit_uses_exact_socket_without_shell(self):
        with patch("app.screen_sessions.subprocess.run") as run:
            quit_screen("42.test")
        self.assertEqual(run.call_args.args[0], ["/usr/bin/screen", "-S", "42.test", "-X", "quit"])
        self.assertNotIn("shell", run.call_args.kwargs)

    def test_report_includes_membership_and_redacts_commands(self):
        self.rows[1] = replace(self.child, command="/bin/zsh 'private contents'")
        data = self.controller.status()
        self.assertTrue(data["ok"])
        self.assertEqual(data["sessions"][0]["process_count"], 1)
        self.assertTrue(data["sessions"][0]["can_stop"])
        self.assertNotIn("private contents", str(data))

    def test_normal_close_only_selected_screen(self):
        self.rows += [replace(self.target, pid=52), replace(self.child, pid=53, ppid=52)]
        self.assertTrue(self.controller.stop(self.payload())["ok"])
        self.assertEqual(self.quits, ["42.test"])
        self.assertEqual([p.pid for p in self.rows], [52, 53])
        self.assertFalse(self.signals)

    def test_requires_explicit_confirmation_and_identity(self):
        for payload in ({"pid": 42}, self.payload(confirmed=False), self.payload(identity="0"*64), self.payload(pid=True)):
            self.assertFalse(self.controller.stop(payload)["ok"])
        self.assertFalse(self.quits)

    def test_live_codex_nested_services_labels_and_server_are_protected(self):
        for command in ("/vendor/bin/codex", "/vendor/bin/codex app-server", "python /project/scripts/cockpit_server.py"):
            with self.subTest(command=command):
                self.rows = [self.target, self.child, replace(self.child, pid=44, ppid=43, command=command)]
                self.assertFalse(self.controller.status()["sessions"][0]["can_stop"])
        self.rows = [self.target, self.child]
        self.controller.labels = lambda: {"ttys014": {"protected": True}}
        self.assertFalse(self.controller.status()["sessions"][0]["can_stop"])
        self.controller.labels = lambda: {}
        self.rows.append(replace(self.child, pid=90, ppid=43))
        self.assertFalse(self.controller.status()["sessions"][0]["can_stop"])
        self.assertFalse(self.quits)

    def test_foreign_owner_executable_and_cwd_are_rejected(self):
        payload = self.payload()
        self.rows[0] = replace(self.target, uid=502)
        self.assertFalse(self.controller.stop(payload)["ok"])
        self.rows[0] = self.target
        self.controller.cwd = lambda _: "/elsewhere"
        self.assertFalse(self.controller.stop(payload)["ok"])
        self.controller.cwd = lambda _: "/project"
        self.controller.executable = lambda _: "/bin/sleep"
        self.assertFalse(self.controller.stop(payload)["ok"])
        self.assertFalse(self.quits)

    def test_macos_root_login_wrapper_requires_exact_user_parent_and_executable(self):
        login = replace(self.child, uid=0, command="login -pflq mila /bin/zsh")
        self.controller.executable = lambda pid: "SCREEN" if pid == 42 else "/usr/bin/login"
        self.rows[1] = login
        self.assertTrue(self.controller.status()["sessions"][0]["can_stop"])
        payload = self.payload()
        self.rows[1] = replace(login, command="login -pflq somebody_else /bin/zsh")
        self.assertFalse(self.controller.stop(payload)["ok"])
        self.rows[1] = replace(login, command="sudo /bin/zsh")
        self.assertFalse(self.controller.status()["sessions"][0]["can_stop"])
        self.rows[1] = login
        self.controller.executable = lambda pid: "SCREEN" if pid == 42 else "/bin/sleep"
        self.assertFalse(self.controller.status()["sessions"][0]["can_stop"])
        self.assertFalse(self.quits)

    def test_pid_reuse_and_changed_membership_are_rejected(self):
        payload = self.payload()
        for changed in ([replace(self.target, started="new"), self.child],
                        [self.target, self.child, replace(self.child, pid=44)],
                        [self.target, replace(self.child, command="/vendor/bin/codex")]):
            self.rows = changed
            self.assertFalse(self.controller.stop(payload)["ok"])
        self.assertFalse(self.quits)

    def test_membership_is_checked_again_immediately_before_close(self):
        payload = self.payload()
        self.controller.processes = Mock(side_effect=[self.rows, self.rows + [replace(self.child, pid=44)]])
        self.assertFalse(self.controller.stop(payload)["ok"])
        self.assertFalse(self.quits)

    def test_force_requires_attempt_then_fresh_same_identity(self):
        payload = self.payload(force=True)
        self.assertFalse(self.controller.stop(payload)["ok"])
        self.controller.quit_session = Mock(side_effect=subprocess.TimeoutExpired("screen", 3))
        self.assertEqual(self.controller.stop(self.payload())["status"], "still_running")
        self.assertTrue(self.controller.status()["sessions"][0]["force_available"])
        self.assertTrue(self.controller.stop(payload)["ok"])
        self.assertEqual(self.signals, [(42, signal.SIGKILL)])
        self.assertEqual([p.pid for p in self.rows], [43])

    def test_disappeared_socket_never_signals_process(self):
        payload = self.payload()
        self.screens = []
        self.assertFalse(self.controller.stop(payload)["ok"])
        self.assertFalse(self.quits)

    def test_disappeared_process_and_unavailable_inventory(self):
        payload = self.payload()
        self.rows = []
        self.assertEqual(self.controller.stop(payload)["status"], "already_stopped")
        self.controller.screens = Mock(side_effect=OSError("private failure detail"))
        self.assertFalse(self.controller.status()["ok"])
        self.assertNotIn("private failure", str(self.controller.status()))

    def test_http_get_stop_and_cross_origin_protection(self):
        with patch("app.cockpit.SCREEN_SESSIONS", self.controller), running_cockpit_server() as (host, port, _):
            code, data, _ = request_json(host, port, "GET", "/api/screen/sessions")
            self.assertEqual(code, 200)
            self.assertEqual(data["sessions"][0]["socket"], "42.test")
            body = json.dumps(self.payload())
            code, _, _ = request_json(host, port, "POST", "/api/screen/sessions/stop", body=body,
                                      headers={"Origin": "https://example.org", "Content-Type": "application/json"})
            self.assertEqual(code, 403)
            self.assertFalse(self.quits)
            code, data, _ = request_json(host, port, "POST", "/api/screen/sessions/stop", body=body,
                                      headers={"Origin": f"http://{host}:{port}", "Content-Type": "application/json"})
            self.assertEqual(code, 200)
            self.assertTrue(data["ok"])
            self.assertEqual(self.quits, ["42.test"])


if __name__ == "__main__":
    unittest.main()
