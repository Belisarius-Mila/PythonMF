from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.communication.codex_delivery_recovery import (
    CodexDeliveryRecoveryError,
    read_completed_delivery_evidence,
)


class CodexDeliveryRecoveryTests(unittest.TestCase):
    def _write_rollout(self, root: Path, thread_id: str, events: list[dict[str, object]]) -> None:
        path = root / "2026" / "08" / "16" / f"rollout-test-{thread_id}.jsonl"
        path.parent.mkdir(parents=True)
        path.write_text(
            "".join(json.dumps(item) + "\n" for item in events),
            encoding="utf-8",
        )

    @staticmethod
    def _event(payload: dict[str, object]) -> dict[str, object]:
        return {"timestamp": "2026-08-16T08:49:58Z", "type": "event_msg", "payload": payload}

    def test_reads_exact_matching_final_answer_and_completion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_rollout(
                root,
                "thread-0001",
                [
                    self._event(
                        {"type": "user_message", "client_id": "message-0001", "message": "private"}
                    ),
                    self._event(
                        {"type": "agent_message", "phase": "final_answer", "message": "Hotovo"}
                    ),
                    self._event(
                        {
                            "type": "task_complete",
                            "turn_id": "turn-0001",
                            "completed_at": "2026-08-16T08:49:58Z",
                            "last_agent_message": "Hotovo",
                        }
                    ),
                ],
            )
            evidence = read_completed_delivery_evidence(
                sessions_root=root,
                thread_id="thread-0001",
                client_message_id="message-0001",
            )

        self.assertEqual(evidence.turn_id, "turn-0001")
        self.assertEqual(evidence.answer, "Hotovo")

    def test_rejects_mismatch_duplicate_or_later_turn(self) -> None:
        cases = [
            [
                self._event({"type": "user_message", "client_id": "message-0001"}),
                self._event({"type": "agent_message", "phase": "final_answer", "message": "A"}),
                self._event(
                    {
                        "type": "task_complete",
                        "turn_id": "turn-0001",
                        "completed_at": "done",
                        "last_agent_message": "B",
                    }
                ),
            ],
            [
                self._event({"type": "user_message", "client_id": "message-0001"}),
                self._event({"type": "agent_message", "phase": "final_answer", "message": "A"}),
                self._event(
                    {
                        "type": "task_complete",
                        "turn_id": "turn-0001",
                        "completed_at": "done",
                        "last_agent_message": "A",
                    }
                ),
                self._event({"type": "user_message", "client_id": "message-0002"}),
            ],
        ]
        for events in cases:
            with self.subTest(events=len(events)), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                self._write_rollout(root, "thread-0001", events)
                with self.assertRaises(CodexDeliveryRecoveryError):
                    read_completed_delivery_evidence(
                        sessions_root=root,
                        thread_id="thread-0001",
                        client_message_id="message-0001",
                    )
