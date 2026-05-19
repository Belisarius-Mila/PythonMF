from __future__ import annotations

import re
from collections.abc import Iterable

from .action_case_service import build_email_action_case, reminder_draft_to_dict
from .case_vault import EmailCaseRecord
from .models import EmailMessage
from .redaction import redact_email_addresses
from .triage_models import TriageEmailItem, TriageResult


DATE_PATTERN = re.compile(r"\b\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?\b")
DEADLINE_PHRASES = (
    "do konce",
    "splatnost",
    "splatnosti",
    "deadline",
    "objednat do",
)
ACTION_WORDS = (
    "objednat",
    "zaplatit",
    "potvrdit",
    "odpovedet",
    "odpovědět",
    "zrusit",
    "zrušit",
    "vypoved",
    "výpověď",
    "vyplnit",
)
NEWSLETTER_WORDS = (
    "newsletter",
    "sleva",
    "akce",
    "marketing",
    "odhlasit",
    "odhlásit",
)
NON_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def triage_email_messages(messages: Iterable[EmailMessage]) -> TriageResult:
    items = tuple(_triage_one(message) for message in messages)
    important = tuple(item for item in items if item.priority in {"high", "normal"})
    deadlines = tuple(item for item in items if item.has_deadline)
    actions = tuple(item for item in items if item.has_action)
    newsletters = tuple(item for item in items if item.is_newsletter or item.priority == "low")
    candidates = tuple(
        item
        for item in items
        if item.has_deadline or item.has_action or item.priority in {"high", "normal"}
    )
    return TriageResult(
        important_emails=important,
        deadline_emails=deadlines,
        action_emails=actions,
        newsletter_emails=newsletters,
        case_candidates=candidates,
        all_items=items,
    )


def triage_item_to_case_record(item: TriageEmailItem) -> EmailCaseRecord:
    reason_parts: list[str] = []
    if item.has_deadline:
        reason_parts.append("obsahuje deadline")
    if item.has_action:
        reason_parts.append("obsahuje akcni krok")
    if item.is_newsletter:
        reason_parts.append("vypada jako newsletter")

    return EmailCaseRecord(
        case_id=item.case_id,
        source={
            "type": "email",
            "uid": item.uid,
            "date": item.date,
            "sender": item.sender,
            "subject": item.subject,
        },
        classification={
            "importance": item.priority,
            "category": item.category,
            "reason": ", ".join(reason_parts) or "bez vyrazneho signalu",
        },
        summary_redacted=item.summary_redacted,
        action_items=list(item.action_items),
        deadlines=list(item.deadline_texts),
        link_domains=[
            {"domain": link.domain, "count": link.count}
            for link in item.link_domains
        ],
        attachments=[
            {
                "filename": attachment.filename,
                "content_type": attachment.content_type,
                "size_bytes": attachment.size_bytes,
                "part_id": attachment.part_id,
                "disposition": attachment.disposition,
            }
            for attachment in item.attachments
        ],
        reminder_draft=reminder_draft_to_dict(item.reminder_draft),
        status="open",
        created_at="",
    )


def _triage_one(message: EmailMessage) -> TriageEmailItem:
    action_case = build_email_action_case(message)
    text = _normalized_text(message)
    deadline_texts = tuple(_extract_deadline_texts(text))
    has_deadline = bool(deadline_texts)
    has_action = _contains_any(text, ACTION_WORDS) or bool(action_case.action_items)
    is_newsletter = _contains_any(text, NEWSLETTER_WORDS)
    priority = _priority(has_deadline=has_deadline, has_action=has_action, is_newsletter=is_newsletter)
    category = _category(has_deadline=has_deadline, has_action=has_action, is_newsletter=is_newsletter)
    subject = redact_email_addresses(message.header.subject or "(bez predmetu)")

    return TriageEmailItem(
        uid=message.header.internal_id,
        date=message.header.date,
        sender=redact_email_addresses(message.header.sender),
        subject=subject,
        summary_redacted=action_case.summary_redacted,
        priority=priority,
        category=category,
        has_deadline=has_deadline,
        has_action=has_action,
        is_newsletter=is_newsletter,
        deadline_texts=deadline_texts,
        action_items=action_case.action_items,
        link_domains=action_case.link_domains,
        attachments=action_case.attachments,
        reminder_draft=action_case.reminder_draft,
        case_id=_case_id(uid=message.header.internal_id, subject=subject),
    )


def _normalized_text(message: EmailMessage) -> str:
    return _strip_accents(
        f"{message.header.subject}\n{message.body_text}".casefold()
    )


def _extract_deadline_texts(text: str) -> list[str]:
    deadlines = list(DATE_PATTERN.findall(text))
    deadlines.extend(phrase for phrase in DEADLINE_PHRASES if phrase in text)
    return _dedupe_keep_order(deadlines)


def _priority(has_deadline: bool, has_action: bool, is_newsletter: bool) -> str:
    if has_deadline and has_action:
        return "high"
    if has_deadline or has_action:
        return "normal"
    if is_newsletter:
        return "low"
    return "low"


def _category(has_deadline: bool, has_action: bool, is_newsletter: bool) -> str:
    if has_deadline:
        return "deadline"
    if has_action:
        return "task"
    if is_newsletter:
        return "newsletter"
    return "info"


def _case_id(uid: str, subject: str) -> str:
    slug = NON_SLUG_PATTERN.sub("-", _strip_accents(f"email-case-{uid}-{subject}".casefold()))
    return slug.strip("-")[:100] or "email-case"


def _contains_any(text: str, words: tuple[str, ...]) -> bool:
    return any(_strip_accents(word.casefold()) in text for word in words)


def _dedupe_keep_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
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
