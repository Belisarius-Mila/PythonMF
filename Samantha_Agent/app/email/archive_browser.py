from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

from app.documents.search_service import (
    READING_STATUS_LABELS,
    document_reference,
    effective_document_reading_status,
)
from app.documents.vault import (
    DEFAULT_DOCUMENTS_DIR,
    PROJECT_ROOT,
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
EMAIL_ARCHIVE_BODY_TEXT_MAX_BYTES = 512 * 1024


def email_archive_reference(archive_directory_name: str) -> str:
    digest = hashlib.sha256(archive_directory_name.encode("utf-8")).hexdigest()[:16]
    return f"archive-ref-{digest}"


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

    for metadata_path in sorted(
        archive_directory.glob("*/metadata.json"),
        key=lambda path: path.stat().st_mtime if path.exists() else 0,
        reverse=True,
    ):
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
            }
        )
        if len(archives) >= safe_limit:
            break

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
            payload = handle.read(safe_limit + 1)
    except OSError:
        return "", False
    truncated = len(payload) > safe_limit
    if truncated:
        payload = payload[:safe_limit]
    return payload.decode("utf-8", errors="replace").replace("\x00", " "), truncated


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
