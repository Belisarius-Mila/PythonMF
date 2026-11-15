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
from app.file_persistence import FilePersistenceError, atomic_write_text
from app.communication.human_adam_workspace import HumanAdamWorkspaceManager
from app.communication.validation_policy import (
    POLICY_VERSION, ValidationPlan, ValidationPolicyError, ValidationReceiptStore,
    capture_inputs, changed_paths, select_validation_plan,
    contract_plan, covers, validation_environment,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRUSTED_PYTHON = Path(sys.executable)
DEFAULT_GATE_LOG = PROJECT_ROOT / "data" / "private" / "communication" / "human_adam_deploy_gate.log"
MAX_GATE_LOG_CHARS = 2_000_000
DEFAULT_GATE_TIMEOUT_SECONDS = 1500.0
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
    mode: str = "full"
    reused: bool = False
    receipt_id: str = ""
    policy_version: str = ""

    def public_dict(self) -> dict[str, Any]:
        result = {
            "passed": self.passed,
            "returncode": self.returncode,
            "test_count": self.test_count,
            "duration_seconds": self.duration_seconds,
            "log_path": self.log_path,
            "mode": self.mode,
        }
        if self.policy_version:
            result.update(reused=self.reused, receipt_id=self.receipt_id, policy_version=self.policy_version)
        return result


def run_checkpoint_quality_gate(
    *,
    workspace: HumanAdamWorkspaceManager,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    log_path: Path = DEFAULT_GATE_LOG,
    timeout: float = DEFAULT_GATE_TIMEOUT_SECONDS,
    skip_unit_tests: bool = False,
    validation_base: str | None = None,
    full_suite: bool = False,
) -> GateEvidence:
    gate_script = workspace.project_root / "scripts" / "cockpit_quality_gate.py"
    if not TRUSTED_PYTHON.is_file() or not gate_script.is_file():
        raise HumanAdamGateError(
            "Chybí důvěryhodné Python prostředí nebo quality gate checkpointu.",
            failure_type="gate_process_error",
        )
    started = time.monotonic()
    repo = workspace.workspace_root
    plan = contract_plan('default_contracts')
    before = store = baseline = None
    try:
        base, paths = changed_paths(repo, validation_base)
        plan = select_validation_plan(paths, repo=repo, base=base)
        if plan.reason == "policy_runtime_requires_reload":
            raise HumanAdamGateError("Validační runtime potřebuje načíst novou verzi.", failure_type="gate_failure")
        if full_suite:
            plan = ValidationPlan('full', reason='explicit_full_request')
        before = capture_inputs(repo)
        store = ValidationReceiptStore(workspace.source_repo)
        # A caller's old skip flag never grants a static-only publication.
        # After push there is no new diff; an attested receipt for this exact
        # clean commit can also satisfy deployment/already-aligned validation.
        cached = None if full_suite else store.find(before, plan, allow_bound=not paths)
        compatible = store.compatible_baseline(before)
        if (not full_suite and cached is None and compatible and compatible["inputs"] == before.digest
                and (covers(compatible, plan) or not paths and before.clean and compatible.get('head') == before.head)):
            cached = compatible
        if cached:
            if capture_inputs(repo) != before:
                raise HumanAdamGateError("Vstupy se při ověření účtenky změnily.", failure_type="gate_failure")
            store.bind(before, cached)
            return GateEvidence(True, 0, cached["test_count"], round(time.monotonic() - started, 1),
                                "", cached["mode"], True, cached["inputs"], POLICY_VERSION)
        if compatible and not full_suite:
            previous_scope, current_scope = dict(compatible["scope_inputs"]), dict(before.scope)
            scope_changes = [name for name in previous_scope.keys() | current_scope.keys()
                             if previous_scope.get(name) != current_scope.get(name)]
            compatible_plan = select_validation_plan(scope_changes, repo=repo)
            coverage = set(compatible.get('covered_modules', compatible.get('modules', ()))) | set(compatible_plan.modules)
            if compatible_plan.mode == "targeted" and set(plan.modules).issubset(coverage):
                plan, baseline = compatible_plan, compatible
    except (ValidationPolicyError, FilePersistenceError, OSError, ValueError, TypeError) as exc:
        raise HumanAdamGateError("Validační vstupy nelze ověřit; místo skryté plné sady oprav příčinu.",
                                failure_type="gate_failure") from exc
    try:
        command = [str(TRUSTED_PYTHON), str(gate_script)]
        if plan.mode == "targeted":
            command.extend(["--test-modules", *plan.modules])
        completed = runner(
            command,
            cwd=str(workspace.project_root),
            env=validation_environment(),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        partial = exc.stdout or b""
        if isinstance(partial, bytes):
            partial = partial.decode("utf-8", errors="replace")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(log_path, partial[-MAX_GATE_LOG_CHARS:] + "\n")
        raise HumanAdamGateError(
            "Kontrolní brána checkpointu se nedokončila; nic nebylo nasazeno.",
            failure_type="gate_timeout",
        ) from exc
    except OSError as exc:
        raise HumanAdamGateError(
            "Kontrolní brána checkpointu se nedokončila; nic nebylo nasazeno.",
            failure_type="gate_process_error",
        ) from exc
    duration = round(time.monotonic() - started, 1)
    output = (f"Validation policy: {POLICY_VERSION}; mode: {plan.mode}; reason: {plan.reason}; "
              f"domains: {','.join(plan.domains)}\n"
              f"{completed.stdout or ''}\n{completed.stderr or ''}").strip()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(log_path, output[-MAX_GATE_LOG_CHARS:] + "\n")
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
        mode=plan.mode,
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
            f"Kontrolní brána checkpointu neprošla; nic nebylo nasazeno. Log: {evidence.log_path}",
            failure_type=failure_type,
        )
    if evidence.test_count < 1:
        raise HumanAdamGateError("Brána nedoložila provedení testů.", failure_type="gate_failure")
    if before is not None and store is not None:
        try:
            after = capture_inputs(repo)
        except (ValidationPolicyError, OSError) as exc:
            raise HumanAdamGateError("Vstupy po validační bráně nelze bezpečně ověřit.", failure_type="gate_failure") from exc
        if after != before:
            raise HumanAdamGateError("Vstupy se během validační brány změnily.", failure_type="gate_failure")
        try:
            body = store.record(after, plan, test_count=evidence.test_count,
                                duration_seconds=evidence.duration_seconds, baseline=baseline)
            return GateEvidence(evidence.passed, evidence.returncode, evidence.test_count,
                                evidence.duration_seconds, evidence.log_path, evidence.mode,
                                False, body["inputs"], POLICY_VERSION)
        except (ValidationPolicyError, FilePersistenceError, OSError) as exc:
            if plan.mode != "full":
                raise HumanAdamGateError("Cílená brána nemá ověřitelnou účtenku.", failure_type="gate_failure") from exc
            # A real successful full run remains valid without an accelerator.
    return evidence
