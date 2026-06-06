#!/usr/bin/env python3
"""Add missing safe mapping.json entries to Jana's shared Pict folder."""

from __future__ import annotations

import argparse
import json
import shutil
import unicodedata
import re
from datetime import datetime
from pathlib import Path


DEFAULT_SOURCE_MAPPING = Path("/Users/miloslavfalta/Desktop/PythonMF/Pict/mapping.json")
DEFAULT_TARGET_MAPPING = Path(
    "/Users/miloslavfalta/Library/Mobile Documents/com~apple~CloudDocs/"
    "PythonMF/Pict/mapping.json"
)
DEFAULT_TARGET_PICT = Path(
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


def load_json_dict(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"JSON neni objekt: {path}")
    return {str(key): str(value) for key, value in data.items()}


def target_image_stems(pict_dir: Path) -> set[str]:
    stems: set[str] = set()
    for path in pict_dir.iterdir():
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            stems.add(normalize_word(path.stem))
    return stems


def make_backup(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_name(f"{path.stem}.before_mapping_sync_{stamp}{path.suffix}")
    shutil.copy2(path, backup_path)
    return backup_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-mapping", type=Path, default=DEFAULT_SOURCE_MAPPING)
    parser.add_argument("--target-mapping", type=Path, default=DEFAULT_TARGET_MAPPING)
    parser.add_argument("--target-pict", type=Path, default=DEFAULT_TARGET_PICT)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Zapsat doplneny mapping. Bez --apply se jen vypise preview.",
    )
    args = parser.parse_args()

    source_mapping_path = args.source_mapping.expanduser()
    target_mapping_path = args.target_mapping.expanduser()
    target_pict = args.target_pict.expanduser()

    if not source_mapping_path.is_file():
        raise SystemExit(f"Zdrojovy mapping neexistuje: {source_mapping_path}")
    if not target_mapping_path.is_file():
        raise SystemExit(f"Cilovy mapping neexistuje: {target_mapping_path}")
    if not target_pict.is_dir():
        raise SystemExit(f"Cilovy Pict neexistuje: {target_pict}")

    source_mapping = load_json_dict(source_mapping_path)
    target_mapping = load_json_dict(target_mapping_path)
    image_stems = target_image_stems(target_pict)

    additions: list[tuple[str, str]] = []
    skipped_missing_image: list[tuple[str, str]] = []
    conflicts: list[tuple[str, str, str]] = []

    for key, value in source_mapping.items():
        if key in target_mapping:
            if target_mapping[key] != value:
                conflicts.append((key, target_mapping[key], value))
            continue
        if normalize_word(value) not in image_stems:
            skipped_missing_image.append((key, value))
            continue
        additions.append((key, value))

    print(f"Zdrojovy mapping: {source_mapping_path}")
    print(f"Cilovy mapping: {target_mapping_path}")
    print(f"Cilovy Pict: {target_pict}")
    print(f"Zdrojovych zaznamu: {len(source_mapping)}")
    print(f"Cilovych zaznamu pred syncem: {len(target_mapping)}")
    print(f"Jedinecnych obrazkovych stemu v cili: {len(image_stems)}")
    print(f"Doplnit lze: {len(additions)}")
    print(f"Preskoceno, obrazek v cili chybi: {len(skipped_missing_image)}")
    for key, value in skipped_missing_image:
        print(f"- CHYBI OBRAZEK {key!r} -> {value!r}")
    print(f"Konflikty existujicich klicu, neprepisuji: {len(conflicts)}")
    for key, old_value, new_value in conflicts:
        print(f"- KONFLIKT {key!r}: Jana={old_value!r}, zdroj={new_value!r}")
    print("Doplnovane zaznamy:")
    for key, value in additions:
        print(f"- {key} -> {value}")

    if not args.apply:
        print("DRY RUN: nic jsem nezapsal.")
        return 0

    backup_path = make_backup(target_mapping_path)
    updated_mapping = dict(target_mapping)
    for key, value in additions:
        updated_mapping[key] = value

    target_mapping_path.write_text(
        json.dumps(updated_mapping, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    reloaded = load_json_dict(target_mapping_path)
    if len(reloaded) != len(target_mapping) + len(additions):
        raise SystemExit(
            f"Po zapisu nesedi pocet: {len(reloaded)} != "
            f"{len(target_mapping)} + {len(additions)}"
        )

    print(f"Zaloha: {backup_path}")
    print(f"Cilovych zaznamu po syncu: {len(reloaded)}")
    print("Zapsano.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
