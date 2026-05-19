from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InsuranceCaseSource:
    uid: str
    date: str
    sender: str
    subject: str
    body_truncated: bool
    source_body_chars: int


@dataclass(frozen=True)
class InsuranceParticipant:
    name_or_label: str
    role: str
    source_uid: str


@dataclass(frozen=True)
class InsuranceTimelineItem:
    text: str
    source_uid: str
    date_or_reference: str = ""


@dataclass(frozen=True)
class InsuranceActionItem:
    text: str
    source_uid: str
    status: str = "open"


@dataclass(frozen=True)
class InsuranceAttachmentRef:
    uid: str
    filename: str
    content_type: str
    size_bytes: int | None
    part_id: str
    disposition: str


@dataclass(frozen=True)
class InsuranceLinkDomainSummary:
    domain: str
    count: int
    source_uids: tuple[str, ...]


@dataclass(frozen=True)
class InsuranceCase:
    title: str
    status: str
    priority: str
    source_count: int
    sources: tuple[InsuranceCaseSource, ...]
    summary_redacted: str
    participants: tuple[InsuranceParticipant, ...]
    policy_reference: str
    claim_reference: str
    timeline: tuple[InsuranceTimelineItem, ...]
    action_items: tuple[InsuranceActionItem, ...]
    attachments: tuple[InsuranceAttachmentRef, ...]
    link_domains: tuple[InsuranceLinkDomainSummary, ...]
    open_questions: tuple[str, ...]
    safety_note: str
