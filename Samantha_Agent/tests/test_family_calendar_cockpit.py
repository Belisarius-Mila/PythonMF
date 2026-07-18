from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from types import ModuleType

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
    family_calendar_prefill_action,
    family_calendar_save_action,
    family_calendar_status_action,
)


class FamilyCalendarCockpitTests(unittest.TestCase):
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
        self.assertIn('id="familyCalendarBtn">Rodinný kalendář</button>', COCKPIT_HTML)
        self.assertIn('id="familyCalendarModal"', COCKPIT_HTML)
        self.assertIn('id="familyCalendarForm"', COCKPIT_HTML)
        self.assertIn('id="familyCalendarTableBody"', COCKPIT_HTML)
        self.assertIn("Datum narození", COCKPIT_HTML)
        self.assertIn("Datum svátku", COCKPIT_HTML)
        self.assertIn("e-mailové odesílání zatím není aktivní", COCKPIT_HTML)
        self.assertIn('fetchJson("/api/family-calendar/status")', COCKPIT_HTML)
        self.assertIn('postJson("/api/family-calendar/prefill", {})', COCKPIT_HTML)
        self.assertIn('postJson("/api/family-calendar/save"', COCKPIT_HTML)
        self.assertIn("function editFamilyCalendarPerson(personId)", COCKPIT_HTML)
        self.assertIn("familyCalendarEditorDirty", COCKPIT_HTML)
        self.assertIn(".family-calendar-form-grid { grid-template-columns: 1fr; }", COCKPIT_HTML)

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
