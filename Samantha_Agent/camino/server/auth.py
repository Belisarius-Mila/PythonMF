"""Revocable bearer-token verification for the private Camino owner API."""

from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
import stat
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from camino.domain.model import ContractError


SCHEMA_VERSION = 1
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _private_database(path_value: str | Path) -> Path:
    requested = Path(path_value).expanduser()
    if requested.is_symlink():
        raise ContractError("private Camino authentication database cannot be a symlink")
    path = requested.resolve()
    if path.is_relative_to(_PROJECT_ROOT):
        raise ContractError("private Camino authentication database must stay outside the source repository")
    if not path.parent.is_dir():
        raise ContractError("private Camino authentication database parent does not exist")
    if path.exists():
        if not path.is_file() or stat.S_IMODE(path.stat().st_mode) & 0o077:
            raise ContractError("private Camino authentication database must be a restricted regular file")
    else:
        descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(descriptor)
    return path


class RevocableTokenStore:
    """Persist only token digests; token management has no network endpoint."""

    def __init__(self, database_path: str | Path):
        self.path = _private_database(database_path)
        self._initialize()

    def _open(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    def _initialize(self) -> None:
        with self._open() as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, SCHEMA_VERSION):
                raise ContractError("unsupported Camino authentication schema version")
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS owner_tokens ("
                    "id TEXT PRIMARY KEY, label TEXT NOT NULL, token_sha256 TEXT NOT NULL UNIQUE, "
                    "created_at TEXT NOT NULL, revoked_at TEXT)"
                )
                connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def _token_digest(token: str) -> str:
        if not isinstance(token, str) or len(token.encode("utf-8")) < 32 or token.strip() != token:
            raise ContractError("owner token must contain at least 32 bytes without outer whitespace")
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def add(self, token: str, *, label: str) -> str:
        if not isinstance(label, str) or not label.strip() or len(label) > 80:
            raise ContractError("owner token label is required and must be short")
        token_id = str(uuid4())
        digest = self._token_digest(token)
        with self._open() as connection:
            try:
                connection.execute(
                    "INSERT INTO owner_tokens VALUES (?,?,?,?,NULL)",
                    (token_id, label.strip(), digest, _now()),
                )
            except sqlite3.IntegrityError as error:
                raise ContractError("owner token is already registered") from error
        return token_id

    def revoke(self, token_id: str) -> bool:
        try:
            if str(UUID(token_id)) != token_id:
                raise ValueError
        except (TypeError, ValueError, AttributeError) as error:
            raise ContractError("token ID must be a canonical UUID") from error
        with self._open() as connection:
            cursor = connection.execute(
                "UPDATE owner_tokens SET revoked_at=COALESCE(revoked_at,?) WHERE id=?",
                (_now(), token_id),
            )
            return cursor.rowcount == 1

    def authenticate(self, authorization: str) -> bool:
        prefix = "Bearer "
        if not isinstance(authorization, str) or not authorization.startswith(prefix):
            return False
        token = authorization[len(prefix):]
        try:
            digest = self._token_digest(token)
        except ContractError:
            return False
        with self._open() as connection:
            rows = connection.execute(
                "SELECT token_sha256 FROM owner_tokens WHERE revoked_at IS NULL"
            ).fetchall()
        return any(hmac.compare_digest(digest, row["token_sha256"]) for row in rows)

    def active_count(self) -> int:
        with self._open() as connection:
            return int(connection.execute(
                "SELECT COUNT(*) FROM owner_tokens WHERE revoked_at IS NULL"
            ).fetchone()[0])
