from __future__ import annotations

import json
import stat
import tempfile
import unittest
from pathlib import Path

from app.family_calendar_delivery_config import load_family_calendar_delivery_config
from app.family_calendar_delivery_config_migration import (
    DELIVERY_CONFIG_MIGRATION_CONFIRMATION,
    DeliveryConfigMigrationError,
    apply_family_calendar_delivery_config_migration,
    inspect_family_calendar_delivery_config_migration,
    plan_family_calendar_delivery_config_migration,
)
from app.file_persistence import lock_path_for


ADDRESSES = (
    "one@example.invalid",
    "two@example.invalid",
    "three@example.invalid",
    "four@example.invalid",
)
SENDER_ADDRESS = "sender@example.invalid"


class FamilyCalendarDeliveryConfigMigrationTests(unittest.TestCase):
    def test_inspection_is_read_only_and_exposes_only_safe_metadata(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _write_legacy_config(Path(temp_dir))
            original = path.read_bytes()
            entries_before = tuple(sorted(path.parent.iterdir()))

            inspection = inspect_family_calendar_delivery_config_migration(path=path)

            self.assertEqual(inspection.smtp_provider, "icloud")
            self.assertEqual(inspection.mode, "disabled")
            self.assertEqual(inspection.recipient_count, 4)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(tuple(sorted(path.parent.iterdir())), entries_before)
            visible = repr(inspection)
            self.assertIn("from_schema=1", visible)
            self.assertIn("to_schema=2", visible)
            self.assertNotIn("@", visible)
            for private_value in (*ADDRESSES, str(path)):
                self.assertNotIn(private_value, visible)

    def test_plan_is_read_only_and_redacts_all_private_values(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _write_legacy_config(Path(temp_dir))
            original = path.read_bytes()
            entries_before = tuple(sorted(path.parent.iterdir()))

            plan = plan_family_calendar_delivery_config_migration(
                sender_address=SENDER_ADDRESS,
                path=path,
            )

            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(tuple(sorted(path.parent.iterdir())), entries_before)
            self.assertEqual(plan.config.sender_address, SENDER_ADDRESS)
            self.assertEqual(len(plan.config.recipients), 4)
            visible = repr(plan)
            self.assertIn("from_schema=1", visible)
            self.assertIn("to_schema=2", visible)
            self.assertNotIn("@", visible)
            for private_value in (*ADDRESSES, SENDER_ADDRESS, str(path)):
                self.assertNotIn(private_value, visible)

    def test_wrong_confirmation_changes_nothing_and_creates_no_backup(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _write_legacy_config(Path(temp_dir))
            original = path.read_bytes()
            plan = plan_family_calendar_delivery_config_migration(
                sender_address=SENDER_ADDRESS,
                path=path,
            )

            with self.assertRaisesRegex(DeliveryConfigMigrationError, "confirmation"):
                apply_family_calendar_delivery_config_migration(
                    plan,
                    confirmation="yes",
                )

            self.assertEqual(path.read_bytes(), original)
            self.assertFalse(_backup_path(path).exists())
            self.assertFalse(lock_path_for(path).exists())

    def test_confirmed_apply_creates_private_backup_and_atomic_schema_two_config(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _write_legacy_config(Path(temp_dir))
            original = path.read_bytes()
            plan = plan_family_calendar_delivery_config_migration(
                sender_address=SENDER_ADDRESS,
                path=path,
            )

            result = apply_family_calendar_delivery_config_migration(
                plan,
                confirmation=DELIVERY_CONFIG_MIGRATION_CONFIRMATION,
            )
            config = load_family_calendar_delivery_config(path)
            backup_path = _backup_path(path)

            self.assertTrue(result.backup_created)
            self.assertEqual(config.sender_address, SENDER_ADDRESS)
            self.assertEqual(
                tuple(recipient.address for recipient in config.recipients),
                ADDRESSES,
            )
            self.assertEqual(backup_path.read_bytes(), original)
            self.assertEqual(json.loads(backup_path.read_text(encoding="utf-8"))["schema_version"], 1)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["schema_version"], 2)
            self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(backup_path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(lock_path_for(path).stat().st_mode), 0o600)
            visible = repr(result)
            self.assertNotIn("@", visible)
            for private_value in (*ADDRESSES, SENDER_ADDRESS):
                self.assertNotIn(private_value, visible)

    def test_changed_source_is_not_overwritten_after_planning(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _write_legacy_config(Path(temp_dir))
            plan = plan_family_calendar_delivery_config_migration(
                sender_address=SENDER_ADDRESS,
                path=path,
            )
            changed = _legacy_document()
            changed["mode"] = "dry_run"
            changed_text = json.dumps(changed)
            path.write_text(changed_text, encoding="utf-8")
            path.chmod(0o600)

            with self.assertRaisesRegex(DeliveryConfigMigrationError, "changed"):
                apply_family_calendar_delivery_config_migration(
                    plan,
                    confirmation=DELIVERY_CONFIG_MIGRATION_CONFIRMATION,
                )

            self.assertEqual(path.read_text(encoding="utf-8"), changed_text)
            self.assertFalse(_backup_path(path).exists())

    def test_existing_backup_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _write_legacy_config(Path(temp_dir))
            original = path.read_bytes()
            backup_path = _backup_path(path)
            backup_path.write_text("existing private backup", encoding="utf-8")
            backup_path.chmod(0o600)
            plan = plan_family_calendar_delivery_config_migration(
                sender_address=SENDER_ADDRESS,
                path=path,
            )

            with self.assertRaisesRegex(DeliveryConfigMigrationError, "backup already exists"):
                apply_family_calendar_delivery_config_migration(
                    plan,
                    confirmation=DELIVERY_CONFIG_MIGRATION_CONFIRMATION,
                )

            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(
                backup_path.read_text(encoding="utf-8"),
                "existing private backup",
            )

    def test_invalid_legacy_schema_secrets_and_permissions_fail_closed(self) -> None:
        cases = ("schema_two", "secret_field", "permissions", "invalid_sender")
        for case in cases:
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    path = _write_legacy_config(Path(temp_dir))
                    sender_address = SENDER_ADDRESS
                    if case == "schema_two":
                        document = _legacy_document()
                        document["schema_version"] = 2
                        path.write_text(json.dumps(document), encoding="utf-8")
                    elif case == "secret_field":
                        document = _legacy_document()
                        document["password"] = "private-secret-value"
                        path.write_text(json.dumps(document), encoding="utf-8")
                    elif case == "permissions":
                        path.chmod(0o644)
                    else:
                        sender_address = "private@example.invalid\r\nBcc: hidden@example.invalid"

                    with self.assertRaises(DeliveryConfigMigrationError) as raised:
                        plan_family_calendar_delivery_config_migration(
                            sender_address=sender_address,
                            path=path,
                        )

                    self.assertNotIn("@", str(raised.exception))
                    self.assertNotIn("private-secret-value", str(raised.exception))
                    self.assertFalse(_backup_path(path).exists())


def _legacy_document() -> dict:
    return {
        "schema_version": 1,
        "mode": "disabled",
        "smtp_provider": "icloud",
        "recipients": [
            {"recipient_id": f"recipient-{index}", "address": address}
            for index, address in enumerate(ADDRESSES, start=1)
        ],
    }


def _write_legacy_config(root: Path) -> Path:
    private_dir = root / "family"
    private_dir.mkdir(mode=0o700)
    path = private_dir / "notification_config.json"
    path.write_text(json.dumps(_legacy_document()), encoding="utf-8")
    path.chmod(0o600)
    return path


def _backup_path(path: Path) -> Path:
    return path.with_name("notification_config.schema1.backup.json")


if __name__ == "__main__":
    unittest.main()
