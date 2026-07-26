from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from app.family_calendar_delivery_keychain import (
    FamilyCalendarKeychainError,
    read_family_calendar_app_password,
)
from app.family_calendar_delivery_readiness import (
    FAMILY_CALENDAR_KEYCHAIN_ACCOUNT,
    FAMILY_CALENDAR_KEYCHAIN_SERVICE,
)


PRIVATE_SECRET = "synthetic-app-password"


class FamilyCalendarDeliveryKeychainTests(unittest.TestCase):
    def test_reads_fixed_keychain_identity_without_secret_in_arguments(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            executable = _executable(Path(temp_dir))
            calls = []

            def runner(argv):
                calls.append(tuple(argv))
                return 0, f"{PRIVATE_SECRET}\n"

            secret = read_family_calendar_app_password(
                command_runner=runner,
                executable_locator=lambda _name: str(executable),
            )

        self.assertEqual(secret, PRIVATE_SECRET)
        self.assertEqual(len(calls), 1)
        self.assertIn("find-generic-password", calls[0])
        self.assertIn("-w", calls[0])
        self.assertIn(FAMILY_CALENDAR_KEYCHAIN_SERVICE, calls[0])
        self.assertIn(FAMILY_CALENDAR_KEYCHAIN_ACCOUNT, calls[0])
        self.assertNotIn(PRIVATE_SECRET, calls[0])

    def test_missing_failed_or_malformed_keychain_result_is_redacted(self) -> None:
        cases = (
            ("missing", None, None),
            ("failed", (44, f"{PRIVATE_SECRET}\n"), True),
            ("empty", (0, ""), True),
            ("multiline", (0, f"{PRIVATE_SECRET}\nsecond-line"), True),
            ("invalid_result", "private-invalid-result", True),
        )
        for case, runner_result, executable_present in cases:
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    executable = _executable(Path(temp_dir))

                    def runner(_argv):
                        return runner_result

                    with self.assertRaises(FamilyCalendarKeychainError) as raised:
                        read_family_calendar_app_password(
                            command_runner=runner,
                            executable_locator=(
                                (lambda _name: str(executable))
                                if executable_present
                                else (lambda _name: None)
                            ),
                        )

                visible = f"{raised.exception!r} {raised.exception}"
                self.assertNotIn(PRIVATE_SECRET, visible)
                self.assertNotIn("second-line", visible)
                self.assertIsNone(raised.exception.__cause__)
                self.assertIsNone(raised.exception.__context__)

    def test_runner_exception_does_not_survive_as_secret_context(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            executable = _executable(Path(temp_dir))

            def runner(_argv):
                raise RuntimeError(f"private failure {PRIVATE_SECRET}")

            with self.assertRaises(FamilyCalendarKeychainError) as raised:
                read_family_calendar_app_password(
                    command_runner=runner,
                    executable_locator=lambda _name: str(executable),
                )

        self.assertIsNone(raised.exception.__cause__)
        self.assertIsNone(raised.exception.__context__)
        self.assertNotIn(PRIVATE_SECRET, str(raised.exception))

    def test_rejects_non_executable_security_path_without_running_command(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "security"
            path.write_text("#!/bin/sh\n", encoding="utf-8")
            path.chmod(0o600)
            called = False

            def runner(_argv):
                nonlocal called
                called = True
                return 0, PRIVATE_SECRET

            with self.assertRaisesRegex(FamilyCalendarKeychainError, "unsafe"):
                read_family_calendar_app_password(
                    command_runner=runner,
                    executable_locator=lambda _name: str(path),
                )

        self.assertFalse(called)


def _executable(root: Path) -> Path:
    path = root / "security"
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o700)
    os.utime(path, None)
    return path


if __name__ == "__main__":
    unittest.main()
