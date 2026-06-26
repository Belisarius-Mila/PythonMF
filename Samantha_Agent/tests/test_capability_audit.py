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
        self.assertIn("Capability registry records: 15", text)
        self.assertIn("High-risk capability records: 2", text)
        self.assertIn("Registry-covered agent tools: 12/", text)
        self.assertIn("Capability registry: OK", text)
        self.assertIn("Capability registry validation:\n- OK", text)
        self.assertIn("Priority missing capability records:", text)
        self.assertIn("- `restore_path_from_backup`", text)
        self.assertIn("Agent tools missing capability records:", text)
        self.assertIn("- `search_memory`", text)
        self.assertNotIn("- `send_prepared_email_draft`", text)
        self.assertNotIn("- `send_confirmed_sms_rcs`", text)
        self.assertNotIn("- `apply_document_import`", text)


if __name__ == "__main__":
    unittest.main()
