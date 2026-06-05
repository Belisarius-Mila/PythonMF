from __future__ import annotations

import asyncio
from typing import Any, Callable

from app.speech.local_tts import MAX_SPEECH_CHARS, SpeechError, normalize_text


DEFAULT_EDGE_TTS_VOICE = "cs-CZ-AntoninNeural"
DEFAULT_EDGE_TTS_RATE = "-10%"


class EdgeTtsError(RuntimeError):
    """Raised when online Edge TTS synthesis fails."""


async def synthesize_edge_tts_mp3(
    text: str,
    *,
    voice: str = DEFAULT_EDGE_TTS_VOICE,
    rate: str = DEFAULT_EDGE_TTS_RATE,
    communicate_factory: Callable[..., Any] | None = None,
) -> bytes:
    spoken_text = normalize_text(text, max_chars=MAX_SPEECH_CHARS)
    if communicate_factory is None:
        try:
            import edge_tts
        except ImportError as exc:
            raise EdgeTtsError("Chybí knihovna edge-tts.") from exc
        communicate_factory = edge_tts.Communicate

    audio = bytearray()
    try:
        communicate = communicate_factory(text=spoken_text, voice=voice, rate=rate)
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio":
                audio.extend(chunk.get("data") or b"")
    except SpeechError:
        raise
    except Exception as exc:
        raise EdgeTtsError(f"Edge TTS selhalo: {exc}") from exc
    if not audio:
        raise EdgeTtsError("Edge TTS nevrátilo žádné audio.")
    return bytes(audio)


def synthesize_edge_tts_mp3_sync(
    text: str,
    *,
    voice: str = DEFAULT_EDGE_TTS_VOICE,
    rate: str = DEFAULT_EDGE_TTS_RATE,
) -> bytes:
    try:
        return asyncio.run(synthesize_edge_tts_mp3(text, voice=voice, rate=rate))
    except SpeechError:
        raise
    except EdgeTtsError:
        raise
    except RuntimeError as exc:
        raise EdgeTtsError(f"Edge TTS runtime selhalo: {exc}") from exc
