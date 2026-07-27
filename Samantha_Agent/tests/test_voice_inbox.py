from __future__ import annotations

import tempfile
import threading
import time
import unittest
from pathlib import Path

from app.speech.voice_inbox import (
    load_latest_voice_command,
    triage_voice_command,
    wait_for_latest_voice_command,
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

    def test_triage_voice_command_does_not_treat_stisknout_as_printing(self) -> None:
        triage = triage_voice_command(
            "Na Macu bylo třeba stisknout potvrzení, abys mohl pokračovat dál."
        )

        self.assertEqual(triage.risk, "read_only")
        self.assertEqual(triage.action, "execute_read_only")
        self.assertFalse(triage.requires_confirmation)

    def test_triage_voice_command_still_requires_confirmation_for_printing(self) -> None:
        triage = triage_voice_command("Vytiskni fakturu.")

        self.assertEqual(triage.risk, "needs_confirmation")
        self.assertTrue(triage.requires_confirmation)

    def test_triage_voice_command_treats_outbound_message_as_confirmable_not_blocked(self) -> None:
        triage = triage_voice_command("Pošli SMS Janičce, jestli něco nepotřebuje.")

        self.assertEqual(triage.risk, "outbound_confirmation")
        self.assertEqual(triage.action, "prepare_outbound_and_confirm")
        self.assertTrue(triage.requires_confirmation)
        self.assertIn("samostatném potvrzení", triage.reason)

    def test_wait_for_latest_voice_command_returns_new_file(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)

            def write_later() -> None:
                time.sleep(0.05)
                (inbox / "latest_voice_command.md").write_text(
                    "# Voice command\n\n"
                    "Created at: 2026-06-05T10:00:00+00:00\n"
                    "Status: transcribed_only_not_executed\n\n"
                    "## Text\n\n"
                    "Zobraz první dvě věty eseje Fraška.\n",
                    encoding="utf-8",
                )

            thread = threading.Thread(target=write_later)
            thread.start()
            command = wait_for_latest_voice_command(inbox_dir=inbox, timeout_seconds=2, poll_seconds=0.01)
            thread.join(timeout=2)

        self.assertTrue(command.ok)
        self.assertIn("Fraška", command.text)
        self.assertEqual(command.triage.risk, "read_only")


if __name__ == "__main__":
    unittest.main()
