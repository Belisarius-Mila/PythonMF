#!/usr/bin/env python3
"""Read-only audit of temporary development branches and worktrees."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.development_branch_lifecycle import DevelopmentBranchAuditor


def format_text(payload: dict[str, Any]) -> str:
    lines = [
        "Audit životního cyklu vývojových větví:",
        f"- větve: {payload.get('branch_count', 0)}",
        f"- aktivní worktrees: {payload.get('active_worktree_count', 0)}",
        f"- kandidáti k potvrzenému úklidu: {payload.get('cleanup_candidate_count', 0)}",
        f"- vyžaduje revizi: {payload.get('needs_review_count', 0)}",
    ]
    for item in payload.get("branches") or []:
        lines.append(
            f"  {item.get('name')} · {item.get('classification')} · {item.get('reason')}"
        )
    lines.append("- režim: read-only; žádné Git reference ani worktrees se nezměnily")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--repo-root", type=Path, default=PROJECT_ROOT.parent)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = DevelopmentBranchAuditor(repo_root=args.repo_root).audit()
    except (OSError, RuntimeError, ValueError) as exc:
        payload = {"ok": False, "mode": "read_only", "message": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else str(exc))
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else format_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
