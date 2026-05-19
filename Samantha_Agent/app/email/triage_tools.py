from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from agents import function_tool

from .config import EmailConfigError
from .activity_state import DEFAULT_EMAIL_ACTIVITY_STATE_PATH, record_email_triage_completed
from .icloud_provider import EmailProviderError, ICloudReadOnlyEmailProvider
from .models import EmailMessage
from .redaction import EMAIL_PATTERN, redact_email_addresses
from .triage_models import TriageEmailItem, TriageResult
from .triage_service import triage_email_messages


URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
TRIAGE_WORDS = ("triage", "email triage")
HEADER_READ_WORDS = ("hlavicky", "hlavicek", "hlavičky", "hlaviček", "headers")
BODY_READ_WORDS = ("tel", "tela", "telo", "těla", "tělo", "body")
CANDIDATE_WORDS = ("kandidat", "kandidatu", "kandidátn", "candidate", "email", "e-mail")
DENIAL_PHRASES = {
    "open_urls": (
        "neotevirat odkazy",
        "neotevirat url",
        "neotevírat odkazy",
        "neotevírat url",
        "neotevirej odkazy",
        "neotevirej url",
        "neotevírej odkazy",
        "neotevírej url",
        "neotvirej odkazy",
        "neotvírej odkazy",
        "neotvirej url",
        "neotvírej url",
    ),
    "download_attachments": (
        "nestahovat prilohy",
        "nestahovat přílohy",
        "nestahuj prilohy",
        "nestahuj přílohy",
    ),
    "send_email": (
        "nic neodesilat",
        "nic neodesílat",
        "neodesilat",
        "neodesílat",
        "nic neodesilej",
        "nic neodesílej",
        "neodesilej",
        "neodesílej",
    ),
    "delete_email": (
        "nemazat",
        "nemazat e-maily",
        "nemazat emaily",
        "nemaz",
        "nemaz e-maily",
        "nemaž e-maily",
        "nemaz emaily",
    ),
    "move_email": (
        "nepresouvat",
        "nepřesouvat",
        "nepresouvej",
        "nepřesouvej",
    ),
    "mark_read": (
        "neoznacovat jako prectene",
        "neoznačovat jako přečtené",
        "neoznacovat jako precteny",
        "neoznačovat jako přečtený",
        "neoznacovat jako prectene",
        "neoznacuj e-maily jako prectene",
        "neoznačuj e-maily jako přečtené",
        "neoznacuj emaily jako prectene",
        "neoznacuj jako prectene",
        "neoznačuj jako přečtené",
    ),
}


@function_tool
def run_email_triage_session(
    days: int = 7,
    limit: int = 50,
    max_chars_per_email: int = 3_000,
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    """Run a read-only iCloud Mail triage session after explicit confirmation."""
    return run_email_triage_session_text(
        days=days,
        limit=limit,
        max_chars_per_email=max_chars_per_email,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )


def run_email_triage_session_text(
    days: int = 7,
    limit: int = 50,
    max_chars_per_email: int = 3_000,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    provider_factory: Callable[[], object] = ICloudReadOnlyEmailProvider,
    activity_state_path: Path = DEFAULT_EMAIL_ACTIVITY_STATE_PATH,
) -> str:
    safe_days = min(max(1, days), 30)
    safe_limit = min(max(1, limit), 200)
    safe_max_chars = min(max(200, max_chars_per_email), 20_000)

    if not user_confirmed or not has_explicit_triage_confirmation(
        days=safe_days,
        confirmation_text=confirmation_text,
    ):
        return (
            "Nejdrive potrebuji jasne potvrzeni od Mily v aktualni zprave. "
            "Potvrzeni musi obsahovat triage/Email Triage, pocet dni nebo frazi "
            f"poslednich {safe_days} dni, souhlas se ctenim hlavicek a tel "
            "kandidatnich e-mailu a zakazy: neotevirat odkazy, nestahovat prilohy, "
            "nic neodesilat, nemazat, nepresouvat a neoznacovat jako prectene. "
            "Bez toho provider nevolam."
        )

    try:
        provider = provider_factory()
        list_recent_messages = getattr(provider, "list_recent_messages")
        messages = list_recent_messages(
            days=safe_days,
            limit=safe_limit,
            max_chars=safe_max_chars,
        )
        if not isinstance(messages, list) or not all(
            isinstance(message, EmailMessage) for message in messages
        ):
            raise EmailProviderError("Provider vratil neocekavany typ zprav.")
    except EmailConfigError:
        return (
            "Chybi lokalni konfigurace pro iCloud Mail. "
            "Zkontroluj lokalni .env; neposilej heslo do chatu."
        )
    except EmailProviderError as exc:
        return f"Email triage selhala: {exc}"

    triage = triage_email_messages(messages)
    record_email_triage_completed(path=activity_state_path)
    return format_email_triage_session_result(triage=triage, days=safe_days)


def has_explicit_triage_confirmation(days: int, confirmation_text: str) -> bool:
    normalized = _normalize_confirmation_text(confirmation_text)
    return (
        any(word in normalized for word in TRIAGE_WORDS)
        and _contains_days_reference(normalized, days)
        and any(word in normalized for word in HEADER_READ_WORDS)
        and any(word in normalized for word in BODY_READ_WORDS)
        and any(word in normalized for word in CANDIDATE_WORDS)
        and all(
            any(phrase in normalized for phrase in phrases)
            for phrases in DENIAL_PHRASES.values()
        )
    )


def format_email_triage_session_result(triage: TriageResult, days: int) -> str:
    lines = [
        f"Email Triage Session: poslednich {days} dni",
        "",
        "Dulezite e-maily:",
    ]
    _append_items(lines, triage.important_emails)
    lines.append("")
    lines.append("Deadline e-maily:")
    _append_items(lines, triage.deadline_emails)
    lines.append("")
    lines.append("Action e-maily:")
    _append_items(lines, triage.action_emails)
    lines.append("")
    lines.append("Newslettery / nizka priorita:")
    _append_items(lines, triage.newsletter_emails)
    lines.append("")
    lines.append("Case kandidati:")
    _append_items(lines, triage.case_candidates)
    lines.extend(
        [
            "",
            "Bezpecnost: provider byl pouzit read-only; odkazy nebyly otevreny, "
            "prilohy nebyly stazeny, nic nebylo odeslano, smazano, presunuto ani "
            "oznaceno jako prectene. Nic nebylo ulozeno do EmailCaseVault, reminders "
            "ani memory.",
        ]
    )
    return _sanitize_output("\n".join(lines))


def _append_items(lines: list[str], items: tuple[TriageEmailItem, ...]) -> None:
    if not items:
        lines.append("- Nenalezeny")
        return

    for item in items:
        lines.extend(
            [
                f"- UID: {_safe_text(item.uid)}",
                f"  Datum: {_safe_text(item.date)}",
                f"  Od: {_safe_text(item.sender)}",
                f"  Predmet: {_safe_text(item.subject)}",
                f"  Priorita: {_safe_text(item.priority)}",
                f"  Dalsi krok: {_safe_text(_next_step(item))}",
            ]
        )


def _next_step(item: TriageEmailItem) -> str:
    if item.action_items:
        return item.action_items[0].rstrip(".")
    if item.has_deadline:
        return "Zkontrolovat deadline a rozhodnout o dalsim kroku"
    if item.is_newsletter:
        return "Pouze informativni / nizka priorita"
    return item.reminder_draft.title or "Zkontrolovat e-mail"


def _safe_text(value: Any) -> str:
    text = str(value) if value is not None else ""
    text = URL_PATTERN.sub("[URL redigovano]", text)
    text = redact_email_addresses(text)
    return " ".join(text.split())


def _sanitize_output(text: str) -> str:
    text = URL_PATTERN.sub("[URL redigovano]", text)
    text = redact_email_addresses(text)
    if EMAIL_PATTERN.search(text) or URL_PATTERN.search(text):
        return "Triage vystup byl odmitnut, protoze obsahuje citliva data."
    return text


def _contains_days_reference(normalized: str, days: int) -> bool:
    if f"poslednich {days} dni" in normalized:
        return True
    if f"poslednich {days} dnu" in normalized:
        return True
    return str(days) in normalized and ("dni" in normalized or "dnu" in normalized)


def _normalize_confirmation_text(text: str) -> str:
    normalized = _strip_accents(text.casefold())
    return " ".join(normalized.split())


def _strip_accents(text: str) -> str:
    replacements = str.maketrans(
        {
            "á": "a",
            "č": "c",
            "ď": "d",
            "é": "e",
            "ě": "e",
            "í": "i",
            "ň": "n",
            "ó": "o",
            "ř": "r",
            "š": "s",
            "ť": "t",
            "ú": "u",
            "ů": "u",
            "ý": "y",
            "ž": "z",
        }
    )
    return text.translate(replacements)
