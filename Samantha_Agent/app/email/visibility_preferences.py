"""Reversible Cockpit filtering of already assessed, unimportant email only."""
from __future__ import annotations

import hashlib

from app.file_persistence import exclusive_file_lock
from .continuous_agent import _importance_sender, _now, _similar_importance_subject, importance_subject_key


def hidden_low_importance(item: dict, preferences: dict) -> bool:
    # Important cards, failed assessments and missing verdicts always remain visible.
    if item.get("status") != "hourly_summary" or item.get("proposal", {}).get("important") is not False:
        return False
    try:
        sender = _importance_sender(item["header"]["sender"])
    except (ValueError, KeyError):
        return False
    subject = importance_subject_key(item["header"]["subject"])
    return any(p["active"] and p["account"] == item["account"] and p["sender"] == sender
               and _similar_importance_subject(p["subject_key"], subject) for p in preferences.values())


class EmailVisibilityPreferences:
    def __init__(self, worker):
        self.worker = worker

    def remember(self, item_id: str) -> str:
        with exclusive_file_lock(self.worker.root / "worker", timeout=0):
            result = []
            def update(document):
                item = document["items"][item_id]
                if item["status"] != "hourly_summary" or item.get("proposal", {}).get("important") is not False:
                    raise ValueError("Nezobrazování lze nastavit jen z posouzené nedůležité zprávy.")
                sender = _importance_sender(item["header"]["sender"])
                subject = item["header"]["subject"]
                key = importance_subject_key(subject)
                if not any(c.isalpha() for c in key):
                    raise ValueError("Předmět neposkytuje dostatečný vzor pro budoucí zprávy.")
                identity = (item["account"], sender, key)
                preference_id = hashlib.sha256(repr(identity).encode()).hexdigest()
                preferences = document.setdefault("visibility_preferences", {})
                old = preferences.get(preference_id, {})
                preferences[preference_id] = {
                    "account": item["account"], "sender": sender, "subject": subject,
                    "subject_key": key, "active": True,
                    "created_at": old.get("created_at", _now()), "updated_at": _now(),
                }
                result.append(preference_id)
            self.worker._update(update)
            return result[0]

    def forget(self, preference_id: str) -> None:
        with exclusive_file_lock(self.worker.root / "worker", timeout=0):
            self.worker._update(lambda d: d["visibility_preferences"][preference_id].update(
                active=False, updated_at=_now()))
