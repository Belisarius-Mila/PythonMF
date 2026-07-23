"""Exactly confirmed one-shot iCloud test email for family-calendar delivery."""

from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path

from app.family_calendar_delivery_config import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    DeliveryConfigMode,
    FamilyCalendarDeliveryConfig,
    load_family_calendar_delivery_config,
)
from app.family_calendar_icloud_smtp_client import (
    ICloudSMTPClient,
    ICloudSMTPClientError,
    SMTPFactory,
    TLSContextFactory,
    create_icloud_tls_context,
)


FAMILY_CALENDAR_TEST_EMAIL_CONFIRMATION = (
    "SEND_ONE_FAMILY_CALENDAR_TEST_EMAIL_TO_FOUR_RECIPIENTS"
)
TEST_EMAIL_SUBJECT = "Samantha: test rodinných upozornění"
TEST_EMAIL_BODY = (
    "Toto je jednorázový test společného doručování upozornění "
    "z rodinného kalendáře.\n"
)


class FamilyCalendarTestEmailError(RuntimeError):
    """Redacted pre-send failure safe for terminal output and logs."""


@dataclass(frozen=True, repr=False)
class FamilyCalendarTestEmailPlan:
    config_path: Path
    config: FamilyCalendarDeliveryConfig

    def __repr__(self) -> str:
        return (
            "FamilyCalendarTestEmailPlan("
            f"mode={self.config.mode.value!r}, "
            f"recipient_count={len(self.config.recipients)}, redacted=True)"
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "status": "preview",
            "mode": self.config.mode.value,
            "recipient_count": len(self.config.recipients),
            "confirmation_required": True,
            "transport_called": False,
        }


@dataclass(frozen=True, repr=False)
class FamilyCalendarTestEmailResult:
    status: str
    recipient_count: int
    accepted_count: int
    refused_count: int
    unknown_count: int
    transport_called: bool

    def __repr__(self) -> str:
        return (
            "FamilyCalendarTestEmailResult("
            f"status={self.status!r}, "
            f"recipient_count={self.recipient_count}, "
            f"accepted_count={self.accepted_count}, "
            f"refused_count={self.refused_count}, "
            f"unknown_count={self.unknown_count}, "
            f"transport_called={self.transport_called}, redacted=True)"
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "status": self.status,
            "recipient_count": self.recipient_count,
            "accepted_count": self.accepted_count,
            "refused_count": self.refused_count,
            "unknown_count": self.unknown_count,
            "transport_called": self.transport_called,
        }


def plan_family_calendar_test_email(
    *,
    config_path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
) -> FamilyCalendarTestEmailPlan:
    """Load one redacted no-send plan from the trusted private configuration."""

    target = Path(config_path)
    config_failed = False
    try:
        config = load_family_calendar_delivery_config(target)
    except Exception:  # noqa: BLE001 - private configuration details stay redacted.
        config_failed = True
    if config_failed:
        raise FamilyCalendarTestEmailError(
            "Family-calendar test email configuration cannot be trusted."
        )
    if config.mode is not DeliveryConfigMode.DRY_RUN:
        raise FamilyCalendarTestEmailError(
            "Family-calendar test email requires dry-run mode."
        )
    if config.smtp_provider != "icloud":
        raise FamilyCalendarTestEmailError(
            "Family-calendar test email requires the iCloud provider."
        )
    return FamilyCalendarTestEmailPlan(config_path=target, config=config)


def require_family_calendar_test_email_confirmation(confirmation: str) -> None:
    """Reject every value except the one exact, auditable send confirmation."""

    if confirmation != FAMILY_CALENDAR_TEST_EMAIL_CONFIRMATION:
        raise FamilyCalendarTestEmailError(
            "Exact family-calendar test email confirmation is required."
        )


def assert_family_calendar_test_email_plan_current(
    plan: FamilyCalendarTestEmailPlan,
) -> None:
    """Fail before secret entry or transport when the previewed config changed."""

    if not isinstance(plan, FamilyCalendarTestEmailPlan):
        raise FamilyCalendarTestEmailError(
            "A validated family-calendar test email plan is required."
        )
    config_failed = False
    try:
        current = load_family_calendar_delivery_config(plan.config_path)
    except Exception:  # noqa: BLE001 - private configuration details stay redacted.
        config_failed = True
    if config_failed or current != plan.config:
        raise FamilyCalendarTestEmailError(
            "Family-calendar test email configuration changed after preview."
        )


def send_family_calendar_test_email(
    plan: FamilyCalendarTestEmailPlan,
    *,
    confirmation: str,
    app_password: str,
    smtp_factory: SMTPFactory | None = None,
    tls_context_factory: TLSContextFactory | None = None,
) -> FamilyCalendarTestEmailResult:
    """Attempt one shared message after confirmation; never persist a secret."""

    require_family_calendar_test_email_confirmation(confirmation)
    assert_family_calendar_test_email_plan_current(plan)
    client_failed = False
    try:
        client = ICloudSMTPClient(
            username=plan.config.sender_address,
            app_password=app_password,
            smtp_factory=smtplib.SMTP if smtp_factory is None else smtp_factory,
            tls_context_factory=(
                create_icloud_tls_context
                if tls_context_factory is None
                else tls_context_factory
            ),
        )
    except ICloudSMTPClientError:
        client_failed = True
    if client_failed:
        raise FamilyCalendarTestEmailError(
            "Local iCloud test email credentials are unavailable."
        )

    recipients = tuple(recipient.address for recipient in plan.config.recipients)
    message = _build_test_message(
        sender=plan.config.sender_address,
        recipients=recipients,
    )
    send_failed = False
    try:
        result = client.send_message(
            message,
            from_addr=plan.config.sender_address,
            to_addrs=recipients,
        )
    except Exception:  # noqa: BLE001 - an attempted SMTP effect is always unknown.
        send_failed = True
    recipient_count = len(recipients)
    if send_failed:
        return FamilyCalendarTestEmailResult(
            status="delivery_unknown",
            recipient_count=recipient_count,
            accepted_count=0,
            refused_count=0,
            unknown_count=recipient_count,
            transport_called=True,
        )

    refused_count = len(result.refused_addresses)
    accepted_count = recipient_count - refused_count
    if refused_count == 0:
        status = "sent"
    elif accepted_count == 0:
        status = "refused"
    else:
        status = "partial"
    return FamilyCalendarTestEmailResult(
        status=status,
        recipient_count=recipient_count,
        accepted_count=accepted_count,
        refused_count=refused_count,
        unknown_count=0,
        transport_called=True,
    )


def _build_test_message(
    *,
    sender: str,
    recipients: tuple[str, ...],
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message["Subject"] = TEST_EMAIL_SUBJECT
    message.set_content(TEST_EMAIL_BODY)
    return message
