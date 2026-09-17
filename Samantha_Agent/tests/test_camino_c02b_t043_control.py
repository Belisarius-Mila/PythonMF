from __future__ import annotations

import hashlib
import json
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.workflows.commands import WORKFLOW_COMMANDS
from scripts import camino_c02b_t043_control as control


class _FakeHTTPResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _FakeProcess:
    pid = 4242

    def __init__(self, argv, **kwargs):
        self.argv = list(argv)
        self.kwargs = kwargs
        self.terminated = False

    def terminate(self) -> None:
        self.terminated = True

    def wait(self, timeout=None) -> int:
        return 0


class CaminoC02bT043ControlTests(unittest.TestCase):
    def _config(self, root: Path) -> control.ControlConfig:
        tools = root / "tools"
        tools.mkdir()
        paths = [tools / name for name in ("tailscale", "python", "receiver.py", "pbcopy")]
        for path in paths:
            path.write_text("test\n", encoding="utf-8")
        return control.ControlConfig(
            state_root=root / "private-state",
            tailscale_cli=paths[0],
            python=paths[1],
            receiver=paths[2],
            pbcopy=paths[3],
            port=18765,
        )

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

    def test_route_parser_preserves_root_and_detects_only_explicit_funnel(self) -> None:
        baseline = self._baseline()
        self.assertIsNone(control._route_proxy(baseline))
        self.assertFalse(control._funnel_enabled(baseline))

        changed = json.loads(json.dumps(baseline))
        handlers = changed["Web"]["private.example.ts.net:443"]["Handlers"]
        handlers[control.ROUTE_PATH] = {"Proxy": "http://127.0.0.1:8765"}
        self.assertEqual("http://127.0.0.1:8765", control._route_proxy(changed))
        self.assertEqual("http://127.0.0.1:8770", handlers["/"]["Proxy"])
        self.assertTrue(control._funnel_enabled({"AllowFunnel": {"443": True}}))

    def test_registered_commands_are_fixed_and_confirmation_gated(self) -> None:
        commands = {item.command_id: item for item in WORKFLOW_COMMANDS}
        expected_actions = {
            "camino_c02b_t043_start": ("start", True),
            "camino_c02b_t043_copy_token": ("copy-token", True),
            "camino_c02b_t043_status": ("status", False),
            "camino_c02b_t043_stop": ("stop", True),
        }
        for command_id, (action, confirmation) in expected_actions.items():
            command = commands[command_id]
            self.assertEqual("camino_c02b_t043_control.py", Path(command.argv[-2]).name)
            self.assertEqual(action, command.argv[-1])
            self.assertEqual(confirmation, command.requires_confirmation)

    def test_receiver_module_entrypoint_does_not_shadow_standard_email(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", control.RECEIVER_MODULE, "--help"],
            cwd=str(control.PROJECT_ROOT),
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Camino C02b chunk receiver", completed.stdout)

    def test_system_tls_context_keeps_verification_and_loads_mac_ca_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = Path(temp_dir) / "cert.pem"
            bundle.write_text("test CA bundle\n", encoding="utf-8")
            fake_context = mock.Mock()
            with (
                mock.patch.object(control.ssl, "create_default_context", return_value=fake_context),
                mock.patch.object(control, "SYSTEM_CA_BUNDLE", bundle),
            ):
                result = control._system_tls_context()

        self.assertIs(fake_context, result)
        fake_context.load_verify_locations.assert_called_once_with(cafile=str(bundle))

    def test_start_uses_exact_private_route_and_keeps_token_out_of_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self._config(Path(temp_dir))
            baseline = self._baseline()
            active = False
            calls: list[list[str]] = []

            def runner(argv):
                nonlocal active
                command = list(argv)
                calls.append(command)
                if command[1:] == ["status", "--json"]:
                    body = {
                        "BackendState": "Running",
                        "Self": {"Online": True, "DNSName": "private.example.ts.net."},
                    }
                elif command[1:] == ["serve", "status", "--json"]:
                    body = json.loads(json.dumps(baseline))
                    if active:
                        body["Web"]["private.example.ts.net:443"]["Handlers"][control.ROUTE_PATH] = {
                            "Proxy": f"http://{control.LOOPBACK_HOST}:{config.port}"
                        }
                elif command[1:] == ["funnel", "status", "--json"]:
                    body = baseline
                elif command[1:6] == [
                    "serve",
                    "--yes",
                    "--bg",
                    "--https=443",
                    f"--set-path={control.ROUTE_PATH}",
                ]:
                    active = True
                    return subprocess.CompletedProcess(command, 0, "", "")
                else:
                    self.fail(f"unexpected command: {command}")
                return subprocess.CompletedProcess(command, 0, json.dumps(body), "")

            copied: list[str] = []
            fake_processes: list[_FakeProcess] = []

            def popen(argv, **kwargs):
                process = _FakeProcess(argv, **kwargs)
                fake_processes.append(process)
                return process

            with (
                mock.patch.object(control, "_ensure_port_available"),
                mock.patch.object(control, "_wait_for_health"),
                mock.patch.object(
                    control,
                    "_http_json",
                    return_value=(200, {"scope": "c02b_synthetic_only"}),
                ),
                mock.patch.object(control.urllib.request, "urlopen", return_value=_FakeHTTPResponse()),
                mock.patch.object(control.subprocess, "Popen", side_effect=popen),
                mock.patch.object(control, "_copy_to_clipboard", side_effect=lambda value, _config: copied.append(value)),
            ):
                result = control.start(config, runner=runner)

            self.assertIn("READY", result)
            self.assertNotIn("Bearer", result)
            self.assertEqual(["https://private.example.ts.net/camino-c02b"], copied)
            self.assertEqual(1, len(fake_processes))
            receiver_argv = fake_processes[0].argv
            token = fake_processes[0].kwargs["env"]["CAMINO_C02B_TOKEN"]
            self.assertNotIn(token, receiver_argv)
            self.assertEqual(["-m", control.RECEIVER_MODULE], receiver_argv[1:3])
            self.assertIn("--read-delay-ms-per-mib", receiver_argv)
            self.assertIn("1000", receiver_argv)
            self.assertIn("--verify-delay-seconds", receiver_argv)
            self.assertIn("5", receiver_argv)
            self.assertIn(
                [
                    str(config.tailscale_cli),
                    "serve",
                    "--yes",
                    "--bg",
                    "--https=443",
                    f"--set-path={control.ROUTE_PATH}",
                    f"http://{control.LOOPBACK_HOST}:{config.port}",
                ],
                calls,
            )
            state = json.loads(config.current_path.read_text(encoding="utf-8"))
            token_path = Path(state["token_path"])
            self.assertEqual(token, token_path.read_text(encoding="utf-8"))
            self.assertEqual(stat.S_IMODE(token_path.stat().st_mode), 0o600)

    def test_copy_token_and_stop_restore_exact_baseline_without_deleting_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = self._config(root)
            control._private_directory(config.state_root)
            run_dir = config.state_root / "run_test"
            receiver_root = run_dir / "receiver"
            control._private_directory(receiver_root)
            for name in ("objects", "receipts"):
                control._private_directory(receiver_root / name)
            token_path = run_dir / "token.txt"
            token = "t" * 48
            control._write_private_text(token_path, token, exclusive=True)
            baseline_path = run_dir / "serve-before.json"
            baseline = self._baseline()
            control._write_private_json(baseline_path, baseline)
            state = {
                "schema": 1,
                "phase": "ready",
                "run_dir": str(run_dir),
                "receiver_pid": 4242,
                "receiver_root": str(receiver_root),
                "receiver_log": str(run_dir / "receiver.log"),
                "token_path": str(token_path),
                "serve_before_path": str(baseline_path),
                "route_path": control.ROUTE_PATH,
                "port": config.port,
            }
            control._write_private_json(config.current_path, state)
            active = True
            calls: list[list[str]] = []

            def runner(argv):
                nonlocal active
                command = list(argv)
                calls.append(command)
                if command[1:] == ["serve", "status", "--json"]:
                    body = json.loads(json.dumps(baseline))
                    if active:
                        body["Web"]["private.example.ts.net:443"]["Handlers"][control.ROUTE_PATH] = {
                            "Proxy": f"http://{control.LOOPBACK_HOST}:{config.port}"
                        }
                    return subprocess.CompletedProcess(command, 0, json.dumps(body), "")
                if command[1:] == ["funnel", "status", "--json"]:
                    return subprocess.CompletedProcess(command, 0, json.dumps(baseline), "")
                if command[-1] == "off":
                    active = False
                    return subprocess.CompletedProcess(command, 0, "", "")
                self.fail(f"unexpected command: {command}")

            copied: list[str] = []
            with (
                mock.patch.object(control, "_owned_receiver_alive", return_value=True),
                mock.patch.object(control, "_copy_to_clipboard", side_effect=lambda value, _config: copied.append(value)),
            ):
                result = control.copy_token(config, runner=runner)
            self.assertEqual([token], copied)
            self.assertNotIn(token, result)

            with mock.patch.object(control, "_terminate_owned_receiver") as terminate:
                stopped = control.stop(config, runner=runner)
            terminate.assert_called_once()
            self.assertIn("Original Serve configuration restored exactly", stopped)
            self.assertTrue(token_path.exists())
            final_state = json.loads(config.current_path.read_text(encoding="utf-8"))
            self.assertEqual("stopped", final_state["phase"])
            self.assertIn(
                [
                    str(config.tailscale_cli),
                    "serve",
                    "--yes",
                    "--https=443",
                    f"--set-path={control.ROUTE_PATH}",
                    "off",
                ],
                calls,
            )

    def test_evidence_verifies_multiple_distinct_assets_without_false_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            receiver_root = Path(temp_dir) / "receiver"
            objects = receiver_root / "objects"
            receipts = receiver_root / "receipts"
            objects.mkdir(parents=True)
            receipts.mkdir()
            expected_bytes = 0
            for asset_id, body in (("asset-one", b"first"), ("asset-two", b"second")):
                (objects / f"{asset_id}.bin").write_bytes(body)
                (receipts / f"{asset_id}.json").write_text(
                    json.dumps(
                        {
                            "schema": 1,
                            "asset_id": asset_id,
                            "byte_count": len(body),
                            "sha256": hashlib.sha256(body).hexdigest(),
                            "chunk_count": 1,
                            "state": "verified",
                            "content_kind": "synthetic",
                        }
                    ),
                    encoding="utf-8",
                )
                expected_bytes += len(body)

            evidence = control._evidence({"receiver_root": str(receiver_root)})

            self.assertEqual(2, evidence["object_count"])
            self.assertEqual(2, evidence["receipt_count"])
            self.assertTrue(evidence["verified_match"])
            self.assertEqual(expected_bytes, evidence["byte_count"])

    def test_evidence_fails_closed_when_one_asset_receipt_does_not_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            receiver_root = Path(temp_dir) / "receiver"
            objects = receiver_root / "objects"
            receipts = receiver_root / "receipts"
            objects.mkdir(parents=True)
            receipts.mkdir()
            body = b"source"
            (objects / "asset-one.bin").write_bytes(body)
            (receipts / "asset-one.json").write_text(
                json.dumps(
                    {
                        "asset_id": "asset-one",
                        "byte_count": len(body),
                        "sha256": "0" * 64,
                        "state": "verified",
                    }
                ),
                encoding="utf-8",
            )

            evidence = control._evidence({"receiver_root": str(receiver_root)})

            self.assertFalse(evidence["verified_match"])
            self.assertEqual(0, evidence["byte_count"])


if __name__ == "__main__":
    unittest.main()
