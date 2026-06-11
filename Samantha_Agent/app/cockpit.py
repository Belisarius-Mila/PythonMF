from __future__ import annotations

import csv
import errno
import base64
import binascii
import html
import json
import hashlib
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
import urllib.error
from collections.abc import Callable
from datetime import date, datetime, timezone
from email import message_from_bytes
from email.utils import parsedate_to_datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, urlparse

from app.adam_service import (
    adam_service_status,
    load_adam_text_reply,
    restart_adam_service,
    start_adam_service,
    stop_adam_service,
    submit_adam_text_request,
)
from app.article_archive import (
    archive_text_entry,
    archive_url,
    get_article,
    get_article_attachment,
    attach_article_image,
    ATTACHMENT_CONFIRMATION_PHRASE,
    list_articles,
    search_articles,
)
from app.backup.activity_state import backup_activity_status
from app.documents.consistency_audit import format_document_consistency_audit, run_document_consistency_audit, save_audit_decision
from app.documents.scandocu import DEFAULT_DOWNLOADS_DIR, scan_downloads_for_pdfs
from app.documents.vault import (
    DEFAULT_DOCUMENTS_DIR,
    DEFAULT_MOBILE_DOCUMENT_INBOX,
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
    save_document_due_reminder_summary,
    tokenize,
    write_json,
    write_jsonl,
)
from app.quantitative_status import DEFAULT_METRICS_PATH as QUANTITATIVE_STATUS_METRICS_PATH
from app.quantitative_status import ExtensionStats as QuantitativeExtensionStats
from app.quantitative_status import run_samantha_quantitative_status
from app.quick_notes import DEFAULT_ICLOUD_SHORTCUTS_INBOX, DEFAULT_INDEX_PATH as QUICK_NOTES_INDEX_PATH
from app.quick_notes import sync_quick_notes_index
from app.urgent_reminders import DEFAULT_INDEX_PATH as URGENT_REMINDERS_INDEX_PATH
from app.urgent_reminders import mark_urgent_reminder_done
from app.urgent_reminders import sync_urgent_reminders_index
from app.email.activity_state import DEFAULT_EMAIL_ACTIVITY_STATE_PATH, record_email_archive_completed
from app.email.archive_models import EmailArchiveSource
from app.email.archive_service import DEFAULT_EMAIL_ARCHIVE_DIR, save_email_archive
from app.email.config import EmailConfigError
from app.email.icloud_provider import EmailProviderError, ICloudReadOnlyEmailProvider
from app.email.models import EmailAttachmentMeta, EmailHeader, EmailMessage
from app.email.redaction import redact_email_addresses
from app.email.seznam_provider import SeznamEmailProviderError, SeznamReadOnlyEmailProvider
from app.reminders.query_tools import mark_reminder_done_text
from app.reminders.store import DEFAULT_REMINDERS_PATH, load_reminders_store, write_reminders_store
from app.speech import SpeechError, TranscriptionError, speak_text, transcribe_audio_base64
from app.speech.edge_tts_mp3 import (
    DEFAULT_EDGE_TTS_RATE,
    DEFAULT_EDGE_TTS_VOICE,
    EdgeTtsError,
    synthesize_edge_tts_mp3_sync,
)
from app.speech.local_tts import DEFAULT_VOICE
from app.speech.adam_voice_mode import (
    ADAM_LAST_RESPONSE_PATH,
    load_voice_mode_status,
    load_last_adam_response,
    pid_exists,
    update_pending_approval,
    write_voice_mode_status,
)
from app.speech.terminal_bridge import (
    CURRENT_CODEX_TTY_PATH,
    discover_codex_ttys,
    normalize_tty,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COCKPIT_PORT = 8770
COCKPIT_URL = f"http://127.0.0.1:{COCKPIT_PORT}"
SCANDOCU_URL = "http://127.0.0.1:8766"
SCANDOCU_PORT = 8766
SCANDOCU_LOG_DIR = PROJECT_ROOT / "data" / "private" / "documents" / "scandocu"
SCANDOCU_LOG_FILE = SCANDOCU_LOG_DIR / "server.log"
SCANDOCU_SERVER_SCRIPT = PROJECT_ROOT / "scripts" / "scandocu_server.py"
COCKPIT_RESTART_SCRIPT = PROJECT_ROOT / "scripts" / "restart_cockpit.py"
ADAM_VOICE_MODE_SCRIPT = PROJECT_ROOT / "scripts" / "adam_voice_mode.py"
ADAM_VOICE_MODE_LOG_FILE = PROJECT_ROOT / "data" / "private" / "voice_inbox" / "adam_voice_mode.log"
EMAIL_SESSION_HANDOFF_DIR = PROJECT_ROOT / "data" / "private" / "email_session_handoffs"
LOCAL_SEZNAM_EMAIL_DIR = PROJECT_ROOT / "data" / "private" / "email_seznam"
EMAIL_PROCESSING_DECISIONS_FILE = EMAIL_SESSION_HANDOFF_DIR / "email_processing_decisions.json"
EMAIL_WORK_QUEUE_ACTIONS_FILE = EMAIL_SESSION_HANDOFF_DIR / "email_work_queue_actions.jsonl"
EMAIL_ATTACHMENT_PREVIEW_DIR = Path("/private/tmp/samantha_email_attachment_preview")
DOCUMENT_PRINT_PRINTER_LABEL = "HP LaserJet M110w (1CA1A9)"
DOCUMENT_PRINT_PREFERRED_CUPS_QUEUE = "HP_LaserJet_M110w__1CA1A9__20240926171754"
DOCUMENT_PRINT_REQUIRED_WIFI = "Telekom-865692"
DOCUMENT_PRINT_IPP_ID = "NPI1CA1A9.local"
DOCUMENT_PRINT_DISCOVERY_TIMEOUT = 5.0
GIT_ROOT = PROJECT_ROOT.parent
ACTIVE_PROJECTS_PATH = PROJECT_ROOT / "memory" / "ACTIVE_PROJECTS.md"
PROJECT_CAPABILITY_MAP_PATH = PROJECT_ROOT / "memory" / "technical" / "project_capability_map.md"
JANICKA_COOKBOOK_PATH = PROJECT_ROOT / "memory" / "projects" / "janicka_cockpit_kucharka.md"
JANICKA_TAKEOVER_PATH = PROJECT_ROOT / "memory" / "projects" / "janicka_cockpit_takeover.md"
SESSION_AUTOSAVE_DIR = PROJECT_ROOT / "data" / "session_autosave"
VOICE_COMMAND_INBOX_DIR = PROJECT_ROOT / "data" / "private" / "voice_inbox"
MEMORY_INDEX_PATH = PROJECT_ROOT / "memory" / "MEMORY_INDEX.md"
RECOVERY_HANDOFF_PATHS = (
    PROJECT_ROOT / "memory" / "handoffs" / "cockpit_recovery_center_priority_2026_06_03.md",
    PROJECT_ROOT / "memory" / "handoffs" / "cockpit_development_priorities_2026_06_03.md",
)
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
        "title": "E-maily",
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
}
DOCUMENT_DOMAIN_LABELS: dict[str, str] = {
    "car": "auto",
    "home": "domácnost / bydlení",
    "insurance": "pojištění",
    "tax": "daně",
    "energy": "energie",
    "employment": "práce / zaměstnání",
    "health": "zdraví",
    "warranty": "záruky",
    "other": "ostatní",
}
DOCUMENT_TYPE_LABELS: dict[str, str] = {
    "contract": "smlouva",
    "document": "dokument",
    "email-attachment-pdf": "PDF příloha e-mailu",
    "employment_contract": "pracovní smlouva",
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
DOCUMENT_METADATA_UPDATE_FIELDS: tuple[str, ...] = (
    "domain",
    "document_type",
    "counterparty",
    "related_asset",
)
DOCUMENT_DUE_TYPE_LABELS: dict[str, str] = {
    "payment_due": "platba",
    "valid_until": "konec platnosti",
    "service_due": "servis / revize",
    "deadline": "termín",
    "context_date": "kontextové datum",
    "unknown_date": "nejasné datum",
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


def web_apps_catalog() -> dict[str, Any]:
    return {"ok": True, "apps": [dict(item) for item in WEB_APP_CATALOG]}


def parse_tag_payload(raw_tags: Any) -> list[str]:
    if isinstance(raw_tags, str):
        return [part.strip() for part in re.split(r"[,;]", raw_tags) if part.strip()]
    if isinstance(raw_tags, list):
        return [str(part).strip() for part in raw_tags if str(part).strip()]
    return []


def library_archive_url_action(payload: dict[str, Any]) -> dict[str, Any]:
    tags = parse_tag_payload(payload.get("tags", []))
    try:
        result = archive_url(
            url=str(payload.get("url", "")),
            category=str(payload.get("category", "other")),
            tags=tags,
        )
    except ValueError as exc:
        return {"ok": False, "message": str(exc), "error": "invalid_url"}
    except urllib.error.URLError as exc:
        return {"ok": False, "message": f"URL se nepodařilo stáhnout: {exc}", "error": "fetch_failed"}
    except OSError as exc:
        return {"ok": False, "message": f"Článek se nepodařilo uložit: {exc}", "error": "archive_failed"}
    return result


def library_archive_text_action(payload: dict[str, Any]) -> dict[str, Any]:
    tags = parse_tag_payload(payload.get("tags", []))
    try:
        return archive_text_entry(
            title=str(payload.get("title", "")),
            text=str(payload.get("text", "")),
            category=str(payload.get("category", "other")),
            tags=tags,
            source_label=str(payload.get("source_label", "")) or "Vložený text",
            source_note=str(payload.get("source_note", "")),
        )
    except ValueError as exc:
        return {"ok": False, "message": str(exc), "error": "invalid_text"}
    except OSError as exc:
        return {"ok": False, "message": f"Text se nepodařilo uložit: {exc}", "error": "archive_failed"}


def library_attach_image_action(payload: dict[str, Any]) -> dict[str, Any]:
    data_url = str(payload.get("image_data_url", "")).strip()
    if "," not in data_url:
        return {"ok": False, "message": "Vyber obrázek k připojení.", "error": "missing_image"}
    header, encoded = data_url.split(",", 1)
    mime_type = "image/jpeg"
    match = re.match(r"data:([^;]+);base64$", header)
    if match:
        mime_type = match.group(1)
    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        return {"ok": False, "message": "Obrázek se nepodařilo přečíst.", "error": "invalid_image"}
    tags = parse_tag_payload(payload.get("tags", []))
    for tag in ("rodinny-recept", "rucne-psany", "scan", "ma-obrazek", "prepis-overit"):
        if tag not in tags:
            tags.append(tag)
    try:
        return attach_article_image(
            article_id=str(payload.get("article_id", "")),
            image_bytes=image_bytes,
            filename=str(payload.get("filename", "")),
            label=str(payload.get("label", "")) or "Ručně psaný recept",
            role=str(payload.get("role", "")) or "handwritten_recipe_scan",
            note=str(payload.get("note", "")),
            mime_type=mime_type,
            tags=tags,
            user_confirmed=True,
            confirmation_text=ATTACHMENT_CONFIRMATION_PHRASE,
        )
    except ValueError as exc:
        return {"ok": False, "message": str(exc), "error": "invalid_attachment"}
    except OSError as exc:
        return {"ok": False, "message": f"Obrázek se nepodařilo uložit: {exc}", "error": "archive_failed"}


def recovery_center_status(
    *,
    autosave_dir: Path = SESSION_AUTOSAVE_DIR,
    active_projects_path: Path = ACTIVE_PROJECTS_PATH,
    memory_index_path: Path = MEMORY_INDEX_PATH,
    handoff_paths: tuple[Path, ...] = RECOVERY_HANDOFF_PATHS,
    git_status: Callable[[], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    git = git_status() if git_status is not None else git_status_summary()
    return {
        "ok": True,
        "message": "Recovery centrum je read-only a nic neprepisuje.",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "autosave": latest_autosave_metadata(autosave_dir),
        "git": git,
        "active_project": recovery_active_project(active_projects_path),
        "handoffs": recovery_handoff_summaries(handoff_paths),
        "memory_index": {
            "path": str(relative_to_project(memory_index_path)),
            "exists": memory_index_path.exists(),
        },
        "commands": [
            {
                "label": "Bezny navrat do bezici relace",
                "command": "samantha",
                "note": "Pripoji existujici screen relaci, nebo zalozi novou.",
            },
            {
                "label": "Kdyz shell prikaz neexistuje",
                "command": "source ~/.zshrc && samantha",
                "note": "Nacte shell konfiguraci a pak spusti Samanthu.",
            },
            {
                "label": "Po padu Codexu",
                "command": "codex resume --last",
                "note": "Navaze posledni Codex session v adresari projektu.",
            },
        ],
        "references": [
            "memory/technical/session_recovery_rules.md",
            "memory/infrastructure/codex_reconnect_recovery.md",
            "memory/handoffs/cockpit_recovery_center_priority_2026_06_03.md",
        ],
        "safety_note": "Autosave logy jsou jen nouzova lokalni obnova; panel ukazuje metadata, ne obsah logu.",
    }


def latest_autosave_metadata(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_dir():
        return {
            "ok": False,
            "message": "Autosave slozka zatim neexistuje.",
            "dir": str(relative_to_project(path)),
            "file_count": 0,
            "latest_file": "",
            "latest_modified_at": "",
            "latest_age_seconds": None,
        }
    files = [
        item
        for item in path.iterdir()
        if item.is_file()
        and item.name.startswith("session_")
        and item.suffix.lower() in {".txt", ".jsonl"}
    ]
    if not files:
        return {
            "ok": False,
            "message": "V autosave slozce nejsou zadne TXT/JSONL snapshoty.",
            "dir": str(relative_to_project(path)),
            "file_count": 0,
            "latest_file": "",
            "latest_modified_at": "",
            "latest_age_seconds": None,
        }
    latest = max(files, key=lambda item: item.stat().st_mtime)
    modified = latest.stat().st_mtime
    age_seconds = max(0, int(time.time() - modified))
    return {
        "ok": True,
        "message": "Autosave metadata nactena bez cteni obsahu logu.",
        "dir": str(relative_to_project(path)),
        "file_count": len(files),
        "latest_file": latest.name,
        "latest_modified_at": datetime.fromtimestamp(modified).isoformat(timespec="seconds"),
        "latest_age_seconds": age_seconds,
    }


def recovery_active_project(path: Path = ACTIVE_PROJECTS_PATH) -> dict[str, Any]:
    try:
        projects = parse_active_projects_table(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return {
            "ok": False,
            "message": f"ACTIVE_PROJECTS nejde nacist: {exc}",
            "source": str(relative_to_project(path)),
        }
    project = next((item for item in projects if item.get("name") == "Cockpit Recovery centrum"), None)
    if project is None:
        return {
            "ok": False,
            "message": "Cockpit Recovery centrum neni v ACTIVE_PROJECTS.",
            "source": str(relative_to_project(path)),
        }
    return {
        "ok": True,
        "message": "Aktivni projekt Recovery centra nalezen.",
        "source": str(relative_to_project(path)),
        "name": project.get("name", ""),
        "priority": project.get("priority", ""),
        "status": project.get("status", ""),
        "next_step": project.get("next_step", ""),
        "memory_file": project.get("memory_file", ""),
        "handoff": project.get("handoff", ""),
        "flags": project.get("flags", []),
    }


def recovery_handoff_summaries(paths: tuple[Path, ...] = RECOVERY_HANDOFF_PATHS) -> list[dict[str, Any]]:
    return [recovery_handoff_summary(path) for path in paths]


def recovery_handoff_summary(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": path.exists(),
        "path": str(relative_to_project(path)),
        "title": "",
        "priority": "",
        "status": "",
        "remind_on_start": "",
        "date": "",
        "next_step": "",
    }
    if not path.exists():
        result["message"] = "Handoff soubor neexistuje."
        return result
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        result["ok"] = False
        result["message"] = f"Handoff nejde nacist: {exc}"
        return result
    fields: dict[str, str] = {}
    capture_next = False
    next_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if capture_next:
            if stripped and not stripped.endswith(":"):
                next_lines.append(stripped.lstrip("- ").strip())
                if len(next_lines) >= 2:
                    capture_next = False
            elif stripped.endswith(":"):
                capture_next = False
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            normalized = key.strip().casefold()
            if normalized in {"nazev", "priorita", "stav", "pripomenout pri startu", "datum"}:
                fields[normalized] = value.strip()
            if normalized == "dalsi krok":
                capture_next = True
                if value.strip():
                    next_lines.append(value.strip())
    result.update(
        {
            "title": safe_text(fields.get("nazev", ""))[:180],
            "priority": safe_text(fields.get("priorita", ""))[:40],
            "status": safe_text(fields.get("stav", ""))[:120],
            "remind_on_start": safe_text(fields.get("pripomenout pri startu", ""))[:40],
            "date": safe_text(fields.get("datum", ""))[:40],
            "next_step": safe_text(" ".join(next_lines))[:300],
        }
    )
    result["message"] = "Handoff metadata nactena."
    return result


def quick_notes_status(
    *,
    inbox_dir: Path = DEFAULT_ICLOUD_SHORTCUTS_INBOX,
    index_path: Path = QUICK_NOTES_INDEX_PATH,
    limit: int = 20,
) -> dict[str, Any]:
    inbox_exists = inbox_dir.exists()
    try:
        notes = sync_quick_notes_index(inbox_dir=inbox_dir, index_path=index_path)
    except (OSError, ValueError) as exc:
        fallback = quick_notes_status_from_index(index_path=index_path, limit=limit)
        if fallback["notes"]:
            return {
                **fallback,
                "ok": True,
                "message": f"Quick Notes z lokálního indexu; iCloud sync teď selhal: {exc}",
                "inbox_exists": inbox_exists,
                "inbox": str(inbox_dir),
                "index": str(relative_to_project(index_path)),
                "sync_error": safe_text(str(exc))[:300],
            }
        return {
            **fallback,
            "ok": False,
            "message": f"Quick Notes se nepodařilo načíst: {exc}",
            "inbox_exists": inbox_exists,
            "inbox": str(inbox_dir),
            "index": str(relative_to_project(index_path)),
            "sync_error": safe_text(str(exc))[:300],
        }

    active_notes = sorted(
        (note for note in notes if note.status == "inbox"),
        key=lambda note: note.note_number,
        reverse=True,
    )
    shown = active_notes[: max(1, limit)]
    if not inbox_exists:
        message = "Quick Notes inbox zatím není synchronizovaný na Mac."
    elif not active_notes:
        message = "Quick Notes inbox je prázdný."
    else:
        message = f"{len(active_notes)} poznámek v Quick Notes inboxu."
    return {
        "ok": True,
        "message": message,
        "inbox_exists": inbox_exists,
        "inbox": str(inbox_dir),
        "index": str(relative_to_project(index_path)),
        "counts": {"active": len(active_notes), "total": len(notes)},
        "notes": [
            {
                "note_number": note.note_number,
                "category": safe_text(note.category)[:80],
                "status": safe_text(note.status)[:80],
                "created_at": safe_text(note.created_at)[:80],
                "modified_at": safe_text(note.modified_at)[:80],
                "title": safe_text(note.title)[:180],
                "snippet": safe_text(note.snippet)[:300],
                "size_bytes": note.size_bytes,
                "triage": quick_note_triage_hint(note.snippet),
            }
            for note in shown
        ],
    }


def quick_notes_status_from_index(*, index_path: Path, limit: int = 20) -> dict[str, Any]:
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        records: list[dict[str, Any]] = []
    else:
        raw_records = data.get("notes", [])
        records = raw_records if isinstance(raw_records, list) else []
    usable = [record for record in records if isinstance(record, dict)]
    active = [record for record in usable if str(record.get("status", "inbox") or "inbox") == "inbox"]
    active.sort(key=lambda item: quick_note_number(item), reverse=True)
    return {
        "ok": True,
        "message": "Quick Notes načtené z lokálního indexu.",
        "inbox_exists": False,
        "inbox": "",
        "index": str(relative_to_project(index_path)),
        "counts": {"active": len(active), "total": len(usable)},
        "notes": [
            {
                "note_number": quick_note_number(record),
                "category": safe_text(str(record.get("category", "inbox") or "inbox"))[:80],
                "status": safe_text(str(record.get("status", "inbox") or "inbox"))[:80],
                "created_at": safe_text(str(record.get("created_at", "") or ""))[:80],
                "modified_at": safe_text(str(record.get("modified_at", "") or ""))[:80],
                "title": safe_text(str(record.get("title", "") or ""))[:180],
                "snippet": safe_text(str(record.get("snippet", "") or ""))[:300],
                "size_bytes": quick_note_size(record),
                "triage": quick_note_triage_hint(str(record.get("snippet", "") or "")),
            }
            for record in active[: max(1, limit)]
        ],
    }


def quick_note_detail_status(
    note_number: int,
    *,
    inbox_dir: Path = DEFAULT_ICLOUD_SHORTCUTS_INBOX,
    index_path: Path = QUICK_NOTES_INDEX_PATH,
    max_chars: int = 50000,
) -> dict[str, Any]:
    if note_number < 1:
        return {
            "ok": False,
            "message": "Neplatné číslo Quick Note.",
            "note_number": note_number,
            "body_text": "",
            "truncated": False,
        }

    try:
        notes = sync_quick_notes_index(inbox_dir=inbox_dir, index_path=index_path)
    except (OSError, ValueError) as exc:
        return quick_note_detail_from_index(
            note_number=note_number,
            index_path=index_path,
            max_chars=max_chars,
            sync_error=exc,
        )

    note = next((item for item in notes if item.note_number == note_number and item.status == "inbox"), None)
    if note is None:
        return {
            "ok": False,
            "message": f"Quick Note #{note_number} není v aktivním inboxu.",
            "note_number": note_number,
            "body_text": "",
            "truncated": False,
        }

    return quick_note_detail_payload(
        note_number=note.note_number,
        category=note.category,
        status=note.status,
        created_at=note.created_at,
        modified_at=note.modified_at,
        title=note.title,
        snippet=note.snippet,
        size_bytes=note.size_bytes,
        source_path=note.source_path,
        max_chars=max_chars,
    )


def quick_note_detail_from_index(
    *,
    note_number: int,
    index_path: Path,
    max_chars: int,
    sync_error: Exception | None = None,
) -> dict[str, Any]:
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        message = f"Quick Note #{note_number} se nepodařilo najít v lokálním indexu."
        if sync_error is not None:
            message += f" iCloud sync teď selhal: {sync_error}"
        return {
            "ok": False,
            "message": message,
            "note_number": note_number,
            "body_text": "",
            "truncated": False,
            "index_error": safe_text(str(exc))[:300],
        }

    raw_records = data.get("notes", [])
    records = raw_records if isinstance(raw_records, list) else []
    record = next(
        (
            item
            for item in records
            if isinstance(item, dict)
            and quick_note_number(item) == note_number
            and str(item.get("status", "inbox") or "inbox") == "inbox"
        ),
        None,
    )
    if record is None:
        return {
            "ok": False,
            "message": f"Quick Note #{note_number} není v lokálním indexu aktivního inboxu.",
            "note_number": note_number,
            "body_text": "",
            "truncated": False,
        }

    payload = quick_note_detail_payload(
        note_number=quick_note_number(record),
        category=safe_text(str(record.get("category", "inbox") or "inbox"))[:80],
        status=safe_text(str(record.get("status", "inbox") or "inbox"))[:80],
        created_at=safe_text(str(record.get("created_at", "") or ""))[:80],
        modified_at=safe_text(str(record.get("modified_at", "") or ""))[:80],
        title=safe_text(str(record.get("title", "") or ""))[:180],
        snippet=safe_text(str(record.get("snippet", "") or ""))[:300],
        size_bytes=quick_note_size(record),
        source_path=Path(str(record.get("source_path", "") or "")),
        max_chars=max_chars,
    )
    if sync_error is not None:
        payload["message"] = f"{payload['message']} Detail je z lokálního indexu; iCloud sync teď selhal: {sync_error}"
        payload["sync_error"] = safe_text(str(sync_error))[:300]
    return payload


def quick_note_detail_payload(
    *,
    note_number: int,
    category: str,
    status: str,
    created_at: str,
    modified_at: str,
    title: str,
    snippet: str,
    size_bytes: int,
    source_path: Path,
    max_chars: int,
) -> dict[str, Any]:
    body_text = ""
    truncated = False
    message = f"Quick Note #{note_number} načtena."
    source_suffix = source_path.suffix.lower()
    if not source_path.is_file() or source_suffix not in {".md", ".txt"}:
        message = f"Quick Note #{note_number} je v indexu, ale zdrojový soubor nejde bezpečně přečíst."
    else:
        try:
            text = source_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            message = f"Quick Note #{note_number} se nepodařilo přečíst: {exc}"
        else:
            truncated = len(text) > max_chars
            body_text = text[:max_chars].rstrip()

    return {
        "ok": bool(body_text),
        "message": message,
        "note_number": note_number,
        "category": safe_text(category)[:80],
        "status": safe_text(status)[:80],
        "created_at": safe_text(created_at)[:80],
        "modified_at": safe_text(modified_at)[:80],
        "title": safe_text(title)[:180],
        "snippet": safe_text(snippet)[:300],
        "size_bytes": size_bytes,
        "body_text": body_text,
        "truncated": truncated,
        "triage": quick_note_triage_hint(body_text or snippet),
    }


def quick_note_triage_hint(text: str) -> dict[str, Any]:
    folded = safe_text(text).casefold()
    checks: tuple[tuple[str, tuple[str, ...], str, bool], ...] = (
        (
            "Cockpit / správa projektů",
            ("cockpit", "kokpit", "projekt", "projekty", "tool", "vrstva", "stavove okno", "stavové okno"),
            "Zařadit jako návrh na Cockpit; před zápisem udělat malý plán nebo patch.",
            False,
        ),
        (
            "Dokumenty / private vault",
            ("dokument", "pdf", "smlouv", "pojist", "faktura", "scan", "scandocu", "trezor"),
            "Zkontrolovat, jestli jde o dokument, připomínku nebo metadata; nic nepřesouvat bez potvrzení.",
            True,
        ),
        (
            "Připomínka / úkol",
            ("připome", "pripome", "zavolat", "zavolej", "termín", "termin", "deadline", "úkol", "ukol"),
            "Navrhnout připomínku nebo akční položku; uložit až po potvrzení.",
            False,
        ),
        (
            "Matýsek / výuka angličtiny",
            ("matýsek", "matysek", "angličtin", "anglictin", "bunny", "benji", "forest", "lekce"),
            "Zařadit do MMTX/Matýsek English a před změnou načíst příslušný handoff.",
            False,
        ),
        (
            "Zdraví / lékárna",
            ("zdrav", "lék", "lek", "ekzém", "ekzem", "kůže", "kuze", "dávkov", "davkov"),
            "Brát jako citlivou poznámku; nedělat zdravotní závěry a případné uložení potvrdit.",
            True,
        ),
        (
            "Rodina / média",
            ("family", "rodin", "dovolen", "usa", "film", "fotk", "video", "imovie"),
            "Držet odděleně od ostatních commitů; soukromé soubory necommitovat bez výslovného souhlasu.",
            True,
        ),
        (
            "Nákup / záruka",
            ("nákup", "nakup", "objedn", "záruk", "zaruk", "eshop", "e-shop", "prodej"),
            "Navrhnout nákupní nebo záruční workflow; ukládání dokladů jen do soukromého archivu.",
            True,
        ),
        (
            "Esej / psaní",
            ("esej", "text", "kapitol", "emoce", "fraška", "fraska", "dante"),
            "Zařadit jako textový námět; před úpravami držet verzi a cílový výstup.",
            False,
        ),
        (
            "E-mail / komunikace",
            ("email", "e-mail", "mail", "zpráv", "zprav", "odeslat", "poslat"),
            "Použít e-mailový read-only nebo dvoukrokový outbound workflow podle rizika.",
            True,
        ),
    )
    for label, needles, next_step, sensitive in checks:
        if any(needle in folded for needle in needles):
            return {
                "classification": label,
                "suggested_next_step": next_step,
                "sensitive": sensitive,
                "safety_note": "Zobrazit jen bezpečný souhrn v přehledu." if sensitive else "Bez tiché akce; nejdřív návrh nebo potvrzení.",
            }
    return {
        "classification": "Nezařazeno",
        "suggested_next_step": "Přečíst detail a ručně rozhodnout, jestli z toho bude projekt, tool, reminder nebo jen poznámka.",
        "sensitive": False,
        "safety_note": "Bez tiché akce; jen návrh klasifikace.",
    }


def urgent_reminders_status(
    *,
    inbox_dir: Path = DEFAULT_ICLOUD_SHORTCUTS_INBOX,
    index_path: Path = URGENT_REMINDERS_INDEX_PATH,
    limit: int = 12,
) -> dict[str, Any]:
    inbox_exists = inbox_dir.exists()
    sync_error: OSError | ValueError | None = None
    try:
        for attempt in range(5):
            try:
                reminders = sync_urgent_reminders_index(inbox_dir=inbox_dir, index_path=index_path)
                break
            except OSError as exc:
                sync_error = exc
                if getattr(exc, "errno", None) == errno.EDEADLK and attempt < 4:
                    time.sleep(0.25 * (attempt + 1))
                    continue
                raise
        else:
            raise sync_error or OSError("iCloud sync selhal.")
    except (OSError, ValueError) as exc:
        fallback = urgent_reminders_status_from_index(index_path=index_path, limit=limit)
        if fallback["items"]:
            return {
                **fallback,
                "ok": True,
                "message": f"Důležitá připomenutí z lokálního indexu; iCloud sync teď selhal: {exc}",
                "inbox_exists": inbox_exists,
                "inbox": str(inbox_dir),
                "index": str(relative_to_project(index_path)),
                "sync_error": safe_text(str(exc))[:300],
            }
        return {
            **fallback,
            "ok": False,
            "message": f"Důležitá připomenutí se nepodařilo načíst: {exc}",
            "inbox_exists": inbox_exists,
            "inbox": str(inbox_dir),
            "index": str(relative_to_project(index_path)),
            "sync_error": safe_text(str(exc))[:300],
        }

    open_items = sorted(
        (item for item in reminders if item.status == "open"),
        key=lambda item: item.reminder_number,
        reverse=True,
    )
    shown = open_items[: max(1, limit)]
    if not inbox_exists:
        message = "Inbox pro mobilní vstupy zatím není synchronizovaný na Mac."
    elif not open_items:
        message = "Žádná otevřená důležitá připomenutí."
    else:
        message = f"{len(open_items)} otevřených důležitých připomenutí."
    return {
        "ok": True,
        "message": message,
        "inbox_exists": inbox_exists,
        "inbox": str(inbox_dir),
        "index": str(relative_to_project(index_path)),
        "counts": {"open": len(open_items), "total": len(reminders)},
        "items": [
            {
                "reminder_number": item.reminder_number,
                "priority": safe_text(item.priority)[:80],
                "status": safe_text(item.status)[:80],
                "created_at": safe_text(item.created_at)[:80],
                "modified_at": safe_text(item.modified_at)[:80],
                "title": safe_text(item.title)[:180],
                "summary": safe_text(item.summary)[:300],
                "body_text": safe_multiline_text(str(getattr(item, "body_text", item.summary)), limit=8000),
                "size_bytes": item.size_bytes,
            }
            for item in shown
        ],
    }


def urgent_reminders_status_from_index(*, index_path: Path, limit: int = 12) -> dict[str, Any]:
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        records: list[dict[str, Any]] = []
    else:
        raw_records = data.get("reminders", [])
        records = raw_records if isinstance(raw_records, list) else []
    usable = [record for record in records if isinstance(record, dict)]
    open_items = [record for record in usable if str(record.get("status", "open") or "open") == "open"]
    open_items.sort(key=lambda item: urgent_reminder_number(item), reverse=True)
    return {
        "ok": True,
        "message": "Důležitá připomenutí načtená z lokálního indexu.",
        "inbox_exists": False,
        "inbox": "",
        "index": str(relative_to_project(index_path)),
        "counts": {"open": len(open_items), "total": len(usable)},
        "items": [
            {
                "reminder_number": urgent_reminder_number(record),
                "priority": safe_text(str(record.get("priority", "urgent") or "urgent"))[:80],
                "status": safe_text(str(record.get("status", "open") or "open"))[:80],
                "created_at": safe_text(str(record.get("created_at", "") or ""))[:80],
                "modified_at": safe_text(str(record.get("modified_at", "") or ""))[:80],
                "title": safe_text(str(record.get("title", "") or ""))[:180],
                "summary": safe_text(str(record.get("summary", "") or ""))[:300],
                "body_text": safe_multiline_text(str(record.get("body_text") or record.get("summary", "") or ""), limit=8000),
                "size_bytes": urgent_reminder_size(record),
            }
            for record in open_items[: max(1, limit)]
        ],
    }


def urgent_reminder_done_action(
    reminder_number: int,
    *,
    index_path: Path = URGENT_REMINDERS_INDEX_PATH,
) -> dict[str, Any]:
    if reminder_number < 1:
        return {
            "ok": False,
            "message": "Chybí platné číslo důležité připomínky.",
            "urgent_reminders": urgent_reminders_status_from_index(index_path=index_path),
        }
    try:
        reminder = mark_urgent_reminder_done(reminder_number, index_path=index_path)
    except (OSError, ValueError) as exc:
        return {
            "ok": False,
            "message": f"Důležitou připomínku se nepodařilo označit jako splněnou: {exc}",
            "urgent_reminders": urgent_reminders_status_from_index(index_path=index_path),
        }
    if reminder is None:
        return {
            "ok": False,
            "message": f"Důležitá připomínka #{reminder_number} nebyla nalezena.",
            "urgent_reminders": urgent_reminders_status_from_index(index_path=index_path),
        }
    return {
        "ok": True,
        "reminder_number": reminder.reminder_number,
        "message": f"Důležitá připomínka #{reminder.reminder_number} označena jako splněná.",
        "urgent_reminders": urgent_reminders_status_from_index(index_path=index_path),
    }


def quick_note_number(record: dict[str, Any]) -> int:
    try:
        return int(record.get("note_number", 0) or 0)
    except (TypeError, ValueError):
        return 0


def quick_note_size(record: dict[str, Any]) -> int:
    try:
        return int(record.get("size_bytes", 0) or 0)
    except (TypeError, ValueError):
        return 0


def urgent_reminder_number(record: dict[str, Any]) -> int:
    try:
        return int(record.get("reminder_number", 0) or 0)
    except (TypeError, ValueError):
        return 0


def urgent_reminder_size(record: dict[str, Any]) -> int:
    try:
        return int(record.get("size_bytes", 0) or 0)
    except (TypeError, ValueError):
        return 0


def safe_multiline_text(value: str, *, limit: int = 8000) -> str:
    lines = [safe_text(line) for line in str(value or "").splitlines()]
    return "\n".join(lines).strip()[:limit]


def projects_status(
    path: Path = ACTIVE_PROJECTS_PATH,
    capability_map_path: Path = PROJECT_CAPABILITY_MAP_PATH,
) -> dict[str, Any]:
    try:
        projects = parse_active_projects_table(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return {
            "ok": False,
            "message": f"Seznam projektů se nepodařilo načíst: {exc}",
            "projects": [],
            "tools": [],
            "infrastructure_capabilities": [],
            "items": [],
            "summary": empty_projects_summary(),
            "catalog_summary": empty_project_catalog_summary(),
        }
    tools: list[dict[str, Any]] = []
    infrastructure_capabilities: list[dict[str, Any]] = []
    capability_error = ""
    try:
        capability_map_text = capability_map_path.read_text(encoding="utf-8")
        tools = parse_global_tools_table(capability_map_text)
        infrastructure_capabilities = parse_infrastructure_capabilities_table(capability_map_text)
    except OSError as exc:
        capability_error = f"Mapa schopností se nepodařila načíst: {exc}"
    summary = summarize_projects(projects)
    items = build_project_catalog_items(projects, tools, infrastructure_capabilities)
    catalog_summary = summarize_project_catalog(projects, tools, infrastructure_capabilities)
    active_total = int(summary.get("active_total", summary.get("total", 0)) or 0)
    return {
        "ok": True,
        "message": (
            f"{active_total} aktivních projektů, "
            f"{len(tools)} toolů a {len(infrastructure_capabilities)} infrastrukturních vrstev v paměti."
        ),
        "source": str(relative_to_project(path)),
        "capability_source": str(relative_to_project(capability_map_path)),
        "capability_error": capability_error,
        "projects": projects,
        "tools": tools,
        "infrastructure_capabilities": infrastructure_capabilities,
        "items": items,
        "summary": summary,
        "catalog_summary": catalog_summary,
    }


def project_lifecycle_action(
    *,
    project_name: str,
    lifecycle: str,
    confirmed: bool,
    path: Path = ACTIVE_PROJECTS_PATH,
    backup_dir: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    if not confirmed:
        return {
            "ok": False,
            "status": "confirmation_required",
            "message": "Změna režimu projektu nebyla potvrzena.",
        }
    name = safe_text(project_name).strip()
    if not name:
        return {"ok": False, "status": "missing_project", "message": "Chybí název projektu."}
    target = normalize_project_lifecycle(lifecycle)
    try:
        result = update_project_lifecycle_in_registry(
            project_name=name,
            lifecycle=target,
            path=path,
            backup_dir=backup_dir,
            now=now,
        )
    except FileNotFoundError:
        return {"ok": False, "status": "registry_missing", "message": "Registr projektů nejde najít."}
    except ValueError as exc:
        return {"ok": False, "status": "registry_update_failed", "message": str(exc)}

    status = projects_status(path=path)
    return {
        "ok": True,
        "status": "updated",
        "message": f"Projekt `{name}` je teď v režimu {project_lifecycle_label(target)}.",
        "project": result,
        "projects_status": status,
    }


def update_project_lifecycle_in_registry(
    *,
    project_name: str,
    lifecycle: str,
    path: Path,
    backup_dir: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    headers: list[str] = []
    target = normalize_project_lifecycle(lifecycle)
    found = False
    changed = False
    previous = ""

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells:
            continue
        if set("".join(cells)) <= {"-", ":", " "}:
            continue
        if not headers:
            headers = [normalize_project_header(cell) for cell in cells]
            continue
        row = dict(zip(headers, cells[: len(headers)], strict=False))
        if safe_text(row.get("oblast", "")) != project_name:
            continue
        found = True
        if "rezim" not in headers:
            raise ValueError("Registr projektů nemá sloupec `Rezim`.")
        lifecycle_index = headers.index("rezim")
        previous = normalize_project_lifecycle(cells[lifecycle_index] if lifecycle_index < len(cells) else "")
        if previous == target:
            break
        while len(cells) < len(headers):
            cells.append("")
        cells[lifecycle_index] = target
        newline = "\n" if line.endswith("\n") else ""
        lines[index] = "| " + " | ".join(cells) + " |" + newline
        changed = True
        break

    if not found:
        raise ValueError(f"Projekt `{project_name}` v registru není.")

    backup_path = ""
    if changed:
        backup_root = backup_dir or PROJECT_ROOT / "data" / "private" / "cockpit" / "project_registry_backups"
        backup_root.mkdir(parents=True, exist_ok=True)
        stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%d_%H%M%S")
        backup = backup_root / f"ACTIVE_PROJECTS_{stamp}.md"
        shutil.copy2(path, backup)
        path.write_text("".join(lines), encoding="utf-8")
        backup_path = str(relative_to_project(backup))

    return {
        "name": project_name,
        "previous_lifecycle": previous,
        "lifecycle": target,
        "lifecycle_label": project_lifecycle_label(target),
        "changed": changed,
        "backup": backup_path,
    }


def quantitative_status_overview(
    *,
    metrics_path: Path = QUANTITATIVE_STATUS_METRICS_PATH,
    project_root: Path = PROJECT_ROOT,
    repo_root: Path = GIT_ROOT,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    current = run_samantha_quantitative_status(
        save=False,
        project_root=project_root,
        repo_root=repo_root,
        metrics_path=metrics_path,
        runner=runner,
    )
    previous = read_last_quantitative_metric(metrics_path)
    diff = diff_quantitative_status(current=current, previous=previous)
    return {
        "ok": True,
        "message": "Systémový souhrn načten.",
        "metrics_path": str(relative_to_project(metrics_path)),
        "current": quantitative_result_to_json(current),
        "previous": previous,
        "diff": diff,
    }


def read_last_quantitative_metric(metrics_path: Path) -> dict[str, Any] | None:
    try:
        rows = read_jsonl(metrics_path)
    except OSError:
        return None
    if not rows:
        return None
    last = rows[-1]
    return last if isinstance(last, dict) else None


def quantitative_result_to_json(result) -> dict[str, Any]:
    return {
        "created_at": result.created_at,
        "git_summary": result.git_summary,
        "stored_path": str(relative_to_project(result.stored_path)) if result.stored_path else "",
        "totals": {
            "local": quantitative_stats_totals(result.local_stats),
            "git_tracked": quantitative_stats_totals(result.git_stats),
        },
        "local": quantitative_stats_to_json(result.local_stats),
        "git_tracked": quantitative_stats_to_json(result.git_stats),
    }


def quantitative_stats_totals(stats: dict[str, QuantitativeExtensionStats]) -> dict[str, int]:
    return {
        "files": sum(item.files for item in stats.values()),
        "lines": sum(item.lines for item in stats.values()),
    }


def quantitative_stats_to_json(stats: dict[str, QuantitativeExtensionStats]) -> dict[str, dict[str, int]]:
    return {key: {"files": value.files, "lines": value.lines} for key, value in stats.items()}


def diff_quantitative_status(
    *,
    current,
    previous: dict[str, Any] | None,
) -> dict[str, Any]:
    current_local = quantitative_stats_to_json(current.local_stats)
    current_git = quantitative_stats_to_json(current.git_stats)
    previous_local = extract_quantitative_stats(previous, "local")
    previous_git = extract_quantitative_stats(previous, "git_tracked")
    return {
        "totals": {
            "local": diff_totals(quantitative_stats_totals(current.local_stats), extract_quantitative_totals(previous, "local")),
            "git_tracked": diff_totals(quantitative_stats_totals(current.git_stats), extract_quantitative_totals(previous, "git_tracked")),
        },
        "local": diff_stat_rows(current_local, previous_local),
        "git_tracked": diff_stat_rows(current_git, previous_git),
    }


def extract_quantitative_stats(row: dict[str, Any] | None, key: str) -> dict[str, dict[str, int]]:
    if not row:
        return {}
    raw = row.get(key, {})
    if not isinstance(raw, dict):
        return {}
    result: dict[str, dict[str, int]] = {}
    for extension, item in raw.items():
        if not isinstance(item, dict):
            continue
        result[str(extension)] = {
            "files": int(item.get("files", 0) or 0),
            "lines": int(item.get("lines", 0) or 0),
        }
    return result


def extract_quantitative_totals(row: dict[str, Any] | None, key: str) -> dict[str, int]:
    if not row:
        return {"files": 0, "lines": 0}
    raw = row.get("totals", {})
    if not isinstance(raw, dict):
        return {"files": 0, "lines": 0}
    totals = raw.get(key, {})
    if not isinstance(totals, dict):
        return {"files": 0, "lines": 0}
    return {
        "files": int(totals.get("files", 0) or 0),
        "lines": int(totals.get("lines", 0) or 0),
    }


def diff_totals(current: dict[str, int], previous: dict[str, int]) -> dict[str, int]:
    return {
        "files": current["files"] - previous["files"],
        "lines": current["lines"] - previous["lines"],
    }


def diff_stat_rows(
    current: dict[str, dict[str, int]],
    previous: dict[str, dict[str, int]],
    limit: int = 12,
) -> list[dict[str, int | str]]:
    keys = sorted(set(current) | set(previous))
    rows: list[dict[str, int | str]] = []
    for key in keys:
        current_item = current.get(key, {"files": 0, "lines": 0})
        previous_item = previous.get(key, {"files": 0, "lines": 0})
        delta_files = current_item["files"] - previous_item["files"]
        delta_lines = current_item["lines"] - previous_item["lines"]
        if delta_files == 0 and delta_lines == 0:
            continue
        rows.append(
            {
                "extension": key,
                "files": current_item["files"],
                "lines": current_item["lines"],
                "delta_files": delta_files,
                "delta_lines": delta_lines,
            }
        )
    rows.sort(key=lambda item: (-abs(int(item["delta_lines"])), -abs(int(item["delta_files"])), str(item["extension"])))
    return rows[:limit]


def parse_active_projects_table(text: str) -> list[dict[str, Any]]:
    projects: list[dict[str, Any]] = []
    headers: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells:
            continue
        if set("".join(cells)) <= {"-", ":", " "}:
            continue
        if not headers:
            headers = [normalize_project_header(cell) for cell in cells]
            continue
        if len(cells) < len(headers):
            cells.extend([""] * (len(headers) - len(cells)))
        row = dict(zip(headers, cells[: len(headers)], strict=False))
        name = safe_text(row.get("oblast", ""))
        if not name:
            continue
        status = safe_text(row.get("stav", ""))
        next_step = safe_text(row.get("dalsi_krok", ""))
        lifecycle = normalize_project_lifecycle(row.get("rezim", ""))
        project = {
            "name": name,
            "priority": safe_text(row.get("priorita", "")),
            "lifecycle": lifecycle,
            "lifecycle_label": project_lifecycle_label(lifecycle),
            "status": status,
            "next_step": next_step,
            "memory_file": safe_text(row.get("memory_soubor", "")),
            "handoff": safe_text(row.get("handoff", "")),
            "flags": project_flags(status=status, next_step=next_step, row=row),
        }
        projects.append(project)
    return projects


def parse_global_tools_table(text: str) -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = []
    for row in parse_markdown_table_in_section(text, "Globalni schopnosti Samanthy"):
        name = safe_text(row.get("oblast", ""))
        if not name:
            continue
        tools.append(
            {
                "name": name,
                "level": safe_text(row.get("uroven", "")),
                "status": safe_text(row.get("aktualni_schopnost", "")),
                "safety_gate": safe_text(row.get("bezpecnostni_brana", "")),
            }
        )
    return tools


def parse_infrastructure_capabilities_table(text: str) -> list[dict[str, Any]]:
    capabilities: list[dict[str, Any]] = []
    for row in parse_markdown_table_in_section(text, "Infrastructure capabilities"):
        name = safe_text(row.get("capability", ""))
        if not name:
            continue
        capabilities.append(
            {
                "name": name,
                "status": safe_text(row.get("stav", "")),
                "contains": safe_text(row.get("obsahuje", "")),
                "helps": safe_text(row.get("krmi_pomaha", "")),
            }
        )
    return capabilities


def parse_markdown_table_in_section(text: str, heading: str) -> list[dict[str, str]]:
    table_lines: list[str] = []
    in_section = False
    found_table = False
    target = heading.casefold()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        heading_match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading_match:
            current_heading = heading_match.group(2).casefold()
            if current_heading == target:
                in_section = True
                table_lines = []
                found_table = False
                continue
            if in_section:
                break
        if not in_section:
            continue
        if line.startswith("|") and line.endswith("|"):
            table_lines.append(line)
            found_table = True
            continue
        if found_table and line:
            break
    return parse_markdown_table_lines(table_lines)


def parse_markdown_table_lines(lines: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    headers: list[str] = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells:
            continue
        if set("".join(cells)) <= {"-", ":", " "}:
            continue
        if not headers:
            headers = [normalize_catalog_header(cell) for cell in cells]
            continue
        if len(cells) < len(headers):
            cells.extend([""] * (len(headers) - len(cells)))
        rows.append(dict(zip(headers, cells[: len(headers)], strict=False)))
    return rows


def normalize_catalog_header(value: str) -> str:
    folded = value.casefold()
    mapping = {
        "oblast": "oblast",
        "úroveň": "uroven",
        "uroven": "uroven",
        "aktualni schopnost": "aktualni_schopnost",
        "aktuální schopnost": "aktualni_schopnost",
        "bezpecnostni brana": "bezpecnostni_brana",
        "bezpečnostní brána": "bezpecnostni_brana",
        "capability": "capability",
        "stav": "stav",
        "obsahuje": "obsahuje",
        "krmi / pomaha": "krmi_pomaha",
        "krmí / pomáhá": "krmi_pomaha",
    }
    return mapping.get(folded, safe_slug(value, default="field", limit=50).replace("-", "_"))


def build_project_catalog_items(
    projects: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    infrastructure_capabilities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for project in projects:
        status = safe_text(project.get("status", ""))
        next_step = safe_text(project.get("next_step", ""))
        memory_file = safe_text(project.get("memory_file", ""))
        handoff = safe_text(project.get("handoff", ""))
        management = project_management_signals(project)
        item = {
            "category": "project",
            "category_label": "Project",
            "name": safe_text(project.get("name", "")),
            "priority": safe_text(project.get("priority", "")),
            "lifecycle": safe_text(project.get("lifecycle", "active")),
            "lifecycle_label": safe_text(project.get("lifecycle_label", "Aktivní")),
            "status": status,
            "summary": status,
            "next_step": next_step,
            "memory_file": memory_file,
            "handoff": handoff,
            "last_worked": latest_date_hint(status, next_step, memory_file, handoff),
            "flags": project.get("flags", []),
            "management_flags": management["flags"],
            "management_status": management["status"],
            "management_reason": management["reason"],
            "needs_attention": management["needs_attention"],
            "detail_fields": [
                {"label": "Správa", "value": management["reason"]},
                {"label": "Režim", "value": safe_text(project.get("lifecycle_label", ""))},
                {"label": "Memory", "value": memory_file},
                {"label": "Handoff", "value": handoff},
                {"label": "Stav", "value": status},
                {"label": "Další krok", "value": next_step},
            ],
        }
        items.append(item)
    for tool in tools:
        status = safe_text(tool.get("status", ""))
        safety_gate = safe_text(tool.get("safety_gate", ""))
        level = safe_text(tool.get("level", ""))
        items.append(
            {
                "category": "tool",
                "category_label": "Tool",
                "name": safe_text(tool.get("name", "")),
                "level": level,
                "status": status,
                "summary": status,
                "next_step": safety_gate,
                "flags": project_catalog_flags("tool", status, safety_gate),
                "detail_fields": [
                    {"label": "Úroveň", "value": level},
                    {"label": "Schopnost", "value": status},
                    {"label": "Bezpečnostní brána", "value": safety_gate},
                ],
            }
        )
    for capability in infrastructure_capabilities:
        status = safe_text(capability.get("status", ""))
        contains = safe_text(capability.get("contains", ""))
        helps = safe_text(capability.get("helps", ""))
        items.append(
            {
                "category": "infrastructure",
                "category_label": "Infrastructure capability",
                "name": safe_text(capability.get("name", "")),
                "status": status,
                "summary": contains,
                "next_step": helps,
                "flags": project_catalog_flags("infrastructure", status, contains, helps),
                "detail_fields": [
                    {"label": "Stav", "value": status},
                    {"label": "Obsahuje", "value": contains},
                    {"label": "Krmí / pomáhá", "value": helps},
                ],
            }
        )
    return items


def project_catalog_flags(category: str, *values: str) -> list[str]:
    folded = " ".join(values).casefold()
    flags: list[str] = []
    if "pending" in folded or "koncept" in folded:
        flags.append("čeká na rozhodnutí")
    if "aktivni" in folded or "aktivní" in folded:
        flags.append("aktivní")
    if "potvrzeni" in folded or "potvrzení" in folded:
        flags.append("potvrzovací brána")
    return flags


def project_management_signals(project: dict[str, Any]) -> dict[str, Any]:
    lifecycle = normalize_project_lifecycle(safe_text(project.get("lifecycle", "active")))
    if lifecycle == "archived":
        return {
            "status": "archived",
            "reason": "Archivní projekt bez okamžité akce.",
            "flags": ["archiv"],
            "needs_attention": False,
        }
    status = safe_text(project.get("status", ""))
    next_step = safe_text(project.get("next_step", ""))
    memory_file = safe_text(project.get("memory_file", ""))
    handoff = safe_text(project.get("handoff", ""))
    folded = " ".join([status, next_step]).casefold()
    flags: list[str] = []
    if not has_project_reference(memory_file):
        flags.append("chybí memory")
    if not has_project_reference(handoff):
        flags.append("chybí handoff")
    if not has_project_reference(next_step):
        flags.append("chybí další krok")
    if any(needle in folded for needle in ("rozhodnout", "čeká", "ceka", "retest", "otestovat")):
        flags.append("čeká na Mílu")
    if any(needle in folded for needle in ("žádný aktivní vývoj", "zadny aktivni vyvoj", "hotovo / údržba", "hotovo / udrzba")):
        flags.append("údržba")

    blocking_flags = [flag for flag in flags if flag != "údržba"]
    if not blocking_flags:
        return {
            "status": "ok",
            "reason": "Projekt má uvedený další krok, memory i handoff.",
            "flags": flags,
            "needs_attention": False,
        }
    if flags == ["údržba"]:
        return {
            "status": "maintenance",
            "reason": "Projekt je v údržbě bez okamžité akce.",
            "flags": flags,
            "needs_attention": False,
        }
    return {
        "status": "needs_attention",
        "reason": "Doplnit nebo rozhodnout: " + ", ".join(blocking_flags) + ".",
        "flags": flags,
        "needs_attention": True,
    }


def has_project_reference(value: str) -> bool:
    folded = safe_text(value).strip().strip("`").casefold()
    if not folded:
        return False
    missing_values = {
        "-",
        "n/a",
        "na",
        "none",
        "zatim neni",
        "zatím není",
        "neni",
        "není",
        "zadny",
        "žádný",
    }
    return folded not in missing_values


def summarize_project_catalog(
    projects: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    infrastructure_capabilities: list[dict[str, Any]],
) -> dict[str, Any]:
    management_counts: dict[str, int] = {}
    lifecycle_counts: dict[str, int] = {}
    for project in projects:
        lifecycle = normalize_project_lifecycle(safe_text(project.get("lifecycle", "active")))
        lifecycle_counts[lifecycle] = lifecycle_counts.get(lifecycle, 0) + 1
        signals = project_management_signals(project)
        status = safe_text(signals.get("status", ""))
        management_counts[status] = management_counts.get(status, 0) + 1
    active_projects = [project for project in projects if normalize_project_lifecycle(safe_text(project.get("lifecycle", "active"))) != "archived"]
    return {
        "projects": len(active_projects),
        "projects_all": len(projects),
        "archived_projects": lifecycle_counts.get("archived", 0),
        "tools": len(tools),
        "infrastructure_capabilities": len(infrastructure_capabilities),
        "total": len(active_projects) + len(tools) + len(infrastructure_capabilities),
        "total_all": len(projects) + len(tools) + len(infrastructure_capabilities),
        "project_management": management_counts,
        "project_lifecycle": lifecycle_counts,
    }


def empty_project_catalog_summary() -> dict[str, Any]:
    return {
        "projects": 0,
        "projects_all": 0,
        "archived_projects": 0,
        "tools": 0,
        "infrastructure_capabilities": 0,
        "total": 0,
        "total_all": 0,
        "project_management": {},
        "project_lifecycle": {},
    }


def latest_date_hint(*values: str) -> str:
    dates: list[str] = []
    for value in values:
        for match in re.findall(r"\b(20\d{2})[-_](\d{2})[-_](\d{2})\b", value or ""):
            dates.append("-".join(match))
    return max(dates) if dates else ""


def normalize_project_header(value: str) -> str:
    return {
        "oblast": "oblast",
        "priorita": "priorita",
        "stav": "stav",
        "rezim": "rezim",
        "režim": "rezim",
        "zivotni cyklus": "rezim",
        "životní cyklus": "rezim",
        "lifecycle": "rezim",
        "memory soubor": "memory_soubor",
        "handoff": "handoff",
        "dalsi krok": "dalsi_krok",
        "další krok": "dalsi_krok",
    }.get(value.casefold(), safe_slug(value, default="field", limit=40).replace("-", "_"))


def normalize_project_lifecycle(value: str) -> str:
    folded = safe_text(value).strip().casefold()
    if folded in {"archiv", "archivni", "archivní", "archive", "archived"}:
        return "archived"
    if folded in {"paused", "pause", "pozastaveno", "zmrazeno", "frozen"}:
        return "paused"
    return "active"


def project_lifecycle_label(value: str) -> str:
    lifecycle = normalize_project_lifecycle(value)
    return {
        "active": "Aktivní",
        "paused": "Pozastaveno",
        "archived": "Archiv",
    }.get(lifecycle, "Aktivní")


def project_flags(status: str, next_step: str, row: dict[str, str]) -> list[str]:
    folded = " ".join([status, next_step, *row.values()]).casefold()
    flags: list[str] = []
    lifecycle = normalize_project_lifecycle(row.get("rezim", ""))
    if lifecycle == "archived":
        flags.append("archiv")
    elif lifecycle == "paused":
        flags.append("pozastaveno")
    checks = (
        ("připomenout", ("[pripomenout]", "[připomenout]", "pripomenout", "připomenout")),
        ("čeká na retest", ("ceka na retest", "čeká na retest", "rucni retest", "ruční retest", "rucne otestovat", "ručně otestovat")),
        ("hotovo/údržba", ("hotovo / udrzba", "hotovo / údržba", "zadny aktivni vyvoj", "žádný aktivní vývoj")),
        ("blokováno", ("blokov", "ceka na rozhodnuti", "čeká na rozhodnutí")),
    )
    for label, needles in checks:
        if any(needle in folded for needle in needles):
            flags.append(label)
    return flags


def summarize_projects(projects: list[dict[str, Any]]) -> dict[str, Any]:
    summary = empty_projects_summary()
    summary["total"] = len(projects)
    active_projects = [
        project
        for project in projects
        if normalize_project_lifecycle(safe_text(project.get("lifecycle", "active"))) != "archived"
    ]
    summary["active_total"] = len(active_projects)
    summary["archived_total"] = len(projects) - len(active_projects)
    for project in projects:
        lifecycle = normalize_project_lifecycle(safe_text(project.get("lifecycle", "active")))
        summary["lifecycle_counts"][lifecycle] = summary["lifecycle_counts"].get(lifecycle, 0) + 1
        if lifecycle == "archived":
            continue
        priority = str(project.get("priority", "") or "nezadáno")
        summary["priority_counts"][priority] = summary["priority_counts"].get(priority, 0) + 1
        flags = project.get("flags", [])
        if isinstance(flags, list):
            for flag in flags:
                summary["flag_counts"][str(flag)] = summary["flag_counts"].get(str(flag), 0) + 1
    return summary


def empty_projects_summary() -> dict[str, Any]:
    return {
        "total": 0,
        "active_total": 0,
        "archived_total": 0,
        "priority_counts": {},
        "flag_counts": {},
        "lifecycle_counts": {},
    }


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
DOCUMENT_INTAKE_LARGE_PDF_BYTES = 150_000
DOCUMENT_INTAKE_EMAIL_POSITIVE_TERMS = (
    "smlouv",
    "pojist",
    "pojišt",
    "faktura",
    "invoice",
    "doklad",
    "účten",
    "ucten",
    "upom",
    "splat",
    "platba",
    "předpis",
    "predpis",
    "vyúčt",
    "vyuct",
    "dokument",
    "potvrzen",
    "protokol",
    "revize",
    "servis",
    "výzva",
    "vyzva",
    "úřad",
    "urad",
    "daň",
    "dan",
    "pdf",
    "příloha",
    "priloha",
    "contract",
    "policy",
    "reminder",
    "payment",
    "statement",
    "receipt",
)
DOCUMENT_INTAKE_EMAIL_NEGATIVE_TERMS = (
    "newsletter",
    "akce",
    "sleva",
    "slev",
    "výprodej",
    "vyprodej",
    "nabídka",
    "nabidka",
    "promo",
    "reklam",
    "marketing",
    "krmivo",
    "granule",
    "chovat",
    "mazlíček",
    "mazlicek",
    "pet",
    "feed",
    "notifikace",
    "notification",
    "upozornění",
    "upozorneni",
    "aplikace",
    "app",
    "novinky",
    "tipy",
)


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
        stable_key = email_processing_stable_key(
            str(item.get("provider", "")),
            str(item.get("folder", "")),
            str(item.get("uid", "")),
        )
        if stable_key:
            keys.add(stable_key)
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
            stable_key = email_processing_stable_key(
                str(raw_item.get("provider", "")),
                str(raw_item.get("folder", "INBOX")),
                str(raw_item.get("uid", "")),
            )
            if stable_key:
                keys.add(stable_key)
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
    attachments = tuple(getattr(header, "attachments", ()) or ())
    attachment_items = [
        {
            "filename": attachment.filename,
            "content_type": attachment.content_type,
            "size_bytes": attachment.size_bytes,
            "part_id": attachment.part_id,
            "disposition": attachment.disposition,
        }
        for attachment in attachments
    ]
    pdf_attachments = [
        attachment
        for attachment in attachments
        if "pdf" in f"{attachment.filename} {attachment.content_type}".casefold()
    ]
    large_pdf_attachments = [
        attachment
        for attachment in pdf_attachments
        if isinstance(attachment.size_bytes, int) and attachment.size_bytes >= DOCUMENT_INTAKE_LARGE_PDF_BYTES
    ]
    item = {
        "category": category,
        "provider": source,
        "folder": folder,
        "uid": str(header.internal_id),
        "date": header.date,
        "sender": header.sender,
        "subject": header.subject or "(bez předmětu)",
        "reason": "nová hlavička z read-only kontroly",
        "action": "",
        "is_new_header": True,
        "attachments": attachment_items,
        "attachment_count": len(attachments),
        "pdf_attachment_count": len(pdf_attachments),
        "large_pdf_attachment_count": len(large_pdf_attachments),
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


def document_intake_email_candidate_filter(item: dict[str, Any]) -> dict[str, Any]:
    subject = str(item.get("subject", ""))
    sender = str(item.get("sender", ""))
    category = str(item.get("category", ""))
    reason = str(item.get("reason", ""))
    value = f"{subject} {sender} {category} {reason}".casefold()
    matched_positive = sorted({term for term in DOCUMENT_INTAKE_EMAIL_POSITIVE_TERMS if term in value})
    matched_negative = sorted({term for term in DOCUMENT_INTAKE_EMAIL_NEGATIVE_TERMS if term in value})
    raw_attachments = item.get("attachments", [])
    attachments = raw_attachments if isinstance(raw_attachments, list) else []
    pdf_attachment_count = int(item.get("pdf_attachment_count", 0) or 0)
    large_pdf_attachment_count = int(item.get("large_pdf_attachment_count", 0) or 0)

    score = 0
    reasons: list[str] = []
    if large_pdf_attachment_count:
        score += 8
        reasons.append(f"velké PDF přílohy: {large_pdf_attachment_count}")
    elif pdf_attachment_count:
        score += 6
        reasons.append(f"PDF přílohy: {pdf_attachment_count}")
    elif attachments:
        score += 1
        reasons.append(f"přílohy: {len(attachments)}")
    if category in {"pojištění/smlouvy", "úřady/daně"}:
        score += 5
        reasons.append(category)
    elif category == "faktury/e-shopy":
        score += 3
        reasons.append("faktura/platba/e-shop")
    if matched_positive:
        score += min(6, len(matched_positive) * 2)
        reasons.append("dokumentové slovo: " + ", ".join(matched_positive[:3]))
    if "pdf" in value or "příloha" in value or "priloha" in value:
        score += 3
        reasons.append("možná PDF příloha")
    if matched_negative and not matched_positive and category == "ostatní":
        score -= 5
        reasons.append("pravděpodobný marketing/notifikace")
    elif matched_negative:
        score -= 1

    include = score >= 2
    if include and not reasons:
        reasons.append("slabý dokumentový kandidát")
    label = "Dokumentový kandidát" if include else "Potlačeno filtrem"
    return {
        "include": include,
        "score": score,
        "label": label,
        "reasons": reasons[:4],
        "matched_positive": matched_positive[:8],
        "matched_negative": matched_negative[:8],
    }


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
    suppressed_known_ids = sorted(known & (decided_keys | completed_keys))
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
        "suppressed_known_ids": suppressed_known_ids,
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
            "title": "E-maily",
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
        "title": "E-maily",
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
                    "date": str(item.get("date", "")),
                    "sender": str(item.get("sender", "")),
                    "subject": str(item.get("subject", "")),
                    "status": str(item.get("status", "")),
                    "archive_id": str(item.get("archive_id", "")),
                    "attachments_imported": int(item.get("attachments_imported", 0) or 0),
                    "attachment_count": int(item.get("attachment_count", 0) or 0),
                    "pdf_attachment_count": int(item.get("pdf_attachment_count", 0) or 0),
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
        "date": safe_text(str(item.get("date", "")))[:120],
        "sender": redact_email_addresses(safe_text(str(item.get("sender", ""))))[:180],
        "subject": safe_text(str(item.get("subject", "")))[:180],
        "attachment_count": int(item.get("attachment_count", 0) or 0),
        "pdf_attachment_count": int(item.get("pdf_attachment_count", 0) or 0),
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
    document_work = document_work_status(downloads=downloads)
    document_intake = document_intake_status(downloads=downloads)
    document_cases = document_cases_status()
    document_classification = document_classification_status()
    document_due_candidates = document_due_candidates_status()
    reminders = reminders_status()
    urgent = urgent_reminders_status()
    backup_status = backup_activity_status()
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "downloads": downloads,
        "document_work": document_work,
        "document_intake": document_intake,
        "document_cases": document_cases,
        "document_classification": document_classification,
        "document_due_candidates": document_due_candidates,
        "action_queue": action_queue_status(document_work=document_work, reminders=reminders, urgent_reminders=urgent),
        "backup": backup_status["message"],
        "backup_status": backup_status,
        "vault": document_vault_status_summary(),
        "reminders": reminders,
        "urgent_reminders": urgent,
        "scandocu": probe_scandocu(),
        "voice_mode": load_voice_mode_status(),
        "voice_bridge": adam_voice_bridge_status(),
        "git": git_status_summary(),
    }


def adam_voice_bridge_status(
    *,
    marker_path: Path = CURRENT_CODEX_TTY_PATH,
    codex_tty_discoverer: Callable[[], list[str]] = discover_codex_ttys,
    screen_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    expected_codex_session_limit: int = 3,
) -> dict[str, Any]:
    marker: dict[str, Any] = {}
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        marker = {}

    marked_tty = normalize_tty(str(marker.get("tty") or ""))
    try:
        codex_ttys = [normalize_tty(item) for item in codex_tty_discoverer()]
    except Exception:
        codex_ttys = []
    codex_ttys = [item for item in codex_ttys if item and item != "??"]

    screen_status = "unknown"
    screen_message = "screen stav nelze zjistit"
    try:
        completed = screen_runner(
            ["screen", "-ls"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        screen_output = f"{completed.stdout}\n{completed.stderr}".strip()
        if completed.returncode == 0:
            screen_status = "running"
            screen_message = "screen běží"
        elif "No Sockets found" in screen_output:
            screen_status = "not_running"
            screen_message = "screen neběží"
        else:
            screen_status = "unknown"
            screen_message = screen_output or "screen stav nelze zjistit"
    except (OSError, subprocess.TimeoutExpired) as exc:
        screen_message = str(exc)

    warnings: list[str] = []
    effective_tty = marked_tty if marked_tty in codex_ttys else ""
    if not effective_tty and marked_tty and len(codex_ttys) == 1:
        effective_tty = codex_ttys[0]
    if not marked_tty:
        warnings.append("není označené cílové TTY")
    elif marked_tty not in codex_ttys:
        if effective_tty:
            warnings.append(f"označené TTY {marked_tty} je staré; použije se jediná aktivní Codex relace {effective_tty}")
        else:
            warnings.append(f"označené TTY {marked_tty} není mezi aktivními Codex relacemi")
    if len(codex_ttys) > expected_codex_session_limit:
        warnings.append(f"běží {len(codex_ttys)} Codex relací, očekáváno nejvýše {expected_codex_session_limit}")
    if screen_status == "not_running":
        warnings.append("screen neběží")

    target = effective_tty or marked_tty or "nezjištěno"
    marker_label = marked_tty or "nezjištěno"
    message = (
        f"Bridge cílí na {target} (marker: {marker_label}). Codex relace: {len(codex_ttys)} "
        f"(limit {expected_codex_session_limit}). {screen_message}."
    )
    if warnings:
        message = f"{message} Pozor: {', '.join(warnings)}."

    return {
        "ok": True,
        "status": "warn" if warnings else "ok",
        "message": message,
        "marked_tty": marked_tty,
        "effective_tty": effective_tty,
        "marked_at": str(marker.get("marked_at") or ""),
        "parent_pid": marker.get("parent_pid"),
        "codex_ttys": codex_ttys,
        "codex_tty_count": len(codex_ttys),
        "expected_codex_session_limit": expected_codex_session_limit,
        "screen_status": screen_status,
        "screen_message": screen_message,
        "warnings": warnings,
    }


def set_adam_voice_bridge_marker_action(
    tty: str,
    *,
    marker_path: Path = CURRENT_CODEX_TTY_PATH,
    codex_tty_discoverer: Callable[[], list[str]] = discover_codex_ttys,
) -> dict[str, Any]:
    target_tty = normalize_tty(str(tty or ""))
    if not target_tty or target_tty == "??":
        return {
            "ok": False,
            "status": "missing_tty",
            "message": "Chybí cílové TTY pro voice bridge.",
        }
    try:
        codex_ttys = [normalize_tty(item) for item in codex_tty_discoverer()]
    except Exception:
        codex_ttys = []
    codex_ttys = [item for item in codex_ttys if item and item != "??"]
    if target_tty not in codex_ttys:
        return {
            "ok": False,
            "status": "tty_not_active",
            "message": f"TTY {target_tty} není mezi aktivními Codex relacemi.",
            "target_tty": target_tty,
            "codex_ttys": codex_ttys,
        }
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text(
        json.dumps(
            {
                "tty": target_tty,
                "marked_at": datetime.now(timezone.utc).isoformat(),
                "parent_pid": os.getpid(),
                "note": "Private runtime marker for Adam Voice Mode terminal bridge, set from Cockpit.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "ok": True,
        "status": "marker_updated",
        "message": f"Voice bridge marker byl nastaven na {target_tty}.",
        "marked_tty": target_tty,
        "codex_ttys": codex_ttys,
    }


def action_queue_status(
    document_work: dict[str, Any] | None = None,
    reminders: dict[str, Any] | None = None,
    urgent_reminders: dict[str, Any] | None = None,
    limit: int = 8,
) -> dict[str, Any]:
    work = document_work if document_work is not None else document_work_status()
    reminder_data = reminders if reminders is not None else reminders_status()
    urgent_data = urgent_reminders if urgent_reminders is not None else {"items": []}
    items: list[dict[str, Any]] = []

    for urgent_item in (urgent_data.get("items") or [])[:3]:
        title = safe_text(str(urgent_item.get("summary") or urgent_item.get("title") or ""))[:180]
        created = safe_text(str(urgent_item.get("created_at", "")))[:60]
        items.append(
            {
                "kind": "urgent_reminder",
                "priority": 1,
                "title": title or "Důležité připomenutí",
                "detail": f"Mobilní urgentní vstup{': ' + created if created else ''}",
                "action": "open_urgent_reminders",
                "action_label": "Otevřít připomenutí",
            }
        )

    for conflict in (reminder_data.get("conflicts") or [])[:3]:
        conflict_items = conflict.get("items") or []
        asset = safe_text(str(conflict.get("asset", "")))[:120]
        coverage_start = safe_text(str(conflict.get("coverage_start", "")))[:40]
        items.append(
            {
                "kind": "payment_conflict",
                "priority": 1,
                "title": f"Konflikt plateb{': ' + asset if asset else ''}",
                "detail": (
                    f"{len(conflict_items)} otevřené platební připomínky"
                    f"{' od ' + coverage_start if coverage_start else ''}. Nekonat platbu bez porovnání."
                ),
                "action": "open_reminders",
                "action_label": "Otevřít připomenutí",
            }
        )

    for problem in (work.get("problems") or [])[:3]:
        name = safe_text(str(problem.get("name", "")))[:180]
        label = safe_text(str(problem.get("problem_label") or problem.get("status") or "problém"))[:80]
        modified = safe_text(str(problem.get("modified_at", "")))[:60]
        items.append(
            {
                "kind": "document_problem",
                "priority": 1,
                "title": name or "Dokument vyžaduje ruční kontrolu",
                "detail": f"{label}{' | ' + modified if modified else ''}",
                "action": "open_scandocu",
                "action_label": "Otevřít ScanDocu",
            }
        )

    for pdf in (work.get("new_pdfs") or [])[:3]:
        name = safe_text(str(pdf.get("name", "")))[:180]
        modified = safe_text(str(pdf.get("modified_at", "")))[:60]
        items.append(
            {
                "kind": "new_pdf",
                "priority": 2,
                "title": name or "Nové PDF ve Downloads",
                "detail": f"Nový dokument čeká na zpracování{': ' + modified if modified else '.'}",
                "action": "open_scandocu",
                "action_label": "Zpracovat",
            }
        )

    review = work.get("review") or {}
    for review_item in (review.get("next_items") or [])[:3]:
        title = safe_text(str(review_item.get("title") or review_item.get("document_id") or ""))[:180]
        domain = safe_text(str(review_item.get("domain", "other")))[:60]
        document_type = safe_text(str(review_item.get("document_type", "document")))[:60]
        items.append(
            {
                "kind": "document_review",
                "priority": 2,
                "title": title or "Uložený dokument k revizi",
                "detail": f"{domain} / {document_type}",
                "action": "open_scandocu_review",
                "action_label": "Revidovat",
            }
        )

    groups = reminder_data.get("groups") or {}
    for group_name, label, priority in [
        ("overdue", "Po termínu", 1),
        ("today", "Dnes", 2),
        ("soon", "Brzy", 3),
    ]:
        for reminder in (groups.get(group_name) or [])[:2]:
            title = safe_text(str(reminder.get("title", "")))[:180]
            due_date = safe_text(str(reminder.get("due_date", "")))[:40]
            amount = safe_text(str(reminder.get("amount_due", "")))[:80]
            detail_parts = [label]
            if due_date:
                detail_parts.append(due_date)
            if amount:
                detail_parts.append(amount)
            items.append(
                {
                    "kind": "reminder",
                    "priority": priority,
                    "title": title or "Otevřená připomínka",
                    "detail": " | ".join(detail_parts),
                    "action": "open_reminders",
                    "action_label": "Otevřít připomenutí",
                }
            )

    items.sort(key=lambda item: (int(item.get("priority", 9)), kind_rank(str(item.get("kind", "")))))
    limited_items = items[: max(0, limit)]
    counts = {
        "total": len(items),
        "shown": len(limited_items),
        "priority_1": sum(1 for item in items if item.get("priority") == 1),
        "priority_2": sum(1 for item in items if item.get("priority") == 2),
        "priority_3": sum(1 for item in items if item.get("priority") == 3),
    }
    if not limited_items:
        message = "Žádná urgentní akce."
    elif counts["priority_1"]:
        message = f"{counts['priority_1']} akutních položek k řešení."
    else:
        message = f"{len(limited_items)} navržených dalších kroků."
    return {"ok": True, "items": limited_items, "counts": counts, "message": message}


def kind_rank(kind: str) -> int:
    ranks = {
        "urgent_reminder": 0,
        "payment_conflict": 1,
        "document_problem": 2,
        "new_pdf": 3,
        "document_review": 4,
        "reminder": 5,
    }
    return ranks.get(kind, 99)


def document_consistency_status() -> dict[str, Any]:
    try:
        result = run_document_consistency_audit()
    except (OSError, ValueError) as exc:
        result = {
            "ok": False,
            "scope": "insurance_auto",
            "fact_count": 0,
            "finding_count": 0,
            "severity_counts": {},
            "findings": [],
            "message": str(exc),
        }
    return {**result, "summary_text": format_document_consistency_audit(result)}


def resolve_consistency_finding_action(*, finding_id: str, reason: str, status: str = "resolved") -> dict[str, Any]:
    decision = save_audit_decision(finding_id=finding_id, status=status, reason=reason)
    if not decision.get("ok"):
        return {**decision, "consistency": document_consistency_status()}
    return {**decision, "consistency": document_consistency_status()}


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
                        "amount_due": safe_text(str(item.get("amount_due", "")))[:80],
                        "amount_note": safe_text(str(item.get("amount_note", "")))[:240],
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


def cancel_payment_reminder_action(
    reminder_id: str,
    *,
    reason: str = "",
    evidence_archive_id: str = "",
    reminders_path: Path = DEFAULT_REMINDERS_PATH,
    archive_directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
) -> dict[str, Any]:
    clean_id = reminder_id.strip()
    if not clean_id:
        return {"ok": False, "message": "Chybí id připomínky.", "reminders": reminders_status(path=reminders_path)}

    store = load_reminders_store(reminders_path)
    reminder = find_reminder_record_in_store(clean_id, store)
    if reminder is None:
        return {"ok": False, "message": "Připomínka nebyla nalezena.", "reminders": reminders_status(path=reminders_path)}
    if not reminder_is_payment_related(reminder):
        return {
            "ok": False,
            "message": "Připomínka nevypadá jako platební/pojistná připomínka.",
            "reminders": reminders_status(path=reminders_path),
        }

    evidence = email_archive_evidence_summary(
        evidence_archive_id=evidence_archive_id or "latest",
        archive_directory=archive_directory,
    )
    if evidence is None:
        return {
            "ok": False,
            "message": "E-mailový důkaz nebyl nalezen v EmailArchiveVault.",
            "reminders": reminders_status(path=reminders_path),
        }

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    resolution_reason = safe_text(reason).strip() or (
        "Pojišťovna akceptovala odstoupení od duplicitní nebo nevýhodné smlouvy."
    )
    reminder["status"] = "cancelled"
    reminder["resolution"] = {
        "status": "cancelled",
        "reason": resolution_reason,
        "resolved_at": now,
        "resolved_by": "samantha_cockpit",
    }
    reminder["evidence"] = evidence
    write_reminders_store(store, path=reminders_path)
    return {
        "ok": True,
        "reminder_id": safe_text(str(reminder.get("id", ""))),
        "reminder_ref": reminder_reference(str(reminder.get("id", ""))),
        "evidence": evidence,
        "message": "Platební připomínka byla uzavřena jako zrušená a e-mail byl připojen jako důkaz.",
        "reminders": reminders_status(path=reminders_path),
    }


def find_reminder_record_in_store(reminder_id: str, store: dict[str, list[dict[str, Any]]]) -> dict[str, Any] | None:
    clean_id = reminder_id.strip()
    if not clean_id:
        return None
    for reminder in store.get("reminders", []):
        if not isinstance(reminder, dict):
            continue
        stored_id = str(reminder.get("id", ""))
        if stored_id == clean_id or reminder_reference(stored_id) == clean_id:
            return reminder
    return None


def email_archive_evidence_summary(
    *,
    evidence_archive_id: str,
    archive_directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
) -> dict[str, Any] | None:
    archive_id = str(evidence_archive_id).strip()
    if not archive_id:
        return None
    if archive_id == "latest":
        latest = latest_email_archive_metadata_path(archive_directory=archive_directory)
        if latest is None:
            return None
        metadata_path = latest
        archive_id = latest.parent.name
    else:
        if "/" in archive_id or "\\" in archive_id or archive_id.startswith("."):
            return None
        metadata_path = archive_directory / archive_id / "metadata.json"

    try:
        root = archive_directory.resolve(strict=True)
        resolved_metadata = metadata_path.resolve(strict=True)
    except OSError:
        return None
    if root not in resolved_metadata.parents:
        return None
    try:
        metadata = read_json_file(resolved_metadata)
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    return {
        "type": "email_archive",
        "archive_id": str(metadata.get("archive_id") or archive_id)[:180],
        "archive_path": str(relative_to_project(resolved_metadata.parent)),
        "metadata_path": str(relative_to_project(resolved_metadata)),
        "subject": safe_text(str(metadata.get("subject", "")))[:240],
        "sender": redact_email_addresses(safe_text(str(metadata.get("from", ""))))[:180],
        "email_date": safe_text(str(metadata.get("date", "")))[:120],
        "archived_at": safe_text(str(metadata.get("archived_at", "")))[:80],
    }


def latest_email_archive_metadata_path(*, archive_directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR) -> Path | None:
    candidates = [path for path in archive_directory.glob("*/metadata.json") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def reminder_source_detail_action(
    reminder_id: str,
    reminders_path: Path = DEFAULT_REMINDERS_PATH,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    archive_directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
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
    if source_type == "email_archive":
        return reminder_email_archive_source_detail(base=base, source=source, archive_directory=archive_directory)
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
    if preferred == "seznam":
        local_detail = local_seznam_email_source_detail(uid=uid, folder=folder)
        if local_detail is not None:
            return {
                **base,
                "ok": True,
                "kind": "email",
                "message": "E-mail dohledán v lokálním Seznam katalogu a cache příloh.",
                "email": local_detail,
            }

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


def reminder_email_archive_source_detail(
    *,
    base: dict[str, Any],
    source: dict[str, Any],
    archive_directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
) -> dict[str, Any]:
    archive_id = safe_text(str(source.get("uid", ""))).strip()
    if not archive_id or "/" in archive_id or "\\" in archive_id or archive_id.startswith("."):
        return {**base, "ok": False, "kind": "email_archive", "message": "Zdrojový e-mailový archiv nemá bezpečné ID."}
    evidence = email_archive_evidence_summary(evidence_archive_id=archive_id, archive_directory=archive_directory)
    if evidence is None:
        return {**base, "ok": False, "kind": "email_archive", "message": "E-mailový archiv nebyl nalezen."}
    attachments_path = archive_directory / archive_id / "attachments" / "attachments.json"
    attachments: list[dict[str, Any]] = []
    try:
        raw_attachments = read_json_file(attachments_path).get("attachments", [])
    except (OSError, ValueError, json.JSONDecodeError):
        raw_attachments = []
    if isinstance(raw_attachments, list):
        for attachment in raw_attachments[:12]:
            if not isinstance(attachment, dict):
                continue
            attachments.append(
                {
                    "filename": safe_text(str(attachment.get("filename", "")))[:240],
                    "content_type": safe_text(str(attachment.get("content_type", "")))[:80],
                    "size_bytes": attachment.get("size_bytes"),
                    "part_id": safe_text(str(attachment.get("part_id", "")))[:40],
                }
            )
    return {
        **base,
        "ok": True,
        "kind": "email_archive",
        "message": "Zdroj připomínky je uložený lokální e-mailový archiv.",
        "email": {
            "provider": "archive",
            "folder": "",
            "uid": archive_id,
            "subject": evidence.get("subject", ""),
            "sender": evidence.get("sender", ""),
            "date": evidence.get("email_date", ""),
            "body_text": "Tělo e-mailu je uložené lokálně v EmailArchiveVault; v Cockpitu se ukazují jen bezpečná metadata.",
            "attachments": attachments,
        },
        "archive": evidence,
    }


def local_seznam_email_source_detail(uid: str, folder: str) -> dict[str, Any] | None:
    row = local_seznam_email_catalog_row(uid=uid)
    attachment_dir = LOCAL_SEZNAM_EMAIL_DIR / "attachments" / safe_email_folder_part(folder) / f"uid_{uid}"
    attachments = local_email_attachment_details(attachment_dir)
    if row is None and not attachments:
        return None
    return {
        "provider": "seznam",
        "folder": safe_text(folder or str(row.get("folder", "")) if row else folder)[:80],
        "uid": safe_text(uid)[:80],
        "subject": safe_text(str(row.get("subject", "")) if row else "")[:300],
        "sender": safe_text(str(row.get("sender", "")) if row else "")[:240],
        "date": safe_text(str(row.get("date", "")) if row else "")[:160],
        "body_text": (
            "Lokální rychlý náhled ze Seznam katalogu. Pro plné tělo e-mailu použít "
            "read-only načtení e-mailu; PDF přílohy jsou níže vypsané z lokální cache."
        ),
        "attachments": attachments,
    }


def safe_email_folder_part(folder: str) -> str:
    cleaned = safe_text(folder or "INBOX").replace("/", "_").replace("\\", "_").strip()
    return cleaned[:80] or "INBOX"


def local_seznam_email_catalog_row(uid: str) -> dict[str, str] | None:
    catalog_paths = [
        LOCAL_SEZNAM_EMAIL_DIR / "seznam_pojisteni_smlouvy_2011_2026.csv",
        LOCAL_SEZNAM_EMAIL_DIR / "seznam_pojisteni_only_2011_2026.csv",
        LOCAL_SEZNAM_EMAIL_DIR / "seznam_pojisteni_smlouvy_priority_2011_2026.csv",
    ]
    for path in catalog_paths:
        if not path.exists():
            continue
        try:
            with path.open("r", encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    if str(row.get("uid", "")).strip() == uid:
                        return dict(row)
        except OSError:
            continue
    return None


def local_email_attachment_details(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or not path.is_dir():
        return []
    attachments: list[dict[str, Any]] = []
    for item in sorted(path.iterdir()):
        if not item.is_file() or item.name == "attachments_manifest.json":
            continue
        try:
            size = item.stat().st_size
        except OSError:
            size = 0
        content_type = "application/pdf" if item.suffix.casefold() == ".pdf" else "application/octet-stream"
        attachments.append(
            {
                "filename": safe_text(item.name)[:240],
                "content_type": content_type,
                "size_bytes": size,
                "stored_path": safe_text(str(relative_to_project(item)))[:500],
            }
        )
    return attachments


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
            "payment_options": document_payment_options(text),
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


def document_due_candidates_status(
    *,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    reminders_path: Path = DEFAULT_REMINDERS_PATH,
    archive_directory: Path | None = None,
    today: date | None = None,
    limit: int = 8,
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
    candidates = document_candidates + email_candidates
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
        "document_candidate_count": len(document_candidates),
        "email_candidate_count": len(email_candidates),
        "actionable_count": len(actionable),
        "already_reminded_count": len(already),
        "past_count": len(past),
        "items": [public_document_due_candidate(item) for item in shown],
        "truncated": len(candidates) > len(shown),
        "message": (
            f"Termíny: {len(actionable)} ke schválení, {len(already)} už hlídáno, "
            f"{len(past)} prošlé bez nové připomínky."
        ),
    }


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


def public_document_case_reminder(raw: dict[str, Any], today: date) -> dict[str, Any]:
    item = reminder_status_item(raw, today)
    item.pop("id", None)
    return item


def public_document_case_conflict(conflict: dict[str, Any]) -> dict[str, Any]:
    public = dict(conflict)
    public["items"] = [
        {key: value for key, value in item.items() if key != "id"}
        for item in conflict.get("items", [])
        if isinstance(item, dict)
    ]
    return public


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
        signals.append(
            {
                "level": "bad",
                "label": "Konflikt",
                "detail": f"{conflict_count} konfliktů v připomínkách nebo platbách.",
                "next_action": "Porovnat konfliktní podklady a nekonat platbu naslepo.",
            }
        )
    if actionable_count:
        signals.append(
            {
                "level": "warn",
                "label": "Termíny ke schválení",
                "detail": f"{actionable_count} termínů z dokumentů čeká na rozhodnutí.",
                "next_action": "Ověřit, zda jde o skutečný závazek, a případně vytvořit připomínku.",
            }
        )
    if review_document_count:
        signals.append(
            {
                "level": "warn",
                "label": "Dokumenty k revizi",
                "detail": f"{review_document_count} dokumentů v case není potvrzeno jako OK.",
                "next_action": "Otevřít dokumenty k revizi a doplnit stav čtení.",
            }
        )
    if reminder_count:
        signals.append(
            {
                "level": "ok",
                "label": "Otevřené hlídání",
                "detail": f"{reminder_count} otevřených připomínek je navázáno na case.",
                "next_action": "Bez nové akce, pokud připomínka odpovídá platnému závazku.",
            }
        )
    if already_count:
        signals.append(
            {
                "level": "ok",
                "label": "Termíny už hlídané",
                "detail": f"{already_count} termínů už má existující připomínku.",
                "next_action": "Nevytvářet duplicitní připomínku.",
            }
        )
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
        signals.append(
            {
                "level": "ok",
                "label": "Bez akčního nálezu",
                "detail": "Case nemá konflikt, nový termín ke schválení ani dokument k revizi.",
                "next_action": "Nic akutního.",
            }
        )
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
        if key not in {"document_id", "archive_id", "reminder_id"}
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
EMAIL_ARCHIVE_AMOUNT_PATTERN = re.compile(r"\b([0-9]{1,3}(?:[ \u00a0]\d{3})*(?:,\d{1,2})?\s*K[čc])\b")


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
        archived_at = parse_email_archive_date(str(metadata.get("archived_at", "") or metadata.get("date", "")))
        if archived_at is not None and (today - archived_at).days > max_age_days:
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
        status = "already_reminded" if reminder is not None else "ready"
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
                "status_label": "ke schválení" if status == "ready" else "už hlídáno",
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
    amounts = [safe_text(match.group(1)).replace(" .", " ") for match in EMAIL_ARCHIVE_AMOUNT_PATTERN.finditer(text)]
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


def create_document_due_reminder_action(
    *,
    candidate_ref: str,
    title: str = "",
    notes: str = "",
    priority: str = "",
    confirmed: bool = False,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    reminders_path: Path = DEFAULT_REMINDERS_PATH,
    archive_directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
    today: date | None = None,
) -> dict[str, Any]:
    if not confirmed:
        return {"ok": False, "message": "Chybí potvrzení vytvoření připomínky."}
    today_date = today or date.today()
    candidates = build_document_due_candidates(vault_dir=vault_dir, reminders_path=reminders_path, today=today_date)
    candidates.extend(
        build_email_archive_due_candidates(
            archive_directory=archive_directory,
            reminders_path=reminders_path,
            today=today_date,
        )
    )
    candidate = next((item for item in candidates if item["candidate_ref"] == candidate_ref.strip()), None)
    if candidate is None:
        return {
            "ok": False,
            "message": "Termínový kandidát nebyl nalezen.",
            "document_due_candidates": document_due_candidates_status(
                vault_dir=vault_dir,
                reminders_path=reminders_path,
                today=today_date,
            ),
        }
    if candidate.get("source_kind") == "email_archive":
        return create_email_archive_due_reminder_action(
            candidate=candidate,
            title=title,
            notes=notes,
            priority=priority,
            vault_dir=vault_dir,
            reminders_path=reminders_path,
            archive_directory=archive_directory,
            today=today_date,
        )
    if candidate["status"] == "already_reminded":
        return {
            "ok": False,
            "message": "Pro tento termín už připomínka existuje.",
            "document_due_candidates": document_due_candidates_status(
                vault_dir=vault_dir,
                reminders_path=reminders_path,
                today=today_date,
            ),
        }
    if candidate["status"] == "past_due":
        return {
            "ok": False,
            "message": "Termín je už v minulosti; novou připomínku z něj teď nevytvářím.",
            "document_due_candidates": document_due_candidates_status(
                vault_dir=vault_dir,
                reminders_path=reminders_path,
                today=today_date,
            ),
        }

    reminder_id = str(candidate["reminder_id"])
    reminder_title = safe_text(title.strip())[:160] or str(candidate["suggested_title"])
    reminder_notes = safe_text(notes.strip())[:700] or str(candidate["suggested_notes"])
    result_text = save_document_due_reminder_summary(
        document_id=str(candidate["document_id"]),
        title=reminder_title,
        due_date=str(candidate["date"]),
        due_date_type=str(candidate["type"]),
        notes=reminder_notes,
        priority=priority or str(candidate["priority"]),
        user_confirmed=True,
        confirmation_text=f"Potvrzuji, uloz pripominku {reminder_id}.",
        reminders_path=reminders_path,
    )
    ok = result_text.startswith("Ulozeno:")
    if ok:
        enrich_document_due_reminder(reminder_id=reminder_id, candidate=candidate, reminders_path=reminders_path)
    return {
        "ok": ok,
        "reminder_ref": reminder_reference(reminder_id),
        "message": safe_text(result_text),
        "document_due_candidates": document_due_candidates_status(
            vault_dir=vault_dir,
            reminders_path=reminders_path,
            today=today_date,
        ),
        "reminders": reminders_status(path=reminders_path, today=today_date),
    }


def create_email_archive_due_reminder_action(
    *,
    candidate: dict[str, Any],
    title: str = "",
    notes: str = "",
    priority: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    reminders_path: Path = DEFAULT_REMINDERS_PATH,
    archive_directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
    today: date,
) -> dict[str, Any]:
    if candidate["status"] == "already_reminded":
        return {
            "ok": False,
            "message": "Pro tento e-mailový termín už připomínka existuje.",
            "document_due_candidates": document_due_candidates_status(
                vault_dir=vault_dir,
                reminders_path=reminders_path,
                archive_directory=archive_directory,
                today=today,
            ),
        }
    reminder_id = str(candidate["reminder_id"])
    reminder_title = safe_text(title.strip())[:160] or str(candidate["suggested_title"])
    reminder_notes = safe_text(notes.strip())[:700] or str(candidate["suggested_notes"])
    store = load_reminders_store(reminders_path)
    if any(item.get("id") == reminder_id for item in store.get("reminders", []) if isinstance(item, dict)):
        return {
            "ok": False,
            "message": "Připomínka už existuje; duplicita nebyla přidána.",
            "document_due_candidates": document_due_candidates_status(
                vault_dir=vault_dir,
                reminders_path=reminders_path,
                archive_directory=archive_directory,
                today=today,
            ),
        }
    source_sender = safe_text(str(candidate.get("counterparty", "")))[:180]
    reminder = {
        "id": reminder_id,
        "title": reminder_title,
        "notes": reminder_notes,
        "due_date": safe_text(str(candidate.get("date", "")))[:40],
        "priority": priority or safe_text(str(candidate.get("priority", "high")))[:40] or "high",
        "status": "open",
        "source": {
            "type": "email_archive",
            "uid": safe_text(str(candidate.get("archive_id", "")))[:180],
            "date": safe_text(str(candidate.get("date", "")))[:120],
            "sender": source_sender,
        },
        "amount_due": safe_text(str(candidate.get("amount_due", "")))[:80],
        "amount_note": (
            safe_text(str(candidate.get("amount_note", "")))[:240]
            or "Částka byla odhadnuta z textu uloženého e-mailu."
        ),
        "archive_id": safe_text(str(candidate.get("archive_id", "")))[:180],
        "due_date_type": safe_text(str(candidate.get("type", "payment_due")))[:80],
    }
    store.setdefault("reminders", []).append(reminder)
    write_reminders_store(store, path=reminders_path)
    return {
        "ok": True,
        "reminder_ref": reminder_reference(reminder_id),
        "message": "Uloženo: připomínka z uloženého e-mailu byla vytvořena.",
        "document_due_candidates": document_due_candidates_status(
            vault_dir=vault_dir,
            reminders_path=reminders_path,
            archive_directory=archive_directory,
            today=today,
        ),
        "reminders": reminders_status(path=reminders_path, today=today),
    }


def enrich_document_due_reminder(*, reminder_id: str, candidate: dict[str, Any], reminders_path: Path) -> None:
    store = load_reminders_store(reminders_path)
    reminder = next((item for item in store.get("reminders", []) if item.get("id") == reminder_id), None)
    if reminder is None:
        return
    if candidate.get("related_asset"):
        reminder["related_asset"] = safe_text(str(candidate.get("related_asset", "")))[:180]
    if candidate.get("amount_due"):
        reminder["amount_due"] = safe_text(str(candidate.get("amount_due", "")))[:80]
        reminder["amount_note"] = (
            safe_text(str(candidate.get("amount_note", "")))[:240]
            or "Částka byla odhadnuta z krátkého kontextu termínu v dokumentu."
        )
    reminder["document_ref"] = safe_text(str(candidate.get("document_ref", "")))[:80]
    reminder["due_date_type"] = safe_text(str(candidate.get("type", "")))[:80]
    write_reminders_store(store, path=reminders_path)


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


def document_stored_path_is_openable_pdf(stored_path: str, vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> bool:
    try:
        root = vault_dir.resolve(strict=True)
        target = (PROJECT_ROOT / stored_path).resolve(strict=True)
    except (OSError, RuntimeError):
        return False
    return target.is_file() and target.suffix.casefold() == ".pdf" and (target == root or root in target.parents)


def resolve_openable_document_pdf(
    document_id: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
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
    title = safe_text(str(row.get("title", "") or row.get("filename", "") or "Dokument"))[:240]
    document_ref = document_reference(str(row.get("document_id", "")))
    return {
        "ok": True,
        "path": target,
        "title": title,
        "document_id": safe_text(str(row.get("document_id", ""))),
        "document_ref": document_ref,
    }


def open_document_pdf_action(
    document_id: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    opener: Callable[[list[str]], object] | None = None,
) -> dict[str, Any]:
    resolved = resolve_openable_document_pdf(document_id, vault_dir=vault_dir)
    if not resolved.get("ok"):
        return resolved
    target = resolved["path"]
    runner = opener or (lambda command: subprocess.run(command, check=False))
    runner(["/usr/bin/open", str(target)])
    return {
        "ok": True,
        "message": "PDF otevřeno v lokální aplikaci.",
        "document_id": resolved["document_id"],
        "document_ref": resolved["document_ref"],
    }


def document_reader_page_html(document_id: str, title: str) -> str:
    safe_title = html.escape(title or "Dokument")
    safe_document_id = html.escape(document_id)
    document_id_json = json.dumps(document_id, ensure_ascii=False)
    pdf_url = f"/documents/pdf?document_id={quote(document_id, safe='')}"
    safe_pdf_url = html.escape(pdf_url, quote=True)
    return f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Čtení dokumentu - {safe_title}</title>
  <style>
    :root {{ color-scheme: light; --blue: #2563eb; --ink: #172033; --muted: #667085; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f6f8fb; color: var(--ink); }}
    .bar {{ min-height: 58px; display: grid; grid-template-columns: minmax(0, 1fr) auto auto auto; gap: 10px; align-items: center; padding: 10px 14px; background: white; border-bottom: 1px solid #d7dee8; }}
    .title {{ min-width: 0; }}
    .title strong {{ display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .title span {{ color: var(--muted); font-size: 12px; }}
    button, a.button {{ border: 0; border-radius: 6px; padding: 9px 12px; font: inherit; font-weight: 700; cursor: pointer; background: #e4e9f0; color: #172033; text-decoration: none; white-space: nowrap; }}
    button.primary, a.button.primary {{ background: var(--blue); color: white; }}
    .status {{ grid-column: 1 / -1; color: var(--muted); font-size: 13px; min-height: 18px; }}
    .viewer {{ width: 100vw; height: calc(100vh - 82px); border: 0; display: block; background: white; }}
    .fallback {{ padding: 16px; }}
    @media (max-width: 720px) {{
      .bar {{ grid-template-columns: 1fr; align-items: stretch; }}
      button, a.button {{ width: 100%; text-align: center; }}
      .viewer {{ height: calc(100vh - 210px); }}
    }}
  </style>
</head>
<body>
  <div class="bar">
    <div class="title">
      <strong>{safe_title}</strong>
      <span>{safe_document_id}</span>
    </div>
    <button type="button" class="primary" id="readerPrintBtn">Tisknout</button>
    <button type="button" id="readerBackBtn">Zpět do Cockpitu</button>
    <button type="button" id="readerCloseBtn">Zavřít okno</button>
    <div class="status" id="readerStatus">Dokument je otevřený ke čtení. Po kontrole ho můžeš rovnou vytisknout.</div>
  </div>
  <iframe class="viewer" src="{safe_pdf_url}" title="PDF dokument"></iframe>
  <noscript><div class="fallback"><a class="button primary" href="{safe_pdf_url}">Otevřít PDF</a></div></noscript>
  <script>
    const DOCUMENT_ID = {document_id_json};
    const readerStatus = document.getElementById("readerStatus");
    const readerPrintBtn = document.getElementById("readerPrintBtn");
    const readerBackBtn = document.getElementById("readerBackBtn");
    const readerCloseBtn = document.getElementById("readerCloseBtn");

    async function postJson(url, payload) {{
      const res = await fetch(url, {{
        method: "POST",
        headers: {{"Content-Type": "application/json"}},
        body: JSON.stringify(payload || {{}})
      }});
      return await res.json();
    }}

    function focusCockpit() {{
      if (window.opener && !window.opener.closed) {{
        window.opener.focus();
        readerStatus.textContent = "Vracím zpět původní Cockpit.";
        window.close();
        window.setTimeout(() => {{
          window.location.href = "/";
        }}, 350);
        return true;
      }}
      window.location.href = "/";
      return false;
    }}

    function closeReader() {{
      if (window.opener && !window.opener.closed) {{
        window.opener.focus();
      }}
      window.close();
      window.setTimeout(() => {{
        readerStatus.textContent = "Pokud se okno nezavřelo, použij Zpět do Cockpitu. Dokument můžeš vytisknout i odsud.";
      }}, 300);
    }}

    async function printFromReader() {{
      if (!DOCUMENT_ID) return;
      readerPrintBtn.disabled = true;
      readerStatus.textContent = "Připravuji dokument k tisku...";
      try {{
        const prepared = await postJson("/api/documents/print/prepare", {{document_id: DOCUMENT_ID}});
        if (!prepared.ok) {{
          readerStatus.textContent = prepared.message || "Příprava tisku selhala.";
          return;
        }}
        const confirmation = `Potvrzuji, vytiskni print job ${{prepared.print_job_id}}.`;
        const shouldPrint = window.confirm(`Dokument je připraven k tisku.\\n\\nPrint job: ${{prepared.print_job_id}}\\n\\nOdeslat na tiskárnu?`);
        if (!shouldPrint) {{
          readerStatus.textContent = "Tisk je připravený, ale nebyl odeslán na tiskárnu.";
          return;
        }}
        readerStatus.textContent = "Odesílám tisk na macOS tiskovou frontu...";
        const printed = await postJson("/api/documents/print/run", {{
          print_job_id: prepared.print_job_id,
          confirmation_text: confirmation
        }});
        readerStatus.textContent = printed.message || "Tisk dokončen.";
      }} catch (err) {{
        readerStatus.textContent = `Chyba tisku: ${{err}}`;
      }} finally {{
        readerPrintBtn.disabled = false;
      }}
    }}

    readerPrintBtn.addEventListener("click", printFromReader);
    readerBackBtn.addEventListener("click", focusCockpit);
    readerCloseBtn.addEventListener("click", closeReader);
  </script>
</body>
</html>"""


def markdown_inline_html(text: str) -> str:
    parts = re.split(r"`([^`]+)`", text)
    rendered: list[str] = []
    for index, part in enumerate(parts):
        if index % 2:
            rendered.append(f"<code>{html.escape(part)}</code>")
        else:
            rendered.append(html.escape(part))
    return "".join(rendered)


def basic_markdown_to_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    output: list[str] = []
    paragraph: list[str] = []
    list_mode = ""

    def flush_paragraph() -> None:
        if not paragraph:
            return
        output.append(f"<p>{markdown_inline_html(' '.join(paragraph))}</p>")
        paragraph.clear()

    def close_list() -> None:
        nonlocal list_mode
        if list_mode:
            output.append(f"</{list_mode}>")
            list_mode = ""

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            close_list()
            continue

        if (raw_line.startswith((" ", "\t")) and list_mode and output and output[-1].startswith("<li>")):
            output[-1] = output[-1][:-5] + " " + markdown_inline_html(line) + "</li>"
            continue

        heading_match = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading_match:
            flush_paragraph()
            close_list()
            level = len(heading_match.group(1))
            output.append(f"<h{level}>{markdown_inline_html(heading_match.group(2).strip())}</h{level}>")
            continue

        bullet_match = re.match(r"^-\s+(.+)$", line)
        if bullet_match:
            flush_paragraph()
            if list_mode != "ul":
                close_list()
                output.append("<ul>")
                list_mode = "ul"
            output.append(f"<li>{markdown_inline_html(bullet_match.group(1).strip())}</li>")
            continue

        number_match = re.match(r"^\d+\.\s+(.+)$", line)
        if number_match:
            flush_paragraph()
            if list_mode != "ol":
                close_list()
                output.append("<ol>")
                list_mode = "ol"
            output.append(f"<li>{markdown_inline_html(number_match.group(1).strip())}</li>")
            continue

        close_list()
        paragraph.append(line)

    flush_paragraph()
    close_list()
    return "\n".join(output)


def janicka_cookbook_page_html(path: Path = JANICKA_COOKBOOK_PATH) -> str:
    try:
        markdown_text = path.read_text(encoding="utf-8")
        body_html = basic_markdown_to_html(markdown_text)
        status = f"Zdroj: {html.escape(str(relative_to_project(path)))}"
    except OSError as exc:
        body_html = (
            "<h1>Janička Cockpit - kuchařka</h1>"
            f"<p>Kuchařku se nepodařilo načíst: {html.escape(str(exc))}</p>"
        )
        status = "Kuchařka není dostupná."
    return f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Janička Cockpit - kuchařka</title>
  <style>
    :root {{ color-scheme: light; --pink: #be185d; --ink: #271923; --muted: #705366; --line: #fbcfe8; --paper: #fff7fb; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--paper); color: var(--ink); line-height: 1.58; }}
    header {{ position: sticky; top: 0; z-index: 1; background: #fce7f3; border-bottom: 1px solid var(--line); padding: 12px 18px; display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: 10px; align-items: center; }}
    header strong {{ display: block; font-size: 18px; color: #581c35; }}
    header span {{ display: block; color: var(--muted); font-size: 12px; margin-top: 2px; }}
    main {{ width: min(880px, 100%); margin: 0 auto; padding: 24px 18px 48px; }}
    article {{ background: white; border: 1px solid var(--line); border-radius: 8px; padding: 22px; box-shadow: 0 10px 28px rgba(88, 28, 53, .08); }}
    h1 {{ margin: 0 0 18px; color: #581c35; line-height: 1.18; font-size: 30px; }}
    h2 {{ margin: 28px 0 10px; color: #831843; line-height: 1.25; font-size: 22px; }}
    h3 {{ margin: 22px 0 8px; color: #9d174d; line-height: 1.25; font-size: 18px; }}
    p {{ margin: 10px 0; }}
    ul, ol {{ margin: 10px 0 14px; padding-left: 24px; }}
    li {{ margin: 5px 0; }}
    code {{ background: #fff1f2; border: 1px solid #ffe4e6; border-radius: 5px; padding: 1px 5px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .93em; }}
    button, a.button {{ border: 0; border-radius: 6px; padding: 9px 12px; font: inherit; font-weight: 750; cursor: pointer; background: #f9a8d4; color: #581c35; text-decoration: none; white-space: nowrap; }}
    button.primary, a.button.primary {{ background: var(--pink); color: white; }}
    @media (max-width: 720px) {{
      header {{ grid-template-columns: 1fr; align-items: stretch; }}
      button, a.button {{ width: 100%; text-align: center; }}
      article {{ padding: 18px; }}
      h1 {{ font-size: 26px; }}
    }}
    @media print {{
      header {{ position: static; }}
      button, a.button {{ display: none; }}
      body {{ background: white; }}
      article {{ border: 0; box-shadow: none; padding: 0; }}
      main {{ padding: 0; width: 100%; }}
    }}
  </style>
</head>
<body>
  <header>
    <div>
      <strong>Janička Cockpit - kuchařka</strong>
      <span>{status}</span>
    </div>
    <a class="button" href="/">Zpět do Cockpitu</a>
    <button class="primary" type="button" onclick="window.print()">Tisk</button>
  </header>
  <main>
    <article>
      {body_html}
    </article>
  </main>
</body>
</html>"""


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
        "amount_due": safe_text(str(raw.get("amount_due", "")))[:80],
        "amount_note": safe_text(str(raw.get("amount_note", "")))[:240],
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
    dirty_items = [classify_git_dirty_line(line) for line in dirty_files]
    categories: dict[str, int] = {}
    for item in dirty_items:
        category = str(item.get("category", "other"))
        categories[category] = categories.get(category, 0) + 1
    safe_commit_candidates = [
        item for item in dirty_items
        if item.get("commit_safety") == "safe"
    ]
    excluded_private = [
        item for item in dirty_items
        if item.get("commit_safety") == "exclude"
    ]
    message = "čistý pracovní strom" if not dirty_files else f"{len(dirty_files)} změn v pracovním stromu"
    return {
        "ok": True,
        "message": message,
        "branch": branch,
        "dirty_count": len(dirty_files),
        "dirty_files": dirty_files[:8],
        "dirty_items": dirty_items[:12],
        "categories": categories,
        "safe_commit_count": len(safe_commit_candidates),
        "excluded_private_count": len(excluded_private),
        "safe_commit_candidates": safe_commit_candidates[:8],
        "excluded_private": excluded_private[:8],
        "ahead": "ahead" in branch,
        "behind": "behind" in branch,
    }


def classify_git_dirty_line(line: str) -> dict[str, Any]:
    raw = safe_text(str(line)).strip()
    status = raw[:2].strip() or "?"
    path = raw[3:].strip() if len(raw) > 3 else raw
    normalized = path.replace("\\", "/")
    folded = normalized.casefold()
    category = "other"
    commit_safety = "safe"
    reason = "Git-safe technická nebo projektová změna."
    if "family_memory" in folded or "family-memory" in folded or "/family_memory" in folded:
        category = "family_memory"
        commit_safety = "exclude"
        reason = "Family Memory práce je v této session výslovně mimo commit."
    elif "/data/private/" in folded or folded.startswith("samantha_agent/data/private/"):
        category = "private_data"
        commit_safety = "exclude"
        reason = "Private data nepatří do gitu."
    elif "/data/session_autosave/" in folded or folded.startswith("samantha_agent/data/session_autosave/"):
        category = "autosave"
        commit_safety = "exclude"
        reason = "Nouzové autosave logy se nikdy necommitují."
    elif "/memory/active_projects.md" in folded or "/memory/memory_index.md" in folded:
        category = "memory_index"
        commit_safety = "review"
        reason = "Memory index může obsahovat smíšené hunky; před commitem zkontrolovat obsah."
    elif "/memory/" in folded:
        category = "memory"
        commit_safety = "review"
        reason = "Memory soubor vyžaduje kontrolu citlivosti a tématu."
    elif "/app/speech/" in folded or normalized.endswith("/scripts/speak_text.py"):
        category = "speech_tooling"
        reason = "Technická TTS/speech změna; commitovat jen po samostatném ověření."
    elif "/tests/" in folded:
        category = "tests"
    elif "/app/" in folded:
        category = "app_code"
    elif "/scripts/" in folded:
        category = "script"
    return {
        "status": status,
        "path": normalized,
        "category": category,
        "commit_safety": commit_safety,
        "reason": reason,
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


def document_intake_status(
    downloads: dict[str, Any] | None = None,
    *,
    decisions_path: Path = EMAIL_PROCESSING_DECISIONS_FILE,
    mobile_inbox_dir: Path = DEFAULT_MOBILE_DOCUMENT_INBOX,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 5,
) -> dict[str, Any]:
    downloads = downloads if downloads is not None else safe_downloads_status(limit=50)
    download_items = [item for item in downloads.get("items", []) if isinstance(item, dict)]
    new_downloads = [item for item in download_items if item.get("status") == "new"]
    email_pending = email_processing_pending_work_items(path=decisions_path)
    email_items = [
        item for item in email_pending.get("items", [])
        if isinstance(item, dict) and str(item.get("action", "")) == "process"
    ]
    mobile = mobile_document_intake_source(mobile_inbox_dir=mobile_inbox_dir, limit=limit)
    local = local_document_inbox_source(vault_dir=vault_dir, limit=limit)
    sources = [
        {
            "id": "downloads",
            "label": "Downloads",
            "count": len(new_downloads),
            "status": "ready" if new_downloads else "empty",
            "next_action": "Zpracovat další PDF přes ScanDocu." if new_downloads else "Žádné nové PDF ke zpracování.",
            "items": [
                {
                    "title": safe_text(str(item.get("name", "")))[:180],
                    "meta": safe_text(str(item.get("modified_at", "")))[:120],
                }
                for item in new_downloads[:limit]
            ],
        },
        {
            "id": "email",
            "label": "E-mail work queue",
            "count": len(email_items),
            "status": "ready" if email_items else "empty",
            "next_action": "Zpracovat označené e-maily a PDF přílohy." if email_items else "Žádný e-mail není označený ke zpracování.",
            "items": [
                {
                    "title": safe_text(str(item.get("subject", "") or "E-mail bez předmětu"))[:180],
                    "meta": safe_text(
                        f"{item.get('provider', '')} / {item.get('folder', '')} / {item.get('date', '')}"
                    )[:180],
                }
                for item in email_items[:limit]
            ],
        },
        mobile,
        local,
    ]
    total = sum(int(source.get("count", 0) or 0) for source in sources)
    unified_items = document_intake_unified_items(sources=sources, limit=max(4, limit * 2))
    return {
        "ok": True,
        "count": total,
        "sources": sources,
        "unified_items": unified_items,
        "monitor": {
            "local_interval_minutes": 10,
            "email_interval_minutes": 30,
            "email_mode": "headers_only",
        },
        "message": (
            f"Čeká {total} dokumentových vstupů napříč zdroji."
            if total
            else "Žádný nový dokumentový vstup nečeká."
        ),
    }


def document_intake_email_scan_status(
    *,
    limit_per_source: int = 10,
    since: str = "",
    days: int = 1,
    known_ids: set[str] | None = None,
    decisions_path: Path = EMAIL_PROCESSING_DECISIONS_FILE,
    actions_path: Path = EMAIL_WORK_QUEUE_ACTIONS_FILE,
    icloud_provider_factory: Callable[[], object] | None = None,
    seznam_provider_factory: Callable[[], object] | None = None,
) -> dict[str, Any]:
    result = new_email_headers_overview(
        limit_per_source=limit_per_source,
        since=since,
        days=days,
        known_ids=known_ids,
        decisions_path=decisions_path,
        actions_path=actions_path,
        icloud_provider_factory=icloud_provider_factory,
        seznam_provider_factory=seznam_provider_factory,
    )
    raw_items = [item for item in result.get("items", []) if isinstance(item, dict)]
    items: list[dict[str, Any]] = []
    filtered_out_count = 0
    for item in raw_items:
        email_filter = document_intake_email_candidate_filter(item)
        if not email_filter["include"]:
            filtered_out_count += 1
            continue
        raw_attachments = item.get("attachments", [])
        attachments = raw_attachments if isinstance(raw_attachments, list) else []
        safe_item = {
            "id": safe_text(str(item.get("id", "")))[:180],
            "legacy_id": safe_text(str(item.get("legacy_id", "")))[:180],
            "source_key": safe_text(
                email_processing_stable_key(
                    str(item.get("provider", "")),
                    str(item.get("folder", "")),
                    str(item.get("uid", "")),
                )
            )[:180],
            "provider": safe_text(str(item.get("provider", "")))[:80],
            "folder": safe_text(str(item.get("folder", "")))[:80],
            "uid": safe_text(str(item.get("uid", "")))[:80],
            "date": safe_text(str(item.get("date", "")))[:120],
            "sender": safe_text(str(item.get("sender", "")))[:180],
            "subject": safe_text(str(item.get("subject", "") or "E-mail bez předmětu"))[:180],
            "category": safe_text(str(item.get("category", "")))[:80],
            "reason": safe_text(str(item.get("reason", "")))[:180],
            "attachment_count": int(item.get("attachment_count", 0) or 0),
            "pdf_attachment_count": int(item.get("pdf_attachment_count", 0) or 0),
            "large_pdf_attachment_count": int(item.get("large_pdf_attachment_count", 0) or 0),
            "attachment_metadata": [
                {
                    "filename": safe_text(str(attachment.get("filename", "") if isinstance(attachment, dict) else ""))[:180],
                    "content_type": safe_text(str(attachment.get("content_type", "") if isinstance(attachment, dict) else ""))[:80],
                    "size_bytes": attachment.get("size_bytes") if isinstance(attachment, dict) else None,
                }
                for attachment in attachments[:5]
                if isinstance(attachment, dict)
            ],
            "filter_score": int(email_filter["score"]),
            "filter_label": safe_text(str(email_filter["label"]))[:80],
            "filter_reasons": [
                safe_text(str(reason))[:120]
                for reason in email_filter["reasons"]
                if str(reason).strip()
            ],
        }
        items.append(safe_item)
    filter_message = (
        f"Dokumentový filtr: z {len(raw_items)} hlaviček zobrazeno {len(items)}, "
        f"potlačeno {filtered_out_count}."
    )
    return {
        "ok": bool(result.get("ok", True)),
        "message": safe_text(filter_message)[:300],
        "generated_at": safe_text(str(result.get("generated_at", "")))[:80],
        "raw_count": len(raw_items),
        "count": len(items),
        "filtered_out_count": filtered_out_count,
        "suppressed_known_ids": [
            safe_text(str(item_id))[:180]
            for item_id in result.get("suppressed_known_ids", [])
            if str(item_id).strip()
        ],
        "items": items,
        "unavailable": [
            safe_text(str(item))[:180]
            for item in result.get("unavailable", [])
            if str(item).strip()
        ],
        "filter": {
            "mode": "document_candidates",
            "description": "Zobrazuje jen hlavičky se signály smlouvy, pojištění, faktury, upomínky, úřadu nebo PDF.",
            "filtered_out_count": filtered_out_count,
        },
        "monitor": {
            "interval_minutes": 30,
            "mode": "headers_only",
            "does_not_read_bodies": True,
            "does_not_download_attachments": True,
            "does_read_attachment_metadata": True,
            "does_not_write_decisions": True,
        },
    }


def document_intake_unified_items(*, sources: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    source_priority = {"downloads": 10, "email": 20, "mobile": 30, "local_inbox": 40}
    action_by_source = {
        "downloads": {"kind": "open_scandocu", "label": "ScanDocu"},
        "email": {"kind": "open_email_processing", "label": "E-maily"},
        "mobile": {"kind": "manual", "label": ""},
        "local_inbox": {"kind": "manual", "label": ""},
    }
    status_labels = {
        "ready": "čeká",
        "problem": "problém",
        "missing": "chybí",
        "empty": "prázdné",
    }
    items: list[dict[str, Any]] = []
    for source in sources:
        source_id = safe_text(str(source.get("id", ""))).strip()
        source_label = safe_text(str(source.get("label", "") or source_id))[:80]
        source_status = safe_text(str(source.get("status", "")))[:40]
        action = action_by_source.get(source_id, {"kind": "manual", "label": ""})
        for index, raw_item in enumerate(source.get("items", []) if isinstance(source.get("items"), list) else []):
            if not isinstance(raw_item, dict):
                continue
            title = safe_text(str(raw_item.get("title", "") or "Dokumentový vstup"))[:180]
            meta = safe_text(str(raw_item.get("meta", "")))[:240]
            items.append(
                {
                    "source_id": source_id,
                    "source_label": source_label,
                    "source_status": source_status,
                    "source_status_label": status_labels.get(source_status, source_status),
                    "title": title,
                    "meta": meta,
                    "next_action": safe_text(str(source.get("next_action", "")))[:240],
                    "action_kind": action["kind"],
                    "action_label": action["label"],
                    "sort_key": source_priority.get(source_id, 90) + index / 100,
                }
            )
    items.sort(key=lambda item: float(item.get("sort_key", 999)))
    return [
        {key: value for key, value in item.items() if key != "sort_key"}
        for item in items[: max(1, limit)]
    ]


def mobile_document_intake_source(
    *,
    mobile_inbox_dir: Path = DEFAULT_MOBILE_DOCUMENT_INBOX,
    limit: int = 5,
) -> dict[str, Any]:
    inbox = mobile_inbox_dir.expanduser()
    process_request = inbox / "process_request.json"
    if not inbox.exists():
        return {
            "id": "mobile",
            "label": "Mobilní sken",
            "count": 0,
            "status": "missing",
            "next_action": "Mobilní inbox zatím není synchronizovaný na Mac.",
            "items": [],
        }
    if not inbox.is_dir():
        return {
            "id": "mobile",
            "label": "Mobilní sken",
            "count": 0,
            "status": "problem",
            "next_action": "Mobilní inbox není složka.",
            "items": [],
        }
    manifests = sorted(
        inbox.glob("scan_*_manifest.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    items: list[dict[str, str]] = []
    for manifest_path in manifests[:limit]:
        try:
            manifest = read_json_file(manifest_path)
        except ValueError as exc:
            items.append(
                {
                    "title": safe_text(manifest_path.name)[:180],
                    "meta": f"chyba manifestu: {safe_text(str(exc))[:120]}",
                }
            )
            continue
        batch_id = safe_text(str(manifest.get("batch_id", ""))).strip()
        title = safe_text(str(manifest.get("document_title", ""))).strip() or batch_id or manifest_path.stem
        expected_count = safe_text(str(manifest.get("page_count", ""))).strip() or "?"
        pages = sorted(inbox.glob(f"{batch_id}_page_*")) if batch_id else []
        modified = datetime.fromtimestamp(manifest_path.stat().st_mtime).isoformat(timespec="minutes")
        items.append(
            {
                "title": title[:180],
                "meta": f"{len(pages)} / {expected_count} stran | {modified}",
            }
        )
    count = len(manifests)
    request_note = " Process request čeká." if process_request.exists() else ""
    return {
        "id": "mobile",
        "label": "Mobilní sken",
        "count": count,
        "status": "ready" if count else "empty",
        "next_action": (
            f"Připravit nebo zpracovat mobilní batch.{request_note}"
            if count
            else f"Žádný mobilní scan nečeká.{request_note}"
        ),
        "items": items,
    }


def local_document_inbox_source(
    *,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 5,
) -> dict[str, Any]:
    incoming = vault_dir / "inbox" / "incoming"
    if not incoming.exists():
        return {
            "id": "local_inbox",
            "label": "Lokální inbox",
            "count": 0,
            "status": "missing",
            "next_action": "Lokální document inbox zatím neexistuje.",
            "items": [],
        }
    if not incoming.is_dir():
        return {
            "id": "local_inbox",
            "label": "Lokální inbox",
            "count": 0,
            "status": "problem",
            "next_action": "Lokální document inbox není složka.",
            "items": [],
        }
    files = sorted(
        (item for item in incoming.iterdir() if item.is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return {
        "id": "local_inbox",
        "label": "Lokální inbox",
        "count": len(files),
        "status": "ready" if files else "empty",
        "next_action": "Připravit import souboru z inboxu." if files else "Lokální inbox je prázdný.",
        "items": [
            {
                "title": safe_text(path.name)[:180],
                "meta": f"{path.stat().st_size} B | {datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec='minutes')}",
            }
            for path in files[:limit]
        ],
    }


def document_cases_status(
    *,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 6,
    documents_per_case: int = 3,
) -> dict[str, Any]:
    groups: dict[str, dict[str, Any]] = {}
    active_count = 0
    linked_count = 0
    unlinked_count = 0
    for row in read_jsonl(vault_dir / "index" / "documents_index.jsonl"):
        document_id = safe_text(str(row.get("document_id", ""))).strip()
        if not document_id:
            continue
        lifecycle_status = safe_text(str(row.get("lifecycle_status", "active") or "active")).casefold()
        if lifecycle_status in {"archived", "trashed"}:
            continue
        active_count += 1
        title = safe_text(str(row.get("title") or row.get("original_filename") or document_id))[:180]
        domain = safe_text(str(row.get("domain", "")))[:80]
        document_type = safe_text(str(row.get("document_type", "")))[:80]
        counterparty = safe_text(str(row.get("counterparty", "")))[:120]
        related_asset = safe_text(str(row.get("related_asset", "")))[:120]
        reading_status = effective_document_reading_status(row)
        if related_asset:
            linked_count += 1
            group_type = "asset"
            group_label = related_asset
            group_key = f"asset:{related_asset.casefold()}"
        else:
            unlinked_count += 1
            if counterparty:
                group_type = "counterparty"
                group_label = f"Protistrana: {counterparty}"
                group_key = f"counterparty:{counterparty.casefold()}"
            else:
                group_type = "unlinked"
                group_label = "Bez vazby"
                group_key = "unlinked:"
        group = groups.setdefault(
            group_key,
            {
                "case_ref": document_case_reference(group_key),
                "label": group_label,
                "group_type": group_type,
                "document_count": 0,
                "domains": set(),
                "document_types": set(),
                "documents": [],
            },
        )
        group["document_count"] += 1
        if domain:
            group["domains"].add(domain)
        if document_type:
            group["document_types"].add(document_type)
        if len(group["documents"]) < max(1, documents_per_case):
            group["documents"].append(
                {
                    "document_ref": document_reference(document_id),
                    "title": title,
                    "domain": domain,
                    "domain_label": document_domain_label(domain),
                    "document_type": document_type,
                    "document_type_label": document_type_label(document_type),
                    "counterparty": counterparty,
                    "related_asset": related_asset,
                    "reading_status": reading_status,
                    "reading_status_label": READING_STATUS_LABELS.get(reading_status, reading_status),
                }
            )
    all_groups = []
    for group in groups.values():
        all_groups.append(
            {
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
            }
        )
    cases = [item for item in all_groups if int(item["document_count"]) >= 2]
    singletons_count = sum(1 for item in all_groups if int(item["document_count"]) == 1)
    cases.sort(
        key=lambda item: (
            0 if item["group_type"] == "asset" else 1 if item["group_type"] == "counterparty" else 2,
            -int(item["document_count"]),
            str(item["label"]).casefold(),
        )
    )
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
        if related_asset:
            group_type = "asset"
            group_label = related_asset
            group_key = f"asset:{related_asset.casefold()}"
        elif counterparty:
            group_type = "counterparty"
            group_label = f"Protistrana: {counterparty}"
            group_key = f"counterparty:{counterparty.casefold()}"
        else:
            group_type = "unlinked"
            group_label = "Bez vazby"
            group_key = "unlinked:"

        group = groups.setdefault(
            group_key,
            {
                "case_ref": document_case_reference(group_key),
                "label": group_label,
                "group_type": group_type,
                "domains": set(),
                "document_types": set(),
                "documents": [],
                "document_ids": set(),
            },
        )
        group["document_ids"].add(document_id)
        if domain:
            group["domains"].add(domain)
        if document_type:
            group["document_types"].add(document_type)
        stored_path = safe_text(str(row.get("stored_path", "")))[:500]
        reading_status = effective_document_reading_status(row)
        group["documents"].append(
            {
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
                "can_open_pdf": document_stored_path_is_openable_pdf(stored_path, vault_dir=vault_dir),
            }
        )

    for group in groups.values():
        if group["case_ref"] != safe_case_ref or len(group["documents"]) < 2:
            continue
        documents = sorted(
            group["documents"],
            key=lambda item: (
                str(item.get("document_type_label", "")).casefold(),
                str(item.get("title", "")).casefold(),
            ),
        )
        summary = document_case_summary(
            group_type=str(group["group_type"]),
            label=str(group["label"]),
            document_count=len(documents),
            domains=sorted(group["domains"]),
            document_types=sorted(group["document_types"]),
        )
        raw_document_ids = {str(item) for item in group.get("document_ids", set()) if str(item).strip()}
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
            source_uid = safe_text(str(source.get("uid", ""))).strip() if isinstance(source, dict) else ""
            related_asset = safe_text(str(reminder.get("related_asset", ""))).strip()
            if (
                source_uid in raw_document_ids
                or source_uid in document_refs
                or document_case_asset_matches(related_asset, case_assets)
            ):
                case_open_reminders.append(reminder)
        case_open_reminders.sort(
            key=lambda item: (
                parse_reminder_due_date(item.get("due_date")) or date.max,
                safe_text(str(item.get("title", ""))).casefold(),
            )
        )

        due_candidates = [
            item
            for item in build_document_due_candidates(
                vault_dir=vault_dir,
                reminders_path=reminders_path,
                today=today_date,
            )
            if str(item.get("document_id", "")).strip() in raw_document_ids
            or document_case_asset_matches(str(item.get("related_asset", "")), case_assets)
        ]
        conflicts = [
            conflict
            for conflict in reminder_conflicts(open_reminders)
            if document_case_asset_matches(str(conflict.get("asset", "")), case_assets)
        ]
        public_reminders = [public_document_case_reminder(reminder, today_date) for reminder in case_open_reminders]
        public_due_candidates = [public_document_due_candidate(item) for item in due_candidates]
        public_conflicts = [public_document_case_conflict(conflict) for conflict in conflicts]
        case_health = document_case_health_status(
            documents=documents,
            reminders=public_reminders,
            due_candidates=public_due_candidates,
            conflicts=public_conflicts,
        )
        return {
            "ok": True,
            "case_ref": safe_case_ref,
            "label": safe_text(str(group["label"]))[:180],
            "group_type": safe_text(str(group["group_type"]))[:80],
            "group_type_label": document_case_group_type_label(str(group["group_type"])),
            "summary": summary,
            "document_count": len(documents),
            "documents": documents[: max(1, limit)],
            "reminders": public_reminders,
            "due_candidates": public_due_candidates,
            "conflicts": public_conflicts,
            "case_health": case_health,
            "truncated": len(documents) > max(1, limit),
            "message": "Detail case načten.",
        }
    return {"ok": False, "message": "Case nebyl nalezen nebo má jen jeden dokument.", "documents": []}


def document_classification_status(
    *,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 6,
) -> dict[str, Any]:
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
                "missing_fields": missing_fields,
                "missing_labels": missing_labels,
                "classification_summary": (
                    f"{document_domain_label(domain)} / {document_type_label(document_type)} | "
                    f"{counterparty or 'protistrana chybí'} | {related_asset or 'vazba chybí'}"
                ),
                "recommended_action": f"Doplnit: {', '.join(missing_labels)}.",
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
    if not type_slug or type_slug in {"document", "unknown"}:
        missing.append("document_type")
    if not safe_text(counterparty):
        missing.append("counterparty")
    if not safe_text(related_asset):
        missing.append("related_asset")
    return missing


def update_document_classification_metadata_action(
    document_id: str,
    metadata: dict[str, Any],
    *,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> dict[str, Any]:
    safe_reference = safe_slug(document_id, default="", limit=140)
    if not safe_reference:
        return {"ok": False, "message": "Chybí document_id."}
    if not isinstance(metadata, dict):
        return {"ok": False, "message": "Chybí metadata dokumentu."}

    documents_path = vault_dir / "index" / "documents_index.jsonl"
    documents = read_jsonl(documents_path)
    row_index = find_document_row_index_by_reference(documents, safe_reference)
    if row_index is None:
        return {"ok": False, "message": "Dokument nebyl nalezen v indexu."}

    current = dict(documents[row_index])
    resolved_document_id = str(current.get("document_id", ""))
    updates: dict[str, str] = {}
    for field in DOCUMENT_METADATA_UPDATE_FIELDS:
        if field not in metadata:
            continue
        raw_value = str(metadata.get(field, "") or "").strip()
        if field in {"domain", "document_type"}:
            updates[field] = safe_slug(raw_value, default="", limit=80)
        else:
            updates[field] = safe_text(raw_value)[:180]
    if not updates:
        return {"ok": False, "message": "Není co uložit; nebylo předáno žádné podporované metadata pole."}

    previous = {field: safe_text(str(current.get(field, "") or "")) for field in DOCUMENT_METADATA_UPDATE_FIELDS}
    changed = {
        field: value
        for field, value in updates.items()
        if safe_text(str(current.get(field, "") or "")) != value
    }
    if not changed:
        return {
            "ok": True,
            "document_id": safe_text(resolved_document_id),
            "document_ref": document_reference(resolved_document_id),
            "message": "Metadata se nezměnila.",
            "document_classification": document_classification_status(vault_dir=vault_dir),
        }

    stored_path_value = str(current.get("stored_path", "") or "")
    manifest_path = (PROJECT_ROOT / stored_path_value).parent / "manifest.json" if stored_path_value else None
    now_value = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    backup_dir = backup_document_metadata(vault_dir=vault_dir, document_id=resolved_document_id, manifest_path=manifest_path)

    updated = dict(current)
    updated.update(changed)
    updated["metadata_updated_at"] = now_value
    documents[row_index] = updated
    write_jsonl(documents_path, documents)
    if manifest_path is not None and manifest_path.exists():
        manifest = read_json_file(manifest_path)
        manifest.update(updated)
        write_json(manifest_path, manifest)

    append_jsonl(
        vault_dir / "index" / "document_metadata_actions.jsonl",
        {
            "action": "update_classification_metadata",
            "document_id": resolved_document_id,
            "previous": previous,
            "updated": {field: safe_text(str(updated.get(field, "") or "")) for field in DOCUMENT_METADATA_UPDATE_FIELDS},
            "changed_fields": sorted(changed),
            "created_at": now_value,
            "backup_dir": str(relative_to_project(backup_dir)),
            "do_not_commit": True,
        },
    )
    missing_fields = document_classification_missing_fields(
        domain=str(updated.get("domain", "")),
        document_type=str(updated.get("document_type", "")),
        counterparty=str(updated.get("counterparty", "")),
        related_asset=str(updated.get("related_asset", "")),
    )
    return {
        "ok": True,
        "document_id": safe_text(resolved_document_id),
        "document_ref": document_reference(resolved_document_id),
        "changed_fields": sorted(changed),
        "missing_fields": missing_fields,
        "message": (
            f"Metadata dokumentu uložena. Změněno: "
            f"{', '.join(DOCUMENT_REVIEW_FIELD_LABELS.get(field, field) for field in sorted(changed))}."
        ),
        "document_classification": document_classification_status(vault_dir=vault_dir),
    }


def backup_document_metadata(vault_dir: Path, document_id: str, manifest_path: Path | None) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = vault_dir / "index" / "metadata_backups" / f"{stamp}_{document_id}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    index_path = vault_dir / "index" / "documents_index.jsonl"
    if index_path.exists():
        shutil.copy2(index_path, backup_dir / "documents_index.jsonl")
    if manifest_path is not None and manifest_path.exists():
        shutil.copy2(manifest_path, backup_dir / "manifest.json")
    return backup_dir


def document_case_reference(group_key: str) -> str:
    digest = hashlib.sha256(group_key.encode("utf-8")).hexdigest()[:16]
    return f"caseref-{digest}"


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
        lifecycle_status = safe_text(str(row.get("lifecycle_status", "active") or "active")).casefold()
        if lifecycle_status in {"archived", "trashed"}:
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
        if text_chars == 0:
            reasons.append("zero_text")
        elif text_chars < short_text_threshold:
            reasons.append("short_text")
        if extraction.get("ocr_needed") is True:
            reasons.append("ocr_needed")
        for field, fallback in (("domain", "other"), ("document_type", "document")):
            value = safe_slug(str(row.get(field, "")), default="", limit=80)
            if not value or value in {fallback, "unknown"}:
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
            redacted_document_id = safe_text(document_id)
            if document_id and (
                document_reference(document_id) == safe_reference
                or document_reference(redacted_document_id) == safe_reference
            ):
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
    labels = {
        "encrypted": "šifrované PDF",
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


def run_print_preflight_command(command: list[str], timeout: float = DOCUMENT_PRINT_DISCOVERY_TIMEOUT) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, str(exc)
    output = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
    return completed.returncode, output


def current_airport_network(
    command_runner: Callable[[list[str], float], tuple[int, str]] = run_print_preflight_command,
) -> str:
    _code, output = command_runner(["networksetup", "-getairportnetwork", "en0"], 3.0)
    if ":" not in output:
        return ""
    return output.split(":", 1)[1].strip()


def document_print_preflight_status(
    command_runner: Callable[[list[str], float], tuple[int, str]] = run_print_preflight_command,
) -> dict[str, Any]:
    wifi = current_airport_network(command_runner)
    _ipp_code, ipp_output = command_runner(["ippfind", "-T", str(int(DOCUMENT_PRINT_DISCOVERY_TIMEOUT)), "-l"], DOCUMENT_PRINT_DISCOVERY_TIMEOUT + 1)
    _dnssd_code, dnssd_output = command_runner(["lpinfo", "--include-schemes", "dnssd", "-v"], DOCUMENT_PRINT_DISCOVERY_TIMEOUT)
    combined = f"{ipp_output}\n{dnssd_output}"
    normalized = combined.casefold()
    printer_visible = (
        DOCUMENT_PRINT_IPP_ID.casefold() in normalized
        or DOCUMENT_PRINT_PRINTER_LABEL.casefold() in normalized
        or "1ca1a9" in normalized
    )
    if not printer_visible:
        wifi_note = f" Aktuální Wi‑Fi: {wifi}." if wifi else ""
        return {
            "ok": False,
            "status": "printer_not_visible",
            "printer": DOCUMENT_PRINT_PRINTER_LABEL,
            "required_wifi": DOCUMENT_PRINT_REQUIRED_WIFI,
            "current_wifi": wifi,
            "message": (
                f"Pro tisk na tiskárně {DOCUMENT_PRINT_PRINTER_LABEL} musí být počítač připojený "
                f"ke stejné Wi‑Fi jako tiskárna: {DOCUMENT_PRINT_REQUIRED_WIFI}.{wifi_note} "
                "Cockpit teď tiskárnu přes IPP/Bonjour nevidí, proto tisk nespouštím."
            ),
        }

    blocking_tokens = [
        "media-empty-error",
        "media-needed-error",
        "paused",
        "stopped accepting-jobs",
    ]
    if any(token in normalized for token in blocking_tokens):
        return {
            "ok": False,
            "status": "printer_blocked",
            "printer": DOCUMENT_PRINT_PRINTER_LABEL,
            "required_wifi": DOCUMENT_PRINT_REQUIRED_WIFI,
            "current_wifi": wifi,
            "message": (
                f"Tiskárna {DOCUMENT_PRINT_PRINTER_LABEL} je vidět, ale nepřijímá tisk. "
                "Zkontroluj papír, formát A4 a případné potvrzovací okno na tiskárně "
                "nebo tonerovou hlášku. Potom zkus tisk znovu."
            ),
            "detail": sanitize_output(combined)[:800],
        }

    return {
        "ok": True,
        "status": "printer_visible",
        "printer": DOCUMENT_PRINT_PRINTER_LABEL,
        "required_wifi": DOCUMENT_PRINT_REQUIRED_WIFI,
        "current_wifi": wifi,
        "message": f"Tiskárna {DOCUMENT_PRINT_PRINTER_LABEL} je viditelná pro macOS tisk.",
    }


def prepare_document_print_action(
    document_id: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    preflight_checker: Callable[[], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    documents = read_jsonl(vault_dir / "index" / "documents_index.jsonl")
    row_index = find_document_row_index_by_reference(documents, document_id)
    if row_index is None:
        return {"ok": False, "message": "Dokument nebyl nalezen v indexu."}
    resolved_document_id = str(documents[row_index].get("document_id", ""))
    if preflight_checker is not None or vault_dir == DEFAULT_DOCUMENTS_DIR:
        preflight = (preflight_checker or document_print_preflight_status)()
        if not preflight.get("ok"):
            return {
                "ok": False,
                "message": str(preflight.get("message", "Tiskárna není připravená.")),
                "preflight": preflight,
            }
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
            printer=DOCUMENT_PRINT_PREFERRED_CUPS_QUEUE,
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


def cockpit_process_command(pid: int) -> str:
    try:
        completed = subprocess.run(
            ["ps", "-p", str(pid), "-o", "command="],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def command_is_cockpit_server(command: str) -> bool:
    script_path = str(PROJECT_ROOT / "scripts" / "cockpit_server.py")
    return script_path in command or "scripts/cockpit_server.py" in command


def start_cockpit_restart_action(
    *,
    confirmed: bool,
    host: str = "127.0.0.1",
    port: int = COCKPIT_PORT,
    pid: int | None = None,
    launcher: Callable[..., object] | None = None,
) -> dict[str, Any]:
    if not confirmed:
        return {
            "ok": False,
            "message": "Restart Cockpitu nebyl potvrzen.",
            "status": "confirmation_required",
        }
    current_pid = pid if pid is not None else os.getpid()
    command = cockpit_process_command(current_pid)
    if not command_is_cockpit_server(command):
        return {
            "ok": False,
            "message": "Bezpečnostní kontrola selhala: aktuální proces nevypadá jako Cockpit server.",
            "status": "unsafe_target",
            "pid": current_pid,
        }
    log_file = PROJECT_ROOT / "data" / "private" / "cockpit" / "restart.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_file.open("a", encoding="utf-8")
    command_args = [
        str(PROJECT_ROOT / ".venv" / "bin" / "python"),
        str(COCKPIT_RESTART_SCRIPT),
        "--pid",
        str(current_pid),
        "--host",
        host,
        "--port",
        str(port),
    ]
    starter = launcher or subprocess.Popen
    try:
        starter(
            command_args,
            cwd=str(PROJECT_ROOT),
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        log_handle.close()
    except OSError as exc:
        log_handle.close()
        return {
            "ok": False,
            "message": f"Restart worker se nepodařilo spustit: {exc}",
            "status": "worker_failed",
            "pid": current_pid,
        }
    return {
        "ok": True,
        "message": "Bezpečný restart Cockpitu zahájen. Stránka bude pár sekund nedostupná, potom ji obnov.",
        "status": "restart_started",
        "pid": current_pid,
        "url": f"http://{host}:{port}",
        "log": str(relative_to_project(log_file)),
    }


def start_adam_voice_mode_action(
    *,
    launcher: Callable[..., object] | None = None,
    log_file: Path = ADAM_VOICE_MODE_LOG_FILE,
    terminal_bridge: bool | None = None,
) -> dict[str, Any]:
    current = load_voice_mode_status()
    if current.get("running"):
        return {
            "ok": True,
            "status": "already_running",
            "message": "Adam Voice Mode watcher už běží.",
            "pid": current.get("pid"),
            "voice_mode": current,
        }
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_file.open("a", encoding="utf-8")
    command_args = [
        str(PROJECT_ROOT / ".venv" / "bin" / "python"),
        str(ADAM_VOICE_MODE_SCRIPT),
        "--poll",
        "0.5",
    ]
    bridge_env = os.environ.get("ADAM_VOICE_TERMINAL_BRIDGE", "").strip().lower()
    bridge_enabled = terminal_bridge if terminal_bridge is not None else bridge_env not in {"0", "false", "no", "ne"}
    if bridge_enabled:
        command_args.append("--terminal-bridge")
    starter = launcher or subprocess.Popen
    try:
        process = starter(
            command_args,
            cwd=str(PROJECT_ROOT),
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        log_handle.close()
    except OSError as exc:
        log_handle.close()
        return {
            "ok": False,
            "status": "watcher_failed",
            "message": f"Adam Voice Mode watcher se nepodařilo spustit: {exc}",
        }
    pid = int(getattr(process, "pid", 0) or 0)
    write_voice_mode_status(
        state="starting",
        message="Adam Voice Mode watcher se spouští.",
        pid=pid,
    )
    return {
        "ok": True,
        "status": "started",
        "message": "Adam Voice Mode watcher spuštěn. Teď můžeš nahrávat hlasové pokyny.",
        "pid": pid,
        "log": str(relative_to_project(log_file)),
        "terminal_bridge": bridge_enabled,
        "voice_mode": load_voice_mode_status(stale_after_seconds=60.0),
    }


def stop_adam_voice_mode_action() -> dict[str, Any]:
    current = load_voice_mode_status(stale_after_seconds=60.0)
    pid = int(current.get("pid") or 0)
    if not current.get("running") or not pid_exists(pid):
        write_voice_mode_status(
            state="stopped",
            message="Adam Voice Mode watcher neběží.",
            pid=pid,
        )
        return {
            "ok": True,
            "status": "already_stopped",
            "message": "Adam Voice Mode watcher neběží.",
            "voice_mode": load_voice_mode_status(),
        }
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError as exc:
        return {
            "ok": False,
            "status": "stop_failed",
            "message": f"Adam Voice Mode watcher se nepodařilo zastavit: {exc}",
            "pid": pid,
        }
    write_voice_mode_status(
        state="stopped",
        message="Adam Voice Mode watcher byl zastaven z Cockpitu.",
        pid=pid,
    )
    return {
        "ok": True,
        "status": "stopped",
        "message": "Adam Voice Mode watcher zastaven.",
        "pid": pid,
        "voice_mode": load_voice_mode_status(),
    }


def cockpit_voice_approval_action(payload: dict[str, Any]) -> dict[str, Any]:
    decision = str(payload.get("decision") or "").strip().lower()
    note = safe_text(str(payload.get("note") or ""))[:500]
    result = update_pending_approval(decision=decision, note=note)
    return {
        "ok": bool(result.get("ok")),
        "status": result.get("status"),
        "message": result.get("message") or "Rozhodnutí k hlasovému pokynu bylo uloženo.",
        "pending_for_adam": result,
        "voice_mode": load_voice_mode_status(stale_after_seconds=60.0),
    }


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


def cockpit_speak_action(text: str, *, voice: str = DEFAULT_VOICE) -> dict[str, Any]:
    try:
        return speak_text(text, voice=voice)
    except SpeechError as exc:
        return {
            "ok": False,
            "message": f"Hlasový výstup selhal: {exc}",
            "status": "speech_failed",
        }


def cockpit_edge_tts_action(
    text: str,
    *,
    voice: str = DEFAULT_EDGE_TTS_VOICE,
    rate: str = DEFAULT_EDGE_TTS_RATE,
    synthesizer: Callable[..., bytes] = synthesize_edge_tts_mp3_sync,
) -> dict[str, Any]:
    try:
        audio = synthesizer(text, voice=voice, rate=rate)
    except (SpeechError, EdgeTtsError) as exc:
        return {
            "ok": False,
            "message": f"Edge TTS selhalo: {exc}",
            "status": "edge_tts_failed",
            "voice": voice,
        }
    return {
        "ok": True,
        "message": "Text byl namluven českým mužským hlasem.",
        "status": "edge_tts_ready",
        "voice": voice,
        "rate": rate,
        "mime_type": "audio/mpeg",
        "audio_base64": base64.b64encode(audio).decode("ascii"),
        "audio_bytes": len(audio),
    }


def save_voice_command_to_inbox(
    transcription: dict[str, Any],
    *,
    inbox_dir: Path = VOICE_COMMAND_INBOX_DIR,
    now: datetime | None = None,
) -> dict[str, Any]:
    text = safe_text(str(transcription.get("text", "") or "")).strip()
    if not text:
        raise ValueError("Chybí přepsaný text hlasového pokynu.")

    created_at = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    stamp = created_at.strftime("%Y%m%d_%H%M%S")
    inbox_dir.mkdir(parents=True, exist_ok=True)
    command_path = inbox_dir / f"voice_command_{stamp}.md"
    counter = 2
    while command_path.exists():
        command_path = inbox_dir / f"voice_command_{stamp}_{counter}.md"
        counter += 1

    content = (
        "# Voice command\n\n"
        f"Created at: {created_at.isoformat()}\n"
        "Source: Samantha Cockpit / Hlasový pokyn\n"
        "Status: transcribed_only_not_executed\n\n"
        "## Text\n\n"
        f"{text}\n"
    )
    command_path.write_text(content, encoding="utf-8")
    latest_path = inbox_dir / "latest_voice_command.md"
    latest_path.write_text(content, encoding="utf-8")

    record = {
        "created_at": created_at.isoformat(),
        "path": str(relative_to_project(command_path)),
        "latest_path": str(relative_to_project(latest_path)),
        "text_chars": len(text),
        "status": "transcribed_only_not_executed",
    }
    append_jsonl(inbox_dir / "index.jsonl", record)
    return {
        "saved": True,
        "voice_command_path": str(relative_to_project(command_path)),
        "latest_voice_command_path": str(relative_to_project(latest_path)),
    }


def cockpit_transcribe_voice_action(
    payload: dict[str, Any],
    *,
    inbox_dir: Path = VOICE_COMMAND_INBOX_DIR,
) -> dict[str, Any]:
    try:
        result = transcribe_audio_base64(
            str(payload.get("audio_base64", "")),
            mime_type=str(payload.get("mime_type", "")),
            language=str(payload.get("language", "cs") or "cs"),
        )
        result.update(save_voice_command_to_inbox(result, inbox_dir=inbox_dir))
        result["message"] = "Hlasový pokyn byl přepsán a uložen pro Codex."
        return result
    except TranscriptionError as exc:
        return {
            "ok": False,
            "message": f"Přepis hlasu selhal: {exc}",
            "status": "transcription_failed",
        }
    except OSError as exc:
        return {
            "ok": False,
            "message": f"Přepis se povedl, ale uložení hlasového pokynu selhalo: {exc}",
            "status": "voice_inbox_save_failed",
        }
    except ValueError as exc:
        return {
            "ok": False,
            "message": f"Přepis se povedl, ale hlasový pokyn nejde uložit: {exc}",
            "status": "voice_inbox_save_failed",
        }


def cockpit_save_voice_text_action(
    payload: dict[str, Any],
    *,
    inbox_dir: Path = VOICE_COMMAND_INBOX_DIR,
) -> dict[str, Any]:
    text = safe_text(str(payload.get("text", "") or "")).strip()
    if not text:
        return {
            "ok": False,
            "message": "Chybí text hlasového pokynu.",
            "status": "empty_voice_text",
        }
    try:
        result = {
            "ok": True,
            "text": text,
            "message": "Textový hlasový pokyn byl uložen pro Codex.",
            "status": "voice_text_saved",
        }
        result.update(save_voice_command_to_inbox({"text": text}, inbox_dir=inbox_dir))
        return result
    except OSError as exc:
        return {
            "ok": False,
            "message": f"Uložení textového hlasového pokynu selhalo: {exc}",
            "status": "voice_inbox_save_failed",
        }
    except ValueError as exc:
        return {
            "ok": False,
            "message": f"Textový hlasový pokyn nejde uložit: {exc}",
            "status": "voice_inbox_save_failed",
        }


def janicka_chat_memory_context(
    *,
    cookbook_path: Path = JANICKA_COOKBOOK_PATH,
    takeover_path: Path = JANICKA_TAKEOVER_PATH,
    active_projects_path: Path = ACTIVE_PROJECTS_PATH,
    memory_index_path: Path = MEMORY_INDEX_PATH,
    max_chars_per_file: int = 7000,
) -> str:
    sections: list[str] = []
    for label, path in (
        ("Kuchařka pro Janu", cookbook_path),
        ("Projekt Janička Cockpit", takeover_path),
        ("Aktivní projekty", active_projects_path),
        ("Memory index", memory_index_path),
    ):
        try:
            text = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if not text:
            continue
        if len(text) > max_chars_per_file:
            text = text[:max_chars_per_file].rstrip() + "\n\n[Zkráceno.]"
        sections.append(f"## {label}\n{text}")
    if not sections:
        return "Projektová paměť Janičky se teď nepodařila načíst."
    return "\n\n---\n\n".join(sections)


def janicka_quick_note_chat_answer(message: str, history: list[Any]) -> str | None:
    normalized = message.casefold()
    mentions_qn = bool(re.search(r"\bqn\b|quick\s*notes?|rychl[áa]\s+pozn", normalized))
    wants_latest = any(term in normalized for term in ("posled", "nejnov", "latest", "last"))
    wants_detail = any(term in normalized for term in ("detail", "cel", "přeč", "prect", "ukaž", "ukaz"))
    explicit_match = re.search(r"(?:\bqn\b|quick\s*note)\s*#?\s*(\d+)|#\s*(\d+)", normalized)

    note_number: int | None = None
    if explicit_match:
        note_number = int(next(group for group in explicit_match.groups() if group))
    elif wants_detail and not mentions_qn:
        note_number = _latest_quick_note_number_from_history(history)

    if mentions_qn and wants_latest:
        status = quick_notes_status(limit=1)
        notes = status.get("notes", [])
        if not status.get("ok") or not notes:
            return str(status.get("message") or "Quick Notes se teď nepodařilo načíst.")
        latest = notes[0]
        note_number = int(latest.get("note_number") or 0)
        if wants_detail and note_number > 0:
            return _format_janicka_quick_note_detail(note_number)
        return _format_janicka_quick_note_summary(latest, status)

    if note_number is not None and (mentions_qn or wants_detail):
        return _format_janicka_quick_note_detail(note_number)

    return None


def _latest_quick_note_number_from_history(history: list[Any]) -> int | None:
    for item in reversed(history):
        if not isinstance(item, dict):
            continue
        content = safe_text(str(item.get("content", "") or ""))
        match = re.search(r"(?:QN|Quick Note)\s*#\s*(\d+)|#\s*(\d+)", content, flags=re.IGNORECASE)
        if match:
            return int(next(group for group in match.groups() if group))
    return None


def _format_janicka_quick_note_summary(note: dict[str, Any], status: dict[str, Any]) -> str:
    note_number = int(note.get("note_number") or 0)
    created_at = safe_text(str(note.get("created_at", "") or ""))[:80]
    snippet = safe_text(str(note.get("snippet", "") or ""))[:500]
    counts = status.get("counts", {}) if isinstance(status.get("counts"), dict) else {}
    active_count = int(counts.get("active") or 0)
    lines = [
        f"Poslední QN je **#{note_number}** z **{created_at}**:",
        snippet,
    ]
    if active_count:
        lines.append(f"V aktivním QN inboxu je teď celkem {active_count} poznámek.")
    lines.append("Chceš k ní i detail?")
    return "\n\n".join(line for line in lines if line)


def _format_janicka_quick_note_detail(note_number: int) -> str:
    detail = quick_note_detail_status(note_number, max_chars=6000)
    if not detail.get("ok"):
        return str(detail.get("message") or f"Quick Note #{note_number} se nepodařilo načíst.")
    created_at = safe_text(str(detail.get("created_at", "") or ""))[:80]
    body = "\n".join(
        safe_text(line)
        for line in str(detail.get("body_text", "") or "").replace("\x00", " ").splitlines()
    ).strip()
    if detail.get("truncated"):
        body += "\n\n[Zkráceno.]"
    return f"Detail QN **#{note_number}** z **{created_at}**:\n\n{body}"


def janicka_latest_codex_reply_action(
    payload: dict[str, Any],
    *,
    response_path: Path = ADAM_LAST_RESPONSE_PATH,
) -> dict[str, Any]:
    request_id = safe_text(str(payload.get("request_id", "") or "")).strip()
    if request_id:
        return load_adam_text_reply(request_id=request_id)
    expected_user_text = safe_text(str(payload.get("message", "") or "")).strip()
    response = load_last_adam_response(path=response_path)
    if not response.get("ok"):
        return response
    if not response.get("available"):
        return {
            "ok": True,
            "available": False,
            "status": "no_reply",
            "message": "Adamova odpověď z Codexu zatím není zapsaná.",
        }
    user_text = safe_text(str(response.get("user_text", "") or "")).strip()
    route = safe_text(str(response.get("route", "") or "")).strip()
    if expected_user_text and user_text != expected_user_text:
        return {
            "ok": True,
            "available": False,
            "status": "different_reply",
            "message": "Poslední uložená odpověď patří k jinému dotazu.",
            "route": route,
        }
    if route != "janicka_text_bridge":
        return {
            "ok": True,
            "available": False,
            "status": "different_route",
            "message": "Poslední uložená odpověď není z Janička text bridge.",
            "route": route,
        }
    return {
        "ok": True,
        "available": True,
        "status": "reply_available",
        "message": "Adamova odpověď z Codexu je připravená.",
        "answer": safe_text(str(response.get("adam_response", "") or "")).strip(),
        "created_at": response.get("created_at"),
        "route": route,
    }


def janicka_chat_action(
    payload: dict[str, Any],
    *,
    asker: Callable[[str], str] | None = None,
    service_submitter: Callable[..., dict[str, Any]] = submit_adam_text_request,
) -> dict[str, Any]:
    message = safe_text(str(payload.get("message", "") or "")).strip()
    if not message:
        return {
            "ok": False,
            "status": "empty_message",
            "message": "Napiš otázku nebo pokyn pro Adama.",
        }
    history = payload.get("history", [])
    try:
        result = service_submitter(message=message, history=history if isinstance(history, list) else [])
    except Exception as exc:  # pragma: no cover - exact macOS/terminal exceptions vary.
        return {
            "ok": False,
            "status": "adam_service_failed",
            "message": f"Dotaz se nepodařilo předat Adamovi: {exc}",
        }
    if not result.get("ok"):
        return {
            "ok": False,
            "status": str(result.get("status") or "adam_service_failed"),
            "message": str(result.get("message") or "Dotaz se nepodařilo předat Adamovi."),
            "request_id": result.get("request_id"),
            "service": result,
        }
    bridge_message = (
        "Dotaz jsem předal Adamovi. Pokud Adam ještě neběžel, Cockpit ho zkusil spustit. "
        "Odpověď se zobrazí tady, až ji Adam zapíše zpět."
    )
    return {
        "ok": True,
        "status": "delivered_to_adam",
        "message": "Dotaz předán Adamovi v Codexu.",
        "answer": bridge_message,
        "request_id": result.get("request_id"),
        "service": result,
        "poll_latest": True,
    }


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
        cockpit_host = self.host
        cockpit_port = self.port

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
                if parsed.path == "/janicka-kucharka/":
                    self.respond_html(janicka_cookbook_page_html())
                    return
                if parsed.path == "/documents/read":
                    params = parse_qs(parsed.query)
                    document_id = params.get("document_id", [""])[0]
                    self.respond_document_reader(document_id)
                    return
                if parsed.path == "/documents/pdf":
                    params = parse_qs(parsed.query)
                    document_id = params.get("document_id", [""])[0]
                    self.respond_document_pdf(document_id)
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
                if parsed.path == "/api/recovery/status":
                    self.respond_json(recovery_center_status())
                    return
                if parsed.path == "/api/quick-notes/status":
                    self.respond_json(quick_notes_status())
                    return
                if parsed.path == "/api/urgent-reminders/status":
                    self.respond_json(urgent_reminders_status())
                    return
                if parsed.path == "/api/quick-notes/detail":
                    params = parse_qs(parsed.query)
                    raw_note_number = params.get("note_number", params.get("note", ["0"]))[0]
                    try:
                        note_number = int(raw_note_number)
                    except (TypeError, ValueError):
                        note_number = 0
                    self.respond_json(quick_note_detail_status(note_number=note_number))
                    return
                if parsed.path == "/api/projects/status":
                    self.respond_json(projects_status())
                    return
                if parsed.path == "/api/library/list":
                    params = parse_qs(parsed.query)
                    category = params.get("category", ["other"])[0]
                    try:
                        limit = int(params.get("limit", ["200"])[0])
                    except (TypeError, ValueError):
                        limit = 200
                    self.respond_json(list_articles(category=category, limit=limit))
                    return
                if parsed.path == "/api/library/search":
                    params = parse_qs(parsed.query)
                    category = params.get("category", ["all"])[0]
                    query = params.get("q", [""])[0]
                    try:
                        limit = int(params.get("limit", ["50"])[0])
                    except (TypeError, ValueError):
                        limit = 50
                    self.respond_json(search_articles(query=query, category=category, limit=limit))
                    return
                if parsed.path == "/api/library/item":
                    params = parse_qs(parsed.query)
                    article_id = params.get("id", [""])[0]
                    self.respond_json(get_article(article_id=article_id))
                    return
                if parsed.path == "/api/library/attachment":
                    params = parse_qs(parsed.query)
                    article_id = params.get("id", [""])[0]
                    attachment_id = params.get("attachment_id", [""])[0]
                    variant = params.get("variant", ["readable"])[0]
                    self.respond_library_attachment(article_id, attachment_id, variant)
                    return
                if parsed.path == "/api/quantitative-status":
                    self.respond_json(quantitative_status_overview())
                    return
                if parsed.path == "/api/consistency-status":
                    self.respond_json(document_consistency_status())
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
                if parsed.path == "/api/documents/review-report":
                    self.respond_json(document_review_report_status())
                    return
                if parsed.path == "/api/documents/case-detail":
                    params = parse_qs(parsed.query)
                    case_ref = params.get("case_ref", [""])[0]
                    self.respond_json(document_case_detail_status(case_ref=case_ref))
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
                if parsed.path == "/api/speech/speak":
                    payload = self.read_json()
                    self.respond_json(cockpit_speak_action(text=str(payload.get("text", ""))))
                    return
                if parsed.path == "/api/speech/edge-tts":
                    payload = self.read_json()
                    self.respond_json(cockpit_edge_tts_action(text=str(payload.get("text", ""))))
                    return
                if parsed.path == "/api/speech/transcribe":
                    payload = self.read_json()
                    self.respond_json(cockpit_transcribe_voice_action(payload))
                    return
                if parsed.path == "/api/speech/voice-text":
                    payload = self.read_json()
                    self.respond_json(cockpit_save_voice_text_action(payload))
                    return
                if parsed.path == "/api/janicka/chat":
                    payload = self.read_json()
                    self.respond_json(janicka_chat_action(payload))
                    return
                if parsed.path == "/api/janicka/chat/latest":
                    payload = self.read_json()
                    self.respond_json(janicka_latest_codex_reply_action(payload))
                    return
                if parsed.path == "/api/adam/status":
                    self.respond_json(adam_service_status())
                    return
                if parsed.path == "/api/adam/start":
                    self.respond_json(start_adam_service())
                    return
                if parsed.path == "/api/adam/restart":
                    payload = self.read_json()
                    self.respond_json(restart_adam_service(confirmed=bool(payload.get("confirmed"))))
                    return
                if parsed.path == "/api/adam/stop":
                    payload = self.read_json()
                    self.respond_json(stop_adam_service(confirmed=bool(payload.get("confirmed"))))
                    return
                if parsed.path == "/api/voice-mode/start":
                    self.respond_json(start_adam_voice_mode_action())
                    return
                if parsed.path == "/api/voice-mode/stop":
                    self.respond_json(stop_adam_voice_mode_action())
                    return
                if parsed.path == "/api/voice-mode/approval":
                    payload = self.read_json()
                    self.respond_json(cockpit_voice_approval_action(payload))
                    return
                if parsed.path == "/api/voice-bridge/marker":
                    payload = self.read_json()
                    self.respond_json(set_adam_voice_bridge_marker_action(str(payload.get("tty", ""))))
                    return
                if parsed.path == "/api/cockpit/restart":
                    payload = self.read_json()
                    self.respond_json(
                        start_cockpit_restart_action(
                            confirmed=bool(payload.get("confirmed")),
                            host=cockpit_host,
                            port=cockpit_port,
                        )
                    )
                    return
                if parsed.path == "/api/projects/lifecycle":
                    payload = self.read_json()
                    self.respond_json(
                        project_lifecycle_action(
                            project_name=str(payload.get("project_name", "")),
                            lifecycle=str(payload.get("lifecycle", "")),
                            confirmed=bool(payload.get("confirmed")),
                        )
                    )
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
                if parsed.path == "/api/reminders/cancel-payment":
                    payload = self.read_json()
                    self.respond_json(
                        cancel_payment_reminder_action(
                            reminder_id=str(payload.get("reminder_id", "")),
                            reason=str(payload.get("reason", "")),
                            evidence_archive_id=str(payload.get("evidence_archive_id", "")),
                        )
                    )
                    return
                if parsed.path == "/api/urgent-reminders/done":
                    payload = self.read_json()
                    try:
                        reminder_number = int(payload.get("reminder_number", 0) or 0)
                    except (TypeError, ValueError):
                        reminder_number = 0
                    self.respond_json(urgent_reminder_done_action(reminder_number=reminder_number))
                    return
                if parsed.path == "/api/consistency/resolve-finding":
                    payload = self.read_json()
                    self.respond_json(
                        resolve_consistency_finding_action(
                            finding_id=str(payload.get("finding_id", "")),
                            reason=str(payload.get("reason", "")),
                            status=str(payload.get("status", "resolved")),
                        )
                    )
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
                if parsed.path == "/api/library/archive":
                    payload = self.read_json()
                    self.respond_json(library_archive_url_action(payload))
                    return
                if parsed.path == "/api/library/text":
                    payload = self.read_json()
                    self.respond_json(library_archive_text_action(payload))
                    return
                if parsed.path == "/api/library/attachment/add":
                    payload = self.read_json()
                    self.respond_json(library_attach_image_action(payload))
                    return
                if parsed.path == "/api/documents/classification-metadata":
                    payload = self.read_json()
                    raw_metadata = payload.get("metadata")
                    self.respond_json(
                        update_document_classification_metadata_action(
                            document_id=str(payload.get("document_id", "")),
                            metadata=raw_metadata if isinstance(raw_metadata, dict) else {},
                        )
                    )
                    return
                if parsed.path == "/api/documents/due-reminder":
                    payload = self.read_json()
                    self.respond_json(
                        create_document_due_reminder_action(
                            candidate_ref=str(payload.get("candidate_ref", "")),
                            title=str(payload.get("title", "")),
                            notes=str(payload.get("notes", "")),
                            priority=str(payload.get("priority", "")),
                            confirmed=bool(payload.get("confirmed")),
                        )
                    )
                    return
                if parsed.path == "/api/documents/intake-email-scan":
                    payload = self.read_json()
                    try:
                        limit = int(payload.get("limit_per_source", 10))
                    except (TypeError, ValueError):
                        limit = 10
                    try:
                        days = int(payload.get("days", 1))
                    except (TypeError, ValueError):
                        days = 1
                    raw_known_ids = payload.get("known_ids", [])
                    known_ids = set()
                    if isinstance(raw_known_ids, list):
                        known_ids = {str(item_id).strip() for item_id in raw_known_ids if str(item_id).strip()}
                    self.respond_json(
                        document_intake_email_scan_status(
                            limit_per_source=limit,
                            since=str(payload.get("since", "")),
                            days=days,
                            known_ids=known_ids,
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

            def respond_html(self, html: str, status: HTTPStatus = HTTPStatus.OK) -> None:
                data = html.encode("utf-8")
                self.send_response(status)
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

            def respond_document_reader(self, document_id: str) -> None:
                resolved = resolve_openable_document_pdf(document_id)
                if not resolved.get("ok"):
                    self.respond_html(
                        document_reader_page_html(
                            document_id=safe_text(document_id)[:180],
                            title=str(resolved.get("message", "Dokument není dostupný.")),
                        ),
                        status=HTTPStatus.NOT_FOUND,
                    )
                    return
                self.respond_html(
                    document_reader_page_html(
                        document_id=str(resolved["document_ref"]),
                        title=str(resolved["title"]),
                    )
                )

            def respond_document_pdf(self, document_id: str) -> None:
                resolved = resolve_openable_document_pdf(document_id)
                if not resolved.get("ok"):
                    self.respond_json({"error": "not_found", "message": resolved.get("message", "")}, status=HTTPStatus.NOT_FOUND)
                    return
                target = resolved["path"]
                data = target.read_bytes()
                filename = safe_filename(str(target.name or "document.pdf"))
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Disposition", f'inline; filename="{filename}"')
                self.send_header("Cache-Control", "no-store, max-age=0")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def respond_library_attachment(self, article_id: str, attachment_id: str, variant: str) -> None:
                resolved = get_article_attachment(
                    article_id=article_id,
                    attachment_id=attachment_id,
                    variant=variant,
                )
                if not resolved.get("ok"):
                    self.respond_json(
                        {"error": resolved.get("error", "not_found"), "message": resolved.get("message", "")},
                        status=HTTPStatus.NOT_FOUND,
                    )
                    return
                target = resolved["path"]
                data = target.read_bytes()
                content_type = str(resolved.get("mime_type") or content_type_for_path(target))
                filename = safe_filename(str(resolved.get("filename") or target.name or "attachment"))
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Disposition", f'inline; filename="{filename}"')
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
  <title>E-maily</title>
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
    <h1>E-maily</h1>
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
          button.addEventListener("click", () => {
            const documentId = button.dataset.documentId || "";
            if (!documentId) return;
            const url = "/documents/read?document_id=" + encodeURIComponent(documentId);
            button.disabled = true;
            queueStatus.textContent = "Otevírám uložené PDF ve čtecím okně Cockpitu.";
            try {
              const reader = window.open(url, "samanthaDocumentReader", "width=1180,height=860");
              if (reader) {
                reader.focus();
              } else {
                window.location.href = url;
              }
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

    function returnToCockpit() {
      const cockpitUrl = "/";
      if (window.opener && !window.opener.closed) {
        try {
          window.opener.focus();
        } catch (err) {
          // Focus can fail across browser contexts; closing this popup still avoids duplicate Cockpit windows.
        }
        window.close();
        return;
      }
      const cockpit = window.open(cockpitUrl, "SamanthaCockpit", "popup=yes,width=1280,height=880,left=90,top=60");
      if (cockpit) {
        cockpit.focus();
        window.close();
      } else {
        window.location.href = cockpitUrl;
      }
    }

    refreshBtn.addEventListener("click", () => loadNewHeaders({newOnly: true}));
    emailDaysInput.addEventListener("change", normalizeDaysInput);
    loadHeadersBtn.addEventListener("click", () => loadNewHeaders({lastSevenDays: true}));
    loadPendingBtn.addEventListener("click", loadPendingWork);
    processEmailsBtn.addEventListener("click", openWorkQueueWindow);
    cockpitBtn.addEventListener("click", returnToCockpit);
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
    button.janicka-button { background: #f9a8d4; color: #581c35; }
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
    .dashboard-updated { display: block; margin-top: 2px; color: var(--muted); font-size: 11px; line-height: 1.25; }
    .dashboard-overall { border: 1px solid var(--line); border-radius: 8px; padding: 10px; display: grid; gap: 4px; background: #fbfcfe; }
    .dashboard-overall-ok { border-color: #bbf7d0; background: #f0fdf4; }
    .dashboard-overall-warn { border-color: #fde68a; background: #fffbeb; }
    .dashboard-overall-bad { border-color: #fecaca; background: #fff4f2; }
    .dashboard-overall-loading { border-color: #dbeafe; background: #eff6ff; }
    .dashboard-overall-label { font-weight: 800; font-size: 15px; }
    .dashboard-overall-reason { color: #344054; font-size: 12px; line-height: 1.35; overflow-wrap: anywhere; }
    .quick-actions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; align-content: start; }
    .quick-actions button { width: 100%; }
    .janicka-modal { width: min(1040px, 100%); background: #fff7fb; border-color: #fbcfe8; }
    .janicka-modal .modal-header { background: #fce7f3; border-bottom-color: #fbcfe8; }
    .janicka-intro { border: 1px solid #fbcfe8; border-radius: 8px; background: #fff; padding: 14px; display: grid; gap: 7px; }
    .janicka-title { margin: 0; font-size: 22px; color: #581c35; line-height: 1.2; }
    .janicka-subtitle { margin: 0; color: #533044; font-size: 14px; line-height: 1.45; }
    .janicka-grid { display: grid; grid-template-columns: repeat(2, minmax(260px, 1fr)); gap: 10px; }
    .janicka-action { border: 1px solid #fbcfe8; border-radius: 8px; padding: 12px; background: #fff; display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; align-items: center; }
    .janicka-action-title { font-weight: 750; color: #581c35; }
    .janicka-action-text { margin-top: 3px; color: #5f4052; font-size: 13px; line-height: 1.4; }
    .janicka-action button { background: #be185d; color: white; }
    .janicka-action button.secondary { background: #fce7f3; color: #831843; }
    .janicka-note { border: 1px solid #fed7aa; border-radius: 8px; background: #fffbeb; color: #5f370e; padding: 11px 12px; font-size: 13px; line-height: 1.45; }
    .janicka-return { position: fixed; right: 18px; bottom: 18px; z-index: 14; box-shadow: 0 10px 28px rgba(88, 28, 53, .22); background: #be185d; color: white; }
    .janicka-chat-modal { width: min(920px, 100%); background: #fff7fb; border-color: #fbcfe8; }
    .janicka-chat-log { min-height: 320px; max-height: 48vh; overflow: auto; display: grid; gap: 10px; padding: 10px; border: 1px solid #fbcfe8; border-radius: 8px; background: white; }
    .janicka-chat-message { border: 1px solid #edf0f4; border-radius: 8px; padding: 10px; background: #fbfcfe; white-space: pre-wrap; overflow-wrap: anywhere; line-height: 1.45; }
    .janicka-chat-message.user { background: #fce7f3; border-color: #fbcfe8; }
    .janicka-chat-message.assistant { background: #fff; border-color: #fbcfe8; }
    .janicka-chat-meta { font-size: 12px; font-weight: 750; color: #831843; margin-bottom: 4px; }
    .janicka-chat-runtime { display: grid; gap: 8px; padding: 10px; border: 1px solid #fbcfe8; border-radius: 8px; background: #fff; }
    .compact-actions { gap: 8px; }
    .compact-actions button { min-height: 34px; padding: 6px 10px; }
    .janicka-chat-input { display: grid; gap: 8px; }
    .janicka-chat-input textarea { width: 100%; min-height: 110px; resize: vertical; border: 1px solid #fbcfe8; border-radius: 8px; padding: 10px; font: inherit; line-height: 1.45; }
    .health-panel { border: 1px solid #cfd7e3; border-radius: 8px; background: #fbfcfe; padding: 10px 12px; display: grid; gap: 7px; }
    .health-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
    .health-item { border: 1px solid #edf0f4; border-radius: 7px; background: white; padding: 8px; min-width: 0; }
    .health-label { display: block; color: var(--muted); font-size: 11px; line-height: 1.2; }
    .health-value { display: block; margin-top: 3px; font-size: 13px; font-weight: 650; overflow-wrap: anywhere; }
    .diagnostics-row.bad { border-left: 4px solid var(--red); padding-left: 8px; }
    .diagnostics-row.warn { border-left: 4px solid var(--amber); padding-left: 8px; }
    .diagnostics-row.loading { border-left: 4px solid var(--blue); padding-left: 8px; }
    .diagnostics-row.ok { border-left: 4px solid var(--green); padding-left: 8px; }
    .urgent-alert { border: 2px solid var(--red); border-radius: 8px; background: #fff4f2; padding: 12px 14px; display: grid; gap: 9px; }
    .urgent-alert.hidden { display: none; }
    .urgent-alert-head { display: flex; justify-content: space-between; gap: 12px; align-items: center; }
    .urgent-alert-title { color: var(--red); font-weight: 800; }
    .urgent-alert-list { display: grid; gap: 5px; color: #5f1d18; font-size: 13px; }
    .urgent-alert-item { border-top: 1px solid #fecaca; padding-top: 7px; display: grid; gap: 5px; }
    .urgent-alert-item:first-child { border-top: 0; padding-top: 0; }
    .urgent-alert-summary { width: 100%; text-align: left; padding: 7px 8px; background: #fee2e2; color: #7f1d1d; }
    .urgent-alert-detail { white-space: pre-wrap; overflow-wrap: anywhere; color: #5f1d18; background: #fff; border: 1px solid #fecaca; border-radius: 7px; padding: 8px; max-height: 220px; overflow: auto; }
    .urgent-reminder-body { white-space: pre-wrap; overflow-wrap: anywhere; border: 1px solid #edf0f4; border-radius: 7px; background: white; padding: 9px; max-height: 360px; overflow: auto; color: #263244; font-size: 13px; line-height: 1.45; }
    .action-queue { display: grid; gap: 9px; }
    .action-card { border: 1px solid #edf0f4; border-radius: 8px; padding: 11px; background: #fbfcfe; display: grid; gap: 8px; }
    .action-card-head { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 8px; align-items: start; }
    .action-title { font-weight: 750; overflow-wrap: anywhere; }
    .action-detail { color: var(--muted); font-size: 13px; overflow-wrap: anywhere; }
    .work-grid { display: grid; grid-template-columns: repeat(3, minmax(220px, 1fr)); gap: 12px; align-items: stretch; }
    .work-card { border: 1px solid var(--line); border-radius: 8px; padding: 12px; background: #fbfcfe; display: grid; gap: 10px; align-content: start; min-height: 170px; }
    .work-card h3 { margin: 0; font-size: 13px; color: #253047; }
    .work-count { font-size: 27px; font-weight: 750; line-height: 1; }
    .work-list { display: grid; gap: 7px; font-size: 12px; color: #344054; }
    .review-report-list { max-height: 360px; overflow: auto; padding-right: 4px; align-content: start; }
    .work-item { border-top: 1px solid #edf0f4; padding-top: 7px; overflow-wrap: anywhere; }
    .work-item:first-child { border-top: 0; padding-top: 0; }
    .work-meta { color: var(--muted); font-size: 11px; margin-top: 2px; }
    .review-group { border-top: 1px solid #edf0f4; padding-top: 9px; display: grid; gap: 7px; }
    .review-group:first-child { border-top: 0; padding-top: 0; }
    .review-group-head { display: flex; justify-content: space-between; gap: 8px; align-items: baseline; }
    .review-group-title { font-weight: 750; color: #253047; }
    .review-group-count { color: var(--muted); font-size: 11px; white-space: nowrap; }
    .review-action { color: #344054; font-size: 12px; font-weight: 650; }
    .search-controls { display: grid; grid-template-columns: minmax(220px, 1fr) auto; gap: 10px; align-items: center; }
    input[type="search"], select { box-sizing: border-box; width: 100%; border: 1px solid var(--line); border-radius: 6px; padding: 10px 11px; font: inherit; background: white; color: var(--ink); }
    textarea { box-sizing: border-box; width: 100%; border: 1px solid var(--line); border-radius: 6px; padding: 10px 11px; font: inherit; background: white; color: var(--ink); resize: vertical; min-height: 94px; }
    .search-results { display: grid; gap: 9px; margin-top: 12px; }
    .search-result { border: 1px solid #edf0f4; border-radius: 8px; padding: 10px; background: #fbfcfe; display: grid; gap: 5px; }
    .search-result-head { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; align-items: start; }
    .search-result-head-actions { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
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
    .voice-command-grid { display: grid; gap: 10px; }
    .voice-command-actions { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    .voice-command-actions button.recording { background: #fee2e2; color: var(--red); }
    .voice-command-actions button:disabled { cursor: not-allowed; }
    .voice-card { border: 1px solid var(--line); border-radius: 8px; padding: 10px; background: #f8fafc; display: grid; gap: 8px; }
    .voice-card.warn { border-color: #fbbf24; background: #fffbeb; }
    .voice-card-title { font-size: 13px; font-weight: 700; color: var(--ink); }
    .voice-card-text { color: var(--ink); font-size: 14px; line-height: 1.45; white-space: pre-wrap; overflow-wrap: anywhere; }
    .voice-card-actions { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    .voice-card.hidden { display: none; }
    .voice-transcript-row { display: grid; gap: 6px; }
    .voice-transcript-row label { color: #253047; font-size: 12px; font-weight: 750; }
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
    .button-link.secondary-link { background: #dfe5ec; color: #172033; }
    .library-modal { width: min(1180px, 100%); }
    .library-tabs { display: flex; gap: 8px; flex-wrap: wrap; }
    .library-tab.active { background: var(--blue); color: white; }
    .library-archive { border: 1px solid #edf0f4; border-radius: 8px; background: #fbfcfe; padding: 10px; display: grid; gap: 8px; }
    .library-archive-grid { display: grid; grid-template-columns: minmax(260px, 1fr) minmax(140px, 180px) minmax(140px, 220px) auto; gap: 8px; align-items: center; }
    .library-text-grid { display: grid; grid-template-columns: minmax(220px, 1fr) minmax(140px, 180px) minmax(160px, 220px) auto; gap: 8px; align-items: center; }
    .library-attachment-grid { display: grid; grid-template-columns: minmax(180px, 1fr) minmax(160px, 220px) minmax(180px, 1fr) auto; gap: 8px; align-items: center; }
    .library-text-area { min-height: 130px; resize: vertical; }
    .library-controls { display: grid; grid-template-columns: minmax(220px, 1fr) auto; gap: 10px; align-items: center; }
    .library-layout { display: grid; grid-template-columns: minmax(260px, .85fr) minmax(320px, 1.15fr); gap: 12px; align-items: start; }
    .library-list { display: grid; gap: 8px; max-height: 58vh; overflow: auto; padding-right: 4px; }
    .library-item { border: 1px solid #edf0f4; border-radius: 8px; background: #fbfcfe; padding: 10px; display: grid; gap: 5px; text-align: left; cursor: pointer; }
    .library-item.active { border-color: #93c5fd; background: #eff6ff; }
    .library-title { font-weight: 750; overflow-wrap: anywhere; }
    .library-meta { color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
    .library-reader { border: 1px solid #edf0f4; border-radius: 8px; background: #fbfcfe; min-height: 420px; display: grid; grid-template-rows: auto 1fr; overflow: hidden; }
    .library-reader-head { padding: 12px; border-bottom: 1px solid #edf0f4; display: grid; gap: 6px; background: white; }
    .library-reader-title { margin: 0; font-size: 18px; line-height: 1.25; overflow-wrap: anywhere; }
    .library-reader-text { padding: 14px 16px; white-space: pre-wrap; overflow: auto; max-height: 58vh; line-height: 1.58; font-size: 15px; background: white; }
    .library-reader-attachments { display: grid; gap: 10px; padding: 12px 16px; border-top: 1px solid #edf0f4; background: #fbfcfe; }
    .library-reader-attachments.hidden { display: none; }
    .library-attachment-card { border: 1px solid #edf0f4; border-radius: 8px; background: white; padding: 10px; display: grid; gap: 8px; }
    .library-attachment-title { font-weight: 700; overflow-wrap: anywhere; }
    .library-attachment-meta { color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
    .library-attachment-image { max-width: 100%; max-height: 420px; object-fit: contain; border: 1px solid #edf0f4; border-radius: 6px; background: #f8fafc; }
    .library-snippet { color: #344054; font-size: 12px; line-height: 1.45; overflow-wrap: anywhere; }
	    .project-toolbar { display: flex; gap: 8px; flex-wrap: wrap; }
	    .project-toolbar button.active { background: var(--blue); color: white; }
	    .voice-command-actions button.active { background: var(--blue); color: white; }
	    .project-list { display: grid; gap: 9px; }
	    .project-card { border: 1px solid #edf0f4; border-radius: 8px; padding: 11px; background: #fbfcfe; display: grid; gap: 7px; }
	    .project-card.needs-attention { border-color: #fed7aa; background: #fffaf3; }
	    .project-head { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; align-items: start; }
	    .project-title { font-weight: 750; overflow-wrap: anywhere; }
	    .project-priority { border: 1px solid var(--line); border-radius: 999px; padding: 3px 7px; font-size: 12px; background: white; color: #344054; }
	    .project-meta { color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
	    .project-next { color: #263244; font-size: 13px; line-height: 1.4; overflow-wrap: anywhere; }
	    .project-flags { display: flex; gap: 6px; flex-wrap: wrap; }
	    .project-flag { border-radius: 999px; padding: 3px 7px; font-size: 11px; background: #fff7ed; color: #9a6700; }
	    .project-flag.attention { background: #fee2e2; color: #991b1b; }
	    .project-detail { display: grid; gap: 5px; border-top: 1px solid #edf0f4; padding-top: 7px; }
	    .project-detail.hidden { display: none; }
    .quick-note-detail pre { white-space: pre-wrap; margin: 6px 0 0; max-height: 360px; overflow: auto; border: 1px solid #edf0f4; border-radius: 7px; padding: 10px; background: #fff; font-size: 13px; line-height: 1.45; }
    .quantitative-panel { display: grid; gap: 10px; }
    .quantitative-summary { display: grid; gap: 6px; }
    .quantitative-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
    .quantitative-card { border: 1px solid #edf0f4; border-radius: 8px; padding: 10px; background: #fbfcfe; display: grid; gap: 5px; }
    .quantitative-card h3 { margin: 0; font-size: 13px; color: #253047; }
    .quantitative-card pre { white-space: pre-wrap; overflow-wrap: anywhere; }
	    .quantitative-diff-list { display: grid; gap: 8px; }
	    .quantitative-diff-item { border-top: 1px solid #edf0f4; padding-top: 8px; display: grid; gap: 4px; }
	    .quantitative-diff-item:first-child { border-top: 0; padding-top: 0; }
	    .quantitative-diff-meta { color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
	    .recovery-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
		    .recovery-card { border: 1px solid #edf0f4; border-radius: 8px; padding: 10px; background: #fbfcfe; display: grid; gap: 5px; }
		    .recovery-card h3 { margin: 0; font-size: 13px; color: #253047; }
		    .recovery-list { display: grid; gap: 8px; }
		    .recovery-command { font: 12px ui-monospace, SFMono-Regular, Menlo, monospace; background: #fff; border: 1px solid #edf0f4; border-radius: 7px; padding: 8px; overflow-wrap: anywhere; }
    .diagnostics-list { display: grid; gap: 8px; }
    .diagnostics-row { border: 1px solid #edf0f4; border-radius: 8px; padding: 10px; background: #fbfcfe; display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; align-items: start; }
    .diagnostics-row-title { font-weight: 750; overflow-wrap: anywhere; }
    .diagnostics-row-meta { color: var(--muted); font-size: 12px; overflow-wrap: anywhere; margin-top: 3px; }
    .diagnostics-badge { border-radius: 999px; padding: 3px 8px; font-size: 12px; font-weight: 700; background: white; border: 1px solid var(--line); }
    .case-detail { border-top: 1px solid #edf0f4; margin-top: 8px; padding-top: 8px; display: grid; gap: 8px; }
    .case-detail.hidden { display: none; }
    .case-section-title { font-size: 12px; font-weight: 750; color: #253047; margin-top: 2px; }
    .case-status-row { border: 1px solid #edf0f4; border-radius: 8px; padding: 8px; background: #fff; display: grid; gap: 4px; }
    .case-document-row { border: 1px solid #edf0f4; border-radius: 8px; padding: 9px; background: #fbfcfe; display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; align-items: start; }
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
    .consistency-panel { display: grid; gap: 10px; }
    .consistency-panel pre { border: 1px solid #edf0f4; border-radius: 7px; padding: 10px; background: #fbfcfe; }
    .consistency-finding { border: 1px solid #edf0f4; border-radius: 8px; padding: 10px; background: #fbfcfe; display: grid; gap: 7px; }
    .consistency-finding-head { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 8px; align-items: start; }
    .consistency-finding-title { font-weight: 750; overflow-wrap: anywhere; }
    .consistency-finding-meta { color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
    .section-toggle { margin: 18px 0; }
    .section-toggle > summary,
    .service-panel > summary,
    .voice-advanced > summary {
      cursor: pointer;
      font-weight: 750;
      color: #172033;
      padding: 10px 0;
      list-style-position: inside;
    }
    .section-toggle > summary { font-size: 20px; }
    .service-panel { margin-top: 12px; border-top: 1px solid var(--line); }
    .service-actions { margin-top: 10px; }
    .voice-advanced { margin-top: 8px; border-top: 1px solid var(--line); }
    @media (max-width: 1050px) { .today-dashboard { grid-template-columns: 1fr; } .work-grid { grid-template-columns: 1fr; } }
	    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } .dashboard-metrics { grid-template-columns: 1fr; } .quick-actions { grid-template-columns: 1fr; } .health-grid { grid-template-columns: 1fr; } .search-controls { grid-template-columns: 1fr; } .search-result-head { grid-template-columns: 1fr; } .search-result-head-actions { justify-content: flex-start; } .recovery-grid { grid-template-columns: 1fr; } .janicka-grid { grid-template-columns: 1fr; } .janicka-action { grid-template-columns: 1fr; } .library-archive-grid { grid-template-columns: 1fr; } .library-text-grid { grid-template-columns: 1fr; } .library-attachment-grid { grid-template-columns: 1fr; } .library-controls { grid-template-columns: 1fr; } .library-layout { grid-template-columns: 1fr; } header { height: auto; padding: 12px 16px; align-items: flex-start; gap: 10px; flex-direction: column; } .app-card { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <header>
    <h1>Samantha Cockpit</h1>
    <div class="toolbar">
      <button class="janicka-button" id="janickaBtn">Janička</button>
      <button class="secondary" id="refreshBtn">Obnovit</button>
      <button class="secondary" id="webAppsBtn">Webové aplikace</button>
      <button class="secondary" id="libraryBtn">Knihovna</button>
      <button class="secondary" id="projectsBtn">Projekty</button>
      <button class="secondary" id="remindersBtn">Připomenutí</button>
      <button class="secondary" id="emailProcessingBtn">E-maily</button>
      <button class="secondary" id="serviceBtn">Servis</button>
      <button class="primary" id="scanDocuBtn">ScanDocu</button>
      <button class="secondary" id="scanDocuReviewBtn">Revidovat dokumenty</button>
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
          <div id="dashboardOverall" class="dashboard-overall dashboard-overall-loading" role="button" tabindex="0" title="Otevřít detail stavu">
            <span id="dashboardOverallLabel" class="dashboard-overall-label">Načítám</span>
            <span id="dashboardOverallReason" class="dashboard-overall-reason">Skládám hlavní a samostatně načítané kontroly.</span>
          </div>
          <div id="dashboardMorningSentence" class="status-line">Ranní stav se načte spolu s Cockpitem.</div>
          <div class="dashboard-row"><span class="dashboard-label">Dokumenty</span><span id="dashboardDocuments" class="dashboard-value"></span></div>
          <div class="dashboard-row"><span class="dashboard-label">Připomenutí</span><span id="dashboardReminders" class="dashboard-value"></span></div>
          <div class="dashboard-row"><span class="dashboard-label">Hlas</span><span id="dashboardVoiceMode" class="dashboard-value"></span></div>
          <div class="dashboard-row"><span class="dashboard-label">Záloha</span><span id="dashboardBackup" class="dashboard-value"></span></div>
          <div class="dashboard-row"><span class="dashboard-label">Systém</span><span id="dashboardQuantitative" class="dashboard-value"></span></div>
          <details class="service-panel">
            <summary>Další stav</summary>
            <div class="dashboard-list">
              <div class="dashboard-row"><span class="dashboard-label">ScanDocu</span><span id="dashboardScanDocu" class="dashboard-value"></span></div>
              <div class="dashboard-row"><span class="dashboard-label">Projekty</span><span id="dashboardProjects" class="dashboard-value"></span></div>
              <div class="dashboard-row"><span class="dashboard-label">Kontrola</span><span id="dashboardConsistency" class="dashboard-value"></span></div>
              <div class="dashboard-row"><span class="dashboard-label">Rychlé poznámky</span><span id="dashboardQuickNotes" class="dashboard-value"></span></div>
              <div class="dashboard-row"><span class="dashboard-label">Git</span><span id="dashboardGit" class="dashboard-value"></span></div>
            </div>
          </details>
        </div>
      </section>
      <section class="dashboard-card">
        <h2>Rychlé akce</h2>
        <div class="dashboard-body">
          <div class="quick-actions">
            <button class="primary" id="dashboardProcessBtn">Zpracovat další</button>
            <button class="secondary" id="dashboardReviewBtn">Revidovat další</button>
		        <button class="secondary" id="dashboardUrgentRemindersBtn">Důležitá připomenutí</button>
		        <button class="secondary" id="dashboardRefreshBtn">Obnovit stav</button>
	          </div>
          <div id="dashboardActionHint" class="status-line"></div>
        </div>
      </section>
	    </div>
	    <div id="statusLine" class="status-line">Načítám stav...</div>
		    <section id="urgentReminderAlert" class="urgent-alert hidden" aria-live="polite">
		      <div class="urgent-alert-head">
		        <div id="urgentReminderAlertTitle" class="urgent-alert-title">Důležitá připomenutí</div>
		        <button class="secondary" id="urgentReminderAlertBtn">Otevřít</button>
		      </div>
		      <div id="urgentReminderAlertList" class="urgent-alert-list"></div>
		    </section>
		    <section>
		      <h2>Co teď dělat</h2>
		      <div class="body">
		        <div id="actionQueueStatus" class="status-line">Načítám doporučené akce...</div>
		        <div id="actionQueueList" class="action-queue"></div>
		      </div>
		    </section>
        <details id="voiceCommandDetails" class="section-toggle">
          <summary>Hlas</summary>
		    <section id="voiceCommandPanel">
		      <h2>Hlasový pokyn</h2>
		      <div class="body voice-command-grid">
		        <div class="voice-command-actions">
		          <button class="secondary" id="voiceModeToggleBtn" aria-pressed="false">Hlasový mód: vypnuto</button>
		          <button class="secondary" id="voiceModeStartBtn">Spustit Adamův poslech</button>
		          <button class="secondary" id="voiceModeStopBtn">Zastavit poslech</button>
		          <button class="primary" id="voiceRecordBtn">Nahrát hlasový pokyn</button>
		          <button class="secondary" id="voiceStopBtn" disabled>Zastavit a přepsat</button>
		          <button class="primary" id="voiceTranscriptSendBtn">Odeslat přepis Adamovi</button>
		        </div>
		        <div id="voiceCommandStatus" class="status-line">Pokyn se po přepisu automaticky uloží pro Codex. Adam reaguje jen při spuštěném watcheru.</div>
            <details class="voice-advanced">
              <summary>Pokročilé</summary>
		          <div id="voiceModeRuntimeStatus" class="status-line">Adam Voice Mode watcher: čekám na kontrolu.</div>
		          <div id="voiceBridgeStatus" class="status-line">Terminálový bridge: čekám na kontrolu.</div>
		          <div id="voiceBridgeSessions" class="status-line">Codex relace: čekám na kontrolu.</div>
		          <div id="voiceBridgeSwitcher" class="voice-card hidden">
		            <div class="voice-card-title">Voice bridge cíl</div>
		            <div id="voiceBridgeSwitcherStatus" class="status-line">Načítám dostupné Codex relace.</div>
		            <div id="voiceBridgeSwitcherActions" class="voice-card-actions"></div>
		          </div>
            </details>
		        <div id="voicePendingStatus" class="status-line">Žádný hlasový pokyn nečeká na Adama.</div>
		        <div id="voiceLastResponseCard" class="voice-card hidden">
		          <div class="voice-card-title">Poslední Adamova odpověď</div>
		          <div id="voiceLastResponseText" class="voice-card-text"></div>
		          <div class="voice-card-actions">
		            <button class="secondary" id="voiceLastResponseSpeakBtn">Přehrát Adamovu odpověď</button>
		          </div>
		        </div>
		        <div id="voiceApprovalCard" class="voice-card warn hidden">
		          <div class="voice-card-title">Schválení přes Cockpit</div>
		          <div id="voiceApprovalReason" class="status-line"></div>
		          <div id="voiceApprovalText" class="voice-card-text"></div>
		          <div class="voice-card-actions">
		            <button class="primary" id="voiceApprovalApproveBtn">Schválit</button>
		            <button class="secondary" id="voiceApprovalRejectBtn">Zamítnout</button>
		          </div>
		        </div>
	        <div class="voice-transcript-row">
	          <label for="voiceTranscript">Přepis</label>
	          <textarea id="voiceTranscript" placeholder="Tady se objeví přepsaný hlasový pokyn." spellcheck="true"></textarea>
	        </div>
	      </div>
	    </section>
        </details>
    <details id="documentsPanel" class="section-toggle">
      <summary>Dokumenty</summary>
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
            <div class="status-line">Akční chyby ve frontě</div>
            <div id="problemList" class="work-list"></div>
          </div>
          <div class="work-card">
            <h3>Dokumentový intake</h3>
            <div id="documentIntakeCount" class="work-count">0</div>
            <div id="documentIntakeSummary" class="status-line">Downloads / e-mail / mobilní sken / lokální inbox</div>
            <div id="documentIntakeList" class="work-list"></div>
          </div>
          <div class="work-card">
            <h3>Související dokumenty</h3>
            <div id="documentCasesCount" class="work-count">0</div>
            <div id="documentCasesStatus" class="status-line">Seskupení podle věci nebo protistrany.</div>
            <div id="documentCasesList" class="work-list"></div>
          </div>
          <div class="work-card">
            <h3>Klasifikace</h3>
            <div id="documentClassificationCount" class="work-count">0</div>
            <div id="documentClassificationStatus" class="status-line">Kvalita metadat dokumentů.</div>
            <div id="documentClassificationList" class="work-list"></div>
          </div>
          <div class="work-card">
            <h3>Termíny v dokumentech</h3>
            <div id="documentDueCount" class="work-count">0</div>
            <div id="documentDueStatus" class="status-line">Kandidáti na připomínky z dokumentů.</div>
            <div id="documentDueList" class="work-list"></div>
          </div>
          <div class="work-card">
            <h3>Dokumenty k revizi</h3>
            <div id="reviewReportCount" class="work-count">0</div>
            <div class="actions">
              <button class="secondary" id="reviewReportBtn">Načíst report</button>
            </div>
            <div id="reviewReportStatus" class="status-line">Report zatím není načtený. Skupiny: Bez textu / OCR, Krátký text, Doplnit údaje, K revizi, V pořádku.</div>
            <div id="reviewReportList" class="work-list review-report-list"></div>
          </div>
        </div>
      </div>
    </section>
    </details>
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
    <details id="servicePanel" class="section-toggle">
      <summary>Servis</summary>
      <section>
        <h2>Servisní akce</h2>
        <div class="body">
          <div class="quick-actions service-actions">
            <button class="secondary" id="dashboardTerminalBtn">Terminál v projektu</button>
            <button class="secondary" id="dashboardQuantitativeBtn">Systémový souhrn</button>
            <button class="secondary" id="dashboardQuickNotesBtn">Rychlé poznámky</button>
            <button class="secondary" id="dashboardRecoveryBtn">Recovery centrum</button>
            <button class="secondary" id="dashboardDiagnosticsBtn">Diagnostika</button>
            <button class="secondary" id="dashboardRestartBtn">Restart Cockpitu</button>
            <button class="secondary" id="dashboardSpeakBtn">Přečíst stav</button>
            <button class="secondary" id="dashboardSpeakSelectionBtn">Přečíst výběr</button>
          </div>
        </div>
      </section>
      <section>
        <h2>Technický stav Cockpitu</h2>
        <div class="body">
		      <div id="frontendHealthPanel" class="health-panel" aria-label="Health stav Cockpitu">
		        <div class="health-grid">
		          <div class="health-item"><span class="health-label">Frontend</span><span id="frontendHealthJs" class="health-value warn">JS se zatím nespustil</span></div>
		          <div class="health-item"><span class="health-label">Tlačítka</span><span id="frontendHealthButtons" class="health-value warn">čekám na napojení</span></div>
		          <div class="health-item"><span class="health-label">API</span><span id="frontendHealthApi" class="health-value warn">čekám na kontrolu</span></div>
		          <div class="health-item"><span class="health-label">Poslední chyba</span><span id="frontendHealthError" class="health-value ok">žádná</span></div>
		        </div>
		      </div>
        </div>
      </section>
      <h2>Servisní přehledy</h2>
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
    <section>
      <h2>Kontrola nesrovnalostí</h2>
      <div class="body"><div id="consistencyText" class="consistency-panel"></div></div>
    </section>
    </details>
  </main>
  <div id="janickaModal" class="modal-backdrop hidden" role="dialog" aria-modal="true" aria-labelledby="janickaTitle">
    <div class="modal janicka-modal">
      <div class="modal-header">
        <h2 id="janickaTitle">Janička</h2>
        <button class="secondary" id="janickaCloseBtn">Zavřít</button>
      </div>
      <div class="modal-body">
        <div class="janicka-intro">
          <h3 class="janicka-title">Samantha bez technické vrstvy</h3>
          <p class="janicka-subtitle">Tahle obrazovka je vstup pro Janu. Neomezuje přístup; jen převádí hotové části Samanthy do srozumitelných kroků.</p>
        </div>
        <div class="janicka-grid" aria-label="Janička rozcestník">
          <div class="janicka-action">
            <div>
              <div class="janicka-action-title">Najít dokument</div>
              <div class="janicka-action-text">Vyhledat smlouvu, fakturu, dopis nebo jiný uložený dokument.</div>
            </div>
            <button id="janickaFindDocumentBtn" type="button">Hledat</button>
          </div>
          <div class="janicka-action">
            <div>
              <div class="janicka-action-title">Vytisknout dokument</div>
              <div class="janicka-action-text">Nejdřív dokument najít, pak v detailu použít tisk.</div>
            </div>
            <button id="janickaPrintDocumentBtn" type="button">Najít k tisku</button>
          </div>
          <div class="janicka-action">
            <div>
              <div class="janicka-action-title">E-maily</div>
              <div class="janicka-action-text">Otevřít pracovní přehled e-mailů a jejich příloh.</div>
            </div>
            <button id="janickaEmailBtn" type="button">Otevřít</button>
          </div>
          <div class="janicka-action">
            <div>
              <div class="janicka-action-title">Lékárna</div>
              <div class="janicka-action-text">Najít domácí léky podle názvu nebo potíží.</div>
            </div>
            <button id="janickaLekarnaBtn" type="button">Otevřít</button>
          </div>
          <div class="janicka-action">
            <div>
              <div class="janicka-action-title">Rodinné projekty</div>
              <div class="janicka-action-text">Otevřít připravené rodinné fotky a videa, například USA.</div>
            </div>
            <button id="janickaFamilyBtn" type="button">Otevřít</button>
          </div>
          <div class="janicka-action">
            <div>
              <div class="janicka-action-title">Zeptat se Adama</div>
              <div class="janicka-action-text">Napsat nebo nadiktovat běžný pokyn bez technických příkazů.</div>
            </div>
            <button id="janickaAskAdamBtn" type="button">Zeptat se</button>
          </div>
          <div class="janicka-action">
            <div>
              <div class="janicka-action-title">Připomenutí</div>
              <div class="janicka-action-text">Zobrazit důležité termíny a otevřené připomínky.</div>
            </div>
            <button id="janickaRemindersBtn" type="button">Zobrazit</button>
          </div>
          <div class="janicka-action">
            <div>
              <div class="janicka-action-title">Nouzové převzetí</div>
              <div class="janicka-action-text">Otevřít recovery přehled a odkazy na navazující pozůstalostní plán.</div>
            </div>
            <button class="secondary" id="janickaRecoveryBtn" type="button">Otevřít</button>
          </div>
        </div>
        <div class="janicka-note">Vývoj, terminál a diagnostika zůstávají v běžném Cockpitu. Jana sem nemá chodit přes technické pojmy; má začít tím, co potřebuje udělat.</div>
        <div class="actions">
          <button class="secondary" id="janickaWebAppsBtn" type="button">Všechny aplikace</button>
          <button class="secondary" id="janickaProjectsBtn" type="button">Projekty</button>
          <button class="secondary" id="janickaCookbookBtn" type="button">Kuchařka</button>
        </div>
      </div>
    </div>
  </div>
  <button class="janicka-return hidden" id="janickaReturnBtn" type="button">Zpět k Janičce</button>
  <div id="janickaChatModal" class="modal-backdrop hidden" role="dialog" aria-modal="true" aria-labelledby="janickaChatTitle">
    <div class="modal janicka-chat-modal">
      <div class="modal-header">
        <h2 id="janickaChatTitle">Zeptat se Adama</h2>
        <button class="secondary" id="janickaChatCloseBtn">Zpět k Janičce</button>
      </div>
      <div class="modal-body">
        <div class="janicka-intro">
          <h3 class="janicka-title">Textový chat</h3>
          <p class="janicka-subtitle">Napiš běžnou větou, co potřebuješ. Cockpit Adama podle potřeby spustí a předá mu dotaz.</p>
        </div>
        <div class="janicka-chat-runtime">
          <div id="janickaAdamStatus" class="status-line">Adam: čekám na kontrolu.</div>
          <div class="actions compact-actions">
            <button class="secondary" id="janickaAdamStartBtn" type="button">Spustit Adama</button>
            <button class="secondary" id="janickaAdamRestartBtn" type="button">Restartovat</button>
            <button class="secondary" id="janickaAdamStopBtn" type="button">Zastavit</button>
          </div>
        </div>
        <div id="janickaChatLog" class="janicka-chat-log" aria-live="polite"></div>
        <div class="janicka-chat-input">
          <label for="janickaChatInput">Otázka nebo pokyn</label>
          <textarea id="janickaChatInput" spellcheck="true" placeholder="Například: Najdi mi dokument k pojištění auta."></textarea>
          <div class="actions">
            <button class="primary" id="janickaChatSendBtn" type="button">Odeslat Adamovi</button>
            <button class="secondary" id="janickaChatClearBtn" type="button">Vyčistit chat</button>
          </div>
          <div id="janickaChatStatus" class="status-line">Připraveno.</div>
        </div>
      </div>
    </div>
  </div>
  <div id="remindersModal" class="modal-backdrop hidden" role="dialog" aria-modal="true" aria-labelledby="remindersTitle">
    <div class="modal">
      <div class="modal-header">
        <h2 id="remindersTitle">Připomenutí</h2>
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
  <div id="libraryModal" class="modal-backdrop hidden" role="dialog" aria-modal="true" aria-labelledby="libraryTitle">
    <div class="modal library-modal">
      <div class="modal-header">
        <h2 id="libraryTitle">Knihovna</h2>
        <button class="secondary" id="libraryCloseBtn">Zavřít</button>
      </div>
      <div class="modal-body">
        <div class="library-archive">
          <div class="library-archive-grid">
            <input id="libraryArchiveUrlInput" type="url" placeholder="Vložit URL článku">
            <select id="libraryArchiveCategory">
              <option value="recipes">Recepty</option>
              <option value="science">Vědecké články</option>
              <option value="other" selected>Ostatní</option>
            </select>
            <input id="libraryArchiveTagsInput" type="text" placeholder="Tagy, volitelné">
            <button class="primary" id="libraryArchiveBtn" type="button">Uložit URL</button>
          </div>
          <div id="libraryArchiveStatus" class="status-line">Vlož URL, vyber kategorii a ulož ji do soukromé knihovny.</div>
          <div class="library-text-grid">
            <input id="libraryTextTitleInput" type="text" placeholder="Název vloženého textu">
            <select id="libraryTextCategory">
              <option value="recipes">Recepty</option>
              <option value="science">Vědecké články</option>
              <option value="other" selected>Ostatní</option>
            </select>
            <input id="libraryTextSourceInput" type="text" placeholder="Zdroj, volitelné">
            <button class="primary" id="libraryTextSaveBtn" type="button">Uložit text</button>
          </div>
          <input id="libraryTextTagsInput" type="text" placeholder="Tagy pro vložený text, volitelné">
          <textarea id="libraryTextBodyInput" class="library-text-area" placeholder="Vložit text receptu, poznámky nebo výstřižku"></textarea>
          <div id="libraryTextStatus" class="status-line">Text bez URL se uloží jako interní znalostní karta.</div>
          <div class="library-attachment-grid">
            <input id="libraryAttachmentFileInput" type="file" accept="image/*">
            <input id="libraryAttachmentLabelInput" type="text" placeholder="Popisek obrázku">
            <input id="libraryAttachmentTagsInput" type="text" placeholder="Tagy, volitelné">
            <button class="primary" id="libraryAttachmentSaveBtn" type="button">Připojit obrázek</button>
          </div>
          <input id="libraryAttachmentNoteInput" type="text" placeholder="Poznámka k obrázku, volitelné">
          <div id="libraryAttachmentStatus" class="status-line">Vyber kartu v seznamu a připoj k ní scan, fotku nebo obrázek.</div>
        </div>
        <div class="library-tabs" aria-label="Kategorie knihovny">
          <button class="secondary library-tab active" type="button" data-library-category="recipes">Recepty</button>
          <button class="secondary library-tab" type="button" data-library-category="science">Vědecké články</button>
          <button class="secondary library-tab" type="button" data-library-category="other">Ostatní</button>
        </div>
        <div class="library-controls">
          <input id="librarySearchInput" type="search" placeholder="Hledat ve vybrané kategorii">
          <button class="primary" id="librarySearchBtn" type="button">Hledat</button>
        </div>
        <div id="libraryStatus" class="status-line">Načítám knihovnu...</div>
        <div class="library-layout">
          <div id="libraryList" class="library-list"></div>
          <div class="library-reader" aria-live="polite">
            <div class="library-reader-head">
              <h3 id="libraryReaderTitle" class="library-reader-title">Vyber článek</h3>
              <div id="libraryReaderMeta" class="library-meta">Vlevo vyber položku nebo použij fulltextové hledání.</div>
            </div>
            <div id="libraryReaderText" class="library-reader-text"></div>
            <div id="libraryReaderAttachments" class="library-reader-attachments hidden"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div id="projectsModal" class="modal-backdrop hidden" role="dialog" aria-modal="true" aria-labelledby="projectsTitle">
    <div class="modal">
      <div class="modal-header">
        <h2 id="projectsTitle">Projekty a schopnosti</h2>
        <button class="secondary" id="projectsCloseBtn">Zavřít</button>
      </div>
      <div class="modal-body">
        <div id="projectsStatus" class="status-line">Načítám projekty a schopnosti...</div>
        <div class="project-toolbar" aria-label="Filtr projektů a schopností">
          <button class="secondary active" type="button" data-project-filter="all">Vše</button>
          <button class="secondary" type="button" data-project-filter="projects">Projekty</button>
          <button class="secondary" type="button" data-project-filter="archived">Archiv</button>
          <button class="secondary" type="button" data-project-filter="tools">Tooly</button>
          <button class="secondary" type="button" data-project-filter="infrastructure">Vrstvy</button>
	          <button class="secondary" type="button" data-project-filter="priority1">Priorita 1</button>
	          <button class="secondary" type="button" data-project-filter="remind">Připomenout</button>
	          <button class="secondary" type="button" data-project-filter="waiting">Čeká na mě</button>
	          <button class="secondary" type="button" data-project-filter="needs_attention">Doplnit</button>
	        </div>
        <div id="projectsList" class="project-list"></div>
      </div>
    </div>
  </div>
	  <div id="quickNotesModal" class="modal-backdrop hidden" role="dialog" aria-modal="true" aria-labelledby="quickNotesTitle">
	    <div class="modal">
	      <div class="modal-header">
	        <h2 id="quickNotesTitle">Rychlé poznámky</h2>
        <button class="secondary" id="quickNotesCloseBtn">Zavřít</button>
      </div>
      <div class="modal-body">
        <div id="quickNotesStatus" class="status-line">Načítám rychlé poznámky...</div>
        <div id="quickNotesList" class="project-list"></div>
	      </div>
	    </div>
	  </div>
	  <div id="urgentRemindersModal" class="modal-backdrop hidden" role="dialog" aria-modal="true" aria-labelledby="urgentRemindersTitle">
	    <div class="modal">
	      <div class="modal-header">
	        <h2 id="urgentRemindersTitle">Důležitá připomenutí</h2>
        <button class="secondary" id="urgentRemindersCloseBtn">Zavřít</button>
      </div>
      <div class="modal-body">
        <div id="urgentRemindersStatus" class="status-line">Načítám důležitá připomenutí...</div>
        <div id="urgentRemindersList" class="project-list"></div>
	      </div>
	    </div>
	  </div>
		  <div id="recoveryModal" class="modal-backdrop hidden" role="dialog" aria-modal="true" aria-labelledby="recoveryTitle">
		    <div class="modal">
		      <div class="modal-header">
		        <h2 id="recoveryTitle">Recovery centrum</h2>
	        <button class="secondary" id="recoveryCloseBtn">Zavřít</button>
	      </div>
	      <div class="modal-body">
	        <div id="recoveryStatus" class="status-line">Načítám recovery stav...</div>
	        <div class="recovery-grid">
	          <div class="recovery-card">
	            <h3>Autosave</h3>
	            <div id="recoveryAutosave" class="project-meta"></div>
	          </div>
	          <div class="recovery-card">
	            <h3>Git</h3>
	            <div id="recoveryGit" class="project-meta"></div>
	          </div>
	        </div>
	        <div class="recovery-card">
	          <h3>Aktivní navázání</h3>
	          <div id="recoveryProject" class="project-next"></div>
	        </div>
	        <div class="recovery-card">
	          <h3>Handoffy</h3>
	          <div id="recoveryHandoffs" class="recovery-list"></div>
	        </div>
	        <div class="recovery-card">
	          <h3>Příkazy</h3>
	          <div id="recoveryCommands" class="recovery-list"></div>
	        </div>
		      </div>
		    </div>
		  </div>
	  <div id="diagnosticsModal" class="modal-backdrop hidden" role="dialog" aria-modal="true" aria-labelledby="diagnosticsTitle">
	    <div class="modal">
	      <div class="modal-header">
	        <h2 id="diagnosticsTitle">Diagnostika</h2>
	        <button class="secondary" id="diagnosticsCloseBtn">Zavřít</button>
	      </div>
	      <div class="modal-body">
	        <div id="diagnosticsStatus" class="status-line">Načítám diagnostiku...</div>
	        <div class="recovery-card">
	          <h3>Stav</h3>
	          <div id="diagnosticsStatusSignals" class="diagnostics-list"></div>
	        </div>
	        <div class="recovery-card">
	          <h3>Frontend</h3>
	          <div id="diagnosticsFrontend" class="project-meta"></div>
	        </div>
	        <div class="recovery-card">
	          <h3>Endpointy</h3>
	          <div id="diagnosticsEndpointList" class="diagnostics-list"></div>
	        </div>
	        <div class="recovery-card">
	          <h3>Poslední chyby</h3>
	          <div id="diagnosticsErrorList" class="diagnostics-list"></div>
	        </div>
	      </div>
	    </div>
	  </div>
		  <div id="quantitativeModal" class="modal-backdrop hidden" role="dialog" aria-modal="true" aria-labelledby="quantitativeTitle">
    <div class="modal">
      <div class="modal-header">
        <h2 id="quantitativeTitle">Systémový souhrn</h2>
        <button class="secondary" id="quantitativeCloseBtn">Zavřít</button>
      </div>
      <div class="modal-body quantitative-panel">
        <div id="quantitativeStatus" class="status-line">Načítám kvantitativní status...</div>
        <div class="quantitative-grid">
          <div class="quantitative-card">
            <h3>Aktuální stav</h3>
            <pre id="quantitativeCurrent"></pre>
          </div>
          <div class="quantitative-card">
            <h3>Poslední snapshot</h3>
            <pre id="quantitativePrevious"></pre>
          </div>
        </div>
        <div class="quantitative-card">
          <h3>Diff</h3>
          <div id="quantitativeDiffTotals" class="quantitative-summary"></div>
          <div id="quantitativeDiffList" class="quantitative-diff-list"></div>
        </div>
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
    const webAppsBtn = document.getElementById("webAppsBtn");
    const libraryBtn = document.getElementById("libraryBtn");
    const projectsBtn = document.getElementById("projectsBtn");
    const remindersBtn = document.getElementById("remindersBtn");
    const emailProcessingBtn = document.getElementById("emailProcessingBtn");
    const serviceBtn = document.getElementById("serviceBtn");
    const servicePanel = document.getElementById("servicePanel");
    const janickaBtn = document.getElementById("janickaBtn");
    const janickaModal = document.getElementById("janickaModal");
    const janickaCloseBtn = document.getElementById("janickaCloseBtn");
    const janickaFindDocumentBtn = document.getElementById("janickaFindDocumentBtn");
    const janickaPrintDocumentBtn = document.getElementById("janickaPrintDocumentBtn");
    const janickaEmailBtn = document.getElementById("janickaEmailBtn");
    const janickaLekarnaBtn = document.getElementById("janickaLekarnaBtn");
    const janickaFamilyBtn = document.getElementById("janickaFamilyBtn");
    const janickaAskAdamBtn = document.getElementById("janickaAskAdamBtn");
    const janickaRemindersBtn = document.getElementById("janickaRemindersBtn");
    const janickaRecoveryBtn = document.getElementById("janickaRecoveryBtn");
    const janickaWebAppsBtn = document.getElementById("janickaWebAppsBtn");
    const janickaProjectsBtn = document.getElementById("janickaProjectsBtn");
    const janickaCookbookBtn = document.getElementById("janickaCookbookBtn");
    const janickaReturnBtn = document.getElementById("janickaReturnBtn");
    const janickaChatModal = document.getElementById("janickaChatModal");
    const janickaChatCloseBtn = document.getElementById("janickaChatCloseBtn");
    const janickaChatLog = document.getElementById("janickaChatLog");
    const janickaChatInput = document.getElementById("janickaChatInput");
    const janickaChatSendBtn = document.getElementById("janickaChatSendBtn");
    const janickaChatClearBtn = document.getElementById("janickaChatClearBtn");
    const janickaChatStatus = document.getElementById("janickaChatStatus");
    const janickaAdamStatus = document.getElementById("janickaAdamStatus");
    const janickaAdamStartBtn = document.getElementById("janickaAdamStartBtn");
    const janickaAdamRestartBtn = document.getElementById("janickaAdamRestartBtn");
    const janickaAdamStopBtn = document.getElementById("janickaAdamStopBtn");
    const remindersModal = document.getElementById("remindersModal");
    const remindersCloseBtn = document.getElementById("remindersCloseBtn");
    const remindersStatus = document.getElementById("remindersStatus");
    const remindersList = document.getElementById("remindersList");
    const webAppsModal = document.getElementById("webAppsModal");
    const webAppsCloseBtn = document.getElementById("webAppsCloseBtn");
    const webAppsStatus = document.getElementById("webAppsStatus");
    const webAppsList = document.getElementById("webAppsList");
    const libraryModal = document.getElementById("libraryModal");
    const libraryCloseBtn = document.getElementById("libraryCloseBtn");
    const libraryStatus = document.getElementById("libraryStatus");
    const libraryArchiveUrlInput = document.getElementById("libraryArchiveUrlInput");
    const libraryArchiveCategory = document.getElementById("libraryArchiveCategory");
    const libraryArchiveTagsInput = document.getElementById("libraryArchiveTagsInput");
    const libraryArchiveBtn = document.getElementById("libraryArchiveBtn");
    const libraryArchiveStatus = document.getElementById("libraryArchiveStatus");
    const libraryTextTitleInput = document.getElementById("libraryTextTitleInput");
    const libraryTextCategory = document.getElementById("libraryTextCategory");
    const libraryTextSourceInput = document.getElementById("libraryTextSourceInput");
    const libraryTextSaveBtn = document.getElementById("libraryTextSaveBtn");
    const libraryTextTagsInput = document.getElementById("libraryTextTagsInput");
    const libraryTextBodyInput = document.getElementById("libraryTextBodyInput");
    const libraryTextStatus = document.getElementById("libraryTextStatus");
    const libraryAttachmentFileInput = document.getElementById("libraryAttachmentFileInput");
    const libraryAttachmentLabelInput = document.getElementById("libraryAttachmentLabelInput");
    const libraryAttachmentTagsInput = document.getElementById("libraryAttachmentTagsInput");
    const libraryAttachmentNoteInput = document.getElementById("libraryAttachmentNoteInput");
    const libraryAttachmentSaveBtn = document.getElementById("libraryAttachmentSaveBtn");
    const libraryAttachmentStatus = document.getElementById("libraryAttachmentStatus");
    const librarySearchInput = document.getElementById("librarySearchInput");
    const librarySearchBtn = document.getElementById("librarySearchBtn");
    const libraryList = document.getElementById("libraryList");
    const libraryReaderTitle = document.getElementById("libraryReaderTitle");
    const libraryReaderMeta = document.getElementById("libraryReaderMeta");
    const libraryReaderText = document.getElementById("libraryReaderText");
    const libraryReaderAttachments = document.getElementById("libraryReaderAttachments");
    const projectsModal = document.getElementById("projectsModal");
    const projectsCloseBtn = document.getElementById("projectsCloseBtn");
    const projectsStatus = document.getElementById("projectsStatus");
    const projectsList = document.getElementById("projectsList");
    const quickNotesModal = document.getElementById("quickNotesModal");
	    const quickNotesCloseBtn = document.getElementById("quickNotesCloseBtn");
	    const quickNotesStatus = document.getElementById("quickNotesStatus");
	    const quickNotesList = document.getElementById("quickNotesList");
    const urgentRemindersModal = document.getElementById("urgentRemindersModal");
    const urgentRemindersCloseBtn = document.getElementById("urgentRemindersCloseBtn");
    const urgentRemindersStatus = document.getElementById("urgentRemindersStatus");
    const urgentRemindersList = document.getElementById("urgentRemindersList");
	    const recoveryModal = document.getElementById("recoveryModal");
	    const recoveryCloseBtn = document.getElementById("recoveryCloseBtn");
	    const recoveryStatus = document.getElementById("recoveryStatus");
	    const recoveryAutosave = document.getElementById("recoveryAutosave");
	    const recoveryGit = document.getElementById("recoveryGit");
		    const recoveryProject = document.getElementById("recoveryProject");
		    const recoveryHandoffs = document.getElementById("recoveryHandoffs");
		    const recoveryCommands = document.getElementById("recoveryCommands");
    const diagnosticsModal = document.getElementById("diagnosticsModal");
    const diagnosticsCloseBtn = document.getElementById("diagnosticsCloseBtn");
    const diagnosticsStatus = document.getElementById("diagnosticsStatus");
    const diagnosticsStatusSignals = document.getElementById("diagnosticsStatusSignals");
    const diagnosticsFrontend = document.getElementById("diagnosticsFrontend");
    const diagnosticsEndpointList = document.getElementById("diagnosticsEndpointList");
    const diagnosticsErrorList = document.getElementById("diagnosticsErrorList");
		    const quantitativeModal = document.getElementById("quantitativeModal");
    const quantitativeCloseBtn = document.getElementById("quantitativeCloseBtn");
    const quantitativeStatus = document.getElementById("quantitativeStatus");
    const quantitativeCurrent = document.getElementById("quantitativeCurrent");
    const quantitativePrevious = document.getElementById("quantitativePrevious");
    const quantitativeDiffTotals = document.getElementById("quantitativeDiffTotals");
    const quantitativeDiffList = document.getElementById("quantitativeDiffList");
    const todayNewPdfCount = document.getElementById("todayNewPdfCount");
    const todayReviewCount = document.getElementById("todayReviewCount");
    const todayProblemCount = document.getElementById("todayProblemCount");
    const todayHint = document.getElementById("todayHint");
    const dashboardDocuments = document.getElementById("dashboardDocuments");
    const dashboardScanDocu = document.getElementById("dashboardScanDocu");
    const dashboardReminders = document.getElementById("dashboardReminders");
    const dashboardVoiceMode = document.getElementById("dashboardVoiceMode");
    const dashboardProjects = document.getElementById("dashboardProjects");
    const dashboardQuantitative = document.getElementById("dashboardQuantitative");
    const dashboardConsistency = document.getElementById("dashboardConsistency");
    const dashboardQuickNotes = document.getElementById("dashboardQuickNotes");
    const dashboardBackup = document.getElementById("dashboardBackup");
    const dashboardGit = document.getElementById("dashboardGit");
    const dashboardOverall = document.getElementById("dashboardOverall");
    const dashboardOverallLabel = document.getElementById("dashboardOverallLabel");
    const dashboardOverallReason = document.getElementById("dashboardOverallReason");
    const dashboardMorningSentence = document.getElementById("dashboardMorningSentence");
    const dashboardProcessBtn = document.getElementById("dashboardProcessBtn");
    const dashboardReviewBtn = document.getElementById("dashboardReviewBtn");
    const dashboardTerminalBtn = document.getElementById("dashboardTerminalBtn");
		    const dashboardQuantitativeBtn = document.getElementById("dashboardQuantitativeBtn");
		    const dashboardQuickNotesBtn = document.getElementById("dashboardQuickNotesBtn");
    const dashboardUrgentRemindersBtn = document.getElementById("dashboardUrgentRemindersBtn");
    const dashboardRecoveryBtn = document.getElementById("dashboardRecoveryBtn");
    const dashboardDiagnosticsBtn = document.getElementById("dashboardDiagnosticsBtn");
    const dashboardRestartBtn = document.getElementById("dashboardRestartBtn");
			    const dashboardSpeakBtn = document.getElementById("dashboardSpeakBtn");
			    const dashboardSpeakSelectionBtn = document.getElementById("dashboardSpeakSelectionBtn");
			    const dashboardRefreshBtn = document.getElementById("dashboardRefreshBtn");
    const dashboardActionHint = document.getElementById("dashboardActionHint");
    const voiceCommandDetails = document.getElementById("voiceCommandDetails");
    const voiceModeToggleBtn = document.getElementById("voiceModeToggleBtn");
    const voiceModeStartBtn = document.getElementById("voiceModeStartBtn");
    const voiceModeStopBtn = document.getElementById("voiceModeStopBtn");
    const voiceRecordBtn = document.getElementById("voiceRecordBtn");
    const voiceStopBtn = document.getElementById("voiceStopBtn");
    const voiceCommandStatus = document.getElementById("voiceCommandStatus");
    const voiceModeRuntimeStatus = document.getElementById("voiceModeRuntimeStatus");
    const voiceBridgeStatus = document.getElementById("voiceBridgeStatus");
    const voiceBridgeSessions = document.getElementById("voiceBridgeSessions");
    const voiceBridgeSwitcher = document.getElementById("voiceBridgeSwitcher");
    const voiceBridgeSwitcherStatus = document.getElementById("voiceBridgeSwitcherStatus");
    const voiceBridgeSwitcherActions = document.getElementById("voiceBridgeSwitcherActions");
    const voicePendingStatus = document.getElementById("voicePendingStatus");
    const voiceLastResponseCard = document.getElementById("voiceLastResponseCard");
    const voiceLastResponseText = document.getElementById("voiceLastResponseText");
    const voiceLastResponseSpeakBtn = document.getElementById("voiceLastResponseSpeakBtn");
    const voiceApprovalCard = document.getElementById("voiceApprovalCard");
    const voiceApprovalReason = document.getElementById("voiceApprovalReason");
    const voiceApprovalText = document.getElementById("voiceApprovalText");
    const voiceApprovalApproveBtn = document.getElementById("voiceApprovalApproveBtn");
    const voiceApprovalRejectBtn = document.getElementById("voiceApprovalRejectBtn");
    const voiceTranscript = document.getElementById("voiceTranscript");
    const voiceTranscriptSendBtn = document.getElementById("voiceTranscriptSendBtn");
    const urgentReminderAlert = document.getElementById("urgentReminderAlert");
    const urgentReminderAlertTitle = document.getElementById("urgentReminderAlertTitle");
    const urgentReminderAlertList = document.getElementById("urgentReminderAlertList");
    const urgentReminderAlertBtn = document.getElementById("urgentReminderAlertBtn");
    const newPdfCount = document.getElementById("newPdfCount");
    const reviewCount = document.getElementById("reviewCount");
    const problemCount = document.getElementById("problemCount");
    const newPdfList = document.getElementById("newPdfList");
    const reviewList = document.getElementById("reviewList");
    const problemList = document.getElementById("problemList");
    const documentIntakeCount = document.getElementById("documentIntakeCount");
    const documentIntakeSummary = document.getElementById("documentIntakeSummary");
    const documentIntakeList = document.getElementById("documentIntakeList");
    const documentCasesCount = document.getElementById("documentCasesCount");
    const documentCasesStatus = document.getElementById("documentCasesStatus");
    const documentCasesList = document.getElementById("documentCasesList");
    const documentClassificationCount = document.getElementById("documentClassificationCount");
    const documentClassificationStatus = document.getElementById("documentClassificationStatus");
    const documentClassificationList = document.getElementById("documentClassificationList");
    const documentDueCount = document.getElementById("documentDueCount");
    const documentDueStatus = document.getElementById("documentDueStatus");
    const documentDueList = document.getElementById("documentDueList");
    const reviewReportCount = document.getElementById("reviewReportCount");
    const reviewReportBtn = document.getElementById("reviewReportBtn");
    const reviewReportStatus = document.getElementById("reviewReportStatus");
    const reviewReportList = document.getElementById("reviewReportList");
    const documentSearchInput = document.getElementById("documentSearchInput");
    const documentSearchBtn = document.getElementById("documentSearchBtn");
    const documentSearchStatus = document.getElementById("documentSearchStatus");
    const documentSearchResults = document.getElementById("documentSearchResults");
    const frontendHealthJs = document.getElementById("frontendHealthJs");
    const frontendHealthButtons = document.getElementById("frontendHealthButtons");
    const frontendHealthApi = document.getElementById("frontendHealthApi");
    const frontendHealthError = document.getElementById("frontendHealthError");
    const actionQueueStatus = document.getElementById("actionQueueStatus");
    const actionQueueList = document.getElementById("actionQueueList");
    const readingStatusOptions = [
      ["ok", "OK"],
      ["needs_review", "k revizi"],
      ["unreadable", "nečitelné"],
      ["superseded", "nahrazeno lepší kopií"]
    ];
    let currentProjects = [];
    let currentProjectFilter = "all";
    let currentLibraryCategory = "recipes";
    let currentLibraryItems = [];
    let currentLibrarySelectedId = "";
    let currentQuantitative = null;
    let frontendLastError = "";
    let frontendErrorHistory = [];
    let dashboardStatusSignals = {};

    function escapeHtml(value) {
      return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }

    const diagnosticsEndpoints = [
      ["Hlavní status", "/api/status"],
      ["Recovery", "/api/recovery/status"],
      ["Webové aplikace", "/api/web-apps"],
      ["Knihovna", "/api/library/list?category=other&limit=1"],
      ["Projekty", "/api/projects/status"],
      ["Quick Notes", "/api/quick-notes/status"],
      ["Důležitá připomenutí", "/api/urgent-reminders/status"],
      ["Kvantitativní", "/api/quantitative-status"],
      ["Consistency audit", "/api/consistency-status"],
      ["Dokumenty k revizi", "/api/documents/review-report"]
    ];

    function setHealthValue(node, text, className) {
      if (!node) return;
      node.textContent = text;
      node.className = `health-value ${className || ""}`.trim();
    }

    function recordFrontendError(error) {
      const text = String(error && (error.message || error.reason || error) || "neznámá chyba");
      frontendLastError = text;
      frontendErrorHistory = [
        {createdAt: new Date().toISOString(), text},
        ...frontendErrorHistory
      ].slice(0, 8);
      setHealthValue(frontendHealthError, text.slice(0, 220), "bad");
    }

    function clearFrontendErrorsMatching(matchText) {
      if (!matchText) return;
      frontendErrorHistory = frontendErrorHistory.filter((item) => !String(item.text || "").includes(matchText));
      if (frontendLastError.includes(matchText)) {
        frontendLastError = "";
      }
      if (!frontendLastError) {
        setHealthValue(frontendHealthError, "žádná", "ok");
      }
    }

    window.addEventListener("error", (event) => {
      recordFrontendError(event.error || event.message || "frontend error");
      setHealthValue(frontendHealthJs, "chyba ve frontendu", "bad");
    });
    window.addEventListener("unhandledrejection", (event) => {
      recordFrontendError(event.reason || "unhandled promise rejection");
      setHealthValue(frontendHealthJs, "chyba ve frontendu", "bad");
    });

    let lastSelectedSpeechText = "";
    function captureSelectedSpeechText() {
      const selected = (window.getSelection ? window.getSelection().toString() : "").trim();
      if (selected) {
        lastSelectedSpeechText = selected;
      }
      return selected;
    }
    document.addEventListener("selectionchange", captureSelectedSpeechText);
    document.addEventListener("mouseup", captureSelectedSpeechText);
    document.addEventListener("keyup", captureSelectedSpeechText);

    function verifyButtonHealth() {
      const requiredIds = [
        "refreshBtn",
        "serviceBtn",
        "servicePanel",
        "janickaBtn",
        "janickaCloseBtn",
        "janickaFindDocumentBtn",
        "janickaPrintDocumentBtn",
        "janickaEmailBtn",
        "janickaLekarnaBtn",
        "janickaFamilyBtn",
        "janickaAskAdamBtn",
        "janickaRemindersBtn",
        "janickaRecoveryBtn",
        "janickaWebAppsBtn",
        "janickaProjectsBtn",
        "janickaCookbookBtn",
        "janickaReturnBtn",
        "janickaChatCloseBtn",
        "janickaChatInput",
        "janickaChatSendBtn",
        "janickaChatClearBtn",
        "janickaAdamStartBtn",
        "janickaAdamRestartBtn",
        "janickaAdamStopBtn",
        "webAppsBtn",
        "libraryBtn",
        "libraryCloseBtn",
        "libraryArchiveUrlInput",
        "libraryArchiveCategory",
        "libraryArchiveTagsInput",
        "libraryArchiveBtn",
        "libraryTextTitleInput",
        "libraryTextCategory",
        "libraryTextSourceInput",
        "libraryTextSaveBtn",
        "libraryTextTagsInput",
        "libraryTextBodyInput",
        "libraryAttachmentFileInput",
        "libraryAttachmentLabelInput",
        "libraryAttachmentTagsInput",
        "libraryAttachmentNoteInput",
        "libraryAttachmentSaveBtn",
        "libraryAttachmentStatus",
        "librarySearchInput",
        "librarySearchBtn",
        "libraryReaderAttachments",
        "projectsBtn",
        "remindersBtn",
        "emailProcessingBtn",
        "scanDocuBtn",
        "scanDocuReviewBtn",
        "dashboardProcessBtn",
        "dashboardDocuments",
        "dashboardReviewBtn",
        "dashboardTerminalBtn",
        "dashboardQuantitativeBtn",
	        "dashboardQuickNotesBtn",
        "dashboardUrgentRemindersBtn",
	        "dashboardRecoveryBtn",
	        "dashboardRestartBtn",
	        "dashboardSpeakBtn",
        "dashboardSpeakSelectionBtn",
        "dashboardRefreshBtn",
        "voiceCommandDetails",
        "voiceModeToggleBtn",
        "voiceModeStartBtn",
        "voiceModeStopBtn",
        "voiceModeRuntimeStatus",
        "voiceBridgeStatus",
        "voiceBridgeSessions",
        "voicePendingStatus",
        "voiceLastResponseCard",
        "voiceLastResponseText",
        "voiceLastResponseSpeakBtn",
        "voiceApprovalCard",
        "voiceApprovalReason",
        "voiceApprovalText",
        "voiceApprovalApproveBtn",
        "voiceApprovalRejectBtn",
        "voiceRecordBtn",
        "voiceStopBtn",
        "voiceTranscriptSendBtn",
        "urgentReminderAlertBtn",
        "reviewReportBtn",
        "documentSearchBtn",
        "processNextBtn",
        "reviewNextBtn"
      ];
      const missing = requiredIds.filter((id) => !document.getElementById(id));
      if (missing.length) {
        setHealthValue(frontendHealthButtons, `chybí ${missing.length}: ${missing.slice(0, 3).join(", ")}`, "bad");
        recordFrontendError(`Chybí UI tlačítka: ${missing.join(", ")}`);
        return false;
      }
      setHealthValue(frontendHealthButtons, "napojeno", "ok");
      return true;
    }

    async function checkEndpointHealth(url, timeoutMs = 6000) {
      const controller = new AbortController();
      const timer = window.setTimeout(() => controller.abort(), timeoutMs);
      try {
        const startedAt = performance.now();
        const res = await fetch(url, {cache: "no-store", signal: controller.signal});
        const elapsed = Math.round(performance.now() - startedAt);
        return {url, ok: res.ok, status: res.status, elapsed};
      } catch (err) {
        const isAbort = err && err.name === "AbortError";
        return {url, ok: false, status: 0, elapsed: timeoutMs, error: isAbort ? `timeout po ${timeoutMs} ms` : String(err)};
      } finally {
        window.clearTimeout(timer);
      }
    }

    async function runFrontendHealthCheck() {
      setHealthValue(frontendHealthJs, "běží", "ok");
      verifyButtonHealth();
      setHealthValue(frontendHealthApi, "kontroluji...", "warn");
      const results = await Promise.all([
        checkEndpointHealth("/api/status"),
        checkEndpointHealth("/api/recovery/status")
      ]);
      const failed = results.filter((item) => !item.ok);
      if (failed.length) {
        setHealthValue(frontendHealthApi, `chyba ${failed.map((item) => item.url).join(", ")}`, "bad");
        recordFrontendError(`API health selhal: ${failed.map((item) => `${item.url} ${item.status || item.error || ""}`).join("; ")}`);
      } else {
        const slowest = Math.max(...results.map((item) => item.elapsed || 0));
        setHealthValue(frontendHealthApi, `OK, max ${slowest} ms`, "ok");
        if (frontendLastError.startsWith("API health selhal:")) {
          frontendLastError = "";
          setHealthValue(frontendHealthError, "žádná", "ok");
        } else if (!frontendLastError) {
          setHealthValue(frontendHealthError, "žádná", "ok");
        }
      }
    }

    async function openDiagnosticsModal() {
      diagnosticsModal.classList.remove("hidden");
      diagnosticsStatus.textContent = "Měřím endpointy...";
      diagnosticsFrontend.textContent = "";
      renderDiagnosticsStatusSignals();
      diagnosticsEndpointList.innerHTML = "";
      diagnosticsErrorList.innerHTML = "";
      const buttonsOk = verifyButtonHealth();
      diagnosticsFrontend.textContent = [
        `Frontend JS: běží`,
        `Tlačítka: ${buttonsOk ? "napojeno" : "problém"}`,
        `Poslední chyba: ${frontendLastError || "žádná"}`
      ].join(" | ");
      try {
        const results = await Promise.all(
          diagnosticsEndpoints.map(([label, url]) =>
            checkEndpointHealth(url, 8000).then((result) => ({...result, label}))
          )
        );
        renderDiagnosticsEndpointRows(results);
        renderDiagnosticsErrors();
        const failed = results.filter((item) => !item.ok);
        diagnosticsStatus.textContent = failed.length
          ? `Diagnostika doběhla: ${failed.length} endpointů má problém.`
          : "Diagnostika doběhla: endpointy odpovídají.";
      } catch (err) {
        recordFrontendError(err);
        diagnosticsStatus.textContent = `Chyba diagnostiky: ${err}`;
      }
    }

    function closeDiagnosticsModal() {
      diagnosticsModal.classList.add("hidden");
    }

    function renderDiagnosticsStatusSignals() {
      if (!diagnosticsStatusSignals) return;
      diagnosticsStatusSignals.innerHTML = "";
      const signals = Object.values(dashboardStatusSignals || {}).filter(Boolean);
      if (!signals.length) {
        const empty = document.createElement("div");
        empty.className = "diagnostics-row";
        empty.textContent = "Stavové signály zatím nejsou načtené.";
        diagnosticsStatusSignals.appendChild(empty);
        return;
      }
      signals.slice().sort((a, b) => {
        const rankDiff = dashboardStatusRank(b.level) - dashboardStatusRank(a.level);
        if (rankDiff) return rankDiff;
        return dashboardStatusPriority(b.key) - dashboardStatusPriority(a.key);
      }).forEach((signal) => {
        const row = document.createElement("div");
        row.className = `diagnostics-row ${signal.level || "ok"}`;
        const title = document.createElement("div");
        title.className = "diagnostics-row-title";
        title.textContent = `${dashboardSignalLabel(signal.key)}: ${dashboardSignalMeaning(signal.level)}`;
        const detail = document.createElement("div");
        detail.className = "project-meta";
        detail.textContent = signal.reason || "";
        const action = document.createElement("div");
        action.className = "project-meta";
        action.textContent = `Co teď: ${dashboardSignalNextAction(signal)}`;
        row.appendChild(title);
        row.appendChild(detail);
        row.appendChild(action);
        diagnosticsStatusSignals.appendChild(row);
      });
    }

    function dashboardSignalMeaning(level) {
      return {
        bad: "chyba nebo nutná akce",
        warn: "varování / ruční kontrola",
        loading: "samostatné načítání",
        ok: "v pořádku"
      }[level] || "stav neznámý";
    }

    function dashboardSignalNextAction(signal) {
      const level = signal && signal.level || "ok";
      const reason = String(signal && signal.reason || "").toLocaleLowerCase("cs-CZ");
      if (level === "loading") return "počkat na samostatné načtení nebo stisknout Obnovit stav";
      if (level === "bad") return "otevřít diagnostiku endpointů nebo příslušné okno a řešit chybu";
      if (level === "warn") {
        if (reason.includes("připomen")) return "otevřít příslušný přehled a rozhodnout, jestli je akce potřeba";
        if (reason.includes("git")) return "zkontrolovat pracovní strom a případně udělat tematický commit";
        if (reason.includes("záloh")) return "zkontrolovat stav zálohy";
        if (reason.includes("audit")) return "otevřít auditní detail";
        if (reason.includes("dokument")) return "otevřít dokumentovou frontu nebo ScanDocu";
        if (reason.includes("hlas")) return "spustit Adam Voice Mode watcher v terminálu, nebo hlasový mód vypnout";
        return "otevřít detail dané oblasti a rozhodnout další krok";
      }
      return "nic akutního";
    }

    function dashboardSignalLabel(key) {
      return {
        main: "Hlavní status",
        consistency: "Audit",
        documents: "Dokumenty",
        reminders: "Připomenutí",
        backup: "Záloha",
        git: "Git",
        voice: "Hlas",
        projects: "Projekty",
        quickNotes: "QN",
        quantitative: "Systém",
        scandocu: "ScanDocu"
      }[key] || key || "Signál";
    }

    function renderDiagnosticsEndpointRows(results) {
      diagnosticsEndpointList.innerHTML = "";
      results.forEach((item) => {
        const row = document.createElement("div");
        row.className = "diagnostics-row";
        const text = document.createElement("div");
        const title = document.createElement("div");
        title.className = "diagnostics-row-title";
        title.textContent = item.label || item.url || "";
        const meta = document.createElement("div");
        meta.className = "diagnostics-row-meta";
        meta.textContent = `${item.url || ""} | status ${item.status || 0} | ${item.elapsed || 0} ms${item.error ? " | " + item.error : ""}`;
        const badge = document.createElement("div");
        badge.className = `diagnostics-badge ${item.ok ? "ok" : "bad"}`;
        badge.textContent = item.ok ? "OK" : "chyba";
        text.appendChild(title);
        text.appendChild(meta);
        row.appendChild(text);
        row.appendChild(badge);
        diagnosticsEndpointList.appendChild(row);
      });
    }

    function renderDiagnosticsErrors() {
      diagnosticsErrorList.innerHTML = "";
      if (!frontendErrorHistory.length) {
        const empty = document.createElement("div");
        empty.className = "status-line";
        empty.textContent = "Žádné frontend/API chyby nejsou zachycené.";
        diagnosticsErrorList.appendChild(empty);
        return;
      }
      frontendErrorHistory.forEach((item) => {
        const row = document.createElement("div");
        row.className = "diagnostics-row";
        const text = document.createElement("div");
        const title = document.createElement("div");
        title.className = "diagnostics-row-title";
        title.textContent = item.text || "";
        const meta = document.createElement("div");
        meta.className = "diagnostics-row-meta";
        meta.textContent = item.createdAt || "";
        text.appendChild(title);
        text.appendChild(meta);
        row.appendChild(text);
        diagnosticsErrorList.appendChild(row);
      });
    }

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

    const INTAKE_LOCAL_MONITOR_MS = 10 * 60 * 1000;
    const INTAKE_EMAIL_MONITOR_MS = 30 * 60 * 1000;
    const URGENT_REMINDERS_MONITOR_MS = 30 * 1000;
    let refreshInFlight = false;
    let urgentRemindersRefreshInFlight = false;
    let lastMainRefreshStartedAt = 0;
    let latestDocumentIntakeData = null;
    let lastEmailIntakeMonitor = {
      generated_at: "",
      count: 0,
      raw_count: 0,
      filtered_out_count: 0,
      items: [],
      message: "E-mailové hlavičky zatím nebyly automaticky zkontrolované.",
      unavailable: []
    };

    async function refresh(options = {}) {
      if (refreshInFlight) return;
      refreshInFlight = true;
      lastMainRefreshStartedAt = Date.now();
      const silent = options.silent === true;
      const includeSecondary = options.includeSecondary !== false;
      refreshBtn.disabled = true;
      if (!silent) {
        statusLine.textContent = "Načítám stav...";
      }
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
        renderUrgentReminderAlert(data.urgent_reminders || {});
	        renderActionQueue(data.action_queue || {});
        renderDocumentWork(data.document_work || {});
        latestDocumentIntakeData = data.document_intake || {};
        renderDocumentIntake(latestDocumentIntakeData);
        renderDocumentCases(data.document_cases || {});
        renderDocumentClassification(data.document_classification || {});
        renderDocumentDueCandidates(data.document_due_candidates || {});
        renderDownloads(data.downloads || {});
        if (includeSecondary) {
          refreshSecondaryStatus();
        }
      } catch (err) {
        recordFrontendError(err);
        statusLine.textContent = `Chyba načtení: ${err}`;
        setDashboardStatusSignal("main", "bad", `Hlavní status: ${err}`);
      } finally {
        refreshBtn.disabled = false;
        refreshInFlight = false;
      }
    }

    function refreshMainStatusOnReturn(minAgeMs = 5000) {
      if (document.hidden) return;
      const now = Date.now();
      if (now - lastMainRefreshStartedAt < minAgeMs) return;
      refresh({silent: true, includeSecondary: false});
    }

    function refreshSecondaryStatus() {
      refreshProjectsSummary();
      refreshQuantitativeSummary();
      refreshConsistencySummary();
      refreshQuickNotesSummary();
      refreshUrgentRemindersSummary();
    }

    async function refreshUrgentRemindersSummary() {
      if (urgentRemindersRefreshInFlight) return;
      urgentRemindersRefreshInFlight = true;
      try {
        const data = await fetchJson("/api/urgent-reminders/status");
        renderUrgentReminderAlert(data || {});
        if (!urgentRemindersModal.classList.contains("hidden")) {
          renderUrgentReminders(data || {});
        }
      } catch (err) {
        recordFrontendError(err);
      } finally {
        urgentRemindersRefreshInFlight = false;
      }
    }

    async function runEmailIntakeMonitor() {
      try {
        const payload = lastEmailIntakeMonitor.generated_at
          ? {limit_per_source: 10, since: lastEmailIntakeMonitor.generated_at, known_ids: emailIntakeKnownIds()}
          : {limit_per_source: 10, days: 1, known_ids: emailIntakeKnownIds()};
        const res = await fetch("/api/documents/intake-email-scan", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        const suppressed = new Set(data.suppressed_known_ids || []);
        const keptItems = (lastEmailIntakeMonitor.items || []).filter((item) => {
          const id = item.id || "";
          const legacyId = item.legacy_id || "";
          const sourceKey = emailIntakeSourceKey(item);
          return !suppressed.has(id) && !suppressed.has(legacyId) && !suppressed.has(sourceKey);
        });
        const mergedItems = mergeEmailIntakeItems(keptItems, data.items || []);
        lastEmailIntakeMonitor = {
          generated_at: data.generated_at || new Date().toISOString(),
          count: mergedItems.length,
          raw_count: Number(data.raw_count || 0),
          filtered_out_count: Number(data.filtered_out_count || 0),
          items: mergedItems,
          message: data.message || "E-mailové hlavičky zkontrolované read-only.",
          unavailable: data.unavailable || []
        };
        renderDocumentIntake(latestDocumentIntakeData || {});
      } catch (err) {
        recordFrontendError(err);
        lastEmailIntakeMonitor = {
          ...lastEmailIntakeMonitor,
          message: `Chyba e-mail intake monitoru: ${err}`,
          unavailable: []
        };
        renderDocumentIntake(latestDocumentIntakeData || {});
      }
    }

    function emailIntakeKnownIds() {
      const ids = [];
      (lastEmailIntakeMonitor.items || []).forEach((item) => {
        if (item && item.id) ids.push(item.id);
        if (item && item.legacy_id) ids.push(item.legacy_id);
        const sourceKey = emailIntakeSourceKey(item);
        if (sourceKey) ids.push(sourceKey);
      });
      return ids;
    }

    function emailIntakeSourceKey(item) {
      if (!item) return "";
      if (item.source_key) return String(item.source_key);
      const provider = String(item.provider || "").trim().toLowerCase().replace(/\s+/g, " ");
      const folder = String(item.folder || "INBOX").trim().toLowerCase().replace(/\s+/g, " ");
      const uid = String(item.uid || "").trim();
      if (!provider || !uid) return "";
      return `${provider}|${folder || "inbox"}|${uid}`;
    }

    function emailIntakeDateValue(item) {
      const parsed = Date.parse(item.date || "");
      return Number.isFinite(parsed) ? parsed : 0;
    }

    function mergeEmailIntakeItems(existing, incoming) {
      const byId = new Map();
      (existing || []).forEach((item) => {
        if (!item || !item.id) return;
        byId.set(item.id, item);
        if (item.legacy_id) byId.set(item.legacy_id, item);
      });
      (incoming || []).forEach((item) => {
        if (!item || !item.id || byId.has(item.id)) return;
        if (item.legacy_id && byId.has(item.legacy_id)) return;
        byId.set(item.id, item);
        if (item.legacy_id) byId.set(item.legacy_id, item);
      });
      return Array.from(new Set(byId.values())).sort((a, b) => emailIntakeDateValue(b) - emailIntakeDateValue(a));
    }

    async function hideEmailIntakeCandidate(item, button) {
      const itemId = item.id || "";
      if (!itemId) return;
      if (button) button.disabled = true;
      try {
        const res = await fetch("/api/email-processing/decision", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({item_id: itemId, action: "ignore", item})
        });
        const data = await res.json();
        if (!data.ok) throw new Error(data.message || "Nepodařilo se uložit ignorování.");
        lastEmailIntakeMonitor.items = (lastEmailIntakeMonitor.items || []).filter((candidate) => candidate.id !== itemId);
        lastEmailIntakeMonitor.count = lastEmailIntakeMonitor.items.length;
        lastEmailIntakeMonitor.message = "E-mail skrytý z Cockpitu. V dalších scanech se nebude zobrazovat.";
        renderDocumentIntake(latestDocumentIntakeData || {});
      } catch (err) {
        recordFrontendError(err);
        if (button) button.disabled = false;
        showMessage(`Chyba při skrývání e-mailu: ${err}`);
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

    function renderDocumentIntake(data) {
      const sources = data.sources || [];
      const unifiedItems = data.unified_items || [];
      const sourceCount = (sourceId) => {
        const source = sources.find((item) => item.id === sourceId) || {};
        return Number(source.count || 0);
      };
      const downloadsCount = sourceCount("downloads");
      const queuedEmailCount = sourceCount("email");
      const mobileCount = sourceCount("mobile");
      const localInboxCount = sourceCount("local_inbox");
      const emailCandidateCount = Number(lastEmailIntakeMonitor.count || 0);
      const filteredEmailCount = Number(lastEmailIntakeMonitor.filtered_out_count || 0);
      documentIntakeCount.textContent = String(Number(data.count || 0) + emailCandidateCount);
      if (documentIntakeSummary) {
        documentIntakeSummary.textContent = `Downloads: ${downloadsCount} | E-mail kandidáti: ${emailCandidateCount} | E-mail work queue: ${queuedEmailCount} | Mobilní: ${mobileCount} | Lokální: ${localInboxCount} | Potlačeno e-mail filtrem: ${filteredEmailCount}`;
      }
      documentIntakeList.innerHTML = "";
      if (!sources.length && !unifiedItems.length) {
        const empty = document.createElement("div");
        empty.className = "status-line";
        empty.textContent = data.message || "Vstupy dokumentů nejdou načíst.";
        documentIntakeList.appendChild(empty);
        return;
      }
      const monitor = document.createElement("div");
      monitor.className = "work-meta";
      monitor.textContent = "Monitor: lokální zdroje každých 10 min; e-mailové hlavičky read-only každých 30 min.";
      documentIntakeList.appendChild(monitor);
      if (unifiedItems.length) {
        unifiedItems.forEach((item) => {
          const row = document.createElement("div");
          row.className = "work-item";
          const title = document.createElement("div");
          title.textContent = `${item.source_label || "Zdroj"}: ${item.title || "Dokumentový vstup"}`;
          const meta = document.createElement("div");
          meta.className = "work-meta";
          meta.textContent = `${item.source_status_label || item.source_status || ""}${item.meta ? " | " + item.meta : ""}`;
          const action = document.createElement("div");
          action.className = "work-meta";
          action.textContent = item.next_action || "";
          row.appendChild(title);
          row.appendChild(meta);
          row.appendChild(action);
          if (item.action_kind === "open_scandocu") {
            const button = document.createElement("button");
            button.className = "secondary";
            button.type = "button";
            button.textContent = item.action_label || "ScanDocu";
            button.addEventListener("click", () => openScanDocu(false));
            row.appendChild(button);
          } else if (item.action_kind === "open_email_processing") {
            const button = document.createElement("button");
            button.className = "secondary";
            button.type = "button";
            button.textContent = item.action_label || "E-maily";
            button.addEventListener("click", openEmailProcessing);
            row.appendChild(button);
          }
          documentIntakeList.appendChild(row);
        });
      } else {
        const empty = document.createElement("div");
        empty.className = "status-line";
        empty.textContent = data.message || "Žádný nový dokumentový vstup nečeká.";
        documentIntakeList.appendChild(empty);
      }
      if (lastEmailIntakeMonitor.count > 0) {
        lastEmailIntakeMonitor.items.slice(0, 5).forEach((item) => {
          const row = document.createElement("div");
          row.className = "work-item";
          const title = document.createElement("div");
          title.textContent = `E-mail kandidát: ${item.subject || "E-mail bez předmětu"}`;
          const meta = document.createElement("div");
          meta.className = "work-meta";
          meta.textContent = `${item.provider || "e-mail"} / ${item.folder || "INBOX"} | ${item.date || ""} | ${item.sender || ""}`;
          const action = document.createElement("div");
          action.className = "work-meta";
          const filterReasons = (item.filter_reasons || []).join("; ");
          const attachmentMeta = item.pdf_attachment_count
            ? ` PDF: ${item.pdf_attachment_count}${item.large_pdf_attachment_count ? ", velké PDF: " + item.large_pdf_attachment_count : ""}.`
            : (item.attachment_count ? ` Přílohy: ${item.attachment_count}.` : "");
          action.textContent = `${item.filter_label || "Dokumentový kandidát"}${filterReasons ? " | " + filterReasons : ""}.${attachmentMeta} Read-only: tělo e-mailu není načtené, přílohy nejsou stažené.`;
          const button = document.createElement("button");
          button.className = "secondary";
          button.type = "button";
          button.textContent = "E-maily";
          button.addEventListener("click", openEmailProcessing);
          const hideButton = document.createElement("button");
          hideButton.className = "secondary";
          hideButton.type = "button";
          hideButton.textContent = "Neukazovat";
          hideButton.addEventListener("click", () => hideEmailIntakeCandidate(item, hideButton));
          row.appendChild(title);
          row.appendChild(meta);
          row.appendChild(action);
          row.appendChild(button);
          row.appendChild(hideButton);
          documentIntakeList.appendChild(row);
        });
      }
      const emailMonitor = document.createElement("div");
      emailMonitor.className = "work-meta";
      const unavailable = lastEmailIntakeMonitor.unavailable.length
        ? ` Nedostupné: ${lastEmailIntakeMonitor.unavailable.join("; ")}`
        : "";
      const filteredOut = lastEmailIntakeMonitor.filtered_out_count
        ? ` Potlačeno filtrem: ${lastEmailIntakeMonitor.filtered_out_count}.`
        : "";
      emailMonitor.textContent = `E-mail monitor: ${lastEmailIntakeMonitor.message}${filteredOut}${unavailable}`;
      documentIntakeList.appendChild(emailMonitor);
      if (sources.length) {
        const summaryTitle = document.createElement("div");
        summaryTitle.className = "case-section-title";
        summaryTitle.textContent = "Souhrn zdrojů";
        documentIntakeList.appendChild(summaryTitle);
      }
      sources.forEach((source) => {
        const row = document.createElement("div");
        row.className = "work-item";
        const title = document.createElement("div");
        title.textContent = `${source.label || source.id || "Zdroj"}: ${source.count || 0}`;
        const meta = document.createElement("div");
        meta.className = "work-meta";
        meta.textContent = source.next_action || source.status || "";
        row.appendChild(title);
        row.appendChild(meta);
        (source.items || []).slice(0, 2).forEach((item) => {
          const detail = document.createElement("div");
          detail.className = "work-meta";
          detail.textContent = `${item.title || ""}${item.meta ? " | " + item.meta : ""}`;
          row.appendChild(detail);
        });
        documentIntakeList.appendChild(row);
      });
    }

    function renderDocumentCases(data) {
      const cases = data.cases || [];
      documentCasesCount.textContent = String(data.case_count || 0);
      documentCasesStatus.textContent = data.message || "Vazby dokumentů nejsou načtené.";
      documentCasesList.innerHTML = "";
      if (!cases.length) {
        const empty = document.createElement("div");
        empty.className = "status-line";
        empty.textContent = "Žádné skutečné vazby se dvěma a více dokumenty nejsou zjištěné.";
        documentCasesList.appendChild(empty);
        return;
      }
      cases.slice(0, 6).forEach((item) => {
        const row = document.createElement("div");
        row.className = "work-item";
        const title = document.createElement("div");
        title.textContent = `${item.label || "Case"}: ${item.document_count || 0}`;
        const meta = document.createElement("div");
        meta.className = "work-meta";
        meta.textContent = item.summary || item.group_type_label || "";
        row.appendChild(title);
        row.appendChild(meta);
        (item.documents || []).slice(0, 2).forEach((doc) => {
          const detail = document.createElement("div");
          detail.className = "work-meta";
          detail.textContent = `${doc.title || ""} | ${doc.domain_label || doc.domain || "oblast nezjištěna"} / ${doc.document_type_label || doc.document_type || "typ nezjištěn"}`;
          row.appendChild(detail);
        });
        const detailNode = document.createElement("div");
        detailNode.className = "case-detail hidden";
        const actions = document.createElement("div");
        actions.className = "actions";
        const detailBtn = document.createElement("button");
        detailBtn.className = "secondary";
        detailBtn.type = "button";
        detailBtn.textContent = "Detail case";
        detailBtn.addEventListener("click", () => loadDocumentCaseDetail(item.case_ref, detailNode, detailBtn));
        actions.appendChild(detailBtn);
        row.appendChild(actions);
        row.appendChild(detailNode);
        documentCasesList.appendChild(row);
      });
      if (data.truncated) {
        const note = document.createElement("div");
        note.className = "status-line";
        note.textContent = "Seznam vazeb je zkrácený.";
        documentCasesList.appendChild(note);
      }
    }

    async function loadDocumentCaseDetail(caseRef, detailNode, button) {
      if (!caseRef) return;
      if (!detailNode.classList.contains("hidden") && detailNode.dataset.loaded === "true") {
        detailNode.classList.add("hidden");
        button.textContent = "Detail case";
        return;
      }
      button.disabled = true;
      button.textContent = "Načítám...";
      documentCasesStatus.textContent = "Načítám detail case...";
      try {
        const res = await fetch(`/api/documents/case-detail?case_ref=${encodeURIComponent(caseRef)}`);
        const data = await res.json();
        renderDocumentCaseDetail(data, detailNode);
        detailNode.classList.remove("hidden");
        detailNode.dataset.loaded = "true";
        button.textContent = "Skrýt detail";
        documentCasesStatus.textContent = data.message || "Detail case načten.";
      } catch (err) {
        recordFrontendError(err);
        documentCasesStatus.textContent = `Chyba detailu case: ${err}`;
      } finally {
        button.disabled = false;
      }
    }

    function appendDocumentCaseSection(target, titleText, items, emptyText, renderItem) {
      const title = document.createElement("div");
      title.className = "case-section-title";
      title.textContent = titleText;
      target.appendChild(title);
      if (!items || !items.length) {
        const empty = document.createElement("div");
        empty.className = "work-meta";
        empty.textContent = emptyText;
        target.appendChild(empty);
        return;
      }
      items.forEach((item) => target.appendChild(renderItem(item)));
    }

    function renderDocumentCaseStatusRow(titleText, metaText, detailText) {
      const row = document.createElement("div");
      row.className = "case-status-row";
      const title = document.createElement("div");
      title.className = "search-title";
      title.textContent = titleText;
      row.appendChild(title);
      if (metaText) {
        const meta = document.createElement("div");
        meta.className = "work-meta";
        meta.textContent = metaText;
        row.appendChild(meta);
      }
      if (detailText) {
        const detail = document.createElement("div");
        detail.className = "work-meta";
        detail.textContent = detailText;
        row.appendChild(detail);
      }
      return row;
    }

    function renderDocumentCaseDetail(data, target) {
      target.innerHTML = "";
      if (!data.ok) {
        const error = document.createElement("div");
        error.className = "work-meta";
        error.textContent = data.message || "Case detail se nepodařilo načíst.";
        target.appendChild(error);
        return;
      }
      const summary = document.createElement("div");
      summary.className = "work-meta";
      summary.textContent = data.summary || "";
      target.appendChild(summary);
      if (data.case_health && data.case_health.summary) {
        const health = document.createElement("div");
        health.className = "case-status-row";
        health.textContent = data.case_health.summary;
        target.appendChild(health);
        appendDocumentCaseHealthSignals(target, data.case_health.signals || []);
      }
      appendDocumentCaseSection(
        target,
        "Připomínky",
        data.reminders || [],
        "Žádná otevřená připomínka k této case.",
        (item) => renderDocumentCaseStatusRow(
          item.title || "Připomínka",
          `${item.due_date || "bez data"} | ${item.priority || "priorita neurčena"} | ${item.related_asset || "bez vazby"}`,
          item.amount_due || item.amount_note || ""
        )
      );
      appendDocumentCaseSection(
        target,
        "Termíny case",
        data.due_candidates || [],
        "Žádný termín z dokumentů k této case.",
        (item) => renderDocumentCaseStatusRow(
          item.suggested_title || item.title || "Termín",
          `${item.date || "bez data"} | ${item.status_label || item.status || "stav neurčen"} | ${item.type_label || item.type || "typ neurčen"}`,
          item.context || ""
        )
      );
      appendDocumentCaseSection(
        target,
        "Konflikty",
        data.conflicts || [],
        "Žádný konflikt k této case.",
        (item) => renderDocumentCaseStatusRow(
          item.message || "Konflikt",
          `${item.asset || "věc neurčena"} | začátek krytí ${item.coverage_start || "neurčen"}`,
          `${(item.items || []).length} konfliktních připomínek`
        )
      );
      const documentsTitle = document.createElement("div");
      documentsTitle.className = "case-section-title";
      documentsTitle.textContent = "Dokumenty v case";
      target.appendChild(documentsTitle);
      (data.documents || []).forEach((doc) => {
        const row = document.createElement("div");
        row.className = "case-document-row";
        const text = document.createElement("div");
        const title = document.createElement("div");
        title.className = "search-title";
        title.textContent = doc.title || "Dokument";
        const meta = document.createElement("div");
        meta.className = "work-meta";
        meta.textContent = `${doc.domain_label || doc.domain || "oblast nezjištěna"} / ${doc.document_type_label || doc.document_type || "typ nezjištěn"} | ${doc.counterparty || "protistrana nezjištěna"} | ${doc.reading_status_label || ""}`;
        text.appendChild(title);
        text.appendChild(meta);
        row.appendChild(text);
        if (doc.can_open_pdf && doc.document_ref) {
          const openBtn = document.createElement("button");
          openBtn.className = "secondary";
          openBtn.type = "button";
          openBtn.textContent = "Otevřít PDF";
          openBtn.addEventListener("click", () => openCaseDocument(doc.document_ref, openBtn));
          row.appendChild(openBtn);
        }
        target.appendChild(row);
      });
      if (data.truncated) {
        const note = document.createElement("div");
        note.className = "status-line";
        note.textContent = "Detail case je zkrácený.";
        target.appendChild(note);
      }
    }

    function appendDocumentCaseHealthSignals(target, signals) {
      if (!signals.length) return;
      const title = document.createElement("div");
      title.className = "case-section-title";
      title.textContent = "Proč tento stav";
      target.appendChild(title);
      signals.forEach((signal) => {
        const row = document.createElement("div");
        row.className = "case-status-row";
        const heading = document.createElement("div");
        heading.className = `search-title ${signal.level === "bad" ? "bad" : signal.level === "warn" ? "warn" : "ok"}`;
        heading.textContent = signal.label || "Signál";
        const detail = document.createElement("div");
        detail.className = "work-meta";
        detail.textContent = signal.detail || "";
        const action = document.createElement("div");
        action.className = "work-meta";
        action.textContent = signal.next_action ? `Co teď: ${signal.next_action}` : "";
        row.appendChild(heading);
        if (detail.textContent) row.appendChild(detail);
        if (action.textContent) row.appendChild(action);
        target.appendChild(row);
      });
    }

    function openCaseDocument(documentRef, button) {
      openDocumentReaderWindow(documentRef, documentCasesStatus, button);
    }

    function renderDocumentClassification(data) {
      const items = data.items || [];
      documentClassificationCount.textContent = String(data.issue_count || 0);
      documentClassificationStatus.textContent = data.message || "Klasifikace není načtená.";
      documentClassificationList.innerHTML = "";
      if (!items.length) {
        const empty = document.createElement("div");
        empty.className = "status-line";
        empty.textContent = data.active_documents ? "Základní metadata jsou kompletní." : "Žádné dokumenty ke klasifikaci.";
        documentClassificationList.appendChild(empty);
        return;
      }
      items.slice(0, 6).forEach((item) => {
        const row = document.createElement("div");
        row.className = "work-item";
        const title = document.createElement("div");
        title.textContent = item.title || "Dokument";
        const action = document.createElement("div");
        action.className = "work-meta";
        action.textContent = item.recommended_action || "";
        const meta = document.createElement("div");
        meta.className = "work-meta";
        meta.textContent = item.classification_summary || "";
        const actions = document.createElement("div");
        actions.className = "actions";
        const editBtn = document.createElement("button");
        editBtn.className = "secondary";
        editBtn.type = "button";
        editBtn.textContent = "Doplnit metadata";
        editBtn.addEventListener("click", () => updateDocumentClassificationMetadata(item, editBtn));
        actions.appendChild(editBtn);
        row.appendChild(title);
        row.appendChild(action);
        row.appendChild(meta);
        row.appendChild(actions);
        documentClassificationList.appendChild(row);
      });
      if (data.truncated) {
        const note = document.createElement("div");
        note.className = "status-line";
        note.textContent = "Seznam klasifikace je zkrácený.";
        documentClassificationList.appendChild(note);
      }
    }

    function promptClassificationValue(label, currentValue, helpText) {
      const value = window.prompt(`${label}\\n${helpText}`, currentValue || "");
      if (value === null) return null;
      return value.trim();
    }

    async function updateDocumentClassificationMetadata(item, button) {
      const documentRef = item.document_ref || item.document_id || "";
      if (!documentRef) return;
      const domain = promptClassificationValue(
        "Oblast dokumentu",
        item.domain || "",
        "Např. insurance, car, home, tax, energy, employment, health, warranty, other."
      );
      if (domain === null) return;
      const documentType = promptClassificationValue(
        "Typ dokumentu",
        item.document_type || "",
        "Např. insurance_policy, insurance_payment_notice, employment_contract, invoice, lease, green_card, email-attachment-pdf, tax-penzijni-generali, document."
      );
      if (documentType === null) return;
      const counterparty = promptClassificationValue("Protistrana", item.counterparty || "", "Kdo dokument vystavil nebo koho se smluvně týká.");
      if (counterparty === null) return;
      const relatedAsset = promptClassificationValue("Vazba na auto/projekt/věc", item.related_asset || "", "Např. auto, Volvo V40, byt, penze, energie.");
      if (relatedAsset === null) return;
      const summary = [
        `Oblast: ${domain || "(prázdné)"}`,
        `Typ: ${documentType || "(prázdné)"}`,
        `Protistrana: ${counterparty || "(prázdné)"}`,
        `Vazba: ${relatedAsset || "(prázdné)"}`
      ].join("\\n");
      const ok = window.confirm(`Uložit metadata dokumentu?\\n\\n${item.title || "Dokument"}\\n\\n${summary}`);
      if (!ok) return;
      const originalText = button.textContent;
      button.disabled = true;
      button.textContent = "Ukládám...";
      documentClassificationStatus.textContent = "Ukládám metadata dokumentu...";
      try {
        const result = await postJson("/api/documents/classification-metadata", {
          document_id: documentRef,
          metadata: {
            domain,
            document_type: documentType,
            counterparty,
            related_asset: relatedAsset
          }
        });
        documentClassificationStatus.textContent = result.message || "Metadata uložena.";
        if (result.ok) {
          if (result.document_classification) {
            renderDocumentClassification(result.document_classification);
          }
          await refresh({silent: true});
        }
      } catch (err) {
        recordFrontendError(err);
        documentClassificationStatus.textContent = `Chyba uložení metadat: ${err}`;
      } finally {
        button.disabled = false;
        button.textContent = originalText || "Doplnit metadata";
      }
    }

    function renderDocumentDueCandidates(data) {
      const items = data.items || [];
      documentDueCount.textContent = String(data.actionable_count || 0);
      documentDueStatus.textContent = data.message || "Termíny nejsou načtené.";
      documentDueList.innerHTML = "";
      if (!items.length) {
        const empty = document.createElement("div");
        empty.className = "status-line";
        empty.textContent = "Žádné termínové kandidáty vhodné k připomínce nejsou v indexu.";
        documentDueList.appendChild(empty);
        return;
      }
      items.slice(0, 8).forEach((item) => {
        const row = document.createElement("div");
        row.className = "work-item";
        const title = document.createElement("div");
        title.textContent = `${item.date || "bez data"} | ${item.type_label || item.type || "termín"} | ${item.status_label || ""}`;
        const meta = document.createElement("div");
        meta.className = "work-meta";
        const amount = item.amount_due ? ` | částka ${item.amount_due}` : "";
        const sourceLabel = item.source_kind === "email_archive" ? "E-mail" : "Dokument";
        const sourceSummary = item.source_summary ? ` | ${item.source_summary}` : "";
        meta.textContent = `${sourceLabel}: ${item.title || "bez názvu"}${amount}${sourceSummary}`;
        const context = document.createElement("div");
        context.className = "work-meta";
        context.textContent = item.context || "";
        row.appendChild(title);
        row.appendChild(meta);
        row.appendChild(context);
        if (item.status === "ready") {
          const actions = document.createElement("div");
          actions.className = "actions";
          const btn = document.createElement("button");
          btn.className = "secondary";
          btn.type = "button";
          btn.textContent = "Vytvořit připomínku";
          btn.addEventListener("click", () => createDocumentDueReminder(item, btn));
          actions.appendChild(btn);
          row.appendChild(actions);
        }
        documentDueList.appendChild(row);
      });
      if (data.truncated) {
        const note = document.createElement("div");
        note.className = "status-line";
        note.textContent = "Seznam termínů je zkrácený.";
        documentDueList.appendChild(note);
      }
    }

    async function createDocumentDueReminder(item, button) {
      const candidateRef = item.candidate_ref || "";
      if (!candidateRef) return;
      const defaultTitle = item.suggested_title || `Zkontrolovat termín ${item.date || ""}`;
      const title = window.prompt("Název připomínky", defaultTitle);
      if (title === null) return;
      const defaultNotes = item.suggested_notes || item.context || "";
      const notes = window.prompt("Poznámka k připomínce", defaultNotes);
      if (notes === null) return;
      const summary = [
        `Datum: ${item.date || ""}`,
        `Typ: ${item.type_label || item.type || ""}`,
        `${item.source_kind === "email_archive" ? "E-mail" : "Dokument"}: ${item.title || ""}`,
        `Název: ${title.trim() || defaultTitle}`
      ].join("\\n");
      const ok = window.confirm(`Vytvořit připomínku z ${item.source_kind === "email_archive" ? "uloženého e-mailu" : "dokumentu"}?\\n\\n${summary}`);
      if (!ok) return;
      const originalText = button.textContent;
      button.disabled = true;
      button.textContent = "Ukládám...";
      documentDueStatus.textContent = "Ukládám připomínku...";
      try {
        const result = await postJson("/api/documents/due-reminder", {
          candidate_ref: candidateRef,
          title: title.trim(),
          notes: notes.trim(),
          priority: item.priority || "high",
          confirmed: true
        });
        documentDueStatus.textContent = result.message || "Hotovo.";
        if (result.document_due_candidates) {
          renderDocumentDueCandidates(result.document_due_candidates);
        }
        if (result.ok) {
          await refresh({silent: true});
        }
      } catch (err) {
        recordFrontendError(err);
        documentDueStatus.textContent = `Chyba vytvoření připomínky: ${err}`;
      } finally {
        button.disabled = false;
        button.textContent = originalText || "Vytvořit připomínku";
      }
    }

    async function loadDocumentReviewReport() {
      reviewReportBtn.disabled = true;
      reviewReportStatus.textContent = "Načítám report dokumentů k revizi...";
      reviewReportList.innerHTML = "";
      try {
        const res = await fetch("/api/documents/review-report");
        const data = await res.json();
        renderDocumentReviewReport(data);
      } catch (err) {
        recordFrontendError(err);
        reviewReportStatus.textContent = `Chyba reportu: ${err}`;
      } finally {
        reviewReportBtn.disabled = false;
      }
    }

    function renderDocumentReviewReport(data) {
      const summary = data.summary || {};
      const groups = data.groups || [];
      reviewReportCount.textContent = String(summary.candidate_count || 0);
      reviewReportStatus.textContent = data.message || "Report načten.";
      reviewReportList.innerHTML = "";
      if (!groups.length) {
        const empty = document.createElement("div");
        empty.className = "work-item empty";
        empty.textContent = "Žádný dokument nevyžaduje revizi podle aktuálních pravidel.";
        reviewReportList.appendChild(empty);
        return;
      }
      groups.forEach((group) => {
        const groupNode = document.createElement("div");
        groupNode.className = "review-group";
        const head = document.createElement("div");
        head.className = "review-group-head";
        const title = document.createElement("div");
        title.className = "review-group-title";
        title.textContent = group.label || group.id || "Skupina";
        const count = document.createElement("div");
        count.className = "review-group-count";
        count.textContent = `${group.count || 0} položek`;
        head.appendChild(title);
        head.appendChild(count);
        groupNode.appendChild(head);
        const action = document.createElement("div");
        action.className = "review-action";
        action.textContent = group.recommended_action || "";
        groupNode.appendChild(action);
        const items = group.items || [];
        if (!items.length) {
          const empty = document.createElement("div");
          empty.className = "work-meta";
          empty.textContent = group.empty_label || "Bez položek.";
          groupNode.appendChild(empty);
          reviewReportList.appendChild(groupNode);
          return;
        }
        items.forEach((item) => {
          groupNode.appendChild(renderDocumentReviewReportItem(item));
        });
        if (group.truncated) {
          const note = document.createElement("div");
          note.className = "work-meta";
          note.textContent = "Skupina je zkrácená; další položky existují v indexu.";
          groupNode.appendChild(note);
        }
        reviewReportList.appendChild(groupNode);
      });
      if (data.truncated) {
        const note = document.createElement("div");
        note.className = "status-line";
        note.textContent = "Celkový report je zkrácený; další položky existují v indexu.";
        reviewReportList.appendChild(note);
      }
    }

    function renderDocumentReviewReportItem(item) {
        const row = document.createElement("div");
        row.className = "work-item";
        const title = document.createElement("div");
        title.className = "work-title";
        title.textContent = item.title || item.document_id || "Dokument bez názvu";
        const recommendation = document.createElement("div");
        recommendation.className = "work-meta";
        recommendation.textContent = item.recommended_action || item.review_summary || "Zkontrolovat dokument.";
        const meta = document.createElement("div");
        meta.className = "work-meta";
        meta.textContent = `${item.classification_summary || ""} | ${item.reading_summary || ""}`;
        const reasons = document.createElement("div");
        reasons.className = "work-meta";
        reasons.textContent = (item.reasons || []).map((reason) => reason.label || reason.id || "").filter(Boolean).join(", ");
        row.appendChild(title);
        row.appendChild(recommendation);
        row.appendChild(meta);
        if (reasons.textContent) row.appendChild(reasons);
        return row;
    }

	    function renderDashboard(data) {
      setDashboardStatusSignal("main", "ok", "Hlavní status načten");
      const work = data.document_work || {};
      const summary = work.summary || {};
      const review = work.review || {};
      const newCount = summary.new_pdf_count || 0;
      const reviewPending = summary.review_pending_count || review.pending_count || 0;
      const problemTotal = summary.problem_count || 0;
      todayNewPdfCount.textContent = String(newCount);
      todayReviewCount.textContent = String(reviewPending);
      todayProblemCount.textContent = String(problemTotal);
      const documentsPanelNode = document.getElementById("documentsPanel");
      if (documentsPanelNode && (newCount > 0 || reviewPending > 0 || problemTotal > 0)) {
        documentsPanelNode.open = true;
      }
      todayHint.textContent = dashboardTodayHint(newCount, reviewPending, problemTotal);
      const documentSignal = problemTotal > 0
        ? {level: "warn", reason: `Dokumenty: ${problemTotal} problémů k ruční kontrole`}
        : newCount > 0
          ? {level: "warn", reason: `Dokumenty: ${newCount} nových PDF čeká na zpracování`}
          : reviewPending > 0
            ? {level: "warn", reason: `Dokumenty: ${reviewPending} uložených dokumentů čeká na revizi`}
            : {level: "ok", reason: "Dokumentová fronta je klidná"};
      if (dashboardDocuments) {
        const documentClass = documentSignal.level === "ok" ? "ok" : "warn";
        setDashboardValue(dashboardDocuments, `<span class="${documentClass}">${documentSignal.reason}</span>`);
      }
      setDashboardStatusSignal("documents", documentSignal.level, documentSignal.reason);
      dashboardActionHint.textContent = newCount > 0
        ? "Nejbližší akce: zpracovat další PDF přes ScanDocu."
        : reviewPending > 0
          ? "Nejbližší akce: revidovat uložený dokument."
          : "Fronta nevypadá akutně.";

      const scandocu = data.scandocu || {};
      dashboardScanDocu.innerHTML = scandocu.running
        ? `<span class="ok">běží</span> | ${scandocu.url || ""}`
        : `<span class="warn">neběží</span> | ${scandocu.url || ""}`;
      setDashboardStatusSignal(
        "scandocu",
        "ok",
        scandocu.running ? "ScanDocu běží" : "ScanDocu neběží; spustí se až při práci s PDF"
      );

      const reminders = data.reminders || {};
      const reminderCounts = reminders.counts || {};
      const activeReminders = reminderCounts.active || 0;
      const openReminders = reminderCounts.open || 0;
      const conflictReminders = reminderCounts.conflicts || 0;
      const reminderClass = conflictReminders > 0 ? "bad" : activeReminders > 0 ? "warn" : openReminders > 0 ? "ok" : "ok";
      const conflictText = conflictReminders > 0 ? ` | <span class="bad">${conflictReminders} konflikt</span>` : "";
      dashboardReminders.innerHTML = `<span class="${reminderClass}">${activeReminders} aktivní</span> | ${openReminders} otevřené${conflictText}`;
      setDashboardStatusSignal(
        "reminders",
        conflictReminders > 0 ? "bad" : activeReminders > 0 ? "warn" : "ok",
        conflictReminders > 0
          ? `Připomenutí: ${conflictReminders} konflikt`
          : activeReminders > 0
            ? `Připomenutí: ${activeReminders} aktivní`
            : "Připomenutí bez akutní akce"
      );

      const voiceMode = data.voice_mode || {};
      const voiceBridge = data.voice_bridge || {};
      latestVoiceModeRuntime = voiceMode;
      const voiceRunning = Boolean(voiceMode.running);
      const voiceState = voiceMode.state || "unknown";
      const voiceMessage = voiceMode.message || "Adam Voice Mode stav není načtený.";
      const voiceBridgeWarn = voiceBridge.status === "warn" || voiceBridge.status === "missing";
      const voiceBridgeMessage = voiceBridge.message || "Terminálový bridge stav není načtený.";
      const voicePending = voiceMode.pending_for_adam || {};
      const voicePendingActive = Boolean(voicePending.pending);
      const voicePendingText = String(voicePending.text || "");
      const voicePendingShort = voicePendingText.length > 160 ? `${voicePendingText.slice(0, 160)}...` : voicePendingText;
      const voicePendingDashboard = voicePendingActive ? `<br><span class="warn">čeká pokyn</span>` : "";
      const voiceBridgeDashboard = voiceBridgeWarn ? `<br><span class="warn">${escapeHtml(voiceBridgeMessage)}</span>` : "";
      dashboardVoiceMode.innerHTML = voiceRunning
        ? `<span class="${voiceBridgeWarn ? "warn" : "ok"}">Adam poslouchá</span><br>${escapeHtml(voiceState)}${voicePendingDashboard}${voiceBridgeDashboard}`
        : `<span class="${voiceModeEnabled || voicePendingActive || voiceBridgeWarn ? "warn" : "ok"}">${voiceModeEnabled ? "Adam neposlouchá" : "vypnuto"}</span><br>${escapeHtml(voiceState)}${voicePendingDashboard}${voiceBridgeDashboard}`;
      if (voiceModeRuntimeStatus) {
        voiceModeRuntimeStatus.textContent = voiceRunning
          ? `Adam Voice Mode watcher běží: ${voiceMessage}`
          : `Adam Voice Mode watcher neběží: ${voiceMessage}`;
      }
      if (voiceBridgeStatus) {
        voiceBridgeStatus.textContent = `Terminálový bridge: ${voiceBridgeMessage}`;
        voiceBridgeStatus.classList.toggle("warn", voiceBridgeWarn);
        voiceBridgeStatus.classList.toggle("ok", !voiceBridgeWarn);
      }
      if (voiceBridgeSessions) {
        const markedTty = String(voiceBridge.marked_tty || "");
        const effectiveTty = String(voiceBridge.effective_tty || "");
        const codexTtys = Array.isArray(voiceBridge.codex_ttys)
          ? voiceBridge.codex_ttys.map((item) => String(item || "")).filter(Boolean)
          : [];
        const sessionParts = codexTtys.map((tty) => (
          tty === markedTty
            ? `${tty} -> voice marker`
            : tty === effectiveTty
              ? `${tty} -> voice bridge`
              : `${tty} -> Codex`
        ));
        if (markedTty && !codexTtys.includes(markedTty)) {
          sessionParts.unshift(`${markedTty} -> voice bridge mimo běžící Codex relace`);
        }
        voiceBridgeSessions.textContent = sessionParts.length
          ? `Codex relace: ${sessionParts.join(" | ")}`
          : "Codex relace: žádná běžící relace nebyla nalezena";
        voiceBridgeSessions.classList.toggle("warn", voiceBridgeWarn || (markedTty && !codexTtys.includes(markedTty)));
        voiceBridgeSessions.classList.toggle("ok", !voiceBridgeWarn && (!markedTty || codexTtys.includes(markedTty)));
      }
      renderVoiceBridgeSwitcher(voiceBridge);
      if (voiceCommandDetails) {
        voiceCommandDetails.open = Boolean(voiceRunning || voicePendingActive || voiceModeEnabled || voiceBridgeWarn);
      }
      if (voicePendingStatus) {
        voicePendingStatus.textContent = voicePendingActive
          ? `Čeká hlasový pokyn na Adama: ${voicePendingShort || voicePending.message || "bez textu"}`
          : voicePending.message || "Žádný hlasový pokyn nečeká na Adama.";
      }
      renderVoiceLastResponse(voiceMode.last_adam_response || {});
      renderVoiceApproval(voicePending);
      if (voiceModeStartBtn) {
        voiceModeStartBtn.disabled = voiceRunning;
        voiceModeStartBtn.textContent = voiceRunning ? "Poslech běží" : "Spustit Adamův poslech";
        voiceModeStartBtn.classList.toggle("active", voiceRunning);
      }
      if (voiceModeStopBtn) {
        voiceModeStopBtn.disabled = !voiceRunning;
        voiceModeStopBtn.textContent = voiceRunning ? "Zastavit poslech" : "Poslech neběží";
      }
      setDashboardStatusSignal(
        "voice",
        voicePendingActive || voiceBridgeWarn || (voiceModeEnabled && !voiceRunning) ? "warn" : "ok",
        voicePendingActive
          ? "Čeká hlasový pokyn na převzetí Adamem v Codexu"
          : voiceBridgeWarn
          ? voiceBridgeMessage
          : voiceModeEnabled && !voiceRunning
          ? "Hlasový mód je v UI zapnutý, ale Adam Voice Mode watcher neběží"
          : voiceRunning
            ? "Adam Voice Mode watcher běží"
            : "Hlasový mód je vypnutý"
      );
      updateVoiceModeUi();

      setDashboardPendingIfEmpty(dashboardProjects, "načítám samostatně");
      setDashboardPendingIfEmpty(dashboardQuantitative, "načítám samostatně");
      setDashboardPendingIfEmpty(dashboardConsistency, "načítám samostatně");
      setDashboardPendingIfEmpty(dashboardQuickNotes, "načítám samostatně");
      if (dashboardValueIsPending(dashboardProjects)) {
        setDashboardStatusSignal("projects", "loading", "Projekty se načítají samostatně");
      }
      if (dashboardValueIsPending(dashboardQuantitative)) {
        setDashboardStatusSignal("quantitative", "loading", "Systémový souhrn se načítá samostatně");
      }
      if (dashboardValueIsPending(dashboardConsistency)) {
        setDashboardStatusSignal("consistency", "loading", "Audit se načítá samostatně");
      }
      if (dashboardValueIsPending(dashboardQuickNotes)) {
        setDashboardStatusSignal("quickNotes", "loading", "QN se načítají samostatně");
      }

      const backupState = classifyBackup(data.backup || "", data.backup_status || null);
      setDashboardValue(dashboardBackup, `<span class="${backupState.className}">${backupState.label}</span>`);
      setDashboardStatusSignal(
        "backup",
        backupState.className === "ok" ? "ok" : "warn",
        `Záloha: ${backupState.label}`
      );

      const git = data.git || {};
      if (!git.ok) {
        dashboardGit.innerHTML = `<span class="warn">nelze zjistit</span>`;
        setDashboardStatusSignal("git", "warn", "Git: nelze zjistit stav");
      } else {
        const gitClass = git.dirty_count ? "warn" : "ok";
        const sync = git.ahead ? " | čeká push" : git.behind ? " | čeká pull" : "";
        const reviewCount = Math.max(0, Number(git.dirty_count || 0) - Number(git.safe_commit_count || 0) - Number(git.excluded_private_count || 0));
        const gitBreakdown = git.dirty_count
          ? `<br>git-safe ${git.safe_commit_count || 0} | zkontrolovat ${reviewCount} | private/family mimo ${git.excluded_private_count || 0}`
          : "";
        dashboardGit.innerHTML = `<span class="${gitClass}">${git.message || ""}</span>${sync}<br>${git.branch || ""}${gitBreakdown}`;
        setDashboardStatusSignal(
          "git",
          git.dirty_count || git.ahead || git.behind ? "warn" : "ok",
          git.dirty_count
            ? `Git: ${git.message || `${git.dirty_count} změn v pracovní kopii`} | git-safe ${git.safe_commit_count || 0}, private/family mimo ${git.excluded_private_count || 0}`
            : git.ahead
              ? "Git: lokální změny čekají na push"
              : git.behind
                ? "Git: vzdálené změny čekají na pull"
                : "Git je synchronizovaný"
        );
	      }
      renderDashboardMorningSentence(data);
	    }

    function renderDashboardMorningSentence(data) {
      if (!dashboardMorningSentence) return;
      const stable = ["Cockpit odpovídá"];
      const warnings = [];
      const backup = data.backup_status || {};
      const git = data.git || {};
      const bridge = data.voice_bridge || {};

      if (backup.status === "ok") {
        stable.push("záloha je v pořádku");
      } else {
        warnings.push("záloha");
      }
      if (git.ok && !git.dirty_count && !git.ahead && !git.behind) {
        stable.push("git je čistý");
      } else {
        warnings.push("git");
      }
      if (bridge.status && bridge.status !== "ok") {
        warnings.push("Adam bridge");
      }

      dashboardMorningSentence.textContent = warnings.length
        ? `Ranní stav: Samantha je vzhůru; ${stable.join(", ")}; zkontrolovat: ${warnings.join(", ")}.`
        : `Ranní stav: Samantha je vzhůru; ${stable.join(", ")}.`;
    }

	    function renderActionQueue(queue) {
	      const items = queue.items || [];
	      const counts = queue.counts || {};
	      actionQueueStatus.textContent = queue.message || (
	        items.length ? `${items.length} doporučených akcí.` : "Žádná urgentní akce."
	      );
	      actionQueueList.innerHTML = "";
	      if (!items.length) {
	        const empty = document.createElement("div");
	        empty.className = "status-line";
	        empty.textContent = "Nic akutního. Vhodný další krok je jen ruční kontrola projektu nebo pokračování podle plánu.";
	        actionQueueList.appendChild(empty);
	        return;
	      }
	      items.forEach((item) => {
	        const card = document.createElement("div");
	        card.className = "action-card";
	        const head = document.createElement("div");
	        head.className = "action-card-head";
	        const title = document.createElement("div");
	        title.className = "action-title";
	        title.textContent = item.title || "Doporučená akce";
	        const badge = document.createElement("span");
	        badge.className = "project-priority";
	        badge.textContent = `P${item.priority || "?"}`;
	        head.appendChild(title);
	        head.appendChild(badge);
	        const detail = document.createElement("div");
	        detail.className = "action-detail";
	        detail.textContent = item.detail || "";
	        card.appendChild(head);
	        card.appendChild(detail);
	        const button = actionQueueButton(item);
	        if (button) card.appendChild(button);
	        actionQueueList.appendChild(card);
	      });
	      if (counts.total > items.length) {
	        const more = document.createElement("div");
	        more.className = "status-line";
	        more.textContent = `Zobrazeno ${items.length} z ${counts.total} položek.`;
	        actionQueueList.appendChild(more);
	      }
	    }

	    function actionQueueButton(item) {
	      const action = item.action || "";
	      if (!action || action === "none") return null;
	      const button = document.createElement("button");
	      button.className = "secondary";
	      button.type = "button";
	      button.textContent = item.action_label || "Otevřít";
	      button.addEventListener("click", () => {
	        if (action === "open_scandocu") {
	          openScanDocu(false);
	        } else if (action === "open_scandocu_review") {
	          openScanDocu(true);
	        } else if (action === "open_reminders") {
	          openRemindersModal();
        } else if (action === "open_urgent_reminders") {
          openUrgentRemindersModal();
	        } else if (action === "open_recovery") {
	          openRecoveryModal();
	        }
	      });
	      return button;
	    }

    function renderConsistencyAudit(consistency) {
      const node = document.getElementById("consistencyText");
      if (!node) return;
      node.innerHTML = "";
      const summary = document.createElement("pre");
      summary.textContent = consistency.summary_text || "";
      node.appendChild(summary);
      const findings = Array.isArray(consistency.findings) ? consistency.findings : [];
      findings.forEach((finding) => {
        const card = document.createElement("div");
        card.className = "consistency-finding";
        const head = document.createElement("div");
        head.className = "consistency-finding-head";
        const title = document.createElement("div");
        title.className = "consistency-finding-title";
        title.textContent = finding.title || finding.message || finding.finding_id || "Auditní nález";
        const badge = document.createElement("span");
        badge.className = `project-priority ${finding.severity === "critical" ? "bad" : "warn"}`;
        badge.textContent = finding.severity || "warning";
        head.appendChild(title);
        head.appendChild(badge);
        const meta = document.createElement("div");
        meta.className = "consistency-finding-meta";
        meta.textContent = `${finding.code || ""} | ${finding.asset || ""} | ${finding.coverage_start || ""} | ${finding.finding_id || ""}`;
        const message = document.createElement("div");
        message.className = "project-next";
        message.textContent = finding.message || "";
        const actions = document.createElement("div");
        actions.className = "project-flags";
        const okBtn = document.createElement("button");
        okBtn.type = "button";
        okBtn.className = "secondary";
        okBtn.textContent = "Označit jako OK";
        okBtn.disabled = !finding.finding_id;
        okBtn.addEventListener("click", () => resolveConsistencyFinding(finding, okBtn));
        actions.appendChild(okBtn);
        card.appendChild(head);
        card.appendChild(meta);
        if (message.textContent) card.appendChild(message);
        card.appendChild(actions);
        node.appendChild(card);
      });
      const suppressedCount = Number(consistency.suppressed_finding_count || 0);
      if (suppressedCount) {
        const suppressed = document.createElement("div");
        suppressed.className = "consistency-finding-meta";
        suppressed.textContent = `${suppressedCount} nálezů je potlačeno lokálním rozhodnutím.`;
        node.appendChild(suppressed);
      }
    }

    async function resolveConsistencyFinding(finding, button) {
      const findingId = finding && finding.finding_id || "";
      if (!findingId) return;
      const defaultReason = finding.code === "multiple_payment_options_in_document"
        ? "Zkontrolováno ručně: jde o volitelnou variantu nebo vyřešenou platební cestu."
        : "Zkontrolováno ručně a nález je v pořádku.";
      const reason = window.prompt("Proč je tento auditní nález v pořádku? Uloží se jen lokálně do private dat.", defaultReason);
      if (!reason) return;
      const originalText = button.textContent;
      button.disabled = true;
      button.textContent = "Ukládám...";
      try {
        const result = await postJson("/api/consistency/resolve-finding", {
          finding_id: findingId,
          status: "resolved",
          reason
        });
        if (result.consistency) {
          renderConsistencyAudit(result.consistency);
        }
        await refreshConsistencySummary();
        showMessage(result.message || "Auditní rozhodnutí uloženo.");
      } catch (err) {
        recordFrontendError(err);
        showMessage(`Chyba uložení auditního rozhodnutí: ${err}`);
        button.disabled = false;
        button.textContent = originalText;
      }
    }

    function setDashboardPendingIfEmpty(node, text) {
      if (!node || node.textContent.trim()) return;
      node.innerHTML = `<span class="warn">${escapeDashboardHtml(text || "načítám...")}</span>`;
    }

    function dashboardValueIsPending(node) {
      const text = String(node && node.textContent || "").trim().toLocaleLowerCase("cs-CZ");
      return !text || text.includes("načítám");
    }

    function setDashboardValue(node, html, loadedAt = new Date()) {
      if (!node) return;
      node.innerHTML = `${html}<span class="dashboard-updated">načteno ${formatDashboardLoadedAt(loadedAt)}</span>`;
    }

    function formatDashboardLoadedAt(value) {
      const date = value instanceof Date ? value : new Date(value);
      if (!Number.isFinite(date.getTime())) return "čas neznámý";
      return date.toLocaleTimeString("cs-CZ", {hour: "2-digit", minute: "2-digit", second: "2-digit"});
    }

    function dashboardStatusRank(level) {
      if (level === "bad") return 4;
      if (level === "warn") return 3;
      if (level === "loading") return 2;
      if (level === "ok") return 1;
      return 0;
    }

    function dashboardStatusPriority(key) {
      const priorities = {
        main: 100,
        consistency: 90,
        documents: 80,
        reminders: 70,
        backup: 60,
        git: 50,
        voice: 45,
        projects: 40,
        quickNotes: 35,
        quantitative: 30,
        scandocu: 10
      };
      return priorities[key] || 0;
    }

    function setDashboardStatusSignal(key, level, reason) {
      if (!key) return;
      dashboardStatusSignals = {
        ...dashboardStatusSignals,
        [key]: {key, level: level || "ok", reason: reason || ""}
      };
      updateDashboardOverallStatus();
    }

    function updateDashboardOverallStatus() {
      if (!dashboardOverall || !dashboardOverallLabel || !dashboardOverallReason) return;
      const signals = Object.values(dashboardStatusSignals).filter(Boolean);
      if (!signals.length) {
        dashboardOverall.className = "dashboard-overall dashboard-overall-loading";
        dashboardOverallLabel.textContent = "Načítám";
        dashboardOverallReason.textContent = "Skládám hlavní a samostatně načítané kontroly.";
        return;
      }
      const sorted = signals.slice().sort((a, b) => {
        const rankDiff = dashboardStatusRank(b.level) - dashboardStatusRank(a.level);
        if (rankDiff) return rankDiff;
        return dashboardStatusPriority(b.key) - dashboardStatusPriority(a.key);
      });
      const worst = sorted[0] || {level: "loading"};
      const actionSignals = sorted.filter((item) => item.level === "bad" || item.level === "warn");
      const loadingSignals = sorted.filter((item) => item.level === "loading");
      let level = "ok";
      let label = "V pořádku";
      let reasons = ["Hlavní kontroly jsou bez zásahu."];
      if (worst.level === "bad") {
        level = "bad";
        label = "Akce potřeba";
        reasons = actionSignals;
      } else if (worst.level === "warn") {
        level = "warn";
        label = "Pozor";
        reasons = actionSignals;
      } else if (worst.level === "loading") {
        level = "loading";
        label = "Čekám na kontroly";
        reasons = loadingSignals;
      }
      dashboardOverall.className = `dashboard-overall dashboard-overall-${level}`;
      dashboardOverallLabel.textContent = label;
      dashboardOverallReason.textContent = Array.isArray(reasons)
        ? reasons.map((item) => item.reason || "").filter(Boolean).slice(0, 3).join(" | ")
        : String(reasons || "");
    }

    function escapeDashboardHtml(value) {
      return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }

    function consistencyDashboardSummary(consistency) {
      if (!consistency || consistency.ok === false) return "nelze zjistit";
      const findingCount = Number(consistency.finding_count || 0);
      const suppressedCount = Number(consistency.suppressed_finding_count || 0);
      const suppressedSuffix = suppressedCount ? ` | ${suppressedCount} potlačeno` : "";
      if (!findingCount) return `0 nálezů${suppressedSuffix}`;
      const severityCounts = consistency.severity_counts || {};
      const severity = severityCounts.critical ? "kritické" : severityCounts.warning ? "varování" : "info";
      const findings = Array.isArray(consistency.findings) ? consistency.findings : [];
      const first = findings[0] || {};
      const title = String(first.title || first.message || "detail je v auditním okně");
      const compactTitle = title.length > 90 ? `${title.slice(0, 87)}...` : title;
      return `${findingCount} ${severity}: ${compactTitle}${suppressedSuffix}`;
    }

    async function fetchJson(url) {
      const res = await fetch(url);
      if (!res.ok) {
        const error = new Error(`${url} returned ${res.status}`);
        recordFrontendError(error);
        throw error;
      }
      return await res.json();
    }

    async function refreshProjectsSummary() {
      setDashboardPendingIfEmpty(dashboardProjects, "načítám...");
      try {
        const res = await fetch("/api/projects/status");
        const projects = await res.json();
        const projectSummary = projects.summary || {};
        const catalogSummary = projects.catalog_summary || {};
        const priorityCounts = projectSummary.priority_counts || {};
        const flagCounts = projectSummary.flag_counts || {};
        const priorityOne = (priorityCounts["1"] || 0) + (priorityCounts["A1+"] || 0);
        const remindCount = flagCounts["připomenout"] || 0;
        const activeProjects = projectSummary.active_total || catalogSummary.projects || projectSummary.total || 0;
        setDashboardValue(
          dashboardProjects,
          projects.ok === false
            ? `<span class="warn">nelze načíst</span>`
            : `<span class="${priorityOne > 0 ? "warn" : "ok"}">${priorityOne} priorita 1</span> | ${activeProjects} aktivních projektů | ${catalogSummary.tools || 0} toolů | ${catalogSummary.infrastructure_capabilities || 0} vrstev${remindCount ? ` | ${remindCount} připomenout` : ""}`
        );
        setDashboardStatusSignal(
          "projects",
          projects.ok === false ? "warn" : remindCount > 0 ? "warn" : "ok",
          projects.ok === false
            ? "Projekty: nelze načíst"
            : remindCount > 0
              ? `Projekty: ${remindCount} připomenout`
              : "Projekty bez samostatného varování"
        );
      } catch (err) {
        recordFrontendError(err);
        setDashboardValue(dashboardProjects, `<span class="warn">chyba načtení</span>`);
        setDashboardStatusSignal("projects", "warn", `Projekty: chyba načtení (${err})`);
      }
    }

    async function refreshQuantitativeSummary() {
      setDashboardPendingIfEmpty(dashboardQuantitative, "načítám...");
      try {
        const quantitative = await fetchJson("/api/quantitative-status");
        const quantitativeCurrentSummary = quantitative.current || {};
        const quantitativeTotals = quantitativeCurrentSummary.totals || {};
        const quantitativeLocalTotals = quantitativeTotals.local || {};
        const quantitativeGitTotals = quantitativeTotals.git_tracked || {};
        setDashboardValue(
          dashboardQuantitative,
          quantitative.ok === false
            ? `<span class="warn">nelze zjistit</span>`
            : `<span class="ok">${quantitativeLocalTotals.files || 0} souborů</span> | ${quantitativeLocalTotals.lines || 0} lokálních řádků | git ${quantitativeGitTotals.lines || 0} řádků`
        );
        setDashboardStatusSignal(
          "quantitative",
          quantitative.ok === false ? "warn" : "ok",
          quantitative.ok === false ? "Systémový souhrn: nelze zjistit" : "Systémový souhrn načten"
        );
      } catch (err) {
        recordFrontendError(err);
        setDashboardValue(dashboardQuantitative, `<span class="warn">chyba načtení</span>`);
        setDashboardStatusSignal("quantitative", "warn", `Systémový souhrn: chyba načtení (${err})`);
      }
    }

    async function refreshConsistencySummary() {
      setDashboardPendingIfEmpty(dashboardConsistency, "načítám...");
      renderConsistencyAudit({summary_text: "Načítám consistency audit samostatně..."});
      try {
        const consistency = await fetchJson("/api/consistency-status");
        const severityCounts = consistency.severity_counts || {};
        const criticalFindings = severityCounts.critical || 0;
        const warningFindings = severityCounts.warning || 0;
        const findingCount = consistency.finding_count || 0;
        const auditClass = criticalFindings > 0 ? "bad" : warningFindings > 0 ? "warn" : "ok";
        setDashboardValue(
          dashboardConsistency,
          consistency.ok === false
            ? `<span class="warn">nelze zjistit</span>`
            : `<span class="${auditClass}">${escapeDashboardHtml(consistencyDashboardSummary(consistency))}</span>`
        );
        setDashboardStatusSignal(
          "consistency",
          consistency.ok === false ? "warn" : criticalFindings > 0 ? "bad" : warningFindings > 0 ? "warn" : "ok",
          consistency.ok === false ? "Audit: nelze zjistit" : `Audit: ${consistencyDashboardSummary(consistency)}`
        );
        renderConsistencyAudit(consistency || {});
        clearFrontendErrorsMatching("escapeHtml");
      } catch (err) {
        recordFrontendError(err);
        setDashboardValue(dashboardConsistency, `<span class="warn">chyba načtení</span>`);
        setDashboardStatusSignal("consistency", "warn", `Audit: chyba načtení (${err})`);
        renderConsistencyAudit({summary_text: `Chyba načtení consistency auditu: ${err}`});
      }
    }

    async function refreshQuickNotesSummary() {
      setDashboardPendingIfEmpty(dashboardQuickNotes, "načítám...");
      try {
        const quickNotes = await fetchJson("/api/quick-notes/status");
        const counts = quickNotes.counts || {};
        const active = counts.active || 0;
        const first = (quickNotes.notes || [])[0] || {};
        const firstClass = first.triage && first.triage.classification ? ` | poslední: ${escapeDashboardHtml(first.triage.classification)}` : "";
        setDashboardValue(
          dashboardQuickNotes,
          quickNotes.ok === false
            ? `<span class="warn">nelze načíst</span>`
            : `<span class="${active > 0 ? "warn" : "ok"}">${active} aktivní</span>${firstClass}`
        );
        setDashboardStatusSignal(
          "quickNotes",
          quickNotes.ok === false ? "warn" : active > 0 ? "warn" : "ok",
          quickNotes.ok === false ? "QN: nelze načíst" : active > 0 ? `QN: ${active} aktivních poznámek` : "QN inbox je prázdný"
        );
      } catch (err) {
        recordFrontendError(err);
        setDashboardValue(dashboardQuickNotes, `<span class="warn">chyba načtení</span>`);
        setDashboardStatusSignal("quickNotes", "warn", `QN: chyba načtení (${err})`);
      }
    }

    async function openQuantitativeModal() {
      quantitativeModal.classList.remove("hidden");
      quantitativeStatus.textContent = "Načítám systémový souhrn...";
      quantitativeCurrent.textContent = "";
      quantitativePrevious.textContent = "";
      quantitativeDiffTotals.innerHTML = "";
      quantitativeDiffList.innerHTML = "";
      try {
        const data = await fetchJson("/api/quantitative-status");
        currentQuantitative = data;
        renderQuantitativeStatus(data);
      } catch (err) {
        recordFrontendError(err);
        quantitativeStatus.textContent = `Chyba načtení systémového souhrnu: ${err}`;
      }
    }

    function closeQuantitativeModal() {
      quantitativeModal.classList.add("hidden");
    }

    function renderQuantitativeStatus(data) {
      const current = data.current || {};
      const previous = data.previous || null;
      const diff = data.diff || {};
      const currentLocal = (current.totals && current.totals.local) || {files: 0, lines: 0};
      const currentGit = (current.totals && current.totals.git_tracked) || {files: 0, lines: 0};
      const previousLocal = previous ? (((previous.totals || {}).local) || {files: 0, lines: 0}) : {files: 0, lines: 0};
      const previousGit = previous ? (((previous.totals || {}).git_tracked) || {files: 0, lines: 0}) : {files: 0, lines: 0};
      const diffLocal = (diff.totals && diff.totals.local) || {files: 0, lines: 0};
      const diffGit = (diff.totals && diff.totals.git_tracked) || {files: 0, lines: 0};

      quantitativeStatus.textContent = data.message || "Systémový souhrn načten.";
      quantitativeCurrent.textContent = [
        `Created: ${current.created_at || ""}`,
        `Git: ${current.git_summary || ""}`,
        `Stored: ${current.stored_path || "ne"}`,
        "",
        `Lokalni: ${currentLocal.files || 0} souborů, ${currentLocal.lines || 0} řádků`,
        `Git tracked: ${currentGit.files || 0} souborů, ${currentGit.lines || 0} řádků`,
      ].join("\\n");
      quantitativePrevious.textContent = previous ? [
        `Created: ${previous.created_at || ""}`,
        `Git: ${previous.git_summary || ""}`,
        `Lokalni: ${previousLocal.files || 0} souborů, ${previousLocal.lines || 0} řádků`,
        `Git tracked: ${previousGit.files || 0} souborů, ${previousGit.lines || 0} řádků`,
      ].join("\\n") : "Žádný předchozí snapshot nebyl nalezen.";

      quantitativeDiffTotals.innerHTML = "";
      [
        ["Lokalni soubory", diffLocal.files],
        ["Lokalni řádky", diffLocal.lines],
        ["Git tracked soubory", diffGit.files],
        ["Git tracked řádky", diffGit.lines],
      ].forEach(([label, delta]) => {
        const row = document.createElement("div");
        row.className = "quantitative-diff-meta";
        row.textContent = `${label}: ${formatDelta(Number(delta))}`;
        quantitativeDiffTotals.appendChild(row);
      });

      quantitativeDiffList.innerHTML = "";
      const sections = [
        ["Lokalní diff", diff.local || []],
        ["Git tracked diff", diff.git_tracked || []],
      ];
      sections.forEach(([label, items]) => {
        const heading = document.createElement("div");
        heading.className = "project-meta";
        heading.textContent = label;
        quantitativeDiffList.appendChild(heading);
        if (!items.length) {
          const empty = document.createElement("div");
          empty.className = "quantitative-diff-meta";
          empty.textContent = "Bez změn.";
          quantitativeDiffList.appendChild(empty);
          return;
        }
        items.forEach((item) => {
          const row = document.createElement("div");
          row.className = "quantitative-diff-item";
          const title = document.createElement("div");
          title.className = "project-title";
          title.textContent = item.extension || "";
          const meta = document.createElement("div");
          meta.className = "quantitative-diff-meta";
          meta.textContent = `Soubory ${formatDelta(Number(item.delta_files))} | Řádky ${formatDelta(Number(item.delta_lines))} | nyní ${item.files || 0} souborů / ${item.lines || 0} řádků`;
          row.appendChild(title);
          row.appendChild(meta);
          quantitativeDiffList.appendChild(row);
        });
      });
    }

    function formatDelta(value) {
      const prefix = value > 0 ? "+" : "";
      return `${prefix}${value}`;
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

    function classifyBackup(text, status) {
      if (status && typeof status === "object") {
        const raw = String(status.status || "");
        if (raw === "ok") return {label: "v pořádku", className: "ok"};
        if (raw === "missing" || raw === "stale") return {label: "potřebuje zálohu", className: "warn"};
        if (raw === "error") return {label: "chyba stavu zálohy", className: "warn"};
      }
      if (!text) return {label: "neznámý stav", className: "warn"};
      const lower = text.toLocaleLowerCase("cs-CZ");
      if (lower.includes("starsi nez 3 dny") || lower.includes("starší než 3 dny") || lower.includes("chybi") || lower.includes("chybí")) {
        return {label: "potřebuje zálohu", className: "warn"};
      }
      if (lower.includes("posledni uspesna") || lower.includes("poslední úspěšná")) {
        return {label: "záloha evidovaná", className: "ok"};
      }
      if (
        lower.includes("v 3dennim intervalu")
        || lower.includes("v 3denním intervalu")
        || lower.includes("posledni zaloha je v 3dennim intervalu")
        || lower.includes("poslední záloha je v 3denním intervalu")
        || lower.includes("v poradku")
        || lower.includes("v pořádku")
      ) {
        return {label: "v pořádku", className: "ok"};
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
	        recordFrontendError(err);
	        showMessage(`Chyba: ${err}`);
	      } finally {
        button.disabled = false;
	      }
	    }

	    async function restartCockpit() {
	      const ok = window.confirm(
	        "Restartovat lokální Samantha Cockpit?\\n\\n" +
	        "Akce ukončí jen ověřený proces Cockpitu na portu 8770 a spustí ho znovu. " +
	        "Stránka bude pár sekund nedostupná."
	      );
	      if (!ok) return;
	      dashboardRestartBtn.disabled = true;
	      showMessage("Spouštím bezpečný restart Cockpitu...");
	      try {
	        const res = await fetch("/api/cockpit/restart", {
	          method: "POST",
	          headers: {"Content-Type": "application/json"},
	          body: JSON.stringify({confirmed: true})
	        });
	        const data = await res.json();
	        showMessage(data.message || (data.ok ? "Restart zahájen." : "Restart se nepodařilo zahájit."));
	        if (data.ok) {
	          window.setTimeout(() => {
	            window.location.reload();
	          }, 4500);
	        } else {
	          dashboardRestartBtn.disabled = false;
	        }
	      } catch (err) {
	        recordFrontendError(err);
	        showMessage(`Chyba restartu Cockpitu: ${err}`);
	        dashboardRestartBtn.disabled = false;
	      }
	    }

	    async function speakText(text, button, label) {
	      const cleaned = (text || "").trim();
	      if (!cleaned) {
	        showMessage("Nejdřív označ text, který mám přečíst.");
	        return;
	      }
	      button.disabled = true;
	      showMessage(label || "Čtu nahlas...");
	      try {
	        const edgeRes = await fetch("/api/speech/edge-tts", {
	          method: "POST",
	          headers: {"Content-Type": "application/json"},
	          body: JSON.stringify({text: cleaned})
	        });
	        const edgeData = await edgeRes.json();
	        if (edgeData.ok && edgeData.audio_base64) {
	          const audio = new Audio(`data:${edgeData.mime_type || "audio/mpeg"};base64,${edgeData.audio_base64}`);
	          try {
	            await audio.play();
	            showMessage(edgeData.message || "Přečteno českým mužským hlasem.");
	            return;
	          } catch (playErr) {
	            recordFrontendError(playErr);
	          }
	        }
	        const res = await fetch("/api/speech/speak", {
	          method: "POST",
	          headers: {"Content-Type": "application/json"},
	          body: JSON.stringify({text: cleaned})
	        });
	        const data = await res.json();
	        const fallbackHint = edgeData && edgeData.message ? ` Edge TTS: ${edgeData.message}` : "";
	        showMessage((data.message || (data.ok ? "Přečteno nahlas." : "Hlasový výstup selhal.")) + fallbackHint);
	      } catch (err) {
	        recordFrontendError(err);
	        showMessage(`Chyba hlasového výstupu: ${err}`);
	      } finally {
	        button.disabled = false;
	      }
	    }

	    async function speakDashboardStatus() {
	      const parts = [
	        statusLine.textContent,
	        dashboardOverallLabel.textContent,
	        dashboardOverallReason.textContent,
	        dashboardActionHint.textContent
	      ].map((part) => (part || "").trim()).filter(Boolean);
	      const text = parts.length
	        ? parts.join(". ")
	        : "Samantha Cockpit běží, ale aktuální stav ještě není načtený.";
	      await speakText(text, dashboardSpeakBtn, "Čtu aktuální stav nahlas...");
	    }

	    async function speakSelectedText() {
	      const currentSelection = captureSelectedSpeechText();
	      const text = currentSelection || lastSelectedSpeechText;
	      await speakText(text, dashboardSpeakSelectionBtn, "Čtu vybraný text nahlas...");
	    }

	    let voiceRecorder = null;
	    let voiceStream = null;
	    let voiceChunks = [];
	    let voiceStopTimer = null;
		    let voiceRecordingStartedAt = 0;
		    let voiceModeEnabled = localStorage.getItem("samanthaVoiceModeEnabled") === "true";
		    let latestVoiceModeRuntime = null;
		    let latestAdamResponseText = "";

	    function preferredVoiceMimeType() {
	      if (!window.MediaRecorder || !MediaRecorder.isTypeSupported) {
	        return "";
	      }
	      const candidates = [
	        "audio/webm;codecs=opus",
	        "audio/webm",
	        "audio/mp4",
	        "audio/aac"
	      ];
	      return candidates.find((candidate) => MediaRecorder.isTypeSupported(candidate)) || "";
	    }

	    function createVoiceRecorder(stream, mimeType) {
	      const baseOptions = mimeType ? {mimeType} : {};
	      try {
	        return new MediaRecorder(stream, {
	          ...baseOptions,
	          audioBitsPerSecond: 32000
	        });
	      } catch (err) {
	        return new MediaRecorder(stream, baseOptions);
	      }
	    }

	    function blobToDataUrl(blob) {
	      return new Promise((resolve, reject) => {
	        const reader = new FileReader();
	        reader.onloadend = () => resolve(String(reader.result || ""));
	        reader.onerror = () => reject(reader.error || new Error("Audio se nepodařilo načíst."));
	        reader.readAsDataURL(blob);
	      });
	    }

	    function resetVoiceRecordingUi() {
	      voiceRecordBtn.disabled = false;
	      voiceRecordBtn.classList.remove("recording");
	      voiceStopBtn.disabled = true;
	      if (voiceStopTimer) {
	        window.clearTimeout(voiceStopTimer);
	        voiceStopTimer = null;
	      }
	    }

		    function updateVoiceModeUi() {
		      voiceModeToggleBtn.textContent = voiceModeEnabled ? "Hlasový mód: zapnuto" : "Hlasový mód: vypnuto";
		      voiceModeToggleBtn.setAttribute("aria-pressed", voiceModeEnabled ? "true" : "false");
		      voiceModeToggleBtn.classList.toggle("active", voiceModeEnabled);
		      const watcherRunning = Boolean(latestVoiceModeRuntime && latestVoiceModeRuntime.running);
		      if (voiceModeEnabled) {
		        voiceCommandStatus.textContent = watcherRunning
		          ? "Hlasový mód je zapnutý a Adam Voice Mode watcher běží. Nahrané pokyny se budou hlásit Adamovi."
		          : "Hlasový mód je zapnutý jen v UI. Adam neposlouchá, dokud neběží scripts/adam_voice_mode.py.";
		      } else {
		        voiceCommandStatus.textContent = "Pokyn se po přepisu automaticky uloží pro Codex. Adam reaguje jen při spuštěném watcheru.";
		      }
		    }

		    function renderVoiceLastResponse(lastResponse) {
		      const text = String(lastResponse && lastResponse.adam_response || "").trim();
		      latestAdamResponseText = text;
		      if (!voiceLastResponseCard || !voiceLastResponseText) return;
		      voiceLastResponseCard.classList.toggle("hidden", !text);
		      voiceLastResponseText.textContent = text || "Zatím není uložená žádná Adamova odpověď.";
		      if (voiceLastResponseSpeakBtn) {
		        voiceLastResponseSpeakBtn.disabled = !text;
		      }
		    }

		    function pendingNeedsCockpitApproval(pending) {
		      if (!pending || !pending.pending) return false;
		      if (pending.approval_status === "approved") return false;
		      const reason = String(pending.reason || pending.status || "");
		      return [
		        "requires_confirmation",
		        "outbound_confirmation",
		        "terminal_delivery_failed",
		        "terminal_delivery_unverified",
		        "direct_response_failed"
		      ].includes(reason);
		    }

		    function renderVoiceApproval(pending) {
		      const visible = pendingNeedsCockpitApproval(pending);
		      if (!voiceApprovalCard) return;
		      voiceApprovalCard.classList.toggle("hidden", !visible);
		      if (!visible) return;
		      const reason = String(pending.reason || pending.status || "čeká na rozhodnutí");
		      const message = String(pending.message || "").trim();
		      const text = String(pending.text || "").trim();
		      if (voiceApprovalReason) {
		        voiceApprovalReason.textContent = message ? `${reason}: ${message}` : reason;
		      }
		      if (voiceApprovalText) {
		        voiceApprovalText.textContent = text || "Pokyn nemá uložený text.";
		      }
		    }

		    function renderVoiceBridgeSwitcher(voiceBridge) {
		      if (!voiceBridgeSwitcher || !voiceBridgeSwitcherStatus || !voiceBridgeSwitcherActions) return;
		      const markedTty = String(voiceBridge.marked_tty || "");
		      const effectiveTty = String(voiceBridge.effective_tty || "");
		      const codexTtys = Array.isArray(voiceBridge.codex_ttys)
		        ? voiceBridge.codex_ttys.map((item) => String(item || "")).filter(Boolean)
		        : [];
		      voiceBridgeSwitcher.classList.toggle("hidden", codexTtys.length === 0);
		      if (codexTtys.length === 0) {
		        voiceBridgeSwitcherStatus.textContent = "Není nalezená žádná aktivní Codex relace.";
		        voiceBridgeSwitcherActions.innerHTML = "";
		        return;
		      }
		      voiceBridgeSwitcherStatus.textContent = markedTty
		        ? `Marker: ${markedTty}. Efektivní cíl: ${effectiveTty || "nezjištěno"}.`
		        : `Marker zatím není nastavený. Efektivní cíl: ${effectiveTty || "nezjištěno"}.`;
		      voiceBridgeSwitcherActions.innerHTML = codexTtys.map((tty) => {
		        const active = tty === markedTty;
		        const effective = tty === effectiveTty && tty !== markedTty;
		        const label = active
		          ? `${tty} ✓ marker`
		          : effective
		            ? `${tty} ✓ aktivní cíl`
		            : `Nastavit ${tty}`;
		        return `<button class="${active || effective ? "primary" : "secondary"}" data-voice-bridge-tty="${escapeHtml(tty)}">${escapeHtml(label)}</button>`;
		      }).join("");
		    }

		    async function setVoiceBridgeMarker(tty, button) {
		      const targetTty = String(tty || "").trim();
		      if (!targetTty) return;
		      if (button) button.disabled = true;
		      try {
		        const data = await postJson("/api/voice-bridge/marker", {tty: targetTty});
		        showMessage(data.message || (data.ok ? `Voice bridge marker nastaven na ${targetTty}.` : "Marker se nepodařilo nastavit."));
		        await refresh({silent: true, includeSecondary: false});
		      } catch (err) {
		        recordFrontendError(err);
		        showMessage(`Nastavení voice bridge markeru selhalo: ${err}`);
		      } finally {
		        if (button) button.disabled = false;
		      }
		    }

		    async function speakLastAdamResponse() {
		      await speakText(
		        latestAdamResponseText,
		        voiceLastResponseSpeakBtn,
		        "Přehrávám poslední Adamovu odpověď v tomto prohlížeči..."
		      );
		    }

		    async function submitVoiceApproval(decision) {
		      const button = decision === "approved" ? voiceApprovalApproveBtn : voiceApprovalRejectBtn;
		      if (button) button.disabled = true;
		      try {
		        const data = await postJson("/api/voice-mode/approval", {decision});
		        showMessage(data.message || (data.ok ? "Rozhodnutí bylo uloženo." : "Rozhodnutí se nepodařilo uložit."));
		        await refresh({silent: true, includeSecondary: false});
		      } catch (err) {
		        recordFrontendError(err);
		        showMessage(`Schválení hlasového pokynu selhalo: ${err}`);
		      } finally {
		        if (voiceApprovalApproveBtn) voiceApprovalApproveBtn.disabled = false;
		        if (voiceApprovalRejectBtn) voiceApprovalRejectBtn.disabled = false;
		      }
		    }

		    function toggleVoiceMode() {
		      voiceModeEnabled = !voiceModeEnabled;
		      localStorage.setItem("samanthaVoiceModeEnabled", voiceModeEnabled ? "true" : "false");
		      updateVoiceModeUi();
		    }

		    async function startVoiceModeWatcher() {
		      voiceModeStartBtn.disabled = true;
		      voiceCommandStatus.textContent = "Spouštím Adam Voice Mode watcher...";
		      try {
		        const data = await postJson("/api/voice-mode/start", {});
		        voiceCommandStatus.textContent = data.message || "Adam Voice Mode watcher spuštěn.";
		        if (data.ok) {
		          voiceModeEnabled = true;
		          localStorage.setItem("samanthaVoiceModeEnabled", "true");
		        }
		        await refresh({silent: true, includeSecondary: false});
		      } catch (err) {
		        recordFrontendError(err);
		        voiceCommandStatus.textContent = `Adam Voice Mode watcher se nepodařilo spustit: ${err}`;
		      } finally {
		        updateVoiceModeUi();
		      }
		    }

		    async function stopVoiceModeWatcher() {
		      voiceModeStopBtn.disabled = true;
		      voiceCommandStatus.textContent = "Zastavuji Adam Voice Mode watcher...";
		      try {
		        const data = await postJson("/api/voice-mode/stop", {});
		        voiceCommandStatus.textContent = data.message || "Adam Voice Mode watcher zastaven.";
		        await refresh({silent: true, includeSecondary: false});
		      } catch (err) {
		        recordFrontendError(err);
		        voiceCommandStatus.textContent = `Adam Voice Mode watcher se nepodařilo zastavit: ${err}`;
		      } finally {
		        updateVoiceModeUi();
		      }
		    }

	    async function startVoiceRecording() {
	      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder) {
	        voiceCommandStatus.textContent = "Tento prohlížeč nepodporuje přímé nahrávání. Použij diktování do pole Přepis a tlačítko Odeslat přepis Adamovi.";
	        return;
	      }
	      voiceRecordBtn.disabled = true;
	      voiceCommandStatus.textContent = "Žádám o přístup k mikrofonu...";
	      try {
	        voiceStream = await navigator.mediaDevices.getUserMedia({
	          audio: {
	            channelCount: 1,
	            echoCancellation: true,
	            noiseSuppression: true,
	            autoGainControl: true
	          }
	        });
	        voiceChunks = [];
	        const mimeType = preferredVoiceMimeType();
	        voiceRecorder = createVoiceRecorder(voiceStream, mimeType);
	        voiceRecorder.addEventListener("dataavailable", (event) => {
	          if (event.data && event.data.size > 0) {
	            voiceChunks.push(event.data);
	          }
	        });
	        voiceRecorder.addEventListener("stop", transcribeVoiceRecording);
	        voiceRecorder.start();
	        voiceRecordingStartedAt = Date.now();
	        voiceRecordBtn.classList.add("recording");
	        voiceStopBtn.disabled = false;
	        voiceCommandStatus.textContent = "Nahrávám hlasový pokyn. Limit je 30 sekund.";
	        voiceStopTimer = window.setTimeout(stopVoiceRecording, 30000);
	      } catch (err) {
	        recordFrontendError(err);
	        voiceCommandStatus.textContent = `Mikrofon se nepodařilo spustit: ${err}`;
	        resetVoiceRecordingUi();
	      }
	    }

	    function stopVoiceRecording() {
	      if (voiceRecorder && voiceRecorder.state === "recording") {
	        voiceCommandStatus.textContent = "Zastavuji nahrávání a připravuji přepis...";
	        voiceRecorder.stop();
	      }
	      resetVoiceRecordingUi();
	    }

	    async function transcribeVoiceRecording() {
	      if (voiceStream) {
	        voiceStream.getTracks().forEach((track) => track.stop());
	        voiceStream = null;
	      }
	      const blob = new Blob(voiceChunks, {type: (voiceRecorder && voiceRecorder.mimeType) || "audio/webm"});
	      voiceRecorder = null;
	      voiceChunks = [];
	      if (!blob.size) {
	        voiceCommandStatus.textContent = "Nahrávka je prázdná. Zkus to znovu.";
	        return;
	      }
	      const recordedSeconds = voiceRecordingStartedAt ? Math.max(0, Math.round((Date.now() - voiceRecordingStartedAt) / 1000)) : 0;
	      const audioKb = Math.round(blob.size / 1024);
	      const requestStartedAt = Date.now();
	      voiceCommandStatus.textContent = `Přepisuji hlasový pokyn (${recordedSeconds} s, ${audioKb} kB)...`;
	      try {
	        const dataUrl = await blobToDataUrl(blob);
	        const audioBase64 = dataUrl.includes(",") ? dataUrl.split(",", 2)[1] : dataUrl;
	        const res = await fetch("/api/speech/transcribe", {
	          method: "POST",
	          headers: {"Content-Type": "application/json"},
	          body: JSON.stringify({
	            audio_base64: audioBase64,
	            mime_type: blob.type || "audio/webm",
	            language: "cs"
	          })
	        });
	        const data = await res.json();
		        if (data.ok) {
		          voiceTranscript.value = data.text || "";
	          const totalMs = Date.now() - requestStartedAt;
	          const serverMs = data.duration_ms || 0;
	          const openaiMs = data.timing && data.timing.openai_ms ? data.timing.openai_ms : 0;
	          const timing = `celkem ${Math.round(totalMs / 1000)} s, server ${Math.round(serverMs / 1000)} s, OpenAI ${Math.round(openaiMs / 1000)} s, audio ${data.audio_kb || audioKb} kB`;
	          const savedHint = data.latest_voice_command_path ? ` Uloženo: ${data.latest_voice_command_path}.` : "";
		          const modeHint = voiceModeEnabled ? " Hlasový mód: čekám na Adamovo převzetí nebo další nahrávku." : "";
		          voiceCommandStatus.textContent = `${data.message || "Hlasový pokyn byl přepsán a uložen."}${savedHint}${modeHint} (${timing})`;
	        } else {
	          voiceCommandStatus.textContent = data.message || "Přepis hlasu selhal.";
	        }
	      } catch (err) {
	        recordFrontendError(err);
	        voiceCommandStatus.textContent = `Přepis hlasu selhal: ${err}`;
	      }
	    }

	    async function submitVoiceTranscript() {
	      const text = voiceTranscript.value.trim();
	      if (!text) {
	        voiceCommandStatus.textContent = "Nejdřív napiš nebo nadiktuj text do pole Přepis.";
	        voiceTranscript.focus();
	        return;
	      }
	      voiceTranscriptSendBtn.disabled = true;
	      voiceCommandStatus.textContent = "Ukládám přepis pro Adama...";
	      try {
	        const data = await postJson("/api/speech/voice-text", {text});
	        if (data.ok) {
	          const savedHint = data.latest_voice_command_path ? ` Uloženo: ${data.latest_voice_command_path}.` : "";
	          const modeHint = voiceModeEnabled ? " Hlasový mód: čekám na Adamovo převzetí." : "";
	          voiceCommandStatus.textContent = `${data.message || "Textový hlasový pokyn byl uložen."}${savedHint}${modeHint}`;
	          voiceTranscript.value = "";
	          await refresh({silent: true, includeSecondary: false});
	        } else {
	          voiceCommandStatus.textContent = data.message || "Textový hlasový pokyn se nepodařilo uložit.";
	        }
	      } catch (err) {
	        recordFrontendError(err);
	        voiceCommandStatus.textContent = `Textový hlasový pokyn se nepodařilo uložit: ${err}`;
	      } finally {
	        voiceTranscriptSendBtn.disabled = false;
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
        const headOpenBtn = document.createElement("button");
        headOpenBtn.className = "primary";
        headOpenBtn.type = "button";
        headOpenBtn.textContent = "Otevřít / číst";
        const headActions = document.createElement("div");
        headActions.className = "search-result-head-actions";
        headActions.appendChild(headOpenBtn);
        headActions.appendChild(toggle);
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
        const openBtn = document.createElement("button");
        openBtn.className = "primary";
        openBtn.type = "button";
        openBtn.textContent = "Otevřít / číst PDF";
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
        headOpenBtn.addEventListener("click", () => openDocumentForReading(documentRef, headOpenBtn));
        openBtn.addEventListener("click", () => openDocumentForReading(documentRef, openBtn));
        printBtn.addEventListener("click", () => printDocument(documentRef));
        archiveBtn.addEventListener("click", () => moveDocumentLifecycle(documentRef, "archive"));
        trashBtn.addEventListener("click", () => moveDocumentLifecycle(documentRef, "trash"));
        actions.appendChild(openBtn);
        actions.appendChild(printBtn);
        actions.appendChild(archiveBtn);
        actions.appendChild(trashBtn);
        summary.appendChild(title);
        summary.appendChild(meta);
        head.appendChild(summary);
        head.appendChild(headActions);
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

    function documentReaderUrl(documentId) {
      return `/documents/read?document_id=${encodeURIComponent(documentId || "")}`;
    }

    function openDocumentReaderWindow(documentId, statusNode, button) {
      if (!documentId) return;
      const originalText = button ? button.textContent : "";
      if (button) button.disabled = true;
      if (button) button.textContent = "Otevírám...";
      const url = documentReaderUrl(documentId);
      try {
        const reader = window.open(url, "samanthaDocumentReader", "width=1180,height=860");
        if (reader) {
          reader.focus();
          if (statusNode) statusNode.textContent = "Dokument je otevřený ve čtecím okně Cockpitu.";
        } else {
          window.location.href = url;
        }
      } catch (err) {
        recordFrontendError(err);
        if (statusNode) statusNode.textContent = `Chyba otevření dokumentu: ${err}`;
      } finally {
        if (button) button.disabled = false;
        if (button) button.textContent = originalText || "Otevřít PDF";
      }
    }

    function openDocumentForReading(documentId, button) {
      openDocumentReaderWindow(documentId, documentSearchStatus, button);
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
	        recordFrontendError(err);
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
        recordFrontendError(err);
        webAppsStatus.textContent = `Chyba načtení aplikací: ${err}`;
      }
    }

    function closeWebAppsModal() {
      webAppsModal.classList.add("hidden");
      maybeReturnToJanicka("webApps");
    }

    async function openLibraryModal() {
      libraryModal.classList.remove("hidden");
      await loadLibraryCategory(currentLibraryCategory);
    }

    function closeLibraryModal() {
      libraryModal.classList.add("hidden");
    }

    async function loadLibraryCategory(category) {
      currentLibraryCategory = category || "other";
      currentLibrarySelectedId = "";
      setLibraryActiveTab();
      librarySearchInput.value = "";
      libraryStatus.textContent = "Načítám knihovnu...";
      libraryReaderTitle.textContent = "Vyber článek";
      libraryReaderMeta.textContent = "Vlevo vyber položku nebo použij fulltextové hledání.";
      libraryReaderText.textContent = "";
      renderLibraryAttachments("", []);
      try {
        const data = await fetchJson(`/api/library/list?category=${encodeURIComponent(currentLibraryCategory)}&limit=200`);
        currentLibraryItems = data.items || [];
        renderLibraryItems(currentLibraryItems);
        libraryStatus.textContent = currentLibraryItems.length
          ? `${data.category_label || "Kategorie"}: ${currentLibraryItems.length} položek.`
          : `${data.category_label || "Kategorie"} zatím nemá uložené položky.`;
      } catch (err) {
        recordFrontendError(err);
        libraryStatus.textContent = `Chyba načtení knihovny: ${err}`;
      }
    }

    function setLibraryActiveTab() {
      document.querySelectorAll("[data-library-category]").forEach((button) => {
        button.classList.toggle("active", button.dataset.libraryCategory === currentLibraryCategory);
      });
    }

    async function searchLibrary() {
      const query = librarySearchInput.value.trim();
      if (query.length < 2) {
        await loadLibraryCategory(currentLibraryCategory);
        return;
      }
      libraryStatus.textContent = "Hledám ve fulltextu...";
      try {
        const url = `/api/library/search?category=${encodeURIComponent(currentLibraryCategory)}&q=${encodeURIComponent(query)}&limit=80`;
        const data = await fetchJson(url);
        currentLibraryItems = data.items || [];
        renderLibraryItems(currentLibraryItems);
        libraryStatus.textContent = currentLibraryItems.length
          ? `Nalezeno ${currentLibraryItems.length} položek pro „${query}“.`
          : `Pro „${query}“ nic nenalezeno.`;
      } catch (err) {
        recordFrontendError(err);
        libraryStatus.textContent = `Chyba hledání v knihovně: ${err}`;
      }
    }

    async function archiveLibraryUrl() {
      const url = libraryArchiveUrlInput.value.trim();
      if (!url) {
        libraryArchiveStatus.textContent = "Vlož URL článku.";
        libraryArchiveUrlInput.focus();
        return;
      }
      const category = libraryArchiveCategory.value || currentLibraryCategory || "other";
      const tags = libraryArchiveTagsInput.value.trim();
      libraryArchiveBtn.disabled = true;
      libraryArchiveStatus.textContent = "Stahuji a ukládám článek do soukromé knihovny...";
      try {
        const data = await postJson("/api/library/archive", {url, category, tags});
        if (!data.ok) {
          libraryArchiveStatus.textContent = data.message || "Článek se nepodařilo uložit.";
          return;
        }
        const item = data.item || {};
        libraryArchiveStatus.textContent = data.message || "Článek uložen.";
        libraryArchiveUrlInput.value = "";
        libraryArchiveTagsInput.value = "";
        currentLibraryCategory = item.category || category;
        await loadLibraryCategory(currentLibraryCategory);
        if (item.id) {
          await loadLibraryItem(item.id);
        }
      } catch (err) {
        recordFrontendError(err);
        libraryArchiveStatus.textContent = `Chyba uložení URL: ${err}`;
      } finally {
        libraryArchiveBtn.disabled = false;
      }
    }

    async function saveLibraryText() {
      const title = libraryTextTitleInput.value.trim();
      const text = libraryTextBodyInput.value.trim();
      if (!text) {
        libraryTextStatus.textContent = "Vlož text, který chceš uložit.";
        libraryTextBodyInput.focus();
        return;
      }
      const category = libraryTextCategory.value || currentLibraryCategory || "other";
      const tags = libraryTextTagsInput.value.trim();
      const sourceLabel = libraryTextSourceInput.value.trim() || "Vložený text";
      libraryTextSaveBtn.disabled = true;
      libraryTextStatus.textContent = "Ukládám text do znalostní databáze...";
      try {
        const data = await postJson("/api/library/text", {
          title,
          text,
          category,
          tags,
          source_label: sourceLabel,
          source_note: sourceLabel,
        });
        if (!data.ok) {
          libraryTextStatus.textContent = data.message || "Text se nepodařilo uložit.";
          return;
        }
        const item = data.item || {};
        libraryTextStatus.textContent = data.message || "Text uložen.";
        libraryTextTitleInput.value = "";
        libraryTextTagsInput.value = "";
        libraryTextBodyInput.value = "";
        currentLibraryCategory = item.category || category;
        await loadLibraryCategory(currentLibraryCategory);
        if (item.id) {
          await loadLibraryItem(item.id);
        }
      } catch (err) {
        recordFrontendError(err);
        libraryTextStatus.textContent = `Chyba uložení textu: ${err}`;
      } finally {
        libraryTextSaveBtn.disabled = false;
      }
    }

    async function attachLibraryImage() {
      const articleId = currentLibrarySelectedId;
      if (!articleId) {
        libraryAttachmentStatus.textContent = "Nejdřív vyber kartu v seznamu vlevo.";
        return;
      }
      const file = libraryAttachmentFileInput.files && libraryAttachmentFileInput.files[0];
      if (!file) {
        libraryAttachmentStatus.textContent = "Vyber obrázek k připojení.";
        libraryAttachmentFileInput.focus();
        return;
      }
      if (!String(file.type || "").startsWith("image/")) {
        libraryAttachmentStatus.textContent = "Soubor musí být obrázek.";
        return;
      }
      if (file.size > 20 * 1024 * 1024) {
        libraryAttachmentStatus.textContent = "Obrázek je větší než 20 MB. Nejdřív ho zmenši nebo pošli menší kopii.";
        return;
      }
      libraryAttachmentSaveBtn.disabled = true;
      libraryAttachmentStatus.textContent = "Připojuji obrázek a vytvářím čitelnou kopii...";
      try {
        const imageDataUrl = await blobToDataUrl(file);
        const data = await postJson("/api/library/attachment/add", {
          article_id: articleId,
          image_data_url: imageDataUrl,
          filename: file.name || "attachment.jpg",
          label: libraryAttachmentLabelInput.value.trim() || "Ručně psaný recept",
          tags: libraryAttachmentTagsInput.value.trim(),
          note: libraryAttachmentNoteInput.value.trim()
        });
        if (!data.ok) {
          libraryAttachmentStatus.textContent = data.message || "Obrázek se nepodařilo připojit.";
          return;
        }
        libraryAttachmentStatus.textContent = data.message || "Obrázek připojen.";
        libraryAttachmentFileInput.value = "";
        libraryAttachmentLabelInput.value = "";
        libraryAttachmentTagsInput.value = "";
        libraryAttachmentNoteInput.value = "";
        await loadLibraryCategory(currentLibraryCategory);
        await loadLibraryItem(articleId);
      } catch (err) {
        recordFrontendError(err);
        libraryAttachmentStatus.textContent = `Chyba připojení obrázku: ${err}`;
      } finally {
        libraryAttachmentSaveBtn.disabled = false;
      }
    }

    function renderLibraryItems(items) {
      libraryList.innerHTML = "";
      if (!items.length) {
        const empty = document.createElement("div");
        empty.className = "library-item";
        empty.textContent = "Žádné položky k zobrazení.";
        libraryList.appendChild(empty);
        return;
      }
      items.forEach((item) => {
        const row = document.createElement("button");
        row.type = "button";
        row.className = "library-item";
        row.dataset.articleId = item.id || "";
        row.classList.toggle("active", currentLibrarySelectedId === item.id);
        const title = document.createElement("div");
        title.className = "library-title";
        title.textContent = item.one_line_title || item.title || "Bez názvu";
        const meta = document.createElement("div");
        meta.className = "library-meta";
        meta.textContent = libraryItemMeta(item);
        row.appendChild(title);
        row.appendChild(meta);
        if (item.snippet) {
          const snippet = document.createElement("div");
          snippet.className = "library-snippet";
          snippet.textContent = item.snippet;
          row.appendChild(snippet);
        }
        row.addEventListener("click", () => loadLibraryItem(item.id || ""));
        libraryList.appendChild(row);
      });
    }

    function libraryItemMeta(item) {
      const parts = [];
      const date = String(item.archived_at || "").slice(0, 10);
      if (date) parts.push(date);
      if (item.category_label) parts.push(item.category_label);
      if (item.source_label) parts.push(item.source_label);
      const url = item.canonical_url || item.source_url || "";
      if (url) {
        try {
          parts.push(new URL(url).hostname);
        } catch (_err) {
          parts.push(url);
        }
      }
      if (item.text_chars) parts.push(`${item.text_chars} znaků`);
      if (item.attachment_count) parts.push(`${item.attachment_count} příloh`);
      return parts.join(" | ");
    }

    function libraryAttachmentUrl(articleId, attachmentId, variant) {
      return `/api/library/attachment?id=${encodeURIComponent(articleId || "")}&attachment_id=${encodeURIComponent(attachmentId || "")}&variant=${encodeURIComponent(variant || "readable")}`;
    }

    function renderLibraryAttachments(articleId, attachments) {
      if (!libraryReaderAttachments) return;
      libraryReaderAttachments.innerHTML = "";
      const items = Array.isArray(attachments) ? attachments : [];
      libraryReaderAttachments.classList.toggle("hidden", items.length === 0);
      items.forEach((attachment) => {
        const card = document.createElement("div");
        card.className = "library-attachment-card";
        const title = document.createElement("div");
        title.className = "library-attachment-title";
        title.textContent = attachment.label || "Příloha";
        const meta = document.createElement("div");
        meta.className = "library-attachment-meta";
        const metaParts = [];
        if (attachment.role) metaParts.push(attachment.role);
        if (attachment.kind) metaParts.push(attachment.kind);
        if (attachment.mime_type) metaParts.push(attachment.mime_type);
        if (attachment.size_bytes) metaParts.push(`${Math.round(Number(attachment.size_bytes) / 1024)} kB`);
        meta.textContent = metaParts.join(" | ");
        card.appendChild(title);
        card.appendChild(meta);
        const attachmentId = attachment.id || "";
        const imageSrc = libraryAttachmentUrl(articleId, attachmentId, attachment.has_readable ? "readable" : "original");
        if (String(attachment.kind || "").toLowerCase().includes("image") || String(attachment.mime_type || "").startsWith("image/")) {
          const link = document.createElement("a");
          link.href = imageSrc;
          link.setAttribute("target", "_blank");
          link.rel = "noopener";
          const image = document.createElement("img");
          image.className = "library-attachment-image";
          image.src = libraryAttachmentUrl(articleId, attachmentId, attachment.has_thumb ? "thumb" : "readable");
          image.alt = attachment.label || "Příloha";
          link.appendChild(image);
          card.appendChild(link);
        }
        const actions = document.createElement("div");
        actions.className = "actions compact-actions";
        const readable = document.createElement("a");
        readable.className = "button-link";
        readable.href = imageSrc;
        readable.setAttribute("target", "_blank");
        readable.rel = "noopener";
        readable.textContent = "Otevřít přílohu";
        actions.appendChild(readable);
        if (attachment.has_original) {
          const original = document.createElement("a");
          original.className = "button-link secondary-link";
          original.href = libraryAttachmentUrl(articleId, attachmentId, "original");
          original.setAttribute("target", "_blank");
          original.rel = "noopener";
          original.textContent = "Originál";
          actions.appendChild(original);
        }
        card.appendChild(actions);
        if (attachment.note) {
          const note = document.createElement("div");
          note.className = "library-snippet";
          note.textContent = attachment.note;
          card.appendChild(note);
        }
        libraryReaderAttachments.appendChild(card);
      });
    }

    async function loadLibraryItem(articleId) {
      if (!articleId) return;
      currentLibrarySelectedId = articleId;
      document.querySelectorAll(".library-item").forEach((node) => {
        node.classList.toggle("active", node.dataset.articleId === articleId);
      });
      libraryReaderTitle.textContent = "Načítám článek...";
      libraryReaderMeta.textContent = "";
      libraryReaderText.textContent = "";
      renderLibraryAttachments("", []);
      try {
        const data = await fetchJson(`/api/library/item?id=${encodeURIComponent(articleId)}`);
        if (!data.ok) {
          libraryReaderTitle.textContent = "Článek nelze načíst";
          libraryReaderMeta.textContent = data.message || data.error || "";
          return;
        }
        const item = data.item || {};
        libraryReaderTitle.textContent = item.one_line_title || item.title || "Bez názvu";
        libraryReaderMeta.textContent = libraryItemMeta(item);
        libraryReaderText.textContent = data.text || "";
        renderLibraryAttachments(item.id || articleId, item.attachments || []);
      } catch (err) {
        recordFrontendError(err);
        libraryReaderTitle.textContent = "Chyba čtení";
        libraryReaderMeta.textContent = String(err);
        renderLibraryAttachments("", []);
      }
    }

    async function openProjectsModal() {
      projectsModal.classList.remove("hidden");
      projectsStatus.textContent = "Načítám projekty a schopnosti...";
      projectsList.innerHTML = "";
      try {
        const res = await fetch("/api/projects/status");
        const data = await res.json();
        currentProjects = data.items || data.projects || [];
        renderProjects(currentProjects, currentProjectFilter);
        renderProjectsStatusLine(data);
      } catch (err) {
        recordFrontendError(err);
        projectsStatus.textContent = `Chyba načtení projektů a schopností: ${err}`;
      }
    }

    function renderProjectsStatusLine(data) {
      const summary = data.summary || {};
      const catalogSummary = data.catalog_summary || {};
      const management = catalogSummary.project_management || {};
      const lifecycle = catalogSummary.project_lifecycle || {};
      const flags = summary.flag_counts || {};
      const remind = flags["připomenout"] || 0;
      const needsAttention = management.needs_attention || 0;
      const archived = lifecycle.archived || catalogSummary.archived_projects || 0;
      projectsStatus.textContent = data.ok
        ? `${catalogSummary.projects || summary.active_total || 0} aktivních projektů, ${catalogSummary.tools || 0} toolů, ${catalogSummary.infrastructure_capabilities || 0} infrastrukturních vrstev${archived ? `; ${archived} archiv` : ""}${remind ? `; ${remind} připomenout` : ""}${needsAttention ? `; ${needsAttention} doplnit` : ""}.`
        : (data.message || "Projekty nejdou načíst.");
    }

    function closeProjectsModal() {
      projectsModal.classList.add("hidden");
      maybeReturnToJanicka("projects");
    }

    async function openQuickNotesModal() {
      quickNotesModal.classList.remove("hidden");
      quickNotesStatus.textContent = "Načítám rychlé poznámky...";
      quickNotesList.innerHTML = "";
      try {
        const data = await fetchJson("/api/quick-notes/status");
        renderQuickNotes(data);
      } catch (err) {
        recordFrontendError(err);
        quickNotesStatus.textContent = `Chyba načtení rychlých poznámek: ${err}`;
      }
    }

	    function closeQuickNotesModal() {
	      quickNotesModal.classList.add("hidden");
	    }

    async function openUrgentRemindersModal() {
      urgentRemindersModal.classList.remove("hidden");
      urgentRemindersStatus.textContent = "Načítám důležitá připomenutí...";
      urgentRemindersList.innerHTML = "";
      try {
        const data = await fetchJson("/api/urgent-reminders/status");
        renderUrgentReminders(data);
      } catch (err) {
        recordFrontendError(err);
        urgentRemindersStatus.textContent = `Chyba načtení důležitých připomenutí: ${err}`;
      }
    }

    function closeUrgentRemindersModal() {
      urgentRemindersModal.classList.add("hidden");
    }

    function renderUrgentReminderAlert(data) {
      const counts = data.counts || {};
      const openCount = counts.open || 0;
      const hasLoadError = data && data.ok === false;
      urgentReminderAlert.classList.toggle("hidden", openCount <= 0 && !hasLoadError);
      urgentReminderAlertList.innerHTML = "";
      if (hasLoadError) {
        urgentReminderAlertTitle.textContent = "Důležitá připomenutí: chyba načtení";
        const line = document.createElement("div");
        line.className = "urgent-alert-detail";
        line.textContent = data.message || "Důležitá připomenutí se nepodařilo načíst.";
        urgentReminderAlertList.appendChild(line);
        return;
      }
      if (openCount <= 0) {
        urgentReminderAlertTitle.textContent = "Důležitá připomenutí";
        return;
      }
      urgentReminderAlertTitle.textContent = `Důležitá připomenutí: ${openCount}`;
      (data.items || []).slice(0, 3).forEach((item) => {
        const row = document.createElement("div");
        row.className = "urgent-alert-item";
        const toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "urgent-alert-summary";
        toggle.textContent = `#${item.reminder_number || "?"}: ${item.summary || item.title || ""}`;
        const detail = document.createElement("div");
        detail.className = "urgent-alert-detail hidden";
        detail.textContent = urgentReminderBodyText(item);
        toggle.addEventListener("click", () => {
          detail.classList.toggle("hidden");
        });
        row.appendChild(toggle);
        row.appendChild(detail);
        urgentReminderAlertList.appendChild(row);
      });
      if ((data.items || []).length > 3 || openCount > 3) {
        const more = document.createElement("div");
        more.textContent = "Další položky jsou v přehledu.";
        urgentReminderAlertList.appendChild(more);
      }
    }

    function renderUrgentReminders(data) {
      const counts = data.counts || {};
      urgentRemindersStatus.textContent = data.ok
        ? `${counts.open || 0} otevřených. ${data.message || ""}`
        : (data.message || "Důležitá připomenutí nejdou načíst.");
      urgentRemindersList.innerHTML = "";
      const items = data.items || [];
      if (!items.length) {
        const empty = document.createElement("div");
        empty.className = "status-line";
        empty.textContent = data.inbox_exists ? "Žádná otevřená důležitá připomenutí." : "Inbox zatím není synchronizovaný na Mac.";
        urgentRemindersList.appendChild(empty);
        return;
      }
      items.forEach((item) => {
        const card = document.createElement("div");
        card.className = "project-card";
        const head = document.createElement("div");
        head.className = "project-head";
        const title = document.createElement("div");
        title.className = "project-title";
        title.textContent = `Připomenutí #${item.reminder_number || "?"}: ${item.summary || item.title || ""}`;
        const badge = document.createElement("span");
        badge.className = "project-priority bad";
        badge.textContent = item.priority || "urgent";
        head.appendChild(title);
        head.appendChild(badge);
        const meta = document.createElement("div");
        meta.className = "project-meta";
        meta.textContent = `${item.created_at || ""} | ${item.size_bytes || 0} B | ${item.status || "open"}`;
        const body = document.createElement("div");
        body.className = "urgent-reminder-body";
        body.textContent = urgentReminderBodyText(item);
        const actions = document.createElement("div");
        actions.className = "project-flags";
        const doneBtn = document.createElement("button");
        doneBtn.type = "button";
        doneBtn.className = "reminder-done";
        doneBtn.textContent = "Splněno";
        doneBtn.disabled = !item.reminder_number;
        doneBtn.addEventListener("click", () => markUrgentReminderDone(item.reminder_number, doneBtn));
        actions.appendChild(doneBtn);
        card.appendChild(head);
        card.appendChild(meta);
        card.appendChild(body);
        card.appendChild(actions);
        urgentRemindersList.appendChild(card);
      });
    }

    function urgentReminderBodyText(item) {
      return item.body_text || item.summary || item.title || "";
    }

	    async function openRecoveryModal() {
	      recoveryModal.classList.remove("hidden");
	      recoveryStatus.textContent = "Načítám recovery stav...";
	      recoveryAutosave.textContent = "";
	      recoveryGit.textContent = "";
	      recoveryProject.textContent = "";
	      recoveryHandoffs.innerHTML = "";
	      recoveryCommands.innerHTML = "";
	      try {
	        const data = await fetchJson("/api/recovery/status");
	        renderRecoveryStatus(data);
		      } catch (err) {
		        recordFrontendError(err);
		        recoveryStatus.textContent = `Chyba načtení Recovery centra: ${err}`;
	      }
	    }

    function closeRecoveryModal() {
      recoveryModal.classList.add("hidden");
      maybeReturnToJanicka("recovery");
    }

	    function renderRecoveryStatus(data) {
	      const autosave = data.autosave || {};
	      const git = data.git || {};
	      const project = data.active_project || {};
	      recoveryStatus.textContent = `${data.message || "Recovery centrum načteno."} ${data.safety_note || ""}`;
	      recoveryAutosave.textContent = autosave.ok
	        ? `Poslední: ${autosave.latest_file || ""} | ${autosave.latest_modified_at || ""} | ${formatAge(autosave.latest_age_seconds)} | souborů: ${autosave.file_count || 0}`
	        : (autosave.message || "Autosave metadata nejsou dostupná.");
	      recoveryGit.textContent = git.ok
	        ? `${git.message || ""} | ${git.branch || ""}${git.dirty_count ? ` | ukázka: ${(git.dirty_files || []).join("; ")}` : ""}`
	        : (git.message || "Git status nejde načíst.");
	      recoveryProject.textContent = project.ok
	        ? `${project.name || "Cockpit Recovery centrum"} | priorita ${project.priority || ""} | ${project.next_step || project.status || ""}`
	        : (project.message || "Aktivní projekt Recovery centra není nalezen.");
	      renderRecoveryHandoffs(data.handoffs || []);
	      renderRecoveryCommands(data.commands || []);
	    }

	    function renderRecoveryHandoffs(items) {
	      recoveryHandoffs.innerHTML = "";
	      if (!items.length) {
	        recoveryHandoffs.textContent = "Žádné recovery handoffy nejsou nastavené.";
	        return;
	      }
	      items.forEach((item) => {
	        const card = document.createElement("div");
	        card.className = "project-card";
	        const title = document.createElement("div");
	        title.className = "project-title";
	        title.textContent = item.title || item.path || "Handoff";
	        const meta = document.createElement("div");
	        meta.className = "project-meta";
	        meta.textContent = `${item.path || ""} | priorita ${item.priority || ""} | ${item.status || ""} | ${item.date || ""}`;
	        const next = document.createElement("div");
	        next.className = "project-next";
	        next.textContent = item.next_step || item.message || "";
	        card.appendChild(title);
	        card.appendChild(meta);
	        card.appendChild(next);
	        recoveryHandoffs.appendChild(card);
	      });
	    }

	    function renderRecoveryCommands(items) {
	      recoveryCommands.innerHTML = "";
	      items.forEach((item) => {
	        const card = document.createElement("div");
	        card.className = "project-card";
	        const title = document.createElement("div");
	        title.className = "project-title";
	        title.textContent = item.label || "Příkaz";
	        const command = document.createElement("div");
	        command.className = "recovery-command";
	        command.textContent = item.command || "";
	        const note = document.createElement("div");
	        note.className = "project-meta";
	        note.textContent = item.note || "";
	        card.appendChild(title);
	        card.appendChild(command);
	        card.appendChild(note);
	        recoveryCommands.appendChild(card);
	      });
	    }

	    function formatAge(seconds) {
	      if (seconds === null || seconds === undefined) return "stáří neznámé";
	      const value = Number(seconds);
	      if (!Number.isFinite(value)) return "stáří neznámé";
	      if (value < 60) return `${Math.round(value)} s`;
	      if (value < 3600) return `${Math.round(value / 60)} min`;
	      if (value < 86400) return `${Math.round(value / 3600)} h`;
	      return `${Math.round(value / 86400)} d`;
	    }

	    function renderQuickNotes(data) {
      const counts = data.counts || {};
      quickNotesStatus.textContent = data.ok
        ? `${counts.active || 0} aktivních QN. ${data.message || ""}`
        : (data.message || "Quick Notes nejdou načíst.");
      quickNotesList.innerHTML = "";
      const notes = data.notes || [];
      if (!notes.length) {
        const empty = document.createElement("div");
        empty.className = "status-line";
        empty.textContent = data.inbox_exists ? "Žádné aktivní QN." : "Inbox zatím není synchronizovaný na Mac.";
        quickNotesList.appendChild(empty);
        return;
      }
      notes.forEach((note) => {
        const card = document.createElement("div");
        card.className = "project-card";
        const head = document.createElement("div");
        head.className = "project-head";
        const title = document.createElement("div");
        title.className = "project-title";
        title.textContent = `QN #${note.note_number || "?"}: ${note.snippet || note.title || ""}`;
        const badge = document.createElement("span");
        badge.className = "project-priority";
        badge.textContent = note.category || "inbox";
        head.appendChild(title);
        head.appendChild(badge);
        const meta = document.createElement("div");
        meta.className = "project-meta";
        meta.textContent = `${note.created_at || ""} | ${note.size_bytes || 0} B`;
        const triage = document.createElement("div");
        triage.className = "project-next";
        triage.textContent = quickNoteTriageLine(note.triage || {});
        const safety = document.createElement("div");
        safety.className = "project-meta";
        safety.textContent = (note.triage && note.triage.safety_note) || "";
        const actions = document.createElement("div");
        actions.className = "project-flags";
        const detailBtn = document.createElement("button");
        detailBtn.className = "secondary";
        detailBtn.type = "button";
        detailBtn.textContent = "Detail";
        const detail = document.createElement("div");
        detail.className = "project-detail quick-note-detail hidden";
        detailBtn.addEventListener("click", () => loadQuickNoteDetail(note, detail, detailBtn));
        actions.appendChild(detailBtn);
        card.appendChild(head);
        card.appendChild(meta);
        card.appendChild(triage);
        if (safety.textContent) card.appendChild(safety);
        card.appendChild(actions);
        card.appendChild(detail);
        quickNotesList.appendChild(card);
      });
    }

    function quickNoteTriageLine(triage) {
      const classification = triage.classification || "Nezařazeno";
      const next = triage.suggested_next_step || "Přečíst detail a ručně rozhodnout.";
      return `Klasifikace: ${classification}. Další krok: ${next}`;
    }

    async function loadQuickNoteDetail(note, detailNode, button) {
      if (!note.note_number) {
        detailNode.textContent = "QN nemá platné číslo.";
        detailNode.classList.remove("hidden");
        return;
      }
      if (detailNode.dataset.loaded === "true") {
        const isHidden = detailNode.classList.toggle("hidden");
        button.textContent = isHidden ? "Detail" : "Zavřít detail";
        return;
      }
      button.disabled = true;
      button.textContent = "Načítám...";
      detailNode.classList.remove("hidden");
      detailNode.textContent = "Načítám detail QN...";
      try {
        const data = await fetchJson(`/api/quick-notes/detail?note_number=${encodeURIComponent(note.note_number)}`);
        detailNode.innerHTML = "";
        const status = document.createElement("div");
        status.className = "project-meta";
        status.textContent = data.ok
          ? `${data.created_at || ""} | ${data.size_bytes || 0} B${data.truncated ? " | zkráceno" : ""}`
          : (data.message || "Detail QN se nepodařilo načíst.");
        const triage = document.createElement("div");
        triage.className = "project-next";
        triage.textContent = quickNoteTriageLine(data.triage || {});
        const safety = document.createElement("div");
        safety.className = "project-meta";
        safety.textContent = (data.triage && data.triage.safety_note) || "";
        const pre = document.createElement("pre");
        pre.textContent = data.body_text || data.message || "";
        detailNode.appendChild(status);
        detailNode.appendChild(triage);
        if (safety.textContent) detailNode.appendChild(safety);
        detailNode.appendChild(pre);
        detailNode.dataset.loaded = "true";
        button.textContent = "Zavřít detail";
      } catch (err) {
        detailNode.textContent = `Chyba načtení detailu QN: ${err}`;
        button.textContent = "Detail";
      } finally {
        button.disabled = false;
      }
    }

    function projectMatchesFilter(project, filter) {
      const priority = String(project.priority || "");
      const flags = project.flags || [];
      const haystack = `${project.status || ""} ${project.next_step || ""}`.toLocaleLowerCase("cs-CZ");
      const category = project.category || "project";
      const lifecycle = project.lifecycle || "active";
      if (filter === "archived") return category === "project" && lifecycle === "archived";
      if (lifecycle === "archived") return false;
      if (filter === "projects") return category === "project";
      if (filter === "tools") return category === "tool";
      if (filter === "infrastructure") return category === "infrastructure";
	      if (filter === "priority1") return priority === "1" || priority === "A1+";
	      if (filter === "remind") return flags.includes("připomenout");
	      if (filter === "needs_attention") return Boolean(project.needs_attention);
	      if (filter === "waiting") {
	        return flags.includes("čeká na retest")
	          || flags.includes("blokováno")
	          || (project.management_flags || []).includes("čeká na Mílu")
	          || haystack.includes("čeká")
	          || haystack.includes("ceka")
          || haystack.includes("rozhodnout")
          || haystack.includes("otestovat")
          || haystack.includes("retest");
      }
      return true;
    }

    function renderProjects(projects, filter) {
      projectsList.innerHTML = "";
      document.querySelectorAll("[data-project-filter]").forEach((button) => {
        button.classList.toggle("active", button.dataset.projectFilter === filter);
      });
      const filtered = (projects || []).filter((project) => projectMatchesFilter(project, filter));
      if (!filtered.length) {
        const empty = document.createElement("div");
        empty.className = "status-line";
        empty.textContent = "Žádná položka pro tento filtr.";
        projectsList.appendChild(empty);
        return;
      }
	      filtered.forEach((project) => {
	        const card = document.createElement("div");
	        card.className = "project-card";
	        if (project.needs_attention) card.classList.add("needs-attention");
	        const head = document.createElement("div");
        head.className = "project-head";
        const title = document.createElement("div");
        title.className = "project-title";
        title.textContent = project.name || "Položka bez názvu";
        const priority = document.createElement("span");
        priority.className = "project-priority";
        priority.textContent = project.priority
          ? `P ${project.priority}`
          : (project.level || project.category_label || project.category || "?");
        head.appendChild(title);
        head.appendChild(priority);
        const status = document.createElement("div");
        status.className = "project-meta";
        status.textContent = project.summary || project.status || "";
	        const next = document.createElement("div");
	        next.className = "project-next";
        const nextLabel = project.category === "tool"
          ? "Bezpečnostní rozsah"
          : project.category === "infrastructure"
            ? "Pomáhá"
            : "Další krok";
	        next.textContent = project.next_step ? `${nextLabel}: ${project.next_step}` : `${nextLabel} není uveden.`;
	        const management = document.createElement("div");
	        management.className = project.needs_attention ? "project-next" : "project-meta";
	        management.textContent = project.management_reason || "";
	        const flags = document.createElement("div");
	        flags.className = "project-flags";
        const categoryFlag = document.createElement("span");
        categoryFlag.className = "project-flag";
        categoryFlag.textContent = project.category_label || project.category || "Project";
        flags.appendChild(categoryFlag);
        if (project.lifecycle_label) {
          const lifecycleFlag = document.createElement("span");
          lifecycleFlag.className = "project-flag";
          lifecycleFlag.textContent = project.lifecycle_label;
          flags.appendChild(lifecycleFlag);
        }
	        (project.flags || []).forEach((flag) => {
	          const node = document.createElement("span");
	          node.className = "project-flag";
	          node.textContent = flag;
	          flags.appendChild(node);
	        });
	        (project.management_flags || []).forEach((flag) => {
	          const node = document.createElement("span");
	          node.className = `project-flag ${project.needs_attention ? "attention" : ""}`;
	          node.textContent = flag;
	          flags.appendChild(node);
	        });
        const toggle = document.createElement("button");
        toggle.className = "secondary";
        toggle.type = "button";
        toggle.textContent = "Detail";
        const detail = document.createElement("div");
        detail.className = "project-detail hidden";
        appendProjectDetail(detail, "Naposledy práce", project.last_worked || "");
        (project.detail_fields || []).forEach((field) => {
          appendProjectDetail(detail, field.label || "", field.value || "");
        });
        toggle.addEventListener("click", () => {
          const hidden = detail.classList.toggle("hidden");
          toggle.textContent = hidden ? "Detail" : "Sbalit";
        });
        const actions = document.createElement("div");
        actions.className = "project-flags";
        actions.appendChild(toggle);
        if (project.category === "project") {
          const lifecycleButton = document.createElement("button");
          lifecycleButton.className = "secondary";
          lifecycleButton.type = "button";
          const archived = (project.lifecycle || "active") === "archived";
          lifecycleButton.textContent = archived ? "Obnovit" : "Archivovat";
          lifecycleButton.addEventListener("click", () => {
            setProjectLifecycle(project, archived ? "active" : "archived", lifecycleButton);
          });
          actions.appendChild(lifecycleButton);
        }
        card.appendChild(head);
	        card.appendChild(status);
	        card.appendChild(next);
	        if (management.textContent) card.appendChild(management);
	        if (project.lifecycle_label || (project.flags || []).length || (project.management_flags || []).length) card.appendChild(flags);
        card.appendChild(actions);
        card.appendChild(detail);
        projectsList.appendChild(card);
      });
    }

    async function setProjectLifecycle(project, lifecycle, button) {
      const name = project.name || "";
      if (!name) return;
      const archive = lifecycle === "archived";
      const ok = window.confirm(
        `${archive ? "Archivovat" : "Obnovit"} projekt?\n\n${name}\n\n` +
        "Akce pouze změní sloupec Rezim v ACTIVE_PROJECTS.md a před změnou vytvoří lokální zálohu."
      );
      if (!ok) return;
      const originalText = button ? button.textContent : "";
      if (button) button.disabled = true;
      if (button) button.textContent = "Ukládám...";
      projectsStatus.textContent = archive ? "Archivuji projekt..." : "Obnovuji projekt...";
      try {
        const data = await postJson("/api/projects/lifecycle", {
          project_name: name,
          lifecycle,
          confirmed: true
        });
        if (!data.ok) {
          projectsStatus.textContent = data.message || "Změna režimu projektu se nepodařila.";
          return;
        }
        const status = data.projects_status || {};
        currentProjects = status.items || status.projects || [];
        renderProjects(currentProjects, currentProjectFilter);
        renderProjectsStatusLine(status);
        refreshProjectsSummary();
      } catch (err) {
        recordFrontendError(err);
        projectsStatus.textContent = `Chyba změny režimu projektu: ${err}`;
      } finally {
        if (button) button.disabled = false;
        if (button) button.textContent = originalText || (archive ? "Archivovat" : "Obnovit");
      }
    }

    function appendProjectDetail(parent, label, value) {
      if (!value) return;
      const row = document.createElement("div");
      row.className = "project-meta";
      row.textContent = `${label}: ${value}`;
      parent.appendChild(row);
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
      maybeReturnToJanicka("reminders");
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
          const amount = item.amount_due ? ` | částka ${item.amount_due}` : "";
          meta.textContent = `${due}${amount} | priorita ${item.priority || "nezadaná"} | zdroj ${item.source_type || "nezadaný"}`;
          const amountNote = document.createElement("div");
          amountNote.className = "reminder-meta";
          amountNote.textContent = item.amount_note || "";
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
          if (item.amount_note) card.appendChild(amountNote);
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
          const amount = item.amount_due ? ` | částka ${item.amount_due}` : "";
          summary.textContent = `${item.title || item.id || "Připomínka"} | deadline ${item.due_date || "bez data"}${amount} | zdroj ${item.source_type || "nezadaný"}`;
          const amountNote = document.createElement("div");
          amountNote.className = "reminder-meta";
          amountNote.textContent = item.amount_note || "";
          const note = document.createElement("div");
          note.className = "reminder-meta";
          note.textContent = item.conflict_note || "";
          const sourceBtn = document.createElement("button");
          sourceBtn.type = "button";
          sourceBtn.className = "secondary";
          sourceBtn.textContent = "Zdroj";
          sourceBtn.disabled = !item.reminder_ref;
          const cancelBtn = document.createElement("button");
          cancelBtn.type = "button";
          cancelBtn.className = "secondary";
          cancelBtn.textContent = "Uzavřít jako zrušené";
          cancelBtn.disabled = !item.reminder_ref;
          const detail = document.createElement("div");
          detail.className = "reminder-source hidden";
          sourceBtn.addEventListener("click", () => loadReminderSource(item.reminder_ref || "", detail, sourceBtn));
          cancelBtn.addEventListener("click", () => cancelPaymentReminder(item.reminder_ref || "", cancelBtn));
          row.appendChild(summary);
          if (item.amount_note) row.appendChild(amountNote);
          if (item.conflict_note) row.appendChild(note);
          row.appendChild(sourceBtn);
          row.appendChild(cancelBtn);
          row.appendChild(detail);
          box.appendChild(row);
        });
        remindersList.appendChild(box);
      });
    }

    async function cancelPaymentReminder(reminderId, button) {
      if (!reminderId) return;
      const confirmed = window.confirm(
        "Uzavřít tuto platební připomínku jako zrušenou? Jako důkaz se připojí poslední uložený e-mail z EmailArchiveVault."
      );
      if (!confirmed) return;
      const originalText = button ? button.textContent : "";
      if (button) {
        button.disabled = true;
        button.textContent = "Uzavírám...";
      }
      remindersStatus.textContent = "Uzavírám připomínku a připojuji e-mailový důkaz...";
      try {
        const result = await postJson("/api/reminders/cancel-payment", {
          reminder_id: reminderId,
          evidence_archive_id: "latest",
          reason: "Pojišťovna akceptovala odstoupení od duplicitní nebo nevýhodné smlouvy."
        });
        remindersStatus.textContent = result.message || (result.ok ? "Připomínka byla uzavřena." : "Připomínku se nepodařilo uzavřít.");
        if (result.reminders) renderReminders(result.reminders);
        await refresh({silent: true, includeSecondary: false});
      } catch (err) {
        remindersStatus.textContent = `Chyba uzavření připomínky: ${err}`;
        if (button) {
          button.disabled = false;
          button.textContent = originalText || "Uzavřít jako zrušené";
        }
      }
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
      if ((result.kind === "email" || result.kind === "email_archive") && result.email) {
        renderReminderEmailSource(result.email, detailNode, result.kind);
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

    function renderReminderEmailSource(email, detailNode, kind = "email") {
      const isArchive = kind === "email_archive" || email.provider === "archive";
      appendSourceRow(detailNode, isArchive ? "Uložený e-mail" : "Předmět", email.subject || "");
      appendSourceRow(detailNode, "Od", email.sender || "");
      appendSourceRow(detailNode, "Datum", email.date || "");
      const sourceText = isArchive
        ? `EmailArchiveVault / ${email.uid || ""}`
        : `${email.provider || ""} / ${email.folder || ""} / UID ${email.uid || ""}`;
      appendSourceRow(detailNode, "Zdroj", sourceText);
      appendSourcePre(detailNode, email.body_text || "");
      const attachments = email.attachments || [];
      if (attachments.length) {
        appendSourceRow(
          detailNode,
          "Přílohy",
          attachments.map((item) => `${item.filename || "(bez názvu)"} | ${item.content_type || ""} | ${item.size_bytes || 0} B${item.stored_path ? " | " + item.stored_path : ""}`).join("; ")
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
      const paymentOptions = documentInfo.payment_options || [];
      if (paymentOptions.length) {
        appendSourceRow(
          detailNode,
          "Platební varianty",
          paymentOptions.map((item) => `${item.label || "Varianta"}: ${item.amount || ""}`).join("; ")
        );
        paymentOptions.forEach((item) => {
          if (item.note) appendSourceRow(detailNode, item.label || "Varianta", item.note);
        });
      }
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

    function openReminderDocument(documentId, button) {
      openDocumentReaderWindow(documentId, remindersStatus, button);
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

    async function markUrgentReminderDone(reminderNumber, button) {
      if (!reminderNumber) return;
      if (!window.confirm("Označit toto důležité připomenutí jako splněné?")) {
        return;
      }
      button.disabled = true;
      urgentRemindersStatus.textContent = "Označuji důležité připomenutí jako splněné...";
      try {
        const result = await postJson("/api/urgent-reminders/done", {reminder_number: reminderNumber});
        if (result.urgent_reminders) {
          renderUrgentReminders(result.urgent_reminders);
          renderUrgentReminderAlert(result.urgent_reminders);
        }
        urgentRemindersStatus.textContent = result.message || "Hotovo.";
        await refresh({silent: true, includeSecondary: false});
      } catch (err) {
        urgentRemindersStatus.textContent = `Chyba uložení důležité připomínky: ${err}`;
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

    function openJanickaModal() {
      janickaReturnBtn.classList.add("hidden");
      janickaModal.classList.remove("hidden");
    }

    function closeJanickaModal() {
      janickaModal.classList.add("hidden");
    }

    let janickaReturnModal = "";

    function armJanickaModalReturn(modalName) {
      janickaReturnModal = modalName || "";
    }

    function maybeReturnToJanicka(modalName) {
      if (janickaReturnModal !== modalName) return;
      janickaReturnModal = "";
      window.setTimeout(openJanickaModal, 0);
    }

    function showJanickaReturnButton() {
      janickaReturnBtn.classList.remove("hidden");
    }

    function focusDocumentSearchForJanicka(message) {
      closeJanickaModal();
      showJanickaReturnButton();
      documentSearchInput.scrollIntoView({behavior: "smooth", block: "center"});
      documentSearchInput.focus();
      if (message) {
        documentSearchStatus.textContent = message;
      }
    }

    function focusAdamForJanicka() {
      closeJanickaModal();
      openJanickaChatModal();
    }

    let janickaChatHistory = [];

    function openJanickaChatModal() {
      janickaReturnBtn.classList.add("hidden");
      janickaChatModal.classList.remove("hidden");
      if (!janickaChatHistory.length) {
        renderJanickaChat();
      }
      refreshJanickaAdamStatus();
      window.setTimeout(() => janickaChatInput.focus(), 0);
    }

    function closeJanickaChatModal() {
      janickaChatModal.classList.add("hidden");
      openJanickaModal();
    }

    function renderJanickaChat() {
      janickaChatLog.innerHTML = "";
      if (!janickaChatHistory.length) {
        const empty = document.createElement("div");
        empty.className = "janicka-chat-message assistant";
        empty.innerHTML = '<div class="janicka-chat-meta">Adam</div>Napiš mi běžnou větou, co potřebuješ. Nejde o hlasový pokyn a nic se samo neprovede.';
        janickaChatLog.appendChild(empty);
        return;
      }
      janickaChatHistory.forEach((item) => {
        const row = document.createElement("div");
        row.className = `janicka-chat-message ${item.role === "user" ? "user" : "assistant"}`;
        const meta = document.createElement("div");
        meta.className = "janicka-chat-meta";
        meta.textContent = item.role === "user" ? "Jana" : "Adam";
        const text = document.createElement("div");
        text.textContent = item.content || "";
        row.appendChild(meta);
        row.appendChild(text);
        janickaChatLog.appendChild(row);
      });
      janickaChatLog.scrollTop = janickaChatLog.scrollHeight;
    }

    async function submitJanickaChat() {
      const message = janickaChatInput.value.trim();
      if (!message) {
        janickaChatStatus.textContent = "Napiš otázku nebo pokyn.";
        janickaChatInput.focus();
        return;
      }
      janickaChatHistory.push({role: "user", content: message});
      janickaChatInput.value = "";
      renderJanickaChat();
      janickaChatSendBtn.disabled = true;
      janickaChatStatus.textContent = "Předávám dotaz Adamovi do Codexu...";
      try {
        const data = await postJson("/api/janicka/chat", {
          message,
          history: janickaChatHistory.slice(-10)
        });
        if (data.ok) {
          janickaChatHistory.push({role: "assistant", content: data.answer || ""});
          janickaChatStatus.textContent = data.message || "Adam odpověděl.";
          if (data.status === "delivered_to_codex" && data.poll_latest) {
            renderJanickaChat();
            pollJanickaCodexReply(message, data.request_id || "");
            return;
          }
          if (data.status === "delivered_to_adam" && data.poll_latest) {
            renderJanickaChat();
            pollJanickaCodexReply(message, data.request_id || "");
            refreshJanickaAdamStatus();
            return;
          }
        } else {
          janickaChatHistory.push({role: "assistant", content: data.message || "Adam teď neodpověděl."});
          janickaChatStatus.textContent = data.message || "Adam teď neodpověděl.";
        }
        renderJanickaChat();
      } catch (err) {
        recordFrontendError(err);
        janickaChatHistory.push({role: "assistant", content: `Adam teď neodpověděl: ${err}`});
        janickaChatStatus.textContent = `Adam teď neodpověděl: ${err}`;
        renderJanickaChat();
      } finally {
        janickaChatSendBtn.disabled = false;
        janickaChatInput.focus();
      }
    }

    async function pollJanickaCodexReply(message, requestId) {
      const maxAttempts = 60;
      const delayMs = 2000;
      for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, delayMs));
        try {
          const data = await postJson("/api/janicka/chat/latest", {message, request_id: requestId});
          if (data.ok && data.available && data.answer) {
            janickaChatHistory.push({role: "assistant", content: data.answer});
            janickaChatStatus.textContent = "Adamova odpověď z Codexu je tady.";
            renderJanickaChat();
            return;
          }
        } catch (err) {
          recordFrontendError(err);
        }
      }
      janickaChatStatus.textContent = "Odpověď se zatím nevrátila do okna. Zkontroluj hlavní Codex chat.";
    }

    async function refreshJanickaAdamStatus() {
      try {
        const data = await postJson("/api/adam/status", {});
        const running = Boolean(data.running);
        const marker = data.marked_tty ? ` Cíl: ${data.marked_tty}.` : "";
        const pending = Number(data.pending_count || 0);
        janickaAdamStatus.textContent = `${data.message || "Adam status není dostupný."}${marker}${pending ? ` Čeká ${pending} dotazů.` : ""}`;
        janickaAdamStatus.classList.toggle("ok", running);
        janickaAdamStatus.classList.toggle("warn", !running);
        janickaAdamStartBtn.disabled = running;
      } catch (err) {
        recordFrontendError(err);
        janickaAdamStatus.textContent = `Adam status se nepodařilo načíst: ${err}`;
        janickaAdamStatus.classList.add("warn");
      }
    }

    async function startJanickaAdam() {
      janickaAdamStatus.textContent = "Spouštím Adama...";
      try {
        const data = await postJson("/api/adam/start", {});
        janickaAdamStatus.textContent = data.message || "Adam se spouští.";
        await refreshJanickaAdamStatus();
      } catch (err) {
        recordFrontendError(err);
        janickaAdamStatus.textContent = `Adama se nepodařilo spustit: ${err}`;
      }
    }

    async function restartJanickaAdam() {
      if (!window.confirm("Restartovat Adama? Rozpracovaná odpověď v Codexu se může přerušit.")) return;
      janickaAdamStatus.textContent = "Restartuji Adama...";
      try {
        const data = await postJson("/api/adam/restart", {confirmed: true});
        janickaAdamStatus.textContent = data.message || "Adam se restartuje.";
        await refreshJanickaAdamStatus();
      } catch (err) {
        recordFrontendError(err);
        janickaAdamStatus.textContent = `Adama se nepodařilo restartovat: ${err}`;
      }
    }

    async function stopJanickaAdam() {
      if (!window.confirm("Zastavit Adama? Běžně je lepší ho nechat spuštěného.")) return;
      janickaAdamStatus.textContent = "Zastavuji Adama...";
      try {
        const data = await postJson("/api/adam/stop", {confirmed: true});
        janickaAdamStatus.textContent = data.message || "Adam byl zastaven.";
        await refreshJanickaAdamStatus();
      } catch (err) {
        recordFrontendError(err);
        janickaAdamStatus.textContent = `Adama se nepodařilo zastavit: ${err}`;
      }
    }

    function clearJanickaChat() {
      janickaChatHistory = [];
      janickaChatStatus.textContent = "Chat je vyčištěný.";
      renderJanickaChat();
      janickaChatInput.focus();
    }

    async function openCatalogAppById(appId) {
      try {
        const res = await fetch("/api/web-apps");
        const data = await res.json();
        const apps = Array.isArray(data.apps) ? data.apps : [];
        const app = apps.find((item) => item && item.id === appId);
        if (!app) {
          showMessage(`Aplikaci ${appId} se nepodařilo najít v katalogu.`);
          return;
        }
        openWebApp(app);
      } catch (err) {
        recordFrontendError(err);
        showMessage(`Chyba otevření aplikace: ${err}`);
      }
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

    janickaBtn.addEventListener("click", openJanickaModal);
    janickaCloseBtn.addEventListener("click", closeJanickaModal);
    janickaFindDocumentBtn.addEventListener("click", () => focusDocumentSearchForJanicka("Zadej, co chceš najít. Po otevření detailu lze dokument přečíst, otevřít nebo vytisknout."));
    janickaPrintDocumentBtn.addEventListener("click", () => focusDocumentSearchForJanicka("Najdi dokument k tisku a v jeho detailu použij tlačítko Tisknout."));
    janickaEmailBtn.addEventListener("click", () => {
      openEmailProcessing();
    });
    janickaLekarnaBtn.addEventListener("click", () => {
      openCatalogAppById("lekarna");
    });
    janickaFamilyBtn.addEventListener("click", () => {
      openCatalogAppById("family-video-organizer");
    });
    janickaAskAdamBtn.addEventListener("click", focusAdamForJanicka);
    janickaRemindersBtn.addEventListener("click", () => {
      armJanickaModalReturn("reminders");
      closeJanickaModal();
      openRemindersModal();
    });
    janickaRecoveryBtn.addEventListener("click", () => {
      armJanickaModalReturn("recovery");
      closeJanickaModal();
      openRecoveryModal();
    });
    janickaWebAppsBtn.addEventListener("click", () => {
      armJanickaModalReturn("webApps");
      closeJanickaModal();
      openWebAppsModal();
    });
    janickaProjectsBtn.addEventListener("click", () => {
      armJanickaModalReturn("projects");
      closeJanickaModal();
      openProjectsModal();
    });
    janickaCookbookBtn.addEventListener("click", () => {
      const cookbookWindow = window.open(
        "/janicka-kucharka/",
        "SamanthaJanickaCookbook",
        "popup=yes,width=920,height=900,left=160,top=60"
      );
      if (cookbookWindow) {
        cookbookWindow.focus();
      } else {
        window.location.href = "/janicka-kucharka/";
      }
    });
    janickaReturnBtn.addEventListener("click", openJanickaModal);
    janickaChatCloseBtn.addEventListener("click", closeJanickaChatModal);
    janickaChatSendBtn.addEventListener("click", submitJanickaChat);
    janickaChatClearBtn.addEventListener("click", clearJanickaChat);
    janickaAdamStartBtn.addEventListener("click", startJanickaAdam);
    janickaAdamRestartBtn.addEventListener("click", restartJanickaAdam);
    janickaAdamStopBtn.addEventListener("click", stopJanickaAdam);
    janickaChatInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        submitJanickaChat();
      }
    });
    refreshBtn.addEventListener("click", refresh);
    serviceBtn.addEventListener("click", () => {
      servicePanel.open = true;
      servicePanel.scrollIntoView({behavior: "smooth", block: "start"});
    });
    dashboardRefreshBtn.addEventListener("click", refresh);
    dashboardProcessBtn.addEventListener("click", () => openScanDocu(false));
    dashboardReviewBtn.addEventListener("click", () => openScanDocu(true));
	    dashboardTerminalBtn.addEventListener("click", () => postAction("/api/terminal/open", dashboardTerminalBtn));
		    dashboardQuantitativeBtn.addEventListener("click", openQuantitativeModal);
		    dashboardQuickNotesBtn.addEventListener("click", openQuickNotesModal);
    dashboardUrgentRemindersBtn.addEventListener("click", openUrgentRemindersModal);
    urgentReminderAlertBtn.addEventListener("click", openUrgentRemindersModal);
		    dashboardRecoveryBtn.addEventListener("click", openRecoveryModal);
    dashboardDiagnosticsBtn.addEventListener("click", openDiagnosticsModal);
    dashboardOverall.addEventListener("click", openDiagnosticsModal);
    dashboardOverall.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openDiagnosticsModal();
      }
    });
    dashboardRestartBtn.addEventListener("click", restartCockpit);
    dashboardSpeakBtn.addEventListener("click", speakDashboardStatus);
    dashboardSpeakSelectionBtn.addEventListener("pointerdown", captureSelectedSpeechText);
    dashboardSpeakSelectionBtn.addEventListener("mousedown", captureSelectedSpeechText);
    dashboardSpeakSelectionBtn.addEventListener("click", speakSelectedText);
    voiceModeToggleBtn.addEventListener("click", toggleVoiceMode);
    voiceModeStartBtn.addEventListener("click", startVoiceModeWatcher);
    voiceModeStopBtn.addEventListener("click", stopVoiceModeWatcher);
    voiceRecordBtn.addEventListener("click", startVoiceRecording);
    voiceStopBtn.addEventListener("click", stopVoiceRecording);
    voiceTranscriptSendBtn.addEventListener("click", submitVoiceTranscript);
    voiceLastResponseSpeakBtn.addEventListener("click", speakLastAdamResponse);
    voiceApprovalApproveBtn.addEventListener("click", () => submitVoiceApproval("approved"));
    voiceApprovalRejectBtn.addEventListener("click", () => submitVoiceApproval("rejected"));
    voiceBridgeSwitcherActions.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-voice-bridge-tty]");
      if (!button) return;
      setVoiceBridgeMarker(button.dataset.voiceBridgeTty || "", button);
    });
    updateVoiceModeUi();
			    webAppsBtn.addEventListener("click", openWebAppsModal);
    libraryBtn.addEventListener("click", openLibraryModal);
    projectsBtn.addEventListener("click", openProjectsModal);
    reviewReportBtn.addEventListener("click", loadDocumentReviewReport);
    remindersBtn.addEventListener("click", openRemindersModal);
    emailProcessingBtn.addEventListener("click", openEmailProcessing);
	    remindersCloseBtn.addEventListener("click", closeRemindersModal);
		    quickNotesCloseBtn.addEventListener("click", closeQuickNotesModal);
    urgentRemindersCloseBtn.addEventListener("click", closeUrgentRemindersModal);
		    recoveryCloseBtn.addEventListener("click", closeRecoveryModal);
    diagnosticsCloseBtn.addEventListener("click", closeDiagnosticsModal);
		    quantitativeCloseBtn.addEventListener("click", closeQuantitativeModal);
    remindersModal.addEventListener("click", (event) => {
      if (event.target === remindersModal) {
        closeRemindersModal();
      }
    });
    janickaModal.addEventListener("click", (event) => {
      if (event.target === janickaModal) {
        closeJanickaModal();
      }
    });
    janickaChatModal.addEventListener("click", (event) => {
      if (event.target === janickaChatModal) {
        closeJanickaChatModal();
      }
    });
    quantitativeModal.addEventListener("click", (event) => {
      if (event.target === quantitativeModal) {
        closeQuantitativeModal();
      }
    });
    webAppsCloseBtn.addEventListener("click", closeWebAppsModal);
    webAppsModal.addEventListener("click", (event) => {
      if (event.target === webAppsModal) {
        closeWebAppsModal();
      }
    });
    libraryCloseBtn.addEventListener("click", closeLibraryModal);
    libraryArchiveBtn.addEventListener("click", archiveLibraryUrl);
    libraryTextSaveBtn.addEventListener("click", saveLibraryText);
    libraryAttachmentSaveBtn.addEventListener("click", attachLibraryImage);
    libraryArchiveUrlInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        archiveLibraryUrl();
      }
    });
    librarySearchBtn.addEventListener("click", searchLibrary);
    librarySearchInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        searchLibrary();
      }
    });
    document.querySelectorAll("[data-library-category]").forEach((button) => {
      button.addEventListener("click", () => loadLibraryCategory(button.dataset.libraryCategory || "other"));
    });
    libraryModal.addEventListener("click", (event) => {
      if (event.target === libraryModal) {
        closeLibraryModal();
      }
    });
    projectsCloseBtn.addEventListener("click", closeProjectsModal);
    projectsModal.addEventListener("click", (event) => {
      if (event.target === projectsModal) {
        closeProjectsModal();
      }
    });
	    quickNotesModal.addEventListener("click", (event) => {
	      if (event.target === quickNotesModal) {
	        closeQuickNotesModal();
	      }
	    });
    urgentRemindersModal.addEventListener("click", (event) => {
      if (event.target === urgentRemindersModal) {
        closeUrgentRemindersModal();
      }
    });
	    recoveryModal.addEventListener("click", (event) => {
	      if (event.target === recoveryModal) {
	        closeRecoveryModal();
	      }
	    });
    diagnosticsModal.addEventListener("click", (event) => {
      if (event.target === diagnosticsModal) {
        closeDiagnosticsModal();
      }
    });
    document.querySelectorAll("[data-project-filter]").forEach((button) => {
      button.addEventListener("click", () => {
        currentProjectFilter = button.dataset.projectFilter || "all";
        renderProjects(currentProjects, currentProjectFilter);
      });
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !remindersModal.classList.contains("hidden")) {
        closeRemindersModal();
      } else if (event.key === "Escape" && !quantitativeModal.classList.contains("hidden")) {
        closeQuantitativeModal();
      } else if (event.key === "Escape" && !webAppsModal.classList.contains("hidden")) {
        closeWebAppsModal();
      } else if (event.key === "Escape" && !libraryModal.classList.contains("hidden")) {
        closeLibraryModal();
      } else if (event.key === "Escape" && !projectsModal.classList.contains("hidden")) {
        closeProjectsModal();
	      } else if (event.key === "Escape" && !quickNotesModal.classList.contains("hidden")) {
	        closeQuickNotesModal();
      } else if (event.key === "Escape" && !urgentRemindersModal.classList.contains("hidden")) {
        closeUrgentRemindersModal();
		      } else if (event.key === "Escape" && !recoveryModal.classList.contains("hidden")) {
		        closeRecoveryModal();
      } else if (event.key === "Escape" && !diagnosticsModal.classList.contains("hidden")) {
        closeDiagnosticsModal();
		      } else if (event.key === "Escape" && !janickaModal.classList.contains("hidden")) {
		        closeJanickaModal();
		      } else if (event.key === "Escape" && !janickaChatModal.classList.contains("hidden")) {
		        closeJanickaChatModal();
      }
    });
    scanDocuBtn.addEventListener("click", () => openScanDocu(false));
    scanDocuReviewBtn.addEventListener("click", () => openScanDocu(true));
    processNextBtn.addEventListener("click", () => openScanDocu(false));
    reviewNextBtn.addEventListener("click", () => openScanDocu(true));
    documentSearchBtn.addEventListener("click", searchDocuments);
	    documentSearchInput.addEventListener("keydown", (event) => {
	      if (event.key === "Enter") {
	        event.preventDefault();
	        searchDocuments();
	      }
	    });
	    runFrontendHealthCheck();
	    window.setInterval(runFrontendHealthCheck, 60000);
	    window.setInterval(() => refresh({silent: true, includeSecondary: false}), INTAKE_LOCAL_MONITOR_MS);
      window.setInterval(refreshUrgentRemindersSummary, URGENT_REMINDERS_MONITOR_MS);
      window.setInterval(runEmailIntakeMonitor, INTAKE_EMAIL_MONITOR_MS);
      window.addEventListener("focus", () => refreshMainStatusOnReturn());
      window.addEventListener("pageshow", () => refreshMainStatusOnReturn(1000));
      document.addEventListener("visibilitychange", () => refreshMainStatusOnReturn());
	    refresh();
      window.setTimeout(refreshUrgentRemindersSummary, 3000);
      window.setTimeout(runEmailIntakeMonitor, 5000);
	  </script>
</body>
</html>
"""


def run_cockpit_server(host: str = "127.0.0.1", port: int = COCKPIT_PORT) -> None:
    CockpitServer(host=host, port=port).serve()
