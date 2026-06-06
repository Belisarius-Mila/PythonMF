#!/usr/bin/env python3
"""Apply reviewed VocabularyFR fallback mappings that use existing images."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import unicodedata
from datetime import datetime
from pathlib import Path


DEFAULT_REVIEW_CSV = Path(
    "/Users/miloslavfalta/Library/Mobile Documents/com~apple~CloudDocs/"
    "PythonMF/PictNew/jana_vocabularyfr_fallback_review.csv"
)
DEFAULT_MAPPING = Path(
    "/Users/miloslavfalta/Library/Mobile Documents/com~apple~CloudDocs/"
    "PythonMF/Pict/mapping.json"
)
DEFAULT_PICT = Path(
    "/Users/miloslavfalta/Library/Mobile Documents/com~apple~CloudDocs/PythonMF/Pict"
)
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def normalize_word(text: str) -> str:
    value = (text or "").strip().casefold()
    value = "".join(
        ch
        for ch in unicodedata.normalize("NFD", value)
        if unicodedata.category(ch) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", "", value)


def load_mapping(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"mapping.json neni objekt: {path}")
    return {str(key): str(value) for key, value in data.items()}


def image_stems(pict_dir: Path) -> set[str]:
    return {
        normalize_word(path.stem)
        for path in pict_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    }


def make_backup(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_name(f"{path.stem}.before_existing_fallbacks_{stamp}{path.suffix}")
    shutil.copy2(path, backup_path)
    return backup_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-csv", type=Path, default=DEFAULT_REVIEW_CSV)
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    parser.add_argument("--pict", type=Path, default=DEFAULT_PICT)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Zapsat mapping. Bez --apply se jen vypise preview.",
    )
    args = parser.parse_args()

    review_csv = args.review_csv.expanduser()
    mapping_path = args.mapping.expanduser()
    pict_dir = args.pict.expanduser()

    if not review_csv.is_file():
        raise SystemExit(f"Review CSV neexistuje: {review_csv}")
    if not mapping_path.is_file():
        raise SystemExit(f"Mapping neexistuje: {mapping_path}")
    if not pict_dir.is_dir():
        raise SystemExit(f"Pict slozka neexistuje: {pict_dir}")

    mapping = load_mapping(mapping_path)
    stems = image_stems(pict_dir)

    with review_csv.open("r", encoding="utf-8", newline="") as handle:
        review_rows = list(csv.DictReader(handle))

    additions: list[tuple[str, str, str]] = []
    already_same: list[tuple[str, str, str]] = []
    conflicts: list[str] = []
    missing_images: list[str] = []
    seen_keys: set[str] = set()

    for row in review_rows:
        if row.get("Decision") != "use_existing":
            continue
        order = row.get("Order", "")
        key = (row.get("ProposedMappingKey") or "").strip()
        value = (row.get("ProposedStem") or "").strip()
        if not key or not value:
            conflicts.append(f"{order}: prazdny ProposedMappingKey nebo ProposedStem")
            continue
        if key in seen_keys:
            conflicts.append(f"{order}: duplicitni ProposedMappingKey v review CSV: {key!r}")
            continue
        seen_keys.add(key)
        if normalize_word(value) not in stems:
            missing_images.append(f"{order}: {key!r} -> {value!r}")
            continue

        existing = mapping.get(key)
        if existing is None:
            additions.append((order, key, value))
        elif existing == value:
            already_same.append((order, key, value))
        else:
            conflicts.append(f"{order}: {key!r} uz ma {existing!r}, nechci prepsat na {value!r}")

    print(f"Review CSV: {review_csv}")
    print(f"Mapping: {mapping_path}")
    print(f"Radku v review CSV: {len(review_rows)}")
    print(f"use_existing radku: {len(additions) + len(already_same) + len(conflicts) + len(missing_images)}")
    print(f"Doplnit: {len(additions)}")
    print(f"Uz existuje stejne: {len(already_same)}")
    print(f"Chybi obrazek: {len(missing_images)}")
    print(f"Konflikty: {len(conflicts)}")
    if missing_images:
        print("Chybejici obrazky:")
        for item in missing_images:
            print(f"- {item}")
    if conflicts:
        print("Konflikty:")
        for item in conflicts:
            print(f"- {item}")
    print("Doplnovane mappingy:")
    for order, key, value in additions:
        print(f"- {order}: {key} -> {value}")

    if conflicts or missing_images:
        print("Kvuli konfliktum/chybejicim obrazkum nic nezapisuji.")
        return 2

    if not args.apply:
        print("DRY RUN: nic jsem nezapsal.")
        return 0

    backup_path = make_backup(mapping_path)
    updated = dict(mapping)
    for _, key, value in additions:
        updated[key] = value

    mapping_path.write_text(
        json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    reloaded = load_mapping(mapping_path)
    expected_count = len(mapping) + len(additions)
    if len(reloaded) != expected_count:
        raise SystemExit(f"Po zapisu nesedi pocet: {len(reloaded)} != {expected_count}")

    print(f"Zaloha: {backup_path}")
    print(f"Zaznamu pred: {len(mapping)}")
    print(f"Zaznamu po: {len(reloaded)}")
    print("Zapsano.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
