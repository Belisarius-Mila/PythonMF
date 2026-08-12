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
        self.assertIn("Durably consented external generation capabilities:", text)
        self.assertIn(
            "generate_human_adam_image_candidate: risk=external_generation",
            text,
        )
        self.assertIn("generate_project_audio_asset: risk=external_generation", text)

    def test_agent_instructions_include_runtime_policy(self) -> None:
        agent = build_agent("TEST MEMORY")

        self.assertIn("Capability registry runtime policy:", agent.instructions)
        self.assertIn("send_confirmed_sms_rcs: risk=external_send", agent.instructions)
        self.assertIn("LOKALNI PAMET:\nTEST MEMORY", agent.instructions)

    def test_agent_instructions_prefer_live_status_over_memory_snapshot(self) -> None:
        instructions = build_agent("TEST MEMORY").instructions

        live_rule_start = instructions.index(
            "Kdyz se Mila pta na promenlivy provozni stav"
        )
        memory_rule_start = instructions.index(
            "Kdyz dotaz vyzaduje konkretni kontext"
        )
        live_rule = instructions[live_rule_start:memory_rule_start]

        self.assertLess(live_rule_start, memory_rule_start)
        self.assertIn("family_calendar_delivery_readiness", live_rule)
        self.assertIn("jeho vysledek ma prednost pred markdown pameti", live_rule)
        self.assertIn("`stáří nezjištěno`", live_rule)
        self.assertIn("stav nebyl živě\nověřen, je nejisty", live_rule)

    def test_agent_instructions_compare_current_memory_without_source_filter(self) -> None:
        agent = build_agent("TEST MEMORY")

        self.assertIn(
            "volej search_memory nejprve\nbez source_type",
            agent.instructions,
        )
        self.assertIn(
            "Pokud prvni hledani vrati relevantni `canonical` zdroj",
            agent.instructions,
        )
        self.assertIn(
            "uz search_memory nezuzuj ani neopakuj. source_type pouzij jen kdyz Mila",
            agent.instructions,
        )
        self.assertIn(
            "preferuj `canonical`;\n`aggregate_unverified` nebo `reference`",
            agent.instructions,
        )
        self.assertNotIn(
            "preferuj search_memory se\nsource_type `core`, `projects` nebo `technical`",
            agent.instructions,
        )


if __name__ == "__main__":
    unittest.main()
