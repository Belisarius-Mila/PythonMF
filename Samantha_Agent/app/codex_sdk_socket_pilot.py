"""05/P1-C: fixture-only SDK/CLI proxy experiment; no production imports.

Callers supply a synthetic socket in their own temporary directory. This is
neither a runtime controller nor a persistent delivery journal. Never point it
at the shared Samantha socket. No automatic retry or thread creation exists.
"""

from __future__ import annotations

import queue
import threading
import time
from pathlib import Path
from typing import Any, Callable

from app.codex_sdk_pilot import Delivery, PilotContractError, evaluate_events, proxy_config


def deny_approval(method: str, _params: Any) -> dict[str, str]:
    """Override SDK 0.163's accepting default; unknown requests fail closed."""
    if method in {"item/commandExecution/requestApproval", "item/fileChange/requestApproval"}:
        return {"decision": "decline"}
    raise PilotContractError("Unsupported server request; no approval granted")


class FixtureProxyClient:
    """Bound synchronous SDK calls; timeout destroys ONLY this proxy child.

    The ledger is intentionally process-local and must not replace the session
    hub. It reserves a client ID before sending; all exceptions stay unknown.
    Timeout does not prove that the server stopped or that an action failed.
    """

    def __init__(self, *, codex_binary: Path, fixture_directory: Path,
                 cwd: Path, timeout: float = 3.0):
        from openai_codex.client import CodexClient

        if timeout <= 0 or not fixture_directory.is_absolute():
            raise PilotContractError("Explicit fixture directory and positive timeout required")
        if (fixture_directory / "fixture-only").read_text() != "05/P1-C synthetic RPC\n":
            raise PilotContractError("Synthetic fixture marker missing")
        self.timeout = timeout
        self.ledger: dict[str, str] = {}
        self._ledger_lock = threading.Lock()
        self.client = CodexClient(proxy_config(
            codex_binary=codex_binary, socket_path=fixture_directory / "rpc.sock", cwd=cwd,
        ), approval_handler=deny_approval)
        self.process = None
        self.closed = False
        try:
            self.client.start()
            self.process = self.client._proc  # Pilot-only lifecycle observation, not a public SDK contract.
            self.initialized = self.call(self.client.initialize)
        except BaseException:
            self.close()
            raise

    def call(self, operation: Callable[[], Any], *, timeout: float | None = None) -> Any:
        if self.closed:
            raise PilotContractError("Proxy is closed; reconnect is explicit, never a resend")
        result: queue.Queue[tuple[bool, Any]] = queue.Queue(maxsize=1)

        def run():
            try:
                result.put((True, operation()))
            except BaseException as exc:
                result.put((False, exc))

        worker = threading.Thread(target=run, daemon=True)
        worker.start()
        try:
            ok, value = result.get(timeout=max(0, self.timeout if timeout is None else timeout))
        except queue.Empty:
            self.close()
            worker.join(timeout=1)
            raise PilotContractError("Deadline expired; delivery_unknown; do not resend") from None
        if not ok:
            raise value
        return value

    def send_once(self, client_id: str, operation: Callable[[], Any]) -> Any:
        if not client_id:
            raise PilotContractError("Client ID required")
        with self._ledger_lock:
            if client_id in self.ledger:
                raise PilotContractError("Already attempted; audit original result instead of resending")
            self.ledger[client_id] = "pending"
        try:
            result = self.call(operation)
        except BaseException:
            with self._ledger_lock:
                self.ledger[client_id] = "delivery_unknown"
            raise
        with self._ledger_lock:
            self.ledger[client_id] = "awaiting_delivery_evidence"
        return result  # An RPC acknowledgement alone never confirms delivery.

    def observe_delivery(self, client_id: str, *, thread_id: str, turn_id: str) -> Delivery:
        """Bound the whole observation, including a stream that never completes."""
        deadline = time.monotonic() + self.timeout
        events = []
        try:
            while True:
                notification = self.call(lambda: self.client.next_turn_notification(turn_id),
                                         timeout=deadline - time.monotonic())
                payload = notification.payload
                params = (payload.model_dump(by_alias=True, mode="json")
                          if hasattr(payload, "model_dump") else payload.params)
                events.append({"method": notification.method, "params": params})
                if notification.method == "turn/completed":
                    break
        except Exception:
            # The incomplete transcript is evaluated as unknown, preserving raw
            # structured error events; no transport error proves non-delivery.
            pass
        delivery = evaluate_events(events, thread_id=thread_id, turn_id=turn_id, client_id=client_id)
        with self._ledger_lock:
            self.ledger[client_id] = delivery.state
        return delivery

    def close(self):
        if self.closed:
            return
        self.closed = True
        with self._ledger_lock:
            for client_id, state in self.ledger.items():
                if state in {"pending", "awaiting_delivery_evidence"}:
                    self.ledger[client_id] = "delivery_unknown"
        self.client.close()
        if self.process is not None:
            self.process.wait(timeout=3)
            for pipe in (self.process.stdin, self.process.stdout, self.process.stderr):
                if pipe is not None:
                    pipe.close()

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()
