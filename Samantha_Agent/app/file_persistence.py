from __future__ import annotations

import copy
import json
import os
import stat
import tempfile
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover - Samantha runs on macOS/Linux.
    fcntl = None


class FilePersistenceError(RuntimeError):
    """Raised when a safe file persistence operation cannot be completed."""


class FileLockTimeoutError(FilePersistenceError):
    """Raised when a stable file lock cannot be acquired in time."""


def lock_path_for(path: Path) -> Path:
    target = Path(path)
    return target.with_name(f"{target.name}.lock")


@contextmanager
def exclusive_file_lock(
    path: Path,
    *,
    timeout: float = 10.0,
    poll_interval: float = 0.05,
) -> Iterator[None]:
    """Lock a stable sidecar inode shared by threads and processes."""

    if fcntl is None:
        raise FilePersistenceError("File locking requires fcntl on macOS/Linux.")
    if timeout < 0:
        raise ValueError("timeout nesmi byt zaporny")
    if poll_interval <= 0:
        raise ValueError("poll_interval musi byt kladny")

    lock_path = lock_path_for(Path(path))
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+b")
    deadline = time.monotonic() + timeout
    try:
        while True:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError as exc:
                if time.monotonic() >= deadline:
                    raise FileLockTimeoutError(f"Timeout pri zamykani souboru: {Path(path).name}") from exc
                time.sleep(min(poll_interval, max(0.0, deadline - time.monotonic())))
        yield
    finally:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def atomic_write_text(
    path: Path,
    text: str,
    *,
    encoding: str = "utf-8",
    timeout: float = 10.0,
) -> None:
    target = Path(path)
    payload = str(text).encode(encoding)
    with exclusive_file_lock(target, timeout=timeout):
        _atomic_write_bytes_unlocked(target, payload)


def atomic_write_json(
    path: Path,
    payload: Any,
    *,
    ensure_ascii: bool = False,
    indent: int | None = 2,
    sort_keys: bool = False,
    timeout: float = 10.0,
) -> None:
    text = json.dumps(payload, ensure_ascii=ensure_ascii, indent=indent, sort_keys=sort_keys) + "\n"
    atomic_write_text(path, text, timeout=timeout)


def update_json_file(
    path: Path,
    updater: Callable[[Any], Any | None],
    *,
    default: Any,
    ensure_ascii: bool = False,
    indent: int | None = 2,
    sort_keys: bool = False,
    timeout: float = 10.0,
) -> Any:
    """Run a read-modify-write transaction under one stable exclusive lock."""

    target = Path(path)
    with exclusive_file_lock(target, timeout=timeout):
        if target.exists():
            with target.open("r", encoding="utf-8") as handle:
                current = json.load(handle)
        else:
            current = copy.deepcopy(default)
        updated = updater(current)
        if updated is None:
            updated = current
        text = json.dumps(updated, ensure_ascii=ensure_ascii, indent=indent, sort_keys=sort_keys) + "\n"
        _atomic_write_bytes_unlocked(target, text.encode("utf-8"))
        return updated


def append_jsonl_locked(
    path: Path,
    payload: Any,
    *,
    ensure_ascii: bool = False,
    sort_keys: bool = False,
    timeout: float = 10.0,
) -> None:
    target = Path(path)
    encoded = (json.dumps(payload, ensure_ascii=ensure_ascii, sort_keys=sort_keys) + "\n").encode("utf-8")
    with exclusive_file_lock(target, timeout=timeout):
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("ab") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())


def _atomic_write_bytes_unlocked(path: Path, payload: bytes) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    existing_mode = _existing_file_mode(target)
    file_descriptor, temp_name = tempfile.mkstemp(
        dir=str(target.parent),
        prefix=f".{target.name}.",
        suffix=".tmp",
    )
    temp_path = Path(temp_name)
    try:
        if existing_mode is not None:
            os.fchmod(file_descriptor, existing_mode)
        with os.fdopen(file_descriptor, "wb") as handle:
            file_descriptor = -1
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, target)
        _fsync_directory(target.parent)
    finally:
        if file_descriptor >= 0:
            os.close(file_descriptor)
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


def _existing_file_mode(path: Path) -> int | None:
    try:
        return stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        return None


def _fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        try:
            os.fsync(descriptor)
        except OSError:
            # Some filesystems do not support fsync on directories.
            pass
    finally:
        os.close(descriptor)
