from __future__ import annotations

import io
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from app.family_calendar_delivery_dry_run import (
    run_family_calendar_operational_dry_run,
)
from app.family_calendar_delivery_runner import FamilyCalendarDeliveryRunResult
from scripts.family_calendar_delivery_dry_run import main


TODAY = date(2026, 12, 17)
PRIVATE_NAME = "Private Alena"
PRIVATE_EVENT_KEY_FRAGMENT = "person-privateaaaa"
PRIVATE_ADDRESSES = (
    "one@example.invalid",
    "two@example.invalid",
    "three@example.invalid",
    "four@example.invalid",
)


class FamilyCalendarDeliveryOperationalDryRunTests(unittest.TestCase):
    def test_real_d2_d1_candidates_are_aggregated_without_runtime_io(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _private_paths(Path(temp_dir))
            _write_people(paths[0])
            _write_config(paths[1], mode="dry_run")

            result = run_family_calendar_operational_dry_run(
                today=TODAY,
                people_path=paths[0],
                config_path=paths[1],
                state_path=paths[2],
                worker_path=paths[3],
            )

            self.assertEqual(
                result.safe_document(),
                {
                    "status": "dry_run",
                    "candidate_count": 2,
                    "d2_count": 1,
                    "d1_count": 1,
                    "eligible_count": 2,
                    "recipient_count": 4,
                    "coordinator_called": False,
                    "transport_called": False,
                },
            )
            _assert_runtime_absent(self, paths)
            _assert_redacted(self, f"{result!r} {json.dumps(result.safe_document())}", paths)

    def test_day_without_candidates_still_validates_real_dry_run_config(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _private_paths(Path(temp_dir))
            _write_people(paths[0], birth_date="", name_day="01-15")
            _write_config(paths[1], mode="dry_run")

            result = run_family_calendar_operational_dry_run(
                today=TODAY,
                people_path=paths[0],
                config_path=paths[1],
                state_path=paths[2],
                worker_path=paths[3],
            )

            self.assertEqual(result.status, "dry_run")
            self.assertEqual(result.candidate_count, 0)
            self.assertEqual(result.recipient_count, 4)
            self.assertFalse(result.coordinator_called)
            self.assertFalse(result.transport_called)
            _assert_runtime_absent(self, paths)

    def test_disabled_or_invalid_config_fails_before_private_calendar_access(self) -> None:
        for case in ("disabled", "invalid"):
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    paths = _private_paths(Path(temp_dir))
                    if case == "disabled":
                        _write_config(paths[1], mode="disabled")
                    else:
                        _write_private_text(paths[1], "private@example.invalid {invalid")

                    result = run_family_calendar_operational_dry_run(
                        today=TODAY,
                        people_path=paths[0],
                        config_path=paths[1],
                        state_path=paths[2],
                        worker_path=paths[3],
                    )

                    self.assertEqual(
                        result.status,
                        "not_dry_run" if case == "disabled" else "config_error",
                    )
                    self.assertEqual(result.candidate_count, 0)
                    self.assertFalse(paths[0].exists())
                    _assert_runtime_absent(self, paths)
                    _assert_redacted(self, repr(result), paths)

    def test_missing_insecure_corrupt_or_linked_calendar_fails_redacted(self) -> None:
        cases = ("missing", "insecure", "corrupt", "symlink")
        for case in cases:
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    root = Path(temp_dir)
                    paths = _private_paths(root)
                    _write_config(paths[1], mode="dry_run")
                    if case == "insecure":
                        _write_people(paths[0])
                        paths[0].chmod(0o644)
                    elif case == "corrupt":
                        _write_private_text(paths[0], f"{PRIVATE_NAME} {{invalid")
                    elif case == "symlink":
                        source = root / "private-source.json"
                        _write_people(source)
                        paths[0].symlink_to(source)

                    result = run_family_calendar_operational_dry_run(
                        today=TODAY,
                        people_path=paths[0],
                        config_path=paths[1],
                        state_path=paths[2],
                        worker_path=paths[3],
                    )

                    self.assertEqual(result.status, "calendar_error")
                    self.assertEqual(result.recipient_count, 4)
                    _assert_runtime_absent(self, paths)
                    _assert_redacted(self, repr(result), paths)

    def test_forbidden_transport_or_coordinator_call_is_visible_only_as_safety_error(self) -> None:
        for case in ("transport", "coordinator"):
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    paths = _private_paths(Path(temp_dir))
                    _write_people(paths[0])
                    _write_config(paths[1], mode="dry_run")

                    def unsafe_runner(**kwargs):
                        if case == "transport":
                            kwargs["transport"](None)
                        kwargs["coordinator"]()

                    result = run_family_calendar_operational_dry_run(
                        today=TODAY,
                        people_path=paths[0],
                        config_path=paths[1],
                        state_path=paths[2],
                        worker_path=paths[3],
                        configured_runner=unsafe_runner,
                    )

                    self.assertEqual(result.status, "safety_error")
                    self.assertEqual(result.transport_called, case == "transport")
                    self.assertEqual(result.coordinator_called, case == "coordinator")
                    _assert_runtime_absent(self, paths)
                    _assert_redacted(self, repr(result), paths)

    def test_runner_reported_runtime_effect_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _private_paths(Path(temp_dir))
            _write_people(paths[0])
            _write_config(paths[1], mode="dry_run")

            def unsafe_result_runner(**_kwargs):
                return FamilyCalendarDeliveryRunResult(
                    status="dry_run",
                    recipient_count=4,
                    attempt_eligible=True,
                    coordinator_called=False,
                    transport_called=True,
                )

            result = run_family_calendar_operational_dry_run(
                today=TODAY,
                people_path=paths[0],
                config_path=paths[1],
                state_path=paths[2],
                worker_path=paths[3],
                configured_runner=unsafe_result_runner,
            )

            self.assertEqual(result.status, "safety_error")
            self.assertTrue(result.transport_called)
            _assert_runtime_absent(self, paths)

    def test_cli_emits_only_redacted_aggregate_and_never_writes_runtime(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _private_paths(Path(temp_dir))
            _write_people(paths[0])
            _write_config(paths[1], mode="dry_run")
            output = io.StringIO()

            exit_code = main(
                [
                    "--today",
                    TODAY.isoformat(),
                    "--people-path",
                    str(paths[0]),
                    "--config-path",
                    str(paths[1]),
                    "--state-path",
                    str(paths[2]),
                    "--worker-path",
                    str(paths[3]),
                ],
                output=output,
            )

            document = json.loads(output.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(document["status"], "dry_run")
            self.assertEqual(document["candidate_count"], 2)
            self.assertFalse(document["coordinator_called"])
            self.assertFalse(document["transport_called"])
            _assert_runtime_absent(self, paths)
            _assert_redacted(self, output.getvalue(), paths)

    def test_cli_invalid_date_is_redacted_and_read_only(self) -> None:
        output = io.StringIO()

        exit_code = main(["--today", "private-invalid-date"], output=output)

        self.assertEqual(exit_code, 1)
        self.assertEqual(
            json.loads(output.getvalue()),
            {"redacted": True, "status": "input_error"},
        )


def _private_paths(root: Path) -> tuple[Path, Path, Path, Path]:
    private_dir = root / "family"
    return (
        private_dir / "people.json",
        private_dir / "notification_config.json",
        root / "runtime" / "delivery_state.json",
        root / "runtime" / "delivery_worker",
    )


def _write_people(
    path: Path,
    *,
    birth_date: str = "1980-12-19",
    name_day: str = "12-18",
) -> None:
    _write_private_text(
        path,
        json.dumps(
            {
                "schema_version": 1,
                "people": [
                    {
                        "id": f"{PRIVATE_EVENT_KEY_FRAGMENT}aaaa",
                        "display_name": PRIVATE_NAME,
                        "relation": "private relation",
                        "birth_date": birth_date,
                        "name_day": name_day,
                        "reminders_enabled": True,
                        "active": True,
                        "created_at": "2026-01-01T08:00:00+00:00",
                        "updated_at": "2026-01-01T08:00:00+00:00",
                    }
                ],
            }
        ),
    )


def _write_config(path: Path, *, mode: str) -> None:
    _write_private_text(
        path,
        json.dumps(
            {
                "schema_version": 2,
                "mode": mode,
                "smtp_provider": "icloud",
                "sender_address": "sender@example.invalid",
                "recipients": [
                    {"recipient_id": f"recipient-{index}", "address": address}
                    for index, address in enumerate(PRIVATE_ADDRESSES, start=1)
                ],
            }
        ),
    )


def _write_private_text(path: Path, text: str) -> None:
    path.parent.mkdir(mode=0o700, exist_ok=True)
    path.parent.chmod(0o700)
    path.write_text(text, encoding="utf-8")
    path.chmod(0o600)


def _assert_runtime_absent(
    test_case: unittest.TestCase,
    paths: tuple[Path, Path, Path, Path],
) -> None:
    state_path, worker_path = paths[2], paths[3]
    test_case.assertFalse(state_path.exists())
    test_case.assertFalse(worker_path.exists())
    test_case.assertFalse(Path(f"{worker_path}.lock").exists())
    test_case.assertFalse(state_path.parent.exists())


def _assert_redacted(
    test_case: unittest.TestCase,
    visible: str,
    paths: tuple[Path, Path, Path, Path],
) -> None:
    test_case.assertNotIn("@", visible)
    for private_value in (
        PRIVATE_NAME,
        PRIVATE_EVENT_KEY_FRAGMENT,
        "private relation",
        *PRIVATE_ADDRESSES,
        *(str(path) for path in paths),
    ):
        test_case.assertNotIn(private_value, visible)


if __name__ == "__main__":
    unittest.main()
