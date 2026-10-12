#!/usr/bin/env python3
"""Registered Mac-only film project operation, without a Camino restart."""
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.camino_film_workshop import camino_mac_film_project_action, camino_mac_film_project_status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "create"))
    parser.add_argument("--confirm-final-mac-data", action="store_true")
    args = parser.parse_args()
    if args.action == "create" and not args.confirm_final_mac_data:
        parser.error("create requires explicit confirmation of final Mac inputs for 2026-10-06")
    result = (camino_mac_film_project_action(confirmed=True) if args.action == "create"
              else camino_mac_film_project_status())
    print(json.dumps({k: v for k, v in result.items() if k not in ("shots", "project_id")},
                     ensure_ascii=False, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
