from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

from app.worktree_cleanup import CONFIRMATION, GRACE_SECONDS, Housekeeping
from scripts.workspace_housekeeping import activate, agent, prepare


class WorktreeCleanupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.project = self.repo / "Samantha_Agent"
        self.project.mkdir()
        self.base = self.root / "worktrees"
        self.base.mkdir()
        self.command(self.repo, "init", "-b", "main")
        self.command(self.repo, "config", "user.email", "fixture@example.invalid")
        self.command(self.repo, "config", "user.name", "Fixture")
        (self.repo / "tracked.txt").write_text("original")
        (self.repo / ".gitignore").write_text(".venv/\n__pycache__/\nprivate/\n*.secret\n.DS_Store\n")
        self.command(self.repo, "add", "tracked.txt", ".gitignore")
        self.command(self.repo, "commit", "-m", "fixture")
        self.path = self.base / "data-finished"
        self.command(self.repo, "worktree", "add", "-b", "data/finished", str(self.path))
        self.head = self.command(self.path, "rev-parse", "HEAD").strip()
        self.now = time.time()
        self.service = Housekeeping(self.project, worktrees=self.base, busy_probe=lambda p: False,
                                    clock=lambda: self.now)

    def command(self, root, *argv):
        return subprocess.run(["git", "-C", str(root), *argv], check=True, capture_output=True, text=True).stdout

    def retire(self):
        return self.service.retire("data-finished", expected_head=self.head)

    def enable(self):
        self.service._write("activation.json", {"enabled": True})
        self.now += GRACE_SECONDS + 1

    def autosave(self):
        root = self.project / "data/session_autosave"
        root.mkdir(parents=True)
        for name in ("latest_session.jsonl", "latest_session.txt", "previous_session.jsonl", "previous_session.txt"):
            (root / name).write_text("fixture")
        for hour in range(20):
            for ext in ("jsonl", "txt"):
                (root / f"session_20261101_{hour:02}0000.{ext}").write_text("fixture")
        (root / "previous_session 2.jsonl").write_text("keep unknown name")
        return root

    def test_preview_does_not_write_or_retire(self):
        row = self.service.preview()["worktrees"][0]
        self.assertTrue(row["eligible"])
        self.assertEqual(row["retirement"], "not_retired")
        self.assertFalse(self.service.root.exists())

    def test_disabled_tick_does_not_delete(self):
        self.retire()
        self.now += GRACE_SECONDS + 1
        self.assertEqual(self.service.tick()["state"], "disabled")
        self.assertTrue(self.path.exists())

    def test_unregistered_worktree_is_preserved_even_when_clean(self):
        self.enable()
        self.service.tick()
        self.assertTrue(self.path.exists())

    def test_clean_retired_workspace_removed_branch_preserved(self):
        self.retire()
        self.enable()
        with patch("app.worktree_cleanup.shutil.disk_usage") as space:
            space.side_effect = [type("Space", (), {"free": 100})(), type("Space", (), {"free": 150})()]
            result = self.service.tick()
        self.assertEqual(result["removed"], ["data-finished"])
        self.assertEqual(result["free_change_bytes"], 50)
        self.assertFalse(self.path.exists())
        self.assertEqual(self.command(self.repo, "rev-parse", "data/finished").strip(), self.head)
        self.assertEqual(self.service.tick()["removed"], [])

    def test_completion_marker_has_one_hour_grace(self):
        self.retire()
        self.service._write("activation.json", {"enabled": True})
        self.assertEqual(self.service.tick()["removed"], [])
        self.assertTrue(self.path.exists())

    def test_two_ticks_remove_only_once(self):
        self.retire()
        self.enable()
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: self.service.tick(), range(2)))
        self.assertEqual(sum(len(r["removed"]) for r in results), 1)

    def test_changed_tracked_file_after_retirement_blocks(self):
        self.retire()
        (self.path / "tracked.txt").write_text("new work")
        self.enable()
        self.assertTrue(self.service.tick()["blocked"])
        self.assertTrue(self.path.exists())

    def test_staged_and_untracked_files_block(self):
        (self.path / "new.txt").write_text("new")
        self.assertFalse(self.service.inspect("data-finished")["eligible"])
        self.command(self.path, "add", "new.txt")
        self.assertFalse(self.service.inspect("data-finished")["eligible"])

    def test_unmerged_commit_and_wrong_head_block_retirement(self):
        with self.assertRaises(ValueError):
            self.service.retire("data-finished", expected_head="0" * 40)
        (self.path / "tracked.txt").write_text("unmerged")
        self.command(self.path, "commit", "-am", "unmerged")
        self.assertFalse(self.service.inspect("data-finished")["eligible"])

    def test_ignored_private_file_blocks_without_reading_content(self):
        secret = self.path / "example.secret"
        secret.write_text("not inspected")
        row = self.service.inspect("data-finished")
        self.assertFalse(row["eligible"])
        self.assertEqual(row["unknown_ignored_files"], 1)
        self.assertNotIn("not inspected", json.dumps(row))

    def test_regenerable_cache_is_permitted_and_removed_by_git(self):
        cache = self.path / "__pycache__"
        cache.mkdir()
        (cache / "fixture.pyc").write_bytes(b"cache")
        self.retire()
        self.enable()
        self.assertEqual(self.service.tick()["removed"], ["data-finished"])

    def test_ignored_data_must_have_exact_canonical_copy_and_is_revalidated(self):
        canonical = self.repo / "private"
        local = self.path / "private"
        canonical.mkdir()
        local.mkdir()
        (canonical / "fixture").write_text("preserved")
        (local / "fixture").write_text("preserved")
        row = self.service.inspect("data-finished")
        self.assertTrue(row["eligible"])
        self.assertEqual(row["verified_canonical_duplicates"], 1)
        self.retire()
        (canonical / "fixture").write_text("different")
        self.enable()
        self.assertTrue(self.service.tick()["blocked"])
        self.assertEqual((local / "fixture").read_text(), "preserved")

    def test_canonical_duplicate_survives_removal(self):
        for root in (self.repo, self.path):
            (root / "private").mkdir()
            (root / "private/fixture").write_text("preserved")
        self.retire()
        self.enable()
        self.assertEqual(self.service.tick()["removed"], ["data-finished"])
        self.assertEqual((self.repo / "private/fixture").read_text(), "preserved")

    def test_busy_or_locked_workspace_is_preserved(self):
        self.service.busy_probe = lambda p: True
        self.assertFalse(self.service.inspect("data-finished")["eligible"])
        self.service.busy_probe = lambda p: False
        self.command(self.repo, "worktree", "lock", str(self.path))
        self.assertFalse(self.service.inspect("data-finished")["eligible"])

    def test_probe_failure_is_fail_closed(self):
        def fail(path):
            raise ValueError("probe unavailable")
        self.service.busy_probe = fail
        self.assertFalse(self.service.inspect("data-finished")["eligible"])

    def test_protected_root_path_traversal_symlink_and_foreign_repo_block(self):
        for name in ("ebbd", "../repo", str(self.repo), "data-finished/subdir"):
            self.assertFalse(self.service.inspect(name)["eligible"])
        (self.base / "data-alias").symlink_to(self.path, target_is_directory=True)
        self.assertFalse(self.service.inspect("data-alias")["eligible"])
        foreign = self.base / "data-foreign"
        foreign.mkdir()
        self.command(foreign, "init")
        self.assertFalse(self.service.inspect("data-foreign")["eligible"])

    def test_cache_symlink_is_never_followed_or_deleted(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "precious").write_text("keep")
        (self.path / "__pycache__").symlink_to(outside, target_is_directory=True)
        self.assertFalse(self.service.inspect("data-finished")["eligible"])
        self.assertTrue((outside / "precious").exists())

    def test_completion_can_be_cancelled_before_reuse(self):
        self.retire()
        self.service.cancel("data-finished")
        self.enable()
        self.assertEqual(self.service.tick()["removed"], [])
        self.assertTrue(self.path.exists())

    def test_interrupted_or_failed_removal_is_not_repeated(self):
        self.retire()
        self.enable()
        original = self.service._git
        attempts = []
        def fail(path, *args, **kwargs):
            if args[:2] == ("worktree", "remove"):
                attempts.append(args)
                raise ValueError("uncertain removal")
            return original(path, *args, **kwargs)
        self.service._git = fail
        self.service.tick()
        self.service.tick()
        self.assertEqual(len(attempts), 1)
        self.assertNotIn("--force", attempts[0])
        self.assertTrue(self.path.exists())

    def test_crash_marker_requires_review(self):
        self.retire()
        state = self.service._read("state.json", {})
        state["entries"]["data-finished"]["state"] = "removing"
        self.service._write("state.json", state)
        self.enable()
        self.assertEqual(self.service.tick()["state"], "attention")
        self.assertTrue(self.path.exists())

    def test_retention_keeps_twelve_pairs_and_all_current_previous_unknown_files(self):
        root = self.autosave()
        self.assertEqual(self.service._autosave()["removed"], 16)
        self.assertEqual(len(list(root.glob("session_*.jsonl"))), 12)
        self.assertTrue((root / "session_20261101_190000.jsonl").exists())
        self.assertTrue((root / "latest_session.jsonl").exists())
        self.assertTrue((root / "previous_session.jsonl").exists())
        self.assertTrue((root / "previous_session 2.jsonl").exists())

    def test_missing_stale_or_symlinked_recovery_preserves_history(self):
        root = self.autosave()
        self.now += 1201
        self.assertEqual(self.service._autosave()["state"], "blocked")
        self.assertEqual(len(list(root.glob("session_*.jsonl"))), 20)
        self.now = time.time()
        (root / "latest_session.jsonl").unlink()
        (root / "latest_session.jsonl").symlink_to(root / "previous_session.jsonl")
        self.assertEqual(self.service._autosave()["state"], "blocked")

    def test_activation_requires_exact_phrase_and_unchanged_proposal(self):
        proposal = prepare(self.service)
        with self.assertRaises(ValueError):
            activate(self.service, confirmation="ano", proposal_sha256=proposal["sha256"])
        with self.assertRaises(ValueError):
            activate(self.service, confirmation=CONFIRMATION, proposal_sha256="0" * 64)
        self.assertFalse((self.service.root / "activation.json").exists())

    def test_activation_installs_only_new_owned_job_and_never_retries_uncertain_bootstrap(self):
        interpreter = self.project / ".venv/bin/python"
        interpreter.parent.mkdir(parents=True)
        interpreter.touch()
        proposal = prepare(self.service)
        calls = []
        def runner(argv, **kwargs):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 1)
        with self.assertRaises(ValueError):
            activate(self.service, confirmation=CONFIRMATION, proposal_sha256=proposal["sha256"],
                     agents=self.root / "agents", runner=runner)
        with self.assertRaises(ValueError):
            activate(self.service, confirmation=CONFIRMATION, proposal_sha256=proposal["sha256"],
                     agents=self.root / "agents", runner=runner)
        self.assertEqual(sum("bootstrap" in c for c in calls), 1)
        self.assertFalse(self.service._read("activation.json", {})["enabled"])
        self.assertEqual(agent(self.project)["StartInterval"], 3600)
        self.assertNotIn("KeepAlive", agent(self.project))

    def test_successful_activation_and_existing_definition_protection(self):
        interpreter = self.project / ".venv/bin/python"
        interpreter.parent.mkdir(parents=True)
        interpreter.touch()
        proposal = prepare(self.service)
        calls = []
        def runner(argv, **kwargs):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 1 if len(calls) == 1 else 0)
        result = activate(self.service, confirmation=CONFIRMATION, proposal_sha256=proposal["sha256"],
                          agents=self.root / "agents", runner=runner)
        self.assertTrue(result["enabled"])
        self.assertEqual(result["state"], "active")
        definition = next((self.root / "agents").glob("*.plist"))
        original = definition.read_bytes()
        self.service.root.joinpath("activation.json").unlink()  # independent fixture of pre-existing job
        with self.assertRaises(ValueError):
            activate(self.service, confirmation=CONFIRMATION, proposal_sha256=proposal["sha256"],
                     agents=self.root / "agents", runner=runner)
        self.assertEqual(definition.read_bytes(), original)
        self.assertEqual(len(calls), 3)


class HousekeepingCardTests(unittest.TestCase):
    def setUp(self):
        from app.cockpit_housekeeping import HousekeepingOverview
        self.now = 10000
        self.callbacks = []
        class Store:
            def __init__(self):
                self.files = {"activation.json": {"enabled": True}, "state.json": {"entries": {}},
                              "latest.json": {"time": 9900, "state": "completed", "removed": [],
                                              "autosave": {"removed": 48}, "free_change_bytes": 2**29}}
                self.rows = [{"name": "data-finished", "eligible": True, "inventory_sha256": "private-hash"},
                             {"name": "data-private", "eligible": False, "reason": "Unknown ignored data must be preserved first", "path": "/private/secret"}]
                self.fail = False
            def _read(self, name, default):
                return self.files.get(name, default)
            def preview(self):
                if self.fail:
                    raise RuntimeError("private information")
                return {"worktrees": self.rows}
            def _write(self, *args):
                raise AssertionError("A status card must never persist or mutate")
        self.store = Store()
        self.view = HousekeepingOverview(self.store, probe=lambda: {"loaded": True, "last_exit_code": 0},
                                         clock=lambda: self.now, start=self.callbacks.append)

    def sample(self):
        self.view.overview()
        self.callbacks.pop()()
        return self.view.overview()

    def test_first_request_is_pending_not_an_empty_success_and_one_audit_only(self):
        for _ in range(3):
            result = self.view.overview(refresh=True)
            self.assertTrue(result["audit"]["pending"])
            self.assertIsNone(result["counts"]["blocked"])
            self.assertIsNone(result["scheduler"]["loaded"])
        self.assertEqual(len(self.callbacks), 1)

    def test_card_redacts_private_metadata_and_distinguishes_unclosed_blocked_and_pending(self):
        result = self.sample()
        self.assertEqual(result["counts"], {"pending": 0, "blocked": 1, "unclosed": 1})
        self.assertEqual(result["last_run"]["autosave_removed"], 48)
        self.assertEqual(result["last_run"]["free_change_bytes"], 2**29)
        self.assertTrue(result["scheduler"]["loaded"])
        self.assertNotIn("private-hash", json.dumps(result))
        self.assertNotIn("/private/secret", json.dumps(result))
        self.store.files["state.json"]["entries"]["data-finished"] = {"state": "retired", "marked_at": self.now}
        result = self.view.overview()
        self.assertEqual(result["counts"]["pending"], 1)
        self.assertEqual(result["rows"][0]["ready_after"], self.now + GRACE_SECONDS)

    def test_old_and_failed_audit_never_looks_current_or_erases_known_rows(self):
        first = self.sample()
        self.now += 301
        result = self.view.overview()
        self.assertTrue(result["audit"]["pending"])
        self.assertTrue(result["audit"]["stale"])
        self.store.fail = True
        self.callbacks.pop()()
        result = self.view.overview()
        self.assertTrue(result["audit"]["failed"])
        self.assertEqual(result["rows"], first["rows"])
        self.assertNotIn("private information", json.dumps(result))

    def test_stale_worker_and_unknown_measurement_are_not_success_or_zero(self):
        self.store.files["latest.json"] = {"time": 10, "state": "attention"}
        result = self.sample()
        self.assertFalse(result["last_run"]["recent"])
        self.assertIsNone(result["last_run"]["free_change_bytes"])
        self.assertIsNone(result["last_run"]["autosave_removed"])

    def test_uncertain_removal_is_shown_even_when_worktree_is_missing(self):
        self.store.files["state.json"]["entries"]["data-missing"] = {"state": "attention"}
        result = self.sample()
        self.assertEqual(result["counts"]["blocked"], 2)
        self.assertIn("ruční ověření", next(r for r in result["rows"] if r["name"] == "data-missing")["reason"])

    def test_http_is_get_only_and_refresh_does_not_run_cleanup(self):
        from http.client import HTTPConnection
        from http.server import ThreadingHTTPServer
        import threading
        from app import cockpit
        result = self.sample()
        server = ThreadingHTTPServer(("127.0.0.1", 0), cockpit.CockpitServer().make_handler())
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch("app.cockpit.housekeeping_overview", return_value=result) as overview, patch.object(Housekeeping, "tick") as tick:
                for suffix in ("", "?refresh=1", "?apply=1"):
                    connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                    connection.request("GET", "/api/workspace-housekeeping" + suffix)
                    response = connection.getresponse()
                    self.assertEqual(response.status, 400 if "apply" in suffix else 200)
                    response.read(); connection.close()
                self.assertEqual(overview.call_count, 2)
                self.assertEqual(overview.call_args.kwargs, {"refresh": True})
                connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                connection.request("POST", "/api/workspace-housekeeping", body="{}", headers={"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{server.server_port}"})
                response = connection.getresponse()
                self.assertIn(response.status, (400, 404, 405)); response.read(); connection.close()
                self.assertEqual(overview.call_count, 2)
                tick.assert_not_called()
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=3)

    def test_card_frontend_behavior(self):
        from scripts.cockpit_quality_gate import node_binary
        result = subprocess.run([node_binary(), str(Path(__file__).with_name("housekeeping_frontend.test.cjs"))],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
