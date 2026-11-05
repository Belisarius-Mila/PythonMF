"""One price-approved synthetic GPT-Live test; no microphone or application data.

Uses a primary WebSocket to avoid starting a server or asking a browser for audio
permission. This proves neither WebRTC/sideband compatibility nor iPhone quality.
Every paid start is preceded by a durable reservation; no retries are performed.
"""

from __future__ import annotations

import array
import base64
import hashlib
import json
import math
import os
import re
import sys
import threading
import time
import wave
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

from app.communication.voice_conversation_gateway import (
    CandidateVoiceGrant, OpenAILiveProvider, VoiceAttemptJournal, VoiceGatewayError,
)
from app.communication.voice_conversation_pilot import VOICE_RATE_USD_PER_MINUTE
from app.file_persistence import atomic_create_text


GREETING = "Promluv nyní česky. Řekni jen: Hlasový pilot Samanthy funguje. Potom se odmlč a poslouchej."
_SILENCE = base64.b64encode(b"\0" * 4800).decode("ascii")  # 100 ms, mono PCM16LE, 24 kHz.
_ID = re.compile(r"[A-Za-z0-9_.:-]{1,160}\Z")


def probe_session(model):
    return {"model": model, "store": False,
            "instructions": "Jsi AI hlas v jednorázové syntetické technické zkoušce. Mluv česky. Nic neprováděj ani nevyžaduj nástroje.",
            "audio": {"format": {"type": "audio/pcm", "rate": 24000}, "output": {"voice": "marin"}},
            "delegation": {"type": "client"},
            "input": [{"role": "developer", "content": [{"type": "input_text", "text": GREETING}]}]}


def _voice_key():
    endpoint = os.environ.get("OPENAI_BASE_URL", "")
    if endpoint and (urlparse(endpoint).hostname != "api.openai.com" or urlparse(endpoint).scheme != "https"):
        raise VoiceGatewayError("Configured credential endpoint differs; no key was sent")
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise VoiceGatewayError("No project credential in this process; no model attempt was made")
    return key


def run_voice_candidate_probe(*, grant: CandidateVoiceGrant, directory: Path,
                              provider=None, clock=time.monotonic, wall_clock=time.time,
                              timer_factory=threading.Timer, authorization_directory: Path | None = None):
    """One confirmed synthetic start. Results/artifacts stay in explicit private storage.

    Default provider reads the existing process credential only after validating
    the explicit paid grant. No dotenv, SDK update, service or production role.
    """
    grant.validate()
    if grant.binding.workstream_id != "synthetic-voice-probe" or grant.binding.thread_id != "synthetic-thread":
        raise VoiceGatewayError("The live probe accepts synthetic bindings only")
    if (directory / "proof.json").exists() or (directory / "synthetic-output.wav").exists():
        raise VoiceGatewayError("Probe artifacts already exist; inspect the original attempt")
    authority = authorization_directory or directory
    if not authority.is_absolute() or authority.is_symlink():
        raise VoiceGatewayError("Explicit private authorization directory required")
    paid_start_path = authority / ("paid-start-" + hashlib.sha256(grant.request_id.encode()).hexdigest() + ".json")
    if paid_start_path.exists():
        raise VoiceGatewayError("This authorization already attempted a model start; do not repeat")
    previous_proof_digest = None
    if authority != directory:
        # A new transport connection is allowed ONLY when the original durable
        # proof establishes that session.start was never attempted. Model-start
        # uncertainty is never resolved by another model call.
        try:
            proof_path = authority / "proof.json"
            if proof_path.is_symlink() or proof_path.stat().st_size > 8192:
                raise ValueError()
            proof_bytes = proof_path.read_bytes()
            prior = json.loads(proof_bytes)
            receipt = VoiceAttemptJournal(authority).read(grant.request_id)
            if (prior["model"] != grant.model or prior["session_start_attempted"] is not False
                    or prior["session_started"] is not False or prior["output_audio_bytes"] != 0
                    or receipt["state"] != "creation_unknown" or receipt["session_id"] is not None
                    or receipt["owner_digest"] != hashlib.sha256(grant.owner.encode()).hexdigest()):
                raise ValueError()
            previous_proof_digest = hashlib.sha256(proof_bytes).hexdigest()
        except Exception:
            raise VoiceGatewayError("No conclusive pre-start proof; model attempt remains blocked") from None
    provider = provider if provider is not None else OpenAILiveProvider(_voice_key())
    journal = VoiceAttemptJournal(directory)
    journal.reserve(grant, wall_clock())
    began = clock()
    result = {"model": grant.model, "transport": "primary_websocket", "connection_attempts": 1,
              "session_start_attempted": False, "session_started": False, "session_closed": False,
              "final_usage_confirmed": False, "seconds": None, "voice_usd_estimate": None,
              "output_audio_bytes": 0, "non_silent_audio": False, "czech_marker_observed": False,
              "probe_pass": False, "failure": None, "http_status": None}
    if previous_proof_digest:
        result["pre_start_proof_sha256"] = previous_proof_digest
    connection = None
    identity = None
    transcript = ""
    audio = bytearray()
    last_audio = None
    first_audio = None
    close_sent = False
    close_at = began + max(1, grant.max_seconds - 10)  # Reserve finalization/cleanup time inside the window.
    finish_at = began + max(2, grant.max_seconds - 5)
    latest_usage = 0.0
    delegations = set()
    interrupted = threading.Event()

    def hard_stop():
        interrupted.set()
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass

    watchdog = timer_factory(grant.max_seconds, hard_stop)
    watchdog.daemon = True
    watchdog.start()
    try:
        connection = provider.primary(timeout=min(8, grant.max_seconds))
        if interrupted.is_set():
            raise VoiceGatewayError("Probe window expired before startup")
        authority.mkdir(mode=0o700, parents=True, exist_ok=True)
        atomic_create_text(paid_start_path, json.dumps({"model": grant.model,
            "request_digest": hashlib.sha256(grant.request_id.encode()).hexdigest(),
            "state": "model_start_attempt_reserved", "at": wall_clock()}) + "\n", mode=0o600)
        result["session_start_attempted"] = True  # Mark before send; a failed write can be ambiguous.
        connection.send({"type": "session.start", "event_id": "synthetic-probe-start",
                         "session": probe_session(grant.model)})
        next_silence = clock()
        while not interrupted.is_set() and clock() < finish_at:
            now = clock()
            if not result["session_started"] and now - began > 10:
                raise VoiceGatewayError("Session startup was not confirmed")
            if result["session_started"] and not close_sent:
                # Silence keeps model input active. No real microphone is accessed.
                if now >= next_silence:
                    connection.send({"type": "session.input_audio.append", "audio": _SILENCE})
                    next_silence = now + 0.1
                quiet_after_output = last_audio is not None and now - began >= 10 and now - last_audio >= 1.5
                if now >= close_at or quiet_after_output or len(audio) >= 2_880_000:
                    close_sent = True
                    connection.send({"type": "session.close", "event_id": "synthetic-probe-close"})
                    journal.record(grant.request_id, state="closing")
            try:
                event = connection.recv(timeout=0.05)
            except TimeoutError:
                continue
            if not isinstance(event, dict):
                raise VoiceGatewayError("Invalid event")
            kind = event.get("type")
            if kind == "session.started":
                session = event.get("session")
                candidate_id = session.get("id") if isinstance(session, dict) else None
                if not isinstance(candidate_id, str) or not _ID.fullmatch(candidate_id):
                    raise VoiceGatewayError("Invalid session identity")
                if identity is not None and candidate_id != identity:
                    raise VoiceGatewayError("Voice identity changed")
                if session.get("model", grant.model) != grant.model:
                    raise VoiceGatewayError("Unexpected resolved voice model")
                identity = candidate_id
                if not result["session_started"]:
                    result["session_started"] = True
                    journal.record(grant.request_id, state="active", session_id=identity)
                    connection.send({"type": "session.input_audio.append", "audio": _SILENCE})
                    connection.send({"type": "session.commentary.append", "event_id": "synthetic-probe-greeting",
                                     "delegation_id": None, "content": GREETING})
            elif kind == "session.output_audio.delta":
                value = event.get("delta")
                if not isinstance(value, str) or len(value) > 262144:
                    raise VoiceGatewayError("Invalid audio frame")
                chunk = base64.b64decode(value, validate=True)
                if len(chunk) % 2 or len(audio) + len(chunk) > 3_000_000:
                    raise VoiceGatewayError("Audio bounds exceeded")
                audio.extend(chunk)
                last_audio = clock()
                if first_audio is None:
                    first_audio = clock() - began
            elif kind == "session.output_transcript.delta":
                delta = event.get("delta")
                if not isinstance(delta, str) or len(delta) > 4096:
                    raise VoiceGatewayError("Invalid transcript")
                transcript = (transcript + delta)[-12000:]
            elif kind in {"session.usage.updated", "session.closed"}:
                usage = event.get("usage")
                seconds = usage.get("seconds") if isinstance(usage, dict) else None
                valid = type(seconds) in {int, float} and math.isfinite(seconds) and seconds >= latest_usage
                if valid:
                    latest_usage = float(seconds)
                if kind == "session.closed":
                    result.update(session_closed=True, final_usage_confirmed=valid,
                                  seconds=latest_usage if valid else None)
                    if not valid:
                        result["failure"] = "final_usage_unconfirmed"
                    journal.record(grant.request_id, state="closed", seconds=latest_usage,
                                   final_usage_confirmed=valid)
                    break
            elif kind == "session.delegation.created":
                delegation = event.get("delegation", {})
                identifier = delegation.get("id") if isinstance(delegation, dict) else None
                if not isinstance(identifier, str) or not _ID.fullmatch(identifier):
                    raise VoiceGatewayError("Invalid delegation identity")
                if identifier in delegations:
                    continue
                if len(delegations) >= 32:
                    raise VoiceGatewayError("Delegation budget exceeded")
                delegations.add(identifier)
                # Fixed synthetic context, no model/agent/tool backend and no private data.
                connection.send({"type": "session.commentary.append", "event_id": "synthetic-no-tools-" + str(len(delegations)),
                                 "delegation_id": identifier, "content": "Toto je pouze syntetická hlasová zkouška. Žádná další úloha ani nástroj se nespouští."})
            elif kind == "error":
                error = event.get("error", {})
                code = error.get("code") if isinstance(error, dict) else None
                result["failure"] = code if isinstance(code, str) and re.fullmatch(r"[a-zA-Z0-9_]{1,64}", code) else "provider_error"
                raise VoiceGatewayError("Provider rejected the synthetic probe")
        if not result["session_closed"]:
            raise VoiceGatewayError("Final session usage was not confirmed")
    except Exception as exc:
        result["failure"] = result["failure"] or "connection_or_finalization_unconfirmed"
        result["failure_type"] = type(exc).__name__[:64]
        response = getattr(exc, "response", None)
        status = getattr(response, "status_code", None)
        if type(status) is int and 100 <= status <= 599:
            result["http_status"] = status
    finally:
        watchdog.cancel()
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass
        if not result["session_closed"]:
            if identity is not None:
                try:
                    provider.hangup(identity, timeout=3)
                except Exception:
                    pass
            journal.record(grant.request_id, state="finalization_unknown" if identity else "creation_unknown",
                           seconds=latest_usage, final_usage_confirmed=False)
    result["elapsed_seconds"] = round(clock() - began, 3)
    result["first_audio_seconds"] = round(first_audio, 3) if first_audio is not None else None
    result["output_audio_bytes"] = len(audio)
    result["czech_marker_observed"] = "hlas" in transcript.casefold() and "pilot" in transcript.casefold()
    samples = array.array("h", audio)
    if sys.byteorder != "little":
        samples.byteswap()
    result["non_silent_audio"] = any(abs(value) > 100 for value in samples)
    result["probe_pass"] = bool(result["session_started"] and result["session_closed"]
                                 and result["final_usage_confirmed"] and result["non_silent_audio"]
                                 and result["czech_marker_observed"] and result["seconds"] is not None
                                 and result["seconds"] > 0)
    if not result["probe_pass"] and result["failure"] is None:
        result["failure"] = "speech_or_czech_marker_unconfirmed"
    if result["seconds"] is not None:
        cost = Decimal(str(result["seconds"])) / 60 * VOICE_RATE_USD_PER_MINUTE
        result["voice_usd_estimate"] = str(cost.quantize(Decimal("0.000001")))
    if audio:
        sample_path = directory / "synthetic-output.wav"
        with sample_path.open("xb") as handle:
            sample_path.chmod(0o600)
            with wave.open(handle, "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(24000)
                output.writeframes(bytes(audio))
        result["audio_sha256"] = hashlib.sha256(sample_path.read_bytes()).hexdigest()
    # No transcript, credentials, session identity, remote error message or audio in the public summary.
    atomic_create_text(directory / "proof.json", json.dumps(result, indent=2) + "\n", mode=0o600)
    return result
