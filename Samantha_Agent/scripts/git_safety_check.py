#!/usr/bin/env python3
"""Pre-commit safety check for staged Samantha/PythonMF changes."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
DEFAULT_LARGE_FILE_BYTES = 5 * 1024 * 1024
BLOCKED_PATH_PARTS = (
    "/data/private/",
    "/data/session_autosave/",
)
BLOCKED_FILENAMES = {
    ".env",
    ".env.local",
    ".env.production",
}
BINARY_SUFFIXES = {
    ".aac",
    ".aif",
    ".aiff",
    ".dmg",
    ".doc",
    ".docx",
    ".heic",
    ".jpeg",
    ".jpg",
    ".m4a",
    ".mov",
    ".mp3",
    ".mp4",
    ".pdf",
    ".png",
    ".wav",
    ".webp",
    ".zip",
}


@dataclass(frozen=True)
class StagedFile:
    status: str
    path: str


@dataclass(frozen=True)
class BranchGuardStatus:
    current_branch: str
    base_branch: str
    unmerged_branches: tuple[str, ...]
    warning: str = ""


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/usr/bin/git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        timeout=8,
        check=False,
    )


def staged_files() -> list[StagedFile]:
    completed = run_git(["diff", "--cached", "--name-status"])
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout).strip())
    files: list[StagedFile] = []
    for line in completed.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0]
        path = parts[-1]
        files.append(StagedFile(status=status, path=path))
    return files


def current_branch() -> str:
    completed = run_git(["branch", "--show-current"])
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def parse_unmerged_branches_output(output: str) -> tuple[str, ...]:
    branches: list[str] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("*"):
            line = line[1:].strip()
        if line.startswith("+"):
            line = line[1:].strip()
        if " -> " in line:
            continue
        branches.append(line)
    return tuple(branches)


def branch_guard_status(base_branch: str = "main") -> BranchGuardStatus:
    branch = current_branch()
    completed = run_git(["branch", "--no-merged", base_branch, "--all"])
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        return BranchGuardStatus(
            current_branch=branch,
            base_branch=base_branch,
            unmerged_branches=(),
            warning=f"branch guard nelze spustit: {detail}",
        )
    return BranchGuardStatus(
        current_branch=branch,
        base_branch=base_branch,
        unmerged_branches=parse_unmerged_branches_output(completed.stdout),
    )


def staged_file_size(path: str) -> int | None:
    completed = run_git(["cat-file", "-s", f":{path}"])
    if completed.returncode != 0:
        return None
    try:
        return int(completed.stdout.strip())
    except ValueError:
        return None


def path_is_blocked(path: str) -> str:
    normalized = "/" + path.replace("\\", "/").casefold()
    name = Path(path).name.casefold()
    if name in BLOCKED_FILENAMES:
        return "env file"
    for part in BLOCKED_PATH_PARTS:
        if part in normalized:
            return part.strip("/")
    return ""


def check_staged(files: list[StagedFile], large_file_bytes: int) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for item in files:
        blocked_reason = path_is_blocked(item.path)
        if blocked_reason:
            errors.append(f"blocked path: {item.path} ({blocked_reason})")

        suffix = Path(item.path).suffix.casefold()
        size = staged_file_size(item.path)
        if size is not None and size > large_file_bytes:
            warnings.append(f"large staged file: {item.path} ({size} bytes)")
        if suffix in BINARY_SUFFIXES:
            warnings.append(f"binary/media staged file: {item.path}")
    return errors, warnings


def format_branch_guard(status: BranchGuardStatus) -> list[str]:
    lines: list[str] = []
    current = status.current_branch or "(detached HEAD)"
    if status.warning:
        lines.append(f"- WARN {status.warning}")
    elif current != status.base_branch:
        lines.append(f"- WARN current branch is `{current}`, expected `{status.base_branch}` for mainline commits")
    else:
        lines.append(f"- OK current branch: {current}")

    if status.unmerged_branches:
        lines.append(f"- WARN branches not merged into `{status.base_branch}`:")
        lines.extend(f"  - {branch}" for branch in status.unmerged_branches)
        lines.append("- Next: audit/cherry-pick/archive branch work before assuming main has everything.")
    elif not status.warning:
        lines.append(f"- OK no branches outside `{status.base_branch}`")
    return lines


def format_report(
    files: list[StagedFile],
    errors: list[str],
    warnings: list[str],
    branch_status: BranchGuardStatus | None = None,
) -> str:
    lines = ["Git safety check:"]
    if not files:
        lines.append("- OK no staged files")
        if branch_status is not None:
            lines.append("Branch guard:")
            lines.extend(format_branch_guard(branch_status))
        return "\n".join(lines)

    lines.append(f"- staged files: {len(files)}")
    if errors:
        lines.append("- FAIL blocked staged content:")
        lines.extend(f"  - {item}" for item in errors)
    else:
        lines.append("- OK no blocked private/autosave/env paths staged")
    if warnings:
        lines.append("- WARN review before commit:")
        lines.extend(f"  - {item}" for item in warnings)
    else:
        lines.append("- OK no large or obvious binary/media staged files")
    if branch_status is not None:
        lines.append("Branch guard:")
        lines.extend(format_branch_guard(branch_status))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check staged files for private/autosave/env and large binary risks.")
    parser.add_argument("--large-file-bytes", type=int, default=DEFAULT_LARGE_FILE_BYTES)
    parser.add_argument("--base-branch", default="main")
    parser.add_argument("--no-branch-guard", action="store_true", help="Skip warning about branches not merged into base branch.")
    parser.add_argument(
        "--fail-on-branch-risk",
        action="store_true",
        help="Return non-zero when current branch is not base or unmerged branches exist.",
    )
    args = parser.parse_args()

    try:
        files = staged_files()
        errors, warnings = check_staged(files, args.large_file_bytes)
        branch_status = None if args.no_branch_guard else branch_guard_status(args.base_branch)
    except RuntimeError as exc:
        print(f"Git safety check:\n- FAIL {exc}", file=sys.stderr)
        return 2
    print(format_report(files, errors, warnings, branch_status))
    branch_risk = bool(
        branch_status
        and (
            branch_status.warning
            or branch_status.unmerged_branches
            or (branch_status.current_branch and branch_status.current_branch != branch_status.base_branch)
        )
    )
    return 1 if errors or (args.fail_on_branch_risk and branch_risk) else 0


if __name__ == "__main__":
    raise SystemExit(main())
