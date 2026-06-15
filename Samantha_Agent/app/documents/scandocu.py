from __future__ import annotations

import json
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

from .consistency_audit import AuditFact, best_asset_label, document_row_to_fact, primary_amount
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
    write_jsonl,
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
        return {
            "found": True,
            "source_mode": self.source_mode,
            "token": self.token,
            "source_name": self.source_path.name,
            "source_path": str(self.source_path),
            "working_path": str(relative_to_project(self.working_path)),
            "pdf_url": f"/pdf/{self.token}",
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
    documents = read_jsonl(vault_dir / "index" / "documents_index.jsonl")
    current = next((row for row in documents if str(row.get("document_id", "")) == document_id), None)
    if current is None:
        raise ValueError("puvodni dokument nebyl nalezen v indexu.")
    stored_path = PROJECT_ROOT / str(current.get("stored_path", ""))
    manifest_path = stored_path.parent / "manifest.json"
    manifest = read_json_file(manifest_path) if manifest_path.exists() else {}
    updated = {**current, **manifest}
    updated["title"] = safe_text(title) or candidate.title
    updated["domain"] = normalize_domain(domain or candidate.domain)
    register_document_domain(domain or candidate.domain, vault_dir=vault_dir)
    updated["document_type"] = safe_ascii_slug(document_type or candidate.document_type, default="document", limit=50)
    updated["counterparty"] = safe_text(counterparty)
    updated["related_asset"] = safe_text(related_asset)
    updated["case_id"] = safe_ascii_slug(case_id, default="", limit=100) if case_id else ""
    updated["tags"] = merge_tags(parse_tags(tags), [])
    reviewed_at = now_iso()
    updated["reviewed_at"] = reviewed_at
    updated["review_source"] = "scandocu_vault_review"
    updated["reading_status"] = "ok"
    updated["reading_status_updated_at"] = reviewed_at
    updated["reading_status_note"] = "Potvrzeno revizí ve ScanDocu."

    backup_dir = backup_review_document_metadata(vault_dir=vault_dir, document_id=document_id, manifest_path=manifest_path)
    write_json(manifest_path, updated)
    write_jsonl(
        vault_dir / "index" / "documents_index.jsonl",
        [updated if str(row.get("document_id", "")) == document_id else row for row in documents],
    )
    update_scandocu_candidate_status(
        candidate=candidate,
        status="reviewed",
        document_id=document_id,
        domain=updated["domain"],
        document_type=updated["document_type"],
        title=updated["title"],
        case_id=updated["case_id"],
        vault_dir=vault_dir,
    )
    append_scandocu_action(
        vault_dir=vault_dir,
        action="reviewed",
        token=candidate.token,
        source_path=candidate.source_path,
        source_sha256=sha256_file(candidate.working_path),
        document_id=document_id,
    )
    return {
        "status": "reviewed",
        "document_id": document_id,
        "domain": updated["domain"],
        "stored_path": str(relative_to_project(stored_path)),
        "manifest_path": str(relative_to_project(manifest_path)),
        "backup_dir": str(relative_to_project(backup_dir)),
        "message": "Metadata existujiciho dokumentu byla potvrzene aktualizovana.",
    }


def backup_review_document_metadata(vault_dir: Path, document_id: str, manifest_path: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = vault_dir / "index" / "review_backups" / f"{stamp}_{document_id}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    index_path = vault_dir / "index" / "documents_index.jsonl"
    if index_path.exists():
        shutil.copy2(index_path, backup_dir / "documents_index.jsonl")
    if manifest_path.exists():
        shutil.copy2(manifest_path, backup_dir / "manifest.json")
    return backup_dir


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
    data = read_json_file(candidate.metadata_path)
    data["status"] = status
    data["updated_at"] = now_iso()
    data["final_document_id"] = document_id
    data["title"] = safe_text(title)
    data["domain"] = normalize_domain(domain)
    data["document_type"] = safe_ascii_slug(document_type, default="document", limit=50)
    data["case_id"] = safe_ascii_slug(case_id, default="", limit=100) if case_id else ""
    write_json(candidate.metadata_path, data)


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
                        self.respond_html(SCANDOCU_HTML)
                        return
                    if parsed.path == "/api/next":
                        mode = parse_qs(parsed.query).get("mode", ["downloads"])[0]
                        if mode == "review":
                            candidate = prepare_next_stored_document_review(vault_dir=app.vault_dir)
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
                    if parsed.path.startswith("/pdf/"):
                        token = parsed.path.rsplit("/", 1)[-1]
                        candidate = get_scandocu_candidate(token=token, vault_dir=app.vault_dir)
                        self.respond_file(candidate.working_path, "application/pdf")
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

            def respond_file(self, path: Path, content_type: str) -> None:
                root = scandocu_processing_dir(app.vault_dir).resolve()
                resolved = path.resolve()
                if root not in resolved.parents:
                    raise ValueError("pozadovany soubor neni ve ScanDocu processing slozce.")
                payload = resolved.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(payload)))
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
    .checkline { display: flex; gap: 8px; align-items: flex-start; margin-top: 10px; color: #7c2d12; font-weight: 650; }
    .checkline input { width: auto; margin-top: 3px; }
    .hidden { display: none; }
    @media (max-width: 860px) {
      main { grid-template-columns: 1fr; height: auto; }
      iframe { height: 72vh; }
      .download-search-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <h1>ScanDocu</h1>
    <div class="actions" style="margin-top: 0;">
      <button class="secondary" id="cockpitBtn">Zpět do Cockpitu</button>
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
    <section>
      <iframe id="pdfFrame" title="Náhled PDF"></iframe>
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
      saveBtn: document.getElementById("saveBtn"),
      skipBtn: document.getElementById("skipBtn")
    };
    let current = null;
    let saving = false;
    const appMode = new URLSearchParams(window.location.search).get("mode") === "review" ? "review" : "downloads";
    const isReviewMode = appMode === "review";
    document.querySelector("h1").textContent = isReviewMode ? "ScanDocu Review" : "ScanDocu";
    document.getElementById("nextBtn").textContent = isReviewMode ? "Další uložený dokument" : "Další PDF";

    async function loadNext() {
      fields.status.textContent = isReviewMode ? "Hledám další uložený dokument..." : "Hledám další PDF...";
      fields.formWrap.classList.add("hidden");
      fields.completionActions.classList.add("hidden");
      fields.pdfFrame.removeAttribute("src");
      const res = await fetch(`/api/next?mode=${appMode}`);
      const data = await res.json();
      if (!data.found) {
        current = null;
        fields.status.textContent = data.message || "Nenalezeno.";
        return;
      }
      loadCandidate(data);
    }

    function loadCandidate(data) {
      current = data;
      fields.status.textContent = "Zkontroluj PDF a metadata.";
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
      fields.pdfFrame.src = data.pdf_url;
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
        const res = await fetch("/api/domains");
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
        const res = await fetch(`/api/search-downloads?q=${encodeURIComponent(query)}&date=${encodeURIComponent(date)}`);
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
      const res = await fetch("/api/select-download", {
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
        const res = await fetch("/api/save", {
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
      await fetch("/api/skip", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({token: current.token})
      });
      await loadNext();
    }

    function returnToCockpit() {
      const cockpitUrl = "http://127.0.0.1:8770";
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


def run_scandocu_server(
    host: str = "127.0.0.1",
    port: int = 8765,
    downloads_dir: Path = DEFAULT_DOWNLOADS_DIR,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> None:
    ScanDocuServer(downloads_dir=downloads_dir, vault_dir=vault_dir).serve(host=host, port=port)
