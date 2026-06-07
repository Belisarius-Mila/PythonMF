from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.speech.terminal_bridge import (
    CURRENT_CODEX_TTY_PATH,
    deliver_prompt_to_terminal,
    deliver_prompt_to_vscode,
    discover_codex_ttys,
    load_marked_codex_tty,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ADAM_SERVICE_DIR = PROJECT_ROOT / "data" / "private" / "adam_text_bridge"
ADAM_REQUESTS_DIR = ADAM_SERVICE_DIR / "requests"
ADAM_SERVICE_SESSION = "samantha_adam"
ADAM_SCREEN_ENTRY_SCRIPT = PROJECT_ROOT / "scripts" / "samantha_screen_entry.sh"
ADAM_REPLY_SCRIPT = ".venv/bin/python scripts/adam_voice_reply.py"
SCREEN_CLEAR_INPUT = "\x15"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def compact_text(value: str, *, max_chars: int = 8000) -> str:
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", str(value or ""))
    compact = "\n".join(" ".join(line.split()) for line in cleaned.splitlines()).strip()
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1].rstrip() + "…"


def screen_input_text(value: str, *, max_chars: int = 12000) -> str:
    return " ".join(compact_text(value, max_chars=max_chars).split())


def adam_request_path(request_id: str, *, requests_dir: Path = ADAM_REQUESTS_DIR) -> Path:
    safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", str(request_id or ""))
    return requests_dir / f"{safe_id}.json"


def make_adam_request_id(now: str | None = None) -> str:
    stamp = (now or datetime.now().strftime("%Y%m%d_%H%M%S_%f")).replace(":", "").replace("-", "")
    return f"janicka_{stamp}"


def screen_session_exists(
    session_name: str = ADAM_SERVICE_SESSION,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> bool:
    try:
        completed = runner(["screen", "-ls"], capture_output=True, text=True, timeout=4, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False
    output = f"{completed.stdout}\n{completed.stderr}"
    return f".{session_name}" in output


def adam_service_status(
    *,
    session_name: str = ADAM_SERVICE_SESSION,
    screen_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    codex_tty_discoverer: Callable[[], list[str]] = discover_codex_ttys,
    marker_path: Path = CURRENT_CODEX_TTY_PATH,
    requests_dir: Path = ADAM_REQUESTS_DIR,
) -> dict[str, Any]:
    running = screen_session_exists(session_name=session_name, runner=screen_runner)
    try:
        codex_ttys = codex_tty_discoverer()
    except Exception:
        codex_ttys = []
    marked_tty = load_marked_codex_tty(marker_path)
    pending = 0
    answered = 0
    if requests_dir.exists():
        for path in requests_dir.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if payload.get("answer"):
                answered += 1
            elif payload.get("status") in {"queued", "delivered"}:
                pending += 1
    if running and marked_tty:
        state = "running"
        message = "Adam běží a má označenou Codex relaci."
    elif running:
        state = "running_without_marker"
        message = "Adam běží, ale nemá ověřený marker cílové Codex relace."
    else:
        state = "stopped"
        message = "Adam zatím neběží."
    return {
        "ok": True,
        "running": running,
        "state": state,
        "message": message,
        "session_name": session_name,
        "marked_tty": marked_tty,
        "codex_ttys": codex_ttys,
        "pending_count": pending,
        "answered_count": answered,
    }


def start_adam_service(
    *,
    session_name: str = ADAM_SERVICE_SESSION,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    entry_script: Path = ADAM_SCREEN_ENTRY_SCRIPT,
) -> dict[str, Any]:
    if screen_session_exists(session_name=session_name, runner=runner):
        return {
            "ok": True,
            "status": "already_running",
            "message": "Adam už běží.",
            "session_name": session_name,
        }
    if not entry_script.exists():
        return {
            "ok": False,
            "status": "missing_entry_script",
            "message": f"Chybí startovací skript Adama: {entry_script}",
            "session_name": session_name,
        }
    env = os.environ.copy()
    env.update(
        {
            "SAMANTHA_MARK_VOICE_TTY": "1",
            "SAMANTHA_MANAGED_ADAM": "1",
            "LANG": "cs_CZ.UTF-8",
            "LC_ALL": "cs_CZ.UTF-8",
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
        }
    )
    try:
        completed = runner(
            ["screen", "-dmS", session_name, str(entry_script)],
            cwd=str(PROJECT_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "ok": False,
            "status": "start_failed",
            "message": f"Adama se nepodařilo spustit: {exc}",
            "session_name": session_name,
        }
    if completed.returncode != 0:
        return {
            "ok": False,
            "status": "start_failed",
            "message": (completed.stderr or completed.stdout or "Start screen relace selhal.").strip(),
            "returncode": completed.returncode,
            "session_name": session_name,
        }
    return {
        "ok": True,
        "status": "start_requested",
        "message": "Adam se spouští.",
        "session_name": session_name,
    }


def stop_adam_service(
    *,
    confirmed: bool,
    session_name: str = ADAM_SERVICE_SESSION,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    if not confirmed:
        return {
            "ok": False,
            "status": "confirmation_required",
            "message": "Zastavení Adama vyžaduje potvrzení.",
        }
    if not screen_session_exists(session_name=session_name, runner=runner):
        return {
            "ok": True,
            "status": "already_stopped",
            "message": "Adam neběží.",
            "session_name": session_name,
        }
    try:
        completed = runner(["screen", "-S", session_name, "-X", "quit"], capture_output=True, text=True, timeout=8, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "ok": False,
            "status": "stop_failed",
            "message": f"Adama se nepodařilo zastavit: {exc}",
            "session_name": session_name,
        }
    if completed.returncode != 0:
        return {
            "ok": False,
            "status": "stop_failed",
            "message": (completed.stderr or completed.stdout or "Zastavení screen relace selhalo.").strip(),
            "returncode": completed.returncode,
            "session_name": session_name,
        }
    return {
        "ok": True,
        "status": "stopped",
        "message": "Adam byl zastaven.",
        "session_name": session_name,
    }


def restart_adam_service(
    *,
    confirmed: bool,
    session_name: str = ADAM_SERVICE_SESSION,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    if not confirmed:
        return {
            "ok": False,
            "status": "confirmation_required",
            "message": "Restart Adama vyžaduje potvrzení.",
        }
    stop_result = stop_adam_service(confirmed=True, session_name=session_name, runner=runner)
    if not stop_result.get("ok"):
        return stop_result
    time.sleep(0.5)
    start_result = start_adam_service(session_name=session_name, runner=runner)
    return {
        **start_result,
        "status": "restart_requested" if start_result.get("ok") else start_result.get("status"),
        "message": "Adam se restartuje." if start_result.get("ok") else start_result.get("message"),
        "stop": stop_result,
    }


def wait_for_adam_ready(
    *,
    timeout_seconds: float = 12.0,
    poll_seconds: float = 0.5,
    status_getter: Callable[[], dict[str, Any]] = adam_service_status,
) -> dict[str, Any]:
    deadline = time.monotonic() + max(0.0, timeout_seconds)
    last_status: dict[str, Any] = status_getter()
    while time.monotonic() <= deadline:
        last_status = status_getter()
        if last_status.get("running") and (last_status.get("marked_tty") or last_status.get("codex_ttys")):
            return {
                **last_status,
                "ready": True,
                "message": "Adam je připravený převzít dotaz.",
            }
        time.sleep(max(0.1, poll_seconds))
    return {
        **last_status,
        "ready": False,
        "message": "Adam se spustil, ale připravenost Codex relace se zatím nepodařilo ověřit.",
    }


def deliver_prompt_to_adam_screen(
    prompt: str,
    *,
    submit: bool = True,
    session_name: str = ADAM_SERVICE_SESSION,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    if not screen_session_exists(session_name=session_name, runner=runner):
        return {
            "ok": False,
            "status": "screen_not_running",
            "message": "Spravovaná Adamova screen relace neběží.",
            "session_name": session_name,
            "delivery_method": "managed_screen",
        }
    payload = SCREEN_CLEAR_INPUT + screen_input_text(prompt) + ("\n" if submit else "")
    try:
        completed = runner(
            ["screen", "-S", session_name, "-X", "stuff", payload],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "ok": False,
            "status": "screen_delivery_failed",
            "message": f"Dotaz se nepodařilo vložit do Adamovy screen relace: {exc}",
            "session_name": session_name,
            "delivery_method": "managed_screen",
        }
    if completed.returncode != 0:
        return {
            "ok": False,
            "status": "screen_delivery_failed",
            "message": (completed.stderr or completed.stdout or "Vložení dotazu do screen relace selhalo.").strip(),
            "returncode": completed.returncode,
            "session_name": session_name,
            "delivery_method": "managed_screen",
        }
    return {
        "ok": True,
        "status": "delivered_screen",
        "message": "Dotaz byl vložen přímo do spravované Adamovy relace.",
        "session_name": session_name,
        "delivery_method": "managed_screen",
        "verified": True,
    }


def deliver_prompt_to_visible_adam(
    prompt: str,
    *,
    submit: bool = True,
    deliverer: Callable[..., dict[str, Any]] = deliver_prompt_to_vscode,
) -> dict[str, Any]:
    return {
        **deliverer(prompt, submit=submit),
        "adam_delivery_target": "visible_vscode",
    }


def save_adam_text_request(
    *,
    message: str,
    history: list[Any] | None = None,
    request_id: str | None = None,
    requests_dir: Path = ADAM_REQUESTS_DIR,
) -> dict[str, Any]:
    clean_message = compact_text(message, max_chars=8000)
    rid = request_id or make_adam_request_id()
    path = adam_request_path(rid, requests_dir=requests_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ok": True,
        "request_id": rid,
        "status": "queued",
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "message": clean_message,
        "history": history or [],
        "path": str(path),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def build_adam_text_prompt(request: dict[str, Any]) -> str:
    request_id = str(request.get("request_id") or "")
    message = compact_text(str(request.get("message") or ""))
    history = request.get("history") if isinstance(request.get("history"), list) else []
    history_lines: list[str] = []
    for item in history[-8:]:
        if not isinstance(item, dict):
            continue
        role = compact_text(str(item.get("role", "") or ""), max_chars=20)
        content = compact_text(str(item.get("content", "") or ""), max_chars=1200)
        if role in {"user", "assistant"} and content:
            label = "Jana/Míla" if role == "user" else "Adam"
            history_lines.append(f"{label}: {content}")
    reply_command = (
        f"{ADAM_REPLY_SCRIPT} "
        f"--request-id {shlex.quote(request_id)} "
        f"--user-text {shlex.quote(message)} "
        "--route janicka_text_bridge "
        "\"STRUČNÁ ODPOVĚĎ PRO OKNO JANIČKA\""
    )
    parts = [
        "Textový dotaz z okna `Jana Adam` v Samantha Cockpitu.",
        f"Request ID: {request_id}",
        "Jana má spuštěný jen Cockpit. Codex neovládá. Ty jsi běžící Adam/Codex relace, která má dotaz převzít.",
        "Odpověz normálně v tomto Codex chatu a potom zapiš stručnou odpověď zpět do Cockpitu příkazem:",
        reply_command,
        "Bezpečnost: pokud jde o mazání, odesílání, commit, push, platbu, tajemství nebo jinou rizikovou akci, nejdřív si v chatu vyžádej potvrzení.",
    ]
    if history_lines:
        parts.append("Krátká historie z okna Janička:\n" + "\n".join(history_lines))
    parts.append("Aktuální dotaz:\n" + message)
    return "\n\n".join(parts)


def record_adam_text_reply(
    *,
    request_id: str,
    response: str,
    requests_dir: Path = ADAM_REQUESTS_DIR,
) -> dict[str, Any]:
    path = adam_request_path(request_id, requests_dir=requests_dir)
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {"request_id": request_id}
    else:
        payload = {"request_id": request_id, "created_at": utc_now()}
    payload.update(
        {
            "ok": True,
            "status": "answered",
            "answer": compact_text(response, max_chars=12000),
            "answered_at": utc_now(),
            "updated_at": utc_now(),
            "path": str(path),
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def load_adam_text_reply(
    *,
    request_id: str,
    requests_dir: Path = ADAM_REQUESTS_DIR,
) -> dict[str, Any]:
    path = adam_request_path(request_id, requests_dir=requests_dir)
    if not path.exists():
        return {
            "ok": True,
            "available": False,
            "status": "missing_request",
            "message": "Dotaz zatím není ve frontě Adama.",
            "request_id": request_id,
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "available": False,
            "status": "read_failed",
            "message": f"Odpověď Adama nejde načíst: {exc}",
            "request_id": request_id,
        }
    answer = compact_text(str(payload.get("answer") or ""), max_chars=12000)
    return {
        "ok": True,
        "available": bool(answer),
        "status": "reply_available" if answer else str(payload.get("status") or "queued"),
        "message": "Adamova odpověď je připravená." if answer else "Adam zatím neodpověděl.",
        "request_id": request_id,
        "answer": answer,
        "created_at": payload.get("created_at"),
        "answered_at": payload.get("answered_at"),
    }


def submit_adam_text_request(
    *,
    message: str,
    history: list[Any] | None = None,
    requests_dir: Path = ADAM_REQUESTS_DIR,
    starter: Callable[..., dict[str, Any]] = start_adam_service,
    ready_waiter: Callable[[], dict[str, Any]] | None = None,
    deliverer: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if deliverer is None:
        deliverer = deliver_prompt_to_terminal
    start_result = starter()
    if not start_result.get("ok"):
        request = save_adam_text_request(message=message, history=history, requests_dir=requests_dir)
        return {
            "ok": False,
            "status": "start_failed",
            "message": str(start_result.get("message") or "Adama se nepodařilo spustit."),
            "request_id": request["request_id"],
            "start": start_result,
        }
    ready_result: dict[str, Any] = {"ready": True, "message": "Adam už byl spuštěný."}
    if start_result.get("status") in {"start_requested", "restart_requested"}:
        ready_result = ready_waiter() if ready_waiter is not None else wait_for_adam_ready()
    request = save_adam_text_request(message=message, history=history, requests_dir=requests_dir)
    if not ready_result.get("ready", True):
        return {
            "ok": False,
            "status": "adam_not_ready",
            "message": str(ready_result.get("message") or "Adam zatím není připravený převzít dotaz."),
            "request_id": request["request_id"],
            "start": start_result,
            "ready": ready_result,
        }
    prompt = build_adam_text_prompt(request)
    delivery = deliverer(prompt, submit=True)
    path = Path(str(request.get("path") or ""))
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = request
        payload.update(
            {
                "status": "delivered" if delivery.get("ok") else "delivery_failed",
                "updated_at": utc_now(),
                "delivery": delivery,
                "start": start_result,
                "ready": ready_result,
            }
        )
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": bool(delivery.get("ok")),
        "status": "delivered_to_adam" if delivery.get("ok") else "delivery_failed",
        "message": "Dotaz byl předán Adamovi." if delivery.get("ok") else f"Dotaz se nepodařilo předat Adamovi: {delivery.get('message')}",
        "request_id": request["request_id"],
        "start": start_result,
        "ready": ready_result,
        "delivery": delivery,
    }
