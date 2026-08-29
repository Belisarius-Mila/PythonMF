"""Local speech output helpers for Samantha."""

from app.speech.local_tts import SpeechError, speak_text, synthesize_local_tts_m4a


def __getattr__(name: str):
    """Load optional transcription dependencies only when transcription is used."""

    if name in {"TranscriptionError", "transcribe_audio_base64"}:
        from app.speech.transcribe import TranscriptionError, transcribe_audio_base64

        return {
            "TranscriptionError": TranscriptionError,
            "transcribe_audio_base64": transcribe_audio_base64,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "SpeechError",
    "TranscriptionError",
    "speak_text",
    "synthesize_local_tts_m4a",
    "transcribe_audio_base64",
]
