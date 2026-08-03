from __future__ import annotations

import json
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


def lookup_book_by_isbn(
    *,
    isbn: str,
    opener: Callable[..., Any] | None = None,
    timeout: float = DEFAULT_BOOK_ISBN_LOOKUP_TIMEOUT,
) -> dict[str, Any]:
    normalized_isbn = normalize_book_isbn(isbn)
    if not normalized_isbn:
        raise ValueError("Vyplň ISBN knihy.")

    query = urllib.parse.urlencode(
        {
            "bibkeys": f"ISBN:{normalized_isbn}",
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
        if exc.code == 404:
            raise BookIsbnNotFoundError("Pro toto ISBN nebyla v katalogu nalezena kniha.") from exc
        raise BookIsbnLookupError("Veřejný katalog je dočasně nedostupný. Údaje vyplň ručně.") from exc
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise BookIsbnLookupError("Veřejný katalog je dočasně nedostupný. Údaje vyplň ručně.") from exc

    if len(raw) > MAX_BOOK_ISBN_LOOKUP_BYTES:
        raise BookIsbnLookupError("Odpověď veřejného katalogu byla příliš velká.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BookIsbnLookupError("Veřejný katalog vrátil neplatnou odpověď.") from exc
    if not isinstance(payload, dict):
        raise BookIsbnLookupError("Veřejný katalog vrátil neplatnou odpověď.")

    record = payload.get(f"ISBN:{normalized_isbn}")
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
        "title": title,
        "author": author,
        "publisher": publisher,
        "publish_date": publish_date,
        "number_of_pages": number_of_pages,
        "source_name": OPEN_LIBRARY_SOURCE_NAME,
        "source_url": f"https://openlibrary.org/isbn/{normalized_isbn}",
    }


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
