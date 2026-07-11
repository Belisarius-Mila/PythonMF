from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from app.documents.case_service import (
    DocumentCaseDependencies,
    document_case_detail_status,
    document_case_health_status,
    document_cases_status,
)


class DocumentCaseServiceTests(unittest.TestCase):
    @staticmethod
    def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )

    def test_overview_groups_only_real_multi_document_cases(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            self.write_jsonl(
                vault / "index" / "documents_index.jsonl",
                [
                    {"document_id": "auto-1", "title": "Smlouva", "domain": "insurance", "related_asset": "Volvo"},
                    {"document_id": "auto-2", "title": "Platba", "domain": "insurance", "related_asset": "Volvo"},
                    {"document_id": "single", "title": "Jediný", "counterparty": "Dodavatel"},
                    {"document_id": "trash", "title": "Koš", "related_asset": "Volvo", "lifecycle_status": "trashed"},
                ],
            )

            result = document_cases_status(vault_dir=vault)

        self.assertTrue(result["ok"])
        self.assertEqual(result["active_documents"], 3)
        self.assertEqual(result["case_count"], 1)
        self.assertEqual(result["singletons_count"], 1)
        self.assertEqual(result["cases"][0]["label"], "Volvo")
        self.assertNotIn("auto-1", json.dumps(result, ensure_ascii=False))

    def test_detail_uses_dependencies_and_redacts_internal_ids(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            reminders_path = root / "reminders.json"
            self.write_jsonl(
                vault / "index" / "documents_index.jsonl",
                [
                    {"document_id": "secret-doc-1", "title": "A", "related_asset": "auto", "reading_status": "ok"},
                    {"document_id": "secret-doc-2", "title": "B", "related_asset": "auto", "reading_status": "ok"},
                ],
            )
            reminders_path.write_text(
                json.dumps({"reminders": [{
                    "id": "secret-reminder",
                    "title": "Hlídání",
                    "status": "open",
                    "due_date": "2026-08-01",
                    "related_asset": "AUTO",
                    "source": {"type": "private_document", "uid": "secret-doc-1"},
                }]}, ensure_ascii=False),
                encoding="utf-8",
            )
            overview = document_cases_status(vault_dir=vault)
            dependencies = DocumentCaseDependencies(
                due_candidates=lambda **_kwargs: [{
                    "document_id": "secret-doc-1",
                    "case_id": "secret-case",
                    "reminder_id": "secret-reminder",
                    "status": "already_reminded",
                    "title": "Termín",
                }],
                reminder_conflicts=lambda _items: [],
                stored_pdf_is_openable=lambda _path, _vault: False,
            )

            result = document_case_detail_status(
                overview["cases"][0]["case_ref"],
                dependencies=dependencies,
                vault_dir=vault,
                reminders_path=reminders_path,
                today=date(2026, 7, 11),
            )

        serialized = json.dumps(result, ensure_ascii=False)
        self.assertTrue(result["ok"])
        self.assertEqual(result["case_health"]["status"], "ok")
        self.assertEqual(result["case_health"]["open_reminder_count"], 1)
        self.assertNotIn("secret-doc", serialized)
        self.assertNotIn("secret-reminder", serialized)
        self.assertNotIn('"id"', serialized)

    def test_health_prioritizes_conflict_over_other_signals(self) -> None:
        result = document_case_health_status(
            documents=[{"reading_status": "needs_review"}],
            reminders=[{"title": "Hlídání"}],
            due_candidates=[{"status": "ready"}],
            conflicts=[{"severity": "high"}],
        )

        self.assertEqual(result["status"], "bad")
        self.assertEqual(result["conflict_count"], 1)
        self.assertEqual(result["review_document_count"], 1)


if __name__ == "__main__":
    unittest.main()
