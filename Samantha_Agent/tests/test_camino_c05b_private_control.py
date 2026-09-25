from __future__ import annotations

import hashlib
import json
import sqlite3
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.workflows.commands import WORKFLOW_COMMANDS
from camino.domain.revision_store import RevisionStore
from scripts import camino_c05b_private_control as control


class _FakeProcess:
    pid = 5252

    def __init__(self, argv, **kwargs):
        self.argv = list(argv)
        self.kwargs = kwargs
        self.terminated = False

    def terminate(self) -> None:
        self.terminated = True

    def wait(self, timeout=None) -> int:
        return 0


class CaminoC05bPrivateControlTests(unittest.TestCase):
    @staticmethod
    def _baseline() -> dict[str, object]:
        return {
            "TCP": {"443": {"HTTPS": True}},
            "Web": {
                "private.example.ts.net:443": {
                    "Handlers": {"/": {"Proxy": "http://127.0.0.1:8770"}}
                }
            },
        }

    def _config(self, root: Path) -> control.ControlConfig:
        tools = root / "tools"
        tools.mkdir()
        paths = [tools / name for name in ("tailscale", "python", "pbcopy")]
        for path in paths:
            path.write_text("test\n", encoding="utf-8")
        return control.ControlConfig(
            state_root=root / "private-state",
            tailscale_cli=paths[0], python=paths[1], pbcopy=paths[2], port=18766,
        )

    def test_script_can_be_invoked_directly(self) -> None:
        script = Path(control.__file__).resolve()
        result = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=script.parents[1],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("usage:", result.stdout)

    def test_registered_lifecycle_is_fixed_and_confirmation_gated(self) -> None:
        with mock.patch.dict(control.os.environ, {"CAMINO_VIEWER_ENABLED": "1"}):
            environment = control._server_environment(Path("/synthetic/run"), storage_fault=False)
        self.assertEqual(environment["CAMINO_VIEWER_ENABLED"], "0")
        commands = {item.command_id: item for item in WORKFLOW_COMMANDS}
        for action in ("start", "copy_url", "copy_token", "status", "stop"):
            command = commands[f"camino_c05b_private_{action}"]
            self.assertEqual("camino_c05b_private_control.py", Path(command.argv[-2]).name)
            self.assertEqual(action.replace("_", "-"), command.argv[-1])
            self.assertEqual(action != "status", command.requires_confirmation)
            self.assertNotIn("funnel", command.command_id)
        self.assertEqual(
            "storage-full-on",
            commands["camino_c05b_private_storage_full_on"].argv[-1],
        )
        self.assertEqual(
            "storage-full-off",
            commands["camino_c05b_private_storage_full_off"].argv[-1],
        )
        self.assertEqual(
            "rotate-epoch", commands["camino_c05b_private_rotate_epoch"].argv[-1]
        )
        for command_id in (
            "camino_c05b_private_storage_full_on",
            "camino_c05b_private_storage_full_off",
            "camino_c05b_private_rotate_epoch",
        ):
            self.assertTrue(commands[command_id].requires_confirmation)

    def test_copy_url_requires_live_owned_route_and_keeps_value_out_of_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self._config(Path(temp_dir))
            config.state_root.mkdir(mode=0o700)
            address = "https://private.example.ts.net/camino-api"
            config.current_path.write_text(
                json.dumps({"schema": 1, "phase": "ready", "base_url": address}),
                encoding="utf-8",
            )
            copied: list[str] = []
            with (
                mock.patch.object(control, "_validate_state_paths"),
                mock.patch.object(control, "_owned_server_alive", return_value=True),
                mock.patch.object(control, "_serve_state", return_value={}),
                mock.patch.object(
                    control, "_route_proxy",
                    return_value=f"http://{control.LOOPBACK_HOST}:{config.port}",
                ),
                mock.patch.object(control, "_funnel_enabled", return_value=False),
                mock.patch.object(
                    control, "_copy_to_clipboard",
                    side_effect=lambda value, _config: copied.append(value),
                ),
            ):
                result = control.copy_url(config)
            self.assertEqual([address], copied)
            self.assertIn("URL_READY", result)
            self.assertNotIn(address, result)

    def test_route_is_separate_from_cockpit_and_funnel_stays_explicit(self) -> None:
        baseline = self._baseline()
        self.assertIsNone(control._route_proxy(baseline))
        changed = json.loads(json.dumps(baseline))
        handlers = changed["Web"]["private.example.ts.net:443"]["Handlers"]
        expected_proxy = f"http://127.0.0.1:{control.DEFAULT_PORT}"
        handlers[control.ROUTE_PATH] = {"Proxy": expected_proxy}
        self.assertEqual(expected_proxy, control._route_proxy(changed))
        self.assertEqual("http://127.0.0.1:8770", handlers["/"]["Proxy"])
        self.assertFalse(control._funnel_enabled(changed))
        self.assertTrue(control._funnel_enabled({"AllowFunnel": {"443": True}}))

    def test_start_keeps_token_out_of_output_and_stores_only_hash_in_auth_db(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self._config(Path(temp_dir))
            baseline = self._baseline()
            active = False

            def runner(argv):
                nonlocal active
                command = list(argv)
                if command[1:] == ["status", "--json"]:
                    body = {
                        "BackendState": "Running",
                        "Self": {"Online": True, "DNSName": "private.example.ts.net."},
                    }
                elif command[1:] == ["serve", "status", "--json"]:
                    body = json.loads(json.dumps(baseline))
                    if active:
                        body["Web"]["private.example.ts.net:443"]["Handlers"][
                            control.ROUTE_PATH
                        ] = {"Proxy": f"http://{control.LOOPBACK_HOST}:{config.port}"}
                elif command[1:] == ["funnel", "status", "--json"]:
                    body = baseline
                elif command[1:6] == [
                    "serve", "--yes", "--bg", "--https=443",
                    f"--set-path={control.ROUTE_PATH}",
                ]:
                    active = True
                    return subprocess.CompletedProcess(command, 0, "", "")
                else:
                    self.fail(f"unexpected command: {command}")
                return subprocess.CompletedProcess(command, 0, json.dumps(body), "")

            copied: list[str] = []
            processes: list[_FakeProcess] = []

            def popen(argv, **kwargs):
                process = _FakeProcess(argv, **kwargs)
                processes.append(process)
                return process

            with (
                mock.patch.object(control.network, "_ensure_port_available"),
                mock.patch.object(control, "_wait_for_health"),
                mock.patch.object(
                    control, "_http_json",
                    return_value=(200, {"scope": "c05a_private_owner"}),
                ),
                mock.patch.object(control, "_cockpit_root_healthy", return_value=True),
                mock.patch.object(control.subprocess, "Popen", side_effect=popen),
                mock.patch.object(
                    control, "_copy_to_clipboard",
                    side_effect=lambda value, _config: copied.append(value),
                ),
            ):
                result = control.start(config, runner=runner)

            self.assertIn("READY", result)
            self.assertNotIn("Bearer", result)
            self.assertEqual(["https://private.example.ts.net/camino-api"], copied)
            self.assertEqual(1, len(processes))
            state = json.loads(config.current_path.read_text(encoding="utf-8"))
            token_path = Path(state["token_path"])
            token = token_path.read_text(encoding="utf-8")
            self.assertGreaterEqual(len(token.encode("utf-8")), 32)
            self.assertEqual(0, stat.S_IMODE(token_path.stat().st_mode) & 0o077)
            with sqlite3.connect(state["auth_db"]) as database:
                row = database.execute(
                    "SELECT token_sha256, revoked_at FROM owner_tokens"
                ).fetchone()
            self.assertEqual(hashlib.sha256(token.encode()).hexdigest(), row[0])
            self.assertIsNone(row[1])
            self.assertNotIn(token, result)

    def test_stop_removes_only_owned_route_revokes_token_and_preserves_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self._config(Path(temp_dir))
            baseline = self._baseline()
            active = False

            def runner(argv):
                nonlocal active
                command = list(argv)
                if command[1:] == ["status", "--json"]:
                    body = {
                        "BackendState": "Running",
                        "Self": {"Online": True, "DNSName": "private.example.ts.net."},
                    }
                elif command[1:] == ["serve", "status", "--json"]:
                    body = json.loads(json.dumps(baseline))
                    if active:
                        body["Web"]["private.example.ts.net:443"]["Handlers"][
                            control.ROUTE_PATH
                        ] = {"Proxy": f"http://{control.LOOPBACK_HOST}:{config.port}"}
                elif command[1:] == ["funnel", "status", "--json"]:
                    body = baseline
                elif command[1:6] == [
                    "serve", "--yes", "--bg", "--https=443",
                    f"--set-path={control.ROUTE_PATH}",
                ]:
                    active = True
                    return subprocess.CompletedProcess(command, 0, "", "")
                elif command[1:5] == [
                    "serve", "--yes", "--https=443", f"--set-path={control.ROUTE_PATH}",
                ] and command[-1] == "off":
                    active = False
                    return subprocess.CompletedProcess(command, 0, "", "")
                else:
                    self.fail(f"unexpected command: {command}")
                return subprocess.CompletedProcess(command, 0, json.dumps(body), "")

            with (
                mock.patch.object(control.network, "_ensure_port_available"),
                mock.patch.object(control, "_wait_for_health"),
                mock.patch.object(
                    control, "_http_json",
                    return_value=(200, {"scope": "c05a_private_owner"}),
                ),
                mock.patch.object(control, "_cockpit_root_healthy", return_value=True),
                mock.patch.object(control.subprocess, "Popen", return_value=_FakeProcess([], env={})),
                mock.patch.object(control, "_copy_to_clipboard"),
            ):
                control.start(config, runner=runner)

            state = json.loads(config.current_path.read_text(encoding="utf-8"))
            with mock.patch.object(control, "_terminate_owned_server"):
                result = control.stop(config, runner=runner)

            self.assertIn("STOPPED", result)
            self.assertTrue(Path(state["run_dir"]).is_dir())
            self.assertTrue(Path(state["token_path"]).is_file())
            with sqlite3.connect(state["auth_db"]) as database:
                revoked = database.execute(
                    "SELECT revoked_at FROM owner_tokens WHERE id=?", (state["token_id"],)
                ).fetchone()[0]
            self.assertIsNotNone(revoked)
            completed = json.loads(config.current_path.read_text(encoding="utf-8"))
            self.assertEqual("stopped", completed["phase"])

    def test_fault_mode_and_epoch_rotation_keep_same_acceptance_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self._config(Path(temp_dir))
            run_dir = config.state_root / "run_test"
            run_dir.mkdir(parents=True)
            (run_dir / "media").mkdir()
            for directory in (config.state_root, run_dir, run_dir / "media"):
                directory.chmod(0o700)
            token = "t" * 48
            (run_dir / "token.txt").write_text(token, encoding="utf-8")
            (run_dir / "token.txt").chmod(0o600)
            auth = control.RevocableTokenStore(run_dir / "auth.sqlite")
            token_id = auth.add(token, label="test")
            RevisionStore(run_dir / "metadata.sqlite")
            for path in (run_dir / "media.sqlite", run_dir / "server.log"):
                path.write_bytes(b"")
                path.chmod(0o600)
            (run_dir / "serve-before.json").write_text("{}\n", encoding="utf-8")
            state = control._state_payload(
                run_dir=run_dir, server_pid=5252, token_id=token_id,
                base_url="https://private.example.ts.net/camino-api",
                config=config, started_at="2026-09-23T23:00:00+02:00",
            )
            control._write_private_json(config.current_path, state)
            control._write_private_json(run_dir / "run.json", state)

            def runner(argv):
                command = list(argv)
                if command[1:] == ["serve", "status", "--json"]:
                    body = self._baseline()
                    body["Web"]["private.example.ts.net:443"]["Handlers"][
                        control.ROUTE_PATH
                    ] = {"Proxy": f"http://{control.LOOPBACK_HOST}:{config.port}"}
                elif command[1:] == ["funnel", "status", "--json"]:
                    body = self._baseline()
                else:
                    self.fail(f"unexpected command: {command}")
                return subprocess.CompletedProcess(command, 0, json.dumps(body), "")

            with (
                mock.patch.object(control, "_owned_server_alive", return_value=True),
                mock.patch.object(control, "_terminate_owned_server"),
                mock.patch.object(
                    control, "_spawn_server", return_value=_FakeProcess([], env={})
                ) as spawn,
            ):
                self.assertIn("STORAGE_FAULT_ON", control.set_storage_fault(
                    True, config, runner=runner
                ))
                self.assertIn("EPOCH_ROTATED", control.rotate_epoch(config, runner=runner))

            spawn.assert_called_once_with(run_dir, token, config, storage_fault=True)
            updated = json.loads(config.current_path.read_text(encoding="utf-8"))
            self.assertTrue(updated["storage_fault"])
            state_now = RevisionStore(run_dir / "metadata.sqlite").state()
            self.assertTrue(state_now["reconciliation_required"])
            self.assertTrue(state_now["exports_blocked"])
            self.assertTrue((run_dir / "token.txt").is_file())


if __name__ == "__main__":
    unittest.main()
