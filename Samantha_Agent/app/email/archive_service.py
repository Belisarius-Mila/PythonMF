from __future__ import annotations

import json
import re
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from .archive_models import EmailArchiveSaveResult, EmailArchiveSource
from .models import EmailAttachmentMeta, EmailMessage


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EMAIL_ARCHIVE_DIR = PROJECT_ROOT / "data" / "email" / "archive"
URL_PATTERN = re.compile(r"https?://[^\s<>'\")]+", re.IGNORECASE)
NON_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def email_message_to_archive_source(
    message: EmailMessage,
    body_html: str = "",
    original_eml: bytes | None = None,
    message_id: str = "",
    mailbox: str = "INBOX",
    provider: str = "local",
) -> EmailArchiveSource:
    body_text = message.body_text or ""
    links = tuple(_dedupe_keep_order(_extract_links(body_text, body_html)))
    return EmailArchiveSource(
        uid=message.header.internal_id,
        date=message.header.date,
        sender=message.header.sender,
        subject=message.header.subject,
        body_text=body_text,
        body_html=body_html,
        links=links,
        attachments=message.attachments,
        original_eml=original_eml,
        message_id=message_id,
        mailbox=mailbox,
        provider=provider,
    )


def save_email_archive(
    source: EmailArchiveSource,
    directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
    archived_at: datetime | None = None,
) -> EmailArchiveSaveResult:
    archive_id = _archive_id(uid=source.uid, subject=source.subject)
    archive_dir = directory / archive_id
    if archive_dir.exists():
        return EmailArchiveSaveResult(
            archive_id=archive_id,
            created=False,
            path=archive_dir,
            files=tuple(_relative_files(archive_dir)),
            message="Archiv e-mailu uz existuje; duplicita nebyla pridana.",
        )

    archive_dir.mkdir(parents=True, exist_ok=True)
    attachments_dir = archive_dir / "attachments"
    attachments_dir.mkdir(parents=True, exist_ok=True)

    archive_time = (archived_at or datetime.now(timezone.utc)).replace(microsecond=0)
    links = tuple(_dedupe_keep_order(source.links or _extract_links(source.body_text, source.body_html)))

    _write_json(
        archive_dir / "metadata.json",
        _metadata_dict(
            source=source,
            archive_id=archive_id,
            archived_at=archive_time.isoformat(),
            links_count=len(links),
        ),
    )
    (archive_dir / "body.txt").write_text(source.body_text or "", encoding="utf-8")

    if source.body_html:
        (archive_dir / "body.html").write_text(source.body_html, encoding="utf-8")

    _write_json(archive_dir / "links.json", _links_dict(uid=source.uid, links=links))
    _write_json(
        attachments_dir / "attachments.json",
        _attachments_dict(uid=source.uid, attachments=source.attachments),
    )

    if source.original_eml is not None:
        (archive_dir / "original.eml").write_bytes(source.original_eml)

    return EmailArchiveSaveResult(
        archive_id=archive_id,
        created=True,
        path=archive_dir,
        files=tuple(_relative_files(archive_dir)),
        message="Archiv e-mailu byl ulozen do EmailArchiveVault.",
    )


def _metadata_dict(
    source: EmailArchiveSource,
    archive_id: str,
    archived_at: str,
    links_count: int,
) -> dict[str, object]:
    return {
        "archive_id": archive_id,
        "uid": source.uid,
        "message_id": source.message_id,
        "date": source.date,
        "from": source.sender,
        "subject": source.subject,
        "provider": source.provider,
        "mailbox": source.mailbox,
        "archived_at": archived_at,
        "body_text_saved": True,
        "body_html_saved": bool(source.body_html),
        "original_eml_saved": source.original_eml is not None,
        "attachments_count": len(source.attachments),
        "links_count": links_count,
        "safety_flags": {
            "contains_full_body": True,
            "contains_full_urls": True,
            "contains_unredacted_headers": True,
            "local_sensitive_archive": True,
            "do_not_commit": True,
        },
    }


def _links_dict(uid: str, links: Iterable[str]) -> dict[str, object]:
    return {
        "uid": uid,
        "links": [
            {
                "url": link,
                "domain": urlparse(link).netloc,
            }
            for link in links
        ],
    }


def _attachments_dict(
    uid: str,
    attachments: tuple[EmailAttachmentMeta, ...],
) -> dict[str, object]:
    return {
        "uid": uid,
        "attachments": [
            {
                "filename": attachment.filename,
                "content_type": attachment.content_type,
                "size_bytes": attachment.size_bytes,
                "part_id": attachment.part_id,
                "content_id": attachment.content_id,
                "disposition": attachment.disposition,
                "saved": False,
            }
            for attachment in attachments
        ],
    }


def _write_json(path: Path, data: dict[str, object]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _extract_links(*texts: str) -> list[str]:
    links: list[str] = []
    for text in texts:
        links.extend(URL_PATTERN.findall(text or ""))
    return links


def _dedupe_keep_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _relative_files(directory: Path) -> list[str]:
    return sorted(
        str(path.relative_to(directory))
        for path in directory.rglob("*")
        if path.is_file()
    )


def _archive_id(uid: str, subject: str) -> str:
    uid_part = re.sub(r"[^A-Za-z0-9_.-]+", "-", uid.strip()).strip("-")
    slug = NON_SLUG_PATTERN.sub("-", _strip_accents(subject.casefold())).strip("-")
    return f"email-{uid_part}-{slug}"[:120].rstrip("-") or f"email-{uid_part}"


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
