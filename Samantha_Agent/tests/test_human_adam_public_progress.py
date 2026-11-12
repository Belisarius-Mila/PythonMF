import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.communication.human_adam_public_progress import (
    MAX_COMMENTS, MAX_COMMENT_TEXT, MAX_STEPS, MAX_STEP_TEXT,
    merge_public_progress, public_event, public_projection,
)
from app.communication.human_adam_work import WorkStore, normalized_request
from app.communication.human_adam_work_observer import WorkObserver
from app.codex_appserver_dispatch import AppServerDispatcher


class PublicProgressTests(unittest.TestCase):
    def comment(self, identity="comment-1", phase="commentary", **fields):
        return {"item": {"id": identity, "type": "agentMessage", "phase": phase,
                         "text": "Veřejná průběžná zpráva.", **fields}}

    def test_only_completed_explicit_commentary_is_public(self):
        for phase in (None, "analysis", "partial_answer", "final_answer", {}, []):
            self.assertIsNone(public_event("item/completed", self.comment(phase=phase)))
        self.assertIsNone(public_event("item/started", self.comment()))
        self.assertIsNone(public_event("item/agentMessage/delta", {"delta": "PRIVATE"}))
        self.assertIsNotNone(public_event("item/completed", self.comment()))

    def test_reasoning_and_tool_payloads_never_enter_projection(self):
        for kind in ("reasoning", "commandExecution", "mcpToolCall", "webSearch", "fileChange"):
            params = self.comment(type=kind, arguments="PRIVATE_ARGUMENTS", text="PRIVATE_TEXT")
            self.assertIsNone(public_event("item/completed", params))

    def test_plan_has_only_bounded_step_and_status(self):
        raw = {"plan": [{"step": "x" * (MAX_STEP_TEXT + 5), "status": "pending", "private": "PRIVATE"}
                        for _ in range(MAX_STEPS + 3)], "explanation": "PRIVATE_EXPLANATION"}
        result = merge_public_progress(None, public_event("turn/plan/updated", raw))
        self.assertEqual(len(result["plan"]), MAX_STEPS)
        self.assertEqual(len(result["plan"][0]["step"]), MAX_STEP_TEXT)
        self.assertTrue(result["plan_truncated"])
        self.assertNotIn("PRIVATE", json.dumps(result))

    def test_comments_are_bounded_deduplicated_and_copied(self):
        result = None
        for index in range(MAX_COMMENTS + 3):
            result = merge_public_progress(result, public_event("item/completed", self.comment(str(index))))
        self.assertEqual(len(result["comments"]), MAX_COMMENTS)
        self.assertTrue(result["comments_truncated"])
        result = merge_public_progress(result, public_event("item/completed", self.comment(str(MAX_COMMENTS + 2), text="x" * 3000)))
        self.assertEqual(len(result["comments"]), MAX_COMMENTS)
        self.assertEqual(len(result["comments"][-1]["text"]), MAX_COMMENT_TEXT)
        exported = public_projection(result)
        exported["comments"].clear()
        self.assertEqual(len(result["comments"]), MAX_COMMENTS)

    def test_export_discards_all_extra_fields(self):
        value = merge_public_progress(None, public_event("item/completed", self.comment(arguments="PRIVATE")))
        value.update(reasoning="PRIVATE", raw_event={"args": "PRIVATE"})
        value["comments"][0]["internal"] = "PRIVATE"
        self.assertNotIn("PRIVATE", json.dumps(public_projection(value)))

    def test_invalid_public_data_is_unavailable(self):
        for value in (None, {}, {"schema_version": 1, "source": "raw"}):
            self.assertIsNone(public_projection(value))
        for plan in (None, {}, [None], [{"step": "", "status": "pending"}], [{"step": "a", "status": {}}]):
            self.assertIsNone(public_event("turn/plan/updated", {"plan": plan}))

    def test_empty_plan_explicitly_clears_previous_plan(self):
        original = merge_public_progress(None, public_event("turn/plan/updated", {"plan": [{"step": "Hotovo", "status": "completed"}]}))
        cleared = merge_public_progress(original, public_event("turn/plan/updated", {"plan": []}))
        self.assertEqual(cleared["plan"], [])
        self.assertEqual(len(original["plan"]), 1)


class ScopedPublicProgressTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = WorkStore(Path(self.temp.name) / "work")
        self.scope = {"workstream_id": "project-current", "profile_id": "human-adam",
                      "thread_id": "thread-current", "connection_generation": 3}
        self.request = normalized_request({"text": "Synthetic request", "client_message_id": "human-adam-request-1"})
        self.value, _ = self.store.admit(self.request, self.scope, "owner", session_path=Path(self.temp.name) / "session.json")
        self.identity = self.value["operation_id"]
        self.observer = WorkObserver(self.store, self.identity, "owner")
        self.dispatcher = AppServerDispatcher()
        self.addCleanup(self.dispatcher.close)
        self.subscription = self.dispatcher.subscribe(thread_id="thread-current")
        self.addCleanup(self.subscription.close)

    def emit(self, method, **params):
        self.assertTrue(self.dispatcher.feed({"method": method, "params": params}, generation=self.dispatcher.generation))
        self.observer._event(self.subscription.get(timeout=.1))

    def public(self):
        return self.store.public(self.store.load(self.identity), owned=True)

    def test_plan_waits_for_exact_ack_then_public_export_omits_explanation(self):
        self.dispatcher.register(1, "turn/start", {"threadId": "thread-current"})
        self.assertTrue(self.dispatcher.feed({"method": "turn/plan/updated", "params": {
            "turnId": "turn-current", "explanation": "PRIVATE_EXPLANATION",
            "plan": [{"step": "Prověřit podklady", "status": "inProgress"}]}}, generation=self.dispatcher.generation))
        self.assertTrue(self.dispatcher.feed({"id": 1, "result": {"turn": {"id": "turn-current"}}}, generation=self.dispatcher.generation))
        self.observer._event(self.subscription.get(timeout=.1))
        self.assertNotIn("public_progress", self.public())
        self.observer.accepted("turn-current")
        exported = self.public()
        self.assertEqual(exported["public_progress"]["plan"][0]["step"], "Prověřit podklady")
        self.assertNotIn("PRIVATE", json.dumps(exported))

    def test_foreign_turn_and_wire_generation_do_not_change_public_work(self):
        self.observer.accepted("turn-current")
        self.emit("turn/plan/updated", threadId="thread-current", turnId="turn-current",
                  plan=[{"step": "Správný plán", "status": "pending"}])
        before = self.store.load(self.identity)
        self.emit("turn/plan/updated", threadId="thread-current", turnId="turn-other",
                  plan=[{"step": "FOREIGN", "status": "pending"}])
        self.assertEqual(self.store.load(self.identity), before)
        other = AppServerDispatcher()
        self.addCleanup(other.close)
        sub = other.subscribe(thread_id="thread-current")
        other.feed({"method": "turn/plan/updated", "params": {"threadId": "thread-current", "turnId": "turn-current",
                   "plan": [{"step": "OTHER_GENERATION", "status": "pending"}]}}, generation=other.generation)
        self.observer._event(sub.get(timeout=.1))
        self.assertEqual(self.store.load(self.identity), before)

    def test_only_public_commentary_is_retained_and_delivery_is_independent(self):
        self.observer.accepted("turn-current")
        for phase, text in ((None, "PRIVATE_UNKNOWN"), ("final_answer", "FINAL_SEPARATE"), ("commentary", "Veřejný postup")):
            self.emit("item/completed", threadId="thread-current", turnId="turn-current",
                      item={"id": "item-" + str(phase), "type": "agentMessage", "phase": phase, "text": text})
        exported = self.public()
        self.assertEqual([c["text"] for c in exported["public_progress"]["comments"]], ["Veřejný postup"])
        self.assertNotIn("PRIVATE_UNKNOWN", json.dumps(exported))
        self.assertNotIn("FINAL_SEPARATE", json.dumps(exported))
        self.assertEqual(exported["delivery_state"], "not_started")

    def test_evicted_terminal_progress_is_compacted_but_identity_is_preserved(self):
        original_id = self.identity
        with patch("app.communication.human_adam_work.MAX_RECENT", 2):
            for index in range(3):
                request = normalized_request({"text": "Synthetic request", "client_message_id": f"human-adam-request-{index + 1}"})
                value, _ = self.store.admit(request, self.scope, "owner", session_path=Path(self.temp.name) / "session.json")
                self.store.change(value["operation_id"], "owner", "execution_finished", fields={
                    "lifecycle_state": "completed", "delivery_state": "confirmed",
                    "public_progress": merge_public_progress(None, {"kind": "comment", "comment": {"id": "item", "text": "Old public comment"}})})
            self.assertNotIn("public_progress", self.store.load(original_id))
            self.assertTrue(self.store.repository(original_id).path.exists())
            old, created = self.store.admit(self.request, self.scope, "owner", session_path=Path(self.temp.name) / "session.json")
            self.assertFalse(created)
            self.assertEqual(old["operation_id"], original_id)
