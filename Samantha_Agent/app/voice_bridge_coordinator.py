"""Command routing orchestration for Samantha Cockpit VoiceBridge."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.documents.vault import append_jsonl, relative_to_project, safe_text
from app.speech.adam_voice_mode import (
    ADAM_PENDING_COMMAND_PATH,
    ADAM_VOICE_HISTORY_PATH,
    append_voice_history_turn,
    save_pending_for_adam,
)
from app.speech import TranscriptionError
from app.speech.terminal_bridge import assess_terminal_bridge, build_codex_terminal_prompt
from app.speech.voice_inbox import (
    VOICE_COMMAND_INBOX_DIR,
    VoiceCommand,
    parse_voice_command_file,
    voice_command_to_dict,
)


VoiceResult = dict[str, Any]
VOICE_FRONTEND_EVENTS_PATH = VOICE_COMMAND_INBOX_DIR / "frontend_events.jsonl"
VOICE_DELIVERY_TRANSPORT_ENV = "ADAM_VOICE_TRANSPORT"


@dataclass(frozen=True)
class VoiceBridgeCommandDependencies:
    """Adapters used by the coordinator without owning transport or persistence."""

    save_command: Callable[..., VoiceResult]
    load_voice_mode: Callable[[], VoiceResult]
    deliver_inline: Callable[..., VoiceResult]
    record_transcription_failure: Callable[..., None]
    sanitize_text: Callable[[str], str]


def save_voice_command_to_inbox(
    transcription: VoiceResult,
    *,
    inbox_dir: Path = VOICE_COMMAND_INBOX_DIR,
    now: datetime | None = None,
) -> VoiceResult:
    """Persist a normalized command and its private inbox index entry."""
    text = safe_text(str(transcription.get("text", "") or "")).strip()
    if not text:
        raise ValueError("Chybí přepsaný text hlasového pokynu.")

    created_at = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    stamp = created_at.strftime("%Y%m%d_%H%M%S")
    inbox_dir.mkdir(parents=True, exist_ok=True)
    command_path = inbox_dir / f"voice_command_{stamp}.md"
    counter = 2
    while command_path.exists():
        command_path = inbox_dir / f"voice_command_{stamp}_{counter}.md"
        counter += 1

    content = (
        "# Voice command\n\n"
        f"Created at: {created_at.isoformat()}\n"
        "Source: Samantha Cockpit / Hlasový pokyn\n"
        "Status: transcribed_only_not_executed\n\n"
        "## Text\n\n"
        f"{text}\n"
    )
    command_path.write_text(content, encoding="utf-8")
    latest_path = inbox_dir / "latest_voice_command.md"
    latest_path.write_text(content, encoding="utf-8")

    record = {
        "created_at": created_at.isoformat(),
        "path": str(relative_to_project(command_path)),
        "latest_path": str(relative_to_project(latest_path)),
        "text_chars": len(text),
        "status": "transcribed_only_not_executed",
    }
    append_jsonl(inbox_dir / "index.jsonl", record)
    return {
        "saved": True,
        "voice_command_path": str(relative_to_project(command_path)),
        "latest_voice_command_path": str(relative_to_project(latest_path)),
    }


def record_voice_delivery_attempt(
    *,
    command: VoiceCommand,
    bridge_result: VoiceResult,
    delivery_status: str,
    message: str,
    inbox_dir: Path = VOICE_COMMAND_INBOX_DIR,
) -> None:
    """Append a private metadata-only delivery attempt record."""
    try:
        append_jsonl(
            inbox_dir / "delivery_attempts.jsonl",
            {
                "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                "command_created_at": command.created_at,
                "command_path": str(relative_to_project(Path(command.path))),
                "text_chars": len(command.text.strip()),
                "delivery_status": delivery_status,
                "bridge_status": str(bridge_result.get("status") or ""),
                "ok": bool(bridge_result.get("ok")),
                "verified": bool(bridge_result.get("verified")),
                "voice_transport": str(bridge_result.get("voice_transport") or ""),
                "delivery_method": str(bridge_result.get("delivery_method") or ""),
                "target_tty": str(bridge_result.get("target_tty") or ""),
                "target_ttys": bridge_result.get("target_ttys") or [],
                "message": safe_text(message)[:800],
            },
        )
    except OSError:
        return


def record_voice_delivery_issue_for_cockpit(
    *,
    command: VoiceCommand,
    bridge_result: VoiceResult,
    delivery_status: str,
    message: str,
    pending_path: Path = ADAM_PENDING_COMMAND_PATH,
    history_path: Path = ADAM_VOICE_HISTORY_PATH,
) -> None:
    """Keep an unverified or failed delivery visible in the pending state."""
    detail = str(bridge_result.get("reason") or bridge_result.get("message") or "").strip()
    pending_message = message if not detail else f"{message} Detail: {detail}"
    pending_reason = (
        "terminal_delivery_pending_reply"
        if delivery_status == "voice_command_delivery_unverified"
        else delivery_status
    )
    try:
        save_pending_for_adam(
            command,
            reason=pending_reason,
            message=pending_message,
            path=pending_path,
            history_path=history_path,
        )
        append_voice_history_turn(command, adam_response=message, route=pending_reason, path=history_path)
    except OSError:
        return


def deliver_saved_voice_command_inline(
    *,
    inbox_dir: Path,
    configured_bridge: Callable[[VoiceCommand], VoiceResult],
    terminal_bridge: Callable[..., VoiceResult] | None = None,
    pending_path: Path = ADAM_PENDING_COMMAND_PATH,
    history_path: Path = ADAM_VOICE_HISTORY_PATH,
    attempt_recorder: Callable[..., None] = record_voice_delivery_attempt,
    issue_recorder: Callable[..., None] = record_voice_delivery_issue_for_cockpit,
) -> VoiceResult:
    """Run the explicit inline fallback and record its verified outcome."""
    try:
        command = parse_voice_command_file(inbox_dir / "latest_voice_command.md")
    except OSError as exc:
        return {
            "voice_delivery_status": "voice_command_not_loaded",
            "voice_delivery": {"ok": False, "message": str(exc)},
            "voice_delivery_message": f"Hlasový pokyn byl uložen, ale nejde načíst pro okamžité předání: {exc}",
        }

    bridge = terminal_bridge or configured_bridge
    bridge_result = bridge(command)
    if bridge_result.get("ok") and bridge_result.get("verified"):
        status = "voice_command_delivered"
        message = "Hlasový pokyn byl uložen a předán přímo do Codexu."
    elif bridge_result.get("ok"):
        status = "voice_command_delivery_unverified"
        message = "Zpráva byla vložena do hlasového inboxu. Čekám na Adamovu odpověď."
    else:
        bridge_status = str(bridge_result.get("status") or "voice_command_delivery_failed")
        bridge_message = str(bridge_result.get("reason") or bridge_result.get("message") or "bez detailu")
        status = bridge_status
        message = f"Hlasový pokyn byl uložen, ale okamžité předání do Codexu neproběhlo: {bridge_message}"
    attempt_recorder(
        command=command,
        bridge_result=bridge_result,
        delivery_status=status,
        message=message,
        inbox_dir=inbox_dir,
    )
    if status != "voice_command_delivered":
        issue_recorder(
            command=command,
            bridge_result=bridge_result,
            delivery_status=status,
            message=message,
            pending_path=pending_path,
            history_path=history_path,
        )
    return {
        "voice_delivery_status": status,
        "voice_delivery": bridge_result,
        "voice_delivery_message": message,
    }


def selected_voice_delivery_transport(
    *,
    environ: dict[str, str] | os._Environ[str] = os.environ,
    env_name: str = VOICE_DELIVERY_TRANSPORT_ENV,
) -> str:
    transport = environ.get(env_name, "local_tty").strip().lower()
    if transport in {"local", "local_tty", "tty", "mac", "mac_tty", "terminal"}:
        return "local_tty"
    if transport in {"screen", "ssh", "sslh", "managed", "managed_screen"}:
        return "managed_screen"
    return "managed_screen"


def deliver_voice_command_via_managed_screen(
    command: VoiceCommand,
    *,
    starter: Callable[[], VoiceResult],
    ready_waiter: Callable[[], VoiceResult],
    screen_deliverer: Callable[..., VoiceResult],
    submit: bool = True,
) -> VoiceResult:
    """Start or reuse the managed Adam screen and deliver one safe prompt."""
    decision = assess_terminal_bridge(command)
    if not decision.get("ok"):
        return {**decision, "voice_transport": "managed_screen", "command": voice_command_to_dict(command)}
    start_result = starter()
    if not start_result.get("ok"):
        return {
            "ok": False,
            "status": "managed_screen_start_failed",
            "message": str(start_result.get("message") or "Spravovanou Adamovu screen relaci se nepodařilo spustit."),
            "voice_transport": "managed_screen",
            "start": start_result,
            "decision": decision,
            "command": voice_command_to_dict(command),
        }
    ready_result: VoiceResult = {"ready": True, "message": "Spravovaná Adamova relace už běžela."}
    if start_result.get("status") in {"start_requested", "restart_requested"}:
        ready_result = ready_waiter()
    prompt = build_codex_terminal_prompt(command)
    delivery = screen_deliverer(prompt, submit=submit)
    message = str(delivery.get("message") or "")
    if delivery.get("ok") and not ready_result.get("ready", True):
        ready_message = str(ready_result.get("message") or "připravenost se nepodařilo ověřit")
        message = f"{message} Pozor: {ready_message}"
    return {
        **delivery,
        "message": message or ("Pokyn byl vložen do spravované Adamovy screen relace." if delivery.get("ok") else "Doručení do spravované Adamovy screen relace selhalo."),
        "voice_transport": "managed_screen",
        "prompt": prompt,
        "decision": decision,
        "start": start_result,
        "ready": ready_result,
        "command": voice_command_to_dict(command),
    }


def deliver_voice_command_by_configured_transport(
    command: VoiceCommand,
    *,
    transport: str,
    local_deliverer: Callable[..., VoiceResult],
    managed_deliverer: Callable[..., VoiceResult],
    submit: bool = True,
) -> VoiceResult:
    if transport == "local_tty":
        result = local_deliverer(command, submit=submit)
        return {**result, "voice_transport": "local_tty"}
    return managed_deliverer(command, submit=submit)


def record_voice_transcription_failure(
    *,
    message: str,
    events_path: Path = VOICE_FRONTEND_EVENTS_PATH,
    status: str = "transcription_failed",
) -> None:
    try:
        append_jsonl(
            events_path,
            {
                "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                "kind": "backend_transcribe_failed",
                "detail": {
                    "ok": False,
                    "status": status,
                    "step": "transcribe",
                    "error": safe_text(message)[:500],
                },
            },
        )
    except OSError:
        return


def watcher_will_deliver_result(voice_mode: VoiceResult) -> VoiceResult:
    """Describe the watcher-owned route without attempting inline delivery."""
    return {
        "voice_delivery_status": "watcher_will_deliver",
        "voice_delivery": {
            "ok": True,
            "status": "watcher_running",
            "message": "Běžící Adam Voice Mode watcher pokyn převezme z hlasového inboxu.",
        },
        "voice_delivery_message": (
            "Zpráva byla vložena do hlasového inboxu. "
            "Běžící watcher ji předá Adamovi."
        ),
        "voice_mode": voice_mode,
    }


def coordinate_transcribed_voice_command(
    payload: VoiceResult,
    *,
    dependencies: VoiceBridgeCommandDependencies,
    inbox_dir: Path,
    pending_path: Path,
    history_path: Path,
    transcriber: Callable[..., VoiceResult],
    terminal_bridge: Callable[..., VoiceResult] | None = None,
) -> VoiceResult:
    """Transcribe, persist and select exactly one owner for command delivery."""
    try:
        result = transcriber(
            str(payload.get("audio_base64", "")),
            mime_type=str(payload.get("mime_type", "")),
            language=str(payload.get("language", "cs") or "cs"),
        )
        result.update(dependencies.save_command(result, inbox_dir=inbox_dir))
        if terminal_bridge is None:
            voice_mode = dependencies.load_voice_mode()
            if voice_mode.get("running"):
                result.update(watcher_will_deliver_result(voice_mode))
                result["message"] = result["voice_delivery_message"]
                return result
        result.update(
            dependencies.deliver_inline(
                inbox_dir=inbox_dir,
                terminal_bridge=terminal_bridge,
                pending_path=pending_path,
                history_path=history_path,
            )
        )
        result["message"] = result.get("voice_delivery_message") or "Hlasový pokyn byl přepsán a uložen pro Codex."
        return result
    except TranscriptionError as exc:
        dependencies.record_transcription_failure(message=str(exc))
        return {
            "ok": False,
            "message": f"Přepis hlasu selhal: {exc}",
            "status": "transcription_failed",
        }
    except OSError as exc:
        return {
            "ok": False,
            "message": f"Přepis se povedl, ale uložení hlasového pokynu selhalo: {exc}",
            "status": "voice_inbox_save_failed",
        }
    except ValueError as exc:
        return {
            "ok": False,
            "message": f"Přepis se povedl, ale hlasový pokyn nejde uložit: {exc}",
            "status": "voice_inbox_save_failed",
        }


def coordinate_text_voice_command(
    payload: VoiceResult,
    *,
    dependencies: VoiceBridgeCommandDependencies,
    inbox_dir: Path,
    pending_path: Path,
    history_path: Path,
    terminal_bridge: Callable[..., VoiceResult] | None = None,
) -> VoiceResult:
    """Persist a text command and select watcher or inline delivery ownership."""
    text = dependencies.sanitize_text(str(payload.get("text", "") or "")).strip()
    if not text:
        return {
            "ok": False,
            "message": "Chybí text hlasového pokynu.",
            "status": "empty_voice_text",
        }
    try:
        result = {
            "ok": True,
            "text": text,
            "message": "Textový hlasový pokyn byl uložen pro Codex.",
            "status": "voice_text_saved",
        }
        result.update(dependencies.save_command({"text": text}, inbox_dir=inbox_dir))
        voice_mode = dependencies.load_voice_mode()
        if terminal_bridge is None and voice_mode.get("running"):
            result.update(watcher_will_deliver_result(voice_mode))
            result["message"] = result["voice_delivery_message"]
            return result
        result.update(
            dependencies.deliver_inline(
                inbox_dir=inbox_dir,
                terminal_bridge=terminal_bridge,
                pending_path=pending_path,
                history_path=history_path,
            )
        )
        result["message"] = result.get("voice_delivery_message") or result["message"]
        return result
    except OSError as exc:
        return {
            "ok": False,
            "message": f"Uložení textového hlasového pokynu selhalo: {exc}",
            "status": "voice_inbox_save_failed",
        }
    except ValueError as exc:
        return {
            "ok": False,
            "message": f"Textový hlasový pokyn nejde uložit: {exc}",
            "status": "voice_inbox_save_failed",
        }
