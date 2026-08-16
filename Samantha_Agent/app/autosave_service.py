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
    filesystem_free_bytes,
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
    disk_free_getter: Callable[[Path], int] = filesystem_free_bytes,
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
                f"logická velikost {plan_dict['logical_gib']} GiB a fyzická alokace "
                f"{plan_dict['allocated_gib']} GiB. Skutečná změna volného místa se změří "
                f"až po potvrzeném úklidu.{runtime_note}"
            ),
            "confirmation_text": AUTOSAVE_CLEANUP_CONFIRM_TEXT,
            "plan": plan_dict,
            "runtime": runtime,
            "disk_measurement": _disk_measurement_dict(),
            "safety_note": "Obsah autosave logů se nečetl; kontrolují se jen názvy a velikosti.",
            "measurement_note": (
                "Alokované bloky mohou být na APFS sdílené; skutečný zisk ukáže pouze "
                "rozdíl volného místa před a po úklidu."
            ),
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
    disk_free_before = disk_free_getter(autosave_dir)
    removed = apply_session_autosave_cleanup(plan)
    disk_free_after = disk_free_getter(autosave_dir)
    disk_measurement = _disk_measurement_dict(before=disk_free_before, after=disk_free_after)
    runtime_after = autosave_runtime_dict(
        autosave_runtime_getter(latest_info_path=autosave_dir / "latest_info.txt")
    )
    return {
        "ok": True,
        "status": "applied",
        "applied": True,
        "removed": removed,
        "message": (
            f"Úklid autosave hotov: smazáno {removed} starých snapshotů; skutečná změna "
            f"volného místa {disk_measurement['free_change_gib']:+.2f} GiB."
        ),
        "plan": plan_dict,
        "runtime": runtime_after,
        "disk_measurement": disk_measurement,
        "safety_note": (
            "Ponechané jsou aktuální latest soubory a nastavený počet "
            "nejnovějších časových snapshotů."
        ),
        "measurement_note": (
            "Logická velikost a alokované bloky jsou popis kandidátů; skutečný výsledek "
            "je změřený rozdílem volného místa filesystemu."
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
    plan_dict["logical_gib"] = _bytes_to_gib(plan_dict.get("logical_bytes"))
    plan_dict["allocated_gib"] = _bytes_to_gib(plan_dict.get("allocated_bytes"))
    return plan_dict


def _disk_measurement_dict(*, before: int | None = None, after: int | None = None) -> dict[str, Any]:
    change = after - before if before is not None and after is not None else None
    return {
        "free_before_bytes": before,
        "free_after_bytes": after,
        "free_change_bytes": change,
        "free_before_gib": _bytes_to_gib(before),
        "free_after_gib": _bytes_to_gib(after),
        "free_change_gib": _bytes_to_gib(change),
    }


def _bytes_to_gib(value: Any) -> float | None:
    if value is None:
        return None
    return round(int(value) / 1024 / 1024 / 1024, 3)


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
