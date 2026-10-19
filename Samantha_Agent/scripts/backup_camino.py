#!/usr/bin/env python3
"""Registered encrypted Camino supplement; public output contains aggregates only."""
from pathlib import Path
import argparse
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.backup.camino import backup_camino


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    os.environ.setdefault('TAILSCALE_BE_CLI', '1')
    try:
        result = backup_camino(mode='execute' if args.execute else 'dry-run')
        # Identity digests stay in the encrypted manifest, alongside private filenames.
        print(json.dumps({k: v for k, v in result.items()
                          if k not in ('identity_sha256', 'trips_sha256')}, ensure_ascii=False))
        return 0 if result['state'] != 'not_configured' else 1
    except Exception as error:
        print(json.dumps({'ok': False, 'error_type': type(error).__name__,
                          'next': 'Inspect preserved backup and owned service status; never retry blindly.'}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
