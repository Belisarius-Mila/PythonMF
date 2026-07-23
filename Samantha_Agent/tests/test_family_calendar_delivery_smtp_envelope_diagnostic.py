from __future__ import annotations

import io
import json
import ssl
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.family_calendar_icloud_smtp_client import (
    ICLOUD_SMTP_HOST,
    ICLOUD_SMTP_PORT,
    ICLOUD_SMTP_TIMEOUT_SECONDS,
    ICloudSMTPClient,
    ICloudSMTPClientError,
    ICloudSMTPDiagnosticCategory,
)
from scripts.family_calendar_delivery_smtp_envelope_diagnose import main


ADDRESSES = (
    "one@example.invalid",
    "two@example.invalid",
    "three@example.invalid",
    "four@example.invalid",
)
SENDER = "sender@example.invalid"
APP_PASSWORD = "private-app-password"


class FakeSMTPSession:
    def __init__(
        self,
        *,
        mail_code: int = 250,
        rcpt_codes: tuple[int, ...] = (250, 250, 250, 250),
        rset_code: int = 250,
        failure_at: str = "",
    ) -> None:
        self.mail_code = mail_code
        self.rcpt_codes = rcpt_codes
        self.rset_code = rset_code
        self.failure_at = failure_at
        self.calls: list[object] = []
        self.ehlo_count = 0
        self.rcpt_count = 0

    def __enter__(self):
        self.calls.append("enter")
        self._fail("enter")
        return self

    def __exit__(self, _exc_type, _exc, _traceback):
        self.calls.append("exit")
        self._fail("exit")
        return None

    def ehlo(self):
        self.ehlo_count += 1
        step = f"ehlo_{self.ehlo_count}"
        self.calls.append(step)
        self._fail(step)

    def starttls(self, *, context):
        self.calls.append(("starttls", context))
        self._fail("starttls")

    def login(self, user, password):
        self.calls.append(("login", user, password))
        self._fail("login")

    def mail(self, sender):
        self.calls.append(("mail", sender))
        self._fail("mail")
        return self.mail_code, b"private mail reply"

    def rcpt(self, recipient):
        self.rcpt_count += 1
        step = f"rcpt_{self.rcpt_count}"
        self.calls.append(("rcpt", recipient))
        self._fail(step)
        return self.rcpt_codes[self.rcpt_count - 1], b"private rcpt reply"

    def rset(self):
        self.calls.append("rset")
        self._fail("rset")
        return self.rset_code, b"private rset reply"

    def data(self, *_args, **_kwargs):
        raise AssertionError("Envelope diagnostic must never call DATA.")

    def send_message(self, *_args, **_kwargs):
        raise AssertionError("Envelope diagnostic must never call send_message.")

    def _fail(self, step: str) -> None:
        if self.failure_at == step:
            raise RuntimeError(
                f"private failure for private@example.invalid using {APP_PASSWORD}"
            )


class FakeSMTPFactory:
    def __init__(self, session: FakeSMTPSession, *, fail: bool = False) -> None:
        self.session = session
        self.fail = fail
        self.calls: list[tuple[object, ...]] = []

    def __call__(self, host, port, *, timeout):
        self.calls.append((host, port, timeout))
        if self.fail:
            raise RuntimeError(
                f"private failure for private@example.invalid using {APP_PASSWORD}"
            )
        return self.session


class FamilyCalendarDeliverySMTPEnvelopeDiagnosticTests(unittest.TestCase):
    def test_success_checks_four_recipients_then_rsets_without_data(self) -> None:
        session = FakeSMTPSession()
        factory = FakeSMTPFactory(session)
        tls_context = _tls_context()
        client = _client(factory, tls_context_factory=lambda: tls_context)

        result = client.diagnose_envelope(
            from_addr=SENDER,
            to_addrs=ADDRESSES,
        )

        self.assertTrue(result.succeeded)
        self.assertEqual(
            result.category,
            ICloudSMTPDiagnosticCategory.ENVELOPE_OK_NO_DATA_NO_SEND,
        )
        self.assertEqual(
            factory.calls,
            [(ICLOUD_SMTP_HOST, ICLOUD_SMTP_PORT, ICLOUD_SMTP_TIMEOUT_SECONDS)],
        )
        self.assertEqual(
            session.calls,
            [
                "enter",
                "ehlo_1",
                ("starttls", tls_context),
                "ehlo_2",
                ("login", SENDER, APP_PASSWORD),
                ("mail", SENDER),
                *[("rcpt", address) for address in ADDRESSES],
                "rset",
                "exit",
            ],
        )
        self.assertEqual(
            result.safe_document(),
            {
                "accepted_recipient_count": 4,
                "category": "ENVELOPE_OK_NO_DATA_NO_SEND",
                "data_called": False,
                "recipient_count": 4,
                "redacted": True,
                "rejected_recipient_count": 0,
                "rset_ok": True,
                "send_called": False,
                "session_close_ok": True,
                "status": "diagnostic",
                "unknown_recipient_count": 0,
            },
        )
        _assert_redacted(self, f"{result!r} {result.safe_document()!r}")

    def test_mail_rejection_skips_recipients_and_still_rsets(self) -> None:
        session = FakeSMTPSession(mail_code=550)
        result = _client(FakeSMTPFactory(session)).diagnose_envelope(
            from_addr=SENDER,
            to_addrs=ADDRESSES,
        )

        self.assertEqual(
            result.category,
            ICloudSMTPDiagnosticCategory.MAIL_FROM_REJECTED,
        )
        self.assertEqual(result.accepted_recipient_count, 0)
        self.assertEqual(result.rejected_recipient_count, 0)
        self.assertEqual(result.unknown_recipient_count, 4)
        self.assertEqual(
            [call for call in session.calls if isinstance(call, tuple) and call[0] == "rcpt"],
            [],
        )
        self.assertIn("rset", session.calls)
        _assert_redacted(self, repr(result))

    def test_all_recipients_are_checked_and_rejections_are_counted_only(self) -> None:
        session = FakeSMTPSession(rcpt_codes=(250, 550, 251, 551))
        result = _client(FakeSMTPFactory(session)).diagnose_envelope(
            from_addr=SENDER,
            to_addrs=ADDRESSES,
        )

        self.assertEqual(
            result.category,
            ICloudSMTPDiagnosticCategory.RECIPIENTS_REJECTED,
        )
        self.assertEqual(result.accepted_recipient_count, 2)
        self.assertEqual(result.rejected_recipient_count, 2)
        self.assertEqual(result.unknown_recipient_count, 0)
        self.assertEqual(session.rcpt_count, 4)
        self.assertTrue(result.rset_ok)
        _assert_redacted(self, f"{result!r} {result.safe_document()!r}")

    def test_rset_and_session_close_failures_are_distinct_and_never_send(self) -> None:
        cases = (
            (
                FakeSMTPSession(rset_code=500),
                ICloudSMTPDiagnosticCategory.RSET_FAILED_NO_DATA_NO_SEND,
                False,
                True,
            ),
            (
                FakeSMTPSession(failure_at="exit"),
                ICloudSMTPDiagnosticCategory.SESSION_CLOSE_FAILED_NO_DATA_NO_SEND,
                True,
                False,
            ),
        )
        for session, expected, expected_rset, expected_close in cases:
            with self.subTest(category=expected.value):
                result = _client(FakeSMTPFactory(session)).diagnose_envelope(
                    from_addr=SENDER,
                    to_addrs=ADDRESSES,
                )

                self.assertEqual(result.category, expected)
                self.assertEqual(result.rset_ok, expected_rset)
                self.assertEqual(result.session_close_ok, expected_close)
                self.assertEqual(result.accepted_recipient_count, 4)
                _assert_redacted(self, f"{result!r} {result.safe_document()!r}")

    def test_auth_or_envelope_exception_stays_redacted_and_never_calls_data(self) -> None:
        cases = (
            (
                "login",
                ICloudSMTPDiagnosticCategory.AUTHENTICATION_FAILED,
                4,
            ),
            (
                "rcpt_2",
                ICloudSMTPDiagnosticCategory.OTHER_REDACTED,
                3,
            ),
        )
        for failure_at, expected, unknown_count in cases:
            with self.subTest(failure_at=failure_at):
                session = FakeSMTPSession(failure_at=failure_at)
                result = _client(FakeSMTPFactory(session)).diagnose_envelope(
                    from_addr=SENDER,
                    to_addrs=ADDRESSES,
                )

                self.assertEqual(result.category, expected)
                self.assertEqual(result.unknown_recipient_count, unknown_count)
                self.assertNotIn("data", session.calls)
                self.assertNotIn("send_message", session.calls)
                _assert_redacted(self, f"{result!r} {result.safe_document()!r}")

    def test_invalid_envelope_never_opens_smtp(self) -> None:
        invalid_attempts = (
            ("other@example.invalid", ADDRESSES),
            (SENDER, ADDRESSES[:3]),
            (SENDER, (*ADDRESSES[:3], ADDRESSES[0].upper())),
        )
        for sender, recipients in invalid_attempts:
            with self.subTest(sender_matches=sender == SENDER, count=len(recipients)):
                factory = FakeSMTPFactory(FakeSMTPSession())
                client = _client(factory)

                with self.assertRaises(ICloudSMTPClientError) as raised:
                    client.diagnose_envelope(
                        from_addr=sender,
                        to_addrs=recipients,
                    )

                self.assertEqual(factory.calls, [])
                _assert_redacted(self, str(raised.exception))

    def test_cli_success_uses_certifi_factory_and_outputs_counts_only(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            config_path = _write_config(Path(temp_dir))
            session = FakeSMTPSession()
            factory = FakeSMTPFactory(session)
            output = io.StringIO()
            tls_context = _tls_context()

            with patch(
                "scripts.family_calendar_delivery_smtp_envelope_diagnose.create_icloud_tls_context",
                return_value=tls_context,
            ) as tls_factory:
                exit_code = main(
                    ["--config-path", str(config_path)],
                    secret_reader=lambda _prompt: APP_PASSWORD,
                    smtp_factory=factory,
                    output=output,
                )

            self.assertEqual(exit_code, 0)
            tls_factory.assert_called_once_with()
            document = json.loads(output.getvalue())
            self.assertEqual(document["category"], "ENVELOPE_OK_NO_DATA_NO_SEND")
            self.assertEqual(document["accepted_recipient_count"], 4)
            self.assertFalse(document["data_called"])
            self.assertFalse(document["send_called"])
            self.assertIn("rset", session.calls)
            _assert_redacted(self, output.getvalue())

    def test_cli_preconnection_failures_do_not_open_smtp(self) -> None:
        cases = (
            (
                "CONFIGURATION_FAILED",
                "disabled",
                lambda _prompt: APP_PASSWORD,
            ),
            (
                "CREDENTIAL_INPUT_FAILED",
                "dry_run",
                lambda _prompt: (_ for _ in ()).throw(EOFError()),
            ),
            (
                "CREDENTIAL_VALIDATION_FAILED",
                "dry_run",
                lambda _prompt: " private-password ",
            ),
        )
        for expected, mode, secret_reader in cases:
            with self.subTest(category=expected):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    config_path = _write_config(Path(temp_dir), mode=mode)
                    factory = FakeSMTPFactory(FakeSMTPSession())
                    output = io.StringIO()

                    exit_code = main(
                        ["--config-path", str(config_path)],
                        secret_reader=secret_reader,
                        smtp_factory=factory,
                        tls_context_factory=_tls_context,
                        output=output,
                    )

                    self.assertEqual(exit_code, 1)
                    self.assertEqual(factory.calls, [])
                    document = json.loads(output.getvalue())
                    self.assertEqual(document["category"], expected)
                    self.assertFalse(document["data_called"])
                    self.assertFalse(document["send_called"])
                    self.assertEqual(document["unknown_recipient_count"], 4)
                    _assert_redacted(self, output.getvalue())


def _client(
    factory: FakeSMTPFactory,
    *,
    tls_context_factory=None,
) -> ICloudSMTPClient:
    return ICloudSMTPClient(
        username=SENDER,
        app_password=APP_PASSWORD,
        smtp_factory=factory,
        tls_context_factory=tls_context_factory or _tls_context,
    )


def _tls_context() -> ssl.SSLContext:
    return ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)


def _write_config(root: Path, *, mode: str = "dry_run") -> Path:
    config_path = root / "family" / "notification_config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    config_path.parent.chmod(0o700)
    config_path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "mode": mode,
                "smtp_provider": "icloud",
                "sender_address": SENDER,
                "recipients": [
                    {
                        "recipient_id": f"recipient-{index}",
                        "address": address,
                    }
                    for index, address in enumerate(ADDRESSES, start=1)
                ],
            }
        ),
        encoding="utf-8",
    )
    config_path.chmod(0o600)
    return config_path


def _assert_redacted(test_case: unittest.TestCase, visible: str) -> None:
    test_case.assertNotIn("@", visible)
    for private_value in (
        *ADDRESSES,
        SENDER,
        APP_PASSWORD,
        "private failure",
        "private mail reply",
        "private rcpt reply",
        "private rset reply",
    ):
        test_case.assertNotIn(private_value, visible)


if __name__ == "__main__":
    unittest.main()
