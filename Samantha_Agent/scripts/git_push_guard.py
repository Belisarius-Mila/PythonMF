#!/usr/bin/env python3
"""Read-only guard before routine `git push origin main`."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.git_safety_check import (
    BINARY_SUFFIXES,
    DEFAULT_LARGE_FILE_BYTES,
    branch_guard_status,
    path_is_blocked,
)


@dataclass(frozen=True)
class PushGuardStatus:
    branch: str
    upstream: str
    ahead: int
    behind: int
    dirty_paths: tuple[str, ...]
    merge_state: tuple[str, ...]
    last_commit: str
    last_commit_files: tuple[str, ...]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/usr/bin/git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        timeout=8,
        check=False,
    )


def git_output(args: list[str]) -> str:
    completed = run_git(args)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(detail or f"git {' '.join(args)} failed")
    return completed.stdout.strip()


def parse_tracking_counts(status_output: str) -> tuple[int, int]:
    first_line = status_output.splitlines()[0] if status_output.splitlines() else ""
    ahead = 0
    behind = 0
    if "[" not in first_line or "]" not in first_line:
        return ahead, behind
    detail = first_line.split("[", 1)[1].split("]", 1)[0]
    for part in detail.split(","):
        text = part.strip()
        if text.startswith("ahead "):
            ahead = int(text.removeprefix("ahead ").strip())
        elif text.startswith("behind "):
            behind = int(text.removeprefix("behind ").strip())
    return ahead, behind


def dirty_paths(status_output: str) -> tuple[str, ...]:
    paths: list[str] = []
    for line in status_output.splitlines()[1:]:
        if not line:
            continue
        paths.append(line[3:].strip() if len(line) > 3 else line.strip())
    return tuple(paths)


def merge_state() -> tuple[str, ...]:
    git_dir = Path(git_output(["rev-parse", "--git-dir"]))
    if not git_dir.is_absolute():
        git_dir = REPO_ROOT / git_dir
    markers = {
        "MERGE_HEAD": "merge",
        "REBASE_HEAD": "rebase",
        "CHERRY_PICK_HEAD": "cherry-pick",
        "REVERT_HEAD": "revert",
    }
    return tuple(label for marker, label in markers.items() if (git_dir / marker).exists())


def last_commit_files() -> tuple[str, ...]:
    output = git_output(["diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"])
    return tuple(line.strip() for line in output.splitlines() if line.strip())


def object_size(path: str) -> int | None:
    completed = run_git(["cat-file", "-s", f"HEAD:{path}"])
    if completed.returncode != 0:
        return None
    try:
        return int(completed.stdout.strip())
    except ValueError:
        return None


def inspect_last_commit_files(files: tuple[str, ...], large_file_bytes: int) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for path in files:
        blocked_reason = path_is_blocked(path)
        if blocked_reason:
            errors.append(f"blocked path in last commit: {path} ({blocked_reason})")
        size = object_size(path)
        if size is not None and size > large_file_bytes:
            warnings.append(f"large file in last commit: {path} ({size} bytes)")
        if Path(path).suffix.casefold() in BINARY_SUFFIXES:
            warnings.append(f"binary/media file in last commit: {path}")
    return errors, warnings


def push_guard_status(base_branch: str, remote: str, large_file_bytes: int) -> PushGuardStatus:
    status_output = git_output(["status", "--porcelain=v1", "--branch"])
    branch = git_output(["branch", "--show-current"])
    upstream = ""
    upstream_completed = run_git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    if upstream_completed.returncode == 0:
        upstream = upstream_completed.stdout.strip()

    ahead, behind = parse_tracking_counts(status_output)
    dirty = dirty_paths(status_output)
    active_merge_state = merge_state()
    last_commit = git_output(["rev-parse", "--short", "HEAD"])
    files = last_commit_files()
    branch_status = branch_guard_status(base_branch)
    errors: list[str] = []
    warnings: list[str] = []

    if branch != base_branch:
        errors.append(f"current branch is `{branch or '(detached HEAD)'}`, expected `{base_branch}`")
    if upstream and upstream != f"{remote}/{base_branch}":
        errors.append(f"upstream is `{upstream}`, expected `{remote}/{base_branch}`")
    elif not upstream:
        errors.append("current branch has no upstream")
    if dirty:
        errors.append(f"working tree is not clean ({len(dirty)} paths)")
    if behind:
        errors.append(f"branch is behind upstream by {behind} commit(s)")
    if active_merge_state:
        errors.append(f"git operation in progress: {', '.join(active_merge_state)}")
    if branch_status.warning:
        errors.append(branch_status.warning)
    if branch_status.unmerged_branches:
        errors.append(f"unmerged branches outside `{base_branch}`: {len(branch_status.unmerged_branches)}")

    commit_errors, commit_warnings = inspect_last_commit_files(files, large_file_bytes)
    errors.extend(commit_errors)
    warnings.extend(commit_warnings)
    if ahead == 0:
        warnings.append("no local commits ahead of upstream; push would be a no-op")

    return PushGuardStatus(
        branch=branch,
        upstream=upstream,
        ahead=ahead,
        behind=behind,
        dirty_paths=dirty,
        merge_state=active_merge_state,
        last_commit=last_commit,
        last_commit_files=files,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def format_report(status: PushGuardStatus, base_branch: str, remote: str) -> str:
    lines = ["Git push guard:"]
    lines.append(f"- branch: {status.branch or '(detached HEAD)'}")
    lines.append(f"- upstream: {status.upstream or '(none)'}")
    lines.append(f"- sync: ahead {status.ahead}, behind {status.behind}")
    lines.append(f"- last commit: {status.last_commit}")
    if status.dirty_paths:
        lines.append(f"- dirty paths: {len(status.dirty_paths)}")
    else:
        lines.append("- OK working tree clean")
    if status.last_commit_files:
        lines.append(f"- last commit files: {len(status.last_commit_files)}")
    else:
        lines.append("- WARN last commit has no file changes")
    if status.errors:
        lines.append("- FAIL push guard blocked:")
        lines.extend(f"  - {item}" for item in status.errors)
        lines.append("Next: do not run routine push; resolve the blocking item or ask Mila.")
    else:
        lines.append(f"- OK routine push allowed: git push {remote} {base_branch}")
    if status.warnings:
        lines.append("- WARN review:")
        lines.extend(f"  - {item}" for item in status.warnings)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether routine `git push origin main` is allowed.")
    parser.add_argument("--base-branch", default="main")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--large-file-bytes", type=int, default=DEFAULT_LARGE_FILE_BYTES)
    args = parser.parse_args()

    try:
        status = push_guard_status(args.base_branch, args.remote, args.large_file_bytes)
    except RuntimeError as exc:
        print(f"Git push guard:\n- FAIL {exc}", file=sys.stderr)
        return 2
    print(format_report(status, args.base_branch, args.remote))
    return 0 if status.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
