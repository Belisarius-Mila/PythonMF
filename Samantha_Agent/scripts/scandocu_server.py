from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.documents.scandocu import DEFAULT_DOWNLOADS_DIR, run_scandocu_server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Spusti lokalni ScanDocu web pro kontrolu PDF z Downloads.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--downloads-dir", default=str(DEFAULT_DOWNLOADS_DIR))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_scandocu_server(
        host=args.host,
        port=args.port,
        downloads_dir=Path(args.downloads_dir).expanduser(),
    )


if __name__ == "__main__":
    main()
