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
