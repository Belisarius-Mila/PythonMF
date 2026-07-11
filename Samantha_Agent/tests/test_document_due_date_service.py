from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from app.documents.due_date_service import (
    annotate_due_candidate_groups,
    build_document_due_candidates,
    document_due_candidates_status,
    public_document_due_candidate,
)


class DocumentDueDateServiceTests(unittest.TestCase):
    @staticmethod
    def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )

    def test_document_candidate_is_ready_and_public_result_redacts_ids(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            reminders_path = root / "reminders.json"
            self.write_jsonl(
                vault / "index" / "documents_index.jsonl",
                [{
                    "document_id": "private-document-id",
                    "title": "Pojistné",
                    "domain": "insurance",
                    "document_type": "payment_notice",
                    "counterparty": "Pojišťovna",
                    "related_asset": "auto",
                }],
            )
            self.write_jsonl(vault / "index" / "text_index.jsonl", [])
            self.write_jsonl(
                vault / "index" / "due_dates.jsonl",
                [{
                    "document_id": "private-document-id",
                    "date": "2026-08-01",
                    "type": "payment_due",
                    "confidence": "high",
                    "context": "Uhradit 1 500 Kč do termínu.",
                    "create_reminder_candidate": True,
                }],
            )
            reminders_path.write_text('{"reminders": []}', encoding="utf-8")

            candidates = build_document_due_candidates(
                vault_dir=vault,
                reminders_path=reminders_path,
                today=date(2026, 7, 11),
            )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["status"], "ready")
        self.assertEqual(candidates[0]["amount_due"], "1 500 Kč")
        public = public_document_due_candidate(candidates[0])
        self.assertNotIn("document_id", public)
        self.assertNotIn("reminder_id", public)

    def test_existing_reminder_changes_candidate_to_already_reminded(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            reminders_path = root / "reminders.json"
            self.write_jsonl(
                vault / "index" / "documents_index.jsonl",
                [{"document_id": "doc-1", "title": "Termín"}],
            )
            self.write_jsonl(vault / "index" / "text_index.jsonl", [])
            self.write_jsonl(
                vault / "index" / "due_dates.jsonl",
                [{
                    "document_id": "doc-1",
                    "date": "2026-08-01",
                    "type": "deadline",
                    "create_reminder_candidate": True,
                }],
            )
            reminders_path.write_text(json.dumps({"reminders": [{
                "id": "document-doc-1-deadline-2026-08-01",
                "status": "open",
            }]}), encoding="utf-8")

            result = document_due_candidates_status(
                vault_dir=vault,
                reminders_path=reminders_path,
                archive_directory=None,
                today=date(2026, 7, 11),
            )

        self.assertEqual(result["already_reminded_count"], 1)
        self.assertEqual(result["actionable_count"], 0)

    def test_same_email_and_attachment_are_related_not_duplicates(self) -> None:
        candidates = [
            {
                "candidate_ref": "email",
                "source_kind": "email_archive",
                "archive_id": "email-icloud-12345",
                "counterparty": "Dodavatel",
                "type": "payment_due",
                "date": "2026-08-01",
            },
            {
                "candidate_ref": "document",
                "source_kind": "document",
                "case_id": "icloud_uid_12345_attachment",
                "counterparty": "Dodavatel",
                "type": "payment_due",
                "date": "2026-08-01",
            },
        ]

        groups = annotate_due_candidate_groups(candidates)

        self.assertEqual(len(groups["related_sources"]), 1)
        self.assertEqual(groups["duplicates"], [])
        self.assertTrue(all(item.get("related_source_group_id") for item in candidates))

    def test_stale_past_due_candidate_is_hidden_from_action_list(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            reminders_path = root / "reminders.json"
            self.write_jsonl(vault / "index" / "documents_index.jsonl", [{"document_id": "old", "title": "Starý"}])
            self.write_jsonl(vault / "index" / "text_index.jsonl", [])
            self.write_jsonl(vault / "index" / "due_dates.jsonl", [{
                "document_id": "old",
                "date": "2025-01-01",
                "type": "deadline",
                "create_reminder_candidate": True,
            }])
            reminders_path.write_text('{"reminders": []}', encoding="utf-8")

            result = document_due_candidates_status(
                vault_dir=vault,
                reminders_path=reminders_path,
                archive_directory=None,
                today=date(2026, 7, 11),
                stale_past_due_days=90,
            )

        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(result["stale_past_due_count"], 1)
        self.assertEqual(result["items"], [])


if __name__ == "__main__":
    unittest.main()
