from __future__ import annotations

import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import Mock

from scripts.cockpit_fast_feedback import (
    DOMAIN_SUITES,
    PROJECT_ROOT,
    RELEASE_GATE_COMMAND,
    FastFeedbackError,
    format_suite_catalog,
    main,
    resolve_test_targets,
    run_fast_feedback,
    unittest_command,
)


class CockpitFastFeedbackTests(unittest.TestCase):
    def test_domain_catalog_is_small_explicit_and_unique(self) -> None:
        self.assertEqual(
            tuple(DOMAIN_SUITES),
            ("email-archive", "frontend", "http-security"),
        )
        for suite_id, suite in DOMAIN_SUITES.items():
            with self.subTest(suite_id=suite_id):
                self.assertTrue(suite.description)
                self.assertTrue(suite.test_targets)
                self.assertEqual(
                    len(suite.test_targets),
                    len(set(suite.test_targets)),
                )

    def test_resolve_test_targets_preserves_order_and_removes_overlap(self) -> None:
        targets = resolve_test_targets(("frontend", "email-archive", "frontend"))

        self.assertEqual(targets[0], "tests.test_cockpit_frontend")
        self.assertIn("tests.test_email_archive_browser", targets)
        self.assertEqual(len(targets), len(set(targets)))

    def test_resolve_test_targets_rejects_missing_or_unknown_domain(self) -> None:
        with self.assertRaises(FastFeedbackError):
            resolve_test_targets(())
        with self.assertRaises(FastFeedbackError):
            resolve_test_targets(("all",))

    def test_unittest_command_uses_current_interpreter(self) -> None:
        command = unittest_command(("tests.test_example",), verbose=True)

        self.assertEqual(
            command,
            (sys.executable, "-m", "unittest", "-v", "tests.test_example"),
        )

    def test_runner_executes_only_resolved_targets(self) -> None:
        runner = Mock(return_value=subprocess.CompletedProcess([], 0))

        result = run_fast_feedback(("http-security",), runner=runner)

        self.assertEqual(result, 0)
        command = runner.call_args.args[0]
        self.assertEqual(
            command,
            [
                sys.executable,
                "-m",
                "unittest",
                "tests.test_cockpit_http_security",
            ],
        )
        self.assertEqual(runner.call_args.kwargs["cwd"], str(PROJECT_ROOT))
        self.assertFalse(runner.call_args.kwargs["check"])

    def test_runner_preserves_failure_and_fails_closed_on_timeout(self) -> None:
        failed_runner = Mock(return_value=subprocess.CompletedProcess([], 7))
        self.assertEqual(
            run_fast_feedback(("frontend",), runner=failed_runner),
            7,
        )

        timeout_runner = Mock(
            side_effect=subprocess.TimeoutExpired(cmd=["unittest"], timeout=120)
        )
        with redirect_stderr(StringIO()):
            self.assertEqual(
                run_fast_feedback(("frontend",), runner=timeout_runner),
                124,
            )

    def test_list_mode_does_not_run_tests(self) -> None:
        runner = Mock()
        output = StringIO()

        with redirect_stdout(output):
            result = main(("--list",), runner=runner)

        self.assertEqual(result, 0)
        runner.assert_not_called()
        self.assertEqual(output.getvalue().strip(), format_suite_catalog())

    def test_missing_domain_is_rejected_before_runner(self) -> None:
        runner = Mock()
        with redirect_stderr(StringIO()):
            with self.assertRaisesRegex(SystemExit, "2"):
                main((), runner=runner)
        runner.assert_not_called()

    def test_success_output_keeps_release_gate_boundary_visible(self) -> None:
        runner = Mock(return_value=subprocess.CompletedProcess([], 0))
        output = StringIO()

        with redirect_stdout(output):
            result = main(("frontend",), runner=runner)

        self.assertEqual(result, 0)
        self.assertIn("D3 fast feedback: OK", output.getvalue())
        self.assertIn(RELEASE_GATE_COMMAND, output.getvalue())


if __name__ == "__main__":
    unittest.main()
