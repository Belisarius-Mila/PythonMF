"""Confirmed deployment of one audited Human–Adam checkpoint."""

from __future__ import annotations

import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, TYPE_CHECKING

from app.codex_appserver import AppServerError
from app.remote_work_cell import RemoteWorkspaceManager
from scripts.human_adam_takeover import (
    CONFIRMATION_TEXT,
    TakeoverError,
    TakeoverPlan,
    apply_takeover,
    build_takeover_plan,
)

if TYPE_CHECKING:
    from app.communication.human_adam_service import HumanAdamService


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRUSTED_PYTHON = Path(sys.executable)
DEFAULT_GATE_LOG = PROJECT_ROOT / "data" / "private" / "communication" / "human_adam_deploy_gate.log"
DEPLOYMENT_LOCK = threading.Lock()
MAX_GATE_LOG_CHARS = 2_000_000


class HumanAdamDeployError(AppServerError):
    """Raised before main changes when a deployment proof is not sufficient."""


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


def _public_plan(plan: TakeoverPlan) -> dict[str, Any]:
    return {
        **plan.public_dict(),
        "checkpoint_token": plan.checkpoint_head,
        "confirmation_text": CONFIRMATION_TEXT,
    }


def audit_checkpoint(*, workspace: RemoteWorkspaceManager) -> dict[str, Any]:
    """Read-only proof of the exact checkpoint and paths offered for deployment."""
    return _public_plan(build_takeover_plan(workspace=workspace))


def run_checkpoint_quality_gate(
    *,
    workspace: RemoteWorkspaceManager,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    log_path: Path = DEFAULT_GATE_LOG,
    timeout: float = 420.0,
) -> GateEvidence:
    gate_script = workspace.project_root / "scripts" / "cockpit_quality_gate.py"
    if not TRUSTED_PYTHON.is_file() or not gate_script.is_file():
        raise HumanAdamDeployError("Chybí důvěryhodné Python prostředí nebo quality gate checkpointu.")
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
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HumanAdamDeployError("Plná brána checkpointu se nedokončila; nic nebylo nasazeno.") from exc
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
        log_path=str(log_path.relative_to(PROJECT_ROOT)) if log_path.is_relative_to(PROJECT_ROOT) else str(log_path),
    )
    if not evidence.passed:
        raise HumanAdamDeployError(
            f"Plná brána checkpointu neprošla; nic nebylo nasazeno. Log: {evidence.log_path}"
        )
    return evidence


def deploy_checkpoint(
    *,
    workspace: RemoteWorkspaceManager,
    confirmation: str,
    expected_checkpoint_head: str,
    gate_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    gate_log_path: Path = DEFAULT_GATE_LOG,
) -> dict[str, Any]:
    if str(confirmation or "").strip() != CONFIRMATION_TEXT:
        raise HumanAdamDeployError(f"Chybí přesná potvrzovací věta: {CONFIRMATION_TEXT}")
    expected = str(expected_checkpoint_head or "").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", expected):
        raise HumanAdamDeployError("Chybí platný audit token checkpointu; spusť audit znovu.")
    if not DEPLOYMENT_LOCK.acquire(blocking=False):
        raise HumanAdamDeployError("Jiné nasazení Human–Adam už probíhá.")
    try:
        plan = build_takeover_plan(workspace=workspace)
        if plan.checkpoint_head != expected:
            raise HumanAdamDeployError("Checkpoint se od auditu změnil; spusť audit znovu.")
        evidence = run_checkpoint_quality_gate(
            workspace=workspace,
            runner=gate_runner,
            log_path=gate_log_path,
        )
        refreshed = build_takeover_plan(workspace=workspace)
        if refreshed != plan or refreshed.checkpoint_head != expected:
            raise HumanAdamDeployError("Stav se během plné brány změnil; nic nebylo nasazeno.")
        applied = apply_takeover(
            confirmation=CONFIRMATION_TEXT,
            push=True,
            workspace=workspace,
        )
        return {
            **applied,
            "checkpoint_token": expected,
            "gate": evidence.public_dict(),
            "restart_required": True,
        }
    finally:
        DEPLOYMENT_LOCK.release()


def _turn_busy(service: HumanAdamService) -> bool:
    return bool(service.hub.snapshot().get("turn_busy"))


def human_adam_deploy_audit_action(*, service: HumanAdamService) -> dict[str, Any]:
    try:
        if _turn_busy(service):
            raise HumanAdamDeployError("Audit nelze spustit během aktivního tahu Adama.")
        return audit_checkpoint(workspace=service.workspace)
    except (HumanAdamDeployError, TakeoverError, AppServerError, OSError, ValueError) as exc:
        return {"ok": False, "ready": False, "message": str(exc)}


def human_adam_deploy_action(
    payload: dict[str, Any],
    *,
    service: HumanAdamService,
) -> dict[str, Any]:
    try:
        if _turn_busy(service):
            raise HumanAdamDeployError("Nasazení nelze spustit během aktivního tahu Adama.")
        result = deploy_checkpoint(
            workspace=service.workspace,
            confirmation=str(payload.get("confirmation") or ""),
            expected_checkpoint_head=str(payload.get("checkpoint_token") or ""),
        )
        return {"ok": True, **result}
    except (HumanAdamDeployError, TakeoverError, AppServerError, OSError, ValueError) as exc:
        return {"ok": False, "ready": False, "message": str(exc)}
