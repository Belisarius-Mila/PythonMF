"""Bounded, connection-owned JSON-RPC routing. No retries, persistence or UI.

Only the wire reader calls feed. RPC waiters never consume notifications.
Callbacks run on subscription workers, never on the reader. Payloads are private
internal protocol data; neither repr nor diagnostics expose their contents.
"""
from __future__ import annotations

import json
import math
import re
import threading
import time
import uuid
from collections import OrderedDict, deque
from copy import deepcopy
from dataclasses import dataclass, field, replace
from typing import Any, Callable

from app.release_usage import normalize_usage

MAX_FRAME_BYTES = 64 * 1024 * 1024
MAX_BUFFER_BYTES = 128 * 1024 * 1024
_METHOD = re.compile(r"[A-Za-z][A-Za-z0-9_./:-]{0,127}\Z")
CORE_METHODS = frozenset({"turn/started", "turn/completed", "item/started", "item/completed", "error", "thread/tokenUsage/updated"})


class AppServerError(RuntimeError):
    def __init__(self, message: str):
        super().__init__(message)
        self.turn_error: dict[str, Any] | None = None
        self.will_retry: bool | None = None


class AppServerTimeout(AppServerError):
    """Required evidence did not arrive. Never permission to resend."""


class AppServerContractError(AppServerError):
    """Invalid or ambiguous protocol evidence."""


class AppServerClosedError(AppServerContractError):
    """This connection/subscription is closed; a new connection is explicit."""


class AppServerOverflowError(AppServerContractError):
    """A bounded buffer has a gap. It cannot silently continue as complete."""


def _identifier(value: Any) -> str | None:
    return value if isinstance(value, str) and 0 < len(value) <= 256 and all(32 < ord(c) < 127 for c in value) else None


def _member(value: Any, allowed: set[str]) -> bool:
    return isinstance(value, str) and value in allowed


def _rpc_id(value: Any) -> bool:
    return type(value) is int or bool(isinstance(value, str) and 0 < len(value) <= 128)


def _limit(value: int, maximum: int) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError("Neplatný limit dispatcheru.")
    return value


@dataclass(frozen=True, repr=False)
class AppServerEvent:
    method: str
    kind: str
    thread_id: str | None
    turn_id: str | None
    generation: str
    sequence: int
    compatibility: str = "core"
    _message: dict[str, Any] = field(default_factory=dict, repr=False)
    _bytes: int = field(default=0, repr=False)
    received_sequence: int = 0

    @property
    def params(self) -> dict[str, Any]:
        return deepcopy(self._message["params"])

    def as_message(self) -> dict[str, Any]:
        return deepcopy(self._message)

    def __repr__(self) -> str:
        return f"AppServerEvent(kind={self.kind!r}, sequence={self.sequence})"


def validated_notification(message: dict[str, Any], *, generation: str, sequence: int, size: int) -> AppServerEvent | None:
    """Validate consumed core fields, tolerate additive fields/legacy item shape.

    Reduced-scope plan/usage variants are explicit compatibility cases, not
    a claim of conformance to every field of the reference schema.
    Missing scope is never filled from whichever turn happens to be active.
    Invalid optional telemetry becomes an unavailable measurement, never
    evidence against delivery.
    """
    method, params = message["method"], message.get("params")
    if not isinstance(params, dict):
        return None
    thread = _identifier(params.get("threadId"))
    turn = _identifier(params.get("turnId"))
    for key in ("threadId", "turnId"):
        if key in params and _identifier(params[key]) is None:
            return None
    compatibility = "core"
    if method in {"turn/started", "turn/completed"}:
        body = params.get("turn")
        if not thread or not isinstance(body, dict) or not _identifier(body.get("id")):
            return None
        if turn and turn != body["id"]:
            return None
        turn = body["id"]
        status = body.get("status")
        if method == "turn/completed" and not _member(status, {"completed", "failed", "interrupted"}):
            return None
        if method == "turn/started" and status is not None and status != "inProgress":
            return None
        if "items" in body and (not isinstance(body["items"], list) or any(not isinstance(i, dict) for i in body["items"])):
            return None
        kind = "turn_started" if method == "turn/started" else "turn_completed"
    elif method in {"item/started", "item/completed"}:
        item = params.get("item")
        if not thread or not turn or not isinstance(item, dict) or not _identifier(item.get("id")) or not _identifier(item.get("type")):
            return None
        if item["type"] == "agentMessage" and (not isinstance(item.get("text"), str)
                or item.get("phase") is not None and not _member(item["phase"], {"commentary", "partial_answer", "final_answer"})):
            return None
        if item["type"] == "userMessage" and item.get("clientId") is not None and not _identifier(item["clientId"]):
            return None
        for key in ("startedAtMs", "completedAtMs"):
            if key in params and (type(params[key]) is not int or params[key] < 0):
                return None
        kind = "item_started" if method == "item/started" else "item_completed"
    elif method == "turn/plan/updated":
        plan = params.get("plan")
        if not turn or not isinstance(plan, list) or len(plan) > 128:
            return None
        if any(not isinstance(p, dict) or not isinstance(p.get("step"), str) or len(p["step"]) > 8192
               or not _member(p.get("status"), {"pending", "inProgress", "completed"}) for p in plan):
            return None
        if params.get("explanation") is not None and not isinstance(params["explanation"], str):
            return None
        kind = "plan"
        if not thread:
            compatibility = "compatible_turn_only"
    elif method == "thread/tokenUsage/updated":
        if not thread:
            return None
        usage = params.get("tokenUsage")
        total_valid = isinstance(usage, dict) and normalize_usage(usage.get("total"), camel_case=True) is not None
        # Preserve unknown measurement explicitly: dropping it would leave an old
        # good total in the receipt. Delivery itself must remain independent.
        kind = "thread_usage" if total_valid else "telemetry_unavailable"
        if not turn:
            compatibility = "compatible_thread_only"
    elif method in {"item/agentMessage/delta", "item/commandExecution/outputDelta", "item/fileChange/outputDelta", "item/plan/delta"}:
        if not thread or not turn or not _identifier(params.get("itemId")) or not isinstance(params.get("delta"), str):
            return None
        kind = "agent_delta" if method == "item/agentMessage/delta" else "item_delta"
    elif method == "error":
        error = params.get("error")
        if not thread or not turn or not isinstance(error, dict) or not isinstance(error.get("message"), str) or type(params.get("willRetry")) is not bool:
            return None
        kind = "turn_error"
    elif method == "thread/status/changed":
        status = params.get("status")
        if not thread or not isinstance(status, dict) or not _member(status.get("type"), {"notLoaded", "idle", "active", "systemError"}):
            return None
        if status["type"] == "active" and not isinstance(status.get("activeFlags"), list):
            return None
        kind = "thread_status"
    elif method in {"thread/closed", "thread/archived", "thread/unarchived"}:
        if not thread:
            return None
        kind = "thread_lifecycle"
    else:
        kind = "unknown"  # Explicit opt-in only; never validated progress.
        body = params.get("turn")
        if isinstance(body, dict) and _identifier(body.get("id")):
            if turn and turn != body["id"]:
                return None
            turn = body["id"]
    return AppServerEvent(method, kind, thread, turn, generation, 0, compatibility, message, size, received_sequence=sequence)


class _Mailbox:
    def __init__(self, max_events: int, max_bytes: int):
        self.max_events, self.max_bytes = max_events, max_bytes
        self._condition = threading.Condition()
        self._items: deque[AppServerEvent] = deque()
        self._bytes = 0
        self._revision = 0
        self._error: AppServerError | None = None

    def put(self, event: AppServerEvent, *, coalesce: bool = False) -> bool:
        with self._condition:
            if self._error:
                return False
            if coalesce:
                for old in list(self._items):
                    if (old.method, old.thread_id, old.turn_id) == (event.method, event.thread_id, event.turn_id):
                        self._items.remove(old); self._bytes -= old._bytes
            if len(self._items) >= self.max_events or self._bytes + event._bytes > self.max_bytes:
                self.close(AppServerOverflowError("Fronta událostí překročila limit; stav vyžaduje nové ověření."), discard=True)
                return False
            self._items.append(event); self._bytes += event._bytes; self._revision += 1
            self._condition.notify_all()
            return True

    def get(self, predicate: Callable[[AppServerEvent], bool], timeout: float | None) -> AppServerEvent:
        if timeout is not None and (type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout < 0):
            raise ValueError("Neplatný časový limit odběru.")
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            with self._condition:
                snapshot, revision, error = list(self._items), self._revision, self._error
            # No caller-supplied code may hold a routing/producer lock.
            chosen = next((e for e in snapshot if predicate(e)), None)
            with self._condition:
                if chosen is not None and chosen in self._items:
                    self._items.remove(chosen); self._bytes -= chosen._bytes; self._revision += 1
                    return chosen
                if self._revision != revision:
                    continue
                if error:
                    raise type(error)(str(error))
                remaining = None if deadline is None else deadline - time.monotonic()
                if remaining is not None and remaining <= 0:
                    raise AppServerTimeout("Vypršel čas při čekání na událost app-serveru.")
                self._condition.wait(remaining)

    def close(self, error: AppServerError, *, discard: bool = False) -> None:
        with self._condition:
            if self._error is None:
                self._error = error
            if discard:
                self._items.clear(); self._bytes = 0
            self._revision += 1
            self._condition.notify_all()

    def stats(self) -> dict[str, Any]:
        with self._condition:
            return {"queued": len(self._items), "bytes": self._bytes, "closed": self._error is not None}


class EventSubscription:
    """Independent bounded queue. get() is private protocol data, not UI output."""
    def __init__(self, owner, key, *, methods, thread_id, turn_id, include_unknown, max_events, max_bytes, callback):
        self._owner, self._key = owner, key
        self.methods, self.thread_id, self.turn_id = methods, thread_id, turn_id
        self.include_unknown = include_unknown
        self._mailbox = _Mailbox(max_events, max_bytes)
        self._callback = callback
        self._worker = None

    def matches(self, event: AppServerEvent) -> bool:
        return ((event.kind != "unknown" or self.include_unknown)
                and (self.methods is None or event.method in self.methods)
                and (self.thread_id is None or event.thread_id == self.thread_id)
                and (self.turn_id is None or event.turn_id == self.turn_id))

    def get(self, *, timeout: float | None = None) -> AppServerEvent:
        event = self._mailbox.get(lambda _event: True, timeout)
        return replace(event, _message=event.as_message())

    def _run_callback(self) -> None:
        try:
            while True:
                try:
                    event = self.get()
                except AppServerError:
                    return
                if not self._owner.running or self._mailbox.stats()["closed"]:
                    return
                try:
                    self._callback(event)
                except Exception:
                    self._owner._count("callback_failures")
                    return
        finally:
            self.close()
            self._owner._worker_done(self._key)

    def close(self) -> None:
        self._owner.unsubscribe(self._key)
        self._mailbox.close(AppServerClosedError("Odběr událostí je uzavřený."), discard=True)

    def diagnostics(self) -> dict[str, Any]:
        return self._mailbox.stats()

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()


@dataclass
class _Pending:
    method: str
    thread_id: str | None
    response: dict[str, Any] | None = None
    size: int = 0
    error: AppServerError | None = None


class AppServerDispatcher:
    def __init__(self, *, max_pending: int = 32, max_subscriptions: int = 32,
                 max_events: int = 512, max_bytes: int = MAX_BUFFER_BYTES,
                 max_bindings: int = 256, max_unresolved: int = 64):
        self.generation = uuid.uuid4().hex
        self._condition = threading.Condition()
        self._route_lock = threading.RLock()
        self._pending: dict[int, _Pending] = {}
        self._pending_bytes = 0
        self._subscriptions: dict[int, EventSubscription] = {}
        self._next_subscription = 0
        self._callback_workers: dict[int, EventSubscription] = {}
        self._legacy = _Mailbox(_limit(max_events, 8192), _limit(max_bytes, MAX_BUFFER_BYTES))
        self._max_pending = _limit(max_pending, 128)
        self._max_subscriptions = _limit(max_subscriptions, 128)
        self._max_bytes = max_bytes
        self._max_bindings = _limit(max_bindings, 4096)
        self._max_unresolved = _limit(max_unresolved, 512)
        self._bindings: OrderedDict[str, tuple[str, bool]] = OrderedDict()
        self._unresolved: deque[AppServerEvent] = deque()
        self._unresolved_bytes = 0
        self._closed: AppServerError | None = None
        self._reason = "open"
        self._sequence = 0
        self._published_sequence = 0
        self._counts: dict[str, int] = {}

    @property
    def running(self) -> bool:
        with self._condition:
            return self._closed is None

    def _count(self, key: str) -> None:
        with self._condition:
            self._counts[key] = self._counts.get(key, 0) + 1

    def register(self, request_id: int, method: str, params: dict[str, Any]) -> None:
        with self._condition:
            if self._closed:
                raise type(self._closed)(str(self._closed))
            if len(self._pending) >= self._max_pending:
                raise AppServerOverflowError("Příliš mnoho čekajících RPC požadavků; nový nebyl odeslán.")
            if request_id in self._pending:
                raise AppServerContractError("Opakovaná identita RPC požadavku.")
            self._pending[request_id] = _Pending(method, _identifier(params.get("threadId")))

    def wait(self, request_id: int, *, timeout: float) -> dict[str, Any]:
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout < 0:
            raise ValueError("Neplatný časový limit RPC.")
        deadline = time.monotonic() + timeout
        with self._condition:
            pending = self._pending[request_id]
            try:
                while pending.response is None and pending.error is None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        self._count("rpc_timeouts")
                        raise AppServerTimeout("Vypršel čas při čekání na RPC odpověď app-serveru.")
                    self._condition.wait(remaining)
                if pending.error:
                    raise type(pending.error)(str(pending.error))
                return pending.response
            finally:
                self._pending.pop(request_id, None)
                self._pending_bytes -= pending.size

    def forget(self, request_id: int) -> None:
        with self._condition:
            pending = self._pending.pop(request_id, None)
            if pending is not None:
                self._pending_bytes -= pending.size

    def close(self, error: AppServerError | None = None, *, reason: str = "closed", discard: bool = False) -> None:
        error = error or AppServerClosedError("Spojení s app-serverem je uzavřené.")
        with self._condition:
            if self._closed is not None:
                return
            self._closed, self._reason = error, reason
            for pending in self._pending.values():
                if pending.response is None or discard:
                    pending.error = error
            subscriptions = list(self._subscriptions.values())
            self._subscriptions.clear()
            self._counts["discarded_unresolved"] = self._counts.get("discarded_unresolved", 0) + len(self._unresolved)
            self._unresolved.clear(); self._unresolved_bytes = 0
            self._bindings.clear()
            self._condition.notify_all()
        self._legacy.close(error, discard=discard)
        for subscription in subscriptions:
            subscription._mailbox.close(error, discard=True)

    def subscribe(self, *, methods: tuple[str, ...] | None = None, thread_id: str | None = None,
                  turn_id: str | None = None, include_unknown: bool = False,
                  max_events: int = 128, max_bytes: int = 4 * 1024 * 1024,
                  callback: Callable[[AppServerEvent], None] | None = None) -> EventSubscription:
        if methods is not None and (not isinstance(methods, tuple) or not methods or len(methods) > 64
                or any(not isinstance(m, str) or not _METHOD.fullmatch(m) for m in methods)):
            raise ValueError("Neplatný výběr událostí.")
        if any(value is not None and _identifier(value) is None for value in (thread_id, turn_id)):
            raise ValueError("Neplatný rozsah odběru.")
        if type(include_unknown) is not bool or callback is not None and not callable(callback):
            raise ValueError("Neplatný odběr událostí.")
        _limit(max_events, 8192); _limit(max_bytes, MAX_BUFFER_BYTES)
        with self._condition:
            if self._closed:
                raise type(self._closed)(str(self._closed))
            if len(self._subscriptions) >= self._max_subscriptions or len(self._callback_workers) >= self._max_subscriptions:
                raise AppServerOverflowError("Příliš mnoho odběrů nebo nedokončených callbacků.")
            if sum(sub._mailbox.max_bytes for sub in self._subscriptions.values()) + max_bytes > MAX_BUFFER_BYTES:
                raise AppServerOverflowError("Odběry překročily společný paměťový rozpočet.")
            self._next_subscription += 1
            sub = EventSubscription(self, self._next_subscription, methods=None if methods is None else frozenset(methods),
                                    thread_id=thread_id, turn_id=turn_id, include_unknown=include_unknown,
                                    max_events=max_events, max_bytes=max_bytes, callback=callback)
            self._subscriptions[self._next_subscription] = sub
            if callback is not None:
                self._callback_workers[self._next_subscription] = sub
                sub._worker = threading.Thread(target=sub._run_callback, name="appserver-event-callback", daemon=True)
                try:
                    sub._worker.start()
                except RuntimeError:
                    self._subscriptions.pop(sub._key, None)
                    self._callback_workers.pop(sub._key, None)
                    sub._mailbox.close(AppServerClosedError("Odběr nelze zahájit."), discard=True)
                    raise AppServerError("Vlákno odběru událostí nelze zahájit.") from None
            return sub

    def unsubscribe(self, key: int) -> None:
        with self._condition:
            self._subscriptions.pop(key, None)

    def _worker_done(self, key: int) -> None:
        with self._condition:
            self._callback_workers.pop(key, None)

    def receive(self, predicate: Callable[[dict[str, Any]], bool], *, timeout: float) -> dict[str, Any]:
        event = self._legacy.get(lambda candidate: predicate(candidate.as_message()), timeout)
        return event.as_message()

    def _publish(self, event: AppServerEvent) -> None:
        if self._closed is not None:
            return
        # Deferred scope resolution may happen after another event was delivered.
        # Queue order stays monotonic; preserve wire order in a separate field.
        self._published_sequence += 1
        event = replace(event, sequence=self._published_sequence)
        params = event._message["params"]
        guard_payload = "item" in params or isinstance(params.get("turn"), dict) and "items" in params["turn"]
        if event.thread_id and event.turn_id and (event.method in CORE_METHODS or guard_payload):
            if not self._legacy.put(event, coalesce=event.method == "thread/tokenUsage/updated"):
                self.close(AppServerOverflowError("Fronta důkazů tahu překročila limit."), reason="capacity", discard=True)
                return
        for key, subscription in list(self._subscriptions.items()):
            if subscription.matches(event) and not subscription._mailbox.put(event):
                self._count("subscription_overflows")
                self._subscriptions.pop(key, None)

    def _bind(self, turn_id: str, thread_id: str, *, completed: bool = False) -> None:
        old = self._bindings.get(turn_id)
        if old and old[0] != thread_id:
            raise AppServerContractError("Identita tahu má rozporné přiřazení vlákna.")
        if not old and len(self._bindings) >= self._max_bindings:
            retired = next((key for key, value in self._bindings.items() if value[1]), None)
            if retired is None:
                raise AppServerOverflowError("Příliš mnoho aktivních vazeb tahů.")
            del self._bindings[retired]
        self._bindings[turn_id] = (thread_id, completed or bool(old and old[1]))
        for event in list(self._unresolved):
            if event.turn_id == turn_id:
                self._unresolved.remove(event); self._unresolved_bytes -= event._bytes
                self._publish(replace(event, thread_id=thread_id))

    def feed(self, message: Any, *, generation: str, size: int | None = None) -> bool:
        """Route one reader frame; False means the reader must stop this wire."""
        with self._route_lock, self._condition:
            if generation != self.generation:
                self._count("stale_generations")
                return self._closed is None
            if self._closed:
                return False
            try:
                size = len(json.dumps(message, ensure_ascii=False).encode()) if size is None else size
                if type(size) is not int or not 1 <= size <= MAX_FRAME_BYTES or not isinstance(message, dict) or message.get("jsonrpc", "2.0") != "2.0":
                    raise AppServerContractError("App-server vrátil neplatný rámec.")
                if "method" in message:
                    method = message["method"]
                    if not isinstance(method, str) or not _METHOD.fullmatch(method) or "result" in message or "error" in message:
                        raise AppServerContractError("App-server vrátil neplatnou obálku události.")
                    if "id" in message:
                        self._count("unhandled_server_requests")
                        self.close(AppServerContractError("App-server vyžádal nepovolenou klientskou operaci."), reason="server_request", discard=True)
                        return False
                    self._sequence += 1
                    event = validated_notification(message, generation=self.generation, sequence=self._sequence, size=size)
                    if event is None:
                        self._count("invalid_notifications")
                        params = message.get("params")
                        guard_payload = isinstance(params, dict) and (
                            "item" in params and params["item"] is not None
                            or isinstance(params.get("turn"), dict) and "items" in params["turn"])
                        if method in CORE_METHODS - {"thread/tokenUsage/updated"} or guard_payload:
                            raise AppServerContractError("App-server vrátil neplatný důkaz průběhu tahu.")
                    else:
                        self._count("unknown_notifications" if event.kind == "unknown" else
                                    "invalid_telemetry" if event.kind == "telemetry_unavailable" else "validated_notifications")
                        if event.compatibility != "core":
                            self._count("compatibility_variants")
                        if event.kind not in {"unknown", "telemetry_unavailable"} and event.thread_id and event.turn_id:
                            self._bind(event.turn_id, event.thread_id, completed=event.kind == "turn_completed")
                        if event.kind != "unknown" and event.turn_id and not event.thread_id:
                            binding = self._bindings.get(event.turn_id)
                            if binding:
                                event = replace(event, thread_id=binding[0])
                            else:
                                if len(self._unresolved) >= self._max_unresolved or self._unresolved_bytes + size > 4 * 1024 * 1024:
                                    raise AppServerOverflowError("Nevyřešené rozsahy událostí překročily limit.")
                                self._unresolved.append(event); self._unresolved_bytes += size
                                return True
                        self._publish(event)
                else:
                    if not _rpc_id(message.get("id")) or ("result" in message) == ("error" in message):
                        raise AppServerContractError("App-server vrátil neplatnou RPC odpověď.")
                    error = message.get("error")
                    if "error" in message and (not isinstance(error, dict) or type(error.get("code")) is not int or not isinstance(error.get("message"), str)):
                        raise AppServerContractError("App-server vrátil neplatnou RPC chybu.")
                    pending = self._pending.get(message["id"])
                    if pending is None:
                        self._count("orphan_responses")
                    elif pending.response is not None:
                        self._count("duplicate_responses")
                        if pending.response != message:
                            raise AppServerContractError("Rozporná opakovaná RPC odpověď.")
                    else:
                        if self._pending_bytes + size > self._max_bytes:
                            raise AppServerOverflowError("RPC odpovědi překročily limit paměti.")
                        result = message.get("result")
                        if pending.method == "turn/start" and pending.thread_id and isinstance(result, dict):
                            turn = result.get("turn")
                            if isinstance(turn, dict) and _identifier(turn.get("id")):
                                self._bind(turn["id"], pending.thread_id)
                        pending.response, pending.size = message, size
                        self._pending_bytes += size
                        self._condition.notify_all()
                return self._closed is None
            except (TypeError, ValueError, RecursionError, AppServerContractError) as exc:
                error = exc if isinstance(exc, AppServerContractError) else AppServerContractError("App-server vrátil neplatný rámec.")
                self.close(error, reason="capacity" if isinstance(error, AppServerOverflowError) else "protocol_error", discard=True)
                return False

    def diagnostics(self) -> dict[str, Any]:
        with self._route_lock, self._condition:
            return {"generation": self.generation, "closed": self._closed is not None, "close_reason": self._reason,
                    "pending_rpc": len(self._pending), "pending_bytes": self._pending_bytes,
                    "subscriptions": len(self._subscriptions), "callback_workers": len(self._callback_workers),
                    "subscription_reserved_bytes": sum(s._mailbox.max_bytes for s in self._subscriptions.values()),
                    "legacy": self._legacy.stats(),
                    "received_notifications": self._sequence, "published_notifications": self._published_sequence,
                    "bindings": len(self._bindings), "unresolved": len(self._unresolved),
                    "unresolved_bytes": self._unresolved_bytes, "counters": dict(self._counts)}
