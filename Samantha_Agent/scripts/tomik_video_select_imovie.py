from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path("data/private/tomik_rok_2")
AUDIT = ROOT / "03_audit"
SORTED = ROOT / "04_chronologicky_pojmenovane"
SHORT_DIR = ROOT / "05_imovie_vyber_short"
FAMILY_DIR = ROOT / "06_imovie_vyber_family"


SHORT_ANCHORS = {
    1,
    7,
    14,
    21,
    25,
    28,
    32,
    37,
    40,
    48,
    55,
    56,
    65,
    75,
    77,
    80,
    85,
    98,
    104,
    115,
    134,
    140,
    141,
    150,
    158,
    162,
    168,
    170,
    177,
    190,
    194,
    195,
    203,
    211,
    217,
}

FAMILY_SEED = SHORT_ANCHORS | {
    2,
    10,
    12,
    19,
    27,
    29,
    35,
    39,
    52,
    62,
    67,
    72,
    87,
    92,
    103,
    109,
    114,
    118,
    136,
    142,
    144,
    149,
    153,
    164,
    172,
    183,
    189,
    205,
    212,
    214,
}

FAMILY_TARGET = 82

CHAPTER_TARGETS = {
    "01_jaro_2025_start": 13,
    "02_leto_2025_venku": 11,
    "03_more_a_cesty": 10,
    "04_podzim_2025": 10,
    "05_rodina_a_vanoce": 12,
    "06_zima_2026": 6,
    "07_jaro_2026": 12,
    "08_narozeniny_a_finale": 8,
}


@dataclass(frozen=True)
class VideoRow:
    index: int
    taken: str
    original_name: str
    duration_s: float
    description: str
    proposed_name: str
    chapter: str
    score: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create private iMovie selections and storyboards for Tomik year 2 videos."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print what would be created; do not write files.",
    )
    return parser.parse_args()


def date_from_taken(value: str) -> datetime:
    match = re.match(r"(20\d{2})-(\d{2})-(\d{2})", value)
    if not match:
        return datetime(1900, 1, 1)
    year, month, day = (int(part) for part in match.groups())
    return datetime(year, month, day)


def chapter_for(taken: str) -> str:
    day = date_from_taken(taken)
    if day < datetime(2025, 6, 1):
        return "01_jaro_2025_start"
    if day < datetime(2025, 8, 15):
        return "02_leto_2025_venku"
    if day < datetime(2025, 9, 1):
        return "03_more_a_cesty"
    if day < datetime(2025, 11, 1):
        return "04_podzim_2025"
    if day < datetime(2026, 1, 1):
        return "05_rodina_a_vanoce"
    if day < datetime(2026, 3, 1):
        return "06_zima_2026"
    if day < datetime(2026, 4, 11):
        return "07_jaro_2026"
    return "08_narozeniny_a_finale"


def score_row(index: int, description: str, duration_s: float) -> int:
    text = description.lower()
    score = 0
    positive_terms = [
        "rodin",
        "hra",
        "hristi",
        "hřišti",
        "zahrad",
        "venk",
        "voda",
        "bazen",
        "bazén",
        "more",
        "moř",
        "plaz",
        "pláž",
        "cest",
        "letadl",
        "vlak",
        "kolo",
        "odrazed",
        "odráž",
        "dort",
        "svick",
        "svíčk",
        "vano",
        "váno",
        "sank",
        "sáň",
        "cteni",
        "čten",
        "tanec",
        "houp",
        "skluz",
    ]
    negative_terms = ["tmav", "velmi tmav", "kratky detail", "krátký detail", "nejas"]
    for term in positive_terms:
        if term in text:
            score += 3
    for term in negative_terms:
        if term in text:
            score -= 8
    if 8 <= duration_s <= 60:
        score += 2
    if 12 <= duration_s <= 35:
        score += 2
    if duration_s > 75:
        score -= 3
    if index in FAMILY_SEED:
        score += 20
    if index in SHORT_ANCHORS:
        score += 40
    return score


def load_rows() -> list[VideoRow]:
    source = AUDIT / "video_audit_described.csv"
    rows: list[VideoRow] = []
    with source.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            idx = int(raw["index"])
            duration_s = float(raw["duration_s"])
            description = raw["draft_description"].strip()
            chapter = chapter_for(raw["taken"])
            rows.append(
                VideoRow(
                    index=idx,
                    taken=raw["taken"],
                    original_name=raw["original_name"],
                    duration_s=duration_s,
                    description=description,
                    proposed_name=raw["proposed_name"],
                    chapter=chapter,
                    score=score_row(idx, description, duration_s),
                )
            )
    rows.sort(key=lambda row: row.index)
    return rows


def select_short(rows: list[VideoRow]) -> list[VideoRow]:
    selected = [row for row in rows if row.index in SHORT_ANCHORS]
    missing = SHORT_ANCHORS - {row.index for row in selected}
    if missing:
        raise RuntimeError(f"Missing short anchors: {sorted(missing)}")
    return selected


def select_family(rows: list[VideoRow]) -> list[VideoRow]:
    by_index = {row.index: row for row in rows}
    selected: dict[int, VideoRow] = {
        idx: by_index[idx] for idx in sorted(FAMILY_SEED) if idx in by_index
    }

    for chapter, target in CHAPTER_TARGETS.items():
        current = [row for row in selected.values() if row.chapter == chapter]
        if len(current) >= target:
            continue
        candidates = [
            row
            for row in rows
            if row.chapter == chapter and row.index not in selected
        ]
        candidates.sort(key=lambda row: (-row.score, row.index))
        for row in candidates[: target - len(current)]:
            selected[row.index] = row

    if len(selected) < FAMILY_TARGET:
        candidates = [row for row in rows if row.index not in selected]
        candidates.sort(key=lambda row: (-row.score, row.index))
        for row in candidates[: FAMILY_TARGET - len(selected)]:
            selected[row.index] = row

    return [selected[idx] for idx in sorted(selected)]


def link_or_copy(src: Path, dst: Path) -> str:
    if dst.exists():
        return "exists"
    try:
        os.link(src, dst)
        return "hardlink"
    except OSError:
        shutil.copy2(src, dst)
        return "copy2"


def chapter_title(chapter: str) -> str:
    return {
        "01_jaro_2025_start": "Jaro 2025 - zacatek druheho roku",
        "02_leto_2025_venku": "Leto 2025 - venku, voda a hriste",
        "03_more_a_cesty": "Cestovani a more",
        "04_podzim_2025": "Podzim 2025 - vychazky a odrazedla",
        "05_rodina_a_vanoce": "Rodina, svetylka a Vanoce",
        "06_zima_2026": "Zima 2026 - doma a na snehu",
        "07_jaro_2026": "Jaro 2026 - hriste, vylety a hry",
        "08_narozeniny_a_finale": "Druhe narozeniny a finale",
    }[chapter]


def write_manifest(
    rows: list[VideoRow],
    out_dir: Path,
    manifest_name: str,
    dry_run: bool,
) -> list[dict[str, str]]:
    manifest: list[dict[str, str]] = []
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    for order, row in enumerate(rows, 1):
        src = SORTED / row.proposed_name
        if not src.exists():
            raise FileNotFoundError(src)
        dst_name = f"{order:03d}_{row.proposed_name}"
        dst = out_dir / dst_name
        action = "dry-run"
        if not dry_run:
            action = link_or_copy(src, dst)
        manifest.append(
            {
                "order": f"{order:03d}",
                "index": f"{row.index:03d}",
                "taken": row.taken,
                "chapter": row.chapter,
                "selection_file": dst_name,
                "source_file": row.proposed_name,
                "duration_s": f"{row.duration_s:.2f}",
                "description": row.description,
                "action": action,
            }
        )

    if not dry_run:
        with (out_dir / manifest_name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "order",
                    "index",
                    "taken",
                    "chapter",
                    "selection_file",
                    "source_file",
                    "duration_s",
                    "description",
                    "action",
                ],
            )
            writer.writeheader()
            writer.writerows(manifest)
    return manifest


def format_duration(seconds: float) -> str:
    minutes = int(seconds // 60)
    rest = int(round(seconds % 60))
    return f"{minutes}:{rest:02d}"


def write_storyboard(
    rows: list[VideoRow],
    output: Path,
    title: str,
    target_note: str,
    dry_run: bool,
) -> None:
    total = sum(row.duration_s for row in rows)
    lines = [
        f"# {title}",
        "",
        f"Pocet klipu: {len(rows)}",
        f"Soucet surove delky: {format_duration(total)}",
        f"Cil strihu: {target_note}",
        "",
        "Poznamka: vyber je pracovni. V iMovie z kazdeho klipu typicky pouzij jen nejlepsich par sekund.",
        "",
    ]

    for chapter in CHAPTER_TARGETS:
        chapter_rows = [row for row in rows if row.chapter == chapter]
        if not chapter_rows:
            continue
        lines.extend(
            [
                f"## {chapter_title(chapter)}",
                "",
                "| Poradi | Index | Datum | Klip | Popis | Hruba delka |",
                "|---|---|---|---|---|---|",
            ]
        )
        for order, row in enumerate(rows, 1):
            if row.chapter != chapter:
                continue
            lines.append(
                f"| {order:03d} | {row.index:03d} | {row.taken} | `{order:03d}_{row.proposed_name}` | {row.description} | {format_duration(row.duration_s)} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Prakticky postup v iMovie",
            "",
            "1. Importuj obsah odpovidajici vyberove slozky.",
            "2. Seradeni ponech podle ciselneho prefixu v nazvu souboru.",
            "3. U kratke verze zkracuj vetsinu klipu na 5-10 sekund.",
            "4. U rodinne verze nech dulezite rodinne momenty delsi, ale opakujici se sceny zkrat.",
            "5. Tmave nebo technicky slabsi zabery pouzij jen pokud maji rodinnou hodnotu.",
            "6. Po prvnim exportu udelej kontrolu na telefonu nebo TV a az potom finalni export.",
            "",
        ]
    )
    if not dry_run:
        output.write_text("\n".join(lines), encoding="utf-8")


def print_summary(name: str, rows: list[VideoRow]) -> None:
    total = sum(row.duration_s for row in rows)
    print(f"{name}: {len(rows)} clips, raw duration {format_duration(total)}")
    for chapter in CHAPTER_TARGETS:
        chapter_rows = [row for row in rows if row.chapter == chapter]
        if chapter_rows:
            print(f"  {chapter}: {len(chapter_rows)}")


def main() -> None:
    args = parse_args()
    rows = load_rows()
    short_rows = select_short(rows)
    family_rows = select_family(rows)

    write_manifest(short_rows, SHORT_DIR, "selection_manifest_short.csv", args.dry_run)
    write_manifest(family_rows, FAMILY_DIR, "selection_manifest_family.csv", args.dry_run)
    write_storyboard(
        short_rows,
        AUDIT / "storyboard_short.md",
        "Storyboard short - Tomik druhy rok",
        "3-5 minutovy sestřih pro rychle pusteni rodine.",
        args.dry_run,
    )
    write_storyboard(
        family_rows,
        AUDIT / "storyboard_family.md",
        "Storyboard family - Tomik druhy rok",
        "12-18 minutovy rodinny film s chronologickymi kapitolami.",
        args.dry_run,
    )

    print_summary("short", short_rows)
    print_summary("family", family_rows)
    if args.dry_run:
        print("dry-run only; no files written")
    else:
        print(f"short_dir={SHORT_DIR}")
        print(f"family_dir={FAMILY_DIR}")
        print(f"storyboard_short={AUDIT / 'storyboard_short.md'}")
        print(f"storyboard_family={AUDIT / 'storyboard_family.md'}")


if __name__ == "__main__":
    main()
