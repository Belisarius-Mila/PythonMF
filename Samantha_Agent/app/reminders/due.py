from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from app.email.redaction import EMAIL_PATTERN

from .store import DEFAULT_REMINDERS_PATH, URL_PATTERN, load_reminders_store


DUE_SOON_DAYS = 14
FULL_URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)


@dataclass(frozen=True)
class DueReminder:
    id: str
    title: str
    due_date: date
    status: str
    priority: str
    source_type: str
    source_uid: str


def load_active_due_reminders(
    path: Path = DEFAULT_REMINDERS_PATH,
    today: date | str | None = None,
) -> dict[str, list[DueReminder]]:
    """Load open reminders that are overdue, due today, or due within 14 days."""
    today_date = _parse_today(today)
    result: dict[str, list[DueReminder]] = {
        "overdue": [],
        "due_today": [],
        "due_soon": [],
    }

    for raw_reminder in load_reminders_store(path)["reminders"]:
        reminder = _to_due_reminder(raw_reminder)
        if reminder is None:
            continue
        if reminder.status.casefold() != "open":
            continue

        if reminder.due_date < today_date:
            result["overdue"].append(reminder)
        elif reminder.due_date == today_date:
            result["due_today"].append(reminder)
        elif reminder.due_date <= today_date + timedelta(days=DUE_SOON_DAYS):
            result["due_soon"].append(reminder)

    for reminders in result.values():
        reminders.sort(key=lambda item: (item.due_date, item.id))
    return result


def format_active_due_reminders(
    path: Path = DEFAULT_REMINDERS_PATH,
    today: date | str | None = None,
) -> str:
    """Format a safe startup reminder section for Samantha instructions."""
    grouped = load_active_due_reminders(path=path, today=today)
    if not any(grouped.values()):
        return "AKTIVNI PRIPOMINKY:\n- Zadna otevrena pripominka neni prosla ani do 14 dnu."

    lines = ["AKTIVNI PRIPOMINKY:"]
    _append_group(lines, "Prosle", grouped["overdue"])
    _append_group(lines, "Dnes", grouped["due_today"])
    _append_group(lines, "Do 14 dnu", grouped["due_soon"])
    return "\n".join(lines)


def _append_group(lines: list[str], label: str, reminders: list[DueReminder]) -> None:
    if not reminders:
        return

    lines.append(f"{label}:")
    for reminder in reminders:
        item = (
            f"- {reminder.id}: {reminder.title} "
            f"(deadline {reminder.due_date.isoformat()}, priorita {reminder.priority})"
        )
        if reminder.source_type.casefold() == "email":
            item += (
                f"; zdrojovy e-mail UID {reminder.source_uid}. "
                "Pro praci se zdrojovym e-mailem je nutne samostatne potvrzeni UID."
            )
        lines.append(item)


def _to_due_reminder(raw_reminder: dict[str, Any]) -> DueReminder | None:
    due_date = _parse_date(raw_reminder.get("due_date"))
    if due_date is None:
        return None

    source = raw_reminder.get("source")
    if not isinstance(source, dict):
        source = {}

    return DueReminder(
        id=_safe_text(raw_reminder.get("id", "")),
        title=_safe_text(raw_reminder.get("title", "")),
        due_date=due_date,
        status=_safe_text(raw_reminder.get("status", "")),
        priority=_safe_text(raw_reminder.get("priority", "")),
        source_type=_safe_text(source.get("type", "")),
        source_uid=_safe_text(source.get("uid", "")),
    )


def _parse_today(today: date | str | None) -> date:
    if today is None:
        return date.today()
    if isinstance(today, date):
        return today
    return date.fromisoformat(today)


def _parse_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _safe_text(value: Any) -> str:
    text = str(value) if value is not None else ""
    text = FULL_URL_PATTERN.sub("[URL redigovano]", text)
    text = EMAIL_PATTERN.sub("[e-mail redigovan]", text)
    text = " ".join(text.split())
    if URL_PATTERN.search(text) or EMAIL_PATTERN.search(text):
        return "[redigovano]"
    return text
