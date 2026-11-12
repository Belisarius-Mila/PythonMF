from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.communication.human_adam_work_state import build_human_adam_work_state

SCOPE = "layer-human-adam-development"
AT = "2026-11-12T09:00:00+00:00"
BEFORE = "2026-11-12T08:00:00+00:00"
AFTER = "2026-11-12T08:30:00+00:00"
HEAD = "a" * 40


def message(**changes):
    return dict(client_message_id="request-current", thread_id="thread-current",
                received_at=BEFORE, completed_at=AFTER, status="completed",
                delivery_confirmed=True, user_text="PRIVATE_TEXT", answer="PRIVATE_TEXT") | changes


def session(**changes):
    return dict(thread_id="thread-current", connected=True, turn_busy=False,
                updated_at=AFTER, messages=[message()], active_turn=None) | changes


def completion(**changes):
    return dict(schema_version=1, server_authoritative=True, workstream_id=SCOPE,
                client_message_id="request-current", state="checkpoint_completed",
                updated_at=AFTER, summary="PRIVATE_TEXT") | changes


def release(**changes):
    return dict(workstream_id=SCOPE, job_id="release-current", state="completed",
                active=False, created_at=AFTER, updated_at=AT,
                deployment_target="github_pages", target_short=HEAD[:12], dry_run=False,
                message="PRIVATE_TEXT", token="PRIVATE_TEXT", verification={}) | changes


def build(**changes):
    return build_human_adam_work_state(**(dict(
        workstream_id=SCOPE, observed_at=AT, session_snapshot=session(),
        runtime_snapshot={"reachable": True},
    ) | changes))


class WorkStateTests(unittest.TestCase):
    def test_idle_connected_is_ready_and_does_not_grant_mutations(self):
        result = build()
        self.assertEqual(result["summary"]["state"], "ready")
        self.assertEqual(result["actions"], {"refresh_status": True, "inspect_work": True,
                                           "steer": False, "interrupt": False})
        self.assertEqual(result["model"]["state"], "idle")
        self.assertNotIn("PRIVATE_TEXT", json.dumps(result))

    def test_running_model_has_priority_over_old_attention_and_completion(self):
        result = build(session_snapshot=session(turn_busy=True, active_turn={"client_message_id": "request-current", "started_at": BEFORE},
            messages=[message(status="pending", delivery_confirmed=False)]),
            completion_snapshot=completion(client_message_id="request-old"),
            release_snapshot=release(state="attention"))
        self.assertEqual(result["summary"]["state"], "running")
        self.assertEqual(result["publication"]["state"], "recorded")
        self.assertTrue(any(i["code"] == "receipt_attention" for i in result["incidents"]))
        self.assertEqual(result["summary"]["operation_id"], result["model"]["operation"]["operation_id"])

    def test_wrong_active_request_is_unverified(self):
        result = build(session_snapshot=session(turn_busy=True, active_turn={"client_message_id": "wrong"}))
        self.assertEqual(result["summary"]["state"], "unverified")
        self.assertIsNone(result["model"]["operation"])

    def test_latest_message_from_other_thread_does_not_replace_current_one(self):
        result = build(session_snapshot=session(messages=[message(), message(thread_id="another", status="delivery_unknown")]))
        self.assertEqual(result["summary"]["state"], "ready")

    def test_unknown_delivery_survives_disconnection_without_becoming_running(self):
        result = build(session_snapshot=session(connected=False, messages=[message(status="delivery_unknown", delivery_confirmed=False)]))
        self.assertEqual(result["connection"]["state"], "disconnected")
        self.assertEqual(result["summary"]["state"], "unverified")

    def test_old_unknown_delivery_is_history_after_new_completed_request(self):
        result = build(session_snapshot=session(messages=[message(client_message_id="old", status="delivery_unknown"), message()]))
        self.assertEqual(result["summary"]["state"], "ready")

    def test_completion_waits_for_confirmed_model_result_and_same_request(self):
        job = dict(workstream_id=SCOPE, client_message_id="request-current", state="running", updated_at=AFTER)
        result = build(completion_job_snapshot=job)
        self.assertEqual(result["summary"]["state"], "verifying")
        self.assertEqual(result["completion"]["operation"]["parent_operation_id"], result["history"][0]["operation_id"])
        for other in [job | {"client_message_id": "old"}, job | {"updated_at": "2020-01-01T00:00:00Z"}, job | {"workstream_id": "project-other"}]:
            with self.subTest(other=other):
                self.assertNotEqual(build(completion_job_snapshot=other)["completion"]["state"], "verifying")
        self.assertNotEqual(build(completion_job_snapshot=job,session_snapshot=session(messages=[message(delivery_confirmed=False)]))["completion"]["state"],"verifying")

    def test_newer_completion_record_wins_over_old_job(self):
        result = build(completion_snapshot=completion(state="receipt_accepted"), completion_job_snapshot={
            "workstream_id": SCOPE, "client_message_id": "old", "state": "completed", "updated_at": BEFORE})
        self.assertEqual(result["completion"]["state"], "verifying")

    def test_foreign_records_are_not_returned_as_history_or_incidents(self):
        result = build(completion_snapshot=completion(workstream_id="project-other"), release_snapshot=release(workstream_id="project-other"))
        self.assertEqual([r["kind"] for r in result["history"]], ["model"])
        self.assertFalse(result["incidents"])

    def test_active_publication_is_explicitly_receipt_reported_not_live_verified(self):
        result = build(release_snapshot=release(state="running", active=True))
        self.assertEqual(result["summary"]["state"], "publication_reported")
        self.assertEqual(result["publication"]["operation"]["liveness"], "not_checked")
        self.assertIsNone(result["publication"]["operation"]["client_request_id"])
        self.assertEqual(result["publication"]["outcome"], "unverified")

    def test_old_reported_release_does_not_become_current_work(self):
        result = build(release_snapshot=release(state="running", active=True,created_at="2020-01-01T00:00:00Z"))
        self.assertEqual(result["summary"]["state"], "ready")
        self.assertEqual(result["publication"]["state"], "recorded")

    def test_current_empty_conversation_can_report_its_new_release(self):
        result = build(session_snapshot=session(messages=[]),release_snapshot=release(state="queued",active=True))
        self.assertEqual(result["summary"]["state"],"publication_reported")

    def test_later_exact_deployment_evidence_does_not_rewrite_attention_receipt(self):
        source = release(state="attention", verification={"state":"deployed", "main_head":HEAD,
            "deployment_target":"github_pages", "deployment_id":42,"smoke_http_status":200})
        before = copy.deepcopy(source)
        result = build(release_snapshot=source)
        self.assertEqual(result["publication"]["outcome"], "deployment_verified")
        self.assertEqual(result["publication"]["operation"]["state"], "attention")
        self.assertEqual(source,before)
        self.assertTrue(any(i["code"]=="receipt_attention_verified_deployment" for i in result["incidents"]))

    def test_wrong_head_target_or_smoke_cannot_confirm_publication(self):
        good={"state":"deployed","main_head":HEAD,"deployment_target":"github_pages","deployment_id":42,"smoke_http_status":200}
        for patch_value in [{"main_head":"b"*40},{"deployment_target":"cockpit"},{"deployment_id":True},{"smoke_http_status":503}]:
            self.assertEqual(build(release_snapshot=release(verification=good|patch_value))["publication"]["outcome"],"unverified")

    def test_dry_run_never_confirms_a_deployment(self):
        result=build(release_snapshot=release(dry_run=True,state="dry_run_completed",verification={
            "state":"deployed","main_head":HEAD,"deployment_target":"github_pages","deployment_id":42,"smoke_http_status":200}))
        self.assertEqual(result["publication"]["outcome"],"dry_run_completed")

    def test_future_publication_is_unverified(self):
        result=build(release_snapshot=release(updated_at="2027-01-01T00:00:00Z"))
        self.assertEqual(result["publication"]["state"],"unverified")

    def test_revision_is_stable_when_only_observation_time_changes(self):
        first=build();second=build(observed_at="2026-11-12T10:00:00Z")
        self.assertEqual(first["revision"],second["revision"])
        self.assertNotEqual(first["observed_at"],second["observed_at"])
        self.assertNotEqual(first["revision"],build(session_snapshot=session(connected=False))["revision"])

    def test_scope_change_invalidates_all_current_operations(self):
        result=build(snapshot_consistent=False,release_snapshot=release(state="running",active=True))
        self.assertFalse(result["consistent"])
        self.assertEqual(result["summary"]["state"],"unverified")
        self.assertIsNone(result["summary"]["operation_id"])
        self.assertFalse(result["history"])

    def test_bad_source_is_separate_from_no_work(self):
        result=build(source_errors=("session","publication"))
        self.assertEqual(result["summary"]["state"],"unverified")
        self.assertEqual(len([i for i in result["incidents"] if i["code"]=="source_unavailable"]),2)
        self.assertEqual(build(source_errors=("publication",))["summary"]["state"],"unverified")

    def test_inputs_are_unchanged_and_raw_fields_are_not_exported(self):
        values={"session_snapshot":session(),"completion_snapshot":completion(),"release_snapshot":release()}
        before=copy.deepcopy(values)
        result=build(**values)
        self.assertEqual(values,before)
        self.assertNotIn("PRIVATE_TEXT",json.dumps(result))

    def test_unknown_state_or_bad_field_types_do_not_leak_source_text(self):
        result=build(completion_snapshot=completion(state="PRIVATE_TEXT"),release_snapshot=release(state="PRIVATE_TEXT"),
                     session_snapshot=session(messages=[message(status=[])]))
        self.assertNotIn("PRIVATE_TEXT",json.dumps(result))
        self.assertEqual(result["publication"]["operation"]["state"],"unverified")

    def test_future_completion_cannot_be_verifying(self):
        result=build(completion_snapshot=completion(state="receipt_accepted",updated_at="2027-01-01T00:00:00Z"))
        self.assertNotEqual(result["completion"]["state"],"verifying")

    def test_confirmed_delivery_and_connection_generation_are_independent(self):
        result=build(session_snapshot=session(connection_generation=2,messages=[message(delivery_confirmed=False)]))
        self.assertEqual(result["connection"]["state"],"connected")
        self.assertEqual(result["model"]["state"],"unverified")
        self.assertEqual(result["scope"]["connection_generation"],2)

    def test_future_model_start_cannot_claim_running(self):
        result=build(session_snapshot=session(turn_busy=True,messages=[message(status="pending")],
            active_turn={"client_message_id":"request-current","started_at":"2027-01-01T00:00:00Z"}))
        self.assertEqual(result["model"]["state"],"unverified")

    def test_invalid_scope_or_clock_is_fail_closed(self):
        for overrides in [{"workstream_id":"/private/path"},{"observed_at":"not a clock"}]:
            self.assertFalse(build(**overrides)["consistent"])


class WorkStateIntegrationTests(unittest.TestCase):
    def test_status_adds_projection_without_release_recovery_or_source_writes(self):
        from tests import test_human_adam_profiles as fixtures
        from app.communication.luna_release import LunaReleaseStore
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            manager,*_=fixtures.HumanAdamProfileManagerTests().make_manager(root)
            try:
                manager.status()  # Existing manager bootstrap is outside the new projection.
                before={str(p.relative_to(root)):(p.read_bytes(),p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file()}
                with patch.object(LunaReleaseStore,"status",side_effect=AssertionError("mutating recovery")):
                    result=manager.status()
                after={str(p.relative_to(root)):(p.read_bytes(),p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file()}
                self.assertEqual(before,after)
                projection=result["work_state"]
                self.assertEqual(projection["scope"]["workstream_id"],SCOPE)
                self.assertTrue(projection["read_only"])
                self.assertFalse(projection["writes_performed"])
            finally:manager.close()

    def test_corrupt_release_receipt_does_not_break_session_status(self):
        from tests import test_human_adam_profiles as fixtures
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);manager,*_=fixtures.HumanAdamProfileManagerTests().make_manager(root)
            try:
                folder=root/"luna_release";folder.mkdir();(folder/"current.json").write_text("bad-json")
                result=manager.status()
                self.assertTrue(result["ok"])
                self.assertIn({"source":"publication","code":"source_unavailable"},result["work_state"]["incidents"])
            finally:manager.close()

    def test_thread_rotation_during_collection_invalidates_projection(self):
        from tests import test_human_adam_profiles as fixtures
        with tempfile.TemporaryDirectory() as directory:
            manager,*_=fixtures.HumanAdamProfileManagerTests().make_manager(Path(directory))
            try:
                payload=manager.status();service=manager.active_service
                service.hub.thread_id="rotated-thread"
                result=manager._project_work_state(payload,SCOPE,service)
                self.assertFalse(result["consistent"])
                self.assertEqual(result["summary"]["state"],"unverified")
            finally:manager.close()

    def test_new_message_during_collection_cannot_reactivate_an_old_snapshot(self):
        from tests import test_human_adam_profiles as fixtures
        with tempfile.TemporaryDirectory() as directory:
            manager,*_=fixtures.HumanAdamProfileManagerTests().make_manager(Path(directory))
            try:
                payload=manager.status();service=manager.active_service
                service.hub.messages.append(message(client_message_id="newer-request"))
                result=manager._project_work_state(payload,SCOPE,service)
                self.assertFalse(result["consistent"])
                self.assertIsNone(result["summary"]["operation_id"])
            finally:manager.close()
