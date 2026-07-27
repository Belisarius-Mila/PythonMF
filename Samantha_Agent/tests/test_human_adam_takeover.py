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

    def test_audit_accepts_graph_valid_checkpoint_with_stale_base_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source, manager = prepare_with_origin(Path(temp_dir))
            source_head = git(source, "rev-parse", "HEAD")
            (manager.project_root / "tracked.py").write_text("VALUE = 22\n", encoding="utf-8")
            checkpoint = manager.checkpoint(confirmed=True, message="WIP stale metadata audit")
            manager.metadata_path.write_text(
                '{"schema_version": 1, "base_head": "stale"}\n',
                encoding="utf-8",
            )

            status = manager.status()
            plan = build_takeover_plan(workspace=manager)

        self.assertEqual(status["workspace_relation"], "local_ahead")
        self.assertEqual(status["base_head"], "stale")
        self.assertEqual(plan.source_head, source_head)
        self.assertEqual(plan.checkpoint_parent, source_head)
        self.assertEqual(plan.checkpoint_head, checkpoint["checkpoint_head"])

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

    def test_deferred_push_fast_forwards_local_main_while_origin_stays_behind(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source, manager = prepare_with_origin(Path(temp_dir))
            origin_head = git(source, "rev-parse", "origin/main")
            (manager.project_root / "tracked.py").write_text(
                "VALUE = 301\n", encoding="utf-8"
            )
            checkpoint = manager.checkpoint(
                confirmed=True,
                message="Local daytime checkpoint",
            )

            first = apply_takeover(
                confirmation=CONFIRMATION_TEXT,
                push=False,
                defer_remote_push=True,
                workspace=manager,
            )
            first_local_head = git(source, "rev-parse", "HEAD")
            first_origin_head = git(source, "rev-parse", "origin/main")

            (manager.project_root / "tracked.py").write_text(
                "VALUE = 302\n", encoding="utf-8"
            )
            second_checkpoint = manager.checkpoint(
                confirmed=True,
                message="Second local daytime checkpoint",
            )
            second = apply_takeover(
                confirmation=CONFIRMATION_TEXT,
                push=False,
                defer_remote_push=True,
                workspace=manager,
            )
            second_local_head = git(source, "rev-parse", "HEAD")
            second_origin_head = git(source, "rev-parse", "origin/main")

        self.assertTrue(first["applied"])
        self.assertFalse(first["pushed"])
        self.assertTrue(first["remote_push_deferred"])
        self.assertEqual(first_local_head, checkpoint["checkpoint_head"])
        self.assertEqual(first_origin_head, origin_head)
        self.assertTrue(second["applied"])
        self.assertFalse(second["pushed"])
        self.assertEqual(second_local_head, second_checkpoint["checkpoint_head"])
        self.assertEqual(second_origin_head, origin_head)

    def test_local_takeover_without_push_requires_batch_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _source, manager = prepare_with_origin(Path(temp_dir))
            (manager.project_root / "tracked.py").write_text(
                "VALUE = 303\n", encoding="utf-8"
            )
            manager.checkpoint(confirmed=True, message="Local checkpoint")

            with self.assertRaisesRegex(TakeoverError, "dávkový režim"):
                apply_takeover(
                    confirmation=CONFIRMATION_TEXT,
                    push=False,
                    workspace=manager,
                )

    def test_remote_divergence_does_not_block_another_deferred_local_takeover(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, manager = prepare_with_origin(root)
            local_base = source / "Samantha_Agent" / "local_base.py"
            local_base.write_text("LOCAL = 1\n", encoding="utf-8")
            git(source, "add", str(local_base.relative_to(source)))
            git(source, "commit", "-m", "Existing local daytime work")
            manager.sync_from_main(confirmed=True)

            competitor = root / "competitor-divergence"
            subprocess.run(
                ["/usr/bin/git", "clone", str(root / "origin.git"), str(competitor)],
                capture_output=True,
                text=True,
                check=True,
            )
            git(competitor, "config", "user.name", "Other writer")
            git(competitor, "config", "user.email", "other@example.invalid")
            (competitor / "remote.txt").write_text("remote\n", encoding="utf-8")
            git(competitor, "add", "remote.txt")
            git(competitor, "commit", "-m", "Remote divergent work")
            git(competitor, "push", "origin", "main")
            git(source, "fetch", "origin", "main:refs/remotes/origin/main")

            (manager.project_root / "tracked.py").write_text(
                "VALUE = 304\n",
                encoding="utf-8",
            )
            checkpoint = manager.checkpoint(
                confirmed=True,
                message="Continue local work after divergence",
            )
            result = apply_takeover(
                confirmation=CONFIRMATION_TEXT,
                push=False,
                defer_remote_push=True,
                workspace=manager,
            )

            local_head = git(source, "rev-parse", "HEAD")
            remote_head = git(source, "rev-parse", "origin/main")

        self.assertTrue(result["applied"])
        self.assertTrue(result["remote_push_deferred"])
        self.assertEqual(local_head, checkpoint["checkpoint_head"])
        self.assertNotEqual(local_head, remote_head)

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

    def test_audit_rejects_tracked_source_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, manager = prepare_with_origin(root)
            (manager.project_root / "tracked.py").write_text("VALUE = 4\n", encoding="utf-8")
            manager.checkpoint(confirmed=True, message="WIP blocked by source")
            (source / "Samantha_Agent" / "tracked.py").write_text("SOURCE DIRTY\n", encoding="utf-8")
            with self.assertRaises(TakeoverError):
                build_takeover_plan(workspace=manager)

    def test_audit_accepts_small_checkpoint_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _source, manager = prepare_with_origin(Path(temp_dir))
            (manager.project_root / "tracked.py").unlink()
            manager.checkpoint(confirmed=True, message="WIP deletion")

            plan = build_takeover_plan(workspace=manager)

        self.assertEqual(
            plan.changes,
            ({"status": "D", "path": "Samantha_Agent/tracked.py"},),
        )

    def test_audit_rejects_bulk_checkpoint_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, manager = prepare_with_origin(root)
            relative_paths = [
                f"Samantha_Agent/delete-{index:02d}.py"
                for index in range(11)
            ]
            for relative_path in relative_paths:
                (source / relative_path).write_text("DELETE = True\n", encoding="utf-8")
            git(source, "add", *relative_paths)
            git(source, "commit", "-m", "Add bulk deletion fixtures")
            git(source, "push", "origin", "main")
            manager.sync_from_main(confirmed=True)
            for relative_path in relative_paths:
                (manager.workspace_root / relative_path).unlink()
            manager.checkpoint(confirmed=True, message="WIP bulk deletion")

            with self.assertRaisesRegex(TakeoverError, "hromadné mazání"):
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
