"""Private App-server LAB service for the first Cockpit vertical slice."""

from __future__ import annotations

import atexit
import json
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
MAX_REGISTERED_THREADS = 12
LAB_STATE_SCHEMA_VERSION = 2
CAPSULE_SCHEMA_VERSION = 1
MAX_THREAD_LABEL_CHARS = 60
MAX_THREAD_ROLE_CHARS = 40
MAX_CAPSULE_FIELD_CHARS = 600
MAX_CAPSULE_CONSTRAINT_CHARS = 200
MAX_CAPSULE_CONSTRAINTS = 6
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


def empty_context_capsule() -> dict[str, Any]:
    return {
        "schema_version": CAPSULE_SCHEMA_VERSION,
        "objective": "",
        "current_state": "",
        "next_step": "",
        "constraints": [],
        "revision": 0,
        "updated_at": "",
    }


def empty_lab_state() -> dict[str, Any]:
    return {
        "schema_version": LAB_STATE_SCHEMA_VERSION,
        "active_registry_id": "",
        "threads": [],
        "updated_at": "",
        "connection_state": "disconnected",
        "connection_generation": 0,
        "connection_id": "",
        "process_pid": 0,
    }


def _bounded_text(value: Any, *, field: str, max_chars: int) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise AppServerError(f"Pole {field} musí být text.")
    clean = value.replace("\x00", "").strip()
    if len(clean) > max_chars:
        raise AppServerError(f"Pole {field} smí mít nejvýše {max_chars} znaků.")
    return clean


def normalize_context_capsule(
    payload: dict[str, Any] | None,
    *,
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    raw = payload if isinstance(payload, dict) else {}
    constraints = raw.get("constraints", [])
    if constraints is None:
        constraints = []
    if not isinstance(constraints, list):
        raise AppServerError("Omezení v Context Capsule musí být seznam.")
    if len(constraints) > MAX_CAPSULE_CONSTRAINTS:
        raise AppServerError(f"Context Capsule smí mít nejvýše {MAX_CAPSULE_CONSTRAINTS} omezení.")
    clean_constraints = [
        _bounded_text(item, field="omezení", max_chars=MAX_CAPSULE_CONSTRAINT_CHARS)
        for item in constraints
    ]
    clean_constraints = [item for item in clean_constraints if item]
    old_revision = int((previous or {}).get("revision") or 0)
    return {
        "schema_version": CAPSULE_SCHEMA_VERSION,
        "objective": _bounded_text(
            raw.get("objective", ""), field="cíl", max_chars=MAX_CAPSULE_FIELD_CHARS
        ),
        "current_state": _bounded_text(
            raw.get("current_state", ""), field="stav", max_chars=MAX_CAPSULE_FIELD_CHARS
        ),
        "next_step": _bounded_text(
            raw.get("next_step", ""), field="další krok", max_chars=MAX_CAPSULE_FIELD_CHARS
        ),
        "constraints": clean_constraints,
        "revision": old_revision + 1,
        "updated_at": utc_now(),
    }


def turn_text_with_context_capsule(
    user_text: str,
    capsule: dict[str, Any] | None,
) -> tuple[str, int]:
    capsule = capsule or {}
    context = {
        "objective": str(capsule.get("objective") or "").strip(),
        "current_state": str(capsule.get("current_state") or "").strip(),
        "next_step": str(capsule.get("next_step") or "").strip(),
        "constraints": [
            str(item).strip()
            for item in capsule.get("constraints", [])
            if str(item).strip()
        ]
        if isinstance(capsule.get("constraints"), list)
        else [],
    }
    if not any((context["objective"], context["current_state"], context["next_step"], context["constraints"])):
        return user_text, 0
    revision = max(1, int(capsule.get("revision") or 0))
    envelope = {
        "application_context": {
            "type": "samantha_context_capsule",
            "revision": revision,
            **context,
        },
        "user_message": user_text,
    }
    prefix = (
        "Následující JSON obsahuje aktuální aplikační Context Capsule a vlastní zprávu uživatele. "
        "Odpověz na user_message. Capsule je autoritativní pro údaje, které výslovně uvádí; "
        "při rozporu s dřívější historií použij aktuální capsule.\n"
    )
    return prefix + json.dumps(envelope, ensure_ascii=False, separators=(",", ":")), revision


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
        self._version_cache: dict[str, Any] | None = None
        self._lock = threading.RLock()
        self._state = self._load_state()
        self._state["connection_state"] = "disconnected"
        self._state["connection_id"] = ""
        self._state["process_pid"] = 0

    def _load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return empty_lab_state()
        try:
            loaded = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return empty_lab_state()
        if not isinstance(loaded, dict):
            return empty_lab_state()
        return self._normalize_state(loaded)

    @staticmethod
    def _normalize_thread_record(raw: dict[str, Any], *, fallback_label: str) -> dict[str, Any]:
        messages = raw.get("messages")
        clean_messages = messages[-MAX_LAB_MESSAGES:] if isinstance(messages, list) else []
        events = raw.get("lifecycle_events")
        clean_events = events[-MAX_LIFECYCLE_EVENTS:] if isinstance(events, list) else []
        capsule_raw = raw.get("capsule")
        capsule = empty_context_capsule()
        if isinstance(capsule_raw, dict):
            for key in capsule:
                if key in capsule_raw:
                    capsule[key] = capsule_raw[key]
            capsule["constraints"] = (
                list(capsule.get("constraints") or [])[:MAX_CAPSULE_CONSTRAINTS]
                if isinstance(capsule.get("constraints"), list)
                else []
            )
        created_at = str(raw.get("created_at") or "")
        updated_at = str(raw.get("updated_at") or created_at)
        completed_count = sum(
            1 for item in clean_messages if isinstance(item, dict) and item.get("status") == "completed"
        )
        return {
            "registry_id": str(raw.get("registry_id") or uuid.uuid4().hex),
            "thread_id": str(raw.get("thread_id") or ""),
            "label": str(raw.get("label") or fallback_label)[:MAX_THREAD_LABEL_CHARS],
            "role": str(raw.get("role") or "read-only LAB")[:MAX_THREAD_ROLE_CHARS],
            "created_at": created_at,
            "updated_at": updated_at,
            "last_resumed_at": str(raw.get("last_resumed_at") or ""),
            "last_turn_id": str(raw.get("last_turn_id") or ""),
            "last_turn_completed_at": str(raw.get("last_turn_completed_at") or ""),
            "turn_count": int(raw.get("turn_count") or completed_count),
            "capsule": capsule,
            "lifecycle_events": clean_events,
            "messages": clean_messages,
        }

    def _normalize_state(self, loaded: dict[str, Any]) -> dict[str, Any]:
        state = empty_lab_state()
        for key in ("updated_at", "connection_generation"):
            state[key] = loaded.get(key, state[key])

        raw_threads = loaded.get("threads")
        if int(loaded.get("schema_version") or 0) >= LAB_STATE_SCHEMA_VERSION and isinstance(raw_threads, list):
            state["threads"] = [
                self._normalize_thread_record(item, fallback_label=f"LAB relace {index}")
                for index, item in enumerate(raw_threads, start=1)
                if isinstance(item, dict) and str(item.get("thread_id") or "")
            ]
            requested_active = str(loaded.get("active_registry_id") or "")
            registry_ids = {item["registry_id"] for item in state["threads"]}
            state["active_registry_id"] = (
                requested_active
                if requested_active in registry_ids
                else (state["threads"][0]["registry_id"] if state["threads"] else "")
            )
            return state

        # Nedestruktivní převod původního single-thread stavu na registr v2.
        legacy_thread_id = str(loaded.get("thread_id") or "")
        if legacy_thread_id:
            record = self._normalize_thread_record(
                {
                    "thread_id": legacy_thread_id,
                    "label": "Původní LAB relace",
                    "role": "read-only LAB",
                    "created_at": loaded.get("created_at", ""),
                    "updated_at": loaded.get("updated_at", ""),
                    "messages": loaded.get("messages", []),
                    "lifecycle_events": loaded.get("lifecycle_events", []),
                },
                fallback_label="Původní LAB relace",
            )
            state["threads"] = [record]
            state["active_registry_id"] = record["registry_id"]
        return state

    def _save(self) -> None:
        self._state["updated_at"] = utc_now()
        atomic_write_json(self.state_path, self._state, ensure_ascii=False, indent=2)

    def _threads(self) -> list[dict[str, Any]]:
        return self._state["threads"]

    def _thread_by_registry_id(self, registry_id: str) -> dict[str, Any] | None:
        expected = str(registry_id or "").strip()
        for item in self._threads():
            if item.get("registry_id") == expected:
                return item
        return None

    def _active_thread(self, *, required: bool = False) -> dict[str, Any] | None:
        thread = self._thread_by_registry_id(str(self._state.get("active_registry_id") or ""))
        if required and thread is None:
            raise AppServerError("LAB ještě nemá vybraný testovací thread.")
        return thread

    @staticmethod
    def _thread_summary(thread: dict[str, Any]) -> dict[str, Any]:
        return {
            key: thread.get(key)
            for key in (
                "registry_id",
                "thread_id",
                "label",
                "role",
                "created_at",
                "updated_at",
                "last_resumed_at",
                "last_turn_id",
                "last_turn_completed_at",
                "turn_count",
                "capsule",
            )
        }

    def _version_payload(self) -> dict[str, Any]:
        if self._version_cache is not None:
            return dict(self._version_cache)
        try:
            version = self.version_getter(self.codex_binary)
        except AppServerError as exc:
            return {"ok": False, "raw": "", "message": str(exc)}
        payload = {
            "ok": True,
            "raw": version.raw,
            "major": version.major,
            "minor": version.minor,
            "patch": version.patch,
        }
        self._version_cache = payload
        return dict(payload)

    def status(self) -> dict[str, Any]:
        with self._lock:
            connected = bool(self._client and self._client.running)
            self._state["connection_state"] = "connected" if connected else "disconnected"
            active = self._active_thread()
            thread_id = str((active or {}).get("thread_id") or "")
            return {
                "ok": True,
                "lab": True,
                "read_only": True,
                "connection_state": self._state["connection_state"],
                "schema_version": LAB_STATE_SCHEMA_VERSION,
                "active_registry_id": str(self._state.get("active_registry_id") or ""),
                "thread_id": thread_id,
                "thread_ready": bool(thread_id),
                "active_thread": self._thread_summary(active) if active else None,
                "threads": [self._thread_summary(item) for item in self._threads()],
                "connection_generation": int(self._state.get("connection_generation") or 0),
                "connection_id": str(self._state.get("connection_id") or ""),
                "process_pid": int(self._state.get("process_pid") or 0),
                "lifecycle_events": list((active or {}).get("lifecycle_events") or []),
                "created_at": str((active or {}).get("created_at") or ""),
                "updated_at": str(self._state.get("updated_at") or ""),
                "messages": list((active or {}).get("messages") or []),
                "version": self._version_payload(),
                "message": (
                    "LAB je připojený k vybranému read-only app-server threadu."
                    if connected
                    else "LAB není připojený. Vybraný thread lze obnovit nebo založit nový."
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
        active = self._active_thread(required=True)
        assert active is not None
        current = self._connection_evidence()
        event = {
            "event_id": uuid.uuid4().hex,
            "action": action,
            "started_at": started_at,
            "completed_at": utc_now(),
            "ok": bool(ok),
            "registry_id": str(active.get("registry_id") or ""),
            "thread_id": str(active.get("thread_id") or ""),
            "previous_generation": int(previous.get("generation") or 0),
            "connection_generation": int(current.get("generation") or 0),
            "previous_connection_id": str(previous.get("connection_id") or ""),
            "connection_id": str(current.get("connection_id") or ""),
            "previous_process_pid": int(previous.get("process_pid") or 0),
            "process_pid": int(current.get("process_pid") or 0),
        }
        events = list(active.get("lifecycle_events") or [])
        events.append(event)
        active["lifecycle_events"] = events[-MAX_LIFECYCLE_EVENTS:]
        active["updated_at"] = event["completed_at"]

    def new_thread(
        self,
        *,
        label: str = "",
        role: str = "read-only LAB",
        capsule: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            if len(self._threads()) >= MAX_REGISTERED_THREADS:
                raise AppServerError(
                    f"LAB registr už obsahuje maximum {MAX_REGISTERED_THREADS} relací."
                )
            clean_label = _bounded_text(
                label, field="název relace", max_chars=MAX_THREAD_LABEL_CHARS
            ) or f"LAB relace {len(self._threads()) + 1}"
            clean_role = _bounded_text(
                role, field="role relace", max_chars=MAX_THREAD_ROLE_CHARS
            ) or "read-only LAB"
            clean_capsule = (
                normalize_context_capsule(capsule) if capsule else empty_context_capsule()
            )
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
            now = utc_now()
            record = self._normalize_thread_record(
                {
                    "registry_id": uuid.uuid4().hex,
                    "thread_id": thread_id,
                    "label": clean_label,
                    "role": clean_role,
                    "capsule": clean_capsule,
                    "created_at": now,
                    "updated_at": now,
                    "last_resumed_at": now,
                    "messages": [],
                    "lifecycle_events": [],
                },
                fallback_label=clean_label,
            )
            self._threads().append(record)
            self._state["active_registry_id"] = record["registry_id"]
            self._activate_client(client)
            self._append_lifecycle_event(action="thread_created", started_at=started_at, previous=previous)
            self._save()
            return self.status()

    def _connect_existing(self, *, action: str, registry_id: str = "") -> None:
        previous_registry_id = str(self._state.get("active_registry_id") or "")
        if registry_id:
            selected = self._thread_by_registry_id(registry_id)
            if selected is None:
                raise AppServerError("Vybraná LAB relace v soukromém registru neexistuje.")
            self._state["active_registry_id"] = selected["registry_id"]
        active = self._active_thread(required=True)
        assert active is not None
        thread_id = str(active.get("thread_id") or "")
        if not thread_id:
            raise AppServerError("Vybraná LAB relace nemá app-server thread ID.")
        started_at = utc_now()
        previous = self._connection_evidence()
        self._close_client()
        client = self.client_factory(codex_binary=self.codex_binary)
        try:
            client.resume_thread(
                # threadId je podle lokálního schématu 0.144.1 preferovaná identita pro resume.
                thread_id,
                cwd=self.project_root,
                developer_instructions=LAB_DEVELOPER_INSTRUCTIONS,
            )
        except Exception:
            client.close()
            self._state["active_registry_id"] = previous_registry_id
            raise
        self._activate_client(client)
        active["last_resumed_at"] = utc_now()
        self._append_lifecycle_event(action=action, started_at=started_at, previous=previous)
        self._save()

    def resume(self, *, registry_id: str = "") -> dict[str, Any]:
        with self._lock:
            self._connect_existing(action="thread_resumed", registry_id=registry_id)
            return self.status()

    def select_thread(self, *, registry_id: str) -> dict[str, Any]:
        with self._lock:
            selected = self._thread_by_registry_id(registry_id)
            if selected is None:
                raise AppServerError("Vybraná LAB relace v soukromém registru neexistuje.")
            if (
                selected.get("registry_id") == self._state.get("active_registry_id")
                and self._client is not None
                and self._client.running
            ):
                return self.status()
            self._connect_existing(action="thread_selected", registry_id=registry_id)
            result = self.status()
            result["message"] = "Vybraná LAB relace byla obnovena přes své app-server thread ID."
            return result

    def update_capsule(self, *, registry_id: str, capsule: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            thread = self._thread_by_registry_id(registry_id)
            if thread is None:
                raise AppServerError("Vybraná LAB relace v soukromém registru neexistuje.")
            thread["capsule"] = normalize_context_capsule(
                capsule, previous=thread.get("capsule") if isinstance(thread.get("capsule"), dict) else None
            )
            thread["updated_at"] = utc_now()
            self._save()
            result = self.status()
            result["message"] = (
                "Context Capsule byla uložena do private dat a připojí se k příštímu LAB turnu."
            )
            return result

    def disconnect(self) -> dict[str, Any]:
        with self._lock:
            started_at = utc_now()
            previous = self._connection_evidence()
            self._close_client()
            if self._active_thread() is not None:
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
        for thread in self._threads():
            for message in thread.get("messages") or []:
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
            active = self._active_thread(required=True)
            assert active is not None
            model_text, capsule_revision = turn_text_with_context_capsule(
                clean_text,
                active.get("capsule") if isinstance(active.get("capsule"), dict) else None,
            )

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
                "registry_id": str(active.get("registry_id") or ""),
                "thread_id": str(active.get("thread_id") or ""),
                "turn_id": "",
                "duration_ms": 0,
                "capsule_attached": capsule_revision > 0,
                "capsule_revision_sent": capsule_revision,
            }
            messages = list(active.get("messages") or [])
            messages.append(entry)
            active["messages"] = messages[-MAX_LAB_MESSAGES:]
            active["updated_at"] = entry["cockpit_received_at"]
            self._save()
            try:
                assert self._client is not None
                receipt: TurnReceipt = self._client.send_text(
                    thread_id=entry["thread_id"],
                    text=model_text,
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
            active["last_turn_id"] = receipt.turn_id
            active["last_turn_completed_at"] = receipt.completed_at
            active["turn_count"] = int(active.get("turn_count") or 0) + 1
            active["updated_at"] = receipt.completed_at
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
