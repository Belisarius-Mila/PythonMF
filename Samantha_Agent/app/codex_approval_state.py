"""Private runtime state for a pending Codex system approval."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Keep the existing private location during the VoiceBridge retirement.
CODEX_APPROVAL_REQUEST_PATH = (
    PROJECT_ROOT / "data" / "private" / "voice_inbox" / "codex_approval_request.json"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def save_codex_approval_request(
    *,
    reason: str,
    command: str = "",
    next_step: str = "",
    risk: str = "",
    confirmation_text: str = "",
    path: Path = CODEX_APPROVAL_REQUEST_PATH,
) -> dict[str, Any]:
    now = utc_now()
    payload = {
        "ok": True,
        "active": True,
        "status": "waiting_for_codex_approval",
        "reason": str(reason or "").strip()[:500],
        "command": str(command or "").strip()[:500],
        "next_step": str(next_step or "").strip()[:500],
        "risk": str(risk or "").strip()[:500],
        "confirmation_text": str(confirmation_text or "").strip()[:1000],
        "created_at": now,
        "updated_at": now,
        "path": str(path),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def clear_codex_approval_request(
    *,
    note: str = "",
    path: Path = CODEX_APPROVAL_REQUEST_PATH,
) -> dict[str, Any]:
    now = utc_now()
    previous = load_codex_approval_request(path=path)
    payload = {
        "ok": True,
        "active": False,
        "status": "cleared",
        "note": str(note or "").strip()[:500],
        "cleared_at": now,
        "updated_at": now,
        "previous": previous if previous.get("available") else {},
        "path": str(path),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def load_codex_approval_request(
    *,
    path: Path = CODEX_APPROVAL_REQUEST_PATH,
) -> dict[str, Any]:
    if not path.exists():
        return {
            "ok": True,
            "available": False,
            "active": False,
            "status": "none",
            "message": "Codex nehlásí žádné čekání na systémové potvrzení.",
            "path": str(path),
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "available": False,
            "active": False,
            "status": "error",
            "message": f"Stav Codex approval nejde načíst: {exc}",
            "path": str(path),
        }
    payload.setdefault("ok", True)
    payload.setdefault("available", True)
    payload.setdefault("active", payload.get("status") == "waiting_for_codex_approval")
    payload.setdefault("path", str(path))
    return payload
