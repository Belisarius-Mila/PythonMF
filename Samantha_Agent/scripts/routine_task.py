#!/usr/bin/env python3
"""Fixed routine pilot; default previews routing without a model call."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.routine_tasks import TASK, route_routine_task, run_routine_task


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-confirmed", action="store_true")
    args = parser.parse_args()
    result = run_routine_task(TASK, confirmed=True) if args.run_confirmed else route_routine_task(TASK)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("state") == "completed" or not args.run_confirmed else 1


if __name__ == "__main__":
    raise SystemExit(main())
