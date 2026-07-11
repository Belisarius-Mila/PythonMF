from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.documents.search_service import (
    document_search_intent_bonus,
    document_search_query_intent,
    search_document_index,
)


class DocumentSearchServiceTests(unittest.TestCase):
    def test_empty_query_is_rejected_without_reading_indexes(self) -> None:
        result = search_document_index(" ", vault_dir=Path("/private/tmp/missing-vault"))

        self.assertFalse(result["ok"])
        self.assertEqual(result["results"], [])

    def test_invoice_intent_prioritizes_invoice_and_penalizes_quote(self) -> None:
        intent = document_search_query_intent("faktura dodavatel PDF", ["faktura", "dodavatel", "pdf"])
        terms = {"faktura", "dodavatel", "pdf"}

        invoice_bonus = document_search_intent_bonus(
            {"document_type": "invoice", "original_filename": "doklad.pdf"}, intent, terms
        )
        quote_bonus = document_search_intent_bonus(
            {"document_type": "quote", "original_filename": "nabidka.pdf"}, intent, terms
        )

        self.assertGreater(invoice_bonus, quote_bonus)

    def test_metadata_match_returns_redacted_structured_result(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            record = {
                "document_id": "doc-test",
                "title": "Servis fotovoltaika",
                "original_filename": "servis.pdf",
                "stored_path": "data/private/documents/vault/energy/doc-test/servis.pdf",
                "domain": "energy",
                "document_type": "service_protocol",
            }
            (index / "documents_index.jsonl").write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
            (index / "text_index.jsonl").write_text("", encoding="utf-8")

            result = search_document_index("fotovoltaika", vault_dir=vault)

        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["source_type"], "document")
        self.assertEqual(result["results"][0]["reading_status"], "needs_review")


if __name__ == "__main__":
    unittest.main()
