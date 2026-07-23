"""iCloud STARTTLS SMTP client with an explicitly injected session factory."""

from __future__ import annotations

import ssl
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from email.message import EmailMessage
from enum import StrEnum
from typing import Any, Protocol

import certifi

from app.family_calendar_delivery_config import (
    CANONICAL_RECIPIENT_IDS,
    EMAIL_ADDRESS_RE,
)
from app.family_calendar_smtp_adapter import SMTPClientResult


ICLOUD_SMTP_HOST = "smtp.mail.me.com"
ICLOUD_SMTP_PORT = 587
ICLOUD_SMTP_TIMEOUT_SECONDS = 30


class ICloudSMTPClientError(RuntimeError):
    """Redacted iCloud SMTP failure safe for logs and status surfaces."""


class ICloudSMTPDiagnosticCategory(StrEnum):
    CONNECTION_FAILED = "CONNECTION_FAILED"
    TLS_CONTEXT_FAILED = "TLS_CONTEXT_FAILED"
    STARTTLS_FAILED = "STARTTLS_FAILED"
    POST_TLS_EHLO_FAILED = "POST_TLS_EHLO_FAILED"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    AUTH_OK_NO_SEND = "AUTH_OK_NO_SEND"
    MAIL_FROM_REJECTED = "MAIL_FROM_REJECTED"
    RECIPIENTS_REJECTED = "RECIPIENTS_REJECTED"
    RSET_FAILED_NO_DATA_NO_SEND = "RSET_FAILED_NO_DATA_NO_SEND"
    SESSION_CLOSE_FAILED_NO_DATA_NO_SEND = "SESSION_CLOSE_FAILED_NO_DATA_NO_SEND"
    ENVELOPE_OK_NO_DATA_NO_SEND = "ENVELOPE_OK_NO_DATA_NO_SEND"
    OTHER_REDACTED = "OTHER_REDACTED"


@dataclass(frozen=True, repr=False)
class ICloudSMTPDiagnosticResult:
    category: ICloudSMTPDiagnosticCategory

    @property
    def succeeded(self) -> bool:
        return self.category is ICloudSMTPDiagnosticCategory.AUTH_OK_NO_SEND

    def __repr__(self) -> str:
        return (
            "ICloudSMTPDiagnosticResult("
            f"category={self.category.value!r}, redacted=True, send_called=False)"
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "category": self.category.value,
            "redacted": True,
            "send_called": False,
            "status": "diagnostic",
        }


@dataclass(frozen=True, repr=False)
class ICloudSMTPEnvelopeDiagnosticResult:
    category: ICloudSMTPDiagnosticCategory
    recipient_count: int
    accepted_recipient_count: int
    rejected_recipient_count: int
    unknown_recipient_count: int
    rset_ok: bool | None
    session_close_ok: bool | None

    @property
    def succeeded(self) -> bool:
        return (
            self.category
            is ICloudSMTPDiagnosticCategory.ENVELOPE_OK_NO_DATA_NO_SEND
        )

    def __repr__(self) -> str:
        return (
            "ICloudSMTPEnvelopeDiagnosticResult("
            f"category={self.category.value!r}, "
            f"recipient_count={self.recipient_count}, "
            f"accepted_recipient_count={self.accepted_recipient_count}, "
            f"rejected_recipient_count={self.rejected_recipient_count}, "
            f"unknown_recipient_count={self.unknown_recipient_count}, "
            f"rset_ok={self.rset_ok!r}, session_close_ok={self.session_close_ok!r}, "
            "redacted=True, data_called=False, send_called=False)"
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "accepted_recipient_count": self.accepted_recipient_count,
            "category": self.category.value,
            "data_called": False,
            "recipient_count": self.recipient_count,
            "redacted": True,
            "rejected_recipient_count": self.rejected_recipient_count,
            "rset_ok": self.rset_ok,
            "send_called": False,
            "session_close_ok": self.session_close_ok,
            "status": "diagnostic",
            "unknown_recipient_count": self.unknown_recipient_count,
        }


class SMTPSession(Protocol):
    def __enter__(self) -> "SMTPSession": ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: Any,
    ) -> object: ...

    def ehlo(self) -> object: ...

    def starttls(self, *, context: ssl.SSLContext) -> object: ...

    def login(self, user: str, password: str) -> object: ...

    def mail(self, sender: str) -> tuple[int, bytes]: ...

    def rcpt(self, recipient: str) -> tuple[int, bytes]: ...

    def rset(self) -> tuple[int, bytes]: ...

    def send_message(
        self,
        message: EmailMessage,
        *,
        from_addr: str,
        to_addrs: Sequence[str],
    ) -> Mapping[str, object]: ...


SMTPFactory = Callable[..., SMTPSession]
TLSContextFactory = Callable[[], ssl.SSLContext]


def create_icloud_tls_context() -> ssl.SSLContext:
    """Build a verified TLS context from the application's declared CA bundle."""

    return ssl.create_default_context(cafile=certifi.where())


@dataclass(frozen=True, repr=False)
class ICloudSMTPClient:
    username: str
    app_password: str
    smtp_factory: SMTPFactory
    tls_context_factory: TLSContextFactory = create_icloud_tls_context

    def __post_init__(self) -> None:
        clean_username = _validate_address(self.username, field="username")
        if (
            not isinstance(self.app_password, str)
            or not self.app_password
            or self.app_password != self.app_password.strip()
            or "\r" in self.app_password
            or "\n" in self.app_password
        ):
            raise ICloudSMTPClientError("iCloud SMTP credentials are invalid.")
        if not callable(self.smtp_factory) or not callable(self.tls_context_factory):
            raise ICloudSMTPClientError("iCloud SMTP dependencies are invalid.")
        object.__setattr__(self, "username", clean_username)

    def __repr__(self) -> str:
        return (
            "ICloudSMTPClient("
            f"host={ICLOUD_SMTP_HOST!r}, port={ICLOUD_SMTP_PORT}, redacted=True)"
        )

    def send_message(
        self,
        message: EmailMessage,
        *,
        from_addr: str,
        to_addrs: Sequence[str],
    ) -> SMTPClientResult:
        """Send one shared message and return only validated refused addresses."""

        if not isinstance(message, EmailMessage):
            raise ICloudSMTPClientError("iCloud SMTP message is invalid.")
        clean_from = _validate_address(from_addr, field="sender")
        if clean_from.casefold() != self.username.casefold():
            raise ICloudSMTPClientError("iCloud SMTP sender does not match its account.")
        recipients = _validate_recipients(to_addrs)
        operation_failed = False
        try:
            tls_context = self.tls_context_factory()
            with self.smtp_factory(
                ICLOUD_SMTP_HOST,
                ICLOUD_SMTP_PORT,
                timeout=ICLOUD_SMTP_TIMEOUT_SECONDS,
            ) as smtp:
                smtp.ehlo()
                smtp.starttls(context=tls_context)
                smtp.ehlo()
                smtp.login(self.username, self.app_password)
                refused = smtp.send_message(
                    message,
                    from_addr=clean_from,
                    to_addrs=recipients,
                )
            refused_addresses = _validated_refused_addresses(
                refused,
                recipients=recipients,
            )
        except ICloudSMTPClientError:
            raise
        except Exception:
            operation_failed = True
        if operation_failed:
            raise ICloudSMTPClientError("iCloud SMTP operation failed safely.")
        return SMTPClientResult(refused_addresses=refused_addresses)

    def diagnose_authentication(self) -> ICloudSMTPDiagnosticResult:
        """Verify connection, STARTTLS and login without constructing or sending mail."""

        stage = ICloudSMTPDiagnosticCategory.TLS_CONTEXT_FAILED
        try:
            tls_context = self.tls_context_factory()
            stage = ICloudSMTPDiagnosticCategory.CONNECTION_FAILED
            with self.smtp_factory(
                ICLOUD_SMTP_HOST,
                ICLOUD_SMTP_PORT,
                timeout=ICLOUD_SMTP_TIMEOUT_SECONDS,
            ) as smtp:
                smtp.ehlo()
                stage = ICloudSMTPDiagnosticCategory.STARTTLS_FAILED
                smtp.starttls(context=tls_context)
                stage = ICloudSMTPDiagnosticCategory.POST_TLS_EHLO_FAILED
                smtp.ehlo()
                stage = ICloudSMTPDiagnosticCategory.AUTHENTICATION_FAILED
                smtp.login(self.username, self.app_password)
                stage = ICloudSMTPDiagnosticCategory.OTHER_REDACTED
        except Exception:  # noqa: BLE001 - only the redacted stage leaves this boundary.
            return ICloudSMTPDiagnosticResult(category=stage)
        return ICloudSMTPDiagnosticResult(
            category=ICloudSMTPDiagnosticCategory.AUTH_OK_NO_SEND
        )

    def diagnose_envelope(
        self,
        *,
        from_addr: str,
        to_addrs: Sequence[str],
    ) -> ICloudSMTPEnvelopeDiagnosticResult:
        """Validate one SMTP envelope, then RSET before DATA can be issued."""

        clean_from = _validate_address(from_addr, field="sender")
        if clean_from.casefold() != self.username.casefold():
            raise ICloudSMTPClientError(
                "iCloud SMTP sender does not match its account."
            )
        recipients = _validate_recipients(to_addrs)
        recipient_count = len(recipients)
        accepted_count = 0
        rejected_count = 0
        envelope_category: ICloudSMTPDiagnosticCategory | None = None
        rset_ok: bool | None = None
        session_close_ok: bool | None = None
        stage = ICloudSMTPDiagnosticCategory.TLS_CONTEXT_FAILED
        try:
            tls_context = self.tls_context_factory()
            stage = ICloudSMTPDiagnosticCategory.CONNECTION_FAILED
            with self.smtp_factory(
                ICLOUD_SMTP_HOST,
                ICLOUD_SMTP_PORT,
                timeout=ICLOUD_SMTP_TIMEOUT_SECONDS,
            ) as smtp:
                smtp.ehlo()
                stage = ICloudSMTPDiagnosticCategory.STARTTLS_FAILED
                smtp.starttls(context=tls_context)
                stage = ICloudSMTPDiagnosticCategory.POST_TLS_EHLO_FAILED
                smtp.ehlo()
                stage = ICloudSMTPDiagnosticCategory.AUTHENTICATION_FAILED
                smtp.login(self.username, self.app_password)
                stage = ICloudSMTPDiagnosticCategory.OTHER_REDACTED
                transaction_attempted = False
                try:
                    transaction_attempted = True
                    mail_code, _mail_reply = smtp.mail(clean_from)
                    if mail_code != 250:
                        envelope_category = (
                            ICloudSMTPDiagnosticCategory.MAIL_FROM_REJECTED
                        )
                    else:
                        for recipient in recipients:
                            rcpt_code, _rcpt_reply = smtp.rcpt(recipient)
                            if rcpt_code in {250, 251}:
                                accepted_count += 1
                            else:
                                rejected_count += 1
                        envelope_category = (
                            ICloudSMTPDiagnosticCategory.ENVELOPE_OK_NO_DATA_NO_SEND
                            if rejected_count == 0
                            else ICloudSMTPDiagnosticCategory.RECIPIENTS_REJECTED
                        )
                except Exception:  # noqa: BLE001 - only redacted state crosses out.
                    envelope_category = ICloudSMTPDiagnosticCategory.OTHER_REDACTED
                finally:
                    if transaction_attempted:
                        try:
                            rset_code, _rset_reply = smtp.rset()
                        except Exception:  # noqa: BLE001 - reply details stay private.
                            rset_ok = False
                        else:
                            rset_ok = rset_code == 250
                if (
                    rset_ok is False
                    and envelope_category
                    is ICloudSMTPDiagnosticCategory.ENVELOPE_OK_NO_DATA_NO_SEND
                ):
                    envelope_category = (
                        ICloudSMTPDiagnosticCategory.RSET_FAILED_NO_DATA_NO_SEND
                    )
                stage = (
                    ICloudSMTPDiagnosticCategory.SESSION_CLOSE_FAILED_NO_DATA_NO_SEND
                )
            session_close_ok = True
        except Exception:  # noqa: BLE001 - only redacted stage leaves this boundary.
            if envelope_category is not None:
                session_close_ok = False
                if (
                    envelope_category
                    is ICloudSMTPDiagnosticCategory.ENVELOPE_OK_NO_DATA_NO_SEND
                ):
                    envelope_category = stage
            else:
                envelope_category = stage
        unknown_count = recipient_count - accepted_count - rejected_count
        return ICloudSMTPEnvelopeDiagnosticResult(
            category=envelope_category,
            recipient_count=recipient_count,
            accepted_recipient_count=accepted_count,
            rejected_recipient_count=rejected_count,
            unknown_recipient_count=unknown_count,
            rset_ok=rset_ok,
            session_close_ok=session_close_ok,
        )


def _validate_recipients(values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or len(values) != len(CANONICAL_RECIPIENT_IDS):
        raise ICloudSMTPClientError("iCloud SMTP requires exactly four recipients.")
    recipients = tuple(_validate_address(value, field="recipient") for value in values)
    if len({address.casefold() for address in recipients}) != len(recipients):
        raise ICloudSMTPClientError("iCloud SMTP recipients must be distinct.")
    return recipients


def _validated_refused_addresses(
    refused: Mapping[str, object],
    *,
    recipients: Sequence[str],
) -> tuple[str, ...]:
    if not isinstance(refused, Mapping):
        raise ICloudSMTPClientError("iCloud SMTP returned an unknown result.")
    known = {address.casefold(): address for address in recipients}
    normalized_refused: set[str] = set()
    for raw_address in refused:
        clean_address = _validate_address(raw_address, field="refused recipient")
        normalized = clean_address.casefold()
        if normalized not in known or normalized in normalized_refused:
            raise ICloudSMTPClientError("iCloud SMTP returned an unknown result.")
        normalized_refused.add(normalized)
    return tuple(
        address for address in recipients if address.casefold() in normalized_refused
    )


def _validate_address(value: str, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or "\r" in value
        or "\n" in value
        or len(value) > 320
        or EMAIL_ADDRESS_RE.fullmatch(value) is None
    ):
        raise ICloudSMTPClientError(f"iCloud SMTP {field} is invalid.")
    return value
