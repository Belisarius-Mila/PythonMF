from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from app.codex_appserver import AppServerError
from app.project_continuity import ProjectContinuityService, parse_project_catalog


CATALOG = """\
| Oblast | Priorita | Rezim | Stav | Memory soubor | Handoff | Dalsi krok |
| --- | --- | --- | --- | --- | --- | --- |
| Testovací projekt | 1 | active | Rozpracováno | `memory/tvbcp/test_project.txt` | `memory/handoffs/test_project.md`; `handoffs/older.md` | Pokračovat. |
| Pozastavený projekt | 2 | paused | Čeká | `memory/tvbcp/paused.txt` | `memory/handoffs/paused.md` | Nic. |
| Nebezpečná cesta | 1 | active | Chyba | `memory/tvbcp/../secret.txt` | `memory/handoffs/../../secret.md` | Nic. |
"""


def run_git(root: Path, *args: str) -> None:
    subprocess.run(
        ["/usr/bin/git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )


class ProjectContinuityTests(unittest.TestCase):
    def make_project(self, root: Path) -> ProjectContinuityService:
        (root / "memory/handoffs").mkdir(parents=True)
        (root / "memory/tvbcp").mkdir(parents=True)
        (root / "memory/ACTIVE_PROJECTS.md").write_text(CATALOG, encoding="utf-8")
        (root / "memory/handoffs/test_project.md").write_text("Handoff\n", encoding="utf-8")
        (root / "memory/handoffs/older.md").write_text("Starší handoff\n", encoding="utf-8")
        (root / "memory/tvbcp/test_project.txt").write_text("TVBCP\n", encoding="utf-8")
        run_git(root, "init")
        run_git(root, "config", "user.name", "Test Adam")
        run_git(root, "config", "user.email", "adam@example.invalid")
        run_git(root, "add", "memory")
        run_git(root, "commit", "-m", "Create project memory")
        return ProjectContinuityService(project_root=root)

    def binding(self, service: ProjectContinuityService) -> dict[str, str]:
        project = service.catalog()[0]
        return service.resolve_binding(
            project_id=project.project_id,
            handoff_path="memory/handoffs/test_project.md",
        )

    def audit(
        self,
        service: ProjectContinuityService,
        *,
        binding: dict[str, str] | None = None,
        review: dict[str, object] | None = None,
        anchor: dict[str, object] | None = None,
        workspace_root: Path | None = None,
    ) -> dict[str, object]:
        return service.audit(
            binding=binding or self.binding(service),
            workspace_root=workspace_root or service.project_root,
            workspace_review=review or {"changes": [], "checkpoint_changes": []},
            context_anchor=anchor or {},
        )

    def test_catalog_includes_only_active_projects_with_safe_handoffs(self) -> None:
        projects = parse_project_catalog(CATALOG)

        self.assertEqual([project.label for project in projects], ["Testovací projekt"])
        self.assertEqual(
            projects[0].handoff_paths,
            ("memory/handoffs/test_project.md", "memory/handoffs/older.md"),
        )
        self.assertEqual(projects[0].tvbcp_paths, ("memory/tvbcp/test_project.txt",))

    def test_binding_accepts_only_registered_existing_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = self.make_project(Path(temp_dir))
            binding = self.binding(service)
            with self.assertRaisesRegex(AppServerError, "registrovaný aktuální handoff"):
                service.resolve_binding(
                    project_id=binding["project_id"],
                    handoff_path="memory/handoffs/unregistered.md",
                )

        self.assertEqual(binding["project_label"], "Testovací projekt")
        self.assertEqual(binding["tvbcp_path"], "memory/tvbcp/test_project.txt")

    def test_audit_is_current_when_no_newer_evidence_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = self.make_project(Path(temp_dir))
            result = self.audit(service)

        self.assertEqual(result["state"], "current")
        self.assertTrue(result["read_only"])
        self.assertFalse(result["blocking"])

    def test_workspace_changes_without_handoff_need_update(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = self.make_project(Path(temp_dir))
            result = self.audit(
                service,
                review={"changes": [{"path": "app/example.py"}], "checkpoint_changes": []},
            )

        self.assertEqual(result["state"], "needs_update")
        self.assertIn("handoff mezi nimi není", " ".join(result["reasons"]))

    def test_newer_anchor_needs_update(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = self.make_project(Path(temp_dir))
            result = self.audit(
                service,
                anchor={"revision": 3, "updated_at": "2099-01-01T12:00:00+00:00"},
            )

        self.assertEqual(result["state"], "needs_update")
        self.assertIn("kotva", " ".join(result["reasons"]))

    def test_missing_workspace_handoff_is_unverifiable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, tempfile.TemporaryDirectory() as workspace_dir:
            service = self.make_project(Path(temp_dir))
            result = self.audit(service, workspace_root=Path(workspace_dir))

        self.assertEqual(result["state"], "unverifiable")
        self.assertIn("pracovním prostoru", str(result["message"]))


if __name__ == "__main__":
    unittest.main()
