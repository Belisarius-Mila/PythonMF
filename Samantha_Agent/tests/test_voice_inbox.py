from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from app.speech.voice_inbox import (
    load_latest_voice_command,
    triage_voice_command,
)


class VoiceInboxTests(unittest.TestCase):
    def test_load_latest_voice_command_triages_read_only_text(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            latest = inbox / "latest_voice_command.md"
            latest.write_text(
                "# Voice command\n\n"
                "Created at: 2026-06-05T10:00:00+00:00\n"
                "Status: transcribed_only_not_executed\n\n"
                "## Text\n\n"
                "Najdi poslední dokumenty k pojištění.\n",
                encoding="utf-8",
            )

            command = load_latest_voice_command(inbox_dir=inbox)

        self.assertTrue(command.ok)
        self.assertEqual(command.created_at, "2026-06-05T10:00:00+00:00")
        self.assertEqual(command.status, "transcribed_only_not_executed")
        self.assertEqual(command.triage.risk, "read_only")
        self.assertEqual(command.triage.action, "execute_read_only")
        self.assertFalse(command.triage.requires_confirmation)

    def test_triage_voice_command_requires_confirmation_for_state_changes(self) -> None:
        triage = triage_voice_command("Smaž ty dvě testovací připomínky.")

        self.assertEqual(triage.risk, "needs_confirmation")
        self.assertEqual(triage.action, "prepare_and_confirm")
        self.assertTrue(triage.requires_confirmation)

    def test_voice_inbox_triage_cli_can_print_json(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            (inbox / "latest_voice_command.md").write_text(
                "# Voice command\n\n"
                "Created at: 2026-06-05T10:00:00+00:00\n"
                "Status: transcribed_only_not_executed\n\n"
                "## Text\n\n"
                "Připrav návrh odpovědi.\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    ".venv/bin/python",
                    "scripts/voice_inbox_triage.py",
                    "--inbox-dir",
                    str(inbox),
                    "--json",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["triage"]["risk"], "draft")
        self.assertEqual(payload["triage"]["action"], "draft_only")


if __name__ == "__main__":
    unittest.main()
