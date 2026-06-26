from __future__ import annotations

import unittest

from app.capabilities.runtime_policy import format_runtime_capability_policy
from app.samantha_agent import build_agent


class CapabilityRuntimePolicyTests(unittest.TestCase):
    def test_runtime_policy_lists_confirmed_capabilities_only(self) -> None:
        text = format_runtime_capability_policy()

        self.assertIn("Capability registry runtime policy:", text)
        self.assertIn("send_prepared_email_draft: risk=external_send", text)
        self.assertIn("read_email_body_by_uid: risk=private_export", text)
        self.assertIn("confirmation=exact_current_message", text)
        self.assertNotIn("list_recent_email_headers: risk=read_only", text)

    def test_agent_instructions_include_runtime_policy(self) -> None:
        agent = build_agent("TEST MEMORY")

        self.assertIn("Capability registry runtime policy:", agent.instructions)
        self.assertIn("send_confirmed_sms_rcs: risk=external_send", agent.instructions)
        self.assertIn("LOKALNI PAMET:\nTEST MEMORY", agent.instructions)


if __name__ == "__main__":
    unittest.main()
