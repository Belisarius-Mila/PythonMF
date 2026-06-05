from __future__ import annotations

import subprocess
from typing import Any


DEFAULT_VOICE = "Zuzana"
ALLOWED_VOICES = {"Daniel", "Zuzana"}
MAX_SPEECH_CHARS = 1500
SAY_BIN = "/usr/bin/say"


class SpeechError(RuntimeError):
    """Raised when local speech synthesis or playback fails."""


def normalize_text(text: str, max_chars: int = MAX_SPEECH_CHARS) -> str:
    normalized = " ".join(str(text or "").split())
    if not normalized:
        raise SpeechError("Chybí text k přečtení.")
    if len(normalized) > max_chars:
        normalized = normalized[: max_chars - 1].rstrip() + "…"
    return normalized


def speak_text(
    text: str,
    *,
    voice: str = DEFAULT_VOICE,
    max_chars: int = MAX_SPEECH_CHARS,
    timeout_seconds: int = 45,
    runner: Any = subprocess.run,
    temp_dir: str = "/private/tmp",
) -> dict[str, Any]:
    if voice not in ALLOWED_VOICES:
        raise SpeechError(f"Nepovolený hlas: {voice}")

    spoken_text = normalize_text(text, max_chars=max_chars)
    try:
        speech = runner(
            [SAY_BIN, "-v", voice, spoken_text],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        if speech.returncode != 0:
            detail = (speech.stderr or speech.stdout or "").strip()
            raise SpeechError(detail or "Nepodařilo se přečíst text nahlas.")
    except subprocess.TimeoutExpired as exc:
        raise SpeechError(f"Hlasový výstup vypršel: {exc}") from exc
    except OSError as exc:
        raise SpeechError(f"Hlasový výstup selhal: {exc}") from exc

    return {
        "ok": True,
        "message": "Text byl přečten nahlas.",
        "voice": voice,
        "chars": len(spoken_text),
    }
