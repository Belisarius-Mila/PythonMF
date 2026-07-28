from __future__ import annotations

import io
import json
import os
import plistlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.family_calendar_delivery_automation_activation import (
    FamilyCalendarAutomationActivationError,
    apply_family_calendar_automation_activation,
    plan_family_calendar_automation_activation,
)
from app.family_calendar_delivery_automation_preview import (
    FAMILY_CALENDAR_AUTOMATION_CONFIRMATION,
)
from app.family_calendar_delivery_config import (
    DeliveryConfigMode,
    load_family_calendar_delivery_config,
)
from app.family_calendar_delivery_launchctl_load import (
    GLOBAL_SAFETY_BRAKE_CONFIRMATION,
)
from app.family_calendar_delivery_readiness import (
    FAMILY_CALENDAR_KEYCHAIN_SERVICE,
    FAMILY_CALENDAR_PLANNER_LABEL,
)
from scripts.family_calendar_delivery_automation_activate import main


PRIVATE_ADDRESS = "private-sender@example.invalid"
PRIVATE_EVENT_KEY = "private-person:birthday:2026-12-19"


class _FakeSystem:
    def __init__(
        self,
        paths: dict[str, Path],
        *,
        loaded: bool = True,
        bootout_results: list[int] | None = None,
        bootstrap_results: list[int] | None = None,
        security_results: list[int] | None = None,
        print_results: list[int] | None = None,
    ) -> None:
        self.paths = paths
        self.loaded = loaded
        self.bootout_results = list(bootout_results or [])
        self.bootstrap_results = list(bootstrap_results or [])
        self.security_results = list(security_results or [])
        self.print_results = list(print_results or [])
        self.calls: list[tuple[str, ...]] = []
        self.mutation_modes: list[tuple[str, str]] = []

    def run(self, argv) -> int:
        call = tuple(str(item) for item in argv)
        self.calls.append(call)
        if call[0] == str(self.paths["security"]):
            return self.security_results.pop(0) if self.security_results else 0
        if call[1] == "print":
            if self.print_results:
                return self.print_results.pop(0)
            return 0 if self.loaded else 113
        if call[1] == "bootout":
            self.mutation_modes.append(("bootout", self._config_mode()))
            status = self.bootout_results.pop(0) if self.bootout_results else 0
            if status == 0:
                self.loaded = False
            return status
        if call[1] == "bootstrap":
            self.mutation_modes.append(("bootstrap", self._config_mode()))
            status = self.bootstrap_results.pop(0) if self.bootstrap_results else 0
            if status == 0:
                self.loaded = True
            return status
        raise AssertionError(f"Unexpected simulated command: {call[1:2]!r}")

    def locate(self, name: str) -> str | None:
        path = self.paths.get(name)
        return str(path) if path is not None else None

    def mutation_calls(self) -> list[tuple[str, ...]]:
        return [
            call
            for call in self.calls
            if len(call) > 1 and call[1] in {"bootout", "bootstrap"}
        ]

    def _config_mode(self) -> str:
        return load_family_calendar_delivery_config(
            self.paths["config"]
        ).mode.value


class FamilyCalendarAutomationActivationTests(unittest.TestCase):
    def test_plan_is_redacted_read_only_and_exposes_exact_gate(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _paths(Path(temp_dir))
            _prepare_inputs(paths)
            system = _FakeSystem(paths)
            before = _snapshot(paths)

            plan = _plan(paths, system)
            document = plan.safe_document()
            rendered = json.dumps(document, ensure_ascii=False)
            after = _snapshot(paths)

        self.assertEqual(before, after)
        self.assertEqual(document["status"], "preview")
        self.assertTrue(document["activation_implementation_available"])
        self.assertTrue(document["apply_available"])
        self.assertFalse(document["automatic_sending_enabled"])
        self.assertEqual(
            document["required_global_confirmation"],
            GLOBAL_SAFETY_BRAKE_CONFIRMATION,
        )
        self.assertEqual(
            document["required_confirmation"],
            FAMILY_CALENDAR_AUTOMATION_CONFIRMATION,
        )
        self.assertFalse(document["writes_performed"])
        self.assertFalse(document["launchctl_mutation_called"])
        self.assertFalse(document["secret_read"])
        self.assertFalse(document["transport_called"])
        self.assertEqual(system.mutation_calls(), [])
        self.assertNotIn(PRIVATE_ADDRESS, rendered)
        self.assertNotIn(PRIVATE_EVENT_KEY, rendered)
        keychain_calls = [
            call for call in system.calls if "find-generic-password" in call
        ]
        self.assertEqual(len(keychain_calls), 1)
        self.assertIn(FAMILY_CALENDAR_KEYCHAIN_SERVICE, keychain_calls[0])
        self.assertNotIn("-w", keychain_calls[0])
        self.assertNotIn("-g", keychain_calls[0])

    def test_each_confirmation_and_fingerprint_mismatch_blocks_before_mutation(
        self,
    ) -> None:
        cases = (
            ("global_confirmation", "wrong", "global_confirmation"),
            ("confirmation", "wrong", "confirmation"),
            ("expected_fingerprint", "0" * 64, "fingerprint"),
        )
        for argument, wrong_value, expected_stage in cases:
            with self.subTest(argument=argument):
                with tempfile.TemporaryDirectory(
                    dir="/private/tmp"
                ) as temp_dir:
                    paths = _paths(Path(temp_dir))
                    _prepare_inputs(paths)
                    system = _FakeSystem(paths)
                    plan = _plan(paths, system)
                    kwargs = _confirmations(plan)
                    kwargs[argument] = wrong_value

                    with self.assertRaises(
                        FamilyCalendarAutomationActivationError
                    ) as raised:
                        apply_family_calendar_automation_activation(
                            plan,
                            command_runner=system.run,
                            executable_locator=system.locate,
                            **kwargs,
                        )

                    error = raised.exception.safe_document()
                    config = load_family_calendar_delivery_config(
                        paths["config"]
                    )

                self.assertEqual(raised.exception.stage, expected_stage)
                self.assertFalse(error["writes_performed"])
                self.assertFalse(error["launchctl_mutation_called"])
                self.assertTrue(error["retry_safe"])
                self.assertEqual(config.mode, DeliveryConfigMode.DRY_RUN)
                self.assertEqual(system.mutation_calls(), [])

    def test_changed_state_blocks_recheck_before_mutation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _paths(Path(temp_dir))
            _prepare_inputs(paths)
            system = _FakeSystem(paths)
            plan = _plan(paths, system)
            _write_blocking_state(paths["state"])

            with self.assertRaises(
                FamilyCalendarAutomationActivationError
            ) as raised:
                apply_family_calendar_automation_activation(
                    plan,
                    command_runner=system.run,
                    executable_locator=system.locate,
                    **_confirmations(plan),
                )

            config = load_family_calendar_delivery_config(paths["config"])

        self.assertEqual(raised.exception.stage, "plan_recheck")
        self.assertFalse(raised.exception.mutation_attempted)
        self.assertEqual(config.mode, DeliveryConfigMode.DRY_RUN)
        self.assertEqual(system.mutation_calls(), [])

    def test_success_unloads_then_changes_only_mode_and_reloads(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _paths(Path(temp_dir))
            _prepare_inputs(paths)
            system = _FakeSystem(paths)
            source_document = json.loads(
                paths["config"].read_text(encoding="utf-8")
            )
            plan = _plan(paths, system)

            result = apply_family_calendar_automation_activation(
                plan,
                command_runner=system.run,
                executable_locator=system.locate,
                **_confirmations(plan),
            )

            target_document = json.loads(
                paths["config"].read_text(encoding="utf-8")
            )
            document = result.safe_document()
            mode = os.stat(paths["config"]).st_mode & 0o777

        self.assertEqual(
            {key for key in source_document if source_document[key] != target_document[key]},
            {"mode"},
        )
        self.assertEqual(target_document["mode"], "enabled")
        self.assertEqual(mode, 0o600)
        self.assertEqual(
            system.mutation_modes,
            [("bootout", "dry_run"), ("bootstrap", "enabled")],
        )
        self.assertTrue(system.loaded)
        self.assertEqual(document["status"], "activated")
        self.assertTrue(document["automatic_sending_enabled"])
        self.assertTrue(document["writes_performed"])
        self.assertFalse(document["secret_read"])
        self.assertFalse(document["transport_called"])
        self.assertFalse(paths["state"].exists())
        keychain_calls = [
            call for call in system.calls if "find-generic-password" in call
        ]
        self.assertTrue(keychain_calls)
        self.assertTrue(
            all("-w" not in call and "-g" not in call for call in keychain_calls)
        )

    def test_unload_failure_rolls_back_to_loaded_dry_run(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _paths(Path(temp_dir))
            _prepare_inputs(paths)
            system = _FakeSystem(paths, bootout_results=[5, 0])
            plan = _plan(paths, system)

            with self.assertRaises(
                FamilyCalendarAutomationActivationError
            ) as raised:
                apply_family_calendar_automation_activation(
                    plan,
                    command_runner=system.run,
                    executable_locator=system.locate,
                    **_confirmations(plan),
                )

            config = load_family_calendar_delivery_config(paths["config"])
            document = raised.exception.safe_document()

        self.assertEqual(raised.exception.stage, "unload_verification")
        self.assertEqual(config.mode, DeliveryConfigMode.DRY_RUN)
        self.assertTrue(system.loaded)
        self.assertTrue(document["rollback_attempted"])
        self.assertTrue(document["rollback_confirmed"])
        self.assertFalse(document["config_write_attempted"])
        self.assertFalse(document["retry_safe"])
        self.assertFalse(document["manual_audit_required"])

    def test_atomic_write_failure_restores_loaded_dry_run(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _paths(Path(temp_dir))
            _prepare_inputs(paths)
            system = _FakeSystem(paths)
            plan = _plan(paths, system)

            with patch(
                "app.family_calendar_delivery_automation_activation."
                "atomic_replace_text_under_external_lock",
                side_effect=OSError("synthetic write failure"),
            ):
                with self.assertRaises(
                    FamilyCalendarAutomationActivationError
                ) as raised:
                    apply_family_calendar_automation_activation(
                        plan,
                        command_runner=system.run,
                        executable_locator=system.locate,
                        **_confirmations(plan),
                    )

            config = load_family_calendar_delivery_config(paths["config"])
            document = raised.exception.safe_document()

        self.assertEqual(raised.exception.stage, "configuration_write")
        self.assertEqual(config.mode, DeliveryConfigMode.DRY_RUN)
        self.assertTrue(system.loaded)
        self.assertTrue(document["config_write_attempted"])
        self.assertFalse(document["config_write_confirmed"])
        self.assertTrue(document["rollback_confirmed"])
        self.assertFalse(document["manual_audit_required"])
        self.assertNotIn("synthetic write failure", json.dumps(document))

    def test_runtime_race_after_write_restores_loaded_dry_run(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _paths(Path(temp_dir))
            _prepare_inputs(paths)
            system = _FakeSystem(
                paths,
                print_results=[0, 0, 113, 113, 0],
            )
            plan = _plan(paths, system)

            with self.assertRaises(
                FamilyCalendarAutomationActivationError
            ) as raised:
                apply_family_calendar_automation_activation(
                    plan,
                    command_runner=system.run,
                    executable_locator=system.locate,
                    **_confirmations(plan),
                )

            config = load_family_calendar_delivery_config(paths["config"])
            document = raised.exception.safe_document()

        self.assertEqual(raised.exception.stage, "runtime_verification")
        self.assertEqual(config.mode, DeliveryConfigMode.DRY_RUN)
        self.assertTrue(system.loaded)
        self.assertTrue(document["config_write_attempted"])
        self.assertTrue(document["config_write_confirmed"])
        self.assertTrue(document["rollback_confirmed"])

    def test_load_failure_restores_loaded_dry_run(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _paths(Path(temp_dir))
            _prepare_inputs(paths)
            system = _FakeSystem(paths, bootstrap_results=[5, 0])
            plan = _plan(paths, system)

            with self.assertRaises(
                FamilyCalendarAutomationActivationError
            ) as raised:
                apply_family_calendar_automation_activation(
                    plan,
                    command_runner=system.run,
                    executable_locator=system.locate,
                    **_confirmations(plan),
                )

            config = load_family_calendar_delivery_config(paths["config"])
            document = raised.exception.safe_document()

        self.assertEqual(raised.exception.stage, "load_verification")
        self.assertEqual(config.mode, DeliveryConfigMode.DRY_RUN)
        self.assertTrue(system.loaded)
        self.assertTrue(document["config_write_confirmed"])
        self.assertTrue(document["rollback_confirmed"])
        self.assertEqual(
            system.mutation_modes,
            [
                ("bootout", "dry_run"),
                ("bootstrap", "enabled"),
                ("bootout", "enabled"),
                ("bootstrap", "dry_run"),
            ],
        )

    def test_readiness_failure_restores_loaded_dry_run(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _paths(Path(temp_dir))
            _prepare_inputs(paths)
            system = _FakeSystem(
                paths,
                security_results=[0, 0, 44, 0],
            )
            plan = _plan(paths, system)

            with self.assertRaises(
                FamilyCalendarAutomationActivationError
            ) as raised:
                apply_family_calendar_automation_activation(
                    plan,
                    command_runner=system.run,
                    executable_locator=system.locate,
                    **_confirmations(plan),
                )

            config = load_family_calendar_delivery_config(paths["config"])
            document = raised.exception.safe_document()

        self.assertEqual(raised.exception.stage, "readiness_verification")
        self.assertEqual(config.mode, DeliveryConfigMode.DRY_RUN)
        self.assertTrue(system.loaded)
        self.assertTrue(document["rollback_confirmed"])
        self.assertFalse(document["manual_audit_required"])

    def test_failed_rollback_leaves_enabled_state_for_manual_audit(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _paths(Path(temp_dir))
            _prepare_inputs(paths)
            system = _FakeSystem(
                paths,
                bootout_results=[0, 5],
                security_results=[0, 0, 44],
            )
            plan = _plan(paths, system)

            with self.assertRaises(
                FamilyCalendarAutomationActivationError
            ) as raised:
                apply_family_calendar_automation_activation(
                    plan,
                    command_runner=system.run,
                    executable_locator=system.locate,
                    **_confirmations(plan),
                )

            config = load_family_calendar_delivery_config(paths["config"])
            document = raised.exception.safe_document()

        self.assertEqual(raised.exception.stage, "readiness_verification")
        self.assertEqual(config.mode, DeliveryConfigMode.ENABLED)
        self.assertTrue(system.loaded)
        self.assertFalse(document["rollback_confirmed"])
        self.assertTrue(document["manual_audit_required"])
        self.assertFalse(document["retry_safe"])
        self.assertEqual(document["runtime_state"], "loaded")
        self.assertEqual(document["config_mode"], "enabled")

    def test_cli_requires_apply_and_emits_only_redacted_documents(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _paths(Path(temp_dir))
            _prepare_inputs(paths)
            preview_system = _FakeSystem(paths)
            preview_output = io.StringIO()

            preview_exit = main(
                _cli_paths(paths),
                command_runner=preview_system.run,
                executable_locator=preview_system.locate,
                output=preview_output,
            )
            preview_document = json.loads(preview_output.getvalue())
            apply_system = _FakeSystem(paths)
            apply_output = io.StringIO()
            apply_exit = main(
                [
                    *_cli_paths(paths),
                    "--apply",
                    "--global-confirmation",
                    GLOBAL_SAFETY_BRAKE_CONFIRMATION,
                    "--confirmation",
                    FAMILY_CALENDAR_AUTOMATION_CONFIRMATION,
                    "--expected-fingerprint",
                    preview_document["plan_fingerprint"],
                ],
                command_runner=apply_system.run,
                executable_locator=apply_system.locate,
                output=apply_output,
            )
            lines = [
                json.loads(line)
                for line in apply_output.getvalue().splitlines()
            ]

        self.assertEqual(preview_exit, 0)
        self.assertEqual(preview_document["status"], "preview")
        self.assertEqual(preview_system.mutation_calls(), [])
        self.assertEqual(apply_exit, 0)
        self.assertEqual([line["status"] for line in lines], ["preview", "activated"])
        self.assertNotIn(PRIVATE_ADDRESS, apply_output.getvalue())
        self.assertTrue(lines[1]["automatic_sending_enabled"])
        self.assertFalse(lines[1]["transport_called"])


def _paths(root: Path) -> dict[str, Path]:
    return {
        "config": root / "private" / "notification_config.json",
        "state": root / "private" / "delivery_state.json",
        "python": root / "venv" / "bin" / "python",
        "runner": root / "project" / "family_calendar_delivery_run.py",
        "planner": (
            root
            / "Library"
            / "LaunchAgents"
            / f"{FAMILY_CALENDAR_PLANNER_LABEL}.plist"
        ),
        "launchctl": root / "bin" / "launchctl",
        "security": root / "bin" / "security",
    }


def _prepare_inputs(paths: dict[str, Path]) -> None:
    _write_config(paths["config"])
    _write_executable(paths["python"])
    _write_runner(paths["runner"])
    _write_planner(paths["planner"], paths["python"], paths["runner"])
    _write_executable(paths["launchctl"])
    _write_executable(paths["security"])


def _write_config(path: Path) -> None:
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    path.parent.chmod(0o700)
    path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "mode": "dry_run",
                "smtp_provider": "icloud",
                "sender_address": PRIVATE_ADDRESS,
                "recipients": [
                    {
                        "recipient_id": f"recipient-{index}",
                        "address": f"{index}@example.invalid",
                    }
                    for index in range(1, 5)
                ],
            }
        ),
        encoding="utf-8",
    )
    path.chmod(0o600)


def _write_blocking_state(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "records": {
                    f"{PRIVATE_EVENT_KEY}:D-2": {
                        "event_key": PRIVATE_EVENT_KEY,
                        "offset": "D-2",
                        "operation_id": f"{PRIVATE_EVENT_KEY}:D-2",
                        "state": "delivery_unknown",
                        "recipients": [
                            {
                                "recipient_id": f"recipient-{index}",
                                "state": "unknown",
                            }
                            for index in range(1, 5)
                        ],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    path.chmod(0o600)


def _write_executable(path: Path) -> None:
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    path.parent.chmod(0o700)
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o700)


def _write_runner(path: Path) -> None:
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    path.write_text("# safe runner\n", encoding="utf-8")
    path.chmod(0o600)


def _write_planner(
    path: Path,
    python_path: Path,
    runner_path: Path,
) -> None:
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    path.parent.chmod(0o700)
    path.write_bytes(
        plistlib.dumps(
            {
                "Label": FAMILY_CALENDAR_PLANNER_LABEL,
                "ProgramArguments": [str(python_path), str(runner_path)],
                "StartCalendarInterval": {"Hour": 8, "Minute": 0},
                "RunAtLoad": False,
                "ProcessType": "Background",
            }
        )
    )
    path.chmod(0o600)


def _snapshot(paths: dict[str, Path]) -> dict[str, bytes | None]:
    return {
        name: path.read_bytes() if path.is_file() else None
        for name, path in paths.items()
    }


def _plan(
    paths: dict[str, Path],
    system: _FakeSystem,
):
    return plan_family_calendar_automation_activation(
        config_path=paths["config"],
        state_path=paths["state"],
        planner_path=paths["planner"],
        planner_runner_path=paths["runner"],
        command_runner=system.run,
        executable_locator=system.locate,
    )


def _confirmations(plan) -> dict[str, str]:
    return {
        "global_confirmation": GLOBAL_SAFETY_BRAKE_CONFIRMATION,
        "confirmation": FAMILY_CALENDAR_AUTOMATION_CONFIRMATION,
        "expected_fingerprint": plan.fingerprint,
    }


def _cli_paths(paths: dict[str, Path]) -> list[str]:
    return [
        "--config-path",
        str(paths["config"]),
        "--state-path",
        str(paths["state"]),
        "--planner-path",
        str(paths["planner"]),
        "--planner-runner-path",
        str(paths["runner"]),
    ]
