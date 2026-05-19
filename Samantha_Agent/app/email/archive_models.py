from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import EmailAttachmentMeta


@dataclass(frozen=True)
class EmailArchiveSource:
    uid: str
    date: str
    sender: str
    subject: str
    body_text: str
    body_html: str = ""
    links: tuple[str, ...] = ()
    attachments: tuple[EmailAttachmentMeta, ...] = ()
    original_eml: bytes | None = None
    message_id: str = ""
    mailbox: str = "INBOX"
    provider: str = "local"


@dataclass(frozen=True)
class EmailArchiveSaveResult:
    archive_id: str
    created: bool
    path: Path
    files: tuple[str, ...]
    message: str
