from __future__ import annotations

import json
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path

from app.speech.adam_voice_mode import (
    handle_voice_command,
    load_voice_mode_status,
    spoken_notice_for_command,
    write_voice_mode_status,
)
from app.speech.voice_inbox import load_latest_voice_command


def write_voice_command(path: Path, text: str) -> None:
    path.write_text(
        "# Voice command\n\n"
        "Created at: 2026-06-05T10:00:00+00:00\n"
        "Status: transcribed_only_not_executed\n\n"
        "## Text\n\n"
        f"{text}\n",
        encoding="utf-8",
    )


class AdamVoiceModeTests(unittest.TestCase):
    def test_spoken_notice_describes_read_only_command(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            latest = Path(temp_dir) / "latest_voice_command.md"
            write_voice_command(latest, "Najdi stav dokumentů.")
            command = load_latest_voice_command(inbox_dir=Path(temp_dir))

        notice = spoken_notice_for_command(command)

        self.assertIn("bezpečný pro čtení", notice)
        self.assertIn("Najdi stav dokumentů.", notice)

    def test_handle_voice_command_writes_status_and_can_skip_speech(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            latest = inbox / "latest_voice_command.md"
            status_path = inbox / "adam_voice_mode_status.json"
            write_voice_command(latest, "Připrav návrh odpovědi.")
            command = load_latest_voice_command(inbox_dir=inbox)

            result = handle_voice_command(command, should_speak=False, status_path=status_path)
            payload = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertTrue(result["ok"])
        self.assertEqual(result["speech"]["transport"], "disabled")
        self.assertEqual(payload["state"], "command_ready")
        self.assertEqual(payload["last_command"]["text"], "Připrav návrh odpovědi.")

    def test_load_voice_mode_status_reports_missing_watcher(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            status = load_voice_mode_status(status_path=Path(temp_dir) / "missing.json")

        self.assertTrue(status["ok"])
        self.assertFalse(status["running"])
        self.assertEqual(status["state"], "stopped")

    def test_load_voice_mode_status_reports_current_process_running(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            status_path = Path(temp_dir) / "status.json"
            write_voice_mode_status(
                status_path=status_path,
                state="listening",
                message="Test watcher běží.",
            )

            status = load_voice_mode_status(status_path=status_path)

        self.assertTrue(status["running"])
        self.assertEqual(status["state"], "listening")

    def test_adam_voice_mode_cli_waits_for_new_command_and_stops_after_count(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            status_path = inbox / "status.json"
            write_voice_command(inbox / "latest_voice_command.md", "Starý pokyn.")

            def write_later() -> None:
                time.sleep(1.5)
                write_voice_command(inbox / "latest_voice_command.md", "Najdi stav projektu Dokumenty.")

            thread = threading.Thread(target=write_later)
            thread.start()
            completed = subprocess.run(
                [
                    ".venv/bin/python",
                    "scripts/adam_voice_mode.py",
                    "--inbox-dir",
                    str(inbox),
                    "--status-path",
                    str(status_path),
                    "--count",
                    "1",
                    "--timeout",
                    "5",
                    "--poll",
                    "0.01",
                    "--no-speak",
                ],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
            thread.join(timeout=2)
            payload = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("VOICE INBOX TRIAGE", completed.stdout)
        self.assertIn("Najdi stav projektu Dokumenty.", completed.stdout)
        self.assertEqual(payload["state"], "completed")
        self.assertEqual(payload["last_command"]["text"], "Najdi stav projektu Dokumenty.")


if __name__ == "__main__":
    unittest.main()
