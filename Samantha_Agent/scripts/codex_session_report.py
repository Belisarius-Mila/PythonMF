from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LABELS_PATH = PROJECT_ROOT / "data/private/voice_inbox/codex_session_labels.json"
PS_COMMAND = ["ps", "-axo", "pid=,ppid=,tty=,etime=,command="]
DEFAULT_STALE_HOURS = 36.0


@dataclass(frozen=True)
class ProcessRow:
    pid: int
    ppid: int
    tty: str
    elapsed_seconds: int
    command: str


@dataclass(frozen=True)
class CodexSession:
    tty: str
    pids: tuple[int, ...]
    age_seconds: int
    label: str
    role: str
    command: str
    candidate: bool
    candidate_reason: str


def normalize_tty(value: str) -> str:
    text = str(value or "").strip()
    if text.startswith("/dev/"):
        return text.removeprefix("/dev/")
    return text


def parse_etime(value: str) -> int:
    text = str(value or "").strip()
    if not text:
        return 0
    days = 0
    if "-" in text:
        day_text, text = text.split("-", 1)
        try:
            days = int(day_text)
        except ValueError:
            days = 0
    parts = text.split(":")
    try:
        if len(parts) == 3:
            hours, minutes, seconds = [int(part) for part in parts]
        elif len(parts) == 2:
            hours = 0
            minutes, seconds = [int(part) for part in parts]
        else:
            hours = 0
            minutes = 0
            seconds = int(parts[0])
    except ValueError:
        return 0
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def format_age(seconds: int) -> str:
    if seconds >= 86400:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h" if hours else f"{days}d"
    if seconds >= 3600:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m" if minutes else f"{hours}h"
    minutes = seconds // 60
    return f"{minutes}m" if minutes else f"{seconds}s"


def parse_process_rows(output: str) -> list[ProcessRow]:
    rows: list[ProcessRow] = []
    for raw_line in str(output or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        pid_text, ppid_text, tty, etime, command = parts
        try:
            pid = int(pid_text)
            ppid = int(ppid_text)
        except ValueError:
            continue
        rows.append(
            ProcessRow(
                pid=pid,
                ppid=ppid,
                tty=normalize_tty(tty),
                elapsed_seconds=parse_etime(etime),
                command=command,
            )
        )
    return rows


def run_ps(
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> list[ProcessRow]:
    try:
        completed = runner(
            PS_COMMAND,
            capture_output=True,
            text=True,
            timeout=4,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if completed.returncode != 0:
        return []
    return parse_process_rows(completed.stdout)


def current_tty() -> str:
    try:
        return normalize_tty(os.ttyname(0))
    except OSError:
        return ""


def load_labels(path: Path = LABELS_PATH) -> dict[str, dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    sessions = payload.get("sessions", payload)
    if not isinstance(sessions, dict):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for tty, value in sessions.items():
        if isinstance(value, str):
            result[normalize_tty(tty)] = {"label": value}
        elif isinstance(value, dict):
            result[normalize_tty(tty)] = value
    return result


def ssh_ttys(rows: list[ProcessRow]) -> set[str]:
    result: set[str] = set()
    pattern = re.compile(r"@(?P<tty>ttys\d+)")
    for row in rows:
        match = pattern.search(row.command)
        if "sshd-session:" in row.command and match:
            result.add(normalize_tty(match.group("tty")))
    return result


def classify_label(tty: str, labels: dict[str, dict[str, Any]]) -> str:
    configured = labels.get(tty, {})
    label = str(configured.get("label") or "").strip()
    return label or "nepojmenovaná relace"


def discover_sessions(
    rows: list[ProcessRow],
    *,
    current_tty_value: str = "",
    labels: dict[str, dict[str, Any]] | None = None,
    stale_after_hours: float = DEFAULT_STALE_HOURS,
) -> list[CodexSession]:
    labels = labels or {}
    ssh = ssh_ttys(rows)
    grouped: dict[str, list[ProcessRow]] = {}
    for row in rows:
        folded = row.command.casefold()
        if "codex" not in folded or "app-server" in folded:
            continue
        if not row.tty or row.tty == "??":
            continue
        grouped.setdefault(row.tty, []).append(row)

    sessions: list[CodexSession] = []
    stale_after_seconds = int(stale_after_hours * 3600)
    current_tty_value = normalize_tty(current_tty_value)
    for tty, tty_rows in sorted(grouped.items()):
        oldest = max(row.elapsed_seconds for row in tty_rows)
        pids = tuple(sorted(row.pid for row in tty_rows))
        command = next((row.command for row in tty_rows if "vendor" in row.command), tty_rows[0].command)
        role_parts: list[str] = []
        configured = labels.get(tty, {})
        protected = bool(configured.get("protected"))
        if tty == current_tty_value:
            role_parts.append("tato terminálová relace")
        if tty in ssh:
            role_parts.append("SSH")
        if protected:
            role_parts.append("chráněná")
        role = ", ".join(role_parts) if role_parts else "běžná"

        candidate = False
        reason = ""
        if tty != current_tty_value and not protected and oldest >= stale_after_seconds:
            candidate = True
            reason = f"běží déle než {format_age(stale_after_seconds)} a není aktuální ani chráněná"

        sessions.append(
            CodexSession(
                tty=tty,
                pids=pids,
                age_seconds=oldest,
                label=classify_label(tty, labels),
                role=role,
                command=command,
                candidate=candidate,
                candidate_reason=reason,
            )
        )
    return sessions


def build_report(
    sessions: list[CodexSession],
    *,
    current_tty_value: str,
) -> str:
    lines = ["Codex relace:"]
    current_tty_value = current_tty_value or "nezjištěno"
    lines.append(f"- aktuální terminál: {current_tty_value}")
    if not sessions:
        lines.append("- žádná další Codex relace nebyla nalezena")
        return "\n".join(lines)

    for session in sessions:
        lines.append(
            f"- {session.tty}: {session.label} ({format_age(session.age_seconds)}), "
            f"role: {session.role}, PID: {', '.join(str(pid) for pid in session.pids)}"
        )
    candidates = [session for session in sessions if session.candidate]
    if candidates:
        lines.append("Kandidáti na ukončení:")
        for session in candidates:
            lines.append(f"- {session.tty}: {session.label}; důvod: {session.candidate_reason}")
        lines.append("Pokud chceš některou relaci ukončit, napiš přesně: Ukonči relaci ttysXXX.")
    else:
        lines.append("Kandidát na ukončení: žádný.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only report of running Codex CLI sessions.")
    parser.add_argument("--stale-hours", type=float, default=DEFAULT_STALE_HOURS)
    parser.add_argument("--include-current", action="store_true")
    args = parser.parse_args()

    current = current_tty()
    labels = load_labels()
    sessions = discover_sessions(
        run_ps(),
        current_tty_value=current,
        labels=labels,
        stale_after_hours=args.stale_hours,
    )
    if not args.include_current:
        sessions = [session for session in sessions if session.tty != current]
    print(build_report(sessions, current_tty_value=current))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
