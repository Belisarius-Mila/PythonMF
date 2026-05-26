from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.reminders.store import DEFAULT_REMINDERS_PATH, save_reminder_draft
from app.reminders.tools import has_explicit_reminder_save_confirmation


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOCUMENTS_DIR = PROJECT_ROOT / "data" / "private" / "documents"
DEFAULT_MOBILE_DOCUMENT_INBOX = (
    Path.home()
    / "Library"
    / "Mobile Documents"
    / "iCloud~is~workflow~my~workflows"
    / "Documents"
    / "SamanthaDocumentInbox"
)
MAX_DOCUMENT_BYTES = 50 * 1024 * 1024
MAX_INDEX_TEXT_CHARS = 200_000
MAX_OUTPUT_SNIPPET_CHARS = 320
DEFAULT_OCR_MAX_PAGES = 8
DEFAULT_TABLE_MAX_PAGES = 8
MAX_TABLE_TEXT_CHARS = 60_000
OCR_RENDER_DPI = 200
OCR_TIMEOUT_SECONDS = 180
SAFE_ID_PATTERN = re.compile(r"[^a-z0-9_.-]+")
SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")
URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
RODNE_CISLO_PATTERN = re.compile(r"\b\d{6}/?\d{3,4}\b")

SAVE_WORDS = ("uloz", "ulož", "ulozit", "uložit", "zkopiruj", "zkopíruj", "archivuj")
DOCUMENT_WORDS = ("dokument", "pdf", "smlouv", "faktur", "pojist", "reviz", "servis")

DOMAIN_ALIASES = {
    "insurance": "insurance",
    "pojisteni": "insurance",
    "pojištění": "insurance",
    "pojistky": "insurance",
    "energy": "energy",
    "energie": "energy",
    "fve": "energy",
    "fotovoltaika": "energy",
    "home": "home",
    "dum": "home",
    "dům": "home",
    "kotel": "home",
    "car": "car",
    "auto": "car",
    "health": "health",
    "zdravi": "health",
    "zdraví": "health",
    "tax": "tax",
    "dane": "tax",
    "daně": "tax",
    "warranty": "warranty",
    "zaruka": "warranty",
    "záruka": "warranty",
    "other": "other",
    "ostatni": "other",
    "ostatní": "other",
}


@dataclass(frozen=True)
class TextExtractionResult:
    text: str
    method: str
    ocr_needed: bool
    warning: str = ""


@dataclass(frozen=True)
class TableExtractionResult:
    text: str
    method: str
    table_count: int = 0
    warning: str = ""


@dataclass(frozen=True)
class DocumentImportResult:
    document_id: str
    created: bool
    destination: Path
    manifest: Path
    message: str


@dataclass(frozen=True)
class DocumentPrintJobResult:
    print_job_id: str
    document_id: str
    queue_path: Path
    status: str
    message: str


@dataclass(frozen=True)
class MobileDocumentBatchResult:
    batch_id: str
    document_title: str
    page_count: int
    processing_dir: Path
    pdf_path: Path
    manifest_path: Path


def prepare_document_import_summary(
    source_path: str,
    document_hint: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    source = resolve_allowed_source(source_path)
    if isinstance(source, str):
        return source

    try:
        validate_source_file(source)
    except ValueError as exc:
        return f"Priprava importu dokumentu byla odmitnuta: {exc}"

    digest = sha256_file(source)
    extraction = extract_text(source)
    metadata = propose_metadata(
        source=source,
        text=extraction.text,
        document_hint=document_hint,
    )
    due_dates = find_due_date_candidates(extraction.text)
    duplicate = find_duplicate_by_sha(vault_dir=vault_dir, sha256=digest)

    lines = [
        "Navrh importu dokumentu (read-only):",
        f"- Soubor: {source.name}",
        f"- Velikost: {source.stat().st_size} B",
        f"- SHA256: {digest[:16]}...{digest[-8:]}",
        f"- Textova extrakce: {extraction.method}",
        f"- OCR potreba: {'ano' if extraction.ocr_needed else 'ne'}",
        f"- Navrzeny typ: {metadata['document_type']}",
        f"- Navrzena oblast: {metadata['domain']}",
        f"- Protistrana: {metadata['counterparty'] or 'nezjisteno'}",
        f"- Vazba na majetek/zarizeni: {metadata['related_asset'] or 'nezjisteno'}",
    ]
    suggested_tags = metadata.get("tags", [])
    if isinstance(suggested_tags, list) and suggested_tags:
        lines.append(f"- Navrzene tagy: {', '.join(safe_text(str(tag)) for tag in suggested_tags[:12])}")
    if duplicate:
        lines.append(f"- Duplicita: stejny hash uz je ulozen jako {duplicate.get('document_id')}")
    if extraction.warning:
        lines.append(f"- Poznamka: {extraction.warning}")

    lines.append("")
    lines.append("Kandidati na due date:")
    if due_dates:
        for item in due_dates[:8]:
            lines.append(
                "- "
                f"{item['date']} | {item['type']} | confidence={item['confidence']} | "
                f"{sanitize_output(str(item['context']))}"
            )
    else:
        lines.append("- Nenalezeny")

    lines.append("")
    lines.append(
        "Bezpecnost: nic nebylo zkopirovano ani zapsano. Pro definitivni zarazeni "
        "je potreba samostatne potvrzeny apply_document_import."
    )
    return "\n".join(lines)


def scan_document_inbox_summary(
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    max_items: int = 20,
) -> str:
    incoming = vault_dir / "inbox" / "incoming"
    if not incoming.exists():
        return (
            "Document inbox zatim neexistuje. Ocekavana slozka je "
            f"`{relative_to_project(incoming)}`."
        )
    if not incoming.is_dir():
        return f"Document inbox neni slozka: `{relative_to_project(incoming)}`."

    files = sorted(
        (path for path in incoming.iterdir() if path.is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not files:
        return (
            "Document inbox je prazdny.\n"
            f"- Slozka: `{relative_to_project(incoming)}`\n"
            "- Dalsi krok: nove PDF nebo dokument ulozit sem a potom spustit "
            "`prepare_document_import`."
        )

    shown = files[: max(1, max_items)]
    lines = [
        "Document inbox - cekajici soubory (read-only):",
        f"- Slozka: `{relative_to_project(incoming)}`",
        f"- Pocet cekajicich souboru: {len(files)}",
        "",
    ]
    for path in shown:
        stat = path.stat()
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        lines.append(
            "- "
            f"{safe_text(path.name)} | {stat.st_size} B | zmeneno {modified} | "
            f"`{relative_to_project(path)}`"
        )
    if len(files) > len(shown):
        lines.append(f"- ... dalsich {len(files) - len(shown)}")
    lines.extend(
        [
            "",
            "Dalsi krok: pro vybrany soubor pouzij read-only `prepare_document_import`.",
            "Bezpecnost: tento scan jen vypisuje lokalni soubory, nic nepresouva ani neindexuje.",
        ]
    )
    return "\n".join(lines)


def scan_mobile_document_inbox_summary(
    mobile_inbox_dir: Path = DEFAULT_MOBILE_DOCUMENT_INBOX,
    max_batches: int = 20,
) -> str:
    """Read-only scan of iPhone Shortcuts document capture inbox."""
    inbox = mobile_inbox_dir.expanduser()
    if not inbox.exists():
        return f"Mobile document inbox zatim neexistuje: `{safe_text(str(inbox))}`."
    if not inbox.is_dir():
        return f"Mobile document inbox neni slozka: `{safe_text(str(inbox))}`."

    process_request = inbox / "process_request.json"
    manifests = sorted(
        inbox.glob("scan_*_manifest.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not manifests:
        request_state = "ano" if process_request.exists() else "ne"
        return (
            "Mobile document inbox je prazdny.\n"
            f"- Process request: {request_state}\n"
            f"- Slozka: `{safe_text(str(inbox))}`\n"
            "- Dalsi krok: na iPhonu spustit zkratku `Skenovat dokument pro Samanthu v4`."
        )

    lines = [
        "Mobile document inbox - zachycene davky (read-only):",
        f"- Slozka: `{safe_text(str(inbox))}`",
        f"- Process request: {'ano' if process_request.exists() else 'ne'}",
        f"- Pocet manifestu: {len(manifests)}",
        "",
    ]
    shown = manifests[: max(1, max_batches)]
    for manifest_path in shown:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            lines.append(f"- {safe_text(manifest_path.name)} | chyba manifestu: {safe_text(str(exc))}")
            continue

        batch_id = safe_text(str(manifest.get("batch_id", ""))).strip()
        title = safe_text(str(manifest.get("document_title", ""))).strip() or "bez nazvu"
        expected_count = safe_text(str(manifest.get("page_count", ""))).strip() or "nezjisteno"
        if batch_id:
            pages = sorted(inbox.glob(f"{batch_id}_page_*"))
        else:
            pages = []
        modified = datetime.fromtimestamp(manifest_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        lines.extend(
            [
                f"- Batch: {batch_id or safe_text(manifest_path.stem)}",
                f"  Nazev: {title}",
                f"  Stranky: {len(pages)} nalezeno / {expected_count} podle manifestu",
                f"  Manifest: {safe_text(manifest_path.name)} | zmeneno {modified}",
            ]
        )
        if pages:
            page_names = ", ".join(safe_text(path.name) for path in pages[:8])
            if len(pages) > 8:
                page_names += f", ... dalsich {len(pages) - 8}"
            lines.append(f"  Soubory: {page_names}")
    if len(manifests) > len(shown):
        lines.append(f"- ... dalsich {len(manifests) - len(shown)}")
    lines.extend(
        [
            "",
            "Bezpecnost: tento scan jen vypisuje manifesty a nazvy souboru, nic nepresouva ani necte obsah fotek.",
        ]
    )
    return "\n".join(lines)


def prepare_mobile_document_batch_summary(
    batch_id: str = "",
    mobile_inbox_dir: Path = DEFAULT_MOBILE_DOCUMENT_INBOX,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    try:
        result = prepare_mobile_document_batch(
            batch_id=batch_id,
            mobile_inbox_dir=mobile_inbox_dir,
            vault_dir=vault_dir,
        )
    except ValueError as exc:
        return f"Priprava mobilniho dokumentu byla odmitnuta: {exc}"

    return (
        "Mobilni dokument je pripraveny ke kontrole/importu.\n"
        f"- Batch: {safe_text(result.batch_id)}\n"
        f"- Nazev: {safe_text(result.document_title)}\n"
        f"- Stranky: {result.page_count}\n"
        f"- Pracovni slozka: `{relative_to_project(result.processing_dir)}`\n"
        f"- PDF: `{relative_to_project(result.pdf_path)}`\n"
        f"- Manifest: `{relative_to_project(result.manifest_path)}`\n"
        "- Zdrojove fotky v iCloud inboxu zustaly beze zmeny.\n"
        "Dalsi krok: zkontrolovat PDF a potom teprve spustit read-only "
        "`prepare_document_import` nad vytvorenym PDF."
    )


def prepare_mobile_document_batch(
    batch_id: str = "",
    mobile_inbox_dir: Path = DEFAULT_MOBILE_DOCUMENT_INBOX,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> MobileDocumentBatchResult:
    inbox = mobile_inbox_dir.expanduser().resolve()
    if not inbox.exists() or not inbox.is_dir():
        raise ValueError(f"mobile inbox neexistuje nebo neni slozka: {inbox}")

    manifest_path, manifest = select_mobile_batch_manifest(inbox=inbox, batch_id=batch_id)
    raw_batch_id = safe_text(str(manifest.get("batch_id", ""))).strip()
    if not raw_batch_id or not re.fullmatch(r"[A-Za-z0-9_.-]+", raw_batch_id):
        raise ValueError("manifest nema bezpecny batch_id.")
    document_title = safe_text(str(manifest.get("document_title", ""))).strip() or raw_batch_id
    expected_count = int(str(manifest.get("page_count", "0")).strip() or "0")
    pages = sorted(
        inbox.glob(f"{raw_batch_id}_page_*"),
        key=mobile_page_sort_key,
    )
    if not pages:
        raise ValueError(f"pro batch {raw_batch_id} nebyly nalezeny zadne stranky.")
    if expected_count and len(pages) != expected_count:
        raise ValueError(
            f"pocet stran nesedi: nalezeno {len(pages)}, manifest uvadi {expected_count}."
        )
    for page in pages:
        validate_source_file(page)

    safe_batch_id = safe_slug(raw_batch_id, default="mobile-scan", limit=80)
    work_root = vault_dir / "mobile_inbox" / "processing"
    processing_dir = next_available_path(work_root / safe_batch_id)
    originals_dir = processing_dir / "originals"
    normalized_dir = processing_dir / "normalized_pages"
    originals_dir.mkdir(parents=True, exist_ok=False)
    normalized_dir.mkdir(parents=True, exist_ok=False)

    copied_originals: list[str] = []
    normalized_pages: list[Path] = []
    for index, page in enumerate(pages, start=1):
        original_target = originals_dir / f"page_{index:03d}{safe_image_suffix(page)}"
        shutil.copy2(page, original_target)
        copied_originals.append(str(relative_to_project(original_target)))
        normalized_target = normalized_dir / f"page_{index:03d}.jpg"
        normalize_mobile_document_page(page, normalized_target)
        normalized_pages.append(normalized_target)

    pdf_path = processing_dir / f"{safe_batch_id}.pdf"
    build_pdf_from_images(normalized_pages, pdf_path)
    prepared_at = datetime.now(timezone.utc).replace(microsecond=0)
    processing_manifest = {
        "schema_version": "1",
        "status": "prepared",
        "prepared_at": prepared_at.isoformat(),
        "batch_id": raw_batch_id,
        "document_title": document_title,
        "source_manifest": str(manifest_path),
        "source_pages": [str(page) for page in pages],
        "original_copies": copied_originals,
        "normalized_pages": [str(relative_to_project(path)) for path in normalized_pages],
        "pdf_path": str(relative_to_project(pdf_path)),
        "source_preserved": True,
        "do_not_commit": True,
    }
    output_manifest = processing_dir / "manifest.json"
    output_manifest.write_text(
        json.dumps(processing_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    append_jsonl(vault_dir / "index" / "mobile_batches.jsonl", processing_manifest)

    return MobileDocumentBatchResult(
        batch_id=raw_batch_id,
        document_title=document_title,
        page_count=len(pages),
        processing_dir=processing_dir,
        pdf_path=pdf_path,
        manifest_path=output_manifest,
    )


def format_document_inbox_reminder(vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> str:
    incoming = vault_dir / "inbox" / "incoming"
    try:
        pending_count = sum(1 for path in incoming.iterdir() if path.is_file())
    except OSError:
        pending_count = 0

    if pending_count <= 0:
        return "Document inbox: zadne cekajici soubory."
    return (
        "Document inbox: "
        f"{pending_count} cekajici soubor(y) v `data/private/documents/inbox/incoming/`. "
        "Pri startu na to Milu upozorni a pro detaily pouzij read-only tool "
        "`scan_document_inbox`."
    )


def propose_document_inbox_cleanup_summary(
    source_path: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    source = resolve_inbox_source_file(source_path=source_path, vault_dir=vault_dir)
    if isinstance(source, str):
        return source

    digest = sha256_file(source)
    imported = find_duplicate_by_sha(vault_dir=vault_dir, sha256=digest)
    processed_dir = vault_dir / "inbox" / "processed"

    lines = [
        "Navrh vyreseni dokumentu v inboxu (read-only):",
        f"- Dokument: {safe_text(source.name)}",
        f"- Inbox: `{relative_to_project(source.parent)}`",
    ]
    if imported:
        lines.extend(
            [
                "- Stav: dokument se stejnym obsahem uz je importovany ve vaultu.",
                f"- Document ID: {safe_text(str(imported.get('document_id', '')))}",
            ]
        )
    else:
        lines.append(
            "- Stav: stejny obsah jsem v indexu vaultu nenasla; mazani nedoporucuji."
        )

    lines.extend(
        [
            "",
            f"Dokument {safe_text(source.name)} je zpracovan. Presunout do slozky "
            f"`{relative_to_project(processed_dir)}`?",
            "1. presunout",
            "2. smazat",
            "",
            "Pro volbu 1 priprav Milovi vetu:",
            f"`Potvrzuji, presunout dokument {source.name} do processed.`",
            "",
            "Pro volbu 2 se nejdriv zeptej:",
            f"`Opravdu chcete dokument {source.name} smazat z inboxu?`",
            "A az po odpovedi ano pouzij vetu:",
            f"`Ano, smazat dokument {source.name} z inboxu.`",
            "",
            "Bezpecnost: tento navrh nic nepresouva ani nemaze.",
        ]
    )
    return "\n".join(lines)


def resolve_document_inbox_item_summary(
    source_path: str,
    action: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    source = resolve_inbox_source_file(source_path=source_path, vault_dir=vault_dir)
    if isinstance(source, str):
        return source

    normalized_action = action.casefold().strip()
    if normalized_action in {"move", "presun", "presunout", "přesun", "přesunout"}:
        return move_document_inbox_item(
            source=source,
            confirmation_text=confirmation_text,
            user_confirmed=user_confirmed,
            vault_dir=vault_dir,
        )
    if normalized_action in {"delete", "smazat", "smaz", "smaž", "remove", "odstranit"}:
        return delete_document_inbox_item(
            source=source,
            confirmation_text=confirmation_text,
            user_confirmed=user_confirmed,
            vault_dir=vault_dir,
        )
    return "Neznam akci. Pouzij `move` pro presun nebo `delete` pro smazani."


def inspect_document_text_summary(
    source_path: str = "",
    document_id: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    resolved = resolve_document_source(
        source_path=source_path,
        document_id=document_id,
        vault_dir=vault_dir,
    )
    if isinstance(resolved, str):
        return resolved

    extraction = extract_text(resolved)
    due_dates = find_due_date_candidates(extraction.text)
    lines = [
        "Inspekce dokumentu (read-only):",
        f"- Soubor: {resolved.name}",
        f"- Textova extrakce: {extraction.method}",
        f"- OCR potreba: {'ano' if extraction.ocr_needed else 'ne'}",
    ]
    if extraction.warning:
        lines.append(f"- Poznamka: {extraction.warning}")
    lines.append("")
    lines.append("Kandidati na due date:")
    if due_dates:
        for item in due_dates[:12]:
            lines.append(
                "- "
                f"{item['date']} | {item['type']} | confidence={item['confidence']} | "
                f"reminder={'ano' if item['create_reminder_candidate'] else 'ne'} | "
                f"{sanitize_output(str(item['context']))}"
            )
    else:
        lines.append("- Nenalezeny")

    snippet = sanitize_output(extraction.text[:1000].strip())
    lines.append("")
    lines.append("Nahled textu:")
    lines.append(snippet if snippet else "- Text nebyl ziskany.")
    lines.append("")
    lines.append("Bezpecnost: dokument nebyl presunut, zkopirovan ani ulozen do memory.")
    return "\n".join(lines)


def apply_document_import_file(
    source_path: str,
    target_domain: str,
    document_type: str = "",
    counterparty: str = "",
    related_asset: str = "",
    tags: str = "",
    document_id: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    now: datetime | None = None,
) -> DocumentImportResult:
    source = resolve_allowed_source(source_path)
    if isinstance(source, str):
        raise ValueError(source)
    validate_source_file(source)

    normalized_domain = normalize_domain(target_domain)
    extraction = extract_text(source)
    metadata = propose_metadata(
        source=source,
        text=extraction.text,
        document_hint=document_type,
        target_domain=normalized_domain,
        counterparty=counterparty,
        related_asset=related_asset,
    )
    if document_type.strip():
        metadata["document_type"] = safe_slug(document_type, default="document", limit=50)
    digest = sha256_file(source)
    duplicate = find_duplicate_by_sha(vault_dir=vault_dir, sha256=digest)
    if duplicate:
        existing_path = PROJECT_ROOT / str(duplicate.get("stored_path", ""))
        return DocumentImportResult(
            document_id=str(duplicate.get("document_id", "")),
            created=False,
            destination=existing_path,
            manifest=existing_path.parent / "manifest.json",
            message="Dokument se stejnym obsahem uz je ve vaultu ulozen.",
        )

    archive_time = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    safe_document_id = document_id.strip() or build_document_id(
        source=source,
        domain=normalized_domain,
        document_type=str(metadata["document_type"]),
        digest=digest,
        imported_at=archive_time,
    )
    safe_document_id = safe_slug(safe_document_id, default="document", limit=140)

    document_dir = vault_dir / "vault" / normalized_domain / safe_document_id
    document_dir.mkdir(parents=True, exist_ok=True)
    stored_name = safe_filename(source.name)
    destination = document_dir / stored_name
    counter = 1
    while destination.exists():
        counter += 1
        destination = document_dir / f"{destination.stem}-{counter}{destination.suffix}"
    shutil.copy2(source, destination)

    due_dates = find_due_date_candidates(extraction.text)
    explicit_tags = parse_tags(tags)
    suggested_tags = metadata.get("tags", [])
    if not isinstance(suggested_tags, list):
        suggested_tags = []

    record = {
        "document_id": safe_document_id,
        "original_filename": source.name,
        "stored_path": str(relative_to_project(destination)),
        "domain": normalized_domain,
        "document_type": metadata["document_type"],
        "counterparty": safe_text(str(metadata.get("counterparty") or "")),
        "related_asset": safe_text(str(metadata.get("related_asset") or "")),
        "tags": merge_tags(explicit_tags, [str(tag) for tag in suggested_tags]),
        "sha256": digest,
        "size_bytes": source.stat().st_size,
        "imported_at": archive_time.isoformat(),
        "text_extraction": {
            "method": extraction.method,
            "ocr_needed": extraction.ocr_needed,
            "warning": extraction.warning,
            "indexed_chars": min(len(extraction.text), MAX_INDEX_TEXT_CHARS),
        },
        "safety_flags": {
            "local_sensitive_archive": True,
            "do_not_commit": True,
            "private_text_index": True,
        },
    }
    manifest_path = document_dir / "manifest.json"
    write_json(manifest_path, record)

    index_dir = vault_dir / "index"
    append_jsonl(index_dir / "documents_index.jsonl", record)
    append_jsonl(
        index_dir / "text_index.jsonl",
        {
            "document_id": safe_document_id,
            "stored_path": str(relative_to_project(destination)),
            "text": extraction.text[:MAX_INDEX_TEXT_CHARS],
            "text_truncated": len(extraction.text) > MAX_INDEX_TEXT_CHARS,
        },
    )
    for candidate in due_dates:
        append_jsonl(
            index_dir / "due_dates.jsonl",
            {
                "document_id": safe_document_id,
                **candidate,
            },
        )

    return DocumentImportResult(
        document_id=safe_document_id,
        created=True,
        destination=destination,
        manifest=manifest_path,
        message="Dokument byl zkopirovan do soukromeho dokumentoveho vaultu a zaindexovan.",
    )


def search_private_documents_summary(
    query: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    max_results: int = 5,
) -> str:
    terms = [term for term in tokenize(query) if len(term) >= 2]
    if not terms:
        return "Zadej konkretnejsi dotaz pro hledani v dokumentech."

    documents = {item["document_id"]: item for item in read_jsonl(vault_dir / "index" / "documents_index.jsonl")}
    text_rows = read_jsonl(vault_dir / "index" / "text_index.jsonl")
    if not documents and not text_rows:
        return "V private document vaultu zatim neni zadny index dokumentu."

    results: list[tuple[int, dict[str, Any], str]] = []
    for row in text_rows:
        document_id = str(row.get("document_id", ""))
        metadata = documents.get(document_id, {"document_id": document_id})
        haystack = " ".join(
            [
                str(row.get("text", "")),
                str(metadata.get("original_filename", "")),
                str(metadata.get("document_id", "")),
                str(metadata.get("stored_path", "")),
                str(metadata.get("document_type", "")),
                str(metadata.get("domain", "")),
                str(metadata.get("counterparty", "")),
                str(metadata.get("related_asset", "")),
                " ".join(str(tag) for tag in metadata.get("tags", []) if isinstance(tag, str)),
            ]
        )
        haystack_folded = haystack.casefold()
        score = sum(haystack_folded.count(term) for term in terms)
        if score <= 0:
            continue
        snippet = build_snippet(str(row.get("text", "")), terms)
        if not snippet.strip():
            snippet = "Text zatim neni k dispozici; dokument je indexovan jen podle metadat a potrebuje OCR."
        results.append((score, metadata, snippet))

    if not results:
        return "V private document vaultu jsem nenasla shodu."

    lines = ["Vysledky hledani v private document vaultu:"]
    for score, metadata, snippet in sorted(results, key=lambda item: item[0], reverse=True)[:max_results]:
        document_id = str(metadata.get("document_id", ""))
        inbox_action = latest_inbox_action_for_document(vault_dir=vault_dir, document_id=document_id)
        lines.extend(
            [
                f"- Document ID: {safe_text(document_id)}",
                f"  Soubor: {safe_text(str(metadata.get('original_filename', '')))}",
                f"  Typ/oblast: {safe_text(str(metadata.get('document_type', '')))} / {safe_text(str(metadata.get('domain', '')))}",
                f"  Protistrana: {safe_text(str(metadata.get('counterparty', '')) or 'nezjisteno')}",
                f"  Cesta: {safe_text(str(metadata.get('stored_path', '')))}",
                f"  Snippet: {sanitize_output(snippet)}",
            ]
        )
        if inbox_action:
            action = str(inbox_action.get("action", ""))
            to_path = str(inbox_action.get("to_path", ""))
            if action == "move_to_processed" and to_path:
                lines.append(f"  Zdrojova kopie: {safe_text(to_path)}")
            elif action == "delete_from_inbox":
                lines.append("  Zdrojova kopie: smazana z inboxu po potvrzeni")
    lines.append("")
    lines.append("Bezpecnost: vysledky jsou jen metadata a kratke snippety, ne cele dokumenty.")
    return "\n".join(lines)


def prepare_document_print_job_summary(
    query: str = "",
    document_id: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    try:
        result = prepare_document_print_job(
            query=query,
            document_id=document_id,
            vault_dir=vault_dir,
        )
    except ValueError as exc:
        return f"Priprava tisku byla odmitnuta: {exc}"

    return (
        "Dokument je pripraven k tisku.\n"
        f"- Print job ID: {safe_text(result.print_job_id)}\n"
        f"- Document ID: {safe_text(result.document_id)}\n"
        f"- Kopie k tisku: `{safe_text(str(relative_to_project(result.queue_path)))}`\n"
        "- Originál ve vaultu zustal beze zmeny.\n"
        "Pro samotny tisk pouzij samostatne potvrzeni: "
        f"`Potvrzuji, vytiskni print job {result.print_job_id}.`"
    )


def prepare_document_print_job(
    query: str = "",
    document_id: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    now: datetime | None = None,
) -> DocumentPrintJobResult:
    metadata = select_single_document_for_print(
        query=query,
        document_id=document_id,
        vault_dir=vault_dir,
    )
    safe_document_id = str(metadata.get("document_id", ""))
    stored_path = PROJECT_ROOT / str(metadata.get("stored_path", ""))
    if not stored_path.exists() or not stored_path.is_file():
        raise ValueError("dokument je v indexu, ale soubor ve vaultu nebyl nalezen.")
    validate_source_file(stored_path)

    prepared_at = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    queue_dir = vault_dir / "print_queue"
    queue_dir.mkdir(parents=True, exist_ok=True)
    print_job_id = build_print_job_id(safe_document_id, prepared_at)
    queue_name = f"{print_job_id}-{safe_filename(stored_path.name)}"
    queue_path = next_available_path(queue_dir / queue_name)
    shutil.copy2(stored_path, queue_path)

    record = {
        "print_job_id": print_job_id,
        "document_id": safe_document_id,
        "source_path": str(metadata.get("stored_path", "")),
        "queue_path": str(relative_to_project(queue_path)),
        "status": "prepared",
        "created_at": prepared_at.isoformat(),
        "original_filename": metadata.get("original_filename", ""),
        "do_not_commit": True,
    }
    append_jsonl(vault_dir / "index" / "print_jobs.jsonl", record)
    return DocumentPrintJobResult(
        print_job_id=print_job_id,
        document_id=safe_document_id,
        queue_path=queue_path,
        status="prepared",
        message="prepared",
    )


def run_document_print_job_summary(
    print_job_id: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    printer: str = "",
    print_runner: Any | None = None,
) -> str:
    try:
        result = run_document_print_job(
            print_job_id=print_job_id,
            user_confirmed=user_confirmed,
            confirmation_text=confirmation_text,
            vault_dir=vault_dir,
            printer=printer,
            print_runner=print_runner,
        )
    except ValueError as exc:
        return f"Tisk byl odmitnut: {exc}"

    return result.message


def run_document_print_job(
    print_job_id: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    printer: str = "",
    print_runner: Any | None = None,
) -> DocumentPrintJobResult:
    safe_print_job_id = safe_slug(print_job_id, default="", limit=120)
    if not safe_print_job_id:
        raise ValueError("chybi print_job_id.")
    if not user_confirmed or not has_explicit_document_print_confirmation(
        print_job_id=safe_print_job_id,
        confirmation_text=confirmation_text,
    ):
        raise ValueError(
            "pro tisk potrebuji samostatne potvrzeni v aktualni zprave. "
            f"Pouzij: Potvrzuji, vytiskni print job {safe_print_job_id}."
        )

    job = latest_print_job(vault_dir=vault_dir, print_job_id=safe_print_job_id)
    if not job:
        raise ValueError(f"print job {safe_print_job_id} nebyl nalezen.")
    if str(job.get("status", "")) not in {"prepared", "failed"}:
        raise ValueError(f"print job {safe_print_job_id} neni ve stavu pripravenem k tisku.")

    queue_path = PROJECT_ROOT / str(job.get("queue_path", ""))
    queue_dir = (vault_dir / "print_queue").resolve()
    try:
        resolved_queue_path = queue_path.resolve(strict=True)
    except FileNotFoundError as exc:
        append_print_job_status(
            vault_dir=vault_dir,
            job=job,
            status="failed",
            message="kopie k tisku nebyla nalezena.",
        )
        raise ValueError("kopie k tisku nebyla nalezena v print_queue.") from exc
    if resolved_queue_path.parent != queue_dir:
        raise ValueError("print job ukazuje mimo povolenou slozku print_queue.")

    command = ["lp"]
    safe_printer = printer.strip()
    if safe_printer:
        if not re.fullmatch(r"[A-Za-z0-9_.@:+-]{1,120}", safe_printer):
            raise ValueError("nazev tiskarny obsahuje nepovolene znaky.")
        command.extend(["-d", safe_printer])
    command.append(str(resolved_queue_path))

    runner = print_runner or subprocess.run
    try:
        completed = runner(
            command,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        append_print_job_status(
            vault_dir=vault_dir,
            job=job,
            status="failed",
            message=f"systemovy tiskovy prikaz selhal: {exc}",
        )
        return DocumentPrintJobResult(
            print_job_id=safe_print_job_id,
            document_id=str(job.get("document_id", "")),
            queue_path=resolved_queue_path,
            status="failed",
            message=(
                "Tisk se nedari: systemovy tiskovy prikaz selhal. "
                "Zkontroluj tiskarnu/frontu a pripadne to zkus znovu."
            ),
        )

    if completed.returncode != 0:
        stderr = safe_text(str(getattr(completed, "stderr", "")))[:300]
        append_print_job_status(
            vault_dir=vault_dir,
            job=job,
            status="failed",
            message=f"lp vratil kod {completed.returncode}: {stderr}",
        )
        return DocumentPrintJobResult(
            print_job_id=safe_print_job_id,
            document_id=str(job.get("document_id", "")),
            queue_path=resolved_queue_path,
            status="failed",
            message=(
                "Tisk se nedari: macOS tiskovy prikaz vratil chybu. "
                f"Detail: {stderr or 'bez detailu'}"
            ),
        )

    resolved_queue_path.unlink()
    append_print_job_status(
        vault_dir=vault_dir,
        job=job,
        status="printed",
        message="tisk predan systemu, kopie z print_queue smazana.",
    )
    return DocumentPrintJobResult(
        print_job_id=safe_print_job_id,
        document_id=str(job.get("document_id", "")),
        queue_path=resolved_queue_path,
        status="printed",
        message=(
            f"Tisk byl predan systemu. Print job: {safe_print_job_id}. "
            "Kopie v print_queue byla po uspesnem predani tisku smazana; "
            "original ve vaultu zustal zachovan."
        ),
    )


def select_single_document_for_print(
    query: str,
    document_id: str,
    vault_dir: Path,
) -> dict[str, Any]:
    documents = read_jsonl(vault_dir / "index" / "documents_index.jsonl")
    if not documents:
        raise ValueError("ve vaultu zatim neni zadny index dokumentu.")

    safe_document_id = safe_slug(document_id, default="", limit=140)
    if safe_document_id:
        matches = [item for item in documents if item.get("document_id") == safe_document_id]
        if not matches:
            raise ValueError(f"document_id {safe_document_id} nebyl nalezen.")
        return matches[0]

    terms = [term for term in tokenize(query) if len(term) >= 2]
    if not terms:
        raise ValueError("zadej document_id nebo konkretni dotaz pro vyhledani dokumentu.")

    text_by_id = {
        str(row.get("document_id", "")): str(row.get("text", ""))
        for row in read_jsonl(vault_dir / "index" / "text_index.jsonl")
    }
    scored: list[tuple[int, dict[str, Any]]] = []
    for item in documents:
        haystack = " ".join(
            [
                str(item.get("document_id", "")),
                str(item.get("original_filename", "")),
                str(item.get("stored_path", "")),
                str(item.get("document_type", "")),
                str(item.get("domain", "")),
                str(item.get("counterparty", "")),
                str(item.get("related_asset", "")),
                " ".join(str(tag) for tag in item.get("tags", []) if isinstance(tag, str)),
                text_by_id.get(str(item.get("document_id", "")), ""),
            ]
        ).casefold()
        score = sum(haystack.count(term) for term in terms)
        if score > 0:
            scored.append((score, item))

    if not scored:
        raise ValueError("nenasla jsem dokument odpovidajici dotazu.")
    scored.sort(key=lambda item: item[0], reverse=True)
    top_score = scored[0][0]
    top_matches = [item for score, item in scored if score == top_score]
    if len(top_matches) > 1:
        choices = ", ".join(safe_text(str(item.get("document_id", ""))) for item in top_matches[:5])
        raise ValueError(
            "dotaz neni jednoznacny. Nejdrive vyber konkretni document_id. "
            f"Kandidati: {choices}"
        )
    return top_matches[0]


def build_print_job_id(document_id: str, created_at: datetime) -> str:
    compact_time = created_at.strftime("%Y%m%d%H%M%S")
    return safe_slug(f"print-{compact_time}-{document_id}", default="print-job", limit=120)


def latest_print_job(vault_dir: Path, print_job_id: str) -> dict[str, Any] | None:
    jobs = read_jsonl(vault_dir / "index" / "print_jobs.jsonl")
    for item in reversed(jobs):
        if item.get("print_job_id") == print_job_id:
            return item
    return None


def append_print_job_status(
    vault_dir: Path,
    job: dict[str, Any],
    status: str,
    message: str,
) -> None:
    updated = dict(job)
    updated["status"] = status
    updated["message"] = message
    updated["updated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    append_jsonl(vault_dir / "index" / "print_jobs.jsonl", updated)


def has_explicit_document_print_confirmation(
    print_job_id: str,
    confirmation_text: str,
) -> bool:
    normalized = normalize_confirmation_text(confirmation_text)
    safe_print_job_id = normalize_confirmation_text(print_job_id)
    return (
        safe_print_job_id in normalized
        and any(word in normalized for word in ("vytisk", "tisk", "print"))
        and any(word in normalized for word in ("potvrzuji", "ano"))
    )


def document_vault_status_summary(
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    documents = read_jsonl(vault_dir / "index" / "documents_index.jsonl")
    due_dates = read_jsonl(vault_dir / "index" / "due_dates.jsonl")
    inbox_actions = read_jsonl(vault_dir / "index" / "inbox_actions.jsonl")

    domain_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    for item in documents:
        domain = safe_slug(str(item.get("domain", "")), default="other", limit=40)
        document_type = safe_slug(str(item.get("document_type", "")), default="document", limit=60)
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        type_counts[document_type] = type_counts.get(document_type, 0) + 1

    incoming_count = count_files(vault_dir / "inbox" / "incoming")
    processed_count = count_files(vault_dir / "inbox" / "processed")
    rejected_count = count_files(vault_dir / "inbox" / "rejected")
    reminder_candidate_count = sum(
        1 for item in due_dates if bool(item.get("create_reminder_candidate"))
    )
    moved_count = sum(1 for item in inbox_actions if item.get("action") == "move_to_processed")
    deleted_count = sum(1 for item in inbox_actions if item.get("action") == "delete_from_inbox")
    resolved_from_incoming_count = moved_count + deleted_count
    linked_action_document_ids = {
        str(item.get("document_id", ""))
        for item in inbox_actions
        if str(item.get("document_id", "")).strip()
    }
    action_times = [
        parsed
        for item in inbox_actions
        if (parsed := parse_iso_datetime(str(item.get("action_at", "")))) is not None
    ]
    now = datetime.now(timezone.utc)
    recent_30_count = sum(1 for item in action_times if item >= now - timedelta(days=30))
    if action_times:
        audit_period = (
            f"od {format_status_datetime(min(action_times))} "
            f"do {format_status_datetime(max(action_times))}"
        )
    else:
        audit_period = "zatim zadne auditni akce"

    lines = [
        "Document vault status (read-only):",
        f"- Dokumentu v indexu: {len(documents)}",
        f"- Inbox incoming (ceka na zpracovani): {incoming_count}",
        f"- Zdrojove kopie ulozene v processed: {processed_count}",
        f"- Rejected: {rejected_count}",
        f"- Datumovych/due-date kandidatu celkem v indexu: {len(due_dates)}",
        f"- Z toho kandidatu vhodnych na pripominku: {reminder_candidate_count}",
        f"- Inbox audit obdobi: {audit_period}",
        f"- Inbox audit akci celkem v tomto obdobi: {len(inbox_actions)}",
        f"- Inbox audit akci za poslednich 30 dni: {recent_30_count}",
        f"- Vyresenych souboru z incoming celkem: {resolved_from_incoming_count}",
        f"- Z toho presunuto do processed (odstraneno z incoming, soubor zustal ulozeny): {moved_count}",
        f"- Z toho trvale smazano po druhem potvrzeni: {deleted_count}",
        f"- Dokumentu s auditni stopou zdrojove kopie celkem: {len(linked_action_document_ids)}",
        "",
        "Dokumenty podle oblasti:",
    ]
    if domain_counts:
        lines.extend(
            f"- {safe_text(domain)}: {count}"
            for domain, count in sorted(domain_counts.items())
        )
    else:
        lines.append("- zadne")

    lines.append("")
    lines.append("Nejcastejsi typy dokumentu:")
    if type_counts:
        lines.extend(
            f"- {safe_text(document_type)}: {count}"
            for document_type, count in sorted(
                type_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )[:8]
        )
    else:
        lines.append("- zadne")

    lines.append("")
    if incoming_count:
        lines.append(
            "Dalsi krok: v inboxu jsou cekajici soubory; pouzij `scan_document_inbox`."
        )
    else:
        lines.append("Dalsi krok: inbox je prazdny; cekat na dalsi dokument.")
    lines.append(
        "Poznamka: status nezobrazuje zmeny od posledniho spusteni; jde o aktualni "
        "celkove pocty v indexech."
    )
    lines.append(
        "Poznamka: datumovy/due-date kandidat je jen nalezene datum v dokumentu, "
        "ne ulozena pripominka."
    )
    lines.append(
        "Bezpecnost: status vraci jen agregovane pocty a typy, ne obsah dokumentu."
    )
    return "\n".join(lines)


def save_document_due_reminder_summary(
    document_id: str,
    title: str,
    due_date: str,
    due_date_type: str = "deadline",
    notes: str = "",
    priority: str = "high",
    user_confirmed: bool = False,
    confirmation_text: str = "",
    reminders_path: Path = DEFAULT_REMINDERS_PATH,
) -> str:
    document_id = safe_slug(document_id, default="document", limit=140)
    due_date = require_iso_date(due_date)
    due_type = safe_slug(due_date_type, default="deadline", limit=50)
    reminder_id = f"document-{document_id}-{due_type}-{due_date}"

    if not user_confirmed or not has_explicit_reminder_save_confirmation(
        reminder_id=reminder_id,
        confirmation_text=confirmation_text,
    ):
        return (
            "Nejdrive potrebuji samostatne potvrzeni od Mily v aktualni zprave. "
            f"Potvrzeni musi obsahovat id pripominky {reminder_id} a jasny souhlas "
            "s ulozenim pripominky. Bez toho na disk nic nezapisuji."
        )

    reminder = {
        "id": reminder_id,
        "title": safe_text(title)[:160] or f"Zkontrolovat dokument {document_id}",
        "notes": safe_text(notes)[:700]
        or "Pripominka vznikla z potvrzeneho due date kandidata v private document vaultu.",
        "due_date": due_date,
        "priority": safe_priority(priority),
        "status": "open",
        "source": {
            "type": "private_document",
            "uid": document_id,
            "date": "",
            "sender": "Private document vault",
        },
        "links": [],
        "attachments": [],
    }
    try:
        result = save_reminder_draft(reminder, path=reminders_path)
    except ValueError as exc:
        return f"Ulozeni dokumentove pripominky bylo odmitnuto: {exc}"

    if result.created:
        return (
            f"Ulozeno: {result.reminder_id}. "
            "Byla ulozena jen bezpecna pripominka z potvrzeneho due date; "
            "obsah dokumentu nebyl ulozen do memory."
        )
    return f"Neulozeno: {result.reminder_id}. {result.message}"


def has_explicit_document_import_confirmation(
    filename: str,
    target_domain: str,
    confirmation_text: str,
) -> bool:
    normalized = normalize_confirmation_text(confirmation_text)
    safe_filename = normalize_confirmation_text(filename)
    original_domain = normalize_confirmation_text(target_domain)
    canonical_domain = normalize_confirmation_text(normalize_domain(target_domain))
    return (
        safe_filename in normalized
        and (canonical_domain in normalized or original_domain in normalized)
        and any(word in normalized for word in SAVE_WORDS)
        and any(word in normalized for word in DOCUMENT_WORDS)
    )


def has_explicit_document_inbox_move_confirmation(
    filename: str,
    confirmation_text: str,
) -> bool:
    normalized = normalize_confirmation_text(confirmation_text)
    safe_filename = normalize_confirmation_text(filename)
    return (
        safe_filename in normalized
        and any(word in normalized for word in ("presun", "přesun"))
        and any(word in normalized for word in ("processed", "zpracov"))
        and any(word in normalized for word in DOCUMENT_WORDS)
    )


def has_explicit_document_inbox_delete_confirmation(
    filename: str,
    confirmation_text: str,
) -> bool:
    normalized = normalize_confirmation_text(confirmation_text)
    safe_filename = normalize_confirmation_text(filename)
    return (
        safe_filename in normalized
        and "ano" in normalized
        and any(word in normalized for word in ("smaz", "smaž", "odstran"))
        and any(word in normalized for word in DOCUMENT_WORDS)
    )


def normalize_confirmation_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = " ".join(normalized.split())
    return re.sub(r"\s*-\s*", "-", normalized)


def resolve_allowed_source(source_path: str) -> Path | str:
    if URL_PATTERN.search(source_path):
        return "Prace s dokumentem byla odmitnuta: zdroj musi byt lokalni soubor, ne URL."
    candidate = Path(source_path).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError:
        return f"Prace s dokumentem byla odmitnuta: soubor neexistuje: {source_path}"

    allowed_roots = ((PROJECT_ROOT / "data").resolve(), Path("/private/tmp").resolve())
    if not any(is_relative_to(resolved, root) for root in allowed_roots):
        return (
            "Prace s dokumentem byla odmitnuta: zdroj musi byt v projektove slozce "
            "`data/` nebo v docasne slozce `/private/tmp`."
        )
    return resolved


def resolve_inbox_source_file(source_path: str, vault_dir: Path) -> Path | str:
    source = resolve_allowed_source(source_path)
    if isinstance(source, str):
        return source
    incoming = (vault_dir / "inbox" / "incoming").resolve()
    try:
        if source.parent.resolve() != incoming:
            return (
                "Prace s inboxem byla odmitnuta: soubor musi byt primo ve slozce "
                f"`{relative_to_project(incoming)}`."
            )
    except OSError:
        return "Prace s inboxem byla odmitnuta: inbox nelze overit."
    if not source.is_file():
        return "Prace s inboxem byla odmitnuta: source_path musi ukazovat na soubor."
    return source


def resolve_document_source(source_path: str, document_id: str, vault_dir: Path) -> Path | str:
    if source_path.strip():
        return resolve_allowed_source(source_path)
    document_id = safe_slug(document_id, default="", limit=140)
    if not document_id:
        return "Chybi source_path nebo document_id."
    for item in read_jsonl(vault_dir / "index" / "documents_index.jsonl"):
        if item.get("document_id") == document_id:
            path = PROJECT_ROOT / str(item.get("stored_path", ""))
            if path.exists():
                return path
            return f"Dokument {document_id} je v indexu, ale soubor nebyl nalezen."
    return f"Document ID {document_id} nebyl nalezen v private indexu."


def move_document_inbox_item(
    source: Path,
    confirmation_text: str,
    user_confirmed: bool,
    vault_dir: Path,
) -> str:
    if not user_confirmed or not has_explicit_document_inbox_move_confirmation(
        filename=source.name,
        confirmation_text=confirmation_text,
    ):
        return (
            "Pro presun z inboxu potrebuji potvrzeni v aktualni zprave. "
            f"Pouzij presne: Potvrzuji, presunout dokument {source.name} do processed."
        )

    processed_dir = vault_dir / "inbox" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    digest = sha256_file(source)
    imported = find_duplicate_by_sha(vault_dir=vault_dir, sha256=digest)
    destination = next_available_path(processed_dir / safe_filename(source.name))
    shutil.move(str(source), str(destination))
    append_inbox_action(
        vault_dir=vault_dir,
        action="move_to_processed",
        source=source,
        sha256=digest,
        document_id=str(imported.get("document_id", "")) if imported else "",
        destination=destination,
    )
    return (
        "Dokument byl presunut z inboxu.\n"
        f"- Z: `{relative_to_project(source)}`\n"
        f"- Do: `{relative_to_project(destination)}`"
    )


def delete_document_inbox_item(
    source: Path,
    confirmation_text: str,
    user_confirmed: bool,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    if not user_confirmed or not has_explicit_document_inbox_delete_confirmation(
        filename=source.name,
        confirmation_text=confirmation_text,
    ):
        return (
            "Mazani z inboxu vyzaduje druhe vyslovne potvrzeni. "
            f"Nejdriv se zeptej: Opravdu chcete dokument {source.name} smazat z inboxu? "
            f"Po odpovedi ano pouzij presne: Ano, smazat dokument {source.name} z inboxu."
        )

    digest = sha256_file(source)
    imported = find_duplicate_by_sha(vault_dir=vault_dir, sha256=digest)
    source.unlink()
    append_inbox_action(
        vault_dir=vault_dir,
        action="delete_from_inbox",
        source=source,
        sha256=digest,
        document_id=str(imported.get("document_id", "")) if imported else "",
        destination=None,
    )
    return f"Dokument byl smazan z inboxu: `{relative_to_project(source)}`."


def select_mobile_batch_manifest(
    inbox: Path,
    batch_id: str = "",
) -> tuple[Path, dict[str, Any]]:
    manifests = sorted(
        inbox.glob("scan_*_manifest.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not manifests:
        raise ValueError("v mobile inboxu neni zadny scan manifest.")

    wanted = safe_text(batch_id).strip()
    if wanted:
        matches: list[tuple[Path, dict[str, Any]]] = []
        for path in manifests:
            manifest = read_json_file(path)
            if safe_text(str(manifest.get("batch_id", ""))).strip() == wanted:
                matches.append((path, manifest))
        if not matches:
            raise ValueError(f"batch_id {wanted} nebyl v mobile inboxu nalezen.")
        return matches[0]

    if len(manifests) > 1:
        choices: list[str] = []
        for path in manifests[:5]:
            manifest = read_json_file(path)
            choices.append(safe_text(str(manifest.get("batch_id", path.stem))))
        raise ValueError(
            "v mobile inboxu je vice batchu; zadej konkretni batch_id. "
            f"Kandidati: {', '.join(choices)}"
        )
    return manifests[0], read_json_file(manifests[0])


def read_json_file(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"nejde precist JSON manifest {path.name}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"JSON manifest {path.name} nema objektovy tvar.")
    return data


def mobile_page_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"_page_(\d+)", path.stem)
    page_number = int(match.group(1)) if match else 999_999
    return page_number, path.name


def safe_image_suffix(path: Path) -> str:
    suffix = path.suffix.casefold()
    if suffix in {".jpg", ".jpeg", ".png", ".heic", ".heif", ".tif", ".tiff"}:
        return suffix
    return ".img"


def normalize_mobile_document_page(source: Path, target: Path) -> None:
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise ValueError("chybi Python balik Pillow pro zpracovani obrazku.") from exc

    try:
        from pillow_heif import register_heif_opener

        register_heif_opener()
    except ImportError:
        pass

    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        normalized = ImageOps.exif_transpose(image)
        normalized = ImageOps.autocontrast(normalized.convert("RGB"))
        normalized.save(target, format="JPEG", quality=92, optimize=True)


def build_pdf_from_images(images: list[Path], target: Path) -> None:
    if not images:
        raise ValueError("nelze vytvorit PDF bez stran.")
    try:
        from PIL import Image
    except ImportError as exc:
        raise ValueError("chybi Python balik Pillow pro tvorbu PDF.") from exc

    pdf_pages = []
    for image_path in images:
        with Image.open(image_path) as image:
            pdf_pages.append(image.convert("RGB").copy())
    target.parent.mkdir(parents=True, exist_ok=True)
    first, rest = pdf_pages[0], pdf_pages[1:]
    first.save(target, "PDF", save_all=True, append_images=rest, resolution=200.0)


def validate_source_file(source: Path) -> None:
    if not source.is_file():
        raise ValueError("source_path musi ukazovat na soubor.")
    size = source.stat().st_size
    if size <= 0:
        raise ValueError("soubor je prazdny.")
    if size > MAX_DOCUMENT_BYTES:
        raise ValueError("soubor je vetsi nez bezpecny limit 50 MB.")


def extract_text(source: Path) -> TextExtractionResult:
    suffix = source.suffix.casefold()
    if suffix in {".txt", ".md", ".csv"}:
        text = source.read_text(encoding="utf-8", errors="ignore")
        return TextExtractionResult(text=text, method="plain-text", ocr_needed=False)

    if suffix == ".pdf":
        has_encryption_marker = is_pdf_encrypted(source)
        pdftotext = extract_pdf_with_pdftotext(source)
        if pdftotext.text.strip():
            return enrich_pdf_text_with_tables(source, pdftotext)
        pypdf = extract_pdf_with_pypdf(source)
        if pypdf.text.strip():
            return enrich_pdf_text_with_tables(source, pypdf)
        fallback = decode_printable_bytes(source)
        if looks_like_meaningful_text(fallback):
            return TextExtractionResult(
                text=fallback,
                method="pdf-byte-decode-fallback",
                ocr_needed=False,
                warning="PDF text byl ziskan nouzovym dekodovanim bajtu; overit kvalitu.",
            )
        tesseract_ocr = extract_pdf_with_tesseract_ocr(source)
        if tesseract_ocr.text.strip():
            return tesseract_ocr
        ocr = extract_pdf_with_macos_vision_ocr(source)
        if ocr.text.strip():
            return ocr
        if has_encryption_marker:
            return TextExtractionResult(
                text="",
                method="pdf-encrypted",
                ocr_needed=True,
                warning=(
                    "PDF obsahuje sifrovaci znacku /Encrypt a bezne extraktory z nej "
                    "neziskaly text. Je potreba odemcena kopie nebo heslo."
                ),
            )
        return TextExtractionResult(
            text="",
            method="pdf-no-text",
            ocr_needed=True,
            warning=(
                "PDF nema dostupnou textovou vrstvu nebo chybi kvalitni extraktor; "
                "nalezen byl jen binarni/obrazovy obsah. Bude potreba OCR."
            ),
        )

    text = decode_printable_bytes(source)
    return TextExtractionResult(
        text=text,
        method="byte-decode-fallback",
        ocr_needed=not bool(text.strip()),
        warning="Neznamy typ souboru; text byl ziskan jen nouzove.",
    )


def extract_pdf_with_pdftotext(source: Path) -> TextExtractionResult:
    try:
        completed = subprocess.run(
            ["pdftotext", "-layout", str(source), "-"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return TextExtractionResult(text="", method="pdftotext-unavailable", ocr_needed=True)
    if completed.returncode == 0 and completed.stdout.strip():
        return TextExtractionResult(text=completed.stdout, method="pdftotext", ocr_needed=False)
    return TextExtractionResult(text="", method="pdftotext-empty", ocr_needed=True)


def is_pdf_encrypted(source: Path) -> bool:
    try:
        head = source.read_bytes()
    except OSError:
        return False
    return b"/Encrypt" in head[: min(len(head), 1024 * 1024 * 2)]


def extract_pdf_with_pypdf(source: Path) -> TextExtractionResult:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return TextExtractionResult(text="", method="pypdf-unavailable", ocr_needed=True)
    try:
        reader = PdfReader(str(source))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception:
        return TextExtractionResult(text="", method="pypdf-failed", ocr_needed=True)
    return TextExtractionResult(text=text, method="pypdf", ocr_needed=not bool(text.strip()))


def enrich_pdf_text_with_tables(source: Path, extraction: TextExtractionResult) -> TextExtractionResult:
    tables = extract_pdf_tables_with_pdfplumber(source)
    if not tables.text.strip():
        return extraction

    warning_parts = [part for part in (extraction.warning, tables.warning) if part]
    table_text = tables.text[:MAX_TABLE_TEXT_CHARS]
    if len(tables.text) > MAX_TABLE_TEXT_CHARS:
        warning_parts.append(f"Tabulkovy text byl zkracen na {MAX_TABLE_TEXT_CHARS} znaku.")
    return TextExtractionResult(
        text=f"{extraction.text.rstrip()}\n\n[extracted tables: {tables.method}]\n{table_text}",
        method=f"{extraction.method}+{tables.method}",
        ocr_needed=extraction.ocr_needed,
        warning="; ".join(warning_parts),
    )


def extract_pdf_tables_with_pdfplumber(
    source: Path,
    max_pages: int = DEFAULT_TABLE_MAX_PAGES,
) -> TableExtractionResult:
    if os.environ.get("SAMANTHA_DOCUMENT_PDFPLUMBER_TABLES", "1").casefold() in {"0", "false", "no"}:
        return TableExtractionResult(
            text="",
            method="pdfplumber-tables-disabled",
            warning="pdfplumber tabulkova extrakce je vypnuta promennou SAMANTHA_DOCUMENT_PDFPLUMBER_TABLES.",
        )

    try:
        import pdfplumber  # type: ignore
    except Exception:
        return TableExtractionResult(text="", method="pdfplumber-tables-unavailable")

    page_count = 0
    table_count = 0
    chunks: list[str] = []
    warnings: list[str] = []
    try:
        with pdfplumber.open(str(source)) as pdf:
            page_count = len(pdf.pages)
            for page_index, page in enumerate(pdf.pages[:max_pages], start=1):
                try:
                    tables = page.extract_tables()
                except Exception as exc:
                    warnings.append(f"strana {page_index}: pdfplumber selhal ({type(exc).__name__})")
                    continue
                for table_index, table in enumerate(tables or [], start=1):
                    rows = table_to_text_rows(table)
                    if not rows:
                        continue
                    table_count += 1
                    chunks.append(f"[page {page_index} table {table_index}]")
                    chunks.extend(rows)
    except Exception as exc:
        return TableExtractionResult(
            text="",
            method="pdfplumber-tables-failed",
            warning=f"pdfplumber selhal: {type(exc).__name__}",
        )

    if page_count > max_pages:
        warnings.append(f"pdfplumber zpracoval jen prvnich {max_pages} z {page_count} stran.")
    return TableExtractionResult(
        text="\n".join(chunks),
        method="pdfplumber-tables",
        table_count=table_count,
        warning="; ".join(warnings),
    )


def table_to_text_rows(table: list[list[Any]]) -> list[str]:
    rows: list[str] = []
    for row in table:
        if not row:
            continue
        cells = [normalize_whitespace(str(cell or ""))[:160] for cell in row]
        if not any(cells):
            continue
        rows.append(" | ".join(cells))
    return rows


def extract_pdf_with_tesseract_ocr(
    source: Path,
    max_pages: int = DEFAULT_OCR_MAX_PAGES,
) -> TextExtractionResult:
    if os.environ.get("SAMANTHA_DOCUMENT_TESSERACT_OCR", "1").casefold() in {"0", "false", "no"}:
        return TextExtractionResult(
            text="",
            method="tesseract-ocr-disabled",
            ocr_needed=True,
            warning="Tesseract OCR je vypnute promennou SAMANTHA_DOCUMENT_TESSERACT_OCR.",
        )

    pdftoppm = shutil.which("pdftoppm")
    tesseract = shutil.which("tesseract")
    if not pdftoppm or not tesseract:
        return TextExtractionResult(
            text="",
            method="tesseract-ocr-unavailable",
            ocr_needed=True,
            warning="Chybi pdftoppm nebo tesseract.",
        )

    with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
        temp_path = Path(temp_dir)
        prefix = temp_path / "page"
        try:
            render = subprocess.run(
                [
                    pdftoppm,
                    "-f",
                    "1",
                    "-l",
                    str(max_pages),
                    "-r",
                    str(OCR_RENDER_DPI),
                    "-png",
                    str(source),
                    str(prefix),
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
            return TextExtractionResult(
                text="",
                method="tesseract-ocr-render-failed",
                ocr_needed=True,
                warning="pdftoppm se nepodarilo spustit pro OCR render.",
            )
        if render.returncode != 0:
            return TextExtractionResult(
                text="",
                method="tesseract-ocr-render-failed",
                ocr_needed=True,
                warning=normalize_whitespace(render.stderr or render.stdout)[:300],
            )

        images = sorted(temp_path.glob("page-*.png"))
        if not images:
            return TextExtractionResult(
                text="",
                method="tesseract-ocr-no-pages",
                ocr_needed=True,
                warning="pdftoppm nevytvoril zadne obrazky stran.",
            )

        lang = tesseract_languages()
        page_texts: list[str] = []
        warnings: list[str] = []
        for index, image in enumerate(images, start=1):
            try:
                ocr = subprocess.run(
                    [tesseract, str(image), "stdout", "-l", lang, "--psm", "3"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
            except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
                warnings.append(f"strana {index}: tesseract selhal")
                continue
            if ocr.returncode != 0:
                warnings.append(f"strana {index}: {normalize_whitespace(ocr.stderr)[:120]}")
                continue
            text = ocr.stdout.strip()
            if text:
                page_texts.append(f"[page {index}]\n{text}")

        warning = "; ".join(warnings[:3])
        if len(images) >= max_pages:
            extra = f"OCR zpracovalo nejvyse prvnich {max_pages} stran."
            warning = f"{warning}; {extra}" if warning else extra
        return TextExtractionResult(
            text="\n\n".join(page_texts),
            method="tesseract-ocr",
            ocr_needed=not bool(page_texts),
            warning=warning,
        )


def tesseract_languages() -> str:
    tesseract = shutil.which("tesseract")
    if not tesseract:
        return "eng"
    try:
        completed = subprocess.run(
            [tesseract, "--list-langs"],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        return "eng"
    langs = set(completed.stdout.split())
    preferred = [lang for lang in ("ces", "eng") if lang in langs]
    return "+".join(preferred) if preferred else "eng"


def extract_pdf_with_macos_vision_ocr(
    source: Path,
    max_pages: int = DEFAULT_OCR_MAX_PAGES,
) -> TextExtractionResult:
    if os.environ.get("SAMANTHA_DOCUMENT_OCR", "1").casefold() in {"0", "false", "no"}:
        return TextExtractionResult(
            text="",
            method="macos-vision-ocr-disabled",
            ocr_needed=True,
            warning="OCR je vypnute promennou SAMANTHA_DOCUMENT_OCR.",
        )

    swift = shutil.which("swift")
    helper = PROJECT_ROOT / "scripts" / "ocr_pdf_vision.swift"
    if not swift or not helper.exists():
        return TextExtractionResult(
            text="",
            method="macos-vision-ocr-unavailable",
            ocr_needed=True,
            warning="macOS Vision OCR helper neni dostupny.",
        )

    env = dict(os.environ)
    env.setdefault("CLANG_MODULE_CACHE_PATH", "/private/tmp/samantha_swift_module_cache")
    env.setdefault("TMPDIR", "/private/tmp")
    parsed = run_macos_vision_helper(source=source, max_pages=max_pages, swift=swift, helper=helper, env=env)
    if isinstance(parsed, str):
        return TextExtractionResult(
            text="",
            method="macos-vision-ocr-failed",
            ocr_needed=True,
            warning=parsed,
        )
    text = str(parsed["text"])
    page_count = int(parsed["page_count"])
    processed_pages = int(parsed["processed_pages"])
    warning = ""
    if processed_pages < page_count:
        warning = f"OCR zpracovalo jen prvnich {processed_pages} z {page_count} stran."
    if text.strip():
        return TextExtractionResult(
            text=text,
            method="macos-vision-ocr",
            ocr_needed=False,
            warning=warning,
        )

    image_ocr = extract_pdf_thumbnail_with_qlmanage_ocr(
        source=source,
        swift=swift,
        helper=helper,
        env=env,
    )
    if image_ocr.text.strip():
        return image_ocr

    return TextExtractionResult(
        text="",
        method="macos-vision-ocr-empty",
        ocr_needed=True,
        warning=image_ocr.warning or "macOS Vision OCR nenasel text.",
    )


def run_macos_vision_helper(
    source: Path,
    max_pages: int,
    swift: str,
    helper: Path,
    env: dict[str, str],
) -> dict[str, object] | str:
    try:
        completed = subprocess.run(
            [swift, str(helper), str(source), str(max_pages)],
            check=False,
            capture_output=True,
            text=True,
            timeout=OCR_TIMEOUT_SECONDS,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return "macOS Vision OCR prekrocil casovy limit."
    except (OSError, subprocess.SubprocessError):
        return "macOS Vision OCR se nepodarilo spustit."

    if completed.returncode != 0:
        warning = normalize_whitespace(completed.stderr or completed.stdout)
        return f"macOS Vision OCR selhal: {warning[:300]}"

    parsed = parse_macos_vision_ocr_json(completed.stdout)
    if isinstance(parsed, str):
        return parsed
    return parsed


def extract_pdf_thumbnail_with_qlmanage_ocr(
    source: Path,
    swift: str,
    helper: Path,
    env: dict[str, str],
) -> TextExtractionResult:
    qlmanage = shutil.which("qlmanage")
    if not qlmanage:
        return TextExtractionResult(
            text="",
            method="qlmanage-vision-ocr-unavailable",
            ocr_needed=True,
            warning="qlmanage neni dostupny pro vykresleni PDF nahledu.",
        )

    with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
        temp_path = Path(temp_dir)
        try:
            completed = subprocess.run(
                [qlmanage, "-t", "-s", "2400", "-o", str(temp_path), str(source)],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
            return TextExtractionResult(
                text="",
                method="qlmanage-vision-ocr-failed",
                ocr_needed=True,
                warning="qlmanage se nepodarilo spustit pro PDF nahled.",
            )
        if completed.returncode != 0:
            return TextExtractionResult(
                text="",
                method="qlmanage-vision-ocr-failed",
                ocr_needed=True,
                warning=normalize_whitespace(completed.stderr or completed.stdout)[:300],
            )

        thumbnails = sorted(temp_path.glob("*.png"))
        if not thumbnails:
            return TextExtractionResult(
                text="",
                method="qlmanage-vision-ocr-empty",
                ocr_needed=True,
                warning="qlmanage nevytvoril PNG nahled PDF.",
            )
        parsed = run_macos_vision_helper(
            source=thumbnails[0],
            max_pages=1,
            swift=swift,
            helper=helper,
            env=env,
        )
        if isinstance(parsed, str):
            return TextExtractionResult(
                text="",
                method="qlmanage-vision-ocr-failed",
                ocr_needed=True,
                warning=parsed,
            )
        text = str(parsed["text"])
        return TextExtractionResult(
            text=text,
            method="qlmanage-thumbnail-vision-ocr",
            ocr_needed=not bool(text.strip()),
            warning="OCR bylo provedeno jen z Quick Look nahledu prvni strany PDF.",
        )


def parse_macos_vision_ocr_json(raw_output: str) -> dict[str, object] | str:
    start = raw_output.find("{")
    if start > 0:
        raw_output = raw_output[start:]
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError:
        return "macOS Vision OCR vratil necitelny JSON vystup."
    if not isinstance(data, dict):
        return "macOS Vision OCR vratil neocekavany format."
    if data.get("error"):
        return f"macOS Vision OCR chyba: {data.get('error')}"
    pages = data.get("pages")
    if not isinstance(pages, list):
        return "macOS Vision OCR nevrazil seznam stran."

    texts: list[str] = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        page_number = page.get("page")
        text = str(page.get("text") or "").strip()
        if text:
            texts.append(f"[page {page_number}]\n{text}")
    return {
        "text": "\n\n".join(texts),
        "page_count": int(data.get("page_count") or len(pages)),
        "processed_pages": int(data.get("processed_pages") or len(pages)),
    }


def decode_printable_bytes(source: Path) -> str:
    raw = source.read_bytes()[:MAX_INDEX_TEXT_CHARS]
    text = raw.decode("utf-8", errors="ignore")
    text = "".join(char if char.isprintable() or char in "\n\t" else " " for char in text)
    return normalize_whitespace(text)


def looks_like_meaningful_text(text: str) -> bool:
    normalized = normalize_whitespace(text)
    if len(normalized) < 20:
        return False
    letters = sum(1 for char in normalized if char.isalpha())
    ratio = letters / max(len(normalized), 1)
    if ratio < 0.45:
        return False
    folded = normalized.casefold()
    meaningful_markers = (
        "smlouva",
        "pojist",
        "faktura",
        "splatnost",
        "platnost",
        "revize",
        "servis",
        "protokol",
    )
    return any(marker in folded for marker in meaningful_markers)


def propose_metadata(
    source: Path,
    text: str,
    document_hint: str = "",
    target_domain: str = "",
    counterparty: str = "",
    related_asset: str = "",
) -> dict[str, Any]:
    combined = f"{source.name}\n{document_hint}\n{text[:5000]}".casefold()
    document_type = safe_slug(document_hint, default="", limit=50) if document_hint else ""
    if not document_type:
        document_type = guess_document_type(combined)
    domain = normalize_domain(target_domain or guess_domain(combined, document_type))
    asset = safe_text(related_asset or guess_related_asset(combined))
    return {
        "document_type": document_type,
        "domain": domain,
        "counterparty": safe_text(counterparty or guess_counterparty(text)),
        "related_asset": asset,
        "tags": suggest_document_tags(combined, document_type, domain, asset),
    }


def guess_document_type(text: str) -> str:
    if any(word in text for word in ("zelena karta", "zelená karta", "green card")):
        return "green_card"
    if any(word in text for word in ("faktura", "invoice", "danovy doklad", "daňový doklad", "vyuctovani", "vyúčtování", "variabilni symbol", "variabilní symbol")):
        return "invoice"
    if any(word in text for word in ("pojistka", "pojisteni", "pojištění", "pojistna smlouva", "pojistná smlouva")):
        return "insurance_policy"
    if any(word in text for word in ("smlouva", "contract")):
        return "contract"
    if any(word in text for word in ("stk", "technicka kontrola", "technická kontrola", "emisni kontrola", "emisní kontrola", "revize", "revizni", "revizní")):
        return "inspection_report"
    if any(word in text for word in ("servis", "servisni", "servisní", "garanční prohlídka", "garancni prohlidka", "udrzba", "údržba", "zakazkovy list", "zakázkový list", "protokol")):
        return "service_report"
    if any(word in text for word in ("zaruka", "záruka", "warranty")):
        return "warranty"
    return "document"


def guess_domain(text: str, document_type: str) -> str:
    if any(word in text for word in ("volvo", "v40", "vozidlo", "spz", "vin", "stk", "technicka kontrola", "technická kontrola", "servisni prohlidka", "servisní prohlídka")):
        if document_type in {"invoice", "service_report", "inspection_report", "green_card"}:
            return "car"
    if document_type == "insurance_policy":
        return "insurance"
    if any(word in text for word in ("pojist", "rixo", "pojistovna", "pojišťovna")):
        return "insurance"
    if any(word in text for word in ("fotovolta", "fve", "elektr", "distribuc", "energie")):
        return "energy"
    if any(word in text for word in ("kotel", "komin", "komín", "dum", "dům", "home")):
        return "home"
    if any(word in text for word in ("auto", "vozidlo", "spz", "vin", "volvo", "stk")):
        return "car"
    if any(word in text for word in ("dan", "daň", "financni urad", "finanční úřad")):
        return "tax"
    if document_type == "warranty":
        return "warranty"
    return "other"


def guess_counterparty(text: str) -> str:
    for raw_line in text.splitlines()[:30]:
        line = normalize_whitespace(raw_line)
        if not 3 <= len(line) <= 100:
            continue
        folded = line.casefold()
        if any(marker in folded for marker in ("s.r.o", "a.s", "pojistovna", "pojišťovna", "servis", "rixo")):
            return line
    return ""


def guess_related_asset(text: str) -> str:
    if "volvo" in text and "v40" in text:
        return "Volvo V40"
    if "volvo" in text:
        return "Volvo"
    if "fotovolta" in text or "fve" in text:
        return "fotovoltaika"
    if "kotel" in text:
        return "kotel"
    if any(word in text for word in ("auto", "vozidlo", "spz", "vin", "stk")):
        return "auto"
    return ""


def suggest_document_tags(
    text: str,
    document_type: str,
    domain: str,
    related_asset: str,
) -> list[str]:
    tags: list[str] = [domain, document_type]
    if related_asset:
        tags.append(related_asset)
    checks = (
        ("auto", ("auto", "vozidlo", "spz", "vin", "stk", "volvo")),
        ("volvo-v40", ("volvo v40", "v40")),
        ("pojisteni", ("pojist", "zelena karta", "zelená karta")),
        ("faktura", ("faktura", "invoice", "danovy doklad", "daňový doklad")),
        ("servis", ("servis", "udrzba", "údržba", "garanční prohlídka", "garancni prohlidka")),
        ("technicka-kontrola", ("stk", "technicka kontrola", "technická kontrola", "emisni kontrola", "emisní kontrola")),
        ("splatnost", ("splatnost", "uhradit", "zaplatit")),
        ("platnost", ("platnost do", "platna do", "platná do")),
    )
    for tag, markers in checks:
        if any(marker in text for marker in markers):
            tags.append(tag)
    for year in re.findall(r"\b20\d{2}\b", text):
        tags.append(year)
    return merge_tags([], tags)


def merge_tags(primary: list[str], secondary: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for tag in [*primary, *secondary]:
        safe = safe_slug(str(tag), default="", limit=60)
        if not safe or safe in seen:
            continue
        merged.append(safe)
        seen.add(safe)
    return merged


def find_due_date_candidates(text: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for match in iter_date_matches(text):
        parsed = parse_date_match(match.group(0))
        if not parsed:
            continue
        context = context_window(text, match.start(), match.end(), window=120)
        candidate_type, confidence, create_reminder = classify_date_context(context)
        key = (parsed, candidate_type, normalize_whitespace(context)[:80])
        if key in seen:
            continue
        seen.add(key)
        candidates.append(
            {
                "date": parsed,
                "type": candidate_type,
                "confidence": confidence,
                "create_reminder_candidate": create_reminder,
                "context": normalize_whitespace(context)[:500],
            }
        )
    candidates.sort(key=lambda item: (0 if item["create_reminder_candidate"] else 1, item["date"]))
    return candidates


def iter_date_matches(text: str):
    date_pattern = re.compile(r"\b(?:\d{4}-\d{1,2}-\d{1,2}|\d{1,2}\.\s*\d{1,2}\.\s*\d{4})\b")
    return date_pattern.finditer(text)


def parse_date_match(value: str) -> str:
    cleaned = value.strip()
    formats = ("%Y-%m-%d", "%d.%m.%Y", "%d. %m. %Y")
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt).date().isoformat()
        except ValueError:
            continue
    match = re.fullmatch(r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})", cleaned)
    if match:
        day, month, year = (int(part) for part in match.groups())
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return ""
    return ""


def classify_date_context(context: str) -> tuple[str, str, bool]:
    folded = context.casefold()
    if any(word in folded for word in ("splatnost", "uhradit", "zaplatit", "k uhrade", "k úhradě")):
        return "payment_due", "high", True
    if any(word in folded for word in ("platnost do", "platna do", "platná do", "konec smlouvy")):
        return "valid_until", "high", True
    if any(word in folded for word in ("revize", "servis", "kontrola", "prohlidka", "prohlídka")):
        return "service_due", "medium", True
    if any(word in folded for word in ("platnost od", "pocatek", "počátek", "vystaveni", "vystavení")):
        return "context_date", "medium", False
    return "unknown_date", "low", False


def context_window(text: str, start: int, end: int, window: int) -> str:
    left = max(0, start - window)
    right = min(len(text), end + window)
    return text[left:right]


def build_document_id(
    source: Path,
    domain: str,
    document_type: str,
    digest: str,
    imported_at: datetime,
) -> str:
    stem = safe_slug(source.stem, default="document", limit=45)
    return f"doc-{imported_at.date().isoformat()}-{domain}-{document_type}-{stem}-{digest[:8]}"


def find_duplicate_by_sha(vault_dir: Path, sha256: str) -> dict[str, Any] | None:
    for item in read_jsonl(vault_dir / "index" / "documents_index.jsonl"):
        if item.get("sha256") == sha256:
            return item
    return None


def latest_inbox_action_for_document(vault_dir: Path, document_id: str) -> dict[str, Any] | None:
    if not document_id:
        return None
    actions = read_jsonl(vault_dir / "index" / "inbox_actions.jsonl")
    for item in reversed(actions):
        if item.get("document_id") == document_id:
            return item
    return None


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                rows.append(data)
    return rows


def append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, sort_keys=True)
        handle.write("\n")


def append_inbox_action(
    vault_dir: Path,
    action: str,
    source: Path,
    sha256: str,
    document_id: str = "",
    destination: Path | None = None,
    now: datetime | None = None,
) -> None:
    action_time = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    record: dict[str, Any] = {
        "action": action,
        "action_at": action_time.isoformat(),
        "document_id": safe_slug(document_id, default="", limit=140),
        "filename": safe_text(source.name),
        "from_path": str(relative_to_project(source)),
        "sha256": sha256,
    }
    if destination is not None:
        record["to_path"] = str(relative_to_project(destination))
    append_jsonl(vault_dir / "index" / "inbox_actions.jsonl", record)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_domain(value: str) -> str:
    key = value.casefold().strip()
    key = SAFE_ID_PATTERN.sub("-", key).strip("-")
    return DOMAIN_ALIASES.get(value.casefold().strip(), DOMAIN_ALIASES.get(key, "other"))


def parse_tags(tags: str) -> list[str]:
    values = re.split(r"[,;]", tags)
    return [safe_slug(value, default="", limit=40) for value in values if safe_slug(value, default="", limit=40)]


def safe_slug(value: str, default: str, limit: int) -> str:
    normalized = SAFE_ID_PATTERN.sub("-", value.casefold().strip()).strip("-")
    return (normalized or default)[:limit]


def safe_filename(filename: str) -> str:
    path = Path(filename)
    safe_stem = SAFE_FILENAME_PATTERN.sub("-", path.stem).strip("-") or "document"
    safe_suffix = SAFE_FILENAME_PATTERN.sub("", path.suffix)[:12] or ".bin"
    return f"{safe_stem[:90]}{safe_suffix}"


def next_available_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    counter = 2
    while True:
        candidate = path.with_name(f"{stem}-{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def count_files(path: Path) -> int:
    try:
        return sum(1 for item in path.iterdir() if item.is_file())
    except OSError:
        return 0


def parse_iso_datetime(value: str) -> datetime | None:
    if not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip())
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def format_status_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def safe_text(value: str) -> str:
    return sanitize_output(normalize_whitespace(value))


def sanitize_output(value: str) -> str:
    value = URL_PATTERN.sub("[URL redigovano]", value)
    value = EMAIL_PATTERN.sub("[e-mail redigovan]", value)
    value = RODNE_CISLO_PATTERN.sub("[rodne cislo redigovano]", value)
    return normalize_whitespace(value)


def normalize_whitespace(value: str) -> str:
    return " ".join(value.replace("\x00", " ").split())


def tokenize(query: str) -> list[str]:
    return re.findall(r"[\wÀ-ž0-9]+", query.casefold())


def build_snippet(text: str, terms: list[str]) -> str:
    folded = text.casefold()
    positions = [folded.find(term) for term in terms if folded.find(term) >= 0]
    if not positions:
        return sanitize_output(text[:MAX_OUTPUT_SNIPPET_CHARS])
    start = max(0, min(positions) - 120)
    end = min(len(text), start + MAX_OUTPUT_SNIPPET_CHARS)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{text[start:end]}{suffix}"


def require_iso_date(value: str) -> str:
    try:
        return date.fromisoformat(value.strip()).isoformat()
    except ValueError as exc:
        raise ValueError("due_date musi byt ve formatu YYYY-MM-DD.") from exc


def safe_priority(value: str) -> str:
    normalized = value.casefold().strip()
    return normalized if normalized in {"low", "medium", "high"} else "high"


def relative_to_project(path: Path) -> Path:
    try:
        return path.resolve().relative_to(PROJECT_ROOT)
    except ValueError:
        return path


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
