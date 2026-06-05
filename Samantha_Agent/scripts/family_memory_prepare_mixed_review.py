from __future__ import annotations

import argparse
import csv
from pathlib import Path

from family_memory_prepare_review import build_blocks, load_manifest, make_contact_sheet


FIELDS = [
    "item_index",
    "block_id",
    "original_taken",
    "original_name",
    "source_group",
    "relative_path",
    "media_type",
    "duration_s",
    "size_mb",
    "thumb",
    "sheet",
    "correct_day",
    "use_in_film",
    "title",
    "confidence",
    "notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare item-level review for mixed date blocks.")
    parser.add_argument("--manifest", required=True, type=Path, help="media_manifest.csv from intake.")
    parser.add_argument("--review-dir", required=True, type=Path, help="Existing review directory with thumbs.")
    parser.add_argument("--out-dir", required=True, type=Path, help="Output directory for mixed item review.")
    parser.add_argument("--block-id", action="append", required=True, help="Block id to expand. Can be repeated.")
    parser.add_argument("--gap-minutes", type=int, default=75)
    parser.add_argument("--sheet-cols", type=int, default=5)
    parser.add_argument("--sheet-rows", type=int, default=4)
    return parser.parse_args()


def thumb_for_item(review_dir: Path, item) -> str:
    safe_name = None
    for path in (review_dir / "thumbs" / item.source_group).glob(f"{item.index}_*.jpg"):
        safe_name = path
        break
    if safe_name is None:
        return ""
    return str(safe_name.relative_to(review_dir))


def main() -> None:
    args = parse_args()
    review_dir = args.review_dir
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    items = load_manifest(args.manifest)
    blocks = {block.block_id: block for block in build_blocks(items, args.gap_minutes)}
    selected = []
    for block_id in args.block_id:
        if block_id not in blocks:
            raise KeyError(f"Unknown block id: {block_id}")
        selected.extend((block_id, item) for item in blocks[block_id].items)

    thumb_map = {}
    for _, item in selected:
        thumb = thumb_for_item(review_dir, item)
        if thumb:
            thumb_map[item.index] = thumb

    rows_per_sheet = args.sheet_cols * args.sheet_rows
    csv_rows = []
    for page_no, start in enumerate(range(0, len(selected), rows_per_sheet), start=1):
        page_items = selected[start : start + rows_per_sheet]
        if not page_items:
            continue
        sheet_name = f"mixed_2019-08-05_p{page_no:02d}.jpg"
        make_contact_sheet(
            out_dir / sheet_name,
            f"2019-08-05 mixed review p{page_no:02d} | {start + 1}-{start + len(page_items)} of {len(selected)}",
            [item for _, item in page_items],
            thumb_map,
            review_dir,
            args.sheet_cols,
            args.sheet_rows,
        )
        for block_id, item in page_items:
            csv_rows.append(
                {
                    "item_index": item.index,
                    "block_id": block_id,
                    "original_taken": item.taken.strftime("%Y-%m-%d %H:%M:%S"),
                    "original_name": item.original_name,
                    "source_group": item.source_group,
                    "relative_path": item.relative_path,
                    "media_type": item.media_type,
                    "duration_s": f"{item.duration_s:.2f}" if item.duration_s is not None else "",
                    "size_mb": f"{item.size_mb:.1f}",
                    "thumb": thumb_map.get(item.index, ""),
                    "sheet": sheet_name,
                    "correct_day": "",
                    "use_in_film": "ne",
                    "title": "",
                    "confidence": "",
                    "notes": "Defaultne vyrazeno ze zpracovani, dokud neni rucne nebo vizualne spolehlive prirazeno ke spravnemu dni.",
                }
            )

    with (out_dir / "mixed_2019-08-05_review.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"items={len(csv_rows)}")
    print(out_dir / "mixed_2019-08-05_review.csv")


if __name__ == "__main__":
    main()
