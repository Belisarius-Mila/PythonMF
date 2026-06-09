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


def format_report(files: list[StagedFile], errors: list[str], warnings: list[str]) -> str:
    lines = ["Git safety check:"]
    if not files:
        lines.append("- OK no staged files")
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
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check staged files for private/autosave/env and large binary risks.")
    parser.add_argument("--large-file-bytes", type=int, default=DEFAULT_LARGE_FILE_BYTES)
    args = parser.parse_args()

    try:
        files = staged_files()
        errors, warnings = check_staged(files, args.large_file_bytes)
    except RuntimeError as exc:
        print(f"Git safety check:\n- FAIL {exc}", file=sys.stderr)
        return 2
    print(format_report(files, errors, warnings))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
