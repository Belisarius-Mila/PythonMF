"""Enabled family-calendar delivery over private state, Keychain, and SMTP."""

from __future__ import annotations

import smtplib
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
    DeliveryRuntimeRecoveryResult,
    recover_delivery_runtime,
)
from app.family_calendar_delivery_keychain import read_family_calendar_app_password
from app.family_calendar_delivery_message import (
    build_family_calendar_delivery_envelope,
)
from app.family_calendar_delivery_runner import (
    FamilyCalendarDeliveryRunResult,
    run_configured_family_calendar_delivery,
)
from app.family_calendar_delivery_store import DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH
from app.family_calendar_icloud_smtp_client import ICloudSMTPClient
from app.family_calendar_smtp_adapter import (
    SMTPClient,
    build_family_calendar_smtp_transport,
)


@dataclass(frozen=True, repr=False)
class FamilyCalendarAutomaticDeliveryResult:
    """Aggregate enabled-run result containing no private identity or message text."""

    status: str
    candidate_count: int
    d2_count: int
    d1_count: int
    eligible_count: int
    attempted_count: int
    skipped_count: int
    accepted_count: int
    not_sent_count: int
    partial_count: int
    delivery_unknown_count: int
    recovery_required_count: int
    recipient_count: int
    coordinator_called: bool
    recovery_checked: bool
    keychain_read: bool
    transport_called: bool

    def __repr__(self) -> str:
        return (
            "FamilyCalendarAutomaticDeliveryResult("
            f"status={self.status!r}, candidate_count={self.candidate_count}, "
            f"attempted_count={self.attempted_count}, redacted=True)"
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "status": self.status,
            "candidate_count": self.candidate_count,
            "d2_count": self.d2_count,
            "d1_count": self.d1_count,
            "eligible_count": self.eligible_count,
            "attempted_count": self.attempted_count,
            "skipped_count": self.skipped_count,
            "accepted_count": self.accepted_count,
            "not_sent_count": self.not_sent_count,
            "partial_count": self.partial_count,
            "delivery_unknown_count": self.delivery_unknown_count,
            "recovery_required_count": self.recovery_required_count,
            "recipient_count": self.recipient_count,
            "coordinator_called": self.coordinator_called,
            "recovery_checked": self.recovery_checked,
            "keychain_read": self.keychain_read,
            "transport_called": self.transport_called,
            "redacted": True,
        }


CredentialReader = Callable[[], str]
SMTPClientFactory = Callable[[str, str], SMTPClient]
ConfiguredRunner = Callable[..., FamilyCalendarDeliveryRunResult]
RuntimeRecovery = Callable[..., DeliveryRuntimeRecoveryResult]
_ENABLED_RUNNER_STATUSES = frozenset(
    {
        "smtp_accepted",
        "not_sent",
        "partial",
        "delivery_unknown",
        "recovery_required",
        "runtime_error",
        "input_error",
        "config_error",
        "skipped",
    }
)


def run_family_calendar_automatic_delivery(
    *,
    today: date | None = None,
    people_path: Path = DEFAULT_FAMILY_CALENDAR_PATH,
    config_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    state_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_PATH,
    worker_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_WORKER_PATH,
    credential_reader: CredentialReader = read_family_calendar_app_password,
    smtp_client_factory: SMTPClientFactory | None = None,
    configured_runner: ConfiguredRunner = run_configured_family_calendar_delivery,
    runtime_recovery: RuntimeRecovery = recover_delivery_runtime,
) -> FamilyCalendarAutomaticDeliveryResult:
    """Run today's enabled D-2/D-1 candidates through the persistent coordinator."""

    today_date = today or date.today()
    if not isinstance(today_date, date):
        return _empty_result("input_error")
    try:
        config = load_family_calendar_delivery_config(config_path)
    except Exception:  # noqa: BLE001 - private configuration details stay redacted.
        return _empty_result("config_error")
    recipient_count = len(config.recipients)
    if config.mode is not DeliveryConfigMode.ENABLED:
        return _empty_result("not_enabled", recipient_count=recipient_count)
    if config.smtp_provider != "icloud":
        return _empty_result("provider_error", recipient_count=recipient_count)

    try:
        recovery = runtime_recovery(
            state_path=state_path,
            worker_path=worker_path,
        )
    except Exception:  # noqa: BLE001 - persistence details stay redacted.
        return _empty_result(
            "runtime_error",
            recipient_count=recipient_count,
            recovery_checked=True,
        )
    if (
        not isinstance(recovery, DeliveryRuntimeRecoveryResult)
        or recovery.status not in {"ready", "recovery_required"}
        or recovery.blocking_count < 0
    ):
        return _empty_result(
            "safety_error",
            recipient_count=recipient_count,
            recovery_checked=True,
        )
    if recovery.status == "recovery_required":
        return _aggregate_result(
            status="recovery_required",
            candidate_count=0,
            d2_count=0,
            d1_count=0,
            recipient_count=recipient_count,
            recovery_checked=True,
            recovery_required_count=recovery.blocking_count,
            keychain_read=False,
            results=(),
        )

    try:
        _assert_private_people_file(Path(people_path))
        people = load_family_people(people_path, today=today_date)
        events = upcoming_family_events(people, today=today_date, lookahead_days=2)
        candidates = tuple(
            event
            for event in events
            if event.notification_due and event.days_until in (1, 2)
        )
    except Exception:  # noqa: BLE001 - private calendar details stay redacted.
        return _empty_result("calendar_error", recipient_count=recipient_count)

    d2_count = sum(event.days_until == 2 for event in candidates)
    d1_count = sum(event.days_until == 1 for event in candidates)
    if not candidates:
        return _aggregate_result(
            status="enabled",
            candidate_count=0,
            d2_count=0,
            d1_count=0,
            recipient_count=recipient_count,
            recovery_checked=True,
            keychain_read=False,
            results=(),
        )

    try:
        app_password = credential_reader()
    except Exception:  # noqa: BLE001 - Keychain and secret details stay redacted.
        return _aggregate_result(
            status="credential_error",
            candidate_count=len(candidates),
            d2_count=d2_count,
            d1_count=d1_count,
            recipient_count=recipient_count,
            recovery_checked=True,
            keychain_read=True,
            results=(),
        )
    try:
        client_factory = smtp_client_factory or _build_icloud_smtp_client
        client = client_factory(config.sender_address, app_password)
    except Exception:  # noqa: BLE001 - credential details stay redacted.
        return _aggregate_result(
            status="runtime_error",
            candidate_count=len(candidates),
            d2_count=d2_count,
            d1_count=d1_count,
            recipient_count=recipient_count,
            recovery_checked=True,
            keychain_read=True,
            results=(),
        )

    results: list[FamilyCalendarDeliveryRunResult] = []
    try:
        for event in candidates:
            envelope = build_family_calendar_delivery_envelope(
                event,
                recipients=config.recipients,
            )
            transport = build_family_calendar_smtp_transport(
                envelope=envelope,
                sender_address=config.sender_address,
                client=client,
            )
            result = configured_runner(
                event_key=envelope.event_key,
                offset=envelope.offset,
                transport=transport,
                config_path=config_path,
                state_path=state_path,
                worker_path=worker_path,
            )
            results.append(result)
            if (
                not isinstance(result, FamilyCalendarDeliveryRunResult)
                or result.recipient_count != recipient_count
                or not result.coordinator_called
                or result.status not in _ENABLED_RUNNER_STATUSES
            ):
                return _aggregate_result(
                    status="safety_error",
                    candidate_count=len(candidates),
                    d2_count=d2_count,
                    d1_count=d1_count,
                    recipient_count=recipient_count,
                    recovery_checked=True,
                    keychain_read=True,
                    results=tuple(results),
                )
            if result.status in {
                "partial",
                "delivery_unknown",
                "recovery_required",
                "runtime_error",
                "config_error",
                "input_error",
            }:
                break
    except Exception:  # noqa: BLE001 - all runtime details stay redacted.
        return _aggregate_result(
            status="safety_error",
            candidate_count=len(candidates),
            d2_count=d2_count,
            d1_count=d1_count,
            recipient_count=recipient_count,
            recovery_checked=True,
            keychain_read=True,
            results=tuple(results),
        )

    statuses = {result.status for result in results}
    if statuses & {"delivery_unknown", "recovery_required"}:
        status = "recovery_required"
    elif "partial" in statuses:
        status = "manual_review_required"
    elif statuses & {
        "runtime_error",
        "config_error",
        "input_error",
    }:
        status = "safety_error"
    else:
        status = "enabled"
    return _aggregate_result(
        status=status,
        candidate_count=len(candidates),
        d2_count=d2_count,
        d1_count=d1_count,
        recipient_count=recipient_count,
        recovery_checked=True,
        keychain_read=True,
        results=tuple(results),
    )


def _build_icloud_smtp_client(username: str, app_password: str) -> SMTPClient:
    return ICloudSMTPClient(
        username=username,
        app_password=app_password,
        smtp_factory=smtplib.SMTP,
    )


def _aggregate_result(
    *,
    status: str,
    candidate_count: int,
    d2_count: int,
    d1_count: int,
    recipient_count: int,
    recovery_checked: bool,
    keychain_read: bool,
    results: tuple[FamilyCalendarDeliveryRunResult, ...],
    recovery_required_count: int | None = None,
) -> FamilyCalendarAutomaticDeliveryResult:
    return FamilyCalendarAutomaticDeliveryResult(
        status=status,
        candidate_count=candidate_count,
        d2_count=d2_count,
        d1_count=d1_count,
        eligible_count=sum(result.attempt_eligible for result in results),
        attempted_count=sum(result.transport_called for result in results),
        skipped_count=sum(result.status == "skipped" for result in results),
        accepted_count=sum(result.status == "smtp_accepted" for result in results),
        not_sent_count=sum(result.status == "not_sent" for result in results),
        partial_count=sum(result.status == "partial" for result in results),
        delivery_unknown_count=sum(
            result.status == "delivery_unknown" for result in results
        ),
        recovery_required_count=(
            sum(result.status == "recovery_required" for result in results)
            if recovery_required_count is None
            else recovery_required_count
        ),
        recipient_count=recipient_count,
        coordinator_called=any(result.coordinator_called for result in results),
        recovery_checked=recovery_checked,
        keychain_read=keychain_read,
        transport_called=any(result.transport_called for result in results),
    )


def _empty_result(
    status: str,
    *,
    recipient_count: int = 0,
    recovery_checked: bool = False,
) -> FamilyCalendarAutomaticDeliveryResult:
    return _aggregate_result(
        status=status,
        candidate_count=0,
        d2_count=0,
        d1_count=0,
        recipient_count=recipient_count,
        recovery_checked=recovery_checked,
        keychain_read=False,
        results=(),
    )


def _assert_private_people_file(path: Path) -> None:
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError("Private family calendar must not use symbolic links.")
    if not path.is_file():
        raise ValueError("Private family calendar is missing.")
    if stat.S_IMODE(path.parent.stat().st_mode) != 0o700:
        raise ValueError("Private family calendar directory is not private.")
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise ValueError("Private family calendar file is not private.")
