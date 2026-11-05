"""Cockpit actions for email cards, including explicitly confirmed replies."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

from app.email.continuous_agent import ContinuousEmailAgent, EmailProposal
from app.email.continuous_source import IMAPAgentSource
from app.email.agent_reply import AgentReplyService
from app.email.pushcut import PushcutNotifier, pushcut_status
from app.file_persistence import FilePersistenceError
from app.work_repository import WorkRepositoryError


def email_agent_overview(*, worker=None) -> dict:
    state = (worker or ContinuousEmailAgent()).status()
    cards, groups, archived = [], {}, []
    for item_id, item in state["items"].items():
        status = item["status"]
        reply = item.get("reply", {})
        pending_archived_reply = status == "archived" and item["proposal"].get("reply_draft") and reply.get("status") != "smtp_sent"
        if status in {"awaiting_confirmation", "saving"} or pending_archived_reply:
            public = {"id": item_id, **item}
            public["reply"] = {key: value for key, value in reply.items()
                               if key not in {"confirmation_token", "message_b64", "confirmation_digest"}}
            cards.append(public)
        elif status == "hourly_summary":
            hour = item["hour"]
            group = groups.setdefault(hour, {"hour": hour, "ids": [], "messages": []})
            group["ids"].append(item_id)
            group["messages"].append({"id": item_id, **item["header"]})
        if item.get("receipt"):
            archived.append({"id": item_id, "header": item.get("header", {}), "proposal": item["proposal"]})
    rows = []
    for hour, group in sorted(groups.items(), reverse=True):
        entries, messages = [], []
        for message in group["messages"]:
            try:
                date_text = parsedate_to_datetime(message["date"]).astimezone(ZoneInfo("Europe/Prague")).strftime("%d. %m. %H:%M")
            except (ValueError, TypeError, OverflowError):
                date_text = message["date"] or "čas neuveden"
            text = f"{date_text} {message['sender']} — {message['subject'] or '(bez předmětu)'}"
            entries.append(text)
            messages.append({"id": message["id"], "text": text})
        label = datetime.fromisoformat(hour).strftime("%d. %m. %Y, kontrola v %H:%M")
        rows.append({"hour": hour, "ids": group["ids"], "text": label + ": " + "; ".join(entries),
                     "messages": messages})
    counts = Counter(item["status"] for item in state["items"].values())
    preferences = [{"id": key, "sender": p["sender"], "subject": p["subject"]}
                   for key, p in state.get("importance_preferences", {}).items() if p["active"]]
    return {"ok": True, "cards": sorted(cards, key=lambda item: item["created_at"], reverse=True),
            "hours": rows, "archived": archived, "schedule": state.get("schedule", {}),
            "sources": list(state["sources"].values()), "importance_preferences": preferences,
            "assessment_errors": sum(counts[s] for s in ("analysis_failed", "analysis_interrupted", "analyzing")),
            "pushcut": pushcut_status(worker or ContinuousEmailAgent())}


def email_agent_pushcut_configure_action(payload: dict, *, notifier=None) -> dict:
    try:
        status = (notifier or PushcutNotifier()).configure(
            webhook_url=payload.get("webhook_url", ""), cockpit_url=payload.get("cockpit_url", ""),
            enabled=payload.get("enabled"))
        return {"ok": True, "pushcut": status}
    except Exception:
        return {"ok": False, "message": "Nastavení se nepodařilo uložit. Ověř adresu z Pushcutu a HTTPS odkaz na E-maily k řešení."}


def email_agent_pushcut_test_action(payload: dict, *, notifier=None) -> dict:
    try:
        outcome = (notifier or PushcutNotifier()).test(request_id=payload.get("request_id", ""),
                                                      confirmed=payload.get("confirmed") is True)
        return {"ok": True, **outcome}
    except Exception:
        return {"ok": False, "message": "Test se nepodařilo spustit. Nejdřív ulož nastavení; případný předchozí výsledek ověř na iPhonu."}


def email_agent_remember_importance_action(payload: dict, *, worker=None) -> dict:
    try:
        preference_id = (worker or ContinuousEmailAgent()).remember_low_importance(str(payload["id"]))
        return {"ok": True, "preference_id": preference_id}
    except (OSError, ValueError, KeyError, FilePersistenceError, WorkRepositoryError) as exc:
        return {"ok": False, "message": str(exc)}


def email_agent_forget_importance_action(payload: dict, *, worker=None) -> dict:
    try:
        (worker or ContinuousEmailAgent()).forget_importance_preference(str(payload["id"]))
        return {"ok": True}
    except (OSError, ValueError, KeyError, FilePersistenceError, WorkRepositoryError) as exc:
        return {"ok": False, "message": str(exc)}


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


def email_agent_prepare_reply_action(payload: dict, *, service=None) -> dict:
    try:
        prepared = (service or AgentReplyService()).prepare(str(payload["id"]), expected_digest=str(payload["expected_digest"]))
        return {"ok": True, "prepared": prepared}
    except ValueError as exc:
        return {"ok": False, "message": str(exc)}
    except Exception as exc:
        return {"ok": False, "message": "Odpověď se nepodařilo připravit. Ověř aktuální koncept a zdroj zprávy.",
                "error_type": type(exc).__name__}


def email_agent_send_reply_action(payload: dict, *, service=None) -> dict:
    try:
        receipt = (service or AgentReplyService()).send(
            str(payload["id"]), confirmation_token=str(payload.get("confirmation_token", "")),
            confirmation_digest=str(payload.get("confirmation_digest", "")), confirmed=payload.get("confirmed") is True)
        return {"ok": True, "receipt": receipt}
    except ValueError as exc:
        return {"ok": False, "message": str(exc)}
    except Exception as exc:
        return {"ok": False, "message": "Odeslání nebylo potvrzené. Neopakuj pokus, dokud nebude ověřený jeho stav.",
                "error_type": type(exc).__name__}
