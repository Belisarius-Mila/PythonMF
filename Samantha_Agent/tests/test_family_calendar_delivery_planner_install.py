from __future__ import annotations

import io
import json
import plistlib
import stat
import tempfile
import unittest
from pathlib import Path

from app.family_calendar_delivery_planner_install import (
    FAMILY_CALENDAR_PLANNER_INSTALL_CONFIRMATION,
    FamilyCalendarPlannerInstallError,
    apply_family_calendar_planner_install,
    plan_family_calendar_planner_install,
)
from app.family_calendar_delivery_readiness import FAMILY_CALENDAR_PLANNER_LABEL
from scripts.family_calendar_delivery_planner_install import main


ADDRESSES = (
    "one@example.invalid",
    "two@example.invalid",
    "three@example.invalid",
    "four@example.invalid",
)


class FamilyCalendarPlannerInstallTests(unittest.TestCase):
    def test_plan_is_exact_read_only_and_requires_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _install_paths(Path(temp_dir))
            _prepare_inputs(paths)
            entries_before = tuple(paths["target"].parent.iterdir())

            plan = plan_family_calendar_planner_install(**_plan_kwargs(paths))
            document = plan.safe_document()

            self.assertEqual(document["status"], "preview")
            self.assertEqual(document["target_path"], str(paths["target"]))
            self.assertEqual(document["file_mode"], "0600")
            self.assertTrue(document["create_only"])
            self.assertEqual(document["config_mode"], "dry_run")
            self.assertTrue(document["confirmation_required"])
            self.assertEqual(
                document["required_confirmation"],
                FAMILY_CALENDAR_PLANNER_INSTALL_CONFIRMATION,
            )
            self.assertEqual(document["plan_fingerprint"], plan.fingerprint)
            self.assertEqual(len(plan.fingerprint), 64)
            self.assertEqual(
                document["configuration"]["ProgramArguments"],
                [str(paths["python"]), str(paths["runner"])],
            )
            self.assertEqual(
                document["configuration"]["StartCalendarInterval"],
                {"Hour": 8, "Minute": 0},
            )
            self.assertFalse(document["writes_performed"])
            self.assertFalse(document["install_called"])
            self.assertFalse(document["launchctl_called"])
            self.assertFalse(document["secret_read"])
            self.assertFalse(document["transport_called"])
            self.assertFalse(paths["target"].exists())
            self.assertEqual(tuple(paths["target"].parent.iterdir()), entries_before)
            _assert_redacted(self, repr(plan))

    def test_wrong_confirmation_or_fingerprint_creates_nothing(self) -> None:
        for case in ("confirmation", "fingerprint"):
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    paths = _install_paths(Path(temp_dir))
                    _prepare_inputs(paths)
                    plan = plan_family_calendar_planner_install(
                        **_plan_kwargs(paths)
                    )

                    with self.assertRaises(FamilyCalendarPlannerInstallError):
                        apply_family_calendar_planner_install(
                            plan,
                            confirmation=(
                                "yes"
                                if case == "confirmation"
                                else FAMILY_CALENDAR_PLANNER_INSTALL_CONFIRMATION
                            ),
                            expected_fingerprint=(
                                plan.fingerprint
                                if case == "confirmation"
                                else "0" * 64
                            ),
                        )

                    self.assertFalse(paths["target"].exists())
                    self.assertEqual(
                        list(paths["target"].parent.glob(".*.tmp")),
                        [],
                    )

    def test_changed_runner_after_preview_is_not_installed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _install_paths(Path(temp_dir))
            _prepare_inputs(paths)
            plan = plan_family_calendar_planner_install(**_plan_kwargs(paths))
            paths["runner"].write_text("# changed runner\n", encoding="utf-8")
            paths["runner"].chmod(0o600)

            with self.assertRaisesRegex(
                FamilyCalendarPlannerInstallError,
                "changed",
            ):
                apply_family_calendar_planner_install(
                    plan,
                    confirmation=FAMILY_CALENDAR_PLANNER_INSTALL_CONFIRMATION,
                    expected_fingerprint=plan.fingerprint,
                )

            self.assertFalse(paths["target"].exists())

    def test_exact_confirmation_atomically_creates_mode_0600_plist(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _install_paths(Path(temp_dir))
            _prepare_inputs(paths)
            plan = plan_family_calendar_planner_install(**_plan_kwargs(paths))

            result = apply_family_calendar_planner_install(
                plan,
                confirmation=FAMILY_CALENDAR_PLANNER_INSTALL_CONFIRMATION,
                expected_fingerprint=plan.fingerprint,
            )

            payload = paths["target"].read_bytes()
            self.assertEqual(result.safe_document()["status"], "installed")
            self.assertEqual(payload, plan.plist_text.encode("utf-8"))
            self.assertEqual(plistlib.loads(payload), plan.configuration)
            self.assertEqual(
                stat.S_IMODE(paths["target"].stat().st_mode),
                0o600,
            )
            self.assertFalse(paths["target"].is_symlink())
            self.assertEqual(
                list(paths["target"].parent.glob(f".{paths['target'].name}.*.tmp")),
                [],
            )
            self.assertTrue(result.safe_document()["writes_performed"])
            self.assertFalse(result.safe_document()["launchctl_called"])
            self.assertFalse(result.safe_document()["secret_read"])
            self.assertFalse(result.safe_document()["transport_called"])
            _assert_redacted(self, repr(result))

    def test_non_dry_run_existing_or_linked_target_fails_closed(self) -> None:
        for case in ("disabled", "existing", "linked"):
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    paths = _install_paths(Path(temp_dir))
                    _prepare_inputs(
                        paths,
                        mode="disabled" if case == "disabled" else "dry_run",
                    )
                    original = None
                    if case == "existing":
                        original = b"existing planner\n"
                        paths["target"].write_bytes(original)
                        paths["target"].chmod(0o600)
                    elif case == "linked":
                        source = Path(temp_dir) / "existing.plist"
                        source.write_bytes(b"linked planner\n")
                        paths["target"].symlink_to(source)

                    with self.assertRaises(FamilyCalendarPlannerInstallError):
                        plan_family_calendar_planner_install(
                            **_plan_kwargs(paths)
                        )

                    if original is not None:
                        self.assertEqual(paths["target"].read_bytes(), original)
                    if case == "linked":
                        self.assertTrue(paths["target"].is_symlink())

    def test_cli_previews_then_applies_only_matching_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _install_paths(Path(temp_dir))
            _prepare_inputs(paths)
            arguments = _cli_arguments(paths)
            preview_output = io.StringIO()

            preview_exit = main(arguments, output=preview_output)
            preview = json.loads(preview_output.getvalue())

            self.assertEqual(preview_exit, 0)
            self.assertEqual(preview["status"], "preview")
            self.assertFalse(paths["target"].exists())

            failed_output = io.StringIO()
            failed_exit = main(
                [
                    *arguments,
                    "--apply",
                    "--confirmation",
                    FAMILY_CALENDAR_PLANNER_INSTALL_CONFIRMATION,
                    "--expected-fingerprint",
                    "0" * 64,
                ],
                output=failed_output,
            )

            self.assertEqual(failed_exit, 1)
            self.assertFalse(paths["target"].exists())
            self.assertFalse(
                json.loads(failed_output.getvalue())["writes_performed"]
            )

            applied_output = io.StringIO()
            applied_exit = main(
                [
                    *arguments,
                    "--apply",
                    "--confirmation",
                    FAMILY_CALENDAR_PLANNER_INSTALL_CONFIRMATION,
                    "--expected-fingerprint",
                    preview["plan_fingerprint"],
                ],
                output=applied_output,
            )
            applied = json.loads(applied_output.getvalue())

            self.assertEqual(applied_exit, 0)
            self.assertEqual(applied["status"], "installed")
            self.assertTrue(applied["writes_performed"])
            self.assertFalse(applied["launchctl_called"])
            self.assertFalse(applied["secret_read"])
            self.assertFalse(applied["transport_called"])
            self.assertEqual(
                stat.S_IMODE(paths["target"].stat().st_mode),
                0o600,
            )


def _install_paths(root: Path) -> dict[str, Path]:
    return {
        "config": root / "private" / "notification_config.json",
        "python": root / "venv" / "bin" / "python",
        "runner": root / "project" / "family_calendar_delivery_run.py",
        "target": (
            root
            / "Library"
            / "LaunchAgents"
            / f"{FAMILY_CALENDAR_PLANNER_LABEL}.plist"
        ),
    }


def _prepare_inputs(paths: dict[str, Path], *, mode: str = "dry_run") -> None:
    paths["config"].parent.mkdir(parents=True, mode=0o700)
    paths["config"].parent.chmod(0o700)
    paths["config"].write_text(
        json.dumps(
            {
                "schema_version": 2,
                "mode": mode,
                "smtp_provider": "icloud",
                "sender_address": "sender@example.invalid",
                "recipients": [
                    {
                        "recipient_id": f"recipient-{index}",
                        "address": address,
                    }
                    for index, address in enumerate(ADDRESSES, start=1)
                ],
            }
        ),
        encoding="utf-8",
    )
    paths["config"].chmod(0o600)
    paths["python"].parent.mkdir(parents=True, mode=0o700)
    paths["python"].write_text("#!/bin/sh\n", encoding="utf-8")
    paths["python"].chmod(0o700)
    paths["runner"].parent.mkdir(parents=True, mode=0o700)
    paths["runner"].write_text("# safe runner\n", encoding="utf-8")
    paths["runner"].chmod(0o600)
    paths["target"].parent.mkdir(parents=True, mode=0o700)
    paths["target"].parent.chmod(0o700)


def _plan_kwargs(paths: dict[str, Path]) -> dict[str, object]:
    return {
        "target_path": paths["target"],
        "config_path": paths["config"],
        "python_path": paths["python"],
        "runner_path": paths["runner"],
        "hour": 8,
        "minute": 0,
    }


def _cli_arguments(paths: dict[str, Path]) -> list[str]:
    return [
        "--target-path",
        str(paths["target"]),
        "--config-path",
        str(paths["config"]),
        "--python-path",
        str(paths["python"]),
        "--runner-path",
        str(paths["runner"]),
        "--hour",
        "8",
        "--minute",
        "0",
    ]


def _assert_redacted(test_case: unittest.TestCase, visible: str) -> None:
    test_case.assertNotIn("@", visible)
    for value in ADDRESSES:
        test_case.assertNotIn(value, visible)


if __name__ == "__main__":
    unittest.main()
