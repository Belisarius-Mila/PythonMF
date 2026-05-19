from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.lekarna.photo_import import (
    APPLY_CONFIRMATION_PHRASE,
    apply_lekarna_photo_import_manifest,
    prepare_lekarna_photo_import_manifest,
    validate_lekarna_photo_sources,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare, apply, or validate the home pharmacy photo import."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare", help="Create a CSV manifest for new medicine photos.")
    prepare_parser.add_argument("--manifest", help="Optional output manifest path.")

    apply_parser = subparsers.add_parser("apply", help="Apply a reviewed manifest.")
    apply_parser.add_argument("--manifest", required=True, help="Path to the reviewed CSV manifest.")
    apply_parser.add_argument(
        "--confirm",
        required=True,
        help=f"Required confirmation text containing: {APPLY_CONFIRMATION_PHRASE}",
    )

    subparsers.add_parser("validate", help="Validate that CSV photo sources exist.")

    args = parser.parse_args()
    if args.command == "prepare":
        manifest_path = Path(args.manifest) if args.manifest else None
        result = prepare_lekarna_photo_import_manifest(manifest_path=manifest_path)
        print(result.message)
        print(f"manifest={result.manifest_path}")
        print(f"rows={result.rows}")
        return 0

    if args.command == "apply":
        result = apply_lekarna_photo_import_manifest(
            manifest_path=Path(args.manifest),
            user_confirmed=True,
            confirmation_text=args.confirm,
        )
        print(f"renamed={result.renamed_count}")
        print(f"appended={result.appended_count}")
        print(f"backup={result.backup_path}")
        print(f"report={result.report_path}")
        for warning in result.warnings:
            print(f"warning={warning}")
        return 0

    missing = validate_lekarna_photo_sources()
    print(f"missing_sources={len(missing)}")
    for source in missing:
        print(source)
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
