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
from app.communication.human_adam_deploy import (
    DEPLOYMENT_LOCK,
    DEFAULT_DEPLOYMENT_DIAGNOSTIC,
    DEFAULT_DEPLOYMENT_RECEIPT,
)
from app.communication.human_adam_service import (
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


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRIVATE_COMMUNICATION_ROOT = PROJECT_ROOT / "data" / "private" / "communication"
PRIVATE_PROFILE_ROOT = PROJECT_ROOT / "data" / "private" / "human_adam_profiles"
DEFAULT_PROFILE_STATE_PATH = PRIVATE_COMMUNICATION_ROOT / "human_adam_active_profile.json"
DEFAULT_HUMAN_SESSION_PATH = PRIVATE_COMMUNICATION_ROOT / "canonical_session.json"
DEFAULT_HUMAN_CONTEXT_ANCHOR_PATH = PRIVATE_COMMUNICATION_ROOT / "human_adam_context_anchor.json"
KNIHOVNA_PROFILE_ROOT = PRIVATE_PROFILE_ROOT / "knihovna"
KNIHOVNA_CONTEXT_ANCHOR_PATH = PRIVATE_COMMUNICATION_ROOT / "knihovna_context_anchor.json"
KNIHOVNA_TVBCP_RELATIVE_PATH = Path("memory/tvbcp/knihovna_cockpit.txt")
PROFILE_ID_RE = re.compile(r"[a-z][a-z0-9_-]{1,31}")
PROFILE_STATE_SCHEMA = 1

KNIHOVNA_DEVELOPER_INSTRUCTIONS = HUMAN_ADAM_WORKSPACE_DEVELOPER_INSTRUCTIONS + (
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
            }
        except (AppServerError, SessionHubError, OSError, ValueError) as exc:
            return {
                "ok": False,
                "status": "human_adam_profile_status_failed",
                "message": str(exc),
                "work_profiles": [],
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
            result = service.connect()
        return {**result, **self._profile_status_fields()}

    def send(self, **kwargs: Any) -> dict[str, Any]:
        with self.profile_operation() as service:
            return service.send(**kwargs)

    def tvbcp(self) -> dict[str, Any]:
        return self.active_service.tvbcp()

    def context_anchor(self, *, include_content: bool = True) -> dict[str, Any]:
        return self.active_service.context_anchor(include_content=include_content)

    def set_context_anchor(self, **kwargs: Any) -> dict[str, Any]:
        with self.profile_operation() as service:
            return service.set_context_anchor(**kwargs)

    def work_review(self) -> dict[str, Any]:
        return self.active_service.work_review()

    def checkpoint(self, **kwargs: Any) -> dict[str, Any]:
        with self.profile_operation() as service:
            result = service.checkpoint(**kwargs)
        return result

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
        return any(
            item.get("status") in {"pending", "delivery_unknown"}
            or item.get("recovery_required") is True
            for item in session.get("messages") or []
            if isinstance(item, dict)
        )

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


def build_human_adam_profiles() -> HumanAdamProfileManager:
    runtime = LocalAppServerProcessController()
    human_service = HumanAdamService(
        runtime=runtime,
        state_path=DEFAULT_HUMAN_SESSION_PATH,
        deployment_receipt_path=DEFAULT_DEPLOYMENT_RECEIPT,
        deployment_diagnostic_path=DEFAULT_DEPLOYMENT_DIAGNOSTIC,
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
                "service": human_service,
            },
            "knihovna": {
                "label": "Knihovna",
                "description": "Články, přílohy a práce s Knihovnou v Cockpitu",
                "service": knihovna_service,
            },
        },
        default_profile_id="human_adam",
        runtime=runtime,
    )


HUMAN_ADAM = build_human_adam_profiles()
atexit.register(HUMAN_ADAM.close)
