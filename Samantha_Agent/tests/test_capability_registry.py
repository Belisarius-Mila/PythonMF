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

        self.assertGreaterEqual(len(records), 25)
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

    def test_send_confirmed_sms_rcs_is_external_send_with_exact_confirmation(self) -> None:
        record = get_capability("send_confirmed_sms_rcs")

        self.assertEqual(record.risk, RiskLevel.EXTERNAL_SEND)
        self.assertTrue(record.requires_confirmation)
        self.assertEqual(record.confirmation_policy, ConfirmationPolicy.EXACT_CURRENT_MESSAGE)

    def test_confirmed_local_write_capabilities_require_confirmation(self) -> None:
        for capability_id in (
            "archive_email_by_uid",
            "save_selected_email_cases_from_uids",
            "prepare_forward_email_by_uid",
            "mark_reminder_done",
            "save_email_action_case_reminder",
            "save_payment_case_document",
            "save_payment_sms_reminder",
            "save_document_due_reminder",
            "apply_document_import",
            "apply_document_reindex",
            "apply_mobile_document_final_import",
            "apply_vyrazeni_leku",
            "apply_zmenseni_obrazku",
            "apply_lekarna_photo_import",
        ):
            with self.subTest(capability_id=capability_id):
                record = get_capability(capability_id)
                self.assertEqual(record.risk, RiskLevel.LOCAL_WRITE)
                self.assertTrue(record.requires_confirmation)
                self.assertEqual(record.confirmation_policy, ConfirmationPolicy.EXACT_CURRENT_MESSAGE)

    def test_mobile_processing_describes_unconfirmed_local_write(self) -> None:
        record = get_capability("process_mobile_document_inbox")

        self.assertEqual(record.risk, RiskLevel.LOCAL_WRITE)
        self.assertFalse(record.requires_confirmation)

    def test_print_and_inbox_resolution_are_strictly_confirmed(self) -> None:
        expected = {
            "restore_path_from_backup": RiskLevel.DESTRUCTIVE,
            "run_workflow_command": RiskLevel.SYSTEM_CHANGE,
            "run_document_print_job": RiskLevel.SYSTEM_CHANGE,
            "resolve_document_inbox_item": RiskLevel.DESTRUCTIVE,
        }
        for capability_id, risk in expected.items():
            with self.subTest(capability_id=capability_id):
                record = get_capability(capability_id)
                self.assertEqual(record.risk, risk)
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
