from __future__ import annotations

import json
import hashlib
import re
import shutil
import subprocess
import time
from collections.abc import Callable
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from app.backup.activity_state import format_backup_activity_reminder
from app.documents.scandocu import DEFAULT_DOWNLOADS_DIR, scan_downloads_for_pdfs
from app.documents.vault import (
    DEFAULT_DOCUMENTS_DIR,
    build_snippet,
    document_vault_status_summary,
    append_jsonl,
    is_pdf_encrypted,
    next_available_path,
    prepare_document_print_job,
    read_jsonl,
    read_json_file,
    relative_to_project,
    run_document_print_job,
    safe_text,
    safe_slug,
    sanitize_output,
    tokenize,
    write_json,
    write_jsonl,
)
from app.email.config import EmailConfigError
from app.email.icloud_provider import EmailProviderError, ICloudReadOnlyEmailProvider
from app.email.models import EmailHeader
from app.email.seznam_provider import SeznamEmailProviderError, SeznamReadOnlyEmailProvider


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COCKPIT_PORT = 8770
COCKPIT_URL = f"http://127.0.0.1:{COCKPIT_PORT}"
SCANDOCU_URL = "http://127.0.0.1:8766"
SCANDOCU_PORT = 8766
SCANDOCU_LOG_DIR = PROJECT_ROOT / "data" / "private" / "documents" / "scandocu"
SCANDOCU_LOG_FILE = SCANDOCU_LOG_DIR / "server.log"
SCANDOCU_SERVER_SCRIPT = PROJECT_ROOT / "scripts" / "scandocu_server.py"
EMAIL_SESSION_HANDOFF_DIR = PROJECT_ROOT / "data" / "private" / "email_session_handoffs"
EMAIL_PROCESSING_DECISIONS_FILE = EMAIL_SESSION_HANDOFF_DIR / "email_processing_decisions.json"
GIT_ROOT = PROJECT_ROOT.parent
LOCAL_WEB_APPS = {
    "family-video-organizer": PROJECT_ROOT / "docs" / "family-video-organizer",
}
WEB_APP_CATALOG: tuple[dict[str, str], ...] = (
    {
        "id": "scandocu",
        "title": "ScanDocu",
        "description": "Kontrola, klasifikace a uložení PDF dokumentů z Downloads do soukromého document vaultu.",
        "url": SCANDOCU_URL,
        "kind": "lokální",
    },
    {
        "id": "cockpit",
        "title": "Samantha Cockpit",
        "description": "Řídicí panel pro dokumenty, ScanDocu, zálohy a praktické rutiny Samanthy.",
        "url": COCKPIT_URL,
        "kind": "lokální",
    },
    {
        "id": "email-processing",
        "title": "Email Processing",
        "description": "Read-only pracovní přehled e-mailových kandidátů a navazující zpracování PDF.",
        "url": "/email-processing/",
        "kind": "lokální",
    },
    {
        "id": "lekarna",
        "title": "Lékárna",
        "description": "Šifrovaná webová evidence domácí lékárny s vyhledáním léků a stručnými pokyny.",
        "url": "https://belisarius-mila.github.io/PythonMF/lekarna/",
        "kind": "GitHub Pages",
    },
    {
        "id": "matysek-mmtx",
        "title": "Matýsek MMTX",
        "description": "Příběhová dětská výuková aplikace se scénami, obrázky, hlasem a lekcemi Forest School.",
        "url": "https://belisarius-mila.github.io/PythonMF/",
        "kind": "GitHub Pages",
    },
    {
        "id": "colors-numbers",
        "title": "Colors and Numbers",
        "description": "Jednoduchá výuková webová aplikace s barvami, čísly a sovími hlasovými nahrávkami.",
        "url": "https://belisarius-mila.github.io/PythonMF/colors-numbers/",
        "kind": "GitHub Pages",
    },
    {
        "id": "vocabulary-en",
        "title": "Vocabulary EN",
        "description": "Obrazové kartičky pro anglická slovíčka, připravené z lokální slovníkové evidence.",
        "url": "https://belisarius-mila.github.io/PythonMF/vocabulary-en/",
        "kind": "GitHub Pages",
    },
    {
        "id": "family-video-organizer",
        "title": "Family Video Organizer",
        "description": "Lokální prototyp pro třídění rodinných videí, výběr záběrů a přípravu podkladů pro sestřih.",
        "url": "/local-apps/family-video-organizer/",
        "kind": "lokální prototyp",
    },
)

READING_STATUS_LABELS: dict[str, str] = {
    "ok": "OK",
    "needs_review": "k revizi",
    "unreadable": "nečitelné",
    "superseded": "nahrazeno lepší kopií",
}
READING_STATUS_ALIASES: dict[str, str] = {
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


def web_apps_catalog() -> dict[str, Any]:
    return {"ok": True, "apps": [dict(item) for item in WEB_APP_CATALOG]}


EMAIL_PROCESSING_CATEGORY_TITLES = {
    "Faktury / e-shopy": "faktury/e-shopy",
    "Pojisteni / smlouvy": "pojištění/smlouvy",
    "Pojištění / smlouvy": "pojištění/smlouvy",
    "Urady / dane": "úřady/daně",
    "Úřady / daně": "úřady/daně",
    "Ostatni kandidati": "ostatní",
    "Ostatní kandidáti": "ostatní",
}
EMAIL_PROCESSING_ACTIONS = {"process", "ignore", "trash_requested", ""}
EMAIL_PROCESSING_CATEGORY_ORDER = ("faktury/e-shopy", "pojištění/smlouvy", "úřady/daně", "ostatní")


def email_processing_stable_key(provider: str, folder: str, uid: str) -> str:
    provider_key = " ".join(provider.casefold().split())
    folder_key = " ".join((folder or "INBOX").casefold().split())
    uid_key = str(uid).strip()
    if not provider_key or not uid_key:
        return ""
    return "|".join([provider_key, folder_key, uid_key])


def email_processing_legacy_item_id(category: str, provider: str, folder: str, uid: str, date: str, subject: str) -> str:
    raw = "|".join([category, provider, folder, uid, date, subject])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def email_processing_item_id(category: str, provider: str, folder: str, uid: str, date: str, subject: str) -> str:
    stable_key = email_processing_stable_key(provider, folder, uid)
    if stable_key:
        return hashlib.sha256(stable_key.encode("utf-8")).hexdigest()[:16]
    return email_processing_legacy_item_id(category, provider, folder, uid, date, subject)


def email_processing_decision_lookup_keys(decisions: dict[str, dict[str, Any]]) -> set[str]:
    keys = set(decisions)
    for decision in decisions.values():
        item = decision.get("item", {})
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("id", "")).strip()
        legacy_id = str(item.get("legacy_id", "")).strip()
        if item_id:
            keys.add(item_id)
        if legacy_id:
            keys.add(legacy_id)
        computed_id = email_processing_item_id(
            str(item.get("category", "")),
            str(item.get("provider", "")),
            str(item.get("folder", "")),
            str(item.get("uid", "")),
            str(item.get("date", "")),
            str(item.get("subject", "")),
        )
        if computed_id:
            keys.add(computed_id)
    return keys


def classify_email_processing_category(subject: str, sender: str = "") -> str:
    value = f"{subject} {sender}".casefold()
    if any(
        token in value
        for token in (
            "pojišt",
            "pojist",
            "smlouv",
            "zelen",
            "karta",
            "generali",
            "kooperativa",
            "čpp",
            "cpp",
        )
    ):
        return "pojištění/smlouvy"
    if any(token in value for token in ("úřad", "urad", "daň", "dan", "finanční", "financni", "datov", "správa")):
        return "úřady/daně"
    if any(
        token in value
        for token in (
            "faktura",
            "objedn",
            "platba",
            "zaplac",
            "booking",
            "temu",
            "apple",
            "doruč",
            "doruc",
            "balík",
            "balicek",
            "zásilk",
            "zasilk",
            "eshop",
            "e-shop",
        )
    ):
        return "faktury/e-shopy"
    return "ostatní"


def email_header_timestamp(value: str) -> float:
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return 0.0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def parse_iso_timestamp(value: str) -> float:
    if not value:
        return 0.0
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return 0.0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def email_header_to_processing_item(header: EmailHeader, source: str) -> dict[str, Any]:
    category = classify_email_processing_category(header.subject, header.sender)
    folder = header.folder or "INBOX"
    item = {
        "category": category,
        "provider": source,
        "folder": folder,
        "uid": str(header.internal_id),
        "date": header.date,
        "subject": header.subject or "(bez předmětu)",
        "reason": "nová hlavička z read-only kontroly",
        "action": "",
        "is_new_header": True,
    }
    item["id"] = email_processing_item_id(
        category,
        source,
        folder,
        str(header.internal_id),
        header.date,
        header.subject or "",
    )
    item["legacy_id"] = email_processing_legacy_item_id(
        category,
        source,
        folder,
        str(header.internal_id),
        header.date,
        header.subject or "",
    )
    return item


def parse_email_processing_items(text: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    category = ""
    current: dict[str, Any] | None = None

    def finish_current() -> None:
        nonlocal current
        if not current:
            return
        current["id"] = email_processing_item_id(
            str(current.get("category", "")),
            str(current.get("provider", "")),
            str(current.get("folder", "")),
            str(current.get("uid", "")),
            str(current.get("date", "")),
            str(current.get("subject", "")),
        )
        current["legacy_id"] = email_processing_legacy_item_id(
            str(current.get("category", "")),
            str(current.get("provider", "")),
            str(current.get("folder", "")),
            str(current.get("uid", "")),
            str(current.get("date", "")),
            str(current.get("subject", "")),
        )
        items.append(current)
        current = None

    for line in text.splitlines():
        section = re.match(r"^##\s+(.+?)\s*$", line)
        if section:
            finish_current()
            category = EMAIL_PROCESSING_CATEGORY_TITLES.get(section.group(1).strip(), "")
            continue
        if not category:
            continue

        numbered = re.match(r"^\d+\.\s+(.+?)\s+/\s+(.+?)\s+/\s+UID\s+([^/]+?)\s+/\s+([0-9]{4}-[0-9]{2}-[0-9]{2})\s*$", line)
        if numbered:
            finish_current()
            current = {
                "category": category,
                "provider": numbered.group(1).strip(),
                "folder": numbered.group(2).strip(),
                "uid": numbered.group(3).strip(),
                "date": numbered.group(4).strip(),
                "subject": "",
                "reason": "",
            }
            continue

        bullet = re.match(r"^-\s+(.+?)\s+UID\s+([^:]+):\s*(.+?)\s*$", line)
        if bullet:
            finish_current()
            subject = bullet.group(3).strip()
            current = {
                "category": category,
                "provider": bullet.group(1).strip(),
                "folder": "",
                "uid": bullet.group(2).strip(),
                "date": "",
                "subject": subject,
                "reason": subject,
            }
            finish_current()
            continue

        if not current:
            continue
        subject = re.match(r"^\s*-\s+Predmet:\s*(.+?)\s*$", line)
        if subject:
            current["subject"] = subject.group(1).strip()
            continue
        reason = re.match(r"^\s*-\s+Duvod:\s*(.+?)\s*$", line)
        if reason:
            current["reason"] = reason.group(1).strip()
            continue

    finish_current()
    return items


def read_email_processing_decisions(path: Path = EMAIL_PROCESSING_DECISIONS_FILE) -> dict[str, dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    decisions = data.get("decisions", {})
    if not isinstance(decisions, dict):
        return {}
    return {str(key): value for key, value in decisions.items() if isinstance(value, dict)}


def save_email_processing_decision(
    *,
    item_id: str,
    action: str,
    item: dict[str, Any] | None = None,
    path: Path = EMAIL_PROCESSING_DECISIONS_FILE,
) -> dict[str, Any]:
    item_id = item_id.strip()
    action = action.strip()
    if not item_id:
        return {"ok": False, "message": "Chybí ID e-mailu."}
    if action not in EMAIL_PROCESSING_ACTIONS:
        return {"ok": False, "message": "Neznámá akce."}

    decisions = read_email_processing_decisions(path)
    if action:
        decisions[item_id] = {
            "action": action,
            "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "item": item if isinstance(item, dict) else {},
        }
    else:
        decisions.pop(item_id, None)
    write_json(path, {"decisions": decisions})
    label = {
        "process": "označeno ke zpracování",
        "ignore": "označeno k ignorování",
        "trash_requested": "označeno ke smazání po potvrzení",
        "": "rozhodnutí zrušeno",
    }[action]
    return {"ok": True, "message": label, "item_id": item_id, "action": action}


def new_email_headers_overview(
    limit_per_source: int = 50,
    since: str = "",
    days: int = 0,
    known_ids: set[str] | None = None,
    decisions_path: Path = EMAIL_PROCESSING_DECISIONS_FILE,
    icloud_provider_factory: Callable[[], object] | None = None,
    seznam_provider_factory: Callable[[], object] | None = None,
) -> dict[str, Any]:
    safe_limit = min(max(1, limit_per_source), 75)
    since_ts = parse_iso_timestamp(since)
    safe_days = min(max(0, days), 14)
    since_days_ts = 0.0
    if not since_ts and safe_days:
        since_days_ts = datetime.now(timezone.utc).timestamp() - (safe_days * 24 * 60 * 60)
    cutoff_ts = since_ts or since_days_ts
    known = {str(item_id).strip() for item_id in (known_ids or set()) if str(item_id).strip()}
    decided = read_email_processing_decisions(decisions_path)
    decided_keys = email_processing_decision_lookup_keys(decided)
    entries: list[dict[str, Any]] = []
    unavailable: list[str] = []
    providers: list[tuple[str, Callable[[], object], type[Exception], str]] = [
        (
            "iCloud",
            icloud_provider_factory or ICloudReadOnlyEmailProvider,
            EmailProviderError,
            "iCloud: read-only přístup selhal",
        ),
        (
            "Seznam",
            seznam_provider_factory or SeznamReadOnlyEmailProvider,
            SeznamEmailProviderError,
            "Seznam: read-only přístup selhal",
        ),
    ]
    for source, provider_factory, provider_error, error_message in providers:
        try:
            provider = provider_factory()
            headers = provider.list_recent_headers(limit=safe_limit)  # type: ignore[attr-defined]
        except EmailConfigError:
            unavailable.append(f"{source}: chybí lokální konfigurace")
            continue
        except provider_error:
            unavailable.append(error_message)
            continue
        for header in headers:
            header_ts = email_header_timestamp(header.date)
            if cutoff_ts and (not header_ts or header_ts <= cutoff_ts):
                continue
            item = email_header_to_processing_item(header, source)
            item_id = str(item.get("id", ""))
            legacy_id = str(item.get("legacy_id", ""))
            if item_id in known or legacy_id in known or item_id in decided_keys or legacy_id in decided_keys:
                continue
            entries.append(item)

    entries.sort(key=lambda item: email_header_timestamp(str(item.get("date", ""))), reverse=True)
    if entries:
        if safe_days and not since_ts:
            message = f"Načteno {len(entries)} e-mailových hlaviček za posledních {safe_days} dní read-only."
        else:
            message = f"Načteno {len(entries)} nových e-mailových hlaviček read-only."
    elif since_ts:
        message = "Od otevření přehledu nepřišly žádné novější e-mailové hlavičky."
    elif safe_days:
        message = f"Za posledních {safe_days} dní nebyly nalezeny žádné e-mailové hlavičky."
    else:
        message = "Nebyly nalezeny žádné e-mailové hlavičky."
    return {
        "ok": True,
        "message": message,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "limit_per_source": safe_limit,
        "since": since,
        "days": safe_days,
        "known_count": len(known),
        "skipped_decided_count": len(decided_keys),
        "items": entries,
        "unavailable": unavailable,
    }


def latest_email_processing_overview(root: Path = EMAIL_SESSION_HANDOFF_DIR) -> dict[str, Any]:
    files = sorted(
        root.glob("weekly_email_overview_*_private.md") if root.exists() else [],
        key=lambda path: (path.stat().st_mtime, path.name),
        reverse=True,
    )
    if not files:
        return {
            "ok": False,
            "message": "Žádný uložený e-mailový přehled zatím není k dispozici.",
            "path": "",
            "title": "Email Processing",
            "text": "",
            "updated_at": "",
        }

    path = files[0]
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {
            "ok": False,
            "message": f"Přehled se nepodařilo načíst: {exc}",
            "path": str(relative_to_project(path)),
            "title": path.name,
            "text": "",
            "updated_at": "",
        }

    title = path.stem
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip() or title
            break
    updated_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat()
    decisions = read_email_processing_decisions(root / EMAIL_PROCESSING_DECISIONS_FILE.name)
    items = parse_email_processing_items(text)
    for item in items:
        decision = (
            decisions.get(str(item.get("id", "")), {})
            or decisions.get(str(item.get("legacy_id", "")), {})
        )
        action = str(decision.get("action", ""))
        item["action"] = "process" if action == "save" else action
    return {
        "ok": True,
        "message": "Načten poslední uložený read-only přehled e-mailů.",
        "path": str(relative_to_project(path)),
        "title": title,
        "text": text,
        "items": items,
        "updated_at": updated_at,
    }


def empty_email_processing_overview() -> dict[str, Any]:
    return {
        "ok": True,
        "message": "Pracovní seznam je prázdný. Zvol rozsah a načti e-maily.",
        "path": "",
        "title": "Email Processing",
        "text": "",
        "items": [],
        "updated_at": "",
    }


def cockpit_status() -> dict[str, Any]:
    downloads = safe_downloads_status()
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "downloads": downloads,
        "document_work": document_work_status(downloads=downloads),
        "backup": format_backup_activity_reminder(),
        "vault": document_vault_status_summary(),
        "scandocu": probe_scandocu(),
        "git": git_status_summary(),
    }


def git_status_summary(root: Path = GIT_ROOT) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["/usr/bin/git", "-C", str(root), "status", "--short", "--branch"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "message": str(exc), "branch": "", "dirty_count": 0, "dirty_files": []}
    if completed.returncode != 0:
        return {
            "ok": False,
            "message": (completed.stderr or completed.stdout).strip(),
            "branch": "",
            "dirty_count": 0,
            "dirty_files": [],
        }
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    branch = lines[0].replace("## ", "", 1) if lines else ""
    dirty_files = [line.strip() for line in lines[1:]]
    message = "čistý pracovní strom" if not dirty_files else f"{len(dirty_files)} změn v pracovním stromu"
    return {
        "ok": True,
        "message": message,
        "branch": branch,
        "dirty_count": len(dirty_files),
        "dirty_files": dirty_files[:8],
        "ahead": "ahead" in branch,
        "behind": "behind" in branch,
    }


def safe_downloads_status(limit: int = 20) -> dict[str, Any]:
    try:
        items = scan_downloads_for_pdfs(
            downloads_dir=DEFAULT_DOWNLOADS_DIR,
            vault_dir=DEFAULT_DOCUMENTS_DIR,
            limit=limit,
        )
    except ValueError as exc:
        return {"ok": False, "error": str(exc), "items": []}
    counts: dict[str, int] = {}
    for item in items:
        status = str(item.get("status", "unknown"))
        counts[status] = counts.get(status, 0) + 1
        path_value = item.get("path")
        if isinstance(path_value, str) and path_value and is_pdf_encrypted(Path(path_value)):
            item["is_encrypted"] = True
            item["problem_kind"] = "encrypted"
            item["problem_label"] = "šifrované PDF"
    return {
        "ok": True,
        "folder": str(DEFAULT_DOWNLOADS_DIR),
        "counts": counts,
        "items": items,
    }


def document_work_status(
    downloads: dict[str, Any] | None = None,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 8,
) -> dict[str, Any]:
    downloads = downloads if downloads is not None else safe_downloads_status(limit=50)
    items = [item for item in downloads.get("items", []) if isinstance(item, dict)]
    new_pdfs = [item for item in items if item.get("status") == "new"][:limit]
    problems = [with_problem_label(item) for item in items if download_problem_kind(item)][:limit]
    review = stored_documents_review_status(vault_dir=vault_dir, limit=limit)
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


def stored_documents_review_status(vault_dir: Path = DEFAULT_DOCUMENTS_DIR, limit: int = 8) -> dict[str, Any]:
    text_by_id = {
        str(item.get("document_id", "")): str(item.get("text", ""))
        for item in read_jsonl(vault_dir / "index" / "text_index.jsonl")
    }
    pending: list[dict[str, Any]] = []
    status_counts = {status: 0 for status in READING_STATUS_LABELS}
    for row in read_jsonl(vault_dir / "index" / "documents_index.jsonl"):
        document_id = str(row.get("document_id", ""))
        if not document_id:
            continue
        reading_status = effective_document_reading_status(row, text_chars=len(text_by_id.get(document_id, "")))
        status_counts[reading_status] = status_counts.get(reading_status, 0) + 1
        if reading_status != "needs_review":
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


def normalize_reading_status(value: str) -> str:
    normalized = safe_slug(value, default="", limit=80)
    if normalized in READING_STATUS_LABELS:
        return normalized
    alias = READING_STATUS_ALIASES.get(normalized)
    if alias:
        return alias
    raise ValueError("Neznámý stav čtení dokumentu.")


def document_reference(document_id: str) -> str:
    digest = hashlib.sha256(document_id.encode("utf-8")).hexdigest()[:16]
    return f"docref-{digest}"


def find_document_row_index_by_reference(documents: list[dict[str, Any]], reference: str) -> int | None:
    safe_reference = safe_slug(reference, default="", limit=140)
    if not safe_reference:
        return None
    for index, row in enumerate(documents):
        if str(row.get("document_id", "")) == safe_reference:
            return index
    if safe_reference.startswith("docref-"):
        for index, row in enumerate(documents):
            document_id = str(row.get("document_id", ""))
            if document_id and document_reference(document_id) == safe_reference:
                return index
    return None


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


def set_document_reading_status_action(
    document_id: str,
    reading_status: str,
    note: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> dict[str, Any]:
    safe_document_id = safe_slug(document_id, default="", limit=140)
    if not safe_document_id:
        return {"ok": False, "message": "Chybí document_id."}
    try:
        normalized_status = normalize_reading_status(reading_status)
    except ValueError as exc:
        return {"ok": False, "message": str(exc)}

    documents_path = vault_dir / "index" / "documents_index.jsonl"
    documents = read_jsonl(documents_path)
    row_index = find_document_row_index_by_reference(documents, safe_document_id)
    if row_index is None:
        return {"ok": False, "message": "Dokument nebyl nalezen v indexu."}

    current = dict(documents[row_index])
    resolved_document_id = str(current.get("document_id", ""))
    stored_path = PROJECT_ROOT / str(current.get("stored_path", ""))
    manifest_path = stored_path.parent / "manifest.json"
    manifest = read_json_file(manifest_path) if manifest_path.exists() else {}
    updated = {**current, **manifest}
    previous_status = effective_document_reading_status(updated)
    now_value = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    updated["reading_status"] = normalized_status
    updated["reading_status_updated_at"] = now_value
    if note.strip():
        updated["reading_status_note"] = safe_text(note.strip())

    backup_dir = backup_document_reading_status_metadata(
        vault_dir=vault_dir,
        document_id=resolved_document_id,
        manifest_path=manifest_path,
    )
    documents[row_index] = updated
    write_jsonl(documents_path, documents)
    if manifest_path.exists():
        write_json(manifest_path, updated)
    append_jsonl(
        vault_dir / "index" / "document_reading_status_actions.jsonl",
        {
            "action": "set_reading_status",
            "document_id": resolved_document_id,
            "previous_status": previous_status,
            "reading_status": normalized_status,
            "reading_status_label": READING_STATUS_LABELS[normalized_status],
            "note": safe_text(note.strip()),
            "created_at": now_value,
            "backup_dir": str(relative_to_project(backup_dir)),
            "do_not_commit": True,
        },
    )
    return {
        "ok": True,
        "document_id": safe_text(resolved_document_id),
        "document_ref": document_reference(resolved_document_id),
        "reading_status": normalized_status,
        "reading_status_label": READING_STATUS_LABELS[normalized_status],
        "message": f"Stav dokumentu uložen: {READING_STATUS_LABELS[normalized_status]}.",
    }


def backup_document_reading_status_metadata(vault_dir: Path, document_id: str, manifest_path: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = vault_dir / "index" / "status_backups" / f"{stamp}_{document_id}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    index_path = vault_dir / "index" / "documents_index.jsonl"
    if index_path.exists():
        shutil.copy2(index_path, backup_dir / "documents_index.jsonl")
    if manifest_path.exists():
        shutil.copy2(manifest_path, backup_dir / "manifest.json")
    return backup_dir


def download_problem_kind(item: dict[str, Any]) -> str:
    if item.get("is_encrypted"):
        return "encrypted"
    status = str(item.get("status", ""))
    if status == "invalid":
        return "invalid"
    if status in {"already_in_vault", "duplicate"}:
        return "duplicate"
    if status == "skipped":
        return "skipped"
    return ""


def with_problem_label(item: dict[str, Any]) -> dict[str, Any]:
    kind = download_problem_kind(item)
    labels = {
        "encrypted": "šifrované PDF",
        "duplicate": "už uložené / duplicita",
        "skipped": "přeskočeno",
        "invalid": "neplatný soubor",
    }
    enriched = dict(item)
    enriched["problem_kind"] = kind
    enriched["problem_label"] = labels.get(kind, kind or "problém")
    return enriched


def search_document_index(
    query: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 8,
) -> dict[str, Any]:
    terms = [term.casefold() for term in tokenize(query) if len(term) >= 2]
    if not terms:
        return {"ok": False, "message": "Zadej konkrétnější dotaz.", "results": []}

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
        scored.append((score, metadata, snippet, len(text)))

    results: list[dict[str, Any]] = []
    for score, metadata, snippet, text_chars in sorted(scored, key=lambda row: row[0], reverse=True)[
        : max(1, min(limit, 20))
    ]:
        reading_status = effective_document_reading_status(metadata, text_chars=text_chars)
        results.append(
            {
                "score": score,
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
    return {
        "ok": True,
        "query": query,
        "count": len(results),
        "results": results,
        "message": "Nalezena shoda." if results else "V dokumentech jsem nenašla shodu.",
    }


def prepare_document_print_action(document_id: str, vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> dict[str, Any]:
    documents = read_jsonl(vault_dir / "index" / "documents_index.jsonl")
    row_index = find_document_row_index_by_reference(documents, document_id)
    if row_index is None:
        return {"ok": False, "message": "Dokument nebyl nalezen v indexu."}
    resolved_document_id = str(documents[row_index].get("document_id", ""))
    try:
        result = prepare_document_print_job(document_id=resolved_document_id, vault_dir=vault_dir)
    except ValueError as exc:
        return {"ok": False, "message": str(exc)}
    return {
        "ok": True,
        "message": "Dokument je připraven k tisku. Originál ve vaultu zůstal beze změny.",
        "print_job_id": result.print_job_id,
        "document_id": result.document_id,
        "queue_path": str(relative_to_project(result.queue_path)),
    }


def run_document_print_action(
    print_job_id: str,
    confirmation_text: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> dict[str, Any]:
    safe_print_job_id = safe_slug(print_job_id, default="", limit=120)
    try:
        result = run_document_print_job(
            print_job_id=safe_print_job_id,
            user_confirmed=True,
            confirmation_text=confirmation_text,
            vault_dir=vault_dir,
        )
    except ValueError as exc:
        return {"ok": False, "message": str(exc)}
    return {
        "ok": result.status == "printed",
        "status": result.status,
        "message": result.message,
        "print_job_id": result.print_job_id,
        "document_id": result.document_id,
    }


def move_document_lifecycle_action(
    document_id: str,
    target: str,
    confirmation_text: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> dict[str, Any]:
    safe_reference = safe_slug(document_id, default="", limit=140)
    if not safe_reference:
        return {"ok": False, "message": "Chybí document_id."}
    documents = read_jsonl(vault_dir / "index" / "documents_index.jsonl")
    row_index = find_document_row_index_by_reference(documents, safe_reference)
    if row_index is None:
        return {"ok": False, "message": "Dokument nebyl nalezen v indexu."}
    resolved_document_id = str(documents[row_index].get("document_id", ""))
    if target not in {"archive", "trash"}:
        return {"ok": False, "message": "Neznámá akce nad dokumentem."}
    required = (
        f"Potvrzuji, archivuj dokument {safe_reference}."
        if target == "archive"
        else f"Potvrzuji, přesuň dokument {safe_reference} do koše."
    )
    if confirmation_text.strip() != required:
        return {"ok": False, "message": f"Chybí přesné potvrzení: {required}"}

    try:
        return move_document_to_archive_or_trash(
            document_id=resolved_document_id,
            target=target,
            vault_dir=vault_dir,
        )
    except ValueError as exc:
        return {"ok": False, "message": str(exc)}


def move_document_to_archive_or_trash(
    document_id: str,
    target: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> dict[str, Any]:
    documents_path = vault_dir / "index" / "documents_index.jsonl"
    documents = read_jsonl(documents_path)
    row_index = next((index for index, row in enumerate(documents) if str(row.get("document_id", "")) == document_id), None)
    if row_index is None:
        raise ValueError(f"Dokument {document_id} nebyl nalezen v indexu.")
    current = dict(documents[row_index])
    stored_path = PROJECT_ROOT / str(current.get("stored_path", ""))
    try:
        resolved_stored_path = stored_path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ValueError("Dokument je v indexu, ale soubor ve vaultu nebyl nalezen.") from exc
    document_dir = resolved_stored_path.parent
    vault_root = vault_dir.resolve()
    if vault_root not in document_dir.parents:
        raise ValueError("Dokument není uvnitř povoleného document vaultu.")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    domain = safe_slug(str(current.get("domain", "other")), default="other", limit=80)
    if target == "archive":
        target_dir = next_available_path(vault_dir / "archive" / domain / document_id)
        lifecycle_status = "archived"
        action = "archived"
        time_key = "archived_at"
        message = "Dokument byl přesunut do archivu."
    else:
        target_dir = next_available_path(vault_dir / "trash" / f"{stamp}_{document_id}")
        lifecycle_status = "trashed"
        action = "moved_to_trash"
        time_key = "trashed_at"
        message = "Dokument byl přesunut do koše. Nebyl trvale smazán."

    target_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(document_dir), str(target_dir))
    new_stored_path = target_dir / resolved_stored_path.name
    now_value = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    updated = dict(current)
    updated["stored_path"] = str(relative_to_project(new_stored_path))
    updated["lifecycle_status"] = lifecycle_status
    updated[time_key] = now_value
    documents[row_index] = updated
    write_jsonl(documents_path, documents)

    manifest_path = target_dir / "manifest.json"
    if manifest_path.exists():
        manifest = read_json_file(manifest_path)
        manifest.update(updated)
        write_json(manifest_path, manifest)

    append_jsonl(
        vault_dir / "index" / "document_lifecycle_actions.jsonl",
        {
            "action": action,
            "document_id": document_id,
            "from_path": str(relative_to_project(document_dir)),
            "to_path": str(relative_to_project(target_dir)),
            "created_at": now_value,
            "do_not_commit": True,
        },
    )
    return {
        "ok": True,
        "status": lifecycle_status,
        "message": message,
        "document_id": document_id,
        "stored_path": str(relative_to_project(new_stored_path)),
    }


def probe_scandocu() -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["/usr/bin/curl", "-fsS", f"{SCANDOCU_URL}/api/list"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"running": False, "url": SCANDOCU_URL, "message": str(exc)}
    return {
        "running": completed.returncode == 0,
        "url": SCANDOCU_URL,
        "message": "běží" if completed.returncode == 0 else "neběží",
    }


def start_scandocu() -> dict[str, Any]:
    if probe_scandocu().get("running"):
        return {"ok": True, "message": "ScanDocu už běží.", "url": SCANDOCU_URL}
    if not SCANDOCU_SERVER_SCRIPT.exists():
        return {"ok": False, "message": f"ScanDocu server neexistuje: {SCANDOCU_SERVER_SCRIPT}"}
    try:
        SCANDOCU_LOG_DIR.mkdir(parents=True, exist_ok=True)
        with SCANDOCU_LOG_FILE.open("a", encoding="utf-8") as log_handle:
            subprocess.Popen(
                [
                    str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                    str(SCANDOCU_SERVER_SCRIPT),
                    "--port",
                    str(SCANDOCU_PORT),
                ],
                cwd=str(PROJECT_ROOT),
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
    except OSError as exc:
        return {"ok": False, "message": f"ScanDocu se nepodařilo spustit: {exc}"}
    for _ in range(10):
        if probe_scandocu().get("running"):
            return {"ok": True, "message": "ScanDocu spuštěno.", "url": SCANDOCU_URL}
        time.sleep(0.2)
    return {"ok": False, "message": f"ScanDocu se spustilo, ale zatím neodpovídá. Log: {SCANDOCU_LOG_FILE}"}


def open_project_terminal() -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["/usr/bin/open", "-a", "Terminal", str(PROJECT_ROOT)],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "message": f"Terminál se nepodařilo otevřít: {exc}"}
    message = completed.stderr.strip() or completed.stdout.strip() or "Terminál otevřen v projektu."
    return {"ok": completed.returncode == 0, "message": message, "returncode": completed.returncode}


def open_terminal_command(command: str, label: str) -> dict[str, Any]:
    script = (
        'tell application "Terminal"\n'
        "  activate\n"
        f'  do script "cd {shell_quote_for_applescript(str(PROJECT_ROOT))}; {command}"\n'
        "end tell\n"
    )
    try:
        completed = subprocess.run(
            ["/usr/bin/osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "message": f"{label} se nepodařilo otevřít: {exc}"}
    detail = completed.stderr.strip() or completed.stdout.strip()
    message = detail or f"{label} otevřen v novém Terminal okně."
    return {"ok": completed.returncode == 0, "message": message, "returncode": completed.returncode}


def open_samantha_chat() -> dict[str, Any]:
    return open_terminal_command("source ~/.zshrc; samantha", "Samantha chat")


def open_codex_cli() -> dict[str, Any]:
    return open_terminal_command("source ~/.zshrc; codex resume --last || codex", "Codex CLI")


def shell_quote_for_applescript(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


class CockpitServer:
    def __init__(self, host: str = "127.0.0.1", port: int = COCKPIT_PORT) -> None:
        self.host = host
        self.port = port

    def serve(self) -> None:
        server = ThreadingHTTPServer((self.host, self.port), self.make_handler())
        print(f"Samantha Cockpit běží na http://{self.host}:{self.port}", flush=True)
        server.serve_forever()

    def make_handler(self):
        class Handler(BaseHTTPRequestHandler):
            server_version = "SamanthaCockpit/0.1"

            def do_GET(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                if parsed.path == "/":
                    self.respond_html(COCKPIT_HTML)
                    return
                if parsed.path == "/email-processing/":
                    self.respond_html(EMAIL_PROCESSING_HTML)
                    return
                if parsed.path == "/api/status":
                    self.respond_json(cockpit_status())
                    return
                if parsed.path == "/api/web-apps":
                    self.respond_json(web_apps_catalog())
                    return
                if parsed.path == "/api/email-processing/overview":
                    self.respond_json(empty_email_processing_overview())
                    return
                if parsed.path == "/api/documents/search":
                    params = parse_qs(parsed.query)
                    query = params.get("q", [""])[0]
                    self.respond_json(search_document_index(query=query))
                    return
                if parsed.path.startswith("/local-apps/"):
                    self.respond_local_app_file(parsed.path)
                    return
                self.respond_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)

            def do_POST(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                if parsed.path == "/api/scandocu/open":
                    self.respond_json(start_scandocu())
                    return
                if parsed.path == "/api/terminal/open":
                    self.respond_json(open_project_terminal())
                    return
                if parsed.path == "/api/samantha/open":
                    self.respond_json(open_samantha_chat())
                    return
                if parsed.path == "/api/codex/open":
                    self.respond_json(open_codex_cli())
                    return
                if parsed.path == "/api/documents/print/prepare":
                    payload = self.read_json()
                    self.respond_json(prepare_document_print_action(document_id=str(payload.get("document_id", ""))))
                    return
                if parsed.path == "/api/documents/print/run":
                    payload = self.read_json()
                    self.respond_json(
                        run_document_print_action(
                            print_job_id=str(payload.get("print_job_id", "")),
                            confirmation_text=str(payload.get("confirmation_text", "")),
                        )
                    )
                    return
                if parsed.path == "/api/documents/lifecycle":
                    payload = self.read_json()
                    self.respond_json(
                        move_document_lifecycle_action(
                            document_id=str(payload.get("document_id", "")),
                            target=str(payload.get("target", "")),
                            confirmation_text=str(payload.get("confirmation_text", "")),
                        )
                    )
                    return
                if parsed.path == "/api/documents/reading-status":
                    payload = self.read_json()
                    self.respond_json(
                        set_document_reading_status_action(
                            document_id=str(payload.get("document_id", "")),
                            reading_status=str(payload.get("reading_status", "")),
                            note=str(payload.get("note", "")),
                        )
                    )
                    return
                if parsed.path == "/api/email-processing/decision":
                    payload = self.read_json()
                    item = payload.get("item")
                    self.respond_json(
                        save_email_processing_decision(
                            item_id=str(payload.get("item_id", "")),
                            action=str(payload.get("action", "")),
                            item=item if isinstance(item, dict) else {},
                        )
                    )
                    return
                if parsed.path == "/api/email-processing/new-headers":
                    payload = self.read_json()
                    raw_limit = payload.get("limit_per_source", 10)
                    raw_days = payload.get("days", 0)
                    try:
                        limit = int(raw_limit)
                    except (TypeError, ValueError):
                        limit = 10
                    try:
                        days = int(raw_days)
                    except (TypeError, ValueError):
                        days = 0
                    raw_known_ids = payload.get("known_ids", [])
                    known_ids = set()
                    if isinstance(raw_known_ids, list):
                        known_ids = {str(item_id).strip() for item_id in raw_known_ids if str(item_id).strip()}
                    self.respond_json(
                        new_email_headers_overview(
                            limit_per_source=limit,
                            since=str(payload.get("since", "")),
                            days=days,
                            known_ids=known_ids,
                        )
                    )
                    return
                self.respond_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)

            def read_json(self) -> dict[str, Any]:
                length = int(self.headers.get("Content-Length", "0") or "0")
                raw = self.rfile.read(length).decode("utf-8") if length else "{}"
                data = json.loads(raw or "{}")
                if not isinstance(data, dict):
                    raise ValueError("JSON payload musí být objekt.")
                return data

            def log_message(self, format: str, *args: Any) -> None:
                return

            def respond_html(self, html: str) -> None:
                data = html.encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store, max-age=0")
                self.send_header("Pragma", "no-cache")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def respond_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
                data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store, max-age=0")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def respond_local_app_file(self, request_path: str) -> None:
                parts = [part for part in request_path.split("/") if part]
                if len(parts) < 2 or parts[0] != "local-apps":
                    self.respond_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)
                    return
                app_id = parts[1]
                root = LOCAL_WEB_APPS.get(app_id)
                if root is None:
                    self.respond_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)
                    return
                rel_parts = parts[2:]
                if not rel_parts:
                    relative = Path("index.html")
                elif request_path.endswith("/"):
                    relative = Path(*rel_parts) / "index.html"
                else:
                    relative = Path(*rel_parts)
                try:
                    root_resolved = root.resolve(strict=True)
                    target = (root / relative).resolve(strict=True)
                except FileNotFoundError:
                    self.respond_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)
                    return
                if root_resolved != target and root_resolved not in target.parents:
                    self.respond_json({"error": "forbidden"}, status=HTTPStatus.FORBIDDEN)
                    return
                if not target.is_file():
                    self.respond_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)
                    return
                data = target.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", content_type_for_path(target))
                self.send_header("Cache-Control", "no-store, max-age=0")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        return Handler


def content_type_for_path(path: Path) -> str:
    suffix = path.suffix.casefold()
    if suffix == ".html":
        return "text/html; charset=utf-8"
    if suffix == ".css":
        return "text/css; charset=utf-8"
    if suffix == ".js":
        return "text/javascript; charset=utf-8"
    if suffix == ".json":
        return "application/json; charset=utf-8"
    if suffix in {".png"}:
        return "image/png"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    return "application/octet-stream"


EMAIL_PROCESSING_HTML = """<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Email Processing</title>
  <style>
    :root { --bg: #f5f7fb; --panel: #ffffff; --ink: #162033; --muted: #667085; --line: #d9e0ea; --blue: #1f5fbf; --green: #16794c; --amber: #9a5b00; }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--bg); color: var(--ink); font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    header { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 16px 20px; background: var(--panel); border-bottom: 1px solid var(--line); position: sticky; top: 0; z-index: 2; }
    h1 { margin: 0; font-size: 20px; }
    button { border: 0; border-radius: 6px; padding: 9px 12px; font: inherit; font-weight: 650; cursor: pointer; white-space: nowrap; }
    button.primary { background: var(--blue); color: white; }
    button.secondary { background: #e8eef8; color: #1d3b74; }
    input[type="number"] { width: 54px; border: 1px solid var(--line); border-radius: 6px; padding: 8px 7px; font: inherit; font-weight: 650; color: var(--ink); background: white; }
    main { padding: 18px 20px 28px; display: grid; gap: 14px; }
    .toolbar { display: flex; gap: 8px; flex-wrap: wrap; }
    .days-control { display: inline-flex; align-items: center; gap: 6px; color: var(--muted); font-size: 13px; white-space: nowrap; }
    .grid { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 14px; align-items: start; }
    section, aside { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
    h2 { margin: 0; padding: 12px 14px; font-size: 14px; border-bottom: 1px solid var(--line); background: #f8fafc; }
    .body { padding: 13px 14px; }
    .status-line { color: var(--muted); font-size: 13px; overflow-wrap: anywhere; }
    .meta { display: grid; gap: 7px; color: var(--muted); font-size: 13px; }
    .meta strong { color: var(--ink); }
    .pill-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
    .pill { border: 1px solid var(--line); border-radius: 999px; padding: 5px 8px; font-size: 12px; background: #f8fafc; }
    .overview { display: grid; gap: 10px; }
    .category { border: 1px solid #edf0f4; border-radius: 8px; background: #fbfcfe; overflow: hidden; }
    .category h3 { margin: 0; padding: 10px 11px; font-size: 14px; border-bottom: 1px solid #edf0f4; }
    .category pre { margin: 0; padding: 11px; white-space: pre-wrap; overflow-wrap: anywhere; font: 12px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; color: #263244; }
    .category-items { display: grid; gap: 9px; padding: 10px; }
    .email-card { border: 1px solid #edf0f4; border-radius: 8px; background: #fbfcfe; padding: 11px; display: grid; gap: 8px; }
    .email-card.new-header { border-color: #b8cdf2; background: #f5f8ff; }
    .email-head { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; align-items: start; }
    .email-title { font-weight: 750; overflow-wrap: anywhere; }
    .email-meta, .email-reason { color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
    .email-actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; border-top: 1px solid #edf0f4; padding-top: 8px; }
    .email-actions label { display: inline-flex; gap: 5px; align-items: center; font-size: 13px; }
    .email-actions input { margin: 0; }
    .trash-button { background: #fee2e2; color: #991b1b; padding: 7px 10px; }
    .decision { color: var(--green); font-size: 12px; font-weight: 650; }
    .work-button { width: 100%; }
    .work-button:disabled { opacity: 0.45; cursor: not-allowed; }
    .headers-box { display: grid; gap: 8px; margin-top: 10px; }
    .busy-row { display: none; align-items: center; gap: 8px; padding: 8px 9px; border-radius: 7px; background: #eef4ff; color: #1d3b74; font-size: 13px; font-weight: 650; }
    .busy-row.active { display: flex; }
    .spinner { width: 14px; height: 14px; border: 2px solid #bfd0ef; border-top-color: var(--blue); border-radius: 50%; animation: spin 0.8s linear infinite; flex: 0 0 auto; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .empty { padding: 14px; color: var(--muted); }
    .safe { color: var(--green); font-weight: 700; }
    .warn { color: var(--amber); font-weight: 700; }
    @media (max-width: 900px) { header { align-items: flex-start; flex-direction: column; } .grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <header>
    <h1>Email Processing</h1>
    <div class="toolbar">
      <button class="secondary" id="refreshBtn">Obnovit nové</button>
      <span class="days-control">
        <span>Za posledních:</span>
        <input id="emailDaysInput" type="number" min="1" max="14" step="1" value="7" inputmode="numeric" aria-label="Počet dní">
        <span>dní</span>
      </span>
      <button class="primary" id="loadHeadersBtn">Načti emaily</button>
      <button class="secondary" id="cockpitBtn">Otevřít Cockpit</button>
    </div>
  </header>
  <main>
    <div class="grid">
      <section>
        <h2>Pracovní seznam e-mailů</h2>
        <div class="body">
          <div id="overviewStatus" class="status-line">Načítám uložený přehled...</div>
          <div id="overview" class="overview"></div>
        </div>
      </section>
      <aside>
        <h2>Bezpečnost</h2>
        <div class="body meta">
          <div><strong>Režim:</strong> <span class="safe">read-only</span></div>
          <div>Okno startuje prázdné. Nové hlavičky se načtou až tlačítkem.</div>
          <div><strong>Obnovit nové:</strong> doplní jen e-maily novější než aktuální seznam.</div>
          <div><strong>Načti emaily:</strong> doplní jen e-maily ve zvoleném rozsahu 1-14 dní, které ještě nejsou v aktuálním seznamu ani nemají uložené rozhodnutí.</div>
          <div><strong>Koš:</strong> tlačítko zatím jen označí e-mail ke smazání; skutečné smazání bude samostatná potvrzená akce.</div>
          <div><strong>Další krok:</strong> vybrat konkrétní UID a zdroj; načtení e-mailu nebo PDF až po samostatném potvrzení.</div>
          <div id="sourcePath" class="status-line"></div>
          <div id="updatedAt" class="status-line"></div>
          <button class="primary work-button" id="processEmailsBtn" disabled>Zpracovat e-maily</button>
          <div id="processEmailsStatus" class="status-line">Nejdřív přiřaď status všem viditelným e-mailům.</div>
          <div class="headers-box">
            <div id="headersBusy" class="busy-row" role="status" aria-live="polite">
              <span class="spinner" aria-hidden="true"></span>
              <span id="headersBusyText">Načítám...</span>
            </div>
            <div id="newHeadersStatus" class="status-line"></div>
          </div>
          <div class="pill-row">
            <span class="pill">faktury/e-shopy</span>
            <span class="pill">pojištění/smlouvy</span>
            <span class="pill">úřady/daně</span>
            <span class="pill">ostatní</span>
          </div>
        </div>
      </aside>
    </div>
  </main>
  <script>
    const overviewStatus = document.getElementById("overviewStatus");
    const overview = document.getElementById("overview");
    const sourcePath = document.getElementById("sourcePath");
    const updatedAt = document.getElementById("updatedAt");
    const refreshBtn = document.getElementById("refreshBtn");
    const loadHeadersBtn = document.getElementById("loadHeadersBtn");
    const emailDaysInput = document.getElementById("emailDaysInput");
    const headersBusy = document.getElementById("headersBusy");
    const headersBusyText = document.getElementById("headersBusyText");
    const newHeadersStatus = document.getElementById("newHeadersStatus");
    const processEmailsBtn = document.getElementById("processEmailsBtn");
    const processEmailsStatus = document.getElementById("processEmailsStatus");
    const cockpitBtn = document.getElementById("cockpitBtn");
    let headersBusyTimer = null;
    let emailItems = [];
    let overviewSince = "";

    function categoryTitle(raw) {
      return raw.replace(/^#+\\s*/, "").trim();
    }

    function splitOverview(text) {
      const allowed = new Set([
        "Faktury / e-shopy",
        "Pojisteni / smlouvy",
        "Pojištění / smlouvy",
        "Urady / dane",
        "Úřady / daně",
        "Ostatni kandidati",
        "Ostatní kandidáti",
        "Doporučeny dalsi krok po navazani",
        "Doporučený další krok po navázání"
      ]);
      const sections = [];
      let current = null;
      text.split(/\\r?\\n/).forEach((line) => {
        if (line.startsWith("## ")) {
          const title = categoryTitle(line);
          if (allowed.has(title)) {
            current = {title, lines: []};
            sections.push(current);
          } else {
            current = null;
          }
          return;
        }
        if (current) current.lines.push(line);
      });
      return sections.map((section) => ({
        title: section.title,
        text: section.lines.join("\\n").trim()
      })).filter((section) => section.text);
    }

    function renderSections(sections) {
      overview.innerHTML = "";
      if (!sections.length) {
        const empty = document.createElement("div");
        empty.className = "empty";
        empty.textContent = "Uložený přehled neobsahuje rozpoznatelné kategorie.";
        overview.appendChild(empty);
        return;
      }
      sections.forEach((section) => {
        const card = document.createElement("div");
        card.className = "category";
        const title = document.createElement("h3");
        title.textContent = section.title;
        const pre = document.createElement("pre");
        pre.textContent = section.text;
        card.appendChild(title);
        card.appendChild(pre);
        overview.appendChild(card);
      });
    }

    function actionLabel(action) {
      if (action === "process") return "Zpracovat";
      if (action === "ignore") return "Ignorovat";
      if (action === "trash_requested") return "Koš - čeká na potvrzení";
      return "";
    }

    function decisionCounts(items) {
      const counts = {total: 0, decided: 0, process: 0, ignore: 0, trash: 0};
      (items || []).forEach((item) => {
        counts.total += 1;
        if (item.action) counts.decided += 1;
        if (item.action === "process") counts.process += 1;
        if (item.action === "ignore") counts.ignore += 1;
        if (item.action === "trash_requested") counts.trash += 1;
      });
      return counts;
    }

    function updateWorkQueueState() {
      const counts = decisionCounts(emailItems);
      const actionable = counts.process + counts.trash;
      if (!counts.total) {
        processEmailsBtn.disabled = true;
        processEmailsBtn.textContent = "Zpracovat e-maily";
        processEmailsStatus.textContent = "Zatím není načtený žádný e-mailový seznam.";
        return;
      }
      if (counts.decided < counts.total) {
        processEmailsBtn.disabled = true;
        processEmailsBtn.textContent = "Zpracovat e-maily";
        processEmailsStatus.textContent = `Rozhodnuto ${counts.decided}/${counts.total}. Zbývá označit ${counts.total - counts.decided}.`;
        return;
      }
      processEmailsBtn.disabled = false;
      processEmailsStatus.textContent = `Připraveno: zpracovat ${counts.process}, koš ${counts.trash}, ignorovat ${counts.ignore}.`;
      processEmailsBtn.textContent = actionable ? `Zpracovat e-maily (${actionable})` : "Zpracovat e-maily";
    }

    function itemMeta(item) {
      const parts = [];
      if (item.provider) parts.push(item.provider);
      if (item.folder) parts.push(item.folder);
      if (item.uid) parts.push(`UID ${item.uid}`);
      if (item.date) parts.push(item.date);
      if (item.category) parts.push(item.category);
      return parts.join(" | ");
    }

    function categoryTitleForKey(key) {
      if (key === "faktury/e-shopy") return "Faktury / e-shopy";
      if (key === "pojištění/smlouvy") return "Pojištění / smlouvy";
      if (key === "úřady/daně") return "Úřady / daně";
      return "Ostatní";
    }

    function itemDateValue(item) {
      const parsed = Date.parse(item.date || "");
      return Number.isFinite(parsed) ? parsed : 0;
    }

    function knownItemIds() {
      const ids = [];
      emailItems.forEach((item) => {
        if (item && item.id) ids.push(item.id);
        if (item && item.legacy_id) ids.push(item.legacy_id);
      });
      return ids;
    }

    function newestItemIso() {
      const latest = Math.max(0, ...emailItems.map(itemDateValue));
      return latest ? new Date(latest).toISOString() : "";
    }

    function selectedDays() {
      const parsed = Number.parseInt(emailDaysInput.value, 10);
      if (!Number.isFinite(parsed)) return 7;
      return Math.min(14, Math.max(1, parsed));
    }

    function normalizeDaysInput() {
      emailDaysInput.value = String(selectedDays());
    }

    function mergeItems(existing, incoming) {
      const byId = new Map();
      (existing || []).forEach((item) => {
        if (item && item.id) byId.set(item.id, item);
      });
      (incoming || []).forEach((item) => {
        if (!item || !item.id || byId.has(item.id)) return;
        if (item.legacy_id && byId.has(item.legacy_id)) return;
        byId.set(item.id, item);
        if (item.legacy_id) byId.set(item.legacy_id, item);
      });
      return Array.from(new Set(byId.values())).sort((a, b) => itemDateValue(b) - itemDateValue(a));
    }

    function createEmailCard(item) {
      const card = document.createElement("div");
      card.className = item.is_new_header ? "email-card new-header" : "email-card";
      card.dataset.itemId = item.id || "";
      const head = document.createElement("div");
      head.className = "email-head";
      const summary = document.createElement("div");
      const title = document.createElement("div");
      title.className = "email-title";
      title.textContent = item.subject || "(bez předmětu)";
      const meta = document.createElement("div");
      meta.className = "email-meta";
      meta.textContent = itemMeta(item);
      const decision = document.createElement("div");
      decision.className = "decision";
      decision.textContent = item.is_new_header ? "nově načteno" : actionLabel(item.action || "");
      summary.appendChild(title);
      summary.appendChild(meta);
      if (item.reason) {
        const reason = document.createElement("div");
        reason.className = "email-reason";
        reason.textContent = `Důvod: ${item.reason}`;
        summary.appendChild(reason);
      }
      head.appendChild(summary);
      head.appendChild(decision);

      const actions = document.createElement("div");
      actions.className = "email-actions";
      [
        ["process", "Zpracovat"],
        ["ignore", "Ignorovat"]
      ].forEach(([value, labelText]) => {
        const label = document.createElement("label");
        const input = document.createElement("input");
        input.type = "checkbox";
        input.checked = item.action === value;
        input.addEventListener("change", () => {
          const nextAction = input.checked ? value : "";
          actions.querySelectorAll('input[type="checkbox"]').forEach((other) => {
            if (other !== input) other.checked = false;
          });
          item.is_new_header = false;
          card.classList.remove("new-header");
          saveDecision(item, nextAction, decision);
        });
        label.appendChild(input);
        label.appendChild(document.createTextNode(labelText));
        actions.appendChild(label);
      });

      const trash = document.createElement("button");
      trash.className = "trash-button";
      trash.type = "button";
      trash.textContent = "Koš";
      trash.addEventListener("click", () => {
        const ok = window.confirm("Označit tento e-mail ke smazání?\\n\\nE-mail se teď fyzicky nemaže, jen se uloží pracovní rozhodnutí.");
        if (!ok) return;
        actions.querySelectorAll('input[type="checkbox"]').forEach((input) => {
          input.checked = false;
        });
        item.is_new_header = false;
        card.classList.remove("new-header");
        saveDecision(item, "trash_requested", decision);
      });
      actions.appendChild(trash);
      card.appendChild(head);
      card.appendChild(actions);
      return card;
    }

    function renderItems(items) {
      overview.innerHTML = "";
      if (!items || !items.length) {
        if (!window.lastOverviewText) {
          const empty = document.createElement("div");
          empty.className = "empty";
          empty.textContent = "Pracovní seznam je prázdný. Zadej rozsah 1-14 dní a klikni Načti emaily.";
          overview.appendChild(empty);
          return;
        }
        renderSections(splitOverview(window.lastOverviewText || ""));
        return;
      }
      const order = ["faktury/e-shopy", "pojištění/smlouvy", "úřady/daně", "ostatní"];
      const grouped = new Map(order.map((key) => [key, []]));
      items.forEach((item) => {
        const key = order.includes(item.category) ? item.category : "ostatní";
        grouped.get(key).push(item);
      });
      order.forEach((key) => {
        const groupItems = grouped.get(key);
        const section = document.createElement("div");
        section.className = "category";
        const title = document.createElement("h3");
        title.textContent = `${categoryTitleForKey(key)} (${groupItems.length})`;
        const body = document.createElement("div");
        body.className = "category-items";
        if (groupItems.length) {
          groupItems.forEach((item) => body.appendChild(createEmailCard(item)));
        } else {
          const empty = document.createElement("div");
          empty.className = "status-line";
          empty.textContent = "Žádné položky.";
          body.appendChild(empty);
        }
        section.appendChild(title);
        section.appendChild(body);
        overview.appendChild(section);
      });
    }

    async function saveDecision(item, action, decisionNode) {
      if (!item || !item.id) return;
      decisionNode.textContent = "Ukládám...";
      try {
        const res = await fetch("/api/email-processing/decision", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({item_id: item.id, action, item})
        });
        const data = await res.json();
        if (!data.ok) {
          decisionNode.textContent = data.message || "Uložení selhalo";
          return;
        }
        item.action = action;
        decisionNode.textContent = actionLabel(action);
        overviewStatus.textContent = data.message || "Rozhodnutí uloženo.";
        updateWorkQueueState();
      } catch (err) {
        decisionNode.textContent = `Chyba: ${err}`;
      }
    }

    function escapeHtml(value) {
      return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }

    function workQueueRows(items) {
      if (!items.length) return '<div class="empty">Žádné položky.</div>';
      return items.map((item) => `
        <article class="item">
          <div class="subject">${escapeHtml(item.subject || "(bez předmětu)")}</div>
          <div class="meta">${escapeHtml(itemMeta(item))}</div>
          ${item.reason ? `<div class="reason">Důvod: ${escapeHtml(item.reason)}</div>` : ""}
        </article>
      `).join("");
    }

    function openWorkQueueWindow() {
      const counts = decisionCounts(emailItems);
      if (!counts.total || counts.decided < counts.total) {
        window.alert("Nejdřív přiřaď status všem viditelným e-mailům.");
        return;
      }
      const toProcess = emailItems.filter((item) => item.action === "process");
      const toTrash = emailItems.filter((item) => item.action === "trash_requested");
      const ignored = emailItems.filter((item) => item.action === "ignore");
      const queue = window.open("", "SamanthaEmailWorkQueue", "popup=yes,width=980,height=760,left=140,top=70");
      if (!queue) {
        window.alert("Popup okno bylo blokováno. Povol v prohlížeči vyskakovací okna pro lokální Cockpit.");
        return;
      }
      queue.document.open();
      queue.document.write(`<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Email Work Queue</title>
  <style>
    :root { --bg: #f5f7fb; --panel: #ffffff; --ink: #162033; --muted: #667085; --line: #d9e0ea; --blue: #1f5fbf; --red: #991b1b; --amber: #9a5b00; }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--bg); color: var(--ink); font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    header { padding: 16px 20px; background: var(--panel); border-bottom: 1px solid var(--line); }
    h1 { margin: 0; font-size: 20px; }
    main { padding: 18px 20px 28px; display: grid; gap: 14px; }
    section { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
    h2 { margin: 0; padding: 12px 14px; font-size: 14px; border-bottom: 1px solid var(--line); background: #f8fafc; }
    .body { padding: 13px 14px; display: grid; gap: 9px; }
    .item { border: 1px solid #edf0f4; border-radius: 8px; padding: 10px; background: #fbfcfe; display: grid; gap: 5px; }
    .subject { font-weight: 750; overflow-wrap: anywhere; }
    .meta, .reason, .empty, .note { color: var(--muted); font-size: 13px; overflow-wrap: anywhere; }
    .note strong { color: var(--ink); }
    .trash h2 { color: var(--red); }
  </style>
</head>
<body>
  <header>
    <h1>Email Work Queue</h1>
  </header>
  <main>
    <section>
      <h2>Souhrn</h2>
      <div class="body note">
        <div><strong>Připraveno ke zpracování:</strong> ${toProcess.length}</div>
        <div><strong>Koš čeká na potvrzení:</strong> ${toTrash.length}</div>
        <div><strong>Ignorováno:</strong> ${ignored.length}</div>
        <div>Tohle okno zatím nic nečte, nestahuje a nemaže. Další krok bude postupně otevírat konkrétní položky a každé čtení e-mailu, uložení PDF nebo smazání bude samostatně potvrzené.</div>
      </div>
    </section>
    <section>
      <h2>Zpracovat</h2>
      <div class="body">${workQueueRows(toProcess)}</div>
    </section>
    <section class="trash">
      <h2>Koš - čeká na potvrzení</h2>
      <div class="body">${workQueueRows(toTrash)}</div>
    </section>
  </main>
</body>
</html>`);
      queue.document.close();
      queue.focus();
    }

    async function loadNewHeaders(options = {}) {
      const lastSevenDays = Boolean(options.lastSevenDays);
      const newOnly = Boolean(options.newOnly);
      const startedAt = Date.now();
      const days = selectedDays();
      refreshBtn.disabled = true;
      loadHeadersBtn.disabled = true;
      emailDaysInput.disabled = true;
      headersBusy.classList.add("active");
      headersBusyText.textContent = lastSevenDays
        ? `Doplňuji chybějící hlavičky za posledních ${days} dní... 0 s`
        : "Načítám nové hlavičky... 0 s";
      headersBusyTimer = window.setInterval(() => {
        const seconds = Math.max(0, Math.round((Date.now() - startedAt) / 1000));
        headersBusyText.textContent = lastSevenDays
          ? `Doplňuji posledních ${days} dní z iCloud + Seznam... ${seconds} s`
          : `Načítám nové hlavičky z iCloud + Seznam... ${seconds} s`;
      }, 1000);
      newHeadersStatus.textContent = lastSevenDays
        ? `Doplňuji jen dosud nenačtené a nerozhodnuté hlavičky za posledních ${days} dní...`
        : "Doplňuji jen nové příchozí hlavičky z iCloud + Seznam...";
      try {
        const payload = lastSevenDays
          ? {limit_per_source: days <= 7 ? 50 : 75, days, known_ids: knownItemIds()}
          : {limit_per_source: 25, since: newestItemIso() || overviewSince, known_ids: knownItemIds()};
        const res = await fetch("/api/email-processing/new-headers", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        const incoming = data.items || [];
        const before = emailItems.length;
        emailItems = mergeItems(emailItems, incoming);
        renderItems(emailItems);
        updateWorkQueueState();
        const added = emailItems.length - before;
        const unavailable = data.unavailable && data.unavailable.length
          ? ` Nedostupné zdroje: ${data.unavailable.join("; ")}`
          : "";
        newHeadersStatus.textContent = `${data.message || "Hotovo."} Přidáno do hlavního seznamu: ${added}.${unavailable}`;
      } catch (err) {
        newHeadersStatus.textContent = `Chyba načtení hlaviček: ${err}`;
      } finally {
        if (headersBusyTimer) {
          window.clearInterval(headersBusyTimer);
          headersBusyTimer = null;
        }
        headersBusy.classList.remove("active");
        refreshBtn.disabled = false;
        loadHeadersBtn.disabled = false;
        emailDaysInput.disabled = false;
      }
    }

    async function loadOverview() {
      refreshBtn.disabled = true;
      overviewStatus.textContent = "Načítám uložený přehled...";
      overview.innerHTML = "";
      try {
        const res = await fetch("/api/email-processing/overview");
        const data = await res.json();
        overviewStatus.textContent = data.message || "";
        sourcePath.textContent = data.path ? `Soubor: ${data.path}` : "";
        updatedAt.textContent = data.updated_at ? `Aktualizováno: ${data.updated_at}` : "";
        if (!data.ok) {
          const empty = document.createElement("div");
          empty.className = "empty";
          empty.textContent = data.message || "Přehled není k dispozici.";
          overview.appendChild(empty);
          return;
        }
        window.lastOverviewText = data.text || "";
        overviewSince = data.updated_at || "";
        emailItems = mergeItems([], data.items || []);
        renderItems(emailItems);
        updateWorkQueueState();
      } catch (err) {
        overviewStatus.textContent = `Chyba načtení: ${err}`;
      } finally {
        refreshBtn.disabled = false;
      }
    }

    refreshBtn.addEventListener("click", () => loadNewHeaders({newOnly: true}));
    emailDaysInput.addEventListener("change", normalizeDaysInput);
    loadHeadersBtn.addEventListener("click", () => loadNewHeaders({lastSevenDays: true}));
    processEmailsBtn.addEventListener("click", openWorkQueueWindow);
    cockpitBtn.addEventListener("click", () => {
      const cockpit = window.open("/", "SamanthaCockpit", "popup=yes,width=1280,height=880,left=90,top=60");
      if (cockpit) cockpit.focus();
    });
    loadOverview();
  </script>
</body>
</html>
"""


COCKPIT_HTML = """<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Samantha Cockpit</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #eef1f4;
      --ink: #172033;
      --muted: #667085;
      --line: #d6dce5;
      --panel: #ffffff;
      --blue: #1f5fbf;
      --green: #18794e;
      --amber: #9a6700;
      --red: #b42318;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    body { margin: 0; background: var(--bg); color: var(--ink); }
    header { height: 54px; padding: 0 20px; display: flex; align-items: center; justify-content: space-between; background: #182230; color: white; }
    h1 { margin: 0; font-size: 19px; font-weight: 650; letter-spacing: 0; }
    main { padding: 18px 20px 24px; display: grid; gap: 16px; }
    .toolbar { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    button { border: 0; border-radius: 6px; padding: 9px 12px; font: inherit; font-weight: 650; cursor: pointer; background: #e4e9f0; color: #172033; }
    button.primary { background: var(--blue); color: white; }
    button.secondary { background: #dfe5ec; }
    button:disabled { opacity: .6; cursor: wait; }
    .grid { display: grid; grid-template-columns: minmax(320px, 1.15fr) minmax(320px, .85fr); gap: 16px; align-items: start; }
    .today-dashboard { display: grid; grid-template-columns: 1.05fr 1fr 1fr; gap: 12px; align-items: stretch; }
    .dashboard-card { border: 1px solid var(--line); border-radius: 8px; background: var(--panel); overflow: hidden; display: grid; grid-template-rows: auto 1fr; min-height: 168px; }
    .dashboard-card h2 { margin: 0; padding: 12px 14px; font-size: 14px; border-bottom: 1px solid var(--line); background: #f8fafc; }
    .dashboard-body { padding: 13px 14px; display: grid; gap: 10px; align-content: start; }
    .dashboard-metrics { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
    .metric { border: 1px solid #edf0f4; border-radius: 7px; padding: 9px; background: #fbfcfe; min-width: 0; }
    .metric-value { display: block; font-size: 24px; font-weight: 750; line-height: 1; }
    .metric-label { display: block; margin-top: 4px; color: var(--muted); font-size: 12px; line-height: 1.25; }
    .dashboard-list { display: grid; gap: 8px; }
    .dashboard-row { display: grid; grid-template-columns: minmax(92px, auto) minmax(0, 1fr); gap: 10px; align-items: start; font-size: 13px; }
    .dashboard-label { color: var(--muted); }
    .dashboard-value { overflow-wrap: anywhere; }
    .quick-actions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; align-content: start; }
    .quick-actions button { width: 100%; }
    .work-grid { display: grid; grid-template-columns: repeat(3, minmax(220px, 1fr)); gap: 12px; align-items: stretch; }
    .work-card { border: 1px solid var(--line); border-radius: 8px; padding: 12px; background: #fbfcfe; display: grid; gap: 10px; align-content: start; min-height: 170px; }
    .work-card h3 { margin: 0; font-size: 13px; color: #253047; }
    .work-count { font-size: 27px; font-weight: 750; line-height: 1; }
    .work-list { display: grid; gap: 7px; font-size: 12px; color: #344054; }
    .work-item { border-top: 1px solid #edf0f4; padding-top: 7px; overflow-wrap: anywhere; }
    .work-item:first-child { border-top: 0; padding-top: 0; }
    .work-meta { color: var(--muted); font-size: 11px; margin-top: 2px; }
    .search-controls { display: grid; grid-template-columns: minmax(220px, 1fr) auto; gap: 10px; align-items: center; }
    input[type="search"], select { box-sizing: border-box; width: 100%; border: 1px solid var(--line); border-radius: 6px; padding: 10px 11px; font: inherit; background: white; color: var(--ink); }
    .search-results { display: grid; gap: 9px; margin-top: 12px; }
    .search-result { border: 1px solid #edf0f4; border-radius: 8px; padding: 10px; background: #fbfcfe; display: grid; gap: 5px; }
    .search-result-head { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; align-items: start; }
    .search-title { font-weight: 700; overflow-wrap: anywhere; }
    .search-meta { color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
    .search-detail { display: grid; gap: 5px; margin-top: 6px; padding-top: 8px; border-top: 1px solid #edf0f4; }
    .search-snippet { font-size: 12px; line-height: 1.45; color: #263244; overflow-wrap: anywhere; }
    .status-select-row { display: grid; grid-template-columns: 120px minmax(190px, 260px); gap: 10px; align-items: center; margin-top: 4px; }
    .status-select-row label { color: var(--muted); font-size: 12px; }
    .danger-soft { background: #fee2e2; color: #991b1b; }
    .stack { display: grid; gap: 16px; }
    section { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
    section h2 { margin: 0; padding: 12px 14px; font-size: 14px; border-bottom: 1px solid var(--line); background: #f8fafc; }
    .body { padding: 13px 14px; }
    .status-line { color: var(--muted); font-size: 13px; }
    .pills { display: flex; gap: 8px; flex-wrap: wrap; margin: 0 0 12px; }
    .pill { border: 1px solid var(--line); border-radius: 999px; padding: 5px 8px; font-size: 12px; background: #f8fafc; color: #344054; }
    .ok { color: var(--green); }
    .warn { color: var(--amber); }
    .bad { color: var(--red); }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { text-align: left; border-bottom: 1px solid #edf0f4; padding: 8px 6px; vertical-align: top; }
    th { color: #475467; font-size: 12px; font-weight: 650; background: #fbfcfe; }
    td.name { max-width: 360px; overflow-wrap: anywhere; }
    pre { margin: 0; white-space: pre-wrap; font: 12px ui-monospace, SFMono-Regular, Menlo, monospace; line-height: 1.45; color: #263244; }
    .actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
    .message { margin-top: 10px; padding: 9px 10px; border-radius: 6px; background: #eef4ff; color: #1d3b74; font-size: 13px; }
    .hidden { display: none; }
    .modal-backdrop { position: fixed; inset: 0; z-index: 20; background: rgba(15, 23, 42, .42); display: flex; align-items: flex-start; justify-content: center; padding: 72px 18px 24px; }
    .modal-backdrop.hidden { display: none; }
    .modal { width: min(860px, 100%); max-height: calc(100vh - 96px); overflow: auto; background: white; border: 1px solid #cfd7e3; border-radius: 8px; box-shadow: 0 24px 60px rgba(15, 23, 42, .28); }
    .modal-header { display: flex; justify-content: space-between; gap: 12px; align-items: center; padding: 13px 14px; border-bottom: 1px solid var(--line); background: #f8fafc; }
    .modal-header h2 { margin: 0; padding: 0; border: 0; background: transparent; }
    .modal-body { padding: 13px 14px; display: grid; gap: 10px; }
    .app-list { display: grid; gap: 9px; }
    .app-card { border: 1px solid #edf0f4; border-radius: 8px; padding: 11px; background: #fbfcfe; display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 12px; align-items: center; }
    .app-title { font-weight: 750; }
    .app-description { color: #344054; font-size: 13px; line-height: 1.4; margin-top: 3px; }
    .app-kind { color: var(--muted); font-size: 12px; margin-top: 4px; }
    .button-link { display: inline-block; border-radius: 6px; padding: 9px 12px; font-weight: 650; text-decoration: none; background: var(--blue); color: white; white-space: nowrap; }
    @media (max-width: 1050px) { .today-dashboard { grid-template-columns: 1fr; } .work-grid { grid-template-columns: 1fr; } }
    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } .dashboard-metrics { grid-template-columns: 1fr; } .quick-actions { grid-template-columns: 1fr; } .search-controls { grid-template-columns: 1fr; } header { height: auto; padding: 12px 16px; align-items: flex-start; gap: 10px; flex-direction: column; } .app-card { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <header>
    <h1>Samantha Cockpit</h1>
    <div class="toolbar">
      <button class="secondary" id="refreshBtn">Obnovit</button>
      <button class="secondary" id="webAppsBtn">Webové aplikace</button>
      <button class="secondary" id="emailProcessingBtn">Email Processing</button>
      <button class="primary" id="scanDocuBtn">Otevřít ScanDocu</button>
      <button class="secondary" id="scanDocuReviewBtn">Revidovat uložené</button>
      <button class="secondary" id="samanthaChatBtn">Samantha chat</button>
      <button class="secondary" id="codexCliBtn">Codex CLI</button>
      <button class="secondary" id="terminalBtn">Terminál v projektu</button>
    </div>
  </header>
  <main>
    <div class="today-dashboard" aria-label="Dnešní přehled">
      <section class="dashboard-card">
        <h2>Dnes</h2>
        <div class="dashboard-body">
          <div class="dashboard-metrics">
            <div class="metric"><span id="todayNewPdfCount" class="metric-value">0</span><span class="metric-label">nová PDF</span></div>
            <div class="metric"><span id="todayReviewCount" class="metric-value">0</span><span class="metric-label">k revizi</span></div>
            <div class="metric"><span id="todayProblemCount" class="metric-value">0</span><span class="metric-label">problémy</span></div>
          </div>
          <div id="todayHint" class="status-line"></div>
        </div>
      </section>
      <section class="dashboard-card">
        <h2>Stav</h2>
        <div class="dashboard-body dashboard-list">
          <div class="dashboard-row"><span class="dashboard-label">ScanDocu</span><span id="dashboardScanDocu" class="dashboard-value"></span></div>
          <div class="dashboard-row"><span class="dashboard-label">Záloha</span><span id="dashboardBackup" class="dashboard-value"></span></div>
          <div class="dashboard-row"><span class="dashboard-label">Git</span><span id="dashboardGit" class="dashboard-value"></span></div>
        </div>
      </section>
      <section class="dashboard-card">
        <h2>Akce</h2>
        <div class="dashboard-body">
          <div class="quick-actions">
            <button class="primary" id="dashboardProcessBtn">Zpracovat další</button>
            <button class="secondary" id="dashboardReviewBtn">Revidovat další</button>
            <button class="secondary" id="dashboardWebAppsBtn">Webové aplikace</button>
            <button class="secondary" id="dashboardEmailBtn">Email Processing</button>
            <button class="secondary" id="dashboardSamanthaBtn">Samantha chat</button>
            <button class="secondary" id="dashboardCodexBtn">Codex CLI</button>
            <button class="secondary" id="dashboardRefreshBtn">Obnovit stav</button>
          </div>
          <div id="dashboardActionHint" class="status-line"></div>
        </div>
      </section>
    </div>
    <div id="statusLine" class="status-line">Načítám stav...</div>
    <section>
      <h2>Práce s dokumenty</h2>
      <div class="body">
        <div class="work-grid">
          <div class="work-card">
            <h3>Nová PDF ve Downloads za 7 dní</h3>
            <div id="newPdfCount" class="work-count">0</div>
            <div class="actions">
              <button class="primary" id="processNextBtn">Zpracovat další dokument</button>
            </div>
            <div id="newPdfList" class="work-list"></div>
          </div>
          <div class="work-card">
            <h3>Uložené dokumenty k revizi</h3>
            <div id="reviewCount" class="work-count">0</div>
            <div class="actions">
              <button class="secondary" id="reviewNextBtn">Revidovat další uložený</button>
            </div>
            <div id="reviewList" class="work-list"></div>
          </div>
          <div class="work-card">
            <h3>Problémy</h3>
            <div id="problemCount" class="work-count">0</div>
            <div class="status-line">Šifrované / duplicitní / přeskočené</div>
            <div id="problemList" class="work-list"></div>
          </div>
        </div>
      </div>
    </section>
    <section>
      <h2>Najít dokument</h2>
      <div class="body">
        <div class="search-controls">
          <input id="documentSearchInput" type="search" placeholder="Hledat podle názvu, typu, protistrany, věci, tagu nebo textu">
          <button class="primary" id="documentSearchBtn">Hledat</button>
        </div>
        <div id="documentSearchStatus" class="status-line"></div>
        <div id="documentSearchResults" class="search-results"></div>
      </div>
    </section>
    <div class="grid">
      <section>
        <h2>PDF ve Downloads za 7 dní</h2>
        <div class="body">
          <div id="downloadPills" class="pills"></div>
          <table>
            <thead><tr><th>Soubor</th><th>Stav</th><th>Změněno</th></tr></thead>
            <tbody id="downloadsBody"></tbody>
          </table>
        </div>
      </section>
      <div class="stack">
        <section>
          <h2>ScanDocu</h2>
          <div class="body">
            <div id="scanDocuState" class="status-line"></div>
            <div id="actionMessage" class="message hidden"></div>
          </div>
        </section>
        <section>
          <h2>Záloha</h2>
          <div class="body"><pre id="backupText"></pre></div>
        </section>
      </div>
    </div>
    <section>
      <h2>Document Vault</h2>
      <div class="body"><pre id="vaultText"></pre></div>
    </section>
  </main>
  <div id="webAppsModal" class="modal-backdrop hidden" role="dialog" aria-modal="true" aria-labelledby="webAppsTitle">
    <div class="modal">
      <div class="modal-header">
        <h2 id="webAppsTitle">Webové aplikace</h2>
        <button class="secondary" id="webAppsCloseBtn">Zavřít</button>
      </div>
      <div class="modal-body">
        <div id="webAppsStatus" class="status-line">Načítám aplikace...</div>
        <div id="webAppsList" class="app-list"></div>
      </div>
    </div>
  </div>
  <script>
    const statusLine = document.getElementById("statusLine");
    const downloadsBody = document.getElementById("downloadsBody");
    const downloadPills = document.getElementById("downloadPills");
    const backupText = document.getElementById("backupText");
    const vaultText = document.getElementById("vaultText");
    const scanDocuState = document.getElementById("scanDocuState");
    const actionMessage = document.getElementById("actionMessage");
    const refreshBtn = document.getElementById("refreshBtn");
    const scanDocuBtn = document.getElementById("scanDocuBtn");
    const scanDocuReviewBtn = document.getElementById("scanDocuReviewBtn");
    const processNextBtn = document.getElementById("processNextBtn");
    const reviewNextBtn = document.getElementById("reviewNextBtn");
    const samanthaChatBtn = document.getElementById("samanthaChatBtn");
    const codexCliBtn = document.getElementById("codexCliBtn");
    const terminalBtn = document.getElementById("terminalBtn");
    const webAppsBtn = document.getElementById("webAppsBtn");
    const emailProcessingBtn = document.getElementById("emailProcessingBtn");
    const webAppsModal = document.getElementById("webAppsModal");
    const webAppsCloseBtn = document.getElementById("webAppsCloseBtn");
    const webAppsStatus = document.getElementById("webAppsStatus");
    const webAppsList = document.getElementById("webAppsList");
    const todayNewPdfCount = document.getElementById("todayNewPdfCount");
    const todayReviewCount = document.getElementById("todayReviewCount");
    const todayProblemCount = document.getElementById("todayProblemCount");
    const todayHint = document.getElementById("todayHint");
    const dashboardScanDocu = document.getElementById("dashboardScanDocu");
    const dashboardBackup = document.getElementById("dashboardBackup");
    const dashboardGit = document.getElementById("dashboardGit");
    const dashboardProcessBtn = document.getElementById("dashboardProcessBtn");
    const dashboardReviewBtn = document.getElementById("dashboardReviewBtn");
    const dashboardWebAppsBtn = document.getElementById("dashboardWebAppsBtn");
    const dashboardEmailBtn = document.getElementById("dashboardEmailBtn");
    const dashboardSamanthaBtn = document.getElementById("dashboardSamanthaBtn");
    const dashboardCodexBtn = document.getElementById("dashboardCodexBtn");
    const dashboardRefreshBtn = document.getElementById("dashboardRefreshBtn");
    const dashboardActionHint = document.getElementById("dashboardActionHint");
    const newPdfCount = document.getElementById("newPdfCount");
    const reviewCount = document.getElementById("reviewCount");
    const problemCount = document.getElementById("problemCount");
    const newPdfList = document.getElementById("newPdfList");
    const reviewList = document.getElementById("reviewList");
    const problemList = document.getElementById("problemList");
    const documentSearchInput = document.getElementById("documentSearchInput");
    const documentSearchBtn = document.getElementById("documentSearchBtn");
    const documentSearchStatus = document.getElementById("documentSearchStatus");
    const documentSearchResults = document.getElementById("documentSearchResults");
    const readingStatusOptions = [
      ["ok", "OK"],
      ["needs_review", "k revizi"],
      ["unreadable", "nečitelné"],
      ["superseded", "nahrazeno lepší kopií"]
    ];

    function statusClass(value) {
      if (value === "new") return "ok";
      if (value === "already_in_vault" || value === "imported" || value === "skipped") return "warn";
      if (value === "invalid") return "bad";
      return "";
    }

    function showMessage(text) {
      actionMessage.textContent = text || "";
      actionMessage.classList.toggle("hidden", !text);
    }

    async function refresh() {
      refreshBtn.disabled = true;
      statusLine.textContent = "Načítám stav...";
      try {
        const res = await fetch("/api/status");
        const data = await res.json();
        statusLine.textContent = `Aktualizováno: ${data.generated_at || ""}`;
        scanDocuState.innerHTML = data.scandocu && data.scandocu.running
          ? `<span class="ok">ScanDocu běží</span> | ${data.scandocu.url}`
          : `<span class="warn">ScanDocu neběží</span> | ${data.scandocu ? data.scandocu.url : ""}`;
        backupText.textContent = data.backup || "";
        vaultText.textContent = data.vault || "";
        renderDashboard(data);
        renderDocumentWork(data.document_work || {});
        renderDownloads(data.downloads || {});
      } catch (err) {
        statusLine.textContent = `Chyba načtení: ${err}`;
      } finally {
        refreshBtn.disabled = false;
      }
    }

    function renderDocumentWork(work) {
      const summary = work.summary || {};
      const review = work.review || {};
      const newItems = work.new_pdfs || [];
      const reviewItems = review.next_items || [];
      const problemItems = work.problems || [];
      newPdfCount.textContent = String(summary.new_pdf_count || 0);
      reviewCount.textContent = String(summary.review_pending_count || review.pending_count || 0);
      problemCount.textContent = String(summary.problem_count || 0);
      processNextBtn.disabled = newItems.length === 0;
      reviewNextBtn.disabled = reviewItems.length === 0;
      dashboardProcessBtn.disabled = newItems.length === 0;
      dashboardReviewBtn.disabled = reviewItems.length === 0;
      renderWorkList(newPdfList, newItems, (item) => ({
        title: item.name || "",
        meta: `${item.status || ""} | ${item.modified_at || ""}`
      }), "Žádné nové PDF.");
      renderWorkList(reviewList, reviewItems, (item) => ({
        title: item.title || item.document_id || "",
        meta: `${item.domain || "other"} / ${item.document_type || "document"}`
      }), "Žádný uložený dokument nečeká na revizi.");
      renderWorkList(problemList, problemItems, (item) => ({
        title: item.name || "",
        meta: `${item.problem_label || item.status || ""} | ${item.modified_at || ""}`
      }), "Žádné zjevné problémy ve frontě.");
    }

    function renderDashboard(data) {
      const work = data.document_work || {};
      const summary = work.summary || {};
      const review = work.review || {};
      const newCount = summary.new_pdf_count || 0;
      const reviewPending = summary.review_pending_count || review.pending_count || 0;
      const problemTotal = summary.problem_count || 0;
      todayNewPdfCount.textContent = String(newCount);
      todayReviewCount.textContent = String(reviewPending);
      todayProblemCount.textContent = String(problemTotal);
      todayHint.textContent = dashboardTodayHint(newCount, reviewPending, problemTotal);
      dashboardActionHint.textContent = newCount > 0
        ? "Nejbližší akce: zpracovat další PDF přes ScanDocu."
        : reviewPending > 0
          ? "Nejbližší akce: revidovat uložený dokument."
          : "Fronta nevypadá akutně.";

      const scandocu = data.scandocu || {};
      dashboardScanDocu.innerHTML = scandocu.running
        ? `<span class="ok">běží</span> | ${scandocu.url || ""}`
        : `<span class="warn">neběží</span> | ${scandocu.url || ""}`;

      const backupState = classifyBackup(data.backup || "");
      dashboardBackup.innerHTML = `<span class="${backupState.className}">${backupState.label}</span>`;

      const git = data.git || {};
      if (!git.ok) {
        dashboardGit.innerHTML = `<span class="warn">nelze zjistit</span>`;
      } else {
        const gitClass = git.dirty_count ? "warn" : "ok";
        const sync = git.ahead ? " | čeká push" : git.behind ? " | čeká pull" : "";
        dashboardGit.innerHTML = `<span class="${gitClass}">${git.message || ""}</span>${sync}<br>${git.branch || ""}`;
      }
    }

    function dashboardTodayHint(newCount, reviewPending, problemTotal) {
      if (newCount > 0) return `Ve frontě je ${newCount} nových PDF.`;
      if (reviewPending > 0) return `Nová PDF nejsou, ale ${reviewPending} uložených dokumentů čeká na revizi.`;
      if (problemTotal > 0) return `Fronta nemá nové PDF, ale má ${problemTotal} položek k ruční kontrole.`;
      return "Dokumentová fronta je klidná.";
    }

    function classifyBackup(text) {
      if (!text) return {label: "neznámý stav", className: "warn"};
      const lower = text.toLocaleLowerCase("cs-CZ");
      if (lower.includes("starsi nez 3 dny") || lower.includes("starší než 3 dny") || lower.includes("chybi") || lower.includes("chybí")) {
        return {label: "potřebuje zálohu", className: "warn"};
      }
      if (lower.includes("posledni uspesna") || lower.includes("poslední úspěšná")) {
        return {label: "záloha evidovaná", className: "ok"};
      }
      return {label: "zkontrolovat", className: "warn"};
    }

    function renderWorkList(target, items, mapItem, emptyText) {
      target.innerHTML = "";
      if (!items || items.length === 0) {
        const empty = document.createElement("div");
        empty.className = "status-line";
        empty.textContent = emptyText;
        target.appendChild(empty);
        return;
      }
      items.slice(0, 5).forEach((item) => {
        const mapped = mapItem(item);
        const row = document.createElement("div");
        row.className = "work-item";
        const title = document.createElement("div");
        title.textContent = mapped.title || "";
        const meta = document.createElement("div");
        meta.className = "work-meta";
        meta.textContent = mapped.meta || "";
        row.appendChild(title);
        row.appendChild(meta);
        target.appendChild(row);
      });
    }

    function renderDownloads(downloads) {
      downloadPills.innerHTML = "";
      const counts = downloads.counts || {};
      Object.keys(counts).sort().forEach((key) => {
        const pill = document.createElement("span");
        pill.className = `pill ${statusClass(key)}`;
        pill.textContent = `${key}: ${counts[key]}`;
        downloadPills.appendChild(pill);
      });
      downloadsBody.innerHTML = "";
      (downloads.items || []).slice(0, 20).forEach((item) => {
        const row = document.createElement("tr");
        row.innerHTML = `<td class="name"></td><td></td><td></td>`;
        row.children[0].textContent = item.name || "";
        row.children[1].textContent = item.status || "";
        row.children[1].className = statusClass(item.status || "");
        row.children[2].textContent = item.modified_at || "";
        downloadsBody.appendChild(row);
      });
      if (!downloads.items || downloads.items.length === 0) {
        const row = document.createElement("tr");
        row.innerHTML = `<td colspan="3">Žádné PDF nenalezeno.</td>`;
        downloadsBody.appendChild(row);
      }
    }

    async function postAction(url, button) {
      button.disabled = true;
      showMessage("Provádím akci...");
      try {
        const res = await fetch(url, {method: "POST"});
        const data = await res.json();
        showMessage(data.message || data.error || "Hotovo.");
        await refresh();
      } catch (err) {
        showMessage(`Chyba: ${err}`);
      } finally {
        button.disabled = false;
      }
    }

    async function searchDocuments() {
      const query = documentSearchInput.value.trim();
      documentSearchResults.innerHTML = "";
      if (query.length < 2) {
        documentSearchStatus.textContent = "Zadej aspoň dvě písmena nebo číslice.";
        return;
      }
      documentSearchBtn.disabled = true;
      documentSearchStatus.textContent = "Hledám v indexu dokumentů...";
      try {
        const res = await fetch(`/api/documents/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        documentSearchStatus.textContent = data.message || "";
        renderDocumentSearchResults(data.results || []);
      } catch (err) {
        documentSearchStatus.textContent = `Chyba hledání: ${err}`;
      } finally {
        documentSearchBtn.disabled = false;
      }
    }

    function renderDocumentSearchResults(results) {
      documentSearchResults.innerHTML = "";
      if (!results || results.length === 0) {
        return;
      }
      results.forEach((item) => {
        const documentRef = item.document_ref || item.document_id;
        const card = document.createElement("div");
        card.className = "search-result";
        const head = document.createElement("div");
        head.className = "search-result-head";
        const summary = document.createElement("div");
        const title = document.createElement("div");
        title.className = "search-title";
        title.textContent = item.title || item.original_filename || item.document_id || "Dokument bez názvu";
        const meta = document.createElement("div");
        meta.className = "search-meta";
        meta.textContent = `Čtení: ${item.reading_status_label || "k revizi"} | ${item.domain || "other"} / ${item.document_type || "document"} | ${item.counterparty || "protistrana nezjištěna"} | ${item.related_asset || "věc nezjištěna"}`;
        const toggle = document.createElement("button");
        toggle.className = "secondary";
        toggle.type = "button";
        toggle.textContent = "Rozbalit";
        const detail = document.createElement("div");
        detail.className = "search-detail hidden";
        const id = document.createElement("div");
        id.className = "search-meta";
        id.textContent = `ID: ${item.document_id || ""}`;
        const path = document.createElement("div");
        path.className = "search-meta";
        path.textContent = `Cesta: ${item.stored_path || ""}`;
        const lifecycle = document.createElement("div");
        lifecycle.className = "search-meta";
        lifecycle.textContent = `Stav: ${item.lifecycle_status || "active"}`;
        const readingStatus = document.createElement("div");
        readingStatus.className = "search-meta";
        readingStatus.textContent = `Stav čtení: ${item.reading_status_label || "k revizi"}`;
        const statusRow = document.createElement("div");
        statusRow.className = "status-select-row";
        const statusLabel = document.createElement("label");
        statusLabel.textContent = "Stav čtení";
        const statusSelect = document.createElement("select");
        readingStatusOptions.forEach(([value, label]) => {
          const option = document.createElement("option");
          option.value = value;
          option.textContent = label;
          option.selected = value === (item.reading_status || "needs_review");
          statusSelect.appendChild(option);
        });
        statusSelect.addEventListener("change", () => setDocumentReadingStatus(documentRef, statusSelect.value));
        statusRow.appendChild(statusLabel);
        statusRow.appendChild(statusSelect);
        const snippet = document.createElement("div");
        snippet.className = "search-snippet";
        snippet.textContent = item.snippet || "";
        const actions = document.createElement("div");
        actions.className = "actions";
        const printBtn = document.createElement("button");
        printBtn.className = "secondary";
        printBtn.type = "button";
        printBtn.textContent = "Tisknout";
        const archiveBtn = document.createElement("button");
        archiveBtn.className = "secondary";
        archiveBtn.type = "button";
        archiveBtn.textContent = "Archivovat";
        const trashBtn = document.createElement("button");
        trashBtn.className = "danger-soft";
        trashBtn.type = "button";
        trashBtn.textContent = "Do koše";
        printBtn.addEventListener("click", () => printDocument(documentRef));
        archiveBtn.addEventListener("click", () => moveDocumentLifecycle(documentRef, "archive"));
        trashBtn.addEventListener("click", () => moveDocumentLifecycle(documentRef, "trash"));
        actions.appendChild(printBtn);
        actions.appendChild(archiveBtn);
        actions.appendChild(trashBtn);
        summary.appendChild(title);
        summary.appendChild(meta);
        head.appendChild(summary);
        head.appendChild(toggle);
        detail.appendChild(id);
        detail.appendChild(path);
        detail.appendChild(lifecycle);
        detail.appendChild(readingStatus);
        detail.appendChild(statusRow);
        detail.appendChild(snippet);
        detail.appendChild(actions);
        toggle.addEventListener("click", () => {
          const isHidden = detail.classList.toggle("hidden");
          toggle.textContent = isHidden ? "Rozbalit" : "Sbalit";
        });
        card.appendChild(head);
        card.appendChild(detail);
        documentSearchResults.appendChild(card);
      });
    }

    async function postJson(url, payload) {
      const res = await fetch(url, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload || {})
      });
      return await res.json();
    }

    async function printDocument(documentId) {
      if (!documentId) return;
      documentSearchStatus.textContent = "Připravuji kopii k tisku...";
      const prepared = await postJson("/api/documents/print/prepare", {document_id: documentId});
      if (!prepared.ok) {
        documentSearchStatus.textContent = prepared.message || "Příprava tisku selhala.";
        return;
      }
      const confirmation = `Potvrzuji, vytiskni print job ${prepared.print_job_id}.`;
      const shouldPrint = window.confirm(`Dokument je připraven k tisku.\n\nPrint job: ${prepared.print_job_id}\n\nOdeslat na tiskárnu?`);
      if (!shouldPrint) {
        documentSearchStatus.textContent = "Tisk je připravený, ale nebyl odeslán na tiskárnu.";
        return;
      }
      documentSearchStatus.textContent = "Odesílám tisk na macOS tiskovou frontu...";
      const printed = await postJson("/api/documents/print/run", {
        print_job_id: prepared.print_job_id,
        confirmation_text: confirmation
      });
      documentSearchStatus.textContent = printed.message || "Tisk dokončen.";
    }

    async function moveDocumentLifecycle(documentId, target) {
      if (!documentId) return;
      const archive = target === "archive";
      const confirmation = archive
        ? `Potvrzuji, archivuj dokument ${documentId}.`
        : `Potvrzuji, přesuň dokument ${documentId} do koše.`;
      const label = archive ? "archivu" : "koše";
      const ok = window.confirm(`Přesunout dokument do ${label}?\n\n${documentId}\n\nSoubor nebude trvale smazán.`);
      if (!ok) return;
      documentSearchStatus.textContent = archive ? "Archivuji dokument..." : "Přesouvám dokument do koše...";
      const result = await postJson("/api/documents/lifecycle", {
        document_id: documentId,
        target,
        confirmation_text: confirmation
      });
      documentSearchStatus.textContent = result.message || "Akce dokončena.";
      if (result.ok && documentSearchInput.value.trim().length >= 2) {
        await searchDocuments();
        await refresh();
      }
    }

    async function setDocumentReadingStatus(documentId, readingStatus) {
      if (!documentId) return;
      documentSearchStatus.textContent = "Ukládám stav čtení dokumentu...";
      const result = await postJson("/api/documents/reading-status", {
        document_id: documentId,
        reading_status: readingStatus
      });
      documentSearchStatus.textContent = result.message || "Stav uložen.";
      if (result.ok) {
        await refresh();
        if (documentSearchInput.value.trim().length >= 2) {
          await searchDocuments();
        }
      }
    }

    async function openScanDocu(reviewMode = false) {
      const scanDocuWindow = window.open(
        "about:blank",
        reviewMode ? "SamanthaScanDocuReview" : "SamanthaScanDocu",
        "popup=yes,width=1380,height=920,left=80,top=60"
      );
      const activeButton = reviewMode ? scanDocuReviewBtn : scanDocuBtn;
      activeButton.disabled = true;
      showMessage(reviewMode ? "Spouštím ScanDocu Review..." : "Spouštím ScanDocu...");
      try {
        const res = await fetch("/api/scandocu/open", {method: "POST"});
        const data = await res.json();
        showMessage(data.message || data.error || "Hotovo.");
        if (data.ok && data.url) {
          const targetUrl = reviewMode ? `${data.url}/?mode=review` : data.url;
          if (scanDocuWindow) {
            scanDocuWindow.location.href = targetUrl;
            scanDocuWindow.focus();
          } else {
            showMessage(`${data.message || "ScanDocu běží."} Popup okno bylo blokováno, otevři ${targetUrl}`);
          }
        } else if (scanDocuWindow) {
          scanDocuWindow.close();
        }
        await refresh();
      } catch (err) {
        if (scanDocuWindow) {
          scanDocuWindow.close();
        }
        showMessage(`Chyba: ${err}`);
      } finally {
        activeButton.disabled = false;
      }
    }

    async function openWebAppsModal() {
      webAppsModal.classList.remove("hidden");
      webAppsStatus.textContent = "Načítám aplikace...";
      webAppsList.innerHTML = "";
      try {
        const res = await fetch("/api/web-apps");
        const data = await res.json();
        renderWebApps(data.apps || []);
        webAppsStatus.textContent = data.apps && data.apps.length
          ? `${data.apps.length} aplikací k dispozici.`
          : "Žádná aplikace není v katalogu.";
      } catch (err) {
        webAppsStatus.textContent = `Chyba načtení aplikací: ${err}`;
      }
    }

    function closeWebAppsModal() {
      webAppsModal.classList.add("hidden");
    }

    function renderWebApps(apps) {
      webAppsList.innerHTML = "";
      apps.forEach((app) => {
        const card = document.createElement("div");
        card.className = "app-card";
        const text = document.createElement("div");
        const title = document.createElement("div");
        title.className = "app-title";
        title.textContent = app.title || "";
        const description = document.createElement("div");
        description.className = "app-description";
        description.textContent = app.description || "";
        const kind = document.createElement("div");
        kind.className = "app-kind";
        kind.textContent = app.kind || "";
        const link = document.createElement("button");
        link.className = "button-link";
        link.type = "button";
        link.textContent = "Otevřít";
        link.addEventListener("click", () => openWebApp(app));
        text.appendChild(title);
        text.appendChild(description);
        text.appendChild(kind);
        card.appendChild(text);
        card.appendChild(link);
        webAppsList.appendChild(card);
      });
    }

    function openWebApp(app) {
      if (!app || !app.url) return;
      if (app.id === "scandocu") {
        openScanDocu(false);
        return;
      }
      const targetUrl = new URL(app.url, window.location.href).href;
      const windowName = `SamanthaWebApp_${String(app.id || "app").replace(/[^A-Za-z0-9_]+/g, "_")}`;
      const appWindow = window.open(
        "about:blank",
        windowName,
        "popup=yes,width=1280,height=880,left=120,top=70"
      );
      if (appWindow) {
        appWindow.location.href = targetUrl;
        appWindow.focus();
      } else {
        showMessage(`Popup okno bylo blokováno, otevři ${targetUrl}`);
      }
    }

    function openEmailProcessing() {
      const emailWindow = window.open(
        "/email-processing/",
        "SamanthaEmailProcessing",
        "popup=yes,width=1280,height=880,left=120,top=70"
      );
      if (emailWindow) {
        emailWindow.focus();
      } else {
        showMessage("Popup okno bylo blokováno, otevři /email-processing/");
      }
    }

    refreshBtn.addEventListener("click", refresh);
    dashboardRefreshBtn.addEventListener("click", refresh);
    dashboardProcessBtn.addEventListener("click", () => openScanDocu(false));
    dashboardReviewBtn.addEventListener("click", () => openScanDocu(true));
    dashboardWebAppsBtn.addEventListener("click", openWebAppsModal);
    dashboardEmailBtn.addEventListener("click", openEmailProcessing);
    dashboardSamanthaBtn.addEventListener("click", () => postAction("/api/samantha/open", dashboardSamanthaBtn));
    dashboardCodexBtn.addEventListener("click", () => postAction("/api/codex/open", dashboardCodexBtn));
    webAppsBtn.addEventListener("click", openWebAppsModal);
    emailProcessingBtn.addEventListener("click", openEmailProcessing);
    webAppsCloseBtn.addEventListener("click", closeWebAppsModal);
    webAppsModal.addEventListener("click", (event) => {
      if (event.target === webAppsModal) {
        closeWebAppsModal();
      }
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !webAppsModal.classList.contains("hidden")) {
        closeWebAppsModal();
      }
    });
    scanDocuBtn.addEventListener("click", () => openScanDocu(false));
    scanDocuReviewBtn.addEventListener("click", () => openScanDocu(true));
    samanthaChatBtn.addEventListener("click", () => postAction("/api/samantha/open", samanthaChatBtn));
    codexCliBtn.addEventListener("click", () => postAction("/api/codex/open", codexCliBtn));
    processNextBtn.addEventListener("click", () => openScanDocu(false));
    reviewNextBtn.addEventListener("click", () => openScanDocu(true));
    documentSearchBtn.addEventListener("click", searchDocuments);
    documentSearchInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        searchDocuments();
      }
    });
    terminalBtn.addEventListener("click", () => postAction("/api/terminal/open", terminalBtn));
    refresh();
  </script>
</body>
</html>
"""


def run_cockpit_server(host: str = "127.0.0.1", port: int = COCKPIT_PORT) -> None:
    CockpitServer(host=host, port=port).serve()
