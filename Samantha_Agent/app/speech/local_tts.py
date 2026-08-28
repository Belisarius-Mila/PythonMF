from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
from typing import Any


DEFAULT_VOICE = "Zuzana"
ALLOWED_VOICES = {"Daniel", "Zuzana"}
MAX_SPEECH_CHARS = 1500
MAX_LOCAL_AUDIO_BYTES = 8 * 1024 * 1024
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


def synthesize_local_tts_m4a(
    text: str,
    *,
    voice: str = DEFAULT_VOICE,
    max_chars: int = MAX_SPEECH_CHARS,
    max_audio_bytes: int = MAX_LOCAL_AUDIO_BYTES,
    timeout_seconds: int = 45,
    runner: Any = subprocess.run,
    temp_dir: str = "/private/tmp",
) -> bytes:
    """Render local macOS speech to transient browser-playable audio."""

    if voice not in ALLOWED_VOICES:
        raise SpeechError(f"Nepovolený hlas: {voice}")

    spoken_text = normalize_text(text, max_chars=max_chars)
    try:
        with tempfile.TemporaryDirectory(prefix="samantha_local_tts_", dir=temp_dir) as working_dir:
            output_path = Path(working_dir) / "speech.m4a"
            speech = runner(
                [
                    SAY_BIN,
                    "-v",
                    voice,
                    "-o",
                    str(output_path),
                    "--file-format=m4af",
                    spoken_text,
                ],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            if speech.returncode != 0:
                detail = (speech.stderr or speech.stdout or "").strip()
                raise SpeechError(detail or "Nepodařilo se vytvořit místní hlasové audio.")
            try:
                audio = output_path.read_bytes()
            except OSError as exc:
                raise SpeechError(f"Místní hlasové audio nelze načíst: {exc}") from exc
            if not audio:
                raise SpeechError("Místní hlasové audio je prázdné.")
            if len(audio) > max_audio_bytes:
                raise SpeechError("Místní hlasové audio překročilo povolenou velikost.")
            return audio
    except subprocess.TimeoutExpired as exc:
        raise SpeechError(f"Vytvoření místního hlasového audia vypršelo: {exc}") from exc
    except OSError as exc:
        raise SpeechError(f"Vytvoření místního hlasového audia selhalo: {exc}") from exc
