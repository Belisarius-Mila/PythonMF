from __future__ import annotations

import unittest

from app.capabilities import (
    AuditPolicy,
    CapabilityRecord,
    ConfirmationPolicy,
    MobilePolicy,
    RiskLevel,
    VoicePolicy,
)


class CapabilityRecordTests(unittest.TestCase):
    def test_read_only_capability_accepts_no_confirmation(self) -> None:
        record = CapabilityRecord(
            capability_id="quick_notes_action_status",
            label="Quick Notes action inbox",
            risk=RiskLevel.READ_ONLY,
            reads=("data/private/quick_notes metadata", "selected note text"),
            writes=(),
            requires_confirmation=False,
            voice_allowed=VoicePolicy.ALLOWED,
            mobile_allowed=MobilePolicy.ALLOWED,
            audit=AuditPolicy.SAFE_SUMMARY,
            tool="quick_notes_action_status",
        )

        self.assertTrue(record.is_read_only)
        self.assertFalse(record.is_high_risk)
        self.assertEqual(record.to_dict()["risk"], "read_only")
        self.assertEqual(record.to_dict()["reads"][0], "data/private/quick_notes metadata")

    def test_external_send_requires_confirmation(self) -> None:
        with self.assertRaisesRegex(ValueError, "require confirmation"):
            CapabilityRecord(
                capability_id="send_prepared_email_draft",
                label="Send prepared email draft",
                risk=RiskLevel.EXTERNAL_SEND,
                reads=("local outbox draft",),
                writes=("SMTP send", "best-effort Sent copy"),
                requires_confirmation=False,
                audit=AuditPolicy.REDACTED,
                tool="send_prepared_email_draft",
            )

    def test_external_send_with_exact_confirmation_is_valid(self) -> None:
        record = CapabilityRecord(
            capability_id="send_prepared_email_draft",
            label="Send prepared email draft",
            risk=RiskLevel.EXTERNAL_SEND,
            reads=("local outbox draft",),
            writes=("SMTP send", "best-effort Sent copy"),
            requires_confirmation=True,
            confirmation_policy=ConfirmationPolicy.EXACT_CURRENT_MESSAGE,
            voice_allowed=VoicePolicy.APPROVAL_ONLY,
            mobile_allowed=MobilePolicy.APPROVAL_CARD,
            audit=AuditPolicy.REDACTED,
            tool="send_prepared_email_draft",
        )

        self.assertTrue(record.is_high_risk)
        self.assertEqual(record.to_dict()["confirmation_policy"], "exact_current_message")

    def test_invalid_capability_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid capability_id"):
            CapabilityRecord(
                capability_id="Send Email",
                label="Send email",
                risk=RiskLevel.READ_ONLY,
                reads=(),
                writes=(),
                tool="send_email",
            )

    def test_confirmation_policy_and_flag_must_match(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires_confirmation needs"):
            CapabilityRecord(
                capability_id="local_write_example",
                label="Local write example",
                risk=RiskLevel.LOCAL_WRITE,
                reads=(),
                writes=("local file",),
                requires_confirmation=True,
                confirmation_policy=ConfirmationPolicy.NONE,
                tool="local_write_example",
            )


if __name__ == "__main__":
    unittest.main()
