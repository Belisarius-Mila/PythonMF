"""Fail-closed work-profile routing for the Human–Adam interface."""

from __future__ import annotations

import atexit
import json
import re
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
from app.communication.human_adam_service import (
    DEVELOPMENT_CONTROL_DEVELOPER_INSTRUCTIONS,
    HUMAN_ADAM_DEVELOPER_INSTRUCTIONS,
    HumanAdamService,
)
from app.communication.human_adam_workspace import (
    HUMAN_ADAM_SANDBOX_POLICY,
    HUMAN_ADAM_WORKSPACE_DEVELOPER_INSTRUCTIONS,
    HumanAdamWorkspaceManager,
)
from app.communication.human_adam_workstream_backends import (
    CompatibilityWorkstreamAdapter,
    WorkstreamBackendRegistry,
)
from app.communication.human_adam_workstream_binding import (
    CanonicalWorkstreamBinding,
    canonical_workstream_binding,
)
from app.communication.human_adam_workstream_catalog import CanonicalWorkstream
from app.communication.human_adam_workstream_memory import WorkstreamMemoryRegistry
from app.communication.human_adam_workstream_selection import GroupedWorkstreamSelection
from app.communication.human_adam_workstream_threads import WorkstreamThreadRegistry
from app.communication.human_adam_turn_completion import (
    ParsedTurnCompletion,
    TurnCompletionMetadata,
    automatic_completion_instruction,
    parse_turn_completion,
)
from app.communication.human_adam_operations import (
    HumanAdamOperationError,
    ParsedHumanAdamOperation,
    automatic_operation_instruction,
    execute_human_adam_operation,
    parse_human_adam_operation,
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
    load_completed_simple_main_deployment,
    load_recent_simple_main_deployment,
    load_simple_main_deployment_receipt,
    prepare_simple_main_deployment as prepare_clean_main_deployment,
    verify_simple_main_deployment as verify_clean_main_deployment,
)
from app.file_persistence import atomic_write_json
from app.project_continuity import ProjectContinuityError, ProjectContinuityService


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRIVATE_COMMUNICATION_ROOT = PROJECT_ROOT / "data" / "private" / "communication"
PRIVATE_PROFILE_ROOT = PROJECT_ROOT / "data" / "private" / "human_adam_profiles"
PRIVATE_WORKSTREAM_THREAD_ROOT = PRIVATE_COMMUNICATION_ROOT / "workstreams"
DEFAULT_PROFILE_STATE_PATH = PRIVATE_COMMUNICATION_ROOT / "human_adam_active_profile.json"
DEFAULT_DEVELOPMENT_SEMAPHORE_PATH = PRIVATE_COMMUNICATION_ROOT / "development_semaphore.json"
DEFAULT_HUMAN_SESSION_PATH = PRIVATE_COMMUNICATION_ROOT / "canonical_session.json"
DEFAULT_HUMAN_CONTEXT_ANCHOR_PATH = PRIVATE_COMMUNICATION_ROOT / "human_adam_context_anchor.json"
KNIHOVNA_PROFILE_ROOT = PRIVATE_PROFILE_ROOT / "knihovna"
KNIHOVNA_CONTEXT_ANCHOR_PATH = PRIVATE_COMMUNICATION_ROOT / "knihovna_context_anchor.json"
KNIHOVNA_TVBCP_RELATIVE_PATH = Path("memory/tvbcp/knihovna_cockpit.txt")
KNIHOVNA_WORKSTREAM_ID = "project-knowledge-library"
KNIHOVNA_LIVE_ARCHIVE_ROOT = PROJECT_ROOT / "data" / "private" / "article_archive"
KNIHOVNA_PRIVATE_CONFIRMATION_CATEGORIES = (
    "delete",
    "bulk_change",
    "external_send",
    "system_change",
)
KNIHOVNA_SANDBOX_POLICY = {
    **HUMAN_ADAM_SANDBOX_POLICY,
    "writableRoots": [str(KNIHOVNA_LIVE_ARCHIVE_ROOT)],
}
PROFILE_ID_RE = re.compile(r"[a-z][a-z0-9_-]{1,31}")
LEGACY_PROFILE_STATE_SCHEMA = 1
WORKSTREAM_STATE_SCHEMA = 2
ONE_TURN_WRITABLE_LAZY_WORKSTREAM_IDS = frozenset(
    {"project-mmtx", "project-family-calendar"}
)

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
        "nikdy automaticky nevypisuj do Gitu, logu, TVBCP ani odpovedi; zobraz jen "
        "nejmensi rozsah, ktery si Mila vyslovne vyzada. Knihovna ma uzkou vyjimku z "
        "obecneho zakazu prace mimo izolovany workspace: kanonicky zivy archiv je "
        f"{KNIHOVNA_LIVE_ARCHIVE_ROOT}. Tento koren smi byt primo cten pro diagnostiku "
        "a na Miluv jasny pokyn smi byt pres API app.article_archive upravena jedna "
        "konkretni karta. Pro bezne cteni a jednu nedestruktivni upravu nazvu, textu, "
        "kategorie, tagu nebo zdrojovych poznamek nevyzaduj dalsi potvrzeni a nepouzivej "
        "tlacitko Zahajit vyvoj. Hodnota writable v DEVELOPMENT_CONTROL se tyka kodu, "
        "izolovaneho workspace a Gitu; vyjimku z ni tvori pouze explicitni "
        "private_archive_access ve stejnem bloku. Jedna logicka karta muze zahrnovat "
        "jeji text, metadata a registr. Vice karet nebo mechanicka zmena celeho vyberu "
        "je hromadna zmena. Mazani nebo odebirani, hromadna zmena, odeslani ven a "
        "systemovy zasah vyzaduji samostatne Milovo potvrzeni; pouzij existujici presnou "
        "potvrzovaci branu prislusneho API. Nikdy tyto operace neobchazej primym zapisem "
        "nebo obecnym shellovym prikazem. Mimo tento jediny koren zustava vse mimo "
        "workspace bez zapisu, sit zustava zakazana a Git, checkpoint, commit, push i "
        "nasazeni dale obsluhuje pouze Cockpit. Pri cteni nebo uprave nevypisuj do "
        "terminalu cely soukromy fulltext; vrat jen redigovany technicky vysledek. "
        "V bezne odpovedi uvadej jen samotny nazev souboru, pripadne nejkratsi nutnou "
        "relativni cestu pri shodnych nazvech."
    )
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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
        self._active_profile_id, self._active_workstream_id = self._load_active_state()

    def _load_active_state(self) -> tuple[str, str]:
        default_workstream_id = self.workstream_backends.compatibility_workstream_id(
            self.default_profile_id
        )
        if not self.state_path.exists():
            return self.default_profile_id, default_workstream_id
        try:
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._state_error = "Stav pracovního proudu nelze bezpečně načíst."
            return "", ""
        if not isinstance(raw, dict):
            self._state_error = "Stav pracovního proudu má neznámé schéma."
            return "", ""
        schema = raw.get("schema_version")
        if schema == LEGACY_PROFILE_STATE_SCHEMA:
            profile_id = str(raw.get("active_profile_id") or "").strip()
            if profile_id not in self.profiles:
                self._state_error = "Stav odkazuje na neznámý pracovní profil."
                return "", ""
            return (
                profile_id,
                self.workstream_backends.compatibility_workstream_id(profile_id),
            )
        if schema != WORKSTREAM_STATE_SCHEMA:
            self._state_error = "Stav pracovního proudu má neznámé schéma."
            return "", ""
        workstream_id = str(raw.get("active_workstream_id") or "").strip()
        try:
            binding = self.workstream_backends.binding(workstream_id)
        except AppServerError:
            self._state_error = "Stav odkazuje na neznámý pracovní proud."
            return "", ""
        adapter = binding.compatibility_adapter
        if adapter is not None:
            return adapter.profile_id, binding.record.workstream_id
        if self.workstream_threads is None:
            self._state_error = "Lazy aktivní proud nemá dostupný private backend."
            return "", ""
        try:
            self.workstream_threads.restore_active(
                workstream_id=binding.record.workstream_id
            )
        except (AppServerError, OSError, ValueError) as exc:
            self._state_error = str(exc)
            return "", ""
        return self.default_profile_id, binding.record.workstream_id

    def _write_active_workstream_id(self, workstream_id: str) -> str:
        binding = self.workstream_backends.binding(workstream_id)
        canonical_id = binding.record.workstream_id
        atomic_write_json(
            self.state_path,
            {
                "schema_version": WORKSTREAM_STATE_SCHEMA,
                "active_workstream_id": canonical_id,
                "updated_at": _now(),
            },
            ensure_ascii=False,
            indent=2,
        )
        return canonical_id

    def _set_active_workstream_id_unlocked(self, workstream_id: str) -> None:
        canonical_id = self._write_active_workstream_id(workstream_id)
        with self._state_lock:
            self._active_workstream_id = canonical_id
            self._state_error = ""

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
        with self._state_lock:
            if self._state_error or not self._active_workstream_id:
                raise AppServerError(
                    self._state_error or "Aktivní pracovní proud není známý."
                )
            workstream_id = self._active_workstream_id
        binding = self.workstream_backends.binding(workstream_id)
        adapter = binding.compatibility_adapter
        if adapter is not None:
            if self.active_lazy_workstream_id or self.active_profile_id != adapter.profile_id:
                raise AppServerError("Aktivní kompatibilní proud nemá konzistentní backend.")
        elif self.active_lazy_workstream_id != workstream_id:
            raise AppServerError("Aktivní lazy proud nemá konzistentní backend.")
        return workstream_id

    @property
    def workspace(self) -> HumanAdamWorkspaceManager:
        return self.active_service.workspace

    @property
    def hub(self):
        return self.active_service.hub

    @property
    def work_profile_id(self) -> str:
        return self.active_service.work_profile_id

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
            self._assert_one_turn_writable_lazy_workstream(workstream_id)
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
            "workstream": {
                "id": binding.workstream_id,
                "type": binding.workstream_type,
                "name": binding.name,
            },
        }

    def _workstream_capabilities(self) -> dict[str, Any]:
        lazy_id = self.active_lazy_workstream_id
        lazy = bool(lazy_id)
        writable_pilot = lazy_id == "project-mmtx"
        one_turn_write = not lazy or lazy_id in ONE_TURN_WRITABLE_LAZY_WORKSTREAM_IDS
        direct_private_archive = self.active_workstream_id == KNIHOVNA_WORKSTREAM_ID
        return {
            "conversation": True,
            "context_anchor": True,
            "tvbcp": True,
            "development": one_turn_write,
            "checkpoint": one_turn_write,
            "deployment": not lazy,
            "lazy_backend": lazy,
            "writable_pilot": writable_pilot,
            "one_turn_write": one_turn_write,
            "write_authorization": "one_turn" if one_turn_write else "read_only",
            "private_archive_direct": direct_private_archive,
            "private_archive_read": direct_private_archive,
            "private_archive_single_edit": direct_private_archive,
            "private_archive_confirmation_required": (
                list(KNIHOVNA_PRIVATE_CONFIRMATION_CATEGORIES)
                if direct_private_archive
                else []
            ),
        }

    def _assert_one_turn_writable_lazy_workstream(self, workstream_id: str) -> None:
        clean_id = str(workstream_id or "").strip()
        if clean_id not in ONE_TURN_WRITABLE_LAZY_WORKSTREAM_IDS:
            raise AppServerError(
                "Tento lazy pracovní proud zůstává read-only; jednorázový vývoj "
                "je povolen jen pro výslovně schválené pracovní proudy."
            )

    def _assert_legacy_only_backend(self, *, operation: str) -> None:
        if self.active_lazy_workstream_id:
            raise AppServerError(
                f"{operation} lazy pracovního proudu zatím není povolené."
            )

    def status(self) -> dict[str, Any]:
        try:
            selection = self.grouped_workstream_status()
            active = selection.get("active") or {}
            active_workstream_id = str(active.get("workstream_id") or "")
            payload = self.active_service.status()
            last_deployment = load_completed_simple_main_deployment(
                self.simple_main_deployment_receipt_path,
                expected_workstream_id=active_workstream_id,
            )
            recent_deployment = load_recent_simple_main_deployment(
                self.simple_main_deployment_receipt_path,
                expected_workstream_id=active_workstream_id,
            )
            return {
                **payload,
                "workstream_selection": selection,
                "workstream_capabilities": self._workstream_capabilities(),
                "development_semaphore": self.development_status(),
                "last_simple_main_deployment": last_deployment,
                "recent_simple_main_deployment": recent_deployment,
            }
        except (AppServerError, SessionHubError, OSError, ValueError) as exc:
            return {
                "ok": False,
                "status": "human_adam_profile_status_failed",
                "message": str(exc),
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
        with self.profile_operation() as service:
            workspace_synced = self._sync_clean_active_workspace_from_main(
                service=service,
            )
            session = service.hub.snapshot()
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
            **self._workstream_status_fields(),
            "workspace_synced": workspace_synced,
        }

    def send(self, **kwargs: Any) -> dict[str, Any]:
        with self.profile_operation() as service:
            workspace_synced = self._sync_clean_active_workspace_from_main(
                service=service,
            )
            active_id = self.work_profile_id
            lazy_id = self.active_lazy_workstream_id
            write_intent = kwargs.pop("write_intent", False) is True
            writable = False
            state = "not_requested"
            control_source = "one_turn_direct_main_authorization"
            control_owner = "none"
            integration_deferred = False
            if write_intent:
                integration_deferred = self._assert_one_turn_write_ready(
                    service=service,
                    active_id=active_id,
                    lazy_id=lazy_id,
                )
                writable = True
                state = (
                    "authorized_isolated_source_wip"
                    if integration_deferred
                    else "authorized_once"
                )
                if integration_deferred:
                    control_source = "one_turn_isolated_source_wip_authorization"
                control_owner = active_id
            elif lazy_id and lazy_id not in ONE_TURN_WRITABLE_LAZY_WORKSTREAM_IDS:
                control_source = "lazy_read_only_policy"
                state = "read_only"
            control_lines = [
                "[DEVELOPMENT_CONTROL]",
                f"source={control_source}",
                f"profile_id={active_id}",
                f"lease_state={state}",
                f"lease_owner_id={control_owner}",
                f"writable={'true' if writable else 'false'}",
                f"integration_deferred={'true' if integration_deferred else 'false'}",
            ]
            if self.active_workstream_id == KNIHOVNA_WORKSTREAM_ID:
                control_lines.extend(
                    (
                        f"workspace_writable={'true' if writable else 'false'}",
                        "private_archive_access=read_diagnose_and_explicit_single_edit",
                        f"private_archive_root={KNIHOVNA_LIVE_ARCHIVE_ROOT}",
                        "private_archive_confirmation_required="
                        + ",".join(KNIHOVNA_PRIVATE_CONFIRMATION_CATEGORIES),
                        "rule=When workspace_writable=false, do not change workspace files "
                        "or Git. The only write exception is one explicitly requested, "
                        "non-destructive card edit under private_archive_root through "
                        "app.article_archive. Never bypass confirmation gates.",
                    )
                )
            else:
                if integration_deferred:
                    control_lines.extend(
                        (
                            "rule=You may edit and test only inside the isolated workspace.",
                            "rule=The source main has terminal WIP. Do not run git add, "
                            "commit, checkpoint, push, merge, rebase, reset or deployment. "
                            "Leave successful changes uncommitted for a later conflict audit.",
                        )
                    )
                else:
                    control_lines.append(
                        "rule=When writable=false, remain read-only and do not change files or Git."
                    )
            control_lines.append("[/DEVELOPMENT_CONTROL]")
            development_control_block = "\n".join(control_lines)
            completion_instruction = automatic_completion_instruction(
                writable=writable and not integration_deferred
            )
            if completion_instruction:
                development_control_block = (
                    development_control_block + "\n\n" + completion_instruction
                )
            operation_instruction = automatic_operation_instruction(
                workstream_id=self.active_workstream_id,
            )
            if operation_instruction:
                development_control_block = (
                    development_control_block + "\n\n" + operation_instruction
                )
            result = service.send(
                **kwargs,
                development_control_block=development_control_block,
            )
            completed = self._complete_successful_turn(
                service=service,
                active_id=active_id,
                writable=writable,
                integration_deferred=integration_deferred,
                result=result,
            )
            return {
                **completed,
                "workspace_synced": workspace_synced,
            }

    def _sync_clean_active_workspace_from_main(
        self,
        *,
        service: HumanAdamService,
    ) -> bool:
        """Fast-forward one clean idle active workspace before connect or send."""

        workspace = service.workspace.status()
        if not workspace.get("source_update_available"):
            return False
        session = service.hub.snapshot()
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
                "Zdrojový main má pracovní změny; aktivní profil nyní nelze "
                "bezpečně aktualizovat."
            )
        self._assert_target_workspace(workspace)
        if workspace.get("workspace_relation") != "source_ahead":
            raise AppServerError(
                "Aktivní workspace není v jednoznačném stavu pro automatickou "
                "synchronizaci."
            )
        workspace = service.workspace.sync_from_main(confirmed=True)
        self._assert_target_workspace(workspace)
        if (
            workspace.get("source_update_available")
            or workspace.get("workspace_relation") != "aligned"
        ):
            raise AppServerError(
                "Aktivní workspace se nepodařilo bezpečně synchronizovat s main."
            )
        return True

    def _assert_one_turn_write_ready(
        self,
        *,
        service: HumanAdamService,
        active_id: str,
        lazy_id: str,
    ) -> bool:
        if lazy_id:
            self._assert_one_turn_writable_lazy_workstream(lazy_id)
            if self.workstream_memory is None:
                raise AppServerError(
                    "Pracovní proud nemá kanonickou paměť pro bezpečný checkpoint."
                )
            memory_binding = self.workstream_memory.binding(lazy_id)
            if memory_binding.workstream_id != self.active_workstream_id:
                raise AppServerError(
                    "Aktivní pracovní proud nemá konzistentní kanonickou vazbu."
                )
        else:
            binding = self.workstream_backends.binding(self.active_workstream_id)
            adapter = binding.compatibility_adapter
            if adapter is None or adapter.profile_id != active_id:
                raise AppServerError(
                    "Aktivní pracovní proud nemá konzistentní direct-main adaptér."
                )

        session = service.hub.snapshot()
        if not session.get("connected"):
            raise AppServerError("Nejdřív výslovně připoj Human–Adam.")
        if session.get("turn_busy") or session.get("active_turn"):
            raise SessionBusyError("Vývoj nelze zahájit během aktivního tahu Adama.")
        if self._has_uncertain_delivery(session):
            raise SessionBusyError(
                "Vývoj nelze zahájit, dokud není vyřešené nejisté doručení."
            )

        active_workspace = service.workspace.status()
        self._assert_target_workspace(active_workspace)
        if int(active_workspace.get("source_pending_changes") or 0) > 0:
            if active_id != "human_adam" or lazy_id:
                raise AppServerError(
                    "Main má pracovní změny; jednorázový vývoj zůstává uzamčený."
                )
            self._assert_isolated_source_wip_write_ready(
                active_workspace=active_workspace,
            )
            return True

        self._sync_clean_source_ahead_workspaces_for_one_turn()

        active_workspace = service.workspace.status()
        self._assert_target_workspace(active_workspace)
        if int(active_workspace.get("source_pending_changes") or 0) > 0:
            raise AppServerError(
                "Main má pracovní změny; jednorázový vývoj zůstává uzamčený."
            )
        if active_workspace.get("workspace_relation") != "aligned":
            raise AppServerError(
                "Aktivní workspace není synchronní s main; před vývojem jej bezpečně synchronizuj."
            )

        for row in self._development_workspace_rows():
            blocker = self._row_blocker(row)
            if blocker:
                raise AppServerError("Jednorázový vývoj blokuje workspace: " + blocker)
            if int(row.get("source_pending_changes") or 0) > 0:
                raise AppServerError(
                    f"Main má pracovní změny viditelné z workspace {row['label']}; vývoj zůstává uzamčený."
                )
            if row.get("workspace_relation") != "aligned":
                raise AppServerError(
                    f"Workspace {row['label']} není synchronní s main; vývoj zůstává uzamčený."
                )
        return False

    def _assert_isolated_source_wip_write_ready(
        self,
        *,
        active_workspace: dict[str, Any],
    ) -> None:
        """Allow only isolated edits while terminal WIP keeps integration locked."""

        if active_workspace.get("workspace_relation") != "aligned":
            raise AppServerError(
                "Main má pracovní změny a aktivní workspace není zarovnaný s "
                "posledním commitem; izolovaný vývoj zůstává uzamčený."
            )
        for row in self._development_workspace_rows():
            blocker = self._row_blocker(row)
            if blocker:
                raise AppServerError("Izolovaný vývoj blokuje workspace: " + blocker)
            if row.get("workspace_relation") != "aligned":
                raise AppServerError(
                    f"Workspace {row['label']} není zarovnaný s posledním commitem; "
                    "izolovaný vývoj zůstává uzamčený."
                )

    def _sync_clean_source_ahead_workspaces_for_one_turn(self) -> None:
        rows = self._development_workspace_rows()
        for row in rows:
            blocker = self._row_blocker(row)
            if blocker:
                raise AppServerError("Jednorázový vývoj blokuje workspace: " + blocker)
            if int(row.get("source_pending_changes") or 0) > 0:
                raise AppServerError(
                    f"Main má pracovní změny viditelné z workspace {row['label']}; "
                    "vývoj zůstává uzamčený."
                )
            if row.get("workspace_relation") not in {"aligned", "source_ahead"}:
                raise AppServerError(
                    f"Workspace {row['label']} není v bezpečném stavu pro "
                    "jednorázový vývoj."
                )

        for row in rows:
            if row.get("workspace_relation") != "source_ahead":
                continue
            profile = self.profiles[str(row["id"])]
            profile_service = profile["service"]
            session = profile_service.hub.snapshot()
            if session.get("turn_busy") or session.get("active_turn"):
                raise SessionBusyError(
                    f"Workspace {row['label']} nelze před vývojem synchronizovat "
                    "během aktivního tahu Adama."
                )
            if self._has_uncertain_delivery(session):
                raise SessionBusyError(
                    f"Workspace {row['label']} nelze před vývojem synchronizovat, "
                    "dokud není vyřešené nejisté doručení."
                )

            workspace = profile_service.workspace.status()
            self._assert_target_workspace(workspace)
            if int(workspace.get("source_pending_changes") or 0) > 0:
                raise AppServerError(
                    f"Main má pracovní změny viditelné z workspace {row['label']}; "
                    "vývoj zůstává uzamčený."
                )
            relation = str(workspace.get("workspace_relation") or "unknown")
            if relation == "aligned":
                continue
            if relation != "source_ahead":
                raise AppServerError(
                    f"Workspace {row['label']} se během kontroly změnil; "
                    "vývoj zůstává uzamčený."
                )
            workspace = profile_service.workspace.sync_from_main(confirmed=True)
            self._assert_target_workspace(workspace)
            if workspace.get("workspace_relation") != "aligned":
                raise AppServerError(
                    f"Workspace {row['label']} se nepodařilo bezpečně "
                    "synchronizovat s main."
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
            self._assert_one_turn_writable_lazy_workstream(lazy_id)
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
        integration_deferred: bool = False,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """Finish a delivered writable turn, or leave its work visibly recoverable."""

        if result.get("duplicate_prevented") is True:
            entry = result.get("entry")
            if isinstance(entry, dict):
                operation = parse_human_adam_operation(entry.get("answer"))
                if operation.state != "absent":
                    answer = self._completion_answer(
                        operation.visible_answer,
                        "Opakovaná zpráva byla rozpoznána; provozní operace se znovu nespustila.",
                    )
                    self._store_completed_answer(service=service, entry=entry, answer=answer)
                    return {
                        **result,
                        "entry": entry,
                        "automatic_operation": {
                            "state": "duplicate_prevented",
                            "attempted": False,
                        },
                        "automatic_completion": {
                            "state": "duplicate_prevented",
                            "attempted": False,
                        },
                    }
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
                "automatic_operation": {"state": "unavailable", "attempted": False},
                "automatic_completion": {"state": "unavailable", "attempted": False},
            }
        operation: ParsedHumanAdamOperation = parse_human_adam_operation(
            entry.get("answer")
        )
        workspace = service.workspace.status()
        dirty = bool(workspace.get("dirty"))
        if operation.state != "absent":
            if dirty:
                note = (
                    "Provozní operace se nespustila: workspace obsahuje pracovní změny. "
                    "Změny zůstaly viditelné a bez checkpointu."
                )
                answer = self._completion_answer(operation.visible_answer, note)
                answer_persisted = self._store_completed_answer(
                    service=service,
                    entry=entry,
                    answer=answer,
                )
                return {
                    **result,
                    "entry": entry,
                    "automatic_operation": {
                        "state": "blocked_dirty",
                        "attempted": False,
                        "answer_persisted": answer_persisted,
                    },
                    "automatic_completion": {
                        "state": "metadata_missing",
                        "attempted": False,
                    },
                }
            if operation.state != "valid" or operation.request is None:
                note = (
                    "Provozní operace se nespustila: "
                    + (operation.error or "chybí platná provozní účtenka.")
                )
                answer = self._completion_answer(operation.visible_answer, note)
                answer_persisted = self._store_completed_answer(
                    service=service,
                    entry=entry,
                    answer=answer,
                )
                return {
                    **result,
                    "entry": entry,
                    "automatic_operation": {
                        "state": "invalid",
                        "attempted": False,
                        "answer_persisted": answer_persisted,
                    },
                    "automatic_completion": {
                        "state": "not_needed",
                        "attempted": False,
                    },
                }
            try:
                operation_document = execute_human_adam_operation(
                    operation.request,
                    workstream_id=self.active_workstream_id,
                )
                operation_state = "completed"
            except (HumanAdamOperationError, OSError, TypeError, ValueError):
                operation_document = {"status": "failed", "redacted": True}
                operation_state = "failed"
            safe_json = json.dumps(
                operation_document,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            note = (
                "Provozní operace hlavního backendu:\n\n"
                f"```json\n{safe_json}\n```"
            )
            answer = self._completion_answer(operation.visible_answer, note)
            answer_persisted = self._store_completed_answer(
                service=service,
                entry=entry,
                answer=answer,
            )
            return {
                **result,
                "entry": entry,
                "automatic_operation": {
                    "state": operation_state,
                    "attempted": True,
                    "operation_id": operation.request.operation_id,
                    "result": operation_document,
                    "answer_persisted": answer_persisted,
                },
                "automatic_completion": {
                    "state": "not_needed",
                    "attempted": False,
                },
            }
        parsed: ParsedTurnCompletion = parse_turn_completion(entry.get("answer"))
        if not dirty and parsed.state == "absent":
            return {
                **result,
                "automatic_operation": {"state": "not_needed", "attempted": False},
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

        if integration_deferred:
            note = (
                "Změny a testy zůstaly bezpečně v izolovaném workspace bez commitu. "
                "Zdrojový main obsahuje terminálový WIP; checkpoint, push a začlenění "
                "čekají na čistý main a samostatný audit konfliktů."
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
                    "state": "deferred_source_wip",
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
        service = self.active_service
        lazy_id = self.active_lazy_workstream_id
        if not lazy_id:
            return service.tvbcp()
        if self.workstream_memory is None:
            raise AppServerError("Lazy pracovní proud nemá kanonickou paměťovou vazbu.")
        binding = self.workstream_memory.binding(lazy_id)
        return service.tvbcp(
            initial_content=self.workstream_memory.initial_tvbcp(binding),
        )

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
            active_workstream_id = self.active_workstream_id
            deployment_summary = (
                load_completed_simple_main_deployment(
                    self.simple_main_deployment_receipt_path,
                    expected_workstream_id=active_workstream_id,
                )
                if include_profile_receipt
                else None
            )
            audit = self.project_continuity.audit(
                binding=binding,
                workspace_root=self.active_service.workspace.project_root,
                workspace_review=self.active_service.workspace.review(),
                context_anchor=self.active_service.context_anchor(include_content=False),
                deployment_summary=deployment_summary,
                expected_workstream_id=active_workstream_id,
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
        return {
            **lease,
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

    def _workstream_status_fields(self) -> dict[str, Any]:
        selection = self.grouped_workstream_status()
        return {
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

    def _switch_unlocked(
        self,
        target_id: str,
        *,
        persist_active_workstream: bool = True,
    ) -> dict[str, Any]:
        current_id = self.active_profile_id
        target_workstream_id = self.workstream_backends.compatibility_workstream_id(
            target_id
        )
        if target_id == current_id:
            if persist_active_workstream:
                self._set_active_workstream_id_unlocked(target_workstream_id)
                return {**self.status(), "switched": False}
            return {"ok": True, "switched": False}
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
            if persist_active_workstream:
                self._set_active_workstream_id_unlocked(target_workstream_id)
        except Exception:
            try:
                target.hub.close()
            finally:
                current.connect()
            raise
        with self._state_lock:
            self._active_profile_id = target_id
            self._state_error = ""
        if persist_active_workstream:
            return {**self.status(), "switched": True}
        return {"ok": True, "switched": True}

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
        shared = self.profiles[self.default_profile_id]["service"]
        try:
            if original_profile_id != self.default_profile_id:
                self._switch_unlocked(
                    self.default_profile_id,
                    persist_active_workstream=False,
                )
            self._assert_session_can_leave(shared.hub.snapshot())
            self._assert_workspace_can_leave(shared.workspace.status())
            self._prepare_profile_workspace_unlocked(shared)
            shared.connect(
                recover_unreachable_runtime=self._target_recovery_allowed(shared)
            )
            shared.hub.close()
            result = threads.open(workstream_id=workstream_id, confirmed=True)
            self._set_active_workstream_id_unlocked(workstream_id)
            return result
        except Exception as target_error:
            try:
                if threads.active_workstream_id == workstream_id:
                    threads.close_active(confirmed=True)
                if self.active_profile_id == self.default_profile_id:
                    shared.connect(
                        recover_unreachable_runtime=self._target_recovery_allowed(shared)
                    )
                if self.active_profile_id != original_profile_id:
                    self._switch_unlocked(
                        original_profile_id,
                        persist_active_workstream=False,
                    )
            except Exception as rollback_error:
                raise AppServerError(
                    "Cílový proud se nepřipojil a původní kompatibilní proud nelze obnovit."
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
            self._switch_unlocked(
                self.default_profile_id,
                persist_active_workstream=False,
            )
        shared = self.profiles[self.default_profile_id]["service"]
        shared.hub.close()
        threads.open(workstream_id=workstream_id, confirmed=True)
        self._set_active_workstream_id_unlocked(workstream_id)

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
                self._set_active_workstream_id_unlocked(
                    self.workstream_backends.compatibility_workstream_id(profile_id)
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
                    try:
                        threads.open(workstream_id=clean_id, confirmed=True)
                        self._set_active_workstream_id_unlocked(clean_id)
                    except Exception as target_error:
                        if (
                            previous_lazy_id != clean_id
                            and threads.active_workstream_id == clean_id
                        ):
                            try:
                                threads.open(
                                    workstream_id=previous_lazy_id,
                                    confirmed=True,
                                )
                            except Exception as rollback_error:
                                raise AppServerError(
                                    "Cílový lazy proud nelze uložit a původní proud nelze obnovit."
                                ) from rollback_error
                        raise target_error
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
        if self.active_lazy_workstream_id:
            return self.activate_grouped_workstream(
                workstream_id=self.workstream_backends.compatibility_workstream_id(
                    target_id
                ),
                confirmed=True,
            )
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
        if "profile_id" in payload:
            raise AppServerError(
                "Pole profile_id již není podporované; použij kanonické workstream_id."
            )
        workstream_id = str(payload.get("workstream_id") or "").strip()
        if not workstream_id:
            raise AppServerError(
                "Přepnutí pracovního proudu vyžaduje kanonické workstream_id."
            )
        return service.activate_grouped_workstream(
            workstream_id=workstream_id,
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


def build_human_adam_profiles() -> HumanAdamProfileManager:
    runtime = LocalAppServerProcessController()
    human_service = HumanAdamService(
        runtime=runtime,
        state_path=DEFAULT_HUMAN_SESSION_PATH,
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
        work_profile_id="knihovna",
        context_anchor_path=KNIHOVNA_CONTEXT_ANCHOR_PATH,
        developer_instructions=KNIHOVNA_DEVELOPER_INSTRUCTIONS,
        sandbox_policy=KNIHOVNA_SANDBOX_POLICY,
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
