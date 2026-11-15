"""HA-08 counter, ownership and recovery contracts; no live model calls."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch, Mock

from app.codex_usage import UsageMeter, measurement_projection
from app.codex_appserver import CodexAppServerClient, CodexVersion, AppServerTurnInterrupted
from app.communication.human_adam_usage import usage_projection
from app.communication.human_adam_work import WorkController, WorkStore, normalized_request
from app.communication.human_adam_work import WorkReservation
from app.communication.human_adam_work_observer import WorkObserver
from app.file_persistence import atomic_write_json
from app.file_persistence import exclusive_file_lock
from app.release_usage import TOKEN_KEYS
from tests.test_codex_appserver import _ScriptedTransport


def counts(n):
    return dict(zip(TOKEN_KEYS, (n * 10, n * 2, n * 5, n, n * 15)))


def meter(anchor=None, model="synthetic-model"):
    value = UsageMeter("thread-1", model=model, effort="high", anchor=anchor)
    value.turn_id = "turn-1"
    return value


def complete():
    value = meter({"fresh": True, "total": counts(0)})
    value.observe(counts(2))
    return value.snapshot(terminal=True, duration_ms=1234)


class CounterTests(unittest.TestCase):
    def test_cumulative_duplicates_and_coalescing_are_never_summed(self):
        value = meter({"context": ("synthetic-model", "high", None), "total": counts(2)})
        for n in (3, 3, 7):
            value.observe(counts(n))
        result = value.snapshot(terminal=True)
        self.assertEqual(result["usage"], counts(5))
        self.assertTrue(result["complete"])
        self.assertEqual(measurement_projection(result), result)

    def test_existing_thread_without_baseline_stays_unknown_then_establishes_anchor(self):
        value = meter(); value.observe(counts(7))
        self.assertIsNone(value.snapshot(terminal=True)["usage"])
        following = meter(value.anchor(terminal=True)); following.observe(counts(9))
        self.assertEqual(following.snapshot(terminal=True)["usage"], counts(2))

    def test_model_effort_and_tier_changes_do_not_forge_delta(self):
        for context in (("other", "high", None), ("synthetic-model", "low", None),
                        ("synthetic-model", "high", "priority")):
            value = meter({"context": context, "total": counts(1)}); value.observe(counts(3))
            self.assertIsNone(value.snapshot(terminal=True)["usage"])
            self.assertEqual(value.snapshot(terminal=True)["reason"], "context_changed")

    def test_reset_and_malformed_update_are_sticky_and_cannot_seed_next_turn(self):
        for bad in (counts(1), None, {**counts(3), "input_tokens": True},
                    {**counts(3), "cached_input_tokens": 10000}):
            value = meter({"fresh": True, "total": counts(0)})
            value.observe(counts(2)); value.observe(bad); value.observe(counts(4))
            result = value.snapshot(terminal=True)
            self.assertFalse(result["complete"]); self.assertIsNone(result["usage"])
            self.assertIsNone(value.anchor(terminal=True))

    def test_running_or_unknown_model_never_claims_complete(self):
        for model in (None, "synthetic-model"):
            value = meter({"fresh": True, "total": counts(0)}, model=model); value.observe(counts(1))
            self.assertFalse(value.snapshot()["complete"])
        self.assertIsNone(value.anchor(terminal=False))

    def test_public_projection_recomputes_and_strips_sensitive_fields(self):
        result = complete()
        self.assertNotIn("PRIVATE", json.dumps(measurement_projection({**result, "prompt": "PRIVATE"})))
        self.assertIsNone(measurement_projection({**result, "usage": counts(9)}))
        self.assertIsNone(measurement_projection({**result, "model": "PRIVATE model text"}))


class ClientMeasurementTests(unittest.TestCase):
    def client(self):
        transport = _ScriptedTransport(completed_items=[])
        with patch("app.codex_appserver.read_codex_version", return_value=CodexVersion.parse("codex-cli 0.169.0")):
            client = CodexAppServerClient(transport_factory=lambda **_: transport)
        self.addCleanup(client.close)
        return client, transport

    def turn(self, client, transport, n, *, callback=None, status="completed"):
        transport._events = _ScriptedTransport(completed_items=[])._events
        transport._events[-1]["params"]["turn"]["status"] = status
        aliases = ("inputTokens", "cachedInputTokens", "outputTokens", "reasoningOutputTokens", "totalTokens")
        total = dict(zip(aliases, counts(n).values()))
        transport._events.insert(2, {"method": "thread/tokenUsage/updated", "params": {
            "threadId": "thread-1", "turnId": "turn-1", "tokenUsage": {"total": total, "last": total}}})
        return client.send_text(thread_id="thread-1", text="Synthetic", client_message_id="message-1",
                                model="synthetic-model", effort="high", on_usage=callback, allow_interrupt=True)

    def test_new_thread_receipt_following_delta_and_resume_boundary(self):
        client, transport = self.client()
        client.start_thread(cwd=Path.cwd())
        first = self.turn(client, transport, 2)
        self.assertEqual(first.token_measurement["usage"], counts(2))
        self.assertEqual(self.turn(client, transport, 5).token_measurement["usage"], counts(3))
        client.resume_thread("thread-1", cwd=Path.cwd())
        self.assertIsNone(self.turn(client, transport, 7).token_measurement["usage"])
        self.assertEqual(self.turn(client, transport, 9).token_measurement["usage"], counts(2))

    def test_telemetry_callback_failure_does_not_break_delivery(self):
        client, transport = self.client(); callback = Mock(side_effect=OSError("PRIVATE"))
        self.assertTrue(self.turn(client, transport, 1, callback=callback).delivered)
        self.assertGreaterEqual(callback.call_count, 2)

    def test_interruption_keeps_numeric_terminal_measurement_without_success(self):
        client, transport = self.client(); client.start_thread(cwd=Path.cwd()); observed = []
        with self.assertRaises(AppServerTurnInterrupted):
            self.turn(client, transport, 2, status="interrupted", callback=observed.append)
        self.assertTrue(observed[-1]["complete"])
        self.assertEqual(observed[-1]["usage"], counts(2))

    def test_missing_update_invalidates_continuity(self):
        client, transport = self.client(); client.start_thread(cwd=Path.cwd())
        self.turn(client, transport, 2)
        transport._events = _ScriptedTransport(completed_items=[])._events
        receipt = client.send_text(thread_id="thread-1", text="Synthetic", client_message_id="message-1", model="synthetic-model", effort="high")
        self.assertFalse(receipt.token_measurement["complete"])
        self.assertIsNone(self.turn(client, transport, 5).token_measurement["usage"])

    def test_transport_adapters_without_constructor_initialize_measurement_lazily(self):
        client, transport = self.client(); del client._usage_anchors
        client.resume_thread("thread-1", cwd=Path.cwd())
        self.assertIsNone(self.turn(client, transport, 2).token_measurement["usage"])
        del client._usage_anchors
        client.start_thread(cwd=Path.cwd())
        self.assertEqual(self.turn(client, transport, 3).token_measurement["usage"], counts(3))


class OwnedUsageTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name); self.controller = WorkController(self.root / "work")
        self.addCleanup(self.controller.close)
        self.store = self.controller.store
        self.scope = {"workstream_id": "project-a", "profile_id": "human_adam", "thread_id": "thread-1", "connection_generation": 1}
        self.session = self.root / "session.json"
        self.record, _ = self.store.admit(normalized_request({"text": "PRIVATE", "client_message_id": "request-0001"}),
                                         self.scope, self.controller.owner, session_path=self.session)
        self.identity = self.record["operation_id"]
        self.observer = WorkObserver(self.store, self.identity, self.controller.owner)
        self.observer.dispatching(); self.observer.accepted("turn-1")

    def summary(self):
        return WorkStore.public(self.store.load(self.identity), owned=True)["usage_summary"]

    def test_exact_binding_rejects_foreign_usage_and_private_fields(self):
        for change in ({"thread_id": "other-thread"}, {"turn_id": "other-turn"}):
            self.observer.measured({**complete(), **change})
        self.assertIsNone(self.summary()["recorded_usage"])
        self.observer.measured({**complete(), "private": "SECRET"})
        self.assertEqual(self.summary()["recorded_usage"], counts(2))
        self.assertNotIn("SECRET", json.dumps(self.store.load(self.identity)))

    def test_busy_repository_and_observer_do_not_delay_original_receiver(self):
        with exclusive_file_lock(self.store.repository(self.identity).path):
            started = time.monotonic(); self.observer.measured(complete())
            self.assertLess(time.monotonic() - started, .5)
        locked, release = threading.Event(), threading.Event()
        def busy():
            with self.observer._lock:
                locked.set(); release.wait(2)
        worker = threading.Thread(target=busy); worker.start()
        try:
            self.assertTrue(locked.wait(1))
            started = time.monotonic(); self.observer.measured(complete())
            self.assertLess(time.monotonic() - started, .5)
        finally:
            release.set(); worker.join(2)
        self.assertIsNone(self.summary()["recorded_usage"])
        self.observer.measured(complete())
        self.assertEqual(self.summary()["recorded_usage"], counts(2))

    def test_helper_deduplication_parent_binding_and_cached_subsets(self):
        self.observer.measured(complete())
        helper = {"executor": {"model": "synthetic-helper"}, "model_usage": counts(3), "job_id": "job-a"}
        for _ in range(2):
            self.controller.record_helper_usage("project-a", "request-0001", "thread-1", "a" * 64, helper)
        self.controller.record_helper_usage("project-a", "request-0001", "foreign", "b" * 64, helper)
        self.store.change(self.identity, self.controller.owner, "finalized", fields={"_usage_finalized": True})
        result = self.summary()
        self.assertEqual(result["recorded_usage"], counts(5)); self.assertEqual(len(result["components"]), 2)
        self.assertTrue(result["complete"])
        self.assertIsNone(result["price"]["amount"]); self.assertIsNone(result["price"]["price_version"])

    def test_unknown_helper_is_visible_and_never_becomes_zero(self):
        self.observer.measured(complete())
        self.controller.record_helper_usage("project-a", "request-0001", "thread-1", "a" * 64, {})
        result = self.summary()
        self.assertFalse(result["complete"]); self.assertIsNone(result["components"][1]["usage"])
        self.assertEqual(result["recorded_usage"], counts(2))

    def test_optional_helper_write_failure_is_flushed_with_original_completion(self):
        request = normalized_request({"text": "Synthetic", "client_message_id": "request-b001"})
        scope = {**self.scope, "workstream_id": "project-b"}
        original_change = self.store.change
        def fail_optional(identity, owner, kind, **kwargs):
            if kind == "helper_usage_updated":
                raise OSError("Synthetic optional telemetry failure")
            return original_change(identity, owner, kind, **kwargs)
        def execute(observer):
            observer.dispatching(); observer.accepted("turn-1"); observer.measured(complete())
            try:
                self.controller.record_helper_usage("project-b", "request-b001", "thread-1", "a" * 64, {})
            except OSError:
                pass  # The trusted portal isolates the optional write failure.
            return {"ok": True, "entry": {"status": "completed", "delivery_confirmed": True,
                "client_message_id": "request-b001", "thread_id": "thread-1", "turn_id": "turn-1"}}
        with patch.object(self.store, "change", side_effect=fail_optional):
            result = self.controller.submit("project-b", request,
                lambda: WorkReservation(scope, self.session, execute, lambda: None), wait=True)
        self.assertTrue(result["ok"])
        summary = self.controller.view("project-b")["operations"][0]["usage_summary"]
        self.assertEqual(len(summary["components"]), 2)
        self.assertFalse(summary["complete"])
        self.assertIsNone(summary["components"][1]["usage"])

    def test_restart_reads_same_totals_and_terminal_duration_is_stable(self):
        self.observer.measured(complete())
        self.store.change(self.identity, self.controller.owner, "finished", fields={"lifecycle_state": "interrupted", "delivery_state": "confirmed"})
        restored = WorkStore(self.root / "work")
        before = self.summary(); after = WorkStore.public(restored.load(self.identity), owned=True)["usage_summary"]
        self.assertEqual(before, after); self.assertTrue(after["elapsed_final"])
        self.assertEqual(after["components"][0]["duration_ms"], 1234)

    def test_recovery_copies_exact_canonical_measurement_without_new_turn(self):
        atomic_write_json(self.session, {"messages": [{"client_message_id": "request-0001", "thread_id": "thread-1",
            "turn_id": "turn-1", "status": "completed", "delivery_confirmed": True, "token_measurement": complete()}]})
        restored = WorkController(self.root / "work"); self.addCleanup(restored.close)
        result = restored.recover("project-a", self.identity)
        self.assertFalse(result["recovery"]["redispatched"])
        self.assertEqual(result["operations"][0]["usage_summary"]["recorded_usage"], counts(2))

    def test_legacy_and_malformed_telemetry_do_not_break_work_read(self):
        record = self.store.load(self.identity)
        for measurement in (None, "invalid", {"private": "SECRET"}):
            summary = usage_projection({**record, "_model_usage": measurement})
            self.assertIsNone(summary["recorded_usage"]); self.assertFalse(summary["complete"])
            self.assertNotIn("SECRET", json.dumps(summary))

    def test_frontend_numeric_breakdown_and_unknown_states(self):
        from app.communication.human_adam_live_ui import HUMAN_ADAM_LIVE_SCRIPT
        from scripts.cockpit_quality_gate import node_binary
        self.observer.measured(complete())
        self.store.change(self.identity, self.controller.owner, "finalized", fields={"_usage_finalized": True})
        script = HUMAN_ADAM_LIVE_SCRIPT + r'''
const assert=require('node:assert/strict'), summary=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
const operation={usage_summary:summary}, view=humanAdamUsageLines(operation);
assert(view.title.includes('30'));assert(view.title.includes('doložená'));
assert(view.parts.some(s=>s.includes('cache 4')));assert(view.parts.some(s=>s.includes('uvažování 2')));
assert(view.parts.some(s=>s.includes('0 → 30')));
summary.complete=false;assert(humanAdamUsageLines(operation).title.includes('neúplná'));
summary.recorded_usage=null;assert(humanAdamUsageLines(operation).title.includes('není k dispozici'));
summary.recorded_usage={total_tokens:-1};assert.equal(humanAdamUsageLines(operation).parts.length,0);
assert.equal(humanAdamUsageLines(null).parts.length,0);console.log('HA08 frontend PASS');
'''
        result = subprocess.run([node_binary(), "-e", script], input=json.dumps(self.summary()), text=True,
                                capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
