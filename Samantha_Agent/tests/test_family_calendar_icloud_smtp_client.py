from __future__ import annotations

import ssl
import unittest
from datetime import date
from email.message import EmailMessage
from unittest.mock import patch

from app.family_calendar import FamilyEvent
from app.family_calendar_delivery import begin_delivery, plan_delivery
from app.family_calendar_delivery_config import DeliveryRecipientConfig
from app.family_calendar_delivery_message import build_family_calendar_delivery_envelope
from app.family_calendar_icloud_smtp_client import (
    ICLOUD_SMTP_HOST,
    ICLOUD_SMTP_PORT,
    ICLOUD_SMTP_TIMEOUT_SECONDS,
    ICloudSMTPClient,
    ICloudSMTPClientError,
    create_icloud_tls_context,
)
from app.family_calendar_smtp_adapter import send_family_calendar_envelope_via_smtp


ADDRESSES = (
    "one@example.invalid",
    "two@example.invalid",
    "three@example.invalid",
    "four@example.invalid",
)
RECIPIENT_IDS = ("recipient-1", "recipient-2", "recipient-3", "recipient-4")
SENDER_ADDRESS = "sender@example.invalid"
APP_PASSWORD = "private-app-password"
DEFAULT_REFUSAL_RESULT = object()


class FakeSMTPSession:
    def __init__(
        self,
        *,
        refused: object = DEFAULT_REFUSAL_RESULT,
        failure_at: str = "",
    ) -> None:
        self.refused = {} if refused is DEFAULT_REFUSAL_RESULT else refused
        self.failure_at = failure_at
        self.calls: list[object] = []
        self.exited = False
        self.message: EmailMessage | None = None
        self.from_addr = ""
        self.to_addrs: tuple[str, ...] = ()

    def __enter__(self):
        self.calls.append("enter")
        self._fail("enter")
        return self

    def __exit__(self, _exc_type, _exc, _traceback):
        self.calls.append("exit")
        self.exited = True
        return None

    def ehlo(self):
        self.calls.append("ehlo")
        self._fail("ehlo")

    def starttls(self, *, context):
        self.calls.append(("starttls", context))
        self._fail("starttls")

    def login(self, user, password):
        self.calls.append(("login", user, password))
        self._fail("login")

    def send_message(self, message, *, from_addr, to_addrs):
        self.calls.append("send_message")
        self.message = message
        self.from_addr = from_addr
        self.to_addrs = tuple(to_addrs)
        self._fail("send_message")
        return self.refused

    def _fail(self, step: str) -> None:
        if self.failure_at == step:
            raise RuntimeError(
                f"private failure for private@example.invalid using {APP_PASSWORD}"
            )


class FakeSMTPFactory:
    def __init__(self, session: FakeSMTPSession) -> None:
        self.session = session
        self.calls: list[tuple[object, ...]] = []

    def __call__(self, host, port, *, timeout):
        self.calls.append((host, port, timeout))
        return self.session


class FamilyCalendarICloudSMTPClientTests(unittest.TestCase):
    def test_tls_context_uses_certifi_ca_bundle(self) -> None:
        expected_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

        with (
            patch(
                "app.family_calendar_icloud_smtp_client.certifi.where",
                return_value="/test/certifi-ca.pem",
            ) as certifi_where,
            patch(
                "app.family_calendar_icloud_smtp_client.ssl.create_default_context",
                return_value=expected_context,
            ) as create_default_context,
        ):
            context = create_icloud_tls_context()

        self.assertIs(context, expected_context)
        certifi_where.assert_called_once_with()
        create_default_context.assert_called_once_with(cafile="/test/certifi-ca.pem")

    def test_starttls_login_and_one_shared_message_use_injected_session(self) -> None:
        session = FakeSMTPSession()
        factory = FakeSMTPFactory(session)
        tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        client = _client(factory, tls_context=tls_context)
        message = _message()

        result = client.send_message(
            message,
            from_addr=SENDER_ADDRESS,
            to_addrs=ADDRESSES,
        )

        self.assertEqual(result.refused_addresses, ())
        self.assertEqual(
            factory.calls,
            [(ICLOUD_SMTP_HOST, ICLOUD_SMTP_PORT, ICLOUD_SMTP_TIMEOUT_SECONDS)],
        )
        self.assertEqual(
            session.calls,
            [
                "enter",
                "ehlo",
                ("starttls", tls_context),
                "ehlo",
                ("login", SENDER_ADDRESS, APP_PASSWORD),
                "send_message",
                "exit",
            ],
        )
        self.assertIs(session.message, message)
        self.assertEqual(session.from_addr, SENDER_ADDRESS)
        self.assertEqual(session.to_addrs, ADDRESSES)
        self.assertTrue(session.exited)

    def test_all_partial_and_no_refusals_are_mapped_without_smtp_details(self) -> None:
        cases = {
            "all_accepted": ({}, ()),
            "partial": (
                {
                    ADDRESSES[1].upper(): (550, b"private detail"),
                    ADDRESSES[3]: (551, b"private detail"),
                },
                (ADDRESSES[1], ADDRESSES[3]),
            ),
            "all_refused": (
                {address: (550, b"private detail") for address in ADDRESSES},
                ADDRESSES,
            ),
        }
        for case, (refused, expected) in cases.items():
            with self.subTest(case=case):
                client = _client(FakeSMTPFactory(FakeSMTPSession(refused=refused)))

                result = client.send_message(
                    _message(),
                    from_addr=SENDER_ADDRESS,
                    to_addrs=ADDRESSES,
                )

                self.assertEqual(result.refused_addresses, expected)
                visible = f"{client!r} {result!r}"
                _assert_redacted(self, visible)

    def test_tls_login_and_send_failures_become_generic_and_adapter_marks_unknown(self) -> None:
        for failure_at in ("starttls", "login", "send_message"):
            with self.subTest(failure_at=failure_at):
                session = FakeSMTPSession(failure_at=failure_at)
                client = _client(FakeSMTPFactory(session))
                record, envelope = _attempt()

                outcome = send_family_calendar_envelope_via_smtp(
                    record,
                    envelope=envelope,
                    sender_address=SENDER_ADDRESS,
                    client=client,
                )

                self.assertEqual(outcome.accepted_recipient_ids, ())
                self.assertEqual(outcome.not_sent_recipient_ids, ())
                self.assertEqual(outcome.unknown_recipient_ids, RECIPIENT_IDS)
                self.assertTrue(session.exited)
                _assert_redacted(self, repr(outcome))

    def test_client_error_suppresses_private_exception_context(self) -> None:
        client = _client(FakeSMTPFactory(FakeSMTPSession(failure_at="login")))

        with self.assertRaises(ICloudSMTPClientError) as raised:
            client.send_message(
                _message(),
                from_addr=SENDER_ADDRESS,
                to_addrs=ADDRESSES,
            )

        self.assertIsNone(raised.exception.__cause__)
        self.assertIsNone(raised.exception.__context__)
        _assert_redacted(self, str(raised.exception))

    def test_invalid_or_unknown_refusal_results_fail_closed_and_stay_redacted(self) -> None:
        cases = (
            None,
            [ADDRESSES[0]],
            {"unknown@example.invalid": (550, b"private")},
            {
                ADDRESSES[0]: (550, b"private"),
                ADDRESSES[0].upper(): (550, b"private"),
            },
        )
        for refused in cases:
            with self.subTest(refused=type(refused).__name__):
                session = FakeSMTPSession(refused=refused)
                client = _client(FakeSMTPFactory(session))

                with self.assertRaises(ICloudSMTPClientError) as raised:
                    client.send_message(
                        _message(),
                        from_addr=SENDER_ADDRESS,
                        to_addrs=ADDRESSES,
                    )

                _assert_redacted(self, str(raised.exception))

    def test_invalid_credentials_sender_or_recipients_never_open_session(self) -> None:
        invalid_client_values = (
            ("private@example.invalid\r\n", APP_PASSWORD),
            (SENDER_ADDRESS, " private-password "),
        )
        for username, password in invalid_client_values:
            with self.subTest(kind="credentials"):
                factory = FakeSMTPFactory(FakeSMTPSession())
                with self.assertRaises(ICloudSMTPClientError) as raised:
                    ICloudSMTPClient(
                        username=username,
                        app_password=password,
                        smtp_factory=factory,
                    )
                self.assertEqual(factory.calls, [])
                _assert_redacted(self, str(raised.exception))

        client = _client(FakeSMTPFactory(FakeSMTPSession()))
        invalid_attempts = (
            ("other@example.invalid", ADDRESSES),
            (SENDER_ADDRESS, ADDRESSES[:3]),
            (SENDER_ADDRESS, (*ADDRESSES[:3], ADDRESSES[0].upper())),
        )
        for sender, recipients in invalid_attempts:
            with self.subTest(kind="attempt"):
                factory = FakeSMTPFactory(FakeSMTPSession())
                client = _client(factory)
                with self.assertRaises(ICloudSMTPClientError) as raised:
                    client.send_message(
                        _message(),
                        from_addr=sender,
                        to_addrs=recipients,
                    )
                self.assertEqual(factory.calls, [])
                _assert_redacted(self, str(raised.exception))


def _client(
    factory: FakeSMTPFactory,
    *,
    tls_context: ssl.SSLContext | None = None,
) -> ICloudSMTPClient:
    context = tls_context or ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    return ICloudSMTPClient(
        username=SENDER_ADDRESS,
        app_password=APP_PASSWORD,
        smtp_factory=factory,
        tls_context_factory=lambda: context,
    )


def _message() -> EmailMessage:
    message = EmailMessage()
    message["From"] = SENDER_ADDRESS
    message["To"] = ", ".join(ADDRESSES)
    message["Subject"] = "Private family reminder"
    message.set_content("Private family message")
    return message


def _attempt():
    event = FamilyEvent(
        event_key="person-example:birthday:2026-12-19",
        person_id="person-example",
        display_name="Private Alena",
        relation="private relation",
        event_type="birthday",
        event_label="narozeniny",
        event_date=date(2026, 12, 19),
        days_until=2,
        age=46,
        notification_due=True,
        catch_up=False,
    )
    envelope = build_family_calendar_delivery_envelope(
        event,
        recipients=tuple(
            DeliveryRecipientConfig(recipient_id, address)
            for recipient_id, address in zip(RECIPIENT_IDS, ADDRESSES, strict=True)
        ),
    )
    plan = plan_delivery(event_key=event.event_key, offset="D-2")
    return begin_delivery(plan, recipient_ids=RECIPIENT_IDS), envelope


def _assert_redacted(test_case: unittest.TestCase, visible: str) -> None:
    test_case.assertNotIn("@", visible)
    for private_value in (
        *ADDRESSES,
        SENDER_ADDRESS,
        APP_PASSWORD,
        "private failure",
        "Private Alena",
        "private relation",
        "Private family reminder",
        "Private family message",
    ):
        test_case.assertNotIn(private_value, visible)


if __name__ == "__main__":
    unittest.main()
