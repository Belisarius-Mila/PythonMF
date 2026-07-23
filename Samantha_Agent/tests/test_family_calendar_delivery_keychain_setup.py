from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from app.family_calendar_delivery_keychain_setup import (
    FAMILY_CALENDAR_KEYCHAIN_LABEL,
    FAMILY_CALENDAR_KEYCHAIN_SETUP_CONFIRMATION,
    FamilyCalendarKeychainSetupError,
    apply_family_calendar_keychain_setup,
    plan_family_calendar_keychain_setup,
)
from app.family_calendar_delivery_readiness import (
    FAMILY_CALENDAR_KEYCHAIN_ACCOUNT,
    FAMILY_CALENDAR_KEYCHAIN_SERVICE,
)
from scripts.family_calendar_delivery_keychain_setup import main


PRIVATE_SENTINEL = "private-app-password-must-never-appear"


class FakeKeychain:
    def __init__(self, *, present: bool = False, write_status: int = 0) -> None:
        self.present = present
        self.write_status = write_status
        self.status_calls: list[tuple[str, ...]] = []
        self.write_calls: list[tuple[str, ...]] = []

    def status(self, argv) -> int:
        command = tuple(str(value) for value in argv)
        self.status_calls.append(command)
        if "find-generic-password" not in command:
            raise AssertionError("unexpected status command")
        return 0 if self.present else 44

    def write(self, argv) -> int:
        command = tuple(str(value) for value in argv)
        self.write_calls.append(command)
        if self.write_status == 0:
            self.present = True
        return self.write_status


class FamilyCalendarDeliveryKeychainSetupTests(unittest.TestCase):
    def test_preview_is_redacted_create_only_and_never_prompts_for_password(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            config_path = _write_config(root)
            security_path = _fake_security(root)
            keychain = FakeKeychain()
            output = io.StringIO()

            exit_code = main(
                ["--config-path", str(config_path)],
                confirmation_reader=_forbidden_reader,
                command_runner=keychain.status,
                credential_writer=_forbidden_writer,
                executable_locator=lambda _name: str(security_path),
                output=output,
            )
            document = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(document["status"], "preview")
        self.assertEqual(document["service"], FAMILY_CALENDAR_KEYCHAIN_SERVICE)
        self.assertEqual(document["account"], FAMILY_CALENDAR_KEYCHAIN_ACCOUNT)
        self.assertEqual(document["label"], FAMILY_CALENDAR_KEYCHAIN_LABEL)
        self.assertEqual(document["config_mode"], "dry_run")
        self.assertEqual(document["smtp_provider"], "icloud")
        self.assertTrue(document["create_only"])
        self.assertEqual(document["password_input"], "hidden_security_prompt")
        self.assertFalse(document["secret_passed_in_arguments"])
        self.assertFalse(document["writes_performed"])
        self.assertFalse(document["keychain_write_called"])
        self.assertEqual(keychain.write_calls, [])
        _assert_redacted(self, output.getvalue())

    def test_exact_confirmation_uses_security_hidden_prompt_without_secret_argv(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            config_path = _write_config(root)
            security_path = _fake_security(root)
            keychain = FakeKeychain()
            output = io.StringIO()

            exit_code = main(
                ["--apply", "--config-path", str(config_path)],
                confirmation_reader=lambda _prompt: (
                    FAMILY_CALENDAR_KEYCHAIN_SETUP_CONFIRMATION
                ),
                command_runner=keychain.status,
                credential_writer=keychain.write,
                executable_locator=lambda _name: str(security_path),
                output=output,
            )
            documents = [
                json.loads(line) for line in output.getvalue().splitlines()
            ]

        self.assertEqual(exit_code, 0)
        self.assertEqual([item["status"] for item in documents], ["preview", "created"])
        self.assertEqual(len(keychain.write_calls), 1)
        command = keychain.write_calls[0]
        self.assertEqual(command[-1], "-w")
        self.assertNotIn("-U", command)
        self.assertNotIn("-A", command)
        self.assertNotIn("-p", command)
        self.assertNotIn(PRIVATE_SENTINEL, command)
        self.assertEqual(command.count("-w"), 1)
        self.assertTrue(documents[-1]["credential_reference_present"])
        self.assertFalse(documents[-1]["secret_passed_in_arguments"])
        self.assertFalse(documents[-1]["secret_output"])
        _assert_redacted(self, output.getvalue())

    def test_wrong_confirmation_never_invokes_keychain_writer(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            config_path = _write_config(root)
            security_path = _fake_security(root)
            keychain = FakeKeychain()
            output = io.StringIO()

            exit_code = main(
                ["--apply", "--config-path", str(config_path)],
                confirmation_reader=lambda _prompt: "STORE",
                command_runner=keychain.status,
                credential_writer=keychain.write,
                executable_locator=lambda _name: str(security_path),
                output=output,
            )
            documents = [
                json.loads(line) for line in output.getvalue().splitlines()
            ]

        self.assertEqual(exit_code, 1)
        self.assertEqual(documents[-1]["failure_stage"], "confirmation")
        self.assertFalse(documents[-1]["write_attempted"])
        self.assertTrue(documents[-1]["retry_safe"])
        self.assertEqual(keychain.write_calls, [])
        _assert_redacted(self, output.getvalue())

    def test_configuration_change_after_preview_blocks_before_password_prompt(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            config_path = _write_config(root)
            security_path = _fake_security(root)
            keychain = FakeKeychain()
            output = io.StringIO()

            def change_config_then_confirm(_prompt: str) -> str:
                _write_config(root, fourth_address="changed@example.invalid")
                return FAMILY_CALENDAR_KEYCHAIN_SETUP_CONFIRMATION

            exit_code = main(
                ["--apply", "--config-path", str(config_path)],
                confirmation_reader=change_config_then_confirm,
                command_runner=keychain.status,
                credential_writer=keychain.write,
                executable_locator=lambda _name: str(security_path),
                output=output,
            )
            documents = [
                json.loads(line) for line in output.getvalue().splitlines()
            ]

        self.assertEqual(exit_code, 1)
        self.assertEqual(documents[-1]["failure_stage"], "plan_recheck")
        self.assertFalse(documents[-1]["write_attempted"])
        self.assertEqual(keychain.write_calls, [])
        _assert_redacted(self, output.getvalue())

    def test_existing_reference_is_rejected_create_only_during_preview(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            config_path = _write_config(root)
            security_path = _fake_security(root)
            keychain = FakeKeychain(present=True)
            output = io.StringIO()

            exit_code = main(
                ["--config-path", str(config_path)],
                command_runner=keychain.status,
                credential_writer=_forbidden_writer,
                executable_locator=lambda _name: str(security_path),
                output=output,
            )
            document = json.loads(output.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertEqual(document["failure_stage"], "preview")
        self.assertFalse(document["write_attempted"])
        self.assertEqual(keychain.write_calls, [])
        _assert_redacted(self, output.getvalue())

    def test_writer_failure_is_redacted_and_never_claimed_retry_safe(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            config_path = _write_config(root)
            security_path = _fake_security(root)
            keychain = FakeKeychain(write_status=1)
            output = io.StringIO()

            exit_code = main(
                ["--apply", "--config-path", str(config_path)],
                confirmation_reader=lambda _prompt: (
                    FAMILY_CALENDAR_KEYCHAIN_SETUP_CONFIRMATION
                ),
                command_runner=keychain.status,
                credential_writer=keychain.write,
                executable_locator=lambda _name: str(security_path),
                output=output,
            )
            documents = [
                json.loads(line) for line in output.getvalue().splitlines()
            ]

        self.assertEqual(exit_code, 1)
        self.assertEqual(documents[-1]["failure_stage"], "keychain_write")
        self.assertTrue(documents[-1]["write_attempted"])
        self.assertTrue(documents[-1]["write_outcome_unknown"])
        self.assertFalse(documents[-1]["retry_safe"])
        _assert_redacted(self, output.getvalue())

    def test_successful_writer_without_reference_fails_verification_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            config_path = _write_config(root)
            security_path = _fake_security(root)
            keychain = FakeKeychain()
            plan = plan_family_calendar_keychain_setup(
                config_path=config_path,
                command_runner=keychain.status,
                executable_locator=lambda _name: str(security_path),
            )

            with self.assertRaises(FamilyCalendarKeychainSetupError) as raised:
                apply_family_calendar_keychain_setup(
                    plan,
                    confirmation=FAMILY_CALENDAR_KEYCHAIN_SETUP_CONFIRMATION,
                    command_runner=keychain.status,
                    credential_writer=lambda _argv: 0,
                    executable_locator=lambda _name: str(security_path),
                )

        self.assertEqual(raised.exception.stage, "verification")
        self.assertTrue(raised.exception.write_attempted)

    def test_plan_repr_and_safe_document_omit_private_configuration(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            config_path = _write_config(root)
            security_path = _fake_security(root)
            keychain = FakeKeychain()

            plan = plan_family_calendar_keychain_setup(
                config_path=config_path,
                command_runner=keychain.status,
                executable_locator=lambda _name: str(security_path),
            )
            rendered = repr(plan) + json.dumps(plan.safe_document())

        _assert_redacted(self, rendered)
        self.assertNotIn(str(config_path), rendered)
        self.assertNotIn(str(security_path), rendered)


def _write_config(
    root: Path,
    *,
    fourth_address: str = "four@example.invalid",
) -> Path:
    private_dir = root / "family_calendar"
    private_dir.mkdir(mode=0o700, exist_ok=True)
    os.chmod(private_dir, 0o700)
    path = private_dir / "notification_config.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "mode": "dry_run",
                "smtp_provider": "icloud",
                "sender_address": "sender@example.invalid",
                "recipients": [
                    {
                        "recipient_id": "recipient-1",
                        "address": "one@example.invalid",
                    },
                    {
                        "recipient_id": "recipient-2",
                        "address": "two@example.invalid",
                    },
                    {
                        "recipient_id": "recipient-3",
                        "address": "three@example.invalid",
                    },
                    {
                        "recipient_id": "recipient-4",
                        "address": fourth_address,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    os.chmod(path, 0o600)
    return path


def _fake_security(root: Path) -> Path:
    path = root / "security"
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    os.chmod(path, 0o700)
    return path


def _forbidden_reader(_prompt: str) -> str:
    raise AssertionError("preview must not request confirmation or password")


def _forbidden_writer(_argv) -> int:
    raise AssertionError("preview must not invoke the Keychain writer")


def _assert_redacted(test_case: unittest.TestCase, text: str) -> None:
    test_case.assertNotIn(PRIVATE_SENTINEL, text)
    test_case.assertNotIn("sender@example.invalid", text)
    test_case.assertNotIn("one@example.invalid", text)
    test_case.assertNotIn("two@example.invalid", text)
    test_case.assertNotIn("three@example.invalid", text)
    test_case.assertNotIn("four@example.invalid", text)
    test_case.assertNotIn("changed@example.invalid", text)
