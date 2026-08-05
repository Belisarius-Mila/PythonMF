from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from app.communication.human_adam_completion_status import (
    ATTENTION_REQUIRED,
    CHECKPOINT_COMPLETED,
    RECEIPT_ACCEPTED,
    HumanAdamCompletionStatusError,
    HumanAdamCompletionStatusStore,
    completion_status_model_block,
    public_completion_status,
)


WORKSTREAM_ID = "project-knowledge-library"
CLIENT_MESSAGE_ID = "completion-status-test-001"
BASE_HEAD = "a" * 40
CHECKPOINT_HEAD = "b" * 40


def clean_workspace(*, source_head: str = CHECKPOINT_HEAD) -> dict[str, object]:
    return {
        "ok": True,
        "prepared": True,
        "dirty": False,
        "source_pending_changes": 0,
        "workspace_relation": "aligned",
        "source_head": source_head,
    }


class HumanAdamCompletionStatusStoreTests(unittest.TestCase):
    def test_completed_record_is_private_and_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "completion.json"
            store = HumanAdamCompletionStatusStore(path)
            store.begin(
                workstream_id=WORKSTREAM_ID,
                client_message_id=CLIENT_MESSAGE_ID,
                base_head=BASE_HEAD,
                now_factory=lambda: "2026-08-05T10:00:00+00:00",
            )
            accepted = store.update(
                workstream_id=WORKSTREAM_ID,
                client_message_id=CLIENT_MESSAGE_ID,
                state=RECEIPT_ACCEPTED,
                now_factory=lambda: "2026-08-05T10:01:00+00:00",
            )
            completed = store.update(
                workstream_id=WORKSTREAM_ID,
                client_message_id=CLIENT_MESSAGE_ID,
                state=CHECKPOINT_COMPLETED,
                checkpoint_head=CHECKPOINT_HEAD,
                answer_persisted=True,
                remote_push_deferred=True,
                pending_remote_commit_count=5,
                now_factory=lambda: "2026-08-05T10:02:00+00:00",
            )

            loaded = store.load(workstream_id=WORKSTREAM_ID)

            self.assertEqual(accepted.state, RECEIPT_ACCEPTED)
            self.assertEqual(loaded, completed)
            self.assertEqual(loaded.checkpoint_head, CHECKPOINT_HEAD)
            self.assertEqual(loaded.pending_remote_commit_count, 5)
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertNotIn("summary", json.dumps(payload))
            self.assertNotIn("visible_answer", json.dumps(payload))
            self.assertNotIn("chat_text", json.dumps(payload))

    def test_same_message_begin_does_not_erase_completed_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = HumanAdamCompletionStatusStore(
                Path(temp_dir) / "completion.json"
            )
            store.begin(
                workstream_id=WORKSTREAM_ID,
                client_message_id=CLIENT_MESSAGE_ID,
                base_head=BASE_HEAD,
            )
            completed = store.update(
                workstream_id=WORKSTREAM_ID,
                client_message_id=CLIENT_MESSAGE_ID,
                state=CHECKPOINT_COMPLETED,
                checkpoint_head=CHECKPOINT_HEAD,
            )

            duplicate = store.begin(
                workstream_id=WORKSTREAM_ID,
                client_message_id=CLIENT_MESSAGE_ID,
                base_head=BASE_HEAD,
            )

            self.assertEqual(duplicate, completed)

    def test_new_turn_cannot_overwrite_unfinished_server_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = HumanAdamCompletionStatusStore(
                Path(temp_dir) / "completion.json"
            )
            store.begin(
                workstream_id=WORKSTREAM_ID,
                client_message_id=CLIENT_MESSAGE_ID,
                base_head=BASE_HEAD,
            )

            with self.assertRaisesRegex(
                HumanAdamCompletionStatusError,
                "není uzavřený",
            ):
                store.begin(
                    workstream_id=WORKSTREAM_ID,
                    client_message_id="completion-status-test-002",
                    base_head=BASE_HEAD,
                )

    def test_unknown_schema_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "completion.json"
            path.write_text('{"schema_version":99,"records":{}}', encoding="utf-8")
            store = HumanAdamCompletionStatusStore(path)

            with self.assertRaises(HumanAdamCompletionStatusError):
                store.load(workstream_id=WORKSTREAM_ID)


class HumanAdamCompletionPublicStatusTests(unittest.TestCase):
    def completed_record(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = HumanAdamCompletionStatusStore(
                Path(temp_dir) / "completion.json"
            )
            store.begin(
                workstream_id=WORKSTREAM_ID,
                client_message_id=CLIENT_MESSAGE_ID,
                base_head=BASE_HEAD,
            )
            return store.update(
                workstream_id=WORKSTREAM_ID,
                client_message_id=CLIENT_MESSAGE_ID,
                state=CHECKPOINT_COMPLETED,
                checkpoint_head=CHECKPOINT_HEAD,
                answer_persisted=True,
                remote_push_deferred=True,
                pending_remote_commit_count=5,
            )

    def test_completed_status_requires_git_and_workspace_evidence(self) -> None:
        status = public_completion_status(
            record=self.completed_record(),
            observed_at="2026-08-05T10:03:00+00:00",
            source_snapshot=clean_workspace(),
            deployment_snapshot={"main_short": CHECKPOINT_HEAD[:12]},
            checkpoint_reachable=True,
        )

        self.assertEqual(status["state"], CHECKPOINT_COMPLETED)
        self.assertTrue(status["git_verified"])
        self.assertTrue(status["workspace_verified"])
        self.assertEqual(status["deployment_state"], "verified_current")

    def test_completed_record_becomes_attention_when_git_disagrees(self) -> None:
        status = public_completion_status(
            record=self.completed_record(),
            observed_at="2026-08-05T10:03:00+00:00",
            source_snapshot=clean_workspace(),
            deployment_snapshot={},
            checkpoint_reachable=False,
        )

        self.assertEqual(status["state"], ATTENTION_REQUIRED)
        self.assertFalse(status["git_verified"])

    def test_model_block_names_server_as_completion_authority(self) -> None:
        status = public_completion_status(
            record=self.completed_record(),
            observed_at="2026-08-05T10:03:00+00:00",
            source_snapshot=clean_workspace(),
            deployment_snapshot={},
            checkpoint_reachable=True,
        )

        block = completion_status_model_block(status)

        self.assertIn("[LAST_STEP_COMPLETION]", block)
        self.assertIn("state=checkpoint_completed", block)
        self.assertIn(f"checkpoint={CHECKPOINT_HEAD[:12]}", block)
        self.assertIn("server block is the authority", block)

    def test_orphaned_running_state_requires_attention(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = HumanAdamCompletionStatusStore(
                Path(temp_dir) / "completion.json"
            )
            running = store.begin(
                workstream_id=WORKSTREAM_ID,
                client_message_id=CLIENT_MESSAGE_ID,
                base_head=BASE_HEAD,
            )

        status = public_completion_status(
            record=running,
            observed_at="2026-08-05T10:03:00+00:00",
            source_snapshot=clean_workspace(source_head=BASE_HEAD),
            deployment_snapshot={},
            checkpoint_reachable=None,
            server_operation_active=False,
        )

        self.assertEqual(status["state"], ATTENTION_REQUIRED)
        self.assertEqual(status["record_state"], "turn_started")
