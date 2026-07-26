from __future__ import annotations

import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from app.codex_appserver import AppServerError
from app.communication.human_adam_workspace import HumanAdamWorkspaceManager
from app.communication.simple_main_checkpoint import (
    CURRENT_STATUS_END,
    CURRENT_STATUS_START,
    SimpleMainCheckpointError,
    SimpleMainCheckpointRequest,
    _checkpoint_status_projection,
    _replace_current_status,
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


def checkpoint_request(**overrides: object) -> SimpleMainCheckpointRequest:
    values: dict[str, object] = {
        "workstream_id": "layer-human-adam-development",
        "commit_message": "Complete one simple step",
        "summary": "Jednoduchý backend dokončil jeden krok",
        "next_step": "Ručně ověřit výsledek",
        "handoff_relative_path": "memory/handoffs/demo.md",
        "tvbcp_relative_path": "memory/tvbcp/demo.txt",
        "decision": "Nové TVBCP zápisy mají lidský souhrn před technickým důkazem",
        "proposed_next_steps": (
            "Ověřit nový záznam v jednom projektu",
            "Podle výsledku pokračovat druhou fází",
        ),
    }
    values.update(overrides)
    return SimpleMainCheckpointRequest(**values)  # type: ignore[arg-type]


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
            commit_count = int(
                git(source, "rev-list", "--count", f"{original_head}..HEAD")
            )

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
        self.assertIn("Stav při vytvoření checkpointu:", handoff)
        self.assertIn("## Aktuální stav", handoff)
        self.assertIn("plná Cockpit brána: 12 testů", handoff)
        self.assertIn("### 2026-07-20 07:00 CEST", tvbcp)
        self.assertIn("Jednoduchý backend dokončil jeden krok", tvbcp)
        chronological_start = tvbcp.index(
            "### 2026-07-20 07:00 CEST – Jednoduchý backend dokončil jeden krok"
        )
        section_positions = [
            tvbcp.index(label, chronological_start)
            for label in (
                "Hotovo:",
                "Otevřeno:",
                "Rizika:",
                "Rozhodnutí:",
                "Další krok:",
                "Navrhované další kroky:",
                "Technický důkaz:",
            )
        ]
        self.assertEqual(section_positions, sorted(section_positions))
        self.assertIn(
            "Nové TVBCP zápisy mají lidský souhrn před technickým důkazem",
            tvbcp,
        )
        self.assertIn("Ověřit nový záznam v jednom projektu", tvbcp)
        self.assertNotIn("Milník:", tvbcp)
        self.assertNotIn("Checkpoint backend připravuje", tvbcp)
        self.assertTrue(tvbcp.startswith(CURRENT_STATUS_START))
        self.assertIn("# Demo TVBCP\n\n### ", tvbcp)
        self.assertEqual(handoff.count(CURRENT_STATUS_START), 1)
        self.assertEqual(handoff.count(CURRENT_STATUS_END), 1)
        self.assertEqual(tvbcp.count(CURRENT_STATUS_START), 1)
        self.assertEqual(tvbcp.count(CURRENT_STATUS_END), 1)
        self.assertNotIn("čeká na nasazení", handoff)
        self.assertEqual(commit_count, 1)
        self.assertEqual(progress[0:4], [
            ("preflight", "running"),
            ("preflight", "passed"),
            ("gate", "running"),
            ("gate", "passed"),
        ])
        self.assertIn(("push", "passed"), progress)
        self.assertIn(("workspace_alignment", "passed"), progress)

    def test_current_status_replaces_only_generated_summary_and_keeps_history(
        self,
    ) -> None:
        original_history = "# Handoff\n\n### 2026-07-19\nHistorický blok.\n"
        first = (
            f"{CURRENT_STATUS_START}\n## Aktuální stav\n\n- První\n"
            f"{CURRENT_STATUS_END}"
        )
        second = (
            f"{CURRENT_STATUS_START}\n## Aktuální stav\n\n- Druhý\n"
            f"{CURRENT_STATUS_END}"
        )

        with_first = _replace_current_status(original_history, first)
        with_second = _replace_current_status(with_first, second)

        self.assertIn("- Druhý", with_second)
        self.assertNotIn("- První", with_second)
        self.assertIn(original_history, with_second)
        self.assertEqual(with_second.count(CURRENT_STATUS_START), 1)
        self.assertEqual(with_second.count(CURRENT_STATUS_END), 1)

    def test_current_status_fails_closed_on_ambiguous_markers(self) -> None:
        malformed = (
            f"{CURRENT_STATUS_START}\nA\n{CURRENT_STATUS_END}\n"
            f"{CURRENT_STATUS_START}\nB\n{CURRENT_STATUS_END}\n"
        )

        with self.assertRaisesRegex(SimpleMainCheckpointError, "nejednoznačné"):
            _replace_current_status(malformed, "nový blok")

    def test_current_status_uses_safe_previous_deployment_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _source, manager = prepare_environment(root)
            previous_head = git(manager.source_repo, "rev-parse", "HEAD")[:12]
            (manager.project_root / "tracked.py").write_text(
                "VALUE = 24\n",
                encoding="utf-8",
            )

            complete_simple_main_checkpoint(
                workspace=manager,
                request=checkpoint_request(
                    last_deployed_main_short=previous_head,
                    last_deployed_at="2026-07-20T06:30:00+00:00",
                    last_deployed_test_count=11,
                    last_deployed_smoke_count=5,
                ),
                confirmed=True,
                gate_runner=passing_gate_runner,
                gate_log_path=root / "gate.log",
                now_factory=fixed_now,
            )

            handoff = (
                manager.project_root / "memory" / "handoffs" / "demo.md"
            ).read_text(encoding="utf-8")

        self.assertIn(f"`{previous_head}`", handoff)
        self.assertIn("odpovídá ověřenému main před tímto checkpointem", handoff)
        self.assertIn("11 testů", handoff)
        self.assertIn("smoke 5/5", handoff)

    def test_checkpoint_projects_live_evidence_into_semantic_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _source, manager = prepare_environment(root)
            previous_head = git(manager.source_repo, "rev-parse", "HEAD")
            (manager.project_root / "tracked.py").write_text(
                "VALUE = 25\n",
                encoding="utf-8",
            )
            context = {
                "deployment_expected": True,
                "deployment": {
                    "state": "deployed",
                    "main_head": previous_head,
                    "expected_code_stamp": "0123456789abcdef",
                    "test_count": 11,
                    "smoke_count": 5,
                    "gate_passed": True,
                    "smoke_passed": True,
                    "deployed_at": "2026-07-20T06:30:00+00:00",
                    "private_path": "/never/return/this",
                },
                "runtime": {
                    "reachable": True,
                    "socket_path": "/never/return/this",
                },
                "session": {
                    "connected": True,
                    "turn_busy": False,
                    "active_turn": None,
                    "messages": [
                        {
                            "status": "completed",
                            "user_text": "never return this private text",
                        }
                    ],
                },
                "server": {
                    "code_stamp": "0123456789abcdef",
                    "pid": 12345,
                },
            }

            complete_simple_main_checkpoint(
                workspace=manager,
                request=checkpoint_request(
                    last_deployed_main_short=previous_head[:12],
                    last_deployed_at="2026-07-20T06:30:00+00:00",
                    last_deployed_test_count=11,
                    last_deployed_smoke_count=5,
                    operational_context=context,
                ),
                confirmed=True,
                gate_runner=passing_gate_runner,
                gate_log_path=root / "gate.log",
                now_factory=fixed_now,
            )

            handoff = (
                manager.project_root / "memory" / "handoffs" / "demo.md"
            ).read_text(encoding="utf-8")
            tvbcp = (
                manager.project_root / "memory" / "tvbcp" / "demo.txt"
            ).read_text(encoding="utf-8")

        self.assertIn("### Hotovo", handoff)
        self.assertIn("### Otevřeno", handoff)
        self.assertIn("### Rizika", handoff)
        self.assertIn(
            "Předchozí stav main byl před tímto checkpointem serverově",
            handoff,
        )
        self.assertIn(
            "Pozdější nasazení nového checkpointu zatím není",
            handoff,
        )
        self.assertIn("Žádné další doložené provozní riziko", handoff)
        self.assertIn("Hotovo:", tvbcp)
        self.assertIn("Otevřeno:", tvbcp)
        self.assertIn("Rizika:", tvbcp)
        self.assertNotIn("never return", handoff.casefold())
        self.assertNotIn("never return", tvbcp.casefold())
        self.assertNotIn("12345", handoff)
        self.assertNotIn("12345", tvbcp)

    def test_projection_fails_closed_for_foreign_or_malformed_live_status(
        self,
    ) -> None:
        request = checkpoint_request()
        projection = _checkpoint_status_projection(
            request=request,
            live_status={
                "schema_version": 1,
                "read_only": True,
                "writes_performed": False,
                "workstream_id": "project-other",
                "main": {"state": "aligned"},
                "deployment": {"state": "verified_current"},
                "runtime": {"state": "connected"},
                "private_text": "never return this",
            },
        )

        self.assertEqual(projection.completed, (request.summary,))
        self.assertIn("nebyl", projection.risks[0])
        self.assertNotIn("never return", " ".join(projection.risks).casefold())

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

    def test_first_checkpoint_materializes_missing_canonical_memory_pair(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, manager = prepare_environment(root)
            (manager.project_root / "tracked.py").write_text("VALUE = 20\n", encoding="utf-8")
            handoff_relative = "memory/handoffs/workstreams/project-mmtx.md"
            tvbcp_relative = "memory/tvbcp/workstreams/project-mmtx.md"

            result = complete_simple_main_checkpoint(
                workspace=manager,
                request=checkpoint_request(
                    workstream_id="project-mmtx",
                    handoff_relative_path=handoff_relative,
                    tvbcp_relative_path=tvbcp_relative,
                    handoff_initial_content="# Handoff MMTX\n",
                    tvbcp_initial_content="# TVBCP MMTX\n",
                ),
                confirmed=True,
                gate_runner=passing_gate_runner,
                gate_log_path=root / "gate.log",
                now_factory=fixed_now,
            )

            handoff = (source / "Samantha_Agent" / handoff_relative).read_text(
                encoding="utf-8"
            )
            tvbcp = (source / "Samantha_Agent" / tvbcp_relative).read_text(
                encoding="utf-8"
            )
            committed_paths = git(source, "show", "--format=", "--name-only", "HEAD")

        self.assertTrue(result["ok"])
        self.assertIn("# Handoff MMTX", handoff)
        self.assertIn("Automatický checkpoint 2026-07-20 07:00 CEST", handoff)
        self.assertIn("# TVBCP MMTX", tvbcp)
        self.assertIn("Jednoduchý backend dokončil jeden krok", tvbcp)
        self.assertIn(handoff_relative, committed_paths)
        self.assertIn(tvbcp_relative, committed_paths)

    def test_missing_memory_without_template_is_rejected_before_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _source, manager = prepare_environment(root)
            (manager.project_root / "tracked.py").write_text("VALUE = 21\n", encoding="utf-8")

            with self.assertRaisesRegex(SimpleMainCheckpointError, "nebyl nalezen"):
                complete_simple_main_checkpoint(
                    workspace=manager,
                    request=checkpoint_request(
                        handoff_relative_path="memory/handoffs/workstreams/missing.md",
                        tvbcp_relative_path="memory/tvbcp/workstreams/missing.md",
                    ),
                    confirmed=True,
                    gate_runner=passing_gate_runner,
                    gate_log_path=root / "gate.log",
                )
            self.assertFalse(
                (manager.project_root / "memory" / "handoffs" / "workstreams").exists()
            )

    def test_gate_failure_does_not_materialize_lazy_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _source, manager = prepare_environment(root)
            (manager.project_root / "tracked.py").write_text("VALUE = 22\n", encoding="utf-8")
            handoff = manager.project_root / "memory/handoffs/workstreams/project-mmtx.md"
            tvbcp = manager.project_root / "memory/tvbcp/workstreams/project-mmtx.md"

            with self.assertRaisesRegex(SimpleMainCheckpointError, "brána"):
                complete_simple_main_checkpoint(
                    workspace=manager,
                    request=checkpoint_request(
                        handoff_relative_path=handoff.relative_to(manager.project_root).as_posix(),
                        tvbcp_relative_path=tvbcp.relative_to(manager.project_root).as_posix(),
                        handoff_initial_content="# Handoff MMTX\n",
                        tvbcp_initial_content="# TVBCP MMTX\n",
                    ),
                    confirmed=True,
                    gate_runner=failing_gate_runner,
                    gate_log_path=root / "gate.log",
                )
            self.assertFalse(handoff.exists())
            self.assertFalse(tvbcp.exists())

    def test_checkpoint_failure_removes_new_lazy_memory_pair(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _source, manager = prepare_environment(root)
            changed = manager.project_root / "tracked.py"
            changed.write_text("VALUE = 23\n", encoding="utf-8")
            handoff = manager.project_root / "memory/handoffs/workstreams/project-mmtx.md"
            tvbcp = manager.project_root / "memory/tvbcp/workstreams/project-mmtx.md"

            with patch.object(
                manager,
                "checkpoint",
                side_effect=AppServerError("simulated commit failure"),
            ):
                with self.assertRaisesRegex(SimpleMainCheckpointError, "nepodařilo vytvořit"):
                    complete_simple_main_checkpoint(
                        workspace=manager,
                        request=checkpoint_request(
                            handoff_relative_path=(
                                handoff.relative_to(manager.project_root).as_posix()
                            ),
                            tvbcp_relative_path=tvbcp.relative_to(
                                manager.project_root
                            ).as_posix(),
                            handoff_initial_content="# Handoff MMTX\n",
                            tvbcp_initial_content="# TVBCP MMTX\n",
                        ),
                        confirmed=True,
                        gate_runner=passing_gate_runner,
                        gate_log_path=root / "gate.log",
                    )

            self.assertFalse(handoff.exists())
            self.assertFalse(tvbcp.exists())
            self.assertTrue(changed.exists())
            self.assertTrue(manager.status()["dirty"])

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
