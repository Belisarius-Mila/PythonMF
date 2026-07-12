from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from app.tvbcp import CURRENT_RULES, append_tvbcp_entry, start_tvbcp, tvbcp_status, update_tvbcp_contract


class TvbcpTests(unittest.TestCase):
    def test_start_append_and_read_full_substantive_protocol(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "TVBCP_current.txt"
            created = start_tvbcp(
                title="SOS aplikace",
                path=path,
                now=datetime(2026, 7, 12, 8, 0, tzinfo=timezone.utc),
            )
            appended = append_tvbcp_entry(
                mila="První odstavec Mílova návrhu.\n\nDruhý odstavec zůstane celý.",
                adam="Adamův plný věcný návrh bez testovacích mezistavů.",
                conclusion="Aplikace nenahrazuje krizovou službu.",
                path=path,
                now=datetime(2026, 7, 12, 8, 5, tzinfo=timezone.utc),
            )
            status = tvbcp_status(path)

        self.assertTrue(created["created"])
        self.assertTrue(appended["ok"])
        self.assertTrue(status["active"])
        self.assertIn(CURRENT_RULES, status["content"])
        self.assertIn("Míla – plné znění návrhu / myšlenky:", status["content"])
        self.assertIn("První odstavec Mílova návrhu.\n\nDruhý odstavec zůstane celý.", status["content"])
        self.assertIn("Adam – plné znění návrhu / myšlenky:", status["content"])

    def test_start_never_overwrites_existing_protocol(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "TVBCP_current.txt"
            start_tvbcp(title="První", path=path)
            result = start_tvbcp(title="Druhý", path=path)
            content = path.read_text(encoding="utf-8")

        self.assertFalse(result["created"])
        self.assertIn("Téma: První", content)
        self.assertNotIn("Téma: Druhý", content)

    def test_contract_upgrade_preserves_existing_entries(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "TVBCP_current.txt"
            start_tvbcp(title="SOS", path=path)
            content = path.read_text(encoding="utf-8").replace(CURRENT_RULES, (
                "- Jen stručné myšlenky, návrhy, závěry a otevřené otázky.\n"
                "- Neukládat plné přepisy, tajemství, osobní údaje ani citlivé krizové příběhy.\n"
                "- Nic se automaticky nemaže ani nepřesouvá. O osudu protokolu rozhodne Míla."
            )) + "\nPůvodní věcný záznam zůstává.\n"
            path.write_text(content, encoding="utf-8")

            result = update_tvbcp_contract(path)
            updated = path.read_text(encoding="utf-8")

        self.assertTrue(result["changed"])
        self.assertIn(CURRENT_RULES, updated)
        self.assertIn("Původní věcný záznam zůstává.", updated)

    def test_append_requires_active_protocol(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "missing.txt"
            with self.assertRaises(FileNotFoundError):
                append_tvbcp_entry(mila="Nápad", path=path)


if __name__ == "__main__":
    unittest.main()
