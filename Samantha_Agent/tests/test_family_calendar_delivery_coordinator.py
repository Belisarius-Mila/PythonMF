from __future__ import annotations

import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from app.family_calendar_delivery import DeliveryState, NotificationOffset, RecipientDeliveryState
from app.family_calendar_delivery_coordinator import (
    DeliveryTransportOutcome,
    coordinate_delivery_attempt,
)
from app.family_calendar_delivery_store import load_delivery_records
from app.file_persistence import lock_path_for


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVENT_KEY = "person-example:birthday:2026-12-19"
RECIPIENT_IDS = ("recipient-1", "recipient-2", "recipient-3", "recipient-4")


class FamilyCalendarDeliveryCoordinatorTests(unittest.TestCase):
    def test_sending_is_persisted_before_transport_and_result_is_completed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            state_path, worker_path = _paths(Path(temp_dir))
            observed_states = []

            def transport(record):
                stored = load_delivery_records(state_path)
                observed_states.append(stored[0].state)
                self.assertEqual(stored[0], record)
                return DeliveryTransportOutcome(accepted_recipient_ids=RECIPIENT_IDS)

            result = _coordinate(state_path, worker_path, transport)
            stored = load_delivery_records(state_path)

            self.assertEqual(observed_states, [DeliveryState.SENDING])
            self.assertTrue(result.transport_called)
            self.assertEqual(result.status, "smtp_accepted")
            self.assertIsNotNone(result.record)
            self.assertEqual(stored, (result.record,))
            self.assertEqual(stat.S_IMODE(worker_path.parent.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(lock_path_for(worker_path).stat().st_mode), 0o600)

    def test_transport_exception_is_persisted_as_unknown(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            state_path, worker_path = _paths(Path(temp_dir))

            def failing_transport(_record):
                raise RuntimeError("simulated transport failure")

            result = _coordinate(state_path, worker_path, failing_transport)
            stored = load_delivery_records(state_path)

        self.assertEqual(result.status, "delivery_unknown")
        self.assertTrue(result.transport_called)
        self.assertEqual(stored, (result.record,))
        self.assertTrue(
            all(
                recipient.state is RecipientDeliveryState.UNKNOWN
                for recipient in stored[0].recipients
            )
        )

    def test_invalid_transport_outcome_is_persisted_as_unknown(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            state_path, worker_path = _paths(Path(temp_dir))

            result = _coordinate(state_path, worker_path, lambda _record: object())
            stored = load_delivery_records(state_path)

        self.assertEqual(result.status, "delivery_unknown")
        self.assertEqual(stored[0].state, DeliveryState.DELIVERY_UNKNOWN)

    def test_existing_terminal_delivery_skips_transport(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            state_path, worker_path = _paths(Path(temp_dir))
            first = _coordinate(
                state_path,
                worker_path,
                lambda _record: DeliveryTransportOutcome(accepted_recipient_ids=RECIPIENT_IDS),
            )
            calls = 0

            def transport(_record):
                nonlocal calls
                calls += 1
                return DeliveryTransportOutcome(accepted_recipient_ids=RECIPIENT_IDS)

            second = _coordinate(state_path, worker_path, transport)

        self.assertEqual(first.status, "smtp_accepted")
        self.assertEqual(second.status, "skipped")
        self.assertFalse(second.transport_called)
        self.assertEqual(second.plan.reason, "already_recorded")
        self.assertEqual(calls, 0)

    def test_d1_blocked_by_accepted_d2_skips_transport(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            state_path, worker_path = _paths(Path(temp_dir))
            _coordinate(
                state_path,
                worker_path,
                lambda _record: DeliveryTransportOutcome(accepted_recipient_ids=RECIPIENT_IDS),
            )
            calls = 0

            def transport(_record):
                nonlocal calls
                calls += 1
                return DeliveryTransportOutcome(accepted_recipient_ids=RECIPIENT_IDS)

            result = coordinate_delivery_attempt(
                event_key=EVENT_KEY,
                offset=NotificationOffset.D1,
                recipient_ids=RECIPIENT_IDS,
                transport=transport,
                state_path=state_path,
                worker_path=worker_path,
            )

        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.plan.reason, "d1_blocked_by_d2")
        self.assertEqual(calls, 0)

    def test_two_processes_hold_one_worker_lock_and_call_transport_once(self) -> None:
        script = """
import sys
import time
from pathlib import Path
from app.family_calendar_delivery_coordinator import DeliveryTransportOutcome, coordinate_delivery_attempt

state_path = Path(sys.argv[1])
worker_path = Path(sys.argv[2])
counter_path = Path(sys.argv[3])

def transport(_record):
    with counter_path.open("a", encoding="utf-8") as handle:
        handle.write("called\\n")
        handle.flush()
    time.sleep(0.3)
    return DeliveryTransportOutcome(
        accepted_recipient_ids=("recipient-1", "recipient-2", "recipient-3", "recipient-4")
    )

result = coordinate_delivery_attempt(
    event_key="person-example:birthday:2026-12-19",
    offset="D-2",
    recipient_ids=("recipient-1", "recipient-2", "recipient-3", "recipient-4"),
    transport=transport,
    state_path=state_path,
    worker_path=worker_path,
)
print(result.status)
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            state_path, worker_path = _paths(root)
            counter_path = root / "transport_calls.txt"
            processes = [
                subprocess.Popen(
                    [sys.executable, "-c", script, str(state_path), str(worker_path), str(counter_path)],
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
            self.assertEqual(
                sorted(stdout.strip() for stdout, _stderr in outputs),
                ["skipped", "smtp_accepted"],
            )
            self.assertEqual(counter_path.read_text(encoding="utf-8").splitlines(), ["called"])
            self.assertEqual(load_delivery_records(state_path)[0].state, DeliveryState.SMTP_ACCEPTED)

    def test_process_crash_after_begin_recovers_unknown_without_retry(self) -> None:
        script = """
import os
import sys
from pathlib import Path
from app.family_calendar_delivery_coordinator import coordinate_delivery_attempt

def crash_after_begin(_record):
    os._exit(23)

coordinate_delivery_attempt(
    event_key="person-example:birthday:2026-12-19",
    offset="D-2",
    recipient_ids=("recipient-1", "recipient-2", "recipient-3", "recipient-4"),
    transport=crash_after_begin,
    state_path=Path(sys.argv[1]),
    worker_path=Path(sys.argv[2]),
)
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            state_path, worker_path = _paths(Path(temp_dir))
            crashed = subprocess.run(
                [sys.executable, "-c", script, str(state_path), str(worker_path)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=20,
            )
            self.assertEqual(crashed.returncode, 23, crashed.stderr)
            self.assertEqual(load_delivery_records(state_path)[0].state, DeliveryState.SENDING)
            calls = 0

            def transport(_record):
                nonlocal calls
                calls += 1
                return DeliveryTransportOutcome(accepted_recipient_ids=RECIPIENT_IDS)

            recovered = _coordinate(state_path, worker_path, transport)
            stored = load_delivery_records(state_path)

        self.assertEqual(recovered.status, "skipped")
        self.assertFalse(recovered.transport_called)
        self.assertEqual(recovered.recovered_operation_ids, (f"{EVENT_KEY}:D-2",))
        self.assertEqual(calls, 0)
        self.assertEqual(stored[0].state, DeliveryState.DELIVERY_UNKNOWN)


def _paths(root: Path) -> tuple[Path, Path]:
    private_dir = root / "family"
    return private_dir / "delivery_state.json", private_dir / "delivery_worker"


def _coordinate(state_path: Path, worker_path: Path, transport):
    return coordinate_delivery_attempt(
        event_key=EVENT_KEY,
        offset=NotificationOffset.D2,
        recipient_ids=RECIPIENT_IDS,
        transport=transport,
        state_path=state_path,
        worker_path=worker_path,
    )


if __name__ == "__main__":
    unittest.main()
