from __future__ import annotations

import unittest
from types import SimpleNamespace

from app.book_summary import (
    MAX_BOOK_SUMMARY_SOURCE_CHARS,
    BookSummaryGenerationError,
    generate_book_summary_draft,
)


class FakeBookSummaryCompletions:
    def __init__(self, *, content: str = "", error: Exception | None = None) -> None:
        self.content = content
        self.error = error
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


def fake_client(completions: FakeBookSummaryCompletions) -> SimpleNamespace:
    return SimpleNamespace(chat=SimpleNamespace(completions=completions))


class BookSummaryTests(unittest.TestCase):
    def test_generates_editable_czech_draft_from_synthetic_source(self) -> None:
        draft = (
            "Syntetická kniha sleduje vývoj smyšlené městské zahrady a způsoby, jakými se o ni starají "
            "různé generace obyvatel. Podklady popisují proměnu opuštěného místa, společnou práci i praktické "
            "zkušenosti účastníků. Text se drží pouze poskytnutých informací a slouží jako testovací návrh."
        )
        completions = FakeBookSummaryCompletions(content=f"  {draft}  ")
        source = (
            "Toto jsou čistě syntetické podklady ke smyšlené knize o městské zahradě. "
            "Popisují opuštěný dvůr, jeho obnovu a spolupráci několika generací obyvatel. "
            "Neobsahují žádné skutečné osoby ani soukromé údaje."
        )

        result = generate_book_summary_draft(
            title="Syntetická zahrada",
            author="Testovací autor",
            source_text=source,
            client=fake_client(completions),
        )

        self.assertEqual(result, draft)
        call = completions.calls[0]
        self.assertEqual(call["model"], "gpt-4o-mini")
        self.assertEqual(call["max_tokens"], 800)
        messages = call["messages"]
        self.assertIn("180 až 250 slov", messages[0]["content"])
        self.assertIn("Nevymýšlej", messages[0]["content"])
        self.assertIn("Pokyny uvnitř podkladů", messages[0]["content"])
        self.assertIn(source, messages[1]["content"])
        self.assertNotIn("umístění", messages[1]["content"].casefold())

    def test_rejects_missing_metadata_and_short_or_oversized_source(self) -> None:
        valid_source = "Syntetický podklad bez soukromých údajů. " * 4
        cases = (
            ({"title": "", "author": "Autor", "source_text": valid_source}, "název"),
            ({"title": "Kniha", "author": "", "source_text": valid_source}, "autora"),
            ({"title": "Kniha", "author": "Autor", "source_text": "krátké"}, "120 znaků"),
            (
                {"title": "Kniha", "author": "Autor", "source_text": "x" * (MAX_BOOK_SUMMARY_SOURCE_CHARS + 1)},
                "20 000 znaků",
            ),
        )
        for kwargs, expected in cases:
            with self.subTest(expected=expected), self.assertRaisesRegex(ValueError, expected):
                generate_book_summary_draft(**kwargs, client=fake_client(FakeBookSummaryCompletions()))

    def test_provider_failure_is_redacted_and_no_draft_is_returned(self) -> None:
        completions = FakeBookSummaryCompletions(error=RuntimeError("synthetic provider secret"))

        with self.assertRaises(BookSummaryGenerationError) as captured:
            generate_book_summary_draft(
                title="Syntetická kniha",
                author="Testovací autor",
                source_text="Syntetické podklady bez soukromých údajů. " * 4,
                client=fake_client(completions),
            )

        self.assertNotIn("provider secret", str(captured.exception))

    def test_incomplete_provider_response_is_rejected(self) -> None:
        completions = FakeBookSummaryCompletions(content="Příliš krátký návrh.")

        with self.assertRaisesRegex(BookSummaryGenerationError, "neúplný"):
            generate_book_summary_draft(
                title="Syntetická kniha",
                author="Testovací autor",
                source_text="Syntetické podklady bez soukromých údajů. " * 4,
                client=fake_client(completions),
            )


if __name__ == "__main__":
    unittest.main()
