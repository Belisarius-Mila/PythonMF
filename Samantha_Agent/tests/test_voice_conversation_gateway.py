"""Candidate broker contracts: fake provider, private temp receipts, no API calls."""

from __future__ import annotations

import copy
import io
import json
import tempfile
import threading
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

from app.communication.voice_conversation_gateway import (
    CandidateVoiceGateway, CandidateVoiceGrant, OpenAILiveProvider, VoiceAttemptJournal,
    VoiceGatewayError, VoiceSessionSupervisor, _BoundedSnapshot, _NoRedirect,
)
from app.communication.voice_conversation_pilot import VoiceBinding


BINDING = VoiceBinding("synthetic-stream", "synthetic-thread")
HEADERS = {"Origin": "https://synthetic.example", "Content-Type": "application/json",
           "X-Voice-CSRF": "synthetic-csrf-token-1234567890"}
OFFER = json.dumps({"sdp": "v=0\r\nsynthetic-offer"}).encode()
SNAPSHOT = {"workstream_id": "synthetic-stream", "session": {
    "thread_id": "synthetic-thread", "turn_busy": True,
    "active_turn": {"client_message_id": "synthetic-long-task"},
    "messages": [{"answer": "SYNTHETIC PRIVATE", "status": "pending"}],
}}


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class FakeSideband:
    def __init__(self, clock):
        self.clock = clock
        self.events = []
        self.sent = []
        self.closed = False
        self.confirm_close = True
        self.error = None

    def recv(self, *, timeout):
        if self.error:
            raise self.error
        if self.events:
            return self.events.pop(0)
        self.clock.now += timeout
        raise TimeoutError()

    def send(self, event):
        self.sent.append(copy.deepcopy(event))
        if event["type"] == "session.close" and self.confirm_close:
            self.events.append({"type": "session.closed", "event_id": "final-close",
                                "usage": {"seconds": 60}, "reason": "close_requested"})

    def close(self):
        self.closed = True


class FakeProvider:
    def __init__(self, clock):
        self.sideband = FakeSideband(clock)
        self.created = []
        self.attached = []
        self.hung_up = []
        self.response = {"session": {"id": "synthetic-voice"},
                         "transport": {"type": "webrtc", "sdp": "v=0\r\nsynthetic-answer"}}
        self.create_error = self.attach_error = None

    def create(self, payload, **_kwargs):
        self.created.append(copy.deepcopy(payload))
        if self.create_error:
            raise self.create_error
        return copy.deepcopy(self.response)

    def attach(self, identity, **_kwargs):
        self.attached.append(identity)
        if self.attach_error:
            raise self.attach_error
        return self.sideband

    def hangup(self, identity, **_kwargs):
        self.hung_up.append(identity)


class ManualSupervisor(VoiceSessionSupervisor):
    def start(self):
        pass  # Tests run the same event loop explicitly with a fake clock.


class GatewayTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name) / "own-private-voice-receipts"
        self.clock = FakeClock()
        self.provider = FakeProvider(self.clock)
        self.reader = Mock(return_value=copy.deepcopy(SNAPSHOT))
        self.grant = CandidateVoiceGrant("synthetic-approved-test-1", "synthetic-owner", "gpt-live-1",
                                         BINDING, confirmed_live_test=True)
        self.journal = VoiceAttemptJournal(self.directory)
        self.gateway = self.new_gateway()

    def new_gateway(self, **kwargs):
        return CandidateVoiceGateway(grant=self.grant, provider=self.provider, journal=self.journal,
            read_snapshot=self.reader, origin=HEADERS["Origin"], csrf_token=HEADERS["X-Voice-CSRF"],
            wall_clock=self.clock, monotonic=self.clock, supervisor_factory=ManualSupervisor, **kwargs)

    def create(self, gateway=None, headers=None, body=OFFER, principal="synthetic-owner"):
        return (gateway or self.gateway).create(principal=principal, headers=headers or HEADERS, body=body)

    def receipt(self):
        return self.journal.read(self.grant.request_id)

    def test_construction_is_inert(self):
        self.assertFalse(self.directory.exists())
        self.reader.assert_not_called()
        self.assertEqual(self.provider.created, [])

    def test_candidate_approval_is_not_a_paid_test_grant(self):
        self.gateway.grant = replace(self.grant, confirmed_live_test=False)
        with self.assertRaises(VoiceGatewayError):
            self.create()
        self.assertFalse(self.directory.exists())
        self.assertEqual(self.provider.created, [])

    def test_wrong_principal_origin_and_csrf_never_read_or_create(self):
        for principal, headers in [("other", HEADERS), ("synthetic-owner", {**HEADERS, "Origin": "https://elsewhere.example"}),
                                   ("synthetic-owner", {**HEADERS, "X-Voice-CSRF": "špatně"})]:
            with self.subTest(principal=principal, headers=headers), self.assertRaises(VoiceGatewayError):
                self.create(principal=principal, headers=headers)
        self.reader.assert_not_called()
        self.assertFalse(self.directory.exists())
        self.assertEqual(self.provider.created, [])

    def test_browser_cannot_select_model_thread_or_backend_operation(self):
        for extra in ({"model": "other"}, {"thread_id": "other"}, {"method": "send_email"}):
            with self.subTest(extra=extra), self.assertRaises(VoiceGatewayError):
                self.create(body=json.dumps({"sdp": "v=0", **extra}).encode())
        self.assertEqual(self.provider.created, [])

    def test_http_header_names_are_case_insensitive_and_duplicates_fail_closed(self):
        with self.assertRaises(VoiceGatewayError):
            self.create(headers={**HEADERS, "origin": HEADERS["Origin"]})
        self.assertEqual(self.provider.created, [])
        self.create(headers={name.lower(): value for name, value in HEADERS.items()})
        self.assertEqual(len(self.provider.created), 1)

    def test_invalid_body_and_content_type_fail_before_reservation(self):
        for body in (b"x" * 65537, b"not json", b"[]", b'{"sdp":"bad"}'):
            with self.subTest(body=body[:20]), self.assertRaises(VoiceGatewayError):
                self.create(body=body)
        with self.assertRaises(VoiceGatewayError):
            self.create(headers={**HEADERS, "Content-Type": "text/plain"})
        self.assertFalse(self.directory.exists())

    def test_binding_change_blocks_paid_request(self):
        self.reader.return_value["session"]["thread_id"] = "different"
        with self.assertRaises(VoiceGatewayError):
            self.create()
        self.assertEqual(self.provider.created, [])

    def test_create_reserves_before_provider_and_uses_only_selected_model(self):
        original = self.provider.create

        def inspect_reservation(payload, **kwargs):
            self.assertEqual(self.receipt()["state"], "creating")
            return original(payload, **kwargs)

        self.provider.create = inspect_reservation
        answer = self.create()
        self.assertEqual(answer["session"]["id"], "synthetic-voice")
        self.assertEqual(self.provider.created[0]["session"]["model"], "gpt-live-1")
        self.assertEqual(self.receipt()["state"], "active")
        self.assertEqual(self.provider.attached, ["synthetic-voice"])
        self.assertEqual(self.provider.sideband.sent, [])  # No session.start on sideband.

    def test_restart_and_duplicate_never_create_again(self):
        self.create()
        for gateway in (self.gateway, self.new_gateway()):
            with self.assertRaises(VoiceGatewayError):
                self.create(gateway)
        self.assertEqual(len(self.provider.created), 1)

    def test_concurrent_create_has_single_durable_winner(self):
        barrier = threading.Barrier(2)
        successes, failures = [], []

        def attempt():
            gateway = self.new_gateway()
            barrier.wait(timeout=2)
            try:
                successes.append(self.create(gateway))
            except VoiceGatewayError:
                failures.append(True)

        workers = [threading.Thread(target=attempt) for _ in range(2)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=5)
        self.assertFalse(any(worker.is_alive() for worker in workers))
        self.assertEqual(len(successes), 1)
        self.assertEqual(len(failures), 1)
        self.assertEqual(len(self.provider.created), 1)

    def test_unknown_creation_retains_receipt_and_never_retries(self):
        self.provider.create_error = TimeoutError("SYNTHETIC PRIVATE")
        for _ in range(2):
            with self.assertRaises(VoiceGatewayError) as caught:
                self.create()
            self.assertNotIn("PRIVATE", str(caught.exception))
        self.assertEqual(len(self.provider.created), 1)
        self.assertEqual(self.receipt()["state"], "creation_unknown")
        self.assertEqual(self.provider.attached, [])

    def test_malformed_answer_or_failed_attach_cleans_known_session_once(self):
        self.provider.response["transport"] = {"sdp": "bad"}
        with self.assertRaises(VoiceGatewayError):
            self.create()
        self.assertEqual(self.provider.hung_up, ["synthetic-voice"])
        self.assertEqual(self.receipt()["state"], "finalization_unknown")
        self.assertFalse(self.receipt()["final_usage_confirmed"])

    def test_failed_attach_never_returns_sdp_or_recreates(self):
        self.provider.attach_error = OSError("SYNTHETIC PRIVATE")
        with self.assertRaises(VoiceGatewayError):
            self.create()
        self.assertEqual(self.provider.hung_up, ["synthetic-voice"])
        self.assertEqual(self.receipt()["session_id"], "synthetic-voice")
        with self.assertRaises(VoiceGatewayError):
            self.create(self.new_gateway())
        self.assertEqual(len(self.provider.created), 1)

    def test_failure_to_persist_known_session_prevents_attach(self):
        with patch.object(self.journal, "record", side_effect=OSError("disk unavailable")):
            with self.assertRaises(VoiceGatewayError):
                self.create()
        self.assertEqual(self.provider.attached, [])
        self.assertEqual(self.provider.hung_up, ["synthetic-voice"])
        self.assertEqual(self.receipt()["state"], "creating")
        with self.assertRaises(VoiceGatewayError):
            self.create(self.new_gateway())
        self.assertEqual(len(self.provider.created), 1)

    def test_server_watchdog_closes_voice_without_browser_or_backend_cancellation(self):
        before = copy.deepcopy(self.reader.return_value)
        self.create()
        self.gateway.supervisor.run()
        self.assertEqual(self.provider.sideband.sent, [self.provider.sideband.sent[0]])
        self.assertEqual(self.provider.sideband.sent[0]["type"], "session.close")
        self.assertEqual(self.receipt()["state"], "closed")
        self.assertTrue(self.receipt()["final_usage_confirmed"])
        self.assertEqual(self.reader.return_value, before)
        self.reader.assert_called_once()  # Initial binding check only.

    def test_close_deadline_without_final_usage_records_unknown(self):
        self.provider.sideband.confirm_close = False
        self.create()
        self.gateway.supervisor.run()
        self.assertEqual(self.receipt()["state"], "finalization_unknown")
        self.assertFalse(self.receipt()["final_usage_confirmed"])
        self.assertEqual(self.provider.hung_up, ["synthetic-voice"])
        self.assertEqual(len(self.provider.created), 1)

    def test_reflected_audio_without_id_is_discarded_and_final_usage_is_cumulative(self):
        self.create()
        self.provider.sideband.events = [
            {"type": "session.input_audio.append", "audio": "SYNTHETIC AUDIO"},
            {"type": "session.output_audio.delta", "delta": "SYNTHETIC AUDIO"},
            {"type": "session.usage.updated", "event_id": "u1", "usage": {"seconds": 12}},
            {"type": "session.usage.updated", "event_id": "u2", "usage": {"seconds": 15}},
            {"type": "session.closed", "event_id": "u3", "usage": {"seconds": 16}},
        ]
        self.gateway.supervisor.run()
        self.assertEqual(self.receipt()["seconds"], 16)
        self.assertTrue(self.receipt()["final_usage_confirmed"])
        text = self.journal.path(self.grant.request_id).read_text()
        self.assertNotIn("AUDIO", text)
        self.assertNotIn("PRIVATE", text)
        self.assertNotIn("sdp", text)
        self.assertEqual(self.directory.stat().st_mode & 0o777, 0o700)
        self.assertEqual(self.journal.path(self.grant.request_id).stat().st_mode & 0o777, 0o600)

    def test_client_delegation_deduplicated_and_cannot_execute_write_tools(self):
        self.create()
        delegation = {"type": "session.delegation.created", "event_id": "d1",
                      "delegation": {"id": "task-1", "target": "client"}}
        self.provider.sideband.events = [
            delegation, {**delegation, "event_id": "d2"},
            {"type": "response.event", "event_id": "fake-tool", "event": {"type": "function_call", "name": "send_email"}},
            {"type": "session.closed", "event_id": "final", "usage": {"seconds": 2}},
        ]
        self.gateway.supervisor.run()
        results = [value for value in self.provider.sideband.sent if value["type"] == "session.commentary.append"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["delegation_id"], "task-1")
        self.assertIn("právě pracuje", results[0]["content"])
        self.assertNotIn("PRIVATE", json.dumps(results))
        self.assertEqual(self.reader.call_count, 2)  # Initial bind + one delegated read.

    def test_socket_loss_never_claims_final_usage_or_cancels_backend(self):
        self.create()
        self.provider.sideband.error = OSError("synthetic drop")
        self.gateway.supervisor.run()
        self.assertEqual(self.receipt()["state"], "finalization_unknown")
        self.assertEqual(self.provider.hung_up, ["synthetic-voice"])
        self.reader.assert_called_once()

    def test_abandon_is_bound_to_owner_and_original_session(self):
        self.create()
        with self.assertRaises(VoiceGatewayError):
            self.gateway.abandon(principal="synthetic-owner", headers=HEADERS, body=b'{"session_id":"other"}')
        result = self.gateway.abandon(principal="synthetic-owner", headers=HEADERS, body=b'{"session_id":"synthetic-voice"}')
        self.assertTrue(result["close_requested"])
        self.assertFalse(result["final_usage_confirmed"])
        self.gateway.supervisor.run()
        self.assertTrue(self.receipt()["final_usage_confirmed"])

    def test_abandon_after_restart_requires_audit_of_original_receipt(self):
        self.create()
        with self.assertRaises(VoiceGatewayError):
            self.new_gateway().abandon(principal="synthetic-owner", headers=HEADERS,
                                       body=b'{"session_id":"synthetic-voice"}')
        self.assertEqual(self.provider.hung_up, [])

    def test_unknown_creation_cannot_acknowledge_a_null_session_close(self):
        self.provider.create_error = TimeoutError()
        with self.assertRaises(VoiceGatewayError):
            self.create()
        with self.assertRaises(VoiceGatewayError):
            self.gateway.abandon(principal="synthetic-owner", headers=HEADERS, body=b'{"session_id":null}')
        self.assertEqual(self.receipt()["state"], "creation_unknown")

    def test_transport_cleanup_failure_does_not_emit_raw_error_or_lose_final_usage(self):
        self.create()
        self.provider.sideband.close = Mock(side_effect=OSError("SYNTHETIC PRIVATE"))
        self.gateway.supervisor.run()
        self.assertTrue(self.gateway.supervisor.done.is_set())
        self.assertTrue(self.receipt()["final_usage_confirmed"])

    def test_dispatch_is_exact_and_denies_unauthenticated_requests(self):
        base = dict(principal="synthetic-owner", headers=HEADERS, body=OFFER)
        self.assertIsNone(self.gateway.dispatch(method="POST", path="/api/not-voice", **base))
        path = "/api/human-adam/voice-candidate/session"
        self.assertEqual(self.gateway.dispatch(method="GET", path=path, **base)[0], 405)
        self.assertEqual(self.gateway.dispatch(method="POST", path=path, **{**base, "principal": None})[0], 403)
        self.assertEqual(self.gateway.dispatch(method="POST", path=path, **base)[0], 201)
        code, response = self.gateway.dispatch(method="POST", path=path, **base)
        self.assertEqual(code, 409)
        self.assertIs(response["retry_allowed"], False)

    def test_terminal_receipt_cannot_be_overwritten_by_late_close(self):
        self.create()
        self.gateway.supervisor.run()
        before = self.receipt()
        self.journal.record(self.grant.request_id, state="closing", final_usage_confirmed=False)
        self.assertEqual(self.receipt(), before)

    def test_only_candidate_model_and_reviewed_window_are_accepted(self):
        for grant in [replace(self.grant, model="other"), replace(self.grant, max_seconds=61),
                      replace(self.grant, max_seconds=True), replace(self.grant, request_id="../bad")]:
            with self.subTest(grant=grant), self.assertRaises(VoiceGatewayError):
                grant.validate()

    def test_candidate_capability_is_registered_with_separate_confirmation(self):
        from app.capabilities import get_capability
        record = get_capability("create_voice_candidate_session")
        self.assertTrue(record.requires_confirmation)
        self.assertEqual(record.voice_allowed, "blocked")
        self.assertEqual(record.confirmation_policy, "exact_current_message")


class SnapshotDeadlineTests(unittest.TestCase):
    def test_slow_reader_is_bounded_and_not_spawned_again_while_unfinished(self):
        release = threading.Event()
        self.addCleanup(release.set)
        reader = Mock(side_effect=lambda: release.wait(timeout=2))
        bounded = _BoundedSnapshot(reader, timeout=0.01)
        with self.assertRaises(VoiceGatewayError):
            bounded()
        first = bounded.worker
        with self.assertRaises(VoiceGatewayError):
            bounded()
        self.assertIs(bounded.worker, first)
        reader.assert_called_once()
        release.set()
        first.join(timeout=1)
        self.assertFalse(first.is_alive())


class ProviderTransportTests(unittest.TestCase):
    def test_provider_is_inert_and_transport_is_fixed_origin_without_retries(self):
        opener = Mock()
        response = io.BytesIO(b'{"session":{"id":"synthetic"}}')
        opener.open.return_value = response
        provider = OpenAILiveProvider("synthetic-secret", opener=opener)
        opener.open.assert_not_called()
        self.assertNotIn("synthetic-secret", repr(provider))
        provider.create({"session": {"model": "gpt-live-1"}})
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.openai.com/v1/live/sessions")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(opener.open.call_count, 1)
        self.assertIsNone(_NoRedirect().redirect_request(None, None, None, None, None, None))

    def test_provider_failure_is_safe_and_single_attempt(self):
        opener = Mock()
        opener.open.side_effect = TimeoutError("synthetic-secret PRIVATE")
        provider = OpenAILiveProvider("synthetic-secret", opener=opener)
        with self.assertRaises(VoiceGatewayError) as caught:
            provider.create({})
        self.assertNotIn("PRIVATE", str(caught.exception))
        self.assertNotIn("synthetic-secret", str(caught.exception))
        opener.open.assert_called_once()

    def test_sideband_attaches_to_exact_session_with_private_logging(self):
        connect = Mock()
        provider = OpenAILiveProvider("synthetic-secret", connect=connect)
        provider.attach("live_synthetic")
        self.assertEqual(connect.call_args.args[0], "wss://api.openai.com/v1/live/sessions/live_synthetic/attach")
        self.assertEqual(connect.call_args.kwargs["additional_headers"]["Authorization"], "Bearer synthetic-secret")
        self.assertGreaterEqual(connect.call_args.kwargs["logger"].level, 50)
        with self.assertRaises(VoiceGatewayError):
            provider.attach("https://other.example/steal")
        self.assertEqual(connect.call_count, 1)

    def test_known_session_hangup_uses_same_origin_and_does_not_create(self):
        opener = Mock()
        opener.open.return_value = io.BytesIO(b"")
        provider = OpenAILiveProvider("synthetic-secret", opener=opener)
        provider.hangup("live_synthetic")
        self.assertEqual(opener.open.call_args.args[0].full_url,
                         "https://api.openai.com/v1/live/sessions/live_synthetic/hangup")
        self.assertEqual(opener.open.call_count, 1)


if __name__ == "__main__":
    unittest.main()
