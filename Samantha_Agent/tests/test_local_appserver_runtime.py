from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from app.codex_appserver import AppServerError
from app.communication.local_runtime import LocalAppServerProcessController


class LocalAppServerProcessControllerTests(unittest.TestCase):
    def test_existing_reachable_socket_is_reused_without_spawning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            socket_path = Path(temp_dir) / "server.sock"
            socket_path.touch()
            controller = LocalAppServerProcessController(socket_path=socket_path)
            with patch.object(controller, "_socket_reachable", return_value=True), patch(
                "app.communication.local_runtime.subprocess.Popen"
            ) as popen:
                result = controller.start()

        self.assertFalse(result["started"])
        self.assertTrue(result["reachable"])
        popen.assert_not_called()

    def test_stale_socket_is_never_deleted_or_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            socket_path = Path(temp_dir) / "server.sock"
            socket_path.write_text("foreign", encoding="utf-8")
            controller = LocalAppServerProcessController(socket_path=socket_path)
            with patch.object(controller, "_socket_reachable", return_value=False), patch(
                "app.communication.local_runtime.subprocess.Popen"
            ) as popen:
                with self.assertRaises(AppServerError):
                    controller.start()
                still_present = socket_path.read_text(encoding="utf-8")

        self.assertEqual(still_present, "foreign")
        popen.assert_not_called()

    def test_new_process_listens_only_on_the_configured_unix_socket(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            socket_path = Path(temp_dir) / "server.sock"
            controller = LocalAppServerProcessController(socket_path=socket_path)
            process = Mock()
            process.poll.return_value = None
            with patch.object(controller, "_socket_reachable", side_effect=[False, True, True]), patch(
                "app.communication.local_runtime.subprocess.Popen", return_value=process
            ) as popen:
                result = controller.start()

        command = popen.call_args.args[0]
        self.assertEqual(command[:3], [controller.codex_binary, "app-server", "--listen"])
        self.assertEqual(command[3], f"unix://{controller.socket_path}")
        self.assertNotIn("127.0.0.1", " ".join(command))
        self.assertNotIn("0.0.0.0", " ".join(command))
        self.assertTrue(result["started"])
        self.assertTrue(result["owned_by_cockpit"])


if __name__ == "__main__":
    unittest.main()
