from __future__ import annotations

import errno
import json
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

from app.article_archive import normalize_book_isbn


OPEN_LIBRARY_BOOKS_API = "https://openlibrary.org/api/books"
OPEN_LIBRARY_SOURCE_NAME = "Open Library"
MAX_BOOK_ISBN_LOOKUP_BYTES = 512 * 1024
DEFAULT_BOOK_ISBN_LOOKUP_TIMEOUT = 8.0


class BookIsbnLookupError(RuntimeError):
    """Raised when the fixed external catalog cannot be queried safely."""


class BookIsbnNotFoundError(BookIsbnLookupError):
    """Raised when the fixed external catalog has no record for the ISBN."""


class BookIsbnTimeoutError(BookIsbnLookupError):
    """Raised when the fixed external catalog does not answer in time."""


class BookIsbnConnectionRefusedError(BookIsbnLookupError):
    """Raised when the fixed external catalog refuses the connection."""


class BookIsbnConnectionError(BookIsbnLookupError):
    """Raised when the fixed external catalog cannot be reached."""


class BookIsbnDnsError(BookIsbnConnectionError):
    """Raised when the fixed external catalog hostname cannot be resolved."""


class BookIsbnCertificateError(BookIsbnConnectionError):
    """Raised when the fixed external catalog certificate cannot be verified."""


class BookIsbnTlsError(BookIsbnConnectionError):
    """Raised when a secure connection to the fixed external catalog fails."""


class BookIsbnHttpError(BookIsbnLookupError):
    """Raised when the fixed external catalog responds with an HTTP error."""

    def __init__(self, status_code: int) -> None:
        self.status_code = status_code if 100 <= status_code <= 599 else 0
        status_label = str(self.status_code) if self.status_code else "chybu"
        super().__init__(f"Veřejný katalog vrátil HTTP {status_label}. Zkus to později.")


def lookup_book_by_isbn(
    *,
    isbn: str,
    opener: Callable[..., Any] | None = None,
    timeout: float = DEFAULT_BOOK_ISBN_LOOKUP_TIMEOUT,
) -> dict[str, Any]:
    normalized_isbn = normalize_book_isbn(isbn)
    if not normalized_isbn:
        raise ValueError("Vyplň ISBN knihy.")

    isbn_candidates = [normalized_isbn]
    if len(normalized_isbn) == 10:
        isbn_candidates.append(isbn10_to_isbn13(normalized_isbn))

    query = urllib.parse.urlencode(
        {
            "bibkeys": ",".join(f"ISBN:{candidate}" for candidate in isbn_candidates),
            "jscmd": "data",
            "format": "json",
        }
    )
    request = urllib.request.Request(
        f"{OPEN_LIBRARY_BOOKS_API}?{query}",
        headers={
            "Accept": "application/json",
            "User-Agent": "Samantha-Knihovna/1.0 ISBN lookup",
        },
        method="GET",
    )
    open_request = opener or urllib.request.urlopen
    try:
        with open_request(request, timeout=timeout) as response:
            raw = response.read(MAX_BOOK_ISBN_LOOKUP_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise BookIsbnHttpError(int(exc.code or 0)) from exc
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise _safe_transport_error(exc) from exc

    if len(raw) > MAX_BOOK_ISBN_LOOKUP_BYTES:
        raise BookIsbnLookupError("Odpověď veřejného katalogu byla příliš velká.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BookIsbnLookupError("Veřejný katalog vrátil neplatnou odpověď.") from exc
    if not isinstance(payload, dict):
        raise BookIsbnLookupError("Veřejný katalog vrátil neplatnou odpověď.")

    matched_isbn = ""
    record: dict[str, Any] | None = None
    for candidate in isbn_candidates:
        candidate_record = payload.get(f"ISBN:{candidate}")
        if isinstance(candidate_record, dict):
            matched_isbn = candidate
            record = candidate_record
            break
    if not isinstance(record, dict):
        raise BookIsbnNotFoundError("Pro toto ISBN nebyla v katalogu nalezena kniha.")

    title = _clean_text(record.get("title"), 500)
    author = _join_named_values(record.get("authors"), 300)
    publisher = _join_named_values(record.get("publishers"), 300)
    publish_date = _clean_text(record.get("publish_date"), 100)
    number_of_pages = _safe_page_count(record.get("number_of_pages"))
    if not title and not author:
        raise BookIsbnNotFoundError("Katalog pro toto ISBN nevrátil použitelný název ani autora.")

    return {
        "isbn": normalized_isbn,
        "matched_isbn": matched_isbn,
        "title": title,
        "author": author,
        "publisher": publisher,
        "publish_date": publish_date,
        "number_of_pages": number_of_pages,
        "source_name": OPEN_LIBRARY_SOURCE_NAME,
        "source_url": f"https://openlibrary.org/isbn/{matched_isbn}",
    }


def isbn10_to_isbn13(isbn10: str) -> str:
    normalized = normalize_book_isbn(isbn10)
    if len(normalized) != 10:
        raise ValueError("Převod vyžaduje platné ISBN-10.")
    base = f"978{normalized[:9]}"
    checksum = (10 - sum((1 if index % 2 == 0 else 3) * int(char) for index, char in enumerate(base)) % 10) % 10
    return f"{base}{checksum}"


def _safe_transport_error(exc: BaseException) -> BookIsbnLookupError:
    reason = exc.reason if isinstance(exc, urllib.error.URLError) else exc
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return BookIsbnTimeoutError("Veřejný katalog neodpověděl včas. Zkus to znovu.")
    if isinstance(reason, socket.gaierror):
        return BookIsbnDnsError("Název openlibrary.org se nepodařilo přeložit pomocí DNS.")
    if isinstance(reason, ssl.SSLCertVerificationError):
        return BookIsbnCertificateError("Python nedokázal ověřit TLS certifikát veřejného katalogu.")
    if isinstance(reason, ssl.SSLError):
        return BookIsbnTlsError("Python nedokázal navázat zabezpečené TLS spojení s veřejným katalogem.")
    if isinstance(reason, ConnectionRefusedError) or getattr(reason, "errno", None) == errno.ECONNREFUSED:
        return BookIsbnConnectionRefusedError("Veřejný katalog odmítl spojení. Zkus to později.")
    return BookIsbnConnectionError("K veřejnému katalogu se nepodařilo připojit. Zkus to později.")


def _clean_text(value: Any, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def _join_named_values(value: Any, limit: int) -> str:
    if not isinstance(value, list):
        return ""
    names: list[str] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        name = _clean_text(item.get("name"), limit)
        if name:
            names.append(name)
    return ", ".join(names)[:limit]


def _safe_page_count(value: Any) -> int:
    try:
        count = int(value)
    except (TypeError, ValueError):
        return 0
    return count if 0 < count <= 100_000 else 0
