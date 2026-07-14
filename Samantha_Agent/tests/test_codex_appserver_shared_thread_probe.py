from __future__ import annotations

import unittest
from pathlib import Path

from scripts.codex_appserver_shared_thread_probe import (
    SharedThreadEvidence,
    SharedThreadProbeError,
    unix_server_command,
)


class SharedThreadProbeTests(unittest.TestCase):
    def test_unix_server_command_is_local_and_shell_free(self) -> None:
        self.assertEqual(
            unix_server_command(codex_binary="codex", socket_path=Path("/tmp/samantha.sock")),
            ["codex", "app-server", "--listen", "unix:///tmp/samantha.sock"],
        )
        with self.assertRaises(SharedThreadProbeError):
            unix_server_command(codex_binary="codex", socket_path=Path("relative.sock"))

    def test_evidence_requires_two_clients_and_same_resumed_thread(self) -> None:
        good = SharedThreadEvidence(
            server_process_id=100,
            first_connection_id="connection-1",
            second_connection_id="connection-2",
            thread_id="thread-1",
            resumed_thread_id="thread-1",
            first_turn_id="turn-1",
            second_turn_id="turn-2",
            first_reply_exact=True,
            context_reply_exact=True,
            first_delivery_confirmed=True,
            second_delivery_confirmed=True,
            archived_after_probe=True,
        )
        self.assertTrue(good.passed)
        self.assertFalse(
            SharedThreadEvidence(
                **(good.__dict__ | {"resumed_thread_id": "thread-2"})
            ).passed
        )
        self.assertFalse(
            SharedThreadEvidence(
                **(good.__dict__ | {"second_connection_id": "connection-1"})
            ).passed
        )


if __name__ == "__main__":
    unittest.main()
