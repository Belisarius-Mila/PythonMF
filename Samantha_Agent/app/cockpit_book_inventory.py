"""Scoped HTTP adapters for the existing private book archive."""
from pathlib import Path
from urllib.parse import parse_qs

from app.article_archive import DEFAULT_ARCHIVE_ROOT
from app.book_inventory import (CatalogPreview, assign_inventory_locations, canonical_isbn,
                                cover_url, inventory_books, inventory_operation, save_inventory_book)
from app.book_isbn_lookup import BookIsbnLookupError
from app.file_persistence import FilePersistenceError

CATALOG = CatalogPreview()
ASSETS = Path(__file__).parent / "frontend/cockpit/vendor/zxing-3.1.6"
SCANNER_ASSETS = {"reader.js": "application/javascript; charset=utf-8",
                  "zxing_reader.wasm": "application/wasm", "LICENSE.txt": "text/plain; charset=utf-8"}
BOOK_INVENTORY_GET_PATHS = ("/api/library/books/inventory", "/api/library/book/quick-status", "/api/library/book/quick-lookup")


def inventory_action(payload, *, action="create", archive_root=DEFAULT_ARCHIVE_ROOT):
    try:
        if action not in {"create", "locations"}:
            raise ValueError("Neznámá operace knihovny.")
        return (save_inventory_book if action == "create" else assign_inventory_locations)(payload, archive_root=archive_root)
    except ValueError as exc:
        accepted = True
        try:
            accepted = inventory_operation(payload.get("request_id"), archive_root=archive_root)["state"] != "not_found"
        except (ValueError, OSError, FilePersistenceError, KeyError, TypeError, AttributeError):
            pass
        return {"ok": False, "state": "invalid" if not accepted else "unknown", "accepted": accepted, "message": str(exc)}
    except (OSError, FilePersistenceError, KeyError, TypeError):
        return {"ok": False, "state": "unknown", "message": "Výsledek zápisu není ověřený. Obnov stav původního požadavku."}


def inventory_overview(*, archive_root=DEFAULT_ARCHIVE_ROOT):
    try:
        return inventory_books(archive_root=archive_root)
    except (OSError, FilePersistenceError, ValueError, KeyError, TypeError):
        return {"ok": False, "state": "unavailable", "message": "Přehled knih se nepodařilo ověřit."}


def inventory_status(identity, *, archive_root=DEFAULT_ARCHIVE_ROOT):
    try:
        return inventory_operation(identity, archive_root=archive_root)
    except (OSError, FilePersistenceError, ValueError, KeyError, TypeError):
        return {"ok": False, "state": "unknown", "message": "Stav původního zápisu nelze ověřit."}


def inventory_lookup(isbn, *, catalog=CATALOG):
    try:
        isbn = canonical_isbn(isbn)
        try:
            result = catalog.preview(isbn)
        except BookIsbnLookupError:
            return {"ok": True, "found": False, "book": {"isbn": isbn, "title": "", "author": "", "cover_url": cover_url(isbn)},
                    "message": "Katalog není dostupný nebo knihu nenašel. Doplň název ručně."}
        return {"ok": True, "found": True, "book": result}
    except ValueError as exc:
        return {"ok": False, "state": "invalid", "message": str(exc)}


def book_inventory_get_route(parsed, handler):
    prefix = "/assets/book-scanner/3.1.6/"
    if parsed.path.startswith(prefix):
        name = parsed.path[len(prefix):]
        if name not in SCANNER_ASSETS or parsed.query:
            handler.respond_json({"ok": False, "message": "Soubor nebyl nalezen."}, status=404)
        else:
            handler.respond_local_file_bytes(target=ASSETS / name, content_type=SCANNER_ASSETS[name], filename=name)
        return True
    if parsed.path not in BOOK_INVENTORY_GET_PATHS:
        return False
    query = parse_qs(parsed.query, keep_blank_values=True)
    key = "request_id" if parsed.path.endswith("quick-status") else "isbn"
    expected = set() if parsed.path.endswith("/inventory") else {key}
    if set(query) != expected or any(len(v) != 1 for v in query.values()):
        handler.respond_json({"ok": False, "message": "Neplatný dotaz knihovny."}, status=400)
    else:
        result = (inventory_overview() if not expected else inventory_status(query[key][0])
                  if key == "request_id" else inventory_lookup(query[key][0]))
        handler.respond_json(result, status=200 if result.get("ok") else 400)
    return True
