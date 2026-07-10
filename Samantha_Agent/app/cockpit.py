from __future__ import annotations

import csv
import errno
import base64
import binascii
import html
import json
import hashlib
import ipaddress
import mimetypes
import os
import re
import shutil
import signal
import subprocess
import tempfile
import threading
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

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional local convenience dependency
    def load_dotenv(*_args: object, **_kwargs: object) -> bool:
        return False

from app.adam_service import (
    ADAM_SERVICE_SESSION,
    JANICKA_LIGHT_SESSION,
    adam_service_status,
    deliver_prompt_to_adam_screen,
    discover_managed_adam_codex_ttys,
    janicka_light_status,
    load_adam_text_reply,
    restart_adam_service,
    start_adam_service,
    start_janicka_light_session,
    stop_adam_service,
    stop_janicka_light_session,
    submit_janicka_text_request,
    wait_for_adam_ready,
)
from app.article_archive import (
    ATTACHMENT_CONFIRMATION_PHRASE,
    LIBRARY_EXPORT_EMAIL_MARKER,
    LIBRARY_EXPORT_SUBJECT_PREFIX,
    archive_text_entry,
    archive_url,
    delete_article,
    get_article,
    get_article_attachment,
    attach_article_image,
    list_articles,
    prepare_article_pdf_export,
    search_articles,
    send_article_pdf_export,
    set_article_read_state,
)
from app.autosave_service import (
    SESSION_AUTOSAVE_DIR,
    autosave_runtime_dict as cockpit_autosave_runtime_dict,
    latest_autosave_metadata,
    session_autosave_cleanup_action,
)
from app.backup.activity_state import backup_activity_status
from app.documents.consistency_audit import format_document_consistency_audit, run_document_consistency_audit, save_audit_decision
from app.documents.scandocu import DEFAULT_DOWNLOADS_DIR, reviewed_document_ids, scan_downloads_for_pdfs
from app.documents.transactions import (
    DocumentRecordMutation,
    DocumentRecordNotFoundError,
    DocumentTransactionError,
    transact_document_record,
)
from app.documents.vault import (
    DEFAULT_DOCUMENTS_DIR,
    DEFAULT_MOBILE_DOCUMENT_INBOX,
    PROJECT_ROOT,
    apply_document_import_file,
    build_snippet,
    document_vault_status_summary,
    append_jsonl,
    is_pdf_encrypted,
    next_available_path,
    normalize_domain,
    prepare_document_print_job,
    propose_metadata,
    read_jsonl,
    read_json_file,
    relative_to_project,
    run_document_print_job,
    safe_ascii_slug,
    safe_filename,
    safe_text,
    safe_slug,
    sanitize_output,
    save_document_due_reminder_summary,
    tokenize,
    write_json,
    write_jsonl,
)
from app.lekarna.auto_import import (
    OPENAI_DRAFT_CONFIRMATION_PHRASE,
    apply_auto_import_manifest_from_downloads,
    build_auto_import_draft,
)
from app.lekarna.download_intake import find_recent_download_photos
from app.lekarna.openai_vision import DEFAULT_OPENAI_VISION_MODEL
from app.lekarna.photo_import import APPLY_CONFIRMATION_PHRASE
from app.lekarna.photo_import import MANIFEST_FIELD_NAMES as LEKARNA_MANIFEST_FIELD_NAMES
from app.lekarna.service import (
    RETIRE_CONFIRMATION_PHRASE,
    format_domaci_lek_retire_preview,
    format_retire_domaci_lek,
    search_domaci_leky_records,
)
from app.lekarna.sukl_pil_archive import build_pil_short_from_text, resolve_sukl_pil_document
from app.lekarna.web_bundle import refresh_lekarna_web_bundle
from app.quantitative_status import DEFAULT_METRICS_PATH as QUANTITATIVE_STATUS_METRICS_PATH
from app.quantitative_status import ExtensionStats as QuantitativeExtensionStats
from app.quantitative_status import run_samantha_quantitative_status
from app.project_audit_report import REPORTS_DIR as PROJECT_AUDIT_REPORTS_DIR
from app.project_audit_report import format_project_audit_result, run_samantha_project_audit
from app.quick_notes import DEFAULT_ICLOUD_SHORTCUTS_INBOX, DEFAULT_INDEX_PATH as QUICK_NOTES_INDEX_PATH
from app.quick_notes import ACTION_KIND_LABELS, classify_quick_note_text
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
from app.file_persistence import FilePersistenceError, append_jsonl_locked
from app.cockpit_code_stamp import cockpit_code_stamp
from app.cockpit_status_service import (
    LIVE_STATUS_BRIDGE_CACHE_TTL_SECONDS,
    CockpitStatusLoaders,
    build_cockpit_live_status,
    build_cockpit_status,
    build_server_health_status,
)
from app.reminders.query_tools import mark_reminder_done_text
from app.reminders.store import (
    DEFAULT_REMINDERS_PATH,
    cancel_reminder_record,
    enrich_reminder_record,
    load_reminders_store,
    save_reminder_draft,
)
from app.speech import SpeechError, TranscriptionError, speak_text
from app.speech.transcribe import MIME_EXTENSIONS, decode_audio_base64, normalize_mime_type
from app.speech.edge_tts_mp3 import (
    DEFAULT_EDGE_TTS_RATE,
    DEFAULT_EDGE_TTS_VOICE,
    EdgeTtsError,
    synthesize_edge_tts_mp3_sync,
)
from app.speech.local_tts import DEFAULT_VOICE
from app.speech.adam_voice_mode import (
    ADAM_LAST_RESPONSE_PATH,
    ADAM_PENDING_COMMAND_PATH,
    ADAM_VOICE_HISTORY_PATH,
    append_voice_history_turn,
    clear_codex_approval_request,
    load_voice_mode_status,
    load_last_adam_response,
    pid_exists,
    save_pending_for_adam,
    update_pending_approval,
    write_voice_mode_status,
)
from app.speech.terminal_bridge import (
    CURRENT_CODEX_TTY_PATH,
    assess_terminal_bridge,
    build_codex_terminal_prompt,
    deliver_voice_command_to_terminal,
    discover_codex_ttys,
    normalize_tty,
)
from app.speech.voice_inbox import VoiceCommand, parse_voice_command_file, voice_command_to_dict
from scripts.autosave_status import autosave_status as read_autosave_runtime_status


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COCKPIT_PORT = 8770
COCKPIT_URL = f"http://127.0.0.1:{COCKPIT_PORT}"
DEFAULT_PURCHASES_DIR = PROJECT_ROOT / "data" / "private" / "purchases"
SCANDOCU_URL = "http://127.0.0.1:8766"
SCANDOCU_PORT = 8766
SCANDOCU_LOG_DIR = PROJECT_ROOT / "data" / "private" / "documents" / "scandocu"
SCANDOCU_LOG_FILE = SCANDOCU_LOG_DIR / "server.log"
SCANDOCU_SERVER_SCRIPT = PROJECT_ROOT / "scripts" / "scandocu_server.py"
COCKPIT_RESTART_SCRIPT = PROJECT_ROOT / "scripts" / "restart_cockpit.py"
ADAM_VOICE_MODE_SCRIPT = PROJECT_ROOT / "scripts" / "adam_voice_mode.py"
ADAM_VOICE_MODE_LOG_FILE = PROJECT_ROOT / "data" / "private" / "voice_inbox" / "adam_voice_mode.log"
VOICE_FRONTEND_EVENTS_PATH = PROJECT_ROOT / "data" / "private" / "voice_inbox" / "frontend_events.jsonl"
VOICE_DELIVERY_TRANSPORT_ENV = "ADAM_VOICE_TRANSPORT"
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
VOICE_COMMAND_INBOX_DIR = PROJECT_ROOT / "data" / "private" / "voice_inbox"
MEMORY_INDEX_PATH = PROJECT_ROOT / "memory" / "MEMORY_INDEX.md"
RECOVERY_HANDOFF_PATHS = (
    PROJECT_ROOT / "memory" / "handoffs" / "cockpit_recovery_center_priority_2026_06_03.md",
    PROJECT_ROOT / "memory" / "handoffs" / "cockpit_development_priorities_2026_06_03.md",
)
LOCAL_WEB_APPS = {
    "family-video-organizer": PROJECT_ROOT / "docs" / "family-video-organizer",
}
DESKTOP_APP_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "id": "vocabulary-it-trainer",
        "title": "Vocabulary IT trainer",
        "description": "Desktopový italský slovníkový trenažér s obrázky a lokálními CSV daty.",
        "kind": "desktopová aplikace",
        "working_dir": GIT_ROOT / "VocabularyIT",
        "script": GIT_ROOT / "VocabularyIT" / "vocab_trainer_it.py",
    },
    {
        "id": "vocabulary-fr-trainer",
        "title": "Vocabulary FR trainer",
        "description": "Desktopový francouzský slovníkový trenažér s obrázky a lokálními CSV daty.",
        "kind": "desktopová aplikace",
        "working_dir": GIT_ROOT / "VocabularyFR",
        "script": GIT_ROOT / "VocabularyFR" / "vocab_trainer_fr.py",
    },
)
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
        "id": "email-archive",
        "title": "Archiv e-mailů",
        "description": "Read-only prohlížeč lokálně uložených e-mailů z EmailArchiveVault.",
        "url": "/email-archive/",
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
        "id": "lekarna-admin",
        "title": "Lékárna - správa",
        "description": "Lokální bezpečná správa položek v domácí lékárně včetně potvrzovaného vyřazení a importu fotek.",
        "url": "/lekarna-admin/",
        "kind": "lokální",
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
        "id": "vocabulary-it-trainer",
        "title": "Vocabulary IT trainer",
        "description": "Desktopový italský slovníkový trenažér s obrázky a lokálními CSV daty.",
        "url": "",
        "kind": "desktopová aplikace",
        "launch_type": "desktop",
    },
    {
        "id": "vocabulary-fr-trainer",
        "title": "Vocabulary FR trainer",
        "description": "Desktopový francouzský slovníkový trenažér s obrázky a lokálními CSV daty.",
        "url": "",
        "kind": "desktopová aplikace",
        "launch_type": "desktop",
    },
    {
        "id": "family-video-organizer",
        "title": "Family Video Organizer",
        "description": "Lokální prototyp pro třídění rodinných videí, výběr záběrů a přípravu podkladů pro sestřih.",
        "url": "/local-apps/family-video-organizer/",
        "kind": "lokální prototyp",
    },
)


COCKPIT_CODE_STAMP = cockpit_code_stamp()
MAX_JSON_BODY_BYTES = 10 * 1024 * 1024
COCKPIT_HTTP_EVENT_LOG = PROJECT_ROOT / "data" / "private" / "cockpit" / "http_events.jsonl"
_COCKPIT_HTTP_EVENT_LOG_LOCK = threading.Lock()
TAILSCALE_IPV4_NETWORK = ipaddress.ip_network("100.64.0.0/10")
TAILSCALE_IPV6_NETWORK = ipaddress.ip_network("fd7a:115c:a1e0::/48")
COCKPIT_SECURITY_HEADERS: tuple[tuple[str, str], ...] = (
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "SAMEORIGIN"),
    ("Referrer-Policy", "no-referrer"),
    ("Cross-Origin-Resource-Policy", "same-origin"),
    ("Permissions-Policy", "camera=(), geolocation=(), microphone=(self)"),
    (
        "Content-Security-Policy",
        "default-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'self'; "
        "script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; media-src 'self' data: blob:; connect-src 'self'; "
        "frame-src 'self'; form-action 'self'",
    ),
)


class CockpitHttpError(RuntimeError):
    def __init__(
        self,
        *,
        status: HTTPStatus,
        error: str,
        message: str,
        close_connection: bool = False,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.error = error
        self.message = message
        self.close_connection = close_connection


def cockpit_request_hostname(host_header: str) -> str:
    raw = str(host_header or "").strip()
    if not raw or any(character in raw for character in ("/", "\\", "\r", "\n")):
        return ""
    try:
        return str(urlparse(f"//{raw}").hostname or "").rstrip(".").casefold()
    except ValueError:
        return ""


def cockpit_host_is_allowed(host_header: str) -> bool:
    hostname = cockpit_request_hostname(host_header)
    if not hostname:
        return False
    if hostname in {"localhost", "127.0.0.1", "::1"} or hostname.endswith(".ts.net"):
        return True
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return False
    return bool(
        address.is_loopback
        or (address.version == 4 and address in TAILSCALE_IPV4_NETWORK)
        or (address.version == 6 and address in TAILSCALE_IPV6_NETWORK)
    )


def cockpit_origin_matches_host(origin_or_referer: str, host_header: str) -> bool:
    raw = str(origin_or_referer or "").strip()
    if not raw or raw.casefold() == "null":
        return False
    try:
        parsed = urlparse(raw)
    except ValueError:
        return False
    if parsed.scheme.casefold() not in {"http", "https"} or not parsed.netloc:
        return False
    return parsed.netloc.rstrip(".").casefold() == str(host_header or "").strip().rstrip(".").casefold()


def log_cockpit_http_event(
    *,
    event: str,
    method: str,
    request_path: str,
    status: int,
    detail: str = "",
    path: Path = COCKPIT_HTTP_EVENT_LOG,
) -> None:
    try:
        safe_request_path = urlparse(str(request_path or "")).path
    except ValueError:
        safe_request_path = "[invalid-path]"
    record = {
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "event": safe_text(event)[:80],
        "method": safe_text(method).upper()[:12],
        "path": safe_text(safe_request_path)[:240],
        "status": int(status),
        "detail": safe_text(detail)[:120],
    }
    try:
        with _COCKPIT_HTTP_EVENT_LOG_LOCK:
            append_jsonl_locked(path, record, sort_keys=True, timeout=0.25)
    except (FilePersistenceError, OSError):
        return

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


def server_health_status(*, host: str = "127.0.0.1", port: int = COCKPIT_PORT) -> dict[str, Any]:
    return build_server_health_status(code_stamp=COCKPIT_CODE_STAMP, host=host, port=port)


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
DOCUMENT_METADATA_UPDATE_FIELDS: tuple[str, ...] = (
    "domain",
    "document_type",
    "counterparty",
    "related_asset",
    "case_id",
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


def desktop_app_by_id(app_id: str) -> dict[str, Any] | None:
    safe_id = safe_slug(str(app_id or ""), default="", limit=80)
    return {item["id"]: item for item in DESKTOP_APP_CATALOG}.get(safe_id)


def open_desktop_app_action(
    payload: dict[str, Any],
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    app = desktop_app_by_id(str(payload.get("app_id", "")))
    if app is None:
        return {
            "ok": False,
            "status": "unknown_desktop_app",
            "message": "Tahle desktopová aplikace není v Cockpit allowlistu.",
        }
    working_dir = Path(app["working_dir"])
    script_path = Path(app["script"])
    if not working_dir.exists() or not script_path.is_file():
        return {
            "ok": False,
            "status": "missing_app_file",
            "message": f"{app['title']} nejde spustit, chybí lokální soubor aplikace.",
            "app": {key: app[key] for key in ("id", "title", "description", "kind")},
        }
    shell_command = (
        f"cd {shell_quote_for_applescript(str(working_dir))}; "
        f"python3 {shell_quote_for_applescript(str(script_path))}"
    )
    script = (
        'tell application "Terminal"\n'
        "  activate\n"
        f'  do script "{shell_command}"\n'
        "end tell\n"
    )
    try:
        completed = runner(
            ["/usr/bin/osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "ok": False,
            "status": "launch_failed",
            "message": f"{app['title']} se nepodařilo spustit: {exc}",
            "app": {key: app[key] for key in ("id", "title", "description", "kind")},
        }
    detail = completed.stderr.strip() or completed.stdout.strip()
    return {
        "ok": completed.returncode == 0,
        "status": "launched" if completed.returncode == 0 else "launch_failed",
        "message": detail or f"{app['title']} se spouští v novém Terminal okně.",
        "returncode": completed.returncode,
        "app": {key: app[key] for key in ("id", "title", "description", "kind")},
    }


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


def library_delete_article_action(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return delete_article(
            article_id=str(payload.get("article_id", "")),
            user_confirmed=bool(payload.get("user_confirmed")),
            confirmation_text=str(payload.get("confirmation_text", "")),
        )
    except ValueError as exc:
        return {"ok": False, "message": str(exc), "error": "invalid_delete"}
    except OSError as exc:
        return {"ok": False, "message": f"Položku se nepodařilo vyřadit: {exc}", "error": "archive_failed"}


def lekarna_retire_preview_action(payload: dict[str, Any]) -> dict[str, Any]:
    query = str(payload.get("query", "")).strip()
    reason = str(payload.get("reason", "")).strip()
    if not query:
        return {"ok": False, "message": "Zadej název nebo část názvu léku.", "error": "missing_query"}
    try:
        return {
            "ok": True,
            "mode": "preview",
            "confirmation_phrase": RETIRE_CONFIRMATION_PHRASE,
            "message": format_domaci_lek_retire_preview(query=query, reason=reason),
        }
    except OSError as exc:
        return {"ok": False, "message": f"Náhled vyřazení se nepodařilo načíst: {exc}", "error": "preview_failed"}


def lekarna_search_action(query: str, limit: int = 25) -> dict[str, Any]:
    query = str(query or "").strip()
    if not query:
        return {"ok": True, "query": query, "items": [], "message": "Zadej název, potíž nebo část názvu léku."}
    try:
        matches = search_domaci_leky_records(query=query, limit=max(1, min(limit, 50)))
    except OSError as exc:
        return {"ok": False, "message": f"Lékárnu se nepodařilo načíst: {exc}", "error": "search_failed"}
    return {"ok": True, "query": query, "items": [_lekarna_match_to_dict(match) for match in matches]}


def lekarna_retire_apply_action(payload: dict[str, Any]) -> dict[str, Any]:
    query = str(payload.get("query", "")).strip()
    reason = str(payload.get("reason", "")).strip()
    confirmation_text = str(payload.get("confirmation_text", "")).strip()
    if not query:
        return {"ok": False, "message": "Zadej název nebo část názvu léku.", "error": "missing_query"}
    try:
        message = format_retire_domaci_lek(
            query=query,
            reason=reason,
            user_confirmed=bool(payload.get("user_confirmed")),
            confirmation_text=confirmation_text,
        )
        web_publish = refresh_and_publish_lekarna_web_bundle()
        return {
            "ok": True,
            "mode": "apply",
            "message": message,
            **web_publish,
        }
    except ValueError as exc:
        return {
            "ok": False,
            "message": str(exc),
            "error": "invalid_retire_request",
            "confirmation_phrase": RETIRE_CONFIRMATION_PHRASE,
        }
    except OSError as exc:
        return {"ok": False, "message": f"Lék se nepodařilo vyřadit: {exc}", "error": "retire_failed"}


def lekarna_import_photos_status(limit: int = 3) -> dict[str, Any]:
    try:
        safe_limit = max(1, min(int(limit), 25))
    except (TypeError, ValueError):
        safe_limit = 3
    photos = find_recent_download_photos(downloads_dir=Path.home() / "Downloads", limit=safe_limit)
    return {
        "ok": True,
        "photos": [
            {"name": photo.path.name, "bytes": photo.bytes_size, "modified_at": photo.modified_at}
            for photo in photos
        ],
    }


def lekarna_auto_import_draft_action(payload: dict[str, Any]) -> dict[str, Any]:
    backend = str(payload.get("ocr_backend", "openai") or "openai").strip().casefold()
    confirmation_text = str(payload.get("confirmation_text", "") or "").strip()
    if backend == "openai" and OPENAI_DRAFT_CONFIRMATION_PHRASE.casefold() not in confirmation_text.casefold():
        return {
            "ok": False,
            "message": "OpenAI Vision draft odesílá fotky do API a vyžaduje potvrzení.",
            "error": "confirmation_required",
            "confirmation_phrase": OPENAI_DRAFT_CONFIRMATION_PHRASE,
        }
    try:
        limit = max(1, min(int(payload.get("limit", 3) or 3), 10))
    except (TypeError, ValueError):
        limit = 3
    photo_names_payload = payload.get("photo_names", [])
    photo_names = (
        [Path(str(name)).name for name in photo_names_payload if str(name).strip()]
        if isinstance(photo_names_payload, list)
        else []
    )
    try:
        load_dotenv(PROJECT_ROOT / ".env", override=True)
        result = build_auto_import_draft(
            downloads_dir=Path.home() / "Downloads",
            limit=limit,
            photo_names=photo_names,
            ocr_backend=backend,
            ocr_model=str(payload.get("model", DEFAULT_OPENAI_VISION_MODEL) or DEFAULT_OPENAI_VISION_MODEL),
            allow_online_pil_download=True,
        )
    except Exception as exc:
        return {"ok": False, "message": f"Návrh importu se nepodařilo připravit: {exc}", "error": "draft_failed"}
    return {
        "ok": True,
        "message": "Návrh importu z Downloads je připravený.",
        "manifest_path": str(result.manifest_path),
        "report_path": str(result.report_path),
        "photos": result.photos,
        "new_candidates": result.new_candidates,
        "duplicate_existing": result.duplicate_existing,
        "needs_review": result.needs_review,
    }


def publish_lekarna_encrypted_bundle(
    encrypted_bundle_path: Path | None,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    if encrypted_bundle_path is None:
        return {"ok": True, "status": "skipped", "message": "Šifrovaný balíček nebyl vytvořený; publikace přeskočena."}
    git_root = GIT_ROOT.resolve()
    expected_path = (git_root / "docs" / "lekarna" / "encrypted-data" / "lekarna.enc.json").resolve()
    try:
        bundle_path = encrypted_bundle_path.resolve()
    except OSError as exc:
        return {"ok": False, "status": "invalid_path", "message": f"Šifrovaný balíček nejde ověřit: {exc}"}
    if bundle_path != expected_path:
        return {"ok": False, "status": "unexpected_path", "message": "Šifrovaný balíček není na očekávané produkční cestě."}
    if not bundle_path.exists():
        return {"ok": False, "status": "missing_file", "message": "Šifrovaný produkční balíček neexistuje."}

    relative_path = bundle_path.relative_to(git_root)

    def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
        return runner(
            ["/usr/bin/git", "-C", str(git_root), *args],
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )

    try:
        diff = run_git(["diff", "--quiet", "--", str(relative_path)])
        staged_diff = run_git(["diff", "--cached", "--quiet", "--", str(relative_path)])
        if diff.returncode == 0 and staged_diff.returncode == 0:
            return {"ok": True, "status": "no_changes", "message": "Produkční šifrovaný balíček už je beze změny."}
        add = run_git(["add", "--", str(relative_path)])
        if add.returncode != 0:
            return {"ok": False, "status": "git_add_failed", "message": "Balíček se nepodařilo připravit pro commit."}
        commit = run_git(["commit", "--only", "-m", "Update Lekarna encrypted data bundle", "--", str(relative_path)])
        if commit.returncode != 0:
            return {"ok": False, "status": "git_commit_failed", "message": "Balíček se nepodařilo commitnout."}
        push = run_git(["push"])
        if push.returncode != 0:
            return {"ok": False, "status": "git_push_failed", "message": "Balíček je commitnutý lokálně, ale push na GitHub se nepodařil."}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "status": "git_failed", "message": f"Publikace na produkci se nepodařila: {exc}"}

    commit_line = next((line.strip() for line in commit.stdout.splitlines() if line.strip().startswith("[") and "]" in line), "")
    return {
        "ok": True,
        "status": "published",
        "message": "Produkční šifrovaný balíček byl commitnutý a pushnutý.",
        "commit": commit_line,
        "path": str(relative_path),
    }


def refresh_and_publish_lekarna_web_bundle() -> dict[str, Any]:
    refresh = refresh_lekarna_web_bundle()
    publish = publish_lekarna_encrypted_bundle(refresh.encrypted_path)
    return {
        "web_export_path": str(refresh.export_path) if refresh.export_path else "",
        "encrypted_bundle_path": str(refresh.encrypted_path) if refresh.encrypted_path else "",
        "production_publish": publish,
        "warnings": [safe_text(str(warning)) for warning in refresh.warnings],
    }


def lekarna_auto_import_apply_action(payload: dict[str, Any]) -> dict[str, Any]:
    manifest_path = str(payload.get("manifest_path", "") or "").strip()
    confirmation_text = str(payload.get("confirmation_text", "") or "").strip()
    location = str(payload.get("location", "") or "").strip() or "Horní koupelna"
    if not manifest_path:
        return {"ok": False, "message": "Chybí cesta k manifestu z posledního návrhu.", "error": "missing_manifest"}
    if APPLY_CONFIRMATION_PHRASE.casefold() not in confirmation_text.casefold():
        return {
            "ok": False,
            "message": "Přijetí na sklad zapisuje do CSV a vyžaduje potvrzení.",
            "error": "confirmation_required",
            "confirmation_phrase": APPLY_CONFIRMATION_PHRASE,
        }
    try:
        quality_warnings = _lekarna_manifest_quality_warnings(Path(manifest_path), effective_location=location)
    except Exception as exc:
        return {"ok": False, "message": f"Manifest se před příjmem nepodařilo zkontrolovat: {exc}", "error": "manifest_invalid"}
    if quality_warnings:
        return {
            "ok": False,
            "message": "Návrh není připravený k přijetí. Oprav kontrolu návrhu a znovu ji ulož.",
            "error": "manifest_needs_review",
            "warnings": quality_warnings,
        }
    try:
        result = apply_auto_import_manifest_from_downloads(
            manifest_path=Path(manifest_path),
            downloads_dir=Path.home() / "Downloads",
            location=location,
            user_confirmed=True,
            confirmation_text=confirmation_text,
        )
    except Exception as exc:
        return {"ok": False, "message": f"Návrh se nepodařilo přijmout na sklad: {exc}", "error": "apply_failed"}
    publish_result = publish_lekarna_encrypted_bundle(getattr(result, "encrypted_bundle_path", None))
    return {
        "ok": True,
        "message": "Návrh byl přijat na sklad.",
        "copied": result.copied_count,
        "renamed": result.renamed_count,
        "appended": result.appended_count,
        "backup_path": str(result.backup_path),
        "report_path": str(result.report_path),
        "web_export_path": str(result.web_export_path) if getattr(result, "web_export_path", None) else "",
        "encrypted_bundle_path": str(result.encrypted_bundle_path) if getattr(result, "encrypted_bundle_path", None) else "",
        "production_publish": publish_result,
        "warnings": [safe_text(str(warning)) for warning in getattr(result, "warnings", ())],
    }


LEKARNA_MANIFEST_REVIEW_FIELDS = (
    "include",
    "source_file",
    "new_file",
    "nazev",
    "ucinna_latka",
    "forma",
    "sila",
    "kategorie",
    "pouziti",
    "pro_koho",
    "nevhodne_pro_koho",
    "expirace",
    "mnozstvi",
    "umisteni",
    "overeno_z_letaku",
    "stav_obalu",
    "jistota_cteni",
    "nutno_overit",
    "poznamky",
    "PIL_Short",
    "PIL_Source",
    "PIL_Checked_Date",
    "PIL_Match_Status",
    "Search_Tags",
)

LEKARNA_MANIFEST_FIELD_HELP = {
    "include": "ano = tento řádek se přijme na sklad; ne = řádek se přeskočí.",
    "source_file": "Původní název fotky z Downloads. Slouží ke kontrole zdroje.",
    "new_file": "Cílový bezpečný název fotky v Lékárně, například testovaci_roztok_100_ml.jpg.",
    "nazev": "Krátký název léku nebo přípravku tak, jak ho chceš vidět v seznamu.",
    "ucinna_latka": "Účinná látka, pokud je z obalu nebo příbalového letáku jasná. Jinak nech prázdné nebo napiš nezjištěno.",
    "forma": "Léková forma: tablety, kapsle, kapky, sirup, mast, gel, kožní roztok apod.",
    "sila": "Síla nebo koncentrace. Pokud přípravek sílu nemá, napiš nezjištěno nebo věcnou hodnotu z obalu.",
    "kategorie": "Praktická skupina pro hledání, například bolest, rýma, kašel, dezinfekce, doplněk stravy.",
    "pouziti": "Krátce k čemu přípravek obecně je. Ne osobní doporučení, jen věcný účel.",
    "pro_koho": "Pro koho je přípravek obecně vhodný podle obalu nebo letáku, například dospělí.",
    "nevhodne_pro_koho": "Důležitá omezení z obalu nebo letáku. Pokud nejsou známa, napiš nezjištěno.",
    "expirace": "Datum expirace z obalu, ideálně RRRR-MM nebo RRRR-MM-DD. Pokud není čitelné, napiš nečitelná.",
    "mnozstvi": "Kolik toho je nebo kolik kusů se přijímá: například 1 balení, 20 tablet, 100 ml.",
    "umisteni": "Kde doma bude lék uložen. Pokud používáš společné pole Umístění nahoře, může zůstat prázdné.",
    "overeno_z_letaku": "ano/ne podle toho, jestli byl obsah ověřený z příbalové informace nebo jen z fotky obalu.",
    "stav_obalu": "Stav obalu nebo čitelnosti: dobrý, poškozený, neúplný, špatně čitelný.",
    "jistota_cteni": "Jak jisté je čtení z fotky: vysoká, střední, nízká.",
    "nutno_overit": "ano pokud si nejsi jistý názvem, silou, účelem, expirací nebo příbalovým textem.",
    "poznamky": "Krátká interní poznámka k importu. Nepiš sem hesla ani citlivé osobní údaje.",
    "PIL_Short": "Krátký, věcný výtah z příbalové informace: na co přípravek je, hlavní omezení a bezpečné upozornění bez osobního dávkování.",
    "PIL_Source": "Zdroj výtahu: například SÚKL DLP, příbalová informace, fotografie obalu, URL nebo nedohledáno.",
    "PIL_Checked_Date": "Datum kontroly příbalové informace ve formátu RRRR-MM-DD.",
    "PIL_Match_Status": "Stav párování příbalové informace: overeno, overeno_z_dlp, overeno_z_obalu, ceka_na_pil_overeni, nedohledano.",
    "Search_Tags": "Vyhledávací slova oddělená čárkou: název, účel, potíž, účinná látka, běžné překlepy.",
}

LEKARNA_MANIFEST_PLACEHOLDER_VALUES = {"", "nezarazeno", "leky v krabickach - umisteni nezadano"}
LEKARNA_MANIFEST_WEAK_PIL_STATUSES = {"", "ceka_na_pil_overeni", "nedohledano"}


def _safe_lekarna_auto_import_manifest_path(manifest_path: str) -> Path:
    raw_path = str(manifest_path or "").strip()
    if not raw_path:
        raise ValueError("Chybí cesta k manifestu.")
    path = Path(raw_path).expanduser().resolve()
    allowed_dir = (PROJECT_ROOT / "data" / "lekarna" / "photo_imports").resolve()
    try:
        path.relative_to(allowed_dir)
    except ValueError as exc:
        raise ValueError("Manifest musí být ve složce data/lekarna/photo_imports.") from exc
    if not path.name.startswith("lekarna_auto_import_manifest_") or path.suffix.casefold() != ".csv":
        raise ValueError("Manifest nevypadá jako automatický návrh importu Lékárny.")
    return path


def _latest_lekarna_auto_import_manifest_path() -> Path:
    manifest_dir = (PROJECT_ROOT / "data" / "lekarna" / "photo_imports").resolve()
    manifests = sorted(
        manifest_dir.glob("lekarna_auto_import_manifest_*.csv"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not manifests:
        raise ValueError("Nejdřív připrav návrh importu.")
    return _safe_lekarna_auto_import_manifest_path(str(manifests[0]))


def _read_lekarna_manifest_rows(manifest_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not manifest_path.exists():
        raise ValueError(f"Manifest neexistuje: {manifest_path}")
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        missing = sorted(set(LEKARNA_MANIFEST_FIELD_NAMES) - set(fieldnames))
        if missing:
            raise ValueError(f"Manifest nemá povinná pole: {', '.join(missing)}")
        rows = [{field: str(row.get(field, "") or "") for field in fieldnames} for row in reader]
    return fieldnames, rows


def _lekarna_manifest_review(
    rows: list[dict[str, str]],
    *,
    effective_location: str = "",
) -> tuple[list[str], list[dict[str, list[str]]]]:
    included_rows = [
        (row_index, row)
        for row_index, row in enumerate(rows)
        if str(row.get("include", "")).strip().casefold() in {"ano", "yes", "true", "1"}
    ]
    if not included_rows:
        return ["Manifest neobsahuje žádný řádek s include=ano."], [{} for _ in rows]

    warnings: list[str] = []
    row_issues: list[dict[str, list[str]]] = [{} for _ in rows]

    def add_issue(row_index: int, row: dict[str, str], field: str, message: str) -> None:
        label = str(row.get("nazev") or row.get("source_file") or f"řádek {row_index + 1}").strip()
        prefix = f"{label}: "
        warnings.append(f"{prefix}{message}")
        row_issues[row_index].setdefault(field, []).append(message)

    for row_index, row in included_rows:
        for field in ("new_file", "nazev", "forma", "kategorie", "pouziti", "mnozstvi"):
            value = str(row.get(field, "")).strip()
            if not value or value.casefold() in LEKARNA_MANIFEST_PLACEHOLDER_VALUES:
                add_issue(row_index, row, field, f"chybí nebo je neurčené pole `{field}`.")
        if not str(row.get("sila", "")).strip():
            add_issue(
                row_index,
                row,
                "sila",
                "chybí pole `sila`; pokud přípravek sílu nemá, vyplň `nezjisteno` nebo věcnou hodnotu.",
            )
        location = str(row.get("umisteni", "") or "").strip()
        effective = str(effective_location or "").strip()
        if (not location or location.casefold() in LEKARNA_MANIFEST_PLACEHOLDER_VALUES) and not effective:
            add_issue(row_index, row, "umisteni", "chybí konkrétní umístění.")

        pil_short = str(row.get("PIL_Short", "") or "").strip()
        if (
            not pil_short
            or "automaticky inventarni zaznam" in pil_short.casefold()
            or "nejde o plne overeny vytah" in pil_short.casefold()
        ):
            add_issue(
                row_index,
                row,
                "PIL_Short",
                "`PIL_Short` pořád vypadá jako automatický fallback, ne zkontrolovaný stručný výtah.",
            )
        pil_source = str(row.get("PIL_Source", "") or "").strip()
        if not pil_source or "pil zatim nedohledan" in pil_source.casefold():
            add_issue(row_index, row, "PIL_Source", "chybí věcný `PIL_Source`.")
        pil_status = str(row.get("PIL_Match_Status", "") or "").strip().casefold()
        if pil_status in LEKARNA_MANIFEST_WEAK_PIL_STATUSES:
            add_issue(row_index, row, "PIL_Match_Status", "`PIL_Match_Status` není zkontrolovaný.")
        pil_source_lower = pil_source.casefold()
        has_dlp_pil = "sukl dlp" in pil_source_lower and "pil " in pil_source_lower
        has_verified_pil_text = pil_status == "overeno" and (
            "pil dokument" in pil_source_lower or "pil archiv" in pil_source_lower
        )
        if has_dlp_pil and not has_verified_pil_text:
            add_issue(
                row_index,
                row,
                "PIL_Match_Status",
                "DLP uvádí konkrétní PIL dokument; před příjmem musí být stažený a přečtený příbalový leták.",
            )
        if not str(row.get("Search_Tags", "") or "").strip():
            add_issue(row_index, row, "Search_Tags", "chybí `Search_Tags` pro dohledání v Lékárně.")
    return warnings, row_issues


def _lekarna_manifest_quality_warnings(manifest_path: Path, *, effective_location: str = "") -> list[str]:
    _, rows = _read_lekarna_manifest_rows(_safe_lekarna_auto_import_manifest_path(str(manifest_path)))
    warnings, _ = _lekarna_manifest_review(rows, effective_location=effective_location)
    return warnings


def lekarna_import_manifest_load_action(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        raw_manifest_path = str(payload.get("manifest_path", "") or "")
        manifest_path = (
            _safe_lekarna_auto_import_manifest_path(raw_manifest_path)
            if raw_manifest_path.strip()
            else _latest_lekarna_auto_import_manifest_path()
        )
        effective_location = str(payload.get("effective_location", "") or "").strip()
        fieldnames, rows = _read_lekarna_manifest_rows(manifest_path)
    except Exception as exc:
        return {"ok": False, "message": f"Manifest se nepodařilo načíst: {exc}", "error": "manifest_load_failed"}

    review_fields = [field for field in LEKARNA_MANIFEST_REVIEW_FIELDS if field in fieldnames]
    warnings, row_issues = _lekarna_manifest_review(rows, effective_location=effective_location)
    return {
        "ok": True,
        "message": "Manifest načtený ke kontrole." if not warnings else "Manifest načtený. Některá pole je potřeba doplnit.",
        "manifest_path": str(manifest_path),
        "fields": review_fields,
        "field_help": {
            field: safe_text(LEKARNA_MANIFEST_FIELD_HELP.get(field, ""))
            for field in review_fields
        },
        "warnings": [safe_text(warning) for warning in warnings],
        "rows": [
            {field: safe_text(str(row.get(field, ""))) for field in review_fields}
            for row in rows
        ],
        "row_issues": [
            {field: [safe_text(issue) for issue in issues] for field, issues in row_issue.items()}
            for row_issue in row_issues
        ],
    }


def lekarna_import_manifest_save_action(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        manifest_path = _safe_lekarna_auto_import_manifest_path(str(payload.get("manifest_path", "") or ""))
        fieldnames, existing_rows = _read_lekarna_manifest_rows(manifest_path)
        incoming_rows = payload.get("rows", [])
        if not isinstance(incoming_rows, list):
            raise ValueError("Řádky manifestu musí být seznam.")
        if len(incoming_rows) != len(existing_rows):
            raise ValueError("Počet řádků nesouhlasí s manifestem.")

        editable = set(LEKARNA_MANIFEST_REVIEW_FIELDS)
        saved_rows: list[dict[str, str]] = []
        for existing, incoming in zip(existing_rows, incoming_rows, strict=True):
            if not isinstance(incoming, dict):
                raise ValueError("Každý řádek manifestu musí být objekt.")
            row = {field: str(existing.get(field, "") or "") for field in fieldnames}
            for field, value in incoming.items():
                if field in editable and field in fieldnames:
                    row[field] = safe_text(str(value or "")).strip()
            saved_rows.append(row)

        with manifest_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(saved_rows)
    except Exception as exc:
        return {"ok": False, "message": f"Manifest se nepodařilo uložit: {exc}", "error": "manifest_save_failed"}

    included_count = sum(
        1
        for row in saved_rows
        if str(row.get("include", "")).strip().casefold() in {"ano", "yes", "true", "1"}
    )
    warnings, row_issues = _lekarna_manifest_review(
        saved_rows,
        effective_location=str(payload.get("effective_location", "") or "").strip(),
    )
    return {
        "ok": True,
        "message": (
            f"Manifest uložený. Řádky k importu: {included_count}. Ještě je potřeba doplnit zvýrazněná pole."
            if warnings
            else f"Manifest uložený. Řádky k importu: {included_count}. Návrh vypadá připravený k přijetí."
        ),
        "manifest_path": str(manifest_path),
        "rows": len(saved_rows),
        "included": included_count,
        "warnings": [safe_text(warning) for warning in warnings],
        "row_issues": [
            {field: [safe_text(issue) for issue in issues] for field, issues in row_issue.items()}
            for row_issue in row_issues
        ],
    }


def lekarna_import_manifest_retry_pil_action(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        raw_manifest_path = str(payload.get("manifest_path", "") or "")
        manifest_path = (
            _safe_lekarna_auto_import_manifest_path(raw_manifest_path)
            if raw_manifest_path.strip()
            else _latest_lekarna_auto_import_manifest_path()
        )
        effective_location = str(payload.get("effective_location", "") or "").strip()
        fieldnames, rows = _read_lekarna_manifest_rows(manifest_path)
        changed = 0
        attempted = 0
        failed: list[str] = []
        for row in rows:
            if str(row.get("include", "")).strip().casefold() not in {"ano", "yes", "true", "1"}:
                continue
            pil_name = _extract_lekarna_pil_filename(str(row.get("PIL_Source", "") or ""))
            if not pil_name:
                continue
            if str(row.get("PIL_Match_Status", "")).strip().casefold() == "overeno" and "pil dokument" in str(
                row.get("PIL_Source", "")
            ).casefold():
                continue
            attempted += 1
            document = resolve_sukl_pil_document(pil_name, allow_online_download=True)
            if not document:
                failed.append(pil_name)
                continue
            product_name = str(row.get("nazev", "") or Path(pil_name).stem).strip()
            pil_short = build_pil_short_from_text(product_name, document.text)
            if not pil_short:
                failed.append(pil_name)
                continue
            source = str(row.get("PIL_Source", "") or "").strip()
            row["PIL_Short"] = pil_short
            row["PIL_Source"] = (
                f"{source}; PIL dokument {document.source_path.name}; soubor {document.member_name}; "
                f"zdroj {document.source_kind}; extrakce {document.extraction_method}"
            )
            row["PIL_Checked_Date"] = datetime.now().strftime("%Y-%m-%d")
            row["PIL_Match_Status"] = "overeno"
            row["overeno_z_letaku"] = "ano"
            changed += 1

        if changed:
            with manifest_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
    except Exception as exc:
        return {"ok": False, "message": f"PIL se nepodařilo znovu načíst: {exc}", "error": "pil_retry_failed"}

    warnings, row_issues = _lekarna_manifest_review(rows, effective_location=effective_location)
    review_fields = [field for field in LEKARNA_MANIFEST_REVIEW_FIELDS if field in fieldnames]
    return {
        "ok": True,
        "message": (
            f"PIL znovu načtený: opraveno {changed} z {attempted} pokusů."
            if attempted
            else "Není tu žádný neověřený PIL k opakování."
        ),
        "manifest_path": str(manifest_path),
        "changed": changed,
        "attempted": attempted,
        "failed": [safe_text(value) for value in failed],
        "fields": review_fields,
        "field_help": {field: safe_text(LEKARNA_MANIFEST_FIELD_HELP.get(field, "")) for field in review_fields},
        "warnings": [safe_text(warning) for warning in warnings],
        "rows": [{field: safe_text(str(row.get(field, ""))) for field in review_fields} for row in rows],
        "row_issues": [
            {field: [safe_text(issue) for issue in issues] for field, issues in row_issue.items()}
            for row_issue in row_issues
        ],
    }


def _extract_lekarna_pil_filename(source: str) -> str:
    match = re.search(r"\b(PI\d+\.(?:pdf|docx?|rtf|txt))\b", str(source or ""), flags=re.IGNORECASE)
    return match.group(1) if match else ""


def _lekarna_match_to_dict(match: Any) -> dict[str, Any]:
    lek = match.lek
    return {
        "query": safe_text(str(lek.nazev)),
        "nazev": safe_text(str(lek.nazev)),
        "ucinna_latka": safe_text(str(lek.ucinna_latka)),
        "sila": safe_text(str(lek.sila)),
        "forma": safe_text(str(lek.forma)),
        "kategorie": safe_text(str(lek.kategorie)),
        "pouziti": safe_text(str(lek.pouziti)),
        "mnozstvi": safe_text(str(lek.mnozstvi)),
        "umisteni": safe_text(str(lek.umisteni)),
        "expirace": safe_text(str(lek.expirace)),
        "poznamka": safe_text(str(lek.poznamky)),
        "pil_short": safe_text(str(lek.PIL_Short)),
        "zdroj": safe_text(str(lek.zdroj)),
        "score": int(match.score),
        "reasons": [safe_text(str(reason)) for reason in match.reasons],
        "warnings": [safe_text(str(warning)) for warning in match.warnings],
    }


def library_read_state_action(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return set_article_read_state(
            article_id=str(payload.get("article_id", "")),
            read_state=str(payload.get("read_state", "normal")),
            note=str(payload.get("note", "")),
        )
    except ValueError as exc:
        return {"ok": False, "message": str(exc), "error": "invalid_read_state"}
    except OSError as exc:
        return {"ok": False, "message": f"Stav článku se nepodařilo uložit: {exc}", "error": "archive_failed"}


def library_prepare_pdf_export_action(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return prepare_article_pdf_export(
            article_id=str(payload.get("article_id", "")),
            recipient_email=str(payload.get("recipient_email", "")),
        )
    except ValueError as exc:
        return {"ok": False, "message": str(exc), "error": "invalid_export"}
    except OSError as exc:
        return {"ok": False, "message": f"PDF export se nepodařilo připravit: {exc}", "error": "export_failed"}
    except Exception as exc:
        return {"ok": False, "message": f"PDF export se nepodařilo připravit: {exc}", "error": "export_failed"}


def library_send_pdf_export_action(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return send_article_pdf_export(
            export_id=str(payload.get("export_id", "")),
            user_confirmed=bool(payload.get("user_confirmed")),
            confirmation_text=str(payload.get("confirmation_text", "")),
        )
    except ValueError as exc:
        return {"ok": False, "message": str(exc), "error": "invalid_send"}
    except OSError as exc:
        return {"ok": False, "message": f"PDF export se nepodařilo odeslat: {exc}", "error": "send_failed"}
    except Exception as exc:
        return {"ok": False, "message": f"PDF export se nepodařilo odeslat: {exc}", "error": "send_failed"}


def recovery_center_status(
    *,
    autosave_dir: Path = SESSION_AUTOSAVE_DIR,
    active_projects_path: Path = ACTIVE_PROJECTS_PATH,
    memory_index_path: Path = MEMORY_INDEX_PATH,
    handoff_paths: tuple[Path, ...] = RECOVERY_HANDOFF_PATHS,
    git_status: Callable[[], dict[str, Any]] | None = None,
    autosave_runtime_getter: Callable[..., Any] = read_autosave_runtime_status,
) -> dict[str, Any]:
    git = git_status() if git_status is not None else git_status_summary()
    autosave = latest_autosave_metadata(autosave_dir)
    autosave["runtime"] = cockpit_autosave_runtime_dict(
        autosave_runtime_getter(latest_info_path=autosave_dir / "latest_info.txt")
    )
    return {
        "ok": True,
        "message": "Recovery centrum je read-only a nic neprepisuje.",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "autosave": autosave,
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
    classification = classify_quick_note_text(text)
    return {
        "classification": ACTION_KIND_LABELS.get(classification.kind, classification.kind),
        "suggested_next_step": classification.suggested_next_step,
        "sensitive": classification.sensitive,
        "safety_note": "Zobrazit jen bezpečný souhrn v přehledu." if classification.sensitive else "Bez tiché akce; jen návrh klasifikace.",
        "confidence": classification.confidence,
        "risk": classification.risk,
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


def project_audit_report_status(*, mode: str = "quick", save: bool = False) -> dict[str, Any]:
    normalized_mode = mode if mode in {"quick", "full"} else "quick"
    try:
        result = run_samantha_project_audit(mode=normalized_mode, save=save)
    except Exception as exc:  # pragma: no cover - defensive UI boundary
        return {
            "ok": False,
            "message": f"Systémový audit se nepodařilo vygenerovat: {exc}",
            "mode": normalized_mode,
            "saved_path": "",
            "report": "",
        }
    saved_path = str(relative_to_project(result.saved_path)) if result.saved_path else ""
    return {
        "ok": True,
        "message": f"Systémový audit uložen: {saved_path}" if saved_path else "Systémový audit načten.",
        "mode": result.mode,
        "saved_path": saved_path,
        "report": format_project_audit_result(result),
    }


def project_audit_recent_reports(*, limit: int = 5, reports_dir: Path = PROJECT_AUDIT_REPORTS_DIR) -> dict[str, Any]:
    safe_limit = max(1, min(int(limit or 5), 20))
    try:
        paths = sorted(
            reports_dir.glob("systemovy_audit_projekty_tooly_vrstvy_*.txt"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
    except OSError as exc:
        return {"ok": False, "message": f"Nelze nacist ulozene audity: {exc}", "reports": []}
    return {
        "ok": True,
        "message": f"Načteno posledních {min(len(paths), safe_limit)} systémových auditů.",
        "reports": [_project_audit_report_file_summary(path) for path in paths[:safe_limit]],
    }


def project_audit_report_file_status(*, name: str, reports_dir: Path = PROJECT_AUDIT_REPORTS_DIR) -> dict[str, Any]:
    safe_name = Path(str(name or "")).name
    if not safe_name.startswith("systemovy_audit_projekty_tooly_vrstvy_") or not safe_name.endswith(".txt"):
        return {"ok": False, "message": "Neplatny nazev reportu.", "report": "", "name": safe_name}
    path = reports_dir / safe_name
    try:
        resolved = path.resolve()
        if not resolved.is_relative_to(reports_dir.resolve()):
            return {"ok": False, "message": "Report musi byt v adresari memory/reports.", "report": "", "name": safe_name}
        text = resolved.read_text(encoding="utf-8")
    except OSError as exc:
        return {"ok": False, "message": f"Report nelze nacist: {exc}", "report": "", "name": safe_name}
    return {
        "ok": True,
        "message": f"Systémový audit načten: {safe_name}",
        "name": safe_name,
        "path": str(relative_to_project(resolved)),
        "report": text,
    }


def _project_audit_report_file_summary(path: Path) -> dict[str, Any]:
    try:
        stat = path.stat()
        modified_at = datetime.fromtimestamp(stat.st_mtime, timezone.utc).astimezone().isoformat(timespec="seconds")
        size = stat.st_size
    except OSError:
        modified_at = ""
        size = 0
    return {
        "name": path.name,
        "path": str(relative_to_project(path)),
        "modified_at": modified_at,
        "size": size,
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


def email_processing_is_inbound_work_folder(folder: str) -> bool:
    folder_key = " ".join((folder or "INBOX").casefold().split())
    outbound_folders = {
        "sent",
        "sent messages",
        "sent mail",
        "odeslané",
        "odeslane",
        "odeslaná pošta",
        "odeslana posta",
        "outbox",
        "drafts",
        "koncepty",
    }
    return folder_key not in outbound_folders


def email_processing_legacy_item_id(category: str, provider: str, folder: str, uid: str, date: str, subject: str) -> str:
    raw = "|".join([category, provider, folder, uid, date, subject])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def email_processing_item_id(category: str, provider: str, folder: str, uid: str, date: str, subject: str) -> str:
    stable_key = email_processing_stable_key(provider, folder, uid)
    if stable_key:
        return hashlib.sha256(stable_key.encode("utf-8")).hexdigest()[:16]
    return email_processing_legacy_item_id(category, provider, folder, uid, date, subject)


def email_processing_item_lookup_keys(item: dict[str, Any]) -> set[str]:
    keys = {
        str(item.get("id", "")).strip(),
        str(item.get("legacy_id", "")).strip(),
        str(item.get("source_key", "")).strip(),
    }
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
    legacy_id = email_processing_legacy_item_id(
        str(item.get("category", "")),
        str(item.get("provider", "")),
        str(item.get("folder", "")),
        str(item.get("uid", "")),
        str(item.get("date", "")),
        str(item.get("subject", "")),
    )
    if legacy_id:
        keys.add(legacy_id)
    return {key for key in keys if key}


def email_processing_decision_lookup_keys(decisions: dict[str, dict[str, Any]]) -> set[str]:
    keys = set(decisions)
    for decision in decisions.values():
        item = decision.get("item", {})
        if not isinstance(item, dict):
            continue
        keys.update(email_processing_item_lookup_keys(item))
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
    invoice_value = any(
        token in value
        for token in (
            "faktura",
            "invoice",
            "daňový doklad",
            "danovy doklad",
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
    )
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
    if invoice_value:
        return "faktury/e-shopy"
    if any(token in value for token in ("finanční správa", "financni sprava", "daneelektronicky", "fs.mfcr.cz", "fs.gov.cz")):
        return "úřady/daně"
    if any(token in value for token in ("úřad", "urad", "finanční", "financni", "datov", "správa", "sprava")):
        return "úřady/daně"
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
    item["source_key"] = email_processing_stable_key(source, folder, str(header.internal_id))
    item["legacy_id"] = email_processing_legacy_item_id(
        category,
        source,
        folder,
        str(header.internal_id),
        header.date,
        header.subject or "",
    )
    item["samantha_library_export"] = email_processing_item_is_library_export(item)
    return item


def email_processing_item_is_library_export(item: dict[str, Any]) -> bool:
    values = [
        str(item.get("subject", "")),
        str(item.get("reason", "")),
        str(item.get("original_subject", "")),
        str(item.get("headers", "")),
        str(item.get("raw_headers", "")),
    ]
    for key in (LIBRARY_EXPORT_EMAIL_MARKER, "X-Samantha-Article-ID"):
        value = item.get(key)
        if value is not None:
            values.append(str(value))
    for attachment in item.get("attachments", []) if isinstance(item.get("attachments", []), list) else []:
        if isinstance(attachment, dict):
            values.append(str(attachment.get("filename", "")))
            values.append(str(attachment.get("content_type", "")))
    text = " ".join(values).casefold()
    return (
        LIBRARY_EXPORT_SUBJECT_PREFIX.casefold() in text
        or LIBRARY_EXPORT_EMAIL_MARKER.casefold() in text
    )


def document_intake_email_candidate_filter(item: dict[str, Any]) -> dict[str, Any]:
    if email_processing_item_is_library_export(item):
        return {
            "include": False,
            "score": -100,
            "label": "Potlačeno: export Knihovny",
            "reasons": ["PDF export z Knihovny se záměrně neimportuje zpět"],
            "matched_positive": [],
            "matched_negative": [],
        }
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


def email_processing_batch_groups(item: dict[str, Any]) -> list[dict[str, str]]:
    text = " ".join(
        [
            str(item.get("sender", "")),
            str(item.get("subject", "")),
            str(item.get("reason", "")),
            " ".join(str(tag) for tag in (item.get("worklist_tags") or []) if str(tag).strip()),
        ]
    ).casefold()
    category = str(item.get("category", "")).casefold()
    tags = {str(tag).strip() for tag in (item.get("worklist_tags") or []) if str(tag).strip()}
    groups: list[dict[str, str]] = []

    def add(group_id: str, label: str) -> None:
        if not any(group["id"] == group_id for group in groups):
            groups.append({"id": group_id, "label": label})

    if "true_tax_office" in tags or any(
        needle in text for needle in ("daneelektronicky", "fs.mfcr.cz", "fs.gov.cz", "finanční správa")
    ):
        add("tax_office", "Finanční správa")
    if "true_vak" in tags or "vakmb" in text or "vodovod" in text or "kanaliz" in text:
        add("vak", "VAK")
    amount_scan = item.get("amount_scan")
    max_amount = 0.0
    if isinstance(amount_scan, dict):
        try:
            max_amount = float(amount_scan.get("max_amount_czk", 0) or 0)
        except (TypeError, ValueError):
            max_amount = 0.0
    if "invoice_over_2000" in tags or max_amount > 2000:
        add("invoice_over_2000", "Faktury nad 2000 Kč")
    if category == "faktury/e-shopy":
        add("invoice", "Faktury / e-shopy")
    if int(item.get("pdf_attachment_count", 0) or 0) > 0:
        add("pdf", "S PDF přílohou")
    if int(item.get("large_pdf_attachment_count", 0) or 0) > 0:
        add("large_pdf", "Velké PDF")
    if not groups:
        add("other", "Ostatní")
    return groups


def email_processing_pending_work_items(
    path: Path = EMAIL_PROCESSING_DECISIONS_FILE,
) -> dict[str, Any]:
    decisions = read_email_processing_decisions(path)
    items: list[dict[str, Any]] = []
    skipped_outbound_count = 0
    skipped_library_export_count = 0
    for item_id, decision in decisions.items():
        action = str(decision.get("action", ""))
        if action not in {"process", "trash_requested"}:
            continue
        raw_item = decision.get("item", {})
        if not isinstance(raw_item, dict):
            continue
        item = dict(raw_item)
        if not email_processing_is_inbound_work_folder(str(item.get("folder", ""))):
            skipped_outbound_count += 1
            continue
        if email_processing_item_is_library_export(item):
            skipped_library_export_count += 1
            continue
        normalized_category = classify_email_processing_category(
            str(item.get("subject", "")),
            str(item.get("sender", "")),
        )
        if normalized_category != "ostatní" and normalized_category != str(item.get("category", "")):
            item["original_category"] = str(item.get("category", ""))
            item["category"] = normalized_category
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
        batch_groups = email_processing_batch_groups(item)
        item["batch_groups"] = batch_groups
        item["primary_batch_group"] = batch_groups[0]["id"] if batch_groups else "other"
        items.append(item)

    items.sort(key=lambda item: email_header_timestamp(str(item.get("date", ""))), reverse=True)
    message = f"Načteno rozpracovaných e-mailů: {len(items)}."
    if skipped_outbound_count:
        message += f" Skryto odchozích/konceptových položek: {skipped_outbound_count}."
    if skipped_library_export_count:
        message += f" Skryto exportů Knihovny: {skipped_library_export_count}."
    return {
        "ok": True,
        "message": message,
        "items": items,
        "count": len(items),
        "skipped_outbound_count": skipped_outbound_count,
        "skipped_library_export_count": skipped_library_export_count,
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
    suppressed_known_ids = set(known & (decided_keys | completed_keys))
    entries: list[dict[str, Any]] = []
    unavailable: list[str] = []
    skipped_library_export_count = 0
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
            if email_processing_item_is_library_export(item):
                skipped_library_export_count += 1
                continue
            item_keys = email_processing_item_lookup_keys(item)
            blocked_keys = item_keys & (decided_keys | completed_keys)
            known_item_keys = item_keys & known
            if blocked_keys and known_item_keys:
                suppressed_known_ids.update(known_item_keys)
            if item_keys & known or blocked_keys:
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
        "skipped_library_export_count": skipped_library_export_count,
        "suppressed_known_ids": sorted(suppressed_known_ids),
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
    items = [
        item
        for item in parse_email_processing_items(text)
        if not email_processing_item_is_library_export(item)
    ]
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
    required_confirmation = purge_trash_confirmation_phrase(len(safe_items))
    if not confirmed or confirmation_text.strip() != required_confirmation:
        return {
            "ok": True,
            "message": f"Trvalé smazání čeká na přesné potvrzení: {required_confirmation}",
            "required_confirmation": required_confirmation,
            "summary": {"purge_pending": len(safe_items), "purged": 0, "errors": 0},
            "items": [
                {
                    "item_id": safe_text(str(item.get("id") or item.get("item_id") or "")),
                    "provider": safe_text(str(item.get("provider", ""))),
                    "uid": safe_text(str(item.get("uid", ""))),
                    "status": "purge_pending",
                    "ok": True,
                    "required_confirmation": required_confirmation,
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


def purge_trash_confirmation_phrase(count: int) -> str:
    safe_count = max(1, int(count or 1))
    if safe_count == 1:
        noun = "e-mail"
    elif safe_count in {2, 3, 4}:
        noun = "e-maily"
    else:
        noun = "e-mailů"
    return f"Potvrzuji, trvale smaž {safe_count} {noun} z koše."


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
    save_attachment_filenames = {
        safe_text(str(attachment.get("filename", ""))).strip()
        for attachment in item.get("attachment_metadata", item.get("attachments", []))
        if isinstance(attachment, dict)
        and safe_text(str(attachment.get("part_id", ""))).strip() in save_attachment_ids
        and safe_text(str(attachment.get("filename", ""))).strip()
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

    attachment_results = import_selected_email_attachments(
        source=source,
        selected_part_ids=save_attachment_ids,
        documents_dir=documents_dir,
        category=safe_text(str(item.get("category", ""))),
        selected_filenames=save_attachment_filenames,
    )
    clear_email_processing_decision(item_id=item_id, path=decisions_path)
    ok_attachments = [result for result in attachment_results if result.get("ok") and result.get("document_id")]
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
            f"E-mail uložen do EmailArchiveVault; příloh uloženo: {len(ok_attachments)}."
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
    filename: str = "",
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
    safe_filename_hint = safe_text(filename).strip()
    for index, part in enumerate(message.walk() if message.is_multipart() else [message]):
        current_part_id = str(index)
        meta = meta_by_part_id.get(current_part_id)
        part_filename = safe_text(str((meta.filename if meta else part.get_filename()) or "")).strip()
        if not email_attachment_part_matches(
            current_part_id=current_part_id,
            requested_part_id=safe_part_id,
            part_filename=part_filename,
            requested_filename=safe_filename_hint,
        ):
            continue
        filename = safe_filename((meta.filename if meta else part.get_filename()) or f"attachment-{current_part_id}.bin")
        content_type = (meta.content_type if meta else part.get_content_type()) or ""
        if not email_attachment_is_previewable(content_type=content_type, filename=filename):
            return {"ok": False, "part_id": safe_part_id, "filename": safe_text(filename), "message": "Náhled je zatím povolený jen pro PDF a obrázkové přílohy."}
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
            "message": "Příloha otevřena jako dočasný náhled; nebyla uložena do document vaultu.",
            "part_id": safe_part_id,
            "filename": safe_text(filename),
            "preview_path": str(preview_path),
        }

    return {"ok": False, "part_id": safe_part_id, "message": "Vybraná příloha nebyla v e-mailu nalezena."}


def import_selected_email_attachments(
    *,
    source: EmailArchiveSource,
    selected_part_ids: set[str],
    documents_dir: Path,
    category: str,
    selected_filenames: set[str] | None = None,
) -> list[dict[str, Any]]:
    selected_names = {safe_text(name).strip() for name in (selected_filenames or set()) if safe_text(name).strip()}
    if not selected_part_ids and not selected_names:
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
            meta = meta_by_part_id.get(part_id)
            part_filename = safe_text(str((meta.filename if meta else part.get_filename()) or "")).strip()
            matching_requested_ids = {
                requested_id
                for requested_id in selected_part_ids
                if email_attachment_part_matches(
                    current_part_id=part_id,
                    requested_part_id=requested_id,
                    part_filename=part_filename,
                    requested_filename="",
                )
            }
            filename_matched = bool(part_filename and part_filename in selected_names)
            if not matching_requested_ids and not filename_matched:
                continue
            found_part_ids.update(matching_requested_ids)
            if filename_matched:
                found_part_ids.update(selected_part_ids or {part_id})
            filename = safe_filename((meta.filename if meta else part.get_filename()) or f"attachment-{part_id}.pdf")
            content_type = (meta.content_type if meta else part.get_content_type()) or ""
            if not email_attachment_is_storable(content_type=content_type, filename=filename):
                imported.append(
                    {
                        "ok": True,
                        "status": "skipped",
                        "part_id": part_id,
                        "filename": safe_text(filename),
                        "message": "Příloha není PDF ani podporovaný obrázek; pro dávkový import byla přeskočena.",
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
            attachment_kind = email_attachment_storage_kind(content_type=content_type, filename=filename)
            document_type = "email-attachment-image" if attachment_kind == "image" else "email-attachment-pdf"
            tag_kind = "image" if attachment_kind == "image" else "pdf"
            temp_path = temp_root / filename
            temp_path.write_bytes(payload)
            try:
                result = apply_document_import_file(
                    source_path=str(temp_path),
                    target_domain=email_processing_category_to_document_domain(category),
                    document_type=document_type,
                    counterparty=source.sender,
                    tags=f"email,email-attachment,{tag_kind},{source.provider}",
                    case_id=f"email-{source.provider}-{source.uid}",
                    document_title=f"E-mail UID {source.uid} příloha {filename}",
                    reading_status="needs_review",
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


def email_attachment_part_matches(
    *,
    current_part_id: str,
    requested_part_id: str,
    part_filename: str,
    requested_filename: str,
) -> bool:
    if current_part_id == requested_part_id:
        return True
    if requested_filename and part_filename and part_filename == requested_filename:
        return True
    return False


def email_attachment_is_previewable(*, content_type: str, filename: str) -> bool:
    normalized_type = content_type.casefold().strip()
    normalized_name = filename.casefold().strip()
    previewable_extensions = (".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".tif", ".tiff")
    if normalized_type == "application/pdf" or normalized_type.startswith("image/"):
        return True
    return normalized_name.endswith(previewable_extensions)


def email_attachment_is_storable(*, content_type: str, filename: str) -> bool:
    return email_attachment_storage_kind(content_type=content_type, filename=filename) in {"pdf", "image"}


def email_attachment_storage_kind(*, content_type: str, filename: str) -> str:
    normalized_type = content_type.casefold().strip()
    normalized_name = filename.casefold().strip()
    if normalized_type == "application/pdf" or normalized_name.endswith(".pdf"):
        return "pdf"
    if normalized_type.startswith("image/") or normalized_name.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".tif", ".tiff")):
        return "image"
    return ""


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
    loaders = CockpitStatusLoaders(
        downloads=safe_downloads_status,
        document_work=lambda downloads: document_work_status(downloads=downloads),
        document_intake=lambda downloads: document_intake_status(downloads=downloads),
        document_cases=document_cases_status,
        document_classification=document_classification_status,
        document_due_candidates=document_due_candidates_status,
        reminders=reminders_status,
        urgent_reminders=urgent_reminders_status,
        backup_status=backup_activity_status,
        action_queue=lambda document_work, reminders, urgent: action_queue_status(
            document_work=document_work,
            reminders=reminders,
            urgent_reminders=urgent,
        ),
        vault=document_vault_status_summary,
        scandocu=probe_scandocu,
        voice_mode=load_voice_mode_status,
        voice_bridge=lambda: adam_voice_bridge_status(
            orphaned_janicka_reporter=janicka_orphaned_codex_session_report
        ),
        git=git_status_summary,
    )
    return build_cockpit_status(loaders=loaders, code_stamp=COCKPIT_CODE_STAMP)


def cockpit_live_status(
    *,
    voice_mode_loader: Callable[..., dict[str, Any]] | None = None,
    voice_bridge_loader: Callable[[], dict[str, Any]] | None = None,
    monotonic_clock: Callable[[], float] | None = None,
    bridge_cache: dict[str, Any] | None = None,
    bridge_cache_ttl_seconds: float = LIVE_STATUS_BRIDGE_CACHE_TTL_SECONDS,
) -> dict[str, Any]:
    """Return frequently changing voice state without rebuilding the full Cockpit status."""
    load_voice_bridge = voice_bridge_loader or (
        lambda: adam_voice_bridge_status(orphaned_janicka_reporter=janicka_orphaned_codex_session_report)
    )
    return build_cockpit_live_status(
        voice_mode_loader=voice_mode_loader or load_voice_mode_status,
        voice_bridge_loader=load_voice_bridge,
        monotonic_clock=monotonic_clock or time.monotonic,
        bridge_cache=bridge_cache,
        bridge_cache_ttl_seconds=bridge_cache_ttl_seconds,
    )


def adam_voice_bridge_status(
    *,
    marker_path: Path = CURRENT_CODEX_TTY_PATH,
    codex_tty_discoverer: Callable[[], list[str]] = discover_codex_ttys,
    managed_codex_tty_labeler: Callable[[], dict[str, str]] | None = None,
    orphaned_janicka_reporter: Callable[[], dict[str, Any]] | None = None,
    screen_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    marker_pid_checker: Callable[[int], bool] | None = None,
    expected_codex_session_limit: int = 1,
) -> dict[str, Any]:
    marker: dict[str, Any] = {}
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        marker = {}

    marked_tty = normalize_tty(str(marker.get("tty") or ""))
    parent_pid = marker.get("parent_pid")
    marker_parent_pid_active = False
    marker_parent_pid_unverified = False
    if marker_pid_checker is None:
        marker_pid_checker = lambda pid: os.kill(pid, 0) is None
    if isinstance(parent_pid, int) and parent_pid > 0:
        try:
            marker_parent_pid_active = bool(marker_pid_checker(parent_pid))
        except PermissionError:
            marker_parent_pid_unverified = True
        except (OSError, ValueError):
            marker_parent_pid_active = False
    try:
        codex_ttys = [normalize_tty(item) for item in codex_tty_discoverer()]
    except Exception:
        codex_ttys = []
    codex_ttys = [item for item in codex_ttys if item and item != "??"]
    try:
        managed_codex_labels = managed_codex_tty_labeler() if managed_codex_tty_labeler else managed_codex_session_tty_labels()
    except Exception:
        managed_codex_labels = {}
    managed_codex_labels = {
        normalize_tty(str(tty)): safe_text(str(label))[:80]
        for tty, label in managed_codex_labels.items()
        if normalize_tty(str(tty)) in codex_ttys
    }
    managed_codex_ttys = sorted(managed_codex_labels)
    try:
        orphan_report = orphaned_janicka_reporter() if orphaned_janicka_reporter else {}
    except Exception:
        orphan_report = {}
    orphaned_janicka_ttys = sorted(
        {
            normalize_tty(str(tty))
            for tty in orphan_report.get("orphaned_ttys", [])
            if normalize_tty(str(tty)) in codex_ttys and normalize_tty(str(tty)) not in managed_codex_labels
        }
    )
    orphaned_janicka_labels = {tty: "stará Janička mimo správu" for tty in orphaned_janicka_ttys}
    human_codex_ttys = [
        tty
        for tty in codex_ttys
        if tty not in managed_codex_labels and tty not in orphaned_janicka_labels
    ]

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
        if completed.returncode == 0 or "There is a screen on" in screen_output or "samantha_codex" in screen_output:
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

    effective_tty = marked_tty if marked_tty in codex_ttys else ""
    if not effective_tty and marked_tty and len(codex_ttys) == 1:
        effective_tty = codex_ttys[0]
    marker_pid_fallback = False
    if not effective_tty and marked_tty and not codex_ttys and (
        marker_parent_pid_active or (marker_parent_pid_unverified and screen_status == "running")
    ):
        effective_tty = marked_tty
        marker_pid_fallback = True
    mac_bridge_ready = bool(effective_tty)
    warnings: list[str] = []
    notes: list[str] = []
    if not marked_tty:
        warnings.append("není označené cílové TTY")
    elif marked_tty not in codex_ttys:
        if marker_pid_fallback:
            if marker_parent_pid_active:
                warnings.append(
                    f"aktivní Codex relaci nelze ověřit přes ps, ale marker {marked_tty} má živý Codex PID {parent_pid}"
                )
            else:
                warnings.append(
                    f"aktivní Codex relaci nelze ověřit přes ps ani PID kvůli oprávnění, ale screen běží a marker míří na {marked_tty}"
                )
        elif effective_tty:
            warnings.append(f"označené TTY {marked_tty} je staré; použije se jediná aktivní Codex relace {effective_tty}")
        else:
            warnings.append(f"označené TTY {marked_tty} není mezi aktivními Codex relacemi")
    if len(human_codex_ttys) > expected_codex_session_limit:
        warnings.append(f"běží {len(human_codex_ttys)} běžných Codex relací, očekáváno nejvýše {expected_codex_session_limit}")
    if managed_codex_ttys:
        notes.append(
            "spravované relace mimo limit: "
            + ", ".join(f"{tty}={managed_codex_labels[tty]}" for tty in managed_codex_ttys)
        )
    if orphaned_janicka_ttys:
        warnings.append(
            "stará Janička relace mimo správu: "
            + ", ".join(orphaned_janicka_ttys)
            + "; uklidit v okně Janička"
        )
    if screen_status == "not_running":
        notes.append("screen neběží; pro lokální Mac TTY bridge to není blokující")

    target = effective_tty or marked_tty or "nezjištěno"
    marker_label = marked_tty or "nezjištěno"
    readiness = "Mac TTY bridge připravený" if mac_bridge_ready else "Mac TTY bridge není připravený"
    codex_count_label = "neověřeno přes ps" if marker_pid_fallback and not codex_ttys else str(len(human_codex_ttys))
    message = (
        f"{readiness}. Bridge cílí na {target} (marker: {marker_label}). "
        f"Codex relace celkem: {len(codex_ttys)} "
        f"(běžné: {codex_count_label}, limit {expected_codex_session_limit}; "
        f"spravované: {len(managed_codex_ttys)}). {screen_message}."
    )
    if notes:
        message = f"{message} Info: {', '.join(notes)}."
    if warnings:
        message = f"{message} Pozor: {', '.join(warnings)}."

    return {
        "ok": True,
        "status": "warn" if warnings else "ok",
        "message": message,
        "marked_tty": marked_tty,
        "effective_tty": effective_tty,
        "marked_at": str(marker.get("marked_at") or ""),
        "parent_pid": parent_pid,
        "marker_parent_pid_active": marker_parent_pid_active,
        "marker_parent_pid_unverified": marker_parent_pid_unverified,
        "marker_pid_fallback": marker_pid_fallback,
        "mac_bridge_ready": mac_bridge_ready,
        "codex_ttys": codex_ttys,
        "codex_tty_count": len(codex_ttys),
        "human_codex_ttys": human_codex_ttys,
        "human_codex_tty_count": len(human_codex_ttys),
        "managed_codex_ttys": managed_codex_ttys,
        "managed_codex_labels": managed_codex_labels,
        "orphaned_janicka_ttys": orphaned_janicka_ttys,
        "orphaned_janicka_labels": orphaned_janicka_labels,
        "orphaned_janicka_count": len(orphaned_janicka_ttys),
        "codex_tty_count_label": codex_count_label,
        "expected_codex_session_limit": expected_codex_session_limit,
        "screen_status": screen_status,
        "screen_message": screen_message,
        "notes": notes,
        "warnings": warnings,
    }


def managed_codex_session_tty_labels() -> dict[str, str]:
    labels: dict[str, str] = {}
    for session_name, label in (
        (ADAM_SERVICE_SESSION, "Adam managed"),
        (JANICKA_LIGHT_SESSION, "Janička light"),
    ):
        for tty in discover_managed_adam_codex_ttys(session_name=session_name):
            normalized = normalize_tty(tty)
            if normalized:
                labels[normalized] = label
    return labels


CODEX_SESSION_PS_COMMAND = ["ps", "-axo", "pid=,ppid=,tty=,comm=,args="]


def is_codex_cli_process(comm: str, args: str) -> bool:
    folded = f"{comm} {args}".casefold()
    if "app-server" in folded:
        return False
    tokens = [comm, *str(args or "").split()]
    return any(Path(token).name == "codex" for token in tokens if token)


def discover_codex_process_sessions(
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> list[dict[str, Any]]:
    try:
        completed = runner(
            CODEX_SESSION_PS_COMMAND,
            capture_output=True,
            text=True,
            timeout=4,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if completed.returncode != 0:
        return []

    rows: list[dict[str, Any]] = []
    codex_pids: set[int] = set()
    for line in completed.stdout.splitlines():
        parts = line.strip().split(None, 4)
        if len(parts) < 5:
            continue
        pid_text, ppid_text, tty, comm, args = parts
        try:
            pid = int(pid_text)
            ppid = int(ppid_text)
        except ValueError:
            continue
        if not is_codex_cli_process(comm, args):
            continue
        codex_pids.add(pid)
        rows.append(
            {
                "pid": pid,
                "ppid": ppid,
                "tty": normalize_tty(tty),
                "command": str(args or comm).strip(),
            }
        )

    sessions: dict[str, dict[str, Any]] = {}
    for row in rows:
        tty = str(row.get("tty") or "")
        if not tty or tty == "??":
            continue
        session = sessions.setdefault(tty, {"tty": tty, "pids": [], "root_pids": [], "commands": []})
        pid = int(row["pid"])
        session["pids"].append(pid)
        session["commands"].append(row["command"])
        if int(row["ppid"]) not in codex_pids:
            session["root_pids"].append(pid)

    result: list[dict[str, Any]] = []
    for tty in sorted(sessions):
        session = sessions[tty]
        session["pids"] = sorted(set(session["pids"]))
        session["root_pids"] = sorted(set(session["root_pids"] or session["pids"]))
        result.append(session)
    return result


def terminate_stale_codex_sessions_action(
    payload: dict[str, Any],
    *,
    marker_path: Path = CURRENT_CODEX_TTY_PATH,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    screen_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    managed_codex_tty_labeler: Callable[[], dict[str, str]] | None = None,
    killer: Callable[[int, int], None] = os.kill,
) -> dict[str, Any]:
    confirmed = bool(payload.get("confirmed"))
    sessions = discover_codex_process_sessions(runner=runner)
    codex_ttys = [str(session.get("tty") or "") for session in sessions if session.get("tty")]
    bridge = adam_voice_bridge_status(
        marker_path=marker_path,
        codex_tty_discoverer=lambda: codex_ttys,
        managed_codex_tty_labeler=managed_codex_tty_labeler,
        screen_runner=screen_runner,
        expected_codex_session_limit=1,
    )
    protected_tty = str(bridge.get("effective_tty") or "")
    if not protected_tty:
        return {
            "ok": False,
            "status": "no_protected_tty",
            "message": "Neukončuji staré Codex relace: voice bridge nemá jednoznačný chráněný cíl.",
            "voice_bridge": bridge,
            "sessions": sessions,
        }

    protected_ttys = {protected_tty, *[str(tty) for tty in bridge.get("managed_codex_ttys", []) if tty]}
    stale_sessions = [session for session in sessions if session.get("tty") not in protected_ttys]
    stale_ttys = [str(session.get("tty") or "") for session in stale_sessions]
    root_pids = sorted({int(pid) for session in stale_sessions for pid in session.get("root_pids", [])})
    if not stale_sessions:
        return {
            "ok": True,
            "status": "no_stale_sessions",
            "message": f"Žádné staré Codex relace k ukončení. Chráněný cíl je {protected_tty}.",
            "protected_tty": protected_tty,
            "protected_ttys": sorted(protected_ttys),
            "managed_codex_ttys": bridge.get("managed_codex_ttys", []),
            "voice_bridge": bridge,
            "sessions": sessions,
        }
    if not confirmed:
        return {
            "ok": False,
            "status": "confirmation_required",
            "message": f"K ukončení jsou připravené staré Codex relace: {', '.join(stale_ttys)}. Akci je potřeba potvrdit.",
            "protected_tty": protected_tty,
            "protected_ttys": sorted(protected_ttys),
            "managed_codex_ttys": bridge.get("managed_codex_ttys", []),
            "stale_ttys": stale_ttys,
            "root_pids": root_pids,
            "voice_bridge": bridge,
            "sessions": sessions,
        }

    killed: list[int] = []
    errors: list[str] = []
    for pid in root_pids:
        try:
            killer(pid, signal.SIGTERM)
            killed.append(pid)
        except OSError as exc:
            errors.append(f"PID {pid}: {exc}")
    if errors:
        return {
            "ok": False,
            "status": "partial_or_failed",
            "message": f"Některé staré Codex relace se nepodařilo ukončit: {' | '.join(errors)}",
            "protected_tty": protected_tty,
            "protected_ttys": sorted(protected_ttys),
            "managed_codex_ttys": bridge.get("managed_codex_ttys", []),
            "stale_ttys": stale_ttys,
            "killed_pids": killed,
            "errors": errors,
        }
    return {
        "ok": True,
        "status": "stale_sessions_terminated",
        "message": f"Ukončil jsem staré Codex relace: {', '.join(stale_ttys)}. Chráněný cíl {protected_tty} zůstal běžet.",
        "protected_tty": protected_tty,
        "protected_ttys": sorted(protected_ttys),
        "managed_codex_ttys": bridge.get("managed_codex_ttys", []),
        "stale_ttys": stale_ttys,
        "killed_pids": killed,
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
    resolved_id = str(reminder.get("id", ""))
    updated = cancel_reminder_record(
        resolved_id,
        reason=resolution_reason,
        resolved_at=now,
        evidence=evidence,
        path=reminders_path,
    )
    if not updated:
        return {
            "ok": False,
            "message": "Připomínka se během zpracování změnila; nic nebylo zapsáno.",
            "reminders": reminders_status(path=reminders_path),
        }
    return {
        "ok": True,
        "reminder_id": safe_text(resolved_id),
        "reminder_ref": reminder_reference(resolved_id),
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


EMAIL_ARCHIVE_OPENABLE_FILES: dict[str, tuple[Path, str]] = {
    "body_html": (Path("body.html"), "text/html; charset=utf-8"),
    "body_txt": (Path("body.txt"), "text/plain; charset=utf-8"),
    "original_eml": (Path("original.eml"), "message/rfc822"),
    "metadata": (Path("metadata.json"), "application/json; charset=utf-8"),
    "attachments": (Path("attachments") / "attachments.json", "application/json; charset=utf-8"),
}


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
        uid = safe_text(str(metadata.get("uid", "")))[:80]
        date_text = safe_text(str(metadata.get("date", "")))[:160]
        archived_at = safe_text(str(metadata.get("archived_at", "")))[:120]
        haystack = " ".join([archive_id, uid, subject, sender, date_text]).casefold()
        if safe_query and safe_query not in haystack:
            continue
        archives.append(
            {
                "archive_id": archive_id,
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
    uid = safe_text(str(metadata.get("uid", ""))).strip()
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
                "url": f"/email-archive/file?archive_id={quote(safe_archive_id)}&file={quote(key)}",
            }
        )

    attachments = read_email_archive_attachment_metadata(archive_dir)
    downloaded = downloaded_email_archive_attachments(uid=uid, documents_dir=documents_dir)

    return {
        "ok": True,
        "archive_id": safe_archive_id,
        "uid": uid,
        "subject": safe_text(str(metadata.get("subject", "")))[:260],
        "sender": redact_email_addresses(safe_text(str(metadata.get("from", ""))))[:220],
        "date": safe_text(str(metadata.get("date", "")))[:160],
        "archived_at": safe_text(str(metadata.get("archived_at", "")))[:120],
        "relative_path": safe_text(str(relative_to_project(archive_dir)))[:500],
        "files": files,
        "attachments": attachments,
        "downloaded_attachments": downloaded,
        "message": "Archiv e-mailu načten read-only.",
    }


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
                "content_type": content_type_for_path(path),
                "size_bytes": size,
                "relative_path": safe_text(str(relative_to_project(path)))[:500],
                "url": f"/email-archive/incoming?name={quote(path.name)}",
            }
        )
    return result


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
        "content_type": content_type_for_path(resolved),
        "filename": safe_filename(resolved.name),
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
    if candidate["status"] == "past_due":
        return {
            "ok": False,
            "message": "E-mailový termín je už v minulosti; novou připomínku z něj teď nevytvářím.",
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
    save_result = save_reminder_draft(reminder, path=reminders_path)
    if not save_result.created:
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
    amount_due = safe_text(str(candidate.get("amount_due", "")))[:80]
    enrich_reminder_record(
        reminder_id,
        related_asset=safe_text(str(candidate.get("related_asset", "")))[:180],
        amount_due=amount_due,
        amount_note=(
            safe_text(str(candidate.get("amount_note", "")))[:240]
            or ("Částka byla odhadnuta z krátkého kontextu termínu v dokumentu." if amount_due else "")
        ),
        document_ref=safe_text(str(candidate.get("document_ref", "")))[:80],
        due_date_type=safe_text(str(candidate.get("type", "")))[:80],
        path=reminders_path,
    )


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


OPENABLE_DOCUMENT_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".tif", ".tiff"}
IMAGE_DOCUMENT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".tif", ".tiff"}


def resolve_document_stored_path(stored_path: str, vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> Path | None:
    try:
        root = vault_dir.resolve(strict=True)
        raw_target = Path(stored_path)
        target = (raw_target if raw_target.is_absolute() else PROJECT_ROOT / raw_target).resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    if target.is_file() and (target == root or root in target.parents):
        return target
    return None


def document_stored_path_is_openable_pdf(stored_path: str, vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> bool:
    target = resolve_document_stored_path(stored_path, vault_dir=vault_dir)
    return bool(target and target.suffix.casefold() == ".pdf")


def purchase_stored_path_is_openable_pdf(stored_path: str, purchases_dir: Path = DEFAULT_PURCHASES_DIR) -> bool:
    try:
        root = purchases_dir.resolve(strict=True)
        raw_target = Path(stored_path)
        target = (raw_target if raw_target.is_absolute() else PROJECT_ROOT / raw_target).resolve(strict=True)
    except (OSError, RuntimeError):
        return False
    return target.is_file() and target.suffix.casefold() == ".pdf" and (target == root or root in target.parents)


def resolve_openable_document_file(
    document_id: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> dict[str, Any]:
    documents = read_jsonl(vault_dir / "index" / "documents_index.jsonl")
    row_index = find_document_row_index_by_reference(documents, document_id)
    if row_index is None:
        return {"ok": False, "message": "Dokument nebyl nalezen ve vault indexu."}
    row = documents[row_index]
    stored_path = str(row.get("stored_path", ""))
    target = resolve_document_stored_path(stored_path, vault_dir=vault_dir)
    if target is None:
        return {"ok": False, "message": "Soubor dokumentu není dostupný nebo neleží ve vaultu."}
    extension = target.suffix.casefold()
    if extension not in OPENABLE_DOCUMENT_EXTENSIONS:
        return {"ok": False, "message": "Soubor dokumentu není podporovaný pro čtení v Cockpitu."}

    guessed_content_type = mimetypes.guess_type(target.name)[0]
    if extension == ".pdf":
        content_type = "application/pdf"
        viewer_kind = "pdf"
    elif extension in IMAGE_DOCUMENT_EXTENSIONS:
        content_type = guessed_content_type or "application/octet-stream"
        viewer_kind = "image"
    else:
        content_type = guessed_content_type or "application/octet-stream"
        viewer_kind = "download"
    title = safe_text(str(row.get("title", "") or row.get("filename", "") or "Dokument"))[:240]
    document_ref = document_reference(str(row.get("document_id", "")))
    return {
        "ok": True,
        "path": target,
        "title": title,
        "document_id": safe_text(str(row.get("document_id", ""))),
        "document_ref": document_ref,
        "extension": extension,
        "content_type": content_type,
        "viewer_kind": viewer_kind,
    }


def resolve_openable_purchase_pdf(
    purchase_id: str,
    purchases_dir: Path = DEFAULT_PURCHASES_DIR,
) -> dict[str, Any]:
    safe_reference = safe_slug(purchase_id, default="", limit=180)
    if not safe_reference or not purchases_dir.exists():
        return {"ok": False, "message": "Nákup nebyl nalezen v nákupním archivu."}
    for manifest_path in purchases_dir.glob("*/*/invoice_manifest.json"):
        current_purchase_id = f"purchase-{manifest_path.parent.parent.name}-{manifest_path.parent.name}"
        current_ref = purchase_reference(current_purchase_id)
        if safe_reference not in {safe_slug(current_purchase_id, default="", limit=180), current_ref}:
            continue
        try:
            manifest = read_json_file(manifest_path)
        except ValueError:
            return {"ok": False, "message": "Manifest nákupu nejde přečíst."}
        attachments = [item for item in manifest.get("attachments", []) if isinstance(item, dict)]
        for attachment in attachments:
            stored_path = str(attachment.get("stored_path", ""))
            if not stored_path or not purchase_stored_path_is_openable_pdf(stored_path, purchases_dir=purchases_dir):
                continue
            raw_target = Path(stored_path)
            target = (raw_target if raw_target.is_absolute() else PROJECT_ROOT / raw_target).resolve(strict=True)
            title = safe_text(str(manifest.get("subject", "") or attachment.get("filename", "") or "Nákup / faktura"))[:240]
            return {
                "ok": True,
                "path": target,
                "title": title,
                "purchase_id": safe_text(current_purchase_id),
                "purchase_ref": current_ref,
            }
        return {"ok": False, "message": "PDF nákupu není dostupné nebo neleží v nákupním archivu."}
    return {"ok": False, "message": "Nákup nebyl nalezen v nákupním archivu."}


def open_document_pdf_action(
    document_id: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    opener: Callable[[list[str]], object] | None = None,
) -> dict[str, Any]:
    resolved = resolve_openable_document_file(document_id, vault_dir=vault_dir)
    if not resolved.get("ok"):
        return resolved
    target = resolved["path"]
    runner = opener or (lambda command: subprocess.run(command, check=False))
    runner(["/usr/bin/open", str(target)])
    message = "PDF otevřeno v lokální aplikaci."
    if resolved.get("viewer_kind") != "pdf":
        message = "Dokument otevřen v lokální aplikaci."
    return {
        "ok": True,
        "message": message,
        "document_id": resolved["document_id"],
        "document_ref": resolved["document_ref"],
    }


def document_reader_page_html(document_id: str, title: str, viewer_kind: str = "pdf") -> str:
    safe_title = html.escape(title or "Dokument")
    safe_document_id = html.escape(document_id)
    document_id_json = json.dumps(document_id, ensure_ascii=False)
    pdf_url = f"/documents/pdf?document_id={quote(document_id, safe='')}"
    safe_pdf_url = html.escape(pdf_url, quote=True)
    if viewer_kind == "image":
        viewer_html = (
            f'<main class="image-viewer"><img class="document-image" src="{safe_pdf_url}" '
            f'alt="Náhled dokumentu"></main>\n'
            f'  <noscript><div class="fallback"><a class="button primary" href="{safe_pdf_url}">'
            f"Otevřít obrázek</a></div></noscript>"
        )
    else:
        viewer_html = (
            f'<iframe class="viewer" src="{safe_pdf_url}" title="PDF dokument"></iframe>\n'
            f'  <noscript><div class="fallback"><a class="button primary" href="{safe_pdf_url}">'
            f"Otevřít PDF</a></div></noscript>"
        )
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
    .image-viewer {{ width: 100vw; min-height: calc(100vh - 82px); overflow: auto; display: grid; place-items: start center; padding: 16px; background: #0f172a; }}
    .document-image {{ max-width: 100%; height: auto; background: white; box-shadow: 0 18px 42px rgba(15, 23, 42, 0.28); }}
    .fallback {{ padding: 16px; }}
    @media (max-width: 720px) {{
      .bar {{ grid-template-columns: 1fr; align-items: stretch; }}
      button, a.button {{ width: 100%; text-align: center; }}
      .viewer {{ height: calc(100vh - 210px); }}
      .image-viewer {{ min-height: calc(100vh - 210px); padding: 10px; }}
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
  {viewer_html}
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


def purchase_reader_page_html(purchase_id: str, title: str) -> str:
    safe_title = html.escape(title or "Nákup / faktura")
    safe_purchase_id = html.escape(purchase_id)
    pdf_url = f"/purchases/pdf?purchase_id={quote(purchase_id, safe='')}"
    safe_pdf_url = html.escape(pdf_url, quote=True)
    return f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Nákup / záruka - {safe_title}</title>
  <style>
    :root {{ color-scheme: light; --blue: #2563eb; --ink: #172033; --muted: #667085; }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: #f6f7fb; }}
    header {{ display: flex; gap: 12px; align-items: center; justify-content: space-between; padding: 14px 18px; background: #fff; border-bottom: 1px solid #d8deea; }}
    h1 {{ margin: 0; font-size: 18px; }}
    .meta {{ color: var(--muted); font-size: 13px; margin-top: 3px; }}
    .actions {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    button, a.button {{ border: 1px solid #b9c4d6; background: #fff; color: var(--ink); border-radius: 7px; padding: 8px 11px; font-size: 14px; text-decoration: none; cursor: pointer; }}
    a.primary {{ background: var(--blue); color: #fff; border-color: var(--blue); }}
    main {{ height: calc(100vh - 70px); }}
    iframe {{ width: 100%; height: 100%; border: 0; background: #fff; }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>{safe_title}</h1>
      <div class="meta">Nákupní evidence: {safe_purchase_id}</div>
    </div>
    <div class="actions">
      <a class="button primary" href="{safe_pdf_url}" target="_blank" rel="noopener">Otevřít PDF</a>
      <button type="button" onclick="window.opener && window.opener.focus ? window.opener.focus() : null">Zpět do Cockpitu</button>
      <button type="button" onclick="window.close()">Zavřít okno</button>
    </div>
  </header>
  <main>
    <iframe title="PDF nákupní faktury" src="{safe_pdf_url}"></iframe>
  </main>
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


def lekarna_admin_page_html() -> str:
    retire_phrase = html.escape(RETIRE_CONFIRMATION_PHRASE)
    openai_phrase = html.escape(OPENAI_DRAFT_CONFIRMATION_PHRASE)
    import_phrase = html.escape(APPLY_CONFIRMATION_PHRASE)
    return f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Lékárna - správa</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; padding: 22px; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f6f8fb; color: #172033; }}
    main {{ max-width: 1120px; margin: 0 auto; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; letter-spacing: 0; }}
    h2 {{ margin: 0 0 12px; font-size: 20px; letter-spacing: 0; }}
    p {{ line-height: 1.5; }}
    .layout {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(320px, 0.9fr); gap: 18px; margin-top: 20px; }}
    section {{ background: white; border: 1px solid #d8dee8; border-radius: 8px; padding: 18px; }}
    label {{ display: block; font-weight: 650; margin-top: 12px; }}
    input, textarea {{ width: 100%; margin-top: 6px; border: 1px solid #b9c2d0; border-radius: 6px; padding: 10px 12px; font: inherit; background: white; }}
    button {{ border: 0; border-radius: 6px; padding: 10px 14px; font: inherit; font-weight: 700; cursor: pointer; background: #1f5f8f; color: white; margin: 12px 8px 0 0; }}
    button.secondary {{ background: #4b5563; }}
    button.danger {{ background: #9f2d2d; }}
    button:disabled {{ opacity: 0.55; cursor: wait; }}
    .muted {{ color: #5d6778; font-size: 14px; }}
    .result {{ white-space: pre-wrap; background: #f2f5f8; border: 1px solid #d8dee8; border-radius: 8px; padding: 12px; min-height: 44px; margin-top: 12px; }}
    .items {{ display: grid; gap: 10px; margin-top: 12px; }}
    .item {{ border: 1px solid #d8dee8; border-radius: 8px; padding: 12px; background: #fbfcfd; }}
    .item strong {{ display: block; margin-bottom: 4px; }}
    .row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .review-row {{ border: 1px solid #d8dee8; border-radius: 8px; padding: 12px; margin-top: 12px; background: #fbfcfd; }}
    .review-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
    .review-grid .wide {{ grid-column: 1 / -1; }}
    .review-grid textarea {{ min-height: 86px; resize: vertical; }}
    .quick-review {{ border: 1px solid #cfd8e3; border-radius: 8px; padding: 12px; margin-top: 12px; background: #ffffff; }}
    .quick-review-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px 14px; margin-top: 10px; }}
    .quick-review-item strong {{ color: #334155; font-size: 12px; text-transform: uppercase; }}
    .quick-review-item div {{ margin-top: 3px; overflow-wrap: anywhere; }}
    .quick-review-item.wide {{ grid-column: 1 / -1; }}
    .status-pill {{ display: inline-flex; align-items: center; min-height: 26px; border-radius: 999px; padding: 3px 10px; font-size: 13px; font-weight: 800; }}
    .status-pill.ok {{ background: #e4f7eb; color: #176334; }}
    .status-pill.warn {{ background: #fff4d8; color: #875200; }}
    .status-pill.bad {{ background: #ffe5e5; color: #9f2d2d; }}
    .pipeline {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin-top: 12px; }}
    .pipeline-step {{ border: 1px solid #d8dee8; border-radius: 8px; padding: 9px; background: #f8fafc; }}
    .pipeline-step strong {{ display: block; font-size: 13px; }}
    .pipeline-step span {{ display: block; margin-top: 3px; color: #5d6778; font-size: 13px; }}
    details.advanced-review {{ margin-top: 12px; }}
    details.advanced-review summary {{ cursor: pointer; font-weight: 800; color: #334155; }}
    .review-summary {{ border: 1px solid #b7d5c1; border-radius: 8px; padding: 12px; background: #effaf2; color: #1f5630; }}
    .review-summary.alert {{ border-color: #f0a8a8; background: #fff2f2; color: #842323; }}
    .review-summary ul {{ margin: 8px 0 0; padding-left: 20px; }}
    .field-heading {{ display: flex; align-items: center; gap: 6px; }}
    .field-heading span {{ overflow-wrap: anywhere; }}
    .help-button {{ width: 22px; height: 22px; margin: 0; padding: 0; border-radius: 999px; background: #e9eef5; color: #334155; font-size: 14px; line-height: 22px; }}
    .field-help {{ margin-top: 6px; padding: 8px; border: 1px solid #d8dee8; border-radius: 6px; background: #f7f9fc; color: #475569; font-size: 13px; font-weight: 500; }}
    .field-warning {{ margin-top: 6px; color: #9f2d2d; font-size: 13px; font-weight: 750; }}
    label.needs-review input, label.needs-review textarea {{ border-color: #d04444; background: #fff8f8; box-shadow: 0 0 0 2px rgba(208, 68, 68, 0.12); }}
    label.needs-review .field-heading span::after {{ content: " - doplnit"; color: #9f2d2d; font-weight: 800; }}
    @media (max-width: 840px) {{ body {{ padding: 14px; }} .layout, .row, .pipeline {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <h1>Lékárna - správa</h1>
    <p class="muted">Lokální bezpečná správa položek v domácí lékárně. Vyhledávání je read-only; vyřazení a příjem fotek zapisují až po opsání potvrzovací věty.</p>
    <div class="layout">
      <section>
        <h2>Vyhledání a vyřazení</h2>
        <label for="searchInput">Název, potíž nebo část názvu</label>
        <input id="searchInput" placeholder="např. heparin, kašel, rýma">
        <button id="searchBtn">Hledat</button>
        <div id="searchResults" class="items"></div>

        <label for="retireReason">Důvod vyřazení</label>
        <input id="retireReason" placeholder="např. spotřebováno, prošlá expirace">
        <button id="previewRetireBtn" class="secondary">Náhled vyřazení</button>
        <div id="retirePreview" class="result">Nejdřív vyhledej položku nebo napiš přesný název.</div>
        <label for="retireConfirm">Potvrzení pro zápis: {retire_phrase}</label>
        <input id="retireConfirm" placeholder="{retire_phrase}">
        <button id="applyRetireBtn" class="danger">Potvrzeně vyřadit</button>
      </section>

      <section>
        <h2>Příjem léku z fotky</h2>
        <p class="muted">Návrh přečte vybrané fotky přes OpenAI Vision, spáruje lék se SÚKL DLP a stáhne konkrétní příbalový leták. Na sklad se zapisuje až posledním potvrzeným krokem.</p>
        <button id="refreshPhotosBtn" class="secondary">Obnovit seznam fotek</button>
        <div id="photoList" class="items"></div>
        <div class="row">
          <label for="importLimit">Limit fotek
            <input id="importLimit" type="number" min="1" max="10" value="3">
          </label>
          <label for="importLocation">Umístění
            <input id="importLocation" value="Horní koupelna" placeholder="Vlastní umístění">
          </label>
        </div>
        <label for="openaiConfirm">Potvrzení pro zpracování fotek přes OpenAI: {openai_phrase}</label>
        <input id="openaiConfirm" placeholder="{openai_phrase}">
        <button id="draftImportBtn">Připravit návrh z fotek</button>
        <div id="draftResult" class="result">Vyber fotku nebo ponech nejnovější fotky podle limitu. Návrh zatím není připravený.</div>
        <label for="manifestPath">Manifest z posledního návrhu</label>
        <input id="manifestPath" readonly>
        <div class="row">
          <button id="reloadManifestBtn" class="secondary">Znovu načíst kontrolu</button>
          <button id="saveManifestBtn" class="secondary">Uložit opravy návrhu</button>
        </div>
        <div id="manifestLoadStatus" class="muted">Kontrola návrhu se po přípravě načte automaticky. Tlačítko ji jen znovu přenačte.</div>
        <button id="retryPilBtn" class="secondary">Zkusit PIL znovu</button>
        <div id="manifestEditor" class="items"></div>
        <label for="importConfirm">Potvrzení pro příjem na sklad: {import_phrase}</label>
        <input id="importConfirm" placeholder="{import_phrase}">
        <button id="applyImportBtn" class="danger">Přijmout návrh na sklad</button>
        <div id="applyResult" class="result">Příjem zatím nebyl spuštěný.</div>
      </section>
    </div>
  </main>
  <script>
    const searchInput = document.getElementById("searchInput");
    const searchBtn = document.getElementById("searchBtn");
    const searchResults = document.getElementById("searchResults");
    const retireReason = document.getElementById("retireReason");
    const previewRetireBtn = document.getElementById("previewRetireBtn");
    const retirePreview = document.getElementById("retirePreview");
    const retireConfirm = document.getElementById("retireConfirm");
    const applyRetireBtn = document.getElementById("applyRetireBtn");
    const refreshPhotosBtn = document.getElementById("refreshPhotosBtn");
    const photoList = document.getElementById("photoList");
    const importLimit = document.getElementById("importLimit");
    const importLocation = document.getElementById("importLocation");
    const openaiConfirm = document.getElementById("openaiConfirm");
    const draftImportBtn = document.getElementById("draftImportBtn");
    const draftResult = document.getElementById("draftResult");
    const manifestPath = document.getElementById("manifestPath");
    const reloadManifestBtn = document.getElementById("reloadManifestBtn");
    const saveManifestBtn = document.getElementById("saveManifestBtn");
    const manifestLoadStatus = document.getElementById("manifestLoadStatus");
    const retryPilBtn = document.getElementById("retryPilBtn");
    const manifestEditor = document.getElementById("manifestEditor");
    const importConfirm = document.getElementById("importConfirm");
    const applyImportBtn = document.getElementById("applyImportBtn");
    let currentManifestFields = [];
    let currentManifestFieldHelp = {{}};

    async function postJson(url, payload) {{
      const res = await fetch(url, {{
        method: "POST",
        headers: {{"Content-Type": "application/json"}},
        body: JSON.stringify(payload || {{}})
      }});
      return res.json();
    }}

    function selectedPhotoNames() {{
      return Array.from(photoList.querySelectorAll("input[type=checkbox]:checked")).map((input) => input.value);
    }}

    function escapeText(value) {{
      return String(value || "").replace(/[&<>"']/g, (char) => ({{"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}}[char]));
    }}

    function renderItems(items) {{
      searchResults.innerHTML = "";
      if (!items.length) {{
        searchResults.innerHTML = '<div class="muted">Nic nenalezeno.</div>';
        return;
      }}
      for (const item of items) {{
        const card = document.createElement("div");
        card.className = "item";
        card.innerHTML = `
          <strong>${{escapeText(item.nazev || "Název neuveden")}}</strong>
          <div>${{escapeText(item.ucinna_latka)}} ${{escapeText(item.sila)}} ${{escapeText(item.forma)}}</div>
          <div>Kde je: ${{escapeText(item.umisteni || "neuvedeno")}} | Expirace: ${{escapeText(item.expirace || "neuvedena")}}</div>
          <div class="muted">Proč se našlo: ${{escapeText((item.reasons || []).join(", "))}}</div>
        `;
        card.addEventListener("click", () => {{
          searchInput.value = item.nazev || "";
          retirePreview.textContent = `Vybráno: ${{item.nazev || ""}}`;
        }});
        searchResults.appendChild(card);
      }}
    }}

    function isLongManifestField(field) {{
      return ["pouziti", "pro_koho", "nevhodne_pro_koho", "poznamky", "PIL_Short", "PIL_Source", "Search_Tags"].includes(field);
    }}

    function renderManifestSummary(warnings) {{
      const summary = document.createElement("div");
      const list = Array.isArray(warnings) ? warnings : [];
      if (!list.length) {{
        summary.className = "review-summary";
        summary.textContent = "Návrh vypadá připravený k přijetí. Přesto zkontroluj název, sílu, množství a příbalový výtah.";
        return summary;
      }}
      summary.className = "review-summary alert";
      const heading = document.createElement("strong");
      heading.textContent = "Co je nutné doplnit";
      summary.appendChild(heading);
      const ul = document.createElement("ul");
      list.forEach((warning) => {{
        const li = document.createElement("li");
        li.textContent = warning;
        ul.appendChild(li);
      }});
      summary.appendChild(ul);
      return summary;
    }}

    function quickReviewValue(row, field) {{
      const value = String((row && row[field]) || "").trim();
      return value || "nedoplněno";
    }}

    function appendQuickReviewItem(parent, labelText, value, wide) {{
      const item = document.createElement("div");
      item.className = wide ? "quick-review-item wide" : "quick-review-item";
      const label = document.createElement("strong");
      label.textContent = labelText;
      const content = document.createElement("div");
      content.textContent = value;
      item.appendChild(label);
      item.appendChild(content);
      parent.appendChild(item);
    }}

    function pilStatusInfo(row) {{
      const status = quickReviewValue(row, "PIL_Match_Status");
      const source = quickReviewValue(row, "PIL_Source").toLowerCase();
      if (status === "overeno" && source.includes("pil dokument")) {{
        return {{className: "ok", text: "PIL ověřený z dokumentu"}};
      }}
      if (status === "overeno_z_dlp") {{
        return {{className: "warn", text: "PIL čeká na stažení"}};
      }}
      if (status === "ceka_na_pil_overeni" || status === "nedohledano") {{
        return {{className: "bad", text: "PIL není ověřený"}};
      }}
      return {{className: "warn", text: status}};
    }}

    function appendPilStatusItem(parent, row) {{
      const item = document.createElement("div");
      item.className = "quick-review-item";
      const label = document.createElement("strong");
      label.textContent = "Stav PIL";
      const pill = document.createElement("span");
      const info = pilStatusInfo(row);
      pill.className = `status-pill ${{info.className}}`;
      pill.textContent = info.text;
      item.appendChild(label);
      item.appendChild(pill);
      parent.appendChild(item);
    }}

    function renderPipeline(data) {{
      const rows = Array.isArray(data.rows) ? data.rows : [];
      const hasRows = rows.length > 0;
      const pilVerified = rows.some((row) => pilStatusInfo(row).className === "ok");
      const hasWarnings = Array.isArray(data.warnings) && data.warnings.length > 0;
      const pipeline = document.createElement("div");
      pipeline.className = "pipeline";
      const steps = [
        ["OCR", hasRows ? "text z fotky načtený" : "čeká na návrh"],
        ["SÚKL DLP", hasRows ? "lékový záznam spárovaný" : "čeká na OCR"],
        ["PIL", pilVerified ? "příbalový leták ověřený" : hasWarnings ? "vyžaduje opakování" : "není vyžadovaná akce"]
      ];
      steps.forEach(([title, detail]) => {{
        const step = document.createElement("div");
        step.className = "pipeline-step";
        const strong = document.createElement("strong");
        strong.textContent = title;
        const span = document.createElement("span");
        span.textContent = detail;
        step.appendChild(strong);
        step.appendChild(span);
        pipeline.appendChild(step);
      }});
      return pipeline;
    }}

    function renderQuickReview(row, rowIndex) {{
      const card = document.createElement("div");
      card.className = "quick-review";
      const title = document.createElement("strong");
      title.textContent = `Rychlá kontrola #${{rowIndex + 1}}`;
      card.appendChild(title);
      const grid = document.createElement("div");
      grid.className = "quick-review-grid";
      appendQuickReviewItem(grid, "Název", quickReviewValue(row, "nazev"), false);
      appendQuickReviewItem(
        grid,
        "Balení",
        [quickReviewValue(row, "sila"), quickReviewValue(row, "forma"), quickReviewValue(row, "mnozstvi")]
          .filter((value) => value !== "nedoplněno")
          .join(" | ") || "nedoplněno",
        false
      );
      appendQuickReviewItem(grid, "Účinná látka", quickReviewValue(row, "ucinna_latka"), false);
      appendPilStatusItem(grid, row);
      appendQuickReviewItem(grid, "Použití / klasifikace", quickReviewValue(row, "pouziti"), true);
      appendQuickReviewItem(grid, "PIL short", quickReviewValue(row, "PIL_Short"), true);
      appendQuickReviewItem(grid, "Zdroj", quickReviewValue(row, "PIL_Source"), true);
      card.appendChild(grid);
      return card;
    }}

    function renderManifestEditor(data) {{
      currentManifestFields = Array.isArray(data.fields) ? data.fields : [];
      currentManifestFieldHelp = data.field_help && typeof data.field_help === "object" ? data.field_help : currentManifestFieldHelp;
      const rows = Array.isArray(data.rows) ? data.rows : [];
      const rowIssues = Array.isArray(data.row_issues) ? data.row_issues : [];
      manifestEditor.innerHTML = "";
      manifestEditor.appendChild(renderManifestSummary(data.warnings || []));
      manifestEditor.appendChild(renderPipeline(data));
      if (!rows.length) {{
        const empty = document.createElement("div");
        empty.className = "muted";
        empty.textContent = "Manifest nemá žádné řádky ke kontrole.";
        manifestEditor.appendChild(empty);
        return;
      }}
      rows.forEach((row, rowIndex) => {{
        manifestEditor.appendChild(renderQuickReview(row, rowIndex));
      }});
      const advanced = document.createElement("details");
      advanced.className = "advanced-review";
      advanced.open = Array.isArray(data.warnings) && data.warnings.length > 0;
      const advancedSummary = document.createElement("summary");
      advancedSummary.textContent = "Pokročilé úpravy návrhu";
      advanced.appendChild(advancedSummary);
      rows.forEach((row, rowIndex) => {{
        const card = document.createElement("div");
        card.className = "review-row";
        const title = document.createElement("strong");
        title.textContent = `Kontrola návrhu #${{rowIndex + 1}}`;
        card.appendChild(title);
        const grid = document.createElement("div");
        grid.className = "review-grid";
        currentManifestFields.forEach((field) => {{
          const label = document.createElement("label");
          if (isLongManifestField(field)) label.className = "wide";
          const fieldIssues = rowIssues[rowIndex] && Array.isArray(rowIssues[rowIndex][field]) ? rowIssues[rowIndex][field] : [];
          if (fieldIssues.length) label.classList.add("needs-review");
          const heading = document.createElement("div");
          heading.className = "field-heading";
          const fieldName = document.createElement("span");
          fieldName.textContent = field;
          heading.appendChild(fieldName);
          const helpText = currentManifestFieldHelp[field] || "";
          if (helpText) {{
            const helpButton = document.createElement("button");
            helpButton.type = "button";
            helpButton.className = "help-button";
            helpButton.textContent = "?";
            helpButton.title = helpText;
            heading.appendChild(helpButton);
            const helpBox = document.createElement("div");
            helpBox.className = "field-help";
            helpBox.hidden = true;
            helpBox.textContent = helpText;
            helpButton.addEventListener("click", (event) => {{
              event.preventDefault();
              event.stopPropagation();
              helpBox.hidden = !helpBox.hidden;
            }});
            label.appendChild(heading);
            label.appendChild(helpBox);
          }} else {{
            label.appendChild(heading);
          }}
          if (fieldIssues.length) {{
            const warning = document.createElement("div");
            warning.className = "field-warning";
            warning.textContent = fieldIssues.join(" ");
            label.appendChild(warning);
          }}
          const control = isLongManifestField(field) ? document.createElement("textarea") : document.createElement("input");
          control.value = row[field] || "";
          control.dataset.rowIndex = String(rowIndex);
          control.dataset.field = field;
          label.appendChild(control);
          grid.appendChild(label);
        }});
        card.appendChild(grid);
        advanced.appendChild(card);
      }});
      manifestEditor.appendChild(advanced);
    }}

    function collectManifestRows() {{
      const rowCount = manifestEditor.querySelectorAll(".review-row").length;
      const rows = Array.from({{length: rowCount}}, () => ({{}}));
      manifestEditor.querySelectorAll("input[data-field], textarea[data-field]").forEach((control) => {{
        const rowIndex = Number(control.dataset.rowIndex || 0);
        const field = control.dataset.field || "";
        if (rows[rowIndex] && field) rows[rowIndex][field] = control.value;
      }});
      return rows;
    }}

    function setManifestLoadStatus(message) {{
      if (manifestLoadStatus) manifestLoadStatus.textContent = message;
    }}

    async function loadManifest(source = "manual") {{
      reloadManifestBtn.disabled = true;
      const originalText = reloadManifestBtn.textContent;
      reloadManifestBtn.textContent = "Načítám kontrolu...";
      setManifestLoadStatus("Načítám aktuální kontrolu návrhu z manifestu.");
      try {{
        const data = await postJson("/api/lekarna/import/manifest/load", {{
          manifest_path: manifestPath.value,
          effective_location: importLocation.value
        }});
        if (!data.ok) {{
          manifestEditor.innerHTML = `<div class="result">${{escapeText(data.message || "Manifest se nepodařilo načíst.")}}</div>`;
          setManifestLoadStatus(data.message || "Kontrolu návrhu se nepodařilo načíst.");
          return;
        }}
        if (data.manifest_path) manifestPath.value = data.manifest_path;
        renderManifestEditor(data);
        const loadedAt = new Date().toLocaleTimeString("cs-CZ", {{hour: "2-digit", minute: "2-digit", second: "2-digit"}});
        const prefix = source === "auto" ? "Kontrola návrhu načtena automaticky" : "Kontrola návrhu znovu načtena";
        setManifestLoadStatus(`${{prefix}} v ${{loadedAt}}.`);
      }} finally {{
        reloadManifestBtn.disabled = false;
        reloadManifestBtn.textContent = originalText || "Znovu načíst kontrolu";
      }}
    }}

    async function saveManifest() {{
      if (!manifestPath.value.trim()) {{
        return {{ok: false, message: "Chybí manifest."}};
      }}
      saveManifestBtn.disabled = true;
      try {{
        const rows = collectManifestRows();
        const data = await postJson("/api/lekarna/import/manifest/save", {{
          manifest_path: manifestPath.value,
          effective_location: importLocation.value,
          rows
        }});
        draftResult.textContent = data.message || "Manifest uložený.";
        if (Array.isArray(data.warnings) && data.warnings.length) {{
          draftResult.textContent += `\\nDoplnit:\\n- ${{data.warnings.join("\\n- ")}}`;
        }}
        renderManifestEditor({{
          fields: currentManifestFields,
          field_help: currentManifestFieldHelp,
          rows,
          warnings: data.warnings || [],
          row_issues: data.row_issues || []
        }});
        return data;
      }} finally {{
        saveManifestBtn.disabled = false;
      }}
    }}

    async function retryPil() {{
      retryPilBtn.disabled = true;
      try {{
        draftResult.textContent = "Zkouším znovu stáhnout a přečíst konkrétní PIL dokument pro aktuální návrh.";
        const data = await postJson("/api/lekarna/import/manifest/retry-pil", {{
          manifest_path: manifestPath.value,
          effective_location: importLocation.value
        }});
        draftResult.textContent = data.message || "PIL kontrola doběhla.";
        if (Array.isArray(data.failed) && data.failed.length) {{
          draftResult.textContent += `\\nNepodařilo se: ${{data.failed.join(", ")}}`;
        }}
        if (!data.ok) {{
          manifestEditor.innerHTML = `<div class="result">${{escapeText(data.message || "PIL se nepodařilo znovu načíst.")}}</div>`;
          return;
        }}
        if (data.manifest_path) manifestPath.value = data.manifest_path;
        renderManifestEditor(data);
      }} finally {{
        retryPilBtn.disabled = false;
      }}
    }}

    async function searchLekarna() {{
      const query = searchInput.value.trim();
      const res = await fetch(`/api/lekarna/search?q=${{encodeURIComponent(query)}}&limit=25`);
      const data = await res.json();
      if (!data.ok) {{
        searchResults.innerHTML = `<div class="result">${{escapeText(data.message || "Vyhledání selhalo.")}}</div>`;
        return;
      }}
      renderItems(Array.isArray(data.items) ? data.items : []);
    }}

    async function previewRetire() {{
      previewRetireBtn.disabled = true;
      try {{
        const data = await postJson("/api/lekarna/retire/preview", {{query: searchInput.value, reason: retireReason.value}});
        retirePreview.textContent = data.message || "Náhled není dostupný.";
      }} finally {{
        previewRetireBtn.disabled = false;
      }}
    }}

    async function applyRetire() {{
      applyRetireBtn.disabled = true;
      try {{
        const data = await postJson("/api/lekarna/retire/apply", {{
          query: searchInput.value,
          reason: retireReason.value,
          user_confirmed: true,
          confirmation_text: retireConfirm.value
        }});
        retirePreview.textContent = data.message || "Vyřazení doběhlo.";
        if (data.ok) {{
          if (data.web_export_path) retirePreview.textContent += `\\nWeb export: ${{data.web_export_path}}`;
          if (data.encrypted_bundle_path) retirePreview.textContent += `\\nŠifrovaný balíček: ${{data.encrypted_bundle_path}}`;
          if (data.production_publish && data.production_publish.message) {{
            retirePreview.textContent += `\\nProdukce: ${{data.production_publish.message}}`;
          }}
          if (Array.isArray(data.warnings) && data.warnings.length) {{
            retirePreview.textContent += `\\nUpozornění:\\n- ${{data.warnings.join("\\n- ")}}`;
          }}
        }}
      }} finally {{
        applyRetireBtn.disabled = false;
      }}
    }}

    async function refreshPhotos() {{
      const visibleLimit = Math.max(1, Math.min(Number(importLimit.value || 3), 10));
      const res = await fetch(`/api/lekarna/import/photos?limit=${{encodeURIComponent(String(visibleLimit))}}`);
      const data = await res.json();
      const photos = Array.isArray(data.photos) ? data.photos : [];
      photoList.innerHTML = "";
      if (!photos.length) {{
        photoList.innerHTML = '<div class="muted">V Downloads nejsou nalezené podporované fotky.</div>';
        return;
      }}
      const note = document.createElement("div");
      note.className = "muted";
      note.textContent = `Zobrazuji nejnovější fotky podle limitu: ${{visibleLimit}}. Zaškrtnuté fotky půjdou do návrhu.`;
      photoList.appendChild(note);
      for (const photo of photos) {{
        const row = document.createElement("label");
        row.className = "item";
        row.innerHTML = `<input type="checkbox" checked value="${{escapeText(photo.name)}}"> <strong>${{escapeText(photo.name)}}</strong><div class="muted">${{Number(photo.bytes || 0)}} B</div>`;
        photoList.appendChild(row);
      }}
    }}

    async function draftImport() {{
      draftImportBtn.disabled = true;
      try {{
        draftResult.textContent = "Připravuji návrh: OCR z fotky, párování SÚKL DLP a stažení konkrétního příbalového letáku.";
        const data = await postJson("/api/lekarna/import/draft", {{
          limit: Number(importLimit.value || 3),
          ocr_backend: "openai",
          photo_names: selectedPhotoNames(),
          confirmation_text: openaiConfirm.value
        }});
        draftResult.textContent = data.message || "Návrh doběhl.";
        if (data.manifest_path) manifestPath.value = data.manifest_path;
        if (data.ok) {{
          draftResult.textContent += `\\nFotky: ${{data.photos}} | nové: ${{data.new_candidates}} | duplicity: ${{data.duplicate_existing}} | revize: ${{data.needs_review}}`;
          await loadManifest("auto");
        }}
      }} finally {{
        draftImportBtn.disabled = false;
      }}
    }}

    async function applyImport() {{
      applyImportBtn.disabled = true;
      try {{
        if (manifestEditor.querySelector(".review-row")) {{
          const saveData = await saveManifest();
          if (!saveData.ok) {{
            applyResult.textContent = saveData.message || "Manifest se před příjmem nepodařilo uložit.";
            return;
          }}
        }}
        const data = await postJson("/api/lekarna/import/apply", {{
          manifest_path: manifestPath.value,
          location: importLocation.value,
          confirmation_text: importConfirm.value
        }});
        applyResult.textContent = data.message || "Příjem doběhl.";
        if (data.ok) {{
          applyResult.textContent += `\\nZapsáno: ${{data.appended}} | kopie: ${{data.copied}} | přejmenováno: ${{data.renamed}}\\nZáloha: ${{data.backup_path}}`;
          if (data.web_export_path) applyResult.textContent += `\\nWeb export: ${{data.web_export_path}}`;
          if (data.encrypted_bundle_path) applyResult.textContent += `\\nŠifrovaný balíček: ${{data.encrypted_bundle_path}}`;
          if (data.production_publish && data.production_publish.message) {{
            applyResult.textContent += `\\nProdukce: ${{data.production_publish.message}}`;
          }}
          if (Array.isArray(data.warnings) && data.warnings.length) {{
            applyResult.textContent += `\\nUpozornění:\\n- ${{data.warnings.join("\\n- ")}}`;
          }}
        }}
      }} finally {{
        applyImportBtn.disabled = false;
      }}
    }}

    searchBtn.addEventListener("click", searchLekarna);
    searchInput.addEventListener("keydown", (event) => {{ if (event.key === "Enter") {{ event.preventDefault(); searchLekarna(); }} }});
    previewRetireBtn.addEventListener("click", previewRetire);
    applyRetireBtn.addEventListener("click", applyRetire);
    refreshPhotosBtn.addEventListener("click", refreshPhotos);
    importLimit.addEventListener("change", refreshPhotos);
    draftImportBtn.addEventListener("click", draftImport);
    reloadManifestBtn.addEventListener("click", loadManifest);
    saveManifestBtn.addEventListener("click", saveManifest);
    retryPilBtn.addEventListener("click", retryPil);
    applyImportBtn.addEventListener("click", applyImport);
    refreshPhotos();
  </script>
</body>
</html>
"""


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
        "skipped_library_export_count": int(result.get("skipped_library_export_count", 0) or 0),
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
        case_id = safe_text(str(row.get("case_id", "")))[:120]
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


def accept_document_classification_suggestion_action(
    document_id: str,
    *,
    confirmed: bool = False,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> dict[str, Any]:
    safe_reference = safe_slug(document_id, default="", limit=140)
    if not safe_reference:
        return {"ok": False, "message": "Chybí document_id."}
    if not confirmed:
        return {"ok": False, "message": "Přijetí návrhu nebylo potvrzeno."}
    documents = read_jsonl(vault_dir / "index" / "documents_index.jsonl")
    row_index = find_document_row_index_by_reference(documents, safe_reference)
    if row_index is None:
        return {"ok": False, "message": "Dokument nebyl nalezen v indexu."}
    row = documents[row_index]
    document_id_value = safe_text(str(row.get("document_id", ""))).strip()
    text_by_id = {
        str(item.get("document_id", "")): str(item.get("text", ""))
        for item in read_jsonl(vault_dir / "index" / "text_index.jsonl")
    }
    suggestion = document_classification_metadata_suggestion(
        row=row,
        text=text_by_id.get(document_id_value, ""),
    )
    metadata = suggestion.get("metadata", {})
    if not suggestion.get("can_accept") or not isinstance(metadata, dict) or not metadata:
        return {"ok": False, "message": "Automatický návrh už není dostupný nebo není dost jistý."}
    result = update_document_classification_metadata_action(
        document_id=safe_reference,
        metadata=metadata,
        vault_dir=vault_dir,
    )
    if result.get("ok"):
        result["accepted_suggestion"] = suggestion
    return result


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

    updates: dict[str, str] = {}
    for field in DOCUMENT_METADATA_UPDATE_FIELDS:
        if field not in metadata:
            continue
        raw_value = str(metadata.get(field, "") or "").strip()
        if field == "domain":
            updates[field] = normalize_domain(raw_value) if raw_value else ""
        elif field in {"document_type", "case_id"}:
            updates[field] = safe_manual_metadata_slug(raw_value, limit=80)
        else:
            updates[field] = safe_text(raw_value)[:180]
    if not updates:
        return {"ok": False, "message": "Není co uložit; nebylo předáno žádné podporované metadata pole."}

    now_value = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def manifest_path_for(current: dict[str, Any]) -> Path | None:
        stored_path_value = str(current.get("stored_path", "") or "")
        return (PROJECT_ROOT / stored_path_value).parent / "manifest.json" if stored_path_value else None

    def build_mutation(
        current: dict[str, Any],
        manifest: dict[str, Any] | None,
    ) -> DocumentRecordMutation | None:
        previous = {
            field: safe_text(str(current.get(field, "") or ""))
            for field in DOCUMENT_METADATA_UPDATE_FIELDS
        }
        changed = {
            field: value
            for field, value in updates.items()
            if safe_text(str(current.get(field, "") or "")) != value
        }
        if not changed:
            return None
        updated = dict(current)
        updated.update(changed)
        updated["metadata_updated_at"] = now_value
        updated_manifest = None
        if manifest is not None:
            updated_manifest = dict(manifest)
            updated_manifest.update(updated)
        return DocumentRecordMutation(
            index_record=updated,
            manifest_record=updated_manifest,
            audit_record={
                "action": "update_classification_metadata",
                "document_id": str(current.get("document_id", "")),
                "previous": previous,
                "updated": {
                    field: safe_text(str(updated.get(field, "") or ""))
                    for field in DOCUMENT_METADATA_UPDATE_FIELDS
                },
                "changed_fields": sorted(changed),
                "created_at": now_value,
                "do_not_commit": True,
            },
        )

    try:
        transaction = transact_document_record(
            vault_dir=vault_dir,
            reference=safe_reference,
            row_selector=find_document_row_index_by_reference,
            manifest_path_resolver=manifest_path_for,
            mutation_builder=build_mutation,
            audit_path=vault_dir / "index" / "document_metadata_actions.jsonl",
            backup_group="metadata_backups",
            backup_path_labeler=lambda path: str(relative_to_project(path)),
        )
    except DocumentRecordNotFoundError:
        return {"ok": False, "message": "Dokument nebyl nalezen v indexu."}
    except DocumentTransactionError as exc:
        return {"ok": False, "message": f"Metadata dokumentu se nepodařilo bezpečně uložit: {exc}"}
    except OSError:
        return {"ok": False, "message": "Metadata dokumentu se nepodařilo bezpečně uložit kvůli I/O chybě."}

    current = transaction.previous_record
    updated = transaction.updated_record
    resolved_document_id = str(updated.get("document_id", ""))
    changed = {
        field: value
        for field, value in updates.items()
        if safe_text(str(current.get(field, "") or "")) != value
    }
    if not transaction.changed:
        return {
            "ok": True,
            "document_id": safe_text(resolved_document_id),
            "document_ref": document_reference(resolved_document_id),
            "message": "Metadata se nezměnila.",
            "document_classification": document_classification_status(vault_dir=vault_dir),
        }

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


def purchase_reference(purchase_id: str) -> str:
    digest = hashlib.sha256(purchase_id.encode("utf-8")).hexdigest()[:16]
    return f"purref-{digest}"


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

    now_value = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    safe_note = safe_text(note.strip())

    def manifest_path_for(current: dict[str, Any]) -> Path | None:
        stored_path_value = str(current.get("stored_path", "") or "")
        return (PROJECT_ROOT / stored_path_value).parent / "manifest.json" if stored_path_value else None

    def build_mutation(
        current: dict[str, Any],
        manifest: dict[str, Any] | None,
    ) -> DocumentRecordMutation:
        updated = {**current, **(manifest or {})}
        previous_status = effective_document_reading_status(updated)
        updated["reading_status"] = normalized_status
        updated["reading_status_updated_at"] = now_value
        if safe_note:
            updated["reading_status_note"] = safe_note
        return DocumentRecordMutation(
            index_record=updated,
            manifest_record=dict(updated) if manifest is not None else None,
            audit_record={
                "action": "set_reading_status",
                "document_id": str(current.get("document_id", "")),
                "previous_status": previous_status,
                "reading_status": normalized_status,
                "reading_status_label": READING_STATUS_LABELS[normalized_status],
                "note": safe_note,
                "created_at": now_value,
                "do_not_commit": True,
            },
        )

    try:
        transaction = transact_document_record(
            vault_dir=vault_dir,
            reference=safe_document_id,
            row_selector=find_document_row_index_by_reference,
            manifest_path_resolver=manifest_path_for,
            mutation_builder=build_mutation,
            audit_path=vault_dir / "index" / "document_reading_status_actions.jsonl",
            backup_group="status_backups",
            backup_path_labeler=lambda path: str(relative_to_project(path)),
        )
    except DocumentRecordNotFoundError:
        return {"ok": False, "message": "Dokument nebyl nalezen v indexu."}
    except DocumentTransactionError as exc:
        return {"ok": False, "message": f"Stav dokumentu se nepodařilo bezpečně uložit: {exc}"}
    except OSError:
        return {"ok": False, "message": "Stav dokumentu se nepodařilo bezpečně uložit kvůli I/O chybě."}

    resolved_document_id = str(transaction.updated_record.get("document_id", ""))
    return {
        "ok": True,
        "document_id": safe_text(resolved_document_id),
        "document_ref": document_reference(resolved_document_id),
        "reading_status": normalized_status,
        "reading_status_label": READING_STATUS_LABELS[normalized_status],
        "message": f"Stav dokumentu uložen: {READING_STATUS_LABELS[normalized_status]}.",
    }


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
        "--delay",
        "2.0",
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
    poll = getattr(process, "poll", None)
    if callable(poll):
        time.sleep(0.35)
        returncode = poll()
        if returncode is not None:
            write_voice_mode_status(
                state="stopped",
                message=f"Adam Voice Mode watcher po startu hned skončil (exit {returncode}).",
                pid=pid,
            )
            try:
                recent_log = "\n".join(log_file.read_text(encoding="utf-8").splitlines()[-20:])
            except OSError:
                recent_log = ""
            return {
                "ok": False,
                "status": "watcher_exited",
                "message": "Adam Voice Mode watcher po startu hned skončil. Zkontroluj log v Cockpitu.",
                "pid": pid,
                "returncode": returncode,
                "log": str(relative_to_project(log_file)),
                "recent_log": recent_log,
            }
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


def cockpit_codex_approval_clear_action(
    payload: dict[str, Any],
    *,
    clearer: Callable[..., dict[str, Any]] = clear_codex_approval_request,
    status_loader: Callable[..., dict[str, Any]] = load_voice_mode_status,
) -> dict[str, Any]:
    if not bool(payload.get("confirmed")):
        return {
            "ok": False,
            "status": "confirmation_required",
            "message": "Vyčištění karty Codex potvrzení vyžaduje potvrzení v Cockpitu.",
        }
    note = safe_text(str(payload.get("note") or "Vyčištěno z Cockpitu po ručním vyřešení."))[:500]
    result = clearer(note=note)
    return {
        "ok": bool(result.get("ok")),
        "status": result.get("status"),
        "message": "Karta čekání na Codex potvrzení byla vyčištěna.",
        "codex_approval": result,
        "voice_mode": status_loader(stale_after_seconds=60.0),
    }


SAFE_READONLY_CAPABILITIES: tuple[dict[str, str], ...] = (
    {
        "id": "codex_sessions",
        "label": "Codex relace",
        "summary": "Read-only kontrola aktivních Codex relací, TTY a voice bridge cíle.",
    },
    {
        "id": "voice_bridge",
        "label": "Voice bridge",
        "summary": "Read-only kontrola markeru, efektivního cíle a připravenosti terminálového bridge.",
    },
    {
        "id": "git_status",
        "label": "Git stav",
        "summary": "Read-only souhrn pracovního stromu bez commitování nebo pushování.",
    },
    {
        "id": "backup_status",
        "label": "Záloha",
        "summary": "Read-only souhrn poslední lokální zálohovací aktivity.",
    },
)


def cockpit_safe_readonly_capabilities_action() -> dict[str, Any]:
    return {
        "ok": True,
        "status": "available",
        "message": "Načtené jsou jen pevně povolené read-only kontroly.",
        "capabilities": [dict(item) for item in SAFE_READONLY_CAPABILITIES],
    }


def safe_readonly_codex_sessions_result() -> dict[str, Any]:
    sessions = discover_codex_process_sessions()
    bridge = adam_voice_bridge_status(orphaned_janicka_reporter=janicka_orphaned_codex_session_report)
    safe_sessions = [
        {
            "tty": safe_text(str(session.get("tty") or ""))[:40],
            "pids": [int(pid) for pid in session.get("pids", [])],
            "root_pids": [int(pid) for pid in session.get("root_pids", [])],
        }
        for session in sessions
    ]
    return {
        "ok": True,
        "summary": f"Nalezeno {len(safe_sessions)} Codex relací. Efektivní voice bridge cíl: {bridge.get('effective_tty') or 'nezjištěno'}.",
        "sessions": safe_sessions,
        "voice_bridge": bridge,
    }


def safe_readonly_voice_bridge_result() -> dict[str, Any]:
    bridge = adam_voice_bridge_status(orphaned_janicka_reporter=janicka_orphaned_codex_session_report)
    return {
        "ok": bool(bridge.get("ok", True)),
        "summary": str(bridge.get("message") or "Voice bridge stav načten."),
        "voice_bridge": bridge,
    }


def safe_readonly_git_status_result() -> dict[str, Any]:
    git = git_status_summary()
    return {
        "ok": bool(git.get("ok", True)),
        "summary": str(git.get("message") or "Git stav načten."),
        "git": git,
    }


def safe_readonly_backup_status_result() -> dict[str, Any]:
    backup = backup_activity_status()
    return {
        "ok": bool(backup.get("ok", True)),
        "summary": str(backup.get("message") or "Stav zálohy načten."),
        "backup": backup,
    }


def default_safe_readonly_handlers() -> dict[str, Callable[[], dict[str, Any]]]:
    return {
        "codex_sessions": safe_readonly_codex_sessions_result,
        "voice_bridge": safe_readonly_voice_bridge_result,
        "git_status": safe_readonly_git_status_result,
        "backup_status": safe_readonly_backup_status_result,
    }


def cockpit_safe_readonly_run_action(
    payload: dict[str, Any],
    *,
    handlers: dict[str, Callable[[], dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    capability_id = safe_slug(str(payload.get("capability_id") or ""), default="", limit=80).replace("-", "_")
    meta_by_id = {item["id"]: item for item in SAFE_READONLY_CAPABILITIES}
    if capability_id not in meta_by_id:
        return {
            "ok": False,
            "status": "unknown_capability",
            "message": "Tahle kontrola není v Cockpit allowlistu read-only schopností.",
            "capability_id": capability_id,
        }
    selected_handlers = handlers or default_safe_readonly_handlers()
    handler = selected_handlers.get(capability_id)
    if handler is None:
        return {
            "ok": False,
            "status": "handler_missing",
            "message": "Kontrola je v allowlistu, ale nemá registrovaný handler.",
            "capability": meta_by_id[capability_id],
        }
    try:
        result = handler()
    except Exception as exc:  # pragma: no cover - defensive boundary for UI endpoint
        return {
            "ok": False,
            "status": "capability_failed",
            "message": f"Read-only kontrola selhala: {exc}",
            "capability": meta_by_id[capability_id],
        }
    return {
        "ok": bool(result.get("ok", True)),
        "status": "completed",
        "message": str(result.get("summary") or "Read-only kontrola dokončena."),
        "capability": meta_by_id[capability_id],
        "result": result,
    }


DEV_RUNNER_ACTIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "cockpit_voice_tests",
        "label": "Testy Cockpit + voice",
        "summary": "Spustí cílené unittesty pro Cockpit, Adam voice mode a terminal bridge.",
        "command": [str(PROJECT_ROOT / ".venv" / "bin" / "python"), "-m", "unittest", "tests.test_cockpit", "tests.test_adam_voice_mode", "tests.test_terminal_bridge"],
        "timeout": 90,
    },
    {
        "id": "cockpit_py_compile",
        "label": "Python syntax",
        "summary": "Zkontroluje syntaxi hlavních Cockpit/voice Python souborů.",
        "command": [str(PROJECT_ROOT / ".venv" / "bin" / "python"), "-m", "py_compile", "app/cockpit.py", "app/speech/adam_voice_mode.py", "app/speech/terminal_bridge.py"],
        "timeout": 30,
    },
    {
        "id": "git_diff_check",
        "label": "Diff check",
        "summary": "Spustí git diff --check proti celému PythonMF repozitáři.",
        "command": ["/usr/bin/git", "-C", str(GIT_ROOT), "diff", "--check"],
        "timeout": 30,
    },
)


def cockpit_dev_runner_actions() -> dict[str, Any]:
    return {
        "ok": True,
        "status": "available",
        "message": "Načtené jsou jen pevně povolené vývojové akce.",
        "actions": [
            {key: item[key] for key in ("id", "label", "summary")}
            for item in DEV_RUNNER_ACTIONS
        ],
    }


def _dev_runner_output(text: str, *, limit: int = 12_000) -> str:
    return safe_multiline_text(str(text or ""), limit=limit)


def cockpit_dev_runner_run_action(
    payload: dict[str, Any],
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    action_id = safe_slug(str(payload.get("action_id") or ""), default="", limit=80).replace("-", "_")
    action_by_id = {item["id"]: item for item in DEV_RUNNER_ACTIONS}
    action = action_by_id.get(action_id)
    if action is None:
        return {
            "ok": False,
            "status": "unknown_action",
            "message": "Tahle vývojová akce není v Dev runner allowlistu.",
            "action_id": action_id,
        }

    started_at = datetime.now(timezone.utc).replace(microsecond=0)
    try:
        completed = runner(
            list(action["command"]),
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=int(action["timeout"]),
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "status": "timeout",
            "message": f"Vývojová akce překročila limit {action['timeout']} s.",
            "action": {key: action[key] for key in ("id", "label", "summary")},
            "stdout": _dev_runner_output(exc.stdout or ""),
            "stderr": _dev_runner_output(exc.stderr or ""),
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }
    except OSError as exc:
        return {
            "ok": False,
            "status": "runner_failed",
            "message": f"Vývojovou akci se nepodařilo spustit: {exc}",
            "action": {key: action[key] for key in ("id", "label", "summary")},
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }

    ok = completed.returncode == 0
    label = str(action["label"])
    return {
        "ok": ok,
        "status": "passed" if ok else "failed",
        "message": f"{label}: {'prošlo' if ok else 'selhalo'} (exit {completed.returncode}).",
        "action": {key: action[key] for key in ("id", "label", "summary")},
        "returncode": completed.returncode,
        "stdout": _dev_runner_output(completed.stdout),
        "stderr": _dev_runner_output(completed.stderr),
        "started_at": started_at.isoformat(),
        "finished_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


def cockpit_voice_latest_response_action(
    *,
    response_path: Path = ADAM_LAST_RESPONSE_PATH,
) -> dict[str, Any]:
    return load_last_adam_response(path=response_path)


def cockpit_voice_frontend_event_action(
    payload: dict[str, Any],
    *,
    events_path: Path = VOICE_FRONTEND_EVENTS_PATH,
    now: datetime | None = None,
) -> dict[str, Any]:
    kind = safe_ascii_slug(str(payload.get("kind") or ""), default="unknown", limit=80)
    raw_detail = payload.get("detail")
    detail = raw_detail if isinstance(raw_detail, dict) else {}
    safe_detail: dict[str, Any] = {}
    for key in ("ok", "status", "step", "text_chars", "audio_kb", "recorded_seconds", "url", "visibility"):
        if key in detail:
            value = detail[key]
            if isinstance(value, (bool, int, float)) or value is None:
                safe_detail[key] = value
            else:
                safe_detail[key] = safe_text(str(value))[:220]
    if "error" in detail:
        safe_detail["error"] = safe_text(str(detail.get("error") or ""))[:300]
    record = {
        "created_at": (now or datetime.now(timezone.utc)).replace(microsecond=0).isoformat(),
        "kind": kind,
        "detail": safe_detail,
    }
    append_jsonl(events_path, record)
    return {
        "ok": True,
        "status": "recorded",
        "message": "Technická událost hlasového frontendu byla zapsána.",
        "path": str(relative_to_project(events_path)),
    }


def open_terminal_command(
    command: str,
    label: str,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    script = (
        'tell application "Terminal"\n'
        "  activate\n"
        f'  do script "cd {shell_quote_for_applescript(str(PROJECT_ROOT))}; {command}"\n'
        "end tell\n"
    )
    try:
        completed = runner(
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


def janicka_full_adam_prompt() -> str:
    return """Jsi plný Adam/Codex pro Janu, otevřený z nouzového tlačítka `Janička`.

Odpovídej česky, jednoduše a prakticky. Jana nemusí znát žádnou syntaxi příkazů.
Když Jana napíše běžnou větou, co potřebuje, nejdřív vysvětli nejbližší bezpečný krok a pak ho podle možností proveď.

Bezpečnost:
- Čtení a hledání dokumentů/e-mailů je v pořádku.
- Nic neposílej, nemaž, nepřesouvej, neplať a neměň účty bez jasného potvrzení.
- Pokud je potřeba technický příkaz, nečekej, že ho Jana zná; navrhni ho sám a vysvětli, co udělá.
- Citlivé texty neopisuj zbytečně do chatu ani do gitu.

Začni krátkou větou pro Janu: `Jano, jsem plný Adam. Piš normální větou, co potřebuješ; příkazy znát nemusíš.`"""


def open_janicka_full_adam_action(
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    codex_bin = shutil.which("codex") or "/usr/local/bin/codex"
    prompt = janicka_full_adam_prompt()
    command = (
        "source ~/.zshrc; "
        "echo 'Oteviram plneho Adama pro Janu.'; "
        "echo 'Az se Adam ozve, pis normalni vetou. Prikazy znat nemusis.'; "
        f"{shell_quote_for_applescript(codex_bin)} --no-alt-screen -C {shell_quote_for_applescript(str(PROJECT_ROOT))} "
        f"{shell_quote_for_applescript(prompt)}"
    )
    result = open_terminal_command(command, "Nouzový plný Adam", runner=runner)
    manual_steps = [
        "Když se okno neotevře, otevři aplikaci Terminal.",
        f"Do Terminalu napiš: cd {PROJECT_ROOT}",
        "Potom napiš: codex --no-alt-screen",
        "Až se Adam spustí, napiš běžnou větou, co potřebuješ. Příkazy znát nemusíš.",
    ]
    return {
        **result,
        "status": "terminal_opened" if result.get("ok") else "terminal_open_failed",
        "manual_command": f"cd {PROJECT_ROOT} && codex --no-alt-screen",
        "manual_steps": manual_steps,
        "message": (
            "Otevřel jsem plného Adama. Do nového okna může Jana psát normální větou; příkazy znát nemusí."
            if result.get("ok")
            else f"{result.get('message', 'Terminál se nepodařilo otevřít')} Ruční postup je zobrazený v Janičce."
        ),
    }


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


def deliver_saved_voice_command_inline(
    *,
    inbox_dir: Path = VOICE_COMMAND_INBOX_DIR,
    terminal_bridge: Callable[..., dict[str, Any]] | None = None,
    pending_path: Path = ADAM_PENDING_COMMAND_PATH,
    history_path: Path = ADAM_VOICE_HISTORY_PATH,
) -> dict[str, Any]:
    try:
        command = parse_voice_command_file(inbox_dir / "latest_voice_command.md")
    except OSError as exc:
        return {
            "voice_delivery_status": "voice_command_not_loaded",
            "voice_delivery": {"ok": False, "message": str(exc)},
            "voice_delivery_message": f"Hlasový pokyn byl uložen, ale nejde načíst pro okamžité předání: {exc}",
        }

    bridge = terminal_bridge or deliver_voice_command_by_configured_transport
    bridge_result = bridge(command)
    if bridge_result.get("ok") and bridge_result.get("verified"):
        status = "voice_command_delivered"
        message = "Hlasový pokyn byl uložen a předán přímo do Codexu."
    elif bridge_result.get("ok"):
        status = "voice_command_delivery_unverified"
        message = (
            "Zpráva byla vložena do hlasového inboxu. "
            "Čekám na Adamovu odpověď."
        )
    else:
        bridge_status = str(bridge_result.get("status") or "voice_command_delivery_failed")
        bridge_message = str(bridge_result.get("reason") or bridge_result.get("message") or "bez detailu")
        status = bridge_status
        message = f"Hlasový pokyn byl uložen, ale okamžité předání do Codexu neproběhlo: {bridge_message}"
    record_voice_delivery_attempt(
        command=command,
        bridge_result=bridge_result,
        delivery_status=status,
        message=message,
        inbox_dir=inbox_dir,
    )
    if status != "voice_command_delivered":
        record_voice_delivery_issue_for_cockpit(
            command=command,
            bridge_result=bridge_result,
            delivery_status=status,
            message=message,
            pending_path=pending_path,
            history_path=history_path,
        )
    return {
        "voice_delivery_status": status,
        "voice_delivery": bridge_result,
        "voice_delivery_message": message,
    }


def voice_watcher_will_deliver_result(voice_mode: dict[str, Any]) -> dict[str, Any]:
    return {
        "voice_delivery_status": "watcher_will_deliver",
        "voice_delivery": {
            "ok": True,
            "status": "watcher_running",
            "message": "Běžící Adam Voice Mode watcher pokyn převezme z hlasového inboxu.",
        },
        "voice_delivery_message": (
            "Zpráva byla vložena do hlasového inboxu. "
            "Běžící watcher ji předá Adamovi."
        ),
        "voice_mode": voice_mode,
    }


def record_voice_delivery_attempt(
    *,
    command: VoiceCommand,
    bridge_result: dict[str, Any],
    delivery_status: str,
    message: str,
    inbox_dir: Path = VOICE_COMMAND_INBOX_DIR,
) -> None:
    try:
        append_jsonl(
            inbox_dir / "delivery_attempts.jsonl",
            {
                "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                "command_created_at": command.created_at,
                "command_path": str(relative_to_project(Path(command.path))),
                "text_chars": len(command.text.strip()),
                "delivery_status": delivery_status,
                "bridge_status": str(bridge_result.get("status") or ""),
                "ok": bool(bridge_result.get("ok")),
                "verified": bool(bridge_result.get("verified")),
                "voice_transport": str(bridge_result.get("voice_transport") or ""),
                "delivery_method": str(bridge_result.get("delivery_method") or ""),
                "target_tty": str(bridge_result.get("target_tty") or ""),
                "target_ttys": bridge_result.get("target_ttys") or [],
                "message": safe_text(message)[:800],
            },
        )
    except OSError:
        return


def record_voice_delivery_issue_for_cockpit(
    *,
    command: VoiceCommand,
    bridge_result: dict[str, Any],
    delivery_status: str,
    message: str,
    pending_path: Path = ADAM_PENDING_COMMAND_PATH,
    history_path: Path = ADAM_VOICE_HISTORY_PATH,
) -> None:
    detail = str(bridge_result.get("reason") or bridge_result.get("message") or "").strip()
    pending_message = message if not detail else f"{message} Detail: {detail}"
    pending_reason = (
        "terminal_delivery_pending_reply"
        if delivery_status == "voice_command_delivery_unverified"
        else delivery_status
    )
    try:
        save_pending_for_adam(
            command,
            reason=pending_reason,
            message=pending_message,
            path=pending_path,
            history_path=history_path,
        )
        append_voice_history_turn(command, adam_response=message, route=pending_reason, path=history_path)
    except OSError:
        return


def selected_voice_delivery_transport() -> str:
    transport = os.environ.get(VOICE_DELIVERY_TRANSPORT_ENV, "local_tty").strip().lower()
    if transport in {"local", "local_tty", "tty", "mac", "mac_tty", "terminal"}:
        return "local_tty"
    if transport in {"screen", "ssh", "sslh", "managed", "managed_screen"}:
        return "managed_screen"
    return "managed_screen"


def deliver_voice_command_via_managed_screen(
    command: VoiceCommand,
    *,
    submit: bool = True,
    starter: Callable[..., dict[str, Any]] | None = None,
    ready_waiter: Callable[[], dict[str, Any]] | None = None,
    screen_deliverer: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    starter = starter or start_adam_service
    ready_waiter = ready_waiter or wait_for_adam_ready
    screen_deliverer = screen_deliverer or deliver_prompt_to_adam_screen
    decision = assess_terminal_bridge(command)
    if not decision.get("ok"):
        return {
            **decision,
            "voice_transport": "managed_screen",
            "command": voice_command_to_dict(command),
        }
    start_result = starter()
    if not start_result.get("ok"):
        return {
            "ok": False,
            "status": "managed_screen_start_failed",
            "message": str(start_result.get("message") or "Spravovanou Adamovu screen relaci se nepodařilo spustit."),
            "voice_transport": "managed_screen",
            "start": start_result,
            "decision": decision,
            "command": voice_command_to_dict(command),
        }
    ready_result: dict[str, Any] = {"ready": True, "message": "Spravovaná Adamova relace už běžela."}
    if start_result.get("status") in {"start_requested", "restart_requested"}:
        ready_result = ready_waiter()
    prompt = build_codex_terminal_prompt(command)
    delivery = screen_deliverer(prompt, submit=submit)
    message = str(delivery.get("message") or "")
    if delivery.get("ok") and not ready_result.get("ready", True):
        ready_message = str(ready_result.get("message") or "připravenost se nepodařilo ověřit")
        message = f"{message} Pozor: {ready_message}"
    return {
        **delivery,
        "message": message or ("Pokyn byl vložen do spravované Adamovy screen relace." if delivery.get("ok") else "Doručení do spravované Adamovy screen relace selhalo."),
        "voice_transport": "managed_screen",
        "prompt": prompt,
        "decision": decision,
        "start": start_result,
        "ready": ready_result,
        "command": voice_command_to_dict(command),
    }


def deliver_voice_command_by_configured_transport(command: VoiceCommand, *, submit: bool = True) -> dict[str, Any]:
    transport = selected_voice_delivery_transport()
    if transport == "local_tty":
        result = deliver_voice_command_to_terminal(command, submit=submit)
        return {**result, "voice_transport": "local_tty"}
    return deliver_voice_command_via_managed_screen(command, submit=submit)


def transcribe_audio_base64_isolated(
    audio_base64: str,
    *,
    mime_type: str,
    language: str = "cs",
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    timeout_seconds: int = 90,
    temp_dir: Path | str = "/private/tmp",
) -> dict[str, Any]:
    safe_mime_type = normalize_mime_type(mime_type)
    audio_bytes = decode_audio_base64(audio_base64)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix="samantha_cockpit_voice_",
            suffix=MIME_EXTENSIONS[safe_mime_type],
            dir=str(temp_dir),
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(audio_bytes)
        completed = runner(
            [
                str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                str(PROJECT_ROOT / "app" / "speech" / "transcribe.py"),
                "--audio-file",
                str(temp_path),
                "--mime-type",
                safe_mime_type,
                "--language",
                language,
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise TranscriptionError("Přepis hlasu překročil časový limit.") from exc
    except OSError as exc:
        raise TranscriptionError(f"Izolovaný přepis hlasu se nepodařilo spustit: {exc}") from exc
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    try:
        result = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError as exc:
        detail = stderr or stdout[:500] or f"exit {completed.returncode}"
        raise TranscriptionError(f"Izolovaný přepis vrátil nečitelný výsledek: {detail}") from exc
    if completed.returncode != 0 or not result.get("ok"):
        message = str(result.get("message") or stderr or f"exit {completed.returncode}")
        raise TranscriptionError(message)
    return result


def record_voice_transcription_failure(
    *,
    message: str,
    status: str = "transcription_failed",
    events_path: Path | None = None,
) -> None:
    try:
        append_jsonl(
            events_path or VOICE_FRONTEND_EVENTS_PATH,
            {
                "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                "kind": "backend_transcribe_failed",
                "detail": {
                    "ok": False,
                    "status": status,
                    "step": "transcribe",
                    "error": safe_text(message)[:500],
                },
            },
        )
    except OSError:
        return


def cockpit_transcribe_voice_action(
    payload: dict[str, Any],
    *,
    inbox_dir: Path = VOICE_COMMAND_INBOX_DIR,
    terminal_bridge: Callable[..., dict[str, Any]] | None = None,
    pending_path: Path = ADAM_PENDING_COMMAND_PATH,
    history_path: Path = ADAM_VOICE_HISTORY_PATH,
    transcriber: Callable[..., dict[str, Any]] = transcribe_audio_base64_isolated,
) -> dict[str, Any]:
    try:
        result = transcriber(
            str(payload.get("audio_base64", "")),
            mime_type=str(payload.get("mime_type", "")),
            language=str(payload.get("language", "cs") or "cs"),
        )
        result.update(save_voice_command_to_inbox(result, inbox_dir=inbox_dir))
        if terminal_bridge is None:
            voice_mode = load_voice_mode_status()
            if voice_mode.get("running"):
                result.update(voice_watcher_will_deliver_result(voice_mode))
                result["message"] = result["voice_delivery_message"]
                return result
        result.update(
            deliver_saved_voice_command_inline(
                inbox_dir=inbox_dir,
                terminal_bridge=terminal_bridge,
                pending_path=pending_path,
                history_path=history_path,
            )
        )
        result["message"] = result.get("voice_delivery_message") or "Hlasový pokyn byl přepsán a uložen pro Codex."
        return result
    except TranscriptionError as exc:
        record_voice_transcription_failure(message=str(exc))
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
    terminal_bridge: Callable[..., dict[str, Any]] | None = None,
    pending_path: Path = ADAM_PENDING_COMMAND_PATH,
    history_path: Path = ADAM_VOICE_HISTORY_PATH,
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
        voice_mode = load_voice_mode_status()
        if terminal_bridge is None and voice_mode.get("running"):
            result.update(voice_watcher_will_deliver_result(voice_mode))
            result["message"] = result["voice_delivery_message"]
            return result
        result.update(
            deliver_saved_voice_command_inline(
                inbox_dir=inbox_dir,
                terminal_bridge=terminal_bridge,
                pending_path=pending_path,
                history_path=history_path,
            )
        )
        result["message"] = result.get("voice_delivery_message") or result["message"]
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
    service_submitter: Callable[..., dict[str, Any]] = submit_janicka_text_request,
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
        "Dotaz jsem předal Adamovi v light Samantha relaci. Pokud ještě neběžela, Cockpit ji zkusil spustit. "
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


JANICKA_ORPHAN_SIGNATURES = (
    "Jsi lehká Samantha/Adam relace pro okno Janička",
    "jen čekej na textové dotazy z Janičky",
)


def janicka_orphaned_codex_session_report(
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    managed_codex_tty_labeler: Callable[[], dict[str, str]] | None = None,
) -> dict[str, Any]:
    sessions = discover_codex_process_sessions(runner=runner)
    try:
        managed_labels = managed_codex_tty_labeler() if managed_codex_tty_labeler else managed_codex_session_tty_labels()
    except Exception:
        managed_labels = {}
    managed_ttys = {normalize_tty(str(tty)) for tty in managed_labels if normalize_tty(str(tty))}
    orphaned: list[dict[str, Any]] = []
    for session in sessions:
        tty = normalize_tty(str(session.get("tty") or ""))
        if not tty or tty in managed_ttys:
            continue
        command_text = "\n".join(str(command or "") for command in session.get("commands", []))
        folded_command = command_text.casefold()
        if not all(signature.casefold() in folded_command for signature in JANICKA_ORPHAN_SIGNATURES):
            continue
        orphaned.append(
            {
                "tty": tty,
                "pids": [int(pid) for pid in session.get("pids", [])],
                "root_pids": [int(pid) for pid in session.get("root_pids", [])],
            }
        )
    return {
        "ok": True,
        "status": "orphaned_found" if orphaned else "none",
        "message": (
            "Nalezené staré Janička Codex relace mimo správu: "
            + ", ".join(item["tty"] for item in orphaned)
            if orphaned
            else "Žádné staré Janička Codex relace mimo správu nejsou nalezené."
        ),
        "orphaned_ttys": [item["tty"] for item in orphaned],
        "orphaned_count": len(orphaned),
        "orphaned_sessions": orphaned,
        "managed_codex_ttys": sorted(managed_ttys),
    }


def janicka_light_status_action(
    *,
    status_getter: Callable[[], dict[str, Any]] = janicka_light_status,
    orphan_reporter: Callable[[], dict[str, Any]] = janicka_orphaned_codex_session_report,
) -> dict[str, Any]:
    status = status_getter()
    try:
        orphan_report = orphan_reporter()
    except Exception as exc:
        return {
            **status,
            "orphaned_janicka_check_ok": False,
            "orphaned_janicka_message": f"Kontrola starých Janička relací selhala: {exc}",
            "orphaned_janicka_ttys": [],
            "orphaned_janicka_count": 0,
        }
    orphaned_ttys = [safe_text(str(tty))[:40] for tty in orphan_report.get("orphaned_ttys", [])]
    if orphaned_ttys:
        base_message = str(status.get("message") or "").rstrip()
        status["message"] = (
            f"{base_message} Pozor: staré Janička relace mimo správu: {', '.join(orphaned_ttys)}."
            if base_message
            else f"Pozor: staré Janička relace mimo správu: {', '.join(orphaned_ttys)}."
        )
    return {
        **status,
        "orphaned_janicka_check_ok": bool(orphan_report.get("ok", True)),
        "orphaned_janicka_message": str(orphan_report.get("message") or ""),
        "orphaned_janicka_ttys": orphaned_ttys,
        "orphaned_janicka_count": int(orphan_report.get("orphaned_count") or 0),
    }


def terminate_orphaned_janicka_sessions_action(
    payload: dict[str, Any],
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    managed_codex_tty_labeler: Callable[[], dict[str, str]] | None = None,
    marker_path: Path = CURRENT_CODEX_TTY_PATH,
    killer: Callable[[int, int], None] = os.kill,
) -> dict[str, Any]:
    confirmed = bool(payload.get("confirmed"))
    report = janicka_orphaned_codex_session_report(
        runner=runner,
        managed_codex_tty_labeler=managed_codex_tty_labeler,
    )
    orphaned_sessions = list(report.get("orphaned_sessions", []))
    if not orphaned_sessions:
        return {
            **report,
            "ok": True,
            "status": "no_orphaned_janicka_sessions",
            "message": "Žádné staré Janička relace mimo správu k ukončení.",
        }

    protected_ttys = set(report.get("managed_codex_ttys", []))
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        marked_tty = normalize_tty(str(marker.get("tty") or ""))
        if marked_tty:
            protected_ttys.add(marked_tty)
    except (OSError, json.JSONDecodeError):
        marked_tty = ""

    killable_sessions = [session for session in orphaned_sessions if session.get("tty") not in protected_ttys]
    protected_orphaned_ttys = [
        str(session.get("tty") or "")
        for session in orphaned_sessions
        if session.get("tty") in protected_ttys
    ]
    if protected_orphaned_ttys and not killable_sessions:
        return {
            **report,
            "ok": False,
            "status": "protected_by_voice_marker",
            "message": (
                "Staré Janička relace jsou teď chráněné voice markerem. "
                "Nejdřív nastav VoiceBridge na hlavního Adama, potom cleanup zopakuj."
            ),
            "protected_ttys": sorted(protected_ttys),
            "protected_orphaned_ttys": protected_orphaned_ttys,
        }

    stale_ttys = [str(session.get("tty") or "") for session in killable_sessions]
    root_pids = sorted({int(pid) for session in killable_sessions for pid in session.get("root_pids", [])})
    if not confirmed:
        return {
            **report,
            "ok": False,
            "status": "confirmation_required",
            "message": f"K ukončení jsou připravené staré Janička relace: {', '.join(stale_ttys)}.",
            "stale_ttys": stale_ttys,
            "root_pids": root_pids,
            "protected_ttys": sorted(protected_ttys),
            "protected_orphaned_ttys": protected_orphaned_ttys,
        }

    killed: list[int] = []
    errors: list[str] = []
    for pid in root_pids:
        try:
            killer(pid, signal.SIGTERM)
            killed.append(pid)
        except OSError as exc:
            errors.append(f"PID {pid}: {exc}")
    if errors:
        return {
            **report,
            "ok": False,
            "status": "partial_or_failed",
            "message": f"Některé staré Janička relace se nepodařilo ukončit: {' | '.join(errors)}",
            "stale_ttys": stale_ttys,
            "killed_pids": killed,
            "errors": errors,
            "protected_ttys": sorted(protected_ttys),
        }
    return {
        **report,
        "ok": True,
        "status": "orphaned_janicka_sessions_terminated",
        "message": f"Ukončil jsem staré Janička relace mimo správu: {', '.join(stale_ttys)}.",
        "stale_ttys": stale_ttys,
        "killed_pids": killed,
        "protected_ttys": sorted(protected_ttys),
        "protected_orphaned_ttys": protected_orphaned_ttys,
    }


def shell_quote_for_applescript(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


COCKPIT_POST_ACTIONS: tuple[dict[str, str], ...] = (
    {
        "path": "/api/scandocu/open",
        "label": "Otevrit ScanDocu",
        "risk": "local_service",
        "confirmation": "allowlist_only",
        "handler_name": "start_scandocu",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/terminal/open",
        "label": "Otevrit terminal v projektu",
        "risk": "local_open",
        "confirmation": "fixed_project_path",
        "handler_name": "open_project_terminal",
        "test_level": "indirect",
    },
    {
        "path": "/api/speech/speak",
        "label": "macOS hlasovy vystup",
        "risk": "local_open",
        "confirmation": "none_local_audio",
        "handler_name": "cockpit_speak_action",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/speech/edge-tts",
        "label": "Edge TTS audio",
        "risk": "local_open",
        "confirmation": "none_local_audio",
        "handler_name": "cockpit_edge_tts_action",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/speech/transcribe",
        "label": "Prepis a doruceni hlasoveho pokynu",
        "risk": "voice_local_outbound",
        "confirmation": "terminal_bridge_triage",
        "handler_name": "cockpit_transcribe_voice_action",
        "test_level": "voice_tests",
    },
    {
        "path": "/api/speech/voice-text",
        "label": "Doruceni textoveho hlasoveho pokynu",
        "risk": "voice_local_outbound",
        "confirmation": "terminal_bridge_triage",
        "handler_name": "cockpit_save_voice_text_action",
        "test_level": "voice_tests",
    },
    {
        "path": "/api/voice-bridge/frontend-event",
        "label": "Technicky voice frontend event",
        "risk": "private_write",
        "confirmation": "technical_event_no_content",
        "handler_name": "cockpit_voice_frontend_event_action",
        "test_level": "direct",
    },
    {
        "path": "/api/janicka/chat",
        "label": "Janička chat s Adamem",
        "risk": "voice_local_outbound",
        "confirmation": "managed_adam_route",
        "handler_name": "janicka_chat_action",
        "test_level": "direct",
    },
    {
        "path": "/api/janicka/chat/latest",
        "label": "Posledni Janička odpoved",
        "risk": "read_only_via_post",
        "confirmation": "none_readonly",
        "handler_name": "janicka_latest_codex_reply_action",
        "test_level": "direct",
    },
    {
        "path": "/api/adam/status",
        "label": "Adam status",
        "risk": "read_only_via_post",
        "confirmation": "none_readonly",
        "handler_name": "adam_service_status",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/adam/start",
        "label": "Spustit Adama",
        "risk": "local_service",
        "confirmation": "fixed_workflow",
        "handler_name": "start_adam_service",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/adam/restart",
        "label": "Restartovat Adama",
        "risk": "local_service",
        "confirmation": "ui_confirm_boolean",
        "handler_name": "restart_adam_service",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/adam/stop",
        "label": "Zastavit Adama",
        "risk": "local_service",
        "confirmation": "ui_confirm_boolean",
        "handler_name": "stop_adam_service",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/janicka/light/status",
        "label": "Janička light Samantha status",
        "risk": "read_only_via_post",
        "confirmation": "none_readonly",
        "handler_name": "janicka_light_status_action",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/janicka/light/start",
        "label": "Spustit Janička light Samantha",
        "risk": "local_service",
        "confirmation": "fixed_workflow",
        "handler_name": "start_janicka_light_session",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/janicka/light/stop",
        "label": "Zastavit Janička light Samantha",
        "risk": "local_service",
        "confirmation": "ui_confirm_boolean",
        "handler_name": "stop_janicka_light_session",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/janicka/light/cleanup-orphans",
        "label": "Ukoncit stare Janicka relace mimo spravu",
        "risk": "local_service",
        "confirmation": "ui_confirm_boolean",
        "handler_name": "terminate_orphaned_janicka_sessions_action",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/voice-mode/start",
        "label": "Spustit voice watcher",
        "risk": "local_service",
        "confirmation": "fixed_workflow",
        "handler_name": "start_adam_voice_mode_action",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/voice-mode/stop",
        "label": "Zastavit voice watcher",
        "risk": "local_service",
        "confirmation": "pid_exists",
        "handler_name": "stop_adam_voice_mode_action",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/voice-mode/approval",
        "label": "Schvalit hlasovy pokyn",
        "risk": "private_write",
        "confirmation": "approval_decision_payload",
        "handler_name": "cockpit_voice_approval_action",
        "test_level": "voice_tests",
    },
    {
        "path": "/api/voice-mode/codex-approval/clear",
        "label": "Vycistit Codex approval kartu",
        "risk": "private_write",
        "confirmation": "ui_confirm_boolean",
        "handler_name": "cockpit_codex_approval_clear_action",
        "test_level": "direct",
    },
    {
        "path": "/api/voice-mode/safe-readonly/run",
        "label": "Spustit read-only kontrolu",
        "risk": "read_only_via_post",
        "confirmation": "allowlist_only",
        "handler_name": "cockpit_safe_readonly_run_action",
        "test_level": "direct",
    },
    {
        "path": "/api/dev-runner/run",
        "label": "Spustit dev runner akci",
        "risk": "dev_runner",
        "confirmation": "allowlist_argv_only",
        "handler_name": "cockpit_dev_runner_run_action",
        "test_level": "direct",
    },
    {
        "path": "/api/desktop-apps/open",
        "label": "Otevrit desktop aplikaci",
        "risk": "local_open",
        "confirmation": "allowlist_only",
        "handler_name": "open_desktop_app_action",
        "test_level": "direct",
    },
    {
        "path": "/api/voice-bridge/marker",
        "label": "Nastavit voice bridge marker",
        "risk": "private_write",
        "confirmation": "active_tty_validation",
        "handler_name": "set_adam_voice_bridge_marker_action",
        "test_level": "direct",
    },
    {
        "path": "/api/voice-bridge/terminate-stale",
        "label": "Ukoncit stare Codex relace",
        "risk": "local_service",
        "confirmation": "preview_then_ui_confirm",
        "handler_name": "terminate_stale_codex_sessions_action",
        "test_level": "direct",
    },
    {
        "path": "/api/cockpit/restart",
        "label": "Restartovat Cockpit",
        "risk": "local_service",
        "confirmation": "ui_confirm_boolean",
        "handler_name": "start_cockpit_restart_action",
        "test_level": "direct",
    },
    {
        "path": "/api/session-autosave/cleanup",
        "label": "Uklidit stare autosave snapshoty",
        "risk": "delete_or_purge",
        "confirmation": "ui_confirm_plus_exact_phrase",
        "handler_name": "session_autosave_cleanup_action",
        "test_level": "direct",
    },
    {
        "path": "/api/projects/lifecycle",
        "label": "Zmenit stav projektu",
        "risk": "private_write",
        "confirmation": "ui_confirm_boolean",
        "handler_name": "project_lifecycle_action",
        "test_level": "direct",
    },
    {
        "path": "/api/samantha/open",
        "label": "Otevrit Samantha chat",
        "risk": "local_open",
        "confirmation": "fixed_terminal_command",
        "handler_name": "open_samantha_chat",
        "test_level": "indirect",
    },
    {
        "path": "/api/codex/open",
        "label": "Otevrit Codex CLI",
        "risk": "local_open",
        "confirmation": "fixed_terminal_command",
        "handler_name": "open_codex_cli",
        "test_level": "indirect",
    },
    {
        "path": "/api/janicka/full-adam/open",
        "label": "Janička nouzove otevrit plneho Adama",
        "risk": "local_open",
        "confirmation": "fixed_terminal_command",
        "handler_name": "open_janicka_full_adam_action",
        "test_level": "direct",
    },
    {
        "path": "/api/reminders/done",
        "label": "Oznacit pripominku jako splnenou",
        "risk": "private_write",
        "confirmation": "helper_exact_phrase",
        "handler_name": "mark_reminder_done_action",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/reminders/cancel-payment",
        "label": "Zrusit platebni pripominku",
        "risk": "private_write",
        "confirmation": "none_backend",
        "handler_name": "cancel_payment_reminder_action",
        "test_level": "indirect",
    },
    {
        "path": "/api/urgent-reminders/done",
        "label": "Oznacit urgentni pripominku jako splnenou",
        "risk": "private_write",
        "confirmation": "none_backend",
        "handler_name": "urgent_reminder_done_action",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/consistency/resolve-finding",
        "label": "Vyresit consistency nalez",
        "risk": "private_write",
        "confirmation": "ui_confirm_boolean",
        "handler_name": "resolve_consistency_finding_action",
        "test_level": "direct",
    },
    {
        "path": "/api/reminders/source",
        "label": "Nacist zdroj pripominky",
        "risk": "read_only_via_post",
        "confirmation": "none_readonly",
        "handler_name": "reminder_source_detail_action",
        "test_level": "direct",
    },
    {
        "path": "/api/documents/open",
        "label": "Otevrit PDF dokument",
        "risk": "local_open",
        "confirmation": "safe_document_id",
        "handler_name": "open_document_pdf_action",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/documents/print/prepare",
        "label": "Pripravit tisk dokumentu",
        "risk": "print",
        "confirmation": "preflight_only",
        "handler_name": "prepare_document_print_action",
        "test_level": "direct",
    },
    {
        "path": "/api/documents/print/run",
        "label": "Spustit tisk dokumentu",
        "risk": "print",
        "confirmation": "exact_phrase",
        "handler_name": "run_document_print_action",
        "test_level": "direct",
    },
    {
        "path": "/api/documents/lifecycle",
        "label": "Archivovat nebo presunout dokument do kose",
        "risk": "delete_or_purge",
        "confirmation": "exact_phrase",
        "handler_name": "move_document_lifecycle_action",
        "test_level": "direct",
    },
    {
        "path": "/api/documents/reading-status",
        "label": "Zapsat stav cteni dokumentu",
        "risk": "private_write",
        "confirmation": "none_backend",
        "handler_name": "set_document_reading_status_action",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/library/archive",
        "label": "Ulozit URL do knihovny",
        "risk": "private_write",
        "confirmation": "validated_url",
        "handler_name": "library_archive_url_action",
        "test_level": "direct",
    },
    {
        "path": "/api/library/text",
        "label": "Ulozit text do knihovny",
        "risk": "private_write",
        "confirmation": "validated_text",
        "handler_name": "library_archive_text_action",
        "test_level": "direct",
    },
    {
        "path": "/api/library/attachment/add",
        "label": "Pripojit obrazek ke knihovne",
        "risk": "private_write",
        "confirmation": "helper_exact_phrase",
        "handler_name": "library_attach_image_action",
        "test_level": "direct",
    },
    {
        "path": "/api/library/delete",
        "label": "Vyradit polozku knihovny",
        "risk": "delete_or_purge",
        "confirmation": "user_confirmed_text",
        "handler_name": "library_delete_article_action",
        "test_level": "direct",
    },
    {
        "path": "/api/lekarna/retire/preview",
        "label": "Nahled vyrazeni leku",
        "risk": "read_only_via_post",
        "confirmation": "none_readonly",
        "handler_name": "lekarna_retire_preview_action",
        "test_level": "direct",
    },
    {
        "path": "/api/lekarna/retire/apply",
        "label": "Vyradit lek",
        "risk": "private_write",
        "confirmation": "exact_phrase",
        "handler_name": "lekarna_retire_apply_action",
        "test_level": "direct",
    },
    {
        "path": "/api/lekarna/import/draft",
        "label": "Pripravit lekarna import draft",
        "risk": "external_ai",
        "confirmation": "exact_phrase_for_openai",
        "handler_name": "lekarna_auto_import_draft_action",
        "test_level": "direct",
    },
    {
        "path": "/api/lekarna/import/manifest/load",
        "label": "Nacist lekarna import manifest ke kontrole",
        "risk": "read_only_via_post",
        "confirmation": "none_readonly",
        "handler_name": "lekarna_import_manifest_load_action",
        "test_level": "direct",
    },
    {
        "path": "/api/lekarna/import/manifest/save",
        "label": "Ulozit opraveny lekarna import manifest",
        "risk": "private_write",
        "confirmation": "none_backend_draft_only",
        "handler_name": "lekarna_import_manifest_save_action",
        "test_level": "direct",
    },
    {
        "path": "/api/lekarna/import/manifest/retry-pil",
        "label": "Zkusit znovu nacist PIL pro lekarna import",
        "risk": "private_write",
        "confirmation": "none_backend_draft_only",
        "handler_name": "lekarna_import_manifest_retry_pil_action",
        "test_level": "direct",
    },
    {
        "path": "/api/lekarna/import/apply",
        "label": "Prijmout lekarna import na sklad",
        "risk": "private_write",
        "confirmation": "exact_phrase",
        "handler_name": "lekarna_auto_import_apply_action",
        "test_level": "direct",
    },
    {
        "path": "/api/library/read-state",
        "label": "Zapsat stav cteni clanku",
        "risk": "private_write",
        "confirmation": "none_backend",
        "handler_name": "library_read_state_action",
        "test_level": "direct",
    },
    {
        "path": "/api/library/export/prepare",
        "label": "Pripravit PDF export knihovny",
        "risk": "private_write",
        "confirmation": "prepare_only",
        "handler_name": "library_prepare_pdf_export_action",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/library/export/send",
        "label": "Odeslat PDF export knihovny",
        "risk": "external_send",
        "confirmation": "exact_phrase",
        "handler_name": "library_send_pdf_export_action",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/documents/classification-metadata",
        "label": "Zapsat metadata dokumentu",
        "risk": "private_write",
        "confirmation": "ui_confirm_only",
        "handler_name": "update_document_classification_metadata_action",
        "test_level": "direct",
    },
    {
        "path": "/api/documents/classification-suggestion/accept",
        "label": "Prijmout navrh metadata dokumentu",
        "risk": "private_write",
        "confirmation": "ui_confirm_boolean",
        "handler_name": "accept_document_classification_suggestion_action",
        "test_level": "direct",
    },
    {
        "path": "/api/documents/due-reminder",
        "label": "Vytvorit pripominku z dokumentu",
        "risk": "private_write",
        "confirmation": "ui_confirm_boolean",
        "handler_name": "create_document_due_reminder_action",
        "test_level": "direct",
    },
    {
        "path": "/api/documents/intake-email-scan",
        "label": "Nacist e-mail intake kandidaty",
        "risk": "read_only_via_post",
        "confirmation": "none_readonly",
        "handler_name": "document_intake_email_scan_status",
        "test_level": "direct",
    },
    {
        "path": "/api/email-processing/decision",
        "label": "Ulozit pracovni rozhodnuti k e-mailu",
        "risk": "private_write",
        "confirmation": "none_backend",
        "handler_name": "save_email_processing_decision",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/email-processing/read-message",
        "label": "Nacist detail e-mailu",
        "risk": "read_only_via_post",
        "confirmation": "none_readonly",
        "handler_name": "read_email_processing_message_detail",
        "test_level": "direct",
    },
    {
        "path": "/api/email-processing/preview-attachment",
        "label": "Nacist preview e-mail prilohy",
        "risk": "read_only_via_post",
        "confirmation": "none_readonly",
        "handler_name": "preview_email_work_queue_attachment_action",
        "test_level": "ui_presence",
    },
    {
        "path": "/api/project-audit/save",
        "label": "Ulozit systemovy audit",
        "risk": "private_write",
        "confirmation": "none_backend",
        "handler_name": "project_audit_report_status",
        "test_level": "direct",
    },
    {
        "path": "/api/email-processing/process-batch",
        "label": "Zpracovat davku e-mailu",
        "risk": "private_write",
        "confirmation": "ui_confirm_plus_exact_phrase_for_trash",
        "handler_name": "process_email_work_queue_batch",
        "test_level": "direct",
    },
    {
        "path": "/api/email-processing/purge-trash",
        "label": "Trvale smazat e-maily z kose",
        "risk": "delete_or_purge",
        "confirmation": "exact_phrase",
        "handler_name": "process_email_work_queue_purge_trash_batch",
        "test_level": "direct",
    },
    {
        "path": "/api/email-processing/new-headers",
        "label": "Nacist nove hlavicky e-mailu",
        "risk": "read_only_via_post",
        "confirmation": "none_readonly",
        "handler_name": "new_email_headers_overview",
        "test_level": "direct",
    },
)


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
            server_version = "SamanthaCockpit/0.2"
            sys_version = ""

            def handle_one_request(self) -> None:
                self._response_started = False
                self._security_headers_sent = False
                try:
                    super().handle_one_request()
                except CockpitHttpError as exc:
                    log_cockpit_http_event(
                        event=exc.error,
                        method=getattr(self, "command", ""),
                        request_path=getattr(self, "path", ""),
                        status=int(exc.status),
                        detail=exc.error,
                    )
                    if exc.close_connection:
                        self.close_connection = True
                    self.respond_request_error(exc)
                except (BrokenPipeError, ConnectionResetError):
                    self.close_connection = True
                except Exception as exc:  # noqa: BLE001 - central HTTP safety boundary
                    log_cockpit_http_event(
                        event="internal_error",
                        method=getattr(self, "command", ""),
                        request_path=getattr(self, "path", ""),
                        status=int(HTTPStatus.INTERNAL_SERVER_ERROR),
                        detail=type(exc).__name__,
                    )
                    self.close_connection = True
                    self.respond_request_error(
                        CockpitHttpError(
                            status=HTTPStatus.INTERNAL_SERVER_ERROR,
                            error="internal_error",
                            message="Cockpit narazil na vnitřní chybu. Citlivé podrobnosti nebyly zveřejněny.",
                            close_connection=True,
                        )
                    )

            def respond_request_error(self, error: CockpitHttpError) -> None:
                if getattr(self, "_response_started", False):
                    return
                try:
                    self.respond_json(
                        {"ok": False, "error": error.error, "message": error.message},
                        status=error.status,
                    )
                except (BrokenPipeError, ConnectionResetError, OSError):
                    self.close_connection = True

            def validate_request_access(self, *, require_origin: bool) -> None:
                host_header = str(self.headers.get("Host", "") or "")
                if not cockpit_host_is_allowed(host_header):
                    raise CockpitHttpError(
                        status=HTTPStatus.BAD_REQUEST,
                        error="invalid_host",
                        message="Požadavek nemá povolenou adresu Cockpitu.",
                        close_connection=True,
                    )
                if not require_origin:
                    return
                origin = str(self.headers.get("Origin", "") or "").strip()
                referer = str(self.headers.get("Referer", "") or "").strip()
                if origin and not cockpit_origin_matches_host(origin, host_header):
                    raise CockpitHttpError(
                        status=HTTPStatus.FORBIDDEN,
                        error="origin_forbidden",
                        message="Původ požadavku není pro Cockpit povolený.",
                        close_connection=True,
                    )
                if not origin and referer and not cockpit_origin_matches_host(referer, host_header):
                    raise CockpitHttpError(
                        status=HTTPStatus.FORBIDDEN,
                        error="referer_forbidden",
                        message="Zdroj požadavku není pro Cockpit povolený.",
                        close_connection=True,
                    )

            def do_GET(self) -> None:  # noqa: N802
                self.validate_request_access(require_origin=False)
                parsed = urlparse(self.path)
                if parsed.path == "/":
                    self.respond_html(COCKPIT_HTML)
                    return
                if parsed.path == "/email-processing/":
                    self.respond_html(EMAIL_PROCESSING_HTML)
                    return
                if parsed.path == "/email-archive/":
                    self.respond_html(EMAIL_ARCHIVE_HTML)
                    return
                if parsed.path == "/janicka-kucharka/":
                    self.respond_html(janicka_cookbook_page_html())
                    return
                if parsed.path == "/lekarna-admin/":
                    self.respond_html(lekarna_admin_page_html())
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
                if parsed.path == "/purchases/read":
                    params = parse_qs(parsed.query)
                    purchase_id = params.get("purchase_id", [""])[0]
                    self.respond_purchase_reader(purchase_id)
                    return
                if parsed.path == "/purchases/pdf":
                    params = parse_qs(parsed.query)
                    purchase_id = params.get("purchase_id", [""])[0]
                    self.respond_purchase_pdf(purchase_id)
                    return
                if parsed.path == "/api/status":
                    self.respond_json(cockpit_status())
                    return
                if parsed.path == "/api/live-status":
                    self.respond_json(cockpit_live_status())
                    return
                if parsed.path == "/api/server/health":
                    self.respond_json(server_health_status(host=cockpit_host, port=cockpit_port))
                    return
                if parsed.path == "/api/reminders":
                    self.respond_json(reminders_status())
                    return
                if parsed.path == "/api/web-apps":
                    self.respond_json(web_apps_catalog())
                    return
                if parsed.path == "/api/lekarna/import/photos":
                    params = parse_qs(parsed.query)
                    try:
                        limit = int(params.get("limit", ["12"])[0])
                    except (TypeError, ValueError):
                        limit = 12
                    self.respond_json(lekarna_import_photos_status(limit=limit))
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
                    read_state = params.get("read_state", [""])[0]
                    try:
                        limit = int(params.get("limit", ["200"])[0])
                    except (TypeError, ValueError):
                        limit = 200
                    self.respond_json(list_articles(category=category, read_state=read_state, limit=limit))
                    return
                if parsed.path == "/api/library/search":
                    params = parse_qs(parsed.query)
                    category = params.get("category", ["all"])[0]
                    read_state = params.get("read_state", [""])[0]
                    query = params.get("q", [""])[0]
                    try:
                        limit = int(params.get("limit", ["50"])[0])
                    except (TypeError, ValueError):
                        limit = 50
                    self.respond_json(search_articles(query=query, category=category, read_state=read_state, limit=limit))
                    return
                if parsed.path == "/api/lekarna/search":
                    params = parse_qs(parsed.query)
                    query = params.get("q", [""])[0]
                    try:
                        limit = int(params.get("limit", ["25"])[0])
                    except (TypeError, ValueError):
                        limit = 25
                    self.respond_json(lekarna_search_action(query=query, limit=limit))
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
                if parsed.path == "/api/project-audit":
                    params = parse_qs(parsed.query)
                    mode = params.get("mode", ["quick"])[0]
                    self.respond_json(project_audit_report_status(mode=mode, save=False))
                    return
                if parsed.path == "/api/project-audit/recent":
                    params = parse_qs(parsed.query)
                    try:
                        limit = int(params.get("limit", ["5"])[0])
                    except (TypeError, ValueError):
                        limit = 5
                    self.respond_json(project_audit_recent_reports(limit=limit))
                    return
                if parsed.path == "/api/project-audit/report":
                    params = parse_qs(parsed.query)
                    name = params.get("name", [""])[0]
                    self.respond_json(project_audit_report_file_status(name=name))
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
                if parsed.path == "/api/email-archive/list":
                    params = parse_qs(parsed.query)
                    query = params.get("q", [""])[0]
                    try:
                        limit = int(params.get("limit", ["120"])[0])
                    except (TypeError, ValueError):
                        limit = 120
                    self.respond_json(email_archive_list_status(query=query, limit=limit))
                    return
                if parsed.path == "/api/email-archive/detail":
                    params = parse_qs(parsed.query)
                    archive_id = params.get("archive_id", [""])[0]
                    self.respond_json(email_archive_detail_status(archive_id=archive_id))
                    return
                if parsed.path == "/email-archive/file":
                    params = parse_qs(parsed.query)
                    archive_id = params.get("archive_id", [""])[0]
                    file_key = params.get("file", [""])[0]
                    self.respond_email_archive_file(archive_id=archive_id, file_key=file_key)
                    return
                if parsed.path == "/email-archive/incoming":
                    params = parse_qs(parsed.query)
                    name = params.get("name", [""])[0]
                    self.respond_email_archive_incoming_file(name=name)
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
                if parsed.path == "/api/voice-mode/latest-response":
                    self.respond_json(cockpit_voice_latest_response_action())
                    return
                if parsed.path == "/api/voice-mode/safe-readonly":
                    self.respond_json(cockpit_safe_readonly_capabilities_action())
                    return
                if parsed.path == "/api/dev-runner/actions":
                    self.respond_json(cockpit_dev_runner_actions())
                    return
                if parsed.path.startswith("/local-apps/"):
                    self.respond_local_app_file(parsed.path)
                    return
                self.respond_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)

            def do_POST(self) -> None:  # noqa: N802
                self.validate_request_access(require_origin=True)
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
                if parsed.path == "/api/voice-bridge/frontend-event":
                    payload = self.read_json()
                    self.respond_json(cockpit_voice_frontend_event_action(payload))
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
                if parsed.path == "/api/janicka/light/status":
                    self.respond_json(janicka_light_status_action())
                    return
                if parsed.path == "/api/janicka/light/start":
                    self.respond_json(start_janicka_light_session())
                    return
                if parsed.path == "/api/janicka/light/stop":
                    payload = self.read_json()
                    self.respond_json(stop_janicka_light_session(confirmed=bool(payload.get("confirmed"))))
                    return
                if parsed.path == "/api/janicka/light/cleanup-orphans":
                    payload = self.read_json()
                    self.respond_json(terminate_orphaned_janicka_sessions_action(payload))
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
                if parsed.path == "/api/voice-mode/codex-approval/clear":
                    payload = self.read_json()
                    self.respond_json(cockpit_codex_approval_clear_action(payload))
                    return
                if parsed.path == "/api/voice-mode/safe-readonly/run":
                    payload = self.read_json()
                    self.respond_json(cockpit_safe_readonly_run_action(payload))
                    return
                if parsed.path == "/api/dev-runner/run":
                    payload = self.read_json()
                    self.respond_json(cockpit_dev_runner_run_action(payload))
                    return
                if parsed.path == "/api/desktop-apps/open":
                    payload = self.read_json()
                    self.respond_json(open_desktop_app_action(payload))
                    return
                if parsed.path == "/api/voice-bridge/marker":
                    payload = self.read_json()
                    self.respond_json(set_adam_voice_bridge_marker_action(str(payload.get("tty", ""))))
                    return
                if parsed.path == "/api/voice-bridge/terminate-stale":
                    payload = self.read_json()
                    self.respond_json(terminate_stale_codex_sessions_action(payload))
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
                if parsed.path == "/api/session-autosave/cleanup":
                    payload = self.read_json()
                    self.respond_json(session_autosave_cleanup_action(payload))
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
                if parsed.path == "/api/janicka/full-adam/open":
                    self.respond_json(open_janicka_full_adam_action())
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
                if parsed.path == "/api/library/delete":
                    payload = self.read_json()
                    self.respond_json(library_delete_article_action(payload))
                    return
                if parsed.path == "/api/lekarna/retire/preview":
                    payload = self.read_json()
                    self.respond_json(lekarna_retire_preview_action(payload))
                    return
                if parsed.path == "/api/lekarna/retire/apply":
                    payload = self.read_json()
                    self.respond_json(lekarna_retire_apply_action(payload))
                    return
                if parsed.path == "/api/lekarna/import/draft":
                    payload = self.read_json()
                    self.respond_json(lekarna_auto_import_draft_action(payload))
                    return
                if parsed.path == "/api/lekarna/import/manifest/load":
                    payload = self.read_json()
                    self.respond_json(lekarna_import_manifest_load_action(payload))
                    return
                if parsed.path == "/api/lekarna/import/manifest/save":
                    payload = self.read_json()
                    self.respond_json(lekarna_import_manifest_save_action(payload))
                    return
                if parsed.path == "/api/lekarna/import/manifest/retry-pil":
                    payload = self.read_json()
                    self.respond_json(lekarna_import_manifest_retry_pil_action(payload))
                    return
                if parsed.path == "/api/lekarna/import/apply":
                    payload = self.read_json()
                    self.respond_json(lekarna_auto_import_apply_action(payload))
                    return
                if parsed.path == "/api/library/read-state":
                    payload = self.read_json()
                    self.respond_json(library_read_state_action(payload))
                    return
                if parsed.path == "/api/library/export/prepare":
                    payload = self.read_json()
                    self.respond_json(library_prepare_pdf_export_action(payload))
                    return
                if parsed.path == "/api/library/export/send":
                    payload = self.read_json()
                    self.respond_json(library_send_pdf_export_action(payload))
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
                if parsed.path == "/api/documents/classification-suggestion/accept":
                    payload = self.read_json()
                    self.respond_json(
                        accept_document_classification_suggestion_action(
                            document_id=str(payload.get("document_id", "")),
                            confirmed=bool(payload.get("confirmed")),
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
                            filename=str(payload.get("filename", "")),
                        )
                    )
                    return
                if parsed.path == "/api/project-audit/save":
                    payload = self.read_json()
                    mode = str(payload.get("mode", "full"))
                    self.respond_json(project_audit_report_status(mode=mode, save=True))
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
                transfer_encoding = str(self.headers.get("Transfer-Encoding", "") or "").strip()
                if transfer_encoding and transfer_encoding.casefold() != "identity":
                    raise CockpitHttpError(
                        status=HTTPStatus.BAD_REQUEST,
                        error="unsupported_transfer_encoding",
                        message="Cockpit nepodporuje tento způsob přenosu JSON těla.",
                        close_connection=True,
                    )
                raw_length = str(self.headers.get("Content-Length", "0") or "0").strip()
                try:
                    length = int(raw_length)
                except ValueError as exc:
                    raise CockpitHttpError(
                        status=HTTPStatus.BAD_REQUEST,
                        error="invalid_content_length",
                        message="Neplatná délka požadavku.",
                        close_connection=True,
                    ) from exc
                if length < 0:
                    raise CockpitHttpError(
                        status=HTTPStatus.BAD_REQUEST,
                        error="invalid_content_length",
                        message="Neplatná délka požadavku.",
                        close_connection=True,
                    )
                if length > MAX_JSON_BODY_BYTES:
                    raise CockpitHttpError(
                        status=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                        error="request_too_large",
                        message="JSON požadavek je příliš velký.",
                        close_connection=True,
                    )
                if length and self.headers.get_content_type().casefold() != "application/json":
                    raise CockpitHttpError(
                        status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                        error="json_content_type_required",
                        message="Cockpit očekává JSON s Content-Type application/json.",
                        close_connection=True,
                    )
                raw_bytes = self.rfile.read(length) if length else b"{}"
                if len(raw_bytes) != length and length:
                    raise CockpitHttpError(
                        status=HTTPStatus.BAD_REQUEST,
                        error="incomplete_request_body",
                        message="JSON tělo požadavku nebylo přijato celé.",
                        close_connection=True,
                    )
                try:
                    raw = raw_bytes.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise CockpitHttpError(
                        status=HTTPStatus.BAD_REQUEST,
                        error="invalid_json_encoding",
                        message="JSON požadavek musí být v UTF-8.",
                    ) from exc
                try:
                    data = json.loads(raw or "{}")
                except json.JSONDecodeError as exc:
                    raise CockpitHttpError(
                        status=HTTPStatus.BAD_REQUEST,
                        error="invalid_json",
                        message="JSON požadavek není platný.",
                    ) from exc
                if not isinstance(data, dict):
                    raise CockpitHttpError(
                        status=HTTPStatus.BAD_REQUEST,
                        error="json_object_required",
                        message="JSON požadavek musí být objekt.",
                    )
                return data

            def send_response(self, code: int, message: str | None = None) -> None:
                self._response_started = True
                super().send_response(code, message)

            def end_headers(self) -> None:
                if not getattr(self, "_security_headers_sent", False):
                    for name, value in COCKPIT_SECURITY_HEADERS:
                        self.send_header(name, value)
                    self._security_headers_sent = True
                super().end_headers()

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
                resolved = resolve_openable_document_file(document_id)
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
                        viewer_kind=str(resolved.get("viewer_kind", "pdf")),
                    )
                )

            def respond_document_pdf(self, document_id: str) -> None:
                resolved = resolve_openable_document_file(document_id)
                if not resolved.get("ok"):
                    self.respond_json({"error": "not_found", "message": resolved.get("message", "")}, status=HTTPStatus.NOT_FOUND)
                    return
                target = resolved["path"]
                data = target.read_bytes()
                filename = safe_filename(str(target.name or "document.pdf"))
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", str(resolved.get("content_type") or "application/octet-stream"))
                self.send_header("Content-Disposition", f'inline; filename="{filename}"')
                self.send_header("Cache-Control", "no-store, max-age=0")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def respond_purchase_reader(self, purchase_id: str) -> None:
                resolved = resolve_openable_purchase_pdf(purchase_id)
                if not resolved.get("ok"):
                    self.respond_html(
                        purchase_reader_page_html(
                            purchase_id=safe_text(purchase_id)[:180],
                            title=str(resolved.get("message", "Nákup není dostupný.")),
                        ),
                        status=HTTPStatus.NOT_FOUND,
                    )
                    return
                self.respond_html(
                    purchase_reader_page_html(
                        purchase_id=str(resolved["purchase_ref"]),
                        title=str(resolved["title"]),
                    )
                )

            def respond_purchase_pdf(self, purchase_id: str) -> None:
                resolved = resolve_openable_purchase_pdf(purchase_id)
                if not resolved.get("ok"):
                    self.respond_json({"error": "not_found", "message": resolved.get("message", "")}, status=HTTPStatus.NOT_FOUND)
                    return
                target = resolved["path"]
                data = target.read_bytes()
                filename = safe_filename(str(target.name or "purchase.pdf"))
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Disposition", f'inline; filename="{filename}"')
                self.send_header("Cache-Control", "no-store, max-age=0")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def respond_email_archive_file(self, archive_id: str, file_key: str) -> None:
                resolved = resolve_email_archive_file(archive_id=archive_id, file_key=file_key)
                if not resolved.get("ok"):
                    self.respond_json(
                        {"error": "not_found", "message": resolved.get("message", "")},
                        status=HTTPStatus.NOT_FOUND,
                    )
                    return
                self.respond_local_file_bytes(
                    target=resolved["path"],
                    content_type=str(resolved.get("content_type") or "application/octet-stream"),
                    filename=str(resolved.get("filename") or "email-archive"),
                )

            def respond_email_archive_incoming_file(self, name: str) -> None:
                resolved = resolve_email_archive_incoming_file(name=name)
                if not resolved.get("ok"):
                    self.respond_json(
                        {"error": "not_found", "message": resolved.get("message", "")},
                        status=HTTPStatus.NOT_FOUND,
                    )
                    return
                self.respond_local_file_bytes(
                    target=resolved["path"],
                    content_type=str(resolved.get("content_type") or "application/octet-stream"),
                    filename=str(resolved.get("filename") or "attachment"),
                )

            def respond_local_file_bytes(self, *, target: Path, content_type: str, filename: str) -> None:
                data = target.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", content_type)
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
    if suffix == ".txt":
        return "text/plain; charset=utf-8"
    if suffix == ".css":
        return "text/css; charset=utf-8"
    if suffix == ".js":
        return "text/javascript; charset=utf-8"
    if suffix == ".json":
        return "application/json; charset=utf-8"
    if suffix == ".eml":
        return "message/rfc822"
    if suffix == ".pdf":
        return "application/pdf"
    if suffix == ".doc":
        return "application/msword"
    if suffix == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if suffix in {".png"}:
        return "image/png"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    return "application/octet-stream"


EMAIL_ARCHIVE_HTML = """<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Archiv e-mailů</title>
  <style>
    :root { --bg: #f5f7fb; --panel: #fff; --ink: #162033; --muted: #667085; --line: #d9e0ea; --blue: #1f5fbf; --green: #16794c; }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--bg); color: var(--ink); font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    header { display: flex; justify-content: space-between; gap: 12px; align-items: center; padding: 16px 20px; background: var(--panel); border-bottom: 1px solid var(--line); position: sticky; top: 0; z-index: 2; }
    h1 { margin: 0; font-size: 20px; }
    button, a.button { border: 0; border-radius: 6px; padding: 8px 11px; font: inherit; font-weight: 650; cursor: pointer; white-space: nowrap; text-decoration: none; display: inline-flex; align-items: center; color: inherit; }
    button.primary, a.button.primary { background: var(--blue); color: white; }
    button.secondary, a.button.secondary { background: #e8eef8; color: #1d3b74; }
    input { min-width: min(420px, 100%); border: 1px solid var(--line); border-radius: 7px; padding: 9px 10px; font: inherit; background: #fff; color: var(--ink); }
    main { padding: 18px 20px 28px; display: grid; grid-template-columns: 410px minmax(0, 1fr); gap: 14px; align-items: start; }
    section { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
    h2 { margin: 0; padding: 12px 14px; font-size: 14px; border-bottom: 1px solid var(--line); background: #f8fafc; }
    .body { padding: 13px 14px; display: grid; gap: 10px; }
    .toolbar { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    .status, .meta, .empty, .note { color: var(--muted); font-size: 13px; overflow-wrap: anywhere; }
    .list { display: grid; gap: 8px; }
    .item { border: 1px solid #edf0f4; border-radius: 8px; padding: 10px; background: #fbfcfe; display: grid; gap: 5px; text-align: left; width: 100%; color: inherit; }
    .item.active { border-color: #8eb1ed; background: #f4f8ff; }
    .subject { font-weight: 750; overflow-wrap: anywhere; }
    .actions, .files { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    .pill { border: 1px solid var(--line); border-radius: 999px; padding: 4px 8px; font-size: 12px; background: #f8fafc; color: #344054; }
    .attachment { border: 1px solid #edf0f4; border-radius: 7px; padding: 9px; display: grid; gap: 5px; background: #fbfcfe; }
    .ok { color: var(--green); font-weight: 700; }
    @media (max-width: 900px) { main { grid-template-columns: 1fr; } input { min-width: 0; width: 100%; } }
  </style>
</head>
<body>
  <header>
    <h1>Archiv e-mailů</h1>
    <div class="actions">
      <button class="secondary" id="returnBtn">Zpět do Cockpitu</button>
      <button class="primary" id="refreshBtn">Obnovit</button>
    </div>
  </header>
  <main>
    <section>
      <h2>Hledání</h2>
      <div class="body">
        <div class="toolbar">
          <input id="searchInput" placeholder="UID, předmět, odesílatel...">
          <button class="primary" id="searchBtn">Hledat</button>
        </div>
        <div class="status" id="status">Načítám archiv...</div>
        <div class="list" id="archiveList"></div>
      </div>
    </section>
    <section>
      <h2>Detail</h2>
      <div class="body" id="detailPane">
        <div class="empty">Vyber e-mail ze seznamu.</div>
      </div>
    </section>
  </main>
  <script>
    const listNode = document.getElementById("archiveList");
    const detailPane = document.getElementById("detailPane");
    const statusNode = document.getElementById("status");
    const searchInput = document.getElementById("searchInput");
    const searchBtn = document.getElementById("searchBtn");
    const refreshBtn = document.getElementById("refreshBtn");
    const returnBtn = document.getElementById("returnBtn");
    let selectedArchiveId = "";

    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }[ch]));
    }

    function fileSize(bytes) {
      const value = Number(bytes || 0);
      if (value >= 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)} MB`;
      if (value >= 1024) return `${Math.round(value / 1024)} kB`;
      return `${value} B`;
    }

    function renderList(items) {
      if (!items.length) {
        listNode.innerHTML = '<div class="empty">Nic nenalezeno.</div>';
        return;
      }
      listNode.innerHTML = items.map((item) => `
        <button class="item ${item.archive_id === selectedArchiveId ? "active" : ""}" data-archive-id="${escapeHtml(item.archive_id)}">
          <div class="subject">${escapeHtml(item.subject || item.archive_id)}</div>
          <div class="meta">UID ${escapeHtml(item.uid || "")} | ${escapeHtml(item.date || "")}</div>
          <div class="meta">${escapeHtml(item.sender || "")}</div>
          <div class="actions">
            <span class="pill">odkazy: ${Number(item.links_count || 0)}</span>
            <span class="pill">přílohy: ${Number(item.attachments_count || 0)}</span>
          </div>
        </button>
      `).join("");
      listNode.querySelectorAll("[data-archive-id]").forEach((button) => {
        button.addEventListener("click", () => loadDetail(button.dataset.archiveId || ""));
      });
    }

    function renderDetail(data) {
      if (!data.ok) {
        detailPane.innerHTML = `<div class="empty">${escapeHtml(data.message || "Archiv se nepodařilo načíst.")}</div>`;
        return;
      }
      const files = data.files || [];
      const attachments = data.attachments || [];
      const downloaded = data.downloaded_attachments || [];
      detailPane.innerHTML = `
        <div class="subject">${escapeHtml(data.subject || data.archive_id)}</div>
        <div class="meta">Archive ID: ${escapeHtml(data.archive_id || "")}</div>
        <div class="meta">UID: ${escapeHtml(data.uid || "")}</div>
        <div class="meta">Datum: ${escapeHtml(data.date || "")}</div>
        <div class="meta">Odesílatel: ${escapeHtml(data.sender || "")}</div>
        <div class="meta">Složka: ${escapeHtml(data.relative_path || "")}</div>
        <div class="files">
          ${files.map((file) => `<a class="button secondary" target="_blank" href="${escapeHtml(file.url)}">${escapeHtml(file.label)} (${fileSize(file.size_bytes)})</a>`).join("")}
        </div>
        <h2>Stažené přílohy v document inboxu</h2>
        ${downloaded.length ? downloaded.map((item) => `
          <div class="attachment">
            <div class="subject">${escapeHtml(item.filename)}</div>
            <div class="meta">${escapeHtml(item.content_type)} | ${fileSize(item.size_bytes)}</div>
            <div class="meta">${escapeHtml(item.relative_path || "")}</div>
            <div><a class="button secondary" target="_blank" href="${escapeHtml(item.url)}">Otevřít přílohu</a></div>
          </div>
        `).join("") : '<div class="empty">Žádná fyzicky stažená příloha nenalezena.</div>'}
        <h2>Metadata příloh z e-mailu</h2>
        ${attachments.length ? attachments.map((item) => `
          <div class="attachment">
            <div class="subject">${escapeHtml(item.filename || "(bez názvu)")}</div>
            <div class="meta">${escapeHtml(item.content_type || "")} | ${fileSize(item.size_bytes)} | saved=${item.saved ? "ano" : "ne"}</div>
          </div>
        `).join("") : '<div class="empty">Bez metadat příloh.</div>'}
        <div class="note">Bezpečnost: stránka čte jen lokální archiv. Nevolá e-mailový provider, neotevírá externí odkazy a nic nemaže ani neposílá.</div>
      `;
    }

    async function loadList() {
      statusNode.textContent = "Načítám...";
      try {
        const params = new URLSearchParams({q: searchInput.value || "", limit: "160"});
        const res = await fetch(`/api/email-archive/list?${params.toString()}`);
        const data = await res.json();
        statusNode.textContent = data.message || "";
        renderList(data.items || []);
      } catch (err) {
        statusNode.textContent = `Chyba načtení archivu: ${err}`;
      }
    }

    async function loadDetail(archiveId) {
      selectedArchiveId = archiveId;
      detailPane.innerHTML = '<div class="empty">Načítám detail...</div>';
      try {
        const params = new URLSearchParams({archive_id: archiveId});
        const res = await fetch(`/api/email-archive/detail?${params.toString()}`);
        const data = await res.json();
        renderDetail(data);
        await loadList();
      } catch (err) {
        detailPane.innerHTML = `<div class="empty">Chyba načtení: ${escapeHtml(err)}</div>`;
      }
    }

    function returnToCockpit() {
      if (window.opener && !window.opener.closed) {
        window.opener.focus();
        window.close();
        return;
      }
      window.location.href = "/";
    }

    searchBtn.addEventListener("click", loadList);
    refreshBtn.addEventListener("click", loadList);
    returnBtn.addEventListener("click", returnToCockpit);
    searchInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") loadList();
    });
    loadList();
  </script>
</body>
</html>"""


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
          <div class="status-line">Blokové přepínače jako VAK, Finanční správa nebo Faktury nad 2000 Kč jsou až v okně Work Queue po kliknutí na Zpracovat e-maily.</div>
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
      if (item.sender) parts.push(item.sender);
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
      const queueVisibleCount = queueDoc.getElementById("queueVisibleCount");
      const batchFilters = queueDoc.getElementById("batchFilters");
      const batchBtn = queueDoc.getElementById("batchBtn");
      const trashBatchBtn = queueDoc.getElementById("trashBatchBtn");
      const purgeTrashBtn = queueDoc.getElementById("purgeTrashBtn");
      let selectedId = queueItems.length ? queueItems[0].id : "";
      let activeBatchFilter = "all";
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

      function itemBatchGroups(item) {
        const groups = Array.isArray(item.batch_groups) ? item.batch_groups : [];
        return groups
          .map((group) => ({id: String(group.id || ""), label: String(group.label || group.id || "")}))
          .filter((group) => group.id);
      }

      function itemMatchesBatchFilter(item) {
        if (activeBatchFilter === "all") return true;
        return itemBatchGroups(item).some((group) => group.id === activeBatchFilter);
      }

      function visibleQueueItems() {
        return queueItems.filter((item) => itemMatchesBatchFilter(item));
      }

      function activeBatchLabel() {
        if (activeBatchFilter === "all") return "Vše";
        for (const item of queueItems) {
          const found = itemBatchGroups(item).find((group) => group.id === activeBatchFilter);
          if (found) return found.label;
        }
        return activeBatchFilter;
      }

      function ensureSelectedVisible() {
        const visible = visibleQueueItems();
        if (!visible.length) {
          selectedId = "";
          return null;
        }
        if (!visible.some((item) => item.id === selectedId)) selectedId = visible[0].id;
        return visible.find((item) => item.id === selectedId) || visible[0];
      }

      function currentItem() {
        return ensureSelectedVisible();
      }

      function renderBatchFilters() {
        const groupMap = new Map();
        groupMap.set("all", {id: "all", label: "Vše", count: queueItems.length});
        queueItems.forEach((item) => {
          itemBatchGroups(item).forEach((group) => {
            const current = groupMap.get(group.id) || {id: group.id, label: group.label, count: 0};
            current.count += 1;
            groupMap.set(group.id, current);
          });
        });
        const priority = ["all", "tax_office", "vak", "invoice_over_2000", "invoice", "pdf", "large_pdf", "other"];
        const groups = Array.from(groupMap.values()).sort((left, right) => {
          const leftRank = priority.includes(left.id) ? priority.indexOf(left.id) : 99;
          const rightRank = priority.includes(right.id) ? priority.indexOf(right.id) : 99;
          if (leftRank !== rightRank) return leftRank - rightRank;
          return left.label.localeCompare(right.label, "cs");
        });
        if (!groups.some((group) => group.id === activeBatchFilter)) activeBatchFilter = "all";
        batchFilters.innerHTML = groups.map((group) => {
          const active = group.id === activeBatchFilter ? " active" : "";
          return '<button type="button" class="filter-chip' + active + '" data-filter="' + escapeHtml(group.id) + '">' +
            escapeHtml(group.label) + ' <span>' + escapeHtml(String(group.count)) + '</span></button>';
        }).join("");
        batchFilters.querySelectorAll(".filter-chip").forEach((button) => {
          button.addEventListener("click", () => {
            activeBatchFilter = button.dataset.filter || "all";
            selectedId = "";
            renderQueueList();
            const item = currentItem();
            if (item) renderDetail(item);
            else detailPane.innerHTML = '<div class="empty">V tomto bloku není žádný e-mail.</div>';
          });
        });
      }

      function updateSummaryCounts() {
        const visible = visibleQueueItems();
        const workItems = visible.filter((item) => item.queueDecision !== "trash_requested");
        const trashItems = visible.filter((item) => item.queueDecision === "trash_requested");
        if (queueProcessCount) queueProcessCount.textContent = String(workItems.length);
        if (queueTrashCount) queueTrashCount.textContent = String(trashItems.length);
        if (queuePurgeCount) queuePurgeCount.textContent = String(permanentDeleteItems.length);
        if (queueVisibleCount) queueVisibleCount.textContent = `${visible.length}/${queueItems.length}`;
      }

      function updateBatchState() {
        const visible = visibleQueueItems();
        const decided = visible.filter((item) => Boolean(item.queueDecision)).length;
        const workItems = visible.filter((item) => item.queueDecision !== "trash_requested");
        const workReady = workItems.filter((item) => Boolean(item.queueDecision)).length;
        const trashItems = visible.filter((item) => item.queueDecision === "trash_requested");
        updateSummaryCounts();
        batchBtn.disabled = !workItems.length || workReady < workItems.length;
        trashBatchBtn.disabled = !trashItems.length;
        purgeTrashBtn.disabled = !permanentDeleteItems.length;
        queueStatus.textContent = visible.length
          ? `Blok: ${activeBatchLabel()}. Rozhodnuto ${decided}/${visible.length}. Koš: ${trashItems.length}. Dávkové akce platí jen pro aktuální blok.`
          : "Fronta je prázdná.";
      }

      function renderQueueList() {
        renderBatchFilters();
        const visible = visibleQueueItems();
        ensureSelectedVisible();
        if (!queueItems.length || !visible.length) {
          queueList.innerHTML = !queueItems.length
            ? '<div class="empty">Fronta je prázdná.</div>'
            : '<div class="empty">V tomto bloku není žádný e-mail.</div>';
          detailPane.innerHTML = '<div class="empty">Žádný e-mail ke zpracování v aktuálním bloku.</div>';
          batchBtn.disabled = true;
          trashBatchBtn.disabled = true;
          purgeTrashBtn.disabled = !permanentDeleteItems.length;
          updateSummaryCounts();
          return;
        }
        queueList.innerHTML = visible.map((item) => {
          const active = item.id === selectedId ? " active" : "";
          const done = item.queueDecision || item.detailLoaded ? " done" : "";
          const loading = item.detailLoading ? " loading" : "";
          const groups = itemBatchGroups(item).map((group) => group.label).slice(0, 3).join(" | ");
          const amount = item.amount_scan && item.amount_scan.max_amount_czk
            ? " | max " + Math.round(Number(item.amount_scan.max_amount_czk)).toLocaleString("cs-CZ") + " Kč"
            : "";
          return '<button type="button" class="item' + active + '" data-id="' + escapeHtml(item.id) + '">' +
            '<span class="subject">' + escapeHtml(item.subject || "(bez předmětu)") + '</span>' +
            '<span class="meta">' + escapeHtml(itemMeta(item)) + '</span>' +
            (groups ? '<span class="meta">' + escapeHtml(groups + amount) + '</span>' : "") +
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
          const filename = attachment.filename || "";
          const contentType = (attachment.content_type || "").toLowerCase();
          const lowerFilename = filename.toLowerCase();
          const canSaveToVault = contentType === "application/pdf" ||
            contentType.startsWith("image/") ||
            lowerFilename.endsWith(".pdf") ||
            lowerFilename.endsWith(".png") ||
            lowerFilename.endsWith(".jpg") ||
            lowerFilename.endsWith(".jpeg") ||
            lowerFilename.endsWith(".gif") ||
            lowerFilename.endsWith(".webp") ||
            lowerFilename.endsWith(".tif") ||
            lowerFilename.endsWith(".tiff");
          const checked = canSaveToVault && (item.saveAttachments || []).includes(partId) ? " checked" : "";
          const size = attachment.size_bytes === null || attachment.size_bytes === undefined
            ? "velikost neznámá"
            : Math.round(Number(attachment.size_bytes) / 1024) + " kB";
          const saveControl = canSaveToVault
            ? '<label><input type="checkbox" class="attachment-save" data-part-id="' + escapeHtml(partId) + '"' + checked + '> Uložit</label>'
            : '<span class="meta">Jen náhled</span>';
          return '<div class="attachment-row" data-part-id="' + escapeHtml(partId) + '">' +
            '<div><strong>' + escapeHtml(filename || "(bez názvu)") + '</strong></div>' +
            '<div class="meta">' + escapeHtml(attachment.content_type || "") + " | " + escapeHtml(size) + '</div>' +
            '<div class="attachment-tools">' +
            saveControl +
            '<button type="button" class="secondary attachment-preview" data-part-id="' + escapeHtml(partId) + '" data-filename="' + escapeHtml(filename) + '">Náhled</button>' +
            '<button type="button" class="secondary attachment-toggle">Metadata</button>' +
            '</div>' +
            '<div class="meta hidden attachment-detail">part_id: ' + escapeHtml(partId) + '<br>dispozice: ' + escapeHtml(attachment.disposition || "") + '<br>Náhled otevře dočasnou kopii PDF nebo obrázku; trvalé uložení podporované PDF/obrázkové přílohy do vaultu proběhne až po zaškrtnutí Uložit a zpracování dávky.</div>' +
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
            const filename = button.dataset.filename || "";
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
                  part_id: partId,
                  filename: filename
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
        const workItems = visibleQueueItems().filter((item) => item.queueDecision !== "trash_requested");
        if (!workItems.length) {
          queueStatus.textContent = "V této frontě jsou jen kandidáti ke koši. Použij tlačítko Emaily určené ke smazání smazat.";
          return;
        }
        const ok = queue.confirm(`Zpracovat aktuální blok "${activeBatchLabel()}" (${workItems.length} položek)?\\n\\nUložené e-maily půjdou do EmailArchiveVault. Vybrané PDF přílohy půjdou do private document vaultu a fulltextového indexu.`);
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
        const trashItems = visibleQueueItems().filter((item) => item.queueDecision === "trash_requested");
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
        queueStatus.textContent = "Připravuji přesné potvrzení pro trvalé smazání.";
        try {
          const previewRes = await fetch("/api/email-processing/purge-trash", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
              items: permanentDeleteItems,
              confirmed: false
            })
          });
          const preview = await previewRes.json();
          const required = preview.required_confirmation || "";
          if (!required) {
            queueStatus.textContent = preview.message || "Backend nevrátil potvrzovací větu pro trvalé smazání.";
            return;
          }
          const typed = queue.prompt(
            "Pro trvalé smazání opiš přesně potvrzovací větu:\\n\\n" + required,
            ""
          );
          if (typed !== required) {
            queueStatus.textContent = "Trvalé smazání z koše nebylo potvrzeno přesnou větou.";
            return;
          }
          queueStatus.textContent = "Trvale mažu e-maily z koše.";
          const res = await fetch("/api/email-processing/purge-trash", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
              items: permanentDeleteItems,
              confirmed: true,
              confirmation_text: typed
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
    .batch-filters { display: flex; flex-wrap: wrap; gap: 7px; }
    .filter-chip { background: #eef2f7; color: #263244; border: 1px solid #d9e0ea; }
    .filter-chip.active { background: var(--blue); color: white; border-color: var(--blue); }
    .filter-chip span { opacity: 0.78; font-weight: 700; }
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
        <div><strong>Aktuální blok:</strong> <span id="queueVisibleCount">${toProcess.length + toTrash.length}/${toProcess.length + toTrash.length}</span></div>
        <div><strong>Ignorováno:</strong> ${ignored.length}</div>
        <div class="batch-filters" id="batchFilters"></div>
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
    .janicka-action.emergency { grid-column: 1 / -1; border-color: #fecaca; background: #fff7f7; }
    .janicka-action-title { font-weight: 750; color: #581c35; }
    .janicka-action.emergency .janicka-action-title { color: #991b1b; }
    .janicka-action-text { margin-top: 3px; color: #5f4052; font-size: 13px; line-height: 1.4; }
    .janicka-action button { background: #be185d; color: white; }
    .janicka-action button.secondary { background: #fce7f3; color: #831843; }
    .janicka-action button.emergency { background: #b91c1c; color: white; }
    .janicka-note { border: 1px solid #fed7aa; border-radius: 8px; background: #fffbeb; color: #5f370e; padding: 11px 12px; font-size: 13px; line-height: 1.45; }
    .janicka-return { position: fixed; right: 18px; bottom: 18px; z-index: 14; box-shadow: 0 10px 28px rgba(88, 28, 53, .22); background: #be185d; color: white; }
    .janicka-chat-modal { width: min(920px, 100%); background: #fff7fb; border-color: #fbcfe8; }
    .janicka-chat-log { min-height: 320px; max-height: 48vh; overflow: auto; display: grid; gap: 10px; padding: 10px; border: 1px solid #fbcfe8; border-radius: 8px; background: white; }
    .janicka-chat-message { border: 1px solid #edf0f4; border-radius: 8px; padding: 10px; background: #fbfcfe; white-space: pre-wrap; overflow-wrap: anywhere; line-height: 1.45; }
    .janicka-chat-message.user { background: #fce7f3; border-color: #fbcfe8; }
    .janicka-chat-message.assistant { background: #fff; border-color: #fbcfe8; }
    .janicka-chat-meta { font-size: 12px; font-weight: 750; color: #831843; margin-bottom: 4px; }
    .janicka-chat-runtime { display: grid; gap: 8px; padding: 10px; border: 1px solid #fbcfe8; border-radius: 8px; background: #fff; }
    .janicka-service-details { border-top: 1px solid #f3f4f6; padding-top: 8px; }
    .janicka-service-details summary { cursor: pointer; color: var(--muted); font-size: 13px; font-weight: 700; }
    .janicka-service-details[open] { display: grid; gap: 8px; }
    .compact-actions { gap: 8px; }
    .compact-actions button { min-height: 34px; padding: 6px 10px; }
    .janicka-chat-input { display: grid; gap: 8px; }
    .janicka-chat-input textarea { width: 100%; min-height: 110px; resize: vertical; border: 1px solid #fbcfe8; border-radius: 8px; padding: 10px; font: inherit; line-height: 1.45; }
    .janicka-family-modal { width: min(860px, 100%); background: #fff7fb; border-color: #fbcfe8; }
    .janicka-family-list { display: grid; gap: 10px; }
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
    .voice-command-actions.voice-primary-actions { justify-content: flex-start; }
    .voice-command-actions.voice-text-actions { justify-content: flex-end; }
    .voice-command-actions button.recording { background: #fee2e2; color: var(--red); }
    .voice-command-actions button.voice-audio-unlock.active { background: var(--green); color: white; }
    .voice-command-actions button:disabled { cursor: not-allowed; }
    .voice-card { border: 1px solid var(--line); border-radius: 8px; padding: 10px; background: #f8fafc; display: grid; gap: 8px; }
    .voice-card.warn { border-color: #fbbf24; background: #fffbeb; }
    .voice-card-title { font-size: 13px; font-weight: 700; color: var(--ink); }
    .voice-card-text { color: var(--ink); font-size: 14px; line-height: 1.45; white-space: pre-wrap; overflow-wrap: anywhere; }
    .voice-card-field { display: grid; gap: 2px; }
    .voice-card-label { color: var(--muted); font-size: 12px; font-weight: 700; }
    .voice-card-actions { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    .voice-card-actions button.needs-tap { background: var(--blue); color: white; }
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
    .library-tab.read-queue { border-color: #f59e0b; background: #fffbeb; color: #92400e; font-weight: 750; }
    .library-tab.read-queue.active { background: #f59e0b; color: #172033; }
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
    .library-item.to-read { border-color: #f59e0b; background: #fffbeb; box-shadow: inset 3px 0 0 #f59e0b; }
    .library-title { font-weight: 750; overflow-wrap: anywhere; }
    .library-read-badge { justify-self: start; border: 1px solid #f59e0b; border-radius: 999px; padding: 2px 7px; background: #fff7ed; color: #92400e; font-size: 12px; font-weight: 750; }
    .library-meta { color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
    .library-reader { border: 1px solid #edf0f4; border-radius: 8px; background: #fbfcfe; min-height: 420px; display: grid; grid-template-rows: auto 1fr; overflow: visible; }
    .library-reader-head { padding: 12px; border-bottom: 1px solid #edf0f4; display: grid; gap: 6px; background: white; }
    .library-reader-title { margin: 0; font-size: 18px; line-height: 1.25; overflow-wrap: anywhere; }
    .library-reader-actions { display: flex; gap: 8px; justify-content: flex-end; flex-wrap: wrap; }
    .library-reader-text { padding: 14px 16px; white-space: pre-wrap; overflow: visible; line-height: 1.58; font-size: 15px; background: white; }
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
    .project-audit-report { white-space: pre-wrap; overflow-wrap: anywhere; max-height: 70vh; overflow: auto; margin: 0; }
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
		      <h2>Hlas / text pro Adama</h2>
		      <div class="body voice-command-grid">
		        <div class="voice-command-actions voice-primary-actions">
		          <button class="primary" id="voiceRecordBtn">Nahrát pokyn</button>
		          <button class="secondary hidden" id="voiceStopBtn" disabled>Zastavit</button>
		        </div>
		        <div id="voiceCommandStatus" class="status-line">Nahraj pokyn, nebo napiš text. Cockpit ho pošle Adamovi přímo.</div>
	        <div class="voice-transcript-row">
	          <label for="voiceTranscript">Textový pokyn</label>
	          <textarea id="voiceTranscript" placeholder="Nadiktuj nebo napiš pokyn pro Adama." spellcheck="true"></textarea>
	        </div>
		        <div class="voice-command-actions voice-text-actions">
		          <button class="secondary voice-audio-unlock" id="voiceAudioUnlockBtn">Otevřít audiokanál</button>
		          <button class="primary" id="voiceTranscriptSendBtn">Odeslat Adamovi</button>
		        </div>
            <details class="voice-advanced">
              <summary>Technické nastavení</summary>
		        <div class="voice-command-actions">
		          <button class="secondary" id="voiceModeToggleBtn" aria-pressed="false">Starý poslech: vypnuto</button>
		          <button class="secondary" id="voiceModeStartBtn">Spustit watcher</button>
		          <button class="secondary" id="voiceModeStopBtn">Zastavit watcher</button>
		        </div>
		          <div id="voiceModeRuntimeStatus" class="status-line">Adam Voice Mode watcher: čekám na kontrolu.</div>
		          <div id="voiceBridgeStatus" class="status-line">Terminálový bridge: čekám na kontrolu.</div>
		          <div id="voiceBridgeSessions" class="status-line">Codex relace: čekám na kontrolu.</div>
		          <div id="voiceBridgeSwitcher" class="voice-card hidden">
		            <div class="voice-card-title">Voice bridge cíl</div>
		            <div id="voiceBridgeSwitcherStatus" class="status-line">Načítám dostupné Codex relace.</div>
		            <div id="voiceBridgeSwitcherActions" class="voice-card-actions"></div>
		          </div>
		          <div id="safeReadonlyCard" class="voice-card">
		            <div class="voice-card-title">Bezpečné kontroly</div>
		            <div class="status-line">Pevný read-only allowlist bez volného shell příkazu.</div>
		            <div class="voice-card-actions">
		              <button class="secondary" data-safe-readonly="codex_sessions">Codex relace</button>
		              <button class="secondary" data-safe-readonly="voice_bridge">Voice bridge</button>
		              <button class="secondary" data-safe-readonly="git_status">Git stav</button>
		              <button class="secondary" data-safe-readonly="backup_status">Záloha</button>
		            </div>
		            <pre id="safeReadonlyResult" class="voice-card-text"></pre>
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
		        <div id="codexApprovalCard" class="voice-card warn hidden">
		          <div class="voice-card-title">Codex čeká na potvrzení</div>
		          <div class="voice-card-field">
		            <div class="voice-card-label">Co chci udělat</div>
		            <div id="codexApprovalCommand" class="voice-card-text"></div>
		          </div>
		          <div class="voice-card-field">
		            <div class="voice-card-label">Proč</div>
		            <div id="codexApprovalReason" class="voice-card-text"></div>
		          </div>
		          <div class="voice-card-field">
		            <div class="voice-card-label">Riziko</div>
		            <div id="codexApprovalRisk" class="voice-card-text"></div>
		          </div>
		          <div class="voice-card-field">
		            <div class="voice-card-label">Co má Míla udělat</div>
		            <div id="codexApprovalNextStep" class="voice-card-text"></div>
		          </div>
		          <div id="codexApprovalConfirmationBlock" class="voice-card-field hidden">
		            <div class="voice-card-label">Přesná potvrzovací věta</div>
		            <div id="codexApprovalConfirmationText" class="voice-card-text"></div>
		            <textarea id="codexApprovalConfirmationInput" spellcheck="false"></textarea>
		          </div>
		          <div class="voice-card-actions">
		            <button class="primary hidden" id="codexApprovalSendConfirmationBtn">Odeslat potvrzení Adamovi</button>
		            <button class="secondary hidden" id="codexApprovalCopyConfirmationBtn">Kopírovat větu</button>
		            <button class="secondary" id="codexApprovalClearBtn">Vyčistit kartu</button>
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
            <h3>Dokumenty k revizi</h3>
            <div id="reviewReportCount" class="work-count">?</div>
            <div class="actions">
              <button class="secondary" id="reviewReportBtn">Načti report</button>
            </div>
            <div id="reviewReportStatus" class="status-line">Report zatím není načtený. Skupiny: Bez textu / OCR, Krátký text, Doplnit údaje, K revizi, V pořádku.</div>
            <div id="reviewReportList" class="work-list review-report-list"></div>
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
            <h3>Související dokumenty</h3>
            <div id="documentCasesCount" class="work-count">0</div>
            <div id="documentCasesStatus" class="status-line">Seskupení podle věci nebo protistrany.</div>
            <div id="documentCasesList" class="work-list"></div>
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
            <button class="secondary" id="dashboardProjectAuditBtn">Systémový audit</button>
            <button class="secondary" id="dashboardQuickNotesBtn">Rychlé poznámky</button>
            <button class="secondary" id="dashboardRecoveryBtn">Recovery centrum</button>
            <button class="secondary" id="dashboardAutosaveCleanupBtn">Autosave úklid</button>
            <button class="secondary" id="dashboardDiagnosticsBtn">Diagnostika</button>
            <button class="secondary" id="dashboardRestartBtn">Restart Cockpitu</button>
            <button class="secondary" id="dashboardSpeakBtn">Přečíst stav</button>
            <button class="secondary" id="dashboardSpeakSelectionBtn">Přečíst výběr</button>
          </div>
        </div>
      </section>
      <section>
        <h2>Autosave úklid</h2>
        <div class="body">
          <div class="voice-card">
            <div class="voice-card-title">Staré session snapshoty</div>
            <div id="autosaveCleanupStatus" class="status-line">Dry-run zatím nebyl spuštěný.</div>
            <div class="voice-card-actions">
              <button class="secondary" id="autosaveCleanupPreviewBtn" type="button">Spočítat úklid</button>
              <button class="secondary danger" id="autosaveCleanupApplyBtn" type="button" disabled>Vyčistit staré autosave</button>
            </div>
            <pre id="autosaveCleanupOutput" class="voice-card-text"></pre>
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
      <section>
        <h2>Vývojový runner</h2>
        <div class="body">
          <div id="devRunnerPanel" class="voice-card">
            <div class="voice-card-title">Pevné vývojové akce</div>
            <div class="status-line">Spouští jen allowlistované příkazy pro opakované ladění, ne volný shell.</div>
            <div class="voice-card-actions">
              <button class="secondary" data-dev-runner="cockpit_voice_tests">Testy Cockpit + voice</button>
              <button class="secondary" data-dev-runner="cockpit_py_compile">Python syntax</button>
              <button class="secondary" data-dev-runner="git_diff_check">Diff check</button>
            </div>
            <pre id="devRunnerOutput" class="voice-card-text"></pre>
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
          <div class="janicka-action emergency">
            <div>
              <div class="janicka-action-title">Když Adam light nestačí</div>
              <div class="janicka-action-text">Otevře plného Adama, kde Jana píše normální větou. Není potřeba znát příkazy.</div>
            </div>
            <button class="emergency" id="janickaFullAdamBtn" type="button">Otevřít plného Adama</button>
          </div>
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
        <div id="janickaFullAdamStatus" class="janicka-note">Když běžný chat nestačí, tlačítko otevře plného Adama v Terminalu. Jana potom píše normální větou. Kdyby automatika selhala: otevřít aplikaci Terminal, napsat <code>cd /Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent</code>, stisknout Enter, potom napsat <code>codex --no-alt-screen</code>.</div>
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
          <div id="janickaLightStatus" class="status-line">Janička chat: čekám na kontrolu.</div>
          <div class="actions compact-actions">
            <button class="secondary" id="janickaLightStartBtn" type="button">Spustit Janičku</button>
            <button class="secondary" id="janickaLightStopBtn" type="button">Zastavit Janičku</button>
            <button class="secondary hidden" id="janickaLightCleanupOrphansBtn" type="button">Uklidit staré relace</button>
          </div>
          <details class="janicka-service-details">
            <summary>Servisní fallback</summary>
            <div id="janickaAdamStatus" class="status-line">Starý Adam fallback: čekám na kontrolu.</div>
            <div class="actions compact-actions">
              <button class="secondary" id="janickaAdamStartBtn" type="button">Spustit fallback</button>
              <button class="secondary" id="janickaAdamRestartBtn" type="button">Restartovat fallback</button>
              <button class="secondary" id="janickaAdamStopBtn" type="button">Zastavit fallback</button>
            </div>
          </details>
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
  <div id="janickaFamilyModal" class="modal-backdrop hidden" role="dialog" aria-modal="true" aria-labelledby="janickaFamilyTitle">
    <div class="modal janicka-family-modal">
      <div class="modal-header">
        <h2 id="janickaFamilyTitle">Rodinné projekty</h2>
        <button class="secondary" id="janickaFamilyCloseBtn">Zpět k Janičce</button>
      </div>
      <div class="modal-body">
        <div class="janicka-intro">
          <h3 class="janicka-title">Fotky, videa a rodinné výstupy</h3>
          <p class="janicka-subtitle">Tady jsou bezpečné vstupy k připraveným rodinným věcem. Původní fotky a videa se odsud nemažou ani nepřesouvají.</p>
        </div>
        <div class="janicka-family-list">
          <div class="janicka-action">
            <div>
              <div class="janicka-action-title">Rodinný výběr videí a fotek</div>
              <div class="janicka-action-text">Otevřít lokální přehled pro třídění rodinných videí, výběr záběrů a přípravu sestřihu.</div>
            </div>
            <button id="janickaFamilyOrganizerBtn" type="button">Otevřít</button>
          </div>
          <div class="janicka-action">
            <div>
              <div class="janicka-action-title">Přehled projektů</div>
              <div class="janicka-action-text">Zobrazit aktivní rodinné projekty a další kroky, když není jasné, co otevřít.</div>
            </div>
            <button class="secondary" id="janickaFamilyProjectsBtn" type="button">Zobrazit</button>
          </div>
        </div>
        <div id="janickaFamilyStatus" class="status-line">Vyber, co chceš otevřít.</div>
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
              <option value="ai_tools">Samantha / AI nástroje</option>
              <option value="travel_places">Cestování / místa</option>
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
              <option value="ai_tools">Samantha / AI nástroje</option>
              <option value="travel_places">Cestování / místa</option>
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
          <button class="secondary library-tab" type="button" data-library-category="ai_tools">Samantha / AI nástroje</button>
          <button class="secondary library-tab" type="button" data-library-category="travel_places">Cestování / místa</button>
          <button class="secondary library-tab" type="button" data-library-category="other">Ostatní</button>
          <button class="secondary library-tab read-queue" type="button" data-library-category="all" data-library-read-state="to_read">K přečtení</button>
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
              <div class="library-reader-actions">
                <button class="secondary" id="libraryOpenSourceBtn" type="button" disabled>Otevřít na webu</button>
                <button class="secondary" id="libraryExportPrepareBtn" type="button" disabled>Připravit PDF</button>
                <button class="primary" id="libraryExportSendBtn" type="button" disabled>Odeslat export</button>
                <button class="secondary" id="libraryToReadBtn" type="button" disabled>K přečtení</button>
                <button class="secondary" id="libraryDoneBtn" type="button" disabled>Hotovo</button>
                <button class="secondary" id="libraryClearReadStateBtn" type="button" disabled>Zrušit příznak</button>
                <button class="secondary danger" id="libraryDeleteBtn" type="button" disabled>Vyřadit z knihovny</button>
              </div>
              <div id="libraryExportStatus" class="status-line">Export PDF se připraví lokálně a odešle až po potvrzení.</div>
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
  <div id="projectAuditModal" class="modal-backdrop hidden" role="dialog" aria-modal="true" aria-labelledby="projectAuditTitle">
    <div class="modal">
      <div class="modal-header">
        <h2 id="projectAuditTitle">Systémový audit</h2>
        <div class="quick-actions">
          <button class="secondary" id="projectAuditSaveBtn">Uložit full audit</button>
          <button class="secondary" id="projectAuditCloseBtn">Zavřít</button>
        </div>
      </div>
      <div class="modal-body quantitative-panel">
        <div id="projectAuditStatus" class="status-line">Načítám systémový audit...</div>
        <div class="quantitative-card">
          <h3>Poslední uložené audity</h3>
          <div id="projectAuditRecentList" class="project-list"></div>
        </div>
        <div class="quantitative-card">
          <h3>Aktuální report</h3>
          <pre id="projectAuditText" class="project-audit-report"></pre>
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
    const janickaFullAdamBtn = document.getElementById("janickaFullAdamBtn");
    const janickaFullAdamStatus = document.getElementById("janickaFullAdamStatus");
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
    const janickaFamilyModal = document.getElementById("janickaFamilyModal");
    const janickaFamilyCloseBtn = document.getElementById("janickaFamilyCloseBtn");
    const janickaFamilyOrganizerBtn = document.getElementById("janickaFamilyOrganizerBtn");
    const janickaFamilyProjectsBtn = document.getElementById("janickaFamilyProjectsBtn");
    const janickaFamilyStatus = document.getElementById("janickaFamilyStatus");
    const janickaAdamStatus = document.getElementById("janickaAdamStatus");
    const janickaAdamStartBtn = document.getElementById("janickaAdamStartBtn");
    const janickaAdamRestartBtn = document.getElementById("janickaAdamRestartBtn");
    const janickaAdamStopBtn = document.getElementById("janickaAdamStopBtn");
    const janickaLightStatus = document.getElementById("janickaLightStatus");
    const janickaLightStartBtn = document.getElementById("janickaLightStartBtn");
    const janickaLightStopBtn = document.getElementById("janickaLightStopBtn");
    const janickaLightCleanupOrphansBtn = document.getElementById("janickaLightCleanupOrphansBtn");
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
    const libraryOpenSourceBtn = document.getElementById("libraryOpenSourceBtn");
    const libraryExportPrepareBtn = document.getElementById("libraryExportPrepareBtn");
    const libraryExportSendBtn = document.getElementById("libraryExportSendBtn");
    const libraryExportStatus = document.getElementById("libraryExportStatus");
    const libraryToReadBtn = document.getElementById("libraryToReadBtn");
    const libraryDoneBtn = document.getElementById("libraryDoneBtn");
    const libraryClearReadStateBtn = document.getElementById("libraryClearReadStateBtn");
    const libraryDeleteBtn = document.getElementById("libraryDeleteBtn");
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
    const projectAuditModal = document.getElementById("projectAuditModal");
    const projectAuditCloseBtn = document.getElementById("projectAuditCloseBtn");
    const projectAuditSaveBtn = document.getElementById("projectAuditSaveBtn");
    const projectAuditStatus = document.getElementById("projectAuditStatus");
    const projectAuditRecentList = document.getElementById("projectAuditRecentList");
    const projectAuditText = document.getElementById("projectAuditText");
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
    const dashboardProjectAuditBtn = document.getElementById("dashboardProjectAuditBtn");
		    const dashboardQuickNotesBtn = document.getElementById("dashboardQuickNotesBtn");
    const dashboardUrgentRemindersBtn = document.getElementById("dashboardUrgentRemindersBtn");
    const dashboardRecoveryBtn = document.getElementById("dashboardRecoveryBtn");
    const dashboardAutosaveCleanupBtn = document.getElementById("dashboardAutosaveCleanupBtn");
    const autosaveCleanupPreviewBtn = document.getElementById("autosaveCleanupPreviewBtn");
    const autosaveCleanupApplyBtn = document.getElementById("autosaveCleanupApplyBtn");
    const autosaveCleanupStatus = document.getElementById("autosaveCleanupStatus");
    const autosaveCleanupOutput = document.getElementById("autosaveCleanupOutput");
    const dashboardDiagnosticsBtn = document.getElementById("dashboardDiagnosticsBtn");
    const dashboardRestartBtn = document.getElementById("dashboardRestartBtn");
			    const dashboardSpeakBtn = document.getElementById("dashboardSpeakBtn");
			    const dashboardSpeakSelectionBtn = document.getElementById("dashboardSpeakSelectionBtn");
			    const dashboardRefreshBtn = document.getElementById("dashboardRefreshBtn");
    const devRunnerPanel = document.getElementById("devRunnerPanel");
    const devRunnerOutput = document.getElementById("devRunnerOutput");
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
    const safeReadonlyCard = document.getElementById("safeReadonlyCard");
    const safeReadonlyResult = document.getElementById("safeReadonlyResult");
    const voicePendingStatus = document.getElementById("voicePendingStatus");
    const voiceLastResponseCard = document.getElementById("voiceLastResponseCard");
    const voiceLastResponseText = document.getElementById("voiceLastResponseText");
    const voiceLastResponseSpeakBtn = document.getElementById("voiceLastResponseSpeakBtn");
    const codexApprovalCard = document.getElementById("codexApprovalCard");
    const codexApprovalReason = document.getElementById("codexApprovalReason");
    const codexApprovalCommand = document.getElementById("codexApprovalCommand");
    const codexApprovalRisk = document.getElementById("codexApprovalRisk");
    const codexApprovalNextStep = document.getElementById("codexApprovalNextStep");
    const codexApprovalConfirmationBlock = document.getElementById("codexApprovalConfirmationBlock");
    const codexApprovalConfirmationText = document.getElementById("codexApprovalConfirmationText");
    const codexApprovalConfirmationInput = document.getElementById("codexApprovalConfirmationInput");
    const codexApprovalSendConfirmationBtn = document.getElementById("codexApprovalSendConfirmationBtn");
    const codexApprovalCopyConfirmationBtn = document.getElementById("codexApprovalCopyConfirmationBtn");
    const codexApprovalClearBtn = document.getElementById("codexApprovalClearBtn");
    const voiceApprovalCard = document.getElementById("voiceApprovalCard");
    const voiceApprovalReason = document.getElementById("voiceApprovalReason");
    const voiceApprovalText = document.getElementById("voiceApprovalText");
    const voiceApprovalApproveBtn = document.getElementById("voiceApprovalApproveBtn");
    const voiceApprovalRejectBtn = document.getElementById("voiceApprovalRejectBtn");
    const voiceTranscript = document.getElementById("voiceTranscript");
    const voiceAudioUnlockBtn = document.getElementById("voiceAudioUnlockBtn");
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
    let currentLibraryReadStateFilter = "";
    let currentLibraryItems = [];
    let currentLibrarySelectedId = "";
    let currentLibrarySelectedItem = null;
    let currentLibrarySourceUrl = "";
    let currentLibraryExport = null;
    let currentQuantitative = null;
    let currentAutosaveCleanupPlan = null;
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
      ["Server health", "/api/server/health"],
      ["Hlavní status", "/api/status"],
      ["Recovery", "/api/recovery/status"],
      ["Webové aplikace", "/api/web-apps"],
      ["Knihovna", "/api/library/list?category=other&limit=1"],
      ["Projekty", "/api/projects/status"],
      ["Quick Notes", "/api/quick-notes/status"],
      ["Důležitá připomenutí", "/api/urgent-reminders/status"],
      ["Kvantitativní", "/api/quantitative-status"],
      ["Systémový audit", "/api/project-audit?mode=quick"],
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

    function recordVoiceFrontendEvent(kind, detail = {}) {
      const payload = {
        kind,
        detail: {
          ...detail,
          visibility: document.hidden ? "hidden" : "visible",
          url: window.location.host || ""
        }
      };
      try {
        const body = JSON.stringify(payload);
        if (navigator.sendBeacon) {
          const blob = new Blob([body], {type: "application/json"});
          if (navigator.sendBeacon("/api/voice-bridge/frontend-event", blob)) return;
        }
        fetch("/api/voice-bridge/frontend-event", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body,
          keepalive: true
        }).catch(() => {});
      } catch (_) {
        // Voice diagnostics must never block the UI.
      }
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

    function frontendErrorLooksRecoverableNetwork(text) {
      const value = String(text || "").toLowerCase();
      return value.includes("load failed")
        || value.includes("failed to fetch")
        || value.includes("networkerror")
        || value.includes("network error")
        || value.includes("api health selhal:");
    }

    function clearRecoverableFrontendNetworkErrors() {
      frontendErrorHistory = frontendErrorHistory.filter((item) => !frontendErrorLooksRecoverableNetwork(item.text));
      if (frontendErrorLooksRecoverableNetwork(frontendLastError)) {
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
        "janickaFullAdamBtn",
        "janickaFullAdamStatus",
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
        "janickaFamilyCloseBtn",
        "janickaFamilyOrganizerBtn",
        "janickaFamilyProjectsBtn",
        "janickaAdamStartBtn",
        "janickaAdamRestartBtn",
        "janickaAdamStopBtn",
        "janickaLightStatus",
        "janickaLightStartBtn",
        "janickaLightStopBtn",
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
        "libraryExportPrepareBtn",
        "libraryExportSendBtn",
        "libraryExportStatus",
        "libraryToReadBtn",
        "libraryDoneBtn",
        "libraryClearReadStateBtn",
        "libraryDeleteBtn",
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
        "dashboardAutosaveCleanupBtn",
        "autosaveCleanupPreviewBtn",
        "autosaveCleanupApplyBtn",
        "autosaveCleanupStatus",
        "autosaveCleanupOutput",
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
        "codexApprovalCard",
        "codexApprovalReason",
        "codexApprovalCommand",
        "codexApprovalRisk",
        "codexApprovalNextStep",
        "voiceApprovalCard",
        "voiceApprovalReason",
        "voiceApprovalText",
        "voiceApprovalApproveBtn",
        "voiceApprovalRejectBtn",
        "voiceRecordBtn",
        "voiceStopBtn",
        "voiceAudioUnlockBtn",
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
        checkEndpointHealth("/api/server/health"),
        checkEndpointHealth("/api/recovery/status")
      ]);
      const failed = results.filter((item) => !item.ok);
      if (failed.length) {
        setHealthValue(frontendHealthApi, `chyba ${failed.map((item) => item.url).join(", ")}`, "bad");
        recordFrontendError(`API health selhal: ${failed.map((item) => `${item.url} ${item.status || item.error || ""}`).join("; ")}`);
      } else {
        const slowest = Math.max(...results.map((item) => item.elapsed || 0));
        setHealthValue(frontendHealthApi, `OK, max ${slowest} ms`, "ok");
        clearRecoverableFrontendNetworkErrors();
        if (!frontendLastError) {
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
        if (reason.includes("hlas")) return "zkontrolovat terminálový bridge, případně poslat text znovu";
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

    const FULL_STATUS_MONITOR_MS = 5 * 60 * 1000;
    const INTAKE_EMAIL_MONITOR_MS = 30 * 60 * 1000;
    const URGENT_REMINDERS_MONITOR_MS = 30 * 1000;
    const VOICE_STATUS_MONITOR_MS = 3000;
    let refreshInFlight = false;
    let liveStatusRefreshInFlight = false;
    let urgentRemindersRefreshInFlight = false;
    let lastMainRefreshStartedAt = 0;
    let lastCodexApprovalActive = false;
    let latestMainStatusData = null;
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
        latestMainStatusData = data;
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
        if (!silent) {
          runEmailIntakeMonitor();
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

    async function refreshLiveStatus() {
      if (liveStatusRefreshInFlight) return;
      liveStatusRefreshInFlight = true;
      try {
        const res = await fetch("/api/live-status", {cache: "no-store"});
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!latestMainStatusData) return;
        latestMainStatusData = {
          ...latestMainStatusData,
          voice_mode: data.voice_mode || {},
          voice_bridge: data.voice_bridge || {}
        };
        renderVoiceStatus(latestMainStatusData);
      } catch (err) {
        recordFrontendError(err);
        setDashboardStatusSignal("voice", "warn", `Živý stav hlasu: ${err}`);
      } finally {
        liveStatusRefreshInFlight = false;
      }
    }

    function refreshMainStatusOnReturn(minAgeMs = FULL_STATUS_MONITOR_MS) {
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
      const provider = String(item.provider || "").trim().toLowerCase().replace(/\\s+/g, " ");
      const folder = String(item.folder || "INBOX").trim().toLowerCase().replace(/\\s+/g, " ");
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
        const sourceKey = emailIntakeSourceKey(item);
        if (sourceKey) byId.set(sourceKey, item);
      });
      (incoming || []).forEach((item) => {
        if (!item || !item.id || byId.has(item.id)) return;
        if (item.legacy_id && byId.has(item.legacy_id)) return;
        const sourceKey = emailIntakeSourceKey(item);
        if (sourceKey && byId.has(sourceKey)) return;
        byId.set(item.id, item);
        if (item.legacy_id) byId.set(item.legacy_id, item);
        if (sourceKey) byId.set(sourceKey, item);
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
        const itemSourceKey = emailIntakeSourceKey(item);
        lastEmailIntakeMonitor.items = (lastEmailIntakeMonitor.items || []).filter((candidate) => {
          if (candidate.id === itemId || candidate.legacy_id === itemId) return false;
          if (itemSourceKey && emailIntakeSourceKey(candidate) === itemSourceKey) return false;
          return true;
        });
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
        const suggestion = item.metadata_suggestion || {};
        let suggestionNode = null;
        if (suggestion.can_accept && suggestion.summary) {
          suggestionNode = document.createElement("div");
          suggestionNode.className = "work-meta";
          suggestionNode.textContent = `Návrh: ${suggestion.summary}`;
        }
        const actions = document.createElement("div");
        actions.className = "actions";
        if (suggestion.can_accept) {
          const acceptBtn = document.createElement("button");
          acceptBtn.className = "primary";
          acceptBtn.type = "button";
          acceptBtn.textContent = "Přijmout návrh";
          acceptBtn.addEventListener("click", () => acceptDocumentClassificationSuggestion(item, acceptBtn));
          actions.appendChild(acceptBtn);
        }
        const editBtn = document.createElement("button");
        editBtn.className = "secondary";
        editBtn.type = "button";
        editBtn.textContent = "Doplnit metadata";
        editBtn.addEventListener("click", () => updateDocumentClassificationMetadata(item, editBtn));
        actions.appendChild(editBtn);
        row.appendChild(title);
        row.appendChild(action);
        row.appendChild(meta);
        if (suggestionNode) row.appendChild(suggestionNode);
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

    async function acceptDocumentClassificationSuggestion(item, button) {
      const documentRef = item.document_ref || item.document_id || "";
      const suggestion = item.metadata_suggestion || {};
      if (!documentRef || !suggestion.can_accept) return;
      const ok = window.confirm(`Přijmout návrh metadat?\\n\\n${item.title || "Dokument"}\\n\\n${suggestion.summary || ""}`);
      if (!ok) return;
      const originalText = button.textContent;
      button.disabled = true;
      button.textContent = "Ukládám...";
      documentClassificationStatus.textContent = "Ukládám potvrzený návrh metadat...";
      try {
        const result = await postJson("/api/documents/classification-suggestion/accept", {
          document_id: documentRef,
          confirmed: true
        });
        documentClassificationStatus.textContent = result.message || "Návrh uložen.";
        if (result.ok) {
          if (result.document_classification) {
            renderDocumentClassification(result.document_classification);
          }
          await refresh({silent: true});
        }
      } catch (err) {
        recordFrontendError(err);
        documentClassificationStatus.textContent = `Chyba přijetí návrhu: ${err}`;
      } finally {
        button.disabled = false;
        button.textContent = originalText || "Přijmout návrh";
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
        "Např. insurance, car, home, tax, energy, telecom, employment, health, warranty. Můžeš napsat i novou oblast, uloží se jako bezpečný slug."
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
      const caseId = promptClassificationValue(
        "Case / souvislost",
        item.case_id || "",
        "Volitelné. Např. cez-smlouva-energie-2026 nebo ponech prázdné. Nový case vznikne tímto názvem."
      );
      if (caseId === null) return;
      const summary = [
        `Oblast: ${domain || "(prázdné)"}`,
        `Typ: ${documentType || "(prázdné)"}`,
        `Protistrana: ${counterparty || "(prázdné)"}`,
        `Vazba: ${relatedAsset || "(prázdné)"}`,
        `Case: ${caseId || "(prázdné)"}`
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
            related_asset: relatedAsset,
            case_id: caseId
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
        if (item.duplicate_note) {
          const duplicate = document.createElement("div");
          duplicate.className = "work-meta warning";
          duplicate.textContent = item.duplicate_note;
          row.appendChild(duplicate);
        }
        if (item.related_source_note) {
          const relatedSource = document.createElement("div");
          relatedSource.className = "work-meta";
          relatedSource.textContent = item.related_source_note;
          row.appendChild(relatedSource);
        }
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
        const documentRef = item.document_ref || item.document_id || "";
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
        const id = document.createElement("div");
        id.className = "work-meta";
        id.textContent = `ID: ${item.document_id || ""}`;
        const actions = document.createElement("div");
        actions.className = "actions";
        const openBtn = document.createElement("button");
        openBtn.className = "primary";
        openBtn.type = "button";
        openBtn.textContent = "Otevřít / číst";
        openBtn.addEventListener("click", () => openDocumentForReading(documentRef, openBtn, reviewReportStatus));
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
        statusSelect.addEventListener("change", async () => {
          await setDocumentReadingStatus(documentRef, statusSelect.value, {
            statusNode: reviewReportStatus,
            afterSave: loadDocumentReviewReport
          });
        });
        statusRow.appendChild(statusLabel);
        statusRow.appendChild(statusSelect);
        actions.appendChild(openBtn);
        row.appendChild(title);
        row.appendChild(recommendation);
        row.appendChild(meta);
        if (reasons.textContent) row.appendChild(reasons);
        row.appendChild(id);
        row.appendChild(actions);
        row.appendChild(statusRow);
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

      renderVoiceStatus(data);

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

    function renderVoiceStatus(data) {
      const voiceMode = data.voice_mode || {};
      const voiceBridge = data.voice_bridge || {};
      latestVoiceModeRuntime = voiceMode;
      const voiceRunning = Boolean(voiceMode.running);
      const voiceState = voiceMode.state || "unknown";
      const voiceMessage = voiceMode.message || "Adam Voice Mode stav není načtený.";
      const voiceBridgeWarn = voiceBridge.status === "warn" || voiceBridge.status === "missing";
      const voiceBridgeMessage = voiceBridge.message || "Terminálový bridge stav není načtený.";
      const totalCodexSessions = Number(voiceBridge.codex_tty_count || 0);
      const humanCodexSessions = Number(voiceBridge.human_codex_tty_count || 0);
      const managedCodexSessions = Array.isArray(voiceBridge.managed_codex_ttys)
        ? voiceBridge.managed_codex_ttys.length
        : 0;
      const codexSessionOverview = `relace ${totalCodexSessions}: běžné ${humanCodexSessions}, spravované ${managedCodexSessions}`;
      const voicePending = voiceMode.pending_for_adam || {};
      const voicePendingActive = Boolean(voicePending.pending);
      const voicePendingApprovalStatus = String(voicePending.approval_status || "");
      const voicePendingNeedsApproval = pendingNeedsCockpitApproval(voicePending);
      const voicePendingActionable = voicePendingActive && voicePendingNeedsApproval && voicePendingApprovalStatus !== "approved";
      const voicePendingText = String(voicePending.text || "");
      const voicePendingMessage = String(voicePending.message || "").trim();
      const voicePendingShort = voicePendingText.length > 160 ? `${voicePendingText.slice(0, 160)}...` : voicePendingText;
      const codexApproval = voiceMode.codex_approval || {};
      const codexApprovalActive = Boolean(codexApproval.active);
      const codexApprovalReasonText = String(codexApproval.reason || codexApproval.message || "Codex čeká na systémové potvrzení.");
      const voiceReady = !voiceBridgeWarn && (voiceBridge.status === "ok" || voiceBridge.status === "unknown" || !voiceBridge.status);
      const voiceBridgeDashboard = voiceBridgeWarn ? `<br><span class="warn">${escapeHtml(voiceBridgeMessage)}</span>` : "";
      dashboardVoiceMode.innerHTML = voicePendingActive
        ? `<span class="warn">${voicePendingActionable ? "čeká potvrzení" : "hlasový pokyn"}</span><br>${escapeHtml(voicePendingMessage || voicePendingShort || voiceState)}${voiceBridgeDashboard}`
        : codexApprovalActive
          ? `<span class="warn">čeká Codex</span><br>${escapeHtml(codexApprovalReasonText)}${voiceBridgeDashboard}`
        : voiceBridgeWarn
          ? `<span class="warn">zkontrolovat</span><br>${escapeHtml(voiceBridgeMessage)}`
          : `<span class="${voiceReady ? "ok" : "warn"}">${voiceReady ? "připraveno" : "nezjištěno"}</span><br>přímé odeslání z Cockpitu | ${escapeHtml(codexSessionOverview)}`;
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
        const managedLabels = voiceBridge.managed_codex_labels && typeof voiceBridge.managed_codex_labels === "object"
          ? voiceBridge.managed_codex_labels
          : {};
        const orphanedLabels = voiceBridge.orphaned_janicka_labels && typeof voiceBridge.orphaned_janicka_labels === "object"
          ? voiceBridge.orphaned_janicka_labels
          : {};
        const sessionLabels = {...managedLabels, ...orphanedLabels};
        const codexTtys = Array.isArray(voiceBridge.codex_ttys)
          ? voiceBridge.codex_ttys.map((item) => String(item || "")).filter(Boolean)
          : [];
        const sessionParts = codexTtys.map((tty) => (
          sessionLabels[tty]
            ? `${tty} -> ${sessionLabels[tty]}`
            : tty === markedTty
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
      if (voiceCommandDetails && (voicePendingActive || codexApprovalActive || voiceBridgeWarn)) {
        voiceCommandDetails.open = true;
      }
      if (voicePendingStatus) {
        voicePendingStatus.textContent = voicePendingActive
          ? voicePendingActionable
            ? `Čeká potvrzení: ${voicePendingMessage || voicePendingShort || "bez textu"}`
            : voicePendingMessage || `Čeká hlasový pokyn na Adama: ${voicePendingShort || "bez textu"}`
          : "Žádný hlasový pokyn nečeká na Adama.";
      }
	      renderVoiceLastResponse(voiceMode.last_adam_response || {}, {
	        autoSpeak: voiceAudioUnlocked,
	        allowAlreadyRenderedAutoSpeak: true
	      });
      renderCodexApproval(codexApproval);
      renderVoiceApproval(voicePending);
      if (voiceModeStartBtn) {
        voiceModeStartBtn.disabled = voiceRunning;
        voiceModeStartBtn.textContent = voiceRunning ? "Watcher běží" : "Spustit watcher";
        voiceModeStartBtn.classList.toggle("active", voiceRunning);
      }
      if (voiceModeStopBtn) {
        voiceModeStopBtn.disabled = !voiceRunning;
        voiceModeStopBtn.textContent = voiceRunning ? "Zastavit watcher" : "Watcher neběží";
      }
      setDashboardStatusSignal(
        "voice",
        voicePendingActionable || codexApprovalActive || voiceBridgeWarn ? "warn" : "ok",
        voicePendingActionable
          ? "Čeká hlasový pokyn na převzetí Adamem"
          : codexApprovalActive
          ? "Codex čeká na systémové potvrzení"
          : voiceBridgeWarn
          ? voiceBridgeMessage
          : "Hlasový vstup v Cockpitu je připravený"
      );
      updateVoiceModeUi();
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
      const res = await fetch(url, {cache: "no-store"});
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

    async function openProjectAuditModal() {
      projectAuditModal.classList.remove("hidden");
      projectAuditStatus.textContent = "Načítám systémový audit...";
      projectAuditText.textContent = "";
      await Promise.all([
        fetchJson("/api/project-audit?mode=quick")
          .then((data) => renderProjectAuditReport(data))
          .catch((err) => {
            recordFrontendError(err);
            projectAuditStatus.textContent = `Chyba načtení systémového auditu: ${err}`;
          }),
        loadRecentProjectAuditReports(),
      ]);
    }

    function closeProjectAuditModal() {
      projectAuditModal.classList.add("hidden");
    }

    function renderProjectAuditReport(data) {
      projectAuditStatus.textContent = data.message || "Systémový audit načten.";
      projectAuditText.textContent = data.report || "Report je prázdný.";
    }

    async function loadRecentProjectAuditReports() {
      try {
        const data = await fetchJson("/api/project-audit/recent?limit=5");
        renderRecentProjectAuditReports(data.reports || []);
      } catch (err) {
        recordFrontendError(err);
        projectAuditRecentList.innerHTML = `<div class="muted">Nelze načíst uložené audity: ${escapeHtml(err.message || String(err))}</div>`;
      }
    }

    function renderRecentProjectAuditReports(reports) {
      projectAuditRecentList.innerHTML = "";
      if (!reports.length) {
        projectAuditRecentList.innerHTML = '<div class="muted">Zatím není uložený žádný audit.</div>';
        return;
      }
      reports.forEach((report) => {
        const item = document.createElement("div");
        item.className = "project-row";
        item.innerHTML = `
          <div>
            <strong>${escapeHtml(report.name || "")}</strong>
            <div class="project-meta">${escapeHtml(report.modified_at || "")} · ${Number(report.size || 0)} B</div>
            <div class="project-meta">${escapeHtml(report.path || "")}</div>
          </div>
          <button class="secondary" type="button">Načíst</button>
        `;
        item.querySelector("button").addEventListener("click", () => loadProjectAuditReport(report.name || ""));
        projectAuditRecentList.appendChild(item);
      });
    }

    async function loadProjectAuditReport(name) {
      if (!name) return;
      projectAuditStatus.textContent = "Načítám uložený audit...";
      try {
        const data = await fetchJson(`/api/project-audit/report?name=${encodeURIComponent(name)}`);
        renderProjectAuditReport(data);
      } catch (err) {
        recordFrontendError(err);
        projectAuditStatus.textContent = `Chyba načtení uloženého auditu: ${err}`;
      }
    }

    async function saveProjectAuditReport() {
      const original = projectAuditSaveBtn.textContent;
      projectAuditSaveBtn.disabled = true;
      projectAuditSaveBtn.textContent = "Ukládám...";
      projectAuditStatus.textContent = "Generuji a ukládám full systémový audit...";
      try {
        const res = await fetch("/api/project-audit/save", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({mode: "full"}),
        });
        if (!res.ok) {
          throw new Error(`/api/project-audit/save returned ${res.status}`);
        }
        const data = await res.json();
        renderProjectAuditReport(data);
        await loadRecentProjectAuditReports();
      } catch (err) {
        recordFrontendError(err);
        projectAuditStatus.textContent = `Chyba uložení systémového auditu: ${err}`;
      } finally {
        projectAuditSaveBtn.disabled = false;
        projectAuditSaveBtn.textContent = original;
      }
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
	      const waitForCockpitAndReload = async () => {
	        await new Promise((resolve) => window.setTimeout(resolve, 2500));
	        for (let attempt = 1; attempt <= 45; attempt += 1) {
	          try {
	            const probe = await fetch("/api/server/health", {cache: "no-store"});
	            if (probe.ok) {
	              showMessage("Cockpit znovu běží. Obnovuji stránku...");
	              window.location.reload();
	              return;
	            }
	          } catch (probeErr) {
	            // Cockpit se prave restartuje; dalsi pokus probehne za chvili.
	          }
	          showMessage(`Čekám na návrat Cockpitu... pokus ${attempt}/45`);
	          await new Promise((resolve) => window.setTimeout(resolve, 1000));
	        }
	        showMessage("Cockpit se restartoval pomaleji než čekám. Zkus stránku obnovit ručně.");
	        dashboardRestartBtn.disabled = false;
	      };
	      try {
	        const res = await fetch("/api/cockpit/restart", {
	          method: "POST",
	          headers: {"Content-Type": "application/json"},
	          body: JSON.stringify({confirmed: true})
	        });
	        const data = await res.json();
	        showMessage(data.message || (data.ok ? "Restart zahájen." : "Restart se nepodařilo zahájit."));
	        if (data.ok) {
	          await waitForCockpitAndReload();
	        } else {
	          dashboardRestartBtn.disabled = false;
	        }
	      } catch (err) {
	        recordFrontendError(err);
	        showMessage("Spojení se při restartu přerušilo. Počkám, až Cockpit znovu odpoví.");
	        await waitForCockpitAndReload();
	      }
	    }

	    function formatAutosaveCleanupPlan(data) {
	      const plan = data.plan || {};
	      const runtime = data.runtime || {};
	      const reclaim = Number(plan.reclaim_gib || 0);
	      return [
	        data.message || "Autosave úklid spočítán.",
	        "",
	        `Retence: ponechat posledních ${plan.retention_days || 3} dní`,
	        `Pojistka: ponechat nejnovějších ${plan.keep_latest_snapshots || 12} časových snapshotů`,
	        `Timestampované soubory: ${plan.scanned_timestamped_files || 0}`,
	        `Chráněné soubory: ${plan.protected_timestamped_files || 0}`,
	        `Ke smazání: ${plan.delete_count || 0}`,
	        `Odhad uvolnění: ${reclaim.toFixed(2)} GiB`,
	        `Autosave watchery: ${Number(runtime.watcher_count || 0)} (očekáván 1)`,
	        runtime.warning ? `Varování: ${runtime.warning}` : "Autosave watcher stav: OK",
	        "",
	        data.safety_note || "Obsah autosave logů se nečte."
	      ].join("\\n");
	    }

	    async function previewAutosaveCleanup(button) {
	      const targetButton = button || autosaveCleanupPreviewBtn || dashboardAutosaveCleanupBtn;
	      targetButton.disabled = true;
	      if (autosaveCleanupStatus) autosaveCleanupStatus.textContent = "Počítám autosave úklid...";
	      if (autosaveCleanupOutput) autosaveCleanupOutput.textContent = "";
	      try {
	        const data = await postJson("/api/session-autosave/cleanup", {
	          retention_days: 3,
	          keep_latest_snapshots: 12,
	          apply: false
	        });
	        currentAutosaveCleanupPlan = data.plan || null;
	        if (autosaveCleanupStatus) autosaveCleanupStatus.textContent = data.message || "Dry-run hotov.";
	        if (autosaveCleanupOutput) autosaveCleanupOutput.textContent = formatAutosaveCleanupPlan(data);
	        if (autosaveCleanupApplyBtn) autosaveCleanupApplyBtn.disabled = !((data.plan || {}).delete_count > 0);
	        servicePanel.open = true;
	        showMessage(data.message || "Autosave úklid spočítán.");
	      } catch (err) {
	        recordFrontendError(err);
	        if (autosaveCleanupStatus) autosaveCleanupStatus.textContent = `Chyba autosave dry-runu: ${err}`;
	        if (autosaveCleanupApplyBtn) autosaveCleanupApplyBtn.disabled = true;
	        showMessage(`Chyba autosave dry-runu: ${err}`);
	      } finally {
	        targetButton.disabled = false;
	      }
	    }

	    async function applyAutosaveCleanup() {
	      if (!currentAutosaveCleanupPlan) {
	        await previewAutosaveCleanup(autosaveCleanupPreviewBtn);
	      }
	      const plan = currentAutosaveCleanupPlan || {};
	      const deleteCount = Number(plan.delete_count || 0);
	      const reclaim = Number(plan.reclaim_gib || 0);
	      if (!deleteCount) {
	        if (autosaveCleanupStatus) autosaveCleanupStatus.textContent = "Není co mazat.";
	        return;
	      }
	      const ok = window.confirm(
	        "Vyčistit staré autosave snapshoty?\\n\\n" +
	        `Smazat se má ${deleteCount} starých timestampovaných souborů.\\n` +
	        `Odhad uvolnění: ${reclaim.toFixed(2)} GiB.\\n\\n` +
	        "Zůstanou latest soubory, poslední 3 dny a nejnovější pojistné snapshoty."
	      );
	      if (!ok) return;
	      autosaveCleanupApplyBtn.disabled = true;
	      if (autosaveCleanupPreviewBtn) autosaveCleanupPreviewBtn.disabled = true;
	      if (autosaveCleanupStatus) autosaveCleanupStatus.textContent = "Mažu staré autosave snapshoty...";
	      try {
	        const data = await postJson("/api/session-autosave/cleanup", {
	          retention_days: 3,
	          keep_latest_snapshots: 12,
	          apply: true,
	          confirmation_text: "SMAZAT STARE AUTOSAVE"
	        });
	        currentAutosaveCleanupPlan = null;
	        if (autosaveCleanupStatus) autosaveCleanupStatus.textContent = data.message || "Autosave úklid hotov.";
	        if (autosaveCleanupOutput) autosaveCleanupOutput.textContent = formatAutosaveCleanupPlan(data);
	        showMessage(data.message || "Autosave úklid hotov.");
	        await refresh({silent: true, includeSecondary: false});
	        await previewAutosaveCleanup(autosaveCleanupPreviewBtn);
	      } catch (err) {
	        recordFrontendError(err);
	        if (autosaveCleanupStatus) autosaveCleanupStatus.textContent = `Chyba autosave úklidu: ${err}`;
	        showMessage(`Chyba autosave úklidu: ${err}`);
	      } finally {
	        if (autosaveCleanupPreviewBtn) autosaveCleanupPreviewBtn.disabled = false;
	        if (autosaveCleanupApplyBtn) autosaveCleanupApplyBtn.disabled = !currentAutosaveCleanupPlan || !(currentAutosaveCleanupPlan.delete_count > 0);
	      }
	    }

	    function formatDevRunnerResult(data) {
	      const parts = [data.message || "Vývojová akce dokončena."];
	      const stdout = String(data.stdout || "").trim();
	      const stderr = String(data.stderr || "").trim();
	      if (stdout) {
	        parts.push(`STDOUT:\\n${stdout}`);
	      }
	      if (stderr) {
	        parts.push(`STDERR:\\n${stderr}`);
	      }
	      return parts.join("\\n\\n");
	    }

	    async function runDevRunnerAction(actionId, button) {
	      const action = String(actionId || "").trim();
	      if (!action) return;
	      if (button) button.disabled = true;
	      if (devRunnerOutput) {
	        devRunnerOutput.textContent = "Spouštím vývojovou akci...";
	      }
	      showMessage("Spouštím vývojovou akci...");
	      try {
	        const data = await postJson("/api/dev-runner/run", {action_id: action});
	        if (devRunnerOutput) {
	          devRunnerOutput.textContent = formatDevRunnerResult(data);
	        }
	        showMessage(data.message || (data.ok ? "Vývojová akce prošla." : "Vývojová akce selhala."));
	        await refresh({silent: true, includeSecondary: false});
	      } catch (err) {
	        recordFrontendError(err);
	        if (devRunnerOutput) {
	          devRunnerOutput.textContent = `Vývojová akce selhala: ${err}`;
	        }
	        showMessage(`Vývojová akce selhala: ${err}`);
	      } finally {
	        if (button) button.disabled = false;
	      }
	    }

	    function isRemoteCockpitClient() {
	      const host = String(window.location.hostname || "").toLowerCase();
	      return Boolean(host && !["127.0.0.1", "localhost", "::1"].includes(host));
	    }

	    function isMobileCockpitClient() {
	      const userAgent = String(navigator.userAgent || "").toLowerCase();
	      const platform = String(navigator.platform || "").toLowerCase();
	      return /iphone|ipad|ipod|android/.test(userAgent) || /iphone|ipad|ipod/.test(platform);
	    }

	    function shouldUseSystemSpeechFallback() {
	      return !(isRemoteCockpitClient() && isMobileCockpitClient());
	    }

	    let voiceAudioContext = null;
	    let voiceAudioUnlocked = false;

	    function updateVoiceAudioUnlockUi(opened) {
	      if (!voiceAudioUnlockBtn) return;
	      voiceAudioUnlockBtn.classList.toggle("active", Boolean(opened));
	      voiceAudioUnlockBtn.textContent = opened ? "Audiokanál otevřený" : "Otevřít audiokanál";
	      voiceAudioUnlockBtn.title = opened
	        ? "Audio v tomto prohlížeči je připravené pro Adamovy odpovědi."
	        : "Na iPhonu jednou klepni, aby prohlížeč dovolil přehrávat Adamovy odpovědi.";
	    }

	    function getVoiceAudioContext() {
	      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
	      if (!AudioContextClass) return null;
	      if (voiceAudioContext && voiceAudioContext.state === "closed") {
	        voiceAudioContext = null;
	        voiceAudioUnlocked = false;
	        updateVoiceAudioUnlockUi(false);
	      }
	      if (!voiceAudioContext) {
	        voiceAudioContext = new AudioContextClass();
	        const observedContext = voiceAudioContext;
	        observedContext.addEventListener("statechange", () => {
	          if (voiceAudioContext !== observedContext) return;
	          const state = String(observedContext.state || "unknown");
	          const running = state === "running";
	          if (!running) voiceAudioUnlocked = false;
	          updateVoiceAudioUnlockUi(running && voiceAudioUnlocked);
	          recordVoiceFrontendEvent("audio_context_state_changed", {state});
	        });
	      }
	      return voiceAudioContext;
	    }

	    async function ensureVoiceAudioContextRunning(context) {
	      if (!context) return false;
	      const state = String(context.state || "unknown");
	      if (["suspended", "interrupted"].includes(state)) {
	        await context.resume();
	      }
	      if (context.state !== "running") {
	        throw new Error(`Audiokanal zustal ve stavu ${context.state || "unknown"}.`);
	      }
	      return true;
	    }

	    async function primeVoiceAudioContextFromGesture() {
	      const context = getVoiceAudioContext();
	      if (!context) return false;
	      await ensureVoiceAudioContextRunning(context);
	      const source = context.createBufferSource();
	      source.buffer = context.createBuffer(1, 1, 22050);
	      source.connect(context.destination);
	      source.start(0);
	      if (!voiceAudioUnlocked) {
	        autoSpokenAdamResponseKey = latestAdamResponseKey;
	      }
	      voiceAudioUnlocked = true;
	      updateVoiceAudioUnlockUi(true);
	      return true;
	    }

	    async function primeMobileVoiceAudioForCommandGesture(source = "voice_command") {
	      if (!isRemoteCockpitClient() || !isMobileCockpitClient()) return voiceAudioUnlocked;
	      const contextState = voiceAudioContext ? String(voiceAudioContext.state || "unknown") : "missing";
	      if (voiceAudioUnlocked && contextState === "running") return true;
	      try {
	        const opened = await primeVoiceAudioContextFromGesture();
	        recordVoiceFrontendEvent(opened ? "audio_channel_auto_opened" : "audio_channel_auto_open_unavailable", {source});
	        return opened;
	      } catch (err) {
	        updateVoiceAudioUnlockUi(false);
	        recordVoiceFrontendEvent("audio_channel_auto_open_failed", {source, error: String(err)});
	        return false;
	      }
	    }

		    async function openVoiceAudioChannel() {
		      if (!voiceAudioUnlockBtn) return;
		      voiceAudioUnlockBtn.disabled = true;
		      showMessage("Otevírám audiokanál pro odpovědi Adama...");
		      if (voiceCommandStatus) voiceCommandStatus.textContent = "Otevírám audiokanál pro odpovědi Adama...";
		      try {
		        const opened = await primeVoiceAudioContextFromGesture();
		        if (opened) {
		          showMessage("Audiokanál je otevřený. Spouštím watcher pro hlasové pokyny...");
		          if (voiceCommandStatus) voiceCommandStatus.textContent = "Audiokanál je otevřený. Watcher kontroluji nebo spouštím...";
		          await ensureVoiceModeWatcherRunningFromAudioChannel();
		        } else {
		          showMessage("Tento prohlížeč nepodporuje otevření webového audiokanálu.");
		          if (voiceCommandStatus) voiceCommandStatus.textContent = "Tento prohlížeč nepodporuje otevření webového audiokanálu.";
		        }
		      } catch (err) {
		        recordFrontendError(err);
		        updateVoiceAudioUnlockUi(false);
		        showMessage(`Audiokanál se nepodařilo otevřít: ${err}`);
		        if (voiceCommandStatus) voiceCommandStatus.textContent = `Audiokanál se nepodařilo otevřít: ${err}`;
		      } finally {
		        voiceAudioUnlockBtn.disabled = false;
		      }
		    }

	    function base64ToArrayBuffer(base64) {
	      const binary = window.atob(String(base64 || ""));
	      const bytes = new Uint8Array(binary.length);
	      for (let index = 0; index < binary.length; index += 1) {
	        bytes[index] = binary.charCodeAt(index);
	      }
	      return bytes.buffer;
	    }

	    async function playVoiceAudioBase64(edgeData) {
	      if (!voiceAudioUnlocked || !edgeData || !edgeData.audio_base64) return false;
	      const context = getVoiceAudioContext();
	      if (!context) return false;
	      await ensureVoiceAudioContextRunning(context);
	      const audioBuffer = await context.decodeAudioData(base64ToArrayBuffer(edgeData.audio_base64));
	      await new Promise((resolve, reject) => {
	        const source = context.createBufferSource();
	        source.buffer = audioBuffer;
	        source.connect(context.destination);
	        source.onended = resolve;
	        try {
	          source.start(0);
	        } catch (err) {
	          reject(err);
	        }
	      });
	      return true;
	    }

	    function markVoiceResponseNeedsTap(message) {
	      if (voiceLastResponseSpeakBtn) {
	        voiceLastResponseSpeakBtn.textContent = isRemoteCockpitClient() ? "Přehrát v iPhonu" : "Přehrát Adamovu odpověď";
	        voiceLastResponseSpeakBtn.classList.add("needs-tap");
	        voiceLastResponseSpeakBtn.disabled = false;
	      }
	      showMessage(message || "Prohlížeč zablokoval automatické přehrání. Klepni na tlačítko Přehrát v iPhonu.");
	    }

	    function isExpectedAudioAutoplayBlock(error) {
	      const name = String(error && error.name || "").toLowerCase();
	      const message = String(error && error.message || error || "").toLowerCase();
	      return name === "notallowederror"
	        || message.includes("not allowed by the user agent")
	        || message.includes("user denied permission")
	        || message.includes("play() failed because the user didn't interact");
	    }

	    async function speakText(text, button, label, options = {}) {
	      const cleaned = (text || "").trim();
	      if (!cleaned) {
	        showMessage("Nejdřív označ text, který mám přečíst.");
	        return;
	      }
	      const allowSystemFallback = options.allowSystemFallback !== false && shouldUseSystemSpeechFallback();
	      button.disabled = true;
	      button.classList.remove("needs-tap");
	      showMessage(label || "Čtu nahlas...");
	      try {
	        if (options.userGesture && isRemoteCockpitClient()) {
	          try {
	            const recovered = await primeVoiceAudioContextFromGesture();
	            recordVoiceFrontendEvent(recovered ? "audio_context_recovered_from_gesture" : "audio_context_recovery_unavailable", {source: "manual_play"});
	          } catch (audioPrimeErr) {
	            voiceAudioUnlocked = false;
	            updateVoiceAudioUnlockUi(false);
	            recordVoiceFrontendEvent("audio_context_recovery_failed", {source: "manual_play", error: String(audioPrimeErr)});
	          }
	        }
	        const edgeRes = await fetch("/api/speech/edge-tts", {
	          method: "POST",
	          headers: {"Content-Type": "application/json"},
	          body: JSON.stringify({text: cleaned})
	        });
	        const edgeData = await edgeRes.json();
	        if (edgeData.ok && edgeData.audio_base64) {
	          if (isRemoteCockpitClient() && voiceAudioUnlocked) {
	            try {
	              await playVoiceAudioBase64(edgeData);
	              updateVoiceAudioUnlockUi(true);
	              button.textContent = button === voiceLastResponseSpeakBtn ? "Přehrát Adamovu odpověď" : button.textContent;
	              recordVoiceFrontendEvent("audio_play_succeeded", {player: "audio_context"});
	              showMessage(edgeData.message || "Přehráno v tomto prohlížeči.");
	              return;
	            } catch (contextPlayErr) {
	              if (isExpectedAudioAutoplayBlock(contextPlayErr)) {
	                voiceAudioUnlocked = false;
	                updateVoiceAudioUnlockUi(false);
	                recordVoiceFrontendEvent("audio_autoplay_blocked", {player: "audio_context"});
	              } else {
	                recordFrontendError(contextPlayErr);
	              }
	            }
	          }
	          const audio = new Audio(`data:${edgeData.mime_type || "audio/mpeg"};base64,${edgeData.audio_base64}`);
	          try {
	            await audio.play();
	            button.textContent = button === voiceLastResponseSpeakBtn ? "Přehrát Adamovu odpověď" : button.textContent;
	            recordVoiceFrontendEvent("audio_play_succeeded", {player: "html_audio"});
	            showMessage(edgeData.message || "Přečteno českým mužským hlasem.");
	            return;
	          } catch (playErr) {
	            const autoplayBlocked = isExpectedAudioAutoplayBlock(playErr);
	            if (autoplayBlocked) {
	              recordVoiceFrontendEvent("audio_autoplay_blocked", {player: "html_audio"});
	            } else {
	              recordFrontendError(playErr);
	            }
	            if (!allowSystemFallback) {
	              markVoiceResponseNeedsTap(autoplayBlocked
	                ? "iPhone zablokoval automatické přehrání. Klepni na Přehrát v iPhonu."
	                : "Přehrání v prohlížeči se nepodařilo. Klepni na Přehrát v iPhonu.");
	              return;
	            }
	          }
	        }
	        if (!allowSystemFallback) {
	          markVoiceResponseNeedsTap("Přehrání v prohlížeči se nepodařilo. Klepni na Přehrát v iPhonu.");
	          return;
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
		    let latestAdamResponseKey = "";
		    let autoSpokenAdamResponseKey = "";
		    let voiceReplyPollTimer = null;
		    let voiceReplyPollUntil = 0;
		    let voiceReplyExpectedUserText = "";
		    let voiceReplyMinCreatedAt = 0;

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

	    function directVoiceRecordingSupported() {
	      return Boolean(
	        window.isSecureContext &&
	        navigator.mediaDevices &&
	        navigator.mediaDevices.getUserMedia &&
	        window.MediaRecorder
	      );
	    }

	    function updateVoiceRecordingAvailability() {
	      if (directVoiceRecordingSupported()) {
	        voiceRecordBtn.textContent = "Nahrát pokyn";
	        voiceRecordBtn.title = "";
	        voiceRecordBtn.classList.remove("secondary");
	        voiceRecordBtn.classList.add("primary");
	        return;
	      }
	      voiceRecordBtn.textContent = "Diktovat text";
	      voiceRecordBtn.title = "Na iPhonu přes HTTP prohlížeč nepustí mikrofon. Použij diktování do textového pole.";
	      voiceRecordBtn.classList.remove("primary");
	      voiceRecordBtn.classList.add("secondary");
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
	      voiceStopBtn.classList.add("hidden");
	      if (voiceStopTimer) {
	        window.clearTimeout(voiceStopTimer);
	        voiceStopTimer = null;
	      }
	    }

		    function updateVoiceModeUi() {
		      voiceModeToggleBtn.textContent = voiceModeEnabled ? "Starý poslech: zapnuto" : "Starý poslech: vypnuto";
		      voiceModeToggleBtn.setAttribute("aria-pressed", voiceModeEnabled ? "true" : "false");
		      voiceModeToggleBtn.classList.toggle("active", voiceModeEnabled);
		      const watcherRunning = Boolean(latestVoiceModeRuntime && latestVoiceModeRuntime.running);
		      if (voiceModeEnabled) {
		        voiceCommandStatus.textContent = watcherRunning
		          ? "Nahraj pokyn, nebo napiš text. Cockpit ho pošle Adamovi přímo; starý watcher běží jen jako záloha."
		          : "Nahraj pokyn, nebo napiš text. Cockpit ho pošle Adamovi přímo.";
		      } else {
		        voiceCommandStatus.textContent = "Nahraj pokyn, nebo napiš text. Cockpit ho pošle Adamovi přímo.";
		      }
		    }

		    function voiceResponseKey(lastResponse) {
		      const text = String(lastResponse && lastResponse.adam_response || "").trim();
		      if (!text) return "";
		      const createdAt = String(lastResponse && lastResponse.created_at || "").trim();
		      return `${createdAt}|${text}`;
		    }

		    function normalizeVoiceText(value) {
		      return String(value || "").replace(/\\s+/g, " ").trim();
		    }

		    function voiceResponseMatchesCurrentRequest(lastResponse, options = {}) {
		      const expectedUserText = normalizeVoiceText(options.expectedUserText || "");
		      if (expectedUserText) {
		        const actualUserText = normalizeVoiceText(lastResponse && lastResponse.user_text || "");
		        if (actualUserText !== expectedUserText) {
		          return false;
		        }
		      }
		      const minCreatedAt = Number(options.minCreatedAt || 0);
		      if (minCreatedAt) {
		        const createdAtMs = Date.parse(String(lastResponse && lastResponse.created_at || ""));
		        if (!Number.isFinite(createdAtMs) || createdAtMs < minCreatedAt) {
		          return false;
		        }
		      }
		      return true;
		    }

		    function renderVoiceLastResponse(lastResponse, options = {}) {
		      const text = String(lastResponse && lastResponse.adam_response || "").trim();
		      const responseKey = voiceResponseKey(lastResponse);
		      const isNewResponse = Boolean(responseKey && responseKey !== latestAdamResponseKey);
		      latestAdamResponseText = text;
		      if (responseKey) {
		        latestAdamResponseKey = responseKey;
		      }
		      if (!voiceLastResponseCard || !voiceLastResponseText) return;
		      voiceLastResponseCard.classList.toggle("hidden", !text);
		      voiceLastResponseText.textContent = text || "Zatím není uložená žádná Adamova odpověď.";
		      if (voiceLastResponseSpeakBtn) {
		        voiceLastResponseSpeakBtn.disabled = !text;
		      }
		      if (text && voiceCommandDetails && (options.openPanel || isNewResponse)) {
		        voiceCommandDetails.open = true;
		      }
	      const allowRenderedAutoSpeak = options.allowAlreadyRenderedAutoSpeak === true;
	      if (text && options.autoSpeak && responseKey && responseKey !== autoSpokenAdamResponseKey && (isNewResponse || allowRenderedAutoSpeak)) {
	        autoSpokenAdamResponseKey = responseKey;
	        recordVoiceFrontendEvent("voice_autospeak_requested", {response_created_at: String(lastResponse && lastResponse.created_at || "")});
	        speakText(text, voiceLastResponseSpeakBtn, "Čtu Adamovu odpověď nahlas...", {allowSystemFallback: shouldUseSystemSpeechFallback()});
	      }
		    }

		    async function refreshVoiceLatestResponse(options = {}) {
		      try {
		        const res = await fetch("/api/voice-mode/latest-response");
		        const data = await res.json();
		        if (data && data.available) {
		          if (!voiceResponseMatchesCurrentRequest(data, options)) {
		            return null;
		          }
		          renderVoiceLastResponse(data, {
		            openPanel: true,
		            autoSpeak: options.autoSpeak === true,
		            allowAlreadyRenderedAutoSpeak: true
		          });
		          return data;
		        }
		      } catch (err) {
		        recordFrontendError(err);
		      }
		      return null;
		    }

		    const VOICE_REPLY_POLL_DURATION_MS = 600000;

		    function startVoiceReplyPolling({autoSpeak = true, durationMs = VOICE_REPLY_POLL_DURATION_MS, expectedUserText = ""} = {}) {
		      voiceReplyExpectedUserText = expectedUserText;
		      voiceReplyMinCreatedAt = Date.now() - 5000;
		      voiceReplyPollUntil = Math.max(voiceReplyPollUntil, Date.now() + durationMs);
		      if (voiceReplyPollTimer) return;
		      voiceReplyPollTimer = window.setInterval(async () => {
		        if (Date.now() > voiceReplyPollUntil) {
		          window.clearInterval(voiceReplyPollTimer);
			          voiceReplyPollTimer = null;
			          return;
			        }
			        await refresh({silent: true, includeSecondary: false});
			        await refreshVoiceLatestResponse({
			          autoSpeak,
			          expectedUserText: voiceReplyExpectedUserText,
			          minCreatedAt: voiceReplyMinCreatedAt
			        });
			      }, 3000);
			      window.setTimeout(async () => {
			        await refresh({silent: true, includeSecondary: false});
			        await refreshVoiceLatestResponse({
			          autoSpeak,
			          expectedUserText: voiceReplyExpectedUserText,
			          minCreatedAt: voiceReplyMinCreatedAt
			        });
			      }, 1000);
			    }

		    function pendingNeedsCockpitApproval(pending) {
		      if (!pending || !pending.pending) return false;
		      if (pending.approval_status === "approved") return false;
		      const reason = String(pending.reason || pending.status || "");
		      return [
		        "requires_confirmation",
		        "outbound_confirmation"
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

		    function renderCodexApproval(approval) {
		      if (!codexApprovalCard) return;
			      const active = Boolean(approval && approval.active);
			      codexApprovalCard.classList.toggle("hidden", !active);
			      if (!active) {
			        lastCodexApprovalActive = false;
			        return;
			      }
			      const becameActive = !lastCodexApprovalActive;
			      lastCodexApprovalActive = true;
		      const reason = String(approval.reason || approval.message || "Codex čeká na systémové potvrzení.").trim();
		      const command = String(approval.command || approval.action || "").trim();
		      const risk = String(approval.risk || "").trim();
		      const nextStep = String(approval.next_step || "").trim();
		      const confirmationText = String(approval.confirmation_text || "").trim();
		      if (codexApprovalReason) {
		        codexApprovalReason.textContent = reason;
		      }
		      if (codexApprovalCommand) {
		        codexApprovalCommand.textContent = command || "V Codexu je otevřená systémová žádost o povolení.";
		      }
		      if (codexApprovalRisk) {
		        codexApprovalRisk.textContent = risk || "Běžné systémové potvrzení. Před schválením se řiď textem v Codexu, pokud ukazuje vyšší riziko.";
		      }
		      if (codexApprovalNextStep) {
		        codexApprovalNextStep.textContent = nextStep || "Otevři aktivní Codex relaci a schval nebo zamítni systémové potvrzení podle zobrazeného textu.";
		      }
		      if (codexApprovalConfirmationBlock) {
		        codexApprovalConfirmationBlock.classList.toggle("hidden", !confirmationText);
		      }
		      if (codexApprovalConfirmationText) {
		        codexApprovalConfirmationText.textContent = confirmationText;
		      }
		      if (codexApprovalConfirmationInput && confirmationText && codexApprovalConfirmationInput.value.trim() !== confirmationText) {
		        codexApprovalConfirmationInput.value = confirmationText;
		      }
		      if (codexApprovalSendConfirmationBtn) {
		        codexApprovalSendConfirmationBtn.classList.toggle("hidden", !confirmationText);
		        codexApprovalSendConfirmationBtn.disabled = !confirmationText;
		      }
			      if (codexApprovalCopyConfirmationBtn) {
			        codexApprovalCopyConfirmationBtn.classList.toggle("hidden", !confirmationText);
			        codexApprovalCopyConfirmationBtn.disabled = !confirmationText;
			      }
			      if (becameActive) {
			        if (voiceCommandDetails) voiceCommandDetails.open = true;
			        showMessage(confirmationText
			          ? "Codex čeká na potvrzení. Přesná potvrzovací věta je v kartě Hlas."
			          : "Codex čeká na potvrzení. Karta je v sekci Hlas."
			        );
			        window.setTimeout(() => {
			          try {
			            codexApprovalCard.scrollIntoView({block: "center", behavior: "smooth"});
			          } catch (_err) {
			            codexApprovalCard.scrollIntoView();
			          }
			        }, 100);
			      }
			    }

		    function renderVoiceBridgeSwitcher(voiceBridge) {
		      if (!voiceBridgeSwitcher || !voiceBridgeSwitcherStatus || !voiceBridgeSwitcherActions) return;
		      const markedTty = String(voiceBridge.marked_tty || "");
		      const effectiveTty = String(voiceBridge.effective_tty || "");
		      const managedLabels = voiceBridge.managed_codex_labels && typeof voiceBridge.managed_codex_labels === "object"
		        ? voiceBridge.managed_codex_labels
		        : {};
		      const orphanedLabels = voiceBridge.orphaned_janicka_labels && typeof voiceBridge.orphaned_janicka_labels === "object"
		        ? voiceBridge.orphaned_janicka_labels
		        : {};
		      const nonTargetLabels = {...managedLabels, ...orphanedLabels};
		      const codexTtys = Array.isArray(voiceBridge.codex_ttys)
		        ? voiceBridge.codex_ttys.map((item) => String(item || "")).filter(Boolean)
		        : [];
		      const bridgeTtys = codexTtys.filter((tty) => !nonTargetLabels[tty]);
		      const staleTtys = bridgeTtys.filter((tty) => tty !== effectiveTty);
		      voiceBridgeSwitcher.classList.toggle("hidden", codexTtys.length === 0);
		      if (codexTtys.length === 0) {
		        voiceBridgeSwitcherStatus.textContent = "Není nalezená žádná aktivní Codex relace.";
		        voiceBridgeSwitcherActions.innerHTML = "";
		        return;
		      }
		      const managedText = Object.keys(managedLabels).length
		        ? ` Spravované relace: ${Object.keys(managedLabels).map((tty) => `${tty}=${managedLabels[tty]}`).join(", ")}.`
		        : "";
		      const orphanedText = Object.keys(orphanedLabels).length
		        ? ` Staré Janička relace: ${Object.keys(orphanedLabels).map((tty) => `${tty}=${orphanedLabels[tty]}`).join(", ")}.`
		        : "";
		      voiceBridgeSwitcherStatus.textContent = markedTty
		        ? `Marker: ${markedTty}. Efektivní cíl: ${effectiveTty || "nezjištěno"}.${managedText}${orphanedText}`
		        : `Marker zatím není nastavený. Efektivní cíl: ${effectiveTty || "nezjištěno"}.${managedText}${orphanedText}`;
		      voiceBridgeSwitcherActions.innerHTML = bridgeTtys.map((tty) => {
		        const active = tty === markedTty;
		        const effective = tty === effectiveTty && tty !== markedTty;
		        const label = active
		          ? `${tty} ✓ marker`
		          : effective
		            ? `${tty} ✓ aktivní cíl`
		            : `Nastavit ${tty}`;
		        return `<button class="${active || effective ? "primary" : "secondary"}" data-voice-bridge-tty="${escapeHtml(tty)}">${escapeHtml(label)}</button>`;
		      }).join("");
		      if (effectiveTty && staleTtys.length > 0) {
		        voiceBridgeSwitcherActions.insertAdjacentHTML(
		          "beforeend",
		          `<button class="secondary" data-voice-bridge-cleanup="1">Ukončit staré relace (${staleTtys.length})</button>`
		        );
		      }
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

		    async function terminateStaleVoiceBridgeSessions(button) {
		      if (button) button.disabled = true;
		      try {
		        const preview = await postJson("/api/voice-bridge/terminate-stale", {confirmed: false});
		        const staleTtys = Array.isArray(preview.stale_ttys) ? preview.stale_ttys.join(", ") : "";
		        if (preview.status === "no_stale_sessions") {
		          showMessage(preview.message || "Žádné staré Codex relace k ukončení.");
		          await refresh({silent: true, includeSecondary: false});
		          return;
		        }
		        if (preview.status !== "confirmation_required") {
		          showMessage(preview.message || "Staré Codex relace nejde bezpečně určit.");
		          return;
		        }
		        const protectedTty = preview.protected_tty || "nezjištěno";
		        const ok = window.confirm(`Ukončit staré Codex relace ${staleTtys}? Chráněná relace ${protectedTty} zůstane běžet.`);
		        if (!ok) {
		          showMessage("Ukončení starých Codex relací zrušeno.");
		          return;
		        }
		        const data = await postJson("/api/voice-bridge/terminate-stale", {confirmed: true});
		        showMessage(data.message || (data.ok ? "Staré Codex relace ukončeny." : "Ukončení starých Codex relací selhalo."));
		        await refresh({silent: true, includeSecondary: false});
		      } catch (err) {
		        recordFrontendError(err);
		        showMessage(`Ukončení starých Codex relací selhalo: ${err}`);
		      } finally {
		        if (button) button.disabled = false;
		      }
		    }

		    function formatSafeReadonlyResult(data) {
		      const capability = data.capability || {};
		      const result = data.result || {};
		      const lines = [
		        `${capability.label || "Kontrola"}: ${data.message || "hotovo"}`,
		      ];
		      if (result.voice_bridge && result.voice_bridge.message) {
		        lines.push(`Voice bridge: ${result.voice_bridge.message}`);
		      }
		      if (Array.isArray(result.sessions)) {
		        const sessions = result.sessions.map((item) => {
		          const pids = Array.isArray(item.pids) ? item.pids.join(",") : "";
		          const roots = Array.isArray(item.root_pids) ? item.root_pids.join(",") : "";
		          return `${item.tty || "?"} pids=${pids || "-"} roots=${roots || "-"}`;
		        });
		        lines.push(`Codex relace: ${sessions.length ? sessions.join(" | ") : "žádná"}`);
		      }
		      if (result.git && result.git.message) {
		        lines.push(`Git: ${result.git.message}`);
		      }
		      if (result.backup && result.backup.message) {
		        lines.push(`Záloha: ${result.backup.message}`);
		      }
		      return lines.join("\\n");
		    }

		    async function runSafeReadonlyCapability(capabilityId, button) {
		      const capability = String(capabilityId || "").trim();
		      if (!capability) return;
		      if (button) button.disabled = true;
		      if (safeReadonlyResult) {
		        safeReadonlyResult.textContent = "Spouštím read-only kontrolu...";
		      }
		      try {
		        const data = await postJson("/api/voice-mode/safe-readonly/run", {capability_id: capability});
		        if (safeReadonlyResult) {
		          safeReadonlyResult.textContent = data.ok
		            ? formatSafeReadonlyResult(data)
		            : (data.message || "Read-only kontrola selhala.");
		        }
		        showMessage(data.message || (data.ok ? "Read-only kontrola dokončena." : "Read-only kontrola selhala."));
		        await refresh({silent: true, includeSecondary: false});
		      } catch (err) {
		        recordFrontendError(err);
		        if (safeReadonlyResult) {
		          safeReadonlyResult.textContent = `Read-only kontrola selhala: ${err}`;
		        }
		        showMessage(`Read-only kontrola selhala: ${err}`);
		      } finally {
		        if (button) button.disabled = false;
		      }
		    }

		    async function speakLastAdamResponse() {
		      await speakText(
		        latestAdamResponseText,
		        voiceLastResponseSpeakBtn,
		        "Přehrávám poslední Adamovu odpověď v tomto prohlížeči...",
		        {userGesture: true, allowSystemFallback: false}
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

		    async function clearCodexApprovalCard() {
		      if (codexApprovalClearBtn) codexApprovalClearBtn.disabled = true;
		      try {
		        const data = await postJson("/api/voice-mode/codex-approval/clear", {
		          confirmed: true,
		          note: "Vyčištěno z Cockpitu po ručním vyřešení nebo zrušení systémového potvrzení."
		        });
		        showMessage(data.message || (data.ok ? "Karta Codex potvrzení byla vyčištěna." : "Kartu se nepodařilo vyčistit."));
		        await refresh({silent: true, includeSecondary: false});
		      } catch (err) {
		        recordFrontendError(err);
		        showMessage(`Vyčištění karty Codex potvrzení selhalo: ${err}`);
		      } finally {
		        if (codexApprovalClearBtn) codexApprovalClearBtn.disabled = false;
		      }
		    }

		    async function copyCodexApprovalConfirmation() {
		      const text = String((codexApprovalConfirmationInput && codexApprovalConfirmationInput.value) || (codexApprovalConfirmationText && codexApprovalConfirmationText.textContent) || "").trim();
		      if (!text) return;
		      if (codexApprovalCopyConfirmationBtn) codexApprovalCopyConfirmationBtn.disabled = true;
		      try {
		        if (navigator.clipboard && navigator.clipboard.writeText) {
		          await navigator.clipboard.writeText(text);
		          showMessage("Potvrzovací věta je zkopírovaná.");
		        } else {
		          if (codexApprovalConfirmationInput) {
		            codexApprovalConfirmationInput.focus();
		            codexApprovalConfirmationInput.select();
		          }
		          showMessage("Větu nejde automaticky kopírovat, ale je označená v poli.");
		        }
		      } catch (err) {
		        recordFrontendError(err);
		        showMessage(`Kopírování potvrzovací věty selhalo: ${err}`);
		      } finally {
		        if (codexApprovalCopyConfirmationBtn) codexApprovalCopyConfirmationBtn.disabled = false;
		      }
		    }

		    async function sendCodexApprovalConfirmation() {
		      const text = String((codexApprovalConfirmationInput && codexApprovalConfirmationInput.value) || "").trim();
		      if (!text) {
		        showMessage("Nejdřív zkontroluj nebo opiš potvrzovací větu.");
		        if (codexApprovalConfirmationInput) codexApprovalConfirmationInput.focus();
		        return;
		      }
		      if (codexApprovalSendConfirmationBtn) codexApprovalSendConfirmationBtn.disabled = true;
		      if (voiceCommandStatus) voiceCommandStatus.textContent = "Odesílám potvrzovací větu Adamovi...";
		      try {
		        const data = await postJson("/api/speech/voice-text", {text});
		        if (data.ok) {
		          const savedHint = data.latest_voice_command_path ? ` Uloženo: ${data.latest_voice_command_path}.` : "";
		          showMessage(`${data.message || "Potvrzovací věta byla odeslána Adamovi."}${savedHint}`);
		          if (voiceCommandStatus) voiceCommandStatus.textContent = `${data.message || "Potvrzovací věta byla odeslána Adamovi."}${savedHint}`;
		          startVoiceReplyPolling({autoSpeak: true, expectedUserText: text});
		          await refresh({silent: true, includeSecondary: false});
		        } else {
		          showMessage(data.message || "Potvrzovací větu se nepodařilo odeslat.");
		          if (voiceCommandStatus) voiceCommandStatus.textContent = data.message || "Potvrzovací větu se nepodařilo odeslat.";
		        }
		      } catch (err) {
		        recordFrontendError(err);
		        showMessage(`Odeslání potvrzovací věty selhalo: ${err}`);
		        if (voiceCommandStatus) voiceCommandStatus.textContent = `Odeslání potvrzovací věty selhalo: ${err}`;
		      } finally {
		        if (codexApprovalSendConfirmationBtn) codexApprovalSendConfirmationBtn.disabled = false;
		      }
		    }

		    function toggleVoiceMode() {
		      voiceModeEnabled = !voiceModeEnabled;
		      localStorage.setItem("samanthaVoiceModeEnabled", voiceModeEnabled ? "true" : "false");
		      updateVoiceModeUi();
		    }

		    function isVoiceModeWatcherRunning() {
		      return Boolean(latestVoiceModeRuntime && latestVoiceModeRuntime.running);
		    }

			    async function ensureVoiceModeWatcherRunningFromAudioChannel() {
			      if (isVoiceModeWatcherRunning()) {
			        showMessage("Audiokanál je otevřený a watcher už běží.");
			        if (voiceCommandStatus) voiceCommandStatus.textContent = "Audiokanál je otevřený a watcher už běží.";
			        return;
			      }
			      await startVoiceModeWatcher({source: "audio_channel"});
			    }

		    async function startVoiceModeWatcher(options = {}) {
		      const fromAudioChannel = options.source === "audio_channel";
		      if (isVoiceModeWatcherRunning()) {
		        if (voiceCommandStatus) voiceCommandStatus.textContent = "Adam Voice Mode watcher už běží.";
		        updateVoiceModeUi();
		        return;
		      }
		      if (voiceModeStartBtn) voiceModeStartBtn.disabled = true;
		      if (voiceCommandStatus) {
		        voiceCommandStatus.textContent = fromAudioChannel
		          ? "Audiokanál otevřený. Spouštím záložní Adam Voice Mode watcher..."
		          : "Spouštím záložní Adam Voice Mode watcher...";
		      }
		      try {
		        const data = await postJson("/api/voice-mode/start", {});
		        if (voiceCommandStatus) voiceCommandStatus.textContent = data.message || "Záložní Adam Voice Mode watcher spuštěn.";
		        if (data.ok) {
		          voiceModeEnabled = true;
		          localStorage.setItem("samanthaVoiceModeEnabled", "true");
		        }
		        await refresh({silent: true, includeSecondary: false});
		      } catch (err) {
		        recordFrontendError(err);
		        if (voiceCommandStatus) voiceCommandStatus.textContent = `Adam Voice Mode watcher se nepodařilo spustit: ${err}`;
		      } finally {
		        updateVoiceModeUi();
		      }
		    }

		    async function stopVoiceModeWatcher() {
		      voiceModeStopBtn.disabled = true;
		      voiceCommandStatus.textContent = "Zastavuji záložní Adam Voice Mode watcher...";
		      try {
		        const data = await postJson("/api/voice-mode/stop", {});
		        voiceCommandStatus.textContent = data.message || "Záložní Adam Voice Mode watcher zastaven.";
		        await refresh({silent: true, includeSecondary: false});
		      } catch (err) {
		        recordFrontendError(err);
		        voiceCommandStatus.textContent = `Adam Voice Mode watcher se nepodařilo zastavit: ${err}`;
		      } finally {
		        updateVoiceModeUi();
		      }
		    }

	    async function startVoiceRecording() {
	      recordVoiceFrontendEvent("record_start_clicked", {step: "start_recording"});
	      if (voiceCommandDetails) {
	        voiceCommandDetails.open = true;
	      }
	      if (!directVoiceRecordingSupported()) {
	        voiceCommandStatus.textContent = "Na iPhonu přes tuto HTTP adresu prohlížeč nepovolí přímý mikrofon. Klepni do pole Textový pokyn, použij iOS diktování a potom Odeslat Adamovi.";
	        recordVoiceFrontendEvent("record_start_failed", {step: "direct_recording_supported", error: "direct recording not supported"});
	        voiceTranscript.focus();
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
	        voiceStopBtn.classList.remove("hidden");
	        voiceCommandStatus.textContent = "Nahrávám hlasový pokyn. Limit je 30 sekund.";
	        recordVoiceFrontendEvent("record_started", {step: "recording"});
	        voiceStopTimer = window.setTimeout(stopVoiceRecording, 30000);
	      } catch (err) {
	        recordFrontendError(err);
	        recordVoiceFrontendEvent("record_start_failed", {step: "start_recording", error: String(err)});
	        voiceCommandStatus.textContent = `Mikrofon se nepodařilo spustit: ${err}`;
	        resetVoiceRecordingUi();
	      }
	    }

	    function stopVoiceRecording() {
	      recordVoiceFrontendEvent("record_stop_clicked", {step: "stop_recording"});
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
	        recordVoiceFrontendEvent("record_empty", {step: "transcribe", audio_kb: 0});
	        return;
	      }
	      const recordedSeconds = voiceRecordingStartedAt ? Math.max(0, Math.round((Date.now() - voiceRecordingStartedAt) / 1000)) : 0;
	      const audioKb = Math.round(blob.size / 1024);
	      const requestStartedAt = Date.now();
	      voiceCommandStatus.textContent = `Přepisuji hlasový pokyn (${recordedSeconds} s, ${audioKb} kB)...`;
	      recordVoiceFrontendEvent("transcribe_post_start", {step: "transcribe", recorded_seconds: recordedSeconds, audio_kb: audioKb});
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
	        recordVoiceFrontendEvent("transcribe_post_result", {
	          step: "transcribe",
	          ok: Boolean(data.ok),
	          status: data.status || "",
	          error: data.ok ? "" : (data.message || ""),
	          audio_kb: data.audio_kb || audioKb,
	          recorded_seconds: recordedSeconds
	        });
		        if (data.ok) {
		          voiceTranscript.value = data.text || "";
	          startVoiceReplyPolling({autoSpeak: true, expectedUserText: data.text || ""});
	          const totalMs = Date.now() - requestStartedAt;
	          const serverMs = data.duration_ms || 0;
	          const openaiMs = data.timing && data.timing.openai_ms ? data.timing.openai_ms : 0;
	          const timing = `celkem ${Math.round(totalMs / 1000)} s, server ${Math.round(serverMs / 1000)} s, OpenAI ${Math.round(openaiMs / 1000)} s, audio ${data.audio_kb || audioKb} kB`;
	          const savedHint = data.latest_voice_command_path ? ` Uloženo: ${data.latest_voice_command_path}.` : "";
		          voiceCommandStatus.textContent = `${data.message || "Hlasový pokyn byl přepsán a odeslán Adamovi."}${savedHint} (${timing})`;
	        } else {
	          voiceCommandStatus.textContent = data.message || "Přepis hlasu selhal.";
	        }
	      } catch (err) {
	        recordFrontendError(err);
	        recordVoiceFrontendEvent("transcribe_post_failed", {step: "transcribe", error: String(err), audio_kb: audioKb, recorded_seconds: recordedSeconds});
	        voiceCommandStatus.textContent = `Přepis hlasu selhal: ${err}`;
	      }
	    }

	    async function submitVoiceTranscript() {
	      const text = voiceTranscript.value.trim();
	      recordVoiceFrontendEvent("voice_text_submit_clicked", {step: "voice_text", text_chars: text.length});
	      if (!text) {
	        voiceCommandStatus.textContent = "Nejdřív napiš nebo nadiktuj text do pole Textový pokyn.";
	        recordVoiceFrontendEvent("voice_text_submit_blocked", {step: "voice_text", status: "empty_text", text_chars: 0});
	        voiceTranscript.focus();
	        return;
	      }
	      await primeMobileVoiceAudioForCommandGesture("voice_text_submit");
	      voiceTranscriptSendBtn.disabled = true;
	      voiceCommandStatus.textContent = "Odesílám text Adamovi...";
	      recordVoiceFrontendEvent("voice_text_post_start", {step: "voice_text", text_chars: text.length});
	      try {
	        const data = await postJson("/api/speech/voice-text", {text});
	        recordVoiceFrontendEvent("voice_text_post_result", {
	          step: "voice_text",
	          ok: Boolean(data.ok),
	          status: data.status || data.voice_delivery_status || "",
	          text_chars: text.length
	        });
	        if (data.ok) {
	          const savedHint = data.latest_voice_command_path ? ` Uloženo: ${data.latest_voice_command_path}.` : "";
	          voiceCommandStatus.textContent = `${data.message || "Textový pokyn byl odeslán Adamovi."}${savedHint}`;
	          voiceTranscript.value = "";
	          startVoiceReplyPolling({autoSpeak: true, expectedUserText: text});
	          await refresh({silent: true, includeSecondary: false});
	        } else {
	          voiceCommandStatus.textContent = data.message || "Textový hlasový pokyn se nepodařilo uložit.";
	        }
	      } catch (err) {
	        recordFrontendError(err);
	        recordVoiceFrontendEvent("voice_text_post_failed", {step: "voice_text", error: String(err), text_chars: text.length});
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
        const sourceType = item.source_type || "document";
        const isPurchase = sourceType === "purchase";
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
        const sourceLabel = item.source_label || (isPurchase ? "Nákup / záruka" : "Dokument");
        meta.textContent = `${sourceLabel} | ${item.domain || "other"} / ${item.document_type || "document"} | ${item.counterparty || "protistrana nezjištěna"} | ${item.related_asset || "věc nezjištěna"}`;
        const toggle = document.createElement("button");
        toggle.className = "secondary";
        toggle.type = "button";
        toggle.textContent = "Rozbalit";
        const headOpenBtn = document.createElement("button");
        headOpenBtn.className = "primary";
        headOpenBtn.type = "button";
        headOpenBtn.textContent = isPurchase ? "Otevřít PDF" : "Otevřít / číst";
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
        readingStatus.textContent = isPurchase ? "Stav: nákupní evidence" : `Stav čtení: ${item.reading_status_label || "k revizi"}`;
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
        if (!isPurchase) {
          statusSelect.addEventListener("change", () => setDocumentReadingStatus(documentRef, statusSelect.value));
          statusRow.appendChild(statusLabel);
          statusRow.appendChild(statusSelect);
        }
        const snippet = document.createElement("div");
        snippet.className = "search-snippet";
        snippet.textContent = item.snippet || "";
        const actions = document.createElement("div");
        actions.className = "actions";
        const openBtn = document.createElement("button");
        openBtn.className = "primary";
        openBtn.type = "button";
        openBtn.textContent = isPurchase ? "Otevřít nákupní PDF" : "Otevřít / číst PDF";
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
        if (!isPurchase) {
          headOpenBtn.addEventListener("click", () => openDocumentForReading(documentRef, headOpenBtn));
          openBtn.addEventListener("click", () => openDocumentForReading(documentRef, openBtn));
          printBtn.addEventListener("click", () => printDocument(documentRef));
          archiveBtn.addEventListener("click", () => moveDocumentLifecycle(documentRef, "archive"));
          trashBtn.addEventListener("click", () => moveDocumentLifecycle(documentRef, "trash"));
          actions.appendChild(openBtn);
          actions.appendChild(printBtn);
          actions.appendChild(archiveBtn);
          actions.appendChild(trashBtn);
        } else {
          headOpenBtn.addEventListener("click", () => openPurchaseForReading(documentRef, headOpenBtn));
          openBtn.addEventListener("click", () => openPurchaseForReading(documentRef, openBtn));
          actions.appendChild(openBtn);
        }
        summary.appendChild(title);
        summary.appendChild(meta);
        head.appendChild(summary);
        head.appendChild(headActions);
        detail.appendChild(id);
        detail.appendChild(path);
        detail.appendChild(lifecycle);
        detail.appendChild(readingStatus);
        if (!isPurchase) {
          detail.appendChild(statusRow);
        }
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

    function purchaseReaderUrl(purchaseId) {
      return `/purchases/read?purchase_id=${encodeURIComponent(purchaseId || "")}`;
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

    function openDocumentForReading(documentId, button, statusNode = documentSearchStatus) {
      openDocumentReaderWindow(documentId, statusNode, button);
    }

    function openPurchaseReaderWindow(purchaseId, statusNode, button) {
      if (!purchaseId) return;
      const originalText = button ? button.textContent : "";
      if (button) button.disabled = true;
      if (button) button.textContent = "Otevírám...";
      const url = purchaseReaderUrl(purchaseId);
      try {
        const reader = window.open(url, "samanthaPurchaseReader", "width=1180,height=860");
        if (reader) {
          reader.focus();
          if (statusNode) statusNode.textContent = "Nákupní PDF je otevřené ve čtecím okně Cockpitu.";
        } else {
          window.location.href = url;
        }
      } catch (err) {
        recordFrontendError(err);
        if (statusNode) statusNode.textContent = `Chyba otevření nákupního PDF: ${err}`;
      } finally {
        if (button) button.disabled = false;
        if (button) button.textContent = originalText || "Otevřít PDF";
      }
    }

    function openPurchaseForReading(purchaseId, button) {
      openPurchaseReaderWindow(purchaseId, documentSearchStatus, button);
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

    async function setDocumentReadingStatus(documentId, readingStatus, options = {}) {
      if (!documentId) return;
      const statusNode = options.statusNode || documentSearchStatus;
      if (statusNode) statusNode.textContent = "Ukládám stav čtení dokumentu...";
      const result = await postJson("/api/documents/reading-status", {
        document_id: documentId,
        reading_status: readingStatus
      });
      if (statusNode) statusNode.textContent = result.message || "Stav uložen.";
      if (result.ok) {
        await refresh();
        if (documentSearchInput.value.trim().length >= 2) {
          await searchDocuments();
        }
        if (typeof options.afterSave === "function") {
          await options.afterSave();
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

    function resetLibraryExportState(message) {
      currentLibraryExport = null;
      libraryExportPrepareBtn.disabled = !currentLibrarySelectedId;
      libraryExportSendBtn.disabled = true;
      libraryExportStatus.textContent = message || "Export PDF se připraví lokálně a odešle až po potvrzení.";
    }

    function updateLibraryReadStateButtons(item) {
      currentLibrarySelectedItem = item || null;
      const selected = Boolean(currentLibrarySelectedId);
      const state = selected && item ? String(item.read_state || "normal") : "normal";
      libraryToReadBtn.disabled = !selected || state === "to_read";
      libraryDoneBtn.disabled = !selected || state === "done";
      libraryClearReadStateBtn.disabled = !selected || state === "normal";
      currentLibrarySourceUrl = selected && item ? librarySourceUrl(item) : "";
      libraryOpenSourceBtn.disabled = !currentLibrarySourceUrl;
    }

    function librarySourceUrl(item) {
      const url = String((item && (item.canonical_url || item.source_url)) || "").trim();
      if (!url) return "";
      try {
        const parsed = new URL(url);
        return parsed.protocol === "http:" || parsed.protocol === "https:" ? parsed.href : "";
      } catch (_err) {
        return "";
      }
    }

    function openSelectedLibrarySource() {
      if (!currentLibrarySourceUrl) {
        libraryStatus.textContent = "Vybraná položka nemá původní webovou URL.";
        return;
      }
      const opened = window.open(currentLibrarySourceUrl, "_blank", "noopener");
      if (!opened) {
        libraryStatus.textContent = `Prohlížeč zablokoval nové okno. Otevři ručně: ${currentLibrarySourceUrl}`;
        return;
      }
      libraryStatus.textContent = "Otevírám původní článek na webu.";
    }

    async function loadLibraryCategory(category, readState = "") {
      currentLibraryCategory = category || "other";
      currentLibraryReadStateFilter = readState || "";
      currentLibrarySelectedId = "";
      updateLibraryReadStateButtons(null);
      setLibraryActiveTab();
      librarySearchInput.value = "";
      libraryDeleteBtn.disabled = true;
      resetLibraryExportState();
      libraryStatus.textContent = "Načítám knihovnu...";
      libraryReaderTitle.textContent = "Vyber článek";
      libraryReaderMeta.textContent = "Vlevo vyber položku nebo použij fulltextové hledání.";
      libraryReaderText.textContent = "";
      renderLibraryAttachments("", []);
      try {
        const url = `/api/library/list?category=${encodeURIComponent(currentLibraryCategory)}&read_state=${encodeURIComponent(currentLibraryReadStateFilter)}&limit=200`;
        const data = await fetchJson(url);
        currentLibraryItems = data.items || [];
        renderLibraryItems(currentLibraryItems);
        const label = currentLibraryReadStateFilter ? (data.read_state_label || "K přečtení") : (data.category_label || "Kategorie");
        libraryStatus.textContent = currentLibraryItems.length
          ? `${label}: ${currentLibraryItems.length} položek.`
          : `${label} zatím nemá uložené položky.`;
      } catch (err) {
        recordFrontendError(err);
        libraryStatus.textContent = `Chyba načtení knihovny: ${err}`;
      }
    }

    function setLibraryActiveTab() {
      document.querySelectorAll("[data-library-category]").forEach((button) => {
        const category = button.dataset.libraryCategory || "other";
        const readState = button.dataset.libraryReadState || "";
        button.classList.toggle("active", category === currentLibraryCategory && readState === currentLibraryReadStateFilter);
      });
    }

    async function searchLibrary() {
      const query = librarySearchInput.value.trim();
      if (query.length < 2) {
        await loadLibraryCategory(currentLibraryCategory, currentLibraryReadStateFilter);
        return;
      }
      currentLibrarySelectedId = "";
      updateLibraryReadStateButtons(null);
      libraryDeleteBtn.disabled = true;
      resetLibraryExportState();
      libraryStatus.textContent = "Hledám ve fulltextu...";
      libraryReaderTitle.textContent = "Vyber článek";
      libraryReaderMeta.textContent = "Vlevo vyber položku z výsledků hledání.";
      libraryReaderText.textContent = "";
      renderLibraryAttachments("", []);
      try {
        const url = `/api/library/search?category=${encodeURIComponent(currentLibraryCategory)}&read_state=${encodeURIComponent(currentLibraryReadStateFilter)}&q=${encodeURIComponent(query)}&limit=80`;
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
        const savedTitle = item.one_line_title || item.title || "uložený článek";
        const savedMessage = `${data.message || "Článek uložen."} Otevřeno: ${savedTitle}`;
        libraryArchiveStatus.textContent = savedMessage;
        libraryArchiveUrlInput.value = "";
        libraryArchiveTagsInput.value = "";
        currentLibraryCategory = item.category || category;
        await loadLibraryCategory(currentLibraryCategory, "");
        if (item.id) {
          await loadLibraryItem(item.id);
          document.querySelectorAll(".library-item").forEach((node) => {
            if (node.dataset.articleId === item.id) {
              node.scrollIntoView({block: "nearest"});
            }
          });
        }
        libraryStatus.textContent = savedMessage;
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

    async function deleteSelectedLibraryItem() {
      const articleId = currentLibrarySelectedId;
      if (!articleId) {
        libraryStatus.textContent = "Nejdřív vyber položku v knihovně.";
        return;
      }
      const title = libraryReaderTitle.textContent || articleId;
      const confirmed = window.confirm(`Vyřadit z knihovny: ${title}?\n\nPoložka zmizí ze seznamu a přesune se do soukromého koše.`);
      if (!confirmed) {
        return;
      }
      libraryDeleteBtn.disabled = true;
      libraryStatus.textContent = "Vyřazuji položku z knihovny...";
      try {
        const data = await postJson("/api/library/delete", {
          article_id: articleId,
          user_confirmed: true,
          confirmation_text: "Potvrzuji vyřazení z knihovny"
        });
        if (!data.ok) {
          libraryStatus.textContent = data.message || "Položku se nepodařilo vyřadit.";
          libraryDeleteBtn.disabled = false;
          libraryExportPrepareBtn.disabled = false;
          return;
        }
        currentLibrarySelectedId = "";
        resetLibraryExportState(data.message || "Položka byla vyřazena.");
        libraryReaderTitle.textContent = "Vyber článek";
        libraryReaderMeta.textContent = data.message || "Položka byla vyřazena.";
        libraryReaderText.textContent = "";
        updateLibraryReadStateButtons(null);
        renderLibraryAttachments("", []);
        if (librarySearchInput.value.trim().length >= 2) {
          await searchLibrary();
        } else {
          await loadLibraryCategory(currentLibraryCategory, currentLibraryReadStateFilter);
        }
        libraryStatus.textContent = data.message || "Položka byla vyřazena z knihovny.";
      } catch (err) {
        recordFrontendError(err);
        libraryStatus.textContent = `Chyba vyřazení položky: ${err}`;
        libraryDeleteBtn.disabled = false;
        libraryExportPrepareBtn.disabled = false;
      }
    }

    async function prepareSelectedLibraryPdfExport() {
      const articleId = currentLibrarySelectedId;
      if (!articleId) {
        libraryExportStatus.textContent = "Nejdřív vyber položku v knihovně.";
        return;
      }
      libraryExportPrepareBtn.disabled = true;
      libraryExportSendBtn.disabled = true;
      libraryExportStatus.textContent = "Připravuji PDF a e-mailový draft lokálně...";
      try {
        const data = await postJson("/api/library/export/prepare", {article_id: articleId});
        if (!data.ok) {
          libraryExportStatus.textContent = data.message || "PDF export se nepodařilo připravit.";
          libraryExportPrepareBtn.disabled = false;
          return;
        }
        currentLibraryExport = data.export || null;
        const sizeKb = currentLibraryExport && currentLibraryExport.size_bytes
          ? `${Math.max(1, Math.round(Number(currentLibraryExport.size_bytes) / 1024))} kB`
          : "neznámá velikost";
        const confirmation = currentLibraryExport && currentLibraryExport.confirmation_text
          ? currentLibraryExport.confirmation_text
          : "";
        libraryExportStatus.textContent = `${data.message || "Export připraven."} PDF: ${sizeKb}. Potvrzení pro odeslání: ${confirmation}`;
        libraryExportSendBtn.disabled = !currentLibraryExport || !currentLibraryExport.export_id;
      } catch (err) {
        recordFrontendError(err);
        libraryExportStatus.textContent = `Chyba přípravy PDF exportu: ${err}`;
      } finally {
        libraryExportPrepareBtn.disabled = false;
      }
    }

    async function sendSelectedLibraryPdfExport() {
      if (!currentLibraryExport || !currentLibraryExport.export_id) {
        libraryExportStatus.textContent = "Nejdřív připrav PDF export.";
        return;
      }
      const confirmation = currentLibraryExport.confirmation_text || "";
      const typed = window.prompt(`Pro odeslání PDF exportu opiš přesně:\n\n${confirmation}`, "");
      if (typed === null) {
        return;
      }
      libraryExportSendBtn.disabled = true;
      libraryExportPrepareBtn.disabled = true;
      libraryExportStatus.textContent = "Odesílám PDF export e-mailem...";
      try {
        const data = await postJson("/api/library/export/send", {
          export_id: currentLibraryExport.export_id,
          user_confirmed: true,
          confirmation_text: typed
        });
        if (!data.ok) {
          libraryExportStatus.textContent = data.message || "PDF export se nepodařilo odeslat.";
          libraryExportSendBtn.disabled = false;
          return;
        }
        currentLibraryExport = null;
        libraryExportStatus.textContent = data.message || "PDF export byl odeslán.";
      } catch (err) {
        recordFrontendError(err);
        libraryExportStatus.textContent = `Chyba odeslání PDF exportu: ${err}`;
        libraryExportSendBtn.disabled = false;
      } finally {
        libraryExportPrepareBtn.disabled = !currentLibrarySelectedId;
      }
    }

    async function setSelectedLibraryReadState(readState) {
      const articleId = currentLibrarySelectedId;
      if (!articleId) {
        libraryStatus.textContent = "Nejdřív vyber položku v knihovně.";
        return;
      }
      let note = "";
      if (readState === "to_read") {
        note = window.prompt("Volitelná poznámka k přečtení:", currentLibrarySelectedItem && currentLibrarySelectedItem.read_note ? currentLibrarySelectedItem.read_note : "") || "";
      }
      libraryToReadBtn.disabled = true;
      libraryDoneBtn.disabled = true;
      libraryClearReadStateBtn.disabled = true;
      libraryStatus.textContent = "Ukládám stav článku...";
      try {
        const data = await postJson("/api/library/read-state", {
          article_id: articleId,
          read_state: readState,
          note
        });
        if (!data.ok) {
          libraryStatus.textContent = data.message || "Stav článku se nepodařilo uložit.";
          updateLibraryReadStateButtons(currentLibrarySelectedItem);
          return;
        }
        const item = data.item || {};
        libraryStatus.textContent = data.message || "Stav článku uložen.";
        libraryReaderMeta.textContent = libraryItemMeta(item);
        updateLibraryReadStateButtons(item);
        const targetCategory = currentLibraryReadStateFilter ? "all" : (item.category || currentLibraryCategory);
        const targetReadState = currentLibraryReadStateFilter || "";
        await loadLibraryCategory(targetCategory, targetReadState);
        if (item.id) {
          await loadLibraryItem(item.id);
        }
      } catch (err) {
        recordFrontendError(err);
        libraryStatus.textContent = `Chyba uložení stavu článku: ${err}`;
        updateLibraryReadStateButtons(currentLibrarySelectedItem);
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
        row.classList.toggle("to-read", item.read_state === "to_read");
        const title = document.createElement("div");
        title.className = "library-title";
        title.textContent = item.one_line_title || item.title || "Bez názvu";
        const meta = document.createElement("div");
        meta.className = "library-meta";
        meta.textContent = libraryItemMeta(item);
        row.appendChild(title);
        if (item.read_state === "to_read") {
          const badge = document.createElement("div");
          badge.className = "library-read-badge";
          badge.textContent = item.read_state_label || "k přečtení";
          row.appendChild(badge);
        }
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
      if (item.read_state && item.read_state !== "normal") {
        parts.push(item.read_state_label || item.read_state);
      }
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
      if (item.read_note) parts.push(item.read_note);
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
      libraryDeleteBtn.disabled = false;
      resetLibraryExportState();
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
          libraryDeleteBtn.disabled = true;
          currentLibrarySelectedId = "";
          updateLibraryReadStateButtons(null);
          resetLibraryExportState(data.message || "Článek nelze načíst.");
          return;
        }
        const item = data.item || {};
        libraryReaderTitle.textContent = item.one_line_title || item.title || "Bez názvu";
        libraryReaderMeta.textContent = libraryItemMeta(item);
        libraryReaderText.textContent = data.text || "";
        updateLibraryReadStateButtons(item);
        renderLibraryAttachments(item.id || articleId, item.attachments || []);
      } catch (err) {
        recordFrontendError(err);
        libraryReaderTitle.textContent = "Chyba čtení";
        libraryReaderMeta.textContent = String(err);
        renderLibraryAttachments("", []);
        libraryDeleteBtn.disabled = true;
        currentLibrarySelectedId = "";
        updateLibraryReadStateButtons(null);
        resetLibraryExportState(`Chyba čtení: ${err}`);
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
	      const autosaveRuntime = autosave.runtime || {};
	      const git = data.git || {};
	      const project = data.active_project || {};
	      recoveryStatus.textContent = `${data.message || "Recovery centrum načteno."} ${data.safety_note || ""}`;
	      recoveryAutosave.textContent = autosave.ok
	        ? `Poslední: ${autosave.latest_file || ""} | ${autosave.latest_modified_at || ""} | ${formatAge(autosave.latest_age_seconds)} | souborů: ${autosave.file_count || 0} | watchery: ${Number(autosaveRuntime.watcher_count || 0)} (očekáván 1)${autosaveRuntime.warning ? ` | ${autosaveRuntime.warning}` : ""}`
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
        const data = await fetchJson("/api/reminders");
        renderReminders(data);
      } catch (err) {
        recordFrontendError(err);
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
        remindersStatus.textContent = result.message || "Hotovo.";
        const fresh = await fetchJson("/api/reminders");
        renderReminders(fresh);
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
        urgentRemindersStatus.textContent = result.message || "Hotovo.";
        const fresh = await fetchJson("/api/urgent-reminders/status");
        renderUrgentReminders(fresh);
        renderUrgentReminderAlert(fresh);
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

    async function openFullAdamForJanicka() {
      janickaFullAdamBtn.disabled = true;
      janickaFullAdamStatus.textContent = "Otevírám plného Adama v Terminalu...";
      try {
        const data = await postJson("/api/janicka/full-adam/open", {});
        const steps = Array.isArray(data.manual_steps) ? data.manual_steps.filter(Boolean) : [];
        const manual = data.manual_command ? `\\n\\nRuční příkaz: ${data.manual_command}` : "";
        const stepsText = steps.length ? `\\n\\nKdyž se okno neotevře:\\n- ${steps.join("\\n- ")}` : "";
        janickaFullAdamStatus.textContent = `${data.message || "Hotovo."}${manual}${stepsText}`;
      } catch (err) {
        recordFrontendError(err);
        janickaFullAdamStatus.textContent =
          `Plného Adama se nepodařilo otevřít: ${err}\n\n` +
          "Ruční postup: otevři aplikaci Terminal, napiš cd /Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent, stiskni Enter a potom napiš codex --no-alt-screen.";
      } finally {
        janickaFullAdamBtn.disabled = false;
      }
    }

    let janickaChatHistory = [];

    function openJanickaChatModal() {
      janickaReturnBtn.classList.add("hidden");
      janickaChatModal.classList.remove("hidden");
      if (!janickaChatHistory.length) {
        renderJanickaChat();
      }
      refreshJanickaAdamStatus();
      refreshJanickaLightStatus();
      window.setTimeout(() => janickaChatInput.focus(), 0);
    }

    function closeJanickaChatModal() {
      janickaChatModal.classList.add("hidden");
      openJanickaModal();
    }

    function openJanickaFamilyModal() {
      closeJanickaModal();
      janickaFamilyStatus.textContent = "Vyber, co chceš otevřít.";
      janickaFamilyModal.classList.remove("hidden");
    }

    function closeJanickaFamilyModal() {
      janickaFamilyModal.classList.add("hidden");
      openJanickaModal();
    }

    function openJanickaFamilyOrganizer() {
      janickaFamilyStatus.textContent = "Otevírám rodinný výběr videí a fotek...";
      openCatalogAppById("family-video-organizer");
    }

    function openJanickaFamilyProjects() {
      janickaFamilyModal.classList.add("hidden");
      armJanickaModalReturn("projects");
      openProjectsModal();
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
      janickaChatStatus.textContent = "Předávám dotaz light Samanthě do Codexu...";
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
            refreshJanickaLightStatus();
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
      janickaChatStatus.textContent = "Odpověď se zatím nevrátila do okna. Adam může ještě odpovídat ve své spravované relaci.";
    }

    async function refreshJanickaAdamStatus() {
      try {
        const data = await postJson("/api/adam/status", {});
        const running = Boolean(data.running);
        const managedTtys = Array.isArray(data.managed_codex_ttys) ? data.managed_codex_ttys.filter(Boolean) : [];
        const managedTarget = managedTtys.length ? ` Relace: ${managedTtys.join(", ")}.` : "";
        const marker = data.marked_tty ? ` Mílův hlasový bridge: ${data.marked_tty}.` : "";
        const pending = Number(data.pending_count || 0);
        const ready = running && managedTtys.length > 0;
        const stateText = ready
          ? `Starý Adam fallback běží.${managedTarget}${marker}`
          : `Starý Adam fallback neběží nebo není připravený.${marker}`;
        janickaAdamStatus.textContent = `${stateText}${pending ? ` Starých nevyřízených dotazů: ${pending}.` : ""}`;
        janickaAdamStatus.classList.toggle("ok", ready);
        janickaAdamStatus.classList.toggle("warn", !ready);
        janickaAdamStartBtn.disabled = running;
      } catch (err) {
        recordFrontendError(err);
        janickaAdamStatus.textContent = `Fallback status se nepodařilo načíst: ${err}`;
        janickaAdamStatus.classList.add("warn");
      }
    }

    async function startJanickaAdam() {
      janickaAdamStatus.textContent = "Spouštím fallback...";
      try {
        const data = await postJson("/api/adam/start", {});
        janickaAdamStatus.textContent = data.message || "Fallback se spouští.";
        await refreshJanickaAdamStatus();
      } catch (err) {
        recordFrontendError(err);
        janickaAdamStatus.textContent = `Fallback se nepodařilo spustit: ${err}`;
      }
    }

    async function restartJanickaAdam() {
      if (!window.confirm("Restartovat starý Adam fallback? Rozpracovaná odpověď ve fallback relaci se může přerušit.")) return;
      janickaAdamStatus.textContent = "Restartuji fallback...";
      try {
        const data = await postJson("/api/adam/restart", {confirmed: true});
        janickaAdamStatus.textContent = data.message || "Fallback se restartuje.";
        await refreshJanickaAdamStatus();
      } catch (err) {
        recordFrontendError(err);
        janickaAdamStatus.textContent = `Fallback se nepodařilo restartovat: ${err}`;
      }
    }

    async function stopJanickaAdam() {
      if (!window.confirm("Zastavit starý Adam fallback? Běžně není potřeba na něj sahat.")) return;
      janickaAdamStatus.textContent = "Zastavuji fallback...";
      try {
        const data = await postJson("/api/adam/stop", {confirmed: true});
        janickaAdamStatus.textContent = data.message || "Fallback byl zastaven.";
        await refreshJanickaAdamStatus();
      } catch (err) {
        recordFrontendError(err);
        janickaAdamStatus.textContent = `Fallback se nepodařilo zastavit: ${err}`;
      }
    }

    async function refreshJanickaLightStatus() {
      try {
        const data = await postJson("/api/janicka/light/status", {});
        const running = Boolean(data.running);
        const managedTtys = Array.isArray(data.managed_codex_ttys) ? data.managed_codex_ttys.filter(Boolean) : [];
        const orphanedTtys = Array.isArray(data.orphaned_janicka_ttys) ? data.orphaned_janicka_ttys.filter(Boolean) : [];
        const managedTarget = managedTtys.length ? ` Relace: ${managedTtys.join(", ")}.` : "";
        const orphanedText = orphanedTtys.length ? ` Staré relace mimo správu: ${orphanedTtys.join(", ")}.` : "";
        const ready = running && managedTtys.length > 0;
        janickaLightStatus.textContent = ready
          ? `Janička chat běží.${managedTarget}${orphanedText}`
          : `Janička chat není připravený.${managedTarget}${orphanedText}`;
        janickaLightStatus.classList.toggle("ok", ready && !orphanedTtys.length);
        janickaLightStatus.classList.toggle("warn", !ready || orphanedTtys.length > 0);
        janickaLightStartBtn.disabled = running;
        janickaLightStopBtn.disabled = !running;
        janickaLightCleanupOrphansBtn.classList.toggle("hidden", orphanedTtys.length === 0);
        janickaLightCleanupOrphansBtn.disabled = orphanedTtys.length === 0;
      } catch (err) {
        recordFrontendError(err);
        janickaLightStatus.textContent = `Janička chat status se nepodařilo načíst: ${err}`;
        janickaLightStatus.classList.add("warn");
        janickaLightStopBtn.disabled = true;
        janickaLightCleanupOrphansBtn.classList.add("hidden");
        janickaLightCleanupOrphansBtn.disabled = true;
      }
    }

    async function startJanickaLight() {
      janickaLightStatus.textContent = "Spouštím Janička chat...";
      try {
        const data = await postJson("/api/janicka/light/start", {});
        janickaLightStatus.textContent = data.message || "Janička chat se spouští.";
        await refreshJanickaLightStatus();
      } catch (err) {
        recordFrontendError(err);
        janickaLightStatus.textContent = `Janička chat se nepodařilo spustit: ${err}`;
      }
    }

    async function stopJanickaLight() {
      if (!window.confirm("Zastavit Janička chat?")) return;
      janickaLightStatus.textContent = "Zastavuji Janička chat...";
      try {
        const data = await postJson("/api/janicka/light/stop", {confirmed: true});
        janickaLightStatus.textContent = data.message || "Janička chat byl zastaven.";
        await refreshJanickaLightStatus();
      } catch (err) {
        recordFrontendError(err);
        janickaLightStatus.textContent = `Janička chat se nepodařilo zastavit: ${err}`;
      }
    }

    async function cleanupJanickaLightOrphans() {
      janickaLightCleanupOrphansBtn.disabled = true;
      try {
        const preview = await postJson("/api/janicka/light/cleanup-orphans", {confirmed: false});
        const staleTtys = Array.isArray(preview.stale_ttys) ? preview.stale_ttys.join(", ") : "";
        if (preview.status === "no_orphaned_janicka_sessions") {
          janickaLightStatus.textContent = preview.message || "Žádné staré Janička relace k úklidu.";
          await refreshJanickaLightStatus();
          return;
        }
        if (preview.status !== "confirmation_required") {
          janickaLightStatus.textContent = preview.message || "Staré Janička relace nejde bezpečně určit.";
          await refreshJanickaLightStatus();
          return;
        }
        const ok = window.confirm(`Ukončit staré Janička relace mimo správu ${staleTtys}? Aktuální Janička i hlavní Adam zůstanou běžet.`);
        if (!ok) {
          janickaLightStatus.textContent = "Úklid starých Janička relací zrušen.";
          await refreshJanickaLightStatus();
          return;
        }
        const data = await postJson("/api/janicka/light/cleanup-orphans", {confirmed: true});
        janickaLightStatus.textContent = data.message || "Staré Janička relace byly uklizeny.";
        await refreshJanickaLightStatus();
      } catch (err) {
        recordFrontendError(err);
        janickaLightStatus.textContent = `Úklid starých Janička relací selhal: ${err}`;
      } finally {
        janickaLightCleanupOrphansBtn.disabled = false;
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

    async function openDesktopApp(app) {
      if (!app || !app.id) return;
      showMessage(`Spouštím ${app.title || "desktopovou aplikaci"}...`);
      try {
        const data = await postJson("/api/desktop-apps/open", {app_id: app.id});
        showMessage(data.message || (data.ok ? "Aplikace se spouští." : "Aplikaci se nepodařilo spustit."));
      } catch (err) {
        recordFrontendError(err);
        showMessage(`Chyba spuštění aplikace: ${err}`);
      }
    }

    function openWebApp(app) {
      if (!app) return;
      if (app.launch_type === "desktop") {
        openDesktopApp(app);
        return;
      }
      if (!app.url) return;
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
    janickaFamilyBtn.addEventListener("click", openJanickaFamilyModal);
    janickaAskAdamBtn.addEventListener("click", focusAdamForJanicka);
    janickaFullAdamBtn.addEventListener("click", openFullAdamForJanicka);
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
    janickaFamilyCloseBtn.addEventListener("click", closeJanickaFamilyModal);
    janickaFamilyOrganizerBtn.addEventListener("click", openJanickaFamilyOrganizer);
    janickaFamilyProjectsBtn.addEventListener("click", openJanickaFamilyProjects);
    janickaAdamStartBtn.addEventListener("click", startJanickaAdam);
    janickaAdamRestartBtn.addEventListener("click", restartJanickaAdam);
    janickaAdamStopBtn.addEventListener("click", stopJanickaAdam);
    janickaLightStartBtn.addEventListener("click", startJanickaLight);
    janickaLightStopBtn.addEventListener("click", stopJanickaLight);
    janickaLightCleanupOrphansBtn.addEventListener("click", cleanupJanickaLightOrphans);
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
    dashboardProjectAuditBtn.addEventListener("click", openProjectAuditModal);
		    dashboardQuickNotesBtn.addEventListener("click", openQuickNotesModal);
    dashboardUrgentRemindersBtn.addEventListener("click", openUrgentRemindersModal);
    urgentReminderAlertBtn.addEventListener("click", openUrgentRemindersModal);
		    dashboardRecoveryBtn.addEventListener("click", openRecoveryModal);
    dashboardAutosaveCleanupBtn.addEventListener("click", () => {
      servicePanel.open = true;
      previewAutosaveCleanup(dashboardAutosaveCleanupBtn);
      autosaveCleanupStatus.scrollIntoView({behavior: "smooth", block: "center"});
    });
    dashboardDiagnosticsBtn.addEventListener("click", openDiagnosticsModal);
    dashboardOverall.addEventListener("click", openDiagnosticsModal);
    dashboardOverall.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openDiagnosticsModal();
      }
    });
    dashboardRestartBtn.addEventListener("click", restartCockpit);
    autosaveCleanupPreviewBtn.addEventListener("click", () => previewAutosaveCleanup(autosaveCleanupPreviewBtn));
    autosaveCleanupApplyBtn.addEventListener("click", applyAutosaveCleanup);
    devRunnerPanel.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-dev-runner]");
      if (!button) return;
      runDevRunnerAction(button.dataset.devRunner || "", button);
    });
    dashboardSpeakBtn.addEventListener("click", speakDashboardStatus);
    dashboardSpeakSelectionBtn.addEventListener("pointerdown", captureSelectedSpeechText);
    dashboardSpeakSelectionBtn.addEventListener("mousedown", captureSelectedSpeechText);
    dashboardSpeakSelectionBtn.addEventListener("click", speakSelectedText);
    voiceModeToggleBtn.addEventListener("click", toggleVoiceMode);
    voiceModeStartBtn.addEventListener("click", startVoiceModeWatcher);
    voiceModeStopBtn.addEventListener("click", stopVoiceModeWatcher);
    voiceRecordBtn.addEventListener("click", startVoiceRecording);
    voiceStopBtn.addEventListener("click", stopVoiceRecording);
    voiceAudioUnlockBtn.addEventListener("click", openVoiceAudioChannel);
    voiceTranscriptSendBtn.addEventListener("click", submitVoiceTranscript);
    voiceLastResponseSpeakBtn.addEventListener("click", speakLastAdamResponse);
    codexApprovalSendConfirmationBtn.addEventListener("click", sendCodexApprovalConfirmation);
    codexApprovalCopyConfirmationBtn.addEventListener("click", copyCodexApprovalConfirmation);
    codexApprovalClearBtn.addEventListener("click", clearCodexApprovalCard);
    voiceApprovalApproveBtn.addEventListener("click", () => submitVoiceApproval("approved"));
    voiceApprovalRejectBtn.addEventListener("click", () => submitVoiceApproval("rejected"));
    voiceBridgeSwitcherActions.addEventListener("click", (event) => {
      const cleanupButton = event.target.closest("button[data-voice-bridge-cleanup]");
      if (cleanupButton) {
        terminateStaleVoiceBridgeSessions(cleanupButton);
        return;
      }
      const button = event.target.closest("button[data-voice-bridge-tty]");
      if (!button) return;
      setVoiceBridgeMarker(button.dataset.voiceBridgeTty || "", button);
    });
    safeReadonlyCard.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-safe-readonly]");
      if (!button) return;
      runSafeReadonlyCapability(button.dataset.safeReadonly || "", button);
    });
    updateVoiceRecordingAvailability();
    updateVoiceAudioUnlockUi(false);
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
    projectAuditCloseBtn.addEventListener("click", closeProjectAuditModal);
    projectAuditSaveBtn.addEventListener("click", saveProjectAuditReport);
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
    janickaFamilyModal.addEventListener("click", (event) => {
      if (event.target === janickaFamilyModal) {
        closeJanickaFamilyModal();
      }
    });
    quantitativeModal.addEventListener("click", (event) => {
      if (event.target === quantitativeModal) {
        closeQuantitativeModal();
      }
    });
    projectAuditModal.addEventListener("click", (event) => {
      if (event.target === projectAuditModal) {
        closeProjectAuditModal();
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
    libraryOpenSourceBtn.addEventListener("click", openSelectedLibrarySource);
    libraryExportPrepareBtn.addEventListener("click", prepareSelectedLibraryPdfExport);
    libraryExportSendBtn.addEventListener("click", sendSelectedLibraryPdfExport);
    libraryToReadBtn.addEventListener("click", () => setSelectedLibraryReadState("to_read"));
    libraryDoneBtn.addEventListener("click", () => setSelectedLibraryReadState("done"));
    libraryClearReadStateBtn.addEventListener("click", () => setSelectedLibraryReadState("normal"));
    libraryDeleteBtn.addEventListener("click", deleteSelectedLibraryItem);
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
      button.addEventListener("click", () => loadLibraryCategory(button.dataset.libraryCategory || "other", button.dataset.libraryReadState || ""));
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
      } else if (event.key === "Escape" && !projectAuditModal.classList.contains("hidden")) {
        closeProjectAuditModal();
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
		      } else if (event.key === "Escape" && !janickaFamilyModal.classList.contains("hidden")) {
		        closeJanickaFamilyModal();
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
	    window.setInterval(() => refresh({silent: true, includeSecondary: false}), FULL_STATUS_MONITOR_MS);
	    window.setInterval(() => {
	      if (!document.hidden) {
	        refreshLiveStatus();
	      }
	    }, VOICE_STATUS_MONITOR_MS);
      window.setInterval(refreshUrgentRemindersSummary, URGENT_REMINDERS_MONITOR_MS);
      window.setInterval(runEmailIntakeMonitor, INTAKE_EMAIL_MONITOR_MS);
      window.addEventListener("focus", () => {
        refreshLiveStatus();
        refreshMainStatusOnReturn();
      });
      window.addEventListener("pageshow", () => {
        refreshLiveStatus();
        refreshMainStatusOnReturn();
      });
      document.addEventListener("visibilitychange", () => {
        if (!document.hidden) {
          refreshLiveStatus();
          refreshMainStatusOnReturn();
        }
      });
	    refresh();
      window.setTimeout(() => refreshVoiceLatestResponse({autoSpeak: false}), 2000);
      window.setTimeout(refreshUrgentRemindersSummary, 3000);
      window.setTimeout(runEmailIntakeMonitor, 5000);
	  </script>
</body>
</html>
"""


def run_cockpit_server(host: str = "127.0.0.1", port: int = COCKPIT_PORT) -> None:
    CockpitServer(host=host, port=port).serve()
