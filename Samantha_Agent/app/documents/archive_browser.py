"""Read-only listing and detail service for documents stored in the private vault."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.documents.search_service import (
    READING_STATUS_LABELS,
    document_reference,
    effective_document_reading_status,
    normalize_reading_status,
    validated_document_id,
)
from app.documents.vault import (
    DEFAULT_DOCUMENTS_DIR,
    build_snippet,
    read_jsonl,
    resolve_indexed_document_path,
    safe_text,
    tokenize,
)


MAX_STORED_DOCUMENTS = 500
IMAGE_EXTENSIONS = {".gif", ".jpeg", ".jpg", ".png", ".webp"}
HIDDEN_LIFECYCLE_STATES = {"deleted", "trashed"}


def stored_document_list_status(
    *,
    query: str = "",
    domain: str = "",
    reading_status: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = MAX_STORED_DOCUMENTS,
) -> dict[str, Any]:
    """Return one mailbox-like, read-only list without exposing storage identifiers."""

    documents = read_jsonl(vault_dir / "index" / "documents_index.jsonl")
    text_by_id = {
        str(row.get("document_id", "")): str(row.get("text", ""))
        for row in read_jsonl(vault_dir / "index" / "text_index.jsonl")
    }
    query_terms = [term for term in tokenize(query) if len(term) >= 2]
    safe_domain = str(domain or "").strip().casefold()
    normalized_reading_status = (
        normalize_reading_status(reading_status)
        if str(reading_status or "").strip()
        else ""
    )

    all_items: list[tuple[tuple[float, int], dict[str, Any]]] = []
    domain_counts: dict[str, int] = {}
    review_count = 0
    for position, record in enumerate(documents):
        document_id = validated_document_id(record.get("document_id"))
        if not document_id or _document_is_hidden(record):
            continue
        text = text_by_id.get(document_id, "")
        current_reading_status = effective_document_reading_status(
            record,
            text_chars=len(text),
        )
        current_domain = safe_text(str(record.get("domain", "") or "other")) or "other"
        domain_counts[current_domain] = domain_counts.get(current_domain, 0) + 1
        if current_reading_status == "needs_review":
            review_count += 1

        if safe_domain and current_domain.casefold() != safe_domain:
            continue
        if normalized_reading_status and current_reading_status != normalized_reading_status:
            continue
        if query_terms and not _document_matches_query(record, text, query_terms):
            continue

        stored_path = resolve_indexed_document_path(
            str(record.get("stored_path", "")),
            vault_dir=vault_dir,
        )
        original_filename = safe_text(str(record.get("original_filename", "")))
        filename = safe_text(stored_path.name) if stored_path is not None else original_filename
        suffix = (stored_path.suffix if stored_path is not None else Path(original_filename).suffix).lower()
        imported_at = safe_text(str(record.get("imported_at", "")))
        item = {
            "document_ref": document_reference(document_id),
            "title": safe_text(
                str(record.get("title") or original_filename or "Dokument bez názvu")
            )[:260],
            "original_filename": original_filename[:260],
            "domain": current_domain[:100],
            "document_type": safe_text(str(record.get("document_type", "")))[:100],
            "counterparty": safe_text(str(record.get("counterparty", "")))[:220],
            "related_asset": safe_text(str(record.get("related_asset", "")))[:220],
            "tags": _safe_tags(record.get("tags")),
            "imported_at": imported_at[:120],
            "reading_status": current_reading_status,
            "reading_status_label": READING_STATUS_LABELS[current_reading_status],
            "lifecycle_status": safe_text(
                str(record.get("lifecycle_status", "active") or "active")
            )[:80],
            "filename": filename[:260],
            "file_extension": suffix,
            "can_open": stored_path is not None,
            "size_bytes": _safe_int(record.get("size_bytes")),
            "snippet": build_snippet(text, query_terms) if query_terms and text else "",
        }
        all_items.append((_document_sort_key(record, position), item))

    safe_limit = max(1, min(int(limit), MAX_STORED_DOCUMENTS))
    sorted_items = [
        item
        for _sort_key, item in sorted(all_items, key=lambda row: row[0], reverse=True)
    ][:safe_limit]
    return {
        "ok": True,
        "read_only": True,
        "count": len(sorted_items),
        "total_count": sum(domain_counts.values()),
        "review_count": review_count,
        "query": safe_text(query)[:160],
        "active_domain": safe_text(domain)[:100],
        "active_reading_status": normalized_reading_status,
        "domains": [
            {"value": value, "label": value, "count": count}
            for value, count in sorted(
                domain_counts.items(),
                key=lambda row: (-row[1], row[0].casefold()),
            )
        ],
        "items": sorted_items,
    }


def stored_document_detail_status(
    *,
    document_ref: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> dict[str, Any]:
    """Return one safe local detail and a full-file URL for the selected document."""

    resolved = resolve_stored_document_file(
        document_ref=document_ref,
        vault_dir=vault_dir,
    )
    if not resolved.get("ok"):
        return resolved
    record = resolved["record"]
    document_id = resolved["document_id"]
    text = ""
    text_truncated = False
    for row in read_jsonl(vault_dir / "index" / "text_index.jsonl"):
        if str(row.get("document_id", "")) != document_id:
            continue
        text = str(row.get("text", ""))
        text_truncated = bool(row.get("text_truncated", False))
        break
    reading_status = effective_document_reading_status(record, text_chars=len(text))
    path = resolved["path"]
    suffix = path.suffix.lower()
    viewer_kind = (
        "pdf"
        if suffix == ".pdf"
        else ("image" if suffix in IMAGE_EXTENSIONS else "download")
    )
    reference = document_reference(document_id)
    return {
        "ok": True,
        "read_only": True,
        "document_ref": reference,
        "title": safe_text(
            str(record.get("title") or record.get("original_filename") or path.name)
        )[:260],
        "original_filename": safe_text(str(record.get("original_filename", "")))[:260],
        "filename": safe_text(path.name)[:260],
        "domain": safe_text(str(record.get("domain", "")))[:100],
        "document_type": safe_text(str(record.get("document_type", "")))[:100],
        "counterparty": safe_text(str(record.get("counterparty", "")))[:220],
        "related_asset": safe_text(str(record.get("related_asset", "")))[:220],
        "tags": _safe_tags(record.get("tags")),
        "imported_at": safe_text(str(record.get("imported_at", "")))[:120],
        "reading_status": reading_status,
        "reading_status_label": READING_STATUS_LABELS[reading_status],
        "lifecycle_status": safe_text(
            str(record.get("lifecycle_status", "active") or "active")
        )[:80],
        "size_bytes": path.stat().st_size,
        "viewer_kind": viewer_kind,
        "file_url": f"/vault/document?document_ref={reference}",
        "text_preview": build_snippet(text, []) if text else "",
        "text_truncated": text_truncated,
    }


def resolve_stored_document_file(
    *,
    document_ref: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> dict[str, Any]:
    """Resolve one opaque reference to a file proven to stay inside the vault."""

    safe_reference = str(document_ref or "").strip()
    if not safe_reference.startswith("docref-"):
        return {"ok": False, "message": "Dokument nebyl nalezen."}
    for record in read_jsonl(vault_dir / "index" / "documents_index.jsonl"):
        document_id = validated_document_id(record.get("document_id"))
        if (
            not document_id
            or _document_is_hidden(record)
            or document_reference(document_id) != safe_reference
        ):
            continue
        path = resolve_indexed_document_path(
            str(record.get("stored_path", "")),
            vault_dir=vault_dir,
        )
        if path is None:
            return {
                "ok": False,
                "message": "Dokument je v seznamu, ale uložený soubor není dostupný.",
            }
        return {
            "ok": True,
            "document_id": document_id,
            "record": record,
            "path": path,
        }
    return {"ok": False, "message": "Dokument nebyl nalezen."}


def _document_is_hidden(record: dict[str, Any]) -> bool:
    lifecycle_status = str(record.get("lifecycle_status", "")).strip().casefold()
    stored_path = str(record.get("stored_path", "")).replace("\\", "/").casefold()
    return lifecycle_status in HIDDEN_LIFECYCLE_STATES or "/trash/" in stored_path


def _document_matches_query(
    record: dict[str, Any],
    text: str,
    query_terms: list[str],
) -> bool:
    haystack = " ".join(
        [
            text,
            str(record.get("title", "")),
            str(record.get("original_filename", "")),
            str(record.get("domain", "")),
            str(record.get("document_type", "")),
            str(record.get("counterparty", "")),
            str(record.get("related_asset", "")),
            " ".join(
                str(tag)
                for tag in record.get("tags", [])
                if isinstance(tag, str)
            ),
        ]
    ).casefold()
    return all(term.casefold() in haystack for term in query_terms)


def _document_sort_key(record: dict[str, Any], position: int) -> tuple[float, int]:
    imported_at = str(record.get("imported_at", "")).strip()
    if imported_at:
        try:
            parsed = datetime.fromisoformat(imported_at.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.timestamp(), position
        except ValueError:
            pass
    return 0.0, position


def _safe_tags(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [safe_text(str(tag))[:80] for tag in value if safe_text(str(tag))][:30]


def _safe_int(value: object) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0
