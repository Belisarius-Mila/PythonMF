"""15/P2-A: inert GPT-Live protocol pilot above the existing session snapshot.

No network client, API key, runtime, file persistence or write capability is
constructed here. A future trusted gateway must authenticate the caller, bind
the workstream/thread, approve a central voice role and supervise cost/expiry.
This module is deliberately not registered in Cockpit or model tools.
"""

from __future__ import annotations

import math
import re
import threading
import time
import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable


class VoicePilotError(ValueError):
    """Safe public error; never include raw provider or backend content."""


@dataclass(frozen=True)
class VoiceBinding:
    workstream_id: str
    thread_id: str

    def __post_init__(self):
        if not all(isinstance(value, str) and 0 < len(value) <= 160
                   and re.fullmatch(r"[A-Za-z0-9_.:-]+", value)
                   for value in (self.workstream_id, self.thread_id)):
            raise VoicePilotError("Explicit server-owned workstream and thread required")


VOICE_RATE_USD_PER_MINUTE = Decimal("0.05")  # Official pricing checked 2026-11-05; not a billing limit.
VOICE_INSTRUCTIONS = (
    "Jsi hlasové rozhraní Samanthy. Mluv stručně a přirozeně česky. "
    "Jsi AI hlas, nikoli člověk. Tento pilot umí pouze číst stav existující práce. "
    "Pro aktuální stav požádej backend. Žádné soubory, e-maily ani kalendář neměníš. "
    "Hlasové ano ani doplnění detailu není schválením akce. "
    "Změny a nové úkoly odkaž do běžného Human–Adam. "
    "Neříkej, že je práce dokončená nebo zrušená, pokud to backend nepotvrdil. "
    "Přerušení tvé řeči ani ukončení hlasu neukončuje práci backendu."
)


def session_request(*, approved_model: str, sdp: str) -> dict[str, Any]:
    """Build only. The caller owns central role approval and ONE HTTP attempt.

    Never select a model, create a session or load a credential implicitly.
    A model string here is not proof of account entitlement or activation.
    """
    if not isinstance(approved_model, str) or not re.fullmatch(r"[a-zA-Z0-9_.:-]{1,96}", approved_model):
        raise VoicePilotError("Explicit approved voice model required")
    if not isinstance(sdp, str) or not sdp.startswith("v=0") or len(sdp.encode()) > 60_000:
        raise VoicePilotError("Valid bounded SDP offer required")
    return {
        "session": {
            "model": approved_model, "store": False, "instructions": VOICE_INSTRUCTIONS,
            "delegation": {"type": "client"},
            # The browser cannot reconfigure delegation, add tools or impersonate
            # trusted backend results. Appends require the future server sideband.
            "client": {"data_channel": {
                "allowed_client_events": ["session.close"],
                "allowed_server_events": [{"type": kind} for kind in (
                    "session.started", "session.closed", "session.usage.updated",
                    "session.input_transcript.delta", "session.output_transcript.delta", "error",
                )],
            }},
        },
        "transport": {"type": "webrtc", "sdp": sdp},
    }


def status_summary(snapshot: dict[str, Any], binding: VoiceBinding) -> str:
    """Allowlisted facts only. Never forward chat text, paths or instructions."""
    session = snapshot.get("session")
    if not isinstance(session, dict) or session.get("thread_id") != binding.thread_id:
        raise VoicePilotError("Bound thread changed; reconnect through the application")
    # Workstream is fixed by the gateway closure, not a voice event. Check it if
    # the existing source includes it; older snapshots have no workstream field.
    if snapshot.get("workstream_id", binding.workstream_id) != binding.workstream_id:
        raise VoicePilotError("Bound workstream changed")
    if session.get("turn_busy") or session.get("active_turn"):
        return "Adam právě pracuje. Hlasové spojení můžeš ukončit; úloha pokračuje samostatně."
    messages = session.get("messages")
    matching = ([item for item in messages if isinstance(item, dict)
                 and item.get("thread_id", binding.thread_id) == binding.thread_id]
                if isinstance(messages, list) else [])
    latest = matching[-1] if matching else None
    if isinstance(latest, dict):
        state = latest.get("status")
        if state in {"delivery_unknown", "pending"}:
            return "Výsledek posledního dotazu zatím není potvrzený. Dotaz neopakuj; ověř stav v Human–Adam."
        if state == "completed" and latest.get("delivery_confirmed") is True:
            return "Poslední odpověď je potvrzená jako dokončená. Podrobnosti jsou v Human–Adam."
        if state in {"failed", "interrupted"}:
            return "Poslední tah neskončil úspěšně. Podrobnosti a další postup ověř v Human–Adam."
    return "Není potvrzená dokončená odpověď. Aktuální podrobnosti ověř v Human–Adam."


class ReadOnlyVoicePilot:
    """One voice session, bounded memory, read-only dependency and no retries.

    `read_snapshot` must be bound by trusted application code to the selected
    workstream (e.g. an already-owned CanonicalSessionHub.snapshot adapter).
    Do not construct HumanAdamService here: cold construction/recovery can write.
    The injected callable is the ONLY backend dependency. Disconnect never calls
    it, cancels a task, creates a thread, steers or starts a model turn.
    """

    def __init__(self, *, binding: VoiceBinding, read_snapshot: Callable[[], dict[str, Any]],
                 voice_session_id: str, max_seconds: int = 300,
                 clock: Callable[[], float] = time.monotonic):
        if (not isinstance(voice_session_id, str) or not voice_session_id
                or len(voice_session_id) > 160 or type(max_seconds) is not int or not 15 <= max_seconds <= 600):
            raise VoicePilotError("Session identity and 15–600 second pilot window required")
        self.binding, self.read_snapshot = binding, read_snapshot
        self.voice_session_id, self.max_seconds = voice_session_id, max_seconds
        self.clock, self.created_at = clock, clock()
        self.state = "connecting"
        self.transcripts = {"input": "", "output": ""}  # In-memory only; not consent or a tool request.
        self.usage_seconds = 0.0
        self.usage_confirmed = False
        self.close_reason = ""
        self.first_transcript_latency_ms = None
        self.delegations: dict[str, str] = {}
        self.seen_events: set[str] = set()
        self._lock = threading.RLock()

    def _close_event(self):
        return {"type": "session.close", "event_id": "voice-close-" + uuid.uuid4().hex}

    def close(self) -> list[dict[str, Any]]:
        with self._lock:
            if self.state in {"closing", "closed", "disconnected"}:
                return []
            self.state = "closing"
            return [self._close_event()]

    def disconnected(self):
        with self._lock:
            if self.state != "closed":
                self.state = "disconnected"
                self.usage_confirmed = False
            # No automatic session recreation, result replay or backend cancellation.

    def tick(self) -> list[dict[str, Any]]:
        """Future trusted server watchdog calls this; a browser timer is insufficient."""
        return self.close() if self.clock() - self.created_at >= self.max_seconds else []

    def cost(self) -> dict[str, Any]:
        voice = Decimal(str(self.usage_seconds)) / 60 * VOICE_RATE_USD_PER_MINUTE
        return {"seconds": self.usage_seconds, "voice_usd": str(voice.quantize(Decimal("0.000001"))),
                "final_usage_confirmed": self.usage_confirmed, "backend_cost": "not_included"}

    def handle(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        with self._lock:
            if not isinstance(event, dict):
                raise VoicePilotError("Invalid event")
            kind = event.get("type")
            if self.state == "closed" or self.state == "disconnected":
                return []  # Late events from an old connection never revive it.
            event_id = event.get("event_id")
            if not isinstance(event_id, str) or not 0 < len(event_id) <= 200:
                raise VoicePilotError("Bounded event ID required")
            if event_id in self.seen_events:
                return []
            if len(self.seen_events) >= 4096 and kind not in {"session.usage.updated", "session.closed"}:
                return self.close()
            if len(self.seen_events) < 4096:
                self.seen_events.add(event_id)
            if kind == "session.started":
                session = event.get("session")
                if not isinstance(session, dict) or session.get("id") != self.voice_session_id:
                    return self.close()
                if self.state == "connecting":
                    self.state = "active"
            elif kind in {"session.usage.updated", "session.closed"}:
                usage = event.get("usage")
                seconds = usage.get("seconds") if isinstance(usage, dict) else None
                valid = type(seconds) in {float, int} and math.isfinite(seconds) and seconds >= self.usage_seconds
                if valid:
                    self.usage_seconds = float(seconds)  # Cumulative, never add successive updates.
                if kind == "session.closed":
                    self.state = "closed"
                    self.usage_confirmed = valid
                    self.close_reason = str(event.get("reason", "unknown"))[:64]
            elif self.state != "active":
                return []
            elif kind in {"session.input_transcript.delta", "session.output_transcript.delta"}:
                side = "input" if kind == "session.input_transcript.delta" else "output"
                delta = event.get("delta")
                if not isinstance(delta, str) or len(delta) > 4096:
                    return self.close()
                self.transcripts[side] = (self.transcripts[side] + delta)[-12000:]
                if side == "output" and self.first_transcript_latency_ms is None:
                    self.first_transcript_latency_ms = round((self.clock() - self.created_at) * 1000)
            elif kind == "session.delegation.created":
                delegation = event.get("delegation")
                if not isinstance(delegation, dict) or delegation.get("target") != "client":
                    return self.close()
                identity = delegation.get("id")
                if not isinstance(identity, str) or not 0 < len(identity) <= 160:
                    return self.close()
                if identity in self.delegations:
                    return []
                if len(self.delegations) >= 32:
                    return self.close()
                self.delegations[identity] = "pending"  # Reserve before reading the backend.
                try:
                    content = status_summary(self.read_snapshot(), self.binding)
                except Exception:
                    self.delegations[identity] = "unconfirmed"
                    content = "Stav backendu se nepodařilo bezpečně ověřit. Nic nebylo spuštěno ani potvrzeno."
                else:
                    self.delegations[identity] = "read_completed"
                return [{"type": "session.commentary.append", "event_id": "voice-result-" + uuid.uuid4().hex,
                         "delegation_id": identity, "content": content}]
            elif kind == "error":
                return self.close()  # No raw error text, fallback model or retry.
            return []
