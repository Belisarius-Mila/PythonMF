from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from app.voice_bridge_runtime import (
    set_voice_bridge_marker,
    start_voice_mode_watcher,
    stop_voice_mode_watcher,
    voice_bridge_status,
)


class VoiceBridgeRuntimeTests(unittest.TestCase):
    def test_marker_service_validates_and_writes_active_tty(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            marker_path = Path(temp_dir) / "marker.json"
            result = set_voice_bridge_marker(
                "ttys004",
                marker_path=marker_path,
                codex_tty_discoverer=lambda: ["ttys004"],
                pid_loader=lambda: 4321,
                timestamp_loader=lambda: "2026-07-10T22:00:00+00:00",
            )
            payload = json.loads(marker_path.read_text(encoding="utf-8"))

        self.assertTrue(result["ok"])
        self.assertEqual(payload["tty"], "ttys004")
        self.assertEqual(payload["parent_pid"], 4321)

    def test_start_service_does_not_launch_when_watcher_is_running(self) -> None:
        result = start_voice_mode_watcher(
            status_loader=lambda **kwargs: {"running": True, "pid": 123},
            status_writer=lambda **kwargs: self.fail("must not write"),
            launcher=lambda *args, **kwargs: self.fail("must not launch"),
            log_file=Path("/tmp/unused.log"),
            project_root=Path("/tmp/project"),
            script_path=Path("/tmp/watcher.py"),
            path_formatter=str,
        )

        self.assertEqual(result["status"], "already_running")

    def test_stop_service_terminates_only_live_reported_pid(self) -> None:
        killed: list[tuple[int, int]] = []
        writes: list[str] = []
        result = stop_voice_mode_watcher(
            status_loader=lambda **kwargs: {"running": True, "pid": 321},
            status_writer=lambda **kwargs: writes.append(str(kwargs["state"])) or {},
            pid_checker=lambda pid: pid == 321,
            killer=lambda pid, sig: killed.append((pid, sig)),
        )

        self.assertEqual(result["status"], "stopped")
        self.assertEqual(killed[0][0], 321)
        self.assertEqual(writes, ["stopped"])

    def test_status_separates_human_managed_and_orphaned_sessions(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            marker_path = Path(temp_dir) / "marker.json"
            marker_path.write_text(
                json.dumps({"tty": "ttys001", "parent_pid": 123, "marked_at": "now"}),
                encoding="utf-8",
            )
            status = voice_bridge_status(
                marker_path=marker_path,
                codex_tty_discoverer=lambda: ["ttys001", "ttys002", "ttys003"],
                managed_codex_tty_labeler=lambda: {"ttys002": "Adam managed"},
                orphaned_janicka_reporter=lambda: {"orphaned_ttys": ["ttys003"]},
                screen_runner=lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "screen running", ""),
                marker_pid_checker=lambda pid: True,
            )

        self.assertEqual(status["effective_tty"], "ttys001")
        self.assertEqual(status["human_codex_ttys"], ["ttys001"])
        self.assertEqual(status["managed_codex_ttys"], ["ttys002"])
        self.assertEqual(status["orphaned_janicka_ttys"], ["ttys003"])
        self.assertEqual(status["status"], "warn")

    def test_missing_marker_is_a_safe_warning(self) -> None:
        status = voice_bridge_status(
            marker_path=Path("/private/tmp/nonexistent_voice_marker_test.json"),
            codex_tty_discoverer=lambda: [],
            managed_codex_tty_labeler=lambda: {},
            orphaned_janicka_reporter=None,
            screen_runner=lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1, "", "No Sockets found"),
        )

        self.assertFalse(status["mac_bridge_ready"])
        self.assertEqual(status["screen_status"], "not_running")
        self.assertIn("není označené cílové TTY", status["warnings"])


if __name__ == "__main__":
    unittest.main()
