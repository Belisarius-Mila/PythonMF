"""Single-worker coordinator for family-calendar delivery attempts."""

from __future__ import annotations

import stat
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from app.family_calendar_delivery import (
    DeliveryPlan,
    DeliveryRecord,
    NotificationOffset,
    complete_delivery,
)
from app.family_calendar_delivery_store import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
    DeliveryStoreError,
    begin_stored_delivery,
    complete_stored_delivery,
    recover_interrupted_deliveries,
)
from app.file_persistence import FilePersistenceError, exclusive_file_lock, lock_path_for


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FAMILY_CALENDAR_DELIVERY_WORKER_PATH = (
    PROJECT_ROOT / "data" / "private" / "family_calendar" / "delivery_worker"
)


class DeliveryCoordinatorError(RuntimeError):
    """Raised when a coordinated attempt cannot finish safely."""


@dataclass(frozen=True)
class DeliveryTransportOutcome:
    accepted_recipient_ids: tuple[str, ...] = ()
    not_sent_recipient_ids: tuple[str, ...] = ()
    unknown_recipient_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class DeliveryCoordinatorResult:
    status: str
    plan: DeliveryPlan
    record: DeliveryRecord | None
    transport_called: bool
    recovered_operation_ids: tuple[str, ...]


DeliveryTransport = Callable[[DeliveryRecord], DeliveryTransportOutcome]


def coordinate_delivery_attempt(
    *,
    event_key: str,
    offset: NotificationOffset | str,
    recipient_ids: Sequence[str],
    transport: DeliveryTransport,
    state_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
    worker_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_WORKER_PATH,
    lock_timeout: float = 10.0,
) -> DeliveryCoordinatorResult:
    """Run one fail-closed attempt while holding the global delivery-worker lock."""

    if not callable(transport):
        raise ValueError("Delivery transport must be callable.")
    worker_target = Path(worker_path)
    state_target = Path(state_path)
    try:
        _prepare_worker_target(worker_target)
        with exclusive_file_lock(worker_target, timeout=lock_timeout):
            _harden_worker_target(worker_target)
            recovered = recover_interrupted_deliveries(state_target)
            recovered_ids = tuple(record.operation_id for record in recovered)
            started = begin_stored_delivery(
                event_key=event_key,
                offset=offset,
                recipient_ids=recipient_ids,
                path=state_target,
            )
            if not started.started:
                return DeliveryCoordinatorResult(
                    status="skipped",
                    plan=started.plan,
                    record=started.record,
                    transport_called=False,
                    recovered_operation_ids=recovered_ids,
                )
            if started.record is None:  # pragma: no cover - defensive invariant.
                raise DeliveryCoordinatorError("Started delivery has no persisted record.")

            record = started.record
            try:
                outcome = transport(record)
                _validate_transport_outcome(record, outcome)
            except Exception:  # noqa: BLE001 - the transport is the external-effect boundary.
                completed = _complete_as_unknown(record, state_target)
                return DeliveryCoordinatorResult(
                    status=completed.state.value,
                    plan=started.plan,
                    record=completed,
                    transport_called=True,
                    recovered_operation_ids=recovered_ids,
                )

            completed = complete_stored_delivery(
                operation_id=record.operation_id,
                accepted_recipient_ids=outcome.accepted_recipient_ids,
                not_sent_recipient_ids=outcome.not_sent_recipient_ids,
                unknown_recipient_ids=outcome.unknown_recipient_ids,
                path=state_target,
            )
            return DeliveryCoordinatorResult(
                status=completed.state.value,
                plan=started.plan,
                record=completed,
                transport_called=True,
                recovered_operation_ids=recovered_ids,
            )
    except DeliveryCoordinatorError:
        raise
    except (DeliveryStoreError, FilePersistenceError, OSError) as exc:
        raise DeliveryCoordinatorError("Family-calendar delivery attempt failed safely.") from exc
    finally:
        _harden_worker_target_best_effort(worker_target)


def _validate_transport_outcome(
    record: DeliveryRecord,
    outcome: DeliveryTransportOutcome,
) -> None:
    if not isinstance(outcome, DeliveryTransportOutcome):
        raise TypeError("Delivery transport returned an unsupported outcome.")
    complete_delivery(
        record,
        accepted_recipient_ids=outcome.accepted_recipient_ids,
        not_sent_recipient_ids=outcome.not_sent_recipient_ids,
        unknown_recipient_ids=outcome.unknown_recipient_ids,
    )


def _complete_as_unknown(record: DeliveryRecord, state_path: Path) -> DeliveryRecord:
    recipient_ids = tuple(recipient.recipient_id for recipient in record.recipients)
    return complete_stored_delivery(
        operation_id=record.operation_id,
        unknown_recipient_ids=recipient_ids,
        path=state_path,
    )


def _prepare_worker_target(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.parent.chmod(0o700)
    worker_lock = lock_path_for(path)
    if worker_lock.exists():
        worker_lock.chmod(0o600)


def _harden_worker_target(path: Path) -> None:
    path.parent.chmod(0o700)
    worker_lock = lock_path_for(path)
    if worker_lock.exists():
        worker_lock.chmod(0o600)
    if stat.S_IMODE(path.parent.stat().st_mode) != 0o700:
        raise DeliveryCoordinatorError("Delivery worker directory is not private.")
    if not worker_lock.exists() or stat.S_IMODE(worker_lock.stat().st_mode) != 0o600:
        raise DeliveryCoordinatorError("Delivery worker lock is not private.")


def _harden_worker_target_best_effort(path: Path) -> None:
    try:
        _harden_worker_target(path)
    except (OSError, DeliveryCoordinatorError):
        return
