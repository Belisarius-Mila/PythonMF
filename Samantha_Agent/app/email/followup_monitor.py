"""Opt-in, deterministic follow-up observations inside the existing mail worker.

No model, send, notification channel, mailbox scan or service activation here.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.work_repository import RepositoryMutation, WorkRepositoryError
from .followup_matching import binding_candidates, trusted_evidence
from .followups import _space, _record, _instant

PRAGUE = ZoneInfo("Europe/Prague")
VERSION = 1
FRESHNESS = timedelta(minutes=75)
SOURCE_KEYS = ("account", "provider", "folder", "uidvalidity", "uid", "content_digest")


def configuration(document):
    space = _space(document)
    value = space.get("monitor", {"version": VERSION, "enabled": False})
    if (not isinstance(value, dict) or value.get("version") != VERSION
            or type(value.get("enabled")) is not bool):
        raise WorkRepositoryError("Neznámá konfigurace hlídání.")
    return value


def next_slot(instant: datetime) -> datetime:
    local = instant.astimezone(PRAGUE)
    rounded = local.replace(minute=0, second=0, microsecond=0)
    if local != rounded:
        rounded += timedelta(hours=1)
    if rounded.hour < 7:
        rounded = rounded.replace(hour=7)
    elif rounded.hour > 22:
        rounded = (rounded + timedelta(days=1)).replace(hour=7)
    return rounded.astimezone(timezone.utc)


def runtime_view(document, now, health=None):
    config = configuration(document)
    last = config.get("last_run_at", "")
    try:
        recent = timedelta(0) <= now - _instant(last) <= FRESHNESS
    except ValueError:
        recent = False
    health = health or {}
    try:
        recent = (recent and health.get("followup_monitor_version") == VERSION
                  and health.get("status") in {"completed", "already_completed", "incomplete"}
                  and timedelta(0) <= now - _instant(health.get("finished_at", "")) <= FRESHNESS)
    except ValueError:
        recent = False
    return {"version": VERSION, "configured": config["enabled"],
            "worker_recent": bool(config["enabled"] and recent), "last_run_at": last,
            "status": config.get("last_run_status", "not_connected")}


def _bump(value, action, changes, at, identity):
    value["revision"] += 1
    value["updated_at"] = at
    value["history"].append({"action": action, "operation_id": "monitor-" + identity,
        "at": at, "revision": value["revision"], "generation": value["generation"],
        "changes": copy.deepcopy(changes)})


def bind_cached(document, value):
    item = document["items"].get(value["source"]["item_id"], {})
    evidence = trusted_evidence(item)
    if not evidence or any(item.get(k) != value["source"].get(k) for k in SOURCE_KEYS):
        return False
    value["source"]["thread_binding"] = "verified_headers"
    observations = value.setdefault("observations", {"message_ids": [], "items": {}, "reviews": {}})
    if evidence["message_id"] not in observations["message_ids"]:
        observations["message_ids"].append(evidence["message_id"])
    return True


def admit_observation(document, item_id, *, at):
    """Called in the same transaction as admission, before model/UID advance."""
    if not configuration(document)["enabled"]:
        return
    space = _space(document)
    account = document["items"][item_id]["account"]
    scoped = [_record(space, key) for key in space["items"]
              if space["items"][key].get("source", {}).get("account") == account]
    active = [v for v in scoped if v["state"] == "active"]
    for value in active:
        was_bound = value["source"].get("thread_binding") == "verified_headers"
        if bind_cached(document, value) and not was_bound:
            _bump(value, "source_verified", {"thread_binding": "verified_headers"}, at,
                  hashlib.sha256((value["id"] + value["source"]["content_digest"]).encode()).hexdigest())
    identities, decision = binding_candidates(document, item_id, scoped)
    for identity in identities:
        value = _record(space, identity)
        observations = value.setdefault("observations", {"message_ids": [], "items": {}, "reviews": {}})
        bucket = observations["items"] if decision == "linked" else observations["reviews"]
        if item_id in observations["items"] or item_id in observations["reviews"]:
            continue
        evidence = trusted_evidence(document["items"][item_id])
        event = {"item_id": item_id, "generation": value["generation"], "observed_at": at,
                 "decision": decision, "content_digest": document["items"][item_id]["content_digest"],
                 "source": {k: document["items"][item_id][k] for k in SOURCE_KEYS}}
        bucket[item_id] = event
        if decision == "linked":
            observations["message_ids"].append(evidence["message_id"])
        observations["latest_item_id"] = item_id
        observations["latest_decision"] = decision
        # A fact survives a later failed/uncertain model assessment. No manual
        # field, lifecycle or check_at is changed by this observation.
        _bump(value, "related_message" if decision == "linked" else "binding_review",
              {"item_id": item_id, "decision": decision}, at,
              hashlib.sha256((identity + str(value["generation"]) + item_id).encode()).hexdigest())


class EmailFollowupMonitor:
    def __init__(self, worker):
        self.worker = worker

    def check(self, *, now, unavailable_reason="", allowed_accounts=None):
        if now.tzinfo is None:
            raise ValueError("Čas kontroly musí obsahovat pásmo.")
        now = now.astimezone(timezone.utc)
        local = now.astimezone(PRAGUE)
        snapshot = self.worker.status()
        if not configuration(snapshot)["enabled"]:
            return {"status": "not_connected", "checked": 0}
        if not 7 <= local.hour <= 22:
            return {"status": "outside_hours", "checked": 0}
        slot = local.replace(minute=0, second=0, microsecond=0).isoformat()
        def mutate(document):
            config = configuration(document)
            if not config["enabled"]:
                return RepositoryMutation(document, {"status": "not_connected", "checked": 0}, changed=False)
            space = _space(document)
            checked, changed = 0, False
            for identity in space["items"]:
                value = _record(space, identity)
                if value["state"] != "active":
                    continue
                was_bound = value["source"].get("thread_binding") == "verified_headers"
                bound = bind_cached(document, value)
                account = value["source"]["account"]
                source = document["sources"].get(account, {})
                proof = source.get("followup_scan", {})
                try:
                    verified_at = _instant(proof.get("verified_at", ""))
                    as_of = _instant(proof.get("as_of", ""))
                    fresh = timedelta(0) <= now - as_of <= FRESHNESS and as_of <= verified_at <= now
                except ValueError:
                    verified_at, as_of, fresh = None, None, False
                complete = (not unavailable_reason and bound and source.get("health") == "ok"
                    and proof.get("status") == "complete" and proof.get("uidvalidity") == value["source"]["uidvalidity"]
                    and fresh and (allowed_accounts is None or account in allowed_accounts))
                due = _instant(value["check_at"]) <= now
                observations = value.get("observations", {})
                current_items = [key for key, event in observations.get("items", {}).items()
                                 if event["generation"] == value["generation"]]
                current_reviews = [key for key, event in observations.get("reviews", {}).items()
                                   if event["generation"] == value["generation"]]
                if not bound:
                    kind = "source_binding_unverified"
                elif current_reviews:
                    kind = "binding_review"
                elif not complete or due and as_of < _instant(value["check_at"]):
                    kind = "source_unverified"
                elif current_items:
                    kind = "related_message"
                elif due:
                    kind = "due_no_observed_reply"
                else:
                    kind = "waiting"
                reason = unavailable_reason or ("source_incomplete_or_stale" if not complete else "")
                # At most one current Cockpit notice. Same situation retains its
                # identity across hourly retries, crashes and generic cache trim.
                notice_id = hashlib.sha256(json.dumps([identity, value["generation"], value["check_at"],
                    observations.get("latest_item_id", "")]).encode()).hexdigest()
                key = hashlib.sha256(json.dumps([slot, kind, reason, proof, value["generation"],
                    value["check_at"], observations.get("latest_item_id", "")], sort_keys=True).encode()).hexdigest()
                previous = value.get("tracking", {})
                if key == previous.get("check_key") and (was_bound or not bound):
                    continue
                last_verified = previous.get("last_verified_at", "")
                if complete:
                    last_verified = proof["verified_at"]
                tracking = {"version": VERSION, "check_key": key, "last_checked_at": now.isoformat(),
                    "last_verified_at": last_verified, "status": kind, "reason": reason,
                    "next_check_slot": next_slot(max(now + timedelta(microseconds=1), _instant(value["check_at"]))).isoformat(),
                    "notice": {"id": notice_id, "kind": kind, "item_ids": current_items,
                               "review_item_ids": current_reviews}}
                value["tracking"] = tracking
                _bump(value, "monitor_check", {"status": kind, "notice_id": notice_id}, now.isoformat(), key)
                checked += 1; changed = True
            if config.get("last_slot") != slot or checked:
                config.update(last_slot=slot, last_run_at=now.isoformat(),
                              last_run_status="source_unverified" if unavailable_reason else "checked")
                changed = True
            return RepositoryMutation(document, {"status": "checked", "checked": checked}, changed=changed)
        return self.worker.repository.transact(mutate).result
