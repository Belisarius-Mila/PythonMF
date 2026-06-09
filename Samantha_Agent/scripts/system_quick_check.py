#!/usr/bin/env python3
"""Read-only Samantha system quick check for reconnects and morning starts."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.backup.activity_state import backup_activity_status
from app.cockpit import adam_voice_bridge_status
from scripts.cockpit_smoke_check import run_smoke_check


AUTOSAVE_INFO_PATH = PROJECT_ROOT / "data" / "session_autosave" / "latest_info.txt"
DEFAULT_AUTOSAVE_WARN_MINUTES = 20


@dataclass(frozen=True)
class CheckLine:
    name: str
    ok: bool
    message: str


def git_status_line() -> CheckLine:
    try:
        completed = subprocess.run(
            ["/usr/bin/git", "-C", str(PROJECT_ROOT.parent), "status", "--short", "--branch"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return CheckLine("git", False, str(exc))
    if completed.returncode != 0:
        return CheckLine("git", False, (completed.stderr or completed.stdout).strip())
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    branch = lines[0].removeprefix("## ") if lines else "unknown"
    dirty_count = max(0, len(lines) - 1)
    message = f"{branch}; {'clean' if dirty_count == 0 else f'{dirty_count} dirty files'}"
    return CheckLine("git", dirty_count == 0 and "behind" not in branch, message)


def backup_line() -> CheckLine:
    status = backup_activity_status()
    return CheckLine("backup", bool(status.get("ok")), str(status.get("message", "")).replace("\n", " | "))


def cockpit_line(base_url: str, timeout: float) -> CheckLine:
    results = run_smoke_check(base_url, timeout)
    failed = [item for item in results if not item.ok]
    if failed:
        return CheckLine("cockpit", False, "; ".join(f"{item.name}: {item.message}" for item in failed))
    return CheckLine("cockpit", True, f"{base_url} smoke OK")


def bridge_line() -> CheckLine:
    status = adam_voice_bridge_status()
    ok = status.get("status") == "ok"
    return CheckLine("adam_bridge", ok, str(status.get("message", "")))


def autosave_line(path: Path = AUTOSAVE_INFO_PATH, warn_minutes: int = DEFAULT_AUTOSAVE_WARN_MINUTES) -> CheckLine:
    display_path = display_path_for(path)
    if not path.exists():
        return CheckLine("autosave", False, f"missing {display_path}")
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    age_minutes = int((datetime.now(timezone.utc) - modified).total_seconds() // 60)
    ok = age_minutes <= warn_minutes
    return CheckLine(
        "autosave",
        ok,
        f"{display_path} modified {age_minutes} min ago (warn > {warn_minutes})",
    )


def display_path_for(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def format_quick_check(lines: list[CheckLine]) -> str:
    output = ["Samantha system quick check:"]
    for line in lines:
        output.append(f"- {'OK' if line.ok else 'WARN'} {line.name}: {line.message}")
    return "\n".join(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Samantha system quick check.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8770")
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--autosave-warn-minutes", type=int, default=DEFAULT_AUTOSAVE_WARN_MINUTES)
    args = parser.parse_args()

    lines = [
        git_status_line(),
        backup_line(),
        cockpit_line(args.base_url, args.timeout),
        bridge_line(),
        autosave_line(warn_minutes=args.autosave_warn_minutes),
    ]
    print(format_quick_check(lines))
    return 0 if all(line.ok for line in lines) else 1


if __name__ == "__main__":
    raise SystemExit(main())
