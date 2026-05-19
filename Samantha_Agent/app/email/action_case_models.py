from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionCaseAttachmentMeta:
    filename: str
    content_type: str
    size_bytes: int | None
    part_id: str
    disposition: str


@dataclass(frozen=True)
class ActionCaseLinkDomain:
    domain: str
    count: int


@dataclass(frozen=True)
class ReminderSource:
    type: str
    uid: str
    date: str
    sender: str


@dataclass(frozen=True)
class ReminderDraft:
    id: str
    title: str
    notes: str
    due_date: str
    priority: str
    status: str
    source: ReminderSource
    links: tuple[ActionCaseLinkDomain, ...]
    attachments: tuple[ActionCaseAttachmentMeta, ...]


@dataclass(frozen=True)
class EmailActionCase:
    uid: str
    date: str
    sender: str
    subject: str
    summary_redacted: str
    action_items: tuple[str, ...]
    deadline_raw: str
    deadline_date: str
    recommended_due_date: str
    attachments: tuple[ActionCaseAttachmentMeta, ...]
    link_domains: tuple[ActionCaseLinkDomain, ...]
    reminder_draft: ReminderDraft
    body_truncated: bool
    source_body_chars: int
    safety_note: str
