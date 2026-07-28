from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_search_pages_preserve_total_count_and_stable_order(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            records = [
                {
                    "document_id": f"doc-recept-{number:02d}",
                    "title": f"Recept {number:02d}",
                    "original_filename": f"recept-{number:02d}.pdf",
                    "stored_path": (
                        "data/private/documents/vault/recipes/"
                        f"doc-recept-{number:02d}/recept-{number:02d}.pdf"
                    ),
                    "domain": "recipes",
                    "document_type": "recipe",
                }
                for number in range(1, 7)
            ]
            (index / "documents_index.jsonl").write_text(
                "".join(
                    json.dumps(record, ensure_ascii=False) + "\n"
                    for record in reversed(records)
                ),
                encoding="utf-8",
            )
            (index / "text_index.jsonl").write_text("", encoding="utf-8")

            first = search_document_index(
                "recept",
                vault_dir=vault,
                limit=2,
                offset=0,
            )
            second = search_document_index(
                "recept",
                vault_dir=vault,
                limit=2,
                offset=2,
            )
            last = search_document_index(
                "recept",
                vault_dir=vault,
                limit=2,
                offset=4,
            )

        self.assertEqual(first["total_count"], 6)
        self.assertEqual(first["count"], 2)
        self.assertTrue(first["has_more"])
        self.assertEqual(first["next_offset"], 2)
        self.assertEqual(second["offset"], 2)
        self.assertEqual(second["next_offset"], 4)
        self.assertEqual(last["count"], 2)
        self.assertFalse(last["has_more"])
        self.assertIsNone(last["next_offset"])
        paged_ids = [
            row["document_id"]
            for page in (first, second, last)
            for row in page["results"]
        ]
        self.assertEqual(
            paged_ids,
            [f"doc-recept-{number:02d}" for number in range(1, 7)],
        )

    def test_document_only_page_does_not_read_purchase_archive(self) -> None:
        with patch(
            "app.documents.search_service.search_purchase_manifests"
        ) as purchase_search:
            result = search_document_index(
                "recept",
                vault_dir=Path("/private/tmp/missing-vault"),
                source_type="document",
                limit=20,
                offset=0,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["total_count"], 0)
        purchase_search.assert_not_called()


if __name__ == "__main__":
    unittest.main()
