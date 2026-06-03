from __future__ import annotations

import json
import hashlib
import re
import shutil
import subprocess
import tempfile
import time
from collections.abc import Callable
from datetime import date, datetime, timezone
from email import message_from_bytes
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
    apply_document_import_file,
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
    safe_filename,
    safe_text,
    safe_slug,
    sanitize_output,
    tokenize,
    write_json,
    write_jsonl,
)
from app.email.activity_state import DEFAULT_EMAIL_ACTIVITY_STATE_PATH, record_email_archive_completed
from app.email.archive_models import EmailArchiveSource
from app.email.archive_service import DEFAULT_EMAIL_ARCHIVE_DIR, save_email_archive
from app.email.config import EmailConfigError
from app.email.icloud_provider import EmailProviderError, ICloudReadOnlyEmailProvider
from app.email.models import EmailAttachmentMeta, EmailHeader, EmailMessage
from app.email.seznam_provider import SeznamEmailProviderError, SeznamReadOnlyEmailProvider
from app.reminders.query_tools import mark_reminder_done_text
from app.reminders.store import DEFAULT_REMINDERS_PATH, load_reminders_store


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
EMAIL_WORK_QUEUE_ACTIONS_FILE = EMAIL_SESSION_HANDOFF_DIR / "email_work_queue_actions.jsonl"
EMAIL_ATTACHMENT_PREVIEW_DIR = Path("/private/tmp/samantha_email_attachment_preview")
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


def email_processing_completed_lookup_keys(actions_path: Path = EMAIL_WORK_QUEUE_ACTIONS_FILE) -> set[str]:
    keys: set[str] = set()
    completed_statuses = {"saved", "skipped", "trashed", "purged"}
    for action in read_jsonl(actions_path):
        raw_items = action.get("items", [])
        if not isinstance(raw_items, list):
            continue
        for raw_item in raw_items:
            if not isinstance(raw_item, dict):
                continue
            status = str(raw_item.get("status", "")).strip()
            if status not in completed_statuses:
                continue
            item_id = str(raw_item.get("item_id", "")).strip()
            if item_id:
                keys.add(item_id)
            computed_id = email_processing_item_id(
                "",
                str(raw_item.get("provider", "")),
                str(raw_item.get("folder", "INBOX")),
                str(raw_item.get("uid", "")),
                "",
                "",
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


def email_processing_pending_work_items(
    path: Path = EMAIL_PROCESSING_DECISIONS_FILE,
) -> dict[str, Any]:
    decisions = read_email_processing_decisions(path)
    items: list[dict[str, Any]] = []
    for item_id, decision in decisions.items():
        action = str(decision.get("action", ""))
        if action not in {"process", "trash_requested"}:
            continue
        raw_item = decision.get("item", {})
        if not isinstance(raw_item, dict):
            continue
        item = dict(raw_item)
        item["id"] = str(item.get("id") or item_id)
        item["action"] = action
        item["is_new_header"] = False
        if "legacy_id" not in item:
            item["legacy_id"] = email_processing_legacy_item_id(
                str(item.get("category", "")),
                str(item.get("provider", "")),
                str(item.get("folder", "")),
                str(item.get("uid", "")),
                str(item.get("date", "")),
                str(item.get("subject", "")),
            )
        items.append(item)

    items.sort(key=lambda item: email_header_timestamp(str(item.get("date", ""))), reverse=True)
    return {
        "ok": True,
        "message": f"Načteno rozpracovaných e-mailů: {len(items)}.",
        "items": items,
        "count": len(items),
    }


def new_email_headers_overview(
    limit_per_source: int = 50,
    since: str = "",
    days: int = 0,
    known_ids: set[str] | None = None,
    decisions_path: Path = EMAIL_PROCESSING_DECISIONS_FILE,
    actions_path: Path = EMAIL_WORK_QUEUE_ACTIONS_FILE,
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
    completed_keys = email_processing_completed_lookup_keys(actions_path)
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
            if (
                item_id in known
                or legacy_id in known
                or item_id in decided_keys
                or legacy_id in decided_keys
                or item_id in completed_keys
                or legacy_id in completed_keys
            ):
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
        "skipped_completed_count": len(completed_keys),
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


def email_attachment_to_processing_detail(attachment: EmailAttachmentMeta) -> dict[str, Any]:
    return {
        "filename": attachment.filename or "(bez názvu)",
        "content_type": attachment.content_type or "application/octet-stream",
        "size_bytes": attachment.size_bytes,
        "part_id": attachment.part_id,
        "content_id": attachment.content_id,
        "disposition": attachment.disposition,
    }


def email_message_to_processing_detail(message: EmailMessage) -> dict[str, Any]:
    header = message.header
    return {
        "provider": header.source,
        "folder": header.folder or "INBOX",
        "uid": str(header.internal_id),
        "date": header.date,
        "sender": header.sender,
        "subject": header.subject or "(bez předmětu)",
        "body_text": message.body_text,
        "truncated": message.truncated,
        "attachments": [email_attachment_to_processing_detail(attachment) for attachment in message.attachments],
    }


def read_email_processing_message_detail(
    *,
    provider: str,
    folder: str,
    uid: str,
    max_chars: int = 12_000,
    icloud_provider_factory: Callable[[], object] | None = None,
    seznam_provider_factory: Callable[[], object] | None = None,
) -> dict[str, Any]:
    safe_provider = provider.strip().casefold()
    safe_folder = folder.strip() or "INBOX"
    safe_uid = uid.strip()
    safe_max_chars = min(max(500, max_chars), 20_000)
    if not safe_uid:
        return {"ok": False, "message": "Chybí UID e-mailu."}

    try:
        if safe_provider == "icloud":
            provider_client = (icloud_provider_factory or ICloudReadOnlyEmailProvider)()
            message = provider_client.read_message_by_uid(  # type: ignore[attr-defined]
                uid=safe_uid,
                folder=safe_folder,
                max_chars=safe_max_chars,
            )
        elif safe_provider == "seznam":
            provider_client = (seznam_provider_factory or SeznamReadOnlyEmailProvider)()
            if hasattr(provider_client, "read_message_by_uid_from_folder"):
                message = provider_client.read_message_by_uid_from_folder(  # type: ignore[attr-defined]
                    uid=safe_uid,
                    folder=safe_folder,
                    max_chars=safe_max_chars,
                )
            else:
                message = provider_client.read_message_by_uid(uid=safe_uid, max_chars=safe_max_chars)  # type: ignore[attr-defined]
        else:
            return {"ok": False, "message": "Neznámý e-mailový zdroj."}
    except EmailConfigError:
        return {"ok": False, "message": "Chybí lokální konfigurace e-mailu."}
    except (EmailProviderError, SeznamEmailProviderError) as exc:
        return {"ok": False, "message": str(exc) or "E-mail se nepodařilo načíst."}

    return {
        "ok": True,
        "message": "E-mail načten read-only.",
        "email": email_message_to_processing_detail(message),
    }


def process_email_work_queue_batch(
    *,
    items: list[dict[str, Any]],
    trash_confirmation_text: str = "",
    archive_directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
    documents_dir: Path = DEFAULT_DOCUMENTS_DIR,
    decisions_path: Path = EMAIL_PROCESSING_DECISIONS_FILE,
    actions_path: Path = EMAIL_WORK_QUEUE_ACTIONS_FILE,
    activity_state_path: Path = DEFAULT_EMAIL_ACTIVITY_STATE_PATH,
    icloud_provider_factory: Callable[[], object] | None = None,
    seznam_provider_factory: Callable[[], object] | None = None,
) -> dict[str, Any]:
    if not items:
        return {"ok": False, "message": "Dávka je prázdná.", "items": []}

    processed: list[dict[str, Any]] = []
    has_error = False
    trash_batch_size = sum(
        1
        for item in items
        if isinstance(item, dict)
        and safe_text(str(item.get("queueDecision") or item.get("action") or "")).strip() == "trash_requested"
    )
    for raw_item in items:
        if not isinstance(raw_item, dict):
            has_error = True
            processed.append({"ok": False, "message": "Neplatná položka dávky."})
            continue
        result = process_email_work_queue_item(
            item=raw_item,
            trash_confirmation_text=trash_confirmation_text,
            archive_directory=archive_directory,
            documents_dir=documents_dir,
            decisions_path=decisions_path,
            activity_state_path=activity_state_path,
            icloud_provider_factory=icloud_provider_factory,
            seznam_provider_factory=seznam_provider_factory,
            trash_batch_size=trash_batch_size,
        )
        processed.append(result)
        has_error = has_error or not bool(result.get("ok"))

    summary = {
        "saved": sum(1 for item in processed if item.get("status") == "saved"),
        "skipped": sum(1 for item in processed if item.get("status") == "skipped"),
        "trash_pending": sum(1 for item in processed if item.get("status") == "trash_pending"),
        "trashed": sum(1 for item in processed if item.get("status") == "trashed"),
        "errors": sum(1 for item in processed if not item.get("ok")),
        "attachments_imported": sum(int(item.get("attachments_imported", 0) or 0) for item in processed),
    }
    append_jsonl(
        actions_path,
        {
            "action": "process_email_work_queue_batch",
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "summary": summary,
            "items": [
                {
                    "item_id": str(item.get("item_id", "")),
                    "provider": str(item.get("provider", "")),
                    "folder": str(item.get("folder", "")),
                    "uid": str(item.get("uid", "")),
                    "status": str(item.get("status", "")),
                    "archive_id": str(item.get("archive_id", "")),
                    "attachments_imported": int(item.get("attachments_imported", 0) or 0),
                }
                for item in processed
            ],
            "do_not_commit": True,
        },
    )
    message = (
        "Dávka zpracována s chybami."
        if has_error
        else "Dávka zpracována. Archivované e-maily a PDF přílohy jsou uložené lokálně."
    )
    return {"ok": not has_error, "message": message, "summary": summary, "items": processed}


def process_email_work_queue_purge_trash_batch(
    *,
    items: list[dict[str, Any]],
    confirmed: bool = False,
    confirmation_text: str = "",
    actions_path: Path = EMAIL_WORK_QUEUE_ACTIONS_FILE,
    icloud_provider_factory: Callable[[], object] | None = None,
    seznam_provider_factory: Callable[[], object] | None = None,
) -> dict[str, Any]:
    if not items:
        return {"ok": False, "message": "Dávka pro trvalé smazání je prázdná.", "items": []}

    safe_items = [item for item in items if isinstance(item, dict)]
    if not confirmed and confirmation_text.strip() != "yes":
        return {
            "ok": True,
            "message": "Trvalé smazání čeká na potvrzení tlačítkem.",
            "summary": {"purge_pending": len(safe_items), "purged": 0, "errors": 0},
            "items": [
                {
                    "item_id": safe_text(str(item.get("id") or item.get("item_id") or "")),
                    "provider": safe_text(str(item.get("provider", ""))),
                    "uid": safe_text(str(item.get("uid", ""))),
                    "status": "purge_pending",
                    "ok": True,
                }
                for item in safe_items
            ],
        }

    processed: list[dict[str, Any]] = []
    has_error = False
    for item in safe_items:
        result = process_email_work_queue_purge_trash_item(
            item=item,
            icloud_provider_factory=icloud_provider_factory,
            seznam_provider_factory=seznam_provider_factory,
        )
        processed.append(result)
        has_error = has_error or not bool(result.get("ok"))

    summary = {
        "purged": sum(1 for item in processed if item.get("status") == "purged"),
        "purge_pending": sum(1 for item in processed if item.get("status") == "purge_pending"),
        "errors": sum(1 for item in processed if not item.get("ok")),
    }
    append_jsonl(
        actions_path,
        {
            "action": "purge_email_work_queue_trash_batch",
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "summary": summary,
            "items": [
                {
                    "item_id": str(item.get("item_id", "")),
                    "provider": str(item.get("provider", "")),
                    "trash_folder": str(item.get("trash_folder", "")),
                    "trash_uid": str(item.get("trash_uid", "")),
                    "status": str(item.get("status", "")),
                }
                for item in processed
            ],
            "do_not_commit": True,
        },
    )
    message = "Trvalé smazání skončilo s chybami." if has_error else "E-maily v koši byly trvale smazány."
    return {"ok": not has_error, "message": message, "summary": summary, "items": processed}


def email_processing_message_id_ref(value: object) -> str:
    normalized = " ".join(str(value or "").split())
    if len(normalized) > 300:
        return ""
    return normalized


def process_email_work_queue_purge_trash_item(
    *,
    item: dict[str, Any],
    icloud_provider_factory: Callable[[], object] | None,
    seznam_provider_factory: Callable[[], object] | None,
) -> dict[str, Any]:
    base = {
        "item_id": safe_text(str(item.get("id") or item.get("item_id") or "")),
        "provider": safe_text(str(item.get("provider", ""))),
        "uid": safe_text(str(item.get("uid", ""))),
        "folder": safe_text(str(item.get("folder", ""))),
        "trash_folder": safe_text(str(item.get("trash_folder", ""))),
        "trash_uid": safe_text(str(item.get("trash_uid", ""))),
        "message_id": email_processing_message_id_ref(item.get("message_id", "")),
    }
    if not base["provider"]:
        return {**base, "ok": False, "status": "error", "message": "Položce chybí provider."}
    if not base["trash_uid"] and not base["message_id"]:
        return {
            **base,
            "ok": False,
            "status": "purge_pending",
            "message": "Chybí UID v koši i Message-ID; nelze bezpečně trvale smazat.",
        }
    try:
        safe_provider = str(base["provider"]).strip().casefold()
        if safe_provider == "icloud":
            client = (icloud_provider_factory or ICloudReadOnlyEmailProvider)()
        elif safe_provider == "seznam":
            client = (seznam_provider_factory or SeznamReadOnlyEmailProvider)()
        else:
            raise EmailProviderError("Neznámý e-mailový zdroj.")
        purge = getattr(client, "permanently_delete_message_from_trash", None)
        if not callable(purge):
            return {
                **base,
                "ok": False,
                "status": "purge_pending",
                "message": "Provider zatím neumí trvalé smazání z koše.",
            }
        purge(  # type: ignore[misc]
            trash_uid=str(base["trash_uid"]),
            message_id=str(base["message_id"]),
            trash_folder=str(base["trash_folder"]),
        )
    except (EmailConfigError, EmailProviderError, SeznamEmailProviderError) as exc:
        return {**base, "ok": False, "status": "purge_pending", "message": str(exc)}
    return {**base, "ok": True, "status": "purged", "message": "E-mail byl trvale smazán z koše."}


def process_email_work_queue_item(
    *,
    item: dict[str, Any],
    trash_confirmation_text: str,
    archive_directory: Path,
    documents_dir: Path,
    decisions_path: Path,
    activity_state_path: Path,
    icloud_provider_factory: Callable[[], object] | None,
    seznam_provider_factory: Callable[[], object] | None,
    trash_batch_size: int = 1,
) -> dict[str, Any]:
    item_id = safe_text(str(item.get("id", ""))).strip()
    provider = safe_text(str(item.get("provider", ""))).strip()
    folder = safe_text(str(item.get("folder", "INBOX"))).strip() or "INBOX"
    uid = safe_text(str(item.get("uid", ""))).strip()
    decision = safe_text(str(item.get("queueDecision") or item.get("action") or "")).strip()
    save_attachment_ids = {
        safe_text(str(part_id)).strip()
        for part_id in item.get("saveAttachments", [])
        if safe_text(str(part_id)).strip()
    }
    base = {
        "item_id": item_id,
        "provider": provider,
        "folder": folder,
        "uid": uid,
    }
    if not uid or not provider:
        return {**base, "ok": False, "status": "error", "message": "Položce chybí provider nebo UID."}
    if decision == "skip":
        clear_email_processing_decision(item_id=item_id, path=decisions_path)
        return {**base, "ok": True, "status": "skipped", "message": "E-mail byl uzavřen bez uložení."}
    if decision == "trash_requested":
        return process_email_work_queue_trash_item(
            base=base,
            trash_confirmation_text=trash_confirmation_text,
            decisions_path=decisions_path,
            icloud_provider_factory=icloud_provider_factory,
            seznam_provider_factory=seznam_provider_factory,
            trash_batch_size=trash_batch_size,
        )
    if decision != "save":
        return {**base, "ok": False, "status": "error", "message": "Položka nemá platné dávkové rozhodnutí."}

    try:
        source = read_email_archive_source_for_processing(
            provider=provider,
            folder=folder,
            uid=uid,
            icloud_provider_factory=icloud_provider_factory,
            seznam_provider_factory=seznam_provider_factory,
        )
    except (EmailConfigError, EmailProviderError, SeznamEmailProviderError) as exc:
        return {**base, "ok": False, "status": "error", "message": str(exc)}

    archive_result = save_email_archive(source, directory=archive_directory)
    if archive_result.created:
        record_email_archive_completed(path=activity_state_path)

    attachment_results = import_selected_email_pdf_attachments(
        source=source,
        selected_part_ids=save_attachment_ids,
        documents_dir=documents_dir,
        category=safe_text(str(item.get("category", ""))),
    )
    clear_email_processing_decision(item_id=item_id, path=decisions_path)
    ok_attachments = [result for result in attachment_results if result.get("ok")]
    failed_attachments = [result for result in attachment_results if not result.get("ok")]
    return {
        **base,
        "ok": not failed_attachments,
        "status": "saved",
        "archive_id": archive_result.archive_id,
        "archive_created": archive_result.created,
        "archive_path": str(relative_to_project(archive_result.path)),
        "attachments_imported": len(ok_attachments),
        "attachments": attachment_results,
        "message": (
            f"E-mail uložen do EmailArchiveVault; PDF příloh uloženo: {len(ok_attachments)}."
            if not failed_attachments
            else f"E-mail uložen, ale {len(failed_attachments)} příloh se nepodařilo uložit."
        ),
    }


def read_email_archive_source_for_processing(
    *,
    provider: str,
    folder: str,
    uid: str,
    icloud_provider_factory: Callable[[], object] | None,
    seznam_provider_factory: Callable[[], object] | None,
) -> EmailArchiveSource:
    safe_provider = provider.strip().casefold()
    safe_uid = uid.strip()
    safe_folder = folder.strip() or "INBOX"
    if safe_provider == "icloud":
        client = (icloud_provider_factory or ICloudReadOnlyEmailProvider)()
    elif safe_provider == "seznam":
        client = (seznam_provider_factory or SeznamReadOnlyEmailProvider)()
    else:
        raise EmailProviderError("Neznámý e-mailový zdroj.")
    source = client.read_archive_source_by_uid(uid=safe_uid, folder=safe_folder, max_chars=200_000)  # type: ignore[attr-defined]
    if not isinstance(source, EmailArchiveSource):
        raise EmailProviderError("Provider vrátil neplatný archivní zdroj.")
    return source


def preview_email_work_queue_attachment_action(
    *,
    provider: str,
    folder: str,
    uid: str,
    part_id: str,
    preview_dir: Path = EMAIL_ATTACHMENT_PREVIEW_DIR,
    opener: Callable[[list[str]], object] | None = None,
    icloud_provider_factory: Callable[[], object] | None = None,
    seznam_provider_factory: Callable[[], object] | None = None,
) -> dict[str, Any]:
    safe_part_id = safe_text(part_id).strip()
    if not safe_part_id:
        return {"ok": False, "message": "Chybí ID přílohy pro náhled."}
    try:
        source = read_email_archive_source_for_processing(
            provider=provider,
            folder=folder,
            uid=uid,
            icloud_provider_factory=icloud_provider_factory,
            seznam_provider_factory=seznam_provider_factory,
        )
    except (EmailConfigError, EmailProviderError, SeznamEmailProviderError) as exc:
        return {"ok": False, "message": str(exc)}
    if source.original_eml is None:
        return {"ok": False, "message": "Archivní zdroj neobsahuje původní EML, přílohu nelze otevřít."}

    message = message_from_bytes(source.original_eml)
    meta_by_part_id = {attachment.part_id: attachment for attachment in source.attachments}
    for index, part in enumerate(message.walk() if message.is_multipart() else [message]):
        current_part_id = str(index)
        if current_part_id != safe_part_id:
            continue
        meta = meta_by_part_id.get(current_part_id)
        filename = safe_filename((meta.filename if meta else part.get_filename()) or f"attachment-{current_part_id}.pdf")
        content_type = (meta.content_type if meta else part.get_content_type()) or ""
        if content_type.casefold() != "application/pdf" and not filename.casefold().endswith(".pdf"):
            return {"ok": False, "part_id": safe_part_id, "filename": safe_text(filename), "message": "Náhled je zatím povolený jen pro PDF přílohy."}
        payload = part.get_payload(decode=True)
        if not isinstance(payload, bytes) or not payload:
            return {"ok": False, "part_id": safe_part_id, "filename": safe_text(filename), "message": "Příloha neobsahuje čitelná data."}

        preview_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        preview_name = f"{stamp}_{safe_slug(provider, default='email', limit=24)}_{safe_slug(uid, default='uid', limit=40)}_{filename}"
        preview_path = next_available_path(preview_dir / preview_name)
        preview_path.write_bytes(payload)
        runner = opener or (lambda command: subprocess.run(command, check=False))
        runner(["/usr/bin/open", str(preview_path)])
        return {
            "ok": True,
            "message": "PDF příloha otevřena jako dočasný náhled; nebyla uložena do document vaultu.",
            "part_id": safe_part_id,
            "filename": safe_text(filename),
            "preview_path": str(preview_path),
        }

    return {"ok": False, "part_id": safe_part_id, "message": "Vybraná příloha nebyla v e-mailu nalezena."}


def import_selected_email_pdf_attachments(
    *,
    source: EmailArchiveSource,
    selected_part_ids: set[str],
    documents_dir: Path,
    category: str,
) -> list[dict[str, Any]]:
    if not selected_part_ids:
        return []
    if source.original_eml is None:
        return [
            {
                "ok": False,
                "part_id": part_id,
                "message": "Archivní zdroj neobsahuje původní EML, přílohu nelze uložit.",
            }
            for part_id in sorted(selected_part_ids)
        ]

    message = message_from_bytes(source.original_eml)
    meta_by_part_id = {attachment.part_id: attachment for attachment in source.attachments}
    imported: list[dict[str, Any]] = []
    found_part_ids: set[str] = set()
    with tempfile.TemporaryDirectory(prefix="samantha_email_pdf_", dir="/private/tmp") as temp_dir:
        temp_root = Path(temp_dir)
        for index, part in enumerate(message.walk() if message.is_multipart() else [message]):
            part_id = str(index)
            if part_id not in selected_part_ids:
                continue
            found_part_ids.add(part_id)
            meta = meta_by_part_id.get(part_id)
            filename = safe_filename((meta.filename if meta else part.get_filename()) or f"attachment-{part_id}.pdf")
            content_type = (meta.content_type if meta else part.get_content_type()) or ""
            if content_type.casefold() != "application/pdf" and not filename.casefold().endswith(".pdf"):
                imported.append(
                    {
                        "ok": False,
                        "part_id": part_id,
                        "filename": safe_text(filename),
                        "message": "Příloha není PDF; pro dávkový import byla přeskočena.",
                    }
                )
                continue
            payload = part.get_payload(decode=True)
            if not isinstance(payload, bytes) or not payload:
                imported.append(
                    {
                        "ok": False,
                        "part_id": part_id,
                        "filename": safe_text(filename),
                        "message": "Příloha neobsahuje čitelná data.",
                    }
                )
                continue
            temp_path = temp_root / filename
            temp_path.write_bytes(payload)
            try:
                result = apply_document_import_file(
                    source_path=str(temp_path),
                    target_domain=email_processing_category_to_document_domain(category),
                    document_type="email-attachment-pdf",
                    counterparty=source.sender,
                    tags=f"email,email-attachment,pdf,{source.provider}",
                    case_id=f"email-{source.provider}-{source.uid}",
                    document_title=f"E-mail UID {source.uid} příloha {filename}",
                    vault_dir=documents_dir,
                )
            except ValueError as exc:
                imported.append(
                    {
                        "ok": False,
                        "part_id": part_id,
                        "filename": safe_text(filename),
                        "message": str(exc),
                    }
                )
                continue
            imported.append(
                {
                    "ok": True,
                    "part_id": part_id,
                    "filename": safe_text(filename),
                    "document_id": result.document_id,
                    "document_ref": document_reference(result.document_id),
                    "created": result.created,
                    "stored_path": str(relative_to_project(result.destination)),
                    "message": result.message,
                }
            )

    for missing_part_id in sorted(selected_part_ids - found_part_ids):
        imported.append(
            {
                "ok": False,
                "part_id": missing_part_id,
                "message": "Vybraná příloha nebyla v e-mailu nalezena.",
            }
        )
    return imported


def email_processing_category_to_document_domain(category: str) -> str:
    normalized = category.casefold()
    if "pojist" in normalized or "smlouv" in normalized:
        return "insurance"
    if "úřad" in normalized or "urad" in normalized or "dan" in normalized:
        return "tax"
    return "other"


def process_email_work_queue_trash_item(
    *,
    base: dict[str, Any],
    trash_confirmation_text: str,
    decisions_path: Path,
    icloud_provider_factory: Callable[[], object] | None,
    seznam_provider_factory: Callable[[], object] | None,
    trash_batch_size: int = 1,
) -> dict[str, Any]:
    safe_batch_size = max(1, int(trash_batch_size or 1))
    if safe_batch_size == 1:
        noun = "e-mail označený"
    elif safe_batch_size in {2, 3, 4}:
        noun = "e-maily označené"
    else:
        noun = "e-mailů označených"
    required = f"Potvrzuji, přesuň {safe_batch_size} {noun} ke smazání do koše."
    legacy_required = f"Potvrzuji, přesuň e-mail UID {base['uid']} do koše."
    entered = trash_confirmation_text.strip()
    if entered not in {required, legacy_required}:
        return {
            **base,
            "ok": True,
            "status": "trash_pending",
            "required_confirmation": required,
            "message": f"Koš čeká na přesné potvrzení: {required}",
        }
    try:
        safe_provider = str(base["provider"]).strip().casefold()
        if safe_provider == "icloud":
            client = (icloud_provider_factory or ICloudReadOnlyEmailProvider)()
        elif safe_provider == "seznam":
            client = (seznam_provider_factory or SeznamReadOnlyEmailProvider)()
        else:
            raise EmailProviderError("Neznámý e-mailový zdroj.")
        move_to_trash = getattr(client, "move_message_to_trash", None)
        if not callable(move_to_trash):
            return {
                **base,
                "ok": False,
                "status": "trash_pending",
                "required_confirmation": required,
                "message": "Provider zatím neumí bezpečný přesun do koše; položka zůstává čekající.",
            }
        trash_result = move_to_trash(uid=str(base["uid"]), folder=str(base["folder"]))  # type: ignore[misc]
    except (EmailConfigError, EmailProviderError, SeznamEmailProviderError) as exc:
        return {**base, "ok": False, "status": "trash_pending", "required_confirmation": required, "message": str(exc)}
    clear_email_processing_decision(item_id=str(base["item_id"]), path=decisions_path)
    trash_meta = trash_result if isinstance(trash_result, dict) else {}
    return {
        **base,
        "ok": True,
        "status": "trashed",
        "trash_folder": safe_text(str(trash_meta.get("trash_folder", ""))),
        "trash_uid": safe_text(str(trash_meta.get("trash_uid", ""))),
        "message_id": email_processing_message_id_ref(trash_meta.get("message_id", "")),
        "message": "E-mail byl přesunut do koše.",
    }


def clear_email_processing_decision(*, item_id: str, path: Path) -> None:
    if not item_id:
        return
    decisions = read_email_processing_decisions(path)
    if item_id not in decisions:
        return
    decisions.pop(item_id, None)
    write_json(path, {"decisions": decisions})


def cockpit_status() -> dict[str, Any]:
    downloads = safe_downloads_status()
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "downloads": downloads,
        "document_work": document_work_status(downloads=downloads),
        "backup": format_backup_activity_reminder(),
        "vault": document_vault_status_summary(),
        "reminders": reminders_status(),
        "scandocu": probe_scandocu(),
        "git": git_status_summary(),
    }


def reminders_status(path: Path = DEFAULT_REMINDERS_PATH, today: date | None = None) -> dict[str, Any]:
    today_date = today or date.today()
    groups: dict[str, list[dict[str, Any]]] = {
        "overdue": [],
        "today": [],
        "soon": [],
        "later": [],
        "undated": [],
    }
    try:
        raw_reminders = load_reminders_store(path)["reminders"]
    except (OSError, ValueError) as exc:
        return {"ok": False, "message": str(exc), "groups": groups, "counts": {}}

    open_count = 0
    open_raw_reminders: list[dict[str, Any]] = []
    for raw in raw_reminders:
        if not isinstance(raw, dict):
            continue
        if safe_text(str(raw.get("status", ""))).casefold() != "open":
            continue
        open_count += 1
        open_raw_reminders.append(raw)
        item = reminder_status_item(raw=raw, today=today_date)
        due_date = item.get("due_date")
        if not due_date:
            groups["undated"].append(item)
        elif item["days_until"] < 0:
            groups["overdue"].append(item)
        elif item["days_until"] == 0:
            groups["today"].append(item)
        elif item["days_until"] <= 14:
            groups["soon"].append(item)
        else:
            groups["later"].append(item)

    for items in groups.values():
        items.sort(key=lambda item: (item.get("due_date") or "9999-12-31", item.get("id") or ""))

    active_count = len(groups["overdue"]) + len(groups["today"]) + len(groups["soon"])
    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "today": today_date.isoformat(),
        "groups": groups,
        "counts": {
            "open": open_count,
            "active": active_count,
            "conflicts": len(reminder_conflicts(open_raw_reminders)),
            "overdue": len(groups["overdue"]),
            "today": len(groups["today"]),
            "soon": len(groups["soon"]),
            "later": len(groups["later"]),
            "undated": len(groups["undated"]),
        },
        "conflicts": reminder_conflicts(open_raw_reminders),
        "startup_window_days": 14,
        "message": (
            "Pri startu Samanthy se ukazuji prosle, dnesni a do 14 dnu. "
            "Cockpit zobrazuje vsechny otevrene pripominky."
        ),
    }


def reminder_conflicts(raw_reminders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for raw in raw_reminders:
        if not reminder_is_payment_related(raw):
            continue
        asset = normalize_reminder_asset(str(raw.get("related_asset", "")))
        coverage_start = safe_text(str(raw.get("coverage_start", ""))).strip()
        if not asset or not coverage_start:
            continue
        groups.setdefault((asset, coverage_start), []).append(raw)

    conflicts: list[dict[str, Any]] = []
    for (asset, coverage_start), items in sorted(groups.items()):
        if len(items) < 2:
            continue
        conflicts.append(
            {
                "asset": asset,
                "coverage_start": coverage_start,
                "severity": "high",
                "message": (
                    "Pozor: více otevřených platebních připomínek pro stejné vozidlo "
                    "a stejný začátek krytí. Nekonat platbu bez porovnání nabídek."
                ),
                "items": [
                    {
                        "reminder_ref": reminder_reference(str(item.get("id", ""))),
                        "id": safe_text(str(item.get("id", "")))[:180],
                        "title": safe_text(str(item.get("title", "")))[:180],
                        "due_date": safe_text(str(item.get("due_date", "")))[:40],
                        "priority": safe_text(str(item.get("priority", "")))[:32],
                        "source_type": safe_text(str((item.get("source") or {}).get("type", "")))[:64]
                        if isinstance(item.get("source"), dict)
                        else "",
                        "conflict_note": safe_text(str(item.get("conflict_note", "")))[:500],
                    }
                    for item in items
                ],
            }
        )
    return conflicts


def reminder_is_payment_related(raw: dict[str, Any]) -> bool:
    text = " ".join(
        [
            str(raw.get("id", "")),
            str(raw.get("title", "")),
            str(raw.get("notes", "")),
            str((raw.get("source") or {}).get("type", "")) if isinstance(raw.get("source"), dict) else "",
        ]
    ).casefold()
    return any(term in text for term in ("zaplat", "platb", "pojist", "payment_due", "splatnost"))


def normalize_reminder_asset(value: str) -> str:
    text = safe_text(value).strip()
    if not text:
        return ""
    return " ".join(text.upper().replace("/", " ").split())


def mark_reminder_done_action(
    reminder_id: str,
    path: Path = DEFAULT_REMINDERS_PATH,
) -> dict[str, Any]:
    clean_id = reminder_id.strip()
    if not clean_id:
        return {"ok": False, "message": "Chybí id připomínky.", "reminders": reminders_status(path=path)}
    reminder = find_reminder_record(reminder_id=clean_id, path=path)
    if reminder is None:
        return {"ok": False, "message": "Připomínka nebyla nalezena.", "reminders": reminders_status(path=path)}
    resolved_id = str(reminder.get("id", ""))

    message = mark_reminder_done_text(
        reminder_id=resolved_id,
        user_confirmed=True,
        confirmation_text=f"Potvrzuji, označ {resolved_id} jako splněno.",
        path=path,
    )
    ok = message.startswith("Oznaceno jako hotove:")
    return {
        "ok": ok,
        "reminder_id": safe_text(resolved_id),
        "reminder_ref": reminder_reference(resolved_id),
        "message": safe_text(message),
        "reminders": reminders_status(path=path),
    }


def reminder_source_detail_action(
    reminder_id: str,
    reminders_path: Path = DEFAULT_REMINDERS_PATH,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    icloud_provider_factory: Callable[[], object] | None = None,
    seznam_provider_factory: Callable[[], object] | None = None,
) -> dict[str, Any]:
    reminder = find_reminder_record(reminder_id=reminder_id, path=reminders_path)
    if reminder is None:
        return {"ok": False, "message": "Připomínka nebyla nalezena."}

    source = reminder.get("source")
    if not isinstance(source, dict):
        source = {}
    source_type = safe_text(str(source.get("type", ""))).casefold()
    base = {
        "reminder": reminder_status_item(reminder, today=date.today()),
        "source": {
            "type": safe_text(str(source.get("type", "")))[:64],
            "uid": safe_text(str(source.get("uid", "")))[:180],
            "date": safe_text(str(source.get("date", "")))[:120],
            "sender": safe_text(str(source.get("sender", "")))[:180],
        },
        "links": safe_reminder_links(reminder.get("links")),
        "notes": sanitize_output(str(reminder.get("notes", "")))[:2000],
    }
    if source_type == "email":
        return reminder_email_source_detail(
            base=base,
            source=source,
            icloud_provider_factory=icloud_provider_factory,
            seznam_provider_factory=seznam_provider_factory,
        )
    if source_type == "private_document":
        return reminder_document_source_detail(base=base, source=source, vault_dir=vault_dir)
    return {
        **base,
        "ok": True,
        "kind": source_type or "source",
        "message": "Zdroj připomínky nemá přímý e-mail ani PDF vazbu.",
    }


def find_reminder_record(reminder_id: str, path: Path = DEFAULT_REMINDERS_PATH) -> dict[str, Any] | None:
    clean_id = reminder_id.strip()
    if not clean_id:
        return None
    for reminder in load_reminders_store(path)["reminders"]:
        if not isinstance(reminder, dict):
            continue
        stored_id = str(reminder.get("id", ""))
        if stored_id == clean_id or reminder_reference(stored_id) == clean_id:
            return reminder
    return None


def safe_reminder_links(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    links: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        links.append(
            {
                "domain": safe_text(str(item.get("domain", "")))[:180],
                "count": safe_text(str(item.get("count", "")))[:24],
            }
        )
    return links


def reminder_email_source_detail(
    *,
    base: dict[str, Any],
    source: dict[str, Any],
    icloud_provider_factory: Callable[[], object] | None = None,
    seznam_provider_factory: Callable[[], object] | None = None,
) -> dict[str, Any]:
    uid = str(source.get("uid", "")).strip()
    if not uid:
        return {**base, "ok": False, "kind": "email", "message": "Zdrojový e-mail nemá UID."}

    folder = str(source.get("folder", "")).strip() or "INBOX"
    preferred = safe_text(str(source.get("provider", ""))).casefold()
    providers = [preferred] if preferred in {"icloud", "seznam"} else ["icloud", "seznam"]
    attempts: list[str] = []
    for provider in providers:
        detail = read_email_processing_message_detail(
            provider=provider,
            folder=folder,
            uid=uid,
            max_chars=10_000,
            icloud_provider_factory=icloud_provider_factory,
            seznam_provider_factory=seznam_provider_factory,
        )
        if detail.get("ok"):
            return {
                **base,
                "ok": True,
                "kind": "email",
                "message": f"E-mail načten read-only ze zdroje {provider}.",
                "email": detail.get("email", {}),
            }
        attempts.append(f"{provider}: {safe_text(str(detail.get('message', 'neúspěch')))}")

    return {
        **base,
        "ok": False,
        "kind": "email",
        "message": "Zdrojový e-mail se nepodařilo načíst read-only. " + " | ".join(attempts),
    }


def reminder_document_source_detail(
    *,
    base: dict[str, Any],
    source: dict[str, Any],
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> dict[str, Any]:
    source_uid = str(source.get("uid", "")).strip()
    row = find_document_record_for_source(source_uid=source_uid, vault_dir=vault_dir)
    if row is None:
        return {
            **base,
            "ok": False,
            "kind": "document",
            "message": "Související dokument nebyl nalezen ve vault indexu.",
        }

    document_id = str(row.get("document_id", ""))
    text_by_id = {
        str(item.get("document_id", "")): str(item.get("text", ""))
        for item in read_jsonl(vault_dir / "index" / "text_index.jsonl")
    }
    text = text_by_id.get(document_id, "")
    terms = [term.casefold() for term in tokenize(" ".join([document_id, source_uid, str(row.get("title", ""))]))]
    snippet = build_snippet(text, terms) if text and terms else text[:900]
    if not snippet.strip():
        snippet = "Text zatím není k dispozici; detail je podle metadat."

    reading_status = effective_document_reading_status(row, text_chars=len(text))
    stored_path = str(row.get("stored_path", ""))
    return {
        **base,
        "ok": True,
        "kind": "document",
        "message": "Dokument nalezen ve vaultu.",
        "document": {
            "document_id": safe_text(document_id),
            "document_ref": document_reference(document_id),
            "title": safe_text(str(row.get("title") or row.get("original_filename") or document_id)),
            "original_filename": safe_text(str(row.get("original_filename", ""))),
            "domain": safe_text(str(row.get("domain", ""))),
            "document_type": safe_text(str(row.get("document_type", ""))),
            "counterparty": safe_text(str(row.get("counterparty", ""))),
            "related_asset": safe_text(str(row.get("related_asset", ""))),
            "stored_path": safe_text(stored_path),
            "reading_status": reading_status,
            "reading_status_label": READING_STATUS_LABELS[reading_status],
            "snippet": sanitize_output(snippet),
            "due_contexts": reminder_document_due_contexts(document_id=document_id, vault_dir=vault_dir),
            "can_open_pdf": document_stored_path_is_openable_pdf(stored_path, vault_dir=vault_dir),
        },
    }


def find_document_record_for_source(source_uid: str, vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> dict[str, Any] | None:
    clean_uid = source_uid.strip()
    documents = read_jsonl(vault_dir / "index" / "documents_index.jsonl")
    row_index = find_document_row_index_by_reference(documents, clean_uid)
    if row_index is not None:
        return documents[row_index]

    if clean_uid:
        search = search_document_index(clean_uid, vault_dir=vault_dir, limit=1)
        results = search.get("results") if search.get("ok") else []
        if isinstance(results, list) and results:
            found_id = str(results[0].get("document_id", ""))
            found_index = find_document_row_index_by_reference(documents, found_id)
            if found_index is not None:
                return documents[found_index]
    return None


def reminder_document_due_contexts(document_id: str, vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> list[dict[str, Any]]:
    contexts: list[dict[str, Any]] = []
    for item in read_jsonl(vault_dir / "index" / "due_dates.jsonl"):
        if str(item.get("document_id", "")) != document_id:
            continue
        contexts.append(
            {
                "date": safe_text(str(item.get("date", "")))[:40],
                "type": safe_text(str(item.get("type", "")))[:80],
                "confidence": safe_text(str(item.get("confidence", "")))[:40],
                "context": sanitize_output(str(item.get("context", "")))[:700],
            }
        )
        if len(contexts) >= 4:
            break
    return contexts


def document_stored_path_is_openable_pdf(stored_path: str, vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> bool:
    try:
        root = vault_dir.resolve(strict=True)
        target = (PROJECT_ROOT / stored_path).resolve(strict=True)
    except (OSError, RuntimeError):
        return False
    return target.is_file() and target.suffix.casefold() == ".pdf" and (target == root or root in target.parents)


def open_document_pdf_action(
    document_id: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    opener: Callable[[list[str]], object] | None = None,
) -> dict[str, Any]:
    documents = read_jsonl(vault_dir / "index" / "documents_index.jsonl")
    row_index = find_document_row_index_by_reference(documents, document_id)
    if row_index is None:
        return {"ok": False, "message": "Dokument nebyl nalezen ve vault indexu."}
    row = documents[row_index]
    stored_path = str(row.get("stored_path", ""))
    if not document_stored_path_is_openable_pdf(stored_path, vault_dir=vault_dir):
        return {"ok": False, "message": "PDF není dostupné nebo neleží ve vaultu."}

    target = (PROJECT_ROOT / stored_path).resolve(strict=True)
    runner = opener or (lambda command: subprocess.run(command, check=False))
    runner(["/usr/bin/open", str(target)])
    return {
        "ok": True,
        "message": "PDF otevřeno v lokální aplikaci.",
        "document_id": safe_text(str(row.get("document_id", ""))),
        "document_ref": document_reference(str(row.get("document_id", ""))),
    }


def reminder_status_item(raw: dict[str, Any], today: date) -> dict[str, Any]:
    due_date = parse_reminder_due_date(raw.get("due_date"))
    source = raw.get("source")
    if not isinstance(source, dict):
        source = {}
    reminder_id = str(raw.get("id", ""))
    return {
        "reminder_ref": reminder_reference(reminder_id),
        "id": safe_text(reminder_id)[:180],
        "title": safe_text(str(raw.get("title", "")))[:180],
        "due_date": due_date.isoformat() if due_date else "",
        "days_until": (due_date - today).days if due_date else 999999,
        "priority": safe_text(str(raw.get("priority", "")))[:32],
        "status": safe_text(str(raw.get("status", "")))[:32],
        "source_type": safe_text(str(source.get("type", "")))[:64],
        "related_asset": safe_text(str(raw.get("related_asset", "")))[:180],
        "coverage_start": safe_text(str(raw.get("coverage_start", "")))[:40],
        "conflict_note": safe_text(str(raw.get("conflict_note", "")))[:500],
    }


def parse_reminder_due_date(value: Any) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


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


def reminder_reference(reminder_id: str) -> str:
    digest = hashlib.sha256(reminder_id.encode("utf-8")).hexdigest()[:16]
    return f"remref-{digest}"


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
                if parsed.path == "/api/reminders":
                    self.respond_json(reminders_status())
                    return
                if parsed.path == "/api/web-apps":
                    self.respond_json(web_apps_catalog())
                    return
                if parsed.path == "/api/email-processing/overview":
                    self.respond_json(empty_email_processing_overview())
                    return
                if parsed.path == "/api/email-processing/pending-work":
                    self.respond_json(email_processing_pending_work_items())
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
                if parsed.path == "/api/reminders/done":
                    payload = self.read_json()
                    self.respond_json(mark_reminder_done_action(reminder_id=str(payload.get("reminder_id", ""))))
                    return
                if parsed.path == "/api/reminders/source":
                    payload = self.read_json()
                    self.respond_json(reminder_source_detail_action(reminder_id=str(payload.get("reminder_id", ""))))
                    return
                if parsed.path == "/api/documents/open":
                    payload = self.read_json()
                    self.respond_json(open_document_pdf_action(document_id=str(payload.get("document_id", ""))))
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
                if parsed.path == "/api/email-processing/read-message":
                    payload = self.read_json()
                    raw_max_chars = payload.get("max_chars", 12000)
                    try:
                        max_chars = int(raw_max_chars)
                    except (TypeError, ValueError):
                        max_chars = 12000
                    self.respond_json(
                        read_email_processing_message_detail(
                            provider=str(payload.get("provider", "")),
                            folder=str(payload.get("folder", "INBOX")),
                            uid=str(payload.get("uid", "")),
                            max_chars=max_chars,
                        )
                    )
                    return
                if parsed.path == "/api/email-processing/preview-attachment":
                    payload = self.read_json()
                    self.respond_json(
                        preview_email_work_queue_attachment_action(
                            provider=str(payload.get("provider", "")),
                            folder=str(payload.get("folder", "INBOX")),
                            uid=str(payload.get("uid", "")),
                            part_id=str(payload.get("part_id", "")),
                        )
                    )
                    return
                if parsed.path == "/api/email-processing/process-batch":
                    payload = self.read_json()
                    raw_items = payload.get("items", [])
                    items = raw_items if isinstance(raw_items, list) else []
                    self.respond_json(
                        process_email_work_queue_batch(
                            items=[item for item in items if isinstance(item, dict)],
                            trash_confirmation_text=str(payload.get("trash_confirmation_text", "")),
                        )
                    )
                    return
                if parsed.path == "/api/email-processing/purge-trash":
                    payload = self.read_json()
                    raw_items = payload.get("items", [])
                    items = raw_items if isinstance(raw_items, list) else []
                    self.respond_json(
                        process_email_work_queue_purge_trash_batch(
                            items=[item for item in items if isinstance(item, dict)],
                            confirmed=bool(payload.get("confirmed")),
                            confirmation_text=str(payload.get("confirmation_text", "")),
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
      <button class="secondary" id="refreshBtn" disabled>Obnovit nové</button>
      <span class="days-control">
        <span>Za posledních:</span>
        <input id="emailDaysInput" type="number" min="1" max="14" step="1" value="7" inputmode="numeric" aria-label="Počet dní">
        <span>dní</span>
      </span>
      <button class="primary" id="loadHeadersBtn">Načti emaily</button>
      <button class="secondary" id="loadPendingBtn">Načti rozpracované</button>
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
          <div><strong>Obnovit nové:</strong> aktivuje se až po načtení seznamu a doplní jen e-maily novější než nejnovější viditelný e-mail.</div>
          <div><strong>Načti emaily:</strong> doplní jen e-maily ve zvoleném rozsahu 1-14 dní, které ještě nejsou v aktuálním seznamu ani nemají uložené rozhodnutí.</div>
          <div><strong>Načti rozpracované:</strong> vrátí do seznamu e-maily, které už mají status `Zpracovat` nebo `Koš` a čekají na Work Queue.</div>
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
    const loadPendingBtn = document.getElementById("loadPendingBtn");
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
      updateRefreshButtonState();
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

    function updateRefreshButtonState() {
      const canRefresh = Boolean(newestItemIso());
      refreshBtn.disabled = !canRefresh;
      refreshBtn.title = canRefresh
        ? "Doplní jen e-maily novější než nejnovější viditelný e-mail."
        : "Nejdřív použij Načti emaily.";
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

    function initializeWorkQueueWindow(queue, queueItems) {
      const queueDoc = queue.document;
      const queueList = queueDoc.getElementById("queueList");
      const detailPane = queueDoc.getElementById("detailPane");
      const queueStatus = queueDoc.getElementById("queueStatus");
      const queueProcessCount = queueDoc.getElementById("queueProcessCount");
      const queueTrashCount = queueDoc.getElementById("queueTrashCount");
      const queuePurgeCount = queueDoc.getElementById("queuePurgeCount");
      const batchBtn = queueDoc.getElementById("batchBtn");
      const trashBatchBtn = queueDoc.getElementById("trashBatchBtn");
      const purgeTrashBtn = queueDoc.getElementById("purgeTrashBtn");
      let selectedId = queueItems.length ? queueItems[0].id : "";
      let permanentDeleteItems = [];
      let recentImportedAttachments = [];

      function decisionLabel(item) {
        if (item.detailLoading) return "načítám detail...";
        if (item.detailLoaded) return item.queueDecision ? decisionLabel({...item, detailLoaded: false}) : "detail načten";
        if (item.queueDecision === "save") return "uložit";
        if (item.queueDecision === "skip") return "neukládat";
        if (item.queueDecision === "trash_requested") return "koš připraven";
        return "čeká na rozhodnutí";
      }

      function currentItem() {
        return queueItems.find((item) => item.id === selectedId) || queueItems[0] || null;
      }

      function updateSummaryCounts() {
        const workItems = queueItems.filter((item) => item.queueDecision !== "trash_requested");
        const trashItems = queueItems.filter((item) => item.queueDecision === "trash_requested");
        if (queueProcessCount) queueProcessCount.textContent = String(workItems.length);
        if (queueTrashCount) queueTrashCount.textContent = String(trashItems.length);
        if (queuePurgeCount) queuePurgeCount.textContent = String(permanentDeleteItems.length);
      }

      function updateBatchState() {
        const decided = queueItems.filter((item) => Boolean(item.queueDecision)).length;
        const workItems = queueItems.filter((item) => item.queueDecision !== "trash_requested");
        const workReady = workItems.filter((item) => Boolean(item.queueDecision)).length;
        const trashItems = queueItems.filter((item) => item.queueDecision === "trash_requested");
        updateSummaryCounts();
        batchBtn.disabled = !workItems.length || workReady < workItems.length;
        trashBatchBtn.disabled = !trashItems.length;
        purgeTrashBtn.disabled = !permanentDeleteItems.length;
        queueStatus.textContent = queueItems.length
          ? `Rozhodnuto ${decided}/${queueItems.length}. Koš: ${trashItems.length}. Ukládání a mazání se spouští odděleně.`
          : "Fronta je prázdná.";
      }

      function renderQueueList() {
        if (!queueItems.length) {
          queueList.innerHTML = '<div class="empty">Fronta je prázdná.</div>';
          detailPane.innerHTML = '<div class="empty">Žádný e-mail ke zpracování.</div>';
          batchBtn.disabled = true;
          trashBatchBtn.disabled = true;
          purgeTrashBtn.disabled = !permanentDeleteItems.length;
          updateSummaryCounts();
          return;
        }
        queueList.innerHTML = queueItems.map((item) => {
          const active = item.id === selectedId ? " active" : "";
          const done = item.queueDecision || item.detailLoaded ? " done" : "";
          const loading = item.detailLoading ? " loading" : "";
          return '<button type="button" class="item' + active + '" data-id="' + escapeHtml(item.id) + '">' +
            '<span class="subject">' + escapeHtml(item.subject || "(bez předmětu)") + '</span>' +
            '<span class="meta">' + escapeHtml(itemMeta(item)) + '</span>' +
            (item.reason ? '<span class="reason">Důvod: ' + escapeHtml(item.reason) + '</span>' : "") +
            '<span class="status' + done + loading + '">' + escapeHtml(decisionLabel(item)) + '</span>' +
            '</button>';
        }).join("");
        queueList.querySelectorAll(".item").forEach((button) => {
          button.addEventListener("click", () => selectItem(button.dataset.id || ""));
        });
        updateBatchState();
      }

      function renderAttachmentRows(item, attachments) {
        if (!attachments.length) return '<div class="empty">Bez příloh.</div>';
        return attachments.map((attachment, index) => {
          const partId = attachment.part_id || String(index);
          const checked = (item.saveAttachments || []).includes(partId) ? " checked" : "";
          const size = attachment.size_bytes === null || attachment.size_bytes === undefined
            ? "velikost neznámá"
            : Math.round(Number(attachment.size_bytes) / 1024) + " kB";
          return '<div class="attachment-row" data-part-id="' + escapeHtml(partId) + '">' +
            '<div><strong>' + escapeHtml(attachment.filename || "(bez názvu)") + '</strong></div>' +
            '<div class="meta">' + escapeHtml(attachment.content_type || "") + " | " + escapeHtml(size) + '</div>' +
            '<div class="attachment-tools">' +
            '<label><input type="checkbox" class="attachment-save" data-part-id="' + escapeHtml(partId) + '"' + checked + '> Uložit</label>' +
            '<button type="button" class="secondary attachment-preview" data-part-id="' + escapeHtml(partId) + '">Náhled PDF</button>' +
            '<button type="button" class="secondary attachment-toggle">Metadata</button>' +
            '</div>' +
            '<div class="meta hidden attachment-detail">part_id: ' + escapeHtml(partId) + '<br>dispozice: ' + escapeHtml(attachment.disposition || "") + '<br>Náhled PDF otevře dočasnou kopii; trvalé uložení do vaultu proběhne až po zaškrtnutí Uložit a zpracování dávky.</div>' +
            '</div>';
        }).join("");
      }

      function renderRecentImportedAttachments() {
        if (!recentImportedAttachments.length) return "";
        return '<div><strong>Právě uložené přílohy</strong></div>' +
          '<div class="attachments">' +
          recentImportedAttachments.map((attachment) => {
            const documentId = attachment.document_ref || attachment.document_id || "";
            return '<div class="attachment-row">' +
              '<div><strong>' + escapeHtml(attachment.filename || "uložená příloha") + '</strong></div>' +
              '<div class="meta">Dokument: ' + escapeHtml(documentId) + '</div>' +
              '<div class="attachment-tools">' +
              '<button type="button" class="primary attachment-open" data-document-id="' + escapeHtml(documentId) + '">Otevřít uložené PDF</button>' +
              '</div>' +
              '</div>';
          }).join("") +
          '</div>';
      }

      function bindAttachmentOpenButtons() {
        detailPane.querySelectorAll(".attachment-open").forEach((button) => {
          button.addEventListener("click", async () => {
            const documentId = button.dataset.documentId || "";
            if (!documentId) return;
            button.disabled = true;
            queueStatus.textContent = "Otevírám uložené PDF z document vaultu.";
            try {
              const res = await fetch("/api/documents/open", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({document_id: documentId})
              });
              const data = await res.json();
              queueStatus.textContent = data.message || (data.ok ? "PDF otevřeno." : "PDF se nepodařilo otevřít.");
            } catch (err) {
              queueStatus.textContent = "Chyba otevření PDF: " + err;
            } finally {
              button.disabled = false;
            }
          });
        });
      }

      function bindAttachmentPreviewButtons(item) {
        detailPane.querySelectorAll(".attachment-preview").forEach((button) => {
          button.addEventListener("click", async () => {
            const partId = button.dataset.partId || "";
            if (!partId) return;
            button.disabled = true;
            queueStatus.textContent = "Otevírám dočasný náhled PDF přílohy. Příloha se neukládá do vaultu.";
            try {
              const res = await fetch("/api/email-processing/preview-attachment", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                  provider: item.provider,
                  folder: item.folder || "INBOX",
                  uid: item.uid,
                  part_id: partId
                })
              });
              const data = await res.json();
              queueStatus.textContent = data.message || (data.ok ? "Náhled otevřen." : "Náhled se nepodařilo otevřít.");
            } catch (err) {
              queueStatus.textContent = "Chyba náhledu přílohy: " + err;
            } finally {
              button.disabled = false;
            }
          });
        });
      }

      function collectImportedAttachments(results, items) {
        const itemById = new Map((items || []).map((item) => [item.id, item]));
        const imported = [];
        (results || []).forEach((result) => {
          const sourceItem = itemById.get(result.item_id) || {};
          (result.attachments || []).forEach((attachment) => {
            if (!attachment || !attachment.ok || !(attachment.document_ref || attachment.document_id)) return;
            imported.push({
              ...attachment,
              subject: sourceItem.subject || ""
            });
          });
        });
        return imported;
      }

      function setQueueDecision(item, decision) {
        item.queueDecision = decision;
        if (decision === "skip") item.saveAttachments = [];
        renderQueueList();
        renderDetail(item);
      }

      function renderLoadingDetail(item) {
        detailPane.innerHTML =
          '<div class="detail-head">' +
            '<div>' +
              '<div class="subject">' + escapeHtml(item.subject || "(bez předmětu)") + '</div>' +
              '<div class="meta">' + escapeHtml(itemMeta(item)) + '</div>' +
            '</div>' +
            '<div class="status loading">načítám detail</div>' +
          '</div>' +
          '<div class="loading-box"><span class="mini-spinner" aria-hidden="true"></span><span>Načítám celý e-mail read-only. U zpráv s PDF přílohami to může chvíli trvat.</span></div>';
      }

      function renderDetail(item) {
        const detail = item.detail || {};
        const attachments = detail.attachments || [];
        detailPane.innerHTML =
          '<div class="detail-head">' +
            '<div>' +
              '<div class="subject">' + escapeHtml(detail.subject || item.subject || "(bez předmětu)") + '</div>' +
              '<div class="meta">' + escapeHtml((detail.sender ? detail.sender + " | " : "") + itemMeta(item)) + '</div>' +
            '</div>' +
            '<div class="status' + (item.queueDecision ? " done" : "") + '">' + escapeHtml(decisionLabel(item)) + '</div>' +
          '</div>' +
          '<div class="detail-actions">' +
            '<label><input type="checkbox" id="saveEmail"' + (item.queueDecision === "save" ? " checked" : "") + '> Uložit e-mail</label>' +
            '<label><input type="checkbox" id="skipEmail"' + (item.queueDecision === "skip" ? " checked" : "") + '> Neukládat</label>' +
            '<button type="button" class="danger" id="trashEmail">Koš</button>' +
          '</div>' +
          '<div><strong>Tělo e-mailu</strong></div>' +
          '<pre>' + escapeHtml(detail.body_text || "") + (detail.truncated ? "\\n\\n[Text je zkrácený.]" : "") + '</pre>' +
          '<div><strong>Přílohy</strong></div>' +
          '<div class="attachments">' + renderAttachmentRows(item, attachments) + '</div>' +
          renderRecentImportedAttachments();

        bindAttachmentOpenButtons();
        bindAttachmentPreviewButtons(item);
        queueDoc.getElementById("saveEmail").addEventListener("change", (event) => {
          setQueueDecision(item, event.target.checked ? "save" : "");
        });
        queueDoc.getElementById("skipEmail").addEventListener("change", (event) => {
          setQueueDecision(item, event.target.checked ? "skip" : "");
        });
        queueDoc.getElementById("trashEmail").addEventListener("click", () => {
          const ok = queue.confirm("Opravdu označit e-mail ke smazání?\\n\\nSkutečné smazání bude samostatná potvrzená akce v dalším kroku.");
          if (!ok) return;
          setQueueDecision(item, "trash_requested");
        });
        detailPane.querySelectorAll(".attachment-save").forEach((input) => {
          input.addEventListener("change", () => {
            const partId = input.dataset.partId || "";
            const current = new Set(item.saveAttachments || []);
            if (input.checked) current.add(partId);
            else current.delete(partId);
            item.saveAttachments = Array.from(current);
            if (item.saveAttachments.length && item.queueDecision !== "save") item.queueDecision = "save";
            renderQueueList();
          });
        });
        detailPane.querySelectorAll(".attachment-toggle").forEach((button) => {
          button.addEventListener("click", () => {
            const detailNode = button.closest(".attachment-row").querySelector(".attachment-detail");
            detailNode.classList.toggle("hidden");
            button.textContent = detailNode.classList.contains("hidden") ? "Metadata" : "Zavřít";
          });
        });
      }

      async function selectItem(itemId) {
        selectedId = itemId;
        const item = currentItem();
        renderQueueList();
        if (!item) return;
        if (item.detailLoaded) {
          queueStatus.textContent = "Detail načten z cache v tomto okně. IMAP se znovu nevolal.";
          renderDetail(item);
          return;
        }
        if (item.detailLoading) {
          renderLoadingDetail(item);
          return;
        }
        item.detailLoading = true;
        renderQueueList();
        renderLoadingDetail(item);
        queueStatus.textContent = "Načítám celý e-mail read-only. U větších zpráv s PDF to může chvíli trvat.";
        try {
          const res = await fetch("/api/email-processing/read-message", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
              provider: item.provider,
              folder: item.folder || "INBOX",
              uid: item.uid,
              max_chars: 12000
            })
          });
          const data = await res.json();
          if (!data.ok) {
            detailPane.innerHTML = '<div class="empty">' + escapeHtml(data.message || "E-mail se nepodařilo načíst.") + '</div>';
            return;
          }
          item.detail = data.email || {};
          item.detailLoaded = true;
          queueStatus.textContent = "Detail načten. Další kliknutí na stejný e-mail použije cache v tomto okně.";
          renderDetail(item);
        } catch (err) {
          detailPane.innerHTML = '<div class="empty">Chyba načtení: ' + escapeHtml(err) + '</div>';
        } finally {
          item.detailLoading = false;
          renderQueueList();
        }
      }

      batchBtn.addEventListener("click", async () => {
        const workItems = queueItems.filter((item) => item.queueDecision !== "trash_requested");
        if (!workItems.length) {
          queueStatus.textContent = "V této frontě jsou jen kandidáti ke koši. Použij tlačítko Emaily určené ke smazání smazat.";
          return;
        }
        const ok = queue.confirm("Zpracovat dávku?\\n\\nUložené e-maily půjdou do EmailArchiveVault. Vybrané PDF přílohy půjdou do private document vaultu a fulltextového indexu.");
        if (!ok) return;
        batchBtn.disabled = true;
        queueStatus.textContent = "Zpracovávám dávku. U větších PDF to může chvíli trvat.";
        try {
          const res = await fetch("/api/email-processing/process-batch", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
              items: workItems,
              trash_confirmation_text: ""
            })
          });
          const data = await res.json();
          if (!data.ok) {
            queueStatus.textContent = data.message || "Zpracování dávky skončilo s chybou.";
          } else {
            queueStatus.textContent = data.message || "Dávka zpracována.";
          }
          const importedNow = collectImportedAttachments(data.items || [], workItems);
          if (importedNow.length) {
            recentImportedAttachments = importedNow.concat(recentImportedAttachments).slice(0, 20);
            queueStatus.textContent += " Uložené PDF přílohy můžeš otevřít v detailu.";
          }
          const remaining = [];
          const byId = new Map((data.items || []).map((result) => [result.item_id, result]));
          queueItems.forEach((item) => {
            const result = byId.get(item.id);
            item.batchResult = result || {};
            if (!result || !result.ok || result.status === "trash_pending" || item.queueDecision === "trash_requested") remaining.push(item);
          });
          queueItems.splice(0, queueItems.length, ...remaining);
          selectedId = queueItems.length ? queueItems[0].id : "";
          renderQueueList();
          if (selectedId) renderDetail(currentItem());
          else {
            detailPane.innerHTML = '<div class="empty">Dávka je hotová.</div>' + renderRecentImportedAttachments();
            bindAttachmentOpenButtons();
          }
        } catch (err) {
          queueStatus.textContent = "Chyba zpracování dávky: " + err;
        } finally {
          updateBatchState();
        }
      });

      trashBatchBtn.addEventListener("click", async () => {
        const trashItems = queueItems.filter((item) => item.queueDecision === "trash_requested");
        if (!trashItems.length) {
          queueStatus.textContent = "Žádné e-maily nejsou označené ke smazání.";
          return;
        }
        const noun = trashItems.length === 1
          ? "e-mail označený"
          : (trashItems.length >= 2 && trashItems.length <= 4 ? "e-maily označené" : "e-mailů označených");
        const required = "Potvrzuji, přesuň " + trashItems.length + " " + noun + " ke smazání do koše.";
        const ok = queue.confirm(
          "Přesunout do koše " + trashItems.length + " e-mailů označených ke smazání?\\n\\n" +
          "Nepoužívá se EXPUNGE; zprávy se jen přesunou do koše provideru."
        );
        if (!ok) return;
        trashBatchBtn.disabled = true;
        queueStatus.textContent = "Přesouvám označené e-maily do koše.";
        try {
          const res = await fetch("/api/email-processing/process-batch", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
              items: trashItems,
              trash_confirmation_text: required
            })
          });
          const data = await res.json();
          queueStatus.textContent = data.message || (data.ok ? "Koš zpracován." : "Koš skončil s chybou.");
          const byId = new Map((data.items || []).map((result) => [result.item_id, result]));
          const remaining = [];
          queueItems.forEach((item) => {
            const result = byId.get(item.id);
            item.batchResult = result || {};
            if (result && result.ok && result.status === "trashed") {
              permanentDeleteItems.push({
                id: item.id,
                item_id: item.id,
                provider: item.provider,
                folder: item.folder || "INBOX",
                uid: item.uid,
                subject: item.subject || "",
                trash_folder: result.trash_folder || "",
                trash_uid: result.trash_uid || "",
                message_id: result.message_id || ""
              });
            }
            if (!result || !result.ok || result.status === "trash_pending") remaining.push(item);
          });
          queueItems.splice(0, queueItems.length, ...remaining);
          selectedId = queueItems.length ? queueItems[0].id : "";
          renderQueueList();
          if (selectedId) renderDetail(currentItem());
          else detailPane.innerHTML = '<div class="empty">Koš je hotový.</div>';
        } catch (err) {
          queueStatus.textContent = "Chyba přesunu do koše: " + err;
        } finally {
          updateBatchState();
        }
      });

      purgeTrashBtn.addEventListener("click", async () => {
        if (!permanentDeleteItems.length) {
          queueStatus.textContent = "Žádné e-maily nejsou připravené k trvalému smazání z koše.";
          return;
        }
        const count = permanentDeleteItems.length;
        const ok = queue.confirm(
          "Trvale smazat z koše " + count + " e-mailů?\\n\\n" +
          "Tato akce je nevratná a použije IMAP EXPUNGE nad zprávami v koši."
        );
        if (!ok) return;
        purgeTrashBtn.disabled = true;
        queueStatus.textContent = "Trvale mažu e-maily z koše.";
        try {
          const res = await fetch("/api/email-processing/purge-trash", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
              items: permanentDeleteItems,
              confirmed: true
            })
          });
          const data = await res.json();
          queueStatus.textContent = data.message || (data.ok ? "Trvalé smazání dokončeno." : "Trvalé smazání skončilo s chybou.");
          const byId = new Map((data.items || []).map((result) => [result.item_id, result]));
          permanentDeleteItems = permanentDeleteItems.filter((item) => {
            const result = byId.get(item.item_id || item.id);
            item.purgeResult = result || {};
            return !result || !result.ok || result.status !== "purged";
          });
          updateBatchState();
        } catch (err) {
          queueStatus.textContent = "Chyba trvalého smazání z koše: " + err;
          updateBatchState();
        }
      });

      renderQueueList();
      if (selectedId) selectItem(selectedId);
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
      const queueItems = [...toProcess, ...toTrash].map((item) => ({
        ...item,
        queueAction: item.action === "trash_requested" ? "trash_requested" : "process",
        queueDecision: item.action === "trash_requested" ? "trash_requested" : "",
        saveAttachments: []
      }));
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
    button { border: 0; border-radius: 6px; padding: 8px 11px; font: inherit; font-weight: 650; cursor: pointer; white-space: nowrap; }
    button.primary { background: var(--blue); color: white; }
    button.secondary { background: #e8eef8; color: #1d3b74; }
    button.danger { background: #fee2e2; color: var(--red); }
    button:disabled { opacity: 0.45; cursor: not-allowed; }
    main { padding: 18px 20px 28px; display: grid; gap: 14px; }
    .topbar { display: flex; justify-content: space-between; gap: 10px; align-items: center; flex-wrap: wrap; }
    .topbar-actions { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    .queue-grid { display: grid; grid-template-columns: 360px minmax(0, 1fr); gap: 14px; align-items: start; }
    section { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
    h2 { margin: 0; padding: 12px 14px; font-size: 14px; border-bottom: 1px solid var(--line); background: #f8fafc; }
    .body { padding: 13px 14px; display: grid; gap: 9px; }
    .item { border: 1px solid #edf0f4; border-radius: 8px; padding: 10px; background: #fbfcfe; display: grid; gap: 5px; text-align: left; width: 100%; color: inherit; }
    .item.active { border-color: #8eb1ed; background: #f4f8ff; }
    .subject { font-weight: 750; overflow-wrap: anywhere; }
    .meta, .reason, .empty, .note { color: var(--muted); font-size: 13px; overflow-wrap: anywhere; }
    .note strong { color: var(--ink); }
    .status { font-size: 12px; font-weight: 700; color: var(--amber); }
    .status.done { color: #16794c; }
    .status.loading { color: #1f5fbf; }
    .detail-head { display: flex; justify-content: space-between; gap: 10px; align-items: flex-start; flex-wrap: wrap; }
    .detail-actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; border-top: 1px solid #edf0f4; padding-top: 10px; }
    .detail-actions label, .attachment-row label { display: inline-flex; gap: 5px; align-items: center; }
    pre { margin: 0; max-height: 360px; overflow: auto; white-space: pre-wrap; overflow-wrap: anywhere; font: 12px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; background: #fbfcfe; border: 1px solid #edf0f4; border-radius: 7px; padding: 10px; }
    .attachments { display: grid; gap: 8px; }
    .attachment-row { border: 1px solid #edf0f4; border-radius: 7px; padding: 9px; display: grid; gap: 6px; background: #fbfcfe; }
    .attachment-tools { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    .loading-box { display: flex; align-items: center; gap: 8px; padding: 10px; border: 1px solid #bfd0ef; border-radius: 7px; background: #eef4ff; color: #1d3b74; font-weight: 650; }
    .mini-spinner { width: 14px; height: 14px; border: 2px solid #bfd0ef; border-top-color: var(--blue); border-radius: 50%; animation: spin 0.8s linear infinite; flex: 0 0 auto; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .hidden { display: none; }
    @media (max-width: 820px) { .queue-grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <header>
    <div class="topbar">
      <h1>Email Work Queue</h1>
      <div class="topbar-actions">
        <button class="danger" id="purgeTrashBtn" disabled>Trvale smazat e-maily v koši</button>
        <button class="danger" id="trashBatchBtn" disabled>Emaily určené ke smazání smazat</button>
        <button class="primary" id="batchBtn" disabled>Zpracovat dávku</button>
      </div>
    </div>
  </header>
  <main>
    <section>
      <h2>Souhrn</h2>
      <div class="body note">
        <div><strong>Připraveno ke zpracování:</strong> <span id="queueProcessCount">${toProcess.length}</span></div>
        <div><strong>Koš čeká na potvrzení:</strong> <span id="queueTrashCount">${toTrash.length}</span></div>
        <div><strong>Trvalé smazání v koši:</strong> <span id="queuePurgeCount">0</span></div>
        <div><strong>Ignorováno:</strong> ${ignored.length}</div>
        <div id="queueStatus">Klikni na e-mail vlevo. Detail se načte read-only, bez stahování příloh a bez mazání.</div>
      </div>
    </section>
    <div class="queue-grid">
      <section>
        <h2>E-maily k rozhodnutí</h2>
        <div class="body" id="queueList"></div>
      </section>
      <section>
        <h2>Detail e-mailu</h2>
        <div class="body" id="detailPane">
          <div class="empty">Vyber e-mail ze seznamu.</div>
        </div>
      </section>
    </div>
  </main>
</body>
</html>`);
      queue.document.close();
      initializeWorkQueueWindow(queue, queueItems);
      queue.focus();
      emailItems = [];
      window.lastOverviewText = "";
      renderItems(emailItems);
      updateWorkQueueState();
      overviewStatus.textContent = "Fronta byla otevřena v okně Email Work Queue; hlavní seznam je vyprázdněný.";
    }

    async function loadNewHeaders(options = {}) {
      const lastSevenDays = Boolean(options.lastSevenDays);
      const newOnly = Boolean(options.newOnly);
      const newestVisible = newestItemIso();
      if (newOnly && !newestVisible) {
        newHeadersStatus.textContent = "Obnovit nové je dostupné až po prvním načtení seznamu. Nejdřív použij Načti emaily.";
        updateRefreshButtonState();
        return;
      }
      const startedAt = Date.now();
      const days = selectedDays();
      refreshBtn.disabled = true;
      loadHeadersBtn.disabled = true;
      loadPendingBtn.disabled = true;
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
          : {limit_per_source: 25, since: newestVisible, known_ids: knownItemIds()};
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
        updateRefreshButtonState();
        loadHeadersBtn.disabled = false;
        loadPendingBtn.disabled = false;
        emailDaysInput.disabled = false;
      }
    }

    async function loadPendingWork() {
      loadPendingBtn.disabled = true;
      newHeadersStatus.textContent = "Načítám rozpracované e-maily z uložených rozhodnutí...";
      try {
        const res = await fetch("/api/email-processing/pending-work");
        const data = await res.json();
        if (!data.ok) {
          newHeadersStatus.textContent = data.message || "Rozpracované e-maily se nepodařilo načíst.";
          return;
        }
        const before = emailItems.length;
        emailItems = mergeItems(emailItems, data.items || []);
        renderItems(emailItems);
        updateWorkQueueState();
        const added = emailItems.length - before;
        newHeadersStatus.textContent = `${data.message || "Rozpracované e-maily načteny."} Přidáno do hlavního seznamu: ${added}.`;
      } catch (err) {
        newHeadersStatus.textContent = `Chyba načtení rozpracovaných e-mailů: ${err}`;
      } finally {
        loadPendingBtn.disabled = false;
      }
    }

    async function loadOverview() {
      refreshBtn.disabled = true;
      loadPendingBtn.disabled = true;
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
        updateRefreshButtonState();
        loadPendingBtn.disabled = false;
      }
    }

    refreshBtn.addEventListener("click", () => loadNewHeaders({newOnly: true}));
    emailDaysInput.addEventListener("change", normalizeDaysInput);
    loadHeadersBtn.addEventListener("click", () => loadNewHeaders({lastSevenDays: true}));
    loadPendingBtn.addEventListener("click", loadPendingWork);
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
    .reminder-list { display: grid; gap: 10px; }
    .reminder-conflict { border: 1px solid #f59e0b; border-radius: 8px; padding: 10px; background: #fffbeb; display: grid; gap: 7px; }
    .reminder-conflict-title { font-weight: 750; color: #92400e; }
    .reminder-conflict-item { border-top: 1px solid #fde68a; padding-top: 7px; display: grid; gap: 5px; }
    .reminder-conflict-item:first-of-type { border-top: 0; padding-top: 0; }
    .reminder-group { display: grid; gap: 7px; }
    .reminder-group h3 { margin: 0; font-size: 13px; color: #253047; }
    .reminder-card { border: 1px solid #edf0f4; border-radius: 8px; padding: 10px; background: #fbfcfe; display: grid; gap: 4px; }
    .reminder-card-head { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; align-items: start; }
    .reminder-actions { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
    .reminder-title { font-weight: 700; }
    .reminder-meta { color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
    .reminder-done { background: #dcfce7; color: #166534; }
    .reminder-source { border-top: 1px solid #edf0f4; margin-top: 6px; padding-top: 8px; display: grid; gap: 7px; }
    .reminder-source pre { margin: 0; border: 1px solid #edf0f4; border-radius: 7px; padding: 9px; background: white; max-height: 320px; overflow: auto; white-space: pre-wrap; overflow-wrap: anywhere; }
    .reminder-source-row { color: #344054; font-size: 12px; overflow-wrap: anywhere; }
    .vault-summary { display: grid; gap: 10px; }
    .vault-summary pre { border: 1px solid #edf0f4; border-radius: 7px; padding: 10px; background: #fbfcfe; }
    .vault-summary details { border: 1px solid #edf0f4; border-radius: 7px; padding: 9px 10px; background: #fbfcfe; }
    .vault-summary summary { cursor: pointer; font-weight: 650; }
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
      <button class="secondary" id="remindersBtn">Reminders</button>
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
          <div class="dashboard-row"><span class="dashboard-label">Reminders</span><span id="dashboardReminders" class="dashboard-value"></span></div>
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
            <button class="secondary" id="dashboardRemindersBtn">Reminders</button>
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
      <h2>Souhrn vaultu</h2>
      <div class="body"><div id="vaultText" class="vault-summary"></div></div>
    </section>
  </main>
  <div id="remindersModal" class="modal-backdrop hidden" role="dialog" aria-modal="true" aria-labelledby="remindersTitle">
    <div class="modal">
      <div class="modal-header">
        <h2 id="remindersTitle">Reminders</h2>
        <button class="secondary" id="remindersCloseBtn">Zavřít</button>
      </div>
      <div class="modal-body">
        <div id="remindersStatus" class="status-line">Načítám připomínky...</div>
        <div id="remindersList" class="reminder-list"></div>
      </div>
    </div>
  </div>
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
    const remindersBtn = document.getElementById("remindersBtn");
    const emailProcessingBtn = document.getElementById("emailProcessingBtn");
    const remindersModal = document.getElementById("remindersModal");
    const remindersCloseBtn = document.getElementById("remindersCloseBtn");
    const remindersStatus = document.getElementById("remindersStatus");
    const remindersList = document.getElementById("remindersList");
    const webAppsModal = document.getElementById("webAppsModal");
    const webAppsCloseBtn = document.getElementById("webAppsCloseBtn");
    const webAppsStatus = document.getElementById("webAppsStatus");
    const webAppsList = document.getElementById("webAppsList");
    const todayNewPdfCount = document.getElementById("todayNewPdfCount");
    const todayReviewCount = document.getElementById("todayReviewCount");
    const todayProblemCount = document.getElementById("todayProblemCount");
    const todayHint = document.getElementById("todayHint");
    const dashboardScanDocu = document.getElementById("dashboardScanDocu");
    const dashboardReminders = document.getElementById("dashboardReminders");
    const dashboardBackup = document.getElementById("dashboardBackup");
    const dashboardGit = document.getElementById("dashboardGit");
    const dashboardProcessBtn = document.getElementById("dashboardProcessBtn");
    const dashboardReviewBtn = document.getElementById("dashboardReviewBtn");
    const dashboardWebAppsBtn = document.getElementById("dashboardWebAppsBtn");
    const dashboardRemindersBtn = document.getElementById("dashboardRemindersBtn");
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
        renderVaultSummary(data.vault || "");
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

      const reminders = data.reminders || {};
      const reminderCounts = reminders.counts || {};
      const activeReminders = reminderCounts.active || 0;
      const openReminders = reminderCounts.open || 0;
      const conflictReminders = reminderCounts.conflicts || 0;
      const reminderClass = conflictReminders > 0 ? "bad" : activeReminders > 0 ? "warn" : openReminders > 0 ? "ok" : "ok";
      const conflictText = conflictReminders > 0 ? ` | <span class="bad">${conflictReminders} konflikt</span>` : "";
      dashboardReminders.innerHTML = `<span class="${reminderClass}">${activeReminders} aktivní</span> | ${openReminders} otevřené${conflictText}`;

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

    function renderVaultSummary(text) {
      vaultText.innerHTML = "";
      const raw = text || "";
      if (!raw) {
        const empty = document.createElement("div");
        empty.className = "status-line";
        empty.textContent = "Souhrn vaultu není dostupný.";
        vaultText.appendChild(empty);
        return;
      }
      const marker = "\\n- Inbox audit";
      const markerIndex = raw.indexOf(marker);
      const currentText = markerIndex >= 0 ? raw.slice(0, markerIndex).trim() : raw.trim();
      const auditText = markerIndex >= 0 ? raw.slice(markerIndex + 1).trim() : "";
      const current = document.createElement("pre");
      current.textContent = currentText;
      vaultText.appendChild(current);
      if (auditText) {
        const details = document.createElement("details");
        const summary = document.createElement("summary");
        summary.textContent = "Auditní historie inboxu";
        const audit = document.createElement("pre");
        audit.textContent = auditText;
        details.appendChild(summary);
        details.appendChild(audit);
        vaultText.appendChild(details);
      }
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

    async function openRemindersModal() {
      remindersModal.classList.remove("hidden");
      remindersStatus.textContent = "Načítám připomínky...";
      remindersList.innerHTML = "";
      try {
        const res = await fetch("/api/reminders");
        const data = await res.json();
        renderReminders(data);
      } catch (err) {
        remindersStatus.textContent = `Chyba načtení připomínek: ${err}`;
      }
    }

    function closeRemindersModal() {
      remindersModal.classList.add("hidden");
    }

    function renderReminders(data) {
      const counts = data.counts || {};
      remindersStatus.textContent = data.ok
        ? `${counts.open || 0} otevřené; ${counts.active || 0} ve startovním okně do ${data.startup_window_days || 14} dnů.`
        : (data.message || "Připomínky nejdou načíst.");
      remindersList.innerHTML = "";
      renderReminderConflicts(data.conflicts || []);
      const groups = data.groups || {};
      const order = [
        ["overdue", "Prošlé"],
        ["today", "Dnes"],
        ["soon", "Do 14 dnů"],
        ["later", "Později"],
        ["undated", "Bez data"]
      ];
      let rendered = 0;
      order.forEach(([key, label]) => {
        const items = groups[key] || [];
        if (!items.length) return;
        rendered += items.length;
        const group = document.createElement("div");
        group.className = "reminder-group";
        const heading = document.createElement("h3");
        heading.textContent = `${label} (${items.length})`;
        group.appendChild(heading);
        items.forEach((item) => {
          const actionId = item.reminder_ref || item.id || "";
          const card = document.createElement("div");
          card.className = "reminder-card";
          const head = document.createElement("div");
          head.className = "reminder-card-head";
          const title = document.createElement("div");
          title.className = "reminder-title";
          title.textContent = item.title || item.id || "Připomínka bez názvu";
          const actions = document.createElement("div");
          actions.className = "reminder-actions";
          const sourceBtn = document.createElement("button");
          sourceBtn.type = "button";
          sourceBtn.className = "secondary";
          sourceBtn.textContent = "Zdroj";
          sourceBtn.disabled = !actionId;
          const doneBtn = document.createElement("button");
          doneBtn.type = "button";
          doneBtn.className = "reminder-done";
          doneBtn.textContent = "Splněno";
          doneBtn.disabled = !actionId;
          doneBtn.addEventListener("click", () => markReminderDone(actionId, doneBtn));
          actions.appendChild(sourceBtn);
          actions.appendChild(doneBtn);
          const meta = document.createElement("div");
          meta.className = "reminder-meta";
          const due = item.due_date ? `deadline ${item.due_date}` : "bez data";
          meta.textContent = `${due} | priorita ${item.priority || "nezadaná"} | zdroj ${item.source_type || "nezadaný"}`;
          const id = document.createElement("div");
          id.className = "reminder-meta";
          id.textContent = `id: ${item.id || ""}`;
          const sourceDetail = document.createElement("div");
          sourceDetail.className = "reminder-source hidden";
          sourceBtn.addEventListener("click", () => loadReminderSource(actionId, sourceDetail, sourceBtn));
          head.appendChild(title);
          head.appendChild(actions);
          card.appendChild(head);
          card.appendChild(meta);
          card.appendChild(id);
          card.appendChild(sourceDetail);
          group.appendChild(card);
        });
        remindersList.appendChild(group);
      });
      if (!rendered) {
        const empty = document.createElement("div");
        empty.className = "status-line";
        empty.textContent = "Žádné otevřené připomínky.";
        remindersList.appendChild(empty);
      }
    }

    function renderReminderConflicts(conflicts) {
      conflicts.forEach((conflict) => {
        const box = document.createElement("div");
        box.className = "reminder-conflict";
        const title = document.createElement("div");
        title.className = "reminder-conflict-title";
        title.textContent = `Konflikt plateb: ${conflict.asset || "stejná věc"} | krytí od ${conflict.coverage_start || "nezjištěno"}`;
        const message = document.createElement("div");
        message.className = "reminder-meta";
        message.textContent = conflict.message || "Nekonat platbu bez porovnání.";
        box.appendChild(title);
        box.appendChild(message);
        (conflict.items || []).forEach((item) => {
          const row = document.createElement("div");
          row.className = "reminder-conflict-item";
          const summary = document.createElement("div");
          summary.className = "reminder-meta";
          summary.textContent = `${item.title || item.id || "Připomínka"} | deadline ${item.due_date || "bez data"} | zdroj ${item.source_type || "nezadaný"}`;
          const note = document.createElement("div");
          note.className = "reminder-meta";
          note.textContent = item.conflict_note || "";
          const sourceBtn = document.createElement("button");
          sourceBtn.type = "button";
          sourceBtn.className = "secondary";
          sourceBtn.textContent = "Zdroj";
          sourceBtn.disabled = !item.reminder_ref;
          const detail = document.createElement("div");
          detail.className = "reminder-source hidden";
          sourceBtn.addEventListener("click", () => loadReminderSource(item.reminder_ref || "", detail, sourceBtn));
          row.appendChild(summary);
          if (item.conflict_note) row.appendChild(note);
          row.appendChild(sourceBtn);
          row.appendChild(detail);
          box.appendChild(row);
        });
        remindersList.appendChild(box);
      });
    }

    async function loadReminderSource(reminderId, detailNode, button) {
      if (!reminderId) return;
      if (!detailNode.classList.contains("hidden") && detailNode.dataset.loaded === "1") {
        detailNode.classList.add("hidden");
        button.textContent = "Zdroj";
        return;
      }
      button.disabled = true;
      button.textContent = "Načítám...";
      detailNode.classList.remove("hidden");
      detailNode.textContent = "Načítám zdroj read-only...";
      try {
        const result = await postJson("/api/reminders/source", {reminder_id: reminderId});
        renderReminderSource(result, detailNode);
        detailNode.dataset.loaded = "1";
        button.textContent = "Skrýt zdroj";
      } catch (err) {
        detailNode.textContent = `Chyba načtení zdroje: ${err}`;
        button.textContent = "Zdroj";
      } finally {
        button.disabled = false;
      }
    }

    function renderReminderSource(result, detailNode) {
      detailNode.innerHTML = "";
      const status = document.createElement("div");
      status.className = "reminder-source-row";
      status.textContent = result.message || (result.ok ? "Zdroj načten." : "Zdroj se nepodařilo načíst.");
      detailNode.appendChild(status);
      if (result.kind === "email" && result.email) {
        renderReminderEmailSource(result.email, detailNode);
      } else if (result.kind === "document" && result.document) {
        renderReminderDocumentSource(result.document, detailNode);
      } else {
        renderReminderGenericSource(result, detailNode);
      }
    }

    function appendSourceRow(parent, label, value) {
      if (!value) return;
      const row = document.createElement("div");
      row.className = "reminder-source-row";
      row.textContent = `${label}: ${value}`;
      parent.appendChild(row);
    }

    function appendSourcePre(parent, text) {
      if (!text) return;
      const pre = document.createElement("pre");
      pre.textContent = text;
      parent.appendChild(pre);
    }

    function renderReminderEmailSource(email, detailNode) {
      appendSourceRow(detailNode, "Předmět", email.subject || "");
      appendSourceRow(detailNode, "Od", email.sender || "");
      appendSourceRow(detailNode, "Datum", email.date || "");
      appendSourceRow(detailNode, "Zdroj", `${email.provider || ""} / ${email.folder || ""} / UID ${email.uid || ""}`);
      appendSourcePre(detailNode, email.body_text || "");
      const attachments = email.attachments || [];
      if (attachments.length) {
        appendSourceRow(
          detailNode,
          "Přílohy",
          attachments.map((item) => `${item.filename || "(bez názvu)"} | ${item.content_type || ""} | ${item.size_bytes || 0} B`).join("; ")
        );
      }
    }

    function renderReminderDocumentSource(documentInfo, detailNode) {
      appendSourceRow(detailNode, "Dokument", documentInfo.title || documentInfo.document_id || "");
      appendSourceRow(detailNode, "Soubor", documentInfo.original_filename || "");
      appendSourceRow(detailNode, "Oblast", documentInfo.domain || "");
      appendSourceRow(detailNode, "Typ", documentInfo.document_type || "");
      appendSourceRow(detailNode, "Protistrana", documentInfo.counterparty || "");
      appendSourceRow(detailNode, "Vazba", documentInfo.related_asset || "");
      appendSourceRow(detailNode, "Stav čtení", documentInfo.reading_status_label || "");
      appendSourcePre(detailNode, documentInfo.snippet || "");
      const contexts = documentInfo.due_contexts || [];
      contexts.forEach((item) => {
        appendSourcePre(detailNode, `${item.date || ""} | ${item.type || ""} | ${item.confidence || ""}\n${item.context || ""}`);
      });
      if (documentInfo.can_open_pdf && documentInfo.document_ref) {
        const openBtn = document.createElement("button");
        openBtn.type = "button";
        openBtn.className = "secondary";
        openBtn.textContent = "Otevřít PDF";
        openBtn.addEventListener("click", () => openReminderDocument(documentInfo.document_ref, openBtn));
        detailNode.appendChild(openBtn);
      }
    }

    function renderReminderGenericSource(result, detailNode) {
      const source = result.source || {};
      appendSourceRow(detailNode, "Typ", source.type || "");
      appendSourceRow(detailNode, "UID", source.uid || "");
      appendSourceRow(detailNode, "Datum", source.date || "");
      appendSourceRow(detailNode, "Odesílatel", source.sender || "");
      appendSourcePre(detailNode, result.notes || "");
      const links = result.links || [];
      if (links.length) {
        appendSourceRow(detailNode, "Odkazy", links.map((item) => `${item.domain || ""} (${item.count || "1"})`).join("; "));
      }
    }

    async function openReminderDocument(documentId, button) {
      if (!documentId) return;
      button.disabled = true;
      try {
        const result = await postJson("/api/documents/open", {document_id: documentId});
        remindersStatus.textContent = result.message || "Hotovo.";
      } catch (err) {
        remindersStatus.textContent = `Chyba otevření PDF: ${err}`;
      } finally {
        button.disabled = false;
      }
    }

    async function markReminderDone(reminderId, button) {
      if (!reminderId) return;
      if (!window.confirm("Označit tuto připomínku jako splněnou?")) {
        return;
      }
      button.disabled = true;
      remindersStatus.textContent = "Označuji připomínku jako splněnou...";
      try {
        const result = await postJson("/api/reminders/done", {reminder_id: reminderId});
        if (result.reminders) {
          renderReminders(result.reminders);
        }
        remindersStatus.textContent = result.message || "Hotovo.";
        await refresh();
      } catch (err) {
        remindersStatus.textContent = `Chyba uložení připomínky: ${err}`;
      } finally {
        button.disabled = false;
      }
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
      const target = new URL(app.url, window.location.href);
      if (app.kind === "GitHub Pages") {
        target.searchParams.set("cockpit_cache", String(Date.now()));
      }
      const targetUrl = target.href;
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
    dashboardRemindersBtn.addEventListener("click", openRemindersModal);
    dashboardEmailBtn.addEventListener("click", openEmailProcessing);
    dashboardSamanthaBtn.addEventListener("click", () => postAction("/api/samantha/open", dashboardSamanthaBtn));
    dashboardCodexBtn.addEventListener("click", () => postAction("/api/codex/open", dashboardCodexBtn));
    webAppsBtn.addEventListener("click", openWebAppsModal);
    remindersBtn.addEventListener("click", openRemindersModal);
    emailProcessingBtn.addEventListener("click", openEmailProcessing);
    remindersCloseBtn.addEventListener("click", closeRemindersModal);
    remindersModal.addEventListener("click", (event) => {
      if (event.target === remindersModal) {
        closeRemindersModal();
      }
    });
    webAppsCloseBtn.addEventListener("click", closeWebAppsModal);
    webAppsModal.addEventListener("click", (event) => {
      if (event.target === webAppsModal) {
        closeWebAppsModal();
      }
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !remindersModal.classList.contains("hidden")) {
        closeRemindersModal();
      } else if (event.key === "Escape" && !webAppsModal.classList.contains("hidden")) {
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
