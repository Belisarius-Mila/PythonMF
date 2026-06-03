from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

import app.workflows.commands as workflow_commands
from app.workflows.commands import (
    WorkflowCommand,
    list_workflow_commands_text,
    preview_workflow_command_text,
    run_workflow_command_text,
)


class WorkflowCommandTests(unittest.TestCase):
    def test_lists_registered_exact_commands(self) -> None:
        result = list_workflow_commands_text()

        self.assertIn("backup_project_recovery", result)
        self.assertIn(".venv/bin/python", result)
        self.assertIn("backup_samantha_python.py", result)
        self.assertIn("--execute --profile recovery", result)
        self.assertIn("Samantha smi spoustet jen prikazy z tohoto registru", result)

    def test_human_backup_request_maps_to_exact_command_preview(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            original_commands = workflow_commands.WORKFLOW_COMMANDS
            pending = Path(temp_dir) / "pending.json"
            command = WorkflowCommand(
                command_id="backup_project_recovery",
                title="Ostra recovery zaloha PythonMF/Samantha",
                purpose="Testovaci zaloha",
                aliases=("zalohuj data projektu",),
                argv=(
                    "/tmp/backup_samantha.command",
                    "--execute",
                    "--profile",
                    "recovery",
                    "--target",
                    "/Volumes/SamanthaSecureBackup/SamanthaBackups",
                ),
                cwd=Path(temp_dir),
                risk="external_backup_write",
                writes="/Volumes/SamanthaSecureBackup/SamanthaBackups",
                requires_confirmation=True,
            )
            workflow_commands.WORKFLOW_COMMANDS = (command,)

            try:
                result = preview_workflow_command_text(
                    "Zalohuj data projektu",
                    pending_path=pending,
                )
            finally:
                workflow_commands.WORKFLOW_COMMANDS = original_commands

            self.assertIn("backup_project_recovery", result)
            self.assertIn("Presny shell prikaz", result)
            self.assertIn("--execute --profile recovery", result)
            self.assertIn("/Volumes/SamanthaSecureBackup/SamanthaBackups", result)
            self.assertIn("Pro spusteni napis `ano`", result)
            self.assertIn("Nahled nic nespustil", result)
            self.assertTrue(pending.exists())

    def test_semantic_backup_request_does_not_need_exact_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = preview_workflow_command_text(
                "Chci zazalohovat praci na disk",
                pending_path=Path(temp_dir) / "pending.json",
            )

        self.assertIn("backup_project_recovery", result)
        self.assertIn("--execute --profile recovery", result)

    def test_weak_generic_request_does_not_match_backup(self) -> None:
        result = preview_workflow_command_text("Uloz to")

        self.assertIn("Nenasla jsem odpovidajici workflow prikaz", result)

    def test_unknown_request_is_not_run(self) -> None:
        result = run_workflow_command_text("Udelej neco neurciteho")

        self.assertIn("Nenasla jsem odpovidajici workflow prikaz", result)

    def test_registered_command_runs_without_shell_improvisation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            original_commands = workflow_commands.WORKFLOW_COMMANDS
            command = WorkflowCommand(
                command_id="test_echo",
                title="Test echo",
                purpose="Testovaci prikaz",
                aliases=("lidsky test prikaz",),
                argv=("/bin/echo", "ok"),
                cwd=Path(temp_dir),
                risk="test",
                writes="nic",
            )
            workflow_commands.WORKFLOW_COMMANDS = (command,)
            calls: list[list[str]] = []

            def fake_runner(*args, **kwargs):
                calls.append(args[0])
                return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="done\n", stderr="")

            try:
                result = run_workflow_command_text("lidsky test prikaz", runner=fake_runner)
            finally:
                workflow_commands.WORKFLOW_COMMANDS = original_commands

            self.assertEqual(calls, [["/bin/echo", "ok"]])
            self.assertIn("Workflow prikaz dokoncen", result)
            self.assertIn("test_echo", result)
            self.assertIn("/bin/echo ok", result)

    def test_confirmation_gate_for_risky_registered_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            original_commands = workflow_commands.WORKFLOW_COMMANDS
            command = WorkflowCommand(
                command_id="test_risky",
                title="Risky test",
                purpose="Testovaci prikaz s potvrzenim",
                aliases=("riskantni test",),
                argv=("/bin/echo", "ok"),
                cwd=Path(temp_dir),
                risk="write",
                writes="test",
                requires_confirmation=True,
            )
            workflow_commands.WORKFLOW_COMMANDS = (command,)

            try:
                pending = Path(temp_dir) / "pending.json"
                preview_workflow_command_text("riskantni test", pending_path=pending)
                rejected = run_workflow_command_text(
                    "riskantni test",
                    pending_path=pending,
                )
                accepted = run_workflow_command_text(
                    "ano",
                    user_confirmed=True,
                    confirmation_text="ano",
                    pending_path=pending,
                    runner=lambda *args, **kwargs: subprocess.CompletedProcess(
                        args=args[0],
                        returncode=0,
                        stdout="done\n",
                        stderr="",
                    ),
                )
            finally:
                workflow_commands.WORKFLOW_COMMANDS = original_commands

            self.assertIn("chybi samostatne potvrzeni", rejected)
            self.assertIn("Workflow prikaz dokoncen", accepted)
            self.assertFalse(pending.exists())


if __name__ == "__main__":
    unittest.main()
