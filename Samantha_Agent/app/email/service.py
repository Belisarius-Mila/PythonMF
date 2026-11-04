"""Opt-in one-shot service entry; preview/readiness never activate a service."""

from __future__ import annotations

from datetime import datetime, timezone
from functools import partial
from pathlib import Path
import plistlib
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.communication.agent_roles import EMAIL_ROLE, AgentRoleError, load_role, resolve_role, assert_current
from app.communication.local_runtime import DEFAULT_SOCKET_PATH
from app.codex_appserver import CodexAppServerClient, UnixSocketAppServerTransport
from app.file_persistence import FileLockTimeoutError, exclusive_file_lock
from .continuous_agent import ContinuousEmailAgent, DEFAULT_ROOT
from .continuous_source import IMAPAgentSource
from .codex_proposer import CodexEmailProposer
from .hourly_agent import HourlyEmailScheduler, PRAGUE, hourly_slot
from .pushcut import PushcutNotifier, pushcut_status


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_PATH = DEFAULT_ROOT / "service.json"
LABEL = "com.miloslavfalta.samantha.continuous-email"


class ServiceSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    enabled: bool = False
    providers: list[Literal["icloud", "seznam"]] = Field(default_factory=lambda: ["icloud", "seznam"], min_length=1)
    max_assessments_per_day: int = Field(default=20, ge=1, le=1000)
    batch_size: int = Field(default=10, ge=1, le=100)
    max_batches: int = Field(default=2, ge=1, le=20)


def load_settings(path: Path = SETTINGS_PATH) -> ServiceSettings:
    settings = ServiceSettings.model_validate_json(path.read_text(encoding="utf-8"))
    if len(set(settings.providers)) != len(settings.providers):
        raise ValueError("Duplicitní e-mailové zdroje.")
    return settings


def readiness(*, settings_path: Path = SETTINGS_PATH, worker=None,
              source_factory=IMAPAgentSource, role_loader=load_role,
              socket_path: Path = DEFAULT_SOCKET_PATH) -> dict:
    """Local configuration only: no IMAP, model, socket connection or writes."""
    blockers, sources = [], []
    try:
        settings = load_settings(settings_path)
    except (OSError, ValueError):
        settings = ServiceSettings()
        blockers.append("settings_missing_or_invalid")
    if not settings.enabled:
        blockers.append("service_disabled")
    try:
        role_loader(role=EMAIL_ROLE)
    except AgentRoleError:
        blockers.append("email_role_not_approved")
    if not socket_path.is_socket():
        blockers.append("appserver_socket_unavailable")
    state = (worker or ContinuousEmailAgent()).status()
    for provider in settings.providers:
        try:
            source = source_factory(provider)
            cursor = state["sources"].get(source.key, {})
            initialized = (isinstance(cursor.get("uidvalidity"), str) and bool(cursor["uidvalidity"])
                           and type(cursor.get("after_uid")) is int and cursor["after_uid"] >= 0)
            sources.append({"provider": provider, "initialized": initialized})
            if not initialized:
                blockers.append(provider + "_needs_initialization")
            if cursor.get("error") == "MailboxEpochChanged":
                blockers.append(provider + "_mailbox_epoch_changed")
        except Exception:
            blockers.append(provider + "_configuration_unavailable")
    return {"ready": not blockers, "blockers": blockers, "sources": sources,
            "enabled": settings.enabled, "role": EMAIL_ROLE,
            "hours": "07:00–22:00 Europe/Prague", "max_assessments_per_day": settings.max_assessments_per_day,
            "pushcut": pushcut_status(worker)}


def launch_agent_preview(*, project: Path = PROJECT_ROOT, python: Path | None = None) -> dict:
    """Return a future definition, never write to LaunchAgents or load launchd."""
    project = project.resolve()
    # Preserve the venv executable path, even when it is a symlink to base Python.
    python = python or project / ".venv/bin/python"
    return {"Label": LABEL,
            "ProgramArguments": [str(python), str(project / "scripts/continuous_email_agent.py"), "tick"],
            "WorkingDirectory": str(project), "StartInterval": 60, "RunAtLoad": True,
            "ProcessType": "Background",
            "StandardOutPath": str(project / "logs/continuous_email_service.out.log"),
            "StandardErrorPath": str(project / "logs/continuous_email_service.err.log")}


def launch_agent_xml() -> str:
    return plistlib.dumps(launch_agent_preview()).decode("utf-8")


def approved_selection() -> dict:
    # Fail before connecting if the dedicated role is not yet approved.
    load_role(role=EMAIL_ROLE)
    factory = partial(UnixSocketAppServerTransport, socket_path=DEFAULT_SOCKET_PATH)
    with CodexAppServerClient(transport_factory=factory) as client:
        selected = resolve_role(client.list_models(), role=EMAIL_ROLE)
    if selected["fallback"]:
        raise AgentRoleError("E-mailový provoz nesmí automaticky změnit zvolený model.")
    return selected


def service_tick(*, settings_path: Path = SETTINGS_PATH, worker=None, now: datetime | None = None,
                 source_factory=IMAPAgentSource, select_model=approved_selection,
                 selection_validator=assert_current, proposer_factory=CodexEmailProposer) -> dict:
    """One bounded pass. Attempts are reserved durably before each model call."""
    settings = load_settings(settings_path)
    if not settings.enabled:
        return {"status": "disabled", "proposals": 0}
    now = now or datetime.now(timezone.utc)
    if hourly_slot(now) is None:
        return {"status": "outside_hours", "proposals": 0}
    worker = worker or ContinuousEmailAgent()
    def finish(result):
        return {**result, "notifications": PushcutNotifier(worker).drain()}
    try:
        with exclusive_file_lock(worker.root / "service", timeout=0):
            sources = [source_factory(provider) for provider in settings.providers]
            state = worker.status()
            if any(not state["sources"].get(source.key, {}).get("uidvalidity")
                   or type(state["sources"][source.key].get("after_uid")) is not int
                   or state["sources"][source.key]["after_uid"] < 0 for source in sources):
                return {"status": "needs_initialization", "proposals": 0}
            slot = hourly_slot(now)
            if state.get("schedule", {}).get("completed_slot") == slot:
                return finish({"status": "already_completed", "proposals": 0})
            day = now.astimezone(PRAGUE).date().isoformat()

            def paused():
                current = load_settings(settings_path)
                used = worker.status().get("service", {}).get("daily_attempts", {}).get(day, 0)
                return (not current.enabled or current.providers != settings.providers
                        or used >= current.max_assessments_per_day)

            if paused():
                return finish({"status": "paused", "proposals": 0})
            selected = select_model()
            selection_validator(selected, role=EMAIL_ROLE)
            proposer = proposer_factory(selected["model"], effort=selected["reasoning_effort"])

            def propose(observed):
                selection_validator(selected, role=EMAIL_ROLE)
                def reserve(document):
                    counts = document.setdefault("service", {}).setdefault("daily_attempts", {})
                    counts[day] = counts.get(day, 0) + 1
                worker._update(reserve)
                return proposer(observed)

            return finish(HourlyEmailScheduler(worker).tick(sources, propose, now=now,
                batch_size=settings.batch_size, max_batches=settings.max_batches, should_stop=paused))
    except FileLockTimeoutError:
        return {"status": "busy", "proposals": 0}
