from __future__ import annotations

import unittest

from app.capabilities import (
    CapabilityRecord,
    ConfirmationPolicy,
    RiskLevel,
    all_capabilities,
    get_capability,
    validate_registry,
)


class CapabilityRegistryTests(unittest.TestCase):
    def test_registry_is_valid_and_ids_are_unique(self) -> None:
        records = all_capabilities()
        ids = [record.capability_id for record in records]

        self.assertGreaterEqual(len(records), 5)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(validate_registry(), ())

    def test_all_items_are_capability_records(self) -> None:
        for record in all_capabilities():
            self.assertIsInstance(record, CapabilityRecord)

    def test_send_prepared_email_draft_is_external_send_with_exact_confirmation(self) -> None:
        record = get_capability("send_prepared_email_draft")

        self.assertEqual(record.risk, RiskLevel.EXTERNAL_SEND)
        self.assertTrue(record.requires_confirmation)
        self.assertEqual(record.confirmation_policy, ConfirmationPolicy.EXACT_CURRENT_MESSAGE)

    def test_git_push_main_after_guard_requires_green_guard_metadata(self) -> None:
        record = get_capability("git_push_main_after_guard")

        self.assertEqual(record.risk, RiskLevel.GIT_PUBLISH)
        self.assertFalse(record.requires_confirmation)
        self.assertEqual(record.metadata["requires_green_guard"], "true")
        self.assertEqual(record.metadata["allowed_remote"], "origin")
        self.assertEqual(record.metadata["allowed_branch"], "main")

    def test_unknown_capability_raises_key_error(self) -> None:
        with self.assertRaisesRegex(KeyError, "unknown capability_id"):
            get_capability("does_not_exist")

    def test_validate_registry_reports_duplicates(self) -> None:
        first = all_capabilities()[0]

        errors = validate_registry((first, first))

        self.assertEqual(errors, (f"duplicate capability_id: {first.capability_id}",))


if __name__ == "__main__":
    unittest.main()
