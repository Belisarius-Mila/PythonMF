#!/usr/bin/env python3
"""Audit and safely fast-forward one Human–Adam WIP checkpoint into main."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.codex_appserver import AppServerError
from app.communication.human_adam_workspace import (
    MAX_SAFE_DELETED_PATHS_PER_STEP,
    SAFE_CHECKPOINT_CHANGE_TYPES,
    HumanAdamWorkspaceManager,
)


CONFIRMATION_TEXT = "POTVRZUJI PREVZETI HUMAN-ADAM WIP DO MAIN"


class TakeoverError(RuntimeError):
    """Raised when the checkpoint cannot be taken over by an exact fast-forward."""


@dataclass(frozen=True)
class TakeoverPlan:
    source_head: str
    checkpoint_head: str
    checkpoint_parent: str
    checkpoint_subject: str
    changes: tuple[dict[str, str], ...]
    source_untracked_count: int

    def public_dict(self) -> dict[str, Any]:
        return {
            "ok": True,
            "ready": True,
            "operation": "exact_fast_forward",
            "source_head": self.source_head[:12],
            "checkpoint_head": self.checkpoint_head[:12],
            "checkpoint_parent": self.checkpoint_parent[:12],
            "checkpoint_subject": self.checkpoint_subject,
            "change_count": len(self.changes),
            "changes": [dict(item) for item in self.changes],
            "source_untracked_count": self.source_untracked_count,
            "will_create_merge_commit": False,
            "will_rewrite_history": False,
        }


def _git(cwd: Path, args: Sequence[str], *, timeout: float = 120.0) -> str:
    completed = subprocess.run(
        ["/usr/bin/git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise TakeoverError(detail or f"Git operace selhala: {' '.join(args)}")
    return completed.stdout.strip()


def _source_pending(source_repo: Path) -> tuple[list[str], list[str]]:
    output = _git(source_repo, ["status", "--porcelain=v1", "--untracked-files=all"])
    tracked: list[str] = []
    untracked: list[str] = []
    for line in output.splitlines():
        if line.startswith("?? "):
            untracked.append(line[3:])
        elif line:
            tracked.append(line)
    return tracked, untracked


def refresh_origin_main(source_repo: Path) -> str:
    """Refresh and return the live origin/main without changing the working tree."""
    try:
        _git(
            source_repo,
            ["fetch", "--no-tags", "origin", "refs/heads/main:refs/remotes/origin/main"],
        )
        return _git(source_repo, ["rev-parse", "origin/main"])
    except TakeoverError as exc:
        raise TakeoverError("Nelze obnovit aktuální stav origin/main z GitHubu.") from exc


def build_takeover_plan(
    *,
    workspace: HumanAdamWorkspaceManager | None = None,
    allow_source_ahead_of_origin: bool = False,
) -> TakeoverPlan:
    manager = workspace or HumanAdamWorkspaceManager()
    source_repo = manager.source_repo
    status = manager.status()
    if status.get("workspace_relation") != "local_ahead":
        raise TakeoverError("Izolovaný workspace nemá lokální WIP checkpoint připravený k převzetí.")
    if int(status.get("local_commit_count") or 0) != 1:
        raise TakeoverError("Převzetí zatím podporuje přesně jeden lokální WIP commit.")
    if status.get("dirty") or status.get("remotes"):
        raise TakeoverError("Izolovaný workspace musí být čistý a bez Git remote.")
    if status.get("branch") != "main":
        raise TakeoverError("Izolovaný WIP musí být na větvi main.")

    tracked_pending, untracked_pending = _source_pending(source_repo)
    if tracked_pending:
        raise TakeoverError("Živý main obsahuje staged nebo tracked změny; převzetí je zablokované.")
    if _git(source_repo, ["branch", "--show-current"]) != "main":
        raise TakeoverError("Živý repozitář není na větvi main.")

    source_head = _git(source_repo, ["rev-parse", "HEAD"])
    try:
        origin_head = _git(source_repo, ["rev-parse", "origin/main"])
    except TakeoverError as exc:
        raise TakeoverError("Nelze ověřit lokální referenci origin/main.") from exc
    if source_head != origin_head and not allow_source_ahead_of_origin:
        raise TakeoverError("Lokální main a známý origin/main se neshodují; nejdřív obnov vzdálený stav.")

    checkpoint_head = _git(manager.workspace_root, ["rev-parse", "HEAD"])
    checkpoint_parent = _git(manager.workspace_root, ["rev-parse", "HEAD^"])
    checkpoint_subject = _git(manager.workspace_root, ["log", "-1", "--format=%s"])
    if checkpoint_parent != source_head:
        raise TakeoverError("WIP checkpoint není přímým potomkem aktuálního main.")

    _git(manager.workspace_root, ["diff", "--check", "HEAD^", "HEAD"])
    diff_text = _git(
        manager.workspace_root,
        ["diff", "--name-status", "--find-renames", "HEAD^", "HEAD"],
    )
    changes: list[dict[str, str]] = []
    deletion_count = 0
    for line in diff_text.splitlines():
        parts = line.split("\t")
        if (
            len(parts) != 2
            or parts[0][:1] not in SAFE_CHECKPOINT_CHANGE_TYPES
        ):
            raise TakeoverError("Checkpoint obsahuje přejmenování nebo netypickou změnu.")
        path = parts[1]
        if not manager.checkpoint_path_allowed(path):
            raise TakeoverError(
                "Checkpoint obsahuje blokovanou soukromou, env, balíkovou "
                "nebo příliš velkou mediální cestu."
            )
        if parts[0][:1] == "D":
            deletion_count += 1
        changes.append({"status": parts[0], "path": path})
    if not changes:
        raise TakeoverError("Checkpoint neobsahuje žádnou převzatelnou změnu.")
    if deletion_count > MAX_SAFE_DELETED_PATHS_PER_STEP:
        raise TakeoverError(
            "Checkpoint obsahuje hromadné mazání; převzetí vyžaduje servisní potvrzení."
        )

    return TakeoverPlan(
        source_head=source_head,
        checkpoint_head=checkpoint_head,
        checkpoint_parent=checkpoint_parent,
        checkpoint_subject=checkpoint_subject,
        changes=tuple(changes),
        source_untracked_count=len(untracked_pending),
    )


def apply_takeover(
    *,
    confirmation: str,
    push: bool,
    defer_remote_push: bool = False,
    workspace: HumanAdamWorkspaceManager | None = None,
    progress_callback: Callable[[str, str], None] | None = None,
) -> dict[str, Any]:
    if str(confirmation or "").strip() != CONFIRMATION_TEXT:
        raise TakeoverError(f"Chybí přesná potvrzovací věta: {CONFIRMATION_TEXT}")
    manager = workspace or HumanAdamWorkspaceManager()
    if push and defer_remote_push:
        raise TakeoverError("Push nelze současně provést a odložit.")
    plan = build_takeover_plan(
        workspace=manager,
        allow_source_ahead_of_origin=defer_remote_push,
    )
    source_repo = manager.source_repo

    live_source_head = _git(source_repo, ["rev-parse", "HEAD"])
    if live_source_head != plan.source_head:
        raise TakeoverError(
            "Lokální main se během kontroly změnil; převzetí zopakuj."
        )
    if push:
        if progress_callback is not None:
            progress_callback("remote_recheck", "running")
        live_origin_head = refresh_origin_main(source_repo)
        if live_origin_head != plan.source_head:
            raise TakeoverError(
                "GitHub main se během kontroly změnil; lokální main zůstal beze změny. "
                "Nejdřív obnov main a potom vytvoř nový checkpoint."
            )
        if progress_callback is not None:
            progress_callback("remote_recheck", "passed")
    elif defer_remote_push:
        # Daytime local main is authoritative.  The ref must exist for the
        # later batch audit, but its relationship must not block another local
        # checkpoint after an evening audit discovered remote divergence.
        _git(source_repo, ["rev-parse", "origin/main"])
    else:
        raise TakeoverError(
            "Lokální převzetí bez pushnutí vyžaduje výslovně zapnutý dávkový režim."
        )

    _git(source_repo, ["fetch", "--no-tags", str(manager.workspace_root), "refs/heads/main"])
    fetched_head = _git(source_repo, ["rev-parse", "FETCH_HEAD"])
    if fetched_head != plan.checkpoint_head:
        raise TakeoverError("Lokální fetch vrátil jiný checkpoint; nic nepřebírám.")
    refreshed = build_takeover_plan(
        workspace=manager,
        allow_source_ahead_of_origin=defer_remote_push,
    )
    if refreshed != plan:
        raise TakeoverError("Stav se během kontroly změnil; převzetí zopakuj.")

    _git(source_repo, ["diff", "--check", "HEAD", "FETCH_HEAD"])
    pushed = False
    if push:
        if progress_callback is not None:
            progress_callback("push", "running")
        # Push the audited object before moving local main. If another writer (for
        # example the daily owl workflow) wins the race, Git rejects this update
        # and the user's local main remains untouched.
        _git(source_repo, ["push", "origin", "FETCH_HEAD:refs/heads/main"])
        pushed = True
        if progress_callback is not None:
            progress_callback("push", "passed")
    if progress_callback is not None:
        progress_callback("fast_forward", "running")
    _git(source_repo, ["merge", "--ff-only", "FETCH_HEAD"])
    if progress_callback is not None:
        progress_callback("fast_forward", "passed")
    if progress_callback is not None:
        progress_callback("workspace_alignment", "running")
    sync = manager.sync_from_main(confirmed=True)
    if sync.get("head") != sync.get("source_head") or sync.get("dirty") or sync.get("remotes"):
        raise TakeoverError("Checkpoint je převzatý, ale závěrečná kontrola workspace není čistá.")
    if progress_callback is not None:
        progress_callback("workspace_alignment", "passed")
    return {
        **plan.public_dict(),
        "applied": True,
        "pushed": pushed,
        "remote_push_deferred": bool(defer_remote_push and not pushed),
        "workspace_aligned": True,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit = subparsers.add_parser("audit", help="Jen ověřit a vypsat bezpečný plán.")
    audit.add_argument("--json", action="store_true")
    apply = subparsers.add_parser("apply", help="Potvrzeně převzít přesným fast-forwardem.")
    apply.add_argument("--confirm", required=True)
    apply.add_argument("--push", action="store_true")
    apply.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "audit":
            result = build_takeover_plan().public_dict()
        else:
            result = apply_takeover(confirmation=args.confirm, push=bool(args.push))
    except (TakeoverError, AppServerError, OSError, ValueError) as exc:
        result = {"ok": False, "ready": False, "message": str(exc)}
        print(json.dumps(result, ensure_ascii=False, indent=2) if getattr(args, "json", False) else result["message"])
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2) if getattr(args, "json", False) else _format_text(result))
    return 0


def _format_text(result: dict[str, Any]) -> str:
    lines = [
        "Human–Adam takeover:",
        f"- checkpoint: {result.get('checkpoint_head')}",
        f"- rodič/main: {result.get('source_head')}",
        f"- změny: {result.get('change_count')}",
    ]
    lines.extend(f"  {item['status']} {item['path']}" for item in result.get("changes") or [])
    if result.get("applied"):
        lines.append(f"- převzato: ano; push: {'ano' if result.get('pushed') else 'ne'}")
    else:
        lines.append("- režim: audit, nic nezměněno")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
