from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable, Sequence

from .case_models import EmailCaseDraft
from .case_service import build_email_case_draft
from .insurance_case_models import (
    InsuranceActionItem,
    InsuranceAttachmentRef,
    InsuranceCase,
    InsuranceCaseSource,
    InsuranceLinkDomainSummary,
    InsuranceParticipant,
    InsuranceTimelineItem,
)
from .models import EmailMessage
from .redaction import redact_email_addresses


POLICY_PATTERN = re.compile(
    r"\b(?:pojist(?:ka|na|ne|eni|eni smlouva)|policy|smlouva)\b\s*(?:c\.|cislo|number|no\.?)?\s*[:#-]?\s*([A-Z0-9][A-Z0-9/-]{3,})",
    re.IGNORECASE,
)
CLAIM_PATTERN = re.compile(
    r"\b(?:skoda|skodn[ia] udalost|udalost|claim)\b\s*(?:c\.|cislo|number|no\.?)?\s*[:#-]?\s*([A-Z0-9][A-Z0-9/-]{3,})",
    re.IGNORECASE,
)
URL_PATTERN = re.compile(r"https?://[^\s<>\")]+", re.IGNORECASE)
INSURANCE_WORDS = (
    "rixo",
    "pojist",
    "skoda",
    "skodn",
    "claim",
    "policy",
    "smlouva",
    "likvidace",
)


def build_insurance_case(
    messages: Sequence[EmailMessage],
    title: str = "RIXO Insurance Case",
) -> InsuranceCase:
    if not messages:
        raise ValueError("InsuranceCase vyzaduje alespon jeden potvrzene precteny e-mail.")

    drafts = [build_email_case_draft(message) for message in messages]
    sources = tuple(_build_sources(messages))
    policy_reference = _first_match(messages, POLICY_PATTERN)
    claim_reference = _first_match(messages, CLAIM_PATTERN)
    link_domains = tuple(_build_link_domain_summaries(drafts))

    return InsuranceCase(
        title=title,
        status="draft",
        priority=_aggregate_priority(draft.priority for draft in drafts),
        source_count=len(messages),
        sources=sources,
        summary_redacted=_build_summary(drafts),
        participants=tuple(_build_participants(messages)),
        policy_reference=policy_reference or "nezjisteno",
        claim_reference=claim_reference or "nezjisteno",
        timeline=tuple(_build_timeline(messages, drafts)),
        action_items=tuple(_build_action_items(drafts)),
        attachments=tuple(_build_attachment_refs(messages)),
        link_domains=link_domains,
        open_questions=tuple(_build_open_questions(policy_reference, claim_reference, drafts)),
        safety_note=(
            "Bezpecnost: byly pouzity jen potvrzene prectene e-maily; odkazy nebyly "
            "otevreny, prilohy nebyly stazeny, nic nebylo odeslano ani ulozeno do memory."
        ),
    )


def format_insurance_case(case: InsuranceCase) -> str:
    lines = [
        f"Nazev: {case.title}",
        f"Stav: {case.status}",
        f"Priorita: {case.priority}",
        f"Potvrzene prectene zdroje: {case.source_count}",
        f"Pojistka / smlouva: {case.policy_reference}",
        f"Skoda / udalost: {case.claim_reference}",
        "",
        "Zdroje:",
    ]

    for source in case.sources:
        truncated = " ano" if source.body_truncated else " ne"
        lines.append(
            "- "
            f"UID {source.uid} | {source.date} | {source.sender} | "
            f"{source.subject} | zkraceno:{truncated}"
        )

    lines.extend(["", "Redigovane shrnuti:", case.summary_redacted or "(nenalezen text)"])

    lines.extend(["", "Ucastnici:"])
    if case.participants:
        for participant in case.participants:
            lines.append(
                f"- {participant.name_or_label} | role: {participant.role} | UID {participant.source_uid}"
            )
    else:
        lines.append("- Nezjisteno")

    lines.extend(["", "Casova osa:"])
    if case.timeline:
        for item in case.timeline:
            prefix = f"{item.date_or_reference}: " if item.date_or_reference else ""
            lines.append(f"- {prefix}{item.text} (UID {item.source_uid})")
    else:
        lines.append("- Nezjisteno")

    lines.extend(["", "Akcni kroky:"])
    if case.action_items:
        for item in case.action_items:
            lines.append(f"- [{item.status}] {item.text} (UID {item.source_uid})")
    else:
        lines.append("- Nenalezeny")

    lines.extend(["", "Prilohy pouze jako metadata:"])
    if case.attachments:
        for attachment in case.attachments:
            size = "neznamy" if attachment.size_bytes is None else str(attachment.size_bytes)
            lines.append(
                "- "
                f"UID {attachment.uid} | {attachment.filename} | "
                f"{attachment.content_type} | {size} B | part_id={attachment.part_id}"
            )
    else:
        lines.append("- Nenalezeny")

    lines.extend(["", "Odkazy pouze domeny a pocty:"])
    if case.link_domains:
        for link in case.link_domains:
            suffix = "odkaz" if link.count == 1 else "odkazu"
            source_uids = ", ".join(link.source_uids)
            lines.append(f"- {link.domain}: {link.count} {suffix} | UID {source_uids}")
        lines.append("  Plne URL nezobrazuji automaticky; odkazy nebyly otevreny.")
    else:
        lines.append("- Nenalezeny")

    lines.extend(["", "Otevrene otazky:"])
    if case.open_questions:
        lines.extend(f"- {question}" for question in case.open_questions)
    else:
        lines.append("- Zadna automaticky zjistena")

    lines.extend(["", case.safety_note])
    return "\n".join(lines)


def _build_sources(messages: Sequence[EmailMessage]) -> list[InsuranceCaseSource]:
    sources: list[InsuranceCaseSource] = []
    for message in messages:
        sources.append(
            InsuranceCaseSource(
                uid=message.header.internal_id,
                date=message.header.date,
                sender=redact_email_addresses(message.header.sender),
                subject=message.header.subject or "(bez predmetu)",
                body_truncated=message.truncated,
                source_body_chars=len(redact_email_addresses(message.body_text or "")),
            )
        )
    return sources


def _build_summary(drafts: Sequence[EmailCaseDraft]) -> str:
    parts: list[str] = []
    for draft in drafts:
        if draft.summary_redacted:
            parts.append(f"UID {draft.uid}: {draft.summary_redacted}")
    return "\n".join(parts)


def _build_participants(messages: Sequence[EmailMessage]) -> list[InsuranceParticipant]:
    participants: list[InsuranceParticipant] = []
    seen: set[tuple[str, str]] = set()
    for message in messages:
        sender = redact_email_addresses(message.header.sender).strip() or "neznamy odesilatel"
        source_text = f"{message.header.sender}\n{message.header.subject}\n{message.body_text}".casefold()
        role = "insurance contact" if any(word in source_text for word in INSURANCE_WORDS) else "sender"
        key = (sender, role)
        if key in seen:
            continue
        seen.add(key)
        participants.append(
            InsuranceParticipant(
                name_or_label=sender,
                role=role,
                source_uid=message.header.internal_id,
            )
        )
    return participants


def _build_timeline(
    messages: Sequence[EmailMessage],
    drafts: Sequence[EmailCaseDraft],
) -> list[InsuranceTimelineItem]:
    timeline: list[InsuranceTimelineItem] = []
    for message in messages:
        timeline.append(
            InsuranceTimelineItem(
                text=f"E-mail prijat: {message.header.subject or '(bez predmetu)'}",
                source_uid=message.header.internal_id,
                date_or_reference=message.header.date,
            )
        )

    for draft in drafts:
        if draft.deadline is None:
            continue
        timeline.append(
            InsuranceTimelineItem(
                text=f"Mozny deadline nebo casovy udaj: {draft.deadline.raw_text}",
                source_uid=draft.uid,
                date_or_reference=draft.deadline.parsed_date,
            )
        )
    return timeline


def _build_action_items(drafts: Sequence[EmailCaseDraft]) -> list[InsuranceActionItem]:
    items: list[InsuranceActionItem] = []
    seen: set[tuple[str, str]] = set()
    for draft in drafts:
        for item in draft.action_items:
            key = (draft.uid, item.text)
            if key in seen:
                continue
            seen.add(key)
            items.append(
                InsuranceActionItem(
                    text=_sanitize_case_text(item.text),
                    source_uid=draft.uid,
                    status=item.status,
                )
            )
    return items


def _build_attachment_refs(messages: Sequence[EmailMessage]) -> list[InsuranceAttachmentRef]:
    attachments: list[InsuranceAttachmentRef] = []
    for message in messages:
        for attachment in message.attachments:
            attachments.append(
                InsuranceAttachmentRef(
                    uid=message.header.internal_id,
                    filename=attachment.filename,
                    content_type=attachment.content_type,
                    size_bytes=attachment.size_bytes,
                    part_id=attachment.part_id,
                    disposition=attachment.disposition,
                )
            )
    return attachments


def _build_link_domain_summaries(
    drafts: Sequence[EmailCaseDraft],
) -> list[InsuranceLinkDomainSummary]:
    counts: dict[str, int] = defaultdict(int)
    source_uids: dict[str, set[str]] = defaultdict(set)
    for draft in drafts:
        for link in draft.links:
            domain = link.label
            counts[domain] += 1
            source_uids[domain].add(draft.uid)

    summaries: list[InsuranceLinkDomainSummary] = []
    for domain, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        summaries.append(
            InsuranceLinkDomainSummary(
                domain=domain,
                count=count,
                source_uids=tuple(sorted(source_uids[domain])),
            )
        )
    return summaries


def _build_open_questions(
    policy_reference: str,
    claim_reference: str,
    drafts: Sequence[EmailCaseDraft],
) -> list[str]:
    questions: list[str] = []
    if not policy_reference:
        questions.append("Jake je cislo pojistky nebo smlouvy?")
    if not claim_reference:
        questions.append("Jake je cislo skodni udalosti nebo claimu?")
    if not any(draft.action_items for draft in drafts):
        questions.append("Jaky je konkretni dalsi krok, pokud neni v e-mailech vyslovne uveden?")
    return questions


def _first_match(messages: Sequence[EmailMessage], pattern: re.Pattern[str]) -> str:
    for message in messages:
        text = redact_email_addresses(
            f"{message.header.subject}\n{message.body_text or ''}"
        )
        match = pattern.search(text)
        if match:
            return match.group(1)
    return ""


def _sanitize_case_text(text: str) -> str:
    without_urls = URL_PATTERN.sub("[odkaz redigovan]", text)
    return redact_email_addresses(without_urls)


def _aggregate_priority(priorities: Iterable[str]) -> str:
    ordered = tuple(priorities)
    if "high" in ordered:
        return "high"
    if "normal" in ordered:
        return "normal"
    return "low"
