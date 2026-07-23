from __future__ import annotations

import io
import json
import os
import plistlib
import tempfile
import unittest
from pathlib import Path

from app.family_calendar_delivery_launchctl_preview import (
    build_family_calendar_launchctl_preview,
)
from app.family_calendar_delivery_readiness import FAMILY_CALENDAR_PLANNER_LABEL
from scripts.family_calendar_delivery_launchctl_preview import (
    build_parser,
    main,
)


PRIVATE_ADDRESS = "private-sender@example.invalid"


class FamilyCalendarLaunchctlPreviewTests(unittest.TestCase):
    def test_valid_preview_has_exact_commands_without_execution_or_writes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _preview_paths(Path(temp_dir))
            _prepare_inputs(paths)
            before = _snapshot(paths)
            locator_calls: list[str] = []

            def locate(name: str) -> str:
                locator_calls.append(name)
                return str(paths["launchctl"])

            result = build_family_calendar_launchctl_preview(
                config_path=paths["config"],
                planner_path=paths["planner"],
                planner_runner_path=paths["runner"],
                executable_locator=locate,
            )

            document = result.safe_document()
            operation = document["operation"]
            uid = os.getuid()
            domain = f"gui/{uid}"
            service = f"{domain}/{FAMILY_CALENDAR_PLANNER_LABEL}"
            after = _snapshot(paths)

        self.assertEqual(result.status, "preview")
        self.assertEqual(result.issues, ())
        self.assertEqual(locator_calls, ["launchctl"])
        self.assertEqual(
            operation["bootstrap"],
            [str(paths["launchctl"]), "bootstrap", domain, str(paths["planner"])],
        )
        self.assertEqual(
            operation["verify_loaded"],
            [str(paths["launchctl"]), "print", service],
        )
        self.assertEqual(
            operation["rollback"],
            [str(paths["launchctl"]), "bootout", service],
        )
        self.assertEqual(
            operation["verify_unloaded"],
            [str(paths["launchctl"]), "print", service],
        )
        self.assertEqual(before, after)
        self.assertEqual(len(document["plan_fingerprint"]), 64)
        self.assertFalse(document["current_load_state_probed"])
        self.assertFalse(document["apply_available"])
        self.assertTrue(document["separate_confirmation_required_for_load"])
        self.assertFalse(document["writes_performed"])
        self.assertFalse(document["launchctl_called"])
        self.assertFalse(document["secret_read"])
        self.assertFalse(document["transport_called"])
        self.assertNotIn(PRIVATE_ADDRESS, json.dumps(document))

    def test_invalid_inputs_fail_closed_without_commands_or_fingerprint(self) -> None:
        cases = (
            "non_dry_run",
            "run_at_load",
            "wrong_process_type",
            "unsafe_mode",
            "linked_planner",
            "missing_launchctl",
        )
        for case in cases:
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    paths = _preview_paths(Path(temp_dir))
                    _prepare_inputs(
                        paths,
                        mode="disabled" if case == "non_dry_run" else "dry_run",
                        run_at_load=case == "run_at_load",
                        process_type=(
                            "Interactive"
                            if case == "wrong_process_type"
                            else "Background"
                        ),
                    )
                    if case == "unsafe_mode":
                        paths["planner"].chmod(0o644)
                    elif case == "linked_planner":
                        source = Path(temp_dir) / "source.plist"
                        paths["planner"].replace(source)
                        paths["planner"].symlink_to(source)
                    locator = (
                        (lambda _name: None)
                        if case == "missing_launchctl"
                        else (lambda _name: str(paths["launchctl"]))
                    )
                    before = _snapshot(paths)

                    result = build_family_calendar_launchctl_preview(
                        config_path=paths["config"],
                        planner_path=paths["planner"],
                        planner_runner_path=paths["runner"],
                        executable_locator=locator,
                    )
                    document = result.safe_document()

                    self.assertEqual(result.status, "invalid")
                    self.assertTrue(result.issues)
                    self.assertIsNone(document["operation"])
                    self.assertIsNone(document["plan_fingerprint"])
                    self.assertFalse(document["launchctl_called"])
                    self.assertFalse(document["writes_performed"])
                    self.assertEqual(before, _snapshot(paths))
                    self.assertNotIn(PRIVATE_ADDRESS, json.dumps(document))

    def test_fingerprint_changes_with_plist_or_private_config(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _preview_paths(Path(temp_dir))
            _prepare_inputs(paths)
            kwargs = {
                "config_path": paths["config"],
                "planner_path": paths["planner"],
                "planner_runner_path": paths["runner"],
                "executable_locator": lambda _name: str(paths["launchctl"]),
            }

            first = build_family_calendar_launchctl_preview(**kwargs)
            _write_config(paths["config"], sender="changed@example.invalid")
            second = build_family_calendar_launchctl_preview(**kwargs)
            _write_config(paths["config"])
            _write_planner(paths["planner"], paths["python"], paths["runner"], minute=1)
            third = build_family_calendar_launchctl_preview(**kwargs)

        self.assertNotEqual(first.fingerprint, second.fingerprint)
        self.assertNotEqual(first.fingerprint, third.fingerprint)
        self.assertNotIn(PRIVATE_ADDRESS, repr(first))

    def test_cli_is_preview_only_and_emits_redacted_json(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _preview_paths(Path(temp_dir))
            _prepare_inputs(paths)
            output = io.StringIO()

            exit_code = main(
                [
                    "--config-path",
                    str(paths["config"]),
                    "--planner-path",
                    str(paths["planner"]),
                    "--planner-runner-path",
                    str(paths["runner"]),
                ],
                executable_locator=lambda _name: str(paths["launchctl"]),
                output=output,
            )
            document = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(document["status"], "preview")
        self.assertFalse(document["apply_available"])
        self.assertFalse(document["launchctl_called"])
        self.assertFalse(document["writes_performed"])
        self.assertNotIn(PRIVATE_ADDRESS, output.getvalue())
        self.assertNotIn("--apply", build_parser().format_help())


def _preview_paths(root: Path) -> dict[str, Path]:
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


def _prepare_inputs(
    paths: dict[str, Path],
    *,
    mode: str = "dry_run",
    run_at_load: bool = False,
    process_type: str = "Background",
) -> None:
    _write_config(paths["config"], mode=mode)
    _write_executable(paths["python"])
    _write_runner(paths["runner"])
    _write_planner(
        paths["planner"],
        paths["python"],
        paths["runner"],
        run_at_load=run_at_load,
        process_type=process_type,
    )
    _write_executable(paths["launchctl"])


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
    run_at_load: bool = False,
    process_type: str = "Background",
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
                "RunAtLoad": run_at_load,
                "ProcessType": process_type,
            },
            sort_keys=True,
        )
    )
    path.chmod(0o600)


def _snapshot(paths: dict[str, Path]) -> dict[str, tuple[bool, bool, bytes | None]]:
    result: dict[str, tuple[bool, bool, bytes | None]] = {}
    for name, path in paths.items():
        result[name] = (
            path.exists(),
            path.is_symlink(),
            path.read_bytes() if path.is_file() and not path.is_symlink() else None,
        )
    return result
