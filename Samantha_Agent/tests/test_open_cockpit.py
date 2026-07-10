import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.cockpit_code_stamp import COCKPIT_CODE_STAMP_PATHS, default_cockpit_code_stamp_paths
from scripts import open_cockpit


class OpenCockpitTests(unittest.TestCase):
    def test_launcher_uses_shared_code_stamp_manifest(self) -> None:
        self.assertEqual(open_cockpit.CODE_STAMP_PATHS, COCKPIT_CODE_STAMP_PATHS)
        relative_paths = {str(path.relative_to(open_cockpit.PROJECT_DIR)) for path in COCKPIT_CODE_STAMP_PATHS}
        self.assertIn("app/cockpit.py", relative_paths)
        self.assertIn("app/quick_notes.py", relative_paths)
        self.assertIn("app/reminders/store.py", relative_paths)
        self.assertIn("app/urgent_reminders.py", relative_paths)
        self.assertIn("scripts/cockpit_server.py", relative_paths)

    def test_default_code_stamp_manifest_is_stable_and_unique(self) -> None:
        paths = default_cockpit_code_stamp_paths(open_cockpit.PROJECT_DIR)

        self.assertEqual(paths, default_cockpit_code_stamp_paths(open_cockpit.PROJECT_DIR))
        self.assertEqual(len(paths), len(set(paths)))

    def test_cockpit_code_stamp_changes_with_file_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "cockpit.py"
            path.write_text("one", encoding="utf-8")
            first = open_cockpit.cockpit_code_stamp((path,))
            path.write_text("two-two", encoding="utf-8")
            second = open_cockpit.cockpit_code_stamp((path,))

        self.assertNotEqual(first, second)

    def test_server_is_current_requires_matching_stamp(self) -> None:
        payload = {"server": {"code_stamp": "abc123"}}

        self.assertTrue(open_cockpit.server_is_current(payload, "abc123"))
        self.assertFalse(open_cockpit.server_is_current(payload, "different"))
        self.assertFalse(open_cockpit.server_is_current({"downloads": {}}, "abc123"))

    def test_startup_readiness_uses_lightweight_server_health(self) -> None:
        self.assertIn("/api/server/health", open_cockpit.READY_PATHS)
        self.assertNotIn("/api/status", open_cockpit.READY_PATHS)

    def test_current_status_payload_retries_before_restart_decision(self) -> None:
        payload = {"server": {"code_stamp": "abc123"}}
        with (
            patch.object(open_cockpit, "status_payload", side_effect=[None, payload]) as status_payload,
            patch.object(open_cockpit.time, "sleep") as sleep,
        ):
            result = open_cockpit.current_status_payload(
                "127.0.0.1",
                8770,
                expected_stamp="abc123",
                attempts=2,
                delay=0.01,
            )

        self.assertEqual(result, payload)
        self.assertEqual(status_payload.call_count, 2)
        sleep.assert_called_once_with(0.01)

    def test_main_opens_running_server_only_after_current_check(self) -> None:
        with (
            patch.object(sys, "argv", ["open_cockpit.py"]),
            patch.object(open_cockpit, "url_ok", return_value=True),
            patch.object(open_cockpit, "ensure_current_server", return_value=True) as ensure_current_server,
            patch.object(open_cockpit, "wait_until_ready", return_value=True) as wait_until_ready,
            patch.object(open_cockpit, "open_browser") as open_browser,
        ):
            result = open_cockpit.main()

        self.assertEqual(result, 0)
        ensure_current_server.assert_called_once_with("127.0.0.1", 8770)
        wait_until_ready.assert_called_once_with("127.0.0.1", 8770)
        open_browser.assert_called_once_with("http://127.0.0.1:8770")

    def test_main_does_not_open_running_server_when_current_check_fails(self) -> None:
        with (
            patch.object(sys, "argv", ["open_cockpit.py"]),
            patch.object(open_cockpit, "url_ok", return_value=True),
            patch.object(open_cockpit, "ensure_current_server", return_value=False),
            patch.object(open_cockpit, "wait_until_ready") as wait_until_ready,
            patch.object(open_cockpit, "open_browser") as open_browser,
        ):
            result = open_cockpit.main()

        self.assertEqual(result, 1)
        wait_until_ready.assert_not_called()
        open_browser.assert_not_called()

    def test_main_does_not_open_running_server_until_ready(self) -> None:
        with (
            patch.object(sys, "argv", ["open_cockpit.py"]),
            patch.object(open_cockpit, "url_ok", return_value=True),
            patch.object(open_cockpit, "ensure_current_server", return_value=True),
            patch.object(open_cockpit, "wait_until_ready", return_value=False),
            patch.object(open_cockpit, "open_browser") as open_browser,
        ):
            result = open_cockpit.main()

        self.assertEqual(result, 1)
        open_browser.assert_not_called()

    def test_main_starts_fallback_when_default_port_is_busy_and_unresponsive(self) -> None:
        with (
            patch.object(sys, "argv", ["open_cockpit.py", "--no-open"]),
            patch.object(open_cockpit, "FALLBACK_PORTS", [8771]),
            patch.object(open_cockpit, "url_ok", return_value=False),
            patch.object(open_cockpit, "port_is_busy", side_effect=[True, False]),
            patch.object(open_cockpit, "start_server") as start_server,
            patch.object(open_cockpit, "wait_until_ready", return_value=True),
        ):
            result = open_cockpit.main()

        self.assertEqual(result, 0)
        start_server.assert_called_once()
        self.assertEqual(start_server.call_args.args[0:2], ("127.0.0.1", 8771))
        self.assertTrue(str(start_server.call_args.args[2]).endswith("server_8771.log"))

    def test_main_does_not_fallback_for_explicit_non_default_port(self) -> None:
        with (
            patch.object(sys, "argv", ["open_cockpit.py", "--port", "8899", "--no-open"]),
            patch.object(open_cockpit, "url_ok", return_value=False),
            patch.object(open_cockpit, "port_is_busy", return_value=True),
            patch.object(open_cockpit, "open_or_start_fallback") as open_or_start_fallback,
        ):
            result = open_cockpit.main()

        self.assertEqual(result, 1)
        open_or_start_fallback.assert_not_called()

    def test_main_does_not_fallback_when_disabled(self) -> None:
        with (
            patch.object(sys, "argv", ["open_cockpit.py", "--no-open", "--no-fallback"]),
            patch.object(open_cockpit, "url_ok", return_value=False),
            patch.object(open_cockpit, "port_is_busy", return_value=True),
            patch.object(open_cockpit, "open_or_start_fallback") as open_or_start_fallback,
        ):
            result = open_cockpit.main()

        self.assertEqual(result, 1)
        open_or_start_fallback.assert_not_called()

    def test_open_browser_adds_cache_buster(self) -> None:
        with patch.object(open_cockpit.subprocess, "run") as run:
            open_cockpit.open_browser("http://127.0.0.1:8770")

        opened_url = run.call_args.args[0][1]
        self.assertTrue(opened_url.startswith("http://127.0.0.1:8770?cockpit_launch="))


if __name__ == "__main__":
    unittest.main()
