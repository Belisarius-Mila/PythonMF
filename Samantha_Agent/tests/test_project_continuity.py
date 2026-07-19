from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from app.codex_appserver import AppServerError
from app.project_continuity import ProjectContinuityService, parse_project_catalog
from app.project_continuity import PROJECT_BOOTSTRAP_CONFIRMATION


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

    def test_project_bootstrap_preview_is_read_only_and_create_writes_two_git_safe_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self.make_project(root)
            registry = root / "memory/ACTIVE_PROJECTS.md"
            before = registry.read_text(encoding="utf-8")
            preview = service.project_bootstrap_preview(
                project_label="Rodinný kalendář",
                priority="2",
                goal="Připravit read-only náhled upozornění D-2 a D-1.",
                next_step="Zobrazit náhled bez odesílání e-mailu.",
            )
            self.assertEqual(before, registry.read_text(encoding="utf-8"))
            self.assertFalse((root / preview["handoff_path"]).exists())

            created = service.create_project_bootstrap(
                project_label="Rodinný kalendář",
                priority="2",
                goal="Připravit read-only náhled upozornění D-2 a D-1.",
                next_step="Zobrazit náhled bez odesílání e-mailu.",
                confirmation=PROJECT_BOOTSTRAP_CONFIRMATION,
            )
            handoff = root / created["handoff_path"]
            project = next(item for item in service.catalog() if item.label == "Rodinný kalendář")
            handoff_exists = handoff.is_file()
            handoff_text = handoff.read_text(encoding="utf-8")
            registry_text = registry.read_text(encoding="utf-8")

        self.assertTrue(preview["read_only"])
        self.assertFalse(preview["writes_performed"])
        self.assertTrue(created["writes_performed"])
        self.assertTrue(created["created"])
        self.assertEqual(project.project_id, created["project_id"])
        self.assertEqual(project.handoff_paths, (created["handoff_path"],))
        self.assertTrue(handoff_exists)
        self.assertIn("Vlastni implementace zatim nezacala", handoff_text)
        self.assertIn("Rodinný kalendář", registry_text)

    def test_project_bootstrap_rejects_duplicate_unsafe_text_and_missing_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self.make_project(root)
            with self.assertRaisesRegex(AppServerError, "už v aktivním registru"):
                service.project_bootstrap_preview(
                    project_label="Testovací projekt",
                    priority="1",
                    goal="Platný cíl projektu.",
                    next_step="Platný první krok.",
                )
            with self.assertRaisesRegex(AppServerError, "bezpečný textový řádek"):
                service.project_bootstrap_preview(
                    project_label="Nový | projekt",
                    priority="2",
                    goal="Platný cíl projektu.",
                    next_step="Platný první krok.",
                )
            with self.assertRaisesRegex(AppServerError, "potvrzovací věta"):
                service.create_project_bootstrap(
                    project_label="Nový projekt",
                    priority="2",
                    goal="Platný cíl projektu.",
                    next_step="Platný první krok.",
                    confirmation="ano",
                )

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

    def test_handoff_proposal_is_metadata_only_ready_and_does_not_write_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = self.make_project(Path(temp_dir))
            handoff = service.project_root / "memory/handoffs/test_project.md"
            before = handoff.read_text(encoding="utf-8")
            result = service.handoff_proposal(
                binding=self.binding(service),
                topic="Bezpečný návrh handoffu",
                workspace_review={
                    "local_checkpoint_ahead": True,
                    "local_commit_count": 1,
                    "checkpoint_head": "a" * 40,
                    "checkpoint_subject": "WIP návrh handoffu",
                    "checkpoint_changes": [
                        {"status": "M", "path": "Samantha_Agent/app/example.py"},
                        {"status": "A", "path": "Samantha_Agent/tests/test_example.py"},
                    ],
                },
                context_anchor={"revision": 4, "active": True},
            )
            after = handoff.read_text(encoding="utf-8")

        self.assertTrue(result["available"])
        self.assertEqual(result["state"], "ready")
        self.assertTrue(result["read_only"])
        self.assertFalse(result["blocking"])
        self.assertFalse(result["writes_performed"])
        self.assertEqual(before, after)
        self.assertIn("ZATÍM NEULOŽENO", result["draft"])
        self.assertIn("revize 4, připnutá", result["draft"])
        self.assertIn("Samantha_Agent/app/example.py", result["draft"])
        self.assertNotIn("Handoff\n", result["draft"])

    def test_handoff_proposal_waits_for_checkpoint_and_rejects_private_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = self.make_project(Path(temp_dir))
            binding = self.binding(service)
            waiting = service.handoff_proposal(
                binding=binding,
                topic="Čekající návrh",
                workspace_review={"local_checkpoint_ahead": False},
                context_anchor={},
            )
            unsafe = service.handoff_proposal(
                binding=binding,
                topic="Nebezpečný návrh",
                workspace_review={
                    "local_checkpoint_ahead": True,
                    "local_commit_count": 1,
                    "checkpoint_head": "b" * 40,
                    "checkpoint_subject": "WIP private",
                    "checkpoint_changes": [
                        {"status": "A", "path": "Samantha_Agent/data/private/secret.txt"}
                    ],
                },
                context_anchor={},
            )

        self.assertEqual(waiting["state"], "waiting_checkpoint")
        self.assertFalse(waiting["available"])
        self.assertEqual(unsafe["state"], "unverifiable")
        self.assertFalse(unsafe["available"])
        self.assertIn("nevhodnou", unsafe["message"])

    def test_takeover_check_verifies_registered_handoff_in_checkpoint_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = self.make_project(Path(temp_dir))
            handoff = service.project_root / "memory/handoffs/test_project.md"
            before = handoff.read_text(encoding="utf-8")
            result = service.takeover_handoff_check(
                binding=self.binding(service),
                checkpoint_changes=[
                    {"status": "M", "path": "Samantha_Agent/memory/handoffs/test_project.md"},
                    {"status": "M", "path": "Samantha_Agent/app/example.py"},
                ],
                project_dir_name="Samantha_Agent",
            )
            after = handoff.read_text(encoding="utf-8")

        self.assertEqual(result["state"], "verified")
        self.assertTrue(result["handoff_in_checkpoint"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["blocking"])
        self.assertFalse(result["writes_performed"])
        self.assertEqual(before, after)

    def test_takeover_check_warns_without_blocking_when_handoff_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = self.make_project(Path(temp_dir))
            result = service.takeover_handoff_check(
                binding=self.binding(service),
                checkpoint_changes=[
                    {"status": "M", "path": "Samantha_Agent/app/example.py"},
                ],
                project_dir_name="Samantha_Agent",
            )

        self.assertEqual(result["state"], "warning")
        self.assertFalse(result["handoff_in_checkpoint"])
        self.assertFalse(result["blocking"])
        self.assertIn("neobsahuje", result["message"])

    def test_takeover_check_is_unverifiable_for_wrong_project_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = self.make_project(Path(temp_dir))
            result = service.takeover_handoff_check(
                binding={
                    "project_id": "wrong-project-123",
                    "handoff_path": "memory/handoffs/test_project.md",
                },
                checkpoint_changes=[
                    {"status": "M", "path": "Samantha_Agent/memory/handoffs/test_project.md"},
                ],
                project_dir_name="Samantha_Agent",
            )

        self.assertEqual(result["state"], "unverifiable")
        self.assertFalse(result["blocking"])
        self.assertNotIn("Handoff\n", str(result))

    def test_deployment_completion_entry_contains_only_verified_safe_facts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = self.make_project(Path(temp_dir))
            result = service.deployment_completion_entry(
                binding=self.binding(service),
                checkpoint_head="c" * 40,
                test_count=849,
                deployed_at="2026-07-19T12:55:31+00:00",
                next_step="Ručně ověřit novou kartu v Cockpitu.",
            )

        self.assertEqual(result["target_handoff"], "memory/handoffs/test_project.md")
        self.assertIn("Stav: nasazeno", result["entry"])
        self.assertIn("849 testů, OK", result["entry"])
        self.assertIn("Smoke test: 5/5", result["entry"])
        self.assertIn("Ručně ověřit", result["entry"])
        self.assertNotIn("Handoff\n", result["entry"])

    def test_deployment_completion_entry_rejects_multiline_next_step(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = self.make_project(Path(temp_dir))
            with self.assertRaisesRegex(AppServerError, "jeden krátký řádek"):
                service.deployment_completion_entry(
                    binding=self.binding(service),
                    checkpoint_head="d" * 40,
                    test_count=849,
                    deployed_at="2026-07-19T12:55:31+00:00",
                    next_step="První řádek\ndruhý řádek",
                )


if __name__ == "__main__":
    unittest.main()
