from __future__ import annotations

import json
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.family_calendar_delivery import DeliveryState, NotificationOffset, RecipientDeliveryState
from app.family_calendar_delivery_store import (
    DELIVERY_STORE_SCHEMA_VERSION,
    DeliveryStoreError,
    begin_stored_delivery,
    complete_stored_delivery,
    load_delivery_records,
    recover_interrupted_deliveries,
)
from app.file_persistence import lock_path_for


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVENT_KEY = "person-example:birthday:2026-12-19"
RECIPIENT_IDS = ("recipient-1", "recipient-2", "recipient-3", "recipient-4")


class FamilyCalendarDeliveryStoreTests(unittest.TestCase):
    def test_begin_persists_sending_with_private_permissions(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _state_path(Path(temp_dir))

            result = _begin(path)
            records = load_delivery_records(path)
            stored = json.loads(path.read_text(encoding="utf-8"))

            self.assertTrue(result.started)
            self.assertIsNotNone(result.record)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].state, DeliveryState.SENDING)
            self.assertEqual(stored["schema_version"], DELIVERY_STORE_SCHEMA_VERSION)
            self.assertEqual(list(stored["records"]), [result.plan.operation_id])
            self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(lock_path_for(path).stat().st_mode), 0o600)

    def test_repeated_begin_is_idempotent_and_keeps_one_record(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _state_path(Path(temp_dir))

            first = _begin(path)
            second = _begin(path)
            records = load_delivery_records(path)

        self.assertTrue(first.started)
        self.assertFalse(second.started)
        self.assertEqual(second.plan.reason, "already_recorded")
        self.assertEqual(second.record, first.record)
        self.assertEqual(len(records), 1)

    def test_complete_requires_sending_and_persists_partial_result(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _state_path(Path(temp_dir))
            started = _begin(path)

            completed = complete_stored_delivery(
                operation_id=started.plan.operation_id,
                accepted_recipient_ids=RECIPIENT_IDS[:2],
                not_sent_recipient_ids=RECIPIENT_IDS[2:],
                path=path,
            )
            records = load_delivery_records(path)

            with self.assertRaisesRegex(DeliveryStoreError, "current state"):
                complete_stored_delivery(
                    operation_id=started.plan.operation_id,
                    accepted_recipient_ids=RECIPIENT_IDS,
                    path=path,
                )

        self.assertEqual(completed.state, DeliveryState.PARTIAL)
        self.assertEqual(records, (completed,))

    def test_failed_atomic_completion_keeps_original_sending_record(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _state_path(Path(temp_dir))
            started = _begin(path)

            with patch(
                "app.file_persistence._atomic_write_bytes_unlocked",
                side_effect=OSError("simulated replace failure"),
            ):
                with self.assertRaisesRegex(DeliveryStoreError, "failed safely"):
                    complete_stored_delivery(
                        operation_id=started.plan.operation_id,
                        accepted_recipient_ids=RECIPIENT_IDS,
                        path=path,
                    )

            records = load_delivery_records(path)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].state, DeliveryState.SENDING)

    def test_d1_is_replanned_from_atomically_stored_d2_result(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _state_path(Path(temp_dir))
            d2 = _begin(path)
            complete_stored_delivery(
                operation_id=d2.plan.operation_id,
                not_sent_recipient_ids=RECIPIENT_IDS,
                path=path,
            )

            d1 = _begin(path, offset=NotificationOffset.D1)
            records = load_delivery_records(path)

        self.assertTrue(d1.started)
        self.assertEqual(d1.plan.reason, "catch_up_d1_after_not_sent")
        self.assertEqual(len(records), 2)

    def test_d1_is_blocked_after_unknown_d2(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _state_path(Path(temp_dir))
            d2 = _begin(path)
            complete_stored_delivery(
                operation_id=d2.plan.operation_id,
                unknown_recipient_ids=RECIPIENT_IDS,
                path=path,
            )

            d1 = _begin(path, offset=NotificationOffset.D1)
            records = load_delivery_records(path)

        self.assertFalse(d1.started)
        self.assertIsNone(d1.record)
        self.assertEqual(d1.plan.reason, "d1_blocked_by_d2")
        self.assertEqual(len(records), 1)

    def test_recovery_marks_sending_unknown_once(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _state_path(Path(temp_dir))
            _begin(path)

            first = recover_interrupted_deliveries(path)
            second = recover_interrupted_deliveries(path)
            records = load_delivery_records(path)

        self.assertEqual(len(first), 1)
        self.assertEqual(first[0].state, DeliveryState.DELIVERY_UNKNOWN)
        self.assertTrue(
            all(
                recipient.state is RecipientDeliveryState.UNKNOWN
                for recipient in first[0].recipients
            )
        )
        self.assertEqual(second, ())
        self.assertEqual(records, first)

    def test_missing_store_load_and_recovery_do_not_create_files(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _state_path(Path(temp_dir))

            loaded = load_delivery_records(path)
            recovered = recover_interrupted_deliveries(path)

            self.assertEqual(loaded, ())
            self.assertEqual(recovered, ())
            self.assertFalse(path.exists())
            self.assertFalse(lock_path_for(path).exists())

    def test_corrupt_or_unknown_schema_fails_closed_without_overwrite(self) -> None:
        documents = (
            b"{not-json\n",
            b'{"schema_version": 999, "records": {}}\n',
        )
        for content in documents:
            with self.subTest(content=content):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    path = _state_path(Path(temp_dir))
                    path.parent.mkdir(mode=0o700)
                    path.write_bytes(content)
                    path.chmod(0o600)

                    with self.assertRaises(DeliveryStoreError):
                        _begin(path)

                    self.assertEqual(path.read_bytes(), content)

    def test_inconsistent_record_is_rejected_on_load(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _state_path(Path(temp_dir))
            path.parent.mkdir(mode=0o700)
            payload = {
                "schema_version": DELIVERY_STORE_SCHEMA_VERSION,
                "records": {
                    f"{EVENT_KEY}:D-2": {
                        "event_key": EVENT_KEY,
                        "offset": "D-2",
                        "operation_id": f"{EVENT_KEY}:D-2",
                        "state": "smtp_accepted",
                        "recipients": [
                            {"recipient_id": recipient_id, "state": "pending"}
                            for recipient_id in RECIPIENT_IDS
                        ],
                    }
                },
            }
            path.write_text(json.dumps(payload), encoding="utf-8")
            path.chmod(0o600)

            with self.assertRaisesRegex(DeliveryStoreError, "state machine"):
                load_delivery_records(path)

    def test_two_processes_cannot_begin_the_same_delivery(self) -> None:
        script = """
import sys
from pathlib import Path
from app.family_calendar_delivery_store import begin_stored_delivery

result = begin_stored_delivery(
    event_key="person-example:birthday:2026-12-19",
    offset="D-2",
    recipient_ids=("recipient-1", "recipient-2", "recipient-3", "recipient-4"),
    path=Path(sys.argv[1]),
)
print(int(result.started))
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _state_path(Path(temp_dir))
            processes = [
                subprocess.Popen(
                    [sys.executable, "-c", script, str(path)],
                    cwd=PROJECT_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for _ in range(2)
            ]
            outputs = [process.communicate(timeout=20) for process in processes]

            for process, (_stdout, stderr) in zip(processes, outputs, strict=True):
                self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(sorted(stdout.strip() for stdout, _stderr in outputs), ["0", "1"])
            self.assertEqual(len(load_delivery_records(path)), 1)


def _state_path(root: Path) -> Path:
    return root / "family" / "delivery_state.json"


def _begin(path: Path, *, offset: NotificationOffset = NotificationOffset.D2):
    return begin_stored_delivery(
        event_key=EVENT_KEY,
        offset=offset,
        recipient_ids=RECIPIENT_IDS,
        path=path,
    )


if __name__ == "__main__":
    unittest.main()
