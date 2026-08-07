from __future__ import annotations

import errno
import json
import re
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

import certifi

from app.article_archive import normalize_book_isbn


OPEN_LIBRARY_BOOKS_API = "https://openlibrary.org/api/books"
OPEN_LIBRARY_SEARCH_API = "https://openlibrary.org/search.json"
OPEN_LIBRARY_SOURCE_NAME = "Open Library"
KNIHOVNY_SEARCH_API = "https://www.knihovny.cz/api/v1/search"
KNIHOVNY_SOURCE_NAME = "Knihovny.cz"
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
    tls_context: ssl.SSLContext | None = None,
) -> dict[str, Any]:
    normalized_isbn = normalize_book_isbn(isbn)
    if not normalized_isbn:
        raise ValueError("Vyplň ISBN knihy.")

    isbn_candidates = [normalized_isbn]
    if len(normalized_isbn) == 10:
        isbn_candidates.append(isbn10_to_isbn13(normalized_isbn))

    open_request = opener or urllib.request.urlopen
    verified_tls_context = tls_context or create_book_isbn_tls_context()
    primary_error: BookIsbnLookupError | None = None
    try:
        result = _lookup_book_in_knihovny(
            normalized_isbn,
            isbn_candidates,
            opener=open_request,
            timeout=timeout,
            tls_context=verified_tls_context,
        )
    except BookIsbnLookupError as exc:
        primary_error = exc
    else:
        try:
            open_library = _lookup_book_in_open_library(
                normalized_isbn,
                isbn_candidates,
                opener=open_request,
                timeout=timeout,
                tls_context=verified_tls_context,
            )
        except BookIsbnLookupError:
            open_library = None
        if open_library:
            for field in ("publisher", "publish_date", "publication_year", "number_of_pages"):
                if open_library.get(field):
                    result[field] = open_library[field]
        return result

    try:
        return _lookup_book_in_open_library(
            normalized_isbn,
            isbn_candidates,
            opener=open_request,
            timeout=timeout,
            tls_context=verified_tls_context,
        )
    except BookIsbnLookupError as fallback_error:
        if primary_error is not None and not isinstance(primary_error, BookIsbnNotFoundError):
            raise primary_error
        raise fallback_error


def _lookup_book_in_knihovny(
    normalized_isbn: str,
    isbn_candidates: list[str],
    *,
    opener: Callable[..., Any],
    timeout: float,
    tls_context: ssl.SSLContext,
) -> dict[str, Any]:
    for candidate in isbn_candidates:
        query = urllib.parse.urlencode(
            {
                "lookfor": candidate,
                "type": "ISN",
                "limit": 10,
            }
        )
        payload = _request_json(
            f"{KNIHOVNY_SEARCH_API}?{query}",
            opener=opener,
            timeout=timeout,
            tls_context=tls_context,
            catalog_host="www.knihovny.cz",
        )
        if payload.get("status") != "OK":
            raise BookIsbnLookupError("Český katalog vrátil neplatnou odpověď.")
        records = payload.get("records", [])
        if not isinstance(records, list):
            raise BookIsbnLookupError("Český katalog vrátil neplatnou odpověď.")
        for record in records:
            if not isinstance(record, dict):
                continue
            title = _clean_text(record.get("title"), 500)
            author = _knihovny_author(record.get("authors"))
            if not title and not author:
                continue
            record_id = _clean_text(record.get("id"), 300)
            source_url = ""
            if record_id:
                safe_record_id = urllib.parse.quote(record_id, safe="._-")
                source_url = f"https://www.knihovny.cz/Record/{safe_record_id}"
            return {
                "isbn": normalized_isbn,
                "matched_isbn": candidate,
                "title": title,
                "author": author,
                "publisher": "",
                "publish_date": "",
                "publication_year": "",
                "number_of_pages": 0,
                "source_name": KNIHOVNY_SOURCE_NAME,
                "source_url": source_url,
            }
    raise BookIsbnNotFoundError("Pro toto ISBN nebyla v českém katalogu nalezena kniha.")


def _lookup_book_in_open_library(
    normalized_isbn: str,
    isbn_candidates: list[str],
    *,
    opener: Callable[..., Any],
    timeout: float,
    tls_context: ssl.SSLContext,
) -> dict[str, Any]:

    query = urllib.parse.urlencode(
        {
            "bibkeys": ",".join(f"ISBN:{candidate}" for candidate in isbn_candidates),
            "jscmd": "data",
            "format": "json",
        }
    )
    payload = _request_json(
        f"{OPEN_LIBRARY_BOOKS_API}?{query}",
        opener=opener,
        timeout=timeout,
        tls_context=tls_context,
        catalog_host="openlibrary.org",
    )

    matched_isbn = ""
    record: dict[str, Any] | None = None
    for candidate in isbn_candidates:
        candidate_record = payload.get(f"ISBN:{candidate}")
        if isinstance(candidate_record, dict):
            matched_isbn = candidate
            record = candidate_record
            break
    if not isinstance(record, dict):
        matched_isbn, record = _lookup_book_in_search_index(
            isbn_candidates,
            opener=opener,
            timeout=timeout,
            tls_context=tls_context,
        )

    title = _clean_text(record.get("title"), 500)
    author = _join_catalog_values(record.get("authors") or record.get("author_name"), 300)
    publisher = _join_catalog_values(record.get("publishers") or record.get("publisher"), 300)
    publish_date = _clean_text(record.get("publish_date") or record.get("first_publish_year"), 100)
    number_of_pages = _safe_page_count(
        record.get("number_of_pages") or record.get("number_of_pages_median")
    )
    if not title and not author:
        raise BookIsbnNotFoundError("Katalog pro toto ISBN nevrátil použitelný název ani autora.")

    return {
        "isbn": normalized_isbn,
        "matched_isbn": matched_isbn,
        "title": title,
        "author": author,
        "publisher": publisher,
        "publish_date": publish_date,
        "publication_year": _extract_publication_year(publish_date),
        "number_of_pages": number_of_pages,
        "source_name": OPEN_LIBRARY_SOURCE_NAME,
        "source_url": f"https://openlibrary.org/isbn/{matched_isbn}",
    }


def _lookup_book_in_search_index(
    isbn_candidates: list[str],
    *,
    opener: Callable[..., Any],
    timeout: float,
    tls_context: ssl.SSLContext,
) -> tuple[str, dict[str, Any]]:
    fields = "title,author_name,publisher,first_publish_year,number_of_pages_median,isbn"
    for candidate in isbn_candidates:
        query = urllib.parse.urlencode(
            {
                "isbn": candidate,
                "fields": fields,
                "limit": 10,
            }
        )
        payload = _request_json(
            f"{OPEN_LIBRARY_SEARCH_API}?{query}",
            opener=opener,
            timeout=timeout,
            tls_context=tls_context,
            catalog_host="openlibrary.org",
        )
        docs = payload.get("docs")
        if not isinstance(docs, list):
            raise BookIsbnLookupError("Veřejný katalog vrátil neplatnou odpověď.")
        for record in docs:
            if not isinstance(record, dict):
                continue
            matched_isbn = _matched_search_isbn(record, isbn_candidates)
            if matched_isbn:
                return matched_isbn, record
    raise BookIsbnNotFoundError("Pro toto ISBN nebyla v katalogu nalezena kniha.")


def _request_json(
    url: str,
    *,
    opener: Callable[..., Any],
    timeout: float,
    tls_context: ssl.SSLContext,
    catalog_host: str,
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Samantha-Knihovna/1.0 ISBN lookup",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=timeout, context=tls_context) as response:
            raw = response.read(MAX_BOOK_ISBN_LOOKUP_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise BookIsbnHttpError(int(exc.code or 0)) from exc
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise _safe_transport_error(exc, catalog_host=catalog_host) from exc

    if len(raw) > MAX_BOOK_ISBN_LOOKUP_BYTES:
        raise BookIsbnLookupError("Odpověď veřejného katalogu byla příliš velká.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BookIsbnLookupError("Veřejný katalog vrátil neplatnou odpověď.") from exc
    if not isinstance(payload, dict):
        raise BookIsbnLookupError("Veřejný katalog vrátil neplatnou odpověď.")
    return payload


def create_book_isbn_tls_context() -> ssl.SSLContext:
    """Build a verified TLS context from the application's declared CA bundle."""

    return ssl.create_default_context(cafile=certifi.where())


def isbn10_to_isbn13(isbn10: str) -> str:
    normalized = normalize_book_isbn(isbn10)
    if len(normalized) != 10:
        raise ValueError("Převod vyžaduje platné ISBN-10.")
    base = f"978{normalized[:9]}"
    checksum = (10 - sum((1 if index % 2 == 0 else 3) * int(char) for index, char in enumerate(base)) % 10) % 10
    return f"{base}{checksum}"


def _safe_transport_error(exc: BaseException, *, catalog_host: str) -> BookIsbnLookupError:
    reason = exc.reason if isinstance(exc, urllib.error.URLError) else exc
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return BookIsbnTimeoutError("Veřejný katalog neodpověděl včas. Zkus to znovu.")
    if isinstance(reason, socket.gaierror):
        return BookIsbnDnsError(f"Název {catalog_host} se nepodařilo přeložit pomocí DNS.")
    if isinstance(reason, ssl.SSLCertVerificationError):
        return BookIsbnCertificateError("Python nedokázal ověřit TLS certifikát veřejného katalogu.")
    if isinstance(reason, ssl.SSLError):
        return BookIsbnTlsError("Python nedokázal navázat zabezpečené TLS spojení s veřejným katalogem.")
    if isinstance(reason, ConnectionRefusedError) or getattr(reason, "errno", None) == errno.ECONNREFUSED:
        return BookIsbnConnectionRefusedError("Veřejný katalog odmítl spojení. Zkus to později.")
    return BookIsbnConnectionError("K veřejnému katalogu se nepodařilo připojit. Zkus to později.")


def _clean_text(value: Any, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def _join_catalog_values(value: Any, limit: int) -> str:
    if not isinstance(value, list):
        return ""
    names: list[str] = []
    for item in value:
        name = _clean_text(item.get("name") if isinstance(item, dict) else item, limit)
        if name:
            names.append(name)
    return ", ".join(names)[:limit]


def _knihovny_author(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    for group in ("primary", "secondary", "corporate"):
        raw_group = value.get(group)
        candidates = list(raw_group) if isinstance(raw_group, dict) else raw_group
        if not isinstance(candidates, list):
            continue
        names: list[str] = []
        for candidate in candidates:
            raw_name = candidate.get("name") if isinstance(candidate, dict) else candidate
            name = _clean_text(raw_name, 300)
            name = re.sub(r",\s*[0-9]{4}(?:-[0-9]{0,4})?\s*$", "", name).strip(" ,")
            if name and name not in names:
                names.append(name)
        if names:
            return ", ".join(names)[:300]
    return ""


def _extract_publication_year(value: Any) -> str:
    match = re.search(r"(?<![0-9])([12][0-9]{3})(?![0-9])", str(value or ""))
    return match.group(1) if match else ""


def _matched_search_isbn(record: dict[str, Any], isbn_candidates: list[str]) -> str:
    values = record.get("isbn")
    if not isinstance(values, list):
        return ""
    normalized_values: set[str] = set()
    for value in values:
        try:
            normalized_value = normalize_book_isbn(str(value))
        except ValueError:
            continue
        if normalized_value:
            normalized_values.add(normalized_value)
    return next((candidate for candidate in isbn_candidates if candidate in normalized_values), "")


def _safe_page_count(value: Any) -> int:
    try:
        count = int(value)
    except (TypeError, ValueError):
        return 0
    return count if 0 < count <= 100_000 else 0
