from __future__ import annotations

import io
import json
import ssl
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.family_calendar_delivery_test_email import (
    FAMILY_CALENDAR_TEST_EMAIL_CONFIRMATION,
    TEST_EMAIL_BODY,
    TEST_EMAIL_SUBJECT,
    FamilyCalendarTestEmailError,
    plan_family_calendar_test_email,
    send_family_calendar_test_email,
)
from scripts.family_calendar_delivery_test_email import main


ADDRESSES = (
    "one@example.invalid",
    "two@example.invalid",
    "three@example.invalid",
    "four@example.invalid",
)
SENDER = "sender@example.invalid"
APP_PASSWORD = "private-app-password"
DEFAULT_REFUSALS = object()


class FakeSMTPSession:
    def __init__(
        self,
        *,
        refused: object = DEFAULT_REFUSALS,
        failure_at: str = "",
    ) -> None:
        self.refused = {} if refused is DEFAULT_REFUSALS else refused
        self.failure_at = failure_at
        self.calls: list[object] = []
        self.message = None
        self.from_addr = ""
        self.to_addrs: tuple[str, ...] = ()

    def __enter__(self):
        self.calls.append("enter")
        self._fail("enter")
        return self

    def __exit__(self, _exc_type, _exc, _traceback):
        self.calls.append("exit")
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


class FamilyCalendarDeliveryTestEmailTests(unittest.TestCase):
    def test_preview_is_redacted_and_does_not_request_secret_or_open_transport(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            config_path = _config_path(Path(temp_dir))
            _write_config(config_path)
            output = io.StringIO()

            exit_code = main(
                ["--config-path", str(config_path)],
                confirmation_reader=_forbidden_reader,
                secret_reader=_forbidden_reader,
                smtp_factory=_forbidden_factory,
                output=output,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                json.loads(output.getvalue()),
                {
                    "confirmation_required": True,
                    "mode": "dry_run",
                    "recipient_count": 4,
                    "status": "preview",
                    "transport_called": False,
                },
            )
            _assert_redacted(self, output.getvalue())

    def test_exact_cli_confirmation_reads_secret_then_sends_one_shared_message(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            config_path = _config_path(Path(temp_dir))
            _write_config(config_path)
            output = io.StringIO()
            session = FakeSMTPSession()
            factory = FakeSMTPFactory(session)
            reader_calls: list[str] = []
            tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

            exit_code = main(
                ["--send", "--config-path", str(config_path)],
                confirmation_reader=lambda prompt: (
                    reader_calls.append(f"confirm:{prompt}")
                    or FAMILY_CALENDAR_TEST_EMAIL_CONFIRMATION
                ),
                secret_reader=lambda prompt: (
                    reader_calls.append(f"secret:{prompt}") or APP_PASSWORD
                ),
                smtp_factory=factory,
                tls_context_factory=lambda: tls_context,
                output=output,
            )

            documents = [json.loads(line) for line in output.getvalue().splitlines()]
            self.assertEqual(exit_code, 0)
            self.assertEqual(documents[0]["status"], "preview")
            self.assertEqual(
                documents[1],
                {
                    "accepted_count": 4,
                    "recipient_count": 4,
                    "refused_count": 0,
                    "status": "sent",
                    "transport_called": True,
                    "unknown_count": 0,
                },
            )
            self.assertEqual(
                [value.split(":", 1)[0] for value in reader_calls],
                ["confirm", "secret"],
            )
            self.assertEqual(session.calls.count("send_message"), 1)
            self.assertEqual(session.from_addr, SENDER)
            self.assertEqual(session.to_addrs, ADDRESSES)
            self.assertEqual(session.message["To"], ", ".join(ADDRESSES))
            self.assertEqual(session.message["Subject"], TEST_EMAIL_SUBJECT)
            self.assertEqual(session.message.get_content(), TEST_EMAIL_BODY)
            _assert_redacted(self, output.getvalue())

    def test_wrong_confirmation_never_reads_secret_or_opens_transport(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            config_path = _config_path(Path(temp_dir))
            _write_config(config_path)
            output = io.StringIO()

            exit_code = main(
                ["--send", "--config-path", str(config_path)],
                confirmation_reader=lambda _prompt: "SEND",
                secret_reader=_forbidden_reader,
                smtp_factory=_forbidden_factory,
                output=output,
            )

            documents = [json.loads(line) for line in output.getvalue().splitlines()]
            self.assertEqual(exit_code, 1)
            self.assertEqual(
                documents[-1],
                {
                    "failure_stage": "confirmation",
                    "redacted": True,
                    "status": "failed",
                },
            )
            _assert_redacted(self, output.getvalue())

    def test_config_change_after_preview_prevents_secret_read_and_transport(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            config_path = _config_path(Path(temp_dir))
            _write_config(config_path)
            output = io.StringIO()

            def change_config_then_confirm(_prompt: str) -> str:
                _write_config(
                    config_path,
                    addresses=(
                        "changed@example.invalid",
                        ADDRESSES[1],
                        ADDRESSES[2],
                        ADDRESSES[3],
                    ),
                )
                return FAMILY_CALENDAR_TEST_EMAIL_CONFIRMATION

            exit_code = main(
                ["--send", "--config-path", str(config_path)],
                confirmation_reader=change_config_then_confirm,
                secret_reader=_forbidden_reader,
                smtp_factory=_forbidden_factory,
                output=output,
            )

            documents = [json.loads(line) for line in output.getvalue().splitlines()]
            self.assertEqual(exit_code, 1)
            self.assertEqual(
                documents[-1],
                {
                    "failure_stage": "configuration_recheck",
                    "redacted": True,
                    "status": "failed",
                },
            )
            _assert_redacted(self, output.getvalue())

    def test_failed_cli_stages_remain_redacted_and_never_open_transport(self) -> None:
        cases = (
            ("confirmation_input", lambda _prompt: (_ for _ in ()).throw(EOFError()), _forbidden_reader),
            (
                "credential_input",
                lambda _prompt: FAMILY_CALENDAR_TEST_EMAIL_CONFIRMATION,
                lambda _prompt: (_ for _ in ()).throw(EOFError()),
            ),
            (
                "pre_transport_validation",
                lambda _prompt: FAMILY_CALENDAR_TEST_EMAIL_CONFIRMATION,
                lambda _prompt: " private-password ",
            ),
        )
        for expected_stage, confirmation_reader, secret_reader in cases:
            with self.subTest(stage=expected_stage):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    config_path = _config_path(Path(temp_dir))
                    _write_config(config_path)
                    output = io.StringIO()

                    exit_code = main(
                        ["--send", "--config-path", str(config_path)],
                        confirmation_reader=confirmation_reader,
                        secret_reader=secret_reader,
                        smtp_factory=_forbidden_factory,
                        output=output,
                    )

                    documents = [
                        json.loads(line) for line in output.getvalue().splitlines()
                    ]
                    self.assertEqual(exit_code, 1)
                    self.assertEqual(
                        documents[-1],
                        {
                            "failure_stage": expected_stage,
                            "redacted": True,
                            "status": "failed",
                        },
                    )
                    _assert_redacted(self, output.getvalue())

    def test_preview_failure_has_redacted_stage_without_prompting(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            config_path = _config_path(Path(temp_dir))
            _write_config(config_path, mode="disabled")
            output = io.StringIO()

            exit_code = main(
                ["--send", "--config-path", str(config_path)],
                confirmation_reader=_forbidden_reader,
                secret_reader=_forbidden_reader,
                smtp_factory=_forbidden_factory,
                output=output,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(
                json.loads(output.getvalue()),
                {
                    "failure_stage": "preview",
                    "redacted": True,
                    "status": "failed",
                },
            )
            _assert_redacted(self, output.getvalue())

    def test_accepted_partial_refused_and_unknown_results_are_counted_only(self) -> None:
        cases = {
            "sent": ({}, (4, 0, 0)),
            "partial": (
                {
                    ADDRESSES[1]: (550, b"private detail"),
                    ADDRESSES[3]: (551, b"private detail"),
                },
                (2, 2, 0),
            ),
            "refused": (
                {address: (550, b"private detail") for address in ADDRESSES},
                (0, 4, 0),
            ),
            "delivery_unknown": ("failure", (0, 0, 4)),
        }
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            config_path = _config_path(Path(temp_dir))
            _write_config(config_path)
            plan = plan_family_calendar_test_email(config_path=config_path)
            for status, (refused, counts) in cases.items():
                with self.subTest(status=status):
                    session = (
                        FakeSMTPSession(failure_at="send_message")
                        if refused == "failure"
                        else FakeSMTPSession(refused=refused)
                    )
                    result = send_family_calendar_test_email(
                        plan,
                        confirmation=FAMILY_CALENDAR_TEST_EMAIL_CONFIRMATION,
                        app_password=APP_PASSWORD,
                        smtp_factory=FakeSMTPFactory(session),
                        tls_context_factory=_tls_context,
                    )

                    self.assertEqual(result.status, status)
                    self.assertEqual(
                        (
                            result.accepted_count,
                            result.refused_count,
                            result.unknown_count,
                        ),
                        counts,
                    )
                    self.assertTrue(result.transport_called)
                    _assert_redacted(self, f"{result!r} {result.safe_document()!r}")

    def test_changed_config_or_invalid_secret_fails_before_smtp_factory(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            config_path = _config_path(Path(temp_dir))
            _write_config(config_path)
            plan = plan_family_calendar_test_email(config_path=config_path)
            _write_config(
                config_path,
                addresses=(
                    "changed@example.invalid",
                    ADDRESSES[1],
                    ADDRESSES[2],
                    ADDRESSES[3],
                ),
            )
            factory = FakeSMTPFactory(FakeSMTPSession())

            with self.assertRaises(FamilyCalendarTestEmailError):
                send_family_calendar_test_email(
                    plan,
                    confirmation=FAMILY_CALENDAR_TEST_EMAIL_CONFIRMATION,
                    app_password=APP_PASSWORD,
                    smtp_factory=factory,
                )
            self.assertEqual(factory.calls, [])

            _write_config(config_path)
            plan = plan_family_calendar_test_email(config_path=config_path)
            with self.assertRaises(FamilyCalendarTestEmailError):
                send_family_calendar_test_email(
                    plan,
                    confirmation=FAMILY_CALENDAR_TEST_EMAIL_CONFIRMATION,
                    app_password=" private-password ",
                    smtp_factory=factory,
                )
            self.assertEqual(factory.calls, [])

    def test_plan_rejects_non_dry_run_non_icloud_and_untrusted_config(self) -> None:
        cases = (
            ("disabled", "icloud"),
            ("dry_run", "seznam"),
            ("dry_run", "icloud"),
        )
        for mode, provider in cases:
            with self.subTest(mode=mode, provider=provider):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    config_path = _config_path(Path(temp_dir))
                    _write_config(config_path, mode=mode, provider=provider)
                    if mode == "dry_run" and provider == "icloud":
                        config_path.chmod(0o644)

                    with self.assertRaises(FamilyCalendarTestEmailError) as raised:
                        plan_family_calendar_test_email(config_path=config_path)

                    _assert_redacted(self, str(raised.exception))

    def test_default_runtime_factory_is_smtplib_smtp_but_is_patchable_without_network(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            config_path = _config_path(Path(temp_dir))
            _write_config(config_path)
            plan = plan_family_calendar_test_email(config_path=config_path)
            session = FakeSMTPSession()
            factory = FakeSMTPFactory(session)
            tls_context = _tls_context()

            with (
                patch(
                    "app.family_calendar_delivery_test_email.smtplib.SMTP",
                    factory,
                ),
                patch(
                    "app.family_calendar_delivery_test_email.create_icloud_tls_context",
                    return_value=tls_context,
                ) as tls_factory,
            ):
                result = send_family_calendar_test_email(
                    plan,
                    confirmation=FAMILY_CALENDAR_TEST_EMAIL_CONFIRMATION,
                    app_password=APP_PASSWORD,
                )

            self.assertEqual(result.status, "sent")
            tls_factory.assert_called_once_with()
            self.assertEqual(len(factory.calls), 1)
            self.assertIn(("starttls", tls_context), session.calls)
            self.assertEqual(session.calls.count("send_message"), 1)


def _config_path(root: Path) -> Path:
    return root / "family" / "notification_config.json"


def _write_config(
    path: Path,
    *,
    mode: str = "dry_run",
    provider: str = "icloud",
    addresses: tuple[str, str, str, str] = ADDRESSES,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.parent.chmod(0o700)
    path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "mode": mode,
                "smtp_provider": provider,
                "sender_address": SENDER,
                "recipients": [
                    {
                        "recipient_id": f"recipient-{index}",
                        "address": address,
                    }
                    for index, address in enumerate(addresses, start=1)
                ],
            },
        ),
        encoding="utf-8",
    )
    path.chmod(0o600)


def _tls_context() -> ssl.SSLContext:
    return ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)


def _forbidden_reader(_prompt: str) -> str:
    raise AssertionError("No interactive input was expected.")


def _forbidden_factory(*_args, **_kwargs):
    raise AssertionError("SMTP transport was not expected.")


def _assert_redacted(test_case: unittest.TestCase, visible: str) -> None:
    test_case.assertNotIn("@", visible)
    for private_value in (
        *ADDRESSES,
        SENDER,
        APP_PASSWORD,
        "private failure",
        "private detail",
        TEST_EMAIL_SUBJECT,
        TEST_EMAIL_BODY.strip(),
    ):
        test_case.assertNotIn(private_value, visible)


if __name__ == "__main__":
    unittest.main()
