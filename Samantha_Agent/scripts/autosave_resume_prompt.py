#!/usr/bin/env python3
"""Read-only startup helper for offering autosave context recovery."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LATEST_INFO_PATH = PROJECT_ROOT / "data" / "session_autosave" / "latest_info.txt"


@dataclass(frozen=True)
class AutosaveResumeCandidate:
    should_offer: bool
    latest_info_path: str
    source_path: str
    source_modified_at: str
    commit_modified_at: str
    source_age_minutes: int | None
    reason: str


def autosave_resume_candidate(
    *,
    latest_info_path: Path = LATEST_INFO_PATH,
    project_root: Path = PROJECT_ROOT,
) -> AutosaveResumeCandidate:
    source_path = parse_autosave_source(latest_info_path)
    if not source_path:
        return empty_candidate(latest_info_path, "autosave source nebyl nalezen")
    if not source_path.exists():
        return empty_candidate(latest_info_path, "autosave source soubor neexistuje", source_path=source_path)

    source_mtime = source_path.stat().st_mtime
    commit_mtime, commit_warning = last_commit_timestamp(project_root)
    if commit_mtime is None:
        return empty_candidate(
            latest_info_path,
            commit_warning or "nelze zjistit cas posledniho commitu",
            source_path=source_path,
            source_mtime=source_mtime,
        )

    source_modified_at = datetime.fromtimestamp(source_mtime, tz=timezone.utc).isoformat()
    commit_modified_at = datetime.fromtimestamp(commit_mtime, tz=timezone.utc).isoformat()
    source_age_minutes = int((datetime.now(timezone.utc).timestamp() - source_mtime) // 60)
    if source_mtime > commit_mtime:
        return AutosaveResumeCandidate(
            should_offer=True,
            latest_info_path=display_path(latest_info_path, project_root),
            source_path=display_path(source_path, project_root),
            source_modified_at=source_modified_at,
            commit_modified_at=commit_modified_at,
            source_age_minutes=source_age_minutes,
            reason="posledni autosave je novejsi nez posledni commit",
        )
    return AutosaveResumeCandidate(
        should_offer=False,
        latest_info_path=display_path(latest_info_path, project_root),
        source_path=display_path(source_path, project_root),
        source_modified_at=source_modified_at,
        commit_modified_at=commit_modified_at,
        source_age_minutes=source_age_minutes,
        reason="posledni autosave neni novejsi nez posledni commit",
    )


def parse_autosave_source(latest_info_path: Path) -> Path | None:
    if not latest_info_path.exists():
        return None
    try:
        lines = latest_info_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for line in lines:
        if not line.startswith("Source:"):
            continue
        value = line.removeprefix("Source:").strip()
        if value:
            return Path(value).expanduser()
    return None


def last_commit_timestamp(project_root: Path) -> tuple[float | None, str]:
    try:
        completed = subprocess.run(
            ["/usr/bin/git", "-C", str(project_root), "log", "-1", "--format=%ct"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)
    if completed.returncode != 0:
        return None, (completed.stderr or completed.stdout or "git log failed").strip()
    try:
        return float(completed.stdout.strip()), ""
    except ValueError:
        return None, "git log vratil necitelny cas"


def empty_candidate(
    latest_info_path: Path,
    reason: str,
    *,
    source_path: Path | None = None,
    source_mtime: float | None = None,
) -> AutosaveResumeCandidate:
    source_modified_at = ""
    source_age_minutes: int | None = None
    if source_mtime is not None:
        source_modified_at = datetime.fromtimestamp(source_mtime, tz=timezone.utc).isoformat()
        source_age_minutes = int((datetime.now(timezone.utc).timestamp() - source_mtime) // 60)
    return AutosaveResumeCandidate(
        should_offer=False,
        latest_info_path=display_path(latest_info_path, PROJECT_ROOT),
        source_path=display_path(source_path, PROJECT_ROOT) if source_path else "",
        source_modified_at=source_modified_at,
        commit_modified_at="",
        source_age_minutes=source_age_minutes,
        reason=reason,
    )


def display_path(path: Path, project_root: Path) -> str:
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


def format_candidate(candidate: AutosaveResumeCandidate) -> str:
    lines = ["Autosave recovery check:"]
    lines.append(f"- {'NABIDNOUT' if candidate.should_offer else 'nenabizet'}: {candidate.reason}")
    if candidate.source_path:
        lines.append(f"- source: {candidate.source_path}")
    if candidate.source_age_minutes is not None:
        lines.append(f"- age: {candidate.source_age_minutes} min")
    if candidate.commit_modified_at:
        lines.append(f"- last commit: {candidate.commit_modified_at}")
    lines.append("- obsah autosave se zatim necetl")
    return "\n".join(lines)


def startup_prompt() -> str:
    return (
        "Obnov kontext z posledniho autosave. Jen cti, nic nemen. "
        "Shrn rozpracovanou praci, otevrene kroky a rizika; neopisuj citlive texty."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Offer autosave recovery when it is newer than the last commit.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--prompt", action="store_true", help="Print the Codex startup prompt for recovery.")
    parser.add_argument("--quiet", action="store_true", help="Print nothing; exit 0 when recovery should be offered.")
    args = parser.parse_args()

    if args.prompt:
        print(startup_prompt())
        return 0

    candidate = autosave_resume_candidate()
    if args.quiet:
        return 0 if candidate.should_offer else 1
    if args.json:
        print(json.dumps(asdict(candidate), ensure_ascii=False, indent=2))
    else:
        print(format_candidate(candidate))
    return 0 if candidate.should_offer else 1


if __name__ == "__main__":
    raise SystemExit(main())
