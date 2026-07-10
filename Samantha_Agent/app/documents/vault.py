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

from app.file_persistence import append_jsonl_locked, atomic_write_json, atomic_write_text
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
    "food": "food",
    "jidlo": "food",
    "jídlo": "food",
    "recept": "food",
    "recepty": "food",
    "kuchyne": "food",
    "kuchyně": "food",
    "tax": "tax",
    "dane": "tax",
    "daně": "tax",
    "warranty": "warranty",
    "zaruka": "warranty",
    "záruka": "warranty",
    "travel": "travel",
    "cestovani": "travel",
    "cestování": "travel",
    "dovolena": "travel",
    "dovolená": "travel",
    "telecom": "telecom",
    "telefon": "telecom",
    "telefonni-sluzby": "telecom",
    "telefonní-služby": "telecom",
    "mobil": "telecom",
    "mobilni-sluzby": "telecom",
    "mobilní-služby": "telecom",
    "telekomunikace": "telecom",
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


@dataclass(frozen=True)
class MobileDocumentProcessItem:
    batch_id: str
    document_title: str
    status: str
    page_count: int
    processing_dir: Path | None = None
    pdf_path: Path | None = None
    manifest_path: Path | None = None
    extraction_method: str = ""
    ocr_needed: bool = False
    document_type: str = ""
    domain: str = ""
    due_date_count: int = 0
    warning: str = ""


@dataclass(frozen=True)
class MobileDocumentFinalMetadata:
    domain: str
    document_type: str
    counterparty: str
    related_asset: str
    tags: str
    case_id: str


@dataclass(frozen=True)
class DocumentReindexProposal:
    document_id: str
    stored_path: Path
    manifest_path: Path
    current: dict[str, Any]
    proposed: dict[str, Any]
    changes: dict[str, dict[str, Any]]


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


def process_mobile_document_inbox_summary(
    batch_id: str = "",
    mobile_inbox_dir: Path = DEFAULT_MOBILE_DOCUMENT_INBOX,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    max_batches: int = 20,
    force_reprocess: bool = False,
) -> str:
    try:
        items, request_warning = process_mobile_document_inbox(
            batch_id=batch_id,
            mobile_inbox_dir=mobile_inbox_dir,
            vault_dir=vault_dir,
            max_batches=max_batches,
            force_reprocess=force_reprocess,
        )
    except ValueError as exc:
        return f"Zpracovani mobilniho inboxu bylo odmitnuto: {exc}"

    if not items:
        return "Zpracovani mobilniho inboxu: nebyl nalezen zadny batch ke zpracovani."

    processed = sum(1 for item in items if item.status in {"prepared", "already_prepared", "reprocessed"})
    failed = sum(1 for item in items if item.status == "failed")
    lines = [
        "Zpracovani mobilniho inboxu probehlo.",
        f"- Batchu celkem: {len(items)}",
        f"- Pripraveno ke kontrole/importu: {processed}",
        f"- Chyby: {failed}",
    ]
    if request_warning:
        lines.append(f"- Poznamka k requestu: {safe_text(request_warning)}")
    lines.append("")

    for item in items:
        lines.extend(
            [
                f"- Batch: {safe_text(item.batch_id)}",
                f"  Nazev: {safe_text(item.document_title) or 'bez nazvu'}",
                f"  Stav: {safe_text(item.status)}",
            ]
        )
        if item.page_count:
            lines.append(f"  Stranky: {item.page_count}")
        if item.pdf_path is not None:
            lines.append(f"  PDF: `{relative_to_project(item.pdf_path)}`")
        if item.manifest_path is not None:
            lines.append(f"  Manifest: `{relative_to_project(item.manifest_path)}`")
        if item.extraction_method:
            lines.append(
                f"  Text/OCR: {safe_text(item.extraction_method)} | "
                f"OCR potreba: {'ano' if item.ocr_needed else 'ne'}"
            )
        if item.document_type or item.domain:
            lines.append(
                f"  Navrh: {safe_text(item.domain or 'other')} / "
                f"{safe_text(item.document_type or 'document')}"
            )
        lines.append(f"  Due date kandidati: {item.due_date_count}")
        if item.warning:
            lines.append(f"  Poznamka: {safe_text(item.warning)}")

    lines.extend(
        [
            "",
            "Bezpecnost: finalni import do vaultu neprobehl. Zdrojove fotky v iCloud "
            "inboxu zustaly beze zmeny. Dalsi krok je kontrola PDF a potvrzeny import.",
        ]
    )
    return "\n".join(lines)


def prepare_mobile_document_final_import_summary(
    batch_id: str = "",
    target_domain: str = "",
    document_type: str = "",
    counterparty: str = "",
    related_asset: str = "",
    tags: str = "",
    case_id: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    try:
        prepared = find_prepared_mobile_batch_for_import(
            vault_dir=vault_dir,
            batch_id=batch_id,
            include_imported=True,
        )
        analysis = ensure_prepared_mobile_analysis(
            prepared=prepared,
            vault_dir=vault_dir,
        )
    except ValueError as exc:
        return f"Priprava finalniho importu mobilniho dokumentu byla odmitnuta: {exc}"

    metadata = choose_mobile_final_metadata(
        analysis=analysis,
        target_domain=target_domain,
        document_type=document_type,
        counterparty=counterparty,
        related_asset=related_asset,
        tags=tags,
        case_id=case_id,
    )
    manifest = read_json_file(prepared.manifest_path)
    already_imported = bool(manifest.get("final_import_done", False))
    due_dates = analysis.get("due_dates", [])
    if not isinstance(due_dates, list):
        due_dates = []

    lines = [
        "Navrh finalniho importu mobilniho dokumentu (read-only):",
        f"- Batch: {safe_text(prepared.batch_id)}",
        f"- Nazev: {safe_text(prepared.document_title) or 'bez nazvu'}",
        f"- Stranky: {prepared.page_count}",
        f"- PDF ke kontrole: `{relative_to_project(prepared.pdf_path)}`",
        f"- Manifest: `{relative_to_project(prepared.manifest_path)}`",
        f"- Stav importu: {'uz importovano' if already_imported else 'ceka na potvrzeni'}",
        f"- Text/OCR: {safe_text(str(analysis.get('extraction_method', '')))} | "
        f"OCR potreba: {'ano' if analysis.get('ocr_needed') else 'ne'}",
        f"- Navrzena oblast: {metadata.domain}",
        f"- Navrzeny typ: {metadata.document_type}",
        f"- Protistrana: {metadata.counterparty or 'nezjisteno'}",
        f"- Vazba na vec/majetek: {metadata.related_asset or 'nezjisteno'}",
        f"- Case ID / souvislost: {metadata.case_id or 'nezadano'}",
    ]
    if metadata.tags:
        lines.append(f"- Tagy: {metadata.tags}")
    lines.append(f"- Due date kandidati: {len(due_dates)}")
    warning = safe_text(str(analysis.get("warning", "")))
    if warning:
        lines.append(f"- Poznamka: {warning}")

    lines.extend(
        [
            "",
            "Kontrola pred ulozenim:",
            "1. Otevri PDF a zkontroluj citelnost/orez.",
            "2. Pokud kvalita nesedi, nepokracuj ve finalnim importu a zkusime RAW/LIGHT/BW nebo GPT PDF.",
            "3. Pokud sedi kvalita i metadata, potvrd ulozeni.",
            "",
            "Potvrzovaci veta pro navrzena metadata:",
            f"`Potvrzuji, uloz dokument {prepared.pdf_path.name} do oblasti {metadata.domain}.`",
            "",
            "Pokud chces zmenit klasifikaci, pouzij pri finalnim importu jine hodnoty "
            "`target_domain`, `document_type`, `tags` nebo `case_id`.",
        ]
    )
    return "\n".join(lines)


def apply_mobile_document_final_import_summary(
    batch_id: str = "",
    target_domain: str = "",
    document_type: str = "",
    counterparty: str = "",
    related_asset: str = "",
    tags: str = "",
    document_id: str = "",
    case_id: str = "",
    user_confirmed: bool = False,
    confirmation_text: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    try:
        prepared = find_prepared_mobile_batch_for_import(
            vault_dir=vault_dir,
            batch_id=batch_id,
            include_imported=False,
        )
        analysis = ensure_prepared_mobile_analysis(
            prepared=prepared,
            vault_dir=vault_dir,
        )
    except ValueError as exc:
        return f"Finalni import mobilniho dokumentu byl odmitnut: {exc}"

    metadata = choose_mobile_final_metadata(
        analysis=analysis,
        target_domain=target_domain,
        document_type=document_type,
        counterparty=counterparty,
        related_asset=related_asset,
        tags=tags,
        case_id=case_id,
    )
    if not user_confirmed or not has_explicit_document_import_confirmation(
        filename=prepared.pdf_path.name,
        target_domain=metadata.domain,
        confirmation_text=confirmation_text,
    ):
        return (
            "Nejdrive potrebuji samostatne potvrzeni od Mily v aktualni zprave. "
            f"Potvrzeni musi obsahovat nazev souboru {prepared.pdf_path.name}, "
            f"cilovou oblast {metadata.domain} a jasny souhlas s ulozenim dokumentu. "
            f"Navrzena veta: Potvrzuji, uloz dokument {prepared.pdf_path.name} "
            f"do oblasti {metadata.domain}."
        )

    try:
        result = apply_document_import_file(
            source_path=str(prepared.pdf_path),
            target_domain=metadata.domain,
            document_type=metadata.document_type,
            counterparty=metadata.counterparty,
            related_asset=metadata.related_asset,
            tags=metadata.tags,
            document_id=document_id,
            case_id=metadata.case_id,
            vault_dir=vault_dir,
        )
    except ValueError as exc:
        return f"Finalni import mobilniho dokumentu byl odmitnut: {exc}"

    mark_mobile_document_final_import(
        prepared=prepared,
        result=result,
        metadata=metadata,
        vault_dir=vault_dir,
    )
    status = "ulozeno" if result.created else "uz existuje"
    return (
        f"Stav: {status}. Document ID: {result.document_id}. "
        f"Batch: {prepared.batch_id}. Dokument: {relative_to_project(result.destination)}. "
        f"Manifest: {relative_to_project(result.manifest)}. "
        "Mobilni pracovni PDF je oznacene jako finalne importovane. "
        "Zdrojove fotky v iCloud inboxu se timto krokem nemazou."
    )


def process_mobile_document_inbox(
    batch_id: str = "",
    mobile_inbox_dir: Path = DEFAULT_MOBILE_DOCUMENT_INBOX,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    max_batches: int = 20,
    force_reprocess: bool = False,
) -> tuple[list[MobileDocumentProcessItem], str]:
    inbox = mobile_inbox_dir.expanduser().resolve()
    if not inbox.exists() or not inbox.is_dir():
        raise ValueError(f"mobile inbox neexistuje nebo neni slozka: {inbox}")

    request_path = inbox / "process_request.json"
    if not request_path.exists():
        raise ValueError("chybi process_request.json; spust zkratku `Zpracovat dokumenty pro Samanthu`.")
    request = read_json_file(request_path)
    request_name = safe_text(str(request.get("request", ""))).strip()
    if request_name and request_name != "process_mobile_document_inbox":
        raise ValueError(f"process_request.json ma neznamy request: {request_name}")
    request_status = safe_text(str(request.get("status", ""))).strip().casefold()
    if request_status in {"processed", "done", "hotovo"} and not force_reprocess:
        raise ValueError("process_request.json je uz oznaceny jako processed; pro opakovani pouzij force_reprocess=True.")

    manifests = select_mobile_process_manifests(
        inbox=inbox,
        batch_id=batch_id,
        max_batches=max(1, min(max_batches, 50)),
    )
    items: list[MobileDocumentProcessItem] = []
    run_started_at = datetime.now(timezone.utc).replace(microsecond=0)
    for manifest_path, manifest in manifests:
        raw_batch_id = safe_text(str(manifest.get("batch_id", ""))).strip()
        title = safe_text(str(manifest.get("document_title", ""))).strip() or raw_batch_id
        try:
            existing = find_existing_prepared_mobile_batch(
                vault_dir=vault_dir,
                batch_id=raw_batch_id,
                source_manifest=manifest_path,
            )
            if existing is None:
                prepared = prepare_mobile_document_batch(
                    batch_id=raw_batch_id,
                    mobile_inbox_dir=inbox,
                    vault_dir=vault_dir,
                )
                status = "prepared"
            else:
                prepared = existing
                status = "reprocessed" if force_reprocess else "already_prepared"
            item = analyze_prepared_mobile_document(
                prepared=prepared,
                status=status,
                vault_dir=vault_dir,
                force_reprocess=force_reprocess,
            )
        except ValueError as exc:
            item = MobileDocumentProcessItem(
                batch_id=raw_batch_id or safe_text(manifest_path.stem),
                document_title=title,
                status="failed",
                page_count=0,
                warning=str(exc),
            )
        items.append(item)

    process_record = {
        "schema_version": "1",
        "request": "process_mobile_document_inbox",
        "status": "processed" if all(item.status != "failed" for item in items) else "partial",
        "processed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "started_at": run_started_at.isoformat(),
        "batch_count": len(items),
        "batches": [
            {
                "batch_id": item.batch_id,
                "document_title": item.document_title,
                "status": item.status,
                "pdf_path": str(relative_to_project(item.pdf_path)) if item.pdf_path else "",
                "manifest_path": str(relative_to_project(item.manifest_path)) if item.manifest_path else "",
                "document_type": item.document_type,
                "domain": item.domain,
                "due_date_count": item.due_date_count,
                "warning": item.warning,
            }
            for item in items
        ],
        "source_preserved": True,
        "final_import_done": False,
        "do_not_commit": True,
    }
    append_jsonl(vault_dir / "index" / "mobile_process_runs.jsonl", process_record)
    request_warning = write_mobile_process_result(
        request_path=request_path,
        process_record=process_record,
    )
    return items, request_warning


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
    case_id: str = "",
    document_title: str = "",
    reading_status: str = "",
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
        metadata["document_type"] = safe_ascii_slug(document_type, default="document", limit=50)
    safe_reading_status = safe_slug(reading_status, default="", limit=50)
    if safe_reading_status and safe_reading_status not in {"ok", "needs_review", "unreadable", "superseded"}:
        raise ValueError("Neplatny stav cteni dokumentu.")
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
        "title": safe_text(document_title),
        "original_filename": source.name,
        "stored_path": str(relative_to_project(destination)),
        "domain": normalized_domain,
        "document_type": metadata["document_type"],
        "counterparty": safe_text(str(metadata.get("counterparty") or "")),
        "related_asset": safe_text(str(metadata.get("related_asset") or "")),
        "case_id": safe_ascii_slug(case_id, default="", limit=100) if case_id else "",
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
    if safe_reading_status:
        record["reading_status"] = safe_reading_status
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


def preview_document_reindex_summary(
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    max_documents: int = 50,
    mode: str = "improve_weak",
) -> str:
    proposals = build_document_reindex_proposals(
        vault_dir=vault_dir,
        max_documents=max_documents,
        mode=mode,
    )
    documents = read_jsonl(vault_dir / "index" / "documents_index.jsonl")
    lines = [
        "Navrh reindexu ulozenych dokumentu (read-only):",
        f"- Dokumentu v indexu: {len(documents)}",
        f"- Dokumentu s navrzenou zmenou: {len(proposals)}",
        f"- Rezim: {safe_text(mode)}",
    ]
    if not proposals:
        lines.append("- Nic k doplneni podle aktualnich pravidel.")
    for proposal in proposals[:max(1, min(max_documents, 20))]:
        changed_fields = ", ".join(proposal.changes.keys())
        lines.append(f"- {safe_text(proposal.document_id)} | zmeny: {safe_text(changed_fields)}")
        for field, change in proposal.changes.items():
            before = redact_reindex_value(field, change.get("before"))
            after = redact_reindex_value(field, change.get("after"))
            lines.append(f"  {field}: {before} -> {after}")
    if len(proposals) > 20:
        lines.append(f"- ... dalsich {len(proposals) - 20} navrhu")
    lines.append("")
    lines.append(
        "Bezpecnost: nic nebylo zapsano. Pro aplikaci je nutne samostatne potvrzeni "
        "s textem obsahujicim `potvrzuji` a `reindex`."
    )
    return "\n".join(lines)


def apply_document_reindex_summary(
    user_confirmed: bool = False,
    confirmation_text: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    max_documents: int = 50,
    mode: str = "improve_weak",
) -> str:
    if not has_explicit_reindex_confirmation(user_confirmed, confirmation_text):
        return (
            "Reindex ulozenych dokumentu nebyl spusten.\n"
            "Bezpecnost: jde o zapis do soukromeho vaultu. Potvrd vetou obsahujici `potvrzuji` a `reindex`."
        )
    proposals = build_document_reindex_proposals(
        vault_dir=vault_dir,
        max_documents=max_documents,
        mode=mode,
    )
    if not proposals:
        return "Reindex ulozenych dokumentu: zadne zmeny k aplikaci."

    backup_dir = backup_reindex_targets(vault_dir=vault_dir, proposals=proposals)
    document_rows = read_jsonl(vault_dir / "index" / "documents_index.jsonl")
    updated_by_id = {proposal.document_id: apply_reindex_changes_to_record(proposal) for proposal in proposals}
    new_rows = [updated_by_id.get(str(row.get("document_id", "")), row) for row in document_rows]
    write_jsonl(vault_dir / "index" / "documents_index.jsonl", new_rows)
    for proposal in proposals:
        write_json(proposal.manifest_path, updated_by_id[proposal.document_id])
    append_jsonl(
        vault_dir / "index" / "document_reindex_runs.jsonl",
        {
            "run_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "mode": safe_text(mode),
            "changed_count": len(proposals),
            "backup_dir": str(relative_to_project(backup_dir)),
            "document_ids": [proposal.document_id for proposal in proposals],
        },
    )
    return (
        "Reindex ulozenych dokumentu dokoncen.\n"
        f"- Upravenych dokumentu: {len(proposals)}\n"
        f"- Zaloha pred zmenou: `{relative_to_project(backup_dir)}`\n"
        "- Aktualizovano: manifesty a `index/documents_index.jsonl`.\n"
        "Bezpecnost: PDF ani textovy index nebyly meneny."
    )


def build_document_reindex_proposals(
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    max_documents: int = 50,
    mode: str = "improve_weak",
) -> list[DocumentReindexProposal]:
    mode = normalize_reindex_mode(mode)
    documents = read_jsonl(vault_dir / "index" / "documents_index.jsonl")
    text_by_id = {
        str(row.get("document_id", "")): str(row.get("text", ""))
        for row in read_jsonl(vault_dir / "index" / "text_index.jsonl")
    }
    proposals: list[DocumentReindexProposal] = []
    for row in documents[: max(1, min(max_documents, 500))]:
        document_id = safe_slug(str(row.get("document_id", "")), default="", limit=140)
        if not document_id:
            continue
        stored_path = PROJECT_ROOT / str(row.get("stored_path", ""))
        if not stored_path.exists():
            continue
        manifest_path = stored_path.parent / "manifest.json"
        manifest = read_json_file(manifest_path) if manifest_path.exists() else {}
        current = {**row, **manifest}
        text = text_by_id.get(document_id, "")
        if not text.strip():
            text = reindex_metadata_fallback_text(current=current, source=stored_path)
        proposed_metadata = propose_metadata(source=stored_path, text=text)
        proposed = {
            "title": suggest_reindex_title(current=current, source=stored_path),
            "domain": proposed_metadata.get("domain", ""),
            "document_type": proposed_metadata.get("document_type", ""),
            "counterparty": proposed_metadata.get("counterparty", ""),
            "related_asset": proposed_metadata.get("related_asset", ""),
            "tags": proposed_metadata.get("tags", []),
        }
        changes = build_reindex_changes(current=current, proposed=proposed, mode=mode)
        if changes:
            proposals.append(
                DocumentReindexProposal(
                    document_id=document_id,
                    stored_path=stored_path,
                    manifest_path=manifest_path,
                    current=current,
                    proposed=proposed,
                    changes=changes,
                )
            )
    return proposals


def normalize_reindex_mode(mode: str) -> str:
    safe = safe_slug(mode, default="improve_weak", limit=40)
    if safe not in {"fill_blank", "improve_weak", "force"}:
        return "improve_weak"
    return safe


def build_reindex_changes(
    current: dict[str, Any],
    proposed: dict[str, Any],
    mode: str,
) -> dict[str, dict[str, Any]]:
    changes: dict[str, dict[str, Any]] = {}
    for field in ("domain", "document_type", "counterparty", "related_asset"):
        before = normalize_reindex_scalar(current.get(field, ""))
        after = normalize_reindex_scalar(proposed.get(field, ""))
        if should_update_reindex_field(field=field, before=before, after=after, mode=mode):
            changes[field] = {"before": before, "after": after}
    before_tags = [str(tag) for tag in current.get("tags", []) if isinstance(tag, str)]
    after_tags = merge_tags(before_tags, [str(tag) for tag in proposed.get("tags", []) if isinstance(tag, str)])
    if changes and after_tags != merge_tags(before_tags, []):
        changes["tags"] = {"before": before_tags, "after": after_tags}
    return changes


def should_update_reindex_field(field: str, before: str, after: str, mode: str) -> bool:
    if not after or before == after:
        return False
    if mode == "force":
        return True
    if not before or before in {"nezjisteno", "unknown", "none"}:
        return True
    if mode == "fill_blank":
        return False
    if field == "domain":
        return before == "other" and after != "other"
    if field == "document_type":
        return before in {"document", "contract"} and after not in {"document", "contract"}
    if field == "related_asset":
        return before in {"auto", "byt"} and after not in {"auto", "byt"}
    return False


def normalize_reindex_scalar(value: Any) -> str:
    return safe_text(str(value or "")).strip()


def suggest_reindex_title(current: dict[str, Any], source: Path) -> str:
    title = normalize_reindex_scalar(current.get("title", ""))
    if title:
        return title
    stem = split_camel_case_text(source.stem).replace("_", " ").replace("-", " ")
    return normalize_whitespace(stem).title()


def reindex_metadata_fallback_text(current: dict[str, Any], source: Path) -> str:
    parts = [
        source.name,
        str(current.get("original_filename", "")),
        str(current.get("document_id", "")),
        str(current.get("document_type", "")),
        str(current.get("domain", "")),
        str(current.get("counterparty", "")),
        str(current.get("related_asset", "")),
        " ".join(str(tag) for tag in current.get("tags", []) if isinstance(tag, str)),
    ]
    return "\n".join(parts)


def apply_reindex_changes_to_record(proposal: DocumentReindexProposal) -> dict[str, Any]:
    updated = dict(proposal.current)
    for field, change in proposal.changes.items():
        updated[field] = change["after"]
    updated["reindexed_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    updated["reindex_source"] = "document_reindex"
    return updated


def backup_reindex_targets(vault_dir: Path, proposals: list[DocumentReindexProposal]) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = vault_dir / "index" / "reindex_backups" / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    index_path = vault_dir / "index" / "documents_index.jsonl"
    if index_path.exists():
        shutil.copy2(index_path, backup_dir / "documents_index.jsonl")
    manifest_dir = backup_dir / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    for proposal in proposals:
        if proposal.manifest_path.exists():
            shutil.copy2(proposal.manifest_path, manifest_dir / f"{proposal.document_id}.manifest.json")
    return backup_dir


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    atomic_write_text(path, payload)


def has_explicit_reindex_confirmation(user_confirmed: bool, confirmation_text: str) -> bool:
    if not user_confirmed:
        return False
    normalized = normalize_confirmation_text(confirmation_text)
    return "reindex" in normalized and any(word in normalized for word in ("potvrzuji", "ano"))


def redact_reindex_value(field: str, value: Any) -> str:
    if field in {"counterparty", "related_asset", "title"}:
        return "[vyplneno]" if normalize_reindex_scalar(value) else "[prazdne]"
    if field == "tags" and isinstance(value, list):
        return ", ".join(safe_text(str(tag)) for tag in value[:10])
    return safe_text(str(value or ""))


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


def select_mobile_process_manifests(
    inbox: Path,
    batch_id: str = "",
    max_batches: int = 20,
) -> list[tuple[Path, dict[str, Any]]]:
    wanted = safe_text(batch_id).strip()
    if wanted:
        return [select_mobile_batch_manifest(inbox=inbox, batch_id=wanted)]

    manifests = sorted(
        inbox.glob("scan_*_manifest.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not manifests:
        raise ValueError("v mobile inboxu neni zadny scan manifest.")

    selected: list[tuple[Path, dict[str, Any]]] = []
    for path in manifests[:max_batches]:
        selected.append((path, read_json_file(path)))
    return selected


def find_existing_prepared_mobile_batch(
    vault_dir: Path,
    batch_id: str,
    source_manifest: Path,
) -> MobileDocumentBatchResult | None:
    wanted_source = str(source_manifest)
    for row in reversed(read_jsonl(vault_dir / "index" / "mobile_batches.jsonl")):
        if safe_text(str(row.get("batch_id", ""))).strip() != batch_id:
            continue
        if str(row.get("source_manifest", "")) != wanted_source:
            continue
        pdf_path = project_path_from_record(str(row.get("pdf_path", "")))
        manifest_path = pdf_path.parent / "manifest.json"
        if not pdf_path.exists() or not manifest_path.exists():
            continue
        document_title = safe_text(str(row.get("document_title", ""))).strip() or batch_id
        page_count = len(row.get("normalized_pages", [])) if isinstance(row.get("normalized_pages"), list) else 0
        return MobileDocumentBatchResult(
            batch_id=batch_id,
            document_title=document_title,
            page_count=page_count,
            processing_dir=pdf_path.parent,
            pdf_path=pdf_path,
            manifest_path=manifest_path,
        )
    return None


def analyze_prepared_mobile_document(
    prepared: MobileDocumentBatchResult,
    status: str,
    vault_dir: Path,
    force_reprocess: bool = False,
) -> MobileDocumentProcessItem:
    analysis_path = prepared.processing_dir / "analysis.json"
    text_path = prepared.processing_dir / "extracted_text.txt"
    if analysis_path.exists() and text_path.exists() and not force_reprocess:
        analysis = read_json_file(analysis_path)
        return MobileDocumentProcessItem(
            batch_id=prepared.batch_id,
            document_title=prepared.document_title,
            status=status,
            page_count=prepared.page_count,
            processing_dir=prepared.processing_dir,
            pdf_path=prepared.pdf_path,
            manifest_path=prepared.manifest_path,
            extraction_method=safe_text(str(analysis.get("extraction_method", ""))),
            ocr_needed=bool(analysis.get("ocr_needed", False)),
            document_type=safe_text(str(analysis.get("document_type", ""))),
            domain=safe_text(str(analysis.get("domain", ""))),
            due_date_count=int(analysis.get("due_date_count", 0) or 0),
            warning=safe_text(str(analysis.get("warning", ""))),
        )

    extraction = extract_text(prepared.pdf_path)
    text_path.write_text(extraction.text, encoding="utf-8")
    metadata = propose_metadata(
        source=prepared.pdf_path,
        text=extraction.text,
    )
    due_dates = find_due_date_candidates(extraction.text)
    analysis = {
        "schema_version": "1",
        "status": "analyzed",
        "analyzed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "batch_id": prepared.batch_id,
        "document_title": prepared.document_title,
        "pdf_path": str(relative_to_project(prepared.pdf_path)),
        "extracted_text_path": str(relative_to_project(text_path)),
        "extraction_method": extraction.method,
        "ocr_needed": extraction.ocr_needed,
        "warning": extraction.warning,
        "document_type": metadata.get("document_type", "document"),
        "domain": metadata.get("domain", "other"),
        "counterparty": metadata.get("counterparty", ""),
        "related_asset": metadata.get("related_asset", ""),
        "tags": metadata.get("tags", []),
        "due_date_count": len(due_dates),
        "due_dates": due_dates,
        "source_preserved": True,
        "final_import_done": False,
        "do_not_commit": True,
    }
    write_json(analysis_path, analysis)
    append_jsonl(vault_dir / "index" / "mobile_analyses.jsonl", analysis)

    processing_manifest = read_json_file(prepared.manifest_path)
    processing_manifest["status"] = "analyzed"
    processing_manifest["analysis_path"] = str(relative_to_project(analysis_path))
    processing_manifest["extracted_text_path"] = str(relative_to_project(text_path))
    processing_manifest["final_import_done"] = False
    write_json(prepared.manifest_path, processing_manifest)

    return MobileDocumentProcessItem(
        batch_id=prepared.batch_id,
        document_title=prepared.document_title,
        status=status,
        page_count=prepared.page_count,
        processing_dir=prepared.processing_dir,
        pdf_path=prepared.pdf_path,
        manifest_path=prepared.manifest_path,
        extraction_method=extraction.method,
        ocr_needed=extraction.ocr_needed,
        document_type=safe_text(str(metadata.get("document_type", "document"))),
        domain=safe_text(str(metadata.get("domain", "other"))),
        due_date_count=len(due_dates),
        warning=extraction.warning,
    )


def find_prepared_mobile_batch_for_import(
    vault_dir: Path,
    batch_id: str = "",
    include_imported: bool = False,
) -> MobileDocumentBatchResult:
    wanted = safe_text(batch_id).strip()
    records = list(reversed(read_jsonl(vault_dir / "index" / "mobile_batches.jsonl")))
    if not records:
        raise ValueError("neni pripraveny zadny mobilni dokument; nejdrive spust process_mobile_document_inbox.")

    skipped_imported = False
    for row in records:
        row_batch_id = safe_text(str(row.get("batch_id", ""))).strip()
        if wanted and row_batch_id != wanted:
            continue
        pdf_path = project_path_from_record(str(row.get("pdf_path", "")))
        manifest_path = pdf_path.parent / "manifest.json"
        if not pdf_path.exists() or not manifest_path.exists():
            continue
        manifest = read_json_file(manifest_path)
        if manifest.get("final_import_done") and not include_imported:
            skipped_imported = True
            continue
        document_title = safe_text(str(row.get("document_title", ""))).strip() or row_batch_id
        page_count = len(row.get("normalized_pages", [])) if isinstance(row.get("normalized_pages"), list) else 0
        return MobileDocumentBatchResult(
            batch_id=row_batch_id,
            document_title=document_title,
            page_count=page_count,
            processing_dir=pdf_path.parent,
            pdf_path=pdf_path,
            manifest_path=manifest_path,
        )

    if wanted:
        raise ValueError(f"pripraveny batch {wanted} nebyl nalezen nebo uz byl importovan.")
    if skipped_imported:
        raise ValueError("vsechny nalezene mobilni dokumenty uz jsou finalne importovane.")
    raise ValueError("neni pripraveny zadny mobilni dokument s existujicim PDF.")


def ensure_prepared_mobile_analysis(
    prepared: MobileDocumentBatchResult,
    vault_dir: Path,
) -> dict[str, Any]:
    analysis_path = prepared.processing_dir / "analysis.json"
    if not analysis_path.exists():
        analyze_prepared_mobile_document(
            prepared=prepared,
            status="analyzed",
            vault_dir=vault_dir,
            force_reprocess=False,
        )
    return read_json_file(analysis_path)


def choose_mobile_final_metadata(
    analysis: dict[str, Any],
    target_domain: str = "",
    document_type: str = "",
    counterparty: str = "",
    related_asset: str = "",
    tags: str = "",
    case_id: str = "",
) -> MobileDocumentFinalMetadata:
    analysis_tags = analysis.get("tags", [])
    if not isinstance(analysis_tags, list):
        analysis_tags = []
    merged_tags = merge_tags(
        parse_tags(tags),
        [safe_text(str(tag)) for tag in analysis_tags],
    )
    return MobileDocumentFinalMetadata(
        domain=normalize_domain(target_domain or safe_text(str(analysis.get("domain", "other")))),
        document_type=safe_ascii_slug(
            document_type or safe_text(str(analysis.get("document_type", "document"))),
            default="document",
            limit=50,
        ),
        counterparty=safe_text(counterparty or str(analysis.get("counterparty", ""))),
        related_asset=safe_text(related_asset or str(analysis.get("related_asset", ""))),
        tags=", ".join(merged_tags),
        case_id=safe_ascii_slug(case_id, default="", limit=100) if case_id else "",
    )


def mark_mobile_document_final_import(
    prepared: MobileDocumentBatchResult,
    result: DocumentImportResult,
    metadata: MobileDocumentFinalMetadata,
    vault_dir: Path,
) -> None:
    imported_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    import_record = {
        "schema_version": "1",
        "batch_id": prepared.batch_id,
        "document_title": prepared.document_title,
        "document_id": result.document_id,
        "created": result.created,
        "imported_at": imported_at,
        "source_pdf": str(relative_to_project(prepared.pdf_path)),
        "stored_path": str(relative_to_project(result.destination)),
        "manifest_path": str(relative_to_project(result.manifest)),
        "domain": metadata.domain,
        "document_type": metadata.document_type,
        "counterparty": metadata.counterparty,
        "related_asset": metadata.related_asset,
        "tags": parse_tags(metadata.tags),
        "case_id": metadata.case_id,
        "source_preserved": True,
        "do_not_commit": True,
    }
    append_jsonl(vault_dir / "index" / "mobile_final_imports.jsonl", import_record)

    processing_manifest = read_json_file(prepared.manifest_path)
    processing_manifest["final_import_done"] = True
    processing_manifest["final_imported_at"] = imported_at
    processing_manifest["final_document_id"] = result.document_id
    processing_manifest["final_stored_path"] = str(relative_to_project(result.destination))
    processing_manifest["final_manifest_path"] = str(relative_to_project(result.manifest))
    processing_manifest["case_id"] = metadata.case_id
    write_json(prepared.manifest_path, processing_manifest)

    analysis_path = prepared.processing_dir / "analysis.json"
    if analysis_path.exists():
        analysis = read_json_file(analysis_path)
        analysis["final_import_done"] = True
        analysis["final_imported_at"] = imported_at
        analysis["final_document_id"] = result.document_id
        analysis["final_stored_path"] = str(relative_to_project(result.destination))
        analysis["case_id"] = metadata.case_id
        write_json(analysis_path, analysis)


def write_mobile_process_result(
    request_path: Path,
    process_record: dict[str, Any],
) -> str:
    result_path = request_path.with_name("process_result.json")
    try:
        write_json(result_path, process_record)
        request = read_json_file(request_path)
        request["status"] = process_record["status"]
        request["processed_at"] = process_record["processed_at"]
        request["process_result"] = result_path.name
        write_json(request_path, request)
    except OSError as exc:
        return f"nepodarilo se zapsat process_result/process_request: {exc}"
    except ValueError as exc:
        return f"nepodarilo se aktualizovat process_request: {exc}"
    return ""


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
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    except ImportError as exc:
        raise ValueError("chybi Python balik Pillow pro zpracovani obrazku.") from exc

    try:
        from pillow_heif import register_heif_opener

        register_heif_opener()
    except ImportError:
        pass

    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        normalized = ImageOps.exif_transpose(image).convert("RGB")
        if should_use_mobile_document_raw_profile():
            normalized.save(target, format="JPEG", quality=94, optimize=True)
            return
        rectified = rectify_mobile_document_page_with_opencv(normalized)
        if rectified is not None:
            normalized = rectified
        else:
            normalized = crop_mobile_page_area(normalized)
            normalized = crop_mobile_document_content(normalized, padding_ratio=0.08)
            deskew_angle = estimate_mobile_document_skew_angle(normalized)
            if abs(deskew_angle) >= 0.25:
                normalized = normalized.rotate(deskew_angle, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=(255, 255, 255))
                normalized = crop_mobile_page_area(normalized)
                normalized = crop_mobile_document_content(normalized, padding_ratio=0.05)
        normalized = ImageOps.autocontrast(normalized, cutoff=1)
        normalized = ImageEnhance.Brightness(normalized).enhance(1.18)
        normalized = ImageEnhance.Contrast(normalized).enhance(1.10)
        normalized = normalized.filter(ImageFilter.SHARPEN)
        if should_use_mobile_document_bw_profile():
            normalized = clean_mobile_document_as_black_white(normalized)
        normalized.save(target, format="JPEG", quality=92, optimize=True)


def should_use_mobile_document_raw_profile() -> bool:
    value = os.environ.get("SAMANTHA_DOCUMENT_CLEAN_PROFILE", "raw").strip().casefold()
    return value in {"raw", "original", "none", "passthrough"}


def should_use_mobile_document_bw_profile() -> bool:
    value = os.environ.get("SAMANTHA_DOCUMENT_CLEAN_PROFILE", "raw").strip().casefold()
    return value not in {"0", "false", "no", "color", "colour", "rgb"}


def clean_mobile_document_as_black_white(image: Any) -> Any:
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
        from PIL import Image, ImageFilter, ImageOps
    except Exception:
        return image

    grayscale = ImageOps.autocontrast(image.convert("L"), cutoff=1)
    array = np.array(grayscale)
    if array.size == 0:
        return image

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(array)
    background = cv2.GaussianBlur(enhanced, (0, 0), sigmaX=45, sigmaY=45)
    flattened = cv2.divide(enhanced, background, scale=255)
    flattened = cv2.GaussianBlur(flattened, (3, 3), 0)
    _, thresholded = cv2.threshold(flattened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    thresholded = remove_mobile_scan_noise_components(thresholded, cv2=cv2, np=np)
    thresholded = remove_mobile_scan_margin_artifacts(thresholded, cv2=cv2, np=np)
    cleaned = Image.fromarray(thresholded, mode="L")
    cleaned = crop_mobile_document_content(cleaned.convert("RGB"), padding_ratio=0.015).convert("L")
    cleaned = remove_light_edge_noise(cleaned)
    cleaned = place_mobile_document_on_a4_canvas(cleaned)
    return cleaned.filter(ImageFilter.SHARPEN).convert("RGB")


def remove_mobile_scan_noise_components(thresholded: Any, cv2: Any, np: Any) -> Any:
    black_mask = (thresholded < 128).astype("uint8")
    component_count, labels, stats, _ = cv2.connectedComponentsWithStats(black_mask, connectivity=8)
    cleaned_mask = np.zeros_like(black_mask)
    height, width = black_mask.shape[:2]
    edge_margin = max(3, int(min(width, height) * 0.006))
    min_area = max(3, int(width * height * 0.0000015))
    for label in range(1, component_count):
        x, y, w, h, area = stats[label]
        touches_edge = (
            x <= edge_margin
            or y <= edge_margin
            or x + w >= width - edge_margin
            or y + h >= height - edge_margin
        )
        if area <= min_area:
            continue
        if touches_edge and area > min_area * 8:
            continue
        cleaned_mask[labels == label] = 1
    return np.where(cleaned_mask > 0, 0, 255).astype("uint8")


def remove_mobile_scan_margin_artifacts(thresholded: Any, cv2: Any, np: Any) -> Any:
    black_mask = (thresholded < 128).astype("uint8")
    component_count, labels, stats, _ = cv2.connectedComponentsWithStats(black_mask, connectivity=8)
    cleaned_mask = np.zeros_like(black_mask)
    height, width = black_mask.shape[:2]
    min_area = max(4, int(width * height * 0.000002))
    side_band = int(width * 0.07)
    top_band = int(height * 0.08)
    bottom_band = int(height * 0.04)
    for label in range(1, component_count):
        x, y, w, h, area = stats[label]
        if area <= min_area:
            continue
        near_left = x < side_band
        near_right = x + w > width - side_band
        near_top = y < top_band
        near_bottom = y + h > height - bottom_band
        long_horizontal = w > width * 0.18 and h < height * 0.035
        long_vertical = h > height * 0.18 and w < width * 0.04
        bulky_margin_mark = area > min_area * 12 and (near_left or near_right or near_top or near_bottom)
        if near_bottom and long_horizontal:
            continue
        if near_top and long_horizontal and (near_left or near_right) and area > min_area * 10:
            continue
        if long_horizontal:
            cleaned_mask[labels == label] = 1
            continue
        if (near_left or near_right) and (long_vertical or bulky_margin_mark):
            continue
        if (near_left or near_right) and area > min_area * 24:
            continue
        cleaned_mask[labels == label] = 1
    return np.where(cleaned_mask > 0, 0, 255).astype("uint8")


def remove_light_edge_noise(image: Any) -> Any:
    width, height = image.size
    if width <= 0 or height <= 0:
        return image
    pixels = image.load()
    edge = max(8, int(min(width, height) * 0.012))
    for y in range(height):
        for x in range(width):
            if x >= edge and y >= edge and x < width - edge and y < height - edge:
                continue
            if pixels[x, y] > 105:
                pixels[x, y] = 255
    return image


def place_mobile_document_on_a4_canvas(image: Any) -> Any:
    from PIL import Image

    canvas_width, canvas_height = 1240, 1754
    margin_x = 40
    margin_y = 52
    available_width = canvas_width - 2 * margin_x
    available_height = canvas_height - 2 * margin_y
    width, height = image.size
    if width <= 0 or height <= 0:
        return image
    scale = min(available_width / width, available_height / height)
    resized = image.resize(
        (max(1, int(width * scale)), max(1, int(height * scale))),
        resample=Image.Resampling.LANCZOS,
    )
    canvas = Image.new("L", (canvas_width, canvas_height), 255)
    left = (canvas_width - resized.width) // 2
    top = (canvas_height - resized.height) // 2
    canvas.paste(resized, (left, top))
    return canvas


def rectify_mobile_document_page_with_opencv(image: Any) -> Any | None:
    if os.environ.get("SAMANTHA_DOCUMENT_OPENCV_RECTIFY", "0").casefold() not in {"1", "true", "yes"}:
        return None

    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
        from PIL import Image
    except Exception:
        return None

    rgb = np.array(image.convert("RGB"))
    height, width = rgb.shape[:2]
    max_dimension = 1400
    scale = max(width, height) / max_dimension if max(width, height) > max_dimension else 1.0
    small = cv2.resize(rgb, (int(width / scale), int(height / scale)), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
    image_area = small.shape[0] * small.shape[1]
    page_quad = detect_document_quad_from_bright_page(
        gray=gray,
        cv2=cv2,
        np=np,
        image_area=image_area,
        scale=scale,
    )
    if page_quad is None:
        page_quad = detect_document_quad_from_edges(
            gray=gray,
            cv2=cv2,
            image_area=image_area,
            scale=scale,
        )

    if page_quad is None:
        return None

    rect = order_quad_points(page_quad, np=np)
    top_left, top_right, bottom_right, bottom_left = rect
    width_top = np.linalg.norm(top_right - top_left)
    width_bottom = np.linalg.norm(bottom_right - bottom_left)
    height_left = np.linalg.norm(bottom_left - top_left)
    height_right = np.linalg.norm(bottom_right - top_right)
    target_width = int(max(width_top, width_bottom))
    target_height = int(max(height_left, height_right))
    if target_width < width * 0.35 or target_height < height * 0.35:
        return None
    if target_width * target_height < width * height * 0.18:
        return None

    destination = np.array(
        [
            [0, 0],
            [target_width - 1, 0],
            [target_width - 1, target_height - 1],
            [0, target_height - 1],
        ],
        dtype="float32",
    )
    matrix = cv2.getPerspectiveTransform(rect, destination)
    warped = cv2.warpPerspective(rgb, matrix, (target_width, target_height), borderMode=cv2.BORDER_REPLICATE)
    if warped.shape[1] > warped.shape[0]:
        warped = cv2.rotate(warped, cv2.ROTATE_90_CLOCKWISE)
    return Image.fromarray(warped)


def detect_document_quad_from_bright_page(gray: Any, cv2: Any, np: Any, image_area: int, scale: float) -> Any | None:
    otsu_threshold_value, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    threshold = min(255, int(otsu_threshold_value) + 5)
    _, mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:5]:
        if cv2.contourArea(contour) < image_area * 0.35:
            continue
        hull = cv2.convexHull(contour)
        perimeter = cv2.arcLength(hull, True)
        for epsilon in (0.02, 0.025, 0.03, 0.04, 0.05):
            approx = cv2.approxPolyDP(hull, epsilon * perimeter, True)
            if len(approx) == 4:
                return approx.reshape(4, 2).astype("float32") * scale
    return None


def detect_document_quad_from_edges(gray: Any, cv2: Any, image_area: int, scale: float) -> Any | None:
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 40, 120)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    edges = cv2.dilate(edges, kernel, iterations=1)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:12]:
        area = cv2.contourArea(contour)
        if area < image_area * 0.22:
            continue
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.025 * perimeter, True)
        if len(approx) == 4:
            return approx.reshape(4, 2).astype("float32") * scale
    return None


def order_quad_points(points: Any, np: Any) -> Any:
    rect = np.zeros((4, 2), dtype="float32")
    sums = points.sum(axis=1)
    diffs = np.diff(points, axis=1)
    rect[0] = points[np.argmin(sums)]
    rect[2] = points[np.argmax(sums)]
    rect[1] = points[np.argmin(diffs)]
    rect[3] = points[np.argmax(diffs)]
    return rect


def crop_mobile_page_area(image: Any) -> Any:
    grayscale = image.convert("L")
    threshold = min(235, otsu_threshold(grayscale) + 20)
    mask = grayscale.point(lambda pixel: 255 if pixel > threshold else 0)
    bbox = mask.getbbox()
    if not bbox:
        return image

    left, top, right, bottom = bbox
    width, height = image.size
    crop_area = (right - left) * (bottom - top)
    original_area = width * height
    if crop_area < original_area * 0.35:
        return image
    if (right - left) < width * 0.45 or (bottom - top) < height * 0.45:
        return image

    margin_x = max(12, int((right - left) * 0.015))
    margin_y = max(12, int((bottom - top) * 0.015))
    left = max(0, left - margin_x)
    top = max(0, top - margin_y)
    right = min(width, right + margin_x)
    bottom = min(height, bottom + margin_y)
    if (right - left) >= width * 0.985 and (bottom - top) >= height * 0.985:
        return image
    return image.crop((left, top, right, bottom))


def crop_mobile_document_content(image: Any, padding_ratio: float = 0.06) -> Any:
    from PIL import ImageOps

    width, height = image.size
    inset_x = max(0, int(width * 0.025))
    inset_y = max(0, int(height * 0.025))
    working = image.crop((inset_x, inset_y, width - inset_x, height - inset_y))
    grayscale = ImageOps.autocontrast(working.convert("L"), cutoff=1)
    threshold = estimate_dark_content_threshold(grayscale)
    mask = grayscale.point(lambda pixel: 255 if pixel < threshold else 0)
    bbox = mask.getbbox()
    if not bbox:
        return image

    left, top, right, bottom = bbox
    left += inset_x
    right += inset_x
    top += inset_y
    bottom += inset_y
    crop_width = right - left
    crop_height = bottom - top
    original_area = width * height
    crop_area = crop_width * crop_height
    if crop_area < original_area * 0.03:
        return image
    if crop_width < width * 0.2 or crop_height < height * 0.08:
        return image

    margin_x = max(18, int(crop_width * padding_ratio))
    margin_y = max(18, int(crop_height * padding_ratio))
    left = max(0, left - margin_x)
    top = max(0, top - margin_y)
    right = min(width, right + margin_x)
    bottom = min(height, bottom + margin_y)

    if (right - left) >= width * 0.98 and (bottom - top) >= height * 0.98:
        return image
    return image.crop((left, top, right, bottom))


def otsu_threshold(grayscale: Any) -> int:
    histogram = grayscale.histogram()
    total = sum(histogram)
    if total <= 0:
        return 128
    sum_total = sum(value * count for value, count in enumerate(histogram))
    sum_background = 0
    weight_background = 0
    best_threshold = 128
    best_variance = 0.0
    for value, count in enumerate(histogram):
        weight_background += count
        if weight_background <= 0:
            continue
        weight_foreground = total - weight_background
        if weight_foreground <= 0:
            break
        sum_background += value * count
        mean_background = sum_background / weight_background
        mean_foreground = (sum_total - sum_background) / weight_foreground
        variance = weight_background * weight_foreground * (mean_background - mean_foreground) ** 2
        if variance > best_variance:
            best_variance = variance
            best_threshold = value
    return best_threshold


def estimate_dark_content_threshold(grayscale: Any) -> int:
    histogram = grayscale.histogram()
    total = sum(histogram)
    if total <= 0:
        return 210
    dark_pixels = 0
    threshold = 210
    # Prefer the darkest 35 percent at most; this avoids treating mild paper
    # shade as content while still catching grey text from phone scans.
    for value, count in enumerate(histogram):
        dark_pixels += count
        if dark_pixels / total >= 0.35:
            threshold = max(135, min(215, value + 12))
            break
    return threshold


def estimate_mobile_document_skew_angle(image: Any) -> float:
    from PIL import Image, ImageOps

    grayscale = ImageOps.autocontrast(image.convert("L"), cutoff=1)
    max_width = 900
    if grayscale.width > max_width:
        ratio = max_width / grayscale.width
        grayscale = grayscale.resize(
            (max_width, max(1, int(grayscale.height * ratio))),
            resample=Image.Resampling.BILINEAR,
        )

    threshold = estimate_dark_content_threshold(grayscale)
    angles = [value / 2 for value in range(-10, 11)]
    best_angle = 0.0
    best_score = 0.0
    for angle in angles:
        rotated = grayscale.rotate(angle, resample=Image.Resampling.BILINEAR, expand=True, fillcolor=255)
        score = horizontal_projection_score(rotated, threshold=threshold)
        if score > best_score:
            best_score = score
            best_angle = angle
    return best_angle


def horizontal_projection_score(grayscale: Any, threshold: int) -> float:
    width, height = grayscale.size
    if width <= 0 or height <= 0:
        return 0.0
    pixels = grayscale.load()
    row_counts: list[int] = []
    total_dark = 0
    step_x = max(1, width // 700)
    for y in range(height):
        count = 0
        for x in range(0, width, step_x):
            if pixels[x, y] < threshold:
                count += 1
        row_counts.append(count)
        total_dark += count
    if total_dark < max(40, width // step_x):
        return 0.0

    mean = total_dark / len(row_counts)
    variance = sum((count - mean) ** 2 for count in row_counts) / len(row_counts)
    transitions = sum(abs(row_counts[index] - row_counts[index - 1]) for index in range(1, len(row_counts)))
    return variance + transitions * 0.05


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

    if suffix in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".tif", ".tiff"}:
        return TextExtractionResult(
            text="",
            method="image-no-text",
            ocr_needed=True,
            warning="Obrázková příloha byla uložena bez textové vrstvy; pro fulltext je potřeba OCR.",
        )

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
    pdftotext = resolve_pdftotext_binary()
    if not pdftotext:
        return TextExtractionResult(text="", method="pdftotext-unavailable", ocr_needed=True)
    try:
        completed = subprocess.run(
            [pdftotext, "-layout", str(source), "-"],
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


def resolve_pdftotext_binary() -> str:
    found = shutil.which("pdftotext")
    if found:
        return found
    for candidate in (
        "/usr/local/bin/pdftotext",
        "/opt/homebrew/bin/pdftotext",
        "/usr/bin/pdftotext",
    ):
        if Path(candidate).is_file():
            return candidate
    return ""


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
    asset = safe_text(related_asset or guess_related_asset_for_document(source=source, text=text, folded=combined, document_type=document_type))
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
    if looks_like_travel_document(text):
        return "travel_booking"
    if looks_like_recipe_document(text):
        return "recipe"
    if looks_like_diet_guidance(text):
        return "diet_guidance"
    if looks_like_lease_document(text):
        return "lease"
    if any(word in text for word in ("smlouva", "contract")):
        return "contract"
    if has_stk_marker(text) or any(word in text for word in ("technicka kontrola", "technická kontrola", "emisni kontrola", "emisní kontrola", "revize", "revizni", "revizní")):
        return "inspection_report"
    if any(word in text for word in ("servis", "servisni", "servisní", "garanční prohlídka", "garancni prohlidka", "udrzba", "údržba", "zakazkovy list", "zakázkový list", "protokol")):
        return "service_report"
    if any(word in text for word in ("zaruka", "záruka", "warranty")):
        return "warranty"
    return "document"


def guess_domain(text: str, document_type: str) -> str:
    if document_type == "recipe":
        return "food"
    if document_type == "diet_guidance":
        return "health"
    if document_type == "travel_booking":
        return "travel"
    if document_type == "lease":
        return "home"
    vehicle_signal = has_vehicle_domain_signal(text)
    if vehicle_signal:
        if document_type in {"invoice", "service_report", "inspection_report", "green_card"}:
            return "car"
    if document_type == "insurance_policy":
        return "insurance"
    if any(word in text for word in ("pojist", "rixo", "pojistovna", "pojišťovna")):
        return "insurance"
    if any(word in text for word in ("t-mobile", "telefon", "mobilni sluzby", "mobilní služby", "telekomunika")):
        return "telecom"
    if any(
        word in text
        for word in (
            "fotovolta",
            "fve",
            "elektrina",
            "elektřina",
            "elektricke energie",
            "elektrické energie",
            "distribuc",
            "energie",
        )
    ):
        return "energy"
    if any(word in text for word in ("kotel", "komin", "komín", "dum", "dům", "home")):
        return "home"
    if vehicle_signal:
        return "car"
    if any(word in text for word in ("dan", "daň", "financni urad", "finanční úřad")):
        return "tax"
    if document_type == "warranty":
        return "warranty"
    return "other"


def has_stk_marker(text: str) -> bool:
    return has_short_token_marker(text, "stk")


def has_auto_marker(text: str) -> bool:
    return has_short_token_marker(text, "auto")


def has_short_token_marker(text: str, token: str) -> bool:
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])", text))


def has_car_marker(text: str) -> bool:
    return (
        has_auto_marker(text)
        or has_stk_marker(text)
        or has_short_token_marker(text, "spz")
        or has_short_token_marker(text, "rz")
        or has_short_token_marker(text, "vin")
        or any(word in text for word in ("vozidlo", "volvo", "motocykl", "motorka"))
    )


def has_vehicle_domain_signal(text: str) -> bool:
    return (
        has_auto_marker(text)
        or has_stk_marker(text)
        or has_short_token_marker(text, "spz")
        or has_short_token_marker(text, "rz")
        or has_short_token_marker(text, "vin")
        or any(
            phrase in text
            for phrase in (
                "vozidlo",
                "vozidla",
                "volvo",
                "v40",
                "motocykl",
                "motorka",
                "technicka kontrola",
                "technická kontrola",
                "emisni kontrola",
                "emisní kontrola",
            )
        )
    )


def looks_like_recipe_document(text: str) -> bool:
    strong_markers = (
        "recept",
        "recepty",
        "přísady",
        "prisady",
        "ingredience",
        "doba přípravy",
        "doba pripravy",
        "porce",
    )
    if any(marker in text for marker in strong_markers):
        return True
    recipe_words = (
        "salát",
        "salat",
        "polévka",
        "polevka",
        "brambor",
        "mrkev",
        "cuketa",
        "lžíce",
        "lzice",
        "ocet",
        "olej",
        "sůl",
        "sul",
        "vaříme",
        "varime",
        "nakrájíme",
        "nakrajime",
    )
    return sum(1 for marker in recipe_words if marker in text) >= 3


def looks_like_diet_guidance(text: str) -> bool:
    diet_markers = (
        "dieta",
        "dietní",
        "dietni",
        "jídelníček",
        "jidelnicek",
        "pacient",
        "potraviny",
        "purin",
        "sacharid",
        "bílkovin",
        "bilkovin",
        "vláknin",
        "vlaknin",
        "cukrovk",
        "diabet",
        "cholesterol",
        "dna ",
        " dnou",
    )
    return sum(1 for marker in diet_markers if marker in text) >= 2


def looks_like_lease_document(text: str) -> bool:
    lease_markers = (
        "nájemní smlouva",
        "najemni smlouva",
        "nájemce",
        "najemce",
        "pronajímatel",
        "pronajimatel",
        "nájemné",
        "najemne",
        r"\bbyt\b",
        r"\bbytu\b",
        "bytová jednotka",
        "bytova jednotka",
    )
    return sum(1 for marker in lease_markers if re.search(marker, text)) >= 2


def looks_like_travel_document(text: str) -> bool:
    travel_markers = (
        "booking.com",
        "rezervace",
        "potvrzení rezervace",
        "potvrzeni rezervace",
        "ubytování",
        "ubytovani",
        "check-in",
        "check-out",
        "hotel",
        "apartmán",
        "apartman",
        "pobyt",
        "pobytu",
        "dovolená",
        "dovolena",
    )
    return sum(1 for marker in travel_markers if marker in text) >= 2


def guess_counterparty(text: str) -> str:
    counterparty = guess_lease_counterparty(text)
    if counterparty:
        return counterparty
    for raw_line in text.splitlines()[:30]:
        line = normalize_whitespace(raw_line)
        folded = line.casefold()
        compact = re.sub(r"\s+", "", folded)
        if any(marker in folded for marker in ("s.r.o", "pojistovna", "pojišťovna", "servis", "rixo")) or "a.s" in compact:
            company = clean_counterparty_line(line)
            if 3 <= len(company) <= 120:
                return company
    return ""


def clean_counterparty_line(line: str) -> str:
    cleaned = normalize_whitespace(line)
    cleaned = re.split(
        r",\s*(?:IČO|ICO|Pobřežní|Pobrezni|se\s+sídlem|se\s+sidlem)\b",
        cleaned,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return cleaned.strip(" ,;")


def guess_lease_counterparty(text: str) -> str:
    structured_names = guess_lease_counterparty_from_party_block(text)
    if structured_names:
        return structured_names
    for raw_line in re.split(r"[\n\r.]+", text[:8000]):
        line = normalize_whitespace(raw_line)
        folded = line.casefold()
        if not folded.startswith(("nájemce:", "najemce:", "pronajímatel:", "pronajimatel:")):
            continue
        if ":" in line:
            candidate = normalize_whitespace(line.split(":", 1)[1])
            if 3 <= len(candidate) <= 100 and len(candidate.split()) >= 2:
                return candidate
    return ""


def guess_lease_counterparty_from_party_block(text: str) -> str:
    lines = [normalize_whitespace(line) for line in text[:12000].splitlines()]
    for index, line in enumerate(lines):
        folded = line.casefold()
        if "jako nájemce" not in folded and "jako najemce" not in folded:
            continue
        names: list[str] = []
        start = max(0, index - 40)
        for previous_index in range(index - 1, start - 1, -1):
            previous = lines[previous_index].casefold()
            if "jako pronajímatel" in previous or "jako pronajimatel" in previous:
                start = previous_index + 1
                break
        for candidate_line in lines[start:index]:
            candidate = extract_person_name_from_labeled_line(candidate_line)
            if candidate and candidate not in names:
                names.append(candidate)
        if names:
            return "; ".join(names[:3])
    return ""


def extract_person_name_from_labeled_line(line: str) -> str:
    folded = line.casefold()
    labels = (
        "titul, jméno a příjmení",
        "titul, jmeno a prijmeni",
        "jméno a příjmení",
        "jmeno a prijmeni",
    )
    if not any(label in folded for label in labels) or ":" not in line:
        return ""
    value = normalize_whitespace(line.split(":", 1)[1])
    value = re.split(r"\s+(?:e-mail|email|telefon|tel\.?)\b", value, maxsplit=1, flags=re.IGNORECASE)[0]
    value = value.split("|", 1)[0].strip(" ,;")
    if not 3 <= len(value) <= 100:
        return ""
    words = value.split()
    if len(words) < 2 or len(words) > 5:
        return ""
    if not all(re.match(r"^[A-ZÁ-Ž][\wÀ-ž.'-]*$", word) for word in words):
        return ""
    return value


def guess_related_asset_for_document(
    source: Path,
    text: str,
    folded: str,
    document_type: str,
) -> str:
    if document_type == "lease":
        return guess_lease_related_asset(source=source, text=text, folded=folded)
    if document_type == "travel_booking":
        return ""
    return guess_related_asset(text)


def guess_related_asset(text: str) -> str:
    folded = text.casefold()
    registration = extract_vehicle_registration(text)
    vehicle = guess_vehicle_kind(folded)
    vehicle_name = extract_vehicle_make_model(text)
    if vehicle:
        detail = f"{vehicle} {vehicle_name}".strip()
        return f"{detail} SPZ {registration}" if registration else detail
    if vehicle_name:
        return f"auto {vehicle_name} SPZ {registration}" if registration else f"auto {vehicle_name}"
    if "volvo" in folded and "v40" in folded:
        return "Volvo V40"
    if "volvo" in folded:
        return "Volvo"
    if "fotovolta" in folded or "fve" in folded:
        return "fotovoltaika"
    if "kotel" in folded:
        return "kotel"
    if "t-mobile" in folded or "mobilní služby" in folded or "mobilni sluzby" in folded:
        return "T-Mobile / mobilní služby"
    if "cestovní pojištění" in folded or "cestovni pojisteni" in folded or "travel insurance" in folded:
        return "cestovní pojištění"
    if has_car_marker(folded):
        return f"auto SPZ {registration}" if registration else "auto"
    return ""


def guess_vehicle_kind(folded_text: str) -> str:
    if "motocykl" in folded_text or "motorka" in folded_text:
        return "motocykl"
    return ""


def extract_vehicle_registration(text: str) -> str:
    patterns = (
        r"\b(?:spz|rz)\s*(?:vozidla)?\s*(?:\([^)]*\))?\s*[:#-]?\s*([A-Z0-9][A-Z0-9 -]{4,12})\b",
        r"\b(?:registrační|registracni|evidenční|evidencni)\s+(?:značka|znacka|číslo|cislo)\s*(?:\([^)]*\))?\s*[:#-]?\s*([A-Z0-9][A-Z0-9 -]{4,12})\b",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, text[:20000], flags=re.IGNORECASE):
            candidate = normalize_vehicle_registration(match.group(1))
            if candidate:
                return candidate
    return ""


def extract_vehicle_make_model(text: str) -> str:
    make = ""
    model = ""
    for raw_line in text[:20000].splitlines():
        line = normalize_whitespace(raw_line)
        folded = line.casefold()
        if not make and ("tovární značka" in folded or "tovarni znacka" in folded):
            make = extract_table_value_after_label(
                line,
                ("Tovární značka", "Tovarni znacka"),
                ("VIN", "Registrační značka", "Registracni znacka", "RZ", "SPZ"),
            )
        if not model and ("obchodní označení" in folded or "obchodni oznaceni" in folded):
            model = extract_table_value_after_label(
                line,
                ("Obchodní označení", "Obchodni oznaceni"),
                ("Série", "Serie", "Rozlišovací značka", "Rozlisovaci znacka", "Státu", "Statu"),
            )
        if make and model:
            break
    return normalize_whitespace(" ".join(part for part in (make, model) if part))


def extract_table_value_after_label(line: str, labels: tuple[str, ...], stop_labels: tuple[str, ...]) -> str:
    value = line
    folded = line.casefold()
    for label in labels:
        index = folded.find(label.casefold())
        if index >= 0:
            value = line[index + len(label) :]
            break
    for stop in stop_labels:
        stop_index = value.casefold().find(stop.casefold())
        if stop_index >= 0:
            value = value[:stop_index]
    value = normalize_whitespace(value).strip(" :;-")
    value = re.sub(r"^/\s*(?:typ|type)\s*:\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^(?:typ|type)\s*:\s*", "", value, flags=re.IGNORECASE)
    if value.casefold() in {"není", "neni", "neuvedeno"}:
        return ""
    if not 2 <= len(value) <= 60:
        return ""
    return value


def normalize_vehicle_registration(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]", "", value).upper()
    if not 5 <= len(normalized) <= 10:
        return ""
    if not any(char.isdigit() for char in normalized):
        return ""
    if normalized in {"VOZIDLA", "ZNACKA", "CISLO"}:
        return ""
    return normalized


def guess_lease_related_asset(source: Path, text: str, folded: str) -> str:
    address = extract_street_from_text(text)
    if address:
        return address
    filename_address = extract_street_from_filename(source)
    if filename_address:
        return filename_address
    if "byt" in folded or "bytu" in folded:
        return "byt"
    return ""


def extract_street_from_text(text: str) -> str:
    patterns = (
        r"\b([A-ZÁ-Ž][\wÀ-ž.'-]{3,40})\s+(?:ulice|ul\.)\b",
        r"\b(?:ulice|ul\.)\s+([A-ZÁ-Ž][\wÀ-ž.'-]{3,40})\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text[:12000])
        if match:
            street = normalize_whitespace(match.group(1))
            if street.casefold() not in {"tato", "této", "teto"}:
                return f"{street} ulice"
    return ""


def extract_street_from_filename(source: Path) -> str:
    words = split_camel_case_text(source.stem).split()
    ignored = {"najemni", "nájemní", "smlouva", "lease", "contract", "dokument", "document"}
    useful = [word for word in words if safe_slug(word, default="", limit=40) not in ignored]
    if not useful:
        return ""
    if useful[-1].casefold() in {"ulice", "ul"} and len(useful) >= 2:
        return f"{useful[-2]} ulice"
    return ""


def split_camel_case_text(value: str) -> str:
    return re.sub(r"(?<=[a-zá-ž])(?=[A-ZÁ-Ž])", " ", value)


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
        ("auto", ("vozidlo", "volvo")),
        ("motocykl", ("motocykl", "motorka")),
        ("volvo-v40", ("volvo v40", "v40")),
        ("pojisteni", ("pojist", "zelena karta", "zelená karta")),
        ("faktura", ("faktura", "invoice", "danovy doklad", "daňový doklad")),
        ("servis", ("servis", "udrzba", "údržba", "garanční prohlídka", "garancni prohlidka")),
        ("technicka-kontrola", ("technicka kontrola", "technická kontrola", "emisni kontrola", "emisní kontrola")),
        ("recept", ("recept", "přísady", "prisady", "ingredience", "doba přípravy", "doba pripravy")),
        ("jidlo", ("salát", "salat", "polévka", "polevka", "brambor", "mrkev", "cuketa")),
        ("dieta", ("dieta", "dietní", "dietni", "jídelníček", "jidelnicek", "purin", "diabet")),
        ("cestovani", ("booking.com", "rezervace", "ubytování", "ubytovani", "check-in", "check-out", "hotel", "apartmán", "apartman", "dovolená", "dovolena")),
        ("najem", ("nájemní smlouva", "najemni smlouva", "nájemce", "najemce", "nájemné", "najemne")),
        ("bydleni", ("nájemní smlouva", "najemni smlouva", "bytová jednotka", "bytova jednotka", "pronajímatel", "pronajimatel")),
        ("splatnost", ("splatnost", "uhradit", "zaplatit")),
        ("platnost", ("platnost do", "platna do", "platná do")),
    )
    for tag, markers in checks:
        if any(marker in text for marker in markers):
            tags.append(tag)
    if domain != "travel" and has_car_marker(text):
        tags.append("auto")
    registration = extract_vehicle_registration(text)
    if registration:
        tags.append("spz")
        tags.append(f"spz-{registration}")
    if has_stk_marker(text):
        tags.append("technicka-kontrola")
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
    append_jsonl_locked(path, data, sort_keys=True)


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
    atomic_write_json(path, data, sort_keys=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_domain(value: str) -> str:
    raw = value.casefold().strip()
    alias = DOMAIN_ALIASES.get(raw)
    if alias:
        return alias
    key = safe_ascii_slug(raw, default="", limit=80)
    if not key:
        return "other"
    return DOMAIN_ALIASES.get(key, key)


def parse_tags(tags: str) -> list[str]:
    values = re.split(r"[,;]", tags)
    return [safe_slug(value, default="", limit=40) for value in values if safe_slug(value, default="", limit=40)]


def safe_slug(value: str, default: str, limit: int) -> str:
    normalized = SAFE_ID_PATTERN.sub("-", value.casefold().strip()).strip("-")
    return (normalized or default)[:limit]


def safe_ascii_slug(value: str, default: str, limit: int) -> str:
    folded = unicodedata.normalize("NFKD", value.casefold().strip())
    ascii_value = "".join(char for char in folded if not unicodedata.combining(char))
    return safe_slug(ascii_value, default=default, limit=limit)


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


def project_path_from_record(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


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
