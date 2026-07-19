from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from app.development_branch_lifecycle import (
    DevelopmentBranchAuditor,
    development_branch_audit_action,
)


class DevelopmentBranchLifecycleTests(unittest.TestCase):
    def git(self, repo: Path, *args: str) -> str:
        completed = subprocess.run(
            ["/usr/bin/git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            self.fail((completed.stderr or completed.stdout).strip())
        return completed.stdout.strip()

    def make_repo(self, root: Path) -> Path:
        repo = root / "repo"
        repo.mkdir()
        self.git(repo, "init", "-b", "main")
        self.git(repo, "config", "user.name", "Samantha Test")
        self.git(repo, "config", "user.email", "samantha@example.invalid")
        (repo / "base.txt").write_text("base\n", encoding="utf-8")
        self.git(repo, "add", "base.txt")
        self.git(repo, "commit", "-m", "Base")
        return repo

    def auditor(self, repo: Path, *, archive_text: str = "") -> DevelopmentBranchAuditor:
        archive = repo.parent / "archive.md"
        archive.write_text(archive_text, encoding="utf-8")
        return DevelopmentBranchAuditor(repo_root=repo, archive_path=archive)

    @staticmethod
    def branch(payload: dict[str, object], name: str) -> dict[str, object]:
        return next(
            item
            for item in payload["branches"]  # type: ignore[index,union-attr]
            if item["name"] == name
        )

    def test_main_only_is_empty_read_only_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.make_repo(Path(temp_dir))
            before = self.git(repo, "show-ref")
            payload = self.auditor(repo).audit()
            after = self.git(repo, "show-ref")

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["mode"], "read_only")
        self.assertEqual(payload["branch_count"], 0)
        self.assertFalse(payload["network_refreshed"])
        self.assertEqual(before, after)

    def test_merged_branch_is_cleanup_candidate_when_not_checked_out(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.make_repo(Path(temp_dir))
            self.git(repo, "checkout", "-b", "wip/merged")
            (repo / "merged.txt").write_text("done\n", encoding="utf-8")
            self.git(repo, "add", "merged.txt")
            self.git(repo, "commit", "-m", "Merged change")
            self.git(repo, "checkout", "main")
            self.git(repo, "merge", "--ff-only", "wip/merged")
            item = self.branch(self.auditor(repo).audit(), "wip/merged")

        self.assertEqual(item["classification"], "merged")
        self.assertTrue(item["cleanup_candidate"])
        self.assertFalse(item["checked_out"])

    def test_cherry_picked_branch_is_patch_equivalent_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.make_repo(Path(temp_dir))
            self.git(repo, "checkout", "-b", "wip/cherry")
            (repo / "feature.txt").write_text("feature\n", encoding="utf-8")
            self.git(repo, "add", "feature.txt")
            self.git(repo, "commit", "-m", "Feature")
            feature_head = self.git(repo, "rev-parse", "HEAD")
            self.git(repo, "checkout", "main")
            (repo / "main.txt").write_text("main\n", encoding="utf-8")
            self.git(repo, "add", "main.txt")
            self.git(repo, "commit", "-m", "Main advance")
            self.git(repo, "cherry-pick", feature_head)
            item = self.branch(self.auditor(repo).audit(), "wip/cherry")

        self.assertEqual(item["classification"], "patch_equivalent")
        self.assertTrue(item["cleanup_candidate"])
        self.assertEqual(item["unique_patch_count"], 0)
        self.assertEqual(item["integrated_patch_count"], 1)

    def test_unique_commit_requires_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.make_repo(Path(temp_dir))
            self.git(repo, "checkout", "-b", "wip/unique")
            (repo / "unique.txt").write_text("unique\n", encoding="utf-8")
            self.git(repo, "add", "unique.txt")
            self.git(repo, "commit", "-m", "Unique")
            self.git(repo, "checkout", "main")
            item = self.branch(self.auditor(repo).audit(), "wip/unique")

        self.assertEqual(item["classification"], "needs_review")
        self.assertFalse(item["cleanup_candidate"])
        self.assertEqual(item["unique_patch_count"], 1)

    def test_checked_out_dirty_worktree_is_never_cleanup_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo = self.make_repo(root)
            worktree = root / "worktree"
            self.git(repo, "worktree", "add", "-b", "wip/active", str(worktree), "main")
            (worktree / "draft.txt").write_text("draft\n", encoding="utf-8")
            payload = self.auditor(repo).audit()
            item = self.branch(payload, "wip/active")
            serialized = json.dumps(payload, ensure_ascii=False)

        self.assertEqual(item["classification"], "active_dirty_worktree")
        self.assertFalse(item["cleanup_candidate"])
        self.assertTrue(item["checked_out"])
        self.assertEqual(item["worktree_change_count"], 1)
        self.assertNotIn(str(worktree), serialized)

    def test_active_archive_acknowledges_but_does_not_recommend_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.make_repo(Path(temp_dir))
            self.git(repo, "checkout", "-b", "wip/archived")
            (repo / "archive.txt").write_text("archive\n", encoding="utf-8")
            self.git(repo, "add", "archive.txt")
            self.git(repo, "commit", "-m", "Archived")
            self.git(repo, "checkout", "main")
            archive_text = """# Git branch archive

## Aktivni archivovane neintegrovane vetve

- `wip/archived` - vědomě zachovat

## Smazane vetve

- `wip/deleted`
"""
            item = self.branch(
                self.auditor(repo, archive_text=archive_text).audit(),
                "wip/archived",
            )

        self.assertEqual(item["classification"], "archived")
        self.assertTrue(item["archived"])
        self.assertFalse(item["cleanup_candidate"])

    def test_action_fails_closed_outside_git_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = development_branch_audit_action(
                repo_root=root,
                archive_path=root / "missing.md",
            )

        self.assertFalse(payload["ok"])
        self.assertEqual(payload["mode"], "read_only")
        self.assertEqual(payload["branches"], [])


if __name__ == "__main__":
    unittest.main()
