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

        self.assertGreaterEqual(len(records), 84)
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

    def test_generation_capabilities_use_durable_external_generation_consent(self) -> None:
        record = get_capability("generate_human_adam_image_candidate")

        self.assertEqual(record.risk, RiskLevel.EXTERNAL_GENERATION)
        self.assertFalse(record.requires_confirmation)
        self.assertEqual(
            record.metadata["durable_consent"],
            "trusted_external_generation_v1",
        )
        self.assertIn("HumanAdamImageCandidateStore.generate", record.tool)

        audio = get_capability("generate_project_audio_asset")
        self.assertEqual(audio.risk, RiskLevel.EXTERNAL_GENERATION)
        self.assertFalse(audio.requires_confirmation)
        self.assertEqual(
            audio.metadata["durable_consent"],
            "trusted_external_generation_v1",
        )
        self.assertEqual(
            audio.tool,
            "app.speech.edge_tts_mp3.synthesize_edge_tts_mp3_sync",
        )

    def test_confirmed_local_write_capabilities_require_confirmation(self) -> None:
        for capability_id in (
            "archive_email_by_uid",
            "save_selected_email_cases_from_uids",
            "mark_reminder_done",
            "save_email_action_case_reminder",
            "save_payment_case_document",
            "save_payment_sms_reminder",
            "save_document_due_reminder",
            "apply_document_import",
            "apply_document_reindex",
            "apply_mobile_document_final_import",
            "copy_downloads_files_to_knowledge_inbox",
            "prepare_iphone_shortcut",
            "apply_vyrazeni_leku",
            "apply_zmenseni_obrazku",
            "apply_lekarna_photo_import",
        ):
            with self.subTest(capability_id=capability_id):
                record = get_capability(capability_id)
                self.assertEqual(record.risk, RiskLevel.LOCAL_WRITE)
                self.assertTrue(record.requires_confirmation)
                self.assertEqual(record.confirmation_policy, ConfirmationPolicy.EXACT_CURRENT_MESSAGE)

    def test_unconfirmed_local_write_capabilities_match_existing_safe_workflows(self) -> None:
        for capability_id in (
            "process_mobile_document_inbox",
            "samantha_knowledge_inbox_inventory",
            "samantha_quantitative_status",
            "samantha_project_audit",
            "list_quick_notes",
            "show_quick_note_detail",
            "quick_notes_action_status",
            "preview_workflow_command",
            "stage_lekarna_photo_import",
            "prepare_mobile_document_batch",
            "prepare_next_scandocu_document",
            "prepare_document_print_job",
            "prepare_lekarna_photo_import",
            "prepare_forward_email_by_uid",
            "run_email_triage_session",
            "run_unified_email_triage_session",
            "prepare_human_adam_image_candidate",
            "review_human_adam_image_candidate",
        ):
            with self.subTest(capability_id=capability_id):
                record = get_capability(capability_id)
                self.assertEqual(record.risk, RiskLevel.LOCAL_WRITE)
                self.assertFalse(record.requires_confirmation)

    def test_read_only_inbox_and_shortcuts_status_do_not_require_confirmation(self) -> None:
        for capability_id in (
            "samantha_downloads_inventory",
            "iphone_shortcuts_playground_status",
        ):
            with self.subTest(capability_id=capability_id):
                record = get_capability(capability_id)
                self.assertEqual(record.risk, RiskLevel.READ_ONLY)
                self.assertFalse(record.requires_confirmation)

    def test_read_only_backup_and_workflow_previews_do_not_require_confirmation(self) -> None:
        for capability_id in (
            "list_backup_snapshots",
            "preview_backup_restore",
            "list_workflow_commands",
        ):
            with self.subTest(capability_id=capability_id):
                record = get_capability(capability_id)
                self.assertEqual(record.risk, RiskLevel.READ_ONLY)
                self.assertFalse(record.requires_confirmation)

    def test_read_only_lekarna_tools_do_not_require_confirmation(self) -> None:
        for capability_id in (
            "search_domaci_leky",
            "audit_domaci_lekarna",
            "preview_vyrazeni_leku",
            "validate_lekarna_photo_sources",
        ):
            with self.subTest(capability_id=capability_id):
                record = get_capability(capability_id)
                self.assertEqual(record.risk, RiskLevel.READ_ONLY)
                self.assertFalse(record.requires_confirmation)

    def test_read_only_reminder_and_media_previews_do_not_require_confirmation(self) -> None:
        for capability_id in (
            "list_open_reminders",
            "show_reminder_detail",
            "preview_zmenseni_obrazku",
        ):
            with self.subTest(capability_id=capability_id):
                record = get_capability(capability_id)
                self.assertEqual(record.risk, RiskLevel.READ_ONLY)
                self.assertFalse(record.requires_confirmation)

    def test_read_only_document_vault_tools_do_not_require_confirmation(self) -> None:
        for capability_id in (
            "scan_document_inbox",
            "scan_downloaded_pdfs",
            "preview_document_reindex",
            "scan_mobile_document_inbox",
            "document_vault_status",
            "search_private_documents",
            "prepare_restricted_bank_document_import",
        ):
            with self.subTest(capability_id=capability_id):
                record = get_capability(capability_id)
                self.assertEqual(record.risk, RiskLevel.READ_ONLY)
                self.assertFalse(record.requires_confirmation)

    def test_read_only_memory_and_report_capabilities_do_not_require_confirmation(self) -> None:
        for capability_id in (
            "search_memory",
            "memory_status",
            "samantha_health_check",
            "samantha_system_reports",
            "samantha_capability_audit",
            "family_calendar_delivery_readiness",
        ):
            with self.subTest(capability_id=capability_id):
                record = get_capability(capability_id)
                self.assertEqual(record.risk, RiskLevel.READ_ONLY)
                self.assertFalse(record.requires_confirmation)

    def test_read_only_email_headers_and_archive_summaries_do_not_require_confirmation(self) -> None:
        for capability_id in (
            "list_recent_email_headers",
            "search_email_headers",
            "list_recent_seznam_email_headers",
            "search_seznam_email_headers",
            "list_unified_email_headers",
            "show_new_email_overview",
            "list_email_archives",
            "show_email_archive_summary",
        ):
            with self.subTest(capability_id=capability_id):
                record = get_capability(capability_id)
                self.assertEqual(record.risk, RiskLevel.READ_ONLY)
                self.assertFalse(record.requires_confirmation)

    def test_read_only_action_previews_do_not_require_confirmation(self) -> None:
        for capability_id in (
            "prepare_document_import",
            "inspect_document_text",
            "prepare_mobile_document_final_import",
            "propose_document_inbox_cleanup",
        ):
            with self.subTest(capability_id=capability_id):
                record = get_capability(capability_id)
                self.assertEqual(record.risk, RiskLevel.READ_ONLY)
                self.assertFalse(record.requires_confirmation)

    def test_private_export_capabilities_are_strictly_confirmed(self) -> None:
        for capability_id in (
            "build_email_case_from_uid",
            "build_email_action_case_from_uid",
            "build_rixo_insurance_case_from_uids",
            "search_email_text_year",
            "search_seznam_email_text_year",
            "read_email_body_by_uid",
            "read_seznam_email_body_by_uid",
            "show_email_archive_links",
            "show_email_case_links",
            "inspect_payment_page_for_reminder",
        ):
            with self.subTest(capability_id=capability_id):
                record = get_capability(capability_id)
                self.assertEqual(record.risk, RiskLevel.PRIVATE_EXPORT)
                self.assertTrue(record.requires_confirmation)
                self.assertEqual(record.confirmation_policy, ConfirmationPolicy.EXACT_CURRENT_MESSAGE)

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
