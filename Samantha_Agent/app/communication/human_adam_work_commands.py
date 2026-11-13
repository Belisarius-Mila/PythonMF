"""HA-06 durable append receipts. No command replay, worker launch or turn/start."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import threading
from datetime import datetime
from pathlib import Path

from app.codex_appserver import AppServerRpcError, AppServerSteerRejected, utc_now
from app.communication.human_adam_work import WorkConflict, WorkError, WorkUnavailable, ID
from app.work_repository import JsonWorkRepository, RepositoryMutation

MAX_COMMANDS = 64
VISIBLE_COMMANDS = 16
STATES = {"pending", "accepted", "rejected", "unverified"}
REASONS = {"", "work_not_running", "scope_changed", "turn_changed", "owner_unavailable", "connection_unavailable",
           "previous_unverified", "command_limit", "command_identity_conflict", "invalid_request", "server_rejected",
           "delivery_unknown"}


def normalize_command(workstream_id, payload):
    if (not isinstance(payload, dict) or set(payload) != {"operation_id", "command_id", "expectedTurnId", "text"}
            or not isinstance(payload["operation_id"], str) or not ID.fullmatch(payload["operation_id"])
            or not isinstance(payload["command_id"], str)
            or not re.fullmatch(r"ha06-" + payload["operation_id"] + r"-[a-f0-9]{32}", payload["command_id"])
            or not isinstance(payload["expectedTurnId"], str) or not 1 <= len(payload["expectedTurnId"]) <= 256
            or not all(32 < ord(c) < 127 for c in payload["expectedTurnId"])
            or not isinstance(payload["text"], str) or not payload["text"].strip() or len(payload["text"]) > 4000):
        raise WorkError("Doplnění nemá platnou původní identitu, tah nebo text do 4000 znaků.")
    value = {**payload, "workstream_id": workstream_id, "text": payload["text"].strip()}
    value["request_digest"] = hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return value


class WorkCommands:
    def __init__(self, root: Path, owner: str, *, resolve, before_dispatch, journal_required):
        self.root, self.owner, self.resolve = Path(root), owner, resolve
        self.before_dispatch, self.journal_required = before_dispatch, journal_required
        self._live_lock = threading.RLock()
        self._inflight = set()

    def repository(self, identity):
        if not isinstance(identity, str) or not ID.fullmatch(identity):
            raise WorkError("Neplatná identita původní práce.")
        return JsonWorkRepository(self.root / (identity + ".json"))

    def _validate(self, value, workstream_id, identity):
        if not value:
            return {"schema_version": 1, "operation_id": identity, "workstream_id": workstream_id, "revision": 0, "commands": []}
        try:
            if (type(value["schema_version"]) is not int or value["schema_version"] != 1 or value["operation_id"] != identity or value["workstream_id"] != workstream_id
                    or type(value["revision"]) is not int or value["revision"] < 1
                    or not isinstance(value["commands"], list) or len(value["commands"]) > MAX_COMMANDS):
                raise ValueError()
            seen = set()
            for command in value["commands"]:
                if (command["command_id"] in seen or not re.fullmatch(r"ha06-" + identity + r"-[a-f0-9]{32}", command["command_id"])
                        or command["state"] not in STATES or command["reason"] not in REASONS
                        or not re.fullmatch(r"[a-f0-9]{64}", command["request_digest"])
                        or not isinstance(command["owner_generation"], str)
                        or not isinstance(command["expected_turn_id"], str) or not 1 <= len(command["expected_turn_id"]) <= 256
                        or not all(32 < ord(c) < 127 for c in command["expected_turn_id"])
                        or "text" in command and (not isinstance(command["text"], str) or not 0 < len(command["text"]) <= 4000)
                        or command["state"] in {"pending", "unverified"} and "text" not in command):
                    raise ValueError()
                datetime.fromisoformat(command["created_at"]); datetime.fromisoformat(command["updated_at"])
                if "text" in command and normalize_command(workstream_id, {"operation_id": identity,
                    "command_id": command["command_id"], "expectedTurnId": command["expected_turn_id"],
                    "text": command["text"]})["request_digest"] != command["request_digest"]:
                    raise ValueError()
                seen.add(command["command_id"])
        except (KeyError, TypeError, ValueError, WorkError):
            raise WorkUnavailable("Účtenky doplnění nelze ověřit; nic se znovu neodesílá.") from None
        return value

    def load(self, workstream_id, identity):
        value = self.repository(identity).read()
        if not value and self.journal_required(identity):
            raise WorkUnavailable("Původní journal doplnění chybí; novou identitu nevytvářím.")
        return self._validate(value, workstream_id, identity)

    def public(self, command):
        value = {key: copy.deepcopy(command[key]) for key in
                 ("command_id", "expected_turn_id", "state", "reason", "created_at", "updated_at")}
        if "text" in command:
            value["text"] = command["text"]
        if value["state"] == "pending" and (command["owner_generation"] != self.owner or command["command_id"] not in self._inflight):
            value.update(state="unverified", reason="owner_unavailable" if command["owner_generation"] != self.owner else "delivery_unknown")
        value["accepted_into_turn"] = value["state"] == "accepted"
        value["permission_scope"] = "original_turn"
        return value

    def recent(self, workstream_id, identity):
        with self._live_lock:
            doc = self.load(workstream_id, identity)
            return {"revision": doc["revision"], "commands": [self.public(c) for c in doc["commands"][-VISIBLE_COMMANDS:]]}

    def blocked(self, workstream_id, identity):
        return any(c["state"] in {"pending", "unverified"} for c in self.load(workstream_id, identity)["commands"])

    def read(self, workstream_id, identity, command_id):
        if not isinstance(command_id, str) or not re.fullmatch(r"ha06-" + identity + r"-[a-f0-9]{32}", command_id):
            raise WorkError("Neplatná identita doplnění.")
        with self._live_lock:
            doc = self.load(workstream_id, identity)
            command = next((c for c in doc["commands"] if c["command_id"] == command_id), None)
            return {"ok": True, "schema_version": 1, "read_only": True, "writes_performed": False,
                    "operation_id": identity, "workstream_id": workstream_id,
                    "command_revision": doc["revision"], "command": self.public(command) if command else None, "found": command is not None}

    @staticmethod
    def rejection(request, reason):
        now = utc_now()
        return {"command_id": request["command_id"], "expected_turn_id": request["expectedTurnId"],
                "state": "rejected", "reason": reason, "created_at": now, "updated_at": now,
                "text": request["text"], "accepted_into_turn": False, "permission_scope": "original_turn"}

    def rejected(self, request, reason):
        return {"ok": True, "schema_version": 1, "operation_id": request["operation_id"],
                "workstream_id": request["workstream_id"], "command": self.rejection(request, reason),
                "recorded": False, "dispatch_performed": False, "duplicate_prevented": False,
                "command_revision": 0, "read_only": True, "writes_performed": False}

    def submit(self, workstream_id, payload):
        request = normalize_command(workstream_id, payload)
        identity, command_id = request["operation_id"], request["command_id"]
        existing = next((c for c in self.load(workstream_id, identity)["commands"] if c["command_id"] == command_id), None)
        if existing:
            if existing["request_digest"] != request["request_digest"]:
                raise WorkConflict("Stejná identita doplnění už patří jinému textu nebo tahu.")
            return {**self.read(workstream_id, identity, command_id), "duplicate_prevented": True, "dispatch_performed": False}
        perform, rejection = None, ""
        try:
            perform = self.resolve(request)
        except AppServerSteerRejected as exc:
            rejection = exc.reason if exc.reason in REASONS else "work_not_running"
        now = utc_now()
        def admit(doc):
            doc = self._validate(doc, workstream_id, identity)
            old = next((c for c in doc["commands"] if c["command_id"] == command_id), None)
            if old:
                if old["request_digest"] != request["request_digest"]:
                    raise WorkConflict("Stejná identita doplnění už patří jinému textu nebo tahu.")
                return RepositoryMutation(doc, {"new": False}, changed=False)
            if len(doc["commands"]) >= MAX_COMMANDS:
                return RepositoryMutation(doc, {"new": False, "rejected": "command_limit"}, changed=False)
            reason = "previous_unverified" if any(c["state"] in {"pending", "unverified"} for c in doc["commands"]) else rejection
            command = {"command_id": command_id, "expected_turn_id": request["expectedTurnId"], "text": request["text"],
                       "request_digest": request["request_digest"], "owner_generation": self.owner,
                       "state": "rejected" if reason else "pending", "reason": reason,
                       "created_at": now, "updated_at": now}
            doc["commands"].append(command); doc["revision"] += 1
            # Keep compact identity/digest receipts for the whole parent work.
            for old in doc["commands"][:-VISIBLE_COMMANDS]:
                if old["state"] in {"accepted", "rejected"}:
                    old.pop("text", None)
            return RepositoryMutation(doc, {"new": True, "dispatch": not bool(reason)})
        with self._live_lock:
            result = self.repository(identity).transact(admit).result
            if result.get("dispatch"):
                self._inflight.add(command_id)
        if result.get("rejected"):
            return self.rejected(request, result["rejected"])
        if not result.get("dispatch"):
            return {**self.read(workstream_id, identity, command_id), "duplicate_prevented": not result["new"], "dispatch_performed": False,
                    "read_only": not result["new"], "writes_performed": result["new"]}
        # Durable pending is the dispatch barrier. Every uncertain exit keeps
        # that identity non-replayable, including process/HTTP termination.
        state, reason, dispatched = "unverified", "delivery_unknown", True
        try:
            self.before_dispatch(request)
            receipt = perform()
            if receipt == {"turn_id": request["expectedTurnId"], "command_id": command_id, "accepted_into_turn": True}:
                state, reason = "accepted", ""
        except AppServerSteerRejected as exc:
            state, reason = "rejected", exc.reason if exc.reason in REASONS else "work_not_running"
            dispatched = False
        except AppServerRpcError:
            state, reason = "rejected", "server_rejected"
        except Exception:
            pass  # Raw errors/payloads never enter a receipt, log or UI.
        except BaseException:
            with self._live_lock:
                self._inflight.discard(command_id)
            raise
        def finish(doc):
            doc = self._validate(doc, workstream_id, identity)
            current = next((c for c in doc["commands"] if c["command_id"] == command_id), None)
            if current is None:
                raise WorkUnavailable("Původní účtenka doplnění chybí; nic neopakuji.")
            if current["state"] != "pending" or current["owner_generation"] != self.owner:
                raise WorkConflict("Účtenka doplnění změnila vlastníka nebo stav.")
            current.update(state=state, reason=reason, updated_at=utc_now()); doc["revision"] += 1
            return RepositoryMutation(doc, {})
        with self._live_lock:
            try:
                self.repository(identity).transact(finish)
            finally:
                self._inflight.discard(command_id)
        return {**self.read(workstream_id, identity, command_id), "duplicate_prevented": False, "dispatch_performed": dispatched,
                "read_only": False, "writes_performed": True}
