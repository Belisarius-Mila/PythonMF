from __future__ import annotations

import re
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
    node_binary,
    source_metrics,
    run_checked,
)


class CockpitQualityGateTests(unittest.TestCase):
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
        self.assertIn("tests.test_adam_voice_mode", TEST_MODULES)
        self.assertIn("tests.test_human_adam_profiles", TEST_MODULES)
        self.assertIn("tests.test_cockpit_quality_gate", TEST_MODULES)
        self.assertIn("tests.test_command_cheatsheet", TEST_MODULES)
        self.assertIn("app/communication/human_adam_profiles.py", COMPILE_PATHS)
        self.assertIn("app/command_cheatsheet.py", COMPILE_PATHS)
        self.assertIn("app/development_branch_lifecycle.py", COMPILE_PATHS)
        self.assertIn("scripts/development_branch_audit.py", COMPILE_PATHS)
        self.assertIn("tests.test_development_branch_lifecycle", TEST_MODULES)
        self.assertIn("tests.test_project_continuity", TEST_MODULES)
        self.assertIn("app/project_continuity.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_config.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_coordinator.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_message.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_runner.py", COMPILE_PATHS)
        self.assertIn("app/family_calendar_delivery_store.py", COMPILE_PATHS)
        self.assertIn("tests.test_family_calendar_delivery", TEST_MODULES)
        self.assertIn("tests.test_family_calendar_delivery_config", TEST_MODULES)
        self.assertIn("tests.test_family_calendar_delivery_coordinator", TEST_MODULES)
        self.assertIn("tests.test_family_calendar_delivery_message", TEST_MODULES)
        self.assertIn("tests.test_family_calendar_delivery_runner", TEST_MODULES)
        self.assertIn("tests.test_family_calendar_delivery_store", TEST_MODULES)

    def test_architecture_baselines_are_informational_and_reported(self) -> None:
        messages = architecture_messages()

        self.assertEqual(len(ARCHITECTURE_BASELINES), 2)
        self.assertTrue(any("app/cockpit.py" in message for message in messages))
        self.assertTrue(any("app/speech/adam_voice_mode.py" in message for message in messages))

    def test_orphaned_human_adam_deploy_module_is_absent(self) -> None:
        legacy_source = "app/communication/human_adam_deploy.py"
        legacy_test = "tests.test_human_adam_deploy"

        self.assertNotIn(legacy_source, COMPILE_PATHS)
        self.assertNotIn(legacy_test, TEST_MODULES)
        self.assertFalse((PROJECT_ROOT / legacy_source).exists())
        self.assertFalse((PROJECT_ROOT / "tests/test_human_adam_deploy.py").exists())

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
