"""Private manual follow-up actions; automatic monitoring is not connected yet."""
from app.email.followups import EmailFollowups, FollowupError
from app.file_persistence import FilePersistenceError
from app.work_repository import WorkRepositoryError


def _call(callback):
    try:
        return callback()
    except FollowupError as exc:
        return {"ok": False, "error": exc.code, "message": str(exc)}
    except (OSError, FilePersistenceError, WorkRepositoryError):
        return {"ok": False, "error": "unavailable",
                "message": "Stav hlídání nelze potvrdit. Ověř stejnou záležitost a původní operaci."}


def email_followups_overview(query=None, *, service=None):
    return _call(lambda: (service or EmailFollowups()).overview(query))


def email_followups_action(payload, *, service=None):
    return _call(lambda: (service or EmailFollowups()).execute(payload))


def email_followups_http_status(result):
    return 200 if result.get("ok") else {
        "conflict": 409, "not_found": 404, "unavailable": 503,
    }.get(result.get("error"), 400)
