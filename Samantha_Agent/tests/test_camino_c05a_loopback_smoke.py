"""Safety and registration checks for the confirmed C05a loopback smoke."""

from __future__ import annotations

import json
import stat
import tempfile
import unittest
from pathlib import Path

from app.workflows.commands import WORKFLOW_COMMANDS
from scripts import camino_c05a_loopback_smoke as smoke


class CaminoC05aLoopbackSmokeTests(unittest.TestCase):
    def test_fixture_is_deterministic_synthetic_and_multichunk(self) -> None:
        first = smoke.synthetic_media()
        second = smoke.synthetic_media()

        self.assertEqual(first, second)
        self.assertEqual(len(first), smoke.FIXTURE_BYTES)
        self.assertGreater(len(first), smoke.CHUNK_SIZE * 4)
        self.assertEqual(smoke.digest(first), smoke.digest(second))
        self.assertNotIn(b"Miloslav", first)
        self.assertNotIn(b"Camino", first)

    def test_private_receipt_is_exclusive_and_owner_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "private"
            receipt = root / "receipt.json"
            smoke.write_private_json(receipt, {"state": "synthetic"})

            self.assertEqual(stat.S_IMODE(root.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(receipt.stat().st_mode), 0o600)
            self.assertEqual(json.loads(receipt.read_text(encoding="utf-8")), {"state": "synthetic"})
            with self.assertRaises(FileExistsError):
                smoke.write_private_json(receipt, {"state": "overwrite"})

    def test_public_summary_never_discloses_token_or_private_path(self) -> None:
        secret = "synthetic-secret-that-must-not-appear"
        receipt = {
            "state": "passed",
            "run_id": "synthetic-run",
            "byte_count": 123,
            "chunk_count": 2,
            "checks": {"one": True, "two": True},
            "token": secret,
            "private_path": "/private/tmp/hidden",
        }

        summary = smoke.public_summary(receipt)

        self.assertIn("PASS", summary)
        self.assertIn("checks=2/2", summary)
        self.assertNotIn(secret, summary)
        self.assertNotIn("/private/", summary)

    def test_registered_command_is_fixed_local_and_confirmation_gated(self) -> None:
        command = {item.command_id: item for item in WORKFLOW_COMMANDS}["camino_c05a_loopback_smoke"]

        self.assertEqual(command.argv[0], "/private/tmp/camino-c05a-venv/bin/python")
        self.assertEqual(command.argv[1:3], ("-m", "scripts.camino_c05a_loopback_smoke"))
        self.assertEqual(command.argv[3:], ("--execute",))
        self.assertTrue(command.requires_confirmation)
        self.assertEqual(command.risk, "private_local_test_write")
        self.assertIn("127.0.0.1", command.purpose)
        self.assertIn("nemění Serve, Funnel, iPhone, Git, push ani deployment", command.writes)
        self.assertNotIn("tailscale", command.exact_shell().lower())
        self.assertNotIn("serve", command.exact_shell().lower())
        self.assertNotIn("funnel", command.exact_shell().lower())


if __name__ == "__main__":
    unittest.main()
