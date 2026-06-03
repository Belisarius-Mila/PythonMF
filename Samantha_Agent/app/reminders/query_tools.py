from __future__ import annotations

import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from agents import function_tool

from app.email.redaction import EMAIL_PATTERN

from .store import DEFAULT_REMINDERS_PATH, URL_PATTERN, load_reminders_store


DUE_SOON_DAYS = 14
FULL_URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
DONE_CONFIRMATION_WORDS = (
    "hotovo",
    "hotove",
    "hotové",
    "splneno",
    "splněno",
    "done",
)
MARK_CONFIRMATION_WORDS = (
    "oznac",
    "označ",
    "oznacit",
    "označit",
    "nastav",
    "mark",
)


@function_tool
def list_open_reminders(include_future: bool = True) -> str:
    """List safe summaries of open reminders from the local reminders JSON."""
    return list_open_reminders_text(include_future=include_future)


@function_tool
def show_reminder_detail(reminder_id: str) -> str:
    """Show a safe detail for one local reminder without reading any source email."""
    return show_reminder_detail_text(reminder_id=reminder_id)


@function_tool
def mark_reminder_done(
    reminder_id: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    """Mark one reminder as done only after explicit confirmation."""
    return mark_reminder_done_text(
        reminder_id=reminder_id,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )


def list_open_reminders_text(
    include_future: bool = True,
    path: Path = DEFAULT_REMINDERS_PATH,
    today: date | str | None = None,
) -> str:
    reminders = [
        reminder
        for reminder in load_reminders_store(path)["reminders"]
        if _safe_text(reminder.get("status")).casefold() == "open"
    ]
    if not include_future:
        today_date = _parse_today(today)
        limit = today_date + timedelta(days=DUE_SOON_DAYS)
        reminders = [
            reminder
            for reminder in reminders
            if (due_date := _parse_date(reminder.get("due_date"))) is not None
            and due_date <= limit
        ]

    reminders.sort(key=lambda item: (_safe_text(item.get("due_date")), _safe_text(item.get("id"))))
    if not reminders:
        return "Otevrene pripominky: zadne."

    lines = ["Otevrene pripominky:"]
    for reminder in reminders:
        source = _source_dict(reminder)
        lines.append(
            "- "
            f"id: {_safe_text(reminder.get('id'))}; "
            f"title: {_safe_text(reminder.get('title'))}; "
            f"due_date: {_safe_text(reminder.get('due_date'))}; "
            f"priority: {_safe_text(reminder.get('priority'))}; "
            f"status: {_safe_text(reminder.get('status'))}; "
            f"source_type: {_safe_text(source.get('type'))}"
        )
    return "\n".join(lines)


def show_reminder_detail_text(
    reminder_id: str,
    path: Path = DEFAULT_REMINDERS_PATH,
) -> str:
    reminder = _find_reminder(reminder_id=reminder_id, path=path)
    if reminder is None:
        return f"Pripominka nenalezena: {_safe_text(reminder_id)}."

    source = _source_dict(reminder)
    source_type = _safe_text(source.get("type"))
    lines = [
        "Detail pripominky:",
        f"- id: {_safe_text(reminder.get('id'))}",
        f"- title: {_safe_text(reminder.get('title'))}",
        f"- notes: {_safe_text(reminder.get('notes'))}",
        f"- due_date: {_safe_text(reminder.get('due_date'))}",
        f"- priority: {_safe_text(reminder.get('priority'))}",
        f"- status: {_safe_text(reminder.get('status'))}",
        f"- source_type: {source_type}",
    ]

    if source_type.casefold() == "email":
        lines.append(f"- source_uid: {_safe_text(source.get('uid'))}")
        lines.append(
            "- poznamka: Cteni zdrojoveho e-mailu vyzaduje samostatne potvrzeni UID."
        )

    link_lines = _format_links(reminder.get("links"))
    if link_lines:
        lines.append("- odkazy: " + ", ".join(link_lines))

    attachment_lines = _format_attachments(reminder.get("attachments"))
    if attachment_lines:
        lines.append("- prilohy: " + ", ".join(attachment_lines))

    return "\n".join(lines)


def mark_reminder_done_text(
    reminder_id: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    path: Path = DEFAULT_REMINDERS_PATH,
) -> str:
    safe_id = _safe_text(reminder_id)
    if not user_confirmed or not has_explicit_done_confirmation(
        reminder_id=reminder_id,
        confirmation_text=confirmation_text,
    ):
        return (
            "Nejdrive potrebuji samostatne potvrzeni od Mily v aktualni zprave. "
            f"Potvrzeni musi obsahovat id pripominky {safe_id} a jasny souhlas "
            "s oznacenim jako hotove. Bez toho na disk nic nezapisuji."
        )

    store = load_reminders_store(path)
    for reminder in store["reminders"]:
        if reminder.get("id") == reminder_id:
            reminder["status"] = "done"
            _write_reminders_store(path=path, store=store)
            return (
                f"Oznaceno jako hotove: {safe_id}. "
                "Byl zmenen pouze status pripominky; e-mail nebyl cten, odkazy nebyly "
                "otevreny, prilohy nebyly stazeny a nic nebylo ulozeno do memory."
            )

    return f"Pripominka nenalezena: {safe_id}. Nic nebylo zapsano."


def has_explicit_done_confirmation(reminder_id: str, confirmation_text: str) -> bool:
    normalized = confirmation_text.casefold()
    return (
        reminder_id.strip().casefold() in normalized
        and any(word in normalized for word in DONE_CONFIRMATION_WORDS)
        and any(word in normalized for word in MARK_CONFIRMATION_WORDS)
    )


def _find_reminder(reminder_id: str, path: Path) -> dict[str, Any] | None:
    for reminder in load_reminders_store(path)["reminders"]:
        if reminder.get("id") == reminder_id:
            return reminder
    return None


def _write_reminders_store(path: Path, store: dict[str, list[dict[str, Any]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(store, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _source_dict(reminder: dict[str, Any]) -> dict[str, Any]:
    source = reminder.get("source")
    if isinstance(source, dict):
        return source
    return {}


def _format_links(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    lines: list[str] = []
    for link in value:
        if isinstance(link, dict):
            domain = _safe_text(link.get("domain"))
            count = _safe_text(link.get("count"))
            if domain:
                lines.append(f"{domain}|{count or '1'}")
    return lines


def _format_attachments(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    lines: list[str] = []
    for attachment in value:
        if isinstance(attachment, dict):
            filename = _safe_text(attachment.get("filename"))
            content_type = _safe_text(attachment.get("content_type"))
            size_bytes = _safe_text(attachment.get("size_bytes"))
            if filename:
                lines.append(f"{filename}|{content_type}|{size_bytes}")
    return lines


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
