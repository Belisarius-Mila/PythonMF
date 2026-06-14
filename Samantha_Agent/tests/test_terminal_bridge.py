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
    deliver_prompt_to_vscode,
    deliver_voice_command_to_terminal,
    load_marked_codex_tty,
    normalize_tty,
    terminal_applescript,
    vscode_applescript,
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
        self.assertIn("přečti stručnou verzi výsledku nahlas", prompt)
        self.assertIn("scripts/speak_edge_open.py", prompt)
        self.assertIn("mimo Codex sandbox", prompt)
        self.assertIn("scripts/adam_voice_reply.py --latest-command", prompt)
        self.assertIn("zapiš stejný stručný výsledek do Cockpitu", prompt)

    def test_change_command_requires_manual_terminal_prompt(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            latest = Path(temp_dir) / "latest_voice_command.md"
            write_voice_command(latest, "Oprav chybu v Cockpitu a commitni změny.")
            command = load_latest_voice_command(inbox_dir=Path(temp_dir))

        decision = assess_terminal_bridge(command)

        self.assertFalse(decision["ok"])
        self.assertEqual(decision["status"], "manual_required")

    def test_read_only_thinking_prompt_with_send_word_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            latest = Path(temp_dir) / "latest_voice_command.md"
            write_voice_command(
                latest,
                "Adame, vezmi to do terminálu, zkus to promyslet a pošli stručnou odpověď.",
            )
            command = load_latest_voice_command(inbox_dir=Path(temp_dir))

        decision = assess_terminal_bridge(command)

        self.assertTrue(decision["ok"])
        self.assertEqual(decision["status"], "allowed")
        self.assertEqual(command.triage.risk, "read_only")

    def test_outbound_sms_prompt_still_requires_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            latest = Path(temp_dir) / "latest_voice_command.md"
            write_voice_command(latest, "Pošli SMS Janičce, jestli něco nepotřebuje.")
            command = load_latest_voice_command(inbox_dir=Path(temp_dir))

        decision = assess_terminal_bridge(command)

        self.assertFalse(decision["ok"])
        self.assertEqual(decision["status"], "manual_required")
        self.assertEqual(command.triage.risk, "outbound_confirmation")

    def test_deliver_prompt_uses_osascript_arguments_without_shell(self) -> None:
        calls = []

        def fake_runner(args, **kwargs):
            calls.append({"args": args, **kwargs})
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="delivered\n", stderr="")

        def fake_ps_runner(args, **kwargs):
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            result = deliver_prompt_to_terminal(
                "Hlasový pokyn od Míly.",
                submit=False,
                runner=fake_runner,
                ps_runner=fake_ps_runner,
                script="return \"delivered\"",
                vscode_fallback=False,
                marked_tty_path=Path(temp_dir) / "missing_marker.json",
            )

        self.assertTrue(result["ok"])
        self.assertEqual(calls[0]["args"][0], "/usr/bin/osascript")
        self.assertEqual(calls[0]["args"][-2], "0")
        self.assertEqual(calls[0]["args"][-1], "")
        self.assertFalse(result["submitted"])

    def test_deliver_prompt_falls_back_to_vscode_when_terminal_is_missing(self) -> None:
        calls = []

        def fake_runner(args, **kwargs):
            calls.append({"args": args, **kwargs})
            if len(calls) == 1:
                return subprocess.CompletedProcess(args=args, returncode=1, stdout="", stderr="No Terminal tab.")
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="delivered_vscode\n", stderr="")

        def fake_ps_runner(args, **kwargs):
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        result = deliver_prompt_to_terminal(
            "Hlasový pokyn od Míly.",
            submit=True,
            runner=fake_runner,
            ps_runner=fake_ps_runner,
            script="error \"No Terminal tab.\"",
            vscode_script="return \"delivered_vscode\"",
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "delivered_vscode")
        self.assertEqual(result["terminal_status"]["status"], "terminal_delivery_failed")
        self.assertTrue(result["verified"])
        self.assertEqual(result["delivery_method"], "local_gui_vscode")
        self.assertEqual(len(calls), 2)

    def test_deliver_prompt_to_vscode_uses_osascript_arguments_without_shell(self) -> None:
        calls = []

        def fake_runner(args, **kwargs):
            calls.append({"args": args, **kwargs})
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="delivered_vscode\n", stderr="")

        result = deliver_prompt_to_vscode(
            "Hlasový pokyn od Míly.",
            submit=False,
            runner=fake_runner,
            script="return \"delivered_vscode\"",
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "delivered_vscode")
        self.assertEqual(calls[0]["args"][0], "/usr/bin/osascript")
        self.assertEqual(calls[0]["args"][-1], "0")
        self.assertFalse(result["submitted"])
        self.assertTrue(result["verified"])
        self.assertEqual(result["delivery_method"], "local_gui_vscode")

    def test_vscode_applescript_does_not_paste_focus_command_text(self) -> None:
        script = vscode_applescript()

        self.assertNotIn(">workbench.action.terminal.focus", script)
        self.assertNotIn("Terminal: Focus Terminal", script)
        self.assertIn("promptText", script)
        self.assertIn("frontAppName", script)
        self.assertIn("tell application frontAppName to activate", script)
        self.assertRegex(script, r'keystroke "v" using command down\s+delay 0\.25\s+if shouldSubmit is "1" then key code 36')

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

    def test_discover_codex_ttys_ignores_screen_attach_session_name(self) -> None:
        def fake_ps_runner(args, **kwargs):
            return subprocess.CompletedProcess(
                args=args,
                returncode=0,
                stdout=(
                    "100 1 ttys000 zsh -zsh\n"
                    "101 100 ttys000 node /usr/local/bin/codex -C /repo .\n"
                    "102 1 ttys003 screen screen -U -r samantha_codex\n"
                    "103 1 ?? codex codex app-server --analytics-default-enabled\n"
                ),
                stderr="",
            )

        self.assertEqual(discover_codex_ttys(runner=fake_ps_runner), ["ttys000"])

    def test_load_marked_codex_tty_reads_private_marker(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            marker = Path(temp_dir) / "current_codex_tty.json"
            marker.write_text('{"tty": "/dev/ttys005"}', encoding="utf-8")

            self.assertEqual(load_marked_codex_tty(marker), "ttys005")

    def test_normalize_tty_pads_short_numeric_suffix(self) -> None:
        self.assertEqual(normalize_tty("ttys01"), "ttys001")
        self.assertEqual(normalize_tty("/dev/ttys1"), "ttys001")
        self.assertEqual(normalize_tty("ttys001"), "ttys001")

    def test_deliver_prompt_prefers_marked_tty_before_gui_fallback(self) -> None:
        runner_calls = []
        tty_calls = []

        def fake_runner(args, **kwargs):
            runner_calls.append(args)
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="delivered\n", stderr="")

        def fake_ps_runner(args, **kwargs):
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="100 1 ttys005 codex codex\n", stderr="")

        def fake_tty_deliverer(tty, prompt, **kwargs):
            tty_calls.append((tty, prompt, kwargs))
            return {"ok": True, "status": "delivered_tty", "submitted": kwargs.get("submit"), "verified": True}

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            marker = Path(temp_dir) / "current_codex_tty.json"
            marker.write_text('{"tty": "ttys005"}', encoding="utf-8")

            result = deliver_prompt_to_terminal(
                "Hlasový pokyn od Míly.",
                runner=fake_runner,
                ps_runner=fake_ps_runner,
                marked_tty_path=marker,
                tty_deliverer=fake_tty_deliverer,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "delivered_tty")
        self.assertEqual(tty_calls[0][0], "ttys005")
        self.assertEqual(runner_calls, [])

    def test_deliver_prompt_uses_single_active_codex_tty_when_marker_is_stale(self) -> None:
        runner_calls = []
        tty_calls = []

        def fake_runner(args, **kwargs):
            runner_calls.append(args)
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="delivered\n", stderr="")

        def fake_ps_runner(args, **kwargs):
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="100 1 ttys002 codex codex\n", stderr="")

        def fake_tty_deliverer(tty, prompt, **kwargs):
            tty_calls.append((tty, prompt, kwargs))
            return {"ok": True, "status": "delivered_tty", "submitted": kwargs.get("submit"), "verified": True}

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            marker = Path(temp_dir) / "current_codex_tty.json"
            marker.write_text('{"tty": "ttys001"}', encoding="utf-8")

            result = deliver_prompt_to_terminal(
                "Hlasový pokyn od Míly.",
                runner=fake_runner,
                ps_runner=fake_ps_runner,
                marked_tty_path=marker,
                tty_deliverer=fake_tty_deliverer,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "delivered_tty")
        self.assertEqual(tty_calls[0][0], "ttys002")
        self.assertEqual(result["auto_target_tty"], "ttys002")
        self.assertEqual(result["marked_tty_status"]["target_tty"], "ttys001")
        self.assertEqual(runner_calls, [])

    def test_deliver_prompt_uses_marked_tty_when_ps_detection_is_empty(self) -> None:
        runner_calls = []
        tty_calls = []

        def fake_runner(args, **kwargs):
            runner_calls.append(args)
            self.fail("GUI fallback should not run for marked tty")

        def fake_ps_runner(args, **kwargs):
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        def fake_tty_deliverer(tty, prompt, **kwargs):
            tty_calls.append((tty, prompt, kwargs))
            return {"ok": True, "status": "delivered_tty", "submitted": kwargs.get("submit"), "verified": False}

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            marker = Path(temp_dir) / "current_codex_tty.json"
            marker.write_text('{"tty": "ttys001"}', encoding="utf-8")

            result = deliver_prompt_to_terminal(
                "Hlasový pokyn od Míly.",
                runner=fake_runner,
                ps_runner=fake_ps_runner,
                marked_tty_path=marker,
                tty_deliverer=fake_tty_deliverer,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "delivered_tty")
        self.assertEqual(result["delivery_method"], "marked_tty")
        self.assertIn("nespouštím GUI fallback", result["message"])
        self.assertEqual(tty_calls[0][0], "ttys001")
        self.assertEqual(runner_calls, [])

    def test_deliver_prompt_does_not_use_gui_fallback_when_marked_tty_is_unverified(self) -> None:
        runner_calls = []
        tty_calls = []

        def fake_runner(args, **kwargs):
            runner_calls.append(args)
            self.fail("marked tty unverified delivery must not use GUI fallback")

        def fake_ps_runner(args, **kwargs):
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="100 1 ttys005 codex codex\n", stderr="")

        def fake_tty_deliverer(tty, prompt, **kwargs):
            tty_calls.append((tty, prompt, kwargs))
            return {"ok": True, "status": "delivered_tty", "submitted": kwargs.get("submit"), "verified": False}

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            marker = Path(temp_dir) / "current_codex_tty.json"
            marker.write_text('{"tty": "ttys005"}', encoding="utf-8")

            result = deliver_prompt_to_terminal(
                "Hlasový pokyn od Míly.",
                runner=fake_runner,
                ps_runner=fake_ps_runner,
                script="return \"delivered\"",
                marked_tty_path=marker,
                tty_deliverer=fake_tty_deliverer,
                vscode_fallback=False,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "delivered_tty")
        self.assertFalse(result["verified"])
        self.assertEqual(result["delivery_method"], "marked_tty")
        self.assertIn("nespouštím GUI fallback", result["message"])
        self.assertEqual(len(tty_calls), 1)
        self.assertEqual(runner_calls, [])

    def test_deliver_prompt_reports_marked_tty_and_vscode_failures(self) -> None:
        calls = []

        def fake_runner(args, **kwargs):
            calls.append(args)
            if len(calls) == 1:
                return subprocess.CompletedProcess(args=args, returncode=1, stdout="", stderr="No Terminal tab.")
            return subprocess.CompletedProcess(args=args, returncode=1, stdout="", stderr="osascript nemá povoleno posílání stisknutí kláves.")

        def fake_ps_runner(args, **kwargs):
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="100 1 ttys006 codex codex\n101 1 ttys007 codex codex\n", stderr="")

        def fake_tty_deliverer(tty, prompt, **kwargs):
            return {"ok": False, "status": "tty_delivery_failed", "message": "Operation not permitted", "target_tty": tty}

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            marker = Path(temp_dir) / "current_codex_tty.json"
            marker.write_text('{"tty": "ttys005"}', encoding="utf-8")

            result = deliver_prompt_to_terminal(
                "Hlasový pokyn od Míly.",
                runner=fake_runner,
                ps_runner=fake_ps_runner,
                script="error \"No Terminal tab.\"",
                vscode_script="error \"osascript nemá povoleno posílání stisknutí kláves.\"",
                marked_tty_path=marker,
                tty_deliverer=fake_tty_deliverer,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "terminal_delivery_failed")
        self.assertIn("No Terminal tab.", result["message"])
        self.assertIn("TTY ttys005: Označené TTY ttys005 už nepatří aktivní Codex relaci.", result["message"])
        self.assertIn("VS Code fallback: osascript nemá povoleno", result["message"])
        self.assertEqual(result["marked_tty_status"]["target_tty"], "ttys005")
        self.assertEqual(result["vscode_status"]["status"], "vscode_delivery_failed")

    def test_terminal_gui_fallback_targets_marked_tty_after_direct_tty_failure(self) -> None:
        calls = []

        def fake_runner(args, **kwargs):
            calls.append(args)
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="delivered\n", stderr="")

        def fake_ps_runner(args, **kwargs):
            return subprocess.CompletedProcess(
                args=args,
                returncode=0,
                stdout=(
                    "100 1 ttys004 node /usr/local/bin/codex -C /repo .\n"
                    "101 1 ttys005 node /usr/local/bin/codex -C /repo .\n"
                ),
                stderr="",
            )

        def fake_tty_deliverer(tty, prompt, **kwargs):
            return {"ok": False, "status": "tty_delivery_failed", "message": "Operation not permitted", "target_tty": tty}

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            marker = Path(temp_dir) / "current_codex_tty.json"
            marker.write_text('{"tty": "ttys005"}', encoding="utf-8")

            result = deliver_prompt_to_terminal(
                "Hlasový pokyn od Míly.",
                runner=fake_runner,
                ps_runner=fake_ps_runner,
                script="return \"delivered\"",
                marked_tty_path=marker,
                tty_deliverer=fake_tty_deliverer,
                vscode_fallback=False,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "delivered")
        self.assertEqual(calls[0][-1], "ttys005")
        self.assertEqual(result["target_ttys"], ["ttys004", "ttys005"])

    def test_terminal_applescript_prefers_target_ttys_before_any_codex_tab(self) -> None:
        script = terminal_applescript()

        target_index = script.index("if targetTtys contains tabTty then")
        codex_index = script.index('if tabProcesses contains "codex" then')

        self.assertLess(target_index, codex_index)

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
