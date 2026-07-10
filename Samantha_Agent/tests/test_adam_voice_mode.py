from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.file_persistence import lock_path_for
from app.speech.adam_voice_mode import (
    append_manual_voice_history_turn,
    build_spoken_result_for_command,
    clear_codex_approval_request,
    format_automatic_watcher_response,
    format_voice_history_for_prompt,
    generate_direct_voice_response,
    handle_voice_command,
    load_codex_approval_request,
    load_last_adam_response,
    load_pending_for_adam,
    load_voice_history,
    load_voice_mode_status,
    mark_pending_for_adam_processed,
    save_pending_for_adam,
    save_last_adam_response,
    save_codex_approval_request,
    spoken_notice_for_command,
    update_pending_approval,
    voice_command_needs_codex_work,
    write_voice_mode_status,
)
from app.speech.voice_inbox import load_latest_voice_command, parse_voice_command_file


PROJECT_ROOT = Path(__file__).resolve().parents[1]


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
    def test_same_pending_command_save_is_idempotent_without_replace(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            pending_path = inbox / "pending_for_adam.json"
            write_voice_command(inbox / "latest_voice_command.md", "Zkontroluj stav Cockpitu.")
            command = load_latest_voice_command(inbox_dir=inbox)
            first = save_pending_for_adam(
                command,
                reason="codex_work",
                message="Čeká na Adama.",
                path=pending_path,
                history_path=inbox / "history.jsonl",
            )

            with patch("app.file_persistence.os.replace", side_effect=OSError("must not replace")):
                second = save_pending_for_adam(
                    command,
                    reason="codex_work",
                    message="Čeká na Adama.",
                    path=pending_path,
                    history_path=inbox / "history.jsonl",
                )

            self.assertEqual(second, first)
            self.assertTrue(second["pending"])
            self.assertEqual(second["status"], "pending_for_adam")

    def test_same_pending_approval_is_idempotent_without_replace(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            pending_path = root / "pending_for_adam.json"
            write_voice_command(root / "latest_voice_command.md", "Potvrď bezpečný test.")
            command = load_latest_voice_command(inbox_dir=root)
            save_pending_for_adam(
                command,
                reason="requires_confirmation",
                message="Čeká na potvrzení.",
                path=pending_path,
                history_path=root / "history.jsonl",
            )
            first = update_pending_approval(decision="approved", note="Schváleno.", path=pending_path)

            with patch("app.file_persistence.os.replace", side_effect=OSError("must not replace")):
                second = update_pending_approval(decision="approved", note="Schváleno.", path=pending_path)

            self.assertEqual(second, first)
            self.assertEqual(second["status"], "approved_in_cockpit")
            self.assertTrue(second["pending"])

    def test_two_processes_cannot_overwrite_different_pending_commands(self) -> None:
        script = """
import json
import sys
import time
from pathlib import Path
from app.speech.adam_voice_mode import save_pending_for_adam
from app.speech.voice_inbox import VoiceCommand, VoiceCommandTriage

pending_path = Path(sys.argv[1])
start_path = Path(sys.argv[2])
worker = sys.argv[3]
while not start_path.exists():
    time.sleep(0.01)
triage = VoiceCommandTriage(risk="read_only", action="execute_read_only", reason="test", requires_confirmation=False)
command = VoiceCommand(ok=True, path=f"/tmp/{worker}.md", created_at=f"2026-07-10T14:00:0{worker}+00:00", status="transcribed_only_not_executed", text=f"Pokyn {worker}", triage=triage, message="test")
result = save_pending_for_adam(command, reason="codex_work", message="Čeká na Adama.", path=pending_path, history_path=pending_path.parent / "history.jsonl")
print(json.dumps({"ok": result.get("ok"), "status": result.get("status")}, ensure_ascii=False))
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            pending_path = root / "pending_for_adam.json"
            start_path = root / "start"
            processes = [
                subprocess.Popen(
                    [sys.executable, "-c", script, str(pending_path), str(start_path), worker],
                    cwd=PROJECT_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for worker in ("1", "2")
            ]
            start_path.write_text("start\n", encoding="utf-8")
            outputs = [process.communicate(timeout=20) for process in processes]
            results = []
            for process, (stdout, stderr) in zip(processes, outputs, strict=True):
                self.assertEqual(process.returncode, 0, stderr)
                results.append(json.loads(stdout))
            pending = json.loads(pending_path.read_text(encoding="utf-8"))

        self.assertEqual(sum(1 for item in results if item["ok"]), 1)
        self.assertEqual(sum(1 for item in results if item["status"] == "pending_conflict"), 1)
        self.assertIn(pending["text"], {"Pokyn 1", "Pokyn 2"})
        self.assertTrue(pending["pending"])

    def test_two_processes_complete_pending_exactly_once(self) -> None:
        script = """
import json
import sys
import time
from pathlib import Path
from app.speech.adam_voice_mode import mark_pending_for_adam_processed

pending_path = Path(sys.argv[1])
history_path = Path(sys.argv[2])
start_path = Path(sys.argv[3])
worker = sys.argv[4]
while not start_path.exists():
    time.sleep(0.01)
result = mark_pending_for_adam_processed(adam_response=f"Odpověď {worker}", path=pending_path, history_path=history_path)
print(json.dumps({"ok": result.get("ok"), "status": result.get("status"), "response": result.get("response")}, ensure_ascii=False))
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            pending_path = root / "pending_for_adam.json"
            history_path = root / "history.jsonl"
            start_path = root / "start"
            write_voice_command(root / "latest_voice_command.md", "Dokonči test.")
            command = load_latest_voice_command(inbox_dir=root)
            save_pending_for_adam(
                command,
                reason="codex_work",
                message="Čeká na Adama.",
                path=pending_path,
                history_path=history_path,
            )
            processes = [
                subprocess.Popen(
                    [sys.executable, "-c", script, str(pending_path), str(history_path), str(start_path), worker],
                    cwd=PROJECT_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for worker in ("1", "2")
            ]
            start_path.write_text("start\n", encoding="utf-8")
            outputs = [process.communicate(timeout=20) for process in processes]
            results = []
            for process, (stdout, stderr) in zip(processes, outputs, strict=True):
                self.assertEqual(process.returncode, 0, stderr)
                results.append(json.loads(stdout))
            pending = json.loads(pending_path.read_text(encoding="utf-8"))
            history = [json.loads(line) for line in history_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(sum(1 for item in results if item["ok"]), 1)
        self.assertEqual(len(history), 1)
        self.assertEqual(pending["status"], "processed_by_codex")
        self.assertEqual(pending["response"], history[0]["adam_response"])

    def test_pending_conflict_is_reported_without_replacing_first_command(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            pending_path = root / "pending_for_adam.json"
            history_path = root / "history.jsonl"
            first_path = root / "first.md"
            second_path = root / "second.md"
            write_voice_command(first_path, "První pracovní pokyn.")
            write_voice_command(second_path, "Druhý pracovní pokyn.")
            first = parse_voice_command_file(first_path)
            second = parse_voice_command_file(second_path)
            save_pending_for_adam(
                first,
                reason="codex_work",
                message="První čeká.",
                path=pending_path,
                history_path=history_path,
            )

            response = build_spoken_result_for_command(
                second,
                response_generator=lambda text: self.fail("work command should not call direct responder"),
                pending_path=pending_path,
                history_path=history_path,
            )
            pending = json.loads(pending_path.read_text(encoding="utf-8"))
            history = load_voice_history(path=history_path, limit=3)

        self.assertIn("Předchozí hlasový pokyn stále čeká", response)
        self.assertEqual(pending["text"], "První pracovní pokyn.")
        self.assertEqual(history[-1]["route"], "pending_conflict")

    def test_voice_status_uses_atomic_locked_json_write(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            status_path = Path(temp_dir) / "adam_voice_mode_status.json"

            payload = write_voice_mode_status(
                status_path=status_path,
                state="listening",
                message="Watcher běží.",
            )

            self.assertEqual(json.loads(status_path.read_text(encoding="utf-8")), payload)
            self.assertTrue(lock_path_for(status_path).exists())
            self.assertEqual(list(status_path.parent.glob(f".{status_path.name}.*.tmp")), [])

    def test_last_response_uses_atomic_locked_json_write(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            response_path = Path(temp_dir) / "last_adam_response.json"

            payload = save_last_adam_response(
                user_text="Bezpečný test.",
                adam_response="Hotovo.",
                route="codex_manual",
                path=response_path,
            )

            self.assertEqual(json.loads(response_path.read_text(encoding="utf-8")), payload)
            self.assertTrue(lock_path_for(response_path).exists())
            self.assertEqual(list(response_path.parent.glob(f".{response_path.name}.*.tmp")), [])

    def test_voice_status_failed_replace_preserves_previous_json(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            status_path = Path(temp_dir) / "adam_voice_mode_status.json"
            previous = {"ok": True, "state": "listening", "message": "Původní stav."}
            status_path.write_text(json.dumps(previous, ensure_ascii=False) + "\n", encoding="utf-8")

            with patch("app.file_persistence.os.replace", side_effect=OSError("replace failed")):
                with self.assertRaises(OSError):
                    write_voice_mode_status(
                        status_path=status_path,
                        state="stopped",
                        message="Nový stav.",
                    )

            self.assertEqual(json.loads(status_path.read_text(encoding="utf-8")), previous)
            self.assertEqual(list(status_path.parent.glob(f".{status_path.name}.*.tmp")), [])

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

        self.assertEqual(
            spoken,
            [
                "Automatická odpověď watcheru, ne převzetí v Codex chatu: "
                "Ahoj Janičko, rád tě poznávám. Můžu pro tebe něco udělat?"
            ],
        )
        self.assertEqual(result["response"], spoken[0])
        self.assertNotIn("Janička přijela", spoken[0])

    def test_handle_voice_command_does_not_speak_pending_terminal_delivery_status(self) -> None:
        spoken = []

        def fake_speak(text, **kwargs):
            spoken.append(text)
            return {"ok": True, "transport": "fake", "message": "Přečteno."}

        def fake_terminal_bridge(command):
            return {"ok": True, "status": "delivered_screen", "verified": False}

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            latest = inbox / "latest_voice_command.md"
            status_path = inbox / "adam_voice_mode_status.json"
            pending_path = inbox / "pending_for_adam.json"
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(latest, "Zkontroluj stav hlasového režimu.")
            command = load_latest_voice_command(inbox_dir=inbox)

            result = handle_voice_command(
                command,
                speak=fake_speak,
                response_generator=lambda text: self.fail("work command should not call direct responder"),
                status_path=status_path,
                pending_path=pending_path,
                history_path=history_path,
                terminal_bridge=fake_terminal_bridge,
            )

        self.assertEqual(spoken, [])
        self.assertEqual(result["speech"]["transport"], "disabled")
        self.assertTrue(result["pending_for_adam"]["pending"])
        self.assertEqual(result["pending_for_adam"]["reason"], "terminal_delivery_pending_reply")

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

    def test_build_spoken_result_routes_outbound_message_to_terminal_bridge(self) -> None:
        calls = []

        def fake_terminal_bridge(command):
            calls.append(command.text)
            return {"ok": True, "status": "delivered", "verified": True}

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
                terminal_bridge=fake_terminal_bridge,
            )

        self.assertEqual(calls, ["Pošli SMS Janičce, jestli něco nepotřebuje."])
        self.assertIn("vložil do Codex terminálu", response)
        self.assertFalse(pending_path.exists())

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
            last_response = load_last_adam_response(path=inbox / "last_adam_response.json")

        self.assertIn("vložena do hlasového inboxu", response)
        self.assertIn("Čekám na Adamovu odpověď", response)
        self.assertNotIn("předána do Codex terminálu", response)
        self.assertTrue(pending["pending"])
        self.assertEqual(pending["reason"], "terminal_delivery_pending_reply")
        self.assertEqual(history[0]["route"], "terminal_delivery_pending_reply")
        self.assertFalse(last_response["available"])

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
                risk="Read-only systémová kontrola běžících procesů.",
                next_step="Na iPhonu otevři Codex a rozhodni systémové potvrzení.",
                confirmation_text="Potvrzuji bezpečnou kontrolu procesu.",
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
        self.assertIn("Read-only", loaded["risk"])
        self.assertEqual(loaded["confirmation_text"], "Potvrzuji bezpečnou kontrolu procesu.")
        self.assertTrue(status["codex_approval"]["active"])
        self.assertEqual(status["codex_approval"]["confirmation_text"], "Potvrzuji bezpečnou kontrolu procesu.")
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
            history_lock_exists = lock_path_for(history_path).exists()

        self.assertTrue(last_response["available"])
        self.assertEqual(last_response["route"], "codex_manual")
        self.assertIn("testovací sadu", last_response["adam_response"])
        self.assertEqual(status["last_adam_response"]["adam_response"], last_response["adam_response"])
        self.assertTrue(history_lock_exists)

    def test_two_processes_append_complete_voice_history_and_non_final_never_replaces_response(self) -> None:
        script = """
import sys
import time
from pathlib import Path
from app.speech.adam_voice_mode import append_manual_voice_history_turn

history_path = Path(sys.argv[1])
response_path = Path(sys.argv[2])
start_path = Path(sys.argv[3])
worker = sys.argv[4]
route = sys.argv[5]
while not start_path.exists():
    time.sleep(0.01)
for index in range(30):
    append_manual_voice_history_turn(
        user_text=f"{worker}-{index}",
        adam_response=f"Odpověď {worker}-{index}",
        route=route,
        path=history_path,
        response_path=response_path,
    )
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            history_path = root / "adam_voice_history.jsonl"
            response_path = root / "last_adam_response.json"
            start_path = root / "start"
            workers = (
                ("final", "codex_manual"),
                ("transport", "terminal_delivery_pending_reply"),
            )
            processes = [
                subprocess.Popen(
                    [
                        sys.executable,
                        "-c",
                        script,
                        str(history_path),
                        str(response_path),
                        str(start_path),
                        worker,
                        route,
                    ],
                    cwd=PROJECT_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for worker, route in workers
            ]
            start_path.write_text("start\n", encoding="utf-8")
            outputs = [process.communicate(timeout=20) for process in processes]

            for process, (_stdout, stderr) in zip(processes, outputs, strict=True):
                self.assertEqual(process.returncode, 0, stderr)
            records = [json.loads(line) for line in history_path.read_text(encoding="utf-8").splitlines()]
            last_response = load_last_adam_response(path=response_path)

        self.assertEqual(len(records), 60)
        self.assertEqual(
            {item["user_text"] for item in records},
            {f"{worker}-{index}" for worker, _route in workers for index in range(30)},
        )
        self.assertEqual(
            {item["route"] for item in records},
            {"codex_manual", "terminal_delivery_pending_reply"},
        )
        self.assertEqual(last_response["route"], "codex_manual")
        self.assertTrue(last_response["user_text"].startswith("final-"))

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

    def test_load_voice_mode_status_does_not_use_pending_transport_as_last_response(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            history_path = Path(temp_dir) / "adam_voice_history.jsonl"
            append_manual_voice_history_turn(
                user_text="TEST",
                adam_response="Zpráva byla vložena do hlasového inboxu. Čekám na Adamovu odpověď.",
                route="terminal_delivery_pending_reply",
                path=history_path,
            )

            status = load_voice_mode_status(
                status_path=Path(temp_dir) / "missing_status.json",
                pending_path=Path(temp_dir) / "missing_pending.json",
                history_path=history_path,
                last_response_path=Path(temp_dir) / "missing_last_response.json",
            )
            last_response = load_last_adam_response(path=Path(temp_dir) / "last_adam_response.json")

        self.assertFalse(last_response["available"])
        self.assertFalse(status["last_adam_response"]["available"])

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
                    sys.executable,
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
                    sys.executable,
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

    def test_adam_voice_pending_cli_hides_processed_stale_error_text(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            pending_path = Path(temp_dir) / "pending_for_adam.json"
            history_path = Path(temp_dir) / "adam_voice_history.jsonl"
            pending_path.write_text(
                json.dumps(
                    {
                        "ok": True,
                        "pending": False,
                        "status": "processed_by_codex",
                        "reason": "manual_required",
                        "message": "Triage hlasového pokynu vyžaduje ruční potvrzení.",
                        "text": "Starý už vyřízený hlasový pokyn.",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
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

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("pending: false", completed.stdout)
        self.assertIn("reason: -", completed.stdout)
        self.assertIn("Žádný hlasový pokyn nečeká na Adama.", completed.stdout)
        self.assertNotIn("Triage hlasového pokynu", completed.stdout)
        self.assertNotIn("Starý už vyřízený", completed.stdout)
        self.assertNotIn("KONTEXT", completed.stdout)

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
        self.assertEqual(
            history[0]["adam_response"],
            "Automatická odpověď watcheru, ne převzetí v Codex chatu: Ahoj, rád tě poznávám.",
        )
        self.assertIn("Míla: Co jí řekneš?", format_voice_history_for_prompt(history))

    def test_format_automatic_watcher_response_marks_non_codex_chat(self) -> None:
        self.assertEqual(
            format_automatic_watcher_response("OK"),
            "Automatická odpověď watcheru, ne převzetí v Codex chatu: OK",
        )

    def test_direct_response_failure_records_safe_error_detail(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            pending_path = inbox / "pending_for_adam.json"
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(inbox / "latest_voice_command.md", "Ahoj, jsi tam?")
            command = load_latest_voice_command(inbox_dir=inbox)

            def failing_response(_text: str) -> str:
                raise RuntimeError("temporary provider failure")

            response = build_spoken_result_for_command(
                command,
                response_generator=failing_response,
                pending_path=pending_path,
                history_path=history_path,
            )
            pending = json.loads(pending_path.read_text(encoding="utf-8"))

        self.assertIn("automatická odpověď se nepovedla", response)
        self.assertEqual(pending["reason"], "direct_response_failed")
        self.assertIn("Technický detail: RuntimeError: temporary provider failure", pending["message"])

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
                    sys.executable,
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

    def test_adam_voice_reply_cli_marks_processing_started_without_final_response(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            pending_path = inbox / "pending_for_adam.json"
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(inbox / "latest_voice_command.md", "Zkontroluj stav hlasového režimu.")
            command = load_latest_voice_command(inbox_dir=inbox)
            build_spoken_result_for_command(command, pending_path=pending_path, history_path=history_path)

            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/adam_voice_reply.py",
                    "--processing-started",
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
            pending = json.loads(pending_path.read_text(encoding="utf-8"))
            last_response = load_last_adam_response(path=inbox / "last_adam_response.json")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("processing_by_codex", completed.stdout)
        self.assertTrue(pending["pending"])
        self.assertEqual(pending["status"], "processing_by_codex")
        self.assertEqual(pending["message"], "Zpráva vložena do chatu a zahájeno zpracování.")
        self.assertFalse(last_response["available"])

    def test_adam_voice_reply_cli_can_record_latest_terminal_command_without_pending(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(inbox / "latest_voice_command.md", "Zkontroluj iPhone Cockpit.")

            completed = subprocess.run(
                [
                    sys.executable,
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

    def test_adam_voice_reply_cli_latest_command_closes_matching_pending(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            pending_path = inbox / "pending_for_adam.json"
            history_path = inbox / "adam_voice_history.jsonl"
            write_voice_command(inbox / "latest_voice_command.md", "Zkontroluj stav hlasového režimu.")
            command = load_latest_voice_command(inbox_dir=inbox)
            build_spoken_result_for_command(command, pending_path=pending_path, history_path=history_path)

            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/adam_voice_reply.py",
                    "--latest-command",
                    "--path",
                    str(pending_path),
                    "--inbox-dir",
                    str(inbox),
                    "--history-path",
                    str(history_path),
                    "Hotovo, mezistavy jsou textové.",
                ],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
            pending = json.loads(pending_path.read_text(encoding="utf-8"))
            history = load_voice_history(path=history_path, limit=3)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertFalse(pending["pending"])
        self.assertEqual(pending["status"], "processed_by_codex")
        self.assertEqual(history[-1]["route"], "codex_manual")
        self.assertIn("mezistavy jsou textové", history[-1]["adam_response"])

    def test_adam_voice_reply_cli_can_record_explicit_janicka_text_reply(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir)
            history_path = inbox / "adam_voice_history.jsonl"

            completed = subprocess.run(
                [
                    sys.executable,
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
