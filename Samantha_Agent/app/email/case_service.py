from __future__ import annotations

import re
from urllib.parse import urlparse

from .case_models import EmailActionItem, EmailCaseDraft, EmailDeadline, EmailLinkMeta
from .models import EmailMessage
from .redaction import redact_email_addresses


URL_PATTERN = re.compile(r"https?://[^\s<>\")]+", re.IGNORECASE)
DATE_PATTERN = re.compile(
    r"\b("
    r"\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?"
    r"|today|tomorrow|zítra|zitra|dnes|asap|urgentně|urgentne"
    r")\b",
    re.IGNORECASE,
)
HIGH_PRIORITY_WORDS = (
    "urgent",
    "urgentni",
    "urgentní",
    "asap",
    "deadline",
    "overdue",
    "ihned",
    "dnes",
)
NORMAL_PRIORITY_WORDS = (
    "prosím",
    "prosim",
    "please",
    "request",
    "invoice",
    "faktura",
    "payment",
    "platba",
)
ACTION_WORDS = (
    "prosím",
    "prosim",
    "please",
    "potvrď",
    "potvrd",
    "confirm",
    "reply",
    "odpověz",
    "odpovez",
    "zaplať",
    "zaplat",
    "review",
    "zkontroluj",
)
NEWSLETTER_WORDS = (
    "newsletter",
    "unsubscribe",
    "odhlasit",
    "odhlásit",
    "zobrazit online verzi",
    "moje prodejna",
    "muj ucet",
    "můj účet",
    "vernostni",
    "věrnostní",
)


def build_email_case_draft(message: EmailMessage) -> EmailCaseDraft:
    body_text = redact_email_addresses(message.body_text or "")
    sender = redact_email_addresses(message.header.sender)
    subject = message.header.subject or "(bez predmetu)"

    return EmailCaseDraft(
        uid=message.header.internal_id,
        date=message.header.date,
        sender=sender,
        subject=subject,
        email_type=_classify_email(subject=subject, body_text=body_text),
        priority=_estimate_priority(subject=subject, body_text=body_text),
        deadline=_extract_deadline(body_text),
        action_items=tuple(_extract_action_items(body_text)),
        links=tuple(_extract_links(body_text)),
        attachments=message.attachments,
        reply_draft=_draft_reply(
            sender=sender,
            subject=subject,
            email_type=_classify_email(subject=subject, body_text=body_text),
        ),
        summary_redacted=_summarize(body_text),
        body_truncated=message.truncated,
        source_body_chars=len(body_text),
    )


def format_email_case_draft(case: EmailCaseDraft) -> str:
    lines = [
        f"UID: {case.uid}",
        f"Datum: {case.date}",
        f"Od: {case.sender}",
        f"Predmet: {case.subject}",
        f"Typ: {case.email_type}",
        f"Priorita: {case.priority}",
    ]

    if case.deadline is None:
        lines.append("Deadline: nenalezen")
    else:
        lines.append(
            "Deadline: "
            f"{case.deadline.raw_text} "
            f"(parsed: {case.deadline.parsed_date or 'neznamy'}, "
            f"confidence: {case.deadline.confidence})"
        )

    lines.extend(["", "Shrnuti:", case.summary_redacted or "(nenalezen text)"])

    lines.extend(["", "Akcni kroky:"])
    if case.action_items:
        lines.extend(f"- {item.text}" for item in case.action_items)
    else:
        lines.append("- Nenalezeny")

    lines.extend(["", "Odkazy metadata:"])
    if case.links:
        lines.extend(_format_link_summary(case.links))
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

    lines.extend(["", "Navrh odpovedi bez odeslani:", case.reply_draft])

    if case.body_truncated:
        lines.extend(["", "[Poznamka: telo bylo zkraceno podle limitu max_chars]"])

    lines.extend(
        [
            "",
            "Bezpecnost: odkazy nebyly otevreny, prilohy nebyly stazeny,",
            "odpoved nebyla odeslana a nic nebylo ulozeno do memory.",
        ]
    )

    return "\n".join(lines)


def format_email_full_links(
    message: EmailMessage,
    limit: int = 20,
) -> str:
    safe_limit = min(max(1, limit), 50)
    body_text = redact_email_addresses(message.body_text or "")
    links = _extract_links(body_text, limit=safe_limit)

    lines = [
        f"UID: {message.header.internal_id}",
        "Plne URL odkazu:",
    ]

    if links:
        for index, link in enumerate(links, start=1):
            lines.append(f"{index}. {link.url}")
    else:
        lines.append("- Nenalezeny")

    if len(links) >= safe_limit:
        lines.append(f"[Zobrazeno maximalne {safe_limit} odkazu]")

    lines.extend(
        [
            "",
            "Bezpecnost: odkazy nebyly otevreny, prilohy nebyly stazeny,",
            "e-mail nebyl upraven a nic nebylo ulozeno do memory.",
        ]
    )

    return "\n".join(lines)


def _summarize(body_text: str, max_sentences: int = 4, max_chars: int = 900) -> str:
    compact = _clean_summary_source(body_text)
    if not compact:
        return ""

    sentences = re.split(r"(?<=[.!?])\s+", compact)
    summary = " ".join(sentences[:max_sentences]).strip()
    if len(summary) > max_chars:
        summary = summary[:max_chars].rstrip() + "..."
    return summary


def _clean_summary_source(body_text: str) -> str:
    text = URL_PATTERN.sub(" ", body_text)
    text = text.replace("\\", " ")
    text = re.sub(r"\s+", " ", text).strip()

    boilerplate_phrases = (
        "Zobrazit online verzi",
        "Muj ucet",
        "Můj účet",
        "Moje prodejna",
        "Muži Ženy Děti",
    )
    for phrase in boilerplate_phrases:
        text = text.replace(phrase, " ")

    return re.sub(r"\s+", " ", text).strip()


def _estimate_priority(subject: str, body_text: str) -> str:
    text = f"{subject}\n{body_text}".casefold()
    if any(word in text for word in HIGH_PRIORITY_WORDS):
        return "high"
    if any(word in text for word in NORMAL_PRIORITY_WORDS):
        return "normal"
    return "low"


def _classify_email(subject: str, body_text: str) -> str:
    text = f"{subject}\n{body_text}".casefold()
    links = _extract_links(body_text, limit=20)

    if any(word in text for word in NEWSLETTER_WORDS):
        return "newsletter"
    if len(links) >= 8 and not _extract_action_items(body_text, limit=1):
        return "newsletter"
    if "invoice" in text or "faktura" in text:
        return "transactional"
    return "message"


def _extract_deadline(body_text: str) -> EmailDeadline | None:
    for match in DATE_PATTERN.finditer(body_text):
        raw_text = match.group(1)
        if not _is_plausible_deadline_text(raw_text):
            continue

        confidence = "medium" if any(char.isdigit() for char in raw_text) else "low"
        return EmailDeadline(raw_text=raw_text, parsed_date="", confidence=confidence)

    return None


def _is_plausible_deadline_text(raw_text: str) -> bool:
    lowered = raw_text.casefold()
    if not any(char.isdigit() for char in lowered):
        return True

    parts = re.split(r"[./-]", lowered)
    if len(parts) < 2:
        return False

    try:
        day = int(parts[0])
        month = int(parts[1])
    except ValueError:
        return False

    return 1 <= day <= 31 and 1 <= month <= 12


def _extract_action_items(body_text: str, limit: int = 6) -> list[EmailActionItem]:
    items: list[EmailActionItem] = []
    for line in body_text.splitlines():
        compact = " ".join(line.split())
        if not compact:
            continue
        lowered = compact.casefold()
        if any(word in lowered for word in ACTION_WORDS):
            items.append(EmailActionItem(text=compact[:240]))
            if len(items) >= limit:
                break
    return items


def _extract_links(body_text: str, limit: int = 10) -> list[EmailLinkMeta]:
    links: list[EmailLinkMeta] = []
    seen_urls: set[str] = set()
    for match in URL_PATTERN.finditer(body_text):
        url = match.group(0).rstrip(".,;")
        if url in seen_urls:
            continue
        seen_urls.add(url)
        start = max(0, match.start() - 80)
        end = min(len(body_text), match.end() + 80)
        snippet = " ".join(body_text[start:end].split())
        links.append(EmailLinkMeta(url=url, label=_url_domain(url), source_snippet=snippet))
        if len(links) >= limit:
            break
    return links


def _url_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc or "(neznama domena)"


def _format_link_summary(links: tuple[EmailLinkMeta, ...]) -> list[str]:
    domains: dict[str, int] = {}
    for link in links:
        domain = link.label or _url_domain(link.url)
        domains[domain] = domains.get(domain, 0) + 1

    lines: list[str] = []
    for domain, count in sorted(domains.items(), key=lambda item: (-item[1], item[0])):
        suffix = "odkaz" if count == 1 else "odkazu"
        lines.append(f"- {domain}: {count} {suffix}")

    lines.append("  Plne URL nezobrazuji automaticky; odkazy nebyly otevreny.")
    return lines


def _draft_reply(sender: str, subject: str, email_type: str) -> str:
    if email_type == "newsletter":
        return "Newsletter nebo marketingovy e-mail - odpoved se nenavrhuje."

    return "\n".join(
        [
            "Dobry den,",
            "",
            f"dekuji za zpravu k tematu: {subject}.",
            "Podivam se na to a ozvu se s dalsim postupem.",
            "",
            "S pozdravem",
        ]
    )
