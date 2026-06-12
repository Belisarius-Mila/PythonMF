from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from app.speech.adam_voice_mode import (
    append_manual_voice_history_turn,
    build_spoken_result_for_command,
    clear_codex_approval_request,
    format_voice_history_for_prompt,
    generate_direct_voice_response,
    handle_voice_command,
    load_codex_approval_request,
    load_last_adam_response,
    load_pending_for_adam,
    load_voice_history,
    load_voice_mode_status,
    mark_pending_for_adam_processed,
    save_codex_approval_request,
    spoken_notice_for_command,
    update_pending_approval,
    voice_command_needs_codex_work,
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
            pending_path = inbox / "pending_for_adam.json"
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(latest, "Připrav návrh odpovědi.")
            command = load_latest_voice_command(inbox_dir=inbox)

            result = handle_voice_command(
                command,
                response_generator=lambda text: "Návrh odpovědi je připravený.",
                should_speak=False,
                status_path=status_path,
                pending_path=pending_path,
                history_path=history_path,
            )
            payload = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertTrue(result["ok"])
        self.assertEqual(result["speech"]["transport"], "disabled")
        self.assertEqual(payload["state"], "command_ready")
        self.assertEqual(payload["last_command"]["text"], "Připrav návrh odpovědi.")

    def test_handle_voice_command_speaks_generated_response_not_input_text(self) -> None:
        spoken = []

        def fake_speak(text, **kwargs):
            spoken.append(text)
            return {"ok": True, "transport": "fake", "message": "Přečteno."}

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            latest = inbox / "latest_voice_command.md"
            status_path = inbox / "adam_voice_mode_status.json"
            pending_path = inbox / "pending_for_adam.json"
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(latest, "Adame, Janička přijela a zdraví Tě. Co jí řekneš?")
            command = load_latest_voice_command(inbox_dir=inbox)

            result = handle_voice_command(
                command,
                speak=fake_speak,
                response_generator=lambda text: "Ahoj Janičko, rád tě poznávám. Můžu pro tebe něco udělat?",
                status_path=status_path,
                pending_path=pending_path,
                history_path=history_path,
            )

        self.assertEqual(spoken, ["Ahoj Janičko, rád tě poznávám. Můžu pro tebe něco udělat?"])
        self.assertEqual(result["response"], spoken[0])
        self.assertNotIn("Janička přijela", spoken[0])

    def test_build_spoken_result_routes_codex_work_without_claiming_done(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            latest = inbox / "latest_voice_command.md"
            pending_path = inbox / "pending_for_adam.json"
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(latest, "Adame, najdi stav dokumentů v Cockpitu.")
            command = load_latest_voice_command(inbox_dir=inbox)

        response = build_spoken_result_for_command(
            command,
            response_generator=lambda text: self.fail("work command should not call direct responder"),
            pending_path=pending_path,
            history_path=history_path,
        )

        self.assertIn("vyžaduje pracovní převzetí", response)
        pending = json.loads(pending_path.read_text(encoding="utf-8"))
        self.assertTrue(pending["pending"])
        self.assertEqual(pending["reason"], "codex_work")
        self.assertEqual(pending["text"], "Adame, najdi stav dokumentů v Cockpitu.")

    def test_build_spoken_result_saves_outbound_message_for_confirmation_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            latest = inbox / "latest_voice_command.md"
            pending_path = inbox / "pending_for_adam.json"
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(latest, "Pošli SMS Janičce, jestli něco nepotřebuje.")
            command = load_latest_voice_command(inbox_dir=inbox)

            response = build_spoken_result_for_command(
                command,
                response_generator=lambda text: self.fail("outbound command should not call direct responder"),
                pending_path=pending_path,
                history_path=history_path,
            )
            pending = json.loads(pending_path.read_text(encoding="utf-8"))

        self.assertIn("můžu připravit odchozí SMS nebo e-mail", response)
        self.assertIn("samostatné potvrzení", response)
        self.assertNotIn("rizikový nebo mění data", response)
        self.assertTrue(pending["pending"])
        self.assertEqual(pending["reason"], "outbound_confirmation")
        self.assertEqual(pending["command"]["triage"]["risk"], "outbound_confirmation")

    def test_build_spoken_result_can_route_safe_codex_work_to_terminal_bridge(self) -> None:
        calls = []

        def fake_terminal_bridge(command):
            calls.append(command.text)
            return {"ok": True, "status": "delivered", "verified": True}

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            latest = inbox / "latest_voice_command.md"
            pending_path = inbox / "pending_for_adam.json"
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(latest, "Kolik jsme dnes napsali řádků kódu?")
            command = load_latest_voice_command(inbox_dir=inbox)

            response = build_spoken_result_for_command(
                command,
                response_generator=lambda text: self.fail("work command should not call direct responder"),
                pending_path=pending_path,
                history_path=history_path,
                terminal_bridge=fake_terminal_bridge,
            )
            history = load_voice_history(path=history_path, limit=2)

        self.assertEqual(calls, ["Kolik jsme dnes napsali řádků kódu?"])
        self.assertIn("vložil do Codex terminálu", response)
        self.assertFalse(pending_path.exists())
        self.assertEqual(history, [])

    def test_build_spoken_result_routes_write_to_chat_test_to_terminal_bridge(self) -> None:
        calls = []

        def fake_terminal_bridge(command):
            calls.append(command.text)
            return {"ok": True, "status": "delivered", "verified": True}

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            latest = inbox / "latest_voice_command.md"
            pending_path = inbox / "pending_for_adam.json"
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(latest, "Adame, napiš do chatu: test hlasového bridge jedna.")
            command = load_latest_voice_command(inbox_dir=inbox)

            response = build_spoken_result_for_command(
                command,
                response_generator=lambda text: self.fail("work command should not call direct responder"),
                pending_path=pending_path,
                history_path=history_path,
                terminal_bridge=fake_terminal_bridge,
            )
            history = load_voice_history(path=history_path, limit=2)

        self.assertEqual(calls, ["Adame, napiš do chatu: test hlasového bridge jedna."])
        self.assertIn("vložil do Codex terminálu", response)
        self.assertFalse(pending_path.exists())
        self.assertEqual(history, [])

    def test_terminal_bridge_success_clears_matching_pending_command(self) -> None:
        def fake_terminal_bridge(command):
            return {"ok": True, "status": "delivered", "verified": True}

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            latest = inbox / "latest_voice_command.md"
            pending_path = inbox / "pending_for_adam.json"
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(latest, "Adame, napiš do chatu: test hlasového bridge jedna.")
            command = load_latest_voice_command(inbox_dir=inbox)
            build_spoken_result_for_command(command, pending_path=pending_path, history_path=history_path)

            response = build_spoken_result_for_command(
                command,
                response_generator=lambda text: self.fail("work command should not call direct responder"),
                pending_path=pending_path,
                history_path=history_path,
                terminal_bridge=fake_terminal_bridge,
            )
            pending = json.loads(pending_path.read_text(encoding="utf-8"))

        self.assertIn("vložil do Codex terminálu", response)
        self.assertFalse(pending["pending"])
        self.assertEqual(pending["status"], "processed_by_terminal_bridge")

    def test_terminal_bridge_unverified_delivery_stays_pending(self) -> None:
        def fake_terminal_bridge(command):
            return {"ok": True, "status": "delivered_tty", "message": "TIOCSTI accepted bytes.", "verified": False}

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            latest = inbox / "latest_voice_command.md"
            pending_path = inbox / "pending_for_adam.json"
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(latest, "Zkontroluj stav hlasového bridge.")
            command = load_latest_voice_command(inbox_dir=inbox)

            response = build_spoken_result_for_command(
                command,
                response_generator=lambda text: self.fail("work command should not call direct responder"),
                pending_path=pending_path,
                history_path=history_path,
                terminal_bridge=fake_terminal_bridge,
            )
            pending = json.loads(pending_path.read_text(encoding="utf-8"))
            history = load_voice_history(path=history_path, limit=2)

        self.assertIn("neumím ověřit", response)
        self.assertTrue(pending["pending"])
        self.assertEqual(pending["reason"], "terminal_delivery_unverified")
        self.assertEqual(history[0]["route"], "terminal_delivery_unverified")

    def test_build_spoken_result_saves_pending_when_terminal_bridge_rejects(self) -> None:
        def fake_terminal_bridge(command):
            return {"ok": False, "status": "manual_required", "reason": "Změnový pokyn."}

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            latest = inbox / "latest_voice_command.md"
            pending_path = inbox / "pending_for_adam.json"
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(latest, "Najdi stav Cockpitu.")
            command = load_latest_voice_command(inbox_dir=inbox)

            response = build_spoken_result_for_command(
                command,
                response_generator=lambda text: self.fail("work command should not call direct responder"),
                pending_path=pending_path,
                history_path=history_path,
                terminal_bridge=fake_terminal_bridge,
            )
            pending = json.loads(pending_path.read_text(encoding="utf-8"))

        self.assertIn("ruční přesnou formulaci", response)
        self.assertTrue(pending["pending"])
        self.assertEqual(pending["reason"], "manual_required")

    def test_build_spoken_result_explains_terminal_delivery_failure_as_technical(self) -> None:
        def fake_terminal_bridge(command):
            return {"ok": False, "status": "terminal_delivery_failed", "message": "Nenalezen Terminal tab."}

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            latest = inbox / "latest_voice_command.md"
            pending_path = inbox / "pending_for_adam.json"
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(latest, "Kolik jsme dnes napsali řádků kódu?")
            command = load_latest_voice_command(inbox_dir=inbox)

            response = build_spoken_result_for_command(
                command,
                response_generator=lambda text: self.fail("work command should not call direct responder"),
                pending_path=pending_path,
                history_path=history_path,
                terminal_bridge=fake_terminal_bridge,
            )
            pending = json.loads(pending_path.read_text(encoding="utf-8"))

        self.assertIn("bezpečnostně pustil", response)
        self.assertIn("technicky", response)
        self.assertEqual(pending["reason"], "terminal_delivery_failed")

    def test_handle_voice_command_saves_codex_work_as_pending_for_adam(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            latest = inbox / "latest_voice_command.md"
            status_path = inbox / "adam_voice_mode_status.json"
            pending_path = inbox / "pending_for_adam.json"
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(latest, "Adame, kolik jsme dnes napsali řádků kódu?")
            command = load_latest_voice_command(inbox_dir=inbox)

            result = handle_voice_command(
                command,
                response_generator=lambda text: self.fail("work command should not call direct responder"),
                should_speak=False,
                status_path=status_path,
                pending_path=pending_path,
                history_path=history_path,
            )
            status = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertEqual(status["state"], "pending_for_adam")
        self.assertTrue(result["pending_for_adam"]["pending"])
        self.assertEqual(result["pending_for_adam"]["reason"], "codex_work")
        self.assertIn("řádků kódu", result["pending_for_adam"]["text"])

    def test_load_pending_for_adam_reports_missing_file(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            pending = load_pending_for_adam(path=Path(temp_dir) / "pending_for_adam.json")

        self.assertTrue(pending["ok"])
        self.assertFalse(pending["pending"])
        self.assertEqual(pending["status"], "none")

    def test_codex_approval_request_roundtrip_and_status(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            approval_path = Path(temp_dir) / "codex_approval_request.json"
            saved = save_codex_approval_request(
                reason="Codex potřebuje povolit kontrolu procesu.",
                command="ps -o pid,command -ax",
                next_step="Na iPhonu otevři Codex a rozhodni systémové potvrzení.",
                path=approval_path,
            )
            loaded = load_codex_approval_request(path=approval_path)
            status = load_voice_mode_status(
                status_path=Path(temp_dir) / "missing_status.json",
                pending_path=Path(temp_dir) / "missing_pending.json",
                history_path=Path(temp_dir) / "missing_history.jsonl",
                last_response_path=Path(temp_dir) / "missing_response.json",
                codex_approval_path=approval_path,
            )
            cleared = clear_codex_approval_request(note="Vyřešeno.", path=approval_path)

        self.assertTrue(saved["active"])
        self.assertEqual(loaded["status"], "waiting_for_codex_approval")
        self.assertTrue(status["codex_approval"]["active"])
        self.assertIn("kontrolu procesu", status["codex_approval"]["reason"])
        self.assertFalse(cleared["active"])
        self.assertEqual(cleared["status"], "cleared")

    def test_append_history_saves_last_adam_response_for_cockpit(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            history_path = Path(temp_dir) / "adam_voice_history.jsonl"
            response_path = Path(temp_dir) / "last_adam_response.json"

            append_manual_voice_history_turn(
                user_text="Kolik máme testů?",
                adam_response="Máme cílenou testovací sadu pro hlasový režim.",
                path=history_path,
                response_path=response_path,
            )
            last_response = load_last_adam_response(path=response_path)
            status = load_voice_mode_status(
                status_path=Path(temp_dir) / "missing_status.json",
                pending_path=Path(temp_dir) / "missing_pending.json",
                history_path=history_path,
                last_response_path=response_path,
            )

        self.assertTrue(last_response["available"])
        self.assertEqual(last_response["route"], "codex_manual")
        self.assertIn("testovací sadu", last_response["adam_response"])
        self.assertEqual(status["last_adam_response"]["adam_response"], last_response["adam_response"])

    def test_load_voice_mode_status_uses_history_as_last_response_fallback(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            history_path = Path(temp_dir) / "adam_voice_history.jsonl"
            append_manual_voice_history_turn(
                user_text="Co je hotovo?",
                adam_response="Hotové je přehrání odpovědi přes Cockpit.",
                path=history_path,
            )

            status = load_voice_mode_status(
                status_path=Path(temp_dir) / "missing_status.json",
                pending_path=Path(temp_dir) / "missing_pending.json",
                history_path=history_path,
                last_response_path=Path(temp_dir) / "missing_last_response.json",
            )

        self.assertTrue(status["last_adam_response"]["available"])
        self.assertEqual(status["last_adam_response"]["source"], "voice_history")
        self.assertIn("přehrání odpovědi", status["last_adam_response"]["adam_response"])

    def test_update_pending_approval_can_approve_and_reject_from_cockpit(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            pending_path = inbox / "pending_for_adam.json"
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(inbox / "latest_voice_command.md", "Pošli SMS Janičce, jestli něco nepotřebuje.")
            command = load_latest_voice_command(inbox_dir=inbox)
            build_spoken_result_for_command(command, pending_path=pending_path, history_path=history_path)

            approved = update_pending_approval(decision="approved", note="Schváleno v testu.", path=pending_path)
            rejected = update_pending_approval(decision="rejected", path=pending_path)

        self.assertTrue(approved["ok"])
        self.assertTrue(approved["pending"])
        self.assertEqual(approved["status"], "approved_in_cockpit")
        self.assertEqual(approved["approval_status"], "approved")
        self.assertTrue(rejected["ok"])
        self.assertFalse(rejected["pending"])
        self.assertEqual(rejected["status"], "rejected_by_user")
        self.assertEqual(rejected["approval_status"], "rejected")

    def test_voice_command_needs_codex_work_keeps_greetings_direct(self) -> None:
        self.assertFalse(voice_command_needs_codex_work("Janička přijela a zdraví tě. Co jí řekneš?"))
        self.assertTrue(voice_command_needs_codex_work("Najdi stav dokumentů v Cockpitu."))
        self.assertTrue(voice_command_needs_codex_work("Adame, napiš stručně stav hlasového brydže."))

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

    def test_load_voice_mode_status_treats_stopped_state_as_not_running(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            status_path = Path(temp_dir) / "status.json"
            write_voice_mode_status(
                status_path=status_path,
                state="stopped",
                message="Watcher byl zastaven.",
            )

            status = load_voice_mode_status(status_path=status_path)

        self.assertFalse(status["running"])
        self.assertEqual(status["state"], "stopped")

    def test_adam_voice_mode_cli_can_process_existing_command_and_stops_after_count(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            status_path = inbox / "status.json"
            pending_path = inbox / "pending_for_adam.json"
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(inbox / "latest_voice_command.md", "Najdi stav projektu Dokumenty.")
            completed = subprocess.run(
                [
                    ".venv/bin/python",
                    "scripts/adam_voice_mode.py",
                    "--inbox-dir",
                    str(inbox),
                    "--status-path",
                    str(status_path),
                    "--pending-path",
                    str(pending_path),
                    "--history-path",
                    str(history_path),
                    "--include-existing",
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
            payload = json.loads(status_path.read_text(encoding="utf-8"))
            pending = json.loads(pending_path.read_text(encoding="utf-8"))

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("VOICE INBOX TRIAGE", completed.stdout)
        self.assertIn("ADAM VOICE MODE RESPONSE", completed.stdout)
        self.assertIn("Najdi stav projektu Dokumenty.", completed.stdout)
        self.assertEqual(payload["state"], "completed")
        self.assertEqual(payload["last_command"]["text"], "Najdi stav projektu Dokumenty.")
        self.assertEqual(pending["reason"], "codex_work")

    def test_adam_voice_pending_cli_prints_waiting_command(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            pending_path = Path(temp_dir) / "pending_for_adam.json"
            history_path = Path(temp_dir) / "adam_voice_history.jsonl"
            latest = Path(temp_dir) / "latest_voice_command.md"
            write_voice_command(latest, "Zkontroluj dnešní řádky kódu.")
            command = load_latest_voice_command(inbox_dir=Path(temp_dir))
            save_result = build_spoken_result_for_command(
                command,
                pending_path=pending_path,
                history_path=history_path,
            )
            completed = subprocess.run(
                [
                    ".venv/bin/python",
                    "scripts/adam_voice_pending.py",
                    "--path",
                    str(pending_path),
                    "--history-path",
                    str(history_path),
                ],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )

        self.assertIn("pracovní převzetí", save_result)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("ADAM VOICE PENDING", completed.stdout)
        self.assertIn("pending: true", completed.stdout)
        self.assertIn("Zkontroluj dnešní řádky kódu.", completed.stdout)

    def test_direct_response_prompt_includes_recent_voice_history(self) -> None:
        captured = {}

        class FakeResult:
            final_output = "Minule ses ptal na řádky kódu."

        def fake_runner(agent, prompt):
            captured["prompt"] = prompt
            return FakeResult()

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            history_path = Path(temp_dir) / "adam_voice_history.jsonl"
            append_manual_voice_history_turn(
                user_text="Kolik jsme dnes napsali řádků kódu?",
                adam_response="Dnes jsme upravili hlasový režim.",
                path=history_path,
            )
            response = generate_direct_voice_response(
                "Co jsem se ptal minule?",
                history_path=history_path,
                runner=fake_runner,
            )

        self.assertEqual(response, "Minule ses ptal na řádky kódu.")
        self.assertIn("Nedávná hlasová historie", captured["prompt"])
        self.assertIn("Kolik jsme dnes napsali řádků kódu?", captured["prompt"])
        self.assertIn("Co jsem se ptal minule?", captured["prompt"])

    def test_handle_voice_command_records_direct_response_history(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            latest = inbox / "latest_voice_command.md"
            status_path = inbox / "status.json"
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(latest, "Co jí řekneš?")
            command = load_latest_voice_command(inbox_dir=inbox)

            handle_voice_command(
                command,
                response_generator=lambda text: "Ahoj, rád tě poznávám.",
                should_speak=False,
                status_path=status_path,
                pending_path=None,
                history_path=history_path,
            )
            history = load_voice_history(path=history_path, limit=2)

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["route"], "direct_response")
        self.assertEqual(history[0]["user_text"], "Co jí řekneš?")
        self.assertEqual(history[0]["adam_response"], "Ahoj, rád tě poznávám.")
        self.assertIn("Míla: Co jí řekneš?", format_voice_history_for_prompt(history))

    def test_pending_command_carries_recent_voice_history(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            pending_path = inbox / "pending_for_adam.json"
            history_path = inbox / "adam_voice_history.jsonl"
            append_manual_voice_history_turn(
                user_text="Co jsme řešili?",
                adam_response="Řešili jsme hlasový režim.",
                path=history_path,
            )
            write_voice_command(inbox / "latest_voice_command.md", "Najdi stav Cockpitu.")
            command = load_latest_voice_command(inbox_dir=inbox)

            build_spoken_result_for_command(
                command,
                response_generator=lambda text: self.fail("work command should not call direct responder"),
                pending_path=pending_path,
                history_path=history_path,
            )
            pending = json.loads(pending_path.read_text(encoding="utf-8"))

        self.assertEqual(pending["reason"], "codex_work")
        self.assertEqual(pending["voice_history"][0]["user_text"], "Co jsme řešili?")

    def test_mark_pending_processed_records_codex_reply_in_history(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            pending_path = inbox / "pending_for_adam.json"
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(inbox / "latest_voice_command.md", "Kolik řádků kódu jsme napsali?")
            command = load_latest_voice_command(inbox_dir=inbox)
            build_spoken_result_for_command(command, pending_path=pending_path, history_path=history_path)

            result = mark_pending_for_adam_processed(
                adam_response="Dnes jsme upravili hlasový most a přidali testy.",
                path=pending_path,
                history_path=history_path,
            )
            history = load_voice_history(path=history_path, limit=3)

        self.assertTrue(result["ok"])
        self.assertFalse(result["pending"])
        self.assertEqual(result["status"], "processed_by_codex")
        self.assertEqual(history[-1]["route"], "codex_manual")
        self.assertIn("hlasový most", history[-1]["adam_response"])

    def test_adam_voice_reply_cli_marks_pending_processed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            pending_path = inbox / "pending_for_adam.json"
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(inbox / "latest_voice_command.md", "Najdi stav hlasového režimu.")
            command = load_latest_voice_command(inbox_dir=inbox)
            build_spoken_result_for_command(command, pending_path=pending_path, history_path=history_path)

            completed = subprocess.run(
                [
                    ".venv/bin/python",
                    "scripts/adam_voice_reply.py",
                    "--path",
                    str(pending_path),
                    "--history-path",
                    str(history_path),
                    "Hotovo, hlasový režim má uloženou historii.",
                ],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
            pending = json.loads(pending_path.read_text(encoding="utf-8"))
            history = load_voice_history(path=history_path, limit=3)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("ADAM VOICE REPLY", completed.stdout)
        self.assertFalse(pending["pending"])
        self.assertEqual(pending["status"], "processed_by_codex")
        self.assertEqual(history[-1]["route"], "codex_manual")
        self.assertIn("uloženou historii", history[-1]["adam_response"])

    def test_adam_voice_reply_cli_can_record_latest_terminal_command_without_pending(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(inbox / "latest_voice_command.md", "Zkontroluj iPhone Cockpit.")

            completed = subprocess.run(
                [
                    ".venv/bin/python",
                    "scripts/adam_voice_reply.py",
                    "--latest-command",
                    "--inbox-dir",
                    str(inbox),
                    "--history-path",
                    str(history_path),
                    "iPhone Cockpit už má novou hlasovou sekci.",
                ],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
            history = load_voice_history(path=history_path, limit=3)
            last_response = load_last_adam_response(path=inbox / "last_adam_response.json")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("recorded_latest_command_reply", completed.stdout)
        self.assertEqual(history[-1]["route"], "codex_terminal_final")
        self.assertEqual(history[-1]["user_text"], "Zkontroluj iPhone Cockpit.")
        self.assertIn("novou hlasovou sekci", last_response["adam_response"])

    def test_adam_voice_reply_cli_can_record_explicit_janicka_text_reply(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            history_path = inbox / "adam_voice_history.jsonl"

            completed = subprocess.run(
                [
                    ".venv/bin/python",
                    "scripts/adam_voice_reply.py",
                    "--inbox-dir",
                    str(inbox),
                    "--history-path",
                    str(history_path),
                    "--user-text",
                    "Jak funguje hlasový chat?",
                    "--route",
                    "janicka_text_bridge",
                    "Hlasový chat teď nepoužívej; Janička posílá text přímo do Codexu.",
                ],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
            history = load_voice_history(path=history_path, limit=3)
            last_response = load_last_adam_response(path=inbox / "last_adam_response.json")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("recorded_explicit_user_text_reply", completed.stdout)
        self.assertEqual(history[-1]["route"], "janicka_text_bridge")
        self.assertEqual(history[-1]["user_text"], "Jak funguje hlasový chat?")
        self.assertIn("posílá text přímo do Codexu", last_response["adam_response"])


if __name__ == "__main__":
    unittest.main()
