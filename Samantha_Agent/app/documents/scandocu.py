from __future__ import annotations

import json
import mimetypes
import re
import shutil
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .ai_metadata import AIMetadataError, request_codex_metadata_suggestion
from .archive_browser import (
    IMAGE_EXTENSIONS as ARCHIVE_IMAGE_EXTENSIONS,
    resolve_stored_document_file,
    stored_document_detail_status,
    stored_document_list_status,
)
from .consistency_audit import AuditFact, best_asset_label, document_row_to_fact, primary_amount
from .transactions import (
    DocumentRecordMutation,
    DocumentRecordNotFoundError,
    DocumentRelatedJsonMutation,
    DocumentTransactionError,
    transact_document_record,
)
from .vault import (
    DEFAULT_DOCUMENTS_DIR,
    PROJECT_ROOT,
    apply_document_import_file,
    extract_text,
    find_due_date_candidates,
    find_duplicate_by_sha,
    merge_tags,
    normalize_domain,
    parse_tags,
    propose_metadata,
    read_json_file,
    read_jsonl,
    relative_to_project,
    safe_ascii_slug,
    safe_filename,
    safe_slug,
    safe_text,
    sha256_file,
    tokenize,
    validate_source_file,
    write_json,
    append_jsonl,
)


DEFAULT_DOWNLOADS_DIR = Path.home() / "Downloads"
DEFAULT_DOWNLOADS_MAX_AGE_DAYS = 7
SCANDOCU_ROOT_NAME = "scandocu"
SCANDOCU_ACTIONS_FILE = "scandocu_actions.jsonl"
SCANDOCU_CLASSIFIER_VERSION = "2026-06-03-travel-classifier-v2"
SCANDOCU_EXTRACTOR_RETRY_VERSION = "2026-06-03-pdf-text-cache-v3"
SCANDOCU_TOKEN_LIMIT = 80
SCANDOCU_DOMAIN_REGISTRY_FILE = "domain_registry.json"
SCANDOCU_IMAGE_PREVIEW_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
SCANDOCU_BUILTIN_DOMAINS = (
    "food",
    "health",
    "car",
    "insurance",
    "energy",
    "home",
    "tax",
    "warranty",
    "travel",
    "telecom",
    "other",
)


@dataclass(frozen=True)
class ScanDocuCandidate:
    source_mode: str
    token: str
    source_path: Path
    working_path: Path
    metadata_path: Path
    title: str
    domain: str
    document_type: str
    counterparty: str
    related_asset: str
    tags: list[str]
    case_id: str
    extraction_method: str
    ocr_needed: bool
    warning: str
    due_date_count: int
    duplicate_document_id: str = ""
    review_document_id: str = ""
    probable_duplicates: list[dict[str, Any]] | None = None

    def to_api(self) -> dict[str, Any]:
        extension = self.working_path.suffix.lower()
        if extension == ".pdf":
            preview_kind = "pdf"
            preview_url = f"/pdf/{self.token}"
        elif extension in SCANDOCU_IMAGE_PREVIEW_EXTENSIONS:
            preview_kind = "image"
            preview_url = f"/preview/{self.token}"
        else:
            preview_kind = "none"
            preview_url = ""
        inline_preview = preview_kind != "none"
        return {
            "found": True,
            "source_mode": self.source_mode,
            "token": self.token,
            "source_name": self.source_path.name,
            "source_path": str(self.source_path),
            "working_path": str(relative_to_project(self.working_path)),
            "pdf_url": f"/pdf/{self.token}",
            "preview_url": preview_url,
            "file_url": f"/file/{self.token}",
            "file_extension": extension,
            "inline_preview": inline_preview,
            "preview_kind": preview_kind,
            "title": self.title,
            "domain": self.domain,
            "document_type": self.document_type,
            "counterparty": self.counterparty,
            "related_asset": self.related_asset,
            "tags": ", ".join(self.tags),
            "case_id": self.case_id,
            "extraction_method": self.extraction_method,
            "ocr_needed": self.ocr_needed,
            "warning": self.warning,
            "due_date_count": self.due_date_count,
            "duplicate_document_id": self.duplicate_document_id,
            "review_document_id": self.review_document_id,
            "probable_duplicates": self.probable_duplicates or [],
        }


def scandocu_root(vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> Path:
    return vault_dir / SCANDOCU_ROOT_NAME


def scandocu_processing_dir(vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> Path:
    return scandocu_root(vault_dir) / "processing"


def scandocu_actions_path(vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> Path:
    return vault_dir / "index" / SCANDOCU_ACTIONS_FILE


def domain_registry_path(vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> Path:
    return vault_dir / "index" / SCANDOCU_DOMAIN_REGISTRY_FILE


def read_domain_registry(vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> dict[str, Any]:
    path = domain_registry_path(vault_dir)
    if not path.exists():
        return {"domains": []}
    data = read_json_file(path)
    if not isinstance(data.get("domains"), list):
        return {"domains": []}
    return data


def registered_document_domains(vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> list[dict[str, str]]:
    domains: dict[str, str] = {value: value for value in SCANDOCU_BUILTIN_DOMAINS}
    for item in read_domain_registry(vault_dir).get("domains", []):
        if not isinstance(item, dict):
            continue
        value = normalize_domain(str(item.get("value", "")))
        if value:
            domains[value] = safe_text(str(item.get("label", ""))) or value
    for row in read_jsonl(vault_dir / "index" / "documents_index.jsonl"):
        value = normalize_domain(str(row.get("domain", "")))
        if value:
            domains.setdefault(value, value)
    return [{"value": value, "label": domains[value]} for value in sorted(domains)]


def register_document_domain(raw_domain: str, vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> str:
    value = normalize_domain(raw_domain)
    if not value or value in {"other", *SCANDOCU_BUILTIN_DOMAINS}:
        return value
    label = safe_text(raw_domain).strip() or value
    path = domain_registry_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    registry = read_domain_registry(vault_dir)
    now = now_iso()
    domains = registry.setdefault("domains", [])
    for item in domains:
        if not isinstance(item, dict):
            continue
        if normalize_domain(str(item.get("value", ""))) == value:
            item["value"] = value
            if safe_text(str(item.get("label", ""))) in {"", value} and label != value:
                item["label"] = label
            item["updated_at"] = now
            write_json(path, registry)
            return value
    domains.append({"value": value, "label": label, "created_at": now, "updated_at": now})
    write_json(path, registry)
    return value


def scan_downloads_for_pdfs(
    downloads_dir: Path = DEFAULT_DOWNLOADS_DIR,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 50,
    max_age_days: int | None = DEFAULT_DOWNLOADS_MAX_AGE_DAYS,
) -> list[dict[str, Any]]:
    downloads = downloads_dir.expanduser().resolve()
    if not downloads.exists() or not downloads.is_dir():
        raise ValueError(f"Downloads slozka neexistuje nebo neni slozka: {downloads}")
    rows: list[dict[str, Any]] = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days) if max_age_days is not None else None
    paths = sorted(downloads.glob("*.pdf"), key=lambda item: item.stat().st_mtime, reverse=True)
    for path in paths:
        if cutoff is not None and datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) < cutoff:
            continue
        try:
            validate_source_file(path)
            digest = sha256_file(path)
        except ValueError as exc:
            rows.append(
                {
                    "name": path.name,
                    "path": str(path),
                    "size_bytes": path.stat().st_size if path.exists() else 0,
                    "modified_at": format_mtime(path),
                    "status": "invalid",
                    "warning": str(exc),
                }
            )
            continue
        duplicate = find_duplicate_by_sha(vault_dir=vault_dir, sha256=digest)
        item = {
            "name": path.name,
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "modified_at": format_mtime(path),
            "status": "already_in_vault" if duplicate else classify_download_pdf_status(vault_dir=vault_dir, sha256=digest),
            "sha256": digest,
        }
        if duplicate:
            item["duplicate_document_id"] = safe_text(str(duplicate.get("document_id", "")))
        rows.append(item)
        if len(rows) >= limit:
            break
    return rows


def search_downloads_for_pdfs(
    query: str = "",
    modified_date: str = "",
    downloads_dir: Path = DEFAULT_DOWNLOADS_DIR,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 30,
) -> list[dict[str, Any]]:
    downloads = downloads_dir.expanduser().resolve()
    if not downloads.exists() or not downloads.is_dir():
        raise ValueError(f"Downloads slozka neexistuje nebo neni slozka: {downloads}")
    query_terms = [term.casefold() for term in tokenize(query) if len(term) >= 2]
    target_date = parse_search_date(modified_date)
    rows: list[dict[str, Any]] = []
    for path in sorted(downloads.glob("*.pdf"), key=lambda item: item.stat().st_mtime, reverse=True):
        if query_terms and not all(term in path.name.casefold() for term in query_terms):
            continue
        if target_date is not None and local_modified_date(path) != target_date:
            continue
        try:
            validate_source_file(path)
            digest = sha256_file(path)
            duplicate = find_duplicate_by_sha(vault_dir=vault_dir, sha256=digest)
            status = "already_in_vault" if duplicate else classify_download_pdf_status(vault_dir=vault_dir, sha256=digest)
            warning = ""
        except ValueError as exc:
            digest = ""
            duplicate = None
            status = "invalid"
            warning = str(exc)
        item = {
            "name": path.name,
            "path": str(path),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "modified_at": format_mtime(path),
            "modified_date": local_modified_date(path).isoformat(),
            "status": status,
        }
        if digest:
            item["sha256"] = digest
        if duplicate:
            item["duplicate_document_id"] = safe_text(str(duplicate.get("document_id", "")))
        if warning:
            item["warning"] = warning
        rows.append(item)
        if len(rows) >= limit:
            break
    return rows


def parse_search_date(value: str) -> date | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        return date.fromisoformat(cleaned)
    except ValueError as exc:
        raise ValueError("Datum pro hledání zadej ve formátu YYYY-MM-DD.") from exc


def local_modified_date(path: Path) -> date:
    return datetime.fromtimestamp(path.stat().st_mtime).date()


def build_scandocu_token(prefix: str, stable_name: str, digest: str, limit: int = SCANDOCU_TOKEN_LIMIT) -> str:
    digest_part = safe_ascii_slug(digest[:12], default="", limit=12)
    prefix_part = safe_ascii_slug(prefix, default="pdf", limit=20)
    name_part = safe_slug(stable_name, default="", limit=max(20, limit))
    return safe_slug(
        f"{prefix_part}-{digest_part}-{name_part}",
        default=f"{prefix_part}-{digest_part}",
        limit=limit,
    ).strip("-")


def prepare_next_scandocu_pdf(
    downloads_dir: Path = DEFAULT_DOWNLOADS_DIR,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> ScanDocuCandidate | None:
    for item in scan_downloads_for_pdfs(downloads_dir=downloads_dir, vault_dir=vault_dir, limit=200):
        if item.get("status") != "new":
            continue
        return prepare_scandocu_candidate(
            source=Path(str(item["path"])),
            vault_dir=vault_dir,
        )
    return None


def prepare_specific_download_pdf(
    source_path: str,
    downloads_dir: Path = DEFAULT_DOWNLOADS_DIR,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> ScanDocuCandidate:
    downloads = downloads_dir.expanduser().resolve()
    source = Path(source_path).expanduser().resolve()
    if downloads not in source.parents:
        raise ValueError("Vybraný soubor není uvnitř povolené Downloads složky.")
    validate_source_file(source)
    digest = sha256_file(source)
    duplicate = find_duplicate_by_sha(vault_dir=vault_dir, sha256=digest)
    if duplicate:
        stored_path = PROJECT_ROOT / str(duplicate.get("stored_path", ""))
        if not stored_path.exists():
            raise ValueError("Dokument je v indexu, ale uložený soubor ve vaultu nebyl nalezen.")
        return prepare_stored_document_review_candidate(
            document_record=duplicate,
            stored_path=stored_path,
            vault_dir=vault_dir,
        )
    return prepare_scandocu_candidate(source=source, vault_dir=vault_dir)


def prepare_next_stored_document_review(
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> ScanDocuCandidate | None:
    reviewed = reviewed_document_ids(vault_dir)
    text_by_id = {
        str(row.get("document_id", "")): str(row.get("text", ""))
        for row in read_jsonl(vault_dir / "index" / "text_index.jsonl")
    }
    for item in read_jsonl(vault_dir / "index" / "documents_index.jsonl"):
        document_id = safe_slug(str(item.get("document_id", "")), default="", limit=140)
        if not document_id or document_id in reviewed:
            continue
        lifecycle_status = safe_text(str(item.get("lifecycle_status", "active") or "active")).casefold()
        if lifecycle_status in {"archived", "trashed"}:
            continue
        if not scandocu_document_needs_review(item, text_chars=len(text_by_id.get(document_id, ""))):
            continue
        stored_path = PROJECT_ROOT / str(item.get("stored_path", ""))
        if not stored_path.exists():
            continue
        return prepare_stored_document_review_candidate(
            document_record=item,
            stored_path=stored_path,
            vault_dir=vault_dir,
        )
    return None


def prepare_stored_document_review(
    document_ref: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> ScanDocuCandidate:
    """Prepare the exact stored document selected through its opaque reference."""

    resolved = resolve_stored_document_file(
        document_ref=document_ref,
        vault_dir=vault_dir,
    )
    if not resolved.get("ok"):
        raise ValueError(str(resolved.get("message") or "Dokument nebyl nalezen."))
    return prepare_stored_document_review_candidate(
        document_record=resolved["record"],
        stored_path=resolved["path"],
        vault_dir=vault_dir,
    )


def scandocu_document_needs_review(record: dict[str, Any], text_chars: int | None = None) -> bool:
    explicit = safe_slug(str(record.get("reading_status", "") or record.get("document_reading_status", "")), default="", limit=80)
    if explicit in {"ok", "unreadable", "superseded"}:
        return False
    if explicit in {"needs_review", "k-revizi", "k_revizi", "revize"}:
        return True
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
    return int(indexed_chars or 0) == 0


def reviewed_document_ids(vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> set[str]:
    ids: set[str] = set()
    for row in read_jsonl(scandocu_actions_path(vault_dir)):
        if row.get("action") in {"reviewed", "review_skipped"}:
            document_id = safe_slug(str(row.get("document_id", "")), default="", limit=140)
            if document_id:
                ids.add(document_id)
    status_actions_path = vault_dir / "index" / "document_reading_status_actions.jsonl"
    for row in read_jsonl(status_actions_path):
        if row.get("action") != "set_reading_status":
            continue
        document_id = safe_slug(str(row.get("document_id", "")), default="", limit=140)
        if not document_id:
            continue
        status = safe_slug(str(row.get("reading_status", "")), default="", limit=80)
        if status in {"needs_review", "k-revizi", "k_revizi", "revize"}:
            ids.discard(document_id)
        elif status in {"ok", "unreadable", "superseded"}:
            ids.add(document_id)
    return ids


def get_scandocu_candidate(token: str, vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> ScanDocuCandidate:
    token = safe_slug(token, default="", limit=SCANDOCU_TOKEN_LIMIT)
    if not token:
        raise ValueError("chybi token dokumentu.")
    metadata_path = scandocu_processing_dir(vault_dir) / token / "candidate.json"
    if not metadata_path.exists():
        metadata_path = find_scandocu_candidate_metadata_path(token, vault_dir)
    if not metadata_path.exists():
        raise ValueError("ScanDocu kandidat nebyl nalezen.")
    data = read_json_file(metadata_path)
    return candidate_from_record(data, metadata_path=metadata_path)


def suggest_scandocu_candidate_metadata_with_ai(
    token: str,
    *,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    analyzer=request_codex_metadata_suggestion,
) -> dict[str, Any]:
    """Return a read-only AI comparison for one manually selected candidate."""

    candidate = get_scandocu_candidate(token=token, vault_dir=vault_dir)
    extraction = extract_text(candidate.working_path)
    current_metadata = {
        "title": candidate.title,
        "domain": candidate.domain,
        "document_type": candidate.document_type,
        "counterparty": candidate.counterparty,
        "related_asset": candidate.related_asset,
        "tags": list(candidate.tags),
    }
    domains = [
        str(item.get("value", ""))
        for item in registered_document_domains(vault_dir=vault_dir)
        if isinstance(item, dict) and str(item.get("value", "")).strip()
    ]
    return analyzer(
        source_name=candidate.source_path.name,
        source_text=extraction.text,
        current_metadata=current_metadata,
        allowed_domains=domains,
    )


def find_scandocu_candidate_metadata_path(token: str, vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> Path:
    processing_dir = scandocu_processing_dir(vault_dir)
    for candidate_path in processing_dir.glob("*/candidate.json"):
        try:
            data = read_json_file(candidate_path)
        except (OSError, json.JSONDecodeError):
            continue
        record_token = safe_slug(str(data.get("token", "")), default="", limit=SCANDOCU_TOKEN_LIMIT)
        dir_token = safe_slug(candidate_path.parent.name, default="", limit=SCANDOCU_TOKEN_LIMIT)
        if token in {record_token, dir_token}:
            return candidate_path
    return processing_dir / token / "candidate.json"


def can_reuse_scandocu_candidate(record: dict[str, Any]) -> bool:
    if record.get("classifier_version") != SCANDOCU_CLASSIFIER_VERSION:
        return False
    extraction_method = str(record.get("extraction_method", ""))
    if extraction_method == "pdf-no-text" or extraction_method.startswith("macos-vision-ocr"):
        return record.get("extractor_retry_version") == SCANDOCU_EXTRACTOR_RETRY_VERSION
    return True


def prepare_scandocu_candidate(source: Path, vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> ScanDocuCandidate:
    source = source.expanduser().resolve()
    if source.suffix.casefold() != ".pdf":
        raise ValueError("ScanDocu umi v teto fazi zpracovat jen PDF soubory.")
    validate_source_file(source)
    digest = sha256_file(source)
    token = build_scandocu_token("pdf", source.stem, digest, limit=64)
    target_dir = scandocu_processing_dir(vault_dir) / token
    metadata_path = target_dir / "candidate.json"
    if metadata_path.exists():
        existing = read_json_file(metadata_path)
        if can_reuse_scandocu_candidate(existing):
            return candidate_from_record(existing, metadata_path=metadata_path)

    target_dir.mkdir(parents=True, exist_ok=True)
    working_path = target_dir / safe_filename(source.name)
    if not working_path.exists():
        shutil.copy2(source, working_path)
    extraction = extract_text(working_path)
    metadata = propose_metadata(source=working_path, text=extraction.text)
    due_dates = find_due_date_candidates(extraction.text)
    duplicate = find_duplicate_by_sha(vault_dir=vault_dir, sha256=digest)
    suggested_title = suggest_document_title(source=source, metadata=metadata)
    probable_duplicates = find_probable_duplicate_documents(
        vault_dir=vault_dir,
        source=source,
        text=extraction.text,
        metadata=metadata,
    )
    record = {
        "schema_version": "1",
        "classifier_version": SCANDOCU_CLASSIFIER_VERSION,
        "extractor_retry_version": SCANDOCU_EXTRACTOR_RETRY_VERSION,
        "token": token,
        "status": "prepared",
        "prepared_at": now_iso(),
        "source_path": str(source),
        "source_name": source.name,
        "source_sha256": digest,
        "source_modified_at": format_mtime(source),
        "working_path": str(relative_to_project(working_path)),
        "title": suggested_title,
        "domain": metadata.get("domain", "other"),
        "document_type": metadata.get("document_type", "document"),
        "counterparty": metadata.get("counterparty", ""),
        "related_asset": metadata.get("related_asset", ""),
        "tags": metadata.get("tags", []),
        "case_id": "",
        "extraction_method": extraction.method,
        "ocr_needed": extraction.ocr_needed,
        "warning": extraction.warning,
        "due_date_count": len(due_dates),
        "duplicate_document_id": str(duplicate.get("document_id", "")) if duplicate else "",
        "probable_duplicates": probable_duplicates,
        "source_preserved": True,
        "do_not_commit": True,
    }
    write_json(metadata_path, record)
    append_jsonl(vault_dir / "index" / "scandocu_candidates.jsonl", record)
    return candidate_from_record(record, metadata_path=metadata_path)


def prepare_stored_document_review_candidate(
    document_record: dict[str, Any],
    stored_path: Path,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> ScanDocuCandidate:
    validate_source_file(stored_path)
    digest = sha256_file(stored_path)
    document_id = safe_slug(str(document_record.get("document_id", "")), default=f"doc-{digest[:8]}", limit=140)
    token = build_scandocu_token("review", document_id, digest, limit=SCANDOCU_TOKEN_LIMIT)
    target_dir = scandocu_processing_dir(vault_dir) / token
    metadata_path = target_dir / "candidate.json"
    if metadata_path.exists():
        existing = read_json_file(metadata_path)
        if can_reuse_scandocu_candidate(existing):
            return candidate_from_record(existing, metadata_path=metadata_path)

    target_dir.mkdir(parents=True, exist_ok=True)
    working_path = target_dir / safe_filename(stored_path.name)
    if not working_path.exists():
        shutil.copy2(stored_path, working_path)
    extraction = extract_text(working_path)
    metadata = propose_metadata(source=working_path, text=extraction.text)
    due_dates = find_due_date_candidates(extraction.text)
    current_tags = [str(tag) for tag in document_record.get("tags", []) if isinstance(tag, str)]
    suggested_tags = metadata.get("tags", [])
    if not isinstance(suggested_tags, list):
        suggested_tags = []
    record = {
        "schema_version": "1",
        "classifier_version": SCANDOCU_CLASSIFIER_VERSION,
        "extractor_retry_version": SCANDOCU_EXTRACTOR_RETRY_VERSION,
        "source_mode": "vault_review",
        "token": token,
        "status": "prepared",
        "prepared_at": now_iso(),
        "review_document_id": document_id,
        "source_path": str(stored_path),
        "source_name": stored_path.name,
        "source_sha256": digest,
        "source_modified_at": format_mtime(stored_path),
        "working_path": str(relative_to_project(working_path)),
        "title": safe_text(str(document_record.get("title", ""))) or suggest_document_title(stored_path, metadata),
        "domain": metadata.get("domain") or document_record.get("domain", "other"),
        "document_type": metadata.get("document_type") or document_record.get("document_type", "document"),
        "counterparty": metadata.get("counterparty") or document_record.get("counterparty", ""),
        "related_asset": metadata.get("related_asset") or document_record.get("related_asset", ""),
        "tags": merge_tags(current_tags, [str(tag) for tag in suggested_tags]),
        "case_id": safe_slug(str(document_record.get("case_id", "")), default="", limit=100),
        "extraction_method": extraction.method,
        "ocr_needed": extraction.ocr_needed,
        "warning": extraction.warning,
        "due_date_count": len(due_dates),
        "duplicate_document_id": "",
        "probable_duplicates": [],
        "source_preserved": True,
        "do_not_commit": True,
    }
    write_json(metadata_path, record)
    append_jsonl(vault_dir / "index" / "scandocu_review_candidates.jsonl", record)
    return candidate_from_record(record, metadata_path=metadata_path)


def import_scandocu_candidate(
    token: str,
    title: str,
    domain: str,
    document_type: str,
    counterparty: str = "",
    related_asset: str = "",
    tags: str = "",
    case_id: str = "",
    allow_probable_duplicate: bool = False,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> dict[str, Any]:
    candidate = get_scandocu_candidate(token=token, vault_dir=vault_dir)
    if candidate.source_mode == "vault_review":
        return update_reviewed_document_metadata(
            candidate=candidate,
            title=title,
            domain=domain,
            document_type=document_type,
            counterparty=counterparty,
            related_asset=related_asset,
            tags=tags,
            case_id=case_id,
            vault_dir=vault_dir,
        )
    if candidate.duplicate_document_id:
        append_scandocu_action(
            vault_dir=vault_dir,
            action="duplicate",
            token=candidate.token,
            source_path=candidate.source_path,
            source_sha256=sha256_file(candidate.working_path),
            document_id=candidate.duplicate_document_id,
        )
        return {
            "status": "duplicate",
            "document_id": candidate.duplicate_document_id,
            "message": "Dokument se stejnym obsahem uz je ve vaultu.",
        }
    probable_duplicates = candidate.probable_duplicates or []
    if probable_duplicates and not allow_probable_duplicate:
        return {
            "status": "probable_duplicate",
            "message": "Tento dokument je pravdepodobne uz ulozeny. Potvrd ve ScanDocu volbu `Presto ulozit`.",
            "probable_duplicates": probable_duplicates,
        }

    final_title = safe_text(title) or candidate.title
    final_domain = normalize_domain(domain or candidate.domain)
    register_document_domain(domain or candidate.domain, vault_dir=vault_dir)
    final_type = safe_ascii_slug(document_type or candidate.document_type, default="document", limit=50)
    final_tags = ", ".join(
        merge_tags(
            parse_tags(tags),
            candidate.tags,
        )
    )
    final_case_id = safe_ascii_slug(case_id, default="", limit=100) if case_id else ""
    document_id = safe_slug(final_title, default="", limit=100)
    consistency_conflicts = find_import_consistency_conflicts(
        candidate=candidate,
        final_title=final_title,
        final_domain=final_domain,
        final_type=final_type,
        counterparty=counterparty or candidate.counterparty,
        related_asset=related_asset or candidate.related_asset,
        tags=final_tags,
        document_id=document_id,
        vault_dir=vault_dir,
    )
    if consistency_conflicts and not allow_probable_duplicate:
        return {
            "status": "consistency_conflict",
            "message": (
                "Dokument věcně koliduje s již uloženým pojištěním pro stejné vozidlo "
                "a stejné období. Zkontroluj konflikty a potvrď `Přesto uložit`, pokud má jít o další platný dokument."
            ),
            "consistency_conflicts": consistency_conflicts,
        }
    result = apply_document_import_file(
        source_path=str(candidate.working_path),
        target_domain=final_domain,
        document_type=final_type,
        counterparty=counterparty,
        related_asset=related_asset,
        tags=final_tags,
        document_id=document_id,
        case_id=final_case_id,
        document_title=final_title,
        vault_dir=vault_dir,
    )
    update_scandocu_candidate_status(
        candidate=candidate,
        status="imported",
        document_id=result.document_id,
        domain=final_domain,
        document_type=final_type,
        title=final_title,
        case_id=final_case_id,
        vault_dir=vault_dir,
    )
    append_scandocu_action(
        vault_dir=vault_dir,
        action="imported",
        token=candidate.token,
        source_path=candidate.source_path,
        source_sha256=sha256_file(candidate.working_path),
        document_id=result.document_id,
    )
    skipped_variants = mark_resolved_download_variants_skipped(
        candidate=candidate,
        document_id=result.document_id,
        vault_dir=vault_dir,
    )
    return {
        "status": "imported" if result.created else "duplicate",
        "document_id": result.document_id,
        "created": result.created,
        "domain": final_domain,
        "stored_path": str(relative_to_project(result.destination)),
        "manifest_path": str(relative_to_project(result.manifest)),
        "message": result.message,
        "skipped_related_download_variants": skipped_variants,
    }


def find_import_consistency_conflicts(
    *,
    candidate: ScanDocuCandidate,
    final_title: str,
    final_domain: str,
    final_type: str,
    counterparty: str,
    related_asset: str,
    tags: str,
    document_id: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> list[dict[str, Any]]:
    if final_domain not in {"insurance", "car"}:
        return []

    extraction = extract_text(candidate.working_path)
    candidate_fact = document_row_to_fact(
        row={
            "document_id": f"pending:{candidate.token}",
            "title": final_title,
            "original_filename": candidate.source_path.name,
            "domain": final_domain,
            "document_type": final_type,
            "counterparty": counterparty,
            "related_asset": related_asset,
            "tags": parse_tags(tags),
        },
        text=extraction.text,
    )
    if candidate_fact is None or not candidate_fact.asset_key or not candidate_fact.coverage_start:
        return []

    matches = [
        item
        for item in existing_insurance_auto_document_facts(vault_dir=vault_dir)
        if item.asset_key == candidate_fact.asset_key
        and item.coverage_start == candidate_fact.coverage_start
        and item.amounts
    ]
    risky_matches = [item for item in matches if import_fact_is_materially_distinct(candidate_fact, item)]
    if not risky_matches:
        return []

    items = [candidate_fact, *risky_matches]
    return [
        {
            "severity": "warning",
            "code": "insurance_auto_existing_same_asset_period",
            "title": f"Ve vaultu už je pojistný dokument pro {best_asset_label(items)}",
            "message": (
                "Stejné vozidlo a stejný začátek krytí už mají ve vaultu jiný pojistný dokument. "
                "Před uložením porovnat smlouvu/návrh, částku a pojistitele."
            ),
            "asset": best_asset_label(items),
            "coverage_start": candidate_fact.coverage_start,
            "document_id": document_id,
            "items": import_consistency_items(items),
        }
    ]


def existing_insurance_auto_document_facts(vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> list[AuditFact]:
    text_by_id = {
        str(item.get("document_id", "")): str(item.get("text", ""))
        for item in read_jsonl(vault_dir / "index" / "text_index.jsonl")
    }
    facts: list[AuditFact] = []
    for row in read_jsonl(vault_dir / "index" / "documents_index.jsonl"):
        fact = document_row_to_fact(row=row, text=text_by_id.get(str(row.get("document_id", "")), ""))
        if fact is not None:
            facts.append(fact)
    return facts


def import_fact_is_materially_distinct(candidate: AuditFact, existing: AuditFact) -> bool:
    candidate_numbers = set(candidate.policy_numbers)
    existing_numbers = set(existing.policy_numbers)
    if candidate_numbers and existing_numbers and candidate_numbers == existing_numbers:
        return False
    if candidate_numbers and existing_numbers and candidate_numbers.isdisjoint(existing_numbers):
        return True
    candidate_amount = primary_amount(candidate)
    existing_amount = primary_amount(existing)
    if candidate_amount and existing_amount and candidate_amount != existing_amount:
        return True
    return not candidate_numbers or not existing_numbers


def import_consistency_items(items: list[AuditFact]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for item in items:
        result.append(
            {
                "source_type": "pending_import" if item.source_id.startswith("pending:") else item.source_type,
                "source_id": safe_text(item.source_id),
                "label": safe_text(item.title),
                "amount": primary_amount(item),
                "coverage_start": item.coverage_start,
                "insurer": item.insurer,
                "policy_numbers": ", ".join(item.policy_numbers),
            }
        )
    return result


def mark_resolved_download_variants_skipped(
    candidate: ScanDocuCandidate,
    document_id: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> list[str]:
    source = candidate.source_path.expanduser()
    if not source.exists() or not source.parent.exists():
        return []
    base_key = downloads_variant_key(source)
    if not base_key:
        return []
    existing_actions = read_jsonl(scandocu_actions_path(vault_dir))
    skipped: list[str] = []
    for sibling in source.parent.glob("*.pdf"):
        if sibling.resolve() == source.resolve():
            continue
        if downloads_variant_key(sibling) != base_key:
            continue
        try:
            digest = sha256_file(sibling)
        except OSError:
            continue
        if find_duplicate_by_sha(vault_dir=vault_dir, sha256=digest):
            continue
        if any(row.get("source_sha256") == digest for row in existing_actions):
            continue
        token = build_scandocu_token("pdf", sibling.stem, digest, limit=64)
        append_scandocu_action(
            vault_dir=vault_dir,
            action="skipped",
            token=token,
            source_path=sibling,
            source_sha256=digest,
            document_id=document_id,
        )
        skipped.append(sibling.name)
    return skipped


def downloads_variant_key(path: Path) -> str:
    stem = path.stem.casefold()
    stem = unicodedata.normalize("NFKD", stem)
    stem = "".join(char for char in stem if not unicodedata.combining(char))
    parts = [part for part in re.split(r"[^a-z0-9]+", stem) if part]
    ignored = {"odemknute", "odemceno", "odemceny", "unlocked", "decrypted", "kopie", "copy"}
    useful = [part for part in parts if part not in ignored and not re.fullmatch(r"[a-f0-9]{8,}", part)]
    return "-".join(useful)


def update_reviewed_document_metadata(
    candidate: ScanDocuCandidate,
    title: str,
    domain: str,
    document_type: str,
    counterparty: str,
    related_asset: str,
    tags: str,
    case_id: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> dict[str, Any]:
    document_id = safe_slug(candidate.review_document_id, default="", limit=140)
    if not document_id:
        raise ValueError("review kandidat nema document_id.")
    final_title = safe_text(title) or candidate.title
    final_domain = normalize_domain(domain or candidate.domain)
    final_document_type = safe_ascii_slug(
        document_type or candidate.document_type,
        default="document",
        limit=50,
    )
    final_counterparty = safe_text(counterparty)
    final_related_asset = safe_text(related_asset)
    final_case_id = safe_ascii_slug(case_id, default="", limit=100) if case_id else ""
    final_tags = merge_tags(parse_tags(tags), [])
    reviewed_at = now_iso()
    source_sha256 = sha256_file(candidate.working_path)
    register_document_domain(domain or candidate.domain, vault_dir=vault_dir)

    def select_document(rows: list[dict[str, Any]], reference: str) -> int | None:
        return next(
            (index for index, row in enumerate(rows) if str(row.get("document_id", "")) == reference),
            None,
        )

    def manifest_path_for(current: dict[str, Any]) -> Path | None:
        stored_path_value = str(current.get("stored_path", "") or "")
        return (PROJECT_ROOT / stored_path_value).parent / "manifest.json" if stored_path_value else None

    def build_mutation(
        current: dict[str, Any],
        manifest: dict[str, Any] | None,
    ) -> DocumentRecordMutation:
        updated = {**current, **(manifest or {})}
        updated["title"] = final_title
        updated["domain"] = final_domain
        updated["document_type"] = final_document_type
        updated["counterparty"] = final_counterparty
        updated["related_asset"] = final_related_asset
        updated["case_id"] = final_case_id
        updated["tags"] = final_tags
        updated["reviewed_at"] = reviewed_at
        updated["review_source"] = "scandocu_vault_review"
        updated["reading_status"] = "ok"
        updated["reading_status_updated_at"] = reviewed_at
        updated["reading_status_note"] = "Potvrzeno revizí ve ScanDocu."
        candidate_status = build_scandocu_candidate_status_record(
            candidate=candidate,
            status="reviewed",
            document_id=document_id,
            domain=final_domain,
            document_type=final_document_type,
            title=final_title,
            case_id=final_case_id,
            updated_at=reviewed_at,
        )
        return DocumentRecordMutation(
            index_record=updated,
            manifest_record=updated,
            audit_record={
                "action": "reviewed",
                "action_at": reviewed_at,
                "token": candidate.token,
                "source_name": candidate.source_path.name,
                "source_path": str(candidate.source_path),
                "source_sha256": source_sha256,
                "document_id": document_id,
                "do_not_commit": True,
            },
            related_json_files=(
                DocumentRelatedJsonMutation(path=candidate.metadata_path, record=candidate_status),
            ),
        )

    try:
        transaction = transact_document_record(
            vault_dir=vault_dir,
            reference=document_id,
            row_selector=select_document,
            manifest_path_resolver=manifest_path_for,
            mutation_builder=build_mutation,
            audit_path=scandocu_actions_path(vault_dir),
            backup_group="review_backups",
            backup_path_labeler=lambda path: str(relative_to_project(path)),
            allow_manifest_create=True,
        )
    except DocumentRecordNotFoundError as exc:
        raise ValueError("puvodni dokument nebyl nalezen v indexu.") from exc
    except DocumentTransactionError as exc:
        raise OSError("Revizi dokumentu se nepodařilo bezpečně uložit.") from exc

    updated = transaction.updated_record
    stored_path = PROJECT_ROOT / str(updated.get("stored_path", ""))
    manifest_path = stored_path.parent / "manifest.json"
    return {
        "status": "reviewed",
        "document_id": document_id,
        "domain": updated["domain"],
        "stored_path": str(relative_to_project(stored_path)),
        "manifest_path": str(relative_to_project(manifest_path)),
        "backup_dir": str(relative_to_project(transaction.backup_dir)) if transaction.backup_dir else "",
        "message": "Metadata existujiciho dokumentu byla potvrzene aktualizovana.",
    }


def skip_scandocu_candidate(
    token: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> dict[str, Any]:
    candidate = get_scandocu_candidate(token=token, vault_dir=vault_dir)
    is_review = candidate.source_mode == "vault_review"
    update_scandocu_candidate_status(
        candidate=candidate,
        status="review_skipped" if is_review else "skipped",
        document_id=candidate.review_document_id if is_review else "",
        domain=candidate.domain,
        document_type=candidate.document_type,
        title=candidate.title,
        case_id=candidate.case_id,
        vault_dir=vault_dir,
    )
    append_scandocu_action(
        vault_dir=vault_dir,
        action="review_skipped" if is_review else "skipped",
        token=candidate.token,
        source_path=candidate.source_path,
        source_sha256=sha256_file(candidate.working_path),
        document_id=candidate.review_document_id if is_review else "",
    )
    return {"status": "review_skipped" if is_review else "skipped", "message": "Dokument byl pro tuto frontu preskocen."}


def classify_download_pdf_status(vault_dir: Path, sha256: str) -> str:
    if find_duplicate_by_sha(vault_dir=vault_dir, sha256=sha256):
        return "already_in_vault"
    for row in reversed(read_jsonl(scandocu_actions_path(vault_dir))):
        if row.get("source_sha256") == sha256 and row.get("action") in {"imported", "skipped", "duplicate"}:
            return str(row.get("action"))
    return "new"


def find_probable_duplicate_documents(
    vault_dir: Path,
    source: Path,
    text: str,
    metadata: dict[str, Any],
    limit: int = 3,
) -> list[dict[str, Any]]:
    documents = read_jsonl(vault_dir / "index" / "documents_index.jsonl")
    if not documents:
        return []
    text_by_id = {
        str(row.get("document_id", "")): str(row.get("text", ""))
        for row in read_jsonl(vault_dir / "index" / "text_index.jsonl")
    }
    query_terms = build_duplicate_query_terms(source=source, text=text, metadata=metadata)
    if not query_terms:
        return []

    important_terms = important_duplicate_terms(source, text)
    scored: list[tuple[int, dict[str, Any], list[str]]] = []
    for item in documents:
        document_id = str(item.get("document_id", ""))
        haystack = " ".join(
            [
                str(item.get("document_id", "")),
                str(item.get("title", "")),
                str(item.get("original_filename", "")),
                str(item.get("stored_path", "")),
                str(item.get("domain", "")),
                str(item.get("document_type", "")),
                str(item.get("counterparty", "")),
                str(item.get("related_asset", "")),
                " ".join(str(tag) for tag in item.get("tags", []) if isinstance(tag, str)),
                text_by_id.get(document_id, ""),
            ]
        )
        haystack_terms = {normalize_duplicate_term(term) for term in tokenize(haystack) if normalize_duplicate_term(term)}
        matched = [term for term in query_terms if term in haystack_terms]
        if not matched:
            continue
        important_matches = [term for term in matched if term in important_terms]
        if not important_matches:
            continue
        if len(important_matches) < 2 and len(matched) < 3:
            continue
        score = len(matched) + (len(important_matches) * 3)
        if score < 8:
            continue
        scored.append((score, item, matched[:8]))

    results: list[dict[str, Any]] = []
    for score, item, matched in sorted(scored, key=lambda row: row[0], reverse=True)[:limit]:
        results.append(
            {
                "document_id": safe_text(str(item.get("document_id", ""))),
                "title": safe_text(str(item.get("title", ""))),
                "original_filename": safe_text(str(item.get("original_filename", ""))),
                "stored_path": safe_text(str(item.get("stored_path", ""))),
                "domain": safe_text(str(item.get("domain", ""))),
                "document_type": safe_text(str(item.get("document_type", ""))),
                "score": score,
                "matched_terms": matched,
            }
        )
    return results


def build_duplicate_query_terms(source: Path, text: str, metadata: dict[str, Any]) -> list[str]:
    raw = " ".join(
        [
            source.stem,
            split_camel_case(source.stem),
            str(metadata.get("document_type", "")),
            str(metadata.get("domain", "")),
            str(metadata.get("counterparty", "")),
            str(metadata.get("related_asset", "")),
            text[:3000],
        ]
    )
    terms = []
    for term in tokenize(raw):
        cleaned = normalize_duplicate_term(term)
        if not is_duplicate_signal_term(cleaned):
            continue
        terms.append(cleaned)
    return list(dict.fromkeys(terms))[:80]


def important_duplicate_terms(source: Path, text: str) -> set[str]:
    del text
    raw = f"{source.stem} {split_camel_case(source.stem)}"
    return {
        normalize_duplicate_term(term)
        for term in tokenize(raw)
        if is_duplicate_signal_term(normalize_duplicate_term(term), min_len=4)
    }


def split_camel_case(value: str) -> str:
    return re.sub(r"(?<=[a-zá-ž])(?=[A-ZÁ-Ž])", " ", value)


def normalize_duplicate_term(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.casefold())
    ascii_value = "".join(char for char in folded if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9_.-]+", "-", ascii_value).strip("-")[:80]


def is_duplicate_signal_term(value: str, min_len: int = 4) -> bool:
    if len(value) < min_len:
        return False
    if value.isdigit():
        return False
    return value not in DUPLICATE_STOPWORDS


def normalize_probable_duplicates(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "document_id": safe_text(str(item.get("document_id", ""))),
                "title": safe_text(str(item.get("title", ""))),
                "original_filename": safe_text(str(item.get("original_filename", ""))),
                "stored_path": safe_text(str(item.get("stored_path", ""))),
                "domain": safe_text(str(item.get("domain", ""))),
                "document_type": safe_text(str(item.get("document_type", ""))),
                "score": int(item.get("score", 0) or 0),
                "matched_terms": [
                    normalize_duplicate_term(str(term))
                    for term in item.get("matched_terms", [])
                    if normalize_duplicate_term(str(term))
                ][:8],
            }
        )
    return normalized


DUPLICATE_STOPWORDS = {
    "dokument",
    "document",
    "smlouva",
    "smlouvy",
    "smlouvu",
    "smlouve",
    "contract",
    "najem",
    "najemni",
    "strana",
    "page",
    "datum",
    "podpis",
    "priloha",
    "příloha",
    "adresa",
    "ulice",
    "jmeno",
    "prijmeni",
    "rodne",
    "cislo",
    "trvaleho",
    "pobytu",
    "sidla",
    "narozeni",
    "miloslav",
    "falta",
    "praha",
    "ceska",
    "republika",
    "other",
    "download",
    "scan",
    "pdf",
}


def candidate_from_record(data: dict[str, Any], metadata_path: Path) -> ScanDocuCandidate:
    working_path = project_path_from_record_local(str(data.get("working_path", "")))
    tags = data.get("tags", [])
    if not isinstance(tags, list):
        tags = parse_tags(str(tags))
    return ScanDocuCandidate(
        source_mode=safe_slug(str(data.get("source_mode", "downloads_import")), default="downloads_import", limit=40),
        token=safe_slug(str(data.get("token", "")), default="", limit=SCANDOCU_TOKEN_LIMIT),
        source_path=Path(str(data.get("source_path", ""))).expanduser(),
        working_path=working_path,
        metadata_path=metadata_path,
        title=safe_text(str(data.get("title", ""))),
        domain=normalize_domain(str(data.get("domain", "other"))),
        document_type=safe_slug(str(data.get("document_type", "document")), default="document", limit=50),
        counterparty=safe_text(str(data.get("counterparty", ""))),
        related_asset=safe_text(str(data.get("related_asset", ""))),
        tags=[safe_slug(str(tag), default="", limit=60) for tag in tags if safe_slug(str(tag), default="", limit=60)],
        case_id=safe_slug(str(data.get("case_id", "")), default="", limit=100),
        extraction_method=safe_text(str(data.get("extraction_method", ""))),
        ocr_needed=bool(data.get("ocr_needed", False)),
        warning=safe_text(str(data.get("warning", ""))),
        due_date_count=int(data.get("due_date_count", 0) or 0),
        duplicate_document_id=safe_slug(str(data.get("duplicate_document_id", "")), default="", limit=140),
        review_document_id=safe_slug(str(data.get("review_document_id", "")), default="", limit=140),
        probable_duplicates=normalize_probable_duplicates(data.get("probable_duplicates", [])),
    )


def update_scandocu_candidate_status(
    candidate: ScanDocuCandidate,
    status: str,
    document_id: str,
    domain: str,
    document_type: str,
    title: str,
    case_id: str,
    vault_dir: Path,
) -> None:
    data = build_scandocu_candidate_status_record(
        candidate=candidate,
        status=status,
        document_id=document_id,
        domain=domain,
        document_type=document_type,
        title=title,
        case_id=case_id,
    )
    write_json(candidate.metadata_path, data)


def build_scandocu_candidate_status_record(
    *,
    candidate: ScanDocuCandidate,
    status: str,
    document_id: str,
    domain: str,
    document_type: str,
    title: str,
    case_id: str,
    updated_at: str = "",
) -> dict[str, Any]:
    data = read_json_file(candidate.metadata_path)
    data["status"] = status
    data["updated_at"] = updated_at or now_iso()
    data["final_document_id"] = document_id
    data["title"] = safe_text(title)
    data["domain"] = normalize_domain(domain)
    data["document_type"] = safe_ascii_slug(document_type, default="document", limit=50)
    data["case_id"] = safe_ascii_slug(case_id, default="", limit=100) if case_id else ""
    return data


def append_scandocu_action(
    vault_dir: Path,
    action: str,
    token: str,
    source_path: Path,
    source_sha256: str,
    document_id: str = "",
) -> None:
    append_jsonl(
        scandocu_actions_path(vault_dir),
        {
            "action": action,
            "action_at": now_iso(),
            "token": token,
            "source_name": source_path.name,
            "source_path": str(source_path),
            "source_sha256": source_sha256,
            "document_id": document_id,
            "do_not_commit": True,
        },
    )


def suggest_document_title(source: Path, metadata: dict[str, Any]) -> str:
    stem = source.stem.strip()
    doc_type = safe_text(str(metadata.get("document_type", "")))
    domain = safe_text(str(metadata.get("domain", "")))
    if stem and not stem.casefold().startswith(("scan", "document", "untitled", "download")):
        return safe_text(split_camel_case(stem))
    parts = [part for part in (domain, doc_type, datetime.now().date().isoformat()) if part]
    return " ".join(parts) or "Dokument"


def project_path_from_record_local(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def format_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class ScanDocuServer:
    def __init__(
        self,
        downloads_dir: Path = DEFAULT_DOWNLOADS_DIR,
        vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    ) -> None:
        self.downloads_dir = downloads_dir
        self.vault_dir = vault_dir

    def make_handler(self):
        app = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "ScanDocu/0.1"

            def do_GET(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                try:
                    if parsed.path == "/":
                        mode = parse_qs(parsed.query).get("mode", [""])[0]
                        self.respond_html(
                            SCANDOCU_ARCHIVE_HTML
                            if mode == "browse"
                            else SCANDOCU_HTML
                        )
                        return
                    if parsed.path == "/api/next":
                        params = parse_qs(parsed.query)
                        mode = params.get("mode", ["downloads"])[0]
                        if mode == "review":
                            document_ref = params.get("document_ref", [""])[0]
                            candidate = (
                                prepare_stored_document_review(
                                    document_ref=document_ref,
                                    vault_dir=app.vault_dir,
                                )
                                if document_ref
                                else prepare_next_stored_document_review(vault_dir=app.vault_dir)
                            )
                            not_found = "Ve vaultu neni dalsi ulozeny dokument k revizi."
                        else:
                            candidate = prepare_next_scandocu_pdf(
                                downloads_dir=app.downloads_dir,
                                vault_dir=app.vault_dir,
                            )
                            not_found = "V Downloads neni zadne nove PDF ke zpracovani."
                        if candidate is None:
                            self.respond_json({"found": False, "message": not_found})
                        else:
                            self.respond_json(candidate.to_api())
                        return
                    if parsed.path == "/api/list":
                        params = parse_qs(parsed.query)
                        max_age_days_value = params.get("max_age_days", [str(DEFAULT_DOWNLOADS_MAX_AGE_DAYS)])[0]
                        max_age_days = None if max_age_days_value == "all" else int(max_age_days_value)
                        self.respond_json(
                            {
                                "downloads_dir": str(app.downloads_dir),
                                "max_age_days": max_age_days,
                                "items": scan_downloads_for_pdfs(
                                    downloads_dir=app.downloads_dir,
                                    vault_dir=app.vault_dir,
                                    max_age_days=max_age_days,
                                ),
                            }
                        )
                        return
                    if parsed.path == "/api/domains":
                        self.respond_json({"domains": registered_document_domains(vault_dir=app.vault_dir)})
                        return
                    if parsed.path == "/api/documents":
                        params = parse_qs(parsed.query)
                        self.respond_json(
                            stored_document_list_status(
                                query=params.get("q", [""])[0],
                                domain=params.get("domain", [""])[0],
                                reading_status=params.get("reading_status", [""])[0],
                                vault_dir=app.vault_dir,
                            )
                        )
                        return
                    if parsed.path == "/api/document":
                        params = parse_qs(parsed.query)
                        self.respond_json(
                            stored_document_detail_status(
                                document_ref=params.get("document_ref", [""])[0],
                                vault_dir=app.vault_dir,
                            )
                        )
                        return
                    if parsed.path == "/api/search-downloads":
                        params = parse_qs(parsed.query)
                        self.respond_json(
                            {
                                "downloads_dir": str(app.downloads_dir),
                                "items": search_downloads_for_pdfs(
                                    query=params.get("q", [""])[0],
                                    modified_date=params.get("date", [""])[0],
                                    downloads_dir=app.downloads_dir,
                                    vault_dir=app.vault_dir,
                                ),
                            }
                        )
                        return
                    if parsed.path == "/vault/document":
                        params = parse_qs(parsed.query)
                        resolved = resolve_stored_document_file(
                            document_ref=params.get("document_ref", [""])[0],
                            vault_dir=app.vault_dir,
                        )
                        if not resolved.get("ok"):
                            raise ValueError(
                                str(resolved.get("message", "Dokument nebyl nalezen."))
                            )
                        path = resolved["path"]
                        extension = path.suffix.lower()
                        content_type = (
                            "application/pdf"
                            if extension == ".pdf"
                            else (
                                mimetypes.guess_type(path.name)[0]
                                or "application/octet-stream"
                            )
                        )
                        self.respond_vault_file(
                            path,
                            content_type,
                            as_attachment=(
                                extension != ".pdf"
                                and extension not in ARCHIVE_IMAGE_EXTENSIONS
                            ),
                        )
                        return
                    if parsed.path.startswith("/pdf/"):
                        token = parsed.path.rsplit("/", 1)[-1]
                        candidate = get_scandocu_candidate(token=token, vault_dir=app.vault_dir)
                        if candidate.working_path.suffix.lower() != ".pdf":
                            raise ValueError("Nahled v PDF ramecku je dostupny jen pro PDF dokumenty.")
                        self.respond_file(candidate.working_path, "application/pdf")
                        return
                    if parsed.path.startswith("/preview/"):
                        token = parsed.path.rsplit("/", 1)[-1]
                        candidate = get_scandocu_candidate(token=token, vault_dir=app.vault_dir)
                        extension = candidate.working_path.suffix.lower()
                        if extension == ".pdf":
                            self.respond_file(candidate.working_path, "application/pdf")
                            return
                        if extension not in SCANDOCU_IMAGE_PREVIEW_EXTENSIONS:
                            raise ValueError("Nahled je dostupny jen pro PDF nebo obrazkove dokumenty.")
                        content_type = mimetypes.guess_type(candidate.working_path.name)[0] or "application/octet-stream"
                        self.respond_file(candidate.working_path, content_type)
                        return
                    if parsed.path.startswith("/file/"):
                        token = parsed.path.rsplit("/", 1)[-1]
                        candidate = get_scandocu_candidate(token=token, vault_dir=app.vault_dir)
                        content_type = mimetypes.guess_type(candidate.working_path.name)[0] or "application/octet-stream"
                        self.respond_file(candidate.working_path, content_type, as_attachment=True)
                        return
                    self.respond_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)
                except ValueError as exc:
                    self.respond_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                except OSError as exc:
                    self.respond_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

            def do_POST(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                try:
                    payload = self.read_json()
                    if parsed.path == "/api/save":
                        result = import_scandocu_candidate(
                            token=str(payload.get("token", "")),
                            title=str(payload.get("title", "")),
                            domain=str(payload.get("domain", "")),
                            document_type=str(payload.get("document_type", "")),
                            counterparty=str(payload.get("counterparty", "")),
                            related_asset=str(payload.get("related_asset", "")),
                            tags=str(payload.get("tags", "")),
                            case_id=str(payload.get("case_id", "")),
                            allow_probable_duplicate=bool(payload.get("allow_probable_duplicate", False)),
                            vault_dir=app.vault_dir,
                        )
                        self.respond_json(result)
                        return
                    if parsed.path == "/api/ai-metadata":
                        self.respond_json(
                            suggest_scandocu_candidate_metadata_with_ai(
                                token=str(payload.get("token", "")),
                                vault_dir=app.vault_dir,
                            )
                        )
                        return
                    if parsed.path == "/api/skip":
                        self.respond_json(
                            skip_scandocu_candidate(
                                token=str(payload.get("token", "")),
                                vault_dir=app.vault_dir,
                            )
                        )
                        return
                    if parsed.path == "/api/select-download":
                        candidate = prepare_specific_download_pdf(
                            source_path=str(payload.get("source_path", "")),
                            downloads_dir=app.downloads_dir,
                            vault_dir=app.vault_dir,
                        )
                        self.respond_json(candidate.to_api())
                        return
                    self.respond_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)
                except ValueError as exc:
                    self.respond_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                except AIMetadataError as exc:
                    self.respond_json({"error": str(exc)}, status=HTTPStatus.SERVICE_UNAVAILABLE)
                except OSError as exc:
                    self.respond_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

            def read_json(self) -> dict[str, Any]:
                length = int(self.headers.get("Content-Length", "0") or "0")
                raw = self.rfile.read(length).decode("utf-8") if length else "{}"
                data = json.loads(raw or "{}")
                if not isinstance(data, dict):
                    raise ValueError("JSON payload musi byt objekt.")
                return data

            def respond_html(self, html: str, status: HTTPStatus = HTTPStatus.OK) -> None:
                payload = html.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def respond_json(self, data: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
                payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def respond_file(self, path: Path, content_type: str, as_attachment: bool = False) -> None:
                root = scandocu_processing_dir(app.vault_dir).resolve()
                resolved = path.resolve()
                if root not in resolved.parents:
                    raise ValueError("pozadovany soubor neni ve ScanDocu processing slozce.")
                self.respond_resolved_file(
                    resolved,
                    content_type,
                    as_attachment=as_attachment,
                )

            def respond_vault_file(
                self,
                path: Path,
                content_type: str,
                as_attachment: bool = False,
            ) -> None:
                root = app.vault_dir.resolve(strict=True)
                resolved = path.resolve(strict=True)
                if root not in resolved.parents:
                    raise ValueError("Pozadovany soubor neni v dokumentovem vaultu.")
                self.respond_resolved_file(
                    resolved,
                    content_type,
                    as_attachment=as_attachment,
                )

            def respond_resolved_file(
                self,
                resolved: Path,
                content_type: str,
                as_attachment: bool = False,
            ) -> None:
                payload = resolved.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(payload)))
                if as_attachment:
                    self.send_header(
                        "Content-Disposition",
                        f'attachment; filename="{safe_filename(resolved.name)}"',
                    )
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, format: str, *args: Any) -> None:
                return

        return Handler

    def serve(self, host: str = "127.0.0.1", port: int = 8765) -> None:
        server = ThreadingHTTPServer((host, port), self.make_handler())
        print(f"ScanDocu bezi na http://{host}:{port}", flush=True)
        server.serve_forever()


SCANDOCU_HTML = """<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ScanDocu</title>
  <style>
    :root { color-scheme: light; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin: 0; background: #f4f5f7; color: #1d2430; }
    header { padding: 14px 22px; background: #1f2937; color: white; display: flex; align-items: center; justify-content: space-between; }
    h1 { font-size: 20px; margin: 0; font-weight: 650; letter-spacing: 0; }
    main { display: grid; grid-template-columns: minmax(360px, 430px) minmax(0, 1fr); gap: 16px; padding: 16px; height: calc(100vh - 56px); box-sizing: border-box; }
    section { background: white; border: 1px solid #d9dee7; border-radius: 8px; overflow: hidden; }
    .panel { padding: 16px; overflow: auto; }
    label { display: block; margin: 12px 0 6px; font-size: 13px; font-weight: 650; color: #374151; }
    input, select, textarea { box-sizing: border-box; width: 100%; border: 1px solid #c8ced8; border-radius: 6px; padding: 10px 11px; font: inherit; background: white; color: #111827; }
    textarea { min-height: 72px; resize: vertical; }
    iframe { width: 100%; height: 100%; border: 0; background: #e5e7eb; }
    .preview-shell { height: 100%; min-height: 420px; }
    .image-preview-wrap { height: 100%; min-height: 420px; overflow: auto; background: #111827; display: grid; place-items: start center; padding: 14px; box-sizing: border-box; }
    .image-preview { max-width: 100%; height: auto; background: white; box-shadow: 0 18px 38px rgba(17, 24, 39, 0.34); }
    .preview-fallback { height: 100%; min-height: 420px; box-sizing: border-box; padding: 22px; background: #f9fafb; color: #1f2937; display: flex; align-items: center; justify-content: center; }
    .preview-card { max-width: 520px; display: grid; gap: 11px; }
    .preview-card h2 { margin: 0; font-size: 18px; letter-spacing: 0; }
    .preview-card p { margin: 0; color: #4b5563; line-height: 1.45; }
    .preview-download { justify-self: start; display: inline-block; border-radius: 6px; padding: 10px 13px; background: #2563eb; color: white; text-decoration: none; font-weight: 650; }
    .meta { display: grid; gap: 7px; margin: 10px 0 14px; font-size: 13px; color: #4b5563; }
    .meta strong { color: #111827; }
    .actions { display: flex; gap: 8px; margin-top: 16px; flex-wrap: wrap; }
    .completion-actions { display: flex; gap: 8px; margin: 10px 0 12px; flex-wrap: wrap; }
    .download-search { display: grid; gap: 8px; padding: 11px; margin-bottom: 12px; border: 1px solid #e5e7eb; border-radius: 8px; background: #f9fafb; }
    .download-search-grid { display: grid; grid-template-columns: minmax(0, 1fr) 145px auto; gap: 8px; align-items: end; }
    .download-search label { margin: 0 0 4px; }
    .download-results { display: grid; gap: 7px; }
    .download-result { border-top: 1px solid #e5e7eb; padding-top: 7px; display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 8px; align-items: center; font-size: 12px; }
    .download-result:first-child { border-top: 0; padding-top: 0; }
    .download-result-title { font-weight: 650; overflow-wrap: anywhere; }
    .download-result-meta { color: #6b7280; margin-top: 2px; overflow-wrap: anywhere; }
    .custom-domain-wrap { margin-top: 7px; }
    .field-help { margin-top: 5px; color: #6b7280; font-size: 12px; line-height: 1.35; }
    button { border: 0; border-radius: 6px; padding: 10px 13px; font: inherit; font-weight: 650; cursor: pointer; }
    button:disabled { cursor: wait; opacity: 0.65; }
    .primary { background: #2563eb; color: white; }
    .secondary { background: #e5e7eb; color: #111827; }
    .danger { background: #fee2e2; color: #991b1b; }
    .status { padding: 9px 11px; margin: 12px 0; border-radius: 6px; background: #eef2ff; color: #273070; font-size: 13px; }
    .duplicate-box { margin: 12px 0; padding: 11px; border-radius: 7px; background: #fff7ed; border: 1px solid #fed7aa; color: #7c2d12; font-size: 13px; }
    .duplicate-box ul { margin: 8px 0 0; padding-left: 18px; }
    .duplicate-box li { margin: 5px 0; overflow-wrap: anywhere; }
    .encrypted-box { margin: 12px 0; padding: 12px; border-radius: 7px; background: #fef2f2; border: 1px solid #fecaca; color: #7f1d1d; font-size: 13px; }
    .encrypted-box ol { margin: 8px 0 0; padding-left: 20px; }
    .encrypted-box li { margin: 5px 0; }
    .ai-box { margin: 12px 0; padding: 12px; border-radius: 7px; background: #eff6ff; border: 1px solid #bfdbfe; color: #1e3a8a; font-size: 13px; }
    .ai-box h2 { margin: 0 0 7px; font-size: 16px; }
    .ai-box p { margin: 5px 0; line-height: 1.4; }
    .ai-fields { display: grid; gap: 7px; margin: 10px 0; }
    .ai-field { padding-top: 7px; border-top: 1px solid #bfdbfe; }
    .ai-field:first-child { padding-top: 0; border-top: 0; }
    .ai-evidence { color: #475569; font-size: 12px; overflow-wrap: anywhere; }
    .ai-warning { color: #92400e; }
    .checkline { display: flex; gap: 8px; align-items: flex-start; margin-top: 10px; color: #7c2d12; font-weight: 650; }
    .checkline input { width: auto; margin-top: 3px; }
    .hidden { display: none; }
    @media (max-width: 860px) {
      main { grid-template-columns: 1fr; height: auto; }
      iframe { height: 72vh; }
      .preview-shell, .preview-fallback, .image-preview-wrap { min-height: 72vh; }
      .download-search-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <h1>ScanDocu</h1>
    <div class="actions" style="margin-top: 0;">
      <button class="secondary" id="cockpitBtn">Zpět do Cockpitu</button>
      <button class="secondary" id="archiveBtn">Uložené dokumenty</button>
      <button class="secondary" id="nextBtn">Další PDF</button>
    </div>
  </header>
  <main>
    <section class="panel">
      <div class="download-search">
        <div class="download-search-grid">
          <div>
            <label for="downloadQuery">Najít PDF v Downloads podle názvu</label>
            <input id="downloadQuery" autocomplete="off" placeholder="část názvu souboru">
          </div>
          <div>
            <label for="downloadDate">Datum</label>
            <input id="downloadDate" type="date">
          </div>
          <button class="secondary" id="downloadSearchBtn">Hledat</button>
        </div>
        <div id="downloadSearchStatus" class="status hidden"></div>
        <div id="downloadSearchResults" class="download-results"></div>
      </div>
      <div id="status" class="status">Načítám dokument...</div>
      <div id="completionActions" class="completion-actions hidden">
        <button class="primary" id="continueBtn">Ano, další dokument</button>
        <button class="secondary" id="searchAgainBtn">Hledat jiné PDF</button>
        <button class="secondary" id="finishBtn">Ne, hotovo</button>
      </div>
      <div id="formWrap" class="hidden">
        <div class="meta">
          <div><strong>Režim:</strong> <span id="modeInfo"></span></div>
          <div><strong>Soubor:</strong> <span id="sourceName"></span></div>
          <div id="reviewLine" class="hidden"><strong>Uložený dokument:</strong> <span id="reviewInfo"></span></div>
          <div><strong>OCR:</strong> <span id="ocrInfo"></span></div>
          <div><strong>Termíny:</strong> <span id="dueInfo"></span></div>
          <div id="duplicateLine" class="hidden"><strong>Duplicita:</strong> <span id="duplicateInfo"></span></div>
        </div>
        <div id="probableDuplicateBox" class="duplicate-box hidden">
          <strong id="duplicateBoxTitle">Tento dokument je pravděpodobně už uložený.</strong>
          <ul id="probableDuplicateList"></ul>
          <label class="checkline" for="allowDuplicate">
            <input id="allowDuplicate" type="checkbox">
            Přesto uložit jako další dokument
          </label>
        </div>
        <div id="encryptedBox" class="encrypted-box hidden">
          <strong>PDF je šifrované nebo zamčené.</strong>
          <ol>
            <li>Otevři dokument lokálně v Náhledu / Preview.</li>
            <li>Pokud se zeptá na heslo, zadej ho pouze u sebe na Macu.</li>
            <li>Ulož odemčenou kopii přes Exportovat nebo Tisk > PDF > Uložit jako PDF.</li>
            <li>Novou kopii ulož do Downloads a zpracuj ji jako nový dokument.</li>
          </ol>
          <p>Heslo nepiš do chatu a neukládej ho do paměti.</p>
        </div>
        <div class="actions">
          <button type="button" class="secondary" id="aiSuggestBtn">Navrhnout metadata pomocí AI</button>
        </div>
        <div class="field-help">Jen po stisknutí se OCR text tohoto dokumentu odešle do jednorázové read-only relace Codexu. Návrh se sám neuloží.</div>
        <div id="aiBox" class="ai-box hidden">
          <h2>AI návrh ke kontrole</h2>
          <p id="aiSummary"></p>
          <div id="aiFields" class="ai-fields"></div>
          <div id="aiDates"></div>
          <div id="aiWarnings" class="ai-warning"></div>
          <div class="actions">
            <button type="button" class="secondary" id="applyAiBtn">Převzít návrh do formuláře</button>
          </div>
          <p><strong>Nic ještě není uložené.</strong> Zápis provede až hlavní tlačítko Uložit.</p>
        </div>
        <label for="title">Název dokumentu</label>
        <input id="title" autocomplete="off">
        <label for="domain">Oblast</label>
        <select id="domain">
          <option value="food">food</option>
          <option value="health">health</option>
          <option value="car">car</option>
          <option value="insurance">insurance</option>
          <option value="energy">energy</option>
          <option value="home">home</option>
          <option value="tax">tax</option>
          <option value="warranty">warranty</option>
          <option value="other">other</option>
          <option value="__custom__">Jiná oblast...</option>
        </select>
        <div id="domainCustomWrap" class="custom-domain-wrap hidden">
          <input id="domainCustom" autocomplete="off" placeholder="např. ČEZ smlouvy, škola, byt Honzíkova">
          <div class="field-help">Nová oblast se při uložení převede na bezpečný interní název, například `ČEZ smlouvy` na `cez-smlouvy`.</div>
        </div>
        <label for="documentType">Typ dokumentu</label>
        <input id="documentType" autocomplete="off">
        <label for="counterparty">Protistrana</label>
        <input id="counterparty" autocomplete="off">
        <label for="relatedAsset">Související věc</label>
        <input id="relatedAsset" autocomplete="off">
        <label for="caseId">Case ID / souvislost</label>
        <input id="caseId" autocomplete="off">
        <label for="tags">Tagy</label>
        <textarea id="tags"></textarea>
        <div class="actions">
          <button type="button" class="primary" id="saveBtn">Uložit</button>
          <button type="button" class="secondary" id="skipBtn">Přeskočit</button>
          <button type="button" class="danger" id="stopBtn">Ukončit</button>
        </div>
      </div>
    </section>
    <section class="preview-shell">
      <iframe id="pdfFrame" title="Náhled PDF"></iframe>
      <div id="imagePreviewWrap" class="image-preview-wrap hidden">
        <img id="imagePreview" class="image-preview" alt="Náhled dokumentu">
      </div>
      <div id="previewFallback" class="preview-fallback hidden">
        <div class="preview-card">
          <h2>Náhled není dostupný</h2>
          <p id="previewFallbackText"></p>
          <a id="previewDownload" class="preview-download" href="#" download>Stáhnout soubor</a>
        </div>
      </div>
    </section>
  </main>
  <script>
    const fields = {
      status: document.getElementById("status"),
      formWrap: document.getElementById("formWrap"),
      sourceName: document.getElementById("sourceName"),
      modeInfo: document.getElementById("modeInfo"),
      reviewLine: document.getElementById("reviewLine"),
      reviewInfo: document.getElementById("reviewInfo"),
      ocrInfo: document.getElementById("ocrInfo"),
      dueInfo: document.getElementById("dueInfo"),
      duplicateLine: document.getElementById("duplicateLine"),
      duplicateInfo: document.getElementById("duplicateInfo"),
      duplicateBoxTitle: document.getElementById("duplicateBoxTitle"),
      probableDuplicateBox: document.getElementById("probableDuplicateBox"),
      probableDuplicateList: document.getElementById("probableDuplicateList"),
      encryptedBox: document.getElementById("encryptedBox"),
      aiSuggestBtn: document.getElementById("aiSuggestBtn"),
      aiBox: document.getElementById("aiBox"),
      aiSummary: document.getElementById("aiSummary"),
      aiFields: document.getElementById("aiFields"),
      aiDates: document.getElementById("aiDates"),
      aiWarnings: document.getElementById("aiWarnings"),
      applyAiBtn: document.getElementById("applyAiBtn"),
      allowDuplicate: document.getElementById("allowDuplicate"),
      downloadQuery: document.getElementById("downloadQuery"),
      downloadDate: document.getElementById("downloadDate"),
      downloadSearchBtn: document.getElementById("downloadSearchBtn"),
      downloadSearchStatus: document.getElementById("downloadSearchStatus"),
      downloadSearchResults: document.getElementById("downloadSearchResults"),
      completionActions: document.getElementById("completionActions"),
      title: document.getElementById("title"),
      domain: document.getElementById("domain"),
      domainCustomWrap: document.getElementById("domainCustomWrap"),
      domainCustom: document.getElementById("domainCustom"),
      documentType: document.getElementById("documentType"),
      counterparty: document.getElementById("counterparty"),
      relatedAsset: document.getElementById("relatedAsset"),
      caseId: document.getElementById("caseId"),
      tags: document.getElementById("tags"),
      pdfFrame: document.getElementById("pdfFrame"),
      imagePreviewWrap: document.getElementById("imagePreviewWrap"),
      imagePreview: document.getElementById("imagePreview"),
      previewFallback: document.getElementById("previewFallback"),
      previewFallbackText: document.getElementById("previewFallbackText"),
      previewDownload: document.getElementById("previewDownload"),
      saveBtn: document.getElementById("saveBtn"),
      skipBtn: document.getElementById("skipBtn")
    };
    let current = null;
    let saving = false;
    let aiSuggestion = null;
    const appBasePath = window.location.pathname.startsWith("/scandocu") ? "/scandocu" : "";
    const appUrl = (path) => `${appBasePath}${path}`;
    const appApiUrl = (path) => appBasePath ? `/api/scandocu${path.slice(4)}` : path;
    const appResourceUrl = (value) => appBasePath && String(value || "").startsWith("/")
      ? `${appBasePath}${value}`
      : value;
    const queryParams = new URLSearchParams(window.location.search);
    const appMode = queryParams.get("mode") === "review" ? "review" : "downloads";
    let requestedReviewDocumentRef = appMode === "review" ? (queryParams.get("document_ref") || "") : "";
    const isReviewMode = appMode === "review";
    document.querySelector("h1").textContent = isReviewMode ? "ScanDocu Review" : "ScanDocu";
    document.getElementById("nextBtn").textContent = isReviewMode ? "Další uložený dokument" : "Další PDF";

    async function loadNext() {
      fields.status.textContent = isReviewMode ? "Hledám další uložený dokument..." : "Hledám další PDF...";
      fields.formWrap.classList.add("hidden");
      fields.completionActions.classList.add("hidden");
      fields.pdfFrame.removeAttribute("src");
      fields.pdfFrame.classList.remove("hidden");
      fields.imagePreview.removeAttribute("src");
      fields.imagePreviewWrap.classList.add("hidden");
      fields.previewFallback.classList.add("hidden");
      const params = new URLSearchParams({mode: appMode});
      if (requestedReviewDocumentRef) params.set("document_ref", requestedReviewDocumentRef);
      const res = await fetch(appApiUrl(`/api/next?${params.toString()}`));
      const data = await res.json();
      if (!data.found) {
        current = null;
        fields.status.textContent = data.message || "Nenalezeno.";
        return;
      }
      requestedReviewDocumentRef = "";
      loadCandidate(data);
    }

    function loadCandidate(data) {
      current = data;
      aiSuggestion = null;
      fields.aiBox.classList.add("hidden");
      fields.aiFields.textContent = "";
      fields.aiDates.textContent = "";
      fields.aiWarnings.textContent = "";
      fields.aiSuggestBtn.disabled = false;
      fields.aiSuggestBtn.textContent = "Navrhnout metadata pomocí AI";
      const previewKind = data.preview_kind || (data.inline_preview ? "pdf" : "none");
      fields.status.textContent = previewKind === "image"
        ? "Zkontroluj obrázek a metadata."
        : (previewKind === "pdf" ? "Zkontroluj PDF a metadata." : "Zkontroluj dokument a metadata. Náhled je dostupný jen pro PDF a obrázky.");
      fields.formWrap.classList.remove("hidden");
      fields.completionActions.classList.add("hidden");
      fields.modeInfo.textContent = data.source_mode === "vault_review" ? "revize uloženého dokumentu" : "nový dokument z Downloads";
      fields.sourceName.textContent = data.source_name;
      fields.reviewLine.classList.toggle("hidden", data.source_mode !== "vault_review");
      fields.reviewInfo.textContent = data.review_document_id || "";
      fields.ocrInfo.textContent = `${data.extraction_method || "nezjištěno"} / OCR: ${data.ocr_needed ? "ano" : "ne"}`;
      fields.dueInfo.textContent = String(data.due_date_count || 0);
      fields.duplicateLine.classList.toggle("hidden", !data.duplicate_document_id);
      fields.duplicateInfo.textContent = data.duplicate_document_id || "";
      renderImportWarnings(data.probable_duplicates || [], data.consistency_conflicts || []);
      renderEncryptedHelp(data);
      fields.title.value = data.title || "";
      setDomainValue(data.domain || "other");
      fields.documentType.value = data.document_type || "document";
      fields.counterparty.value = data.counterparty || "";
      fields.relatedAsset.value = data.related_asset || "";
      fields.caseId.value = data.case_id || "";
      fields.tags.value = data.tags || "";
      if (previewKind === "pdf") {
        fields.previewFallback.classList.add("hidden");
        fields.imagePreview.removeAttribute("src");
        fields.imagePreviewWrap.classList.add("hidden");
        fields.pdfFrame.classList.remove("hidden");
        fields.pdfFrame.src = appResourceUrl(data.preview_url || data.pdf_url);
      } else if (previewKind === "image") {
        fields.previewFallback.classList.add("hidden");
        fields.pdfFrame.removeAttribute("src");
        fields.pdfFrame.classList.add("hidden");
        fields.imagePreviewWrap.classList.remove("hidden");
        fields.imagePreview.src = appResourceUrl(data.preview_url || data.file_url);
      } else {
        fields.pdfFrame.removeAttribute("src");
        fields.pdfFrame.classList.add("hidden");
        fields.imagePreview.removeAttribute("src");
        fields.imagePreviewWrap.classList.add("hidden");
        fields.previewFallback.classList.remove("hidden");
        const extension = data.file_extension || "soubor";
        fields.previewFallbackText.textContent = `Soubor ${data.source_name || ""} má typ ${extension}. Prohlížeč ho neumí bezpečně zobrazit v PDF náhledu. Stáhni ho a otevři lokálně, metadata pak potvrď vlevo.`;
        fields.previewDownload.href = appResourceUrl(data.file_url) || "#";
        fields.previewDownload.download = data.source_name || "";
      }
    }

    function knownDomainValues() {
      return Array.from(fields.domain.options).map((option) => option.value);
    }

    function customDomainOption() {
      return Array.from(fields.domain.options).find((option) => option.value === "__custom__");
    }

    function upsertDomainOption(value, label) {
      const cleanValue = (value || "").trim();
      if (!cleanValue || cleanValue === "__custom__") return;
      const cleanLabel = (label || cleanValue).trim();
      const existing = Array.from(fields.domain.options).find((option) => option.value === cleanValue);
      if (existing) {
        existing.textContent = cleanLabel;
        return;
      }
      const option = document.createElement("option");
      option.value = cleanValue;
      option.textContent = cleanLabel;
      fields.domain.insertBefore(option, customDomainOption() || null);
    }

    async function loadDomainOptions() {
      try {
        const res = await fetch(appApiUrl("/api/domains"));
        const data = await res.json();
        (data.domains || []).forEach((item) => upsertDomainOption(item.value, item.label));
      } catch (err) {
        // The static domain list is enough to keep ScanDocu usable if the registry endpoint fails.
      }
    }

    function setDomainValue(value) {
      const cleanValue = (value || "other").trim() || "other";
      if (knownDomainValues().includes(cleanValue) && cleanValue !== "__custom__") {
        fields.domain.value = cleanValue;
        fields.domainCustom.value = "";
      } else {
        fields.domain.value = "__custom__";
        fields.domainCustom.value = cleanValue;
      }
      updateCustomDomainVisibility(false);
    }

    function updateCustomDomainVisibility(focusCustom = true) {
      const custom = fields.domain.value === "__custom__";
      fields.domainCustomWrap.classList.toggle("hidden", !custom);
      if (custom && focusCustom) {
        fields.domainCustom.focus({preventScroll: true});
      }
    }

    function selectedDomainValue() {
      if (fields.domain.value !== "__custom__") {
        return fields.domain.value;
      }
      return fields.domainCustom.value.trim();
    }

    function displayAiValue(value) {
      if (Array.isArray(value)) {
        return value.join(", ");
      }
      return String(value || "nezjištěno");
    }

    async function requestAiSuggestion() {
      if (!current) return;
      aiSuggestion = null;
      fields.aiBox.classList.add("hidden");
      fields.aiSuggestBtn.disabled = true;
      fields.aiSuggestBtn.textContent = "AI čte dokument...";
      fields.status.textContent = "Codex připravuje jen read-only návrh metadat. U většího dokumentu to může chvíli trvat.";
      try {
        const res = await fetch(appApiUrl("/api/ai-metadata"), {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({token: current.token})
        });
        const data = await res.json();
        if (!res.ok || data.error || !data.ok) {
          fields.status.textContent = data.error || "AI návrh se nepodařilo připravit.";
          return;
        }
        aiSuggestion = data;
        renderAiSuggestion(data);
        fields.status.textContent = data.message || "AI návrh je připravený ke kontrole; nic nebylo uloženo.";
      } catch (error) {
        fields.status.textContent = `AI návrh selhal nebo server neodpověděl: ${error}`;
      } finally {
        fields.aiSuggestBtn.disabled = false;
        fields.aiSuggestBtn.textContent = "Navrhnout metadata pomocí AI";
      }
    }

    function renderAiSuggestion(data) {
      fields.aiSummary.textContent = data.summary || "";
      fields.aiFields.textContent = "";
      (data.fields || []).forEach((item) => {
        const row = document.createElement("div");
        row.className = "ai-field";
        const comparison = document.createElement("div");
        const strong = document.createElement("strong");
        strong.textContent = `${item.label || item.field}: `;
        comparison.appendChild(strong);
        comparison.appendChild(document.createTextNode(
          `${displayAiValue(item.current)} → ${displayAiValue(item.proposed)} (${item.confidence || "low"})`
        ));
        row.appendChild(comparison);
        if (item.evidence) {
          const evidence = document.createElement("div");
          evidence.className = "ai-evidence";
          evidence.textContent = `Důkaz: „${item.evidence}“`;
          row.appendChild(evidence);
        }
        fields.aiFields.appendChild(row);
      });
      fields.aiDates.textContent = "";
      const dates = data.important_dates || [];
      if (dates.length) {
        const heading = document.createElement("strong");
        heading.textContent = "Důležitá data:";
        fields.aiDates.appendChild(heading);
        dates.forEach((item) => {
          const line = document.createElement("div");
          line.className = "ai-evidence";
          line.textContent = `${item.date} | ${item.type} | ${item.confidence} | „${item.evidence}“`;
          fields.aiDates.appendChild(line);
        });
      }
      fields.aiWarnings.textContent = (data.warnings || []).join(" ");
      fields.applyAiBtn.disabled = !(data.changed_count > 0);
      fields.aiBox.classList.remove("hidden");
    }

    function applyAiSuggestionToForm() {
      if (!aiSuggestion || !aiSuggestion.suggestion) return;
      const suggestion = aiSuggestion.suggestion;
      if (suggestion.title) fields.title.value = suggestion.title;
      if (suggestion.domain) setDomainValue(suggestion.domain);
      if (suggestion.document_type) fields.documentType.value = suggestion.document_type;
      if (suggestion.counterparty) fields.counterparty.value = suggestion.counterparty;
      if (suggestion.related_asset) fields.relatedAsset.value = suggestion.related_asset;
      if (Array.isArray(suggestion.tags) && suggestion.tags.length) {
        fields.tags.value = suggestion.tags.join(", ");
      }
      fields.status.textContent = "AI návrh byl přenesen do formuláře. Zkontroluj ho; nic se neuloží, dokud nestiskneš Uložit.";
    }

    async function searchDownloads() {
      const query = fields.downloadQuery.value.trim();
      const date = fields.downloadDate.value.trim();
      fields.downloadSearchResults.innerHTML = "";
      fields.downloadSearchStatus.classList.remove("hidden");
      if (!query && !date) {
        fields.downloadSearchStatus.textContent = "Zadej část názvu nebo datum.";
        return;
      }
      fields.downloadSearchStatus.textContent = "Hledám PDF v Downloads...";
      fields.downloadSearchBtn.disabled = true;
      try {
        const res = await fetch(appApiUrl(`/api/search-downloads?q=${encodeURIComponent(query)}&date=${encodeURIComponent(date)}`));
        const data = await res.json();
        renderDownloadSearchResults(data.items || []);
        fields.downloadSearchStatus.textContent = data.items && data.items.length
          ? `Nalezeno: ${data.items.length}`
          : "Nenalezeno žádné PDF.";
      } catch (err) {
        fields.downloadSearchStatus.textContent = `Chyba hledání: ${err}`;
      } finally {
        fields.downloadSearchBtn.disabled = false;
      }
    }

    function renderDownloadSearchResults(items) {
      fields.downloadSearchResults.innerHTML = "";
      items.forEach((item) => {
        const row = document.createElement("div");
        row.className = "download-result";
        const text = document.createElement("div");
        const title = document.createElement("div");
        title.className = "download-result-title";
        title.textContent = item.name || "";
        const meta = document.createElement("div");
        meta.className = "download-result-meta";
        meta.textContent = `${item.modified_date || item.modified_at || ""} | ${item.status || "unknown"} | ${item.size_bytes || 0} B`;
        const button = document.createElement("button");
        button.className = "secondary";
        button.type = "button";
        button.textContent = item.status === "already_in_vault" ? "Revidovat z vaultu" : "Zpracovat";
        button.disabled = item.status === "invalid";
        button.addEventListener("click", () => selectDownload(item.path));
        text.appendChild(title);
        text.appendChild(meta);
        row.appendChild(text);
        row.appendChild(button);
        fields.downloadSearchResults.appendChild(row);
      });
    }

    async function selectDownload(sourcePath) {
      if (!sourcePath) return;
      fields.status.textContent = "Připravuji vybraný dokument...";
      const res = await fetch(appApiUrl("/api/select-download"), {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({source_path: sourcePath})
      });
      const data = await res.json();
      if (!res.ok || data.error) {
        fields.status.textContent = data.error || "Vybraný dokument nejde připravit.";
        return;
      }
      loadCandidate(data);
    }

    async function saveCurrent() {
      if (!current || saving) return;
      if (((current.probable_duplicates || []).length > 0 || (current.consistency_conflicts || []).length > 0) && !fields.allowDuplicate.checked) {
        fields.status.textContent = "Neuloženo: dokument má varování. Zkontroluj seznam a zaškrtni `Přesto uložit jako další dokument`, pokud ho chceš uložit.";
        fields.probableDuplicateBox.scrollIntoView({behavior: "smooth", block: "center"});
        return;
      }
      const domainValue = selectedDomainValue();
      if (!domainValue) {
        fields.status.textContent = "Neuloženo: zadej název nové oblasti, nebo vyber existující oblast.";
        fields.domainCustomWrap.scrollIntoView({behavior: "smooth", block: "center"});
        fields.domainCustom.focus();
        return;
      }
      saving = true;
      fields.saveBtn.disabled = true;
      fields.skipBtn.disabled = true;
      fields.saveBtn.textContent = "Ukládám...";
      fields.status.textContent = "Ukládám dokument do vaultu. U větších PDF může krok trvat desítky sekund kvůli kopii, textové extrakci a indexu.";
      try {
        const res = await fetch(appApiUrl("/api/save"), {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            token: current.token,
            title: fields.title.value,
            domain: domainValue,
            document_type: fields.documentType.value,
            counterparty: fields.counterparty.value,
            related_asset: fields.relatedAsset.value,
            case_id: fields.caseId.value,
            tags: fields.tags.value,
            allow_probable_duplicate: fields.allowDuplicate.checked
          })
        });
        const data = await res.json();
        if (!res.ok || data.error || data.status === "probable_duplicate" || data.status === "consistency_conflict") {
          fields.status.textContent = data.message || data.error || "Uložení selhalo.";
          current.consistency_conflicts = data.consistency_conflicts || [];
          if (data.probable_duplicates || data.consistency_conflicts) {
            renderImportWarnings(data.probable_duplicates || current.probable_duplicates || [], data.consistency_conflicts || []);
          }
          return;
        }
        if (data.domain) {
          upsertDomainOption(data.domain, fields.domain.value === "__custom__" ? domainValue : data.domain);
        }
        fields.status.textContent = `${data.status === "reviewed" ? "Aktualizováno" : "Uloženo"}: ${data.document_id}. Chceš pokračovat?`;
        fields.formWrap.classList.add("hidden");
        fields.completionActions.classList.remove("hidden");
        current = null;
      } catch (error) {
        fields.status.textContent = `Uložení selhalo nebo server neodpověděl: ${error}`;
      } finally {
        saving = false;
        fields.saveBtn.disabled = false;
        fields.skipBtn.disabled = false;
        fields.saveBtn.textContent = "Uložit";
      }
    }

    function renderImportWarnings(items, consistencyConflicts) {
      fields.allowDuplicate.checked = false;
      fields.probableDuplicateList.innerHTML = "";
      const hasDuplicates = items.length > 0;
      const hasConsistencyConflicts = consistencyConflicts.length > 0;
      fields.probableDuplicateBox.classList.toggle("hidden", !hasDuplicates && !hasConsistencyConflicts);
      if (hasConsistencyConflicts) {
        fields.duplicateBoxTitle.textContent = "Dokument věcně koliduje s již uloženým pojištěním.";
        fields.status.textContent = "Věcný konflikt: zkontroluj seznam níže. Bez zaškrtnutí `Přesto uložit jako další dokument` se dokument neuloží.";
      } else if (hasDuplicates) {
        fields.duplicateBoxTitle.textContent = "Tento dokument je pravděpodobně už uložený.";
        fields.status.textContent = "Možná duplicita: zkontroluj seznam níže. Bez zaškrtnutí `Přesto uložit jako další dokument` se dokument neuloží.";
      }
      items.forEach((item) => {
        const li = document.createElement("li");
        const name = item.title || item.original_filename || item.document_id || "bez názvu";
        const path = item.stored_path || "";
        li.textContent = `${name} | ${item.domain || "other"} / ${item.document_type || "document"} | ${path}`;
        fields.probableDuplicateList.appendChild(li);
      });
      consistencyConflicts.forEach((finding) => {
        const li = document.createElement("li");
        const title = finding.title || finding.code || "věcný konflikt";
        const details = (finding.items || []).map((item) => {
          const label = item.label || item.source_id || "";
          const amount = item.amount ? ` | ${item.amount}` : "";
          const policy = item.policy_numbers ? ` | smlouva/návrh ${item.policy_numbers}` : "";
          return `${label}${amount}${policy}`;
        }).join("; ");
        li.textContent = `${title}: ${details}`;
        fields.probableDuplicateList.appendChild(li);
      });
    }

    function renderEncryptedHelp(data) {
      const method = (data.extraction_method || "").toLowerCase();
      const warning = (data.warning || "").toLowerCase();
      const encrypted = method.includes("encrypted") || warning.includes("/encrypt") || warning.includes("sifrov");
      fields.encryptedBox.classList.toggle("hidden", !encrypted);
      if (encrypted) {
        fields.status.textContent = "PDF je zamčené. Odemčenou kopii připrav ručně a tento záznam zatím přeskoč.";
      }
    }

    async function skipCurrent() {
      if (!current) return;
      await fetch(appApiUrl("/api/skip"), {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({token: current.token})
      });
      await loadNext();
    }

    function returnToCockpit() {
      const cockpitUrl = appBasePath ? window.location.origin : "http://127.0.0.1:8770";
      if (window.opener && !window.opener.closed) {
        try {
          window.opener.focus();
        } catch (err) {
          // Focus can fail across browser contexts; closing the ScanDocu popup is still the right fallback.
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

    document.getElementById("nextBtn").addEventListener("click", loadNext);
    document.getElementById("cockpitBtn").addEventListener("click", returnToCockpit);
    document.getElementById("archiveBtn").addEventListener("click", () => {
      window.location.href = appUrl("/?mode=browse");
    });
    fields.aiSuggestBtn.addEventListener("click", requestAiSuggestion);
    fields.applyAiBtn.addEventListener("click", applyAiSuggestionToForm);
    document.getElementById("continueBtn").addEventListener("click", loadNext);
    document.getElementById("searchAgainBtn").addEventListener("click", () => {
      fields.completionActions.classList.add("hidden");
      fields.formWrap.classList.add("hidden");
      fields.pdfFrame.removeAttribute("src");
      current = null;
      fields.status.textContent = "Zadej název nebo datum a vyhledej další PDF.";
      fields.downloadQuery.focus();
    });
    document.getElementById("finishBtn").addEventListener("click", () => {
      fields.completionActions.classList.add("hidden");
      fields.formWrap.classList.add("hidden");
      fields.pdfFrame.removeAttribute("src");
      current = null;
      fields.status.textContent = "Hotovo. Okno můžeš zavřít nebo se vrátit k hledání.";
      window.close();
    });
    document.getElementById("downloadSearchBtn").addEventListener("click", searchDownloads);
    fields.downloadQuery.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        searchDownloads();
      }
    });
    document.getElementById("saveBtn").addEventListener("click", saveCurrent);
    document.getElementById("skipBtn").addEventListener("click", skipCurrent);
    fields.domain.addEventListener("change", updateCustomDomainVisibility);
    document.getElementById("stopBtn").addEventListener("click", () => {
      fields.status.textContent = "ScanDocu ukončeno v prohlížeči. Server můžeš zastavit v terminálu.";
      fields.formWrap.classList.add("hidden");
      fields.completionActions.classList.add("hidden");
      fields.pdfFrame.removeAttribute("src");
      current = null;
    });
    async function initializeScanDocu() {
      await loadDomainOptions();
      await loadNext();
    }
    initializeScanDocu();
  </script>
</body>
</html>
"""


SCANDOCU_ARCHIVE_HTML = """<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Uložené dokumenty</title>
  <style>
    :root {
      --bg: #eef2f7;
      --panel: #ffffff;
      --panel-soft: #f7f9fc;
      --ink: #172033;
      --muted: #697386;
      --line: #dce3ed;
      --line-strong: #c8d2e0;
      --blue: #2459a8;
      --blue-dark: #17447f;
      --blue-soft: #eaf2ff;
      --amber: #9a5b08;
      --amber-soft: #fff5df;
      --green: #18794e;
      --green-soft: #eaf8f0;
    }
    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      overflow: hidden;
    }
    button, input { font: inherit; }
    button { border: 0; cursor: pointer; color: inherit; }
    button:focus-visible, input:focus-visible, a:focus-visible {
      outline: 3px solid rgba(36, 89, 168, 0.28);
      outline-offset: 2px;
    }
    .app-header {
      height: 72px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 0 22px;
      background: var(--panel);
      border-bottom: 1px solid var(--line);
      position: relative;
      z-index: 3;
    }
    .brand, .header-actions, .search-row, .list-heading, .document-line,
    .reader-toolbar, .detail-actions {
      display: flex;
      align-items: center;
    }
    .brand { gap: 12px; min-width: 0; }
    .brand-mark {
      width: 38px;
      height: 38px;
      border-radius: 11px;
      display: grid;
      place-items: center;
      background: var(--blue);
      color: white;
      font-size: 19px;
      box-shadow: 0 5px 14px rgba(36, 89, 168, 0.24);
    }
    h1 { margin: 0; font-size: 20px; letter-spacing: -0.01em; }
    .brand-subtitle { color: var(--muted); font-size: 12px; margin-top: 1px; }
    .header-actions { gap: 8px; }
    .primary, .quiet, a.action-link {
      min-height: 38px;
      border-radius: 9px;
      padding: 8px 13px;
      font-weight: 700;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      white-space: nowrap;
    }
    .primary { background: var(--blue); color: white; }
    .primary:hover { background: var(--blue-dark); }
    .quiet { background: #edf2f8; color: #284564; }
    .quiet:hover { background: #e2e9f2; }
    .document-browser {
      height: calc(100vh - 72px);
      display: grid;
      grid-template-columns: 215px minmax(320px, 410px) minmax(440px, 1fr);
      background: var(--panel);
    }
    .folder-pane {
      padding: 22px 14px;
      background: #f4f7fb;
      border-right: 1px solid var(--line);
      overflow-y: auto;
    }
    .folder-title {
      padding: 0 11px 10px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .folder {
      width: 100%;
      min-height: 42px;
      display: grid;
      grid-template-columns: 24px 1fr auto;
      align-items: center;
      gap: 7px;
      padding: 8px 11px;
      border-radius: 9px;
      background: transparent;
      text-align: left;
      font-weight: 700;
      color: #40536c;
    }
    .folder:hover { background: #e9eff7; }
    .folder.active { background: var(--blue-soft); color: var(--blue-dark); }
    .folder-count {
      min-width: 25px;
      padding: 2px 7px;
      border-radius: 999px;
      background: rgba(255,255,255,0.78);
      text-align: center;
      font-size: 12px;
    }
    .domain-folders { display: grid; gap: 2px; }
    .folder-note {
      margin: 24px 8px 0;
      padding-top: 17px;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 12px;
      line-height: 1.55;
    }
    .list-pane {
      min-width: 0;
      display: grid;
      grid-template-rows: auto auto minmax(0, 1fr);
      border-right: 1px solid var(--line);
      background: var(--panel);
    }
    .search-row {
      gap: 8px;
      padding: 15px 14px 11px;
      border-bottom: 1px solid var(--line);
    }
    .search-box {
      flex: 1;
      min-width: 0;
      height: 40px;
      border: 1px solid var(--line-strong);
      border-radius: 10px;
      background: var(--panel-soft);
      padding: 0 11px;
    }
    .search-box:focus {
      border-color: #79a1dc;
      background: white;
      box-shadow: 0 0 0 3px rgba(36, 89, 168, 0.10);
      outline: 0;
    }
    .list-heading {
      justify-content: space-between;
      gap: 12px;
      padding: 10px 15px;
      background: var(--panel-soft);
      border-bottom: 1px solid var(--line);
    }
    .list-heading h2 { margin: 0; font-size: 14px; }
    .status { color: var(--muted); font-size: 12px; text-align: right; }
    .document-list { overflow-y: auto; min-height: 0; }
    .document-item {
      width: 100%;
      display: grid;
      gap: 5px;
      padding: 13px 15px;
      border-bottom: 1px solid #e8edf4;
      background: white;
      text-align: left;
    }
    .document-item:hover { background: #f7faff; }
    .document-item.active {
      background: var(--blue-soft);
      box-shadow: inset 4px 0 0 var(--blue);
    }
    .document-line { justify-content: space-between; gap: 10px; min-width: 0; }
    .document-title {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-weight: 800;
      color: #26384e;
    }
    .document-date { color: var(--muted); font-size: 12px; white-space: nowrap; }
    .document-subtitle {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      color: #40536c;
    }
    .document-badges { display: flex; gap: 6px; flex-wrap: wrap; }
    .badge {
      display: inline-flex;
      border-radius: 999px;
      padding: 2px 7px;
      font-size: 11px;
      font-weight: 750;
      background: #edf2f8;
      color: #40536c;
    }
    .badge.review { background: var(--amber-soft); color: var(--amber); }
    .badge.ok { background: var(--green-soft); color: var(--green); }
    .reader-pane {
      min-width: 0;
      display: grid;
      grid-template-rows: 45px minmax(0, 1fr);
      background: #fbfcfe;
    }
    .reader-toolbar {
      justify-content: space-between;
      padding: 0 18px;
      border-bottom: 1px solid var(--line);
      background: var(--panel-soft);
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }
    .mobile-back { display: none; min-height: 32px; padding: 5px 9px; }
    .reader { min-height: 0; overflow-y: auto; }
    .reader-empty {
      min-height: 100%;
      display: grid;
      place-content: center;
      justify-items: center;
      padding: 30px;
      text-align: center;
      color: var(--muted);
    }
    .reader-empty-icon {
      width: 58px;
      height: 58px;
      display: grid;
      place-items: center;
      border-radius: 18px;
      background: #e9eef5;
      font-size: 25px;
      margin-bottom: 12px;
    }
    .reader-empty h2 { color: var(--ink); margin: 0 0 6px; font-size: 18px; }
    .reader-empty p { margin: 0; max-width: 380px; }
    .document-content { max-width: 1080px; margin: 0 auto; padding: 24px 28px 42px; }
    .document-heading {
      padding-bottom: 17px;
      border-bottom: 1px solid var(--line);
    }
    .document-heading h2 {
      margin: 0 0 12px;
      font-size: clamp(21px, 2.2vw, 29px);
      line-height: 1.2;
      overflow-wrap: anywhere;
    }
    .detail-actions { gap: 8px; flex-wrap: wrap; }
    .detail-meta {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px 18px;
      padding: 18px 0;
      border-bottom: 1px solid var(--line);
    }
    .meta-row { min-width: 0; }
    .meta-label {
      color: var(--muted);
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .meta-value { margin-top: 2px; overflow-wrap: anywhere; }
    .tag-list { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
    .viewer-shell {
      margin-top: 18px;
      height: min(66vh, 760px);
      min-height: 440px;
      border: 1px solid var(--line);
      border-radius: 12px;
      overflow: hidden;
      background: #e5e7eb;
    }
    .document-viewer { width: 100%; height: 100%; border: 0; background: white; }
    .image-viewer { height: 100%; overflow: auto; padding: 14px; text-align: center; background: #111827; }
    .image-viewer img { max-width: 100%; height: auto; background: white; }
    .download-card {
      height: 100%;
      display: grid;
      place-content: center;
      justify-items: center;
      gap: 12px;
      padding: 26px;
      text-align: center;
      background: white;
    }
    details.text-preview {
      margin-top: 18px;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: white;
      padding: 12px 14px;
    }
    details.text-preview summary { cursor: pointer; font-weight: 750; }
    .text-content { white-space: pre-wrap; overflow-wrap: anywhere; margin-top: 12px; color: #34435a; }
    .empty-list { padding: 24px 18px; color: var(--muted); text-align: center; }
    @media (max-width: 900px) {
      body { overflow: auto; }
      .app-header { height: auto; min-height: 72px; padding: 11px 13px; align-items: flex-start; }
      .brand-subtitle { display: none; }
      .header-actions { flex-wrap: wrap; justify-content: flex-end; }
      .document-browser { height: auto; min-height: calc(100vh - 72px); display: block; }
      .folder-pane { display: flex; gap: 6px; overflow-x: auto; padding: 10px; border-right: 0; border-bottom: 1px solid var(--line); }
      .folder-title, .folder-note { display: none; }
      .domain-folders { display: flex; gap: 6px; }
      .folder { width: auto; min-width: max-content; grid-template-columns: auto auto; }
      .folder span:first-child { display: none; }
      .list-pane { height: calc(100vh - 135px); border-right: 0; }
      .reader-pane { display: none; min-height: calc(100vh - 72px); }
      body.reader-open .folder-pane, body.reader-open .list-pane { display: none; }
      body.reader-open .reader-pane { display: grid; }
      .mobile-back { display: inline-flex; }
      .document-content { padding: 18px 15px 32px; }
      .detail-meta { grid-template-columns: 1fr; }
      .viewer-shell { height: 67vh; min-height: 420px; }
    }
  </style>
</head>
<body>
  <header class="app-header">
    <div class="brand">
      <div class="brand-mark" aria-hidden="true">▤</div>
      <div>
        <h1>Uložené dokumenty</h1>
        <div class="brand-subtitle">Místní dokumentový trezor</div>
      </div>
    </div>
    <div class="header-actions">
      <button class="quiet" id="cockpitBtn">Zpět do Cockpitu</button>
      <button class="quiet" id="newDocumentBtn">Nový dokument</button>
      <button class="quiet" id="reviewBtn">Dokumenty k revizi</button>
      <button class="primary" id="refreshBtn">Obnovit</button>
    </div>
  </header>

  <main class="document-browser">
    <aside class="folder-pane" aria-label="Filtry dokumentů">
      <div class="folder-title">Dokumenty</div>
      <button class="folder active" data-reading-status="">
        <span aria-hidden="true">▣</span><span>Všechny</span>
        <span class="folder-count" id="allCount">0</span>
      </button>
      <button class="folder" data-reading-status="needs_review">
        <span aria-hidden="true">!</span><span>K revizi</span>
        <span class="folder-count" id="reviewCount">0</span>
      </button>
      <div class="folder-title" style="margin-top: 18px;">Oblasti</div>
      <div class="domain-folders" id="domainFolders"></div>
      <div class="folder-note">
        Toto je pouze čtení místního trezoru. Dokumenty se zde nemažou,
        nepřesouvají ani neupravují.
      </div>
    </aside>

    <section class="list-pane" aria-labelledby="documentListTitle">
      <div class="search-row">
        <input class="search-box" id="searchInput" type="search" autocomplete="off"
               placeholder="Hledat podle názvu, firmy nebo obsahu">
        <button class="primary" id="searchBtn">Hledat</button>
      </div>
      <div class="list-heading">
        <h2 id="documentListTitle">Všechny dokumenty</h2>
        <div class="status" id="status" role="status">Načítám dokumenty…</div>
      </div>
      <div class="document-list" id="documentList" aria-live="polite"></div>
    </section>

    <section class="reader-pane" aria-label="Otevřený dokument">
      <div class="reader-toolbar">
        <button class="quiet mobile-back" id="documentBackBtn">← Zpět na seznam</button>
        <div>Náhled dokumentu</div>
      </div>
      <div class="reader" id="detailPane">
        <div class="reader-empty">
          <div class="reader-empty-icon" aria-hidden="true">▤</div>
          <h2>Vyber dokument ze seznamu</h2>
          <p>Celý dokument se otevře tady. Původní soubor zůstává beze změny v místním trezoru.</p>
        </div>
      </div>
    </section>
  </main>

  <script>
    const archiveBasePath = window.location.pathname.startsWith("/scandocu") ? "/scandocu" : "";
    const archiveUrl = (path) => `${archiveBasePath}${path}`;
    const archiveApiUrl = (path) => archiveBasePath ? `/api/scandocu${path.slice(4)}` : path;
    const archiveResourceUrl = (value) => archiveBasePath && String(value || "").startsWith("/")
      ? `${archiveBasePath}${value}`
      : value;
    const listNode = document.getElementById("documentList");
    const detailPane = document.getElementById("detailPane");
    const statusNode = document.getElementById("status");
    const searchInput = document.getElementById("searchInput");
    const listTitle = document.getElementById("documentListTitle");
    const allCount = document.getElementById("allCount");
    const reviewCount = document.getElementById("reviewCount");
    const domainFolders = document.getElementById("domainFolders");
    let items = [];
    let domains = [];
    let selectedDocumentRef = "";
    let activeReadingStatus = "";
    let activeDomain = "";
    let requestNumber = 0;

    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, (character) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }[character]));
    }

    function labelForDomain(value) {
      const labels = {
        car: "Auto", energy: "Energie", food: "Jídlo", health: "Zdraví",
        home: "Bydlení", insurance: "Pojištění", other: "Ostatní",
        tax: "Daně", telecom: "Telefon a internet", travel: "Cestování",
        warranty: "Záruky"
      };
      return labels[value] || value || "Ostatní";
    }

    function labelForType(value) {
      const labels = {
        contract: "smlouva", email: "e-mail", invoice: "faktura",
        lease: "nájemní smlouva", payment: "platba", policy: "pojistná smlouva",
        receipt: "účtenka", statement: "výpis"
      };
      return labels[value] || value || "dokument";
    }

    function shortDate(value) {
      const moment = new Date(String(value || ""));
      if (Number.isNaN(moment.getTime())) return String(value || "");
      return new Intl.DateTimeFormat("cs-CZ", {
        day: "numeric", month: "short", year: "numeric"
      }).format(moment);
    }

    function longDate(value) {
      const moment = new Date(String(value || ""));
      if (Number.isNaN(moment.getTime())) return String(value || "nezjištěno");
      return new Intl.DateTimeFormat("cs-CZ", {
        day: "numeric", month: "long", year: "numeric",
        hour: "2-digit", minute: "2-digit"
      }).format(moment);
    }

    function fileSize(bytes) {
      const value = Number(bytes || 0);
      if (value >= 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)} MB`;
      if (value >= 1024) return `${Math.round(value / 1024)} kB`;
      return value > 0 ? `${value} B` : "nezjištěno";
    }

    function renderFolders(data) {
      allCount.textContent = String(data.total_count || 0);
      reviewCount.textContent = String(data.review_count || 0);
      domains = data.domains || [];
      domainFolders.innerHTML = domains.map((domain) => `
        <button class="folder ${activeDomain === domain.value ? "active" : ""}"
                data-domain="${escapeHtml(domain.value)}">
          <span aria-hidden="true">•</span>
          <span>${escapeHtml(labelForDomain(domain.label || domain.value))}</span>
          <span class="folder-count">${Number(domain.count || 0)}</span>
        </button>
      `).join("");
      domainFolders.querySelectorAll("[data-domain]").forEach((button) => {
        button.addEventListener("click", () => {
          activeDomain = activeDomain === button.dataset.domain ? "" : (button.dataset.domain || "");
          loadDocuments();
        });
      });
      document.querySelectorAll("[data-reading-status]").forEach((button) => {
        const active = button.dataset.readingStatus === activeReadingStatus && !activeDomain;
        button.classList.toggle("active", active);
        button.setAttribute("aria-pressed", active ? "true" : "false");
      });
    }

    function renderList() {
      if (!items.length) {
        listNode.innerHTML = '<div class="empty-list">Tomuto hledání neodpovídá žádný dokument.</div>';
        return;
      }
      listNode.innerHTML = items.map((item) => `
        <button class="document-item ${item.document_ref === selectedDocumentRef ? "active" : ""}"
                data-document-ref="${escapeHtml(item.document_ref)}">
          <div class="document-line">
            <div class="document-title">${escapeHtml(item.title || "Dokument bez názvu")}</div>
            <div class="document-date">${escapeHtml(shortDate(item.imported_at))}</div>
          </div>
          <div class="document-subtitle">
            ${escapeHtml(item.counterparty || item.original_filename || labelForType(item.document_type))}
          </div>
          <div class="document-badges">
            <span class="badge">${escapeHtml(labelForDomain(item.domain))}</span>
            <span class="badge ${item.reading_status === "needs_review" ? "review" : "ok"}">
              ${escapeHtml(item.reading_status_label || "")}
            </span>
          </div>
        </button>
      `).join("");
      listNode.querySelectorAll("[data-document-ref]").forEach((button) => {
        button.addEventListener("click", () => loadDetail(button.dataset.documentRef || ""));
      });
    }

    async function loadDocuments() {
      const currentRequest = ++requestNumber;
      statusNode.textContent = "Načítám…";
      const params = new URLSearchParams();
      if (searchInput.value.trim()) params.set("q", searchInput.value.trim());
      if (activeDomain) params.set("domain", activeDomain);
      if (activeReadingStatus) params.set("reading_status", activeReadingStatus);
      try {
        const response = await fetch(archiveApiUrl(`/api/documents?${params.toString()}`));
        const data = await response.json();
        if (currentRequest !== requestNumber) return;
        if (!response.ok || !data.ok) throw new Error(data.message || data.error || "Seznam není dostupný.");
        items = data.items || [];
        renderFolders(data);
        renderList();
        statusNode.textContent = `${items.length} z ${data.total_count || items.length}`;
        listTitle.textContent = activeDomain
          ? labelForDomain(activeDomain)
          : (activeReadingStatus === "needs_review" ? "Dokumenty k revizi" : "Všechny dokumenty");
        if (selectedDocumentRef && !items.some((item) => item.document_ref === selectedDocumentRef)) {
          selectedDocumentRef = "";
          renderEmptyDetail();
        }
      } catch (error) {
        items = [];
        renderList();
        statusNode.textContent = `Chyba: ${error}`;
      }
    }

    function updateActiveDocument() {
      listNode.querySelectorAll("[data-document-ref]").forEach((button) => {
        const active = button.dataset.documentRef === selectedDocumentRef;
        button.classList.toggle("active", active);
        button.setAttribute("aria-current", active ? "true" : "false");
      });
    }

    function renderEmptyDetail() {
      detailPane.innerHTML = `
        <div class="reader-empty">
          <div class="reader-empty-icon" aria-hidden="true">▤</div>
          <h2>Vyber dokument ze seznamu</h2>
          <p>Celý dokument se otevře tady. Původní soubor zůstává beze změny v místním trezoru.</p>
        </div>
      `;
      document.body.classList.remove("reader-open");
    }

    function renderDetail(data) {
      if (!data.ok) {
        detailPane.innerHTML = `
          <div class="reader-empty">
            <div class="reader-empty-icon" aria-hidden="true">!</div>
            <h2>Dokument se nepodařilo otevřít</h2>
            <p>${escapeHtml(data.message || "Soubor není dostupný.")}</p>
          </div>
        `;
        return;
      }
      const fileUrl = escapeHtml(archiveResourceUrl(data.file_url) || "#");
      let viewer = "";
      if (data.viewer_kind === "pdf") {
        viewer = `<iframe class="document-viewer" src="${fileUrl}" title="Celý dokument"></iframe>`;
      } else if (data.viewer_kind === "image") {
        viewer = `<div class="image-viewer"><img src="${fileUrl}" alt="Celý dokument"></div>`;
      } else {
        viewer = `
          <div class="download-card">
            <strong>Tento typ souboru se v prohlížeči bezpečně nezobrazuje.</strong>
            <a class="action-link" href="${fileUrl}">Stáhnout a otevřít soubor</a>
          </div>
        `;
      }
      const tags = (data.tags || []).map((tag) =>
        `<span class="badge">${escapeHtml(tag)}</span>`
      ).join("");
      const textPreview = data.text_preview
        ? `<details class="text-preview">
             <summary>Text nalezený v dokumentu${data.text_truncated ? " (zkrácený)" : ""}</summary>
             <div class="text-content">${escapeHtml(data.text_preview)}</div>
           </details>`
        : "";
      detailPane.innerHTML = `
        <article class="document-content">
          <header class="document-heading">
            <h2>${escapeHtml(data.title || "Dokument bez názvu")}</h2>
            <div class="detail-actions">
              <a class="action-link" target="_blank" rel="noopener" href="${fileUrl}">
                Otevřít samostatně
              </a>
              <span class="badge ${data.reading_status === "needs_review" ? "review" : "ok"}">
                ${escapeHtml(data.reading_status_label || "")}
              </span>
            </div>
          </header>
          <div class="detail-meta">
            <div class="meta-row"><div class="meta-label">Oblast</div><div class="meta-value">${escapeHtml(labelForDomain(data.domain))}</div></div>
            <div class="meta-row"><div class="meta-label">Typ</div><div class="meta-value">${escapeHtml(labelForType(data.document_type))}</div></div>
            <div class="meta-row"><div class="meta-label">Protistrana</div><div class="meta-value">${escapeHtml(data.counterparty || "nezjištěno")}</div></div>
            <div class="meta-row"><div class="meta-label">Související věc</div><div class="meta-value">${escapeHtml(data.related_asset || "nezjištěno")}</div></div>
            <div class="meta-row"><div class="meta-label">Uloženo</div><div class="meta-value">${escapeHtml(longDate(data.imported_at))}</div></div>
            <div class="meta-row"><div class="meta-label">Soubor</div><div class="meta-value">${escapeHtml(data.filename || "")} · ${escapeHtml(fileSize(data.size_bytes))}</div></div>
          </div>
          ${tags ? `<div class="tag-list">${tags}</div>` : ""}
          <div class="viewer-shell">${viewer}</div>
          ${textPreview}
        </article>
      `;
    }

    async function loadDetail(documentRef) {
      if (!documentRef) return;
      selectedDocumentRef = documentRef;
      updateActiveDocument();
      detailPane.innerHTML = `
        <div class="reader-empty">
          <div class="reader-empty-icon" aria-hidden="true">…</div>
          <h2>Otevírám dokument</h2>
        </div>
      `;
      document.body.classList.add("reader-open");
      try {
        const response = await fetch(archiveApiUrl(`/api/document?document_ref=${encodeURIComponent(documentRef)}`));
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.message || data.error || "Dokument není dostupný.");
        renderDetail(data);
      } catch (error) {
        renderDetail({ok: false, message: String(error)});
      }
    }

    function returnToCockpit() {
      const cockpitUrl = archiveBasePath ? window.location.origin : "http://127.0.0.1:8770";
      if (window.opener && !window.opener.closed) {
        try { window.opener.focus(); } catch (error) {}
        window.close();
        return;
      }
      window.location.href = cockpitUrl;
    }

    document.querySelectorAll("[data-reading-status]").forEach((button) => {
      button.addEventListener("click", () => {
        activeReadingStatus = button.dataset.readingStatus || "";
        activeDomain = "";
        loadDocuments();
      });
    });
    document.getElementById("searchBtn").addEventListener("click", loadDocuments);
    searchInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        loadDocuments();
      }
    });
    document.getElementById("refreshBtn").addEventListener("click", loadDocuments);
    document.getElementById("cockpitBtn").addEventListener("click", returnToCockpit);
    document.getElementById("newDocumentBtn").addEventListener("click", () => {
      window.location.href = archiveUrl("/");
    });
    document.getElementById("reviewBtn").addEventListener("click", () => {
      window.location.href = archiveUrl("/?mode=review");
    });
    document.getElementById("documentBackBtn").addEventListener("click", () => {
      document.body.classList.remove("reader-open");
    });
    loadDocuments();
  </script>
</body>
</html>
"""


def run_scandocu_server(
    host: str = "127.0.0.1",
    port: int = 8765,
    downloads_dir: Path = DEFAULT_DOWNLOADS_DIR,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> None:
    ScanDocuServer(downloads_dir=downloads_dir, vault_dir=vault_dir).serve(host=host, port=port)
