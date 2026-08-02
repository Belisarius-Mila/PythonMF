from __future__ import annotations

import gzip
import hashlib
import html
import json
import re
import shutil
import ssl
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from email import message_from_bytes
from email.message import EmailMessage
from email.utils import formatdate
from io import BytesIO
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse, urlunparse
from xml.sax.saxutils import escape


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE_ROOT = PROJECT_ROOT / "data" / "private" / "article_archive"
DEFAULT_LIBRARY_EXPORT_DIR = DEFAULT_ARCHIVE_ROOT / "exports"

CATEGORY_LABELS = {
    "recipes": "Recepty",
    "science": "Vědecké články",
    "health_info": "Zdravotní informace",
    "ai_tools": "Samantha / AI nástroje",
    "travel_places": "Cestování / místa",
    "books": "Knihy",
    "other": "Ostatní",
}

SUPPORTED_ATTACHMENT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
ATTACHMENT_CONFIRMATION_PHRASE = "Potvrzuji připojení obrázku"
ATTACHMENT_REMOVE_CONFIRMATION_PHRASE = "Potvrzuji odebrání přílohy"
DELETE_CONFIRMATION_PHRASE = "Potvrzuji vyřazení z knihovny"
CLEANUP_CONFIRMATION_PHRASE = "Potvrzuji vyčištění článků knihovny"
LIBRARY_EXPORT_EMAIL_MARKER = "X-Samantha-Library-Export"
LIBRARY_EXPORT_EMAIL_MARKER_VALUE = "true"
LIBRARY_EXPORT_SUBJECT_PREFIX = "[SamanthaLibraryExport]"
LIBRARY_EXPORT_SEND_CONFIRMATION_PREFIX = "Potvrzuji odeslání exportu knihovny"
READ_STATES = {"normal", "to_read", "done"}
READ_STATE_LABELS = {
    "normal": "běžné",
    "to_read": "k přečtení",
    "done": "hotovo",
}
SOURCE_REEXTRACT_PREVIEW_ENCODING = "iso-8859-2"
MAX_DECOMPRESSED_HTML_BYTES = 20 * 1024 * 1024


@dataclass(frozen=True)
class ArticleAttachment:
    id: str
    label: str
    kind: str
    role: str
    mime_type: str
    original_file: str
    readable_file: str
    thumb_file: str
    size_bytes: int
    note: str
    created_at: str

    def to_summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "kind": self.kind,
            "role": self.role,
            "mime_type": self.mime_type,
            "has_original": bool(self.original_file),
            "has_readable": bool(self.readable_file),
            "has_thumb": bool(self.thumb_file),
            "size_bytes": self.size_bytes,
            "note": self.note,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class ArticleArchiveItem:
    id: str
    title: str
    one_line_title: str
    category: str
    category_label: str
    archived_at: str
    source_type: str
    source_label: str
    source_note: str
    source_url: str
    canonical_url: str
    text_file: str
    html_file: str
    text_chars: int
    tags: tuple[str, ...]
    book_author: str = ""
    book_location: str = ""
    read_state: str = "normal"
    read_state_label: str = "běžné"
    read_note: str = ""
    read_state_updated_at: str = ""
    attachments: tuple[ArticleAttachment, ...] = ()

    def to_summary(self, snippet: str = "", include_attachments: bool = False) -> dict[str, Any]:
        attachment_types = sorted({attachment.kind for attachment in self.attachments if attachment.kind})
        attachment_roles = sorted({attachment.role for attachment in self.attachments if attachment.role})
        return {
            "id": self.id,
            "title": self.title,
            "one_line_title": self.one_line_title,
            "category": self.category,
            "category_label": self.category_label,
            "archived_at": self.archived_at,
            "source_type": self.source_type,
            "source_label": self.source_label,
            "source_note": self.source_note,
            "source_url": self.source_url,
            "canonical_url": self.canonical_url,
            "text_chars": self.text_chars,
            "tags": list(self.tags),
            "book_author": self.book_author,
            "book_location": self.book_location,
            "snippet": snippet,
            "read_state": self.read_state,
            "read_state_label": self.read_state_label,
            "read_note": self.read_note,
            "read_state_updated_at": self.read_state_updated_at,
            "attachment_count": len(self.attachments),
            "attachment_types": attachment_types,
            "attachment_roles": attachment_roles,
            **(
                {"attachments": [attachment.to_summary() for attachment in self.attachments]}
                if include_attachments
                else {}
            ),
        }


@dataclass(frozen=True)
class ExtractedArticle:
    title: str
    text: str
    canonical_url: str


@dataclass(frozen=True)
class ArticlePdfExportResult:
    export_id: str
    article_id: str
    title: str
    category: str
    pdf_path: Path
    message_path: Path
    metadata_path: Path
    recipient: str
    subject: str
    size_bytes: int

    def to_summary(self) -> dict[str, Any]:
        return {
            "export_id": self.export_id,
            "article_id": self.article_id,
            "title": self.title,
            "category": self.category,
            "pdf_path": str(self.pdf_path),
            "message_path": str(self.message_path),
            "metadata_path": str(self.metadata_path),
            "recipient": self.recipient,
            "subject": self.subject,
            "size_bytes": self.size_bytes,
            "confirmation_text": library_export_confirmation_text(self.export_id),
        }


@dataclass(frozen=True)
class ArticlePdfExportSendResult:
    export_id: str
    recipient: str
    subject: str
    sent_at: str
    sent_copy_status: str
    sent_copy_provider: str
    sent_copy_folder: str
    sent_copy_detail: str = ""

    def to_summary(self) -> dict[str, Any]:
        return {
            "export_id": self.export_id,
            "recipient": self.recipient,
            "subject": self.subject,
            "sent_at": self.sent_at,
            "sent_copy_status": self.sent_copy_status,
            "sent_copy_provider": self.sent_copy_provider,
            "sent_copy_folder": self.sent_copy_folder,
            "sent_copy_detail": self.sent_copy_detail,
        }


class ReadableTextParser(HTMLParser):
    BLOCK_TAGS = {
        "article",
        "aside",
        "blockquote",
        "br",
        "dd",
        "div",
        "dt",
        "figcaption",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "li",
        "main",
        "ol",
        "p",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }
    SKIP_TAGS = {"script", "style", "noscript", "svg"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        text = html.unescape(data)
        if text.strip():
            self.parts.append(text)

    def text(self) -> str:
        raw = "".join(self.parts)
        lines = []
        for line in raw.splitlines():
            cleaned = " ".join(line.split())
            if cleaned:
                lines.append(cleaned)
        return "\n".join(collapse_repeated_lines(lines))


class PreferredReadableTextParser(HTMLParser):
    BLOCK_TAGS = ReadableTextParser.BLOCK_TAGS
    SKIP_TAGS = ReadableTextParser.SKIP_TAGS

    def __init__(self, target: tuple[str, str, str]) -> None:
        super().__init__()
        self.target_tag, self.target_attr, self.target_value = target
        self.parts: list[str] = []
        self.skip_depth = 0
        self.target_depth = 0
        self.found = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.casefold()
        normalized_attrs = {name.casefold(): str(value or "") for name, value in attrs}
        if self.target_depth == 0:
            if (
                normalized_tag == self.target_tag
                and (
                    not self.target_attr
                    or normalized_attrs.get(self.target_attr, "").casefold() == self.target_value
                )
            ):
                self.target_depth = 1
                self.found = True
                if normalized_tag in self.BLOCK_TAGS:
                    self.parts.append("\n")
            return

        if normalized_tag == self.target_tag:
            self.target_depth += 1
        if normalized_tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if normalized_tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self.target_depth == 0:
            return
        normalized_tag = tag.casefold()
        if normalized_tag in self.SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if normalized_tag in self.BLOCK_TAGS:
            self.parts.append("\n")
        if normalized_tag == self.target_tag:
            self.target_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.target_depth == 0 or self.skip_depth:
            return
        text = html.unescape(data)
        if text.strip():
            self.parts.append(text)

    def text(self) -> str:
        if not self.found:
            return ""
        raw = "".join(self.parts)
        lines = []
        for line in raw.splitlines():
            cleaned = " ".join(line.split())
            if cleaned:
                lines.append(cleaned)
        return "\n".join(collapse_repeated_lines(lines))


def collapse_repeated_lines(lines: list[str]) -> list[str]:
    result: list[str] = []
    previous = ""
    repeated = 0
    for line in lines:
        if line == previous:
            repeated += 1
            if repeated > 1:
                continue
        else:
            repeated = 0
        result.append(line)
        previous = line
    return result


def normalize_category(value: str) -> str:
    category = str(value or "").strip().casefold()
    aliases = {
        "recipe": "recipes",
        "recept": "recipes",
        "recepty": "recipes",
        "science": "science",
        "scientific": "science",
        "věda": "science",
        "veda": "science",
        "vědecké články": "science",
        "vedecke clanky": "science",
        "health": "health_info",
        "health_info": "health_info",
        "zdravotní informace": "health_info",
        "zdravotni informace": "health_info",
        "zdraví": "health_info",
        "zdravi": "health_info",
        "ai": "ai_tools",
        "ai tools": "ai_tools",
        "ai_tools": "ai_tools",
        "samantha": "ai_tools",
        "samantha ai": "ai_tools",
        "samantha / ai nástroje": "ai_tools",
        "samantha / ai nastroje": "ai_tools",
        "ai nástroje": "ai_tools",
        "ai nastroje": "ai_tools",
        "openai": "ai_tools",
        "codex": "ai_tools",
        "agents sdk": "ai_tools",
        "travel": "travel_places",
        "travel_places": "travel_places",
        "cestovani": "travel_places",
        "cestování": "travel_places",
        "cestování / místa": "travel_places",
        "cestovani / mista": "travel_places",
        "mista": "travel_places",
        "místa": "travel_places",
        "destinace": "travel_places",
        "vylety": "travel_places",
        "výlety": "travel_places",
        "book": "books",
        "books": "books",
        "kniha": "books",
        "knihy": "books",
        "domácí knihovna": "books",
        "domaci knihovna": "books",
        "other": "other",
        "ostatní": "other",
        "ostatni": "other",
    }
    return aliases.get(category, category if category in CATEGORY_LABELS else "other")


def archive_url(
    *,
    url: str,
    category: str = "other",
    tags: list[str] | None = None,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    timeout: float = 25.0,
) -> dict[str, Any]:
    normalized_url = validate_archive_url(url)
    response_metadata: dict[str, str] = {}
    html_bytes = fetch_url(
        normalized_url,
        timeout=timeout,
        response_metadata=response_metadata,
    )
    article = extract_article(
        html_bytes,
        normalized_url,
        http_encoding=response_metadata.get("charset", ""),
    )
    metadata = write_article_archive(
        source_url=normalized_url,
        html_bytes=html_bytes,
        article=article,
        archive_root=archive_root,
        now=datetime.now(timezone.utc).replace(microsecond=0),
        category=category,
        tags=tags or [],
    )
    return {
        "ok": True,
        "message": "Článek uložen do soukromé knihovny.",
        "item": article_item_from_raw(metadata).to_summary(),
    }


def archive_text_entry(
    *,
    title: str,
    text: str,
    category: str = "other",
    tags: list[str] | None = None,
    source_label: str = "Vložený text",
    source_note: str = "",
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
) -> dict[str, Any]:
    clean_title = compact_title(str(title or ""))
    clean_text = normalize_manual_text(text)
    if not clean_text:
        raise ValueError("Vlož text, který mám uložit.")
    if clean_title == "Bez názvu":
        clean_title = first_text_line(clean_text) or "Vložený text"
    metadata = write_text_archive(
        title=clean_title,
        text=clean_text,
        archive_root=archive_root,
        now=datetime.now(timezone.utc).replace(microsecond=0),
        category=category,
        tags=tags or [],
        source_label=source_label,
        source_note=source_note,
    )
    return {
        "ok": True,
        "message": "Text uložen do znalostní databáze.",
        "item": article_item_from_raw(metadata).to_summary(),
    }


def archive_book_entry(
    *,
    title: str,
    author: str,
    summary: str,
    location: str,
    tags: list[str] | None = None,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
) -> dict[str, Any]:
    clean_title = str(title or "").strip()[:500]
    clean_author = normalize_book_metadata_value(author, "Uveď autora knihy.")
    clean_location = normalize_book_metadata_value(location, "Uveď umístění knihy.")
    clean_summary = normalize_manual_text(summary)
    if not clean_title:
        raise ValueError("Uveď název knihy.")
    if not clean_summary:
        raise ValueError("Vlož stručný obsah knihy.")
    metadata = write_text_archive(
        title=clean_title,
        text=clean_summary,
        archive_root=archive_root,
        now=datetime.now(timezone.utc).replace(microsecond=0),
        category="books",
        tags=tags or [],
        source_label="Domácí knihovna",
        source_note="",
        book_author=clean_author,
        book_location=clean_location,
    )
    return {
        "ok": True,
        "message": "Kniha byla uložena do soukromé knihovny.",
        "item": article_item_from_raw(metadata).to_summary(),
    }


def normalize_book_metadata_value(value: str, missing_message: str) -> str:
    clean = " ".join(str(value or "").split())[:300]
    if not clean:
        raise ValueError(missing_message)
    return clean


def attach_article_image(
    *,
    article_id: str,
    image_path: Path | str | None = None,
    image_bytes: bytes | None = None,
    filename: str = "",
    label: str = "",
    role: str = "handwritten_recipe_scan",
    note: str = "",
    mime_type: str = "",
    tags: list[str] | None = None,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> dict[str, Any]:
    if not user_confirmed or ATTACHMENT_CONFIRMATION_PHRASE.casefold() not in str(confirmation_text).casefold():
        raise ValueError(f"Připojení obrázku vyžaduje potvrzení: {ATTACHMENT_CONFIRMATION_PHRASE}")
    item = find_article(article_id, archive_root=archive_root)
    if item is None:
        raise ValueError("Článek nebyl nalezen.")
    raw_bytes, source_name = read_attachment_input(image_path=image_path, image_bytes=image_bytes, filename=filename)
    extension = normalized_image_extension(source_name, mime_type=mime_type)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    attachment_id = unique_attachment_id(item, label or Path(source_name).stem or "obrazek", now)
    item_dir = archive_root / "articles" / item.id
    original_dir = item_dir / "attachments" / "original"
    readable_dir = item_dir / "attachments" / "readable"
    thumb_dir = item_dir / "attachments" / "thumbs"
    original_dir.mkdir(parents=True, exist_ok=True)
    readable_dir.mkdir(parents=True, exist_ok=True)
    thumb_dir.mkdir(parents=True, exist_ok=True)
    original_path = original_dir / f"{attachment_id}{extension}"
    readable_path = readable_dir / f"{attachment_id}.jpg"
    thumb_path = thumb_dir / f"{attachment_id}.jpg"
    original_path.write_bytes(raw_bytes)
    readable_bytes, thumb_bytes = build_readable_image_versions(raw_bytes)
    readable_path.write_bytes(readable_bytes)
    thumb_path.write_bytes(thumb_bytes)
    attachment = {
        "id": attachment_id,
        "label": str(label or "Doprovodný obrázek").strip()[:160] or "Doprovodný obrázek",
        "kind": "image",
        "role": str(role or "supporting_image").strip()[:80] or "supporting_image",
        "mime_type": mime_type_for_extension(extension),
        "original_file": str(original_path.relative_to(archive_root)),
        "readable_file": str(readable_path.relative_to(archive_root)),
        "thumb_file": str(thumb_path.relative_to(archive_root)),
        "size_bytes": len(raw_bytes),
        "readable_size_bytes": len(readable_bytes),
        "thumb_size_bytes": len(thumb_bytes),
        "note": str(note or "").strip()[:1000],
        "created_at": now.isoformat(),
    }
    metadata = append_attachment_metadata(
        archive_root=archive_root,
        item_id=item.id,
        attachment=attachment,
        tags=tags or [],
    )
    return {
        "ok": True,
        "message": "Obrázek připojen ke znalostní kartě.",
        "item": article_item_from_raw(metadata).to_summary(include_attachments=True),
        "attachment": ArticleAttachment(**{  # type: ignore[arg-type]
            "id": str(attachment["id"]),
            "label": str(attachment["label"]),
            "kind": str(attachment["kind"]),
            "role": str(attachment["role"]),
            "mime_type": str(attachment["mime_type"]),
            "original_file": str(attachment["original_file"]),
            "readable_file": str(attachment["readable_file"]),
            "thumb_file": str(attachment["thumb_file"]),
            "size_bytes": int(attachment["size_bytes"]),
            "note": str(attachment["note"]),
            "created_at": str(attachment["created_at"]),
        }).to_summary(),
    }


def update_article(
    *,
    article_id: str,
    title: str,
    text: str,
    category: str,
    tags: list[str] | None = None,
    source_label: str = "",
    source_note: str = "",
    book_author: str | None = None,
    book_location: str | None = None,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    now: datetime | None = None,
) -> dict[str, Any]:
    item = find_article(article_id, archive_root=archive_root)
    if item is None:
        raise ValueError("Článek nebyl nalezen.")
    clean_title = str(title or "").strip()[:500]
    if not clean_title:
        raise ValueError("Název článku nesmí být prázdný.")
    clean_text = normalize_manual_text(text)
    if not clean_text:
        raise ValueError("Text článku nesmí být prázdný.")
    text_path = resolve_archive_relative_file(archive_root, item.text_file)
    metadata_path = article_metadata_path(item, archive_root=archive_root)
    if text_path is None or not text_path.is_file():
        raise ValueError("Text článku nebyl nalezen.")
    if not metadata_path.is_file():
        raise ValueError("Metadata článku nebyla nalezena.")
    raw = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Metadata článku mají neplatný formát.")
    clean_tags: list[str] = []
    for tag in tags or []:
        clean = str(tag).strip()[:120]
        if clean and clean not in clean_tags:
            clean_tags.append(clean)
    if any(attachment.kind == "image" for attachment in item.attachments) and "ma-obrazek" not in clean_tags:
        clean_tags.append("ma-obrazek")
    normalized_category = normalize_category(category)
    existing_book_author = str(raw.get("book_author", ""))
    existing_book_location = str(raw.get("book_location", ""))
    clean_book_author = " ".join(
        str(existing_book_author if book_author is None else book_author).split()
    )[:300]
    clean_book_location = " ".join(
        str(existing_book_location if book_location is None else book_location).split()
    )[:300]
    if normalized_category == "books":
        if not clean_book_author:
            raise ValueError("Uveď autora knihy.")
        if not clean_book_location:
            raise ValueError("Uveď umístění knihy.")
    raw["title"] = clean_title
    raw["one_line_title"] = compact_title(clean_title)
    raw["category"] = normalized_category
    raw["tags"] = clean_tags
    raw["source_label"] = str(source_label or "").strip()[:160]
    raw["source_note"] = str(source_note or "").strip()[:1000]
    raw["book_author"] = clean_book_author
    raw["book_location"] = clean_book_location
    raw["text_chars"] = str(len(clean_text))
    raw["updated_at"] = (now or datetime.now(timezone.utc)).replace(microsecond=0).isoformat()

    registry_path = archive_root / "registry.jsonl"
    original_text = text_path.read_text(encoding="utf-8")
    original_metadata = metadata_path.read_text(encoding="utf-8")
    original_registry = registry_path.read_text(encoding="utf-8") if registry_path.exists() else None
    try:
        text_path.write_text(clean_text + "\n", encoding="utf-8")
        metadata_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        update_registry(registry_path, raw)
    except Exception:
        text_path.write_text(original_text, encoding="utf-8")
        metadata_path.write_text(original_metadata, encoding="utf-8")
        if original_registry is None:
            registry_path.unlink(missing_ok=True)
        else:
            registry_path.write_text(original_registry, encoding="utf-8")
        raise
    return {
        "ok": True,
        "message": "Úpravy článku byly uloženy.",
        "item": article_item_from_raw(raw).to_summary(include_attachments=True),
        "text": clean_text,
    }


def update_article_attachment(
    *,
    article_id: str,
    attachment_id: str,
    label: str,
    note: str = "",
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    now: datetime | None = None,
) -> dict[str, Any]:
    item = find_article(article_id, archive_root=archive_root)
    if item is None:
        raise ValueError("Článek nebyl nalezen.")
    wanted = slugify(str(attachment_id or "").strip(), max_length=48)
    metadata_path = article_metadata_path(item, archive_root=archive_root)
    if not metadata_path.is_file():
        raise ValueError("Metadata článku nebyla nalezena.")
    original_metadata = metadata_path.read_text(encoding="utf-8")
    raw = json.loads(original_metadata)
    attachments = raw.get("attachments") if isinstance(raw, dict) else None
    if not isinstance(raw, dict) or not isinstance(attachments, list):
        raise ValueError("Metadata příloh mají neplatný formát.")
    updated_attachment: dict[str, Any] | None = None
    for entry in attachments:
        if not isinstance(entry, dict):
            continue
        if slugify(str(entry.get("id", "")).strip(), max_length=48) != wanted:
            continue
        clean_label = str(label or "").strip()[:160]
        if not clean_label:
            raise ValueError("Popisek přílohy nesmí být prázdný.")
        entry["label"] = clean_label
        entry["note"] = str(note or "").strip()[:1000]
        entry["updated_at"] = (now or datetime.now(timezone.utc)).replace(microsecond=0).isoformat()
        updated_attachment = entry
        break
    if updated_attachment is None:
        raise ValueError("Příloha nebyla nalezena.")
    registry_path = archive_root / "registry.jsonl"
    original_registry = registry_path.read_text(encoding="utf-8") if registry_path.exists() else None
    try:
        metadata_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        update_registry(registry_path, raw)
    except Exception:
        metadata_path.write_text(original_metadata, encoding="utf-8")
        if original_registry is None:
            registry_path.unlink(missing_ok=True)
        else:
            registry_path.write_text(original_registry, encoding="utf-8")
        raise
    updated_item = article_item_from_raw(raw)
    attachment = next(entry for entry in updated_item.attachments if entry.id == wanted)
    return {
        "ok": True,
        "message": "Popisek přílohy byl uložen.",
        "item": updated_item.to_summary(include_attachments=True),
        "attachment": attachment.to_summary(),
    }


def remove_article_attachment(
    *,
    article_id: str,
    attachment_id: str,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    now: datetime | None = None,
) -> dict[str, Any]:
    if (
        not user_confirmed
        or str(confirmation_text or "").strip().casefold() != ATTACHMENT_REMOVE_CONFIRMATION_PHRASE.casefold()
    ):
        raise ValueError(f"Odebrání přílohy vyžaduje přesné potvrzení: {ATTACHMENT_REMOVE_CONFIRMATION_PHRASE}")
    item = find_article(article_id, archive_root=archive_root)
    if item is None:
        raise ValueError("Článek nebyl nalezen.")
    wanted = slugify(str(attachment_id or "").strip(), max_length=48)
    metadata_path = article_metadata_path(item, archive_root=archive_root)
    if not metadata_path.is_file():
        raise ValueError("Metadata článku nebyla nalezena.")
    original_metadata = metadata_path.read_text(encoding="utf-8")
    raw = json.loads(original_metadata)
    attachments = raw.get("attachments") if isinstance(raw, dict) else None
    if not isinstance(raw, dict) or not isinstance(attachments, list):
        raise ValueError("Metadata příloh mají neplatný formát.")
    removed: dict[str, Any] | None = None
    remaining: list[Any] = []
    for entry in attachments:
        if (
            removed is None
            and isinstance(entry, dict)
            and slugify(str(entry.get("id", "")).strip(), max_length=48) == wanted
        ):
            removed = entry
        else:
            remaining.append(entry)
    if removed is None:
        raise ValueError("Příloha nebyla nalezena.")

    removed_at = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    trash_root = archive_root / "trash" / "attachments"
    trash_root.mkdir(parents=True, exist_ok=True)
    trash_dir = next_trash_path(
        trash_root / f"{removed_at.strftime('%Y%m%d_%H%M%S')}_{item.id}_{wanted}"
    )
    moved_files: list[tuple[Path, Path, str]] = []
    seen_sources: set[Path] = set()
    manifest_path = trash_dir / "removed_attachment.json"
    attachment_root = (archive_root / "articles" / item.id / "attachments").resolve()
    try:
        for field in ("original_file", "readable_file", "thumb_file"):
            source = resolve_archive_relative_file(archive_root, str(removed.get(field, "")))
            if source is None or not source.is_file() or source in seen_sources:
                continue
            if attachment_root not in source.parents:
                raise ValueError("Soubor přílohy je mimo bezpečný adresář článku.")
            seen_sources.add(source)
            target = trash_dir / field / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
            moved_files.append((source, target, field))

        trash_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "article_id": item.id,
            "attachment": removed,
            "removed_at": removed_at.isoformat(),
            "moved_files": {
                field: str(target.relative_to(archive_root))
                for _source, target, field in moved_files
            },
        }
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        raw["attachments"] = remaining
        if not any(isinstance(entry, dict) and str(entry.get("kind", "")).casefold() == "image" for entry in remaining):
            tags = raw.get("tags", [])
            if isinstance(tags, list):
                raw["tags"] = [tag for tag in tags if str(tag).strip().casefold() != "ma-obrazek"]
        raw["updated_at"] = removed_at.isoformat()
        registry_path = archive_root / "registry.jsonl"
        original_registry = registry_path.read_text(encoding="utf-8") if registry_path.exists() else None
        try:
            metadata_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            update_registry(registry_path, raw)
        except Exception:
            metadata_path.write_text(original_metadata, encoding="utf-8")
            if original_registry is None:
                registry_path.unlink(missing_ok=True)
            else:
                registry_path.write_text(original_registry, encoding="utf-8")
            raise
    except Exception:
        for source, target, _field in reversed(moved_files):
            source.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                shutil.move(str(target), str(source))
        manifest_path.unlink(missing_ok=True)
        raise
    updated_item = article_item_from_raw(raw)
    return {
        "ok": True,
        "message": "Příloha byla odebrána z článku a přesunuta do soukromého koše.",
        "item": updated_item.to_summary(include_attachments=True),
        "attachment_id": wanted,
    }


def read_attachment_input(
    *,
    image_path: Path | str | None,
    image_bytes: bytes | None,
    filename: str,
) -> tuple[bytes, str]:
    if image_bytes is not None:
        if not image_bytes:
            raise ValueError("Obrázek je prázdný.")
        return image_bytes, filename or "attachment.jpg"
    if image_path is None:
        raise ValueError("Zadej cestu k obrázku nebo image_bytes.")
    path = Path(image_path).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise ValueError(f"Obrázek neexistuje: {path}")
    if path.suffix.casefold() not in SUPPORTED_ATTACHMENT_EXTENSIONS:
        raise ValueError("Podporované přílohy jsou JPG, PNG, WEBP, HEIC/HEIF.")
    return path.read_bytes(), path.name


def normalized_image_extension(filename: str, *, mime_type: str = "") -> str:
    suffix = Path(filename or "").suffix.casefold()
    if suffix in SUPPORTED_ATTACHMENT_EXTENSIONS:
        return ".jpg" if suffix == ".jpeg" else suffix
    normalized_mime = str(mime_type or "").casefold()
    if normalized_mime == "image/png":
        return ".png"
    if normalized_mime == "image/webp":
        return ".webp"
    if normalized_mime in {"image/heic", "image/heif"}:
        return ".heic"
    return ".jpg"


def mime_type_for_extension(extension: str) -> str:
    suffix = extension.casefold()
    if suffix == ".pdf":
        return "application/pdf"
    if suffix == ".txt":
        return "text/plain; charset=utf-8"
    if suffix == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    if suffix in {".heic", ".heif"}:
        return "image/heic"
    return "image/jpeg"


def unique_attachment_id(item: ArticleArchiveItem, label: str, now: datetime) -> str:
    base = slugify(label or "obrazek", max_length=44)
    existing = {attachment.id for attachment in item.attachments}
    suffix = hashlib.sha256(f"{item.id}\n{label}\n{now.isoformat()}".encode("utf-8")).hexdigest()[:6]
    candidate = slugify(f"{base}-{suffix}", max_length=52)
    counter = 2
    while candidate in existing:
        candidate = slugify(f"{base}-{suffix}-{counter}", max_length=56)
        counter += 1
    return candidate


def build_readable_image_versions(raw_bytes: bytes) -> tuple[bytes, bytes]:
    try:
        from PIL import Image, ImageOps
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on local environment setup
        raise ValueError("Pillow není nainstalovaný, nejde vytvořit čitelnou kopii obrázku.") from exc
    image = Image.open(BytesIO(raw_bytes))
    image = ImageOps.exif_transpose(image)
    readable = prepare_image_for_jpeg(image)
    readable.thumbnail((2600, 2600), Image.Resampling.LANCZOS)
    thumb = prepare_image_for_jpeg(image.copy())
    thumb.thumbnail((520, 520), Image.Resampling.LANCZOS)
    return encode_jpeg(readable, quality=88), encode_jpeg(thumb, quality=78)


def prepare_image_for_jpeg(image: Any) -> Any:
    if image.mode in {"RGBA", "LA", "P"}:
        rgba = image.convert("RGBA")
        try:
            from PIL import Image
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise ValueError("Pillow není nainstalovaný.") from exc
        background = Image.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    if image.mode != "RGB":
        return image.convert("RGB")
    return image


def encode_jpeg(image: Any, *, quality: int) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True, progressive=True)
    return buffer.getvalue()


def append_attachment_metadata(
    *,
    archive_root: Path,
    item_id: str,
    attachment: dict[str, Any],
    tags: list[str],
) -> dict[str, Any]:
    metadata_path = archive_root / "articles" / item_id / "metadata.json"
    if not metadata_path.exists():
        raise ValueError("Metadata článku nebyla nalezena.")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise ValueError("Metadata článku mají neplatný formát.")
    attachments = metadata.get("attachments", [])
    if not isinstance(attachments, list):
        attachments = []
    attachments.append(attachment)
    metadata["attachments"] = attachments
    existing_tags = [str(tag).strip() for tag in metadata.get("tags", []) if str(tag).strip()] if isinstance(metadata.get("tags"), list) else []
    for tag in tags:
        clean = str(tag).strip()
        if clean and clean not in existing_tags:
            existing_tags.append(clean)
    if attachments and "ma-obrazek" not in existing_tags:
        existing_tags.append("ma-obrazek")
    metadata["tags"] = existing_tags
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_registry(archive_root / "registry.jsonl", metadata)
    return metadata


def validate_archive_url(url: str) -> str:
    value = str(url or "").strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Zadej platnou http/https URL.")
    return value


def fetch_url(
    url: str,
    timeout: float = 25.0,
    *,
    response_metadata: dict[str, str] | None = None,
) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "SamanthaAgentArticleArchive/1.0 (+local personal archive)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = str(response.headers.get("Content-Type", "") or "")
            content_encoding = str(response.headers.get("Content-Encoding", "") or "")
            record_http_content_type(response_metadata, content_type)
            record_http_content_encoding(response_metadata, content_encoding)
            return decompress_http_body(
                response.read(),
                content_encoding=content_encoding,
            )
    except urllib.error.URLError as exc:
        if not is_certificate_verify_failure(exc):
            raise
        return fetch_url_with_curl(
            url,
            timeout=timeout,
            response_metadata=response_metadata,
        )


def is_certificate_verify_failure(exc: urllib.error.URLError) -> bool:
    reason = getattr(exc, "reason", None)
    return isinstance(reason, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in str(exc)


def fetch_url_with_curl(
    url: str,
    timeout: float = 25.0,
    *,
    response_metadata: dict[str, str] | None = None,
) -> bytes:
    completed = subprocess.run(
        [
            "curl",
            "--fail",
            "--location",
            "--silent",
            "--show-error",
            "--max-time",
            str(max(1, int(timeout))),
            "--dump-header",
            "-",
            url,
        ],
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        message = completed.stderr.decode("utf-8", errors="replace").strip()
        raise urllib.error.URLError(message or f"curl failed with exit {completed.returncode}")
    html_bytes, content_type, content_encoding = split_curl_headers(completed.stdout)
    record_http_content_type(response_metadata, content_type)
    record_http_content_encoding(response_metadata, content_encoding)
    return decompress_http_body(
        html_bytes,
        content_encoding=content_encoding,
    )


def record_http_content_type(
    response_metadata: dict[str, str] | None,
    content_type: str,
) -> None:
    if response_metadata is None:
        return
    clean_content_type = str(content_type or "").strip()
    if clean_content_type:
        response_metadata["content_type"] = clean_content_type
    match = re.search(
        r"(?:^|;)\s*charset\s*=\s*[\"']?([a-zA-Z0-9._:-]+)",
        clean_content_type,
        flags=re.I,
    )
    if match:
        response_metadata["charset"] = match.group(1).strip()


def record_http_content_encoding(
    response_metadata: dict[str, str] | None,
    content_encoding: str,
) -> None:
    if response_metadata is None:
        return
    clean_content_encoding = str(content_encoding or "").strip()
    if clean_content_encoding:
        response_metadata["content_encoding"] = clean_content_encoding


def split_curl_headers(payload: bytes) -> tuple[bytes, str, str]:
    body = payload
    content_type = ""
    content_encoding = ""
    while body.startswith(b"HTTP/"):
        separator = re.search(br"\r?\n\r?\n", body)
        if separator is None:
            break
        header_block = body[: separator.start()]
        body = body[separator.end() :]
        block_content_type = ""
        block_content_encoding = ""
        for line in header_block.splitlines()[1:]:
            name, separator_byte, value = line.partition(b":")
            if not separator_byte:
                continue
            normalized_name = name.strip().lower()
            decoded_value = value.decode("latin-1", errors="replace").strip()
            if normalized_name == b"content-type":
                block_content_type = decoded_value
            elif normalized_name == b"content-encoding":
                block_content_encoding = decoded_value
        content_type = block_content_type
        content_encoding = block_content_encoding
    return body, content_type, content_encoding


def decompress_http_body(
    payload: bytes,
    *,
    content_encoding: str = "",
    max_decompressed_bytes: int = MAX_DECOMPRESSED_HTML_BYTES,
) -> bytes:
    encodings = [
        part.strip().casefold()
        for part in str(content_encoding or "").split(",")
        if part.strip() and part.strip().casefold() != "identity"
    ]
    if not encodings and payload.startswith(b"\x1f\x8b"):
        encodings = ["gzip"]
    unsupported = [encoding for encoding in encodings if encoding not in {"gzip", "x-gzip"}]
    if unsupported:
        raise OSError("HTTP odpověď používá nepodporované komprimované kódování.")

    body = payload
    for _encoding in reversed(encodings):
        try:
            with gzip.GzipFile(fileobj=BytesIO(body)) as compressed:
                decompressed = compressed.read(max_decompressed_bytes + 1)
        except (EOFError, OSError) as exc:
            raise OSError("Gzip HTTP odpověď je poškozená.") from exc
        if len(decompressed) > max_decompressed_bytes:
            raise OSError("Rozbalená HTTP odpověď překračuje bezpečný velikostní limit.")
        body = decompressed
    return body


def extract_article(
    html_bytes: bytes,
    source_url: str,
    *,
    http_encoding: str = "",
) -> ExtractedArticle:
    html_bytes = decompress_http_body(html_bytes)
    html_text = decode_html_document(html_bytes, http_encoding=http_encoding)
    title = extract_title(html_text) or urlparse(source_url).netloc or "article"
    canonical = extract_canonical_url(html_text) or strip_tracking_query(source_url)
    text = extract_preferred_readable_text(html_text)
    if not text:
        parser = ReadableTextParser()
        parser.feed(html_text)
        text = parser.text()
    text = trim_to_article_body(text, title)
    return ExtractedArticle(title=title, text=text, canonical_url=canonical)


def decode_html_document(html_bytes: bytes, *, http_encoding: str = "") -> str:
    if html_bytes.startswith(b"\xef\xbb\xbf"):
        return html_bytes.decode("utf-8-sig", errors="replace")

    declared_encoding = detect_html_declared_encoding(html_bytes)
    candidates = [http_encoding, declared_encoding, "utf-8", "windows-1250", "iso-8859-2"]
    tried: set[str] = set()
    for encoding in candidates:
        if not encoding:
            continue
        normalized = encoding.strip().lower()
        if normalized in tried:
            continue
        tried.add(normalized)
        try:
            return html_bytes.decode(normalized)
        except (LookupError, UnicodeDecodeError):
            continue
    return html_bytes.decode("utf-8", errors="replace")


def detect_html_declared_encoding(html_bytes: bytes) -> str:
    head = html_bytes[:4096].decode("ascii", errors="ignore")
    match = re.search(r"<meta[^>]+charset=[\"']?\s*([a-zA-Z0-9._:-]+)", head, flags=re.I)
    if match:
        return match.group(1).strip()
    match = re.search(
        r"<meta[^>]+http-equiv=[\"']content-type[\"'][^>]+content=[\"'][^\"']*charset=([a-zA-Z0-9._:-]+)",
        head,
        flags=re.I,
    )
    if match:
        return match.group(1).strip()
    return ""


def extract_preferred_readable_text(html_text: str) -> str:
    preferred_targets = (
        ("div", "id", "clanek"),
        ("article", "", ""),
        ("main", "", ""),
    )
    for target in preferred_targets:
        parser = PreferredReadableTextParser(target)
        parser.feed(html_text)
        text = parser.text().strip()
        if text:
            return text
    return ""


def extract_title(html_text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text, flags=re.I | re.S)
    if not match:
        return ""
    title = html.unescape(re.sub(r"\s+", " ", match.group(1))).strip()
    return title


def extract_canonical_url(html_text: str) -> str:
    match = re.search(
        r"<link[^>]+rel=[\"']canonical[\"'][^>]+href=[\"']([^\"']+)[\"']",
        html_text,
        flags=re.I,
    )
    if not match:
        return ""
    return html.unescape(match.group(1)).strip()


def strip_tracking_query(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def trim_to_article_body(text: str, title: str) -> str:
    lines = text.splitlines()
    if not lines:
        return ""
    start = detect_article_start(lines, title)
    body_lines = clean_article_lines(lines[start:])
    body_lines = remove_article_boilerplate(body_lines)
    return "\n".join(body_lines).strip()


def clean_article_lines(lines: list[str]) -> list[str]:
    ignored_lines = {"postranní panel", "postranni panel", "."}
    cleaned = [line for line in lines if line.strip().casefold() not in ignored_lines]
    while cleaned and cleaned[0].strip().casefold() in ignored_lines:
        cleaned.pop(0)
    return cleaned


HARD_TAIL_MARKERS = (
    "Související produkty",
    "Diskuze",
    "Přidat komentář",
    "Komentář (",
    "Komentáře",
    "Newsletter",
    "Naposledy navštívené",
    "Hlídací pes",
    "Podobné produkty",
    "Související články",
    "Předchozí článek",
    "Previous",
    "Trendy podle kategorie",
    "Nejčtenější",
    "Google Trends",
    "Aktuální události",
    "Politický systém",
    "Místní",
    "Zobrazit více",
    "Domovská stránka",
    "Centrum nápovědy",
    "Odeslat zpětnou vazbu",
    "Zápatí",
    "Sector 31",
    "Vytvořil Shoptet",
    "Copyright",
)

INLINE_RECOMMENDATION_MARKERS = (
    "Mohlo by vás zajímat",
    "Mohlo by vas zajimat",
    "Mohlo by se vám hodit",
    "Mohlo by se vam hodit",
)

INLINE_RELATED_CATEGORY_MARKERS = {
    "auto moto",
    "cestování",
    "cestovani",
    "dítě a rodina",
    "dite a rodina",
    "domácí",
    "domaci",
    "ekonomika",
    "finance",
    "internet a pc",
    "koktejl",
    "kultura",
    "muži",
    "muzi",
    "novinky",
    "reality",
    "sport",
    "věda a školy",
    "veda a skoly",
    "zahraniční",
    "zahranicni",
    "zdraví",
    "zdravi",
    "žena",
    "zena",
}


def remove_article_boilerplate(lines: list[str]) -> list[str]:
    without_inline_recommendations = remove_inline_recommendation_blocks(lines)
    without_related_cards = remove_inline_related_article_cards(without_inline_recommendations)
    without_share_blocks = remove_social_share_blocks(without_related_cards)
    without_metadata_noise = remove_translated_metadata_noise(without_share_blocks)
    without_labels = [
        line
        for line in without_metadata_noise
        if not line.strip().casefold().startswith(("štítek:", "stitek:"))
    ]
    tail_start = detect_article_tail_start(without_labels)
    return without_labels[:tail_start]


def remove_inline_recommendation_blocks(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    skip_recommendation_lines = 0
    for line in lines:
        folded = line.strip().casefold()
        if any(marker.casefold() in folded for marker in INLINE_RECOMMENDATION_MARKERS):
            skip_recommendation_lines = 3
            continue
        if skip_recommendation_lines > 0:
            skip_recommendation_lines -= 1
            continue
        cleaned.append(line)
    return cleaned


def remove_inline_related_article_cards(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    content_like_lines = 0
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""
        folded_next = next_line.casefold()
        if len(line) > 90:
            content_like_lines += 1
        if (
            content_like_lines >= 2
            and 35 <= len(line) <= 180
            and folded_next in INLINE_RELATED_CATEGORY_MARKERS
        ):
            index += 2
            continue
        cleaned.append(lines[index])
        index += 1
    return cleaned


def remove_social_share_blocks(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        folded = line.casefold()
        if folded.startswith("sledujte ") and " na" in folded:
            index += 1
            while index < len(lines) and lines[index].strip().casefold() in {"google", "news", "0"}:
                index += 1
            continue
        cleaned.append(lines[index])
        index += 1
    return cleaned


def remove_translated_metadata_noise(lines: list[str]) -> list[str]:
    if len(lines) >= 3 and lines[1].strip().casefold() in {"jeden", "one"} and looks_like_byline(lines[2]):
        return [lines[0], *lines[2:]]
    return lines


def looks_like_byline(line: str) -> bool:
    folded = line.strip().casefold()
    return "•" in folded or bool(re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", folded))


def detect_article_tail_start(lines: list[str]) -> int:
    source_seen = False
    content_like_lines = 0
    for index, line in enumerate(lines):
        clean = line.strip()
        folded = clean.casefold()
        if not clean:
            continue
        if folded.startswith(("zdroj:", "podle ")):
            source_seen = True
        if len(clean) > 90:
            content_like_lines += 1
        if source_seen and folded.startswith("sledujte "):
            return index
        if (index >= 5 or content_like_lines >= 2) and any(
            marker.casefold() == folded or folded.startswith(marker.casefold()) for marker in HARD_TAIL_MARKERS
        ):
            return index
        if content_like_lines >= 3 and folded in {"next", "další", "dalsi"}:
            return index
    return len(lines)


def detect_article_start(lines: list[str], title: str) -> int:
    main_content_start = detect_main_content_start(lines)
    if main_content_start >= 0:
        return main_content_start

    title_head = title.split("|", 1)[0].strip()
    title_words = significant_words(title_head)
    candidates: list[tuple[int, int]] = []

    for index, line in enumerate(lines):
        folded = line.casefold()
        if index > 10 and "domů/" in folded and title_words:
            score = matching_word_count(folded, title_words)
            if score >= min(2, len(title_words)):
                candidates.append((95 + score, min(index + 1, len(lines) - 1)))
        if index > 10 and title_words:
            score = matching_word_count(folded, title_words)
            if score >= min(3, len(title_words)) and len(line) <= 180:
                candidates.append((80 + score, index))
        if index > 10 and title_head and title_head.casefold() in folded:
            candidates.append((70, index))

    if candidates:
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    for index, line in enumerate(lines):
        if index > 10 and title_head and title_head.casefold() in line.casefold():
            return index
    return 0


def detect_main_content_start(lines: list[str]) -> int:
    for index, line in enumerate(lines):
        folded = line.strip().casefold()
        if folded in {"hlavní obsah", "hlavni obsah", "main content"}:
            return min(index + 1, len(lines) - 1)
    return -1


def significant_words(value: str) -> list[str]:
    words = re.findall(r"[0-9A-Za-zÁ-ž]{4,}", value.casefold())
    ignored = {"postup", "postupy", "navody", "návody", "praha", "naradi", "nářadí"}
    return [word for word in words if word not in ignored]


def matching_word_count(folded_line: str, words: list[str]) -> int:
    return sum(1 for word in words if word in folded_line)


def slugify(value: str, max_length: int = 72) -> str:
    table = str.maketrans(
        "áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ",
        "acdeeinorstuuyzACDEEINORSTUUYZ",
    )
    ascii_text = value.translate(table)
    slug = re.sub(r"[^A-Za-z0-9]+", "-", ascii_text).strip("-").lower()
    return (slug or "article")[:max_length].strip("-") or "article"


def article_id(title: str, canonical_url: str, now: datetime) -> str:
    digest = hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()[:8]
    return f"{now.date().isoformat()}_{slugify(title)}_{digest}"


def text_entry_id(title: str, text: str, now: datetime) -> str:
    digest_source = f"{title}\n{text}\n{now.isoformat()}"
    digest = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()[:8]
    return f"{now.date().isoformat()}_{slugify(title)}_{digest}"


def write_article_archive(
    *,
    source_url: str,
    html_bytes: bytes,
    article: ExtractedArticle,
    archive_root: Path,
    now: datetime,
    category: str,
    tags: list[str],
) -> dict[str, Any]:
    item_id = article_id(article.title, article.canonical_url or source_url, now)
    item_dir = archive_root / "articles" / item_id
    item_dir.mkdir(parents=True, exist_ok=True)
    html_path = item_dir / "source.html"
    text_path = item_dir / "article.txt"
    metadata_path = item_dir / "metadata.json"
    html_path.write_bytes(html_bytes)
    text_path.write_text(article.text + "\n", encoding="utf-8")
    metadata: dict[str, Any] = {
        "id": item_id,
        "title": article.title,
        "one_line_title": compact_title(article.title),
        "category": normalize_category(category),
        "tags": [str(tag).strip() for tag in tags if str(tag).strip()],
        "source_url": source_url,
        "canonical_url": article.canonical_url,
        "archived_at": now.isoformat(),
        "text_file": str(text_path.relative_to(archive_root)),
        "html_file": str(html_path.relative_to(archive_root)),
        "text_chars": str(len(article.text)),
        "read_state": "normal",
        "read_note": "",
        "read_state_updated_at": "",
        "attachments": [],
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_registry(archive_root / "registry.jsonl", metadata)
    return metadata


def write_text_archive(
    *,
    title: str,
    text: str,
    archive_root: Path,
    now: datetime,
    category: str,
    tags: list[str],
    source_label: str,
    source_note: str,
    book_author: str = "",
    book_location: str = "",
) -> dict[str, Any]:
    clean_text = normalize_manual_text(text)
    item_id = text_entry_id(title, clean_text, now)
    item_dir = archive_root / "articles" / item_id
    item_dir.mkdir(parents=True, exist_ok=True)
    text_path = item_dir / "article.txt"
    metadata_path = item_dir / "metadata.json"
    text_path.write_text(clean_text + "\n", encoding="utf-8")
    metadata: dict[str, Any] = {
        "id": item_id,
        "title": title,
        "one_line_title": compact_title(title),
        "category": normalize_category(category),
        "tags": [str(tag).strip() for tag in tags if str(tag).strip()],
        "source_type": "manual_text",
        "source_label": str(source_label or "Vložený text").strip()[:160] or "Vložený text",
        "source_note": str(source_note or "").strip()[:1000],
        "book_author": " ".join(str(book_author or "").split())[:300],
        "book_location": " ".join(str(book_location or "").split())[:300],
        "source_url": "",
        "canonical_url": "",
        "archived_at": now.isoformat(),
        "text_file": str(text_path.relative_to(archive_root)),
        "html_file": "",
        "text_chars": str(len(clean_text)),
        "read_state": "normal",
        "read_note": "",
        "read_state_updated_at": "",
        "attachments": [],
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_registry(archive_root / "registry.jsonl", metadata)
    return metadata


def update_registry(path: Path, metadata: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    replaced = False
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(item.get("id", "")) == metadata["id"]:
                rows.append(metadata)
                replaced = True
            elif isinstance(item, dict):
                rows.append(item)
    if not replaced:
        rows.append(metadata)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def remove_from_registry(path: Path, item_id: str) -> dict[str, Any] | None:
    wanted = str(item_id or "").strip()
    if not wanted or not path.exists():
        return None
    rows: list[dict[str, Any]] = []
    removed: dict[str, Any] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(item, dict):
            continue
        if str(item.get("id", "")).strip() == wanted:
            removed = item
            continue
        rows.append(item)
    if removed is not None:
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )
    return removed


def load_article_registry(archive_root: Path = DEFAULT_ARCHIVE_ROOT) -> list[ArticleArchiveItem]:
    path = archive_root / "registry.jsonl"
    if not path.exists():
        return []
    items: list[ArticleArchiveItem] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(raw, dict):
            continue
        item = article_item_from_raw(raw)
        if item.id and item.text_file:
            items.append(item)
    items.sort(key=article_sort_key, reverse=True)
    return items


def article_item_from_raw(raw: dict[str, Any]) -> ArticleArchiveItem:
    category = normalize_category(str(raw.get("category", "")))
    tags = raw.get("tags", [])
    if isinstance(tags, str):
        tags_tuple = tuple(part.strip() for part in tags.split(",") if part.strip())
    elif isinstance(tags, list):
        tags_tuple = tuple(str(part).strip() for part in tags if str(part).strip())
    else:
        tags_tuple = ()
    attachments = normalize_attachments(raw.get("attachments", []))
    title = str(raw.get("title", "")).strip()
    one_line_title = str(raw.get("one_line_title", "")).strip() or compact_title(title)
    source_url = str(raw.get("source_url", "")).strip()
    canonical_url = str(raw.get("canonical_url", "")).strip()
    source_type = str(raw.get("source_type", "")).strip() or ("url" if source_url or canonical_url else "manual_text")
    source_label = str(raw.get("source_label", "")).strip()
    if not source_label:
        source_label = "URL článek" if source_type == "url" else "Vložený text"
    try:
        text_chars = int(raw.get("text_chars", 0) or 0)
    except (TypeError, ValueError):
        text_chars = 0
    read_state = normalize_read_state(str(raw.get("read_state", "normal")))
    return ArticleArchiveItem(
        id=str(raw.get("id", "")).strip(),
        title=title,
        one_line_title=one_line_title,
        category=category,
        category_label=CATEGORY_LABELS[category],
        archived_at=str(raw.get("archived_at", "")).strip(),
        source_type=source_type,
        source_label=source_label,
        source_note=str(raw.get("source_note", "")).strip(),
        source_url=source_url,
        canonical_url=canonical_url,
        text_file=str(raw.get("text_file", "")).strip(),
        html_file=str(raw.get("html_file", "")).strip(),
        text_chars=text_chars,
        tags=tags_tuple,
        book_author=str(raw.get("book_author", "")).strip(),
        book_location=str(raw.get("book_location", "")).strip(),
        read_state=read_state,
        read_state_label=READ_STATE_LABELS[read_state],
        read_note=str(raw.get("read_note", "")).strip(),
        read_state_updated_at=str(raw.get("read_state_updated_at", "")).strip(),
        attachments=attachments,
    )


def normalize_read_state(value: str) -> str:
    state = str(value or "").strip().casefold().replace("-", "_")
    aliases = {
        "read": "to_read",
        "todo": "to_read",
        "to-read": "to_read",
        "k_precteni": "to_read",
        "k přečtení": "to_read",
        "k precteni": "to_read",
        "prectist": "to_read",
        "přečíst": "to_read",
        "done": "done",
        "hotovo": "done",
        "read_done": "done",
        "normal": "normal",
        "none": "normal",
        "bezne": "normal",
        "běžné": "normal",
    }
    return aliases.get(state, state if state in READ_STATES else "normal")


def normalize_attachments(raw: Any) -> tuple[ArticleAttachment, ...]:
    if not isinstance(raw, list):
        return ()
    attachments: list[ArticleAttachment] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            continue
        attachment_id = slugify(str(item.get("id", "")).strip() or f"attachment-{index}", max_length=48)
        try:
            size_bytes = int(item.get("size_bytes", 0) or 0)
        except (TypeError, ValueError):
            size_bytes = 0
        attachments.append(
            ArticleAttachment(
                id=attachment_id,
                label=str(item.get("label", "")).strip()[:160] or f"Příloha {index}",
                kind=str(item.get("kind", "")).strip()[:80] or "image",
                role=str(item.get("role", "")).strip()[:80] or "supporting",
                mime_type=str(item.get("mime_type", "")).strip()[:120] or "application/octet-stream",
                original_file=str(item.get("original_file", "")).strip(),
                readable_file=str(item.get("readable_file", "")).strip(),
                thumb_file=str(item.get("thumb_file", "")).strip(),
                size_bytes=max(0, size_bytes),
                note=str(item.get("note", "")).strip()[:1000],
                created_at=str(item.get("created_at", "")).strip(),
            )
        )
    return tuple(attachments)


def compact_title(title: str) -> str:
    head = title.split("|", 1)[0].strip()
    return head or title.strip() or "Bez názvu"


def normalize_manual_text(text: str) -> str:
    lines = []
    for line in str(text or "").replace("\r\n", "\n").replace("\r", "\n").splitlines():
        lines.append(line.rstrip())
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines).strip()


def first_text_line(text: str) -> str:
    for line in text.splitlines():
        clean = line.strip()
        if clean:
            return compact_title(clean[:120])
    return ""


def article_sort_key(item: ArticleArchiveItem) -> tuple[str, str]:
    return (normalized_datetime(item.archived_at), item.id)


def normalized_datetime(value: str) -> str:
    if not value:
        return ""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return value


def list_articles(
    *,
    category: str = "other",
    read_state: str = "",
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    limit: int = 200,
) -> dict[str, Any]:
    wanted = "all" if str(category or "").strip().casefold() == "all" else normalize_category(category)
    wanted_read_state = normalize_read_state(read_state) if str(read_state or "").strip() else ""
    items = [
        item.to_summary()
        for item in load_article_registry(archive_root)
        if (wanted == "all" or item.category == wanted)
        and (not wanted_read_state or item.read_state == wanted_read_state)
    ]
    return {
        "ok": True,
        "category": wanted,
        "category_label": CATEGORY_LABELS[wanted] if wanted != "all" else "Vše",
        "read_state": wanted_read_state,
        "read_state_label": READ_STATE_LABELS[wanted_read_state] if wanted_read_state else "",
        "items": items[: max(1, min(limit, 500))],
        "count": len(items),
    }


def search_articles(
    *,
    query: str,
    category: str = "all",
    read_state: str = "",
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    limit: int = 50,
) -> dict[str, Any]:
    terms = [term.casefold() for term in query.split() if term.strip()]
    if not terms:
        return {"ok": True, "query": query, "items": [], "count": 0}
    wanted = normalize_category(category) if category != "all" else "all"
    wanted_read_state = normalize_read_state(read_state) if str(read_state or "").strip() else ""
    results: list[tuple[int, ArticleArchiveItem, str]] = []
    for item in load_article_registry(archive_root):
        if wanted != "all" and item.category != wanted:
            continue
        if wanted_read_state and item.read_state != wanted_read_state:
            continue
        text = read_article_text(item.id, archive_root=archive_root, max_chars=0)
        folded = text.casefold()
        source_folded = " ".join([item.source_label, item.source_note]).casefold()
        tags_folded = " ".join(item.tags).casefold()
        book_metadata_folded = (
            " ".join([item.book_author, item.book_location]).casefold()
            if item.category == "books"
            else ""
        )
        score = sum(folded.count(term) for term in terms)
        title_score = sum(item.one_line_title.casefold().count(term) for term in terms) * 3
        source_score = sum(source_folded.count(term) for term in terms) * 2
        tag_score = sum(tags_folded.count(term) for term in terms) * 2
        book_metadata_score = sum(
            book_metadata_folded.count(term) for term in terms
        ) * 3
        total_score = score + title_score + source_score + tag_score + book_metadata_score
        if total_score <= 0:
            continue
        results.append((total_score, item, make_snippet(text, terms)))
    results.sort(key=lambda row: row[0], reverse=True)
    limited = results[: max(1, min(limit, 200))]
    return {
        "ok": True,
        "query": query,
        "category": wanted,
        "read_state": wanted_read_state,
        "read_state_label": READ_STATE_LABELS[wanted_read_state] if wanted_read_state else "",
        "items": [
            {
                **item.to_summary(snippet=snippet),
                "score": score,
            }
            for score, item, snippet in limited
        ],
        "count": len(results),
    }


def get_article(
    *,
    article_id: str,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    max_chars: int = 40000,
) -> dict[str, Any]:
    item = find_article(article_id, archive_root=archive_root)
    if item is None:
        return {"ok": False, "error": "not_found", "message": "Článek nebyl nalezen."}
    read_limit = max_chars + 1 if max_chars > 0 else 0
    text = read_article_text(item.id, archive_root=archive_root, max_chars=read_limit)
    truncated = max_chars > 0 and len(text) > max_chars
    if truncated:
        text = text[:max_chars].rstrip()
    return {
        "ok": True,
        "item": item.to_summary(include_attachments=True),
        "text": text,
        "truncated": truncated,
    }


def set_article_read_state(
    *,
    article_id: str,
    read_state: str,
    note: str = "",
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    now: datetime | None = None,
) -> dict[str, Any]:
    item = find_article(article_id, archive_root=archive_root)
    if item is None:
        raise ValueError("Článek nebyl nalezen.")
    normalized_state = normalize_read_state(read_state)
    clean_note = str(note or "").strip()[:1000]
    if normalized_state == "normal":
        clean_note = ""
    metadata_path = article_metadata_path(item, archive_root=archive_root)
    if not metadata_path.exists():
        raise ValueError("Metadata článku nebyla nalezena.")
    raw = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Metadata článku mají neplatný formát.")
    updated_at = (now or datetime.now(timezone.utc)).replace(microsecond=0).isoformat()
    raw["read_state"] = normalized_state
    raw["read_note"] = clean_note
    raw["read_state_updated_at"] = updated_at
    metadata_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_registry(archive_root / "registry.jsonl", raw)
    updated_item = article_item_from_raw(raw)
    return {
        "ok": True,
        "message": article_read_state_message(updated_item),
        "item": updated_item.to_summary(include_attachments=True),
    }


def article_metadata_path(item: ArticleArchiveItem, archive_root: Path = DEFAULT_ARCHIVE_ROOT) -> Path:
    text_path = archive_root / item.text_file
    return text_path.parent / "metadata.json"


def article_read_state_message(item: ArticleArchiveItem) -> str:
    if item.read_state == "to_read":
        return "Článek je označený k přečtení."
    if item.read_state == "done":
        return "Článek je označený jako hotový."
    return "Příznak k přečtení je zrušený."


def prepare_article_pdf_export(
    *,
    article_id: str,
    recipient_email: str = "",
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    export_root: Path | None = None,
    smtp_config_loader: Callable[[str], Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    from app.email.config import load_smtp_config
    from app.email.outbound import validate_email_address

    item = find_article(article_id, archive_root=archive_root)
    if item is None:
        raise ValueError("Článek nebyl nalezen.")
    smtp_config = (smtp_config_loader or load_smtp_config)("icloud")
    recipient = validate_email_address(recipient_email or smtp_config.address)
    prepared_at = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    root = resolve_export_root(archive_root=archive_root, export_root=export_root)
    export_id = build_library_export_id(item, prepared_at)
    target_dir = next_export_path(root / export_id)
    if target_dir.name != export_id:
        export_id = target_dir.name
    target_dir.mkdir(parents=True, exist_ok=False)

    text = read_article_text(item.id, archive_root=archive_root, max_chars=0)
    pdf_path = target_dir / "article_export.pdf"
    message_path = target_dir / "library_export.eml"
    metadata_path = target_dir / "metadata.json"
    title_prefix = article_pdf_kind(item)
    pdf_title = f"{title_prefix}: {item.one_line_title}" if title_prefix else item.one_line_title
    build_article_pdf(
        item=item,
        text=text,
        pdf_path=pdf_path,
        title=pdf_title,
        prepared_at=prepared_at,
        archive_root=archive_root,
    )

    subject = f"{LIBRARY_EXPORT_SUBJECT_PREFIX} {item.one_line_title}"
    message = build_library_export_message(
        item=item,
        smtp_address=smtp_config.address,
        recipient=recipient,
        subject=subject,
        pdf_path=pdf_path,
        prepared_at=prepared_at,
    )
    message_path.write_bytes(message.as_bytes())
    metadata = {
        "export_id": export_id,
        "status": "draft",
        "provider": smtp_config.provider,
        "article_id": item.id,
        "title": item.one_line_title,
        "category": item.category,
        "recipient": recipient,
        "subject": subject,
        "prepared_at": prepared_at.isoformat(),
        "pdf_path": str(pdf_path),
        "message_path": str(message_path),
        "library_export_marker": True,
        "email_marker_header": LIBRARY_EXPORT_EMAIL_MARKER,
        "email_marker_value": LIBRARY_EXPORT_EMAIL_MARKER_VALUE,
        "do_not_commit": True,
        "local_sensitive_export": True,
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = ArticlePdfExportResult(
        export_id=export_id,
        article_id=item.id,
        title=item.one_line_title,
        category=item.category,
        pdf_path=pdf_path,
        message_path=message_path,
        metadata_path=metadata_path,
        recipient=recipient,
        subject=subject,
        size_bytes=pdf_path.stat().st_size,
    )
    return {
        "ok": True,
        "message": "PDF export je připravený lokálně. E-mail zatím nebyl odeslán.",
        "export": result.to_summary(),
    }


def send_article_pdf_export(
    *,
    export_id: str,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    export_root: Path | None = None,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    smtp_config_loader: Callable[[str], Any] | None = None,
    smtp_factory: Callable[..., Any] | None = None,
    sent_copy_saver: Callable[[bytes, Any, datetime], Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    from app.email.config import load_smtp_config
    from app.email.outbound import save_sent_copy_best_effort, send_message_via_smtp

    if not has_explicit_library_export_send_confirmation(export_id, confirmation_text, user_confirmed=user_confirmed):
        raise ValueError(f"Odeslání vyžaduje přesnou potvrzovací větu: {library_export_confirmation_text(export_id)}")
    export_dir = resolve_library_export_dir(
        export_id=export_id,
        archive_root=archive_root,
        export_root=export_root,
    )
    metadata_path = export_dir / "metadata.json"
    message_path = export_dir / "library_export.eml"
    if not metadata_path.exists() or not message_path.exists():
        raise ValueError("Export nebyl nalezen nebo je neúplný.")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if str(metadata.get("status", "")).strip() == "sent":
        raise ValueError("Tento export už byl odeslán.")
    if metadata.get("library_export_marker") is not True:
        raise ValueError("Export nemá bezpečnostní marker Knihovny.")

    provider = str(metadata.get("provider", "icloud") or "icloud")
    smtp_config = (smtp_config_loader or load_smtp_config)(provider)
    message_bytes = message_path.read_bytes()
    parsed = message_from_bytes(message_bytes)
    if str(parsed.get(LIBRARY_EXPORT_EMAIL_MARKER, "")).strip().casefold() != LIBRARY_EXPORT_EMAIL_MARKER_VALUE:
        raise ValueError("E-mail exportu nemá marker pro potlačení dalšího ukládání.")
    sent_at = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    send_message_via_smtp(parsed, smtp_config=smtp_config, smtp_factory=smtp_factory)
    saver = sent_copy_saver or save_sent_copy_best_effort
    sent_copy = saver(message_bytes, smtp_config, sent_at)
    metadata.update(
        {
            "status": "sent",
            "delivery_status": "smtp_sent",
            "sent_at": sent_at.isoformat(),
            "sent_copy_status": getattr(sent_copy, "status", "unknown"),
            "sent_copy_provider": getattr(sent_copy, "provider", ""),
            "sent_copy_folder": getattr(sent_copy, "folder", ""),
            "sent_copy_detail": getattr(sent_copy, "detail", ""),
        }
    )
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = ArticlePdfExportSendResult(
        export_id=str(metadata.get("export_id", export_id)),
        recipient=str(metadata.get("recipient", "")),
        subject=str(metadata.get("subject", "")),
        sent_at=sent_at.isoformat(),
        sent_copy_status=str(metadata.get("sent_copy_status", "")),
        sent_copy_provider=str(metadata.get("sent_copy_provider", "")),
        sent_copy_folder=str(metadata.get("sent_copy_folder", "")),
        sent_copy_detail=str(metadata.get("sent_copy_detail", "")),
    )
    return {
        "ok": True,
        "message": "PDF export byl odeslán e-mailem.",
        "sent": result.to_summary(),
    }


def has_explicit_library_export_send_confirmation(
    export_id: str,
    confirmation_text: str,
    *,
    user_confirmed: bool = False,
) -> bool:
    if not user_confirmed:
        return False
    folded = normalize_confirmation_text(confirmation_text)
    prefix = normalize_confirmation_text(LIBRARY_EXPORT_SEND_CONFIRMATION_PREFIX)
    wanted_id = str(export_id or "").strip().casefold()
    return bool(wanted_id and prefix in folded and wanted_id in folded)


def library_export_confirmation_text(export_id: str) -> str:
    return f"{LIBRARY_EXPORT_SEND_CONFIRMATION_PREFIX} {export_id}."


def normalize_confirmation_text(value: str) -> str:
    table = str.maketrans(
        "áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ",
        "acdeeinorstuuyzACDEEINORSTUUYZ",
    )
    return str(value or "").translate(table).casefold()


def resolve_export_root(*, archive_root: Path, export_root: Path | None) -> Path:
    if export_root is not None:
        return Path(export_root)
    if archive_root == DEFAULT_ARCHIVE_ROOT:
        return DEFAULT_LIBRARY_EXPORT_DIR
    return archive_root / "exports"


def build_library_export_id(item: ArticleArchiveItem, prepared_at: datetime) -> str:
    digest = hashlib.sha256(f"{item.id}\n{prepared_at.isoformat()}".encode("utf-8")).hexdigest()[:8]
    return f"{prepared_at.strftime('%Y%m%d-%H%M%S')}-{slugify(item.one_line_title, max_length=48)}-{digest}"


def next_export_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 1000):
        candidate = path.with_name(f"{path.name}_{index}")
        if not candidate.exists():
            return candidate
    raise OSError("Nepodařilo se najít volný název exportu.")


def resolve_library_export_dir(
    *,
    export_id: str,
    archive_root: Path,
    export_root: Path | None,
) -> Path:
    safe_id = slugify(str(export_id or "").strip(), max_length=140)
    if safe_id != str(export_id or "").strip():
        raise ValueError("Neplatné ID exportu.")
    root = resolve_export_root(archive_root=archive_root, export_root=export_root).resolve()
    target = (root / safe_id).resolve()
    if root != target and root not in target.parents:
        raise ValueError("Neplatná cesta exportu.")
    return target


def article_pdf_kind(item: ArticleArchiveItem) -> str:
    if item.category == "recipes":
        return "Recept"
    if item.category == "science":
        return "Vědecký článek"
    if item.category == "health_info":
        return "Zdravotní informace"
    if item.category == "ai_tools":
        return "Samantha / AI nástroje"
    return "Znalostní karta"


def build_article_pdf(
    *,
    item: ArticleArchiveItem,
    text: str,
    pdf_path: Path,
    title: str,
    prepared_at: datetime,
    archive_root: Path,
) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import Image as PdfImage
        from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on local environment setup
        raise ValueError("ReportLab není nainstalovaný, nejde vytvořit PDF export.") from exc

    font_name = register_pdf_font(pdfmetrics, TTFont)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "LibraryTitle",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=18,
        leading=23,
        spaceAfter=8 * mm,
    )
    heading_style = ParagraphStyle(
        "LibraryHeading",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1f2937"),
        spaceBefore=6 * mm,
        spaceAfter=3 * mm,
    )
    body_style = ParagraphStyle(
        "LibraryBody",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10,
        leading=14,
        spaceAfter=3 * mm,
    )
    meta_style = ParagraphStyle(
        "LibraryMeta",
        parent=body_style,
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#4b5563"),
    )
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=title,
        author="Samantha Agent",
    )
    story: list[Any] = [Paragraph(escape(title), title_style)]
    for line in article_metadata_lines(item=item, prepared_at=prepared_at):
        story.append(Paragraph(escape(line), meta_style))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph("Obsah", heading_style))
    for block in text_to_pdf_blocks(text):
        story.append(Paragraph(block, body_style))
    image_pages: list[tuple[ArticleAttachment, Any]] = []
    if item.attachments:
        story.append(Paragraph("Přílohy", heading_style))
        for attachment in item.attachments:
            details = [
                attachment.label,
                f"typ: {attachment.kind}",
                f"role: {attachment.role}",
            ]
            if attachment.note:
                details.append(f"poznámka: {attachment.note}")
            if attachment.kind.casefold() == "image":
                image_path = article_pdf_image_path(attachment=attachment, archive_root=archive_root)
                if image_path is None:
                    details.append("PDF: obrazový soubor není dostupný")
                else:
                    try:
                        image = PdfImage(str(image_path), lazy=0)
                        max_width = A4[0] - doc.leftMargin - doc.rightMargin
                        max_height = A4[1] - doc.topMargin - doc.bottomMargin - 36 * mm
                        scale = min(
                            1.0,
                            max_width / float(image.imageWidth),
                            max_height / float(image.imageHeight),
                        )
                        image.drawWidth = float(image.imageWidth) * scale
                        image.drawHeight = float(image.imageHeight) * scale
                        image.hAlign = "CENTER"
                        image_pages.append((attachment, image))
                    except Exception:
                        details.append("PDF: obrazový soubor nelze načíst")
            story.append(Paragraph(escape(" | ".join(details)), meta_style))
    for index, (attachment, image) in enumerate(image_pages, start=1):
        story.append(PageBreak())
        story.append(Paragraph(f"Obrazová příloha {index}", heading_style))
        story.append(Paragraph(escape(attachment.label), body_style))
        if attachment.note:
            story.append(Paragraph(escape(attachment.note), meta_style))
        story.append(Spacer(1, 4 * mm))
        story.append(image)
    doc.build(story)


def article_pdf_image_path(*, attachment: ArticleAttachment, archive_root: Path) -> Path | None:
    if attachment.kind.casefold() != "image":
        return None
    for relative_path in (attachment.readable_file, attachment.original_file):
        resolved = resolve_archive_relative_file(archive_root, relative_path)
        if resolved is not None and resolved.is_file():
            return resolved
    return None


def register_pdf_font(pdfmetrics: Any, TTFont: Any) -> str:
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/Supplemental/Verdana.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont("SamanthaArchiveFont", str(path)))
            return "SamanthaArchiveFont"
        except Exception:
            continue
    return "Helvetica"


def article_metadata_lines(*, item: ArticleArchiveItem, prepared_at: datetime) -> list[str]:
    tags = ", ".join(item.tags) if item.tags else "bez tagů"
    lines = [
        f"ID článku: {item.id}",
        f"Kategorie: {item.category_label}",
        f"Archivováno: {item.archived_at or 'neuvedeno'}",
        f"Exportováno: {prepared_at.isoformat()}",
        f"Zdroj: {item.source_label or item.source_type or 'neuvedeno'}",
        f"Tagy: {tags}",
        f"Počet znaků: {item.text_chars}",
    ]
    if item.source_url:
        lines.append(f"URL: {item.source_url}")
    if item.canonical_url and item.canonical_url != item.source_url:
        lines.append(f"Kanonická URL: {item.canonical_url}")
    if item.source_note:
        lines.append(f"Poznámka ke zdroji: {item.source_note}")
    if item.attachments:
        lines.append(f"Přílohy: {len(item.attachments)}")
    return lines


def text_to_pdf_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in str(text or "").replace("\r\n", "\n").replace("\r", "\n").splitlines():
        if line.strip():
            current.append(line.rstrip())
            continue
        if current:
            blocks.append(lines_to_pdf_paragraph(current))
            current = []
    if current:
        blocks.append(lines_to_pdf_paragraph(current))
    return blocks or [escape("(Prázdný obsah článku.)")]


def lines_to_pdf_paragraph(lines: list[str]) -> str:
    return "<br/>".join(escape(line) for line in lines)


def build_library_export_message(
    *,
    item: ArticleArchiveItem,
    smtp_address: str,
    recipient: str,
    subject: str,
    pdf_path: Path,
    prepared_at: datetime,
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = smtp_address
    message["To"] = recipient
    message["Subject"] = subject
    message["Date"] = formatdate(localtime=True)
    message[LIBRARY_EXPORT_EMAIL_MARKER] = LIBRARY_EXPORT_EMAIL_MARKER_VALUE
    message["X-Samantha-Article-ID"] = item.id
    message.set_content(
        "\n".join(
            [
                "Toto je PDF export z Knihovny Samanthy.",
                "E-mail má příznak, aby se nenabízel k dalšímu uložení/importu.",
                "",
                f"Název: {item.one_line_title}",
                f"Kategorie: {item.category_label}",
                f"ID článku: {item.id}",
                f"Exportováno: {prepared_at.isoformat()}",
            ]
        ),
        subtype="plain",
        charset="utf-8",
    )
    message.add_attachment(
        pdf_path.read_bytes(),
        maintype="application",
        subtype="pdf",
        filename=f"{slugify(item.one_line_title, max_length=60)}.pdf",
    )
    return message


def find_article(article_id: str, archive_root: Path = DEFAULT_ARCHIVE_ROOT) -> ArticleArchiveItem | None:
    wanted = str(article_id or "").strip()
    if not wanted:
        return None
    for item in load_article_registry(archive_root):
        if item.id == wanted:
            return item
    return None


def delete_article(
    *,
    article_id: str,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> dict[str, Any]:
    if not user_confirmed or DELETE_CONFIRMATION_PHRASE.casefold() not in str(confirmation_text).casefold():
        raise ValueError(f"Vyřazení položky vyžaduje potvrzení: {DELETE_CONFIRMATION_PHRASE}")
    item = find_article(article_id, archive_root=archive_root)
    if item is None:
        raise ValueError("Článek nebyl nalezen.")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    trash_root = archive_root / "trash" / "articles"
    trash_root.mkdir(parents=True, exist_ok=True)
    source_dir = archive_root / "articles" / item.id
    trash_dir = next_trash_path(trash_root / f"{now.strftime('%Y%m%d_%H%M%S')}_{item.id}")
    moved_to = ""
    if source_dir.exists():
        shutil.move(str(source_dir), str(trash_dir))
        moved_to = str(trash_dir.relative_to(archive_root))

    registry_path = archive_root / "registry.jsonl"
    removed = remove_from_registry(registry_path, item.id)
    if removed is None:
        if moved_to:
            shutil.move(str(trash_dir), str(source_dir))
        raise ValueError("Článek nebyl nalezen v registru.")

    manifest = {
        "id": item.id,
        "title": item.title,
        "category": item.category,
        "removed_at": now.isoformat(),
        "moved_to": moved_to,
        "registry_entry": removed,
    }
    manifest_path = trash_dir / "removed_from_registry.json" if moved_to else trash_root / f"{item.id}_removed_from_registry.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "message": "Položka byla vyřazena z knihovny a přesunuta do soukromého koše.",
        "item_id": item.id,
        "title": item.one_line_title,
        "trash_path": moved_to,
    }


def article_text_cleanup_report(
    *,
    category: str = "science",
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    min_removed_chars: int = 1000,
    max_cleaned_ratio: float = 0.85,
) -> dict[str, Any]:
    wanted = normalize_category(category) if category != "all" else "all"
    items: list[dict[str, Any]] = []
    for item in load_article_registry(archive_root):
        if wanted != "all" and item.category != wanted:
            continue
        analysis = analyze_article_text_cleanup(
            item,
            archive_root=archive_root,
            min_removed_chars=min_removed_chars,
            max_cleaned_ratio=max_cleaned_ratio,
        )
        if analysis is not None:
            items.append(analysis)
    candidates = [item for item in items if item["needs_cleanup"]]
    return {
        "ok": True,
        "category": wanted,
        "count": len(items),
        "candidate_count": len(candidates),
        "items": items,
    }


def cleanup_article_text(
    *,
    article_id: str,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    now: datetime | None = None,
) -> dict[str, Any]:
    if not user_confirmed or CLEANUP_CONFIRMATION_PHRASE.casefold() not in str(confirmation_text).casefold():
        raise ValueError(f"Vyčištění článku vyžaduje potvrzení: {CLEANUP_CONFIRMATION_PHRASE}")
    item = find_article(article_id, archive_root=archive_root)
    if item is None:
        raise ValueError("Článek nebyl nalezen.")
    cleaned = cleaned_text_from_source_html(item, archive_root=archive_root)
    if not cleaned:
        raise ValueError("Článek nemá dostupné source.html pro bezpečné přegenerování.")
    article_path = archive_root / item.text_file
    if not article_path.exists():
        raise ValueError("Soubor article.txt nebyl nalezen.")
    current = article_path.read_text(encoding="utf-8", errors="replace").strip()
    if normalize_text_for_cleanup_compare(current) == normalize_text_for_cleanup_compare(cleaned):
        return {
            "ok": True,
            "message": "Článek už odpovídá nové čisté extrakci.",
            "item_id": item.id,
            "changed": False,
            "old_chars": len(current),
            "new_chars": len(cleaned),
        }
    cleaned_at = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    backup_path = next_cleanup_backup_path(article_path.with_name(f"article_before_cleanup_{cleaned_at.strftime('%Y%m%d_%H%M%S')}.txt"))
    backup_path.write_text(current + "\n", encoding="utf-8")
    article_path.write_text(cleaned.rstrip() + "\n", encoding="utf-8")
    metadata_path = archive_root / "articles" / item.id / "metadata.json"
    if not metadata_path.exists():
        raise ValueError("Metadata článku nebyla nalezena.")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    old_chars = len(current)
    new_chars = len(cleaned.rstrip())
    metadata["text_chars"] = str(new_chars)
    metadata["last_cleaned_at"] = cleaned_at.isoformat()
    metadata["last_cleanup"] = {
        "tool": "article_text_cleanup",
        "old_text_chars": old_chars,
        "new_text_chars": new_chars,
        "removed_chars": max(0, old_chars - new_chars),
        "backup_file": str(backup_path.relative_to(archive_root)),
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_registry(archive_root / "registry.jsonl", metadata)
    return {
        "ok": True,
        "message": "Článek byl přegenerován čistou extrakcí a původní text je uložený jako soukromá záloha.",
        "item_id": item.id,
        "title": item.one_line_title,
        "changed": True,
        "old_chars": old_chars,
        "new_chars": new_chars,
        "removed_chars": max(0, old_chars - new_chars),
        "backup_file": str(backup_path.relative_to(archive_root)),
    }


def analyze_article_text_cleanup(
    item: ArticleArchiveItem,
    *,
    archive_root: Path,
    min_removed_chars: int,
    max_cleaned_ratio: float,
) -> dict[str, Any] | None:
    article_path = archive_root / item.text_file
    if not article_path.exists():
        return None
    current = article_path.read_text(encoding="utf-8", errors="replace").strip()
    cleaned = cleaned_text_from_source_html(item, archive_root=archive_root)
    if not cleaned:
        return None
    old_chars = len(current)
    new_chars = len(cleaned.rstrip())
    removed_chars = max(0, old_chars - new_chars)
    cleaned_ratio = (new_chars / old_chars) if old_chars else 1.0
    marker_count = article_boilerplate_marker_count(current)
    changed = normalize_text_for_cleanup_compare(current) != normalize_text_for_cleanup_compare(cleaned)
    needs_cleanup = changed and marker_count > 0 and removed_chars >= min_removed_chars and cleaned_ratio <= max_cleaned_ratio
    return {
        "id": item.id,
        "title": item.one_line_title,
        "category": item.category,
        "old_chars": old_chars,
        "new_chars": new_chars,
        "removed_chars": removed_chars,
        "cleaned_ratio": round(cleaned_ratio, 3),
        "marker_count": marker_count,
        "needs_cleanup": needs_cleanup,
    }


def cleaned_text_from_source_html(item: ArticleArchiveItem, *, archive_root: Path) -> str:
    html_path = resolve_archive_relative_file(archive_root, item.html_file)
    if html_path is None or not html_path.exists():
        return ""
    return extract_article(html_path.read_bytes(), item.source_url or item.canonical_url).text.strip()


def preview_article_source_reextract(
    *,
    article_id: str,
    source_encoding: str,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
) -> dict[str, Any]:
    normalized_encoding = str(source_encoding or "").strip().lower().replace("_", "-")
    if normalized_encoding != SOURCE_REEXTRACT_PREVIEW_ENCODING:
        raise ValueError("Náhled vyžaduje explicitní kódování ISO-8859-2.")

    item = find_article(article_id, archive_root=archive_root)
    if item is None:
        raise ValueError("Článek nebyl nalezen.")
    html_path = resolve_archive_relative_file(archive_root, item.html_file)
    if html_path is None or not html_path.is_file():
        raise ValueError("Článek nemá dostupné source.html pro bezpečný náhled.")
    article_path = resolve_archive_relative_file(archive_root, item.text_file)
    if article_path is None or not article_path.is_file():
        raise ValueError("Soubor article.txt nebyl nalezen.")

    html_bytes = html_path.read_bytes()
    current_text = normalize_text_for_cleanup_compare(
        article_path.read_text(encoding="utf-8", errors="replace")
    )
    preview_text = normalize_text_for_cleanup_compare(
        extract_article(
            html_bytes,
            item.source_url or item.canonical_url,
            http_encoding=SOURCE_REEXTRACT_PREVIEW_ENCODING,
        ).text
    )
    if not preview_text:
        raise ValueError("Nová extrakce neobsahuje žádný čitelný text.")

    return {
        "ok": True,
        "read_only": True,
        "source_encoding": SOURCE_REEXTRACT_PREVIEW_ENCODING,
        "changed": current_text != preview_text,
        "metrics": {
            "source_bytes": len(html_bytes),
            "current_chars": len(current_text),
            "preview_chars": len(preview_text),
            "char_delta": len(preview_text) - len(current_text),
            "different_positions": text_difference_count(current_text, preview_text),
            "current_replacement_chars": current_text.count("\ufffd"),
            "preview_replacement_chars": preview_text.count("\ufffd"),
            "current_control_chars": unsafe_control_character_count(current_text),
            "preview_control_chars": unsafe_control_character_count(preview_text),
        },
    }


def text_difference_count(current_text: str, preview_text: str) -> int:
    return sum(left != right for left, right in zip(current_text, preview_text)) + abs(
        len(current_text) - len(preview_text)
    )


def unsafe_control_character_count(text: str) -> int:
    return sum(
        (ord(character) < 32 and character not in "\n\r\t") or 127 <= ord(character) <= 159
        for character in text
    )


def article_boilerplate_marker_count(text: str) -> int:
    folded = text.casefold()
    markers = (
        *HARD_TAIL_MARKERS,
        *INLINE_RECOMMENDATION_MARKERS,
        "google trends",
        "nejčtenější",
        "nejctenejsi",
        "trendy podle kategorie",
    )
    return sum(folded.count(marker.casefold()) for marker in markers if marker)


def normalize_text_for_cleanup_compare(text: str) -> str:
    return "\n".join(line.rstrip() for line in str(text or "").strip().splitlines()).strip()


def next_cleanup_backup_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 1000):
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise OSError("Nepodařilo se najít volný název zálohy článku.")


def next_trash_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 1000):
        candidate = path.with_name(f"{path.name}_{index}")
        if not candidate.exists():
            return candidate
    raise OSError("Nepodařilo se najít volný název v koši archivu.")


def read_article_text(article_id: str, archive_root: Path = DEFAULT_ARCHIVE_ROOT, max_chars: int = 0) -> str:
    item = find_article(article_id, archive_root=archive_root)
    if item is None:
        return ""
    text_path = archive_root / item.text_file
    if not text_path.exists():
        return ""
    text = text_path.read_text(encoding="utf-8", errors="replace").strip()
    if max_chars > 0 and len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text


def get_article_attachment(
    *,
    article_id: str,
    attachment_id: str,
    variant: str = "readable",
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
) -> dict[str, Any]:
    item = find_article(article_id, archive_root=archive_root)
    if item is None:
        return {"ok": False, "error": "not_found", "message": "Článek nebyl nalezen."}
    wanted = slugify(str(attachment_id or "").strip(), max_length=48)
    attachment = next((entry for entry in item.attachments if entry.id == wanted), None)
    if attachment is None:
        return {"ok": False, "error": "not_found", "message": "Příloha nebyla nalezena."}
    variant_key = str(variant or "readable").strip().casefold()
    candidates = {
        "thumb": [attachment.thumb_file, attachment.readable_file, attachment.original_file],
        "thumbnail": [attachment.thumb_file, attachment.readable_file, attachment.original_file],
        "readable": [attachment.readable_file, attachment.original_file],
        "original": [attachment.original_file],
    }.get(variant_key, [attachment.readable_file, attachment.original_file])
    for relative_path in candidates:
        resolved = resolve_archive_relative_file(archive_root, relative_path)
        if resolved is not None and resolved.is_file():
            return {
                "ok": True,
                "path": resolved,
                "attachment": attachment.to_summary(),
                "mime_type": mime_type_for_extension(resolved.suffix),
                "filename": resolved.name,
            }
    return {"ok": False, "error": "not_found", "message": "Soubor přílohy nebyl nalezen."}


def resolve_archive_relative_file(archive_root: Path, relative_path: str) -> Path | None:
    value = str(relative_path or "").strip()
    if not value:
        return None
    if Path(value).is_absolute():
        return None
    try:
        root = archive_root.resolve(strict=True)
        target = (archive_root / value).resolve(strict=True)
    except FileNotFoundError:
        return None
    if root != target and root not in target.parents:
        return None
    return target


def make_snippet(text: str, terms: list[str], radius: int = 180) -> str:
    folded = text.casefold()
    positions = [folded.find(term) for term in terms if folded.find(term) >= 0]
    if not positions:
        return " ".join(text[: radius * 2].split())
    center = min(positions)
    start = max(0, center - radius)
    end = min(len(text), center + radius)
    return " ".join(text[start:end].split())
