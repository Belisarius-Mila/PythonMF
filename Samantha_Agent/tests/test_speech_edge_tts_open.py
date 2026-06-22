from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from app.speech.edge_tts_open import speak_edge_tts_open


class EdgeTtsOpenTests(unittest.TestCase):
    def test_speak_edge_tts_open_writes_mp3_and_plays_it_with_afplay(self) -> None:
        calls = []

        def fake_synthesizer(text, **kwargs):
            calls.append(("synth", text, kwargs))
            return b"MP3"

        def fake_opener(args, **kwargs):
            calls.append(("open", args, kwargs))
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            result = speak_edge_tts_open(
                "Hotovo.",
                output_dir=Path(temp_dir),
                synthesizer=fake_synthesizer,
                opener=fake_opener,
            )

            audio_path = Path(result["path"])
            self.assertTrue(audio_path.exists())
            self.assertEqual(audio_path.read_bytes(), b"MP3")

        self.assertTrue(result["ok"])
        self.assertEqual(result["transport"], "edge_tts_afplay")
        self.assertEqual(calls[0][0], "synth")
        self.assertEqual(calls[1][0], "open")
        self.assertEqual(calls[1][1][0], "/usr/bin/afplay")


if __name__ == "__main__":
    unittest.main()
