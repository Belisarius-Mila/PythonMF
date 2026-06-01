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
    email_header_to_processing_item,
    email_processing_item_id,
    email_processing_pending_work_items,
    latest_email_processing_overview,
    move_document_lifecycle_action,
    new_email_headers_overview,
    parse_email_processing_items,
    prepare_document_print_action,
    process_email_work_queue_batch,
    read_email_processing_message_detail,
    read_email_processing_decisions,
    save_email_processing_decision,
    search_document_index,
    set_document_reading_status_action,
    web_apps_catalog,
)
from app.email.archive_models import EmailArchiveSource
from app.email.models import EmailAttachmentMeta, EmailHeader, EmailMessage


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
            latest.write_text(
                "# Latest\n\n## Faktury / e-shopy\n\n"
                "1. iCloud / INBOX / UID 14157 / 2026-05-29\n"
                "   - Predmet: Nová položka\n"
                "   - Duvod: faktura\n",
                encoding="utf-8",
            )

            result = latest_email_processing_overview(root=root)

            self.assertTrue(result["ok"])
            self.assertEqual(result["title"], "Latest")
            self.assertIn("Nová položka", result["text"])
            self.assertNotIn("Stará položka", result["text"])
            self.assertTrue(result["path"].endswith("weekly_email_overview_2026_06_01_private.md"))
            self.assertEqual(len(result["items"]), 1)
            self.assertEqual(result["items"][0]["category"], "faktury/e-shopy")

    def test_email_processing_parser_extracts_candidates(self) -> None:
        text = """# Přehled

## Faktury / e-shopy

1. iCloud / INBOX / UID 14157 / 2026-05-29
   - Predmet: Vaše faktura od společnosti Apple
   - Duvod: faktura, silny kandidat na ulozeni

## Ostatni kandidati

- Seznam UID 155560: T-Mobile pevny internet.
"""

        items = parse_email_processing_items(text)

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["provider"], "iCloud")
        self.assertEqual(items[0]["uid"], "14157")
        self.assertEqual(items[0]["subject"], "Vaše faktura od společnosti Apple")
        self.assertEqual(items[1]["category"], "ostatní")
        self.assertEqual(items[1]["provider"], "Seznam")

    def test_email_processing_decision_is_saved_privately(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "email_processing_decisions.json"
            result = save_email_processing_decision(
                item_id="abc123",
                action="process",
                item={"uid": "14157", "provider": "iCloud"},
                path=path,
            )

            decisions = read_email_processing_decisions(path)
            self.assertTrue(result["ok"])
            self.assertEqual(decisions["abc123"]["action"], "process")
            self.assertEqual(decisions["abc123"]["item"]["uid"], "14157")

    def test_new_email_headers_overview_wraps_readonly_unified_text(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            result = new_email_headers_overview(
                limit_per_source=50,
                since="2026-06-01T07:00:00+00:00",
                decisions_path=Path(temp_dir) / "email_processing_decisions.json",
                icloud_provider_factory=lambda: _FakeEmailProvider(
                    [
                        EmailHeader(
                            internal_id="10",
                            date="Mon, 1 Jun 2026 10:00:00 +0200",
                            sender="Sender <sender@example.com>",
                            subject="Nový iCloud e-mail",
                        ),
                        EmailHeader(
                            internal_id="9",
                            date="Sun, 31 May 2026 10:00:00 +0200",
                            sender="Old <old@example.com>",
                            subject="Starý e-mail",
                        )
                    ]
                ),
                seznam_provider_factory=lambda: _FakeEmailProvider([]),
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["limit_per_source"], 50)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["subject"], "Nový iCloud e-mail")
        self.assertEqual(result["items"][0]["category"], "ostatní")
        self.assertNotIn("text", result)

    def test_email_processing_id_is_stable_for_same_provider_folder_uid(self) -> None:
        first = email_processing_item_id(
            "faktury/e-shopy",
            "iCloud",
            "INBOX",
            "14157",
            "Mon, 1 Jun 2026 10:00:00 +0200",
            "Původní předmět",
        )
        second = email_processing_item_id(
            "ostatní",
            "iCloud",
            "INBOX",
            "14157",
            "2026-06-01",
            "Jinak zapsaný předmět",
        )
        third = email_processing_item_id(
            "ostatní",
            "Seznam",
            "INBOX",
            "14157",
            "2026-06-01",
            "Jinak zapsaný předmět",
        )

        self.assertEqual(first, second)
        self.assertNotEqual(first, third)

    def test_email_header_processing_item_keeps_legacy_id_for_old_decisions(self) -> None:
        item = email_header_to_processing_item(
            EmailHeader(
                internal_id="14157",
                date="Mon, 1 Jun 2026 10:00:00 +0200",
                sender="Sender <sender@example.com>",
                subject="Nový iCloud e-mail",
            ),
            "iCloud",
        )

        self.assertIn("id", item)
        self.assertIn("legacy_id", item)
        self.assertNotEqual(item["id"], item["legacy_id"])

    def test_read_email_processing_message_detail_reads_body_and_attachment_metadata(self) -> None:
        provider = _FakeMessageProvider(
            EmailMessage(
                header=EmailHeader(
                    internal_id="14157",
                    date="Mon, 1 Jun 2026 10:00:00 +0200",
                    sender="Sender <sender@example.com>",
                    subject="Faktura za služby",
                    source="iCloud",
                    folder="INBOX",
                ),
                body_text="Dobrý den, v příloze posíláme fakturu.",
                truncated=False,
                attachments=(
                    EmailAttachmentMeta(
                        filename="faktura.pdf",
                        content_type="application/pdf",
                        size_bytes=12345,
                        part_id="2",
                        content_id="",
                        disposition="attachment",
                    ),
                ),
            )
        )

        result = read_email_processing_message_detail(
            provider="iCloud",
            folder="INBOX",
            uid="14157",
            icloud_provider_factory=lambda: provider,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(provider.calls[0]["uid"], "14157")
        self.assertEqual(result["email"]["subject"], "Faktura za služby")
        self.assertEqual(result["email"]["body_text"], "Dobrý den, v příloze posíláme fakturu.")
        self.assertEqual(result["email"]["attachments"][0]["filename"], "faktura.pdf")
        self.assertEqual(result["email"]["attachments"][0]["part_id"], "2")

    def test_read_email_processing_message_detail_rejects_unknown_provider(self) -> None:
        result = read_email_processing_message_detail(provider="gmail", folder="INBOX", uid="14157")

        self.assertFalse(result["ok"])
        self.assertIn("Neznámý", result["message"])

    def test_email_processing_pending_work_items_returns_only_actionable_decisions(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "email_processing_decisions.json"
            save_email_processing_decision(
                item_id="process-1",
                action="process",
                item={
                    "id": "process-1",
                    "category": "faktury/e-shopy",
                    "provider": "iCloud",
                    "folder": "INBOX",
                    "uid": "14157",
                    "date": "Mon, 1 Jun 2026 10:00:00 +0200",
                    "subject": "Faktura",
                },
                path=path,
            )
            save_email_processing_decision(
                item_id="ignore-1",
                action="ignore",
                item={"id": "ignore-1", "uid": "14158", "subject": "Ignorovat"},
                path=path,
            )

            result = email_processing_pending_work_items(path=path)

        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["items"][0]["id"], "process-1")
        self.assertEqual(result["items"][0]["action"], "process")
        self.assertFalse(result["items"][0]["is_new_header"])

    def test_process_email_work_queue_batch_archives_email_and_imports_pdf_attachment(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            decisions_path = root / "decisions.json"
            archive_dir = root / "email_archive"
            documents_dir = root / "documents"
            actions_path = root / "work_queue_actions.jsonl"
            activity_state_path = root / "activity_state.json"
            raw_message = _raw_email_with_pdf_attachment()
            provider = _FakeArchiveProvider(
                EmailArchiveSource(
                    uid="14157",
                    date="Mon, 1 Jun 2026 10:00:00 +0200",
                    sender="Sender <sender@example.com>",
                    subject="Faktura za služby",
                    body_text="Dobrý den, v příloze posíláme fakturu.",
                    attachments=(
                        EmailAttachmentMeta(
                            filename="faktura.pdf",
                            content_type="application/pdf",
                            size_bytes=62,
                            part_id="2",
                            content_id="",
                            disposition="attachment",
                        ),
                    ),
                    original_eml=raw_message,
                    provider="icloud",
                    mailbox="INBOX",
                )
            )
            save_email_processing_decision(
                item_id="process-1",
                action="process",
                item={"id": "process-1", "provider": "iCloud", "folder": "INBOX", "uid": "14157"},
                path=decisions_path,
            )

            result = process_email_work_queue_batch(
                items=[
                    {
                        "id": "process-1",
                        "provider": "iCloud",
                        "folder": "INBOX",
                        "uid": "14157",
                        "category": "faktury/e-shopy",
                        "queueDecision": "save",
                        "saveAttachments": ["2"],
                    }
                ],
                archive_directory=archive_dir,
                documents_dir=documents_dir,
                decisions_path=decisions_path,
                actions_path=actions_path,
                activity_state_path=activity_state_path,
                icloud_provider_factory=lambda: provider,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["summary"]["saved"], 1)
            self.assertEqual(result["summary"]["attachments_imported"], 1)
            self.assertTrue((archive_dir / "email-14157-faktura-za-sluzby" / "metadata.json").exists())
            self.assertEqual(read_email_processing_decisions(decisions_path), {})
            docs = self.read_jsonl(documents_dir / "index" / "documents_index.jsonl")
            text_rows = self.read_jsonl(documents_dir / "index" / "text_index.jsonl")
            self.assertEqual(len(docs), 1)
            self.assertEqual(docs[0]["document_type"], "email-attachment-pdf")
            self.assertIn("faktura.pdf", docs[0]["original_filename"])
            self.assertEqual(len(text_rows), 1)
            self.assertTrue(actions_path.exists())
            self.assertTrue(activity_state_path.exists())

    def test_process_email_work_queue_batch_skip_clears_decision_without_provider_call(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "decisions.json"
            save_email_processing_decision(
                item_id="skip-1",
                action="process",
                item={"id": "skip-1", "provider": "iCloud", "folder": "INBOX", "uid": "14157"},
                path=path,
            )

            result = process_email_work_queue_batch(
                items=[
                    {
                        "id": "skip-1",
                        "provider": "iCloud",
                        "folder": "INBOX",
                        "uid": "14157",
                        "queueDecision": "skip",
                    }
                ],
                archive_directory=Path(temp_dir) / "archive",
                documents_dir=Path(temp_dir) / "documents",
                decisions_path=path,
                actions_path=Path(temp_dir) / "actions.jsonl",
                activity_state_path=Path(temp_dir) / "activity.json",
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["summary"]["skipped"], 1)
            self.assertEqual(read_email_processing_decisions(path), {})

    def test_process_email_work_queue_batch_trash_requires_exact_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            provider = _FakeArchiveProvider(_archive_source_without_attachment())

            result = process_email_work_queue_batch(
                items=[
                    {
                        "id": "trash-1",
                        "provider": "iCloud",
                        "folder": "INBOX",
                        "uid": "14157",
                        "queueDecision": "trash_requested",
                    }
                ],
                archive_directory=Path(temp_dir) / "archive",
                documents_dir=Path(temp_dir) / "documents",
                decisions_path=Path(temp_dir) / "decisions.json",
                actions_path=Path(temp_dir) / "actions.jsonl",
                activity_state_path=Path(temp_dir) / "activity.json",
                icloud_provider_factory=lambda: provider,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["summary"]["trash_pending"], 1)
            self.assertFalse(provider.trash_calls)
            self.assertIn("Potvrzuji, přesuň e-mail UID 14157 do koše.", result["items"][0]["required_confirmation"])

    def test_process_email_work_queue_batch_confirmed_trash_uses_provider_move(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            provider = _FakeArchiveProvider(_archive_source_without_attachment())

            result = process_email_work_queue_batch(
                items=[
                    {
                        "id": "trash-1",
                        "provider": "iCloud",
                        "folder": "INBOX",
                        "uid": "14157",
                        "queueDecision": "trash_requested",
                    }
                ],
                trash_confirmation_text="Potvrzuji, přesuň e-mail UID 14157 do koše.",
                archive_directory=Path(temp_dir) / "archive",
                documents_dir=Path(temp_dir) / "documents",
                decisions_path=Path(temp_dir) / "decisions.json",
                actions_path=Path(temp_dir) / "actions.jsonl",
                activity_state_path=Path(temp_dir) / "activity.json",
                icloud_provider_factory=lambda: provider,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["summary"]["trashed"], 1)
            self.assertEqual(provider.trash_calls, [{"uid": "14157", "folder": "INBOX"}])

    def test_email_processing_html_contains_readonly_overview_controls(self) -> None:
        self.assertIn("Email Processing", EMAIL_PROCESSING_HTML)
        self.assertIn("/api/email-processing/overview", EMAIL_PROCESSING_HTML)
        self.assertIn("/api/email-processing/pending-work", EMAIL_PROCESSING_HTML)
        self.assertIn("/api/email-processing/decision", EMAIL_PROCESSING_HTML)
        self.assertIn("/api/email-processing/new-headers", EMAIL_PROCESSING_HTML)
        self.assertIn("/api/email-processing/read-message", EMAIL_PROCESSING_HTML)
        self.assertIn("/api/email-processing/process-batch", EMAIL_PROCESSING_HTML)
        self.assertIn("read-only", EMAIL_PROCESSING_HTML)
        self.assertIn("Obnovit nové", EMAIL_PROCESSING_HTML)
        self.assertIn('id="refreshBtn" disabled', EMAIL_PROCESSING_HTML)
        self.assertIn("Nejdřív použij Načti emaily", EMAIL_PROCESSING_HTML)
        self.assertIn("updateRefreshButtonState", EMAIL_PROCESSING_HTML)
        self.assertIn("Načti emaily", EMAIL_PROCESSING_HTML)
        self.assertIn("Načti rozpracované", EMAIL_PROCESSING_HTML)
        self.assertIn("loadPendingWork", EMAIL_PROCESSING_HTML)
        self.assertIn("Za posledních:", EMAIL_PROCESSING_HTML)
        self.assertIn('id="emailDaysInput"', EMAIL_PROCESSING_HTML)
        self.assertIn('min="1"', EMAIL_PROCESSING_HTML)
        self.assertIn('max="14"', EMAIL_PROCESSING_HTML)
        self.assertIn("Okno startuje prázdné", EMAIL_PROCESSING_HTML)
        self.assertIn("Pracovní seznam je prázdný", EMAIL_PROCESSING_HTML)
        self.assertIn("ve zvoleném rozsahu 1-14 dní", EMAIL_PROCESSING_HTML)
        self.assertIn("loadNewHeaders({lastSevenDays: true})", EMAIL_PROCESSING_HTML)
        self.assertIn("loadNewHeaders({newOnly: true})", EMAIL_PROCESSING_HTML)
        self.assertIn("Zpracovat e-maily", EMAIL_PROCESSING_HTML)
        self.assertIn("processEmailsBtn", EMAIL_PROCESSING_HTML)
        self.assertIn("SamanthaEmailWorkQueue", EMAIL_PROCESSING_HTML)
        self.assertIn("initializeWorkQueueWindow", EMAIL_PROCESSING_HTML)
        self.assertIn("Koš - čeká na potvrzení", EMAIL_PROCESSING_HTML)
        self.assertIn("Detail se načte read-only", EMAIL_PROCESSING_HTML)
        self.assertIn("Detail e-mailu", EMAIL_PROCESSING_HTML)
        self.assertIn("detailLoaded", EMAIL_PROCESSING_HTML)
        self.assertIn("Načítám celý e-mail read-only", EMAIL_PROCESSING_HTML)
        self.assertIn("Detail načten z cache", EMAIL_PROCESSING_HTML)
        self.assertIn("IMAP se znovu nevolal", EMAIL_PROCESSING_HTML)
        self.assertIn("Uložit e-mail", EMAIL_PROCESSING_HTML)
        self.assertIn("Neukládat", EMAIL_PROCESSING_HTML)
        self.assertIn("Uložit</label>", EMAIL_PROCESSING_HTML)
        self.assertIn("Otevření souboru bude dostupné po potvrzeném uložení přílohy", EMAIL_PROCESSING_HTML)
        self.assertIn("Zpracovat dávku", EMAIL_PROCESSING_HTML)
        self.assertIn("hlavní seznam je vyprázdněný", EMAIL_PROCESSING_HTML)
        self.assertIn("headersBusy", EMAIL_PROCESSING_HTML)
        self.assertIn("Doplňuji chybějící hlavičky", EMAIL_PROCESSING_HTML)
        self.assertIn("Zpracovat", EMAIL_PROCESSING_HTML)
        self.assertIn("Ignorovat", EMAIL_PROCESSING_HTML)
        self.assertIn("Koš", EMAIL_PROCESSING_HTML)
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


class _FakeEmailProvider:
    def __init__(self, headers: list[EmailHeader]) -> None:
        self._headers = headers

    def list_recent_headers(self, limit: int = 10) -> list[EmailHeader]:
        return self._headers[:limit]


class _FakeMessageProvider:
    def __init__(self, message: EmailMessage) -> None:
        self._message = message
        self.calls: list[dict[str, object]] = []

    def read_message_by_uid(self, uid: str, max_chars: int = 4_000, folder: str = "INBOX") -> EmailMessage:
        self.calls.append({"uid": uid, "max_chars": max_chars, "folder": folder})
        return self._message

    def read_message_by_uid_from_folder(
        self,
        uid: str,
        max_chars: int = 4_000,
        folder: str = "INBOX",
    ) -> EmailMessage:
        self.calls.append({"uid": uid, "max_chars": max_chars, "folder": folder})
        return self._message


class _FakeArchiveProvider:
    def __init__(self, source: EmailArchiveSource) -> None:
        self._source = source
        self.archive_calls: list[dict[str, object]] = []
        self.trash_calls: list[dict[str, object]] = []

    def read_archive_source_by_uid(self, uid: str, max_chars: int = 50_000, folder: str = "INBOX") -> EmailArchiveSource:
        self.archive_calls.append({"uid": uid, "max_chars": max_chars, "folder": folder})
        return self._source

    def move_message_to_trash(self, uid: str, folder: str = "INBOX") -> None:
        self.trash_calls.append({"uid": uid, "folder": folder})


def _archive_source_without_attachment() -> EmailArchiveSource:
    return EmailArchiveSource(
        uid="14157",
        date="Mon, 1 Jun 2026 10:00:00 +0200",
        sender="Sender <sender@example.com>",
        subject="Faktura za služby",
        body_text="Dobrý den.",
        provider="icloud",
        mailbox="INBOX",
    )


def _raw_email_with_pdf_attachment() -> bytes:
    pdf_bytes = b"%PDF-1.4\n1 0 obj <<>> endobj\ntrailer <<>>\n%%EOF\n"
    return (
        b"From: Sender <sender@example.com>\r\n"
        b"Date: Mon, 1 Jun 2026 10:00:00 +0200\r\n"
        b"Subject: Faktura za sluzby\r\n"
        b"MIME-Version: 1.0\r\n"
        b"Content-Type: multipart/mixed; boundary=\"outer\"\r\n"
        b"\r\n"
        b"--outer\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"Dobry den, v priloze posilame fakturu.\r\n"
        b"--outer\r\n"
        b"Content-Type: application/pdf; name=\"faktura.pdf\"\r\n"
        b"Content-Disposition: attachment; filename=\"faktura.pdf\"\r\n"
        b"\r\n"
        + pdf_bytes
        + b"\r\n--outer--\r\n"
    )


if __name__ == "__main__":
    unittest.main()
