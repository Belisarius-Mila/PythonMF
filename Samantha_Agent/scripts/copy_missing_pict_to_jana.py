#!/usr/bin/env python3
"""Copy image files missing from Jana's shared Pict folder."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


DEFAULT_SOURCE = Path("/Users/miloslavfalta/Desktop/PythonMF/Pict")
DEFAULT_TARGET = Path(
    "/Users/miloslavfalta/Library/Mobile Documents/com~apple~CloudDocs/PythonMF/Pict"
)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def is_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS


def image_files(folder: Path) -> list[Path]:
    return sorted(path for path in folder.iterdir() if is_image(path))


def missing_images(source: Path, target: Path) -> list[Path]:
    target_names = {path.name.casefold() for path in image_files(target)}
    return [path for path in image_files(source) if path.name.casefold() not in target_names]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Zkopirovat chybejici obrazky. Bez --apply se jen vypise preview.",
    )
    args = parser.parse_args()

    source = args.source.expanduser()
    target = args.target.expanduser()
    if not source.is_dir():
        raise SystemExit(f"Zdrojovy Pict neexistuje: {source}")
    if not target.is_dir():
        raise SystemExit(f"Cilovy Pict neexistuje: {target}")

    source_images = image_files(source)
    target_images_before = image_files(target)
    missing = missing_images(source, target)

    print(f"Zdroj: {source}")
    print(f"Cil: {target}")
    print(f"Obrazku ve zdroji: {len(source_images)}")
    print(f"Obrazku v cili pred kopii: {len(target_images_before)}")
    print(f"Chybejicich obrazku: {len(missing)}")
    for path in missing:
        print(f"- {path.name}")

    if not args.apply:
        print("DRY RUN: nic jsem nekopiroval.")
        return 0

    copied = 0
    for path in missing:
        destination = target / path.name
        if destination.exists():
            print(f"PRESKAKUJI, uz existuje: {destination.name}")
            continue
        shutil.copy2(path, destination)
        copied += 1

    target_images_after = image_files(target)
    remaining = missing_images(source, target)
    print(f"Zkopirovano: {copied}")
    print(f"Obrazku v cili po kopii: {len(target_images_after)}")
    print(f"Stale chybi: {len(remaining)}")
    return 0 if not remaining else 2


if __name__ == "__main__":
    raise SystemExit(main())
