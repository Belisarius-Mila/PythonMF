from __future__ import annotations

import tempfile
import time
import unittest
import os
import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from scripts.git_safety_check import (
    BranchGuardStatus,
    StagedFile,
    check_staged,
    format_branch_guard,
    format_report,
    parse_archived_branches,
    parse_unmerged_branches_output,
    path_is_blocked,
)
from scripts.autosave_status import autosave_status, find_autosave_watchers, format_autosave_status
from scripts.autosave_resume_prompt import autosave_resume_candidate, parse_autosave_source, startup_prompt
from scripts.cleanup_session_autosave import build_cleanup_plan, format_plan
from scripts.system_quick_check import CheckLine, autosave_line, format_morning_sentence
from scripts.work_context_guard import WorkContextStatus, format_work_context_guard, parse_porcelain_status


class GitSafetyCheckTests(unittest.TestCase):
    def test_blocks_private_autosave_and_env_paths(self) -> None:
        self.assertEqual(path_is_blocked("Samantha_Agent/data/private/documents/index.json"), "data/private")
        self.assertEqual(path_is_blocked("Samantha_Agent/data/session_autosave/latest_info.txt"), "data/session_autosave")
        self.assertEqual(path_is_blocked("Samantha_Agent/.env"), "env file")

    def test_format_report_marks_clean_staged_set(self) -> None:
        report = format_report([StagedFile(status="M", path="Samantha_Agent/app/cockpit.py")], [], [])

        self.assertIn("staged files: 1", report)
        self.assertIn("no blocked", report)
        self.assertIn("no large", report)

    def test_check_staged_warns_for_binary_media(self) -> None:
        errors, warnings = check_staged(
            [StagedFile(status="A", path="docs/colors-numbers/owl.mp3")],
            large_file_bytes=5_000_000,
        )

        self.assertEqual(errors, [])
        self.assertIn("binary/media staged file: docs/colors-numbers/owl.mp3", warnings)

    def test_branch_guard_parses_unmerged_branches(self) -> None:
        branches = parse_unmerged_branches_output(
            """
              cursor/matysek-scene02-mossy-stump-prototype
              remotes/origin/cursor/matysek-scene02-mossy-stump-prototype
              remotes/origin/HEAD -> origin/main
            """
        )

        self.assertEqual(
            branches,
            (
                "cursor/matysek-scene02-mossy-stump-prototype",
                "remotes/origin/cursor/matysek-scene02-mossy-stump-prototype",
            ),
        )

    def test_branch_guard_warns_about_unmerged_work(self) -> None:
        lines = format_branch_guard(
            BranchGuardStatus(
                current_branch="main",
                base_branch="main",
                unmerged_branches=("remotes/origin/cursor/matysek-scene02-mossy-stump-prototype",),
            )
        )

        text = "\n".join(lines)
        self.assertIn("branches not merged", text)
        self.assertIn("cursor/matysek", text)
        self.assertIn("audit/cherry-pick/archive", text)

    def test_branch_guard_acknowledges_archived_work(self) -> None:
        lines = format_branch_guard(
            BranchGuardStatus(
                current_branch="main",
                base_branch="main",
                unmerged_branches=(),
                archived_branches=("remotes/origin/cursor/matysek-scene02-mossy-stump-prototype",),
            )
        )

        text = "\n".join(lines)
        self.assertIn("archived unmerged branches acknowledged", text)
        self.assertNotIn("WARN branches not merged", text)

    def test_parse_archived_branches_reads_markdown_registry(self) -> None:
        branches = parse_archived_branches(
            """
            - `cursor/matysek-scene02-mossy-stump-prototype`
            - not a branch line
            - `remotes/origin/cursor/matysek-scene02-mossy-stump-prototype`
            """
        )

        self.assertEqual(
            branches,
            (
                "cursor/matysek-scene02-mossy-stump-prototype",
                "remotes/origin/cursor/matysek-scene02-mossy-stump-prototype",
            ),
        )

    def test_format_report_includes_branch_guard(self) -> None:
        report = format_report(
            [StagedFile(status="M", path="Samantha_Agent/app/cockpit.py")],
            [],
            [],
            BranchGuardStatus(
                current_branch="feature/mixed",
                base_branch="main",
                unmerged_branches=(),
            ),
        )

        self.assertIn("Branch guard", report)
        self.assertIn("current branch is `feature/mixed`", report)


class SystemQuickCheckTests(unittest.TestCase):
    def test_format_morning_sentence_summarizes_ok_state(self) -> None:
        sentence = format_morning_sentence(
            [
                CheckLine("git", True, "clean"),
                CheckLine("backup", True, "ok"),
                CheckLine("cockpit", True, "ok"),
            ]
        )

        self.assertIn("Samantha je vzhůru", sentence)
        self.assertIn("git je čistý", sentence)

    def test_format_morning_sentence_lists_warnings(self) -> None:
        sentence = format_morning_sentence(
            [
                CheckLine("git", False, "dirty"),
                CheckLine("backup", True, "ok"),
                CheckLine("cockpit", True, "ok"),
            ]
        )

        self.assertIn("zkontrolovat: git", sentence)

    def test_autosave_line_reports_recent_file_ok(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "latest_info.txt"
            path.write_text("Saved at: test\n", encoding="utf-8")

            def fake_runner(*args, **kwargs):
                return subprocess.CompletedProcess(args[0], 0, "123 1 00:01 zsh scripts/autosave_codex_session.sh --watch\n", "")

            status = autosave_status(latest_info_path=path, warn_minutes=20, runner=fake_runner)

        self.assertTrue(status.ok)
        self.assertTrue(status.watcher_running)
        self.assertEqual(status.watcher_pids, (123,))

    def test_autosave_line_warns_for_stale_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "latest_info.txt"
            path.write_text("Saved at: old\n", encoding="utf-8")
            old = time.time() - 3600
            os.utime(path, (old, old))

            line = autosave_line(path=path, warn_minutes=20)

        self.assertFalse(line.ok)
        self.assertIn("warn > 20", line.message)

    def test_find_autosave_watchers_parses_ps_output(self) -> None:
        def fake_runner(*args, **kwargs):
            return subprocess.CompletedProcess(
                args[0],
                0,
                "\n".join(
                    [
                        "111 1 00:10 zsh scripts/autosave_codex_session.sh --watch",
                        "222 1 00:10 python scripts/autosave_status.py",
                    ]
                ),
                "",
            )

        pids, warning = find_autosave_watchers(runner=fake_runner)

        self.assertEqual(pids, [111])
        self.assertEqual(warning, "")

    def test_format_autosave_status_suggests_confirmed_restart_when_stopped(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "latest_info.txt"
            path.write_text("Saved at: test\n", encoding="utf-8")

            def fake_runner(*args, **kwargs):
                return subprocess.CompletedProcess(args[0], 0, "", "")

            status = autosave_status(latest_info_path=path, runner=fake_runner)
            text = format_autosave_status(status)

        self.assertIn("watcher: nebezi", text)
        self.assertIn("Dalsi krok po potvrzeni", text)

    def test_autosave_resume_candidate_offers_newer_autosave_than_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "rollout-test.jsonl"
            latest_info = root / "latest_info.txt"
            source.write_text("{}", encoding="utf-8")
            latest_info.write_text(f"Source: {source}\n", encoding="utf-8")
            os.utime(source, (2000, 2000))

            with patch("scripts.autosave_resume_prompt.last_commit_timestamp", return_value=(1000.0, "")):
                candidate = autosave_resume_candidate(latest_info_path=latest_info, project_root=root)

        self.assertTrue(candidate.should_offer)
        self.assertIn("novejsi nez posledni commit", candidate.reason)

    def test_autosave_resume_candidate_skips_older_autosave_than_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "rollout-test.jsonl"
            latest_info = root / "latest_info.txt"
            source.write_text("{}", encoding="utf-8")
            latest_info.write_text(f"Source: {source}\n", encoding="utf-8")
            os.utime(source, (1000, 1000))

            with patch("scripts.autosave_resume_prompt.last_commit_timestamp", return_value=(2000.0, "")):
                candidate = autosave_resume_candidate(latest_info_path=latest_info, project_root=root)

        self.assertFalse(candidate.should_offer)
        self.assertIn("neni novejsi", candidate.reason)

    def test_parse_autosave_source_and_startup_prompt_do_not_read_session_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "rollout-test.jsonl"
            latest_info = Path(temp_dir) / "latest_info.txt"
            latest_info.write_text(f"Saved at: test\nSource: {source}\n", encoding="utf-8")

            parsed = parse_autosave_source(latest_info)

        self.assertEqual(parsed, source)
        self.assertIn("Jen cti, nic nemen", startup_prompt())


class AutosaveCleanupTests(unittest.TestCase):
    def test_cleanup_plan_deletes_only_old_timestamped_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            old_jsonl = root / "session_20260620_120000.jsonl"
            old_txt = root / "session_20260620_120000.txt"
            recent_jsonl = root / "session_20260629_120000.jsonl"
            latest_jsonl = root / "latest_session.jsonl"
            for path in (old_jsonl, old_txt, recent_jsonl, latest_jsonl):
                path.write_text("x" * 10, encoding="utf-8")

            plan = build_cleanup_plan(
                autosave_dir=root,
                retention_days=3,
                keep_latest_snapshots=0,
                now=datetime(2026, 6, 30, 12, 0, 0),
            )

        self.assertEqual(plan.delete_count, 2)
        self.assertEqual({Path(item.path).name for item in plan.delete_files}, {old_jsonl.name, old_txt.name})
        self.assertEqual(plan.reclaim_bytes, 20)

    def test_cleanup_plan_keeps_latest_snapshots_even_when_old(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            newest_old = root / "session_20260620_130000.jsonl"
            older = root / "session_20260620_120000.jsonl"
            newest_old.write_text("newest", encoding="utf-8")
            older.write_text("older", encoding="utf-8")

            plan = build_cleanup_plan(
                autosave_dir=root,
                retention_days=3,
                keep_latest_snapshots=1,
                now=datetime(2026, 6, 30, 12, 0, 0),
            )

        self.assertEqual(plan.delete_count, 1)
        self.assertEqual(Path(plan.delete_files[0].path).name, older.name)

    def test_format_plan_is_dry_run_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            old_jsonl = root / "session_20260620_120000.jsonl"
            old_jsonl.write_text("x", encoding="utf-8")

            plan = build_cleanup_plan(
                autosave_dir=root,
                retention_days=3,
                keep_latest_snapshots=0,
                now=datetime(2026, 6, 30, 12, 0, 0),
            )
            text = format_plan(plan)

        self.assertIn("dry-run", text)
        self.assertIn("--apply --confirm", text)


class WorkContextGuardTests(unittest.TestCase):
    def test_parse_porcelain_status_counts_pending_work(self) -> None:
        branch, ahead, behind, staged, unstaged, untracked = parse_porcelain_status(
            "\n".join(
                [
                    "## feature/demo...origin/feature/demo [ahead 2, behind 1]",
                    "M  Samantha_Agent/app/cockpit.py",
                    " M Samantha_Agent/tests/test_cockpit.py",
                    "?? Samantha_Agent/tmp.txt",
                ]
            )
        )

        self.assertEqual(branch, "feature/demo")
        self.assertEqual(ahead, 2)
        self.assertEqual(behind, 1)
        self.assertEqual(staged, 1)
        self.assertEqual(unstaged, 1)
        self.assertEqual(untracked, 1)

    def test_work_context_guard_reports_safe_switch(self) -> None:
        text = format_work_context_guard(
            WorkContextStatus(
                current_branch="main",
                base_branch="main",
                ahead=0,
                behind=0,
                staged_count=0,
                unstaged_count=0,
                untracked_count=0,
                git_operation="",
                unmerged_branches=(),
            )
        )

        self.assertIn("safe to switch topic", text)
        self.assertIn("OK no staged", text)

    def test_work_context_guard_blocks_mixed_pending_work(self) -> None:
        status = WorkContextStatus(
            current_branch="feature/demo",
            base_branch="main",
            ahead=1,
            behind=0,
            staged_count=2,
            unstaged_count=1,
            untracked_count=1,
            git_operation="cherry-pick",
            unmerged_branches=("feature/other",),
        )

        text = format_work_context_guard(status)

        self.assertFalse(status.clean)
        self.assertIn("current branch is `feature/demo`", text)
        self.assertIn("pending changes", text)
        self.assertIn("git operation in progress: cherry-pick", text)
        self.assertIn("checkpoint current work", text)


if __name__ == "__main__":
    unittest.main()
