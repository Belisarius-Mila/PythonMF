from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.documents.review_service import (
    document_classification_status,
    document_review_report_status,
    document_work_status,
    stored_documents_review_status,
)


class DocumentReviewServiceTests(unittest.TestCase):
    @staticmethod
    def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )

    def test_classification_reports_weak_metadata_without_internal_id(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            self.write_jsonl(
                vault / "index" / "documents_index.jsonl",
                [{
                    "document_id": "private-document-id",
                    "title": "Nezařazený dokument",
                    "domain": "other",
                    "document_type": "document",
                    "counterparty": "",
                    "related_asset": "",
                }],
            )
            self.write_jsonl(vault / "index" / "text_index.jsonl", [])

            result = document_classification_status(vault_dir=vault)

        self.assertEqual(result["issue_count"], 1)
        self.assertEqual(result["quality_percent"], 0)
        self.assertEqual(len(result["items"][0]["missing_fields"]), 4)
        self.assertNotIn("private-document-id", json.dumps(result, ensure_ascii=False))

    def test_stored_review_ignores_archived_documents(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            self.write_jsonl(
                vault / "index" / "documents_index.jsonl",
                [
                    {"document_id": "active", "title": "Aktivní"},
                    {"document_id": "archive", "title": "Archiv", "lifecycle_status": "archived"},
                ],
            )
            self.write_jsonl(vault / "index" / "text_index.jsonl", [])

            result = stored_documents_review_status(vault_dir=vault)

        self.assertEqual(result["pending_count"], 1)
        self.assertEqual(result["next_items"][0]["title"], "Aktivní")

    def test_review_report_separates_reading_and_metadata_reasons(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            self.write_jsonl(
                vault / "index" / "documents_index.jsonl",
                [{
                    "document_id": "needs-review",
                    "title": "Kontrola",
                    "domain": "other",
                    "document_type": "document",
                    "text_extraction": {"ocr_needed": True},
                }],
            )
            self.write_jsonl(vault / "index" / "text_index.jsonl", [])

            result = document_review_report_status(vault_dir=vault)

        self.assertEqual(result["summary"]["candidate_count"], 1)
        self.assertEqual(result["items"][0]["decision_group"], "zero_text")
        reason_ids = {item["id"] for item in result["items"][0]["reasons"]}
        self.assertTrue({"needs_review", "zero_text", "ocr_needed", "weak_metadata"}.issubset(reason_ids))

    def test_work_status_combines_download_and_review_counts(self) -> None:
        downloads = {
            "items": [
                {"name": "novy.pdf", "status": "new"},
                {"name": "heslo.pdf", "status": "new", "is_encrypted": True},
                {"name": "hotovo.pdf", "status": "imported"},
            ]
        }

        result = document_work_status(
            downloads,
            review_status_loader=lambda **_kwargs: {"pending_count": 2},
        )

        self.assertEqual(result["summary"]["new_pdf_count"], 2)
        self.assertEqual(result["summary"]["problem_count"], 1)
        self.assertEqual(result["summary"]["review_pending_count"], 2)
        self.assertEqual(result["problems"][0]["problem_kind"], "encrypted")


if __name__ == "__main__":
    unittest.main()
