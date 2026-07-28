from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.communication.human_adam_workspace import HumanAdamWorkspaceManager
from app.communication.simple_main_deploy import (
    DEFAULT_DEPLOYMENT_SMOKE_TIMEOUT_SECONDS,
    DEPLOYED,
    PENDING_RESTART,
    SIMPLE_MAIN_DEPLOYMENT_CONFIRMATION,
    SimpleMainDeploymentError,
    SimpleMainDeploymentRequest,
    audit_simple_main_deployment,
    load_completed_simple_main_deployment,
    load_recent_simple_main_deployment,
    load_simple_main_deployment_receipt,
    prepare_simple_main_deployment,
    verify_simple_main_deployment,
)
from app.communication.simple_main_deploy import _default_smoke_runner
from scripts.cockpit_smoke_check import DEFAULT_CHECKS, SmokeResult
from tests.test_human_adam_takeover import prepare_with_origin
from tests.test_human_adam_workspace import git


def successful_gate(command, **_kwargs):
    return subprocess.CompletedProcess(
        command,
        0,
        stdout="Ran 23 tests in 0.100s\nOK\nCockpit quality gate: OK\n",
        stderr="",
    )


def failed_gate(command, **_kwargs):
    return subprocess.CompletedProcess(
        command,
        1,
        stdout="Ran 23 tests in 0.100s\nFAILED\n",
        stderr="",
    )


def successful_smoke() -> list[SmokeResult]:
    return [
        SmokeResult(name=name, path=path, ok=True, status_code=200, message="OK")
        for name, path in DEFAULT_CHECKS
    ]


def prepare_clean_main(root: Path):
    source, primary = prepare_with_origin(root)
    (source / "AuditCockpit56_M.txt").unlink()
    gate_script = source / "Samantha_Agent" / "scripts" / "cockpit_quality_gate.py"
    gate_script.parent.mkdir(parents=True, exist_ok=True)
    gate_script.write_text("raise SystemExit(0)\n", encoding="utf-8")
    git(source, "add", "Samantha_Agent/scripts/cockpit_quality_gate.py")
    git(source, "commit", "-m", "Add test gate")
    git(source, "push", "origin", "main:main")
    primary.sync_from_main(confirmed=True)
    peer = HumanAdamWorkspaceManager(
        source_repo=source,
        workspace_root=root / "peer",
        metadata_path=root / "peer-meta.json",
    )
    peer.prepare()
    return source, primary, peer, git(source, "rev-parse", "HEAD")


def request(head: str) -> SimpleMainDeploymentRequest:
    return SimpleMainDeploymentRequest(
        workstream_id="layer-human-adam-development",
        expected_head=head,
        previous_pid=321,
    )


class SimpleMainDeploymentTests(unittest.TestCase):
    def test_default_smoke_runner_allows_heavy_status_endpoint_to_finish(self) -> None:
        with patch(
            "app.communication.simple_main_deploy.run_smoke_check",
            return_value=[],
        ) as smoke:
            self.assertEqual(_default_smoke_runner(), [])

        smoke.assert_called_once_with(
            "http://127.0.0.1:8770",
            DEFAULT_DEPLOYMENT_SMOKE_TIMEOUT_SECONDS,
        )
        self.assertEqual(DEFAULT_DEPLOYMENT_SMOKE_TIMEOUT_SECONDS, 15.0)

    def test_confirmation_names_runtime_target_unambiguously(self) -> None:
        self.assertEqual(
            SIMPLE_MAIN_DEPLOYMENT_CONFIRMATION,
            "POTVRZUJI NASAZENI AKTUALNIHO MAIN DO COCKPITU",
        )

    def test_batch_mode_deploys_local_ahead_main_with_quick_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, primary, peer, _head = prepare_clean_main(root)
            origin_before = git(source, "rev-parse", "origin/main")
            target = source / "Samantha_Agent" / "ordinary.py"
            target.write_text("VALUE = 27\n", encoding="utf-8")
            git(source, "add", "Samantha_Agent/ordinary.py")
            git(source, "commit", "-m", "Local deployment target")
            head = git(source, "rev-parse", "HEAD")
            primary.sync_from_main(confirmed=True)
            receipt_path = root / "receipt.json"

            audit = audit_simple_main_deployment(
                workspace=primary,
                workstream_id="layer-human-adam-development",
                peer_workspaces=(peer,),
                code_stamp_factory=lambda _workspace: "0123456789abcdef",
                allow_origin_behind=True,
            )
            prepared = prepare_simple_main_deployment(
                workspace=primary,
                request=request(head),
                confirmed=True,
                peer_workspaces=(peer,),
                gate_runner=successful_gate,
                gate_log_path=root / "gate.log",
                receipt_path=receipt_path,
                now_factory=lambda: "2026-07-27T10:00:00+00:00",
                code_stamp_factory=lambda _workspace: "0123456789abcdef",
                allow_origin_behind=True,
                quick_validation=True,
            )
            verified = verify_simple_main_deployment(
                workspace=primary,
                observed_pid=654,
                observed_code_stamp="0123456789abcdef",
                peer_workspaces=(peer,),
                receipt_path=receipt_path,
                smoke_runner=successful_smoke,
                now_factory=lambda: "2026-07-27T10:01:00+00:00",
                allow_origin_behind=True,
            )
            receipt = load_simple_main_deployment_receipt(receipt_path)
            origin_after = git(source, "rev-parse", "origin/main")

        self.assertTrue(audit["ready"])
        self.assertTrue(audit["remote_push_deferred"])
        self.assertEqual(prepared["gate"]["mode"], "quick")
        self.assertEqual(prepared["gate"]["test_count"], 0)
        self.assertEqual(verified["state"], DEPLOYED)
        self.assertEqual(verified["gate"]["mode"], "quick")
        self.assertEqual(receipt["gate_mode"], "quick")
        self.assertEqual(origin_after, origin_before)

    def test_batch_mode_local_deploy_audit_survives_remote_divergence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, primary, peer, _head = prepare_clean_main(root)
            target = source / "Samantha_Agent" / "local_diverged.py"
            target.write_text("VALUE = 28\n", encoding="utf-8")
            git(source, "add", "Samantha_Agent/local_diverged.py")
            git(source, "commit", "-m", "Local divergent deployment target")
            primary.sync_from_main(confirmed=True)

            competitor = root / "competitor-deploy-divergence"
            subprocess.run(
                ["/usr/bin/git", "clone", str(root / "origin.git"), str(competitor)],
                capture_output=True,
                text=True,
                check=True,
            )
            git(competitor, "config", "user.name", "Other writer")
            git(competitor, "config", "user.email", "other@example.invalid")
            (competitor / "remote.txt").write_text("remote\n", encoding="utf-8")
            git(competitor, "add", "remote.txt")
            git(competitor, "commit", "-m", "Remote divergent deployment work")
            git(competitor, "push", "origin", "main")
            git(source, "fetch", "origin", "main:refs/remotes/origin/main")

            result = audit_simple_main_deployment(
                workspace=primary,
                workstream_id="layer-human-adam-development",
                peer_workspaces=(peer,),
                code_stamp_factory=lambda _workspace: "0123456789abcdef",
                allow_origin_behind=True,
            )

        self.assertTrue(result["ready"])
        self.assertTrue(result["remote_push_deferred"])

    def test_simple_main_uses_shared_gate_without_legacy_deploy_import(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        for relative_path in (
            "app/communication/simple_main_checkpoint.py",
            "app/communication/simple_main_deploy.py",
        ):
            source = (project_root / relative_path).read_text(encoding="utf-8")
            self.assertIn("app.communication.checkpoint_quality_gate", source)
            self.assertNotIn("app.communication.human_adam_deploy", source)

    def test_audit_reports_exact_clean_main_without_creating_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, primary, peer, head = prepare_clean_main(root)
            result = audit_simple_main_deployment(
                workspace=primary,
                workstream_id="layer-human-adam-development",
                peer_workspaces=(peer,),
                code_stamp_factory=lambda _workspace: "0123456789abcdef",
            )
            source_status = git(source, "status", "--porcelain=v1")

        self.assertTrue(result["ok"])
        self.assertTrue(result["ready"])
        self.assertEqual(result["main_head"], head)
        self.assertEqual(result["main_short"], head[:12])
        self.assertEqual(result["confirmation_text"], SIMPLE_MAIN_DEPLOYMENT_CONFIRMATION)
        self.assertEqual(len(result["workspaces"]), 2)
        self.assertEqual(result["changes"], [])
        self.assertFalse(result["wip_used"])
        self.assertFalse(result["semaphore_used"])
        self.assertEqual(source_status, "")

    def test_audit_accepts_clean_peer_behind_and_prepare_synchronizes_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, primary, peer, _head = prepare_clean_main(root)
            (source / "Samantha_Agent" / "tracked.py").write_text(
                "VALUE = 91\n", encoding="utf-8"
            )
            git(source, "add", "Samantha_Agent/tracked.py")
            git(source, "commit", "-m", "Advance clean main")
            git(source, "push", "origin", "main:main")
            primary.sync_from_main(confirmed=True)
            head = git(source, "rev-parse", "HEAD")
            receipt_path = root / "receipt.json"

            audit = audit_simple_main_deployment(
                workspace=primary,
                workstream_id="layer-human-adam-development",
                peer_workspaces=(peer,),
                code_stamp_factory=lambda _workspace: "0123456789abcdef",
            )
            peer_before = peer.status()
            prepared = prepare_simple_main_deployment(
                workspace=primary,
                request=request(head),
                confirmed=True,
                peer_workspaces=(peer,),
                gate_runner=successful_gate,
                gate_log_path=root / "gate.log",
                receipt_path=receipt_path,
                code_stamp_factory=lambda _workspace: "0123456789abcdef",
            )
            peer_after = peer.status()

        self.assertTrue(audit["ready"])
        self.assertTrue(audit["workspaces"][1]["clean_source_ahead"])
        self.assertEqual(peer_before["workspace_relation"], "source_ahead")
        self.assertTrue(prepared["ok"])
        self.assertEqual(peer_after["workspace_relation"], "aligned")
        self.assertEqual(peer_after["head"], head)

    def test_prepare_accepts_only_exact_clean_main_and_records_pending_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, primary, peer, head = prepare_clean_main(root)
            receipt_path = root / "receipt.json"

            result = prepare_simple_main_deployment(
                workspace=primary,
                request=request(head),
                confirmed=True,
                peer_workspaces=(peer,),
                gate_runner=successful_gate,
                gate_log_path=root / "gate.log",
                receipt_path=receipt_path,
                now_factory=lambda: "2026-07-20T09:30:00+00:00",
                code_stamp_factory=lambda _workspace: "0123456789abcdef",
            )
            receipt = load_simple_main_deployment_receipt(receipt_path)
            source_status = git(source, "status", "--porcelain=v1")
            source_head = git(source, "rev-parse", "HEAD")
            origin_head = git(source, "rev-parse", "origin/main")

        self.assertTrue(result["ok"])
        self.assertEqual(result["state"], PENDING_RESTART)
        self.assertTrue(result["restart_required"])
        self.assertFalse(result["branches_created"])
        self.assertFalse(result["wip_used"])
        self.assertFalse(result["semaphore_used"])
        self.assertEqual(result["gate"]["test_count"], 23)
        self.assertEqual(len(result["workspaces"]), 2)
        self.assertEqual(receipt["main_head"], head)
        self.assertEqual(receipt["state"], PENDING_RESTART)
        self.assertEqual(source_status, "")
        self.assertEqual(source_head, head)
        self.assertEqual(origin_head, head)

    def test_prepare_rejects_dirty_source_and_dirty_peer_before_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, primary, peer, head = prepare_clean_main(root)
            source_receipt = root / "source-receipt.json"
            (source / "Samantha_Agent" / "tracked.py").write_text("VALUE = 77\n", encoding="utf-8")
            with self.assertRaisesRegex(SimpleMainDeploymentError, "Zdrojový main není čistý"):
                prepare_simple_main_deployment(
                    workspace=primary,
                    request=request(head),
                    confirmed=True,
                    peer_workspaces=(peer,),
                    gate_runner=successful_gate,
                    receipt_path=source_receipt,
                    code_stamp_factory=lambda _workspace: "0123456789abcdef",
                )
            git(source, "restore", "Samantha_Agent/tracked.py")
            peer_receipt = root / "peer-receipt.json"
            (peer.project_root / "tracked.py").write_text("VALUE = 88\n", encoding="utf-8")
            with self.assertRaisesRegex(SimpleMainDeploymentError, "profilové workspaces"):
                prepare_simple_main_deployment(
                    workspace=primary,
                    request=request(head),
                    confirmed=True,
                    peer_workspaces=(peer,),
                    gate_runner=successful_gate,
                    receipt_path=peer_receipt,
                    code_stamp_factory=lambda _workspace: "0123456789abcdef",
                )

        self.assertFalse(source_receipt.exists())
        self.assertFalse(peer_receipt.exists())

    def test_prepare_rejects_remote_race_after_gate_without_writing_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, primary, peer, head = prepare_clean_main(root)
            receipt_path = root / "receipt.json"

            def racing_gate(command, **kwargs):
                competitor = root / "competitor"
                subprocess.run(
                    ["/usr/bin/git", "clone", str(root / "origin.git"), str(competitor)],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                git(competitor, "config", "user.name", "Concurrent Writer")
                git(competitor, "config", "user.email", "writer@example.invalid")
                (competitor / "race.txt").write_text("race\n", encoding="utf-8")
                git(competitor, "add", "race.txt")
                git(competitor, "commit", "-m", "Concurrent main update")
                git(competitor, "push", "origin", "main:main")
                return successful_gate(command, **kwargs)

            with self.assertRaisesRegex(SimpleMainDeploymentError, "origin/main"):
                prepare_simple_main_deployment(
                    workspace=primary,
                    request=request(head),
                    confirmed=True,
                    peer_workspaces=(peer,),
                    gate_runner=racing_gate,
                    receipt_path=receipt_path,
                    code_stamp_factory=lambda _workspace: "0123456789abcdef",
                )
            source_head_after = git(source, "rev-parse", "HEAD")

        self.assertFalse(receipt_path.exists())
        self.assertEqual(source_head_after, head)

    def test_failed_gate_does_not_prepare_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _source, primary, peer, head = prepare_clean_main(root)
            receipt_path = root / "receipt.json"
            with self.assertRaises(SimpleMainDeploymentError):
                prepare_simple_main_deployment(
                    workspace=primary,
                    request=request(head),
                    confirmed=True,
                    peer_workspaces=(peer,),
                    gate_runner=failed_gate,
                    gate_log_path=root / "gate.log",
                    receipt_path=receipt_path,
                    code_stamp_factory=lambda _workspace: "0123456789abcdef",
                )

        self.assertFalse(receipt_path.exists())

    def test_verify_promotes_only_new_process_matching_stamp_and_smoke_five_of_five(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _source, primary, peer, head = prepare_clean_main(root)
            receipt_path = root / "receipt.json"
            prepare_simple_main_deployment(
                workspace=primary,
                request=request(head),
                confirmed=True,
                peer_workspaces=(peer,),
                gate_runner=successful_gate,
                gate_log_path=root / "gate.log",
                receipt_path=receipt_path,
                now_factory=lambda: "2026-07-20T09:30:00+00:00",
                code_stamp_factory=lambda _workspace: "0123456789abcdef",
            )

            result = verify_simple_main_deployment(
                workspace=primary,
                observed_pid=654,
                observed_code_stamp="0123456789abcdef",
                peer_workspaces=(peer,),
                receipt_path=receipt_path,
                smoke_runner=successful_smoke,
                now_factory=lambda: "2026-07-20T09:35:00+00:00",
            )
            receipt = load_simple_main_deployment_receipt(receipt_path)

        self.assertTrue(result["ok"])
        self.assertEqual(result["state"], DEPLOYED)
        self.assertEqual(result["gate"]["test_count"], 23)
        self.assertEqual(result["deployed_at"], "2026-07-20T09:35:00+00:00")
        self.assertEqual(result["smoke"]["check_count"], 5)
        self.assertTrue(result["new_process_confirmed"])
        self.assertFalse(result["branches_created"])
        self.assertFalse(result["wip_used"])
        self.assertFalse(result["semaphore_used"])
        self.assertEqual(receipt["state"], DEPLOYED)
        self.assertEqual(receipt["observed_pid"], 654)

    def test_verify_reuses_completed_proof_for_the_same_running_process(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _source, primary, peer, head = prepare_clean_main(root)
            receipt_path = root / "receipt.json"
            prepare_simple_main_deployment(
                workspace=primary,
                request=request(head),
                confirmed=True,
                peer_workspaces=(peer,),
                gate_runner=successful_gate,
                gate_log_path=root / "gate.log",
                receipt_path=receipt_path,
                now_factory=lambda: "2026-07-20T09:30:00+00:00",
                code_stamp_factory=lambda _workspace: "0123456789abcdef",
            )
            verify_simple_main_deployment(
                workspace=primary,
                observed_pid=654,
                observed_code_stamp="0123456789abcdef",
                peer_workspaces=(peer,),
                receipt_path=receipt_path,
                smoke_runner=successful_smoke,
                now_factory=lambda: "2026-07-20T09:35:00+00:00",
            )

            reused = verify_simple_main_deployment(
                workspace=primary,
                observed_pid=654,
                observed_code_stamp="0123456789abcdef",
                peer_workspaces=(peer,),
                receipt_path=receipt_path,
                smoke_runner=lambda: self.fail("Dokončený smoke se nesmí opakovat."),
                now_factory=lambda: "2026-07-20T10:00:00+00:00",
            )
            with self.assertRaisesRegex(
                SimpleMainDeploymentError,
                "nepatří běžícímu procesu",
            ):
                verify_simple_main_deployment(
                    workspace=primary,
                    observed_pid=777,
                    observed_code_stamp="0123456789abcdef",
                    peer_workspaces=(peer,),
                    receipt_path=receipt_path,
                    smoke_runner=successful_smoke,
                )

        self.assertTrue(reused["ok"])
        self.assertEqual(reused["state"], DEPLOYED)
        self.assertTrue(reused["verification_reused"])
        self.assertEqual(reused["deployed_at"], "2026-07-20T09:35:00+00:00")
        self.assertEqual(reused["smoke"]["check_count"], 5)

    def test_recent_deployed_receipt_returns_only_safe_short_recovery_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            receipt_path = Path(temp_dir) / "receipt.json"
            receipt_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "state": DEPLOYED,
                        "workstream_id": "project-library",
                        "main_head": "a" * 40,
                        "expected_code_stamp": "0123456789abcdef",
                        "previous_pid": 100,
                        "test_count": 904,
                        "gate_duration_seconds": 272.5,
                        "prepared_at": "2026-07-20T13:42:00+00:00",
                        "observed_pid": 200,
                        "smoke_count": 5,
                        "deployed_at": "2026-07-20T13:47:16+00:00",
                    }
                ),
                encoding="utf-8",
            )

            recent = load_recent_simple_main_deployment(
                receipt_path,
                expected_workstream_id="project-library",
                now_factory=lambda: "2026-07-20T13:50:00+00:00",
            )
            stale = load_recent_simple_main_deployment(
                receipt_path,
                expected_workstream_id="project-library",
                now_factory=lambda: "2026-07-20T14:10:00+00:00",
            )

        self.assertEqual(
            recent,
            {
                "state": DEPLOYED,
                "workstream_id": "project-library",
                "main_short": "a" * 12,
                "deployed_at": "2026-07-20T13:47:16+00:00",
                "gate": {
                    "passed": True,
                    "test_count": 904,
                    "duration_seconds": 272.5,
                    "mode": "full",
                },
                "smoke": {"passed": True, "check_count": 5},
            },
        )
        self.assertIsNone(stale)

    def test_completed_summary_is_persistent_and_rejects_foreign_or_invalid_receipts(self) -> None:
        completed = {
            "schema_version": 1,
            "state": DEPLOYED,
            "workstream_id": "project-library",
            "main_head": "a" * 40,
            "expected_code_stamp": "0123456789abcdef",
            "previous_pid": 100,
            "test_count": 904,
            "gate_duration_seconds": 272.5,
            "prepared_at": "2026-07-20T13:42:00+00:00",
            "observed_pid": 200,
            "smoke_count": 5,
            "deployed_at": "2026-07-20T13:47:16+00:00",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            receipt_path = Path(temp_dir) / "receipt.json"
            receipt_path.write_text(json.dumps(completed), encoding="utf-8")
            persistent = load_completed_simple_main_deployment(
                receipt_path,
                expected_workstream_id="project-library",
            )
            global_summary = load_completed_simple_main_deployment(receipt_path)
            foreign = load_completed_simple_main_deployment(
                receipt_path,
                expected_workstream_id="project-mmtx",
            )

            pending = dict(completed)
            pending["state"] = PENDING_RESTART
            pending.pop("observed_pid")
            pending.pop("smoke_count")
            pending.pop("deployed_at")
            receipt_path.write_text(json.dumps(pending), encoding="utf-8")
            waiting = load_completed_simple_main_deployment(
                receipt_path,
                expected_workstream_id="project-library",
            )

            malformed = dict(completed)
            malformed["smoke_count"] = 4
            receipt_path.write_text(json.dumps(malformed), encoding="utf-8")
            invalid = load_completed_simple_main_deployment(
                receipt_path,
                expected_workstream_id="project-library",
            )

        self.assertIsNotNone(persistent)
        self.assertEqual(persistent["workstream_id"], "project-library")
        self.assertEqual(global_summary, persistent)
        self.assertEqual(persistent["main_short"], "a" * 12)
        self.assertNotIn("main_head", persistent)
        self.assertNotIn("expected_code_stamp", persistent)
        self.assertNotIn("previous_pid", persistent)
        self.assertNotIn("observed_pid", persistent)
        self.assertIsNone(foreign)
        self.assertIsNone(waiting)
        self.assertIsNone(invalid)

    def test_verify_keeps_pending_receipt_when_restart_or_smoke_evidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _source, primary, peer, head = prepare_clean_main(root)
            receipt_path = root / "receipt.json"
            prepare_simple_main_deployment(
                workspace=primary,
                request=request(head),
                confirmed=True,
                peer_workspaces=(peer,),
                gate_runner=successful_gate,
                gate_log_path=root / "gate.log",
                receipt_path=receipt_path,
                code_stamp_factory=lambda _workspace: "0123456789abcdef",
            )
            with self.assertRaisesRegex(SimpleMainDeploymentError, "nový proces"):
                verify_simple_main_deployment(
                    workspace=primary,
                    observed_pid=321,
                    observed_code_stamp="0123456789abcdef",
                    peer_workspaces=(peer,),
                    receipt_path=receipt_path,
                    smoke_runner=successful_smoke,
                )
            with self.assertRaisesRegex(SimpleMainDeploymentError, "kódový otisk"):
                verify_simple_main_deployment(
                    workspace=primary,
                    observed_pid=654,
                    observed_code_stamp="fedcba9876543210",
                    peer_workspaces=(peer,),
                    receipt_path=receipt_path,
                    smoke_runner=successful_smoke,
                )
            failed_smoke = successful_smoke()
            failed_smoke[-1] = SmokeResult(
                name=failed_smoke[-1].name,
                path=failed_smoke[-1].path,
                ok=False,
                status_code=500,
                message="FAIL",
            )
            with self.assertRaisesRegex(SimpleMainDeploymentError, "5/5"):
                verify_simple_main_deployment(
                    workspace=primary,
                    observed_pid=654,
                    observed_code_stamp="0123456789abcdef",
                    peer_workspaces=(peer,),
                    receipt_path=receipt_path,
                    smoke_runner=lambda: failed_smoke,
                )
            receipt = load_simple_main_deployment_receipt(receipt_path)

        self.assertEqual(receipt["state"], PENDING_RESTART)

    def test_receipt_rejects_unknown_fields_instead_of_trusting_them(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "receipt.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "state": "pending_restart",
                        "workstream_id": "layer-human-adam-development",
                        "main_head": "a" * 40,
                        "expected_code_stamp": "0123456789abcdef",
                        "previous_pid": 321,
                        "test_count": 23,
                        "gate_duration_seconds": 0.1,
                        "prepared_at": "2026-07-20T09:30:00+00:00",
                        "private_detail": "must not be trusted",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SimpleMainDeploymentError, "neplatná"):
                load_simple_main_deployment_receipt(path)


if __name__ == "__main__":
    unittest.main()
