from __future__ import annotations

import json
import io
import tempfile
import unittest
from datetime import date
from pathlib import Path

from app.family_calendar_delivery import DeliveryState
from app.family_calendar_delivery_automatic import (
    run_family_calendar_automatic_delivery,
)
from app.family_calendar_delivery_config import DELIVERY_CONFIG_SCHEMA_VERSION
from app.family_calendar_delivery_store import (
    begin_stored_delivery,
    load_delivery_records,
)
from app.family_calendar_smtp_adapter import SMTPClientResult
from scripts.family_calendar_delivery_run import main as scheduled_main


TODAY = date(2026, 12, 17)
PRIVATE_NAME = "Synthetic Private Name"
PRIVATE_SECRET = "synthetic-app-password"
RECIPIENT_IDS = ("recipient-1", "recipient-2", "recipient-3", "recipient-4")
ADDRESSES = (
    "one@example.invalid",
    "two@example.invalid",
    "three@example.invalid",
    "four@example.invalid",
)


class FakeSMTPClient:
    def __init__(self, result: SMTPClientResult):
        self.result = result
        self.calls = 0

    def send_message(self, _message, *, from_addr, to_addrs):
        self.calls += 1
        return self.result


class FamilyCalendarAutomaticDeliveryTests(unittest.TestCase):
    def test_scheduled_dispatch_selects_enabled_branch_without_touching_dry_run(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _private_paths(Path(temp_dir))
            _write_config(paths[1], mode="enabled")
            output = io.StringIO()
            calls = {"dry_run": 0, "enabled": 0}

            def dry_run_main(_argv, *, output):
                calls["dry_run"] += 1
                raise AssertionError("enabled dispatch must not call dry-run")

            def enabled_main(argv, *, output):
                calls["enabled"] += 1
                self.assertIn(str(paths[1]), argv)
                output.write('{"status": "synthetic-enabled"}\n')
                return 7

            exit_code = scheduled_main(
                ["--config-path", str(paths[1])],
                output=output,
                dry_run_main=dry_run_main,
                enabled_main=enabled_main,
            )

        self.assertEqual(exit_code, 7)
        self.assertEqual(calls, {"dry_run": 0, "enabled": 1})
        self.assertEqual(
            json.loads(output.getvalue()),
            {"status": "synthetic-enabled"},
        )

    def test_enabled_run_reads_keychain_and_persists_smtp_acceptance(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _private_paths(Path(temp_dir))
            _write_people(paths[0])
            _write_config(paths[1], mode="enabled")
            credential_calls = 0
            client = FakeSMTPClient(SMTPClientResult())

            def credential_reader():
                nonlocal credential_calls
                credential_calls += 1
                return PRIVATE_SECRET

            def client_factory(username, password):
                self.assertEqual(username, "sender@example.invalid")
                self.assertEqual(password, PRIVATE_SECRET)
                return client

            result = run_family_calendar_automatic_delivery(
                today=TODAY,
                people_path=paths[0],
                config_path=paths[1],
                state_path=paths[2],
                worker_path=paths[3],
                credential_reader=credential_reader,
                smtp_client_factory=client_factory,
            )
            records = load_delivery_records(paths[2])

        self.assertEqual(result.status, "enabled")
        self.assertEqual(result.candidate_count, 2)
        self.assertEqual(result.d2_count, 1)
        self.assertEqual(result.d1_count, 1)
        self.assertEqual(result.accepted_count, 2)
        self.assertEqual(result.attempted_count, 2)
        self.assertTrue(result.coordinator_called)
        self.assertTrue(result.keychain_read)
        self.assertTrue(result.transport_called)
        self.assertEqual(credential_calls, 1)
        self.assertEqual(client.calls, 2)
        self.assertEqual(len(records), 2)
        self.assertTrue(
            all(record.state is DeliveryState.SMTP_ACCEPTED for record in records)
        )
        _assert_redacted(self, result)

    def test_second_enabled_run_is_idempotent_and_does_not_send_again(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _private_paths(Path(temp_dir))
            _write_people(paths[0])
            _write_config(paths[1], mode="enabled")
            client = FakeSMTPClient(SMTPClientResult())
            kwargs = {
                "today": TODAY,
                "people_path": paths[0],
                "config_path": paths[1],
                "state_path": paths[2],
                "worker_path": paths[3],
                "credential_reader": lambda: PRIVATE_SECRET,
                "smtp_client_factory": lambda _username, _password: client,
            }

            first = run_family_calendar_automatic_delivery(**kwargs)
            second = run_family_calendar_automatic_delivery(**kwargs)
            records = load_delivery_records(paths[2])

        self.assertEqual(first.accepted_count, 2)
        self.assertEqual(second.status, "enabled")
        self.assertEqual(second.skipped_count, 2)
        self.assertEqual(second.attempted_count, 0)
        self.assertFalse(second.transport_called)
        self.assertEqual(client.calls, 2)
        self.assertEqual(len(records), 2)

    def test_interrupted_state_recovers_unknown_and_blocks_transport(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _private_paths(Path(temp_dir))
            _write_people(paths[0])
            _write_config(paths[1], mode="enabled")
            begin_stored_delivery(
                event_key="synthetic-other:birthday:2026-12-19",
                offset="D-2",
                recipient_ids=RECIPIENT_IDS,
                path=paths[2],
            )
            client = FakeSMTPClient(SMTPClientResult())

            result = run_family_calendar_automatic_delivery(
                today=TODAY,
                people_path=paths[0],
                config_path=paths[1],
                state_path=paths[2],
                worker_path=paths[3],
                credential_reader=lambda: PRIVATE_SECRET,
                smtp_client_factory=lambda _username, _password: client,
            )
            records = load_delivery_records(paths[2])

        self.assertEqual(result.status, "recovery_required")
        self.assertEqual(result.recovery_required_count, 1)
        self.assertEqual(result.attempted_count, 0)
        self.assertFalse(result.transport_called)
        self.assertEqual(client.calls, 0)
        self.assertEqual(records[0].state, DeliveryState.DELIVERY_UNKNOWN)

    def test_partial_delivery_stops_remaining_candidates_for_manual_review(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _private_paths(Path(temp_dir))
            _write_people(paths[0])
            _write_config(paths[1], mode="enabled")
            client = FakeSMTPClient(
                SMTPClientResult(refused_addresses=(ADDRESSES[0],))
            )

            result = run_family_calendar_automatic_delivery(
                today=TODAY,
                people_path=paths[0],
                config_path=paths[1],
                state_path=paths[2],
                worker_path=paths[3],
                credential_reader=lambda: PRIVATE_SECRET,
                smtp_client_factory=lambda _username, _password: client,
            )
            records = load_delivery_records(paths[2])

        self.assertEqual(result.status, "manual_review_required")
        self.assertEqual(result.partial_count, 1)
        self.assertEqual(result.attempted_count, 1)
        self.assertEqual(client.calls, 1)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].state, DeliveryState.PARTIAL)

    def test_dry_run_or_missing_candidate_never_reads_keychain_or_runtime(self) -> None:
        for case in ("dry_run", "no_candidate"):
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    paths = _private_paths(Path(temp_dir))
                    _write_people(
                        paths[0],
                        birth_date="" if case == "no_candidate" else "1980-12-19",
                        name_day="01-15" if case == "no_candidate" else "12-18",
                    )
                    _write_config(
                        paths[1],
                        mode="dry_run" if case == "dry_run" else "enabled",
                    )
                    credential_calls = 0

                    def credential_reader():
                        nonlocal credential_calls
                        credential_calls += 1
                        raise AssertionError("Keychain must not be read")

                    result = run_family_calendar_automatic_delivery(
                        today=TODAY,
                        people_path=paths[0],
                        config_path=paths[1],
                        state_path=paths[2],
                        worker_path=paths[3],
                        credential_reader=credential_reader,
                        smtp_client_factory=lambda _username, _password: object(),
                    )

                    self.assertEqual(
                        result.status,
                        "not_enabled" if case == "dry_run" else "enabled",
                    )
                    self.assertFalse(result.keychain_read)
                    self.assertFalse(result.coordinator_called)
                    self.assertFalse(result.transport_called)
                    self.assertEqual(credential_calls, 0)
                    self.assertFalse(paths[2].exists())
                    self.assertFalse(paths[3].exists())

    def test_keychain_failure_does_not_create_delivery_state(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            paths = _private_paths(Path(temp_dir))
            _write_people(paths[0])
            _write_config(paths[1], mode="enabled")

            def credential_reader():
                raise RuntimeError(f"failed {PRIVATE_SECRET}")

            result = run_family_calendar_automatic_delivery(
                today=TODAY,
                people_path=paths[0],
                config_path=paths[1],
                state_path=paths[2],
                worker_path=paths[3],
                credential_reader=credential_reader,
            )

        self.assertEqual(result.status, "credential_error")
        self.assertTrue(result.keychain_read)
        self.assertFalse(result.coordinator_called)
        self.assertFalse(result.transport_called)
        self.assertFalse(paths[2].exists())
        _assert_redacted(self, result)


def _private_paths(root: Path) -> tuple[Path, Path, Path, Path]:
    private_dir = root / "family"
    return (
        private_dir / "people.json",
        private_dir / "notification_config.json",
        private_dir / "delivery_state.json",
        private_dir / "delivery_worker",
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
                        "id": "person-syntheticaaaa",
                        "display_name": PRIVATE_NAME,
                        "relation": "synthetic relation",
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
                "schema_version": DELIVERY_CONFIG_SCHEMA_VERSION,
                "mode": mode,
                "smtp_provider": "icloud",
                "sender_address": "sender@example.invalid",
                "recipients": [
                    {"recipient_id": recipient_id, "address": address}
                    for recipient_id, address in zip(
                        RECIPIENT_IDS,
                        ADDRESSES,
                        strict=True,
                    )
                ],
            }
        ),
    )


def _write_private_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.parent.chmod(0o700)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o600)


def _assert_redacted(
    test_case: unittest.TestCase,
    result,
) -> None:
    visible = f"{result!r} {json.dumps(result.safe_document(), sort_keys=True)}"
    for private_value in (PRIVATE_NAME, PRIVATE_SECRET, *ADDRESSES):
        test_case.assertNotIn(private_value, visible)
    test_case.assertNotIn("@", visible)


if __name__ == "__main__":
    unittest.main()
