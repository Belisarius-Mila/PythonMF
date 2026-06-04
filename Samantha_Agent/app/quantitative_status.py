from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
DEFAULT_METRICS_PATH = PROJECT_ROOT / "data" / "metrics" / "samantha_quantitative_status.jsonl"

EXCLUDED_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
}

EXCLUDED_RELATIVE_DIRS = {
    Path("data/private"),
    Path("data/session_autosave"),
    Path("data/email/archive"),
    Path("data/metrics"),
    Path("data/tmp"),
    Path("logs"),
}

TEXT_EXTENSIONS = {
    "",
    ".command",
    ".css",
    ".csv",
    ".example",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".rules",
    ".sh",
    ".swift",
    ".txt",
}

Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class ExtensionStats:
    files: int = 0
    lines: int = 0


@dataclass(frozen=True)
class QuantitativeStatusResult:
    created_at: str
    git_summary: str
    local_stats: dict[str, ExtensionStats]
    git_stats: dict[str, ExtensionStats]
    stored_path: Path | None


def format_samantha_quantitative_status(
    *,
    save: bool = False,
    project_root: Path = PROJECT_ROOT,
    repo_root: Path = REPO_ROOT,
    metrics_path: Path = DEFAULT_METRICS_PATH,
    runner: Runner = subprocess.run,
) -> str:
    result = run_samantha_quantitative_status(
        save=save,
        project_root=project_root,
        repo_root=repo_root,
        metrics_path=metrics_path,
        runner=runner,
    )
    return _format_result(result)


def run_samantha_quantitative_status(
    *,
    save: bool = False,
    project_root: Path = PROJECT_ROOT,
    repo_root: Path = REPO_ROOT,
    metrics_path: Path = DEFAULT_METRICS_PATH,
    runner: Runner = subprocess.run,
) -> QuantitativeStatusResult:
    created_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    local_stats = _stats_for_files(_iter_local_files(project_root), base_root=project_root)
    git_stats = _stats_for_files(_iter_git_files(project_root, repo_root, runner), base_root=project_root)
    git_summary = _git_summary(repo_root=repo_root, runner=runner)
    stored_path = None

    result = QuantitativeStatusResult(
        created_at=created_at,
        git_summary=git_summary,
        local_stats=local_stats,
        git_stats=git_stats,
        stored_path=None,
    )
    if save:
        _append_metric_row(metrics_path, result)
        stored_path = metrics_path
        result = QuantitativeStatusResult(
            created_at=result.created_at,
            git_summary=result.git_summary,
            local_stats=result.local_stats,
            git_stats=result.git_stats,
            stored_path=stored_path,
        )
    return result


def _iter_local_files(project_root: Path) -> Iterable[Path]:
    if not project_root.exists():
        return []
    files: list[Path] = []
    for root, dir_names, file_names in os.walk(project_root):
        root_path = Path(root)
        dir_names[:] = [
            dir_name
            for dir_name in dir_names
            if not _is_excluded((root_path / dir_name).relative_to(project_root))
        ]
        for file_name in file_names:
            path = root_path / file_name
            relative = path.relative_to(project_root)
            if not _is_excluded(relative):
                files.append(path)
    return files


def _iter_git_files(project_root: Path, repo_root: Path, runner: Runner) -> list[Path]:
    try:
        completed = runner(
            ["git", "ls-files", str(project_root.relative_to(repo_root))],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except (OSError, ValueError):
        return []
    if completed.returncode != 0:
        return []
    files: list[Path] = []
    for line in completed.stdout.splitlines():
        if not line.startswith(f"{project_root.name}/"):
            continue
        path = repo_root / line
        if path.is_file() and not _is_excluded(path.relative_to(project_root)):
            files.append(path)
    return files


def _is_excluded(relative: Path) -> bool:
    parts = relative.parts
    if any(part in EXCLUDED_DIR_NAMES or part.startswith(".venv_") or part.startswith("tmp") for part in parts):
        return True
    return any(relative == excluded or excluded in relative.parents for excluded in EXCLUDED_RELATIVE_DIRS)


def _stats_for_files(files: Iterable[Path], *, base_root: Path) -> dict[str, ExtensionStats]:
    stats: dict[str, ExtensionStats] = {}
    for path in files:
        relative = path.relative_to(base_root)
        extension = _extension_label(relative)
        current = stats.get(extension, ExtensionStats())
        stats[extension] = ExtensionStats(
            files=current.files + 1,
            lines=current.lines + _line_count(path, extension),
        )
    return dict(sorted(stats.items(), key=lambda item: (-item[1].lines, -item[1].files, item[0])))


def _extension_label(path: Path) -> str:
    if path.name == ".env.example":
        return ".env.example"
    suffix = path.suffix.casefold()
    return suffix if suffix else "(no extension)"


def _line_count(path: Path, extension: str) -> int:
    if extension not in TEXT_EXTENSIONS and extension != ".env.example":
        return 0
    try:
        data = path.read_bytes()
    except OSError:
        return 0
    if not data:
        return 0
    return data.count(b"\n") + (0 if data.endswith(b"\n") else 1)


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


def _append_metric_row(metrics_path: Path, result: QuantitativeStatusResult) -> None:
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "created_at": result.created_at,
        "scope": "Samantha_Agent",
        "git_summary": result.git_summary,
        "local": _stats_to_json(result.local_stats),
        "git_tracked": _stats_to_json(result.git_stats),
        "totals": {
            "local": _totals_to_json(result.local_stats),
            "git_tracked": _totals_to_json(result.git_stats),
        },
    }
    with metrics_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _stats_to_json(stats: dict[str, ExtensionStats]) -> dict[str, dict[str, int]]:
    return {extension: {"files": item.files, "lines": item.lines} for extension, item in stats.items()}


def _totals_to_json(stats: dict[str, ExtensionStats]) -> dict[str, int]:
    return {
        "files": sum(item.files for item in stats.values()),
        "lines": sum(item.lines for item in stats.values()),
    }


def _format_result(result: QuantitativeStatusResult) -> str:
    local_totals = _totals_to_json(result.local_stats)
    git_totals = _totals_to_json(result.git_stats)
    lines = [
        "Samantha Quantitative Status",
        f"- Created: {result.created_at}",
        "- Scope: Samantha_Agent",
        f"- Git: {result.git_summary}",
        f"- Stored: {_stored_line(result.stored_path)}",
        "",
        "Souhrn:",
        "| Metrika | Lokalni | Git tracked |",
        "| --- | ---: | ---: |",
        f"| Soubory | {local_totals['files']} | {git_totals['files']} |",
        f"| Radky textu | {local_totals['lines']} | {git_totals['lines']} |",
        "",
        "Lokalni objem podle typu:",
        "| Typ | Soubory | Radky |",
        "| --- | ---: | ---: |",
        *_table_rows(result.local_stats),
        "",
        "Git tracked objem podle typu:",
        "| Typ | Soubory | Radky |",
        "| --- | ---: | ---: |",
        *_table_rows(result.git_stats),
    ]
    return "\n".join(lines)


def _stored_line(path: Path | None) -> str:
    if path is None:
        return "ne (pouzij --save pro ulozeni datove vety)"
    return str(path)


def _table_rows(stats: dict[str, ExtensionStats], *, limit: int = 12) -> list[str]:
    rows = [
        f"| `{extension}` | {item.files} | {item.lines} |"
        for extension, item in list(stats.items())[:limit]
    ]
    return rows or ["| - | 0 | 0 |"]
