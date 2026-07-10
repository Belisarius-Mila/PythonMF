#!/usr/bin/env python3
"""Canonical local/CI quality gate for Samantha Cockpit changes."""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]

COMPILE_PATHS = (
    "app/cockpit.py",
    "app/file_persistence.py",
    "app/backup/activity_state.py",
    "app/speech/adam_voice_mode.py",
    "app/speech/terminal_bridge.py",
    "scripts/cockpit_server.py",
    "scripts/cockpit_smoke_check.py",
    "scripts/migrate_cockpit_single_instance.py",
)

TEST_MODULES = (
    "tests.test_cockpit_quality_gate",
    "tests.test_file_persistence",
    "tests.test_backup_activity_state",
    "tests.test_backup_incremental",
    "tests.test_project_audit_report",
    "tests.test_cockpit",
    "tests.test_cockpit_http_security",
    "tests.test_terminal_bridge",
    "tests.test_adam_voice_mode",
    "tests.test_speech_transcribe",
    "tests.test_email_outbound_tools",
    "tests.test_document_vault_tools",
    "tests.test_document_consistency_audit",
    "tests.test_migrate_cockpit_single_instance",
)


@dataclass(frozen=True)
class SourceMetrics:
    lines: int
    functions: int
    classes: int


ARCHITECTURE_BASELINES = {
    "app/cockpit.py": SourceMetrics(lines=22_465, functions=332, classes=2),
    "app/speech/adam_voice_mode.py": SourceMetrics(lines=1_105, functions=39, classes=1),
}


def source_metrics(path: Path) -> SourceMetrics:
    source = path.read_text(encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        tree = ast.parse(source, filename=str(path))
    functions = sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in tree.body)
    classes = sum(isinstance(node, ast.ClassDef) for node in tree.body)
    return SourceMetrics(lines=len(source.splitlines()), functions=functions, classes=classes)


def architecture_messages() -> list[str]:
    messages: list[str] = []
    for relative_path, baseline in ARCHITECTURE_BASELINES.items():
        current = source_metrics(PROJECT_ROOT / relative_path)
        delta = current.lines - baseline.lines
        delta_text = f"{delta:+d} vs baseline"
        messages.append(
            f"- {relative_path}: {current.lines} lines, "
            f"{current.functions} functions, {current.classes} classes ({delta_text})"
        )
        if delta > 0:
            messages.append(
                "  WARNING: monolith grew; prefer a new/extracted module for additional domain logic."
            )
    return messages


def run_checked(label: str, command: Sequence[str]) -> None:
    print(f"\n[{label}] {' '.join(command)}", flush=True)
    started = time.monotonic()
    completed = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    elapsed = time.monotonic() - started
    if completed.returncode != 0:
        raise SystemExit(f"{label} failed with exit code {completed.returncode} after {elapsed:.1f}s")
    print(f"{label}: OK ({elapsed:.1f}s)", flush=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the canonical Samantha Cockpit quality gate.")
    parser.add_argument(
        "--skip-unit-tests",
        action="store_true",
        help="Run only whitespace, metrics and syntax checks.",
    )
    parser.add_argument(
        "--skip-git-diff-check",
        action="store_true",
        help="Skip git diff --check (useful outside a Git worktree).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print("Samantha Cockpit quality gate")
    print("Architecture metrics (informational, never a hard failure):")
    for message in architecture_messages():
        print(message)

    if not args.skip_git_diff_check:
        run_checked("whitespace", ["git", "diff", "--check"])
    run_checked(
        "syntax",
        [sys.executable, "-W", "error::SyntaxWarning", "-m", "py_compile", *COMPILE_PATHS],
    )
    if not args.skip_unit_tests:
        run_checked("unit tests", [sys.executable, "-m", "unittest", *TEST_MODULES])

    print("\nCockpit quality gate: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
