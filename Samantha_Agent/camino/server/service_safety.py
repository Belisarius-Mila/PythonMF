"""Small, local-only safeguards for a single Camino server and SQLite upgrades."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def private_write(path: Path, content: bytes) -> None:
    """Create only: never replace a credential, snapshot or service definition."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


@contextmanager
def database_lock(database: Path):
    path = database.with_suffix(database.suffix + ".service-lock")
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def readonly(database: Path) -> sqlite3.Connection:
    return sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)


def snapshot(database: Path, destination: Path) -> Path:
    """SQLite backup API includes committed WAL data; incomplete copies lack receipt."""
    destination.mkdir(mode=0o700, parents=True, exist_ok=True)
    if destination.is_symlink() or destination.stat().st_mode & 0o077:
        raise ValueError("snapshot directory must be private")
    target = destination / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                            + "-" + uuid4().hex + ".sqlite")
    private_write(target, b"")
    source, copy = readonly(database), sqlite3.connect(target)
    try:
        deadline = time.monotonic() + 60
        def progress(_status, _remaining, _total):
            if time.monotonic() > deadline:
                raise TimeoutError("snapshot exceeded the bounded copy interval")
        source.backup(copy, pages=256, progress=progress)
        if copy.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
            raise ValueError("snapshot integrity check failed")
        version = copy.execute("PRAGMA user_version").fetchone()[0]
    finally:
        source.close()
        copy.close()
    with target.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
        os.fsync(stream.fileno())
    private_write(target.with_suffix(".receipt.json"), json.dumps({
        "schema": 1, "user_version": version, "sha256": digest,
        "bytes": target.stat().st_size, "quick_check": "ok",
    }, sort_keys=True).encode())
    return target


def snapshot_before_upgrade(database: Path, destination: Path, version: int) -> Path | None:
    if not database.exists():
        return None
    connection = readonly(database)
    try:
        old = connection.execute("PRAGMA user_version").fetchone()[0]
    finally:
        connection.close()
    if 0 < old < version:
        return snapshot(database, destination)
    if old > version:
        raise ValueError("newer database requires a newer server")
    return None
