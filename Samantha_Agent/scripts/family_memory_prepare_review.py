from __future__ import annotations

import argparse
import csv
import hashlib
import math
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


@dataclass(frozen=True)
class ManifestItem:
    index: str
    media_type: str
    source_group: str
    taken: datetime
    date_source: str
    relative_path: str
    original_name: str
    extension: str
    size_mb: float
    width: str
    height: str
    duration_s: float | None
    has_gps: str
    file_mtime: str


@dataclass(frozen=True)
class Block:
    block_id: str
    day: str
    items: list[ManifestItem]


@dataclass(frozen=True)
class ThumbnailError:
    item: ManifestItem
    source_path: Path
    error: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare thumbnails, time blocks, and contact sheets for a memory film project.")
    parser.add_argument("--source", required=True, type=Path, help="Read-only source media root.")
    parser.add_argument("--manifest", required=True, type=Path, help="media_manifest.csv from family_memory_intake.py.")
    parser.add_argument("--out", required=True, type=Path, help="Private review output directory.")
    parser.add_argument("--gap-minutes", type=int, default=75, help="Start a new block after this time gap within a day.")
    parser.add_argument("--thumb-size", type=int, default=360, help="Max thumbnail width/height.")
    parser.add_argument("--sheet-cols", type=int, default=5)
    parser.add_argument("--sheet-rows", type=int, default=4)
    parser.add_argument("--force-thumbs", action="store_true", help="Regenerate review thumbnails even when output files already exist.")
    return parser.parse_args()


def parse_taken(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def load_manifest(path: Path) -> list[ManifestItem]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    items: list[ManifestItem] = []
    for row in rows:
        raw_duration = row.get("duration_s", "").strip()
        items.append(
            ManifestItem(
                index=row["index"].strip(),
                media_type=row["media_type"].strip(),
                source_group=row["source_group"].strip(),
                taken=parse_taken(row["taken"].strip()),
                date_source=row["date_source"].strip(),
                relative_path=row["relative_path"].strip(),
                original_name=row["original_name"].strip(),
                extension=row["extension"].strip(),
                size_mb=float(row.get("size_mb", "0") or 0),
                width=row.get("width", "").strip(),
                height=row.get("height", "").strip(),
                duration_s=float(raw_duration) if raw_duration else None,
                has_gps=row.get("has_gps", "").strip(),
                file_mtime=row.get("file_mtime", "").strip(),
            )
        )
    return sorted(items, key=lambda item: (item.taken, item.relative_path))


def safe_stem(item: ManifestItem) -> str:
    digest = hashlib.sha1(item.relative_path.encode("utf-8")).hexdigest()[:10]
    return f"{item.index}_{Path(item.original_name).stem}_{digest}"


def make_photo_thumb(source_path: Path, target: Path, max_size: int) -> None:
    if target.exists() and target.stat().st_size > 0:
        return
    with Image.open(source_path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail((max_size, max_size))
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(target, quality=86, optimize=True)


def make_video_thumb(source_path: Path, target: Path, duration_s: float | None, max_size: int) -> None:
    if target.exists() and target.stat().st_size > 0:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if duration_s and duration_s > 1:
        seek = min(max(duration_s * 0.2, 0.5), max(duration_s - 0.2, 0.5))
    else:
        seek = 0.5
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{seek:.3f}",
            "-i",
            str(source_path),
            "-frames:v",
            "1",
            "-vf",
            f"scale='min({max_size},iw)':-1",
            "-q:v",
            "4",
            str(target),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    if not target.exists() or target.stat().st_size == 0:
        raise RuntimeError("ffmpeg finished without creating a thumbnail")


def make_placeholder_thumb(target: Path, max_size: int, title: str, subtitle: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (max_size, max_size), (245, 245, 245))
    draw = ImageDraw.Draw(image)
    font_title = text_font(24, True)
    font_small = text_font(16)
    draw.rectangle((0, 0, max_size - 1, max_size - 1), outline=(170, 170, 170), width=3)
    draw.text((24, 32), title, fill=(120, 0, 0), font=font_title)
    y = 82
    for line in [subtitle[i : i + 34] for i in range(0, len(subtitle), 34)][:7]:
        draw.text((24, y), line, fill=(55, 55, 55), font=font_small)
        y += 24
    image.save(target, quality=86, optimize=True)


def make_thumbnails(source: Path, out: Path, items: list[ManifestItem], max_size: int, force: bool = False) -> tuple[dict[str, str], list[ThumbnailError]]:
    thumbs_dir = out / "thumbs"
    thumb_map: dict[str, str] = {}
    errors: list[ThumbnailError] = []
    for item in items:
        rel = Path(item.relative_path)
        source_path = source / rel
        target = thumbs_dir / item.source_group / f"{safe_stem(item)}.jpg"
        if force and target.exists():
            target.unlink()
        try:
            if item.media_type == "photo":
                make_photo_thumb(source_path, target, max_size)
            else:
                make_video_thumb(source_path, target, item.duration_s, max_size)
        except Exception as exc:
            error_text = str(exc).replace("\n", " ").strip()
            if isinstance(exc, subprocess.CalledProcessError):
                details = (exc.stderr or exc.stdout or "").replace("\n", " ").strip()
                error_text = f"ffmpeg exit {exc.returncode}: {details or error_text}"
            make_placeholder_thumb(target, max_size, f"{item.media_type.upper()} ERROR", item.original_name)
            errors.append(ThumbnailError(item=item, source_path=source_path, error=error_text))
        thumb_map[item.index] = str(target.relative_to(out))
    return thumb_map, errors


def write_thumbnail_errors(out: Path, errors: list[ThumbnailError]) -> None:
    error_path = out / "thumbnail_errors.csv"
    with error_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["index", "media_type", "taken", "source_group", "relative_path", "source_path", "error"])
        for error in errors:
            item = error.item
            writer.writerow(
                [
                    item.index,
                    item.media_type,
                    item.taken.strftime("%Y-%m-%d %H:%M:%S"),
                    item.source_group,
                    item.relative_path,
                    str(error.source_path),
                    error.error,
                ]
            )


def build_blocks(items: list[ManifestItem], gap_minutes: int) -> list[Block]:
    blocks: list[Block] = []
    current: list[ManifestItem] = []
    current_day = ""
    block_no_by_day: dict[str, int] = {}
    gap_seconds = gap_minutes * 60

    for item in items:
        day = item.taken.strftime("%Y-%m-%d")
        starts_new = False
        if not current:
            starts_new = True
        elif day != current_day:
            starts_new = True
        elif (item.taken - current[-1].taken).total_seconds() > gap_seconds:
            starts_new = True

        if starts_new and current:
            block_no = block_no_by_day[current_day]
            blocks.append(Block(f"{current_day}_B{block_no:02d}", current_day, current))
            current = []

        if starts_new:
            current_day = day
            block_no_by_day[day] = block_no_by_day.get(day, 0) + 1

        current.append(item)

    if current:
        block_no = block_no_by_day[current_day]
        blocks.append(Block(f"{current_day}_B{block_no:02d}", current_day, current))
    return blocks


def text_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


def fit_text(text: str, max_chars: int) -> str:
    return text if len(text) <= max_chars else text[: max_chars - 1] + "..."


def make_contact_sheet(
    out_path: Path,
    title: str,
    items: list[ManifestItem],
    thumb_map: dict[str, str],
    review_out: Path,
    cols: int,
    rows: int,
) -> None:
    if not items:
        return
    tile_w = 260
    tile_h = 230
    margin = 24
    header_h = 70
    width = cols * tile_w + margin * 2
    height = rows * tile_h + margin * 2 + header_h
    sheet = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(sheet)
    font_title = text_font(24, True)
    font_small = text_font(14)
    draw.text((margin, margin), title, fill=(0, 0, 0), font=font_title)
    for idx, item in enumerate(items[: cols * rows]):
        col = idx % cols
        row = idx // cols
        x = margin + col * tile_w
        y = margin + header_h + row * tile_h
        thumb_path = review_out / thumb_map[item.index]
        try:
            thumb = Image.open(thumb_path).convert("RGB")
        except OSError:
            continue
        thumb.thumbnail((tile_w - 20, 155))
        sheet.paste(thumb, (x + 10, y + 4))
        label = f"{item.index} {item.media_type} {item.taken.strftime('%H:%M')}"
        draw.text((x + 10, y + 162), fit_text(label, 28), fill=(0, 0, 0), font=font_small)
        draw.text((x + 10, y + 182), fit_text(item.original_name, 30), fill=(70, 70, 70), font=font_small)
        draw.text((x + 10, y + 202), fit_text(item.source_group, 30), fill=(100, 100, 100), font=font_small)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=88)


def representative_items(items: list[ManifestItem], limit: int) -> list[ManifestItem]:
    if len(items) <= limit:
        return items
    step = len(items) / limit
    return [items[min(math.floor(idx * step), len(items) - 1)] for idx in range(limit)]


def write_blocks(out: Path, blocks: list[Block], thumb_map: dict[str, str], cols: int, rows: int) -> None:
    with (out / "blocks.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "block_id",
                "day",
                "files",
                "photos",
                "videos",
                "size_gb",
                "first_taken",
                "last_taken",
                "sources",
                "contact_sheet",
                "working_title",
                "notes",
            ]
        )
        for block in blocks:
            size_gb = sum(item.size_mb for item in block.items) / 1024
            sources = ",".join(sorted({item.source_group for item in block.items}))
            sheet_name = f"{block.block_id}.jpg"
            writer.writerow(
                [
                    block.block_id,
                    block.day,
                    len(block.items),
                    sum(1 for item in block.items if item.media_type == "photo"),
                    sum(1 for item in block.items if item.media_type == "video"),
                    f"{size_gb:.2f}",
                    block.items[0].taken.strftime("%Y-%m-%d %H:%M:%S"),
                    block.items[-1].taken.strftime("%Y-%m-%d %H:%M:%S"),
                    sources,
                    f"contact_sheets/blocks/{sheet_name}",
                    "",
                    "",
                ]
            )
            reps = representative_items(block.items, cols * rows)
            make_contact_sheet(
                out / "contact_sheets" / "blocks" / sheet_name,
                f"{block.block_id} | {len(block.items)} files | {block.items[0].taken:%H:%M}-{block.items[-1].taken:%H:%M}",
                reps,
                thumb_map,
                out,
                cols,
                rows,
            )


def write_day_sheets(out: Path, items: list[ManifestItem], thumb_map: dict[str, str], cols: int, rows: int) -> None:
    by_day: dict[str, list[ManifestItem]] = {}
    for item in items:
        by_day.setdefault(item.taken.strftime("%Y-%m-%d"), []).append(item)
    for day, day_items in sorted(by_day.items()):
        reps = representative_items(day_items, cols * rows)
        make_contact_sheet(
            out / "contact_sheets" / "days" / f"{day}.jpg",
            f"{day} | {len(day_items)} files",
            reps,
            thumb_map,
            out,
            cols,
            rows,
        )


def write_readme(out: Path, blocks: list[Block], items: list[ManifestItem], gap_minutes: int, thumbnail_errors: list[ThumbnailError]) -> None:
    largest_blocks = sorted(blocks, key=lambda block: len(block.items), reverse=True)[:10]
    text = f"""# USA 2019 - review prep

## Vytvoreno

- Nahledy: `thumbs/`
- Bloky podle dne a casove mezery {gap_minutes} minut: `blocks.csv`
- Kontaktni listy bloku: `contact_sheets/blocks/`
- Kontaktni listy dni: `contact_sheets/days/`
- Chyby pri tvorbe nahledu: `thumbnail_errors.csv`

## Souhrn

- Medialnich souboru: {len(items)}
- Bloku: {len(blocks)}
- Fotky: {sum(1 for item in items if item.media_type == "photo")}
- Videa: {sum(1 for item in items if item.media_type == "video")}
- Problemove nahledy: {len(thumbnail_errors)}

## Nejvetsi bloky podle poctu souboru

"""
    for block in largest_blocks:
        text += (
            f"- `{block.block_id}`: {len(block.items)} souboru, "
            f"{sum(1 for item in block.items if item.media_type == 'photo')} fotek, "
            f"{sum(1 for item in block.items if item.media_type == 'video')} videi, "
            f"{block.items[0].taken:%H:%M}-{block.items[-1].taken:%H:%M}\n"
        )
    text += "\n## Bezpecnost\n\n"
    text += "- Skript nemaze, neprejmenovava a nepresouva originaly.\n"
    text += "- Vystupy patri do `data/private/` a nepatri do gitu.\n"
    (out / "README_REVIEW.md").write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    source = args.source.expanduser().resolve()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    items = load_manifest(args.manifest)
    thumb_map, thumbnail_errors = make_thumbnails(source, out, items, args.thumb_size, force=args.force_thumbs)
    write_thumbnail_errors(out, thumbnail_errors)
    blocks = build_blocks(items, args.gap_minutes)
    write_blocks(out, blocks, thumb_map, args.sheet_cols, args.sheet_rows)
    write_day_sheets(out, items, thumb_map, args.sheet_cols, args.sheet_rows)
    write_readme(out, blocks, items, args.gap_minutes, thumbnail_errors)
    print(f"items={len(items)}")
    print(f"blocks={len(blocks)}")
    print(f"thumbnail_errors={len(thumbnail_errors)}")
    print(out / "blocks.csv")
    print(out / "README_REVIEW.md")


if __name__ == "__main__":
    main()
