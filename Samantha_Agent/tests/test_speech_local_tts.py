from __future__ import annotations

import subprocess
import unittest

from app.speech.local_tts import SAY_BIN, SpeechError, normalize_text, speak_text


class LocalTtsTests(unittest.TestCase):
    def test_normalize_text_collapses_whitespace_and_truncates(self) -> None:
        self.assertEqual(normalize_text("  Ahoj\n\nMílo.  "), "Ahoj Mílo.")
        self.assertEqual(normalize_text("abcdef", max_chars=4), "abc…")

    def test_speak_text_uses_direct_say_with_argument_list(self) -> None:
        calls: list[list[str]] = []

        def fake_runner(args, **kwargs):
            calls.append(list(args))
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        result = speak_text("Test hlasu.", runner=fake_runner)

        self.assertTrue(result["ok"])
        self.assertEqual(calls, [[SAY_BIN, "-v", "Daniel", "Test hlasu."]])

    def test_speak_text_rejects_empty_text_and_unknown_voice(self) -> None:
        with self.assertRaises(SpeechError):
            speak_text("   ", runner=lambda *args, **kwargs: None)
        with self.assertRaises(SpeechError):
            speak_text("Ahoj", voice="Unknown", runner=lambda *args, **kwargs: None)


if __name__ == "__main__":
    unittest.main()
