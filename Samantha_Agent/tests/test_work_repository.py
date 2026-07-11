from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.work_repository import JsonWorkRepository, OutboxEvent, RepositoryMutation


PROJECT_ROOT = Path(__file__).resolve().parents[1]


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

    def test_lease_and_ack_require_current_fencing_token(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "work.json"
            repository = JsonWorkRepository(path)
            created = repository.transact(
                lambda document: RepositoryMutation(
                    document=document,
                    outbox=(OutboxEvent("work.ready", "one"),),
                ),
                operation_id="create-one",
            )

            leases = repository.lease_outbox(
                lease_owner="worker-a",
                lease_seconds=30,
                now="2026-07-11T12:00:00+00:00",
            )

            self.assertEqual(len(leases), 1)
            self.assertEqual(leases[0].event_id, created.outbox_event_ids[0])
            self.assertEqual(leases[0].attempts, 1)
            self.assertFalse(repository.acknowledge_outbox(
                event_id=leases[0].event_id,
                lease_token="stale-token",
                now="2026-07-11T12:00:10+00:00",
            ))
            self.assertTrue(repository.acknowledge_outbox(
                event_id=leases[0].event_id,
                lease_token=leases[0].lease_token,
                now="2026-07-11T12:00:10+00:00",
            ))
            self.assertTrue(repository.acknowledge_outbox(
                event_id=leases[0].event_id,
                lease_token=leases[0].lease_token,
                now="2026-07-11T12:00:11+00:00",
            ))
            self.assertEqual(repository.pending_outbox(), [])
            stored = json.loads(path.read_text(encoding="utf-8"))["_repository"]["outbox"][0]
            self.assertEqual(stored["status"], "delivered")
            self.assertNotIn("lease_token", stored)

    def test_retry_is_delayed_and_increments_attempt_on_next_lease(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            repository = JsonWorkRepository(Path(temp_dir) / "work.json")
            repository.transact(
                lambda document: RepositoryMutation(
                    document=document,
                    outbox=(OutboxEvent("work.ready", "one"),),
                )
            )
            first = repository.lease_outbox(
                lease_owner="worker-a", now="2026-07-11T12:00:00+00:00"
            )[0]

            self.assertTrue(repository.retry_outbox(
                event_id=first.event_id,
                lease_token=first.lease_token,
                retry_after_seconds=60,
                error_code="temporary_failure",
                now="2026-07-11T12:00:10+00:00",
            ))
            self.assertTrue(repository.retry_outbox(
                event_id=first.event_id,
                lease_token=first.lease_token,
                retry_after_seconds=60,
                error_code="temporary_failure",
                now="2026-07-11T12:00:11+00:00",
            ))
            self.assertEqual(repository.lease_outbox(
                lease_owner="worker-b", now="2026-07-11T12:01:09+00:00"
            ), [])
            second = repository.lease_outbox(
                lease_owner="worker-b", now="2026-07-11T12:01:10+00:00"
            )[0]
            self.assertEqual(second.attempts, 2)
            self.assertNotEqual(first.lease_token, second.lease_token)

    def test_expired_lease_is_reclaimed_and_stale_ack_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            repository = JsonWorkRepository(Path(temp_dir) / "work.json")
            repository.transact(
                lambda document: RepositoryMutation(
                    document=document,
                    outbox=(OutboxEvent("work.ready", "one"),),
                )
            )
            first = repository.lease_outbox(
                lease_owner="worker-a",
                lease_seconds=10,
                now="2026-07-11T12:00:00+00:00",
            )[0]
            second = repository.lease_outbox(
                lease_owner="worker-b",
                lease_seconds=10,
                now="2026-07-11T12:00:10+00:00",
            )[0]

            self.assertEqual(second.attempts, 2)
            self.assertFalse(repository.acknowledge_outbox(
                event_id=first.event_id,
                lease_token=first.lease_token,
                now="2026-07-11T12:00:11+00:00",
            ))
            self.assertFalse(repository.retry_outbox(
                event_id=first.event_id,
                lease_token=first.lease_token,
                retry_after_seconds=5,
                now="2026-07-11T12:00:11+00:00",
            ))
            self.assertTrue(repository.acknowledge_outbox(
                event_id=second.event_id,
                lease_token=second.lease_token,
                now="2026-07-11T12:00:11+00:00",
            ))

    def test_two_processes_cannot_lease_same_event(self) -> None:
        script = """
import sys
from pathlib import Path
from app.work_repository import JsonWorkRepository

leases = JsonWorkRepository(Path(sys.argv[1])).lease_outbox(
    lease_owner=sys.argv[2],
    lease_seconds=60,
    now="2026-07-11T12:00:00+00:00",
)
print(len(leases))
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "work.json"
            JsonWorkRepository(path).transact(
                lambda document: RepositoryMutation(
                    document=document,
                    outbox=(OutboxEvent("work.ready", "one"),),
                )
            )
            processes = [
                subprocess.Popen(
                    [sys.executable, "-c", script, str(path), owner],
                    cwd=PROJECT_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for owner in ("worker-a", "worker-b")
            ]
            outputs = [process.communicate(timeout=20) for process in processes]

            for process, (_stdout, stderr) in zip(processes, outputs, strict=True):
                self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(sorted(stdout.strip() for stdout, _stderr in outputs), ["0", "1"])

    def test_failed_lease_replace_keeps_event_pending(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "work.json"
            repository = JsonWorkRepository(path)
            repository.transact(
                lambda document: RepositoryMutation(
                    document=document,
                    outbox=(OutboxEvent("work.ready", "one"),),
                )
            )

            with patch("app.work_repository.atomic_replace_text_under_external_lock", side_effect=OSError("failed")):
                with self.assertRaises(OSError):
                    repository.lease_outbox(
                        lease_owner="worker-a",
                        now="2026-07-11T12:00:00+00:00",
                    )

            stored = json.loads(path.read_text(encoding="utf-8"))["_repository"]["outbox"][0]
            self.assertEqual(stored["status"], "pending")
            self.assertNotIn("lease_token", stored)

    def test_failed_ack_replace_keeps_current_lease(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "work.json"
            repository = JsonWorkRepository(path)
            repository.transact(
                lambda document: RepositoryMutation(
                    document=document,
                    outbox=(OutboxEvent("work.ready", "one"),),
                )
            )
            lease = repository.lease_outbox(
                lease_owner="worker-a",
                now="2026-07-11T12:00:00+00:00",
            )[0]

            with patch("app.work_repository.atomic_replace_text_under_external_lock", side_effect=OSError("failed")):
                with self.assertRaises(OSError):
                    repository.acknowledge_outbox(
                        event_id=lease.event_id,
                        lease_token=lease.lease_token,
                        now="2026-07-11T12:00:10+00:00",
                    )

            stored = json.loads(path.read_text(encoding="utf-8"))["_repository"]["outbox"][0]
            self.assertEqual(stored["status"], "leased")
            self.assertEqual(stored["lease_token"], lease.lease_token)


if __name__ == "__main__":
    unittest.main()
