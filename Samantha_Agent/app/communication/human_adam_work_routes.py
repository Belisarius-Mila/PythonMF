"""Scoped HA-04 HTTP adapters. No caller-selected roots, workers or model policy."""
from __future__ import annotations

from app.codex_appserver import AppServerError
from app.communication.session_hub import SessionBusyError, SessionDeliveryUnknownError
from app.communication.human_adam_work import WorkConflict, WorkError, WorkUnavailable
from app.communication.human_adam_workstream_catalog import WORKSTREAM_CATALOG_BY_ID
from app.file_persistence import FilePersistenceError
from app.work_repository import WorkRepositoryError


def _scope(workstream_id):
    if not isinstance(workstream_id, str) or workstream_id not in WORKSTREAM_CATALOG_BY_ID:
        raise WorkError("Vyber známý projekt práce.")
    return workstream_id


def _call(callback):
    try:
        return callback()
    except WorkUnavailable:
        return {"ok": False, "error": "unavailable", "message": "Uloženou práci nelze ověřit; původní identita zůstává zachovaná."}
    except (SessionBusyError, WorkConflict):
        return {"ok": False, "error": "conflict", "message": "Práce nebo její rozsah se změnily. Ověř původní stav."}
    except SessionDeliveryUnknownError:
        return {"ok": False, "error": "unverified", "message": "Původní práce vyžaduje ověření; zadání znovu neposílej."}
    except (AppServerError, ValueError, TypeError):
        return {"ok": False, "error": "invalid_request", "message": "Práci nelze potvrdit. Zkontroluj projekt a původní identitu."}
    except (OSError, FilePersistenceError, WorkRepositoryError):
        return {"ok": False, "error": "unavailable", "message": "Úložiště práce není dostupné. Ověř původní požadavek bez opakování."}


def work_start_action(payload, *, service, observed_code_stamp=""):
    def start():
        allowed = {"message", "client_message_id", "client_sent_at", "workstream_id", "write_intent", "confirmed"}
        if not isinstance(payload, dict) or set(payload) - allowed or payload.get("confirmed") is not True:
            raise WorkError("Práce vyžaduje potvrzené přesné zadání.")
        return service.submit_work(wait=False, expected_workstream_id=_scope(payload.get("workstream_id")),
                                   text=payload.get("message"), client_message_id=payload.get("client_message_id"),
                                   client_sent_at=payload.get("client_sent_at", ""),
                                   write_intent=payload.get("write_intent", False), observed_code_stamp=observed_code_stamp)
    return _call(start)


def work_read_action(query, *, service):
    def read():
        if not isinstance(query, dict) or set(query) - {"workstream_id", "operation_id", "client_message_id", "cursor"}:
            raise WorkError("Neplatný dotaz na práci.")
        cursor = query.get("cursor", "0")
        if not isinstance(cursor, str) or not cursor.isascii() or not cursor.isdigit() or len(cursor) > 16:
            raise WorkError("Neplatný cursor.")
        return service.work_controller.view(_scope(query.get("workstream_id")),
            identity=query.get("operation_id", ""), client_message_id=query.get("client_message_id", ""), cursor=int(cursor))
    return _call(read)


def work_recover_action(payload, *, service):
    def recover():
        if (not isinstance(payload, dict) or set(payload) != {"workstream_id", "operation_id", "confirmed"}
                or payload["confirmed"] is not True):
            raise WorkError("Obnova vyžaduje přesnou potvrzenou identitu.")
        return service.work_controller.recover(_scope(payload["workstream_id"]), payload["operation_id"])
    return _call(recover)


def work_steer_action(payload, *, service):
    def steer():
        if (not isinstance(payload, dict)
                or set(payload) != {"workstream_id", "operation_id", "command_id", "expectedTurnId", "text", "confirmed"}
                or payload["confirmed"] is not True):
            raise WorkError("Doplnění vyžaduje přesný potvrzený text a původní identitu.")
        return service.work_controller.steer(_scope(payload["workstream_id"]),
            {key: payload[key] for key in ("operation_id", "command_id", "expectedTurnId", "text")})
    return _call(steer)


def work_command_read_action(query, *, service):
    def read():
        if not isinstance(query, dict) or set(query) != {"workstream_id", "operation_id", "command_id"}:
            raise WorkError("Vyber přesnou účtenku doplnění.")
        return service.work_controller.read_command(_scope(query["workstream_id"]), query["operation_id"], query["command_id"])
    return _call(read)


def work_http_status(result, *, accepting=False):
    if result.get("ok"):
        return 202 if accepting else 200
    return {"conflict": 409, "unverified": 409, "unavailable": 503}.get(result.get("error"), 400)
