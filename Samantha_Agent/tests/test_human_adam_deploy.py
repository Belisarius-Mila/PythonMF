from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.communication.human_adam_deploy import (
    DEPLOYMENT_PENDING,
    HumanAdamDeployError,
    TRUSTED_PYTHON,
    audit_checkpoint,
    deploy_checkpoint,
    load_deployment_confirmation,
    load_deployment_diagnostic,
    record_deployment_restart,
    write_deployment_receipt,
)
from scripts.human_adam_takeover import CONFIRMATION_TEXT, TakeoverError
from tests.test_human_adam_takeover import prepare_with_origin
from tests.test_remote_work_cell import git


def successful_gate(command, **_kwargs):
    return subprocess.CompletedProcess(
        command,
        0,
        stdout="Ran 19 tests in 0.100s\nOK\nCockpit quality gate: OK\n",
        stderr="",
    )


def failing_gate(command, **_kwargs):
    return subprocess.CompletedProcess(
        command,
        1,
        stdout="Ran 19 tests in 0.100s\nFAILED\n",
        stderr="",
    )


def prepare_checkpoint(root: Path):
    source, manager = prepare_with_origin(root)
    gate_script = manager.project_root / "scripts" / "cockpit_quality_gate.py"
    gate_script.parent.mkdir(parents=True, exist_ok=True)
    gate_script.write_text("raise SystemExit(0)\n", encoding="utf-8")
    (manager.project_root / "tracked.py").write_text("VALUE = 27\n", encoding="utf-8")
    checkpoint = manager.checkpoint(confirmed=True, message="WIP deploy test")
    return source, manager, checkpoint


class HumanAdamDeployTests(unittest.TestCase):
    def test_trusted_python_preserves_the_active_venv_entrypoint(self) -> None:
        self.assertEqual(TRUSTED_PYTHON, Path(sys.executable))

    def test_audit_returns_exact_token_and_safe_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _source, manager, checkpoint = prepare_checkpoint(Path(temp_dir))
            result = audit_checkpoint(workspace=manager)

        self.assertTrue(result["ready"])
        self.assertEqual(result["checkpoint_token"], checkpoint["checkpoint_head"])
        self.assertEqual(result["confirmation_text"], CONFIRMATION_TEXT)
        self.assertEqual(result["change_count"], 2)
        self.assertNotIn("VALUE = 27", str(result))

    def test_deploy_runs_gate_then_fast_forwards_pushes_and_aligns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, manager, checkpoint = prepare_checkpoint(root)
            receipt_path = root / "deployment_receipt.json"
            diagnostic_path = root / "deployment_diagnostic.json"
            result = deploy_checkpoint(
                workspace=manager,
                confirmation=CONFIRMATION_TEXT,
                expected_checkpoint_head=checkpoint["checkpoint_head"],
                gate_runner=successful_gate,
                gate_log_path=root / "gate.log",
                thread_id="canonical-thread",
                deployment_receipt_path=receipt_path,
                deployment_diagnostic_path=diagnostic_path,
            )
            source_head = git(source, "rev-parse", "HEAD")
            origin_head = git(source, "rev-parse", "origin/main")
            status = manager.status()
            receipt_text = receipt_path.read_text(encoding="utf-8")
            receipt = json.loads(receipt_text)
            diagnostic = load_deployment_diagnostic(
                diagnostic_path,
                thread_id="canonical-thread",
            )

        self.assertTrue(result["applied"])
        self.assertTrue(result["pushed"])
        self.assertTrue(result["gate"]["passed"])
        self.assertEqual(result["gate"]["test_count"], 19)
        self.assertEqual(source_head, checkpoint["checkpoint_head"])
        self.assertEqual(origin_head, source_head)
        self.assertEqual(status["workspace_relation"], "aligned")
        self.assertEqual(result["deployment_confirmation"]["checkpoint_short"], source_head[:7])
        self.assertEqual(receipt["state"], "deployed")
        self.assertEqual(diagnostic["stage"], "workspace_alignment")
        self.assertEqual(diagnostic["outcome"], "passed")
        self.assertNotIn("canonical-thread", receipt_text)
        self.assertNotIn(str(root), receipt_text)
        self.assertNotIn("VALUE = 27", receipt_text)

    def test_push_failure_persists_safe_exact_stage_without_exception_detail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _source, manager, checkpoint = prepare_checkpoint(root)
            diagnostic_path = root / "deployment_diagnostic.json"

            def fail_during_push(*, progress_callback, **_kwargs):
                progress_callback("fast_forward", "running")
                progress_callback("fast_forward", "passed")
                progress_callback("push", "running")
                raise TakeoverError("tajná interní cesta /private/example nesmí ven")

            with patch(
                "app.communication.human_adam_deploy.apply_takeover",
                side_effect=fail_during_push,
            ):
                with self.assertRaisesRegex(
                    HumanAdamDeployError,
                    "Push větve main selhal",
                ) as raised:
                    deploy_checkpoint(
                        workspace=manager,
                        confirmation=CONFIRMATION_TEXT,
                        expected_checkpoint_head=checkpoint["checkpoint_head"],
                        gate_runner=successful_gate,
                        gate_log_path=root / "gate.log",
                        thread_id="canonical-thread",
                        deployment_receipt_path=root / "deployment_receipt.json",
                        deployment_diagnostic_path=diagnostic_path,
                    )

            diagnostic_text = diagnostic_path.read_text(encoding="utf-8")
            diagnostic = load_deployment_diagnostic(
                diagnostic_path,
                thread_id="canonical-thread",
            )

        self.assertEqual(diagnostic["stage"], "push")
        self.assertEqual(diagnostic["outcome"], "failed")
        self.assertNotIn("tajná", str(raised.exception))
        self.assertNotIn("private", diagnostic_text)
        self.assertNotIn("example", diagnostic_text)

    def test_restart_result_is_persistent_safe_and_thread_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            diagnostic_path = Path(temp_dir) / "deployment_diagnostic.json"
            service = SimpleNamespace(
                hub=SimpleNamespace(snapshot=lambda: {"thread_id": "canonical-thread"}),
                deployment_diagnostic_path=diagnostic_path,
            )

            running = record_deployment_restart(
                service=service,
                checkpoint_head="b" * 40,
                outcome="running",
            )
            failed = record_deployment_restart(
                service=service,
                checkpoint_head="b" * 40,
                outcome="failed",
            )
            wrong_thread = load_deployment_diagnostic(
                diagnostic_path,
                thread_id="different-thread",
            )
            diagnostic_text = diagnostic_path.read_text(encoding="utf-8")

        self.assertEqual(running["stage"], "restart")
        self.assertEqual(running["outcome"], "running")
        self.assertEqual(failed["outcome"], "failed")
        self.assertIsNone(wrong_thread)
        self.assertNotIn("canonical-thread", diagnostic_text)

    def test_pending_receipt_never_becomes_public_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            receipt_path = Path(temp_dir) / "deployment_receipt.json"
            checkpoint_head = "a" * 40
            write_deployment_receipt(
                receipt_path,
                checkpoint_head=checkpoint_head,
                thread_id="canonical-thread",
                state=DEPLOYMENT_PENDING,
                recorded_at="2026-07-14T20:31:00+00:00",
            )

            before_apply = load_deployment_confirmation(
                receipt_path,
                thread_id="canonical-thread",
            )
            wrong_thread = load_deployment_confirmation(
                receipt_path,
                thread_id="different-thread",
            )
            matching_source_cannot_promote_pending = load_deployment_confirmation(
                receipt_path,
                thread_id="canonical-thread",
            )

        self.assertIsNone(before_apply)
        self.assertIsNone(wrong_thread)
        self.assertIsNone(matching_source_cannot_promote_pending)

    def test_incomplete_takeover_evidence_leaves_only_non_public_pending_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _source, manager, checkpoint = prepare_checkpoint(root)
            receipt_path = root / "deployment_receipt.json"
            incomplete = {"applied": True, "pushed": False, "workspace_aligned": False}

            with patch(
                "app.communication.human_adam_deploy.apply_takeover",
                return_value=incomplete,
            ):
                with self.assertRaises(HumanAdamDeployError):
                    deploy_checkpoint(
                        workspace=manager,
                        confirmation=CONFIRMATION_TEXT,
                        expected_checkpoint_head=checkpoint["checkpoint_head"],
                        gate_runner=successful_gate,
                        gate_log_path=root / "gate.log",
                        thread_id="canonical-thread",
                        deployment_receipt_path=receipt_path,
                    )

            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            confirmation = load_deployment_confirmation(
                receipt_path,
                thread_id="canonical-thread",
            )

        self.assertEqual(receipt["state"], DEPLOYMENT_PENDING)
        self.assertIsNone(confirmation)

    def test_failed_gate_and_wrong_token_leave_main_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, manager, checkpoint = prepare_checkpoint(root)
            original = git(source, "rev-parse", "HEAD")
            receipt_path = root / "failed-deployment-receipt.json"
            with self.assertRaises(HumanAdamDeployError):
                deploy_checkpoint(
                    workspace=manager,
                    confirmation=CONFIRMATION_TEXT,
                    expected_checkpoint_head="0" * 40,
                    gate_runner=successful_gate,
                    gate_log_path=root / "wrong-token.log",
                )
            with self.assertRaises(HumanAdamDeployError):
                deploy_checkpoint(
                    workspace=manager,
                    confirmation=CONFIRMATION_TEXT,
                    expected_checkpoint_head=checkpoint["checkpoint_head"],
                    gate_runner=failing_gate,
                    gate_log_path=root / "failed-gate.log",
                    thread_id="canonical-thread",
                    deployment_receipt_path=receipt_path,
                )
            source_after = git(source, "rev-parse", "HEAD")
            status = manager.status()

        self.assertEqual(source_after, original)
        self.assertEqual(status["workspace_relation"], "local_ahead")
        self.assertFalse(receipt_path.exists())

    def test_deploy_requires_exact_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _source, manager, checkpoint = prepare_checkpoint(root)
            with self.assertRaises(HumanAdamDeployError):
                deploy_checkpoint(
                    workspace=manager,
                    confirmation="ano",
                    expected_checkpoint_head=checkpoint["checkpoint_head"],
                    gate_runner=successful_gate,
                    gate_log_path=root / "unused.log",
                )


if __name__ == "__main__":
    unittest.main()
