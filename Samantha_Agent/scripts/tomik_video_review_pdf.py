from __future__ import annotations

import argparse
import csv
import textwrap
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("data/private/tomik_rok_2")
AUDIT = ROOT / "03_audit"
THUMBS = ROOT / "02_nahledy"
SHORT_DIR = ROOT / "05_imovie_vyber_short"
FAMILY_DIR = ROOT / "06_imovie_vyber_family"

PAGE_W = 1754
PAGE_H = 1240
MARGIN = 54
HEADER_H = 70
CLIP_H = 258

CHAPTER_TITLES = {
    "01_jaro_2025_start": "Jaro 2025 - zacatek druheho roku",
    "02_leto_2025_venku": "Leto 2025 - venku, voda a hriste",
    "03_more_a_cesty": "Cestovani a more",
    "04_podzim_2025": "Podzim 2025 - vychazky a odrazedla",
    "05_rodina_a_vanoce": "Rodina, svetylka a Vanoce",
    "06_zima_2026": "Zima 2026 - doma a na snehu",
    "07_jaro_2026": "Jaro 2026 - hriste, vylety a hry",
    "08_narozeniny_a_finale": "Druhe narozeniny a finale",
}


@dataclass(frozen=True)
class SelectionItem:
    order: str
    index: str
    taken: str
    chapter: str
    selection_file: str
    source_file: str
    duration_s: float
    description: str
    original_name: str
    thumbs: tuple[Path, Path, Path]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create PDF review sheets for Tomik iMovie selections.")
    parser.add_argument("--selection", choices=("short", "family", "all"), default="short")
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
FONT_CHAPTER = font(26, bold=True)
FONT_TEXT = font(21)
FONT_SMALL = font(18)
FONT_MONO = font(16)


def load_mapping() -> dict[str, str]:
    mapping: dict[str, str] = {}
    with (AUDIT / "video_rename_mapping.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            mapping[row["new_name"]] = row["original_name"]
    return mapping


def load_selection(manifest_path: Path) -> list[SelectionItem]:
    mapping = load_mapping()
    items: list[SelectionItem] = []
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            original_name = mapping[row["source_file"]]
            stem = Path(original_name).stem
            items.append(
                SelectionItem(
                    order=row["order"],
                    index=row["index"],
                    taken=row["taken"],
                    chapter=row["chapter"],
                    selection_file=row["selection_file"],
                    source_file=row["source_file"],
                    duration_s=float(row["duration_s"]),
                    description=row["description"],
                    original_name=original_name,
                    thumbs=tuple(THUMBS / f"{stem}__{slot}.jpg" for slot in (1, 2, 3)),  # type: ignore[arg-type]
                )
            )
    return items


def duration_label(seconds: float) -> str:
    minutes = int(seconds // 60)
    rest = int(round(seconds % 60))
    return f"{minutes}:{rest:02d}"


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


def new_page(title: str, page_no: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    page = Image.new("RGB", (PAGE_W, PAGE_H), "#f7f7f2")
    draw = ImageDraw.Draw(page)
    draw.text((MARGIN, 34), title, fill="#1f2933", font=FONT_TITLE)
    draw.text((PAGE_W - MARGIN - 120, 44), f"str. {page_no}", fill="#52616f", font=FONT_SMALL)
    draw.line((MARGIN, HEADER_H + 28, PAGE_W - MARGIN, HEADER_H + 28), fill="#d6d8d0", width=2)
    return page, draw


def draw_clip(page: Image.Image, draw: ImageDraw.ImageDraw, item: SelectionItem, y: int) -> None:
    x = MARGIN
    draw.rounded_rectangle((x, y, PAGE_W - MARGIN, y + CLIP_H - 12), radius=10, fill="#ffffff", outline="#dcded8", width=2)
    label = f"{item.order} / index {item.index} | {item.taken} | {duration_label(item.duration_s)}"
    draw.text((x + 18, y + 16), label, fill="#334155", font=FONT_TEXT)

    thumb_w = 310
    thumb_h = 176
    thumb_y = y + 58
    for pos, thumb in enumerate(item.thumbs):
        paste_thumb(page, thumb, x + 18 + pos * (thumb_w + 10), thumb_y, thumb_w, thumb_h)

    text_x = x + 18 + 3 * (thumb_w + 10) + 22
    text_w = PAGE_W - MARGIN - text_x - 18
    lines = wrap_text(draw, item.description, FONT_TEXT, text_w)
    for line_no, line in enumerate(lines[:4]):
        draw.text((text_x, thumb_y + line_no * 30), line, fill="#1f2933", font=FONT_TEXT)
    file_lines = textwrap.wrap(item.selection_file, width=52)
    for line_no, line in enumerate(file_lines[:3]):
        draw.text((text_x, thumb_y + 126 + line_no * 22), line, fill="#475569", font=FONT_MONO)


def render_pdf(title: str, items: list[SelectionItem], output: Path) -> None:
    pages: list[Image.Image] = []
    page_no = 1
    page, draw = new_page(title, page_no)
    y = HEADER_H + 58
    current_chapter = ""

    for item in items:
        needs_chapter = item.chapter != current_chapter
        needed = CLIP_H + (44 if needs_chapter else 0)
        if y + needed > PAGE_H - MARGIN:
            pages.append(page)
            page_no += 1
            page, draw = new_page(title, page_no)
            y = HEADER_H + 58
        if needs_chapter:
            current_chapter = item.chapter
            draw.text((MARGIN, y), CHAPTER_TITLES.get(item.chapter, item.chapter), fill="#0f172a", font=FONT_CHAPTER)
            y += 44
        draw_clip(page, draw, item, y)
        y += CLIP_H

    pages.append(page)
    output.parent.mkdir(parents=True, exist_ok=True)
    first, rest = pages[0], pages[1:]
    first.save(output, save_all=True, append_images=rest, resolution=150.0)


def main() -> None:
    args = parse_args()
    if args.selection in {"short", "all"}:
        short_items = load_selection(SHORT_DIR / "selection_manifest_short.csv")
        out = AUDIT / "review_short.pdf"
        render_pdf("Tomik druhy rok - short review", short_items, out)
        print(f"short_pdf={out}")
    if args.selection in {"family", "all"}:
        family_items = load_selection(FAMILY_DIR / "selection_manifest_family.csv")
        out = AUDIT / "review_family.pdf"
        render_pdf("Tomik druhy rok - family review", family_items, out)
        print(f"family_pdf={out}")


if __name__ == "__main__":
    main()
