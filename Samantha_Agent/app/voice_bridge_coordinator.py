"""Command routing orchestration for Samantha Cockpit VoiceBridge."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.speech import TranscriptionError


VoiceResult = dict[str, Any]


@dataclass(frozen=True)
class VoiceBridgeCommandDependencies:
    """Adapters used by the coordinator without owning transport or persistence."""

    save_command: Callable[..., VoiceResult]
    load_voice_mode: Callable[[], VoiceResult]
    deliver_inline: Callable[..., VoiceResult]
    record_transcription_failure: Callable[..., None]
    sanitize_text: Callable[[str], str]


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
