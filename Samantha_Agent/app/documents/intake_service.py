"""Unified read-only document intake status across local sources."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from app.documents.intake_models import (
    DocumentIntakeItem,
    DocumentIntakeSource,
    DocumentIntakeSourceSnapshot,
    DocumentIntakeState,
    unified_intake_items,
)
from app.documents.vault import (
    DEFAULT_DOCUMENTS_DIR,
    DEFAULT_MOBILE_DOCUMENT_INBOX,
    read_json_file,
    safe_text,
)


def document_intake_status(
    downloads: dict[str, Any],
    email_pending: dict[str, Any],
    *,
    mobile_inbox_dir: Path = DEFAULT_MOBILE_DOCUMENT_INBOX,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 5,
) -> dict[str, Any]:
    download_items = [item for item in downloads.get("items", []) if isinstance(item, dict)]
    new_downloads = [item for item in download_items if item.get("status") == "new"]
    email_items = [
        item for item in email_pending.get("items", [])
        if isinstance(item, dict) and str(item.get("action", "")) == "process"
    ]
    snapshots = [
        DocumentIntakeSourceSnapshot(
            source=DocumentIntakeSource.DOWNLOADS,
            state=DocumentIntakeState.READY if new_downloads else DocumentIntakeState.EMPTY,
            total_count=len(new_downloads),
            next_action="Zpracovat další PDF přes ScanDocu." if new_downloads else "Žádné nové PDF ke zpracování.",
            items=tuple(
                DocumentIntakeItem.build(
                    source=DocumentIntakeSource.DOWNLOADS,
                    title=str(item.get("name", "")),
                    meta=str(item.get("modified_at", "")),
                    source_key=str(item.get("name", "")),
                )
                for item in new_downloads[:limit]
            ),
        ),
        DocumentIntakeSourceSnapshot(
            source=DocumentIntakeSource.EMAIL,
            state=DocumentIntakeState.READY if email_items else DocumentIntakeState.EMPTY,
            total_count=len(email_items),
            next_action=(
                "Zpracovat označené e-maily a PDF přílohy."
                if email_items
                else "Žádný e-mail není označený ke zpracování."
            ),
            items=tuple(
                DocumentIntakeItem.build(
                    source=DocumentIntakeSource.EMAIL,
                    title=str(item.get("subject", "") or "E-mail bez předmětu"),
                    meta=f"{item.get('provider', '')} / {item.get('folder', '')} / {item.get('date', '')}",
                    source_key=str(
                        item.get("source_key")
                        or item.get("id")
                        or f"{item.get('provider', '')}|{item.get('folder', '')}|{item.get('uid', '')}"
                    ),
                )
                for item in email_items[:limit]
            ),
        ),
        _mobile_document_intake_snapshot(mobile_inbox_dir=mobile_inbox_dir, limit=limit),
        _local_document_inbox_snapshot(vault_dir=vault_dir, limit=limit),
    ]
    sources = [snapshot.to_public_dict() for snapshot in snapshots]
    total = sum(int(source.get("count", 0) or 0) for source in sources)
    unified_items = unified_intake_items(snapshots, limit=max(4, limit * 2))
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


def document_intake_unified_items(*, sources: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    snapshots: list[DocumentIntakeSourceSnapshot] = []
    for source in sources:
        try:
            source_id = DocumentIntakeSource(str(source.get("id", "")))
        except ValueError:
            continue
        try:
            state = DocumentIntakeState(str(source.get("status", "")))
        except ValueError:
            state = DocumentIntakeState.EMPTY
        raw_items = source.get("items", []) if isinstance(source.get("items"), list) else []
        model_items = tuple(
            DocumentIntakeItem.build(
                source=source_id,
                title=str(item.get("title", "") or "Dokumentový vstup"),
                meta=str(item.get("meta", "")),
                source_key=str(item.get("intake_ref", "") or f"{item.get('title', '')}|{item.get('meta', '')}"),
            )
            for item in raw_items
            if isinstance(item, dict)
        )
        snapshots.append(DocumentIntakeSourceSnapshot(
            source=source_id,
            state=state,
            total_count=int(source.get("count", len(model_items)) or 0),
            next_action=str(source.get("next_action", "")),
            items=model_items,
        ))
    return unified_intake_items(snapshots, limit=limit)


def mobile_document_intake_source(
    *,
    mobile_inbox_dir: Path = DEFAULT_MOBILE_DOCUMENT_INBOX,
    limit: int = 5,
) -> dict[str, Any]:
    return _mobile_document_intake_snapshot(
        mobile_inbox_dir=mobile_inbox_dir,
        limit=limit,
    ).to_public_dict()


def _mobile_document_intake_snapshot(
    *,
    mobile_inbox_dir: Path,
    limit: int,
) -> DocumentIntakeSourceSnapshot:
    inbox = mobile_inbox_dir.expanduser()
    process_request = inbox / "process_request.json"
    if not inbox.exists():
        return DocumentIntakeSourceSnapshot(
            source=DocumentIntakeSource.MOBILE,
            state=DocumentIntakeState.MISSING,
            total_count=0,
            next_action="Mobilní inbox zatím není synchronizovaný na Mac.",
        )
    if not inbox.is_dir():
        return DocumentIntakeSourceSnapshot(
            source=DocumentIntakeSource.MOBILE,
            state=DocumentIntakeState.PROBLEM,
            total_count=0,
            next_action="Mobilní inbox není složka.",
        )
    manifests = sorted(
        inbox.glob("scan_*_manifest.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    items: list[DocumentIntakeItem] = []
    for manifest_path in manifests[:limit]:
        try:
            manifest = read_json_file(manifest_path)
        except ValueError as exc:
            items.append(DocumentIntakeItem.build(
                source=DocumentIntakeSource.MOBILE,
                title=manifest_path.name,
                meta=f"chyba manifestu: {safe_text(str(exc))[:120]}",
                source_key=manifest_path.name,
            ))
            continue
        batch_id = safe_text(str(manifest.get("batch_id", ""))).strip()
        title = safe_text(str(manifest.get("document_title", ""))).strip() or batch_id or manifest_path.stem
        expected_count = safe_text(str(manifest.get("page_count", ""))).strip() or "?"
        pages = sorted(inbox.glob(f"{batch_id}_page_*")) if batch_id else []
        modified = datetime.fromtimestamp(manifest_path.stat().st_mtime).isoformat(timespec="minutes")
        items.append(DocumentIntakeItem.build(
            source=DocumentIntakeSource.MOBILE,
            title=title,
            meta=f"{len(pages)} / {expected_count} stran | {modified}",
            source_key=batch_id or manifest_path.name,
        ))
    count = len(manifests)
    request_note = " Process request čeká." if process_request.exists() else ""
    return DocumentIntakeSourceSnapshot(
        source=DocumentIntakeSource.MOBILE,
        state=DocumentIntakeState.READY if count else DocumentIntakeState.EMPTY,
        total_count=count,
        next_action=(
            f"Připravit nebo zpracovat mobilní batch.{request_note}"
            if count
            else f"Žádný mobilní scan nečeká.{request_note}"
        ),
        items=tuple(items),
    )


def local_document_inbox_source(
    *,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 5,
) -> dict[str, Any]:
    return _local_document_inbox_snapshot(vault_dir=vault_dir, limit=limit).to_public_dict()


def _local_document_inbox_snapshot(
    *,
    vault_dir: Path,
    limit: int,
) -> DocumentIntakeSourceSnapshot:
    incoming = vault_dir / "inbox" / "incoming"
    if not incoming.exists():
        return DocumentIntakeSourceSnapshot(
            source=DocumentIntakeSource.LOCAL_INBOX,
            state=DocumentIntakeState.MISSING,
            total_count=0,
            next_action="Lokální document inbox zatím neexistuje.",
        )
    if not incoming.is_dir():
        return DocumentIntakeSourceSnapshot(
            source=DocumentIntakeSource.LOCAL_INBOX,
            state=DocumentIntakeState.PROBLEM,
            total_count=0,
            next_action="Lokální document inbox není složka.",
        )
    files = sorted(
        (item for item in incoming.iterdir() if item.is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return DocumentIntakeSourceSnapshot(
        source=DocumentIntakeSource.LOCAL_INBOX,
        state=DocumentIntakeState.READY if files else DocumentIntakeState.EMPTY,
        total_count=len(files),
        next_action=(
            "Připravit import souboru z inboxu."
            if files
            else "Lokální inbox je prázdný."
        ),
        items=tuple(
            DocumentIntakeItem.build(
                source=DocumentIntakeSource.LOCAL_INBOX,
                title=path.name,
                meta=(
                    f"{path.stat().st_size} B | "
                    f"{datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec='minutes')}"
                ),
                source_key=path.name,
            )
            for path in files[:limit]
        ),
    )
