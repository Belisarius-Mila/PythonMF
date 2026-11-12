from __future__ import annotations

import copy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
from threading import Barrier
import unittest
from unittest.mock import patch

from app.email.continuous_agent import ContinuousEmailAgent
from app.email.followups import EmailFollowups, FollowupError, FollowupConflict, FollowupNotFound
from app.work_repository import MAX_IDEMPOTENCY_RECORDS, RepositoryMutation, WorkRepositoryError
from tests.test_continuous_email_agent import FakeSource, observed, proposal


class EmailFollowupsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.worker = ContinuousEmailAgent(self.root / "agent")
        self.now = datetime(2026, 11, 11, 10, tzinfo=timezone.utc)
        self.service = EmailFollowups(self.worker, clock=lambda: self.now)
        self.message = observed(body="PRIVATE BODY MUST NOT BE COPIED INTO FOLLOWUPS")
        self.worker.cycle(FakeSource([self.message]), lambda _: proposal())
        self.initial = copy.deepcopy(self.worker.status())

    def create_command(self, operation="create-0001", **fields):
        return {"action": "create", "operation_id": operation, "source_item_id": self.message.item_id,
                "fields": {"title": "Nabídka koupelny", "goal": "Získat nabídku včetně montáže",
                           "next_step": "Čekáme na dodavatele", "waiting_on": "other",
                           "check_at": (self.now + timedelta(days=3)).isoformat(), **fields}}

    def create(self):
        return self.service.execute(self.create_command())["followup"]

    def state_command(self, value, state, operation="state-0001", **extra):
        return {"action": "set_state", "id": value["id"], "expected_revision": value["revision"],
                "operation_id": operation, "state": state, **extra}

    def update_command(self, value, operation="update-0001", **fields):
        keys = ("title", "goal", "next_step", "waiting_on", "check_at")
        return {"action": "update", "id": value["id"], "expected_revision": value["revision"],
                "operation_id": operation, "fields": {**{k: value[k] for k in keys}, **fields}}

    def test_empty_read_is_inert_and_does_not_claim_a_running_monitor(self):
        worker = ContinuousEmailAgent(self.root / "absent")
        result = EmailFollowups(worker).overview()
        self.assertEqual(result["active"], [])
        self.assertFalse(result["capabilities"]["automatic_monitoring"])
        self.assertFalse(worker.root.exists())

    def test_create_preserves_existing_data_and_copies_only_source_identity(self):
        with patch("app.email.continuous_source.IMAPAgentSource.scan", side_effect=AssertionError("IMAP")), \
             patch("app.email.codex_proposer.CodexEmailProposer.__call__", side_effect=AssertionError("model")):
            value = self.create()
        state = self.worker.status()
        self.assertEqual(state["items"], self.initial["items"])
        self.assertEqual(state["sources"], self.initial["sources"])
        self.assertEqual(value["revision"], 1)
        self.assertEqual(value["generation"], 1)
        self.assertEqual(value["source"]["content_digest"], self.message.content_digest)
        self.assertEqual(value["source"]["thread_binding"], "pending")
        self.assertEqual(value["monitoring"], "not_connected")
        self.assertNotIn("PRIVATE BODY", str(state["followups"]))
        self.assertNotIn("proposal", value)

    def test_update_complete_and_reopen_preserve_identity_and_audit_history(self):
        first = self.create()
        updated = self.service.execute(self.update_command(first, next_step="Poslat míry", waiting_on="me"))["followup"]
        self.assertEqual(updated["revision"], 2)
        self.assertEqual(updated["generation"], 1)
        done = self.service.execute(self.state_command(updated, "completed"))["followup"]
        self.assertEqual(done["generation"], 2)
        self.assertEqual(self.service.overview()["active"], [])
        self.assertEqual(self.service.overview()["completed"][0]["id"], first["id"])
        # Restart the domain object over the same storage, not a new case.
        self.service = EmailFollowups(ContinuousEmailAgent(self.worker.root), clock=lambda: self.now)
        reopened = self.service.execute(self.state_command(done, "active", "reopen-0001"))["followup"]
        self.assertEqual(reopened["id"], first["id"])
        self.assertEqual(reopened["source"], first["source"])
        self.assertEqual((reopened["revision"], reopened["generation"]), (4, 3))
        self.assertEqual(reopened["completed_at"], "")
        self.assertEqual([e["action"] for e in reopened["history"]], ["create", "update", "set_state", "set_state"])

    def test_explicit_source_detail_reads_hidden_cached_message_without_writes(self):
        value = self.create()
        self.worker.dismiss([self.message.item_id], action="dismiss")
        before = self.worker.repository.path.read_bytes()
        with patch("app.email.continuous_source.IMAPAgentSource.scan", side_effect=AssertionError("IMAP")):
            detail = self.service.overview({"id": value["id"]})
        self.assertEqual(detail["source_message"]["header"]["subject"], "Podklady ke schůzce")
        self.assertIn("PRIVATE BODY", detail["source_message"]["body_text"])
        self.assertEqual(set(detail["source_message"]), {"header", "body_text"})
        self.assertNotIn("PRIVATE BODY", str(self.service.overview()))
        self.assertNotIn("PRIVATE BODY", str(self.worker.status()["followups"]))
        self.assertEqual(self.worker.repository.path.read_bytes(), before)

    def test_source_detail_rejects_replaced_identity_or_missing_original(self):
        value = self.create()
        original = self.worker.repository.read()
        for key in ("account", "provider", "folder", "uidvalidity", "uid", "content_digest"):
            document = copy.deepcopy(original)
            document["items"][self.message.item_id][key] = "different"
            with patch.object(self.service.repository, "read", return_value=document):
                self.assertIsNone(self.service.overview({"id": value["id"]})["source_message"])
        document = copy.deepcopy(original)
        document["items"].pop(self.message.item_id)
        with patch.object(self.service.repository, "read", return_value=document):
            detail = self.service.overview({"id": value["id"]})
            self.assertIsNone(detail["source_message"])
            self.assertEqual(detail["followup"]["id"], value["id"])

    def test_expired_reopen_requires_new_date_and_failed_command_leaves_no_write(self):
        first = self.create()
        done = self.service.execute(self.state_command(first, "completed"))["followup"]
        self.now += timedelta(days=4)
        before = self.worker.repository.path.read_bytes()
        command = self.state_command(done, "active", "reopen-0001")
        with self.assertRaises(FollowupError):
            self.service.execute(command)
        self.assertEqual(self.worker.repository.path.read_bytes(), before)
        command["check_at"] = (self.now + timedelta(days=1)).isoformat()
        value = self.service.execute(command)["followup"]
        self.assertEqual(value["state"], "active")
        self.assertEqual(value["generation"], 3)

    def test_stale_update_and_lifecycle_cannot_overwrite_manual_completion(self):
        first = self.create()
        done = self.service.execute(self.state_command(first, "completed"))["followup"]
        before = self.worker.repository.path.read_bytes()
        for command in [self.update_command(first), self.state_command(first, "active", "stale-0001")]:
            with self.assertRaises(FollowupConflict):
                self.service.execute(command)
        with self.assertRaises(FollowupConflict):
            self.service.execute(self.update_command(done))
        self.assertEqual(self.worker.repository.path.read_bytes(), before)

    def test_replay_returns_current_revision_and_rejects_repurposed_operation(self):
        command = self.create_command()
        first = self.service.execute(command)["followup"]
        done = self.service.execute(self.state_command(first, "completed"))["followup"]
        replay = self.service.execute(command)
        self.assertTrue(replay["idempotent_replay"])
        self.assertEqual(replay["operation_revision"], 1)
        self.assertEqual(replay["followup"], done)
        command["fields"]["goal"] = "Jiný cíl"
        with self.assertRaises(FollowupConflict):
            self.service.execute(command)
        self.assertEqual(len(self.worker.status()["followups"]["items"]), 1)

    def test_second_create_for_same_source_does_not_duplicate_or_reopen(self):
        first = self.create()
        result = self.service.execute(self.create_command("create-0002"))
        self.assertFalse(result["changed"])
        self.assertEqual(result["followup"]["id"], first["id"])
        done = self.service.execute(self.state_command(first, "completed"))["followup"]
        result = self.service.execute(self.create_command("create-0003"))
        self.assertEqual(result["followup"], done)
        with self.assertRaises(FollowupConflict):
            self.service.execute(self.create_command("create-0004", title="Jiná věc"))

    def test_noop_state_does_not_add_revision_or_generation(self):
        first = self.create()
        result = self.service.execute(self.state_command(first, "active"))
        self.assertFalse(result["changed"])
        self.assertEqual(result["followup"], first)

    def test_replay_survives_generic_repository_idempotency_eviction(self):
        command = self.create_command()
        first = self.service.execute(command)["followup"]
        for i in range(MAX_IDEMPOTENCY_RECORDS + 2):
            self.worker.repository.transact(lambda d: RepositoryMutation(d), operation_id=f"other-operation-{i}")
        restarted = EmailFollowups(ContinuousEmailAgent(self.worker.root), clock=lambda: self.now)
        result = restarted.execute(command)
        self.assertTrue(result["idempotent_replay"])
        self.assertEqual(result["followup"], first)

    def test_concurrent_create_has_one_identity_and_one_creation_event(self):
        barrier = Barrier(2)
        def create():
            service = EmailFollowups(ContinuousEmailAgent(self.worker.root), clock=lambda: self.now)
            barrier.wait(timeout=3)
            return service.execute(self.create_command())
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: create(), range(2)))
        self.assertEqual(sum(r["changed"] for r in results), 1)
        self.assertEqual(results[0]["followup"]["id"], results[1]["followup"]["id"])
        self.assertEqual(len(self.service.overview()["active"][0]["history"]), 1)

    def test_concurrent_edits_require_the_new_revision(self):
        first = self.create()
        barrier = Barrier(2)
        def update(i):
            service = EmailFollowups(ContinuousEmailAgent(self.worker.root), clock=lambda: self.now)
            barrier.wait(timeout=3)
            try:
                return service.execute(self.update_command(first, f"update-000{i}", title=f"Nabídka {i}"))
            except FollowupConflict:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(update, [1, 2]))
        self.assertEqual(sum(r is not None for r in results), 1)
        self.assertEqual(self.service.overview()["active"][0]["revision"], 2)

    def test_failed_atomic_write_can_be_recovered_by_same_operation(self):
        before = self.worker.repository.path.read_bytes()
        with patch("app.work_repository._write_repository_document_under_lock", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                self.service.execute(self.create_command())
        self.assertEqual(self.worker.repository.path.read_bytes(), before)
        first = self.create()
        replay = self.service.execute(self.create_command())
        self.assertEqual(replay["followup"], first)
        self.assertEqual(len(replay["followup"]["history"]), 1)

    def test_legacy_mail_cycle_and_dismissal_preserve_followup(self):
        first = self.create()
        second = observed(uid="2")
        self.worker.cycle(FakeSource([self.message, second]), lambda _: proposal())
        self.worker.dismiss([self.message.item_id], action="dismiss")
        self.assertEqual(self.service.overview()["active"][0], first)
        self.assertEqual(self.worker.status()["sources"]["account-a"]["after_uid"], 2)

    def test_existing_archive_operation_preserves_followup(self):
        first = self.create()
        digest = self.worker.status()["items"][self.message.item_id]["proposal_digest"]
        self.worker.accept_archive(self.message, confirmed_digest=digest)
        self.assertEqual(self.service.overview()["active"][0], first)
        self.assertEqual(self.worker.status()["items"][self.message.item_id]["status"], "archived")

    def test_validation_never_changes_existing_document(self):
        first = self.create()
        invalid = [self.create_command("another-001", check_at="2026-11-20T09:00:00"),
                   self.create_command("another-002", check_at=self.now.isoformat()),
                   self.create_command("another-003", waiting_on="automatic"),
                   self.create_command("another-004", title=" "),
                   self.create_command("another-005", goal="x" * 2001),
                   {**self.create_command(), "root": "/not-a-root"},
                   {**self.update_command(first), "expected_revision": True},
                   {**self.state_command(first, "completed"), "check_at": "2027-01-01T00:00:00Z"},
                   {**self.create_command(), "operation_id": "../escape"}, []]
        before = self.worker.repository.path.read_bytes()
        for command in invalid:
            with self.subTest(command=command):
                with self.assertRaises(FollowupError):
                    self.service.execute(command)
                self.assertEqual(self.worker.repository.path.read_bytes(), before)

    def test_timezone_normalization_and_unicode_are_preserved(self):
        command = self.create_command(check_at="2026-11-14T11:00:00+01:00")
        value = self.service.execute(command)["followup"]
        self.assertEqual(value["check_at"], "2026-11-14T10:00:00+00:00")
        self.assertEqual(value["goal"], "Získat nabídku včetně montáže")
        command["fields"]["check_at"] = value["check_at"]
        self.assertTrue(self.service.execute(command)["idempotent_replay"])

    def test_corrupt_or_future_namespace_is_not_replaced(self):
        for invalid in [None, {"version": 2, "items": {}, "operations": {}},
                        {"version": True, "items": {}, "operations": {}}]:
            self.worker._update(lambda d: d.update(followups=invalid))
            before = self.worker.repository.path.read_bytes()
            for callback in [self.service.overview, lambda: self.service.execute(self.create_command())]:
                with self.assertRaises(WorkRepositoryError):
                    callback()
            self.assertEqual(self.worker.repository.path.read_bytes(), before)

    def test_unknown_source_or_case_is_not_found_without_a_partial_create(self):
        before = self.worker.repository.path.read_bytes()
        command = self.create_command()
        command["source_item_id"] = "f" * 64
        with self.assertRaises(FollowupNotFound):
            self.service.execute(command)
        with self.assertRaises(FollowupNotFound):
            self.service.overview({"id": "f" * 32})
        self.assertEqual(self.worker.repository.path.read_bytes(), before)

    def test_same_uid_in_another_account_is_a_different_case(self):
        first = self.create()
        other = observed(account="account-b")
        # Fixture writes only an already assessed card, never contacts a mailbox.
        item = copy.deepcopy(self.initial["items"][self.message.item_id])
        item["account"] = other.account
        self.worker._update(lambda d: d["items"].__setitem__(other.item_id, item))
        command = self.create_command("create-other-0001")
        command["source_item_id"] = other.item_id
        second = self.service.execute(command)["followup"]
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(len(self.service.overview()["active"]), 2)

    def test_corrupt_record_or_operation_is_never_silently_repaired(self):
        value = self.create()
        original = self.worker.status()
        def broken_fields(document):
            document["followups"]["items"][value["id"]].pop("check_at")
        self.worker._update(broken_fields)
        before = self.worker.repository.path.read_bytes()
        with self.assertRaises(WorkRepositoryError):
            self.service.overview()
        self.assertEqual(self.worker.repository.path.read_bytes(), before)
        self.worker.repository.transact(lambda _: RepositoryMutation(original))
        self.worker._update(lambda d: d["followups"]["operations"].update({"create-0001": None}))
        before = self.worker.repository.path.read_bytes()
        with self.assertRaises(WorkRepositoryError):
            self.service.execute(self.create_command())
        self.assertEqual(self.worker.repository.path.read_bytes(), before)

    def test_nonimportant_or_unfinished_source_is_not_automatically_promoted(self):
        for changes in [{"status": "analysis_failed"}, {"proposal": {"important": False}}]:
            self.worker._update(lambda d: d["items"][self.message.item_id].update(changes))
            before = self.worker.repository.path.read_bytes()
            with self.assertRaises(FollowupConflict):
                self.service.execute(self.create_command())
            self.assertEqual(self.worker.repository.path.read_bytes(), before)

    def test_editing_overdue_goal_does_not_silently_move_check_time(self):
        first = self.create()
        self.now += timedelta(days=4)
        value = self.service.execute(self.update_command(first, goal="Získat opravenou nabídku"))["followup"]
        self.assertEqual(value["check_at"], first["check_at"])
        self.assertEqual(value["generation"], 1)
