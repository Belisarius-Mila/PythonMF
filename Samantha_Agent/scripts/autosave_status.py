#!/usr/bin/env python3
"""Read-only status for Samantha/Codex session autosave."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUTOSAVE_DIR = PROJECT_ROOT / "data" / "session_autosave"
LATEST_INFO_PATH = AUTOSAVE_DIR / "latest_info.txt"
WATCHER_SCRIPT_NAME = "autosave_codex_session.sh"
DEFAULT_WARN_MINUTES = 20
DEFAULT_DISK_WARNING_GIB = 30
DEFAULT_DISK_CRITICAL_GIB = 15
PS_COMMAND = ["ps", "-axo", "pid=,ppid=,etime=,command="]


@dataclass(frozen=True)
class AutosaveStatus:
    ok: bool
    latest_info_path: str
    latest_age_minutes: int | None
    latest_modified_at: str
    watcher_running: bool
    watcher_count: int
    watcher_pids: tuple[int, ...]
    disk_free_gib: float | None
    disk_state: str
    warning: str


def autosave_status(
    *,
    latest_info_path: Path = LATEST_INFO_PATH,
    warn_minutes: int = DEFAULT_WARN_MINUTES,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    disk_usage_getter: Callable[[Path], object] = shutil.disk_usage,
) -> AutosaveStatus:
    latest_age_minutes: int | None = None
    latest_modified_at = ""
    warnings: list[str] = []

    if latest_info_path.exists():
        modified = datetime.fromtimestamp(latest_info_path.stat().st_mtime, tz=timezone.utc)
        latest_modified_at = modified.isoformat()
        latest_age_minutes = int((datetime.now(timezone.utc) - modified).total_seconds() // 60)
        if latest_age_minutes > warn_minutes:
            warnings.append(f"posledni autosave je stary {latest_age_minutes} min (warn > {warn_minutes})")
    else:
        warnings.append("chybi latest_info.txt")

    disk_free_gib: float | None = None
    disk_state = "unknown"
    try:
        disk_usage = disk_usage_getter(latest_info_path.parent)
        disk_free_bytes = int(getattr(disk_usage, "free"))
        disk_free_gib = round(disk_free_bytes / 1024**3, 1)
        if disk_free_bytes < DEFAULT_DISK_CRITICAL_GIB * 1024**3:
            disk_state = "critical"
            warnings.append(
                f"kriticky malo mista na SSD: {disk_free_gib:.1f} GiB "
                f"(< {DEFAULT_DISK_CRITICAL_GIB} GiB)"
            )
        elif disk_free_bytes < DEFAULT_DISK_WARNING_GIB * 1024**3:
            disk_state = "warning"
            warnings.append(
                f"malo mista na SSD: {disk_free_gib:.1f} GiB "
                f"(< {DEFAULT_DISK_WARNING_GIB} GiB)"
            )
        else:
            disk_state = "ok"
    except (OSError, TypeError, ValueError, AttributeError) as exc:
        warnings.append(f"volne misto na SSD nelze zjistit: {exc}")

    watcher_pids, ps_warning = find_autosave_watchers(runner=runner)
    if ps_warning:
        warnings.append(ps_warning)
    if not watcher_pids:
        warnings.append("autosave watcher nebezi")
    elif len(watcher_pids) > 1:
        warnings.append(f"bezi {len(watcher_pids)} autosave watchery, ocekavan je prave jeden")

    return AutosaveStatus(
        ok=not warnings,
        latest_info_path=display_path_for(latest_info_path),
        latest_age_minutes=latest_age_minutes,
        latest_modified_at=latest_modified_at,
        watcher_running=bool(watcher_pids),
        watcher_count=len(watcher_pids),
        watcher_pids=tuple(watcher_pids),
        disk_free_gib=disk_free_gib,
        disk_state=disk_state,
        warning="; ".join(warnings),
    )


def find_autosave_watchers(
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> tuple[list[int], str]:
    try:
        completed = runner(PS_COMMAND, capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [], f"nelze precist procesy: {exc}"
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "ps failed").strip()
        return [], f"nelze precist procesy: {message}"

    pids: list[int] = []
    for line in completed.stdout.splitlines():
        parts = line.strip().split(None, 3)
        if len(parts) < 4:
            continue
        pid_text, _ppid_text, _etime, command = parts
        if WATCHER_SCRIPT_NAME not in command or "--watch" not in command:
            continue
        if "autosave_status.py" in command:
            continue
        try:
            pids.append(int(pid_text))
        except ValueError:
            continue
    return sorted(set(pids)), ""


def display_path_for(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def format_autosave_status(status: AutosaveStatus) -> str:
    lines = ["Samantha autosave status:"]
    lines.append(f"- {'OK' if status.ok else 'WARN'} latest: {status.latest_info_path}")
    if status.latest_age_minutes is None:
        lines.append("- latest age: nezjisteno")
    else:
        lines.append(f"- latest age: {status.latest_age_minutes} min")
    lines.append(f"- watcher: {'bezi' if status.watcher_running else 'nebezi'}")
    lines.append(f"- watcher count: {status.watcher_count}")
    if status.watcher_pids:
        lines.append(f"- watcher pids: {', '.join(str(pid) for pid in status.watcher_pids)}")
    if status.disk_free_gib is None:
        lines.append("- SSD free: nezjisteno")
    else:
        lines.append(f"- SSD free: {status.disk_free_gib:.1f} GiB ({status.disk_state})")
    if status.warning:
        lines.append(f"- warning: {status.warning}")
    if not status.watcher_running:
        lines.extend(
            [
                "",
                "Dalsi krok po potvrzeni:",
                "- spustit autosave watcher pres `scripts/autosave_codex_session.sh --watch`",
                "- nebo zacit novou relaci pres `samantha`, ktera watcher spousti automaticky",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Samantha autosave status.")
    parser.add_argument("--warn-minutes", type=int, default=DEFAULT_WARN_MINUTES)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    status = autosave_status(warn_minutes=args.warn_minutes)
    if args.json:
        print(json.dumps(asdict(status), ensure_ascii=False, indent=2))
    else:
        print(format_autosave_status(status))
    return 0 if status.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
