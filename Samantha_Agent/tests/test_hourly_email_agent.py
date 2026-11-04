from __future__ import annotations

from datetime import datetime
from dataclasses import replace
import json
import tempfile
import unittest
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.cockpit_email_agent import (
    email_agent_archive_action, email_agent_dismiss_action, email_agent_edit_action, email_agent_overview,
)
from app.email.codex_proposer import CodexEmailProposer
from app.email.continuous_agent import ContinuousEmailAgent, EmailProposal
from app.email.hourly_agent import HourlyEmailScheduler, hourly_slot
from tests.test_continuous_email_agent import FakeSource, observed, proposal


def at(text):
    return datetime.fromisoformat(text)


class HourlyEmailTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.worker = ContinuousEmailAgent(Path(self.temp.name) / "agent")
        self.scheduler = HourlyEmailScheduler(self.worker)
        self.now = at("2026-11-04T07:00:00+01:00")

    def initialize(self, source):
        source.baseline_cursor = lambda: {"uidvalidity": "10", "after_uid": 0}
        self.scheduler.initialize_from_now([source])

    def test_hours_are_inclusive_seven_to_twenty_two_in_prague(self):
        for hour in range(24):
            with self.subTest(hour=hour):
                self.assertEqual(hourly_slot(self.now.replace(hour=hour)) is not None, 7 <= hour <= 22)
        self.assertTrue(hourly_slot(at("2026-07-01T05:00:00+00:00")).startswith("2026-07-01T07:00"))
        self.assertIsNone(hourly_slot(at("2026-11-04T05:59:59+00:00")))
        with self.assertRaises(ValueError): hourly_slot(datetime(2026, 11, 4, 7))

    def test_first_tick_requires_explicit_activation_boundary_without_reading_mail(self):
        source = FakeSource([observed()])
        self.assertEqual(self.scheduler.tick([source], lambda _: proposal(), now=self.now)["status"], "needs_initialization")
        self.assertEqual(source.calls, [])

    def test_initialize_does_not_move_existing_position_or_read_bodies(self):
        source = FakeSource([observed()])
        self.initialize(source)
        source.baseline_cursor = lambda: self.fail("Must preserve existing cursor")
        self.scheduler.initialize_from_now([source])
        self.assertEqual(source.calls, [])

    def test_hour_drains_all_pages_and_does_not_run_again_same_hour(self):
        source = FakeSource([observed(str(i)) for i in range(1, 8)])
        self.initialize(source)
        seen = []
        def propose(message):
            seen.append(message.source.uid)
            return proposal()
        result = self.scheduler.tick([source], propose, now=self.now, batch_size=2)
        self.assertEqual(result, {"status": "completed", "proposals": 7})
        self.assertEqual(seen, [str(i) for i in range(1, 8)])
        result = self.scheduler.tick([source], propose, now=self.now.replace(minute=55))
        self.assertEqual(result["status"], "already_completed")
        self.assertEqual(len(seen), 7)

    def test_morning_reads_since_last_evening_position(self):
        source = FakeSource([observed("1")])
        self.initialize(source)
        self.scheduler.tick([source], lambda _: proposal(), now=self.now.replace(hour=22))
        source.messages += [observed("2"), observed("3")]
        night = self.scheduler.tick([source], lambda _: self.fail("No night calls"), now=self.now.replace(hour=23))
        self.assertEqual(night["status"], "outside_hours")
        next_morning = at("2026-11-05T07:00:00+01:00")
        result = HourlyEmailScheduler(ContinuousEmailAgent(self.worker.root)).tick(
            [source], lambda _: proposal(), now=next_morning)
        self.assertEqual(result["proposals"], 2)
        self.assertEqual(len(self.worker.status()["items"]), 3)

    def test_network_failure_does_not_finish_hour_or_repeat_completed_assessments(self):
        source = FakeSource([observed("1")])
        self.initialize(source)
        source.error = True
        self.assertEqual(self.scheduler.tick([source], lambda _: proposal(), now=self.now)["status"], "incomplete")
        self.assertNotIn("completed_slot", self.worker.status()["schedule"])
        source.error = False
        self.assertEqual(self.scheduler.tick([source], lambda _: proposal(), now=self.now)["proposals"], 1)

    def test_batch_budget_keeps_cursor_and_continues_without_duplicates(self):
        source = FakeSource([observed(str(i)) for i in range(1, 4)])
        self.initialize(source)
        self.assertEqual(self.scheduler.tick([source], lambda _: proposal(), now=self.now,
                                             batch_size=2, max_batches=1)["status"], "incomplete")
        self.assertEqual(self.scheduler.tick([source], lambda _: proposal(), now=self.now,
                                             batch_size=2, max_batches=1)["status"], "completed")
        self.assertEqual(len(self.worker.status()["items"]), 3)

    def populate_mixed(self):
        messages = [observed("1", body="Important full body"), observed("2", body="Advertisement full body")]
        def classify(message):
            return proposal().model_copy(update={"important": message.source.uid == "1"})
        self.worker.cycle(FakeSource(messages), classify, cycle_at=self.now)
        return messages

    def test_cockpit_has_one_card_and_one_hour_row_with_only_low_value_headers(self):
        self.populate_mixed()
        view = email_agent_overview(worker=self.worker)
        self.assertEqual(len(view["cards"]), 1)
        self.assertEqual(view["cards"][0]["message"]["body_text"], "Important full body")
        self.assertEqual(len(view["hours"]), 1)
        self.assertIn("sender@example.test", view["hours"][0]["text"])
        self.assertNotIn("Advertisement full body", json.dumps(self.worker.status()))

    def test_local_dismiss_keeps_source_cursor_and_cannot_reappear_after_restart(self):
        messages = self.populate_mixed()
        before = self.worker.status()["sources"]
        view = email_agent_overview(worker=self.worker)
        ids = view["hours"][0]["ids"] + [view["cards"][0]["id"]]
        self.assertTrue(email_agent_dismiss_action({"ids": ids}, worker=self.worker)["ok"])
        self.assertEqual(self.worker.status()["sources"], before)
        ContinuousEmailAgent(self.worker.root).cycle(FakeSource(messages), lambda _: self.fail("No duplicate models"))
        after = email_agent_overview(worker=self.worker)
        self.assertEqual(after["cards"], [])
        self.assertEqual(after["hours"], [])

    def test_ignoring_is_local_and_records_distinct_state(self):
        messages = self.populate_mixed()
        result = email_agent_dismiss_action({"ids": [messages[0].item_id], "action": "ignore"}, worker=self.worker)
        self.assertTrue(result["ok"])
        self.assertEqual(self.worker.status()["items"][messages[0].item_id]["status"], "ignored")

    def test_bad_dismiss_batch_is_atomic(self):
        messages = self.populate_mixed()
        self.assertFalse(email_agent_dismiss_action({"ids": [messages[0].item_id, "missing"]}, worker=self.worker)["ok"])
        self.assertEqual(len(email_agent_overview(worker=self.worker)["cards"]), 1)

    def test_background_model_does_not_block_review_of_an_existing_card(self):
        messages = self.populate_mixed()
        started, release = threading.Event(), threading.Event()
        def slow_model(_):
            started.set()
            if not release.wait(5): raise TimeoutError("test model")
            return proposal()
        thread = threading.Thread(target=lambda: self.worker.cycle(FakeSource([observed("3")]), slow_model))
        thread.start()
        try:
            self.assertTrue(started.wait(3))
            result = email_agent_dismiss_action({"ids": [messages[0].item_id]}, worker=self.worker)
            self.assertTrue(result["ok"])
        finally:
            release.set()
            thread.join(timeout=5)
        self.assertFalse(thread.is_alive())

    def test_edit_is_saved_and_stale_editor_cannot_overwrite(self):
        self.populate_mixed()
        card = email_agent_overview(worker=self.worker)["cards"][0]
        updated = {**card["proposal"], "reply_subject": "Upravený předmět", "reply_draft": "Upravená odpověď"}
        payload = {"id": card["id"], "proposal": updated, "expected_digest": card["proposal_digest"]}
        self.assertTrue(email_agent_edit_action(payload, worker=self.worker)["ok"])
        self.assertFalse(email_agent_edit_action(payload, worker=self.worker)["ok"])
        self.assertEqual(email_agent_overview(worker=self.worker)["cards"][0]["proposal"]["reply_subject"], "Upravený předmět")

    def test_archive_requires_confirmation_before_any_source_read(self):
        self.populate_mixed()
        card = email_agent_overview(worker=self.worker)["cards"][0]
        result = email_agent_archive_action({"id": card["id"]}, worker=self.worker,
                                            source_factory=lambda *_: self.fail("No read without confirmation"))
        self.assertFalse(result["ok"])

    def test_confirmed_archive_uses_same_source_and_appears_in_archived_list(self):
        messages = self.populate_mixed()
        card = email_agent_overview(worker=self.worker)["cards"][0]
        result = email_agent_archive_action({"id": card["id"], "confirmed": True,
                                            "proposal_digest": card["proposal_digest"]}, worker=self.worker,
                                            source_factory=lambda *_: SimpleNamespace(read_item=lambda item: messages[0]))
        self.assertTrue(result["ok"])
        view = email_agent_overview(worker=self.worker)
        self.assertEqual(len(view["archived"]), 1)
        self.assertEqual(len(view["cards"]), 1)  # Pending reply remains available after archiving.


class CodexProposalTests(unittest.TestCase):
    def test_preference_is_a_hint_next_to_the_full_body_not_a_filter(self):
        calls = []
        class Client:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def start_thread(self, **kwargs): calls.append(kwargs); return "hint-test"
            def send_text(self, **kwargs):
                calls.append(kwargs)
                return SimpleNamespace(delivered=True, answer=proposal().model_dump_json())
        hint = {"id": "pref-1", "sender": "sender@example.test", "subject": "Newsletter",
                "preference": "prefer_low_importance"}
        message = replace(observed(body="x" * 30000 + "FULL_END"), importance_preferences=(hint,))
        result = CodexEmailProposer("gpt-6.1-terra", client_factory=Client)(message)
        payload = json.loads(calls[1]["text"])
        self.assertEqual(payload["importance_preferences"], [hint])
        self.assertTrue(payload["body_text"].rstrip().endswith("FULL_END"))
        self.assertIn("ponech important=true", calls[0]["developer_instructions"])
        self.assertTrue(result.important)

    def test_strict_output_requires_all_fields_including_local_defaults(self):
        def require_strict_objects(schema):
            if isinstance(schema, dict):
                if schema.get("type") == "object":
                    if set(schema.get("required", [])) != set(schema.get("properties", {})):
                        raise ValueError("invalid_json_schema: every property must be required")
                    if schema.get("additionalProperties") is not False:
                        raise ValueError("invalid_json_schema: additionalProperties must be false")
                for value in schema.values():
                    require_strict_objects(value)
            elif isinstance(schema, list):
                for value in schema:
                    require_strict_objects(value)

        class StrictClient:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def start_thread(self, **kwargs): return "strict-test"
            def send_text(self, **kwargs):
                require_strict_objects(kwargs["output_schema"])
                return SimpleNamespace(delivered=True, answer=proposal().model_dump_json())

        result = CodexEmailProposer("gpt-6.1-terra", client_factory=StrictClient)(observed())
        self.assertTrue(result.important)
        # Historical saved proposals still accept their original local defaults.
        old = proposal().model_dump()
        old.pop("important")
        old.pop("reply_subject")
        self.assertEqual(EmailProposal.model_validate(old).reply_subject, "")

    def test_explicit_terra_model_full_body_and_schema_reach_appserver(self):
        calls = []
        class Client:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def start_thread(self, **kwargs): calls.append(kwargs); return "ephemeral-test"
            def send_text(self, **kwargs):
                calls.append(kwargs)
                return SimpleNamespace(delivered=True, answer=proposal().model_dump_json())
        adapter = CodexEmailProposer("gpt-6.1-terra", client_factory=Client)
        self.assertEqual(adapter(observed(body="x" * 30_000 + "SOURCE_END")), proposal())
        self.assertEqual(calls[0]["model"], "gpt-6.1-terra")
        self.assertIn("SOURCE_END", calls[1]["text"])
        self.assertIn("important", calls[1]["output_schema"]["properties"])
        self.assertEqual(calls[1]["model"], "gpt-6.1-terra")

    def test_unconfirmed_model_receipt_is_not_a_proposal(self):
        class Client:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def start_thread(self, **kwargs): return "test"
            def send_text(self, **kwargs): return SimpleNamespace(delivered=False, answer=proposal().model_dump_json())
        with self.assertRaises(ValueError): CodexEmailProposer("gpt-6.1-terra", client_factory=Client)(observed())


if __name__ == "__main__":
    unittest.main()
