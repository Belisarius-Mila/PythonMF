from __future__ import annotations

import hashlib
import smtplib
import tempfile
import unittest
import threading
from dataclasses import replace
from email import policy
from email.parser import BytesParser
from pathlib import Path
from types import SimpleNamespace

from app.email.agent_reply import AgentReplyService, ReplySMTPOutcome, ReplySMTPTransport, build_reply
from app.email.config import OutgoingMailConfig
from app.email.continuous_agent import ContinuousEmailAgent
from app.email.outbound import SentCopyResult
from app.cockpit_email_agent import email_agent_overview, email_agent_prepare_reply_action, email_agent_send_reply_action
from app.file_persistence import FileLockTimeoutError
from tests.test_continuous_email_agent import FakeSource, observed, proposal


def config(provider="icloud"):
    return OutgoingMailConfig("owner@example.test", "fake-password", "smtp.example.test", 587, "starttls", provider)


class AgentReplyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.worker = ContinuousEmailAgent(Path(self.temporary.name))
        account = hashlib.sha256(b"icloud|owner@example.test|INBOX").hexdigest()
        self.observed = replace(observed(), account=account)
        source = FakeSource([self.observed]); source.key = account
        self.worker.cycle(source, lambda _: proposal())
        self.item_id = self.observed.item_id
        self.digest = self.worker.status()["items"][self.item_id]["proposal_digest"]
        self.sent, self.copies = [], []
        def transport(raw, cfg, recipient):
            self.sent.append((raw, cfg.address, recipient))
            return ReplySMTPOutcome("smtp_sent")
        def copy(raw, cfg, stamp):
            self.copies.append(raw)
            return SentCopyResult("saved", cfg.provider, "Sent")
        self.service = AgentReplyService(self.worker, source_factory=lambda *_: SimpleNamespace(read_item=lambda item: self.observed),
                                         config_loader=lambda _: config(), transport=transport, sent_copy_saver=copy)

    def prepare(self):
        return self.service.prepare(self.item_id, expected_digest=self.digest)

    def send(self, prepared, **overrides):
        args = {"confirmation_token": prepared["confirmation_token"], "confirmation_digest": prepared["confirmation_digest"], "confirmed": True}
        args.update(overrides)
        return self.service.send(self.item_id, **args)

    def test_prepare_does_not_send_and_captures_recipient_final_subject_and_text(self):
        prepared = self.prepare()
        self.assertEqual(self.sent, [])
        self.assertEqual(prepared["recipient"], "sender@example.test")
        self.assertEqual(prepared["sender"], "owner@example.test")
        self.assertEqual(prepared["body"], proposal().reply_draft)
        self.assertNotIn("message_b64", prepared)

    def test_second_confirmation_sends_once_and_copies_sent_message(self):
        prepared = self.prepare()
        receipt = self.send(prepared)
        self.assertEqual(receipt["status"], "smtp_sent")
        self.assertEqual(receipt["sent_copy_status"], "saved")
        self.assertEqual(self.send(prepared), receipt)
        self.assertEqual(len(self.sent), 1)
        self.assertEqual(len(self.copies), 1)
        parsed = BytesParser(policy=policy.default).parsebytes(self.sent[0][0])
        self.assertEqual(parsed["In-Reply-To"], "<test@example.test>")
        self.assertEqual(parsed.get_body().get_content().rstrip(), proposal().reply_draft)

    def test_missing_wrong_or_false_confirmation_never_calls_smtp(self):
        prepared = self.prepare()
        for overrides in ({"confirmed": False}, {"confirmation_token": ""}, {"confirmation_token": "wrong"}, {"confirmation_digest": "changed"}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError): self.send(prepared, **overrides)
        self.assertEqual(self.sent, [])

    def test_edit_invalidates_previous_confirmation_and_sends_only_new_text(self):
        old = self.prepare()
        changed = proposal().model_copy(update={"reply_subject": "Upravený předmět", "reply_draft": "Úplně nový text"})
        self.digest = self.worker.edit_proposal(self.item_id, changed, expected_digest=self.digest)
        with self.assertRaises(ValueError): self.send(old)
        new = self.prepare()
        self.assertNotEqual(old["confirmation_token"], new["confirmation_token"])
        self.send(new)
        parsed = BytesParser(policy=policy.default).parsebytes(self.sent[0][0])
        self.assertEqual(parsed["Subject"], "Upravený předmět")
        self.assertEqual(parsed.get_body().get_content().rstrip(), "Úplně nový text")

    def test_new_preparation_invalidates_an_old_token_even_without_text_changes(self):
        old, new = self.prepare(), self.prepare()
        with self.assertRaises(ValueError): self.send(old)
        self.send(new)
        self.assertEqual(len(self.sent), 1)

    def test_source_or_account_changes_prevent_preparation(self):
        original = self.observed
        self.observed = replace(original, source=replace(original.source, original_eml=b"changed"))
        with self.assertRaises(ValueError): self.prepare()
        self.observed = original
        self.service.config_loader = lambda _: replace(config(), address="other@example.test")
        with self.assertRaises(ValueError): self.prepare()

    def test_changed_envelope_recipient_invalidates_the_frozen_confirmation(self):
        prepared = self.prepare()
        self.worker._update(lambda d: d['items'][self.item_id]['reply'].update(recipient='different@example.test'))
        with self.assertRaises(ValueError): self.send(prepared)
        self.assertEqual(self.sent, [])

    def test_changed_sender_account_after_preparation_prevents_send(self):
        prepared = self.prepare()
        self.service.config_loader = lambda _: replace(config(), address='other@example.test')
        with self.assertRaises(ValueError): self.send(prepared)
        self.assertEqual(self.sent, [])

    def test_parallel_confirmation_cannot_send_twice_or_block_other_cards(self):
        second = replace(observed('2'), account=self.observed.account)
        source = FakeSource([second]); source.key = second.account
        self.worker.cycle(source, lambda _: proposal())
        prepared = self.prepare()
        started, release = threading.Event(), threading.Event()
        receipts, errors = [], []
        original_transport = self.service.transport
        def blocked_transport(*args):
            started.set()
            if not release.wait(5): raise TimeoutError('test transport')
            return original_transport(*args)
        self.service.transport = blocked_transport
        def first_send():
            try: receipts.append(self.send(prepared))
            except BaseException as exc: errors.append(exc)
        thread = threading.Thread(target=first_send)
        thread.start()
        try:
            self.assertTrue(started.wait(3))
            with self.assertRaises(FileLockTimeoutError): self.send(prepared)
            self.worker.dismiss([second.item_id], action='dismiss')
            with self.assertRaises(ValueError):
                self.worker.edit_proposal(self.item_id, proposal(), expected_digest=self.digest)
        finally:
            release.set(); thread.join(timeout=5)
        self.assertEqual(errors, [])
        self.assertEqual(len(self.sent), 1)
        self.assertEqual(receipts[0]['status'], 'smtp_sent')

    def test_unknown_send_outcome_blocks_retry_and_new_preparation(self):
        self.service.transport = lambda *_: ReplySMTPOutcome("delivery_unknown")
        prepared = self.prepare()
        self.assertEqual(self.send(prepared)["status"], "delivery_unknown")
        with self.assertRaises(ValueError): self.send(prepared)
        with self.assertRaises(ValueError): self.prepare()

    def test_interrupted_send_stays_visible_without_repeating_transport(self):
        def crash(*_): raise KeyboardInterrupt()
        self.service.transport = crash
        prepared = self.prepare()
        with self.assertRaises(KeyboardInterrupt): self.send(prepared)
        self.service.transport = lambda *_: self.fail("Must not repeat an interrupted send")
        with self.assertRaises(ValueError): self.send(prepared)
        self.assertEqual(self.worker.status()["items"][self.item_id]["reply"]["status"], "delivery_unknown")

    def test_sent_copy_failure_cannot_turn_accepted_smtp_into_a_retry(self):
        def fail(*_): raise OSError("IMAP unavailable")
        self.service.sent_copy_saver = fail
        prepared = self.prepare()
        receipt = self.send(prepared)
        self.assertEqual(receipt["status"], "smtp_sent")
        self.assertEqual(receipt["sent_copy_status"], "failed")
        self.send(prepared)
        self.assertEqual(len(self.sent), 1)

    def test_archiving_does_not_remove_a_needed_reply_and_edit_cannot_change_archive_metadata(self):
        self.worker.accept_archive(self.observed, confirmed_digest=self.digest)
        self.assertEqual(len(email_agent_overview(worker=self.worker)["cards"]), 1)
        changed = proposal().model_copy(update={"reply_draft": "Odpověď po uložení"})
        self.digest = self.worker.edit_proposal(self.item_id, changed, expected_digest=self.digest)
        bad = changed.model_copy(update={"summary": "Changed archive"})
        with self.assertRaises(ValueError): self.worker.edit_proposal(self.item_id, bad, expected_digest=self.digest)
        self.send(self.prepare())
        self.assertEqual(email_agent_overview(worker=self.worker)["cards"], [])
        self.assertEqual(len(email_agent_overview(worker=self.worker)["archived"]), 1)

    def test_cockpit_endpoints_return_confirmation_then_send_receipt(self):
        prepared = email_agent_prepare_reply_action({"id": self.item_id, "expected_digest": self.digest}, service=self.service)
        self.assertTrue(prepared["ok"])
        self.assertEqual(self.sent, [])
        result = email_agent_send_reply_action({"id": self.item_id, "confirmed": True, **prepared["prepared"]}, service=self.service)
        self.assertEqual(result["receipt"]["status"], "smtp_sent")
        public = email_agent_overview(worker=self.worker)["cards"][0]["reply"]
        self.assertNotIn("confirmation_token", public)
        self.assertNotIn("message_b64", public)


class ReplyHeaderTests(unittest.TestCase):
    def message(self, **headers):
        original = observed()
        parent = BytesParser(policy=policy.default).parsebytes(original.source.original_eml)
        for key, value in headers.items(): parent[key.replace("_", "-")] = value
        return replace(original, source=replace(original.source, original_eml=parent.as_bytes()))

    def test_reply_to_takes_precedence_over_from_and_preserves_thread(self):
        original = self.message(Reply_To='Firma <replies@example.test>', References='<older@example.test>')
        reply = build_reply(original, proposal().model_dump(), config())
        self.assertIn('replies@example.test', str(reply['To']))
        self.assertEqual(reply['References'], '<older@example.test> <test@example.test>')
        self.assertEqual(reply['In-Reply-To'], '<test@example.test>')

    def test_multiple_reply_recipients_are_not_silently_selected(self):
        with self.assertRaises(ValueError):
            build_reply(self.message(Reply_To='a@example.test, b@example.test'), proposal().model_dump(), config())

    def test_changed_subject_and_newlines_are_not_turned_into_extra_headers(self):
        value = proposal().model_dump(); value['reply_subject'] = 'Subject\r\nBcc: hidden@example.test'
        with self.assertRaises(ValueError): build_reply(observed(), value, config())


class ReplyTransportTests(unittest.TestCase):
    def run_transport(self, *, send_error=None, login_error=None, quit_error=None):
        calls = []
        class SMTP:
            def __enter__(self): return self
            def __exit__(self, *_):
                if quit_error: raise quit_error
            def ehlo(self): pass
            def starttls(self, **kwargs): calls.append('tls')
            def login(self, *_):
                if login_error: raise login_error
            def send_message(self, message, **kwargs):
                calls.append(kwargs)
                if send_error: raise send_error
                return {}
        raw = build_reply(observed(), proposal().model_dump(), config()).as_bytes()
        result = ReplySMTPTransport(smtp_factory=lambda *args, **kwargs: SMTP())(raw, config(), 'sender@example.test')
        return result, calls

    def test_confirmed_data_survives_quit_failure(self):
        outcome, calls = self.run_transport(quit_error=OSError('QUIT'))
        self.assertEqual(outcome.status, 'smtp_sent')
        self.assertFalse(outcome.session_close_ok)
        self.assertEqual(calls[-1]['to_addrs'], ['sender@example.test'])
        self.assertEqual(calls[-1]['from_addr'], 'owner@example.test')

    def test_login_failure_is_known_not_sent(self):
        outcome, calls = self.run_transport(login_error=smtplib.SMTPAuthenticationError(535,b'no'))
        self.assertEqual(outcome.status, 'not_sent')
        self.assertEqual(calls, ['tls'])

    def test_disconnect_during_send_is_unknown(self):
        outcome, _ = self.run_transport(send_error=smtplib.SMTPServerDisconnected('lost'))
        self.assertEqual(outcome.status, 'delivery_unknown')

    def test_explicit_smtp_data_rejection_is_known_not_sent(self):
        outcome, _ = self.run_transport(send_error=smtplib.SMTPDataError(554,b'rejected'))
        self.assertEqual(outcome.status, 'not_sent')


if __name__ == '__main__': unittest.main()
