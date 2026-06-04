#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.documents.consistency_audit import (
    audit_result_to_json,
    format_document_consistency_audit,
    run_document_consistency_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only audit uložených dokumentů a reminders pro konflikty ve stejných pojistných věcech."
    )
    parser.add_argument("--vault-dir", type=Path, default=None)
    parser.add_argument("--reminders-path", type=Path, default=None)
    parser.add_argument("--json", action="store_true", help="Vypsat strojově čitelné JSON místo textového souhrnu.")
    args = parser.parse_args()

    kwargs = {}
    if args.vault_dir is not None:
        kwargs["vault_dir"] = args.vault_dir
    if args.reminders_path is not None:
        kwargs["reminders_path"] = args.reminders_path
    result = run_document_consistency_audit(**kwargs)
    if args.json:
        print(audit_result_to_json(result))
    else:
        print(format_document_consistency_audit(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
