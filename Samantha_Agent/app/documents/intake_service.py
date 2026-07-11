"""Unified read-only document intake status across local sources."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

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



