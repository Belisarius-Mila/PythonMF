"""Read-only due-date candidate service for documents and archived email."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from app.documents.case_service import document_domain_label, document_type_label, reminder_reference
from app.documents.search_service import document_reference
from app.documents.vault import DEFAULT_DOCUMENTS_DIR, read_json_file, read_jsonl, safe_slug, safe_text, sanitize_output
from app.email.archive_service import DEFAULT_EMAIL_ARCHIVE_DIR
from app.email.redaction import redact_email_addresses
from app.reminders.store import DEFAULT_REMINDERS_PATH, load_reminders_store


DOCUMENT_DUE_TYPE_LABELS: dict[str, str] = {
    "payment_due": "platba",
    "valid_until": "konec platnosti",
    "service_due": "servis / revize",
    "deadline": "termín",
    "context_date": "kontextové datum",
    "unknown_date": "nejasné datum",
}


def document_due_candidates_status(
    *,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    reminders_path: Path = DEFAULT_REMINDERS_PATH,
    archive_directory: Path | None = None,
    today: date | None = None,
    limit: int = 8,
    stale_past_due_days: int = 90,
) -> dict[str, Any]:
    today_date = today or date.today()
    effective_archive_directory = (
        archive_directory
        if archive_directory is not None
        else DEFAULT_EMAIL_ARCHIVE_DIR
        if vault_dir == DEFAULT_DOCUMENTS_DIR
        else None
    )
    document_candidates = build_document_due_candidates(
        vault_dir=vault_dir,
        reminders_path=reminders_path,
        today=today_date,
    )
    email_candidates = (
        build_email_archive_due_candidates(
            archive_directory=effective_archive_directory,
            reminders_path=reminders_path,
            today=today_date,
        )
        if effective_archive_directory is not None
        else []
    )
    all_candidates = document_candidates + email_candidates
    stale_past_due_candidates: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for item in all_candidates:
        is_stale_past_due = item.get("status") == "past_due" and int(item.get("days_until", 0) or 0) < -abs(stale_past_due_days)
        if is_stale_past_due:
            stale_past_due_candidates.append(item)
        else:
            candidates.append(item)
    candidate_groups = annotate_due_candidate_groups(candidates)
    duplicate_groups = candidate_groups["duplicates"]
    related_source_groups = candidate_groups["related_sources"]
    candidates.sort(
        key=lambda item: (
            0 if item["status"] == "ready" else 1 if item["status"] == "already_reminded" else 2,
            item["date"],
            str(item["title"]).casefold(),
        )
    )
    actionable = [item for item in candidates if item["status"] == "ready"]
    already = [item for item in candidates if item["status"] == "already_reminded"]
    past = [item for item in candidates if item["status"] == "past_due"]
    shown = candidates[: max(1, limit)]
    return {
        "ok": True,
        "today": today_date.isoformat(),
        "candidate_count": len(candidates),
        "document_candidate_count": sum(1 for item in candidates if item.get("source_kind") != "email_archive"),
        "email_candidate_count": sum(1 for item in candidates if item.get("source_kind") == "email_archive"),
        "stale_past_due_count": len(stale_past_due_candidates),
        "stale_past_due_days": abs(stale_past_due_days),
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_candidate_count": sum(1 for item in candidates if item.get("duplicate_group_id")),
        "related_source_group_count": len(related_source_groups),
        "related_source_candidate_count": sum(1 for item in candidates if item.get("related_source_group_id")),
        "actionable_count": len(actionable),
        "already_reminded_count": len(already),
        "past_count": len(past),
        "items": [public_document_due_candidate(item) for item in shown],
        "truncated": len(candidates) > len(shown),
        "message": (
            f"Termíny: {len(actionable)} ke schválení, {len(already)} už hlídáno, "
            f"{len(past)} prošlé bez nové připomínky."
            f"{' Archivní prošlé skryté: ' + str(len(stale_past_due_candidates)) + '.' if stale_past_due_candidates else ''}"
            f"{' Související zdroje: ' + str(len(related_source_groups)) + '.' if related_source_groups else ''}"
            f"{' Pravděpodobné duplicity: ' + str(len(duplicate_groups)) + '.' if duplicate_groups else ''}"
        ),
    }


def annotate_due_candidate_groups(candidates: list[dict[str, Any]]) -> dict[str, list[list[dict[str, Any]]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for item in candidates:
        key = due_candidate_duplicate_key(item)
        if key is None:
            continue
        grouped.setdefault(key, []).append(item)

    duplicate_groups: list[list[dict[str, Any]]] = []
    related_source_groups: list[list[dict[str, Any]]] = []
    for items in grouped.values():
        if len(items) <= 1:
            continue
        if due_candidate_items_are_same_email_with_attachment(items):
            related_source_groups.append(items)
        else:
            duplicate_groups.append(items)

    for items in related_source_groups:
        source_labels = sorted({due_candidate_source_label(item) for item in items})
        group_id = "due-src-" + hashlib.sha256(
            "|".join(str(item.get("candidate_ref", "")) for item in items).encode("utf-8")
        ).hexdigest()[:12]
        note = (
            "Související zdroje: stejný e-mail a jeho PDF příloha "
            f"({', '.join(source_labels)}). Nejde o dvojí závazek."
        )
        for item in items:
            item["related_source_group_id"] = group_id
            item["related_source_group_size"] = len(items)
            item["related_source_note"] = note

    for items in duplicate_groups:
        source_labels = sorted({due_candidate_source_label(item) for item in items})
        group_id = "due-dup-" + hashlib.sha256(
            "|".join(str(item.get("candidate_ref", "")) for item in items).encode("utf-8")
        ).hexdigest()[:12]
        note = (
            "Pravděpodobná duplicita: stejná protistrana, typ a datum "
            f"v {len(items)} kandidátech ({', '.join(source_labels)})."
        )
        for item in items:
            item["duplicate_group_id"] = group_id
            item["duplicate_group_size"] = len(items)
            item["duplicate_note"] = note
    return {"duplicates": duplicate_groups, "related_sources": related_source_groups}


def due_candidate_items_are_same_email_with_attachment(items: list[dict[str, Any]]) -> bool:
    labels = {due_candidate_source_label(item) for item in items}
    if not {"dokument", "e-mail"}.issubset(labels):
        return False
    email_uids = {uid for item in items for uid in due_candidate_email_uids(item)}
    return bool(email_uids)


def due_candidate_email_uids(item: dict[str, Any]) -> set[str]:
    values = [
        str(item.get("case_id", "")),
        str(item.get("title", "")),
        str(item.get("source_summary", "")),
        str(item.get("archive_id", "")),
    ]
    joined = " ".join(values)
    matches = set(re.findall(r"(?:uid|email-seznam-|email-icloud-|email-)[^\d]{0,8}(\d{3,})", joined, flags=re.IGNORECASE))
    return matches


def due_candidate_duplicate_key(item: dict[str, Any]) -> tuple[str, str, str] | None:
    due_type = safe_text(str(item.get("type", ""))).casefold()
    due_date = safe_text(str(item.get("date", ""))).strip()
    if not due_type or not due_date:
        return None
    counterparty = normalize_due_candidate_party(str(item.get("counterparty", "")))
    if len(counterparty) < 4:
        return None
    return due_type, due_date, counterparty


def normalize_due_candidate_party(value: str) -> str:
    text = redact_email_addresses(safe_text(value)).casefold()
    text = text.replace("[e-mail redigovan]", " ")
    text = re.sub(r"[^0-9a-zá-ž]+", " ", text, flags=re.IGNORECASE)
    return " ".join(text.split())[:120]


def due_candidate_source_label(item: dict[str, Any]) -> str:
    return "e-mail" if item.get("source_kind") == "email_archive" else "dokument"


def build_document_due_candidates(
    *,
    vault_dir: Path,
    reminders_path: Path,
    today: date,
) -> list[dict[str, Any]]:
    documents = {
        str(row.get("document_id", "")): row
        for row in read_jsonl(vault_dir / "index" / "documents_index.jsonl")
        if str(row.get("document_id", "")).strip()
        and safe_text(str(row.get("lifecycle_status", "active") or "active")).casefold() not in {"archived", "trashed"}
    }
    text_by_document_id = {
        str(row.get("document_id", "")): str(row.get("text", ""))
        for row in read_jsonl(vault_dir / "index" / "text_index.jsonl")
        if str(row.get("document_id", "")).strip()
    }
    try:
        reminders = load_reminders_store(reminders_path).get("reminders", [])
    except (OSError, ValueError):
        reminders = []
    reminders_by_id = {
        str(item.get("id", "")): item
        for item in reminders
        if isinstance(item, dict) and str(item.get("id", "")).strip()
    }

    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in read_jsonl(vault_dir / "index" / "due_dates.jsonl"):
        if not bool(row.get("create_reminder_candidate")):
            continue
        document_id = str(row.get("document_id", "")).strip()
        document = documents.get(document_id)
        if document is None:
            continue
        due_date = parse_document_due_date(str(row.get("date", "")))
        if due_date is None:
            continue
        due_type = safe_slug(str(row.get("type", "")), default="deadline", limit=50)
        key = (document_id, due_type, due_date.isoformat())
        current = grouped.get(key)
        context = sanitize_output(str(row.get("context", "")))[:700]
        if current is None:
            title = safe_text(str(document.get("title") or document.get("original_filename") or document_id))[:180]
            reminder_id = document_due_candidate_reminder_id(
                document_id=document_id,
                due_type=due_type,
                due_date=due_date.isoformat(),
            )
            reminder = reminders_by_id.get(reminder_id)
            days_until = (due_date - today).days
            if reminder is not None:
                status = "already_reminded"
            elif days_until < 0:
                status = "past_due"
            else:
                status = "ready"
            document_text = text_by_document_id.get(document_id, "")
            amount_due, amount_note = document_due_candidate_amount(
                context=context,
                document_text=document_text,
                reminder=reminder,
                due_type=due_type,
            )
            current = {
                "candidate_ref": document_due_candidate_reference(document_id, due_type, due_date.isoformat()),
                "document_id": document_id,
                "document_ref": document_reference(document_id),
                "case_id": safe_text(str(document.get("case_id", "")))[:120],
                "title": title,
                "domain": safe_text(str(document.get("domain", "")))[:80],
                "domain_label": document_domain_label(str(document.get("domain", ""))),
                "document_type": safe_text(str(document.get("document_type", "")))[:80],
                "document_type_label": document_type_label(str(document.get("document_type", ""))),
                "counterparty": safe_text(str(document.get("counterparty", "")))[:180],
                "related_asset": safe_text(str(document.get("related_asset", "")))[:180],
                "date": due_date.isoformat(),
                "days_until": days_until,
                "type": due_type,
                "type_label": DOCUMENT_DUE_TYPE_LABELS.get(due_type, due_type),
                "confidence": safe_text(str(row.get("confidence", "")))[:40],
                "context": context,
                "context_count": 1,
                "amount_due": amount_due,
                "amount_note": amount_note,
                "status": status,
                "status_label": document_due_candidate_status_label(status),
                "reminder_id": reminder_id,
                "reminder_ref": reminder_reference(reminder_id),
                "reminder_status": safe_text(str(reminder.get("status", "")))[:40] if reminder is not None else "",
                "suggested_title": document_due_candidate_title(title=title, due_type=due_type),
                "suggested_notes": document_due_candidate_notes(title=title, due_type=due_type, context=context),
                "priority": "high" if due_type in {"payment_due", "valid_until"} else "medium",
            }
            grouped[key] = current
        else:
            current["context_count"] = int(current.get("context_count", 1)) + 1
            if not current.get("amount_due"):
                document_text = text_by_document_id.get(document_id, "")
                amount_due, amount_note = document_due_candidate_amount(
                    context=context,
                    document_text=document_text,
                    reminder=reminders_by_id.get(str(current.get("reminder_id", ""))),
                    due_type=due_type,
                )
                current["amount_due"] = amount_due
                current["amount_note"] = amount_note

    candidates = list(grouped.values())
    candidates.sort(
        key=lambda item: (
            0 if item["status"] == "ready" else 1 if item["status"] == "already_reminded" else 2,
            item["date"],
            str(item["title"]).casefold(),
        )
    )
    return candidates


def public_document_due_candidate(item: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in item.items()
        if key not in {"document_id", "archive_id", "reminder_id", "case_id"}
    }


EMAIL_ARCHIVE_PAYMENT_TERMS = (
    "splatnost",
    "dluž",
    "dluz",
    "upom",
    "k zaplacení",
    "k zaplaceni",
    "k úhradě",
    "k uhrade",
    "zaplať",
    "zaplat",
)
EMAIL_ARCHIVE_DATE_PATTERN = re.compile(r"\b(\d{1,2})[.]\s*(\d{1,2})[.]\s*(20\d{2})\b")
EMAIL_ARCHIVE_AMOUNT_PATTERN = re.compile(r"\b([0-9]{1,3}(?:[ .\u00a0]\d{3})*(?:,\d{1,2})?\s*K[čc])\b")


def build_email_archive_due_candidates(
    *,
    archive_directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
    reminders_path: Path = DEFAULT_REMINDERS_PATH,
    today: date,
    max_age_days: int = 45,
) -> list[dict[str, Any]]:
    try:
        reminders = load_reminders_store(reminders_path).get("reminders", [])
    except (OSError, ValueError):
        reminders = []
    reminders_by_id = {
        str(item.get("id", "")): item
        for item in reminders
        if isinstance(item, dict) and str(item.get("id", "")).strip()
    }

    candidates: list[dict[str, Any]] = []
    if not archive_directory.exists():
        return candidates

    for metadata_path in sorted(archive_directory.glob("*/metadata.json"), key=lambda path: path.stat().st_mtime, reverse=True):
        try:
            metadata = read_json_file(metadata_path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        message_date = parse_email_archive_date(str(metadata.get("date", "")))
        archived_at = parse_email_archive_date(str(metadata.get("archived_at", "")))
        freshness_date = message_date or archived_at
        if freshness_date is not None and (today - freshness_date).days > max_age_days:
            continue
        archive_dir = metadata_path.parent
        body_path = archive_dir / "body.txt"
        try:
            body_text = body_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        subject = safe_text(str(metadata.get("subject", "")))[:180]
        sender = redact_email_addresses(safe_text(str(metadata.get("from", ""))))[:180]
        sender_name = email_sender_display_name(sender)
        title_source = f"{sender} | {subject}".strip(" |") or str(metadata.get("archive_id") or archive_dir.name)
        email_text = f"{subject}\n{sender}\n{body_text}"
        if not email_archive_text_looks_payment_related(email_text):
            continue
        due = best_email_archive_due_match(email_text)
        if due is None:
            continue
        due_date, context = due
        archive_id = safe_text(str(metadata.get("archive_id") or archive_dir.name))[:180]
        reminder_id = email_archive_due_candidate_reminder_id(
            archive_id=archive_id,
            due_type="payment_due",
            due_date=due_date.isoformat(),
        )
        reminder = reminders_by_id.get(reminder_id)
        if reminder is not None:
            status = "already_reminded"
        elif due_date < today:
            status = "past_due"
        else:
            status = "ready"
        amount_due = safe_text(str(reminder.get("amount_due", "")))[:80] if reminder is not None else extract_payment_amount_from_text(context)
        amount_note = safe_text(str(reminder.get("amount_note", "")))[:240] if reminder is not None else ""
        candidates.append(
            {
                "candidate_ref": email_archive_due_candidate_reference(archive_id, "payment_due", due_date.isoformat()),
                "source_kind": "email_archive",
                "archive_id": archive_id,
                "title": safe_text(title_source)[:180],
                "domain": "email",
                "domain_label": "e-mail",
                "document_type": "email_payment_notice",
                "document_type_label": "platební e-mail",
                "counterparty": sender,
                "related_asset": "",
                "date": due_date.isoformat(),
                "days_until": (due_date - today).days,
                "type": "payment_due",
                "type_label": DOCUMENT_DUE_TYPE_LABELS.get("payment_due", "platba"),
                "confidence": "medium",
                "context": context,
                "context_count": 1,
                "amount_due": amount_due,
                "amount_note": amount_note,
                "status": status,
                "status_label": document_due_candidate_status_label(status),
                "reminder_id": reminder_id,
                "reminder_ref": reminder_reference(reminder_id),
                "reminder_status": safe_text(str(reminder.get("status", "")))[:40] if reminder is not None else "",
                "suggested_title": email_archive_due_candidate_title(
                    subject=subject,
                    sender_name=sender_name,
                    archive_id=archive_id,
                ),
                "suggested_notes": safe_text(f"Platební kandidát z uloženého e-mailu. Kontext: {context}")[:700],
                "priority": "high",
                "source_summary": safe_text(
                    f"{metadata.get('provider') or 'email'} / {metadata.get('mailbox') or 'INBOX'} / UID {metadata.get('uid') or ''}"
                )[:160],
            }
        )

    return candidates


def email_archive_text_looks_payment_related(text: str) -> bool:
    folded = text.casefold()
    return any(term in folded for term in EMAIL_ARCHIVE_PAYMENT_TERMS) and bool(EMAIL_ARCHIVE_AMOUNT_PATTERN.search(text))


def email_sender_display_name(sender: str) -> str:
    cleaned = redact_email_addresses(safe_text(sender)).strip()
    if "<" in cleaned:
        cleaned = cleaned.split("<", 1)[0].strip().strip('"')
    return cleaned[:80]


def email_archive_due_candidate_title(*, subject: str, sender_name: str, archive_id: str) -> str:
    subject_text = safe_text(subject).strip()
    sender_text = safe_text(sender_name).strip()
    if sender_text and subject_text:
        return safe_text(f"Zaplatit podle e-mailu: {sender_text} - {subject_text}")[:160]
    if subject_text:
        return safe_text(f"Zaplatit podle e-mailu: {subject_text}")[:160]
    if sender_text:
        return safe_text(f"Zaplatit podle e-mailu: {sender_text}")[:160]
    return safe_text(f"Zaplatit podle e-mailu: {archive_id}")[:160]


def best_email_archive_due_match(text: str) -> tuple[date, str] | None:
    matches: list[tuple[int, date, str]] = []
    for match in EMAIL_ARCHIVE_DATE_PATTERN.finditer(text):
        try:
            due_date = date(int(match.group(3)), int(match.group(2)), int(match.group(1)))
        except ValueError:
            continue
        start = max(0, match.start() - 180)
        end = min(len(text), match.end() + 180)
        context = sanitize_output(" ".join(text[start:end].split()))[:700]
        folded = context.casefold()
        score = 0
        if "dluž" in folded or "dluz" in folded:
            score += 8
        if "upom" in folded:
            score += 6
        if "splatnost" in folded:
            score += 4
        if EMAIL_ARCHIVE_AMOUNT_PATTERN.search(context):
            score += 3
        if "celkem" in folded or "k zaplac" in folded or "k úhrad" in folded or "k uhrad" in folded:
            score += 2
        matches.append((-score, due_date, context))
    if not matches:
        return None
    matches.sort(key=lambda item: (item[0], item[1]))
    return matches[0][1], matches[0][2]


def extract_payment_amount_from_text(text: str) -> str:
    amounts = [
        " ".join(safe_text(match.group(1)).replace(".", " ").replace("\u00a0", " ").split())
        for match in EMAIL_ARCHIVE_AMOUNT_PATTERN.finditer(text)
    ]
    if not amounts:
        return ""
    return amounts[-1][:80]


def parse_email_archive_date(value: str) -> date | None:
    if not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError, IndexError):
            return None
    return parsed.date()


def email_archive_due_candidate_reference(archive_id: str, due_type: str, due_date: str) -> str:
    digest = hashlib.sha256(f"{archive_id}|{due_type}|{due_date}".encode("utf-8")).hexdigest()[:16]
    return f"emaildueref-{digest}"


def email_archive_due_candidate_reminder_id(*, archive_id: str, due_type: str, due_date: str) -> str:
    safe_archive_id = safe_slug(archive_id, default="email-archive", limit=140)
    safe_due_type = safe_slug(due_type, default="deadline", limit=50)
    return f"email-archive-{safe_archive_id}-{safe_due_type}-{due_date}"


def document_due_candidate_reference(document_id: str, due_type: str, due_date: str) -> str:
    digest = hashlib.sha256(f"{document_id}|{due_type}|{due_date}".encode("utf-8")).hexdigest()[:16]
    return f"dueref-{digest}"


def document_due_candidate_reminder_id(*, document_id: str, due_type: str, due_date: str) -> str:
    safe_document_id = safe_slug(document_id, default="document", limit=140)
    safe_due_type = safe_slug(due_type, default="deadline", limit=50)
    return f"document-{safe_document_id}-{safe_due_type}-{due_date}"


def parse_document_due_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def document_due_candidate_status_label(status: str) -> str:
    if status == "ready":
        return "ke schválení"
    if status == "already_reminded":
        return "už hlídáno"
    if status == "past_due":
        return "prošlé"
    return "nejasné"


def document_due_candidate_title(*, title: str, due_type: str) -> str:
    if due_type == "payment_due":
        return safe_text(f"Zaplatit podle dokumentu: {title}")[:160]
    if due_type == "valid_until":
        return safe_text(f"Zkontrolovat konec platnosti: {title}")[:160]
    if due_type == "service_due":
        return safe_text(f"Zajistit servis/revizi: {title}")[:160]
    return safe_text(f"Zkontrolovat termín v dokumentu: {title}")[:160]


def document_due_candidate_notes(*, title: str, due_type: str, context: str) -> str:
    type_label = DOCUMENT_DUE_TYPE_LABELS.get(due_type, due_type)
    return safe_text(f"Potvrzený kandidát z dokumentu ({type_label}). Kontext: {context or title}")[:700]


def extract_amount_from_due_context(context: str) -> str:
    match = re.search(r"\b([0-9][0-9 ]{0,12}\s*K[čc])\b", context)
    return safe_text(match.group(1))[:80] if match else ""


def document_due_candidate_amount(
    *,
    context: str,
    document_text: str,
    reminder: dict[str, Any] | None,
    due_type: str,
) -> tuple[str, str]:
    if reminder is not None:
        reminder_amount = safe_text(str(reminder.get("amount_due", "")))[:80]
        if reminder_amount:
            reminder_note = safe_text(str(reminder.get("amount_note", "")))[:240]
            return reminder_amount, reminder_note or "Částka převzata z existující otevřené připomínky."
    if due_type == "payment_due":
        options = document_payment_options(document_text)
        base_options = [item for item in options if "bez doplňkového MAXI" in item.get("label", "")]
        optional_options = [item for item in options if "MAXI" in item.get("label", "") and item not in base_options]
        if base_options and optional_options:
            amount = safe_text(str(base_options[0].get("amount", "")))[:80]
            if amount:
                return amount, "Částka vybrána ze základní varianty; navýšená MAXI varianta je volitelný dodatek."
    return extract_amount_from_due_context(context), ""


def document_payment_options(text: str) -> list[dict[str, str]]:
    options: list[dict[str, str]] = []
    if not text.strip():
        return options

    base_match = re.search(
        r"nov[ěe]\s+p[řr]edepsan[ée]\s+pojistn[ée]\s+[čc]in[íi]\s+([0-9 ]+\s*K[čc])",
        text,
        flags=re.IGNORECASE,
    )
    if base_match:
        options.append(
            {
                "label": "Stávající pojištění bez doplňkového MAXI",
                "amount": safe_text(base_match.group(1)),
                "note": "Částka z věty o nově předepsaném ročním pojistném.",
            }
        )

    extra_match = re.search(
        r"Ro[čc]n[íi]\s+pojistn[ée]\s+za\s+dopl[ňn]kov[ée]\s+poji[šs]t[ěe]n[íi].{0,120}?MAXI:\s*([0-9 ]+\s*K[čc])",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    total_match = re.search(
        r"Pojistn[ée]\s+za\s+pojistn[ée]\s+obdob[íi]\s*\(nav[ýy][šs]en[ée].{0,180}?MAXI\):\s*([0-9 ]+\s*K[čc])",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if total_match:
        note = "Varianta vznikne jen zaplacením dodatku s doplňkovým pojištěním MAXI."
        if extra_match:
            note = f"{note} Samotné doplňkové MAXI: {safe_text(extra_match.group(1))}."
        options.append(
            {
                "label": "Varianta s doplňkovým pojištěním MAXI",
                "amount": safe_text(total_match.group(1)),
                "note": note,
            }
        )

    return options



