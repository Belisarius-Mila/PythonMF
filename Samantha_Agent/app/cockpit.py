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
import subprocess
import tempfile
import threading
import time
import urllib.error
from collections.abc import Callable, Collection
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

from app.cockpit_frontend import (
    COCKPIT_HTML,
    EMAIL_ARCHIVE_HTML,
    EMAIL_PROCESSING_HTML,
)
from app.article_archive import (
    ATTACHMENT_CONFIRMATION_PHRASE,
    ATTACHMENT_REMOVE_CONFIRMATION_PHRASE,
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
    preview_article_source_reextract,
    search_articles,
    send_article_pdf_export,
    set_article_read_state,
    update_article,
    update_article_attachment,
    remove_article_attachment,
)
from app.autosave_service import (
    SESSION_AUTOSAVE_DIR,
    autosave_runtime_dict as cockpit_autosave_runtime_dict,
    latest_autosave_metadata,
    session_autosave_cleanup_action,
)
from app.codex_appserver import AppServerError
from app.command_cheatsheet import load_command_cheatsheet
from app.communication.human_adam_service import (
    human_adam_checkpoint_action,
    human_adam_connect_action,
    human_adam_send_action,
    human_adam_status_action,
    human_adam_thread_rotation_action,
    human_adam_thread_rotation_status_action,
    human_adam_tvbcp_action,
    human_adam_work_review_action,
)
from app.communication.human_adam_profiles import (
    HUMAN_ADAM,
    HumanAdamProfileManager,
    human_adam_deferred_integration_action,
    human_adam_development_semaphore_action,
    human_adam_development_semaphore_status_action,
    human_adam_owned_wip_recovery_action,
    human_adam_project_continuity_action,
    human_adam_profile_switch_action,
)
from app.communication.session_hub import SessionHubError
from app.communication.simple_main_deploy import (
    PENDING_RESTART,
    SIMPLE_MAIN_DEPLOYMENT_CONFIRMATION,
    SimpleMainDeploymentError,
    load_simple_main_deployment_receipt,
)
from app.communication.human_adam_ui import HUMAN_ADAM_HTML
from app.communication.janicka_r2_chat import (
    R2_ADAM_CHAT_HTML,
    R2_ADAM_DOCUMENT_READER_HTML,
    JanickaR2ChatAdapter,
    janicka_r2_chat_connect_action,
    janicka_r2_chat_document_action,
    janicka_r2_chat_documents_action,
    janicka_r2_chat_send_action,
    janicka_r2_chat_status_action,
)
from app.communication.janicka_r2_cockpit import (
    JANICKA_R2_DOCUMENTS_HTML,
    JanickaR2CockpitAdapter,
    janicka_r2_document_compile_action,
    janicka_r2_document_search_action,
)
from app.backup.activity_state import backup_activity_status
from app.family_calendar import (
    DEFAULT_FAMILY_CALENDAR_PREFILL,
    DEFAULT_FAMILY_CALENDAR_PATH,
    build_due_notification_previews,
    ensure_family_calendar_prefill,
    family_calendar_status,
    load_family_people,
    save_family_person,
)
from app.documents.case_service import (
    DocumentCaseDependencies,
    document_case_detail_status as build_document_case_detail_status,
    document_case_group_type_label,
    document_case_health_status as build_document_case_health_status,
    document_case_reference,
    document_case_summary,
    document_cases_status as build_document_cases_status,
    document_domain_label,
    document_type_label,
)
from app.documents.consistency_audit import format_document_consistency_audit, run_document_consistency_audit, save_audit_decision
from app.documents.due_date_service import (
    build_document_due_candidates,
    build_email_archive_due_candidates,
    document_due_candidates_status as build_document_due_candidates_status,
    document_payment_options,
)
from app.documents.intake_service import document_intake_status as build_document_intake_status
from app.documents.scandocu import DEFAULT_DOWNLOADS_DIR, reviewed_document_ids, scan_downloads_for_pdfs
from app.documents.review_service import (
    DOCUMENT_REVIEW_FIELD_LABELS,
    DOCUMENT_REVIEW_REASON_LABELS,
    document_classification_metadata_suggestion,
    document_classification_missing_fields,
    document_classification_status as build_document_classification_status,
    document_metadata_suggestion_confidence,
    document_metadata_value_label,
    document_review_report_status as build_document_review_report_status,
    document_work_status as build_document_work_status,
    safe_manual_metadata_slug,
    stored_documents_review_status as build_stored_documents_review_status,
)
from app.documents.search_service import search_document_index
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
from app.email.archive_browser import (
    email_archive_reference,
    email_archive_detail_status,
    email_archive_list_status,
    email_archive_uid,
    resolve_email_archive_dir,
    resolve_email_archive_embedded_attachment,
    resolve_email_archive_file,
    resolve_email_archive_incoming_file,
    vault_email_archive_attachments,
)
from app.email.archive_models import EmailArchiveSource
from app.email.archive_service import DEFAULT_EMAIL_ARCHIVE_DIR, save_email_archive
from app.email.config import EmailConfigError
from app.email.icloud_provider import EmailProviderError, ICloudReadOnlyEmailProvider
from app.email.models import EmailAttachmentMeta, EmailHeader, EmailMessage
from app.email.redaction import redact_email_addresses
from app.email.seznam_provider import SeznamEmailProviderError, SeznamReadOnlyEmailProvider
from app.email.work_repository import (
    pending_email_purge_items,
    read_email_work_decisions,
    save_email_work_decision as repository_save_email_work_decision,
)
from app.email.work_models import (
    classify_email_processing_category,
    email_processing_batch_groups,
    email_processing_is_inbound_work_folder,
    email_processing_item_id,
    email_processing_item_lookup_keys,
    email_processing_legacy_item_id,
    email_processing_stable_key,
    normalize_email_work_item,
)
from app.file_persistence import FilePersistenceError, append_jsonl_locked
from app.codex_approval_state import (
    clear_codex_approval_request,
    load_codex_approval_request,
)
from app.cockpit_code_stamp import cockpit_code_stamp
from app.cockpit_status_service import (
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
JANICKA_R2_COCKPIT = JanickaR2CockpitAdapter.bind(
    canonical_private_root=HUMAN_ADAM.profiles[
        HUMAN_ADAM.default_profile_id
    ]["service"].workspace.canonical_private_root,
)
JANICKA_R2_CHAT = JanickaR2ChatAdapter.bind(
    base_service=HUMAN_ADAM.profiles[
        HUMAN_ADAM.default_profile_id
    ]["service"],
)
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
        "id": "cockpit",
        "title": "Samantha Cockpit",
        "description": "Řídicí panel pro dokumenty, ScanDocu, zálohy a praktické rutiny Samanthy.",
        "url": COCKPIT_URL,
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


DOCUMENT_METADATA_UPDATE_FIELDS: tuple[str, ...] = (
    "domain",
    "document_type",
    "counterparty",
    "related_asset",
    "case_id",
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


def library_update_article_action(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return update_article(
            article_id=str(payload.get("article_id", "")),
            title=str(payload.get("title", "")),
            text=str(payload.get("text", "")),
            category=str(payload.get("category", "other")),
            tags=parse_tag_payload(payload.get("tags", [])),
            source_label=str(payload.get("source_label", "")),
            source_note=str(payload.get("source_note", "")),
        )
    except ValueError as exc:
        return {"ok": False, "message": str(exc), "error": "invalid_article_update"}
    except OSError as exc:
        return {"ok": False, "message": f"Úpravy článku se nepodařilo uložit: {exc}", "error": "archive_failed"}


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
    category = str(payload.get("category", "recipes") or "recipes").strip().casefold()
    is_recipe = category in {"recipe", "recipes", "recept", "recepty"}
    automatic_tags = ["ma-obrazek"]
    if is_recipe:
        automatic_tags.extend(["rodinny-recept", "rucne-psany", "scan", "prepis-overit"])
    for tag in automatic_tags:
        if tag not in tags:
            tags.append(tag)
    try:
        return attach_article_image(
            article_id=str(payload.get("article_id", "")),
            image_bytes=image_bytes,
            filename=str(payload.get("filename", "")),
            label=str(payload.get("label", "")) or ("Ručně psaný recept" if is_recipe else "Doprovodná fotografie"),
            role=str(payload.get("role", "")) or ("handwritten_recipe_scan" if is_recipe else "supporting_image"),
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


def library_update_attachment_action(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return update_article_attachment(
            article_id=str(payload.get("article_id", "")),
            attachment_id=str(payload.get("attachment_id", "")),
            label=str(payload.get("label", "")),
            note=str(payload.get("note", "")),
        )
    except ValueError as exc:
        return {"ok": False, "message": str(exc), "error": "invalid_attachment_update"}
    except OSError as exc:
        return {"ok": False, "message": f"Popisek přílohy se nepodařilo uložit: {exc}", "error": "archive_failed"}


def library_remove_attachment_action(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return remove_article_attachment(
            article_id=str(payload.get("article_id", "")),
            attachment_id=str(payload.get("attachment_id", "")),
            user_confirmed=bool(payload.get("user_confirmed")),
            confirmation_text=str(payload.get("confirmation_text", "")),
        )
    except ValueError as exc:
        return {"ok": False, "message": str(exc), "error": "invalid_attachment_remove"}
    except OSError as exc:
        return {"ok": False, "message": f"Přílohu se nepodařilo odebrat: {exc}", "error": "archive_failed"}


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


def library_article_reextract_preview_action(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return preview_article_source_reextract(
            article_id=str(payload.get("article_id", "")),
            source_encoding=str(payload.get("source_encoding", "")),
        )
    except ValueError as exc:
        return {
            "ok": False,
            "message": str(exc),
            "error": "invalid_article_reextract_preview",
        }
    except OSError:
        return {
            "ok": False,
            "message": "Náhled nové extrakce se nepodařilo připravit.",
            "error": "archive_failed",
        }


def family_calendar_status_action(
    *,
    path: Path = DEFAULT_FAMILY_CALENDAR_PATH,
    today: date | None = None,
) -> dict[str, Any]:
    try:
        return family_calendar_status(path=path, today=today)
    except (ValueError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "message": f"Rodinný kalendář obsahuje neplatná data: {exc}",
            "error": "invalid_family_calendar",
        }
    except OSError as exc:
        return {
            "ok": False,
            "message": f"Rodinný kalendář se nepodařilo načíst: {exc}",
            "error": "family_calendar_unavailable",
        }


def family_calendar_prefill_action(
    *,
    path: Path = DEFAULT_FAMILY_CALENDAR_PATH,
    records: Collection[dict[str, str]] = DEFAULT_FAMILY_CALENDAR_PREFILL,
    today: date | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    today_date = today or date.today()
    try:
        result = ensure_family_calendar_prefill(
            path=path,
            records=records,
            today=today_date,
            now=now,
        )
        status = family_calendar_status(path=path, today=today_date)
    except (ValueError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "message": f"Předvyplnění rodinného kalendáře není platné: {exc}",
            "error": "invalid_family_calendar_prefill",
        }
    except OSError as exc:
        return {
            "ok": False,
            "message": f"Rodinný kalendář se nepodařilo předvyplnit: {exc}",
            "error": "family_calendar_prefill_failed",
        }
    applied = bool(result.get("applied"))
    return {
        "ok": True,
        "applied": applied,
        "message": (
            "Základní seznam osob a svátků byl předvyplněn. Narozeniny můžeš doplnit přes Upravit."
            if applied
            else "Rodinný kalendář už obsahuje údaje; předvyplnění nic nezměnilo."
        ),
        "status": status,
    }


def family_calendar_save_action(
    payload: dict[str, Any],
    *,
    path: Path = DEFAULT_FAMILY_CALENDAR_PATH,
    today: date | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    today_date = today or date.today()
    try:
        person = save_family_person(
            person_id=str(payload.get("person_id", "")),
            display_name=str(payload.get("display_name", "")),
            relation=str(payload.get("relation", "")),
            birth_date=str(payload.get("birth_date", "")),
            name_day=str(payload.get("name_day", "")),
            reminders_enabled=payload.get("reminders_enabled", True),
            active=payload.get("active", True),
            path=path,
            today=today_date,
            now=now,
        )
        status = family_calendar_status(path=path, today=today_date)
    except (ValueError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "message": str(exc),
            "error": "invalid_family_person",
        }
    except OSError as exc:
        return {
            "ok": False,
            "message": f"Osobu se nepodařilo uložit: {exc}",
            "error": "family_calendar_save_failed",
        }
    action_label = "upravena" if str(payload.get("person_id", "")).strip() else "přidána"
    return {
        "ok": True,
        "message": f"Osoba byla {action_label} v rodinném kalendáři.",
        "person": person.to_summary(today=today_date),
        "status": status,
    }


def family_calendar_notification_preview_action(
    payload: dict[str, Any],
    *,
    path: Path = DEFAULT_FAMILY_CALENDAR_PATH,
    today: date | None = None,
) -> dict[str, Any]:
    today_date = today or date.today()
    recipients = payload.get("recipients", [])
    if not isinstance(recipients, list):
        return {
            "ok": False,
            "message": "Náhled upozornění vyžaduje seznam přesně dvou příjemců.",
            "error": "invalid_notification_preview",
        }
    try:
        people = load_family_people(path, today=today_date)
        previews = build_due_notification_previews(
            people,
            today=today_date,
            recipients=recipients,
        )
    except (ValueError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "message": str(exc),
            "error": "invalid_notification_preview",
        }
    except OSError as exc:
        return {
            "ok": False,
            "message": f"Náhled upozornění se nepodařilo sestavit: {exc}",
            "error": "notification_preview_unavailable",
        }
    return {
        "ok": True,
        "today": today_date.isoformat(),
        "count": len(previews),
        "previews": previews,
        "message": (
            f"Připraveno náhledů: {len(previews)}. Nic nebylo odesláno ani uloženo."
            if previews
            else "Dnes nevychází žádné upozornění D-2 ani D-1. Nic nebylo odesláno ani uloženo."
        ),
    }


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
    sync_diagnostics: dict[str, int] = {}
    try:
        for attempt in range(5):
            try:
                reminders = sync_urgent_reminders_index(
                    inbox_dir=inbox_dir,
                    index_path=index_path,
                    sync_diagnostics=sync_diagnostics,
                )
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
    pending_download_count = max(
        0,
        int(sync_diagnostics.get("pending_download_count", 0) or 0),
    )
    if not inbox_exists:
        message = "Inbox pro mobilní vstupy zatím není synchronizovaný na Mac."
    elif pending_download_count:
        if pending_download_count == 1:
            pending_message = "1 nový iCloud soubor čeká na stažení."
        else:
            pending_message = f"{pending_download_count} nové iCloud soubory čekají na stažení."
        message = (
            f"{pending_message} Zobrazuji poslední platný index; "
            "kontrola se automaticky zopakuje."
        )
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
        "sync_pending": pending_download_count > 0,
        "pending_download_count": pending_download_count,
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
        "imap_flagged": bool(getattr(header, "flagged", False)),
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
    return normalize_email_work_item(item)


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
    return read_email_work_decisions(path)


def set_email_processing_done_flag(
    *,
    provider: str,
    folder: str,
    uid: str,
    done: bool,
    seznam_provider_factory: Callable[[], object] | None = None,
) -> dict[str, Any]:
    safe_provider = safe_text(provider).strip().casefold()
    safe_folder = safe_text(folder).strip() or "INBOX"
    safe_uid = safe_text(uid).strip()
    if safe_provider != "seznam":
        return {
            "ok": False,
            "flagged": False,
            "message": "Příznak Hotovo je v této fázi povolený pouze pro Seznam.",
        }
    if not safe_uid:
        return {"ok": False, "flagged": False, "message": "Chybí UID e-mailu."}
    try:
        client = (seznam_provider_factory or SeznamReadOnlyEmailProvider)()
        set_flagged = getattr(client, "set_message_flagged", None)
        if not callable(set_flagged):
            return {
                "ok": False,
                "flagged": False,
                "message": "Seznam provider neumí příznak Hotovo bezpečně nastavit.",
            }
        flagged = bool(set_flagged(uid=safe_uid, folder=safe_folder, flagged=bool(done)))
    except (EmailConfigError, SeznamEmailProviderError) as exc:
        return {"ok": False, "flagged": False, "message": str(exc)}
    if flagged != bool(done):
        return {
            "ok": False,
            "flagged": flagged,
            "message": "Server nepotvrdil požadovaný stav příznaku.",
        }
    return {
        "ok": True,
        "flagged": flagged,
        "message": "E-mail je na Seznamu označený příznakem Hotovo."
        if flagged
        else "Příznak Hotovo byl na Seznamu zrušen.",
    }


def save_email_processing_decision(
    *,
    item_id: str,
    action: str,
    item: dict[str, Any] | None = None,
    path: Path = EMAIL_PROCESSING_DECISIONS_FILE,
    operation_id: str = "",
) -> dict[str, Any]:
    item_id = item_id.strip()
    action = action.strip()
    if not item_id:
        return {"ok": False, "message": "Chybí ID e-mailu."}
    if action not in EMAIL_PROCESSING_ACTIONS:
        return {"ok": False, "message": "Neznámá akce."}

    repository_result = repository_save_email_work_decision(
        path=path,
        item_id=item_id,
        action=action,
        item=item if isinstance(item, dict) else {},
        operation_id=operation_id,
    )
    resolved_action = str(repository_result.result.get("action", action))
    resolved_item_id = str(repository_result.result.get("item_id", item_id))
    label = {
        "process": "označeno ke zpracování",
        "ignore": "označeno k ignorování",
        "trash_requested": "označeno ke smazání po potvrzení",
        "": "rozhodnutí zrušeno",
    }[resolved_action]
    return {
        "ok": True,
        "message": label,
        "item_id": resolved_item_id,
        "action": resolved_action,
        "changed": repository_result.changed,
        "idempotent_replay": repository_result.idempotent_replay,
    }


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
        items.append(normalize_email_work_item(item))

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
                    "trash_folder": str(item.get("trash_folder", "")),
                    "trash_uid": str(item.get("trash_uid", "")),
                    "message_id": str(item.get("message_id", "")),
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


def email_processing_pending_purge_items(
    actions_path: Path = EMAIL_WORK_QUEUE_ACTIONS_FILE,
) -> dict[str, Any]:
    result = pending_email_purge_items(actions_path)
    count = int(result.get("count", 0) or 0)
    unrecoverable = int(result.get("unrecoverable_count", 0) or 0)
    result["message"] = f"Obnoveno položek připravených k trvalému smazání: {count}."
    if unrecoverable:
        result["message"] += f" Starších neregenerovatelných záznamů: {unrecoverable}."
    return result


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
    repository_save_email_work_decision(
        path=path,
        item_id=item_id,
        action="",
    )


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
        codex_approval=load_codex_approval_request,
        git=git_status_summary,
    )
    return build_cockpit_status(loaders=loaders, code_stamp=COCKPIT_CODE_STAMP)


def cockpit_live_status(
    *,
    codex_approval_loader: Callable[[], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return the lightweight, frequently changing approval state."""
    return build_cockpit_live_status(
        codex_approval_loader=codex_approval_loader or load_codex_approval_request,
    )


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
        return reminder_email_archive_source_detail(
            base=base,
            source=source,
            archive_directory=archive_directory,
            vault_dir=vault_dir,
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
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> dict[str, Any]:
    archive_id = str(source.get("uid", "")).strip()
    resolved = resolve_email_archive_dir(
        archive_id,
        archive_directory=archive_directory,
    )
    if not resolved.get("ok"):
        return {**base, "ok": False, "kind": "email_archive", "message": "Zdrojový e-mailový archiv nemá bezpečné ID."}
    archive_path = resolved["path"]
    evidence = email_archive_evidence_summary(
        evidence_archive_id=archive_path.name,
        archive_directory=archive_directory,
    )
    if evidence is None:
        return {**base, "ok": False, "kind": "email_archive", "message": "E-mailový archiv nebyl nalezen."}
    attachments_path = archive_path / "attachments" / "attachments.json"
    metadata_path = archive_path / "metadata.json"
    try:
        metadata = read_json_file(metadata_path)
    except (OSError, ValueError, json.JSONDecodeError):
        metadata = {}
    email_uid = email_archive_uid(metadata, archive_path.name)
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
    vault_attachments = vault_email_archive_attachments(
        uid=email_uid,
        documents_dir=vault_dir,
    )
    safe_evidence = {
        **evidence,
        "archive_id": safe_text(str(evidence.get("archive_id", ""))),
        "archive_ref": email_archive_reference(archive_path.name),
        "archive_path": safe_text(str(evidence.get("archive_path", ""))),
        "metadata_path": safe_text(str(evidence.get("metadata_path", ""))),
    }
    return {
        **base,
        "ok": True,
        "kind": "email_archive",
        "message": "Zdroj připomínky je uložený lokální e-mailový archiv.",
        "email": {
            "provider": "archive",
            "folder": "",
            "uid": safe_text(archive_id),
            "archive_ref": email_archive_reference(archive_path.name),
            "subject": evidence.get("subject", ""),
            "sender": evidence.get("sender", ""),
            "date": evidence.get("email_date", ""),
            "body_text": "Tělo e-mailu je uložené lokálně v EmailArchiveVault; v Cockpitu se ukazují jen bezpečná metadata.",
            "attachments": attachments,
            "vault_attachments": vault_attachments,
        },
        "archive": safe_evidence,
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
    stale_past_due_days: int = 90,
) -> dict[str, Any]:
    return build_document_due_candidates_status(
        vault_dir=vault_dir,
        reminders_path=reminders_path,
        archive_directory=archive_directory,
        today=today,
        limit=limit,
        stale_past_due_days=stale_past_due_days,
    )


def document_case_health_status(
    *,
    documents: list[dict[str, Any]] | None = None,
    reminders: list[dict[str, Any]],
    due_candidates: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
) -> dict[str, Any]:
    return build_document_case_health_status(
        documents=documents,
        reminders=reminders,
        due_candidates=due_candidates,
        conflicts=conflicts,
    )


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
    resolved_downloads = downloads if downloads is not None else safe_downloads_status(limit=50)
    return build_document_work_status(
        resolved_downloads,
        vault_dir=vault_dir,
        limit=limit,
        review_status_loader=stored_documents_review_status,
    )


def document_intake_status(
    downloads: dict[str, Any] | None = None,
    *,
    decisions_path: Path = EMAIL_PROCESSING_DECISIONS_FILE,
    mobile_inbox_dir: Path = DEFAULT_MOBILE_DOCUMENT_INBOX,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 5,
) -> dict[str, Any]:
    resolved_downloads = downloads if downloads is not None else safe_downloads_status(limit=50)
    email_pending = email_processing_pending_work_items(path=decisions_path)
    return build_document_intake_status(
        resolved_downloads,
        email_pending,
        mobile_inbox_dir=mobile_inbox_dir,
        vault_dir=vault_dir,
        limit=limit,
    )


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


def document_cases_status(
    *,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 6,
    documents_per_case: int = 3,
) -> dict[str, Any]:
    return build_document_cases_status(
        vault_dir=vault_dir,
        limit=limit,
        documents_per_case=documents_per_case,
    )


def document_case_detail_status(
    case_ref: str,
    *,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    reminders_path: Path = DEFAULT_REMINDERS_PATH,
    today: date | None = None,
    limit: int = 30,
) -> dict[str, Any]:
    return build_document_case_detail_status(
        case_ref,
        dependencies=DocumentCaseDependencies(
            due_candidates=build_document_due_candidates,
            reminder_conflicts=reminder_conflicts,
            stored_pdf_is_openable=document_stored_path_is_openable_pdf,
        ),
        vault_dir=vault_dir,
        reminders_path=reminders_path,
        today=today,
        limit=limit,
    )


def document_classification_status(
    *,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 6,
) -> dict[str, Any]:
    return build_document_classification_status(vault_dir=vault_dir, limit=limit)


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


def stored_documents_review_status(
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 8,
) -> dict[str, Any]:
    return build_stored_documents_review_status(vault_dir=vault_dir, limit=limit)


def document_review_report_status(
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 12,
    short_text_threshold: int = 500,
) -> dict[str, Any]:
    return build_document_review_report_status(
        vault_dir=vault_dir,
        limit=limit,
        short_text_threshold=short_text_threshold,
    )


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


def human_adam_simple_main_deployment_action(
    *,
    confirmed: bool,
    service: HumanAdamProfileManager = HUMAN_ADAM,
    host: str = "127.0.0.1",
    port: int = COCKPIT_PORT,
    restart_action: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Privately bind a clean-main deployment to the controlled restart worker.

    The app layer owns the running PID and network coordinates; the profile
    manager owns the canonical workstream, commit and workspace proof.  Phase
    3.1 wires this action to the existing deploy control without changing its
    visual structure.
    """

    previous_pid = os.getpid()
    worker = restart_action or start_cockpit_restart_action

    def schedule_restart() -> dict[str, Any]:
        return worker(
            confirmed=True,
            host=host,
            port=port,
            pid=previous_pid,
        )

    try:
        return service.prepare_simple_main_deployment(
            previous_pid=previous_pid,
            confirmed=confirmed,
            restart_scheduler=schedule_restart,
        )
    except (AppServerError, SessionHubError, OSError, TypeError, ValueError) as exc:
        return {
            "ok": False,
            "status": "simple_main_deployment_failed",
            "message": str(exc),
        }


def human_adam_simple_main_deployment_verification_action(
    *,
    service: HumanAdamProfileManager = HUMAN_ADAM,
) -> dict[str, Any]:
    """Privately verify the restarted Cockpit from server-owned evidence.

    The new process PID and code stamp come from the running server; the profile
    manager binds them to the pending canonical workstream receipt and performs
    the full post-restart proof.
    """

    try:
        return service.verify_simple_main_deployment(
            observed_pid=os.getpid(),
            observed_code_stamp=COCKPIT_CODE_STAMP,
        )
    except (AppServerError, SessionHubError, OSError, TypeError, ValueError) as exc:
        return {
            "ok": False,
            "status": "simple_main_deployment_verification_failed",
            "message": str(exc),
        }


def human_adam_pending_deployment_startup_verification_action(
    *,
    service: HumanAdamProfileManager = HUMAN_ADAM,
    verification_action: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Finish one pending deployment from the restarted server itself."""

    receipt_path = Path(service.simple_main_deployment_receipt_path)
    if not receipt_path.exists():
        return {
            "ok": True,
            "state": "not_pending",
            "verification_needed": False,
        }
    try:
        receipt = load_simple_main_deployment_receipt(receipt_path)
    except (SimpleMainDeploymentError, OSError, TypeError, ValueError) as exc:
        return {
            "ok": False,
            "status": "simple_main_deployment_receipt_invalid",
            "message": str(exc),
        }
    if receipt.get("state") != PENDING_RESTART:
        return {
            "ok": True,
            "state": str(receipt.get("state") or "not_pending"),
            "verification_needed": False,
        }
    verifier = (
        verification_action
        or human_adam_simple_main_deployment_verification_action
    )
    return verifier(service=service)


def schedule_pending_deployment_startup_verification(
    *,
    host: str,
    port: int,
    service: HumanAdamProfileManager = HUMAN_ADAM,
    attempts: int = 60,
    delay_seconds: float = 0.5,
    verification_action: Callable[..., dict[str, Any]] | None = None,
) -> bool:
    """Verify a restart-bound receipt after the canonical server starts serving."""

    if host not in {"127.0.0.1", "localhost"} or int(port) != COCKPIT_PORT:
        return False

    def worker() -> None:
        last_message = ""
        for _attempt in range(max(1, int(attempts))):
            if delay_seconds > 0:
                time.sleep(delay_seconds)
            result = human_adam_pending_deployment_startup_verification_action(
                service=service,
                verification_action=verification_action,
            )
            if result.get("ok") is True:
                if result.get("state") == "deployed" and result.get(
                    "verification_needed"
                ) is not False:
                    print(
                        "Čekající nasazení bylo po restartu serverově ověřeno.",
                        flush=True,
                    )
                return
            last_message = str(
                result.get("message")
                or "Čekající nasazení zatím nelze serverově ověřit."
            )
        print(
            "Automatické ověření čekajícího nasazení zůstalo fail-closed: "
            + last_message,
            flush=True,
        )

    threading.Thread(
        target=worker,
        name="cockpit-deployment-verifier",
        daemon=True,
    ).start()
    return True


def human_adam_simple_main_deployment_audit_action(
    *,
    service: HumanAdamProfileManager = HUMAN_ADAM,
) -> dict[str, Any]:
    """Return the server-derived clean-main audit used by the existing control."""

    try:
        return service.audit_simple_main_deployment()
    except (AppServerError, SessionHubError, OSError, TypeError, ValueError) as exc:
        return {
            "ok": False,
            "ready": False,
            "status": "simple_main_deployment_audit_failed",
            "message": str(exc),
        }


def human_adam_main_remote_sync_audit_action(
    *,
    service: HumanAdamProfileManager = HUMAN_ADAM,
) -> dict[str, Any]:
    """Return a read-only exact fast-forward plan for clean origin/main."""

    try:
        return service.audit_main_remote_sync()
    except (AppServerError, SessionHubError, OSError, TypeError, ValueError) as exc:
        return {
            "ok": False,
            "read_only": True,
            "writes_performed": False,
            "state": "audit_failed",
            "can_fast_forward": False,
            "status": "main_remote_sync_audit_failed",
            "message": str(exc),
        }


def human_adam_github_batch_audit_action(
    *,
    service: HumanAdamProfileManager = HUMAN_ADAM,
) -> dict[str, Any]:
    """Return an exact read-only plan for the accumulated daily GitHub batch."""

    try:
        return service.audit_github_batch()
    except (AppServerError, SessionHubError, OSError, TypeError, ValueError) as exc:
        return {
            "ok": False,
            "read_only": True,
            "writes_performed": False,
            "state": "audit_failed",
            "ready": False,
            "pending": False,
            "status": "github_batch_audit_failed",
            "message": str(exc),
        }


def human_adam_github_batch_action(
    payload: dict[str, Any],
    *,
    service: HumanAdamProfileManager = HUMAN_ADAM,
) -> dict[str, Any]:
    """Run one confirmed full gate and push the exact audited daily batch."""

    try:
        return service.push_github_batch(
            expected_origin_head=str(payload.get("expected_origin_head") or ""),
            expected_local_head=str(payload.get("expected_local_head") or ""),
            confirmation=str(payload.get("confirmation") or ""),
        )
    except (AppServerError, SessionHubError, OSError, TypeError, ValueError) as exc:
        return {
            "ok": False,
            "state": "github_batch_failed",
            "status": "github_batch_failed",
            "message": str(exc),
        }


def human_adam_main_remote_sync_action(
    payload: dict[str, Any],
    *,
    service: HumanAdamProfileManager = HUMAN_ADAM,
) -> dict[str, Any]:
    """Apply one explicitly confirmed fast-forward bound to its audit heads."""

    try:
        return service.apply_main_remote_sync(
            expected_local_head=str(payload.get("expected_local_head") or ""),
            expected_origin_head=str(payload.get("expected_origin_head") or ""),
            confirmed=payload.get("confirmed") is True,
        )
    except (AppServerError, SessionHubError, OSError, TypeError, ValueError) as exc:
        return {
            "ok": False,
            "state": "main_remote_sync_failed",
            "status": "main_remote_sync_failed",
            "message": str(exc),
        }


def cockpit_codex_approval_clear_action(
    payload: dict[str, Any],
    *,
    clearer: Callable[..., dict[str, Any]] = clear_codex_approval_request,
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
    }


DEV_RUNNER_ACTIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "cockpit_tests",
        "label": "Testy Cockpitu",
        "summary": "Spustí cílené unittesty pro Cockpit.",
        "command": [str(PROJECT_ROOT / ".venv" / "bin" / "python"), "-m", "unittest", "tests.test_cockpit"],
        "timeout": 90,
    },
    {
        "id": "cockpit_py_compile",
        "label": "Python syntax",
        "summary": "Zkontroluje syntaxi hlavního Cockpit Python souboru.",
        "command": [str(PROJECT_ROOT / ".venv" / "bin" / "python"), "-m", "py_compile", "app/cockpit.py"],
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


def human_adam_transcribe_action(
    payload: dict[str, Any],
    *,
    transcriber: Callable[..., dict[str, Any]] = transcribe_audio_base64_isolated,
) -> dict[str, Any]:
    """Return an editable transcript without persistence or delivery side effects."""
    language = str(payload.get("language") or "cs").strip().casefold()
    if language != "cs":
        return {
            "ok": False,
            "status": "human_adam_transcription_failed",
            "text": "",
            "message": "První fáze hlasového vstupu podporuje pouze češtinu.",
        }
    try:
        result = transcriber(
            str(payload.get("audio_base64") or ""),
            mime_type=str(payload.get("mime_type") or ""),
            language=language,
        )
        text = str(result.get("text") or "").strip()
        if not text:
            raise TranscriptionError("Přepis je prázdný; zkus mluvit blíž k mikrofonu.")
        if len(text) > 12_000:
            raise TranscriptionError("Přepis je příliš dlouhý pro textové pole Human–Adam.")
        return {"ok": True, "status": "transcribed_for_review", "text": text}
    except (TranscriptionError, OSError, ValueError) as exc:
        return {
            "ok": False,
            "status": "human_adam_transcription_failed",
            "text": "",
            "message": str(exc),
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
        "path": "/api/r2-adam/connect",
        "label": "Pripojit samostatnou relaci R2-Adam",
        "risk": "local_service",
        "confirmation": "automatic_on_explicit_r2_page_open",
        "handler_name": "janicka_r2_chat_connect_action",
        "test_level": "direct",
    },
    {
        "path": "/api/r2-adam/send",
        "label": "Odeslat zpravu do uzce ohraniceneho chatu R2-Adam",
        "risk": "private_write",
        "confirmation": "explicit_chat_message_owned_txt_only",
        "handler_name": "janicka_r2_chat_send_action",
        "test_level": "direct",
    },
    {
        "path": "/api/janicka-r2/documents/search",
        "label": "Vyhledat redigovane volby dokumentu pro Janicku R2",
        "risk": "read_only_via_post",
        "confirmation": "none_readonly",
        "handler_name": "janicka_r2_document_search_action",
        "test_level": "direct",
    },
    {
        "path": "/api/janicka-r2/documents/compile",
        "label": "Vytvorit novy TXT z lidsky vybraneho dokumentu",
        "risk": "private_write",
        "confirmation": "explicit_ui_selection_create_only",
        "handler_name": "janicka_r2_document_compile_action",
        "test_level": "direct",
    },
    {
        "path": "/api/human-adam/transcribe",
        "label": "Prepsat hlas do editovatelneho Human-Adam konceptu",
        "risk": "external_ai",
        "confirmation": "explicit_microphone_recording_no_delivery",
        "handler_name": "human_adam_transcribe_action",
        "test_level": "direct",
    },
    {
        "path": "/api/human-adam/connect",
        "label": "Pripojit kanonickou relaci Human-Adam",
        "risk": "local_service",
        "confirmation": "explicit_human_adam_button",
        "handler_name": "human_adam_connect_action",
        "test_level": "direct",
    },
    {
        "path": "/api/human-adam/profile",
        "label": "Atomicky prepnout kanonicky pracovni proud Human-Adam",
        "risk": "local_service",
        "confirmation": "explicit_workstream_switch",
        "handler_name": "human_adam_profile_switch_action",
        "test_level": "direct",
    },
    {
        "path": "/api/human-adam/development-semaphore",
        "label": "Prevzit nebo zmenit globalni vyvojovy semafor",
        "risk": "private_write",
        "confirmation": "explicit_development_owner_change",
        "handler_name": "human_adam_development_semaphore_action",
        "test_level": "direct",
    },
    {
        "path": "/api/human-adam/deferred-integration",
        "label": "Potvrzene prevzit presne odlozeny Human-Adam WIP do main",
        "risk": "git_commit_push",
        "confirmation": "exact_deferred_integration_phrase_and_ownership_marker",
        "handler_name": "human_adam_deferred_integration_action",
        "test_level": "direct",
    },
    {
        "path": "/api/human-adam/owned-wip-recovery",
        "label": "Potvrzene dokoncit presne vlastneny Human-Adam WIP bez uctenky",
        "risk": "git_commit_push",
        "confirmation": "exact_owned_wip_recovery_phrase_and_metadata",
        "handler_name": "human_adam_owned_wip_recovery_action",
        "test_level": "direct",
    },
    {
        "path": "/api/human-adam/thread-rotation",
        "label": "Potvrzena rotace profiloveho vlakna Human-Adam",
        "risk": "private_write",
        "confirmation": "exact_thread_rotation_phrase",
        "handler_name": "human_adam_thread_rotation_action",
        "test_level": "direct",
    },
    {
        "path": "/api/human-adam/send",
        "label": "Odeslat zapisujici tah Human-Adam",
        "risk": "workspace_write",
        "confirmation": "protocol_ids_required",
        "handler_name": "human_adam_send_action",
        "test_level": "direct",
    },
    {
        "path": "/api/human-adam/checkpoint",
        "label": "Vytvorit lokalni Human-Adam WIP checkpoint",
        "risk": "workspace_write",
        "confirmation": "explicit_human_adam_checkpoint",
        "handler_name": "human_adam_checkpoint_action",
        "test_level": "direct",
    },
    {
        "path": "/api/human-adam/deploy",
        "label": "Overit a nasadit cisty main aktivniho pracovniho proudu",
        "risk": "local_service",
        "confirmation": "clean_main_audit_exact_phrase",
        "handler_name": "human_adam_simple_main_deployment_action",
        "test_level": "direct",
    },
    {
        "path": "/api/human-adam/main-sync",
        "label": "Potvrzene fast-forwardovat cisty lokalni main z origin/main",
        "risk": "git_fast_forward",
        "confirmation": "explicit_button_and_exact_audited_heads",
        "handler_name": "human_adam_main_remote_sync_action",
        "test_level": "direct",
    },
    {
        "path": "/api/human-adam/github-batch",
        "label": "Odeslat potvrzeny denni balik lokalnich main commitu na GitHub",
        "risk": "git_push",
        "confirmation": "exact_phrase_and_exact_audited_heads",
        "handler_name": "human_adam_github_batch_action",
        "test_level": "direct",
    },
    {
        "path": "/api/human-adam/deploy-verification",
        "label": "Overit dokonceni nasazeni po restartu Cockpitu",
        "risk": "private_write",
        "confirmation": "pending_receipt_server_evidence",
        "handler_name": "human_adam_simple_main_deployment_verification_action",
        "test_level": "direct",
    },
    {
        "path": "/api/codex-approval/clear",
        "label": "Vycistit Codex approval kartu",
        "risk": "private_write",
        "confirmation": "ui_confirm_boolean",
        "handler_name": "cockpit_codex_approval_clear_action",
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
        "path": "/api/library/update",
        "label": "Upravit ulozeny clanek knihovny",
        "risk": "private_write",
        "confirmation": "validated_article_content",
        "handler_name": "library_update_article_action",
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
        "path": "/api/library/attachment/update",
        "label": "Upravit popisek prilohy knihovny",
        "risk": "private_write",
        "confirmation": "validated_attachment_metadata",
        "handler_name": "library_update_attachment_action",
        "test_level": "direct",
    },
    {
        "path": "/api/library/attachment/remove",
        "label": "Odebrat prilohu knihovny do soukromeho kose",
        "risk": "delete_or_purge",
        "confirmation": "exact_phrase",
        "handler_name": "library_remove_attachment_action",
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
        "path": "/api/library/reextract-preview",
        "label": "Nahled nove extrakce clanku knihovny",
        "risk": "read_only_via_post",
        "confirmation": "none_readonly_no_persistence",
        "handler_name": "library_article_reextract_preview_action",
        "test_level": "direct",
    },
    {
        "path": "/api/family-calendar/save",
        "label": "Ulozit osobu do rodinneho kalendare",
        "risk": "private_write",
        "confirmation": "validated_family_person",
        "handler_name": "family_calendar_save_action",
        "test_level": "direct",
    },
    {
        "path": "/api/family-calendar/prefill",
        "label": "Predvyplnit rodinny kalendar",
        "risk": "private_write",
        "confirmation": "explicit_user_authorized_defaults",
        "handler_name": "family_calendar_prefill_action",
        "test_level": "direct",
    },
    {
        "path": "/api/family-calendar/notification-preview",
        "label": "Zobrazit nahled upozorneni rodinneho kalendare",
        "risk": "read_only_via_post",
        "confirmation": "none_readonly_no_persistence",
        "handler_name": "family_calendar_notification_preview_action",
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
        "path": "/api/email-processing/done-flag",
        "label": "Nastavit nebo zrusit Seznam IMAP priznak Hotovo",
        "risk": "private_write",
        "confirmation": "explicit_ui_action_reversible",
        "handler_name": "set_email_processing_done_flag",
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
        schedule_pending_deployment_startup_verification(
            host=self.host,
            port=self.port,
        )
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
                if parsed.path == "/human-adam/":
                    self.respond_html(HUMAN_ADAM_HTML)
                    return
                if parsed.path == "/r2-adam/":
                    self.respond_html(R2_ADAM_CHAT_HTML)
                    return
                if parsed.path == "/r2-adam/document/":
                    self.respond_html(R2_ADAM_DOCUMENT_READER_HTML)
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
                if parsed.path == "/janicka-r2-documents/":
                    self.respond_html(JANICKA_R2_DOCUMENTS_HTML)
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
                if parsed.path == "/api/r2-adam/status":
                    self.respond_json(
                        janicka_r2_chat_status_action(adapter=JANICKA_R2_CHAT)
                    )
                    return
                if parsed.path == "/api/r2-adam/documents":
                    self.respond_json(
                        janicka_r2_chat_documents_action(adapter=JANICKA_R2_CHAT)
                    )
                    return
                if parsed.path == "/api/r2-adam/document":
                    params = parse_qs(parsed.query)
                    self.respond_json(
                        janicka_r2_chat_document_action(
                            params.get("ref", [""])[0],
                            adapter=JANICKA_R2_CHAT,
                        )
                    )
                    return
                if parsed.path == "/api/human-adam/status":
                    self.respond_json(human_adam_status_action(service=HUMAN_ADAM))
                    return
                if parsed.path == "/api/human-adam/development-semaphore":
                    self.respond_json(human_adam_development_semaphore_status_action(service=HUMAN_ADAM))
                    return
                if parsed.path == "/api/human-adam/project-continuity":
                    self.respond_json(human_adam_project_continuity_action(service=HUMAN_ADAM))
                    return
                if parsed.path == "/api/human-adam/thread-rotation":
                    self.respond_json(human_adam_thread_rotation_status_action(service=HUMAN_ADAM))
                    return
                if parsed.path == "/api/human-adam/tvbcp":
                    self.respond_json(human_adam_tvbcp_action(service=HUMAN_ADAM))
                    return
                if parsed.path == "/api/human-adam/workspace":
                    self.respond_json(
                        human_adam_work_review_action(
                            service=HUMAN_ADAM,
                            observed_code_stamp=COCKPIT_CODE_STAMP,
                        )
                    )
                    return
                if parsed.path == "/api/human-adam/deploy-audit":
                    self.respond_json(
                        human_adam_simple_main_deployment_audit_action(service=HUMAN_ADAM)
                    )
                    return
                if parsed.path == "/api/human-adam/main-sync-audit":
                    self.respond_json(
                        human_adam_main_remote_sync_audit_action(service=HUMAN_ADAM)
                    )
                    return
                if parsed.path == "/api/human-adam/github-batch-audit":
                    self.respond_json(
                        human_adam_github_batch_audit_action(service=HUMAN_ADAM)
                    )
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
                if parsed.path == "/api/command-cheatsheet":
                    self.respond_json(load_command_cheatsheet())
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
                    full_text = params.get("full", [""])[0].strip().casefold() in {"1", "true", "yes"}
                    self.respond_json(get_article(article_id=article_id, max_chars=0 if full_text else 40000))
                    return
                if parsed.path == "/api/library/attachment":
                    params = parse_qs(parsed.query)
                    article_id = params.get("id", [""])[0]
                    attachment_id = params.get("attachment_id", [""])[0]
                    variant = params.get("variant", ["readable"])[0]
                    self.respond_library_attachment(article_id, attachment_id, variant)
                    return
                if parsed.path == "/api/family-calendar/status":
                    self.respond_json(family_calendar_status_action())
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
                if parsed.path == "/api/email-processing/pending-purge":
                    self.respond_json(email_processing_pending_purge_items())
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
                if parsed.path == "/email-archive/attachment":
                    params = parse_qs(parsed.query)
                    archive_id = params.get("archive_id", [""])[0]
                    attachment_ref = params.get("attachment", [""])[0]
                    self.respond_email_archive_attachment(
                        archive_id=archive_id,
                        attachment_ref=attachment_ref,
                    )
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
                if parsed.path == "/api/r2-adam/connect":
                    self.read_json()
                    self.respond_json(
                        janicka_r2_chat_connect_action(adapter=JANICKA_R2_CHAT)
                    )
                    return
                if parsed.path == "/api/r2-adam/send":
                    payload = self.read_json()
                    self.respond_json(
                        janicka_r2_chat_send_action(
                            payload,
                            adapter=JANICKA_R2_CHAT,
                        )
                    )
                    return
                if parsed.path == "/api/janicka-r2/documents/search":
                    payload = self.read_json()
                    self.respond_json(
                        janicka_r2_document_search_action(
                            payload,
                            adapter=JANICKA_R2_COCKPIT,
                        )
                    )
                    return
                if parsed.path == "/api/janicka-r2/documents/compile":
                    payload = self.read_json()
                    self.respond_json(
                        janicka_r2_document_compile_action(
                            payload,
                            adapter=JANICKA_R2_COCKPIT,
                        )
                    )
                    return
                if parsed.path == "/api/human-adam/transcribe":
                    payload = self.read_json()
                    self.respond_json(human_adam_transcribe_action(payload))
                    return
                if parsed.path == "/api/human-adam/connect":
                    self.respond_json(human_adam_connect_action(service=HUMAN_ADAM))
                    return
                if parsed.path == "/api/human-adam/profile":
                    payload = self.read_json()
                    self.respond_json(human_adam_profile_switch_action(payload, service=HUMAN_ADAM))
                    return
                if parsed.path == "/api/human-adam/development-semaphore":
                    payload = self.read_json()
                    self.respond_json(human_adam_development_semaphore_action(payload, service=HUMAN_ADAM))
                    return
                if parsed.path == "/api/human-adam/deferred-integration":
                    payload = self.read_json()
                    self.respond_json(human_adam_deferred_integration_action(payload, service=HUMAN_ADAM))
                    return
                if parsed.path == "/api/human-adam/owned-wip-recovery":
                    payload = self.read_json()
                    self.respond_json(human_adam_owned_wip_recovery_action(payload, service=HUMAN_ADAM))
                    return
                if parsed.path == "/api/human-adam/thread-rotation":
                    payload = self.read_json()
                    self.respond_json(human_adam_thread_rotation_action(payload, service=HUMAN_ADAM))
                    return
                if parsed.path == "/api/human-adam/send":
                    payload = self.read_json()
                    self.respond_json(
                        human_adam_send_action(
                            payload,
                            service=HUMAN_ADAM,
                            observed_code_stamp=COCKPIT_CODE_STAMP,
                        )
                    )
                    return
                if parsed.path == "/api/human-adam/checkpoint":
                    payload = self.read_json()
                    self.respond_json(human_adam_checkpoint_action(payload, service=HUMAN_ADAM))
                    return
                if parsed.path == "/api/human-adam/deploy":
                    payload = self.read_json()
                    confirmation = str(payload.get("confirmation") or "").strip()
                    self.respond_json(
                        human_adam_simple_main_deployment_action(
                            confirmed=confirmation == SIMPLE_MAIN_DEPLOYMENT_CONFIRMATION,
                            service=HUMAN_ADAM,
                            host=cockpit_host,
                            port=cockpit_port,
                        )
                    )
                    return
                if parsed.path == "/api/human-adam/main-sync":
                    payload = self.read_json()
                    self.respond_json(
                        human_adam_main_remote_sync_action(
                            payload,
                            service=HUMAN_ADAM,
                        )
                    )
                    return
                if parsed.path == "/api/human-adam/github-batch":
                    payload = self.read_json()
                    self.respond_json(
                        human_adam_github_batch_action(
                            payload,
                            service=HUMAN_ADAM,
                        )
                    )
                    return
                if parsed.path == "/api/human-adam/deploy-verification":
                    self.read_json()
                    self.respond_json(
                        human_adam_simple_main_deployment_verification_action(
                            service=HUMAN_ADAM
                        )
                    )
                    return
                if parsed.path == "/api/codex-approval/clear":
                    payload = self.read_json()
                    self.respond_json(cockpit_codex_approval_clear_action(payload))
                    return
                if parsed.path == "/api/dev-runner/run":
                    payload = self.read_json()
                    self.respond_json(cockpit_dev_runner_run_action(payload))
                    return
                if parsed.path == "/api/desktop-apps/open":
                    payload = self.read_json()
                    self.respond_json(open_desktop_app_action(payload))
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
                if parsed.path == "/api/library/update":
                    payload = self.read_json()
                    self.respond_json(library_update_article_action(payload))
                    return
                if parsed.path == "/api/library/attachment/add":
                    payload = self.read_json()
                    self.respond_json(library_attach_image_action(payload))
                    return
                if parsed.path == "/api/library/attachment/update":
                    payload = self.read_json()
                    self.respond_json(library_update_attachment_action(payload))
                    return
                if parsed.path == "/api/library/attachment/remove":
                    payload = self.read_json()
                    self.respond_json(library_remove_attachment_action(payload))
                    return
                if parsed.path == "/api/library/delete":
                    payload = self.read_json()
                    self.respond_json(library_delete_article_action(payload))
                    return
                if parsed.path == "/api/library/reextract-preview":
                    payload = self.read_json()
                    self.respond_json(library_article_reextract_preview_action(payload))
                    return
                if parsed.path == "/api/family-calendar/save":
                    payload = self.read_json()
                    self.respond_json(family_calendar_save_action(payload))
                    return
                if parsed.path == "/api/family-calendar/prefill":
                    self.read_json()
                    self.respond_json(family_calendar_prefill_action())
                    return
                if parsed.path == "/api/family-calendar/notification-preview":
                    payload = self.read_json()
                    self.respond_json(family_calendar_notification_preview_action(payload))
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
                if parsed.path == "/api/email-processing/done-flag":
                    payload = self.read_json()
                    self.respond_json(
                        set_email_processing_done_flag(
                            provider=str(payload.get("provider", "")),
                            folder=str(payload.get("folder", "INBOX")),
                            uid=str(payload.get("uid", "")),
                            done=payload.get("done") is True,
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
                            operation_id=str(payload.get("operation_id", "")),
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

            def respond_email_archive_attachment(
                self,
                archive_id: str,
                attachment_ref: str,
            ) -> None:
                resolved = resolve_email_archive_embedded_attachment(
                    archive_id=archive_id,
                    attachment_ref=attachment_ref,
                )
                if not resolved.get("ok"):
                    self.respond_json(
                        {"error": "not_found", "message": resolved.get("message", "")},
                        status=HTTPStatus.NOT_FOUND,
                    )
                    return
                data = resolved["data"]
                filename = safe_filename(
                    str(resolved.get("filename") or "attachment")
                )
                content_type = str(
                    resolved.get("content_type") or "application/octet-stream"
                )
                disposition = (
                    "inline"
                    if content_type == "application/pdf"
                    or (
                        content_type.startswith("image/")
                        and content_type != "image/svg+xml"
                    )
                    or content_type.startswith("text/plain")
                    else "attachment"
                )
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", content_type)
                self.send_header(
                    "Content-Disposition",
                    f'{disposition}; filename="{filename}"',
                )
                self.send_header("Cache-Control", "no-store, max-age=0")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

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


def run_cockpit_server(host: str = "127.0.0.1", port: int = COCKPIT_PORT) -> None:
    CockpitServer(host=host, port=port).serve()
