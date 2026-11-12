"""Durable admission and bounded read projections; never replay a model request."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from app.codex_appserver import AppServerError, AppServerSteerRejected, utc_now
from app.file_persistence import exclusive_file_lock, FileLockTimeoutError
from app.work_repository import JsonWorkRepository, RepositoryMutation, WorkRepositoryError
from app.communication.session_hub import SessionBusyError, SessionDeliveryUnknownError
from app.communication.human_adam_public_progress import public_projection

ID = re.compile(r"[a-f0-9]{32}\Z")
CLIENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{7,127}\Z")
PROJECT = re.compile(r"[a-z][a-z0-9_-]{1,63}\Z")
TERMINAL = frozenset({"completed", "failed", "not_dispatched"})
STATES = TERMINAL | {"accepted", "running", "awaiting_completion", "unverified"}
MAX_EVENTS, MAX_RECENT = 128, 64
MAX_WORKERS, MAX_RESPONSE_CACHE = 8, 2


class WorkError(AppServerError):
    """Printable errors contain no request or protocol contents."""


class WorkConflict(WorkError):
    pass


class WorkUnavailable(WorkError):
    pass


def operation_id(workstream_id: str, client_message_id: str) -> str:
    if not PROJECT.fullmatch(workstream_id) or not CLIENT.fullmatch(client_message_id):
        raise WorkError("Práce nemá platný projekt nebo identitu požadavku.")
    return hashlib.sha256((workstream_id + "\0" + client_message_id).encode()).hexdigest()[:32]


def normalized_request(payload: dict) -> dict:
    allowed = {"text", "client_message_id", "client_sent_at", "write_intent", "observed_code_stamp"}
    if not isinstance(payload, dict) or set(payload) - allowed:
        raise WorkError("Požadavek práce obsahuje nepovolené údaje.")
    text, client = payload.get("text"), payload.get("client_message_id")
    if not isinstance(text, str) or not text.strip() or len(text) > 12000:
        raise WorkError("Doplň zprávu o nejvýše 12000 znacích.")
    if not isinstance(client, str) or not CLIENT.fullmatch(client):
        raise WorkError("Požadavek nemá platnou identitu.")
    if "write_intent" in payload and type(payload["write_intent"]) is not bool:
        raise WorkError("Oprávnění požadavku není platné.")
    for key, maximum in (("client_sent_at", 64), ("observed_code_stamp", 128)):
        if not isinstance(payload.get(key, ""), str) or len(payload.get(key, "")) > maximum:
            raise WorkError("Metadata požadavku nejsou platná.")
    return {"text": text.strip(), "client_message_id": client,
            "client_sent_at": payload.get("client_sent_at", ""),
            "write_intent": payload.get("write_intent", False),
            "observed_code_stamp": payload.get("observed_code_stamp", "")}


def fingerprint(payload: dict) -> str:
    # Server build metadata may change during a later readback. It never grants
    # permission to execute the already accepted request a second time.
    semantic = {k: v for k, v in payload.items() if k != "observed_code_stamp"}
    return hashlib.sha256(json.dumps(semantic, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class WorkStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.index = JsonWorkRepository(self.root / "recent.json")

    def repository(self, identity: str) -> JsonWorkRepository:
        if not isinstance(identity, str) or not ID.fullmatch(identity):
            raise WorkError("Neplatná identita práce.")
        return JsonWorkRepository(self.root / "operations" / (identity + ".json"))

    def load(self, identity: str) -> dict | None:
        value = self.repository(identity).read()
        if not value:
            return None
        if (value.get("schema_version") != 1 or value.get("operation_id") != identity
                or value.get("lifecycle_state") not in STATES
                or type(value.get("revision")) is not int or value["revision"] < 1
                or not isinstance(value.get("events"), list)
                or not isinstance(value.get("scope"), dict)):
            raise WorkUnavailable("Uložený stav práce nelze ověřit.")
        scope = value["scope"]
        try:
            if operation_id(scope.get("workstream_id", ""), value.get("client_request_id", "")) != identity:
                raise ValueError()
            if (set(scope) != {"workstream_id", "profile_id", "thread_id", "connection_generation"}
                    or type(scope["connection_generation"]) is not int or scope["connection_generation"] < 0
                    or not PROJECT.fullmatch(scope["profile_id"])
                    or not isinstance(scope["thread_id"], str) or not 1 <= len(scope["thread_id"]) <= 256
                    or not all(32 < ord(c) < 127 for c in scope["thread_id"])
                    or value["thread_id"] != scope["thread_id"] or value["kind"] != "model_turn"
                    or value["delivery_state"] not in {"not_started", "pending", "confirmed", "unknown"}
                    or not re.fullmatch(r"[a-f0-9]{64}", value["request_digest"])
                    or not isinstance(value["completion"], dict)
                    or type(value["event_gap"]) is not bool
                    or type(value.get("_commands_journal", False)) is not bool
                    or value["failure_code"] not in {"", "execution_unverified", "preflight_failed", "owner_unavailable",
                                                     "stopped_before_dispatch", "completion_source_unavailable"}
                    or len(value["events"]) > MAX_EVENTS):
                raise ValueError()
            datetime.fromisoformat(value["created_at"]); datetime.fromisoformat(value["updated_at"])
            previous = 0
            for event in value["events"]:
                if (type(event["cursor"]) is not int or not previous < event["cursor"] <= value["revision"]
                        or not re.fullmatch(r"[a-z][a-z_]{1,63}", event["kind"])):
                    raise ValueError()
                datetime.fromisoformat(event["at"]); previous = event["cursor"]
        except (KeyError, TypeError, ValueError, WorkError) as exc:
            raise WorkUnavailable("Uložená identita nebo metadata práce nesouhlasí.") from exc
        return value

    def recent(self, workstream_id: str) -> list[dict]:
        if not isinstance(workstream_id, str) or not PROJECT.fullmatch(workstream_id):
            raise WorkError("Neplatný projekt práce.")
        index = self.index.read()
        if not index:
            return []
        if (index.get("schema_version") != 1 or not isinstance(index.get("ids"), list)
                or len(index["ids"]) > MAX_RECENT or any(not isinstance(k, str) or not ID.fullmatch(k) for k in index["ids"])):
            raise WorkUnavailable("Přehled práce nelze ověřit.")
        values = [self.load(identity) for identity in index["ids"]]
        if any(value is None for value in values):
            raise WorkUnavailable("V přehledu chybí doklad práce.")
        return [v for v in values if v["scope"]["workstream_id"] == workstream_id]

    def admit(self, payload: dict, scope: dict, owner: str, *, session_path: Path) -> tuple[dict, bool]:
        if (set(scope) != {"workstream_id", "profile_id", "thread_id", "connection_generation"}
                or not isinstance(scope["thread_id"], str) or not 1 <= len(scope["thread_id"]) <= 256
                or type(scope["connection_generation"]) is not int or scope["connection_generation"] < 0):
            raise WorkError("Rozsah práce není platný.")
        identity = operation_id(scope["workstream_id"], payload["client_message_id"])
        digest = fingerprint(payload)
        with exclusive_file_lock(self.root / "admission"):
            old = self.load(identity)
            if old:
                if old["request_digest"] != digest:
                    raise WorkConflict("Stejná identita již patří jinému zadání nebo oprávnění.")
                return old, False
            recent = self.recent(scope["workstream_id"])
            if any(v["lifecycle_state"] not in TERMINAL for v in recent):
                raise SessionDeliveryUnknownError("Projekt má nedokončenou práci. Nejdřív ověř původní požadavek.")
            now = utc_now()
            record = {"schema_version": 1, "operation_id": identity,
                      "client_request_id": payload["client_message_id"], "request_digest": digest,
                      "scope": copy.deepcopy(scope), "owner_generation": owner,
                      "thread_id": scope["thread_id"], "turn_id": "", "kind": "model_turn",
                      "lifecycle_state": "accepted", "delivery_state": "not_started",
                      "created_at": now, "updated_at": now, "revision": 1,
                      "events": [{"cursor": 1, "kind": "accepted", "at": now}],
                      "event_gap": False, "gap_cursor": 0, "wire_cursor": 0, "wire_generation": "",
                      "completion": {}, "failure_code": "", "_accepted_input": payload["text"],
                      "_dispatch_started": False,
                      "_session_path": str(Path(session_path).resolve())}
            self.repository(identity).transact(lambda doc: RepositoryMutation(record, {}))
            def update_index(index):
                ids = list(index.get("ids", []))
                if index and (index.get("schema_version") != 1 or not isinstance(index.get("ids"), list)):
                    raise WorkError("Přehled práce nelze aktualizovat.")
                ids.append(identity)
                # Drop only terminal entries from this small navigation index.
                # Their durable identity files remain to prevent later replay.
                while len(ids) > MAX_RECENT:
                    removable = next((i for i, key in enumerate(ids[:-1])
                                      if (self.load(key) or {}).get("lifecycle_state") in TERMINAL), None)
                    if removable is None:
                        raise WorkError("Přehled je plný neověřených prací; nejdřív je vyřeš.")
                    key = ids.pop(removable)
                    def compact(old):
                        if old.get("lifecycle_state") in TERMINAL:
                            old.pop("_accepted_input", None)
                            old.pop("public_progress", None)
                            old["events"] = old["events"][-1:]
                        return RepositoryMutation(old, {})
                    self.repository(key).transact(compact)
                return RepositoryMutation({"schema_version": 1, "ids": ids}, {})
            self.index.transact(update_index)
            return record, True

    def change(self, identity: str, owner: str, kind: str, *, fields: dict | None = None,
               wire: tuple[str, int] | None = None, recover: bool = False, with_effect: bool = False):
        def mutate(value):
            current = self.load(identity)
            if current is None:
                raise WorkError("Práce nebyla nalezena.")
            if current["lifecycle_state"] in TERMINAL:
                return RepositoryMutation(current, current, changed=False)
            if not recover and current["owner_generation"] != owner:
                raise WorkConflict("Událost patří jiné generaci serveru.")
            if wire:
                generation, cursor = wire
                if (current["wire_generation"] and current["wire_generation"] != generation
                        or cursor <= current["wire_cursor"]):
                    return RepositoryMutation(current, current, changed=False)
                current.update(wire_generation=generation, wire_cursor=cursor)
            current.update(copy.deepcopy(fields or {}))
            current["revision"] += 1
            if kind == "event_gap":
                current["gap_cursor"] = current["revision"]
            current["updated_at"] = utc_now()
            current["events"].append({"cursor": current["revision"], "kind": kind,
                                      "at": current["updated_at"]})
            current["events"] = current["events"][-MAX_EVENTS:]
            if current["lifecycle_state"] in TERMINAL and current["delivery_state"] == "confirmed":
                current.pop("_accepted_input", None)  # Original remains in the canonical conversation.
            return RepositoryMutation(current, copy.deepcopy(current))
        result = self.repository(identity).transact(mutate)
        return (result.result, result.changed) if with_effect else result.result

    @staticmethod
    def public(value: dict, *, cursor: int = 0, owned: bool = False) -> dict:
        if type(cursor) is not int or cursor < 0:
            raise WorkError("Neplatný cursor práce.")
        keys = ("schema_version", "operation_id", "client_request_id", "scope", "thread_id", "turn_id",
                "kind", "lifecycle_state", "delivery_state", "created_at", "updated_at", "revision",
                "completion", "failure_code", "event_gap")
        view = {k: copy.deepcopy(value[k]) for k in keys}
        view["completion"] = {key: value["completion"][key] for key in ("kind", "job_id", "state") if key in value["completion"]}
        progress = public_projection(value.get("public_progress"))
        if progress is not None:
            view["public_progress"] = progress
        if value["lifecycle_state"] not in TERMINAL and not owned:
            view["lifecycle_state"] = "unverified"
        first = value["events"][0]["cursor"] if value["events"] else value["revision"]
        resync = bool(cursor and (cursor < first - 1 or cursor > value["revision"]))
        gap = value["event_gap"] and cursor < value.get("gap_cursor", value["revision"])
        view.update(cursor=value["revision"], resync_required=resync or gap,
                    events=[] if resync else [{key: e[key] for key in ("cursor", "kind", "at")}
                                              for e in value["events"] if e["cursor"] > cursor],
                    read_only=True, writes_performed=False,
                    capabilities={"steer": False, "interrupt": False, "replay": False})
        return view


@dataclass
class WorkReservation:
    scope: dict
    session_path: Path
    execute: Callable[[Any], dict]
    release: Callable[[], None]


class _Handle:
    def __init__(self):
        self.finished = threading.Event()
        self.response: dict | None = None
        self.error: BaseException | None = None
        self.thread: threading.Thread | None = None
        self.observer = None
        self.scope = None


class WorkController:
    def __init__(self, root: Path, *, completion_reader: Callable[[dict], dict | None] | None = None,
                 command_scope_guard: Callable[[dict], bool] | None = None):
        self.store = WorkStore(root)
        self.owner = uuid.uuid4().hex
        self.completion_reader = completion_reader or (lambda _: None)
        self._lock = threading.RLock()
        self._handles: dict[str, _Handle] = {}
        self._closing = threading.Event()
        self._command_scope_guard = command_scope_guard
        from app.communication.human_adam_work_commands import WorkCommands
        self.commands = WorkCommands(self.store.root / "commands", self.owner, resolve=self._resolve_command,
            before_dispatch=self._mark_command_dispatch, journal_required=lambda identity:
                (self.store.load(identity) or {}).get("_commands_journal") is True)

    def _command_parent(self, workstream_id, identity):
        value = self.store.load(identity)
        if value is None or value["scope"]["workstream_id"] != workstream_id:
            raise AppServerSteerRejected("scope_changed")
        return value

    def _command_target(self, value, expected_turn_id, *, check_scope=True):
        if check_scope:
            try:
                valid = callable(self._command_scope_guard) and self._command_scope_guard(value) is True
            except Exception:
                valid = False
            if not valid:
                raise AppServerSteerRejected("scope_changed")
        with self._lock:
            handle = self._handles.get(value["operation_id"])
            if (not self._owned(value["operation_id"]) or value["owner_generation"] != self.owner
                    or not handle or value["scope"] != handle.scope):
                raise AppServerSteerRejected("owner_unavailable")
            if value["lifecycle_state"] != "running":
                raise AppServerSteerRejected("work_not_running")
            if not expected_turn_id or value["turn_id"] != expected_turn_id:
                raise AppServerSteerRejected("turn_changed")
            observer = handle.observer
        if observer is None or not observer.can_steer(expected_turn_id):
            raise AppServerSteerRejected("work_not_running")
        return observer

    def _resolve_command(self, request):
        def perform():
            value = self._command_parent(request["workstream_id"], request["operation_id"])
            observer = self._command_target(value, request["expectedTurnId"])
            return observer.steer(expected_turn_id=request["expectedTurnId"], command_id=request["command_id"], text=request["text"])
        value = self._command_parent(request["workstream_id"], request["operation_id"])
        self._command_target(value, request["expectedTurnId"])
        return perform

    def _mark_command_dispatch(self, request):
        value = self._command_parent(request["workstream_id"], request["operation_id"])
        self._command_target(value, request["expectedTurnId"])
        record = self.store.change(value["operation_id"], self.owner, "command_dispatching", fields={"_commands_journal": True})
        if record.get("_commands_journal") is not True:
            raise AppServerSteerRejected("work_not_running")

    def steer(self, workstream_id, payload):
        from app.communication.human_adam_work_commands import normalize_command
        request = normalize_command(workstream_id, payload)
        try:
            self._command_parent(workstream_id, request["operation_id"])
        except AppServerSteerRejected as exc:
            return self.commands.rejected(request, exc.reason)
        return self.commands.submit(workstream_id, payload)

    def read_command(self, workstream_id, identity, command_id):
        self._command_parent(workstream_id, identity)
        return self.commands.read(workstream_id, identity, command_id)

    def _completion(self, record: dict) -> dict | None:
        value = self.completion_reader(record)
        if value is None:
            return None
        if (not isinstance(value, dict) or not all(isinstance(value.get(k), str) and 0 < len(value[k]) <= 128
                                                 for k in ("kind", "job_id", "state"))
                or value["state"] not in {"running", "queued", "retry_waiting", "completed", "failed"}
                or record["completion"].get("job_id") not in (None, value["job_id"])):
            raise WorkUnavailable("Dokončovací doklad nepatří původní práci.")
        return {key: value[key] for key in ("kind", "job_id", "state")}

    def view(self, workstream_id: str, *, identity: str = "", client_message_id: str = "", cursor: int = 0) -> dict:
        if identity and client_message_id:
            raise WorkError("Vyber jedinou identitu práce.")
        with self._lock:
            if client_message_id:
                identity = operation_id(workstream_id, client_message_id)
            values = [self.store.load(identity)] if identity else self.store.recent(workstream_id)
            if identity and values[0] is None:
                raise WorkError("Práce nebyla nalezena; absence není povolení znovu odeslat.")
            if any(v["scope"]["workstream_id"] != workstream_id for v in values):
                raise WorkConflict("Práce patří jinému projektu.")
            operations = []
            for value in values:
                public = self.store.public(value, cursor=cursor, owned=self._owned(value["operation_id"]))
                try:
                    self._command_target(value, value["turn_id"], check_scope=False)
                    public["capabilities"]["steer"] = not self.commands.blocked(workstream_id, value["operation_id"])
                except AppServerSteerRejected:
                    pass
                public["recent_commands"] = self.commands.recent(workstream_id, value["operation_id"])
                operations.append(public)
            return {"ok": True, "schema_version": 1, "read_only": True, "writes_performed": False,
                    "server_generation": self.owner,
                    "operations": operations}

    def _owned(self, identity: str) -> bool:
        handle = self._handles.get(identity)
        return bool(handle and handle.thread and handle.thread.is_alive() and not self._closing.is_set())

    @staticmethod
    def _existing_result(record: dict) -> dict:
        session = JsonWorkRepository(Path(record["_session_path"])).read()
        entry = next((e for e in session.get("messages", []) if e.get("client_message_id") == record["client_request_id"]
                      and e.get("thread_id") == record["thread_id"] and e.get("status") == "completed"
                      and e.get("delivery_confirmed") is True), None)
        if not entry:
            raise SessionDeliveryUnknownError("Původní výsledek není ověřený. Pokyn znovu neposílej.")
        return {"ok": True, "duplicate_prevented": True, "entry": entry, "session": session,
                "automatic_completion": {"state": "duplicate_prevented", "attempted": False}}

    def submit(self, workstream_id: str, payload: dict, reserve: Callable[[], WorkReservation], *, wait: bool = False) -> dict:
        payload = normalized_request(payload)
        identity = operation_id(workstream_id, payload["client_message_id"])
        duplicate = False
        with self._lock:
            if self._closing.is_set():
                raise WorkError("Server ukončuje práci; nový požadavek nebyl přijat.")
            dead = [key for key in self._handles if not self._owned(key)]
            for key in dead[:-MAX_RESPONSE_CACHE]:
                self._handles.pop(key, None)  # Responses are a bounded volatile compatibility cache.
            old = self.store.load(identity)
            if old:
                duplicate = True
                if old["request_digest"] != fingerprint(payload):
                    raise WorkConflict("Stejná identita již patří jinému zadání nebo oprávnění.")
                if (wait and identity in self._handles
                        and (self._owned(identity) or self._handles[identity].finished.is_set())):
                    handle = self._handles[identity]
                elif wait:
                    return self._existing_result(old)
                else:
                    return {**self.view(workstream_id, identity=identity), "accepted": True, "duplicate_prevented": True}
            else:
                if sum(self._owned(key) for key in self._handles) >= MAX_WORKERS:
                    raise SessionBusyError("Server čeká na dokončení přijatých prací; další worker nebyl spuštěn.")
                lease = exclusive_file_lock(self.store.root / "worker", timeout=0)
                try:
                    lease.__enter__()
                except FileLockTimeoutError as exc:
                    raise SessionBusyError("Server již provádí jinou práci.") from exc
                reservation = None
                handle = None
                try:
                    reservation = reserve()
                    if reservation.scope.get("workstream_id") != workstream_id or not reservation.scope.get("thread_id"):
                        raise WorkConflict("Projekt nebo vlákno se před přijetím změnily.")
                    record, created = self.store.admit(payload, reservation.scope, self.owner,
                                                       session_path=reservation.session_path)
                    if not created:
                        raise WorkConflict("Stejnou práci mezitím přijal jiný vlastník.")
                    handle = _Handle()
                    handle.scope = copy.deepcopy(reservation.scope)
                    self._handles[identity] = handle
                    handle.thread = threading.Thread(target=self._run, args=(identity, handle, reservation, lease),
                                                     name="human-adam-owned-work", daemon=True)
                    handle.thread.start()
                except BaseException as exc:
                    # An interruption after handing off to a native thread is
                    # uncertain. Keep ownership with that worker, never release
                    # its guards merely because the accepting caller vanished.
                    if handle is not None and (handle.thread.ident is not None or not isinstance(exc, Exception)):
                        raise
                    if handle is not None:
                        self._handles.pop(identity, None)
                        handle.error = exc
                        handle.finished.set()
                    if reservation is not None:
                        reservation.release()
                    lease.__exit__(None, None, None)
                    raise
        if wait:
            handle.finished.wait()
            if handle.error is not None:
                raise handle.error
            if handle.response is None:
                raise SessionDeliveryUnknownError("Výsledek původní práce nelze potvrdit.")
            if duplicate:
                return self._existing_result(self.store.load(identity))
            return copy.deepcopy(handle.response)
        return {**self.view(workstream_id, identity=identity), "accepted": True, "duplicate_prevented": False,
                "read_only": False, "writes_performed": True}

    def _run(self, identity: str, handle: _Handle, reservation: WorkReservation, lease) -> None:
        from app.communication.human_adam_work_observer import WorkObserver
        observer = WorkObserver(self.store, identity, self.owner)
        handle.observer = observer
        confirmed = False
        try:
            original = self.store.load(identity)
            self.store.change(identity, self.owner, "execution_started",
                              fields={"lifecycle_state": "running"})
            result = reservation.execute(observer)
            entry = result.get("entry") or {}
            delivered = (entry.get("status") == "completed" and entry.get("delivery_confirmed") is True)
            fields = {"lifecycle_state": "completed" if delivered else "unverified",
                      "delivery_state": "confirmed" if delivered else "unknown"}
            if delivered:
                record = original
                if (entry.get("thread_id") != record["thread_id"]
                        or entry.get("client_message_id") != record["client_request_id"]
                        or not entry.get("turn_id")):
                    raise WorkConflict("Výsledek patří jinému vláknu.")
                confirmed = True
                handle.response = result
                fields["turn_id"] = entry.get("turn_id", "")
                try:
                    completion = self._completion(record)
                except Exception:
                    completion = None
                    fields.update(lifecycle_state="unverified", failure_code="completion_source_unavailable")
                if completion:
                    fields["completion"] = completion
                    if completion["state"] not in {"completed", "failed"}:
                        fields["lifecycle_state"] = "awaiting_completion"
                    elif completion["state"] == "failed":
                        fields["lifecycle_state"] = "failed"
            self.store.change(identity, self.owner, "execution_finished", fields=fields)
            handle.response = result
        except BaseException as exc:
            if not confirmed:
                handle.error = exc
            try:
                current = self.store.load(identity)
                dispatched = bool(current and current.get("_dispatch_started"))
                self.store.change(identity, self.owner, "execution_unverified",
                                  fields={"lifecycle_state": "unverified" if confirmed or dispatched else "not_dispatched",
                                          "delivery_state": "confirmed" if confirmed else "unknown" if dispatched else "not_started",
                                          "failure_code": "execution_unverified" if dispatched else "preflight_failed"})
            except Exception:
                pass  # Original durable admission still blocks a second dispatch.
        finally:
            try:
                observer.close()
            finally:
                try:
                    reservation.release()
                finally:
                    lease.__exit__(None, None, None)
                    handle.finished.set()
        try:
            while not self._closing.is_set():
                record = self.store.load(identity)
                if record["lifecycle_state"] != "awaiting_completion":
                    break
                completion = self._completion(record)
                if completion and completion != record["completion"]:
                    state = {"completed": "completed", "failed": "failed"}.get(completion["state"], "awaiting_completion")
                    self.store.change(identity, self.owner, "completion_updated",
                                      fields={"completion": completion, "lifecycle_state": state})
                self._closing.wait(.2)
        except Exception:
            pass  # Missing source evidence never becomes a successful completion.

    def recover(self, workstream_id: str, identity: str) -> dict:
        with self._lock:
            record = self.store.load(identity)
            if record is None or record["scope"]["workstream_id"] != workstream_id:
                raise WorkError("Původní práce nebyla nalezena v tomto projektu.")
            if record["lifecycle_state"] in TERMINAL or self._owned(identity):
                return self.view(workstream_id, identity=identity)
            try:
                with exclusive_file_lock(self.store.root / "worker", timeout=0):
                    fields = {"lifecycle_state": "unverified", "failure_code": "owner_unavailable"}
                    if not record.get("_dispatch_started"):
                        # Durable dispatch barrier always precedes invocation.
                        fields.update(lifecycle_state="not_dispatched", delivery_state="not_started",
                                      failure_code="stopped_before_dispatch")
                    else:
                        session = JsonWorkRepository(Path(record["_session_path"])).read()
                        entry = next((e for e in session.get("messages", [])
                                      if e.get("client_message_id") == record["client_request_id"]
                                      and e.get("thread_id") == record["thread_id"]), None)
                        if (entry and entry.get("status") == "completed" and entry.get("delivery_confirmed") is True
                                and entry.get("turn_id")
                                and (not record["turn_id"] or record["turn_id"] == entry["turn_id"])):
                            fields.update(lifecycle_state="completed", delivery_state="confirmed",
                                          turn_id=entry.get("turn_id", ""), failure_code="")
                            completion = self._completion(record)
                            if record["completion"] and not completion:
                                fields["lifecycle_state"] = "unverified"
                            elif completion:
                                fields["completion"] = completion
                                fields["lifecycle_state"] = {"completed": "completed", "failed": "failed"}.get(
                                    completion["state"], "awaiting_completion")
                    _, changed = self.store.change(identity, self.owner, "recovered_existing_evidence",
                                                   fields=fields, recover=True, with_effect=True)
            except FileLockTimeoutError as exc:
                raise SessionBusyError("Původní worker ještě drží vlastnictví. Obnova nic znovu nespustila.") from exc
            return {**self.view(workstream_id, identity=identity), "read_only": not changed,
                    "writes_performed": changed,
                    "recovery": {"projection_updated": changed, "redispatched": False}}

    def close(self) -> None:
        self._closing.set()
        with self._lock:
            for handle in self._handles.values():
                handle.finished.set()  # Wake HTTP waiters; never cancel/restart the model.
