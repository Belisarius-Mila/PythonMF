"""Project validated HA-03 events into small metadata, never store raw payloads."""
from __future__ import annotations

import threading
from contextlib import contextmanager

from app.codex_appserver import AppServerError
from app.communication.human_adam_work import WorkConflict

METHODS = ("turn/started", "turn/completed", "turn/plan/updated", "item/started", "item/completed")


class WorkObserver:
    def __init__(self, store, identity: str, owner: str):
        self.store, self.identity, self.owner = store, identity, owner
        self._lock = threading.RLock()
        self._subscription = None
        self._turn_id = ""
        self._buffer = []
        self._closed = False
        self._gap = False
        self._terminal_seen = threading.Event()

    def dispatching(self) -> None:
        """Durable barrier before the only permitted turn/start call."""
        self.store.change(self.identity, self.owner, "model_dispatching",
                          fields={"_dispatch_started": True, "delivery_state": "pending"})

    def assert_thread(self, thread_id: str) -> None:
        if thread_id != self.store.load(self.identity)["thread_id"]:
            raise WorkConflict("Vlákno se od přijetí změnilo; nový tah nebyl spuštěn.")

    def accepted(self, turn_id: str) -> None:
        with self._lock:
            self._turn_id = turn_id
            self.store.change(self.identity, self.owner, "turn_acknowledged", fields={"turn_id": turn_id})
            for event in self._buffer:
                self._apply(event)
            self._buffer.clear()

    @contextmanager
    def attach(self, client, thread_id: str):
        self.assert_thread(thread_id)
        try:
            self._subscription = client.subscribe_events(methods=METHODS, thread_id=thread_id,
                                                          max_events=128, max_bytes=4 * 1024 * 1024,
                                                          callback=self._event)
        except (AppServerError, AttributeError):
            self._gap = True  # Legacy test adapters still retain delivery proof.
        self.dispatching()
        try:
            yield self.accepted
        finally:
            self.close()

    def _event(self, event) -> None:
        params = event.params
        # Only validated type/scope and counters are retained. No plan text,
        # message content, reasoning, command arguments or paths enter this store.
        item = params.get("item") or {}
        kinds = {"commandExecution": "tool", "fileChange": "tool", "mcpToolCall": "tool",
                 "webSearch": "tool", "imageGeneration": "tool", "agentMessage": "message"}
        kind = event.kind
        if event.method in {"item/started", "item/completed"}:
            category = kinds.get(item.get("type"))
            if category is None:
                return
            kind = category + ("_started" if event.method == "item/started" else "_finished")
        safe = {"thread_id": event.thread_id, "turn_id": event.turn_id, "kind": kind,
                "generation": event.generation, "sequence": event.received_sequence}
        with self._lock:
            if self._closed:
                return
            if not self._turn_id:
                if len(self._buffer) < 64:
                    self._buffer.append(safe)
                else:
                    self._gap = True
            else:
                self._apply(safe)

    def _apply(self, event: dict) -> None:
        record = self.store.load(self.identity)
        if event["thread_id"] != record["thread_id"] or event["turn_id"] != self._turn_id:
            return
        self.store.change(self.identity, self.owner, event["kind"],
                          wire=(event["generation"], event["sequence"]))
        if event["kind"] == "turn_completed":
            self._terminal_seen.set()

    def close(self) -> None:
        # Give the separate metadata consumer a bounded chance to catch the
        # terminal event already consumed by the delivery guard. Otherwise
        # declare a gap instead of silently dropping queued/in-flight metadata.
        caught_up = self._terminal_seen.wait(.25) if self._subscription is not None else True
        with self._lock:
            if self._closed:
                return
            self._closed = True
            if self._subscription is not None:
                diagnostic = self._subscription.diagnostics()
                self._gap |= not caught_up or bool(diagnostic.get("closed")) or bool(diagnostic.get("queued"))
                self._subscription.close()
            if self._gap:
                try:
                    self.store.change(self.identity, self.owner, "event_gap", fields={"event_gap": True})
                except Exception:
                    pass
