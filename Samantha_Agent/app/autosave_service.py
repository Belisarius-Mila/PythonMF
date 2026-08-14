from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.autosave_status import autosave_status as read_autosave_runtime_status
from scripts.cleanup_session_autosave import (
    CONFIRM_TEXT as AUTOSAVE_CLEANUP_CONFIRM_TEXT,
    apply_cleanup as apply_session_autosave_cleanup,
    build_cleanup_plan as build_session_autosave_cleanup_plan,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SESSION_AUTOSAVE_DIR = PROJECT_ROOT / "data" / "session_autosave"


def latest_autosave_metadata(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_dir():
        return _empty_metadata(path, "Autosave slozka zatim neexistuje.")
    files = [
        item
        for item in path.iterdir()
        if item.is_file()
        and item.name.startswith("session_")
        and item.suffix.lower() in {".txt", ".jsonl"}
    ]
    if not files:
        return _empty_metadata(path, "V autosave slozce nejsou zadne TXT/JSONL snapshoty.")
    latest = max(files, key=lambda item: item.stat().st_mtime)
    modified = latest.stat().st_mtime
    return {
        "ok": True,
        "message": "Autosave metadata nactena bez cteni obsahu logu.",
        "dir": _display_path(path),
        "file_count": len(files),
        "latest_file": latest.name,
        "latest_modified_at": datetime.fromtimestamp(modified).isoformat(timespec="seconds"),
        "latest_age_seconds": max(0, int(time.time() - modified)),
    }


def session_autosave_cleanup_action(
    payload: dict[str, Any],
    *,
    autosave_dir: Path = SESSION_AUTOSAVE_DIR,
    autosave_runtime_getter: Callable[..., Any] = read_autosave_runtime_status,
) -> dict[str, Any]:
    retention_days = _bounded_int(payload.get("retention_days"), default=0, minimum=0, maximum=30)
    keep_latest = _bounded_int(payload.get("keep_latest_snapshots"), default=12, minimum=0, maximum=200)
    plan = build_session_autosave_cleanup_plan(
        autosave_dir=autosave_dir,
        retention_days=retention_days,
        keep_latest_snapshots=keep_latest,
    )
    plan_dict = _cleanup_plan_dict(plan)
    runtime = autosave_runtime_dict(
        autosave_runtime_getter(latest_info_path=autosave_dir / "latest_info.txt")
    )
    runtime_note = ""
    if runtime["watcher_count"] != 1:
        runtime_note = f" Pozor: autosave watcherů běží {runtime['watcher_count']}, očekáván je právě jeden."
    if not bool(payload.get("apply")):
        return {
            "ok": True,
            "status": "dry_run",
            "applied": False,
            "message": (
                f"Dry-run: ke smazání {plan.delete_count} autosave souborů, "
                f"odhad uvolnění {plan_dict['reclaim_gib']} GiB.{runtime_note}"
            ),
            "confirmation_text": AUTOSAVE_CLEANUP_CONFIRM_TEXT,
            "plan": plan_dict,
            "runtime": runtime,
            "safety_note": "Obsah autosave logů se nečetl; kontrolují se jen názvy a velikosti.",
        }
    if str(payload.get("confirmation_text", "")) != AUTOSAVE_CLEANUP_CONFIRM_TEXT:
        return {
            "ok": False,
            "status": "confirmation_required",
            "applied": False,
            "message": "Úklid autosave vyžaduje potvrzení v Cockpitu.",
            "confirmation_text": AUTOSAVE_CLEANUP_CONFIRM_TEXT,
            "plan": plan_dict,
            "runtime": runtime,
        }
    removed = apply_session_autosave_cleanup(plan)
    return {
        "ok": True,
        "status": "applied",
        "applied": True,
        "removed": removed,
        "message": f"Úklid autosave hotov: smazáno {removed} starých snapshotů.",
        "plan": plan_dict,
        "runtime": runtime,
        "safety_note": (
            "Ponechané jsou aktuální latest soubory a nastavený počet "
            "nejnovějších časových snapshotů."
        ),
    }


def autosave_runtime_dict(status: Any) -> dict[str, Any]:
    watcher_pids = tuple(getattr(status, "watcher_pids", ()) or ())
    warning = " ".join(str(getattr(status, "warning", "") or "").split())[:300]
    return {
        "ok": bool(getattr(status, "ok", False)),
        "watcher_running": bool(getattr(status, "watcher_running", False)),
        "watcher_count": int(getattr(status, "watcher_count", len(watcher_pids)) or 0),
        "disk_free_gib": getattr(status, "disk_free_gib", None),
        "disk_state": str(getattr(status, "disk_state", "unknown") or "unknown"),
        "warning": warning,
    }


def _cleanup_plan_dict(plan: Any) -> dict[str, Any]:
    plan_dict = asdict(plan)
    delete_files = plan_dict.get("delete_files", [])
    plan_dict["delete_files_sample"] = delete_files[:12]
    plan_dict["delete_files_omitted"] = max(0, len(delete_files) - 12)
    plan_dict["delete_files"] = []
    plan_dict["reclaim_gib"] = round(int(plan_dict.get("reclaim_bytes", 0)) / 1024 / 1024 / 1024, 2)
    return plan_dict


def _empty_metadata(path: Path, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "message": message,
        "dir": _display_path(path),
        "file_count": 0,
        "latest_file": "",
        "latest_modified_at": "",
        "latest_age_seconds": None,
    }


def _bounded_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(parsed, maximum))


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)
