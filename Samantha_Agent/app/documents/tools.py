from __future__ import annotations

from pathlib import Path

from agents import function_tool

from .scandocu import (
    DEFAULT_DOWNLOADS_DIR,
    prepare_next_scandocu_pdf,
    scan_downloads_for_pdfs,
)
from .vault import (
    DEFAULT_DOCUMENTS_DIR,
    apply_document_import_file,
    apply_mobile_document_final_import_summary,
    document_vault_status_summary,
    format_document_inbox_reminder,
    has_explicit_document_import_confirmation,
    inspect_document_text_summary,
    prepare_document_import_summary,
    prepare_mobile_document_final_import_summary,
    prepare_mobile_document_batch_summary,
    process_mobile_document_inbox_summary,
    prepare_document_print_job_summary,
    preview_document_reindex_summary,
    propose_document_inbox_cleanup_summary,
    relative_to_project,
    resolve_document_inbox_item_summary,
    run_document_print_job_summary,
    apply_document_reindex_summary,
    save_document_due_reminder_summary,
    scan_document_inbox_summary,
    scan_mobile_document_inbox_summary,
    search_private_documents_summary,
)


@function_tool
def scan_document_inbox(max_items: int = 20) -> str:
    """Read-only scan of private document inbox for newly dropped files."""
    return scan_document_inbox_text(max_items=max_items)


@function_tool
def scan_mobile_document_inbox(max_batches: int = 20) -> str:
    """Read-only scan of iPhone Shortcuts document capture inbox."""
    return scan_mobile_document_inbox_text(max_batches=max_batches)


@function_tool
def prepare_mobile_document_batch(batch_id: str = "") -> str:
    """Prepare a captured iPhone document batch as a local working PDF; does not import or delete."""
    return prepare_mobile_document_batch_text(batch_id=batch_id)


@function_tool
def process_mobile_document_inbox(batch_id: str = "", force_reprocess: bool = False) -> str:
    """Process requested iPhone document batches into private working PDFs and OCR metadata; does not import."""
    return process_mobile_document_inbox_text(batch_id=batch_id, force_reprocess=force_reprocess)


@function_tool
def scan_downloaded_pdfs(max_items: int = 20) -> str:
    """Read-only scan of PDF files in Downloads for ScanDocu processing."""
    return scan_downloaded_pdfs_text(max_items=max_items)


@function_tool
def prepare_next_scandocu_document() -> str:
    """Prepare the newest unprocessed Downloads PDF for ScanDocu review; does not import."""
    return prepare_next_scandocu_document_text()


@function_tool
def preview_document_reindex(max_documents: int = 50, mode: str = "improve_weak") -> str:
    """Read-only preview of metadata improvements for already imported private documents."""
    return preview_document_reindex_text(max_documents=max_documents, mode=mode)


@function_tool
def apply_document_reindex(
    max_documents: int = 50,
    mode: str = "improve_weak",
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    """Apply confirmed metadata reindex to already imported private documents."""
    return apply_document_reindex_text(
        max_documents=max_documents,
        mode=mode,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )


@function_tool
def prepare_mobile_document_final_import(
    batch_id: str = "",
    target_domain: str = "",
    document_type: str = "",
    counterparty: str = "",
    related_asset: str = "",
    tags: str = "",
    case_id: str = "",
) -> str:
    """Preview final import of one processed mobile document; read-only."""
    return prepare_mobile_document_final_import_text(
        batch_id=batch_id,
        target_domain=target_domain,
        document_type=document_type,
        counterparty=counterparty,
        related_asset=related_asset,
        tags=tags,
        case_id=case_id,
    )


@function_tool
def apply_mobile_document_final_import(
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
) -> str:
    """Import one processed mobile document into the private vault after explicit confirmation."""
    return apply_mobile_document_final_import_text(
        batch_id=batch_id,
        target_domain=target_domain,
        document_type=document_type,
        counterparty=counterparty,
        related_asset=related_asset,
        tags=tags,
        document_id=document_id,
        case_id=case_id,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )


@function_tool
def prepare_document_import(source_path: str, document_hint: str = "") -> str:
    """Read-only preview of a local private document import."""
    return prepare_document_import_text(source_path=source_path, document_hint=document_hint)


@function_tool
def inspect_document_text(source_path: str = "", document_id: str = "") -> str:
    """Read-only text and due-date inspection for a local or already imported document."""
    return inspect_document_text_text(source_path=source_path, document_id=document_id)


@function_tool
def apply_document_import(
    source_path: str,
    target_domain: str,
    document_type: str = "",
    counterparty: str = "",
    related_asset: str = "",
    tags: str = "",
    document_id: str = "",
    case_id: str = "",
    document_title: str = "",
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    """Copy a confirmed local document into the private document vault and index it."""
    return apply_document_import_text(
        source_path=source_path,
        target_domain=target_domain,
        document_type=document_type,
        counterparty=counterparty,
        related_asset=related_asset,
        tags=tags,
        document_id=document_id,
        case_id=case_id,
        document_title=document_title,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )


@function_tool
def search_private_documents(query: str, max_results: int = 5) -> str:
    """Search the local private document index and return safe snippets."""
    return search_private_documents_text(query=query, max_results=max_results)


@function_tool
def save_document_due_reminder(
    document_id: str,
    title: str,
    due_date: str,
    due_date_type: str = "deadline",
    notes: str = "",
    priority: str = "high",
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    """Save a reminder from a confirmed private document due-date candidate."""
    return save_document_due_reminder_text(
        document_id=document_id,
        title=title,
        due_date=due_date,
        due_date_type=due_date_type,
        notes=notes,
        priority=priority,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )


@function_tool
def propose_document_inbox_cleanup(source_path: str) -> str:
    """Read-only prompt for moving or deleting a processed document from inbox."""
    return propose_document_inbox_cleanup_text(source_path=source_path)


@function_tool
def resolve_document_inbox_item(
    source_path: str,
    action: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    """Move or delete a confirmed document from private document inbox."""
    return resolve_document_inbox_item_text(
        source_path=source_path,
        action=action,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )


@function_tool
def document_vault_status() -> str:
    """Read-only aggregate status of private document vault."""
    return document_vault_status_text()


@function_tool
def prepare_document_print_job(query: str = "", document_id: str = "") -> str:
    """Prepare a private document for printing by copying it into print_queue; does not print."""
    return prepare_document_print_job_text(query=query, document_id=document_id)


@function_tool
def run_document_print_job(
    print_job_id: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    printer: str = "",
) -> str:
    """Print a prepared private document job after explicit confirmation."""
    return run_document_print_job_text(
        print_job_id=print_job_id,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
        printer=printer,
    )


def prepare_document_import_text(
    source_path: str,
    document_hint: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    return prepare_document_import_summary(
        source_path=source_path,
        document_hint=document_hint,
        vault_dir=vault_dir,
    )


def scan_document_inbox_text(
    max_items: int = 20,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    return scan_document_inbox_summary(
        vault_dir=vault_dir,
        max_items=max(1, min(max_items, 50)),
    )


def scan_mobile_document_inbox_text(
    max_batches: int = 20,
    mobile_inbox_dir: Path | None = None,
) -> str:
    kwargs = {"max_batches": max(1, min(max_batches, 50))}
    if mobile_inbox_dir is not None:
        kwargs["mobile_inbox_dir"] = mobile_inbox_dir
    return scan_mobile_document_inbox_summary(**kwargs)


def prepare_mobile_document_batch_text(
    batch_id: str = "",
    mobile_inbox_dir: Path | None = None,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    kwargs = {"batch_id": batch_id, "vault_dir": vault_dir}
    if mobile_inbox_dir is not None:
        kwargs["mobile_inbox_dir"] = mobile_inbox_dir
    return prepare_mobile_document_batch_summary(**kwargs)


def process_mobile_document_inbox_text(
    batch_id: str = "",
    mobile_inbox_dir: Path | None = None,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    max_batches: int = 20,
    force_reprocess: bool = False,
) -> str:
    kwargs = {
        "batch_id": batch_id,
        "vault_dir": vault_dir,
        "max_batches": max(1, min(max_batches, 50)),
        "force_reprocess": force_reprocess,
    }
    if mobile_inbox_dir is not None:
        kwargs["mobile_inbox_dir"] = mobile_inbox_dir
    return process_mobile_document_inbox_summary(**kwargs)


def scan_downloaded_pdfs_text(
    max_items: int = 20,
    downloads_dir: Path = DEFAULT_DOWNLOADS_DIR,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    try:
        items = scan_downloads_for_pdfs(
            downloads_dir=downloads_dir,
            vault_dir=vault_dir,
            limit=max(1, min(max_items, 50)),
        )
    except ValueError as exc:
        return f"ScanDocu scan Downloads byl odmitnut: {exc}"
    if not items:
        return f"ScanDocu: v `{downloads_dir}` neni zadne PDF."
    lines = [
        "ScanDocu PDF v Downloads (read-only):",
        f"- Slozka: `{downloads_dir}`",
    ]
    for item in items:
        lines.append(
            f"- {item['name']} | {item.get('modified_at', '')} | "
            f"{item.get('size_bytes', 0)} B | stav: {item.get('status', 'unknown')}"
        )
    return "\n".join(lines)


def prepare_next_scandocu_document_text(
    downloads_dir: Path = DEFAULT_DOWNLOADS_DIR,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    try:
        candidate = prepare_next_scandocu_pdf(
            downloads_dir=downloads_dir,
            vault_dir=vault_dir,
        )
    except ValueError as exc:
        return f"ScanDocu priprava byla odmitnuta: {exc}"
    if candidate is None:
        return "ScanDocu: v Downloads neni zadne nove PDF ke zpracovani."
    return (
        "ScanDocu dokument je pripraveny ke kontrole.\n"
        f"- Soubor: {candidate.source_path.name}\n"
        f"- Pracovni kopie: `{relative_to_project(candidate.working_path)}`\n"
        f"- Token: {candidate.token}\n"
        f"- Navrzeny nazev: {candidate.title}\n"
        f"- Navrh: {candidate.domain} / {candidate.document_type}\n"
        f"- OCR: {candidate.extraction_method} | OCR potreba: {'ano' if candidate.ocr_needed else 'ne'}\n"
        "Dalsi krok: otevrit ScanDocu web a potvrdit/upravit metadata."
    )


def preview_document_reindex_text(
    max_documents: int = 50,
    mode: str = "improve_weak",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    return preview_document_reindex_summary(
        vault_dir=vault_dir,
        max_documents=max_documents,
        mode=mode,
    )


def apply_document_reindex_text(
    max_documents: int = 50,
    mode: str = "improve_weak",
    user_confirmed: bool = False,
    confirmation_text: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    return apply_document_reindex_summary(
        vault_dir=vault_dir,
        max_documents=max_documents,
        mode=mode,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )


def prepare_mobile_document_final_import_text(
    batch_id: str = "",
    target_domain: str = "",
    document_type: str = "",
    counterparty: str = "",
    related_asset: str = "",
    tags: str = "",
    case_id: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    return prepare_mobile_document_final_import_summary(
        batch_id=batch_id,
        target_domain=target_domain,
        document_type=document_type,
        counterparty=counterparty,
        related_asset=related_asset,
        tags=tags,
        case_id=case_id,
        vault_dir=vault_dir,
    )


def apply_mobile_document_final_import_text(
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
    return apply_mobile_document_final_import_summary(
        batch_id=batch_id,
        target_domain=target_domain,
        document_type=document_type,
        counterparty=counterparty,
        related_asset=related_asset,
        tags=tags,
        document_id=document_id,
        case_id=case_id,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
        vault_dir=vault_dir,
    )


def propose_document_inbox_cleanup_text(
    source_path: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    return propose_document_inbox_cleanup_summary(
        source_path=source_path,
        vault_dir=vault_dir,
    )


def resolve_document_inbox_item_text(
    source_path: str,
    action: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    return resolve_document_inbox_item_summary(
        source_path=source_path,
        action=action,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
        vault_dir=vault_dir,
    )


def document_vault_status_text(
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    return document_vault_status_summary(vault_dir=vault_dir)


def prepare_document_print_job_text(
    query: str = "",
    document_id: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    return prepare_document_print_job_summary(
        query=query,
        document_id=document_id,
        vault_dir=vault_dir,
    )


def run_document_print_job_text(
    print_job_id: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    printer: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    print_runner: object | None = None,
) -> str:
    return run_document_print_job_summary(
        print_job_id=print_job_id,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
        vault_dir=vault_dir,
        printer=printer,
        print_runner=print_runner,
    )


def inspect_document_text_text(
    source_path: str = "",
    document_id: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    return inspect_document_text_summary(
        source_path=source_path,
        document_id=document_id,
        vault_dir=vault_dir,
    )


def apply_document_import_text(
    source_path: str,
    target_domain: str,
    document_type: str = "",
    counterparty: str = "",
    related_asset: str = "",
    tags: str = "",
    document_id: str = "",
    case_id: str = "",
    document_title: str = "",
    user_confirmed: bool = False,
    confirmation_text: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    source_name = Path(source_path).name
    if not user_confirmed or not has_explicit_document_import_confirmation(
        filename=source_name,
        target_domain=target_domain,
        confirmation_text=confirmation_text,
    ):
        return (
            "Nejdrive potrebuji samostatne potvrzeni od Mily v aktualni zprave. "
            f"Potvrzeni musi obsahovat nazev souboru {source_name}, cilovou oblast "
            f"{target_domain} a jasny souhlas s ulozenim dokumentu. "
            "Bez toho do private document vaultu nic nekopiruji."
        )

    try:
        result = apply_document_import_file(
            source_path=source_path,
            target_domain=target_domain,
            document_type=document_type,
            counterparty=counterparty,
            related_asset=related_asset,
            tags=tags,
            document_id=document_id,
            case_id=case_id,
            document_title=document_title,
            vault_dir=vault_dir,
        )
    except ValueError as exc:
        return f"Import dokumentu byl odmitnut: {exc}"

    status = "ulozeno" if result.created else "uz existuje"
    return (
        f"Stav: {status}. Document ID: {result.document_id}. "
        f"Dokument: {result.destination}. Manifest: {result.manifest}. "
        f"{result.message}"
    )


def search_private_documents_text(
    query: str,
    max_results: int = 5,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    return search_private_documents_summary(
        query=query,
        max_results=max(1, min(max_results, 10)),
        vault_dir=vault_dir,
    )


def save_document_due_reminder_text(
    document_id: str,
    title: str,
    due_date: str,
    due_date_type: str = "deadline",
    notes: str = "",
    priority: str = "high",
    user_confirmed: bool = False,
    confirmation_text: str = "",
    reminders_path: Path | None = None,
) -> str:
    kwargs = {
        "document_id": document_id,
        "title": title,
        "due_date": due_date,
        "due_date_type": due_date_type,
        "notes": notes,
        "priority": priority,
        "user_confirmed": user_confirmed,
        "confirmation_text": confirmation_text,
    }
    if reminders_path is not None:
        kwargs["reminders_path"] = reminders_path
    try:
        return save_document_due_reminder_summary(**kwargs)
    except ValueError as exc:
        return f"Ulozeni dokumentove pripominky bylo odmitnuto: {exc}"
