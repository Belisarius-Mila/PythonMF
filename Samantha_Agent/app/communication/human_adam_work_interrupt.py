"""One durable cancellation request per original turn; reads never resend it."""
from __future__ import annotations

import copy
import threading
from datetime import datetime

from app.codex_appserver import AppServerRpcError, AppServerSteerRejected, utc_now
from app.communication.human_adam_work import ID, WorkConflict, WorkError, WorkUnavailable, TERMINAL
from app.work_repository import RepositoryMutation

REASONS = {"", "work_not_running", "scope_changed", "turn_changed", "owner_unavailable",
           "connection_unavailable", "server_rejected", "delivery_unknown"}


class WorkInterrupts:
    def __init__(self, controller):
        self.controller = controller
        self._lock = threading.RLock()
        self._inflight = set()

    def _request(self, value):
        request = value.get("_interrupt_request")
        if request is None:
            if value.get("_interrupt_requested"):
                raise WorkUnavailable("Původní účtenka zastavení chybí; požadavek neopakuji.")
            return None
        try:
            if (request["command_id"] != "ha07-" + value["operation_id"]
                    or request["state"] not in {"pending", "accepted", "rejected", "unverified"}
                    or request["reason"] not in REASONS or not value.get("_interrupt_requested")
                    or not isinstance(request["expected_turn_id"], str) or not 1 <= len(request["expected_turn_id"]) <= 256
                    or not all(32 < ord(c) < 127 for c in request["expected_turn_id"])
                    or not isinstance(request["owner_generation"], str)):
                raise ValueError()
            datetime.fromisoformat(request["created_at"]); datetime.fromisoformat(request["updated_at"])
        except (KeyError, TypeError, ValueError):
            raise WorkUnavailable("Účtenku zastavení nelze ověřit; požadavek neopakuji.") from None
        return request

    def blocked(self, value):
        request = self._request(value)
        return bool(request and request["state"] != "rejected")

    def public(self, value, *, lifecycle_state=None):
        with self._lock:
            request = self._request(value)
            if request is None:
                return None
            result = {key: copy.deepcopy(request[key]) for key in
                      ("command_id", "expected_turn_id", "state", "reason", "created_at", "updated_at")}
            if result["state"] == "pending" and (request["owner_generation"] != self.controller.owner
                                                     or value["operation_id"] not in self._inflight):
                result.update(state="unverified", reason="delivery_unknown")
            # An ACK means only that cancellation was requested. The original
            # canonical turn, not the cancellation RPC, proves its outcome.
            state = lifecycle_state or value["lifecycle_state"]
            result["outcome"] = state if state in TERMINAL else "unverified" if state == "unverified" else "waiting"
            return result

    def submit(self, workstream_id, payload):
        if (not isinstance(payload, dict) or set(payload) != {"operation_id", "command_id", "expectedTurnId"}
                or not isinstance(payload["operation_id"], str) or not ID.fullmatch(payload["operation_id"])
                or payload["command_id"] != "ha07-" + payload["operation_id"]
                or not isinstance(payload["expectedTurnId"], str) or not 1 <= len(payload["expectedTurnId"]) <= 256
                or not all(32 < ord(c) < 127 for c in payload["expectedTurnId"])):
            raise WorkError("Zastavení vyžaduje přesnou původní práci a tah.")
        controller = self.controller
        identity, expected = payload["operation_id"], payload["expectedTurnId"]
        value = controller.store.load(identity)
        if value is None or value["scope"]["workstream_id"] != workstream_id:
            raise WorkConflict("Zastavení patří jinému projektu.")
        if value["turn_id"] != expected:
            raise WorkConflict("Zastavení neodpovídá původnímu tahu.")
        existing = self._request(value)
        if existing:
            if existing["expected_turn_id"] != expected:
                raise WorkConflict("Identita zastavení už patří jinému tahu.")
            return {**controller.view(workstream_id, identity=identity), "duplicate_prevented": True,
                    "dispatch_performed": False}
        reason = ""
        try:
            controller._command_target(value, expected, interrupt=True)
        except AppServerSteerRejected as exc:
            if exc.reason == "scope_changed":
                raise WorkConflict("Původní rozsah zastavení není aktivní.") from None
            reason = exc.reason
        now = utc_now()
        def reserve(document):
            current = controller.store.load(identity)
            old = self._request(current)
            if old:
                if old["expected_turn_id"] != expected:
                    raise WorkConflict("Zastavení patří jinému tahu.")
                return RepositoryMutation(current, {"dispatch":False,"new":False}, changed=False)
            rejection = reason
            if current["lifecycle_state"] != "running":
                rejection = "work_not_running"
            elif current["turn_id"] != expected:
                rejection = "turn_changed"
            current["_interrupt_requested"] = True
            current["_interrupt_request"] = {"command_id": payload["command_id"], "expected_turn_id": expected,
                "owner_generation": controller.owner, "state": "rejected" if rejection else "pending",
                "reason": rejection, "created_at": now, "updated_at": now}
            self._event(current, "interrupt_requested")
            return RepositoryMutation(current, {"dispatch":not bool(rejection),"new":True})
        with self._lock:
            admission = controller.store.repository(identity).transact(reserve).result
            dispatch = admission["dispatch"]
            if dispatch:
                self._inflight.add(identity)
        if not dispatch:
            return {**controller.view(workstream_id, identity=identity), "dispatch_performed": False,
                    "duplicate_prevented":not admission["new"], "read_only":not admission["new"],"writes_performed":admission["new"]}
        state, reason, dispatched = "unverified", "delivery_unknown", True
        try:
            current = controller.store.load(identity)
            observer = controller._command_target(current, expected, interrupt=True)
            result = observer.interrupt(expected)
            if result == {"turn_id": expected, "request_accepted": True}:
                state, reason = "accepted", ""
        except AppServerSteerRejected as exc:
            state, reason, dispatched = "rejected", exc.reason, False
        except AppServerRpcError:
            state, reason = "rejected", "server_rejected"
        except Exception:
            pass
        finally:
            # Even BaseException leaves a non-replayable original receipt.
            with self._lock:
                self._inflight.discard(identity)
        def finish(document):
            current = controller.store.load(identity)
            request = self._request(current)
            if not request or request["owner_generation"] != controller.owner or request["state"] != "pending":
                raise WorkUnavailable("Původní účtenka zastavení se změnila.")
            request.update(state=state, reason=reason, updated_at=utc_now())
            self._event(current, "interrupt_receipt")
            return RepositoryMutation(current, {})
        controller.store.repository(identity).transact(finish)
        return {**controller.view(workstream_id, identity=identity), "dispatch_performed": dispatched,
                "read_only": False, "writes_performed": True}

    @staticmethod
    def _event(value, kind):
        value["revision"] += 1
        value["updated_at"] = utc_now()
        value["events"].append({"cursor": value["revision"], "kind": kind, "at": value["updated_at"]})
        value["events"] = value["events"][-128:]
