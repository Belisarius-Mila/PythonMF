"""Connection-local input identities. An authorized append is never a new turn."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field

from app.codex_appserver_dispatch import AppServerContractError


class AppServerSteerRejected(AppServerContractError):
    """Known local rejection before any steer RPC was written."""
    def __init__(self, reason="work_not_running"):
        super().__init__("Doplnění nebylo odesláno do původního tahu.")
        self.reason = reason


@dataclass(repr=False)
class TurnInputs:
    thread_id: str
    turn_id: str
    original_id: str
    steer_enabled: bool
    commands: set[str] = field(default_factory=set)
    closed: bool = False


class TurnInputLedger:
    def __init__(self):
        self._lock = threading.RLock()
        self._turns = {}

    def begin(self, thread_id, turn_id, original_id, *, steer_enabled=False):
        with self._lock:
            key = (thread_id, turn_id)
            if key in self._turns or len(self._turns) >= 32:
                raise AppServerContractError("Vstupy tahu nemají jednoznačnou kapacitu nebo identitu.")
            state = TurnInputs(thread_id, turn_id, original_id, steer_enabled)
            self._turns[key] = state
            return state

    def available(self, thread_id, turn_id):
        with self._lock:
            state = self._turns.get((thread_id, turn_id))
            return bool(state and not state.closed and state.steer_enabled and len(state.commands) < 64)

    def reserve(self, thread_id, turn_id, command_id):
        with self._lock:
            state = self._turns.get((thread_id, turn_id))
            if not state or state.closed or not state.steer_enabled:
                raise AppServerSteerRejected("work_not_running")
            if command_id == state.original_id or command_id in state.commands:
                raise AppServerSteerRejected("command_identity_conflict")
            if len(state.commands) >= 64:
                raise AppServerSteerRejected("command_limit")
            # Reservation is an authorization identity, not delivery evidence.
            # Retain it on an uncertain/error RPC; never resend it here.
            state.commands.add(command_id)

    def original_proof(self, state, items):
        with self._lock:
            original = [item for item in items if item.get("clientId") == state.original_id]
            additional = [item.get("clientId") for item in items if item.get("clientId") != state.original_id]
            if (len(original) != 1 or any(not isinstance(identity, str) or identity not in state.commands for identity in additional)
                    or len(set(additional)) != len(additional)):
                return []
            return original

    def close(self, state):
        with self._lock:
            state.closed = True
            key = (state.thread_id, state.turn_id)
            if self._turns.get(key) is state:
                self._turns.pop(key)
