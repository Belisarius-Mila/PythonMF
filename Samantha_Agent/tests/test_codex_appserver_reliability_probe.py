import unittest
from pathlib import Path

from scripts.codex_appserver_reliability_probe import (
    DeliveryEvidence,
    ProbeError,
    _item_from_notification,
    run_probe,
)


class DeliveryEvidenceTests(unittest.TestCase):
    def test_passed_requires_all_protocol_evidence(self):
        evidence = DeliveryEvidence(
            sequence=1,
            client_message_id="message-1",
            thread_id="thread-1",
            turn_id="turn-1",
            user_item_confirmed=True,
            turn_status="completed",
            exact_reply_confirmed=True,
            duplicate_user_items=0,
            duration_ms=10,
        )

        self.assertTrue(evidence.passed)

    def test_duplicate_delivery_fails(self):
        evidence = DeliveryEvidence(
            sequence=1,
            client_message_id="message-1",
            thread_id="thread-1",
            turn_id="turn-1",
            user_item_confirmed=True,
            turn_status="completed",
            exact_reply_confirmed=True,
            duplicate_user_items=1,
            duration_ms=10,
        )

        self.assertFalse(evidence.passed)

    def test_extracts_only_object_item(self):
        self.assertEqual(
            _item_from_notification({"params": {"item": {"type": "userMessage"}}}),
            {"type": "userMessage"},
        )
        self.assertIsNone(_item_from_notification({"params": {"item": "bad"}}))
        self.assertIsNone(_item_from_notification({}))

    def test_rejects_invalid_restart_boundary_before_starting_server(self):
        with self.assertRaisesRegex(ProbeError, "restart-after"):
            run_probe(
                count=1,
                timeout=1,
                codex_binary="unused",
                workdir=Path("/tmp"),
                restart_after=1,
            )


if __name__ == "__main__":
    unittest.main()
