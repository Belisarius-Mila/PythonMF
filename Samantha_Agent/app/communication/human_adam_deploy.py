"""Confirmed deployment of one audited Human–Adam checkpoint."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, TYPE_CHECKING

from app.codex_appserver import AppServerError, utc_now
from app.file_persistence import FilePersistenceError, atomic_write_json
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
DEFAULT_DEPLOYMENT_RECEIPT = (
    PROJECT_ROOT / "data" / "private" / "communication" / "human_adam_deployment_receipt.json"
)
DEPLOYMENT_LOCK = threading.Lock()
MAX_GATE_LOG_CHARS = 2_000_000
DEPLOYMENT_RECEIPT_SCHEMA = 1
DEPLOYMENT_PENDING = "gate_passed_pending_apply"
DEPLOYMENT_COMPLETE = "deployed"


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


def _thread_key(thread_id: str) -> str:
    clean_thread_id = str(thread_id or "").strip()
    if not clean_thread_id:
        raise HumanAdamDeployError("Chybí identita Human–Adam vlákna pro potvrzení nasazení.")
    return hashlib.sha256(clean_thread_id.encode("utf-8")).hexdigest()


def _deployment_receipt_payload(
    *,
    checkpoint_head: str,
    thread_id: str,
    state: str,
    recorded_at: str,
    deployed_at: str = "",
) -> dict[str, Any]:
    clean_head = str(checkpoint_head or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", clean_head):
        raise HumanAdamDeployError("Potvrzení nasazení nemá platný commit.")
    if state not in {DEPLOYMENT_PENDING, DEPLOYMENT_COMPLETE}:
        raise HumanAdamDeployError("Potvrzení nasazení má neplatný stav.")
    return {
        "schema_version": DEPLOYMENT_RECEIPT_SCHEMA,
        "state": state,
        "thread_key": _thread_key(thread_id),
        "checkpoint_head": clean_head,
        "gate_passed": True,
        "recorded_at": str(recorded_at or "").strip(),
        "deployed_at": str(deployed_at or "").strip(),
    }


def write_deployment_receipt(
    path: Path,
    *,
    checkpoint_head: str,
    thread_id: str,
    state: str,
    recorded_at: str,
    deployed_at: str = "",
) -> dict[str, Any]:
    payload = _deployment_receipt_payload(
        checkpoint_head=checkpoint_head,
        thread_id=thread_id,
        state=state,
        recorded_at=recorded_at,
        deployed_at=deployed_at,
    )
    try:
        atomic_write_json(Path(path), payload, ensure_ascii=False, indent=2)
    except (FilePersistenceError, OSError) as exc:
        raise HumanAdamDeployError("Trvalé potvrzení nasazení nelze bezpečně uložit.") from exc
    return payload


def load_deployment_confirmation(
    path: Path,
    *,
    thread_id: str,
) -> dict[str, Any] | None:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict) or raw.get("schema_version") != DEPLOYMENT_RECEIPT_SCHEMA:
        return None
    try:
        expected_thread_key = _thread_key(thread_id)
    except HumanAdamDeployError:
        return None
    checkpoint_head = str(raw.get("checkpoint_head") or "").strip().lower()
    state = str(raw.get("state") or "").strip()
    if (
        raw.get("thread_key") != expected_thread_key
        or raw.get("gate_passed") is not True
        or not re.fullmatch(r"[0-9a-f]{40}", checkpoint_head)
        or state != DEPLOYMENT_COMPLETE
    ):
        return None
    completed_at = str(raw.get("deployed_at") or raw.get("recorded_at") or "").strip()
    if not completed_at:
        return None
    try:
        completed_at = datetime.fromisoformat(completed_at.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return None
    return {
        "checkpoint_short": checkpoint_head[:7],
        "gate_passed": True,
        "completed_at": completed_at,
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
    thread_id: str = "",
    deployment_receipt_path: Path | None = None,
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
        receipt_recorded_at = utc_now()
        if deployment_receipt_path is not None:
            write_deployment_receipt(
                deployment_receipt_path,
                checkpoint_head=expected,
                thread_id=thread_id,
                state=DEPLOYMENT_PENDING,
                recorded_at=receipt_recorded_at,
            )
        applied = apply_takeover(
            confirmation=CONFIRMATION_TEXT,
            push=True,
            workspace=workspace,
        )
        final_workspace = workspace.status()
        if (
            applied.get("applied") is not True
            or applied.get("pushed") is not True
            or applied.get("workspace_aligned") is not True
            or str(final_workspace.get("source_head") or "").strip().lower() != expected
            or str(final_workspace.get("head") or "").strip().lower() != expected
            or final_workspace.get("workspace_relation") != "aligned"
            or bool(final_workspace.get("dirty"))
            or bool(final_workspace.get("remotes"))
        ):
            raise HumanAdamDeployError(
                "Nasazení neposkytlo úplný důkaz fast-forwardu, pushnutí a zarovnání workspace."
            )
        deployment_confirmation = None
        receipt_warning = ""
        if deployment_receipt_path is not None:
            try:
                write_deployment_receipt(
                    deployment_receipt_path,
                    checkpoint_head=expected,
                    thread_id=thread_id,
                    state=DEPLOYMENT_COMPLETE,
                    recorded_at=receipt_recorded_at,
                    deployed_at=utc_now(),
                )
            except (HumanAdamDeployError, FilePersistenceError, OSError):
                receipt_warning = "Nasazení proběhlo; potvrzení zůstalo v obnovitelném mezistavu."
            deployment_confirmation = load_deployment_confirmation(
                deployment_receipt_path,
                thread_id=thread_id,
            )
        return {
            **applied,
            "checkpoint_token": expected,
            "gate": evidence.public_dict(),
            "restart_required": True,
            "deployment_confirmation": deployment_confirmation,
            "receipt_warning": receipt_warning,
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
        session = service.hub.snapshot()
        if session.get("turn_busy"):
            raise HumanAdamDeployError("Nasazení nelze spustit během aktivního tahu Adama.")
        result = deploy_checkpoint(
            workspace=service.workspace,
            confirmation=str(payload.get("confirmation") or ""),
            expected_checkpoint_head=str(payload.get("checkpoint_token") or ""),
            thread_id=str(session.get("thread_id") or ""),
            deployment_receipt_path=service.deployment_receipt_path,
        )
        return {"ok": True, **result}
    except (HumanAdamDeployError, TakeoverError, AppServerError, OSError, ValueError) as exc:
        return {"ok": False, "ready": False, "message": str(exc)}
