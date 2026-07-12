from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.codex_appserver import (
    AppServerContractError,
    CodexVersion,
    TurnReceipt,
)
from app.codex_appserver_lab import AppServerLabService, normalize_client_timestamp


class FakeVersion:
    raw = "codex-cli 0.144.1"
    major = 0
    minor = 144
    patch = 1


class FakeClient:
    instances: list["FakeClient"] = []
    next_thread = 1

    def __init__(self):
        self.running = True
        self.thread_id = ""
        self.sent = 0
        self.__class__.instances.append(self)

    def start_thread(self, **_kwargs: object) -> str:
        self.thread_id = f"thread-{self.__class__.next_thread}"
        self.__class__.next_thread += 1
        return self.thread_id

    def resume_thread(self, thread_id: str, **_kwargs: object) -> str:
        self.thread_id = thread_id
        return thread_id

    def send_text(self, *, thread_id: str, text: str, client_message_id: str) -> TurnReceipt:
        self.sent += 1
        return TurnReceipt(
            client_message_id=client_message_id,
            thread_id=thread_id,
            turn_id=f"turn-{self.sent}",
            requested_at="2026-07-12T20:00:01+00:00",
            accepted_at="2026-07-12T20:00:02+00:00",
            started_at="2026-07-12T20:00:03+00:00",
            completed_at="2026-07-12T20:00:04+00:00",
            status="completed",
            answer=f"Odpověď: {text}",
            turn_started_confirmed=True,
            user_item_count=1,
            duration_ms=3000,
        )

    def close(self) -> None:
        self.running = False


class CodexContractTests(unittest.TestCase):
    def test_version_parser_is_strict(self) -> None:
        version = CodexVersion.parse("codex-cli 0.144.1")
        self.assertEqual((version.major, version.minor, version.patch), (0, 144, 1))
        with self.assertRaises(AppServerContractError):
            CodexVersion.parse("unknown")

    def test_receipt_requires_exactly_one_user_item_and_started_event(self) -> None:
        base = dict(
            client_message_id="appserver-lab-12345678",
            thread_id="thread",
            turn_id="turn",
            requested_at="a",
            accepted_at="b",
            started_at="c",
            completed_at="d",
            status="completed",
            answer="ano",
            turn_started_confirmed=True,
            duration_ms=1,
        )
        self.assertTrue(TurnReceipt(user_item_count=1, **base).delivered)
        self.assertFalse(TurnReceipt(user_item_count=2, **base).delivered)
        self.assertFalse(TurnReceipt(user_item_count=1, **(base | {"turn_started_confirmed": False})).delivered)

    def test_client_timestamp_is_normalized_or_rejected(self) -> None:
        self.assertEqual(normalize_client_timestamp("2026-07-12T22:30:00+02:00"), "2026-07-12T20:30:00+00:00")
        self.assertEqual(normalize_client_timestamp("not-a-time"), "")


class AppServerLabServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeClient.instances = []
        FakeClient.next_thread = 1

    def make_service(self, root: Path) -> AppServerLabService:
        return AppServerLabService(
            state_path=root / "state.json",
            project_root=root,
            client_factory=FakeClient,
            version_getter=lambda: FakeVersion(),
        )

    def test_status_does_not_start_appserver(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = self.make_service(Path(temp_dir))
            status = service.status()
        self.assertFalse(status["thread_ready"])
        self.assertEqual(status["connection_state"], "disconnected")
        self.assertEqual(FakeClient.instances, [])

    def test_new_thread_send_and_duplicate_are_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self.make_service(root)
            created = service.new_thread()
            first = service.send(
                text="Test návaznosti",
                client_message_id="appserver-lab-abcdefgh",
                client_sent_at="2026-07-12T22:00:00+02:00",
            )
            duplicate = service.send(
                text="Test návaznosti",
                client_message_id="appserver-lab-abcdefgh",
                client_sent_at="2026-07-12T22:00:00+02:00",
            )
            persisted = self.make_service(root).status()

        self.assertTrue(created["thread_ready"])
        self.assertTrue(first["ok"])
        self.assertEqual(first["entry"]["status"], "completed")
        self.assertEqual(first["entry"]["client_sent_at"], "2026-07-12T20:00:00+00:00")
        self.assertTrue(duplicate["duplicate_prevented"])
        self.assertEqual(len(persisted["messages"]), 1)
        self.assertEqual(FakeClient.instances[0].sent, 1)

    def test_disconnect_and_resume_keep_same_thread(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = self.make_service(Path(temp_dir))
            created = service.new_thread()
            thread_id = created["thread_id"]
            disconnected = service.disconnect()
            resumed = service.resume()

        self.assertEqual(disconnected["connection_state"], "disconnected")
        self.assertEqual(resumed["connection_state"], "connected")
        self.assertEqual(resumed["thread_id"], thread_id)
        self.assertEqual(len(FakeClient.instances), 2)


if __name__ == "__main__":
    unittest.main()
