from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app import samantha_agent
from app.email.activity_state import (
    EmailActivityState,
    format_email_activity_reminder,
    load_email_activity_state,
    record_email_archive_completed,
    record_email_triage_completed,
    save_email_activity_state,
)


class EmailActivityStateTests(unittest.TestCase):
    def test_missing_state_prompts_for_triage_and_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "activity_state.json"

            formatted = format_email_activity_reminder(path=path, today="2026-05-19")

            self.assertIn("Neni zaznam o posledni e-mailove triage", formatted)
            self.assertIn("Neni zaznam o posledni zaloze", formatted)

    def test_recent_state_has_no_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "activity_state.json"
            save_email_activity_state(
                EmailActivityState(
                    last_triage_at="2026-05-19",
                    last_archive_at="2026-05-19",
                ),
                path=path,
            )

            formatted = format_email_activity_reminder(path=path, today="2026-05-19")

            self.assertIn("7dennim intervalu", formatted)
            self.assertNotIn("Chces spustit Email Triage", formatted)

    def test_old_dates_warn_after_seven_days(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "activity_state.json"
            save_email_activity_state(
                EmailActivityState(
                    last_triage_at="2026-05-11",
                    last_archive_at="2026-05-11",
                ),
                path=path,
            )

            formatted = format_email_activity_reminder(path=path, today="2026-05-19")

            self.assertIn("E-maily nebyly projity od 2026-05-11", formatted)
            self.assertIn("Dulezite e-maily nebyly archivovany od 2026-05-11", formatted)

    def test_exactly_seven_days_old_does_not_warn(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "activity_state.json"
            save_email_activity_state(
                EmailActivityState(
                    last_triage_at="2026-05-12",
                    last_archive_at="2026-05-12",
                ),
                path=path,
            )

            formatted = format_email_activity_reminder(path=path, today="2026-05-19")

            self.assertIn("7dennim intervalu", formatted)

    def test_record_functions_update_independent_dates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "activity_state.json"

            record_email_triage_completed("2026-05-18", path=path)
            record_email_archive_completed("2026-05-19", path=path)
            state = load_email_activity_state(path)

            self.assertEqual(state.last_triage_at, "2026-05-18")
            self.assertEqual(state.last_archive_at, "2026-05-19")

    def test_load_memory_appends_email_activity_section(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir)
            (memory_dir / "note.md").write_text("Bezpecna memory poznamka.", encoding="utf-8")
            original_reminder_formatter = samantha_agent.format_active_due_reminders
            original_email_formatter = samantha_agent.format_email_activity_reminder
            samantha_agent.format_active_due_reminders = lambda: "AKTIVNI PRIPOMINKY:\n- Test"
            samantha_agent.format_email_activity_reminder = lambda: "EMAIL UDRZBA:\n- Test"
            try:
                memory_text = samantha_agent.load_memory(memory_dir=memory_dir)
            finally:
                samantha_agent.format_active_due_reminders = original_reminder_formatter
                samantha_agent.format_email_activity_reminder = original_email_formatter

            self.assertIn("Bezpecna memory poznamka.", memory_text)
            self.assertIn("EMAIL UDRZBA:", memory_text)


if __name__ == "__main__":
    unittest.main()
