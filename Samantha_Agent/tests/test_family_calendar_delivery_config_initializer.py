from __future__ import annotations

import io
import json
import stat
import tempfile
import unittest
from collections.abc import Iterator, Mapping
from pathlib import Path

from app.family_calendar_delivery_config import load_family_calendar_delivery_config
from app.family_calendar_delivery_config_initializer import (
    DELIVERY_CONFIG_INITIALIZATION_CONFIRMATION,
    DeliveryConfigInitializationError,
    DeliveryConfigInitializationPlan,
    apply_family_calendar_delivery_config_initialization,
    plan_family_calendar_delivery_config_initialization,
)
from scripts.family_calendar_delivery_config_initialize import main


ADDRESSES = (
    "one@example.invalid",
    "two@example.invalid",
    "three@example.invalid",
    "four@example.invalid",
)
SENDER_ADDRESS = "sender@example.invalid"


class TrackingEnvironment(Mapping[str, str]):
    def __init__(self, values: dict[str, str]) -> None:
        self.values = values
        self.requested_keys: list[str] = []

    def __getitem__(self, key: str) -> str:
        self.requested_keys.append(key)
        return self.values[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.values)

    def __len__(self) -> int:
        return len(self.values)

    def get(self, key: str, default: str | None = None) -> str | None:
        self.requested_keys.append(key)
        return self.values.get(key, default)


class SecretReader:
    def __init__(self, values: tuple[str, ...]) -> None:
        self.values = iter(values)
        self.prompts: list[str] = []

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return next(self.values)


class FamilyCalendarDeliveryConfigInitializerTests(unittest.TestCase):
    def test_plan_is_read_only_disabled_and_redacted(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "family" / "notification_config.json"

            plan = plan_family_calendar_delivery_config_initialization(
                smtp_provider="icloud",
                sender_address=SENDER_ADDRESS,
                recipient_addresses=ADDRESSES,
                path=path,
            )

            self.assertFalse(path.parent.exists())
            self.assertEqual(plan.config.mode.value, "disabled")
            self.assertEqual(len(plan.config.recipients), 4)
            self.assertEqual(
                plan.safe_document(),
                {
                    "status": "ready",
                    "schema": 2,
                    "mode": "disabled",
                    "recipient_count": 4,
                },
            )
            _assert_redacted(self, repr(plan), path)

    def test_wrong_confirmation_creates_nothing(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "family" / "notification_config.json"
            plan = _plan(path)

            with self.assertRaisesRegex(DeliveryConfigInitializationError, "confirmation"):
                apply_family_calendar_delivery_config_initialization(
                    plan,
                    confirmation="yes",
                )

            self.assertFalse(path.parent.exists())

    def test_exact_confirmation_creates_private_disabled_schema_two_once(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "family" / "notification_config.json"
            plan = _plan(path)

            result = apply_family_calendar_delivery_config_initialization(
                plan,
                confirmation=DELIVERY_CONFIG_INITIALIZATION_CONFIRMATION,
            )
            config = load_family_calendar_delivery_config(path)

            self.assertEqual(config, plan.config)
            self.assertEqual(result.config.mode.value, "disabled")
            self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["schema_version"], 2)
            self.assertEqual(list(path.parent.glob(f".{path.name}.*.tmp")), [])
            self.assertFalse(path.with_name("notification_config.schema1.backup.json").exists())
            _assert_redacted(self, repr(result), path)

            with self.assertRaises(DeliveryConfigInitializationError):
                apply_family_calendar_delivery_config_initialization(
                    plan,
                    confirmation=DELIVERY_CONFIG_INITIALIZATION_CONFIRMATION,
                )
            self.assertEqual(load_family_calendar_delivery_config(path), config)

    def test_existing_target_and_unsafe_directory_are_never_repaired_or_replaced(self) -> None:
        for case in ("existing", "unsafe_directory"):
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    parent = Path(temp_dir) / "family"
                    parent.mkdir(mode=0o700)
                    path = parent / "notification_config.json"
                    if case == "existing":
                        path.write_text("existing private data", encoding="utf-8")
                        path.chmod(0o600)
                    else:
                        parent.chmod(0o755)

                    with self.assertRaises(DeliveryConfigInitializationError):
                        _plan(path)

                    if case == "existing":
                        self.assertEqual(
                            path.read_text(encoding="utf-8"),
                            "existing private data",
                        )
                    else:
                        self.assertEqual(stat.S_IMODE(parent.stat().st_mode), 0o755)
                        self.assertFalse(path.exists())

    def test_existing_target_symlink_is_refused_without_reading_or_replacing_it(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            parent = Path(temp_dir) / "family"
            parent.mkdir(mode=0o700)
            private_source = Path(temp_dir) / "private-source.json"
            private_source.write_text("private source", encoding="utf-8")
            path = parent / "notification_config.json"
            path.symlink_to(private_source)

            with self.assertRaises(DeliveryConfigInitializationError):
                _plan(path)

            self.assertTrue(path.is_symlink())
            self.assertEqual(private_source.read_text(encoding="utf-8"), "private source")

    def test_invalid_private_inputs_are_redacted_and_create_nothing(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "family" / "notification_config.json"

            with self.assertRaises(DeliveryConfigInitializationError) as raised:
                plan_family_calendar_delivery_config_initialization(
                    smtp_provider="icloud",
                    sender_address=SENDER_ADDRESS,
                    recipient_addresses=(
                        ADDRESSES[0],
                        ADDRESSES[1],
                        ADDRESSES[2],
                        "private@example.invalid\r\nBcc: hidden@example.invalid",
                    ),
                    path=path,
                )

            _assert_redacted(self, str(raised.exception), path)
            self.assertFalse(path.parent.exists())

    def test_cli_reads_only_sender_address_and_creates_after_hidden_double_entry(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "family" / "notification_config.json"
            environment = TrackingEnvironment(
                {
                    "ICLOUD_MAIL_ADDRESS": SENDER_ADDRESS,
                    "ICLOUD_MAIL_PASSWORD": "must-not-be-read",
                }
            )
            reader = SecretReader(tuple(value for address in ADDRESSES for value in (address, address)))
            output = io.StringIO()

            exit_code = main(
                ["--provider", "icloud", "--path", str(path)],
                environment=environment,
                secret_reader=reader,
                confirmation_reader=lambda _prompt: DELIVERY_CONFIG_INITIALIZATION_CONFIRMATION,
                output=output,
            )

            documents = [json.loads(line) for line in output.getvalue().splitlines()]
            self.assertEqual(exit_code, 0)
            self.assertEqual(environment.requested_keys, ["ICLOUD_MAIL_ADDRESS"])
            self.assertEqual(len(reader.prompts), 8)
            self.assertEqual(documents[0]["status"], "ready")
            self.assertEqual(documents[1]["status"], "created")
            self.assertEqual(load_family_calendar_delivery_config(path).mode.value, "disabled")
            _assert_redacted(self, output.getvalue(), path)
            for prompt in reader.prompts:
                _assert_redacted(self, prompt, path)

    def test_cli_missing_sender_does_not_prompt_or_read_password(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "family" / "notification_config.json"
            environment = TrackingEnvironment(
                {"ICLOUD_MAIL_PASSWORD": "must-not-be-read"}
            )
            reader = SecretReader(())
            output = io.StringIO()

            exit_code = main(
                ["--provider", "icloud", "--path", str(path)],
                environment=environment,
                secret_reader=reader,
                confirmation_reader=lambda _prompt: "must-not-be-called",
                output=output,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(environment.requested_keys, ["ICLOUD_MAIL_ADDRESS"])
            self.assertEqual(reader.prompts, [])
            self.assertFalse(path.parent.exists())
            self.assertEqual(
                json.loads(output.getvalue()),
                {"redacted": True, "status": "failed"},
            )

    def test_cli_mismatch_or_wrong_confirmation_never_creates_target(self) -> None:
        cases = ("mismatch", "wrong_confirmation")
        for case in cases:
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    path = Path(temp_dir) / "family" / "notification_config.json"
                    values = tuple(
                        value
                        for address in ADDRESSES
                        for value in (address, address)
                    )
                    if case == "mismatch":
                        values = (ADDRESSES[0], ADDRESSES[1])
                    output = io.StringIO()

                    exit_code = main(
                        ["--provider", "seznam", "--path", str(path)],
                        environment={"SEZNAM_MAIL_ADDRESS": SENDER_ADDRESS},
                        secret_reader=SecretReader(values),
                        confirmation_reader=lambda _prompt: "wrong",
                        output=output,
                    )

                    self.assertEqual(exit_code, 1)
                    self.assertFalse(path.exists())
                    self.assertEqual(
                        json.loads(output.getvalue().splitlines()[-1]),
                        {"redacted": True, "status": "failed"},
                    )
                    _assert_redacted(self, output.getvalue(), path)


def _plan(path: Path) -> DeliveryConfigInitializationPlan:
    return plan_family_calendar_delivery_config_initialization(
        smtp_provider="icloud",
        sender_address=SENDER_ADDRESS,
        recipient_addresses=ADDRESSES,
        path=path,
    )


def _assert_redacted(
    test_case: unittest.TestCase,
    visible: str,
    path: Path,
) -> None:
    test_case.assertNotIn("@", visible)
    for value in (*ADDRESSES, SENDER_ADDRESS, "must-not-be-read", str(path)):
        test_case.assertNotIn(value, visible)


if __name__ == "__main__":
    unittest.main()
