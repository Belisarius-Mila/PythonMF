from __future__ import annotations

import io
import json
import os
import plistlib
import tempfile
import unittest
from pathlib import Path

from app.family_calendar_delivery_launchctl_load import (
    FAMILY_CALENDAR_LAUNCHCTL_LOAD_CONFIRMATION,
    GLOBAL_SAFETY_BRAKE_CONFIRMATION,
    LAUNCHCTL_SERVICE_NOT_FOUND_EXIT,
    FamilyCalendarLaunchctlLoadError,
    apply_family_calendar_launchctl_load,
    plan_family_calendar_launchctl_load,
)
from app.family_calendar_delivery_readiness import FAMILY_CALENDAR_PLANNER_LABEL
from scripts.family_calendar_delivery_launchctl_load import main


PRIVATE_ADDRESS = "private-sender@example.invalid"


class FakeLaunchctl:
    def __init__(
        self,
        *,
        loaded: bool = False,
        bootstrap_status: int = 0,
        bootout_status: int = 0,
        print_results: list[int] | None = None,
    ) -> None:
        self.loaded = loaded
        self.bootstrap_status = bootstrap_status
        self.bootout_status = bootout_status
        self.print_results = list(print_results or [])
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, argv) -> int:
        command = tuple(str(value) for value in argv)
        self.calls.append(command)
        action = command[1]
        if action == "print":
            if self.print_results:
                return self.print_results.pop(0)
            return 0 if self.loaded else LAUNCHCTL_SERVICE_NOT_FOUND_EXIT
        if action == "bootstrap":
            if self.bootstrap_status == 0:
                self.loaded = True
            return self.bootstrap_status
        if action == "bootout":
            if self.bootout_status == 0:
                self.loaded = False
            return self.bootout_status
        raise AssertionError(f"unexpected launchctl action: {action}")


class FamilyCalendarLaunchctlLoadTests(unittest.TestCase):
    def test_preview_probes_only_exact_unloaded_service(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _load_paths(Path(temp_dir))
            _prepare_inputs(paths)
            launchctl = FakeLaunchctl()
            before = _snapshot(paths)

            plan = plan_family_calendar_launchctl_load(
                **_plan_kwargs(paths, launchctl)
            )
            document = plan.safe_document()
            after = _snapshot(paths)

        self.assertEqual(before, after)
        self.assertEqual(len(launchctl.calls), 1)
        self.assertEqual(launchctl.calls[0], plan.print_command())
        self.assertEqual(document["runtime_state"], "unloaded")
        self.assertEqual(
            document["required_global_confirmation"],
            GLOBAL_SAFETY_BRAKE_CONFIRMATION,
        )
        self.assertEqual(
            document["required_confirmation"],
            FAMILY_CALENDAR_LAUNCHCTL_LOAD_CONFIRMATION,
        )
        self.assertFalse(document["writes_performed"])
        self.assertTrue(document["launchctl_probe_called"])
        self.assertFalse(document["launchctl_mutation_called"])
        self.assertFalse(document["bootstrap_called"])
        self.assertFalse(document["rollback_called"])
        self.assertFalse(document["secret_read"])
        self.assertFalse(document["transport_called"])
        self.assertNotIn(PRIVATE_ADDRESS, json.dumps(document))

    def test_preview_rejects_loaded_or_unknown_state(self) -> None:
        for status, expected_state in ((0, "loaded"), (5, "unknown")):
            with self.subTest(status=status):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    paths = _load_paths(Path(temp_dir))
                    _prepare_inputs(paths)
                    launchctl = FakeLaunchctl(print_results=[status])

                    with self.assertRaises(FamilyCalendarLaunchctlLoadError) as raised:
                        plan_family_calendar_launchctl_load(
                            **_plan_kwargs(paths, launchctl)
                        )

                self.assertEqual(raised.exception.stage, "state_probe")
                self.assertEqual(raised.exception.runtime_state, expected_state)
                self.assertFalse(raised.exception.mutation_attempted)

    def test_confirmations_and_fingerprint_block_before_mutation(self) -> None:
        cases = (
            ("global_confirmation", "no", FAMILY_CALENDAR_LAUNCHCTL_LOAD_CONFIRMATION, None),
            ("confirmation", GLOBAL_SAFETY_BRAKE_CONFIRMATION, "no", None),
            (
                "fingerprint",
                GLOBAL_SAFETY_BRAKE_CONFIRMATION,
                FAMILY_CALENDAR_LAUNCHCTL_LOAD_CONFIRMATION,
                "0" * 64,
            ),
        )
        for stage, global_confirmation, confirmation, fingerprint in cases:
            with self.subTest(stage=stage):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    paths = _load_paths(Path(temp_dir))
                    _prepare_inputs(paths)
                    launchctl = FakeLaunchctl()
                    plan = plan_family_calendar_launchctl_load(
                        **_plan_kwargs(paths, launchctl)
                    )

                    with self.assertRaises(FamilyCalendarLaunchctlLoadError) as raised:
                        apply_family_calendar_launchctl_load(
                            plan,
                            global_confirmation=global_confirmation,
                            confirmation=confirmation,
                            expected_fingerprint=fingerprint or plan.fingerprint,
                            command_runner=launchctl,
                            executable_locator=lambda _name: str(paths["launchctl"]),
                        )

                self.assertEqual(raised.exception.stage, stage)
                self.assertFalse(raised.exception.mutation_attempted)
                self.assertFalse(
                    any(call[1] in {"bootstrap", "bootout"} for call in launchctl.calls)
                )

    def test_success_rechecks_then_bootstraps_and_verifies_loaded(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _load_paths(Path(temp_dir))
            _prepare_inputs(paths)
            launchctl = FakeLaunchctl()
            plan = plan_family_calendar_launchctl_load(
                **_plan_kwargs(paths, launchctl)
            )

            result = apply_family_calendar_launchctl_load(
                plan,
                **_apply_kwargs(paths, launchctl, plan.fingerprint),
            )
            document = result.safe_document()

        self.assertEqual(
            [call[1] for call in launchctl.calls],
            ["print", "print", "bootstrap", "print"],
        )
        self.assertEqual(document["status"], "loaded")
        self.assertEqual(document["runtime_state"], "loaded")
        self.assertTrue(document["planner_loaded"])
        self.assertFalse(document["automatic_sending_enabled"])
        self.assertEqual(document["bootstrap_exit_status"], "zero")
        self.assertTrue(document["writes_performed"])
        self.assertTrue(document["launchctl_mutation_called"])
        self.assertFalse(document["rollback_attempted"])
        self.assertFalse(document["secret_read"])
        self.assertFalse(document["transport_called"])

    def test_changed_inputs_block_during_recheck_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _load_paths(Path(temp_dir))
            _prepare_inputs(paths)
            launchctl = FakeLaunchctl()
            plan = plan_family_calendar_launchctl_load(
                **_plan_kwargs(paths, launchctl)
            )
            _write_config(paths["config"], sender="changed@example.invalid")

            with self.assertRaises(FamilyCalendarLaunchctlLoadError) as raised:
                apply_family_calendar_launchctl_load(
                    plan,
                    **_apply_kwargs(paths, launchctl, plan.fingerprint),
                )

        self.assertEqual(raised.exception.stage, "plan_recheck")
        self.assertFalse(raised.exception.mutation_attempted)
        self.assertFalse(
            any(call[1] in {"bootstrap", "bootout"} for call in launchctl.calls)
        )

    def test_failed_bootstrap_with_confirmed_unloaded_state_never_rolls_back(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _load_paths(Path(temp_dir))
            _prepare_inputs(paths)
            launchctl = FakeLaunchctl(bootstrap_status=5)
            plan = plan_family_calendar_launchctl_load(
                **_plan_kwargs(paths, launchctl)
            )

            with self.assertRaises(FamilyCalendarLaunchctlLoadError) as raised:
                apply_family_calendar_launchctl_load(
                    plan,
                    **_apply_kwargs(paths, launchctl, plan.fingerprint),
                )

        self.assertEqual(raised.exception.stage, "bootstrap")
        self.assertTrue(raised.exception.mutation_attempted)
        self.assertEqual(raised.exception.runtime_state, "unloaded")
        self.assertFalse(raised.exception.rollback_attempted)
        self.assertEqual(raised.exception.bootstrap_exit_status, "nonzero")
        self.assertNotIn("bootout", [call[1] for call in launchctl.calls])

    def test_unknown_verification_runs_and_confirms_rollback(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _load_paths(Path(temp_dir))
            _prepare_inputs(paths)
            launchctl = FakeLaunchctl(
                print_results=[
                    LAUNCHCTL_SERVICE_NOT_FOUND_EXIT,
                    LAUNCHCTL_SERVICE_NOT_FOUND_EXIT,
                    5,
                    LAUNCHCTL_SERVICE_NOT_FOUND_EXIT,
                ]
            )
            plan = plan_family_calendar_launchctl_load(
                **_plan_kwargs(paths, launchctl)
            )

            with self.assertRaises(FamilyCalendarLaunchctlLoadError) as raised:
                apply_family_calendar_launchctl_load(
                    plan,
                    **_apply_kwargs(paths, launchctl, plan.fingerprint),
                )

        self.assertEqual(raised.exception.stage, "verification")
        self.assertTrue(raised.exception.mutation_attempted)
        self.assertEqual(raised.exception.runtime_state, "unloaded")
        self.assertTrue(raised.exception.rollback_attempted)
        self.assertTrue(raised.exception.rollback_confirmed)
        self.assertEqual(
            [call[1] for call in launchctl.calls],
            ["print", "print", "bootstrap", "print", "bootout", "print"],
        )

    def test_unconfirmed_rollback_reports_loaded_state_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _load_paths(Path(temp_dir))
            _prepare_inputs(paths)
            launchctl = FakeLaunchctl(
                bootout_status=5,
                print_results=[
                    LAUNCHCTL_SERVICE_NOT_FOUND_EXIT,
                    LAUNCHCTL_SERVICE_NOT_FOUND_EXIT,
                    5,
                    0,
                ],
            )
            plan = plan_family_calendar_launchctl_load(
                **_plan_kwargs(paths, launchctl)
            )

            with self.assertRaises(FamilyCalendarLaunchctlLoadError) as raised:
                apply_family_calendar_launchctl_load(
                    plan,
                    **_apply_kwargs(paths, launchctl, plan.fingerprint),
                )

        self.assertEqual(raised.exception.stage, "rollback")
        self.assertEqual(raised.exception.runtime_state, "loaded")
        self.assertTrue(raised.exception.rollback_attempted)
        self.assertFalse(raised.exception.rollback_confirmed)
        self.assertFalse(raised.exception.safe_document()["retry_safe"])

    def test_cli_previews_and_applies_only_with_both_confirmations(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _load_paths(Path(temp_dir))
            _prepare_inputs(paths)
            preview_runner = FakeLaunchctl()
            preview_output = io.StringIO()
            arguments = _cli_arguments(paths)

            preview_exit = main(
                arguments,
                command_runner=preview_runner,
                executable_locator=lambda _name: str(paths["launchctl"]),
                output=preview_output,
            )
            preview = json.loads(preview_output.getvalue())

            apply_runner = FakeLaunchctl()
            apply_output = io.StringIO()
            apply_exit = main(
                [
                    *arguments,
                    "--apply",
                    "--global-confirmation",
                    GLOBAL_SAFETY_BRAKE_CONFIRMATION,
                    "--confirmation",
                    FAMILY_CALENDAR_LAUNCHCTL_LOAD_CONFIRMATION,
                    "--expected-fingerprint",
                    preview["plan_fingerprint"],
                ],
                command_runner=apply_runner,
                executable_locator=lambda _name: str(paths["launchctl"]),
                output=apply_output,
            )
            documents = [
                json.loads(line) for line in apply_output.getvalue().splitlines()
            ]

        self.assertEqual(preview_exit, 0)
        self.assertEqual(preview["status"], "preview")
        self.assertEqual(apply_exit, 0)
        self.assertEqual([item["status"] for item in documents], ["preview", "loaded"])
        self.assertFalse(documents[-1]["automatic_sending_enabled"])
        self.assertNotIn(PRIVATE_ADDRESS, apply_output.getvalue())


def _load_paths(root: Path) -> dict[str, Path]:
    return {
        "config": root / "private" / "notification_config.json",
        "python": root / "venv" / "bin" / "python",
        "runner": root / "project" / "family_calendar_delivery_run.py",
        "planner": (
            root
            / "Library"
            / "LaunchAgents"
            / f"{FAMILY_CALENDAR_PLANNER_LABEL}.plist"
        ),
        "launchctl": root / "bin" / "launchctl",
    }


def _prepare_inputs(paths: dict[str, Path]) -> None:
    _write_config(paths["config"])
    _write_executable(paths["python"])
    _write_runner(paths["runner"])
    _write_planner(paths)
    _write_executable(paths["launchctl"])


def _write_config(
    path: Path,
    *,
    sender: str = PRIVATE_ADDRESS,
) -> None:
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    path.parent.chmod(0o700)
    path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "mode": "dry_run",
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


def _write_executable(path: Path) -> None:
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    path.parent.chmod(0o700)
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o700)


def _write_runner(path: Path) -> None:
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    path.write_text("# safe runner\n", encoding="utf-8")
    path.chmod(0o600)


def _write_planner(paths: dict[str, Path]) -> None:
    path = paths["planner"]
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    path.parent.chmod(0o700)
    path.write_bytes(
        plistlib.dumps(
            {
                "Label": FAMILY_CALENDAR_PLANNER_LABEL,
                "ProgramArguments": [
                    str(paths["python"]),
                    str(paths["runner"]),
                ],
                "StartCalendarInterval": {"Hour": 8, "Minute": 0},
                "RunAtLoad": False,
                "ProcessType": "Background",
            },
            sort_keys=True,
        )
    )
    path.chmod(0o600)


def _plan_kwargs(
    paths: dict[str, Path],
    launchctl: FakeLaunchctl,
) -> dict[str, object]:
    return {
        "config_path": paths["config"],
        "planner_path": paths["planner"],
        "planner_runner_path": paths["runner"],
        "command_runner": launchctl,
        "executable_locator": lambda _name: str(paths["launchctl"]),
    }


def _apply_kwargs(
    paths: dict[str, Path],
    launchctl: FakeLaunchctl,
    fingerprint: str,
) -> dict[str, object]:
    return {
        "global_confirmation": GLOBAL_SAFETY_BRAKE_CONFIRMATION,
        "confirmation": FAMILY_CALENDAR_LAUNCHCTL_LOAD_CONFIRMATION,
        "expected_fingerprint": fingerprint,
        "command_runner": launchctl,
        "executable_locator": lambda _name: str(paths["launchctl"]),
    }


def _cli_arguments(paths: dict[str, Path]) -> list[str]:
    return [
        "--config-path",
        str(paths["config"]),
        "--planner-path",
        str(paths["planner"]),
        "--planner-runner-path",
        str(paths["runner"]),
    ]


def _snapshot(paths: dict[str, Path]) -> dict[str, bytes]:
    return {
        name: path.read_bytes()
        for name, path in paths.items()
        if path.is_file() and not path.is_symlink()
    }
