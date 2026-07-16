from __future__ import annotations

import argparse
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import matysek_f5tts_generate


class MatysekF5TtsGenerateTests(unittest.TestCase):
    def test_safe_preview_uses_only_afplay(self) -> None:
        calls: list[tuple[list[str], bool]] = []

        def runner(command: list[str], *, check: bool):
            calls.append((command, check))
            return subprocess.CompletedProcess(command, 0)

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            audio_path = Path(temp_dir) / "bunny.mp3"
            audio_path.write_bytes(b"mp3")
            afplay_path = Path(temp_dir) / "afplay"
            afplay_path.write_text("player", encoding="utf-8")

            matysek_f5tts_generate.play_mp3_with_afplay(
                audio_path,
                runner=runner,
                afplay_path=afplay_path,
            )

        self.assertEqual(calls, [([str(afplay_path), str(audio_path)], False)])
        self.assertNotIn("open", calls[0][0][0].casefold())

    def test_safe_preview_fails_when_afplay_returns_error(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            audio_path = Path(temp_dir) / "bunny.mp3"
            audio_path.write_bytes(b"mp3")
            afplay_path = Path(temp_dir) / "afplay"
            afplay_path.write_text("player", encoding="utf-8")

            with self.assertRaisesRegex(SystemExit, "pres afplay"):
                matysek_f5tts_generate.play_mp3_with_afplay(
                    audio_path,
                    runner=lambda command, check: subprocess.CompletedProcess(command, 1),
                    afplay_path=afplay_path,
                )

    def test_main_plays_generated_output_only_when_requested(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            cli = root / "f5-cli"
            cli.write_text("cli", encoding="utf-8")
            reference = root / "reference.mp3"
            reference.write_bytes(b"reference")
            output_dir = root / "output"
            args = argparse.Namespace(
                cli=cli,
                model="F5TTS_v1_Base",
                device="cpu",
                character=None,
                voice_manifest=root / "manifest.json",
                ref_audio=reference,
                ref_text="Reference text.",
                ref_text_file=None,
                gen_text="Generated text.",
                gen_text_file=None,
                output_dir=output_dir,
                output_file="bunny.mp3",
                nfe_step=None,
                allow_long_ref=False,
                print_command=False,
                play=True,
                dry_run=False,
            )

            with (
                patch.object(matysek_f5tts_generate, "parse_args", return_value=args),
                patch.object(matysek_f5tts_generate, "mp3_duration_seconds", return_value=None),
                patch.object(matysek_f5tts_generate.subprocess, "run") as run_mock,
                patch.object(matysek_f5tts_generate, "play_mp3_with_afplay") as play_mock,
            ):
                run_mock.return_value = subprocess.CompletedProcess([], 0)
                result = matysek_f5tts_generate.main()

        self.assertEqual(result, 0)
        play_mock.assert_called_once_with(output_dir / "bunny.mp3")

    def test_wrapper_contains_no_macos_open_playback(self) -> None:
        source = Path(matysek_f5tts_generate.__file__).read_text(encoding="utf-8")

        self.assertIn('AFPLAY_PATH = Path("/usr/bin/afplay")', source)
        self.assertIn('"--play"', source)
        self.assertNotIn('Path("/usr/bin/open")', source)
        self.assertNotIn('["open",', source)


if __name__ == "__main__":
    unittest.main()
