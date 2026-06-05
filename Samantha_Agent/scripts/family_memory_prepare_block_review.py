from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


FIELDS = [
    "block_id",
    "original_day",
    "correct_day",
    "time_range",
    "files",
    "photos",
    "videos",
    "size_gb",
    "sources",
    "sheet",
    "day_ok",
    "day_priority",
    "use_in_film",
    "title",
    "notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare block-level review CSV from day review and block sheets.")
    parser.add_argument("--blocks", required=True, type=Path, help="Existing blocks.csv from review prep.")
    parser.add_argument("--days", required=True, type=Path, help="Reviewed day_review.csv.")
    parser.add_argument("--out", required=True, type=Path, help="Output block_review.csv.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output.")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def normalized_date_from_note(note: str) -> str:
    match = re.search(r"pat[řr]í\s+(?:k|v?e?|vk)?\s*datumu:?\s*(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?", note, re.IGNORECASE)
    if not match:
        return ""
    day = int(match.group(1))
    month = int(match.group(2))
    year = int(match.group(3) or "2019")
    return f"{year:04d}-{month:02d}-{day:02d}"


def use_value(day: dict[str, str], corrected_day: str) -> str:
    priority = day.get("priority", "").strip()
    ok = day.get("ok", "").strip()
    title = day.get("title", "").strip().lower()
    if priority == "C" or title == "vyřadit":
        return "ne"
    if "roztřídit" in title or "smes" in day.get("notes", "").lower() or "směs" in day.get("notes", "").lower():
        return "roztřídit"
    if ok == "ne" and corrected_day:
        return "ano"
    if priority == "A":
        return "ano"
    if priority == "B":
        return "možná"
    return ""


def main() -> None:
    args = parse_args()
    if args.out.exists() and not args.overwrite:
        raise FileExistsError(f"{args.out} exists; use --overwrite to replace it")

    days_by_day = {row["day"]: row for row in read_csv(args.days)}
    block_rows = read_csv(args.blocks)
    output: list[dict[str, str]] = []

    for block in block_rows:
        original_day = block["day"]
        day = days_by_day.get(original_day, {})
        day_note = day.get("notes", "").strip()
        corrected_day = normalized_date_from_note(day_note)
        if not corrected_day and day.get("ok", "").strip() == "ano":
            corrected_day = original_day

        title = day.get("title", "").strip()
        if block["files"] == "1":
            block_label = title
        else:
            block_label = f"{title} {block['first_taken'][11:16]}-{block['last_taken'][11:16]}".strip()

        note_parts = []
        if day_note:
            note_parts.append(f"Den: {day_note}")
        if day.get("ok", "").strip() == "ne" and corrected_day:
            note_parts.append(f"Původní datum v souboru je {original_day}; ručně určené správné datum je {corrected_day}.")
        if day.get("ok", "").strip() == "ne" and not corrected_day:
            note_parts.append("Datum/blok ručně označený k vyřazení nebo roztřídění.")

        output.append(
            {
                "block_id": block["block_id"],
                "original_day": original_day,
                "correct_day": corrected_day,
                "time_range": f"{block['first_taken'][11:16]}-{block['last_taken'][11:16]}",
                "files": block["files"],
                "photos": block["photos"],
                "videos": block["videos"],
                "size_gb": block["size_gb"],
                "sources": block["sources"],
                "sheet": block["contact_sheet"],
                "day_ok": day.get("ok", ""),
                "day_priority": day.get("priority", ""),
                "use_in_film": use_value(day, corrected_day),
                "title": block_label,
                "notes": " ".join(note_parts),
            }
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(output)

    print(f"blocks={len(output)}")
    print(args.out)


if __name__ == "__main__":
    main()
