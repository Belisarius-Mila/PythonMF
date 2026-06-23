from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from app.backup.activity_state import record_backup_completed
from app.project_audit_report import (
    format_project_audit_result,
    parse_active_project_rows,
    run_samantha_project_audit,
)


ACTIVE_PROJECTS_SAMPLE = """# Project Registry

| Oblast | Priorita | Rezim | Stav | Memory soubor | Handoff | Dalsi krok |
| --- | --- | --- | --- | --- | --- | --- |
| Cockpit Knihovna | 1 | active | [PRIPOMENOUT] Umi URL z `data/private/article_archive/`. | `projects/vedecke_clanky.md` | `handoffs/library.md` | Otestovat otevreni clanku. |
| PictNew | 2 | active | Read-only audit pripraven. | `projects/pictnew.md` | zatim neni | Spustit dry-run. |
| Tax | 3 | active | Ceka na podklady. | `projects/tax.md` | zatim neni | Overit finalni hodnoty. |
| Stary test | 1 | archived | Hotovo. | `projects/old.md` | `handoffs/old.md` | Zadny dalsi krok. |
"""

MEMORY_INDEX_SAMPLE = """# Memory Index

- `reports/systemovy_audit.txt` - [PRIPOMENOUT] aktualni audit.
- `handoffs/library.md` - [PRIPOMENOUT] knihovna.
"""


def fake_git_runner(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
    command = args[0] if args else kwargs.get("args", [])
    if isinstance(command, list) and command[:2] == ["git", "status"]:
        return subprocess.CompletedProcess(
            command,
            0,
            "## main...origin/main [ahead 1]\n M Samantha_Agent/app/cockpit.py\n?? Samantha_Agent/app/new.py\n",
            "",
        )
    if isinstance(command, list) and command[:2] == ["git", "ls-files"]:
        return subprocess.CompletedProcess(command, 0, "", "")
    return subprocess.CompletedProcess(command, 0, "", "")


class ProjectAuditReportTests(unittest.TestCase):
    def test_parse_active_project_rows_keeps_lifecycle_and_redacts_private_paths(self) -> None:
        rows = parse_active_project_rows(ACTIVE_PROJECTS_SAMPLE)

        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0].name, "Cockpit Knihovna")
        self.assertEqual(rows[0].priority, "1")
        self.assertEqual(rows[0].lifecycle, "active")
        self.assertNotIn("data/private", rows[0].status)
        self.assertEqual(rows[-1].lifecycle, "archived")

    def test_quick_audit_contains_manual_report_shape_without_private_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project_root = root / "Samantha_Agent"
            memory_dir = project_root / "memory"
            memory_dir.mkdir(parents=True)
            (memory_dir / "ACTIVE_PROJECTS.md").write_text(ACTIVE_PROJECTS_SAMPLE, encoding="utf-8")
            (memory_dir / "MEMORY_INDEX.md").write_text(MEMORY_INDEX_SAMPLE, encoding="utf-8")
            (project_root / "app.py").write_text("print('ok')\n", encoding="utf-8")
            backup_path = project_root / "data" / "backup" / "activity_state.json"
            record_backup_completed("2026-06-23", path=backup_path)

            result = run_samantha_project_audit(
                mode="quick",
                memory_dir=memory_dir,
                project_root=project_root,
                repo_root=root,
                backup_state_path=backup_path,
                runner=fake_git_runner,
            )
            text = format_project_audit_result(result)

        self.assertIn("RANNI PROVOZNI POZNAMKA", text)
        self.assertIn("RYCHLE DOPORUCENI PRO DNES", text)
        self.assertIn("PRIORITA 1 - HLAVNI KANDIDATI", text)
        self.assertIn("TOOLY A SCHOPNOSTI - RYCHLA MAPA", text)
        self.assertIn("VRSTVY - SYSTEMOVA ARCHITEKTURA", text)
        self.assertIn("Cockpit Knihovna", text)
        self.assertIn("PictNew", text)
        self.assertNotIn("Stary test", text)
        self.assertNotIn("data/private", text)
        self.assertIn("Nejdriv rozhodnout git stav", text)

    def test_save_writes_git_safe_report_to_reports_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project_root = root / "Samantha_Agent"
            memory_dir = project_root / "memory"
            reports_dir = memory_dir / "reports"
            memory_dir.mkdir(parents=True)
            (memory_dir / "ACTIVE_PROJECTS.md").write_text(ACTIVE_PROJECTS_SAMPLE, encoding="utf-8")
            (memory_dir / "MEMORY_INDEX.md").write_text(MEMORY_INDEX_SAMPLE, encoding="utf-8")
            backup_path = project_root / "data" / "backup" / "activity_state.json"
            record_backup_completed("2026-06-23", path=backup_path)

            result = run_samantha_project_audit(
                mode="full",
                save=True,
                memory_dir=memory_dir,
                project_root=project_root,
                repo_root=root,
                reports_dir=reports_dir,
                backup_state_path=backup_path,
                runner=fake_git_runner,
            )

            self.assertIsNotNone(result.saved_path)
            assert result.saved_path is not None
            self.assertTrue(result.saved_path.exists())
            self.assertTrue(result.saved_path.name.startswith("systemovy_audit_projekty_tooly_vrstvy_"))
            self.assertNotIn("data/private", result.saved_path.read_text(encoding="utf-8"))

    def test_save_does_not_overwrite_existing_same_day_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project_root = root / "Samantha_Agent"
            memory_dir = project_root / "memory"
            reports_dir = memory_dir / "reports"
            reports_dir.mkdir(parents=True)
            existing = reports_dir / "systemovy_audit_projekty_tooly_vrstvy_2026_06_23.txt"
            existing.write_text("manual report\n", encoding="utf-8")
            (memory_dir / "ACTIVE_PROJECTS.md").write_text(ACTIVE_PROJECTS_SAMPLE, encoding="utf-8")
            (memory_dir / "MEMORY_INDEX.md").write_text(MEMORY_INDEX_SAMPLE, encoding="utf-8")
            backup_path = project_root / "data" / "backup" / "activity_state.json"
            record_backup_completed("2026-06-23", path=backup_path)

            result = run_samantha_project_audit(
                mode="full",
                save=True,
                memory_dir=memory_dir,
                project_root=project_root,
                repo_root=root,
                reports_dir=reports_dir,
                backup_state_path=backup_path,
                runner=fake_git_runner,
            )

            self.assertEqual(existing.read_text(encoding="utf-8"), "manual report\n")
            self.assertIsNotNone(result.saved_path)
            assert result.saved_path is not None
            self.assertNotEqual(result.saved_path, existing)
            self.assertRegex(result.saved_path.name, r"systemovy_audit_projekty_tooly_vrstvy_\d{4}_\d{2}_\d{2}_\d{6}\.txt")


if __name__ == "__main__":
    unittest.main()
