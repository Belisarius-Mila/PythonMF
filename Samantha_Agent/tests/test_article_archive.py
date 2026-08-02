from __future__ import annotations

import gzip
import json
import re
import ssl
import subprocess
import tempfile
import urllib.error
import unittest
from datetime import datetime, timezone
from email import message_from_bytes
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from app.article_archive import (
    ATTACHMENT_CONFIRMATION_PHRASE,
    ATTACHMENT_REMOVE_CONFIRMATION_PHRASE,
    CLEANUP_CONFIRMATION_PHRASE,
    DELETE_CONFIRMATION_PHRASE,
    LIBRARY_EXPORT_EMAIL_MARKER,
    LIBRARY_EXPORT_EMAIL_MARKER_VALUE,
    LIBRARY_EXPORT_SUBJECT_PREFIX,
    archive_book_entry,
    archive_text_entry,
    archive_url,
    article_text_cleanup_report,
    attach_article_image,
    cleanup_article_text,
    decompress_http_body,
    delete_article,
    extract_article,
    fetch_url,
    get_article,
    get_article_attachment,
    library_export_confirmation_text,
    list_articles,
    prepare_article_pdf_export,
    preview_article_source_reextract,
    search_articles,
    send_article_pdf_export,
    set_article_read_state,
    trim_to_article_body,
    update_article,
    update_article_attachment,
    remove_article_attachment,
)
from app.email.config import OutgoingMailConfig
from app.email.outbound import SentCopyResult

try:
    from PIL import Image
except ModuleNotFoundError:  # pragma: no cover - depends on local environment setup
    Image = None

try:
    import reportlab  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - depends on local environment setup
    HAS_REPORTLAB = False
else:
    HAS_REPORTLAB = True


class ArticleArchiveTests(unittest.TestCase):
    def test_update_article_changes_editable_fields_and_preserves_attachments(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            created = archive_text_entry(
                title="Původní název",
                text="Původní text článku.",
                category="other",
                tags=["puvodni"],
                source_label="Vložený text",
                archive_root=archive_root,
            )
            article_id = created["item"]["id"]
            metadata_path = archive_root / "articles" / article_id / "metadata.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["attachments"] = [{
                "id": "foto-1",
                "label": "Fotografie",
                "kind": "image",
                "role": "supporting_image",
                "mime_type": "image/jpeg",
                "original_file": "",
                "readable_file": "",
                "thumb_file": "",
                "size_bytes": 10,
                "note": "",
                "created_at": "2026-07-16T10:00:00+00:00",
            }]
            metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (archive_root / "registry.jsonl").write_text(json.dumps(metadata, ensure_ascii=False) + "\n", encoding="utf-8")

            result = update_article(
                article_id=article_id,
                title="Nový název",
                text="Upravený text článku s fotografií.",
                category="science",
                tags=["věda", "upraveno"],
                source_label="Mílova poznámka",
                source_note="Ověřená lokální úprava.",
                archive_root=archive_root,
                now=datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc),
            )
            loaded = get_article(article_id=article_id, archive_root=archive_root, max_chars=0)

        self.assertTrue(result["ok"])
        self.assertEqual(loaded["item"]["title"], "Nový název")
        self.assertEqual(loaded["item"]["category"], "science")
        self.assertEqual(loaded["item"]["tags"], ["věda", "upraveno", "ma-obrazek"])
        self.assertEqual(loaded["item"]["attachment_count"], 1)
        self.assertEqual(loaded["text"], "Upravený text článku s fotografií.")

    def test_update_attachment_changes_only_label_and_note(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root, article_id, _files = self.make_article_with_attachment(Path(temp_dir))

            result = update_article_attachment(
                article_id=article_id,
                attachment_id="foto-1",
                label="Nový popisek fotografie",
                note="Pohled od severu.",
                archive_root=archive_root,
                now=datetime(2026, 7, 16, 12, 5, tzinfo=timezone.utc),
            )
            loaded = get_article(article_id=article_id, archive_root=archive_root)

        self.assertTrue(result["ok"])
        attachment = loaded["item"]["attachments"][0]
        self.assertEqual(attachment["label"], "Nový popisek fotografie")
        self.assertEqual(attachment["note"], "Pohled od severu.")
        self.assertTrue(attachment["has_original"])
        self.assertTrue(attachment["has_readable"])
        self.assertTrue(attachment["has_thumb"])

    def test_remove_attachment_requires_exact_phrase_and_moves_files_to_trash(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root, article_id, files = self.make_article_with_attachment(Path(temp_dir))
            with self.assertRaisesRegex(ValueError, ATTACHMENT_REMOVE_CONFIRMATION_PHRASE):
                remove_article_attachment(
                    article_id=article_id,
                    attachment_id="foto-1",
                    archive_root=archive_root,
                    user_confirmed=True,
                    confirmation_text="ano",
                )
            self.assertTrue(all(path.exists() for path in files))

            result = remove_article_attachment(
                article_id=article_id,
                attachment_id="foto-1",
                archive_root=archive_root,
                user_confirmed=True,
                confirmation_text=ATTACHMENT_REMOVE_CONFIRMATION_PHRASE,
                now=datetime(2026, 7, 16, 12, 10, tzinfo=timezone.utc),
            )
            loaded = get_article(article_id=article_id, archive_root=archive_root)
            trash_manifests = list((archive_root / "trash" / "attachments").glob("*/removed_attachment.json"))
            files_were_moved = all(not path.exists() for path in files)
            trash_manifest_count = len(trash_manifests)

        self.assertTrue(result["ok"])
        self.assertTrue(files_were_moved)
        self.assertEqual(loaded["item"]["attachment_count"], 0)
        self.assertNotIn("ma-obrazek", loaded["item"]["tags"])
        self.assertEqual(trash_manifest_count, 1)

    def make_article_with_attachment(self, archive_root: Path) -> tuple[Path, str, list[Path]]:
        created = archive_text_entry(
            title="Článek s fotografií",
            text="Text k fotografii.",
            category="travel_places",
            tags=["ma-obrazek"],
            archive_root=archive_root,
        )
        article_id = created["item"]["id"]
        article_dir = archive_root / "articles" / article_id
        files = [
            article_dir / "attachments" / "original" / "foto-1.png",
            article_dir / "attachments" / "readable" / "foto-1.jpg",
            article_dir / "attachments" / "thumbs" / "foto-1.jpg",
        ]
        for index, path in enumerate(files, start=1):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"image-{index}".encode("ascii"))
        metadata_path = article_dir / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["attachments"] = [{
            "id": "foto-1",
            "label": "Ilustrační foto",
            "kind": "image",
            "role": "supporting_image",
            "mime_type": "image/png",
            "original_file": str(files[0].relative_to(archive_root)),
            "readable_file": str(files[1].relative_to(archive_root)),
            "thumb_file": str(files[2].relative_to(archive_root)),
            "size_bytes": files[0].stat().st_size,
            "note": "Původní poznámka.",
            "created_at": "2026-07-16T10:00:00+00:00",
        }]
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (archive_root / "registry.jsonl").write_text(json.dumps(metadata, ensure_ascii=False) + "\n", encoding="utf-8")
        return archive_root, article_id, files

    def test_lists_searches_and_reads_private_article_archive(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            article_dir = archive_root / "articles" / "article-1"
            article_dir.mkdir(parents=True)
            (article_dir / "article.txt").write_text(
                "Jablečný koláč\nTěsto, jablka a skořice.\nPeče se pomalu.",
                encoding="utf-8",
            )
            (archive_root / "registry.jsonl").write_text(
                json.dumps(
                    {
                        "id": "article-1",
                        "title": "Jablečný koláč | test",
                        "one_line_title": "Jablečný koláč",
                        "category": "recipes",
                        "archived_at": "2026-06-10T07:00:00+00:00",
                        "source_url": "https://example.test/recept",
                        "canonical_url": "https://example.test/recept",
                        "text_file": "articles/article-1/article.txt",
                        "html_file": "articles/article-1/source.html",
                        "text_chars": "48",
                        "tags": ["recept"],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            listed = list_articles(category="recipes", archive_root=archive_root)
            searched = search_articles(query="skořice", category="recipes", archive_root=archive_root)
            article = get_article(article_id="article-1", archive_root=archive_root)

        self.assertEqual(listed["count"], 1)
        self.assertEqual(listed["items"][0]["category_label"], "Recepty")
        self.assertEqual(searched["count"], 1)
        self.assertIn("skořice", searched["items"][0]["snippet"])
        self.assertTrue(article["ok"])
        self.assertIn("Jablečný koláč", article["text"])

    def test_archive_url_fetches_and_writes_private_text(self) -> None:
        html = b"""<!doctype html>
<html><head><title>Test clanek | Web</title><link rel="canonical" href="https://example.test/clanek"></head>
<body><nav>Menu</nav><main><h1>Test clanek</h1><p>Prvni odstavec o lepeni dreva.</p></main></body></html>"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            with patch("app.article_archive.fetch_url", return_value=html):
                result = archive_url(
                    url="https://example.test/clanek?utm_source=test",
                    category="science",
                    tags=["test"],
                    archive_root=archive_root,
                )

            listed = list_articles(category="science", archive_root=archive_root)

        self.assertTrue(result["ok"])
        self.assertEqual(result["item"]["category"], "science")
        self.assertEqual(listed["count"], 1)
        self.assertEqual(listed["items"][0]["canonical_url"], "https://example.test/clanek")

    def test_archive_url_respects_http_iso_8859_2_charset_without_meta_tag(self) -> None:
        html = """<!doctype html>
<html>
<head><title>Český vědecký článek</title></head>
<body><main><p>Příliš žluťoučký kůň úpěl ďábelské ódy.</p></main></body>
</html>""".encode("iso-8859-2")

        class FakeResponse:
            headers = {"Content-Type": "text/html; charset=ISO-8859-2"}

            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, *_args: object) -> None:
                return None

            def read(self) -> bytes:
                return html

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            with patch("urllib.request.urlopen", return_value=FakeResponse()):
                result = archive_url(
                    url="https://example.test/veda",
                    category="science",
                    archive_root=archive_root,
                )
            article = get_article(
                article_id=result["item"]["id"],
                archive_root=archive_root,
                max_chars=0,
            )

        self.assertEqual(result["item"]["title"], "Český vědecký článek")
        self.assertEqual(article["text"], "Příliš žluťoučký kůň úpěl ďábelské ódy.")

    def test_archive_url_decompresses_gzip_before_utf8_decoding_and_saves_html(self) -> None:
        html = """<!doctype html>
<html>
<head><meta charset="utf-8"><title>Český gzip článek</title></head>
<body><main><p>Příliš žluťoučký kůň zůstal po rozbalení čitelný.</p></main></body>
</html>""".encode("utf-8")
        compressed_html = gzip.compress(html)

        class FakeResponse:
            headers = {
                "Content-Type": "text/html",
                "Content-Encoding": "gzip",
            }

            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, *_args: object) -> None:
                return None

            def read(self) -> bytes:
                return compressed_html

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            with patch("urllib.request.urlopen", return_value=FakeResponse()):
                result = archive_url(
                    url="https://example.test/gzip-veda",
                    category="science",
                    archive_root=archive_root,
                )
            article_id = result["item"]["id"]
            article = get_article(
                article_id=article_id,
                archive_root=archive_root,
                max_chars=0,
            )
            saved_source = (
                archive_root / "articles" / article_id / "source.html"
            ).read_bytes()

        self.assertEqual(saved_source, html)
        self.assertEqual(result["item"]["title"], "Český gzip článek")
        self.assertEqual(
            article["text"],
            "Příliš žluťoučký kůň zůstal po rozbalení čitelný.",
        )

    def test_extract_article_reads_legacy_gzip_source_and_enforces_size_limit(self) -> None:
        html = """<!doctype html>
<html><head><meta charset="utf-8"><title>Starší gzip zdroj</title></head>
<body><main><p>Text z dříve uloženého gzip source.html.</p></main></body></html>""".encode("utf-8")
        compressed_html = gzip.compress(html)

        article = extract_article(compressed_html, "https://example.test/legacy-gzip")

        self.assertEqual(article.title, "Starší gzip zdroj")
        self.assertEqual(article.text, "Text z dříve uloženého gzip source.html.")
        with self.assertRaisesRegex(OSError, "bezpečný velikostní limit"):
            decompress_http_body(
                gzip.compress(b"x" * 128),
                content_encoding="gzip",
                max_decompressed_bytes=64,
            )

    def test_extract_article_prefers_main_content_over_footer_title_duplicate(self) -> None:
        html = """<!doctype html>
<html>
<head><title>Krátký titulek z metadat</title></head>
<body>
<nav>Hlavní stránka</nav>
<div>Hlavní obsah</div>
<h1>Skutečný nadpis článku</h1>
<p>První skutečný odstavec článku s důležitým obsahem.</p>
<p>Druhý skutečný odstavec článku.</p>
<h2>Diskuze</h2>
<footer>Krátký titulek z metadat</footer>
</body>
</html>"""

        article = extract_article(html.encode("utf-8"), "https://example.test/clanek")

        self.assertIn("První skutečný odstavec článku", article.text)
        self.assertIn("Druhý skutečný odstavec článku", article.text)
        self.assertNotEqual(article.text, "Krátký titulek z metadat")

    def test_extract_article_respects_declared_windows_1250_and_prefers_clanek_block(self) -> None:
        html = """<!doctype html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=windows-1250">
<title>GVT: Jak zvýšit velikost svalů německým objemovým tréninkem</title>
</head>
<body>
<div class="sidebar">NOVÉ INZERÁTY Osobní trenér do fitness.</div>
<div id=clanek>
<p>Chcete vyzkoušet trénink, který prověří Vaši disciplínu i výkonnost?</p>
<h2>Co je GVT?</h2>
<p>German Volume Training je silově-tréninková metoda pro růst svalové hmoty.</p>
</div>
<div>Diskuse k článku: reklama a komentáře.</div>
</body>
</html>""".encode("windows-1250")

        article = extract_article(html, "https://kulturistika.example.test/clanek")

        self.assertEqual(article.title, "GVT: Jak zvýšit velikost svalů německým objemovým tréninkem")
        self.assertIn("prověří Vaši disciplínu", article.text)
        self.assertIn("Co je GVT?", article.text)
        self.assertIn("silově-tréninková metoda", article.text)
        self.assertNotIn("NOVÉ INZERÁTY", article.text)
        self.assertNotIn("Diskuse k článku", article.text)

    def test_archive_text_entry_saves_searchable_item_without_url(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            result = archive_text_entry(
                title="Samanthin perník",
                text="Suroviny:\nMouka, kakao a med.\nPostup:\nPeč pomalu.",
                category="recipes",
                tags=["recept", "chatgpt"],
                source_label="ChatGPT historický chat",
                source_note="Syntetizovaný recept bez původní URL.",
                archive_root=archive_root,
            )
            item_id = result["item"]["id"]
            listed = list_articles(category="recipes", archive_root=archive_root)
            searched = search_articles(query="kakao med", category="recipes", archive_root=archive_root)
            article = get_article(article_id=item_id, archive_root=archive_root)

        self.assertTrue(result["ok"])
        self.assertEqual(result["item"]["source_type"], "manual_text")
        self.assertEqual(result["item"]["source_label"], "ChatGPT historický chat")
        self.assertEqual(result["item"]["source_url"], "")
        self.assertEqual(listed["count"], 1)
        self.assertEqual(searched["count"], 1)
        self.assertTrue(article["ok"])
        self.assertIn("Mouka, kakao a med", article["text"])
        self.assertEqual(article["item"]["source_note"], "Syntetizovaný recept bez původní URL.")

    def test_search_includes_tags_source_label_and_source_note(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            result = archive_text_entry(
                title="Neutrální znalostní karta",
                text="Obecný text bez hledaných metadat.",
                category="other",
                tags=["unikatni-tag"],
                source_label="Rodinný zápisník",
                source_note="Přepis ověřit podle originálu.",
                archive_root=archive_root,
            )

            by_tag = search_articles(query="unikatni-tag", category="all", archive_root=archive_root)
            by_source = search_articles(query="zápisník", category="all", archive_root=archive_root)
            by_source_note = search_articles(query="originálu", category="all", archive_root=archive_root)

        self.assertEqual(by_tag["items"][0]["id"], result["item"]["id"])
        self.assertEqual(by_source["items"][0]["id"], result["item"]["id"])
        self.assertEqual(by_source_note["items"][0]["id"], result["item"]["id"])

    def test_get_article_reports_truncation_and_can_return_full_text(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            result = archive_text_entry(
                title="Dlouhá karta",
                text="0123456789ABCDEFGHIJ",
                archive_root=archive_root,
            )
            item_id = result["item"]["id"]

            shortened = get_article(article_id=item_id, archive_root=archive_root, max_chars=10)
            exact_length = get_article(article_id=item_id, archive_root=archive_root, max_chars=20)
            full = get_article(article_id=item_id, archive_root=archive_root, max_chars=0)

        self.assertTrue(shortened["truncated"])
        self.assertEqual(shortened["text"], "0123456789")
        self.assertFalse(exact_length["truncated"])
        self.assertEqual(exact_length["text"], "0123456789ABCDEFGHIJ")
        self.assertFalse(full["truncated"])
        self.assertEqual(full["text"], "0123456789ABCDEFGHIJ")

    def test_set_article_read_state_updates_metadata_and_registry(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            result = archive_text_entry(
                title="Důležitý článek",
                text="Text článku, ke kterému se chci vrátit.",
                category="health_info",
                archive_root=archive_root,
            )
            item_id = result["item"]["id"]

            marked = set_article_read_state(
                article_id=item_id,
                read_state="to_read",
                note="Vrátit se k tomu.",
                archive_root=archive_root,
            )
            listed = list_articles(category="health_info", archive_root=archive_root)
            to_read = list_articles(category="all", read_state="to_read", archive_root=archive_root)
            cleared = set_article_read_state(
                article_id=item_id,
                read_state="normal",
                note="Tahle poznámka se má zahodit.",
                archive_root=archive_root,
            )

        self.assertTrue(marked["ok"])
        self.assertEqual(marked["item"]["category"], "health_info")
        self.assertEqual(marked["item"]["category_label"], "Zdravotní informace")
        self.assertEqual(listed["category"], "health_info")
        self.assertEqual(listed["category_label"], "Zdravotní informace")
        self.assertEqual(listed["count"], 1)
        self.assertEqual(marked["item"]["read_state"], "to_read")
        self.assertEqual(marked["item"]["read_note"], "Vrátit se k tomu.")
        self.assertEqual(listed["items"][0]["read_state"], "to_read")
        self.assertEqual(to_read["count"], 1)
        self.assertEqual(to_read["items"][0]["id"], item_id)
        self.assertEqual(cleared["item"]["read_state"], "normal")
        self.assertEqual(cleared["item"]["read_note"], "")

    def test_health_info_category_accepts_czech_label_and_stays_separate_from_other(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            result = archive_text_entry(
                title="Ověřená zdravotní informace",
                text="Syntetická znalostní karta pro test kategorie.",
                category="Zdravotní informace",
                archive_root=archive_root,
            )
            health = list_articles(category="health_info", archive_root=archive_root)
            other = list_articles(category="other", archive_root=archive_root)

        self.assertEqual(result["item"]["category"], "health_info")
        self.assertEqual(result["item"]["category_label"], "Zdravotní informace")
        self.assertEqual(health["count"], 1)
        self.assertEqual(other["count"], 0)

    def test_ai_tools_category_is_supported_for_samantha_knowledge(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            result = archive_text_entry(
                title="Codex Cookbook",
                text="Praktická kuchařka pro práci s Codexem, commity a deployem.",
                category="Samantha / AI nástroje",
                tags=["samantha", "codex"],
                source_label="ChatGPT export review",
                archive_root=archive_root,
            )
            listed = list_articles(category="ai_tools", archive_root=archive_root)
            searched = search_articles(query="Codex deployem", category="ai_tools", archive_root=archive_root)

        self.assertEqual(result["item"]["category"], "ai_tools")
        self.assertEqual(result["item"]["category_label"], "Samantha / AI nástroje")
        self.assertEqual(listed["count"], 1)
        self.assertEqual(searched["count"], 1)

    def test_travel_places_category_is_supported_for_destinations(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            result = archive_text_entry(
                title="Méně známé místo k návštěvě",
                text="Krátká cestovní poznámka o zajímavém místě mimo masovou turistiku.",
                category="Cestování / místa",
                tags=["cestování", "destinace"],
                source_label="ChatGPT export review",
                archive_root=archive_root,
            )
            listed = list_articles(category="travel_places", archive_root=archive_root)
            searched = search_articles(query="masovou turistiku", category="travel_places", archive_root=archive_root)

        self.assertEqual(result["item"]["category"], "travel_places")
        self.assertEqual(result["item"]["category_label"], "Cestování / místa")
        self.assertEqual(listed["count"], 1)
        self.assertEqual(searched["count"], 1)

    def test_books_store_structured_metadata_and_search_author_location_and_summary(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            result = archive_book_entry(
                title="Syntetická cesta krajinou",
                author="Anna Testovací",
                summary="Stručný obsah o putování, paměti míst a rodinné historii.",
                location="Obývák, levá knihovna, druhá police",
                tags=["historie", "cestování"],
                archive_root=archive_root,
            )
            listed = list_articles(category="knihy", archive_root=archive_root)
            by_author = search_articles(
                query="Anna Testovací",
                category="books",
                archive_root=archive_root,
            )
            by_location = search_articles(
                query="druhá police",
                category="books",
                archive_root=archive_root,
            )
            by_summary = search_articles(
                query="paměti míst",
                category="books",
                archive_root=archive_root,
            )

        self.assertEqual(result["item"]["category"], "books")
        self.assertEqual(result["item"]["category_label"], "Knihy")
        self.assertEqual(result["item"]["book_author"], "Anna Testovací")
        self.assertEqual(
            result["item"]["book_location"],
            "Obývák, levá knihovna, druhá police",
        )
        self.assertEqual(listed["count"], 1)
        self.assertEqual(by_author["count"], 1)
        self.assertEqual(by_location["count"], 1)
        self.assertEqual(by_summary["count"], 1)

    def test_book_requires_title_author_summary_and_location(self) -> None:
        required_fields = {
            "title": "Uveď název knihy",
            "author": "Uveď autora knihy",
            "summary": "Vlož stručný obsah knihy",
            "location": "Uveď umístění knihy",
        }
        complete = {
            "title": "Testovací kniha",
            "author": "Testovací autor",
            "summary": "Stručný syntetický obsah.",
            "location": "Testovací police",
        }
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            for field, message in required_fields.items():
                payload = {**complete, field: ""}
                with self.subTest(field=field):
                    with self.assertRaisesRegex(ValueError, message):
                        archive_book_entry(
                            **payload,
                            archive_root=Path(temp_dir),
                        )

    def test_update_book_preserves_structured_metadata_in_registry(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            created = archive_book_entry(
                title="Původní kniha",
                author="Původní autor",
                summary="Původní stručný obsah.",
                location="První police",
                archive_root=archive_root,
            )
            article_id = created["item"]["id"]
            updated = update_article(
                article_id=article_id,
                title="Upravená kniha",
                text="Upravený stručný obsah knihy.",
                category="books",
                book_author="Nový autor",
                book_location="Pracovna, třetí police",
                archive_root=archive_root,
            )
            reloaded = get_article(
                article_id=article_id,
                archive_root=archive_root,
                max_chars=0,
            )

        self.assertEqual(updated["item"]["book_author"], "Nový autor")
        self.assertEqual(
            reloaded["item"]["book_location"],
            "Pracovna, třetí police",
        )
        self.assertEqual(reloaded["text"], "Upravený stručný obsah knihy.")

    def test_trim_to_article_body_removes_recommendations_and_tail_without_losing_article(self) -> None:
        raw_text = "\n".join(
            [
                "Průlom, který oživuje baterie elektromobilů.",
                "Jeden",
                "Báo An Giang•13/06/2026",
                "Sledujte Vietnam.vn na",
                "Google",
                "News",
                "0",
                "Životní cyklus baterií elektromobilů obvykle zahrnuje uzavřený a náročný proces.",
                "Podle webu Interesting Engineering vyvinuli vědci z Cornell University novou metodu.",
                "Profesor Vibha Kalra uvedl, že baterii opraví bez drcení.",
                "Mohlo by vás zajímat",
                "Důležitá kritéria při výběru elektrické motorky pro studenty.",
                "Třicetiletá studie odhaluje zlatý čas pro silový trénink.",
                "Quang Ninh otevřela továrnu na lithium-iontové baterie.",
                "Slibné řešení pro recyklaci baterií elektromobilů.",
                "Metoda DEER umožňuje inženýrům vyjmout elektrody bez poškození.",
                "Tento nový průlom je pozoruhodný vzhledem k rostoucí poptávce po bateriích.",
                "Metoda DEER snižuje náklady a může probíhat lokálně.",
                "Mohlo by vás zajímat",
                "Hovězí rýže s charakteristickým jménem Chau Phong.",
                "Superkondenzátory a technologie nabíjení autobusů.",
                "Hanoj zužuje okruh osob s nárokem na podporu.",
                "Podle Thanhnien.vn",
                "Zdroj: https://example.test/article",
                "Sledujte Vietnam.vn na",
                "Google",
                "News",
                "0",
                "Štítek:Cornellova univerzitaNoviny An Giang",
                "Komentář (0)",
                "Previous",
                "Trendy podle kategorie",
                "Nesouvisející nabídka za článkem.",
            ]
        )

        cleaned = trim_to_article_body(raw_text, "Průlom, který oživuje baterie elektromobilů.")

        self.assertIn("Životní cyklus baterií elektromobilů", cleaned)
        self.assertIn("Metoda DEER umožňuje", cleaned)
        self.assertIn("Metoda DEER snižuje náklady", cleaned)
        self.assertIn("Zdroj: https://example.test/article", cleaned)
        self.assertNotIn("\nJeden\n", f"\n{cleaned}\n")
        self.assertNotIn("Důležitá kritéria při výběru", cleaned)
        self.assertNotIn("Hovězí rýže", cleaned)
        self.assertNotIn("Sledujte Vietnam.vn", cleaned)
        self.assertNotIn("Štítek:", cleaned)
        self.assertNotIn("Komentář", cleaned)
        self.assertNotIn("Nesouvisející nabídka", cleaned)

    def test_trim_to_article_body_keeps_legitimate_commentary_sentence(self) -> None:
        raw_text = "\n".join(
            [
                "Nadpis vědeckého článku",
                "Úvodní odstavec s delším vědeckým obsahem, který vypadá jako skutečný text článku.",
                "Další odstavec s vysvětlením experimentu a výsledků.",
                "Komentář na webu časopisu Nature dal slovo kritikům výzkumu.",
                "Závěrečný odstavec článku, který musí zůstat zachovaný.",
                "Komentář (0)",
                "Previous",
                "Nesouvisející navigace webu.",
            ]
        )

        cleaned = trim_to_article_body(raw_text, "Nadpis vědeckého článku")

        self.assertIn("Komentář na webu časopisu Nature", cleaned)
        self.assertIn("Závěrečný odstavec článku", cleaned)
        self.assertNotIn("Komentář (0)", cleaned)
        self.assertNotIn("Nesouvisející navigace", cleaned)

    def test_trim_to_article_body_removes_inline_related_article_cards(self) -> None:
        raw_text = "\n".join(
            [
                "Nová technologie brýlových čoček",
                "Úvodní odstavec článku s delším obsahem o krátkozrakosti u dětí, který má dost slov na to, aby působil jako skutečný obsah článku.",
                "Další odstavec vysvětluje rizika a proč je vhodné vývoj vady sledovat, včetně dopadů na školu, soustředění a běžný život.",
                "Související titulek o jiné rodinné zdravotní situaci",
                "Dítě a rodina",
                "Třetí odstavec hlavního článku musí zůstat zachovaný.",
                "Jiný související titulek po hlavním textu",
                "Dítě a rodina",
                "Diskuze",
                "Výběr článků",
            ]
        )

        cleaned = trim_to_article_body(raw_text, "Nová technologie brýlových čoček")

        self.assertIn("Úvodní odstavec článku", cleaned)
        self.assertIn("Třetí odstavec hlavního článku", cleaned)
        self.assertNotIn("Související titulek", cleaned)
        self.assertNotIn("Dítě a rodina", cleaned)
        self.assertNotIn("Výběr článků", cleaned)

    def test_cleanup_article_text_rewrites_noisy_saved_article_with_backup(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            article_dir = archive_root / "articles" / "science-noisy"
            article_dir.mkdir(parents=True)
            clean_html = """<!doctype html>
<html><head><title>Čistý vědecký článek</title><link rel="canonical" href="https://example.test/science"></head>
<body>
<main>
<h1>Čistý vědecký článek</h1>
<p>První skutečný odstavec vědeckého článku s dostatečně dlouhým obsahem.</p>
<p>Druhý skutečný odstavec popisuje experiment a jeho hlavní výsledky.</p>
<p>Mohlo by vás zajímat</p>
<p>Nesouvisející doporučení jedna.</p>
<p>Nesouvisející doporučení dvě.</p>
<p>Nesouvisející doporučení tři.</p>
<p>Třetí skutečný odstavec musí po čištění zůstat zachovaný.</p>
<p>Zdroj: https://example.test/source</p>
<p>Komentář (0)</p>
<p>Trendy podle kategorie</p>
<p>Balast za článkem.</p>
</main>
</body></html>"""
            noisy_text = "\n".join(
                [
                    "Čistý vědecký článek",
                    "První skutečný odstavec vědeckého článku s dostatečně dlouhým obsahem.",
                    "Druhý skutečný odstavec popisuje experiment a jeho hlavní výsledky.",
                    "Mohlo by vás zajímat",
                    "Nesouvisející doporučení jedna.",
                    "Nesouvisející doporučení dvě.",
                    "Nesouvisející doporučení tři.",
                    "Třetí skutečný odstavec musí po čištění zůstat zachovaný.",
                    "Zdroj: https://example.test/source",
                    "Komentář (0)",
                    "Trendy podle kategorie",
                    "Balast za článkem.",
                    "Další balast navíc " * 80,
                ]
            )
            (article_dir / "source.html").write_text(clean_html, encoding="utf-8")
            (article_dir / "article.txt").write_text(noisy_text + "\n", encoding="utf-8")
            metadata = {
                "id": "science-noisy",
                "title": "Čistý vědecký článek",
                "one_line_title": "Čistý vědecký článek",
                "category": "science",
                "archived_at": "2026-06-22T10:00:00+00:00",
                "source_url": "https://example.test/science",
                "canonical_url": "https://example.test/science",
                "text_file": "articles/science-noisy/article.txt",
                "html_file": "articles/science-noisy/source.html",
                "text_chars": str(len(noisy_text)),
                "tags": [],
                "attachments": [],
            }
            (article_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (archive_root / "registry.jsonl").write_text(json.dumps(metadata, ensure_ascii=False) + "\n", encoding="utf-8")

            report = article_text_cleanup_report(category="science", archive_root=archive_root)
            cleaned = cleanup_article_text(
                article_id="science-noisy",
                archive_root=archive_root,
                user_confirmed=True,
                confirmation_text=CLEANUP_CONFIRMATION_PHRASE,
            )
            article_text = (article_dir / "article.txt").read_text(encoding="utf-8")
            updated_metadata = json.loads((article_dir / "metadata.json").read_text(encoding="utf-8"))
            registry = json.loads((archive_root / "registry.jsonl").read_text(encoding="utf-8").splitlines()[0])
            backups = list(article_dir.glob("article_before_cleanup_*.txt"))

        self.assertEqual(report["candidate_count"], 1)
        self.assertTrue(cleaned["changed"])
        self.assertEqual(len(backups), 1)
        self.assertIn("Třetí skutečný odstavec", article_text)
        self.assertNotIn("Nesouvisející doporučení", article_text)
        self.assertNotIn("Balast za článkem", article_text)
        self.assertEqual(updated_metadata["text_chars"], registry["text_chars"])
        self.assertEqual(updated_metadata["last_cleanup"]["old_text_chars"], len(noisy_text.strip()))
        self.assertGreater(updated_metadata["last_cleanup"]["removed_chars"], 1000)

    def test_source_reextract_preview_is_read_only_redacted_and_uses_explicit_iso_8859_2(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            article_dir = archive_root / "articles" / "synthetic-iso"
            article_dir.mkdir(parents=True)
            source_html = """<!doctype html>
<html><head><title>Syntetický test</title></head>
<body><main>
<h1>Syntetický test</h1>
<p>Žluťoučký kůň běží přes bezpečně dlouhý syntetický odstavec.</p>
</main></body></html>"""
            source_bytes = source_html.encode("iso-8859-2")
            source_url = "https://synthetic.invalid/private-source"
            wrong_text = extract_article(source_bytes, source_url).text.strip()
            correct_text = extract_article(
                source_bytes,
                source_url,
                http_encoding="iso-8859-2",
            ).text.strip()
            self.assertNotEqual(wrong_text, correct_text)
            (article_dir / "source.html").write_bytes(source_bytes)
            (article_dir / "article.txt").write_text(wrong_text + "\n", encoding="utf-8")
            metadata = {
                "id": "synthetic-iso",
                "title": "Syntetický test",
                "one_line_title": "Syntetický test",
                "category": "science",
                "archived_at": "2026-07-23T10:00:00+00:00",
                "source_url": source_url,
                "canonical_url": source_url,
                "text_file": "articles/synthetic-iso/article.txt",
                "html_file": "articles/synthetic-iso/source.html",
                "text_chars": str(len(wrong_text)),
                "tags": [],
                "attachments": [],
            }
            (article_dir / "metadata.json").write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (archive_root / "registry.jsonl").write_text(
                json.dumps(metadata, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            before = {
                path.relative_to(archive_root): path.read_bytes()
                for path in archive_root.rglob("*")
                if path.is_file()
            }

            result = preview_article_source_reextract(
                article_id="synthetic-iso",
                source_encoding="ISO-8859-2",
                archive_root=archive_root,
            )

            after = {
                path.relative_to(archive_root): path.read_bytes()
                for path in archive_root.rglob("*")
                if path.is_file()
            }

        self.assertEqual(before, after)
        self.assertEqual(
            set(result),
            {"ok", "read_only", "source_encoding", "changed", "metrics"},
        )
        self.assertEqual(
            set(result["metrics"]),
            {
                "source_bytes",
                "current_chars",
                "preview_chars",
                "char_delta",
                "different_positions",
                "current_replacement_chars",
                "preview_replacement_chars",
                "current_control_chars",
                "preview_control_chars",
            },
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["read_only"])
        self.assertTrue(result["changed"])
        self.assertEqual(result["source_encoding"], "iso-8859-2")
        self.assertGreater(result["metrics"]["different_positions"], 0)
        self.assertEqual(result["metrics"]["preview_replacement_chars"], 0)
        serialized = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("Syntetický test", serialized)
        self.assertNotIn(source_url, serialized)
        self.assertNotIn("Žluťoučký", serialized)
        self.assertEqual(list(article_dir.glob("article_before_cleanup_*.txt")), [])

    def test_source_reextract_preview_rejects_implicit_or_other_encoding(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)

            for source_encoding in ("", "utf-8", "windows-1250"):
                with self.subTest(source_encoding=source_encoding):
                    with self.assertRaisesRegex(ValueError, "explicitní kódování ISO-8859-2"):
                        preview_article_source_reextract(
                            article_id="unused",
                            source_encoding=source_encoding,
                            archive_root=archive_root,
                        )

    def test_delete_article_requires_confirmation_and_moves_item_to_trash(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            result = archive_text_entry(
                title="Nevhodný recept",
                text="Toto je testovací položka k vyřazení.",
                category="recipes",
                tags=["test"],
                archive_root=archive_root,
            )
            article_id = result["item"]["id"]

            with self.assertRaises(ValueError):
                delete_article(article_id=article_id, archive_root=archive_root)

            deleted = delete_article(
                article_id=article_id,
                archive_root=archive_root,
                user_confirmed=True,
                confirmation_text=DELETE_CONFIRMATION_PHRASE,
            )
            listed = list_articles(category="recipes", archive_root=archive_root)
            article = get_article(article_id=article_id, archive_root=archive_root)
            trash_dirs = list((archive_root / "trash" / "articles").glob(f"*_{article_id}"))
            trash_article_exists = len(trash_dirs) == 1 and (trash_dirs[0] / "article.txt").exists()
            trash_manifest_exists = len(trash_dirs) == 1 and (trash_dirs[0] / "removed_from_registry.json").exists()

        self.assertTrue(deleted["ok"])
        self.assertEqual(listed["count"], 0)
        self.assertFalse(article["ok"])
        self.assertEqual(len(trash_dirs), 1)
        self.assertTrue(trash_article_exists)
        self.assertTrue(trash_manifest_exists)

    def test_article_attachments_are_listed_and_resolved_inside_archive(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            article_dir = archive_root / "articles" / "family-recipe"
            attachments_dir = article_dir / "attachments" / "readable"
            pdf_dir = article_dir / "attachments" / "original"
            attachments_dir.mkdir(parents=True)
            pdf_dir.mkdir(parents=True)
            (article_dir / "article.txt").write_text("Rodinný recept\nPřepis rukopisu.", encoding="utf-8")
            readable = attachments_dir / "recept_readable.jpg"
            readable.write_bytes(b"fake-jpeg")
            original_pdf = pdf_dir / "recept.pdf"
            original_pdf.write_bytes(b"%PDF-1.4\n")
            (archive_root / "registry.jsonl").write_text(
                json.dumps(
                    {
                        "id": "family-recipe",
                        "title": "Babiččin koláč",
                        "one_line_title": "Babiččin koláč",
                        "category": "recipes",
                        "archived_at": "2026-06-11T10:00:00+00:00",
                        "source_type": "manual_text",
                        "source_label": "Rodinný ručně psaný recept",
                        "source_url": "",
                        "canonical_url": "",
                        "text_file": "articles/family-recipe/article.txt",
                        "html_file": "",
                        "text_chars": "29",
                        "tags": ["rodinny-recept", "rucne-psany", "ma-obrazek"],
                        "attachments": [
                            {
                                "id": "rukopis-1",
                                "label": "Ručně psaný originál",
                                "kind": "image",
                                "role": "handwritten_recipe_scan",
                                "mime_type": "image/jpeg",
                                "readable_file": "articles/family-recipe/attachments/readable/recept_readable.jpg",
                                "note": "Čitelná kopie rukopisu.",
                            },
                            {
                                "id": "pdf-1",
                                "label": "PDF originál",
                                "kind": "pdf",
                                "role": "original_pdf",
                                "mime_type": "application/pdf",
                                "original_file": "articles/family-recipe/attachments/original/recept.pdf",
                                "readable_file": "",
                                "thumb_file": "",
                                "note": "PDF příloha.",
                            }
                        ],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            listed = list_articles(category="recipes", archive_root=archive_root)
            article = get_article(article_id="family-recipe", archive_root=archive_root)
            attachment = get_article_attachment(
                article_id="family-recipe",
                attachment_id="rukopis-1",
                variant="readable",
                archive_root=archive_root,
            )
            pdf_attachment = get_article_attachment(
                article_id="family-recipe",
                attachment_id="pdf-1",
                variant="original",
                archive_root=archive_root,
            )

        self.assertEqual(listed["items"][0]["attachment_count"], 2)
        self.assertEqual(listed["items"][0]["attachment_roles"], ["handwritten_recipe_scan", "original_pdf"])
        self.assertTrue(article["ok"])
        self.assertEqual(article["item"]["attachments"][0]["label"], "Ručně psaný originál")
        self.assertTrue(attachment["ok"])
        self.assertEqual(attachment["path"].name, "recept_readable.jpg")
        self.assertTrue(pdf_attachment["ok"])
        self.assertEqual(pdf_attachment["mime_type"], "application/pdf")

    @unittest.skipIf(Image is None, "Pillow is not installed")
    def test_attach_article_image_writes_original_readable_thumb_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            result = archive_text_entry(
                title="Rodinný koláč",
                text="Přepis ručně psaného receptu.",
                category="recipes",
                tags=["rodinny-recept"],
                source_label="Rodinný ručně psaný recept",
                archive_root=archive_root,
            )
            article_id = result["item"]["id"]
            image_buffer = BytesIO()
            Image.new("RGB", (900, 650), "white").save(image_buffer, format="PNG")

            attached = attach_article_image(
                article_id=article_id,
                image_bytes=image_buffer.getvalue(),
                filename="recept.png",
                label="Rukopis",
                note="Testovací scan.",
                archive_root=archive_root,
                user_confirmed=True,
                confirmation_text=ATTACHMENT_CONFIRMATION_PHRASE,
            )
            article = get_article(article_id=article_id, archive_root=archive_root)
            attachment_id = attached["attachment"]["id"]
            original = get_article_attachment(
                article_id=article_id,
                attachment_id=attachment_id,
                variant="original",
                archive_root=archive_root,
            )
            thumb = get_article_attachment(
                article_id=article_id,
                attachment_id=attachment_id,
                variant="thumb",
                archive_root=archive_root,
            )

        self.assertTrue(attached["ok"])
        self.assertEqual(article["item"]["attachment_count"], 1)
        self.assertIn("ma-obrazek", article["item"]["tags"])
        self.assertTrue(original["ok"])
        self.assertTrue(thumb["ok"])
        self.assertEqual(thumb["path"].suffix, ".jpg")

    @unittest.skipIf(not HAS_REPORTLAB, "ReportLab is not installed")
    def test_prepare_article_pdf_export_writes_pdf_email_and_marker(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            result = archive_text_entry(
                title="Samanthin perník",
                text="Suroviny:\nMouka, kakao a med.\n\nPostup:\nPeč pomalu.",
                category="recipes",
                tags=["recept"],
                archive_root=archive_root,
            )
            article_id = result["item"]["id"]

            prepared = prepare_article_pdf_export(
                article_id=article_id,
                archive_root=archive_root,
                smtp_config_loader=_smtp_config,
            )
            export = prepared["export"]
            pdf_path = Path(export["pdf_path"])
            message_path = Path(export["message_path"])
            metadata_path = Path(export["metadata_path"])
            pdf_exists = pdf_path.exists()
            pdf_size = pdf_path.stat().st_size if pdf_exists else 0
            message_exists = message_path.exists()
            message = message_from_bytes(message_path.read_bytes())
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        self.assertTrue(prepared["ok"])
        self.assertTrue(pdf_exists)
        self.assertGreater(pdf_size, 1000)
        self.assertTrue(message_exists)
        self.assertEqual(message["To"], "sender@example.com")
        self.assertTrue(str(message["Subject"]).startswith(LIBRARY_EXPORT_SUBJECT_PREFIX))
        self.assertEqual(message[LIBRARY_EXPORT_EMAIL_MARKER], LIBRARY_EXPORT_EMAIL_MARKER_VALUE)
        self.assertEqual(metadata["status"], "draft")
        self.assertTrue(metadata["library_export_marker"])
        self.assertIn(export["export_id"], export["confirmation_text"])

    @unittest.skipIf(Image is None or not HAS_REPORTLAB, "Pillow and ReportLab are required")
    def test_prepare_article_pdf_export_embeds_readable_image_on_separate_page(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            result = archive_text_entry(
                title="Výlet s obrázkem",
                text="Krátký syntetický text pro PDF export.",
                category="travel_places",
                archive_root=archive_root,
            )
            article_id = result["item"]["id"]
            image_buffer = BytesIO()
            Image.new("RGB", (1800, 900), "#4f7f5f").save(image_buffer, format="PNG")
            attach_article_image(
                article_id=article_id,
                image_bytes=image_buffer.getvalue(),
                filename="landscape.png",
                label="Syntetická krajina",
                note="Syntetická obrazová příloha.",
                archive_root=archive_root,
                user_confirmed=True,
                confirmation_text=ATTACHMENT_CONFIRMATION_PHRASE,
            )
            portrait_buffer = BytesIO()
            Image.new("RGB", (700, 1400), "#7c5f91").save(portrait_buffer, format="PNG")
            attach_article_image(
                article_id=article_id,
                image_bytes=portrait_buffer.getvalue(),
                filename="portrait.png",
                label="Syntetický portrét",
                archive_root=archive_root,
                user_confirmed=True,
                confirmation_text=ATTACHMENT_CONFIRMATION_PHRASE,
            )
            metadata_path = archive_root / "articles" / article_id / "metadata.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            for attachment in metadata["attachments"]:
                (archive_root / attachment["original_file"]).write_bytes(b"unusable original")

            prepared = prepare_article_pdf_export(
                article_id=article_id,
                archive_root=archive_root,
                smtp_config_loader=_smtp_config,
            )
            pdf_bytes = Path(prepared["export"]["pdf_path"]).read_bytes()

        self.assertTrue(prepared["ok"])
        self.assertGreaterEqual(pdf_bytes.count(b"/Subtype /Image"), 2)
        self.assertGreaterEqual(len(re.findall(rb"/Type\s*/Page\b", pdf_bytes)), 3)

    @unittest.skipIf(Image is None or not HAS_REPORTLAB, "Pillow and ReportLab are required")
    def test_prepare_article_pdf_export_skips_missing_image_without_failing(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            result = archive_text_entry(
                title="Karta s chybějícím obrázkem",
                text="PDF se musí vytvořit i bez obrazového souboru.",
                category="other",
                archive_root=archive_root,
            )
            article_id = result["item"]["id"]
            image_buffer = BytesIO()
            Image.new("RGB", (640, 960), "white").save(image_buffer, format="PNG")
            attach_article_image(
                article_id=article_id,
                image_bytes=image_buffer.getvalue(),
                filename="portrait.png",
                label="Chybějící příloha",
                archive_root=archive_root,
                user_confirmed=True,
                confirmation_text=ATTACHMENT_CONFIRMATION_PHRASE,
            )
            metadata_path = archive_root / "articles" / article_id / "metadata.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            attachment = metadata["attachments"][0]
            for field in ("readable_file", "original_file"):
                (archive_root / attachment[field]).unlink()

            prepared = prepare_article_pdf_export(
                article_id=article_id,
                archive_root=archive_root,
                smtp_config_loader=_smtp_config,
            )
            pdf_bytes = Path(prepared["export"]["pdf_path"]).read_bytes()

        self.assertTrue(prepared["ok"])
        self.assertNotIn(b"/Subtype /Image", pdf_bytes)

    @unittest.skipIf(Image is None or not HAS_REPORTLAB, "Pillow and ReportLab are required")
    def test_prepare_article_pdf_export_skips_corrupt_image_without_failing(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            result = archive_text_entry(
                title="Karta s poškozeným obrázkem",
                text="PDF se musí vytvořit i s poškozenou obrazovou přílohou.",
                category="other",
                archive_root=archive_root,
            )
            article_id = result["item"]["id"]
            image_buffer = BytesIO()
            Image.new("RGB", (640, 960), "white").save(image_buffer, format="PNG")
            attach_article_image(
                article_id=article_id,
                image_bytes=image_buffer.getvalue(),
                filename="portrait.png",
                label="Poškozená příloha",
                archive_root=archive_root,
                user_confirmed=True,
                confirmation_text=ATTACHMENT_CONFIRMATION_PHRASE,
            )
            metadata_path = archive_root / "articles" / article_id / "metadata.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            attachment = metadata["attachments"][0]
            for field in ("readable_file", "original_file"):
                (archive_root / attachment[field]).write_bytes(b"not an image")

            prepared = prepare_article_pdf_export(
                article_id=article_id,
                archive_root=archive_root,
                smtp_config_loader=_smtp_config,
            )
            pdf_bytes = Path(prepared["export"]["pdf_path"]).read_bytes()

        self.assertTrue(prepared["ok"])
        self.assertNotIn(b"/Subtype /Image", pdf_bytes)

    @unittest.skipIf(not HAS_REPORTLAB, "ReportLab is not installed")
    def test_send_article_pdf_export_requires_confirmation_then_uses_smtp(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_root = Path(temp_dir)
            result = archive_text_entry(
                title="Knihovní poznámka",
                text="Krátký text pro export.",
                category="other",
                archive_root=archive_root,
            )
            prepared = prepare_article_pdf_export(
                article_id=result["item"]["id"],
                archive_root=archive_root,
                smtp_config_loader=_smtp_config,
            )
            export_id = prepared["export"]["export_id"]
            smtp = _FakeSMTP()

            with self.assertRaises(ValueError):
                send_article_pdf_export(
                    export_id=export_id,
                    archive_root=archive_root,
                    user_confirmed=False,
                    confirmation_text="",
                    smtp_config_loader=_smtp_config,
                    smtp_factory=lambda *args, **kwargs: smtp,
                    sent_copy_saver=_sent_copy_saved,
                )

            sent = send_article_pdf_export(
                export_id=export_id,
                archive_root=archive_root,
                user_confirmed=True,
                confirmation_text=library_export_confirmation_text(export_id),
                smtp_config_loader=_smtp_config,
                smtp_factory=lambda *args, **kwargs: smtp,
                sent_copy_saver=_sent_copy_saved,
            )
            metadata_path = Path(prepared["export"]["metadata_path"])
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        self.assertEqual(len(smtp.sent_messages), 1)
        self.assertTrue(sent["ok"])
        self.assertEqual(metadata["status"], "sent")
        self.assertEqual(metadata["delivery_status"], "smtp_sent")
        self.assertEqual(metadata["sent_copy_status"], "saved")

    def test_fetch_url_falls_back_to_curl_for_certificate_chain_failure(self) -> None:
        cert_error = ssl.SSLCertVerificationError("certificate verify failed")
        html = "<html><title>Český článek</title></html>".encode("iso-8859-2")
        compressed_html = gzip.compress(html)
        curl_result = subprocess.CompletedProcess(
            args=["curl"],
            returncode=0,
            stdout=(
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/html; charset=ISO-8859-2\r\n"
                b"Content-Encoding: gzip\r\n"
                b"\r\n"
                + compressed_html
            ),
            stderr=b"",
        )
        response_metadata: dict[str, str] = {}

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError(cert_error)):
            with patch("subprocess.run", return_value=curl_result) as run:
                fetched = fetch_url(
                    "https://example.test/clanek",
                    timeout=5,
                    response_metadata=response_metadata,
                )

        self.assertEqual(fetched, html)
        self.assertEqual(response_metadata["charset"], "ISO-8859-2")
        self.assertEqual(response_metadata["content_encoding"], "gzip")
        curl_args = run.call_args.args[0]
        self.assertIn("--fail", curl_args)
        self.assertIn("--dump-header", curl_args)
        self.assertNotIn("--insecure", curl_args)
        self.assertNotIn("-k", curl_args)

    def test_fetch_url_keeps_non_certificate_errors_without_curl_fallback(self) -> None:
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("network down")):
            with patch("subprocess.run") as run:
                with self.assertRaises(urllib.error.URLError):
                    fetch_url("https://example.test/clanek", timeout=5)

        run.assert_not_called()


class _FakeSMTP:
    def __init__(self) -> None:
        self.sent_messages: list[object] = []
        self.logged_in = False

    def __enter__(self) -> "_FakeSMTP":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def starttls(self) -> None:
        return None

    def login(self, address: str, password: str) -> None:
        self.logged_in = (address, password) == ("sender@example.com", "secret")

    def send_message(self, message: object) -> None:
        self.sent_messages.append(message)


def _smtp_config(provider: str) -> OutgoingMailConfig:
    return OutgoingMailConfig(
        address="sender@example.com",
        password="secret",
        host="smtp.example.com",
        port=587,
        security="starttls",
        provider=provider,
    )


def _sent_copy_saved(
    message_bytes: bytes,
    smtp_config: OutgoingMailConfig,
    sent_timestamp: object,
) -> SentCopyResult:
    return SentCopyResult(
        status="saved",
        provider="icloud",
        folder="Sent Messages",
        detail="test saver",
    )


if __name__ == "__main__":
    unittest.main()
