from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmailHeader:
    internal_id: str
    date: str
    sender: str
    subject: str
    source: str = ""
    folder: str = ""


@dataclass(frozen=True)
class EmailAttachmentMeta:
    filename: str
    content_type: str
    size_bytes: int | None
    part_id: str
    content_id: str
    disposition: str


@dataclass(frozen=True)
class EmailMessage:
    header: EmailHeader
    body_text: str
    truncated: bool
    attachments: tuple[EmailAttachmentMeta, ...] = ()


@dataclass(frozen=True)
class EmailSkippedMessage:
    header: EmailHeader
    reason: str


@dataclass(frozen=True)
class EmailMessageBatch:
    messages: tuple[EmailMessage, ...]
    skipped: tuple[EmailSkippedMessage, ...] = ()
    unavailable: tuple[str, ...] = ()


@dataclass(frozen=True)
class EmailTextSearchHit:
    header: EmailHeader
    matched_terms: tuple[str, ...]
