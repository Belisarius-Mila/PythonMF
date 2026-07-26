from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.family_calendar_delivery_config import (
    CANONICAL_RECIPIENT_IDS,
    DELIVERY_CONFIG_SCHEMA_VERSION,
    MAX_DELIVERY_CONFIG_BYTES,
    DeliveryConfigError,
    DeliveryConfigMode,
    load_family_calendar_delivery_config,
)


class FamilyCalendarDeliveryConfigTests(unittest.TestCase):
    def test_loads_disabled_private_config_with_four_canonical_recipients(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _write_private_config(Path(temp_dir), _valid_document())

            config = load_family_calendar_delivery_config(path)

        self.assertEqual(config.mode, DeliveryConfigMode.DISABLED)
        self.assertEqual(config.smtp_provider, "icloud")
        self.assertEqual(config.sender_address, "sender@example.invalid")
        self.assertEqual(config.recipient_ids, CANONICAL_RECIPIENT_IDS)
        self.assertEqual(config.recipients[0].address, "one@example.invalid")
        self.assertFalse(hasattr(config, "password"))
        self.assertFalse(hasattr(config, "credential_ref"))
        self.assertNotIn("@", repr(config))
        self.assertNotIn("@", repr(config.recipients[0]))

    def test_accepts_both_supported_smtp_providers(self) -> None:
        for provider in ("icloud", "seznam"):
            with self.subTest(provider=provider):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    document = _valid_document()
                    document["smtp_provider"] = provider
                    path = _write_private_config(Path(temp_dir), document)

                    config = load_family_calendar_delivery_config(path)

                self.assertEqual(config.smtp_provider, provider)

    def test_loads_dry_run_mode_without_exposing_recipients(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            document = _valid_document()
            document["mode"] = "dry_run"
            path = _write_private_config(Path(temp_dir), document)

            config = load_family_calendar_delivery_config(path)

        self.assertEqual(config.mode, DeliveryConfigMode.DRY_RUN)
        self.assertEqual(config.recipient_ids, CANONICAL_RECIPIENT_IDS)
        self.assertNotIn("@", repr(config))

    def test_loads_enabled_icloud_mode_without_credential_fields(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            document = _valid_document()
            document["mode"] = "enabled"
            path = _write_private_config(Path(temp_dir), document)

            config = load_family_calendar_delivery_config(path)

        self.assertEqual(config.mode, DeliveryConfigMode.ENABLED)
        self.assertEqual(config.smtp_provider, "icloud")
        self.assertFalse(hasattr(config, "password"))
        self.assertFalse(hasattr(config, "credential_ref"))
        self.assertNotIn("@", repr(config))

    def test_schema_two_requires_a_valid_redacted_sender_address(self) -> None:
        self.assertEqual(DELIVERY_CONFIG_SCHEMA_VERSION, 2)
        invalid_senders = (
            "not-an-email",
            "private@example.invalid\r\nBcc: hidden@example.invalid",
        )
        for sender_address in invalid_senders:
            with self.subTest(sender_address=sender_address):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    document = _valid_document()
                    document["sender_address"] = sender_address
                    path = _write_private_config(Path(temp_dir), document)

                    with self.assertRaises(DeliveryConfigError) as raised:
                        load_family_calendar_delivery_config(path)

                self.assertNotIn("@", str(raised.exception))
                self.assertNotIn("private", str(raised.exception).casefold())

    def test_rejects_passwords_and_free_form_credential_references(self) -> None:
        for forbidden_field in ("password", "credential_ref", "password_env"):
            with self.subTest(forbidden_field=forbidden_field):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    document = _valid_document()
                    document[forbidden_field] = "private-secret-value"
                    path = _write_private_config(Path(temp_dir), document)

                    with self.assertRaisesRegex(DeliveryConfigError, "invalid shape") as raised:
                        load_family_calendar_delivery_config(path)

                self.assertNotIn("private-secret-value", str(raised.exception))

    def test_missing_config_fails_closed_without_creating_anything(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "family" / "notification_config.json"

            with self.assertRaisesRegex(DeliveryConfigError, "missing"):
                load_family_calendar_delivery_config(path)

            self.assertFalse(path.exists())
            self.assertFalse(path.parent.exists())

    def test_enabled_mode_rejects_provider_without_runtime_adapter(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            document = _valid_document()
            document["mode"] = "enabled"
            document["smtp_provider"] = "seznam"
            path = _write_private_config(Path(temp_dir), document)

            with self.assertRaisesRegex(DeliveryConfigError, "iCloud"):
                load_family_calendar_delivery_config(path)

    def test_legacy_schema_without_sender_fails_closed_without_migration(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            document = _valid_document()
            document["schema_version"] = 1
            document.pop("sender_address")
            path = _write_private_config(Path(temp_dir), document)
            original = path.read_text(encoding="utf-8")

            with self.assertRaises(DeliveryConfigError):
                load_family_calendar_delivery_config(path)

            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_requires_exactly_four_canonical_recipient_ids(self) -> None:
        invalid_recipient_sets = (
            _valid_document()["recipients"][:3],
            [
                *_valid_document()["recipients"][:3],
                {"recipient_id": "recipient-5", "address": "five@example.invalid"},
            ],
        )
        for recipients in invalid_recipient_sets:
            with self.subTest(recipients=recipients):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    document = _valid_document()
                    document["recipients"] = recipients
                    path = _write_private_config(Path(temp_dir), document)

                    with self.assertRaises(DeliveryConfigError):
                        load_family_calendar_delivery_config(path)

    def test_rejects_duplicate_addresses_case_insensitively(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            document = _valid_document()
            document["recipients"][3]["address"] = "ONE@EXAMPLE.INVALID"
            path = _write_private_config(Path(temp_dir), document)

            with self.assertRaisesRegex(DeliveryConfigError, "duplicate recipient addresses"):
                load_family_calendar_delivery_config(path)

    def test_invalid_address_is_not_repeated_in_error_or_repr(self) -> None:
        private_value = "private-value@example.invalid\r\nInjected: value"
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            document = _valid_document()
            document["recipients"][0]["address"] = private_value
            path = _write_private_config(Path(temp_dir), document)

            with self.assertRaises(DeliveryConfigError) as raised:
                load_family_calendar_delivery_config(path)

        self.assertNotIn("private-value", str(raised.exception))
        self.assertNotIn("example.invalid", str(raised.exception))

    def test_unknown_schema_extra_fields_and_invalid_json_fail_closed(self) -> None:
        documents = []
        unknown_schema = _valid_document()
        unknown_schema["schema_version"] = DELIVERY_CONFIG_SCHEMA_VERSION + 1
        documents.append(json.dumps(unknown_schema))
        extra_field = _valid_document()
        extra_field["unexpected"] = True
        documents.append(json.dumps(extra_field))
        documents.append("{not-json")

        for content in documents:
            with self.subTest(content=content[:30]):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    path = _write_private_text(Path(temp_dir), content)

                    with self.assertRaises(DeliveryConfigError):
                        load_family_calendar_delivery_config(path)

    def test_rejects_non_integer_schema_and_oversized_file(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            document = _valid_document()
            document["schema_version"] = 1.0
            path = _write_private_config(Path(temp_dir), document)

            with self.assertRaisesRegex(DeliveryConfigError, "schema"):
                load_family_calendar_delivery_config(path)

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _write_private_text(Path(temp_dir), "x" * (MAX_DELIVERY_CONFIG_BYTES + 1))

            with self.assertRaisesRegex(DeliveryConfigError, "too large"):
                load_family_calendar_delivery_config(path)

    def test_rejects_non_private_permissions_without_repairing_them(self) -> None:
        for target in ("directory", "file"):
            with self.subTest(target=target):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    path = _write_private_config(Path(temp_dir), _valid_document())
                    if target == "directory":
                        path.parent.chmod(0o755)
                    else:
                        path.chmod(0o644)

                    with self.assertRaisesRegex(DeliveryConfigError, "not private"):
                        load_family_calendar_delivery_config(path)

                    expected_mode = 0o755 if target == "directory" else 0o644
                    actual_path = path.parent if target == "directory" else path
                    self.assertEqual(actual_path.stat().st_mode & 0o777, expected_mode)

    def test_rejects_symbolic_link_without_reading_target(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            real_path = _write_private_config(root, _valid_document())
            link_path = root / "family" / "linked_config.json"
            link_path.symlink_to(real_path)

            with self.assertRaisesRegex(DeliveryConfigError, "symbolic links"):
                load_family_calendar_delivery_config(link_path)


def _valid_document() -> dict:
    return {
        "schema_version": DELIVERY_CONFIG_SCHEMA_VERSION,
        "mode": "disabled",
        "smtp_provider": "icloud",
        "sender_address": "sender@example.invalid",
        "recipients": [
            {"recipient_id": "recipient-4", "address": "four@example.invalid"},
            {"recipient_id": "recipient-2", "address": "two@example.invalid"},
            {"recipient_id": "recipient-1", "address": "one@example.invalid"},
            {"recipient_id": "recipient-3", "address": "three@example.invalid"},
        ],
    }


def _write_private_config(root: Path, document: dict) -> Path:
    return _write_private_text(root, json.dumps(document))


def _write_private_text(root: Path, content: str) -> Path:
    private_dir = root / "family"
    private_dir.mkdir(mode=0o700)
    path = private_dir / "notification_config.json"
    path.write_text(content, encoding="utf-8")
    path.chmod(0o600)
    return path


if __name__ == "__main__":
    unittest.main()
