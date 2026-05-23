from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.startup_prompts import (
    OWL_TEXT_PROMPT_QUESTION,
    format_owl_text_startup_prompt,
    load_owl_text_prompt_state,
)


class StartupPromptsTests(unittest.TestCase):
    def test_owl_text_prompt_is_shown_once_per_day(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "owl_text_prompt.json"

            first = format_owl_text_startup_prompt(path=path, today="2026-05-22")
            second = format_owl_text_startup_prompt(path=path, today="2026-05-22")

            self.assertIn(OWL_TEXT_PROMPT_QUESTION, first)
            self.assertIn("uz byl zobrazen", second)
            self.assertNotIn(OWL_TEXT_PROMPT_QUESTION, second)

    def test_owl_text_prompt_state_is_per_day(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "owl_text_prompt.json"

            format_owl_text_startup_prompt(path=path, today="2026-05-22")
            next_day = format_owl_text_startup_prompt(path=path, today="2026-05-23")

            self.assertIn(OWL_TEXT_PROMPT_QUESTION, next_day)
            self.assertEqual(load_owl_text_prompt_state(path).last_asked_date, "2026-05-23")

    def test_preview_mode_does_not_mark_prompt_as_asked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "owl_text_prompt.json"

            preview = format_owl_text_startup_prompt(
                path=path,
                today="2026-05-22",
                mark_asked=False,
            )

            self.assertIn(OWL_TEXT_PROMPT_QUESTION, preview)
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
