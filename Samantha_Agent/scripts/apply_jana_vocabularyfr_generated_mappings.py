#!/usr/bin/env python3
"""Apply generated-image mappings for Jana's VocabularyFR fallback rows."""

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
DEFAULT_JANA_MAPPING = Path(
    "/Users/miloslavfalta/Library/Mobile Documents/com~apple~CloudDocs/"
    "PythonMF/Pict/mapping.json"
)
DEFAULT_LOCAL_MAPPING = Path("/Users/miloslavfalta/Desktop/PythonMF/Pict/mapping.json")
DEFAULT_JANA_PICT = Path(
    "/Users/miloslavfalta/Library/Mobile Documents/com~apple~CloudDocs/PythonMF/Pict"
)
DEFAULT_LOCAL_PICT = Path("/Users/miloslavfalta/Desktop/PythonMF/Pict")
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
    backup_path = path.with_name(f"{path.stem}.before_generated_mappings_{stamp}{path.suffix}")
    shutil.copy2(path, backup_path)
    return backup_path


def generated_additions(review_csv: Path, stems: set[str]) -> list[tuple[str, str, str]]:
    with review_csv.open("r", encoding="utf-8", newline="") as handle:
        review_rows = list(csv.DictReader(handle))

    additions: list[tuple[str, str, str]] = []
    missing: list[str] = []
    seen: dict[str, str] = {}
    conflicts: list[str] = []

    for row in review_rows:
        if row.get("Decision") != "generate":
            continue
        order = (row.get("Order") or "").strip()
        key = (row.get("FR") or "").strip()
        value = (row.get("ProposedStem") or "").strip()
        if not key or not value:
            conflicts.append(f"{order}: prazdny FR nebo ProposedStem")
            continue
        if normalize_word(value) not in stems:
            missing.append(f"{order}: {key!r} -> {value!r}")
            continue
        previous = seen.get(key)
        if previous and previous != value:
            conflicts.append(f"{order}: {key!r} ma v planu {previous!r} i {value!r}")
            continue
        if not previous:
            additions.append((order, key, value))
            seen[key] = value

    if missing or conflicts:
        if missing:
            print("Chybejici obrazky:")
            for item in missing:
                print(f"- {item}")
        if conflicts:
            print("Konflikty v planu:")
            for item in conflicts:
                print(f"- {item}")
        raise SystemExit(2)

    return additions


def apply_to_mapping(
    *,
    mapping_path: Path,
    additions: list[tuple[str, str, str]],
    apply: bool,
) -> tuple[int, int, list[str], Path | None]:
    mapping = load_mapping(mapping_path)
    add_count = 0
    same_count = 0
    conflicts: list[str] = []

    for order, key, value in additions:
        existing = mapping.get(key)
        if existing is None:
            add_count += 1
        elif existing == value:
            same_count += 1
        else:
            conflicts.append(f"{order}: {key!r} uz ma {existing!r}, nechci prepsat na {value!r}")

    if conflicts:
        return add_count, same_count, conflicts, None

    if not apply:
        return add_count, same_count, [], None

    backup_path = make_backup(mapping_path)
    updated = dict(mapping)
    for _, key, value in additions:
        updated.setdefault(key, value)
    mapping_path.write_text(
        json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return add_count, same_count, [], backup_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-csv", type=Path, default=DEFAULT_REVIEW_CSV)
    parser.add_argument("--jana-mapping", type=Path, default=DEFAULT_JANA_MAPPING)
    parser.add_argument("--local-mapping", type=Path, default=DEFAULT_LOCAL_MAPPING)
    parser.add_argument("--jana-pict", type=Path, default=DEFAULT_JANA_PICT)
    parser.add_argument("--local-pict", type=Path, default=DEFAULT_LOCAL_PICT)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    review_csv = args.review_csv.expanduser()
    jana_mapping = args.jana_mapping.expanduser()
    local_mapping = args.local_mapping.expanduser()
    jana_pict = args.jana_pict.expanduser()
    local_pict = args.local_pict.expanduser()

    for path, label in (
        (review_csv, "review CSV"),
        (jana_mapping, "Jana mapping"),
        (local_mapping, "local mapping"),
    ):
        if not path.is_file():
            raise SystemExit(f"{label} neexistuje: {path}")
    for path, label in ((jana_pict, "Jana Pict"), (local_pict, "local Pict")):
        if not path.is_dir():
            raise SystemExit(f"{label} neexistuje: {path}")

    stems = image_stems(jana_pict) & image_stems(local_pict)
    additions = generated_additions(review_csv, stems)

    print(f"Review CSV: {review_csv}")
    print(f"Generated mapping kandidatu: {len(additions)}")
    for order, key, value in additions:
        print(f"- {order}: {key} -> {value}")

    had_conflict = False
    for mapping_path, label in ((jana_mapping, "Jana"), (local_mapping, "local")):
        add_count, same_count, conflicts, backup_path = apply_to_mapping(
            mapping_path=mapping_path,
            additions=additions,
            apply=args.apply,
        )
        print("")
        print(f"{label} mapping: {mapping_path}")
        print(f"- Doplnit: {add_count}")
        print(f"- Uz existuje stejne: {same_count}")
        print(f"- Konflikty: {len(conflicts)}")
        for item in conflicts:
            print(f"  - {item}")
        if backup_path:
            print(f"- Zaloha: {backup_path}")
        if conflicts:
            had_conflict = True

    if had_conflict:
        print("Kvuli konfliktum nic nezapisuji.")
        return 2
    if not args.apply:
        print("")
        print("DRY RUN: nic jsem nezapsal.")
        return 0

    print("")
    print("Zapsano.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
