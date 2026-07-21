"""Shared quality-gate runner for canonical checkpoint and deployment flows."""

from __future__ import annotations

import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.codex_appserver import AppServerError
from app.communication.human_adam_workspace import HumanAdamWorkspaceManager


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRUSTED_PYTHON = Path(sys.executable)
DEFAULT_GATE_LOG = PROJECT_ROOT / "data" / "private" / "communication" / "human_adam_deploy_gate.log"
MAX_GATE_LOG_CHARS = 2_000_000
GATE_FAILURE_TYPES = frozenset(
    {
        "syntax_error",
        "test_failure",
        "gate_timeout",
        "gate_process_error",
        "gate_failure",
    }
)


class HumanAdamGateError(AppServerError):
    """Quality-gate failure carrying only one allowlisted postmortem category."""

    def __init__(self, message: str, *, failure_type: str):
        if failure_type not in GATE_FAILURE_TYPES:
            failure_type = "gate_failure"
        self.failure_type = failure_type
        super().__init__(message)


@dataclass(frozen=True)
class GateEvidence:
    passed: bool
    returncode: int
    test_count: int
    duration_seconds: float
    log_path: str

    def public_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "returncode": self.returncode,
            "test_count": self.test_count,
            "duration_seconds": self.duration_seconds,
            "log_path": self.log_path,
        }


def run_checkpoint_quality_gate(
    *,
    workspace: HumanAdamWorkspaceManager,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    log_path: Path = DEFAULT_GATE_LOG,
    timeout: float = 420.0,
) -> GateEvidence:
    gate_script = workspace.project_root / "scripts" / "cockpit_quality_gate.py"
    if not TRUSTED_PYTHON.is_file() or not gate_script.is_file():
        raise HumanAdamGateError(
            "Chybí důvěryhodné Python prostředí nebo quality gate checkpointu.",
            failure_type="gate_process_error",
        )
    started = time.monotonic()
    try:
        completed = runner(
            [str(TRUSTED_PYTHON), str(gate_script)],
            cwd=str(workspace.project_root),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise HumanAdamGateError(
            "Plná brána checkpointu se nedokončila; nic nebylo nasazeno.",
            failure_type="gate_timeout",
        ) from exc
    except OSError as exc:
        raise HumanAdamGateError(
            "Plná brána checkpointu se nedokončila; nic nebylo nasazeno.",
            failure_type="gate_process_error",
        ) from exc
    duration = round(time.monotonic() - started, 1)
    output = f"{completed.stdout or ''}\n{completed.stderr or ''}".strip()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(output[-MAX_GATE_LOG_CHARS:] + "\n", encoding="utf-8")
    matches = re.findall(r"Ran\s+(\d+)\s+tests", output)
    evidence = GateEvidence(
        passed=completed.returncode == 0 and "Cockpit quality gate: OK" in output,
        returncode=int(completed.returncode),
        test_count=int(matches[-1]) if matches else 0,
        duration_seconds=duration,
        log_path=(
            str(log_path.relative_to(PROJECT_ROOT))
            if log_path.is_relative_to(PROJECT_ROOT)
            else str(log_path)
        ),
    )
    if not evidence.passed:
        folded_output = output.casefold()
        failure_type = (
            "syntax_error"
            if "syntaxerror" in folded_output
            or re.search(
                r"(?:python|javascript|shell)?\s*syntax:\s*(?:failed|error)",
                folded_output,
            )
            else (
                "test_failure"
                if "failed" in folded_output or "error" in folded_output
                else "gate_failure"
            )
        )
        raise HumanAdamGateError(
            f"Plná brána checkpointu neprošla; nic nebylo nasazeno. Log: {evidence.log_path}",
            failure_type=failure_type,
        )
    return evidence
