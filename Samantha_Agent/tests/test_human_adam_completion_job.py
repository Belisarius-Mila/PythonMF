from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from app.communication.human_adam_completion_job import (
    COMPLETED,
    RUNNING,
    HumanAdamCompletionJobStore,
    completion_idempotency_key,
    workspace_fingerprint,
)


class HumanAdamCompletionJobTests(unittest.TestCase):
    def test_job_survives_reload_and_reaches_terminal_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "completion-job.json"
            store = HumanAdamCompletionJobStore(path)
            job = store.create(
                workstream_id="project-test",
                profile_id="human_adam",
                client_message_id="completion-job-001",
                base_head="a" * 40,
                workspace_fingerprint="b" * 64,
                idempotency_key="c" * 64,
                commit_message="Complete test step",
                summary="Testovací krok je hotový",
                next_step="Pokračovat",
                decision="",
                proposed_next_steps=(),
                visible_answer="Hotovo.",
            )
            running = store.update(job, state=RUNNING, attempts=1)

            reloaded = HumanAdamCompletionJobStore(path).load()
            self.assertEqual(reloaded, running)
            completed = store.update(
                running,
                state=COMPLETED,
                checkpoint_head="d" * 40,
            )

            self.assertEqual(completed.state, COMPLETED)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_worker_lease_allows_only_one_owner(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = HumanAdamCompletionJobStore(Path(temp_dir) / "job.json")
            first = store.acquire_worker_lease()
            self.assertIsNotNone(first)
            try:
                self.assertIsNone(store.acquire_worker_lease())
            finally:
                assert first is not None
                first.close()
            second = store.acquire_worker_lease()
            self.assertIsNotNone(second)
            assert second is not None
            second.close()

    def test_workspace_fingerprint_changes_with_untracked_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(
                ["git", "-C", str(root), "config", "user.name", "Test"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(root), "config", "user.email", "test@example.invalid"],
                check=True,
            )
            tracked = root / "tracked.txt"
            tracked.write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "base"], check=True)
            (root / "new.txt").write_text("one\n", encoding="utf-8")
            first = workspace_fingerprint(root)
            (root / "new.txt").write_text("two\n", encoding="utf-8")
            second = workspace_fingerprint(root)

            self.assertNotEqual(first, second)

    def test_idempotency_key_is_deterministic_and_bound_to_fingerprint(self) -> None:
        first = completion_idempotency_key(
            workstream_id="project-test",
            client_message_id="completion-job-001",
            base_head="a" * 40,
            workspace_fingerprint="b" * 64,
        )
        repeated = completion_idempotency_key(
            workstream_id="project-test",
            client_message_id="completion-job-001",
            base_head="a" * 40,
            workspace_fingerprint="b" * 64,
        )
        changed = completion_idempotency_key(
            workstream_id="project-test",
            client_message_id="completion-job-001",
            base_head="a" * 40,
            workspace_fingerprint="c" * 64,
        )

        self.assertEqual(first, repeated)
        self.assertNotEqual(first, changed)
        self.assertEqual(len(first), 64)


if __name__ == "__main__":
    unittest.main()
