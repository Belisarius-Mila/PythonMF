from __future__ import annotations

import json
import ssl
import subprocess
import tempfile
import urllib.error
import unittest
from pathlib import Path
from unittest.mock import patch

from app.article_archive import archive_text_entry, archive_url, fetch_url, get_article, list_articles, search_articles


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
