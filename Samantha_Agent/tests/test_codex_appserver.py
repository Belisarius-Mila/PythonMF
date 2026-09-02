from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from app.codex_appserver import (
    AppServerContractError,
    CodexAppServerClient,
    CodexVersion,
    TurnReceipt,
    UNIX_APP_SERVER_MAX_MESSAGE_BYTES,
    UnixSocketAppServerTransport,
    completed_generated_images,
    codex_environment,
)


class CodexContractTests(unittest.TestCase):
    def test_version_parser_is_strict(self) -> None:
        version = CodexVersion.parse("codex-cli 0.144.1")
        self.assertEqual((version.major, version.minor, version.patch), (0, 144, 1))
        with self.assertRaises(AppServerContractError):
            CodexVersion.parse("unknown")

    def test_receipt_requires_exactly_one_user_item_and_started_event(self) -> None:
        base = dict(
            client_message_id="appserver-client-12345678",
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

    def test_receipt_public_dict_exposes_only_generated_image_count(self) -> None:
        receipt = TurnReceipt(
            client_message_id="appserver-client-12345678",
            thread_id="thread",
            turn_id="turn",
            requested_at="a",
            accepted_at="b",
            started_at="c",
            completed_at="d",
            status="completed",
            answer="ano",
            turn_started_confirmed=True,
            user_item_count=1,
            duration_ms=1,
            generated_images=(
                {
                    "item_id": "exec-image-12345678",
                    "result": "secret-base64",
                    "revised_prompt": "prompt",
                },
            ),
        )

        public = receipt.as_dict()

        self.assertEqual(public["generated_image_count"], 1)
        self.assertNotIn("generated_images", public)
        self.assertNotIn("secret-base64", json.dumps(public))

    def test_client_preserves_matching_user_item_when_final_turn_omits_inputs(self) -> None:
        transport = _ScriptedTransport(
            completed_items=[
                {"type": "agentMessage", "id": "agent-final", "text": "ano"},
            ]
        )

        with patch(
            "app.codex_appserver.read_codex_version",
            return_value=CodexVersion.parse("codex-cli 0.147.0"),
        ):
            client = CodexAppServerClient(transport_factory=lambda **_kwargs: transport)
            receipt = client.send_text(
                thread_id="thread-1",
                client_message_id="message-1",
                text="test",
            )

        self.assertTrue(receipt.delivered)
        self.assertEqual(receipt.user_item_count, 1)

    def test_client_rejects_different_user_item_in_final_turn(self) -> None:
        transport = _ScriptedTransport(
            completed_items=[
                {"type": "userMessage", "id": "user-other", "clientId": "message-other"},
                {"type": "agentMessage", "id": "agent-final", "text": "ano"},
            ]
        )

        with patch(
            "app.codex_appserver.read_codex_version",
            return_value=CodexVersion.parse("codex-cli 0.147.0"),
        ):
            client = CodexAppServerClient(transport_factory=lambda **_kwargs: transport)
            with self.assertRaises(AppServerContractError):
                client.send_text(
                    thread_id="thread-1",
                    client_message_id="message-1",
                    text="test",
                )

    def test_codex_environment_adds_service_runtime_paths(self) -> None:
        env = codex_environment({"PATH": "/custom/bin", "HOME": "/tmp/home"})
        parts = env["PATH"].split(":")
        self.assertEqual(parts[0], "/usr/local/bin")
        self.assertIn("/usr/bin", parts)
        self.assertIn("/custom/bin", parts)
        self.assertEqual(env["HOME"], "/tmp/home")

    def test_unix_transport_rejects_relative_socket_before_connecting(self) -> None:
        with self.assertRaises(AppServerContractError):
            UnixSocketAppServerTransport(socket_path=Path("relative.sock"))

    def test_unix_transport_accepts_thread_resume_payload_larger_than_one_megabyte(
        self,
    ) -> None:
        message = {
            "id": 1,
            "result": {
                "thread": {
                    "id": "thread-large-resume",
                    "history": "x" * 1_100_000,
                }
            },
        }
        connection = _FakeUnixConnection([json.dumps(message)])

        with patch(
            "websockets.sync.client.unix_connect",
            return_value=connection,
        ) as unix_connect:
            transport = UnixSocketAppServerTransport(
                socket_path=Path("/private/tmp/samantha-app-server.sock"),
                timeout=1,
            )
            received = transport.receive(
                lambda payload: payload.get("id") == 1,
                description="velký thread/resume výsledek",
            )

        self.assertEqual(received["result"]["thread"]["id"], "thread-large-resume")
        self.assertEqual(UNIX_APP_SERVER_MAX_MESSAGE_BYTES, 64 * 1024 * 1024)
        self.assertGreater(UNIX_APP_SERVER_MAX_MESSAGE_BYTES, 46_323_050)
        self.assertEqual(
            unix_connect.call_args.kwargs["max_size"],
            UNIX_APP_SERVER_MAX_MESSAGE_BYTES,
        )

    def test_completed_images_are_bounded_deduplicated_and_drop_saved_paths(self) -> None:
        items = [
            {
                "type": "imageGeneration",
                "id": "exec-image-12345678",
                "status": "completed",
                "result": "aW1hZ2U=",
                "revisedPrompt": "Smyšlená modrá sova",
                "savedPath": "/private/secret/generated.png",
            },
            {
                "type": "imageGeneration",
                "id": "exec-image-12345678",
                "status": "completed",
                "result": "aW1hZ2U=",
            },
            {
                "type": "imageGeneration",
                "id": "exec-image-incomplete",
                "status": "inProgress",
                "result": "aW1hZ2U=",
            },
        ]

        images = completed_generated_images(items)

        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]["item_id"], "exec-image-12345678")
        self.assertEqual(images[0]["result"], "aW1hZ2U=")
        self.assertNotIn("savedPath", images[0])


class _FakeUnixConnection:
    def __init__(self, messages: list[str]) -> None:
        self.messages = list(messages)
        self.closed = False

    def __iter__(self):
        return iter(self.messages)

    def send(self, _message: str) -> None:
        return None

    def close(self) -> None:
        self.closed = True


class _ScriptedTransport:
    def __init__(self, *, completed_items: list[dict[str, str]]) -> None:
        self.running = True
        self.process_id = 0
        self._completed_items = completed_items
        self._events = [
            {
                "method": "turn/started",
                "params": {"threadId": "thread-1", "turn": {"id": "turn-1"}},
            },
            {
                "method": "item/completed",
                "params": {
                    "threadId": "thread-1",
                    "turnId": "turn-1",
                    "item": {
                        "type": "userMessage",
                        "id": "user-1",
                        "clientId": "message-1",
                    },
                },
            },
            {
                "method": "item/completed",
                "params": {
                    "threadId": "thread-1",
                    "turnId": "turn-1",
                    "item": {"type": "agentMessage", "id": "agent-1", "text": "ano"},
                },
            },
            {
                "method": "turn/completed",
                "params": {
                    "threadId": "thread-1",
                    "turn": {
                        "id": "turn-1",
                        "status": "completed",
                        "items": self._completed_items,
                    },
                },
            },
        ]

    def request(self, method: str, _params: dict[str, object]) -> dict[str, object]:
        if method == "initialize":
            return {}
        if method == "turn/start":
            return {"turn": {"id": "turn-1"}}
        raise AssertionError(f"Neočekávaný požadavek: {method}")

    def notify(self, _method: str, _params: dict[str, object] | None = None) -> None:
        return None

    def receive(self, predicate, *, description: str) -> dict[str, object]:
        while self._events:
            event = self._events.pop(0)
            if predicate(event):
                return event
        raise AssertionError(f"Chybí událost: {description}")

    def close(self) -> None:
        self.running = False


if __name__ == "__main__":
    unittest.main()
