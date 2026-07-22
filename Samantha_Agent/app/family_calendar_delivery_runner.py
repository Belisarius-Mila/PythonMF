"""Fail-closed configured runner for family-calendar delivery."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.family_calendar_delivery import NotificationOffset
from app.family_calendar_delivery_config import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    DeliveryConfigError,
    DeliveryConfigMode,
    load_family_calendar_delivery_config,
)
from app.family_calendar_delivery_coordinator import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_WORKER_PATH,
    DeliveryCoordinatorResult,
    DeliveryTransport,
    coordinate_delivery_attempt,
)
from app.family_calendar_delivery_store import DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH


@dataclass(frozen=True)
class FamilyCalendarDeliveryRunResult:
    """Redacted no-op result safe for logs and status surfaces."""

    status: str
    recipient_count: int
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
    """Load private configuration and stop before all effects while disabled."""

    try:
        config = load_family_calendar_delivery_config(config_path)
    except DeliveryConfigError:
        return FamilyCalendarDeliveryRunResult(
            status="config_error",
            recipient_count=0,
            coordinator_called=False,
            transport_called=False,
        )

    if config.mode is DeliveryConfigMode.DISABLED:
        return FamilyCalendarDeliveryRunResult(
            status="disabled",
            recipient_count=len(config.recipients),
            coordinator_called=False,
            transport_called=False,
        )

    # The loader currently rejects every active mode. Keep the runner closed if
    # its contract is widened without an explicit implementation here.
    return FamilyCalendarDeliveryRunResult(
        status="config_error",
        recipient_count=0,
        coordinator_called=False,
        transport_called=False,
    )
