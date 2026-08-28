"""Local speech output helpers for Samantha."""

from app.speech.local_tts import SpeechError, speak_text, synthesize_local_tts_m4a
from app.speech.transcribe import TranscriptionError, transcribe_audio_base64

__all__ = [
    "SpeechError",
    "TranscriptionError",
    "speak_text",
    "synthesize_local_tts_m4a",
    "transcribe_audio_base64",
]
