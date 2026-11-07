from __future__ import annotations

import copy
import json
from pathlib import Path
import socket
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app import recovery_guide_trial as trial
from app.codex_appserver import CodexAppServerClient, CodexVersion, AppServerTimeout


class Wire:
    """Synthetic RPC/events through the real existing client, never a model."""
    def __init__(self, path):
        self.socket_path = path
        self.calls = []
        self.events = []
        self.closed = False
        self.fail = None
        self.answer = {"records": [{"id": s["id"], "quote": s["text"],
            "status": trial.EXPECTED[s["id"]]} for s in trial.SOURCES]}
        self.usage = {"inputTokens": 100, "cachedInputTokens": 0, "outputTokens": 60,
                      "reasoningOutputTokens": 20, "totalTokens": 160}
        self.permissions = {"type": "readOnly", "networkAccess": False}
        self.version = trial.PEER
        self.model = trial.MODEL
        self.started = False
        self.extra_items = []

    def request(self, method, params):
        self.calls.append((method, copy.deepcopy(params)))
        if method == "model/list":
            return {"data": [{"model": self.model,
                "supportedReasoningEfforts": [{"reasoningEffort": "medium"}]}]}
        if method == "account/read":
            return {"account": {"type": "chatgpt", "email": "SECRET_ACCOUNT"}}
        if method == "config/read":
            return {"config": {"service_tier": "fast", "mcp_servers": {
                "test_server": {"env": {"SECRET": "PRIVATE_CONFIG"}}}}}
        if method == "skills/list":
            return {"data": [{"errors": [], "skills": [{"path": "/tmp/test/SKILL.md"}]}]}
        if method == "thread/start":
            self.started = True
            return {"thread": {"id": "test-thread"}, "model": trial.MODEL,
                "cwd": params["cwd"], "approvalPolicy": "never", "sandbox": self.permissions}
        if method == "turn/start":
            record = json.loads((trial.STATE / "receipt.json").read_text())
            assert record["state"] == "delivery_unknown"  # Durable BEFORE wire.
            assert record["model_turn_attempts"] == 1
            if self.fail == "send":
                raise AppServerTimeout("SECRET_EXCEPTION")
            items = [{"type": "userMessage", "clientId": trial.REQUEST},
                     {"type": "agentMessage", "id": "comment", "phase": "commentary", "text": "Pracuji."},
                     {"type": "agentMessage", "id": "final", "phase": "final_answer",
                      "text": self.answer if isinstance(self.answer, str) else json.dumps(self.answer)}]
            items.extend(self.extra_items)
            self.events = [
                {"method": "turn/started", "params": {"turn": {"id": "test-turn"}}},
                {"method": "thread/tokenUsage/updated", "params": {"tokenUsage": {"total": self.usage}}},
                {"method": "turn/completed", "params": {"turn": {
                    "id": "test-turn", "status": "completed", "items": items}}}]
            for e in self.events:
                e["params"].update(threadId="test-thread", turnId="test-turn")
            return {"turn": {"id": "test-turn"}}
        raise AssertionError(method)

    def receive(self, predicate, **_):
        if self.fail == "receive":
            raise AppServerTimeout("SECRET_EXCEPTION")
        event = self.events.pop(0)
        assert predicate(event)
        return event

    def close(self):
        self.closed = True


class TrialTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.sock = socket.socket(socket.AF_UNIX)
        self.addCleanup(self.sock.close)
        path = self.root / "rpc.sock"
        self.sock.bind(str(path))
        self.wire = Wire(path)
        self.real_protocol = trial._protocol
        self.enterContext(patch.object(trial, "STATE", self.root / "state"))
        self.enterContext(patch.object(trial, "_protocol", return_value={"version": trial.PEER}))
        self.enterContext(patch.object(trial, "_reference", return_value={"encoding": "o200k_base",
                          "text_tokens": 900, "exact_model_mapping": False}))
        self.factories = 0

    def factory(self):
        self.factories += 1
        c = CodexAppServerClient.__new__(CodexAppServerClient)
        c.transport = self.wire
        c.server_version = CodexVersion.parse("codex-cli " + self.wire.version)
        c.version = SimpleNamespace(raw="0.166.0")
        return c

    def prepare(self):
        return trial.prepare(client_factory=self.factory)

    def run_trial(self, prepared=None):
        prepared = prepared or self.prepare()
        return trial.run(approved_digest=prepared["approval_digest"], client_factory=self.factory)

    def turns(self):
        return [p for m, p in self.wire.calls if m == "turn/start"]

    def test_prepare_is_nonpaid_redacted_and_immutable(self):
        p = self.prepare()
        self.assertEqual(p, self.prepare())
        self.assertEqual(self.factories, 1)
        self.assertFalse(self.wire.started)
        self.assertFalse(self.turns())
        self.assertNotIn("SECRET_ACCOUNT", json.dumps(p))
        self.assertNotIn("PRIVATE_CONFIG", json.dumps(p))
        self.assertFalse(p["plan"]["inherited_standard"])
        self.assertFalse(p["plan"]["hard_billing_or_output_cap"])
        self.assertFalse(p["plan"]["reads_recovery_guide"])
        self.assertEqual((trial.STATE / "plan.json").stat().st_mode & 0o777, 0o600)

    def test_missing_or_wrong_approval_never_connects(self):
        self.prepare()
        for approval in ("", "yes", "0" * 64):
            with self.assertRaises(ValueError):
                trial.run(approved_digest=approval, client_factory=self.factory)
        self.assertEqual(self.factories, 1)
        self.assertFalse(self.turns())

    def test_tampered_plan_does_not_match_approval(self):
        p = self.prepare()
        tampered = copy.deepcopy(p)
        tampered["plan"]["model"] = "different-model"
        (trial.STATE / "plan.json").write_text(json.dumps(tampered))
        with self.assertRaises(ValueError):
            self.run_trial(p)
        self.assertFalse(self.turns())

    def test_exact_single_turn_standard_is_not_persistent_override(self):
        r = self.run_trial()
        self.assertEqual(r["state"], "trial_passed")
        self.assertEqual(len(self.turns()), 1)
        p = self.turns()[0]
        self.assertEqual(p["serviceTierForTurn"], "default")
        self.assertNotIn("serviceTier", p)
        self.assertEqual(p["effort"], "medium")
        self.assertEqual(p["model"], trial.MODEL)
        self.assertTrue(self.wire.closed)
        self.assertEqual(r["usage"]["output_tokens"], 60)
        self.assertAlmostEqual(r["estimated_standard_credits"], .02)

    def test_isolated_thread_disables_all_known_channels(self):
        self.run_trial()
        p = next(p for m, p in self.wire.calls if m == "thread/start")
        self.assertTrue(p["ephemeral"])
        self.assertEqual(p["sandbox"], "read-only")
        self.assertEqual(p["approvalPolicy"], "never")
        config = p["config"]
        for feature in trial.DISABLED_FEATURES:
            self.assertIs(config["features." + feature], False)
        self.assertEqual(config["project_doc_max_bytes"], 0)
        self.assertEqual(config["web_search"], "disabled")
        self.assertFalse(config["mcp_servers.test_server.enabled"])
        self.assertFalse(config["skills.config"][0]["enabled"])
        self.assertEqual([m for m, _ in self.wire.calls].count("thread/start"), 1)

    def test_completed_slot_is_returned_without_connecting_again(self):
        p = self.prepare()
        r = self.run_trial(p)
        self.assertEqual(self.run_trial(p), r)
        self.assertEqual(self.factories, 2)
        self.assertEqual(len(self.turns()), 1)

    def test_send_or_receive_uncertainty_never_retries(self):
        self.wire.fail = "send"
        p = self.prepare()
        r = self.run_trial(p)
        self.assertTrue(r["delivery_unknown"])
        self.assertNotIn("SECRET_EXCEPTION", json.dumps(r))
        self.assertEqual(r, self.run_trial(p))
        self.assertEqual(len(self.turns()), 1)

    def test_receive_timeout_preserves_acknowledged_turn_identity(self):
        self.wire.fail = "receive"
        r = self.run_trial()
        self.assertTrue(r["delivery_unknown"])
        self.assertEqual(r["turn_id"], "test-turn")
        self.assertEqual(r, self.run_trial())
        self.assertEqual(len(self.turns()), 1)

    def test_process_death_keeps_durable_unknown_slot(self):
        p = self.prepare()
        original = self.wire.receive
        self.wire.receive = lambda *a, **k: (_ for _ in ()).throw(KeyboardInterrupt())
        with self.assertRaises(KeyboardInterrupt):
            self.run_trial(p)
        self.wire.receive = original
        r = self.run_trial(p)
        self.assertEqual(r["state"], "delivery_unknown")
        self.assertEqual(len(self.turns()), 1)

    def test_reserved_preconnect_crash_also_prevents_another_attempt(self):
        p = self.prepare()
        with patch.object(trial, "_runtime", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.run_trial(p)
        self.assertEqual(self.run_trial(p)["state"], "reserved")
        self.assertFalse(self.turns())

    def test_parallel_submissions_share_one_slot(self):
        p = self.prepare()
        results, failures = [], []
        def call():
            try:
                results.append(self.run_trial(p))
            except Exception as e:
                failures.append(e)
        threads = [threading.Thread(target=call) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertFalse(failures)
        self.assertEqual(len(results), 3)
        self.assertEqual(len(self.turns()), 1)

    def test_model_or_peer_drift_blocks_before_thread(self):
        p = self.prepare()
        self.wire.version = "0.166.0"
        r = self.run_trial(p)
        self.assertEqual(r["state"], "attention")
        self.assertFalse(self.wire.started)
        self.assertFalse(self.turns())

    def test_absent_exact_model_prevents_plan(self):
        self.wire.model = "different-model"
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse((trial.STATE / "plan.json").exists())

    def test_peer_identity_uses_parsed_numbers_not_raw_cli_prefix(self):
        c = self.factory()
        self.assertEqual(c.server_version.raw, "codex-cli 0.163.0")
        self.assertEqual(trial._runtime(c)["server_version"], "0.163.0")

    def test_api_account_does_not_reuse_subscription_price_card(self):
        original = self.wire.request
        def request(method, params):
            return {"account": {"type": "apiKey"}} if method == "account/read" else original(method, params)
        self.wire.request = request
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.turns())

    def test_real_protocol_check_requires_matching_version_and_disabled_features(self):
        base = self.root / ".venv/recovery_rec06_peer_schema/v2"
        base.mkdir(parents=True)
        (base / "TurnStartParams.json").write_text(json.dumps({"properties": {"serviceTierForTurn": {
            "type": ["string", "null"], "description": "Use default for standard speed."}}}))
        (base / "ThreadStartResponse.json").write_text('{}')
        package = self.root / ".venv/recovery_rec06_cli/node_modules/@openai/codex/package.json"
        package.parent.mkdir(parents=True)
        package.write_text(json.dumps({"version": trial.PEER}))
        features = self.root / ".venv/recovery_rec06_disabled_features.txt"
        features.write_text('\n'.join(n + ' stable false' for n in trial.DISABLED_FEATURES))
        with patch.object(trial, "ROOT", self.root):
            self.assertEqual(self.real_protocol()["version"], trial.PEER)
            features.write_text('shell_tool stable true')
            with self.assertRaisesRegex(ValueError, 'feature_contract'):
                self.real_protocol()
            package.write_text('{"version":"0.166.0"}')
            with self.assertRaisesRegex(ValueError, 'version_mismatch'):
                self.real_protocol()

    def test_pre_wire_journal_failure_does_not_send(self):
        p = self.prepare()
        original = trial.atomic_write_json
        def fail_marker(path, payload, **kwargs):
            if payload["state"] == "delivery_unknown":
                raise OSError("SECRET_DISK_ERROR")
            return original(path, payload, **kwargs)
        with patch.object(trial, "atomic_write_json", side_effect=fail_marker):
            r = self.run_trial(p)
        self.assertFalse(self.turns())
        self.assertEqual(r, self.run_trial(p))
        self.assertNotIn("SECRET_DISK_ERROR", json.dumps(r))

    def test_unexpected_tool_event_fails_acceptance_despite_valid_json(self):
        self.wire.extra_items = [{"type": "commandExecution", "id": "unexpected"}]
        r = self.run_trial()
        self.assertFalse(r["accepted"])
        self.assertEqual(r["unexpected_item_types"], ["commandExecution"])
        self.assertEqual(len(self.turns()), 1)

    def test_implementation_drift_requires_new_review_without_reserving(self):
        p = self.prepare()
        with patch.object(trial, "_implementation", return_value={}):
            with self.assertRaises(ValueError):
                self.run_trial(p)
        self.assertFalse((trial.STATE / "receipt.json").exists())

    def test_socket_replacement_blocks_even_same_peer_version(self):
        p = self.prepare()
        replacement = socket.socket(socket.AF_UNIX)
        self.addCleanup(replacement.close)
        new_path = self.root / "new.sock"
        replacement.bind(str(new_path))
        self.wire.socket_path = new_path
        r = self.run_trial(p)
        self.assertEqual(r["state"], "attention")
        self.assertFalse(self.wire.started)

    def test_escalated_effective_permissions_block_before_turn(self):
        self.wire.permissions = {"type": "dangerFullAccess"}
        r = self.run_trial()
        self.assertEqual(r["state"], "attention")
        self.assertFalse(self.turns())

    def test_missing_usage_invalid_json_and_bad_semantics_never_retry(self):
        self.wire.answer = "not-json"
        p = self.prepare()
        r = self.run_trial(p)
        self.assertEqual(r["state"], "attention")
        self.assertEqual(r["estimated_standard_credits"], .02)
        self.assertTrue(r["receipt"]["delivered"])
        self.assertEqual(self.run_trial(p), r)
        self.assertEqual(len(self.turns()), 1)

    def test_unknown_usage_does_not_claim_zero_cost_or_success(self):
        self.wire.usage = None
        r = self.run_trial()
        self.assertIsNone(r["estimated_standard_credits"])
        self.assertFalse(r["accepted"])

    def test_over_limit_keeps_actual_usage_and_cost(self):
        self.wire.usage.update(inputTokens=100, outputTokens=10000, totalTokens=10100)
        r = self.run_trial()
        self.assertEqual(r["state"], "attention")
        self.assertEqual(r["usage"]["output_tokens"], 10000)
        self.assertGreater(r["estimated_standard_credits"], 2)

    def test_semantic_validation_rejects_voice_resurrection_duplicate_or_false_quote(self):
        good = copy.deepcopy(self.wire.answer)
        for kind in ("voice", "duplicate", "quote", "extra", "shape"):
            answer = copy.deepcopy(good)
            if kind == "voice":
                answer["records"][3]["status"] = "proposed"
            elif kind == "duplicate":
                answer["records"][1] = answer["records"][0]
            elif kind == "quote":
                answer["records"][0]["quote"] = "Invented"
            elif kind == "extra":
                answer["records"].append(answer["records"][0])
            else:
                answer["records"][0]["id"] = []
            with self.subTest(kind=kind):
                self.assertFalse(trial._answer_ok(answer))
        self.assertTrue(trial._answer_ok(good))

    def test_wrapper_rejects_resume_other_rpc_and_second_thread(self):
        self.run_trial()
        # Same guard is closed with the existing connection, never the daemon.
        guard = trial.StandardOneTurn(self.wire, context=trial.STATE / "context", before_turn=lambda _: None)
        for method in ("thread/resume", "config/write", "command/exec", "thread/archive"):
            with self.assertRaises(ValueError):
                guard.request(method, {})
        guard.start_attempted = True
        with self.assertRaises(ValueError):
            guard.request("thread/start", {"cwd": str(guard.context)})

    def test_wrapper_rejects_foreign_or_second_turn(self):
        guard = trial.StandardOneTurn(self.wire, context=trial.STATE / "context", before_turn=lambda _: None)
        guard.thread_id = "own"
        with self.assertRaises(ValueError):
            guard.request("turn/start", {"threadId": "foreign"})
        guard.attempted = True
        with self.assertRaises(ValueError):
            guard.request("turn/start", {"threadId": "own"})

    def test_symlinked_artifact_is_refused(self):
        self.prepare()
        (trial.STATE / "receipt.json").symlink_to(self.root / "elsewhere")
        with self.assertRaises(ValueError):
            self.run_trial()


if __name__ == "__main__":
    unittest.main()
