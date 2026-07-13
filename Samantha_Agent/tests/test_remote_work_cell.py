from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from app.codex_appserver import AppServerError
from app.remote_work_cell import RemoteWorkspaceManager


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
    git(source, "config", "user.name", "Remote Cell Test")
    git(source, "config", "user.email", "remote-cell@example.invalid")
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


class RemoteWorkspaceManagerTests(unittest.TestCase):
    def test_prepare_creates_independent_main_clone_without_private_untracked_or_remote(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            workspace = root / "private" / "workspace"
            manager = RemoteWorkspaceManager(
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
            self.assertFalse((workspace / "Samantha_Agent" / "data" / "private" / "secret.txt").exists())
            self.assertFalse((workspace / "AuditCockpit56_M.txt").exists())
            self.assertEqual((source / "Samantha_Agent" / "tracked.py").read_text(), "VALUE = 1\n")
            self.assertTrue(changed["dirty"])
            self.assertEqual(changed["changes"][0]["path"], "Samantha_Agent/tracked.py")

    def test_checkpoint_commits_only_inside_isolated_clone_and_never_pushes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            manager = RemoteWorkspaceManager(
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
            self.assertEqual(git(manager.workspace_root, "remote"), "")
            self.assertEqual((source / "Samantha_Agent" / "tracked.py").read_text(), "VALUE = 1\n")

    def test_checkpoint_rejects_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            manager = RemoteWorkspaceManager(
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

    def test_sync_from_main_fast_forwards_clean_clone_without_remote(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            manager = RemoteWorkspaceManager(
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

    def test_sync_from_main_rejects_dirty_workspace_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            manager = RemoteWorkspaceManager(
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
            manager = RemoteWorkspaceManager(
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

            with self.assertRaises(AppServerError):
                manager.sync_from_main(confirmed=True)

            self.assertEqual(git(manager.workspace_root, "rev-parse", "HEAD"), remote_head)
            self.assertEqual(clone_file.read_text(), "REMOTE COMMIT\n")
            self.assertEqual(git(manager.workspace_root, "remote"), "")

    def test_sync_from_main_rejects_incoming_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            manager = RemoteWorkspaceManager(
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

    def test_prepare_never_overwrites_unknown_existing_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = make_source(root)
            workspace = root / "cell"
            workspace.mkdir()
            sentinel = workspace / "keep.txt"
            sentinel.write_text("keep\n", encoding="utf-8")
            manager = RemoteWorkspaceManager(
                source_repo=source,
                workspace_root=workspace,
                metadata_path=root / "meta.json",
            )

            with self.assertRaises(AppServerError):
                manager.prepare()

            self.assertEqual(sentinel.read_text(), "keep\n")


if __name__ == "__main__":
    unittest.main()
