from __future__ import annotations

import base64
import binascii
import argparse
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRANSCRIBE_MODEL = "gpt-4o-mini-transcribe"
OPENAI_TRANSCRIPTIONS_URL = "https://api.openai.com/v1/audio/transcriptions"
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


def openai_api_key_available(env_path: Path | str | None = None) -> bool:
    if os.environ.get("OPENAI_API_KEY"):
        return True
    load_dotenv(env_path or PROJECT_ROOT / ".env", override=True)
    return bool(os.environ.get("OPENAI_API_KEY"))


def load_openai_api_key(env_path: Path | str | None = None) -> str:
    if not openai_api_key_available(env_path=env_path):
        raise TranscriptionError("Chybí OPENAI_API_KEY v prostředí nebo lokálním .env.")
    return str(os.environ.get("OPENAI_API_KEY") or "").strip()


def curl_config_quote(value: str) -> str:
    text = str(value)
    if "\n" in text or "\r" in text:
        raise TranscriptionError("Neplatná hodnota pro OpenAI transkripci.")
    return text.replace("\\", "\\\\").replace('"', '\\"')


def transcribe_audio_file_with_curl(
    audio_file: Path | str,
    *,
    mime_type: str,
    language: str = "cs",
    model: str = DEFAULT_TRANSCRIBE_MODEL,
    runner: Any = subprocess.run,
    timeout_seconds: int = 90,
) -> dict[str, Any]:
    started = time.monotonic()
    safe_mime_type = normalize_mime_type(mime_type)
    path = Path(audio_file)
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise TranscriptionError(f"Audio soubor nejde načíst: {exc}") from exc
    if size <= 0:
        raise TranscriptionError("Audio nahrávka je prázdná.")
    if size > MAX_AUDIO_BYTES:
        raise TranscriptionError("Audio nahrávka je příliš velká; zkus kratší pokyn.")

    api_key = load_openai_api_key()
    config = "\n".join(
        [
            f'url = "{OPENAI_TRANSCRIPTIONS_URL}"',
            'request = "POST"',
            f'header = "Authorization: Bearer {curl_config_quote(api_key)}"',
            f'form = "model={curl_config_quote(model)}"',
            f'form = "language={curl_config_quote(language)}"',
            f'form = "file=@{curl_config_quote(str(path))};type={curl_config_quote(safe_mime_type)}"',
            "",
        ]
    )
    curl_started = time.monotonic()
    try:
        completed = runner(
            [
                "/usr/bin/curl",
                "--silent",
                "--show-error",
                "--fail-with-body",
                "--max-time",
                str(timeout_seconds),
                "--config",
                "-",
            ],
            input=config,
            capture_output=True,
            text=True,
            timeout=timeout_seconds + 5,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise TranscriptionError("OpenAI přepis přes curl překročil časový limit.") from exc
    except OSError as exc:
        raise TranscriptionError(f"OpenAI přepis přes curl se nepodařilo spustit: {exc}") from exc
    curl_ms = int((time.monotonic() - curl_started) * 1000)

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError as exc:
        detail = stderr or stdout[:500] or f"exit {completed.returncode}"
        raise TranscriptionError(f"OpenAI přepis přes curl vrátil nečitelný výsledek: {detail}") from exc
    if completed.returncode != 0:
        message = str(data.get("error", {}).get("message") or stderr or f"exit {completed.returncode}")
        raise TranscriptionError(f"OpenAI přepis přes curl selhal: {message}")

    text = str(data.get("text") or "").strip()
    if not text:
        raise TranscriptionError("Přepis je prázdný; zkus mluvit blíž k mikrofonu.")
    return {
        "ok": True,
        "message": "Hlasový pokyn byl přepsán.",
        "text": text,
        "model": model,
        "language": language,
        "audio_bytes": size,
        "audio_kb": round(size / 1024, 1),
        "duration_ms": int((time.monotonic() - started) * 1000),
        "timing": {
            "curl_ms": curl_ms,
            "openai_ms": curl_ms,
        },
    }


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


def transcribe_audio_file(
    audio_file: Path | str,
    *,
    mime_type: str,
    language: str = "cs",
    model: str = DEFAULT_TRANSCRIBE_MODEL,
    client: Any | None = None,
) -> dict[str, Any]:
    path = Path(audio_file)
    if client is None:
        return transcribe_audio_file_with_curl(
            path,
            mime_type=mime_type,
            language=language,
            model=model,
        )
    try:
        audio_bytes = path.read_bytes()
    except OSError as exc:
        raise TranscriptionError(f"Audio soubor nejde načíst: {exc}") from exc
    return transcribe_audio_bytes(
        audio_bytes,
        mime_type=mime_type,
        language=language,
        model=model,
        client=client,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Transcribe a local voice command audio file.")
    parser.add_argument("--audio-file", type=Path, required=True)
    parser.add_argument("--mime-type", required=True)
    parser.add_argument("--language", default="cs")
    parser.add_argument("--model", default=DEFAULT_TRANSCRIBE_MODEL)
    args = parser.parse_args(argv)

    try:
        result = transcribe_audio_file(
            args.audio_file,
            mime_type=args.mime_type,
            language=args.language,
            model=args.model,
        )
    except TranscriptionError as exc:
        print(json.dumps({"ok": False, "status": "transcription_failed", "message": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
