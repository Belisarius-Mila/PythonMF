from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from email.message import EmailMessage
from pathlib import Path
from types import SimpleNamespace
from threading import Event
from unittest.mock import patch

from app.email.config import ICloudMailConfig, SeznamMailConfig
from app.email.continuous_agent import (
    ArchiveMetadata, ContinuousEmailAgent, EmailProposal, SDKEmailProposer,
)
from app.email.continuous_source import IMAPAgentSource, MailScan, ObservedEmail
from app.email.icloud_provider import _message_data_to_archive_source


def observed(uid="1", *, account="account-a", validity="10", body="Celá zpráva.",
             sender="sender@example.test", subject="Podklady ke schůzce"):
    message = EmailMessage()
    message["From"] = sender
    message["To"] = "recipient@example.test"
    message["Subject"] = subject
    message["Message-ID"] = "<test@example.test>"
    message.set_content(body)
    raw = message.as_bytes()
    source = _message_data_to_archive_source(
        uid, [(b"RFC822.SIZE " + str(len(raw)).encode(), raw)], None,
        max_message_bytes=len(raw),
    )
    return ObservedEmail(account, validity, source)


def proposal():
    return EmailProposal(
        summary="Podklady pro přípravu schůzky.", reason="Uložit k dané věci.",
        reply_draft="Děkuji za podklady.", archive_recommended=True,
        metadata=ArchiveMetadata(title="Schůzka – podklady", domain="work",
                                 document_type="correspondence", counterparty="Odesílatel", tags=["schůzka"]),
    )


class FakeSource:
    key = "account-a"

    def __init__(self, messages):
        self.messages = messages
        self.calls = []
        self.error = False

    def scan(self, cursor, *, limit):
        self.calls.append(dict(cursor))
        if self.error:
            raise OSError("simulated network failure")
        validity = self.messages[0].uidvalidity if self.messages else "10"
        after = cursor.get("after_uid", 0) if cursor.get("uidvalidity") == validity else 0
        return MailScan(validity, tuple(m for m in self.messages if int(m.source.uid) > after)[:limit])


class ContinuousEmailTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "agent"
        self.worker = ContinuousEmailAgent(self.root)

    def prepare(self, message=None):
        message = message or observed()
        self.worker.cycle(FakeSource([message]), lambda _: proposal())
        item = self.worker.status()["items"][message.item_id]
        return message, item["proposal_digest"]

    def test_status_is_readonly_without_initializing_storage(self):
        self.assertEqual(self.worker.status(), {"sources": {}, "items": {}})
        self.assertFalse(self.root.exists())

    def test_service_loop_processes_sources_and_stops_without_cockpit(self):
        stop = Event()
        calls = []
        def propose(message):
            calls.append(message.source.uid)
            stop.set()
            return proposal()
        self.worker.run([FakeSource([observed()])], propose, stop=stop, interval_seconds=0.001)
        self.assertEqual(calls, ["1"])
        with self.assertRaises(ValueError):
            self.worker.run([], propose, stop=stop)

    def test_complete_body_beyond_old_archive_limit_and_html_are_not_cut(self):
        message = EmailMessage()
        text = "x" * 210_000 + "KONEC_CELE_ZPRAVY"
        message.set_content(text)
        message.add_alternative("<html><body>" + text + "</body></html>", subtype="html")
        raw = message.as_bytes()
        source = _message_data_to_archive_source("1", [(b"", raw)], None, max_message_bytes=len(raw))
        self.assertIn("KONEC_CELE_ZPRAVY", source.body_text)
        self.assertIn("KONEC_CELE_ZPRAVY", source.body_html)
        self.assertEqual(source.original_eml, raw)

    def test_existing_bounded_archive_parser_keeps_its_limit(self):
        message = observed(body="x" * 20)
        raw = message.source.original_eml
        source = _message_data_to_archive_source("1", [(b"", raw)], 5, max_message_bytes=len(raw))
        self.assertEqual(source.body_text, "xxxxx")

    def test_proposal_has_full_source_and_does_not_create_business_archive(self):
        message = observed(body="x" * 30_000 + "FINAL_MARKER")
        seen = []
        def propose(value):
            seen.append(value.source.body_text)
            return proposal()
        self.worker.cycle(FakeSource([message]), propose)
        self.assertIn("FINAL_MARKER", seen[0])
        self.assertFalse((self.root / "archive").exists())
        state_text = (self.root / "state.json").read_text()
        self.assertIn("FINAL_MARKER", state_text)
        self.assertNotIn("original_eml", state_text)

    def test_restart_and_batches_do_not_duplicate_or_skip(self):
        messages = [observed(str(i)) for i in range(1, 6)]
        source = FakeSource(messages)
        seen = []
        def propose(value):
            seen.append(value.source.uid)
            return proposal()
        for _ in range(4):
            ContinuousEmailAgent(self.root).cycle(source, propose, limit=2)
        self.assertEqual(seen, ["1", "2", "3", "4", "5"])
        self.assertEqual(len(self.worker.status()["items"]), 5)

    def test_uidvalidity_change_and_second_account_do_not_reuse_identity(self):
        first = observed()
        second = observed(validity="11")
        other = observed(account="account-b")
        self.assertEqual(len({first.item_id, second.item_id, other.item_id}), 3)
        source = FakeSource([first])
        self.worker.cycle(source, lambda _: proposal())
        source.messages = [second]
        self.worker.cycle(source, lambda _: proposal())
        self.assertEqual(len(self.worker.status()["items"]), 2)

    def test_provider_error_keeps_cursor_and_is_distinct_from_empty_mailbox(self):
        source = FakeSource([observed("3")])
        self.worker.cycle(source, lambda _: proposal())
        source.error = True
        result = self.worker.cycle(source, lambda _: self.fail("Must not call model"))
        self.assertEqual(result["health"], "error")
        self.assertEqual(self.worker.status()["sources"][source.key]["after_uid"], 3)
        source.error = False
        self.assertEqual(self.worker.cycle(source, lambda _: proposal())["health"], "ok")

    def test_model_failure_is_visible_and_not_automatically_retried(self):
        message = observed()
        def fail(_):
            raise TimeoutError("uncertain model result")
        self.worker.cycle(FakeSource([message]), fail)
        self.assertEqual(self.worker.status()["items"][message.item_id]["status"], "analysis_failed")
        self.worker.cycle(FakeSource([message]), lambda _: self.fail("Unexpected paid retry"))

    def test_interrupted_model_run_is_recovered_without_new_call(self):
        message = observed()
        def crash(_):
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.worker.cycle(FakeSource([message]), crash)
        self.worker.cycle(FakeSource([message]), lambda _: self.fail("Unexpected retry"))
        self.assertEqual(self.worker.status()["items"][message.item_id]["status"], "analysis_interrupted")

    def test_confirmation_saves_exact_model_metadata_and_complete_eml_once(self):
        message, digest = self.prepare(observed(body="x" * 30_000 + "END"))
        receipt = self.worker.accept_archive(message, confirmed_digest=digest)
        self.assertEqual(receipt, self.worker.accept_archive(message, confirmed_digest=digest))
        archive = self.root / "archive" / message.item_id
        self.assertEqual((archive / "original.eml").read_bytes(), message.source.original_eml)
        self.assertEqual(json.loads((archive / "agent_metadata.json").read_text()), proposal().model_dump())
        self.assertEqual(self.worker.status()["items"][message.item_id]["status"], "archived")

    def test_changed_source_and_missing_confirmation_do_not_save(self):
        message, digest = self.prepare()
        with self.assertRaises(ValueError):
            self.worker.accept_archive(message, confirmed_digest="")
        with self.assertRaises(ValueError):
            self.worker.accept_archive(observed(body="Changed"), confirmed_digest=digest)
        self.assertFalse((self.root / "archive").exists())

    def test_editing_draft_invalidates_old_confirmation(self):
        message, digest = self.prepare()
        updated = proposal().model_copy(update={"reply_draft": "Upravená odpověď."})
        new_digest = self.worker.edit_proposal(message.item_id, updated, expected_digest=digest)
        self.assertNotEqual(digest, new_digest)
        with self.assertRaises(ValueError):
            self.worker.accept_archive(message, confirmed_digest=digest)
        self.worker.accept_archive(message, confirmed_digest=new_digest)

    def test_crash_after_archive_publish_reconciles_receipt(self):
        message, digest = self.prepare()
        original_update = self.worker._update
        count = 0
        def crash_second(callback):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError("state write interrupted after archive rename")
            return original_update(callback)
        with patch.object(self.worker, "_update", side_effect=crash_second):
            with self.assertRaises(OSError):
                self.worker.accept_archive(message, confirmed_digest=digest)
        self.assertEqual(self.worker.status()["items"][message.item_id]["status"], "saving")
        ContinuousEmailAgent(self.root).accept_archive(message, confirmed_digest=digest)
        self.assertEqual(self.worker.status()["items"][message.item_id]["status"], "archived")

    def test_model_adapter_receives_end_of_full_text_and_validates_output(self):
        message = observed(body="x" * 30_000 + "FULL_END")
        def runner(agent, prompt, **kwargs):
            self.assertIn("FULL_END", prompt)
            self.assertEqual(agent.model, "explicit-test-model")
            self.assertEqual(agent.tools, [])
            return SimpleNamespace(final_output=proposal())
        self.assertEqual(SDKEmailProposer("explicit-test-model", runner=runner)(message), proposal())
        with self.assertRaises(ValueError):
            SDKEmailProposer("")


class ImportancePreferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.worker = ContinuousEmailAgent(Path(self.temp.name) / "agent")
        self.message = observed(sender="Firma <Sender@EXAMPLE.test>", subject="Nové pracovní nabídky 4. 11. 2026")
        self.worker.cycle(FakeSource([self.message]), lambda _: proposal())

    def test_explicit_preference_survives_restart_and_double_click_without_changing_card(self):
        before = self.worker.status()
        key = self.worker.remember_low_importance(self.message.item_id)
        self.assertEqual(self.worker.remember_low_importance(self.message.item_id), key)
        restarted = ContinuousEmailAgent(self.worker.root)
        after = restarted.status()
        self.assertEqual(after["items"], before["items"])
        self.assertEqual(after["sources"], before["sources"])
        self.assertEqual(len(after["importance_preferences"]), 1)
        self.assertEqual(after["importance_preferences"][key]["sender"], "sender@example.test")
        self.assertEqual(len(restarted.matching_importance_preferences(self.message)), 1)

    def test_matching_is_scoped_to_account_sender_and_similar_subject(self):
        self.worker.remember_low_importance(self.message.item_id)
        for account, sender, subject, expected in (
            ("account-a", "Jiné jméno <sender@example.test>", "RE: FW: Nové pracovní nabídky 5. 11. 2026", True),
            ("account-a", "sender@example.test", "Nové pracovní nabídky na 5. 11. 2026", True),
            ("account-b", "sender@example.test", self.message.source.subject, False),
            ("account-a", "sender@other.test", self.message.source.subject, False),
            ("account-a", "sender@example.test", "Urgentní žádost o potvrzení schůzky", False),
        ):
            with self.subTest(account=account, sender=sender, subject=subject):
                message = observed("2", account=account, sender=sender, subject=subject)
                self.assertEqual(bool(self.worker.matching_importance_preferences(message)), expected)

    def test_dismiss_ignore_and_unprocessed_cards_do_not_teach_preferences(self):
        self.assertEqual(self.worker.matching_importance_preferences(self.message), ())
        self.worker.dismiss([self.message.item_id], action="ignore")
        self.assertEqual(self.worker.matching_importance_preferences(self.message), ())
        second = observed("2")
        self.worker.cycle(FakeSource([self.message, second]), lambda _: proposal())
        self.worker.dismiss([second.item_id], action="dismiss")
        self.assertNotIn("importance_preferences", self.worker.status())

    def test_forgetting_is_persistent_and_restoring_the_same_preference_is_idempotent(self):
        key = self.worker.remember_low_importance(self.message.item_id)
        created_at = self.worker.status()["importance_preferences"][key]["created_at"]
        self.worker.forget_importance_preference(key)
        self.worker.forget_importance_preference(key)
        restarted = ContinuousEmailAgent(self.worker.root)
        self.assertEqual(restarted.matching_importance_preferences(self.message), ())
        self.assertEqual(restarted.remember_low_importance(self.message.item_id), key)
        self.assertEqual(restarted.status()["importance_preferences"][key]["created_at"], created_at)

    def test_model_still_gets_complete_body_and_can_keep_important_despite_preference(self):
        key = self.worker.remember_low_importance(self.message.item_id)
        critical = observed("2", subject=self.message.source.subject, body="x" * 30000 + "URGENT_FULL_END")
        ordinary = observed("3", subject=self.message.source.subject, body="Reklama FULL_END")
        seen = []
        def assess(message):
            self.assertEqual(message.importance_preferences[0]["id"], key)
            self.assertTrue(message.source.body_text.rstrip().endswith("FULL_END"))
            seen.append(message.source.uid)
            return proposal().model_copy(update={"important": message.source.uid == "2"})
        self.worker.cycle(FakeSource([self.message, critical, ordinary]), assess)
        self.assertEqual(seen, ["2", "3"])
        state = self.worker.status()["items"]
        self.assertEqual(state[critical.item_id]["status"], "awaiting_confirmation")
        self.assertEqual(state[critical.item_id]["message"]["body_text"], critical.source.body_text)
        self.assertEqual(state[ordinary.item_id]["status"], "hourly_summary")
        self.assertEqual(state[ordinary.item_id]["message"], {})
        self.assertEqual(critical.importance_preferences, ())

    def test_invalid_or_ambiguous_sender_and_empty_subject_cannot_create_broad_rules(self):
        for index, changes in enumerate((
            {"sender": "neznámý"}, {"sender": "one@example.test, two@example.test"},
            {"subject": ""}, {"subject": "123 456"},
        ), 2):
            message = observed(str(index), **changes)
            self.worker.cycle(FakeSource([message]), lambda _: proposal())
            with self.assertRaises(ValueError): self.worker.remember_low_importance(message.item_id)
        self.assertNotIn("importance_preferences", self.worker.status())

    def test_preference_does_not_change_existing_reply_confirmation(self):
        self.worker._update(lambda d: d["items"][self.message.item_id].update(
            reply={"status": "prepared", "confirmation_token": "synthetic-token", "confirmation_digest": "synthetic-digest"}))
        before = self.worker.status()["items"][self.message.item_id]
        self.worker.remember_low_importance(self.message.item_id)
        self.assertEqual(self.worker.status()["items"][self.message.item_id], before)

    def test_sdk_model_receives_the_same_soft_hint_with_the_complete_source(self):
        self.worker.remember_low_importance(self.message.item_id)
        message = replace(self.message, importance_preferences=self.worker.matching_importance_preferences(self.message))
        def runner(agent, prompt, **kwargs):
            payload = json.loads(prompt)
            self.assertEqual(payload["body_text"], message.source.body_text)
            self.assertEqual(payload["importance_preferences"][0]["sender"], "sender@example.test")
            self.assertIn("ponech important=true", agent.instructions)
            return SimpleNamespace(final_output=proposal())
        self.assertTrue(SDKEmailProposer("explicit-test-model", runner=runner)(message).important)

    def test_failed_assessment_cannot_be_used_as_a_preference(self):
        self.worker._update(lambda d: d["items"][self.message.item_id].update(status="analysis_failed"))
        with self.assertRaises(ValueError): self.worker.remember_low_importance(self.message.item_id)
        self.assertNotIn("importance_preferences", self.worker.status())


class IMAPSourceTests(unittest.TestCase):
    def make_source(self, *, provider="icloud", validity=b"10", uids=b"4 2 3", search_status="OK"):
        message = observed()
        raw = message.source.original_eml
        calls = []
        class Connection:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def login(self, *_): pass
            def select(self, folder, readonly):
                calls.append(("SELECT", folder, readonly))
                return "OK", []
            def response(self, name): return name, [validity]
            def uid(self, command, *args):
                calls.append((command, *args))
                if command == "SEARCH": return search_status, [uids]
                return "OK", [(b"RFC822.SIZE " + str(len(raw)).encode(), raw)]
        config = ICloudMailConfig("account@example.test", "fake")
        with patch("app.email.continuous_source.load_icloud_mail_config", return_value=config), patch(
            "app.email.continuous_source.load_seznam_mail_config", return_value=SeznamMailConfig("account@example.test", "fake")
        ):
            source = IMAPAgentSource(provider, imap_factory=lambda *_: Connection())
        return source, calls

    def test_readonly_peek_sorted_catchup_and_range_upper_endpoint_filter(self):
        source, calls = self.make_source()
        scan = source.scan({"uidvalidity": "10", "after_uid": 2}, limit=1)
        self.assertEqual([m.source.uid for m in scan.messages], ["3"])
        self.assertIn(("SELECT", "INBOX", True), calls)
        self.assertIn(("FETCH", b"3", "(RFC822.SIZE BODY.PEEK[])"), calls)
        self.assertIn(("SEARCH", None, "UID", "3:*"), calls)

    def test_new_epoch_starts_at_oldest_uid(self):
        source, calls = self.make_source(validity=b"11")
        scan = source.scan({"uidvalidity": "10", "after_uid": 900}, limit=2)
        self.assertEqual([m.source.uid for m in scan.messages], ["2", "3"])
        self.assertIn(("SEARCH", None, "UID", "1:*"), calls)

    def test_seznam_source_keeps_provider_identity(self):
        source, _ = self.make_source(provider="seznam")
        self.assertEqual(source.scan({}).messages[0].source.provider, "seznam")

    def test_search_failure_is_not_empty_success(self):
        source, _ = self.make_source(search_status="NO")
        with self.assertRaises(RuntimeError): source.scan({})

    def test_uidvalidity_is_required(self):
        source, _ = self.make_source(validity=None)
        with self.assertRaises(RuntimeError): source.scan({})


if __name__ == "__main__":
    unittest.main()
