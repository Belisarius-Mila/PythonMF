from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.email.action_case_models import ReminderDraft
from app.email.action_case_service import reminder_draft_to_dict
from app.email.redaction import EMAIL_PATTERN


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REMINDERS_PATH = PROJECT_ROOT / "data" / "reminders" / "reminders.json"
URL_PATTERN = re.compile(r"https?://", re.IGNORECASE)


@dataclass(frozen=True)
class ReminderSaveResult:
    reminder_id: str
    created: bool
    message: str
    path: Path


def save_reminder_draft(
    reminder: ReminderDraft | Mapping[str, Any],
    path: Path = DEFAULT_REMINDERS_PATH,
) -> ReminderSaveResult:
    reminder_dict = _safe_reminder_dict(reminder)
    reminder_id = _require_string(reminder_dict, "id")
    store = load_reminders_store(path)
    reminders = store["reminders"]

    if any(existing.get("id") == reminder_id for existing in reminders):
        return ReminderSaveResult(
            reminder_id=reminder_id,
            created=False,
            message="Ukol uz v reminders JSON existuje; duplicita nebyla pridana.",
            path=path,
        )

    reminders.append(reminder_dict)
    _write_reminders_store(path=path, store=store)
    return ReminderSaveResult(
        reminder_id=reminder_id,
        created=True,
        message="Ukol byl ulozen do reminders JSON.",
        path=path,
    )


def load_reminders_store(path: Path = DEFAULT_REMINDERS_PATH) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        return {"reminders": []}

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError("Reminders JSON musi byt objekt.")

    reminders = data.get("reminders")
    if reminders is None:
        data["reminders"] = []
        reminders = data["reminders"]
    if not isinstance(reminders, list):
        raise ValueError("Pole reminders musi byt seznam.")
    if not all(isinstance(item, dict) for item in reminders):
        raise ValueError("Kazda pripominka musi byt JSON objekt.")

    return {"reminders": reminders}


def write_reminders_store(
    store: dict[str, list[dict[str, Any]]],
    path: Path = DEFAULT_REMINDERS_PATH,
) -> None:
    _write_reminders_store(path=path, store=store)


def _write_reminders_store(
    path: Path,
    store: dict[str, list[dict[str, Any]]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(store, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


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
