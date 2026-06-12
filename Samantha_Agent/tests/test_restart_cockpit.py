import unittest
from unittest.mock import patch

from scripts import restart_cockpit


class RestartCockpitTests(unittest.TestCase):
    def test_restart_returns_without_manual_start_when_launchd_revives_server(self) -> None:
        starts = []

        def fake_start(host: str, port: int):
            starts.append((host, port))
            raise AssertionError("manual start should not run")

        with (
            patch.object(restart_cockpit, "process_command", return_value="/x/scripts/cockpit_server.py --host 127.0.0.1 --port 8770"),
            patch.object(restart_cockpit, "wait_for_exit", return_value=True),
            patch.object(restart_cockpit, "wait_for_launchd_restart", return_value=True),
            patch.object(restart_cockpit.os, "kill") as kill,
            patch.object(restart_cockpit, "start_cockpit", side_effect=fake_start),
        ):
            result = restart_cockpit.restart_cockpit(pid=123, host="127.0.0.1", port=8770, delay=0)

        self.assertEqual(result, 0)
        kill.assert_called_once()
        self.assertEqual(starts, [])

    def test_restart_starts_server_when_launchd_does_not_revive_it(self) -> None:
        class Completed:
            returncode = 0
            stdout = "Samantha Cockpit spuštěn"
            stderr = ""

        with (
            patch.object(restart_cockpit, "process_command", return_value="/x/scripts/cockpit_server.py --host 127.0.0.1 --port 8770"),
            patch.object(restart_cockpit, "wait_for_exit", return_value=True),
            patch.object(restart_cockpit, "wait_for_launchd_restart", return_value=False),
            patch.object(restart_cockpit.os, "kill"),
            patch.object(restart_cockpit, "start_cockpit", return_value=Completed()) as start,
        ):
            result = restart_cockpit.restart_cockpit(pid=123, host="127.0.0.1", port=8770, delay=0)

        self.assertEqual(result, 0)
        start.assert_called_once_with("127.0.0.1", 8770)


if __name__ == "__main__":
    unittest.main()
