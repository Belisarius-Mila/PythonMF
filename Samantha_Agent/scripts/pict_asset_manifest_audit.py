#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.pict_asset_manifest import (  # noqa: E402
    DEFAULT_MAPPING_PATH,
    DEFAULT_PICT_DIR,
    DEFAULT_VOCABULARY_PATHS,
    build_asset_manifest_preview,
    default_preview_output_path,
    default_review_output_path,
    write_manifest_preview,
    write_manifest_review,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Vytvori read-only preview asset manifestu pro Pict slovnikove obrazky."
    )
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING_PATH)
    parser.add_argument("--pict-dir", type=Path, default=DEFAULT_PICT_DIR)
    parser.add_argument("--vocabulary", type=Path, action="append", default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--review-output", type=Path, default=None)
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--no-review", action="store_true")
    parser.add_argument("--max-review-rows", type=int, default=200)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    vocabulary_paths = tuple(args.vocabulary) if args.vocabulary else DEFAULT_VOCABULARY_PATHS
    preview = build_asset_manifest_preview(
        mapping_path=args.mapping,
        pict_dir=args.pict_dir,
        vocabulary_paths=vocabulary_paths,
    )
    if not args.no_write:
        output_path = args.output or default_preview_output_path()
        write_manifest_preview(preview, output_path)
        print(f"Preview ulozen: {output_path}")
        if not args.no_review:
            review_output_path = args.review_output or default_review_output_path()
            write_manifest_review(preview, review_output_path, max_rows=args.max_review_rows)
            print(f"Review ulozen: {review_output_path}")
    print(json.dumps(preview["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
