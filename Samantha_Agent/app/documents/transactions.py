from __future__ import annotations

import json
import re
import shutil
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.file_persistence import (
    append_jsonl_locked,
    atomic_replace_text_under_external_lock,
    atomic_write_json,
    atomic_write_text,
    exclusive_file_lock,
)


DOCUMENT_TRANSACTION_MARKER = "document_record_transaction.json"


class DocumentTransactionError(RuntimeError):
    pass


class DocumentRecordNotFoundError(DocumentTransactionError):
    pass


class DocumentTransactionRecoveryError(DocumentTransactionError):
    pass


@dataclass(frozen=True)
class DocumentRelatedJsonMutation:
    path: Path
    record: dict[str, Any]


@dataclass(frozen=True)
class DocumentRecordMutation:
    index_record: dict[str, Any]
    manifest_record: dict[str, Any] | None
    audit_record: dict[str, Any]
    related_json_files: tuple[DocumentRelatedJsonMutation, ...] = ()


@dataclass(frozen=True)
class DocumentRecordTransactionResult:
    changed: bool
    previous_record: dict[str, Any]
    updated_record: dict[str, Any]
    transaction_id: str = ""
    backup_dir: Path | None = None
    recovered_status: str = ""


RowSelector = Callable[[list[dict[str, Any]], str], int | None]
ManifestPathResolver = Callable[[dict[str, Any]], Path | None]
MutationBuilder = Callable[[dict[str, Any], dict[str, Any] | None], DocumentRecordMutation | None]
BackupPathLabeler = Callable[[Path], str]


def transact_document_record(
    *,
    vault_dir: Path,
    reference: str,
    row_selector: RowSelector,
    manifest_path_resolver: ManifestPathResolver,
    mutation_builder: MutationBuilder,
    audit_path: Path,
    backup_group: str,
    backup_path_labeler: BackupPathLabeler = lambda path: str(path),
    allow_manifest_create: bool = False,
) -> DocumentRecordTransactionResult:
    vault_root = Path(vault_dir).resolve()
    index_path = vault_root / "index" / "documents_index.jsonl"
    marker_path = index_path.with_name(DOCUMENT_TRANSACTION_MARKER)
    safe_audit_path = _require_within(vault_root, audit_path)
    safe_backup_group = _safe_component(backup_group)
    if not safe_backup_group:
        raise DocumentTransactionError("Document transaction backup group is empty.")

    with exclusive_file_lock(index_path):
        recovered_status = _recover_document_transaction_locked(
            vault_root=vault_root,
            index_path=index_path,
            marker_path=marker_path,
        )
        rows = _read_jsonl_strict(index_path)
        row_index = row_selector(rows, reference)
        if row_index is None:
            raise DocumentRecordNotFoundError("Dokument nebyl nalezen v indexu.")

        previous_record = dict(rows[row_index])
        manifest_path = manifest_path_resolver(previous_record)
        safe_manifest_path = _require_within(vault_root, manifest_path) if manifest_path is not None else None
        manifest_record = _read_json_object(safe_manifest_path) if safe_manifest_path and safe_manifest_path.exists() else None
        mutation = mutation_builder(
            dict(previous_record),
            dict(manifest_record) if manifest_record is not None else None,
        )
        if mutation is None:
            return DocumentRecordTransactionResult(
                changed=False,
                previous_record=previous_record,
                updated_record=previous_record,
                recovered_status=recovered_status,
            )
        if mutation.manifest_record is not None and safe_manifest_path is None:
            raise DocumentTransactionError("Manifest mutation has no safe manifest path.")
        _validate_mutation(
            previous_record,
            mutation,
            manifest_record,
            allow_manifest_create=allow_manifest_create,
        )
        related_json_files = _prepare_related_json_files(
            vault_root=vault_root,
            mutation=mutation,
            protected_paths={
                index_path,
                marker_path,
                safe_audit_path,
                *([safe_manifest_path] if safe_manifest_path is not None else []),
            },
        )

        transaction_id = uuid.uuid4().hex
        document_id = str(previous_record.get("document_id", "") or "document")
        backup_dir = _create_backup(
            vault_root=vault_root,
            index_path=index_path,
            manifest_path=safe_manifest_path,
            backup_group=safe_backup_group,
            document_id=document_id,
            transaction_id=transaction_id,
            related_json_paths=[path for path, _record in related_json_files],
        )
        audit_record = dict(mutation.audit_record)
        audit_record["transaction_id"] = transaction_id
        audit_record["backup_dir"] = backup_path_labeler(backup_dir)
        marker = {
            "transaction_id": transaction_id,
            "phase": "prepared",
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "manifest_path": _relative_path(vault_root, safe_manifest_path) if safe_manifest_path else "",
            "manifest_existed": bool(manifest_record is not None),
            "manifest_will_create": bool(manifest_record is None and mutation.manifest_record is not None),
            "backup_index_path": _relative_path(vault_root, backup_dir / "documents_index.jsonl"),
            "backup_manifest_path": (
                _relative_path(vault_root, backup_dir / "manifest.json") if manifest_record is not None else ""
            ),
            "audit_path": _relative_path(vault_root, safe_audit_path),
            "audit_record": audit_record,
            "related_json_files": [
                {
                    "path": _relative_path(vault_root, path),
                    "backup_path": _relative_path(vault_root, backup_dir / f"related_{index:03d}.json"),
                }
                for index, (path, _record) in enumerate(related_json_files)
            ],
        }
        _write_marker(marker_path, marker)

        rows[row_index] = dict(mutation.index_record)
        result = DocumentRecordTransactionResult(
            changed=True,
            previous_record=previous_record,
            updated_record=dict(mutation.index_record),
            transaction_id=transaction_id,
            backup_dir=backup_dir,
            recovered_status=recovered_status,
        )
        try:
            _write_index_under_lock(index_path, rows)
            marker = _set_marker_phase(marker_path, marker, "index_written")
            if mutation.manifest_record is not None:
                if safe_manifest_path is None:
                    raise DocumentTransactionError("Manifest mutation has no safe manifest path.")
                _write_manifest(safe_manifest_path, mutation.manifest_record)
            for related_path, related_record in related_json_files:
                _write_related_json_file(related_path, related_record)
            marker = _set_marker_phase(marker_path, marker, "files_written")
            _append_audit(safe_audit_path, audit_record)
            _set_marker_phase(marker_path, marker, "committed")
        except Exception as exc:
            if _audit_contains_transaction(safe_audit_path, transaction_id):
                _remove_marker_best_effort(marker_path)
                return result
            try:
                _rollback_from_marker(
                    vault_root=vault_root,
                    index_path=index_path,
                    marker=marker,
                )
            except Exception as rollback_exc:
                raise DocumentTransactionRecoveryError(
                    "Dokumentovou transakci se nepodařilo dokončit ani bezpečně vrátit. Recovery marker zůstal zachovaný."
                ) from rollback_exc
            _remove_marker_best_effort(marker_path)
            raise exc

        _remove_marker_best_effort(marker_path)
        return result


def recover_document_record_transaction(vault_dir: Path) -> str:
    vault_root = Path(vault_dir).resolve()
    index_path = vault_root / "index" / "documents_index.jsonl"
    marker_path = index_path.with_name(DOCUMENT_TRANSACTION_MARKER)
    with exclusive_file_lock(index_path):
        return _recover_document_transaction_locked(
            vault_root=vault_root,
            index_path=index_path,
            marker_path=marker_path,
        )


def _recover_document_transaction_locked(*, vault_root: Path, index_path: Path, marker_path: Path) -> str:
    if not marker_path.exists():
        return ""
    marker = _read_json_object(marker_path)
    transaction_id = str(marker.get("transaction_id", "") or "")
    if not transaction_id:
        raise DocumentTransactionRecoveryError("Document transaction marker has no transaction_id.")
    audit_path = _resolve_relative_path(vault_root, str(marker.get("audit_path", "") or ""))
    if str(marker.get("phase", "")) == "committed" or _audit_contains_transaction(audit_path, transaction_id):
        _remove_marker_best_effort(marker_path)
        return "committed"
    try:
        _rollback_from_marker(vault_root=vault_root, index_path=index_path, marker=marker)
    except Exception as exc:
        raise DocumentTransactionRecoveryError(
            "Nedokončenou dokumentovou transakci se nepodařilo obnovit ze zálohy."
        ) from exc
    _remove_marker_best_effort(marker_path)
    return "rolled_back"


def _create_backup(
    *,
    vault_root: Path,
    index_path: Path,
    manifest_path: Path | None,
    backup_group: str,
    document_id: str,
    transaction_id: str,
    related_json_paths: list[Path],
) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    backup_dir = vault_root / "index" / backup_group / f"{stamp}_{_safe_component(document_id)}_{transaction_id[:8]}"
    backup_dir.mkdir(parents=True, exist_ok=False)
    if not index_path.exists():
        raise DocumentTransactionError("Document index is missing; transaction cannot create it implicitly.")
    shutil.copy2(index_path, backup_dir / "documents_index.jsonl")
    if manifest_path is not None and manifest_path.exists():
        shutil.copy2(manifest_path, backup_dir / "manifest.json")
    for index, related_path in enumerate(related_json_paths):
        shutil.copy2(related_path, backup_dir / f"related_{index:03d}.json")
    return backup_dir


def _rollback_from_marker(*, vault_root: Path, index_path: Path, marker: dict[str, Any]) -> None:
    backup_index = _resolve_relative_path(vault_root, str(marker.get("backup_index_path", "") or ""))
    if not backup_index.is_file():
        raise DocumentTransactionRecoveryError("Document transaction index backup is missing.")
    atomic_replace_text_under_external_lock(index_path, backup_index.read_text(encoding="utf-8"))
    if bool(marker.get("manifest_existed")):
        manifest_path = _resolve_relative_path(vault_root, str(marker.get("manifest_path", "") or ""))
        backup_manifest = _resolve_relative_path(vault_root, str(marker.get("backup_manifest_path", "") or ""))
        if not backup_manifest.is_file():
            raise DocumentTransactionRecoveryError("Document transaction manifest backup is missing.")
        atomic_write_text(manifest_path, backup_manifest.read_text(encoding="utf-8"))
    elif bool(marker.get("manifest_will_create")):
        manifest_path = _resolve_relative_path(vault_root, str(marker.get("manifest_path", "") or ""))
        try:
            manifest_path.unlink()
        except FileNotFoundError:
            pass
    related_json_files = marker.get("related_json_files", [])
    if not isinstance(related_json_files, list):
        raise DocumentTransactionRecoveryError("Document transaction related files marker is invalid.")
    for item in related_json_files:
        if not isinstance(item, dict):
            raise DocumentTransactionRecoveryError("Document transaction related file marker is invalid.")
        related_path = _resolve_relative_path(vault_root, str(item.get("path", "") or ""))
        backup_path = _resolve_relative_path(vault_root, str(item.get("backup_path", "") or ""))
        if not backup_path.is_file():
            raise DocumentTransactionRecoveryError("Document transaction related file backup is missing.")
        atomic_write_text(related_path, backup_path.read_text(encoding="utf-8"))


def _validate_mutation(
    previous_record: dict[str, Any],
    mutation: DocumentRecordMutation,
    previous_manifest: dict[str, Any] | None,
    *,
    allow_manifest_create: bool,
) -> None:
    if not isinstance(mutation.index_record, dict) or not isinstance(mutation.audit_record, dict):
        raise DocumentTransactionError("Document mutation must contain dictionary records.")
    previous_id = str(previous_record.get("document_id", "") or "")
    updated_id = str(mutation.index_record.get("document_id", "") or "")
    if not previous_id or updated_id != previous_id:
        raise DocumentTransactionError("Document mutation cannot change document_id.")
    if previous_manifest is None and mutation.manifest_record is not None and not allow_manifest_create:
        raise DocumentTransactionError("Document transaction cannot create a previously missing manifest.")
    if mutation.manifest_record is not None and not isinstance(mutation.manifest_record, dict):
        raise DocumentTransactionError("Document manifest mutation must be a dictionary.")
    if not isinstance(mutation.related_json_files, tuple):
        raise DocumentTransactionError("Document related JSON mutations must be a tuple.")
    for item in mutation.related_json_files:
        if not isinstance(item, DocumentRelatedJsonMutation) or not isinstance(item.record, dict):
            raise DocumentTransactionError("Document related JSON mutation is invalid.")


def _prepare_related_json_files(
    *,
    vault_root: Path,
    mutation: DocumentRecordMutation,
    protected_paths: set[Path],
) -> list[tuple[Path, dict[str, Any]]]:
    prepared: list[tuple[Path, dict[str, Any]]] = []
    seen: set[Path] = set()
    for item in mutation.related_json_files:
        path = _require_within(vault_root, item.path)
        if path in protected_paths or path in seen:
            raise DocumentTransactionError("Document related JSON path is duplicated or reserved.")
        if not path.is_file():
            raise DocumentTransactionError("Document related JSON file is missing.")
        _read_json_object(path)
        prepared.append((path, dict(item.record)))
        seen.add(path)
    return prepared


def _read_jsonl_strict(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DocumentTransactionError(f"Document index has invalid JSON on line {line_number}.") from exc
        if not isinstance(row, dict):
            raise DocumentTransactionError(f"Document index row {line_number} is not an object.")
        rows.append(row)
    return rows


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DocumentTransactionError(f"Transaction JSON cannot be read: {path.name}.") from exc
    if not isinstance(payload, dict):
        raise DocumentTransactionError(f"Transaction JSON is not an object: {path.name}.")
    return payload


def _write_index_under_lock(path: Path, rows: list[dict[str, Any]]) -> None:
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    atomic_replace_text_under_external_lock(path, payload)


def _write_manifest(path: Path, payload: dict[str, Any]) -> None:
    atomic_write_json(path, payload, sort_keys=True)


def _write_related_json_file(path: Path, payload: dict[str, Any]) -> None:
    atomic_write_json(path, payload, sort_keys=True)


def _append_audit(path: Path, payload: dict[str, Any]) -> None:
    append_jsonl_locked(path, payload, sort_keys=True)


def _write_marker(path: Path, marker: dict[str, Any]) -> None:
    atomic_write_json(path, marker, sort_keys=True)


def _set_marker_phase(path: Path, marker: dict[str, Any], phase: str) -> dict[str, Any]:
    updated = dict(marker)
    updated["phase"] = phase
    updated["updated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    _write_marker(path, updated)
    return updated


def _audit_contains_transaction(path: Path, transaction_id: str) -> bool:
    if not path.exists():
        return False
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and str(payload.get("transaction_id", "")) == transaction_id:
            return True
    return False


def _remove_marker_best_effort(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except OSError:
        pass


def _relative_path(root: Path, path: Path) -> str:
    return str(_require_within(root, path).relative_to(root))


def _resolve_relative_path(root: Path, value: str) -> Path:
    if not value or Path(value).is_absolute():
        raise DocumentTransactionRecoveryError("Document transaction marker contains an unsafe path.")
    return _require_within(root, root / value)


def _require_within(root: Path, path: Path) -> Path:
    resolved_root = root.resolve()
    resolved = Path(path).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise DocumentTransactionError("Document transaction path is outside the private vault.")
    return resolved


def _safe_component(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value or "")).strip("-.")[:100]
