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


if __name__ == "__main__":
    unittest.main()
