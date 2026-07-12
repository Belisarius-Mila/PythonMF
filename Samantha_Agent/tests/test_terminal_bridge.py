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
    deliver_prompt_to_screen_session,
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
        self.assertIn("zapiš stejný stručný výsledek do Cockpitu", prompt)
        self.assertIn("scripts/adam_voice_reply.py --processing-started", prompt)
        self.assertIn("scripts/speak_edge_open.py", prompt)
        self.assertIn("Nespouštěj zároveň Mac TTS", prompt)
        self.assertIn("Cockpit audiokanál odpověď přehraje", prompt)
        self.assertIn("scripts/adam_voice_reply.py --latest-command", prompt)
        self.assertIn("scripts/tvbcp.py append --mila", prompt)
        self.assertIn("plné věcné znění", prompt)
        self.assertIn("TVBCP není kopie chatu", prompt)
        self.assertIn("vynech technické mezistavy", prompt)

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

    def test_outbound_sms_prompt_is_routed_to_codex_with_send_confirmation_warning(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            latest = Path(temp_dir) / "latest_voice_command.md"
            write_voice_command(latest, "Pošli SMS Janičce, jestli něco nepotřebuje.")
            command = load_latest_voice_command(inbox_dir=Path(temp_dir))

        decision = assess_terminal_bridge(command)
        prompt = build_codex_terminal_prompt(command)

        self.assertTrue(decision["ok"])
        self.assertEqual(decision["status"], "allowed")
        self.assertEqual(command.triage.risk, "outbound_confirmation")
        self.assertIn("smíš připravit návrh/draft", prompt)
        self.assertIn("samostatné přesné potvrzovací větě", prompt)

    def test_deliver_prompt_uses_osascript_arguments_without_shell(self) -> None:
        calls = []

        def fake_runner(args, **kwargs):
            calls.append({"args": args, **kwargs})
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="delivered\n", stderr="")

        def fake_ps_runner(args, **kwargs):
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="100 1 ttys000 codex codex\n", stderr="")

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
        self.assertEqual(calls[0]["args"][-1], "ttys000")
        self.assertFalse(result["submitted"])
        self.assertFalse(result["verified"])
        self.assertEqual(result["status"], "terminal_delivery_unverified")

    def test_deliver_prompt_does_not_fall_back_to_vscode_when_terminal_is_missing(self) -> None:
        calls = []

        def fake_runner(args, **kwargs):
            calls.append({"args": args, **kwargs})
            if len(calls) == 1:
                return subprocess.CompletedProcess(args=args, returncode=1, stdout="", stderr="No Terminal tab.")
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="delivered_vscode\n", stderr="")

        def fake_ps_runner(args, **kwargs):
            return subprocess.CompletedProcess(
                args=args,
                returncode=0,
                stdout="100 1 ttys000 codex codex\n",
                stderr="",
            )

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            result = deliver_prompt_to_terminal(
                "Hlasový pokyn od Míly.",
                submit=True,
                runner=fake_runner,
                ps_runner=fake_ps_runner,
                script="error \"No Terminal tab.\"",
                vscode_script="return \"delivered_vscode\"",
                vscode_fallback=True,
                screen_session_name="",
                marked_tty_path=Path(temp_dir) / "missing_marker.json",
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "terminal_delivery_failed")
        self.assertEqual(len(calls), 1)

    def test_deliver_prompt_does_not_use_vscode_fallback_without_active_codex_session(self) -> None:
        calls = []

        def fake_runner(args, **kwargs):
            calls.append(args)
            if len(calls) == 1:
                return subprocess.CompletedProcess(args=args, returncode=1, stdout="", stderr="No Terminal tab.")
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="delivered_vscode\n", stderr="")

        def fake_ps_runner(args, **kwargs):
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            result = deliver_prompt_to_terminal(
                "Hlasový pokyn od Míly.",
                submit=True,
                runner=fake_runner,
                ps_runner=fake_ps_runner,
                script="error \"No Terminal tab.\"",
                vscode_script="return \"delivered_vscode\"",
                vscode_fallback=True,
                screen_session_name="",
                marked_tty_path=Path(temp_dir) / "missing_marker.json",
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "no_active_codex_session")
        self.assertIn("Zprávu nikam neposílám", result["message"])
        self.assertEqual(len(calls), 0)

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
        self.assertEqual(result["status"], "vscode_delivery_unverified")
        self.assertEqual(calls[0]["args"][0], "/usr/bin/osascript")
        self.assertEqual(calls[0]["args"][-1], "0")
        self.assertFalse(result["submitted"])
        self.assertFalse(result["verified"])
        self.assertEqual(result["delivery_method"], "local_gui_vscode")

    def test_deliver_prompt_to_screen_session_uses_screen_stuff_with_submit(self) -> None:
        calls = []

        def fake_runner(args, **kwargs):
            calls.append({"args": args, **kwargs})
            if args == ["screen", "-ls"]:
                return subprocess.CompletedProcess(args=args, returncode=0, stdout="\t93159.samantha_codex\t(Attached)\n", stderr="")
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        sleeps = []

        result = deliver_prompt_to_screen_session("První řádek\nDruhý řádek", runner=fake_runner, sleeper=sleeps.append)

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "screen_delivery_unverified")
        self.assertEqual(result["delivery_method"], "screen_stuff")
        self.assertEqual(calls[1]["args"][:7], ["screen", "-S", "samantha_codex", "-p", "0", "-X", "stuff"])
        payload = calls[1]["args"][-1]
        self.assertTrue(payload.startswith("\x15"))
        self.assertIn("\x1b[200~", payload)
        self.assertTrue(payload.endswith("\x1b[201~"))
        self.assertFalse(payload.endswith("\r"))
        self.assertIn("První řádek Druhý řádek", payload)
        self.assertEqual(calls[2]["args"], ["screen", "-S", "samantha_codex", "-p", "0", "-X", "stuff", "\r"])
        self.assertEqual(sleeps, [1.0])
        self.assertFalse(result["verified"])

    def test_deliver_prompt_skips_screen_fallback_and_targets_single_codex_tab(self) -> None:
        calls = []

        def fake_runner(args, **kwargs):
            calls.append(args)
            if args == ["screen", "-ls"]:
                return subprocess.CompletedProcess(args=args, returncode=0, stdout="\t93159.samantha_codex\t(Attached)\n", stderr="")
            if args[:6] == ["screen", "-S", "samantha_codex", "-p", "0", "-X"]:
                return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="delivered\n", stderr="")

        def fake_ps_runner(args, **kwargs):
            return subprocess.CompletedProcess(
                args=args,
                returncode=0,
                stdout="100 1 ttys000 codex codex\n",
                stderr="",
            )

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            result = deliver_prompt_to_terminal(
                "Hlasový pokyn od Míly.",
                submit=True,
                runner=fake_runner,
                ps_runner=fake_ps_runner,
                tty_deliverer=lambda *args, **kwargs: {
                    "ok": False,
                    "status": "tty_delivery_failed",
                    "message": "TIOCSTI blocked",
                },
                script="return \"delivered\"",
                marked_tty_path=Path(temp_dir) / "missing_marker.json",
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "terminal_delivery_unverified")
        self.assertIsNone(result["screen_status"])
        self.assertFalse(result["verified"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "/usr/bin/osascript")

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

    def test_discover_codex_ttys_does_not_climb_from_duplicate_child_to_screen(self) -> None:
        def fake_ps_runner(args, **kwargs):
            return subprocess.CompletedProcess(
                args=args,
                returncode=0,
                stdout=(
                    "17981 74488 ttys003 screen screen -U -S samantha_codex /repo/scripts/samantha_screen_entry.sh\n"
                    "18044 17981 ?? SCREEN SCREEN\n"
                    "18045 18044 ttys000 login login -pflq user /repo/scripts/samantha_screen_entry.sh\n"
                    "18046 18045 ttys000 zsh /bin/zsh /repo/scripts/samantha_screen_entry.sh\n"
                    "18101 18046 ttys000 node node /usr/local/bin/codex -C /repo .\n"
                    "18102 18101 ttys000 codex /vendor/bin/codex -C /repo .\n"
                ),
                stderr="",
            )

        self.assertEqual(discover_codex_ttys(runner=fake_ps_runner), ["ttys000"])

    def test_discover_codex_ttys_ignores_stale_codex_processes(self) -> None:
        def fake_ps_runner(args, **kwargs):
            return subprocess.CompletedProcess(
                args=args,
                returncode=0,
                stdout=(
                    "100 1 ttys000 2-01:00:00 node /usr/local/bin/codex -C /repo .\n"
                    "101 100 ttys000 2-01:00:00 codex /vendor/bin/codex -C /repo .\n"
                    "200 1 ttys001 00:05:00 node /usr/local/bin/codex -C /repo .\n"
                ),
                stderr="",
            )

        self.assertEqual(discover_codex_ttys(runner=fake_ps_runner), ["ttys001"])

    def test_discover_codex_ttys_keeps_foreground_long_running_screen_codex(self) -> None:
        def fake_ps_runner(args, **kwargs):
            return subprocess.CompletedProcess(
                args=args,
                returncode=0,
                stdout=(
                    "53943 53941 ttys000 Ss+ 2-01:00:00 login login -pflq user /repo/scripts/samantha_screen_entry.sh\n"
                    "53945 53943 ttys000 S+ 2-01:00:00 zsh /bin/zsh /repo/scripts/samantha_screen_entry.sh\n"
                    "54094 53945 ttys000 S+ 2-01:00:00 node node /usr/local/bin/codex -C /repo .\n"
                    "54105 54094 ttys000 S+ 2-01:00:00 codex /vendor/bin/codex -C /repo .\n"
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

    def test_deliver_prompt_refuses_other_codex_tty_when_marker_is_stale(self) -> None:
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

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "stale_marked_tty")
        self.assertEqual(result["target_tty"], "ttys001")
        self.assertEqual(tty_calls, [])
        self.assertEqual(runner_calls, [])

    def test_deliver_prompt_refuses_marked_tty_when_ps_detection_is_empty(self) -> None:
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

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "no_active_codex_session")
        self.assertEqual(tty_calls, [])
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
        self.assertEqual(result["delivery_method"], "marked_tty")
        self.assertEqual(len(tty_calls), 1)
        self.assertEqual(runner_calls, [])

    def test_deliver_prompt_reports_stale_marker_without_any_fallback(self) -> None:
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
                screen_session_name="",
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "stale_marked_tty")
        self.assertIn("nevybírám jiný chat automaticky", result["message"])
        self.assertEqual(result["target_tty"], "ttys005")
        self.assertEqual(calls, [])

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
                screen_session_name="",
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "terminal_delivery_unverified")
        self.assertFalse(result["verified"])
        self.assertEqual(calls[0][-1], "ttys005")
        self.assertEqual(result["target_ttys"], ["ttys004", "ttys005"])

    def test_deliver_prompt_uses_only_validated_main_screen_after_direct_tty_failure(self) -> None:
        runner_calls = []
        screen_calls = []

        def fake_runner(args, **kwargs):
            runner_calls.append(args)
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="delivered\n", stderr="")

        def fake_ps_runner(args, **kwargs):
            return subprocess.CompletedProcess(
                args=args,
                returncode=0,
                stdout=(
                    "100 1 ?? Ss 00:10:00 screen screen -S samantha_codex /repo/scripts/samantha_screen_entry.sh\n"
                    "101 100 ttys005 Ss+ 00:10:00 login login -pflq user /repo/scripts/samantha_screen_entry.sh\n"
                    "102 101 ttys005 S+ 00:10:00 codex codex -C /repo .\n"
                ),
                stderr="",
            )

        def fake_tty_deliverer(tty, prompt, **kwargs):
            return {"ok": False, "status": "tty_delivery_failed", "message": "Operation not permitted", "target_tty": tty}

        def fake_screen_deliverer(prompt, **kwargs):
            screen_calls.append({"prompt": prompt, "kwargs": kwargs})
            return {
                "ok": True,
                "status": "delivered_screen",
                "message": "screen ok",
                "delivery_method": "screen_stuff",
                "verified": True,
            }

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            marker = Path(temp_dir) / "current_codex_tty.json"
            marker.write_text('{"tty": "ttys005"}', encoding="utf-8")

            result = deliver_prompt_to_terminal(
                "Hlasový pokyn od Míly.",
                runner=fake_runner,
                ps_runner=fake_ps_runner,
                marked_tty_path=marker,
                tty_deliverer=fake_tty_deliverer,
                screen_deliverer=fake_screen_deliverer,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "screen_delivery_unverified")
        self.assertEqual(result["delivery_method"], "validated_screen_stuff")
        self.assertFalse(result["verified"])
        self.assertEqual(result["marked_tty_status"]["status"], "tty_delivery_failed")
        self.assertEqual(screen_calls[0]["kwargs"]["session_name"], "samantha_codex")
        self.assertEqual(runner_calls, [])

    def test_terminal_applescript_prefers_target_ttys_before_any_codex_tab(self) -> None:
        script = terminal_applescript()

        target_index = script.index("if targetTtys contains tabTty then")
        codex_index = script.index('if tabProcesses contains "codex" then')

        self.assertLess(target_index, codex_index)
        self.assertIn("if not foundTarget and (count of targetTtys) is 0 then", script)

    def test_terminal_applescript_submits_directly_to_selected_target_tab(self) -> None:
        script = terminal_applescript()

        self.assertIn("set targetTab to terminalTab", script)
        self.assertIn('if shouldSubmit is "1" then', script)
        self.assertIn("do script promptText in targetTab", script)
        self.assertIn("do script (ASCII character 13) in targetTab", script)
        self.assertNotIn("key code 36", script)

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
