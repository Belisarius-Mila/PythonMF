from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from app.cockpit_email_agent import email_agent_overview
from app.email.continuous_agent import ContinuousEmailAgent
from app.email.visibility_preferences import EmailVisibilityPreferences, hidden_low_importance
from tests.test_continuous_email_agent import FakeSource, observed, proposal


class EmailVisibilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.worker = ContinuousEmailAgent(Path(self.temp.name) / "agent")
        self.message = observed(subject="Nabídka krmiv pro psy 5. 11. 2026")
        self.low = proposal().model_copy(update={"important": False, "reply_draft": ""})
        self.worker.cycle(FakeSource([self.message]), lambda _: self.low)
        self.rules = EmailVisibilityPreferences(self.worker)

    def test_rule_hides_existing_low_mail_and_persists_without_changing_business_state(self):
        before = self.worker.status()
        key = self.rules.remember(self.message.item_id)
        self.assertEqual(self.rules.remember(self.message.item_id), key)
        restarted = ContinuousEmailAgent(self.worker.root)
        state = restarted.status()
        rules = state.pop("visibility_preferences")
        self.assertEqual(len(rules), 1)
        self.assertEqual(state, before)
        self.assertEqual(email_agent_overview(worker=restarted)["hours"], [])
        self.assertEqual(restarted.status()["items"][self.message.item_id]["status"], "hourly_summary")

    def test_cancel_restores_existing_hour_and_can_reactivate_same_rule(self):
        before = email_agent_overview(worker=self.worker)["hours"]
        key = self.rules.remember(self.message.item_id)
        created = self.worker.status()["visibility_preferences"][key]["created_at"]
        self.rules.forget(key)
        EmailVisibilityPreferences(ContinuousEmailAgent(self.worker.root)).forget(key)
        self.assertEqual(email_agent_overview(worker=self.worker)["hours"], before)
        self.assertEqual(email_agent_overview(worker=self.worker)["visibility_preferences"], [])
        self.assertEqual(self.rules.remember(self.message.item_id), key)
        self.assertEqual(self.worker.status()["visibility_preferences"][key]["created_at"], created)

    def test_scope_is_exact_account_and_address_with_similar_subject(self):
        self.rules.remember(self.message.item_id)
        state = self.worker.status()
        item = state["items"][self.message.item_id]
        for account, sender, subject, expected in (
            ("account-a", "Jiné jméno <sender@example.test>", "RE: Nabídka krmiv pro psy 6. 11. 2026", True),
            ("account-b", "sender@example.test", self.message.source.subject, False),
            ("account-a", "different@example.test", self.message.source.subject, False),
            ("account-a", "sender@example.test", "Vyúčtování zaplacené objednávky", False),
            ("account-a", "sender@example.test, other@example.test", self.message.source.subject, False),
        ):
            candidate = copy.deepcopy(item)
            candidate.update(account=account, header={"sender": sender, "subject": subject})
            with self.subTest(account=account, sender=sender, subject=subject):
                self.assertEqual(hidden_low_importance(candidate, state["visibility_preferences"]), expected)

    def test_future_messages_are_fully_assessed_and_important_match_remains_visible(self):
        self.rules.remember(self.message.item_id)
        ordinary = observed("2", subject=self.message.source.subject, body="Celá reklama END_LOW")
        important = observed("3", subject=self.message.source.subject, body="x" * 30000 + "URGENT_END")
        unrelated = observed("4", subject="Jiný informační přehled")
        seen = []
        def assess(message):
            seen.append(message.source.body_text)
            return proposal() if message.source.uid == "3" else self.low
        self.worker.cycle(FakeSource([ordinary, important, unrelated]), assess)
        self.assertEqual(len(seen), 3)
        self.assertIn("URGENT_END", seen[1])
        view = email_agent_overview(worker=self.worker)
        self.assertEqual([item["id"] for item in view["cards"]], [important.item_id])
        self.assertEqual([m["id"] for h in view["hours"] for m in h["messages"]], [unrelated.item_id])
        self.assertEqual([i for h in view["hours"] for i in h["ids"]], [unrelated.item_id])
        self.assertEqual(self.worker.status()["sources"]["account-a"]["after_uid"], 4)
        self.worker.cycle(FakeSource([ordinary, important, unrelated]), lambda _: self.fail("No repeated assessment"))

    def test_no_soft_preferences_are_created_or_converted(self):
        self.worker.remember_low_importance(self.message.item_id)
        self.assertTrue(email_agent_overview(worker=self.worker)["hours"])
        self.assertNotIn("visibility_preferences", self.worker.status())
        old = self.worker.status()["importance_preferences"]
        self.rules.remember(self.message.item_id)
        self.assertEqual(self.worker.status()["importance_preferences"], old)

    def test_important_failed_or_missing_verdict_cannot_teach_or_hide(self):
        for status, important in (("awaiting_confirmation", True), ("analysis_failed", False), ("hourly_summary", None)):
            self.worker._update(lambda d: d["items"][self.message.item_id].update(
                status=status, proposal={"important": important}))
            with self.subTest(status=status, verdict=important), self.assertRaises(ValueError):
                self.rules.remember(self.message.item_id)
        self.assertNotIn("visibility_preferences", self.worker.status())
        self.assertFalse(hidden_low_importance(self.worker.status()["items"][self.message.item_id], {}))

    def test_empty_subject_or_ambiguous_sender_is_rejected_atomically(self):
        before = self.worker.status()
        for sender, subject in (("sender@example.test", "1234"), ("a@example.test, b@example.test", "Novinky")):
            self.worker._update(lambda d: d["items"][self.message.item_id]["header"].update(sender=sender, subject=subject))
            with self.assertRaises(ValueError): self.rules.remember(self.message.item_id)
        self.assertNotIn("visibility_preferences", self.worker.status())
        self.assertEqual(self.worker.status()["sources"], before["sources"])


if __name__ == "__main__":
    unittest.main()
