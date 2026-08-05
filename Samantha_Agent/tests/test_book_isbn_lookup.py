from __future__ import annotations

import json
import socket
import ssl
import urllib.error
import urllib.parse
import unittest
from unittest.mock import patch

from app.book_isbn_lookup import (
    MAX_BOOK_ISBN_LOOKUP_BYTES,
    BookIsbnCertificateError,
    BookIsbnConnectionRefusedError,
    BookIsbnDnsError,
    BookIsbnHttpError,
    BookIsbnLookupError,
    BookIsbnNotFoundError,
    BookIsbnTlsError,
    BookIsbnTimeoutError,
    create_book_isbn_tls_context,
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
        calls: list[tuple[object, float, object]] = []

        def opener(request: object, *, timeout: float, context: object) -> FakeResponse:
            calls.append((request, timeout, context))
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
        request, timeout, context = calls[0]
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
        self.assertIsInstance(context, ssl.SSLContext)

    def test_tls_context_uses_declared_certifi_ca_bundle(self) -> None:
        synthetic_context = object()
        with (
            patch("app.book_isbn_lookup.certifi.where", return_value="/test/certifi-ca.pem") as certifi_where,
            patch("app.book_isbn_lookup.ssl.create_default_context", return_value=synthetic_context) as create_context,
        ):
            context = create_book_isbn_tls_context()

        self.assertIs(context, synthetic_context)
        certifi_where.assert_called_once_with()
        create_context.assert_called_once_with(cafile="/test/certifi-ca.pem")

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
        responses = iter((b"{}", b'{"docs": []}'))

        with self.assertRaises(BookIsbnNotFoundError):
            lookup_book_by_isbn(
                isbn="9781234567897",
                opener=lambda *_args, **_kwargs: FakeResponse(next(responses)),
            )

    def test_empty_exact_lookup_falls_back_to_search_index(self) -> None:
        search_payload = {
            "docs": [
                {
                    "title": "Syntetická kniha ze search indexu",
                    "author_name": ["Testovací autor"],
                    "publisher": ["Testovací nakladatelství"],
                    "first_publish_year": 2025,
                    "number_of_pages_median": 245,
                    "isbn": ["978-1-23456-789-7"],
                }
            ]
        }
        request_urls: list[str] = []

        def opener(request: object, **_kwargs: object) -> FakeResponse:
            request_urls.append(request.full_url)
            if request.full_url.startswith("https://openlibrary.org/api/books?"):
                return FakeResponse(b"{}")
            return FakeResponse(json.dumps(search_payload).encode("utf-8"))

        result = lookup_book_by_isbn(isbn="9781234567897", opener=opener)

        self.assertEqual(result["matched_isbn"], "9781234567897")
        self.assertEqual(result["title"], "Syntetická kniha ze search indexu")
        self.assertEqual(result["author"], "Testovací autor")
        self.assertEqual(result["publisher"], "Testovací nakladatelství")
        self.assertEqual(result["publish_date"], "2025")
        self.assertEqual(result["number_of_pages"], 245)
        self.assertEqual(len(request_urls), 2)
        search_url = urllib.parse.urlparse(request_urls[1])
        self.assertEqual(
            (search_url.scheme, search_url.netloc, search_url.path),
            ("https", "openlibrary.org", "/search.json"),
        )
        self.assertEqual(
            urllib.parse.parse_qs(search_url.query),
            {
                "isbn": ["9781234567897"],
                "fields": [
                    "title,author_name,publisher,first_publish_year,number_of_pages_median,isbn"
                ],
                "limit": ["10"],
            },
        )

    def test_search_index_rejects_record_without_exact_requested_isbn(self) -> None:
        search_payload = {
            "docs": [
                {
                    "title": "Jiná syntetická kniha",
                    "author_name": ["Jiný autor"],
                    "isbn": ["neplatná hodnota", "9780306406157"],
                }
            ]
        }

        def opener(request: object, **_kwargs: object) -> FakeResponse:
            if request.full_url.startswith("https://openlibrary.org/api/books?"):
                return FakeResponse(b"{}")
            return FakeResponse(json.dumps(search_payload).encode("utf-8"))

        with self.assertRaises(BookIsbnNotFoundError):
            lookup_book_by_isbn(isbn="9781234567897", opener=opener)

    def test_isbn10_search_fallback_also_tries_isbn13_variant(self) -> None:
        isbn13 = "9781234567897"
        responses = iter(
            (
                b"{}",
                b'{"docs": []}',
                json.dumps(
                    {
                        "docs": [
                            {
                                "title": "Syntetická kniha podle ISBN-13",
                                "author_name": ["Testovací autor"],
                                "isbn": [isbn13],
                            }
                        ]
                    }
                ).encode("utf-8"),
            )
        )
        request_urls: list[str] = []

        def opener(request: object, **_kwargs: object) -> FakeResponse:
            request_urls.append(request.full_url)
            return FakeResponse(next(responses))

        result = lookup_book_by_isbn(isbn="123456789X", opener=opener)

        self.assertEqual(result["matched_isbn"], isbn13)
        self.assertEqual(len(request_urls), 3)
        first_search = urllib.parse.parse_qs(urllib.parse.urlparse(request_urls[1]).query)
        second_search = urllib.parse.parse_qs(urllib.parse.urlparse(request_urls[2]).query)
        self.assertEqual(first_search["isbn"], ["123456789X"])
        self.assertEqual(second_search["isbn"], [isbn13])

    def test_search_index_requires_docs_list(self) -> None:
        responses = iter((b"{}", b"{}"))

        with self.assertRaises(BookIsbnLookupError):
            lookup_book_by_isbn(
                isbn="9781234567897",
                opener=lambda *_args, **_kwargs: FakeResponse(next(responses)),
            )

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
            (urllib.error.URLError(socket.gaierror("private DNS detail")), BookIsbnDnsError),
            (
                urllib.error.URLError(ssl.SSLCertVerificationError("private certificate detail")),
                BookIsbnCertificateError,
            ),
            (urllib.error.URLError(ssl.SSLError("private TLS detail")), BookIsbnTlsError),
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
