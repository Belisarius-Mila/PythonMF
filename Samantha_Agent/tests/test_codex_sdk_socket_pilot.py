"""05/P1-C: real SDK and CLI proxy, exclusively synthetic Unix endpoints.

Requires the optional worktree SDK environment and a local CLI executable.
No daemon command, shared socket, model inference or live runtime is used.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import threading
import unittest
from contextlib import ExitStack
from pathlib import Path

from app.codex_sdk_pilot import PilotContractError
from app.codex_sdk_socket_pilot import FixtureProxyClient, deny_approval
from scripts.codex_sdk_socket_fixture import SyntheticSocket


ROOT = Path(__file__).resolve().parents[1]
CLI = shutil.which("codex")
AVAILABLE = bool(CLI and importlib.util.find_spec("openai_codex")
                 and importlib.util.find_spec("websockets"))
SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}},
          "required": ["ok"], "additionalProperties": False}


@unittest.skipUnless(AVAILABLE, "Requires optional isolated SDK, websockets and local CLI")
class SocketPilotTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        # macOS Unix socket paths must fit sun_path. System tmp is too long when
        # combined with its randomized path; this is our own disposable fixture.
        self.directory = Path(self.stack.enter_context(tempfile.TemporaryDirectory(prefix="p1c-", dir="/tmp")))

    def fixture(self, **kwargs):
        return self.stack.enter_context(SyntheticSocket(self.directory, **kwargs))

    def proxy(self, timeout=3):
        return self.stack.enter_context(FixtureProxyClient(
            codex_binary=Path(CLI), fixture_directory=self.directory, cwd=ROOT, timeout=timeout,
        ))

    def resume(self, proxy):
        return proxy.call(lambda: proxy.client.thread_resume("fixture-thread", {
            "excludeTurns": True, "cwd": str(ROOT), "model": "synthetic-approved-model",
            "modelProvider": "openai", "approvalPolicy": "never", "sandbox": "read-only",
            "baseInstructions": "synthetic role instructions", "developerInstructions": "synthetic constraints",
        }))

    def start(self, proxy, client_id="fixture-message"):
        return proxy.send_once(client_id, lambda: proxy.client.turn_start("fixture-thread", "synthetic only", {
            "clientUserMessageId": client_id, "model": "synthetic-approved-model",
            "effort": "low", "outputSchema": SCHEMA, "approvalPolicy": "never",
            "sandboxPolicy": {"type": "readOnly"},
        }))

    def test_two_clients_share_thread_and_closing_one_preserves_listener(self):
        fixture = self.fixture()
        inode = fixture.path.stat().st_ino
        first, second = self.proxy(), self.proxy()
        results = []
        workers = [threading.Thread(target=lambda p=p: results.append(self.resume(p).thread.id)) for p in (first, second)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=5)
        self.assertEqual(results, ["fixture-thread", "fixture-thread"])
        self.assertNotEqual(first.process.pid, second.process.pid)
        self.assertTrue(all(p.process.args[1:4] == ["app-server", "proxy", "--sock"] for p in (first, second)))
        first.close()
        self.assertIsNotNone(first.process.poll())
        self.assertIsNone(second.process.poll())
        self.assertEqual(second.call(lambda: second.client.thread_read("fixture-thread")).thread.id, "fixture-thread")
        third = self.proxy()  # Explicit replacement connection, no automatic replay.
        self.assertEqual(self.resume(third).thread.id, "fixture-thread")
        self.assertEqual(fixture.path.stat().st_ino, inode)
        self.assertTrue(fixture.thread.is_alive())
        self.assertFalse(any(method in {"thread/start", "thread/fork", "turn/start"} for method, _ in fixture.calls))
        for method, params in fixture.calls:
            if method == "thread/resume":
                self.assertIs(params["excludeTurns"], True)
                self.assertEqual(params["approvalPolicy"], "never")
                self.assertEqual(params["sandbox"], "read-only")
                self.assertEqual(params["model"], "synthetic-approved-model")
                self.assertEqual(params["modelProvider"], "openai")
                self.assertEqual(params["cwd"], str(ROOT))
                self.assertEqual(params["baseInstructions"], "synthetic role instructions")
                self.assertEqual(params["developerInstructions"], "synthetic constraints")
        self.assertEqual(fixture.directory.stat().st_mode & 0o777, 0o700)
        self.assertEqual(fixture.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(fixture.errors, [])

    def test_wire_client_id_roles_schema_events_and_unknown_event(self):
        fixture = self.fixture()
        proxy = self.proxy()
        self.resume(proxy)
        self.start(proxy)
        self.assertEqual(proxy.ledger["fixture-message"], "awaiting_delivery_evidence")
        receipt = proxy.observe_delivery("fixture-message", thread_id="fixture-thread", turn_id="fixture-turn")
        self.assertEqual(receipt.state, "completed")
        self.assertEqual(json.loads(receipt.answer), {"ok": True})
        self.assertEqual(proxy.ledger["fixture-message"], "completed")
        # Reference evaluator confirms delivery; transport acknowledgement alone didn't.
        turn_params = [p for m, p in fixture.calls if m == "turn/start"]
        self.assertEqual(len(turn_params), 1)
        self.assertEqual(turn_params[0]["clientUserMessageId"], "fixture-message")
        self.assertEqual(turn_params[0]["outputSchema"], SCHEMA)
        self.assertEqual(turn_params[0]["effort"], "low")
        self.assertEqual(turn_params[0]["model"], "synthetic-approved-model")
        self.assertEqual(turn_params[0]["sandboxPolicy"], {"type": "readOnly"})
        unknown = proxy.call(proxy.client.next_notification)
        self.assertEqual(unknown.method, "fixture/futureEvent")
        self.assertEqual(unknown.payload.params["value"], {"retained": True})
        observer = self.proxy()
        shared = observer.call(lambda: observer.client.thread_read("fixture-thread"))
        self.assertEqual(shared.thread.preview, "synthetic completed")
        with self.assertRaises(PilotContractError):
            self.start(proxy)
        self.assertEqual(sum(m == "turn/start" for m, _ in fixture.calls), 1)

    def test_command_and_file_approvals_are_explicitly_declined(self):
        fixture = self.fixture()
        proxy = self.proxy()
        for method in ("item/commandExecution/requestApproval", "item/fileChange/requestApproval"):
            proxy.call(lambda: proxy.client._request_raw("fixture/approval", {"method": method}))
        # A read after both requests is a deterministic barrier on the same stream.
        proxy.call(lambda: proxy.client.thread_read("fixture-thread"))
        self.assertEqual([m["result"] for m in fixture.approvals], [{"decision": "decline"}] * 2)

    def test_unknown_server_request_closes_reader_without_approval(self):
        fixture = self.fixture()
        proxy = self.proxy()
        with self.assertRaises(PilotContractError):
            proxy.call(lambda: proxy.client._request_raw("fixture/approval", {"method": "fixture/unknownApproval"}))
        self.assertEqual(fixture.approvals, [])

    def test_structured_overload_does_not_retry(self):
        from openai_codex.errors import JsonRpcError

        fixture = self.fixture(scenario="rpc_error")
        proxy = self.proxy()
        with self.assertRaises(JsonRpcError) as caught:
            self.start(proxy)
        self.assertEqual(caught.exception.code, -32001)
        self.assertEqual(caught.exception.data["retryAfterMs"], 1)
        with self.assertRaises(PilotContractError):
            self.start(proxy)
        self.assertEqual(proxy.ledger["fixture-message"], "delivery_unknown")
        self.assertEqual(sum(m == "turn/start" for m, _ in fixture.calls), 1)

    def test_disconnect_before_ack_stays_unknown_without_second_action(self):
        fixture = self.fixture(scenario="disconnect_before_ack")
        proxy = self.proxy()
        proxy.timeout = 0.6  # Bound the tested operation, not CLI/SDK initialization.
        with self.assertRaises(Exception):
            self.start(proxy)
        with self.assertRaises(PilotContractError):
            self.start(proxy)
        self.assertEqual(proxy.ledger["fixture-message"], "delivery_unknown")
        self.assertEqual(sum(m == "turn/start" for m, _ in fixture.calls), 1)
        self.assertTrue(fixture.thread.is_alive())

    def test_silent_rpc_deadline_kills_only_proxy_and_never_resends(self):
        fixture = self.fixture(scenario="silent_before_ack")
        proxy = self.proxy()
        self.assertEqual(proxy.initialized.serverInfo.name, "synthetic")
        self.assertFalse(fixture.started_turn.is_set())
        self.assertEqual(proxy.ledger, {})
        proxy.timeout = 0.5  # Keep the strict RPC deadline after a completed handshake.
        with self.assertRaisesRegex(PilotContractError, "delivery_unknown"):
            self.start(proxy)
        self.assertIsNotNone(proxy.process.poll())
        self.assertTrue(fixture.thread.is_alive())
        observer = self.proxy()
        self.assertEqual(self.resume(observer).thread.id, "fixture-thread")
        with self.assertRaises(PilotContractError):
            self.start(proxy)
        self.assertEqual(sum(m == "turn/start" for m, _ in fixture.calls), 1)

    def test_close_during_turn_then_explicit_reconnect_never_cancels_or_replays(self):
        fixture = self.fixture(scenario="silent_after_ack")
        proxy = self.proxy()
        self.start(proxy)
        proxy.close()
        self.assertEqual(proxy.ledger["fixture-message"], "delivery_unknown")
        observer = self.proxy()
        self.assertEqual(self.resume(observer).thread.id, "fixture-thread")
        self.assertTrue(fixture.thread.is_alive())
        self.assertEqual(sum(m == "turn/start" for m, _ in fixture.calls), 1)
        self.assertFalse(any(m in {"turn/interrupt", "thread/start", "thread/fork"} for m, _ in fixture.calls))

    def test_silent_or_disconnected_completion_is_not_delivery(self):
        for scenario in ("disconnect_after_ack", "silent_after_ack", "retry_hint"):
            with self.subTest(scenario=scenario), ExitStack() as stack:
                directory = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix="p1c-", dir="/tmp")))
                fixture = stack.enter_context(SyntheticSocket(directory, scenario=scenario))
                proxy = stack.enter_context(FixtureProxyClient(codex_binary=Path(CLI), fixture_directory=directory,
                                                            cwd=ROOT))
                proxy.timeout = 0.6
                self.start(proxy)
                receipt = proxy.observe_delivery("fixture-message", thread_id="fixture-thread", turn_id="fixture-turn")
                self.assertEqual(receipt.state, "delivery_unknown")
                self.assertEqual(proxy.ledger["fixture-message"], "delivery_unknown")
                if scenario == "retry_hint":
                    self.assertIs(receipt.error["willRetry"], True)
                    self.assertEqual(receipt.error["error"]["codexErrorInfo"],
                                     {"httpConnectionFailed": {"httpStatusCode": 503}})
                with self.assertRaises(PilotContractError):
                    self.start(proxy)
                self.assertEqual(sum(m == "turn/start" for m, _ in fixture.calls), 1)

    def test_proxy_cannot_speak_current_websocket_transport(self):
        fixture = self.fixture(websocket=True)
        with self.assertRaisesRegex(PilotContractError, "Deadline expired"):
            self.proxy(timeout=1)
        self.assertEqual(fixture.calls, [])  # No initialize RPC reached the WebSocket handler.
        self.assertTrue(fixture.thread.is_alive())
        # Control: our CURRENT production transport works against this very same fixture.
        from app.codex_appserver import UnixSocketAppServerTransport

        transport = UnixSocketAppServerTransport(socket_path=fixture.path, timeout=2)
        try:
            response = transport.request("initialize", {"clientInfo": {"name": "p1c-control", "version": "0"}})
            self.assertEqual(response["serverInfo"]["name"], "synthetic")
        finally:
            transport.close()
        self.assertEqual([m for m, _ in fixture.calls], ["initialize"])

    def test_concurrent_duplicate_is_blocked_while_first_request_is_pending(self):
        fixture = self.fixture(scenario="silent_before_ack")
        proxy = self.proxy()
        proxy.timeout = 0.6
        failures = []

        def first_attempt():
            try:
                self.start(proxy)
            except PilotContractError as exc:
                failures.append(exc)

        worker = threading.Thread(target=first_attempt)
        worker.start()
        self.assertTrue(fixture.started_turn.wait(timeout=2))
        with self.assertRaisesRegex(PilotContractError, "Already attempted"):
            self.start(proxy)
        worker.join(timeout=5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(len(failures), 1)
        self.assertEqual(proxy.ledger["fixture-message"], "delivery_unknown")
        self.assertEqual(sum(m == "turn/start" for m, _ in fixture.calls), 1)


class ApprovalPolicyTests(unittest.TestCase):
    def test_unknown_requests_fail_closed(self):
        with self.assertRaises(PilotContractError):
            deny_approval("item/permissions/requestApproval", {})


if __name__ == "__main__":
    unittest.main()
