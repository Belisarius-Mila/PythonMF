from __future__ import annotations

import json
import urllib.error
import urllib.parse
import unittest

from app.book_isbn_lookup import (
    MAX_BOOK_ISBN_LOOKUP_BYTES,
    BookIsbnConnectionRefusedError,
    BookIsbnHttpError,
    BookIsbnLookupError,
    BookIsbnNotFoundError,
    BookIsbnTimeoutError,
    isbn10_to_isbn13,
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
        self.assertEqual(result["matched_isbn"], "9781234567897")
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

    def test_isbn10_is_looked_up_together_with_its_isbn13_variant(self) -> None:
        payload = {
            "ISBN:9781234567897": {
                "title": "Syntetická kniha",
                "authors": [{"name": "Testovací autor"}],
            }
        }
        request_urls: list[str] = []

        def opener(request: object, **_kwargs: object) -> FakeResponse:
            request_urls.append(request.full_url)
            return FakeResponse(json.dumps(payload).encode("utf-8"))

        result = lookup_book_by_isbn(isbn="123456789X", opener=opener)

        self.assertEqual(isbn10_to_isbn13("123456789X"), "9781234567897")
        self.assertEqual(result["isbn"], "123456789X")
        self.assertEqual(result["matched_isbn"], "9781234567897")
        self.assertEqual(result["source_url"], "https://openlibrary.org/isbn/9781234567897")
        parsed_query = urllib.parse.parse_qs(urllib.parse.urlparse(request_urls[0]).query)
        self.assertEqual(
            parsed_query["bibkeys"],
            ["ISBN:123456789X,ISBN:9781234567897"],
        )

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

    def test_transport_errors_are_distinguished_and_redacted(self) -> None:
        cases = (
            (urllib.error.URLError(TimeoutError("private timeout detail")), BookIsbnTimeoutError),
            (urllib.error.URLError(ConnectionRefusedError("private refusal detail")), BookIsbnConnectionRefusedError),
            (urllib.error.URLError("private connection detail"), BookIsbnLookupError),
        )
        for transport_error, expected_type in cases:
            with self.subTest(expected_type=expected_type.__name__):
                def opener(*_args: object, **_kwargs: object) -> FakeResponse:
                    raise transport_error

                with self.assertRaises(expected_type) as raised:
                    lookup_book_by_isbn(isbn="9781234567897", opener=opener)
                self.assertNotIn("private", str(raised.exception))

    def test_http_error_exposes_only_safe_numeric_status(self) -> None:
        def opener(*_args: object, **_kwargs: object) -> FakeResponse:
            raise urllib.error.HTTPError(
                "https://openlibrary.org/private-detail",
                429,
                "private reason",
                {},
                None,
            )

        with self.assertRaises(BookIsbnHttpError) as raised:
            lookup_book_by_isbn(isbn="9781234567897", opener=opener)
        self.assertEqual(raised.exception.status_code, 429)
        self.assertIn("HTTP 429", str(raised.exception))
        self.assertNotIn("private", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
