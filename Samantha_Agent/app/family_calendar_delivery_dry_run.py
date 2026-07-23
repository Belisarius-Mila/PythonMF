"""Operational read-only dry-run over today's private family-calendar events."""

from __future__ import annotations

import stat
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from app.family_calendar import (
    DEFAULT_FAMILY_CALENDAR_PATH,
    load_family_people,
    upcoming_family_events,
)
from app.family_calendar_delivery import NotificationOffset
from app.family_calendar_delivery_config import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    DeliveryConfigMode,
    load_family_calendar_delivery_config,
)
from app.family_calendar_delivery_coordinator import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_WORKER_PATH,
)
from app.family_calendar_delivery_runner import (
    FamilyCalendarDeliveryRunResult,
    run_configured_family_calendar_delivery,
)
from app.family_calendar_delivery_store import DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH


@dataclass(frozen=True)
class FamilyCalendarOperationalDryRunResult:
    """Aggregate result containing no event, person, or address identity."""

    status: str
    candidate_count: int
    d2_count: int
    d1_count: int
    eligible_count: int
    recipient_count: int
    coordinator_called: bool
    transport_called: bool

    def safe_document(self) -> dict[str, object]:
        return {
            "status": self.status,
            "candidate_count": self.candidate_count,
            "d2_count": self.d2_count,
            "d1_count": self.d1_count,
            "eligible_count": self.eligible_count,
            "recipient_count": self.recipient_count,
            "coordinator_called": self.coordinator_called,
            "transport_called": self.transport_called,
        }


ConfiguredRunner = Callable[..., FamilyCalendarDeliveryRunResult]


class _RuntimeGuards:
    def __init__(self) -> None:
        self.coordinator_called = False
        self.transport_called = False

    def transport(self, _record: object) -> object:
        self.transport_called = True
        raise RuntimeError("Transport is forbidden during operational dry-run.")

    def coordinator(self, **_kwargs: object) -> object:
        self.coordinator_called = True
        raise RuntimeError("Coordinator is forbidden during operational dry-run.")


def run_family_calendar_operational_dry_run(
    *,
    today: date | None = None,
    people_path: Path = DEFAULT_FAMILY_CALENDAR_PATH,
    config_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    state_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
    worker_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_WORKER_PATH,
    configured_runner: ConfiguredRunner = run_configured_family_calendar_delivery,
) -> FamilyCalendarOperationalDryRunResult:
    """Validate today's D-2/D-1 candidates without runtime or transport I/O."""

    today_date = today or date.today()
    if not isinstance(today_date, date):
        return _empty_result("input_error")
    try:
        config = load_family_calendar_delivery_config(config_path)
    except Exception:  # noqa: BLE001 - private config details must stay redacted.
        return _empty_result("config_error")
    if config.mode is not DeliveryConfigMode.DRY_RUN:
        return _empty_result("not_dry_run", recipient_count=len(config.recipients))

    try:
        _assert_private_people_file(Path(people_path))
        people = load_family_people(people_path, today=today_date)
        events = upcoming_family_events(people, today=today_date, lookahead_days=2)
        candidates = [
            event
            for event in events
            if event.notification_due and event.days_until in (1, 2)
        ]
    except Exception:  # noqa: BLE001 - private calendar details must stay redacted.
        return _empty_result("calendar_error", recipient_count=len(config.recipients))

    d2_count = sum(event.days_until == 2 for event in candidates)
    d1_count = sum(event.days_until == 1 for event in candidates)
    guards = _RuntimeGuards()
    results: list[FamilyCalendarDeliveryRunResult] = []
    try:
        for event in candidates:
            result = configured_runner(
                event_key=event.event_key,
                offset=(
                    NotificationOffset.D2
                    if event.days_until == 2
                    else NotificationOffset.D1
                ),
                transport=guards.transport,
                config_path=config_path,
                state_path=state_path,
                worker_path=worker_path,
                coordinator=guards.coordinator,
            )
            results.append(result)
    except Exception:  # noqa: BLE001 - runtime violations must stay redacted.
        return _result(
            status="safety_error",
            candidate_count=len(candidates),
            d2_count=d2_count,
            d1_count=d1_count,
            eligible_count=sum(result.attempt_eligible for result in results),
            recipient_count=len(config.recipients),
            guards=guards,
        )

    try:
        unsafe_result = any(
            result.status != "dry_run"
            or not result.attempt_eligible
            or result.recipient_count != len(config.recipients)
            or result.coordinator_called
            or result.transport_called
            for result in results
        )
        eligible_count = sum(result.attempt_eligible for result in results)
    except Exception:  # noqa: BLE001 - malformed runner results fail closed.
        return _result(
            status="safety_error",
            candidate_count=len(candidates),
            d2_count=d2_count,
            d1_count=d1_count,
            eligible_count=0,
            recipient_count=len(config.recipients),
            guards=guards,
        )
    status = (
        "safety_error"
        if unsafe_result or guards.coordinator_called or guards.transport_called
        else "dry_run"
    )
    return _result(
        status=status,
        candidate_count=len(candidates),
        d2_count=d2_count,
        d1_count=d1_count,
        eligible_count=eligible_count,
        recipient_count=len(config.recipients),
        guards=guards,
        results=results,
    )


def _result(
    *,
    status: str,
    candidate_count: int,
    d2_count: int,
    d1_count: int,
    eligible_count: int,
    recipient_count: int,
    guards: _RuntimeGuards,
    results: list[FamilyCalendarDeliveryRunResult] | None = None,
) -> FamilyCalendarOperationalDryRunResult:
    runner_results = results or []
    return FamilyCalendarOperationalDryRunResult(
        status=status,
        candidate_count=candidate_count,
        d2_count=d2_count,
        d1_count=d1_count,
        eligible_count=eligible_count,
        recipient_count=recipient_count,
        coordinator_called=(
            guards.coordinator_called
            or any(result.coordinator_called for result in runner_results)
        ),
        transport_called=(
            guards.transport_called
            or any(result.transport_called for result in runner_results)
        ),
    )


def _empty_result(
    status: str,
    *,
    recipient_count: int = 0,
) -> FamilyCalendarOperationalDryRunResult:
    return FamilyCalendarOperationalDryRunResult(
        status=status,
        candidate_count=0,
        d2_count=0,
        d1_count=0,
        eligible_count=0,
        recipient_count=recipient_count,
        coordinator_called=False,
        transport_called=False,
    )


def _assert_private_people_file(path: Path) -> None:
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError("Private family calendar must not use links.")
    if not path.is_file():
        raise ValueError("Private family calendar is missing.")
    if stat.S_IMODE(path.parent.stat().st_mode) != 0o700:
        raise ValueError("Private family calendar directory is unsafe.")
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise ValueError("Private family calendar file is unsafe.")
