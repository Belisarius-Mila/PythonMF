from __future__ import annotations

import base64
import binascii
import argparse
import json
import logging
import math
import os
import random
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRANSCRIBE_MODEL = "gpt-transcribe"
DEFAULT_TRANSCRIBE_KEYWORDS = (
    "Samantha",
    "Adam",
    "Míla",
    "Cockpit",
    "Human–Adam",
)
OPENAI_TRANSCRIPTIONS_URL = "https://api.openai.com/v1/audio/transcriptions"
MAX_AUDIO_BYTES = 6 * 1024 * 1024
DEFAULT_CURL_MAX_ATTEMPTS = 3
MAX_CURL_RETRY_WAIT_SECONDS = 30.0
CURL_RETRY_BASE_SECONDS = 1.0
CURL_RETRY_JITTER_SECONDS = 0.25
CURL_ATTEMPT_MAX_SECONDS = 60.0
CURL_TOTAL_HEADROOM_SECONDS = 5.0
CURL_HTTP_META_MARKER = "__SAMANTHA_OPENAI_HTTP__"
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


LOGGER = logging.getLogger(__name__)


class TranscriptionError(RuntimeError):
    """Raised when a local voice command cannot be transcribed safely."""


def transcription_context_fields(language: str) -> dict[str, list[str]]:
    clean_language = str(language or "").strip().casefold()
    if len(clean_language) != 2 or not clean_language.isascii() or not clean_language.isalpha():
        raise TranscriptionError("Jazyk přepisu musí být dvoupísmenný ISO-639-1 kód.")

    keywords: list[str] = []
    for value in DEFAULT_TRANSCRIBE_KEYWORDS:
        keyword = str(value).strip()
        if not keyword or any(character in keyword for character in "<>\r\n"):
            raise TranscriptionError("Klíčová slova pro přepis obsahují neplatnou hodnotu.")
        keywords.append(keyword)
    return {"languages": [clean_language], "keywords": keywords}


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


def split_curl_http_output(
    stdout: str,
    *,
    returncode: int,
) -> tuple[str, int, str]:
    """Separate the response body from curl's safe HTTP metadata trailer."""
    raw = str(stdout or "")
    marker = f"\n{CURL_HTTP_META_MARKER}:"
    if marker not in raw:
        return raw.strip(), 200 if returncode == 0 else 0, ""
    body, trailer = raw.rsplit(marker, 1)
    metadata = trailer.strip("\r\n")
    if "\t" not in metadata:
        return body.strip(), 200 if returncode == 0 else 0, ""
    status_raw, retry_after = metadata.split("\t", 1)
    try:
        status = int(status_raw.strip())
    except ValueError:
        status = 200 if returncode == 0 else 0
    return body.strip(), status, retry_after.strip()


def parse_retry_after_seconds(
    value: str,
    *,
    now: datetime | None = None,
) -> float | None:
    """Parse Retry-After seconds or an HTTP date without exceeding policy bounds."""
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        seconds = float(raw)
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(raw)
        except (TypeError, ValueError, OverflowError):
            return None
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        reference = now or datetime.now(timezone.utc)
        if reference.tzinfo is None:
            reference = reference.replace(tzinfo=timezone.utc)
        seconds = max(0.0, (retry_at - reference).total_seconds())
    if not math.isfinite(seconds) or seconds < 0:
        return None
    return seconds


def curl_transcription_retry_delay(
    *,
    status: int,
    error_code: str,
    retry_after: str,
    attempt: int,
    jitter_fn: Callable[[float, float], float] = random.uniform,
) -> float | None:
    retryable = (status, error_code) in {
        (429, "slow_down"),
        (503, "server_is_overloaded"),
    }
    if not retryable:
        return None
    header_delay = parse_retry_after_seconds(retry_after)
    if header_delay is not None:
        if header_delay > MAX_CURL_RETRY_WAIT_SECONDS:
            return None
        return header_delay
    backoff = CURL_RETRY_BASE_SECONDS * (2 ** max(0, attempt - 1))
    jitter = max(0.0, float(jitter_fn(0.0, CURL_RETRY_JITTER_SECONDS)))
    return min(MAX_CURL_RETRY_WAIT_SECONDS, backoff + jitter)


def transcribe_audio_file_with_curl(
    audio_file: Path | str,
    *,
    mime_type: str,
    language: str = "cs",
    model: str = DEFAULT_TRANSCRIBE_MODEL,
    runner: Any = subprocess.run,
    timeout_seconds: int = 90,
    max_attempts: int = DEFAULT_CURL_MAX_ATTEMPTS,
    sleep_fn: Callable[[float], None] = time.sleep,
    jitter_fn: Callable[[float, float], float] = random.uniform,
) -> dict[str, Any]:
    started = time.monotonic()
    deadline = started + max(1.0, float(timeout_seconds))
    attempts_limit = max(1, min(int(max_attempts), DEFAULT_CURL_MAX_ATTEMPTS))
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
    context_fields = transcription_context_fields(language)
    config_lines = [
        f'url = "{OPENAI_TRANSCRIPTIONS_URL}"',
        'request = "POST"',
        f'header = "Authorization: Bearer {curl_config_quote(api_key)}"',
        f'form = "model={curl_config_quote(model)}"',
        'form = "response_format=json"',
    ]
    config_lines.extend(
        f'form = "languages[]={curl_config_quote(value)}"'
        for value in context_fields["languages"]
    )
    config_lines.extend(
        f'form = "keywords[]={curl_config_quote(value)}"'
        for value in context_fields["keywords"]
    )
    config_lines.extend(
        [
            f'form = "file=@{curl_config_quote(str(path))};type={curl_config_quote(safe_mime_type)}"',
            "",
        ]
    )
    config = "\n".join(config_lines)
    curl_started = time.monotonic()
    attempt = 0
    data: dict[str, Any] = {}
    while attempt < attempts_limit:
        attempt += 1
        remaining = deadline - time.monotonic()
        if remaining <= CURL_TOTAL_HEADROOM_SECONDS:
            raise TranscriptionError("OpenAI přepis přes curl překročil časový limit.")
        attempt_timeout = min(
            CURL_ATTEMPT_MAX_SECONDS,
            max(1.0, remaining - CURL_TOTAL_HEADROOM_SECONDS),
        )
        try:
            completed = runner(
                [
                    "/usr/bin/curl",
                    "--silent",
                    "--show-error",
                    "--fail-with-body",
                    "--max-time",
                    f"{attempt_timeout:.3f}",
                    "--write-out",
                    f"\n{CURL_HTTP_META_MARKER}:%{{http_code}}\t%header{{retry-after}}\n",
                    "--config",
                    "-",
                ],
                input=config,
                capture_output=True,
                text=True,
                timeout=attempt_timeout + 1.0,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise TranscriptionError("OpenAI přepis přes curl překročil časový limit.") from exc
        except OSError as exc:
            raise TranscriptionError(f"OpenAI přepis přes curl se nepodařilo spustit: {exc}") from exc

        stdout, http_status, retry_after = split_curl_http_output(
            completed.stdout or "",
            returncode=completed.returncode,
        )
        stderr = (completed.stderr or "").strip()
        try:
            parsed = json.loads(stdout) if stdout else {}
        except json.JSONDecodeError as exc:
            detail = stderr or stdout[:500] or f"exit {completed.returncode}"
            raise TranscriptionError(f"OpenAI přepis přes curl vrátil nečitelný výsledek: {detail}") from exc
        data = parsed if isinstance(parsed, dict) else {}
        if completed.returncode == 0:
            break

        error = data.get("error") if isinstance(data.get("error"), dict) else {}
        error_code = str(error.get("code") or "").strip()
        delay = curl_transcription_retry_delay(
            status=http_status,
            error_code=error_code,
            retry_after=retry_after,
            attempt=attempt,
            jitter_fn=jitter_fn,
        )
        if delay is None or attempt >= attempts_limit:
            message = str(error.get("message") or stderr or f"exit {completed.returncode}")
            raise TranscriptionError(f"OpenAI přepis přes curl selhal: {message}")
        remaining = deadline - time.monotonic()
        if delay + CURL_TOTAL_HEADROOM_SECONDS >= remaining:
            raise TranscriptionError("OpenAI přepis přes curl překročil časový limit.")
        LOGGER.warning(
            "OpenAI transcription retry status=%s code=%s attempt=%s/%s wait_seconds=%.3f",
            http_status,
            error_code,
            attempt,
            attempts_limit,
            delay,
        )
        sleep_fn(delay)

    curl_ms = int((time.monotonic() - curl_started) * 1000)

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
            "curl_attempts": attempt,
            "curl_retries": max(0, attempt - 1),
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
        context_fields = transcription_context_fields(language)
        with temp_path.open("rb") as audio_file:
            transcription = openai_client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="json",
                extra_body=context_fields,
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
