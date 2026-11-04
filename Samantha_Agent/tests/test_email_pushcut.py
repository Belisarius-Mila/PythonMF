from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

from app.cockpit_email_agent import email_agent_overview, email_agent_pushcut_configure_action, email_agent_pushcut_test_action
from app.email.continuous_agent import ContinuousEmailAgent
from app.email.pushcut import PushcutNotifier, pushcut_status, trigger_pushcut
from app.email.hourly_agent import HourlyEmailScheduler
from app.email.service import ServiceSettings, service_tick
from tests.test_continuous_email_agent import FakeSource, observed, proposal


WEBHOOK = "https://api.pushcut.io/synthetic-secret/notifications/SamanthaEmail"
COCKPIT = "https://synthetic.example.test/emails-to-resolve/"


class PushcutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.worker = ContinuousEmailAgent(self.root / "agent")
        self.sender = Mock(return_value={"status": "accepted"})
        self.notifier = PushcutNotifier(self.worker, sender=self.sender)
        self.now = datetime.fromisoformat("2026-11-04T12:00:00+01:00")

    def configure(self, **changes):
        return self.notifier.configure(**{"webhook_url": WEBHOOK, "cockpit_url": COCKPIT, "enabled": True, **changes})

    def cycle(self, messages=None, classify=None, now=None):
        return self.worker.cycle(FakeSource(messages or [observed()]), classify or (lambda _: proposal()), cycle_at=now or self.now)

    def events(self):
        return list(self.worker.status().get("notification_hours", {}).values())

    def test_only_new_important_cards_queue_and_same_hour_is_grouped(self):
        self.configure()
        messages = [observed(str(i)) for i in range(1, 4)]
        def classify(message):
            return proposal().model_copy(update={"important": message.source.uid != "3"})
        self.cycle(messages, classify)
        self.assertEqual(len(self.events()), 1)
        self.assertEqual(self.events()[0]["item_ids"], [m.item_id for m in messages[:2]])
        self.assertEqual(self.notifier.drain()["accepted"], 1)
        self.worker = ContinuousEmailAgent(self.worker.root)
        self.cycle(messages, lambda _: self.fail("Do not repeat model"))
        PushcutNotifier(self.worker, sender=self.sender).drain()
        self.assertEqual(self.sender.call_count, 1)
        self.assertEqual(len(email_agent_overview(worker=self.worker)["cards"]), 2)

    def test_more_messages_in_alerted_hour_do_not_ring_again_but_next_hour_does(self):
        self.configure(); self.cycle(); self.notifier.drain()
        self.cycle([observed("2")]); self.notifier.drain()
        self.assertEqual(self.sender.call_count, 1)
        self.cycle([observed("3")], now=self.now.replace(hour=13)); self.notifier.drain()
        self.assertEqual(self.sender.call_count, 2)

    def test_disabled_does_not_queue_and_enable_does_not_backfill_old_cards(self):
        self.cycle()
        self.configure()
        self.assertEqual(self.notifier.drain()["accepted"], 0)
        self.assertEqual(self.events(), [])
        self.sender.assert_not_called()

    def test_failed_analysis_never_alerts(self):
        self.configure()
        def fail(_): raise TimeoutError("model")
        self.cycle(classify=fail)
        self.notifier.drain()
        self.assertEqual(self.events(), [])
        self.sender.assert_not_called()

    def test_dismissed_or_ignored_cards_are_not_sent(self):
        self.configure(); self.cycle()
        self.worker.dismiss([observed().item_id], action="ignore")
        self.notifier.drain()
        self.assertEqual(self.events()[0]["status"], "skipped")
        self.sender.assert_not_called()

    def test_uncertain_and_rejected_results_never_repeat_after_restart(self):
        for status in ("rejected", "delivery_unknown"):
            with self.subTest(status=status):
                self.configure(); self.cycle([observed(str(self.sender.call_count+10))], now=self.now.replace(hour=14+self.sender.call_count))
                self.sender.return_value = {"status": status}
                before = self.sender.call_count
                self.notifier.drain()
                PushcutNotifier(ContinuousEmailAgent(self.worker.root), sender=self.sender).drain()
                self.assertEqual(self.sender.call_count, before+1)

    def test_process_interruption_after_durable_sending_is_not_replayed(self):
        self.configure(); self.cycle()
        self.sender.side_effect = KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt): self.notifier.drain()
        self.assertEqual(self.events()[0]["status"], "sending")
        self.sender.side_effect = None
        self.notifier.drain()
        self.assertEqual(self.events()[0]["status"], "delivery_unknown")
        self.assertEqual(self.sender.call_count, 1)

    def test_sender_failure_does_not_leak_url_or_repeat(self):
        self.configure(); self.cycle()
        self.sender.side_effect = RuntimeError(WEBHOOK)
        self.notifier.drain(); self.notifier.drain()
        public = json.dumps(email_agent_overview(worker=self.worker))
        self.assertNotIn("synthetic-secret", public)
        self.assertEqual(self.events()[0]["status"], "delivery_unknown")
        self.assertEqual(self.sender.call_count, 1)

    def test_disable_skips_unsent_notifications_and_keeps_cards(self):
        self.configure(); self.cycle()
        self.configure(webhook_url="", enabled=False)
        self.notifier.drain()
        self.assertEqual(self.events()[0]["status"], "skipped")
        self.assertEqual(len(email_agent_overview(worker=self.worker)["cards"]), 1)
        self.sender.assert_not_called()

    def test_explicit_test_works_with_service_disabled_is_idempotent_and_redacted(self):
        self.configure(enabled=False)
        result = email_agent_pushcut_test_action({"request_id":"same_test_01", "confirmed":True}, notifier=self.notifier)
        self.assertEqual(result, {"ok":True,"status":"accepted"})
        self.assertEqual(self.notifier.test(request_id="same_test_01", confirmed=True)["status"], "accepted")
        self.assertEqual(self.sender.call_count, 1)
        public = pushcut_status(self.worker)
        self.assertEqual(public["last_test_status"], "accepted")
        self.assertNotIn("synthetic-secret", json.dumps(public))
        self.assertEqual(self.worker.status()["items"], {})

    def test_changed_destination_requires_a_new_physical_test_and_does_not_echo_url(self):
        first = self.configure()
        self.notifier.test(request_id="test_old_config", confirmed=True)
        self.assertTrue(first["configured"])
        second = self.configure(webhook_url=WEBHOOK.replace("synthetic-secret", "second-secret"))
        self.assertEqual(second["last_test_status"], "")
        self.assertNotIn("secret", json.dumps(second))

    def test_latest_test_is_chosen_by_time_after_repository_sorts_request_ids(self):
        self.configure()
        self.notifier.test(request_id="zzzz_first_test", confirmed=True)
        self.sender.return_value={"status":"rejected"}
        self.notifier.test(request_id="aaaa_latest_test", confirmed=True)
        self.assertEqual(pushcut_status(ContinuousEmailAgent(self.worker.root))["last_test_status"],"rejected")

    def test_missing_confirmation_prevents_test_and_malformed_config_is_atomic(self):
        self.configure()
        before = self.worker.status()
        for payload in ({}, {"request_id":"unconfirmed_test"}, {"request_id":[],"confirmed":True}):
            self.assertFalse(email_agent_pushcut_test_action(payload, notifier=self.notifier)["ok"])
        for changes in ({"webhook_url":"https://elsewhere.test/x"}, {"enabled":"yes"},
                        {"cockpit_url":"https://localhost/emails-to-resolve/"}, {"webhook_url":None}):
            payload = {"webhook_url":WEBHOOK,"cockpit_url":COCKPIT,"enabled":True,**changes}
            self.assertFalse(email_agent_pushcut_configure_action(payload, notifier=self.notifier)["ok"])
        self.assertEqual(self.worker.status(), before)
        self.sender.assert_not_called()

    def test_simultaneous_dispatch_sends_only_once_and_card_review_stays_available(self):
        self.configure(); self.cycle()
        started, release = threading.Event(), threading.Event()
        def hold(_):
            started.set()
            if not release.wait(5): raise TimeoutError("test")
            return {"status":"accepted"}
        self.sender.side_effect = hold
        thread = threading.Thread(target=self.notifier.drain); thread.start()
        try:
            self.assertTrue(started.wait(3))
            self.assertEqual(self.notifier.drain()["status"], "busy")
            self.worker.dismiss([observed().item_id], action="dismiss")
        finally:
            release.set(); thread.join(timeout=5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(self.sender.call_count, 1)

    def test_service_flushes_pending_without_new_model_or_source_pass_in_completed_hour(self):
        self.configure(); self.cycle()
        source = FakeSource([observed()]); source.baseline_cursor = lambda:{"uidvalidity":"10","after_uid":0}
        HourlyEmailScheduler(self.worker).initialize_from_now([source])
        self.worker._update(lambda d:d.setdefault("schedule",{}).update(completed_slot=self.now.isoformat()))
        settings_path=self.root/'service.json'
        settings_path.write_text(json.dumps({**ServiceSettings().model_dump(),"enabled":True,"providers":["icloud"]}))
        with patch('app.email.service.PushcutNotifier',return_value=self.notifier):
            result=service_tick(settings_path=settings_path,worker=self.worker,now=self.now,source_factory=lambda _:source,
                                select_model=lambda:self.fail('No model catalog'))
        self.assertEqual(result['status'],'already_completed')
        self.assertEqual(result['notifications']['accepted'],1)
        self.assertEqual(source.calls,[])


class PushcutTransportTests(unittest.TestCase):
    def test_plain_post_uses_predefined_free_notification_without_dynamic_json(self):
        response=Mock(); response.status=200
        opener=Mock(); opener.open.return_value.__enter__=Mock(return_value=response)
        opener.open.return_value.__exit__=Mock(return_value=False)
        with patch('app.email.pushcut.build_opener',return_value=opener):
            self.assertEqual(trigger_pushcut(WEBHOOK),{'status':'accepted'})
        request=opener.open.call_args.args[0]
        self.assertEqual(request.get_method(),'POST')
        self.assertEqual(request.data,b'')

    def test_transport_errors_are_bounded_redacted_and_never_retried(self):
        for error, expected in ((HTTPError(WEBHOOK,404,'missing',{},None),'rejected'),
                                (HTTPError(WEBHOOK,503,'unknown',{},None),'delivery_unknown'),
                                (URLError(WEBHOOK),'delivery_unknown')):
            opener=Mock(); opener.open.side_effect=error
            with patch('app.email.pushcut.build_opener',return_value=opener): result=trigger_pushcut(WEBHOOK)
            self.assertEqual(result['status'],expected)
            self.assertNotIn('synthetic-secret',json.dumps(result))
            self.assertEqual(opener.open.call_count,1)


if __name__ == '__main__':
    unittest.main()
