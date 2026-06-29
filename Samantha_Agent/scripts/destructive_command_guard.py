#!/usr/bin/env python3
"""Guard common destructive shell commands in Samantha full-access sessions."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
CONFIRMATION_PHRASE = "Potvrzuji globální brzdu: rozumím riziku a chci pokračovat."
CONFIRMATION_ENV = "SAMANTHA_DESTRUCTIVE_CONFIRMATION"


@dataclass(frozen=True)
class GuardDecision:
    allowed: bool
    reasons: tuple[str, ...]
    confirmation_required: bool = False


def normalize_path(value: str, cwd: Path | None = None) -> Path:
    raw = Path(value).expanduser()
    if not raw.is_absolute():
        raw = (cwd or Path.cwd()) / raw
    return raw.resolve(strict=False)


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def path_scope_reason(path_value: str, cwd: Path | None = None) -> str:
    path = normalize_path(path_value, cwd)
    if is_relative_to(path, PROJECT_ROOT / "data" / "private"):
        return "private data"
    if is_relative_to(path, PROJECT_ROOT / "data" / "session_autosave"):
        return "session autosave"
    if is_relative_to(path, PROJECT_ROOT / "memory"):
        return "Samantha memory"
    if is_relative_to(path, REPO_ROOT):
        return "PythonMF workspace"
    return ""


def confirmation_matches(text: str) -> bool:
    return " ".join(text.split()) == CONFIRMATION_PHRASE


def is_confirmed() -> bool:
    return confirmation_matches(os.environ.get(CONFIRMATION_ENV, ""))


def compact_args(args: list[str]) -> str:
    return " ".join(args[:12]) + (" ..." if len(args) > 12 else "")


def rm_targets(args: list[str]) -> list[str]:
    targets: list[str] = []
    end_options = False
    for arg in args:
        if end_options:
            targets.append(arg)
            continue
        if arg == "--":
            end_options = True
            continue
        if arg.startswith("-"):
            continue
        targets.append(arg)
    return targets


def rm_has_recursive(args: list[str]) -> bool:
    for arg in args:
        if arg in {"-r", "-R", "--recursive"}:
            return True
        if arg.startswith("-") and not arg.startswith("--") and ("r" in arg or "R" in arg):
            return True
    return False


def check_rm(args: list[str], cwd: Path | None = None) -> GuardDecision:
    reasons: list[str] = []
    targets = rm_targets(args)
    if rm_has_recursive(args):
        reasons.append("recursive rm")
    if len(targets) > 5:
        reasons.append(f"bulk delete: {len(targets)} targets")
    for target in targets:
        scope = path_scope_reason(target, cwd)
        if scope:
            reasons.append(f"delete in {scope}: {target}")
    return decision_from_reasons(reasons)


def check_find(args: list[str], cwd: Path | None = None) -> GuardDecision:
    reasons: list[str] = []
    for index, arg in enumerate(args):
        lowered = arg.casefold()
        if lowered == "-delete":
            reasons.append("find -delete")
        if lowered in {"-exec", "-execdir"}:
            next_arg = args[index + 1] if index + 1 < len(args) else ""
            if Path(next_arg).name in {"rm", "trash", "unlink"}:
                reasons.append(f"find {arg} {next_arg}")
    roots: list[str] = []
    for arg in args:
        if arg.startswith("-") or arg in {"!", "(", ")"}:
            break
        roots.append(arg)
    for root in roots:
        scope = path_scope_reason(root, cwd)
        if scope and any(item in args for item in ("-delete", "-exec", "-execdir")):
            reasons.append(f"destructive find in {scope}: {root}")
    return decision_from_reasons(reasons)


def git_subcommand_args(args: list[str]) -> list[str]:
    remaining = list(args)
    options_with_value = {
        "-C",
        "-c",
        "--git-dir",
        "--work-tree",
        "--namespace",
        "--exec-path",
        "--super-prefix",
    }
    options_without_value = {
        "--bare",
        "--no-pager",
        "--paginate",
        "--no-replace-objects",
        "--literal-pathspecs",
        "--glob-pathspecs",
        "--noglob-pathspecs",
        "--icase-pathspecs",
    }
    while remaining:
        current = remaining[0]
        if current in options_with_value:
            remaining = remaining[2:] if len(remaining) >= 2 else []
            continue
        if any(current.startswith(f"{option}=") for option in options_with_value if option.startswith("--")):
            remaining = remaining[1:]
            continue
        if current in options_without_value:
            remaining = remaining[1:]
            continue
        break
    return remaining


def check_git(args: list[str], cwd: Path | None = None) -> GuardDecision:
    del cwd
    reasons: list[str] = []
    subcommand_args = git_subcommand_args(args)
    if not subcommand_args:
        return GuardDecision(allowed=True, reasons=())
    command = subcommand_args[0]
    rest = subcommand_args[1:]
    if command == "reset" and "--hard" in rest:
        reasons.append("git reset --hard")
    if command == "clean":
        reasons.append("git clean")
    if command == "push":
        if any(arg in {"--force", "--force-with-lease", "-f"} for arg in rest):
            reasons.append("force push")
        if any(arg.startswith("+") for arg in rest):
            reasons.append("force push refspec")
        if "--delete" in rest or any(arg.startswith(":") for arg in rest):
            reasons.append("delete remote branch/tag")
    if command == "branch" and any(arg in {"-d", "-D", "--delete"} for arg in rest):
        reasons.append("delete git branch")
    if command == "tag" and any(arg in {"-d", "--delete"} for arg in rest):
        reasons.append("delete git tag")
    return decision_from_reasons(reasons)


def mv_paths(args: list[str]) -> tuple[list[str], str]:
    values: list[str] = []
    end_options = False
    for arg in args:
        if end_options:
            values.append(arg)
            continue
        if arg == "--":
            end_options = True
            continue
        if arg.startswith("-"):
            continue
        values.append(arg)
    if len(values) < 2:
        return values, ""
    return values[:-1], values[-1]


def check_mv(args: list[str], cwd: Path | None = None) -> GuardDecision:
    sources, destination = mv_paths(args)
    reasons: list[str] = []
    if len(sources) > 5:
        reasons.append(f"bulk move: {len(sources)} sources")
    if destination:
        dest_path = normalize_path(destination, cwd)
        dest_outside_repo = not is_relative_to(dest_path, REPO_ROOT)
        for source in sources:
            scope = path_scope_reason(source, cwd)
            if scope in {"private data", "session autosave", "Samantha memory"}:
                reasons.append(f"move from {scope}: {source}")
            elif scope == "PythonMF workspace" and dest_outside_repo:
                reasons.append(f"move from PythonMF workspace outside repo: {source} -> {destination}")
    return decision_from_reasons(reasons)


def decision_from_reasons(reasons: list[str]) -> GuardDecision:
    clean_reasons = tuple(dict.fromkeys(reason for reason in reasons if reason))
    if not clean_reasons:
        return GuardDecision(allowed=True, reasons=())
    return GuardDecision(
        allowed=is_confirmed(),
        reasons=clean_reasons,
        confirmation_required=not is_confirmed(),
    )


def check_command(tool: str, args: list[str], cwd: Path | None = None) -> GuardDecision:
    normalized = Path(tool).name
    if normalized == "rm":
        return check_rm(args, cwd)
    if normalized == "find":
        return check_find(args, cwd)
    if normalized == "git":
        return check_git(args, cwd)
    if normalized == "mv":
        return check_mv(args, cwd)
    return GuardDecision(allowed=True, reasons=())


def format_block_message(tool: str, args: list[str], decision: GuardDecision) -> str:
    lines = [
        "Samantha destructive command guard:",
        f"- BLOCKED command: {tool} {compact_args(args)}".rstrip(),
        "- Reasons:",
    ]
    lines.extend(f"  - {reason}" for reason in decision.reasons)
    lines.extend(
        [
            "- Required exact confirmation:",
            f"  {CONFIRMATION_PHRASE}",
            "- To run anyway, set:",
            f"  {CONFIRMATION_ENV}=\"{CONFIRMATION_PHRASE}\"",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Block destructive commands unless the global safety phrase is present.")
    parser.add_argument("--tool", required=True, help="Command name, e.g. rm, git, find, mv.")
    parser.add_argument("command_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command_args = list(args.command_args)
    if command_args and command_args[0] == "--":
        command_args = command_args[1:]
    decision = check_command(args.tool, command_args)
    if decision.allowed:
        if decision.reasons:
            print("Samantha destructive command guard: confirmation accepted.", file=sys.stderr)
        return 0
    print(format_block_message(args.tool, command_args, decision), file=sys.stderr)
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
