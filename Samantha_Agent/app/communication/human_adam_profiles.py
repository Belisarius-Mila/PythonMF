"""Fail-closed work-profile routing for the Human–Adam interface."""

from __future__ import annotations

import atexit
import json
import re
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

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
from app.communication.local_runtime import LocalAppServerProcessController
from app.communication.session_hub import SessionBusyError, SessionHubError
from app.file_persistence import atomic_write_json
from app.project_continuity import ProjectContinuityError, ProjectContinuityService


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRIVATE_COMMUNICATION_ROOT = PROJECT_ROOT / "data" / "private" / "communication"
PRIVATE_PROFILE_ROOT = PROJECT_ROOT / "data" / "private" / "human_adam_profiles"
DEFAULT_PROFILE_STATE_PATH = PRIVATE_COMMUNICATION_ROOT / "human_adam_active_profile.json"
DEFAULT_DEVELOPMENT_SEMAPHORE_PATH = PRIVATE_COMMUNICATION_ROOT / "development_semaphore.json"
DEFAULT_HUMAN_SESSION_PATH = PRIVATE_COMMUNICATION_ROOT / "canonical_session.json"
DEFAULT_HUMAN_CONTEXT_ANCHOR_PATH = PRIVATE_COMMUNICATION_ROOT / "human_adam_context_anchor.json"
KNIHOVNA_PROFILE_ROOT = PRIVATE_PROFILE_ROOT / "knihovna"
KNIHOVNA_CONTEXT_ANCHOR_PATH = PRIVATE_COMMUNICATION_ROOT / "knihovna_context_anchor.json"
KNIHOVNA_TVBCP_RELATIVE_PATH = Path("memory/tvbcp/knihovna_cockpit.txt")
PROFILE_ID_RE = re.compile(r"[a-z][a-z0-9_-]{1,31}")
PROFILE_STATE_SCHEMA = 1

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


class HumanAdamProfileManager:
    """Route one visible UI to isolated, persistent work-profile bundles."""

    def __init__(
        self,
        *,
        profiles: dict[str, dict[str, Any]],
        default_profile_id: str,
        state_path: Path = DEFAULT_PROFILE_STATE_PATH,
        runtime: LocalAppServerProcessController | None = None,
        development_semaphore: DevelopmentSemaphore | None = None,
        project_continuity: ProjectContinuityService | None = None,
    ):
        if not profiles or default_profile_id not in profiles:
            raise ValueError("Pracovní profily Human–Adam nemají platný výchozí profil.")
        for profile_id, profile in profiles.items():
            if not PROFILE_ID_RE.fullmatch(profile_id):
                raise ValueError("Pracovní profil Human–Adam má neplatný identifikátor.")
            if not isinstance(profile.get("service"), HumanAdamService):
                raise ValueError("Pracovní profil Human–Adam nemá platnou službu.")
        self.profiles = dict(profiles)
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
    def active_service(self) -> HumanAdamService:
        return self.profiles[self.active_profile_id]["service"]

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

    def _profile_rows(self) -> list[dict[str, Any]]:
        active_id = self.active_profile_id
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

    def status(self) -> dict[str, Any]:
        try:
            active_id = self.active_profile_id
            profile = self.profiles[active_id]
            payload = profile["service"].status()
            return {
                **payload,
                "work_profile": {
                    "id": active_id,
                    "label": str(profile.get("label") or active_id),
                    "description": str(profile.get("description") or ""),
                },
                "work_profiles": self._profile_rows(),
                "development_semaphore": self.development_status(),
            }
        except (AppServerError, SessionHubError, OSError, ValueError) as exc:
            return {
                "ok": False,
                "status": "human_adam_profile_status_failed",
                "message": str(exc),
                "work_profiles": [],
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
            if workspace.get("source_update_available"):
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
                        "Zdrojový main má pracovní změny; aktivní profil nyní nelze bezpečně aktualizovat."
                    )
                self._assert_target_workspace(workspace)
                workspace = service.workspace.sync_from_main(confirmed=True)
                self._assert_target_workspace(workspace)
                workspace_synced = True
            result = service.connect()
        return {
            **result,
            **self._profile_status_fields(),
            "workspace_synced": workspace_synced,
        }

    def send(self, **kwargs: Any) -> dict[str, Any]:
        with self.profile_operation() as service:
            lease = self.development_semaphore.status()
            active_id = self.active_profile_id
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
            development_control_block = "\n".join(
                (
                    "[DEVELOPMENT_CONTROL]",
                    "source=private_global_development_semaphore",
                    f"profile_id={active_id}",
                    f"lease_state={state}",
                    f"lease_owner_id={str(lease.get('owner_id') or 'none')}",
                    f"writable={'true' if writable else 'false'}",
                    "rule=When writable=false, remain read-only and do not change files or Git.",
                    "[/DEVELOPMENT_CONTROL]",
                )
            )
            return service.send(
                **kwargs,
                development_control_block=development_control_block,
            )

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

    def checkpoint(self, **kwargs: Any) -> dict[str, Any]:
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
        return {
            **lease,
            "active_profile_id": active_id,
            "active_profile_label": str(self.profiles[active_id].get("label") or active_id),
            "workspace_rows": rows,
            "blockers": blockers,
            "can_acquire_profile": bool(
                free
                and not source_dirty
                and not any(row.get("has_wip") for row in rows if row["id"] != active_id)
            ),
            "can_acquire_terminal": bool(free and not any_profile_wip),
            "can_checkpoint": bool(lease_running and owner_id == active_id),
            "can_deploy": bool(lease_running and owner_id == active_id and not blockers),
            "can_pause": bool(lease_running),
            "can_resume": bool(lease_active and lease.get("mode") == "paused"),
            "can_release": bool(lease_active and self._safe_to_release()),
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
        active_id = self.active_profile_id
        profile = self.profiles[active_id]
        return {
            "work_profile": {
                "id": active_id,
                "label": str(profile.get("label") or active_id),
                "description": str(profile.get("description") or ""),
            },
            "work_profiles": self._profile_rows(),
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
            current_id = self.active_profile_id
            if target_id == current_id:
                return {**self.status(), "switched": False}
            current = self.profiles[current_id]["service"]
            target = self.profiles[target_id]["service"]
            current_session = current.hub.snapshot()
            if current_session.get("turn_busy") or current_session.get("active_turn"):
                raise SessionBusyError("Profil nelze přepnout během aktivního tahu Adama.")
            if self._has_uncertain_delivery(current_session):
                raise SessionBusyError("Profil nelze přepnout, dokud není vyřešené nejisté doručení.")
            self._assert_workspace_can_leave(current.workspace.status())

            target_status = target.workspace.status()
            if int(target_status.get("source_pending_changes") or 0) > 0:
                raise AppServerError("Zdrojový main má pracovní změny; nový profil nyní nelze bezpečně připravit.")
            if not target_status.get("prepared"):
                target_status = target.workspace.prepare()
            self._assert_target_workspace(target_status)
            if target_status.get("source_update_available"):
                target_status = target.workspace.sync_from_main(confirmed=True)
            self._assert_target_workspace(target_status)

            target.connect()
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
        finally:
            self._operation_lock.release()

    def close(self) -> None:
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
    return HumanAdamProfileManager(
        profiles={
            "human_adam": {
                "label": "Human–Adam",
                "description": "Vývoj pracovního rozhraní Human–Adam",
                "default_project_name": "App-server rozhrani / novy Adam",
                "service": human_service,
            },
            "knihovna": {
                "label": "Knihovna",
                "description": "Články, přílohy a práce s Knihovnou v Cockpitu",
                "default_project_name": "Znalostni databaze / Knihovna clanku / Knowledge inbox",
                "service": knihovna_service,
            },
        },
        default_profile_id="human_adam",
        runtime=runtime,
    )


HUMAN_ADAM = build_human_adam_profiles()
atexit.register(HUMAN_ADAM.close)
