#!/usr/bin/env python3
"""Read-only Samantha system quick check for reconnects and morning starts."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.backup.activity_state import backup_activity_status
from scripts.autosave_status import autosave_status
from scripts.cockpit_smoke_check import run_smoke_check


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


def autosave_line(path: Path | None = None, warn_minutes: int = DEFAULT_AUTOSAVE_WARN_MINUTES) -> CheckLine:
    status = autosave_status(
        latest_info_path=path or PROJECT_ROOT / "data" / "session_autosave" / "latest_info.txt",
        warn_minutes=warn_minutes,
    )
    if status.latest_age_minutes is None:
        age_text = "age unknown"
    else:
        age_text = f"{status.latest_age_minutes} min ago"
    watcher_text = "watcher running" if status.watcher_running else "watcher stopped"
    detail = f"{status.latest_info_path} modified {age_text}; {watcher_text}"
    if status.warning:
        detail = f"{detail}; {status.warning}"
    return CheckLine("autosave", status.ok, detail)

def format_quick_check(lines: list[CheckLine]) -> str:
    output = [format_morning_sentence(lines), "Samantha system quick check:"]
    for line in lines:
        output.append(f"- {'OK' if line.ok else 'WARN'} {line.name}: {line.message}")
    return "\n".join(output)


def format_morning_sentence(lines: list[CheckLine]) -> str:
    by_name = {line.name: line for line in lines}
    cockpit_ok = by_name.get("cockpit", CheckLine("cockpit", False, "")).ok
    backup_ok = by_name.get("backup", CheckLine("backup", False, "")).ok
    git_ok = by_name.get("git", CheckLine("git", False, "")).ok
    warnings = [line.name for line in lines if not line.ok]

    if cockpit_ok and backup_ok and git_ok and not warnings:
        return "Ranní stav: Samantha je vzhůru, Cockpit odpovídá, záloha je v pořádku a git je čistý."
    stable_parts: list[str] = []
    if cockpit_ok:
        stable_parts.append("Cockpit odpovídá")
    if backup_ok:
        stable_parts.append("záloha je v pořádku")
    if git_ok:
        stable_parts.append("git je čistý")
    stable_text = ", ".join(stable_parts) if stable_parts else "základní kontrola má varování"
    warning_text = ", ".join(warnings) if warnings else "žádná varování"
    return f"Ranní stav: Samantha je vzhůru; {stable_text}; zkontrolovat: {warning_text}."


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
        autosave_line(warn_minutes=args.autosave_warn_minutes),
    ]
    print(format_quick_check(lines))
    return 0 if all(line.ok for line in lines) else 1


if __name__ == "__main__":
    raise SystemExit(main())
