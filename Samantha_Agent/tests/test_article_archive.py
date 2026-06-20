from __future__ import annotations

import json
import ssl
import subprocess
import tempfile
import urllib.error
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from app.article_archive import (
    ATTACHMENT_CONFIRMATION_PHRASE,
    DELETE_CONFIRMATION_PHRASE,
    archive_text_entry,
    archive_url,
    attach_article_image,
    delete_article,
    fetch_url,
    get_article,
    get_article_attachment,
    list_articles,
    search_articles,
)

try:
    from PIL import Image
except ModuleNotFoundError:  # pragma: no cover - depends on local environment setup
    Image = None


class ArticleArchiveTests(unittest.TestCase):
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
            attachments_dir.mkdir(parents=True)
            (article_dir / "article.txt").write_text("Rodinný recept\nPřepis rukopisu.", encoding="utf-8")
            readable = attachments_dir / "recept_readable.jpg"
            readable.write_bytes(b"fake-jpeg")
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

        self.assertEqual(listed["items"][0]["attachment_count"], 1)
        self.assertEqual(listed["items"][0]["attachment_roles"], ["handwritten_recipe_scan"])
        self.assertTrue(article["ok"])
        self.assertEqual(article["item"]["attachments"][0]["label"], "Ručně psaný originál")
        self.assertTrue(attachment["ok"])
        self.assertEqual(attachment["path"].name, "recept_readable.jpg")

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

    def test_fetch_url_falls_back_to_curl_for_certificate_chain_failure(self) -> None:
        cert_error = ssl.SSLCertVerificationError("certificate verify failed")
        curl_result = subprocess.CompletedProcess(
            args=["curl"],
            returncode=0,
            stdout=b"<html><title>OK</title></html>",
            stderr=b"",
        )

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError(cert_error)):
            with patch("subprocess.run", return_value=curl_result) as run:
                html = fetch_url("https://example.test/clanek", timeout=5)

        self.assertEqual(html, b"<html><title>OK</title></html>")
        curl_args = run.call_args.args[0]
        self.assertIn("--fail", curl_args)
        self.assertNotIn("--insecure", curl_args)
        self.assertNotIn("-k", curl_args)

    def test_fetch_url_keeps_non_certificate_errors_without_curl_fallback(self) -> None:
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("network down")):
            with patch("subprocess.run") as run:
                with self.assertRaises(urllib.error.URLError):
                    fetch_url("https://example.test/clanek", timeout=5)

        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
