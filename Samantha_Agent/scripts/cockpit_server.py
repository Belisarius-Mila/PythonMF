from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.cockpit import COCKPIT_PORT, run_cockpit_server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Spusti lokalni Samantha Cockpit.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=COCKPIT_PORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_cockpit_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
