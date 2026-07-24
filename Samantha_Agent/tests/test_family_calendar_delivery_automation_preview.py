from __future__ import annotations

import io
import json
import os
import plistlib
import tempfile
import unittest
from pathlib import Path

from app.family_calendar_delivery_automation_preview import (
    FAMILY_CALENDAR_AUTOMATION_CONFIRMATION,
    build_family_calendar_automation_preview,
)
from app.family_calendar_delivery_readiness import (
    FAMILY_CALENDAR_KEYCHAIN_SERVICE,
    FAMILY_CALENDAR_PLANNER_LABEL,
)
from scripts.family_calendar_delivery_automation_preview import (
    build_parser,
    main,
)


PRIVATE_ADDRESS = "private-sender@example.invalid"
PRIVATE_EVENT_KEY = "private-person:birthday:2026-12-19"


class FamilyCalendarAutomationPreviewTests(unittest.TestCase):
    def test_valid_preview_is_exact_redacted_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _preview_paths(Path(temp_dir))
            _prepare_inputs(paths)
            before = _snapshot(paths)
            calls: list[tuple[str, ...]] = []

            def run_status(argv) -> int:
                call = tuple(argv)
                calls.append(call)
                return 0

            result = build_family_calendar_automation_preview(
                config_path=paths["config"],
                state_path=paths["state"],
                planner_path=paths["planner"],
                planner_runner_path=paths["runner"],
                command_runner=run_status,
                executable_locator=lambda name: str(paths[name]),
            )
            document = result.safe_document()
            rendered = json.dumps(document, ensure_ascii=False)
            after = _snapshot(paths)

        self.assertEqual(result.status, "preview")
        self.assertEqual(result.issues, ())
        self.assertEqual(before, after)
        self.assertEqual(document["current_configuration"]["mode"], "dry_run")
        self.assertEqual(document["target_configuration"]["mode"], "enabled")
        self.assertEqual(
            document["target_configuration"]["only_changed_field"],
            "mode",
        )
        self.assertEqual(document["current_configuration"]["recipient_count"], 4)
        self.assertEqual(len(document["plan_fingerprint"]), 64)
        self.assertTrue(document["operational_prerequisites_ready"])
        self.assertEqual(
            document["implementation_blockers"],
            ["automatic_mode_unavailable"],
        )
        self.assertNotIn(
            "automatic_mode",
            {check["name"] for check in document["prerequisite_checks"]},
        )
        self.assertFalse(document["target_mode_supported_by_runtime"])
        self.assertFalse(document["activation_implementation_available"])
        self.assertFalse(document["apply_available"])
        self.assertFalse(document["automatic_sending_enabled"])
        self.assertEqual(
            document["required_confirmation"],
            FAMILY_CALENDAR_AUTOMATION_CONFIRMATION,
        )
        actions = [
            item["action"] for item in document["operation"]["sequence"]
        ]
        self.assertEqual(
            actions,
            [
                "revalidate_plan_fingerprint_and_prerequisites",
                "unload_planner",
                "verify_planner_unloaded",
                "atomic_replace_configuration_mode",
                "verify_enabled_configuration",
                "load_planner",
                "verify_planner_loaded_and_ready",
            ],
        )
        self.assertTrue(
            document["idempotency_contract"]["persist_sending_before_transport"]
        )
        self.assertTrue(
            document["delivery_contract"][
                "transport_requires_persisted_sending_state"
            ]
        )
        self.assertTrue(
            document["recovery_contract"]["delivery_unknown_blocks_activation"]
        )
        rollback_actions = [
            item["action"]
            for item in document["operation"]["rollback"]["sequence"]
        ]
        self.assertEqual(
            rollback_actions[:2],
            ["ensure_planner_unloaded", "verify_planner_unloaded"],
        )
        self.assertEqual(
            document["operation"]["rollback"]["fail_closed_state"],
            "planner_unloaded_with_configuration_requiring_manual_audit",
        )
        self.assertFalse(document["writes_performed"])
        self.assertFalse(document["launchctl_mutation_called"])
        self.assertFalse(document["secret_read"])
        self.assertFalse(document["transport_called"])
        self.assertFalse(paths["state"].exists())
        self.assertEqual(len(calls), 2)
        self.assertTrue(any(call[1] == "print" for call in calls))
        keychain_call = next(
            call for call in calls if "find-generic-password" in call
        )
        self.assertIn(FAMILY_CALENDAR_KEYCHAIN_SERVICE, keychain_call)
        self.assertNotIn("-w", keychain_call)
        self.assertNotIn("-g", keychain_call)
        self.assertNotIn(PRIVATE_ADDRESS, rendered)
        self.assertNotIn(PRIVATE_EVENT_KEY, rendered)

    def test_blocking_delivery_state_suppresses_operation_and_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _preview_paths(Path(temp_dir))
            _prepare_inputs(paths)
            _write_state(paths["state"])
            before = _snapshot(paths)

            result = build_family_calendar_automation_preview(
                config_path=paths["config"],
                state_path=paths["state"],
                planner_path=paths["planner"],
                planner_runner_path=paths["runner"],
                command_runner=lambda _argv: 0,
                executable_locator=lambda name: str(paths[name]),
            )
            document = result.safe_document()
            after = _snapshot(paths)

        self.assertEqual(result.status, "blocked")
        self.assertIn("delivery_unknown_present", result.issues)
        self.assertIsNone(document["operation"])
        self.assertIsNone(document["plan_fingerprint"])
        self.assertFalse(document["operational_prerequisites_ready"])
        self.assertEqual(before, after)
        self.assertNotIn(PRIVATE_EVENT_KEY, json.dumps(document))

    def test_invalid_or_changed_inputs_fail_closed(self) -> None:
        cases = ("disabled", "planner_unloaded", "missing_keychain")
        for case in cases:
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    paths = _preview_paths(Path(temp_dir))
                    _prepare_inputs(
                        paths,
                        mode="disabled" if case == "disabled" else "dry_run",
                    )

                    def run_status(argv) -> int:
                        if "find-generic-password" in argv:
                            return 44 if case == "missing_keychain" else 0
                        return 113 if case == "planner_unloaded" else 0

                    result = build_family_calendar_automation_preview(
                        config_path=paths["config"],
                        state_path=paths["state"],
                        planner_path=paths["planner"],
                        planner_runner_path=paths["runner"],
                        command_runner=run_status,
                        executable_locator=lambda name: str(paths[name]),
                    )

                self.assertEqual(result.status, "blocked")
                self.assertTrue(result.issues)
                self.assertIsNone(result.operation_document())
                self.assertIsNone(result.plan_fingerprint)
                self.assertEqual(
                    result.safe_document()["current_configuration"]["mode"],
                    "disabled" if case == "disabled" else "dry_run",
                )

    def test_fingerprint_changes_with_config_or_planner(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _preview_paths(Path(temp_dir))
            _prepare_inputs(paths)
            kwargs = {
                "config_path": paths["config"],
                "state_path": paths["state"],
                "planner_path": paths["planner"],
                "planner_runner_path": paths["runner"],
                "command_runner": lambda _argv: 0,
                "executable_locator": lambda name: str(paths[name]),
            }
            first = build_family_calendar_automation_preview(**kwargs)
            _write_config(
                paths["config"],
                sender="changed@example.invalid",
            )
            second = build_family_calendar_automation_preview(**kwargs)
            _write_config(paths["config"])
            _write_planner(
                paths["planner"],
                paths["python"],
                paths["runner"],
                minute=1,
            )
            third = build_family_calendar_automation_preview(**kwargs)

        self.assertNotEqual(first.plan_fingerprint, second.plan_fingerprint)
        self.assertNotEqual(first.plan_fingerprint, third.plan_fingerprint)
        self.assertNotIn(PRIVATE_ADDRESS, repr(first))

    def test_cli_has_no_apply_path_and_uses_preview_exit_status(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _preview_paths(Path(temp_dir))
            _prepare_inputs(paths)
            output = io.StringIO()

            exit_code = main(
                [
                    "--config-path",
                    str(paths["config"]),
                    "--state-path",
                    str(paths["state"]),
                    "--planner-path",
                    str(paths["planner"]),
                    "--planner-runner-path",
                    str(paths["runner"]),
                ],
                command_runner=lambda _argv: 0,
                executable_locator=lambda name: str(paths[name]),
                output=output,
            )
            document = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(document["status"], "preview")
        self.assertFalse(document["apply_available"])
        self.assertFalse(document["writes_performed"])
        self.assertFalse(document["transport_called"])
        self.assertNotIn(PRIVATE_ADDRESS, output.getvalue())
        self.assertNotIn("--apply", build_parser().format_help())
        self.assertNotIn("--confirmation", build_parser().format_help())


def _preview_paths(root: Path) -> dict[str, Path]:
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


def _prepare_inputs(paths: dict[str, Path], *, mode: str = "dry_run") -> None:
    _write_config(paths["config"], mode=mode)
    _write_executable(paths["python"])
    _write_runner(paths["runner"])
    _write_planner(paths["planner"], paths["python"], paths["runner"])
    _write_executable(paths["launchctl"])
    _write_executable(paths["security"])


def _write_config(
    path: Path,
    *,
    mode: str = "dry_run",
    sender: str = PRIVATE_ADDRESS,
) -> None:
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    path.parent.chmod(0o700)
    path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "mode": mode,
                "smtp_provider": "icloud",
                "sender_address": sender,
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


def _write_state(path: Path) -> None:
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
    *,
    minute: int = 0,
) -> None:
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    path.parent.chmod(0o700)
    path.write_bytes(
        plistlib.dumps(
            {
                "Label": FAMILY_CALENDAR_PLANNER_LABEL,
                "ProgramArguments": [
                    str(python_path),
                    str(runner_path),
                ],
                "StartCalendarInterval": {"Hour": 8, "Minute": minute},
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
        if name not in {"state"}
    } | {
        "state": paths["state"].read_bytes()
        if paths["state"].is_file()
        else None
    }
