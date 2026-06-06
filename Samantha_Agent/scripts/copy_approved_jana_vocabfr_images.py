#!/usr/bin/env python3
"""Copy approved Jana VocabularyFR generated images into both Pict folders."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


DEFAULT_SOURCE_ROOT = Path("/Users/miloslavfalta/Desktop/PythonMF/PictNew/generated")
DEFAULT_LOCAL_PICT = Path("/Users/miloslavfalta/Desktop/PythonMF/Pict")
DEFAULT_JANA_PICT = Path(
    "/Users/miloslavfalta/Library/Mobile Documents/com~apple~CloudDocs/PythonMF/Pict"
)
DEFAULT_BATCH_GLOB = "20260606_fr_jana_batch*"


def generated_images(source_root: Path, batch_glob: str) -> list[Path]:
    images: list[Path] = []
    for batch_dir in sorted(source_root.glob(batch_glob)):
        if batch_dir.is_dir():
            images.extend(sorted(batch_dir.glob("*.webp")))
    return images


def copy_images(images: list[Path], target: Path, apply: bool) -> tuple[int, int, list[str]]:
    copied = 0
    skipped = 0
    errors: list[str] = []
    for image in images:
        destination = target / image.name
        if destination.exists():
            skipped += 1
            continue
        if apply:
            shutil.copy2(image, destination)
            copied += 1
        else:
            copied += 1
    return copied, skipped, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--batch-glob", default=DEFAULT_BATCH_GLOB)
    parser.add_argument("--local-pict", type=Path, default=DEFAULT_LOCAL_PICT)
    parser.add_argument("--jana-pict", type=Path, default=DEFAULT_JANA_PICT)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    source_root = args.source_root.expanduser()
    local_pict = args.local_pict.expanduser()
    jana_pict = args.jana_pict.expanduser()

    for path, label in (
        (source_root, "source root"),
        (local_pict, "local Pict"),
        (jana_pict, "Jana Pict"),
    ):
        if not path.is_dir():
            raise SystemExit(f"{label} neexistuje: {path}")

    images = generated_images(source_root, args.batch_glob)
    names = [image.name for image in images]
    duplicate_names = sorted({name for name in names if names.count(name) > 1})
    if duplicate_names:
        raise SystemExit(f"V generovanych obrazcich jsou duplicity: {duplicate_names}")
    if len(images) != 39:
        raise SystemExit(f"Cekam 39 obrazku, nasel jsem {len(images)}")

    print(f"Zdroj: {source_root} / {args.batch_glob}")
    print(f"Nas Pict: {local_pict}")
    print(f"Jany Pict: {jana_pict}")
    print(f"Schvalenych obrazku: {len(images)}")
    for image in images:
        print(f"- {image.name}")

    local_copied, local_skipped, _ = copy_images(images, local_pict, args.apply)
    jana_copied, jana_skipped, _ = copy_images(images, jana_pict, args.apply)

    print("")
    print(f"Nas Pict - nove/kopirovat: {local_copied}, preskoceno existujici: {local_skipped}")
    print(f"Jany Pict - nove/kopirovat: {jana_copied}, preskoceno existujici: {jana_skipped}")

    if not args.apply:
        print("DRY RUN: nic jsem nekopiroval.")
        return 0

    missing_local = sorted(image.name for image in images if not (local_pict / image.name).is_file())
    missing_jana = sorted(image.name for image in images if not (jana_pict / image.name).is_file())
    print(f"Po kopii chybi v nasem Pict: {len(missing_local)}")
    print(f"Po kopii chybi v Jany Pict: {len(missing_jana)}")
    if missing_local or missing_jana:
        print(f"Missing local: {missing_local}")
        print(f"Missing Jana: {missing_jana}")
        return 2
    print("Zkopirovano a overeno.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
