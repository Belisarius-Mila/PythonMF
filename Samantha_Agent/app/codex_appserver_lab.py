"""Private App-server LAB service for the first Cockpit vertical slice."""

from __future__ import annotations

import atexit
import os
import re
import shutil
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.codex_appserver import (
    LAB_DEVELOPER_INSTRUCTIONS,
    AppServerError,
    CodexAppServerClient,
    TurnReceipt,
    read_codex_version,
    utc_now,
)
from app.file_persistence import atomic_write_json


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LAB_STATE_PATH = PROJECT_ROOT / "data" / "private" / "appserver_lab" / "state.json"
DEFAULT_CODEX_BIN = os.environ.get("CODEX_BIN") or shutil.which("codex") or "/usr/local/bin/codex"
MAX_LAB_MESSAGES = 40
MAX_LIFECYCLE_EVENTS = 40
CLIENT_MESSAGE_ID_RE = re.compile(r"^appserver-lab-[A-Za-z0-9_-]{8,96}$")


def normalize_client_timestamp(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def empty_lab_state() -> dict[str, Any]:
    return {
        "thread_id": "",
        "created_at": "",
        "updated_at": "",
        "connection_state": "disconnected",
        "connection_generation": 0,
        "connection_id": "",
        "process_pid": 0,
        "lifecycle_events": [],
        "messages": [],
    }


class AppServerLabService:
    def __init__(
        self,
        *,
        state_path: Path = DEFAULT_LAB_STATE_PATH,
        project_root: Path = PROJECT_ROOT,
        client_factory: Callable[..., CodexAppServerClient] = CodexAppServerClient,
        version_getter: Callable[..., Any] = read_codex_version,
        codex_binary: str = DEFAULT_CODEX_BIN,
    ):
        self.state_path = Path(state_path)
        self.project_root = Path(project_root)
        self.client_factory = client_factory
        self.version_getter = version_getter
        self.codex_binary = codex_binary
        self._client: CodexAppServerClient | None = None
        self._lock = threading.RLock()
        self._state = self._load_state()
        self._state["connection_state"] = "disconnected"
        self._state["connection_id"] = ""
        self._state["process_pid"] = 0

    def _load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return empty_lab_state()
        try:
            import json

            loaded = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return empty_lab_state()
        if not isinstance(loaded, dict):
            return empty_lab_state()
        messages = loaded.get("messages")
        loaded["messages"] = messages[-MAX_LAB_MESSAGES:] if isinstance(messages, list) else []
        lifecycle_events = loaded.get("lifecycle_events")
        loaded["lifecycle_events"] = (
            lifecycle_events[-MAX_LIFECYCLE_EVENTS:] if isinstance(lifecycle_events, list) else []
        )
        for key, default in empty_lab_state().items():
            loaded.setdefault(key, default)
        return loaded

    def _save(self) -> None:
        self._state["updated_at"] = utc_now()
        atomic_write_json(self.state_path, self._state, ensure_ascii=False, indent=2)

    def _version_payload(self) -> dict[str, Any]:
        try:
            version = self.version_getter(self.codex_binary)
        except AppServerError as exc:
            return {"ok": False, "raw": "", "message": str(exc)}
        return {
            "ok": True,
            "raw": version.raw,
            "major": version.major,
            "minor": version.minor,
            "patch": version.patch,
        }

    def status(self) -> dict[str, Any]:
        with self._lock:
            connected = bool(self._client and self._client.running)
            self._state["connection_state"] = "connected" if connected else "disconnected"
            return {
                "ok": True,
                "lab": True,
                "read_only": True,
                "connection_state": self._state["connection_state"],
                "thread_id": str(self._state.get("thread_id") or ""),
                "thread_ready": bool(self._state.get("thread_id")),
                "connection_generation": int(self._state.get("connection_generation") or 0),
                "connection_id": str(self._state.get("connection_id") or ""),
                "process_pid": int(self._state.get("process_pid") or 0),
                "lifecycle_events": list(self._state.get("lifecycle_events") or []),
                "created_at": str(self._state.get("created_at") or ""),
                "updated_at": str(self._state.get("updated_at") or ""),
                "messages": list(self._state.get("messages") or []),
                "version": self._version_payload(),
                "message": (
                    "LAB je připojený k read-only app-server threadu."
                    if connected
                    else "LAB není připojený. Testovací thread lze obnovit nebo založit."
                ),
            }

    def _close_client(self) -> None:
        if self._client is not None:
            self._client.close()
        self._client = None
        self._state["connection_state"] = "disconnected"
        self._state["connection_id"] = ""
        self._state["process_pid"] = 0

    def _connection_evidence(self) -> dict[str, Any]:
        return {
            "generation": int(self._state.get("connection_generation") or 0),
            "connection_id": str(self._state.get("connection_id") or ""),
            "process_pid": int(self._state.get("process_pid") or 0),
        }

    def _activate_client(self, client: CodexAppServerClient) -> None:
        self._client = client
        self._state["connection_state"] = "connected"
        self._state["connection_generation"] = int(self._state.get("connection_generation") or 0) + 1
        self._state["connection_id"] = str(client.connection_id)
        self._state["process_pid"] = int(client.process_id)

    def _append_lifecycle_event(
        self,
        *,
        action: str,
        started_at: str,
        previous: dict[str, Any],
        ok: bool = True,
    ) -> None:
        current = self._connection_evidence()
        event = {
            "event_id": uuid.uuid4().hex,
            "action": action,
            "started_at": started_at,
            "completed_at": utc_now(),
            "ok": bool(ok),
            "thread_id": str(self._state.get("thread_id") or ""),
            "previous_generation": int(previous.get("generation") or 0),
            "connection_generation": int(current.get("generation") or 0),
            "previous_connection_id": str(previous.get("connection_id") or ""),
            "connection_id": str(current.get("connection_id") or ""),
            "previous_process_pid": int(previous.get("process_pid") or 0),
            "process_pid": int(current.get("process_pid") or 0),
        }
        events = list(self._state.get("lifecycle_events") or [])
        events.append(event)
        self._state["lifecycle_events"] = events[-MAX_LIFECYCLE_EVENTS:]

    def new_thread(self) -> dict[str, Any]:
        with self._lock:
            started_at = utc_now()
            previous = self._connection_evidence()
            self._close_client()
            client = self.client_factory(codex_binary=self.codex_binary)
            try:
                thread_id = client.start_thread(
                    cwd=self.project_root,
                    ephemeral=False,
                    developer_instructions=LAB_DEVELOPER_INSTRUCTIONS,
                )
            except Exception:
                client.close()
                raise
            self._state = {
                **empty_lab_state(),
                "thread_id": thread_id,
                "created_at": utc_now(),
                "updated_at": utc_now(),
            }
            self._activate_client(client)
            self._append_lifecycle_event(action="thread_created", started_at=started_at, previous=previous)
            self._save()
            return self.status()

    def _connect_existing(self, *, action: str) -> None:
        thread_id = str(self._state.get("thread_id") or "")
        if not thread_id:
            raise AppServerError("LAB ještě nemá testovací thread.")
        started_at = utc_now()
        previous = self._connection_evidence()
        self._close_client()
        client = self.client_factory(codex_binary=self.codex_binary)
        try:
            client.resume_thread(
                thread_id,
                cwd=self.project_root,
                developer_instructions=LAB_DEVELOPER_INSTRUCTIONS,
            )
        except Exception:
            client.close()
            raise
        self._activate_client(client)
        self._append_lifecycle_event(action=action, started_at=started_at, previous=previous)
        self._save()

    def resume(self) -> dict[str, Any]:
        with self._lock:
            self._connect_existing(action="thread_resumed")
            return self.status()

    def disconnect(self) -> dict[str, Any]:
        with self._lock:
            started_at = utc_now()
            previous = self._connection_evidence()
            self._close_client()
            self._append_lifecycle_event(action="disconnected", started_at=started_at, previous=previous)
            self._save()
            return self.status()

    def close(self) -> None:
        with self._lock:
            self._close_client()

    def restart(self) -> dict[str, Any]:
        with self._lock:
            self._connect_existing(action="appserver_restarted")
            result = self.status()
            result["message"] = "LAB app-server byl restartován a stejný thread byl obnoven."
            result["restarted"] = True
            return result

    def _existing_message(self, client_message_id: str) -> dict[str, Any] | None:
        for message in self._state.get("messages") or []:
            if isinstance(message, dict) and message.get("client_message_id") == client_message_id:
                return message
        return None

    def send(self, *, text: str, client_message_id: str, client_sent_at: str = "") -> dict[str, Any]:
        clean_text = str(text or "").strip()
        if not clean_text:
            return {"ok": False, "status": "empty_message", "message": "Napiš testovací otázku nebo pokyn."}
        clean_id = str(client_message_id or "").strip()
        if not CLIENT_MESSAGE_ID_RE.fullmatch(clean_id):
            return {"ok": False, "status": "invalid_message_id", "message": "Zpráva nemá platné LAB ID."}

        with self._lock:
            existing = self._existing_message(clean_id)
            if existing is not None:
                return {
                    "ok": existing.get("status") == "completed",
                    "status": "duplicate_returned",
                    "message": "Tento požadavek už Cockpit přijal; vracím původní výsledek bez nového turnu.",
                    "entry": existing,
                    "duplicate_prevented": True,
                }
            if self._client is None or not self._client.running:
                self._connect_existing(action="auto_resumed_before_send")

            entry: dict[str, Any] = {
                "client_message_id": clean_id,
                "user_text": clean_text,
                "client_sent_at": normalize_client_timestamp(client_sent_at),
                "cockpit_received_at": utc_now(),
                "adam_accepted_at": "",
                "turn_started_at": "",
                "completed_at": "",
                "status": "sending",
                "answer": "",
                "thread_id": str(self._state.get("thread_id") or ""),
                "turn_id": "",
                "duration_ms": 0,
            }
            messages = list(self._state.get("messages") or [])
            messages.append(entry)
            self._state["messages"] = messages[-MAX_LAB_MESSAGES:]
            self._save()
            try:
                assert self._client is not None
                receipt: TurnReceipt = self._client.send_text(
                    thread_id=entry["thread_id"],
                    text=clean_text,
                    client_message_id=clean_id,
                )
            except AppServerError as exc:
                entry.update({"status": "failed", "completed_at": utc_now(), "error": str(exc)})
                self._save()
                return {
                    "ok": False,
                    "status": "delivery_failed",
                    "message": "App-server nepotvrdil jednoznačné doručení.",
                    "entry": entry,
                }
            entry.update(
                {
                    "adam_accepted_at": receipt.accepted_at,
                    "turn_started_at": receipt.started_at,
                    "completed_at": receipt.completed_at,
                    "status": "completed",
                    "answer": receipt.answer,
                    "turn_id": receipt.turn_id,
                    "duration_ms": receipt.duration_ms,
                    "user_item_count": receipt.user_item_count,
                    "turn_started_confirmed": receipt.turn_started_confirmed,
                }
            )
            self._save()
            return {
                "ok": True,
                "status": "completed",
                "message": "Zpráva byla potvrzena ve správném app-server turnu.",
                "entry": entry,
                "duplicate_prevented": False,
            }


APP_SERVER_LAB = AppServerLabService()
atexit.register(APP_SERVER_LAB.close)


def new_client_message_id() -> str:
    return f"appserver-lab-{uuid.uuid4().hex}"
