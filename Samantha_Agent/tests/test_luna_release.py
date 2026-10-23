from __future__ import annotations

import json
import os
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
ROLE_POLICY = release.agent_roles.load_role()
ROLE_CANDIDATE = next(item for item in ROLE_POLICY["approved_models"] if item["model"] == ROLE_POLICY["preferred_model"])
ROLE_CATALOG = [{"model": ROLE_CANDIDATE["model"], "supportedReasoningEfforts": [{"reasoningEffort": ROLE_CANDIDATE["reasoning_effort"]}]}]
EXECUTOR = release.agent_roles.validate_selection(release.agent_roles.resolve_role(ROLE_CATALOG))


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
                "expected_code_stamp": STAMP, "workstream_id": self.active_workstream_id}


class LunaReleaseTests(unittest.TestCase):
    def test_service_query_forces_cli_only_for_tailscale_and_preserves_parent_environment(self):
        from scripts import camino_service_control as camino

        with patch.dict(os.environ, {"TAILSCALE_BE_CLI": "0"}), patch.object(release.subprocess, "run") as run:
            release._protected_service_query([camino.TAILSCALE, "serve", "status", "--json"])
            self.assertEqual(run.call_args.kwargs["env"]["TAILSCALE_BE_CLI"], "1")
            self.assertEqual(os.environ["TAILSCALE_BE_CLI"], "0")
            self.assertEqual(run.call_args.args[0], [camino.TAILSCALE, "serve", "status", "--json"])
            release._protected_service_query(["/bin/launchctl", "print", "owned-service"])
            self.assertNotIn("env", run.call_args.kwargs)

    def test_protection_failure_is_separate_from_a_successful_model_handoff(self):
        job = self.create(dry_run=True)
        calls = Mock()
        result = release.run_release(job["job_id"], store=self.store, call=calls,
            accept=Mock(return_value={**EXECUTOR,"accepted":True,"target_head":TARGET}),
            protect=Mock(side_effect=ValueError("private-network-details")))
        self.assertEqual(result["job"]["failure_phase"], "protection")
        self.assertEqual(result["job"]["push_state"], "not_started")
        self.assertNotIn("private-network-details", json.dumps(result))
        calls.assert_not_called()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = release.LunaReleaseStore(Path(self.directory.name) / "private")
        self.service = FakeService()
        resolver = patch.object(release, "resolve_release_executor", return_value=EXECUTOR)
        resolver.start()
        self.addCleanup(resolver.stop)
        self.launcher = Mock()

    def create(self, **changes):
        payload = {"confirmation": release.CONFIRMATION, "client_message_id": "release-request-123",
                   "expected_origin_head": ORIGIN, "expected_local_head": TARGET,
                   "dry_run": False, "user_text": "vše p+n", "expected_executor": EXECUTOR,
                   "expected_workstream_id": self.service.active_workstream_id,
                   "expected_deployment_target": release.release_target(self.service.active_workstream_id), **changes}
        result = release.start_release(payload, service=self.service, store=self.store,
                                       launcher=self.launcher)
        return self.store.load(result["job"]["job_id"])

    def fake_api(self, *, fail_at="", disconnect_deploy=False, bad_stamp=False):
        calls = []
        pushes = 1 if self.service.batch["state"] == "aligned" else 0
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
                        "workstream_id": self.service.active_workstream_id}
            if path.endswith("/deploy"):
                if disconnect_deploy:
                    raise ConnectionError("restart")
                return {"ok": True, "state": "pending_restart"}
            if path.endswith("deploy-verification"):
                return {"ok": True, "state": "deployed", "main_head": TARGET,
                        "smoke": {"check_count": 5}}
            if path.endswith("luna-release/execute"):
                job = self.store.load()
                if job["phase"] == "validation":
                    return {"ok": True, "gate": {"test_count": 2000, "passed": True, "mode": "full"}}
                return {"ok": True, "status": "deployed", "main_head": TARGET,
                        "workflow_run_id": 123, "deployment_id": 456, "smoke_http_status": 200,
                        "smoke_path": release.PAGES_PROJECT_PATHS.get(self.service.active_workstream_id, "")}
            if path.endswith("luna-release/return"):
                return release.return_release(payload, token=kwargs["token"],
                                              service=self.service, store=self.store)
            self.fail(path)

        return call, calls

    def run_job(self, job, **kwargs):
        accept = Mock(return_value={"accepted": True, **EXECUTOR, "target_head": TARGET})
        result = release.run_release(job["job_id"], store=self.store, accept=accept,
                                     protect=lambda: {"camino_pid": 99, "autosave_pids": [98]},
                                     pause=lambda _: None, **kwargs)
        self.assertEqual(accept.call_args.args[0]["commit_count"], job["commit_count"])
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
        self.assertEqual(release.public_job(job)["executor"], EXECUTOR)
        job["executor"]["private_extra"] = "must-not-leak"
        self.assertNotIn("must-not-leak", json.dumps(release.public_job(job)))

    def test_handoff_usage_is_numeric_only_and_legacy_usage_is_unknown(self):
        job = self.create()
        self.assertIsNone(release.public_job(job)["model_usage"])
        counts = dict(input_tokens=100, cached_input_tokens=80, output_tokens=10,
                      reasoning_output_tokens=4, total_tokens=110)
        job["luna_proof"] = {"token_usage": {**counts, "private":"must-not-leak"}}
        public = release.public_job(job)
        self.assertEqual(public["model_usage"], counts)
        self.assertNotIn("must-not-leak", json.dumps(public))

    def test_client_cannot_replace_the_audited_executor(self):
        with self.assertRaises(release.LunaReleaseError):
            self.create(expected_executor={**EXECUTOR, "model":"different-executor"})
        self.launcher.assert_not_called()

    def test_policy_change_or_wrong_executor_proof_cannot_publish(self):
        job = self.create()
        call, calls = self.fake_api()
        accept = Mock()
        with patch.object(release.agent_roles, "assert_current",
                          side_effect=release.agent_roles.AgentRoleError("Nastavení vykonavatele se změnilo.")):
            result = release.run_release(job["job_id"],store=self.store,call=call,accept=accept)
        self.assertEqual(result["job"]["state"], "attention")
        self.assertIn("změnilo", result["job"]["failure_message"])
        accept.assert_not_called()
        self.assertNotIn("/api/human-adam/github-batch", calls)
        self.assertNotIn("/api/human-adam/deploy", calls)

    def test_wrong_executor_answer_stops_before_protected_or_publication_operations(self):
        job = self.create(dry_run=True)
        call = Mock()
        protect = Mock()
        result = release.run_release(job["job_id"],store=self.store,call=call,protect=protect,
            accept=Mock(return_value={**EXECUTOR,"model":"different-executor","target_head":TARGET,"accepted":True}))
        self.assertEqual(result["job"]["state"], "attention")
        call.assert_not_called()
        protect.assert_not_called()

    def test_legacy_receipt_is_readable_but_new_worker_cannot_guess_its_model(self):
        job = self.create(dry_run=True)
        del job["executor"]
        self.store.write(job)
        accept = Mock()
        result = release.run_release(job["job_id"],store=self.store,accept=accept)
        self.assertEqual(result["job"]["state"], "attention")
        self.assertIsNone(result["job"]["executor"])
        accept.assert_not_called()

    def test_missing_confirmation_changed_head_and_invalid_mode_do_not_launch(self):
        for changes in ({"confirmation": "ano"}, {"expected_local_head": "d" * 40}, {"dry_run": "false"}):
            with self.subTest(changes=changes), self.assertRaises(release.LunaReleaseError):
                self.create(**changes)
        self.launcher.assert_not_called()

    def test_every_development_workstream_resolves_its_existing_registered_target(self):
        for record in release.WORKSTREAM_CATALOG_BY_ID.values():
            if record.mode == "archived":
                continue
            with self.subTest(workstream=record.workstream_id):
                self.service.active_workstream_id = record.workstream_id
                audit = release.audit_release(self.service)
                self.assertEqual(audit["workstream_id"], record.workstream_id)
                expected = "github_pages" if record.workstream_id in {"project-mmtx", "project-to-be-to-have", "project-colors-and-numbers"} else "cockpit"
                self.assertEqual(audit["deployment_target"], expected)
        self.launcher.assert_not_called()

    def test_inconsistent_empty_batch_is_rejected(self):
        self.service.batch.update(state="aligned", commit_count=0)
        with self.assertRaises(release.LunaReleaseError):
            self.create()
        self.launcher.assert_not_called()

    def test_unknown_archived_and_unregistered_targets_are_rejected(self):
        from dataclasses import replace
        record = release.WORKSTREAM_CATALOG_BY_ID["project-cockpit"]
        for changed in (replace(record, mode="archived"), replace(record, capabilities=replace(record.capabilities, production_deployment_target="unknown"))):
            with patch.dict(release.WORKSTREAM_CATALOG_BY_ID, {record.workstream_id: changed}), self.assertRaises(release.LunaReleaseError):
                self.create()
        with self.assertRaises(release.LunaReleaseError):
            release.release_target("project-does-not-exist")
        self.launcher.assert_not_called()

    def test_confirmation_cannot_be_reinterpreted_for_another_project_or_target(self):
        for changes in ({"expected_workstream_id": "project-mmtx"}, {"expected_deployment_target": "github_pages"}):
            with self.subTest(changes=changes), self.assertRaises(release.LunaReleaseError):
                self.create(**changes)
        self.launcher.assert_not_called()

    def test_camino_development_uses_shared_runtime_without_releasing_camino_service(self):
        self.service.active_workstream_id = "project-camino"
        job = self.create()
        call, calls = self.fake_api()
        result = self.run_job(job, call=call)
        self.assertTrue(result["ok"])
        self.assertEqual(result["job"]["workstream_id"], "project-camino")
        self.assertEqual(calls.count("/api/human-adam/deploy"), 1)
        self.assertFalse(any("camino" in path for path in calls))

    def test_pages_target_uses_registered_publisher_without_cockpit_restart(self):
        self.service.active_workstream_id = "project-mmtx"
        job = self.create()
        call, calls = self.fake_api()
        result = self.run_job(job, call=call)
        self.assertTrue(result["ok"])
        self.assertEqual(result["job"]["verification"]["deployment_id"], 456)
        self.assertEqual(result["job"]["verification"]["smoke_http_status"], 200)
        self.assertEqual(calls.count("/api/human-adam/luna-release/execute"), 1)
        self.assertNotIn("/api/human-adam/deploy", calls)
        self.assertNotIn("/api/server/health", calls)
        self.assertTrue(self.service.hub.send.call_args.kwargs["read_only"])

    def test_already_pushed_batch_runs_full_validation_without_another_push(self):
        self.service.active_workstream_id = "project-mmtx"
        self.service.batch.update(state="aligned", origin_head=TARGET, commit_count=0)
        job = self.create(expected_origin_head=TARGET)
        call, calls = self.fake_api()
        result = self.run_job(job, call=call)
        self.assertTrue(result["ok"])
        self.assertEqual(result["job"]["push_state"], "already_aligned")
        self.assertFalse(result["job"]["pushed"])
        self.assertEqual(calls.count("/api/human-adam/luna-release/execute"), 2)
        self.assertNotIn("/api/human-adam/github-batch", calls)

    def test_other_public_web_apps_use_pages_and_their_own_http_smoke(self):
        for index, (identity, path) in enumerate((("project-to-be-to-have", "to-be-to-have/"),
                                                  ("project-colors-and-numbers", "colors-numbers/"))):
            with self.subTest(workstream=identity):
                self.service.active_workstream_id = identity
                job = self.create(client_message_id=f"web-app-release-00{index}")
                call, calls = self.fake_api()
                result = self.run_job(job, call=call)
                self.assertTrue(result["ok"])
                self.assertEqual(result["job"]["verification"]["smoke_path"], path)
                self.assertNotIn("/api/human-adam/deploy", calls)

    def test_uncertain_pages_result_is_not_retried_or_replaced_by_runtime_deployment(self):
        self.service.active_workstream_id = "project-mmtx"
        job = self.create()
        call, calls = self.fake_api(fail_at="/api/human-adam/luna-release/execute")
        result = self.run_job(job, call=call)
        self.assertEqual(result["job"]["state"], "attention")
        self.assertEqual(result["job"]["deployment_state"], "uncertain")
        self.assertEqual(calls.count("/api/human-adam/luna-release/execute"), 1)
        self.assertNotIn("/api/human-adam/deploy", calls)

    def test_changed_project_after_handoff_cannot_push_or_deploy(self):
        job = self.create()
        self.service.active_workstream_id = "project-mmtx"
        call, calls = self.fake_api()
        result = self.run_job(job, call=call)
        self.assertEqual(result["job"]["state"], "attention")
        self.assertNotIn("/api/human-adam/github-batch", calls)
        self.assertNotIn("/api/human-adam/deploy", calls)

    def test_internal_execution_uses_stored_head_and_target_without_client_override(self):
        self.service.active_workstream_id = "project-mmtx"
        job = self.create()
        self.store.update(job["job_id"], state="running", phase="publish_requested")
        self.service.publish_luna_release = Mock(return_value={"ok": True})
        result = release.execute_release({"job_id": job["job_id"], "expected_head": ORIGIN,
            "deployment_target": "cockpit"}, token=job["token"], service=self.service, store=self.store)
        self.assertTrue(result["ok"])
        self.service.publish_luna_release.assert_called_once_with(expected_head=TARGET, workstream_id="project-mmtx")
        for token in ("wrong", ""):
            with self.assertRaises(release.LunaReleaseError):
                release.execute_release({"job_id": job["job_id"]}, token=token, service=self.service, store=self.store)

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
            "confirmation": release.CONFIRMATION, "client_message_id": "native-release-123", "expected_executor": EXECUTOR,
            "expected_origin_head": ORIGIN, "expected_local_head": TARGET, "dry_run": False,
            "expected_workstream_id": self.service.active_workstream_id,
            "expected_deployment_target": release.release_target(self.service.active_workstream_id),
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

    def test_native_audit_and_return_follow_the_selected_pages_project(self):
        self.service.active_workstream_id = "project-mmtx"
        call, calls = self.fake_api()
        with patch.object(release, "http_call", side_effect=call):
            audit = release.audit_release()
        self.assertEqual(audit["workstream_id"], "project-mmtx")
        self.assertEqual(audit["deployment_target"], "github_pages")
        result = release.start_terminal_release({**audit, "confirmation": release.CONFIRMATION,
            "expected_workstream_id": "project-mmtx", "expected_deployment_target": "github_pages",
            "client_message_id": "native-pages-release-123", "expected_executor": EXECUTOR, "dry_run": False},
            store=self.store, call=call, launcher=self.launcher)
        job = self.store.load(result["job"]["job_id"])
        result = self.run_job(job, call=call)
        self.assertTrue(result["ok"])
        self.assertNotIn("/api/human-adam/luna-release/return", calls)
        self.service.hub.send.assert_not_called()

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

    def test_status_does_not_probe_worker_lease_during_startup_grace(self):
        job = self.create()
        with patch.object(self.store, "lock", side_effect=AssertionError("startup lease probe")):
            status = self.store.status(job["job_id"])
        self.assertEqual(status["job"]["state"], "queued")
        self.assertEqual(self.launcher.call_count, 1)

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
        client.list_models.return_value = ROLE_CATALOG
        client.start_thread.return_value = "luna-thread"
        client.send_text.return_value = SimpleNamespace(answer=json.dumps({"action": "accept", "target_head": TARGET, "message": "Přebírám."}))
        result = release.accept_handoff({"target_head": TARGET, "commit_count": 7}, client_factory=lambda: client)
        self.assertTrue(result["accepted"])
        self.assertEqual(client.start_thread.call_args.kwargs["model"], EXECUTOR["model"])
        self.assertTrue(client.start_thread.call_args.kwargs["ephemeral"])
        self.assertEqual(client.send_text.call_args.kwargs["sandbox_policy"], {"type": "readOnly", "networkAccess": False})
        client.send_text.return_value.answer = json.dumps({"action": "accept", "target_head": ORIGIN})
        with self.assertRaises(release.LunaReleaseError):
            release.accept_handoff({"target_head": TARGET}, client_factory=lambda: client)

    def test_unapproved_candidate_probe_cannot_approve_or_publish_a_role(self):
        before = release.agent_roles.CONFIG_PATH.read_bytes()
        client = Mock()
        client.__enter__ = Mock(return_value=client)
        client.__exit__ = Mock(return_value=False)
        client.list_models.return_value = [{"model":"candidate-future", "supportedReasoningEfforts":[{"reasoningEffort":"medium"}]}]
        client.send_text.return_value = SimpleNamespace(answer=json.dumps({"action":"accept","target_head":"0"*40,"message":"OK"}))
        proof = release.probe_release_executor_candidate("candidate-future","medium",client_factory=lambda:client)
        self.assertTrue(proof["probe_only"])
        self.assertFalse(proof["published"])
        self.assertEqual(before, release.agent_roles.CONFIG_PATH.read_bytes())
        self.assertEqual(client.send_text.call_args.kwargs["sandbox_policy"], {"type":"readOnly","networkAccess":False})
        prompt = json.loads(client.send_text.call_args.kwargs["text"])
        self.assertEqual(prompt["target_head"], "0"*40)
        self.assertEqual(prompt["deployment_target"], "none")


if __name__ == "__main__":
    unittest.main()
