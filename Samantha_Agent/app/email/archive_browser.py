from __future__ import annotations

import hashlib
import json
import re
import tempfile
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote

from app.documents.ai_metadata import (
    AIMetadataError,
    DEFAULT_AI_METADATA_DOMAINS,
    request_codex_metadata_suggestion,
)
from app.documents.search_service import (
    READING_STATUS_LABELS,
    document_reference,
    effective_document_reading_status,
)
from app.documents.vault import (
    DEFAULT_DOCUMENTS_DIR,
    PROJECT_ROOT,
    extract_text,
    read_json_file,
    read_jsonl,
    relative_to_project,
    safe_filename,
    safe_text,
)
from app.email.archive_service import DEFAULT_EMAIL_ARCHIVE_DIR
from app.email.redaction import redact_email_addresses


EMAIL_ARCHIVE_OPENABLE_FILES: dict[str, tuple[Path, str]] = {
    "body_html": (Path("body.html"), "text/html; charset=utf-8"),
    "body_txt": (Path("body.txt"), "text/plain; charset=utf-8"),
    "original_eml": (Path("original.eml"), "message/rfc822"),
    "metadata": (Path("metadata.json"), "application/json; charset=utf-8"),
    "attachments": (Path("attachments") / "attachments.json", "application/json; charset=utf-8"),
}
EMAIL_ARCHIVE_REFERENCE_PATTERN = re.compile(r"archive-ref-[0-9a-f]{16}")
EMAIL_ARCHIVE_ATTACHMENT_REFERENCE_PATTERN = re.compile(
    r"email-attachment-ref-[0-9a-f]{16}"
)
EMAIL_ARCHIVE_BODY_TEXT_MAX_BYTES = 512 * 1024
EMAIL_ARCHIVE_ORIGINAL_MAX_BYTES = 25 * 1024 * 1024


def email_archive_reference(archive_directory_name: str) -> str:
    digest = hashlib.sha256(archive_directory_name.encode("utf-8")).hexdigest()[:16]
    return f"archive-ref-{digest}"


def _email_archive_attachment_reference(
    *,
    archive_directory_name: str,
    part_index: int,
    filename: str,
) -> str:
    source = f"{archive_directory_name}\0{int(part_index)}\0{filename}"
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
    return f"email-attachment-ref-{digest}"


def _normalized_attachment_name(value: str) -> str:
    return safe_filename(str(value or "")).casefold()


def email_archive_uid(metadata: dict[str, Any], archive_directory_name: str) -> str:
    uid = safe_text(str(metadata.get("uid", ""))).strip()
    if uid.isdigit():
        return uid
    match = re.match(r"^email-(\d+)(?:-|$)", archive_directory_name)
    return match.group(1) if match else ""


def email_archive_list_status(
    query: str = "",
    *,
    limit: int = 120,
    archive_directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
) -> dict[str, Any]:
    safe_query = safe_text(query).casefold().strip()
    safe_limit = min(max(1, int(limit)), 500)
    archives: list[dict[str, Any]] = []
    if not archive_directory.exists():
        return {
            "ok": True,
            "count": 0,
            "items": [],
            "message": "EmailArchiveVault zatím neexistuje.",
        }

    for metadata_path in archive_directory.glob("*/metadata.json"):
        try:
            metadata = read_json_file(metadata_path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        archive_dir = metadata_path.parent
        archive_id = safe_text(str(metadata.get("archive_id") or archive_dir.name)).strip()
        if not archive_id:
            continue
        subject = safe_text(str(metadata.get("subject", "")))[:260]
        sender = redact_email_addresses(safe_text(str(metadata.get("from", ""))))[:220]
        uid = email_archive_uid(metadata, archive_dir.name)[:80]
        date_text = safe_text(str(metadata.get("date", "")))[:160]
        archived_at = safe_text(str(metadata.get("archived_at", "")))[:120]
        haystack = " ".join([archive_id, uid, subject, sender, date_text]).casefold()
        if safe_query and safe_query not in haystack:
            continue
        archives.append(
            {
                "archive_id": archive_id,
                "archive_ref": email_archive_reference(archive_dir.name),
                "uid": uid,
                "subject": subject,
                "sender": sender,
                "date": date_text,
                "archived_at": archived_at,
                "links_count": int(metadata.get("links_count", 0) or 0),
                "attachments_count": int(metadata.get("attachments_count", 0) or 0),
                "relative_path": safe_text(str(relative_to_project(archive_dir)))[:500],
                "_sort_timestamp": email_archive_sort_timestamp(
                    date_text,
                    archived_at,
                    metadata_path=metadata_path,
                ),
            }
        )

    archives.sort(
        key=lambda item: float(item.get("_sort_timestamp", 0.0) or 0.0),
        reverse=True,
    )
    archives = archives[:safe_limit]
    for item in archives:
        item.pop("_sort_timestamp", None)

    return {
        "ok": True,
        "count": len(archives),
        "items": archives,
        "message": f"Nalezeno archivovaných e-mailů: {len(archives)}.",
    }


def email_archive_detail_status(
    archive_id: str,
    *,
    archive_directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
    documents_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> dict[str, Any]:
    resolved = resolve_email_archive_dir(archive_id, archive_directory=archive_directory)
    if not resolved.get("ok"):
        return resolved
    archive_dir = resolved["path"]
    metadata_path = archive_dir / "metadata.json"
    try:
        metadata = read_json_file(metadata_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return {"ok": False, "message": "Archiv nemá čitelná metadata."}

    safe_archive_id = safe_text(str(metadata.get("archive_id") or archive_dir.name))
    archive_ref = email_archive_reference(archive_dir.name)
    uid = email_archive_uid(metadata, archive_dir.name)
    files = []
    for key, (relative, content_type) in EMAIL_ARCHIVE_OPENABLE_FILES.items():
        path = archive_dir / relative
        if not path.is_file():
            continue
        files.append(
            {
                "key": key,
                "label": email_archive_file_label(key),
                "filename": safe_text(path.name)[:180],
                "content_type": content_type,
                "size_bytes": path.stat().st_size,
                "url": f"/email-archive/file?archive_id={quote(archive_ref)}&file={quote(key)}",
            }
        )

    attachments = read_email_archive_attachment_metadata(archive_dir)
    embedded_attachments = read_email_archive_embedded_attachments(
        archive_ref,
        archive_directory=archive_directory,
    )
    embedded_by_name: dict[str, list[dict[str, Any]]] = {}
    for embedded in embedded_attachments:
        embedded_by_name.setdefault(
            _normalized_attachment_name(str(embedded.get("filename", ""))),
            [],
        ).append(embedded)
    for attachment in attachments:
        matches = embedded_by_name.get(
            _normalized_attachment_name(str(attachment.get("filename", ""))),
            [],
        )
        if not matches:
            continue
        embedded = matches.pop(0)
        attachment["url"] = str(embedded.get("url", ""))
        attachment["attachment_ref"] = str(
            embedded.get("attachment_ref", "")
        )
        attachment["embedded"] = True
    known_attachment_names = {
        _normalized_attachment_name(str(item.get("filename", "")))
        for item in attachments
    }
    attachments.extend(
        embedded
        for embedded in embedded_attachments
        if _normalized_attachment_name(str(embedded.get("filename", "")))
        not in known_attachment_names
    )
    downloaded = downloaded_email_archive_attachments(uid=uid, documents_dir=documents_dir)
    vault_attachments = vault_email_archive_attachments(
        uid=uid,
        documents_dir=documents_dir,
    )
    body_text, body_truncated = read_email_archive_body_text(
        archive_ref,
        archive_directory=archive_directory,
    )

    return {
        "ok": True,
        "archive_id": safe_archive_id,
        "archive_ref": archive_ref,
        "uid": uid,
        "subject": safe_text(str(metadata.get("subject", "")))[:260],
        "sender": redact_email_addresses(safe_text(str(metadata.get("from", ""))))[:220],
        "date": safe_text(str(metadata.get("date", "")))[:160],
        "archived_at": safe_text(str(metadata.get("archived_at", "")))[:120],
        "relative_path": safe_text(str(relative_to_project(archive_dir)))[:500],
        "files": files,
        "body_text": body_text,
        "body_truncated": body_truncated,
        "attachments": attachments,
        "downloaded_attachments": downloaded,
        "vault_attachments": vault_attachments,
        "message": "Archiv e-mailu načten read-only.",
    }


def email_archive_ai_metadata_suggestion(
    archive_id: str,
    attachment_ref: str = "",
    *,
    archive_directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
    analyzer=request_codex_metadata_suggestion,
    extractor=extract_text,
) -> dict[str, Any]:
    """Analyze one explicitly opened email and optionally one embedded attachment."""

    resolved = resolve_email_archive_dir(archive_id, archive_directory=archive_directory)
    if not resolved.get("ok"):
        raise AIMetadataError("Vybraný e-mail nebyl v místním archivu nalezen.")
    archive_dir = Path(resolved["path"])
    try:
        metadata = read_json_file(archive_dir / "metadata.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise AIMetadataError("Vybraný e-mail nemá čitelná metadata.") from exc

    archive_ref = email_archive_reference(archive_dir.name)
    body_text, body_truncated = read_email_archive_body_text(
        archive_ref,
        archive_directory=archive_directory,
    )
    subject = safe_text(str(metadata.get("subject", ""))).strip()[:260]
    sender = redact_email_addresses(safe_text(str(metadata.get("from", ""))))[:220]
    source_name = subject or "E-mail bez předmětu"
    source_text = "\n".join(
        part
        for part in (
            f"Předmět: {subject}" if subject else "",
            f"Odesílatel: {sender}" if sender else "",
            body_text,
        )
        if part
    )
    current_metadata: dict[str, Any] = {
        "title": subject,
        "domain": "other",
        "document_type": "email",
        "counterparty": sender,
        "related_asset": "",
        "tags": ["email"],
    }
    attachment_filename = ""
    attachment_extraction_method = ""
    safe_attachment_ref = str(attachment_ref or "").strip()
    if safe_attachment_ref:
        attachment = resolve_email_archive_embedded_attachment(
            archive_ref,
            safe_attachment_ref,
            archive_directory=archive_directory,
        )
        if not attachment.get("ok"):
            raise AIMetadataError("Vybraná příloha nebyla v původním e-mailu nalezena.")
        attachment_filename = safe_filename(str(attachment.get("filename") or "attachment.bin"))
        payload = attachment.get("data")
        if not isinstance(payload, bytes):
            raise AIMetadataError("Vybraná příloha nemá čitelný obsah.")
        with tempfile.TemporaryDirectory(prefix="samantha-email-ai-") as temp_dir:
            attachment_path = Path(temp_dir) / attachment_filename
            attachment_path.write_bytes(payload)
            extraction = extractor(attachment_path)
        attachment_text = str(getattr(extraction, "text", "") or "").strip()
        attachment_extraction_method = safe_text(str(getattr(extraction, "method", "")))[:120]
        if not attachment_text:
            raise AIMetadataError("Z vybrané přílohy se nepodařilo získat text pro AI návrh.")
        source_name = f"{source_name} — {attachment_filename}"
        source_text = "\n".join(
            (
                source_text,
                f"Příloha: {attachment_filename}",
                attachment_text,
            )
        )
        current_metadata = {
            "title": attachment_filename,
            "domain": "other",
            "document_type": "email-attachment",
            "counterparty": sender,
            "related_asset": "",
            "tags": ["email", "email-attachment"],
        }
    if not source_text.strip():
        raise AIMetadataError("E-mail nemá použitelný text pro AI návrh.")

    result = analyzer(
        source_name=source_name,
        source_text=source_text,
        current_metadata=current_metadata,
        allowed_domains=list(DEFAULT_AI_METADATA_DOMAINS),
    )
    return {
        **result,
        "source_kind": "email_attachment" if safe_attachment_ref else "email",
        "archive_ref": archive_ref,
        "attachment_ref": safe_attachment_ref,
        "attachment_filename": attachment_filename,
        "attachment_extraction_method": attachment_extraction_method,
        "body_truncated": body_truncated,
        "message": (
            "AI návrh z e-mailu a vybrané přílohy je pouze ke kontrole; nic nebylo uloženo."
            if safe_attachment_ref
            else "AI návrh z e-mailu je pouze ke kontrole; nic nebylo uloženo."
        ),
    }


def email_archive_reference_for_document_id(
    document_id: str,
    *,
    archive_directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
    documents_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    """Resolve one vault document to exactly one source email using stored UID evidence."""

    safe_document_id = str(document_id or "").strip()
    if not safe_document_id:
        return ""
    index_path = documents_dir / "index" / "documents_index.jsonl"
    source_coordinates = ""
    for row in read_jsonl(index_path):
        if str(row.get("document_id", "")).strip() != safe_document_id:
            continue
        source_coordinates = " ".join(
            str(row.get(key, ""))
            for key in (
                "document_id",
                "title",
                "original_filename",
                "stored_path",
                "case_id",
                "review_source",
            )
        )
        break
    if not source_coordinates:
        return ""

    matches: list[str] = []
    listing = email_archive_list_status(
        limit=500,
        archive_directory=archive_directory,
    )
    for item in listing.get("items", []):
        if not isinstance(item, dict):
            continue
        uid = str(item.get("uid", "")).strip()
        archive_ref = str(item.get("archive_ref", "")).strip()
        if (
            uid.isdigit()
            and EMAIL_ARCHIVE_REFERENCE_PATTERN.fullmatch(archive_ref)
            and re.search(rf"(?<!\d){re.escape(uid)}(?!\d)", source_coordinates)
        ):
            matches.append(archive_ref)
    unique_matches = tuple(dict.fromkeys(matches))
    return unique_matches[0] if len(unique_matches) == 1 else ""


def read_email_archive_body_text(
    archive_id: str,
    *,
    archive_directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
    max_bytes: int = EMAIL_ARCHIVE_BODY_TEXT_MAX_BYTES,
) -> tuple[str, bool]:
    """Read one local plain-text body for the mailbox view without side effects."""

    safe_limit = min(max(1, int(max_bytes)), EMAIL_ARCHIVE_BODY_TEXT_MAX_BYTES)
    resolved = resolve_email_archive_file(
        archive_id,
        "body_txt",
        archive_directory=archive_directory,
    )
    if not resolved.get("ok"):
        return "", False
    try:
        with Path(resolved["path"]).open("rb") as handle:
            stored_payload = handle.read(EMAIL_ARCHIVE_BODY_TEXT_MAX_BYTES + 1)
    except OSError:
        return "", False
    stored_text = stored_payload.decode("utf-8", errors="replace").replace("\x00", " ")
    original_text = read_email_archive_original_body_text(
        archive_id,
        archive_directory=archive_directory,
    )
    body_text = max((stored_text, original_text), key=len)
    payload = body_text.encode("utf-8")
    truncated = len(payload) > safe_limit
    if truncated:
        payload = payload[:safe_limit]
    return payload.decode("utf-8", errors="ignore"), truncated


def read_email_archive_original_body_text(
    archive_id: str,
    *,
    archive_directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
) -> str:
    """Extract the fullest safe readable alternative from the immutable EML."""

    resolved = resolve_email_archive_file(
        archive_id,
        "original_eml",
        archive_directory=archive_directory,
    )
    if not resolved.get("ok"):
        return ""
    try:
        with Path(resolved["path"]).open("rb") as handle:
            payload = handle.read(EMAIL_ARCHIVE_ORIGINAL_MAX_BYTES + 1)
    except OSError:
        return ""
    if len(payload) > EMAIL_ARCHIVE_ORIGINAL_MAX_BYTES:
        return ""
    try:
        message = BytesParser(policy=policy.default).parsebytes(payload)
    except (TypeError, ValueError):
        return ""

    plain_parts: list[str] = []
    html_parts: list[str] = []
    for part in message.walk() if message.is_multipart() else [message]:
        if part.is_multipart() or part.get_content_disposition() == "attachment":
            continue
        content_type = part.get_content_type()
        if content_type not in {"text/plain", "text/html"}:
            continue
        decoded = part.get_payload(decode=True)
        if not isinstance(decoded, bytes):
            continue
        charset = part.get_content_charset() or "utf-8"
        text = decoded.decode(charset, errors="replace")
        if content_type == "text/plain":
            plain_parts.append(_normalize_readable_text(text))
        else:
            html_parts.append(_html_to_readable_text(text))

    candidates = [
        "\n\n".join(part for part in plain_parts if part),
        "\n\n".join(part for part in html_parts if part),
    ]
    return max(candidates, key=len, default="")


def read_email_archive_embedded_attachments(
    archive_id: str,
    *,
    archive_directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
) -> list[dict[str, Any]]:
    """List attachment parts from one immutable original EML without writing files."""

    resolved = resolve_email_archive_file(
        archive_id,
        "original_eml",
        archive_directory=archive_directory,
    )
    if not resolved.get("ok"):
        return []
    try:
        raw = resolved["path"].read_bytes()
    except OSError:
        return []
    if len(raw) > EMAIL_ARCHIVE_ORIGINAL_MAX_BYTES:
        return []
    try:
        message = BytesParser(policy=policy.default).parsebytes(raw)
    except (TypeError, ValueError):
        return []

    archive_ref = email_archive_reference(resolved["path"].parent.name)
    result: list[dict[str, Any]] = []
    for index, part in enumerate(message.walk()):
        if part.is_multipart():
            continue
        raw_filename = str(part.get_filename() or "").strip()
        disposition = str(part.get_content_disposition() or "").casefold()
        if not raw_filename and disposition != "attachment":
            continue
        filename = (
            safe_filename(raw_filename)
            if raw_filename
            else f"priloha-{index + 1}.bin"
        )
        try:
            payload = part.get_payload(decode=True)
        except (LookupError, TypeError, ValueError):
            continue
        if not isinstance(payload, bytes) or len(payload) > EMAIL_ARCHIVE_ORIGINAL_MAX_BYTES:
            continue
        content_type = safe_text(str(part.get_content_type() or "application/octet-stream"))[
            :120
        ]
        attachment_ref = _email_archive_attachment_reference(
            archive_directory_name=resolved["path"].parent.name,
            part_index=index,
            filename=filename,
        )
        result.append(
            {
                "attachment_ref": attachment_ref,
                "filename": safe_text(filename)[:240],
                "content_type": content_type,
                "size_bytes": len(payload),
                "saved": False,
                "embedded": True,
                "url": (
                    "/email-archive/attachment?"
                    f"archive_id={quote(archive_ref)}&attachment={quote(attachment_ref)}"
                ),
            }
        )
    return result


def resolve_email_archive_embedded_attachment(
    archive_id: str,
    attachment_ref: str,
    *,
    archive_directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
) -> dict[str, Any]:
    """Resolve one opaque EML attachment reference to read-only response bytes."""

    safe_ref = str(attachment_ref or "").strip()
    if not EMAIL_ARCHIVE_ATTACHMENT_REFERENCE_PATTERN.fullmatch(safe_ref):
        return {"ok": False, "message": "Příloha nemá platný bezpečný odkaz."}
    resolved = resolve_email_archive_file(
        archive_id,
        "original_eml",
        archive_directory=archive_directory,
    )
    if not resolved.get("ok"):
        return {"ok": False, "message": "Původní e-mail není dostupný."}
    try:
        raw = resolved["path"].read_bytes()
    except OSError:
        return {"ok": False, "message": "Původní e-mail nelze přečíst."}
    if len(raw) > EMAIL_ARCHIVE_ORIGINAL_MAX_BYTES:
        return {"ok": False, "message": "Původní e-mail je příliš velký."}
    try:
        message = BytesParser(policy=policy.default).parsebytes(raw)
    except (TypeError, ValueError):
        return {"ok": False, "message": "Původní e-mail nelze bezpečně načíst."}

    archive_directory_name = resolved["path"].parent.name
    for index, part in enumerate(message.walk()):
        if part.is_multipart():
            continue
        raw_filename = str(part.get_filename() or "").strip()
        disposition = str(part.get_content_disposition() or "").casefold()
        if not raw_filename and disposition != "attachment":
            continue
        filename = (
            safe_filename(raw_filename)
            if raw_filename
            else f"priloha-{index + 1}.bin"
        )
        candidate_ref = _email_archive_attachment_reference(
            archive_directory_name=archive_directory_name,
            part_index=index,
            filename=filename,
        )
        if candidate_ref != safe_ref:
            continue
        try:
            payload = part.get_payload(decode=True)
        except (LookupError, TypeError, ValueError):
            break
        if not isinstance(payload, bytes) or len(payload) > EMAIL_ARCHIVE_ORIGINAL_MAX_BYTES:
            break
        return {
            "ok": True,
            "data": payload,
            "filename": safe_text(filename)[:240],
            "content_type": safe_text(
                str(part.get_content_type() or "application/octet-stream")
            )[:120],
        }
    return {"ok": False, "message": "Příloha nebyla v původním e-mailu nalezena."}


def email_archive_sort_timestamp(
    message_date: str,
    archived_at: str,
    *,
    metadata_path: Path,
) -> float:
    """Sort by received message date, then archive time, then local mtime."""

    clean_message_date = str(message_date or "").strip()
    if clean_message_date:
        try:
            parsed = parsedate_to_datetime(clean_message_date)
        except (TypeError, ValueError, OverflowError):
            parsed = None
        if parsed is not None:
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            try:
                return parsed.timestamp()
            except (OSError, OverflowError, ValueError):
                pass

    clean_archived_at = str(archived_at or "").strip()
    if clean_archived_at:
        try:
            parsed_archive = datetime.fromisoformat(
                clean_archived_at.replace("Z", "+00:00")
            )
            if parsed_archive.tzinfo is None:
                parsed_archive = parsed_archive.replace(tzinfo=timezone.utc)
            return parsed_archive.timestamp()
        except (OSError, OverflowError, TypeError, ValueError):
            pass

    try:
        return metadata_path.stat().st_mtime
    except OSError:
        return 0.0


class _ReadableHtmlParser(HTMLParser):
    BLOCK_TAGS = {
        "address",
        "article",
        "br",
        "div",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "li",
        "p",
        "section",
        "table",
        "tr",
    }
    HIDDEN_TAGS = {"script", "style", "template"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        clean_tag = tag.casefold()
        if clean_tag in self.HIDDEN_TAGS:
            self.hidden_depth += 1
        elif not self.hidden_depth and clean_tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        clean_tag = tag.casefold()
        if clean_tag in self.HIDDEN_TAGS:
            self.hidden_depth = max(0, self.hidden_depth - 1)
        elif not self.hidden_depth and clean_tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth:
            self.parts.append(data)


def _html_to_readable_text(html_text: str) -> str:
    parser = _ReadableHtmlParser()
    try:
        parser.feed(html_text)
        parser.close()
    except (ValueError, TypeError):
        return ""
    return _normalize_readable_text("".join(parser.parts))


def _normalize_readable_text(text: str) -> str:
    cleaned = text.replace("\x00", " ")
    lines = [" ".join(line.split()) for line in cleaned.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def email_archive_file_label(key: str) -> str:
    return {
        "body_html": "Otevřít HTML",
        "body_txt": "Otevřít text",
        "original_eml": "Otevřít původní .eml",
        "metadata": "Metadata",
        "attachments": "Metadata příloh",
    }.get(key, key)


def read_email_archive_attachment_metadata(archive_dir: Path) -> list[dict[str, Any]]:
    attachments_path = archive_dir / "attachments" / "attachments.json"
    if not attachments_path.is_file():
        return []
    try:
        payload = read_json_file(attachments_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return []
    raw_attachments = payload.get("attachments", [])
    if not isinstance(raw_attachments, list):
        return []
    result: list[dict[str, Any]] = []
    for item in raw_attachments:
        if not isinstance(item, dict):
            continue
        result.append(
            {
                "filename": safe_text(str(item.get("filename", "")))[:240],
                "content_type": safe_text(str(item.get("content_type", "")))[:120],
                "size_bytes": int(item.get("size_bytes", 0) or 0),
                "saved": bool(item.get("saved")),
            }
        )
    return result


def downloaded_email_archive_attachments(
    *,
    uid: str,
    documents_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> list[dict[str, Any]]:
    if not uid or not uid.isdigit():
        return []
    incoming = documents_dir / "inbox" / "incoming"
    if not incoming.is_dir():
        return []
    result: list[dict[str, Any]] = []
    for path in sorted(incoming.glob(f"icloud_uid_{uid}_*")):
        if not path.is_file():
            continue
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        result.append(
            {
                "filename": safe_text(path.name)[:240],
                "content_type": _content_type_for_path(path),
                "size_bytes": size,
                "relative_path": safe_text(str(relative_to_project(path)))[:500],
                "url": f"/email-archive/incoming?name={quote(path.name)}",
            }
        )
    return result


def vault_email_archive_attachments(
    *,
    uid: str,
    documents_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> list[dict[str, Any]]:
    """Return redacted links to already imported documents for one email UID."""

    if not uid or not uid.isdigit():
        return []
    uid_pattern = re.compile(rf"(?<!\d){re.escape(uid)}(?!\d)")
    index_path = documents_dir / "index" / "documents_index.jsonl"
    result: list[dict[str, Any]] = []
    for row in read_jsonl(index_path):
        source_coordinates = " ".join(
            str(row.get(key, ""))
            for key in (
                "document_id",
                "title",
                "original_filename",
                "stored_path",
                "case_id",
                "review_source",
            )
        )
        if not uid_pattern.search(source_coordinates):
            continue
        document_id = str(row.get("document_id", "")).strip()
        if not document_id:
            continue
        stored_path = _resolve_vault_document_path(
            str(row.get("stored_path", "")),
            documents_dir=documents_dir,
        )
        reference = document_reference(document_id)
        reading_status = effective_document_reading_status(row)
        result.append(
            {
                "document_ref": reference,
                "title": safe_text(
                    str(
                        row.get("title")
                        or row.get("original_filename")
                        or "Uložená příloha"
                    )
                )[:240],
                "filename": safe_text(str(row.get("original_filename", "")))[:240],
                "domain": safe_text(str(row.get("domain", "")))[:80],
                "document_type": safe_text(str(row.get("document_type", "")))[:100],
                "reading_status": reading_status,
                "reading_status_label": READING_STATUS_LABELS.get(
                    reading_status,
                    reading_status,
                ),
                "size_bytes": (
                    stored_path.stat().st_size
                    if stored_path is not None
                    else int(row.get("size_bytes", 0) or 0)
                ),
                "can_open": stored_path is not None,
                "url": (
                    f"/documents/read?document_id={quote(reference)}"
                    if stored_path is not None
                    else ""
                ),
                "direct_url": (
                    f"/documents/pdf?document_id={quote(reference)}"
                    if stored_path is not None
                    else ""
                ),
            }
        )
    return result[:12]


def _resolve_vault_document_path(
    stored_path: str,
    *,
    documents_dir: Path,
) -> Path | None:
    clean_path = str(stored_path or "").strip()
    if not clean_path:
        return None
    raw = Path(clean_path)
    try:
        root = documents_dir.resolve(strict=True)
    except OSError:
        return None
    candidates = [raw] if raw.is_absolute() else [PROJECT_ROOT / raw]
    if documents_dir != DEFAULT_DOCUMENTS_DIR and not raw.is_absolute():
        candidates.insert(0, documents_dir / raw)
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
        except OSError:
            continue
        if resolved.is_file() and (resolved == root or root in resolved.parents):
            return resolved
    return None


def resolve_email_archive_dir(
    archive_id: str,
    *,
    archive_directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
) -> dict[str, Any]:
    safe_archive_id = str(archive_id or "").strip()
    if (
        not safe_archive_id
        or "/" in safe_archive_id
        or "\\" in safe_archive_id
        or safe_archive_id.startswith(".")
    ):
        return {"ok": False, "message": "Neplatné ID archivu."}
    archive_dir = archive_directory / safe_archive_id
    if EMAIL_ARCHIVE_REFERENCE_PATTERN.fullmatch(safe_archive_id):
        matches = [
            path
            for path in archive_directory.glob("*/metadata.json")
            if email_archive_reference(path.parent.name) == safe_archive_id
        ]
        if len(matches) != 1:
            return {"ok": False, "message": "Archiv nebyl nalezen."}
        archive_dir = matches[0].parent
    elif not archive_dir.is_dir():
        matches = []
        for metadata_path in archive_directory.glob("*/metadata.json"):
            try:
                metadata = read_json_file(metadata_path)
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            display_id = safe_text(
                str(metadata.get("archive_id") or metadata_path.parent.name)
            ).strip()
            if display_id == safe_archive_id:
                matches.append(metadata_path)
        if len(matches) != 1:
            return {"ok": False, "message": "Archiv nebyl nalezen."}
        archive_dir = matches[0].parent
    try:
        root = archive_directory.resolve(strict=True)
        resolved = archive_dir.resolve(strict=True)
    except OSError:
        return {"ok": False, "message": "Archiv nebyl nalezen."}
    if root != resolved and root not in resolved.parents:
        return {"ok": False, "message": "Archiv je mimo povolenou složku."}
    if not (resolved / "metadata.json").is_file():
        return {"ok": False, "message": "Archiv nemá metadata."}
    return {"ok": True, "path": resolved}


def resolve_email_archive_file(
    archive_id: str,
    file_key: str,
    *,
    archive_directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
) -> dict[str, Any]:
    if file_key not in EMAIL_ARCHIVE_OPENABLE_FILES:
        return {"ok": False, "message": "Soubor archivu není povolený."}
    resolved = resolve_email_archive_dir(archive_id, archive_directory=archive_directory)
    if not resolved.get("ok"):
        return resolved
    archive_dir = resolved["path"]
    relative, content_type = EMAIL_ARCHIVE_OPENABLE_FILES[file_key]
    try:
        target = (archive_dir / relative).resolve(strict=True)
    except OSError:
        return {"ok": False, "message": "Soubor archivu nebyl nalezen."}
    if archive_dir != target and archive_dir not in target.parents:
        return {"ok": False, "message": "Soubor archivu je mimo povolenou složku."}
    if not target.is_file():
        return {"ok": False, "message": "Soubor archivu není soubor."}
    return {
        "ok": True,
        "path": target,
        "content_type": content_type,
        "filename": safe_filename(target.name),
    }


def resolve_email_archive_incoming_file(
    name: str,
    *,
    documents_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> dict[str, Any]:
    safe_name = str(name or "").strip()
    if (
        not safe_name
        or "/" in safe_name
        or "\\" in safe_name
        or safe_name.startswith(".")
        or not safe_name.startswith("icloud_uid_")
    ):
        return {"ok": False, "message": "Neplatný název přílohy."}
    incoming = documents_dir / "inbox" / "incoming"
    target = incoming / safe_name
    try:
        root = incoming.resolve(strict=True)
        resolved = target.resolve(strict=True)
    except OSError:
        return {"ok": False, "message": "Příloha nebyla nalezena."}
    if root != resolved and root not in resolved.parents:
        return {"ok": False, "message": "Příloha je mimo povolenou složku."}
    if not resolved.is_file():
        return {"ok": False, "message": "Příloha není soubor."}
    return {
        "ok": True,
        "path": resolved,
        "content_type": _content_type_for_path(resolved),
        "filename": safe_filename(resolved.name),
    }


def _content_type_for_path(path: Path) -> str:
    suffix = path.suffix.casefold()
    return {
        ".html": "text/html; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".eml": "message/rfc822",
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(suffix, "application/octet-stream")
