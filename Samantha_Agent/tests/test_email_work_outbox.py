from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.email.work_outbox import process_email_work_audit_once, read_email_work_audit_count
from app.email.work_repository import EMAIL_WORK_DECISION_TOPIC, save_email_work_decision
from app.work_repository import JsonWorkRepository, OutboxEvent, RepositoryMutation


class EmailWorkOutboxTests(unittest.TestCase):
    def test_decision_produces_minimal_redacted_outbox_event(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "decisions.json"
            result = save_email_work_decision(
                path=path,
                item_id="private-item-id",
                action="ignore",
                item={"subject": "Private subject", "sender": "private@example.test"},
                operation_id="request-one",
            )

            record = JsonWorkRepository(path).pending_outbox()[0]
            self.assertEqual(record["topic"], EMAIL_WORK_DECISION_TOPIC)
            self.assertTrue(record["aggregate_id"].startswith("emailwork-"))
            self.assertNotIn("private-item-id", json.dumps(record))
            self.assertEqual(record["payload"], {"action": "ignore"})
            self.assertEqual(len(result.outbox_event_ids), 1)

    def test_consumer_records_safe_audit_and_acks_event(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            decisions_path = Path(temp_dir) / "decisions.json"
            audit_path = Path(temp_dir) / "audit.json"
            save_email_work_decision(
                path=decisions_path,
                item_id="raw-private-item-84217",
                action="ignore",
                item={"subject": "Not audited"},
                operation_id="request-one",
            )

            result = process_email_work_audit_once(
                decisions_path=decisions_path,
                audit_path=audit_path,
                now="2026-07-11T12:00:00+00:00",
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["status"], "audited")
            self.assertEqual(read_email_work_audit_count(audit_path), 1)
            self.assertEqual(JsonWorkRepository(decisions_path).pending_outbox(), [])
            audit_text = audit_path.read_text(encoding="utf-8")
            self.assertNotIn("Not audited", audit_text)
            self.assertNotIn("raw-private-item-84217", audit_text)

    def test_crash_after_audit_before_ack_replays_without_duplicate_audit(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            decisions_path = Path(temp_dir) / "decisions.json"
            audit_path = Path(temp_dir) / "audit.json"
            save_email_work_decision(
                path=decisions_path,
                item_id="one",
                action="ignore",
                operation_id="request-one",
            )

            with patch("app.work_repository.JsonWorkRepository.acknowledge_outbox", side_effect=RuntimeError("crash")):
                with self.assertRaises(RuntimeError):
                    process_email_work_audit_once(
                        decisions_path=decisions_path,
                        audit_path=audit_path,
                        now="2026-07-11T12:00:00+00:00",
                        lease_seconds=10,
                    )

            replay = process_email_work_audit_once(
                decisions_path=decisions_path,
                audit_path=audit_path,
                now="2026-07-11T12:00:10+00:00",
                lease_seconds=10,
            )
            self.assertTrue(replay["ok"])
            self.assertEqual(read_email_work_audit_count(audit_path), 1)

    def test_unsupported_event_is_retried_without_audit(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            decisions_path = Path(temp_dir) / "decisions.json"
            audit_path = Path(temp_dir) / "audit.json"
            JsonWorkRepository(decisions_path, default={"decisions": {}}).transact(
                lambda document: RepositoryMutation(
                    document=document,
                    outbox=(OutboxEvent("unsupported.topic", "emailwork-test", {"action": "ignore"}),),
                )
            )

            result = process_email_work_audit_once(
                decisions_path=decisions_path,
                audit_path=audit_path,
                now="2026-07-11T12:00:00+00:00",
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["status"], "retry_scheduled")
            self.assertEqual(read_email_work_audit_count(audit_path), 0)
            pending = JsonWorkRepository(decisions_path).pending_outbox()[0]
            self.assertEqual(pending["last_error_code"], "unsupported_topic")


if __name__ == "__main__":
    unittest.main()
