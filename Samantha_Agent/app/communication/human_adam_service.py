"""Canonical Human–Adam text service used by Cockpit on Mac and iPhone."""

from __future__ import annotations

import atexit
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
from app.remote_work_cell import (
    DEFAULT_CODEX_BIN,
    REMOTE_APPROVAL_POLICY,
    REMOTE_DEVELOPER_INSTRUCTIONS,
    REMOTE_REASONING_EFFORT,
    REMOTE_SANDBOX_MODE,
    REMOTE_SANDBOX_POLICY,
    RemoteWorkspaceManager,
    read_remote_runtime_profile,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SESSION_STATE_PATH = PROJECT_ROOT / "data" / "private" / "communication" / "canonical_session.json"
HUMAN_ADAM_DEVELOPER_INSTRUCTIONS = REMOTE_DEVELOPER_INSTRUCTIONS.replace(
    "Jsi Adam Remote,", "Jsi Adam v kanonické relaci Human–Adam,"
) + (
    " Pro projekt komunikacni architektury pred vetsi praci precti "
    "Samantha_Agent/memory/tvbcp/architektura_komunikace_samantha.txt. "
    "Tento TVBCP aktualizuj jen na Miluv pokyn nebo pri skutecnem milniku; zapisuj "
    "rozhodnuti, dukazy, rizika a dalsi krok, nikdy ne plny chat ani citlive texty. "
    "Kazdy novy chronologicky zaznam pridej na konec souboru a oznac ho lokalnim "
    "datem, casem a casovou zonou ve formatu YYYY-MM-DD HH:MM TZ."
    " Private backup metadata v izolovane kopii zamerne nejsou; z jejich absence "
    "nikdy nevyvozuj, ze hlavni projekt nema zalohu."
)
MAX_MESSAGE_CHARS = 12_000
MAX_TVBCP_CHARS = 500_000
CANONICAL_TVBCP_RELATIVE_PATH = Path("memory/tvbcp/architektura_komunikace_samantha.txt")


class HumanAdamService:
    """Join the shared runtime, isolated workspace and one persistent thread."""

    def __init__(
        self,
        *,
        runtime: LocalAppServerProcessController | None = None,
        workspace: RemoteWorkspaceManager | None = None,
        state_path: Path = DEFAULT_SESSION_STATE_PATH,
        codex_binary: str = DEFAULT_CODEX_BIN,
        profile_getter: Callable[..., dict[str, Any]] = read_remote_runtime_profile,
        hub: CanonicalSessionHub | None = None,
    ):
        self.runtime = runtime or LocalAppServerProcessController(codex_binary=codex_binary)
        self.workspace = workspace or RemoteWorkspaceManager()
        self.codex_binary = str(codex_binary)
        self.profile_getter = profile_getter
        self._profile: dict[str, Any] = {}
        self.state_path = Path(state_path)
        self._hub = hub

    @property
    def hub(self) -> CanonicalSessionHub:
        return self._ensure_hub()

    def _ensure_hub(self) -> CanonicalSessionHub:
        if self._hub is not None:
            return self._hub
        self._hub = CanonicalSessionHub(
            state_path=self.state_path,
            workspace=self.workspace.project_root,
            client_factory=self._new_client,
            developer_instructions=HUMAN_ADAM_DEVELOPER_INSTRUCTIONS,
            sandbox=REMOTE_SANDBOX_MODE,
            sandbox_policy=REMOTE_SANDBOX_POLICY,
            approval_policy=REMOTE_APPROVAL_POLICY,
            reasoning_effort=REMOTE_REASONING_EFFORT,
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
                    "local_commit_count": int(workspace.get("local_commit_count") or 0),
                    "has_git_remote": bool(workspace.get("remotes")),
                    "label": "Izolovaný lokální workspace bez Git remote",
                },
                "profile": dict(self._profile),
                "session": self.hub.snapshot(),
            }
        except (AppServerError, SessionHubError, OSError, ValueError) as exc:
            return {"ok": False, "status": "human_adam_status_failed", "message": str(exc)}

    def connect(self) -> dict[str, Any]:
        workspace = self._workspace_status()
        self.runtime.start()
        if not self._profile:
            self._profile = self.profile_getter(
                cwd=self.workspace.project_root,
                codex_binary=self.codex_binary,
                client_factory=self._new_client,
            )
            self.hub.model = str(self._profile.get("model") or "") or None
        session = self.hub.connect()
        return {
            **self.status(),
            "ok": True,
            "connected": True,
            "thread_id": session.get("thread_id", ""),
            "workspace_head": workspace.get("head", ""),
        }

    def send(self, *, text: str, client_message_id: str, client_sent_at: str = "") -> dict[str, Any]:
        clean_text = str(text or "").strip()
        if len(clean_text) > MAX_MESSAGE_CHARS:
            raise SessionHubError(f"Zpráva může mít nejvýše {MAX_MESSAGE_CHARS} znaků.")
        runtime = self.runtime.status()
        session = self.hub.snapshot()
        if not runtime.get("reachable") or not session.get("connected"):
            raise SessionHubError("Nejdřív výslovně připoj Human–Adam.")
        self._workspace_status()
        result = self.hub.send(
            text=clean_text,
            client_message_id=client_message_id,
            client_sent_at=client_sent_at,
        )
        return {**result, "session": self.hub.snapshot()}

    def tvbcp(self) -> dict[str, Any]:
        workspace = self.workspace.status()
        if not workspace.get("prepared") or not workspace.get("project_ready"):
            raise AppServerError("Izolovaný workspace s projektovým TVBCP není připravený.")
        if not workspace.get("ok") or workspace.get("remotes"):
            raise AppServerError("TVBCP nelze číst z workspace s neočekávaným Git remote.")
        project_root = self.workspace.project_root.resolve()
        path = (project_root / CANONICAL_TVBCP_RELATIVE_PATH).resolve()
        if project_root not in path.parents or not path.is_file():
            raise AppServerError("Kanonický projektový TVBCP nebyl nalezen.")
        try:
            content = path.read_text(encoding="utf-8")
            modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(
                microsecond=0
            ).isoformat()
        except OSError as exc:
            raise AppServerError("Kanonický projektový TVBCP nelze bezpečně přečíst.") from exc
        if len(content) > MAX_TVBCP_CHARS:
            raise AppServerError("Kanonický projektový TVBCP překročil bezpečný limit zobrazení.")
        return {
            "ok": True,
            "title": "Architektura komunikace Samantha",
            "content": content,
            "modified_at": modified_at,
            "source": "isolated_workspace",
            "relative_path": CANONICAL_TVBCP_RELATIVE_PATH.as_posix(),
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
        )
    except SessionBusyError as exc:
        return {"ok": False, "status": "human_adam_busy", "message": str(exc)}
    except SessionDeliveryUnknownError as exc:
        return {"ok": False, "status": "delivery_unknown", "message": str(exc)}
    except (AppServerError, SessionHubError, OSError, ValueError) as exc:
        return {"ok": False, "status": "human_adam_send_failed", "message": str(exc)}


HUMAN_ADAM = HumanAdamService()
atexit.register(HUMAN_ADAM.close)
