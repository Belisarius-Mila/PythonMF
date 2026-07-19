"""Read-only audit of temporary Git branches and linked worktrees."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
DEFAULT_ARCHIVE_PATH = PROJECT_ROOT / "memory" / "infrastructure" / "git_branch_archive.md"
GIT_BINARY = "/usr/bin/git"


class DevelopmentBranchAuditError(RuntimeError):
    """Raised when Git metadata cannot be audited without guessing."""


@dataclass(frozen=True)
class WorktreeState:
    branch: str
    head: str
    path: Path
    dirty: bool
    change_count: int
    status_ok: bool


class DevelopmentBranchAuditor:
    """Classify branch lifecycle state without changing refs or worktrees."""

    def __init__(
        self,
        *,
        repo_root: Path = REPO_ROOT,
        base_branch: str = "main",
        remote: str = "origin",
        archive_path: Path = DEFAULT_ARCHIVE_PATH,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.base_branch = str(base_branch or "").strip()
        self.remote = str(remote or "").strip()
        self.archive_path = Path(archive_path)
        if not self.base_branch or not self.remote:
            raise ValueError("Audit větví vyžaduje základní větev a Git remote.")

    def _git(
        self,
        args: Sequence[str],
        *,
        cwd: Path | None = None,
        allowed_returncodes: tuple[int, ...] = (0,),
    ) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [GIT_BINARY, "-C", str(cwd or self.repo_root), *args],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if completed.returncode not in allowed_returncodes:
            detail = (completed.stderr or completed.stdout).strip()
            raise DevelopmentBranchAuditError(
                detail or f"Git audit selhal: {' '.join(args)}"
            )
        return completed

    def _git_output(self, args: Sequence[str], *, cwd: Path | None = None) -> str:
        return self._git(args, cwd=cwd).stdout.strip()

    def _assert_repository(self) -> None:
        if self._git_output(["rev-parse", "--is-inside-work-tree"]) != "true":
            raise DevelopmentBranchAuditError("Auditovaný adresář není Git worktree.")
        self._git_output(["rev-parse", "--verify", self.base_branch])

    def _refs(self) -> list[dict[str, str]]:
        output = self._git_output(
            [
                "for-each-ref",
                "--format=%(refname)%00%(objectname)%00%(subject)%00%(symref)",
                "refs/heads",
                f"refs/remotes/{self.remote}",
            ]
        )
        rows: list[dict[str, str]] = []
        for raw_line in output.splitlines():
            parts = raw_line.split("\0")
            if len(parts) != 4:
                raise DevelopmentBranchAuditError("Git vrátil nečitelný seznam větví.")
            refname, head, subject, symref = parts
            if symref:
                continue
            if refname.startswith("refs/heads/"):
                scope = "local"
                name = refname.removeprefix("refs/heads/")
            elif refname.startswith(f"refs/remotes/{self.remote}/"):
                scope = "remote"
                name = refname.removeprefix("refs/remotes/")
            else:
                continue
            if name in {self.base_branch, f"{self.remote}/{self.base_branch}"}:
                continue
            rows.append(
                {
                    "refname": refname,
                    "name": name,
                    "scope": scope,
                    "head": head,
                    "subject": " ".join(subject.split())[:160],
                }
            )
        return rows

    @staticmethod
    def _parse_worktree_blocks(output: str) -> list[dict[str, str]]:
        blocks: list[dict[str, str]] = []
        current: dict[str, str] = {}
        for raw_line in (*output.splitlines(), ""):
            line = raw_line.strip()
            if not line:
                if current:
                    blocks.append(current)
                    current = {}
                continue
            key, _, value = line.partition(" ")
            current[key] = value.strip()
        return blocks

    def _worktrees(self) -> dict[str, WorktreeState]:
        output = self._git_output(["worktree", "list", "--porcelain"])
        states: dict[str, WorktreeState] = {}
        for block in self._parse_worktree_blocks(output):
            branch_ref = block.get("branch", "")
            if not branch_ref.startswith("refs/heads/"):
                continue
            branch = branch_ref.removeprefix("refs/heads/")
            path = Path(block.get("worktree", ""))
            if not path.is_absolute():
                continue
            status = self._git(
                ["status", "--porcelain=v1", "--untracked-files=all"],
                cwd=path,
                allowed_returncodes=(0, 1, 128),
            )
            status_ok = status.returncode == 0
            changes = tuple(line for line in status.stdout.splitlines() if line.strip())
            states[branch] = WorktreeState(
                branch=branch,
                head=block.get("HEAD", ""),
                path=path,
                dirty=bool(changes) or not status_ok,
                change_count=len(changes),
                status_ok=status_ok,
            )
        return states

    def _active_archived_branches(self) -> set[str]:
        try:
            text = self.archive_path.read_text(encoding="utf-8")
        except OSError:
            return set()
        active = False
        names: set[str] = set()
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if line == "## Aktivni archivovane neintegrovane vetve":
                active = True
                continue
            if active and line.startswith("## "):
                break
            if not active or not line.startswith("- `"):
                continue
            end = line.find("`", 3)
            if end > 3:
                names.add(line[3:end].strip())
        return names

    def _is_merged(self, refname: str) -> bool:
        completed = self._git(
            ["merge-base", "--is-ancestor", refname, self.base_branch],
            allowed_returncodes=(0, 1),
        )
        return completed.returncode == 0

    def _ahead_behind(self, refname: str) -> tuple[int, int]:
        output = self._git_output(
            ["rev-list", "--left-right", "--count", f"{self.base_branch}...{refname}"]
        )
        parts = output.split()
        if len(parts) != 2:
            raise DevelopmentBranchAuditError("Git nevrátil platný vztah větve k main.")
        return int(parts[1]), int(parts[0])

    def _patch_state(self, refname: str) -> tuple[int, int, int]:
        cherry = self._git_output(["cherry", self.base_branch, refname])
        plus = 0
        minus = 0
        for line in cherry.splitlines():
            if line.startswith("+ "):
                plus += 1
            elif line.startswith("- "):
                minus += 1
        merge_count_text = self._git_output(
            ["rev-list", "--count", "--merges", f"{self.base_branch}..{refname}"]
        )
        return plus, minus, int(merge_count_text or 0)

    @staticmethod
    def _classification(
        *,
        checked_out: bool,
        dirty: bool,
        status_ok: bool,
        archived: bool,
        merged: bool,
        patch_equivalent: bool,
    ) -> tuple[str, bool, str]:
        if checked_out:
            if not status_ok:
                return (
                    "unverified_worktree",
                    False,
                    "Připojený worktree nelze bezpečně přečíst; ruční kontrola je nutná.",
                )
            if dirty:
                return (
                    "active_dirty_worktree",
                    False,
                    "Připojený worktree obsahuje pracovní změny; větev je aktivní.",
                )
            return (
                "active_clean_worktree",
                False,
                "Větev je připojená k čistému worktree; audit ji automaticky neuzavírá.",
            )
        if archived:
            return (
                "archived",
                False,
                "Větev je vědomě vedená v aktivním archivu.",
            )
        if merged:
            return (
                "merged",
                True,
                "Celá historie větve je dosažitelná z main.",
            )
        if patch_equivalent:
            return (
                "patch_equivalent",
                True,
                "Všechny ne-main commity mají patchový ekvivalent v main.",
            )
        return (
            "needs_review",
            False,
            "Větev obsahuje jedinečný nebo neověřený commit a nesmí se automaticky uklidit.",
        )

    def audit(self) -> dict[str, Any]:
        self._assert_repository()
        worktrees = self._worktrees()
        archived_names = self._active_archived_branches()
        branches: list[dict[str, Any]] = []
        warnings: list[str] = []
        for row in self._refs():
            name = row["name"]
            refname = row["refname"]
            local_name = name if row["scope"] == "local" else ""
            worktree = worktrees.get(local_name)
            try:
                merged = self._is_merged(refname)
                ahead, behind = self._ahead_behind(refname)
                plus, minus, merge_count = self._patch_state(refname)
                patch_equivalent = bool(not merged and plus == 0 and minus > 0 and merge_count == 0)
                classification, cleanup_candidate, reason = self._classification(
                    checked_out=worktree is not None,
                    dirty=bool(worktree and worktree.dirty),
                    status_ok=bool(not worktree or worktree.status_ok),
                    archived=name in archived_names,
                    merged=merged,
                    patch_equivalent=patch_equivalent,
                )
            except (DevelopmentBranchAuditError, ValueError) as exc:
                merged = False
                ahead = 0
                behind = 0
                plus = 0
                minus = 0
                merge_count = 0
                classification = "unverified"
                cleanup_candidate = False
                reason = "Git vztah větve nelze bezpečně ověřit."
                warnings.append(f"{name}: {exc}")
            branches.append(
                {
                    "name": name,
                    "scope": row["scope"],
                    "head_short": row["head"][:12],
                    "subject": row["subject"],
                    "ahead": ahead,
                    "behind": behind,
                    "unique_patch_count": plus,
                    "integrated_patch_count": minus,
                    "merge_commit_count": merge_count,
                    "merged": merged,
                    "checked_out": worktree is not None,
                    "worktree_label": "pomocný worktree" if worktree else "",
                    "worktree_clean": bool(worktree and worktree.status_ok and not worktree.dirty),
                    "worktree_change_count": int(worktree.change_count if worktree else 0),
                    "archived": name in archived_names,
                    "classification": classification,
                    "cleanup_candidate": cleanup_candidate,
                    "reason": reason,
                }
            )
        branches.sort(key=lambda item: (item["scope"], item["name"]))
        return {
            "ok": True,
            "mode": "read_only",
            "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "base_branch": self.base_branch,
            "remote": self.remote,
            "network_refreshed": False,
            "branch_count": len(branches),
            "cleanup_candidate_count": sum(bool(item["cleanup_candidate"]) for item in branches),
            "needs_review_count": sum(
                item["classification"] in {"needs_review", "unverified", "unverified_worktree"}
                for item in branches
            ),
            "active_worktree_count": sum(bool(item["checked_out"]) for item in branches),
            "branches": branches,
            "warnings": warnings,
            "message": "Audit je pouze read-only; žádná větev ani worktree nebyly změněny.",
        }


def development_branch_audit_action(
    *,
    repo_root: Path = REPO_ROOT,
    archive_path: Path = DEFAULT_ARCHIVE_PATH,
) -> dict[str, Any]:
    try:
        return DevelopmentBranchAuditor(
            repo_root=repo_root,
            archive_path=archive_path,
        ).audit()
    except (DevelopmentBranchAuditError, OSError, ValueError) as exc:
        return {
            "ok": False,
            "mode": "read_only",
            "branch_count": 0,
            "cleanup_candidate_count": 0,
            "needs_review_count": 0,
            "active_worktree_count": 0,
            "branches": [],
            "warnings": [],
            "message": str(exc),
        }
