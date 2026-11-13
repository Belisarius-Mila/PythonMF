import json
import multiprocessing
import os
from pathlib import Path
import tempfile
import subprocess
import threading
import unittest
from unittest.mock import Mock, patch
from urllib.parse import urlparse

from app import article_archive as archive
from app import book_inventory as books
from app import cockpit_book_inventory as routes
from app.book_isbn_lookup import BookIsbnNotFoundError, lookup_book_preview, lookup_book_by_isbn


def crash_before_registry(root, payload):
    with patch.object(archive, "update_registry", side_effect=lambda *_: os._exit(75)):
        books.save_inventory_book(payload, archive_root=Path(root))


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.payload = {"request_id": "book_inventory_test_0001", "isbn": "0385472579", "title": "Test book"}

    def save(self, **changes):
        return books.save_inventory_book({**self.payload, **changes}, archive_root=self.root)

    def locations(self, rows, location="Shelf 1", identity="location_inventory_test_001"):
        return books.assign_inventory_locations({"request_id": identity, "items": [{"id": r["id"], "revision": r["revision"]} for r in rows], "location": location}, archive_root=self.root)

    def test_basic_card_roundtrip_search_and_empty_text(self):
        r = self.save(); item = r["item"]
        self.assertEqual(item["book_isbn"], "9780385472579")
        self.assertEqual(item["book_location"], "")
        self.assertEqual(item["book_author"], "")
        self.assertEqual(item["book_record_state"], "basic")
        self.assertEqual(archive.get_article(article_id=item["id"], archive_root=self.root)["text"], "")
        self.assertEqual(archive.search_articles(query="0385472579", archive_root=self.root)["count"], 1)
        self.assertEqual(books.inventory_books(archive_root=self.root)["missing_location_count"], 1)

    def test_replay_returns_same_card_and_changed_payload_rejected(self):
        item = self.save()["item"]
        self.assertEqual(self.save()["item"]["id"], item["id"])
        with self.assertRaises(ValueError): self.save(title="Different intent")
        self.assertEqual(len(archive.load_article_registry(self.root)), 1)

    def test_isbn10_13_duplicate_and_intentional_copy(self):
        self.save()
        duplicate = self.save(request_id="book_inventory_test_0002", isbn="9780385472579")
        self.assertEqual(duplicate["state"], "duplicate")
        self.assertEqual(len(duplicate["existing"]), 1)
        self.save(request_id="book_inventory_test_0002", additional_copy=True)
        self.assertEqual(len(archive.load_article_registry(self.root)), 2)

    def test_concurrent_same_isbn_creates_one_card(self):
        barrier = threading.Barrier(2); results = []
        def run(n):
            barrier.wait()
            results.append(self.save(request_id=f"book_concurrent_test_{n}"))
        threads = [threading.Thread(target=run, args=(n,)) for n in (1, 2)]
        for t in threads: t.start()
        for t in threads: t.join(10)
        self.assertEqual(sorted(r["state"] for r in results), ["done", "duplicate"])
        self.assertEqual(len(archive.load_article_registry(self.root)), 1)

    def test_invalid_input_cannot_create_card(self):
        for value in ("4006381333931", "9780385472570", "", "not-isbn", 123):
            with self.subTest(value=value), self.assertRaises(ValueError): self.save(isbn=value)
        for values in ({"request_id": "bad"}, {"title": ""}, {"additional_copy": "yes"}, {"cover_url": "https://evil.example"}):
            with self.subTest(values=values), self.assertRaises(ValueError): self.save(**values)
        self.assertFalse((self.root / "registry.jsonl").exists())

    def test_crash_before_publish_resumes_reserved_bytes_once(self):
        context = multiprocessing.get_context("fork")
        process = context.Process(target=crash_before_registry, args=(str(self.root), self.payload))
        process.start(); process.join(10)
        self.assertEqual(process.exitcode, 75)
        before = {p.name: p.read_bytes() for p in self.root.glob("*.json")}
        status = books.inventory_operation(self.payload["request_id"], archive_root=self.root)
        self.assertEqual(status["state"], "pending")
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.glob("*.json")})
        self.save(); self.save()
        self.assertEqual(len(archive.load_article_registry(self.root)), 1)

    def test_lost_ack_after_registry_is_readable_without_another_save(self):
        write = books.atomic_write_json
        def fail_final(path, value):
            if path.name == "inventory_operations.json" and any(x["state"] == "done" for x in value["operations"].values()):
                raise OSError("disk result unknown")
            return write(path, value)
        with patch.object(books, "atomic_write_json", side_effect=fail_final), self.assertRaises(OSError): self.save()
        r = books.inventory_operation(self.payload["request_id"], archive_root=self.root)
        self.assertEqual(r["state"], "done")
        self.assertEqual(len(archive.load_article_registry(self.root)), 1)

    def test_replay_does_not_overwrite_later_edit_or_resurrect_removed_card(self):
        item = self.save()["item"]
        archive.update_article(article_id=item["id"], title="Changed", text="", category="books", archive_root=self.root)
        self.assertEqual(self.save()["item"]["title"], "Changed")
        archive.remove_from_registry(self.root / "registry.jsonl", item["id"])
        self.assertEqual(self.save()["state"], "unavailable")
        self.assertEqual(books.inventory_operation(self.payload["request_id"], archive_root=self.root)["state"], "unavailable")
        self.assertFalse(archive.load_article_registry(self.root))

    def test_locations_single_bulk_and_idempotent_replay(self):
        self.save(); self.save(request_id="book_inventory_test_0002", additional_copy=True)
        rows = books.inventory_books(archive_root=self.root)["items"]
        result = self.locations(rows)
        self.assertEqual(len(result["updated_ids"]), 2)
        self.assertEqual(books.inventory_books(archive_root=self.root)["missing_location_count"], 0)
        self.assertEqual(self.locations(rows), result)
        with self.assertRaises(ValueError): self.locations(rows, location="Other intent")

    def test_locations_reject_all_before_write_on_stale_revision(self):
        self.save(); self.save(request_id="book_inventory_test_0002", additional_copy=True)
        rows = books.inventory_books(archive_root=self.root)["items"]
        archive.update_article(article_id=rows[1]["id"], title="Changed", text="", category="books", archive_root=self.root)
        with self.assertRaises(ValueError): self.locations(rows)
        self.assertTrue(all(not x.book_location for x in archive.load_article_registry(self.root)))

    def test_partial_location_failure_resumes_without_overwriting_foreign_edit(self):
        self.save(); self.save(request_id="book_inventory_test_0002", additional_copy=True)
        rows = books.inventory_books(archive_root=self.root)["items"]
        write = books.atomic_write_json
        def fail_second(path, value):
            if path.name == "metadata.json" and path.parent.name == rows[1]["id"]: raise OSError("disk")
            return write(path, value)
        with patch.object(books, "atomic_write_json", side_effect=fail_second), self.assertRaises(OSError): self.locations(rows)
        self.assertEqual(books.inventory_books(archive_root=self.root)["missing_location_count"], 1)
        self.locations(rows)
        self.assertEqual(books.inventory_books(archive_root=self.root)["missing_location_count"], 0)
        # A later user change survives another replay of the old batch.
        archive.update_article(article_id=rows[0]["id"], title="Changed", text="", category="books", book_location="New shelf", archive_root=self.root)
        self.locations(rows)
        self.assertEqual(archive.find_article(rows[0]["id"], archive_root=self.root).book_location, "New shelf")

    def test_basic_editor_preserves_missing_fields_and_clears_wrong_cover(self):
        item = self.save()["item"]
        r = archive.update_article(article_id=item["id"], title="Changed", text="", category="books", book_isbn="9788025229033", archive_root=self.root)
        self.assertEqual(r["item"]["book_cover_url"], "")
        self.assertEqual(r["item"]["book_location"], "")
        r = archive.update_article(article_id=item["id"], title="Changed", text="Real summary", category="books", book_author="Author", book_location="Shelf", archive_root=self.root)
        self.assertEqual(r["item"]["book_record_state"], "")
        with self.assertRaises(ValueError): archive.update_article(article_id=item["id"], title="Changed", text="", category="books", archive_root=self.root)

    def test_corrupt_identity_store_is_not_overwritten(self):
        path = self.root / "inventory_operations.json"; path.write_text('{"version":1,"operations":{"old":null}}')
        with self.assertRaises(ValueError): self.save()
        self.assertIn('"old":null', path.read_text())

    def test_corrupt_registry_is_not_silently_rewritten(self):
        path = self.root / "registry.jsonl"; path.write_text('{broken}\n')
        with self.assertRaises(ValueError): self.save()
        self.assertEqual(path.read_text(), '{broken}\n')

    def test_partial_batch_with_foreign_edit_reports_conflict_and_preserves_it(self):
        self.save(); self.save(request_id="book_inventory_test_0002", additional_copy=True)
        rows = books.inventory_books(archive_root=self.root)["items"]
        write = books.atomic_write_json
        def fail_second(path, value):
            if path.name == "metadata.json" and path.parent.name == rows[1]["id"]: raise OSError("disk")
            return write(path, value)
        with patch.object(books, "atomic_write_json", side_effect=fail_second), self.assertRaises(OSError): self.locations(rows)
        archive.update_article(article_id=rows[0]["id"], title="New title", text="", category="books", book_location="New shelf", archive_root=self.root)
        state = books.inventory_operation("location_inventory_test_001", archive_root=self.root)
        self.assertEqual(state["state"], "conflict")
        with self.assertRaises(ValueError): self.locations(rows)
        self.assertEqual(archive.find_article(rows[0]["id"], archive_root=self.root).book_location, "New shelf")
        self.assertEqual(archive.find_article(rows[1]["id"], archive_root=self.root).book_location, "")

    def test_route_input_and_safe_recovery(self):
        r = routes.inventory_action({**self.payload, "title": ""}, archive_root=self.root)
        self.assertFalse(r["ok"])
        self.assertFalse(r["accepted"])
        self.assertEqual(routes.inventory_action(self.payload, archive_root=self.root)["state"], "done")
        self.assertEqual(routes.inventory_status(self.payload["request_id"], archive_root=self.root)["state"], "done")


class CatalogTests(unittest.TestCase):
    def test_frontend_behavior(self):
        from scripts.cockpit_quality_gate import node_binary
        result = subprocess.run([node_binary(), str(Path(__file__).with_name("book_quick_add.test.cjs"))], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
    def test_fast_primary_does_not_wait_for_enrichment(self):
        with patch("app.book_isbn_lookup._lookup_book_in_knihovny", return_value={"isbn": "0385472579", "title": "Book"}), patch("app.book_isbn_lookup._lookup_book_in_open_library") as secondary:
            r = lookup_book_preview(isbn="0385472579")
            secondary.assert_not_called()
            self.assertEqual(r["isbn"], "9780385472579")
            self.assertTrue(r["cover_url"].endswith("/9780385472579-S.jpg?default=false"))
            lookup_book_by_isbn(isbn="0385472579")
            secondary.assert_called_once()

    def test_fallback_unchanged_and_invalid_book_prefix_before_network(self):
        with patch("app.book_isbn_lookup._lookup_book_in_knihovny", side_effect=BookIsbnNotFoundError("none")), patch("app.book_isbn_lookup._lookup_book_in_open_library", return_value={"title": "Fallback"}) as fallback:
            self.assertEqual(lookup_book_preview(isbn="0385472579")["title"], "Fallback")
            with self.assertRaises(ValueError): lookup_book_preview(isbn="4006381333931")
            fallback.assert_called_once()

    def test_cache_canonical_alias_expiry_and_bound(self):
        lookup = Mock(return_value={"isbn": "9780385472579", "title": "Book"}); at = [0]
        cache = books.CatalogPreview(lookup=lookup, clock=lambda: at[0])
        self.assertFalse(cache.preview("0385472579")["cached"])
        self.assertTrue(cache.preview("9780385472579")["cached"])
        self.assertEqual(lookup.call_count, 1)
        at[0] = 86401; cache.preview("0385472579")
        self.assertEqual(lookup.call_count, 2)

    def test_unavailable_catalog_allows_manual_title(self):
        fake = Mock(); fake.preview.side_effect = BookIsbnNotFoundError("none")
        r = routes.inventory_lookup("0385472579", catalog=fake)
        self.assertTrue(r["ok"]); self.assertFalse(r["found"])
        self.assertEqual(r["book"]["title"], "")
        self.assertTrue(r["book"]["cover_url"].startswith("https://covers.openlibrary.org/"))

    def test_http_routes_reject_unknown_query_and_asset_paths(self):
        h = Mock()
        for path in ("/api/library/book/quick-status?request_id=a&request_id=b", "/api/library/books/inventory?extra=1", "/assets/book-scanner/3.1.6/../secret", "/assets/book-scanner/3.1.6/reader.js?x=1"):
            self.assertTrue(routes.book_inventory_get_route(urlparse(path), h))
            self.assertFalse(h.respond_json.call_args.args[0]["ok"])
        self.assertFalse(routes.book_inventory_get_route(urlparse("/api/other"), h))
        self.assertTrue(routes.book_inventory_get_route(urlparse("/assets/book-scanner/3.1.6/zxing_reader.wasm"), h))
        self.assertEqual(h.respond_local_file_bytes.call_args.kwargs["content_type"], "application/wasm")


if __name__ == "__main__": unittest.main()
