"""Confirmed, recoverable removal of exactly one scan or indexed document.

The trash is a lifecycle state, not a physical deletion. Original bytes stay in
the private vault; active readers refuse them until an explicit restoration.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs

from app.file_persistence import atomic_replace_text_under_external_lock, exclusive_file_lock
from .transactions import DocumentRecordMutation, DocumentTransactionError, transact_document_record
from .search_service import document_reference
from .vault import DEFAULT_DOCUMENTS_DIR, PROJECT_ROOT, read_jsonl, resolve_indexed_document_path, safe_text

READ_PATHS = ("/api/documents/trash", "/api/documents/trash/preview", "/api/documents/trash/candidate")


def hidden(record):
    return str(record.get("lifecycle_status", "")).casefold() in {"trashed", "deleted"} or "/trash/" in str(record.get("stored_path", "")).replace("\\", "/")


def _safe_path(path, root):
    path, root = Path(path), Path(root)
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Úložiště obsahuje nepovolený odkaz.")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Dokument neleží v povoleném úložišti.")
    return path


def _record(kind, reference, vault_dir):
    if kind == "scan":
        from .scan_inbox import scan_directory
        path = _safe_path(scan_directory(reference, vault_dir) / "scan.json", vault_dir)
        record = json.loads(path.read_text())
        if record.get("scan_id") != reference:
            raise ValueError("Sken neodpovídá odkazu.")
        return record, path
    if kind == "document" and str(reference).startswith("docref-"):
        for row in read_jsonl(_safe_path(Path(vault_dir) / "index/documents_index.jsonl", vault_dir)):
            if document_reference(str(row.get("document_id", ""))) == reference:
                return row, None
    raise ValueError("Dokument nebyl nalezen.")


def _document_file(record, vault_dir):
    stored = str(record.get("stored_path", ""))
    file = resolve_indexed_document_path(stored, vault_dir)
    if file is None:
        raise ValueError("Soubor dokumentu není dostupný.")
    raw = Path(stored)
    candidates = [raw] if raw.is_absolute() else [PROJECT_ROOT / raw]
    if not raw.is_absolute():
        try:
            candidates.insert(0, Path(vault_dir) / raw.relative_to(DEFAULT_DOCUMENTS_DIR.relative_to(PROJECT_ROOT)))
        except ValueError:
            pass
    for candidate in candidates:
        if candidate.resolve() == file:
            _safe_path(candidate, vault_dir)
            return file
    raise ValueError("Cestu k dokumentu nelze bezpečně ověřit.")


def _revision(record, kind, vault_dir):
    if kind == "scan":
        from .scan_inbox import scan_directory
        file = _safe_path(scan_directory(record["scan_id"], vault_dir) / "document.pdf", vault_dir)
    else:
        file = _document_file(record, vault_dir)
    content_hash = hashlib.sha256(file.read_bytes()).hexdigest()
    if record.get("sha256") and record["sha256"] != content_hash:
        raise ValueError("Soubor dokumentu se změnil a neodpovídá záznamu.")
    return hashlib.sha256((json.dumps(record, sort_keys=True, ensure_ascii=False) + content_hash).encode()).hexdigest()


def _public_item(record, kind, reference):
    return {"ok": True, "kind": kind, "reference": reference,
            "title": safe_text(str(record.get("title") or record.get("original_filename") or "Dokument")),
            "trashed": hidden(record),
            "can_restore": bool(record.get("trash_previous_status") is not None)}


def preview(kind, reference, *, vault_dir=DEFAULT_DOCUMENTS_DIR):
    record, _ = _record(kind, reference, vault_dir)
    return {**_public_item(record, kind, reference), "revision": _revision(record, kind, vault_dir)}


def trash_status(*, vault_dir=DEFAULT_DOCUMENTS_DIR):
    items = []
    for row in read_jsonl(_safe_path(Path(vault_dir) / "index/documents_index.jsonl", vault_dir)):
        if hidden(row):
            items.append(_public_item(row, "document", document_reference(str(row.get("document_id", "")))))
    root = _safe_path(Path(vault_dir) / "scans", vault_dir)
    for path in root.glob("*/scan.json"):
        record, _ = _record("scan", path.parent.name, vault_dir)
        item = _public_item(record, "scan", path.parent.name)
        if item["trashed"]:
            items.append(item)
    return {"ok": True, "items": items}


def apply_action(payload, *, vault_dir=DEFAULT_DOCUMENTS_DIR):
    """A persisted request ID prevents an old removal from replaying after restore."""
    try:
        kind, reference = payload.get("kind"), payload.get("reference")
        action, request_id = payload.get("action"), payload.get("request_id", "")
        if payload.get("confirmed") is not True or action not in {"trash", "restore"}:
            raise ValueError("Potvrď přesun konkrétního dokumentu do koše nebo jeho obnovu.")
        if not isinstance(request_id, str) or not re.fullmatch(r"[a-f0-9]{32}", request_id):
            raise ValueError("Chybí platná identita požadavku.")
        fingerprint = {k: payload.get(k) for k in ("kind", "reference", "action", "expected_revision")}
        record, scan_manifest = _record(kind, reference, vault_dir)

        def change(current):
            operations = dict(current.get("lifecycle_requests", {}))
            if request_id in operations:
                if operations[request_id]["input"] != fingerprint:
                    raise ValueError("Tento požadavek už patří jiné změně.")
                return None
            if _revision(current, kind, vault_dir) != payload.get("expected_revision"):
                raise ValueError("Dokument se změnil. Obnov seznam a znovu potvrď aktuální položku.")
            if (action == "trash") == hidden(current):
                raise ValueError("Dokument už je v požadovaném stavu. Obnov seznam.")
            if kind == "scan":
                file = _safe_path(scan_manifest.parent / "document.pdf", vault_dir)
                if hashlib.sha256(file.read_bytes()).hexdigest() != current.get("sha256"):
                    raise ValueError("Uložený sken byl změněn.")
            else:
                _document_file(current, vault_dir)
            updated = dict(current)
            if action == "trash":
                updated["trash_previous_status"] = current.get("lifecycle_status", "active")
                updated["lifecycle_status"] = "trashed"
            else:
                if "trash_previous_status" not in current:
                    raise ValueError("Tento starší koš vyžaduje ruční obnovu; automatický návrat není ověřený.")
                updated["lifecycle_status"] = current["trash_previous_status"]
                updated.pop("trash_previous_status", None)
            updated["lifecycle_changed_at"] = datetime.now(timezone.utc).isoformat()
            operations[request_id] = {"input": fingerprint, "action": action}
            updated["lifecycle_requests"] = operations
            return updated

        if kind == "scan":
            with exclusive_file_lock(scan_manifest):
                current = json.loads(scan_manifest.read_text())
                updated = change(current)
                if updated is not None:
                    atomic_replace_text_under_external_lock(scan_manifest, json.dumps(updated, ensure_ascii=False, sort_keys=True))
        else:
            def manifest_path(current):
                file = _document_file(current, vault_dir)
                path = _safe_path(file.parent / "manifest.json", vault_dir)
                return path if path.is_file() else None

            def mutation(current, manifest):
                if manifest is not None and manifest.get("document_id", current["document_id"]) != current["document_id"]:
                    raise ValueError("Manifest patří jinému dokumentu.")
                updated = change(current)
                if updated is None:
                    return None
                return DocumentRecordMutation(updated, {**manifest, **updated} if manifest is not None else None,
                    {"action": action, "document_ref": reference, "request_id": request_id})

            transact_document_record(vault_dir=vault_dir, reference=reference,
                row_selector=lambda rows, ref: next((i for i, row in enumerate(rows) if document_reference(str(row.get("document_id", ""))) == ref), None),
                manifest_path_resolver=manifest_path, mutation_builder=mutation,
                audit_path=Path(vault_dir) / "index/document_lifecycle_actions.jsonl", backup_group="lifecycle_backups")
        return {"ok": True, "request_id": request_id,
                "message": "Dokument byl přesunut do koše. Lze jej obnovit." if action == "trash" else "Dokument byl obnoven."}
    except (ValueError, OSError, TypeError, DocumentTransactionError) as exc:
        return {"ok": False, "message": str(exc)}


def dispatch_get(parsed, responder, *, vault_dir=DEFAULT_DOCUMENTS_DIR):
    if parsed.path not in READ_PATHS:
        return False
    try:
        params = parse_qs(parsed.query)
        if parsed.path.endswith("/candidate"):
            from .scandocu import get_scandocu_candidate
            candidate = get_scandocu_candidate(params.get("token", [""])[0], vault_dir=vault_dir)
            info = candidate.to_api()
            responder.respond_json({"ok": True, "kind": info["lifecycle_kind"], "reference": info["lifecycle_reference"]})
            return True
        data = trash_status(vault_dir=vault_dir) if parsed.path.endswith("/trash") else preview(
            params.get("kind", [""])[0], params.get("reference", [""])[0], vault_dir=vault_dir)
        responder.respond_json(data)
    except (ValueError, OSError) as exc:
        responder.respond_json({"ok": False, "message": str(exc)}, status=400)
    return True
