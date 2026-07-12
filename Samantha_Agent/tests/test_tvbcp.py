from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from app.tvbcp import TVBCP_PAGE_HTML, append_tvbcp_entry, start_tvbcp, tvbcp_status


class TvbcpTests(unittest.TestCase):
    def test_start_append_and_read_structured_private_protocol(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "TVBCP_current.txt"
            created = start_tvbcp(
                title="SOS aplikace",
                path=path,
                now=datetime(2026, 7, 12, 8, 0, tzinfo=timezone.utc),
            )
            appended = append_tvbcp_entry(
                discussed="Bezpečný první kontakt.",
                conclusion="Aplikace nenahrazuje krizovou službu.",
                next_step="Najít původní Quick Note.",
                path=path,
                now=datetime(2026, 7, 12, 8, 5, tzinfo=timezone.utc),
            )
            status = tvbcp_status(path)

        self.assertTrue(created["created"])
        self.assertTrue(appended["ok"])
        self.assertTrue(status["active"])
        self.assertIn("Téma: SOS aplikace", status["content"])
        self.assertIn("O čem jsme mluvili: Bezpečný první kontakt.", status["content"])
        self.assertIn("K čemu jsme došli: Aplikace nenahrazuje krizovou službu.", status["content"])

    def test_start_never_overwrites_existing_protocol(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "TVBCP_current.txt"
            start_tvbcp(title="První", path=path)
            result = start_tvbcp(title="Druhý", path=path)
            content = path.read_text(encoding="utf-8")

        self.assertFalse(result["created"])
        self.assertIn("Téma: První", content)
        self.assertNotIn("Téma: Druhý", content)

    def test_append_requires_active_protocol(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "missing.txt"
            with self.assertRaises(FileNotFoundError):
                append_tvbcp_entry(discussed="Nápad", path=path)

    def test_reader_renders_protocol_as_text_and_has_safe_return(self) -> None:
        self.assertIn('contentNode.textContent = data.content', TVBCP_PAGE_HTML)
        self.assertNotIn('contentNode.innerHTML = data.content', TVBCP_PAGE_HTML)
        self.assertIn('window.location.href = "/"', TVBCP_PAGE_HTML)
        self.assertIn('fetch("/api/voice-bridge/tvbcp"', TVBCP_PAGE_HTML)


if __name__ == "__main__":
    unittest.main()
