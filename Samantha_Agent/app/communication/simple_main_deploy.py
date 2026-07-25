"""Private two-step deployment backend for one clean synchronized ``main``.

Phase 2.1 intentionally has no Cockpit route or UI.  The backend proves the
exact source and profile state, runs the canonical quality gate, records a
private pending restart receipt, and can later verify the restarted process and
the canonical smoke check.  It never creates a branch, performs a takeover, or
consults the legacy development semaphore.
"""

from __future__ import annotations

import json
import re
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Sequence

from app.codex_appserver import AppServerError, utc_now
from app.cockpit_code_stamp import cockpit_code_stamp, default_cockpit_code_stamp_paths
from app.communication.checkpoint_quality_gate import (
    DEFAULT_GATE_LOG,
    HumanAdamGateError,
    run_checkpoint_quality_gate,
)
from app.communication.human_adam_workspace import HumanAdamWorkspaceManager
from app.file_persistence import FilePersistenceError, atomic_write_json
from scripts.cockpit_smoke_check import DEFAULT_CHECKS, SmokeResult, run_smoke_check
from scripts.human_adam_takeover import TakeoverError, refresh_origin_main


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SIMPLE_MAIN_DEPLOYMENT_RECEIPT = (
    PROJECT_ROOT / "data" / "private" / "communication" / "simple_main_deployment.json"
)
SIMPLE_MAIN_DEPLOYMENT_SCHEMA = 1
PENDING_RESTART = "pending_restart"
DEPLOYED = "deployed"
RECENT_DEPLOYMENT_MAX_AGE_SECONDS = 15 * 60
SIMPLE_MAIN_DEPLOYMENT_CONFIRMATION = "POTVRZUJI NASAZENI CISTEHO MAIN"
_HEAD_RE = re.compile(r"[0-9a-f]{40}")
_CODE_STAMP_RE = re.compile(r"[0-9a-f]{16}")
_WORKSTREAM_ID_RE = re.compile(r"[a-z][a-z0-9_-]{1,63}")
_DEPLOYMENT_LOCK = threading.Lock()


class SimpleMainDeploymentError(AppServerError):
    """Raised when a clean-main deployment proof is incomplete."""


@dataclass(frozen=True)
class SimpleMainDeploymentRequest:
    workstream_id: str
    expected_head: str
    previous_pid: int


def _safe_request(request: SimpleMainDeploymentRequest) -> SimpleMainDeploymentRequest:
    workstream_id = str(request.workstream_id or "").strip().casefold()
    expected_head = str(request.expected_head or "").strip().casefold()
    try:
        previous_pid = int(request.previous_pid)
    except (TypeError, ValueError) as exc:
        raise SimpleMainDeploymentError("Nasazení nemá platný PID běžícího Cockpitu.") from exc
    if not _WORKSTREAM_ID_RE.fullmatch(workstream_id):
        raise SimpleMainDeploymentError("Nasazení nemá platný pracovní proud.")
    if not _HEAD_RE.fullmatch(expected_head):
        raise SimpleMainDeploymentError("Nasazení nemá platný očekávaný commit main.")
    if previous_pid <= 0:
        raise SimpleMainDeploymentError("Nasazení nemá platný PID běžícího Cockpitu.")
    return SimpleMainDeploymentRequest(
        workstream_id=workstream_id,
        expected_head=expected_head,
        previous_pid=previous_pid,
    )


def _safe_timestamp(value: object, *, label: str) -> str:
    text = str(value or "").strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SimpleMainDeploymentError(f"{label} nasazení nemá platný čas.") from exc
    if parsed.tzinfo is None:
        raise SimpleMainDeploymentError(f"{label} nasazení nemá časovou zónu.")
    return parsed.isoformat()


def _source_and_profile_preflight(
    *,
    workspace: HumanAdamWorkspaceManager,
    peer_workspaces: Sequence[HumanAdamWorkspaceManager],
    expected_head: str,
    allow_clean_peer_source_ahead: bool = False,
    synchronize_clean_peers: bool = False,
) -> list[dict[str, Any]]:
    primary = workspace.status()
    if primary.get("source_branch") != "main":
        raise SimpleMainDeploymentError("Jednoduché nasazení vyžaduje zdrojovou větev main.")
    if int(primary.get("source_pending_changes") or 0) != 0:
        raise SimpleMainDeploymentError("Zdrojový main není čistý; nasazení bylo zastaveno.")
    if str(primary.get("source_head") or "").casefold() != expected_head:
        raise SimpleMainDeploymentError("Zdrojový main se liší od očekávaného commitu.")
    try:
        origin_head = refresh_origin_main(workspace.source_repo).casefold()
    except TakeoverError as exc:
        raise SimpleMainDeploymentError("Nelze ověřit aktuální origin/main.") from exc
    refreshed = workspace.status()
    if (
        int(refreshed.get("source_pending_changes") or 0) != 0
        or str(refreshed.get("source_head") or "").casefold() != expected_head
        or origin_head != expected_head
    ):
        raise SimpleMainDeploymentError(
            "Lokální main a origin/main nejsou čisté a shodné na očekávaném commitu."
        )

    unique: list[HumanAdamWorkspaceManager] = []
    seen: set[Path] = set()
    for candidate in (workspace, *peer_workspaces):
        key = candidate.workspace_root.resolve()
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    rows: list[dict[str, Any]] = []
    for index, candidate in enumerate(unique):
        status = candidate.status()
        clean_peer_source_ahead = bool(
            index > 0
            and status.get("ok") is True
            and status.get("prepared") is True
            and status.get("project_ready") is True
            and status.get("branch") == "main"
            and status.get("source_branch") == "main"
            and status.get("workspace_relation") == "source_ahead"
            and not bool(status.get("dirty"))
            and not bool(status.get("remotes"))
            and not bool(status.get("local_checkpoint_ahead"))
            and not bool(status.get("local_checkpoint_preserved"))
            and int(status.get("local_commit_count") or 0) == 0
            and int(status.get("source_pending_changes") or 0) == 0
            and str(status.get("source_head") or "").casefold() == expected_head
        )
        if clean_peer_source_ahead and synchronize_clean_peers:
            status = candidate.sync_from_main(confirmed=True)
        elif clean_peer_source_ahead and allow_clean_peer_source_ahead:
            rows.append(
                {
                    "workspace": f"peer-{index}",
                    "aligned": False,
                    "clean_source_ahead": True,
                    "head": str(status.get("head") or "").casefold(),
                    "target_head": expected_head,
                }
            )
            continue
        if (
            status.get("ok") is not True
            or status.get("prepared") is not True
            or status.get("project_ready") is not True
            or status.get("branch") != "main"
            or status.get("source_branch") != "main"
            or status.get("workspace_relation") != "aligned"
            or bool(status.get("dirty"))
            or bool(status.get("remotes"))
            or bool(status.get("local_checkpoint_ahead"))
            or bool(status.get("local_checkpoint_preserved"))
            or int(status.get("local_commit_count") or 0) != 0
            or int(status.get("source_pending_changes") or 0) != 0
            or str(status.get("head") or "").casefold() != expected_head
            or str(status.get("source_head") or "").casefold() != expected_head
        ):
            raise SimpleMainDeploymentError(
                "Všechny profilové workspaces musí být čisté a zarovnané s přesným main."
            )
        rows.append(
            {
                "workspace": "primary" if index == 0 else f"peer-{index}",
                "aligned": True,
                "head": expected_head,
            }
        )
    return rows


def _expected_code_stamp(workspace: HumanAdamWorkspaceManager) -> str:
    source_project_root = workspace.source_repo / workspace.project_dir_name
    value = cockpit_code_stamp(default_cockpit_code_stamp_paths(source_project_root))
    if not _CODE_STAMP_RE.fullmatch(value):
        raise SimpleMainDeploymentError("Nelze odvodit očekávaný otisk Cockpitu.")
    return value


def _pending_receipt(
    *,
    request: SimpleMainDeploymentRequest,
    expected_code_stamp: str,
    test_count: int,
    gate_duration_seconds: float,
    prepared_at: str,
) -> dict[str, Any]:
    if test_count <= 0:
        raise SimpleMainDeploymentError("Plná brána neposkytla počet testů.")
    if not _CODE_STAMP_RE.fullmatch(expected_code_stamp):
        raise SimpleMainDeploymentError("Nasazení nemá platný očekávaný otisk Cockpitu.")
    return {
        "schema_version": SIMPLE_MAIN_DEPLOYMENT_SCHEMA,
        "state": PENDING_RESTART,
        "workstream_id": request.workstream_id,
        "main_head": request.expected_head,
        "expected_code_stamp": expected_code_stamp,
        "previous_pid": request.previous_pid,
        "test_count": int(test_count),
        "gate_duration_seconds": float(gate_duration_seconds),
        "prepared_at": _safe_timestamp(prepared_at, label="Příprava"),
    }


def _write_receipt(path: Path, payload: dict[str, Any]) -> None:
    try:
        atomic_write_json(Path(path), payload, ensure_ascii=False, indent=2)
    except (FilePersistenceError, OSError) as exc:
        raise SimpleMainDeploymentError("Soukromou účtenku nasazení nelze uložit.") from exc


def load_simple_main_deployment_receipt(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SimpleMainDeploymentError("Soukromou účtenku nasazení nelze načíst.") from exc
    if not isinstance(raw, dict) or raw.get("schema_version") != SIMPLE_MAIN_DEPLOYMENT_SCHEMA:
        raise SimpleMainDeploymentError("Soukromá účtenka nasazení má neznámé schéma.")
    state = str(raw.get("state") or "")
    required = {
        "schema_version",
        "state",
        "workstream_id",
        "main_head",
        "expected_code_stamp",
        "previous_pid",
        "test_count",
        "gate_duration_seconds",
        "prepared_at",
    }
    if state == DEPLOYED:
        required |= {"observed_pid", "smoke_count", "deployed_at"}
    if state not in {PENDING_RESTART, DEPLOYED} or set(raw) != required:
        raise SimpleMainDeploymentError("Soukromá účtenka nasazení je neplatná.")
    try:
        request = _safe_request(
            SimpleMainDeploymentRequest(
                workstream_id=raw.get("workstream_id", ""),
                expected_head=raw.get("main_head", ""),
                previous_pid=raw.get("previous_pid", 0),
            )
        )
        test_count = int(raw.get("test_count") or 0)
        gate_duration_seconds = float(raw.get("gate_duration_seconds") or 0.0)
    except (TypeError, ValueError) as exc:
        raise SimpleMainDeploymentError("Soukromá účtenka nasazení má neplatné číselné údaje.") from exc
    if gate_duration_seconds < 0:
        raise SimpleMainDeploymentError("Soukromá účtenka nasazení má neplatnou dobu brány.")
    expected_code_stamp = str(raw.get("expected_code_stamp") or "").strip().casefold()
    if not _CODE_STAMP_RE.fullmatch(expected_code_stamp):
        raise SimpleMainDeploymentError("Soukromá účtenka má neplatný kódový otisk.")
    normalized = _pending_receipt(
        request=request,
        expected_code_stamp=expected_code_stamp,
        test_count=test_count,
        gate_duration_seconds=gate_duration_seconds,
        prepared_at=str(raw.get("prepared_at") or ""),
    )
    if state == DEPLOYED:
        observed_pid = int(raw.get("observed_pid") or 0)
        smoke_count = int(raw.get("smoke_count") or 0)
        if observed_pid <= 0 or observed_pid == request.previous_pid or smoke_count != len(DEFAULT_CHECKS):
            raise SimpleMainDeploymentError("Dokončená účtenka nasazení nemá úplné důkazy.")
        normalized.update(
            {
                "state": DEPLOYED,
                "observed_pid": observed_pid,
                "smoke_count": smoke_count,
                "deployed_at": _safe_timestamp(raw.get("deployed_at"), label="Dokončení"),
            }
        )
    return normalized


def load_completed_simple_main_deployment(
    path: Path,
    *,
    expected_workstream_id: str,
) -> dict[str, Any] | None:
    """Return a persistent safe summary for one expected canonical workstream."""

    clean_expected = str(expected_workstream_id or "").strip().casefold()
    if not _WORKSTREAM_ID_RE.fullmatch(clean_expected):
        return None
    try:
        receipt = load_simple_main_deployment_receipt(path)
    except SimpleMainDeploymentError:
        return None
    if receipt.get("state") != DEPLOYED or receipt.get("workstream_id") != clean_expected:
        return None
    return {
        "state": DEPLOYED,
        "workstream_id": str(receipt["workstream_id"]),
        "main_short": str(receipt["main_head"])[:12],
        "deployed_at": str(receipt["deployed_at"]),
        "gate": {
            "passed": True,
            "test_count": int(receipt["test_count"]),
            "duration_seconds": float(receipt["gate_duration_seconds"]),
        },
        "smoke": {
            "passed": True,
            "check_count": int(receipt["smoke_count"]),
        },
    }


def load_recent_simple_main_deployment(
    path: Path,
    *,
    expected_workstream_id: str,
    now_factory: Callable[[], str] = utc_now,
    max_age_seconds: int = RECENT_DEPLOYMENT_MAX_AGE_SECONDS,
) -> dict[str, Any] | None:
    """Return a short safe summary of one recently verified deployment."""

    summary = load_completed_simple_main_deployment(
        path,
        expected_workstream_id=expected_workstream_id,
    )
    if summary is None:
        return None
    try:
        now = datetime.fromisoformat(_safe_timestamp(now_factory(), label="Kontrola"))
        deployed_at = datetime.fromisoformat(str(summary["deployed_at"]))
        age_seconds = (now - deployed_at).total_seconds()
    except (KeyError, TypeError, ValueError, SimpleMainDeploymentError):
        return None
    if max_age_seconds <= 0 or age_seconds < 0 or age_seconds > max_age_seconds:
        return None
    return summary


def audit_simple_main_deployment(
    *,
    workspace: HumanAdamWorkspaceManager,
    workstream_id: str,
    peer_workspaces: Sequence[HumanAdamWorkspaceManager] = (),
    code_stamp_factory: Callable[[HumanAdamWorkspaceManager], str] = _expected_code_stamp,
) -> dict[str, Any]:
    """Read and refresh the exact clean-main evidence required before deployment."""

    initial = workspace.status()
    expected_head = str(initial.get("source_head") or "").strip().casefold()
    safe_request = _safe_request(
        SimpleMainDeploymentRequest(
            workstream_id=workstream_id,
            expected_head=expected_head,
            previous_pid=1,
        )
    )
    rows = _source_and_profile_preflight(
        workspace=workspace,
        peer_workspaces=peer_workspaces,
        expected_head=safe_request.expected_head,
        allow_clean_peer_source_ahead=True,
    )
    expected_code_stamp = str(code_stamp_factory(workspace) or "").strip().casefold()
    if not _CODE_STAMP_RE.fullmatch(expected_code_stamp):
        raise SimpleMainDeploymentError("Nelze odvodit očekávaný otisk Cockpitu.")
    return {
        "ok": True,
        "ready": True,
        "operation": "simple_main_deployment_audit",
        "state": "ready",
        "workstream_id": safe_request.workstream_id,
        "main_head": safe_request.expected_head,
        "main_short": safe_request.expected_head[:12],
        "expected_code_stamp": expected_code_stamp,
        "confirmation_text": SIMPLE_MAIN_DEPLOYMENT_CONFIRMATION,
        "workspaces": rows,
        "changes": [],
        "change_count": 0,
        "branches_created": False,
        "wip_used": False,
        "semaphore_used": False,
    }


def prepare_simple_main_deployment(
    *,
    workspace: HumanAdamWorkspaceManager,
    request: SimpleMainDeploymentRequest,
    confirmed: bool,
    peer_workspaces: Sequence[HumanAdamWorkspaceManager] = (),
    gate_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    gate_log_path: Path = DEFAULT_GATE_LOG,
    receipt_path: Path = DEFAULT_SIMPLE_MAIN_DEPLOYMENT_RECEIPT,
    now_factory: Callable[[], str] = utc_now,
    code_stamp_factory: Callable[[HumanAdamWorkspaceManager], str] = _expected_code_stamp,
) -> dict[str, Any]:
    """Prove an exact clean main and prepare one restart-bound deployment."""
    if not confirmed:
        raise SimpleMainDeploymentError("Jednoduché nasazení vyžaduje výslovné potvrzení.")
    safe_request = _safe_request(request)
    if not _DEPLOYMENT_LOCK.acquire(blocking=False):
        raise SimpleMainDeploymentError("Jiné jednoduché nasazení právě probíhá.")
    try:
        initial_rows = _source_and_profile_preflight(
            workspace=workspace,
            peer_workspaces=peer_workspaces,
            expected_head=safe_request.expected_head,
            synchronize_clean_peers=True,
        )
        initial_stamp = str(code_stamp_factory(workspace) or "").strip().casefold()
        if not _CODE_STAMP_RE.fullmatch(initial_stamp):
            raise SimpleMainDeploymentError("Nelze odvodit očekávaný otisk Cockpitu.")
        try:
            evidence = run_checkpoint_quality_gate(
                workspace=workspace,
                runner=gate_runner,
                log_path=gate_log_path,
            )
        except HumanAdamGateError as exc:
            raise SimpleMainDeploymentError(str(exc)) from exc
        final_rows = _source_and_profile_preflight(
            workspace=workspace,
            peer_workspaces=peer_workspaces,
            expected_head=safe_request.expected_head,
        )
        final_stamp = str(code_stamp_factory(workspace) or "").strip().casefold()
        if final_stamp != initial_stamp:
            raise SimpleMainDeploymentError(
                "Kódový otisk se během plné brány změnil; nasazení bylo zastaveno."
            )
        receipt = _pending_receipt(
            request=safe_request,
            expected_code_stamp=final_stamp,
            test_count=evidence.test_count,
            gate_duration_seconds=evidence.duration_seconds,
            prepared_at=now_factory(),
        )
        _write_receipt(receipt_path, receipt)
        return {
            "ok": True,
            "operation": "simple_main_deployment",
            "state": PENDING_RESTART,
            "workstream_id": safe_request.workstream_id,
            "main_head": safe_request.expected_head,
            "main_short": safe_request.expected_head[:12],
            "expected_code_stamp": final_stamp,
            "gate": {
                "passed": True,
                "test_count": evidence.test_count,
                "duration_seconds": evidence.duration_seconds,
            },
            "workspaces": final_rows or initial_rows,
            "restart_required": True,
            "branches_created": False,
            "wip_used": False,
            "semaphore_used": False,
        }
    finally:
        _DEPLOYMENT_LOCK.release()


def _default_smoke_runner() -> Sequence[SmokeResult]:
    return run_smoke_check("http://127.0.0.1:8770", 3.0)


def _verified_deployment_result(
    *,
    receipt: dict[str, Any],
    code_stamp: str,
    workspaces: Sequence[dict[str, Any]],
    verification_reused: bool = False,
) -> dict[str, Any]:
    result = {
        "ok": True,
        "operation": "simple_main_deployment",
        "state": DEPLOYED,
        "workstream_id": receipt["workstream_id"],
        "main_head": receipt["main_head"],
        "main_short": str(receipt["main_head"])[:12],
        "code_stamp": code_stamp,
        "deployed_at": str(receipt["deployed_at"]),
        "gate": {
            "passed": True,
            "test_count": int(receipt["test_count"]),
            "duration_seconds": float(receipt["gate_duration_seconds"]),
        },
        "new_process_confirmed": True,
        "smoke": {
            "passed": True,
            "check_count": int(receipt["smoke_count"]),
        },
        "workspaces": list(workspaces),
        "branches_created": False,
        "wip_used": False,
        "semaphore_used": False,
    }
    if verification_reused:
        result["verification_reused"] = True
    return result


def verify_simple_main_deployment(
    *,
    workspace: HumanAdamWorkspaceManager,
    observed_pid: int,
    observed_code_stamp: str,
    peer_workspaces: Sequence[HumanAdamWorkspaceManager] = (),
    receipt_path: Path = DEFAULT_SIMPLE_MAIN_DEPLOYMENT_RECEIPT,
    smoke_runner: Callable[[], Sequence[SmokeResult]] = _default_smoke_runner,
    now_factory: Callable[[], str] = utc_now,
) -> dict[str, Any]:
    """Verify the restarted Cockpit and promote only complete evidence."""
    if not _DEPLOYMENT_LOCK.acquire(blocking=False):
        raise SimpleMainDeploymentError("Jiné jednoduché nasazení právě probíhá.")
    try:
        receipt = load_simple_main_deployment_receipt(receipt_path)
        try:
            new_pid = int(observed_pid)
        except (TypeError, ValueError) as exc:
            raise SimpleMainDeploymentError("Restart neposkytl platný PID Cockpitu.") from exc
        clean_stamp = str(observed_code_stamp or "").strip().casefold()
        if clean_stamp != receipt["expected_code_stamp"]:
            raise SimpleMainDeploymentError("Běžící Cockpit nemá očekávaný kódový otisk.")
        if receipt.get("state") == DEPLOYED:
            if new_pid <= 0 or new_pid != int(receipt["observed_pid"]):
                raise SimpleMainDeploymentError(
                    "Dokončené nasazení nepatří běžícímu procesu Cockpitu."
                )
            rows = _source_and_profile_preflight(
                workspace=workspace,
                peer_workspaces=peer_workspaces,
                expected_head=str(receipt["main_head"]),
            )
            return _verified_deployment_result(
                receipt=receipt,
                code_stamp=clean_stamp,
                workspaces=rows,
                verification_reused=True,
            )
        if receipt.get("state") != PENDING_RESTART:
            raise SimpleMainDeploymentError("Nasazení nečeká na ověření restartu.")
        if new_pid <= 0 or new_pid == int(receipt["previous_pid"]):
            raise SimpleMainDeploymentError("Nebyl doložen nový proces Cockpitu po restartu.")
        rows = _source_and_profile_preflight(
            workspace=workspace,
            peer_workspaces=peer_workspaces,
            expected_head=str(receipt["main_head"]),
        )
        smoke = list(smoke_runner())
        expected_pairs = list(DEFAULT_CHECKS)
        actual_pairs = [(item.name, item.path) for item in smoke]
        if len(smoke) != len(expected_pairs) or actual_pairs != expected_pairs or not all(item.ok for item in smoke):
            raise SimpleMainDeploymentError("Povinný Cockpit smoke test po restartu neprošel 5/5.")
        deployed_at = _safe_timestamp(now_factory(), label="Dokončení")
        completed = {
            **receipt,
            "state": DEPLOYED,
            "observed_pid": new_pid,
            "smoke_count": len(smoke),
            "deployed_at": deployed_at,
        }
        _write_receipt(receipt_path, completed)
        return _verified_deployment_result(
            receipt=completed,
            code_stamp=clean_stamp,
            workspaces=rows,
        )
    finally:
        _DEPLOYMENT_LOCK.release()
