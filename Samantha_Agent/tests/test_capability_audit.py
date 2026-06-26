from __future__ import annotations

import unittest

from app.capability_audit import format_samantha_capability_audit


class CapabilityAuditTests(unittest.TestCase):
    def test_capability_audit_reports_mapped_tools_and_workflow_count(self) -> None:
        text = format_samantha_capability_audit()

        self.assertIn("Samantha Capability Audit", text)
        self.assertIn("Agent tools:", text)
        self.assertIn("Registered shell workflows:", text)
        self.assertIn("Memory and system reports", text)
        self.assertIn("Document vault", text)
        self.assertIn("No unmapped agent tools.", text)
        self.assertIn("Capability registry records: 42", text)
        self.assertIn("High-risk capability records: 11", text)
        self.assertIn("Registry-covered agent tools: 39/", text)
        self.assertIn("Capability registry: OK", text)
        self.assertIn("Critical/action-write missing records: 0", text)
        self.assertIn("Action/review missing records: 0", text)
        self.assertIn("Read-only or low-risk missing records: 42", text)
        self.assertIn("Capability registry validation:\n- OK", text)
        self.assertIn("Missing capability records by risk tier:", text)
        self.assertIn("- Critical/action-write: 0", text)
        self.assertIn("- Action/review: 0", text)
        self.assertIn("- Read-only or low-risk: 42", text)
        self.assertIn("Priority missing capability records:", text)
        self.assertIn("- None.", text)
        self.assertIn("Action/review missing capability records:", text)
        self.assertIn("Action/review missing capability records:\n- None.", text)
        self.assertIn("Read-only or low-risk missing capability records:", text)
        self.assertIn("Agent tools missing capability records:", text)
        self.assertIn("- `search_memory`", text)
        self.assertNotIn("- `prepare_iphone_shortcut`", text)
        self.assertNotIn("- `build_email_case_from_uid`", text)
        self.assertNotIn("- `build_email_action_case_from_uid`", text)
        self.assertNotIn("- `inspect_payment_page_for_reminder`", text)
        self.assertNotIn("- `prepare_document_import`", text)
        self.assertNotIn("- `prepare_document_print_job`", text)
        self.assertNotIn("- `prepare_lekarna_photo_import`", text)
        self.assertNotIn("- `copy_downloads_files_to_knowledge_inbox`", text)
        self.assertNotIn("- `run_email_triage_session`", text)
        self.assertNotIn("- `run_unified_email_triage_session`", text)
        self.assertNotIn("- `send_prepared_email_draft`", text)
        self.assertNotIn("- `send_confirmed_sms_rcs`", text)
        self.assertNotIn("- `restore_path_from_backup`", text)
        self.assertNotIn("- `run_workflow_command`", text)
        self.assertNotIn("- `apply_vyrazeni_leku`", text)
        self.assertNotIn("- `apply_zmenseni_obrazku`", text)
        self.assertNotIn("- `apply_lekarna_photo_import`", text)
        self.assertNotIn("- `apply_document_import`", text)
        self.assertNotIn("- `run_document_print_job`", text)


if __name__ == "__main__":
    unittest.main()
