"""Project validated HA-03 events into small metadata, never store raw payloads."""
from __future__ import annotations

import threading
from contextlib import contextmanager

from app.codex_appserver import AppServerError, AppServerSteerRejected
from app.communication.human_adam_work import WorkConflict
from app.communication.human_adam_public_progress import public_event, merge_public_progress

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
        self._client = None
        self._guard = None
        self._started = False

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
    def attach(self, client, thread_id: str, *, guard=None):
        self.assert_thread(thread_id)
        with self._lock:
            self._client, self._guard = client, guard
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

    def can_steer(self, expected_turn_id: str) -> bool:
        with self._lock:
            client, guard = self._client, self._guard
            ready = not self._closed and self._started and not self._terminal_seen.is_set() and self._turn_id == expected_turn_id
        check = getattr(client, "can_steer_turn", None)
        try:
            return bool(ready and callable(guard) and guard() is True and callable(check)
                        and check(self.store.load(self.identity)["thread_id"], expected_turn_id) is True)
        except Exception:
            return False

    def steer(self, *, expected_turn_id: str, command_id: str, text: str):
        if not self.can_steer(expected_turn_id):
            raise AppServerSteerRejected("work_not_running")
        with self._lock:
            client = self._client
        if client is None:
            raise AppServerSteerRejected("connection_unavailable")
        # No observer lock across RPC; terminal callbacks and the original
        # receive/delivery guard must remain able to finish independently.
        return client.steer_text(thread_id=self.store.load(self.identity)["thread_id"],
                                 expected_turn_id=expected_turn_id, command_id=command_id, text=text)

    def _event(self, event) -> None:
        params = event.params
        # Raw protocol payloads never enter the store. Public plan/commentary
        # text is rebuilt separately by a bounded whitelist, then applied only
        # after the exact turn/scope binding below.
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
        progress = public_event(event.method, params)
        if progress is not None:
            safe["public_progress_update"] = progress
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
        fields = {}
        if "public_progress_update" in event:
            fields["public_progress"] = merge_public_progress(record.get("public_progress"), event["public_progress_update"])
        _, changed = self.store.change(self.identity, self.owner, event["kind"], fields=fields,
                                       wire=(event["generation"], event["sequence"]), with_effect=True)
        if changed and event["kind"] == "turn_started":
            self._started = True
        if changed and event["kind"] == "turn_completed":
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
            self._client, self._guard = None, None
            if self._subscription is not None:
                diagnostic = self._subscription.diagnostics()
                self._gap |= not caught_up or bool(diagnostic.get("closed")) or bool(diagnostic.get("queued"))
                self._subscription.close()
            if self._gap:
                try:
                    self.store.change(self.identity, self.owner, "event_gap", fields={"event_gap": True})
                except Exception:
                    pass
