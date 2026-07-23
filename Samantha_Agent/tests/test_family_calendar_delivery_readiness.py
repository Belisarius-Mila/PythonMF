from __future__ import annotations

import io
import json
import plistlib
import sys
import tempfile
import unittest
from pathlib import Path

from app.family_calendar_delivery_readiness import (
    FAMILY_CALENDAR_KEYCHAIN_SERVICE,
    FAMILY_CALENDAR_PLANNER_LABEL,
    FamilyCalendarDeliveryReadinessResult,
    ReadinessCheck,
    inspect_family_calendar_delivery_readiness,
)
from scripts.family_calendar_delivery_readiness import main


PRIVATE_ADDRESS = "private-sender@example.invalid"
PRIVATE_EVENT_KEY = "person-private:birthday:2026-12-19"
RECIPIENT_IDS = ("recipient-1", "recipient-2", "recipient-3", "recipient-4")


class FamilyCalendarDeliveryReadinessTests(unittest.TestCase):
    def test_ready_prerequisites_are_redacted_and_do_not_create_state(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _readiness_paths(Path(temp_dir))
            _write_config(paths["config"])
            _write_planner(paths["planner"], paths["runner"])
            before_config = paths["config"].read_bytes()
            before_planner = paths["planner"].read_bytes()
            calls: list[tuple[str, ...]] = []

            def run_status(argv):
                calls.append(tuple(argv))
                return 0

            result = inspect_family_calendar_delivery_readiness(
                config_path=paths["config"],
                state_path=paths["state"],
                planner_path=paths["planner"],
                planner_runner_path=paths["runner"],
                command_runner=run_status,
                executable_locator=_find_test_executable,
                automatic_mode_probe=lambda: True,
            )

            document = result.safe_document()
            rendered = f"{result!r} {json.dumps(document)}"
            self.assertEqual(result.status, "ready_to_enable")
            self.assertTrue(result.ready_to_enable)
            self.assertFalse(result.automation_active)
            self.assertEqual(result.config_mode, "dry_run")
            self.assertEqual(result.recipient_count, 4)
            self.assertEqual(result.record_count, 0)
            self.assertFalse(result.writes_performed)
            self.assertFalse(result.secret_read)
            self.assertFalse(result.transport_called)
            self.assertFalse(paths["state"].exists())
            self.assertEqual(paths["config"].read_bytes(), before_config)
            self.assertEqual(paths["planner"].read_bytes(), before_planner)
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

    def test_current_runtime_without_enabled_mode_is_a_blocker(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _readiness_paths(Path(temp_dir))
            _write_config(paths["config"])
            _write_planner(paths["planner"], paths["runner"])

            result = inspect_family_calendar_delivery_readiness(
                config_path=paths["config"],
                state_path=paths["state"],
                planner_path=paths["planner"],
                planner_runner_path=paths["runner"],
                command_runner=lambda _argv: 0,
                executable_locator=_find_test_executable,
            )

        self.assertEqual(result.status, "not_ready")
        self.assertFalse(result.ready_to_enable)
        self.assertEqual(
            _check(result, "automatic_mode").code,
            "automatic_mode_unavailable",
        )

    def test_missing_planner_and_keychain_are_separate_blockers(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _readiness_paths(Path(temp_dir))
            _write_config(paths["config"])

            def run_status(argv):
                if "find-generic-password" in argv:
                    return 44
                return 1

            result = inspect_family_calendar_delivery_readiness(
                config_path=paths["config"],
                state_path=paths["state"],
                planner_path=paths["planner"],
                planner_runner_path=paths["runner"],
                command_runner=run_status,
                executable_locator=_find_test_executable,
                automatic_mode_probe=lambda: True,
            )

        self.assertEqual(_check(result, "planner").code, "planner_not_installed")
        self.assertEqual(
            _check(result, "keychain").code,
            "credential_reference_missing",
        )
        self.assertFalse(result.ready_to_enable)

    def test_invalid_configuration_blocks_keychain_without_private_output(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _readiness_paths(Path(temp_dir))
            _write_private(paths["config"], f"{PRIVATE_ADDRESS} {{invalid")
            calls: list[tuple[str, ...]] = []

            result = inspect_family_calendar_delivery_readiness(
                config_path=paths["config"],
                state_path=paths["state"],
                planner_path=paths["planner"],
                planner_runner_path=paths["runner"],
                command_runner=lambda argv: calls.append(tuple(argv)) or 0,
                executable_locator=_find_test_executable,
                automatic_mode_probe=lambda: True,
            )

        rendered = json.dumps(result.safe_document())
        self.assertEqual(_check(result, "configuration").code, "configuration_invalid")
        self.assertEqual(
            _check(result, "keychain").code,
            "keychain_check_blocked_by_configuration",
        )
        self.assertFalse(any("find-generic-password" in call for call in calls))
        self.assertNotIn(PRIVATE_ADDRESS, rendered)

    def test_delivery_unknown_blocks_without_mutating_store(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _readiness_paths(Path(temp_dir))
            _write_config(paths["config"])
            _write_planner(paths["planner"], paths["runner"])
            _write_state(paths["state"], state="delivery_unknown", recipient_state="unknown")
            before = paths["state"].read_bytes()

            result = inspect_family_calendar_delivery_readiness(
                config_path=paths["config"],
                state_path=paths["state"],
                planner_path=paths["planner"],
                planner_runner_path=paths["runner"],
                command_runner=lambda _argv: 0,
                executable_locator=_find_test_executable,
                automatic_mode_probe=lambda: True,
            )

            after = paths["state"].read_bytes()

        self.assertEqual(result.delivery_unknown_count, 1)
        self.assertEqual(result.sending_count, 0)
        self.assertEqual(_check(result, "recovery").code, "delivery_unknown_present")
        self.assertFalse(result.ready_to_enable)
        self.assertEqual(after, before)
        self.assertNotIn(PRIVATE_EVENT_KEY, json.dumps(result.safe_document()))

    def test_sending_is_reported_but_never_recovered_by_audit(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _readiness_paths(Path(temp_dir))
            _write_config(paths["config"])
            _write_planner(paths["planner"], paths["runner"])
            _write_state(paths["state"], state="sending", recipient_state="pending")
            before = paths["state"].read_bytes()

            result = inspect_family_calendar_delivery_readiness(
                config_path=paths["config"],
                state_path=paths["state"],
                planner_path=paths["planner"],
                planner_runner_path=paths["runner"],
                command_runner=lambda _argv: 0,
                executable_locator=_find_test_executable,
                automatic_mode_probe=lambda: True,
            )

            after = paths["state"].read_bytes()

        self.assertEqual(result.sending_count, 1)
        self.assertEqual(
            _check(result, "recovery").code,
            "interrupted_delivery_present",
        )
        self.assertEqual(after, before)

    def test_corrupt_state_fails_closed_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _readiness_paths(Path(temp_dir))
            _write_config(paths["config"])
            _write_planner(paths["planner"], paths["runner"])
            _write_private(paths["state"], f"{PRIVATE_EVENT_KEY} {{invalid")
            before = paths["state"].read_bytes()

            result = inspect_family_calendar_delivery_readiness(
                config_path=paths["config"],
                state_path=paths["state"],
                planner_path=paths["planner"],
                planner_runner_path=paths["runner"],
                command_runner=lambda _argv: 0,
                executable_locator=_find_test_executable,
                automatic_mode_probe=lambda: True,
            )

            after = paths["state"].read_bytes()

        self.assertEqual(_check(result, "state_store").code, "state_store_invalid")
        self.assertFalse(result.ready_to_enable)
        self.assertEqual(after, before)
        self.assertNotIn(PRIVATE_EVENT_KEY, json.dumps(result.safe_document()))

    def test_cli_emits_only_safe_document_and_uses_readiness_exit_status(self) -> None:
        result = FamilyCalendarDeliveryReadinessResult(
            status="not_ready",
            ready_to_enable=False,
            automation_active=False,
            checks=(
                ReadinessCheck(
                    name="planner",
                    status="blocked",
                    code="planner_not_installed",
                    blocking=True,
                ),
            ),
            config_mode="dry_run",
            recipient_count=4,
            record_count=0,
            sending_count=0,
            delivery_unknown_count=0,
            partial_count=0,
        )
        output = io.StringIO()

        exit_code = main(
            [],
            output=output,
            readiness_runner=lambda **_kwargs: result,
        )

        document = json.loads(output.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertEqual(document, result.safe_document())
        self.assertTrue(document["redacted"])
        self.assertFalse(document["writes_performed"])
        self.assertFalse(document["secret_read"])
        self.assertFalse(document["transport_called"])


def _readiness_paths(root: Path) -> dict[str, Path]:
    private_dir = root / "family_calendar"
    private_dir.mkdir(mode=0o700)
    runner = root / "family_calendar_delivery_run.py"
    runner.write_text("# test runner\n", encoding="utf-8")
    planner = root / "family-calendar.plist"
    return {
        "config": private_dir / "notification_config.json",
        "state": private_dir / "delivery_state.json",
        "planner": planner,
        "runner": runner,
    }


def _write_config(path: Path) -> None:
    document = {
        "schema_version": 2,
        "mode": "dry_run",
        "smtp_provider": "icloud",
        "sender_address": PRIVATE_ADDRESS,
        "recipients": [
            {
                "recipient_id": recipient_id,
                "address": f"{index}@example.invalid",
            }
            for index, recipient_id in enumerate(RECIPIENT_IDS, start=1)
        ],
    }
    _write_private(path, json.dumps(document))


def _write_planner(path: Path, runner_path: Path) -> None:
    document = {
        "Label": FAMILY_CALENDAR_PLANNER_LABEL,
        "ProgramArguments": [sys.executable, str(runner_path.resolve())],
        "StartCalendarInterval": {"Hour": 8, "Minute": 0},
        "RunAtLoad": False,
    }
    path.write_bytes(plistlib.dumps(document))


def _write_state(path: Path, *, state: str, recipient_state: str) -> None:
    operation_id = f"{PRIVATE_EVENT_KEY}:D-2"
    document = {
        "schema_version": 1,
        "records": {
            operation_id: {
                "event_key": PRIVATE_EVENT_KEY,
                "offset": "D-2",
                "operation_id": operation_id,
                "state": state,
                "recipients": [
                    {"recipient_id": recipient_id, "state": recipient_state}
                    for recipient_id in RECIPIENT_IDS
                ],
            }
        },
    }
    _write_private(path, json.dumps(document))


def _write_private(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.parent.chmod(0o700)
    path.write_text(text, encoding="utf-8")
    path.chmod(0o600)


def _find_test_executable(name: str) -> str | None:
    return f"/test/{name}" if name in {"security", "launchctl"} else None


def _check(
    result: FamilyCalendarDeliveryReadinessResult,
    name: str,
) -> ReadinessCheck:
    return next(check for check in result.checks if check.name == name)


if __name__ == "__main__":
    unittest.main()
