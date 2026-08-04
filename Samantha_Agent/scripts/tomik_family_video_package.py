from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path


DEFAULT_ROOT = Path("data/private/tomik_rok_2")
DEFAULT_APP_DIR = Path("docs/family-video-organizer")
DEFAULT_OUT_DIR = DEFAULT_ROOT / "family_video_organizer_package"


@dataclass(frozen=True)
class PackageSummary:
    output_dir: Path
    videos: int
    short_videos: int
    family_videos: int
    copied_thumbnails: int
    missing_thumbnails: int
    package_videos: int
    missing_videos: int
    includes_videos: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a private FamilyVideoOrganizer package for Tomik videos."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Private Tomik project root. Default: data/private/tomik_rok_2",
    )
    parser.add_argument(
        "--app-dir",
        type=Path,
        default=DEFAULT_APP_DIR,
        help="FamilyVideoOrganizer app source directory.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Package output directory. Default: data/private/tomik_rok_2/family_video_organizer_package",
    )
    parser.add_argument(
        "--include-videos",
        action="store_true",
        help="Add MP4 files to the package as hardlinks or copies. Default package is lightweight.",
    )
    parser.add_argument(
        "--thumbnail-limit",
        type=int,
        default=1,
        choices=(1, 2, 3),
        help="Number of thumbnails copied per video. Default: 1 for email-friendly packages.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_selection_map(path: Path) -> dict[str, dict[str, str]]:
    rows = read_csv(path)
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        source_file = row.get("source_file", "").strip()
        index = row.get("index", "").strip().zfill(3)
        if source_file:
            result[source_file] = row
        if index:
            result[index] = row
    return result


def format_duration(value: str) -> str:
    try:
        seconds = int(round(float(value)))
    except (TypeError, ValueError):
        return ""
    if seconds < 60:
        return f"{seconds}s"
    minutes, rest = divmod(seconds, 60)
    return f"{minutes}:{rest:02d}"


def date_part(value: str) -> str:
    return (value or "").strip()[:10]


def clean_title(description: str, fallback: str) -> str:
    title = (description or "").strip().rstrip(".")
    if title:
        return title[:1].lower() + title[1:]
    return fallback


def copy_app_files(app_dir: Path, out_dir: Path) -> None:
    for filename in ("app.js", "styles.css"):
        shutil.copy2(app_dir / filename, out_dir / filename)

    index = (app_dir / "index.html").read_text(encoding="utf-8")
    index = index.replace("videos-data.example.js", "videos-data.js")
    (out_dir / "index.html").write_text(index, encoding="utf-8")


def make_video_record(
    row: dict[str, str],
    short_map: dict[str, dict[str, str]],
    family_map: dict[str, dict[str, str]],
    thumbs_dir: Path,
    package_thumbs_dir: Path,
    thumbnail_limit: int,
) -> tuple[dict[str, object], int, int]:
    index = row["index"].strip().zfill(3)
    proposed_name = row.get("proposed_name", "").strip()
    short_row = short_map.get(proposed_name) or short_map.get(index)
    family_row = family_map.get(proposed_name) or family_map.get(index)

    thumbs: list[str] = []
    copied = 0
    missing = 0
    for field in ("thumb_1", "thumb_2", "thumb_3")[:thumbnail_limit]:
        name = row.get(field, "").strip()
        if not name:
            continue
        source = thumbs_dir / name
        if source.exists():
            target = package_thumbs_dir / name
            if not target.exists():
                shutil.copy2(source, target)
            copied += 1
            thumbs.append(f"thumbs/{name}")
        else:
            missing += 1

    original_name = row.get("original_name", "").strip()
    description = row.get("draft_description", "").strip()
    record: dict[str, object] = {
        "id": index,
        "date": date_part(row.get("taken", "")),
        "duration": format_duration(row.get("duration_s", "")),
        "title": clean_title(description, proposed_name or original_name),
        "originalName": original_name,
        "description": description,
        "videoShort": short_row is not None,
        "videoFamily": family_row is not None,
        "thumbs": thumbs,
        "videoPath": f"videos/{original_name}",
        "proposedName": proposed_name,
        "sizeMb": row.get("size_mb", ""),
        "resolution": f"{row.get('width', '').strip()}x{row.get('height', '').strip()}",
        "rotation": row.get("rotation", "").strip(),
        "shortOrder": short_row.get("order", "") if short_row else "",
        "shortChapter": short_row.get("chapter", "") if short_row else "",
        "familyOrder": family_row.get("order", "") if family_row else "",
        "familyChapter": family_row.get("chapter", "") if family_row else "",
    }
    return record, copied, missing


def write_videos_data(out_dir: Path, videos: list[dict[str, object]]) -> None:
    payload = {
        "project": "Tomik rok 2 - realna data",
        "videos": videos,
    }
    text = "window.FAMILY_VIDEO_DATA = "
    text += json.dumps(payload, ensure_ascii=False, indent=2)
    text += ";\n"
    (out_dir / "videos-data.js").write_text(text, encoding="utf-8")


def link_or_copy_video(source: Path, target: Path) -> None:
    if target.exists():
        return
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)


def populate_video_files(originals_dir: Path, package_videos_dir: Path, videos: list[dict[str, object]]) -> tuple[int, int]:
    package_videos_dir.mkdir(exist_ok=True)
    available = 0
    missing = 0
    for video in videos:
        original_name = str(video.get("originalName", "")).strip()
        if not original_name:
            missing += 1
            continue
        source = originals_dir / original_name
        target = package_videos_dir / original_name
        if target.exists():
            available += 1
        elif source.exists():
            link_or_copy_video(source, target)
            available += 1
        else:
            missing += 1
    return available, missing


def write_readme(out_dir: Path, summary: PackageSummary) -> None:
    if summary.includes_videos:
        playback_note = (
            "Slozka `videos/` obsahuje hardlinky nebo kopie puvodnich MP4 souboru. "
            "Prehravani by melo fungovat primo tlacitkem `Play`."
        )
        video_folder_note = "Slozka `videos/` obsahuje hardlinky nebo kopie puvodnich MP4 souboru."
    else:
        playback_note = (
            "Balicek neobsahuje MP4 soubory. V Chrome nebo Edge klikni na `Slozka s videi` "
            "a vyber adresar, kde jsou ulozena puvodni videa se stejnymi nazvy souboru."
        )
        video_folder_note = "Balicek neobsahuje MP4 soubory; prehravani probiha pres tlacitko `Slozka s videi`."
    readme = f"""# FamilyVideoOrganizer - Tomik rok 2

Soukromy lokalni balicek pro rozhodovani nad rodinnymi videi.

## Spusteni

1. Otevri `index.html` v Chrome nebo Edge.
2. {playback_note}
3. Prubezne se uklada lokalni draft v prohlizeci.
4. Po dokonceni pouzij `Export rozhodnuti` a posli vznikly JSON zpet.

## Obsah balicku

- videi v tabulce: {summary.videos}
- ve vyberu short: {summary.short_videos}
- ve vyberu family: {summary.family_videos}
- zkopirovane nahledy pri poslednim behu: {summary.copied_thumbnails}
- chybejici nahledy: {summary.missing_thumbnails}
- video soubory v balicku: {summary.package_videos}
- chybejici video soubory: {summary.missing_videos}

{video_folder_note}
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")
    if summary.includes_videos:
        (out_dir / "videos").mkdir(exist_ok=True)
        (out_dir / "videos" / "INFO.txt").write_text(
            "Tato slozka obsahuje hardlinky nebo kopie puvodnich MP4 souboru.\n"
            "Pokud se video v prohlizeci nespusti, pouzij v Chrome/Edge tlacitko Slozka s videi.\n",
            encoding="utf-8",
        )


def build_family_video_package(
    root: Path = DEFAULT_ROOT,
    app_dir: Path = DEFAULT_APP_DIR,
    out_dir: Path = DEFAULT_OUT_DIR,
    include_videos: bool = False,
    thumbnail_limit: int = 1,
) -> PackageSummary:
    if thumbnail_limit not in (1, 2, 3):
        raise ValueError("thumbnail_limit must be 1, 2, or 3")

    audit_csv = root / "03_audit" / "video_audit_described.csv"
    short_csv = root / "05_imovie_vyber_short" / "selection_manifest_short.csv"
    family_csv = root / "06_imovie_vyber_family" / "selection_manifest_family.csv"
    thumbs_dir = root / "02_nahledy"
    originals_dir = root / "01_originaly"

    required_paths = [audit_csv, short_csv, family_csv, thumbs_dir, app_dir / "index.html"]
    if include_videos:
        required_paths.append(originals_dir)
    for required in required_paths:
        if not required.exists():
            raise FileNotFoundError(required)

    out_dir.mkdir(parents=True, exist_ok=True)
    package_thumbs_dir = out_dir / "thumbs"
    package_thumbs_dir.mkdir(exist_ok=True)

    copy_app_files(app_dir, out_dir)

    short_map = load_selection_map(short_csv)
    family_map = load_selection_map(family_csv)
    videos: list[dict[str, object]] = []
    copied_thumbnails = 0
    missing_thumbnails = 0
    for row in read_csv(audit_csv):
        record, copied, missing = make_video_record(
            row,
            short_map,
            family_map,
            thumbs_dir,
            package_thumbs_dir,
            thumbnail_limit,
        )
        videos.append(record)
        copied_thumbnails += copied
        missing_thumbnails += missing

    write_videos_data(out_dir, videos)
    package_videos = 0
    missing_videos = 0
    if include_videos:
        package_videos, missing_videos = populate_video_files(originals_dir, out_dir / "videos", videos)
    summary = PackageSummary(
        output_dir=out_dir,
        videos=len(videos),
        short_videos=sum(1 for video in videos if video["videoShort"]),
        family_videos=sum(1 for video in videos if video["videoFamily"]),
        copied_thumbnails=copied_thumbnails,
        missing_thumbnails=missing_thumbnails,
        package_videos=package_videos,
        missing_videos=missing_videos,
        includes_videos=include_videos,
    )
    write_readme(out_dir, summary)
    return summary


def main() -> None:
    args = parse_args()
    summary = build_family_video_package(
        root=args.root,
        app_dir=args.app_dir,
        out_dir=args.out_dir,
        include_videos=args.include_videos,
        thumbnail_limit=args.thumbnail_limit,
    )
    print(f"package={summary.output_dir}")
    print(f"videos={summary.videos}")
    print(f"short={summary.short_videos}")
    print(f"family={summary.family_videos}")
    print(f"copied_thumbnails={summary.copied_thumbnails}")
    print(f"missing_thumbnails={summary.missing_thumbnails}")
    print(f"package_videos={summary.package_videos}")
    print(f"missing_videos={summary.missing_videos}")


if __name__ == "__main__":
    main()
