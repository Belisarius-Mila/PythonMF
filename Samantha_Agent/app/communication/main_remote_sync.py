"""Read-only audit and confirmed fast-forward of a clean local ``main``.

The remote branch is authoritative only when the local repository is clean,
has no local commits, and can move by a plain fast-forward.  The apply step is
bound to the exact remote commit returned by the preceding audit and refreshes
the remote reference again before changing the working tree.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from app.codex_appserver import AppServerError


_HEAD_RE = re.compile(r"[0-9a-f]{40}")
_SYNC_LOCK_TIMEOUT_SECONDS = 120.0


class MainRemoteSyncError(AppServerError):
    """Raised when a local ``main`` cannot be safely fast-forwarded."""


@dataclass(frozen=True)
class MainRemoteSyncPlan:
    local_head: str
    origin_head: str
    commit_count: int
    changes: tuple[dict[str, str], ...]

    def public_dict(self) -> dict[str, Any]:
        preview = self.changes[:80]
        return {
            "ok": True,
            "read_only": True,
            "writes_performed": False,
            "state": "fast_forward_available",
            "can_fast_forward": True,
            "local_head": self.local_head,
            "local_short": self.local_head[:12],
            "origin_head": self.origin_head,
            "origin_short": self.origin_head[:12],
            "commit_count": self.commit_count,
            "change_count": len(self.changes),
            "changes": [dict(item) for item in preview],
            "changes_truncated": len(preview) < len(self.changes),
            "operation": "main_remote_sync_audit",
            "will_merge": False,
            "will_rebase": False,
            "will_rewrite_history": False,
        }


def _git(
    repo: Path,
    args: Sequence[str],
    *,
    timeout: float = _SYNC_LOCK_TIMEOUT_SECONDS,
) -> str:
    completed = subprocess.run(
        ["/usr/bin/git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise MainRemoteSyncError(
            detail or f"Git operace selhala: {' '.join(args)}"
        )
    return completed.stdout.strip()


def _is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    completed = subprocess.run(
        [
            "/usr/bin/git",
            "-C",
            str(repo),
            "merge-base",
            "--is-ancestor",
            ancestor,
            descendant,
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return completed.returncode == 0


def _refresh_origin_main(repo: Path) -> str:
    try:
        _git(
            repo,
            [
                "fetch",
                "--no-tags",
                "origin",
                "refs/heads/main:refs/remotes/origin/main",
            ],
        )
        return _git(repo, ["rev-parse", "origin/main"]).casefold()
    except MainRemoteSyncError as exc:
        raise MainRemoteSyncError(
            "Nelze načíst aktuální origin/main z GitHubu."
        ) from exc


def _source_state(repo: Path) -> tuple[str, str]:
    branch = _git(repo, ["branch", "--show-current"])
    if branch != "main":
        raise MainRemoteSyncError(
            "Ruční dorovnání je dostupné pouze na lokální větvi main."
        )
    pending = _git(
        repo,
        ["status", "--porcelain=v1", "--untracked-files=all"],
    )
    if pending:
        raise MainRemoteSyncError(
            "Lokální main obsahuje pracovní změny; ruční dorovnání je zablokované."
        )
    local_head = _git(repo, ["rev-parse", "HEAD"]).casefold()
    if not _HEAD_RE.fullmatch(local_head):
        raise MainRemoteSyncError("Lokální main nemá platný commit.")
    return branch, local_head


def _incoming_changes(
    repo: Path,
    *,
    local_head: str,
    origin_head: str,
) -> tuple[dict[str, str], ...]:
    output = _git(
        repo,
        [
            "diff",
            "--name-status",
            "--find-renames",
            local_head,
            origin_head,
        ],
    )
    changes: list[dict[str, str]] = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) == 2:
            changes.append({"status": parts[0], "path": parts[1]})
            continue
        if len(parts) == 3:
            changes.append(
                {
                    "status": parts[0],
                    "path": parts[2],
                    "from_path": parts[1],
                }
            )
            continue
        if line:
            raise MainRemoteSyncError(
                "Příchozí Git změny mají neznámý formát; nic nedorovnávám."
            )
    return tuple(changes)


def audit_main_remote_sync(*, source_repo: Path) -> dict[str, Any]:
    """Refresh GitHub and return a read-only fast-forward plan or safe state."""

    repo = Path(source_repo).resolve()
    _branch, local_head = _source_state(repo)
    origin_head = _refresh_origin_main(repo)
    if not _HEAD_RE.fullmatch(origin_head):
        raise MainRemoteSyncError("Origin/main nemá platný commit.")
    if local_head == origin_head:
        return {
            "ok": True,
            "read_only": True,
            "writes_performed": False,
            "state": "aligned",
            "can_fast_forward": False,
            "local_head": local_head,
            "local_short": local_head[:12],
            "origin_head": origin_head,
            "origin_short": origin_head[:12],
            "commit_count": 0,
            "change_count": 0,
            "changes": [],
            "changes_truncated": False,
            "operation": "main_remote_sync_audit",
            "will_merge": False,
            "will_rebase": False,
            "will_rewrite_history": False,
        }
    if not _is_ancestor(repo, local_head, origin_head):
        local_ahead = _is_ancestor(repo, origin_head, local_head)
        return {
            "ok": True,
            "read_only": True,
            "writes_performed": False,
            "state": "local_ahead" if local_ahead else "diverged",
            "can_fast_forward": False,
            "local_head": local_head,
            "local_short": local_head[:12],
            "origin_head": origin_head,
            "origin_short": origin_head[:12],
            "commit_count": 0,
            "change_count": 0,
            "changes": [],
            "changes_truncated": False,
            "operation": "main_remote_sync_audit",
            "will_merge": False,
            "will_rebase": False,
            "will_rewrite_history": False,
        }
    commit_count = int(
        _git(repo, ["rev-list", "--count", f"{local_head}..{origin_head}"])
        or 0
    )
    if commit_count <= 0:
        raise MainRemoteSyncError(
            "GitHub je napřed, ale počet příchozích commitů nelze bezpečně ověřit."
        )
    return MainRemoteSyncPlan(
        local_head=local_head,
        origin_head=origin_head,
        commit_count=commit_count,
        changes=_incoming_changes(
            repo,
            local_head=local_head,
            origin_head=origin_head,
        ),
    ).public_dict()


def apply_main_remote_sync(
    *,
    source_repo: Path,
    expected_local_head: str,
    expected_origin_head: str,
    confirmed: bool,
) -> dict[str, Any]:
    """Apply the exact audited fast-forward after a fresh remote recheck."""

    if not confirmed:
        raise MainRemoteSyncError(
            "Ruční dorovnání main vyžaduje výslovné potvrzení."
        )
    expected_local = str(expected_local_head or "").strip().casefold()
    expected_origin = str(expected_origin_head or "").strip().casefold()
    if not _HEAD_RE.fullmatch(expected_local) or not _HEAD_RE.fullmatch(
        expected_origin
    ):
        raise MainRemoteSyncError(
            "Ruční dorovnání nemá platný auditovaný zdroj a cíl."
        )
    plan = audit_main_remote_sync(source_repo=source_repo)
    if (
        plan.get("state") != "fast_forward_available"
        or plan.get("can_fast_forward") is not True
    ):
        raise MainRemoteSyncError(
            "Aktuální stav už nenabízí jednoznačný fast-forward."
        )
    if (
        str(plan.get("local_head") or "") != expected_local
        or str(plan.get("origin_head") or "") != expected_origin
    ):
        raise MainRemoteSyncError(
            "Main nebo GitHub se od auditu změnil; spusť novou kontrolu."
        )
    repo = Path(source_repo).resolve()
    _git(repo, ["merge", "--ff-only", expected_origin])
    _branch, final_head = _source_state(repo)
    if final_head != expected_origin:
        raise MainRemoteSyncError(
            "Fast-forward skončil na jiném commitu; další operace jsou zablokované."
        )
    return {
        **plan,
        "ok": True,
        "read_only": False,
        "writes_performed": True,
        "state": "main_fast_forwarded",
        "can_fast_forward": False,
        "operation": "confirmed_main_remote_sync",
        "main_fast_forwarded": True,
        "main_head": final_head,
        "main_short": final_head[:12],
    }
