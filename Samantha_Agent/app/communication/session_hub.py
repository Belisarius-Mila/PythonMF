"""Single owner of Samantha's canonical Codex thread and turn lifecycle."""

from __future__ import annotations

import copy
import json
import re
import threading
from pathlib import Path
from typing import Any, Callable

from app.codex_appserver import AppServerError, CodexAppServerClient, TurnReceipt, utc_now
from app.file_persistence import atomic_write_json


CLIENT_MESSAGE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{7,127}")
MAX_MESSAGES = 500


class SessionHubError(RuntimeError):
    """Base error for the canonical communication session."""


class SessionBusyError(SessionHubError):
    """Raised when another client already owns the active turn."""


class SessionDeliveryUnknownError(SessionHubError):
    """Raised when retrying could duplicate an ambiguously accepted turn."""


def empty_session_state() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "thread_id": "",
        "thread_created_at": "",
        "updated_at": "",
        "connection_state": "disconnected",
        "connection_generation": 0,
        "active_turn": None,
        "messages": [],
    }


class CanonicalSessionHub:
    """Persist one canonical thread and serialize all Cockpit turns fail-closed."""

    def __init__(
        self,
        *,
        state_path: Path,
        workspace: Path,
        client_factory: Callable[[], CodexAppServerClient],
        developer_instructions: str,
        sandbox: str,
        sandbox_policy: dict[str, Any],
        approval_policy: str,
        reasoning_effort: str,
        model: str | None = None,
    ):
        self.state_path = Path(state_path)
        self.workspace = Path(workspace).resolve()
        self.client_factory = client_factory
        self.developer_instructions = str(developer_instructions).strip()
        self.sandbox = str(sandbox).strip()
        self.sandbox_policy = dict(sandbox_policy)
        self.approval_policy = str(approval_policy).strip()
        self.reasoning_effort = str(reasoning_effort).strip()
        self.model = str(model).strip() if model else None
        self._state_lock = threading.RLock()
        self._turn_lock = threading.Lock()
        self._client: CodexAppServerClient | None = None
        self._state = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return empty_session_state()
        try:
            loaded = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SessionHubError("Stav kanonické relace nelze bezpečně načíst.") from exc
        if not isinstance(loaded, dict) or loaded.get("schema_version") != 1:
            raise SessionHubError("Stav kanonické relace má neznámé schéma.")

        state = empty_session_state()
        state["thread_id"] = str(loaded.get("thread_id") or "").strip()
        state["thread_created_at"] = str(loaded.get("thread_created_at") or "").strip()
        state["updated_at"] = str(loaded.get("updated_at") or "").strip()
        state["connection_generation"] = max(0, int(loaded.get("connection_generation") or 0))
        messages = loaded.get("messages")
        if isinstance(messages, list):
            state["messages"] = [copy.deepcopy(item) for item in messages if isinstance(item, dict)][-MAX_MESSAGES:]
        for item in state["messages"]:
            if item.get("status") == "pending":
                item["status"] = "delivery_unknown"
                item["recovery_required"] = True
        state["connection_state"] = "disconnected"
        state["active_turn"] = None
        return state

    def _save_locked(self) -> None:
        self._state["updated_at"] = utc_now()
        atomic_write_json(self.state_path, self._state, ensure_ascii=False, indent=2)

    def snapshot(self) -> dict[str, Any]:
        with self._state_lock:
            payload = copy.deepcopy(self._state)
            payload["connected"] = bool(self._client and self._client.running)
            payload["turn_busy"] = self._turn_lock.locked()
            return payload

    def _new_client_locked(self) -> CodexAppServerClient:
        client: CodexAppServerClient | None = None
        try:
            client = self.client_factory()
            thread_id = str(self._state.get("thread_id") or "")
            if thread_id:
                try:
                    client.resume_thread(
                        thread_id,
                        cwd=self.workspace,
                        developer_instructions=self.developer_instructions,
                        sandbox=self.sandbox,
                        approval_policy=self.approval_policy,
                        model=self.model,
                    )
                except AppServerError:
                    if self._state["messages"]:
                        raise
                    # Codex doesn't materialize a new persistent thread until its
                    # first turn. Replacing an empty, non-resumable ID loses no work.
                    thread_id = ""
            if not thread_id:
                thread_id = client.start_thread(
                    cwd=self.workspace,
                    ephemeral=False,
                    developer_instructions=self.developer_instructions,
                    sandbox=self.sandbox,
                    approval_policy=self.approval_policy,
                    model=self.model,
                )
                self._state["thread_id"] = thread_id
                self._state["thread_created_at"] = utc_now()
            self._client = client
            self._state["connection_state"] = "connected"
            self._state["connection_generation"] = int(self._state["connection_generation"]) + 1
            self._save_locked()
            return client
        except Exception:
            if client is not None:
                client.close()
            self._state["connection_state"] = "error"
            self._save_locked()
            raise

    def connect(self) -> dict[str, Any]:
        with self._state_lock:
            if self._client is None or not self._client.running:
                self._close_client_locked()
                self._new_client_locked()
            return self.snapshot()

    def _close_client_locked(self) -> None:
        client = self._client
        self._client = None
        if client is not None:
            client.close()

    def close(self) -> None:
        if self._turn_lock.locked():
            raise SessionBusyError("Kanonickou relaci nelze zavřít během aktivního tahu.")
        with self._state_lock:
            self._close_client_locked()
            self._state["connection_state"] = "disconnected"
            self._state["active_turn"] = None
            self._save_locked()

    def _message_locked(self, client_message_id: str) -> dict[str, Any] | None:
        for item in self._state["messages"]:
            if item.get("client_message_id") == client_message_id:
                return item
        return None

    def send(self, *, text: str, client_message_id: str, client_sent_at: str = "") -> dict[str, Any]:
        clean_text = str(text or "").strip()
        clean_id = str(client_message_id or "").strip()
        if not clean_text:
            raise SessionHubError("Nelze odeslat prázdnou zprávu.")
        if not CLIENT_MESSAGE_ID_RE.fullmatch(clean_id):
            raise SessionHubError("Zpráva nemá platný client_message_id.")

        with self._state_lock:
            existing = self._message_locked(clean_id)
            if existing is not None:
                if existing.get("status") == "completed":
                    return {"ok": True, "duplicate_prevented": True, "entry": copy.deepcopy(existing)}
                raise SessionDeliveryUnknownError(
                    "Tato zpráva už byla přijata bez konečného důkazu; automaticky ji neposílám znovu."
                )

        if not self._turn_lock.acquire(blocking=False):
            raise SessionBusyError("Kanonická relace právě dokončuje jiný tah.")
        try:
            with self._state_lock:
                existing = self._message_locked(clean_id)
                if existing is not None:
                    if existing.get("status") == "completed":
                        return {"ok": True, "duplicate_prevented": True, "entry": copy.deepcopy(existing)}
                    raise SessionDeliveryUnknownError(
                        "Tato zpráva už byla přijata bez konečného důkazu; automaticky ji neposílám znovu."
                    )
                client = self._client if self._client and self._client.running else self._new_client_locked()
                pending = {
                    "client_message_id": clean_id,
                    "client_sent_at": str(client_sent_at or "").strip(),
                    "received_at": utc_now(),
                    "completed_at": "",
                    "status": "pending",
                    "user_text": clean_text,
                    "answer": "",
                    "thread_id": str(self._state["thread_id"]),
                    "turn_id": "",
                    "delivery_confirmed": False,
                    "recovery_required": False,
                }
                self._state["messages"].append(pending)
                self._state["messages"] = self._state["messages"][-MAX_MESSAGES:]
                self._state["active_turn"] = {
                    "client_message_id": clean_id,
                    "started_at": pending["received_at"],
                }
                self._save_locked()

            try:
                receipt: TurnReceipt = client.send_text(
                    thread_id=str(self._state["thread_id"]),
                    text=clean_text,
                    client_message_id=clean_id,
                    effort=self.reasoning_effort,
                    sandbox_policy=self.sandbox_policy,
                    approval_policy=self.approval_policy,
                    model=self.model,
                )
            except Exception as exc:
                with self._state_lock:
                    entry = self._message_locked(clean_id)
                    if entry is not None:
                        entry["status"] = "delivery_unknown"
                        entry["recovery_required"] = True
                    self._state["active_turn"] = None
                    self._state["connection_state"] = "error"
                    self._close_client_locked()
                    self._save_locked()
                if isinstance(exc, AppServerError):
                    raise
                raise SessionHubError("Tah kanonické relace selhal bez jistoty doručení.") from exc

            with self._state_lock:
                entry = self._message_locked(clean_id)
                if entry is None:
                    raise SessionHubError("Po dokončení tahu chybí jeho persistovaný záznam.")
                entry.update(
                    {
                        "completed_at": receipt.completed_at,
                        "status": "completed",
                        "answer": receipt.answer,
                        "thread_id": receipt.thread_id,
                        "turn_id": receipt.turn_id,
                        "delivery_confirmed": receipt.delivered,
                        "recovery_required": False,
                    }
                )
                self._state["active_turn"] = None
                self._state["connection_state"] = "connected"
                self._save_locked()
                return {"ok": True, "duplicate_prevented": False, "entry": copy.deepcopy(entry)}
        finally:
            self._turn_lock.release()
