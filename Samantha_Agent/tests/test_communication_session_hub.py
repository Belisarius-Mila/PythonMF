from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path

from app.codex_appserver import AppServerError, TurnReceipt
from app.communication.session_hub import (
    CanonicalSessionHub,
    SessionBusyError,
    SessionDeliveryUnknownError,
)


class FakeClient:
    instances: list["FakeClient"] = []
    block_started: threading.Event | None = None
    block_release: threading.Event | None = None
    fail_send = False

    def __init__(self) -> None:
        self.running = True
        self.sent = 0
        self.started_kwargs: dict[str, object] = {}
        self.resumed_thread_id = ""
        self.__class__.instances.append(self)

    def start_thread(self, **kwargs: object) -> str:
        self.started_kwargs = kwargs
        return "canonical-thread"

    def resume_thread(self, thread_id: str, **_kwargs: object) -> str:
        self.resumed_thread_id = thread_id
        return thread_id

    def send_text(self, *, thread_id: str, client_message_id: str, **_kwargs: object) -> TurnReceipt:
        self.sent += 1
        if self.__class__.block_started is not None:
            self.__class__.block_started.set()
        if self.__class__.block_release is not None:
            self.__class__.block_release.wait(timeout=3)
        if self.__class__.fail_send:
            raise AppServerError("ambiguous")
        return TurnReceipt(
            client_message_id=client_message_id,
            thread_id=thread_id,
            turn_id=f"turn-{self.sent}",
            requested_at="a",
            accepted_at="b",
            started_at="c",
            completed_at="d",
            status="completed",
            answer="Hotovo",
            turn_started_confirmed=True,
            user_item_count=1,
            duration_ms=1,
        )

    def close(self) -> None:
        self.running = False


class CanonicalSessionHubTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeClient.instances = []
        FakeClient.block_started = None
        FakeClient.block_release = None
        FakeClient.fail_send = False

    def make_hub(self, root: Path) -> CanonicalSessionHub:
        return CanonicalSessionHub(
            state_path=root / "session.json",
            workspace=root,
            client_factory=FakeClient,
            developer_instructions="Canonical Adam",
            sandbox="read-only",
            sandbox_policy={"type": "readOnly"},
            approval_policy="never",
            reasoning_effort="high",
        )

    def test_persists_one_thread_and_resumes_it_after_reconnect(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = self.make_hub(root)
            connected = first.connect()
            first.close()
            second = self.make_hub(root)
            resumed = second.connect()

        self.assertEqual(connected["thread_id"], "canonical-thread")
        self.assertFalse(FakeClient.instances[0].started_kwargs["ephemeral"])
        self.assertEqual(FakeClient.instances[1].resumed_thread_id, "canonical-thread")
        self.assertEqual(resumed["connection_generation"], 2)

    def test_completed_client_message_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            hub = self.make_hub(Path(temp_dir))
            first = hub.send(text="Ahoj", client_message_id="message-0001")
            duplicate = hub.send(text="Ahoj", client_message_id="message-0001")

        self.assertTrue(first["entry"]["delivery_confirmed"])
        self.assertTrue(duplicate["duplicate_prevented"])
        self.assertEqual(FakeClient.instances[0].sent, 1)

    def test_parallel_turn_is_rejected_instead_of_queued_silently(self) -> None:
        FakeClient.block_started = threading.Event()
        FakeClient.block_release = threading.Event()
        with tempfile.TemporaryDirectory() as temp_dir:
            hub = self.make_hub(Path(temp_dir))
            worker_error: list[BaseException] = []

            def worker() -> None:
                try:
                    hub.send(text="První", client_message_id="message-0001")
                except BaseException as exc:  # pragma: no cover - assertion below reports it.
                    worker_error.append(exc)

            thread = threading.Thread(target=worker)
            thread.start()
            self.assertTrue(FakeClient.block_started.wait(timeout=2))
            with self.assertRaises(SessionBusyError):
                hub.send(text="Druhý", client_message_id="message-0002")
            with self.assertRaises(SessionBusyError):
                hub.close()
            FakeClient.block_release.set()
            thread.join(timeout=3)

        self.assertEqual(worker_error, [])
        self.assertFalse(thread.is_alive())

    def test_ambiguous_failure_is_persisted_and_never_auto_retried(self) -> None:
        FakeClient.fail_send = True
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            hub = self.make_hub(root)
            with self.assertRaises(AppServerError):
                hub.send(text="Nejisté", client_message_id="message-0001")
            FakeClient.fail_send = False
            restored = self.make_hub(root)
            with self.assertRaises(SessionDeliveryUnknownError):
                restored.send(text="Nejisté", client_message_id="message-0001")
            state = restored.snapshot()

        self.assertEqual(state["messages"][0]["status"], "delivery_unknown")
        self.assertTrue(state["messages"][0]["recovery_required"])
        self.assertEqual(len(FakeClient.instances), 1)

    def test_crash_left_pending_message_becomes_delivery_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "session.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "thread_id": "thread",
                        "messages": [{"client_message_id": "message-0001", "status": "pending"}],
                    }
                ),
                encoding="utf-8",
            )
            restored = self.make_hub(root).snapshot()

        self.assertEqual(restored["messages"][0]["status"], "delivery_unknown")
        self.assertTrue(restored["messages"][0]["recovery_required"])


if __name__ == "__main__":
    unittest.main()
