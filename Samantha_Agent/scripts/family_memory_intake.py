from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import ExifTags, Image


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic"}
VIDEO_EXTS = {".mov", ".mp4", ".m4v"}


@dataclass(frozen=True)
class MediaItem:
    index: int
    media_type: str
    source_group: str
    relative_path: str
    original_name: str
    extension: str
    size_bytes: int
    file_mtime: str
    taken_sort: str
    taken_display: str
    date_source: str
    width: int | None
    height: int | None
    duration_s: float | None
    has_gps: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only intake catalog for family memory film projects.")
    parser.add_argument("--source", required=True, type=Path, help="Source media folder, read-only.")
    parser.add_argument("--out", required=True, type=Path, help="Private output folder for manifests and summaries.")
    parser.add_argument("--project-name", required=True, help="Human project name for summary files.")
    return parser.parse_args()


def iso_from_timestamp(value: float) -> str:
    return datetime.fromtimestamp(value).isoformat(timespec="seconds")


def display_from_iso(value: str) -> str:
    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return value


def image_exif(path: Path) -> tuple[str | None, bool, int | None, int | None]:
    try:
        with Image.open(path) as image:
            width, height = image.size
            raw_exif = image.getexif()
            if not raw_exif:
                return None, False, width, height

            exif: dict[str, Any] = {}
            for key, value in raw_exif.items():
                name = ExifTags.TAGS.get(key, key)
                exif[str(name)] = value

            date_value = exif.get("DateTimeOriginal") or exif.get("DateTimeDigitized") or exif.get("DateTime")
            taken = None
            if isinstance(date_value, str):
                for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                    try:
                        taken = datetime.strptime(date_value, fmt).isoformat(timespec="seconds")
                        break
                    except ValueError:
                        pass

            gps_info = raw_exif.get_ifd(ExifTags.IFD.GPSInfo) if hasattr(raw_exif, "get_ifd") else {}
            return taken, bool(gps_info), width, height
    except Exception:
        return None, False, None, None


def ffprobe(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:format_tags=creation_time:stream=width,height",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def video_metadata(path: Path) -> tuple[str | None, int | None, int | None, float | None]:
    try:
        probe = ffprobe(path)
    except Exception:
        return None, None, None, None

    taken = None
    raw_creation = probe.get("format", {}).get("tags", {}).get("creation_time")
    if raw_creation:
        try:
            taken = datetime.fromisoformat(raw_creation.replace("Z", "+00:00")).astimezone().replace(tzinfo=None).isoformat(timespec="seconds")
        except ValueError:
            taken = None

    duration = None
    raw_duration = probe.get("format", {}).get("duration")
    if raw_duration:
        try:
            duration = float(raw_duration)
        except ValueError:
            duration = None

    width = None
    height = None
    for stream in probe.get("streams", []):
        if stream.get("width") and stream.get("height"):
            width = int(stream["width"])
            height = int(stream["height"])
            break
    return taken, width, height, duration


def media_type_for(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTS:
        return "photo"
    if suffix in VIDEO_EXTS:
        return "video"
    return None


def collect(source: Path) -> list[MediaItem]:
    items: list[MediaItem] = []
    raw_paths = [path for path in source.rglob("*") if path.is_file() and media_type_for(path)]
    for path in sorted(raw_paths):
        media_type = media_type_for(path)
        assert media_type is not None
        stat = path.stat()
        taken = None
        has_gps = False
        width = None
        height = None
        duration = None

        if media_type == "photo":
            taken, has_gps, width, height = image_exif(path)
        else:
            taken, width, height, duration = video_metadata(path)

        date_source = "metadata"
        if taken is None:
            taken = iso_from_timestamp(stat.st_mtime)
            date_source = "file_mtime"

        relative = path.relative_to(source)
        source_group = relative.parts[0] if len(relative.parts) > 1 else source.name
        items.append(
            MediaItem(
                index=0,
                media_type=media_type,
                source_group=source_group,
                relative_path=str(relative),
                original_name=path.name,
                extension=path.suffix.lower(),
                size_bytes=stat.st_size,
                file_mtime=iso_from_timestamp(stat.st_mtime),
                taken_sort=taken,
                taken_display=display_from_iso(taken),
                date_source=date_source,
                width=width,
                height=height,
                duration_s=duration,
                has_gps=has_gps,
            )
        )

    items.sort(key=lambda item: (item.taken_sort, item.relative_path))
    return [item.__class__(**{**item.__dict__, "index": index}) for index, item in enumerate(items, 1)]


def write_manifest(out: Path, items: list[MediaItem]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    fields = [
        "index",
        "media_type",
        "source_group",
        "taken",
        "date_source",
        "relative_path",
        "original_name",
        "extension",
        "size_mb",
        "width",
        "height",
        "duration_s",
        "has_gps",
        "file_mtime",
    ]
    with (out / "media_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "index": f"{item.index:05d}",
                    "media_type": item.media_type,
                    "source_group": item.source_group,
                    "taken": item.taken_display,
                    "date_source": item.date_source,
                    "relative_path": item.relative_path,
                    "original_name": item.original_name,
                    "extension": item.extension,
                    "size_mb": f"{item.size_bytes / 1024 / 1024:.1f}",
                    "width": item.width or "",
                    "height": item.height or "",
                    "duration_s": f"{item.duration_s:.2f}" if item.duration_s is not None else "",
                    "has_gps": "yes" if item.has_gps else "no",
                    "file_mtime": display_from_iso(item.file_mtime),
                }
            )


def write_summaries(out: Path, project_name: str, source: Path, items: list[MediaItem]) -> None:
    by_source = Counter(item.source_group for item in items)
    by_type = Counter(item.media_type for item in items)
    by_ext = Counter(item.extension for item in items)
    by_day: dict[str, list[MediaItem]] = defaultdict(list)
    for item in items:
        by_day[item.taken_display[:10]].append(item)

    with (out / "summary_by_source.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source_group", "files", "photos", "videos", "size_gb"])
        for source_group, count in sorted(by_source.items()):
            group_items = [item for item in items if item.source_group == source_group]
            writer.writerow(
                [
                    source_group,
                    count,
                    sum(1 for item in group_items if item.media_type == "photo"),
                    sum(1 for item in group_items if item.media_type == "video"),
                    f"{sum(item.size_bytes for item in group_items) / 1024 / 1024 / 1024:.2f}",
                ]
            )

    with (out / "timeline_by_day.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["day", "files", "photos", "videos", "size_gb", "first_taken", "last_taken"])
        for day, day_items in sorted(by_day.items()):
            writer.writerow(
                [
                    day,
                    len(day_items),
                    sum(1 for item in day_items if item.media_type == "photo"),
                    sum(1 for item in day_items if item.media_type == "video"),
                    f"{sum(item.size_bytes for item in day_items) / 1024 / 1024 / 1024:.2f}",
                    day_items[0].taken_display,
                    day_items[-1].taken_display,
                ]
            )

    total_size_gb = sum(item.size_bytes for item in items) / 1024 / 1024 / 1024
    first = items[0].taken_display if items else ""
    last = items[-1].taken_display if items else ""
    text = f"""# {project_name} - intake status

Zdroj: `{source}`
Vystup: `{out}`

## Stav prvniho read-only katalogu

- Celkem souboru: {len(items)}
- Fotky: {by_type.get("photo", 0)}
- Videa: {by_type.get("video", 0)}
- Velikost podle katalogu: {total_size_gb:.2f} GiB
- Casove rozpeti podle metadat / mtime fallbacku: {first} az {last}
- Soubory s GPS u fotek: {sum(1 for item in items if item.has_gps)}

## Zdroje

"""
    for source_group, count in sorted(by_source.items()):
        text += f"- `{source_group}`: {count} souboru\n"
    text += "\n## Pripony\n\n"
    for extension, count in sorted(by_ext.items()):
        text += f"- `{extension}`: {count}\n"
    text += "\n## Vystupy\n\n"
    text += "- `media_manifest.csv` - kompletni katalog souboru\n"
    text += "- `summary_by_source.csv` - souhrn podle puvodnich zdrojovych slozek\n"
    text += "- `timeline_by_day.csv` - prvni chronologicke bloky po dnech\n"
    text += "\n## Bezpecnost\n\n"
    text += "- Skript necisti, nemaze a neprejmenovava originaly.\n"
    text += "- Vystupy patri do `data/private/` a nepatri do gitu.\n"
    (out / "README_STATUS.md").write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    source = args.source.expanduser().resolve()
    out = args.out
    if not source.exists():
        raise FileNotFoundError(source)
    items = collect(source)
    write_manifest(out, items)
    write_summaries(out, args.project_name, source, items)
    print(f"items={len(items)}")
    print(out / "media_manifest.csv")
    print(out / "README_STATUS.md")


if __name__ == "__main__":
    main()
