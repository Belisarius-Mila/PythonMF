from __future__ import annotations

import csv
import json
import math
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("data/private/tomik_rok_2")
ORIGINALS = ROOT / "01_originaly"
THUMBS = ROOT / "02_nahledy"
SHEETS = THUMBS / "contact_sheets"
AUDIT = ROOT / "03_audit"


@dataclass
class VideoInfo:
    index: int
    original_name: str
    path: Path
    taken_sort: str
    taken_display: str
    date_source: str
    duration_s: float
    size_bytes: int
    width: int | None
    height: int | None
    rotation: str
    thumbnail_files: list[str]


def run_json(command: list[str]) -> dict:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def ffprobe(path: Path) -> dict:
    return run_json(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:format_tags=creation_time:stream=width,height:stream_tags=rotate:side_data=rotation",
            "-of",
            "json",
            str(path),
        ]
    )


def parse_filename_date(name: str) -> tuple[datetime | None, str | None]:
    match = re.search(r"(20\d{6})_(\d{6})", name)
    if match:
        return datetime.strptime("".join(match.groups()), "%Y%m%d%H%M%S"), "filename_datetime"
    match = re.search(r"VID-(20\d{6})-WA(\d+)", name)
    if match:
        date_part, seq = match.groups()
        # WhatsApp names usually do not include time. Use noon plus sequence
        # seconds for stable same-day ordering without claiming a real time.
        base = datetime.strptime(date_part + "120000", "%Y%m%d%H%M%S")
        return base.replace(second=min(int(seq), 59)), "filename_date_whatsapp_sequence"
    return None, None


def parse_creation_time(probe: dict) -> datetime | None:
    value = probe.get("format", {}).get("tags", {}).get("creation_time")
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone().replace(tzinfo=None)
    except ValueError:
        return None


def best_date(path: Path, probe: dict) -> tuple[str, str, str]:
    filename_dt, filename_source = parse_filename_date(path.name)
    creation_dt = parse_creation_time(probe)
    if creation_dt is not None:
        return creation_dt.isoformat(timespec="seconds"), creation_dt.strftime("%Y-%m-%d %H:%M:%S"), "ffprobe_creation_time"
    if filename_dt is not None:
        label = filename_dt.strftime("%Y-%m-%d %H:%M:%S")
        if filename_source == "filename_date_whatsapp_sequence":
            label = filename_dt.strftime("%Y-%m-%d") + " (cas neni ve jmenu; razeno podle WA cisla)"
        return filename_dt.isoformat(timespec="seconds"), label, filename_source or "filename"
    stat_dt = datetime.fromtimestamp(path.stat().st_mtime)
    return stat_dt.isoformat(timespec="seconds"), stat_dt.strftime("%Y-%m-%d %H:%M:%S"), "file_mtime"


def stream_dimensions(probe: dict) -> tuple[int | None, int | None, str]:
    for stream in probe.get("streams", []):
        width = stream.get("width")
        height = stream.get("height")
        if width and height:
            rotation = ""
            tags = stream.get("tags", {})
            if "rotate" in tags:
                rotation = str(tags["rotate"])
            for item in stream.get("side_data_list", []) or []:
                if "rotation" in item:
                    rotation = str(item["rotation"])
            return int(width), int(height), rotation
    return None, None, ""


def extract_thumb(path: Path, duration_s: float, slot: int, fraction: float) -> str:
    safe_stem = path.stem
    out = THUMBS / f"{safe_stem}__{slot}.jpg"
    if out.exists() and out.stat().st_size > 0:
        return out.name
    ts = max(0.1, duration_s * fraction)
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{ts:.3f}",
            "-i",
            str(path),
            "-frames:v",
            "1",
            "-vf",
            "scale=320:-1",
            "-q:v",
            "3",
            str(out),
        ],
        check=True,
    )
    return out.name


def collect() -> list[VideoInfo]:
    THUMBS.mkdir(parents=True, exist_ok=True)
    SHEETS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)

    items: list[VideoInfo] = []
    for path in sorted(ORIGINALS.glob("*.mp4")):
        probe = ffprobe(path)
        duration_s = float(probe.get("format", {}).get("duration") or 0)
        width, height, rotation = stream_dimensions(probe)
        taken_sort, taken_display, date_source = best_date(path, probe)
        thumb_files = [
            extract_thumb(path, duration_s, 1, 0.20),
            extract_thumb(path, duration_s, 2, 0.50),
            extract_thumb(path, duration_s, 3, 0.80),
        ]
        items.append(
            VideoInfo(
                index=0,
                original_name=path.name,
                path=path,
                taken_sort=taken_sort,
                taken_display=taken_display,
                date_source=date_source,
                duration_s=duration_s,
                size_bytes=path.stat().st_size,
                width=width,
                height=height,
                rotation=rotation,
                thumbnail_files=thumb_files,
            )
        )

    items.sort(key=lambda item: (item.taken_sort, item.original_name))
    for idx, item in enumerate(items, 1):
        item.index = idx
    return items


def write_csv(items: list[VideoInfo]) -> None:
    out = AUDIT / "video_audit.csv"
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "index",
                "taken",
                "date_source",
                "original_name",
                "duration_s",
                "size_mb",
                "width",
                "height",
                "rotation",
                "thumb_1",
                "thumb_2",
                "thumb_3",
                "draft_description",
                "proposed_name",
            ],
        )
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "index": f"{item.index:03d}",
                    "taken": item.taken_display,
                    "date_source": item.date_source,
                    "original_name": item.original_name,
                    "duration_s": f"{item.duration_s:.2f}",
                    "size_mb": f"{item.size_bytes / 1024 / 1024:.1f}",
                    "width": item.width or "",
                    "height": item.height or "",
                    "rotation": item.rotation,
                    "thumb_1": item.thumbnail_files[0],
                    "thumb_2": item.thumbnail_files[1],
                    "thumb_3": item.thumbnail_files[2],
                    "draft_description": "",
                    "proposed_name": "",
                }
            )


def text_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
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


def make_contact_sheets(items: list[VideoInfo]) -> None:
    font_small = text_font(16)
    font_big = text_font(18)
    per_sheet = 12
    tile_w = 1000
    tile_h = 250
    margin = 24
    for sheet_no in range(math.ceil(len(items) / per_sheet)):
        chunk = items[sheet_no * per_sheet : (sheet_no + 1) * per_sheet]
        sheet = Image.new("RGB", (tile_w + margin * 2, tile_h * len(chunk) + margin * 2), "white")
        draw = ImageDraw.Draw(sheet)
        for row, item in enumerate(chunk):
            y = margin + row * tile_h
            label = f"{item.index:03d} | {item.taken_display} | {item.original_name} | {item.duration_s:.1f}s"
            draw.text((margin, y), fit_text(label, 108), fill=(0, 0, 0), font=font_big)
            x = margin
            for thumb in item.thumbnail_files:
                img = Image.open(THUMBS / thumb).convert("RGB")
                img.thumbnail((300, 180))
                sheet.paste(img, (x, y + 34))
                x += 320
            meta = f"{item.width or '?'}x{item.height or '?'} rot={item.rotation or '-'} source={item.date_source}"
            draw.text((margin, y + 218), fit_text(meta, 110), fill=(70, 70, 70), font=font_small)
        out = SHEETS / f"contact_sheet_{sheet_no + 1:02d}.jpg"
        sheet.save(out, quality=88)


def write_markdown(items: list[VideoInfo]) -> None:
    total_duration = sum(item.duration_s for item in items)
    total_size = sum(item.size_bytes for item in items)
    lines = [
        "# Tomik rok 2 - audit videi",
        "",
        f"Pocet videi: {len(items)}",
        f"Celkova velikost: {total_size / 1024 / 1024 / 1024:.2f} GB",
        f"Celkova delka: {total_duration / 60:.1f} minut",
        f"Prvni datum: {items[0].taken_display if items else ''}",
        f"Posledni datum: {items[-1].taken_display if items else ''}",
        "",
        "## Vystupy",
        "",
        "- `video_audit.csv` - strojovy katalog s metadaty a mistem pro popis.",
        "- `../02_nahledy/` - tri nahledy ke kazdemu videu.",
        "- `../02_nahledy/contact_sheets/` - kontaktni listy pro rychle prohlizeni.",
        "",
    ]
    (AUDIT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    items = collect()
    write_csv(items)
    make_contact_sheets(items)
    write_markdown(items)
    print(f"videos={len(items)}")
    print(f"audit={AUDIT / 'video_audit.csv'}")
    print(f"sheets={SHEETS}")


if __name__ == "__main__":
    main()
