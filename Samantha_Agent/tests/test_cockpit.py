from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.cockpit import (
    COCKPIT_HTML,
    EMAIL_PROCESSING_HTML,
    document_reference,
    document_work_status,
    latest_email_processing_overview,
    move_document_lifecycle_action,
    prepare_document_print_action,
    search_document_index,
    set_document_reading_status_action,
    web_apps_catalog,
)


class CockpitTests(unittest.TestCase):
    def test_document_work_status_groups_downloads_and_review_queue(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "reviewed-doc",
                        "title": "Reviewed",
                        "domain": "tax",
                        "document_type": "confirmation",
                        "stored_path": "data/private/documents/vault/tax/reviewed-doc/reviewed.pdf",
                        "reading_status": "ok",
                    },
                    {
                        "document_id": "pending-doc",
                        "title": "Pending",
                        "domain": "insurance",
                        "document_type": "policy",
                        "stored_path": "data/private/documents/vault/insurance/pending-doc/pending.pdf",
                    },
                ],
            )
            self.write_jsonl(
                index / "scandocu_actions.jsonl",
                [
                    {"action": "reviewed", "document_id": "reviewed-doc"},
                ],
            )
            downloads = {
                "ok": True,
                "items": [
                    {"name": "new.pdf", "status": "new", "modified_at": "2026-05-28T20:00:00+00:00"},
                    {
                        "name": "encrypted.pdf",
                        "status": "new",
                        "is_encrypted": True,
                        "modified_at": "2026-05-28T19:00:00+00:00",
                    },
                    {"name": "already.pdf", "status": "already_in_vault"},
                    {"name": "skipped.pdf", "status": "skipped"},
                    {"name": "broken.pdf", "status": "invalid"},
                ],
            }

            status = document_work_status(downloads=downloads, vault_dir=vault)

            self.assertEqual(status["summary"]["new_pdf_count"], 2)
            self.assertEqual(status["summary"]["problem_count"], 4)
            self.assertEqual(status["summary"]["review_pending_count"], 1)
            self.assertEqual(status["review"]["status_counts"]["ok"], 1)
            self.assertEqual(status["review"]["status_counts"]["needs_review"], 1)
            self.assertEqual(status["review"]["next_items"][0]["document_id"], "pending-doc")
            self.assertEqual(status["problems"][0]["problem_kind"], "encrypted")
            self.assertEqual(status["problems"][1]["problem_kind"], "duplicate")

    def test_cockpit_html_contains_document_work_controls(self) -> None:
        self.assertIn("Dnes", COCKPIT_HTML)
        self.assertIn("Stav", COCKPIT_HTML)
        self.assertIn("Akce", COCKPIT_HTML)
        self.assertIn("todayNewPdfCount", COCKPIT_HTML)
        self.assertIn("dashboardScanDocu", COCKPIT_HTML)
        self.assertIn("dashboardGit", COCKPIT_HTML)
        self.assertIn("dashboardProcessBtn", COCKPIT_HTML)
        self.assertIn("renderDashboard(data)", COCKPIT_HTML)
        self.assertIn("Samantha chat", COCKPIT_HTML)
        self.assertIn("Codex CLI", COCKPIT_HTML)
        self.assertIn("/api/samantha/open", COCKPIT_HTML)
        self.assertIn("/api/codex/open", COCKPIT_HTML)
        self.assertIn("Práce s dokumenty", COCKPIT_HTML)
        self.assertIn("Nová PDF ve Downloads", COCKPIT_HTML)
        self.assertIn("Uložené dokumenty k revizi", COCKPIT_HTML)
        self.assertIn("Problémy", COCKPIT_HTML)
        self.assertIn("Zpracovat další dokument", COCKPIT_HTML)

    def test_document_search_returns_structured_redacted_results(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "doc-revize",
                        "title": "Revize fotovoltaiky",
                        "original_filename": "revize.pdf",
                        "domain": "energy",
                        "document_type": "inspection_report",
                        "counterparty": "Servis",
                        "related_asset": "fotovoltaika",
                        "stored_path": "data/private/documents/vault/energy/doc-revize/revize.pdf",
                        "tags": ["kontrola"],
                    }
                ],
            )
            self.write_jsonl(
                index / "text_index.jsonl",
                [
                    {
                        "document_id": "doc-revize",
                        "text": (
                            "Revizni protokol fotovoltaika. Kontakt servis@example.com, "
                            "rodne cislo 641215/0987 a odkaz https://example.com/private."
                        ),
                    }
                ],
            )

            result = search_document_index("fotovoltaika", vault_dir=vault)

            self.assertTrue(result["ok"])
            self.assertEqual(result["count"], 1)
            found = result["results"][0]
            self.assertEqual(found["document_id"], "doc-revize")
            self.assertEqual(found["document_ref"], document_reference("doc-revize"))
            self.assertEqual(found["reading_status"], "ok")
            self.assertEqual(found["reading_status_label"], "OK")
            self.assertIn("[e-mail redigovan]", found["snippet"])
            self.assertIn("[rodne cislo redigovano]", found["snippet"])
            self.assertIn("[URL redigovano]", found["snippet"])
            self.assertNotIn("641215/0987", found["snippet"])
            self.assertNotIn("https://example.com/private", found["snippet"])

    def test_document_search_marks_metadata_only_result_as_needs_review(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "doc-text",
                        "title": "Alpha text",
                        "domain": "tax",
                        "document_type": "confirmation",
                        "stored_path": "data/private/documents/vault/tax/doc-text/text.pdf",
                    },
                    {
                        "document_id": "doc-metadata-only",
                        "title": "Metadataonly smlouva",
                        "domain": "insurance",
                        "document_type": "policy",
                        "stored_path": "data/private/documents/vault/insurance/doc-metadata-only/doc.pdf",
                        "text_extraction": {"indexed_chars": 0},
                    },
                ],
            )
            self.write_jsonl(
                index / "text_index.jsonl",
                [
                    {"document_id": "doc-text", "text": "Alpha searchable text."},
                    {"document_id": "doc-metadata-only", "text": ""},
                ],
            )

            result = search_document_index("metadataonly", vault_dir=vault)

            self.assertEqual(result["count"], 1)
            self.assertEqual(result["results"][0]["document_id"], "doc-metadata-only")
            self.assertEqual(result["results"][0]["reading_status"], "needs_review")
            self.assertEqual(result["results"][0]["reading_status_label"], "k revizi")

    def test_cockpit_html_contains_document_search_controls(self) -> None:
        self.assertIn("Najít dokument", COCKPIT_HTML)
        self.assertIn("documentSearchInput", COCKPIT_HTML)
        self.assertIn("/api/documents/search", COCKPIT_HTML)
        self.assertIn("Rozbalit", COCKPIT_HTML)
        self.assertIn("Sbalit", COCKPIT_HTML)
        self.assertIn("search-detail hidden", COCKPIT_HTML)
        self.assertIn("Tisknout", COCKPIT_HTML)
        self.assertIn("Archivovat", COCKPIT_HTML)
        self.assertIn("Do koše", COCKPIT_HTML)
        self.assertIn("Stav čtení", COCKPIT_HTML)
        self.assertIn("/api/documents/reading-status", COCKPIT_HTML)
        self.assertIn("nahrazeno lepší kopií", COCKPIT_HTML)

    def test_cockpit_html_contains_web_apps_modal(self) -> None:
        self.assertIn("Webové aplikace", COCKPIT_HTML)
        self.assertIn("webAppsModal", COCKPIT_HTML)
        self.assertIn("/api/web-apps", COCKPIT_HTML)
        self.assertIn("openWebApp(app)", COCKPIT_HTML)
        self.assertIn("SamanthaWebApp_", COCKPIT_HTML)
        self.assertNotIn('target = "_blank"', COCKPIT_HTML)
        self.assertIn("Zavřít", COCKPIT_HTML)

    def test_email_processing_overview_reads_latest_private_resume(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            older = root / "weekly_email_overview_2026_05_31_private.md"
            latest = root / "weekly_email_overview_2026_06_01_private.md"
            older.write_text("# Older\n\n## Faktury / e-shopy\n\n- Stará položka\n", encoding="utf-8")
            latest.write_text("# Latest\n\n## Faktury / e-shopy\n\n- Nová položka\n", encoding="utf-8")

            result = latest_email_processing_overview(root=root)

            self.assertTrue(result["ok"])
            self.assertEqual(result["title"], "Latest")
            self.assertIn("Nová položka", result["text"])
            self.assertNotIn("Stará položka", result["text"])
            self.assertTrue(result["path"].endswith("weekly_email_overview_2026_06_01_private.md"))

    def test_email_processing_html_contains_readonly_overview_controls(self) -> None:
        self.assertIn("Email Processing", EMAIL_PROCESSING_HTML)
        self.assertIn("/api/email-processing/overview", EMAIL_PROCESSING_HTML)
        self.assertIn("read-only", EMAIL_PROCESSING_HTML)
        self.assertIn("faktury/e-shopy", EMAIL_PROCESSING_HTML)
        self.assertIn("pojištění/smlouvy", EMAIL_PROCESSING_HTML)

    def test_cockpit_html_contains_email_processing_controls(self) -> None:
        self.assertIn("Email Processing", COCKPIT_HTML)
        self.assertIn("emailProcessingBtn", COCKPIT_HTML)
        self.assertIn("dashboardEmailBtn", COCKPIT_HTML)
        self.assertIn("/email-processing/", COCKPIT_HTML)
        self.assertIn("openEmailProcessing", COCKPIT_HTML)

    def test_web_apps_catalog_contains_known_apps(self) -> None:
        catalog = web_apps_catalog()
        titles = {item["title"] for item in catalog["apps"]}

        self.assertTrue(catalog["ok"])
        self.assertIn("ScanDocu", titles)
        self.assertIn("Email Processing", titles)
        self.assertIn("Lékárna", titles)
        self.assertIn("Family Video Organizer", titles)

    def test_prepare_print_action_creates_queue_copy(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault, document_id, source = self.create_indexed_document(Path(temp_dir))

            result = prepare_document_print_action(document_id=document_id, vault_dir=vault)

            self.assertTrue(result["ok"])
            self.assertEqual(result["document_id"], document_id)
            self.assertTrue((vault / "print_queue").exists())
            self.assertTrue(source.exists())

    def test_archive_action_moves_document_and_updates_index(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault, document_id, source = self.create_indexed_document(Path(temp_dir))

            result = move_document_lifecycle_action(
                document_id=document_id,
                target="archive",
                confirmation_text=f"Potvrzuji, archivuj dokument {document_id}.",
                vault_dir=vault,
            )

            docs = self.read_jsonl(vault / "index" / "documents_index.jsonl")
            self.assertTrue(result["ok"])
            self.assertEqual(docs[0]["lifecycle_status"], "archived")
            self.assertIn("/archive/", docs[0]["stored_path"])
            self.assertFalse(source.exists())
            self.assertTrue(Path(docs[0]["stored_path"]).exists())

    def test_trash_action_requires_exact_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault, document_id, source = self.create_indexed_document(Path(temp_dir))

            result = move_document_lifecycle_action(
                document_id=document_id,
                target="trash",
                confirmation_text="ano",
                vault_dir=vault,
            )

            docs = self.read_jsonl(vault / "index" / "documents_index.jsonl")
            self.assertFalse(result["ok"])
            self.assertNotIn("lifecycle_status", docs[0])
            self.assertTrue(source.exists())

    def test_set_document_reading_status_updates_index_manifest_and_audit_log(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault, document_id, _source = self.create_indexed_document(Path(temp_dir))

            result = set_document_reading_status_action(
                document_id=document_id,
                reading_status="unreadable",
                note="OCR později",
                vault_dir=vault,
            )

            docs = self.read_jsonl(vault / "index" / "documents_index.jsonl")
            manifest = json.loads((vault / "vault" / "tax" / document_id / "manifest.json").read_text(encoding="utf-8"))
            actions = self.read_jsonl(vault / "index" / "document_reading_status_actions.jsonl")
            self.assertTrue(result["ok"])
            self.assertEqual(result["reading_status"], "unreadable")
            self.assertEqual(docs[0]["reading_status"], "unreadable")
            self.assertEqual(manifest["reading_status"], "unreadable")
            self.assertEqual(actions[0]["document_id"], document_id)
            self.assertEqual(actions[0]["reading_status"], "unreadable")
            self.assertTrue((vault / "index" / "status_backups").exists())

    def test_set_document_reading_status_accepts_document_ref(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault, _document_id, _source = self.create_indexed_document(Path(temp_dir), document_id="doc-1234567890")

            result = set_document_reading_status_action(
                document_id=document_reference("doc-1234567890"),
                reading_status="superseded",
                vault_dir=vault,
            )

            docs = self.read_jsonl(vault / "index" / "documents_index.jsonl")
            self.assertTrue(result["ok"])
            self.assertEqual(result["document_id"], "doc-[rodne cislo redigovano]")
            self.assertEqual(docs[0]["document_id"], "doc-1234567890")
            self.assertEqual(docs[0]["reading_status"], "superseded")

    @staticmethod
    def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )

    @classmethod
    def create_indexed_document(cls, root: Path, document_id: str = "doc-akce") -> tuple[Path, str, Path]:
        vault = root / "documents"
        document_dir = vault / "vault" / "tax" / document_id
        document_dir.mkdir(parents=True)
        source = document_dir / "smlouva.pdf"
        source.write_bytes(b"%PDF-1.4\nTest document\n")
        record = {
            "document_id": document_id,
            "title": "Smlouva",
            "original_filename": "smlouva.pdf",
            "domain": "tax",
            "document_type": "contract",
            "stored_path": str(source),
        }
        (vault / "index").mkdir(parents=True)
        cls.write_jsonl(vault / "index" / "documents_index.jsonl", [record])
        (document_dir / "manifest.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        return vault, document_id, source

    @staticmethod
    def read_jsonl(path: Path) -> list[dict[str, object]]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


if __name__ == "__main__":
    unittest.main()
