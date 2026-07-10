"""Runtime status and lifecycle services for Samantha VoiceBridge."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable

from app.documents.vault import safe_text
from app.speech.terminal_bridge import normalize_tty


def voice_bridge_status(
    *,
    marker_path: Path,
    codex_tty_discoverer: Callable[[], list[str]],
    managed_codex_tty_labeler: Callable[[], dict[str, str]],
    orphaned_janicka_reporter: Callable[[], dict[str, Any]] | None,
    screen_runner: Callable[..., subprocess.CompletedProcess[str]],
    marker_pid_checker: Callable[[int], bool] | None = None,
    expected_codex_session_limit: int = 1,
) -> dict[str, Any]:
    """Build VoiceBridge readiness without depending on the Cockpit monolith."""
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        marker = {}

    marked_tty = normalize_tty(str(marker.get("tty") or ""))
    parent_pid = marker.get("parent_pid")
    marker_parent_pid_active = False
    marker_parent_pid_unverified = False
    pid_checker = marker_pid_checker or (lambda pid: os.kill(pid, 0) is None)
    if isinstance(parent_pid, int) and parent_pid > 0:
        try:
            marker_parent_pid_active = bool(pid_checker(parent_pid))
        except PermissionError:
            marker_parent_pid_unverified = True
        except (OSError, ValueError):
            marker_parent_pid_active = False
    try:
        codex_ttys = [normalize_tty(item) for item in codex_tty_discoverer()]
    except Exception:
        codex_ttys = []
    codex_ttys = [item for item in codex_ttys if item and item != "??"]
    try:
        managed_codex_labels = managed_codex_tty_labeler()
    except Exception:
        managed_codex_labels = {}
    managed_codex_labels = {
        normalize_tty(str(tty)): safe_text(str(label))[:80]
        for tty, label in managed_codex_labels.items()
        if normalize_tty(str(tty)) in codex_ttys
    }
    managed_codex_ttys = sorted(managed_codex_labels)
    try:
        orphan_report = orphaned_janicka_reporter() if orphaned_janicka_reporter else {}
    except Exception:
        orphan_report = {}
    orphaned_janicka_ttys = sorted(
        {
            normalize_tty(str(tty))
            for tty in orphan_report.get("orphaned_ttys", [])
            if normalize_tty(str(tty)) in codex_ttys and normalize_tty(str(tty)) not in managed_codex_labels
        }
    )
    orphaned_janicka_labels = {tty: "stará Janička mimo správu" for tty in orphaned_janicka_ttys}
    human_codex_ttys = [
        tty for tty in codex_ttys if tty not in managed_codex_labels and tty not in orphaned_janicka_labels
    ]

    screen_status = "unknown"
    screen_message = "screen stav nelze zjistit"
    try:
        completed = screen_runner(
            ["screen", "-ls"], capture_output=True, text=True, timeout=3, check=False
        )
        screen_output = f"{completed.stdout}\n{completed.stderr}".strip()
        if completed.returncode == 0 or "There is a screen on" in screen_output or "samantha_codex" in screen_output:
            screen_status = "running"
            screen_message = "screen běží"
        elif "No Sockets found" in screen_output:
            screen_status = "not_running"
            screen_message = "screen neběží"
        else:
            screen_message = screen_output or "screen stav nelze zjistit"
    except (OSError, subprocess.TimeoutExpired) as exc:
        screen_message = str(exc)

    effective_tty = marked_tty if marked_tty in codex_ttys else ""
    if not effective_tty and marked_tty and len(codex_ttys) == 1:
        effective_tty = codex_ttys[0]
    marker_pid_fallback = False
    if not effective_tty and marked_tty and not codex_ttys and (
        marker_parent_pid_active or (marker_parent_pid_unverified and screen_status == "running")
    ):
        effective_tty = marked_tty
        marker_pid_fallback = True
    mac_bridge_ready = bool(effective_tty)
    warnings: list[str] = []
    notes: list[str] = []
    if not marked_tty:
        warnings.append("není označené cílové TTY")
    elif marked_tty not in codex_ttys:
        if marker_pid_fallback:
            if marker_parent_pid_active:
                warnings.append(
                    f"aktivní Codex relaci nelze ověřit přes ps, ale marker {marked_tty} má živý Codex PID {parent_pid}"
                )
            else:
                warnings.append(
                    f"aktivní Codex relaci nelze ověřit přes ps ani PID kvůli oprávnění, ale screen běží a marker míří na {marked_tty}"
                )
        elif effective_tty:
            warnings.append(f"označené TTY {marked_tty} je staré; použije se jediná aktivní Codex relace {effective_tty}")
        else:
            warnings.append(f"označené TTY {marked_tty} není mezi aktivními Codex relacemi")
    if len(human_codex_ttys) > expected_codex_session_limit:
        warnings.append(f"běží {len(human_codex_ttys)} běžných Codex relací, očekáváno nejvýše {expected_codex_session_limit}")
    if managed_codex_ttys:
        notes.append(
            "spravované relace mimo limit: "
            + ", ".join(f"{tty}={managed_codex_labels[tty]}" for tty in managed_codex_ttys)
        )
    if orphaned_janicka_ttys:
        warnings.append(
            "stará Janička relace mimo správu: " + ", ".join(orphaned_janicka_ttys) + "; uklidit v okně Janička"
        )
    if screen_status == "not_running":
        notes.append("screen neběží; pro lokální Mac TTY bridge to není blokující")

    target = effective_tty or marked_tty or "nezjištěno"
    marker_label = marked_tty or "nezjištěno"
    readiness = "Mac TTY bridge připravený" if mac_bridge_ready else "Mac TTY bridge není připravený"
    codex_count_label = "neověřeno přes ps" if marker_pid_fallback and not codex_ttys else str(len(human_codex_ttys))
    message = (
        f"{readiness}. Bridge cílí na {target} (marker: {marker_label}). "
        f"Codex relace celkem: {len(codex_ttys)} "
        f"(běžné: {codex_count_label}, limit {expected_codex_session_limit}; "
        f"spravované: {len(managed_codex_ttys)}). {screen_message}."
    )
    if notes:
        message = f"{message} Info: {', '.join(notes)}."
    if warnings:
        message = f"{message} Pozor: {', '.join(warnings)}."

    return {
        "ok": True,
        "status": "warn" if warnings else "ok",
        "message": message,
        "marked_tty": marked_tty,
        "effective_tty": effective_tty,
        "marked_at": str(marker.get("marked_at") or ""),
        "parent_pid": parent_pid,
        "marker_parent_pid_active": marker_parent_pid_active,
        "marker_parent_pid_unverified": marker_parent_pid_unverified,
        "marker_pid_fallback": marker_pid_fallback,
        "mac_bridge_ready": mac_bridge_ready,
        "codex_ttys": codex_ttys,
        "codex_tty_count": len(codex_ttys),
        "human_codex_ttys": human_codex_ttys,
        "human_codex_tty_count": len(human_codex_ttys),
        "managed_codex_ttys": managed_codex_ttys,
        "managed_codex_labels": managed_codex_labels,
        "orphaned_janicka_ttys": orphaned_janicka_ttys,
        "orphaned_janicka_labels": orphaned_janicka_labels,
        "orphaned_janicka_count": len(orphaned_janicka_ttys),
        "codex_tty_count_label": codex_count_label,
        "expected_codex_session_limit": expected_codex_session_limit,
        "screen_status": screen_status,
        "screen_message": screen_message,
        "notes": notes,
        "warnings": warnings,
    }
