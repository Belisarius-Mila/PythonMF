"""Canonical Human–Adam text service used by Cockpit on Mac and iPhone."""

from __future__ import annotations

import atexit
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
)
MAX_MESSAGE_CHARS = 12_000


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
        if status.get("sync_available"):
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
                and not workspace.get("sync_available")
            )
            return {
                "ok": workspace_ready,
                "runtime": self.runtime.status(),
                "workspace": {
                    "prepared": bool(workspace.get("prepared")),
                    "ready": bool(workspace.get("project_ready")),
                    "dirty": bool(workspace.get("dirty")),
                    "change_count": int(workspace.get("change_count") or 0),
                    "sync_available": bool(workspace.get("sync_available")),
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
