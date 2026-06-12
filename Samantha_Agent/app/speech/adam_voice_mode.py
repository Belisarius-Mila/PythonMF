from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from agents import Agent, Runner
from dotenv import load_dotenv

from app.speech.report import speak_report
from app.speech.terminal_bridge import deliver_voice_command_to_terminal
from app.speech.voice_inbox import (
    VOICE_COMMAND_INBOX_DIR,
    VoiceCommand,
    format_voice_command_for_adam,
    latest_voice_command_signature,
    voice_command_to_dict,
    wait_for_latest_voice_command,
)


ADAM_VOICE_MODE_STATUS_PATH = VOICE_COMMAND_INBOX_DIR / "adam_voice_mode_status.json"
ADAM_PENDING_COMMAND_PATH = VOICE_COMMAND_INBOX_DIR / "pending_for_adam.json"
ADAM_VOICE_HISTORY_PATH = VOICE_COMMAND_INBOX_DIR / "adam_voice_history.jsonl"
ADAM_LAST_RESPONSE_PATH = VOICE_COMMAND_INBOX_DIR / "last_adam_response.json"
CODEX_APPROVAL_REQUEST_PATH = VOICE_COMMAND_INBOX_DIR / "codex_approval_request.json"
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DIRECT_RESPONSE_INSTRUCTIONS = """
Jsi Adam v hlasovém režimu Samantha Cockpitu.
Odpovídej česky, krátce, lidsky a přímo.
Když máš něco říct konkrétní osobě, oslov ji přímo.
Neopakuj uživateli jeho diktovaný text.
Neprováděj žádné externí akce, nemaž, neposílej, neplať, necommituj.
Pokud jde jen o společenskou nebo konverzační odpověď, odpověz přirozeně.
Ber v úvahu krátkou hlasovou historii, pokud je v dotazu relevantní.
Použij maximálně dvě věty.
""".strip()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def pid_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def write_voice_mode_status(
    *,
    status_path: Path = ADAM_VOICE_MODE_STATUS_PATH,
    state: str,
    message: str,
    last_command: VoiceCommand | None = None,
    pid: int | None = None,
    started_at: str | None = None,
) -> dict[str, Any]:
    status_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "ok": True,
        "state": state,
        "message": message,
        "pid": pid if pid is not None else os.getpid(),
        "started_at": started_at or utc_now(),
        "updated_at": utc_now(),
    }
    if last_command is not None:
        payload["last_command"] = voice_command_to_dict(last_command)
    status_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def load_voice_history(
    *,
    path: Path = ADAM_VOICE_HISTORY_PATH,
    limit: int = 6,
) -> list[dict[str, Any]]:
    if limit <= 0 or not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    history: list[dict[str, Any]] = []
    for line in lines[-max(limit * 3, limit):]:
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            history.append(item)
    return history[-limit:]


def format_voice_history_for_prompt(history: list[dict[str, Any]]) -> str:
    if not history:
        return "Hlasová historie je zatím prázdná."
    lines = ["Nedávná hlasová historie:"]
    for item in history:
        user_text = str(item.get("user_text") or item.get("text") or "").strip()
        adam_response = str(item.get("adam_response") or item.get("response") or "").strip()
        if user_text:
            lines.append(f"Míla: {user_text}")
        if adam_response:
            lines.append(f"Adam: {adam_response}")
    return "\n".join(lines)


def _last_response_path_for_history(history_path: Path) -> Path:
    if history_path == ADAM_VOICE_HISTORY_PATH:
        return ADAM_LAST_RESPONSE_PATH
    return history_path.parent / "last_adam_response.json"


def save_last_adam_response(
    *,
    user_text: str,
    adam_response: str,
    route: str,
    path: Path = ADAM_LAST_RESPONSE_PATH,
) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    response_text = str(adam_response or "").strip()
    payload: dict[str, Any] = {
        "ok": True,
        "available": bool(response_text),
        "created_at": utc_now(),
        "route": str(route or "").strip(),
        "user_text": str(user_text or "").strip(),
        "adam_response": response_text,
        "path": str(path),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def load_last_adam_response(
    *,
    path: Path = ADAM_LAST_RESPONSE_PATH,
) -> dict[str, Any]:
    if not path.exists():
        return {
            "ok": True,
            "available": False,
            "message": "Zatím není uložená žádná Adamova odpověď.",
            "path": str(path),
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "available": False,
            "message": f"Poslední Adamova odpověď nejde načíst: {exc}",
            "path": str(path),
        }
    payload.setdefault("ok", True)
    payload.setdefault("available", bool(str(payload.get("adam_response") or "").strip()))
    payload.setdefault("path", str(path))
    return payload


def append_manual_voice_history_turn(
    *,
    user_text: str,
    adam_response: str,
    route: str = "codex_manual",
    path: Path = ADAM_VOICE_HISTORY_PATH,
    response_path: Path | None = None,
) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "created_at": utc_now(),
        "route": route,
        "user_text": str(user_text or "").strip(),
        "adam_response": str(adam_response or "").strip(),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    if payload["adam_response"]:
        save_last_adam_response(
            user_text=payload["user_text"],
            adam_response=payload["adam_response"],
            route=route,
            path=response_path or _last_response_path_for_history(path),
        )
    return payload


def append_voice_history_turn(
    command: VoiceCommand,
    *,
    adam_response: str,
    route: str,
    path: Path = ADAM_VOICE_HISTORY_PATH,
    response_path: Path | None = None,
) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "created_at": utc_now(),
        "route": route,
        "user_text": command.text.strip(),
        "adam_response": str(adam_response or "").strip(),
        "command": voice_command_to_dict(command),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    if payload["adam_response"]:
        save_last_adam_response(
            user_text=payload["user_text"],
            adam_response=payload["adam_response"],
            route=route,
            path=response_path or _last_response_path_for_history(path),
        )
    return payload


def save_pending_for_adam(
    command: VoiceCommand,
    *,
    reason: str,
    message: str,
    path: Path = ADAM_PENDING_COMMAND_PATH,
    history_path: Path = ADAM_VOICE_HISTORY_PATH,
) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    now = utc_now()
    payload: dict[str, Any] = {
        "ok": True,
        "pending": True,
        "status": "pending_for_adam",
        "reason": reason,
        "message": message,
        "text": command.text.strip(),
        "command": voice_command_to_dict(command),
        "voice_history": load_voice_history(path=history_path, limit=6),
        "created_at": now,
        "updated_at": now,
        "path": str(path),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def load_pending_for_adam(
    *,
    path: Path = ADAM_PENDING_COMMAND_PATH,
) -> dict[str, Any]:
    if not path.exists():
        return {
            "ok": True,
            "pending": False,
            "status": "none",
            "message": "Žádný hlasový pokyn nečeká na Adama.",
            "path": str(path),
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "pending": False,
            "status": "error",
            "message": f"Čekající hlasový pokyn nejde načíst: {exc}",
            "path": str(path),
        }
    payload.setdefault("ok", True)
    payload.setdefault("pending", payload.get("status") == "pending_for_adam")
    payload.setdefault("status", "pending_for_adam" if payload.get("pending") else "unknown")
    payload.setdefault("path", str(path))
    return payload


def mark_pending_for_adam_processed(
    *,
    adam_response: str,
    path: Path = ADAM_PENDING_COMMAND_PATH,
    history_path: Path = ADAM_VOICE_HISTORY_PATH,
) -> dict[str, Any]:
    pending = load_pending_for_adam(path=path)
    if not pending.get("ok"):
        return pending
    if not pending.get("pending"):
        pending["ok"] = False
        pending["message"] = "Žádný čekající hlasový pokyn není připravený k označení jako vyřízený."
        return pending

    now = utc_now()
    response_text = str(adam_response or "").strip()
    pending["pending"] = False
    pending["status"] = "processed_by_codex"
    pending["response"] = response_text
    pending["processed_at"] = now
    pending["updated_at"] = now
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pending, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    append_manual_voice_history_turn(
        user_text=str(pending.get("text") or ""),
        adam_response=response_text,
        route="codex_manual",
        path=history_path,
    )
    return pending


def update_pending_approval(
    *,
    decision: str,
    note: str = "",
    path: Path = ADAM_PENDING_COMMAND_PATH,
) -> dict[str, Any]:
    normalized = str(decision or "").strip().lower()
    if normalized not in {"approved", "rejected"}:
        return {
            "ok": False,
            "status": "invalid_decision",
            "message": "Neplatné rozhodnutí. Použij approved nebo rejected.",
            "path": str(path),
        }
    pending = load_pending_for_adam(path=path)
    if not pending.get("ok"):
        return pending
    if not pending.get("pending"):
        pending["ok"] = False
        pending["status"] = "no_pending_command"
        pending["message"] = "Žádný hlasový pokyn nečeká na schválení."
        return pending

    now = utc_now()
    pending["approval"] = {
        "decision": normalized,
        "decided_at": now,
        "note": str(note or "").strip(),
    }
    pending["approval_status"] = normalized
    pending["updated_at"] = now
    if normalized == "approved":
        pending["status"] = "approved_in_cockpit"
        pending["pending"] = True
        pending["message"] = "Žádost byla schválena v Cockpitu a čeká na převzetí Adamem."
    else:
        pending["status"] = "rejected_by_user"
        pending["pending"] = False
        pending["message"] = "Žádost byla v Cockpitu zamítnuta."
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pending, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return pending


def mark_matching_pending_delivered_to_terminal(
    command: VoiceCommand,
    *,
    path: Path = ADAM_PENDING_COMMAND_PATH,
) -> dict[str, Any] | None:
    pending = load_pending_for_adam(path=path)
    if not pending.get("ok") or not pending.get("pending"):
        return None
    if str(pending.get("text") or "").strip() != command.text.strip():
        return None

    now = utc_now()
    pending["pending"] = False
    pending["status"] = "processed_by_terminal_bridge"
    pending["terminal_delivered_at"] = now
    pending["updated_at"] = now
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pending, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return pending


def save_codex_approval_request(
    *,
    reason: str,
    command: str = "",
    next_step: str = "",
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


def load_voice_mode_status(
    *,
    status_path: Path = ADAM_VOICE_MODE_STATUS_PATH,
    pending_path: Path = ADAM_PENDING_COMMAND_PATH,
    history_path: Path = ADAM_VOICE_HISTORY_PATH,
    last_response_path: Path = ADAM_LAST_RESPONSE_PATH,
    codex_approval_path: Path = CODEX_APPROVAL_REQUEST_PATH,
    stale_after_seconds: float = 15.0,
) -> dict[str, Any]:
    pending_for_adam = load_pending_for_adam(path=pending_path)
    voice_history = load_voice_history(path=history_path, limit=3)
    last_adam_response = load_last_adam_response(path=last_response_path)
    codex_approval = load_codex_approval_request(path=codex_approval_path)
    last_voice_turn = voice_history[-1] if voice_history else None
    if not last_adam_response.get("available") and last_voice_turn:
        history_response = str(last_voice_turn.get("adam_response") or "").strip()
        if history_response:
            last_adam_response = {
                "ok": True,
                "available": True,
                "created_at": last_voice_turn.get("created_at"),
                "route": last_voice_turn.get("route"),
                "user_text": str(last_voice_turn.get("user_text") or "").strip(),
                "adam_response": history_response,
                "source": "voice_history",
                "path": str(last_response_path),
            }
    if not status_path.exists():
        return {
            "ok": True,
            "running": False,
            "state": "stopped",
            "message": "Adam Voice Mode watcher neběží.",
            "status_path": str(status_path),
            "pending_for_adam": pending_for_adam,
            "voice_history_count": len(voice_history),
            "last_voice_turn": last_voice_turn,
            "last_adam_response": last_adam_response,
            "codex_approval": codex_approval,
        }
    try:
        payload = json.loads(status_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "running": False,
            "state": "unknown",
            "message": f"Stav Adam Voice Mode nejde načíst: {exc}",
            "status_path": str(status_path),
            "pending_for_adam": pending_for_adam,
            "voice_history_count": len(voice_history),
            "last_voice_turn": last_voice_turn,
            "last_adam_response": last_adam_response,
            "codex_approval": codex_approval,
        }

    pid = int(payload.get("pid") or 0)
    updated_at = str(payload.get("updated_at") or "")
    age_seconds: float | None = None
    if updated_at:
        try:
            updated = datetime.fromisoformat(updated_at)
            age_seconds = max(0.0, (datetime.now(timezone.utc) - updated).total_seconds())
        except ValueError:
            age_seconds = None
    state = str(payload.get("state") or "")
    terminal_state = state in {"stopped", "timeout", "completed"}
    running = (not terminal_state) and pid_exists(pid) and (age_seconds is None or age_seconds <= stale_after_seconds)
    payload["running"] = running
    payload["stale"] = not running
    payload["age_seconds"] = age_seconds
    payload["status_path"] = str(status_path)
    payload["pending_for_adam"] = pending_for_adam
    payload["voice_history_count"] = len(voice_history)
    payload["last_voice_turn"] = last_voice_turn
    payload["last_adam_response"] = last_adam_response
    payload["codex_approval"] = codex_approval
    if not running and payload.get("state") == "listening":
        payload["state"] = "stale"
        payload["message"] = "Adam Voice Mode watcher pravděpodobně neběží nebo se dlouho neozval."
    return payload


def spoken_notice_for_command(command: VoiceCommand) -> str:
    triage = command.triage
    text = command.text.strip()
    if triage.risk in {"blocked", "needs_confirmation"}:
        return (
            "Nový hlasový pokyn vyžaduje potvrzení. "
            f"Riziko: {triage.risk}. "
            f"Text pokynu: {text}"
        )
    if triage.risk == "draft":
        return f"Nový hlasový pokyn je návrh bez přímé akce. Text pokynu: {text}"
    if triage.risk == "read_only":
        return f"Nový hlasový pokyn je bezpečný pro čtení. Text pokynu: {text}"
    return f"Nový hlasový pokyn byl přijat. Text pokynu: {text or 'bez textu'}"


def voice_command_needs_codex_work(text: str) -> bool:
    folded = " ".join(str(text or "").casefold().split())
    work_terms = (
        "najdi",
        "dohled",
        "napiš",
        "napis",
        "shrň",
        "shrn",
        "ukaž",
        "ukaz",
        "zobraz",
        "otevři",
        "otevri",
        "zkontroluj",
        "prozkoumej",
        "uprav",
        "oprav",
        "commit",
        "push",
        "git",
        "kód",
        "kod",
        "řádk",
        "radk",
        "napsali",
        "cockpit",
        "dokument",
        "projekt",
        "email",
        "e-mail",
        "reminder",
        "připom",
        "scan",
        "soubor",
        "test",
        "codex",
        "terminál",
        "terminal",
        "hlasov",
        "bridge",
        "brydž",
        "brydz",
    )
    conversational_terms = (
        "co jí řekneš",
        "co ji reknes",
        "co mu řekneš",
        "co mu reknes",
        "co jim řekneš",
        "co jim reknes",
        "pozdrav",
        "zdraví tě",
        "zdravi te",
        "řekni jí",
        "rekni ji",
        "řekni mu",
        "rekni mu",
    )
    if any(term in folded for term in conversational_terms):
        return False
    return any(term in folded for term in work_terms)


def pending_reason_for_command(command: VoiceCommand) -> str | None:
    if not command.ok:
        return None
    if command.triage.risk == "outbound_confirmation":
        return "outbound_confirmation"
    if command.triage.requires_confirmation or command.triage.risk in {"blocked", "needs_confirmation"}:
        return "requires_confirmation"
    if voice_command_needs_codex_work(command.text):
        return "codex_work"
    return None


def generate_direct_voice_response(
    text: str,
    *,
    history: list[dict[str, Any]] | None = None,
    history_path: Path = ADAM_VOICE_HISTORY_PATH,
    runner: Callable[..., Any] = Runner.run_sync,
) -> str:
    load_dotenv(PROJECT_ROOT / ".env", override=True)
    agent = Agent(
        name="AdamVoiceResponder",
        instructions=DIRECT_RESPONSE_INSTRUCTIONS,
        tools=[],
    )
    recent_history = load_voice_history(path=history_path, limit=6) if history is None else history
    prompt = (
        f"{format_voice_history_for_prompt(recent_history)}\n\n"
        "Aktuální hlasový vstup od Míly:\n"
        f"{text.strip()}"
    )
    result = runner(agent, prompt)
    response = str(getattr(result, "final_output", "") or "").strip()
    return response or "Slyším tě. Tady Adam, jsem připravený pomoct."


def build_spoken_result_for_command(
    command: VoiceCommand,
    *,
    response_generator: Callable[..., str] = generate_direct_voice_response,
    pending_path: Path | None = ADAM_PENDING_COMMAND_PATH,
    history_path: Path = ADAM_VOICE_HISTORY_PATH,
    terminal_bridge: Callable[[VoiceCommand], dict[str, Any]] | None = None,
) -> str:
    triage = command.triage
    text = command.text.strip()
    if not command.ok:
        return "Hlasový pokyn nemá použitelný text. Zkus ho prosím nahrát znovu."
    pending_reason = pending_reason_for_command(command)
    if pending_reason in {"requires_confirmation", "outbound_confirmation"}:
        if pending_reason == "outbound_confirmation":
            message = (
                "Pokyn jsem přijal a můžu připravit odchozí SMS nebo e-mail, "
                "ale odeslání navenek vyžaduje samostatné potvrzení. "
                "Nejde o blok, jen o bezpečnostní brzdu před odesláním."
            )
        else:
            message = "Pokyn jsem přijal, ale je rizikový nebo mění data. Neprovedu ho bez výslovného potvrzení v chatu."
        if pending_path is not None:
            save_pending_for_adam(
                command,
                reason=pending_reason,
                message=message,
                path=pending_path,
                history_path=history_path,
            )
        append_voice_history_turn(command, adam_response=message, route=pending_reason, path=history_path)
        return message
    if pending_reason == "codex_work":
        if terminal_bridge is not None:
            bridge_result = terminal_bridge(command)
            if bridge_result.get("ok") and bridge_result.get("verified"):
                message = "Pokyn jsem vložil do Codex terminálu. Adam ho převezme přímo tam."
                if pending_path is not None:
                    mark_matching_pending_delivered_to_terminal(command, path=pending_path)
                return message
            if bridge_result.get("ok"):
                bridge_status = str(bridge_result.get("status") or "terminal_delivery_unverified")
                bridge_message = str(bridge_result.get("message") or "Terminálový bridge pokus nahlásil úspěch, ale doručení neumím ověřit.")
                message = (
                    "Pokusil jsem se pokyn vložit do Codex terminálu, ale neumím ověřit, že se skutečně objevil. "
                    "Nechávám ho Adamovi připravený v hlasovém inboxu."
                )
                if pending_path is not None:
                    save_pending_for_adam(
                        command,
                        reason="terminal_delivery_unverified",
                        message=f"{message} Doručovací status: {bridge_status}. Detail: {bridge_message}",
                        path=pending_path,
                        history_path=history_path,
                    )
                append_voice_history_turn(command, adam_response=message, route="terminal_delivery_unverified", path=history_path)
                return message
            bridge_status = str(bridge_result.get("status") or "terminal_bridge_failed")
            bridge_reason = str(bridge_result.get("reason") or bridge_result.get("message") or "Terminálový bridge pokyn nepřevzal.")
            if bridge_status == "terminal_delivery_failed":
                message = (
                    "Pokyn jsem bezpečnostně pustil, ale technicky se mi ho nepodařilo vložit do Codex terminálu. "
                    "Nechávám ho Adamovi připravený v hlasovém inboxu."
                )
            else:
                message = (
                    "Pokyn jsem do terminálu nevložil, protože vyžaduje ruční přesnou formulaci v Codex terminálu. "
                    "Nechávám ho Adamovi připravený v hlasovém inboxu."
                )
            if pending_path is not None:
                save_pending_for_adam(
                    command,
                    reason=bridge_status,
                    message=f"{message} Důvod: {bridge_reason}",
                    path=pending_path,
                    history_path=history_path,
                )
            append_voice_history_turn(command, adam_response=message, route=bridge_status, path=history_path)
            return message
        message = "Pokyn jsem přijal. Tohle vyžaduje pracovní převzetí Adamem v Codexu, takže ho nechávám připravený v hlasovém inboxu."
        if pending_path is not None:
            save_pending_for_adam(
                command,
                reason=pending_reason,
                message=message,
                path=pending_path,
                history_path=history_path,
            )
        append_voice_history_turn(command, adam_response=message, route=pending_reason, path=history_path)
        return message
    try:
        if response_generator is generate_direct_voice_response:
            response = generate_direct_voice_response(text, history_path=history_path)
        else:
            response = response_generator(text)
        append_voice_history_turn(command, adam_response=response, route="direct_response", path=history_path)
        return response
    except Exception:
        message = "Pokyn jsem přijal, ale automatická odpověď se nepovedla. Nechávám ho připravený Adamovi k převzetí v Codexu."
        if pending_path is not None:
            save_pending_for_adam(
                command,
                reason="direct_response_failed",
                message=message,
                path=pending_path,
                history_path=history_path,
            )
        append_voice_history_turn(command, adam_response=message, route="direct_response_failed", path=history_path)
        return message


def handle_voice_command(
    command: VoiceCommand,
    *,
    speak: Callable[..., dict[str, Any]] = speak_report,
    response_generator: Callable[..., str] = generate_direct_voice_response,
    should_speak: bool = True,
    status_path: Path = ADAM_VOICE_MODE_STATUS_PATH,
    pending_path: Path | None = ADAM_PENDING_COMMAND_PATH,
    history_path: Path = ADAM_VOICE_HISTORY_PATH,
    terminal_bridge: Callable[[VoiceCommand], dict[str, Any]] | None = None,
    started_at: str | None = None,
) -> dict[str, Any]:
    spoken_result = build_spoken_result_for_command(
        command,
        response_generator=response_generator,
        pending_path=pending_path,
        history_path=history_path,
        terminal_bridge=terminal_bridge,
    )
    speech_result = {"ok": True, "message": "Hlasové oznámení vypnuté.", "transport": "disabled"}
    if should_speak:
        speech_result = speak(spoken_result, allow_local_fallback=False)
    pending = load_pending_for_adam(path=pending_path) if pending_path is not None else {"pending": False}
    state = "pending_for_adam" if pending.get("pending") else "command_ready" if command.ok else "waiting"
    status = write_voice_mode_status(
        status_path=status_path,
        state=state,
        message=spoken_result,
        last_command=command,
        started_at=started_at,
    )
    return {
        "ok": command.ok,
        "status": status,
        "speech": speech_result,
        "command": voice_command_to_dict(command),
        "notice": spoken_result,
        "response": spoken_result,
        "pending_for_adam": pending,
    }


def run_voice_mode(
    *,
    inbox_dir: Path = VOICE_COMMAND_INBOX_DIR,
    status_path: Path = ADAM_VOICE_MODE_STATUS_PATH,
    pending_path: Path | None = ADAM_PENDING_COMMAND_PATH,
    history_path: Path = ADAM_VOICE_HISTORY_PATH,
    since_now: bool = True,
    timeout_seconds: float = 0.0,
    poll_seconds: float = 1.0,
    count: int = 0,
    should_speak: bool = True,
    terminal_bridge_enabled: bool = False,
    terminal_bridge_submit: bool = True,
    printer: Callable[[str], None] = print,
) -> int:
    started_at = utc_now()
    seen = 0
    since_signature = latest_voice_command_signature(inbox_dir=inbox_dir) if since_now else None
    deadline = time.monotonic() + timeout_seconds if timeout_seconds > 0 else None
    listening_message = (
        "Adam Voice Mode poslouchá nové hlasové pokyny."
        + (" Terminálový bridge je zapnutý." if terminal_bridge_enabled else "")
    )
    write_voice_mode_status(
        status_path=status_path,
        state="listening",
        message=listening_message,
        started_at=started_at,
    )
    try:
        while True:
            if deadline is not None and time.monotonic() >= deadline:
                write_voice_mode_status(
                    status_path=status_path,
                    state="timeout",
                    message="Adam Voice Mode doběhl bez nového hlasového pokynu.",
                    started_at=started_at,
                )
                return 0
            command = wait_for_latest_voice_command(
                inbox_dir=inbox_dir,
                timeout_seconds=max(0.1, poll_seconds),
                poll_seconds=min(max(0.1, poll_seconds), 1.0),
                since_signature=since_signature,
            )
            if not command.ok and command.status == "timeout":
                write_voice_mode_status(
                    status_path=status_path,
                    state="listening",
                    message=listening_message,
                    started_at=started_at,
                )
                continue
            since_signature = latest_voice_command_signature(inbox_dir=inbox_dir)
            result = handle_voice_command(
                command,
                should_speak=should_speak,
                status_path=status_path,
                pending_path=pending_path,
                history_path=history_path,
                terminal_bridge=(
                    (lambda current_command: deliver_voice_command_to_terminal(current_command, submit=terminal_bridge_submit))
                    if terminal_bridge_enabled
                    else None
                ),
                started_at=started_at,
            )
            printer(format_voice_command_for_adam(command))
            printer("")
            printer("ADAM VOICE MODE RESPONSE:")
            printer(result["response"])
            printer("")
            seen += 1
            if count > 0 and seen >= count:
                write_voice_mode_status(
                    status_path=status_path,
                    state="completed",
                    message=f"Adam Voice Mode zpracoval {seen} hlasových pokynů.",
                    last_command=command,
                    started_at=started_at,
                )
                return 0
    except KeyboardInterrupt:
        write_voice_mode_status(
            status_path=status_path,
            state="stopped",
            message="Adam Voice Mode byl zastaven uživatelem.",
            started_at=started_at,
        )
        return 130


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Aktivní Adam Voice Mode watcher pro hlasový inbox.")
    parser.add_argument("--inbox-dir", type=Path, default=VOICE_COMMAND_INBOX_DIR)
    parser.add_argument("--status-path", type=Path, default=ADAM_VOICE_MODE_STATUS_PATH)
    parser.add_argument("--pending-path", type=Path, default=ADAM_PENDING_COMMAND_PATH)
    parser.add_argument("--history-path", type=Path, default=ADAM_VOICE_HISTORY_PATH)
    parser.add_argument("--since-now", action="store_true", default=True, help="Ignorovat existující latest pokyn a čekat na nový.")
    parser.add_argument("--include-existing", action="store_true", help="Zpracovat i aktuální latest pokyn.")
    parser.add_argument("--timeout", type=float, default=0.0, help="Celkový timeout v sekundách. 0 znamená bez limitu.")
    parser.add_argument("--poll", type=float, default=1.0, help="Interval kontroly v sekundách.")
    parser.add_argument("--count", type=int, default=0, help="Počet nových pokynů před ukončením. 0 znamená bez limitu.")
    parser.add_argument("--no-speak", action="store_true", help="Nevyslovovat oznámení nahlas.")
    parser.add_argument("--terminal-bridge", action="store_true", help="Bezpečné pracovní pokyny vložit do aktivního Codex terminálu.")
    parser.add_argument("--terminal-bridge-no-submit", action="store_true", help="Prompt do terminálu jen vložit, neodesílat Enterem.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    return run_voice_mode(
        inbox_dir=args.inbox_dir,
        status_path=args.status_path,
        pending_path=args.pending_path,
        history_path=args.history_path,
        since_now=not args.include_existing,
        timeout_seconds=args.timeout,
        poll_seconds=args.poll,
        count=args.count,
        should_speak=not args.no_speak,
        terminal_bridge_enabled=args.terminal_bridge,
        terminal_bridge_submit=not args.terminal_bridge_no_submit,
    )


if __name__ == "__main__":
    raise SystemExit(main())
