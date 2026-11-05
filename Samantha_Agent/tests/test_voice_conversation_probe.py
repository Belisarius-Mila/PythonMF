"""Offline tests for the one-shot live probe; no real API/key/microphone access."""

from __future__ import annotations

import base64
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.communication.voice_conversation_gateway import CandidateVoiceGrant, VoiceAttemptJournal, VoiceGatewayError
from app.communication.voice_conversation_pilot import VoiceBinding
from app.communication.voice_conversation_probe import run_voice_candidate_probe, _voice_key


class Clock:
    now = 0.0

    def __call__(self):
        return self.now


class Timer:
    def __init__(self, duration, callback):
        self.duration, self.callback = duration, callback
        self.cancelled = False

    def start(self):
        pass

    def cancel(self):
        self.cancelled = True


class Connection:
    def __init__(self, clock):
        self.clock, self.sent, self.events = clock, [], []
        self.audio = base64.b64encode(b"\xe8\x03" * 2400).decode()
        self.started = {"id": "live_synthetic", "model": "gpt-live-1"}
        self.usage = 12.0
        self.finalize = True
        self.emit_audio = True
        self.emit_text = True
        self.fail_recv = False
        self.closed = False

    def send(self, event):
        self.sent.append(event)
        if event["type"] == "session.start":
            self.events.append({"type": "session.started", "event_id": "started", "session": self.started})
        if event.get("event_id") == "synthetic-probe-greeting":
            if self.emit_audio:
                self.events.append({"type": "session.output_audio.delta", "delta": self.audio})
            if self.emit_text:
                self.events.append({"type": "session.output_transcript.delta", "delta": "Hlasový pilot Samanthy funguje."})
        if event["type"] == "session.close" and self.finalize:
            self.events.append({"type": "session.closed", "event_id": "closed", "usage": {"seconds": self.usage}})

    def recv(self, *, timeout):
        if self.fail_recv:
            raise OSError("SYNTHETIC SECRET")
        if self.events:
            return self.events.pop(0)
        self.clock.now += timeout
        raise TimeoutError()

    def close(self):
        self.closed = True


class Provider:
    def __init__(self, connection):
        self.connection = connection
        self.primary_calls = 0
        self.hangups = []
        self.failure = None

    def primary(self, **_kwargs):
        self.primary_calls += 1
        if self.failure:
            raise self.failure
        return self.connection

    def hangup(self, identity, **_kwargs):
        self.hangups.append(identity)


class ProbeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.directory = Path(temp.name) / "own-probe"
        self.clock = Clock()
        self.connection = Connection(self.clock)
        self.provider = Provider(self.connection)
        self.grant = CandidateVoiceGrant("synthetic-one-approved-probe", "synthetic-owner", "gpt-live-1",
            VoiceBinding("synthetic-voice-probe", "synthetic-thread"), confirmed_live_test=True)
        self.timers = []

    def timer(self, seconds, callback):
        timer = Timer(seconds, callback)
        self.timers.append(timer)
        return timer

    def run_probe(self, grant=None, directory=None, authority=None):
        return run_voice_candidate_probe(grant=grant or self.grant, directory=directory or self.directory,
            provider=self.provider, clock=self.clock, wall_clock=self.clock, timer_factory=self.timer,
            authorization_directory=authority)

    def test_approval_and_synthetic_binding_required_before_reservation(self):
        for grant in [replace(self.grant, confirmed_live_test=False),
                      replace(self.grant, binding=VoiceBinding("private-project", "private-thread"))]:
            with self.subTest(grant=grant), self.assertRaises(VoiceGatewayError):
                self.run_probe(grant)
        self.assertFalse(self.directory.exists())
        self.assertEqual(self.provider.primary_calls, 0)

    def test_one_start_fixed_input_voice_output_and_final_usage(self):
        result = self.run_probe()
        self.assertTrue(result["probe_pass"])
        self.assertEqual(result["seconds"], 12)
        self.assertEqual(result["voice_usd_estimate"], "0.010000")
        self.assertEqual(result["output_audio_bytes"], 4800)
        self.assertEqual(self.provider.primary_calls, 1)
        starts = [e for e in self.connection.sent if e["type"] == "session.start"]
        self.assertEqual(len(starts), 1)
        self.assertEqual(self.connection.sent[0]["type"], "session.start")
        self.assertEqual(starts[0]["session"]["delegation"], {"type": "client"})
        self.assertNotIn("tools", starts[0]["session"])
        self.assertNotIn("client", starts[0]["session"])
        self.assertEqual(starts[0]["session"]["audio"]["format"], {"type": "audio/pcm", "rate": 24000})
        self.assertIs(starts[0]["session"]["store"], False)
        self.assertTrue(self.connection.closed)
        self.assertTrue(self.timers[0].cancelled)
        self.assertEqual(self.timers[0].duration, 60)
        self.assertEqual((self.directory / "synthetic-output.wav").read_bytes()[:4], b"RIFF")
        self.assertEqual((self.directory / "proof.json").stat().st_mode & 0o777, 0o600)

    def test_repeated_call_never_creates_another_session(self):
        self.run_probe()
        with self.assertRaises(VoiceGatewayError):
            self.run_probe()
        self.assertEqual(self.provider.primary_calls, 1)

    def test_reservation_precedes_connection(self):
        original = self.provider.primary

        def inspect(**kwargs):
            receipt = VoiceAttemptJournal(self.directory).read(self.grant.request_id)
            self.assertEqual(receipt["state"], "creating")
            return original(**kwargs)

        self.provider.primary = inspect
        self.run_probe()

    def test_provider_rejection_is_safe_and_never_retried(self):
        class Rejected(Exception):
            response = SimpleNamespace(status_code=403)
        self.provider.failure = Rejected("SYNTHETIC SECRET")
        result = self.run_probe()
        self.assertFalse(result["session_start_attempted"])
        self.assertFalse(result["probe_pass"])
        self.assertEqual(result["http_status"], 403)
        self.assertNotIn("SECRET", json.dumps(result))
        with self.assertRaises(VoiceGatewayError):
            self.run_probe()
        self.assertEqual(self.provider.primary_calls, 1)
        self.assertFalse(result["final_usage_confirmed"])
        self.assertIsNone(result["voice_usd_estimate"])

    def test_no_audio_is_not_accepted_as_success(self):
        self.connection.emit_audio = False
        result = self.run_probe()
        self.assertFalse(result["probe_pass"])
        self.assertTrue(result["final_usage_confirmed"])
        self.assertFalse((self.directory / "synthetic-output.wav").exists())

    def test_zero_audio_and_missing_czech_marker_fail_acceptance(self):
        self.connection.audio = base64.b64encode(b"\0" * 4800).decode()
        self.connection.emit_text = False
        result = self.run_probe()
        self.assertFalse(result["probe_pass"])
        self.assertFalse(result["non_silent_audio"])
        self.assertFalse(result["czech_marker_observed"])

    def test_missing_final_event_retains_unknown_usage_and_hangs_up_known_session(self):
        self.connection.finalize = False
        result = self.run_probe()
        self.assertFalse(result["final_usage_confirmed"])
        self.assertIsNone(result["voice_usd_estimate"])
        self.assertEqual(self.provider.hangups, ["live_synthetic"])
        self.assertLess(result["elapsed_seconds"], 60)
        self.assertEqual(VoiceAttemptJournal(self.directory).read(self.grant.request_id)["state"], "finalization_unknown")

    def test_invalid_final_usage_is_not_a_price_receipt(self):
        self.connection.usage = float("nan")
        result = self.run_probe()
        self.assertFalse(result["final_usage_confirmed"])
        self.assertIsNone(result["voice_usd_estimate"])
        self.assertEqual(result["failure"], "final_usage_unconfirmed")

    def test_private_transcript_and_audio_are_not_in_summary(self):
        self.connection.events.append({"type": "session.output_transcript.delta", "delta": "SYNTHETIC PRIVATE"})
        result = self.run_probe()
        text = (self.directory / "proof.json").read_text()
        self.assertNotIn("PRIVATE", text)
        self.assertNotIn("session_id", text)
        self.assertNotIn(self.connection.audio, text)
        self.assertNotIn("transcript", result)

    def test_primary_transport_has_fixed_endpoint_and_no_automatic_retries(self):
        import ssl
        from app.communication.voice_conversation_gateway import OpenAILiveProvider
        connect = Mock()
        provider = OpenAILiveProvider("synthetic-secret", connect=connect)
        provider.primary()
        connect.assert_called_once()
        self.assertEqual(connect.call_args.args[0], "wss://api.openai.com/v1/live/sessions")
        self.assertGreaterEqual(connect.call_args.kwargs["logger"].level, 50)
        context = connect.call_args.kwargs["ssl"]
        self.assertIs(context.check_hostname, True)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertGreater(context.cert_store_stats()["x509_ca"], 0)

    def test_pre_start_connection_failure_does_not_consume_the_single_model_start(self):
        self.provider.failure = OSError("synthetic TLS pre-start failure")
        initial = self.run_probe()
        self.assertIs(initial["session_start_attempted"], False)
        self.provider.failure = None
        second_directory = self.directory.parent / "after-fixed-transport"
        result = self.run_probe(directory=second_directory, authority=self.directory)
        self.assertTrue(result["probe_pass"])
        self.assertIn("pre_start_proof_sha256", result)
        self.assertEqual(self.provider.primary_calls, 2)
        self.assertEqual(sum(x["type"] == "session.start" for x in self.connection.sent), 1)
        with self.assertRaises(VoiceGatewayError):
            self.run_probe(directory=self.directory.parent / "third", authority=self.directory)
        self.assertEqual(self.provider.primary_calls, 2)

    def test_ambiguous_model_start_is_never_repeated_through_another_directory(self):
        original = self.connection.send

        def ambiguous(event):
            original(event)
            if event["type"] == "session.start":
                raise OSError("synthetic write uncertainty")

        self.connection.send = ambiguous
        result = self.run_probe()
        self.assertTrue(result["session_start_attempted"])
        with self.assertRaises(VoiceGatewayError):
            self.run_probe(directory=self.directory.parent / "another", authority=self.directory)
        self.assertEqual(self.provider.primary_calls, 1)

    def test_no_prior_model_start_is_required_even_if_a_claim_file_is_missing(self):
        self.provider.failure = OSError()
        self.run_probe()
        proof_path = self.directory / "proof.json"
        proof = json.loads(proof_path.read_text())
        proof["session_start_attempted"] = True  # Corrupted evidence must fail closed.
        proof_path.write_text(json.dumps(proof))
        self.provider.failure = None
        with self.assertRaises(VoiceGatewayError):
            self.run_probe(directory=self.directory.parent / "another", authority=self.directory)
        self.assertEqual(self.provider.primary_calls, 1)

    def test_different_credential_endpoint_is_refused_before_key_use(self):
        with patch.dict("os.environ", {"OPENAI_BASE_URL": "https://synthetic-other.invalid/v1", "OPENAI_API_KEY": "synthetic-secret"}):
            with self.assertRaises(VoiceGatewayError):
                _voice_key()

    def test_probe_operation_has_explicit_confirmation_and_no_voice_approval(self):
        from app.capabilities import get_capability
        record = get_capability("probe_voice_candidate")
        self.assertTrue(record.requires_confirmation)
        self.assertEqual(record.voice_allowed, "blocked")


if __name__ == "__main__":
    unittest.main()
