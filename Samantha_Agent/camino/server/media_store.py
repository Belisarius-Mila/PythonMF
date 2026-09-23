"""C05a durable chunk, finalization, and crash-recovery store."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import shutil
import sqlite3
import stat
import tempfile
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from pathlib import Path
from typing import Any, BinaryIO, Callable
from uuid import UUID, uuid4

from camino.domain.model import ContractError
from camino.domain.revision_store import StoreNotFound


SCHEMA_VERSION = 1
DEFAULT_CHUNK_BYTES = 8 * 1024 * 1024
DEFAULT_MAX_ASSET_BYTES = 256 * 1024 * 1024 * 1024
DEFAULT_RESERVE_BYTES = 512 * 1024 * 1024
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class MediaStoreError(Exception):
    def __init__(self, status: int | HTTPStatus, code: str, message: str):
        super().__init__(message)
        self.status = int(status)
        self.code = code


@dataclass(frozen=True, slots=True)
class ChunkReservation:
    asset_id: str
    chunk_index: int
    byte_count: int
    sha256: str
    already_stored: bool = False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _uuid(value: Any, *, label: str = "ID") -> str:
    if not isinstance(value, str):
        raise MediaStoreError(HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_id", f"{label} must be a UUID")
    try:
        if str(UUID(value)) != value:
            raise ValueError
    except ValueError as error:
        raise MediaStoreError(
            HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_id", f"{label} must be a canonical UUID"
        ) from error
    return value


def _sha256(value: Any) -> str:
    if not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None:
        raise MediaStoreError(
            HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_sha256", "SHA-256 must be lowercase hexadecimal"
        )
    return value


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class MediaStore:
    """Persistent media truth; network delivery itself remains at-least-once."""

    def __init__(
        self,
        database_path: str | Path,
        root: str | Path,
        *,
        asset_lookup: Callable[[str], dict[str, Any]],
        max_asset_bytes: int = DEFAULT_MAX_ASSET_BYTES,
        max_chunk_bytes: int = DEFAULT_CHUNK_BYTES,
        reserve_bytes: int = DEFAULT_RESERVE_BYTES,
        free_bytes: Callable[[Path], int] | None = None,
        fault_injector: Callable[[str, str, int | None], None] | None = None,
    ):
        if not callable(asset_lookup):
            raise TypeError("an explicit accepted Asset lookup is required")
        if max_asset_bytes <= 0 or max_chunk_bytes <= 0 or reserve_bytes < 0:
            raise ValueError("media limits must be positive")
        self.database_path = self._private_database(database_path)
        self.root = self._private_root(root)
        self.asset_lookup = asset_lookup
        self.max_asset_bytes = max_asset_bytes
        self.max_chunk_bytes = max_chunk_bytes
        self.reserve_bytes = reserve_bytes
        self.free_bytes = free_bytes or (lambda path: shutil.disk_usage(path).free)
        self.fault_injector = fault_injector
        self.sessions = self.root / "sessions"
        self.objects = self.root / "objects"
        self.staging = self.root / ".staging"
        self.quarantine = self.root / "quarantine"
        self._lock = threading.RLock()
        for directory in (self.sessions, self.objects, self.staging, self.quarantine):
            self._prepare_directory(directory)
        self._initialize()
        self.recovery_report = self.recover()

    @staticmethod
    def _private_database(path_value: str | Path) -> Path:
        requested = Path(path_value).expanduser()
        if requested.is_symlink():
            raise ContractError("private Camino media database cannot be a symlink")
        path = requested.resolve()
        if path.is_relative_to(_PROJECT_ROOT):
            raise ContractError("private Camino media database must stay outside the source repository")
        if not path.parent.is_dir():
            raise ContractError("private Camino media database parent does not exist")
        if path.exists():
            if not path.is_file() or stat.S_IMODE(path.stat().st_mode) & 0o077:
                raise ContractError("private Camino media database must be a restricted regular file")
        else:
            descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(descriptor)
        return path

    @staticmethod
    def _private_root(path_value: str | Path) -> Path:
        requested = Path(path_value).expanduser()
        if requested.is_symlink():
            raise ContractError("private Camino media root cannot be a symlink")
        path = requested.resolve()
        if path.is_relative_to(_PROJECT_ROOT):
            raise ContractError("private Camino media root must stay outside the source repository")
        if path.exists():
            if not path.is_dir() or stat.S_IMODE(path.stat().st_mode) & 0o077:
                raise ContractError("private Camino media root must be a restricted directory")
        else:
            path.mkdir(mode=0o700)
        return path

    def _open(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    @contextmanager
    def _transaction(self):
        connection = self._open()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._transaction() as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, SCHEMA_VERSION):
                raise ContractError("unsupported Camino media database schema version")
            for statement in (
                "CREATE TABLE IF NOT EXISTS upload_sessions ("
                "asset_id TEXT PRIMARY KEY, moment_id TEXT NOT NULL, media_kind TEXT NOT NULL, "
                "byte_count INTEGER NOT NULL, sha256 TEXT NOT NULL, chunk_size INTEGER NOT NULL, "
                "chunk_count INTEGER NOT NULL, state TEXT NOT NULL, failure_code TEXT, "
                "created_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
                "CREATE TABLE IF NOT EXISTS upload_chunks ("
                "asset_id TEXT NOT NULL, chunk_index INTEGER NOT NULL, byte_count INTEGER NOT NULL, "
                "sha256 TEXT NOT NULL, state TEXT NOT NULL, updated_at TEXT NOT NULL, "
                "PRIMARY KEY(asset_id,chunk_index), "
                "FOREIGN KEY(asset_id) REFERENCES upload_sessions(asset_id))",
                "CREATE TABLE IF NOT EXISTS verified_assets ("
                "asset_id TEXT PRIMARY KEY, receipt TEXT NOT NULL, verified_at TEXT NOT NULL, "
                "FOREIGN KEY(asset_id) REFERENCES upload_sessions(asset_id))",
                "CREATE TABLE IF NOT EXISTS finalization_journal ("
                "asset_id TEXT PRIMARY KEY, phase TEXT NOT NULL, staging_name TEXT, updated_at TEXT NOT NULL, "
                "FOREIGN KEY(asset_id) REFERENCES upload_sessions(asset_id))",
                "CREATE TABLE IF NOT EXISTS recovery_events ("
                "id TEXT PRIMARY KEY, asset_id TEXT, code TEXT NOT NULL, created_at TEXT NOT NULL)",
            ):
                connection.execute(statement)
            connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")

    def create_session(self, asset_id: str, *, chunk_size: int = DEFAULT_CHUNK_BYTES) -> tuple[dict[str, Any], bool]:
        asset_id = _uuid(asset_id, label="Asset ID")
        if isinstance(chunk_size, bool) or not isinstance(chunk_size, int) or not 1 <= chunk_size <= self.max_chunk_bytes:
            raise MediaStoreError(HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_chunk_size", "chunk size is invalid")
        manifest = self._accepted_manifest(asset_id)
        byte_count = manifest["byte_count"]
        if byte_count <= 0 or byte_count > self.max_asset_bytes:
            raise MediaStoreError(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "invalid_asset_size", "Asset size is outside server limits"
            )
        digest = manifest.get("sha256")
        if digest is None:
            raise MediaStoreError(
                HTTPStatus.CONFLICT, "asset_hash_pending", "accepted Asset manifest has no final SHA-256"
            )
        digest = _sha256(digest)
        chunk_count = (byte_count + chunk_size - 1) // chunk_size
        identity = (
            asset_id, manifest["moment_id"], manifest["media_kind"], byte_count,
            digest, chunk_size, chunk_count,
        )
        with self._lock, self._transaction() as connection:
            row = connection.execute(
                "SELECT asset_id,moment_id,media_kind,byte_count,sha256,chunk_size,chunk_count "
                "FROM upload_sessions WHERE asset_id=?", (asset_id,),
            ).fetchone()
            if row is not None:
                if tuple(row) != identity:
                    raise MediaStoreError(
                        HTTPStatus.CONFLICT, "asset_identity_conflict", "upload session has different identity"
                    )
                created = False
            else:
                now = _now()
                connection.execute(
                    "INSERT INTO upload_sessions VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (*identity, "uploading", None, now, now),
                )
                created = True
                self._prepare_directory(self.sessions / asset_id)
                self._prepare_directory(self.sessions / asset_id / "chunks")
                self._fsync_directory(self.sessions)
        return self.status(asset_id), created

    def reserve_chunk(
        self,
        asset_id: str,
        chunk_index: int,
        *,
        content_length: int,
        expected_sha256: str,
    ) -> ChunkReservation:
        asset_id = _uuid(asset_id, label="Asset ID")
        expected_sha256 = _sha256(expected_sha256)
        with self._lock:
            session = self._session(asset_id)
            if isinstance(chunk_index, bool) or not isinstance(chunk_index, int) or not 0 <= chunk_index < session["chunk_count"]:
                raise MediaStoreError(HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_chunk_index", "chunk index is invalid")
            expected_length = self._chunk_length(session, chunk_index)
            if content_length != expected_length:
                raise MediaStoreError(HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_chunk_length", "chunk length is invalid")
            self._ensure_space(content_length)
            destination = self._chunk_path(asset_id, chunk_index)
            with self._transaction() as connection:
                row = connection.execute(
                    "SELECT byte_count,sha256,state FROM upload_chunks WHERE asset_id=? AND chunk_index=?",
                    (asset_id, chunk_index),
                ).fetchone()
                if row is not None and (row["byte_count"], row["sha256"]) != (content_length, expected_sha256):
                    raise MediaStoreError(
                        HTTPStatus.CONFLICT, "chunk_identity_conflict", "chunk index has different identity"
                    )
                if row is not None and self._valid_file(destination, content_length, expected_sha256):
                    if row["state"] != "stored":
                        connection.execute(
                            "UPDATE upload_chunks SET state='stored',updated_at=? WHERE asset_id=? AND chunk_index=?",
                            (_now(), asset_id, chunk_index),
                        )
                    return ChunkReservation(asset_id, chunk_index, content_length, expected_sha256, True)
                if row is not None and row["state"] == "stored":
                    self._mark_recovery_required(connection, asset_id, "stored_chunk_missing_or_invalid")
                    raise MediaStoreError(
                        HTTPStatus.CONFLICT, "storage_inconsistent", "stored chunk is missing or invalid"
                    )
                if row is None:
                    connection.execute(
                        "INSERT INTO upload_chunks VALUES (?,?,?,?,?,?)",
                        (asset_id, chunk_index, content_length, expected_sha256, "pending", _now()),
                    )
            return ChunkReservation(asset_id, chunk_index, content_length, expected_sha256)

    def new_chunk_staging(self, reservation: ChunkReservation) -> Path:
        descriptor, name = tempfile.mkstemp(
            prefix=f".{reservation.asset_id}.{reservation.chunk_index}.",
            suffix=".incoming", dir=self.staging,
        )
        os.fchmod(descriptor, 0o600)
        os.close(descriptor)
        return Path(name)

    def commit_chunk(self, reservation: ChunkReservation, staged_path: str | Path) -> tuple[dict[str, Any], bool]:
        path = Path(staged_path).resolve()
        if path.parent != self.staging.resolve() or path.is_symlink() or not path.is_file():
            raise MediaStoreError(HTTPStatus.CONFLICT, "unsafe_staging_file", "staging file is unsafe")
        with self._lock:
            if path.stat().st_size != reservation.byte_count or not hmac.compare_digest(
                _hash_file(path), reservation.sha256
            ):
                self.preserve_staging(path, "chunk_verification_failed", reservation.asset_id)
                raise MediaStoreError(
                    HTTPStatus.UNPROCESSABLE_ENTITY, "chunk_hash_mismatch", "chunk bytes do not match receipt"
                )
            destination = self._chunk_path(reservation.asset_id, reservation.chunk_index)
            if destination.exists() or destination.is_symlink():
                if not self._valid_file(destination, reservation.byte_count, reservation.sha256):
                    self.preserve_staging(path, "chunk_conflict", reservation.asset_id)
                    with self._transaction() as connection:
                        self._mark_recovery_required(connection, reservation.asset_id, "chunk_path_conflict")
                    raise MediaStoreError(
                        HTTPStatus.CONFLICT, "chunk_identity_conflict", "chunk path contains different bytes"
                    )
                self.preserve_staging(path, "duplicate_chunk", reservation.asset_id)
                created = False
            else:
                os.replace(path, destination)
                self._fsync_directory(destination.parent)
                created = True
            self._fault("after_chunk_install", reservation.asset_id, reservation.chunk_index)
            journal_mismatch = False
            with self._transaction() as connection:
                row = connection.execute(
                    "SELECT byte_count,sha256 FROM upload_chunks WHERE asset_id=? AND chunk_index=?",
                    (reservation.asset_id, reservation.chunk_index),
                ).fetchone()
                if row is None or (row["byte_count"], row["sha256"]) != (
                    reservation.byte_count, reservation.sha256,
                ):
                    self._mark_recovery_required(connection, reservation.asset_id, "chunk_journal_mismatch")
                    journal_mismatch = True
                else:
                    connection.execute(
                        "UPDATE upload_chunks SET state='stored',updated_at=? WHERE asset_id=? AND chunk_index=?",
                        (_now(), reservation.asset_id, reservation.chunk_index),
                    )
            if journal_mismatch:
                raise MediaStoreError(
                    HTTPStatus.CONFLICT, "storage_inconsistent", "chunk journal no longer matches bytes"
                )
            return self.status(reservation.asset_id), created

    def receive_chunk(
        self,
        asset_id: str,
        chunk_index: int,
        *,
        content_length: int,
        expected_sha256: str,
        stream: BinaryIO,
    ) -> tuple[dict[str, Any], bool]:
        reservation = self.reserve_chunk(
            asset_id, chunk_index, content_length=content_length, expected_sha256=expected_sha256,
        )
        if reservation.already_stored:
            return self.status(asset_id), False
        path = self.new_chunk_staging(reservation)
        remaining = content_length
        try:
            with path.open("wb") as output:
                while remaining:
                    block = stream.read(min(1024 * 1024, remaining))
                    if not block:
                        raise MediaStoreError(
                            HTTPStatus.BAD_REQUEST, "incomplete_chunk", "chunk body ended early"
                        )
                    output.write(block)
                    remaining -= len(block)
                output.flush()
                os.fsync(output.fileno())
            return self.commit_chunk(reservation, path)
        except Exception:
            if path.exists():
                self.preserve_staging(path, "incomplete_chunk", asset_id)
            raise

    def finalize(self, asset_id: str) -> tuple[dict[str, Any], bool]:
        asset_id = _uuid(asset_id, label="Asset ID")
        with self._lock:
            existing = self._verified_receipt(asset_id)
            if existing is not None:
                return existing, False
            session = self._session(asset_id)
            stored = self._stored_indices(session, validate=True)
            if len(stored) != session["chunk_count"]:
                raise MediaStoreError(HTTPStatus.CONFLICT, "missing_chunks", "not all chunks are safely stored")
            self._ensure_space(session["byte_count"])
            descriptor, name = tempfile.mkstemp(prefix=f".{asset_id}.", suffix=".assembled", dir=self.staging)
            staged = Path(name)
            os.fchmod(descriptor, 0o600)
            with self._transaction() as connection:
                now = _now()
                connection.execute(
                    "UPDATE upload_sessions SET state='verifying',failure_code=NULL,updated_at=? WHERE asset_id=?",
                    (now, asset_id),
                )
                connection.execute(
                    "INSERT INTO finalization_journal VALUES (?,?,?,?) "
                    "ON CONFLICT(asset_id) DO UPDATE SET phase=excluded.phase,staging_name=excluded.staging_name,updated_at=excluded.updated_at",
                    (asset_id, "assembling", staged.name, now),
                )
            digest = hashlib.sha256()
            size = 0
            try:
                with os.fdopen(descriptor, "wb") as output:
                    descriptor = -1
                    for index in range(session["chunk_count"]):
                        with self._chunk_path(asset_id, index).open("rb") as source:
                            for block in iter(lambda: source.read(1024 * 1024), b""):
                                output.write(block)
                                digest.update(block)
                                size += len(block)
                    output.flush()
                    os.fsync(output.fileno())
                if size != session["byte_count"] or not hmac.compare_digest(digest.hexdigest(), session["sha256"]):
                    self.preserve_staging(staged, "asset_verification_failed", asset_id)
                    with self._transaction() as connection:
                        connection.execute(
                            "UPDATE upload_sessions SET state='verification_failed',failure_code='asset_hash_mismatch',updated_at=? WHERE asset_id=?",
                            (_now(), asset_id),
                        )
                        connection.execute(
                            "UPDATE finalization_journal SET phase='verification_failed',staging_name=NULL,updated_at=? WHERE asset_id=?",
                            (_now(), asset_id),
                        )
                    raise MediaStoreError(
                        HTTPStatus.UNPROCESSABLE_ENTITY, "asset_hash_mismatch", "assembled Asset hash is invalid"
                    )
                with self._transaction() as connection:
                    connection.execute(
                        "UPDATE finalization_journal SET phase='assembled',updated_at=? WHERE asset_id=?",
                        (_now(), asset_id),
                    )
                destination = self._object_path(asset_id)
                if destination.exists() or destination.is_symlink():
                    if not self._valid_file(destination, session["byte_count"], session["sha256"]):
                        self.preserve_staging(staged, "object_conflict", asset_id)
                        with self._transaction() as connection:
                            self._mark_recovery_required(connection, asset_id, "object_path_conflict")
                        raise MediaStoreError(
                            HTTPStatus.CONFLICT, "asset_identity_conflict", "object path contains different bytes"
                        )
                    self.preserve_staging(staged, "duplicate_object", asset_id)
                    created = False
                else:
                    os.replace(staged, destination)
                    self._fsync_directory(self.objects)
                    created = True
                self._fault("after_object_install", asset_id, None)
                receipt = self._complete_verification(session)
                return receipt, created
            except Exception:
                if staged.exists():
                    self.preserve_staging(staged, "interrupted_finalization", asset_id)
                raise
            finally:
                if descriptor >= 0:
                    os.close(descriptor)

    def status(self, asset_id: str) -> dict[str, Any]:
        asset_id = _uuid(asset_id, label="Asset ID")
        with self._lock:
            session = self._session(asset_id)
            accepted = self._stored_indices(session, validate=False)
            body: dict[str, Any] = {
                "contract_version": 1,
                "asset_id": asset_id,
                "state": session["state"],
                "byte_count": session["byte_count"],
                "sha256": session["sha256"],
                "chunk_size": session["chunk_size"],
                "chunk_count": session["chunk_count"],
                "accepted_chunks": accepted,
                "missing_chunks": [
                    index for index in range(session["chunk_count"]) if index not in accepted
                ],
            }
            receipt = self._verified_receipt(asset_id)
            if receipt is not None:
                body["state"] = "verified"
                body["receipt"] = receipt
            elif session["state"] == "verified":
                with self._transaction() as connection:
                    self._mark_recovery_required(connection, asset_id, "verified_asset_incomplete")
                body["state"] = "recovery_required"
                body["failure_code"] = "verified_asset_incomplete"
            elif session["failure_code"]:
                body["failure_code"] = session["failure_code"]
            return body

    def recover(self) -> dict[str, int]:
        report = {"chunks_recovered": 0, "assets_recovered": 0, "files_quarantined": 0, "blocked": 0}
        with self._lock:
            with self._open() as connection:
                sessions = [dict(row) for row in connection.execute("SELECT * FROM upload_sessions")]
                chunks = [dict(row) for row in connection.execute("SELECT * FROM upload_chunks")]
                journals = [dict(row) for row in connection.execute("SELECT * FROM finalization_journal")]
            known_chunks = {(row["asset_id"], row["chunk_index"]) for row in chunks}
            for row in chunks:
                path = self._chunk_path(row["asset_id"], row["chunk_index"])
                if self._valid_file(path, row["byte_count"], row["sha256"]):
                    if row["state"] != "stored":
                        with self._transaction() as connection:
                            connection.execute(
                                "UPDATE upload_chunks SET state='stored',updated_at=? WHERE asset_id=? AND chunk_index=?",
                                (_now(), row["asset_id"], row["chunk_index"]),
                            )
                        report["chunks_recovered"] += 1
                elif row["state"] == "stored":
                    with self._transaction() as connection:
                        self._mark_recovery_required(connection, row["asset_id"], "stored_chunk_missing_or_invalid")
                    report["blocked"] += 1
            for path in self.sessions.glob("*/chunks/*.part"):
                try:
                    index = int(path.stem)
                except ValueError:
                    index = -1
                asset_id = path.parent.parent.name
                if (asset_id, index) not in known_chunks:
                    self._preserve(path, "orphan_chunk", asset_id if self._looks_uuid(asset_id) else None)
                    report["files_quarantined"] += 1
            session_map = {row["asset_id"]: row for row in sessions}
            for journal in journals:
                if journal["phase"] == "complete":
                    continue
                session = session_map.get(journal["asset_id"])
                if session is None:
                    report["blocked"] += 1
                    continue
                if self._recover_finalization(session, journal):
                    report["assets_recovered"] += 1
            known_assets = set(session_map)
            for path in self.objects.glob("*.bin"):
                if path.stem not in known_assets:
                    self._preserve(path, "orphan_object", path.stem if self._looks_uuid(path.stem) else None)
                    report["files_quarantined"] += 1
            for session in sessions:
                if session["state"] == "verified" and self._verified_receipt(session["asset_id"]) is None:
                    with self._transaction() as connection:
                        self._mark_recovery_required(connection, session["asset_id"], "verified_asset_incomplete")
                    report["blocked"] += 1
        return report

    def preserve_staging(self, path: str | Path, reason: str, asset_id: str | None = None) -> Path | None:
        source = Path(path)
        if not source.exists():
            return None
        return self._preserve(source, reason, asset_id)

    def _accepted_manifest(self, asset_id: str) -> dict[str, Any]:
        try:
            manifest = self.asset_lookup(asset_id)
        except StoreNotFound as error:
            raise MediaStoreError(
                HTTPStatus.NOT_FOUND, "asset_manifest_not_found", "accepted Asset manifest is missing"
            ) from error
        except ContractError as error:
            raise MediaStoreError(
                HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_asset_manifest", "accepted Asset manifest is invalid"
            ) from error
        required = {"id", "moment_id", "media_kind", "origin", "byte_count", "sha256", "duration_ms"}
        if not isinstance(manifest, dict) or set(manifest) != required or manifest.get("id") != asset_id:
            raise MediaStoreError(
                HTTPStatus.CONFLICT, "asset_manifest_mismatch", "accepted Asset manifest is inconsistent"
            )
        _uuid(manifest["moment_id"], label="Moment ID")
        if manifest["media_kind"] not in {"photo", "video", "audio"}:
            raise MediaStoreError(HTTPStatus.CONFLICT, "asset_manifest_mismatch", "media kind is invalid")
        if isinstance(manifest["byte_count"], bool) or not isinstance(manifest["byte_count"], int):
            raise MediaStoreError(HTTPStatus.CONFLICT, "asset_manifest_mismatch", "Asset size is invalid")
        return manifest

    def _session(self, asset_id: str) -> dict[str, Any]:
        with self._open() as connection:
            row = connection.execute("SELECT * FROM upload_sessions WHERE asset_id=?", (asset_id,)).fetchone()
        if row is None:
            raise MediaStoreError(HTTPStatus.NOT_FOUND, "upload_session_not_found", "upload session is missing")
        return dict(row)

    @staticmethod
    def _chunk_length(session: dict[str, Any], index: int) -> int:
        if index < session["chunk_count"] - 1:
            return session["chunk_size"]
        return session["byte_count"] - session["chunk_size"] * index

    def _stored_indices(self, session: dict[str, Any], *, validate: bool) -> list[int]:
        with self._open() as connection:
            rows = connection.execute(
                "SELECT chunk_index,byte_count,sha256 FROM upload_chunks "
                "WHERE asset_id=? AND state='stored' ORDER BY chunk_index", (session["asset_id"],),
            ).fetchall()
        result = []
        for row in rows:
            if not validate or self._valid_file(
                self._chunk_path(session["asset_id"], row["chunk_index"]), row["byte_count"], row["sha256"]
            ):
                result.append(row["chunk_index"])
        return result

    def _verified_receipt(self, asset_id: str) -> dict[str, Any] | None:
        with self._open() as connection:
            row = connection.execute(
                "SELECT receipt FROM verified_assets WHERE asset_id=?", (asset_id,),
            ).fetchone()
        if row is None:
            return None
        receipt = json.loads(row["receipt"])
        if not self._valid_file(self._object_path(asset_id), receipt["byte_count"], receipt["sha256"]):
            return None
        return receipt

    def _complete_verification(self, session: dict[str, Any]) -> dict[str, Any]:
        verified_at = _now()
        receipt = {
            "contract_version": 1,
            "asset_id": session["asset_id"],
            "moment_id": session["moment_id"],
            "media_kind": session["media_kind"],
            "byte_count": session["byte_count"],
            "sha256": session["sha256"],
            "chunk_count": session["chunk_count"],
            "state": "verified",
            "verified_at": verified_at,
        }
        body = json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        receipt_conflict = False
        with self._transaction() as connection:
            prior = connection.execute(
                "SELECT receipt FROM verified_assets WHERE asset_id=?", (session["asset_id"],),
            ).fetchone()
            if prior is not None:
                existing = json.loads(prior["receipt"])
                for key in ("asset_id", "moment_id", "media_kind", "byte_count", "sha256", "chunk_count", "state"):
                    if existing.get(key) != receipt[key]:
                        self._mark_recovery_required(connection, session["asset_id"], "verified_receipt_conflict")
                        receipt_conflict = True
                        break
                receipt = existing
            else:
                connection.execute(
                    "INSERT INTO verified_assets VALUES (?,?,?)",
                    (session["asset_id"], body, verified_at),
                )
            if not receipt_conflict:
                connection.execute(
                    "UPDATE upload_sessions SET state='verified',failure_code=NULL,updated_at=? WHERE asset_id=?",
                    (_now(), session["asset_id"]),
                )
                connection.execute(
                    "UPDATE finalization_journal SET phase='complete',staging_name=NULL,updated_at=? WHERE asset_id=?",
                    (_now(), session["asset_id"]),
                )
        if receipt_conflict:
            raise MediaStoreError(
                HTTPStatus.CONFLICT, "receipt_identity_conflict", "verified receipt has different identity"
            )
        return receipt

    def _recover_finalization(self, session: dict[str, Any], journal: dict[str, Any]) -> bool:
        asset_id = session["asset_id"]
        destination = self._object_path(asset_id)
        if self._valid_file(destination, session["byte_count"], session["sha256"]):
            self._complete_verification(session)
            return True
        staged_name = journal.get("staging_name")
        staged = self.staging / staged_name if staged_name else None
        if staged is not None and self._valid_file(staged, session["byte_count"], session["sha256"]):
            os.replace(staged, destination)
            self._fsync_directory(self.objects)
            self._complete_verification(session)
            return True
        with self._transaction() as connection:
            connection.execute(
                "UPDATE upload_sessions SET state='uploading',failure_code=NULL,updated_at=? WHERE asset_id=?",
                (_now(), asset_id),
            )
            connection.execute(
                "UPDATE finalization_journal SET phase='retry_required',staging_name=NULL,updated_at=? WHERE asset_id=?",
                (_now(), asset_id),
            )
        return False

    def _ensure_space(self, incoming_bytes: int) -> None:
        try:
            available = int(self.free_bytes(self.root))
        except (OSError, TypeError, ValueError) as error:
            raise MediaStoreError(
                HTTPStatus.SERVICE_UNAVAILABLE, "storage_unavailable", "free space cannot be measured"
            ) from error
        if available < incoming_bytes + self.reserve_bytes:
            raise MediaStoreError(
                HTTPStatus.INSUFFICIENT_STORAGE, "insufficient_storage", "server does not have safe free space"
            )

    def _mark_recovery_required(self, connection: sqlite3.Connection, asset_id: str, code: str) -> None:
        connection.execute(
            "UPDATE upload_sessions SET state='recovery_required',failure_code=?,updated_at=? WHERE asset_id=?",
            (code, _now(), asset_id),
        )
        connection.execute(
            "INSERT INTO recovery_events VALUES (?,?,?,?)",
            (str(uuid4()), asset_id, code, _now()),
        )

    def _chunk_path(self, asset_id: str, index: int) -> Path:
        return self.sessions / asset_id / "chunks" / f"{index:08d}.part"

    def _object_path(self, asset_id: str) -> Path:
        return self.objects / f"{asset_id}.bin"

    @staticmethod
    def _valid_file(path: Path, byte_count: int, sha256: str) -> bool:
        return bool(
            path.exists() and not path.is_symlink() and path.is_file()
            and path.stat().st_size == byte_count
            and hmac.compare_digest(_hash_file(path), sha256)
        )

    def _preserve(self, source: Path, reason: str, asset_id: str | None) -> Path:
        safe_reason = re.sub(r"[^a-z0-9_]+", "_", reason.lower()).strip("_") or "preserved"
        destination = self.quarantine / f"{source.name}.{safe_reason}.{uuid4()}"
        os.replace(source, destination)
        self._fsync_directory(self.quarantine)
        with self._transaction() as connection:
            connection.execute(
                "INSERT INTO recovery_events VALUES (?,?,?,?)",
                (str(uuid4()), asset_id, safe_reason, _now()),
            )
        return destination

    def _fault(self, phase: str, asset_id: str, chunk_index: int | None) -> None:
        if self.fault_injector is not None:
            self.fault_injector(phase, asset_id, chunk_index)

    @staticmethod
    def _looks_uuid(value: str) -> bool:
        try:
            return str(UUID(value)) == value
        except (TypeError, ValueError, AttributeError):
            return False

    @staticmethod
    def _prepare_directory(directory: Path) -> None:
        if directory.exists():
            if directory.is_symlink() or not directory.is_dir() or stat.S_IMODE(directory.stat().st_mode) & 0o077:
                raise ContractError("private Camino media directory is unsafe")
            return
        directory.mkdir(mode=0o700)

    @staticmethod
    def _fsync_directory(directory: Path) -> None:
        descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
