"""Read-only document case overview and detail service for Samantha Cockpit."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable

from app.documents.search_service import (
    READING_STATUS_LABELS,
    document_reference,
    effective_document_reading_status,
)
from app.documents.vault import DEFAULT_DOCUMENTS_DIR, read_jsonl, safe_slug, safe_text
from app.reminders.store import DEFAULT_REMINDERS_PATH, load_reminders_store


DOCUMENT_DOMAIN_LABELS: dict[str, str] = {
    "car": "auto",
    "home": "domácnost / bydlení",
    "insurance": "pojištění",
    "tax": "daně",
    "energy": "energie",
    "employment": "práce / zaměstnání",
    "health": "zdraví",
    "telecom": "telefon / internet",
    "warranty": "záruky",
    "other": "ostatní",
}
DOCUMENT_TYPE_LABELS: dict[str, str] = {
    "contract": "smlouva",
    "danove-priznani": "daňové přiznání",
    "document": "dokument",
    "email-attachment-pdf": "PDF příloha e-mailu",
    "employment_contract": "pracovní smlouva",
    "green_card": "zelená karta / potvrzení pojištění",
    "insurance_assistance_card": "asistenční karta",
    "insurance_payment_confirmation": "potvrzení o zaplacení pojistného",
    "invoice": "faktura / doklad",
    "insurance_payment_notice": "předpis platby pojistného",
    "insurance_policy": "pojistná smlouva",
    "lease": "nájemní smlouva",
    "payment_notice": "předpis platby",
    "policy": "smlouva",
    "tax-penzijni-generali": "daňové penzijní potvrzení",
    "confirmation": "potvrzení",
}
DOCUMENT_CASE_GROUP_LABELS: dict[str, str] = {
    "asset": "Vazba podle věci",
    "counterparty": "Vazba podle protistrany",
    "unlinked": "Bez vazby",
}


DueCandidateLoader = Callable[..., list[dict[str, Any]]]
ReminderConflictLoader = Callable[[list[dict[str, Any]]], list[dict[str, Any]]]
StoredPdfChecker = Callable[[str, Path], bool]


@dataclass(frozen=True)
class DocumentCaseDependencies:
    """Runtime collaborators kept outside the read-only case domain."""

    due_candidates: DueCandidateLoader
    reminder_conflicts: ReminderConflictLoader
    stored_pdf_is_openable: StoredPdfChecker


def document_case_reference(group_key: str) -> str:
    digest = hashlib.sha256(group_key.encode("utf-8")).hexdigest()[:16]
    return f"caseref-{digest}"


def reminder_reference(reminder_id: str) -> str:
    digest = hashlib.sha256(reminder_id.encode("utf-8")).hexdigest()[:16]
    return f"remref-{digest}"


def document_domain_label(value: str) -> str:
    clean = safe_slug(value, default="", limit=80)
    return DOCUMENT_DOMAIN_LABELS.get(clean, safe_text(value) or "oblast nezjištěna")


def document_type_label(value: str) -> str:
    clean = safe_slug(value, default="", limit=80)
    return DOCUMENT_TYPE_LABELS.get(clean, safe_text(value) or "typ nezjištěn")


def document_case_group_type_label(value: str) -> str:
    clean = safe_slug(value, default="", limit=80)
    return DOCUMENT_CASE_GROUP_LABELS.get(clean, safe_text(value) or "Vazba")


def document_case_summary(
    *,
    group_type: str,
    label: str,
    document_count: int,
    domains: list[str],
    document_types: list[str],
) -> str:
    group_label = document_case_group_type_label(group_type)
    domain_text = ", ".join(document_domain_label(value) for value in domains) or "oblast nezjištěna"
    type_text = ", ".join(document_type_label(value) for value in document_types[:3]) or "typ nezjištěn"
    if group_type == "asset":
        reason = (
            f"Samostatná související věc: {label}."
            if document_count == 1
            else f"Dokumenty mají stejnou související věc: {label}."
        )
    elif group_type == "counterparty":
        reason = (
            f"Dokument zatím nemá věc, ale má protistranu: {label.replace('Protistrana: ', '')}."
            if document_count == 1
            else f"Dokumenty zatím nemají věc, ale sdílí stejnou protistranu: {label.replace('Protistrana: ', '')}."
        )
    else:
        reason = (
            "Dokument zatím nemá vyplněnou věc ani protistranu."
            if document_count == 1
            else "Dokumenty zatím nemají vyplněnou věc ani protistranu."
        )
    return f"{group_label}: {reason} {document_count} dokumentů; {domain_text}; {type_text}."


def document_case_asset_matches(value: str, case_assets: set[str]) -> bool:
    candidate = normalize_reminder_asset(value)
    if not candidate:
        return False
    for asset in case_assets:
        normalized = normalize_reminder_asset(asset)
        if len(normalized) < 3:
            continue
        if candidate == normalized or candidate in normalized or normalized in candidate:
            return True
    return False


def normalize_reminder_asset(value: str) -> str:
    text = safe_text(value).strip()
    if not text:
        return ""
    return " ".join(text.upper().replace("/", " ").split())


def open_reminder_records(reminders_path: Path) -> list[dict[str, Any]]:
    try:
        reminders = load_reminders_store(reminders_path).get("reminders", [])
    except (OSError, ValueError):
        reminders = []
    return [
        item
        for item in reminders
        if isinstance(item, dict) and safe_text(str(item.get("status", ""))).casefold() == "open"
    ]


def parse_reminder_due_date(value: Any) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def public_document_case_reminder(raw: dict[str, Any], today: date) -> dict[str, Any]:
    due_date = parse_reminder_due_date(raw.get("due_date"))
    source = raw.get("source") if isinstance(raw.get("source"), dict) else {}
    reminder_id = str(raw.get("id", ""))
    return {
        "reminder_ref": reminder_reference(reminder_id),
        "title": safe_text(str(raw.get("title", "")))[:180],
        "due_date": due_date.isoformat() if due_date else "",
        "days_until": (due_date - today).days if due_date else 999999,
        "priority": safe_text(str(raw.get("priority", "")))[:32],
        "status": safe_text(str(raw.get("status", "")))[:32],
        "source_type": safe_text(str(source.get("type", "")))[:64],
        "related_asset": safe_text(str(raw.get("related_asset", "")))[:180],
        "coverage_start": safe_text(str(raw.get("coverage_start", "")))[:40],
        "amount_due": safe_text(str(raw.get("amount_due", "")))[:80],
        "amount_note": safe_text(str(raw.get("amount_note", "")))[:240],
        "conflict_note": safe_text(str(raw.get("conflict_note", "")))[:500],
    }


def public_document_case_conflict(conflict: dict[str, Any]) -> dict[str, Any]:
    public = dict(conflict)
    public["items"] = [
        {key: value for key, value in item.items() if key != "id"}
        for item in conflict.get("items", [])
        if isinstance(item, dict)
    ]
    return public


def public_document_due_candidate(item: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in item.items()
        if key not in {"document_id", "archive_id", "reminder_id", "case_id"}
    }


def document_case_health_status(
    *,
    documents: list[dict[str, Any]] | None = None,
    reminders: list[dict[str, Any]],
    due_candidates: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
) -> dict[str, Any]:
    document_items = documents or []
    actionable_count = sum(1 for item in due_candidates if item.get("status") == "ready")
    already_count = sum(1 for item in due_candidates if item.get("status") == "already_reminded")
    conflict_count = len(conflicts)
    reminder_count = len(reminders)
    review_document_count = sum(
        1
        for item in document_items
        if str(item.get("reading_status", "") or "").casefold() in {"needs_review", "unreadable"}
    )
    signals: list[dict[str, str]] = []
    if conflict_count:
        signals.append({
            "level": "bad",
            "label": "Konflikt",
            "detail": f"{conflict_count} konfliktů v připomínkách nebo platbách.",
            "next_action": "Porovnat konfliktní podklady a nekonat platbu naslepo.",
        })
    if actionable_count:
        signals.append({
            "level": "warn",
            "label": "Termíny ke schválení",
            "detail": f"{actionable_count} termínů z dokumentů čeká na rozhodnutí.",
            "next_action": "Ověřit, zda jde o skutečný závazek, a případně vytvořit připomínku.",
        })
    if review_document_count:
        signals.append({
            "level": "warn",
            "label": "Dokumenty k revizi",
            "detail": f"{review_document_count} dokumentů v case není potvrzeno jako OK.",
            "next_action": "Otevřít dokumenty k revizi a doplnit stav čtení.",
        })
    if reminder_count:
        signals.append({
            "level": "ok",
            "label": "Otevřené hlídání",
            "detail": f"{reminder_count} otevřených připomínek je navázáno na case.",
            "next_action": "Bez nové akce, pokud připomínka odpovídá platnému závazku.",
        })
    if already_count:
        signals.append({
            "level": "ok",
            "label": "Termíny už hlídané",
            "detail": f"{already_count} termínů už má existující připomínku.",
            "next_action": "Nevytvářet duplicitní připomínku.",
        })
    if conflict_count:
        status = "bad"
        label = "konflikt"
        recommendation = "Nejdřív porovnat konfliktní připomínky a nekonat platbu naslepo."
    elif actionable_count or review_document_count:
        status = "warn"
        label = "zkontrolovat"
        recommendation = "Zkontrolovat termíny nebo dokumenty k revizi a akci udělat jen pro skutečně platný závazek."
    elif reminder_count or already_count:
        status = "ok"
        label = "hlídáno"
        recommendation = "Nic nového není potřeba; case už má existující hlídání nebo připomínku."
    else:
        status = "ok"
        label = "bez akce"
        recommendation = "Není nalezen konflikt ani termín, který by teď vyžadoval akci."
    if not signals:
        signals.append({
            "level": "ok",
            "label": "Bez akčního nálezu",
            "detail": "Case nemá konflikt, nový termín ke schválení ani dokument k revizi.",
            "next_action": "Nic akutního.",
        })
    return {
        "status": status,
        "label": label,
        "open_reminder_count": reminder_count,
        "actionable_due_count": actionable_count,
        "already_reminded_due_count": already_count,
        "conflict_count": conflict_count,
        "review_document_count": review_document_count,
        "signals": signals,
        "summary": (
            f"Stav: připomínky {reminder_count}, konflikty {conflict_count}, "
            f"termíny ke schválení {actionable_count}, dokumenty k revizi {review_document_count}. "
            f"Doporučení: {recommendation}"
        ),
    }


def _group_identity(related_asset: str, counterparty: str) -> tuple[str, str, str]:
    if related_asset:
        return "asset", related_asset, f"asset:{related_asset.casefold()}"
    if counterparty:
        return "counterparty", f"Protistrana: {counterparty}", f"counterparty:{counterparty.casefold()}"
    return "unlinked", "Bez vazby", "unlinked:"


def document_cases_status(
    *,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 6,
    documents_per_case: int = 3,
) -> dict[str, Any]:
    groups: dict[str, dict[str, Any]] = {}
    active_count = linked_count = unlinked_count = 0
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
        group_type, group_label, group_key = _group_identity(related_asset, counterparty)
        if group_type == "asset":
            linked_count += 1
        else:
            unlinked_count += 1
        group = groups.setdefault(group_key, {
            "case_ref": document_case_reference(group_key),
            "label": group_label,
            "group_type": group_type,
            "document_count": 0,
            "domains": set(),
            "document_types": set(),
            "documents": [],
        })
        group["document_count"] += 1
        if domain:
            group["domains"].add(domain)
        if document_type:
            group["document_types"].add(document_type)
        if len(group["documents"]) < max(1, documents_per_case):
            reading_status = effective_document_reading_status(row)
            group["documents"].append({
                "document_ref": document_reference(document_id),
                "title": safe_text(str(row.get("title") or row.get("original_filename") or document_id))[:180],
                "domain": domain,
                "domain_label": document_domain_label(domain),
                "document_type": document_type,
                "document_type_label": document_type_label(document_type),
                "counterparty": counterparty,
                "related_asset": related_asset,
                "reading_status": reading_status,
                "reading_status_label": READING_STATUS_LABELS.get(reading_status, reading_status),
            })
    all_groups = [{
        "case_ref": group["case_ref"],
        "label": group["label"],
        "group_type": group["group_type"],
        "group_type_label": document_case_group_type_label(group["group_type"]),
        "summary": document_case_summary(
            group_type=str(group["group_type"]),
            label=str(group["label"]),
            document_count=int(group["document_count"]),
            domains=sorted(group["domains"]),
            document_types=sorted(group["document_types"]),
        ),
        "document_count": group["document_count"],
        "domains": sorted(group["domains"]),
        "domain_labels": [document_domain_label(value) for value in sorted(group["domains"])],
        "document_types": sorted(group["document_types"]),
        "document_type_labels": [document_type_label(value) for value in sorted(group["document_types"])],
        "documents": group["documents"],
    } for group in groups.values()]
    cases = [item for item in all_groups if int(item["document_count"]) >= 2]
    singletons_count = sum(1 for item in all_groups if int(item["document_count"]) == 1)
    cases.sort(key=lambda item: (
        0 if item["group_type"] == "asset" else 1 if item["group_type"] == "counterparty" else 2,
        -int(item["document_count"]),
        str(item["label"]).casefold(),
    ))
    return {
        "ok": True,
        "active_documents": active_count,
        "candidate_group_count": len(all_groups),
        "case_count": len(cases),
        "singletons_count": singletons_count,
        "linked_count": linked_count,
        "unlinked_count": unlinked_count,
        "cases": cases[:limit],
        "truncated": len(cases) > limit,
        "message": (
            f"{len(cases)} skutečných vazeb/cases; {singletons_count} samostatných dokumentů skryto; "
            f"{unlinked_count} dokumentů bez related_asset."
            if active_count
            else "Ve vaultu nejsou aktivní dokumenty pro vazby."
        ),
    }


def document_case_detail_status(
    case_ref: str,
    *,
    dependencies: DocumentCaseDependencies,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    reminders_path: Path = DEFAULT_REMINDERS_PATH,
    today: date | None = None,
    limit: int = 30,
) -> dict[str, Any]:
    safe_case_ref = safe_slug(case_ref, default="", limit=140)
    if not safe_case_ref:
        return {"ok": False, "message": "Chybí case_ref.", "documents": []}
    today_date = today or date.today()
    groups: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(vault_dir / "index" / "documents_index.jsonl"):
        document_id = safe_text(str(row.get("document_id", ""))).strip()
        if not document_id:
            continue
        lifecycle_status = safe_text(str(row.get("lifecycle_status", "active") or "active")).casefold()
        if lifecycle_status in {"archived", "trashed"}:
            continue
        domain = safe_text(str(row.get("domain", "")))[:80]
        document_type = safe_text(str(row.get("document_type", "")))[:80]
        counterparty = safe_text(str(row.get("counterparty", "")))[:180]
        related_asset = safe_text(str(row.get("related_asset", "")))[:180]
        group_type, group_label, group_key = _group_identity(related_asset, counterparty)
        group = groups.setdefault(group_key, {
            "case_ref": document_case_reference(group_key),
            "label": group_label,
            "group_type": group_type,
            "domains": set(),
            "document_types": set(),
            "documents": [],
            "document_ids": set(),
        })
        group["document_ids"].add(document_id)
        if domain:
            group["domains"].add(domain)
        if document_type:
            group["document_types"].add(document_type)
        reading_status = effective_document_reading_status(row)
        group["documents"].append({
            "document_ref": document_reference(document_id),
            "title": safe_text(str(row.get("title") or row.get("original_filename") or document_id))[:220],
            "domain": domain,
            "domain_label": document_domain_label(domain),
            "document_type": document_type,
            "document_type_label": document_type_label(document_type),
            "counterparty": counterparty,
            "related_asset": related_asset,
            "reading_status": reading_status,
            "reading_status_label": READING_STATUS_LABELS.get(reading_status, reading_status),
            "can_open_pdf": dependencies.stored_pdf_is_openable(
                safe_text(str(row.get("stored_path", "")))[:500], vault_dir
            ),
        })

    for group in groups.values():
        if group["case_ref"] != safe_case_ref or len(group["documents"]) < 2:
            continue
        documents = sorted(group["documents"], key=lambda item: (
            str(item.get("document_type_label", "")).casefold(),
            str(item.get("title", "")).casefold(),
        ))
        raw_document_ids = {str(item) for item in group["document_ids"] if str(item).strip()}
        document_refs = {document_reference(document_id) for document_id in raw_document_ids}
        case_assets = {
            safe_text(str(doc.get("related_asset", ""))).strip()
            for doc in documents
            if safe_text(str(doc.get("related_asset", ""))).strip()
        }
        if str(group["group_type"]) == "asset":
            case_assets.add(safe_text(str(group["label"])).strip())
        open_reminders = open_reminder_records(reminders_path)
        case_open_reminders = []
        for reminder in open_reminders:
            source = reminder.get("source") if isinstance(reminder.get("source"), dict) else {}
            source_uid = safe_text(str(source.get("uid", ""))).strip()
            related_asset = safe_text(str(reminder.get("related_asset", ""))).strip()
            if (
                source_uid in raw_document_ids
                or source_uid in document_refs
                or document_case_asset_matches(related_asset, case_assets)
            ):
                case_open_reminders.append(reminder)
        case_open_reminders.sort(key=lambda item: (
            parse_reminder_due_date(item.get("due_date")) or date.max,
            safe_text(str(item.get("title", ""))).casefold(),
        ))
        due_candidates = [
            item
            for item in dependencies.due_candidates(
                vault_dir=vault_dir, reminders_path=reminders_path, today=today_date
            )
            if str(item.get("document_id", "")).strip() in raw_document_ids
            or document_case_asset_matches(str(item.get("related_asset", "")), case_assets)
        ]
        conflicts = [
            conflict
            for conflict in dependencies.reminder_conflicts(open_reminders)
            if document_case_asset_matches(str(conflict.get("asset", "")), case_assets)
        ]
        public_reminders = [public_document_case_reminder(item, today_date) for item in case_open_reminders]
        public_due_candidates = [public_document_due_candidate(item) for item in due_candidates]
        public_conflicts = [public_document_case_conflict(item) for item in conflicts]
        return {
            "ok": True,
            "case_ref": safe_case_ref,
            "label": safe_text(str(group["label"]))[:180],
            "group_type": safe_text(str(group["group_type"]))[:80],
            "group_type_label": document_case_group_type_label(str(group["group_type"])),
            "summary": document_case_summary(
                group_type=str(group["group_type"]),
                label=str(group["label"]),
                document_count=len(documents),
                domains=sorted(group["domains"]),
                document_types=sorted(group["document_types"]),
            ),
            "document_count": len(documents),
            "documents": documents[:max(1, limit)],
            "reminders": public_reminders,
            "due_candidates": public_due_candidates,
            "conflicts": public_conflicts,
            "case_health": document_case_health_status(
                documents=documents,
                reminders=public_reminders,
                due_candidates=public_due_candidates,
                conflicts=public_conflicts,
            ),
            "truncated": len(documents) > max(1, limit),
            "message": "Detail case načten.",
        }
    return {"ok": False, "message": "Case nebyl nalezen nebo má jen jeden dokument.", "documents": []}
