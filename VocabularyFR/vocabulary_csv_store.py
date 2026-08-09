"""Crash-safe CSV persistence for the VocabularyFR desktop application."""

from __future__ import annotations

import csv
import hashlib
import io
import os
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping, Sequence


VOCABULARY_FIELDNAMES = (
    "FR",
    "CZ",
    "Order",
    "Sentence",
    "SentenceT",
    "L",
    "HT",
    "gender_fr",
)


class VocabularyCsvError(RuntimeError):
    """Base class for errors that must stop a CSV save."""


class VocabularyCsvConflictError(VocabularyCsvError):
    """The source file changed since the application loaded it."""


@dataclass(frozen=True)
class CsvSnapshot:
    sha256: str
    size: int


@dataclass(frozen=True)
class CsvDocument:
    fieldnames: tuple[str, ...]
    rows: tuple[dict[str, str], ...]
    snapshot: CsvSnapshot


@dataclass(frozen=True)
class CsvSaveResult:
    snapshot: CsvSnapshot
    fieldnames: tuple[str, ...]
    backup_path: Path | None


def _snapshot_bytes(content: bytes) -> CsvSnapshot:
    return CsvSnapshot(
        sha256=hashlib.sha256(content).hexdigest(),
        size=len(content),
    )


def snapshot_file(path: str | os.PathLike[str]) -> CsvSnapshot:
    csv_path = Path(path)
    return _snapshot_bytes(csv_path.read_bytes())


def _read_csv_bytes(content: bytes) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise VocabularyCsvError("CSV není platně kódované v UTF-8.") from exc

    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None:
        raise VocabularyCsvError("CSV nemá hlavičku.")

    fieldnames = tuple(str(name or "") for name in reader.fieldnames)
    if not fieldnames or any(not name.strip() for name in fieldnames):
        raise VocabularyCsvError("CSV obsahuje prázdný název sloupce.")
    if len(set(fieldnames)) != len(fieldnames):
        raise VocabularyCsvError("CSV obsahuje duplicitní názvy sloupců.")

    rows: list[dict[str, str]] = []
    for raw_row in reader:
        if None in raw_row:
            raise VocabularyCsvError("CSV obsahuje řádek s více hodnotami než hlavička.")
        rows.append({name: str(raw_row.get(name) or "") for name in fieldnames})
    return fieldnames, tuple(rows)


def read_csv_document(path: str | os.PathLike[str]) -> CsvDocument:
    csv_path = Path(path)
    content = csv_path.read_bytes()
    fieldnames, rows = _read_csv_bytes(content)
    return CsvDocument(
        fieldnames=fieldnames,
        rows=rows,
        snapshot=_snapshot_bytes(content),
    )


def merged_fieldnames(
    original: Sequence[str],
    rows: Iterable[Mapping[str, object]],
) -> tuple[str, ...]:
    """Keep the original schema and append only genuinely new columns."""

    result: list[str] = []
    seen: set[str] = set()
    for name in (*original, *VOCABULARY_FIELDNAMES):
        preserved = str(name or "")
        if preserved.strip() and preserved not in seen:
            result.append(preserved)
            seen.add(preserved)
    for row in rows:
        for name in row:
            preserved = str(name or "")
            if preserved.strip() and preserved not in seen:
                result.append(preserved)
                seen.add(preserved)
    return tuple(result)


def _write_temp_csv(
    csv_path: Path,
    rows: Sequence[Mapping[str, object]],
    fieldnames: tuple[str, ...],
    mode: int,
) -> Path:
    descriptor, temp_name = tempfile.mkstemp(
        dir=csv_path.parent,
        prefix=f".{csv_path.name}.",
        suffix=".tmp",
    )
    temp_path = Path(temp_name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=fieldnames,
                extrasaction="raise",
            )
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        # The temporary file is intentionally retained as a recovery artifact.
        raise
    return temp_path


def _validate_temp_csv(
    temp_path: Path,
    *,
    expected_fieldnames: tuple[str, ...],
    expected_rows: Sequence[Mapping[str, object]],
) -> None:
    document = read_csv_document(temp_path)
    if document.fieldnames != expected_fieldnames:
        raise VocabularyCsvError("Kontrola dočasného CSV zjistila změnu hlavičky.")
    expected_content = tuple(
        {
            name: "" if row.get(name) is None else str(row.get(name, ""))
            for name in expected_fieldnames
        }
        for row in expected_rows
    )
    if document.rows != expected_content:
        raise VocabularyCsvError("Kontrola dočasného CSV zjistila změnu uložených dat.")


def _create_backup(source: Path, backup_dir: Path, snapshot: CsvSnapshot) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f")
    backup_path = backup_dir / (
        f"{source.stem}.before_session_{stamp}_{snapshot.sha256[:12]}{source.suffix}"
    )
    shutil.copy2(source, backup_path)
    with backup_path.open("rb") as handle:
        os.fsync(handle.fileno())
    if snapshot_file(backup_path) != snapshot:
        raise VocabularyCsvError("Kontrolní součet zálohy CSV nesouhlasí.")
    return backup_path


def save_csv_atomic(
    path: str | os.PathLike[str],
    rows: Sequence[Mapping[str, object]],
    *,
    fieldnames: Sequence[str],
    expected_snapshot: CsvSnapshot,
    backup_dir: str | os.PathLike[str] | None = None,
    create_backup: bool = False,
) -> CsvSaveResult:
    """Validate, back up and atomically replace one CSV file.

    The caller must provide the snapshot captured when the file was loaded. A
    different current content hash is treated as an external edit and never
    overwritten.
    """

    csv_path = Path(path)
    if not csv_path.is_file():
        raise VocabularyCsvConflictError("CSV od načtení zmizelo nebo bylo přesunuto.")

    current_snapshot = snapshot_file(csv_path)
    if current_snapshot != expected_snapshot:
        raise VocabularyCsvConflictError(
            "CSV se od načtení změnilo v jiné aplikaci nebo na jiném zařízení."
        )

    materialized_rows = [dict(row) for row in rows]
    final_fieldnames = merged_fieldnames(fieldnames, materialized_rows)
    original_mode = csv_path.stat().st_mode & 0o777
    temp_path = _write_temp_csv(
        csv_path,
        materialized_rows,
        final_fieldnames,
        original_mode,
    )
    _validate_temp_csv(
        temp_path,
        expected_fieldnames=final_fieldnames,
        expected_rows=materialized_rows,
    )

    backup_path = None
    if create_backup:
        destination = Path(backup_dir) if backup_dir else csv_path.parent / ".backups"
        backup_path = _create_backup(csv_path, destination, current_snapshot)

    if snapshot_file(csv_path) != current_snapshot:
        raise VocabularyCsvConflictError(
            "CSV se změnilo během přípravy zápisu a nebylo přepsáno."
        )

    os.replace(temp_path, csv_path)
    try:
        directory_fd = os.open(csv_path.parent, os.O_RDONLY)
    except OSError:
        directory_fd = None
    if directory_fd is not None:
        try:
            os.fsync(directory_fd)
        except OSError:
            pass
        finally:
            os.close(directory_fd)

    return CsvSaveResult(
        snapshot=snapshot_file(csv_path),
        fieldnames=final_fieldnames,
        backup_path=backup_path,
    )
