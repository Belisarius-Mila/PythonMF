from __future__ import annotations

import argparse
import csv
import math
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("data/private/tomik_rok_2")
AUDIT = ROOT / "03_audit"
THUMBS = ROOT / "02_nahledy"
SOURCE = AUDIT / "video_audit_described.csv"
SHORT_MANIFEST = ROOT / "05_imovie_vyber_short" / "selection_manifest_short.csv"
FAMILY_MANIFEST = ROOT / "06_imovie_vyber_family" / "selection_manifest_family.csv"

PAGE_W = 1754
PAGE_H = 1240
MARGIN = 54
HEADER_H = 72
CLIP_H = 252


@dataclass(frozen=True)
class ReviewItem:
    index: str
    date: str
    title: str
    description: str
    duration: str
    original_name: str
    in_short: bool
    in_family: bool
    thumbs: tuple[Path, Path, Path]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create split PDF review catalogs for all Tomik videos.")
    parser.add_argument("--parts", type=int, default=2, help="How many PDF parts to create.")
    return parser.parse_args()


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
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


FONT_TITLE = font(34, bold=True)
FONT_SUBTITLE = font(18)
FONT_TEXT = font(21)
FONT_SMALL = font(18)
FONT_MONO = font(16)


def clean_date(value: str) -> str:
    match = re.match(r"(\d{4}-\d{2}-\d{2})", value)
    if match:
        return match.group(1)
    return value[:10]


def clean_title(value: str) -> str:
    name = Path(value).stem
    name = re.sub(r"^\d{3}_\d{4}-\d{2}-\d{2}_", "", name)
    return name.replace("_", " ")


def duration_label(value: str) -> str:
    try:
        total = int(round(float(value)))
    except ValueError:
        return ""
    minutes, seconds = divmod(total, 60)
    if minutes:
        return f"{minutes}m {seconds:02d}s"
    return f"{seconds}s"


def load_selection_indexes(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["index"] for row in csv.DictReader(handle)}


def load_items() -> list[ReviewItem]:
    short_indexes = load_selection_indexes(SHORT_MANIFEST)
    family_indexes = load_selection_indexes(FAMILY_MANIFEST)
    items: list[ReviewItem] = []
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            items.append(
                ReviewItem(
                    index=row["index"],
                    date=clean_date(row["taken"]),
                    title=clean_title(row["proposed_name"]),
                    description=row["draft_description"].strip(),
                    duration=duration_label(row["duration_s"]),
                    original_name=row["original_name"],
                    in_short=row["index"] in short_indexes,
                    in_family=row["index"] in family_indexes,
                    thumbs=tuple(THUMBS / row[f"thumb_{slot}"] for slot in (1, 2, 3)),  # type: ignore[arg-type]
                )
            )
    return items


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font_obj: ImageFont.ImageFont, width_px: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font_obj) <= width_px:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def paste_thumb(page: Image.Image, thumb_path: Path, x: int, y: int, w: int, h: int) -> None:
    img = Image.open(thumb_path).convert("RGB")
    img.thumbnail((w, h))
    bg = Image.new("RGB", (w, h), "#111827")
    px = (w - img.width) // 2
    py = (h - img.height) // 2
    bg.paste(img, (px, py))
    page.paste(bg, (x, y))


def selection_label(item: ReviewItem) -> str:
    flags: list[str] = []
    if item.in_short:
        flags.append("VideoShort: ano")
    if item.in_family:
        flags.append("VideoFamily: ano")
    return " | ".join(flags) if flags else "Mimo vybery"


def new_page(title: str, subtitle: str, page_no: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    page = Image.new("RGB", (PAGE_W, PAGE_H), "#f7f7f2")
    draw = ImageDraw.Draw(page)
    draw.text((MARGIN, 30), title, fill="#1f2933", font=FONT_TITLE)
    draw.text((MARGIN, 70), subtitle, fill="#52616f", font=FONT_SUBTITLE)
    draw.text((PAGE_W - MARGIN - 120, 44), f"str. {page_no}", fill="#52616f", font=FONT_SMALL)
    draw.line((MARGIN, HEADER_H + 28, PAGE_W - MARGIN, HEADER_H + 28), fill="#d6d8d0", width=2)
    return page, draw


def draw_clip(page: Image.Image, draw: ImageDraw.ImageDraw, item: ReviewItem, y: int) -> None:
    x = MARGIN
    draw.rounded_rectangle((x, y, PAGE_W - MARGIN, y + CLIP_H - 12), radius=10, fill="#ffffff", outline="#dcded8", width=2)
    label = f"{item.index} | {item.date} | {item.duration} | {selection_label(item)}"
    draw.text((x + 18, y + 14), label, fill="#334155", font=FONT_TEXT)

    thumb_w = 300
    thumb_h = 170
    thumb_y = y + 56
    for pos, thumb in enumerate(item.thumbs):
        paste_thumb(page, thumb, x + 18 + pos * (thumb_w + 10), thumb_y, thumb_w, thumb_h)

    text_x = x + 18 + 3 * (thumb_w + 10) + 22
    text_w = PAGE_W - MARGIN - text_x - 18
    draw.text((text_x, thumb_y), item.title, fill="#111827", font=FONT_TEXT)
    for line_no, line in enumerate(wrap_text(draw, item.description, FONT_TEXT, text_w)[:3]):
        draw.text((text_x, thumb_y + 34 + line_no * 29), line, fill="#1f2933", font=FONT_TEXT)

    file_lines = textwrap.wrap(item.original_name, width=54)
    for line_no, line in enumerate(file_lines[:2]):
        draw.text((text_x, thumb_y + 128 + line_no * 22), line, fill="#475569", font=FONT_MONO)


def render_part(items: list[ReviewItem], output: Path, part_no: int, total_parts: int, start_index: int, total_items: int) -> None:
    pages: list[Image.Image] = []
    page_no = 1
    title = f"Tomik druhy rok - obrazovy katalog {part_no}/{total_parts}"
    end_index = start_index + len(items) - 1
    subtitle = f"Videa {start_index:03d}-{end_index:03d} z {total_items} | bezpecny nahled, 3 fotky na video"
    page, draw = new_page(title, subtitle, page_no)
    y = HEADER_H + 58

    for item in items:
        if y + CLIP_H > PAGE_H - MARGIN:
            pages.append(page)
            page_no += 1
            page, draw = new_page(title, subtitle, page_no)
            y = HEADER_H + 58
        draw_clip(page, draw, item, y)
        y += CLIP_H

    pages.append(page)
    output.parent.mkdir(parents=True, exist_ok=True)
    first, rest = pages[0], pages[1:]
    first.save(output, "PDF", save_all=True, append_images=rest, resolution=150.0)


def main() -> None:
    args = parse_args()
    items = load_items()
    part_count = max(2, args.parts)
    per_part = math.ceil(len(items) / part_count)
    for idx in range(part_count):
        start = idx * per_part
        part_items = items[start : start + per_part]
        if not part_items:
            continue
        output = AUDIT / f"video_review_all_part{idx + 1}_of_{part_count}.pdf"
        render_part(part_items, output, idx + 1, part_count, start + 1, len(items))
        print(output)


if __name__ == "__main__":
    main()
