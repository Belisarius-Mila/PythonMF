from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.email.action_case_models import ReminderDraft
from app.email.action_case_service import reminder_draft_to_dict
from app.email.redaction import EMAIL_PATTERN
from app.file_persistence import atomic_write_json, update_json_file


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REMINDERS_PATH = PROJECT_ROOT / "data" / "reminders" / "reminders.json"
URL_PATTERN = re.compile(r"https?://", re.IGNORECASE)


@dataclass(frozen=True)
class ReminderSaveResult:
    reminder_id: str
    created: bool
    message: str
    path: Path


class _ReminderTransactionSkipped(RuntimeError):
    def __init__(self, result: Any):
        super().__init__("Reminder transaction skipped.")
        self.result = result


ReminderStore = dict[str, list[dict[str, Any]]]
ReminderStoreUpdater = Callable[[ReminderStore], tuple[bool, Any]]


def save_reminder_draft(
    reminder: ReminderDraft | Mapping[str, Any],
    path: Path = DEFAULT_REMINDERS_PATH,
) -> ReminderSaveResult:
    reminder_dict = _safe_reminder_dict(reminder)
    reminder_id = _require_string(reminder_dict, "id")
    def save_if_missing(store: ReminderStore) -> tuple[bool, ReminderSaveResult]:
        reminders = store["reminders"]
        if any(existing.get("id") == reminder_id for existing in reminders):
            return False, ReminderSaveResult(
                reminder_id=reminder_id,
                created=False,
                message="Ukol uz v reminders JSON existuje; duplicita nebyla pridana.",
                path=path,
            )
        reminders.append(reminder_dict)
        return True, ReminderSaveResult(
            reminder_id=reminder_id,
            created=True,
            message="Ukol byl ulozen do reminders JSON.",
            path=path,
        )

    return transact_reminders_store(save_if_missing, path=path)


def load_reminders_store(path: Path = DEFAULT_REMINDERS_PATH) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        return {"reminders": []}

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    return _normalize_reminders_store(data)


def transact_reminders_store(
    updater: ReminderStoreUpdater,
    *,
    path: Path = DEFAULT_REMINDERS_PATH,
) -> Any:
    result: Any = None

    def apply_update(current: Any) -> ReminderStore:
        nonlocal result
        store = _normalize_reminders_store(current)
        changed, result = updater(store)
        if not changed:
            raise _ReminderTransactionSkipped(result)
        return store

    try:
        update_json_file(path, apply_update, default={"reminders": []})
    except _ReminderTransactionSkipped as skipped:
        return skipped.result
    return result


def patch_reminder_record(
    reminder_id: str,
    changes: Mapping[str, Any],
    *,
    path: Path = DEFAULT_REMINDERS_PATH,
) -> bool:
    patch = dict(changes)
    _validate_safe_value(patch)

    def patch_matching(store: ReminderStore) -> tuple[bool, bool]:
        reminder = next((item for item in store["reminders"] if item.get("id") == reminder_id), None)
        if reminder is None:
            return False, False
        if all(reminder.get(key) == value for key, value in patch.items()):
            return False, True
        reminder.update(patch)
        return True, True

    return bool(transact_reminders_store(patch_matching, path=path))


def cancel_reminder_record(
    reminder_id: str,
    *,
    reason: str,
    resolved_at: str,
    evidence: Mapping[str, Any],
    path: Path = DEFAULT_REMINDERS_PATH,
) -> bool:
    return patch_reminder_record(
        reminder_id,
        {
            "status": "cancelled",
            "resolution": {
                "status": "cancelled",
                "reason": reason,
                "resolved_at": resolved_at,
                "resolved_by": "samantha_cockpit",
            },
            "evidence": dict(evidence),
        },
        path=path,
    )


def enrich_reminder_record(
    reminder_id: str,
    *,
    related_asset: str = "",
    amount_due: str = "",
    amount_note: str = "",
    document_ref: str = "",
    due_date_type: str = "",
    path: Path = DEFAULT_REMINDERS_PATH,
) -> bool:
    changes = {"document_ref": document_ref, "due_date_type": due_date_type}
    if related_asset:
        changes["related_asset"] = related_asset
    if amount_due:
        changes["amount_due"] = amount_due
        changes["amount_note"] = amount_note
    return patch_reminder_record(reminder_id, changes, path=path)


def write_reminders_store(
    store: dict[str, list[dict[str, Any]]],
    path: Path = DEFAULT_REMINDERS_PATH,
) -> None:
    _write_reminders_store(path=path, store=store)


def _write_reminders_store(
    path: Path,
    store: dict[str, list[dict[str, Any]]],
) -> None:
    atomic_write_json(path, _normalize_reminders_store(store))


def _normalize_reminders_store(data: Any) -> ReminderStore:
    if not isinstance(data, dict):
        raise ValueError("Reminders JSON musi byt objekt.")

    reminders = data.get("reminders")
    if reminders is None:
        reminders = []
    if not isinstance(reminders, list):
        raise ValueError("Pole reminders musi byt seznam.")
    if not all(isinstance(item, dict) for item in reminders):
        raise ValueError("Kazda pripominka musi byt JSON objekt.")
    return {"reminders": reminders}


def _safe_reminder_dict(reminder: ReminderDraft | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(reminder, ReminderDraft):
        reminder_dict = reminder_draft_to_dict(reminder)
    else:
        reminder_dict = dict(reminder)

    _validate_required_fields(reminder_dict)
    _validate_safe_value(reminder_dict)
    return reminder_dict


def _validate_required_fields(reminder: Mapping[str, Any]) -> None:
    for field in ("id", "title", "notes", "due_date", "priority", "status", "source"):
        _require_key(reminder, field)

    source = reminder["source"]
    if not isinstance(source, Mapping):
        raise ValueError("source musi byt JSON objekt.")
    for field in ("type", "uid", "date", "sender"):
        _require_key(source, field)


def _require_key(data: Mapping[str, Any], key: str) -> None:
    if key not in data:
        raise ValueError(f"Chybi povinne pole: {key}")


def _require_string(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Pole {key} musi byt neprazdny string.")
    return value


def _validate_safe_value(value: Any) -> None:
    if isinstance(value, str):
        if URL_PATTERN.search(value):
            raise ValueError("Reminder nesmi obsahovat plne URL.")
        if EMAIL_PATTERN.search(value):
            raise ValueError("Reminder nesmi obsahovat neredigovanou e-mailovou adresu.")
        return

    if isinstance(value, Mapping):
        for nested in value.values():
            _validate_safe_value(nested)
        return

    if isinstance(value, list | tuple):
        for nested in value:
            _validate_safe_value(nested)
        return

    if value is None or isinstance(value, int | float | bool):
        return

    raise ValueError(f"Nepodporovana hodnota v reminderu: {type(value).__name__}")
