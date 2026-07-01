from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from app.adam_service import (
    adam_service_status,
    build_adam_text_prompt,
    deliver_prompt_to_adam_screen,
    deliver_prompt_to_visible_adam,
    discover_managed_adam_codex_ttys,
    load_adam_text_reply,
    record_adam_text_reply,
    save_adam_text_request,
    start_adam_service,
    stop_adam_service,
    submit_adam_text_request,
)


class AdamServiceTests(unittest.TestCase):
    def test_start_adam_service_uses_detached_screen_and_marks_tty(self) -> None:
        calls = []

        def fake_runner(args, **kwargs):
            calls.append({"args": args, "kwargs": kwargs})
            if args == ["screen", "-ls"]:
                return subprocess.CompletedProcess(args=args, returncode=1, stdout="No Sockets found.\n", stderr="")
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            entry = Path(temp_dir) / "entry.sh"
            entry.write_text("#!/bin/zsh\n", encoding="utf-8")

            result = start_adam_service(runner=fake_runner, entry_script=entry)

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "start_requested")
        start_call = next(call for call in calls if call["args"][:3] == ["screen", "-dmS", "samantha_adam"])
        self.assertEqual(start_call["kwargs"]["env"]["SAMANTHA_MARK_VOICE_TTY"], "0")
        self.assertEqual(start_call["kwargs"]["env"]["SAMANTHA_AUTOSAVE_RESUME_CHECK"], "0")
        self.assertEqual(start_call["kwargs"]["env"]["SAMANTHA_WORK_CONTEXT_GUARD"], "0")
        self.assertIn("spravovaná Adam/Codex relace", start_call["kwargs"]["env"]["SAMANTHA_START_REQUEST"])

    def test_start_adam_service_restarts_stale_screen_without_codex(self) -> None:
        calls = []
        screen_running = True

        def fake_runner(args, **kwargs):
            nonlocal screen_running
            calls.append(args)
            if args == ["screen", "-ls"]:
                stdout = "\t123.samantha_adam\t(Detached)\n" if screen_running else "No Sockets found.\n"
                return subprocess.CompletedProcess(args=args, returncode=0 if screen_running else 1, stdout=stdout, stderr="")
            if args == ["screen", "-S", "samantha_adam", "-X", "quit"]:
                screen_running = False
                return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            entry = Path(temp_dir) / "entry.sh"
            entry.write_text("#!/bin/zsh\n", encoding="utf-8")

            result = start_adam_service(
                runner=fake_runner,
                entry_script=entry,
                managed_codex_tty_discoverer=lambda: [],
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "start_requested")
        self.assertIn(["screen", "-S", "samantha_adam", "-X", "quit"], calls)

    def test_stop_adam_service_requires_confirmation(self) -> None:
        result = stop_adam_service(confirmed=False)

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "confirmation_required")

    def test_adam_service_status_reports_running_marker_and_counts(self) -> None:
        def fake_runner(args, **kwargs):
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="\t123.samantha_adam\t(Detached)\n", stderr="")

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            marker = Path(temp_dir) / "current_codex_tty.json"
            marker.write_text('{"tty": "ttys005"}', encoding="utf-8")
            requests = Path(temp_dir) / "requests"
            requests.mkdir()
            (requests / "one.json").write_text('{"status": "queued"}', encoding="utf-8")
            (requests / "two.json").write_text('{"status": "answered", "answer": "hotovo"}', encoding="utf-8")

            status = adam_service_status(
                screen_runner=fake_runner,
                codex_tty_discoverer=lambda: ["ttys005"],
                managed_codex_tty_discoverer=lambda: ["ttys005"],
                marker_path=marker,
                requests_dir=requests,
            )

        self.assertTrue(status["running"])
        self.assertEqual(status["state"], "running")
        self.assertEqual(status["marked_tty"], "ttys005")
        self.assertEqual(status["managed_codex_ttys"], ["ttys005"])
        self.assertEqual(status["pending_count"], 1)
        self.assertEqual(status["answered_count"], 1)

    def test_adam_service_status_warns_when_screen_has_no_codex(self) -> None:
        def fake_runner(args, **kwargs):
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="\t123.samantha_adam\t(Detached)\n", stderr="")

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            marker = Path(temp_dir) / "current_codex_tty.json"
            marker.write_text('{"tty": "ttys005"}', encoding="utf-8")

            status = adam_service_status(
                screen_runner=fake_runner,
                codex_tty_discoverer=lambda: ["ttys005"],
                managed_codex_tty_discoverer=lambda: [],
                marker_path=marker,
                requests_dir=Path(temp_dir) / "requests",
            )

        self.assertTrue(status["running"])
        self.assertEqual(status["state"], "running_without_codex")
        self.assertIn("Codex v ní neběží", status["message"])

    def test_deliver_prompt_to_adam_screen_clears_input_and_uses_managed_screen(self) -> None:
        calls = []
        sleeps = []

        def fake_runner(args, **kwargs):
            calls.append({"args": args, "kwargs": kwargs})
            if args == ["screen", "-ls"]:
                return subprocess.CompletedProcess(args=args, returncode=0, stdout="\t123.samantha_adam\t(Detached)\n", stderr="")
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        result = deliver_prompt_to_adam_screen(
            "První řádek\nDruhý řádek",
            runner=fake_runner,
            managed_codex_tty_discoverer=lambda: ["ttys001"],
            sleeper=sleeps.append,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["delivery_method"], "managed_screen")
        self.assertEqual(calls[1]["args"][:7], ["screen", "-S", "samantha_adam", "-p", "0", "-X", "stuff"])
        payload = calls[1]["args"][7]
        self.assertTrue(payload.startswith("\x15"))
        self.assertIn("První řádek Druhý řádek", payload)
        self.assertEqual(calls[2]["args"], ["screen", "-S", "samantha_adam", "-p", "0", "-X", "stuff", "\r"])
        self.assertEqual(sleeps, [0.2])

    def test_deliver_prompt_to_adam_screen_refuses_screen_without_codex(self) -> None:
        def fake_runner(args, **kwargs):
            if args == ["screen", "-ls"]:
                return subprocess.CompletedProcess(args=args, returncode=0, stdout="\t123.samantha_adam\t(Detached)\n", stderr="")
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        result = deliver_prompt_to_adam_screen(
            "Ahoj",
            runner=fake_runner,
            managed_codex_tty_discoverer=lambda: [],
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "managed_codex_not_running")

    def test_deliver_prompt_to_visible_adam_marks_vscode_target(self) -> None:
        calls = []

        def fake_deliverer(prompt, **kwargs):
            calls.append({"prompt": prompt, "kwargs": kwargs})
            return {"ok": True, "status": "delivered_vscode", "delivery_method": "local_gui_vscode"}

        result = deliver_prompt_to_visible_adam("Ahoj", submit=True, deliverer=fake_deliverer)

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "delivered_vscode")
        self.assertEqual(result["adam_delivery_target"], "visible_vscode")
        self.assertEqual(calls[0]["prompt"], "Ahoj")
        self.assertEqual(calls[0]["kwargs"], {"submit": True})

    def test_request_prompt_contains_request_id_and_reply_command(self) -> None:
        request = {
            "request_id": "janicka_test",
            "message": "Jak funguje hlasový chat?",
            "history": [{"role": "user", "content": "Ahoj"}],
        }

        prompt = build_adam_text_prompt(request)

        self.assertIn("Request ID: janicka_test", prompt)
        self.assertIn("--request-id janicka_test", prompt)
        self.assertIn("--route janicka_text_bridge", prompt)
        self.assertIn("Jak funguje hlasový chat?", prompt)
        self.assertIn("Jana má spuštěný jen Cockpit", prompt)

    def test_record_and_load_adam_text_reply_by_request_id(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            requests = Path(temp_dir) / "requests"
            save_adam_text_request(
                message="Kde najdu dokument?",
                request_id="req-doc",
                requests_dir=requests,
            )
            record_adam_text_reply(
                request_id="req-doc",
                response="Dokument najdeš přes tlačítko Najít dokument.",
                requests_dir=requests,
            )

            reply = load_adam_text_reply(request_id="req-doc", requests_dir=requests)

        self.assertTrue(reply["available"])
        self.assertEqual(reply["answer"], "Dokument najdeš přes tlačítko Najít dokument.")

    def test_submit_adam_text_request_starts_and_delivers_prompt(self) -> None:
        calls = []

        def fake_starter():
            calls.append({"starter": True})
            return {"ok": True, "status": "already_running"}

        def fake_deliverer(prompt, **kwargs):
            calls.append({"prompt": prompt, "kwargs": kwargs})
            return {"ok": True, "status": "delivered", "verified": True}

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            result = submit_adam_text_request(
                message="Ahoj Adame.",
                history=[],
                requests_dir=Path(temp_dir) / "requests",
                starter=fake_starter,
                deliverer=fake_deliverer,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "delivered_to_adam")
        self.assertIn("request_id", result)
        self.assertIn("Ahoj Adame.", calls[1]["prompt"])
        self.assertEqual(calls[1]["kwargs"], {"submit": True})

    def test_submit_adam_text_request_defaults_to_managed_screen(self) -> None:
        calls = []
        import app.adam_service as adam_service_module

        def fake_starter():
            calls.append({"starter": True})
            return {"ok": True, "status": "already_running"}

        def fake_screen_deliverer(prompt, **kwargs):
            calls.append({"prompt": prompt, "kwargs": kwargs})
            return {"ok": True, "status": "delivered", "verified": True, "delivery_method": "managed_screen"}

        original_deliver_prompt_to_adam_screen = adam_service_module.deliver_prompt_to_adam_screen
        try:
            adam_service_module.deliver_prompt_to_adam_screen = fake_screen_deliverer
            with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                result = submit_adam_text_request(
                    message="Ahoj Adame.",
                    history=[],
                    requests_dir=Path(temp_dir) / "requests",
                    starter=fake_starter,
                    deliverer=None,
                )
        finally:
            adam_service_module.deliver_prompt_to_adam_screen = original_deliver_prompt_to_adam_screen

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "delivered_to_adam")
        self.assertIn("Ahoj Adame.", calls[1]["prompt"])
        self.assertEqual(calls[1]["kwargs"], {"submit": True})

    def test_discover_managed_adam_codex_ttys_requires_codex_descendant_of_session(self) -> None:
        ps_output = "\n".join(
            [
                "100 1 ?? SCREEN -dmS samantha_adam /repo/scripts/samantha_screen_entry.sh",
                "101 100 ttys001 login -pflq user /repo/scripts/samantha_screen_entry.sh",
                "102 101 ttys001 /bin/zsh /repo/scripts/samantha_screen_entry.sh",
                "103 102 ttys001 node /usr/local/bin/codex -C /repo .",
                "200 1 ttys000 node /usr/local/bin/codex -C /repo .",
            ]
        )

        def fake_runner(args, **kwargs):
            return subprocess.CompletedProcess(args=args, returncode=0, stdout=ps_output, stderr="")

        self.assertEqual(discover_managed_adam_codex_ttys(runner=fake_runner), ["ttys001"])

    def test_submit_adam_text_request_waits_after_start_request(self) -> None:
        calls = []

        def fake_starter():
            calls.append("starter")
            return {"ok": True, "status": "start_requested"}

        def fake_ready():
            calls.append("ready")
            return {"ready": True, "running": True, "marked_tty": "ttys005"}

        def fake_deliverer(prompt, **kwargs):
            calls.append("deliver")
            return {"ok": True, "status": "delivered", "verified": True}

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            result = submit_adam_text_request(
                message="Ahoj Adame.",
                requests_dir=Path(temp_dir) / "requests",
                starter=fake_starter,
                ready_waiter=fake_ready,
                deliverer=fake_deliverer,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(calls, ["starter", "ready", "deliver"])
        self.assertTrue(result["ready"]["ready"])

    def test_submit_adam_text_request_warns_but_still_delivers_when_ready_is_unclear(self) -> None:
        calls = []

        def fake_starter():
            calls.append("starter")
            return {"ok": True, "status": "start_requested"}

        def fake_ready():
            calls.append("ready")
            return {"ready": False, "message": "Codex ještě neběží."}

        def fake_deliverer(prompt, **kwargs):
            calls.append("deliver")
            return {"ok": True}

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            result = submit_adam_text_request(
                message="Ahoj Adame.",
                requests_dir=Path(temp_dir) / "requests",
                starter=fake_starter,
                ready_waiter=fake_ready,
                deliverer=fake_deliverer,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "delivered_to_adam")
        self.assertEqual(calls, ["starter", "ready", "deliver"])
        self.assertIn("Pozor:", result["message"])
        self.assertIn("Codex ještě neběží.", result["message"])
        self.assertEqual(result["ready_warning"], "Codex ještě neběží.")


if __name__ == "__main__":
    unittest.main()
