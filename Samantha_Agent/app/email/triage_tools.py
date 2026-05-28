from __future__ import annotations

import re
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from agents import function_tool

from .config import EmailConfigError
from .activity_state import DEFAULT_EMAIL_ACTIVITY_STATE_PATH, record_email_triage_completed
from .icloud_provider import EmailProviderError, ICloudReadOnlyEmailProvider
from .models import EmailMessage, EmailMessageBatch, EmailSkippedMessage
from .redaction import EMAIL_PATTERN, redact_email_addresses
from .seznam_provider import SeznamEmailProviderError, SeznamReadOnlyEmailProvider
from .triage_models import TriageEmailItem, TriageResult
from .triage_service import triage_email_messages


URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
LOW_INBOX_DISPLAY_LIMIT = 20
SPAM_DISPLAY_LIMIT = 15
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRIAGE_REPORT_DIR = PROJECT_ROOT / "data" / "email" / "triage_reports"
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
    require_confirmation: bool = False,
) -> str:
    """Run a read-only iCloud Mail triage session with a fixed safe action policy."""
    return run_email_triage_session_text(
        days=days,
        limit=limit,
        max_chars_per_email=max_chars_per_email,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
        require_confirmation=require_confirmation,
    )


@function_tool
def run_unified_email_triage_session(
    days: int = 7,
    limit_per_folder: int = 50,
    max_chars_per_email: int = 3_000,
    include_spam: bool = True,
) -> str:
    """Run read-only triage over iCloud and Seznam, including spam folders when available."""
    return run_unified_email_triage_session_text(
        days=days,
        limit_per_folder=limit_per_folder,
        max_chars_per_email=max_chars_per_email,
        include_spam=include_spam,
    )


def run_unified_email_triage_session_text(
    days: int = 7,
    limit_per_folder: int = 50,
    max_chars_per_email: int = 3_000,
    include_spam: bool = True,
    icloud_provider_factory: Callable[[], object] = ICloudReadOnlyEmailProvider,
    seznam_provider_factory: Callable[[], object] = SeznamReadOnlyEmailProvider,
    activity_state_path: Path = DEFAULT_EMAIL_ACTIVITY_STATE_PATH,
    report_dir: Path | None = DEFAULT_TRIAGE_REPORT_DIR,
) -> str:
    safe_days = min(max(1, days), 30)
    safe_limit = min(max(1, limit_per_folder), 200)
    safe_max_chars = min(max(200, max_chars_per_email), 20_000)

    messages: list[EmailMessage] = []
    skipped: list[EmailSkippedMessage] = []
    unavailable: list[str] = []

    for source, provider_factory, config_error, provider_error in [
        ("iCloud", icloud_provider_factory, EmailConfigError, EmailProviderError),
        ("Seznam", seznam_provider_factory, EmailConfigError, SeznamEmailProviderError),
    ]:
        try:
            provider = provider_factory()
            batch_loader = getattr(provider, "list_recent_messages_with_skipped")
            batch = batch_loader(
                days=safe_days,
                limit=safe_limit,
                max_chars=safe_max_chars,
                include_spam=include_spam,
            )
            if not isinstance(batch, EmailMessageBatch):
                raise RuntimeError("Provider vratil neocekavany typ triage batch.")
            messages.extend(batch.messages)
            skipped.extend(batch.skipped)
            unavailable.extend(batch.unavailable)
        except config_error:
            unavailable.append(f"{source}: chybi lokalni konfigurace")
        except provider_error as exc:
            unavailable.append(f"{source}: read-only triage selhala: {exc}")
        except AttributeError:
            unavailable.append(f"{source}: provider nepodporuje sjednocenou triage")

    triage = triage_email_messages(messages)
    record_email_triage_completed(path=activity_state_path)
    report_path = save_email_triage_report(
        triage=triage,
        days=safe_days,
        skipped=tuple(skipped),
        unavailable=tuple(unavailable),
        unified=True,
        include_spam=include_spam,
        report_dir=report_dir,
    )
    return format_email_triage_session_result(
        triage=triage,
        days=safe_days,
        skipped=tuple(skipped),
        unavailable=tuple(unavailable),
        unified=True,
        include_spam=include_spam,
        report_path=report_path,
    )


def run_email_triage_session_text(
    days: int = 7,
    limit: int = 50,
    max_chars_per_email: int = 3_000,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    require_confirmation: bool = False,
    provider_factory: Callable[[], object] = ICloudReadOnlyEmailProvider,
    activity_state_path: Path = DEFAULT_EMAIL_ACTIVITY_STATE_PATH,
    report_dir: Path | None = DEFAULT_TRIAGE_REPORT_DIR,
) -> str:
    safe_days = min(max(1, days), 30)
    safe_limit = min(max(1, limit), 200)
    safe_max_chars = min(max(200, max_chars_per_email), 20_000)

    if require_confirmation and (
        not user_confirmed or not has_explicit_triage_confirmation(
            days=safe_days,
            confirmation_text=confirmation_text,
        )
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
    report_path = save_email_triage_report(
        triage=triage,
        days=safe_days,
        report_dir=report_dir,
    )
    return format_email_triage_session_result(
        triage=triage,
        days=safe_days,
        report_path=report_path,
    )


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


def format_email_triage_session_result(
    triage: TriageResult,
    days: int,
    skipped: tuple[EmailSkippedMessage, ...] = (),
    unavailable: tuple[str, ...] = (),
    unified: bool = False,
    include_spam: bool = False,
    report_path: Path | None = None,
) -> str:
    lines = [
        (
            f"Unified Email Triage Session: poslednich {days} dni"
            if unified
            else f"Email Triage Session: poslednich {days} dni"
        ),
        "",
        "Souhrn:",
        f"- Celkem precteno pro triage: {len(triage.all_items)}",
        f"- High: {len(_items_by_priority(triage.all_items, 'high'))}",
        f"- Normal: {len(_items_by_priority(triage.all_items, 'normal'))}",
        f"- Low/newsletter/spam: {len(_items_by_priority(triage.all_items, 'low'))}",
        f"- Case kandidati: {len(triage.case_candidates)}",
        f"- Preskocene velke/necitene: {len(skipped)}",
        "",
        "High priorita:",
    ]
    _append_items(lines, _items_by_priority(triage.all_items, "high"), detail=True)
    lines.append("")
    lines.append("Normal priorita:")
    _append_items(lines, _items_by_priority(triage.all_items, "normal"), detail=True)
    lines.append("")
    lines.append("Deadline signaly mezi high/normal:")
    _append_items(lines, triage.deadline_emails, detail=False)
    lines.append("")
    lines.append("Low priorita - inbox/newslettery:")
    _append_items(
        lines,
        tuple(item for item in triage.newsletter_emails if item.category != "spam"),
        detail=False,
        display_limit=LOW_INBOX_DISPLAY_LIMIT,
    )
    lines.append("")
    lines.append("Low priorita - spam:")
    _append_items(
        lines,
        tuple(item for item in triage.newsletter_emails if item.category == "spam"),
        detail=False,
        display_limit=SPAM_DISPLAY_LIMIT,
    )
    lines.append("")
    lines.append("Preskocene velke/necitene zpravy:")
    _append_skipped_items(lines, skipped)
    if unavailable:
        lines.append("")
        lines.append("Nedostupne zdroje:")
        lines.extend(f"- {_safe_text(item)}" for item in unavailable)
    if report_path is not None:
        lines.append("")
        lines.append(f"Plny lokalni report: {_safe_text(report_path)}")
    lines.extend(
        [
            "",
            "Bezpecnost: provider byl pouzit read-only; odkazy nebyly otevreny, "
            "prilohy nebyly stazeny, nic nebylo odeslano, smazano, presunuto ani "
            "oznaceno jako prectene. Tato bezpecnostni politika je automaticka "
            "vychozi brzda triage. Nic nebylo ulozeno do EmailCaseVault, reminders "
            f"ani memory. Spam slozky: {'zahrnuty' if include_spam else 'nezahrnuty'}.",
        ]
    )
    return _sanitize_output("\n".join(lines))


def save_email_triage_report(
    triage: TriageResult,
    days: int,
    skipped: tuple[EmailSkippedMessage, ...] = (),
    unavailable: tuple[str, ...] = (),
    unified: bool = False,
    include_spam: bool = False,
    report_dir: Path | None = DEFAULT_TRIAGE_REPORT_DIR,
) -> Path | None:
    if report_dir is None:
        return None

    report_dir.mkdir(parents=True, exist_ok=True)
    scope = "unified" if unified else "icloud"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = report_dir / f"{stamp}_{scope}_email_triage_{days}d.md"
    path.write_text(
        format_email_triage_full_report(
            triage=triage,
            days=days,
            skipped=skipped,
            unavailable=unavailable,
            unified=unified,
            include_spam=include_spam,
        ),
        encoding="utf-8",
    )
    return path


def format_email_triage_full_report(
    triage: TriageResult,
    days: int,
    skipped: tuple[EmailSkippedMessage, ...] = (),
    unavailable: tuple[str, ...] = (),
    unified: bool = False,
    include_spam: bool = False,
) -> str:
    lines = [
        (
            f"Unified Email Triage Full Report: poslednich {days} dni"
            if unified
            else f"Email Triage Full Report: poslednich {days} dni"
        ),
        "",
        "Souhrn:",
        f"- Celkem precteno pro triage: {len(triage.all_items)}",
        f"- High: {len(_items_by_priority(triage.all_items, 'high'))}",
        f"- Normal: {len(_items_by_priority(triage.all_items, 'normal'))}",
        f"- Low/newsletter/spam: {len(_items_by_priority(triage.all_items, 'low'))}",
        f"- Case kandidati: {len(triage.case_candidates)}",
        f"- Preskocene velke/necitene: {len(skipped)}",
        "",
        "High priorita:",
    ]
    _append_items(lines, _items_by_priority(triage.all_items, "high"), detail=True)
    lines.append("")
    lines.append("Normal priorita:")
    _append_items(lines, _items_by_priority(triage.all_items, "normal"), detail=True)
    lines.append("")
    lines.append("Deadline signaly mezi high/normal:")
    _append_items(lines, triage.deadline_emails, detail=True)
    lines.append("")
    lines.append("Low priorita - inbox/newslettery:")
    _append_items(
        lines,
        tuple(item for item in triage.newsletter_emails if item.category != "spam"),
        detail=True,
    )
    lines.append("")
    lines.append("Low priorita - spam:")
    _append_items(
        lines,
        tuple(item for item in triage.newsletter_emails if item.category == "spam"),
        detail=True,
    )
    lines.append("")
    lines.append("Preskocene velke/necitene zpravy:")
    _append_skipped_items(lines, skipped)
    if unavailable:
        lines.append("")
        lines.append("Nedostupne zdroje:")
        lines.extend(f"- {_safe_text(item)}" for item in unavailable)
    lines.extend(
        [
            "",
            "Bezpecnost: report je lokalni a adresar je ignorovany gitem. "
            "Triage byla read-only; odkazy nebyly otevreny, prilohy nebyly "
            "stazeny, nic nebylo odeslano, smazano, presunuto ani oznaceno "
            f"jako prectene. Spam slozky: {'zahrnuty' if include_spam else 'nezahrnuty'}.",
        ]
    )
    return _sanitize_output("\n".join(lines))


def _items_by_priority(
    items: tuple[TriageEmailItem, ...],
    priority: str,
) -> tuple[TriageEmailItem, ...]:
    return tuple(item for item in items if item.priority == priority)


def _append_items(
    lines: list[str],
    items: tuple[TriageEmailItem, ...],
    detail: bool = False,
    display_limit: int | None = None,
) -> None:
    if not items:
        lines.append("- Nenalezeny")
        return

    visible_items = items if display_limit is None else items[:display_limit]
    for item in visible_items:
        lines.extend(
            [
                f"- UID: {_safe_text(item.uid)} | Datum: {_safe_text(item.date)}",
                f"  Zdroj: {_safe_text(_source_label(item))}",
                f"  Od: {_safe_text(item.sender)}",
                f"  Predmet: {_safe_text(item.subject)}",
                f"  Priorita: {_safe_text(item.priority)}",
                f"  Kategorie: {_safe_text(item.category)}",
                f"  Dalsi krok: {_safe_text(_next_step(item))}",
            ]
        )
        if detail:
            lines.extend(_detail_lines(item))

    hidden_count = len(items) - len(visible_items)
    if hidden_count > 0:
        lines.append(
            f"- ... dalsich {hidden_count} nizkoprioritnich polozek skryto v tomto prehledu."
        )


def _detail_lines(item: TriageEmailItem) -> list[str]:
    lines: list[str] = []
    if item.summary_redacted:
        lines.append(f"  Shrnuti: {_safe_text(_shorten(item.summary_redacted, 420))}")
    if item.deadline_texts:
        lines.append(
            "  Deadline signaly: "
            + ", ".join(_safe_text(text) for text in item.deadline_texts[:6])
        )
    if item.action_items:
        lines.append("  Akcni body:")
        lines.extend(f"    - {_safe_text(_shorten(action, 220))}" for action in item.action_items[:3])
    if item.attachments:
        lines.append("  Prilohy:")
        for attachment in item.attachments[:5]:
            size = "neznamy" if attachment.size_bytes is None else f"{attachment.size_bytes} B"
            lines.append(
                "    - "
                f"{_safe_text(attachment.filename)} | "
                f"{_safe_text(attachment.content_type)} | {size}"
            )
    if item.link_domains:
        domains = ", ".join(
            f"{_safe_text(link.domain)} ({link.count})" for link in item.link_domains[:6]
        )
        lines.append(f"  Odkazy domeny: {domains}")
    return lines


def _append_skipped_items(lines: list[str], items: tuple[EmailSkippedMessage, ...]) -> None:
    if not items:
        lines.append("- Nenalezeny")
        return

    for item in items:
        lines.extend(
            [
                f"- UID: {_safe_text(item.header.internal_id)} | Datum: {_safe_text(item.header.date)}",
                f"  Zdroj: {_safe_text(_header_source_label(item.header))}",
                f"  Od: {_safe_text(item.header.sender)}",
                f"  Predmet: {_safe_text(item.header.subject or '(bez predmetu)')}",
                f"  Duvod: {_safe_text(item.reason)}",
                "  Dalsi krok: rucne rozhodnout, zda nacist konkretni UID samostatne s vyssim limitem.",
            ]
        )


def _source_label(item: TriageEmailItem) -> str:
    source = getattr(item, "source", "")
    folder = getattr(item, "folder", "")
    if source and folder:
        return f"{source} / {folder}"
    if source:
        return source
    if folder:
        return folder
    return "neznamy zdroj"


def _header_source_label(header: object) -> str:
    source = getattr(header, "source", "")
    folder = getattr(header, "folder", "")
    if source and folder:
        return f"{source} / {folder}"
    if source:
        return source
    if folder:
        return folder
    return "neznamy zdroj"


def _next_step(item: TriageEmailItem) -> str:
    if item.action_items:
        return item.action_items[0].rstrip(".")
    if item.has_deadline:
        return "Zkontrolovat deadline a rozhodnout o dalsim kroku"
    if item.priority == "high":
        if item.category == "important":
            return "Zkontrolovat dulezity e-mail a rozhodnout, zda zalozit case nebo pripominku"
        return "Zkontrolovat e-mail s vysokou prioritou"
    if item.category == "delivery":
        return "Zkontrolovat stav doruceni"
    if item.is_newsletter:
        return "Pouze informativni / nizka priorita"
    return item.reminder_draft.title or "Zkontrolovat e-mail"


def _safe_text(value: Any) -> str:
    text = str(value) if value is not None else ""
    text = URL_PATTERN.sub("[URL redigovano]", text)
    text = redact_email_addresses(text)
    return " ".join(text.split())


def _shorten(text: str, max_chars: int) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3].rstrip() + "..."


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
