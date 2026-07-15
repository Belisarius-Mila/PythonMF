from __future__ import annotations

import unittest
from pathlib import Path

from app.codex_appserver import (
    AppServerContractError,
    CodexVersion,
    TurnReceipt,
    UnixSocketAppServerTransport,
    codex_environment,
)


class CodexContractTests(unittest.TestCase):
    def test_version_parser_is_strict(self) -> None:
        version = CodexVersion.parse("codex-cli 0.144.1")
        self.assertEqual((version.major, version.minor, version.patch), (0, 144, 1))
        with self.assertRaises(AppServerContractError):
            CodexVersion.parse("unknown")

    def test_receipt_requires_exactly_one_user_item_and_started_event(self) -> None:
        base = dict(
            client_message_id="appserver-client-12345678",
            thread_id="thread",
            turn_id="turn",
            requested_at="a",
            accepted_at="b",
            started_at="c",
            completed_at="d",
            status="completed",
            answer="ano",
            turn_started_confirmed=True,
            duration_ms=1,
        )
        self.assertTrue(TurnReceipt(user_item_count=1, **base).delivered)
        self.assertFalse(TurnReceipt(user_item_count=2, **base).delivered)
        self.assertFalse(TurnReceipt(user_item_count=1, **(base | {"turn_started_confirmed": False})).delivered)

    def test_codex_environment_adds_service_runtime_paths(self) -> None:
        env = codex_environment({"PATH": "/custom/bin", "HOME": "/tmp/home"})
        parts = env["PATH"].split(":")
        self.assertEqual(parts[0], "/usr/local/bin")
        self.assertIn("/usr/bin", parts)
        self.assertIn("/custom/bin", parts)
        self.assertEqual(env["HOME"], "/tmp/home")

    def test_unix_transport_rejects_relative_socket_before_connecting(self) -> None:
        with self.assertRaises(AppServerContractError):
            UnixSocketAppServerTransport(socket_path=Path("relative.sock"))


if __name__ == "__main__":
    unittest.main()
