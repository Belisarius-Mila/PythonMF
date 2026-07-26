"""Status and health response orchestration for Samantha Cockpit."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable


StatusLoader = Callable[[], Any]


@dataclass(frozen=True)
class CockpitStatusLoaders:
    """Loaders used to assemble the full Cockpit status response."""

    downloads: StatusLoader
    document_work: Callable[[Any], Any]
    document_intake: Callable[[Any], Any]
    document_cases: StatusLoader
    document_classification: StatusLoader
    document_due_candidates: StatusLoader
    reminders: StatusLoader
    urgent_reminders: StatusLoader
    backup_status: StatusLoader
    action_queue: Callable[[Any, Any, Any], Any]
    vault: StatusLoader
    scandocu: StatusLoader
    codex_approval: StatusLoader
    git: StatusLoader


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_server_health_status(
    *,
    code_stamp: str,
    host: str,
    port: int,
    timestamp_loader: Callable[[], str] = utc_timestamp,
    pid_loader: Callable[[], int] = os.getpid,
) -> dict[str, Any]:
    """Build the lightweight server liveness and identity response."""
    return {
        "ok": True,
        "generated_at": timestamp_loader(),
        "server": {
            "code_stamp": code_stamp,
            "pid": pid_loader(),
            "host": host,
            "port": port,
        },
    }


def build_cockpit_status(
    *,
    loaders: CockpitStatusLoaders,
    code_stamp: str,
    performance_clock: Callable[[], float] = time.perf_counter,
    timestamp_loader: Callable[[], str] = utc_timestamp,
    pid_loader: Callable[[], int] = os.getpid,
) -> dict[str, Any]:
    """Assemble the full dashboard status while measuring each section."""
    started_at = performance_clock()
    section_timings: dict[str, float] = {}

    def timed_section(name: str, callback: StatusLoader) -> Any:
        section_started_at = performance_clock()
        value = callback()
        section_timings[name] = round((performance_clock() - section_started_at) * 1000, 2)
        return value

    downloads = timed_section("downloads", loaders.downloads)
    document_work = timed_section("document_work", lambda: loaders.document_work(downloads))
    document_intake = timed_section("document_intake", lambda: loaders.document_intake(downloads))
    document_cases = timed_section("document_cases", loaders.document_cases)
    document_classification = timed_section("document_classification", loaders.document_classification)
    document_due_candidates = timed_section("document_due_candidates", loaders.document_due_candidates)
    reminders = timed_section("reminders", loaders.reminders)
    urgent = timed_section("urgent_reminders", loaders.urgent_reminders)
    backup_status = timed_section("backup_status", loaders.backup_status)
    action_queue = timed_section(
        "action_queue",
        lambda: loaders.action_queue(document_work, reminders, urgent),
    )
    vault = timed_section("vault", loaders.vault)
    scandocu = timed_section("scandocu", loaders.scandocu)
    codex_approval = timed_section("codex_approval", loaders.codex_approval)
    git_status = timed_section("git", loaders.git)
    total_ms = round((performance_clock() - started_at) * 1000, 2)
    slowest_sections = [
        {"name": name, "ms": milliseconds}
        for name, milliseconds in sorted(section_timings.items(), key=lambda item: item[1], reverse=True)[:3]
    ]

    return {
        "generated_at": timestamp_loader(),
        "server": {
            "code_stamp": code_stamp,
            "pid": pid_loader(),
        },
        "status_timing": {
            "total_ms": total_ms,
            "sections_ms": section_timings,
            "slowest_sections": slowest_sections,
        },
        "downloads": downloads,
        "document_work": document_work,
        "document_intake": document_intake,
        "document_cases": document_cases,
        "document_classification": document_classification,
        "document_due_candidates": document_due_candidates,
        "action_queue": action_queue,
        "backup": backup_status["message"],
        "backup_status": backup_status,
        "vault": vault,
        "reminders": reminders,
        "urgent_reminders": urgent,
        "scandocu": scandocu,
        "codex_approval": codex_approval,
        "git": git_status,
    }


def build_cockpit_live_status(
    *,
    codex_approval_loader: StatusLoader,
    performance_clock: Callable[[], float] = time.perf_counter,
    timestamp_loader: Callable[[], str] = utc_timestamp,
) -> dict[str, Any]:
    """Build the lightweight, frequently changing approval state."""
    started_at = performance_clock()

    codex_approval_started_at = performance_clock()
    codex_approval = codex_approval_loader()
    codex_approval_ms = round((performance_clock() - codex_approval_started_at) * 1000, 2)

    return {
        "generated_at": timestamp_loader(),
        "codex_approval": codex_approval,
        "live_status_timing": {
            "total_ms": round((performance_clock() - started_at) * 1000, 2),
            "codex_approval_ms": codex_approval_ms,
        },
    }
