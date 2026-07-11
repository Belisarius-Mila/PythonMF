"""Read-only document and purchase search service for Samantha Cockpit."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from app.documents.vault import (
    DEFAULT_DOCUMENTS_DIR,
    PROJECT_ROOT,
    build_snippet,
    read_json_file,
    read_jsonl,
    relative_to_project,
    safe_ascii_slug,
    safe_slug,
    safe_text,
    sanitize_output,
    tokenize,
)
from app.email.redaction import redact_email_addresses


DEFAULT_PURCHASES_DIR = PROJECT_ROOT / "data" / "private" / "purchases"
READING_STATUS_LABELS = {
    "ok": "OK",
    "needs_review": "k revizi",
    "unreadable": "nečitelné",
    "superseded": "nahrazeno lepší kopií",
}
READING_STATUS_ALIASES = {
    "ok": "ok",
    "k": "ok",
    "o.k.": "ok",
    "needs_review": "needs_review",
    "k-revizi": "needs_review",
    "k_revizi": "needs_review",
    "revize": "needs_review",
    "unreadable": "unreadable",
    "necitelne": "unreadable",
    "nečitelné": "unreadable",
    "superseded": "superseded",
    "nahrazeno": "superseded",
    "nahrazeno-lepsi-kopii": "superseded",
    "nahrazeno_lepsi_kopii": "superseded",
}


def normalize_reading_status(value: str) -> str:
    normalized = safe_slug(value, default="", limit=80)
    if normalized in READING_STATUS_LABELS:
        return normalized
    alias = READING_STATUS_ALIASES.get(normalized)
    if alias:
        return alias
    raise ValueError("Neznámý stav čtení dokumentu.")


def effective_document_reading_status(record: dict[str, Any], text_chars: int | None = None) -> str:
    explicit = str(record.get("reading_status", "") or record.get("document_reading_status", ""))
    if explicit:
        try:
            return normalize_reading_status(explicit)
        except ValueError:
            pass
    indexed_chars = text_chars
    if indexed_chars is None:
        extraction = record.get("text_extraction")
        if isinstance(extraction, dict):
            try:
                indexed_chars = int(extraction.get("indexed_chars") or 0)
            except (TypeError, ValueError):
                indexed_chars = 0
        else:
            indexed_chars = 0
    return "ok" if indexed_chars > 0 else "needs_review"


def document_reference(document_id: str) -> str:
    return f"docref-{hashlib.sha256(document_id.encode('utf-8')).hexdigest()[:16]}"


def purchase_reference(purchase_id: str) -> str:
    return f"purref-{hashlib.sha256(purchase_id.encode('utf-8')).hexdigest()[:16]}"


def search_document_index(
    query: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    purchases_dir: Path | None = None,
    limit: int = 8,
) -> dict[str, Any]:
    terms = [term.casefold() for term in tokenize(query) if len(term) >= 2]
    if not terms:
        return {"ok": False, "message": "Zadej konkrétnější dotaz.", "results": []}
    query_intent = document_search_query_intent(query=query, terms=terms)

    documents = {
        str(item.get("document_id", "")): item
        for item in read_jsonl(vault_dir / "index" / "documents_index.jsonl")
        if str(item.get("document_id", "")).strip()
    }
    text_by_id = {
        str(item.get("document_id", "")): str(item.get("text", ""))
        for item in read_jsonl(vault_dir / "index" / "text_index.jsonl")
    }
    scored: list[tuple[int, dict[str, Any], str, int]] = []
    for document_id, metadata in documents.items():
        text = text_by_id.get(document_id, "")
        haystack = " ".join(
            [
                text,
                str(metadata.get("title", "")),
                str(metadata.get("original_filename", "")),
                str(metadata.get("document_id", "")),
                str(metadata.get("stored_path", "")),
                str(metadata.get("document_type", "")),
                str(metadata.get("domain", "")),
                str(metadata.get("counterparty", "")),
                str(metadata.get("related_asset", "")),
                " ".join(str(tag) for tag in metadata.get("tags", []) if isinstance(tag, str)),
            ]
        ).casefold()
        score = sum(haystack.count(term) for term in terms)
        if score <= 0:
            continue
        snippet = build_snippet(text, terms) if text else ""
        if not snippet.strip():
            snippet = "Text zatím není k dispozici; shoda je podle metadat."
        haystack_normalized_terms = {
            safe_ascii_slug(term, default=term, limit=80).casefold()
            for term in tokenize(haystack)
        }
        score += document_search_intent_bonus(
            metadata=metadata,
            query_intent=query_intent,
            haystack_normalized_terms=haystack_normalized_terms,
        )
        if score <= 0:
            continue
        scored.append((score, metadata, snippet, len(text)))

    results: list[dict[str, Any]] = []
    for score, metadata, snippet, text_chars in sorted(scored, key=lambda row: row[0], reverse=True):
        reading_status = effective_document_reading_status(metadata, text_chars=text_chars)
        results.append(
            {
                "score": score,
                "source_type": "document",
                "source_label": "Dokument",
                "document_ref": document_reference(str(metadata.get("document_id", ""))),
                "document_id": safe_text(str(metadata.get("document_id", ""))),
                "title": safe_text(str(metadata.get("title") or metadata.get("original_filename") or "")),
                "original_filename": safe_text(str(metadata.get("original_filename", ""))),
                "domain": safe_text(str(metadata.get("domain", ""))),
                "document_type": safe_text(str(metadata.get("document_type", ""))),
                "counterparty": safe_text(str(metadata.get("counterparty", ""))),
                "related_asset": safe_text(str(metadata.get("related_asset", ""))),
                "stored_path": safe_text(str(metadata.get("stored_path", ""))),
                "lifecycle_status": safe_text(str(metadata.get("lifecycle_status", "active") or "active")),
                "reading_status": reading_status,
                "reading_status_label": READING_STATUS_LABELS[reading_status],
                "snippet": sanitize_output(snippet),
            }
        )
    resolved_purchases_dir = purchases_dir
    if resolved_purchases_dir is None:
        resolved_purchases_dir = DEFAULT_PURCHASES_DIR if vault_dir == DEFAULT_DOCUMENTS_DIR else vault_dir.parent / "purchases"
    results.extend(search_purchase_manifests(query=query, terms=terms, purchases_dir=resolved_purchases_dir))
    limited_results = sorted(results, key=lambda row: int(row.get("score", 0)), reverse=True)[
        : max(1, min(limit, 20))
    ]
    return {
        "ok": True,
        "query": query,
        "count": len(limited_results),
        "results": limited_results,
        "message": "Nalezena shoda." if limited_results else "V dokumentech ani nákupech jsem nenašla shodu.",
    }


def search_purchase_manifests(
    query: str,
    terms: list[str],
    purchases_dir: Path = DEFAULT_PURCHASES_DIR,
) -> list[dict[str, Any]]:
    if not purchases_dir.exists():
        return []
    scored: list[tuple[int, dict[str, Any]]] = []
    query_slug_terms = {safe_ascii_slug(term, default=term, limit=80).casefold() for term in terms}
    for manifest_path in purchases_dir.glob("*/*/invoice_manifest.json"):
        try:
            manifest = read_json_file(manifest_path)
        except ValueError:
            continue
        haystack = purchase_manifest_haystack(manifest=manifest, manifest_path=manifest_path)
        folded = haystack.casefold()
        slug_terms = {safe_ascii_slug(term, default=term, limit=80).casefold() for term in tokenize(haystack)}
        score = sum(folded.count(term) for term in terms)
        score += sum(1 for term in query_slug_terms if term and term in slug_terms)
        if score <= 0:
            continue
        scored.append((score, purchase_manifest_result(manifest=manifest, manifest_path=manifest_path, score=score)))
    return [result for _, result in sorted(scored, key=lambda row: row[0], reverse=True)]


def purchase_manifest_haystack(manifest: dict[str, Any], manifest_path: Path) -> str:
    parts = [
        str(manifest_path.parent.name),
        str(manifest_path.parent.parent.name),
        str(manifest.get("uid", "")),
        str(manifest.get("date", "")),
        str(manifest.get("sender", "")),
        str(manifest.get("subject", "")),
        "nákup nakup nákupy nakupy záruka zaruka faktura invoice účtenka uctenka objednávka objednavka",
    ]
    for attachment in manifest.get("attachments", []):
        if not isinstance(attachment, dict):
            continue
        parts.extend(
            [
                str(attachment.get("filename", "")),
                str(attachment.get("stored_path", "")),
                str(attachment.get("content_type", "")),
            ]
        )
    joined = " ".join(parts)
    if "dolphin" in joined.casefold():
        joined += " bazén bazen bazénový bazenovy robot vysavač vysavac čistič cistic bazénu bazenu"
    return joined


def purchase_manifest_result(manifest: dict[str, Any], manifest_path: Path, score: int) -> dict[str, Any]:
    purchase_id = f"purchase-{manifest_path.parent.parent.name}-{manifest_path.parent.name}"
    attachments = [item for item in manifest.get("attachments", []) if isinstance(item, dict)]
    primary_attachment = attachments[0] if attachments else {}
    stored_path = str(primary_attachment.get("stored_path", ""))
    filename = str(primary_attachment.get("filename", "")) or manifest_path.name
    seller = redact_email_addresses(str(manifest.get("sender", "")))
    subject = str(manifest.get("subject", "")) or "Nákup / faktura"
    title = f"Nákup / záruka: {subject}"
    date_text = str(manifest.get("date", ""))
    snippet_parts = [
        f"Uložený nákup v private archivu: {manifest_path.parent.name}.",
        f"Datum e-mailu: {date_text}." if date_text else "",
        f"Prodejce: {seller}." if seller else "",
        f"Příloha: {filename}." if filename else "",
    ]
    snippet = " ".join(part for part in snippet_parts if part)
    return {
        "score": score,
        "source_type": "purchase",
        "source_label": "Nákup / záruka",
        "document_ref": purchase_reference(purchase_id),
        "document_id": safe_text(purchase_id),
        "title": safe_text(title),
        "original_filename": safe_text(filename),
        "domain": "purchases",
        "document_type": "purchase_invoice",
        "counterparty": safe_text(seller),
        "related_asset": safe_text(manifest_path.parent.name),
        "stored_path": safe_text(stored_path or str(relative_to_project(manifest_path))),
        "lifecycle_status": "active",
        "reading_status": "metadata_only",
        "reading_status_label": "metadata",
        "snippet": sanitize_output(snippet),
    }


INVOICE_QUERY_TERMS = {
    "faktura",
    "faktury",
    "fakturace",
    "invoice",
    "vyuctovani",
    "vyúčtování",
    "danovy",
    "daňový",
    "doklad",
}

INVOICE_DOCUMENT_TYPES = {
    "invoice",
    "tax_invoice",
    "receipt",
    "bill",
}

QUOTE_DOCUMENT_TYPES = {
    "nabidka",
    "nabídka",
    "offer",
    "price_quote",
    "quotation",
    "quote",
}


def document_search_query_intent(query: str, terms: list[str]) -> dict[str, Any]:
    normalized_terms = [safe_ascii_slug(term, default=term, limit=80).casefold() for term in terms]
    routing_terms = INVOICE_QUERY_TERMS | {"pdf"}
    return {
        "wants_invoice": bool(set(terms) & INVOICE_QUERY_TERMS or set(normalized_terms) & INVOICE_QUERY_TERMS),
        "wants_pdf": "pdf" in normalized_terms,
        "content_terms": [term for term in normalized_terms if term not in routing_terms],
        "normalized_terms": normalized_terms,
        "normalized_query": safe_ascii_slug(query, default="", limit=200).casefold(),
    }


def document_search_intent_bonus(
    metadata: dict[str, Any],
    query_intent: dict[str, Any],
    haystack_normalized_terms: set[str],
) -> int:
    bonus = 0
    normalized_terms = set(query_intent.get("normalized_terms", []))
    content_terms = set(query_intent.get("content_terms", []))
    document_type = safe_ascii_slug(str(metadata.get("document_type", "")), default="", limit=80).casefold()
    original_filename = str(metadata.get("original_filename", "")).casefold()
    stored_path = str(metadata.get("stored_path", "")).casefold()
    is_pdf = original_filename.endswith(".pdf") or stored_path.endswith(".pdf")

    if content_terms:
        missing_terms = content_terms - haystack_normalized_terms
        if not missing_terms:
            bonus += 80
        else:
            bonus -= 80 * len(missing_terms)

    if query_intent.get("wants_invoice"):
        if document_type in INVOICE_DOCUMENT_TYPES or "invoice" in document_type:
            bonus += 100
        if document_type in QUOTE_DOCUMENT_TYPES:
            bonus -= 80
        if is_pdf:
            bonus += 15

    if query_intent.get("wants_pdf") and is_pdf:
        bonus += 35

    for field_name, field_bonus in (
        ("domain", 45),
        ("related_asset", 30),
        ("counterparty", 20),
    ):
        field_slug = safe_ascii_slug(str(metadata.get(field_name, "")), default="", limit=160).casefold()
        if not field_slug:
            continue
        field_parts = {part for part in field_slug.split("-") if len(part) >= 2}
        if field_parts and field_parts.issubset(normalized_terms):
            bonus += field_bonus

    return bonus
