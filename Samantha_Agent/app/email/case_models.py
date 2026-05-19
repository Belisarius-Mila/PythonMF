from __future__ import annotations

from dataclasses import dataclass

from .models import EmailAttachmentMeta


@dataclass(frozen=True)
class EmailLinkMeta:
    url: str
    label: str
    source_snippet: str


@dataclass(frozen=True)
class EmailActionItem:
    text: str
    status: str = "open"


@dataclass(frozen=True)
class EmailDeadline:
    raw_text: str
    parsed_date: str
    confidence: str


@dataclass(frozen=True)
class EmailCaseDraft:
    uid: str
    date: str
    sender: str
    subject: str
    email_type: str
    priority: str
    deadline: EmailDeadline | None
    action_items: tuple[EmailActionItem, ...]
    links: tuple[EmailLinkMeta, ...]
    attachments: tuple[EmailAttachmentMeta, ...]
    reply_draft: str
    summary_redacted: str
    body_truncated: bool
    source_body_chars: int
