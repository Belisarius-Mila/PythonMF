from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from app.speech.local_tts import AFPLAY_BIN, SAY_BIN, SpeechError, normalize_text, speak_text


class LocalTtsTests(unittest.TestCase):
    def test_normalize_text_collapses_whitespace_and_truncates(self) -> None:
        self.assertEqual(normalize_text("  Ahoj\n\nMílo.  "), "Ahoj Mílo.")
        self.assertEqual(normalize_text("abcdef", max_chars=4), "abc…")

    def test_speak_text_uses_say_then_afplay_with_argument_lists(self) -> None:
        calls: list[list[str]] = []

        def fake_runner(args, **kwargs):
            calls.append(list(args))
            output_path = Path(args[args.index("-o") + 1]) if "-o" in args else None
            if output_path:
                output_path.write_bytes(b"AIFF")
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            result = speak_text("Test hlasu.", runner=fake_runner, temp_dir=temp_dir)

        self.assertTrue(result["ok"])
        self.assertEqual(calls[0][:5], [SAY_BIN, "-v", "Zuzana", "-o", calls[0][4]])
        self.assertEqual(calls[0][5], "Test hlasu.")
        self.assertEqual(calls[1][0], AFPLAY_BIN)
        self.assertFalse(Path(calls[1][1]).exists())

    def test_speak_text_rejects_empty_text_and_unknown_voice(self) -> None:
        with self.assertRaises(SpeechError):
            speak_text("   ", runner=lambda *args, **kwargs: None)
        with self.assertRaises(SpeechError):
            speak_text("Ahoj", voice="Unknown", runner=lambda *args, **kwargs: None)


if __name__ == "__main__":
    unittest.main()
