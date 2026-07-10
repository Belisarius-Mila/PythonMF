"""Runtime status and lifecycle services for Samantha VoiceBridge."""

from __future__ import annotations

import json
import os
import subprocess
import signal
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.documents.vault import safe_text
from app.speech.terminal_bridge import normalize_tty


def set_voice_bridge_marker(
    tty: str,
    *,
    marker_path: Path,
    codex_tty_discoverer: Callable[[], list[str]],
    pid_loader: Callable[[], int] = os.getpid,
    timestamp_loader: Callable[[], str] = lambda: datetime.now(timezone.utc).isoformat(),
) -> dict[str, Any]:
    target_tty = normalize_tty(str(tty or ""))
    if not target_tty or target_tty == "??":
        return {"ok": False, "status": "missing_tty", "message": "Chybí cílové TTY pro voice bridge."}
    try:
        codex_ttys = [normalize_tty(item) for item in codex_tty_discoverer()]
    except Exception:
        codex_ttys = []
    codex_ttys = [item for item in codex_ttys if item and item != "??"]
    if target_tty not in codex_ttys:
        return {
            "ok": False,
            "status": "tty_not_active",
            "message": f"TTY {target_tty} není mezi aktivními Codex relacemi.",
            "target_tty": target_tty,
            "codex_ttys": codex_ttys,
        }
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text(
        json.dumps(
            {
                "tty": target_tty,
                "marked_at": timestamp_loader(),
                "parent_pid": pid_loader(),
                "note": "Private runtime marker for Adam Voice Mode terminal bridge, set from Cockpit.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "ok": True,
        "status": "marker_updated",
        "message": f"Voice bridge marker byl nastaven na {target_tty}.",
        "marked_tty": target_tty,
        "codex_ttys": codex_ttys,
    }


def start_voice_mode_watcher(
    *,
    status_loader: Callable[..., dict[str, Any]],
    status_writer: Callable[..., dict[str, Any]],
    launcher: Callable[..., object],
    log_file: Path,
    project_root: Path,
    script_path: Path,
    path_formatter: Callable[[Path], Path | str],
    environ: dict[str, str] | os._Environ[str] = os.environ,
    terminal_bridge: bool | None = None,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    current = status_loader()
    if current.get("running"):
        return {
            "ok": True,
            "status": "already_running",
            "message": "Adam Voice Mode watcher už běží.",
            "pid": current.get("pid"),
            "voice_mode": current,
        }
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_file.open("a", encoding="utf-8")
    command_args = [str(project_root / ".venv" / "bin" / "python"), str(script_path), "--poll", "0.5"]
    bridge_env = environ.get("ADAM_VOICE_TERMINAL_BRIDGE", "").strip().lower()
    bridge_enabled = terminal_bridge if terminal_bridge is not None else bridge_env not in {"0", "false", "no", "ne"}
    if bridge_enabled:
        command_args.append("--terminal-bridge")
    try:
        process = launcher(
            command_args,
            cwd=str(project_root),
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        log_handle.close()
    except OSError as exc:
        log_handle.close()
        return {"ok": False, "status": "watcher_failed", "message": f"Adam Voice Mode watcher se nepodařilo spustit: {exc}"}
    pid = int(getattr(process, "pid", 0) or 0)
    poll = getattr(process, "poll", None)
    if callable(poll):
        sleeper(0.35)
        returncode = poll()
        if returncode is not None:
            status_writer(state="stopped", message=f"Adam Voice Mode watcher po startu hned skončil (exit {returncode}).", pid=pid)
            try:
                recent_log = "\n".join(log_file.read_text(encoding="utf-8").splitlines()[-20:])
            except OSError:
                recent_log = ""
            return {
                "ok": False,
                "status": "watcher_exited",
                "message": "Adam Voice Mode watcher po startu hned skončil. Zkontroluj log v Cockpitu.",
                "pid": pid,
                "returncode": returncode,
                "log": str(path_formatter(log_file)),
                "recent_log": recent_log,
            }
    status_writer(state="starting", message="Adam Voice Mode watcher se spouští.", pid=pid)
    return {
        "ok": True,
        "status": "started",
        "message": "Adam Voice Mode watcher spuštěn. Teď můžeš nahrávat hlasové pokyny.",
        "pid": pid,
        "log": str(path_formatter(log_file)),
        "terminal_bridge": bridge_enabled,
        "voice_mode": status_loader(stale_after_seconds=60.0),
    }


def stop_voice_mode_watcher(
    *,
    status_loader: Callable[..., dict[str, Any]],
    status_writer: Callable[..., dict[str, Any]],
    pid_checker: Callable[[int], bool],
    killer: Callable[[int, int], None] = os.kill,
) -> dict[str, Any]:
    current = status_loader(stale_after_seconds=60.0)
    pid = int(current.get("pid") or 0)
    if not current.get("running") or not pid_checker(pid):
        status_writer(state="stopped", message="Adam Voice Mode watcher neběží.", pid=pid)
        return {
            "ok": True,
            "status": "already_stopped",
            "message": "Adam Voice Mode watcher neběží.",
            "voice_mode": status_loader(),
        }
    try:
        killer(pid, signal.SIGTERM)
    except OSError as exc:
        return {"ok": False, "status": "stop_failed", "message": f"Adam Voice Mode watcher se nepodařilo zastavit: {exc}", "pid": pid}
    status_writer(state="stopped", message="Adam Voice Mode watcher byl zastaven z Cockpitu.", pid=pid)
    return {
        "ok": True,
        "status": "stopped",
        "message": "Adam Voice Mode watcher zastaven.",
        "pid": pid,
        "voice_mode": status_loader(),
    }


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
