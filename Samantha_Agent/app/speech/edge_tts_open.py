from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any, Callable

from app.speech.edge_tts_mp3 import DEFAULT_EDGE_TTS_RATE, DEFAULT_EDGE_TTS_VOICE, synthesize_edge_tts_mp3_sync
from app.speech.local_tts import MAX_SPEECH_CHARS, SpeechError, normalize_text


def speak_edge_tts_open(
    text: str,
    *,
    output_dir: Path = Path("/private/tmp"),
    voice: str = DEFAULT_EDGE_TTS_VOICE,
    rate: str = DEFAULT_EDGE_TTS_RATE,
    synthesizer: Callable[..., bytes] = synthesize_edge_tts_mp3_sync,
    opener: Any = subprocess.run,
) -> dict[str, Any]:
    spoken_text = normalize_text(text, max_chars=MAX_SPEECH_CHARS)
    audio = synthesizer(spoken_text, voice=voice, rate=rate)
    if not audio:
        raise SpeechError("Edge TTS nevygenerovalo žádné audio.")

    output_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(spoken_text.encode("utf-8")).hexdigest()[:12]
    audio_path = output_dir / f"adam_voice_report_{digest}.mp3"
    audio_path.write_bytes(audio)

    opened = opener(["open", str(audio_path)], capture_output=True, text=True, timeout=10, check=False)
    if opened.returncode != 0:
        detail = (opened.stderr or opened.stdout or "").strip()
        raise SpeechError(detail or "MP3 se nepodařilo otevřít v macOS přehrávači.")

    return {
        "ok": True,
        "message": "Edge TTS MP3 bylo otevřeno v macOS přehrávači.",
        "transport": "edge_tts_open",
        "path": str(audio_path),
        "voice": voice,
        "chars": len(spoken_text),
    }
