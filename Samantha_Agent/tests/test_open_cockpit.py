import sys
import unittest
from unittest.mock import patch

from scripts import open_cockpit


class OpenCockpitTests(unittest.TestCase):
    def test_main_starts_fallback_when_default_port_is_busy_and_unresponsive(self) -> None:
        with (
            patch.object(sys, "argv", ["open_cockpit.py", "--no-open"]),
            patch.object(open_cockpit, "FALLBACK_PORTS", [8771]),
            patch.object(open_cockpit, "url_ok", return_value=False),
            patch.object(open_cockpit, "port_is_busy", side_effect=[True, False]),
            patch.object(open_cockpit, "start_server") as start_server,
            patch.object(open_cockpit, "wait_until_ok", return_value=True),
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


if __name__ == "__main__":
    unittest.main()
