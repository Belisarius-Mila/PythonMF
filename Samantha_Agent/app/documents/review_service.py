"""Read-only document classification, review, and work status service."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from app.documents.case_service import document_domain_label, document_type_label
from app.documents.scandocu import reviewed_document_ids
from app.documents.search_service import (
    READING_STATUS_LABELS,
    document_reference,
    effective_document_reading_status,
    normalize_reading_status,
)
from app.documents.vault import (
    DEFAULT_DOCUMENTS_DIR,
    PROJECT_ROOT,
    propose_metadata,
    read_jsonl,
    safe_ascii_slug,
    safe_slug,
    safe_text,
)


DOCUMENT_REVIEW_REASON_LABELS: dict[str, str] = {
    "needs_review": "stav čtení k revizi",
    "zero_text": "bez textové vrstvy",
    "short_text": "krátký text",
    "ocr_needed": "OCR kandidát",
    "weak_metadata": "doplnit údaje",
}
DOCUMENT_REVIEW_FIELD_LABELS: dict[str, str] = {
    "domain": "oblast",
    "document_type": "typ dokumentu",
    "counterparty": "protistrana",
    "related_asset": "vazba na auto/projekt/věc",
    "case_id": "case / souvislost",
}
DOCUMENT_REVIEW_GROUPS: tuple[dict[str, str], ...] = (
    {
        "id": "zero_text",
        "label": "Bez textu / OCR",
        "empty_label": "Žádný aktivní dokument bez textové vrstvy.",
        "action": "Spustit OCR nebo po ruční kontrole označit jako OK bez textu.",
    },
    {
        "id": "short_text",
        "label": "Krátký text",
        "empty_label": "Žádný aktivní dokument s podezřele krátkým textem.",
        "action": "Ručně ověřit, zda se načetl celý dokument; případně OCR nebo ruční revize.",
    },
    {
        "id": "weak_metadata",
        "label": "Doplnit údaje",
        "empty_label": "Žádný aktivní dokument se slabými metadaty.",
        "action": "Doplnit metadata: oblast, typ, protistranu nebo související věc.",
    },
    {
        "id": "needs_review",
        "label": "K revizi",
        "empty_label": "Žádný další aktivní dokument označený k revizi.",
        "action": "Otevřít dokument a potvrdit stav čtení.",
    },
    {
        "id": "ok",
        "label": "V pořádku",
        "empty_label": "Zatím žádný aktivní dokument není označený jako OK.",
        "action": "Bez akce.",
    },
)


ReviewStatusLoader = Callable[..., dict[str, Any]]


def download_problem_kind(item: dict[str, Any]) -> str:
    status = str(item.get("status", ""))
    if status in {"already_in_vault", "duplicate", "skipped", "imported"}:
        return ""
    if item.get("is_encrypted"):
        return "encrypted"
    if status == "invalid":
        return "invalid"
    return ""


def with_problem_label(item: dict[str, Any]) -> dict[str, Any]:
    kind = download_problem_kind(item)
    labels = {"encrypted": "šifrované PDF", "invalid": "neplatný soubor"}
    enriched = dict(item)
    enriched["problem_kind"] = kind
    enriched["problem_label"] = labels.get(kind, kind or "problém")
    return enriched


def document_work_status(
    downloads: dict[str, Any],
    *,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 8,
    review_status_loader: ReviewStatusLoader | None = None,
) -> dict[str, Any]:
    items = [item for item in downloads.get("items", []) if isinstance(item, dict)]
    new_pdfs = [item for item in items if item.get("status") == "new"][:limit]
    problems = [with_problem_label(item) for item in items if download_problem_kind(item)][:limit]
    load_review = review_status_loader or stored_documents_review_status
    review = load_review(vault_dir=vault_dir, limit=limit)
    return {
        "new_pdfs": new_pdfs,
        "review": review,
        "problems": problems,
        "summary": {
            "new_pdf_count": sum(1 for item in items if item.get("status") == "new"),
            "problem_count": sum(1 for item in items if download_problem_kind(item)),
            "review_pending_count": review["pending_count"],
        },
    }


def document_classification_status(
    *,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 6,
) -> dict[str, Any]:
    text_by_id = {
        str(item.get("document_id", "")): str(item.get("text", ""))
        for item in read_jsonl(vault_dir / "index" / "text_index.jsonl")
    }
    active_count = 0
    complete_count = 0
    field_counts = {field: 0 for field in DOCUMENT_REVIEW_FIELD_LABELS}
    items: list[dict[str, Any]] = []
    domain_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    for row in read_jsonl(vault_dir / "index" / "documents_index.jsonl"):
        document_id = safe_text(str(row.get("document_id", ""))).strip()
        if not document_id:
            continue
        lifecycle_status = safe_text(str(row.get("lifecycle_status", "active") or "active")).casefold()
        if lifecycle_status in {"archived", "trashed"}:
            continue
        active_count += 1
        domain = safe_text(str(row.get("domain", "")))[:80]
        document_type = safe_text(str(row.get("document_type", "")))[:80]
        counterparty = safe_text(str(row.get("counterparty", "")))[:120]
        related_asset = safe_text(str(row.get("related_asset", "")))[:120]
        case_id = safe_text(str(row.get("case_id", "")))[:120]
        if domain:
            domain_counts[document_domain_label(domain)] = domain_counts.get(document_domain_label(domain), 0) + 1
        if document_type:
            type_counts[document_type_label(document_type)] = type_counts.get(document_type_label(document_type), 0) + 1
        missing_fields = document_classification_missing_fields(
            domain=domain,
            document_type=document_type,
            counterparty=counterparty,
            related_asset=related_asset,
        )
        if not missing_fields:
            complete_count += 1
            continue
        for field in missing_fields:
            field_counts[field] = field_counts.get(field, 0) + 1
        missing_labels = [DOCUMENT_REVIEW_FIELD_LABELS.get(field, field) for field in missing_fields]
        metadata_suggestion = document_classification_metadata_suggestion(
            row=row,
            text=text_by_id.get(document_id, ""),
        )
        recommended_action = (
            "Zkontrolovat automatický návrh a potvrdit zápis."
            if metadata_suggestion.get("can_accept")
            else f"Doplnit: {', '.join(missing_labels)}."
        )
        items.append(
            {
                "document_ref": document_reference(document_id),
                "title": safe_text(str(row.get("title") or row.get("original_filename") or document_id))[:180],
                "domain": domain,
                "domain_label": document_domain_label(domain),
                "document_type": document_type,
                "document_type_label": document_type_label(document_type),
                "counterparty": counterparty,
                "related_asset": related_asset,
                "case_id": case_id,
                "missing_fields": missing_fields,
                "missing_labels": missing_labels,
                "classification_summary": (
                    f"{document_domain_label(domain)} / {document_type_label(document_type)} | "
                    f"{counterparty or 'protistrana chybí'} | {related_asset or 'vazba chybí'}"
                    f"{' | case: ' + case_id if case_id else ''}"
                ),
                "recommended_action": recommended_action,
                "metadata_suggestion": metadata_suggestion,
            }
        )
    items.sort(key=lambda item: (-len(item["missing_fields"]), item["title"].casefold()))
    issue_count = active_count - complete_count
    quality_percent = round((complete_count / active_count) * 100) if active_count else 100
    return {
        "ok": True,
        "active_documents": active_count,
        "complete_count": complete_count,
        "issue_count": issue_count,
        "quality_percent": quality_percent,
        "field_counts": field_counts,
        "field_labels": DOCUMENT_REVIEW_FIELD_LABELS,
        "domain_counts": domain_counts,
        "document_type_counts": type_counts,
        "items": items[:limit],
        "truncated": len(items) > limit,
        "message": (
            f"Klasifikace: {complete_count}/{active_count} dokumentů má kompletní základní metadata "
            f"({quality_percent} %)."
            if active_count
            else "Klasifikace: ve vaultu nejsou aktivní dokumenty."
        ),
    }


def document_classification_metadata_suggestion(row: dict[str, Any], text: str) -> dict[str, Any]:
    document_id = safe_text(str(row.get("document_id", ""))).strip()
    title = safe_text(str(row.get("title") or row.get("original_filename") or document_id))
    stored_path = safe_text(str(row.get("stored_path", ""))).strip()
    source = PROJECT_ROOT / stored_path if stored_path else Path(title or document_id or "document.pdf")
    fallback_text = "\n".join(
        value
        for value in (
            title,
            safe_text(str(row.get("original_filename", ""))),
            safe_text(str(row.get("counterparty", ""))),
            text,
        )
        if value
    )
    proposed = propose_metadata(source=source, text=fallback_text)
    current = {
        "domain": safe_text(str(row.get("domain", "")))[:80],
        "document_type": safe_text(str(row.get("document_type", "")))[:80],
        "counterparty": safe_text(str(row.get("counterparty", "")))[:120],
        "related_asset": safe_text(str(row.get("related_asset", "")))[:120],
    }
    proposed_values = {
        "domain": safe_slug(str(proposed.get("domain", "")), default="", limit=80),
        "document_type": safe_slug(str(proposed.get("document_type", "")), default="", limit=80),
        "counterparty": safe_text(str(proposed.get("counterparty", "")))[:120],
        "related_asset": safe_text(str(proposed.get("related_asset", "")))[:120],
    }
    changes: dict[str, dict[str, str]] = {}
    metadata: dict[str, str] = {}
    for field, proposed_value in proposed_values.items():
        if not proposed_value:
            continue
        current_value = current.get(field, "")
        if not document_metadata_field_needs_suggestion(field, current_value, proposed_value):
            continue
        changes[field] = {
            "field": field,
            "label": DOCUMENT_REVIEW_FIELD_LABELS.get(field, field),
            "current": current_value,
            "proposed": proposed_value,
            "proposed_label": document_metadata_value_label(field, proposed_value),
        }
        metadata[field] = proposed_value
    if not changes:
        return {"can_accept": False, "changes": [], "metadata": {}, "summary": "Automat nemá dost jistý návrh."}
    summary = "; ".join(
        f"{change['label']}: {change['proposed_label']}"
        for change in changes.values()
    )
    return {
        "can_accept": True,
        "confidence": document_metadata_suggestion_confidence(changes),
        "changes": list(changes.values()),
        "metadata": metadata,
        "summary": summary,
    }


def document_metadata_field_needs_suggestion(field: str, current_value: str, proposed_value: str) -> bool:
    current = safe_text(current_value).strip()
    proposed = safe_text(proposed_value).strip()
    if not proposed or current == proposed:
        return False
    current_slug = safe_slug(current, default="", limit=80)
    proposed_slug = safe_slug(proposed, default="", limit=80)
    if field == "domain":
        return current_slug in {"", "other", "unknown"} and proposed_slug not in {"", "other", "unknown"}
    if field == "document_type":
        return current_slug in {"", "document", "unknown", "email-attachment-pdf"} and proposed_slug not in {
            "",
            "document",
            "unknown",
            "email-attachment-pdf",
        }
    if field in {"counterparty", "related_asset"}:
        return not current and bool(proposed)
    return False


def document_metadata_value_label(field: str, value: str) -> str:
    if field == "domain":
        return document_domain_label(value)
    if field == "document_type":
        return document_type_label(value)
    return value


def safe_manual_metadata_slug(value: str, *, limit: int = 80) -> str:
    return safe_ascii_slug(value, default="", limit=limit)


def document_metadata_suggestion_confidence(changes: dict[str, dict[str, str]]) -> str:
    fields = set(changes)
    if "domain" in fields and ("document_type" in fields or "related_asset" in fields):
        return "high"
    if fields:
        return "medium"
    return "low"


def document_classification_missing_fields(
    *,
    domain: str,
    document_type: str,
    counterparty: str,
    related_asset: str,
) -> list[str]:
    missing: list[str] = []
    domain_slug = safe_slug(domain, default="", limit=80)
    type_slug = safe_slug(document_type, default="", limit=80)
    if not domain_slug or domain_slug in {"other", "unknown"}:
        missing.append("domain")
    if not type_slug or type_slug in {"document", "unknown", "email-attachment-pdf"}:
        missing.append("document_type")
    if not safe_text(counterparty):
        missing.append("counterparty")
    if not safe_text(related_asset):
        missing.append("related_asset")
    return missing


def stored_documents_review_status(vault_dir: Path = DEFAULT_DOCUMENTS_DIR, limit: int = 8) -> dict[str, Any]:
    text_by_id = {
        str(item.get("document_id", "")): str(item.get("text", ""))
        for item in read_jsonl(vault_dir / "index" / "text_index.jsonl")
    }
    reviewed_ids = reviewed_document_ids(vault_dir)
    pending: list[dict[str, Any]] = []
    status_counts = {status: 0 for status in READING_STATUS_LABELS}
    for row in read_jsonl(vault_dir / "index" / "documents_index.jsonl"):
        document_id = str(row.get("document_id", ""))
        if not document_id:
            continue
        lifecycle_status = safe_text(str(row.get("lifecycle_status", "active") or "active")).casefold()
        if lifecycle_status in {"archived", "trashed"}:
            continue
        reading_status = effective_document_reading_status(row, text_chars=len(text_by_id.get(document_id, "")))
        status_counts[reading_status] = status_counts.get(reading_status, 0) + 1
        if reading_status != "needs_review":
            continue
        if safe_slug(document_id, default="", limit=140) in reviewed_ids:
            continue
        pending.append(
            {
                "document_id": document_id,
                "title": str(row.get("title") or row.get("original_filename") or document_id),
                "domain": str(row.get("domain", "")),
                "document_type": str(row.get("document_type", "")),
                "stored_path": str(row.get("stored_path", "")),
                "reading_status": reading_status,
                "reading_status_label": READING_STATUS_LABELS[reading_status],
            }
        )
    return {
        "pending_count": len(pending),
        "reviewed_count": status_counts.get("ok", 0),
        "status_counts": status_counts,
        "status_labels": READING_STATUS_LABELS,
        "next_items": pending[:limit],
    }


def document_review_report_status(
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 12,
    short_text_threshold: int = 500,
) -> dict[str, Any]:
    text_by_id = {
        str(item.get("document_id", "")): str(item.get("text", ""))
        for item in read_jsonl(vault_dir / "index" / "text_index.jsonl")
    }
    documents = read_jsonl(vault_dir / "index" / "documents_index.jsonl")
    status_counts = {status: 0 for status in READING_STATUS_LABELS}
    reason_counts = {reason: 0 for reason in DOCUMENT_REVIEW_REASON_LABELS}
    items: list[dict[str, Any]] = []
    grouped_items: dict[str, list[dict[str, Any]]] = {group["id"]: [] for group in DOCUMENT_REVIEW_GROUPS}
    active_count = 0
    for row in documents:
        document_id = str(row.get("document_id", ""))
        if not document_id:
            continue
        lifecycle_status = safe_text(str(row.get("lifecycle_status", "active") or "active")).casefold()
        if lifecycle_status in {"archived", "trashed"}:
            continue
        active_count += 1
        text_chars = len(text_by_id.get(document_id, ""))
        reading_status = effective_document_reading_status(row, text_chars=text_chars)
        status_counts[reading_status] = status_counts.get(reading_status, 0) + 1
        extraction = row.get("text_extraction")
        if not isinstance(extraction, dict):
            extraction = {}

        reasons: list[str] = []
        weak_fields: list[str] = []
        if reading_status == "needs_review":
            reasons.append("needs_review")
        explicit_reading_status = str(row.get("reading_status", "") or row.get("document_reading_status", ""))
        explicit_reading_status_resolved = False
        if explicit_reading_status:
            try:
                explicit_reading_status_resolved = normalize_reading_status(explicit_reading_status) in {
                    "ok",
                    "unreadable",
                    "superseded",
                }
            except ValueError:
                explicit_reading_status_resolved = False
        if not explicit_reading_status_resolved:
            if text_chars == 0:
                reasons.append("zero_text")
            elif text_chars < short_text_threshold:
                reasons.append("short_text")
            if extraction.get("ocr_needed") is True:
                reasons.append("ocr_needed")
        for field, fallback in (("domain", "other"), ("document_type", "document")):
            value = safe_slug(str(row.get(field, "")), default="", limit=80)
            weak_values = {fallback, "unknown"}
            if field == "document_type":
                weak_values.add("email-attachment-pdf")
            if not value or value in weak_values:
                weak_fields.append(field)
        for field in ("counterparty", "related_asset"):
            if not safe_text(str(row.get(field, ""))):
                weak_fields.append(field)
        if weak_fields:
            reasons.append("weak_metadata")

        for reason in set(reasons):
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        if not reasons:
            continue
        weak_labels = [DOCUMENT_REVIEW_FIELD_LABELS.get(field, field) for field in weak_fields]
        reason_labels = [DOCUMENT_REVIEW_REASON_LABELS.get(reason, reason) for reason in reasons]
        if weak_labels and len(reasons) == 1 and reasons[0] == "weak_metadata":
            review_summary = f"Doplnit: {', '.join(weak_labels)}."
        elif weak_labels:
            review_summary = f"Zkontrolovat čtení a doplnit: {', '.join(weak_labels)}."
        else:
            review_summary = "Zkontrolovat čtení dokumentu."
        decision_group = document_review_decision_group(reasons)
        recommended_action = document_review_recommended_action(decision_group, weak_labels)

        item = {
            "document_id": document_id,
            "document_ref": document_reference(document_id),
            "title": safe_text(str(row.get("title") or row.get("original_filename") or document_id))[:180],
            "domain": safe_text(str(row.get("domain", "")))[:80],
            "document_type": safe_text(str(row.get("document_type", "")))[:80],
            "counterparty": safe_text(str(row.get("counterparty", "")))[:120],
            "related_asset": safe_text(str(row.get("related_asset", "")))[:120],
            "reading_status": reading_status,
            "reading_status_label": READING_STATUS_LABELS.get(reading_status, reading_status),
            "text_chars": text_chars,
            "extraction_method": safe_text(str(extraction.get("method", "")))[:80],
            "weak_metadata_fields": weak_fields,
            "weak_metadata_labels": weak_labels,
            "decision_group": decision_group,
            "decision_group_label": document_review_group_label(decision_group),
            "recommended_action": recommended_action,
            "review_summary": review_summary,
            "reading_summary": f"Čtení: {READING_STATUS_LABELS.get(reading_status, reading_status)}, text {text_chars} znaků",
            "classification_summary": (
                f"Oblast: {safe_text(str(row.get('domain', '')))[:80] or 'nezjištěna'}; "
                f"typ: {safe_text(str(row.get('document_type', '')))[:80] or 'nezjištěn'}"
            ),
            "reasons": [
                {"id": reason, "label": label}
                for reason, label in zip(reasons, reason_labels)
            ],
        }
        items.append(item)
        grouped_items.setdefault(decision_group, []).append(item)

    items.sort(
        key=lambda item: (
            0 if any(reason["id"] in {"needs_review", "zero_text", "ocr_needed"} for reason in item["reasons"]) else 1,
            item["text_chars"],
            item["title"].casefold(),
        )
    )
    for group_items in grouped_items.values():
        group_items.sort(
            key=lambda item: (
                item["text_chars"],
                item["title"].casefold(),
            )
        )
    reading_issue_count = sum(
        1
        for item in items
        if any(reason["id"] in {"needs_review", "zero_text", "short_text", "ocr_needed"} for reason in item["reasons"])
    )
    metadata_issue_count = sum(
        1
        for item in items
        if any(reason["id"] == "weak_metadata" for reason in item["reasons"])
    )
    if not items:
        message = f"V pořádku: {active_count} aktivních dokumentů bez zjevné revize."
    elif reading_issue_count == 0:
        message = (
            f"Čtení je v pořádku. {metadata_issue_count} dokumentům chybí doplnit údaje "
            "jako protistrana nebo vazba na auto/projekt."
        )
    else:
        message = (
            f"{len(items)} dokumentů vyžaduje kontrolu: {reading_issue_count} kvůli čtení/OCR, "
            f"{metadata_issue_count} kvůli doplnění údajů."
        )
    groups = document_review_report_groups(
        grouped_items=grouped_items,
        ok_count=max(0, active_count - len(items)),
        limit=limit,
    )
    return {
        "summary": {
            "total_indexed": len(documents),
            "active_documents": active_count,
            "candidate_count": len(items),
            "short_text_threshold": short_text_threshold,
            "status_counts": status_counts,
            "reason_counts": reason_counts,
            "reason_labels": DOCUMENT_REVIEW_REASON_LABELS,
            "field_labels": DOCUMENT_REVIEW_FIELD_LABELS,
        },
        "groups": groups,
        "items": items[:limit],
        "truncated": len(items) > limit,
        "message": message,
    }


def document_review_decision_group(reasons: list[str]) -> str:
    reason_set = set(reasons)
    if "zero_text" in reason_set or "ocr_needed" in reason_set:
        return "zero_text"
    if "short_text" in reason_set:
        return "short_text"
    if "weak_metadata" in reason_set:
        return "weak_metadata"
    if "needs_review" in reason_set:
        return "needs_review"
    return "ok"


def document_review_group_label(group_id: str) -> str:
    for group in DOCUMENT_REVIEW_GROUPS:
        if group["id"] == group_id:
            return group["label"]
    return group_id


def document_review_recommended_action(group_id: str, weak_labels: list[str]) -> str:
    if group_id == "zero_text":
        return "OCR nebo ruční kontrola; pokud dokument text nepotřebuje, označit jako OK bez textu."
    if group_id == "short_text":
        return "Ověřit, zda je text kompletní; při neúplném čtení spustit OCR nebo ruční revizi."
    if group_id == "weak_metadata":
        missing = f": {', '.join(weak_labels)}" if weak_labels else "."
        return f"Doplnit metadata{missing}"
    if group_id == "needs_review":
        return "Otevřít dokument, zkontrolovat čtení a potvrdit stav."
    return "Bez akce."


def document_review_report_groups(
    *,
    grouped_items: dict[str, list[dict[str, Any]]],
    ok_count: int,
    limit: int,
) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for group in DOCUMENT_REVIEW_GROUPS:
        group_id = group["id"]
        if group_id == "ok":
            groups.append(
                {
                    "id": group_id,
                    "label": group["label"],
                    "count": ok_count,
                    "empty_label": group["empty_label"],
                    "recommended_action": group["action"],
                    "items": [],
                    "truncated": False,
                }
            )
            continue
        items = grouped_items.get(group_id, [])
        groups.append(
            {
                "id": group_id,
                "label": group["label"],
                "count": len(items),
                "empty_label": group["empty_label"],
                "recommended_action": group["action"],
                "items": items[:limit],
                "truncated": len(items) > limit,
            }
        )
    return groups



