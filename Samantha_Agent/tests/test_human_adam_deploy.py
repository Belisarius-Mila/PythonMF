from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.communication.human_adam_deploy import (
    DEPLOYMENT_PENDING,
    MAX_DEPLOYMENT_FAILURE_RECORDS,
    HumanAdamDeployError,
    TRUSTED_PYTHON,
    audit_checkpoint,
    deploy_checkpoint,
    human_adam_deploy_action,
    human_adam_deploy_audit_action,
    load_deployment_confirmation,
    load_deployment_diagnostic,
    load_deployment_failure_history,
    record_deployment_restart,
    write_deployment_failure,
    write_deployment_receipt,
)
from scripts.human_adam_takeover import CONFIRMATION_TEXT, TakeoverError
from tests.test_human_adam_takeover import prepare_with_origin
from tests.test_human_adam_workspace import git


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


def syntax_failing_gate(command, **_kwargs):
    return subprocess.CompletedProcess(
        command,
        1,
        stdout="Python syntax: FAILED\nSyntaxError: tajná /private/example\n",
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

    def test_profile_audit_attaches_nonblocking_handoff_check_without_changing_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _source, manager, _checkpoint = prepare_checkpoint(Path(temp_dir))
            active_service = SimpleNamespace(
                hub=SimpleNamespace(snapshot=lambda: {"turn_busy": False}),
                workspace=manager,
                work_profile_id="human_adam",
            )
            calls: dict[str, object] = {}

            @contextmanager
            def profile_operation():
                yield active_service

            def assert_deployment_allowed(owner_id: str) -> None:
                calls["owner_id"] = owner_id

            def takeover_handoff_check(**kwargs: object) -> dict[str, object]:
                calls["check_kwargs"] = kwargs
                return {
                    "ok": True,
                    "state": "warning",
                    "blocking": False,
                    "writes_performed": False,
                }

            wrapper = SimpleNamespace(
                profile_operation=profile_operation,
                assert_deployment_allowed=assert_deployment_allowed,
                takeover_handoff_check=takeover_handoff_check,
            )
            result = human_adam_deploy_audit_action(service=wrapper)

        self.assertTrue(result["ready"])
        self.assertEqual(result["handoff_takeover_check"]["state"], "warning")
        self.assertFalse(result["handoff_takeover_check"]["blocking"])
        self.assertEqual(calls["owner_id"], "human_adam")
        self.assertIs(calls["check_kwargs"]["active_service"], active_service)

    def test_profile_deploy_prepares_post_restart_completion_and_keeps_lease(self) -> None:
        active_service = SimpleNamespace(
            hub=SimpleNamespace(snapshot=lambda: {"turn_busy": False, "thread_id": "thread"}),
            workspace=SimpleNamespace(),
            deployment_receipt_path=Path("receipt.json"),
            deployment_diagnostic_path=Path("diagnostic.json"),
            deployment_failure_history_path=Path("failures.json"),
            work_profile_id="human_adam",
        )
        calls: dict[str, object] = {}

        @contextmanager
        def profile_operation():
            yield active_service

        def prepare_deployment_completion(**kwargs: object) -> dict[str, object]:
            calls["prepare"] = kwargs
            return {"ok": True, "state": "pending_restart"}

        wrapper = SimpleNamespace(
            profile_operation=profile_operation,
            assert_deployment_allowed=lambda owner_id: calls.update(owner_id=owner_id),
            prepare_deployment_completion=prepare_deployment_completion,
            finish_deployment_lease=lambda _owner_id: self.fail("lease must remain active"),
        )
        deployed = {
            "applied": True,
            "checkpoint_token": "a" * 40,
            "gate": {"test_count": 849},
            "deployment_confirmation": {"completed_at": "2026-07-19T12:55:31+00:00"},
            "restart_required": True,
        }
        with patch("app.communication.human_adam_deploy.deploy_checkpoint", return_value=deployed):
            result = human_adam_deploy_action(
                {"confirmation": CONFIRMATION_TEXT, "checkpoint_token": "a" * 40, "_server_pid": 321},
                service=wrapper,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["deployment_completion"]["state"], "pending_restart")
        self.assertIn("zůstává aktivní", result["development_semaphore_message"])
        self.assertEqual(calls["prepare"]["previous_pid"], 321)

    def test_deploy_runs_gate_then_fast_forwards_pushes_and_aligns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, manager, checkpoint = prepare_checkpoint(root)
            receipt_path = root / "deployment_receipt.json"
            diagnostic_path = root / "deployment_diagnostic.json"
            failure_history_path = root / "deployment_failures.json"
            write_deployment_failure(
                failure_history_path,
                profile_id="human_adam",
                checkpoint_head="f" * 40,
                stage="audit",
                failure_type="audit_failure",
                recorded_at="2026-07-16T20:31:00+00:00",
            )
            result = deploy_checkpoint(
                workspace=manager,
                confirmation=CONFIRMATION_TEXT,
                expected_checkpoint_head=checkpoint["checkpoint_head"],
                gate_runner=successful_gate,
                gate_log_path=root / "gate.log",
                thread_id="canonical-thread",
                deployment_receipt_path=receipt_path,
                deployment_diagnostic_path=diagnostic_path,
                deployment_failure_history_path=failure_history_path,
                profile_id="human_adam",
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
            failure_history = load_deployment_failure_history(failure_history_path)

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
        self.assertEqual(len(failure_history), 1)
        self.assertEqual(failure_history[0]["checkpoint_head"], "f" * 40)

    def test_push_failure_persists_safe_exact_stage_without_exception_detail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _source, manager, checkpoint = prepare_checkpoint(root)
            diagnostic_path = root / "deployment_diagnostic.json"
            failure_history_path = root / "deployment_failures.json"

            def fail_during_push(*, progress_callback, **_kwargs):
                progress_callback("remote_recheck", "running")
                progress_callback("remote_recheck", "passed")
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
                        deployment_failure_history_path=failure_history_path,
                        profile_id="knihovna",
                    )

            diagnostic_text = diagnostic_path.read_text(encoding="utf-8")
            diagnostic = load_deployment_diagnostic(
                diagnostic_path,
                thread_id="canonical-thread",
            )
            failure_history_text = failure_history_path.read_text(encoding="utf-8")
            failure_history = load_deployment_failure_history(failure_history_path)

        self.assertEqual(diagnostic["stage"], "push")
        self.assertEqual(diagnostic["outcome"], "failed")
        self.assertNotIn("tajná", str(raised.exception))
        self.assertNotIn("private", diagnostic_text)
        self.assertNotIn("example", diagnostic_text)
        self.assertEqual(
            failure_history,
            [
                {
                    "recorded_at": failure_history[0]["recorded_at"],
                    "profile_id": "knihovna",
                    "checkpoint_head": checkpoint["checkpoint_head"],
                    "stage": "push",
                    "failure_type": "push_failure",
                }
            ],
        )
        self.assertNotIn("tajná", failure_history_text)
        self.assertNotIn("private", failure_history_text)
        self.assertNotIn("example", failure_history_text)

    def test_restart_result_is_persistent_safe_and_thread_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            diagnostic_path = Path(temp_dir) / "deployment_diagnostic.json"
            failure_history_path = Path(temp_dir) / "deployment_failures.json"
            service = SimpleNamespace(
                hub=SimpleNamespace(snapshot=lambda: {"thread_id": "canonical-thread"}),
                deployment_diagnostic_path=diagnostic_path,
                deployment_failure_history_path=failure_history_path,
                work_profile_id="human_adam",
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
            failure_history = load_deployment_failure_history(failure_history_path)

        self.assertEqual(running["stage"], "restart")
        self.assertEqual(running["outcome"], "running")
        self.assertEqual(failed["outcome"], "failed")
        self.assertIsNone(wrong_thread)
        self.assertNotIn("canonical-thread", diagnostic_text)
        self.assertEqual(failure_history[0]["stage"], "restart")
        self.assertEqual(failure_history[0]["failure_type"], "restart_failure")

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
            failure_history_path = root / "deployment_failures.json"
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
                    deployment_failure_history_path=failure_history_path,
                    profile_id="human_adam",
                )
            source_after = git(source, "rev-parse", "HEAD")
            status = manager.status()
            failure_history = load_deployment_failure_history(failure_history_path)

        self.assertEqual(source_after, original)
        self.assertEqual(status["workspace_relation"], "local_ahead")
        self.assertFalse(receipt_path.exists())
        self.assertEqual(failure_history[0]["stage"], "gate")
        self.assertEqual(failure_history[0]["failure_type"], "test_failure")

    def test_syntax_failure_is_categorized_without_storing_gate_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _source, manager, checkpoint = prepare_checkpoint(root)
            failure_history_path = root / "deployment_failures.json"

            with self.assertRaises(HumanAdamDeployError):
                deploy_checkpoint(
                    workspace=manager,
                    confirmation=CONFIRMATION_TEXT,
                    expected_checkpoint_head=checkpoint["checkpoint_head"],
                    gate_runner=syntax_failing_gate,
                    gate_log_path=root / "failed-gate.log",
                    thread_id="canonical-thread",
                    deployment_failure_history_path=failure_history_path,
                    profile_id="human_adam",
                )

            failure_history_text = failure_history_path.read_text(encoding="utf-8")
            failure_history = load_deployment_failure_history(failure_history_path)

        self.assertEqual(failure_history[0]["failure_type"], "syntax_error")
        self.assertNotIn("tajná", failure_history_text)
        self.assertNotIn("private", failure_history_text)
        self.assertNotIn("example", failure_history_text)

    def test_failure_history_is_strict_and_keeps_only_newest_twenty_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "deployment_failures.json"
            for index in range(MAX_DEPLOYMENT_FAILURE_RECORDS + 5):
                write_deployment_failure(
                    history_path,
                    profile_id="human_adam",
                    checkpoint_head=f"{index:040x}",
                    stage="audit",
                    failure_type="audit_failure",
                    recorded_at=f"2026-07-17T20:31:{index:02d}+00:00",
                )

            history = load_deployment_failure_history(history_path)

        self.assertEqual(len(history), MAX_DEPLOYMENT_FAILURE_RECORDS)
        self.assertEqual(history[0]["checkpoint_head"], f"{5:040x}")
        self.assertEqual(history[-1]["checkpoint_head"], f"{24:040x}")
        self.assertEqual(
            set(history[-1]),
            {"recorded_at", "profile_id", "checkpoint_head", "stage", "failure_type"},
        )

    def test_separate_audit_failure_is_registered_without_exception_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _source, manager, checkpoint = prepare_checkpoint(root)
            history_path = root / "deployment_failures.json"
            service = SimpleNamespace(
                hub=SimpleNamespace(snapshot=lambda: {"turn_busy": False}),
                workspace=manager,
                deployment_failure_history_path=history_path,
                work_profile_id="knihovna",
            )

            with patch(
                "app.communication.human_adam_deploy.audit_checkpoint",
                side_effect=TakeoverError("tajná /private/example"),
            ):
                result = human_adam_deploy_audit_action(service=service)

            history_text = history_path.read_text(encoding="utf-8")
            history = load_deployment_failure_history(history_path)

        self.assertFalse(result["ok"])
        self.assertEqual(history[0]["checkpoint_head"], checkpoint["checkpoint_head"])
        self.assertEqual(history[0]["profile_id"], "knihovna")
        self.assertEqual(history[0]["failure_type"], "audit_failure")
        self.assertNotIn("tajná", history_text)
        self.assertNotIn("private", history_text)
        self.assertNotIn("example", history_text)

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
