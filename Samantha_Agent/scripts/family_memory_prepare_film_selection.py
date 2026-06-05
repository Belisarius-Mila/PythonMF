from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

from family_memory_prepare_review import (
    ManifestItem,
    build_blocks,
    load_manifest,
    make_contact_sheet,
    representative_items,
)


CLEAN_DAYS = [
    ("2019-07-20", "Prilet do USA", "Prilet a Los Angeles", "Prilet do USA a prvni vecer"),
    ("2019-07-21", "Los Angeles Hollywood", "Prilet a Los Angeles", "Los Angeles a Hollywood"),
    ("2019-07-22", "San Diego USS Midway", "San Diego a USS Midway", "San Diego a USS Midway"),
    ("2019-07-23", "Joshua Tree a Route 66", "Pouste, Joshua Tree a Route 66", "Joshua Tree a Route 66"),
    ("2019-07-24", "Grand Canyon National Park", "Grand Canyon", "Grand Canyon"),
    ("2019-07-25", "Monument Valley", "Monument Valley a Page/Glen Canyon", "Monument Valley"),
    ("2019-07-26", "Bryce Canyon", "Bryce, Zion, Las Vegas", "Bryce Canyon"),
    ("2019-07-27", "Zion National Park", "Bryce, Zion, Las Vegas", "Zion a Las Vegas"),
    ("2019-07-28", "Las Vegas Hoover Dam", "Bryce, Zion, Las Vegas", "Hoover Dam a Death Valley"),
    ("2019-07-29", "Death Valley National Park", "Death Valley, Mammoth Lakes, Yosemite", "Hoover Dam a Death Valley"),
    ("2019-07-30", "Mammoth Lakes / Sierra Nevada", "Death Valley, Mammoth Lakes, Yosemite", "Mammoth Lakes, Mono Lake, Sierra Nevada"),
    ("2019-07-31", "Yosemite National Park", "Death Valley, Mammoth Lakes, Yosemite", "Yosemite"),
    ("2019-08-01", "Monterey", "Monterey a San Francisco, odlet", "Monterey, Carmel, Big Sur"),
    ("2019-08-02", "San Francisco_1", "Monterey a San Francisco, odlet", "San Francisco prvni cast"),
    ("2019-08-03", "San Francisco_2 Odlet", "Monterey a San Francisco, odlet", "San Francisco druhy den a odlet"),
]


DAY_INFO = {
    day: {
        "day": day,
        "title": title,
        "short_chapter": short_chapter,
        "long_chapter": long_chapter,
    }
    for day, title, short_chapter, long_chapter in CLEAN_DAYS
}


ITEM_FIELDS = [
    "item_index",
    "correct_day",
    "day_title",
    "short_chapter",
    "long_chapter",
    "media_type",
    "taken",
    "original_name",
    "source_group",
    "relative_path",
    "duration_s",
    "size_mb",
    "thumb",
    "source_note",
    "short_pick",
    "long_pick",
    "rating",
    "role",
    "notes",
]


@dataclass(frozen=True)
class FilmItem:
    item: ManifestItem
    correct_day: str
    source_note: str
    notes: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare USA 2019 film selection CSV and HTML form.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/private/family_memory_films/usa_2019/01_intake/media_manifest.csv"),
    )
    parser.add_argument(
        "--review-dir",
        type=Path,
        default=Path("data/private/family_memory_films/usa_2019/02_review"),
    )
    parser.add_argument(
        "--block-review",
        type=Path,
        default=Path("data/private/family_memory_films/usa_2019/02_review/block_review.csv"),
    )
    parser.add_argument(
        "--mixed-review",
        type=Path,
        default=Path("data/private/family_memory_films/usa_2019/02_review/mixed_2019_08_05/mixed_2019-08-05_review.csv"),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/private/family_memory_films/usa_2019/03_overview"),
    )
    parser.add_argument("--gap-minutes", type=int, default=75)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def thumb_for_item(review_dir: Path, item: ManifestItem) -> str:
    candidates = sorted((review_dir / "thumbs" / item.source_group).glob(f"{item.index}_*.jpg"))
    if not candidates:
        return ""
    preferred = [path for path in candidates if not path.name.endswith(" 2.jpg")]
    return str((preferred[0] if preferred else candidates[0]).relative_to(review_dir))


def collect_film_items(
    manifest_items: list[ManifestItem],
    block_review_path: Path,
    mixed_review_path: Path,
    gap_minutes: int,
) -> list[FilmItem]:
    clean_days = set(DAY_INFO)
    by_index = {item.index: item for item in manifest_items}
    blocks = {block.block_id: block for block in build_blocks(manifest_items, gap_minutes)}
    selected: dict[str, FilmItem] = {}

    for row in read_csv(block_review_path):
        correct_day = row.get("correct_day", "").strip()
        use_in_film = row.get("use_in_film", "").strip().lower()
        block_id = row.get("block_id", "").strip()
        if correct_day not in clean_days:
            continue
        if use_in_film in {"ne", "roztřídit", "roztridit"}:
            continue
        block = blocks.get(block_id)
        if not block:
            continue
        for item in block.items:
            selected[item.index] = FilmItem(item=item, correct_day=correct_day, source_note=block_id)

    if mixed_review_path.exists():
        for row in read_csv(mixed_review_path):
            correct_day = row.get("correct_day", "").strip()
            use_in_film = row.get("use_in_film", "").strip().lower()
            item = by_index.get(row.get("item_index", "").strip())
            if not item or correct_day not in clean_days or use_in_film != "ano":
                continue
            selected[item.index] = FilmItem(
                item=item,
                correct_day=correct_day,
                source_note=f"mixed:{row.get('block_id', '').strip()}",
                notes=row.get("title", "").strip(),
            )

    return sorted(selected.values(), key=lambda film_item: (film_item.correct_day, film_item.item.taken, film_item.item.index))


def default_pick(correct_day: str, media_type: str) -> tuple[str, str, str]:
    scenic_days = {
        "2019-07-24",
        "2019-07-25",
        "2019-07-26",
        "2019-07-27",
        "2019-07-29",
        "2019-07-30",
        "2019-07-31",
        "2019-08-01",
        "2019-08-02",
    }
    short_pick = "mozna" if correct_day in scenic_days else ""
    long_pick = "mozna"
    rating = ""
    if media_type == "photo" and correct_day in scenic_days:
        rating = "B"
    return short_pick, long_pick, rating


def write_items_csv(path: Path, review_dir: Path, film_items: list[FilmItem]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ITEM_FIELDS)
        writer.writeheader()
        for film_item in film_items:
            item = film_item.item
            day = DAY_INFO[film_item.correct_day]
            short_pick, long_pick, rating = default_pick(film_item.correct_day, item.media_type)
            writer.writerow(
                {
                    "item_index": item.index,
                    "correct_day": film_item.correct_day,
                    "day_title": day["title"],
                    "short_chapter": day["short_chapter"],
                    "long_chapter": day["long_chapter"],
                    "media_type": item.media_type,
                    "taken": item.taken.strftime("%Y-%m-%d %H:%M:%S"),
                    "original_name": item.original_name,
                    "source_group": item.source_group,
                    "relative_path": item.relative_path,
                    "duration_s": f"{item.duration_s:.2f}" if item.duration_s is not None else "",
                    "size_mb": f"{item.size_mb:.1f}",
                    "thumb": thumb_for_item(review_dir, item),
                    "source_note": film_item.source_note,
                    "short_pick": short_pick,
                    "long_pick": long_pick,
                    "rating": rating,
                    "role": "",
                    "notes": film_item.notes,
                }
            )


def write_day_sheets(out_dir: Path, review_dir: Path, film_items: list[FilmItem]) -> dict[str, dict[str, str]]:
    sheets_dir = out_dir / "film_day_sheets"
    sheets_dir.mkdir(parents=True, exist_ok=True)
    by_day: dict[str, list[FilmItem]] = {}
    for film_item in film_items:
        by_day.setdefault(film_item.correct_day, []).append(film_item)

    result: dict[str, dict[str, str]] = {}
    for day, day_items in by_day.items():
        result[day] = {}
        for media_type in ("photo", "video"):
            media_items = [film_item.item for film_item in day_items if film_item.item.media_type == media_type]
            if not media_items:
                continue
            sheet_path = sheets_dir / f"{day}_{media_type}s.jpg"
            thumb_map = {item.index: thumb_for_item(review_dir, item) for item in media_items}
            make_contact_sheet(
                sheet_path,
                f"{day} {DAY_INFO[day]['title']} | {media_type}s | {len(media_items)} items",
                representative_items(media_items, 20),
                thumb_map,
                review_dir,
                cols=5,
                rows=4,
            )
            result[day][f"{media_type}_sheet"] = str(sheet_path.relative_to(out_dir))
    return result


def day_summaries(film_items: list[FilmItem], sheets: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    summaries = []
    for day, title, short_chapter, long_chapter in CLEAN_DAYS:
        items = [film_item.item for film_item in film_items if film_item.correct_day == day]
        videos = [item for item in items if item.media_type == "video"]
        photos = [item for item in items if item.media_type == "photo"]
        summaries.append(
            {
                "day": day,
                "title": title,
                "short_chapter": short_chapter,
                "long_chapter": long_chapter,
                "photos": len(photos),
                "videos": len(videos),
                "video_min": round(sum(item.duration_s or 0 for item in videos) / 60, 1),
                **sheets.get(day, {}),
            }
        )
    return summaries


def write_html(path: Path, summaries: list[dict[str, object]]) -> None:
    summaries_json = json.dumps(summaries, ensure_ascii=False, indent=2)
    headers_json = json.dumps(ITEM_FIELDS, ensure_ascii=False)
    html = f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>USA 2019 - predstrihovy vyber</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f7f4;
      --panel: #fff;
      --line: #d8d6ce;
      --text: #1f2933;
      --muted: #667085;
      --accent: #0f766e;
      --accent-2: #334155;
      --focus: #99f6e4;
      --skip: #fff1f2;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 15px;
    }}
    header {{
      position: sticky;
      top: 0;
      z-index: 3;
      display: grid;
      gap: 10px;
      padding: 14px 18px;
      background: rgba(255, 255, 255, 0.96);
      border-bottom: 1px solid var(--line);
      backdrop-filter: blur(12px);
    }}
    h1 {{ margin: 0; font-size: 20px; }}
    .toolbar, .summary-links, .autosave-actions, .player-actions {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }}
    button, select, input, textarea {{ font: inherit; }}
    button {{
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--text);
      border-radius: 6px;
      padding: 8px 11px;
      cursor: pointer;
    }}
    button.primary {{ background: var(--accent); border-color: var(--accent); color: #fff; }}
    button.compact {{ padding: 6px 9px; font-size: 14px; }}
    button:focus, select:focus, input:focus, textarea:focus {{
      outline: 3px solid var(--focus);
      outline-offset: 1px;
    }}
    input, select, textarea {{
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 9px;
      background: #fff;
      color: var(--text);
    }}
    main {{ padding: 18px; }}
    .status {{ margin: 0 0 14px; color: var(--muted); }}
    .day-summary, .autosave-panel, .player-panel {{
      margin-bottom: 14px;
      padding: 12px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .day-summary strong {{ display: block; margin-bottom: 6px; font-size: 17px; }}
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(120px, 1fr));
      gap: 8px;
      margin-bottom: 10px;
      color: var(--muted);
    }}
    .summary-grid span {{ display: block; color: var(--text); font-weight: 700; }}
    .autosave-panel {{
      display: none;
      justify-content: space-between;
      gap: 10px;
      background: #ecfdf5;
      border-color: #bbf7d0;
      color: #14532d;
    }}
    .autosave-panel.open {{ display: flex; }}
    .player-panel {{
      position: sticky;
      top: 126px;
      z-index: 2;
      display: none;
      grid-template-columns: minmax(280px, 560px) 1fr;
      gap: 12px;
      box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
    }}
    .player-panel.open {{ display: grid; }}
    .player-panel video {{ width: 100%; max-height: 380px; background: #000; border-radius: 6px; }}
    .player-meta {{ display: grid; gap: 8px; min-width: 0; color: var(--muted); overflow-wrap: anywhere; }}
    .player-meta strong {{ color: var(--text); font-size: 17px; }}
    .item-list {{ display: grid; gap: 12px; }}
    .item-card {{
      display: grid;
      grid-template-columns: 230px 1fr;
      gap: 12px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
    }}
    .item-card.skip {{ background: var(--skip); }}
    .thumb-panel {{ display: grid; gap: 8px; align-content: start; }}
    .thumb {{
      display: block;
      width: 100%;
      max-height: 175px;
      object-fit: contain;
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 6px;
    }}
    .play-button {{ width: 100%; background: var(--accent-2); border-color: var(--accent-2); color: #fff; font-weight: 700; }}
    .fields {{
      display: grid;
      grid-template-columns: repeat(4, minmax(140px, 1fr));
      gap: 10px;
      min-width: 0;
    }}
    .field {{ display: grid; gap: 5px; }}
    .field.wide {{ grid-column: 1 / -1; }}
    label {{ color: var(--muted); font-size: 13px; font-weight: 600; }}
    textarea {{ width: 100%; min-height: 70px; resize: vertical; }}
    .meta {{ grid-column: 1 / -1; color: var(--muted); font-size: 13px; overflow-wrap: anywhere; }}
    a {{ color: var(--accent); }}
    @media (max-width: 980px) {{
      header {{ position: static; }}
      .item-card, .player-panel {{ grid-template-columns: 1fr; }}
      .fields, .summary-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>USA 2019 - předstřihový výběr fotek a videí</h1>
    <div class="toolbar">
      <select id="filterDay" aria-label="Den"></select>
      <select id="filterMedia" aria-label="Typ média">
        <option value="">Fotky i videa</option>
        <option value="photo">Jen fotky</option>
        <option value="video">Jen videa</option>
      </select>
      <select id="filterRating" aria-label="Rating">
        <option value="">Všechny ratingy</option>
        <option value="A">A</option>
        <option value="B">B</option>
        <option value="C">C</option>
        <option value="skip">Vyřadit</option>
        <option value="blank">Bez ratingu</option>
      </select>
      <input id="filterText" type="search" placeholder="Filtrovat text">
      <button id="downloadCsv" class="primary" type="button">Stáhnout CSV</button>
    </div>
  </header>
  <main>
    <section id="daySummary" class="day-summary"></section>
    <p id="status" class="status">Načítám CSV...</p>
    <section id="autosavePanel" class="autosave-panel" aria-live="polite">
      <div id="autosaveStatus">Autosave je připravený.</div>
      <div class="autosave-actions">
        <button id="downloadAutosave" type="button" class="compact">Stáhnout autosave CSV</button>
        <button id="discardAutosave" type="button" class="compact">Zahodit autosave</button>
      </div>
    </section>
    <section id="playerPanel" class="player-panel" aria-live="polite">
      <video id="videoPlayer" controls playsinline preload="metadata"></video>
      <div class="player-meta">
        <strong id="playerTitle">Vyber video</strong>
        <div id="playerDetails"></div>
        <div class="player-actions">
          <a id="openVideoLink" href="#" target="_blank" rel="noreferrer"><button type="button" class="compact">Otevřít samostatně</button></a>
          <button id="closePlayer" type="button" class="compact">Zavřít přehrávač</button>
        </div>
      </div>
    </section>
    <div id="itemList" class="item-list"></div>
  </main>
  <script>
    const CSV_PATH = "film_selection_review.csv";
    const VIDEO_BASE_URL = "http://127.0.0.1:8790/";
    const AUTOSAVE_KEY = "family_memory_media_review:usa_2019_film_selection:v1";
    const HEADERS = {headers_json};
    const DAY_SUMMARIES = {summaries_json};
    const state = {{ rows: [], day: DAY_SUMMARIES[0]?.day || "", media: "", rating: "", text: "", autosaveTimer: null }};

    function parseCsv(text) {{
      const rows = [];
      let row = [];
      let value = "";
      let quoted = false;
      for (let index = 0; index < text.length; index += 1) {{
        const char = text[index];
        const next = text[index + 1];
        if (quoted) {{
          if (char === '"' && next === '"') {{ value += '"'; index += 1; }}
          else if (char === '"') quoted = false;
          else value += char;
        }} else if (char === '"') quoted = true;
        else if (char === ",") {{ row.push(value); value = ""; }}
        else if (char === "\\n") {{
          row.push(value);
          if (row.some((cell) => cell.trim() !== "")) rows.push(row);
          row = [];
          value = "";
        }} else if (char !== "\\r") value += char;
      }}
      if (value || row.length) {{
        row.push(value);
        if (row.some((cell) => cell.trim() !== "")) rows.push(row);
      }}
      const [headers, ...records] = rows;
      return records.map((record) => Object.fromEntries(headers.map((header, index) => [header, record[index] || ""])));
    }}

    function csvEscape(value) {{
      const text = String(value ?? "");
      return /[",\\n\\r]/.test(text) ? `"${{text.replaceAll('"', '""')}}"` : text;
    }}

    function toCsv(rows) {{
      return `${{[HEADERS.join(","), ...rows.map((row) => HEADERS.map((header) => csvEscape(row[header])).join(","))].join("\\n")}}\\n`;
    }}

    function escapeHtml(value) {{
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }}

    function selected(value, current) {{ return value === current ? " selected" : ""; }}

    function videoUrl(row) {{
      return `${{VIDEO_BASE_URL}}${{row.relative_path.split("/").map(encodeURIComponent).join("/")}}`;
    }}

    function visibleRows() {{
      const query = state.text.trim().toLowerCase();
      return state.rows.filter((row) => {{
        if (state.day && row.correct_day !== state.day) return false;
        if (state.media && row.media_type !== state.media) return false;
        if (state.rating === "blank" && row.rating) return false;
        else if (state.rating && state.rating !== "blank" && row.rating !== state.rating) return false;
        if (query) {{
          const haystack = `${{row.item_index}} ${{row.original_name}} ${{row.day_title}} ${{row.short_chapter}} ${{row.long_chapter}} ${{row.role}} ${{row.notes}}`.toLowerCase();
          if (!haystack.includes(query)) return false;
        }}
        return true;
      }});
    }}

    function updateRow(index, key, value) {{
      state.rows[index][key] = value;
      scheduleAutosave();
      renderStatus();
    }}

    function renderStatus() {{
      const rows = visibleRows();
      const a = state.rows.filter((row) => row.rating === "A").length;
      const shortYes = state.rows.filter((row) => row.short_pick === "ano").length;
      const longYes = state.rows.filter((row) => row.long_pick === "ano").length;
      document.getElementById("status").textContent = `${{state.rows.length}} položek, zobrazeno: ${{rows.length}}, A: ${{a}}, krátký ano: ${{shortYes}}, dlouhý ano: ${{longYes}}`;
    }}

    function renderDaySelect() {{
      const select = document.getElementById("filterDay");
      select.innerHTML = DAY_SUMMARIES.map((day) => `<option value="${{escapeHtml(day.day)}}"${{selected(state.day, day.day)}}>${{escapeHtml(day.day)}} - ${{escapeHtml(day.title)}}</option>`).join("");
    }}

    function renderDaySummary() {{
      const summary = DAY_SUMMARIES.find((item) => item.day === state.day) || DAY_SUMMARIES[0];
      if (!summary) return;
      const links = [];
      if (summary.photo_sheet) links.push(`<a href="${{escapeHtml(summary.photo_sheet)}}" target="_blank" rel="noreferrer">Kontaktni list fotek</a>`);
      if (summary.video_sheet) links.push(`<a href="${{escapeHtml(summary.video_sheet)}}" target="_blank" rel="noreferrer">Kontaktni list videi</a>`);
      document.getElementById("daySummary").innerHTML = `
        <strong>${{escapeHtml(summary.day)}} - ${{escapeHtml(summary.title)}}</strong>
        <div class="summary-grid">
          <div>Fotky<span>${{summary.photos}}</span></div>
          <div>Videa<span>${{summary.videos}}</span></div>
          <div>Video min<span>${{summary.video_min}}</span></div>
          <div>Kapitola krátká<span>${{escapeHtml(summary.short_chapter)}}</span></div>
        </div>
        <div class="summary-links">${{links.join("")}}</div>
      `;
    }}

    function autosavePayload() {{
      return {{ savedAt: new Date().toISOString(), csvPath: CSV_PATH, rowCount: state.rows.length, rows: state.rows }};
    }}

    function readAutosave() {{
      try {{
        const raw = localStorage.getItem(AUTOSAVE_KEY);
        return raw ? JSON.parse(raw) : null;
      }} catch {{ return null; }}
    }}

    function renderAutosaveStatus(prefix) {{
      const panel = document.getElementById("autosavePanel");
      const status = document.getElementById("autosaveStatus");
      const saved = readAutosave();
      panel.classList.add("open");
      if (saved?.savedAt) {{
        status.textContent = `${{prefix}}: ${{new Date(saved.savedAt).toLocaleString("cs-CZ")}} (${{saved.rowCount || 0}} řádků).`;
      }} else status.textContent = prefix;
    }}

    function writeAutosave() {{
      try {{
        localStorage.setItem(AUTOSAVE_KEY, JSON.stringify(autosavePayload()));
        renderAutosaveStatus("Průběžně uloženo v prohlížeči");
      }} catch {{
        renderAutosaveStatus("Autosave se nepodařilo uložit");
      }}
    }}

    function scheduleAutosave() {{
      window.clearTimeout(state.autosaveTimer);
      state.autosaveTimer = window.setTimeout(writeAutosave, 250);
    }}

    function restoreAutosaveIfAvailable() {{
      const saved = readAutosave();
      if (!saved?.rows || saved.rowCount !== state.rows.length) {{
        renderAutosaveStatus("Autosave je zapnutý");
        return;
      }}
      state.rows = saved.rows;
      renderAutosaveStatus("Obnoveno z autosave");
    }}

    function downloadRows(rows, filename) {{
      const blob = new Blob([toCsv(rows)], {{ type: "text/csv;charset=utf-8" }});
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
    }}

    function render() {{
      renderDaySummary();
      const list = document.getElementById("itemList");
      list.innerHTML = "";
      for (const row of visibleRows()) {{
        const index = state.rows.indexOf(row);
        const isVideo = row.media_type === "video";
        const card = document.createElement("section");
        card.className = `item-card${{row.rating === "skip" ? " skip" : ""}}`;
        card.innerHTML = `
          <div class="thumb-panel">
            <a href="../02_review/${{escapeHtml(row.thumb)}}" target="_blank" rel="noreferrer">
              <img class="thumb" src="../02_review/${{escapeHtml(row.thumb)}}" alt="${{escapeHtml(row.original_name)}}">
            </a>
            ${{isVideo ? `<button class="play-button" type="button" data-play-index="${{index}}">Přehrát video</button>` : ""}}
          </div>
          <div class="fields">
            <div class="meta">
              <strong>${{escapeHtml(row.item_index)}} ${{escapeHtml(row.original_name)}}</strong>
              | ${{escapeHtml(row.media_type)}} | ${{escapeHtml(row.taken)}} | ${{escapeHtml(row.source_note)}} | ${{escapeHtml(row.relative_path)}}
            </div>
            <div class="field">
              <label for="rating-${{index}}">Rating</label>
              <select id="rating-${{index}}" data-key="rating" data-index="${{index}}">
                <option value=""${{selected(row.rating, "")}}>bez ratingu</option>
                <option value="A"${{selected(row.rating, "A")}}>A - silný kandidát</option>
                <option value="B"${{selected(row.rating, "B")}}>B - rezerva</option>
                <option value="C"${{selected(row.rating, "C")}}>C - jen archiv</option>
                <option value="skip"${{selected(row.rating, "skip")}}>vyřadit ze střihu</option>
              </select>
            </div>
            <div class="field">
              <label for="short-${{index}}">Krátký film</label>
              <select id="short-${{index}}" data-key="short_pick" data-index="${{index}}">
                <option value=""${{selected(row.short_pick, "")}}>nerozhodnuto</option>
                <option value="ano"${{selected(row.short_pick, "ano")}}>ano</option>
                <option value="mozna"${{selected(row.short_pick, "mozna")}}>možná</option>
                <option value="ne"${{selected(row.short_pick, "ne")}}>ne</option>
              </select>
            </div>
            <div class="field">
              <label for="long-${{index}}">Dlouhý film</label>
              <select id="long-${{index}}" data-key="long_pick" data-index="${{index}}">
                <option value=""${{selected(row.long_pick, "")}}>nerozhodnuto</option>
                <option value="ano"${{selected(row.long_pick, "ano")}}>ano</option>
                <option value="mozna"${{selected(row.long_pick, "mozna")}}>možná</option>
                <option value="ne"${{selected(row.long_pick, "ne")}}>ne</option>
              </select>
            </div>
            <div class="field">
              <label for="role-${{index}}">Role</label>
              <select id="role-${{index}}" data-key="role" data-index="${{index}}">
                <option value=""${{selected(row.role, "")}}>nevybráno</option>
                <option value="lidi"${{selected(row.role, "lidi")}}>lidi / rodina</option>
                <option value="panorama"${{selected(row.role, "panorama")}}>panorama</option>
                <option value="misto"${{selected(row.role, "misto")}}>místo / cedule</option>
                <option value="prechod"${{selected(row.role, "prechod")}}>přechod / cesta</option>
                <option value="detail"${{selected(row.role, "detail")}}>detail</option>
                <option value="audio"${{selected(row.role, "audio")}}>dobrý zvuk</option>
              </select>
            </div>
            <div class="field wide">
              <label for="notes-${{index}}">Poznámky ke střihu</label>
              <textarea id="notes-${{index}}" data-key="notes" data-index="${{index}}">${{escapeHtml(row.notes)}}</textarea>
            </div>
          </div>
        `;
        list.appendChild(card);
      }}
      renderStatus();
    }}

    function playVideo(row) {{
      const panel = document.getElementById("playerPanel");
      const player = document.getElementById("videoPlayer");
      const title = document.getElementById("playerTitle");
      const details = document.getElementById("playerDetails");
      const link = document.getElementById("openVideoLink");
      const url = videoUrl(row);
      player.src = url;
      title.textContent = `${{row.item_index}} ${{row.original_name}}`;
      details.textContent = `${{row.correct_day}} | ${{row.duration_s || "foto"}} s | ${{row.relative_path}}`;
      link.href = url;
      panel.classList.add("open");
      player.load();
      player.play().catch(() => {{}});
      panel.scrollIntoView({{ behavior: "smooth", block: "start" }});
    }}

    async function load() {{
      renderDaySelect();
      const response = await fetch(CSV_PATH, {{ cache: "no-store" }});
      if (!response.ok) throw new Error(`CSV nelze načíst: ${{response.status}}`);
      state.rows = parseCsv(await response.text());
      restoreAutosaveIfAvailable();
      render();
    }}

    document.getElementById("itemList").addEventListener("input", (event) => {{
      const target = event.target;
      if (!target.dataset.key) return;
      updateRow(Number(target.dataset.index), target.dataset.key, target.value);
    }});
    document.getElementById("itemList").addEventListener("change", (event) => {{
      const target = event.target;
      if (!target.dataset.key) return;
      updateRow(Number(target.dataset.index), target.dataset.key, target.value);
      render();
    }});
    document.getElementById("itemList").addEventListener("click", (event) => {{
      const target = event.target.closest("[data-play-index]");
      if (!target) return;
      playVideo(state.rows[Number(target.dataset.playIndex)]);
    }});
    document.getElementById("filterDay").addEventListener("change", (event) => {{ state.day = event.target.value; render(); }});
    document.getElementById("filterMedia").addEventListener("change", (event) => {{ state.media = event.target.value; render(); }});
    document.getElementById("filterRating").addEventListener("change", (event) => {{ state.rating = event.target.value; render(); }});
    document.getElementById("filterText").addEventListener("input", (event) => {{ state.text = event.target.value; render(); }});
    document.getElementById("downloadCsv").addEventListener("click", () => {{ writeAutosave(); downloadRows(state.rows, "film_selection_review.csv"); }});
    document.getElementById("downloadAutosave").addEventListener("click", () => {{
      const saved = readAutosave();
      downloadRows(saved?.rows || state.rows, "film_selection_review_autosave.csv");
    }});
    document.getElementById("discardAutosave").addEventListener("click", () => {{
      localStorage.removeItem(AUTOSAVE_KEY);
      renderAutosaveStatus("Autosave byl zahozen; další změna založí nový");
    }});
    document.getElementById("closePlayer").addEventListener("click", () => {{
      const panel = document.getElementById("playerPanel");
      const player = document.getElementById("videoPlayer");
      player.pause();
      player.removeAttribute("src");
      panel.classList.remove("open");
    }});
    window.addEventListener("beforeunload", () => {{ if (state.rows.length) writeAutosave(); }});
    load().catch((error) => {{ document.getElementById("status").textContent = `${{error.message}}.`; }});
  </script>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest_items = load_manifest(args.manifest)
    film_items = collect_film_items(manifest_items, args.block_review, args.mixed_review, args.gap_minutes)
    sheets = write_day_sheets(args.out_dir, args.review_dir, film_items)
    summaries = day_summaries(film_items, sheets)
    write_items_csv(args.out_dir / "film_selection_review.csv", args.review_dir, film_items)
    write_html(args.out_dir / "film_selection_form.html", summaries)
    print(f"items={len(film_items)}")
    print(args.out_dir / "film_selection_review.csv")
    print(args.out_dir / "film_selection_form.html")


if __name__ == "__main__":
    main()
