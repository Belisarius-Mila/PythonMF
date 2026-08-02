from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app import samantha_agent
from app.backup.activity_state import (
    BackupActivityState,
    backup_activity_status,
    format_backup_activity_reminder,
    load_backup_activity_state,
    record_backup_completed,
    resolve_backup_activity_state_path,
    save_backup_activity_state,
)
from app.file_persistence import lock_path_for


class BackupActivityStateTests(unittest.TestCase):
    def test_knihovna_workspace_uses_canonical_backup_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            canonical_root = Path(temp_dir) / "Samantha_Agent"
            workspace_root = (
                canonical_root
                / "data"
                / "private"
                / "human_adam_profiles"
                / "knihovna"
                / "workspace"
                / "Samantha_Agent"
            )
            state_path = resolve_backup_activity_state_path(workspace_root)

            save_backup_activity_state(
                BackupActivityState(last_backup_at="2026-08-02"),
                path=state_path,
            )
            status = backup_activity_status(path=state_path, today="2026-08-02")

            self.assertEqual(
                state_path,
                canonical_root.resolve() / "data" / "backup" / "activity_state.json",
            )
            self.assertEqual(status["status"], "ok")
            self.assertFalse(
                (workspace_root / "data" / "backup" / "activity_state.json").exists()
            )

    def test_human_adam_workspace_uses_canonical_backup_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            canonical_root = Path(temp_dir) / "Samantha_Agent"
            workspace_root = (
                canonical_root
                / "data"
                / "private"
                / "appserver_remote"
                / "workspace"
                / "Samantha_Agent"
            )

            self.assertEqual(
                resolve_backup_activity_state_path(workspace_root),
                canonical_root.resolve() / "data" / "backup" / "activity_state.json",
            )

    def test_regular_checkout_keeps_local_backup_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "standalone" / "Samantha_Agent"

            self.assertEqual(
                resolve_backup_activity_state_path(project_root),
                project_root.resolve() / "data" / "backup" / "activity_state.json",
            )

    def test_missing_state_prompts_for_backup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "activity_state.json"

            formatted = format_backup_activity_reminder(path=path, today="2026-05-19")

            self.assertIn("Neni zaznam o posledni zaloze", formatted)
            self.assertIn("nic nekopiruje", formatted)

    def test_recent_state_has_no_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "activity_state.json"
            save_backup_activity_state(
                BackupActivityState(
                    last_backup_at="2026-05-17",
                    last_backup_target="/Volumes/Falta/SamanthaSecureBackup",
                    last_backup_mode="dry-run",
                ),
                path=path,
            )

            formatted = format_backup_activity_reminder(path=path, today="2026-05-19")
            status = backup_activity_status(path=path, today="2026-05-19")

            self.assertIn("3dennim intervalu", formatted)
            self.assertNotIn("Je starsi nez 3 dny", formatted)
            self.assertTrue(status["ok"])
            self.assertEqual(status["status"], "ok")
            self.assertEqual(status["last_backup_at"], "2026-05-17")
            self.assertEqual(status["age_days"], 2)

    def test_old_state_warns_after_three_days(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "activity_state.json"
            save_backup_activity_state(
                BackupActivityState(
                    last_backup_at="2026-05-15",
                    last_backup_target="/Volumes/Falta/SamanthaSecureBackup",
                    last_backup_mode="manual",
                ),
                path=path,
            )

            formatted = format_backup_activity_reminder(path=path, today="2026-05-19")
            status = backup_activity_status(path=path, today="2026-05-19")

            self.assertIn("Posledni uspesna zaloha byla 2026-05-15", formatted)
            self.assertIn("Je starsi nez 3 dny", formatted)
            self.assertIn("/Volumes/Falta/SamanthaSecureBackup", formatted)
            self.assertFalse(status["ok"])
            self.assertEqual(status["status"], "stale")
            self.assertEqual(status["age_days"], 4)

    def test_exactly_three_days_old_does_not_warn(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "activity_state.json"
            save_backup_activity_state(
                BackupActivityState(last_backup_at="2026-05-16"),
                path=path,
            )

            formatted = format_backup_activity_reminder(path=path, today="2026-05-19")

            self.assertIn("3dennim intervalu", formatted)

    def test_record_backup_completed_saves_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "activity_state.json"

            record_backup_completed(
                "2026-05-19",
                target="/Volumes/Falta/SamanthaSecureBackup",
                mode="manual",
                path=path,
            )
            state = load_backup_activity_state(path)

            self.assertEqual(state.last_backup_at, "2026-05-19")
            self.assertEqual(state.last_backup_target, "/Volumes/Falta/SamanthaSecureBackup")
            self.assertEqual(state.last_backup_mode, "manual")
            self.assertTrue(lock_path_for(path).exists())
            self.assertEqual(list(path.parent.glob(f".{path.name}.*.tmp")), [])

    def test_load_memory_appends_backup_activity_section(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir)
            (memory_dir / "note.md").write_text("Bezpecna memory poznamka.", encoding="utf-8")
            original_reminder_formatter = samantha_agent.format_active_due_reminders
            original_email_formatter = samantha_agent.format_email_activity_reminder
            original_backup_formatter = samantha_agent.format_backup_activity_reminder
            samantha_agent.format_active_due_reminders = lambda: "AKTIVNI PRIPOMINKY:\n- Test"
            samantha_agent.format_email_activity_reminder = lambda: "EMAIL UDRZBA:\n- Test"
            samantha_agent.format_backup_activity_reminder = lambda: "ZALOHA SAMANTHY:\n- Test"
            try:
                memory_text = samantha_agent.load_memory(memory_dir=memory_dir)
            finally:
                samantha_agent.format_active_due_reminders = original_reminder_formatter
                samantha_agent.format_email_activity_reminder = original_email_formatter
                samantha_agent.format_backup_activity_reminder = original_backup_formatter

            self.assertIn("Bezpecna memory poznamka.", memory_text)
            self.assertIn("ZALOHA SAMANTHY:", memory_text)


if __name__ == "__main__":
    unittest.main()
