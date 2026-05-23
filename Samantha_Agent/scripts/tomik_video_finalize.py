from __future__ import annotations

import csv
import os
import re
import shutil
import unicodedata
from pathlib import Path


ROOT = Path("data/private/tomik_rok_2")
ORIGINALS = ROOT / "01_originaly"
AUDIT = ROOT / "03_audit"
SORTED = ROOT / "04_chronologicky_pojmenovane"


def slugify(value: str, max_len: int = 58) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = ascii_value.lower()
    ascii_value = re.sub(r"[^a-z0-9]+", "_", ascii_value).strip("_")
    ascii_value = re.sub(r"_+", "_", ascii_value)
    return ascii_value[:max_len].rstrip("_") or "video"


def date_prefix(taken: str) -> str:
    match = re.match(r"(20\d{2})-(\d{2})-(\d{2})", taken)
    if not match:
        return "unknown-date"
    return "-".join(match.groups())


def load_descriptions() -> dict[str, str]:
    path = AUDIT / "video_descriptions.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        return {
            row["index"].zfill(3): row["draft_description"].strip()
            for row in csv.DictReader(handle)
        }


def link_or_copy(src: Path, dst: Path) -> str:
    if dst.exists():
        return "exists"
    try:
        os.link(src, dst)
        return "hardlink"
    except OSError:
        shutil.copy2(src, dst)
        return "copy2"


def main() -> None:
    descriptions = load_descriptions()
    SORTED.mkdir(parents=True, exist_ok=True)

    source_csv = AUDIT / "video_audit.csv"
    described_csv = AUDIT / "video_audit_described.csv"
    mapping_csv = AUDIT / "video_rename_mapping.csv"
    rows = []
    mappings = []

    with source_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        for row in reader:
            idx = row["index"].zfill(3)
            description = descriptions.get(idx, "").strip()
            base_date = date_prefix(row["taken"])
            proposed_name = f"{idx}_{base_date}_{slugify(description)}.mp4"
            row["draft_description"] = description
            row["proposed_name"] = proposed_name
            src = ORIGINALS / row["original_name"]
            dst = SORTED / proposed_name
            action = link_or_copy(src, dst)
            mappings.append(
                {
                    "index": idx,
                    "taken": row["taken"],
                    "original_name": row["original_name"],
                    "new_name": proposed_name,
                    "description": description,
                    "action": action,
                }
            )
            rows.append(row)

    with described_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with mapping_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["index", "taken", "original_name", "new_name", "description", "action"],
        )
        writer.writeheader()
        writer.writerows(mappings)

    lines = [
        "# Chronologicky pojmenovana sada",
        "",
        f"Pocet videi: {len(mappings)}",
        "",
        "Soubory v `../04_chronologicky_pojmenovane/` jsou serazene podle indexu a data.",
        "Nazvy jsou pracovni popisy podle nahledu. Originaly zustaly v `../01_originaly/`.",
        "",
        "| # | Datum | Novy nazev | Popis |",
        "|---|---|---|---|",
    ]
    for item in mappings:
        lines.append(
            f"| {item['index']} | {item['taken']} | `{item['new_name']}` | {item['description']} |"
        )
    (AUDIT / "chronologicky_katalog.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"described={described_csv}")
    print(f"mapping={mapping_csv}")
    print(f"sorted_dir={SORTED}")
    print(f"videos={len(mappings)}")


if __name__ == "__main__":
    main()
