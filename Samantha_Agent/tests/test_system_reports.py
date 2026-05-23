from __future__ import annotations

import unittest

from app.system_reports import SYSTEM_REPORTS, format_system_reports_overview


class SystemReportsTests(unittest.TestCase):
    def test_system_reports_overview_lists_current_reports(self) -> None:
        text = format_system_reports_overview()

        self.assertIn("Samantha System Reports", text)
        self.assertIn("Health check", text)
        self.assertIn("Kvantitativni status", text)
        self.assertIn("Capability audit", text)
        self.assertIn("Knowledge inbox inventory", text)
        self.assertIn("Downloads inventory", text)
        self.assertIn("iPhone shortcuts status", text)
        self.assertIn("Memory status", text)
        self.assertIn("samantha_health_check", text)
        self.assertIn("samantha_quantitative_status", text)
        self.assertIn("samantha_capability_audit", text)
        self.assertIn("samantha_knowledge_inbox_inventory", text)
        self.assertIn("samantha_downloads_inventory", text)
        self.assertIn("iphone_shortcuts_playground_status", text)

    def test_system_reports_registry_has_unique_names(self) -> None:
        names = [report.name for report in SYSTEM_REPORTS]

        self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
