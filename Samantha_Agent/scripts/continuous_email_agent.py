#!/usr/bin/env python3
"""Read-only status and isolated acceptance tests; no live activation entry point."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.email.continuous_agent import ContinuousEmailAgent


def main() -> int:
    parser = argparse.ArgumentParser(description="Průběžný e-mailový agent: stav / syntetická přejímka.")
    parser.add_argument("command", choices=("status", "synthetic-test"))
    args = parser.parse_args()
    if args.command == "synthetic-test":
        return subprocess.run(
            [sys.executable, "-m", "unittest", "tests.test_continuous_email_agent", "-q"],
            cwd=PROJECT_ROOT, check=False,
        ).returncode
    state = ContinuousEmailAgent().status()
    print(json.dumps({
        "activation": "not_installed",
        "items": dict(Counter(item["status"] for item in state["items"].values())),
        "sources": [{"health": item.get("health", "unchecked"), "checked_at": item.get("checked_at", "")}
                    for item in state["sources"].values()],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
