from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from app.codex_appserver import (
    AppServerContractError,
    AppServerRpcError,
    AppServerTimeout,
    AppServerTurnError,
    CodexAppServerClient,
    CodexVersion,
    TurnReceipt,
    UNIX_APP_SERVER_MAX_MESSAGE_BYTES,
    UnixSocketAppServerTransport,
    StdioAppServerTransport,
    app_server_version,
    completed_generated_images,
    codex_environment,
)


class CodexContractTests(unittest.TestCase):
    def test_local_images_are_explicit_input_items_and_keep_the_same_delivery_contract(self):
        transport = _ScriptedTransport(completed_items=[])
        client = self.client(transport)
        with patch.object(transport, "request", wraps=transport.request) as request:
            receipt = client.send_text(thread_id="thread-1", text="Describe the room", client_message_id="message-1",
                                       local_image_paths=(Path("/tmp/selected.png"),))
        self.assertTrue(receipt.delivered)
        request.assert_called_once()
        self.assertEqual(request.call_args.args[0], "turn/start")
        self.assertEqual(request.call_args.args[1]["input"], [{"type": "text", "text": "Describe the room"},
            {"type": "localImage", "path": "/tmp/selected.png"}])

    def test_invalid_image_input_stops_before_any_model_turn(self):
        for images in ((Path("relative.png"),), ("/tmp/photo.png",), tuple(Path("/tmp/x.png") for _ in range(9))):
            transport = _ScriptedTransport(completed_items=[])
            client = self.client(transport)
            with patch.object(transport, "request") as request, self.assertRaises(AppServerContractError):
                client.send_text(thread_id="thread-1", text="Describe", local_image_paths=images)
            request.assert_not_called()

    def client(self, transport):
        with patch("app.codex_appserver.read_codex_version", return_value=CodexVersion.parse("codex-cli 0.166.0")):
            return CodexAppServerClient(transport_factory=lambda **_kwargs: transport)

    def test_connected_server_version_is_independent_of_local_cli(self):
        for version in ("0.163.0", "0.166.0"):
            transport = _ScriptedTransport(completed_items=[])
            original = transport.request
            with patch.object(transport, "request", side_effect=lambda method, params: (
                {"userAgent": f"codex_cli_rs/{version} (synthetic)"} if method == "initialize"
                else original(method, params))):
                client = self.client(transport)
            self.assertEqual(client.version.minor, 166)
            self.assertEqual(client.server_version.raw, f"codex-cli {version}")

    def test_unknown_old_and_prerelease_server_fail_before_thread_or_turn_requests(self):
        for metadata in ({}, {"userAgent": "unknown"}, {"userAgent": "codex/0.162.0"},
                         {"userAgent": "codex/0.163.0-beta.1"}, {"serverInfo": {"version": "invalid"}}):
            with self.subTest(metadata=metadata):
                transport = _ScriptedTransport(completed_items=[])
                with patch.object(transport, "request", return_value=metadata) as request:
                    with self.assertRaises(AppServerContractError):
                        self.client(transport)
                self.assertFalse(transport.running)
                self.assertEqual([c.args[0] for c in request.call_args_list], ["initialize"])

    def test_server_info_version_and_invalid_version_privacy(self):
        self.assertEqual(app_server_version({"serverInfo": {"version": "0.166.0"}}).minor, 166)
        with self.assertRaises(AppServerContractError) as raised:
            app_server_version({"userAgent": "PRIVATE_METADATA"})
        self.assertNotIn("PRIVATE_METADATA", str(raised.exception))

    def test_resume_excludes_history_and_preserves_thread_model_permissions(self):
        transport = _ScriptedTransport(completed_items=[])
        client = self.client(transport)
        with patch.object(transport, "request", return_value={"thread": {"id": "saved-thread"}}) as request:
            self.assertEqual(client.resume_thread("saved-thread", cwd=Path.cwd(), model="approved-model",
                             developer_instructions="unchanged", sandbox="read-only", approval_policy="never"), "saved-thread")
        request.assert_called_once_with("thread/resume", {
            "threadId": "saved-thread", "excludeTurns": True, "cwd": str(Path.cwd().resolve()),
            "model": "approved-model", "developerInstructions": "unchanged",
            "sandbox": "read-only", "approvalPolicy": "never",
        })

    def test_resume_rejection_or_different_thread_never_retries_or_forks(self):
        for result in ({"thread": {"id": "different"}}, AppServerRpcError("thread/resume", {"code": -32602, "message": "synthetic"})):
            client = self.client(_ScriptedTransport(completed_items=[]))
            with patch.object(client.transport, "request") as request:
                if isinstance(result, Exception):
                    request.side_effect = result
                else:
                    request.return_value = result
                with self.assertRaises(AppServerContractError):
                    client.resume_thread("saved-thread", cwd=Path.cwd())
            self.assertEqual([c.args[0] for c in request.call_args_list], ["thread/resume"])

    def test_final_answer_wins_over_streamed_commentary_partial_and_legacy(self):
        transport = _ScriptedTransport(completed_items=[])
        transport._events[2]["params"]["item"]["phase"] = "final_answer"
        for phase in ("commentary", "partial_answer", None, "future_phase"):
            transport._events.insert(-1, {"method": "item/completed", "params": {
                "threadId": "thread-1", "turnId": "turn-1", "item": {
                    "type": "agentMessage", "id": f"extra-{phase}", "text": "not-final", "phase": phase}}})
        receipt = self.client(transport).send_text(thread_id="thread-1", text="synthetic", client_message_id="message-1")
        self.assertEqual(receipt.answer, "ano")

    def test_completed_snapshot_uses_phase_and_is_authoritative(self):
        transport = _ScriptedTransport(completed_items=[
            {"type": "agentMessage", "id": "final", "phase": "final_answer", "text": "snapshot-final"},
            {"type": "agentMessage", "id": "progress", "phase": "commentary", "text": "snapshot-progress"},
        ])
        receipt = self.client(transport).send_text(thread_id="thread-1", text="synthetic", client_message_id="message-1")
        self.assertEqual(receipt.answer, "snapshot-final")
        self.assertEqual(receipt.user_item_count, 1)

    def test_nonfinal_unknown_and_empty_explicit_final_are_not_delivery(self):
        for phase, text in (("commentary", "progress"), ("partial_answer", "partial"),
                            ("future_phase", "future"), ("final_answer", ""), ("final_answer", 42)):
            transport = _ScriptedTransport(completed_items=[])
            transport._events[2]["params"]["item"].update(phase=phase, text=text)
            with self.subTest(phase=phase, text=text), self.assertRaises(AppServerContractError):
                self.client(transport).send_text(thread_id="thread-1", text="synthetic", client_message_id="message-1")

    def test_empty_final_does_not_fall_back_to_legacy_text(self):
        transport = _ScriptedTransport(completed_items=[
            {"type": "agentMessage", "text": "legacy"},
            {"type": "agentMessage", "phase": "final_answer", "text": " "},
        ])
        with self.assertRaises(AppServerContractError):
            self.client(transport).send_text(thread_id="thread-1", text="synthetic", client_message_id="message-1")

    def test_phase_less_messages_keep_last_legacy_answer(self):
        transport = _ScriptedTransport(completed_items=[
            {"type": "agentMessage", "text": "first"}, {"type": "agentMessage", "phase": None, "text": "last"}])
        receipt = self.client(transport).send_text(thread_id="thread-1", text="synthetic", client_message_id="message-1")
        self.assertEqual(receipt.answer, "last")

    def test_conflicting_finals_are_rejected_but_same_item_can_repeat(self):
        for second_id, second_text, accepted in (("a", "final", True), ("a", "changed", False), ("b", "other", False)):
            transport = _ScriptedTransport(completed_items=[
                {"type": "agentMessage", "id": "a", "phase": "final_answer", "text": "final"},
                {"type": "agentMessage", "id": second_id, "phase": "final_answer", "text": second_text}])
            client = self.client(transport)
            if accepted:
                self.assertEqual(client.send_text(thread_id="thread-1", text="synthetic", client_message_id="message-1").answer, "final")
            else:
                with self.assertRaises(AppServerContractError):
                    client.send_text(thread_id="thread-1", text="synthetic", client_message_id="message-1")

    def test_multiple_final_users_or_missing_started_proof_are_rejected(self):
        for missing_started in (False, True):
            transport = _ScriptedTransport(completed_items=[] if missing_started else [
                {"type": "userMessage", "clientId": "message-1"},
                {"type": "userMessage", "clientId": "other"}])
            if missing_started:
                transport._events.pop(0)
            with self.assertRaises(AppServerContractError):
                self.client(transport).send_text(thread_id="thread-1", text="synthetic", client_message_id="message-1")

    def test_rpc_errors_preserve_structured_details_without_printing_private_data(self):
        transport = StdioAppServerTransport.__new__(StdioAppServerTransport)
        transport._next_request_id = 1
        transport._send = Mock()
        error = {"code": -32001, "message": "PRIVATE_MESSAGE", "data": {"codexErrorInfo": "server_overloaded", "private": "PRIVATE_DATA"}}
        transport.receive = Mock(return_value={"id": 1, "error": error})
        with self.assertRaises(AppServerRpcError) as raised:
            transport.request("turn/start", {})
        exc = raised.exception
        self.assertEqual(exc.code, -32001)
        self.assertEqual(exc.data, error["data"])
        self.assertEqual(exc.server_message, "PRIVATE_MESSAGE")
        error["data"]["private"] = "mutated"
        self.assertEqual(exc.data["private"], "PRIVATE_DATA")
        self.assertNotIn("PRIVATE", str(exc))
        self.assertNotIn("PRIVATE", repr(exc))
        transport._send.assert_called_once()

    def test_malformed_rpc_error_remains_a_safe_contract_failure(self):
        transport = StdioAppServerTransport.__new__(StdioAppServerTransport)
        transport._next_request_id = 1
        transport._send = Mock()
        transport.receive = Mock(return_value={"id": 1, "error": "PRIVATE"})
        with self.assertRaises(AppServerContractError) as raised:
            transport.request("turn/start", {})
        self.assertNotIn("PRIVATE", str(raised.exception))

    def test_failed_or_interrupted_turn_preserves_error_and_never_repeats_start(self):
        for status in ("failed", "interrupted"):
            transport = _ScriptedTransport(completed_items=[])
            error = {"message": "PRIVATE", "additionalDetails": "PRIVATE_DETAIL",
                     "codexErrorInfo": {"httpConnectionFailed": {"httpStatusCode": 503}}}
            transport._events[-1]["params"]["turn"].update(status=status, error=error)
            client = self.client(transport)
            with patch.object(transport, "request", wraps=transport.request) as request:
                with self.assertRaises(AppServerTurnError) as raised:
                    client.send_text(thread_id="thread-1", text="synthetic", client_message_id="message-1")
            self.assertEqual(raised.exception.status, status)
            self.assertEqual(raised.exception.turn_error, error)
            self.assertIs(raised.exception.will_retry, False)
            self.assertNotIn("PRIVATE", str(raised.exception))
            self.assertEqual([c.args[0] for c in request.call_args_list], ["turn/start"])

    def test_retry_notification_does_not_resend_and_completion_can_still_succeed(self):
        transport = _ScriptedTransport(completed_items=[])
        transport._events.insert(1, {"method": "error", "params": {"threadId": "thread-1", "turnId": "turn-1",
            "error": {"message": "synthetic overload", "codexErrorInfo": "serverOverloaded"}, "willRetry": True}})
        client = self.client(transport)
        with patch.object(transport, "request", wraps=transport.request) as request:
            self.assertTrue(client.send_text(thread_id="thread-1", text="synthetic", client_message_id="message-1").delivered)
        self.assertEqual([c.args[0] for c in request.call_args_list], ["turn/start"])

    def test_retry_notification_survives_transport_timeout_without_success_or_resend(self):
        transport = _ScriptedTransport(completed_items=[])
        client = self.client(transport)
        error = {"message": "PRIVATE", "codexErrorInfo": {"httpConnectionFailed": {"httpStatusCode": 503}}}
        timeout = AppServerTimeout("safe timeout")
        with patch.object(transport, "receive", side_effect=[
            {"method": "error", "params": {"threadId": "thread-1", "turnId": "turn-1", "error": error, "willRetry": True}}, timeout]), \
             patch.object(transport, "request", wraps=transport.request) as request:
            with self.assertRaises(AppServerTimeout) as raised:
                client.send_text(thread_id="thread-1", text="synthetic", client_message_id="message-1")
        self.assertIs(raised.exception, timeout)
        self.assertEqual(timeout.turn_error, error)
        self.assertIs(timeout.will_retry, True)
        self.assertNotIn("PRIVATE", str(timeout))
        self.assertEqual([c.args[0] for c in request.call_args_list], ["turn/start"])

    def test_error_notification_supplies_missing_terminal_error(self):
        transport = _ScriptedTransport(completed_items=[])
        error = {"message": "synthetic", "codexErrorInfo": "usageLimitExceeded"}
        transport._events.insert(-1, {"method": "error", "params": {"threadId": "thread-1", "turnId": "turn-1", "error": error, "willRetry": False}})
        transport._events[-1]["params"]["turn"]["status"] = "failed"
        with self.assertRaises(AppServerTurnError) as raised:
            self.client(transport).send_text(thread_id="thread-1", text="synthetic", client_message_id="message-1")
        self.assertEqual(raised.exception.turn_error, error)

    def test_invalid_terminal_status_is_rejected(self):
        transport = _ScriptedTransport(completed_items=[])
        transport._events[-1]["params"]["turn"]["status"] = "inProgress"
        with self.assertRaises(AppServerContractError):
            self.client(transport).send_text(thread_id="thread-1", text="synthetic", client_message_id="message-1")

    def test_real_client_failure_stays_unknown_across_hub_restart_without_resend(self):
        from app.communication.session_hub import CanonicalSessionHub, SessionDeliveryUnknownError

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            transport = _ScriptedTransport(completed_items=[])
            transport._events[-1]["params"]["turn"].update(status="failed", error={"message": "PRIVATE_ERROR"})

            def hub():
                return CanonicalSessionHub(state_path=root / "session.json", workspace=root,
                    client_factory=lambda: self.client(transport), developer_instructions="synthetic",
                    sandbox="read-only", sandbox_policy={"type": "readOnly"}, approval_policy="never", reasoning_effort="low")

            with patch.object(transport, "request", wraps=transport.request) as request:
                first = hub()
                with self.assertRaises(AppServerTurnError):
                    first.send(text="synthetic", client_message_id="message-1")
                for instance in (first, hub()):
                    with self.assertRaises(SessionDeliveryUnknownError):
                        instance.send(text="synthetic", client_message_id="message-1")
            self.assertEqual(sum(c.args[0] == "turn/start" for c in request.call_args_list), 1)
            state = json.loads((root / "session.json").read_text())
            self.assertEqual(state["thread_id"], "thread-1")
            self.assertEqual(state["messages"][-1]["status"], "delivery_unknown")
            self.assertNotIn("PRIVATE_ERROR", json.dumps(state))

    def test_server_compatibility_failure_cannot_trigger_hubs_empty_thread_fallback(self):
        from app.communication.session_hub import CanonicalSessionHub, empty_session_state

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = empty_session_state()
            state["thread_id"] = "saved-empty-thread"
            (root / "session.json").write_text(json.dumps(state))
            transport = _ScriptedTransport(completed_items=[])
            with patch.object(transport, "request", return_value={}) as request:
                hub = CanonicalSessionHub(state_path=root / "session.json", workspace=root,
                    client_factory=lambda: self.client(transport), developer_instructions="synthetic",
                    sandbox="read-only", sandbox_policy={"type": "readOnly"}, approval_policy="never", reasoning_effort="low")
                with self.assertRaises(AppServerContractError):
                    hub.send(text="synthetic", client_message_id="message-1")
            self.assertEqual([c.args[0] for c in request.call_args_list], ["initialize"])
            self.assertEqual(json.loads((root / "session.json").read_text())["thread_id"], "saved-empty-thread")

    def test_thread_overrides_are_per_thread_and_optional(self) -> None:
        transport = _ScriptedTransport(completed_items=[])
        with patch("app.codex_appserver.read_codex_version", return_value=CodexVersion.parse("codex-cli 0.147.0")):
            client = CodexAppServerClient(transport_factory=lambda **_kwargs: transport)
            with patch.object(transport, "request", return_value={"thread": {"id": "new"}}) as request:
                client.start_thread(cwd=Path("."), config_overrides={"project_doc_max_bytes": 0},
                                    base_instructions="Data-only task")
                self.assertEqual(request.call_args.args[1]["config"], {"project_doc_max_bytes": 0})
                self.assertEqual(request.call_args.args[1]["baseInstructions"], "Data-only task")
                client.start_thread(cwd=Path("."))
                self.assertNotIn("config", request.call_args.args[1])
                self.assertNotIn("baseInstructions", request.call_args.args[1])

    def test_token_receipt_uses_latest_matching_thread_total_and_discards_extras(self) -> None:
        transport = _ScriptedTransport(completed_items=[])
        usage = dict(inputTokens=100, cachedInputTokens=80, outputTokens=10,
                     reasoningOutputTokens=4, totalTokens=110, private="must-not-leak")
        transport._events[1:1] = [
            {"method":"thread/tokenUsage/updated", "params":{
                "threadId":"other-thread", "turnId":"turn-1", "tokenUsage":{"total":usage}}},
            {"method":"thread/tokenUsage/updated", "params":{
                "threadId":"thread-1", "turnId":"turn-1", "tokenUsage":{"total":usage}}},
        ]
        with patch("app.codex_appserver.read_codex_version", return_value=CodexVersion.parse("codex-cli 0.147.0")):
            client = CodexAppServerClient(transport_factory=lambda **_kwargs: transport)
            receipt = client.send_text(thread_id="thread-1", client_message_id="message-1", text="test")
        self.assertEqual(receipt.thread_token_usage["total_tokens"], 110)
        self.assertNotIn("must-not-leak", json.dumps(receipt.as_dict()))

    def test_missing_or_bad_token_telemetry_does_not_break_delivery(self) -> None:
        for raw in (None, "invalid", {"total": {"inputTokens": -1}}):
            transport = _ScriptedTransport(completed_items=[])
            transport._events.insert(1, {"method":"thread/tokenUsage/updated", "params":{
                "threadId":"thread-1", "turnId":"turn-1", "tokenUsage":raw}})
            with self.subTest(raw=raw), patch("app.codex_appserver.read_codex_version", return_value=CodexVersion.parse("codex-cli 0.147.0")):
                client = CodexAppServerClient(transport_factory=lambda **_kwargs: transport)
                receipt = client.send_text(thread_id="thread-1", client_message_id="message-1", text="test")
            self.assertTrue(receipt.delivered)
            self.assertIsNone(receipt.thread_token_usage)

    def test_turn_passes_structured_output_without_changing_model(self) -> None:
        transport = _ScriptedTransport(completed_items=[])
        with patch("app.codex_appserver.read_codex_version", return_value=CodexVersion.parse("codex-cli 0.147.0")):
            client = CodexAppServerClient(transport_factory=lambda **_kwargs: transport)
            schema = {"type": "object", "properties": {"accepted": {"type": "boolean"}}}
            with patch.object(transport, "request", wraps=transport.request) as request:
                receipt = client.send_text(thread_id="thread-1", client_message_id="message-1",
                                           text="Handoff", model="gpt-6-luna", output_schema=schema)
            params = request.call_args.args[1]
            self.assertEqual(params["outputSchema"], schema)
            self.assertEqual(params["model"], "gpt-6-luna")
            self.assertTrue(receipt.delivered)

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
            return {"userAgent": "codex_cli_rs/0.166.0 (synthetic)"}
        if method == "turn/start":
            return {"turn": {"id": "turn-1"}}
        if method in {"thread/start", "thread/resume"}:
            return {"thread": {"id": "thread-1"}}
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
