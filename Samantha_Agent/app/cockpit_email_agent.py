"""Cockpit view/actions for model-assessed emails; no mailbox deletion or sending."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

from app.email.continuous_agent import ContinuousEmailAgent, EmailProposal
from app.email.continuous_source import IMAPAgentSource
from app.file_persistence import FilePersistenceError
from app.work_repository import WorkRepositoryError


def email_agent_overview(*, worker=None) -> dict:
    state = (worker or ContinuousEmailAgent()).status()
    cards, groups, archived = [], {}, []
    for item_id, item in state["items"].items():
        status = item["status"]
        if status in {"awaiting_confirmation", "saving"}:
            cards.append({"id": item_id, **item})
        elif status == "hourly_summary":
            hour = item["hour"]
            group = groups.setdefault(hour, {"hour": hour, "ids": [], "messages": []})
            group["ids"].append(item_id)
            group["messages"].append(item["header"])
        elif status == "archived":
            archived.append({"id": item_id, "header": item.get("header", {}), "proposal": item["proposal"]})
    rows = []
    for hour, group in sorted(groups.items(), reverse=True):
        entries = []
        for message in group["messages"]:
            try:
                date_text = parsedate_to_datetime(message["date"]).astimezone(ZoneInfo("Europe/Prague")).strftime("%d. %m. %H:%M")
            except (ValueError, TypeError, OverflowError):
                date_text = message["date"] or "čas neuveden"
            entries.append(f"{date_text} {message['sender']} — {message['subject'] or '(bez předmětu)'}")
        label = datetime.fromisoformat(hour).strftime("%d. %m. %Y, kontrola v %H:%M")
        rows.append({"hour": hour, "ids": group["ids"], "text": label + ": " + "; ".join(entries)})
    counts = Counter(item["status"] for item in state["items"].values())
    return {"ok": True, "cards": sorted(cards, key=lambda item: item["created_at"], reverse=True),
            "hours": rows, "archived": archived, "schedule": state.get("schedule", {}),
            "sources": list(state["sources"].values()),
            "assessment_errors": sum(counts[s] for s in ("analysis_failed", "analysis_interrupted", "analyzing"))}


def email_agent_dismiss_action(payload: dict, *, worker=None) -> dict:
    worker = worker or ContinuousEmailAgent()
    try:
        ids = payload.get("ids")
        if not isinstance(ids, list) or not all(isinstance(item, str) for item in ids):
            raise ValueError("Vyber položky k vyřazení.")
        worker.dismiss(ids, action=str(payload.get("action", "dismiss")))
        return {"ok": True}
    except (OSError, ValueError, KeyError, FilePersistenceError, WorkRepositoryError) as exc:
        return {"ok": False, "message": str(exc)}


def email_agent_edit_action(payload: dict, *, worker=None) -> dict:
    worker = worker or ContinuousEmailAgent()
    try:
        digest = worker.edit_proposal(str(payload["id"]), EmailProposal.model_validate(payload["proposal"]),
                                      expected_digest=str(payload["expected_digest"]))
        return {"ok": True, "proposal_digest": digest}
    except (OSError, ValueError, KeyError, FilePersistenceError, WorkRepositoryError) as exc:
        return {"ok": False, "message": str(exc)}


def email_agent_archive_action(payload: dict, *, worker=None, source_factory=IMAPAgentSource) -> dict:
    worker = worker or ContinuousEmailAgent()
    try:
        item_id = str(payload["id"])
        item = worker.status()["items"][item_id]
        if payload.get("confirmed") is not True or payload.get("proposal_digest") != item["proposal_digest"]:
            raise ValueError("Nejdřív potvrď aktuální návrh uložení.")
        source = source_factory(item["provider"], item["folder"])
        observed = source.read_item(item)
        return {"ok": True, "receipt": worker.accept_archive(observed, confirmed_digest=item["proposal_digest"])}
    except Exception as exc:
        # No transport details, credentials or message content in the public error.
        return {"ok": False, "message": "Uložení se nepodařilo ověřit. Karta zůstává k řešení.",
                "error_type": type(exc).__name__}
