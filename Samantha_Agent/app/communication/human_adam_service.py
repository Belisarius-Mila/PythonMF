"""Canonical Human–Adam text service used by Cockpit on Mac and iPhone."""

from __future__ import annotations

import copy
import re
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from typing import Any, Callable

from app.codex_appserver import AppServerError, CodexAppServerClient, UnixSocketAppServerTransport
from app.communication.local_runtime import LocalAppServerProcessController
from app.communication.session_hub import (
    CanonicalSessionHub,
    SessionBusyError,
    SessionDeliveryUnknownError,
    SessionHubError,
)
from app.communication.human_adam_workspace import (
    DEFAULT_CODEX_BIN,
    HUMAN_ADAM_APPROVAL_POLICY,
    HUMAN_ADAM_REASONING_EFFORT,
    HUMAN_ADAM_SANDBOX_MODE,
    HUMAN_ADAM_SANDBOX_POLICY,
    HUMAN_ADAM_WORKSPACE_DEVELOPER_INSTRUCTIONS,
    HumanAdamWorkspaceManager,
    read_human_adam_runtime_profile,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SESSION_STATE_PATH = PROJECT_ROOT / "data" / "private" / "communication" / "canonical_session.json"
DEVELOPMENT_CONTROL_DEVELOPER_INSTRUCTIONS = (
    " Pred jakoukoli zmenou souboru nebo Gitu se rid blokem [DEVELOPMENT_CONTROL] "
    "vlozenym pred aktualni zpravu. Zapis je povolen jen pri writable=true. Pri "
    "writable=false zustan striktne read-only: nic nevytvarej, neupravuj, nemaz ani "
    "necheckpointuj; muzes analyzovat, vysvetlovat a navrhovat dalsi krok."
)
HUMAN_ADAM_DEVELOPER_INSTRUCTIONS = (
    HUMAN_ADAM_WORKSPACE_DEVELOPER_INSTRUCTIONS
    + DEVELOPMENT_CONTROL_DEVELOPER_INSTRUCTIONS
    + (
        " Pro projekt komunikacni architektury pred vetsi praci precti "
        "Samantha_Agent/memory/tvbcp/architektura_komunikace_samantha.txt. "
        "Tento TVBCP aktualizuj vyhradne na Miluv vyslovny pokyn; nikdy do nej nezapisuj "
        "samostatne ani pri milniku. Pri vyslovne vyzadanem zapisu zachyt "
        "rozhodnuti, dukazy, rizika a dalsi krok, nikdy ne plny chat ani citlive texty. "
        "Kazdy novy chronologicky zaznam pridej na konec souboru a oznac ho lokalnim "
        "datem, casem a casovou zonou ve formatu YYYY-MM-DD HH:MM TZ."
        " Private backup metadata v izolovane kopii zamerne nejsou; z jejich absence "
        "nikdy nevyvozuj, ze hlavni projekt nema zalohu. V bezne odpovedi Milovi "
        "uvadej u souboru jen samotny nazev bez cele cesty. Nejkratsi nutnou relativni "
        "cestu pouzij pouze pri shodnych nazvech nebo na Milovu vyslovnou zadost; "
        "absolutni cestu do textoveho okna nevypisuj."
    )
)
MAX_MESSAGE_CHARS = 12_000
MAX_TVBCP_CHARS = 500_000
CANONICAL_TVBCP_RELATIVE_PATH = Path("memory/tvbcp/architektura_komunikace_samantha.txt")
SAFE_GIT_HEAD_RE = re.compile(r"[0-9a-fA-F]{7,64}")
SAFE_WORKSPACE_RELATIONS = frozenset({"aligned", "local_ahead", "source_ahead", "diverged", "unknown"})
MAX_WORKSPACE_SNAPSHOT_COUNT = 1_000_000
THREAD_ROTATION_CONFIRMATION_TEXT = "POTVRZUJI ROTACI PROFILOVEHO VLAKNA"


def _safe_git_head(value: object) -> str:
    candidate = str(value or "").strip()
    return candidate.lower() if SAFE_GIT_HEAD_RE.fullmatch(candidate) else "unknown"


def _safe_snapshot_count(value: object) -> int:
    try:
        count = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return min(MAX_WORKSPACE_SNAPSHOT_COUNT, max(0, count))


def workspace_model_input(
    user_text: str,
    workspace: dict[str, Any],
    *,
    development_control_block: str = "",
) -> str:
    """Add allowlisted workspace metadata without changing persisted user text."""
    relation = str(workspace.get("workspace_relation") or "unknown").strip()
    if relation not in SAFE_WORKSPACE_RELATIONS:
        relation = "unknown"
    snapshot_lines = [
        "[SAFE_WORKSPACE_SNAPSHOT]",
        f"source_head={_safe_git_head(workspace.get('source_head'))}",
        f"workspace_head={_safe_git_head(workspace.get('head'))}",
        f"workspace_relation={relation}",
        f"uncommitted_change_count={_safe_snapshot_count(workspace.get('change_count'))}",
        f"local_commit_count={_safe_snapshot_count(workspace.get('local_commit_count'))}",
        "[/SAFE_WORKSPACE_SNAPSHOT]",
        "",
    ]
    if development_control_block:
        snapshot_lines.extend((development_control_block, ""))
    snapshot_lines.append(str(user_text))
    return "\n".join(snapshot_lines)


class HumanAdamService:
    """Join the shared runtime, isolated workspace and one persistent thread."""

    def __init__(
        self,
        *,
        runtime: LocalAppServerProcessController | None = None,
        workspace: HumanAdamWorkspaceManager | None = None,
        state_path: Path = DEFAULT_SESSION_STATE_PATH,
        work_profile_id: str = "human_adam",
        codex_binary: str = DEFAULT_CODEX_BIN,
        profile_getter: Callable[..., dict[str, Any]] = read_human_adam_runtime_profile,
        hub: CanonicalSessionHub | None = None,
        developer_instructions: str = HUMAN_ADAM_DEVELOPER_INSTRUCTIONS,
        sandbox_policy: dict[str, Any] | None = None,
        tvbcp_relative_path: Path = CANONICAL_TVBCP_RELATIVE_PATH,
        tvbcp_title: str = "Architektura komunikace Samantha",
    ):
        self.runtime = runtime or LocalAppServerProcessController(codex_binary=codex_binary)
        self.workspace = workspace or HumanAdamWorkspaceManager()
        self.codex_binary = str(codex_binary)
        self.profile_getter = profile_getter
        self.developer_instructions = str(developer_instructions).strip()
        self.sandbox_policy = copy.deepcopy(
            HUMAN_ADAM_SANDBOX_POLICY if sandbox_policy is None else sandbox_policy
        )
        self.tvbcp_relative_path = Path(tvbcp_relative_path)
        self.tvbcp_title = str(tvbcp_title).strip() or "Projektový TVBCP"
        self._profile: dict[str, Any] = {}
        self.state_path = Path(state_path)
        self.work_profile_id = str(work_profile_id or "").strip().lower()
        if not re.fullmatch(r"[a-z][a-z0-9_-]{1,31}", self.work_profile_id):
            raise ValueError("Pracovní profil služby nemá platný bezpečný identifikátor.")
        self._hub = hub

    @property
    def hub(self) -> CanonicalSessionHub:
        return self._ensure_hub()

    def detached_session_hub(
        self,
        *,
        state_path: Path,
        developer_instructions: str,
        workspace: Path | None = None,
        sandbox_policy: dict[str, Any] | None = None,
    ) -> CanonicalSessionHub:
        """Build an inert hub that shares this service's runtime and workspace.

        The returned hub does not create a private file, client or Codex thread
        until its ``connect`` method is called.
        """

        return CanonicalSessionHub(
            state_path=Path(state_path),
            workspace=Path(workspace or self.workspace.project_root),
            client_factory=self._new_client,
            developer_instructions=str(developer_instructions).strip(),
            sandbox=HUMAN_ADAM_SANDBOX_MODE,
            sandbox_policy=(
                self.sandbox_policy
                if sandbox_policy is None
                else copy.deepcopy(sandbox_policy)
            ),
            approval_policy=HUMAN_ADAM_APPROVAL_POLICY,
            reasoning_effort=HUMAN_ADAM_REASONING_EFFORT,
        )

    def _ensure_hub(self) -> CanonicalSessionHub:
        if self._hub is not None:
            return self._hub
        self._hub = self.detached_session_hub(
            state_path=self.state_path,
            developer_instructions=self.developer_instructions,
        )
        return self._hub

    def _new_client(self, **_kwargs: Any) -> CodexAppServerClient:
        transport_factory = partial(
            UnixSocketAppServerTransport,
            socket_path=self.runtime.socket_path,
        )
        return CodexAppServerClient(
            codex_binary=self.codex_binary,
            timeout=180.0,
            transport_factory=transport_factory,
        )

    def _workspace_status(self) -> dict[str, Any]:
        status = self.workspace.status()
        if not status.get("prepared") or not status.get("project_ready"):
            raise AppServerError("Izolovaný workspace Human–Adam není připravený.")
        if not status.get("ok") or status.get("remotes"):
            raise AppServerError("Izolovaný workspace není v bezpečném stavu bez Git remote.")
        if status.get("source_update_available") or status.get("workspace_relation") == "diverged":
            raise AppServerError("Izolovaný workspace čeká na bezpečnou aktualizaci z main.")
        return status

    def status(self) -> dict[str, Any]:
        try:
            workspace = self.workspace.status()
            workspace_ready = bool(
                workspace.get("ok")
                and workspace.get("prepared")
                and workspace.get("project_ready")
                and not workspace.get("remotes")
                and not workspace.get("source_update_available")
                and workspace.get("workspace_relation") != "diverged"
            )
            session = self.hub.snapshot()
            return {
                "ok": workspace_ready,
                "runtime": self.runtime.status(),
                "workspace": {
                    "prepared": bool(workspace.get("prepared")),
                    "ready": bool(workspace.get("project_ready")),
                    "dirty": bool(workspace.get("dirty")),
                    "change_count": int(workspace.get("change_count") or 0),
                    "sync_available": bool(workspace.get("source_update_available")),
                    "workspace_relation": str(workspace.get("workspace_relation") or "unknown"),
                    "local_checkpoint_ahead": bool(workspace.get("local_checkpoint_ahead")),
                    "local_checkpoint_preserved": bool(workspace.get("local_checkpoint_preserved")),
                    "local_commit_count": int(workspace.get("local_commit_count") or 0),
                    "has_git_remote": bool(workspace.get("remotes")),
                    "label": "Izolovaný lokální workspace bez Git remote",
                },
                "profile": dict(self._profile),
                "session": session,
            }
        except (AppServerError, SessionHubError, OSError, ValueError) as exc:
            return {"ok": False, "status": "human_adam_status_failed", "message": str(exc)}

    def connect(self, *, recover_unreachable_runtime: bool = False) -> dict[str, Any]:
        workspace = self._workspace_status()
        self.runtime.start(recover_unreachable_owned=recover_unreachable_runtime)
        if not self._profile:
            self._profile = {
                **self.profile_getter(
                    cwd=self.workspace.project_root,
                    codex_binary=self.codex_binary,
                    client_factory=self._new_client,
                ),
                "sandbox_mode": HUMAN_ADAM_SANDBOX_MODE,
                "sandbox_policy": copy.deepcopy(self.sandbox_policy),
                "network_access": bool(self.sandbox_policy.get("networkAccess")),
            }
            self.hub.model = str(self._profile.get("model") or "") or None
        session = self.hub.connect()
        return {
            **self.status(),
            "ok": True,
            "connected": True,
            "thread_id": session.get("thread_id", ""),
            "workspace_head": workspace.get("head", ""),
        }

    def send(
        self,
        *,
        text: str,
        client_message_id: str,
        client_sent_at: str = "",
        development_control_block: str = "",
        write_intent: bool = False,
    ) -> dict[str, Any]:
        if write_intent:
            raise SessionHubError(
                "Jednorázovou autorizaci zápisu musí ověřit správce pracovních proudů."
            )
        clean_text = str(text or "").strip()
        if len(clean_text) > MAX_MESSAGE_CHARS:
            raise SessionHubError(f"Zpráva může mít nejvýše {MAX_MESSAGE_CHARS} znaků.")
        runtime = self.runtime.status()
        session = self.hub.snapshot()
        if not runtime.get("reachable") or not session.get("connected"):
            raise SessionHubError("Nejdřív výslovně připoj Human–Adam.")
        workspace = self._workspace_status()
        result = self.hub.send(
            text=clean_text,
            client_message_id=client_message_id,
            client_sent_at=client_sent_at,
            model_input_text=workspace_model_input(
                clean_text,
                workspace,
                development_control_block=development_control_block,
            ),
        )
        return {
            **result,
            "session": self.hub.snapshot(),
        }

    def thread_rotation_status(self) -> dict[str, Any]:
        session = self.hub.snapshot()
        rotation = self.hub.rotation_status()
        blockers = list(rotation.get("blockers") or [])
        if not session.get("connected"):
            blockers.append("Před rotací musí být profil připojený.")
        return {
            "ok": True,
            "ready": not blockers,
            "thread_id": str(rotation.get("thread_id") or ""),
            "thread_message_count": int(rotation.get("thread_message_count") or 0),
            "rotation_count": int(rotation.get("rotation_count") or 0),
            "blockers": blockers,
            "confirmation_text": THREAD_ROTATION_CONFIRMATION_TEXT,
            "preserves_previous_thread": True,
            "archives_previous_thread": False,
        }

    def rotate_thread(self, *, confirmation: str, expected_thread_id: str) -> dict[str, Any]:
        if str(confirmation or "").strip() != THREAD_ROTATION_CONFIRMATION_TEXT:
            raise SessionHubError(
                f"Chybí přesná potvrzovací věta: {THREAD_ROTATION_CONFIRMATION_TEXT}"
            )
        audit = self.thread_rotation_status()
        if not audit.get("ready"):
            detail = " ".join(str(item) for item in audit.get("blockers") or [])
            raise SessionHubError(detail or "Profilové vlákno nyní nelze bezpečně rotovat.")
        result = self.hub.rotate_thread(expected_thread_id=expected_thread_id)
        return {
            **result,
            "previous_thread_preserved": True,
        }

    def tvbcp(self, *, initial_content: str = "") -> dict[str, Any]:
        workspace = self.workspace.status()
        if not workspace.get("prepared") or not workspace.get("project_ready"):
            raise AppServerError("Izolovaný workspace s projektovým TVBCP není připravený.")
        if not workspace.get("ok") or workspace.get("remotes"):
            raise AppServerError("TVBCP nelze číst z workspace s neočekávaným Git remote.")
        project_root = self.workspace.project_root.resolve()
        path = (project_root / self.tvbcp_relative_path).resolve()
        if project_root not in path.parents:
            raise AppServerError("Kanonický projektový TVBCP nebyl nalezen.")
        initialized = path.is_file()
        if path.exists() and not initialized:
            raise AppServerError("Kanonický projektový TVBCP nebyl nalezen.")
        if initialized:
            try:
                content = path.read_text(encoding="utf-8")
                modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(
                    microsecond=0
                ).isoformat()
            except OSError as exc:
                raise AppServerError("Kanonický projektový TVBCP nelze bezpečně přečíst.") from exc
        else:
            content = str(initial_content or "")
            modified_at = ""
            if not content:
                raise AppServerError("Kanonický projektový TVBCP nebyl nalezen.")
        if len(content) > MAX_TVBCP_CHARS:
            raise AppServerError("Kanonický projektový TVBCP překročil bezpečný limit zobrazení.")
        return {
            "ok": True,
            "title": self.tvbcp_title,
            "content": content,
            "modified_at": modified_at,
            "source": "isolated_workspace" if initialized else "canonical_template",
            "relative_path": self.tvbcp_relative_path.as_posix(),
            "read_only": True,
            "initialized": initialized,
            "workspace_dirty": bool(workspace.get("dirty")),
            "workspace_change_count": int(workspace.get("change_count") or 0),
            "sync_available": bool(workspace.get("source_update_available")),
        }

    def work_review(self) -> dict[str, Any]:
        return self.workspace.review()

    def checkpoint(self, *, confirmed: bool, message: str = "") -> dict[str, Any]:
        if self.hub.snapshot().get("turn_busy"):
            raise SessionBusyError("Checkpoint nelze vytvořit během aktivního tahu.")
        safe_message = " ".join(str(message or "").split())[:120]
        if not safe_message:
            raise AppServerError("Zadej krátký název WIP checkpointu.")
        result = self.workspace.checkpoint(confirmed=confirmed, message=safe_message)
        return {
            "ok": True,
            "checkpoint_created": bool(result.get("checkpoint_created")),
            "message": str(result.get("message") or ""),
            "work": self.workspace.review(),
            "status": self.status(),
        }

    def close(self) -> None:
        if self._hub is None:
            self.runtime.close()
            return
        try:
            self._hub.close()
        except SessionBusyError:
            return
        self.runtime.close()


def human_adam_status_action(*, service: HumanAdamService) -> dict[str, Any]:
    return service.status()


def human_adam_tvbcp_action(*, service: HumanAdamService) -> dict[str, Any]:
    try:
        return service.tvbcp()
    except (AppServerError, OSError, ValueError) as exc:
        return {"ok": False, "status": "human_adam_tvbcp_failed", "message": str(exc)}


def human_adam_thread_rotation_status_action(*, service: HumanAdamService) -> dict[str, Any]:
    try:
        return service.thread_rotation_status()
    except (AppServerError, SessionHubError, OSError, ValueError) as exc:
        return {"ok": False, "status": "human_adam_thread_rotation_failed", "message": str(exc)}


def human_adam_thread_rotation_action(
    payload: dict[str, Any],
    *,
    service: HumanAdamService,
) -> dict[str, Any]:
    try:
        return service.rotate_thread(
            confirmation=str(payload.get("confirmation") or ""),
            expected_thread_id=str(payload.get("expected_thread_id") or ""),
        )
    except SessionBusyError as exc:
        return {"ok": False, "status": "human_adam_busy", "message": str(exc)}
    except SessionDeliveryUnknownError as exc:
        return {"ok": False, "status": "delivery_unknown", "message": str(exc)}
    except (AppServerError, SessionHubError, OSError, ValueError) as exc:
        return {"ok": False, "status": "human_adam_thread_rotation_failed", "message": str(exc)}


def human_adam_work_review_action(*, service: HumanAdamService) -> dict[str, Any]:
    try:
        return service.work_review()
    except (AppServerError, OSError, ValueError) as exc:
        return {"ok": False, "status": "human_adam_work_review_failed", "message": str(exc)}


def human_adam_checkpoint_action(payload: dict[str, Any], *, service: HumanAdamService) -> dict[str, Any]:
    if payload.get("confirmed") is not True:
        return {
            "ok": False,
            "status": "confirmation_required",
            "message": "Lokální WIP checkpoint vyžaduje výslovné potvrzení.",
        }
    try:
        return service.checkpoint(
            confirmed=True,
            message=str(payload.get("message") or ""),
        )
    except (AppServerError, SessionHubError, OSError, ValueError) as exc:
        return {"ok": False, "status": "human_adam_checkpoint_failed", "message": str(exc)}


def human_adam_connect_action(*, service: HumanAdamService) -> dict[str, Any]:
    try:
        return service.connect()
    except (AppServerError, SessionHubError, OSError, ValueError) as exc:
        return {"ok": False, "status": "human_adam_connect_failed", "message": str(exc)}


def human_adam_send_action(payload: dict[str, Any], *, service: HumanAdamService) -> dict[str, Any]:
    try:
        return service.send(
            text=str(payload.get("message") or ""),
            client_message_id=str(payload.get("client_message_id") or ""),
            client_sent_at=str(payload.get("client_sent_at") or ""),
            write_intent=payload.get("write_intent") is True,
        )
    except SessionBusyError as exc:
        return {"ok": False, "status": "human_adam_busy", "message": str(exc)}
    except SessionDeliveryUnknownError as exc:
        return {"ok": False, "status": "delivery_unknown", "message": str(exc)}
    except (AppServerError, SessionHubError, OSError, ValueError) as exc:
        return {"ok": False, "status": "human_adam_send_failed", "message": str(exc)}


def __getattr__(name: str) -> Any:
    """Keep the former import path while the global instance lives in profile routing."""
    if name == "HUMAN_ADAM":
        from app.communication.human_adam_profiles import HUMAN_ADAM

        return HUMAN_ADAM
    raise AttributeError(name)
