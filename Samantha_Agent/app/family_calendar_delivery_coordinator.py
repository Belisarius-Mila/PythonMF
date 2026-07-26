"""Single-worker coordinator for family-calendar delivery attempts."""

from __future__ import annotations

import stat
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from app.family_calendar_delivery import (
    DeliveryPlan,
    DeliveryRecord,
    DeliveryState,
    NotificationOffset,
    begin_delivery,
    complete_delivery,
    plan_delivery,
)
from app.family_calendar_delivery_store import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
    DeliveryStoreError,
    begin_stored_delivery,
    complete_stored_delivery,
    load_delivery_records,
    recover_interrupted_deliveries,
)
from app.file_persistence import FilePersistenceError, exclusive_file_lock, lock_path_for


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FAMILY_CALENDAR_DELIVERY_WORKER_PATH = (
    PROJECT_ROOT / "data" / "private" / "family_calendar" / "delivery_worker"
)


class DeliveryCoordinatorError(RuntimeError):
    """Raised when a coordinated attempt cannot finish safely."""

    def __init__(self, message: str, *, transport_called: bool = False) -> None:
        super().__init__(message)
        self.transport_called = bool(transport_called)


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


@dataclass(frozen=True, repr=False)
class DeliveryRuntimeRecoveryResult:
    status: str
    blocking_count: int
    recovered_operation_ids: tuple[str, ...]

    def __repr__(self) -> str:
        return (
            "DeliveryRuntimeRecoveryResult("
            f"status={self.status!r}, blocking_count={self.blocking_count}, "
            f"recovered_count={len(self.recovered_operation_ids)}, redacted=True)"
        )


DeliveryTransport = Callable[[DeliveryRecord], DeliveryTransportOutcome]


def recover_delivery_runtime(
    *,
    state_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
    worker_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_WORKER_PATH,
    lock_timeout: float = 10.0,
) -> DeliveryRuntimeRecoveryResult:
    """Recover interrupted records and report global blockers before credentials."""

    state_target = Path(state_path)
    worker_target = Path(worker_path)
    try:
        records = load_delivery_records(state_target)
        if any(record.state is DeliveryState.SENDING for record in records):
            _prepare_worker_target(worker_target)
            with exclusive_file_lock(worker_target, timeout=lock_timeout):
                _harden_worker_target(worker_target)
                recovered = recover_interrupted_deliveries(state_target)
                records = load_delivery_records(state_target)
        else:
            recovered = ()
        blocking_count = sum(
            record.state
            in {
                DeliveryState.SENDING,
                DeliveryState.PARTIAL,
                DeliveryState.DELIVERY_UNKNOWN,
            }
            for record in records
        )
        return DeliveryRuntimeRecoveryResult(
            status="recovery_required" if blocking_count else "ready",
            blocking_count=blocking_count,
            recovered_operation_ids=tuple(
                record.operation_id for record in recovered
            ),
        )
    except (DeliveryStoreError, FilePersistenceError, OSError) as exc:
        raise DeliveryCoordinatorError(
            "Family-calendar delivery recovery failed safely."
        ) from exc
    finally:
        if worker_target.exists() or lock_path_for(worker_target).exists():
            _harden_worker_target_best_effort(worker_target)


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
    validation_plan = plan_delivery(event_key=event_key, offset=offset)
    begin_delivery(validation_plan, recipient_ids=recipient_ids)
    worker_target = Path(worker_path)
    state_target = Path(state_path)
    transport_called = False
    try:
        _prepare_worker_target(worker_target)
        with exclusive_file_lock(worker_target, timeout=lock_timeout):
            _harden_worker_target(worker_target)
            recovered = recover_interrupted_deliveries(state_target)
            recovered_ids = tuple(record.operation_id for record in recovered)
            records = load_delivery_records(state_target)
            current_plan = plan_delivery(
                event_key=event_key,
                offset=offset,
                records=records,
            )
            if any(
                record.state
                in {
                    DeliveryState.SENDING,
                    DeliveryState.PARTIAL,
                    DeliveryState.DELIVERY_UNKNOWN,
                }
                for record in records
            ):
                return DeliveryCoordinatorResult(
                    status="recovery_required",
                    plan=current_plan,
                    record=next(
                        (
                            record
                            for record in records
                            if record.operation_id == current_plan.operation_id
                        ),
                        None,
                    ),
                    transport_called=False,
                    recovered_operation_ids=recovered_ids,
                )
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
                transport_called = True
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
        raise DeliveryCoordinatorError(
            "Family-calendar delivery attempt failed safely.",
            transport_called=transport_called,
        ) from exc
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
