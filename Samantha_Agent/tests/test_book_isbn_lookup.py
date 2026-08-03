from __future__ import annotations

import json
import urllib.error
import urllib.parse
import unittest

from app.book_isbn_lookup import (
    MAX_BOOK_ISBN_LOOKUP_BYTES,
    BookIsbnLookupError,
    BookIsbnNotFoundError,
    lookup_book_by_isbn,
)


class FakeResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, limit: int) -> bytes:
        return self.body[:limit]


class BookIsbnLookupTests(unittest.TestCase):
    def test_lookup_sends_only_normalized_isbn_to_fixed_catalog(self) -> None:
        payload = {
            "ISBN:9781234567897": {
                "title": "Syntetická kniha",
                "authors": [{"name": "Testovací autor"}],
                "publishers": [{"name": "Testovací nakladatelství"}],
                "publish_date": "2026",
                "number_of_pages": 123,
            }
        }
        calls: list[tuple[object, float]] = []

        def opener(request: object, *, timeout: float) -> FakeResponse:
            calls.append((request, timeout))
            return FakeResponse(json.dumps(payload).encode("utf-8"))

        result = lookup_book_by_isbn(isbn="978-1-23456-789-7", opener=opener)

        self.assertEqual(result["isbn"], "9781234567897")
        self.assertEqual(result["title"], "Syntetická kniha")
        self.assertEqual(result["author"], "Testovací autor")
        self.assertEqual(result["publisher"], "Testovací nakladatelství")
        self.assertEqual(result["publish_date"], "2026")
        self.assertEqual(result["number_of_pages"], 123)
        self.assertEqual(result["source_name"], "Open Library")
        self.assertEqual(result["source_url"], "https://openlibrary.org/isbn/9781234567897")
        self.assertEqual(len(calls), 1)
        request, timeout = calls[0]
        parsed = urllib.parse.urlparse(request.full_url)
        self.assertEqual((parsed.scheme, parsed.netloc, parsed.path), ("https", "openlibrary.org", "/api/books"))
        self.assertEqual(
            urllib.parse.parse_qs(parsed.query),
            {
                "bibkeys": ["ISBN:9781234567897"],
                "jscmd": ["data"],
                "format": ["json"],
            },
        )
        self.assertEqual(timeout, 8.0)

    def test_invalid_isbn_is_rejected_before_network(self) -> None:
        called = False

        def opener(*_args: object, **_kwargs: object) -> FakeResponse:
            nonlocal called
            called = True
            return FakeResponse(b"{}")

        with self.assertRaises(ValueError):
            lookup_book_by_isbn(isbn="123", opener=opener)
        self.assertFalse(called)

    def test_unknown_isbn_has_specific_safe_result(self) -> None:
        with self.assertRaises(BookIsbnNotFoundError):
            lookup_book_by_isbn(isbn="9781234567897", opener=lambda *_args, **_kwargs: FakeResponse(b"{}"))

    def test_malformed_and_oversized_responses_are_rejected(self) -> None:
        with self.assertRaises(BookIsbnLookupError):
            lookup_book_by_isbn(
                isbn="9781234567897",
                opener=lambda *_args, **_kwargs: FakeResponse(b"not-json"),
            )
        with self.assertRaises(BookIsbnLookupError):
            lookup_book_by_isbn(
                isbn="9781234567897",
                opener=lambda *_args, **_kwargs: FakeResponse(b"x" * (MAX_BOOK_ISBN_LOOKUP_BYTES + 1)),
            )

    def test_transport_error_is_redacted(self) -> None:
        def opener(*_args: object, **_kwargs: object) -> FakeResponse:
            raise urllib.error.URLError("private transport detail")

        with self.assertRaises(BookIsbnLookupError) as raised:
            lookup_book_by_isbn(isbn="9781234567897", opener=opener)
        self.assertNotIn("private transport detail", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
