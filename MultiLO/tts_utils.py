"""Shared TTS helpers for MultiLO.

The speaker intentionally drops new requests while one utterance is already
playing. This avoids uncontrolled queuing in threaded UI code.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import threading


VOICE_HINTS = {
    "FR": ("fr", "french", "fr-fr"),
    "IT": ("it", "italian", "italiano", "it-it"),
    "ES": ("es", "spanish", "espanol", "es-es"),
    "EN": ("en", "english", "en-gb", "en-us"),
}

PREFERRED_SAY_VOICES = {
    "FR": ["Thomas"],
    "IT": ["Alice"],
    "ES": ["Jorge", "Monica", "Paulina", "Diego", "Marisol"],
    "EN": ["Samantha"],
}


class SingleFlightTTS:
    _cached_say_voices: set[str] | None = None

    def __init__(self) -> None:
        self.tts_engine = None
        self.backend = "none"
        self.say_voices: set[str] = set()
        self._busy_lock = threading.Lock()

        if sys.platform == "darwin" and shutil.which("say"):
            if SingleFlightTTS._cached_say_voices is None:
                SingleFlightTTS._cached_say_voices = self._list_say_voices()
            self.say_voices = set(SingleFlightTTS._cached_say_voices)
            if self.say_voices:
                self.backend = "say"
                return

        try:
            import pyttsx3  # type: ignore
        except Exception:
            self.tts_engine = None
            self.backend = "none"
            return

        self.tts_engine = pyttsx3.init()
        self.backend = "pyttsx3"

    def _list_say_voices(self) -> set[str]:
        try:
            out = subprocess.check_output(["say", "-v", "?"], text=True, stderr=subprocess.DEVNULL)
        except Exception:
            return set()
        voices = set()
        for line in out.splitlines():
            name = line.strip().split(" ", 1)[0]
            if name:
                voices.add(name)
        return voices

    def _pick_say_voice(self, lang: str) -> str | None:
        for voice in PREFERRED_SAY_VOICES.get(lang, []):
            if voice in self.say_voices:
                return voice
        return None

    def _select_pyttsx3_voice(self, lang: str) -> None:
        if self.tts_engine is None:
            return
        hints = VOICE_HINTS.get(lang, ())
        try:
            voices = self.tts_engine.getProperty("voices")
        except Exception:
            return
        for voice in voices:
            blob = f"{getattr(voice, 'id', '')} {getattr(voice, 'name', '')} {getattr(voice, 'languages', '')}".lower()
            if any(h in blob for h in hints):
                try:
                    self.tts_engine.setProperty("voice", voice.id)
                except Exception:
                    pass
                return

    def speak(self, text: str, lang: str, rate: int | None = None) -> bool:
        if not text or self.backend == "none":
            return False
        if not self._busy_lock.acquire(blocking=False):
            return False

        def _worker() -> None:
            try:
                if self.backend == "say":
                    voice = self._pick_say_voice(lang)
                    cmd = ["say"]
                    if voice:
                        cmd += ["-v", voice]
                    cmd.append(text)
                    subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    self._select_pyttsx3_voice(lang)
                    if rate is not None:
                        try:
                            self.tts_engine.setProperty("rate", rate)
                        except Exception:
                            pass
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
            except Exception:
                pass
            finally:
                self._busy_lock.release()

        threading.Thread(target=_worker, daemon=True).start()
        return True

    def is_busy(self) -> bool:
        return self._busy_lock.locked()
