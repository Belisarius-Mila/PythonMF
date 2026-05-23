from __future__ import annotations

import argparse
import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("data/private/tomik_rok_2")
AUDIT = ROOT / "03_audit"
SOURCE = AUDIT / "video_audit_described.csv"
SHORT_MANIFEST = ROOT / "05_imovie_vyber_short" / "selection_manifest_short.csv"
FAMILY_MANIFEST = ROOT / "06_imovie_vyber_family" / "selection_manifest_family.csv"


@dataclass(frozen=True)
class CatalogRow:
    index: str
    date: str
    title: str
    original_name: str
    description: str
    duration: str
    in_short: bool
    in_family: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a one-page PDF video catalog without thumbnails.")
    parser.add_argument("--sample", action="store_true", help="Create a one-page layout sample.")
    parser.add_argument("--limit", type=int, default=34, help="Number of rows in sample mode.")
    parser.add_argument(
        "--output",
        default="video_catalog_sample.pdf",
        help="Output filename inside data/private/tomik_rok_2/03_audit/.",
    )
    parser.add_argument("--pages", type=int, default=1, help="Minimum page count for the full catalog.")
    return parser.parse_args()


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


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


def load_rows() -> list[CatalogRow]:
    short_indexes = load_selection_indexes(SHORT_MANIFEST)
    family_indexes = load_selection_indexes(FAMILY_MANIFEST)
    rows: list[CatalogRow] = []
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                CatalogRow(
                    index=row["index"],
                    date=clean_date(row["taken"]),
                    title=clean_title(row["proposed_name"]),
                    original_name=row["original_name"],
                    description=row["draft_description"].strip(),
                    duration=duration_label(row["duration_s"]),
                    in_short=row["index"] in short_indexes,
                    in_family=row["index"] in family_indexes,
                )
            )
    return rows


def load_selection_indexes(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["index"] for row in csv.DictReader(handle)}


def fit_text(draw: ImageDraw.ImageDraw, text: str, font_obj: ImageFont.ImageFont, width: int) -> str:
    if draw.textlength(text, font=font_obj) <= width:
        return text
    ellipsis = "..."
    trimmed = text
    while trimmed and draw.textlength(trimmed + ellipsis, font=font_obj) > width:
        trimmed = trimmed[:-1]
    return trimmed.rstrip() + ellipsis if trimmed else ellipsis


def draw_row(
    draw: ImageDraw.ImageDraw,
    y: int,
    row_h: int,
    row: CatalogRow,
    columns: tuple[int, int, int, int, int, int, int, int, int],
    font_obj: ImageFont.ImageFont,
    fill: str,
) -> None:
    x_no, x_date, x_title, x_original, x_desc, x_duration, x_short, x_family, x_right = columns
    draw.rectangle((x_no, y, x_right, y + row_h), fill=fill)
    draw.line((x_no, y + row_h, x_right, y + row_h), fill="#d8dde4", width=1)
    pad = 10
    baseline = y + max(6, (row_h - font_obj.size) // 2 - 2)  # type: ignore[attr-defined]
    draw.text((x_no + pad, baseline), row.index, fill="#334155", font=font_obj)
    draw.text((x_date + pad, baseline), row.date, fill="#334155", font=font_obj)
    title = fit_text(draw, row.title, font_obj, x_original - x_title - 2 * pad)
    original_name = fit_text(draw, row.original_name, font_obj, x_desc - x_original - 2 * pad)
    desc = fit_text(draw, row.description, font_obj, x_duration - x_desc - 2 * pad)
    draw.text((x_title + pad, baseline), title, fill="#111827", font=font_obj)
    draw.text((x_original + pad, baseline), original_name, fill="#334155", font=font_obj)
    draw.text((x_desc + pad, baseline), desc, fill="#111827", font=font_obj)
    draw.text((x_duration + pad, baseline), row.duration, fill="#334155", font=font_obj)
    if row.in_short:
        draw.text((x_short + pad, baseline), "ano", fill="#334155", font=font_obj)
    if row.in_family:
        draw.text((x_family + pad, baseline), "ano", fill="#334155", font=font_obj)


def render(rows: list[CatalogRow], output: Path, sample: bool, pages_count: int = 1) -> None:
    if not sample and pages_count > 1:
        render_paginated(rows, output, pages_count)
        return

    if sample:
        width, height = 3508, 2480
        margin = 100
        title_size = 58
        meta_size = 30
        header_size = 27
        row_size = 25
        row_h = 63
    else:
        # One PDF page for all 217 rows. This is intentionally a larger
        # poster-like page so the text stays readable after adding duration.
        width, height = 7600, 10400
        margin = 150
        title_size = 78
        meta_size = 42
        header_size = 37
        row_size = 34
        row_h = 45
    page = Image.new("RGB", (width, height), "#f8fafc")
    draw = ImageDraw.Draw(page)

    title_font = font(title_size, bold=True)
    meta_font = font(meta_size)
    header_font = font(header_size, bold=True)
    row_font = font(row_size)

    title = "Tomik druhy rok - chronologicky seznam videi"
    subtitle = (
        f"Vzorek layoutu: prvnich {len(rows)} z 217 videi | bez fotek | jeden radek = datum, nazev, strucny popis"
        if sample
        else f"Celkem {len(rows)} videi | bez fotek | chronologicky"
    )
    draw.text((margin, margin - 38), title, fill="#0f172a", font=title_font)
    draw.text((margin, margin + 52), subtitle, fill="#475569", font=meta_font)

    table_top = margin + 150
    table_left = margin
    table_right = width - margin
    x_no = table_left
    x_date = x_no + (120 if sample else 170)
    x_title = x_date + (250 if sample else 360)
    x_original = x_title + (650 if sample else 1350)
    x_desc = x_original + (470 if sample else 1400)
    x_duration = table_right - (0 if sample else 680)
    if sample:
        x_duration = table_right - 520
    x_short = table_right - (330 if sample else 480)
    x_family = table_right - (160 if sample else 250)
    columns = (x_no, x_date, x_title, x_original, x_desc, x_duration, x_short, x_family, table_right)

    header_h = 54 if sample else 68
    draw.rectangle((table_left, table_top, table_right, table_top + header_h), fill="#e2e8f0")
    headers = (
        ("#", x_no),
        ("Datum", x_date),
        ("Nazev", x_title),
        ("Puvodni nazev", x_original),
        ("Strucny popis", x_desc),
        ("Trvani", x_duration),
        ("VideoShort", x_short),
        ("VideoFamily", x_family),
    )
    for label, x in headers:
        draw.text((x + 10, table_top + 12), label, fill="#0f172a", font=header_font)
    for x in (x_date, x_title, x_original, x_desc, x_duration, x_short, x_family):
        draw.line((x, table_top, x, height - margin), fill="#cbd5e1", width=2)

    y = table_top + header_h
    max_rows = min(len(rows), (height - margin - y) // row_h)
    for pos, row in enumerate(rows[:max_rows]):
        fill = "#ffffff" if pos % 2 == 0 else "#f1f5f9"
        draw_row(draw, y, row_h, row, columns, row_font, fill)
        y += row_h

    if len(rows) > max_rows:
        note = f"Do teto vzorkove stranky se vejde {max_rows} radku. Finalni PDF pouzije vetsi jednostrankovy format."
        draw.text((margin, height - 70), note, fill="#b45309", font=meta_font)

    output.parent.mkdir(parents=True, exist_ok=True)
    page.save(output, "PDF", resolution=300.0)


def render_paginated(rows: list[CatalogRow], output: Path, pages_count: int) -> None:
    pages_count = max(1, pages_count)
    rows_per_page = max(1, math.ceil(len(rows) / pages_count))

    width, height = 3508, 2480
    margin = 100
    title_font = font(58, bold=True)
    meta_font = font(30)
    header_font = font(31, bold=True)
    row_font = font(30)
    header_h = 62
    row_h = 72
    table_top = 205

    page_images: list[Image.Image] = []
    total_pages = math.ceil(len(rows) / rows_per_page)
    for page_no in range(total_pages):
        page_rows = rows[page_no * rows_per_page : (page_no + 1) * rows_per_page]
        page = Image.new("RGB", (width, height), "#f8fafc")
        draw = ImageDraw.Draw(page)

        title = "Tomik druhy rok - chronologicky seznam videi"
        subtitle = (
            f"Celkem {len(rows)} videi | bez fotek | strana {page_no + 1}/{total_pages} | "
            "datum, nazev, strucny popis, trvani"
        )
        draw.text((margin, 62), title, fill="#0f172a", font=title_font)
        draw.text((margin, 132), subtitle, fill="#475569", font=meta_font)

        table_left = margin
        table_right = width - margin
        x_no = table_left
        x_date = x_no + 120
        x_title = x_date + 250
        x_original = x_title + 730
        x_desc = x_original + 680
        x_duration = table_right - 650
        x_short = table_right - 470
        x_family = table_right - 240
        columns = (x_no, x_date, x_title, x_original, x_desc, x_duration, x_short, x_family, table_right)

        draw.rectangle((table_left, table_top, table_right, table_top + header_h), fill="#e2e8f0")
        headers = (
            ("#", x_no),
            ("Datum", x_date),
            ("Nazev", x_title),
            ("Puvodni nazev", x_original),
            ("Strucny popis", x_desc),
            ("Trvani", x_duration),
            ("VideoShort", x_short),
            ("VideoFamily", x_family),
        )
        for label, x in headers:
            draw.text((x + 10, table_top + 15), label, fill="#0f172a", font=header_font)
        for x in (x_date, x_title, x_original, x_desc, x_duration, x_short, x_family):
            draw.line((x, table_top, x, height - margin), fill="#cbd5e1", width=2)

        y = table_top + header_h
        for pos, row in enumerate(page_rows):
            fill = "#ffffff" if pos % 2 == 0 else "#f1f5f9"
            draw_row(draw, y, row_h, row, columns, row_font, fill)
            y += row_h

        page_images.append(page)

    output.parent.mkdir(parents=True, exist_ok=True)
    first, rest = page_images[0], page_images[1:]
    first.save(output, "PDF", save_all=True, append_images=rest, resolution=300.0)


def main() -> None:
    args = parse_args()
    rows = load_rows()
    if args.sample:
        rows = rows[: args.limit]
    output = AUDIT / args.output
    render(rows, output, sample=args.sample, pages_count=args.pages)
    print(output)


if __name__ == "__main__":
    main()
