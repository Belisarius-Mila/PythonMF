from __future__ import annotations

import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from app.communication.human_adam_workspace import HumanAdamWorkspaceManager
from app.communication.simple_main_checkpoint import (
    SimpleMainCheckpointError,
    SimpleMainCheckpointRequest,
    complete_simple_main_checkpoint,
    _format_timestamp,
)
from scripts.human_adam_takeover import TakeoverError
from tests.test_human_adam_workspace import git, make_source


def passing_gate_runner(*args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=args[0] if args else [],
        returncode=0,
        stdout="Ran 12 tests in 1.250s\n\nOK\nCockpit quality gate: OK\n",
        stderr="",
    )


def failing_gate_runner(*args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=args[0] if args else [],
        returncode=1,
        stdout="Ran 12 tests in 1.250s\n\nFAILED (failures=1)\n",
        stderr="",
    )


def prepare_environment(
    root: Path,
    *,
    workspace_name: str = "cell",
) -> tuple[Path, HumanAdamWorkspaceManager]:
    source = make_source(root)
    (source / "AuditCockpit56_M.txt").unlink()
    project = source / "Samantha_Agent"
    (project / "scripts").mkdir()
    (project / "scripts" / "cockpit_quality_gate.py").write_text(
        "print('test gate')\n",
        encoding="utf-8",
    )
    (project / "memory" / "handoffs").mkdir()
    (project / "memory" / "tvbcp").mkdir()
    (project / "memory" / "handoffs" / "demo.md").write_text(
        "Nazev: Demo\nDalsi krok: puvodni\n",
        encoding="utf-8",
    )
    (project / "memory" / "tvbcp" / "demo.txt").write_text(
        "# Demo TVBCP\n",
        encoding="utf-8",
    )
    git(source, "add", "Samantha_Agent/scripts/cockpit_quality_gate.py")
    git(source, "add", "Samantha_Agent/memory/handoffs/demo.md")
    git(source, "add", "Samantha_Agent/memory/tvbcp/demo.txt")
    git(source, "commit", "-m", "Add workstream memory")
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
        workspace_root=root / workspace_name,
        metadata_path=root / f"{workspace_name}-meta.json",
    )
    manager.prepare()
    return source, manager


def checkpoint_request(**overrides: str) -> SimpleMainCheckpointRequest:
    values = {
        "workstream_id": "layer-human-adam-development",
        "commit_message": "Complete one simple step",
        "summary": "Jednoduchý backend dokončil jeden krok",
        "next_step": "Ručně ověřit výsledek",
        "handoff_relative_path": "memory/handoffs/demo.md",
        "tvbcp_relative_path": "memory/tvbcp/demo.txt",
    }
    values.update(overrides)
    return SimpleMainCheckpointRequest(**values)


def fixed_now() -> datetime:
    return datetime(2026, 7, 20, 7, 0, tzinfo=ZoneInfo("Europe/Prague"))


class SimpleMainCheckpointTests(unittest.TestCase):
    def test_timestamp_is_always_rendered_in_canonical_prague_time(self) -> None:
        github_runner_time = datetime(2026, 7, 20, 5, 0, tzinfo=timezone.utc)

        self.assertEqual(
            _format_timestamp(github_runner_time),
            "2026-07-20 07:00 CEST",
        )

    def test_completes_one_commit_on_main_without_creating_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, manager = prepare_environment(root)
            original_head = git(source, "rev-parse", "HEAD")
            source_branches_before = git(source, "branch", "--format=%(refname:short)")
            workspace_branches_before = git(
                manager.workspace_root,
                "branch",
                "--format=%(refname:short)",
            )
            (manager.project_root / "tracked.py").write_text("VALUE = 2\n", encoding="utf-8")
            progress: list[tuple[str, str]] = []

            result = complete_simple_main_checkpoint(
                workspace=manager,
                request=checkpoint_request(),
                confirmed=True,
                gate_runner=passing_gate_runner,
                gate_log_path=root / "gate.log",
                now_factory=fixed_now,
                progress_callback=lambda stage, outcome: progress.append((stage, outcome)),
            )

            source_head = git(source, "rev-parse", "HEAD")
            origin_head = git(source, "rev-parse", "origin/main")
            workspace_head = git(manager.workspace_root, "rev-parse", "HEAD")
            handoff = (manager.project_root / "memory" / "handoffs" / "demo.md").read_text(
                encoding="utf-8"
            )
            tvbcp = (manager.project_root / "memory" / "tvbcp" / "demo.txt").read_text(
                encoding="utf-8"
            )
            source_subject = git(source, "log", "-1", "--format=%s")
            source_branches_after = git(source, "branch", "--format=%(refname:short)")
            workspace_branches_after = git(
                manager.workspace_root,
                "branch",
                "--format=%(refname:short)",
            )
            source_clean = git(source, "status", "--porcelain")
            workspace_clean = git(manager.workspace_root, "status", "--porcelain")

        self.assertTrue(result["ok"])
        self.assertEqual(result["operation"], "simple_main_checkpoint")
        self.assertTrue(result["pushed"])
        self.assertTrue(result["source_aligned"])
        self.assertTrue(result["workspace_aligned"])
        self.assertFalse(result["branches_created"])
        self.assertNotEqual(source_head, original_head)
        self.assertEqual(source_head, origin_head)
        self.assertEqual(source_head, workspace_head)
        self.assertEqual(source_subject, "Complete one simple step")
        self.assertEqual(source_branches_before, "main")
        self.assertEqual(workspace_branches_before, "main")
        self.assertEqual(source_branches_after, "main")
        self.assertEqual(workspace_branches_after, "main")
        self.assertEqual(source_clean, "")
        self.assertEqual(workspace_clean, "")
        self.assertIn("Automatický checkpoint 2026-07-20 07:00 CEST", handoff)
        self.assertIn("plná Cockpit brána: 12 testů", handoff)
        self.assertIn("### 2026-07-20 07:00 CEST", tvbcp)
        self.assertIn("Jednoduchý backend dokončil jeden krok", tvbcp)
        self.assertEqual(progress[0:4], [
            ("preflight", "running"),
            ("preflight", "passed"),
            ("gate", "running"),
            ("gate", "passed"),
        ])
        self.assertIn(("push", "passed"), progress)
        self.assertIn(("workspace_alignment", "passed"), progress)

    def test_confirmation_is_required_before_any_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, manager = prepare_environment(root)
            original_head = git(source, "rev-parse", "HEAD")
            handoff_path = manager.project_root / "memory" / "handoffs" / "demo.md"
            original_handoff = handoff_path.read_text(encoding="utf-8")
            (manager.project_root / "tracked.py").write_text("VALUE = 3\n", encoding="utf-8")

            with self.assertRaisesRegex(SimpleMainCheckpointError, "výslovné potvrzení"):
                complete_simple_main_checkpoint(
                    workspace=manager,
                    request=checkpoint_request(),
                    confirmed=False,
                    gate_runner=passing_gate_runner,
                    gate_log_path=root / "gate.log",
                )

            source_head_after = git(source, "rev-parse", "HEAD")
            handoff_after = handoff_path.read_text(encoding="utf-8")
            workspace_dirty = manager.status()["dirty"]

        self.assertEqual(source_head_after, original_head)
        self.assertEqual(handoff_after, original_handoff)
        self.assertTrue(workspace_dirty)

    def test_gate_failure_keeps_original_dirty_work_and_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, manager = prepare_environment(root)
            original_head = git(source, "rev-parse", "HEAD")
            handoff_path = manager.project_root / "memory" / "handoffs" / "demo.md"
            tvbcp_path = manager.project_root / "memory" / "tvbcp" / "demo.txt"
            original_handoff = handoff_path.read_text(encoding="utf-8")
            original_tvbcp = tvbcp_path.read_text(encoding="utf-8")
            (manager.project_root / "tracked.py").write_text("VALUE = 4\n", encoding="utf-8")

            with self.assertRaisesRegex(SimpleMainCheckpointError, "brána"):
                complete_simple_main_checkpoint(
                    workspace=manager,
                    request=checkpoint_request(),
                    confirmed=True,
                    gate_runner=failing_gate_runner,
                    gate_log_path=root / "gate.log",
                )

            source_head_after = git(source, "rev-parse", "HEAD")
            workspace_head_after = git(manager.workspace_root, "rev-parse", "HEAD")
            handoff_after = handoff_path.read_text(encoding="utf-8")
            tvbcp_after = tvbcp_path.read_text(encoding="utf-8")
            workspace_dirty = manager.status()["dirty"]

        self.assertEqual(source_head_after, original_head)
        self.assertEqual(workspace_head_after, original_head)
        self.assertEqual(handoff_after, original_handoff)
        self.assertEqual(tvbcp_after, original_tvbcp)
        self.assertTrue(workspace_dirty)

    def test_dirty_source_and_dirty_peer_are_stateless_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, manager = prepare_environment(root)
            (manager.project_root / "tracked.py").write_text("VALUE = 5\n", encoding="utf-8")
            (source / "Samantha_Agent" / "tracked.py").write_text(
                "SOURCE DIRTY\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SimpleMainCheckpointError, "Zdrojový main není čistý"):
                complete_simple_main_checkpoint(
                    workspace=manager,
                    request=checkpoint_request(),
                    confirmed=True,
                    gate_runner=passing_gate_runner,
                    gate_log_path=root / "gate.log",
                )

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _source, manager = prepare_environment(root)
            peer = HumanAdamWorkspaceManager(
                source_repo=manager.source_repo,
                workspace_root=root / "peer",
                metadata_path=root / "peer-meta.json",
            )
            peer.prepare()
            (manager.project_root / "tracked.py").write_text("VALUE = 6\n", encoding="utf-8")
            (peer.project_root / "tracked.py").write_text("PEER DIRTY\n", encoding="utf-8")
            with self.assertRaisesRegex(SimpleMainCheckpointError, "Jiný profil"):
                complete_simple_main_checkpoint(
                    workspace=manager,
                    peer_workspaces=(peer,),
                    request=checkpoint_request(),
                    confirmed=True,
                    gate_runner=passing_gate_runner,
                    gate_log_path=root / "gate.log",
                )

    def test_deletion_and_unsafe_memory_request_fail_before_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, manager = prepare_environment(root)
            original_head = git(source, "rev-parse", "HEAD")
            (manager.project_root / "tracked.py").unlink()
            with self.assertRaisesRegex(SimpleMainCheckpointError, "nepodporuje mazání"):
                complete_simple_main_checkpoint(
                    workspace=manager,
                    request=checkpoint_request(),
                    confirmed=True,
                    gate_runner=passing_gate_runner,
                    gate_log_path=root / "gate.log",
                )
            self.assertEqual(git(source, "rev-parse", "HEAD"), original_head)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _source, manager = prepare_environment(root)
            (manager.project_root / "tracked.py").write_text("VALUE = 7\n", encoding="utf-8")
            with self.assertRaisesRegex(SimpleMainCheckpointError, "povolenou relativní cestu"):
                complete_simple_main_checkpoint(
                    workspace=manager,
                    request=checkpoint_request(handoff_relative_path="../outside.md"),
                    confirmed=True,
                    gate_runner=passing_gate_runner,
                    gate_log_path=root / "gate.log",
                )
            with self.assertRaisesRegex(SimpleMainCheckpointError, "heslo, token"):
                complete_simple_main_checkpoint(
                    workspace=manager,
                    request=checkpoint_request(summary="token=secret-value"),
                    confirmed=True,
                    gate_runner=passing_gate_runner,
                    gate_log_path=root / "gate.log",
                )

    def test_clean_peer_may_wait_behind_main_without_blocking_active_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, manager = prepare_environment(root)
            peer = HumanAdamWorkspaceManager(
                source_repo=source,
                workspace_root=root / "peer",
                metadata_path=root / "peer-meta.json",
            )
            peer.prepare()
            (source / "Samantha_Agent" / "new_memory.md").write_text(
                "new source memory\n",
                encoding="utf-8",
            )
            git(source, "add", "Samantha_Agent/new_memory.md")
            git(source, "commit", "-m", "Advance source main")
            git(source, "push", "origin", "main")
            manager.sync_from_main(confirmed=True)
            self.assertEqual(peer.status()["workspace_relation"], "source_ahead")
            (manager.project_root / "tracked.py").write_text("VALUE = 9\n", encoding="utf-8")

            result = complete_simple_main_checkpoint(
                workspace=manager,
                peer_workspaces=(peer,),
                request=checkpoint_request(),
                confirmed=True,
                gate_runner=passing_gate_runner,
                gate_log_path=root / "gate.log",
                now_factory=fixed_now,
            )

            peer_status = peer.status()

        self.assertTrue(result["ok"])
        self.assertEqual(peer_status["workspace_relation"], "aligned")
        self.assertFalse(peer_status["dirty"])
        self.assertFalse(peer_status["local_checkpoint_ahead"])
        self.assertTrue(result["all_workspaces_aligned"])

    def test_remote_failure_preserves_one_local_checkpoint_for_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, manager = prepare_environment(root)
            original_source_head = git(source, "rev-parse", "HEAD")
            (manager.project_root / "tracked.py").write_text("VALUE = 8\n", encoding="utf-8")

            def fail_takeover(**_kwargs: object) -> dict[str, object]:
                raise TakeoverError("simulated remote race")

            with self.assertRaisesRegex(SimpleMainCheckpointError, "zůstal zachovaný"):
                complete_simple_main_checkpoint(
                    workspace=manager,
                    request=checkpoint_request(),
                    confirmed=True,
                    gate_runner=passing_gate_runner,
                    gate_log_path=root / "gate.log",
                    now_factory=fixed_now,
                    takeover=fail_takeover,
                )

            status = manager.status()
            handoff = (manager.project_root / "memory" / "handoffs" / "demo.md").read_text(
                encoding="utf-8"
            )
            source_head_after = git(source, "rev-parse", "HEAD")
            workspace_subject = git(manager.workspace_root, "log", "-1", "--format=%s")

        self.assertEqual(source_head_after, original_source_head)
        self.assertEqual(status["workspace_relation"], "local_ahead")
        self.assertEqual(status["local_commit_count"], 1)
        self.assertFalse(status["dirty"])
        self.assertIn("Automatický checkpoint 2026-07-20 07:00 CEST", handoff)
        self.assertEqual(workspace_subject, "Complete one simple step")


if __name__ == "__main__":
    unittest.main()
