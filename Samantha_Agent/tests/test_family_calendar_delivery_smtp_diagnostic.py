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
    ICloudSMTPDiagnosticCategory,
)
from scripts.family_calendar_delivery_smtp_diagnose import main


ADDRESSES = (
    "one@example.invalid",
    "two@example.invalid",
    "three@example.invalid",
    "four@example.invalid",
)
SENDER = "sender@example.invalid"
APP_PASSWORD = "private-app-password"


class FakeSMTPSession:
    def __init__(self, *, failure_at: str = "") -> None:
        self.failure_at = failure_at
        self.calls: list[object] = []
        self.ehlo_count = 0

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

    def send_message(self, *_args, **_kwargs):
        raise AssertionError("Diagnostic must never call send_message.")

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


class FamilyCalendarDeliverySMTPDiagnosticTests(unittest.TestCase):
    def test_success_checks_authentication_and_never_sends_message(self) -> None:
        session = FakeSMTPSession()
        factory = FakeSMTPFactory(session)
        tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        client = _client(factory, tls_context_factory=lambda: tls_context)

        result = client.diagnose_authentication()

        self.assertEqual(
            result.category,
            ICloudSMTPDiagnosticCategory.AUTH_OK_NO_SEND,
        )
        self.assertTrue(result.succeeded)
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
                "exit",
            ],
        )
        self.assertEqual(
            result.safe_document(),
            {
                "category": "AUTH_OK_NO_SEND",
                "redacted": True,
                "send_called": False,
                "status": "diagnostic",
            },
        )
        _assert_redacted(self, f"{result!r} {result.safe_document()!r}")

    def test_failures_are_classified_by_stage_without_private_details(self) -> None:
        cases = (
            ("factory", ICloudSMTPDiagnosticCategory.CONNECTION_FAILED),
            ("enter", ICloudSMTPDiagnosticCategory.CONNECTION_FAILED),
            ("ehlo_1", ICloudSMTPDiagnosticCategory.CONNECTION_FAILED),
            ("starttls", ICloudSMTPDiagnosticCategory.STARTTLS_FAILED),
            ("ehlo_2", ICloudSMTPDiagnosticCategory.POST_TLS_EHLO_FAILED),
            ("login", ICloudSMTPDiagnosticCategory.AUTHENTICATION_FAILED),
            ("exit", ICloudSMTPDiagnosticCategory.OTHER_REDACTED),
        )
        for failure_at, expected in cases:
            with self.subTest(failure_at=failure_at):
                session = FakeSMTPSession(failure_at=failure_at)
                factory = FakeSMTPFactory(session, fail=failure_at == "factory")
                client = _client(factory)

                result = client.diagnose_authentication()

                self.assertEqual(result.category, expected)
                self.assertFalse(result.succeeded)
                _assert_redacted(self, f"{result!r} {result.safe_document()!r}")

    def test_tls_context_failure_is_redacted_as_tls_stage(self) -> None:
        factory = FakeSMTPFactory(FakeSMTPSession())
        client = _client(
            factory,
            tls_context_factory=lambda: _raise_private_failure(),
        )

        result = client.diagnose_authentication()

        self.assertEqual(
            result.category,
            ICloudSMTPDiagnosticCategory.TLS_CONTEXT_FAILED,
        )
        self.assertEqual(factory.calls, [])
        _assert_redacted(self, repr(result))

    def test_cli_success_reads_hidden_secret_and_reports_no_send(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            config_path = _write_config(Path(temp_dir))
            session = FakeSMTPSession()
            factory = FakeSMTPFactory(session)
            output = io.StringIO()
            prompts: list[str] = []
            tls_context = _tls_context()

            with patch(
                "scripts.family_calendar_delivery_smtp_diagnose.create_icloud_tls_context",
                return_value=tls_context,
            ) as tls_factory:
                exit_code = main(
                    ["--config-path", str(config_path)],
                    secret_reader=lambda prompt: prompts.append(prompt) or APP_PASSWORD,
                    smtp_factory=factory,
                    output=output,
                )

            self.assertEqual(exit_code, 0)
            tls_factory.assert_called_once_with()
            self.assertEqual(len(prompts), 1)
            self.assertIn("skrytě", prompts[0])
            self.assertEqual(
                json.loads(output.getvalue()),
                {
                    "category": "AUTH_OK_NO_SEND",
                    "redacted": True,
                    "send_called": False,
                    "status": "diagnostic",
                },
            )
            self.assertIn(("starttls", tls_context), session.calls)
            self.assertNotIn("send_message", session.calls)
            _assert_redacted(self, output.getvalue())

    def test_cli_preconnection_failures_do_not_open_smtp(self) -> None:
        cases = (
            (
                "CONFIGURATION_FAILED",
                False,
                lambda _prompt: APP_PASSWORD,
                "disabled",
            ),
            (
                "CREDENTIAL_INPUT_FAILED",
                True,
                lambda _prompt: (_ for _ in ()).throw(EOFError()),
                "dry_run",
            ),
            (
                "CREDENTIAL_VALIDATION_FAILED",
                True,
                lambda _prompt: " private-password ",
                "dry_run",
            ),
        )
        for expected, expects_prompt, secret_reader, mode in cases:
            with self.subTest(category=expected):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    config_path = _write_config(Path(temp_dir), mode=mode)
                    factory = FakeSMTPFactory(FakeSMTPSession())
                    output = io.StringIO()
                    prompt_count = 0

                    def read_secret(prompt: str) -> str:
                        nonlocal prompt_count
                        prompt_count += 1
                        return secret_reader(prompt)

                    exit_code = main(
                        ["--config-path", str(config_path)],
                        secret_reader=read_secret,
                        smtp_factory=factory,
                        tls_context_factory=_tls_context,
                        output=output,
                    )

                    self.assertEqual(exit_code, 1)
                    self.assertEqual(prompt_count, int(expects_prompt))
                    self.assertEqual(factory.calls, [])
                    self.assertEqual(
                        json.loads(output.getvalue()),
                        {
                            "category": expected,
                            "redacted": True,
                            "send_called": False,
                            "status": "diagnostic",
                        },
                    )
                    _assert_redacted(self, output.getvalue())

    def test_cli_transport_failure_returns_only_redacted_stage(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            config_path = _write_config(Path(temp_dir))
            session = FakeSMTPSession(failure_at="login")
            output = io.StringIO()

            exit_code = main(
                ["--config-path", str(config_path)],
                secret_reader=lambda _prompt: APP_PASSWORD,
                smtp_factory=FakeSMTPFactory(session),
                tls_context_factory=_tls_context,
                output=output,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(
                json.loads(output.getvalue()),
                {
                    "category": "AUTHENTICATION_FAILED",
                    "redacted": True,
                    "send_called": False,
                    "status": "diagnostic",
                },
            )
            self.assertNotIn("send_message", session.calls)
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


def _raise_private_failure():
    raise RuntimeError(
        f"private failure for private@example.invalid using {APP_PASSWORD}"
    )


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
    ):
        test_case.assertNotIn(private_value, visible)


if __name__ == "__main__":
    unittest.main()
