from __future__ import annotations

import unittest
from pathlib import Path

from app.speech.edge_tts_mp3 import EdgeTtsError
from scripts.speak_edge_open import speak_voice_reply


class SpeakEdgeOpenTests(unittest.TestCase):
    def test_local_engine_uses_macos_say_voice(self) -> None:
        calls: list[dict[str, object]] = []

        def fake_local(text: str, **kwargs):
            calls.append({"text": text, **kwargs})
            return {"ok": True, "message": "Text byl přečten nahlas.", "voice": kwargs["voice"], "chars": len(text)}

        result = speak_voice_reply("Hotovo.", engine="local", voice=None, local_speaker=fake_local)

        self.assertEqual(result["transport"], "local_tts")
        self.assertEqual(result["voice"], "Zuzana")
        self.assertEqual(calls, [{"text": "Hotovo.", "voice": "Zuzana"}])

    def test_edge_engine_uses_edge_voice(self) -> None:
        calls: list[dict[str, object]] = []

        def fake_edge(text: str, **kwargs):
            calls.append({"text": text, **kwargs})
            return {"ok": True, "message": "Edge OK", "transport": "edge_tts_afplay", "path": "/tmp/test.mp3"}

        result = speak_voice_reply("Hotovo.", engine="edge", voice=None, output_dir=Path("/tmp"), edge_speaker=fake_edge)

        self.assertEqual(result["transport"], "edge_tts_afplay")
        self.assertEqual(calls[0]["voice"], "cs-CZ-AntoninNeural")

    def test_edge_fallback_uses_local_when_edge_fails(self) -> None:
        def fake_edge(*args, **kwargs):
            raise EdgeTtsError("síť není dostupná")

        def fake_local(text: str, **kwargs):
            return {"ok": True, "message": "Text byl přečten nahlas.", "voice": kwargs["voice"], "chars": len(text)}

        result = speak_voice_reply(
            "Hotovo.",
            engine="edge-fallback",
            voice=None,
            edge_speaker=fake_edge,
            local_speaker=fake_local,
        )

        self.assertEqual(result["transport"], "local_tts")
        self.assertEqual(result["fallback_from"], "edge_tts_afplay")
        self.assertIn("síť není dostupná", result["fallback_reason"])


if __name__ == "__main__":
    unittest.main()
