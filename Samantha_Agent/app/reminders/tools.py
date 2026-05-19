from __future__ import annotations

from pathlib import Path
from agents import function_tool

from .store import DEFAULT_REMINDERS_PATH, save_reminder_draft


SAVE_CONFIRMATION_WORDS = (
    "uloz",
    "ulož",
    "ulozit",
    "uložit",
    "ukladam",
    "ukládám",
    "save",
)
REMINDER_CONFIRMATION_WORDS = (
    "pripominku",
    "připomínku",
    "pripominka",
    "připomínka",
    "reminder",
    "ukol",
    "úkol",
)


@function_tool
def save_email_action_case_reminder(
    id: str,
    title: str,
    notes: str,
    due_date: str,
    priority: str,
    status: str,
    source_type: str,
    source_uid: str,
    source_date: str,
    source_sender: str,
    link_domains: list[str],
    attachments: list[str],
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    """Save a safe email action reminder only after separate confirmation."""
    return save_email_action_case_reminder_text(
        id=id,
        title=title,
        notes=notes,
        due_date=due_date,
        priority=priority,
        status=status,
        source_type=source_type,
        source_uid=source_uid,
        source_date=source_date,
        source_sender=source_sender,
        link_domains=link_domains,
        attachments=attachments,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )


def save_email_action_case_reminder_text(
    id: str,
    title: str,
    notes: str,
    due_date: str,
    priority: str,
    status: str,
    source_type: str,
    source_uid: str,
    source_date: str,
    source_sender: str,
    link_domains: list[str],
    attachments: list[str],
    user_confirmed: bool = False,
    confirmation_text: str = "",
    path: Path = DEFAULT_REMINDERS_PATH,
) -> str:
    """Plain implementation behind the function tool, testable with a temp path."""
    if not user_confirmed or not has_explicit_reminder_save_confirmation(
        reminder_id=id,
        confirmation_text=confirmation_text,
    ):
        return (
            "Nejdrive potrebuji druhe samostatne potvrzeni od Mily v aktualni zprave. "
            f"Potvrzeni musi obsahovat id pripominky {id} a jasny souhlas s ulozenim "
            "pripominky. Bez toho na disk nic nezapisuji."
        )

    reminder = {
        "id": id,
        "title": title,
        "notes": notes,
        "due_date": due_date,
        "priority": priority,
        "status": status,
        "source": {
            "type": source_type,
            "uid": source_uid,
            "date": source_date,
            "sender": source_sender,
        },
        "links": _safe_link_domains(link_domains),
        "attachments": _safe_attachments(attachments),
    }

    try:
        result = save_reminder_draft(reminder, path=path)
    except ValueError as exc:
        return f"Ulozeni pripominky bylo odmitnuto: {exc}"

    if result.created:
        return (
            f"Ulozeno: {result.reminder_id}. "
            "Byl ulozen pouze bezpecny navrh pripominky; e-mail nebyl znovu cten, "
            "odkazy nebyly otevreny, prilohy nebyly stazeny a nic nebylo ulozeno do memory."
        )

    return (
        f"Neulozeno: {result.reminder_id}. {result.message} "
        "E-mail nebyl znovu cten a na disk nebyla pridana duplicita."
    )


def has_explicit_reminder_save_confirmation(
    reminder_id: str,
    confirmation_text: str,
) -> bool:
    normalized = confirmation_text.casefold()
    return (
        reminder_id.strip() in normalized
        and any(word in normalized for word in SAVE_CONFIRMATION_WORDS)
        and any(word in normalized for word in REMINDER_CONFIRMATION_WORDS)
    )


def _safe_link_domains(link_domains: list[str]) -> list[dict[str, object]]:
    safe_links: list[dict[str, object]] = []
    for link in link_domains:
        domain, count_text = _split_metadata_line(link, default_count="1")
        safe_links.append({"domain": domain, "count": int(count_text)})
    return safe_links


def _safe_attachments(attachments: list[str]) -> list[dict[str, object]]:
    safe_attachments: list[dict[str, object]] = []
    for attachment in attachments:
        parts = [part.strip() for part in attachment.split("|")]
        filename = parts[0] if len(parts) > 0 else ""
        content_type = parts[1] if len(parts) > 1 else ""
        size_bytes = _parse_optional_int(parts[2]) if len(parts) > 2 else None
        part_id = parts[3] if len(parts) > 3 else ""
        disposition = parts[4] if len(parts) > 4 else ""
        safe_attachments.append(
            {
                "filename": filename,
                "content_type": content_type,
                "size_bytes": size_bytes,
                "part_id": part_id,
                "disposition": disposition,
            }
        )
    return safe_attachments


def _split_metadata_line(value: str, default_count: str) -> tuple[str, str]:
    if "|" in value:
        left, right = value.split("|", 1)
        return left.strip(), right.strip() or default_count
    if ":" in value:
        left, right = value.rsplit(":", 1)
        if right.strip().isdigit():
            return left.strip(), right.strip()
    return value.strip(), default_count


def _parse_optional_int(value: str) -> int | None:
    stripped = value.strip()
    if not stripped or stripped == "None":
        return None
    return int(stripped)
