from __future__ import annotations

import re
from collections.abc import Iterable
from email.utils import parsedate_to_datetime

from .action_case_models import (
    ActionCaseAttachmentMeta,
    ActionCaseLinkDomain,
    EmailActionCase,
    ReminderDraft,
    ReminderSource,
)
from .case_models import EmailCaseDraft
from .case_service import build_email_case_draft
from .models import EmailMessage
from .redaction import redact_email_addresses


URL_PATTERN = re.compile(r"https?://[^\s<>\")]+", re.IGNORECASE)
NON_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")
MONTH_END_PATTERNS = (
    ("leden", "01-31"),
    ("unor", "02-28"),
    ("unora", "02-28"),
    ("brezen", "03-31"),
    ("brezna", "03-31"),
    ("duben", "04-30"),
    ("dubna", "04-30"),
    ("kveten", "05-31"),
    ("kvetna", "05-31"),
    ("cervenec", "07-31"),
    ("cervence", "07-31"),
    ("cerven", "06-30"),
    ("cervna", "06-30"),
    ("srpen", "08-31"),
    ("srpna", "08-31"),
    ("zari", "09-30"),
    ("rijen", "10-31"),
    ("rijna", "10-31"),
    ("listopad", "11-30"),
    ("listopadu", "11-30"),
    ("prosinec", "12-31"),
    ("prosince", "12-31"),
)


def build_email_action_case(message: EmailMessage) -> EmailActionCase:
    """Build a safe action/reminder draft from an already-read EmailMessage."""
    draft = build_email_case_draft(message)
    body_text = redact_email_addresses(message.body_text or "")
    subject = redact_email_addresses(message.header.subject or "(bez predmetu)")
    sender = redact_email_addresses(message.header.sender)
    action_items = tuple(_build_action_items(draft=draft, subject=subject, body_text=body_text))
    deadline_date = _parsed_deadline_date(draft.deadline.raw_text) if draft.deadline else ""
    recommended_due_date = deadline_date or _recommended_due_date(
        date_header=message.header.date,
        body_text=body_text,
    )
    link_domains = tuple(_build_link_domain_summary(draft))
    attachments = tuple(_build_attachment_metadata(message))
    task_title = _build_task_title(action_items=action_items, subject=subject, body_text=body_text)
    task_notes = _build_task_notes(
        summary_redacted=draft.summary_redacted,
        action_items=action_items,
        recommended_due_date=recommended_due_date,
    )

    reminder = ReminderDraft(
        id=_build_reminder_id(uid=message.header.internal_id, title=task_title),
        title=task_title,
        notes=task_notes,
        due_date=recommended_due_date,
        priority=_task_priority(draft.priority),
        status="open",
        source=ReminderSource(
            type="email",
            uid=message.header.internal_id,
            date=message.header.date,
            sender=sender,
        ),
        links=link_domains,
        attachments=attachments,
    )

    return EmailActionCase(
        uid=message.header.internal_id,
        date=message.header.date,
        sender=sender,
        subject=subject,
        summary_redacted=_safe_summary(draft.summary_redacted),
        action_items=action_items,
        deadline_raw=draft.deadline.raw_text if draft.deadline else "",
        deadline_date=deadline_date,
        recommended_due_date=recommended_due_date,
        attachments=attachments,
        link_domains=link_domains,
        reminder_draft=reminder,
        body_truncated=message.truncated,
        source_body_chars=len(body_text),
        safety_note=(
            "Bezpecnost: action case vznikl z jiz potvrzene precteneho e-mailu; "
            "odkazy nebyly otevreny, prilohy nebyly stazeny, nic nebylo odeslano "
            "ani ulozeno do memory nebo reminders JSON."
        ),
    )


def format_email_action_case(case: EmailActionCase) -> str:
    lines = [
        f"UID: {case.uid}",
        f"Datum: {case.date}",
        f"Od: {case.sender}",
        f"Predmet: {case.subject}",
        f"Deadline: {case.deadline_raw or 'nenalezen'}",
        f"Doporuceny termin: {case.recommended_due_date or 'nenavrzen'}",
        "",
        "Shrnuti:",
        case.summary_redacted or "(nenalezen text)",
        "",
        "Akcni kroky:",
    ]

    if case.action_items:
        lines.extend(f"- {item}" for item in case.action_items)
    else:
        lines.append("- Nenalezeny")

    lines.extend(["", "Odkazy metadata:"])
    if case.link_domains:
        for link in case.link_domains:
            suffix = "odkaz" if link.count == 1 else "odkazu"
            lines.append(f"- {link.domain}: {link.count} {suffix}")
        lines.append("  Plne URL nezobrazuji automaticky; odkazy nebyly otevreny.")
    else:
        lines.append("- Nenalezeny")

    lines.extend(["", "Prilohy metadata:"])
    if case.attachments:
        for attachment in case.attachments:
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
            "Navrh ukolu do reminders JSON:",
            f"ID: {case.reminder_draft.id}",
            f"Title: {case.reminder_draft.title}",
            f"Notes: {case.reminder_draft.notes}",
            f"Due date: {case.reminder_draft.due_date or 'nenavrzen'}",
            f"Priority: {case.reminder_draft.priority}",
            f"Status: {case.reminder_draft.status}",
            "",
            case.safety_note,
        ]
    )

    if case.body_truncated:
        lines.append("[Poznamka: telo zdrojoveho e-mailu bylo pri cteni zkraceno.]")

    return "\n".join(lines)


def reminder_draft_to_dict(reminder: ReminderDraft) -> dict[str, object]:
    return {
        "id": reminder.id,
        "title": reminder.title,
        "notes": reminder.notes,
        "due_date": reminder.due_date,
        "priority": reminder.priority,
        "status": reminder.status,
        "source": {
            "type": reminder.source.type,
            "uid": reminder.source.uid,
            "date": reminder.source.date,
            "sender": reminder.source.sender,
        },
        "links": [
            {"domain": link.domain, "count": link.count}
            for link in reminder.links
        ],
        "attachments": [
            {
                "filename": attachment.filename,
                "content_type": attachment.content_type,
                "size_bytes": attachment.size_bytes,
                "part_id": attachment.part_id,
                "disposition": attachment.disposition,
            }
            for attachment in reminder.attachments
        ],
    }


def _build_action_items(
    draft: EmailCaseDraft,
    subject: str,
    body_text: str,
) -> list[str]:
    items = [_sanitize_text(item.text, max_chars=220) for item in draft.action_items]
    text = f"{subject}\n{body_text}".casefold()

    if "fotovolta" in text and _contains_any(text, ("prohlid", "servis", "kontrol")):
        items.insert(0, "Objednat prohlidku fotovoltaiky.")
    elif "nibe" in text and _contains_any(text, ("prohlid", "servis", "kontrol")):
        items.insert(0, "Objednat preventivni servisni prohlidku NIBE.")
    elif _contains_any(text, ("objednejte", "objednat", "rezervujte", "naplanujte")):
        items.insert(0, "Naplanovat navazujici krok podle e-mailu.")

    return _dedupe_keep_order(item for item in items if item)


def _build_task_title(
    action_items: tuple[str, ...],
    subject: str,
    body_text: str,
) -> str:
    text = f"{subject}\n{body_text}".casefold()
    if "fotovolta" in text and _contains_any(text, ("prohlid", "servis", "kontrol")):
        return "Objednat prohlidku fotovoltaiky"
    if action_items:
        return action_items[0].rstrip(".")
    return _sanitize_text(subject, max_chars=90)


def _build_task_notes(
    summary_redacted: str,
    action_items: tuple[str, ...],
    recommended_due_date: str,
) -> str:
    parts = [_safe_summary(summary_redacted)]
    if action_items:
        parts.append("Dalsi krok: " + action_items[0].rstrip(".") + ".")
    if recommended_due_date:
        parts.append(f"Doporuceny termin: {recommended_due_date}.")
    return _sanitize_text(" ".join(part for part in parts if part), max_chars=500)


def _safe_summary(summary: str) -> str:
    compact = _sanitize_text(summary, max_chars=1_000)
    boilerplate = (
        "Nezobrazuje se vam e-mail spravne?",
        "Nezobrazuje se vám e-mail správně?",
        "Kliknete sem",
        "Klikněte sem",
    )
    for phrase in boilerplate:
        compact = compact.replace(phrase, " ")
    compact = re.split(r"\b(?:Kontakt|Contact)\b:?", compact, maxsplit=1)[0].strip()

    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", compact)
        if sentence.strip()
    ]
    short_summary = " ".join(sentences[:3]).strip()
    return _sanitize_text(short_summary, max_chars=320)


def _sanitize_text(text: str, max_chars: int) -> str:
    without_urls = URL_PATTERN.sub("[odkaz redigovan]", text)
    redacted = redact_email_addresses(without_urls)
    compact = re.sub(r"\s+", " ", redacted).strip()
    if len(compact) > max_chars:
        return compact[:max_chars].rstrip() + "..."
    return compact


def _build_link_domain_summary(draft: EmailCaseDraft) -> list[ActionCaseLinkDomain]:
    counts: dict[str, int] = {}
    for link in draft.links:
        counts[link.label] = counts.get(link.label, 0) + 1
    return [
        ActionCaseLinkDomain(domain=domain, count=count)
        for domain, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _build_attachment_metadata(message: EmailMessage) -> list[ActionCaseAttachmentMeta]:
    return [
        ActionCaseAttachmentMeta(
            filename=redact_email_addresses(attachment.filename),
            content_type=attachment.content_type,
            size_bytes=attachment.size_bytes,
            part_id=attachment.part_id,
            disposition=attachment.disposition,
        )
        for attachment in message.attachments
    ]


def _parsed_deadline_date(raw_text: str) -> str:
    match = re.fullmatch(r"(\d{1,2})[./-](\d{1,2})(?:[./-](\d{2,4}))?", raw_text.strip())
    if not match:
        return ""
    day = int(match.group(1))
    month = int(match.group(2))
    year_text = match.group(3)
    if not year_text:
        return ""
    year = int(year_text)
    if year < 100:
        year += 2000
    return f"{year:04d}-{month:02d}-{day:02d}"


def _recommended_due_date(date_header: str, body_text: str) -> str:
    text = _strip_accents(body_text.casefold())
    if "do konce" not in text and "do konce mesice" not in text:
        return ""

    year = _year_from_header(date_header)
    year_match = re.search(r"\b(20\d{2})\b", text)
    if year_match:
        year = int(year_match.group(1))

    for month_name, month_day in MONTH_END_PATTERNS:
        if re.search(rf"\b{re.escape(month_name)}\b", text):
            return f"{year:04d}-{month_day}"
    return ""


def _year_from_header(date_header: str) -> int:
    try:
        return parsedate_to_datetime(date_header).year
    except (TypeError, ValueError):
        return 2026


def _build_reminder_id(uid: str, title: str) -> str:
    slug_source = f"email-{uid}-{title}".casefold()
    slug = NON_SLUG_PATTERN.sub("-", _strip_accents(slug_source)).strip("-")
    return slug[:80] or "email-action"


def _task_priority(email_priority: str) -> str:
    if email_priority == "high":
        return "high"
    if email_priority == "normal":
        return "normal"
    return "low"


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _dedupe_keep_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if not isinstance(item, str) or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


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
