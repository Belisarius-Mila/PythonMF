#!/usr/bin/env python3
"""Read-only guard before switching to a different work topic."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.git_safety_check import branch_guard_status


@dataclass(frozen=True)
class WorkContextStatus:
    current_branch: str
    base_branch: str
    ahead: int
    behind: int
    staged_count: int
    unstaged_count: int
    untracked_count: int
    git_operation: str
    unmerged_branches: tuple[str, ...]
    branch_warning: str = ""

    @property
    def batch_pending(self) -> bool:
        """Return whether only clean local commits are waiting for the GitHub batch."""
        return (
            self.current_branch == self.base_branch
            and self.ahead > 0
            and self.behind == 0
            and self.staged_count == 0
            and self.unstaged_count == 0
            and self.untracked_count == 0
            and not self.git_operation
            and not self.unmerged_branches
            and not self.branch_warning
        )

    @property
    def clean(self) -> bool:
        return not (
            self.current_branch != self.base_branch
            or self.behind
            or self.staged_count
            or self.unstaged_count
            or self.untracked_count
            or self.git_operation
            or self.unmerged_branches
            or self.branch_warning
        )


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/usr/bin/git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        timeout=8,
        check=False,
    )


def parse_ahead_behind(branch_line: str) -> tuple[int, int]:
    ahead = 0
    behind = 0
    match = re.search(r"\[(?P<detail>[^\]]+)\]", branch_line)
    if not match:
        return ahead, behind
    for part in match.group("detail").split(","):
        item = part.strip()
        ahead_match = re.fullmatch(r"ahead (?P<count>\d+)", item)
        behind_match = re.fullmatch(r"behind (?P<count>\d+)", item)
        if ahead_match:
            ahead = int(ahead_match.group("count"))
        if behind_match:
            behind = int(behind_match.group("count"))
    return ahead, behind


def parse_porcelain_status(output: str) -> tuple[str, int, int, int, int, int]:
    branch = ""
    ahead = 0
    behind = 0
    staged = 0
    unstaged = 0
    untracked = 0
    for line in output.splitlines():
        if line.startswith("## "):
            branch_line = line.removeprefix("## ").strip()
            branch = branch_line.split("...", 1)[0].strip()
            ahead, behind = parse_ahead_behind(branch_line)
            continue
        if line.startswith("?? "):
            untracked += 1
            continue
        if len(line) < 2:
            continue
        index_status, worktree_status = line[0], line[1]
        if index_status != " ":
            staged += 1
        if worktree_status != " ":
            unstaged += 1
    return branch, ahead, behind, staged, unstaged, untracked


def git_path(name: str) -> Path:
    completed = run_git(["rev-parse", "--git-path", name])
    if completed.returncode != 0:
        return REPO_ROOT / ".git" / name
    path = Path(completed.stdout.strip())
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def git_operation_in_progress() -> str:
    checks = (
        ("merge", "MERGE_HEAD"),
        ("cherry-pick", "CHERRY_PICK_HEAD"),
        ("revert", "REVERT_HEAD"),
        ("rebase", "rebase-merge"),
        ("rebase", "rebase-apply"),
    )
    for label, marker in checks:
        if git_path(marker).exists():
            return label
    return ""


def work_context_status(base_branch: str = "main") -> WorkContextStatus:
    completed = run_git(["status", "--porcelain=v1", "--branch"])
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        return WorkContextStatus(
            current_branch="",
            base_branch=base_branch,
            ahead=0,
            behind=0,
            staged_count=0,
            unstaged_count=0,
            untracked_count=0,
            git_operation="",
            unmerged_branches=(),
            branch_warning=f"git status failed: {detail}",
        )
    branch, ahead, behind, staged, unstaged, untracked = parse_porcelain_status(completed.stdout)
    branch_status = branch_guard_status(base_branch)
    return WorkContextStatus(
        current_branch=branch or branch_status.current_branch,
        base_branch=base_branch,
        ahead=ahead,
        behind=behind,
        staged_count=staged,
        unstaged_count=unstaged,
        untracked_count=untracked,
        git_operation=git_operation_in_progress(),
        unmerged_branches=branch_status.unmerged_branches,
        branch_warning=branch_status.warning,
    )


def format_work_context_guard(status: WorkContextStatus) -> str:
    lines = ["Work context guard:"]
    if status.current_branch == status.base_branch:
        lines.append(f"- OK current branch: {status.current_branch}")
    else:
        lines.append(f"- WARN current branch is `{status.current_branch or '(unknown)'}`, expected `{status.base_branch}`")

    dirty_total = status.staged_count + status.unstaged_count + status.untracked_count
    if dirty_total:
        lines.append(
            "- WARN workspace has pending changes: "
            f"{status.staged_count} staged, {status.unstaged_count} unstaged, {status.untracked_count} untracked"
        )
    else:
        lines.append("- OK no staged, unstaged or untracked changes")

    if status.batch_pending:
        lines.append(f"- OK GitHub batch pending: {status.ahead} local commit(s)")
    elif status.ahead or status.behind:
        lines.append(f"- WARN branch sync: ahead {status.ahead}, behind {status.behind}")
    else:
        lines.append("- OK no unpushed or missing upstream commits")

    if status.git_operation:
        lines.append(f"- WARN git operation in progress: {status.git_operation}")
    else:
        lines.append("- OK no merge/rebase/cherry-pick in progress")

    if status.branch_warning:
        lines.append(f"- WARN {status.branch_warning}")
    elif status.unmerged_branches:
        lines.append(f"- WARN unmerged branches outside `{status.base_branch}`:")
        lines.extend(f"  - {branch}" for branch in status.unmerged_branches)
    else:
        lines.append(f"- OK no unmerged branches outside `{status.base_branch}`")

    if status.batch_pending:
        lines.append("Next: safe to switch topic; local commits wait for the daily GitHub batch.")
    elif status.clean:
        lines.append("Next: safe to switch topic.")
    else:
        lines.append(
            "Next: checkpoint current work before switching topic: commit finished work locally, "
            "create a WIP branch, or write a handoff. Do not push only to satisfy this guard."
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether it is safe to switch to a different work topic.")
    parser.add_argument("--base-branch", default="main")
    parser.add_argument("--warn-only", action="store_true", help="Always exit 0 even when pending work is detected.")
    args = parser.parse_args()

    status = work_context_status(args.base_branch)
    print(format_work_context_guard(status))
    return 0 if status.clean or args.warn_only else 1


if __name__ == "__main__":
    raise SystemExit(main())
