from __future__ import annotations

import shutil
import http.client
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from types import ModuleType
from types import SimpleNamespace
from http.server import ThreadingHTTPServer
from unittest.mock import patch

try:
    import dotenv  # noqa: F401
except ImportError:  # pragma: no cover - isolated workspace dependency fallback.
    dotenv_stub = ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda *_args, **_kwargs: False  # type: ignore[attr-defined]
    sys.modules["dotenv"] = dotenv_stub

try:
    import agents  # noqa: F401
except ImportError:  # pragma: no cover - isolated workspace dependency fallback.
    agents_stub = ModuleType("agents")

    def function_tool_stub(function=None, *_args, **_kwargs):
        if callable(function):
            return function
        return lambda decorated: decorated

    class RunnerStub:
        @staticmethod
        def run_sync(*_args, **_kwargs):
            raise RuntimeError("Agents SDK není v izolovaném testu dostupné.")

    agents_stub.function_tool = function_tool_stub  # type: ignore[attr-defined]
    agents_stub.Agent = object  # type: ignore[attr-defined]
    agents_stub.Runner = RunnerStub  # type: ignore[attr-defined]
    sys.modules["agents"] = agents_stub

from app.cockpit import (
    COCKPIT_HTML,
    COCKPIT_POST_ACTIONS,
    CockpitServer,
    family_calendar_delivery_status_action,
    family_calendar_notification_preview_action,
    family_calendar_prefill_action,
    family_calendar_save_action,
    family_calendar_status_action,
)


class FamilyCalendarCockpitTests(unittest.TestCase):
    @staticmethod
    def readiness(**changes):
        return SimpleNamespace(**{
            "status": "active", "config_mode": "enabled", "automation_active": True,
            "ready_to_enable": True, "writes_performed": False, "secret_read": False,
            "transport_called": False, "recipients": ["private@example.invalid"],
            "credential": "private-secret", **changes,
        })

    def test_delivery_summary_distinguishes_configured_modes_and_failed_checks(self) -> None:
        cases = [
            ({}, "active", "zapnuté"),
            ({"config_mode": "disabled", "automation_active": False, "ready_to_enable": False}, "disabled", "vypnuté"),
            ({"config_mode": "dry_run", "automation_active": False}, "dry_run", "náhledovém"),
            ({"config_mode": "dry_run", "ready_to_enable": False}, "attention", "překážku"),
            ({"ready_to_enable": False}, "attention", "překážku"),
            ({"status": "not_ready"}, "attention", "překážku"),
            ({"config_mode": "unknown"}, "unavailable", "nepodařilo ověřit"),
            ({"secret_read": True}, "unavailable", "nepodařilo ověřit"),
            ({"transport_called": True}, "unavailable", "nepodařilo ověřit"),
            ({"writes_performed": True}, "unavailable", "nepodařilo ověřit"),
        ]
        for changes, state, message in cases:
            with self.subTest(changes=changes):
                result = family_calendar_delivery_status_action(
                    readiness_loader=lambda: self.readiness(**changes),
                    now=datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc),
                )
                self.assertEqual(result["state"], state)
                self.assertEqual(result["ok"], state != "unavailable")
                self.assertIn(message, result["message"])
                self.assertTrue(result["read_only"])
                self.assertEqual(result["checked_at"], "2026-10-17T12:00:00+00:00")
                self.assertNotIn("private", json.dumps(result))

    def test_failed_delivery_probe_does_not_expose_private_error_or_claim_disabled(self) -> None:
        def unavailable():
            raise OSError("private-secret /private/config.json private@example.invalid")
        result = family_calendar_delivery_status_action(readiness_loader=unavailable)
        self.assertFalse(result["ok"])
        self.assertEqual(result["state"], "unavailable")
        self.assertNotIn("private", json.dumps(result))
        self.assertNotIn("vypnuté", result["message"])

    def test_delivery_status_get_uses_only_the_readonly_probe(self) -> None:
        with patch("app.cockpit.inspect_family_calendar_delivery_readiness", return_value=self.readiness()) as probe:
            server = ThreadingHTTPServer(("127.0.0.1", 0), CockpitServer().make_handler())
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                conn.request("GET", "/api/family-calendar/delivery-status")
                response = conn.getresponse()
                data = json.loads(response.read())
                conn.close()
                self.assertEqual(response.status, 200)
                self.assertEqual(data["state"], "active")
                self.assertNotIn("private", json.dumps(data))
                probe.assert_called_once_with()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_status_and_save_actions_use_private_registry(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "family" / "people.json"

            empty = family_calendar_status_action(path=path, today=date(2026, 7, 18))
            saved = family_calendar_save_action(
                {
                    "display_name": "Alena",
                    "relation": "teta",
                    "birth_date": "1980-12-19",
                    "name_day": "08-13",
                    "reminders_enabled": True,
                    "active": True,
                },
                path=path,
                today=date(2026, 7, 18),
                now=datetime(2026, 7, 18, 8, 0, tzinfo=timezone.utc),
            )
            updated = family_calendar_save_action(
                {
                    "person_id": saved["person"]["id"],
                    "display_name": "Alena",
                    "relation": "sestřenice",
                    "birth_date": "1980-12-19",
                    "name_day": "08-13",
                    "reminders_enabled": False,
                    "active": True,
                },
                path=path,
                today=date(2026, 7, 18),
                now=datetime(2026, 7, 18, 9, 0, tzinfo=timezone.utc),
            )

        self.assertTrue(empty["ok"])
        self.assertEqual(empty["counts"]["people"], 0)
        self.assertTrue(saved["ok"])
        self.assertEqual(saved["status"]["counts"]["people"], 1)
        self.assertTrue(updated["ok"])
        self.assertEqual(updated["person"]["relation"], "sestřenice")
        self.assertFalse(updated["person"]["reminders_enabled"])

    def test_prefill_action_seeds_only_an_empty_registry(self) -> None:
        records = (
            {
                "id": "person-seedaaaa0001",
                "display_name": "Alena",
                "relation": "teta",
                "name_day": "08-13",
            },
        )
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "family" / "people.json"

            first = family_calendar_prefill_action(
                path=path,
                records=records,
                today=date(2026, 7, 19),
                now=datetime(2026, 7, 19, 8, 0, tzinfo=timezone.utc),
            )
            second = family_calendar_prefill_action(
                path=path,
                records=records,
                today=date(2026, 7, 19),
                now=datetime(2026, 7, 19, 9, 0, tzinfo=timezone.utc),
            )

        self.assertTrue(first["ok"])
        self.assertTrue(first["applied"])
        self.assertEqual(first["status"]["counts"]["people"], 1)
        self.assertTrue(second["ok"])
        self.assertFalse(second["applied"])
        self.assertEqual(second["status"]["counts"]["people"], 1)

    def test_save_action_returns_validation_error_without_writing(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "family" / "people.json"

            result = family_calendar_save_action(
                {
                    "display_name": "Alena",
                    "birth_date": "",
                    "name_day": "",
                },
                path=path,
                today=date(2026, 7, 18),
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "invalid_family_person")
        self.assertIn("datum narození nebo datum svátku", result["message"])
        self.assertFalse(path.exists())

    def test_notification_preview_action_is_read_only_and_server_derived(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "family" / "people.json"
            family_calendar_save_action(
                {
                    "display_name": "Alena",
                    "relation": "teta",
                    "birth_date": "1980-12-19",
                    "name_day": "",
                    "reminders_enabled": True,
                    "active": True,
                },
                path=path,
                today=date(2026, 12, 17),
                now=datetime(2026, 12, 17, 8, 0, tzinfo=timezone.utc),
            )
            stored_before = path.read_bytes()

            result = family_calendar_notification_preview_action(
                {
                    "recipients": ["first@example.invalid", "second@example.invalid"],
                    "event": {"display_name": "Podvržená osoba", "days_until": 1},
                },
                path=path,
                today=date(2026, 12, 17),
            )
            stored_after = path.read_bytes()

        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["previews"][0]["display_name"], "Alena")
        self.assertEqual(result["previews"][0]["notification_offset"], "D-2")
        self.assertIn("Nic nebylo odesláno ani uloženo", result["message"])
        self.assertEqual(stored_after, stored_before)

    def test_notification_preview_action_validates_recipients_even_without_due_event(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "missing" / "people.json"

            invalid = family_calendar_notification_preview_action(
                {"recipients": ["not-an-email", "second@example.invalid"]},
                path=path,
                today=date(2026, 12, 17),
            )
            empty = family_calendar_notification_preview_action(
                {"recipients": ["first@example.invalid", "second@example.invalid"]},
                path=path,
                today=date(2026, 12, 17),
            )
            path_exists_after = path.exists()

        self.assertFalse(invalid["ok"])
        self.assertEqual(invalid["error"], "invalid_notification_preview")
        self.assertIn("platná samostatná e-mailová adresa", invalid["message"])
        self.assertTrue(empty["ok"])
        self.assertEqual(empty["count"], 0)
        self.assertFalse(path_exists_after)

    def test_family_calendar_ui_and_route_contract_are_present(self) -> None:
        route = next(
            item for item in COCKPIT_POST_ACTIONS if item["path"] == "/api/family-calendar/save"
        )

        self.assertEqual(route["risk"], "private_write")
        self.assertEqual(route["handler_name"], "family_calendar_save_action")
        prefill_route = next(
            item
            for item in COCKPIT_POST_ACTIONS
            if item["path"] == "/api/family-calendar/prefill"
        )
        self.assertEqual(prefill_route["risk"], "private_write")
        self.assertEqual(prefill_route["handler_name"], "family_calendar_prefill_action")
        preview_route = next(
            item
            for item in COCKPIT_POST_ACTIONS
            if item["path"] == "/api/family-calendar/notification-preview"
        )
        self.assertEqual(preview_route["risk"], "read_only_via_post")
        self.assertEqual(preview_route["confirmation"], "none_readonly_no_persistence")
        self.assertEqual(
            preview_route["handler_name"],
            "family_calendar_notification_preview_action",
        )
        self.assertIn('id="familyCalendarBtn">Rodinný kalendář</button>', COCKPIT_HTML)
        self.assertIn('id="familyCalendarModal"', COCKPIT_HTML)
        self.assertIn('id="familyCalendarForm"', COCKPIT_HTML)
        self.assertIn('id="familyCalendarTableBody"', COCKPIT_HTML)
        self.assertIn("Datum narození", COCKPIT_HTML)
        self.assertIn("Datum svátku", COCKPIT_HTML)
        self.assertNotIn("e-mailové odesílání zatím není aktivní", COCKPIT_HTML)
        self.assertIn('id="familyCalendarDeliveryStatus"', COCKPIT_HTML)
        self.assertIn('fetchJsonWithTimeout("/api/family-calendar/delivery-status", 15000)', COCKPIT_HTML)
        self.assertIn('id="familyCalendarPreviewForm"', COCKPIT_HTML)
        self.assertIn('id="familyCalendarRecipientOne" type="email"', COCKPIT_HTML)
        self.assertIn('id="familyCalendarRecipientTwo" type="email"', COCKPIT_HTML)
        self.assertIn("Nic se neodesílá ani neukládá", COCKPIT_HTML)
        self.assertIn('fetchJson("/api/family-calendar/status")', COCKPIT_HTML)
        self.assertIn('postJson("/api/family-calendar/prefill", {})', COCKPIT_HTML)
        self.assertIn('postJson("/api/family-calendar/save"', COCKPIT_HTML)
        self.assertIn(
            'postJson("/api/family-calendar/notification-preview"',
            COCKPIT_HTML,
        )
        self.assertIn("function renderFamilyCalendarPreviews(previews)", COCKPIT_HTML)
        self.assertIn(
            'subject.textContent = String(preview.subject || "Náhled upozornění")',
            COCKPIT_HTML,
        )
        self.assertIn('body.textContent = String(preview.body || "")', COCKPIT_HTML)
        self.assertIn("function editFamilyCalendarPerson(personId)", COCKPIT_HTML)
        self.assertIn("familyCalendarEditorDirty", COCKPIT_HTML)
        self.assertIn(".family-calendar-form-grid { grid-template-columns: 1fr; }", COCKPIT_HTML)
        self.assertIn('class="family-calendar-person-actions"', COCKPIT_HTML)
        self.assertIn(">Upravit údaje</button>", COCKPIT_HTML)
        self.assertLess(
            COCKPIT_HTML.index('class="family-calendar-person-actions"'),
            COCKPIT_HTML.index("formatFamilyCalendarBirthDate(person.birth_date)"),
        )

    def test_cockpit_javascript_with_family_calendar_is_valid(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js není dostupný pro kontrolu JavaScriptu.")
        start = COCKPIT_HTML.rfind("<script>")
        end = COCKPIT_HTML.rfind("</script>")
        self.assertGreaterEqual(start, 0)
        self.assertGreater(end, start)
        completed = subprocess.run(
            [node, "--check", "-"],
            input=COCKPIT_HTML[start + len("<script>") : end],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
