"""One compact operation preserves the existing exact-batch release protocol."""
import json
from pathlib import Path
import threading
import unittest
from unittest.mock import Mock, patch

from app.communication import luna_release as release
from app.communication.human_adam_workstream_catalog import WORKSTREAM_CATALOG
from tests import test_luna_release as fixtures


class ReleaseSubmissionTests(unittest.TestCase):
    def setUp(self):
        fixtures.LunaReleaseTests.setUp(self)
        self.payload = {"confirmation": release.CONFIRMATION,
                        "client_message_id": "compact-release-123",
                        "expected_workstream_id": "project-cockpit", "expected_local_head": fixtures.TARGET,
                        "dry_run": False}

    def submit(self, **kwargs):
        return release.submit_release(self.payload, service=self.service, store=self.store,
                                      launcher=self.launcher, **kwargs)

    def test_compact_request_freezes_entire_batch_role_and_target(self):
        result = self.submit()
        job = self.store.load(result["job"]["job_id"])
        self.assertEqual(job["commit_count"], 7)
        self.assertEqual(job["origin_head"], fixtures.ORIGIN)
        self.assertEqual(job["target_head"], fixtures.TARGET)
        self.assertEqual(job["executor"], fixtures.EXECUTOR)
        self.assertEqual(job["return_channel"], "cockpit")
        self.assertEqual(job["parent_thread_id"], "original-parent-thread")
        self.launcher.assert_called_once()
        self.assertNotIn("token", json.dumps(result))

    def test_confirmation_schema_and_wait_limits_block_before_audit(self):
        for change in ({"confirmation": ""}, {"client_message_id": ""}, {"dry_run": 1},
                       {"return_channel": "caller"}, {"model": "unreviewed"}, {"expected_local_head": ""}):
            with self.subTest(change=change), patch.object(release, "audit_release") as audit:
                with self.assertRaises(release.LunaReleaseError):
                    release.submit_release({**self.payload, **change}, service=self.service,
                                           store=self.store, launcher=self.launcher)
                audit.assert_not_called()
        with self.assertRaises(release.LunaReleaseError):
            self.submit(wait=True, timeout=-1)
        self.launcher.assert_not_called()

    def test_wrong_project_or_unknown_target_cannot_be_guessed(self):
        for project in ("project-mmtx", "unknown-project"):
            with self.subTest(project=project), self.assertRaises(release.LunaReleaseError):
                release.submit_release({**self.payload, "expected_workstream_id": project},
                                       service=self.service, store=self.store, launcher=self.launcher)
        self.launcher.assert_not_called()

    def test_existing_ui_pins_are_binding(self):
        for pin in ({"expected_local_head": "d" * 40}, {"expected_origin_head": "d" * 40},
                    {"expected_deployment_target": "github_pages"},
                    {"expected_executor": {**fixtures.EXECUTOR, "policy_digest": "0" * 64}}):
            with self.subTest(pin=pin), self.assertRaises(release.LunaReleaseError):
                release.submit_release({**self.payload, **pin}, service=self.service,
                                       store=self.store, launcher=self.launcher)
        self.launcher.assert_not_called()

    def test_existing_complete_ui_payload_is_compatible(self):
        result = release.submit_release({**self.payload, "expected_local_head": fixtures.TARGET,
            "expected_origin_head": fixtures.ORIGIN, "expected_deployment_target": "cockpit",
            "expected_executor": fixtures.EXECUTOR, "user_text": "p+n"},
            service=self.service, store=self.store, launcher=self.launcher)
        self.assertEqual(result["job"]["state"], "queued")
        self.launcher.assert_called_once()

    def test_existing_locked_start_still_rechecks_concurrent_source_drift(self):
        original = release.audit_release
        count = 0

        def audit(*args, **kwargs):
            nonlocal count
            count += 1
            result = original(*args, **kwargs)
            if count == 1:
                self.service.batch["local_head"] = "d" * 40
            return result

        with patch.object(release, "audit_release", side_effect=audit):
            with self.assertRaises(release.LunaReleaseError):
                self.submit()
        self.assertEqual(count, 2)
        self.launcher.assert_not_called()

    def test_same_request_returns_original_receipt_after_origin_advances_without_new_audit(self):
        first = self.submit()
        self.service.batch.update(state="aligned", origin_head=fixtures.TARGET, commit_count=0)
        with patch.object(release, "audit_release", side_effect=AssertionError("second audit")):
            again = self.submit()
        self.assertEqual(first, again)
        self.launcher.assert_called_once()

    def test_same_identity_cannot_change_mode_target_or_original_thread(self):
        self.submit()
        with self.assertRaises(release.LunaReleaseError):
            release.submit_release({**self.payload, "dry_run": True}, service=self.service,
                                   store=self.store, launcher=self.launcher)
        self.service.hub.snapshot = lambda: {"thread_id": "different-thread"}
        with self.assertRaises(release.LunaReleaseError):
            self.submit()
        self.launcher.assert_called_once()

    def test_all_registered_nonarchived_streams_use_the_same_operation(self):
        for record in WORKSTREAM_CATALOG:
            if record.mode == "archived":
                continue
            with self.subTest(project=record.workstream_id):
                self.service.active_workstream_id = record.workstream_id
                store = release.LunaReleaseStore(Path(self.directory.name) / record.workstream_id)
                result = release.submit_release({**self.payload, "expected_workstream_id": record.workstream_id},
                    service=self.service, store=store, launcher=self.launcher)
                job = store.load(result["job"]["job_id"])
                self.assertEqual(job["workstream_id"], record.workstream_id)
                self.assertEqual(job["deployment_target"], release.release_target(record.workstream_id))

    def test_native_one_call_runs_one_luna_and_returns_to_caller(self):
        call, calls = fixtures.LunaReleaseTests.fake_api(self)
        accept = Mock(return_value={"accepted": True, **fixtures.EXECUTOR, "target_head": fixtures.TARGET})
        worker_errors = []

        def worker(job_id):
            try:
                release.run_release(job_id, store=self.store, call=call, accept=accept,
                    protect=lambda: {"Camino": "unchanged", "autosave": "unchanged"}, pause=lambda _: None)
            except Exception as exc:
                worker_errors.append(exc)

        def launch(argv, **kwargs):
            thread = threading.Thread(target=worker, args=(argv[-1],), daemon=True)
            thread.start()
            self.addCleanup(thread.join, 5)

        result = release.submit_release(self.payload, store=self.store, call=call, launcher=launch, wait=True, timeout=5)
        self.assertEqual(worker_errors, [])
        self.assertEqual(result["job"]["state"], "completed")
        accept.assert_called_once()
        self.assertEqual(self.store.load(result["job"]["job_id"])["return_channel"], "caller")
        self.assertNotIn("/api/human-adam/luna-release/return", calls)
        self.service.hub.send.assert_not_called()

    def test_wait_is_pinned_even_when_current_pointer_changes(self):
        first = self.submit()["job"]["job_id"]
        self.store.update(first, state="completed")
        second = release.submit_release({**self.payload, "client_message_id": "second-release-123"},
            service=self.service, store=self.store, launcher=self.launcher)["job"]["job_id"]
        self.assertNotEqual(first, second)
        self.assertEqual(self.store.status(first)["job"]["job_id"], first)
        result = release.wait_for_release(first, store=self.store, timeout=1)
        self.assertEqual(result["job"]["job_id"], first)
        self.assertEqual(result["job"]["state"], "completed")

    def test_timeout_and_attention_never_relaunch_or_overwrite_the_job(self):
        job = self.submit()["job"]["job_id"]
        result = release.wait_for_release(job, store=self.store, timeout=.01, poll_interval=.01)
        self.assertTrue(result["timed_out"])
        self.assertEqual(self.store.load(job)["state"], "queued")
        self.store.update(job, state="attention")
        self.assertFalse(release.wait_for_release(job, store=self.store, timeout=1)["ok"])
        self.launcher.assert_called_once()

    def test_portal_handler_uses_the_shared_entrypoint(self):
        from app.cockpit import human_adam_luna_release_start_action
        with patch.object(release, "submit_release", return_value={"ok": True}) as submit:
            self.assertEqual(human_adam_luna_release_start_action(self.payload, service=self.service), {"ok": True})
        submit.assert_called_once_with(self.payload, service=self.service)


if __name__ == "__main__":
    unittest.main()
