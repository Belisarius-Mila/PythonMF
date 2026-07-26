from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.codex_approval_state import (
    clear_codex_approval_request,
    load_codex_approval_request,
    save_codex_approval_request,
)


class CodexApprovalStateTests(unittest.TestCase):
    def test_missing_state_is_inactive(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            result = load_codex_approval_request(path=Path(temp_dir) / "missing.json")

        self.assertTrue(result["ok"])
        self.assertFalse(result["available"])
        self.assertFalse(result["active"])
        self.assertEqual(result["status"], "none")

    def test_request_roundtrip_and_clear_preserve_contract(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "codex_approval_request.json"
            saved = save_codex_approval_request(
                reason="Codex potřebuje povolit kontrolu procesu.",
                command="read-only process check",
                risk="Read-only systémová kontrola běžících procesů.",
                next_step="Otevři Human–Adam a rozhodni systémové potvrzení.",
                confirmation_text="Potvrzuji bezpečnou kontrolu procesu.",
                path=path,
            )
            loaded = load_codex_approval_request(path=path)
            cleared = clear_codex_approval_request(note="Vyřešeno.", path=path)

        self.assertTrue(saved["active"])
        self.assertEqual(loaded["status"], "waiting_for_codex_approval")
        self.assertEqual(loaded["confirmation_text"], "Potvrzuji bezpečnou kontrolu procesu.")
        self.assertFalse(cleared["active"])
        self.assertEqual(cleared["status"], "cleared")
        self.assertTrue(cleared["previous"]["active"])

    def test_invalid_state_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "codex_approval_request.json"
            path.write_text("{", encoding="utf-8")

            result = load_codex_approval_request(path=path)

        self.assertFalse(result["ok"])
        self.assertFalse(result["available"])
        self.assertFalse(result["active"])
        self.assertEqual(result["status"], "error")

    def test_saved_payload_remains_json_compatible(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "codex_approval_request.json"
            saved = save_codex_approval_request(reason="Test", path=path)

            stored = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(stored, saved)


if __name__ == "__main__":
    unittest.main()
