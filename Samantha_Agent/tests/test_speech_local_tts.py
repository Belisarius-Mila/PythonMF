from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from app.speech.local_tts import (
    SAY_BIN,
    SpeechError,
    normalize_text,
    speak_text,
    synthesize_local_tts_m4a,
)


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
        self.assertEqual(calls, [[SAY_BIN, "-v", "Zuzana", "Test hlasu."]])

    def test_speak_text_rejects_empty_text_and_unknown_voice(self) -> None:
        with self.assertRaises(SpeechError):
            speak_text("   ", runner=lambda *args, **kwargs: None)
        with self.assertRaises(SpeechError):
            speak_text("Ahoj", voice="Unknown", runner=lambda *args, **kwargs: None)

    def test_synthesize_local_tts_m4a_returns_audio_and_removes_temporary_file(self) -> None:
        calls: list[list[str]] = []
        output_paths: list[Path] = []

        def fake_runner(args, **kwargs):
            calls.append(list(args))
            output_path = Path(args[args.index("-o") + 1])
            output_paths.append(output_path)
            output_path.write_bytes(b"M4A-AUDIO")
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as temp_dir:
            result = synthesize_local_tts_m4a("Test místního hlasu.", runner=fake_runner, temp_dir=temp_dir)
            self.assertFalse(output_paths[0].exists())

        self.assertEqual(result, b"M4A-AUDIO")
        self.assertIn("--file-format=m4af", calls[0])
        self.assertEqual(calls[0][-1], "Test místního hlasu.")

    def test_synthesize_local_tts_m4a_rejects_failed_or_oversized_output(self) -> None:
        def failed_runner(args, **kwargs):
            return subprocess.CompletedProcess(args=args, returncode=1, stdout="", stderr="say failed")

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(SpeechError, "say failed"):
                synthesize_local_tts_m4a("Test", runner=failed_runner, temp_dir=temp_dir)

        def oversized_runner(args, **kwargs):
            Path(args[args.index("-o") + 1]).write_bytes(b"12345")
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(SpeechError, "povolenou velikost"):
                synthesize_local_tts_m4a(
                    "Test",
                    runner=oversized_runner,
                    temp_dir=temp_dir,
                    max_audio_bytes=4,
                )


if __name__ == "__main__":
    unittest.main()
