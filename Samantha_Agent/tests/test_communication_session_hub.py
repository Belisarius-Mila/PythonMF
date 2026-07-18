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
    SessionHubError,
)


class FakeClient:
    instances: list["FakeClient"] = []
    block_started: threading.Event | None = None
    block_release: threading.Event | None = None
    fail_send = False
    fail_resume = False
    next_thread_ids: list[str] = []

    def __init__(self) -> None:
        self.running = True
        self.sent = 0
        self.sent_texts: list[str] = []
        self.started_kwargs: dict[str, object] = {}
        self.resumed_thread_id = ""
        self.__class__.instances.append(self)

    def start_thread(self, **kwargs: object) -> str:
        self.started_kwargs = kwargs
        if self.__class__.next_thread_ids:
            return self.__class__.next_thread_ids.pop(0)
        return "canonical-thread"

    def resume_thread(self, thread_id: str, **_kwargs: object) -> str:
        if self.__class__.fail_resume:
            raise AppServerError("missing thread")
        self.resumed_thread_id = thread_id
        return thread_id

    def send_text(
        self,
        *,
        thread_id: str,
        client_message_id: str,
        text: str,
        **_kwargs: object,
    ) -> TurnReceipt:
        self.sent += 1
        self.sent_texts.append(text)
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
        FakeClient.fail_resume = False
        FakeClient.next_thread_ids = []

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

    def test_model_input_is_sent_but_never_persisted_in_user_history(self) -> None:
        model_input = (
            "[WORKSPACE SNAPSHOT]\nsource_head=abcdef12\n\n"
            "[HUMAN_ADAM_CONTEXT_ANCHOR]\nCíl: kontinuita\n[/HUMAN_ADAM_CONTEXT_ANCHOR]\n\n"
            "Původní text"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            hub = self.make_hub(root)
            result = hub.send(
                text="Původní text",
                model_input_text=model_input,
                client_message_id="message-0002",
            )
            snapshot = hub.snapshot()
            persisted = (root / "session.json").read_text(encoding="utf-8")

        self.assertEqual(FakeClient.instances[0].sent_texts, [model_input])
        self.assertEqual(result["entry"]["user_text"], "Původní text")
        self.assertEqual(snapshot["messages"][0]["user_text"], "Původní text")
        self.assertNotIn("WORKSPACE SNAPSHOT", persisted)
        self.assertNotIn("source_head", persisted)
        self.assertNotIn("HUMAN_ADAM_CONTEXT_ANCHOR", persisted)
        self.assertNotIn("Cíl: kontinuita", persisted)

    def test_empty_unmaterialized_thread_can_be_replaced_without_losing_work(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = self.make_hub(root)
            first.connect()
            first.close()
            FakeClient.fail_resume = True
            replacement = self.make_hub(root).connect()

        self.assertEqual(replacement["thread_id"], "canonical-thread")
        self.assertEqual(replacement["messages"], [])

    def test_nonempty_thread_is_never_replaced_when_resume_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = self.make_hub(root)
            first.send(text="Ahoj", client_message_id="message-0001")
            first.close()
            FakeClient.fail_resume = True
            with self.assertRaises(AppServerError):
                self.make_hub(root).connect()

        self.assertEqual(len(FakeClient.instances), 2)

    def test_rotation_preserves_previous_thread_and_local_history(self) -> None:
        FakeClient.next_thread_ids = ["first-thread", "second-thread"]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            hub = self.make_hub(root)
            hub.send(text="Ahoj", client_message_id="message-0001")
            original_client = FakeClient.instances[0]
            result = hub.rotate_thread(expected_thread_id="first-thread")
            snapshot = hub.snapshot()
            persisted = json.loads((root / "session.json").read_text(encoding="utf-8"))

        self.assertTrue(result["rotated"])
        self.assertEqual(result["previous_thread_id"], "first-thread")
        self.assertEqual(result["thread_id"], "second-thread")
        self.assertFalse(original_client.running)
        self.assertEqual(snapshot["thread_message_count"], 0)
        self.assertEqual(snapshot["rotation_count"], 1)
        self.assertEqual(snapshot["messages"][0]["thread_id"], "first-thread")
        self.assertEqual(persisted["previous_threads"][0]["thread_id"], "first-thread")
        self.assertEqual(persisted["previous_threads"][0]["message_count"], 1)

    def test_rotation_rejects_stale_thread_and_unresolved_delivery(self) -> None:
        FakeClient.next_thread_ids = ["first-thread"]
        with tempfile.TemporaryDirectory() as temp_dir:
            hub = self.make_hub(Path(temp_dir))
            hub.connect()
            with self.assertRaisesRegex(SessionHubError, "mezitím změnilo"):
                hub.rotate_thread(expected_thread_id="stale-thread")
            with hub._state_lock:
                hub._state["messages"].append(
                    {
                        "client_message_id": "message-0001",
                        "thread_id": "first-thread",
                        "status": "delivery_unknown",
                        "recovery_required": True,
                    }
                )
            with self.assertRaises(SessionDeliveryUnknownError):
                hub.rotate_thread(expected_thread_id="first-thread")

        self.assertEqual(len(FakeClient.instances), 1)

    def test_empty_rotated_thread_can_be_replaced_after_restart_with_old_history(self) -> None:
        FakeClient.next_thread_ids = ["first-thread", "second-thread", "replacement-thread"]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = self.make_hub(root)
            first.send(text="Ahoj", client_message_id="message-0001")
            first.rotate_thread(expected_thread_id="first-thread")
            first.close()
            FakeClient.fail_resume = True
            replacement = self.make_hub(root).connect()

        self.assertEqual(replacement["thread_id"], "replacement-thread")
        self.assertEqual(replacement["messages"][0]["thread_id"], "first-thread")
        self.assertEqual(replacement["rotation_count"], 1)

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
