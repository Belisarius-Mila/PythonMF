#!/usr/bin/env python3
"""Preview or apply the private legacy TVBCP migration without printing content."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.communication.legacy_tvbcp_migration import (
    MIGRATION_CONFIRMATION,
    LegacyTvbcpMigrationError,
    legacy_tvbcp_migration_status,
    migrate_legacy_tvbcp,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bezeztrátově převede starý private TVBCP do proudu Brainstorm / nápady."
    )
    parser.add_argument("--apply", action="store_true", help="Provést potvrzenou migraci.")
    parser.add_argument("--confirmation", default="", help="Přesná potvrzovací věta.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = (
            migrate_legacy_tvbcp(confirmation=args.confirmation)
            if args.apply
            else legacy_tvbcp_migration_status()
        )
    except (LegacyTvbcpMigrationError, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "message": str(exc)}, ensure_ascii=False))
        return 1
    if not args.apply:
        result["confirmation_text"] = MIGRATION_CONFIRMATION
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
