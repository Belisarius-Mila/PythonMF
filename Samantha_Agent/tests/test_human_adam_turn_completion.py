from __future__ import annotations

import unittest

from app.communication.human_adam_turn_completion import (
    automatic_completion_instruction,
    parse_turn_completion,
)


class HumanAdamTurnCompletionTests(unittest.TestCase):
    def test_read_only_turn_gets_no_completion_protocol(self) -> None:
        self.assertEqual(automatic_completion_instruction(writable=False), "")
        self.assertIn(
            "[HUMAN_ADAM_STEP_COMPLETION]",
            automatic_completion_instruction(writable=True),
        )

    def test_valid_final_receipt_is_parsed_and_hidden(self) -> None:
        parsed = parse_turn_completion(
            "Hotovo a ověřeno.\n\n"
            "[HUMAN_ADAM_STEP_COMPLETION]\n"
            '{"commit_message":"Add safe completion","summary":"Doplněna účtenka",'
            '"next_step":"Spustit cílené testy"}\n'
            "[/HUMAN_ADAM_STEP_COMPLETION]"
        )

        self.assertEqual(parsed.state, "valid")
        self.assertEqual(parsed.visible_answer, "Hotovo a ověřeno.")
        self.assertIsNotNone(parsed.metadata)
        assert parsed.metadata is not None
        self.assertEqual(parsed.metadata.commit_message, "Add safe completion")

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


if __name__ == "__main__":
    unittest.main()
