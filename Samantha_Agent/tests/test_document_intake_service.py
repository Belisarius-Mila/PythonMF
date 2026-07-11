from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.documents.intake_service import (
    document_intake_status,
    document_intake_unified_items,
    local_document_inbox_source,
    mobile_document_intake_source,
)


class DocumentIntakeServiceTests(unittest.TestCase):
    def test_status_combines_four_sources_without_payload_content(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            local = vault / "inbox" / "incoming"
            mobile = root / "mobile"
            local.mkdir(parents=True)
            mobile.mkdir(parents=True)
            (local / "local.pdf").write_bytes(b"pdf")
            (mobile / "scan_A_manifest.json").write_text(
                json.dumps({"batch_id": "scan_A", "document_title": "Mobilní scan", "page_count": 1}),
                encoding="utf-8",
            )
            (mobile / "scan_A_page_001.jpg").write_bytes(b"image")
            downloads = {"items": [{"name": "download.pdf", "status": "new", "modified_at": "2026-07-11"}]}
            email_pending = {"items": [{
                "action": "process",
                "subject": "Doklad",
                "provider": "icloud",
                "folder": "INBOX",
                "date": "2026-07-11",
            }]}

            result = document_intake_status(
                downloads,
                email_pending,
                mobile_inbox_dir=mobile,
                vault_dir=vault,
            )

        self.assertEqual(result["count"], 4)
        self.assertEqual([source["id"] for source in result["sources"]], ["downloads", "email", "mobile", "local_inbox"])
        self.assertEqual(len(result["unified_items"]), 4)
        refs = [item["intake_ref"] for item in result["unified_items"]]
        self.assertEqual(len(set(refs)), 4)
        self.assertTrue(all(ref.startswith("intakeref-") for ref in refs))
        self.assertNotIn("image", json.dumps(result, ensure_ascii=False))

    def test_missing_mobile_and_local_sources_are_reported_readonly(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)

            mobile = mobile_document_intake_source(mobile_inbox_dir=root / "missing-mobile")
            local = local_document_inbox_source(vault_dir=root / "missing-vault")

        self.assertEqual(mobile["status"], "missing")
        self.assertEqual(local["status"], "missing")
        self.assertEqual(mobile["count"], 0)
        self.assertEqual(local["count"], 0)

    def test_unified_items_keep_source_priority_and_actions(self) -> None:
        sources = [
            {"id": "mobile", "label": "Mobil", "status": "ready", "next_action": "Ruční", "items": [{"title": "M"}]},
            {"id": "email", "label": "E-mail", "status": "ready", "next_action": "E", "items": [{"title": "E"}]},
            {"id": "downloads", "label": "Downloads", "status": "ready", "next_action": "D", "items": [{"title": "D"}]},
        ]

        result = document_intake_unified_items(sources=sources)

        self.assertEqual([item["source_id"] for item in result], ["downloads", "email", "mobile"])
        self.assertEqual(result[0]["action_kind"], "open_scandocu")
        self.assertEqual(result[1]["action_kind"], "open_email_processing")
        self.assertEqual(result[2]["action_kind"], "manual")


if __name__ == "__main__":
    unittest.main()
