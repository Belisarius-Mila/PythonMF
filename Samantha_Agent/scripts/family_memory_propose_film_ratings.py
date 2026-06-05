from __future__ import annotations

import argparse
import csv
import math
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageStat


DEFAULT_REVIEW_DIR = Path("data/private/family_memory_films/usa_2019/02_review")
DEFAULT_OVERVIEW_DIR = Path("data/private/family_memory_films/usa_2019/03_overview")


A_QUOTAS = {
    "2019-07-20": {"photo": 3, "video": 3},
    "2019-07-21": {"photo": 12, "video": 7},
    "2019-07-22": {"photo": 8, "video": 12},
    "2019-07-23": {"photo": 10, "video": 6},
    "2019-07-24": {"photo": 15, "video": 15},
    "2019-07-25": {"photo": 25, "video": 12},
    "2019-07-26": {"photo": 18, "video": 10},
    "2019-07-27": {"photo": 12, "video": 10},
    "2019-07-28": {"photo": 6, "video": 4},
    "2019-07-29": {"photo": 18, "video": 12},
    "2019-07-30": {"photo": 25, "video": 18},
    "2019-07-31": {"photo": 25, "video": 24},
    "2019-08-01": {"photo": 22, "video": 18},
    "2019-08-02": {"photo": 18, "video": 26},
    "2019-08-03": {"photo": 5, "video": 7},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply first-pass A/B/C film rating proposal to USA 2019 film selection CSV.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_OVERVIEW_DIR / "film_selection_review.csv")
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
    parser.add_argument("--overview-dir", type=Path, default=DEFAULT_OVERVIEW_DIR)
    parser.add_argument("--apply", action="store_true", help="Write ratings to the CSV. Without this, only reports proposed counts.")
    return parser.parse_args()


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_rows(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def thumbnail_metrics(path: Path) -> dict[str, float]:
    try:
        with Image.open(path) as image:
            image = image.convert("RGB")
            image.thumbnail((220, 220))
            gray = image.convert("L")
            arr = np.asarray(gray, dtype=np.float32)
            rgb = np.asarray(image, dtype=np.float32)
    except Exception:
        return {"ok": 0.0, "score": -10.0, "brightness": 0.0, "contrast": 0.0, "sharpness": 0.0, "color": 0.0}

    stat = ImageStat.Stat(gray)
    brightness = float(stat.mean[0])
    contrast = float(stat.stddev[0])
    dx = np.diff(arr, axis=1)
    dy = np.diff(arr, axis=0)
    sharpness = float(np.mean(np.abs(dx)) + np.mean(np.abs(dy)))
    rg = rgb[:, :, 0] - rgb[:, :, 1]
    yb = 0.5 * (rgb[:, :, 0] + rgb[:, :, 1]) - rgb[:, :, 2]
    color = float(np.sqrt(np.std(rg) ** 2 + np.std(yb) ** 2) + 0.3 * np.sqrt(np.mean(rg) ** 2 + np.mean(yb) ** 2))

    exposure = 1.0 - min(abs(brightness - 128.0) / 128.0, 1.0)
    contrast_score = min(contrast / 64.0, 1.4)
    sharp_score = min(sharpness / 28.0, 1.4)
    color_score = min(color / 72.0, 1.2)
    score = 1.4 * exposure + 1.2 * contrast_score + 1.4 * sharp_score + 0.8 * color_score
    return {
        "ok": 1.0,
        "score": score,
        "brightness": brightness,
        "contrast": contrast,
        "sharpness": sharpness,
        "color": color,
    }


def duration_bonus(row: dict[str, str]) -> float:
    if row.get("media_type") != "video":
        return 0.0
    try:
        duration = float(row.get("duration_s", "") or 0)
    except ValueError:
        return -0.6
    if duration < 1.5:
        return -1.8
    if duration < 4:
        return -0.5
    if duration <= 45:
        return 1.0
    if duration <= 120:
        return 0.3
    return -0.4


def forced_c(row: dict[str, str], metrics: dict[str, float]) -> bool:
    if not metrics["ok"]:
        return True
    if row.get("media_type") == "video":
        try:
            if float(row.get("duration_s", "") or 0) < 1.2:
                return True
        except ValueError:
            return True
    return metrics["contrast"] < 12 or metrics["sharpness"] < 4 or metrics["brightness"] < 20 or metrics["brightness"] > 238


def b_limit(count: int, a_limit: int, media_type: str) -> int:
    if count <= a_limit:
        return count
    cap = 70 if media_type == "video" else 60
    return min(count, max(a_limit * 3, a_limit + min(cap, math.ceil(count * 0.32))))


def propose(rows: list[dict[str, str]], review_dir: Path) -> tuple[list[dict[str, str]], dict[str, dict[str, int]]]:
    scored: list[tuple[dict[str, str], float, bool]] = []
    for row in rows:
        thumb = row.get("thumb", "")
        metrics = thumbnail_metrics(review_dir / thumb) if thumb else {"ok": 0.0, "score": -10.0, "contrast": 0.0, "sharpness": 0.0, "brightness": 0.0}
        score = metrics["score"] + duration_bonus(row)
        if row.get("source_note", "").startswith("mixed:"):
            score += 0.15
        scored.append((row, score, forced_c(row, metrics)))

    by_group: dict[tuple[str, str], list[tuple[dict[str, str], float, bool]]] = defaultdict(list)
    for item in scored:
        row = item[0]
        by_group[(row.get("correct_day", ""), row.get("media_type", ""))].append(item)

    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"A": 0, "B": 0, "C": 0})
    for (day, media_type), group in by_group.items():
        group.sort(key=lambda item: item[1], reverse=True)
        a_limit = min(A_QUOTAS.get(day, {}).get(media_type, max(2, math.ceil(len(group) * 0.08))), len(group))
        b_until = b_limit(len(group), a_limit, media_type)
        good_rank = 0
        for row, _score, is_forced_c in group:
            if is_forced_c:
                rating = "C"
            else:
                good_rank += 1
                if good_rank <= a_limit:
                    rating = "A"
                elif good_rank <= b_until:
                    rating = "B"
                else:
                    rating = "C"
            row["rating"] = rating
            if rating == "A":
                row["short_pick"] = "ano"
                row["long_pick"] = "ano"
            elif rating == "B":
                row["short_pick"] = "mozna"
                row["long_pick"] = "ano"
            else:
                row["short_pick"] = "ne"
                row["long_pick"] = "mozna"
            counts[day][rating] += 1
    return rows, counts


def write_report(path: Path, rows: list[dict[str, str]], counts: dict[str, dict[str, int]]) -> None:
    total = defaultdict(int)
    for row in rows:
        total[row["rating"]] += 1
    lines = [
        "# USA 2019 - Adamuv navrh ratingu A/B/C",
        "",
        f"Vytvoreno: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "Metodika: prvni technicko-dramaturgicky pruchod podle kvality nahledu, delky videa, dne cesty a rozumnych kvot pro film. Neumi spolehlive poznat osobni/emocionalni hodnotu rodinnych momentu, proto je to startovni navrh k rucni korekci.",
        "",
        f"Celkem: A={total['A']}, B={total['B']}, C={total['C']}",
        "",
        "| Den | A | B | C |",
        "|---|---:|---:|---:|",
    ]
    for day in sorted(counts):
        day_counts = counts[day]
        lines.append(f"| {day} | {day_counts['A']} | {day_counts['B']} | {day_counts['C']} |")
    lines.extend(
        [
            "",
            "Doporucene cteni ratingu:",
            "",
            "- A: silny kandidat, ktery se ma prednostne zkontrolovat a pravdepodobne pouzit.",
            "- B: rezerva pro dlouhy film nebo doplneni kapitoly.",
            "- C: archivni material, pouzit jen pokud ma osobni hodnotu nebo chybi lepsi zaber.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def bump_form_autosave_key(form_path: Path) -> None:
    if not form_path.exists():
        return
    text = form_path.read_text(encoding="utf-8")
    text = text.replace(
        "family_memory_media_review:usa_2019_film_selection:v1",
        "family_memory_media_review:usa_2019_film_selection:adam_rating_v1",
    )
    form_path.write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    headers, rows = read_rows(args.csv)
    proposed_rows, counts = propose(rows, args.review_dir)
    report_path = args.overview_dir / "adam_rating_proposal.md"
    write_report(report_path, proposed_rows, counts)
    if args.apply:
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        backup = args.csv.with_name(f"{args.csv.stem}.before_adam_rating_{stamp}{args.csv.suffix}")
        shutil.copy2(args.csv, backup)
        write_rows(args.csv, headers, proposed_rows)
        bump_form_autosave_key(args.overview_dir / "film_selection_form.html")
        print(f"backup={backup}")
        print(f"updated={args.csv}")
    print(f"report={report_path}")
    for day in sorted(counts):
        day_counts = counts[day]
        print(f"{day}: A={day_counts['A']} B={day_counts['B']} C={day_counts['C']}")


if __name__ == "__main__":
    main()
