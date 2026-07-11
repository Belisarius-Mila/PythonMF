from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.work_repository import JsonWorkRepository, OutboxEvent, RepositoryMutation


class WorkRepositoryTests(unittest.TestCase):
    def test_mutation_and_outbox_are_committed_together(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "work.json"
            repository = JsonWorkRepository(path, default={"records": {}})

            result = repository.transact(
                lambda document: RepositoryMutation(
                    document={**document, "records": {"one": {"state": "queued"}}},
                    result={"record_id": "one"},
                    outbox=(OutboxEvent("work.queued", "one", {"safe": True}),),
                ),
                operation_id="operation-one",
            )

            stored = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(result.changed)
            self.assertEqual(stored["records"]["one"]["state"], "queued")
            self.assertEqual(len(repository.pending_outbox()), 1)
            self.assertEqual(result.outbox_event_ids, (stored["_repository"]["outbox"][0]["event_id"],))

    def test_operation_replay_does_not_run_updater_or_duplicate_outbox(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "work.json"
            repository = JsonWorkRepository(path)
            calls = 0

            def update(document: dict[str, object]) -> RepositoryMutation:
                nonlocal calls
                calls += 1
                return RepositoryMutation(
                    document={**document, "value": calls},
                    result={"value": calls},
                    outbox=(OutboxEvent("work.changed", "one"),),
                )

            first = repository.transact(update, operation_id="same-operation")
            second = repository.transact(update, operation_id="same-operation")

            self.assertEqual(calls, 1)
            self.assertTrue(first.changed)
            self.assertTrue(second.idempotent_replay)
            self.assertEqual(second.result, {"value": 1})
            self.assertEqual(second.outbox_event_ids, first.outbox_event_ids)
            self.assertEqual(len(repository.pending_outbox()), 1)

    def test_domain_updater_cannot_drop_existing_repository_ledger(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "work.json"
            repository = JsonWorkRepository(path)
            first = repository.transact(
                lambda _document: RepositoryMutation(
                    document={"value": 1},
                    outbox=(OutboxEvent("work.changed", "one"),),
                ),
                operation_id="first",
            )

            repository.transact(
                lambda _document: RepositoryMutation(document={"value": 2}),
                operation_id="second",
            )

            stored = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(len(stored["_repository"]["idempotency"]), 2)
            self.assertEqual(stored["_repository"]["outbox"][0]["event_id"], first.outbox_event_ids[0])

    def test_failed_replace_keeps_original_document_without_outbox(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "work.json"
            path.write_text('{"safe": "original"}\n', encoding="utf-8")
            repository = JsonWorkRepository(path)

            with patch("app.work_repository.atomic_replace_text_under_external_lock", side_effect=OSError("failed")):
                with self.assertRaises(OSError):
                    repository.transact(
                        lambda document: RepositoryMutation(
                            document={**document, "safe": "changed"},
                            outbox=(OutboxEvent("work.changed", "one"),),
                        )
                    )

            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"safe": "original"})


if __name__ == "__main__":
    unittest.main()
