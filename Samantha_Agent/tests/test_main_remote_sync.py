from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from app.communication.main_remote_sync import (
    MainRemoteSyncError,
    apply_main_remote_sync,
    audit_main_remote_sync,
)
from tests.test_human_adam_workspace import git, make_source


def prepare_clean_origin(root: Path):
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
    (source / "AuditCockpit56_M.txt").unlink()
    return source, None


def advance_origin(root: Path, *, filename: str, value: str) -> str:
    competitor = root / f"competitor-{filename.replace('.', '-')}"
    subprocess.run(
        ["/usr/bin/git", "clone", str(root / "origin.git"), str(competitor)],
        capture_output=True,
        text=True,
        check=True,
    )
    git(competitor, "config", "user.name", "Remote Writer")
    git(competitor, "config", "user.email", "remote@example.invalid")
    (competitor / filename).write_text(value, encoding="utf-8")
    git(competitor, "add", filename)
    git(competitor, "commit", "-m", f"Advance {filename}")
    git(competitor, "push", "origin", "main")
    return git(competitor, "rev-parse", "HEAD")


class MainRemoteSyncTests(unittest.TestCase):
    def test_audit_reports_aligned_without_changing_main(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source, _workspace = prepare_clean_origin(Path(temp_dir))
            head = git(source, "rev-parse", "HEAD")

            result = audit_main_remote_sync(source_repo=source)
            final_head = git(source, "rev-parse", "HEAD")

        self.assertTrue(result["ok"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["writes_performed"])
        self.assertEqual(result["state"], "aligned")
        self.assertFalse(result["can_fast_forward"])
        self.assertEqual(result["local_head"], head)
        self.assertEqual(final_head, head)
        self.assertFalse(result["changes_truncated"])

    def test_audit_offers_exact_fast_forward_and_path_preview(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, _workspace = prepare_clean_origin(root)
            local_head = git(source, "rev-parse", "HEAD")
            origin_head = advance_origin(
                root,
                filename="remote-update.txt",
                value="remote\n",
            )

            result = audit_main_remote_sync(source_repo=source)
            final_head = git(source, "rev-parse", "HEAD")

        self.assertEqual(result["state"], "fast_forward_available")
        self.assertTrue(result["can_fast_forward"])
        self.assertEqual(result["local_head"], local_head)
        self.assertEqual(result["origin_head"], origin_head)
        self.assertEqual(result["commit_count"], 1)
        self.assertEqual(
            result["changes"],
            [{"status": "A", "path": "remote-update.txt"}],
        )
        self.assertEqual(final_head, local_head)
        self.assertFalse(result["will_merge"])
        self.assertFalse(result["will_rebase"])
        self.assertFalse(result["will_rewrite_history"])

    def test_apply_requires_confirmation_and_exact_audited_heads(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, _workspace = prepare_clean_origin(root)
            origin_head = advance_origin(
                root,
                filename="remote-update.txt",
                value="remote\n",
            )
            audit = audit_main_remote_sync(source_repo=source)

            with self.assertRaisesRegex(MainRemoteSyncError, "potvrzení"):
                apply_main_remote_sync(
                    source_repo=source,
                    expected_local_head=audit["local_head"],
                    expected_origin_head=origin_head,
                    confirmed=False,
                )
            with self.assertRaisesRegex(MainRemoteSyncError, "od auditu změnil"):
                apply_main_remote_sync(
                    source_repo=source,
                    expected_local_head="0" * 40,
                    expected_origin_head=origin_head,
                    confirmed=True,
                )

    def test_apply_fast_forwards_only_to_the_audited_remote_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, _workspace = prepare_clean_origin(root)
            origin_head = advance_origin(
                root,
                filename="remote-update.txt",
                value="remote\n",
            )
            audit = audit_main_remote_sync(source_repo=source)

            result = apply_main_remote_sync(
                source_repo=source,
                expected_local_head=audit["local_head"],
                expected_origin_head=audit["origin_head"],
                confirmed=True,
            )
            final_head = git(source, "rev-parse", "HEAD")
            status = git(source, "status", "--porcelain=v1")

        self.assertTrue(result["main_fast_forwarded"])
        self.assertEqual(result["state"], "main_fast_forwarded")
        self.assertEqual(final_head, origin_head)
        self.assertEqual(status, "")
        self.assertFalse(result["will_merge"])
        self.assertFalse(result["will_rebase"])
        self.assertFalse(result["will_rewrite_history"])

    def test_apply_rejects_remote_race_before_local_main_moves(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, _workspace = prepare_clean_origin(root)
            first_origin = advance_origin(
                root,
                filename="first.txt",
                value="first\n",
            )
            audit = audit_main_remote_sync(source_repo=source)
            local_head = audit["local_head"]
            self.assertEqual(audit["origin_head"], first_origin)
            advance_origin(
                root,
                filename="second.txt",
                value="second\n",
            )

            with self.assertRaisesRegex(MainRemoteSyncError, "od auditu změnil"):
                apply_main_remote_sync(
                    source_repo=source,
                    expected_local_head=local_head,
                    expected_origin_head=first_origin,
                    confirmed=True,
                )
            final_head = git(source, "rev-parse", "HEAD")

        self.assertEqual(final_head, local_head)

    def test_audit_blocks_dirty_local_main_and_does_not_offer_local_ahead(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source, _workspace = prepare_clean_origin(Path(temp_dir))
            (source / "local-dirty.txt").write_text("dirty\n", encoding="utf-8")
            with self.assertRaisesRegex(MainRemoteSyncError, "pracovní změny"):
                audit_main_remote_sync(source_repo=source)

        with tempfile.TemporaryDirectory() as temp_dir:
            source, _workspace = prepare_clean_origin(Path(temp_dir))
            (source / "Samantha_Agent" / "tracked.py").write_text(
                "VALUE = 5\n",
                encoding="utf-8",
            )
            git(source, "add", "Samantha_Agent/tracked.py")
            git(source, "commit", "-m", "Local only")

            result = audit_main_remote_sync(source_repo=source)

        self.assertEqual(result["state"], "local_ahead")
        self.assertFalse(result["can_fast_forward"])
        self.assertFalse(result["changes_truncated"])

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, _workspace = prepare_clean_origin(root)
            (source / "Samantha_Agent" / "tracked.py").write_text(
                "VALUE = 6\n",
                encoding="utf-8",
            )
            git(source, "add", "Samantha_Agent/tracked.py")
            git(source, "commit", "-m", "Local divergent commit")
            advance_origin(
                root,
                filename="remote-divergent.txt",
                value="remote\n",
            )

            result = audit_main_remote_sync(source_repo=source)

        self.assertEqual(result["state"], "diverged")
        self.assertFalse(result["can_fast_forward"])
        self.assertFalse(result["changes_truncated"])


if __name__ == "__main__":
    unittest.main()
