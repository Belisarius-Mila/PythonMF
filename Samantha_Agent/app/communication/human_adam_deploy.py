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
from app.file_persistence import FilePersistenceError, atomic_write_json, update_json_file
from app.communication.human_adam_workspace import HumanAdamWorkspaceManager
from app.communication.session_hub import SessionHubError
from scripts.human_adam_takeover import (
    CONFIRMATION_TEXT,
    TakeoverError,
    TakeoverPlan,
    apply_takeover,
    build_takeover_plan,
    refresh_origin_main,
)

if TYPE_CHECKING:
    from app.communication.human_adam_service import HumanAdamService


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRUSTED_PYTHON = Path(sys.executable)
DEFAULT_GATE_LOG = PROJECT_ROOT / "data" / "private" / "communication" / "human_adam_deploy_gate.log"
DEFAULT_DEPLOYMENT_RECEIPT = (
    PROJECT_ROOT / "data" / "private" / "communication" / "human_adam_deployment_receipt.json"
)
DEFAULT_DEPLOYMENT_DIAGNOSTIC = (
    PROJECT_ROOT / "data" / "private" / "communication" / "human_adam_deployment_diagnostic.json"
)
DEFAULT_DEPLOYMENT_FAILURE_HISTORY = (
    PROJECT_ROOT / "data" / "private" / "communication" / "human_adam_deployment_failures.json"
)
DEPLOYMENT_LOCK = threading.Lock()
MAX_GATE_LOG_CHARS = 2_000_000
MAX_DEPLOYMENT_FAILURE_RECORDS = 20
DEPLOYMENT_RECEIPT_SCHEMA = 1
DEPLOYMENT_DIAGNOSTIC_SCHEMA = 1
DEPLOYMENT_FAILURE_HISTORY_SCHEMA = 1
DEPLOYMENT_PENDING = "gate_passed_pending_apply"
DEPLOYMENT_COMPLETE = "deployed"
DEPLOYMENT_DIAGNOSTIC_STAGES = frozenset(
    {
        "audit",
        "gate",
        "receipt",
        "remote_recheck",
        "push",
        "fast_forward",
        "workspace_alignment",
        "restart",
    }
)
DEPLOYMENT_DIAGNOSTIC_OUTCOMES = frozenset({"running", "passed", "failed"})
DEPLOYMENT_FAILURE_TYPES = frozenset(
    {
        "audit_failure",
        "syntax_error",
        "test_failure",
        "gate_timeout",
        "gate_process_error",
        "gate_failure",
        "receipt_failure",
        "remote_recheck_failure",
        "push_failure",
        "fast_forward_failure",
        "workspace_alignment_failure",
        "restart_failure",
    }
)
DEPLOYMENT_DIAGNOSTIC_MESSAGES = {
    ("audit", "running"): "Ověřuji přesný checkpoint a stav Git.",
    ("audit", "passed"): "Audit checkpointu prošel.",
    ("audit", "failed"): "Audit checkpointu selhal.",
    ("gate", "running"): "Probíhá plná testovací brána.",
    ("gate", "passed"): "Plná testovací brána prošla.",
    ("gate", "failed"): "Plná testovací brána selhala; nic nebylo převzato.",
    ("receipt", "running"): "Ukládám bezpečný mezistav nasazení.",
    ("receipt", "passed"): "Bezpečný mezistav nasazení je uložený.",
    ("receipt", "failed"): "Bezpečný mezistav nasazení se nepodařilo uložit.",
    ("remote_recheck", "running"): "Znovu ověřuji aktuální main na GitHubu.",
    ("remote_recheck", "passed"): "GitHub main se během testovací brány nezměnil.",
    ("remote_recheck", "failed"): "GitHub main se změnil; lokální main zůstal beze změny.",
    ("fast_forward", "running"): "Probíhá fast-forward checkpointu do main.",
    ("fast_forward", "passed"): "Fast-forward checkpointu do main prošel.",
    ("fast_forward", "failed"): "Fast-forward checkpointu do main selhal.",
    ("push", "running"): "Probíhá push větve main.",
    ("push", "passed"): "Push větve main prošel.",
    ("push", "failed"): "Push větve main selhal; vzdálená větev není potvrzená.",
    ("workspace_alignment", "running"): "Ověřuji zarovnání izolovaného workspace.",
    ("workspace_alignment", "passed"): "Izolovaný workspace je zarovnaný.",
    ("workspace_alignment", "failed"): "Zarovnání izolovaného workspace selhalo.",
    ("restart", "running"): "Spouštím bezpečný restart Cockpitu.",
    ("restart", "passed"): "Bezpečný restart Cockpitu byl zahájen.",
    ("restart", "failed"): "Bezpečný restart Cockpitu se nepodařilo zahájit.",
}


class HumanAdamDeployError(AppServerError):
    """Raised before main changes when a deployment proof is not sufficient."""


class HumanAdamGateError(HumanAdamDeployError):
    """Quality-gate failure carrying only one allowlisted postmortem category."""

    def __init__(self, message: str, *, failure_type: str):
        if failure_type not in DEPLOYMENT_FAILURE_TYPES:
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


def write_deployment_diagnostic(
    path: Path,
    *,
    checkpoint_head: str,
    thread_id: str,
    stage: str,
    outcome: str,
    updated_at: str,
) -> dict[str, Any]:
    """Persist only allowlisted deployment progress, never exception details or paths."""
    clean_head = str(checkpoint_head or "").strip().lower()
    clean_stage = str(stage or "").strip()
    clean_outcome = str(outcome or "").strip()
    clean_updated_at = str(updated_at or "").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", clean_head):
        raise HumanAdamDeployError("Diagnostika nasazení nemá platný commit.")
    if clean_stage not in DEPLOYMENT_DIAGNOSTIC_STAGES:
        raise HumanAdamDeployError("Diagnostika nasazení má neplatnou fázi.")
    if clean_outcome not in DEPLOYMENT_DIAGNOSTIC_OUTCOMES:
        raise HumanAdamDeployError("Diagnostika nasazení má neplatný výsledek.")
    try:
        normalized_time = datetime.fromisoformat(clean_updated_at.replace("Z", "+00:00")).isoformat()
    except ValueError as exc:
        raise HumanAdamDeployError("Diagnostika nasazení nemá platný čas.") from exc
    payload = {
        "schema_version": DEPLOYMENT_DIAGNOSTIC_SCHEMA,
        "thread_key": _thread_key(thread_id),
        "checkpoint_head": clean_head,
        "stage": clean_stage,
        "outcome": clean_outcome,
        "updated_at": normalized_time,
    }
    try:
        atomic_write_json(Path(path), payload, ensure_ascii=False, indent=2)
    except (FilePersistenceError, OSError) as exc:
        raise HumanAdamDeployError("Diagnostiku nasazení nelze bezpečně uložit.") from exc
    return payload


def _normalized_deployment_failure_record(
    *,
    profile_id: str,
    checkpoint_head: str,
    stage: str,
    failure_type: str,
    recorded_at: str,
) -> dict[str, Any]:
    clean_profile_id = str(profile_id or "").strip().lower()
    clean_head = str(checkpoint_head or "").strip().lower()
    clean_stage = str(stage or "").strip()
    clean_failure_type = str(failure_type or "").strip()
    clean_recorded_at = str(recorded_at or "").strip()
    if not re.fullmatch(r"[a-z][a-z0-9_-]{1,31}", clean_profile_id):
        raise HumanAdamDeployError("Historie selhání nemá platný pracovní profil.")
    if not re.fullmatch(r"[0-9a-f]{40}", clean_head):
        raise HumanAdamDeployError("Historie selhání nemá platný checkpoint.")
    if clean_stage not in DEPLOYMENT_DIAGNOSTIC_STAGES:
        raise HumanAdamDeployError("Historie selhání nemá platnou fázi.")
    if clean_failure_type not in DEPLOYMENT_FAILURE_TYPES:
        raise HumanAdamDeployError("Historie selhání nemá platný typ chyby.")
    try:
        parsed_time = datetime.fromisoformat(clean_recorded_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HumanAdamDeployError("Historie selhání nemá platný čas.") from exc
    if parsed_time.tzinfo is None:
        raise HumanAdamDeployError("Historie selhání nemá časovou zónu.")
    return {
        "recorded_at": parsed_time.isoformat(),
        "profile_id": clean_profile_id,
        "checkpoint_head": clean_head,
        "stage": clean_stage,
        "failure_type": clean_failure_type,
    }


def write_deployment_failure(
    path: Path,
    *,
    profile_id: str,
    checkpoint_head: str,
    stage: str,
    failure_type: str,
    recorded_at: str,
) -> dict[str, Any]:
    """Append one redacted failure and retain only the newest bounded history."""
    record = _normalized_deployment_failure_record(
        profile_id=profile_id,
        checkpoint_head=checkpoint_head,
        stage=stage,
        failure_type=failure_type,
        recorded_at=recorded_at,
    )

    def updater(current: Any) -> dict[str, Any]:
        if not isinstance(current, dict) or current.get("schema_version") != DEPLOYMENT_FAILURE_HISTORY_SCHEMA:
            if current != {"schema_version": DEPLOYMENT_FAILURE_HISTORY_SCHEMA, "failures": []}:
                raise HumanAdamDeployError("Stávající historie selhání má neznámé schéma a nebyla přepsána.")
        existing = current.get("failures")
        if not isinstance(existing, list):
            raise HumanAdamDeployError("Stávající historie selhání je neplatná a nebyla přepsána.")
        normalized_existing = []
        for item in existing:
            if not isinstance(item, dict) or set(item) != set(record):
                raise HumanAdamDeployError("Stávající historie selhání je neplatná a nebyla přepsána.")
            normalized_existing.append(_normalized_deployment_failure_record(**item))
        return {
            "schema_version": DEPLOYMENT_FAILURE_HISTORY_SCHEMA,
            "failures": [*normalized_existing, record][-MAX_DEPLOYMENT_FAILURE_RECORDS:],
        }

    try:
        stored = update_json_file(
            Path(path),
            updater,
            default={"schema_version": DEPLOYMENT_FAILURE_HISTORY_SCHEMA, "failures": []},
            ensure_ascii=False,
            indent=2,
        )
    except (HumanAdamDeployError, FilePersistenceError, OSError, ValueError) as exc:
        if isinstance(exc, HumanAdamDeployError):
            raise
        raise HumanAdamDeployError("Historii selhání nasazení nelze bezpečně uložit.") from exc
    return dict(stored)


def load_deployment_failure_history(path: Path) -> list[dict[str, Any]]:
    """Load only strictly validated redacted records; malformed history is ignored."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(raw, dict) or raw.get("schema_version") != DEPLOYMENT_FAILURE_HISTORY_SCHEMA:
        return []
    failures = raw.get("failures")
    if not isinstance(failures, list) or len(failures) > MAX_DEPLOYMENT_FAILURE_RECORDS:
        return []
    normalized = []
    try:
        for item in failures:
            if not isinstance(item, dict) or set(item) != {
                "recorded_at",
                "profile_id",
                "checkpoint_head",
                "stage",
                "failure_type",
            }:
                return []
            normalized.append(_normalized_deployment_failure_record(**item))
    except HumanAdamDeployError:
        return []
    return normalized


def _record_deployment_failure(
    path: Path | None,
    *,
    profile_id: str,
    checkpoint_head: str,
    stage: str,
    failure_type: str,
) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        stored = write_deployment_failure(
            path,
            profile_id=profile_id,
            checkpoint_head=checkpoint_head,
            stage=stage,
            failure_type=failure_type,
            recorded_at=utc_now(),
        )
    except (HumanAdamDeployError, FilePersistenceError, OSError, ValueError):
        return None
    failures = stored.get("failures")
    return dict(failures[-1]) if isinstance(failures, list) and failures else None


def _deployment_failure_type(stage: str, exc: BaseException) -> str:
    explicit = str(getattr(exc, "failure_type", "") or "").strip()
    if explicit in DEPLOYMENT_FAILURE_TYPES:
        return explicit
    by_stage = {
        "audit": "audit_failure",
        "gate": "gate_failure",
        "receipt": "receipt_failure",
        "remote_recheck": "remote_recheck_failure",
        "push": "push_failure",
        "fast_forward": "fast_forward_failure",
        "workspace_alignment": "workspace_alignment_failure",
        "restart": "restart_failure",
    }
    return by_stage.get(str(stage or "").strip(), "audit_failure")


def load_deployment_diagnostic(
    path: Path,
    *,
    thread_id: str,
) -> dict[str, Any] | None:
    """Return a safe public diagnostic reconstructed from strict enums only."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict) or raw.get("schema_version") != DEPLOYMENT_DIAGNOSTIC_SCHEMA:
        return None
    try:
        expected_thread_key = _thread_key(thread_id)
    except HumanAdamDeployError:
        return None
    checkpoint_head = str(raw.get("checkpoint_head") or "").strip().lower()
    stage = str(raw.get("stage") or "").strip()
    outcome = str(raw.get("outcome") or "").strip()
    updated_at = str(raw.get("updated_at") or "").strip()
    if (
        raw.get("thread_key") != expected_thread_key
        or not re.fullmatch(r"[0-9a-f]{40}", checkpoint_head)
        or stage not in DEPLOYMENT_DIAGNOSTIC_STAGES
        or outcome not in DEPLOYMENT_DIAGNOSTIC_OUTCOMES
    ):
        return None
    try:
        normalized_time = datetime.fromisoformat(updated_at.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return None
    return {
        "checkpoint_short": checkpoint_head[:7],
        "stage": stage,
        "outcome": outcome,
        "message": DEPLOYMENT_DIAGNOSTIC_MESSAGES[(stage, outcome)],
        "updated_at": normalized_time,
    }


def _record_deployment_diagnostic(
    path: Path | None,
    *,
    checkpoint_head: str,
    thread_id: str,
    stage: str,
    outcome: str,
) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        write_deployment_diagnostic(
            path,
            checkpoint_head=checkpoint_head,
            thread_id=thread_id,
            stage=stage,
            outcome=outcome,
            updated_at=utc_now(),
        )
    except (HumanAdamDeployError, FilePersistenceError, OSError, ValueError):
        return None
    return load_deployment_diagnostic(path, thread_id=thread_id)


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


def audit_checkpoint(*, workspace: HumanAdamWorkspaceManager) -> dict[str, Any]:
    """Read-only proof of the exact checkpoint and paths offered for deployment."""
    refresh_origin_main(workspace.source_repo)
    return _public_plan(build_takeover_plan(workspace=workspace))


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
        log_path=str(log_path.relative_to(PROJECT_ROOT)) if log_path.is_relative_to(PROJECT_ROOT) else str(log_path),
    )
    if not evidence.passed:
        folded_output = output.casefold()
        failure_type = (
            "syntax_error"
            if "syntaxerror" in folded_output or re.search(r"(?:python|javascript|shell)?\s*syntax:\s*(?:failed|error)", folded_output)
            else ("test_failure" if "failed" in folded_output or "error" in folded_output else "gate_failure")
        )
        raise HumanAdamGateError(
            f"Plná brána checkpointu neprošla; nic nebylo nasazeno. Log: {evidence.log_path}",
            failure_type=failure_type,
        )
    return evidence


def deploy_checkpoint(
    *,
    workspace: HumanAdamWorkspaceManager,
    confirmation: str,
    expected_checkpoint_head: str,
    gate_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    gate_log_path: Path = DEFAULT_GATE_LOG,
    thread_id: str = "",
    deployment_receipt_path: Path | None = None,
    deployment_diagnostic_path: Path | None = None,
    deployment_failure_history_path: Path | None = None,
    profile_id: str = "human_adam",
) -> dict[str, Any]:
    if str(confirmation or "").strip() != CONFIRMATION_TEXT:
        raise HumanAdamDeployError(f"Chybí přesná potvrzovací věta: {CONFIRMATION_TEXT}")
    expected = str(expected_checkpoint_head or "").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", expected):
        raise HumanAdamDeployError("Chybí platný audit token checkpointu; spusť audit znovu.")
    if not DEPLOYMENT_LOCK.acquire(blocking=False):
        raise HumanAdamDeployError("Jiné nasazení Human–Adam už probíhá.")
    current_stage = "audit"

    def record(stage: str, outcome: str) -> dict[str, Any] | None:
        nonlocal current_stage
        current_stage = stage
        return _record_deployment_diagnostic(
            deployment_diagnostic_path,
            checkpoint_head=expected,
            thread_id=thread_id,
            stage=stage,
            outcome=outcome,
        )

    try:
        record("audit", "running")
        try:
            refresh_origin_main(workspace.source_repo)
            plan = build_takeover_plan(workspace=workspace)
            if plan.checkpoint_head != expected:
                raise HumanAdamDeployError("Checkpoint se od auditu změnil; spusť audit znovu.")
            record("audit", "passed")

            record("gate", "running")
            evidence = run_checkpoint_quality_gate(
                workspace=workspace,
                runner=gate_runner,
                log_path=gate_log_path,
            )
            refreshed = build_takeover_plan(workspace=workspace)
            if refreshed != plan or refreshed.checkpoint_head != expected:
                raise HumanAdamDeployError("Stav se během plné brány změnil; nic nebylo nasazeno.")
            record("gate", "passed")

            receipt_recorded_at = utc_now()
            if deployment_receipt_path is not None:
                record("receipt", "running")
                write_deployment_receipt(
                    deployment_receipt_path,
                    checkpoint_head=expected,
                    thread_id=thread_id,
                    state=DEPLOYMENT_PENDING,
                    recorded_at=receipt_recorded_at,
                )
                record("receipt", "passed")

            applied = apply_takeover(
                confirmation=CONFIRMATION_TEXT,
                push=True,
                workspace=workspace,
                progress_callback=record,
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
                if applied.get("applied") is not True:
                    current_stage = "fast_forward"
                elif applied.get("pushed") is not True:
                    current_stage = "push"
                else:
                    current_stage = "workspace_alignment"
                raise HumanAdamDeployError(
                    "Nasazení neposkytlo úplný důkaz fast-forwardu, pushnutí a zarovnání workspace."
                )
        except (HumanAdamDeployError, TakeoverError, AppServerError, OSError, ValueError) as exc:
            diagnostic = record(current_stage, "failed")
            _record_deployment_failure(
                deployment_failure_history_path,
                profile_id=profile_id,
                checkpoint_head=expected,
                stage=current_stage,
                failure_type=_deployment_failure_type(current_stage, exc),
            )
            safe_message = (
                diagnostic.get("message")
                if diagnostic
                else DEPLOYMENT_DIAGNOSTIC_MESSAGES[(current_stage, "failed")]
            )
            raise HumanAdamDeployError(str(safe_message)) from exc

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
                _record_deployment_failure(
                    deployment_failure_history_path,
                    profile_id=profile_id,
                    checkpoint_head=expected,
                    stage="receipt",
                    failure_type="receipt_failure",
                )
            deployment_confirmation = load_deployment_confirmation(
                deployment_receipt_path,
                thread_id=thread_id,
            )
        deployment_diagnostic = load_deployment_diagnostic(
            deployment_diagnostic_path,
            thread_id=thread_id,
        ) if deployment_diagnostic_path is not None else None
        return {
            **applied,
            "checkpoint_token": expected,
            "gate": evidence.public_dict(),
            "restart_required": True,
            "deployment_confirmation": deployment_confirmation,
            "deployment_diagnostic": deployment_diagnostic,
            "receipt_warning": receipt_warning,
        }
    finally:
        DEPLOYMENT_LOCK.release()


def record_deployment_restart(
    *,
    service: HumanAdamService,
    checkpoint_head: str,
    outcome: str,
) -> dict[str, Any] | None:
    """Persist the restart boundary without storing process details or private paths."""
    if outcome == "failed":
        _record_deployment_failure(
            getattr(service, "deployment_failure_history_path", None),
            profile_id=str(getattr(service, "work_profile_id", "human_adam") or "human_adam"),
            checkpoint_head=checkpoint_head,
            stage="restart",
            failure_type="restart_failure",
        )
    try:
        session = service.hub.snapshot()
    except (AppServerError, OSError, ValueError):
        return None
    diagnostic = _record_deployment_diagnostic(
        service.deployment_diagnostic_path,
        checkpoint_head=checkpoint_head,
        thread_id=str(session.get("thread_id") or ""),
        stage="restart",
        outcome=outcome,
    )
    return diagnostic


def _turn_busy(service: HumanAdamService) -> bool:
    return bool(service.hub.snapshot().get("turn_busy"))


def human_adam_deploy_audit_action(*, service: HumanAdamService) -> dict[str, Any]:
    profile_operation = getattr(service, "profile_operation", None)
    if callable(profile_operation):
        try:
            with profile_operation() as active_service:
                owner_id = str(getattr(active_service, "work_profile_id", "") or "")
                service.assert_deployment_allowed(owner_id)
                result = human_adam_deploy_audit_action(service=active_service)
                checker = getattr(service, "takeover_handoff_check", None)
                if result.get("ok") is True and result.get("ready") is True and callable(checker):
                    result = {
                        **result,
                        "handoff_takeover_check": checker(
                            deployment_audit=result,
                            active_service=active_service,
                        ),
                    }
                return result
        except (AppServerError, SessionHubError) as exc:
            return {"ok": False, "ready": False, "message": str(exc)}
    audit_started = False
    try:
        if _turn_busy(service):
            raise HumanAdamDeployError("Audit nelze spustit během aktivního tahu Adama.")
        audit_started = True
        return audit_checkpoint(workspace=service.workspace)
    except (HumanAdamDeployError, TakeoverError, AppServerError, OSError, ValueError) as exc:
        if audit_started:
            try:
                checkpoint_head = str(service.workspace.status().get("head") or "")
            except (AppServerError, OSError, ValueError):
                checkpoint_head = ""
            _record_deployment_failure(
                getattr(service, "deployment_failure_history_path", None),
                profile_id=str(getattr(service, "work_profile_id", "human_adam") or "human_adam"),
                checkpoint_head=checkpoint_head,
                stage="audit",
                failure_type=_deployment_failure_type("audit", exc),
            )
        return {"ok": False, "ready": False, "message": str(exc)}


def human_adam_deploy_action(
    payload: dict[str, Any],
    *,
    service: HumanAdamService,
) -> dict[str, Any]:
    profile_operation = getattr(service, "profile_operation", None)
    if callable(profile_operation):
        try:
            with profile_operation() as active_service:
                profile_id = str(getattr(active_service, "work_profile_id", "") or "")
                service.assert_deployment_allowed(profile_id)
                result = human_adam_deploy_action(payload, service=active_service)
                if result.get("ok") and result.get("applied") is True:
                    result["development_semaphore_message"] = service.finish_deployment_lease(profile_id)
                return {**result, "_work_profile_id": profile_id}
        except (AppServerError, SessionHubError) as exc:
            return {"ok": False, "ready": False, "message": str(exc)}
    thread_id = ""
    try:
        session = service.hub.snapshot()
        thread_id = str(session.get("thread_id") or "")
        if session.get("turn_busy"):
            raise HumanAdamDeployError("Nasazení nelze spustit během aktivního tahu Adama.")
        result = deploy_checkpoint(
            workspace=service.workspace,
            confirmation=str(payload.get("confirmation") or ""),
            expected_checkpoint_head=str(payload.get("checkpoint_token") or ""),
            thread_id=thread_id,
            deployment_receipt_path=service.deployment_receipt_path,
            deployment_diagnostic_path=service.deployment_diagnostic_path,
            deployment_failure_history_path=service.deployment_failure_history_path,
            profile_id=service.work_profile_id,
        )
        return {"ok": True, **result}
    except (HumanAdamDeployError, TakeoverError, AppServerError, OSError, ValueError) as exc:
        diagnostic = load_deployment_diagnostic(
            service.deployment_diagnostic_path,
            thread_id=thread_id,
        )
        return {
            "ok": False,
            "ready": False,
            "message": str(exc),
            "deployment_diagnostic": diagnostic,
        }
