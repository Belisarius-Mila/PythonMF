"""Fail-closed work-profile routing for the Human–Adam interface."""

from __future__ import annotations

import atexit
import json
import os
import re
import subprocess
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator

from app.codex_appserver import AppServerError
from app.communication.development_semaphore import (
    TERMINAL_OWNER_ID,
    DevelopmentSemaphore,
)
from app.communication.human_adam_deploy import (
    DEPLOYMENT_LOCK,
    DEFAULT_DEPLOYMENT_DIAGNOSTIC,
    DEFAULT_DEPLOYMENT_FAILURE_HISTORY,
    DEFAULT_DEPLOYMENT_RECEIPT,
)
from app.communication.human_adam_service import (
    DEVELOPMENT_CONTROL_DEVELOPER_INSTRUCTIONS,
    HUMAN_ADAM_DEVELOPER_INSTRUCTIONS,
    HumanAdamService,
)
from app.communication.human_adam_workspace import (
    HUMAN_ADAM_WORKSPACE_DEVELOPER_INSTRUCTIONS,
    HumanAdamWorkspaceManager,
)
from app.communication.human_adam_workstream_backends import (
    COMPATIBILITY_ADAPTER_BACKEND,
    CompatibilityWorkstreamAdapter,
    WorkstreamBackendRegistry,
)
from app.communication.human_adam_workstream_catalog import CanonicalWorkstream
from app.communication.human_adam_workstream_coordinator import (
    CanonicalWorkstreamBinding,
    HumanAdamWorkstreamCoordinator,
    canonical_workstream_binding,
)
from app.communication.human_adam_workstream_memory import WorkstreamMemoryRegistry
from app.communication.human_adam_workstream_selection import GroupedWorkstreamSelection
from app.communication.human_adam_workstream_threads import WorkstreamThreadRegistry
from app.communication.human_adam_turn_completion import (
    ParsedTurnCompletion,
    TurnCompletionMetadata,
    automatic_completion_instruction,
    parse_turn_completion,
)
from app.communication.local_runtime import LocalAppServerProcessController
from app.communication.session_hub import (
    CanonicalSessionHub,
    SessionBusyError,
    SessionHubError,
)
from app.communication.simple_main_checkpoint import (
    SimpleMainCheckpointRequest,
    complete_simple_main_checkpoint,
)
from app.communication.simple_main_deploy import (
    DEFAULT_SIMPLE_MAIN_DEPLOYMENT_RECEIPT,
    SimpleMainDeploymentRequest,
    audit_simple_main_deployment as audit_clean_main_deployment,
    load_recent_simple_main_deployment,
    load_simple_main_deployment_receipt,
    prepare_simple_main_deployment as prepare_clean_main_deployment,
    verify_simple_main_deployment as verify_clean_main_deployment,
)
from app.file_persistence import (
    atomic_replace_text_under_external_lock,
    atomic_write_json,
    exclusive_file_lock,
)
from app.project_continuity import ProjectContinuityError, ProjectContinuityService
from scripts.cockpit_smoke_check import run_smoke_check


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRIVATE_COMMUNICATION_ROOT = PROJECT_ROOT / "data" / "private" / "communication"
PRIVATE_PROFILE_ROOT = PROJECT_ROOT / "data" / "private" / "human_adam_profiles"
PRIVATE_WORKSTREAM_THREAD_ROOT = PRIVATE_COMMUNICATION_ROOT / "workstreams"
DEFAULT_PROFILE_STATE_PATH = PRIVATE_COMMUNICATION_ROOT / "human_adam_active_profile.json"
DEFAULT_DEVELOPMENT_SEMAPHORE_PATH = PRIVATE_COMMUNICATION_ROOT / "development_semaphore.json"
DEFAULT_DEPLOYMENT_COMPLETION_PATH = PRIVATE_COMMUNICATION_ROOT / "deployment_completion.json"
DEFAULT_HUMAN_SESSION_PATH = PRIVATE_COMMUNICATION_ROOT / "canonical_session.json"
DEFAULT_HUMAN_CONTEXT_ANCHOR_PATH = PRIVATE_COMMUNICATION_ROOT / "human_adam_context_anchor.json"
KNIHOVNA_PROFILE_ROOT = PRIVATE_PROFILE_ROOT / "knihovna"
KNIHOVNA_CONTEXT_ANCHOR_PATH = PRIVATE_COMMUNICATION_ROOT / "knihovna_context_anchor.json"
KNIHOVNA_TVBCP_RELATIVE_PATH = Path("memory/tvbcp/knihovna_cockpit.txt")
PROFILE_ID_RE = re.compile(r"[a-z][a-z0-9_-]{1,31}")
PROFILE_STATE_SCHEMA = 1
DEPLOYMENT_COMPLETION_SCHEMA = 1
DEPLOYMENT_COMPLETION_CONFIRMATION = "POTVRZUJI DOKONCENI HANDOFFU PO NASAZENI"
WRITABLE_LAZY_WORKSTREAM_IDS = frozenset({"project-mmtx"})

KNIHOVNA_DEVELOPER_INSTRUCTIONS = (
    HUMAN_ADAM_WORKSPACE_DEVELOPER_INSTRUCTIONS
    + DEVELOPMENT_CONTROL_DEVELOPER_INSTRUCTIONS
    + (
        " Aktivni pracovni profil je Knihovna v Samantha Cockpitu. Pred vetsi praci precti "
        "Samantha_Agent/memory/projects/vedecke_clanky.md, "
        "Samantha_Agent/memory/handoffs/knowledge_library_article_editing_2026_07_16.md a "
        "Samantha_Agent/memory/tvbcp/knihovna_cockpit.txt. Tento TVBCP aktualizuj vyhradne "
        "na Miluv vyslovny pokyn; nikdy do nej nezapisuj samostatne ani pri milniku. Pri "
        "vyslovne vyzadanem zapisu zachyt rozhodnuti, dukazy, rizika a dalsi krok, nikdy "
        "plny chat ani citlive texty. Kazdy novy chronologicky zaznam pridej na konec "
        "souboru a oznac ho lokalnim datem, casem a casovou zonou ve formatu "
        "YYYY-MM-DD HH:MM TZ. Soukrome texty clanku, prilohy a metadata konkretnich osob "
        "nikdy nevypisuj do Gitu, TVBCP ani odpovedi bez Milova vyslovneho pokynu. Private "
        "data nejsou soucasti izolovane kopie; z jejich absence nevyvozuj, ze v hlavnim "
        "projektu neexistuji. V bezne odpovedi uvadej jen samotny nazev souboru, pripadne "
        "nejkratsi nutnou relativni cestu pri shodnych nazvech."
    )
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _git_text(repo: Path, args: list[str], *, timeout: float = 30.0) -> str:
    try:
        completed = subprocess.run(
            ["/usr/bin/git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise AppServerError("Git důkaz dokončení nasazení nelze bezpečně ověřit.") from exc
    if completed.returncode != 0:
        raise AppServerError("Git důkaz dokončení nasazení nelze bezpečně ověřit.")
    return completed.stdout.strip()


class HumanAdamProfileManager:
    """Route one visible UI through unified canonical workstream backends."""

    def __init__(
        self,
        *,
        profiles: dict[str, dict[str, Any]],
        default_profile_id: str,
        state_path: Path = DEFAULT_PROFILE_STATE_PATH,
        runtime: LocalAppServerProcessController | None = None,
        development_semaphore: DevelopmentSemaphore | None = None,
        project_continuity: ProjectContinuityService | None = None,
        deployment_completion_path: Path | None = None,
        simple_main_deployment_receipt_path: Path | None = None,
        workstream_threads: WorkstreamThreadRegistry | None = None,
        workstream_memory: WorkstreamMemoryRegistry | None = None,
    ):
        if not profiles or default_profile_id not in profiles:
            raise ValueError("Pracovní profily Human–Adam nemají platný výchozí profil.")
        normalized_profiles: dict[str, dict[str, Any]] = {}
        for profile_id, profile in profiles.items():
            if not PROFILE_ID_RE.fullmatch(profile_id):
                raise ValueError("Pracovní profil Human–Adam má neplatný identifikátor.")
            if not isinstance(profile.get("service"), HumanAdamService):
                raise ValueError("Pracovní profil Human–Adam nemá platnou službu.")
            if profile["service"].work_profile_id != profile_id:
                raise ValueError("Profil a jeho služba nemají shodný bezpečný identifikátor.")
            normalized = dict(profile)
            normalized["workstream_binding"] = canonical_workstream_binding(
                profile_id=profile_id,
                profile=profile,
            )
            normalized_profiles[profile_id] = normalized
        self.profiles = normalized_profiles
        self.workstream_coordinator = HumanAdamWorkstreamCoordinator(self.profiles)
        compatibility_adapters = tuple(
            CompatibilityWorkstreamAdapter(
                workstream_id=binding.workstream_id,
                profile_id=profile_id,
                service=profile["service"],
            )
            for profile_id, profile in self.profiles.items()
            if isinstance(
                (binding := profile.get("workstream_binding")),
                CanonicalWorkstreamBinding,
            )
        )
        self.workstream_backends = WorkstreamBackendRegistry(
            compatibility_adapters=compatibility_adapters,
        )
        self.grouped_workstream_selection = GroupedWorkstreamSelection(
            backend_registry=self.workstream_backends,
        )
        self.workstream_memory = workstream_memory
        if self.workstream_memory is not None:
            for profile in self.profiles.values():
                binding = profile.get("workstream_binding")
                if not isinstance(binding, CanonicalWorkstreamBinding):
                    continue
                memory_binding = self.workstream_memory.binding(binding.workstream_id)
                if (
                    binding.handoff_relative_path != memory_binding.handoff_relative_path
                    or binding.tvbcp_relative_path != memory_binding.tvbcp_relative_path
                ):
                    raise ValueError("Profil neodpovídá kanonické paměti pracovního proudu.")
        self.default_profile_id = default_profile_id
        self.state_path = Path(state_path)
        self.runtime = runtime or self.profiles[default_profile_id]["service"].runtime
        semaphore_path = (
            DEFAULT_DEVELOPMENT_SEMAPHORE_PATH
            if self.state_path == DEFAULT_PROFILE_STATE_PATH
            else self.state_path.with_name("development_semaphore.json")
        )
        self.development_semaphore = development_semaphore or DevelopmentSemaphore(semaphore_path)
        continuity_root = PROJECT_ROOT if self.state_path == DEFAULT_PROFILE_STATE_PATH else self.state_path.parent
        self.project_continuity = project_continuity or ProjectContinuityService(project_root=continuity_root)
        self.deployment_completion_path = Path(
            deployment_completion_path
            or (
                DEFAULT_DEPLOYMENT_COMPLETION_PATH
                if self.state_path == DEFAULT_PROFILE_STATE_PATH
                else self.state_path.with_name("deployment_completion.json")
            )
        )
        self.simple_main_deployment_receipt_path = Path(
            simple_main_deployment_receipt_path
            or (
                DEFAULT_SIMPLE_MAIN_DEPLOYMENT_RECEIPT
                if self.state_path == DEFAULT_PROFILE_STATE_PATH
                else self.state_path.with_name("simple_main_deployment.json")
            )
        )
        self.workstream_threads = workstream_threads
        self._lazy_services: dict[str, HumanAdamService] = {}
        self._state_lock = threading.RLock()
        self._operation_lock = threading.Lock()
        self._state_error = ""
        self._active_profile_id = self._load_active_profile_id()

    def _load_active_profile_id(self) -> str:
        if not self.state_path.exists():
            return self.default_profile_id
        try:
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._state_error = "Stav pracovního profilu nelze bezpečně načíst."
            return ""
        if not isinstance(raw, dict) or raw.get("schema_version") != PROFILE_STATE_SCHEMA:
            self._state_error = "Stav pracovního profilu má neznámé schéma."
            return ""
        profile_id = str(raw.get("active_profile_id") or "").strip()
        if profile_id not in self.profiles:
            self._state_error = "Stav odkazuje na neznámý pracovní profil."
            return ""
        return profile_id

    def _write_active_profile_id(self, profile_id: str) -> None:
        atomic_write_json(
            self.state_path,
            {
                "schema_version": PROFILE_STATE_SCHEMA,
                "active_profile_id": profile_id,
                "updated_at": _now(),
            },
            ensure_ascii=False,
            indent=2,
        )

    @property
    def active_profile_id(self) -> str:
        with self._state_lock:
            if self._state_error or self._active_profile_id not in self.profiles:
                raise AppServerError(self._state_error or "Aktivní pracovní profil není známý.")
            return self._active_profile_id

    @property
    def active_lazy_workstream_id(self) -> str:
        if self.workstream_threads is None:
            return ""
        return self.workstream_threads.active_workstream_id

    def _lazy_service(self, workstream_id: str) -> HumanAdamService:
        clean_id = str(workstream_id or "").strip()
        with self._state_lock:
            existing = self._lazy_services.get(clean_id)
        if existing is not None:
            return existing
        if self.workstream_threads is None or self.workstream_memory is None:
            raise AppServerError("Lazy pracovní proud nemá úplný servisní backend.")
        binding = self.workstream_memory.binding(clean_id)
        hub = self.workstream_threads.active_hub(expected_workstream_id=clean_id)
        base = self.profiles[self.default_profile_id]["service"]
        state_root = self.workstream_threads.state_root / clean_id
        service = HumanAdamService(
            runtime=base.runtime,
            workspace=base.workspace,
            state_path=state_root / "session.json",
            context_anchor_path=state_root / "context_anchor.json",
            deployment_receipt_path=state_root / "deployment_receipt.json",
            deployment_diagnostic_path=state_root / "deployment_diagnostic.json",
            deployment_failure_history_path=state_root / "deployment_failures.json",
            work_profile_id=clean_id,
            codex_binary=base.codex_binary,
            profile_getter=base.profile_getter,
            hub=hub,
            developer_instructions=base.developer_instructions,
            tvbcp_relative_path=Path(binding.tvbcp_relative_path),
            tvbcp_title=f"{binding.name} – TVBCP",
        )
        service._profile = dict(base._profile)
        if service._profile:
            hub.model = str(service._profile.get("model") or "") or None
        with self._state_lock:
            return self._lazy_services.setdefault(clean_id, service)

    @property
    def active_service(self) -> HumanAdamService:
        return self.workstream_backends.service(
            self.active_workstream_id,
            lazy_service_factory=self._lazy_service,
        )

    @property
    def active_workstream_id(self) -> str:
        lazy_id = self.active_lazy_workstream_id
        if lazy_id:
            return lazy_id
        return self.workstream_backends.compatibility_workstream_id(
            self.active_profile_id
        )

    def service_for_profile(self, profile_id: str) -> HumanAdamService:
        clean_id = str(profile_id or "").strip()
        if clean_id not in self.profiles:
            raise AppServerError("Požadovaný pracovní profil neexistuje.")
        return self.profiles[clean_id]["service"]

    @property
    def workspace(self) -> HumanAdamWorkspaceManager:
        return self.active_service.workspace

    @property
    def hub(self):
        return self.active_service.hub

    @property
    def deployment_receipt_path(self) -> Path:
        return self.active_service.deployment_receipt_path

    @property
    def deployment_diagnostic_path(self) -> Path:
        return self.active_service.deployment_diagnostic_path

    @property
    def deployment_failure_history_path(self) -> Path:
        return self.active_service.deployment_failure_history_path

    @property
    def work_profile_id(self) -> str:
        return self.active_service.work_profile_id

    def simple_checkpoint_context(self) -> dict[str, Any]:
        """Return the canonical checkpoint binding of the active profile."""

        return self.workstream_coordinator.context(self.active_profile_id)

    def workstream_status(self) -> dict[str, Any]:
        """Return the private coordinator catalog without thread identifiers."""

        return self.workstream_coordinator.status(self.active_profile_id)

    def lazy_workstream_thread_status(self) -> dict[str, Any]:
        """Return the private phase-4.2 backend status without exposing it to UI."""

        if self.workstream_threads is None:
            return {"ok": True, "available": False, "workstreams": []}
        return {**self.workstream_threads.status(), "available": True}

    def lazy_workstream_memory_status(self) -> dict[str, Any]:
        """Return phase-4.3 bindings without creating missing documents."""

        if self.workstream_memory is None:
            return {"ok": True, "available": False, "workstreams": []}
        project_root = self.profiles[self.default_profile_id]["service"].workspace.project_root
        return {
            **self.workstream_memory.status(project_root=project_root),
            "available": True,
        }

    def grouped_workstream_status(self) -> dict[str, Any]:
        """Return the redacted menu model from one backend authority."""

        return self.grouped_workstream_selection.status(
            active_workstream_id=self.active_workstream_id,
            thread_status=(
                self.workstream_threads.status()
                if self.workstream_threads is not None
                else None
            ),
            memory_status=(
                self.workstream_memory.status(
                    project_root=self.profiles[self.default_profile_id][
                        "service"
                    ].workspace.project_root
                )
                if self.workstream_memory is not None
                else None
            ),
        )

    def open_lazy_workstream_thread(
        self,
        *,
        workstream_id: str,
        confirmed: bool,
    ) -> dict[str, Any]:
        """Internal phase-4.2 entrypoint; Cockpit API/UI integration follows later."""

        if self.workstream_threads is None:
            raise AppServerError("Soukromé vlákno pracovního proudu není dostupné.")
        if not self._operation_lock.acquire(blocking=False):
            raise SessionBusyError("Pracovní profil právě provádí jinou operaci.")
        try:
            return self.workstream_threads.open(
                workstream_id=workstream_id,
                confirmed=confirmed,
            )
        finally:
            self._operation_lock.release()

    def select_workstream(
        self,
        *,
        workstream_id: str,
        confirmed: bool,
    ) -> dict[str, Any]:
        """Select a registered workstream through the existing safe switch path.

        This method is intentionally not exposed through Cockpit API or UI in
        phase 1.3.  The delegated profile switch keeps the current thread,
        delivery and workspace guards and fast-forwards a clean target from
        committed local ``main`` when needed.
        """

        target_profile_id = self.workstream_backends.compatibility_profile_id(
            workstream_id
        )
        result = self.switch(profile_id=target_profile_id, confirmed=confirmed)
        return {
            **result,
            "workstream_selection": self.workstream_status(),
        }

    def simple_main_checkpoint(
        self,
        *,
        commit_message: str,
        summary: str,
        next_step: str,
        confirmed: bool,
    ) -> dict[str, Any]:
        """Run the inactive direct-main backend from profile-owned metadata.

        No caller-controlled workstream ID or memory path crosses this boundary.
        The method is intentionally not exposed through Cockpit API or UI yet.
        """

        with self.profile_operation() as service:
            active_id = self.active_profile_id
            profile = self.profiles[active_id]
            binding = profile.get("workstream_binding")
            if not isinstance(binding, CanonicalWorkstreamBinding):
                raise AppServerError(
                    "Aktivní profil nemá v terminálu zaregistrovaný kanonický pracovní proud."
                )
            memory_binding = (
                self.workstream_memory.binding(binding.workstream_id)
                if self.workstream_memory is not None
                else None
            )
            peer_workspaces = tuple(
                candidate["service"].workspace
                for profile_id, candidate in self.profiles.items()
                if profile_id != active_id
            )
            result = complete_simple_main_checkpoint(
                workspace=service.workspace,
                request=SimpleMainCheckpointRequest(
                    workstream_id=binding.workstream_id,
                    commit_message=commit_message,
                    summary=summary,
                    next_step=next_step,
                    handoff_relative_path=(
                        memory_binding.handoff_relative_path
                        if memory_binding is not None
                        else binding.handoff_relative_path
                    ),
                    tvbcp_relative_path=(
                        memory_binding.tvbcp_relative_path
                        if memory_binding is not None
                        else binding.tvbcp_relative_path
                    ),
                    handoff_initial_content=(
                        self.workstream_memory.initial_handoff(memory_binding)
                        if self.workstream_memory is not None and memory_binding is not None
                        else ""
                    ),
                    tvbcp_initial_content=(
                        self.workstream_memory.initial_tvbcp(memory_binding)
                        if self.workstream_memory is not None and memory_binding is not None
                        else ""
                    ),
                ),
                confirmed=confirmed,
                peer_workspaces=peer_workspaces,
            )
        return {
            **result,
            "work_profile": {
                "id": active_id,
                "label": str(profile.get("label") or active_id),
            },
            "workstream": {
                "id": binding.workstream_id,
                "type": binding.workstream_type,
                "name": binding.name,
            },
        }

    def simple_lazy_workstream_checkpoint(
        self,
        *,
        commit_message: str,
        summary: str,
        next_step: str,
        confirmed: bool,
    ) -> dict[str, Any]:
        """Checkpoint the active lazy stream from server-owned memory metadata."""

        if self.workstream_threads is None or self.workstream_memory is None:
            raise AppServerError("Lazy pracovní proud nemá kanonický checkpointový backend.")
        if not self._operation_lock.acquire(blocking=False):
            raise SessionBusyError("Pracovní profil právě provádí jinou operaci.")
        try:
            workstream_id = self.workstream_threads.checkpoint_workstream_id()
            self._assert_writable_lazy_workstream(workstream_id)
            memory_binding = self.workstream_memory.binding(workstream_id)
            service = self.profiles[self.default_profile_id]["service"]
            peer_workspaces = tuple(
                profile["service"].workspace
                for profile in self.profiles.values()
                if profile["service"].workspace.project_root
                != service.workspace.project_root
            )
            result = complete_simple_main_checkpoint(
                workspace=service.workspace,
                request=SimpleMainCheckpointRequest(
                    workstream_id=memory_binding.workstream_id,
                    commit_message=commit_message,
                    summary=summary,
                    next_step=next_step,
                    handoff_relative_path=memory_binding.handoff_relative_path,
                    tvbcp_relative_path=memory_binding.tvbcp_relative_path,
                    handoff_initial_content=self.workstream_memory.initial_handoff(
                        memory_binding
                    ),
                    tvbcp_initial_content=self.workstream_memory.initial_tvbcp(
                        memory_binding
                    ),
                ),
                confirmed=confirmed,
                peer_workspaces=peer_workspaces,
            )
            return {
                **result,
                "workstream": {
                    "id": memory_binding.workstream_id,
                    "type": memory_binding.workstream_type,
                    "name": memory_binding.name,
                },
            }
        finally:
            self._operation_lock.release()

    def _assert_all_profile_sessions_idle(self) -> None:
        """Block deployment while any registered workstream has an active or uncertain turn."""

        for profile_id, profile in self.profiles.items():
            session = profile["service"].hub.snapshot()
            label = str(profile.get("label") or profile_id)
            if session.get("turn_busy") or session.get("active_turn"):
                raise SessionBusyError(
                    f"Jednoduché nasazení nelze připravit: profil {label} má aktivní tah."
                )
            if self._has_uncertain_delivery(session):
                raise SessionBusyError(
                    f"Jednoduché nasazení nelze připravit: profil {label} má nevyřešené doručení."
                )

    def prepare_simple_main_deployment(
        self,
        *,
        previous_pid: int,
        confirmed: bool,
        restart_scheduler: Callable[[], dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Bind the private clean-main deployment backend to the active workstream.

        The caller cannot provide a workstream ID, commit, workspace or receipt
        path.  An optional trusted app-layer callback can schedule the existing
        restart worker after the full pre-restart proof succeeds.  No HTTP or UI
        surface invokes this method in phase 2.2.
        """

        self._assert_legacy_only_backend(operation="Nasazení")
        with self.profile_operation() as service:
            self._assert_all_profile_sessions_idle()
            active_id = self.active_profile_id
            profile = self.profiles[active_id]
            binding = profile.get("workstream_binding")
            if not isinstance(binding, CanonicalWorkstreamBinding):
                raise AppServerError(
                    "Aktivní profil nemá v terminálu zaregistrovaný kanonický pracovní proud."
                )
            source_head = str(service.workspace.status().get("source_head") or "")
            peers = tuple(
                candidate["service"].workspace
                for profile_id, candidate in self.profiles.items()
                if profile_id != active_id
            )
            result = prepare_clean_main_deployment(
                workspace=service.workspace,
                request=SimpleMainDeploymentRequest(
                    workstream_id=binding.workstream_id,
                    expected_head=source_head,
                    previous_pid=previous_pid,
                ),
                confirmed=confirmed,
                peer_workspaces=peers,
                receipt_path=self.simple_main_deployment_receipt_path,
            )
            restart: dict[str, Any] = {
                "ready": True,
                "scheduled": False,
                "message": "Nasazení je připravené pro existující řízený restart worker.",
            }
            if restart_scheduler is not None:
                if not callable(restart_scheduler):
                    raise AppServerError("Řízený restart worker není platný.")
                scheduled = restart_scheduler()
                if not isinstance(scheduled, dict) or scheduled.get("ok") is not True:
                    raise AppServerError(
                        "Nasazení je ověřené, ale řízený restart se nepodařilo naplánovat."
                    )
                restart = {**scheduled, "ready": True, "scheduled": True}
        return {
            **result,
            "work_profile": {
                "id": active_id,
                "label": str(profile.get("label") or active_id),
            },
            "workstream": {
                "id": binding.workstream_id,
                "type": binding.workstream_type,
                "name": binding.name,
            },
            "restart": restart,
        }

    def audit_simple_main_deployment(self) -> dict[str, Any]:
        """Audit the active canonical workstream for one clean-main deployment."""

        self._assert_legacy_only_backend(operation="Audit nasazení")
        with self.profile_operation() as service:
            self._assert_all_profile_sessions_idle()
            active_id = self.active_profile_id
            profile = self.profiles[active_id]
            binding = profile.get("workstream_binding")
            if not isinstance(binding, CanonicalWorkstreamBinding):
                raise AppServerError(
                    "Aktivní profil nemá v terminálu zaregistrovaný kanonický pracovní proud."
                )
            peers = tuple(
                candidate["service"].workspace
                for profile_id, candidate in self.profiles.items()
                if profile_id != active_id
            )
            result = audit_clean_main_deployment(
                workspace=service.workspace,
                workstream_id=binding.workstream_id,
                peer_workspaces=peers,
            )
        return {
            **result,
            "work_profile": {
                "id": active_id,
                "label": str(profile.get("label") or active_id),
            },
            "workstream": {
                "id": binding.workstream_id,
                "type": binding.workstream_type,
                "name": binding.name,
            },
            "handoff_takeover_check": {
                "state": "verified",
                "label": "Kanonický pracovní proud",
                "message": "Čistý main je svázaný s aktivním handoffem a TVBCP.",
                "target_handoff": binding.handoff_relative_path,
                "blocking": False,
            },
        }

    def verify_simple_main_deployment(
        self,
        *,
        observed_pid: int,
        observed_code_stamp: str,
    ) -> dict[str, Any]:
        """Verify a restarted clean-main deployment in its canonical workstream."""

        with self.profile_operation() as service:
            self._assert_all_profile_sessions_idle()
            receipt = load_simple_main_deployment_receipt(
                self.simple_main_deployment_receipt_path
            )
            workstream_id = str(receipt.get("workstream_id") or "")
            owner_id = self.workstream_backends.compatibility_profile_id(workstream_id)
            active_id = self.active_profile_id
            if owner_id != active_id:
                raise AppServerError(
                    "Ověření nasazení patří jinému pracovnímu proudu; nejdřív jej znovu aktivuj."
                )
            profile = self.profiles[active_id]
            binding = profile.get("workstream_binding")
            if (
                not isinstance(binding, CanonicalWorkstreamBinding)
                or binding.workstream_id != workstream_id
            ):
                raise AppServerError("Účtenka nasazení neodpovídá aktivnímu pracovnímu proudu.")
            peers = tuple(
                candidate["service"].workspace
                for profile_id, candidate in self.profiles.items()
                if profile_id != active_id
            )
            result = verify_clean_main_deployment(
                workspace=service.workspace,
                observed_pid=observed_pid,
                observed_code_stamp=observed_code_stamp,
                peer_workspaces=peers,
                receipt_path=self.simple_main_deployment_receipt_path,
            )
        return {
            **result,
            "work_profile": {
                "id": active_id,
                "label": str(profile.get("label") or active_id),
            },
            "workstream": {
                "id": binding.workstream_id,
                "type": binding.workstream_type,
                "name": binding.name,
            },
        }

    def _profile_rows(self) -> list[dict[str, Any]]:
        active_id = "" if self.active_lazy_workstream_id else self.active_profile_id
        return [
            {
                "id": profile_id,
                "label": str(profile.get("label") or profile_id),
                "description": str(profile.get("description") or ""),
                "active": profile_id == active_id,
                "tvbcp_title": profile["service"].tvbcp_title,
            }
            for profile_id, profile in self.profiles.items()
        ]

    def _active_work_profile(self, selection: dict[str, Any]) -> dict[str, Any]:
        lazy_id = self.active_lazy_workstream_id
        active = selection.get("active") if isinstance(selection, dict) else None
        if lazy_id and isinstance(active, dict):
            return {
                "id": lazy_id,
                "label": str(active.get("workstream_name") or lazy_id),
                "description": str(active.get("workstream_type") or "Pracovní proud"),
                "backend": "lazy_private_thread",
            }
        active_id = self.active_profile_id
        profile = self.profiles[active_id]
        return {
            "id": active_id,
            "label": str(profile.get("label") or active_id),
            "description": str(profile.get("description") or ""),
            "backend": COMPATIBILITY_ADAPTER_BACKEND,
        }

    def _workstream_capabilities(self) -> dict[str, Any]:
        lazy_id = self.active_lazy_workstream_id
        lazy = bool(lazy_id)
        writable_pilot = lazy_id in WRITABLE_LAZY_WORKSTREAM_IDS
        return {
            "conversation": True,
            "context_anchor": True,
            "tvbcp": True,
            "development": not lazy or writable_pilot,
            "checkpoint": not lazy or writable_pilot,
            "deployment": not lazy,
            "lazy_backend": lazy,
            "writable_pilot": writable_pilot,
        }

    def _assert_writable_lazy_workstream(self, workstream_id: str) -> None:
        clean_id = str(workstream_id or "").strip()
        if clean_id not in WRITABLE_LAZY_WORKSTREAM_IDS:
            raise AppServerError(
                "Tento lazy pracovní proud zůstává read-only; zapisovací pilot je povolen jen pro MMTX."
            )

    def _assert_legacy_only_backend(self, *, operation: str) -> None:
        if self.active_lazy_workstream_id:
            raise AppServerError(
                f"{operation} lazy pracovního proudu v MMTX pilotu zatím není povolené."
            )

    def status(self) -> dict[str, Any]:
        try:
            selection = self.grouped_workstream_status()
            active = selection.get("active") or {}
            active_workstream_id = str(active.get("workstream_id") or "")
            payload = self.active_service.status()
            recent_deployment = load_recent_simple_main_deployment(
                self.simple_main_deployment_receipt_path
            )
            if recent_deployment and (
                recent_deployment.get("workstream_id") != active_workstream_id
            ):
                recent_deployment = None
            return {
                **payload,
                "work_profile": self._active_work_profile(selection),
                "work_profiles": self._profile_rows(),
                "workstream_selection": selection,
                "workstream_capabilities": self._workstream_capabilities(),
                "development_semaphore": self.development_status(),
                "recent_simple_main_deployment": recent_deployment,
            }
        except (AppServerError, SessionHubError, OSError, ValueError) as exc:
            return {
                "ok": False,
                "status": "human_adam_profile_status_failed",
                "message": str(exc),
                "work_profiles": [],
                "workstream_selection": {
                    "ok": False,
                    "private_backend": True,
                    "active": {},
                    "workstreams": [],
                    "workstream_count": 0,
                },
                "development_semaphore": self.development_status(),
            }

    @contextmanager
    def profile_operation(self) -> Iterator[HumanAdamService]:
        if not self._operation_lock.acquire(blocking=False):
            raise SessionBusyError("Pracovní profil právě provádí jinou operaci.")
        try:
            yield self.active_service
        finally:
            self._operation_lock.release()

    def connect(self) -> dict[str, Any]:
        workspace_synced = False
        with self.profile_operation() as service:
            workspace = service.workspace.status()
            session = service.hub.snapshot()
            if workspace.get("source_update_available"):
                if session.get("turn_busy") or session.get("active_turn"):
                    raise SessionBusyError(
                        "Workspace nelze aktualizovat během aktivního tahu Adama."
                    )
                if self._has_uncertain_delivery(session):
                    raise SessionBusyError(
                        "Workspace nelze aktualizovat, dokud není vyřešené nejisté doručení."
                    )
                if int(workspace.get("source_pending_changes") or 0) > 0:
                    raise AppServerError(
                        "Zdrojový main má pracovní změny; aktivní profil nyní nelze bezpečně aktualizovat."
                    )
                self._assert_target_workspace(workspace)
                workspace = service.workspace.sync_from_main(confirmed=True)
                self._assert_target_workspace(workspace)
                workspace_synced = True
            runtime_recovery_allowed = bool(
                not session.get("turn_busy")
                and not session.get("active_turn")
                and not self._has_uncertain_delivery(session)
            )
            result = service.connect(
                recover_unreachable_runtime=runtime_recovery_allowed
            )
        return {
            **result,
            **self._profile_status_fields(),
            "workspace_synced": workspace_synced,
        }

    def send(self, **kwargs: Any) -> dict[str, Any]:
        with self.profile_operation() as service:
            lease = self.development_semaphore.status()
            active_id = self.work_profile_id
            lazy_id = self.active_lazy_workstream_id
            if lazy_id:
                writable = lazy_id in WRITABLE_LAZY_WORKSTREAM_IDS
                state = "pilot" if writable else "read_only"
                control_source = (
                    "mmtx_writable_pilot" if writable else "lazy_read_only_policy"
                )
                control_owner = active_id if writable else "none"
            else:
                writable = bool(
                    lease.get("ok") is True
                    and lease.get("active") is True
                    and lease.get("mode") == "active"
                    and lease.get("owner_id") == active_id
                )
                if lease.get("ok") is not True:
                    state = "invalid"
                elif lease.get("active") is not True:
                    state = "free"
                else:
                    state = str(lease.get("mode") or "invalid")
                control_source = "private_global_development_semaphore"
                control_owner = str(lease.get("owner_id") or "none")
            development_control_block = "\n".join(
                (
                    "[DEVELOPMENT_CONTROL]",
                    f"source={control_source}",
                    f"profile_id={active_id}",
                    f"lease_state={state}",
                    f"lease_owner_id={control_owner}",
                    f"writable={'true' if writable else 'false'}",
                    "rule=When writable=false, remain read-only and do not change files or Git.",
                    "[/DEVELOPMENT_CONTROL]",
                )
            )
            completion_instruction = automatic_completion_instruction(writable=writable)
            if completion_instruction:
                development_control_block = (
                    development_control_block + "\n\n" + completion_instruction
                )
            result = service.send(
                **kwargs,
                development_control_block=development_control_block,
            )
            return self._complete_successful_turn(
                service=service,
                active_id=active_id,
                writable=writable,
                result=result,
            )

    @staticmethod
    def _completion_answer(visible_answer: str, note: str) -> str:
        clean_answer = str(visible_answer or "").strip()
        clean_note = str(note or "").strip()
        if clean_answer and clean_note:
            return f"{clean_answer}\n\n—\n{clean_note}"
        return clean_answer or clean_note

    @staticmethod
    def _store_completed_answer(
        *,
        service: HumanAdamService,
        entry: dict[str, Any],
        answer: str,
    ) -> bool:
        client_message_id = str(entry.get("client_message_id") or "")
        entry["answer"] = answer
        if client_message_id:
            try:
                service.hub.replace_completed_answer(
                    client_message_id=client_message_id,
                    answer=answer,
                )
                return True
            except (SessionHubError, OSError, ValueError):
                return False
        return False

    def _completion_checkpoint(
        self,
        *,
        service: HumanAdamService,
        active_id: str,
        metadata: TurnCompletionMetadata,
    ) -> dict[str, Any]:
        lazy_id = self.active_lazy_workstream_id
        if lazy_id:
            if (
                active_id != lazy_id
                or self.workstream_threads is None
                or self.workstream_memory is None
            ):
                raise AppServerError("Aktivní lazy pracovní proud nemá úplný checkpointový backend.")
            self._assert_writable_lazy_workstream(lazy_id)
            checkpoint_id = self.workstream_threads.checkpoint_workstream_id()
            if checkpoint_id != lazy_id:
                raise AppServerError("Aktivní lazy pracovní proud se před checkpointem změnil.")
            memory_binding = self.workstream_memory.binding(lazy_id)
            binding_id = memory_binding.workstream_id
            handoff_path = memory_binding.handoff_relative_path
            tvbcp_path = memory_binding.tvbcp_relative_path
            handoff_initial = self.workstream_memory.initial_handoff(memory_binding)
            tvbcp_initial = self.workstream_memory.initial_tvbcp(memory_binding)
            peers = tuple(
                candidate["service"].workspace
                for candidate in self.profiles.values()
                if candidate["service"].workspace.project_root
                != service.workspace.project_root
            )
        else:
            profile = self.profiles[active_id]
            binding = profile.get("workstream_binding")
            if not isinstance(binding, CanonicalWorkstreamBinding):
                raise AppServerError(
                    "Aktivní profil nemá v terminálu zaregistrovaný kanonický pracovní proud."
                )
            memory_binding = (
                self.workstream_memory.binding(binding.workstream_id)
                if self.workstream_memory is not None
                else None
            )
            binding_id = binding.workstream_id
            handoff_path = (
                memory_binding.handoff_relative_path
                if memory_binding is not None
                else binding.handoff_relative_path
            )
            tvbcp_path = (
                memory_binding.tvbcp_relative_path
                if memory_binding is not None
                else binding.tvbcp_relative_path
            )
            handoff_initial = (
                self.workstream_memory.initial_handoff(memory_binding)
                if self.workstream_memory is not None and memory_binding is not None
                else ""
            )
            tvbcp_initial = (
                self.workstream_memory.initial_tvbcp(memory_binding)
                if self.workstream_memory is not None and memory_binding is not None
                else ""
            )
            peers = tuple(
                candidate["service"].workspace
                for profile_id, candidate in self.profiles.items()
                if profile_id != active_id
            )
        return complete_simple_main_checkpoint(
            workspace=service.workspace,
            request=SimpleMainCheckpointRequest(
                workstream_id=binding_id,
                commit_message=metadata.commit_message,
                summary=metadata.summary,
                next_step=metadata.next_step,
                handoff_relative_path=handoff_path,
                tvbcp_relative_path=tvbcp_path,
                handoff_initial_content=handoff_initial,
                tvbcp_initial_content=tvbcp_initial,
            ),
            confirmed=True,
            peer_workspaces=peers,
        )

    def _complete_successful_turn(
        self,
        *,
        service: HumanAdamService,
        active_id: str,
        writable: bool,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """Finish a delivered writable turn, or leave its work visibly recoverable."""

        if result.get("duplicate_prevented") is True:
            entry = result.get("entry")
            if isinstance(entry, dict):
                parsed = parse_turn_completion(entry.get("answer"))
                if parsed.state != "absent":
                    answer = self._completion_answer(
                        parsed.visible_answer,
                        "Opakovaná zpráva byla rozpoznána; automatické dokončení se znovu nespustilo.",
                    )
                    self._store_completed_answer(service=service, entry=entry, answer=answer)
            return {
                **result,
                "automatic_completion": {"state": "duplicate_prevented", "attempted": False},
            }
        entry = result.get("entry")
        if not isinstance(entry, dict):
            return {
                **result,
                "automatic_completion": {"state": "unavailable", "attempted": False},
            }
        parsed: ParsedTurnCompletion = parse_turn_completion(entry.get("answer"))
        workspace = service.workspace.status()
        dirty = bool(workspace.get("dirty"))
        if not dirty and parsed.state == "absent":
            return {
                **result,
                "automatic_completion": {"state": "not_needed", "attempted": False},
            }

        if not dirty:
            note = "Automatické dokončení se nespustilo: tah nezanechal změnu souborů."
            answer = self._completion_answer(parsed.visible_answer, note)
            answer_persisted = self._store_completed_answer(
                service=service,
                entry=entry,
                answer=answer,
            )
            return {
                **result,
                "entry": entry,
                "automatic_completion": {
                    "state": "no_changes",
                    "attempted": False,
                    "answer_persisted": answer_persisted,
                },
            }

        if not writable:
            note = (
                "Automatické dokončení bylo bezpečně zastaveno: tah neměl oprávnění "
                "k zápisu. Změny zůstaly viditelné ve workspace."
            )
            answer = self._completion_answer(parsed.visible_answer, note)
            answer_persisted = self._store_completed_answer(
                service=service,
                entry=entry,
                answer=answer,
            )
            return {
                **result,
                "entry": entry,
                "automatic_completion": {
                    "state": "not_authorized",
                    "attempted": False,
                    "answer_persisted": answer_persisted,
                },
            }

        if parsed.state != "valid" or parsed.metadata is None:
            detail = parsed.error or "Chybí platná dokončovací účtenka."
            note = (
                f"Automatické dokončení bylo bezpečně zastaveno: {detail} "
                "Změny zůstaly viditelné ve workspace."
            )
            answer = self._completion_answer(parsed.visible_answer, note)
            answer_persisted = self._store_completed_answer(
                service=service,
                entry=entry,
                answer=answer,
            )
            return {
                **result,
                "entry": entry,
                "automatic_completion": {
                    "state": "metadata_missing" if parsed.state == "absent" else "metadata_invalid",
                    "attempted": False,
                    "message": detail,
                    "answer_persisted": answer_persisted,
                },
            }

        try:
            checkpoint = self._completion_checkpoint(
                service=service,
                active_id=active_id,
                metadata=parsed.metadata,
            )
        except (AppServerError, SessionHubError, OSError, ValueError) as exc:
            note = (
                f"Automatické dokončení bylo bezpečně zastaveno: {exc} "
                "Rozpracované změny nebo zachovaný lokální commit zůstaly viditelné."
            )
            answer = self._completion_answer(parsed.visible_answer, note)
            answer_persisted = self._store_completed_answer(
                service=service,
                entry=entry,
                answer=answer,
            )
            return {
                **result,
                "entry": entry,
                "automatic_completion": {
                    "state": "failed",
                    "attempted": True,
                    "message": str(exc),
                    "answer_persisted": answer_persisted,
                },
            }

        all_aligned = checkpoint.get("all_workspaces_aligned") is not False
        alignment_note = (
            "Všechny profilové workspaces jsou čisté a synchronizované."
            if all_aligned
            else "Checkpoint je hotový; jeden čistý profil se dorovná při příštím Připojit."
        )
        note = (
            f"Automatické dokončení: testy prošly, commit "
            f"`{str(checkpoint.get('checkpoint_short') or '')}` je na main a pushnutý. "
            f"{alignment_note}"
        )
        answer = self._completion_answer(parsed.visible_answer, note)
        answer_persisted = self._store_completed_answer(
            service=service,
            entry=entry,
            answer=answer,
        )
        return {
            **result,
            "entry": entry,
            "automatic_completion": {
                "state": "completed" if all_aligned else "completed_sync_pending",
                "attempted": True,
                "checkpoint": checkpoint,
                "answer_persisted": answer_persisted,
            },
        }

    def tvbcp(self) -> dict[str, Any]:
        return self.active_service.tvbcp()

    def context_anchor(self, *, include_content: bool = True) -> dict[str, Any]:
        return self.active_service.context_anchor(include_content=include_content)

    def set_context_anchor(self, **kwargs: Any) -> dict[str, Any]:
        with self.profile_operation() as service:
            return service.set_context_anchor(**kwargs)

    def thread_rotation_status(self) -> dict[str, Any]:
        with self.profile_operation() as service:
            return service.thread_rotation_status()

    def rotate_thread(self, **kwargs: Any) -> dict[str, Any]:
        with self.profile_operation() as service:
            return service.rotate_thread(**kwargs)

    def work_review(self) -> dict[str, Any]:
        work = self.active_service.work_review()
        return {
            **work,
            "development_semaphore": self.development_status(),
            "project_continuity": self.project_continuity_status(),
            "handoff_proposal": self.handoff_proposal_status(work_review=work),
        }

    def handoff_proposal_status(
        self,
        *,
        work_review: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Derive a non-persistent handoff draft from one owned checkpoint."""
        waiting = {
            "ok": True,
            "available": False,
            "read_only": True,
            "blocking": False,
            "writes_performed": False,
            "state": "waiting_checkpoint",
            "label": "Čeká na checkpoint",
            "message": "Návrh vznikne až po checkpointu vlastněném tímto profilem.",
            "draft": "",
            "changed_files": [],
        }
        try:
            active_id = self.active_profile_id
            lease = self.development_semaphore.status()
            if (
                lease.get("ok") is not True
                or lease.get("active") is not True
                or lease.get("owner_id") != active_id
            ):
                return waiting
            binding = {
                "project_id": str(lease.get("project_id") or ""),
                "project_label": str(lease.get("project_label") or ""),
                "handoff_path": str(lease.get("handoff_path") or ""),
                "tvbcp_path": str(lease.get("tvbcp_path") or ""),
            }
            review = work_review if work_review is not None else self.active_service.work_review()
            return self.project_continuity.handoff_proposal(
                binding=binding,
                topic=str(lease.get("topic") or ""),
                workspace_review=review,
                context_anchor=self.active_service.context_anchor(include_content=False),
            )
        except (AppServerError, ProjectContinuityError, OSError, TypeError, ValueError) as exc:
            return {
                **waiting,
                "ok": False,
                "state": "unverifiable",
                "label": "Nelze připravit",
                "message": str(exc),
            }

    def project_continuity_status(self) -> dict[str, Any]:
        """Return project choices and conservative read-only freshness evidence."""
        try:
            active_id = self.active_profile_id
            profile = self.profiles[active_id]
            default_label = str(profile.get("default_project_name") or "")
            projects = self.project_continuity.public_catalog()
            default_project_id = self.project_continuity.default_project_id(default_label)
            lease = self.development_semaphore.status()
            binding = {
                "project_id": str(lease.get("project_id") or ""),
                "project_label": str(lease.get("project_label") or ""),
                "handoff_path": str(lease.get("handoff_path") or ""),
                "tvbcp_path": str(lease.get("tvbcp_path") or ""),
            }
            include_profile_receipt = bool(
                binding["project_id"] and binding["project_id"] == default_project_id
            )
            audit = self.project_continuity.audit(
                binding=binding,
                workspace_root=self.active_service.workspace.project_root,
                workspace_review=self.active_service.workspace.review(),
                context_anchor=self.active_service.context_anchor(include_content=False),
                deployment_receipt_path=(
                    self.active_service.deployment_receipt_path if include_profile_receipt else None
                ),
            )
            if (
                binding["project_id"]
                and lease.get("active") is True
                and lease.get("owner_id") == TERMINAL_OWNER_ID
                and audit.get("state") != "unverifiable"
            ):
                audit = {
                    **audit,
                    "state": "unverifiable",
                    "label": "Nelze ověřit",
                    "message": (
                        "Projektová vazba je uložená, ale Cockpit nezná přesný pracovní strom "
                        "terminálového Adama."
                    ),
                    "reasons": [
                        "Audit terminálového WIP vyžaduje pozdější bezpečnou registraci jeho workspace.",
                        *list(audit.get("reasons") or []),
                    ],
                }
            return {
                "ok": True,
                "read_only": True,
                "blocking": False,
                "projects": projects,
                "default_project_id": default_project_id,
                "binding": binding,
                "audit": audit,
            }
        except (AppServerError, ProjectContinuityError, OSError, ValueError) as exc:
            return {
                "ok": False,
                "read_only": True,
                "blocking": False,
                "projects": [],
                "default_project_id": "",
                "binding": {},
                "audit": {
                    "ok": False,
                    "read_only": True,
                    "blocking": False,
                    "state": "unverifiable",
                    "label": "Nelze ověřit",
                    "message": str(exc),
                    "reasons": [],
                    "evidence": [],
                },
            }

    def takeover_handoff_check(
        self,
        *,
        deployment_audit: dict[str, Any],
        active_service: HumanAdamService | None = None,
    ) -> dict[str, Any]:
        """Return a warning-only proof for the handoff selected by the lease."""
        fallback = {
            "ok": False,
            "read_only": True,
            "blocking": False,
            "writes_performed": False,
            "state": "unverifiable",
            "label": "Nelze ověřit",
            "message": "Kontrola handoffu selhala bezpečně; nasazení zatím neblokuje.",
            "handoff_in_checkpoint": False,
        }
        try:
            service = active_service or self.active_service
            owner_id = str(getattr(service, "work_profile_id", "") or "")
            lease = self.development_semaphore.status()
            if (
                lease.get("ok") is not True
                or lease.get("active") is not True
                or lease.get("owner_id") != owner_id
            ):
                return fallback
            if deployment_audit.get("ok") is not True or deployment_audit.get("ready") is not True:
                return fallback
            binding = {
                "project_id": str(lease.get("project_id") or ""),
                "project_label": str(lease.get("project_label") or ""),
                "handoff_path": str(lease.get("handoff_path") or ""),
                "tvbcp_path": str(lease.get("tvbcp_path") or ""),
            }
            changes = deployment_audit.get("changes")
            if not isinstance(changes, list):
                return fallback
            return self.project_continuity.takeover_handoff_check(
                binding=binding,
                checkpoint_changes=changes,
                project_dir_name=service.workspace.project_root.name,
            )
        except (AppServerError, ProjectContinuityError, OSError, TypeError, ValueError):
            return fallback

    def _load_deployment_completion(self) -> dict[str, Any]:
        if not self.deployment_completion_path.is_file():
            return {}
        try:
            raw = json.loads(self.deployment_completion_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AppServerError("Stav dokončení nasazení nelze bezpečně načíst.") from exc
        if not isinstance(raw, dict) or raw.get("schema_version") != DEPLOYMENT_COMPLETION_SCHEMA:
            raise AppServerError("Stav dokončení nasazení má neznámé schéma.")
        return raw

    def prepare_deployment_completion(
        self,
        *,
        profile_id: str,
        deployment_result: dict[str, Any],
        previous_pid: int,
    ) -> dict[str, Any]:
        """Persist only safe facts required for explicit post-restart completion."""
        lease = self.development_semaphore.status()
        if lease.get("ok") is not True or lease.get("owner_id") != profile_id:
            raise AppServerError("Dokončení nasazení nemá vlastněný vývojový semafor.")
        binding = self.project_continuity.resolve_binding(
            project_id=str(lease.get("project_id") or ""),
            handoff_path=str(lease.get("handoff_path") or ""),
            fallback_tvbcp_path=str(lease.get("tvbcp_path") or ""),
        )
        checkpoint_head = str(deployment_result.get("checkpoint_token") or "").strip().casefold()
        gate = deployment_result.get("gate") or {}
        test_count = int(gate.get("test_count") or 0)
        confirmation = deployment_result.get("deployment_confirmation") or {}
        deployed_at = str(confirmation.get("completed_at") or "").strip()
        clean_previous_pid = int(previous_pid)
        if (
            not re.fullmatch(r"[0-9a-f]{40}", checkpoint_head)
            or test_count <= 0
            or not deployed_at
            or clean_previous_pid <= 0
        ):
            raise AppServerError("Nasazení neposkytlo úplné podklady pro dokončení handoffu.")
        record = {
            "schema_version": DEPLOYMENT_COMPLETION_SCHEMA,
            "state": "pending_restart",
            "profile_id": profile_id,
            "project_id": binding["project_id"],
            "project_label": binding["project_label"],
            "handoff_path": binding["handoff_path"],
            "tvbcp_path": binding.get("tvbcp_path", ""),
            "checkpoint_head": checkpoint_head,
            "test_count": test_count,
            "previous_pid": clean_previous_pid,
            "deployed_at": deployed_at,
            "created_at": _now(),
            "completion_commit": "",
            "completed_at": "",
        }
        atomic_write_json(self.deployment_completion_path, record, ensure_ascii=False, indent=2)
        return {
            "ok": True,
            "available": True,
            "ready": False,
            "state": "pending_restart",
            "label": "Čeká na restart a smoke test",
            "message": "Po návratu Cockpitu otevři Práci a potvrď dokončení handoffu.",
            "blocking": False,
            "writes_performed": False,
        }

    def deployment_completion_status(self) -> dict[str, Any]:
        """Audit restart, Git and smoke evidence without changing handoff or Git."""
        base = {
            "ok": True,
            "available": False,
            "ready": False,
            "read_only": True,
            "blocking": False,
            "writes_performed": False,
            "state": "idle",
            "label": "Bez čekajícího dokončení",
            "message": "Po nasazení se zde nabídne potvrzené dokončení handoffu.",
            "confirmation_text": DEPLOYMENT_COMPLETION_CONFIRMATION,
            "evidence": [],
        }
        try:
            record = self._load_deployment_completion()
            if not record:
                return base
            state = str(record.get("state") or "")
            if state == "complete":
                return {
                    **base,
                    "available": True,
                    "state": "complete",
                    "label": "Handoff dokončen",
                    "message": "Ověřené dokončení je commitnuté a pushnuté v main.",
                    "checkpoint_head": str(record.get("checkpoint_head") or ""),
                    "completion_commit": str(record.get("completion_commit") or ""),
                    "project_label": str(record.get("project_label") or ""),
                    "target_handoff": str(record.get("handoff_path") or ""),
                    "test_count": int(record.get("test_count") or 0),
                }
            if state not in {"pending_restart", "local_commit_pending_push"}:
                raise AppServerError("Stav dokončení nasazení není podporovaný.")

            profile_id = str(record.get("profile_id") or "")
            binding = self.project_continuity.resolve_binding(
                project_id=str(record.get("project_id") or ""),
                handoff_path=str(record.get("handoff_path") or ""),
                fallback_tvbcp_path=str(record.get("tvbcp_path") or ""),
            )
            lease = self.development_semaphore.status()
            binding_matches = bool(
                lease.get("ok") is True
                and lease.get("active") is True
                and lease.get("owner_id") == profile_id
                and lease.get("project_id") == binding["project_id"]
                and lease.get("handoff_path") == binding["handoff_path"]
            )
            active_profile_matches = self.active_profile_id == profile_id
            checkpoint_head = str(record.get("checkpoint_head") or "").strip().casefold()
            previous_pid = int(record.get("previous_pid") or 0)
            restart_confirmed = previous_pid > 0 and os.getpid() != previous_pid
            repo_root = Path(_git_text(self.project_continuity.project_root, ["rev-parse", "--show-toplevel"]))
            local_head = _git_text(repo_root, ["rev-parse", "main"]).casefold()
            origin_head = _git_text(repo_root, ["rev-parse", "origin/main"]).casefold()
            worktree_clean = not bool(_git_text(repo_root, ["status", "--porcelain=v1"]))
            completion_commit = str(record.get("completion_commit") or "").strip().casefold()
            if state == "local_commit_pending_push":
                git_aligned = bool(
                    re.fullmatch(r"[0-9a-f]{40}", completion_commit)
                    and local_head == completion_commit
                    and origin_head in {checkpoint_head, completion_commit}
                    and _git_text(repo_root, ["rev-parse", f"{completion_commit}^"]).casefold()
                    == checkpoint_head
                )
            else:
                git_aligned = local_head == checkpoint_head and origin_head == checkpoint_head
            smoke_results = run_smoke_check("http://127.0.0.1:8770", 3.0)
            smoke_passed = len(smoke_results) == 5 and all(item.ok for item in smoke_results)
            evidence = [
                {"label": "Nový proces Cockpitu", "ok": restart_confirmed},
                {"label": "Projekt a handoff", "ok": binding_matches and active_profile_matches},
                {"label": "Main a origin/main", "ok": git_aligned and worktree_clean},
                {"label": "Smoke test 5/5", "ok": smoke_passed},
            ]
            ready = all(item["ok"] for item in evidence)
            return {
                **base,
                "available": True,
                "ready": ready,
                "state": state if ready else "unverifiable",
                "label": "Připraveno k potvrzení" if ready else "Nelze dokončit",
                "message": (
                    "Všechny důkazy jsou ověřené; zadej další krok a přesnou větu."
                    if ready
                    else "Dokončení čeká na všechny ověřené důkazy; nic nebylo změněno."
                ),
                "project_label": binding["project_label"],
                "target_handoff": binding["handoff_path"],
                "checkpoint_head": checkpoint_head,
                "test_count": int(record.get("test_count") or 0),
                "evidence": evidence,
            }
        except (AppServerError, ProjectContinuityError, OSError, TypeError, ValueError):
            return {
                **base,
                "ok": False,
                "available": True,
                "state": "unverifiable",
                "label": "Nelze dokončit",
                "message": "Dokončení nasazení nelze bezpečně ověřit; nic nebylo změněno.",
            }

    def _finalize_deployment_completion_unlocked(
        self,
        *,
        confirmation: str,
        next_step: str,
    ) -> dict[str, Any]:
        """Append, commit and push one handoff entry after exact confirmation."""
        if str(confirmation or "").strip() != DEPLOYMENT_COMPLETION_CONFIRMATION:
            raise AppServerError(
                f"Chybí přesná potvrzovací věta: {DEPLOYMENT_COMPLETION_CONFIRMATION}"
            )
        status = self.deployment_completion_status()
        if status.get("ready") is not True:
            raise AppServerError(str(status.get("message") or "Dokončení není připravené."))
        record = self._load_deployment_completion()
        repo_root = Path(_git_text(self.project_continuity.project_root, ["rev-parse", "--show-toplevel"]))
        _git_text(repo_root, ["fetch", "origin", "main"], timeout=60)
        checkpoint_head = str(record.get("checkpoint_head") or "").strip().casefold()
        state = str(record.get("state") or "")
        completion_commit = str(record.get("completion_commit") or "").strip().casefold()

        if state == "pending_restart":
            if (
                _git_text(repo_root, ["rev-parse", "main"]).casefold() != checkpoint_head
                or _git_text(repo_root, ["rev-parse", "origin/main"]).casefold() != checkpoint_head
                or _git_text(repo_root, ["status", "--porcelain=v1"])
            ):
                raise AppServerError("Main se od ověření změnil; dokončení bylo bezpečně zastaveno.")
            completion = self.project_continuity.deployment_completion_entry(
                binding=record,
                checkpoint_head=checkpoint_head,
                test_count=int(record.get("test_count") or 0),
                deployed_at=str(record.get("deployed_at") or ""),
                next_step=next_step,
            )
            target = self.project_continuity.project_root / completion["target_handoff"]
            original = target.read_text(encoding="utf-8")
            if completion["marker"] in original:
                raise AppServerError("Toto dokončení už v handoffu existuje.")
            repo_relative = target.relative_to(repo_root).as_posix()
            with exclusive_file_lock(self.deployment_completion_path):
                atomic_replace_text_under_external_lock(
                    target,
                    original.rstrip() + "\n" + completion["entry"],
                )
            changed = _git_text(repo_root, ["status", "--porcelain=v1"])
            if len(changed.splitlines()) != 1 or repo_relative not in changed:
                with exclusive_file_lock(self.deployment_completion_path):
                    atomic_replace_text_under_external_lock(target, original)
                raise AppServerError("Handoff nelze izolovaně připravit k potvrzenému commitu.")
            try:
                _git_text(
                    repo_root,
                    ["commit", "--only", "-m", "Record confirmed deployment completion", "--", repo_relative],
                    timeout=60,
                )
            except AppServerError:
                with exclusive_file_lock(self.deployment_completion_path):
                    atomic_replace_text_under_external_lock(target, original)
                raise
            completion_commit = _git_text(repo_root, ["rev-parse", "HEAD"]).casefold()
            record = {
                **record,
                "state": "local_commit_pending_push",
                "completion_commit": completion_commit,
                "next_step": completion["next_step"],
            }
            atomic_write_json(self.deployment_completion_path, record, ensure_ascii=False, indent=2)

        origin_head = _git_text(repo_root, ["rev-parse", "origin/main"]).casefold()
        if origin_head == checkpoint_head:
            _git_text(repo_root, ["push", "origin", "main:main"], timeout=90)
            _git_text(repo_root, ["fetch", "origin", "main"], timeout=60)
            origin_head = _git_text(repo_root, ["rev-parse", "origin/main"]).casefold()
        if not completion_commit or origin_head != completion_commit:
            raise AppServerError(
                "Handoff je commitnutý lokálně, ale push nebyl potvrzen; semafor zůstává aktivní."
            )

        completed_record = {
            **record,
            "state": "complete",
            "completion_commit": completion_commit,
            "completed_at": _now(),
        }
        atomic_write_json(
            self.deployment_completion_path,
            completed_record,
            ensure_ascii=False,
            indent=2,
        )
        lease = self.development_semaphore.status()
        release_message = "Vývojový semafor zůstal aktivní."
        try:
            self.development_semaphore.release(
                owner_id=str(record.get("profile_id") or ""),
                expected_revision=int(lease.get("revision") or 0),
                confirmed=True,
                safe_to_release=self._safe_to_release(),
            )
            release_message = "Vývojový semafor byl po potvrzeném dokončení uvolněn."
        except AppServerError as exc:
            release_message = f"Handoff je dokončený, ale semafor zůstal aktivní: {exc}"
        return {
            **self.deployment_completion_status(),
            "ok": True,
            "writes_performed": True,
            "completion_commit": completion_commit,
            "release_message": release_message,
        }

    def finalize_deployment_completion(
        self,
        *,
        confirmation: str,
        next_step: str,
    ) -> dict[str, Any]:
        if not self._operation_lock.acquire(blocking=False):
            raise SessionBusyError("Dokončení nasazení právě provádí jinou operaci.")
        try:
            return self._finalize_deployment_completion_unlocked(
                confirmation=confirmation,
                next_step=next_step,
            )
        finally:
            self._operation_lock.release()

    def checkpoint(self, **kwargs: Any) -> dict[str, Any]:
        self._assert_legacy_only_backend(operation="Ruční WIP checkpoint")
        with self.profile_operation() as service:
            self.development_semaphore.assert_owner(self.active_profile_id)
            result = service.checkpoint(**kwargs)
        if result.get("checkpoint_created"):
            return {**result, "work": self.work_review()}
        return result

    @staticmethod
    def _workspace_has_wip(status: dict[str, Any]) -> bool:
        return bool(
            status.get("dirty")
            or status.get("local_checkpoint_ahead")
            or status.get("local_checkpoint_preserved")
            or status.get("workspace_relation") == "diverged"
        )

    def _development_workspace_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for profile_id, profile in self.profiles.items():
            status = profile["service"].workspace.status()
            rows.append(
                {
                    "id": profile_id,
                    "label": str(profile.get("label") or profile_id),
                    "dirty": bool(status.get("dirty")),
                    "change_count": int(status.get("change_count") or 0),
                    "workspace_relation": str(status.get("workspace_relation") or "unknown"),
                    "local_checkpoint_ahead": bool(status.get("local_checkpoint_ahead")),
                    "local_checkpoint_preserved": bool(status.get("local_checkpoint_preserved")),
                    "local_commit_count": int(status.get("local_commit_count") or 0),
                    "source_pending_changes": int(status.get("source_pending_changes") or 0),
                    "head": str(status.get("head") or ""),
                    "prepared": bool(status.get("prepared")),
                    "ok": bool(status.get("ok")),
                    "has_remotes": bool(status.get("remotes")),
                    "has_wip": self._workspace_has_wip(status),
                }
            )
        return rows

    @staticmethod
    def _row_blocker(row: dict[str, Any]) -> str:
        label = str(row.get("label") or row.get("id") or "Neznámý profil")
        if row.get("dirty"):
            return f"{label} má {int(row.get('change_count') or 0)} necheckpointovaných změn."
        if row.get("local_checkpoint_ahead"):
            return f"{label} má lokální WIP checkpoint čekající na rozhodnutí."
        if row.get("local_checkpoint_preserved"):
            return f"{label} má zachovaný rozvětvený WIP checkpoint."
        if row.get("workspace_relation") == "diverged":
            return f"{label} je rozvětvený proti main."
        if not row.get("prepared") or not row.get("ok") or row.get("has_remotes"):
            return f"{label} nemá ověřený bezpečný workspace."
        return ""

    def _foreign_wip_blockers(self, owner_id: str) -> list[str]:
        blockers: list[str] = []
        for row in self._development_workspace_rows():
            if row["id"] == owner_id:
                continue
            blocker = self._row_blocker(row)
            if blocker:
                blockers.append(blocker)
        return blockers

    def _safe_to_release(self) -> bool:
        rows = self._development_workspace_rows()
        return bool(
            rows
            and all(not self._row_blocker(row) for row in rows)
            and all(int(row.get("source_pending_changes") or 0) == 0 for row in rows)
        )

    def development_status(self) -> dict[str, Any]:
        lease = self.development_semaphore.status()
        try:
            active_id = self.active_profile_id
            rows = self._development_workspace_rows()
        except (AppServerError, OSError, ValueError) as exc:
            return {
                **lease,
                "ok": False,
                "message": str(exc),
                "active_profile_id": "",
                "workspace_rows": [],
                "blockers": ["Stav profilových workspaces nelze bezpečně ověřit."],
                "can_acquire_profile": False,
                "can_acquire_terminal": False,
                "can_checkpoint": False,
                "can_deploy": False,
                "can_release": False,
            }
        owner_id = str(lease.get("owner_id") or "")
        blockers = self._foreign_wip_blockers(owner_id) if lease.get("active") else []
        lease_active = lease.get("active") is True and lease.get("ok") is True
        lease_running = lease_active and lease.get("mode") == "active"
        free = lease.get("ok") is True and not lease.get("active")
        any_profile_wip = any(row.get("has_wip") for row in rows)
        source_dirty = any(int(row.get("source_pending_changes") or 0) > 0 for row in rows)
        lazy = bool(self.active_lazy_workstream_id)
        public_active_id = self.work_profile_id
        active_label = (
            str((self.grouped_workstream_status().get("active") or {}).get("workstream_name") or public_active_id)
            if lazy
            else str(self.profiles[active_id].get("label") or active_id)
        )
        return {
            **lease,
            "active_profile_id": public_active_id,
            "active_profile_label": active_label,
            "workspace_rows": rows,
            "blockers": blockers,
            "can_acquire_profile": bool(
                not lazy
                and free
                and not source_dirty
                and not any(row.get("has_wip") for row in rows if row["id"] != active_id)
            ),
            "can_acquire_terminal": bool(not lazy and free and not any_profile_wip),
            "can_checkpoint": bool(not lazy and lease_running and owner_id == active_id),
            "can_deploy": bool(not lazy and lease_running and owner_id == active_id and not blockers),
            "can_pause": bool(not lazy and lease_running),
            "can_resume": bool(not lazy and lease_active and lease.get("mode") == "paused"),
            "can_release": bool(not lazy and lease_active and self._safe_to_release()),
        }

    def change_development_semaphore(
        self,
        *,
        operation: str,
        expected_revision: int,
        topic: str,
        confirmed: bool,
        project_id: str = "",
        handoff_path: str = "",
    ) -> dict[str, Any]:
        self._assert_legacy_only_backend(operation="Změna vývojového semaforu")
        clean_operation = str(operation or "").strip()
        if not self._operation_lock.acquire(blocking=False):
            raise SessionBusyError("Vývojový semafor nelze změnit během jiné profilové operace.")
        try:
            lease = self.development_semaphore.status()
            if lease.get("ok") is not True:
                raise AppServerError(str(lease.get("message") or "Vývojový semafor není ověřený."))
            active_id = self.active_profile_id
            active_profile = self.profiles[active_id]
            active_workspace = active_profile["service"].workspace.status()
            project_binding: dict[str, str] = {}
            if clean_operation in {"acquire_profile", "acquire_terminal"}:
                try:
                    projects = self.project_continuity.catalog()
                except ProjectContinuityError:
                    if self.state_path == DEFAULT_PROFILE_STATE_PATH:
                        raise
                    projects = ()
                if projects:
                    default_id = self.project_continuity.default_project_id(
                        str(active_profile.get("default_project_name") or "")
                    )
                    fallback_tvbcp = (
                        active_profile["service"].tvbcp_relative_path.as_posix()
                        if str(project_id or "").strip() == default_id
                        else ""
                    )
                    project_binding = self.project_continuity.resolve_binding(
                        project_id=project_id,
                        handoff_path=handoff_path,
                        fallback_tvbcp_path=fallback_tvbcp,
                    )
            if clean_operation == "acquire_profile":
                blockers = self._foreign_wip_blockers(active_id)
                if blockers or int(active_workspace.get("source_pending_changes") or 0) > 0:
                    raise AppServerError("Vývoj nelze převzít: " + " ".join(blockers or ["Hlavní repo má pracovní změny."]))
                self.development_semaphore.acquire(
                    owner_id=active_id,
                    owner_label=str(active_profile.get("label") or active_id),
                    workspace_label=f"Profil {str(active_profile.get('label') or active_id)}",
                    base_head=str(active_workspace.get("head") or ""),
                    topic=topic,
                    project_binding=project_binding,
                    expected_revision=expected_revision,
                    confirmed=confirmed,
                )
            elif clean_operation == "acquire_terminal":
                blockers = [self._row_blocker(row) for row in self._development_workspace_rows()]
                blockers = [item for item in blockers if item]
                if blockers:
                    raise AppServerError("Terminál nelze označit jako vlastníka: " + " ".join(blockers))
                self.development_semaphore.acquire(
                    owner_id=TERMINAL_OWNER_ID,
                    owner_label="Terminálový Adam",
                    workspace_label="Hlavní terminál / samostatný worktree",
                    base_head=str(active_workspace.get("source_head") or ""),
                    topic=topic,
                    project_binding=project_binding,
                    expected_revision=expected_revision,
                    confirmed=confirmed,
                )
            elif clean_operation in {"pause", "resume"}:
                owner_id = str(lease.get("owner_id") or "")
                self.development_semaphore.set_mode(
                    owner_id=owner_id,
                    mode="paused" if clean_operation == "pause" else "active",
                    expected_revision=expected_revision,
                    confirmed=confirmed,
                )
            elif clean_operation == "release":
                owner_id = str(lease.get("owner_id") or "")
                self.development_semaphore.release(
                    owner_id=owner_id,
                    expected_revision=expected_revision,
                    confirmed=confirmed,
                    safe_to_release=self._safe_to_release(),
                )
            else:
                raise AppServerError("Neznámá operace vývojového semaforu.")
            return self.development_status()
        finally:
            self._operation_lock.release()

    def assert_deployment_allowed(self, owner_id: str) -> None:
        self.development_semaphore.assert_owner(owner_id)
        blockers = self._foreign_wip_blockers(owner_id)
        if blockers:
            raise AppServerError("Nasazení blokuje cizí WIP: " + " ".join(blockers))

    def finish_deployment_lease(self, owner_id: str) -> str:
        lease = self.development_semaphore.status()
        if lease.get("ok") is not True or lease.get("owner_id") != owner_id:
            return "Vývojový semafor po nasazení zůstal beze změny."
        try:
            self.development_semaphore.release(
                owner_id=owner_id,
                expected_revision=int(lease.get("revision") or 0),
                confirmed=True,
                safe_to_release=self._safe_to_release(),
            )
        except AppServerError as exc:
            return f"Nasazení proběhlo, ale vývojový semafor zůstal uzamčený: {exc}"
        return "Vývojový semafor byl po nasazení uvolněný."

    def _profile_status_fields(self) -> dict[str, Any]:
        selection = self.grouped_workstream_status()
        return {
            "work_profile": self._active_work_profile(selection),
            "work_profiles": self._profile_rows(),
            "workstream_selection": selection,
            "workstream_capabilities": self._workstream_capabilities(),
        }

    @staticmethod
    def _has_uncertain_delivery(session: dict[str, Any]) -> bool:
        """Treat a later confirmed turn as the recovery boundary for older uncertainty."""
        for item in reversed(session.get("messages") or []):
            if not isinstance(item, dict):
                continue
            status = str(item.get("status") or "")
            if status == "completed":
                return False
            if status in {"pending", "delivery_unknown"} or item.get("recovery_required") is True:
                return True
        return False

    @staticmethod
    def _assert_workspace_can_leave(status: dict[str, Any]) -> None:
        if not status.get("prepared") or not status.get("ok") or status.get("remotes"):
            raise AppServerError("Současný workspace není v bezpečném stavu pro přepnutí profilu.")
        if status.get("dirty"):
            raise AppServerError("Profil nelze přepnout: současný workspace má necheckpointované změny.")
        if status.get("local_checkpoint_ahead"):
            raise AppServerError("Profil nelze přepnout: současný WIP checkpoint čeká na rozhodnutí.")
        if status.get("workspace_relation") == "diverged":
            raise AppServerError("Profil nelze přepnout: současný workspace se rozešel s main.")

    @staticmethod
    def _assert_target_workspace(status: dict[str, Any]) -> None:
        if not status.get("prepared") or not status.get("ok") or status.get("remotes"):
            raise AppServerError("Cílový workspace není v bezpečném stavu.")
        if status.get("dirty") or status.get("local_checkpoint_ahead"):
            raise AppServerError("Cílový profil obsahuje rozpracovanou práci a nelze jej automaticky aktivovat.")
        if status.get("workspace_relation") == "diverged":
            raise AppServerError("Cílový workspace se rozešel s main; přepnutí je zablokované.")

    def _assert_session_can_leave(self, session: dict[str, Any]) -> None:
        if session.get("turn_busy") or session.get("active_turn"):
            raise SessionBusyError("Profil nelze přepnout během aktivního tahu Adama.")
        if self._has_uncertain_delivery(session):
            raise SessionBusyError(
                "Profil nelze přepnout, dokud není vyřešené nejisté doručení."
            )

    def _prepare_profile_workspace_unlocked(
        self,
        service: HumanAdamService,
    ) -> dict[str, Any]:
        target_status = service.workspace.status()
        if int(target_status.get("source_pending_changes") or 0) > 0:
            raise AppServerError(
                "Zdrojový main má pracovní změny; nový profil nyní nelze bezpečně připravit."
            )
        if not target_status.get("prepared"):
            target_status = service.workspace.prepare()
        self._assert_target_workspace(target_status)
        if target_status.get("source_update_available"):
            target_status = service.workspace.sync_from_main(confirmed=True)
        self._assert_target_workspace(target_status)
        return target_status

    @staticmethod
    def _target_recovery_allowed(service: HumanAdamService) -> bool:
        target_session = service.hub.snapshot()
        return bool(
            not target_session.get("turn_busy")
            and not target_session.get("active_turn")
            and not HumanAdamProfileManager._has_uncertain_delivery(target_session)
        )

    def _switch_unlocked(self, target_id: str) -> dict[str, Any]:
        current_id = self.active_profile_id
        if target_id == current_id:
            return {**self.status(), "switched": False}
        current = self.profiles[current_id]["service"]
        target = self.profiles[target_id]["service"]
        self._assert_session_can_leave(current.hub.snapshot())
        self._assert_workspace_can_leave(current.workspace.status())
        self._assert_session_can_leave(target.hub.snapshot())
        self._prepare_profile_workspace_unlocked(target)

        target.connect(
            recover_unreachable_runtime=self._target_recovery_allowed(target)
        )
        try:
            current.hub.close()
            self._write_active_profile_id(target_id)
        except Exception:
            try:
                target.hub.close()
            finally:
                current.connect()
            raise
        with self._state_lock:
            self._active_profile_id = target_id
            self._state_error = ""
        return {**self.status(), "switched": True}

    def _grouped_workstream_row(self, workstream_id: str) -> dict[str, Any]:
        selection = self.grouped_workstream_status()
        row = next(
            (
                item
                for item in selection.get("workstreams") or []
                if isinstance(item, dict) and item.get("id") == workstream_id
            ),
            None,
        )
        if row is None:
            raise AppServerError("Požadovaný pracovní proud v katalogu neexistuje.")
        if row.get("available") is not True:
            raise AppServerError("Požadovaný pracovní proud zatím nelze bezpečně otevřít.")
        return row

    def _open_lazy_from_legacy_unlocked(
        self,
        *,
        workstream_id: str,
    ) -> dict[str, Any]:
        threads = self.workstream_threads
        if threads is None:
            raise AppServerError("Soukromé vlákno pracovního proudu není dostupné.")
        original_profile_id = self.active_profile_id
        if original_profile_id != self.default_profile_id:
            self._switch_unlocked(self.default_profile_id)
        shared = self.profiles[self.default_profile_id]["service"]
        self._assert_session_can_leave(shared.hub.snapshot())
        self._assert_workspace_can_leave(shared.workspace.status())
        self._prepare_profile_workspace_unlocked(shared)
        shared.connect(
            recover_unreachable_runtime=self._target_recovery_allowed(shared)
        )
        shared.hub.close()
        try:
            return threads.open(workstream_id=workstream_id, confirmed=True)
        except Exception as target_error:
            try:
                shared.connect(
                    recover_unreachable_runtime=self._target_recovery_allowed(shared)
                )
                if original_profile_id != self.default_profile_id:
                    self._switch_unlocked(original_profile_id)
            except Exception as rollback_error:
                raise AppServerError(
                    "Cílový proud se nepřipojil a původní legacy proud nelze obnovit."
                ) from rollback_error
            raise target_error

    def _restore_lazy_after_legacy_failure_unlocked(
        self,
        *,
        workstream_id: str,
    ) -> None:
        threads = self.workstream_threads
        if threads is None:
            raise AppServerError("Původní lazy proud nelze obnovit.")
        if self.active_profile_id != self.default_profile_id:
            self._switch_unlocked(self.default_profile_id)
        shared = self.profiles[self.default_profile_id]["service"]
        shared.hub.close()
        threads.open(workstream_id=workstream_id, confirmed=True)

    def _activate_legacy_from_lazy_unlocked(
        self,
        *,
        profile_id: str,
        previous_lazy_id: str,
    ) -> dict[str, Any]:
        threads = self.workstream_threads
        if threads is None:
            raise AppServerError("Soukromé vlákno pracovního proudu není dostupné.")
        if self.active_profile_id != self.default_profile_id:
            raise AppServerError(
                "Lazy proud nemá konzistentní vlastnictví sdíleného pracovního profilu."
            )
        threads.checkpoint_workstream_id()
        shared = self.profiles[self.default_profile_id]["service"]
        self._prepare_profile_workspace_unlocked(shared)
        target = self.profiles[profile_id]["service"]
        self._assert_session_can_leave(target.hub.snapshot())
        if profile_id != self.default_profile_id:
            self._prepare_profile_workspace_unlocked(target)
        threads.close_active(confirmed=True)
        try:
            if profile_id == self.default_profile_id:
                target.connect(
                    recover_unreachable_runtime=self._target_recovery_allowed(target)
                )
                return {**self.status(), "switched": True}
            return self._switch_unlocked(profile_id)
        except Exception as target_error:
            try:
                self._restore_lazy_after_legacy_failure_unlocked(
                    workstream_id=previous_lazy_id
                )
            except Exception as rollback_error:
                raise AppServerError(
                    "Legacy proud se nepřipojil a původní lazy proud nelze obnovit."
                ) from rollback_error
            raise target_error

    def activate_grouped_workstream(
        self,
        *,
        workstream_id: str,
        confirmed: bool,
    ) -> dict[str, Any]:
        """Atomically route one catalog selection across unified backends."""

        clean_id = str(workstream_id or "").strip()
        if not confirmed:
            raise AppServerError("Přepnutí pracovního proudu vyžaduje výslovné potvrzení.")
        if DEPLOYMENT_LOCK.locked():
            raise SessionBusyError("Pracovní proud nelze přepnout během auditu nebo nasazení.")
        if not self._operation_lock.acquire(blocking=False):
            raise SessionBusyError("Pracovní proud nelze přepnout během aktivní operace.")
        try:
            target = self._grouped_workstream_row(clean_id)
            previous = self.grouped_workstream_status().get("active") or {}
            previous_id = str(previous.get("workstream_id") or "")
            previous_lazy_id = (
                self.workstream_threads.active_workstream_id
                if self.workstream_threads is not None
                else ""
            )
            backend_binding = self.workstream_backends.binding(clean_id)
            if backend_binding.compatibility_adapter is not None:
                profile_id = backend_binding.profile_id
                if profile_id not in self.profiles:
                    raise AppServerError(
                        "Kompatibilní pracovní proud nemá platný původní profil."
                    )
                if previous_lazy_id:
                    self._activate_legacy_from_lazy_unlocked(
                        profile_id=profile_id,
                        previous_lazy_id=previous_lazy_id,
                    )
                else:
                    self._switch_unlocked(profile_id)
            else:
                threads = self.workstream_threads
                if threads is None:
                    raise AppServerError("Soukromé vlákno pracovního proudu není dostupné.")
                if previous_lazy_id:
                    if self.active_profile_id != self.default_profile_id:
                        raise AppServerError(
                            "Lazy proud nemá konzistentní vlastnictví sdíleného pracovního profilu."
                        )
                    threads.checkpoint_workstream_id()
                    shared = self.profiles[self.default_profile_id]["service"]
                    self._prepare_profile_workspace_unlocked(shared)
                    threads.open(workstream_id=clean_id, confirmed=True)
                else:
                    self._open_lazy_from_legacy_unlocked(workstream_id=clean_id)
            selection = self.grouped_workstream_status()
            return {
                **self.status(),
                "ok": True,
                "switched": clean_id != previous_id,
                "workstream": {
                    "id": target["id"],
                    "type": target["type"],
                    "name": target["name"],
                    "mode": target["mode"],
                    "backend": target["backend"],
                },
                "workstream_selection": selection,
            }
        finally:
            self._operation_lock.release()

    def switch(self, *, profile_id: str, confirmed: bool) -> dict[str, Any]:
        target_id = str(profile_id or "").strip()
        if not confirmed:
            raise AppServerError("Přepnutí pracovního profilu vyžaduje výslovné potvrzení.")
        if target_id not in self.profiles:
            raise AppServerError("Požadovaný pracovní profil neexistuje.")
        if DEPLOYMENT_LOCK.locked():
            raise SessionBusyError("Profil nelze přepnout během auditu nebo nasazení.")
        if not self._operation_lock.acquire(blocking=False):
            raise SessionBusyError("Profil nelze přepnout během aktivní operace.")
        try:
            return self._switch_unlocked(target_id)
        finally:
            self._operation_lock.release()

    def close(self) -> None:
        if self.workstream_threads is not None:
            self.workstream_threads.close()
        for profile in self.profiles.values():
            service = profile["service"]
            if service._hub is None:
                continue
            try:
                service._hub.close()
            except SessionBusyError:
                pass
        self.runtime.close()


def human_adam_profile_switch_action(
    payload: dict[str, Any],
    *,
    service: HumanAdamProfileManager,
) -> dict[str, Any]:
    try:
        workstream_id = str(payload.get("workstream_id") or "").strip()
        if workstream_id:
            return service.activate_grouped_workstream(
                workstream_id=workstream_id,
                confirmed=payload.get("confirmed") is True,
            )
        return service.switch(
            profile_id=str(payload.get("profile_id") or ""),
            confirmed=payload.get("confirmed") is True,
        )
    except (AppServerError, SessionHubError, OSError, ValueError) as exc:
        return {
            "ok": False,
            "status": "human_adam_profile_switch_failed",
            "message": str(exc),
        }


def human_adam_development_semaphore_status_action(
    *,
    service: HumanAdamProfileManager,
) -> dict[str, Any]:
    return service.development_status()


def human_adam_development_semaphore_action(
    payload: dict[str, Any],
    *,
    service: HumanAdamProfileManager,
) -> dict[str, Any]:
    try:
        return {
            "ok": True,
            **service.change_development_semaphore(
                operation=str(payload.get("operation") or ""),
                expected_revision=int(payload.get("expected_revision")),
                topic=str(payload.get("topic") or ""),
                confirmed=payload.get("confirmed") is True,
                project_id=str(payload.get("project_id") or ""),
                handoff_path=str(payload.get("handoff_path") or ""),
            ),
        }
    except (AppServerError, SessionHubError, OSError, TypeError, ValueError) as exc:
        return {
            "ok": False,
            "status": "human_adam_development_semaphore_failed",
            "message": str(exc),
            "development_semaphore": service.development_status(),
        }


def human_adam_project_continuity_action(
    *,
    service: HumanAdamProfileManager,
) -> dict[str, Any]:
    return service.project_continuity_status()


def human_adam_deployment_completion_status_action(
    *,
    service: HumanAdamProfileManager,
) -> dict[str, Any]:
    return service.deployment_completion_status()


def human_adam_deployment_completion_action(
    payload: dict[str, Any],
    *,
    service: HumanAdamProfileManager,
) -> dict[str, Any]:
    try:
        return service.finalize_deployment_completion(
            confirmation=str(payload.get("confirmation") or ""),
            next_step=str(payload.get("next_step") or ""),
        )
    except (AppServerError, ProjectContinuityError, OSError, TypeError, ValueError) as exc:
        return {
            "ok": False,
            "ready": False,
            "message": str(exc),
            "deployment_completion": service.deployment_completion_status(),
        }


def build_human_adam_profiles() -> HumanAdamProfileManager:
    runtime = LocalAppServerProcessController()
    human_service = HumanAdamService(
        runtime=runtime,
        state_path=DEFAULT_HUMAN_SESSION_PATH,
        deployment_receipt_path=DEFAULT_DEPLOYMENT_RECEIPT,
        deployment_diagnostic_path=DEFAULT_DEPLOYMENT_DIAGNOSTIC,
        deployment_failure_history_path=DEFAULT_DEPLOYMENT_FAILURE_HISTORY,
        work_profile_id="human_adam",
        context_anchor_path=DEFAULT_HUMAN_CONTEXT_ANCHOR_PATH,
        developer_instructions=HUMAN_ADAM_DEVELOPER_INSTRUCTIONS,
    )
    knihovna_workspace = HumanAdamWorkspaceManager(
        workspace_root=KNIHOVNA_PROFILE_ROOT / "workspace",
        metadata_path=KNIHOVNA_PROFILE_ROOT / "workspace_meta.json",
    )
    knihovna_service = HumanAdamService(
        runtime=runtime,
        workspace=knihovna_workspace,
        state_path=PRIVATE_COMMUNICATION_ROOT / "knihovna_session.json",
        deployment_receipt_path=PRIVATE_COMMUNICATION_ROOT / "knihovna_deployment_receipt.json",
        deployment_diagnostic_path=PRIVATE_COMMUNICATION_ROOT / "knihovna_deployment_diagnostic.json",
        deployment_failure_history_path=PRIVATE_COMMUNICATION_ROOT / "knihovna_deployment_failures.json",
        work_profile_id="knihovna",
        context_anchor_path=KNIHOVNA_CONTEXT_ANCHOR_PATH,
        developer_instructions=KNIHOVNA_DEVELOPER_INSTRUCTIONS,
        tvbcp_relative_path=KNIHOVNA_TVBCP_RELATIVE_PATH,
        tvbcp_title="Knihovna v Cockpitu",
    )
    workstream_memory = WorkstreamMemoryRegistry()

    def lazy_workstream_hub(
        record: CanonicalWorkstream,
        state_path: Path,
    ) -> CanonicalSessionHub:
        memory_binding = workstream_memory.binding(record.workstream_id)
        project_prefix = Path(human_service.workspace.project_dir_name)
        handoff_path = (project_prefix / memory_binding.handoff_relative_path).as_posix()
        tvbcp_path = (project_prefix / memory_binding.tvbcp_relative_path).as_posix()
        return human_service.detached_session_hub(
            state_path=state_path,
            workspace=human_service.workspace.workspace_root,
            developer_instructions=(
                HUMAN_ADAM_DEVELOPER_INSTRUCTIONS
                + " Lazy pracovni proud bezi z korene izolovane kopie repozitare PythonMF; "
                + "projektova pamet Samantha je proto pod Samantha_Agent/memory/. Aktivni "
                + "kanonicky pracovni proud: "
                + record.name
                + " ("
                + record.workstream_id
                + "). Kanonicky handoff: "
                + handoff_path
                + ". Kanonicky TVBCP: "
                + tvbcp_path
                + ". Tyto dokumenty primo nemen bez Milova vyslovneho pokynu; bezny "
                + "potvrzeny checkpoint je aktualizuje transakcne."
            ),
        )

    workstream_threads = WorkstreamThreadRegistry(
        state_root=PRIVATE_WORKSTREAM_THREAD_ROOT,
        hub_factory=lazy_workstream_hub,
        workspace_status=human_service.workspace.status,
        reserved_workstream_ids={
            "layer-human-adam-development",
            "project-knowledge-library",
        },
    )
    return HumanAdamProfileManager(
        profiles={
            "human_adam": {
                "label": "Human–Adam",
                "description": "Vývoj pracovního rozhraní Human–Adam",
                "default_project_name": "App-server rozhrani / novy Adam",
                "workstream": {
                    "id": "layer-human-adam-development",
                    "type": "Layer",
                    "name": "Human–Adam / vývojové prostředí",
                    "handoff": "memory/handoffs/human_adam_layer_workstream_start_2026_07_20.md",
                    "tvbcp": "memory/tvbcp/architektura_komunikace_samantha.txt",
                },
                "service": human_service,
            },
            "knihovna": {
                "label": "Knihovna",
                "description": "Články, přílohy a práce s Knihovnou v Cockpitu",
                "default_project_name": "Znalostni databaze / Knihovna clanku / Knowledge inbox",
                "workstream": {
                    "id": "project-knowledge-library",
                    "type": "Project",
                    "name": "Knihovna",
                    "handoff": "memory/handoffs/knowledge_library_article_editing_2026_07_16.md",
                    "tvbcp": "memory/tvbcp/knihovna_cockpit.txt",
                },
                "service": knihovna_service,
            },
        },
        default_profile_id="human_adam",
        runtime=runtime,
        workstream_threads=workstream_threads,
        workstream_memory=workstream_memory,
    )


HUMAN_ADAM = build_human_adam_profiles()
atexit.register(HUMAN_ADAM.close)
