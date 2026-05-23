from __future__ import annotations

import unittest
from datetime import date

from app.email.models import EmailHeader, EmailTextSearchHit
from app.email.text_search_tools import (
    has_explicit_text_search_confirmation,
    search_email_text_year_text,
)
from app.email.icloud_provider import _search_text_uids


class EmailTextSearchToolsTests(unittest.TestCase):
    def test_without_confirmation_provider_is_not_called(self) -> None:
        def fail_provider() -> object:
            raise AssertionError("Provider must not be called without confirmation")

        result = search_email_text_year_text(
            terms=["Pojištění"],
            year=2026,
            user_confirmed=False,
            confirmation_text="",
            provider_factory=fail_provider,
        )

        self.assertIn("Bez toho provider nevolam", result)

    def test_confirmation_requires_denials(self) -> None:
        self.assertFalse(
            has_explicit_text_search_confirmation(
                terms=["Pojištění"],
                year=2026,
                confirmation_text=(
                    "Potvrzuji read-only hledani v textech e-mailu za rok 2026 "
                    "pro vyraz Pojištění."
                ),
            )
        )

    def test_confirmation_accepts_terms_and_safety_limits(self) -> None:
        self.assertTrue(
            has_explicit_text_search_confirmation(
                terms=["Pojištění", "připojištění", "výroční zpráva"],
                year=2026,
                confirmation_text=(
                    "Potvrzuji read-only hledání v textech/tělech e-mailů za rok 2026 "
                    "pro výrazy Pojištění, připojištění a výroční zpráva. "
                    "Neotevírat odkazy. Nestahovat přílohy. Nic neodesílat. "
                    "Nemazat. Nepřesouvat. Neoznačovat jako přečtené."
                ),
            )
        )

    def test_confirmed_search_returns_headers_only(self) -> None:
        fake_provider = _FakeProvider()
        result = search_email_text_year_text(
            terms=["Pojištění", "připojištění"],
            year=2026,
            limit=20,
            user_confirmed=True,
            confirmation_text=_confirmation(),
            provider_factory=lambda: fake_provider,
        )

        self.assertEqual(
            fake_provider.calls,
            [(["Pojištění", "připojištění"], date(2026, 1, 1), date(2027, 1, 1), 20)],
        )
        self.assertIn("UID: 123", result)
        self.assertIn("Predmet: Nabidka pojisteni", result)
        self.assertIn("Nalezene vyrazy: Pojištění", result)
        self.assertNotIn("tajne telo", result)
        self.assertNotIn("https://", result)

    def test_provider_text_search_empty_payload_means_no_uids(self) -> None:
        fake_imap = _FakeImap(status="OK", data=[None])

        result = _search_text_uids(
            imap=fake_imap,
            term="Pojištění",
            since_imap="01-Jan-2026",
            before_imap="01-Jan-2027",
        )

        self.assertEqual(result, [])


class _FakeProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], date, date, int]] = []

    def search_text_headers(
        self,
        terms: list[str],
        since: date,
        before: date,
        limit: int,
    ) -> list[EmailTextSearchHit]:
        self.calls.append((terms, since, before, limit))
        return [
            EmailTextSearchHit(
                header=EmailHeader(
                    internal_id="123",
                    date="Tue, 20 Jan 2026 08:00:00 +0000",
                    sender="Pojistovna <kontakt@example.com>",
                    subject="Nabidka pojisteni",
                ),
                matched_terms=("Pojištění",),
            )
        ]


class _FakeImap:
    def __init__(self, status: str, data: list[object]) -> None:
        self.status = status
        self.data = data

    def uid(self, *args: object) -> tuple[str, list[object]]:
        return self.status, self.data


def _confirmation() -> str:
    return (
        "Potvrzuji read-only hledani v textech e-mailu za rok 2026 "
        "pro vyrazy Pojištění a připojištění. "
        "Neotevirat odkazy. Nestahovat prilohy. Nic neodesilat. "
        "Nemazat. Nepresouvat. Neoznacovat jako prectene."
    )


if __name__ == "__main__":
    unittest.main()
