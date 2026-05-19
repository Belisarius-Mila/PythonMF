from __future__ import annotations

import re
from datetime import datetime

from .action_case_service import build_email_action_case, format_email_action_case
from .case_service import URL_PATTERN
from .models import EmailMessage
from .redaction import redact_email_addresses
from .work_session_models import (
    ALLOWED_ACTIONS,
    BUILD_ACTION_CASE,
    BUILD_REMINDER_DRAFT,
    DEFAULT_DENIED_ACTIONS,
    DENIED_ACTIONS,
    DOWNLOAD_ATTACHMENTS,
    EmailWorkSession,
    EmailWorkSessionResult,
    OPEN_URLS,
    READ_BODY,
    SEND_EMAIL,
    DELETE_EMAIL,
    SHOW_ATTACHMENT_METADATA,
    SHOW_FULL_URLS,
)


ACTION_CONFIRMATION_PHRASES: dict[str, tuple[str, ...]] = {
    READ_BODY: ("read_body", "precist telo", "přečíst tělo", "cteni tela", "čtení těla"),
    BUILD_ACTION_CASE: ("build_action_case", "action case"),
    SHOW_FULL_URLS: ("show_full_urls", "plne url", "plné url", "plne odkazy", "plné odkazy"),
    BUILD_REMINDER_DRAFT: (
        "build_reminder_draft",
        "safe reminder",
        "bezpecnou pripominku",
        "bezpečnou připomínku",
        "navrh pripominky",
        "návrh připomínky",
    ),
    SHOW_ATTACHMENT_METADATA: (
        "show_attachment_metadata",
        "metadata priloh",
        "metadata příloh",
    ),
}
REQUIRED_DENIAL_PHRASES: dict[str, tuple[str, ...]] = {
    OPEN_URLS: (
        "neotevirat odkazy",
        "neotevírat odkazy",
        "neotevirat url",
        "neotevírat url",
    ),
    DOWNLOAD_ATTACHMENTS: (
        "nestahovat prilohy",
        "nestahovat přílohy",
    ),
    SEND_EMAIL: (
        "nic neodesilat",
        "nic neodesílat",
        "neodesilat e-mail",
        "neodesílat e-mail",
        "neodesilat email",
        "neodesílat email",
    ),
}
FULL_URL_PATTERN = re.compile(r"https?://[^\s<>\")]+", re.IGNORECASE)


def create_email_work_session(
    uid: str,
    allowed_actions: set[str] | frozenset[str],
    confirmation_text: str,
    denied_actions: set[str] | frozenset[str] = DEFAULT_DENIED_ACTIONS,
    created_at: datetime | None = None,
) -> EmailWorkSession:
    """Validate one-message work-session permission and return a session model."""
    normalized_allowed = frozenset(allowed_actions)
    normalized_denied = frozenset(denied_actions)
    _validate_session_inputs(
        uid=uid,
        allowed_actions=normalized_allowed,
        denied_actions=normalized_denied,
        confirmation_text=confirmation_text,
    )
    return EmailWorkSession(
        uid=uid,
        allowed_actions=normalized_allowed,
        denied_actions=normalized_denied,
        confirmation_text=confirmation_text,
        created_at=created_at or datetime.now(),
    )


def build_email_work_session_result(
    message: EmailMessage,
    session: EmailWorkSession,
) -> EmailWorkSessionResult:
    """Build a safe work-session result from an already-loaded EmailMessage."""
    if message.header.internal_id != session.uid:
        raise ValueError("EmailMessage UID neodpovida EmailWorkSession UID.")

    action_case = build_email_action_case(message)
    full_urls = _extract_full_urls(message) if SHOW_FULL_URLS in session.allowed_actions else ()
    return EmailWorkSessionResult(
        uid=session.uid,
        summary_redacted=action_case.summary_redacted,
        action_case_text=format_email_action_case(action_case),
        full_urls=full_urls,
        attachment_metadata=action_case.attachments,
        reminder_draft=action_case.reminder_draft,
        safety_note=(
            "Bezpecnost: Email Work Session pracovala jen s uz predanym EmailMessage; "
            "nevolala IMAP/provider, URL nebyly otevreny, prilohy nebyly stazeny, "
            "e-mail nebyl odeslan, smazan, presunut ani oznacen jako precteny. "
            "Cele telo e-mailu nebylo ulozeno do memory ani do reminders JSON."
        ),
    )


def format_email_work_session_result(result: EmailWorkSessionResult) -> str:
    lines = [
        f"UID: {result.uid}",
        "",
        "Redigovane shrnuti:",
        result.summary_redacted or "(nenalezen text)",
        "",
        "Action case:",
        result.action_case_text,
        "",
        "Plne URL:",
    ]

    if result.full_urls:
        lines.extend(f"- {url}" for url in result.full_urls)
    else:
        lines.append("- Nepovoleno nebo nenalezeno; odkazy zustavaji jen jako domeny/metadata.")

    lines.extend(["", "Prilohy metadata:"])
    if result.attachment_metadata:
        for attachment in result.attachment_metadata:
            size = "neznamy" if attachment.size_bytes is None else str(attachment.size_bytes)
            lines.append(
                "- "
                f"{attachment.filename} | {attachment.content_type} | "
                f"{size} B | part_id={attachment.part_id}"
            )
    else:
        lines.append("- Nenalezeny")

    lines.extend(
        [
            "",
            "Safe reminder draft:",
            f"ID: {result.reminder_draft.id}",
            f"Title: {result.reminder_draft.title}",
            f"Notes: {result.reminder_draft.notes}",
            f"Due date: {result.reminder_draft.due_date or 'nenavrzen'}",
            f"Priority: {result.reminder_draft.priority}",
            f"Status: {result.reminder_draft.status}",
            "",
            result.safety_note,
        ]
    )
    return _sanitize_formatted_output("\n".join(lines), allowed_full_urls=result.full_urls)


def _validate_session_inputs(
    uid: str,
    allowed_actions: frozenset[str],
    denied_actions: frozenset[str],
    confirmation_text: str,
) -> None:
    if not uid.strip():
        raise ValueError("EmailWorkSession vyzaduje konkretni UID.")
    unknown_allowed = allowed_actions - ALLOWED_ACTIONS
    if unknown_allowed:
        raise ValueError("Neznama povolena akce: " + ", ".join(sorted(unknown_allowed)))
    unknown_denied = denied_actions - DENIED_ACTIONS
    if unknown_denied:
        raise ValueError("Neznama zakazana akce: " + ", ".join(sorted(unknown_denied)))
    missing_denied = DENIED_ACTIONS - denied_actions
    if missing_denied:
        raise ValueError("Chybi zakazana akce: " + ", ".join(sorted(missing_denied)))

    normalized = _normalize_for_confirmation(confirmation_text)
    if "email work session" not in normalized:
        raise ValueError("Potvrzeni musi obsahovat slova Email Work Session.")
    if uid.casefold() not in confirmation_text.casefold():
        raise ValueError("Potvrzeni musi obsahovat konkretni UID.")

    for action in sorted(allowed_actions):
        if not _contains_any_phrase(normalized, ACTION_CONFIRMATION_PHRASES[action]):
            raise ValueError(f"Potvrzeni musi obsahovat povolenou akci {action}.")

    for action, phrases in REQUIRED_DENIAL_PHRASES.items():
        if action not in denied_actions:
            raise ValueError(f"Session musi zakazovat akci {action}.")
        if not _contains_any_phrase(normalized, phrases):
            raise ValueError(f"Potvrzeni musi explicitne zakazat akci {action}.")


def _extract_full_urls(message: EmailMessage) -> tuple[str, ...]:
    urls: list[str] = []
    seen: set[str] = set()
    for match in FULL_URL_PATTERN.finditer(message.body_text or ""):
        url = match.group(0).rstrip(".,;")
        if url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return tuple(urls)


def _sanitize_formatted_output(text: str, allowed_full_urls: tuple[str, ...]) -> str:
    placeholders: dict[str, str] = {}
    safe_text = text
    for index, url in enumerate(allowed_full_urls):
        placeholder = f"__EMAIL_WORK_SESSION_ALLOWED_URL_{index}__"
        placeholders[placeholder] = url
        safe_text = safe_text.replace(url, placeholder)

    safe_text = URL_PATTERN.sub("[odkaz redigovan]", safe_text)
    safe_text = redact_email_addresses(safe_text)

    for placeholder, url in placeholders.items():
        safe_text = safe_text.replace(placeholder, url)
    return safe_text


def _normalize_for_confirmation(text: str) -> str:
    return " ".join(text.casefold().split())


def _contains_any_phrase(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase.casefold() in text for phrase in phrases)
