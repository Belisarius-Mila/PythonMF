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
    "uhradit do",
    "zaplatit do",
    "platnost do",
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
    "marketing",
    "odhlasit",
    "odhlásit",
)
PAYMENT_WORDS = (
    "faktura",
    "doklad",
    "platba",
    "zaplatit",
    "uhrazen",
    "uhradit",
    "uhrada",
    "úhrada",
    "vyuctovani",
    "vyúčtování",
)
INSURANCE_CRITICAL_WORDS = (
    "predpis pojistne",
    "předpis pojistné",
    "pojistna smlouva",
    "pojistná smlouva",
    "pojistne smlouvy",
    "pojistné smlouvy",
    "pojistne do",
    "pojistné do",
)
SECURITY_WORDS = (
    "klientska zona",
    "klientsky portal",
    "klientský portál",
    "overeni prihlaseni",
    "ověření přihlášení",
    "prihlasovaci kod",
    "přihlašovací kód",
    "ucet je pouzivan",
    "účet je používán",
    "heslo pro konkretni aplikaci",
    "heslo pro konkrétní aplikaci",
    "pristupy do klientske zony",
    "přístupy do klientské zóny",
    "onlinebanking",
    "online banking",
    "banking-postfach",
    "postfach",
    "dokumenteneingang",
    "smluvni dokumentace kb",
    "smluvní dokumentace kb",
    "zabezpeceni",
    "bezpecnost",
    "bezpečnost",
)
CRITICAL_WORDS = PAYMENT_WORDS + INSURANCE_CRITICAL_WORDS + SECURITY_WORDS
DELIVERY_WORDS = (
    "balik",
    "balíček",
    "balicek",
    "doru",
    "vyzvedn",
    "zasilk",
    "zásilk",
    "balikovna",
    "balíkovna",
    "dpd",
    "expedice",
)
ORDER_WORDS = (
    "objednavka",
    "objednávka",
    "obj.",
    "cislo objednavky",
    "číslo objednávky",
)
LOW_VALUE_WORDS = (
    "knihkupectvi",
    "knihkupectví",
    "luxor",
    "megaknihy",
    "trh knih",
    "sleva",
    "slevu",
    "marketing",
    "newsletter",
    "odhlasit",
    "odhlásit",
    "duolingo",
    "billa",
    "kosik",
    "košík",
    "esennce",
    "fnac",
    "epoch times",
    "politick",
    "ods",
    "spolu",
    "superdebata",
    "konference",
    "pozvanka",
    "pozvánka",
)
SPAM_FOLDERS = ("junk", "spam", "bulk mail", "nevyzadana", "nevyžádaná")
NON_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def triage_email_messages(messages: Iterable[EmailMessage]) -> TriageResult:
    items = tuple(_triage_one(message) for message in messages)
    important = tuple(item for item in items if item.priority in {"high", "normal"})
    deadlines = tuple(
        item for item in items if item.has_deadline and item.priority != "low"
    )
    actions = tuple(item for item in items if item.has_action and item.priority != "low")
    newsletters = tuple(item for item in items if item.priority == "low")
    candidates = tuple(
        item
        for item in items
        if item.priority in {"high", "normal"}
        or ((item.has_deadline or item.has_action) and item.priority != "low")
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
    is_delivery = _contains_any(text, DELIVERY_WORDS)
    is_order = _contains_any(text, ORDER_WORDS)
    is_low_value = _contains_any(text, LOW_VALUE_WORDS)
    is_spam_folder = _is_spam_folder(message.header.folder)
    has_deadline = bool(deadline_texts)
    critical_value = _critical_value_signal(
        message=message,
        text=text,
        low_context=is_low_value or is_spam_folder,
    )
    generic_action = _contains_any(text, ACTION_WORDS) or bool(action_case.action_items)
    has_action = (
        has_deadline
        or critical_value
        or is_delivery
        or is_order
        or (generic_action and not (is_low_value or is_spam_folder))
    )
    is_newsletter = _contains_any(text, NEWSLETTER_WORDS) or is_low_value
    priority = _priority(
        has_deadline=has_deadline,
        has_action=has_action,
        is_newsletter=is_newsletter,
        critical_value=critical_value,
        is_delivery=is_delivery,
        is_order=is_order,
        is_low_value=is_low_value,
        is_spam_folder=is_spam_folder,
    )
    category = _category(
        has_deadline=has_deadline,
        has_action=has_action,
        is_newsletter=is_newsletter,
        critical_value=critical_value,
        is_delivery=is_delivery,
        is_order=is_order,
        is_spam_folder=is_spam_folder,
    )
    subject = redact_email_addresses(message.header.subject or "(bez predmetu)")

    return TriageEmailItem(
        uid=message.header.internal_id,
        source=message.header.source,
        folder=message.header.folder,
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
        f"{message.header.source}\n{message.header.folder}\n{message.header.subject}\n{message.body_text}".casefold()
    )


def _extract_deadline_texts(text: str) -> list[str]:
    deadlines = [phrase for phrase in DEADLINE_PHRASES if phrase in text]
    if deadlines:
        deadlines.extend(DATE_PATTERN.findall(text))
    return _dedupe_keep_order(deadlines)


def _priority(
    has_deadline: bool,
    has_action: bool,
    is_newsletter: bool,
    critical_value: bool,
    is_delivery: bool,
    is_order: bool,
    is_low_value: bool,
    is_spam_folder: bool,
) -> str:
    if critical_value:
        return "high"
    if is_spam_folder:
        return "low"
    if is_low_value:
        return "low"
    if is_delivery or is_order:
        return "normal"
    if has_deadline or has_action:
        return "normal"
    if is_newsletter:
        return "low"
    return "low"


def _category(
    has_deadline: bool,
    has_action: bool,
    is_newsletter: bool,
    critical_value: bool,
    is_delivery: bool,
    is_order: bool,
    is_spam_folder: bool,
) -> str:
    if is_spam_folder and not critical_value:
        return "spam"
    if critical_value:
        return "important"
    if is_delivery:
        return "delivery"
    if is_order:
        return "order"
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


def _critical_value_signal(
    message: EmailMessage,
    text: str,
    low_context: bool,
) -> bool:
    if not _contains_any(text, CRITICAL_WORDS):
        return False
    if not low_context:
        return True

    subject_text = _strip_accents((message.header.subject or "").casefold())
    sender_text = _strip_accents(message.header.sender.casefold())
    header_text = f"{sender_text}\n{subject_text}"
    return _contains_any(header_text, CRITICAL_WORDS)


def _is_spam_folder(folder: str) -> bool:
    normalized = _strip_accents(folder.casefold())
    return any(word in normalized for word in SPAM_FOLDERS)


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
