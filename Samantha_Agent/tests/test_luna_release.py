from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.communication import luna_release as release


TARGET = "b" * 40
ORIGIN = "a" * 40
STAMP = "c" * 16


class FakeService:
    active_workstream_id = "project-cockpit"

    def __init__(self):
        self.hub = SimpleNamespace(
            snapshot=lambda: {"thread_id": "original-parent-thread", "connected": True},
            send=Mock(return_value={"ok": True}),
        )
        self.active_service = SimpleNamespace(hub=self.hub, connect=Mock())
        self._assert_all_profile_sessions_idle = Mock()
        self.batch = {"ok": True, "state": "ready", "local_head": TARGET,
                      "origin_head": ORIGIN, "commit_count": 7}

    def audit_github_batch(self):
        return dict(self.batch)

    def audit_simple_main_deployment(self):
        return {"ok": True, "ready": True, "main_head": TARGET,
                "expected_code_stamp": STAMP, "workstream_id": "project-cockpit"}


class LunaReleaseTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = release.LunaReleaseStore(Path(self.directory.name) / "private")
        self.service = FakeService()
        self.launcher = Mock()

    def create(self, **changes):
        payload = {"confirmation": release.CONFIRMATION, "client_message_id": "release-request-123",
                   "expected_origin_head": ORIGIN, "expected_local_head": TARGET,
                   "dry_run": False, "user_text": "vše p+n", **changes}
        result = release.start_release(payload, service=self.service, store=self.store,
                                       launcher=self.launcher)
        return self.store.load(result["job"]["job_id"])

    def fake_api(self, *, fail_at="", disconnect_deploy=False, bad_stamp=False):
        calls = []
        pushes = 0
        health_reads = 0

        def call(path, payload=None, **kwargs):
            nonlocal pushes, health_reads
            calls.append(path)
            if path == fail_at:
                raise TimeoutError("private-secret-must-not-leak")
            if path.endswith("github-batch-audit"):
                return {"ok": True, "state": "aligned" if pushes else "ready", "local_head": TARGET,
                        "origin_head": TARGET if pushes else ORIGIN, "commit_count": 0 if pushes else 7}
            if path.endswith("github-batch"):
                self.assertEqual(payload["expected_local_head"], TARGET)
                self.assertEqual(payload["expected_origin_head"], ORIGIN)
                pushes += 1
                return {"ok": True, "pushed": True, "gate": {"test_count": 2000, "passed": True, "mode": "full"}}
            if path.endswith("server/health"):
                health_reads += 1
                return {"server": {"pid": 10 if health_reads == 1 else 11,
                                   "code_stamp": "wrong" if bad_stamp else STAMP}}
            if path.endswith("deploy-audit"):
                return {"ok": True, "ready": True, "main_head": TARGET, "expected_code_stamp": STAMP,
                        "workstream_id": "project-cockpit"}
            if path.endswith("/deploy"):
                if disconnect_deploy:
                    raise ConnectionError("restart")
                return {"ok": True, "state": "pending_restart"}
            if path.endswith("deploy-verification"):
                return {"ok": True, "state": "deployed", "main_head": TARGET,
                        "smoke": {"check_count": 5}}
            if path.endswith("luna-release/return"):
                return release.return_release(payload, token=kwargs["token"],
                                              service=self.service, store=self.store)
            self.fail(path)

        return call, calls

    def run_job(self, job, **kwargs):
        accept = Mock(return_value={"accepted": True, "model": release.MODEL, "target_head": TARGET})
        result = release.run_release(job["job_id"], store=self.store, accept=accept,
                                     protect=lambda: {"camino_pid": 99, "autosave_pids": [98]},
                                     pause=lambda _: None, **kwargs)
        self.assertEqual(accept.call_args.args[0]["commit_count"], 7)
        self.assertNotIn("token", accept.call_args.args[0])
        self.assertNotIn("parent_thread_id", accept.call_args.args[0])
        return result

    def test_whole_batch_is_frozen_and_sensitive_fields_are_private(self):
        job = self.create()
        self.assertEqual(job["commit_count"], 7)
        self.assertEqual(job["target_head"], TARGET)
        self.assertEqual(self.launcher.call_count, 1)
        self.assertTrue(self.launcher.call_args.kwargs["start_new_session"])
        self.assertEqual((self.store.root / f"{job['job_id']}.json").stat().st_mode & 0o777, 0o600)
        self.assertNotIn(job["token"], json.dumps(release.public_job(job)))
        self.assertNotIn("parent_thread_id", release.public_job(job))

    def test_missing_confirmation_changed_head_and_invalid_mode_do_not_launch(self):
        for changes in ({"confirmation": "ano"}, {"expected_local_head": "d" * 40}, {"dry_run": "false"}):
            with self.subTest(changes=changes), self.assertRaises(release.LunaReleaseError):
                self.create(**changes)
        self.launcher.assert_not_called()

    def test_other_workstream_and_empty_batch_are_rejected(self):
        self.service.active_workstream_id = "project-camino"
        with self.assertRaises(release.LunaReleaseError):
            self.create()
        self.service.active_workstream_id = "project-cockpit"
        self.service.batch.update(state="aligned", commit_count=0)
        with self.assertRaises(release.LunaReleaseError):
            self.create()
        self.launcher.assert_not_called()

    def test_missing_original_conversation_cannot_start_release(self):
        self.service.hub.snapshot = lambda: {"thread_id": "", "connected": False}
        with self.assertRaises(release.LunaReleaseError):
            self.create()
        self.launcher.assert_not_called()

    def test_same_request_is_idempotent_but_cannot_change_scope(self):
        job = self.create()
        self.assertEqual(self.create()["job_id"], job["job_id"])
        self.assertEqual(self.launcher.call_count, 1)
        with self.assertRaises(release.LunaReleaseError):
            self.create(dry_run=True)
        with self.assertRaises(release.LunaReleaseError):
            self.create(client_message_id="another-request-123")

    def test_dry_run_calls_luna_without_any_publication_or_parent_turn(self):
        job = self.create(dry_run=True)
        call = Mock(side_effect=AssertionError("dry-run must not call publication API"))
        result = self.run_job(job, call=call)
        self.assertEqual(result["job"]["state"], "dry_run_completed")
        call.assert_not_called()
        self.service.hub.send.assert_not_called()

    def test_failed_dry_run_also_never_calls_publication_or_parent(self):
        job = self.create(dry_run=True)
        call = Mock(side_effect=AssertionError("dry-run must stay local"))
        result = release.run_release(job["job_id"], store=self.store, call=call,
                                     accept=Mock(side_effect=release.LunaReleaseError("Předání odmítnuto.")))
        self.assertEqual(result["job"]["state"], "attention")
        call.assert_not_called()
        self.service.hub.send.assert_not_called()

    def test_terminal_agent_returns_to_its_caller_without_inserting_a_different_chat(self):
        call, calls = self.fake_api()
        started = release.start_terminal_release({
            "confirmation": release.CONFIRMATION, "client_message_id": "native-release-123",
            "expected_origin_head": ORIGIN, "expected_local_head": TARGET, "dry_run": False,
        }, store=self.store, call=call, launcher=self.launcher)
        job = self.store.load(started["job"]["job_id"])
        self.assertEqual(job["return_channel"], "caller")
        self.assertEqual(job["parent_thread_id"], "")
        result = self.run_job(job, call=call)
        self.assertTrue(result["ok"])
        self.assertNotIn("/api/human-adam/luna-release/return", calls)
        self.service.hub.send.assert_not_called()

    def test_http_payload_cannot_redirect_return_channel(self):
        job = self.create(return_channel="caller")
        self.assertEqual(job["return_channel"], "cockpit")

    def test_success_survives_store_reload_and_returns_once_to_read_only_parent(self):
        job = self.create()
        call, calls = self.fake_api()
        result = self.run_job(job, call=call)
        self.assertTrue(result["ok"])
        self.assertTrue(result["job"]["returned_to_adam"])
        self.assertEqual(result["job"]["gate"]["mode"], "full")
        self.assertEqual(result["job"]["verification"]["smoke_count"], 5)
        self.assertEqual(calls.count("/api/human-adam/github-batch"), 1)
        self.assertEqual(calls.count("/api/human-adam/deploy"), 1)
        self.assertEqual(self.service.hub.send.call_count, 1)
        kwargs = self.service.hub.send.call_args.kwargs
        self.assertTrue(kwargs["read_only"])
        self.assertEqual(kwargs["text"], "vše p+n")
        self.assertNotIn(job["token"], kwargs["model_input_text"])
        self.assertEqual(release.LunaReleaseStore(self.store.root).load()["state"], "completed")
        release.run_release(job["job_id"], store=self.store, call=Mock(side_effect=AssertionError()))
        self.assertEqual(self.service.hub.send.call_count, 1)

    def test_deploy_transport_interruption_is_verified_without_restarting_again(self):
        job = self.create()
        call, calls = self.fake_api(disconnect_deploy=True)
        result = self.run_job(job, call=call)
        self.assertTrue(result["ok"])
        self.assertEqual(calls.count("/api/human-adam/deploy"), 1)

    def test_unknown_push_result_is_handed_back_without_retry_or_deployment(self):
        job = self.create()
        call, calls = self.fake_api(fail_at="/api/human-adam/github-batch")
        result = self.run_job(job, call=call)
        self.assertEqual(result["job"]["state"], "attention")
        self.assertEqual(result["job"]["push_state"], "uncertain")
        self.assertEqual(result["job"]["failure_phase"], "push_requested")
        self.assertEqual(calls.count("/api/human-adam/github-batch"), 1)
        self.assertNotIn("/api/human-adam/deploy", calls)
        self.assertTrue(result["job"]["returned_to_adam"])
        self.assertNotIn("private-secret", json.dumps(result))
        self.assertNotIn("private-secret", self.service.hub.send.call_args.kwargs["model_input_text"])

    def test_wrong_new_process_stamp_does_not_replay_deploy(self):
        job = self.create()
        call, calls = self.fake_api(bad_stamp=True)
        result = self.run_job(job, call=call)
        self.assertEqual(result["job"]["state"], "attention")
        self.assertEqual(result["job"]["failure_message"],
                         "Nový proces s předaným kódem nebyl potvrzený.")
        self.assertIn(result["job"]["failure_message"],
                      self.service.hub.send.call_args.kwargs["model_input_text"])
        self.assertEqual(calls.count("/api/human-adam/deploy"), 1)
        self.assertNotIn("/api/human-adam/deploy-verification", calls)

    def test_changed_target_after_luna_acceptance_cannot_push(self):
        job = self.create()
        call = Mock(return_value={"local_head": "d" * 40, "origin_head": ORIGIN})
        result = self.run_job(job, call=call)
        self.assertEqual(result["job"]["state"], "attention")
        self.assertFalse(any(args.args[0].endswith("/github-batch") for args in call.call_args_list))

    def test_nonce_and_phase_guard_block_other_writes(self):
        job = self.create()
        for path in ("/api/human-adam/send", "/api/cockpit/restart", "/api/human-adam/deploy"):
            with self.subTest(path=path), self.assertRaises(release.LunaReleaseError):
                release.authorize_job_call(self.store, path, job["token"])
        self.store.update(job["job_id"], phase="push_requested")
        release.authorize_job_call(self.store, "/api/human-adam/github-batch", job["token"])
        with self.assertRaises(release.LunaReleaseError):
            release.authorize_job_call(self.store, "/api/human-adam/github-batch", "wrong")

    def test_return_does_not_create_or_choose_another_parent_thread(self):
        job = self.create()
        self.store.update(job["job_id"], state="returning", phase="return")
        self.service.hub.snapshot = lambda: {"thread_id": "different-thread", "connected": False}
        with self.assertRaises(release.LunaReleaseError):
            release.return_release({"job_id": job["job_id"]}, token=job["token"],
                                   service=self.service, store=self.store)
        self.service.active_service.connect.assert_not_called()
        self.service.hub.send.assert_not_called()

    def test_return_failure_after_dispatch_is_not_sent_to_parent_again(self):
        job = self.create()
        self.store.update(job["job_id"], state="returning", phase="return")
        self.service.hub.send.side_effect = RuntimeError("transport uncertainty")
        for _ in range(2):
            with self.assertRaises((RuntimeError, release.LunaReleaseError)):
                release.return_release({"job_id": job["job_id"]}, token=job["token"],
                                       service=self.service, store=self.store)
        self.assertEqual(self.service.hub.send.call_count, 1)

    def test_worker_lease_prevents_parallel_runs(self):
        job = self.create()
        with self.store.lock("worker"), self.assertRaises(BlockingIOError):
            release.run_release(job["job_id"], store=self.store)

    def test_dead_worker_becomes_attention_without_replaying_work(self):
        job = self.create()
        self.store.update(job["job_id"], queued_epoch=time.time() - 60, phase="push_requested")
        status = self.store.status()
        self.assertEqual(status["job"]["state"], "attention")
        self.assertNotIn("token", status["job"])
        self.assertEqual(self.launcher.call_count, 1)

    def test_status_preserves_completion_between_initial_read_and_worker_lease(self):
        job = self.create()
        stale = self.store.update(job["job_id"], queued_epoch=time.time() - 60)
        completed = self.store.update(job["job_id"], state="completed", phase="done",
                                      pushed=True, deployed=True)
        with patch.object(self.store, "load", side_effect=[stale, completed]):
            status = self.store.status()
        self.assertEqual(status["job"]["state"], "completed")
        self.assertEqual(self.store.load()["state"], "completed")

    def test_corrupt_receipt_cannot_disable_the_guard(self):
        job = self.create()
        (self.store.root / f"{job['job_id']}.json").write_text("{}")
        with self.assertRaises(release.LunaReleaseError):
            release.authorize_job_call(self.store, "/api/human-adam/send", "")

    def test_http_guard_blocks_new_turn_but_allows_only_owned_release_phase(self):
        from tests.test_cockpit_http_security import running_cockpit_server, request_json
        job = self.create()
        with running_cockpit_server() as (host, port, _logger), \
                patch("app.cockpit.COCKPIT_PORT", port), \
                patch("app.cockpit.HUMAN_ADAM", self.service), \
                patch("app.cockpit.luna_release.LunaReleaseStore", return_value=self.store), \
                patch("app.cockpit.human_adam_send_action") as send, \
                patch("app.cockpit.human_adam_github_batch_action", return_value={"ok": True}) as push:
            headers = {"Content-Type": "application/json", "Origin": f"http://{host}:{port}"}
            status, result, _ = request_json(host, port, "POST", "/api/human-adam/send",
                                             body="{}", headers=headers)
            self.assertEqual(status, 409)
            self.assertFalse(result["ok"])
            send.assert_not_called()
            self.store.update(job["job_id"], phase="push_requested")
            status, _, _ = request_json(host, port, "POST", "/api/human-adam/github-batch",
                                         body="{}", headers={**headers, "X-Luna-Release": job["token"]})
            self.assertEqual(status, 200)
            self.assertEqual(push.call_count, 1)
            status, _, _ = request_json(host, port, "POST", "/api/human-adam/github-batch",
                                         body="{}", headers=headers)
            self.assertEqual(status, 409)
            self.assertEqual(push.call_count, 1)
            self.store.update(job["job_id"], phase="deploy_requested")
            with patch("app.cockpit.human_adam_simple_main_deployment_action", return_value={"ok": True}) as deploy:
                status, _, _ = request_json(host, port, "POST", "/api/human-adam/deploy",
                    body=json.dumps({"confirmation": "POTVRZUJI NASAZENI AKTUALNIHO MAIN DO COCKPITU",
                                     "expected_head": "d" * 40}),
                    headers={**headers, "X-Luna-Release": job["token"]})
                self.assertEqual(status, 200)
                self.assertEqual(deploy.call_args.kwargs["expected_head"], TARGET)

    def test_noncanonical_http_instance_cannot_launch_production_release(self):
        from tests.test_cockpit_http_security import running_cockpit_server, request_json
        with running_cockpit_server() as (host, port, _logger), \
                patch("app.cockpit.human_adam_luna_release_start_action") as start:
            status, _, _ = request_json(host, port, "POST", "/api/human-adam/luna-release/start",
                                        body="{}", headers={"Content-Type": "application/json",
                                                            "Origin": f"http://{host}:{port}"})
            self.assertEqual(status, 409)
            start.assert_not_called()

    def test_accept_handoff_uses_only_luna_read_only_and_matching_structured_target(self):
        client = Mock()
        client.__enter__ = Mock(return_value=client)
        client.__exit__ = Mock(return_value=False)
        client.list_models.return_value = [{"model": release.MODEL}]
        client.start_thread.return_value = "luna-thread"
        client.send_text.return_value = SimpleNamespace(answer=json.dumps({"action": "accept", "target_head": TARGET, "message": "Přebírám."}))
        result = release.accept_handoff({"target_head": TARGET, "commit_count": 7}, client_factory=lambda: client)
        self.assertTrue(result["accepted"])
        self.assertEqual(client.start_thread.call_args.kwargs["model"], release.MODEL)
        self.assertTrue(client.start_thread.call_args.kwargs["ephemeral"])
        self.assertEqual(client.send_text.call_args.kwargs["sandbox_policy"], {"type": "readOnly", "networkAccess": False})
        client.send_text.return_value.answer = json.dumps({"action": "accept", "target_head": ORIGIN})
        with self.assertRaises(release.LunaReleaseError):
            release.accept_handoff({"target_head": TARGET}, client_factory=lambda: client)


if __name__ == "__main__":
    unittest.main()
