"""Cockpit network-trusted browser adapter for the bounded read-only voice pilot.

A browser cookie identifies a one-shot attempt, not an authenticated person.
Access inherits Cockpit's allowed Host/private-network perimeter. Exact Origin
and CSRF protect mutations. No runtime/thread creation, history or tools here.
"""
from __future__ import annotations

import hmac
import html
import json
import os
import re
import secrets
import threading
import time
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urlparse

from app.communication.voice_conversation_gateway import (
    CandidateVoiceGateway, CandidateVoiceGrant, OpenAILiveProvider,
    VoiceAttemptJournal, VoiceGatewayError,
)
from app.communication.voice_conversation_pilot import VoiceBinding, status_summary
from app.communication.voice_conversation_roles import load_voice_role

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "app/frontend/voice_pilot"
COOKIE = "samantha_voice_attempt"
TOKEN = re.compile(r"[a-f0-9]{48}\Z")
PREFIX = "/api/human-adam/voice-candidate/"
CONFIRMATION = "Souhlasím s jednou hlasovou relací do 60 sekund za přibližně 0,05 USD."


def capture_existing_thread(manager):
    """Never call active_service/.hub factories or recover a detached thread."""
    with manager._state_lock:
        workstream = manager.active_workstream_id
        record = manager.workstream_backends.binding(workstream)
        adapter = record.compatibility_adapter
        service = adapter.service if adapter is not None else manager._lazy_services.get(workstream)
        hub = getattr(service, "_hub", None)
        if hub is None:
            raise VoiceGatewayError("Nejprve připoj vybraný proud v Human–Adam.")
        initial_session = hub.snapshot()
        if initial_session.get("connected") is not True:
            raise VoiceGatewayError("Nejprve připoj vybraný proud v Human–Adam.")
        initial = {"workstream_id": workstream, "session": initial_session}
        binding = VoiceBinding(workstream, initial_session.get("thread_id"))
        status_summary(initial, binding)

    def read():
        with manager._state_lock:
            if manager.active_workstream_id != binding.workstream_id:
                raise VoiceGatewayError("Vybraný pracovní proud se změnil.")
            current = manager.workstream_backends.binding(workstream).compatibility_adapter
            selected = current.service if current is not None else manager._lazy_services.get(workstream)
            if selected is not service or getattr(selected, "_hub", None) is not hub:
                raise VoiceGatewayError("Původní backend se změnil.")
            session = hub.snapshot()
            if session.get("connected") is not True:
                raise VoiceGatewayError("Stav odpojeného backendu není potvrzený.")
            snapshot = {"workstream_id": workstream, "session": session}
            status_summary(snapshot, binding)
            return snapshot
    return binding, read


def project_provider():
    if os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/") != "https://api.openai.com/v1":
        raise VoiceGatewayError("Pro hlas není schválený alternativní provider.")
    return OpenAILiveProvider(os.environ.get("OPENAI_API_KEY", ""))


class CockpitVoiceRoutes:
    def __init__(self, manager, *, journal_directory=None, provider_factory=project_provider,
                 role_loader=load_voice_role, capture=capture_existing_thread, clock=time.monotonic,
                 gateway_factory=CandidateVoiceGateway):
        self.gateway_factory = gateway_factory
        self.manager = manager
        self.journal = VoiceAttemptJournal(journal_directory or ROOT / "data/private/communication/voice_sessions")
        self.provider_factory, self.role_loader, self.capture = provider_factory, role_loader, capture
        self.clock, self.lock, self.contexts = clock, threading.RLock(), {}

    @staticmethod
    def cookie(headers):
        try:
            cookies = SimpleCookie()
            cookies.load(headers.get("Cookie", ""))
            value = cookies[COOKIE].value
            return value if TOKEN.fullmatch(value) else None
        except (KeyError, TypeError, ValueError):
            return None

    def page(self, headers):
        # GET is inert: no journal writes, key access, runtime startup or API I/O.
        with self.lock:
            now = self.clock()
            self.contexts = {key: item for key, item in self.contexts.items()
                             if now - item["created"] < 3600}
            owner = self.cookie(headers) or secrets.token_hex(24)
            item = self.contexts.get(owner)
            if item is None or not item["attempted"]:
                if owner not in self.contexts and len(self.contexts) >= 256:
                    raise VoiceGatewayError("Hlasový panel je dočasně obsazený.")
                item = {"created": now, "csrf": secrets.token_hex(24), "attempted": self.journal.path(owner).exists(),
                        "gateway": None}
                try:
                    item["role"] = self.role_loader()
                    item["binding"], item["read"] = self.capture(self.manager)
                    item["message"] = "Připraveno. Mikrofon je vypnutý."
                except Exception:
                    item["message"] = "Hlas není připravený. Ověř hlasovou roli a připoj proud v Human–Adam."
                self.contexts[owner] = item
            can_renew = False
            if item["attempted"]:
                try:
                    receipt = self.journal.read(owner)
                    can_renew = receipt["state"] == "closed" and receipt["final_usage_confirmed"] is True
                except Exception:
                    pass
            enabled = "binding" in item and not item["attempted"]
            message = "Tento pokus už proběhl. Další relaci automaticky nevytvářím." if item["attempted"] else item["message"]
            page = (FRONTEND / "page.html").read_text()
            values = {"VOICE_CAN_RENEW": "true" if can_renew else "false", "VOICE_CSRF": item["csrf"], "VOICE_READY": "true" if enabled else "false",
                      "VOICE_STATUS": message, "VOICE_BINDING": getattr(item.get("binding"), "workstream_id", "nepřipojený proud"),
                      "VOICE_CONFIRMATION": CONFIRMATION}
            for key, value in values.items():
                page = page.replace("{{" + key + "}}", html.escape(value, quote=True))
            # All remote access requires HTTPS for microphone; loopback HTTP is supported.
            host = headers.get("Host", "")
            local = urlparse("http://" + host).hostname in {"localhost", "127.0.0.1"}
            cookie = f"{COOKIE}={owner}; Path=/; HttpOnly; SameSite=Strict" + ("" if local else "; Secure")
            return page, cookie

    def post(self, path, headers, body):
        if path not in {PREFIX + "session", PREFIX + "close", PREFIX + "new"}:
            return 404, {"error": "not_found"}
        try:
            # Reject duplicate authority/framing headers before flattening HTTPMessage.
            if hasattr(headers, "get_all") and any(len(headers.get_all(name) or []) > 1
                    for name in ("Cookie", "Origin", "Host", "X-Voice-CSRF", "Content-Type")):
                raise VoiceGatewayError("Ambiguous authority")
            with self.lock:
                owner = self.cookie(headers)
                item = self.contexts.get(owner)
                origin = headers.get("Origin", "")
                parsed = urlparse(origin)
                if (item is None or self.clock() - item["created"] >= 3600
                        or parsed.netloc != headers.get("Host") or parsed.path or parsed.query or parsed.fragment
                        or parsed.username or parsed.password or parsed.scheme not in {"http", "https"}
                        or (parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1"})
                        or not hmac.compare_digest(headers.get("X-Voice-CSRF", ""), item["csrf"])):
                    return 403, {"error": "voice_not_authorized"}
                if path.endswith("/new"):
                    receipt = self.journal.read(owner)
                    if (json.loads(body) != {"confirmation": CONFIRMATION}
                            or receipt["state"] != "closed" or receipt["final_usage_confirmed"] is not True
                            or item.get("renewed")):
                        raise VoiceGatewayError("Previous session is not conclusively closed")
                    item["renewed"] = True
                    # Only an explicit click after final server evidence permits
                    # a new browser attempt. Never erase or reuse the old receipt.
                    return 200, {"ok": True, "_voice_cookie": f"{COOKIE}=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0"}
                if path.endswith("/close"):
                    gateway = item["gateway"]
                    if gateway is None:
                        raise VoiceGatewayError("No owned session")
                else:
                    if item["attempted"] or "binding" not in item:
                        raise VoiceGatewayError("No new attempt")
                    value = json.loads(body)
                    if (not isinstance(value, dict) or set(value) != {"sdp", "confirmation"}
                            or value["confirmation"] != CONFIRMATION
                            or headers.get("Content-Type", "").split(";", 1)[0] != "application/json"):
                        raise VoiceGatewayError("Explicit price confirmation required")
                    if self.role_loader() != item["role"]:
                        raise VoiceGatewayError("Role changed")
                    item["read"]()  # Reject changed selection before any provider activity.
                    item["attempted"] = True  # Reserve in memory before releasing lock.
                    gateway = self.gateway_factory(
                        grant=CandidateVoiceGrant(owner, owner, item["role"]["model"], item["binding"],
                                                  max_seconds=60, confirmed_live_test=True),
                        provider=self.provider_factory(), journal=self.journal, read_snapshot=item["read"],
                        origin=origin, csrf_token=item["csrf"])
                    item["gateway"] = gateway
                    body = json.dumps({"sdp": value["sdp"]}).encode()
            # Never hold the browser registry lock during provider I/O/watchdog.
            return gateway.dispatch(method="POST", path=path, principal=owner, headers=dict(headers), body=body)
        except Exception:
            return 409, {"error": "voice_not_confirmed", "retry_allowed": False}

    @staticmethod
    def asset(path):
        assets = {"/human-adam/voice/" + name: name for name in ("conversation.js", "panel.js", "cockpit.js")}
        return (FRONTEND / assets[path]).read_text() if path in assets else None
