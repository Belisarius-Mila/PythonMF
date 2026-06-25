from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.lekarna.auto_import import build_auto_import_draft  # noqa: E402
from app.lekarna.openai_vision import DEFAULT_OPENAI_VISION_MODEL  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an automatic draft for home pharmacy photo import.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    draft = subparsers.add_parser("draft", help="Find recent Downloads photos, OCR them and prepare a draft manifest.")
    draft.add_argument("--downloads-dir", default=str(Path.home() / "Downloads"))
    draft.add_argument("--limit", type=int, default=10)
    draft.add_argument("--manifest", help="Optional output CSV manifest path.")
    draft.add_argument("--report", help="Optional output Markdown report path.")
    draft.add_argument("--no-ocr", action="store_true", help="Skip OCR and create only filename-based draft.")
    draft.add_argument(
        "--ocr-backend",
        choices=("macos", "openai"),
        default="macos",
        help="OCR/vision backend for reading medicine-box labels.",
    )
    draft.add_argument("--model", default=DEFAULT_OPENAI_VISION_MODEL, help="OpenAI model for --ocr-backend openai.")

    args = parser.parse_args()
    if args.command == "draft":
        load_dotenv(PROJECT_ROOT / ".env", override=True)
        result = build_auto_import_draft(
            downloads_dir=Path(args.downloads_dir),
            limit=args.limit,
            manifest_path=Path(args.manifest) if args.manifest else None,
            report_path=Path(args.report) if args.report else None,
            run_ocr=not args.no_ocr,
            ocr_backend=args.ocr_backend,
            ocr_model=args.model,
        )
        print(f"manifest={result.manifest_path}")
        print(f"report={result.report_path}")
        print(f"photos={result.photos}")
        print(f"new_candidates={result.new_candidates}")
        print(f"duplicate_existing={result.duplicate_existing}")
        print(f"needs_review={result.needs_review}")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
