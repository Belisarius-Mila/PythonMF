from __future__ import annotations

import subprocess
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
MEMORY_DIR = PROJECT_ROOT / "memory"
ACTIVE_PROJECTS_PATH = MEMORY_DIR / "ACTIVE_PROJECTS.md"
MEMORY_INDEX_PATH = MEMORY_DIR / "MEMORY_INDEX.md"
DIRTY_REPO_WARNING_THRESHOLD = 4

RELATIVE_TIME_MARKERS = (
    "zitra",
    "zítra",
    "dnes",
    "vcera",
    "včera",
    "pristi start",
    "příští start",
    "neni commitnute",
    "není commitnuté",
    "nejsou commitnute",
    "nejsou commitnuté",
    "pushnout zitra",
    "pushnout zítra",
)


Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class HealthCheckResult:
    mode: str
    git_summary: str
    a1_items: tuple[str, ...]
    pending_items: tuple[str, ...]
    reminder_count: int
    warnings: tuple[str, ...]
    suggested_next_action: str


def format_samantha_health_check(
    *,
    mode: str = "quick",
    repo_root: Path = REPO_ROOT,
    memory_dir: Path = MEMORY_DIR,
    runner: Runner = subprocess.run,
) -> str:
    result = run_samantha_health_check(
        mode=mode,
        repo_root=repo_root,
        memory_dir=memory_dir,
        runner=runner,
    )
    return _format_result(result)


def run_samantha_health_check(
    *,
    mode: str = "quick",
    repo_root: Path = REPO_ROOT,
    memory_dir: Path = MEMORY_DIR,
    runner: Runner = subprocess.run,
) -> HealthCheckResult:
    normalized_mode = _normalize_mode(mode)
    active_projects_text = _read_text(memory_dir / "ACTIVE_PROJECTS.md")
    memory_index_text = _read_text(memory_dir / "MEMORY_INDEX.md")
    active_project_rows = _active_project_rows(active_projects_text)
    reminder_lines = _reminder_lines(memory_index_text)
    git_summary = _git_summary(repo_root=repo_root, runner=runner)

    warnings = _health_warnings(
        git_summary=git_summary,
        active_projects_text=active_projects_text,
        memory_index_text=memory_index_text,
        reminder_lines=reminder_lines,
    )
    pending_items = _pending_items(
        active_project_rows,
        reminder_lines,
        include_reminder_details=normalized_mode == "full",
    )
    suggested_next_action = _suggested_next_action(
        git_summary=git_summary,
        warnings=warnings,
        pending_items=pending_items,
    )

    return HealthCheckResult(
        mode=normalized_mode,
        git_summary=git_summary,
        a1_items=tuple(_a1_items(active_project_rows)),
        pending_items=tuple(pending_items if normalized_mode == "full" else pending_items[:4]),
        reminder_count=len(reminder_lines),
        warnings=tuple(warnings if normalized_mode == "full" else warnings[:5]),
        suggested_next_action=suggested_next_action,
    )


def _normalize_mode(mode: str) -> str:
    normalized = mode.strip().casefold()
    if normalized in {"quick", "full"}:
        return normalized
    return "quick"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _git_summary(repo_root: Path, runner: Runner) -> str:
    try:
        completed = runner(
            ["git", "status", "--short", "--branch"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return f"unknown (git status failed: {exc})"

    if completed.returncode != 0:
        stderr = " ".join(completed.stderr.split())
        return f"unknown (git status returned {completed.returncode}: {stderr})"

    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    branch = lines[0] if lines else "unknown branch"
    changes = lines[1:]
    if not changes:
        return f"clean, {branch}"
    return f"dirty ({len(changes)} changed/untracked), {branch}"


def _active_project_rows(active_projects_text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    headers: list[str] = []
    for line in active_projects_text.splitlines():
        if not line.startswith("| ") or "---" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not headers:
            headers = [_normalize_project_header(cell) for cell in cells]
            continue
        if len(cells) < len(headers):
            cells.extend([""] * (len(headers) - len(cells)))
        row = dict(zip(headers, cells[: len(headers)], strict=False))
        if _project_lifecycle(row) == "archived":
            continue
        rows.append(row)
    return rows


def _normalize_project_header(value: str) -> str:
    return {
        "oblast": "oblast",
        "priorita": "priorita",
        "stav": "stav",
        "rezim": "rezim",
        "režim": "rezim",
        "memory soubor": "memory",
        "handoff": "handoff",
        "dalsi krok": "dalsi",
        "další krok": "dalsi",
    }.get(value.strip().casefold(), value.strip().casefold().replace(" ", "_"))


def _project_lifecycle(row: dict[str, str]) -> str:
    value = (row.get("rezim") or "").strip().casefold()
    if value in {"archiv", "archivni", "archivní", "archive", "archived"}:
        return "archived"
    return "active"


def _a1_items(rows: Sequence[dict[str, str]]) -> list[str]:
    items: list[str] = []
    for row in rows:
        if row.get("priorita") == "A1+":
            items.append(f"{row.get('oblast', '')}: {row.get('dalsi', '')}")
    return items


def _reminder_lines(memory_index_text: str) -> list[str]:
    return [
        " ".join(line.removeprefix("- ").split())
        for line in memory_index_text.splitlines()
        if "[PRIPOMENOUT]" in line
    ]


def _pending_items(
    rows: Sequence[dict[str, str]],
    reminder_lines: Sequence[str],
    *,
    include_reminder_details: bool,
) -> list[str]:
    pending: list[str] = []
    markers = (
        "pending",
        "povinne",
        "povinné",
        "fyzicky",
        "T-Mobile",
        "2026-06-01",
        "watchdog",
        "GitHub Actions",
        "owl_230526",
        "owl_240526",
    )
    for row in rows:
        text = f"{row.get('oblast', '')} {row.get('stav', '')} {row.get('dalsi', '')}"
        if any(marker.casefold() in text.casefold() for marker in markers):
            pending.append(f"{row.get('oblast', '')}: {row.get('dalsi', '')}")
    if include_reminder_details or not pending:
        for line in reminder_lines:
            if any(marker.casefold() in line.casefold() for marker in markers):
                pending.append(line)
    return _dedupe(pending)


def _health_warnings(
    *,
    git_summary: str,
    active_projects_text: str,
    memory_index_text: str,
    reminder_lines: Sequence[str],
) -> list[str]:
    warnings: list[str] = []
    dirty_count = _git_dirty_count(git_summary)
    if dirty_count >= DIRTY_REPO_WARNING_THRESHOLD:
        warnings.append(
            f"Repo ma {dirty_count} rozpracovane/zmenene soubory; vhodny je ad hoc commitovy uklid."
        )

    for line in reminder_lines:
        folded = line.casefold()
        if "historicky" in folded or "prekryto" in folded or "překryto" in folded:
            warnings.append(f"Historicky/prekrity handoff zustal aktivni: {line}")

    for source_name, text in (
        ("ACTIVE_PROJECTS.md", active_projects_text),
        ("MEMORY_INDEX.md", memory_index_text),
    ):
        for line_number, line in enumerate(text.splitlines(), start=1):
            folded = line.casefold()
            if any(marker in folded for marker in RELATIVE_TIME_MARKERS):
                warnings.append(
                    f"{source_name}:{line_number} obsahuje relativni nebo git-stavovou formulaci: {line.strip()}"
                )
    return _dedupe(warnings)


def _git_dirty_count(git_summary: str) -> int:
    match = re.search(r"dirty \((\d+) changed/untracked\)", git_summary)
    if not match:
        return 0
    return int(match.group(1))


def _suggested_next_action(
    *,
    git_summary: str,
    warnings: Sequence[str],
    pending_items: Sequence[str],
) -> str:
    if git_summary.startswith("dirty"):
        return "Udelat tematicky commitovy uklid nebo rozhodnout, co zustava rozpracovane."
    if warnings:
        return "Provest memory cleanup varovani a po nem maly commit/push."
    if pending_items:
        return "Pokračovat podle prvni pending polozky nebo ji vedome odlozit."
    return "Bez okamzite akce; pokracovat podle aktualni priority v ACTIVE_PROJECTS.md."


def _format_result(result: HealthCheckResult) -> str:
    lines = [
        "Samantha Health Check",
        f"- Mode: {result.mode}",
        f"- Git: {result.git_summary}",
        f"- Aktivni [PRIPOMENOUT]: {result.reminder_count}",
    ]

    lines.append("")
    lines.append("A1+ pravidla:")
    if result.a1_items:
        lines.extend(f"- {item}" for item in result.a1_items)
    else:
        lines.append("- Nenalezena.")

    lines.append("")
    lines.append("Pending / hlidane veci:")
    if result.pending_items:
        lines.extend(f"- {item}" for item in result.pending_items)
    else:
        lines.append("- Nenalezeny.")

    lines.append("")
    lines.append("Varovani:")
    if result.warnings:
        lines.extend(f"- {warning}" for warning in result.warnings)
    else:
        lines.append("- Zadna kriticka varovani.")

    lines.append("")
    lines.append(f"Doporuceny dalsi krok: {result.suggested_next_action}")
    return "\n".join(lines)


def _dedupe(items: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result
