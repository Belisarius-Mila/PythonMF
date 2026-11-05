"""15/P2-B candidate broker. Inert until constructed by trusted application code.

No routes, services, role edits, credentials or model calls on import. A candidate
grant authorizes ONE synthetic session, not a production model role. The HTTP
adapter requires a server-authenticated principal, exact Origin and a CSRF token.
Only a bound read-only snapshot reaches the voice model. Receipts never contain
audio, SDP, transcripts, credentials or backend text.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import queue
import re
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.file_persistence import atomic_create_text, update_json_file
from app.communication.voice_conversation_pilot import (
    ReadOnlyVoicePilot, VoiceBinding, VoicePilotError, session_request, status_summary,
)


_ID = re.compile(r"[A-Za-z0-9_.:-]{1,160}\Z")
_REFLECTED_AUDIO = frozenset({"session.input_audio.append", "session.output_audio.delta"})
_TERMINAL = frozenset({"closed", "creation_unknown", "finalization_unknown"})


class VoiceGatewayError(RuntimeError):
    pass


@dataclass(frozen=True)
class CandidateVoiceGrant:
    request_id: str
    owner: str
    model: str
    binding: VoiceBinding
    max_seconds: int = 60
    confirmed_live_test: bool = False

    def validate(self):
        # Candidate choice and a paid test are separate decisions. No default
        # role resolution, account upgrade or fallback is performed here.
        if (self.confirmed_live_test is not True or self.model != "gpt-live-1"
                or not all(isinstance(x, str) and _ID.fullmatch(x) for x in (self.request_id, self.owner))
                or not isinstance(self.binding, VoiceBinding)
                or type(self.max_seconds) is not int or not 15 <= self.max_seconds <= 60):
            raise VoiceGatewayError("One explicit price-reviewed candidate test grant is required")


class VoiceAttemptJournal:
    """Create-only reservation survives restart; every repeated ID is blocked."""

    def __init__(self, directory: Path):
        if not directory.is_absolute() or directory.is_symlink():
            raise VoiceGatewayError("Explicit private journal directory required")
        self.directory = directory

    def path(self, request_id: str) -> Path:
        return self.directory / (hashlib.sha256(request_id.encode()).hexdigest() + ".json")

    def reserve(self, grant: CandidateVoiceGrant, now: float):
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.directory.chmod(0o700)
        value = {"schema": 1, "state": "creating", "model": grant.model,
                 "owner_digest": hashlib.sha256(grant.owner.encode()).hexdigest(),
                 "created_at": now, "deadline_at": now + grant.max_seconds,
                 "session_id": None, "seconds": 0.0, "final_usage_confirmed": False}
        try:
            atomic_create_text(self.path(grant.request_id), json.dumps(value) + "\n", mode=0o600)
        except Exception:
            raise VoiceGatewayError("Already attempted or journal unavailable; do not recreate the session") from None

    def record(self, request_id: str, *, state: str, session_id: str | None = None,
               seconds: float | None = None, final_usage_confirmed: bool | None = None):
        if state not in _TERMINAL | {"created", "active", "closing"}:
            raise VoiceGatewayError("Invalid receipt state")

        def update(old):
            if not isinstance(old, dict) or old.get("schema") != 1:
                raise VoiceGatewayError("Receipt is unavailable; no recovery action attempted")
            if old.get("state") in _TERMINAL:
                return old  # A late close request cannot overwrite terminal evidence.
            result = {**old, "state": state}
            if session_id is not None:
                result["session_id"] = session_id
            if seconds is not None:
                result["seconds"] = seconds
            if final_usage_confirmed is not None:
                result["final_usage_confirmed"] = final_usage_confirmed
            return result

        update_json_file(self.path(request_id), update, default=None)
        self.path(request_id).chmod(0o600)

    def read(self, request_id: str) -> dict[str, Any]:
        path = self.path(request_id)
        if path.is_symlink() or path.stat().st_size > 8192:
            raise VoiceGatewayError("Invalid receipt")
        result = json.loads(path.read_text())
        if not isinstance(result, dict) or result.get("schema") != 1:
            raise VoiceGatewayError("Invalid receipt")
        return result


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None  # Never forward a project credential to a redirect target.


class OpenAILiveProvider:
    """Fixed-origin transport, one request per method, no SDK dependency/retry."""

    def __init__(self, api_key: str, *, opener=None, connect=None):
        if not isinstance(api_key, str) or not api_key or any(c.isspace() for c in api_key):
            raise VoiceGatewayError("Project credential is unavailable")
        self._key = api_key
        # Match the existing OpenAI/httpx trust source. Some macOS framework
        # Pythons have an empty system CA store; never disable verification.
        import certifi
        self._ssl = ssl.create_default_context(cafile=certifi.where())
        self._opener = opener or urllib.request.build_opener(
            _NoRedirect(), urllib.request.HTTPSHandler(context=self._ssl))
        self._connect = connect

    def _post(self, path: str, payload: dict[str, Any] | None, *, timeout: float):
        data = json.dumps(payload).encode() if payload is not None else b""
        request = urllib.request.Request("https://api.openai.com/v1/live/sessions" + path,
                                         data=data, method="POST",
                                         headers={"Authorization": "Bearer " + self._key,
                                                  "Content-Type": "application/json"})
        try:
            with self._opener.open(request, timeout=timeout) as response:
                body = response.read(128_001)
                if len(body) > 128_000:
                    raise VoiceGatewayError("Provider response exceeded the limit")
                return json.loads(body) if body else None
        except urllib.error.HTTPError as exc:
            exc.close()
            raise VoiceGatewayError("Voice provider request was not confirmed; do not repeat creation") from None
        except Exception:
            raise VoiceGatewayError("Voice provider request was not confirmed; do not repeat creation") from None

    def create(self, payload, *, timeout=8):
        return self._post("", payload, timeout=timeout)

    def primary(self, *, timeout=8):
        """One primary WebSocket connection; session.start is caller-owned."""
        connect = self._connect
        if connect is None:
            from websockets.sync.client import connect
        raw = connect("wss://api.openai.com/v1/live/sessions",
                      ssl=self._ssl,
                      additional_headers={"Authorization": "Bearer " + self._key},
                      open_timeout=timeout, close_timeout=1, max_size=262144,
                      logger=logging.Logger("samantha.voice.probe", level=logging.CRITICAL))
        return _Sideband(raw)

    def attach(self, session_id, *, timeout=5):
        if not isinstance(session_id, str) or not _ID.fullmatch(session_id):
            raise VoiceGatewayError("Invalid voice session identity")
        connect = self._connect
        if connect is None:
            from websockets.sync.client import connect
        raw = connect("wss://api.openai.com/v1/live/sessions/" + urllib.parse.quote(session_id, safe="") + "/attach",
                      ssl=self._ssl,
                      additional_headers={"Authorization": "Bearer " + self._key},
                      open_timeout=timeout, close_timeout=1, max_size=262144,
                      logger=logging.Logger("samantha.voice.transport", level=logging.CRITICAL))
        return _Sideband(raw)

    def hangup(self, session_id, *, timeout=3):
        if not isinstance(session_id, str) or not _ID.fullmatch(session_id):
            raise VoiceGatewayError("Invalid voice session identity")
        # Cleanup of a KNOWN session, never another session creation. A successful
        # hangup alone is not final usage evidence; session.closed is still needed.
        self._post("/" + urllib.parse.quote(session_id, safe="") + "/hangup", None, timeout=timeout)


class _Sideband:
    def __init__(self, raw):
        self.raw = raw

    def recv(self, *, timeout):
        message = self.raw.recv(timeout=timeout)
        if not isinstance(message, str) or len(message) > 262144:
            raise VoiceGatewayError("Invalid voice event")
        return json.loads(message)

    def send(self, event):
        self.raw.send(json.dumps(event))

    def close(self):
        self.raw.close()


class _BoundedSnapshot:
    """A slow read cannot block voice expiry or spawn an unbounded thread pool."""

    def __init__(self, reader, timeout=0.25):
        self.reader, self.timeout = reader, timeout
        self.worker = None
        self.lock = threading.Lock()

    def __call__(self):
        result = queue.Queue(maxsize=1)

        def read():
            try:
                result.put((True, self.reader()))
            except Exception:
                result.put((False, None))

        with self.lock:
            if self.worker is not None and self.worker.is_alive():
                raise VoiceGatewayError("Previous snapshot read is unfinished")
            self.worker = threading.Thread(target=read, daemon=True, name="voice-snapshot-read")
            self.worker.start()
        try:
            ok, value = result.get(timeout=self.timeout)
        except queue.Empty:
            raise VoiceGatewayError("Snapshot read exceeded its deadline") from None
        if not ok:
            raise VoiceGatewayError("Snapshot read was not confirmed")
        return value


class VoiceSessionSupervisor:
    """Server-owned deadline and sideband receiver; never cancels backend work."""

    def __init__(self, *, provider, sideband, pilot: ReadOnlyVoicePilot,
                 journal: VoiceAttemptJournal, request_id: str, remaining_seconds: float,
                 monotonic=time.monotonic, close_grace: float = 5):
        self.provider, self.sideband, self.pilot = provider, sideband, pilot
        self.journal, self.request_id = journal, request_id
        self.monotonic, self.deadline = monotonic, monotonic() + max(0, remaining_seconds)
        self.close_grace = close_grace
        self.stop_requested = threading.Event()
        self.done = threading.Event()
        self._hangup_attempted = False
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self.run, name="voice-candidate-watchdog", daemon=True)
        self.thread.start()

    def request_close(self):
        self.stop_requested.set()  # Safe even while a backend snapshot is being read.

    def _hangup_once(self):
        if not self._hangup_attempted:
            self._hangup_attempted = True
            try:
                self.provider.hangup(self.pilot.voice_session_id)
            except Exception:
                pass  # No new creation, no false final-usage confirmation.

    def run(self):
        close_deadline = None
        try:
            while not self.done.is_set():
                now = self.monotonic()
                if close_deadline is None and (self.stop_requested.is_set() or now >= self.deadline):
                    for command in self.pilot.close():
                        self.sideband.send(command)
                    self.journal.record(self.request_id, state="closing")
                    close_deadline = now + self.close_grace
                if close_deadline is not None and now >= close_deadline:
                    raise VoiceGatewayError("Final voice usage was not confirmed")
                try:
                    event = self.sideband.recv(timeout=0.2)
                except TimeoutError:
                    continue
                if not isinstance(event, dict):
                    raise VoiceGatewayError("Invalid event")
                if event.get("type") in _REFLECTED_AUDIO:
                    continue  # Audio copies have no event_id. Never persist or send to the backend.
                if event.get("type") == "session.closed":
                    self.pilot.handle(event)
                    self.journal.record(self.request_id, state="closed",
                                        seconds=self.pilot.usage_seconds,
                                        final_usage_confirmed=self.pilot.usage_confirmed)
                    break
                for command in self.pilot.handle(event):
                    self.sideband.send(command)
                    if command.get("type") == "session.close" and close_deadline is None:
                        close_deadline = self.monotonic() + self.close_grace
                        self.journal.record(self.request_id, state="closing")
                if event.get("type") == "session.usage.updated":
                    self.journal.record(self.request_id, state="closing" if close_deadline is not None else "active",
                                        seconds=self.pilot.usage_seconds, final_usage_confirmed=False)
        except Exception:
            self.pilot.disconnected()
            self._hangup_once()
            try:
                self.journal.record(self.request_id, state="finalization_unknown",
                                    seconds=self.pilot.usage_seconds, final_usage_confirmed=False)
            except Exception:
                pass  # Existing durable reservation still blocks a second creation.
        finally:
            try:
                self.sideband.close()
            except Exception:
                pass  # Never emit raw transport exceptions from a background thread.
            finally:
                self.done.set()


class CandidateVoiceGateway:
    """A trusted HTTP host must supply the authenticated principal separately.

    No request can choose the model, grant, workstream, thread or backend method.
    This does not activate a production role or mount an HTTP route by itself.
    """

    def __init__(self, *, grant: CandidateVoiceGrant, provider, journal: VoiceAttemptJournal,
                 read_snapshot: Callable[[], dict[str, Any]], origin: str, csrf_token: str,
                 wall_clock=time.time, monotonic=time.monotonic, supervisor_factory=VoiceSessionSupervisor):
        parsed = urllib.parse.urlparse(origin)
        if (parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.path
                or parsed.query or parsed.fragment or parsed.username or parsed.password
                or (parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1"})
                or not isinstance(csrf_token, str) or len(csrf_token) < 24):
            raise VoiceGatewayError("Exact HTTPS/localhost origin and private CSRF token required")
        self.grant, self.provider, self.journal = grant, provider, journal
        self.read_snapshot, self.origin, self.csrf_token = _BoundedSnapshot(read_snapshot), origin, csrf_token
        self.wall_clock, self.monotonic, self.supervisor_factory = wall_clock, monotonic, supervisor_factory
        self.supervisor = None

    def _authorize(self, principal, headers):
        if not isinstance(headers, dict):
            raise VoiceGatewayError("Voice request is not authorized")
        normalized = {}
        for name, value in headers.items():
            if not isinstance(name, str) or not isinstance(value, str) or name.lower() in normalized:
                raise VoiceGatewayError("Ambiguous HTTP headers")
            normalized[name.lower()] = value
        if (principal != self.grant.owner or not isinstance(principal, str)
                or normalized.get("origin") != self.origin
                or not hmac.compare_digest(normalized.get("x-voice-csrf", "").encode(), self.csrf_token.encode())):
            raise VoiceGatewayError("Voice request is not authorized")
        return normalized

    def create(self, *, principal: str, headers: dict[str, str], body: bytes):
        headers = self._authorize(principal, headers)
        self.grant.validate()
        if (headers.get("content-type", "").split(";", 1)[0] != "application/json"
                or not isinstance(body, bytes) or len(body) > 65536):
            raise VoiceGatewayError("Bounded JSON SDP offer required")
        try:
            offer = json.loads(body)
            if not isinstance(offer, dict) or set(offer) != {"sdp"}:
                raise ValueError()
            payload = session_request(approved_model=self.grant.model, sdp=offer["sdp"])
            status_summary(self.read_snapshot(), self.grant.binding)
        except Exception:
            raise VoiceGatewayError("Voice offer or bound read-only context is invalid") from None
        began = self.monotonic()
        self.journal.reserve(self.grant, self.wall_clock())  # MUST succeed before paid I/O.
        identity, sideband = None, None
        try:
            result = self.provider.create(payload, timeout=min(8, self.grant.max_seconds))
            identity = result.get("session", {}).get("id") if isinstance(result, dict) else None
            if not isinstance(identity, str) or not _ID.fullmatch(identity):
                identity = None
                raise VoiceGatewayError("Invalid provider identity")
            self.journal.record(self.grant.request_id, state="created", session_id=identity)
            answer = result.get("transport")
            if (not isinstance(answer, dict) or answer.get("type") != "webrtc"
                    or not isinstance(answer.get("sdp"), str) or not answer["sdp"].startswith("v=0")
                    or len(answer["sdp"].encode()) > 60000):
                raise VoiceGatewayError("Invalid provider SDP")
            sideband = self.provider.attach(identity, timeout=5)
            pilot = ReadOnlyVoicePilot(binding=self.grant.binding, read_snapshot=self.read_snapshot,
                                       voice_session_id=identity, max_seconds=self.grant.max_seconds)
            # HTTP WebRTC creation already initialized the session; an attached
            # sideband belongs to that running session, no session.start is sent.
            pilot.handle({"type": "session.started", "event_id": "trusted-http-creation", "session": {"id": identity}})
            remaining = self.grant.max_seconds - (self.monotonic() - began)
            if remaining <= 0:
                raise VoiceGatewayError("Candidate session window expired during startup")
            self.supervisor = self.supervisor_factory(provider=self.provider, sideband=sideband, pilot=pilot,
                journal=self.journal, request_id=self.grant.request_id, remaining_seconds=remaining,
                monotonic=self.monotonic)
            self.journal.record(self.grant.request_id, state="active")
            self.supervisor.start()
            return {"session": {"id": identity}, "transport": {"type": "webrtc", "sdp": answer["sdp"]}}
        except Exception:
            if sideband is not None:
                try:
                    sideband.close()
                except Exception:
                    pass
            if identity is not None:
                try:
                    self.provider.hangup(identity)
                except Exception:
                    pass
            try:
                self.journal.record(self.grant.request_id,
                                    state="finalization_unknown" if identity else "creation_unknown")
            except Exception:
                pass
            raise VoiceGatewayError("Voice creation is not confirmed; inspect the original receipt, never repeat") from None

    def abandon(self, *, principal, headers, body):
        self._authorize(principal, headers)
        if not isinstance(body, bytes) or len(body) > 1024:
            raise VoiceGatewayError("Invalid close request")
        try:
            value = json.loads(body)
            receipt = self.journal.read(self.grant.request_id)
            if (not isinstance(value, dict) or set(value) != {"session_id"}
                    or not isinstance(value["session_id"], str) or not _ID.fullmatch(value["session_id"])
                    or value["session_id"] != receipt["session_id"]):
                raise ValueError()
        except Exception:
            raise VoiceGatewayError("Voice session is not owned by this request") from None
        if self.supervisor is not None:
            self.supervisor.request_close()
        elif receipt["state"] not in _TERMINAL:
            # A restarted process must not silently attach or repeat creation.
            raise VoiceGatewayError("Original supervisor unavailable; manual receipt audit required")
        return {"close_requested": True, "final_usage_confirmed": receipt["final_usage_confirmed"]}

    def dispatch(self, *, method, path, principal, headers, body):
        """Inert exact-path adapter; the host supplies its authenticated principal."""
        routes = {"/api/human-adam/voice-candidate/session": self.create,
                  "/api/human-adam/voice-candidate/close": self.abandon}
        if path not in routes:
            return None
        if method != "POST":
            return 405, {"error": "voice_post_required"}
        try:
            self._authorize(principal, headers)
        except VoiceGatewayError:
            return 403, {"error": "voice_not_authorized"}
        try:
            result = routes[path](principal=principal, headers=headers, body=body)
            return (201 if path.endswith("/session") else 200), result
        except VoiceGatewayError:
            return 409, {"error": "voice_not_confirmed", "retry_allowed": False}


def create_candidate_session(*, gateway: CandidateVoiceGateway, principal, headers, body):
    """Registered candidate operation. All authority comes from the trusted host."""
    return gateway.create(principal=principal, headers=headers, body=body)
