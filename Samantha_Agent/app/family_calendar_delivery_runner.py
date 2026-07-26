"""Fail-closed configured runner for family-calendar delivery."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.family_calendar_delivery import NotificationOffset, begin_delivery, plan_delivery
from app.family_calendar_delivery_config import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    DeliveryConfigError,
    DeliveryConfigMode,
    load_family_calendar_delivery_config,
)
from app.family_calendar_delivery_coordinator import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_WORKER_PATH,
    DeliveryCoordinatorError,
    DeliveryCoordinatorResult,
    DeliveryTransport,
    coordinate_delivery_attempt,
)
from app.family_calendar_delivery_store import DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH


@dataclass(frozen=True)
class FamilyCalendarDeliveryRunResult:
    """Redacted non-sending result safe for logs and status surfaces."""

    status: str
    recipient_count: int
    attempt_eligible: bool
    coordinator_called: bool
    transport_called: bool


DeliveryCoordinator = Callable[..., DeliveryCoordinatorResult]


def run_configured_family_calendar_delivery(
    *,
    event_key: str,
    offset: NotificationOffset | str,
    transport: DeliveryTransport,
    config_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    state_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
    worker_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_WORKER_PATH,
    coordinator: DeliveryCoordinator = coordinate_delivery_attempt,
) -> FamilyCalendarDeliveryRunResult:
    """Run one configured attempt, keeping disabled and dry-run free of runtime I/O."""

    try:
        config = load_family_calendar_delivery_config(config_path)
    except DeliveryConfigError:
        return FamilyCalendarDeliveryRunResult(
            status="config_error",
            recipient_count=0,
            attempt_eligible=False,
            coordinator_called=False,
            transport_called=False,
        )

    if config.mode is DeliveryConfigMode.DISABLED:
        return FamilyCalendarDeliveryRunResult(
            status="disabled",
            recipient_count=len(config.recipients),
            attempt_eligible=False,
            coordinator_called=False,
            transport_called=False,
        )

    if config.mode is DeliveryConfigMode.DRY_RUN:
        try:
            plan = plan_delivery(event_key=event_key, offset=offset)
            record = begin_delivery(plan, recipient_ids=config.recipient_ids)
        except ValueError:
            return FamilyCalendarDeliveryRunResult(
                status="input_error",
                recipient_count=0,
                attempt_eligible=False,
                coordinator_called=False,
                transport_called=False,
            )
        return FamilyCalendarDeliveryRunResult(
            status="dry_run",
            recipient_count=len(record.recipients),
            attempt_eligible=plan.eligible,
            coordinator_called=False,
            transport_called=False,
        )

    if config.mode is DeliveryConfigMode.ENABLED:
        try:
            coordinated = coordinator(
                event_key=event_key,
                offset=offset,
                recipient_ids=config.recipient_ids,
                transport=transport,
                state_path=state_path,
                worker_path=worker_path,
            )
        except ValueError:
            return FamilyCalendarDeliveryRunResult(
                status="input_error",
                recipient_count=0,
                attempt_eligible=False,
                coordinator_called=True,
                transport_called=False,
            )
        except DeliveryCoordinatorError as exc:
            return FamilyCalendarDeliveryRunResult(
                status=(
                    "delivery_unknown"
                    if exc.transport_called
                    else "runtime_error"
                ),
                recipient_count=len(config.recipients),
                attempt_eligible=False,
                coordinator_called=True,
                transport_called=exc.transport_called,
            )
        except Exception:  # noqa: BLE001 - injected runtime details stay redacted.
            return FamilyCalendarDeliveryRunResult(
                status="runtime_error",
                recipient_count=len(config.recipients),
                attempt_eligible=False,
                coordinator_called=True,
                transport_called=False,
            )
        return FamilyCalendarDeliveryRunResult(
            status=coordinated.status,
            recipient_count=len(config.recipients),
            attempt_eligible=coordinated.plan.eligible,
            coordinator_called=True,
            transport_called=coordinated.transport_called,
        )

    # Keep the runner closed if the loader grows another mode without an
    # explicit implementation here.
    return FamilyCalendarDeliveryRunResult(
        status="config_error",
        recipient_count=0,
        attempt_eligible=False,
        coordinator_called=False,
        transport_called=False,
    )
