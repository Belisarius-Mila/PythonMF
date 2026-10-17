#!/usr/bin/env python3
"""Run only a previously authorized, frozen Luna release job."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.communication.luna_release import run_release


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    return 0 if run_release(args.job_id)["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
