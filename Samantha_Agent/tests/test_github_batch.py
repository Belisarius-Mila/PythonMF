from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from app.communication.github_batch import (
    GITHUB_BATCH_CONFIRMATION,
    GitHubBatchError,
    audit_github_batch,
    push_github_batch,
)
from app.communication.checkpoint_quality_gate import DEFAULT_GATE_TIMEOUT_SECONDS
from tests.test_human_adam_takeover import prepare_with_origin
from tests.test_human_adam_workspace import git


def successful_gate(command, **kwargs):
    if kwargs.get("timeout") != DEFAULT_GATE_TIMEOUT_SECONDS:
        raise AssertionError("GitHub batch must keep the full-gate timeout reserve")
    return subprocess.CompletedProcess(
        command,
        0,
        stdout="Ran 31 tests in 0.100s\nOK\nCockpit quality gate: OK\n",
        stderr="",
    )


class GitHubBatchTests(unittest.TestCase):
    def test_audit_lists_accumulated_commits_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source, _manager = prepare_with_origin(Path(temp_dir))
            (source / "AuditCockpit56_M.txt").unlink()
            origin_head = git(source, "rev-parse", "origin/main")
            for number in (1, 2):
                path = source / "Samantha_Agent" / f"batch_{number}.py"
                path.write_text(f"VALUE = {number}\n", encoding="utf-8")
                git(source, "add", str(path.relative_to(source)))
                git(source, "commit", "-m", f"Local batch {number}")

            result = audit_github_batch(source_repo=source)
            remote_head = git(source, "rev-parse", "origin/main")

        self.assertTrue(result["ready"])
        self.assertTrue(result["pending"])
        self.assertEqual(result["state"], "ready")
        self.assertEqual(result["commit_count"], 2)
        self.assertEqual(result["change_count"], 2)
        self.assertEqual(result["origin_head"], origin_head)
        self.assertEqual(remote_head, origin_head)
        self.assertEqual(result["confirmation_text"], GITHUB_BATCH_CONFIRMATION)

    def test_confirmed_batch_runs_one_gate_and_pushes_exact_head(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, manager = prepare_with_origin(root)
            (source / "AuditCockpit56_M.txt").unlink()
            path = source / "Samantha_Agent" / "batch.py"
            path.write_text("VALUE = 3\n", encoding="utf-8")
            git(source, "add", str(path.relative_to(source)))
            git(source, "commit", "-m", "Local batch")
            manager.sync_from_main(confirmed=True)
            gate_script = (
                manager.project_root / "scripts" / "cockpit_quality_gate.py"
            )
            gate_script.parent.mkdir(parents=True, exist_ok=True)
            gate_script.write_text("raise SystemExit(0)\n", encoding="utf-8")
            audit = audit_github_batch(source_repo=source)

            with self.assertRaises(GitHubBatchError):
                push_github_batch(
                    workspace=manager,
                    expected_origin_head=audit["origin_head"],
                    expected_local_head=audit["local_head"],
                    confirmation="ano",
                    gate_runner=successful_gate,
                    gate_log_path=root / "gate.log",
                )
            result = push_github_batch(
                workspace=manager,
                expected_origin_head=audit["origin_head"],
                expected_local_head=audit["local_head"],
                confirmation=GITHUB_BATCH_CONFIRMATION,
                gate_runner=successful_gate,
                gate_log_path=root / "gate.log",
            )

            source_head = git(source, "rev-parse", "HEAD")
            origin_head = git(source, "rev-parse", "origin/main")

        self.assertTrue(result["pushed"])
        self.assertEqual(result["state"], "pushed")
        self.assertEqual(result["gate"]["test_count"], 31)
        self.assertEqual(source_head, origin_head)

    def test_divergence_is_read_only_and_not_pushable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, _manager = prepare_with_origin(root)
            (source / "AuditCockpit56_M.txt").unlink()
            local = source / "Samantha_Agent" / "local.py"
            local.write_text("LOCAL = True\n", encoding="utf-8")
            git(source, "add", str(local.relative_to(source)))
            git(source, "commit", "-m", "Local work")

            competitor = root / "competitor"
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
            git(competitor, "commit", "-m", "Remote work")
            git(competitor, "push", "origin", "main")

            result = audit_github_batch(source_repo=source)

        self.assertEqual(result["state"], "diverged")
        self.assertFalse(result["ready"])
        self.assertFalse(result["pending"])

    def test_daytime_status_uses_known_origin_without_fetching_new_remote_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, _manager = prepare_with_origin(root)
            (source / "AuditCockpit56_M.txt").unlink()
            local = source / "Samantha_Agent" / "local.py"
            local.write_text("LOCAL = True\n", encoding="utf-8")
            git(source, "add", str(local.relative_to(source)))
            git(source, "commit", "-m", "Local daytime work")

            competitor = root / "competitor-known-ref"
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
            git(competitor, "commit", "-m", "Remote work")
            git(competitor, "push", "origin", "main")

            known_before = git(source, "rev-parse", "origin/main")
            result = audit_github_batch(
                source_repo=source,
                refresh_remote=False,
            )
            known_after = git(source, "rev-parse", "origin/main")

        self.assertEqual(result["state"], "ready")
        self.assertEqual(result["commit_count"], 1)
        self.assertEqual(known_after, known_before)

    def test_private_or_key_paths_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source, _manager = prepare_with_origin(Path(temp_dir))
            (source / "AuditCockpit56_M.txt").unlink()
            secret = source / "Samantha_Agent" / "data" / "private" / "secret.txt"
            secret.parent.mkdir(parents=True, exist_ok=True)
            secret.write_text("redacted\n", encoding="utf-8")
            git(source, "add", "-f", str(secret.relative_to(source)))
            git(source, "commit", "-m", "Unsafe local commit")

            with self.assertRaisesRegex(GitHubBatchError, "blokovanou"):
                audit_github_batch(source_repo=source)


if __name__ == "__main__":
    unittest.main()
