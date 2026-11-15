#!/usr/bin/env python3
"""Run the same server-owned validation policy locally, without publication."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.communication.checkpoint_quality_gate import run_checkpoint_quality_gate
from app.communication.human_adam_workspace import HumanAdamWorkspaceManager
from app.communication.validation_policy import ValidationReceiptStore, git


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="Compare the complete candidate to this Git revision (default origin/main).")
    parser.add_argument('--full', action='store_true', help='Explicitly run the complete regression, bypassing cache.')
    args = parser.parse_args(argv)
    repo = Path(git(PROJECT_ROOT, "rev-parse", "--show-toplevel").decode().strip())
    workspace = HumanAdamWorkspaceManager(source_repo=repo, workspace_root=repo)
    store = ValidationReceiptStore(repo)
    log_path = store.root.parent / "samantha-validation-gate.log"
    print("Ověřuji programovou politiku a přesné vstupy; výsledek se zapíše do soukromé účtenky.", flush=True)
    evidence = run_checkpoint_quality_gate(workspace=workspace, log_path=log_path, validation_base=args.base,
                                          full_suite=args.full)
    print(json.dumps(evidence.public_dict(), ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
