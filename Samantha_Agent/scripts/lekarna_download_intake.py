#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.lekarna.download_intake import (  # noqa: E402
    DEFAULT_DOWNLOADS_DIR,
    build_download_photo_intake,
    default_download_intake_report_path,
    find_recent_download_photos,
    write_download_photo_intake_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only intake report for new pharmacy photos in Downloads.")
    parser.add_argument("--downloads-dir", type=Path, default=DEFAULT_DOWNLOADS_DIR)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument(
        "--label",
        action="append",
        default=[],
        help="Observed label in the form IMG_0001.JPG=Product name. Repeat for multiple photos.",
    )
    parser.add_argument("--report", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    labels = parse_labels(args.label)
    photos = find_recent_download_photos(downloads_dir=args.downloads_dir, limit=args.limit)
    intake = build_download_photo_intake(photos=photos, observed_labels=labels)
    report_path = args.report or default_download_intake_report_path()
    write_download_photo_intake_report(intake, report_path)
    print(f"Report ulozen: {report_path}")
    print(f"photos={intake['summary']['photos']}")
    for action, count in sorted(intake["summary"]["action_counts"].items()):
        print(f"{action}={count}")
    return 0


def parse_labels(raw_labels: list[str]) -> dict[str, str]:
    labels: dict[str, str] = {}
    for raw in raw_labels:
        if "=" not in raw:
            raise ValueError(f"Label musi mit tvar soubor=nazev: {raw}")
        name, label = raw.split("=", 1)
        labels[name.strip()] = label.strip()
    return labels


if __name__ == "__main__":
    raise SystemExit(main())
