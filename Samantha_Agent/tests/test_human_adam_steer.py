from __future__ import annotations

import json
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from app.codex_appserver import CodexAppServerClient, CodexVersion, AppServerError, AppServerSteerRejected
from app.communication.human_adam_work import WorkController, WorkReservation, WorkConflict, WorkUnavailable
from app.communication.session_hub import CanonicalSessionHub
from app.work_repository import JsonWorkRepository
from tests.test_codex_appserver_dispatch import MemoryTransport


class SteerClient(CodexAppServerClient):
    """Production client/dispatcher and input ledger; only wire responses are synthetic."""
    def __init__(self, *, version="0.167.0"):
        self.connection_id = "synthetic-connection"
        self.version = self.server_version = CodexVersion.parse("codex-cli " + version)
        self.process_id = 0
        self.transport = MemoryTransport(self.respond, timeout=2)
        self.users = []
        self.started = threading.Event()
        self.steer_entered = threading.Event()
        self.steer_release = None
        self.mode = "ok"
        self.thread = "thread-current"
        self.turn = "turn-current"
        self.started_kwargs = {}

    def start_thread(self, **kwargs):
        self.started_kwargs = kwargs
        return self.thread

    def resume_thread(self, thread_id, **kwargs):
        return thread_id

    def respond(self, message):
        method, params = message["method"], message["params"]
        if method == "turn/start":
            self.transport.feed({"id": message["id"], "result": {"turn": {"id": self.turn}}})
            self.transport.feed({"method": "turn/started", "params": {"threadId": self.thread, "turn": {"id": self.turn}}})
            item = {"id": "original-item", "type": "userMessage", "clientId": params["clientUserMessageId"]}
            self.users.append(item)
            self.transport.feed({"method": "item/completed", "params": {"threadId": self.thread, "turnId": self.turn, "item": item}})
            self.started.set()
        elif method == "turn/steer":
            self.steer_entered.set()
            if self.steer_release:
                self.steer_release.wait(2)
            if self.mode == "disconnect":
                self.transport.close()
            elif self.mode == "interrupt":
                raise SystemExit("synthetic caller interruption")
            elif self.mode == "reject":
                self.transport.feed({"id": message["id"], "error": {"code": -32001, "message": "PRIVATE_SERVER_ERROR"}})
            else:
                self.transport.feed({"id": message["id"], "result": {"turnId": self.turn if self.mode != "wrong_turn" else "turn-other"}})
                item = {"id": "item-" + params["clientUserMessageId"], "type": "userMessage", "clientId": params["clientUserMessageId"]}
                self.users.append(item)
                self.transport.feed({"method": "item/completed", "params": {"threadId": self.thread, "turnId": self.turn, "item": item}})
        else:
            raise AssertionError("Unexpected model operation: " + method)

    def finish(self, *, users=None):
        answer = {"id": "answer", "type": "agentMessage", "phase": "final_answer", "text": "Synthetic result"}
        self.transport.feed({"method": "item/completed", "params": {"threadId": self.thread, "turnId": self.turn, "item": answer}})
        self.transport.feed({"method": "turn/completed", "params": {"threadId": self.thread,
            "turn": {"id": self.turn, "status": "completed", "items": [*(self.users if users is None else users), answer]}}})

    def count(self, method):
        return sum(message["method"] == method for message in self.transport.writes)


def wait_until(predicate):
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.005)
    raise AssertionError("Synthetic fixture did not reach the expected state")


class ClientSteerTests(unittest.TestCase):
    def start(self, *, allow=True, version="0.167.0"):
        client = SteerClient(version=version)
        executor = ThreadPoolExecutor(1)
        self.addCleanup(executor.shutdown, wait=True)
        self.addCleanup(client.close)
        future = executor.submit(client.send_text, thread_id=client.thread, text="Original", client_message_id="original-request-0001", allow_steer=allow)
        self.assertTrue(client.started.wait(1))
        wait_until(lambda: bool(client._inputs()._turns))
        return client, future

    def test_ten_appends_keep_one_original_input_proof_and_one_turn_start(self):
        client, future = self.start()
        for index in range(10):
            command_id = f"append-command-{index:04}"
            receipt = client.steer_text(thread_id=client.thread, expected_turn_id=client.turn, command_id=command_id, text="Upřesni původní práci")
            self.assertTrue(receipt["accepted_into_turn"])
        client.finish(); receipt = future.result(2)
        self.assertTrue(receipt.delivered); self.assertEqual(receipt.user_item_count, 1)
        self.assertEqual(client.count("turn/start"), 1); self.assertEqual(client.count("turn/steer"), 10)
        for message in client.transport.writes:
            if message["method"] == "turn/steer":
                self.assertEqual(set(message["params"]), {"threadId", "expectedTurnId", "clientUserMessageId", "input"})
                self.assertIn("DEVELOPMENT_CONTROL", message["params"]["input"][0]["text"])

    def test_append_is_opt_in_and_old_peer_has_no_speculative_probe(self):
        for allow, version in ((False, "0.167.0"), (True, "0.163.0")):
            client, future = self.start(allow=allow, version=version)
            with self.assertRaises(AppServerSteerRejected):
                client.steer_text(thread_id=client.thread, expected_turn_id=client.turn, command_id="append-command-0001", text="More")
            self.assertEqual(client.count("turn/steer"), 0)
            client.finish(); self.assertTrue(future.result(2).delivered)

    def test_unknown_or_duplicate_user_input_does_not_become_initial_delivery(self):
        for scenario in ("unknown", "duplicate_original", "missing_original"):
            client, future = self.start()
            client.steer_text(thread_id=client.thread, expected_turn_id=client.turn, command_id="append-command-0001", text="More")
            users = list(client.users)
            if scenario == "unknown": users.append({"id": "foreign", "type": "userMessage", "clientId": "unregistered-command"})
            if scenario == "duplicate_original": users.append(dict(users[0]))
            if scenario == "missing_original": users = users[1:]
            client.finish(users=users)
            with self.assertRaises(AppServerError): future.result(2)
            self.assertEqual(client.count("turn/start"), 1)

    def test_same_command_or_wrong_turn_is_rejected_before_rpc(self):
        client, future = self.start()
        kwargs = dict(thread_id=client.thread, expected_turn_id=client.turn, command_id="append-command-0001", text="More")
        client.steer_text(**kwargs)
        for change in ({}, {"expected_turn_id": "turn-other"}):
            with self.assertRaises(AppServerSteerRejected): client.steer_text(**{**kwargs, **change})
        self.assertEqual(client.count("turn/steer"), 1)
        client.finish(); self.assertTrue(future.result(2).delivered)


class WorkSteerTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.client = SteerClient()
        self.hub = CanonicalSessionHub(state_path=self.root / "session.json", workspace=self.root,
            client_factory=lambda: self.client, developer_instructions="Synthetic original authorization",
            sandbox="read-only", sandbox_policy={"type": "readOnly", "networkAccess": False}, approval_policy="never", reasoning_effort="low")
        self.hub.connect()
        self.active_project = "project-current"
        self.controller = WorkController(self.root / "work", command_scope_guard=lambda value: value["scope"]["workstream_id"] == self.active_project)
        scope = {"workstream_id": self.active_project, "profile_id": "human-adam", "thread_id": self.client.thread,
                 "connection_generation": self.hub.snapshot()["connection_generation"]}
        request = {"text": "Original consultation", "client_message_id": "original-request-0001"}
        reservation = lambda: WorkReservation(scope, self.hub.state_path,
            lambda observer: self.hub.send(**request, work_observer=observer), lambda: None)
        result = self.controller.submit(self.active_project, request, reservation)
        self.identity = result["operations"][0]["operation_id"]
        self.addCleanup(self.cleanup_work)
        wait_until(lambda: self.controller.view(self.active_project, identity=self.identity)["operations"][0]["capabilities"]["steer"])

    def cleanup_work(self):
        self.client.close()
        self.controller.close()
        for handle in self.controller._handles.values(): handle.thread.join(2)
        self.hub.close()

    def payload(self, index=1, **change):
        return {"operation_id": self.identity, "command_id": f"ha06-{self.identity}-{index:032x}",
                "expectedTurnId": self.client.turn, "text": "Upřesnění původní práce", **change}

    def submit(self, index=1, **change):
        return self.controller.steer(self.active_project, self.payload(index, **change))

    def test_real_hub_observer_and_controller_accept_ten_without_new_turn_or_policy(self):
        original_params = dict(self.client.transport.writes[0]["params"])
        for index in range(10):
            self.assertEqual(self.submit(index)["command"]["state"], "accepted")
        self.client.finish()
        handle = self.controller._handles[self.identity]; self.assertTrue(handle.finished.wait(2))
        self.assertTrue(self.hub.snapshot()["messages"][-1]["delivery_confirmed"])
        self.assertEqual(self.client.count("turn/start"), 1); self.assertEqual(self.client.count("turn/steer"), 10)
        self.assertEqual(self.client.transport.writes[0]["params"], original_params)
        self.assertEqual(self.hub.sandbox_policy, {"type": "readOnly", "networkAccess": False})

    def test_duplicate_and_changed_digest_are_durable_without_rpc(self):
        first = self.submit()
        path = self.controller.commands.repository(self.identity).path
        before = path.read_bytes(), path.stat().st_mtime_ns
        again = self.submit()
        self.assertTrue(again["duplicate_prevented"])
        self.assertEqual(again["command"], first["command"])
        self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), before)
        with self.assertRaises(WorkConflict): self.submit(text="Changed command")
        self.assertEqual(self.client.count("turn/steer"), 1)

    def test_wrong_turn_scope_finished_and_permission_change_never_append(self):
        self.assertEqual(self.submit(1, expectedTurnId="turn-other")["command"]["state"], "rejected")
        self.active_project = "project-other"
        self.assertEqual(self.submit(2)["command"]["state"], "rejected")
        self.active_project = "project-current"
        self.hub.model = "changed-runtime-policy"
        self.assertEqual(self.submit(3)["command"]["state"], "rejected")
        self.client.finish(); self.assertTrue(self.controller._handles[self.identity].finished.wait(2))
        self.assertEqual(self.submit(4)["command"]["state"], "rejected")
        self.assertEqual(self.client.count("turn/steer"), 0); self.assertEqual(self.client.count("turn/start"), 1)

    def test_unknown_disconnect_is_not_replayed_by_retry_or_new_backend(self):
        self.client.mode = "disconnect"
        result = self.submit()
        self.assertEqual(result["command"]["state"], "unverified")
        self.assertEqual(self.submit()["command"]["state"], "unverified")
        another = WorkController(self.root / "work", command_scope_guard=lambda _: True)
        self.addCleanup(another.close)
        self.assertEqual(another.steer(self.active_project, self.payload())["command"]["state"], "unverified")
        self.assertEqual(self.client.count("turn/steer"), 1); self.assertEqual(self.client.count("turn/start"), 1)

    def test_explicit_rpc_rejection_is_private_and_parent_proof_survives(self):
        self.client.mode = "reject"
        result = self.submit()
        self.assertEqual(result["command"]["state"], "rejected")
        self.assertNotIn("PRIVATE_SERVER_ERROR", json.dumps(result))
        self.client.finish(); self.assertTrue(self.controller._handles[self.identity].finished.wait(2))
        self.assertTrue(self.hub.snapshot()["messages"][-1]["delivery_confirmed"])

    def test_wrong_ack_is_unverified_even_if_original_parent_later_completes(self):
        self.client.mode = "wrong_turn"
        self.assertEqual(self.submit()["command"]["state"], "unverified")
        self.client.finish(); self.assertTrue(self.controller._handles[self.identity].finished.wait(2))
        self.assertTrue(self.hub.snapshot()["messages"][-1]["delivery_confirmed"])
        self.assertEqual(self.submit()["command"]["state"], "unverified")
        self.assertEqual(self.client.count("turn/start"), 1); self.assertEqual(self.client.count("turn/steer"), 1)

    def test_inflight_duplicate_returns_pending_and_does_not_repeat(self):
        release = self.client.steer_release = threading.Event(); self.addCleanup(release.set)
        with ThreadPoolExecutor(1) as executor:
            future = executor.submit(self.submit)
            self.assertTrue(self.client.steer_entered.wait(1))
            self.assertEqual(self.submit()["command"]["state"], "pending")
            self.assertEqual(self.submit(2)["command"]["state"], "rejected")
            release.set(); self.assertEqual(future.result(2)["command"]["state"], "accepted")
        self.assertEqual(self.client.count("turn/steer"), 1)

    def test_missing_initialized_journal_and_failed_receipt_never_authorize_repeat(self):
        original = JsonWorkRepository.transact
        def fail_finish(repo, updater, **kwargs):
            if repo.path.parent.name == "commands" and updater.__name__ == "finish":
                raise OSError("PRIVATE_STORAGE_ERROR")
            return original(repo, updater, **kwargs)
        with patch.object(JsonWorkRepository, "transact", fail_finish):
            with self.assertRaises(OSError): self.submit()
        self.assertEqual(self.controller.read_command(self.active_project, self.identity, self.payload()["command_id"])["command"]["state"], "unverified")
        self.assertEqual(self.submit()["command"]["state"], "unverified")
        original_read = JsonWorkRepository.read
        def missing(repo):
            return {} if repo.path.parent.name == "commands" else original_read(repo)
        with patch.object(JsonWorkRepository, "read", missing):
            with self.assertRaises(WorkUnavailable): self.submit()
        self.assertEqual(self.client.count("turn/steer"), 1)

    def test_pending_orphan_is_unverified_after_caller_loss_or_restart(self):
        self.client.mode = "interrupt"
        with self.assertRaises(SystemExit): self.submit()
        self.assertEqual(self.submit()["command"]["state"], "unverified")
        restarted = WorkController(self.root / "work", command_scope_guard=lambda _: True)
        self.addCleanup(restarted.close)
        view = restarted.read_command(self.active_project, self.identity, self.payload()["command_id"])
        self.assertEqual(view["command"]["state"], "unverified")
        self.assertEqual(view["command"]["reason"], "owner_unavailable")
        self.assertEqual(self.client.count("turn/steer"), 1)

    def test_completion_race_keeps_command_receipt_without_changing_parent_result(self):
        release = self.client.steer_release = threading.Event(); self.addCleanup(release.set)
        with ThreadPoolExecutor(1) as executor:
            future = executor.submit(self.submit)
            self.assertTrue(self.client.steer_entered.wait(1))
            self.client.finish(); self.assertTrue(self.controller._handles[self.identity].finished.wait(2))
            parent = self.controller.store.load(self.identity)
            self.client.mode = "reject"; release.set()
            self.assertEqual(future.result(2)["command"]["state"], "rejected")
        self.assertEqual(self.controller.store.load(self.identity), parent)
        self.assertTrue(self.hub.snapshot()["messages"][-1]["delivery_confirmed"])
        self.assertEqual(self.client.count("turn/start"), 1)

    def test_compaction_limit_and_payload_overrides_cannot_replay_or_expand_policy(self):
        from app.communication.human_adam_work import WorkError
        for override in ({"write_intent": True}, {"sandboxPolicy": {"type": "dangerFullAccess"}}, {"model": "different"}):
            with self.assertRaises(WorkError): self.controller.steer(self.active_project, {**self.payload(), **override})
        with patch("app.communication.human_adam_work_commands.MAX_COMMANDS", 3), patch("app.communication.human_adam_work_commands.VISIBLE_COMMANDS", 1):
            for index in (1, 2, 3): self.assertEqual(self.submit(index)["command"]["state"], "accepted")
            self.assertEqual(self.submit(4)["command"]["reason"], "command_limit")
            self.assertTrue(self.submit(1)["duplicate_prevented"])
            old = self.controller.read_command(self.active_project, self.identity, self.payload(1)["command_id"])
            self.assertNotIn("text", old["command"])
        self.assertEqual(self.client.count("turn/steer"), 3)

    def test_generation_change_and_corrupt_command_source_fail_closed(self):
        with self.hub._state_lock:
            self.hub._state["connection_generation"] += 1
        self.assertEqual(self.submit()["command"]["state"], "rejected")
        with self.hub._state_lock:
            self.hub._state["connection_generation"] -= 1
        self.submit(2)
        path = self.controller.commands.repository(self.identity).path
        value = json.loads(path.read_text()); value["commands"][0]["text"] = "Changed private source"
        path.write_text(json.dumps(value))
        with self.assertRaises(WorkUnavailable): self.submit(3)
        self.assertEqual(self.client.count("turn/steer"), 1)
