"""Quick inventory cards in the existing archive, with durable request identities."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import re
import threading
import time
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlsplit

from app import article_archive as archive
from app.book_isbn_lookup import isbn10_to_isbn13, lookup_book_preview
from app.book_thumbnail import fetch_thumbnail, MAX_THUMBNAIL_BYTES
from app.file_persistence import atomic_create_bytes, atomic_create_text, atomic_write_json


REQUEST = re.compile(r"[A-Za-z0-9_-]{12,96}")


def canonical_isbn(value):
    if not isinstance(value, str):
        raise ValueError("Zadej ISBN knihy.")
    value = archive.normalize_book_isbn(value)
    if len(value) == 10:
        value = isbn10_to_isbn13(value)
    if not value.startswith(("978", "979")):
        raise ValueError("Zadej knižní ISBN-10 nebo ISBN-13.")
    return value


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def cover_url(isbn):
    return f"https://covers.openlibrary.org/b/isbn/{canonical_isbn(isbn)}-S.jpg?default=false"


def _text(value, limit):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError("Neplatná délka údaje knihy.")
    return " ".join(value.split())


def _operations(root):
    path = root / "inventory_operations.json"
    if not path.exists():
        return {"version": 1, "operations": {}}
    data = json.loads(path.read_text())
    if data.get("version") != 1 or not isinstance(data.get("operations"), dict):
        raise ValueError("Neověřená evidence ukládání knih.")
    for key, operation in data["operations"].items():
        if (not isinstance(key, str) or not REQUEST.fullmatch(key) or not isinstance(operation, dict)
                or operation.get("kind") not in {"create", "locations"}
                or operation.get("state") not in {"prepared", "done"}
                or not re.fullmatch(r"[0-9a-f]{64}", str(operation.get("fingerprint", "")))
                or (operation["kind"] == "create" and not isinstance(operation.get("metadata"), dict))
                or (operation["kind"] == "locations" and not isinstance(operation.get("changes"), list))):
            raise ValueError("Neověřená evidence ukládání knih.")
    return data


def _request(value):
    if not isinstance(value, str) or not REQUEST.fullmatch(value):
        raise ValueError("Chybí identita ukládání.")
    return value


def _validate_registry(root):
    path = root / "registry.jsonl"
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                if not isinstance(row, dict) or not isinstance(row.get("id"), str):
                    raise ValueError("Registr knihovny vyžaduje kontrolu; zápis se neprovedl.")


def _metadata(root, item):
    path = archive.article_metadata_path(item, archive_root=root)
    if path.is_symlink():
        raise ValueError("Neověřená cesta knihy.")
    return json.loads(path.read_text())


def _summary(root, item):
    raw = _metadata(root, item)
    return {**archive.article_item_from_raw(raw).to_summary(), "revision": fingerprint(raw),
            **({"book_cover_status": raw["book_cover_status"]} if "book_cover_status" in raw else {})}


def inventory_books(*, archive_root=archive.DEFAULT_ARCHIVE_ROOT):
    root = Path(archive_root)
    rows = [_summary(root, item) for item in archive.load_article_registry(root) if item.category == "books"]
    rows.sort(key=lambda item: (bool(item["book_location"]), item["title"].casefold(), item["id"]))
    return {"ok": True, "items": rows, "count": len(rows),
            "missing_location_count": sum(not item["book_location"] for item in rows)}


def _existing(root, isbn):
    found = []
    for item in archive.load_article_registry(root):
        if item.category != "books" or not item.book_isbn:
            continue
        try:
            matches = canonical_isbn(item.book_isbn) == isbn
        except ValueError:
            matches = False
        if matches:
            found.append(_summary(root, item))
    return found


def _finish(root, operation):
    """Resume only reserved bytes; never overwrite an intervening user edit."""
    if operation["kind"] == "create":
        raw = operation["metadata"]
        existing = archive.find_article(raw["id"], archive_root=root)
        if existing:
            return {"ok": True, "state": "done", "item": _summary(root, existing)}
        folder = root / "articles" / raw["id"]
        if any(p.is_symlink() for p in (root / "articles", folder)):
            raise ValueError("Neověřená cesta knihy.")
        folder.mkdir(parents=True, exist_ok=True)
        if "cover_bytes" in operation:
            image = base64.b64decode(operation["cover_bytes"], validate=True)
            if not image or len(image) > MAX_THUMBNAIL_BYTES or hashlib.sha256(image).hexdigest() != operation.get("cover_sha256"):
                raise ValueError("Neověřená miniatura rozepsané knihy.")
            image_path = folder / "book_cover.jpg"
            if image_path.is_symlink():
                raise ValueError("Neověřená cesta miniatury.")
            if image_path.exists():
                if image_path.read_bytes() != image:
                    raise ValueError("Rozepsanou miniaturu změnil jiný zápis.")
            else:
                atomic_create_bytes(image_path, image)
        text = folder / "article.txt"
        metadata = folder / "metadata.json"
        if text.exists():
            if text.is_symlink() or text.read_text() != "":
                raise ValueError("Rozepsanou knihu změnil jiný zápis.")
        else:
            atomic_create_text(text, "")
        if metadata.exists():
            if metadata.is_symlink() or json.loads(metadata.read_text()) != raw:
                raise ValueError("Rozepsanou knihu změnil jiný zápis.")
        else:
            atomic_create_text(metadata, json.dumps(raw, ensure_ascii=False) + "\n")
        archive.update_registry(root / "registry.jsonl", raw)
        return {"ok": True, "state": "done", "item": _summary(root, archive.article_item_from_raw(raw))}
    changes = operation["changes"]
    # Check every version before writing any remaining changes.
    for change in changes:
        item = archive.find_article(change["id"], archive_root=root)
        if item is None or fingerprint(_metadata(root, item)) not in (change["old_revision"], fingerprint(change["metadata"])):
            raise ValueError("Knihu mezitím změnil jiný zápis. Obnov přehled.")
    for change in changes:
        item = archive.find_article(change["id"], archive_root=root)
        raw = change["metadata"]
        if fingerprint(_metadata(root, item)) == change["old_revision"]:
            atomic_write_json(archive.article_metadata_path(item, archive_root=root), raw)
        archive.update_registry(root / "registry.jsonl", raw)
    return {"ok": True, "state": "done", "updated_ids": [c["id"] for c in changes]}


@archive._serialized_archive_write
def save_inventory_book(payload, *, archive_root=archive.DEFAULT_ARCHIVE_ROOT):
    if not isinstance(payload, dict) or set(payload) - {"request_id", "isbn", "title", "author", "publication_year", "additional_copy", "categories", "store_cover"}:
        raise ValueError("Neplatný požadavek knihy.")
    identity = _request(payload.get("request_id"))
    isbn = canonical_isbn(payload.get("isbn"))
    title = _text(payload.get("title", ""), 500)
    author = _text(payload.get("author", ""), 300)
    year = archive.normalize_book_publication_year(payload.get("publication_year", ""))
    additional = payload.get("additional_copy", False)
    if not title or type(additional) is not bool:
        raise ValueError("Vyplň název knihy.")
    content = {"kind": "create", "isbn": isbn, "title": title, "author": author,
               "publication_year": year, "additional_copy": additional}
    categories = payload.get("categories", [])
    if not isinstance(categories, list) or len(categories) > 10 or any(not isinstance(x, str) for x in categories):
        raise ValueError("Zadej nejvýše deset kategorií knihy.")
    categories = archive.merge_book_option_values([], [archive.normalize_book_option_value(x) for x in categories if x.strip()])
    store_cover = payload.get("store_cover", False)
    if type(store_cover) is not bool:
        raise ValueError("Neplatný požadavek miniatury.")
    # Preserve the fingerprint of pending requests created by older clients.
    if "categories" in payload:
        content["categories"] = categories
    if "store_cover" in payload:
        content["store_cover"] = store_cover
    root = Path(archive_root)
    _validate_registry(root)
    document = _operations(root)
    operation = document["operations"].get(identity)
    if operation:
        if operation["fingerprint"] != fingerprint(content):
            raise ValueError("Tato identita už patří jinému zápisu.")
        if operation["state"] == "done":
            item = archive.find_article(operation["metadata"]["id"], archive_root=root)
            if item is None:
                return {"ok": False, "state": "unavailable", "message": "Původně uložená kniha už není v knihovně."}
            return {"ok": True, "state": "done", "item": _summary(root, item)}
    else:
        matches = _existing(root, isbn)
        if matches and not additional:
            return {"ok": False, "state": "duplicate", "message": "Tuto knihu už máš.", "existing": matches}
        item_id = "isbn-" + hashlib.sha256(identity.encode()).hexdigest()[:24]
        if (root / "articles" / item_id).exists():
            raise ValueError("Identita rozepsané knihy není ověřená.")
        raw = {"id": item_id, "title": title, "one_line_title": archive.compact_title(title), "category": "books",
               "tags": categories, "source_type": "manual_text", "source_label": "Domácí knihovna", "source_note": "",
               "book_author": author, "book_location": "", "book_isbn": isbn, "book_publication_year": year,
               "book_record_state": "basic", "book_cover_url": cover_url(isbn), "source_url": "", "canonical_url": "",
               "archived_at": datetime.now(timezone.utc).isoformat(), "text_file": f"articles/{item_id}/article.txt",
               "html_file": "", "text_chars": "0", "read_state": "normal", "read_note": "",
               "read_state_updated_at": "", "attachments": []}
        operation = {"kind": "create", "fingerprint": fingerprint(content), "state": "prepared", "metadata": raw}
        if store_cover:
            image, status = fetch_thumbnail(isbn)
            raw["book_cover_status"] = status
            if image:
                relative = f"articles/{item_id}/book_cover.jpg"
                raw["attachments"] = [{"id": "catalog-cover", "label": "Obálka knihy — Open Library",
                    "kind": "image", "role": "book_cover", "mime_type": "image/jpeg",
                    "original_file": relative, "readable_file": relative, "thumb_file": relative,
                    "size_bytes": len(image), "stored_size_bytes": len(image),
                    "note": cover_url(isbn), "created_at": raw["archived_at"]}]
                operation["cover_bytes"] = base64.b64encode(image).decode("ascii")
                operation["cover_sha256"] = hashlib.sha256(image).hexdigest()
        document["operations"][identity] = operation
        atomic_write_json(root / "inventory_operations.json", document)
    result = _finish(root, operation)
    operation["state"] = "done"
    operation.pop("cover_bytes", None)
    operation["result"] = result
    atomic_write_json(root / "inventory_operations.json", document)
    return result


@archive._serialized_archive_write
def assign_inventory_locations(payload, *, archive_root=archive.DEFAULT_ARCHIVE_ROOT):
    if not isinstance(payload, dict) or set(payload) != {"request_id", "items", "location"}:
        raise ValueError("Neplatný požadavek umístění.")
    identity = _request(payload["request_id"])
    location = _text(payload["location"], 300)
    rows = payload["items"]
    if not location or not isinstance(rows, list) or not 1 <= len(rows) <= 100:
        raise ValueError("Vyber knihy a vyplň umístění.")
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {"id", "revision"}
                or not isinstance(row["id"], str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,180}", row["id"])
                or not isinstance(row["revision"], str) or not re.fullmatch(r"[0-9a-f]{64}", row["revision"])):
            raise ValueError("Neplatná verze vybrané knihy.")
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Kniha je vybraná vícekrát.")
    content = {"kind": "locations", "items": rows, "location": location}
    root = Path(archive_root)
    _validate_registry(root)
    document = _operations(root)
    operation = document["operations"].get(identity)
    if operation:
        if operation["fingerprint"] != fingerprint(content):
            raise ValueError("Tato identita už patří jinému zápisu.")
        if operation["state"] == "done":
            return operation["result"]
    else:
        changes = []
        for row in rows:
            item = archive.find_article(row["id"], archive_root=root)
            if item is None or item.category != "books":
                raise ValueError("Vybraná kniha nebyla nalezena.")
            raw = _metadata(root, item)
            if fingerprint(raw) != row["revision"]:
                raise ValueError("Knihu mezitím změnil jiný zápis. Obnov přehled.")
            changes.append({"id": item.id, "old_revision": row["revision"], "metadata": {**raw, "book_location": location}})
        operation = {"kind": "locations", "fingerprint": fingerprint(content), "state": "prepared", "changes": changes}
        document["operations"][identity] = operation
        atomic_write_json(root / "inventory_operations.json", document)
    result = _finish(root, operation)
    operation.update(state="done", result=result)
    atomic_write_json(root / "inventory_operations.json", document)
    return result


@archive._serialized_archive_write
def inventory_operation(identity, *, archive_root=archive.DEFAULT_ARCHIVE_ROOT):
    """Read original identity only. Never create/resume from a status request."""
    identity = _request(identity)
    root = Path(archive_root)
    operation = _operations(root)["operations"].get(identity)
    if not operation:
        return {"ok": True, "state": "not_found"}
    if operation["kind"] == "create":
        item = archive.find_article(operation["metadata"]["id"], archive_root=root)
        if item:
            return {"ok": True, "state": "done", "item": _summary(root, item)}
    elif operation["state"] == "prepared":
        changes = []
        for change in operation["changes"]:
            item = archive.find_article(change["id"], archive_root=root)
            current = fingerprint(_metadata(root, item)) if item else "missing"
            state = "applied" if current == fingerprint(change["metadata"]) else "pending" if current == change["old_revision"] else "changed"
            changes.append({"id": change["id"], "state": state})
        if any(c["state"] == "changed" for c in changes):
            return {"ok": False, "state": "conflict", "changes": changes,
                    "message": "Některé knihy se změnily. Část přiřazení mohla být dokončená; zkontroluj aktuální umístění a vyber knihy znovu."}
    if operation["kind"] == "create" and operation["state"] == "done":
        return {"ok": False, "state": "unavailable", "message": "Původně uložená kniha už není v knihovně."}
    if operation["state"] == "done":
        return operation["result"]
    return {"ok": True, "state": "pending", "message": "Dokončení původního zápisu zatím není ověřené."}


class CatalogPreview:
    """Small in-process cache; serialize public lookup to respect provider limits."""
    def __init__(self, lookup=lookup_book_preview, clock=time.monotonic):
        self.lookup, self.clock, self.cache = lookup, clock, {}
        self.lock = threading.Lock()
        self.last_open_library = 0.0

    def _open(self, request, **kwargs):
        if urlsplit(request.full_url).hostname == "openlibrary.org":
            wait = 1.0 - (time.monotonic() - self.last_open_library)
            if wait > 0:
                time.sleep(wait)
            self.last_open_library = time.monotonic()
        return urllib.request.urlopen(request, **kwargs)

    def preview(self, isbn):
        isbn = canonical_isbn(isbn)
        with self.lock:
            at = self.clock()
            cached = self.cache.get(isbn)
            if cached and at - cached[0] < 86400:
                return {**cached[1], "cached": True}
            result = self.lookup(isbn=isbn, opener=self._open)
            if canonical_isbn(result.get("isbn", "")) != isbn:
                raise ValueError("Katalog vrátil jiné ISBN.")
            result = {**result, "isbn": isbn, "cover_url": cover_url(isbn)}
            if len(self.cache) >= 200:
                self.cache.pop(next(iter(self.cache)))
            self.cache[isbn] = (self.clock(), result)
            return {**result, "cached": False}
