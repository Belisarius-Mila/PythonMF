from __future__ import annotations

import argparse
import csv
import html
from dataclasses import dataclass
from pathlib import Path


ROOT = Path("data/private/tomik_rok_2")
AUDIT = ROOT / "03_audit"
THUMBS = ROOT / "02_nahledy"
SHORT_DIR = ROOT / "05_imovie_vyber_short"
FAMILY_DIR = ROOT / "06_imovie_vyber_family"


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
    thumbs: tuple[str, str, str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create private HTML review pages for Tomik iMovie selections.")
    parser.add_argument("--selection", choices=("short", "family", "all"), default="all")
    return parser.parse_args()


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
            thumbs = tuple(f"../02_nahledy/{stem}__{slot}.jpg" for slot in (1, 2, 3))
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
                    thumbs=thumbs,  # type: ignore[arg-type]
                )
            )
    return items


def duration_label(seconds: float) -> str:
    minutes = int(seconds // 60)
    rest = int(round(seconds % 60))
    return f"{minutes}:{rest:02d}"


def rel_video_path(selection_dir: Path, filename: str) -> str:
    return "../" + selection_dir.name + "/" + filename


def render_page(title: str, items: list[SelectionItem], selection_dir: Path, output: Path) -> None:
    total = sum(item.duration_s for item in items)
    cards: list[str] = []
    current_chapter = ""
    for item in items:
        if item.chapter != current_chapter:
            current_chapter = item.chapter
            cards.append(f"<h2>{html.escape(CHAPTER_TITLES.get(item.chapter, item.chapter))}</h2>")
        thumb_html = "\n".join(
            f'<img src="{html.escape(src)}" alt="nahled {html.escape(item.order)}">'
            for src in item.thumbs
        )
        video_href = rel_video_path(selection_dir, item.selection_file)
        cards.append(
            f"""
<article class="clip">
  <div class="clip-head">
    <strong>{html.escape(item.order)} / index {html.escape(item.index)}</strong>
    <span>{html.escape(item.taken)} | {duration_label(item.duration_s)}</span>
  </div>
  <div class="thumbs">{thumb_html}</div>
  <p>{html.escape(item.description)}</p>
  <p class="file"><a href="{html.escape(video_href)}" target="_blank" rel="noopener">{html.escape(item.selection_file)}</a></p>
</article>
""".strip()
        )

    page = f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f6f6f3;
      color: #1f2933;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 28px 18px 48px;
    }}
    h1 {{
      font-size: 28px;
      margin: 0 0 8px;
    }}
    .meta {{
      margin: 0 0 24px;
      color: #52616f;
    }}
    h2 {{
      margin: 34px 0 14px;
      padding-top: 10px;
      border-top: 1px solid #d7d9d2;
      font-size: 20px;
    }}
    .clip {{
      background: #ffffff;
      border: 1px solid #dcded8;
      border-radius: 8px;
      padding: 12px;
      margin: 12px 0;
    }}
    .clip-head {{
      display: flex;
      justify-content: space-between;
      gap: 14px;
      margin-bottom: 10px;
      color: #344150;
      font-size: 14px;
    }}
    .thumbs {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
    }}
    img {{
      width: 100%;
      height: 190px;
      object-fit: contain;
      background: #111827;
      border-radius: 6px;
    }}
    p {{
      margin: 10px 0 0;
      line-height: 1.45;
    }}
    .file {{
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 13px;
      overflow-wrap: anywhere;
    }}
    a {{
      color: #075985;
    }}
    @media (max-width: 760px) {{
      .clip-head {{
        display: block;
      }}
      .thumbs {{
        grid-template-columns: 1fr;
      }}
      img {{
        height: auto;
      }}
    }}
  </style>
</head>
<body>
<main>
  <h1>{html.escape(title)}</h1>
  <p class="meta">{len(items)} klipu | surova delka {duration_label(total)} | klik na nazev souboru otevre video</p>
  {"".join(cards)}
</main>
</body>
</html>
"""
    output.write_text(page, encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.selection in {"short", "all"}:
        short_items = load_selection(SHORT_DIR / "selection_manifest_short.csv")
        render_page("Tomik druhy rok - short review", short_items, SHORT_DIR, AUDIT / "review_short.html")
        print(f"short_review={AUDIT / 'review_short.html'}")
    if args.selection in {"family", "all"}:
        family_items = load_selection(FAMILY_DIR / "selection_manifest_family.csv")
        render_page("Tomik druhy rok - family review", family_items, FAMILY_DIR, AUDIT / "review_family.html")
        print(f"family_review={AUDIT / 'review_family.html'}")


if __name__ == "__main__":
    main()
