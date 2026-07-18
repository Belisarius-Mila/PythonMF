#!/usr/bin/env python3
"""Canonical local/CI quality gate for Samantha Cockpit changes."""

from __future__ import annotations

import argparse
import ast
import os
import re
import shutil
import subprocess
import sys
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NODE_FALLBACK_PATHS = (
    Path("/opt/homebrew/bin/node"),
    Path("/usr/local/bin/node"),
)

COMPILE_PATHS = (
    "app/cockpit.py",
    "app/command_cheatsheet.py",
    "app/cockpit_code_stamp.py",
    "app/cockpit_status_service.py",
    "app/voice_bridge_coordinator.py",
    "app/voice_bridge_runtime.py",
    "app/voice_bridge_state.py",
    "app/tvbcp.py",
    "app/adam_service.py",
    "app/autosave_service.py",
    "app/codex_appserver.py",
    "app/communication/human_adam_profiles.py",
    "app/communication/human_adam_service.py",
    "app/communication/human_adam_deploy.py",
    "app/communication/human_adam_ui.py",
    "app/communication/human_adam_workspace.py",
    "app/communication/local_runtime.py",
    "app/communication/session_hub.py",
    "app/file_persistence.py",
    "app/work_repository.py",
    "app/email/work_outbox.py",
    "app/email/work_repository.py",
    "app/email/work_models.py",
    "app/backup/activity_state.py",
    "app/documents/scandocu.py",
    "app/documents/case_service.py",
    "app/documents/due_date_service.py",
    "app/documents/intake_service.py",
    "app/documents/intake_models.py",
    "app/documents/review_service.py",
    "app/documents/search_service.py",
    "app/documents/vault.py",
    "app/documents/transactions.py",
    "app/quick_notes.py",
    "app/urgent_reminders.py",
    "app/reminders/store.py",
    "app/reminders/query_tools.py",
    "app/speech/adam_voice_mode.py",
    "app/speech/terminal_bridge.py",
    "scripts/cockpit_server.py",
    "scripts/open_cockpit.py",
    "scripts/cockpit_launchd_runner.py",
    "scripts/restart_cockpit.py",
    "scripts/cockpit_smoke_check.py",
    "scripts/email_work_outbox_pilot.py",
    "scripts/autosave_status.py",
    "scripts/migrate_cockpit_single_instance.py",
    "scripts/tvbcp.py",
    "scripts/codex_appserver_shared_thread_probe.py",
    "scripts/human_adam_takeover.py",
)

SHELL_PATHS = (
    "scripts/autosave_codex_session.sh",
    "scripts/samantha_screen_entry.sh",
)

TEST_MODULES = (
    "tests.test_cockpit_quality_gate",
    "tests.test_cockpit_status_service",
    "tests.test_command_cheatsheet",
    "tests.test_codex_appserver",
    "tests.test_codex_appserver_shared_thread_probe",
    "tests.test_communication_session_hub",
    "tests.test_human_adam_profiles",
    "tests.test_human_adam_service",
    "tests.test_human_adam_deploy",
    "tests.test_human_adam_ui",
    "tests.test_human_adam_workspace",
    "tests.test_human_adam_takeover",
    "tests.test_local_appserver_runtime",
    "tests.test_voice_bridge_coordinator",
    "tests.test_voice_bridge_runtime",
    "tests.test_voice_bridge_state",
    "tests.test_tvbcp",
    "tests.test_file_persistence",
    "tests.test_backup_activity_state",
    "tests.test_backup_incremental",
    "tests.test_project_audit_report",
    "tests.test_open_cockpit",
    "tests.test_restart_cockpit",
    "tests.test_quick_notes",
    "tests.test_urgent_reminders",
    "tests.test_reminders_store",
    "tests.test_reminders_query_tools",
    "tests.test_cockpit",
    "tests.test_cockpit_http_security",
    "tests.test_adam_service",
    "tests.test_safety_quick_checks",
    "tests.test_terminal_bridge",
    "tests.test_adam_voice_mode",
    "tests.test_speech_transcribe",
    "tests.test_email_outbound_tools",
    "tests.test_email_work_outbox",
    "tests.test_work_repository",
    "tests.test_email_work_repository",
    "tests.test_email_work_models",
    "tests.test_document_persistence",
    "tests.test_document_case_service",
    "tests.test_document_due_date_service",
    "tests.test_document_intake_service",
    "tests.test_document_intake_models",
    "tests.test_document_review_service",
    "tests.test_document_search_service",
    "tests.test_document_transactions",
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


def node_binary() -> str:
    """Find Node even when launchd supplies only the system PATH."""
    candidates: list[str] = []
    configured = str(os.environ.get("NODE_BINARY") or "").strip()
    if configured:
        candidates.append(configured)
    discovered = shutil.which("node")
    if discovered:
        candidates.append(discovered)
    candidates.extend(str(path) for path in NODE_FALLBACK_PATHS)
    for candidate in candidates:
        path = Path(candidate).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
    raise SystemExit(
        "javascript syntax failed: Node.js nebyl nalezen; nastav NODE_BINARY "
        "nebo nainstaluj node do /opt/homebrew/bin ci /usr/local/bin"
    )


def run_checked(label: str, command: Sequence[str], *, input_text: str | None = None) -> None:
    print(f"\n[{label}] {' '.join(command)}", flush=True)
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        input=input_text,
    )
    elapsed = time.monotonic() - started
    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n", flush=True)
    if completed.stderr:
        print(completed.stderr, end="" if completed.stderr.endswith("\n") else "\n", file=sys.stderr, flush=True)
    if completed.returncode != 0:
        if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
            detail = (completed.stderr or completed.stdout or "No subprocess output.")[-6_000:]
            escaped = detail.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
            print(f"::error title={label} failed::{escaped}", flush=True)
        raise SystemExit(f"{label} failed with exit code {completed.returncode} after {elapsed:.1f}s")
    print(f"{label}: OK ({elapsed:.1f}s)", flush=True)


def cockpit_javascript_source() -> str:
    project_root = str(PROJECT_ROOT)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from app.cockpit import COCKPIT_HTML

    scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", COCKPIT_HTML, flags=re.DOTALL)
    if not scripts:
        raise SystemExit("javascript syntax failed: Cockpit HTML neobsahuje script blok")
    return "\n".join(scripts)


def human_adam_javascript_source() -> str:
    project_root = str(PROJECT_ROOT)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from app.communication.human_adam_ui import HUMAN_ADAM_HTML

    scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", HUMAN_ADAM_HTML, flags=re.DOTALL)
    if not scripts:
        raise SystemExit("Human–Adam javascript syntax failed: stránka neobsahuje script blok")
    return "\n".join(scripts)


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
    run_checked(
        "javascript syntax",
        [node_binary(), "--check", "-"],
        input_text=cockpit_javascript_source(),
    )
    run_checked(
        "Human–Adam javascript syntax",
        [node_binary(), "--check", "-"],
        input_text=human_adam_javascript_source(),
    )
    run_checked("shell syntax", ["/bin/zsh", "-n", *SHELL_PATHS])
    if not args.skip_unit_tests:
        run_checked("unit tests", [sys.executable, "-m", "unittest", *TEST_MODULES])

    print("\nCockpit quality gate: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
