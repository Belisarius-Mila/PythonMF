from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.codex_appserver import AppServerError
from app.communication.human_adam_workspace import HumanAdamWorkspaceManager


def git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["/usr/bin/git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError((completed.stderr or completed.stdout).strip())
    return completed.stdout.strip()


def make_source(root: Path) -> Path:
    source = root / "source"
    source.mkdir()
    git(source, "init", "-b", "main")
    git(source, "config", "user.name", "Human Adam Workspace Test")
    git(source, "config", "user.email", "human-adam-workspace@example.invalid")
    project = source / "Samantha_Agent"
    (project / "memory").mkdir(parents=True)
    (project / "AGENTS.md").write_text("Test instructions\n", encoding="utf-8")
    (project / "memory" / "MEMORY_INDEX.md").write_text("# Index\n", encoding="utf-8")
    (project / "tracked.py").write_text("VALUE = 1\n", encoding="utf-8")
    (source / ".gitignore").write_text("Samantha_Agent/data/private/\n", encoding="utf-8")
    git(source, "add", ".gitignore", "Samantha_Agent/AGENTS.md", "Samantha_Agent/memory/MEMORY_INDEX.md", "Samantha_Agent/tracked.py")
    git(source, "commit", "-m", "Initial")
    private_dir = project / "data" / "private"
    private_dir.mkdir(parents=True)
    (private_dir / "secret.txt").write_text("secret\n", encoding="utf-8")
    (source / "AuditCockpit56_M.txt").write_text("untracked\n", encoding="utf-8")
    return source


class HumanAdamWorkspaceManagerTests(unittest.TestCase):
    def test_prepare_creates_independent_main_clone_without_private_untracked_or_remote(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            workspace = root / "private" / "workspace"
            manager = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=workspace,
                metadata_path=root / "private" / "meta.json",
            )

            prepared = manager.prepare()
            clone_file = workspace / "Samantha_Agent" / "tracked.py"
            clone_file.write_text("VALUE = 2\n", encoding="utf-8")
            changed = manager.status()

            self.assertTrue(prepared["created"])
            self.assertTrue(prepared["prepared"])
            self.assertEqual(prepared["branch"], "main")
            self.assertEqual(prepared["remotes"], [])
            self.assertEqual(prepared["source_pending_changes"], 1)
            self.assertEqual(
                git(workspace, "config", "--local", "--get", "user.name"),
                git(source, "config", "--local", "--get", "user.name"),
            )
            self.assertEqual(
                git(workspace, "config", "--local", "--get", "user.email"),
                git(source, "config", "--local", "--get", "user.email"),
            )
            self.assertFalse((workspace / "Samantha_Agent" / "data" / "private" / "secret.txt").exists())
            self.assertFalse((workspace / "AuditCockpit56_M.txt").exists())
            self.assertEqual((source / "Samantha_Agent" / "tracked.py").read_text(), "VALUE = 1\n")
            self.assertTrue(changed["dirty"])
            self.assertEqual(changed["changes"][0]["path"], "Samantha_Agent/tracked.py")

    def test_checkpoint_commits_only_inside_isolated_clone_and_never_pushes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            manager = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=root / "cell",
                metadata_path=root / "meta.json",
            )
            manager.prepare()
            clone_file = manager.project_root / "tracked.py"
            clone_file.write_text("VALUE = 3\n", encoding="utf-8")
            before = git(manager.workspace_root, "rev-parse", "HEAD")

            checkpoint = manager.checkpoint(confirmed=True, message="WIP test")
            after = git(manager.workspace_root, "rev-parse", "HEAD")

            self.assertTrue(checkpoint["checkpoint_created"])
            self.assertNotEqual(before, after)
            self.assertFalse(checkpoint["dirty"])
            self.assertTrue(checkpoint["local_checkpoint_ahead"])
            self.assertEqual(checkpoint["workspace_relation"], "local_ahead")
            self.assertEqual(checkpoint["local_commit_count"], 1)
            self.assertFalse(checkpoint["sync_available"])
            self.assertEqual(git(manager.workspace_root, "remote"), "")
            self.assertEqual((source / "Samantha_Agent" / "tracked.py").read_text(), "VALUE = 1\n")

            review = manager.review()
            self.assertEqual(review["checkpoint_change_count"], 1)
            self.assertEqual(review["checkpoint_changes"][0]["path"], "Samantha_Agent/tracked.py")
            self.assertEqual(review["checkpoint_head"], after)
            self.assertEqual(review["checkpoint_subject"], "WIP test")

    def test_checkpoint_repairs_missing_workspace_local_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            manager = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=root / "cell",
                metadata_path=root / "meta.json",
            )
            manager.prepare()
            git(manager.workspace_root, "config", "--local", "--unset", "user.name")
            git(manager.workspace_root, "config", "--local", "--unset", "user.email")
            (manager.project_root / "tracked.py").write_text("VALUE = 4\n", encoding="utf-8")

            checkpoint = manager.checkpoint(confirmed=True, message="WIP repaired identity")

            self.assertTrue(checkpoint["checkpoint_created"])
            self.assertEqual(
                git(manager.workspace_root, "config", "--local", "--get", "user.name"),
                git(source, "config", "--local", "--get", "user.name"),
            )
            self.assertEqual(
                git(manager.workspace_root, "config", "--local", "--get", "user.email"),
                git(source, "config", "--local", "--get", "user.email"),
            )

    def test_missing_source_identity_fails_before_checkpoint_staging(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            manager = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=root / "cell",
                metadata_path=root / "meta.json",
            )
            manager.prepare()
            git(source, "config", "--local", "--unset", "user.name")
            git(source, "config", "--local", "--unset", "user.email")
            git(manager.workspace_root, "config", "--local", "--unset", "user.name")
            git(manager.workspace_root, "config", "--local", "--unset", "user.email")
            changed = manager.project_root / "tracked.py"
            changed.write_text("VALUE = 5\n", encoding="utf-8")

            with self.assertRaisesRegex(AppServerError, "checkpoint nic nepřipravil"):
                manager.checkpoint(confirmed=True, message="WIP missing identity")

            self.assertEqual(git(manager.workspace_root, "diff", "--cached", "--name-only"), "")
            self.assertEqual(changed.read_text(encoding="utf-8"), "VALUE = 5\n")

    def test_checkpoint_rejects_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            manager = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=root / "cell",
                metadata_path=root / "meta.json",
            )
            manager.prepare()
            (manager.workspace_root / ".env").write_text("TOKEN=secret\n", encoding="utf-8")

            with self.assertRaises(AppServerError):
                manager.checkpoint(confirmed=True)

            self.assertTrue((manager.workspace_root / ".env").exists())
            self.assertEqual(git(manager.workspace_root, "log", "-1", "--pretty=%s"), "Initial")

    def test_status_recognizes_local_checkpoint_with_stale_base_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            metadata_path = root / "meta.json"
            manager = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=root / "cell",
                metadata_path=metadata_path,
            )
            prepared = manager.prepare()
            (manager.project_root / "tracked.py").write_text("VALUE = 9\n", encoding="utf-8")
            checkpoint = manager.checkpoint(confirmed=True, message="WIP stale metadata")
            metadata_path.write_text(
                '{"schema_version": 1, "base_head": "stale"}\n',
                encoding="utf-8",
            )

            status = manager.status()
            review = manager.review()

            self.assertEqual(status["base_head"], "stale")
            self.assertEqual(status["workspace_relation"], "local_ahead")
            self.assertTrue(status["local_checkpoint_ahead"])
            self.assertEqual(status["local_commit_count"], 1)
            self.assertEqual(status["head"], checkpoint["checkpoint_head"])
            self.assertEqual(review["checkpoint_base_head"], prepared["head"])
            self.assertEqual(review["checkpoint_change_count"], 1)
            self.assertEqual(review["checkpoint_changes"][0]["path"], "Samantha_Agent/tracked.py")

    def test_status_recognizes_source_ahead_with_stale_base_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            metadata_path = root / "meta.json"
            manager = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=root / "cell",
                metadata_path=metadata_path,
            )
            manager.prepare()
            metadata_path.write_text(
                '{"schema_version": 1, "base_head": "stale"}\n',
                encoding="utf-8",
            )
            (source / "Samantha_Agent" / "tracked.py").write_text("VALUE = 10\n", encoding="utf-8")
            git(source, "add", "Samantha_Agent/tracked.py")
            git(source, "commit", "-m", "Source ahead with stale metadata")
            source_head = git(source, "rev-parse", "HEAD")

            status = manager.status()

            self.assertEqual(status["base_head"], "stale")
            self.assertEqual(status["workspace_relation"], "source_ahead")
            self.assertTrue(status["source_update_available"])
            self.assertTrue(status["sync_allowed"])

            synced = manager.sync_from_main(confirmed=True)
            self.assertEqual(synced["workspace_relation"], "aligned")
            self.assertEqual(synced["base_head"], source_head)

    def test_pending_integration_audit_waits_while_source_main_is_dirty(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            git(source, "add", "AuditCockpit56_M.txt")
            git(source, "commit", "-m", "Track fixture")
            manager = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=root / "cell",
                metadata_path=root / "meta.json",
            )
            manager.prepare()
            (manager.project_root / "tracked.py").write_text(
                "VALUE = 20\n", encoding="utf-8"
            )
            (source / "Samantha_Agent" / "tracked.py").write_text(
                "VALUE = 21\n", encoding="utf-8"
            )
            source_head = git(source, "rev-parse", "HEAD")
            workspace_head = git(manager.workspace_root, "rev-parse", "HEAD")

            audit = manager.review()["pending_integration_audit"]

            self.assertEqual(audit["state"], "waiting_source_clean")
            self.assertTrue(audit["pending"])
            self.assertTrue(audit["read_only"])
            self.assertFalse(audit["writes_performed"])
            self.assertGreater(audit["source_pending_change_count"], 0)
            self.assertEqual(git(source, "rev-parse", "HEAD"), source_head)
            self.assertEqual(
                git(manager.workspace_root, "rev-parse", "HEAD"),
                workspace_head,
            )

    def test_pending_integration_audit_marks_clean_aligned_base_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            git(source, "add", "AuditCockpit56_M.txt")
            git(source, "commit", "-m", "Track fixture")
            manager = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=root / "cell",
                metadata_path=root / "meta.json",
            )
            manager.prepare()
            (manager.project_root / "tracked.py").write_text(
                "VALUE = 30\n", encoding="utf-8"
            )

            audit = manager.review()["pending_integration_audit"]

            self.assertEqual(
                audit["state"],
                "ready_for_confirmed_integration",
            )
            self.assertTrue(audit["pending"])
            self.assertFalse(audit["requires_service_decision"])
            self.assertIn("neprokazuje vlastnictví", audit["message"])

    def test_pending_integration_audit_reports_path_overlap_when_main_advanced(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            git(source, "add", "AuditCockpit56_M.txt")
            git(source, "commit", "-m", "Track fixture")
            manager = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=root / "cell",
                metadata_path=root / "meta.json",
            )
            manager.prepare()
            workspace_file = manager.project_root / "tracked.py"
            workspace_file.write_text("VALUE = 40\n", encoding="utf-8")
            (source / "Samantha_Agent" / "tracked.py").write_text(
                "VALUE = 41\n", encoding="utf-8"
            )
            git(source, "add", "Samantha_Agent/tracked.py")
            git(source, "commit", "-m", "Advance same path")
            workspace_head = git(manager.workspace_root, "rev-parse", "HEAD")
            workspace_text = workspace_file.read_text(encoding="utf-8")

            audit = manager.review()["pending_integration_audit"]

            self.assertEqual(audit["state"], "source_advanced_service_decision")
            self.assertTrue(audit["source_advanced"])
            self.assertTrue(audit["requires_service_decision"])
            self.assertEqual(audit["overlap_count"], 1)
            self.assertEqual(
                audit["overlap_paths"],
                ["Samantha_Agent/tracked.py"],
            )
            self.assertEqual(git(manager.workspace_root, "rev-parse", "HEAD"), workspace_head)
            self.assertEqual(workspace_file.read_text(encoding="utf-8"), workspace_text)

    def test_pending_integration_audit_still_requires_service_without_overlap(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            git(source, "add", "AuditCockpit56_M.txt")
            git(source, "commit", "-m", "Track fixture")
            manager = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=root / "cell",
                metadata_path=root / "meta.json",
            )
            manager.prepare()
            (manager.project_root / "tracked.py").write_text(
                "VALUE = 50\n", encoding="utf-8"
            )
            index = source / "Samantha_Agent" / "memory" / "MEMORY_INDEX.md"
            index.write_text("# Index\nAdvanced\n", encoding="utf-8")
            git(source, "add", "Samantha_Agent/memory/MEMORY_INDEX.md")
            git(source, "commit", "-m", "Advance different path")

            audit = manager.review()["pending_integration_audit"]

            self.assertEqual(audit["state"], "source_advanced_service_decision")
            self.assertEqual(audit["overlap_count"], 0)
            self.assertEqual(audit["overlap_paths"], [])
            self.assertTrue(audit["requires_service_decision"])

    def test_sync_from_main_fast_forwards_clean_clone_without_remote(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            manager = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=root / "cell",
                metadata_path=root / "meta.json",
            )
            prepared = manager.prepare()
            (source / "Samantha_Agent" / "tracked.py").write_text("VALUE = 2\n", encoding="utf-8")
            git(source, "add", "Samantha_Agent/tracked.py")
            git(source, "commit", "-m", "Update tracked")
            source_head = git(source, "rev-parse", "HEAD")

            with self.assertRaises(AppServerError):
                manager.sync_from_main(confirmed=False)
            self.assertEqual(git(manager.workspace_root, "rev-parse", "HEAD"), prepared["head"])

            synced = manager.sync_from_main(confirmed=True)

            self.assertTrue(synced["synced"])
            self.assertEqual(synced["from_head"], prepared["head"])
            self.assertEqual(synced["to_head"], source_head)
            self.assertEqual(synced["head"], source_head)
            self.assertFalse(synced["dirty"])
            self.assertFalse(synced["sync_available"])
            self.assertEqual(synced["remotes"], [])
            self.assertEqual((manager.project_root / "tracked.py").read_text(), "VALUE = 2\n")
            self.assertFalse((manager.workspace_root / "AuditCockpit56_M.txt").exists())

    def test_fetch_materializes_dataless_metadata_and_retries_one_mmap_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manager = HumanAdamWorkspaceManager(
                source_repo=root / "source",
                workspace_root=root / "cell",
                metadata_path=root / "meta.json",
            )
            mmap_error = AppServerError(
                "fatal: mmap failed: Resource deadlock avoided"
            )
            with patch.object(
                manager, "_materialize_source_git_metadata", return_value=0
            ) as materialize, patch(
                "app.communication.human_adam_workspace._git_output",
                side_effect=[mmap_error, ""],
            ) as git_output:
                manager._fetch_source_main()

        self.assertEqual(materialize.call_count, 2)
        self.assertEqual(git_output.call_count, 2)

    def test_dataless_metadata_is_read_but_dataless_pack_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            manager = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=root / "cell",
                metadata_path=root / "meta.json",
            )
            pack_dir = source / ".git" / "objects" / "pack"
            metadata = pack_dir / "pack-test.rev"
            metadata.write_bytes(b"reverse-index")
            states = iter((True, False))
            with patch(
                "app.communication.human_adam_workspace._path_is_dataless",
                side_effect=lambda _path: next(states),
            ):
                materialized = manager._materialize_source_git_metadata()

            metadata.unlink()
            pack = pack_dir / "pack-test.pack"
            pack.write_bytes(b"pack")
            with patch(
                "app.communication.human_adam_workspace._path_is_dataless",
                return_value=True,
            ):
                with self.assertRaisesRegex(AppServerError, "Zachovat stažené"):
                    manager._materialize_source_git_metadata()

        self.assertEqual(materialized, 1)

    def test_equal_head_sync_repairs_stale_base_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            metadata_path = root / "meta.json"
            manager = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=root / "cell",
                metadata_path=metadata_path,
            )
            prepared = manager.prepare()
            metadata_path.write_text(
                '{"schema_version": 1, "base_head": "stale"}\n',
                encoding="utf-8",
            )

            synced = manager.sync_from_main(confirmed=True)

            self.assertFalse(synced["synced"])
            self.assertEqual(synced["base_head"], prepared["head"])
            self.assertEqual(synced["workspace_relation"], "aligned")

    def test_sync_from_main_rejects_dirty_workspace_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            manager = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=root / "cell",
                metadata_path=root / "meta.json",
            )
            manager.prepare()
            clone_file = manager.project_root / "tracked.py"
            clone_file.write_text("LOCAL WIP\n", encoding="utf-8")
            (source / "Samantha_Agent" / "tracked.py").write_text("SOURCE UPDATE\n", encoding="utf-8")
            git(source, "add", "Samantha_Agent/tracked.py")
            git(source, "commit", "-m", "Source update")

            with self.assertRaises(AppServerError):
                manager.sync_from_main(confirmed=True)

            self.assertEqual(clone_file.read_text(), "LOCAL WIP\n")
            self.assertTrue(manager.status()["dirty"])
            self.assertEqual(git(manager.workspace_root, "remote"), "")

    def test_sync_from_main_rejects_diverged_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            manager = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=root / "cell",
                metadata_path=root / "meta.json",
            )
            manager.prepare()
            clone_file = manager.project_root / "tracked.py"
            clone_file.write_text("REMOTE COMMIT\n", encoding="utf-8")
            manager.checkpoint(confirmed=True, message="Remote WIP")
            remote_head = git(manager.workspace_root, "rev-parse", "HEAD")
            (source / "Samantha_Agent" / "tracked.py").write_text("SOURCE COMMIT\n", encoding="utf-8")
            git(source, "add", "Samantha_Agent/tracked.py")
            git(source, "commit", "-m", "Source diverged")

            diverged = manager.status()
            diverged_review = manager.review()

            self.assertEqual(diverged["workspace_relation"], "diverged")
            self.assertFalse(diverged["local_checkpoint_ahead"])
            self.assertTrue(diverged["local_checkpoint_preserved"])
            self.assertEqual(diverged["local_commit_count"], 1)
            self.assertFalse(diverged["source_update_available"])
            self.assertFalse(diverged["sync_allowed"])
            self.assertIn("zachovaný lokální WIP checkpoint", diverged["message"])
            self.assertTrue(diverged_review["local_checkpoint_preserved"])
            self.assertEqual(diverged_review["checkpoint_change_count"], 1)
            self.assertEqual(diverged_review["checkpoint_changes"][0]["path"], "Samantha_Agent/tracked.py")

            with self.assertRaises(AppServerError):
                manager.sync_from_main(confirmed=True)

            self.assertEqual(git(manager.workspace_root, "rev-parse", "HEAD"), remote_head)
            self.assertEqual(clone_file.read_text(), "REMOTE COMMIT\n")
            self.assertEqual(git(manager.workspace_root, "remote"), "")

    def test_sync_from_main_rejects_incoming_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            manager = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=root / "cell",
                metadata_path=root / "meta.json",
            )
            manager.prepare()
            git(source, "update-index", "--force-remove", "Samantha_Agent/tracked.py")
            git(source, "commit", "-m", "Delete tracked")

            with self.assertRaises(AppServerError):
                manager.sync_from_main(confirmed=True)

            self.assertTrue((manager.project_root / "tracked.py").exists())
            self.assertEqual(git(manager.workspace_root, "remote"), "")

    def test_sync_from_main_allows_small_versioned_public_web_media(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            manager = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=root / "cell",
                metadata_path=root / "meta.json",
            )
            manager.prepare()
            media = source / "ColorsAndNumbers" / "web_colors_numbers" / "public-test.mp3"
            media.parent.mkdir(parents=True)
            media.write_bytes(b"public-test-audio")
            git(source, "add", "ColorsAndNumbers/web_colors_numbers/public-test.mp3")
            git(source, "commit", "-m", "Add public audio")

            synced = manager.sync_from_main(confirmed=True)

            self.assertTrue(synced["synced"])
            self.assertEqual(
                (manager.workspace_root / "ColorsAndNumbers" / "web_colors_numbers" / "public-test.mp3").read_bytes(),
                b"public-test-audio",
            )
            self.assertEqual(synced["remotes"], [])

    def test_sync_from_main_still_rejects_media_outside_public_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            manager = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=root / "cell",
                metadata_path=root / "meta.json",
            )
            prepared = manager.prepare()
            media = source / "Samantha_Agent" / "public-test.mp3"
            media.write_bytes(b"not-allowlisted")
            git(source, "add", "Samantha_Agent/public-test.mp3")
            git(source, "commit", "-m", "Add blocked audio")

            with self.assertRaises(AppServerError):
                manager.sync_from_main(confirmed=True)

            self.assertEqual(git(manager.workspace_root, "rev-parse", "HEAD"), prepared["head"])
            self.assertFalse((manager.workspace_root / "Samantha_Agent" / "public-test.mp3").exists())
            self.assertEqual(git(manager.workspace_root, "remote"), "")

    def test_prepare_never_overwrites_unknown_existing_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            workspace = root / "cell"
            workspace.mkdir()
            sentinel = workspace / "keep.txt"
            sentinel.write_text("keep\n", encoding="utf-8")
            manager = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=workspace,
                metadata_path=root / "meta.json",
            )

            with self.assertRaises(AppServerError):
                manager.prepare()

            self.assertEqual(sentinel.read_text(), "keep\n")


if __name__ == "__main__":
    unittest.main()
