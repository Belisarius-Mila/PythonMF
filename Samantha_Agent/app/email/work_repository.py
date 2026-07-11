"""Transactional repository adapter for Cockpit email work decisions."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from app.work_repository import JsonWorkRepository, RepositoryMutation, RepositoryResult, WorkRepositoryError


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
        )

    return repository.transact(update, operation_id=operation_id)
