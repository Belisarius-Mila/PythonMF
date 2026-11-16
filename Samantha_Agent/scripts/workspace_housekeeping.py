#!/usr/bin/env python3
"""Registered preview, retirement markers and opt-in hourly housekeeping."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.file_persistence import atomic_create_bytes, exclusive_file_lock
from app.worktree_cleanup import CONFIRMATION, GRACE_SECONDS, Housekeeping, LABEL, digest


def agent(project):
    return {"Label": LABEL,
            "ProgramArguments": [str(project / ".venv/bin/python"), str(project / "scripts/workspace_housekeeping.py"), "tick"],
            "WorkingDirectory": str(project), "StartInterval": 3600, "RunAtLoad": True,
            "ProcessType": "Background", "EnvironmentVariables": {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin"},
            "StandardOutPath": str(project / "data/private/workspace_housekeeping/service.stdout.log"),
            "StandardErrorPath": str(project / "data/private/workspace_housekeeping/service.stderr.log")}


def contract(housekeeping):
    sources = [PROJECT_ROOT / "app/worktree_cleanup.py", Path(__file__).resolve(),
               PROJECT_ROOT / "scripts/cleanup_session_autosave.py"]
    return {"schema": 1, "project": str(housekeeping.project), "worktrees": str(housekeeping.base),
            "scope": "explicitly retired direct data-* linked worktrees of this repository only",
            "protected": "main, permanent Data, Human-Adam profiles and all other roots",
            "unknown_ignored_data": "block", "branches": "preserve", "force": False,
            "autosave_keep": 12, "grace_seconds": GRACE_SECONDS, "interval_seconds": 3600,
            "sources": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}


def prepare(housekeeping):
    payload = contract(housekeeping)
    proposal = {"contract": payload, "sha256": digest(payload), "preview": housekeeping.preview()}
    housekeeping._write("proposal.json", proposal)
    return proposal


def activate(housekeeping, *, confirmation, proposal_sha256, agents=None, runner=subprocess.run):
    if confirmation != CONFIRMATION:
        raise ValueError("Missing exact global safety confirmation")
    with exclusive_file_lock(housekeeping.root / "activation-operation"):
        proposal = housekeeping._read("proposal.json", {})
        current = contract(housekeeping)
        if not proposal_sha256 or proposal.get("sha256") != proposal_sha256 or digest(current) != proposal_sha256:
            raise ValueError("Housekeeping proposal changed; prepare and approve the current contract")
        if housekeeping._read("activation.json", {}).get("attempted"):
            raise ValueError("Activation was already attempted; inspect that receipt, do not repeat")
        target = Path(agents or Path.home() / "Library/LaunchAgents") / (LABEL + ".plist")
        if target.parent.resolve() != target.parent:
            raise ValueError("Symlink LaunchAgents directory is preserved")
        if target.exists() or target.is_symlink():
            raise ValueError("Existing LaunchAgent is preserved")
        if not (housekeeping.project / ".venv/bin/python").is_file():
            raise ValueError("Project interpreter missing")
        job = f"gui/{os.getuid()}/{LABEL}"
        loaded = runner(["/bin/launchctl", "print", job], capture_output=True, timeout=30, check=False)
        if loaded.returncode == 0:
            raise ValueError("An existing loaded job is preserved")
        policy = {"enabled": False, "attempted": True, "proposal_sha256": proposal_sha256, "state": "installing"}
        housekeeping._write("activation.json", policy)
        try:
            atomic_create_bytes(target, plistlib.dumps(agent(housekeeping.project)))
            # Consent is durable before RunAtLoad can run. No existing service is stopped.
            policy.update(enabled=True, state="bootstrap_pending")
            housekeeping._write("activation.json", policy)
            result = runner(["/bin/launchctl", "bootstrap", f"gui/{os.getuid()}", str(target)],
                            capture_output=True, timeout=30, check=False)
            if result.returncode:
                raise ValueError("Bootstrap not confirmed")
            result = runner(["/bin/launchctl", "print", job], capture_output=True, timeout=30, check=False)
            if result.returncode:
                raise ValueError("Loaded job not confirmed")
            policy["state"] = "active"
        except (OSError, ValueError, subprocess.SubprocessError):
            policy.update(enabled=False, state="attention")
            housekeeping._write("activation.json", policy)
            raise ValueError("Activation needs review; no automatic retry") from None
        housekeeping._write("activation.json", policy)
        return policy


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("preview", "prepare", "activate", "retire", "cancel", "tick", "status", "prepare-v2", "activate-v2"))
    parser.add_argument("--name", default="")
    parser.add_argument("--head", default="")
    parser.add_argument("--confirmation", default="")
    parser.add_argument("--proposal-sha256", default="")
    parser.add_argument("--approval-ref", default="")
    parser.add_argument("--completed-name", action="append", default=[])
    args = parser.parse_args(argv)
    service = Housekeeping()
    try:
        if args.action == "preview":
            result = service.preview()
        elif args.action == "prepare":
            result = prepare(service)
        elif args.action == "activate":
            result = activate(service, confirmation=args.confirmation, proposal_sha256=args.proposal_sha256)
        elif args.action == "retire":
            result = service.retire(args.name, expected_head=args.head)
        elif args.action == "cancel":
            result = service.cancel(args.name)
        elif args.action == "tick":
            result = service.tick()
        elif args.action in {"prepare-v2", "activate-v2"}:
            from app.worktree_cleanup_v2 import PublishedCleanup
            cleaner = PublishedCleanup(service)
            result = cleaner.prepare(completed_names=args.completed_name) if args.action == "prepare-v2" else cleaner.activate(
                confirmation=args.confirmation, proposal_sha256=args.proposal_sha256, approval_ref=args.approval_ref)
        else:
            result = {"activation": service._read("activation.json", {"enabled": False}),
                      "latest": service._read("latest.json", {})}
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"state": "attention", "error": str(exc) if isinstance(exc, ValueError) else type(exc).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
