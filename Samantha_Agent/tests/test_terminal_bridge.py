from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from app.speech.terminal_bridge import (
    assess_terminal_bridge,
    build_codex_terminal_prompt,
    discover_codex_ttys,
    deliver_prompt_to_terminal,
    deliver_voice_command_to_terminal,
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


class TerminalBridgeTests(unittest.TestCase):
    def test_read_only_work_command_is_allowed_for_terminal_bridge(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            latest = Path(temp_dir) / "latest_voice_command.md"
            write_voice_command(latest, "Kolik jsme dnes napsali řádků kódu?")
            command = load_latest_voice_command(inbox_dir=Path(temp_dir))

        decision = assess_terminal_bridge(command)
        prompt = build_codex_terminal_prompt(command)

        self.assertTrue(decision["ok"])
        self.assertEqual(decision["status"], "allowed")
        self.assertIn("Kolik jsme dnes napsali řádků kódu?", prompt)
        self.assertIn("vyžádej si ruční potvrzení", prompt)

    def test_change_command_requires_manual_terminal_prompt(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            latest = Path(temp_dir) / "latest_voice_command.md"
            write_voice_command(latest, "Oprav chybu v Cockpitu a commitni změny.")
            command = load_latest_voice_command(inbox_dir=Path(temp_dir))

        decision = assess_terminal_bridge(command)

        self.assertFalse(decision["ok"])
        self.assertEqual(decision["status"], "manual_required")

    def test_deliver_prompt_uses_osascript_arguments_without_shell(self) -> None:
        calls = []

        def fake_runner(args, **kwargs):
            calls.append({"args": args, **kwargs})
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="delivered\n", stderr="")

        def fake_ps_runner(args, **kwargs):
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        result = deliver_prompt_to_terminal(
            "Hlasový pokyn od Míly.",
            submit=False,
            runner=fake_runner,
            ps_runner=fake_ps_runner,
            script="return \"delivered\"",
        )

        self.assertTrue(result["ok"])
        self.assertEqual(calls[0]["args"][0], "/usr/bin/osascript")
        self.assertEqual(calls[0]["args"][-2], "0")
        self.assertEqual(calls[0]["args"][-1], "")
        self.assertFalse(result["submitted"])

    def test_discover_codex_ttys_finds_codex_process_tty(self) -> None:
        def fake_ps_runner(args, **kwargs):
            return subprocess.CompletedProcess(
                args=args,
                returncode=0,
                stdout=(
                    "100 1 ttys001 zsh -zsh\n"
                    "101 100 ttys001 node /usr/local/bin/codex -C /repo .\n"
                    "102 1 ?? codex app-server --analytics-default-enabled\n"
                ),
                stderr="",
            )

        self.assertEqual(discover_codex_ttys(runner=fake_ps_runner), ["ttys001"])

    def test_deliver_voice_command_returns_manual_required_without_calling_runner(self) -> None:
        def fake_runner(*args, **kwargs):
            self.fail("manual command must not call osascript")

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            latest = Path(temp_dir) / "latest_voice_command.md"
            write_voice_command(latest, "Smaž poslední soubor.")
            command = load_latest_voice_command(inbox_dir=Path(temp_dir))

        result = deliver_voice_command_to_terminal(command, runner=fake_runner)

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "manual_required")


if __name__ == "__main__":
    unittest.main()
