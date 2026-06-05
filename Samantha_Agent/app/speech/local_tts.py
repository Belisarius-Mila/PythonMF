from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any


DEFAULT_VOICE = "Zuzana"
ALLOWED_VOICES = {"Zuzana"}
MAX_SPEECH_CHARS = 1500
SAY_BIN = "/usr/bin/say"
AFPLAY_BIN = "/usr/bin/afplay"


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
    temp_dir: Path | str = "/private/tmp",
) -> dict[str, Any]:
    if voice not in ALLOWED_VOICES:
        raise SpeechError(f"Nepovolený hlas: {voice}")

    spoken_text = normalize_text(text, max_chars=max_chars)
    with tempfile.NamedTemporaryFile(
        prefix="samantha_speech_",
        suffix=".aiff",
        dir=str(temp_dir),
        delete=False,
    ) as temp_file:
        temp_path = Path(temp_file.name)
    try:
        synth = runner(
            [SAY_BIN, "-v", voice, "-o", str(temp_path), spoken_text],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        if synth.returncode != 0:
            detail = (synth.stderr or synth.stdout or "").strip()
            raise SpeechError(detail or "Nepodařilo se vytvořit hlasový soubor.")

        play = runner(
            [AFPLAY_BIN, str(temp_path)],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        if play.returncode != 0:
            detail = (play.stderr or play.stdout or "").strip()
            raise SpeechError(detail or "Nepodařilo se přehrát hlasový soubor.")
    except subprocess.TimeoutExpired as exc:
        raise SpeechError(f"Hlasový výstup vypršel: {exc}") from exc
    except OSError as exc:
        raise SpeechError(f"Hlasový výstup selhal: {exc}") from exc
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass

    return {
        "ok": True,
        "message": "Text byl přečten nahlas.",
        "voice": voice,
        "chars": len(spoken_text),
    }
