from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.communication.human_adam_workspace import HumanAdamWorkspaceManager
from app.workflows.commands import WORKFLOW_COMMANDS
from scripts import human_adam_takeover as takeover_module
from scripts.human_adam_takeover import (
    CONFIRMATION_TEXT,
    TakeoverError,
    apply_takeover,
    build_takeover_plan,
)
from tests.test_human_adam_workspace import git, make_source


def prepare_with_origin(root: Path) -> tuple[Path, HumanAdamWorkspaceManager]:
    source = make_source(root)
    remote = root / "origin.git"
    subprocess.run(
        ["/usr/bin/git", "init", "--bare", str(remote)],
        capture_output=True,
        text=True,
        check=True,
    )
    git(source, "remote", "add", "origin", str(remote))
    git(source, "push", "-u", "origin", "main")
    manager = HumanAdamWorkspaceManager(
        source_repo=source,
        workspace_root=root / "cell",
        metadata_path=root / "meta.json",
    )
    manager.prepare()
    return source, manager


class HumanAdamTakeoverTests(unittest.TestCase):
    def test_audit_accepts_one_clean_direct_checkpoint_and_hides_contents(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source, manager = prepare_with_origin(Path(temp_dir))
            (manager.project_root / "tracked.py").write_text("VALUE = 2\n", encoding="utf-8")
            manager.checkpoint(confirmed=True, message="WIP takeover test")

            plan = build_takeover_plan(workspace=manager)
            public = plan.public_dict()
            source_head_after = git(source, "rev-parse", "HEAD")

        self.assertEqual(plan.checkpoint_parent, plan.source_head)
        self.assertEqual(public["operation"], "exact_fast_forward")
        self.assertEqual(public["changes"], [{"status": "M", "path": "Samantha_Agent/tracked.py"}])
        self.assertEqual(public["source_untracked_count"], 1)
        self.assertNotIn("VALUE = 2", str(public))
        self.assertEqual(source_head_after, plan.source_head)

    def test_apply_requires_exact_confirmation_then_fast_forwards_and_pushes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source, manager = prepare_with_origin(Path(temp_dir))
            (manager.project_root / "tracked.py").write_text("VALUE = 3\n", encoding="utf-8")
            checkpoint = manager.checkpoint(confirmed=True, message="WIP exact takeover")
            with self.assertRaises(TakeoverError):
                apply_takeover(confirmation="ano", push=True, workspace=manager)

            result = apply_takeover(
                confirmation=CONFIRMATION_TEXT,
                push=True,
                workspace=manager,
            )

            source_head = git(source, "rev-parse", "HEAD")
            origin_head = git(source, "rev-parse", "origin/main")
            workspace_status = manager.status()

        self.assertTrue(result["applied"])
        self.assertTrue(result["pushed"])
        self.assertEqual(source_head, checkpoint["checkpoint_head"])
        self.assertEqual(origin_head, source_head)
        self.assertEqual(workspace_status["workspace_relation"], "aligned")
        self.assertEqual(workspace_status["base_head"], source_head)

    def test_apply_reports_fast_forward_push_and_alignment_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _source, manager = prepare_with_origin(Path(temp_dir))
            (manager.project_root / "tracked.py").write_text("VALUE = 30\n", encoding="utf-8")
            manager.checkpoint(confirmed=True, message="WIP progress callback")
            progress: list[tuple[str, str]] = []

            apply_takeover(
                confirmation=CONFIRMATION_TEXT,
                push=True,
                workspace=manager,
                progress_callback=lambda stage, outcome: progress.append((stage, outcome)),
            )

        self.assertEqual(
            progress,
            [
                ("remote_recheck", "running"),
                ("remote_recheck", "passed"),
                ("push", "running"),
                ("push", "passed"),
                ("fast_forward", "running"),
                ("fast_forward", "passed"),
                ("workspace_alignment", "running"),
                ("workspace_alignment", "passed"),
            ],
        )

    def test_remote_change_after_checkpoint_is_rejected_before_local_main_moves(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, manager = prepare_with_origin(root)
            original_source_head = git(source, "rev-parse", "HEAD")
            (manager.project_root / "tracked.py").write_text("VALUE = 31\n", encoding="utf-8")
            manager.checkpoint(confirmed=True, message="WIP loses remote race")

            competitor = root / "competitor"
            subprocess.run(
                ["/usr/bin/git", "clone", str(root / "origin.git"), str(competitor)],
                capture_output=True,
                text=True,
                check=True,
            )
            git(competitor, "config", "user.name", "Daily Owl")
            git(competitor, "config", "user.email", "owl@example.invalid")
            (competitor / "owl.txt").write_text("new daily audio\n", encoding="utf-8")
            git(competitor, "add", "owl.txt")
            git(competitor, "commit", "-m", "Update owl audio")
            git(competitor, "push", "origin", "main")

            with self.assertRaisesRegex(TakeoverError, "GitHub main se během kontroly změnil"):
                apply_takeover(
                    confirmation=CONFIRMATION_TEXT,
                    push=True,
                    workspace=manager,
                )

            source_head = git(source, "rev-parse", "HEAD")
            workspace_status = manager.status()

        self.assertEqual(source_head, original_source_head)
        self.assertEqual(workspace_status["workspace_relation"], "local_ahead")

    def test_push_failure_never_fast_forwards_local_main(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source, manager = prepare_with_origin(Path(temp_dir))
            original_source_head = git(source, "rev-parse", "HEAD")
            (manager.project_root / "tracked.py").write_text("VALUE = 32\n", encoding="utf-8")
            manager.checkpoint(confirmed=True, message="WIP atomic push failure")
            progress: list[tuple[str, str]] = []
            original_git = takeover_module._git

            def fail_push(cwd, args, **kwargs):
                if list(args[:2]) == ["push", "origin"]:
                    raise TakeoverError("simulated non-fast-forward")
                return original_git(cwd, args, **kwargs)

            with patch("scripts.human_adam_takeover._git", side_effect=fail_push):
                with self.assertRaisesRegex(TakeoverError, "simulated non-fast-forward"):
                    apply_takeover(
                        confirmation=CONFIRMATION_TEXT,
                        push=True,
                        workspace=manager,
                        progress_callback=lambda stage, outcome: progress.append((stage, outcome)),
                    )

            source_head = git(source, "rev-parse", "HEAD")
            workspace_status = manager.status()

        self.assertEqual(source_head, original_source_head)
        self.assertEqual(workspace_status["workspace_relation"], "local_ahead")
        self.assertIn(("push", "running"), progress)
        self.assertNotIn(("fast_forward", "running"), progress)

    def test_audit_rejects_tracked_source_changes_and_checkpoint_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, manager = prepare_with_origin(root)
            (manager.project_root / "tracked.py").write_text("VALUE = 4\n", encoding="utf-8")
            manager.checkpoint(confirmed=True, message="WIP blocked by source")
            (source / "Samantha_Agent" / "tracked.py").write_text("SOURCE DIRTY\n", encoding="utf-8")
            with self.assertRaises(TakeoverError):
                build_takeover_plan(workspace=manager)

        with tempfile.TemporaryDirectory() as temp_dir:
            source, manager = prepare_with_origin(Path(temp_dir))
            (manager.project_root / "tracked.py").unlink()
            manager.checkpoint(confirmed=True, message="WIP deletion")
            with self.assertRaises(TakeoverError):
                build_takeover_plan(workspace=manager)

    def test_takeover_commands_are_registered_with_confirmation_only_on_apply(self) -> None:
        commands = {item.command_id: item for item in WORKFLOW_COMMANDS}

        self.assertFalse(commands["human_adam_takeover_audit"].requires_confirmation)
        self.assertTrue(commands["human_adam_takeover_apply"].requires_confirmation)
        self.assertIn("audit", commands["human_adam_takeover_audit"].argv)
        self.assertIn("--push", commands["human_adam_takeover_apply"].argv)
        self.assertIn(CONFIRMATION_TEXT, commands["human_adam_takeover_apply"].argv)


if __name__ == "__main__":
    unittest.main()
