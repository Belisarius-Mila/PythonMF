from __future__ import annotations

import unittest

from app.communication.human_adam_turn_completion import (
    automatic_completion_instruction,
    parse_turn_completion,
)


class HumanAdamTurnCompletionTests(unittest.TestCase):
    def test_read_only_turn_gets_no_completion_protocol(self) -> None:
        self.assertEqual(automatic_completion_instruction(writable=False), "")
        instruction = automatic_completion_instruction(writable=True)
        self.assertIn("[HUMAN_ADAM_STEP_COMPLETION]", instruction)
        self.assertIn("final current state", instruction)
        self.assertIn(
            "transient test failure that you fixed and reran successfully",
            instruction,
        )
        self.assertIn("final required tests still fail", instruction)
        self.assertIn("If no files changed", instruction)
        self.assertIn("at most four items", instruction)
        self.assertIn("never emit five or more items", instruction)

    def test_valid_final_receipt_is_parsed_and_hidden(self) -> None:
        parsed = parse_turn_completion(
            "Hotovo a ověřeno.\n\n"
            "[HUMAN_ADAM_STEP_COMPLETION]\n"
            '{"commit_message":"Add safe completion","summary":"Doplněna účtenka",'
            '"decision":"Plány budou zachované samostatně",'
            '"next_step":"Spustit cílené testy",'
            '"proposed_next_steps":["Ověřit nový TVBCP záznam","Pokračovat podle výsledku"]}\n'
            "[/HUMAN_ADAM_STEP_COMPLETION]"
        )

        self.assertEqual(parsed.state, "valid")
        self.assertEqual(parsed.visible_answer, "Hotovo a ověřeno.")
        self.assertIsNotNone(parsed.metadata)
        assert parsed.metadata is not None
        self.assertEqual(parsed.metadata.commit_message, "Add safe completion")
        self.assertEqual(
            parsed.metadata.decision,
            "Plány budou zachované samostatně",
        )
        self.assertEqual(
            parsed.metadata.proposed_next_steps,
            ("Ověřit nový TVBCP záznam", "Pokračovat podle výsledku"),
        )

    def test_legacy_three_field_receipt_remains_compatible(self) -> None:
        parsed = parse_turn_completion(
            "Hotovo\n[HUMAN_ADAM_STEP_COMPLETION]\n"
            '{"commit_message":"A","summary":"B","next_step":"C"}\n'
            "[/HUMAN_ADAM_STEP_COMPLETION]"
        )

        self.assertEqual(parsed.state, "valid")
        assert parsed.metadata is not None
        self.assertEqual(parsed.metadata.decision, "")
        self.assertEqual(parsed.metadata.proposed_next_steps, ())

    def test_receipt_must_be_unique_final_and_exact(self) -> None:
        trailing = parse_turn_completion(
            "Hotovo\n[HUMAN_ADAM_STEP_COMPLETION]\n{}\n"
            "[/HUMAN_ADAM_STEP_COMPLETION]\nnavíc"
        )
        repeated = parse_turn_completion(
            "Hotovo\n[HUMAN_ADAM_STEP_COMPLETION]\n{}\n"
            "[/HUMAN_ADAM_STEP_COMPLETION]\n[HUMAN_ADAM_STEP_COMPLETION]"
        )

        self.assertEqual(trailing.state, "invalid")
        self.assertEqual(repeated.state, "invalid")

        end_only = parse_turn_completion("Hotovo\n[/HUMAN_ADAM_STEP_COMPLETION]")
        self.assertEqual(end_only.state, "invalid")
        self.assertNotIn("HUMAN_ADAM_STEP_COMPLETION", end_only.visible_answer)

    def test_receipt_rejects_extra_fields_and_secret_values(self) -> None:
        extra = parse_turn_completion(
            "Hotovo\n[HUMAN_ADAM_STEP_COMPLETION]\n"
            '{"commit_message":"A","summary":"B","next_step":"C","extra":true}\n'
            "[/HUMAN_ADAM_STEP_COMPLETION]"
        )
        secret = parse_turn_completion(
            "Hotovo\n[HUMAN_ADAM_STEP_COMPLETION]\n"
            '{"commit_message":"A","summary":"token=secret","next_step":"C"}\n'
            "[/HUMAN_ADAM_STEP_COMPLETION]"
        )

        self.assertEqual(extra.state, "invalid")
        self.assertEqual(secret.state, "invalid")
        self.assertIn("token", secret.error)

    def test_receipt_rejects_invalid_or_sensitive_future_plans(self) -> None:
        invalid_type = parse_turn_completion(
            "Hotovo\n[HUMAN_ADAM_STEP_COMPLETION]\n"
            '{"commit_message":"A","summary":"B","decision":"","next_step":"C",'
            '"proposed_next_steps":"D"}\n'
            "[/HUMAN_ADAM_STEP_COMPLETION]"
        )
        too_many = parse_turn_completion(
            "Hotovo\n[HUMAN_ADAM_STEP_COMPLETION]\n"
            '{"commit_message":"A","summary":"B","decision":"","next_step":"C",'
            '"proposed_next_steps":["1","2","3","4","5"]}\n'
            "[/HUMAN_ADAM_STEP_COMPLETION]"
        )
        sensitive = parse_turn_completion(
            "Hotovo\n[HUMAN_ADAM_STEP_COMPLETION]\n"
            '{"commit_message":"A","summary":"B","decision":"","next_step":"C",'
            '"proposed_next_steps":["heslo=secret"]}\n'
            "[/HUMAN_ADAM_STEP_COMPLETION]"
        )

        self.assertEqual(invalid_type.state, "invalid")
        self.assertEqual(too_many.state, "invalid")
        self.assertEqual(sensitive.state, "invalid")
        self.assertIn("heslo", sensitive.error)


if __name__ == "__main__":
    unittest.main()
