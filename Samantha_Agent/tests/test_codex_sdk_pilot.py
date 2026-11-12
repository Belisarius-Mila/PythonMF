"""05/P1 contracts: synthetic only, no live socket, role activation or inference.

Run SDK cases in this worktree's optional isolated environment. Tests labelled
characterization deliberately document existing gaps rather than fixing them.
"""

from __future__ import annotations

import copy
import importlib.util
import inspect
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from app.codex_appserver import AppServerContractError, CodexAppServerClient, StdioAppServerTransport
from app.codex_sdk_pilot import (
    PilotContractError, attempt_once, evaluate_events, history_pages,
    proxy_config, resume_existing, synthetic_config, synthetic_codex,
)


ROOT = Path(__file__).resolve().parents[1]
SDK_AVAILABLE = importlib.util.find_spec("openai_codex") is not None
SCHEMA_DIR = ROOT / ".venv" / "p1-cli-schema" / "v2"


def event(method, **params):
    return {"method": method, "params": {"threadId": "t", "turnId": "v", **params}}


def transcript():
    return [event("turn/started", turn={"id": "v"}),
            event("item/completed", item={"type": "userMessage", "id": "u", "clientId": "c"}),
            event("item/completed", item={"type": "agentMessage", "id": "a",
                                         "phase": "final_answer", "text": "final"}),
            event("item/completed", item={"type": "agentMessage", "id": "b",
                                         "phase": "commentary", "text": "progress"}),
            event("turn/completed", turn={"id": "v", "status": "completed", "items": []})]


def evaluate(events, **kwargs):
    return evaluate_events(events, thread_id="t", turn_id="v", client_id="c", **kwargs)


class MemoryTransport:
    def __init__(self, events):
        self.events = copy.deepcopy(events)
        self.calls = []

    def request(self, method, params):
        self.calls.append((method, params))
        return {"turn": {"id": "v"}} if method == "turn/start" else {"thread": {"id": "t"}}

    def receive(self, predicate, **_kwargs):
        while self.events:
            candidate = self.events.pop(0)
            if predicate(candidate):
                return candidate
        raise ConnectionError("synthetic disconnect")


def current_client(events):
    client = CodexAppServerClient.__new__(CodexAppServerClient)
    client.transport = MemoryTransport(events)
    return client


class AcceptanceContractTests(unittest.TestCase):
    def test_final_answer_wins_over_later_commentary_and_other_threads(self):
        events = transcript()
        foreign = copy.deepcopy(events[2])
        foreign["params"]["threadId"] = "other"
        events.insert(3, foreign)
        self.assertEqual(evaluate(events).answer, "final")

    def test_required_delivery_evidence(self):
        for missing in (0, 1, 2, 4):
            events = transcript()
            events.pop(missing)
            with self.subTest(missing=missing):
                self.assertEqual(evaluate(events).state, "delivery_unknown")

    def test_phase_less_is_an_explicit_compatibility_decision(self):
        events = transcript()
        events[2]["params"]["item"].pop("phase")
        self.assertEqual(evaluate(events).state, "delivery_unknown")
        self.assertEqual(evaluate(events, allow_legacy_phase=True).answer, "final")

    def test_final_input_is_authoritative_even_if_stream_matched(self):
        events = transcript()
        events[-1]["params"]["turn"]["items"] = [{"type": "userMessage", "clientId": "other"}]
        self.assertEqual(evaluate(events).state, "delivery_unknown")

    def test_duplicate_item_id_is_idempotent_but_conflict_is_rejected(self):
        events = transcript()
        events.insert(2, copy.deepcopy(events[1]))
        self.assertEqual(evaluate(events).state, "completed")
        events[2]["params"]["item"]["clientId"] = "other"
        self.assertEqual(evaluate(events).state, "delivery_unknown")

    def test_multiple_users_or_finals_are_ambiguous(self):
        for index in (1, 2):
            events = transcript()
            other = copy.deepcopy(events[index])
            other["params"]["item"]["id"] += "-other"
            events.insert(3, other)
            self.assertEqual(evaluate(events).state, "delivery_unknown")

    def test_structured_failure_and_interrupt_are_not_success(self):
        for status in ("failed", "interrupted"):
            events = transcript()
            detail = {"message": "synthetic", "codexErrorInfo": {"httpConnectionFailed": {"httpStatusCode": 503}}}
            events[-1]["params"]["turn"].update(status=status, error=detail)
            result = evaluate(events)
            self.assertEqual(result.state, status)
            self.assertEqual(result.error["error"]["codexErrorInfo"], detail["codexErrorInfo"])
            self.assertIsNone(result.answer)

    def test_retry_hint_and_missing_completion_remain_unknown(self):
        events = transcript()[:-1]
        events.append(event("error", error={"message": "synthetic", "codexErrorInfo": "serverOverloaded"}, willRetry=True))
        result = evaluate(events)
        self.assertEqual(result.state, "delivery_unknown")
        self.assertTrue(result.error["willRetry"])

    def test_completed_snapshot_can_supply_output_when_stream_item_is_missing(self):
        events = transcript()
        final = events.pop(2)["params"]["item"]
        events[-1]["params"]["turn"]["items"] = [final]
        self.assertEqual(evaluate(events).answer, "final")

    def test_duplicate_terminal_event_is_ambiguous(self):
        events = transcript()
        events.append(copy.deepcopy(events[-1]))
        self.assertEqual(evaluate(events).state, "delivery_unknown")

    def test_uncertain_result_never_resends_even_on_second_invocation(self):
        ledger = {}
        action = Mock(side_effect=ConnectionError("unknown"))
        with self.assertRaises(ConnectionError):
            attempt_once(ledger, "c", action)
        with self.assertRaises(PilotContractError):
            attempt_once(ledger, "c", action)
        self.assertEqual(action.call_count, 1)
        self.assertEqual(ledger["c"], "delivery_unknown")

    def test_reservation_precedes_action_and_success_does_not_authorize_repeat(self):
        ledger = {}
        self.assertEqual(attempt_once(ledger, "c", lambda: ledger["c"]), "pending")
        with self.assertRaises(PilotContractError):
            attempt_once(ledger, "c", Mock())

    def test_bounded_pagination_for_turns_and_items(self):
        for method in ("thread/turns/list", "thread/items/list"):
            request = Mock(side_effect=[{"data": [1], "nextCursor": "opaque"}, {"data": [2], "nextCursor": None}])
            self.assertEqual(history_pages(request, method=method, thread_id="t"), [1, 2])
            self.assertEqual(request.call_args.args[1]["cursor"], "opaque")
            self.assertNotIn("includeTurns", request.call_args.args[1])

    def test_bad_page_cursor_cycle_and_page_budget_fail_without_full_history_fallback(self):
        for pages in ([{"data": "bad"}], [{"data": [], "nextCursor": "cycle"}] * 2,
                      [{"data": [], "nextCursor": "one"}, {"data": [], "nextCursor": "two"}]):
            request = Mock(side_effect=pages)
            with self.assertRaises(PilotContractError):
                history_pages(request, method="thread/turns/list", thread_id="t", max_pages=2)
            self.assertTrue(all(c.args[0] == "thread/turns/list" for c in request.call_args_list))


class CurrentClientRegressionTests(unittest.TestCase):
    def test_current_resume_excludes_turns(self):
        client = current_client([])
        client.resume_thread("t", cwd=ROOT)
        self.assertIs(client.transport.calls[0][1]["excludeTurns"], True)

    def test_current_response_uses_final_answer_before_later_commentary(self):
        client = current_client(transcript())
        receipt = client.send_text(thread_id="t", text="synthetic", client_message_id="c")
        self.assertTrue(receipt.delivered)
        self.assertEqual(receipt.answer, "final")

    def test_current_rpc_exception_preserves_error_code_and_data(self):
        transport = StdioAppServerTransport.__new__(StdioAppServerTransport)
        transport._init_dispatcher(timeout=1)
        transport._send = Mock(side_effect=lambda message: transport._dispatcher.feed(
            {"id": message["id"], "error": {"code": -32001, "message": "synthetic", "data": {"reason": "busy"}}},
            generation=transport._dispatcher.generation))
        with self.assertRaises(AppServerContractError) as raised:
            transport.request("turn/start", {})
        self.assertEqual(raised.exception.code, -32001)
        self.assertEqual(raised.exception.data, {"reason": "busy"})
        transport._send.assert_called_once()

    def test_current_disconnect_after_start_does_not_start_again(self):
        client = current_client(transcript()[:-1])
        with self.assertRaises(ConnectionError):
            client.send_text(thread_id="t", text="synthetic", client_message_id="c")
        self.assertEqual(sum(c[0] == "turn/start" for c in client.transport.calls), 1)


@unittest.skipUnless(SDK_AVAILABLE, "Optional SDK: install only in an isolated environment")
class SdkSyntheticTests(unittest.TestCase):
    def resume(self, codex):
        return resume_existing(codex, thread_id="synthetic-thread", cwd=ROOT,
                               model="synthetic-approved-model", provider="openai")

    def test_real_sdk_resume_preserves_identity_model_policy_and_history_option(self):
        from openai_codex import Codex
        with synthetic_codex() as codex:
            with patch.object(codex._client, "_write_message", wraps=codex._client._write_message) as wire:
                self.assertEqual(self.resume(codex).id, "synthetic-thread")
            params = next(c.args[0]["params"] for c in wire.call_args_list if c.args[0].get("method") == "thread/resume")
            self.assertEqual(params["excludeTurns"], True)
            self.assertEqual(params["model"], "synthetic-approved-model")
            self.assertEqual(params["modelProvider"], "openai")
            self.assertEqual(params["sandbox"], "read-only")
            self.assertEqual(params["approvalPolicy"], "never")
            self.assertEqual(params["cwd"], str(ROOT))

    def test_wrong_thread_does_not_fall_back_to_start(self):
        from openai_codex import Codex
        with synthetic_codex("wrong_thread") as codex:
            with self.assertRaises(PilotContractError):
                self.resume(codex)

    def test_sdk_final_phase_legacy_phase_and_commentary_only(self):
        from openai_codex import Codex
        for scenario, expected in (("complete", '{"ok":true}'), ("legacy_phase", '{"ok":true}'), ("commentary_only", None)):
            with self.subTest(scenario=scenario), synthetic_codex(scenario) as codex:
                result = self.resume(codex).run("synthetic")
                self.assertEqual(result.final_response, expected)

    def test_sdk_passes_schema_model_effort_and_deny_policy_without_validating_json(self):
        from openai_codex import ApprovalMode, Codex, Sandbox
        # Deliberately incompatible schema: SDK forwards it; it does not locally validate result text.
        schema = {"type": "object", "required": ["missing"], "properties": {"missing": {"type": "string"}}}
        with synthetic_codex() as codex:
            thread = self.resume(codex)
            with patch.object(codex._client, "_write_message", wraps=codex._client._write_message) as wire:
                result = thread.run("synthetic", model="synthetic-approved-model", effort="low",
                                    sandbox=Sandbox.read_only, approval_mode=ApprovalMode.deny_all, output_schema=schema)
            params = next(c.args[0]["params"] for c in wire.call_args_list if c.args[0].get("method") == "turn/start")
            self.assertEqual(params["outputSchema"], schema)
            self.assertEqual(params["model"], "synthetic-approved-model")
            self.assertEqual(params["effort"], "low")
            self.assertEqual(params["sandboxPolicy"]["type"], "readOnly")
            self.assertEqual(params["approvalPolicy"], "never")
            self.assertNotIn("missing", json.loads(result.final_response))

    def test_rpc_error_retains_code_and_structured_data_without_retry(self):
        from openai_codex import Codex, JsonRpcError
        with synthetic_codex("rpc_error") as codex:
            with patch.object(codex._client, "_write_message", wraps=codex._client._write_message) as wire:
                with self.assertRaises(JsonRpcError) as raised:
                    self.resume(codex)
            self.assertEqual(raised.exception.code, -32001)
            self.assertEqual(raised.exception.data["retryAfterMs"], 25)
            self.assertEqual(sum(c.args[0].get("method") == "thread/resume" for c in wire.call_args_list), 1)

    def test_disconnect_before_after_ack_and_lost_completion_never_replay(self):
        from openai_codex import Codex
        from openai_codex.errors import TransportClosedError
        for scenario in ("disconnect_before_ack", "disconnect_after_ack", "lost_completion"):
            with self.subTest(scenario=scenario), synthetic_codex(scenario) as codex:
                thread = self.resume(codex)
                ledger = {}
                with patch.object(codex._client, "_write_message", wraps=codex._client._write_message) as wire:
                    with self.assertRaises(TransportClosedError):
                        attempt_once(ledger, "c", lambda: thread.run("synthetic"))
                    with self.assertRaises(PilotContractError):
                        attempt_once(ledger, "c", lambda: thread.run("synthetic"))
                self.assertEqual(sum(c.args[0].get("method") == "turn/start" for c in wire.call_args_list), 1)
                self.assertEqual(ledger["c"], "delivery_unknown")

    def test_interrupted_sdk_result_is_not_completed_even_with_text(self):
        from openai_codex import Codex
        with synthetic_codex("interrupted") as codex:
            result = self.resume(codex).run("synthetic")
            self.assertEqual(result.status.value, "interrupted")

    def test_failed_high_level_run_loses_typed_turn_error(self):
        from openai_codex import Codex
        with synthetic_codex("failed") as codex:
            with self.assertRaisesRegex(RuntimeError, "synthetic failure") as raised:
                self.resume(codex).run("synthetic")
            self.assertFalse(hasattr(raised.exception, "codex_error_info"))

    def test_unknown_notification_keeps_raw_payload_but_run_loses_output(self):
        from openai_codex import Codex
        from openai_codex.models import UnknownNotification
        with synthetic_codex("malformed_item") as codex:
            handle = self.resume(codex).turn("synthetic")
            unknown = [e.payload for e in handle.stream() if isinstance(e.payload, UnknownNotification)]
            self.assertTrue(any(e.params.get("item", {}).get("phase") == "final_answer" for e in unknown))
        with synthetic_codex("malformed_item") as codex:
            self.assertIsNone(self.resume(codex).run("synthetic").final_response)

    def test_public_sdk_has_no_caller_client_id_or_native_socket_and_defaults_differ(self):
        from dataclasses import fields
        from openai_codex import ApprovalMode, Codex, CodexConfig, Thread
        from openai_codex.client import CodexClient
        self.assertNotIn("client_user_message_id", inspect.signature(Thread.turn).parameters)
        self.assertNotIn("socket_path", {f.name for f in fields(CodexConfig)})
        self.assertEqual(inspect.signature(Codex.thread_start).parameters["approval_mode"].default, ApprovalMode.auto_review)
        client = CodexClient()
        # No start(): characterize the handler without launching any executable.
        self.assertEqual(client._default_approval_handler("item/commandExecution/requestApproval", {}), {"decision": "accept"})

    def test_low_level_sdk_accepts_client_id_and_retains_typed_event_failure(self):
        from openai_codex.client import CodexClient
        from openai_codex.generated.v2_all import TurnCompletedNotification
        client = CodexClient(synthetic_config("failed"), approval_handler=lambda *_: {"decision": "decline"})
        process = None
        try:
            client.start()
            process = client._proc
            client.initialize()
            client.thread_resume("synthetic-thread", {"cwd": str(ROOT), "excludeTurns": True, "approvalPolicy": "never"})
            with patch.object(client, "_write_message", wraps=client._write_message) as wire:
                response = client.turn_start("synthetic-thread", "synthetic", params={"clientUserMessageId": "caller-id", "approvalPolicy": "never"})
            self.assertEqual(wire.call_args.args[0]["params"]["clientUserMessageId"], "caller-id")
            completed = None
            while completed is None:
                notification = client.next_turn_notification(response.turn.id)
                if isinstance(notification.payload, TurnCompletedNotification):
                    completed = notification.payload
            self.assertIsNotNone(completed.turn.error.codex_error_info)
        finally:
            client.close()
            if process is not None:
                for pipe in (process.stdin, process.stdout, process.stderr):
                    pipe.close()

    def test_shared_proxy_is_config_only_without_spawning_or_connecting(self):
        from openai_codex.client import CodexClient
        with patch("subprocess.Popen") as popen:
            config = proxy_config(codex_binary=Path("/synthetic/codex"), socket_path=Path("/synthetic/shared.sock"), cwd=ROOT)
            self.assertEqual(config.launch_args_override, ("/synthetic/codex", "app-server", "proxy", "--sock", "/synthetic/shared.sock"))
            CodexClient(config).close()
            popen.assert_not_called()
        with self.assertRaises(PilotContractError):
            proxy_config(codex_binary=Path("codex"), socket_path=Path("/synthetic/shared.sock"), cwd=ROOT)

    def test_proxy_launch_uses_only_explicit_socket_and_close_only_terminates_child(self):
        from openai_codex.client import CodexClient
        config = proxy_config(codex_binary=Path("/synthetic/codex"), socket_path=Path("/synthetic/shared.sock"), cwd=ROOT)
        client = CodexClient(config, approval_handler=lambda *_: {"decision": "decline"})
        with patch("subprocess.Popen") as popen, patch.object(client, "_start_reader_thread"), patch.object(client, "_start_stderr_drain_thread"):
            client.start()
            self.assertEqual(popen.call_args.args[0], list(config.launch_args_override))
            client.close()
            popen.return_value.terminate.assert_called_once()
            popen.assert_called_once()

    def test_sdk_raw_requests_support_bounded_history_pagination(self):
        from openai_codex.generated.v2_all import ThreadTurnsListResponse, ThreadItemsListResponse
        with synthetic_codex() as codex:
            for method, response_model in (("thread/turns/list", ThreadTurnsListResponse),
                                           ("thread/items/list", ThreadItemsListResponse)):
                def request(name, params):
                    return codex._client.request(name, params, response_model=response_model).model_dump(by_alias=True, mode="json")
                rows = history_pages(request, method=method, thread_id="synthetic-thread")
                self.assertEqual([r.get("item", r)["id"] for r in rows], ["first", "second"])

    def test_old_runtime_rejects_history_option_before_resume_rpc(self):
        from openai_codex import Codex, CodexError
        with synthetic_codex(cli_version="0.150.0") as codex:
            with patch.object(codex._client, "_write_message", wraps=codex._client._write_message) as wire:
                with self.assertRaises(CodexError):
                    self.resume(codex)
            self.assertFalse(any(c.args[0].get("method") == "thread/resume" for c in wire.call_args_list))

    def test_approved_role_snapshot_is_forwarded_without_fallback_or_activation(self):
        roles_path = ROOT / "config/agent_roles.json"
        before = roles_path.read_bytes()
        role = json.loads(before)["roles"]["simple_developer"]
        model = role["preferred_model"]
        approved = next(r for r in role["approved_models"] if r["model"] == model)
        with synthetic_codex() as codex:
            with patch.object(codex._client, "_write_message", wraps=codex._client._write_message) as wire:
                thread = resume_existing(codex, thread_id="synthetic-thread", cwd=ROOT, model=model, provider="openai")
                thread.run("synthetic", model=model, effort=approved["reasoning_effort"])
            params = [c.args[0]["params"] for c in wire.call_args_list if c.args[0].get("method") == "turn/start"][0]
            self.assertEqual(params["model"], model)
            self.assertEqual(params["effort"], approved["reasoning_effort"])
        self.assertEqual(roles_path.read_bytes(), before)

    def test_sdk_close_leaves_pipes_open_characterization(self):
        from openai_codex import Codex
        codex = Codex(synthetic_config())
        process = codex._client._proc
        try:
            codex.close()
            self.assertIsNotNone(process.poll())
            self.assertFalse(process.stdout.closed)
            self.assertFalse(process.stderr.closed)
        finally:
            for pipe in (process.stdin, process.stdout, process.stderr):
                pipe.close()


@unittest.skipUnless(SCHEMA_DIR.is_dir() and importlib.util.find_spec("jsonschema"), "Generate local CLI schema for version-specific checks")
class InstalledCliSchemaTests(unittest.TestCase):
    def test_synthetic_wire_messages_validate_against_installed_cli_schema(self):
        import jsonschema
        messages = [{"id": 1, "method": "initialize"},
                    {"id": 2, "method": "thread/resume", "params": {"cwd": str(ROOT), "approvalPolicy": "never", "excludeTurns": True}},
                    {"id": 3, "method": "turn/start", "params": {}}]
        process = subprocess.run([sys.executable, "-I", str(ROOT / "scripts/codex_sdk_synthetic_peer.py"), "complete", "0.166.0"],
                                 input="\n".join(json.dumps(m) for m in messages) + "\n", capture_output=True, text=True, timeout=10, check=True)
        names = {"turn/started": "TurnStartedNotification", "item/completed": "ItemCompletedNotification", "turn/completed": "TurnCompletedNotification"}
        for line in process.stdout.splitlines():
            message = json.loads(line)
            name = names.get(message.get("method"))
            payload = message.get("params")
            if message.get("id") == 2:
                name, payload = "ThreadResumeResponse", message["result"]
            if name:
                schema = json.loads((SCHEMA_DIR / f"{name}.json").read_text())
                jsonschema.validate(payload, schema)

    def test_installed_cli_has_exclude_turns_pagination_phase_errors_and_client_id(self):
        def schema(name):
            return json.loads((SCHEMA_DIR / f"{name}.json").read_text())
        self.assertIn("excludeTurns", schema("ThreadResumeParams")["properties"])
        self.assertNotIn("includeTurns", schema("ThreadResumeParams")["properties"])
        for name in ("ThreadTurnsListParams", "ThreadItemsListParams"):
            self.assertIn("cursor", schema(name)["properties"])
        self.assertIn("clientUserMessageId", schema("TurnStartParams")["properties"])
        self.assertIn("willRetry", schema("ErrorNotification")["properties"])
        phases = schema("ThreadResumeResponse")["definitions"]["MessagePhase"]["oneOf"]
        self.assertIn("final_answer", [phase["enum"][0] for phase in phases])

    def test_history_requests_match_both_cli_schemas(self):
        import jsonschema
        for folder in (SCHEMA_DIR, ROOT / ".venv/p1-sdk-cli-schema/v2"):
            if not folder.exists():
                self.skipTest("Generate bundled SDK runtime schema too")
            for method, name in (("thread/turns/list", "ThreadTurnsListParams"),
                                 ("thread/items/list", "ThreadItemsListParams")):
                def request(_method, params):
                    jsonschema.validate(params, json.loads((folder / f"{name}.json").read_text()))
                    return {"data": [], "nextCursor": None}
                history_pages(request, method=method, thread_id="synthetic-thread")


if __name__ == "__main__":
    unittest.main()
