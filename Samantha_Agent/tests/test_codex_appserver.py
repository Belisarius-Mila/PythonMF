from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.codex_appserver import (
    LAB_DEVELOPER_INSTRUCTIONS,
    AppServerContractError,
    AppServerError,
    CodexVersion,
    TurnReceipt,
    codex_environment,
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
    next_process = 1000

    def __init__(self, **_kwargs: object):
        self.running = True
        self.process_id = self.__class__.next_process
        self.__class__.next_process += 1
        self.connection_id = f"connection-{self.process_id}"
        self.thread_id = ""
        self.sent = 0
        self.sent_texts: list[str] = []
        self.started_kwargs: dict[str, object] = {}
        self.resumed_kwargs: dict[str, object] = {}
        self.__class__.instances.append(self)

    def start_thread(self, **kwargs: object) -> str:
        self.started_kwargs = kwargs
        self.thread_id = f"thread-{self.__class__.next_thread}"
        self.__class__.next_thread += 1
        return self.thread_id

    def resume_thread(self, thread_id: str, **kwargs: object) -> str:
        self.resumed_kwargs = kwargs
        self.thread_id = thread_id
        return thread_id

    def send_text(self, *, thread_id: str, text: str, client_message_id: str) -> TurnReceipt:
        self.sent += 1
        self.sent_texts.append(text)
        return TurnReceipt(
            client_message_id=client_message_id,
            thread_id=thread_id,
            turn_id=f"turn-{self.sent}",
            requested_at="2026-07-12T20:00:01+00:00",
            accepted_at="2026-07-12T20:00:02+00:00",
            started_at="2026-07-12T20:00:03+00:00",
            completed_at="2026-07-12T20:00:04+00:00",
            status="completed",
            answer="Odpověď",
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

    def test_codex_environment_adds_service_runtime_paths(self) -> None:
        env = codex_environment({"PATH": "/custom/bin", "HOME": "/tmp/home"})
        parts = env["PATH"].split(":")
        self.assertEqual(parts[0], "/usr/local/bin")
        self.assertIn("/usr/bin", parts)
        self.assertIn("/custom/bin", parts)
        self.assertEqual(env["HOME"], "/tmp/home")


class AppServerLabServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeClient.instances = []
        FakeClient.next_thread = 1
        FakeClient.next_process = 1000

    def make_service(self, root: Path) -> AppServerLabService:
        return AppServerLabService(
            state_path=root / "state.json",
            project_root=root,
            client_factory=FakeClient,
            version_getter=lambda *_args: FakeVersion(),
        )

    def test_status_does_not_start_appserver(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = self.make_service(Path(temp_dir))
            status = service.status()
        self.assertFalse(status["thread_ready"])
        self.assertEqual(status["connection_state"], "disconnected")
        self.assertEqual(FakeClient.instances, [])

    def test_status_caches_immutable_codex_version(self) -> None:
        calls = 0

        def version_getter(*_args: object) -> FakeVersion:
            nonlocal calls
            calls += 1
            return FakeVersion()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = AppServerLabService(
                state_path=root / "state.json",
                project_root=root,
                client_factory=FakeClient,
                version_getter=version_getter,
            )
            first = service.status()
            second = service.status()

        self.assertEqual(calls, 1)
        self.assertEqual(first["version"], second["version"])
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
        self.assertEqual(FakeClient.instances[0].sent_texts, ["Test návaznosti"])
        self.assertFalse(first["entry"]["capsule_attached"])

    def test_completed_message_can_be_explicitly_saved_to_tvbcp_once(self) -> None:
        appended: list[dict[str, str]] = []

        def appender(**kwargs: str) -> dict[str, object]:
            appended.append(kwargs)
            return {"ok": True}

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self.make_service(root)
            service.new_thread(label="Cestovní brainstorming")
            service.send(text="Návrh aplikace", client_message_id="appserver-lab-tvbcp001")
            saved = service.save_message_to_tvbcp(
                client_message_id="appserver-lab-tvbcp001",
                appender=appender,
            )
            duplicate = service.save_message_to_tvbcp(
                client_message_id="appserver-lab-tvbcp001",
                appender=appender,
            )
            persisted = self.make_service(root).status()["messages"][0]

        self.assertTrue(saved["ok"])
        self.assertFalse(saved["duplicate_prevented"])
        self.assertTrue(duplicate["duplicate_prevented"])
        self.assertEqual(len(appended), 1)
        self.assertEqual(appended[0]["mila"], "Návrh aplikace")
        self.assertEqual(appended[0]["adam"], "Odpověď")
        self.assertEqual(appended[0]["discussed"], "Cestovní brainstorming")
        self.assertTrue(persisted["tvbcp_saved_at"])

    def test_disconnect_and_resume_keep_same_thread(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = self.make_service(Path(temp_dir))
            created = service.new_thread()
            thread_id = created["thread_id"]
            disconnected = service.disconnect()
            resumed = service.resume()
            restarted = service.restart()

        self.assertEqual(disconnected["connection_state"], "disconnected")
        self.assertEqual(resumed["connection_state"], "connected")
        self.assertEqual(resumed["thread_id"], thread_id)
        self.assertEqual(restarted["thread_id"], thread_id)
        self.assertEqual(restarted["connection_generation"], 3)
        self.assertEqual(len(FakeClient.instances), 3)
        events = restarted["lifecycle_events"]
        self.assertEqual(
            [event["action"] for event in events],
            ["thread_created", "disconnected", "thread_resumed", "appserver_restarted"],
        )
        self.assertEqual(events[0]["process_pid"], 1000)
        self.assertEqual(events[1]["previous_process_pid"], 1000)
        self.assertEqual(events[1]["process_pid"], 0)
        self.assertEqual(events[2]["process_pid"], 1001)
        self.assertEqual(events[3]["previous_process_pid"], 1001)
        self.assertEqual(events[3]["process_pid"], 1002)
        self.assertTrue(all(event["thread_id"] == thread_id for event in events))
        self.assertTrue(all("user_text" not in event and "answer" not in event for event in events))

    def test_registry_keeps_threads_separate_and_attaches_capsule_to_turn(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = self.make_service(Path(temp_dir))
            first = service.new_thread(label="Relace A")
            first_registry_id = first["active_registry_id"]
            first_thread_id = first["thread_id"]
            service.send(text="Zpráva A", client_message_id="appserver-lab-aaaaaaaa")

            second = service.new_thread(label="Relace B")
            second_registry_id = second["active_registry_id"]
            second_thread_id = second["thread_id"]
            service.send(text="Zpráva B", client_message_id="appserver-lab-bbbbbbbb")
            service.update_capsule(
                registry_id=second_registry_id,
                capsule={
                    "objective": "Ověřit návaznost B",
                    "current_state": "Druhý thread je aktivní",
                    "next_step": "Obnovit relaci",
                    "constraints": ["Bez zápisu mimo private data"],
                },
            )
            capsule_turn = service.send(
                text="Dotaz B2",
                client_message_id="appserver-lab-cccccccc",
            )
            capsule_turn_text = FakeClient.instances[1].sent_texts[-1]
            service.restart()
            second_resume_instructions = str(FakeClient.instances[-1].resumed_kwargs["developer_instructions"])

            selected_first = service.select_thread(registry_id=first_registry_id)
            first_messages = selected_first["messages"]
            selected_second = service.select_thread(registry_id=second_registry_id)
            second_messages = selected_second["messages"]

        self.assertEqual(len(second["threads"]), 2)
        self.assertNotEqual(first_thread_id, second_thread_id)
        self.assertEqual(first_messages[0]["user_text"], "Zpráva A")
        self.assertEqual(second_messages[0]["user_text"], "Zpráva B")
        self.assertEqual(second_messages[1]["user_text"], "Dotaz B2")
        counts = {item["registry_id"]: item["turn_count"] for item in selected_second["threads"]}
        self.assertEqual(counts[first_registry_id], 1)
        self.assertEqual(counts[second_registry_id], 2)
        self.assertTrue(capsule_turn["entry"]["capsule_attached"])
        self.assertEqual(capsule_turn["entry"]["capsule_revision_sent"], 1)
        self.assertIn('"current_state":"Druhý thread je aktivní"', capsule_turn_text)
        self.assertIn('"user_message":"Dotaz B2"', capsule_turn_text)
        self.assertNotIn("Zpráva B", capsule_turn_text)
        self.assertEqual(second_resume_instructions, LAB_DEVELOPER_INSTRUCTIONS)

    def test_legacy_single_thread_state_migrates_without_losing_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state_path = root / "state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "thread_id": "legacy-thread",
                        "created_at": "2026-07-12T20:00:00+00:00",
                        "updated_at": "2026-07-12T20:01:00+00:00",
                        "connection_generation": 3,
                        "messages": [{"status": "completed", "user_text": "Historie"}],
                        "lifecycle_events": [{"action": "thread_created", "thread_id": "legacy-thread"}],
                    }
                ),
                encoding="utf-8",
            )
            service = self.make_service(root)
            migrated = service.status()
            service.disconnect()
            persisted = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(migrated["schema_version"], 2)
        self.assertEqual(migrated["thread_id"], "legacy-thread")
        self.assertEqual(migrated["messages"][0]["user_text"], "Historie")
        self.assertEqual(len(persisted["threads"]), 1)
        self.assertNotIn("thread_id", persisted)
        self.assertNotIn("messages", persisted)

    def test_capsule_rejects_more_than_six_constraints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = self.make_service(Path(temp_dir))
            created = service.new_thread(label="Limit")
            with self.assertRaises(AppServerError):
                service.update_capsule(
                    registry_id=created["active_registry_id"],
                    capsule={"constraints": [str(index) for index in range(7)]},
                )


if __name__ == "__main__":
    unittest.main()
