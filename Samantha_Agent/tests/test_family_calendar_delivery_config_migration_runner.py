from __future__ import annotations

import io
import json
import tempfile
import unittest
from collections.abc import Iterator, Mapping
from pathlib import Path

from app.family_calendar_delivery_config import load_family_calendar_delivery_config
from app.family_calendar_delivery_config_migration import (
    DELIVERY_CONFIG_MIGRATION_CONFIRMATION,
)
from app.family_calendar_delivery_config_migration_runner import (
    LocalDeliveryConfigMigrationRunnerError,
    run_local_family_calendar_delivery_config_migration,
)
from app.file_persistence import lock_path_for
from scripts.family_calendar_delivery_config_migrate import main


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


class FamilyCalendarDeliveryConfigMigrationRunnerTests(unittest.TestCase):
    def test_preview_reads_only_provider_address_and_changes_nothing(self) -> None:
        for provider, expected_key in (
            ("icloud", "ICLOUD_MAIL_ADDRESS"),
            ("seznam", "SEZNAM_MAIL_ADDRESS"),
        ):
            with self.subTest(provider=provider):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    path = _write_legacy_config(Path(temp_dir), provider=provider)
                    original = path.read_bytes()
                    entries_before = tuple(sorted(path.parent.iterdir()))
                    environment = TrackingEnvironment(
                        {
                            expected_key: SENDER_ADDRESS,
                            "ICLOUD_MAIL_PASSWORD": "must-not-be-read",
                            "SEZNAM_MAIL_PASSWORD": "must-not-be-read",
                        }
                    )

                    result = run_local_family_calendar_delivery_config_migration(
                        path=path,
                        environment=environment,
                    )

                    self.assertEqual(result.status, "preview")
                    self.assertEqual(result.mode, "disabled")
                    self.assertEqual(result.recipient_count, 4)
                    self.assertFalse(result.backup_created)
                    self.assertEqual(environment.requested_keys, [expected_key])
                    self.assertEqual(path.read_bytes(), original)
                    self.assertEqual(tuple(sorted(path.parent.iterdir())), entries_before)
                    _assert_redacted(self, repr(result), path)

    def test_missing_sender_fails_without_writing_or_exposing_private_values(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _write_legacy_config(Path(temp_dir))
            original = path.read_bytes()
            environment = TrackingEnvironment({"ICLOUD_MAIL_PASSWORD": "private-secret"})

            with self.assertRaises(LocalDeliveryConfigMigrationRunnerError) as raised:
                run_local_family_calendar_delivery_config_migration(
                    path=path,
                    environment=environment,
                )

            self.assertEqual(environment.requested_keys, ["ICLOUD_MAIL_ADDRESS"])
            self.assertEqual(path.read_bytes(), original)
            self.assertFalse(_backup_path(path).exists())
            self.assertFalse(lock_path_for(path).exists())
            _assert_redacted(self, str(raised.exception), path)

    def test_wrong_confirmation_cannot_apply(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _write_legacy_config(Path(temp_dir))
            original = path.read_bytes()

            with self.assertRaisesRegex(
                LocalDeliveryConfigMigrationRunnerError,
                "confirmation",
            ):
                run_local_family_calendar_delivery_config_migration(
                    path=path,
                    apply=True,
                    confirmation="yes",
                    environment={"ICLOUD_MAIL_ADDRESS": SENDER_ADDRESS},
                )

            self.assertEqual(path.read_bytes(), original)
            self.assertFalse(_backup_path(path).exists())
            self.assertFalse(lock_path_for(path).exists())

    def test_exact_confirmation_applies_existing_safe_migration(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _write_legacy_config(Path(temp_dir))
            original = path.read_bytes()

            result = run_local_family_calendar_delivery_config_migration(
                path=path,
                apply=True,
                confirmation=DELIVERY_CONFIG_MIGRATION_CONFIRMATION,
                environment={"ICLOUD_MAIL_ADDRESS": SENDER_ADDRESS},
            )

            self.assertEqual(result.status, "applied")
            self.assertTrue(result.backup_created)
            self.assertEqual(
                load_family_calendar_delivery_config(path).sender_address,
                SENDER_ADDRESS,
            )
            self.assertEqual(_backup_path(path).read_bytes(), original)
            _assert_redacted(self, repr(result), path)

    def test_cli_defaults_to_redacted_preview(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _write_legacy_config(Path(temp_dir))
            original = path.read_bytes()
            output = io.StringIO()

            exit_code = main(
                ["--path", str(path)],
                environment={"ICLOUD_MAIL_ADDRESS": SENDER_ADDRESS},
                output=output,
            )

            document = json.loads(output.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(
                document,
                {
                    "backup_created": False,
                    "from_schema": 1,
                    "mode": "disabled",
                    "recipient_count": 4,
                    "status": "preview",
                    "to_schema": 2,
                },
            )
            self.assertEqual(path.read_bytes(), original)
            _assert_redacted(self, output.getvalue(), path)

    def test_cli_failure_is_generic_and_redacted(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _write_legacy_config(Path(temp_dir))
            output = io.StringIO()

            exit_code = main(
                ["--path", str(path), "--apply", "--confirmation", "wrong"],
                environment={"ICLOUD_MAIL_ADDRESS": SENDER_ADDRESS},
                output=output,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(
                json.loads(output.getvalue()),
                {"redacted": True, "status": "failed"},
            )
            _assert_redacted(self, output.getvalue(), path)


def _legacy_document(provider: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "mode": "disabled",
        "smtp_provider": provider,
        "recipients": [
            {"recipient_id": f"recipient-{index}", "address": address}
            for index, address in enumerate(ADDRESSES, start=1)
        ],
    }


def _write_legacy_config(root: Path, *, provider: str = "icloud") -> Path:
    private_dir = root / "family"
    private_dir.mkdir(mode=0o700)
    path = private_dir / "notification_config.json"
    path.write_text(json.dumps(_legacy_document(provider)), encoding="utf-8")
    path.chmod(0o600)
    return path


def _backup_path(path: Path) -> Path:
    return path.with_name("notification_config.schema1.backup.json")


def _assert_redacted(
    test_case: unittest.TestCase,
    visible: str,
    path: Path,
) -> None:
    test_case.assertNotIn("@", visible)
    for private_value in (*ADDRESSES, SENDER_ADDRESS, "private-secret", str(path)):
        test_case.assertNotIn(private_value, visible)


if __name__ == "__main__":
    unittest.main()
