from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from app.adam_service import (
    adam_service_status,
    build_adam_text_prompt,
    build_janicka_exec_prompt,
    codex_exec_environment,
    deliver_janicka_request_via_codex_exec,
    deliver_prompt_to_adam_screen,
    deliver_prompt_to_managed_codex_tty,
    deliver_prompt_to_visible_adam,
    discover_managed_adam_codex_ttys,
    janicka_light_status,
    load_adam_text_reply,
    record_adam_text_reply,
    save_adam_text_request,
    start_adam_service,
    start_janicka_light_session,
    stop_adam_service,
    stop_janicka_light_session,
    submit_adam_text_request,
    submit_janicka_text_request,
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

    def test_start_janicka_light_session_uses_separate_screen_and_light_prompt(self) -> None:
        calls = []

        def fake_runner(args, **kwargs):
            calls.append({"args": args, "kwargs": kwargs})
            if args == ["screen", "-ls"]:
                return subprocess.CompletedProcess(args=args, returncode=1, stdout="No Sockets found.\n", stderr="")
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            entry = Path(temp_dir) / "entry.sh"
            entry.write_text("#!/bin/zsh\n", encoding="utf-8")

            result = start_janicka_light_session(runner=fake_runner, entry_script=entry)

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "start_requested")
        start_call = next(call for call in calls if call["args"][:3] == ["screen", "-dmS", "samantha_janicka"])
        env = start_call["kwargs"]["env"]
        self.assertEqual(env["SAMANTHA_JANICKA_LIGHT"], "1")
        self.assertEqual(env["SAMANTHA_MARK_VOICE_TTY"], "0")
        self.assertEqual(env["SAMANTHA_AUTOSAVE_RESUME_CHECK"], "0")
        self.assertEqual(env["SAMANTHA_WORK_CONTEXT_GUARD"], "0")
        self.assertIn("lehká Samantha/Adam relace", env["SAMANTHA_START_REQUEST"])
        self.assertIn("memory/projects/janicka_cockpit_kucharka.md", env["SAMANTHA_START_REQUEST"])

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

    def test_janicka_light_status_uses_separate_session_label(self) -> None:
        def fake_runner(args, **kwargs):
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="\t123.samantha_janicka\t(Detached)\n", stderr="")

        status = janicka_light_status(
            screen_runner=fake_runner,
            codex_tty_discoverer=lambda: ["ttys010"],
        )

        self.assertTrue(status["running"])
        self.assertIn("Janička light Samantha", status["message"])
        self.assertEqual(status["session_name"], "samantha_janicka")

    def test_stop_janicka_light_session_requires_confirmation(self) -> None:
        result = stop_janicka_light_session(confirmed=False)

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "confirmation_required")
        self.assertIn("Janička light Samantha", result["message"])

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

    def test_deliver_prompt_to_adam_screen_verifies_request_id_in_hardcopy(self) -> None:
        def fake_runner(args, **kwargs):
            if args == ["screen", "-ls"]:
                return subprocess.CompletedProcess(args=args, returncode=0, stdout="\t123.samantha_adam\t(Detached)\n", stderr="")
            if args[:7] == ["screen", "-S", "samantha_adam", "-p", "0", "-X", "hardcopy"]:
                Path(args[-1]).write_text("Textový dotaz. Request ID: janicka_test_1", encoding="utf-8")
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        result = deliver_prompt_to_adam_screen(
            "Textový dotaz. Request ID: janicka_test_1",
            runner=fake_runner,
            managed_codex_tty_discoverer=lambda: ["ttys001"],
            sleeper=lambda _seconds: None,
        )

        self.assertTrue(result["ok"])
        self.assertTrue(result["verified"])
        self.assertEqual(result["verification"]["status"], "verified")

    def test_deliver_prompt_to_adam_screen_rejects_unverified_request_id(self) -> None:
        def fake_runner(args, **kwargs):
            if args == ["screen", "-ls"]:
                return subprocess.CompletedProcess(args=args, returncode=0, stdout="\t123.samantha_adam\t(Detached)\n", stderr="")
            if args[:7] == ["screen", "-S", "samantha_adam", "-p", "0", "-X", "hardcopy"]:
                Path(args[-1]).write_text("Adamova relace bez nového requestu.", encoding="utf-8")
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        result = deliver_prompt_to_adam_screen(
            "Textový dotaz. Request ID: janicka_test_missing",
            runner=fake_runner,
            managed_codex_tty_discoverer=lambda: ["ttys001"],
            sleeper=lambda _seconds: None,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "screen_delivery_unverified")
        self.assertFalse(result["verified"])

    def test_deliver_prompt_to_managed_codex_tty_verifies_request_id(self) -> None:
        calls = []

        def fake_runner(args, **kwargs):
            if args[:7] == ["screen", "-S", "samantha_janicka", "-p", "0", "-X", "hardcopy"]:
                Path(args[-1]).write_text("Textový dotaz. Request ID: janicka_tty_1", encoding="utf-8")
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        def fake_tty_deliverer(tty, prompt, **kwargs):
            calls.append({"tty": tty, "prompt": prompt, "kwargs": kwargs})
            return {"ok": True, "status": "delivered_tty", "target_tty": tty, "verified": False}

        result = deliver_prompt_to_managed_codex_tty(
            "Textový dotaz. Request ID: janicka_tty_1",
            session_name="samantha_janicka",
            runner=fake_runner,
            managed_codex_tty_discoverer=lambda: ["ttys004"],
            tty_deliverer=fake_tty_deliverer,
            sleeper=lambda _seconds: None,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "delivered_managed_tty")
        self.assertEqual(result["target_tty"], "ttys004")
        self.assertTrue(result["verified"])
        self.assertEqual(calls[0]["kwargs"], {"submit": True})

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

    def test_submit_janicka_text_request_uses_light_screen_session(self) -> None:
        calls = []
        import app.adam_service as adam_service_module

        def fake_starter():
            calls.append({"starter": True})
            return {"ok": True, "status": "start_requested"}

        def fake_ready():
            calls.append({"ready": True})
            return {"ready": True, "running": True, "managed_codex_ttys": ["ttys004"]}

        def fake_screen_deliverer(prompt, **kwargs):
            calls.append({"prompt": prompt, "kwargs": kwargs})
            return {"ok": True, "status": "delivered_screen", "verified": True, "delivery_method": "managed_screen"}

        original_deliver_prompt_to_adam_screen = adam_service_module.deliver_prompt_to_adam_screen
        try:
            adam_service_module.deliver_prompt_to_adam_screen = fake_screen_deliverer
            with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                result = submit_janicka_text_request(
                    message="Ahoj Janičko.",
                    history=[],
                    requests_dir=Path(temp_dir) / "requests",
                    starter=fake_starter,
                    ready_waiter=fake_ready,
                )
        finally:
            adam_service_module.deliver_prompt_to_adam_screen = original_deliver_prompt_to_adam_screen

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "delivered_to_adam")
        self.assertEqual(result["service_target"], "janicka_light")
        self.assertEqual(calls[0], {"starter": True})
        self.assertEqual(calls[1], {"ready": True})
        self.assertIn("Ahoj Janičko.", calls[2]["prompt"])
        self.assertEqual(calls[2]["kwargs"]["submit"], True)
        self.assertEqual(calls[2]["kwargs"]["session_name"], "samantha_janicka")

    def test_submit_janicka_text_request_falls_back_to_light_tty_when_screen_is_unverified(self) -> None:
        calls = []
        import app.adam_service as adam_service_module

        def fake_starter():
            calls.append({"starter": True})
            return {"ok": True, "status": "already_running"}

        def fake_screen_deliverer(prompt, **kwargs):
            calls.append({"screen": kwargs})
            return {"ok": False, "status": "screen_delivery_unverified", "verified": False}

        def fake_tty_deliverer(prompt, **kwargs):
            calls.append({"tty": kwargs})
            return {"ok": True, "status": "delivered_managed_tty", "verified": True}

        original_screen_deliverer = adam_service_module.deliver_prompt_to_adam_screen
        original_tty_deliverer = adam_service_module.deliver_prompt_to_managed_codex_tty
        try:
            adam_service_module.deliver_prompt_to_adam_screen = fake_screen_deliverer
            adam_service_module.deliver_prompt_to_managed_codex_tty = fake_tty_deliverer
            with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                result = submit_janicka_text_request(
                    message="Druhý dotaz.",
                    history=[],
                    requests_dir=Path(temp_dir) / "requests",
                    starter=fake_starter,
                )
        finally:
            adam_service_module.deliver_prompt_to_adam_screen = original_screen_deliverer
            adam_service_module.deliver_prompt_to_managed_codex_tty = original_tty_deliverer

        self.assertTrue(result["ok"])
        self.assertEqual(result["service_target"], "janicka_light")
        self.assertEqual(calls[0], {"starter": True})
        self.assertEqual(calls[1]["screen"]["session_name"], "samantha_janicka")
        self.assertEqual(calls[2]["tty"]["session_name"], "samantha_janicka")
        self.assertEqual(result["delivery"]["screen_delivery"]["status"], "screen_delivery_unverified")

    def test_deliver_janicka_request_via_codex_exec_records_reply(self) -> None:
        calls = []

        def fake_runner(args, **kwargs):
            calls.append({"args": args, "kwargs": kwargs})
            output_path = Path(args[args.index("--output-last-message") + 1])
            output_path.write_text("Odpověď z read-only workeru.", encoding="utf-8")
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            requests = Path(temp_dir) / "requests"
            request = save_adam_text_request(
                message="Ahoj.",
                history=[],
                request_id="janicka_exec_1",
                requests_dir=requests,
            )
            prompt = build_adam_text_prompt(request)
            result = deliver_janicka_request_via_codex_exec(
                prompt,
                requests_dir=requests,
                output_dir=Path(temp_dir) / "outputs",
                runner=fake_runner,
                codex_bin="/usr/local/bin/codex",
            )
            reply = load_adam_text_reply(request_id="janicka_exec_1", requests_dir=requests)

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "delivered_codex_exec")
        self.assertEqual(reply["answer"], "Odpověď z read-only workeru.")
        self.assertEqual(calls[0]["args"][:5], ["/usr/local/bin/codex", "exec", "-C", str(Path(__file__).resolve().parents[1]), "-s"])
        self.assertIn("read-only", calls[0]["args"])
        self.assertIn("Jsi light Samantha/Adam worker", calls[0]["kwargs"]["input"])
        self.assertIn("/usr/local/bin", calls[0]["kwargs"]["env"]["PATH"].split(":"))

    def test_codex_exec_environment_adds_node_paths_for_server_process(self) -> None:
        env = codex_exec_environment({"PATH": "/custom/bin", "LANG": "C"})
        path_parts = env["PATH"].split(":")

        self.assertLess(path_parts.index("/usr/local/bin"), path_parts.index("/custom/bin"))
        self.assertIn("/opt/homebrew/bin", path_parts)
        self.assertEqual(path_parts.count("/usr/local/bin"), 1)
        self.assertEqual(env["LANG"], "C")
        self.assertEqual(env["PYTHONUTF8"], "1")

    def test_build_janicka_exec_prompt_is_read_only_and_keeps_history(self) -> None:
        prompt = build_janicka_exec_prompt(
            {
                "request_id": "janicka_exec_2",
                "message": "A teď?",
                "history": [
                    {"role": "user", "content": "Ahoj"},
                    {"role": "assistant", "content": "Jsem tady."},
                ],
            }
        )

        self.assertIn("Request ID: janicka_exec_2", prompt)
        self.assertIn("Pracuj read-only", prompt)
        self.assertIn("Jana/Míla: Ahoj", prompt)
        self.assertIn("Adam: Jsem tady.", prompt)
        self.assertIn("Aktuální dotaz:\nA teď?", prompt)

    def test_submit_janicka_text_request_falls_back_to_codex_exec_when_tty_is_denied(self) -> None:
        calls = []
        import app.adam_service as adam_service_module

        def fake_starter():
            calls.append({"starter": True})
            return {"ok": True, "status": "already_running"}

        def fake_screen_deliverer(prompt, **kwargs):
            calls.append({"screen": kwargs})
            return {"ok": False, "status": "screen_delivery_unverified", "verified": False}

        def fake_tty_deliverer(prompt, **kwargs):
            calls.append({"tty": kwargs})
            return {"ok": False, "status": "tty_delivery_failed", "message": "[Errno 1] Operation not permitted"}

        def fake_exec_deliverer(prompt, **kwargs):
            calls.append({"exec": kwargs})
            return {"ok": True, "status": "delivered_codex_exec", "verified": True, "delivery_method": "codex_exec"}

        original_screen_deliverer = adam_service_module.deliver_prompt_to_adam_screen
        original_tty_deliverer = adam_service_module.deliver_prompt_to_managed_codex_tty
        original_exec_deliverer = adam_service_module.deliver_janicka_request_via_codex_exec
        try:
            adam_service_module.deliver_prompt_to_adam_screen = fake_screen_deliverer
            adam_service_module.deliver_prompt_to_managed_codex_tty = fake_tty_deliverer
            adam_service_module.deliver_janicka_request_via_codex_exec = fake_exec_deliverer
            with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                result = submit_janicka_text_request(
                    message="Druhý dotaz.",
                    history=[],
                    requests_dir=Path(temp_dir) / "requests",
                    starter=fake_starter,
                )
        finally:
            adam_service_module.deliver_prompt_to_adam_screen = original_screen_deliverer
            adam_service_module.deliver_prompt_to_managed_codex_tty = original_tty_deliverer
            adam_service_module.deliver_janicka_request_via_codex_exec = original_exec_deliverer

        self.assertTrue(result["ok"])
        self.assertEqual(result["delivery"]["status"], "delivered_codex_exec")
        self.assertEqual(result["delivery"]["screen_delivery"]["status"], "screen_delivery_unverified")
        self.assertEqual(result["delivery"]["tty_delivery"]["status"], "tty_delivery_failed")
        self.assertEqual(calls[3]["exec"]["requests_dir"], Path(temp_dir) / "requests")

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

    def test_submit_adam_text_request_retries_unverified_screen_delivery(self) -> None:
        calls = []

        def fake_starter():
            calls.append("starter")
            return {"ok": True, "status": "already_running"}

        def fake_deliverer(prompt, **kwargs):
            calls.append("deliver")
            if calls.count("deliver") == 1:
                return {"ok": False, "status": "screen_delivery_unverified", "verified": False}
            return {"ok": True, "status": "delivered_screen", "verified": True}

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            result = submit_adam_text_request(
                message="Ahoj Adame.",
                requests_dir=Path(temp_dir) / "requests",
                starter=fake_starter,
                deliverer=fake_deliverer,
                sleeper=lambda seconds: calls.append(("sleep", seconds)),
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "delivered_to_adam")
        self.assertEqual(calls, ["starter", "deliver", ("sleep", 1.0), "deliver"])
        self.assertTrue(result["retry"]["delivery_attempts"][0]["delivery"]["verified"])

    def test_submit_adam_text_request_does_not_restart_after_repeated_unverified_screen_delivery(self) -> None:
        calls = []

        def fake_starter():
            calls.append("starter")
            return {"ok": True, "status": "already_running"}

        def fake_deliverer(prompt, **kwargs):
            calls.append("deliver")
            return {"ok": False, "status": "screen_delivery_unverified", "verified": False}

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            result = submit_adam_text_request(
                message="Ahoj Adame.",
                requests_dir=Path(temp_dir) / "requests",
                starter=fake_starter,
                deliverer=fake_deliverer,
                sleeper=lambda seconds: calls.append(("sleep", seconds)),
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "delivery_failed")
        self.assertEqual(
            calls,
            [
                "starter",
                "deliver",
                ("sleep", 1.0),
                "deliver",
                ("sleep", 2.0),
                "deliver",
            ],
        )
        self.assertNotIn("restart", result["retry"])
        self.assertEqual(len(result["retry"]["delivery_attempts"]), 2)


if __name__ == "__main__":
    unittest.main()
