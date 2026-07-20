from __future__ import annotations

import tempfile
import unittest
import json
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
            with patch.object(controller, "_socket_reachable", return_value=True), patch.object(
                controller, "_adopt_reachable_owner", return_value=False
            ), patch(
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
            process.pid = 4321
            process.poll.return_value = None
            with patch.object(controller, "_socket_reachable", side_effect=[False, True, True]), patch.object(
                controller,
                "_process_identity",
                return_value=f"codex app-server --listen unix://{controller.socket_path}",
            ), patch(
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

    def test_persisted_owner_requires_exact_process_identity_and_group(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            socket_path = Path(temp_dir) / "server.sock"
            owner_path = Path(temp_dir) / "owner.json"
            controller = LocalAppServerProcessController(
                socket_path=socket_path,
                ownership_path=owner_path,
            )
            identity = f"codex app-server --listen unix://{controller.socket_path}"
            owner_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "pid": 321,
                        "process_identity": identity,
                        "socket_path": str(controller.socket_path),
                    }
                ),
                encoding="utf-8",
            )
            with patch.object(controller, "_process_identity", return_value=identity), patch(
                "app.communication.local_runtime.os.getpgid", return_value=321
            ):
                state, record = controller._persisted_owner_state()

        self.assertEqual(state, "running")
        self.assertEqual(record["pid"], 321)

    def test_reachable_exact_listener_can_be_adopted_for_future_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            socket_path = Path(temp_dir) / "server.sock"
            controller = LocalAppServerProcessController(socket_path=socket_path)
            identity = f"codex app-server --listen unix://{controller.socket_path}"
            completed = Mock(returncode=0, stdout="778\n")
            with patch(
                "app.communication.local_runtime.subprocess.run", return_value=completed
            ), patch(
                "app.communication.local_runtime.os.getpgid", return_value=777
            ), patch.object(
                controller, "_process_identity", return_value=identity
            ):
                adopted = controller._adopt_reachable_owner()

        self.assertTrue(adopted)

    def test_confirmed_owned_recovery_starts_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            socket_path = Path(temp_dir) / "server.sock"
            socket_path.write_text("stale", encoding="utf-8")
            controller = LocalAppServerProcessController(socket_path=socket_path)
            process = Mock()
            process.pid = 654
            process.poll.return_value = None

            def recover() -> bool:
                socket_path.unlink()
                return True

            with patch.object(controller, "_recover_persisted_owner", side_effect=recover) as recovery, patch.object(
                controller, "_socket_reachable", side_effect=[False, True, True]
            ), patch.object(
                controller,
                "_process_identity",
                return_value=f"codex app-server --listen unix://{socket_path}",
            ), patch(
                "app.communication.local_runtime.subprocess.Popen", return_value=process
            ):
                result = controller.start(recover_unreachable_owned=True)

        recovery.assert_called_once_with()
        self.assertTrue(result["started"])

    def test_stopped_owner_never_unlinks_socket_held_by_another_listener(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            socket_path = Path(temp_dir) / "server.sock"
            socket_path.write_text("occupied", encoding="utf-8")
            controller = LocalAppServerProcessController(socket_path=socket_path)
            with patch.object(
                controller,
                "_persisted_owner_state",
                return_value=("stopped", {"pid": 321, "process_identity": "old"}),
            ), patch.object(
                controller, "_socket_listener_pids", return_value=[999]
            ):
                recovered = controller._recover_persisted_owner()
                still_present = socket_path.exists()

        self.assertFalse(recovered)
        self.assertTrue(still_present)


if __name__ == "__main__":
    unittest.main()
