from __future__ import annotations

import base64
import binascii
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRANSCRIBE_MODEL = "gpt-4o-mini-transcribe"
MAX_AUDIO_BYTES = 6 * 1024 * 1024
MIME_EXTENSIONS = {
    "audio/webm": ".webm",
    "audio/mp4": ".mp4",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/aac": ".aac",
    "audio/ogg": ".ogg",
}


class TranscriptionError(RuntimeError):
    """Raised when a local voice command cannot be transcribed safely."""


def normalize_mime_type(value: str) -> str:
    mime_type = str(value or "").split(";", 1)[0].strip().casefold()
    if mime_type not in MIME_EXTENSIONS:
        raise TranscriptionError(f"Nepodporovaný audio formát: {mime_type or 'neznámý'}")
    return mime_type


def decode_audio_base64(audio_base64: str, *, max_bytes: int = MAX_AUDIO_BYTES) -> bytes:
    raw = str(audio_base64 or "").strip()
    if "," in raw and raw.startswith("data:"):
        raw = raw.split(",", 1)[1]
    if not raw:
        raise TranscriptionError("Chybí audio data.")
    try:
        data = base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise TranscriptionError("Audio data nejsou platný base64 záznam.") from exc
    if not data:
        raise TranscriptionError("Audio nahrávka je prázdná.")
    if len(data) > max_bytes:
        raise TranscriptionError("Audio nahrávka je příliš velká; zkus kratší pokyn.")
    return data


def openai_api_key_available() -> bool:
    if os.environ.get("OPENAI_API_KEY"):
        return True
    load_dotenv(PROJECT_ROOT / ".env")
    return bool(os.environ.get("OPENAI_API_KEY"))


def transcribe_audio_bytes(
    audio_bytes: bytes,
    *,
    mime_type: str,
    language: str = "cs",
    model: str = DEFAULT_TRANSCRIBE_MODEL,
    client: Any | None = None,
    temp_dir: Path | str = "/private/tmp",
) -> dict[str, Any]:
    started = time.monotonic()
    safe_mime_type = normalize_mime_type(mime_type)
    if not audio_bytes:
        raise TranscriptionError("Audio nahrávka je prázdná.")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise TranscriptionError("Audio nahrávka je příliš velká; zkus kratší pokyn.")
    if client is None and not openai_api_key_available():
        raise TranscriptionError("Chybí OPENAI_API_KEY v prostředí nebo lokálním .env.")

    extension = MIME_EXTENSIONS[safe_mime_type]
    temp_write_started = time.monotonic()
    with tempfile.NamedTemporaryFile(
        prefix="samantha_voice_command_",
        suffix=extension,
        dir=str(temp_dir),
        delete=False,
    ) as temp_file:
        temp_path = Path(temp_file.name)
        temp_file.write(audio_bytes)
    temp_write_ms = int((time.monotonic() - temp_write_started) * 1000)

    try:
        openai_client = client or OpenAI()
        openai_started = time.monotonic()
        with temp_path.open("rb") as audio_file:
            transcription = openai_client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                language=language,
            )
        openai_ms = int((time.monotonic() - openai_started) * 1000)
    except Exception as exc:
        raise TranscriptionError(f"Přepis hlasu selhal: {exc}") from exc
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass

    text = str(getattr(transcription, "text", "") or "").strip()
    if not text:
        raise TranscriptionError("Přepis je prázdný; zkus mluvit blíž k mikrofonu.")
    return {
        "ok": True,
        "message": "Hlasový pokyn byl přepsán.",
        "text": text,
        "model": model,
        "language": language,
        "audio_bytes": len(audio_bytes),
        "audio_kb": round(len(audio_bytes) / 1024, 1),
        "duration_ms": int((time.monotonic() - started) * 1000),
        "timing": {
            "temp_write_ms": temp_write_ms,
            "openai_ms": openai_ms,
        },
    }


def transcribe_audio_base64(
    audio_base64: str,
    *,
    mime_type: str,
    language: str = "cs",
    model: str = DEFAULT_TRANSCRIBE_MODEL,
    client: Any | None = None,
) -> dict[str, Any]:
    audio_bytes = decode_audio_base64(audio_base64)
    return transcribe_audio_bytes(
        audio_bytes,
        mime_type=mime_type,
        language=language,
        model=model,
        client=client,
    )
