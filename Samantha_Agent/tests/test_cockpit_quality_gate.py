from __future__ import annotations

import re
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.cockpit_quality_gate import (
    ARCHITECTURE_BASELINES,
    COMPILE_PATHS,
    PROJECT_ROOT,
    TEST_MODULES,
    SourceMetrics,
    architecture_messages,
    cockpit_javascript_source,
    janicka_r2_javascript_source,
    node_binary,
    r2_adam_chat_javascript_source,
    scandocu_javascript_source,
    source_metrics,
    run_checked,
    main as gate_main,
)
from scripts.cockpit_test_timing import run_timed_suite


class CockpitQualityGateTests(unittest.TestCase):
    def test_timing_accounts_for_tests_and_separates_fixture_overhead(self) -> None:
        suite = unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])
        ticks = iter([10.0, 11.0, 15.0, 18.0])
        result, report = run_timed_suite(suite, load_seconds=2.0,
                                       stream=io.StringIO(), clock=lambda: next(ticks))
        self.assertTrue(result.wasSuccessful())
        self.assertEqual(report["test_count"], 1)
        self.assertEqual(report["load_seconds"], 2.0)
        self.assertEqual(report["run_seconds"], 8.0)
        self.assertEqual(report["measured_test_seconds"], 4.0)
        self.assertEqual(report["unmeasured_run_seconds"], 4.0)
        self.assertEqual(report["modules"][0]["seconds"], 4.0)

    def test_timing_preserves_order_fixtures_outcomes_and_excludes_private_messages(self) -> None:
        events = []

        class Fixture(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                events.append("class setup")

            @classmethod
            def tearDownClass(cls):
                events.append("class teardown")

            def setUp(self):
                events.append(self._testMethodName)

            def test_pass(self):
                pass

            def test_fail(self):
                self.fail("PRIVATE_FIXTURE_MESSAGE")

            def test_error(self):
                raise ValueError("PRIVATE_FIXTURE_MESSAGE")

            @unittest.skip("PRIVATE_FIXTURE_MESSAGE")
            def test_skip(self):
                pass

            @unittest.expectedFailure
            def test_expected_failure(self):
                self.fail("PRIVATE_FIXTURE_MESSAGE")

            @unittest.expectedFailure
            def test_unexpected_success(self):
                pass

        names = ["test_pass", "test_skip", "test_fail", "test_error",
                 "test_expected_failure", "test_unexpected_success"]
        def suite():
            return unittest.TestSuite([Fixture(name) for name in names])

        baseline = unittest.TextTestRunner(stream=io.StringIO()).run(suite())
        expected_events = list(events)
        events.clear()
        measured, report = run_timed_suite(suite(), stream=io.StringIO())
        self.assertEqual(events, expected_events)
        self.assertEqual(measured.testsRun, baseline.testsRun)
        self.assertEqual(measured.wasSuccessful(), baseline.wasSuccessful())
        for attribute in ("failures", "errors", "skipped", "expectedFailures", "unexpectedSuccesses"):
            self.assertEqual(len(getattr(measured, attribute)), len(getattr(baseline, attribute)))
        self.assertEqual(report["test_count"], 6)
        self.assertFalse(report["success"])
        self.assertNotIn("PRIVATE_FIXTURE_MESSAGE", json.dumps(report))

    def test_timing_cli_preserves_success_failure_and_empty_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            fixture = root / "timing_fixture.py"
            fixture.write_text("import unittest\nclass Example(unittest.TestCase):\n"
                               " def test_pass(self): pass\n"
                               " def test_fail(self): self.fail('synthetic failure')\n"
                               "class Empty(unittest.TestCase): pass\n")
            for target, expected in [("Example.test_pass", 0), ("Example.test_fail", 1), ("Empty", 5)]:
                with self.subTest(target=target):
                    command = [sys.executable, "-c", "import sys; sys.path.insert(0, sys.argv.pop(1)); "
                               "from scripts.cockpit_test_timing import main; sys.exit(main())",
                               str(root), "--output", str(root / "timing.json"), f"timing_fixture.{target}"]
                    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=20)
                    self.assertEqual(result.returncode, expected, result.stderr)
                    report = json.loads((root / "timing.json").read_text())
                    self.assertEqual(report["success"], expected == 0)

    def test_optional_timing_uses_exact_same_module_list_and_default_command(self) -> None:
        for args, expected_prefix in [([], [sys.executable, "-m", "unittest"]),
            (["--unit-test-timings", "/tmp/synthetic-timing.json"],
             [sys.executable, "-m", "scripts.cockpit_test_timing", "--output", "/tmp/synthetic-timing.json"])]:
            with self.subTest(args=args), patch("scripts.cockpit_quality_gate.run_checked") as run, \
                    patch("builtins.print"):
                self.assertEqual(gate_main(args), 0)
                command = next(call.args[1] for call in run.call_args_list if call.args[0] == "unit tests")
                self.assertEqual(command, [*expected_prefix, *TEST_MODULES])

    def test_timing_cannot_be_requested_when_unit_tests_are_skipped(self) -> None:
        with patch("scripts.cockpit_quality_gate.run_checked") as run, \
                patch("sys.stderr", io.StringIO()), self.assertRaises(SystemExit) as stopped:
            gate_main(["--skip-unit-tests", "--unit-test-timings", "/tmp/synthetic-timing.json"])
        self.assertEqual(stopped.exception.code, 2)
        run.assert_not_called()

    def test_scandocu_pages_javascript_is_included_in_syntax_gate(self) -> None:
        source = scandocu_javascript_source()

        self.assertIn("async function requestAiSuggestion()", source)
        self.assertIn("async function loadDocuments()", source)

    def test_janicka_r2_page_javascript_is_included_in_syntax_gate(self) -> None:
        source = janicka_r2_javascript_source()

        self.assertIn("async function searchDocuments()", source)
        self.assertIn("async function createDocument()", source)

    def test_r2_adam_chat_javascript_is_included_in_syntax_gate(self) -> None:
        source = r2_adam_chat_javascript_source()

        self.assertIn("async function ensureConnected()", source)
        self.assertIn("async function sendMessage(event)", source)
        self.assertIn("async function loadDocument()", source)

    def test_workflow_triggers_cover_communication_layer_and_match(self) -> None:
        workflow_path = PROJECT_ROOT.parent / ".github" / "workflows" / "cockpit-quality-gate.yml"
        source = workflow_path.read_text(encoding="utf-8")

        def trigger_paths(trigger: str, end_marker: str) -> set[str]:
            start = source.index(f"  {trigger}:")
            end = source.index(end_marker, start)
            block = source[start:end]
            return set(re.findall(r'^\s+- "([^"]+)"$', block, flags=re.MULTILINE))

        pull_request_paths = trigger_paths("pull_request", "  push:")
        push_paths = trigger_paths("push", "\npermissions:")
        required = {
            ".github/workflows/cockpit-quality-gate.yml",
            "Samantha_Agent/app/cockpit_frontend.py",
            "Samantha_Agent/app/cockpit_readonly_routes.py",
            "Samantha_Agent/app/frontend/**",
            "Samantha_Agent/app/communication/**",
            "Samantha_Agent/tests/test_communication*.py",
            "Samantha_Agent/tests/test_human_adam*.py",
            "Samantha_Agent/tests/test_simple_main_*.py",
            "Samantha_Agent/tests/test_local_appserver_runtime.py",
            "Samantha_Agent/app/family_calendar.py",
            "Samantha_Agent/app/family_calendar_delivery*.py",
            "Samantha_Agent/tests/test_family_calendar*.py",
        }

        self.assertEqual(pull_request_paths, push_paths)
        self.assertTrue(required.issubset(push_paths), required - push_paths)

    def test_source_metrics_counts_only_top_level_definitions(self) -> None:
        source = """class Example:
    def nested_method(self):
        return True

def first():
    return 1

async def second():
    return 2
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "sample.py"
            path.write_text(source, encoding="utf-8")

            metrics = source_metrics(path)

        self.assertEqual(metrics, SourceMetrics(lines=9, functions=2, classes=1))

    def test_quality_gate_manifest_paths_and_modules_are_unique(self) -> None:
        self.assertEqual(len(COMPILE_PATHS), len(set(COMPILE_PATHS)))
        self.assertEqual(len(TEST_MODULES), len(set(TEST_MODULES)))
        for relative_path in COMPILE_PATHS:
            self.assertTrue((PROJECT_ROOT / relative_path).is_file(), relative_path)
        self.assertIn("tests.test_cockpit", TEST_MODULES)
        self.assertIn("tests.test_cockpit_awake_mode", TEST_MODULES)
        self.assertIn("tests.test_cockpit_fast_feedback", TEST_MODULES)
        self.assertIn("tests.test_cockpit_frontend", TEST_MODULES)
        self.assertIn("tests.test_library_photos", TEST_MODULES)
        self.assertIn("tests.test_article_archive", TEST_MODULES)
        self.assertIn("tests.test_cockpit_readonly_routes", TEST_MODULES)
        self.assertIn("scripts/cockpit_fast_feedback.py", COMPILE_PATHS)
        self.assertIn("app/cockpit_frontend.py", COMPILE_PATHS)
        self.assertIn("app/cockpit_awake_mode.py", COMPILE_PATHS)
        self.assertIn("app/cockpit_readonly_routes.py", COMPILE_PATHS)
        self.assertIn("app/email/archive_browser.py", COMPILE_PATHS)
        self.assertIn("tests.test_email_archive_browser", TEST_MODULES)
        self.assertIn("app/documents/archive_browser.py", COMPILE_PATHS)
        self.assertIn("tests.test_document_archive_browser", TEST_MODULES)
        self.assertIn("tests.test_cockpit_scandocu_proxy", TEST_MODULES)
        self.assertNotIn("tests.test_adam_voice_mode", TEST_MODULES)
        self.assertIn("tests.test_codex_approval_cockpit_contract", TEST_MODULES)
        self.assertIn("tests.test_codex_approval_state", TEST_MODULES)
        self.assertIn("tests.test_cockpit_voice_frontend_retirement", TEST_MODULES)
        self.assertIn("tests.test_human_adam_profiles", TEST_MODULES)
        self.assertIn("app/communication/mmtx_pages_deploy.py", COMPILE_PATHS)
        self.assertIn("tests.test_mmtx_pages_deploy", TEST_MODULES)
        self.assertIn("tests.test_janicka_r2_documents", TEST_MODULES)
        self.assertIn("tests.test_cockpit_quality_gate", TEST_MODULES)
        self.assertIn("tests.test_capability_audit", TEST_MODULES)
        self.assertIn("tests.test_decision_cockpit", TEST_MODULES)
        self.assertIn("tests.test_command_cheatsheet", TEST_MODULES)
        self.assertNotIn("app/adam_service.py", COMPILE_PATHS)
        self.assertNotIn("tests.test_adam_service", TEST_MODULES)
        self.assertFalse((PROJECT_ROOT / "app" / "adam_service.py").exists())
        self.assertFalse((PROJECT_ROOT / "tests" / "test_adam_service.py").exists())
        self.assertIn("app/codex_approval_state.py", COMPILE_PATHS)
        self.assertIn("app/decision_cockpit.py", COMPILE_PATHS)
        self.assertIn("app/communication/human_adam_profiles.py", COMPILE_PATHS)
        self.assertIn(
            "app/communication/janicka_r2_cockpit.py",
            COMPILE_PATHS,
        )
        self.assertIn(
            "app/communication/janicka_r2_chat.py",
            COMPILE_PATHS,
        )
        self.assertIn(
            "app/communication/janicka_r2_compiler.py",
            COMPILE_PATHS,
        )
        self.assertIn(
            "app/communication/janicka_r2_document_selection.py",
            COMPILE_PATHS,
        )
        self.assertIn(
            "app/communication/janicka_r2_documents.py",
            COMPILE_PATHS,
        )
        self.assertIn(
            "app/communication/workstream_live_status.py",
            COMPILE_PATHS,
        )
        self.assertIn("tests.test_janicka_r2_cockpit", TEST_MODULES)
        self.assertIn("tests.test_janicka_r2_chat", TEST_MODULES)
        self.assertIn("tests.test_janicka_r2_complete_selection", TEST_MODULES)
        self.assertIn("app/command_cheatsheet.py", COMPILE_PATHS)
        self.assertIn("app/development_branch_lifecycle.py", COMPILE_PATHS)
        self.assertIn("scripts/development_branch_audit.py", COMPILE_PATHS)
        self.assertIn("tests.test_development_branch_lifecycle", TEST_MODULES)
        self.assertIn("tests.test_project_continuity", TEST_MODULES)
        self.assertIn("app/project_continuity.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_automatic.py", COMPILE_PATHS)
        self.assertIn(
            "app/family_calendar_delivery_automation_activation.py",
            COMPILE_PATHS,
        )
        self.assertIn(
            "app/family_calendar_delivery_automation_preview.py",
            COMPILE_PATHS,
        )
        self.assertIn("app/family_calendar_icloud_smtp_client.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_test_email.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_config.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_config_initializer.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_config_migration.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_config_migration_runner.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_config_transition.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_readiness.py", COMPILE_PATHS)
        self.assertIn("app/communication/human_adam_operations.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_coordinator.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_dry_run.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_message.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_planner_install.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_keychain_setup.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_keychain.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_launchctl_load.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_launchctl_preview.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_planner_preview.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_runner.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_store.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_smtp_adapter.py", COMPILE_PATHS)
        self.assertIn("scripts/family_calendar_delivery_config_initialize.py", COMPILE_PATHS)
        self.assertIn("scripts/family_calendar_delivery_automatic.py", COMPILE_PATHS)
        self.assertIn(
            "scripts/family_calendar_delivery_automation_activate.py",
            COMPILE_PATHS,
        )
        self.assertIn(
            "scripts/family_calendar_delivery_automation_preview.py",
            COMPILE_PATHS,
        )
        self.assertIn("scripts/family_calendar_delivery_config_enable_dry_run.py", COMPILE_PATHS)
        self.assertIn("scripts/family_calendar_delivery_config_migrate.py", COMPILE_PATHS)
        self.assertIn("scripts/family_calendar_delivery_dry_run.py", COMPILE_PATHS)
        self.assertIn(
            "scripts/family_calendar_delivery_planner_install.py",
            COMPILE_PATHS,
        )
        self.assertIn(
            "scripts/family_calendar_delivery_keychain_setup.py",
            COMPILE_PATHS,
        )
        self.assertIn(
            "scripts/family_calendar_delivery_launchctl_load.py",
            COMPILE_PATHS,
        )
        self.assertIn(
            "scripts/family_calendar_delivery_launchctl_preview.py",
            COMPILE_PATHS,
        )
        self.assertIn(
            "scripts/family_calendar_delivery_planner_preview.py",
            COMPILE_PATHS,
        )
        self.assertIn("scripts/family_calendar_delivery_run.py", COMPILE_PATHS)
        self.assertIn("scripts/family_calendar_delivery_readiness.py", COMPILE_PATHS)
        self.assertIn(
            "scripts/family_calendar_delivery_smtp_envelope_diagnose.py",
            COMPILE_PATHS,
        )
        self.assertIn(
            "scripts/family_calendar_delivery_smtp_diagnose.py",
            COMPILE_PATHS,
        )
        self.assertIn("scripts/family_calendar_delivery_test_email.py", COMPILE_PATHS)
        self.assertIn("tests.test_family_calendar_delivery", TEST_MODULES)
        self.assertIn("tests.test_family_calendar_delivery_automatic", TEST_MODULES)
        self.assertIn(
            "tests.test_family_calendar_delivery_automation_activation",
            TEST_MODULES,
        )
        self.assertIn(
            "tests.test_family_calendar_delivery_automation_preview",
            TEST_MODULES,
        )
        self.assertIn("tests.test_family_calendar_icloud_smtp_client", TEST_MODULES)
        self.assertIn("tests.test_family_calendar_delivery_test_email", TEST_MODULES)
        self.assertIn("tests.test_family_calendar_delivery_config", TEST_MODULES)
        self.assertIn("tests.test_family_calendar_delivery_config_initializer", TEST_MODULES)
        self.assertIn("tests.test_family_calendar_delivery_config_migration", TEST_MODULES)
        self.assertIn("tests.test_family_calendar_delivery_config_migration_runner", TEST_MODULES)
        self.assertIn("tests.test_family_calendar_delivery_config_transition", TEST_MODULES)
        self.assertIn("tests.test_human_adam_operations", TEST_MODULES)
        self.assertIn("tests.test_workstream_live_status", TEST_MODULES)
        self.assertIn("tests.test_family_calendar_delivery_coordinator", TEST_MODULES)
        self.assertIn("tests.test_family_calendar_delivery_dry_run", TEST_MODULES)
        self.assertIn("tests.test_family_calendar_delivery_integration", TEST_MODULES)
        self.assertIn("tests.test_family_calendar_delivery_message", TEST_MODULES)
        self.assertIn(
            "tests.test_family_calendar_delivery_planner_install",
            TEST_MODULES,
        )
        self.assertIn(
            "tests.test_family_calendar_delivery_keychain_setup",
            TEST_MODULES,
        )
        self.assertIn(
            "tests.test_family_calendar_delivery_launchctl_load",
            TEST_MODULES,
        )
        self.assertIn(
            "tests.test_family_calendar_delivery_launchctl_preview",
            TEST_MODULES,
        )
        self.assertIn(
            "tests.test_family_calendar_delivery_planner_preview",
            TEST_MODULES,
        )
        self.assertIn("tests.test_family_calendar_delivery_readiness", TEST_MODULES)
        self.assertIn("tests.test_family_calendar_delivery_keychain", TEST_MODULES)
        self.assertIn("tests.test_family_calendar_delivery_runner", TEST_MODULES)
        self.assertIn("tests.test_family_calendar_delivery_store", TEST_MODULES)
        self.assertIn(
            "tests.test_family_calendar_delivery_smtp_envelope_diagnostic",
            TEST_MODULES,
        )
        self.assertIn(
            "tests.test_family_calendar_delivery_smtp_diagnostic",
            TEST_MODULES,
        )
        self.assertIn("tests.test_family_calendar_smtp_adapter", TEST_MODULES)

    def test_architecture_baselines_are_informational_and_reported(self) -> None:
        messages = architecture_messages()

        self.assertEqual(len(ARCHITECTURE_BASELINES), 1)
        self.assertTrue(any("app/cockpit.py" in message for message in messages))
        self.assertFalse(any("app/speech/adam_voice_mode.py" in message for message in messages))

    def test_orphaned_human_adam_deploy_module_is_absent(self) -> None:
        legacy_source = "app/communication/human_adam_deploy.py"
        legacy_test = "tests.test_human_adam_deploy"

        self.assertNotIn(legacy_source, COMPILE_PATHS)
        self.assertNotIn(legacy_test, TEST_MODULES)
        self.assertFalse((PROJECT_ROOT / legacy_source).exists())
        self.assertFalse((PROJECT_ROOT / "tests/test_human_adam_deploy.py").exists())

    def test_dead_voice_bridge_entry_layers_are_not_in_quality_gate(self) -> None:
        retired_sources = (
            "app/voice_bridge_coordinator.py",
            "app/voice_bridge_runtime.py",
            "app/voice_bridge_state.py",
            "app/speech/adam_voice_mode.py",
            "app/speech/terminal_bridge.py",
            "app/speech/voice_inbox.py",
            "app/tvbcp.py",
            "scripts/adam_voice_reply.py",
            "scripts/tvbcp.py",
        )
        retired_tests = (
            "tests.test_voice_bridge_coordinator",
            "tests.test_voice_bridge_runtime",
            "tests.test_voice_bridge_state",
            "tests.test_adam_voice_mode",
            "tests.test_terminal_bridge",
            "tests.test_tvbcp",
            "tests.test_voice_inbox",
        )

        for retired_source in retired_sources:
            with self.subTest(retired_source=retired_source):
                self.assertNotIn(retired_source, COMPILE_PATHS)
                self.assertFalse((PROJECT_ROOT / retired_source).exists())
        for retired_test in retired_tests:
            with self.subTest(retired_test=retired_test):
                self.assertNotIn(retired_test, TEST_MODULES)
                self.assertFalse(
                    (PROJECT_ROOT / f"{retired_test.replace('.', '/')}.py").exists()
                )

    def test_cockpit_javascript_source_extracts_rendered_script(self) -> None:
        source = cockpit_javascript_source()

        self.assertIn("async function refresh(", source)
        self.assertIn('join("\\n")', source)
        self.assertNotIn("</script>", source)

    def test_node_binary_uses_explicit_executable_without_shell_path(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            executable = Path(temp_dir) / "node"
            executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            executable.chmod(0o755)
            with (
                patch.dict("os.environ", {"NODE_BINARY": str(executable)}, clear=True),
                patch("scripts.cockpit_quality_gate.shutil.which", return_value=None),
            ):
                resolved = node_binary()

        self.assertEqual(resolved, str(executable))

    def test_node_binary_fails_clearly_when_no_candidate_exists(self) -> None:
        with (
            patch.dict("os.environ", {}, clear=True),
            patch("scripts.cockpit_quality_gate.shutil.which", return_value=None),
            patch("scripts.cockpit_quality_gate.NODE_FALLBACK_PATHS", ()),
            self.assertRaisesRegex(SystemExit, "NODE_BINARY"),
        ):
            node_binary()

    def test_failed_ci_command_emits_safe_github_annotation(self) -> None:
        completed = type(
            "Completed",
            (),
            {"returncode": 1, "stdout": "", "stderr": "failure line one\nfailure 100%\n"},
        )()
        with (
            patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}),
            patch("scripts.cockpit_quality_gate.subprocess.run", return_value=completed),
            patch("builtins.print") as printer,
            self.assertRaises(SystemExit),
        ):
            run_checked("unit tests", ["python", "-m", "unittest"])

        rendered = "\n".join(str(call.args[0]) for call in printer.call_args_list if call.args)
        self.assertIn("::error title=unit tests failed::", rendered)
        self.assertIn("failure 100%25%0A", rendered)


if __name__ == "__main__":
    unittest.main()
