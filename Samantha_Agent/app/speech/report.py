from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from app.speech.local_tts import DEFAULT_VOICE, SpeechError, normalize_text, speak_text


DEFAULT_COCKPIT_SPEAK_URL = "http://127.0.0.1:8770/api/speech/speak"


def speak_report(
    text: str,
    *,
    endpoint: str = DEFAULT_COCKPIT_SPEAK_URL,
    voice: str = DEFAULT_VOICE,
    timeout_seconds: float = 30.0,
    allow_local_fallback: bool = True,
    opener: Any = urllib.request.urlopen,
) -> dict[str, Any]:
    spoken_text = normalize_text(text)
    if endpoint:
        try:
            payload = json.dumps({"text": spoken_text}, ensure_ascii=False).encode("utf-8")
            request = urllib.request.Request(
                endpoint,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with opener(request, timeout=timeout_seconds) as response:
                body = response.read().decode("utf-8")
            result = json.loads(body)
            if result.get("ok"):
                return {
                    "ok": True,
                    "message": result.get("message") or "Report byl přečten nahlas přes Cockpit.",
                    "transport": "cockpit",
                    "chars": len(spoken_text),
                }
            if not allow_local_fallback:
                return {
                    "ok": False,
                    "message": result.get("message") or "Cockpit hlasový výstup selhal.",
                    "transport": "cockpit",
                    "chars": len(spoken_text),
                }
        except (OSError, urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
            if not allow_local_fallback:
                return {
                    "ok": False,
                    "message": f"Cockpit hlasový výstup selhal: {exc}",
                    "transport": "cockpit",
                    "chars": len(spoken_text),
                }

    try:
        result = speak_text(spoken_text, voice=voice)
    except SpeechError as exc:
        return {
            "ok": False,
            "message": f"Hlasový report selhal: {exc}",
            "transport": "local_tts",
            "chars": len(spoken_text),
        }
    return {
        "ok": True,
        "message": result.get("message") or "Report byl přečten nahlas.",
        "transport": "local_tts",
        "chars": len(spoken_text),
    }
