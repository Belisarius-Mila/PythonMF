#!/usr/bin/env python3
"""Add the Benji word-set label to the 120 rows imported from MMTX.

The default mode is read-only. ``--apply`` atomically updates only physical CSV
rows whose normalized English word belongs to the curated MMTX import. Existing
word-set labels are preserved and CRLF line endings remain unchanged.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import os
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "VocabularyEN" / "VocabularyEN.csv"
EXPECTED_FIELDS = ("EN", "CZ", "Order", "Sentence", "SentenceT", "WS", "L", "HT")
BENJI_LABEL = "Benji"


def load_import_module():
    path = REPO_ROOT / "VocabularyEN" / "import_mmtx_vocabulary.py"
    spec = importlib.util.spec_from_file_location("import_mmtx_vocabulary", path)
    if not spec or not spec.loader:
        raise SystemExit(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_rows(path: Path = CSV_PATH) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != EXPECTED_FIELDS:
            raise SystemExit(f"Unexpected CSV header: {reader.fieldnames}")
        return list(reader)


def imported_keys(import_module) -> set[str]:
    keys = set(import_module.CURATED)
    if len(keys) != 120:
        raise SystemExit(f"Expected 120 curated MMTX keys, found {len(keys)}")
    return keys


def audit(path: Path = CSV_PATH) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    import_module = load_import_module()
    keys = imported_keys(import_module)
    rows = load_rows(path)
    targets = [row for row in rows if import_module.normalize_word(row["EN"]) in keys]
    if len(targets) != 120:
        raise SystemExit(f"Expected 120 imported MMTX rows, found {len(targets)}")
    if [int(row["Order"]) for row in targets] != list(range(187, 307)):
        raise SystemExit("Imported MMTX rows are not the expected orders 187-306")
    pending = [
        row
        for row in targets
        if BENJI_LABEL.casefold()
        not in {label.casefold() for label in import_module.merge_word_sets(row["WS"]).split("|") if label}
    ]
    return targets, pending


def build_updated_bytes(
    original: bytes,
    target_keys: set[str],
    *,
    import_module=None,
) -> tuple[bytes, list[str]]:
    module = import_module or load_import_module()
    if original.replace(b"\r\n", b"").count(b"\n"):
        raise SystemExit("VocabularyEN.csv contains non-CRLF line endings")
    lines = original.split(b"\r\n")
    if not lines or lines[-1] != b"":
        raise SystemExit("VocabularyEN.csv must end with CRLF")

    changed_words: list[str] = []
    for index in range(1, len(lines) - 1):
        text = lines[index].decode("utf-8")
        fields = next(csv.reader([text]))
        if len(fields) != len(EXPECTED_FIELDS):
            raise SystemExit(f"Unexpected field count on physical CSV line {index + 1}")
        if module.normalize_word(fields[0]) not in target_keys:
            continue
        updated_word_sets = module.merge_word_sets(fields[5], BENJI_LABEL)
        if updated_word_sets == fields[5]:
            continue
        fields[5] = updated_word_sets
        buffer = io.StringIO(newline="")
        csv.writer(buffer, lineterminator="\r\n").writerow(fields)
        encoded = buffer.getvalue().encode("utf-8")
        if not encoded.endswith(b"\r\n"):
            raise SystemExit("CSV writer did not produce CRLF")
        lines[index] = encoded[:-2]
        changed_words.append(fields[0])
    return b"\r\n".join(lines), changed_words


def apply(path: Path = CSV_PATH) -> list[str]:
    import_module = load_import_module()
    original = path.read_bytes()
    updated, changed_words = build_updated_bytes(
        original,
        imported_keys(import_module),
        import_module=import_module,
    )
    if not changed_words:
        return []
    descriptor, temporary_name = tempfile.mkstemp(
        prefix="VocabularyEN.benji.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(updated)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return changed_words


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    targets, pending = audit()
    print(f"Imported MMTX rows: {len(targets)}")
    print(f"Already tagged Benji: {len(targets) - len(pending)}")
    print(f"Rows to tag Benji: {len(pending)}")
    if not args.apply:
        print("Dry run only. VocabularyEN.csv was not changed.")
        return 0
    changed = apply()
    print(f"Applied Benji label: {len(changed)} row(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
