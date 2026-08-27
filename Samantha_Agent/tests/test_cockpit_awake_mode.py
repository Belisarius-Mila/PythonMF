from __future__ import annotations

import json
import stat
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from app.cockpit_awake_mode import (
    CockpitAwakeMode,
    CockpitAwakeModeError,
    cockpit_awake_mode_action,
    cockpit_awake_mode_status_action,
)


class CockpitAwakeModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.state_path = Path(self.temp_dir.name) / "private" / "awake_mode.json"
        self.now_value = datetime(2026, 8, 27, 10, 0, tzinfo=timezone.utc)
        self.commands: dict[int, str] = {}
        self.launches: list[list[str]] = []
        self.terminated: list[int] = []

    def manager(self) -> CockpitAwakeMode:
        def launch(argv: object) -> int:
            clean = [str(item) for item in argv]
            self.launches.append(clean)
            self.commands[4321] = " ".join(clean)
            return 4321

        def terminate(pid: int) -> None:
            self.terminated.append(pid)
            self.commands.pop(pid, None)

        return CockpitAwakeMode(
            state_path=self.state_path,
            caffeinate_path=Path("/usr/bin/caffeinate"),
            now=lambda: self.now_value,
            launcher=launch,
            process_command=lambda pid: self.commands.get(pid, ""),
            terminator=terminate,
            executable_available=lambda _path: True,
        )

    def test_missing_state_is_safely_inactive(self) -> None:
        status = self.manager().status()

        self.assertTrue(status["ok"])
        self.assertFalse(status["active"])
        self.assertEqual(status["status"], "inactive")
        self.assertEqual(status["allowed_hours"], [1, 2, 4])
        self.assertNotIn("pid", status)

    def test_start_uses_exact_allowlisted_argv_and_private_state(self) -> None:
        manager = self.manager()

        result = manager.start(2)

        self.assertTrue(result["active"])
        self.assertEqual(result["remaining_seconds"], 7200)
        self.assertEqual(
            self.launches,
            [["/usr/bin/caffeinate", "-i", "-t", "7200"]],
        )
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["pid"], 4321)
        self.assertEqual(state["duration_seconds"], 7200)
        self.assertEqual(stat.S_IMODE(self.state_path.stat().st_mode), 0o600)
        self.assertNotIn("pid", result)

    def test_status_recovers_active_process_after_manager_restart(self) -> None:
        self.manager().start(4)
        restarted = self.manager()
        self.now_value += timedelta(minutes=15)

        result = restarted.status()

        self.assertTrue(result["active"])
        self.assertEqual(result["remaining_seconds"], 13_500)
        self.assertEqual(result["status"], "active")

    def test_invalid_or_duplicate_start_does_not_launch_another_process(self) -> None:
        manager = self.manager()
        with self.assertRaises(CockpitAwakeModeError):
            manager.start(3)
        manager.start(1)

        with self.assertRaises(CockpitAwakeModeError):
            manager.start(2)

        self.assertEqual(len(self.launches), 1)

    def test_stop_terminates_only_the_exact_owned_process(self) -> None:
        manager = self.manager()
        manager.start(1)

        result = manager.stop()

        self.assertFalse(result["active"])
        self.assertEqual(result["status"], "stopped")
        self.assertEqual(self.terminated, [4321])
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        self.assertFalse(state["active"])
        self.assertNotIn("pid", state)

    def test_stop_refuses_process_with_mismatched_command(self) -> None:
        manager = self.manager()
        manager.start(1)
        self.commands[4321] = "/usr/bin/python3 unrelated.py"

        result = manager.stop()

        self.assertEqual(result["status"], "inactive")
        self.assertEqual(self.terminated, [])

    def test_expired_process_is_reported_inactive_without_killing(self) -> None:
        manager = self.manager()
        manager.start(1)
        self.now_value += timedelta(hours=1, seconds=1)

        result = manager.status()

        self.assertFalse(result["active"])
        self.assertEqual(result["status"], "expired")
        self.assertEqual(self.terminated, [])

    def test_state_write_failure_terminates_new_process(self) -> None:
        manager = self.manager()
        with patch.object(
            manager,
            "_write_state",
            side_effect=CockpitAwakeModeError("nelze uložit"),
        ):
            with self.assertRaises(CockpitAwakeModeError):
                manager.start(1)

        self.assertEqual(self.terminated, [4321])

    def test_action_adapter_accepts_only_start_and_stop(self) -> None:
        manager = Mock()
        manager.start.return_value = {"ok": True, "active": True}
        manager.stop.return_value = {"ok": True, "active": False}

        started = cockpit_awake_mode_action(
            {"action": "start", "hours": 4}, manager=manager
        )
        stopped = cockpit_awake_mode_action({"action": "stop"}, manager=manager)
        invalid = cockpit_awake_mode_action({"action": "extend"}, manager=manager)

        self.assertTrue(started["active"])
        self.assertFalse(stopped["active"])
        self.assertFalse(invalid["ok"])
        manager.start.assert_called_once_with(4)
        manager.stop.assert_called_once_with()

    def test_status_adapter_fails_honestly_on_corrupt_state(self) -> None:
        self.state_path.parent.mkdir(parents=True)
        self.state_path.write_text("not-json", encoding="utf-8")

        result = cockpit_awake_mode_status_action(manager=self.manager())

        self.assertFalse(result["ok"])
        self.assertFalse(result["active"])
        self.assertEqual(result["status"], "unknown")


if __name__ == "__main__":
    unittest.main()
