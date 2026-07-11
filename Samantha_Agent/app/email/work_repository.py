"""Transactional repository adapter for Cockpit email work decisions."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from app.work_repository import (
    JsonWorkRepository,
    OutboxEvent,
    RepositoryMutation,
    RepositoryResult,
    WorkRepositoryError,
)


EMAIL_WORK_DECISION_TOPIC = "email.work_decision.changed"


def read_email_work_decisions(path: Path) -> dict[str, dict[str, Any]]:
    try:
        document = JsonWorkRepository(path, default={"decisions": {}}).read()
    except WorkRepositoryError:
        return {}
    decisions = document.get("decisions", {})
    if not isinstance(decisions, dict):
        return {}
    return {
        str(key): copy.deepcopy(value)
        for key, value in decisions.items()
        if isinstance(value, dict)
    }


def save_email_work_decision(
    *,
    path: Path,
    item_id: str,
    action: str,
    item: Mapping[str, Any] | None = None,
    operation_id: str = "",
) -> RepositoryResult:
    repository = JsonWorkRepository(path, default={"decisions": {}})
    safe_item = copy.deepcopy(dict(item or {}))

    def update(document: dict[str, Any]) -> RepositoryMutation:
        raw_decisions = document.get("decisions", {})
        if not isinstance(raw_decisions, dict):
            raise WorkRepositoryError("Email decision repository has invalid decisions.")
        decisions = copy.deepcopy(raw_decisions)
        current = decisions.get(item_id)
        if action:
            if (
                isinstance(current, dict)
                and str(current.get("action", "")) == action
                and current.get("item", {}) == safe_item
            ):
                return RepositoryMutation(
                    document=document,
                    result={"item_id": item_id, "action": action},
                    changed=False,
                )
            decisions[item_id] = {
                "action": action,
                "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                "item": safe_item,
            }
        else:
            if item_id not in decisions:
                return RepositoryMutation(
                    document=document,
                    result={"item_id": item_id, "action": action},
                    changed=False,
                )
            decisions.pop(item_id)
        updated = dict(document)
        updated["decisions"] = decisions
        return RepositoryMutation(
            document=updated,
            result={"item_id": item_id, "action": action},
            outbox=(
                OutboxEvent(
                    topic=EMAIL_WORK_DECISION_TOPIC,
                    aggregate_id=_email_work_aggregate_ref(item_id),
                    payload={"action": action or "clear"},
                ),
            ),
        )

    return repository.transact(update, operation_id=operation_id)


def _email_work_aggregate_ref(item_id: str) -> str:
    digest = hashlib.sha256(f"email-work-decision|{item_id}".encode("utf-8")).hexdigest()[:20]
    return f"emailwork-{digest}"


def pending_email_purge_items(actions_path: Path) -> dict[str, Any]:
    pending: dict[str, dict[str, str]] = {}
    unrecoverable_ids: set[str] = set()
    unreadable_rows = 0
    if actions_path.exists():
        for line in actions_path.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                unreadable_rows += 1
                continue
            if not isinstance(record, dict):
                continue
            action = str(record.get("action", ""))
            raw_items = record.get("items", [])
            if not isinstance(raw_items, list):
                continue
            for raw_item in raw_items:
                if not isinstance(raw_item, dict):
                    continue
                item_id = _bounded_text(raw_item.get("item_id"), 160)
                if not item_id:
                    continue
                status = str(raw_item.get("status", ""))
                if action == "purge_email_work_queue_trash_batch" and status == "purged":
                    pending.pop(item_id, None)
                    unrecoverable_ids.discard(item_id)
                    continue
                if action != "process_email_work_queue_batch" or status != "trashed":
                    continue
                provider = _bounded_text(raw_item.get("provider"), 80)
                trash_uid = _bounded_text(raw_item.get("trash_uid"), 160)
                message_id = _bounded_text(raw_item.get("message_id"), 300)
                if not provider or (not trash_uid and not message_id):
                    unrecoverable_ids.add(item_id)
                    pending.pop(item_id, None)
                    continue
                pending[item_id] = {
                    "id": item_id,
                    "item_id": item_id,
                    "provider": provider,
                    "folder": _bounded_text(raw_item.get("folder"), 160),
                    "uid": _bounded_text(raw_item.get("uid"), 160),
                    "trash_folder": _bounded_text(raw_item.get("trash_folder"), 160),
                    "trash_uid": trash_uid,
                    "message_id": message_id,
                }
                unrecoverable_ids.discard(item_id)
    return {
        "ok": True,
        "items": list(pending.values()),
        "count": len(pending),
        "unrecoverable_count": len(unrecoverable_ids),
        "unreadable_rows": unreadable_rows,
    }


def _bounded_text(value: object, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]
