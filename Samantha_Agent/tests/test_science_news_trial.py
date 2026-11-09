import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from app import science_news_trial as trial
from app.science_news_model import TRANSLATION_INSTRUCTIONS, TRANSLATION_SCHEMA
from tests.test_science_news_model import Client


class TrialTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        paths = {name: self.root / name.lower() for name in ("REPORT", "PACKET", "SOURCE", "STATE")}
        patched = patch.multiple(trial, **paths)
        patched.start()
        self.addCleanup(patched.stop)
        source = "A complete synthetic public source paragraph. " * 20
        trial.SOURCE.write_text(source)
        payload = {"source_text": source}
        packet = {"payload": payload, "instructions": TRANSLATION_INSTRUCTIONS, "schema": TRANSLATION_SCHEMA}
        trial.PACKET.write_text(json.dumps(packet, ensure_ascii=False, sort_keys=True))
        proxy = len(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()) + len(TRANSLATION_INSTRUCTIONS.encode()) + len(json.dumps(TRANSLATION_SCHEMA).encode())
        self.report = {"request_id": trial.REQUEST, "candidate_model": "gpt-6.1-sol", "reasoning_effort": "medium",
            "speed": "Standard", "proposed_acceptance_credits": 5, "accepted_output_tokens": 16000,
            "packet_sha256": trial.sha(trial.PACKET.read_bytes()), "source_sha256": trial.sha(trial.SOURCE.read_bytes()),
            "trial_code_sha256": trial.sha(Path(trial.__file__).read_bytes()),
            "trial_dependency_sha256": {name: trial.sha((trial.ROOT / name).read_bytes()) for name in trial.DEPENDENCIES},
            "body_proxy_credits": proxy * 50 / 1000000 + 4}
        trial.REPORT.write_text(json.dumps(self.report))
        self.frozen = trial.preview()
        self.args = {"confirmed": True, "approval_ref": "fixture-explicit-approval",
            "approved_report_sha256": self.frozen["report_sha256"], "approved_packet_sha256": self.frozen["packet_sha256"]}

    def client(self, **changes):
        client = Client()
        request = client.inner.request
        def account_checked(method, params):
            if method == "account/read":
                return {"account": {"type": "chatgpt"}}
            return request(method, params)
        client.inner.request = account_checked
        client.list_models = lambda **kw: [{"model": "gpt-6.1-sol", "supportedReasoningEfforts": [{"reasoningEffort": "medium"}]}]
        original = client.send_text
        def send(**kw):
            receipt = original(**kw)
            receipt.answer = json.dumps({"translation": "Úplný český překlad syntetického textu. " * 20, "complete": True})
            for key, value in changes.items():
                setattr(receipt, key, value)
            return receipt
        client.send_text = send
        return client

    def test_preview_and_missing_confirmation_are_nonpaid_and_do_not_create_state(self):
        factory = Mock()
        with self.assertRaises(ValueError):
            trial.run(client_factory=factory)
        factory.assert_not_called()
        self.assertFalse(trial.STATE.exists())

    def test_changed_source_or_wrong_approval_blocks_before_client(self):
        factory = Mock()
        args = {**self.args, "approved_report_sha256": "0" * 64}
        with self.assertRaises(ValueError):
            trial.run(**args, client_factory=factory)
        trial.SOURCE.write_text("changed")
        with self.assertRaises(ValueError):
            trial.run(**self.args, client_factory=factory)
        factory.assert_not_called()
        self.assertFalse(trial.STATE.exists())

    def test_one_shared_candidate_turn_has_standard_permissions_and_replay_is_read_only(self):
        client = self.client()
        factory = Mock(return_value=client)
        result = trial.run(**self.args, client_factory=factory)
        self.assertEqual(result["state"], "review")
        self.assertTrue(result["semantic_review_required"])
        self.assertEqual(trial.run(**self.args, client_factory=factory), result)
        self.assertEqual(factory.call_count, 1)
        turns = [params for method, params in client.inner.calls if method == "turn/start"]
        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0]["serviceTierForTurn"], "default")
        self.assertEqual(turns[0]["sandboxPolicy"], {"type": "readOnly", "networkAccess": False})
        self.assertEqual(turns[0]["outputSchema"], TRANSLATION_SCHEMA)

    def test_attempt_receipt_precedes_connection_and_unknown_never_retries(self):
        def connect():
            receipt = json.loads((trial.STATE / "receipt.json").read_text())
            self.assertEqual(receipt["state"], "delivery_unknown")
            raise TimeoutError("unknown connection")
        factory = Mock(side_effect=connect)
        with self.assertRaises(TimeoutError):
            trial.run(**self.args, client_factory=factory)
        with self.assertRaises(ValueError):
            trial.run(**self.args, client_factory=factory)
        self.assertEqual(factory.call_count, 1)

    def test_missing_candidate_cannot_fallback_or_start_thread(self):
        client = self.client()
        client.list_models = lambda **kw: []
        with self.assertRaises(ValueError):
            trial.run(**self.args, client_factory=Mock(return_value=client))
        self.assertFalse(client.inner.calls)

    def test_api_key_or_unknown_account_blocks_before_thread_or_turn(self):
        for account in ({"type": "apiKey"}, None):
            with self.subTest(account=account), patch.object(trial, "STATE", self.root / f"account_{len(list(self.root.iterdir()))}"):
                client = self.client()
                client.inner.request = Mock(return_value={"account": account})
                with self.assertRaises(ValueError):
                    trial.run(**self.args, client_factory=Mock(return_value=client))
                self.assertEqual(client.inner.request.call_args.args[0], "account/read")
                self.assertEqual(client.inner.request.call_count, 1)

    def test_lost_response_after_turn_start_is_not_resent(self):
        client = self.client()
        original = client.send_text
        def lost(**kw):
            original(**kw)
            raise TimeoutError("response lost after send")
        client.send_text = lost
        factory = Mock(return_value=client)
        with self.assertRaises(TimeoutError):
            trial.run(**self.args, client_factory=factory)
        with self.assertRaises(ValueError):
            trial.run(**self.args, client_factory=factory)
        self.assertEqual(factory.call_count, 1)
        self.assertEqual(sum(method == "turn/start" for method, _ in client.inner.calls), 1)

    def test_bad_delivery_usage_or_schema_preserves_raw_result_and_blocks_repeat(self):
        for changes in ({"delivered": False}, {"thread_id": "wrong"}, {"thread_token_usage": None},
                        {"thread_token_usage": {"input_tokens": 10, "output_tokens": 21000, "total_tokens": 21010}},
                        {"answer": '{"translation":"krátce","complete":false}'}):
            with self.subTest(changes=changes), patch.object(trial, "STATE", self.root / f"state_{len(list(self.root.iterdir()))}"):
                factory = Mock(return_value=self.client(**changes))
                with self.assertRaises(ValueError):
                    trial.run(**self.args, client_factory=factory)
                saved = json.loads((trial.STATE / "receipt.json").read_text())
                self.assertIn("raw_answer", saved)
                self.assertEqual(saved["state"], "attention")
                with self.assertRaises(ValueError):
                    trial.run(**self.args, client_factory=factory)
                self.assertEqual(factory.call_count, 1)

    def test_packet_change_after_preflight_stops_before_paid_turn(self):
        client = self.client()
        def catalog(**kw):
            trial.PACKET.write_text("changed")
            return [{"model": "gpt-6.1-sol", "supportedReasoningEfforts": [{"reasoningEffort": "medium"}]}]
        client.list_models = catalog
        with self.assertRaises(ValueError):
            trial.run(**self.args, client_factory=Mock(return_value=client))
        self.assertFalse(any(method == "turn/start" for method, _ in client.inner.calls))

    def test_symlink_state_is_rejected_before_client(self):
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        trial.STATE.symlink_to(elsewhere, target_is_directory=True)
        factory = Mock()
        with self.assertRaises(ValueError):
            trial.run(**self.args, client_factory=factory)
        factory.assert_not_called()
        self.assertFalse(list(elsewhere.iterdir()))
