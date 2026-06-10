from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import app.cockpit as cockpit_module
from app.cockpit import (
    COCKPIT_HTML,
    EMAIL_PROCESSING_HTML,
    action_queue_status,
    adam_voice_bridge_status,
    cancel_payment_reminder_action,
    cockpit_status,
    create_document_due_reminder_action,
    document_reference,
    library_archive_url_action,
    cockpit_edge_tts_action,
    cockpit_voice_approval_action,
    cockpit_save_voice_text_action,
    cockpit_speak_action,
    cockpit_transcribe_voice_action,
    save_voice_command_to_inbox,
    document_intake_email_scan_status,
    document_intake_status,
    document_cases_status,
    document_case_detail_status,
    document_classification_status,
    document_due_candidates_status,
    document_review_report_status,
    document_work_status,
    email_header_to_processing_item,
    email_processing_item_id,
    email_processing_pending_work_items,
    latest_email_processing_overview,
    local_seznam_email_source_detail,
    mark_reminder_done_action,
    move_document_lifecycle_action,
    new_email_headers_overview,
    open_document_pdf_action,
    parse_active_projects_table,
    parse_global_tools_table,
    parse_infrastructure_capabilities_table,
    parse_email_processing_items,
    prepare_document_print_action,
    projects_status,
    quick_note_detail_status,
    quick_notes_status,
    quantitative_status_overview,
    preview_email_work_queue_attachment_action,
    process_email_work_queue_batch,
    process_email_work_queue_purge_trash_batch,
    read_email_processing_message_detail,
    read_email_processing_decisions,
    reminder_reference,
    reminder_source_detail_action,
    reminders_status,
    recovery_center_status,
    save_email_processing_decision,
    search_document_index,
    set_document_reading_status_action,
    start_adam_voice_mode_action,
    start_cockpit_restart_action,
    stop_adam_voice_mode_action,
    urgent_reminder_done_action,
    urgent_reminders_status,
    update_document_classification_metadata_action,
    web_apps_catalog,
)
from app.email.archive_models import EmailArchiveSource
from app.email.models import EmailAttachmentMeta, EmailHeader, EmailMessage


class CockpitTests(unittest.TestCase):
    def test_library_archive_url_action_passes_url_category_and_tags(self) -> None:
        with patch("app.cockpit.archive_url") as archive_mock:
            archive_mock.return_value = {"ok": True, "item": {"id": "article-1"}}

            result = library_archive_url_action(
                {
                    "url": "https://example.test/clanek",
                    "category": "recipes",
                    "tags": "kolac, rychle",
                }
            )

        self.assertTrue(result["ok"])
        archive_mock.assert_called_once_with(
            url="https://example.test/clanek",
            category="recipes",
            tags=["kolac", "rychle"],
        )

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
                    {
                        "document_id": "trashed-doc",
                        "title": "Trashed",
                        "domain": "insurance",
                        "document_type": "policy",
                        "stored_path": "data/private/documents/trash/trashed-doc/trashed.pdf",
                        "lifecycle_status": "trashed",
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
            self.assertEqual(status["summary"]["problem_count"], 2)
            self.assertEqual(status["summary"]["review_pending_count"], 1)
            self.assertEqual(status["review"]["status_counts"]["ok"], 1)
            self.assertEqual(status["review"]["status_counts"]["needs_review"], 1)
            self.assertEqual(status["review"]["next_items"][0]["document_id"], "pending-doc")
            self.assertNotIn("trashed-doc", str(status["review"]["next_items"]))
            self.assertEqual(status["problems"][0]["problem_kind"], "encrypted")
            self.assertEqual(status["problems"][1]["problem_kind"], "invalid")

    def test_document_intake_status_summarizes_all_document_sources_readonly(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            incoming = vault / "inbox" / "incoming"
            incoming.mkdir(parents=True)
            (incoming / "local.pdf").write_bytes(b"%PDF-1.4\n")
            decisions_path = root / "email_processing_decisions.json"
            save_email_processing_decision(
                item_id="process-1",
                action="process",
                item={
                    "id": "process-1",
                    "provider": "iCloud",
                    "folder": "INBOX",
                    "uid": "14157",
                    "date": "Mon, 1 Jun 2026 10:00:00 +0200",
                    "subject": "Pojistná příloha",
                },
                path=decisions_path,
            )
            mobile = root / "SamanthaDocumentInbox"
            mobile.mkdir()
            (mobile / "scan_A_manifest.json").write_text(
                json.dumps(
                    {
                        "batch_id": "scan_A",
                        "document_title": "Mobilní scan",
                        "page_count": 1,
                    }
                ),
                encoding="utf-8",
            )
            (mobile / "scan_A_page_001.jpg").write_bytes(b"image")
            downloads = {
                "ok": True,
                "items": [
                    {"name": "download.pdf", "status": "new", "modified_at": "2026-06-04T10:00:00+00:00"},
                    {"name": "old.pdf", "status": "already_in_vault"},
                ],
            }

            result = document_intake_status(
                downloads=downloads,
                decisions_path=decisions_path,
                mobile_inbox_dir=mobile,
                vault_dir=vault,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 4)
        sources = {source["id"]: source for source in result["sources"]}
        self.assertEqual(sources["downloads"]["count"], 1)
        self.assertEqual(sources["email"]["count"], 1)
        self.assertEqual(sources["mobile"]["count"], 1)
        self.assertEqual(sources["local_inbox"]["count"], 1)
        self.assertEqual(sources["mobile"]["items"][0]["title"], "Mobilní scan")
        self.assertEqual(len(result["unified_items"]), 4)
        self.assertEqual(result["unified_items"][0]["source_id"], "downloads")
        self.assertEqual(result["unified_items"][0]["action_kind"], "open_scandocu")
        self.assertEqual(result["unified_items"][1]["source_id"], "email")
        self.assertEqual(result["unified_items"][1]["action_kind"], "open_email_processing")
        self.assertEqual(result["unified_items"][2]["source_id"], "mobile")
        self.assertEqual(result["unified_items"][3]["source_id"], "local_inbox")
        self.assertNotIn("image", json.dumps(result, ensure_ascii=False))

    def test_document_cases_status_groups_by_asset_and_counterparty(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "auto-contract",
                        "title": "Auto smlouva",
                        "domain": "insurance",
                        "document_type": "policy",
                        "counterparty": "ČPP",
                        "related_asset": "Volvo V40",
                    },
                    {
                        "document_id": "auto-payment",
                        "title": "Auto platba",
                        "domain": "insurance",
                        "document_type": "payment_notice",
                        "counterparty": "ČPP",
                        "related_asset": "Volvo V40",
                    },
                    {
                        "document_id": "tax-doc",
                        "title": "Daňové potvrzení",
                        "domain": "tax",
                        "document_type": "confirmation",
                        "counterparty": "Generali",
                        "related_asset": "",
                    },
                    {
                        "document_id": "loose-doc",
                        "title": "Bez vazby",
                        "domain": "other",
                        "document_type": "document",
                        "counterparty": "",
                        "related_asset": "",
                    },
                    {
                        "document_id": "single-asset",
                        "title": "Samostatná věc",
                        "domain": "home",
                        "document_type": "lease",
                        "counterparty": "Pronajímatel",
                        "related_asset": "Byt",
                    },
                    {
                        "document_id": "trashed-doc",
                        "title": "Koš",
                        "lifecycle_status": "trashed",
                        "related_asset": "Volvo V40",
                    },
                ],
            )

            result = document_cases_status(vault_dir=vault)

        self.assertTrue(result["ok"])
        self.assertEqual(result["active_documents"], 5)
        self.assertEqual(result["linked_count"], 3)
        self.assertEqual(result["unlinked_count"], 2)
        self.assertEqual(result["candidate_group_count"], 4)
        self.assertEqual(result["case_count"], 1)
        self.assertEqual(result["singletons_count"], 3)
        cases = {case["label"]: case for case in result["cases"]}
        self.assertEqual(cases["Volvo V40"]["group_type"], "asset")
        self.assertEqual(cases["Volvo V40"]["group_type_label"], "Vazba podle věci")
        self.assertEqual(cases["Volvo V40"]["document_count"], 2)
        self.assertIn("stejnou související věc", cases["Volvo V40"]["summary"])
        self.assertIn("pojištění", cases["Volvo V40"]["summary"])
        self.assertEqual(cases["Volvo V40"]["documents"][0]["domain_label"], "pojištění")
        self.assertNotIn("Protistrana: Generali", cases)
        self.assertNotIn("Byt", cases)
        self.assertNotIn("Bez vazby", cases)
        self.assertNotIn("trashed-doc", json.dumps(result, ensure_ascii=False))

    def test_document_case_detail_status_returns_all_documents_in_case(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            reminders_path = root / "reminders.json"
            docs = []
            for number, document_type in enumerate(("insurance_policy", "invoice", "green_card"), start=1):
                pdf_dir = vault / "vault" / "insurance" / f"auto-doc-{number}"
                pdf_dir.mkdir(parents=True)
                pdf_path = pdf_dir / f"auto-doc-{number}.pdf"
                pdf_path.write_bytes(b"%PDF-1.4\n")
                docs.append(
                    {
                        "document_id": f"auto-doc-{number}",
                        "title": f"Auto dokument {number}",
                        "domain": "insurance",
                        "document_type": document_type,
                        "counterparty": "ČPP",
                        "related_asset": "auto",
                        "stored_path": str(pdf_path),
                    }
                )
            docs.append(
                {
                    "document_id": "penze-doc",
                    "title": "Penzijní dokument",
                    "domain": "tax",
                    "document_type": "tax-penzijni-generali",
                    "counterparty": "Generali",
                    "related_asset": "penze",
                }
            )
            self.write_jsonl(index / "documents_index.jsonl", docs)
            overview = document_cases_status(vault_dir=vault, documents_per_case=1)
            auto_case = next(item for item in overview["cases"] if item["label"] == "auto")

            detail = document_case_detail_status(case_ref=auto_case["case_ref"], vault_dir=vault, reminders_path=reminders_path)

        self.assertTrue(detail["ok"])
        self.assertEqual(detail["label"], "auto")
        self.assertEqual(detail["document_count"], 3)
        self.assertEqual(len(detail["documents"]), 3)
        self.assertTrue(detail["documents"][0]["can_open_pdf"])
        self.assertNotIn("document_id", json.dumps(detail, ensure_ascii=False))
        self.assertNotIn("penze-doc", json.dumps(detail, ensure_ascii=False))

    def test_document_case_detail_status_includes_case_health(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            reminders_path = root / "reminders.json"
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "auto-doc-1",
                        "title": "Auto pojistná smlouva",
                        "domain": "insurance",
                        "document_type": "insurance_policy",
                        "counterparty": "ČPP",
                        "related_asset": "auto",
                        "reading_status": "ok",
                    },
                    {
                        "document_id": "auto-doc-2",
                        "title": "Auto faktura",
                        "domain": "insurance",
                        "document_type": "invoice",
                        "counterparty": "ČPP",
                        "related_asset": "auto",
                        "reading_status": "ok",
                    },
                ],
            )
            self.write_jsonl(
                index / "due_dates.jsonl",
                [
                    {
                        "document_id": "auto-doc-1",
                        "date": "2026-08-01",
                        "type": "payment_due",
                        "confidence": "high",
                        "create_reminder_candidate": True,
                        "context": "Částka k úhradě 4 512 Kč Datum splatnosti 1. 8. 2026.",
                    }
                ],
            )
            reminder = self.reminder(
                "document-auto-doc-1-payment_due-2026-08-01",
                "Zaplatit ČPP autopojištění",
                "2026-08-01",
            )
            reminder["source"] = {"type": "private_document", "uid": "auto-doc-1", "date": "", "sender": ""}
            reminder["related_asset"] = "auto VOLVO V40"
            reminders_path.write_text(json.dumps({"reminders": [reminder]}, ensure_ascii=False), encoding="utf-8")
            overview = document_cases_status(vault_dir=vault)
            auto_case = next(item for item in overview["cases"] if item["label"] == "auto")

            detail = document_case_detail_status(
                case_ref=auto_case["case_ref"],
                vault_dir=vault,
                reminders_path=reminders_path,
                today=date(2026, 6, 4),
            )

        self.assertTrue(detail["ok"])
        self.assertEqual(len(detail["reminders"]), 1)
        self.assertEqual(detail["reminders"][0]["title"], "Zaplatit ČPP autopojištění")
        self.assertEqual(len(detail["due_candidates"]), 1)
        self.assertEqual(detail["due_candidates"][0]["status"], "already_reminded")
        self.assertEqual(detail["case_health"]["status"], "ok")
        self.assertEqual(detail["case_health"]["open_reminder_count"], 1)
        self.assertEqual(detail["case_health"]["review_document_count"], 0)
        signal_labels = [item["label"] for item in detail["case_health"]["signals"]]
        self.assertIn("Otevřené hlídání", signal_labels)
        self.assertIn("Termíny už hlídané", signal_labels)
        serialized = json.dumps(detail, ensure_ascii=False)
        self.assertNotIn("document_id", serialized)
        self.assertNotIn('"id"', serialized)
        self.assertNotIn("auto-doc-1", serialized)

    def test_document_case_health_reports_documents_needing_review(self) -> None:
        health = cockpit_module.document_case_health_status(
            documents=[
                {"title": "OK", "reading_status": "ok"},
                {"title": "K revizi", "reading_status": "needs_review"},
            ],
            reminders=[],
            due_candidates=[],
            conflicts=[],
        )

        self.assertEqual(health["status"], "warn")
        self.assertEqual(health["review_document_count"], 1)
        self.assertIn("Dokumenty k revizi", [item["label"] for item in health["signals"]])
        self.assertIn("dokumenty k revizi", health["summary"])

    def test_document_classification_status_reports_missing_metadata_fields(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "complete-doc",
                        "title": "Kompletní",
                        "domain": "insurance",
                        "document_type": "insurance_policy",
                        "counterparty": "ČPP",
                        "related_asset": "Volvo",
                    },
                    {
                        "document_id": "weak-1234567890",
                        "title": "Slabá klasifikace",
                        "domain": "other",
                        "document_type": "document",
                        "counterparty": "",
                        "related_asset": "",
                    },
                    {
                        "document_id": "trashed-doc",
                        "title": "Koš",
                        "domain": "other",
                        "document_type": "document",
                        "lifecycle_status": "trashed",
                    },
                ],
            )

            result = document_classification_status(vault_dir=vault)

        self.assertTrue(result["ok"])
        self.assertEqual(result["active_documents"], 2)
        self.assertEqual(result["complete_count"], 1)
        self.assertEqual(result["issue_count"], 1)
        self.assertEqual(result["field_counts"]["domain"], 1)
        self.assertEqual(result["field_counts"]["document_type"], 1)
        self.assertEqual(result["field_counts"]["counterparty"], 1)
        self.assertEqual(result["field_counts"]["related_asset"], 1)
        self.assertEqual(result["items"][0]["title"], "Slabá klasifikace")
        self.assertIn("Doplnit", result["items"][0]["recommended_action"])
        self.assertIn("ostatní / dokument", result["items"][0]["classification_summary"])
        self.assertNotIn("trashed-doc", json.dumps(result, ensure_ascii=False))

    def test_update_document_classification_metadata_updates_index_manifest_and_audit(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            index = vault / "index"
            document_dir = vault / "vault" / "other" / "weak-doc"
            index.mkdir(parents=True)
            document_dir.mkdir(parents=True)
            stored_pdf = document_dir / "weak.pdf"
            stored_pdf.write_bytes(b"%PDF-1.4\n")
            manifest_path = document_dir / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "document_id": "weak-doc",
                        "title": "Slabá klasifikace",
                        "domain": "other",
                        "document_type": "document",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "weak-1234567890",
                        "title": "Slabá klasifikace",
                        "domain": "other",
                        "document_type": "document",
                        "counterparty": "",
                        "related_asset": "",
                        "stored_path": str(stored_pdf),
                    },
                ],
            )
            classification = document_classification_status(vault_dir=vault)

            result = update_document_classification_metadata_action(
                document_id=classification["items"][0]["document_ref"],
                metadata={
                    "domain": "insurance",
                    "document_type": "insurance_policy",
                    "counterparty": "ČPP",
                    "related_asset": "auto",
                },
                vault_dir=vault,
            )

            docs = self.read_jsonl(index / "documents_index.jsonl")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            audit = self.read_jsonl(index / "document_metadata_actions.jsonl")

        self.assertTrue(result["ok"])
        self.assertEqual(result["missing_fields"], [])
        self.assertEqual(result["document_classification"]["issue_count"], 0)
        self.assertEqual(docs[0]["domain"], "insurance")
        self.assertEqual(docs[0]["document_type"], "insurance_policy")
        self.assertEqual(docs[0]["counterparty"], "ČPP")
        self.assertEqual(docs[0]["related_asset"], "auto")
        self.assertEqual(manifest["domain"], "insurance")
        self.assertEqual(manifest["document_type"], "insurance_policy")
        self.assertEqual(audit[0]["action"], "update_classification_metadata")
        self.assertEqual(audit[0]["document_id"], "weak-1234567890")
        self.assertIn("metadata_backups", audit[0]["backup_dir"])

    def test_document_due_candidates_status_filters_noise_and_marks_existing_reminders(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            reminders_path = root / "reminders.json"
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "doc-ready",
                        "title": "Faktura budoucí",
                        "domain": "insurance",
                        "document_type": "invoice",
                        "related_asset": "auto",
                    },
                    {
                        "document_id": "doc-existing",
                        "title": "Pojistka už hlídaná",
                        "domain": "insurance",
                        "document_type": "insurance_policy",
                        "related_asset": "auto",
                    },
                    {
                        "document_id": "doc-past",
                        "title": "Stará splatnost",
                        "domain": "insurance",
                        "document_type": "invoice",
                    },
                    {
                        "document_id": "doc-trashed",
                        "title": "Koš",
                        "lifecycle_status": "trashed",
                    },
                ],
            )
            self.write_jsonl(
                index / "due_dates.jsonl",
                [
                    {
                        "document_id": "doc-ready",
                        "date": "2026-08-01",
                        "type": "payment_due",
                        "confidence": "high",
                        "create_reminder_candidate": True,
                        "context": "Částka k úhradě 1 234 Kč Datum splatnosti 1. 8. 2026.",
                    },
                    {
                        "document_id": "doc-existing",
                        "date": "2026-09-01",
                        "type": "payment_due",
                        "confidence": "high",
                        "create_reminder_candidate": True,
                        "context": "Datum splatnosti 1. 9. 2026.",
                    },
                    {
                        "document_id": "doc-past",
                        "date": "2026-05-01",
                        "type": "payment_due",
                        "confidence": "high",
                        "create_reminder_candidate": True,
                        "context": "Datum splatnosti 1. 5. 2026.",
                    },
                    {
                        "document_id": "doc-ready",
                        "date": "2026-08-02",
                        "type": "context_date",
                        "confidence": "medium",
                        "create_reminder_candidate": False,
                        "context": "Datum vystavení 2. 8. 2026.",
                    },
                    {
                        "document_id": "doc-trashed",
                        "date": "2026-10-01",
                        "type": "payment_due",
                        "confidence": "high",
                        "create_reminder_candidate": True,
                        "context": "Datum splatnosti 1. 10. 2026.",
                    },
                ],
            )
            reminders_path.write_text(
                json.dumps(
                    {
                        "reminders": [
                            self.reminder(
                                "document-doc-existing-payment_due-2026-09-01",
                                "Už existuje",
                                "2026-09-01",
                            )
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = document_due_candidates_status(vault_dir=vault, reminders_path=reminders_path, today=date(2026, 6, 4))

        self.assertTrue(result["ok"])
        self.assertEqual(result["candidate_count"], 3)
        self.assertEqual(result["actionable_count"], 1)
        self.assertEqual(result["already_reminded_count"], 1)
        self.assertEqual(result["past_count"], 1)
        self.assertEqual(result["items"][0]["status"], "ready")
        self.assertEqual(result["items"][0]["amount_due"], "1 234 Kč")
        self.assertNotIn("document_id", result["items"][0])
        self.assertNotIn("doc-trashed", json.dumps(result, ensure_ascii=False))

    def test_document_due_candidate_uses_existing_reminder_amount_for_resolved_cpp_maxi_variant(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            reminders_path = root / "reminders.json"
            document_id = "cpp-predpis-pojistne-smlouvy-3270612451-2026"
            reminder_id = f"document-{document_id}-payment_due-2026-08-01"
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": document_id,
                        "title": "ČPP předpis pojistného",
                        "domain": "insurance",
                        "document_type": "insurance_payment_notice",
                        "related_asset": "auto VOLVO V40 CROSS COUNTRY SPZ 4SN8981",
                    }
                ],
            )
            self.write_jsonl(
                index / "text_index.jsonl",
                [
                    {
                        "document_id": document_id,
                        "text": (
                            "Vaše nově předepsané pojistné činí 4 512 Kč/ ročně. "
                            "Roční pojistné za doplňkové pojištění nákladů na nájem "
                            "náhradního vozidla MAXI: 499 Kč. "
                            "Pojistné za pojistné období (navýšené o doplňkové "
                            "pojištění nákladů na nájem náhradního vozidla MAXI): 5 011 Kč."
                        ),
                    }
                ],
            )
            self.write_jsonl(
                index / "due_dates.jsonl",
                [
                    {
                        "document_id": document_id,
                        "date": "2026-08-01",
                        "type": "payment_due",
                        "confidence": "high",
                        "create_reminder_candidate": True,
                        "context": "K ÚHRADĚ 5 011 Kč DATUM SPLATNOSTI 1. 8. 2026 4 512 Kč",
                    }
                ],
            )
            reminder = self.reminder(reminder_id, "Zaplatit ČPP autopojištění", "2026-08-01")
            reminder["amount_due"] = "4 512 Kč"
            reminder["amount_note"] = "Platíme základ bez doplňkového MAXI."
            reminders_path.write_text(json.dumps({"reminders": [reminder]}, ensure_ascii=False), encoding="utf-8")

            result = document_due_candidates_status(vault_dir=vault, reminders_path=reminders_path, today=date(2026, 6, 4))

        self.assertTrue(result["ok"])
        self.assertEqual(result["already_reminded_count"], 1)
        self.assertEqual(result["items"][0]["status"], "already_reminded")
        self.assertEqual(result["items"][0]["amount_due"], "4 512 Kč")
        self.assertEqual(result["items"][0]["amount_note"], "Platíme základ bez doplňkového MAXI.")

    def test_create_document_due_reminder_requires_confirmation_and_writes_safe_reminder(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            reminders_path = root / "reminders.json"
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "doc-ready",
                        "title": "Faktura budoucí",
                        "domain": "insurance",
                        "document_type": "invoice",
                        "related_asset": "auto",
                    }
                ],
            )
            self.write_jsonl(
                index / "due_dates.jsonl",
                [
                    {
                        "document_id": "doc-ready",
                        "date": "2026-08-01",
                        "type": "payment_due",
                        "confidence": "high",
                        "create_reminder_candidate": True,
                        "context": "Částka k úhradě 1 234 Kč Datum splatnosti 1. 8. 2026.",
                    }
                ],
            )
            candidate = document_due_candidates_status(
                vault_dir=vault,
                reminders_path=reminders_path,
                today=date(2026, 6, 4),
            )["items"][0]

            rejected = create_document_due_reminder_action(
                candidate_ref=candidate["candidate_ref"],
                confirmed=False,
                vault_dir=vault,
                reminders_path=reminders_path,
                today=date(2026, 6, 4),
            )
            created = create_document_due_reminder_action(
                candidate_ref=candidate["candidate_ref"],
                title="Zaplatit testovací fakturu",
                notes="Potvrzeno z dokumentového kandidáta.",
                confirmed=True,
                vault_dir=vault,
                reminders_path=reminders_path,
                today=date(2026, 6, 4),
            )
            store = json.loads(reminders_path.read_text(encoding="utf-8"))

        self.assertFalse(rejected["ok"])
        self.assertTrue(created["ok"])
        self.assertEqual(store["reminders"][0]["id"], "document-doc-ready-payment_due-2026-08-01")
        self.assertEqual(store["reminders"][0]["title"], "Zaplatit testovací fakturu")
        self.assertEqual(store["reminders"][0]["source"]["type"], "private_document")
        self.assertEqual(store["reminders"][0]["related_asset"], "auto")
        self.assertEqual(store["reminders"][0]["amount_due"], "1 234 Kč")
        self.assertEqual(created["document_due_candidates"]["already_reminded_count"], 1)

    def test_document_review_report_status_flags_safe_review_candidates(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "clean-doc",
                        "title": "Clean",
                        "domain": "tax",
                        "document_type": "confirmation",
                        "counterparty": "Generali",
                        "related_asset": "penze",
                        "text_extraction": {"method": "pdftotext", "indexed_chars": 1200},
                    },
                    {
                        "document_id": "zero-doc",
                        "title": "Zero",
                        "domain": "insurance",
                        "document_type": "policy",
                        "reading_status": "needs_review",
                        "text_extraction": {"method": "pdftotext-empty", "ocr_needed": True, "indexed_chars": 0},
                    },
                    {
                        "document_id": "short-doc",
                        "title": "Short",
                        "domain": "other",
                        "document_type": "document",
                        "counterparty": "",
                        "related_asset": "",
                        "text_extraction": {"method": "pdftotext", "indexed_chars": 20},
                    },
                    {
                        "document_id": "trashed-doc",
                        "title": "Trashed",
                        "domain": "other",
                        "document_type": "document",
                        "lifecycle_status": "trashed",
                    },
                ],
            )
            self.write_jsonl(
                index / "text_index.jsonl",
                [
                    {"document_id": "clean-doc", "text": "x" * 1200},
                    {"document_id": "zero-doc", "text": ""},
                    {"document_id": "short-doc", "text": "secret content that must not be returned"},
                ],
            )

            report = document_review_report_status(vault_dir=vault)

            self.assertEqual(report["summary"]["total_indexed"], 4)
            self.assertEqual(report["summary"]["active_documents"], 3)
            self.assertEqual(report["summary"]["candidate_count"], 2)
            self.assertEqual(report["summary"]["reason_counts"]["zero_text"], 1)
            self.assertEqual(report["summary"]["reason_counts"]["short_text"], 1)
            self.assertEqual(report["summary"]["reason_counts"]["ocr_needed"], 1)
            groups = {group["id"]: group for group in report["groups"]}
            self.assertEqual(groups["zero_text"]["count"], 1)
            self.assertEqual(groups["short_text"]["count"], 1)
            self.assertEqual(groups["weak_metadata"]["count"], 0)
            self.assertEqual(groups["ok"]["count"], 1)
            self.assertIn("OCR", groups["zero_text"]["recommended_action"])
            self.assertIn("metadata", groups["weak_metadata"]["recommended_action"])
            self.assertNotIn("secret content", json.dumps(report, ensure_ascii=False))
            by_id = {item["document_id"]: item for item in report["items"]}
            self.assertIn("zero-doc", by_id)
            self.assertIn("short-doc", by_id)
            self.assertNotIn("clean-doc", by_id)
            self.assertNotIn("trashed-doc", by_id)
            self.assertEqual(by_id["zero-doc"]["decision_group"], "zero_text")
            self.assertEqual(by_id["short-doc"]["decision_group"], "short_text")
            self.assertIn("OCR", by_id["zero-doc"]["recommended_action"])
            self.assertIn("domain", by_id["short-doc"]["weak_metadata_fields"])
            self.assertIn("oblast", by_id["short-doc"]["weak_metadata_labels"])
            self.assertIn("doplnit:", by_id["short-doc"]["review_summary"])
            self.assertIn("Čtení:", by_id["short-doc"]["reading_summary"])
            self.assertIn("protistrana", json.dumps(report, ensure_ascii=False))

    def test_action_queue_prioritizes_conflicts_and_nearest_work(self) -> None:
        document_work = {
            "new_pdfs": [
                {"name": "new.pdf", "status": "new", "modified_at": "2026-06-04T09:00:00+00:00"},
            ],
            "problems": [
                {"name": "encrypted.pdf", "problem_label": "šifrované PDF", "modified_at": "2026-06-04T08:00:00+00:00"},
            ],
            "review": {
                "next_items": [
                    {"document_id": "doc-1", "title": "Pojistka", "domain": "insurance", "document_type": "policy"},
                ],
            },
        }
        reminders = {
            "conflicts": [
                {
                    "asset": "auto",
                    "coverage_start": "2026-07-01",
                    "items": [{"title": "Platba A"}, {"title": "Platba B"}],
                },
            ],
            "groups": {
                "overdue": [{"title": "Po termínu", "due_date": "2026-06-01", "amount_due": "100 Kč"}],
                "today": [],
                "soon": [{"title": "Brzy", "due_date": "2026-06-10"}],
            },
        }

        queue = action_queue_status(document_work=document_work, reminders=reminders, limit=6)

        self.assertTrue(queue["ok"])
        self.assertEqual(queue["items"][0]["kind"], "payment_conflict")
        self.assertEqual(queue["items"][1]["kind"], "document_problem")
        self.assertIn("open_reminders", [item["action"] for item in queue["items"]])
        self.assertIn("open_scandocu", [item["action"] for item in queue["items"]])
        self.assertEqual(queue["counts"]["priority_1"], 3)

    def test_cockpit_html_contains_document_work_controls(self) -> None:
        self.assertIn("Dnes", COCKPIT_HTML)
        self.assertIn("Stav", COCKPIT_HTML)
        self.assertIn("Akce", COCKPIT_HTML)
        self.assertIn("janickaBtn", COCKPIT_HTML)
        self.assertIn("Janička", COCKPIT_HTML)
        self.assertIn("janickaModal", COCKPIT_HTML)
        self.assertIn("Samantha bez technické vrstvy", COCKPIT_HTML)
        self.assertIn("janickaFindDocumentBtn", COCKPIT_HTML)
        self.assertIn("janickaPrintDocumentBtn", COCKPIT_HTML)
        self.assertIn("janickaEmailBtn", COCKPIT_HTML)
        self.assertIn("janickaLekarnaBtn", COCKPIT_HTML)
        self.assertIn("janickaFamilyBtn", COCKPIT_HTML)
        self.assertIn("janickaAskAdamBtn", COCKPIT_HTML)
        self.assertIn("janickaChatModal", COCKPIT_HTML)
        self.assertIn("janickaChatInput", COCKPIT_HTML)
        self.assertIn("janickaChatSendBtn", COCKPIT_HTML)
        self.assertIn("/api/janicka/chat", COCKPIT_HTML)
        self.assertIn("/api/janicka/chat/latest", COCKPIT_HTML)
        self.assertIn("/api/adam/status", COCKPIT_HTML)
        self.assertIn("/api/adam/start", COCKPIT_HTML)
        self.assertIn("/api/adam/restart", COCKPIT_HTML)
        self.assertIn("/api/adam/stop", COCKPIT_HTML)
        self.assertIn("janickaAdamStartBtn", COCKPIT_HTML)
        self.assertIn("janickaAdamRestartBtn", COCKPIT_HTML)
        self.assertIn("janickaAdamStopBtn", COCKPIT_HTML)
        self.assertIn("submitJanickaChat", COCKPIT_HTML)
        self.assertIn("pollJanickaCodexReply", COCKPIT_HTML)
        self.assertIn("janickaRecoveryBtn", COCKPIT_HTML)
        self.assertIn("janickaCookbookBtn", COCKPIT_HTML)
        self.assertIn("/janicka-kucharka/", COCKPIT_HTML)
        self.assertIn("janickaReturnBtn", COCKPIT_HTML)
        self.assertIn("openJanickaModal", COCKPIT_HTML)
        self.assertIn("focusDocumentSearchForJanicka", COCKPIT_HTML)
        self.assertIn("openCatalogAppById", COCKPIT_HTML)
        self.assertIn("armJanickaModalReturn", COCKPIT_HTML)
        self.assertIn("maybeReturnToJanicka", COCKPIT_HTML)
        self.assertIn("Zpět k Janičce", COCKPIT_HTML)
        self.assertIn('armJanickaModalReturn("webApps")', COCKPIT_HTML)
        self.assertIn('armJanickaModalReturn("projects")', COCKPIT_HTML)
        self.assertIn('armJanickaModalReturn("reminders")', COCKPIT_HTML)
        self.assertIn('armJanickaModalReturn("recovery")', COCKPIT_HTML)
        self.assertIn("todayNewPdfCount", COCKPIT_HTML)
        self.assertIn("dashboardScanDocu", COCKPIT_HTML)
        self.assertIn("dashboardGit", COCKPIT_HTML)
        self.assertIn("git-safe", COCKPIT_HTML)
        self.assertIn("private/family mimo", COCKPIT_HTML)
        self.assertIn("dashboardOverall", COCKPIT_HTML)
        self.assertIn("dashboardOverallLabel", COCKPIT_HTML)
        self.assertIn("dashboardOverallReason", COCKPIT_HTML)
        self.assertIn('title="Otevřít detail stavu"', COCKPIT_HTML)
        self.assertIn("dashboard-overall-warn", COCKPIT_HTML)
        self.assertIn("Akce potřeba", COCKPIT_HTML)
        self.assertIn("updateDashboardOverallStatus", COCKPIT_HTML)
        self.assertIn("setDashboardStatusSignal", COCKPIT_HTML)
        self.assertIn("dashboardStatusPriority", COCKPIT_HTML)
        self.assertIn("dashboardValueIsPending", COCKPIT_HTML)
        self.assertIn("dashboard-updated", COCKPIT_HTML)
        self.assertIn("setDashboardValue", COCKPIT_HTML)
        self.assertIn("formatDashboardLoadedAt", COCKPIT_HTML)
        self.assertIn("dashboardProcessBtn", COCKPIT_HTML)
        self.assertIn("dashboardTerminalBtn", COCKPIT_HTML)
        self.assertIn("dashboardQuantitativeBtn", COCKPIT_HTML)
        self.assertIn("projectsBtn", COCKPIT_HTML)
        self.assertIn("dashboardProjects", COCKPIT_HTML)
        self.assertIn("projectsModal", COCKPIT_HTML)
        self.assertIn("Projekty a schopnosti", COCKPIT_HTML)
        self.assertIn('data-project-filter="tools"', COCKPIT_HTML)
        self.assertIn('data-project-filter="infrastructure"', COCKPIT_HTML)
        self.assertIn('data-project-filter="needs_attention"', COCKPIT_HTML)
        self.assertIn("needs-attention", COCKPIT_HTML)
        self.assertIn("management_reason", COCKPIT_HTML)
        self.assertIn("/api/projects/status", COCKPIT_HTML)
        self.assertNotIn('id="quantitativeBtn"', COCKPIT_HTML)
        self.assertIn("dashboardQuantitative", COCKPIT_HTML)
        self.assertIn("dashboardQuantitativeBtn", COCKPIT_HTML)
        self.assertIn("quantitativeModal", COCKPIT_HTML)
        self.assertIn("/api/quantitative-status", COCKPIT_HTML)
        self.assertIn("dashboardQuickNotesBtn", COCKPIT_HTML)
        self.assertIn("dashboardQuickNotes", COCKPIT_HTML)
        self.assertIn("refreshQuickNotesSummary", COCKPIT_HTML)
        self.assertIn("quickNotesModal", COCKPIT_HTML)
        self.assertIn("/api/quick-notes/status", COCKPIT_HTML)
        self.assertIn("/api/quick-notes/detail", COCKPIT_HTML)
        self.assertIn("openQuickNotesModal", COCKPIT_HTML)
        self.assertIn("loadQuickNoteDetail", COCKPIT_HTML)
        self.assertIn("quickNoteTriageLine", COCKPIT_HTML)
        self.assertIn("Klasifikace", COCKPIT_HTML)
        self.assertIn("dashboardUrgentRemindersBtn", COCKPIT_HTML)
        self.assertIn("urgentReminderAlert", COCKPIT_HTML)
        self.assertIn("urgentRemindersModal", COCKPIT_HTML)
        self.assertIn("/api/urgent-reminders/status", COCKPIT_HTML)
        self.assertIn("/api/urgent-reminders/done", COCKPIT_HTML)
        self.assertIn("openUrgentRemindersModal", COCKPIT_HTML)
        self.assertIn("refreshUrgentRemindersSummary", COCKPIT_HTML)
        self.assertIn("URGENT_REMINDERS_MONITOR_MS = 30 * 1000", COCKPIT_HTML)
        self.assertIn("urgentReminderBodyText", COCKPIT_HTML)
        self.assertIn("urgent-alert-detail", COCKPIT_HTML)
        self.assertIn("urgent-reminder-body", COCKPIT_HTML)
        self.assertIn("Důležitá připomenutí: chyba načtení", COCKPIT_HTML)
        self.assertIn("hasLoadError", COCKPIT_HTML)
        self.assertIn("markUrgentReminderDone", COCKPIT_HTML)
        self.assertIn("dashboardRecoveryBtn", COCKPIT_HTML)
        self.assertIn("recoveryModal", COCKPIT_HTML)
        self.assertIn("/api/recovery/status", COCKPIT_HTML)
        self.assertIn("openRecoveryModal", COCKPIT_HTML)
        self.assertIn("dashboardDiagnosticsBtn", COCKPIT_HTML)
        self.assertIn("diagnosticsModal", COCKPIT_HTML)
        self.assertIn("diagnosticsStatusSignals", COCKPIT_HTML)
        self.assertIn("renderDiagnosticsStatusSignals", COCKPIT_HTML)
        self.assertIn("dashboardSignalLabel", COCKPIT_HTML)
        self.assertIn("dashboardSignalMeaning", COCKPIT_HTML)
        self.assertIn("dashboardSignalNextAction", COCKPIT_HTML)
        self.assertIn(".diagnostics-row.loading", COCKPIT_HTML)
        self.assertIn("samostatné načítání", COCKPIT_HTML)
        self.assertIn("Co teď:", COCKPIT_HTML)
        self.assertIn("Čekám na kontroly", COCKPIT_HTML)
        self.assertIn("openDiagnosticsModal", COCKPIT_HTML)
        self.assertIn("renderDiagnosticsEndpointRows", COCKPIT_HTML)
        self.assertIn("diagnosticsEndpoints", COCKPIT_HTML)
        self.assertIn("/api/web-apps", COCKPIT_HTML)
        self.assertIn("dashboardRestartBtn", COCKPIT_HTML)
        self.assertIn("Restart Cockpitu", COCKPIT_HTML)
        self.assertIn("restartCockpit", COCKPIT_HTML)
        self.assertIn("/api/cockpit/restart", COCKPIT_HTML)
        self.assertIn("dashboardSpeakBtn", COCKPIT_HTML)
        self.assertIn("Přečíst stav", COCKPIT_HTML)
        self.assertIn("dashboardSpeakSelectionBtn", COCKPIT_HTML)
        self.assertIn("Přečíst výběr", COCKPIT_HTML)
        self.assertIn("dashboardMorningSentence", COCKPIT_HTML)
        self.assertIn("Ranní stav", COCKPIT_HTML)
        self.assertIn("lastSelectedSpeechText", COCKPIT_HTML)
        self.assertIn("captureSelectedSpeechText", COCKPIT_HTML)
        self.assertIn('addEventListener("pointerdown", captureSelectedSpeechText)', COCKPIT_HTML)
        self.assertIn("speakSelectedText", COCKPIT_HTML)
        self.assertIn("speakDashboardStatus", COCKPIT_HTML)
        self.assertIn("function escapeHtml(value)", COCKPIT_HTML)
        self.assertIn("/api/speech/speak", COCKPIT_HTML)
        self.assertIn("/api/speech/edge-tts", COCKPIT_HTML)
        self.assertIn("audio_base64", COCKPIT_HTML)
        self.assertIn("new Audio", COCKPIT_HTML)
        self.assertIn("voiceRecordBtn", COCKPIT_HTML)
        self.assertIn("voiceModeToggleBtn", COCKPIT_HTML)
        self.assertIn("dashboardVoiceMode", COCKPIT_HTML)
        self.assertIn("voiceModeRuntimeStatus", COCKPIT_HTML)
        self.assertIn("voicePendingStatus", COCKPIT_HTML)
        self.assertIn("voiceLastResponseCard", COCKPIT_HTML)
        self.assertIn("voiceLastResponseSpeakBtn", COCKPIT_HTML)
        self.assertIn("Přehrát Adamovu odpověď", COCKPIT_HTML)
        self.assertIn("voiceApprovalCard", COCKPIT_HTML)
        self.assertIn("voiceApprovalApproveBtn", COCKPIT_HTML)
        self.assertIn("voiceApprovalRejectBtn", COCKPIT_HTML)
        self.assertIn("Schválení přes Cockpit", COCKPIT_HTML)
        self.assertIn("Schválit", COCKPIT_HTML)
        self.assertIn("Zamítnout", COCKPIT_HTML)
        self.assertIn("/api/voice-mode/approval", COCKPIT_HTML)
        self.assertIn("renderVoiceLastResponse", COCKPIT_HTML)
        self.assertIn("renderVoiceApproval", COCKPIT_HTML)
        self.assertIn("speakLastAdamResponse", COCKPIT_HTML)
        self.assertIn("submitVoiceApproval", COCKPIT_HTML)
        self.assertIn("voiceBridgeSessions", COCKPIT_HTML)
        self.assertIn("-> voice bridge", COCKPIT_HTML)
        self.assertIn("Codex relace:", COCKPIT_HTML)
        self.assertIn("Čeká hlasový pokyn na Adama", COCKPIT_HTML)
        self.assertIn("čeká pokyn", COCKPIT_HTML)
        self.assertIn("voiceModeStartBtn", COCKPIT_HTML)
        self.assertIn("voiceModeStopBtn", COCKPIT_HTML)
        self.assertIn("voiceBridgeStatus", COCKPIT_HTML)
        self.assertIn("Terminálový bridge", COCKPIT_HTML)
        self.assertIn('voiceTranscript.value = "";', COCKPIT_HTML)
        self.assertIn("/api/voice-mode/start", COCKPIT_HTML)
        self.assertIn("/api/voice-mode/stop", COCKPIT_HTML)
        self.assertIn("Spustit Adamův poslech", COCKPIT_HTML)
        self.assertIn("Poslech běží", COCKPIT_HTML)
        self.assertIn("Poslech neběží", COCKPIT_HTML)
        self.assertIn(".voice-command-actions button:disabled", COCKPIT_HTML)
        self.assertIn("Adam Voice Mode watcher", COCKPIT_HTML)
        self.assertIn("Hlasový mód: vypnuto", COCKPIT_HTML)
        self.assertIn("samanthaVoiceModeEnabled", COCKPIT_HTML)
        self.assertIn("toggleVoiceMode", COCKPIT_HTML)
        self.assertIn("scripts/adam_voice_mode.py", COCKPIT_HTML)
        update_start = COCKPIT_HTML.index("function updateVoiceModeUi()")
        toggle_start = COCKPIT_HTML.index("function toggleVoiceMode()")
        escape_start = COCKPIT_HTML.index("function escapeHtml(value)")
        voice_dashboard_escape = COCKPIT_HTML.index("${escapeHtml(voiceState)}")
        self.assertLess(update_start, toggle_start)
        self.assertLess(escape_start, voice_dashboard_escape)
        self.assertRegex(
            COCKPIT_HTML,
            r"voiceStopTimer = null;\s*}\s*}\s*function updateVoiceModeUi\(\)",
        )
        self.assertIn("Nahrát hlasový pokyn", COCKPIT_HTML)
        self.assertIn("voiceStopBtn", COCKPIT_HTML)
        self.assertIn("voiceTranscript", COCKPIT_HTML)
        self.assertIn("voiceTranscriptSendBtn", COCKPIT_HTML)
        self.assertIn("Odeslat přepis Adamovi", COCKPIT_HTML)
        self.assertIn("startVoiceRecording", COCKPIT_HTML)
        self.assertIn("transcribeVoiceRecording", COCKPIT_HTML)
        self.assertIn("submitVoiceTranscript", COCKPIT_HTML)
        self.assertIn("/api/speech/transcribe", COCKPIT_HTML)
        self.assertIn("/api/speech/voice-text", COCKPIT_HTML)
        self.assertIn("Tento prohlížeč nepodporuje přímé nahrávání.", COCKPIT_HTML)
        self.assertIn("frontendHealthPanel", COCKPIT_HTML)
        self.assertIn("frontendHealthJs", COCKPIT_HTML)
        self.assertIn("JS se zatím nespustil", COCKPIT_HTML)
        self.assertIn("Co teď dělat", COCKPIT_HTML)
        self.assertIn("actionQueueStatus", COCKPIT_HTML)
        self.assertIn("actionQueueList", COCKPIT_HTML)
        self.assertIn("renderActionQueue", COCKPIT_HTML)
        self.assertIn("actionQueueButton", COCKPIT_HTML)
        self.assertIn("INTAKE_LOCAL_MONITOR_MS = 10 * 60 * 1000", COCKPIT_HTML)
        self.assertIn("INTAKE_EMAIL_MONITOR_MS = 30 * 60 * 1000", COCKPIT_HTML)
        self.assertIn("runEmailIntakeMonitor", COCKPIT_HTML)
        self.assertIn("hideEmailIntakeCandidate", COCKPIT_HTML)
        self.assertIn("Neukazovat", COCKPIT_HTML)
        self.assertIn("filter_reasons", COCKPIT_HTML)
        self.assertIn("/api/documents/intake-email-scan", COCKPIT_HTML)
        self.assertIn("recordFrontendError", COCKPIT_HTML)
        self.assertIn("clearFrontendErrorsMatching", COCKPIT_HTML)
        self.assertIn("verifyButtonHealth", COCKPIT_HTML)
        self.assertIn("runFrontendHealthCheck", COCKPIT_HTML)
        self.assertIn('window.addEventListener("error"', COCKPIT_HTML)
        self.assertIn("remindersBtn", COCKPIT_HTML)
        self.assertIn("dashboardReminders", COCKPIT_HTML)
        self.assertIn("dashboardConsistency", COCKPIT_HTML)
        self.assertIn("Consistency Audit", COCKPIT_HTML)
        self.assertIn("consistencyText", COCKPIT_HTML)
        self.assertIn("renderConsistencyAudit", COCKPIT_HTML)
        self.assertIn("resolveConsistencyFinding", COCKPIT_HTML)
        self.assertIn("Označit jako OK", COCKPIT_HTML)
        self.assertIn("/api/consistency/resolve-finding", COCKPIT_HTML)
        self.assertIn("consistency-finding", COCKPIT_HTML)
        self.assertIn("setDashboardPendingIfEmpty", COCKPIT_HTML)
        self.assertIn("escapeDashboardHtml", COCKPIT_HTML)
        self.assertIn("consistencyDashboardSummary", COCKPIT_HTML)
        self.assertIn("suppressed_finding_count", COCKPIT_HTML)
        self.assertIn("potlačeno", COCKPIT_HTML)
        self.assertIn("v 3dennim intervalu", COCKPIT_HTML)
        self.assertIn("/api/consistency-status", COCKPIT_HTML)
        self.assertIn("renderDashboard(data)", COCKPIT_HTML)
        self.assertNotIn('id="samanthaChatBtn"', COCKPIT_HTML)
        self.assertNotIn('id="codexCliBtn"', COCKPIT_HTML)
        self.assertNotIn('id="terminalBtn"', COCKPIT_HTML)
        self.assertIn("Práce s dokumenty", COCKPIT_HTML)
        self.assertIn("Nová PDF ve Downloads", COCKPIT_HTML)
        self.assertIn("Uložené dokumenty k revizi", COCKPIT_HTML)
        self.assertIn("Problémy", COCKPIT_HTML)
        self.assertIn("Dokumentový intake", COCKPIT_HTML)
        self.assertIn("documentIntakeCount", COCKPIT_HTML)
        self.assertIn("documentIntakeSummary", COCKPIT_HTML)
        self.assertIn("documentIntakeList", COCKPIT_HTML)
        self.assertIn("renderDocumentIntake", COCKPIT_HTML)
        self.assertIn("unified_items", COCKPIT_HTML)
        self.assertIn("Souhrn zdrojů", COCKPIT_HTML)
        self.assertIn("E-mail kandidáti", COCKPIT_HTML)
        self.assertIn("Downloads / e-mail / mobilní sken / lokální inbox", COCKPIT_HTML)
        self.assertIn("Vazby / cases", COCKPIT_HTML)
        self.assertIn("documentCasesCount", COCKPIT_HTML)
        self.assertIn("documentCasesList", COCKPIT_HTML)
        self.assertIn("renderDocumentCases", COCKPIT_HTML)
        self.assertIn("Detail case", COCKPIT_HTML)
        self.assertIn("loadDocumentCaseDetail", COCKPIT_HTML)
        self.assertIn("appendDocumentCaseSection", COCKPIT_HTML)
        self.assertIn("appendDocumentCaseHealthSignals", COCKPIT_HTML)
        self.assertIn("Proč tento stav", COCKPIT_HTML)
        self.assertIn("Termíny case", COCKPIT_HTML)
        self.assertIn("/api/documents/case-detail", COCKPIT_HTML)
        self.assertIn("Klasifikace", COCKPIT_HTML)
        self.assertIn("documentClassificationCount", COCKPIT_HTML)
        self.assertIn("documentClassificationList", COCKPIT_HTML)
        self.assertIn("renderDocumentClassification", COCKPIT_HTML)
        self.assertIn("Doplnit metadata", COCKPIT_HTML)
        self.assertIn("updateDocumentClassificationMetadata", COCKPIT_HTML)
        self.assertIn("/api/documents/classification-metadata", COCKPIT_HTML)
        self.assertIn("Termíny v dokumentech", COCKPIT_HTML)
        self.assertIn("documentDueCount", COCKPIT_HTML)
        self.assertIn("documentDueList", COCKPIT_HTML)
        self.assertIn("renderDocumentDueCandidates", COCKPIT_HTML)
        self.assertIn("Vytvořit připomínku", COCKPIT_HTML)
        self.assertIn("/api/documents/due-reminder", COCKPIT_HTML)
        self.assertIn("Dokumenty k revizi", COCKPIT_HTML)
        self.assertIn("reviewReportBtn", COCKPIT_HTML)
        self.assertIn("/api/documents/review-report", COCKPIT_HTML)
        self.assertIn("loadDocumentReviewReport", COCKPIT_HTML)
        self.assertIn("renderDocumentReviewReportItem", COCKPIT_HTML)
        self.assertIn("review-group", COCKPIT_HTML)
        self.assertIn("review-report-list", COCKPIT_HTML)
        self.assertIn('id="reviewReportList" class="work-list review-report-list"', COCKPIT_HTML)
        self.assertIn("Bez textu / OCR", COCKPIT_HTML)
        self.assertIn("Krátký text", COCKPIT_HTML)
        self.assertIn("Slabá metadata", COCKPIT_HTML)
        self.assertIn("V pořádku", COCKPIT_HTML)
        self.assertIn("Zpracovat další dokument", COCKPIT_HTML)
        self.assertIn("Reminders", COCKPIT_HTML)
        self.assertIn("remindersModal", COCKPIT_HTML)
        self.assertIn("/api/reminders", COCKPIT_HTML)
        self.assertIn("/api/reminders/done", COCKPIT_HTML)
        self.assertIn("/api/reminders/cancel-payment", COCKPIT_HTML)
        self.assertIn("/api/reminders/source", COCKPIT_HTML)
        self.assertIn("/documents/read?document_id=", COCKPIT_HTML)
        self.assertIn("markReminderDone", COCKPIT_HTML)
        self.assertIn("cancelPaymentReminder", COCKPIT_HTML)
        self.assertIn("loadReminderSource", COCKPIT_HTML)
        self.assertIn("item.reminder_ref", COCKPIT_HTML)
        self.assertIn("renderReminderConflicts", COCKPIT_HTML)
        self.assertIn("Konflikt plateb", COCKPIT_HTML)
        self.assertIn("Uzavřít jako zrušené", COCKPIT_HTML)
        self.assertIn("Otevřít PDF", COCKPIT_HTML)
        self.assertIn("Splněno", COCKPIT_HTML)
        self.assertIn("Zdroj", COCKPIT_HTML)
        self.assertIn("Souhrn vaultu", COCKPIT_HTML)
        self.assertIn("Auditní historie inboxu", COCKPIT_HTML)
        self.assertIn('const marker = "\\n- Inbox audit";', COCKPIT_HTML)

    def test_cockpit_status_keeps_heavy_reports_out_of_main_refresh(self) -> None:
        with (
            patch("app.cockpit.safe_downloads_status", return_value={"ok": True, "items": []}),
            patch("app.cockpit.document_work_status", return_value={"summary": {}}),
            patch("app.cockpit.document_intake_status", return_value={"ok": True, "count": 0, "sources": []}),
            patch("app.cockpit.document_cases_status", return_value={"ok": True, "case_count": 0, "cases": []}),
            patch("app.cockpit.document_classification_status", return_value={"ok": True, "issue_count": 0, "items": []}),
            patch("app.cockpit.document_due_candidates_status", return_value={"ok": True, "actionable_count": 0, "items": []}),
            patch(
                "app.cockpit.backup_activity_status",
                return_value={"ok": True, "status": "ok", "message": "backup ok"},
            ),
            patch("app.cockpit.document_vault_status_summary", return_value="vault ok"),
            patch("app.cockpit.reminders_status", return_value={"ok": True, "counts": {}}),
            patch("app.cockpit.probe_scandocu", return_value={"running": False}),
            patch("app.cockpit.load_voice_mode_status", return_value={"ok": True, "running": False, "state": "stopped"}),
            patch("app.cockpit.adam_voice_bridge_status", return_value={"ok": True, "status": "ok"}),
            patch("app.cockpit.git_status_summary", return_value={"ok": True}),
        ):
            status = cockpit_status()

        self.assertIn("document_work", status)
        self.assertIn("document_intake", status)
        self.assertIn("document_cases", status)
        self.assertIn("document_classification", status)
        self.assertIn("document_due_candidates", status)
        self.assertIn("action_queue", status)
        self.assertEqual(status["backup"], "backup ok")
        self.assertEqual(status["backup_status"]["status"], "ok")
        self.assertIn("reminders", status)
        self.assertIn("voice_mode", status)
        self.assertIn("voice_bridge", status)
        self.assertIn("git", status)
        self.assertNotIn("quantitative", status)
        self.assertNotIn("projects", status)
        self.assertNotIn("consistency", status)

    def test_adam_voice_bridge_status_warns_about_multiple_codex_ttys_without_screen(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            marker_path = Path(temp_dir) / "current_codex_tty.json"
            marker_path.write_text(
                json.dumps(
                    {
                        "tty": "ttys002",
                        "marked_at": "2026-06-06T05:07:45+00:00",
                        "parent_pid": 73760,
                    }
                ),
                encoding="utf-8",
            )

            def fake_screen_runner(*args, **kwargs):
                return subprocess.CompletedProcess(
                    args=args[0],
                    returncode=1,
                    stdout="",
                    stderr="No Sockets found in /tmp/.screen.\n",
                )

            result = adam_voice_bridge_status(
                marker_path=marker_path,
                codex_tty_discoverer=lambda: ["ttys001", "ttys002"],
                screen_runner=fake_screen_runner,
                expected_codex_session_limit=1,
            )

        self.assertEqual(result["status"], "warn")
        self.assertEqual(result["marked_tty"], "ttys002")
        self.assertEqual(result["codex_ttys"], ["ttys001", "ttys002"])
        self.assertEqual(result["codex_tty_count"], 2)
        self.assertEqual(result["screen_status"], "not_running")
        self.assertIn("běží 2 Codex relací, očekáváno nejvýše 1", result["warnings"])
        self.assertIn("screen neběží", result["warnings"])

    def test_adam_voice_bridge_status_uses_single_active_tty_when_marker_is_stale(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            marker_path = Path(temp_dir) / "current_codex_tty.json"
            marker_path.write_text(
                json.dumps(
                    {
                        "tty": "ttys001",
                        "marked_at": "2026-06-07T05:07:45+00:00",
                        "parent_pid": 73760,
                    }
                ),
                encoding="utf-8",
            )

            def fake_screen_runner(*args, **kwargs):
                return subprocess.CompletedProcess(
                    args=args[0],
                    returncode=1,
                    stdout="",
                    stderr="No Sockets found in /tmp/.screen.\n",
                )

            result = adam_voice_bridge_status(
                marker_path=marker_path,
                codex_tty_discoverer=lambda: ["ttys002"],
                screen_runner=fake_screen_runner,
            )

        self.assertEqual(result["status"], "warn")
        self.assertEqual(result["marked_tty"], "ttys001")
        self.assertEqual(result["effective_tty"], "ttys002")
        self.assertEqual(result["codex_ttys"], ["ttys002"])
        self.assertIn("označené TTY ttys001 je staré; použije se jediná aktivní Codex relace ttys002", result["warnings"])

    def test_git_dirty_line_classification_separates_private_family_and_safe_changes(self) -> None:
        app_item = cockpit_module.classify_git_dirty_line(" M Samantha_Agent/app/cockpit.py")
        family_item = cockpit_module.classify_git_dirty_line("?? Samantha_Agent/memory/projects/family_memory_films.md")
        private_item = cockpit_module.classify_git_dirty_line("?? Samantha_Agent/data/private/documents/index.json")
        memory_item = cockpit_module.classify_git_dirty_line(" M Samantha_Agent/memory/MEMORY_INDEX.md")
        speech_item = cockpit_module.classify_git_dirty_line("?? Samantha_Agent/app/speech/__init__.py")

        self.assertEqual(app_item["commit_safety"], "safe")
        self.assertEqual(app_item["category"], "app_code")
        self.assertEqual(family_item["commit_safety"], "exclude")
        self.assertEqual(family_item["category"], "family_memory")
        self.assertEqual(private_item["commit_safety"], "exclude")
        self.assertEqual(memory_item["commit_safety"], "review")
        self.assertEqual(speech_item["category"], "speech_tooling")

    def test_start_cockpit_restart_action_requires_confirmation_and_safe_process(self) -> None:
        self.assertEqual(
            start_cockpit_restart_action(confirmed=False, pid=123)["status"],
            "confirmation_required",
        )
        with patch("app.cockpit.cockpit_process_command", return_value="/bin/zsh"):
            result = start_cockpit_restart_action(confirmed=True, pid=123)

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "unsafe_target")

    def test_start_cockpit_restart_action_launches_worker_for_cockpit_process(self) -> None:
        calls: list[dict[str, object]] = []

        def fake_launcher(args, **kwargs):
            calls.append({"args": args, **kwargs})
            return object()

        command = "/Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent/.venv/bin/python /Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent/scripts/cockpit_server.py --host 127.0.0.1 --port 8770"
        with patch("app.cockpit.cockpit_process_command", return_value=command):
            result = start_cockpit_restart_action(
                confirmed=True,
                pid=456,
                host="127.0.0.1",
                port=8770,
                launcher=fake_launcher,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "restart_started")
        self.assertEqual(calls[0]["args"][1], str(cockpit_module.COCKPIT_RESTART_SCRIPT))
        self.assertIn("--pid", calls[0]["args"])
        self.assertIn("456", calls[0]["args"])
        self.assertTrue(calls[0]["start_new_session"])

    def test_start_adam_voice_mode_action_launches_watcher_with_terminal_bridge_by_default(self) -> None:
        calls: list[dict[str, object]] = []

        def fake_launcher(args, **kwargs):
            calls.append({"args": args, **kwargs})
            return SimpleNamespace(pid=12345)

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            log_file = Path(temp_dir) / "adam_voice_mode.log"
            with (
                patch("app.cockpit.load_voice_mode_status", return_value={"running": False}),
                patch("app.cockpit.write_voice_mode_status") as write_status,
            ):
                result = start_adam_voice_mode_action(launcher=fake_launcher, log_file=log_file)

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "started")
        self.assertEqual(result["pid"], 12345)
        self.assertTrue(result["terminal_bridge"])
        self.assertEqual(calls[0]["args"][1], str(cockpit_module.ADAM_VOICE_MODE_SCRIPT))
        self.assertIn("--poll", calls[0]["args"])
        self.assertIn("--terminal-bridge", calls[0]["args"])
        self.assertTrue(calls[0]["start_new_session"])
        write_status.assert_called()

    def test_start_adam_voice_mode_action_can_disable_terminal_bridge(self) -> None:
        calls: list[dict[str, object]] = []

        def fake_launcher(args, **kwargs):
            calls.append({"args": args, **kwargs})
            return SimpleNamespace(pid=12345)

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            log_file = Path(temp_dir) / "adam_voice_mode.log"
            with (
                patch("app.cockpit.load_voice_mode_status", return_value={"running": False}),
                patch("app.cockpit.write_voice_mode_status"),
            ):
                result = start_adam_voice_mode_action(
                    launcher=fake_launcher,
                    log_file=log_file,
                    terminal_bridge=False,
                )

        self.assertTrue(result["ok"])
        self.assertFalse(result["terminal_bridge"])
        self.assertNotIn("--terminal-bridge", calls[0]["args"])

    def test_start_adam_voice_mode_action_can_enable_terminal_bridge(self) -> None:
        calls: list[dict[str, object]] = []

        def fake_launcher(args, **kwargs):
            calls.append({"args": args, **kwargs})
            return SimpleNamespace(pid=12345)

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            log_file = Path(temp_dir) / "adam_voice_mode.log"
            with (
                patch("app.cockpit.load_voice_mode_status", return_value={"running": False}),
                patch("app.cockpit.write_voice_mode_status"),
            ):
                result = start_adam_voice_mode_action(
                    launcher=fake_launcher,
                    log_file=log_file,
                    terminal_bridge=True,
                )

        self.assertTrue(result["ok"])
        self.assertTrue(result["terminal_bridge"])
        self.assertIn("--terminal-bridge", calls[0]["args"])

    def test_start_adam_voice_mode_action_reuses_running_watcher(self) -> None:
        with patch("app.cockpit.load_voice_mode_status", return_value={"running": True, "pid": 12345}):
            result = start_adam_voice_mode_action(launcher=lambda *args, **kwargs: self.fail("should not launch"))

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "already_running")
        self.assertEqual(result["pid"], 12345)

    def test_stop_adam_voice_mode_action_stops_running_watcher(self) -> None:
        with (
            patch("app.cockpit.load_voice_mode_status", return_value={"running": True, "pid": 12345}),
            patch("app.cockpit.pid_exists", return_value=True),
            patch("app.cockpit.os.kill") as kill,
            patch("app.cockpit.write_voice_mode_status") as write_status,
        ):
            result = stop_adam_voice_mode_action()

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "stopped")
        kill.assert_called_once_with(12345, cockpit_module.signal.SIGTERM)
        write_status.assert_called()

    def test_cockpit_voice_approval_action_updates_pending_state(self) -> None:
        with (
            patch(
                "app.cockpit.update_pending_approval",
                return_value={
                    "ok": True,
                    "status": "approved_in_cockpit",
                    "message": "Žádost byla schválena v Cockpitu.",
                    "pending": True,
                },
            ) as update,
            patch("app.cockpit.load_voice_mode_status", return_value={"ok": True, "running": True}) as load_status,
        ):
            result = cockpit_voice_approval_action({"decision": "approved", "note": "ok"})

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "approved_in_cockpit")
        self.assertEqual(result["pending_for_adam"]["pending"], True)
        self.assertEqual(result["voice_mode"]["running"], True)
        update.assert_called_once_with(decision="approved", note="ok")
        load_status.assert_called_once()

    def test_cockpit_speak_action_returns_speech_result(self) -> None:
        with patch("app.cockpit.speak_text", return_value={"ok": True, "message": "Přečteno."}) as speak:
            result = cockpit_speak_action("Stav Cockpitu je v pořádku.")

        self.assertTrue(result["ok"])
        self.assertEqual(result["message"], "Přečteno.")
        speak.assert_called_once_with("Stav Cockpitu je v pořádku.", voice="Zuzana")

    def test_cockpit_speak_action_reports_speech_error(self) -> None:
        with patch("app.cockpit.speak_text", side_effect=cockpit_module.SpeechError("AudioQueueStart failed")):
            result = cockpit_speak_action("Test")

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "speech_failed")
        self.assertIn("AudioQueueStart failed", result["message"])

    def test_cockpit_edge_tts_action_returns_audio_base64(self) -> None:
        result = cockpit_edge_tts_action("Test", synthesizer=lambda *args, **kwargs: b"MP3")

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "edge_tts_ready")
        self.assertEqual(result["voice"], "cs-CZ-AntoninNeural")
        self.assertEqual(result["mime_type"], "audio/mpeg")
        self.assertEqual(result["audio_base64"], "TVAz")

    def test_cockpit_edge_tts_action_reports_error(self) -> None:
        def fail(*args, **kwargs):
            raise cockpit_module.EdgeTtsError("síť není dostupná")

        result = cockpit_edge_tts_action("Test", synthesizer=fail)

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "edge_tts_failed")
        self.assertIn("síť není dostupná", result["message"])

    def test_cockpit_transcribe_voice_action_returns_transcript(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            with patch(
                "app.cockpit.transcribe_audio_base64",
                return_value={"ok": True, "text": "Najdi dnešní dokumenty."},
            ) as transcribe:
                result = cockpit_transcribe_voice_action(
                    {"audio_base64": "abc", "mime_type": "audio/webm", "language": "cs"},
                    inbox_dir=Path(temp_dir),
                )

        self.assertTrue(result["ok"])
        self.assertEqual(result["text"], "Najdi dnešní dokumenty.")
        self.assertTrue(result["saved"])
        self.assertIn("latest_voice_command.md", result["latest_voice_command_path"])
        self.assertIn("přepsán a uložen", result["message"])
        transcribe.assert_called_once_with("abc", mime_type="audio/webm", language="cs")

    def test_cockpit_save_voice_text_action_writes_inbox(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            result = cockpit_save_voice_text_action(
                {"text": "Adame, spočítej dnešní handoffy."},
                inbox_dir=Path(temp_dir),
            )
            latest_path = Path(temp_dir) / "latest_voice_command.md"

            self.assertTrue(result["ok"])
            self.assertEqual(result["status"], "voice_text_saved")
            self.assertTrue(result["saved"])
            self.assertIn("latest_voice_command.md", result["latest_voice_command_path"])
            self.assertIn("Adame, spočítej dnešní handoffy.", latest_path.read_text(encoding="utf-8"))

    def test_cockpit_save_voice_text_action_rejects_empty_text(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            result = cockpit_save_voice_text_action({"text": "   "}, inbox_dir=Path(temp_dir))

            self.assertFalse(result["ok"])
            self.assertEqual(result["status"], "empty_voice_text")
            self.assertFalse((Path(temp_dir) / "latest_voice_command.md").exists())

    def test_save_voice_command_to_inbox_writes_latest_and_index(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            result = save_voice_command_to_inbox(
                {"text": "Najdi poslední PDF."},
                inbox_dir=Path(temp_dir),
            )
            latest_path = Path(temp_dir) / "latest_voice_command.md"
            index_path = Path(temp_dir) / "index.jsonl"

            self.assertTrue(result["saved"])
            self.assertTrue(latest_path.exists())
            self.assertTrue(index_path.exists())
            self.assertIn("Najdi poslední PDF.", latest_path.read_text(encoding="utf-8"))
            self.assertIn("transcribed_only_not_executed", latest_path.read_text(encoding="utf-8"))
            self.assertIn("voice_command_", result["voice_command_path"])
            self.assertIn("latest_voice_command.md", result["latest_voice_command_path"])

    def test_cockpit_transcribe_voice_action_reports_error(self) -> None:
        with patch(
            "app.cockpit.transcribe_audio_base64",
            side_effect=cockpit_module.TranscriptionError("Chybí OPENAI_API_KEY"),
        ):
            result = cockpit_transcribe_voice_action({"audio_base64": "", "mime_type": "audio/webm"})

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "transcription_failed")
        self.assertIn("Chybí OPENAI_API_KEY", result["message"])

    def test_parse_active_projects_table_and_summary(self) -> None:
        text = """# Active Projects

| Oblast | Priorita | Stav | Memory soubor | Handoff | Dalsi krok |
| --- | --- | --- | --- | --- | --- |
| Dokumenty | 1 | [PRIPOMENOUT] Rozpracovane | `projects/docs.md` | `handoffs/docs.md` | Rucne otestovat cockpit. |
| Lekarna | 2 | Hotovo / udrzba | `projects/lekarna.md` | zatim neni | Zadny aktivni vyvoj. |
"""
        projects = parse_active_projects_table(text)

        self.assertEqual(len(projects), 2)
        self.assertEqual(projects[0]["name"], "Dokumenty")
        self.assertEqual(projects[0]["priority"], "1")
        self.assertIn("připomenout", projects[0]["flags"])
        self.assertIn("čeká na retest", projects[0]["flags"])
        self.assertIn("hotovo/údržba", projects[1]["flags"])

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "ACTIVE_PROJECTS.md"
            path.write_text(text, encoding="utf-8")
            status = projects_status(path=path)

        self.assertTrue(status["ok"])
        self.assertEqual(status["summary"]["total"], 2)
        self.assertEqual(status["summary"]["active_total"], 2)
        self.assertEqual(status["summary"]["archived_total"], 0)
        self.assertEqual(status["summary"]["lifecycle_counts"]["active"], 2)
        self.assertEqual(status["summary"]["priority_counts"]["1"], 1)
        self.assertEqual(status["summary"]["flag_counts"]["připomenout"], 1)

    def test_archived_projects_are_hidden_from_active_project_summary(self) -> None:
        text = """# Project Registry

| Oblast | Priorita | Rezim | Stav | Memory soubor | Handoff | Dalsi krok |
| --- | --- | --- | --- | --- | --- | --- |
| Dokumenty | 1 | active | Rozpracovane 2026-06-04 | `projects/docs.md` | `handoffs/docs.md` | Rucne otestovat cockpit. |
| VocabularyFR | 2 | archived | Archiv hotovo | `projects/vocabularyfr.md` | `handoffs/vocabularyfr.md` | Archiv: neukazovat mezi aktivnimi projekty. |
"""
        projects = parse_active_projects_table(text)

        self.assertEqual(len(projects), 2)
        self.assertEqual(projects[0]["lifecycle"], "active")
        self.assertEqual(projects[1]["lifecycle"], "archived")
        self.assertIn("archiv", projects[1]["flags"])

        summary = cockpit_module.summarize_projects(projects)
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["active_total"], 1)
        self.assertEqual(summary["archived_total"], 1)
        self.assertNotIn("2", summary["priority_counts"])

        catalog_summary = cockpit_module.summarize_project_catalog(projects, [], [])
        self.assertEqual(catalog_summary["projects"], 1)
        self.assertEqual(catalog_summary["projects_all"], 2)
        self.assertEqual(catalog_summary["archived_projects"], 1)
        self.assertEqual(catalog_summary["project_management"]["archived"], 1)

        items = cockpit_module.build_project_catalog_items(projects, [], [])
        self.assertFalse(items[1]["needs_attention"])
        self.assertEqual(items[1]["management_status"], "archived")
        self.assertIn('data-project-filter="archived"', COCKPIT_HTML)
        self.assertIn("/api/projects/lifecycle", COCKPIT_HTML)
        self.assertIn("Archivovat", COCKPIT_HTML)
        self.assertIn("Obnovit", COCKPIT_HTML)

    def test_project_lifecycle_action_archives_registry_row_with_backup(self) -> None:
        text = """# Project Registry

| Oblast | Priorita | Rezim | Stav | Memory soubor | Handoff | Dalsi krok |
| --- | --- | --- | --- | --- | --- | --- |
| Dokumenty | 1 | active | Rozpracovane | `projects/docs.md` | `handoffs/docs.md` | Test. |
| VocabularyFR | 2 | archived | Archiv hotovo | `projects/vocabularyfr.md` | `handoffs/vocabularyfr.md` | Archiv. |
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            path = root / "ACTIVE_PROJECTS.md"
            backup_dir = root / "backups"
            path.write_text(text, encoding="utf-8")

            result = cockpit_module.project_lifecycle_action(
                project_name="Dokumenty",
                lifecycle="archived",
                confirmed=True,
                path=path,
                backup_dir=backup_dir,
                now=datetime(2026, 6, 7, 12, 0, tzinfo=timezone.utc),
            )

            updated = path.read_text(encoding="utf-8")
            backup_exists = (backup_dir / "ACTIVE_PROJECTS_20260607_120000.md").exists()

        self.assertTrue(result["ok"])
        self.assertEqual(result["project"]["previous_lifecycle"], "active")
        self.assertEqual(result["project"]["lifecycle"], "archived")
        self.assertEqual(result["projects_status"]["summary"]["active_total"], 0)
        self.assertEqual(result["projects_status"]["summary"]["archived_total"], 2)
        self.assertIn("| Dokumenty | 1 | archived |", updated)
        self.assertTrue(backup_exists)

    def test_project_capability_map_tables_are_exposed_in_projects_status(self) -> None:
        active_projects_text = """# Active Projects

| Oblast | Priorita | Stav | Memory soubor | Handoff | Dalsi krok |
| --- | --- | --- | --- | --- | --- |
| Dokumenty | 1 | Rozpracovane 2026-06-04 | `projects/docs.md` | `handoffs/docs_2026_06_04.md` | Rucne otestovat cockpit. |
"""
        capability_map_text = """# Project capability map

## Globalni schopnosti Samanthy

| Oblast | Uroven | Aktualni schopnost | Bezpecnostni brana |
| --- | --- | --- | --- |
| Lokalni pamet | L3 | `search_memory`, `memory_status` | Necte e-maily ani tajemstvi. |

## Infrastructure capabilities

| Capability | Stav | Obsahuje | Krmi / pomaha |
| --- | --- | --- | --- |
| Mobile Input Layer / iPhone Shortcuts | aktivni priorita 2 | quick notes intake | dokumenty, reminders |
"""
        tools = parse_global_tools_table(capability_map_text)
        capabilities = parse_infrastructure_capabilities_table(capability_map_text)

        self.assertEqual(tools[0]["name"], "Lokalni pamet")
        self.assertEqual(tools[0]["level"], "L3")
        self.assertEqual(capabilities[0]["name"], "Mobile Input Layer / iPhone Shortcuts")
        self.assertEqual(capabilities[0]["contains"], "quick notes intake")

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            active_projects = root / "ACTIVE_PROJECTS.md"
            active_projects.write_text(active_projects_text, encoding="utf-8")
            capability_map = root / "project_capability_map.md"
            capability_map.write_text(capability_map_text, encoding="utf-8")
            status = projects_status(path=active_projects, capability_map_path=capability_map)

        self.assertTrue(status["ok"])
        self.assertEqual(status["catalog_summary"]["projects"], 1)
        self.assertEqual(status["catalog_summary"]["tools"], 1)
        self.assertEqual(status["catalog_summary"]["infrastructure_capabilities"], 1)
        self.assertEqual(status["catalog_summary"]["total"], 3)
        self.assertEqual(status["catalog_summary"]["project_management"]["needs_attention"], 1)
        self.assertEqual([item["category"] for item in status["items"]], ["project", "tool", "infrastructure"])
        self.assertEqual(status["items"][0]["last_worked"], "2026-06-04")
        self.assertTrue(status["items"][0]["needs_attention"])
        self.assertIn("čeká na Mílu", status["items"][0]["management_flags"])

    def test_project_management_signals_find_missing_project_handoff_and_next_step(self) -> None:
        item = cockpit_module.project_management_signals(
            {
                "status": "Rozpracovane",
                "next_step": "",
                "memory_file": "`projects/docs.md`",
                "handoff": "zatim neni",
            }
        )

        self.assertEqual(item["status"], "needs_attention")
        self.assertTrue(item["needs_attention"])
        self.assertIn("chybí handoff", item["flags"])
        self.assertIn("chybí další krok", item["flags"])
        self.assertIn("Doplnit nebo rozhodnout", item["reason"])

    def test_recovery_center_status_reports_metadata_without_autosave_content(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            autosave_dir = root / "session_autosave"
            autosave_dir.mkdir()
            autosave_file = autosave_dir / "session_20260603_203000.txt"
            autosave_file.write_text("citlivy obsah autosave se nesmi vracet\n", encoding="utf-8")
            (autosave_dir / "latest_info.txt").write_text("pomocna metadata nejsou session snapshot\n", encoding="utf-8")
            active_projects = root / "ACTIVE_PROJECTS.md"
            active_projects.write_text(
                """# Active Projects

| Oblast | Priorita | Stav | Memory soubor | Handoff | Dalsi krok |
| --- | --- | --- | --- | --- | --- |
| Cockpit Recovery centrum | 1 | [PRIPOMENOUT] Rozpracovane | `infrastructure/codex_reconnect_recovery.md` | `handoffs/recovery.md` | Implementovat recovery kartu. |
""",
                encoding="utf-8",
            )
            handoff = root / "recovery.md"
            handoff.write_text(
                """Nazev: Recovery test
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-03

Dalsi krok:
- Otevrit Recovery centrum.
""",
                encoding="utf-8",
            )
            memory_index = root / "MEMORY_INDEX.md"
            memory_index.write_text("# Memory Index\n", encoding="utf-8")

            result = recovery_center_status(
                autosave_dir=autosave_dir,
                active_projects_path=active_projects,
                memory_index_path=memory_index,
                handoff_paths=(handoff,),
                git_status=lambda: {
                    "ok": True,
                    "message": "1 změna v pracovním stromu",
                    "branch": "main",
                    "dirty_count": 1,
                    "dirty_files": ["M app/cockpit.py"],
                },
            )

        self.assertTrue(result["ok"])
        self.assertTrue(result["autosave"]["ok"])
        self.assertEqual(result["autosave"]["latest_file"], autosave_file.name)
        self.assertNotIn("citlivy obsah", json.dumps(result, ensure_ascii=False))
        self.assertEqual(result["active_project"]["name"], "Cockpit Recovery centrum")
        self.assertEqual(result["handoffs"][0]["title"], "Recovery test")
        self.assertIn("codex resume --last", [item["command"] for item in result["commands"]])

    def test_quantitative_status_overview_reports_diff_against_previous_snapshot(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            repo_root = root
            project_root = root / "Samantha_Agent"
            (project_root / "app").mkdir(parents=True)
            (project_root / "data" / "private").mkdir(parents=True)
            (project_root / "app" / "main.py").write_text("print('hello')\n", encoding="utf-8")
            (project_root / "README.md").write_text("one\n", encoding="utf-8")
            (project_root / "notes.txt").write_text("alpha\n", encoding="utf-8")
            metrics_path = project_root / "data" / "metrics" / "samantha_quantitative_status.jsonl"
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            metrics_path.write_text(
                json.dumps(
                    {
                        "created_at": "2026-06-02T10:00:00+00:00",
                        "scope": "Samantha_Agent",
                        "git_summary": "clean, on branch main",
                        "local": {
                            ".md": {"files": 1, "lines": 1},
                            ".py": {"files": 1, "lines": 1},
                        },
                        "git_tracked": {
                            ".md": {"files": 1, "lines": 1},
                            ".py": {"files": 1, "lines": 1},
                        },
                        "totals": {
                            "local": {"files": 2, "lines": 2},
                            "git_tracked": {"files": 2, "lines": 2},
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = quantitative_status_overview(
                metrics_path=metrics_path,
                project_root=project_root,
                repo_root=repo_root,
                runner=self.quantitative_runner(
                    ls_files="Samantha_Agent/app/main.py\nSamantha_Agent/README.md\n",
                    status="## main...origin/main\n",
                ),
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["current"]["totals"]["local"]["files"], 3)
        self.assertEqual(result["current"]["totals"]["local"]["lines"], 3)
        self.assertEqual(result["previous"]["totals"]["local"]["files"], 2)
        self.assertEqual(result["diff"]["totals"]["local"]["files"], 1)
        self.assertEqual(result["diff"]["totals"]["local"]["lines"], 1)
        self.assertEqual(result["diff"]["local"][0]["extension"], ".txt")
        self.assertEqual(result["diff"]["local"][0]["delta_lines"], 1)
        self.assertEqual(result["diff"]["git_tracked"], [])

    def test_quick_notes_status_returns_numbered_overview(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "Shortcuts"
            inbox.mkdir()
            index_path = root / "private" / "quick_notes" / "index.json"
            (inbox / "01_old.md").write_text(
                "# Samantha inbox\n\nDatum: 2026-06-03 20:30:00\n\nPoznámka:\nZkontrolovat Cockpit.\n",
                encoding="utf-8",
            )
            (inbox / "02_new.md").write_text(
                "# Samantha inbox\n\nDatum: 2026-06-03 20:45:00\n\nPoznámka:\nNovější QN.\n",
                encoding="utf-8",
            )

            result = quick_notes_status(inbox_dir=inbox, index_path=index_path)

        self.assertTrue(result["ok"])
        self.assertEqual(result["counts"]["active"], 2)
        self.assertEqual(result["notes"][0]["note_number"], 2)
        self.assertEqual(result["notes"][0]["snippet"], "Novější QN.")
        self.assertEqual(result["notes"][0]["triage"]["classification"], "Nezařazeno")
        self.assertNotIn("source_path", result["notes"][0])

    def test_urgent_reminders_status_is_separate_from_quick_notes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "Shortcuts"
            inbox.mkdir()
            quick_index = root / "private" / "quick_notes" / "index.json"
            urgent_index = root / "private" / "urgent_reminders" / "index.json"
            (inbox / "samantha_note_2026-06-04_08-00-00.md").write_text(
                "# Samantha inbox\n\nDatum: 2026-06-04 08:00:00\n\nPoznámka:\nNápad do QN.\n",
                encoding="utf-8",
            )
            (inbox / "samantha_reminder_2026-06-04_08-05-00.md").write_text(
                "# Samantha důležité připomenutí\n\nDatum: 2026-06-04 08:05:00\nPriorita: urgent\n\nPřipomenutí:\nZavolat do servisu.\n",
                encoding="utf-8",
            )

            quick = quick_notes_status(inbox_dir=inbox, index_path=quick_index)
            urgent = urgent_reminders_status(inbox_dir=inbox, index_path=urgent_index)

        self.assertEqual(quick["counts"]["active"], 1)
        self.assertEqual(quick["notes"][0]["snippet"], "Nápad do QN.")
        self.assertEqual(urgent["counts"]["open"], 1)
        self.assertEqual(urgent["items"][0]["summary"], "Zavolat do servisu.")
        self.assertNotIn("source_path", urgent["items"][0])

    def test_urgent_reminders_status_returns_full_body_text_for_long_reminder(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "Shortcuts"
            inbox.mkdir()
            urgent_index = root / "private" / "urgent_reminders" / "index.json"
            long_body = (
                "První řádek delší připomínky.\n"
                "Druhý řádek s vysvětlením, které se nevejde do krátkého červeného řádku.\n"
                "Třetí řádek s konkrétním dalším krokem."
            )
            (inbox / "samantha_reminder_2026-06-05_11-30-00.md").write_text(
                f"# Samantha důležité připomenutí\n\nDatum: 2026-06-05 11:30:00\nPriorita: urgent\n\nPřipomenutí:\n{long_body}\n",
                encoding="utf-8",
            )

            urgent = urgent_reminders_status(inbox_dir=inbox, index_path=urgent_index)

        self.assertEqual(urgent["counts"]["open"], 1)
        self.assertIn("První řádek", urgent["items"][0]["summary"])
        self.assertEqual(urgent["items"][0]["body_text"], long_body)
        self.assertNotIn("source_path", urgent["items"][0])

    def test_action_queue_prioritizes_urgent_mobile_reminders(self) -> None:
        queue = action_queue_status(
            document_work={"new_pdfs": [], "problems": [], "review": {"next_items": []}},
            reminders={"groups": {}, "conflicts": []},
            urgent_reminders={
                "items": [
                    {
                        "summary": "Zavolat do servisu.",
                        "created_at": "2026-06-04 08:05:00",
                    }
                ],
            },
        )

        self.assertEqual(queue["items"][0]["kind"], "urgent_reminder")
        self.assertEqual(queue["items"][0]["priority"], 1)
        self.assertEqual(queue["items"][0]["action"], "open_urgent_reminders")

    def test_urgent_reminders_status_falls_back_to_private_index_when_sync_fails(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "Shortcuts"
            inbox.mkdir()
            index_path = root / "private" / "urgent_reminders" / "index.json"
            index_path.parent.mkdir(parents=True)
            index_path.write_text(
                json.dumps(
                    {
                        "reminders": [
                            {
                                "reminder_number": 1,
                                "priority": "urgent",
                                "status": "open",
                                "created_at": "2026-06-04 10:52:00",
                                "modified_at": "2026-06-04 10:52:00",
                                "title": "Samantha důležité připomenutí",
                                "summary": "Starší připomenutí.",
                                "size_bytes": 120,
                                "source_path": "/private/not-returned-old.md",
                            },
                            {
                                "reminder_number": 2,
                                "priority": "urgent",
                                "status": "open",
                                "created_at": "2026-06-04 11:31:00",
                                "modified_at": "2026-06-04 11:31:00",
                                "title": "Samantha důležité připomenutí",
                                "summary": "Fallback připomenutí.",
                                "size_bytes": 91,
                                "source_path": "/private/not-returned.md",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with patch("app.cockpit.sync_urgent_reminders_index", side_effect=OSError("iCloud busy")):
                result = urgent_reminders_status(inbox_dir=inbox, index_path=index_path)

        self.assertTrue(result["ok"])
        self.assertIn("lokálního indexu", result["message"])
        self.assertEqual(result["counts"]["open"], 2)
        self.assertEqual(result["items"][0]["reminder_number"], 2)
        self.assertEqual(result["items"][0]["summary"], "Fallback připomenutí.")
        self.assertNotIn("source_path", result["items"][0])

    def test_urgent_reminders_status_retries_transient_icloud_deadlock(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "Shortcuts"
            inbox.mkdir()
            index_path = root / "private" / "urgent_reminders" / "index.json"
            reminder = SimpleNamespace(
                reminder_number=3,
                priority="urgent",
                status="open",
                created_at="2026-06-05 09:19:42",
                modified_at="2026-06-05 09:19:42",
                title="Samantha důležité připomenutí",
                summary="Nová iPhone připomínka.",
                size_bytes=278,
            )

            with (
                patch(
                    "app.cockpit.sync_urgent_reminders_index",
                    side_effect=[OSError(11, "Resource deadlock avoided"), [reminder]],
                ),
                patch("app.cockpit.time.sleep", return_value=None),
            ):
                result = urgent_reminders_status(inbox_dir=inbox, index_path=index_path)

        self.assertTrue(result["ok"])
        self.assertEqual(result["counts"]["open"], 1)
        self.assertEqual(result["items"][0]["reminder_number"], 3)
        self.assertEqual(result["items"][0]["summary"], "Nová iPhone připomínka.")

    def test_urgent_reminders_status_retries_multiple_icloud_deadlocks(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "Shortcuts"
            inbox.mkdir()
            index_path = root / "private" / "urgent_reminders" / "index.json"
            reminder = SimpleNamespace(
                reminder_number=4,
                priority="urgent",
                status="open",
                created_at="2026-06-05 11:45:00",
                modified_at="2026-06-05 11:45:00",
                title="Samantha důležité připomenutí",
                summary="Po několika deadlocích načteno.",
                body_text="Po několika deadlocích načteno celé.",
                size_bytes=312,
            )

            with (
                patch(
                    "app.cockpit.sync_urgent_reminders_index",
                    side_effect=[
                        OSError(11, "Resource deadlock avoided"),
                        OSError(11, "Resource deadlock avoided"),
                        OSError(11, "Resource deadlock avoided"),
                        [reminder],
                    ],
                ),
                patch("app.cockpit.time.sleep", return_value=None) as sleep_mock,
            ):
                result = urgent_reminders_status(inbox_dir=inbox, index_path=index_path)

        self.assertTrue(result["ok"])
        self.assertEqual(sleep_mock.call_count, 3)
        self.assertEqual(result["counts"]["open"], 1)
        self.assertEqual(result["items"][0]["body_text"], "Po několika deadlocích načteno celé.")

    def test_urgent_reminder_done_action_hides_open_item_without_deleting_record(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            index_path = root / "private" / "urgent_reminders" / "index.json"
            index_path.parent.mkdir(parents=True)
            index_path.write_text(
                json.dumps(
                    {
                        "reminders": [
                            {
                                "reminder_number": 1,
                                "priority": "urgent",
                                "status": "open",
                                "created_at": "2026-06-04 10:52:00",
                                "modified_at": "2026-06-04 10:52:00",
                                "title": "Samantha důležité připomenutí",
                                "summary": "Splnit a skrýt.",
                                "size_bytes": 120,
                                "source_path": "/private/not-returned.md",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = urgent_reminder_done_action(reminder_number=1, index_path=index_path)
            stored = json.loads(index_path.read_text(encoding="utf-8"))

        self.assertTrue(result["ok"])
        self.assertEqual(result["urgent_reminders"]["counts"]["open"], 0)
        self.assertEqual(result["urgent_reminders"]["counts"]["total"], 1)
        self.assertEqual(result["urgent_reminders"]["items"], [])
        self.assertEqual(stored["reminders"][0]["status"], "done")
        self.assertIn("completed_at", stored["reminders"][0])

    def test_quick_notes_status_falls_back_to_private_index_when_sync_fails(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "Shortcuts"
            inbox.mkdir()
            index_path = root / "private" / "quick_notes" / "index.json"
            index_path.parent.mkdir(parents=True)
            index_path.write_text(
                json.dumps(
                    {
                        "notes": [
                            {
                                "note_number": 6,
                                "category": "inbox",
                                "status": "inbox",
                                "created_at": "2026-06-03 20:20:00",
                                "modified_at": "2026-06-03 20:21:00",
                                "title": "Samantha inbox",
                                "snippet": "Starší fallback poznámka.",
                                "size_bytes": 120,
                                "source_path": "/private/not-returned-old.md",
                            },
                            {
                                "note_number": 7,
                                "category": "inbox",
                                "status": "inbox",
                                "created_at": "2026-06-03 20:30:00",
                                "modified_at": "2026-06-03 20:31:00",
                                "title": "Samantha inbox",
                                "snippet": "Fallback poznámka.",
                                "size_bytes": 123,
                                "source_path": "/private/not-returned.md",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with patch("app.cockpit.sync_quick_notes_index", side_effect=OSError("iCloud busy")):
                result = quick_notes_status(inbox_dir=inbox, index_path=index_path)

        self.assertTrue(result["ok"])
        self.assertIn("lokálního indexu", result["message"])
        self.assertEqual(result["counts"]["active"], 2)
        self.assertEqual(result["notes"][0]["note_number"], 7)
        self.assertEqual(result["notes"][0]["snippet"], "Fallback poznámka.")
        self.assertNotIn("source_path", result["notes"][0])

    def test_quick_notes_status_adds_triage_hint_for_cockpit_project_note(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "Shortcuts"
            inbox.mkdir()
            index_path = root / "private" / "quick_notes" / "index.json"
            (inbox / "project_note.md").write_text(
                "# Samantha inbox\n\nDatum: 2026-06-05 05:14:45\n\nPoznámka:\nChybí tlačítko projekty v Cockpitu a seznam toolů.\n",
                encoding="utf-8",
            )

            result = quick_notes_status(inbox_dir=inbox, index_path=index_path)
            detail = quick_note_detail_status(note_number=1, inbox_dir=inbox, index_path=index_path)

        self.assertEqual(result["notes"][0]["triage"]["classification"], "Cockpit / správa projektů")
        self.assertIn("Cockpit", result["notes"][0]["triage"]["suggested_next_step"])
        self.assertFalse(result["notes"][0]["triage"]["sensitive"])
        self.assertEqual(detail["triage"]["classification"], "Cockpit / správa projektů")

    def test_quick_note_detail_status_reads_full_body_without_source_path(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "Shortcuts"
            inbox.mkdir()
            index_path = root / "private" / "quick_notes" / "index.json"
            (inbox / "note.md").write_text(
                "# Samantha inbox\n\nDatum: 2026-06-03 20:30:00\n\nPoznámka:\nCelý obsah QN.\nDruhý řádek.\n",
                encoding="utf-8",
            )

            result = quick_note_detail_status(note_number=1, inbox_dir=inbox, index_path=index_path)

        self.assertTrue(result["ok"])
        self.assertEqual(result["note_number"], 1)
        self.assertIn("Celý obsah QN.", result["body_text"])
        self.assertIn("Druhý řádek.", result["body_text"])
        self.assertFalse(result["truncated"])
        self.assertNotIn("source_path", result)

    def test_quick_note_detail_status_falls_back_to_private_index_when_sync_fails(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "Shortcuts"
            inbox.mkdir()
            source = root / "fallback_note.md"
            source.write_text(
                "# Samantha inbox\n\nDatum: 2026-06-03 20:30:00\n\nPoznámka:\nFallback detail.\n",
                encoding="utf-8",
            )
            index_path = root / "private" / "quick_notes" / "index.json"
            index_path.parent.mkdir(parents=True)
            index_path.write_text(
                json.dumps(
                    {
                        "notes": [
                            {
                                "note_number": 7,
                                "category": "inbox",
                                "status": "inbox",
                                "created_at": "2026-06-03 20:30:00",
                                "modified_at": "2026-06-03 20:31:00",
                                "title": "Samantha inbox",
                                "snippet": "Fallback poznámka.",
                                "size_bytes": source.stat().st_size,
                                "source_path": str(source),
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with patch("app.cockpit.sync_quick_notes_index", side_effect=OSError("iCloud busy")):
                result = quick_note_detail_status(note_number=7, inbox_dir=inbox, index_path=index_path)

        self.assertTrue(result["ok"])
        self.assertIn("Fallback detail.", result["body_text"])
        self.assertIn("lokálního indexu", result["message"])
        self.assertIn("sync_error", result)
        self.assertNotIn("source_path", result)

    def test_reminders_status_groups_startup_window_and_future(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "reminders.json"
            path.write_text(
                json.dumps(
                    {
                        "reminders": [
                            self.reminder("overdue", "Prošlé", "2026-05-31"),
                            self.reminder("soon", "Brzy", "2026-06-10"),
                            self.reminder("later", "Později", "2026-08-01"),
                            self.reminder("done", "Hotovo", "2026-06-03", status="done"),
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = reminders_status(path=path, today=date(2026, 6, 3))

            self.assertTrue(result["ok"])
            self.assertEqual(result["counts"]["open"], 3)
            self.assertEqual(result["counts"]["active"], 2)
            self.assertEqual(result["groups"]["overdue"][0]["id"], "overdue")
            self.assertEqual(result["groups"]["soon"][0]["id"], "soon")
            self.assertEqual(result["groups"]["later"][0]["id"], "later")
            self.assertEqual(result["groups"]["later"][0]["reminder_ref"], reminder_reference("later"))

    def test_mark_reminder_done_action_changes_selected_reminder_only(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "reminders.json"
            path.write_text(
                json.dumps(
                    {
                        "reminders": [
                            self.reminder("mark-id", "Označit", "2026-06-10"),
                            self.reminder("other-id", "Nechat", "2026-06-11"),
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = mark_reminder_done_action("mark-id", path=path)
            stored = json.loads(path.read_text(encoding="utf-8"))["reminders"]

            self.assertTrue(result["ok"])
            self.assertEqual(stored[0]["status"], "done")
            self.assertEqual(stored[1]["status"], "open")
            self.assertEqual(result["reminders"]["counts"]["open"], 1)
            self.assertEqual(result["reminders"]["groups"]["soon"][0]["id"], "other-id")

    def test_mark_reminder_done_action_accepts_reminder_reference(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "reminders.json"
            sensitive_id = "sms-rixo-zaplatit-pojistku-3275111280-2026-05-21"
            path.write_text(
                json.dumps({"reminders": [self.reminder(sensitive_id, "Označit", "2026-06-10")]}),
                encoding="utf-8",
            )

            result = mark_reminder_done_action(reminder_reference(sensitive_id), path=path)
            stored = json.loads(path.read_text(encoding="utf-8"))["reminders"]

            self.assertTrue(result["ok"])
            self.assertEqual(stored[0]["status"], "done")
            self.assertEqual(result["reminder_ref"], reminder_reference(sensitive_id))
            self.assertNotIn("3275111280", result["message"])

    def test_reminders_status_reports_payment_conflict_for_same_asset_and_coverage(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "reminders.json"
            rixo = self.reminder("rixo-id", "Zaplatit RIXO", "2026-07-31")
            cpp = self.reminder("cpp-id", "Zaplatit ČPP", "2026-08-01")
            for item in (rixo, cpp):
                item["related_asset"] = "auto VOLVO V40 CROSS COUNTRY SPZ 4SN8981"
                item["coverage_start"] = "2026-08-01"
                item["conflict_note"] = "Nekonat platbu bez porovnani."
            path.write_text(json.dumps({"reminders": [rixo, cpp]}), encoding="utf-8")

            result = reminders_status(path=path, today=date(2026, 6, 3))

            self.assertEqual(result["counts"]["conflicts"], 1)
            self.assertEqual(len(result["conflicts"]), 1)
            self.assertEqual(result["conflicts"][0]["asset"], "AUTO VOLVO V40 CROSS COUNTRY SPZ 4SN8981")
            self.assertEqual(result["conflicts"][0]["coverage_start"], "2026-08-01")
            self.assertEqual(len(result["conflicts"][0]["items"]), 2)
            self.assertEqual(result["conflicts"][0]["items"][0]["reminder_ref"], reminder_reference("rixo-id"))

    def test_cancel_payment_reminder_action_attaches_email_evidence_and_clears_conflict(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            temp = Path(temp_dir)
            path = temp / "reminders.json"
            archive_dir = temp / "email" / "archive"
            archive_id = "email-test-pojistna-smlouva-c-3275111280"
            metadata_dir = archive_dir / archive_id
            metadata_dir.mkdir(parents=True)
            (metadata_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "archive_id": archive_id,
                        "subject": "Akceptace odstoupení od smlouvy č. 3275111280",
                        "from": "service@example.test",
                        "date": "Thu, 4 Jun 2026 09:34:29 +0000",
                        "archived_at": "2026-06-04T10:14:45+00:00",
                    }
                ),
                encoding="utf-8",
            )
            rixo = self.reminder("rixo-id", "Zaplatit RIXO", "2026-07-31")
            cpp = self.reminder("cpp-id", "Zaplatit ČPP", "2026-08-01")
            for item in (rixo, cpp):
                item["related_asset"] = "auto VOLVO V40 CROSS COUNTRY SPZ 4SN8981"
                item["coverage_start"] = "2026-08-01"
                item["notes"] = "Pojistná platba."
            path.write_text(json.dumps({"reminders": [rixo, cpp]}), encoding="utf-8")

            result = cancel_payment_reminder_action(
                reminder_id=reminder_reference("rixo-id"),
                evidence_archive_id=archive_id,
                reminders_path=path,
                archive_directory=archive_dir,
            )
            stored = json.loads(path.read_text(encoding="utf-8"))["reminders"]

            self.assertTrue(result["ok"])
            self.assertEqual(result["reminders"]["counts"]["conflicts"], 0)
            self.assertEqual(stored[0]["status"], "cancelled")
            self.assertEqual(stored[0]["resolution"]["status"], "cancelled")
            self.assertEqual(stored[0]["evidence"]["archive_id"], archive_id)
            self.assertEqual(stored[1]["status"], "open")

    def test_reminder_source_detail_loads_email_readonly(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "reminders.json"
            path.write_text(
                json.dumps(
                    {
                        "reminders": [
                            {
                                **self.reminder("email-reminder", "Email", "2026-06-10"),
                                "source": {
                                    "type": "email",
                                    "uid": "14157",
                                    "date": "Mon, 1 Jun 2026 10:00:00 +0200",
                                    "sender": "Sender <[e-mail redigovan]>",
                                    "provider": "icloud",
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            provider = _FakeMessageProvider(
                EmailMessage(
                    header=EmailHeader(
                        internal_id="14157",
                        date="Mon, 1 Jun 2026 10:00:00 +0200",
                        sender="Sender <sender@example.com>",
                        subject="Pojistka vozidla",
                        source="iCloud",
                        folder="INBOX",
                    ),
                    body_text="Platba se týká vozidla Volvo.",
                    truncated=False,
                    attachments=(),
                )
            )

            result = reminder_source_detail_action(
                "email-reminder",
                reminders_path=path,
                icloud_provider_factory=lambda: provider,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["kind"], "email")
            self.assertEqual(result["email"]["subject"], "Pojistka vozidla")
            self.assertEqual(provider.calls[0]["uid"], "14157")

    def test_reminder_source_detail_finds_private_document_context(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            reminders_path = root / "reminders.json"
            reminders_path.write_text(
                json.dumps(
                    {
                        "reminders": [
                            {
                                **self.reminder(
                                    "document-reminder",
                                    "Zaplatit ČPP autopojištění",
                                    "2026-08-01",
                                ),
                                "source": {
                                    "type": "private_document",
                                    "uid": "cpp-predpis-pojistne-smlouvy-3270612451-2026",
                                    "date": "",
                                    "sender": "Private document vault",
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            vault = root / "documents"
            index = vault / "index"
            stored_dir = vault / "vault" / "insurance" / "cpp-predpis-pojistne-smlouvy-3270612451-2026"
            stored_dir.mkdir(parents=True)
            pdf = stored_dir / "predpis.pdf"
            pdf.write_bytes(b"%PDF-1.4\n")
            index.mkdir(parents=True)
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "cpp-predpis-pojistne-smlouvy-3270612451-2026",
                        "title": "ČPP předpis pojistné smlouvy",
                        "original_filename": "predpis.pdf",
                        "domain": "insurance",
                        "document_type": "payment_notice",
                        "related_asset": "VOLVO 4SN 8981",
                        "stored_path": str(pdf),
                    }
                ],
            )
            self.write_jsonl(
                index / "text_index.jsonl",
                [
                    {
                        "document_id": "cpp-predpis-pojistne-smlouvy-3270612451-2026",
                        "text": (
                            "Předpis pojistného pro VOLVO 4SN 8981. "
                            "Vaše nově předepsané pojistné činí 4 512 Kč/ ročně. "
                            "Roční pojistné za doplňkové pojištění nákladů na nájem "
                            "náhradního vozidla MAXI: 499 Kč. "
                            "Pojistné za pojistné období (navýšené o doplňkové "
                            "pojištění nákladů na nájem náhradního vozidla MAXI): 5 011 Kč. "
                            "Datum splatnosti 1. 8. 2026."
                        ),
                    }
                ],
            )
            self.write_jsonl(
                index / "due_dates.jsonl",
                [
                    {
                        "document_id": "cpp-predpis-pojistne-smlouvy-3270612451-2026",
                        "date": "2026-08-01",
                        "type": "payment_due",
                        "confidence": "high",
                        "context": "K úhradě pro VOLVO 4SN 8981.",
                    }
                ],
            )

            result = reminder_source_detail_action(
                reminder_reference("document-reminder"),
                reminders_path=reminders_path,
                vault_dir=vault,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["kind"], "document")
            self.assertEqual(result["document"]["related_asset"], "VOLVO 4SN 8981")
            self.assertTrue(result["document"]["can_open_pdf"])
            self.assertIn("VOLVO", result["document"]["snippet"])
            self.assertEqual(result["document"]["due_contexts"][0]["date"], "2026-08-01")
            self.assertEqual(
                result["document"]["payment_options"],
                [
                    {
                        "label": "Stávající pojištění bez doplňkového MAXI",
                        "amount": "4 512 Kč",
                        "note": "Částka z věty o nově předepsaném ročním pojistném.",
                    },
                    {
                        "label": "Varianta s doplňkovým pojištěním MAXI",
                        "amount": "5 011 Kč",
                        "note": (
                            "Varianta vznikne jen zaplacením dodatku s doplňkovým "
                            "pojištěním MAXI. Samotné doplňkové MAXI: 499 Kč."
                        ),
                    },
                ],
            )

    def test_local_seznam_email_source_detail_uses_cached_catalog_and_attachments(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir) / "email_seznam"
            root.mkdir()
            (root / "seznam_pojisteni_smlouvy_2011_2026.csv").write_text(
                (
                    "folder,uid,date,sender,subject,matched_terms,attachment_count,"
                    "attachment_names,message_id\n"
                    "INBOX,154544,\"Fri, 15 May 2026 09:59:30 +0000\","
                    "pojisteni@rixo.cz,\"Smlouva č.3275111280, RZ 4SN8981\","
                    "pojisteni,1,ORIGINAL.pdf,<msg>\n"
                ),
                encoding="utf-8",
            )
            attachment_dir = root / "attachments" / "INBOX" / "uid_154544"
            attachment_dir.mkdir(parents=True)
            (attachment_dir / "18_ORIGINAL.pdf").write_bytes(b"%PDF-1.4")
            original_root = cockpit_module.LOCAL_SEZNAM_EMAIL_DIR
            cockpit_module.LOCAL_SEZNAM_EMAIL_DIR = root
            try:
                result = local_seznam_email_source_detail(uid="154544", folder="INBOX")
            finally:
                cockpit_module.LOCAL_SEZNAM_EMAIL_DIR = original_root

            self.assertIsNotNone(result)
            assert result is not None
            self.assertEqual(result["subject"], "Smlouva č.[rodne cislo redigovano], RZ 4SN8981")
            self.assertEqual(result["attachments"][0]["filename"], "18_ORIGINAL.pdf")
            self.assertEqual(result["attachments"][0]["content_type"], "application/pdf")

    def test_open_document_pdf_action_opens_only_indexed_vault_pdf(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            index = vault / "index"
            stored_dir = vault / "vault" / "insurance" / "doc-open"
            stored_dir.mkdir(parents=True)
            pdf = stored_dir / "doklad.pdf"
            pdf.write_bytes(b"%PDF-1.4\n")
            index.mkdir(parents=True)
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "doc-open",
                        "title": "Doklad",
                        "stored_path": str(pdf),
                    }
                ],
            )
            calls: list[list[str]] = []

            result = open_document_pdf_action("doc-open", vault_dir=vault, opener=lambda command: calls.append(command))

            self.assertTrue(result["ok"])
            self.assertEqual(calls[0][0], "/usr/bin/open")
            self.assertEqual(Path(calls[0][1]), pdf.resolve())

    def test_document_reader_page_contains_return_controls_and_inline_pdf(self) -> None:
        page = cockpit_module.document_reader_page_html("doc-open", "Doklad & smlouva")

        self.assertIn("Tisknout", page)
        self.assertIn("Zpět do Cockpitu", page)
        self.assertIn("Zavřít okno", page)
        self.assertIn("printFromReader", page)
        self.assertIn("/api/documents/print/prepare", page)
        self.assertIn("/api/documents/print/run", page)
        self.assertIn("window.opener.focus", page)
        self.assertIn("window.close()", page)
        self.assertIn('window.location.href = "/"', page)
        self.assertIn("/documents/pdf?document_id=doc-open", page)
        self.assertIn("Doklad &amp; smlouva", page)

    def test_janicka_chat_action_submits_managed_adam_request_without_agent(self) -> None:
        calls = []

        def fake_submitter(**kwargs) -> dict[str, object]:
            calls.append(kwargs)
            return {"ok": True, "status": "delivered_to_adam", "request_id": "req-1"}

        result = cockpit_module.janicka_chat_action(
            {
                "message": "Kde najdu dokument?",
                "history": [
                    {"role": "user", "content": "Ahoj"},
                    {"role": "assistant", "content": "Dobrý den."},
                ],
            },
            asker=lambda _: self.fail("Janička chat must not call the separate text agent"),
            service_submitter=fake_submitter,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "delivered_to_adam")
        self.assertTrue(result["poll_latest"])
        self.assertEqual(result["request_id"], "req-1")
        self.assertIn("Dotaz jsem předal Adamovi", result["answer"])
        self.assertEqual(calls[0]["message"], "Kde najdu dokument?")
        self.assertEqual(calls[0]["history"][0]["content"], "Ahoj")

    def test_janicka_chat_action_rejects_empty_message(self) -> None:
        result = cockpit_module.janicka_chat_action({"message": "   "}, asker=lambda _: "x")

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "empty_message")

    def test_janicka_chat_action_routes_latest_qn_to_managed_adam(self) -> None:
        calls = []

        def fake_submitter(**kwargs) -> dict[str, object]:
            calls.append(kwargs)
            return {"ok": True, "status": "delivered_to_adam", "request_id": "req-qn"}

        result = cockpit_module.janicka_chat_action(
            {"message": "Najdi mi poslední QN."},
            asker=lambda _: self.fail("Janička chat must not call the separate text agent"),
            service_submitter=fake_submitter,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "delivered_to_adam")
        self.assertEqual(result["request_id"], "req-qn")
        self.assertEqual(calls[0]["message"], "Najdi mi poslední QN.")

    def test_janicka_chat_action_routes_followup_detail_to_managed_adam(self) -> None:
        calls = []

        def fake_submitter(**kwargs) -> dict[str, object]:
            calls.append(kwargs)
            return {"ok": True, "status": "delivered_to_adam", "request_id": "req-detail"}

        result = cockpit_module.janicka_chat_action(
            {
                "message": "Ano, detail.",
                "history": [
                    {
                        "role": "assistant",
                        "content": "Poslední QN je **#37** z **2026-06-05 05:14:45**.",
                    }
                ],
            },
            asker=lambda _: self.fail("Janička chat must not call the separate text agent"),
            service_submitter=fake_submitter,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "delivered_to_adam")
        self.assertEqual(calls[0]["message"], "Ano, detail.")
        self.assertIn("Poslední QN je **#37**", calls[0]["history"][0]["content"])

    def test_janicka_latest_codex_reply_matches_text_bridge_response(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            response_path = Path(temp_dir) / "last_adam_response.json"
            response_path.write_text(
                json.dumps(
                    {
                        "ok": True,
                        "available": True,
                        "route": "janicka_text_bridge",
                        "user_text": "Kde najdu dokument?",
                        "adam_response": "Dokument najdeš přes tlačítko Najít dokument.",
                        "created_at": "2026-06-07T10:00:00+00:00",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = cockpit_module.janicka_latest_codex_reply_action(
                {"message": "Kde najdu dokument?"},
                response_path=response_path,
            )

        self.assertTrue(result["ok"])
        self.assertTrue(result["available"])
        self.assertEqual(result["answer"], "Dokument najdeš přes tlačítko Najít dokument.")

    def test_janicka_chat_memory_context_includes_project_files(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            base = Path(temp_dir)
            cookbook = base / "cookbook.md"
            takeover = base / "takeover.md"
            active = base / "active.md"
            index = base / "index.md"
            cookbook.write_text("Kuchařka: Zeptat se Adama je textový chat.", encoding="utf-8")
            takeover.write_text("Projekt: Janička Cockpit pro Janu.", encoding="utf-8")
            active.write_text("Aktivní projekty: další krok Rodinné projekty.", encoding="utf-8")
            index.write_text("Memory index: janicka_cockpit_takeover.md.", encoding="utf-8")

            context = cockpit_module.janicka_chat_memory_context(
                cookbook_path=cookbook,
                takeover_path=takeover,
                active_projects_path=active,
                memory_index_path=index,
            )

        self.assertIn("Kuchařka: Zeptat se Adama", context)
        self.assertIn("Projekt: Janička Cockpit", context)
        self.assertIn("Aktivní projekty", context)
        self.assertIn("Memory index", context)

    def test_janicka_cookbook_page_renders_markdown_safely(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "cookbook.md"
            path.write_text(
                "# Kuchařka\n\n"
                "Použij `Janička`.\n\n"
                "1. Do hledání napsat běžná slova, například název firmy nebo\n"
                "   téma.\n\n"
                "- Najít dokument\n"
                "- <script>alert(1)</script>\n",
                encoding="utf-8",
            )

            page = cockpit_module.janicka_cookbook_page_html(path)

        self.assertIn("Janička Cockpit - kuchařka", page)
        self.assertIn("<h1>Kuchařka</h1>", page)
        self.assertIn("<code>Janička</code>", page)
        self.assertIn("<li>Do hledání napsat běžná slova, například název firmy nebo téma.</li>", page)
        self.assertIn("<li>Najít dokument</li>", page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)
        self.assertNotIn("<script>alert(1)</script>", page)

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
        self.assertIn("Otevřít / číst", COCKPIT_HTML)
        self.assertIn("Otevřít / číst PDF", COCKPIT_HTML)
        self.assertIn("openDocumentForReading", COCKPIT_HTML)
        self.assertIn("openDocumentReaderWindow", COCKPIT_HTML)
        self.assertIn("documentReaderUrl", COCKPIT_HTML)
        self.assertIn("search-result-head-actions", COCKPIT_HTML)
        self.assertIn("/documents/read?document_id=", COCKPIT_HTML)
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
                actions_path=Path(temp_dir) / "email_work_queue_actions.jsonl",
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

    def test_document_intake_email_scan_status_is_headers_only(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            result = document_intake_email_scan_status(
                limit_per_source=10,
                since="2026-06-01T07:00:00+00:00",
                days=0,
                decisions_path=Path(temp_dir) / "email_processing_decisions.json",
                actions_path=Path(temp_dir) / "email_work_queue_actions.jsonl",
                icloud_provider_factory=lambda: _FakeEmailProvider(
                    [
                        EmailHeader(
                            internal_id="10",
                            date="Mon, 1 Jun 2026 10:00:00 +0200",
                            sender="Pojišťovna <pojistovna@example.com>",
                            subject="Pojistná smlouva PDF",
                            attachments=(
                                EmailAttachmentMeta(
                                    filename="smlouva.pdf",
                                    content_type="application/pdf",
                                    size_bytes=300_000,
                                    part_id="2",
                                    content_id="",
                                    disposition="attachment",
                                ),
                            ),
                        ),
                        EmailHeader(
                            internal_id="11",
                            date="Mon, 1 Jun 2026 11:00:00 +0200",
                            sender="Pet Shop <shop@example.com>",
                            subject="Akce na krmivo pro mazlíčky",
                        )
                    ]
                ),
                seznam_provider_factory=lambda: _FakeEmailProvider([]),
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["raw_count"], 2)
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["filtered_out_count"], 1)
        self.assertEqual(result["items"][0]["subject"], "Pojistná smlouva PDF")
        self.assertEqual(result["items"][0]["sender"], "Pojišťovna <[e-mail redigovan]>")
        self.assertEqual(result["items"][0]["pdf_attachment_count"], 1)
        self.assertEqual(result["items"][0]["large_pdf_attachment_count"], 1)
        self.assertEqual(result["items"][0]["attachment_metadata"][0]["filename"], "smlouva.pdf")
        self.assertEqual(result["items"][0]["filter_label"], "Dokumentový kandidát")
        self.assertIn("document_candidates", result["filter"]["mode"])
        self.assertEqual(result["monitor"]["mode"], "headers_only")
        self.assertTrue(result["monitor"]["does_not_read_bodies"])
        self.assertTrue(result["monitor"]["does_not_download_attachments"])
        self.assertTrue(result["monitor"]["does_read_attachment_metadata"])
        self.assertTrue(result["monitor"]["does_not_write_decisions"])
        serialized = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("body_text", serialized)
        self.assertNotIn("PDFDATA", serialized)

    def test_new_email_headers_overview_skips_completed_work_queue_items(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            actions_path = Path(temp_dir) / "email_work_queue_actions.jsonl"
            completed_id = email_processing_item_id("", "iCloud", "INBOX", "10", "", "")
            self.write_jsonl(
                actions_path,
                [
                    {
                        "action": "process_email_work_queue_batch",
                        "items": [
                            {
                                "item_id": completed_id,
                                "provider": "iCloud",
                                "folder": "INBOX",
                                "uid": "10",
                                "status": "saved",
                            }
                        ],
                    }
                ],
            )

            result = new_email_headers_overview(
                limit_per_source=50,
                since="2026-06-01T07:00:00+00:00",
                known_ids={completed_id},
                decisions_path=Path(temp_dir) / "email_processing_decisions.json",
                actions_path=actions_path,
                icloud_provider_factory=lambda: _FakeEmailProvider(
                    [
                        EmailHeader(
                            internal_id="11",
                            date="Mon, 1 Jun 2026 11:00:00 +0200",
                            sender="Sender <sender@example.com>",
                            subject="Ještě nezpracovaný e-mail",
                        ),
                        EmailHeader(
                            internal_id="10",
                            date="Mon, 1 Jun 2026 10:00:00 +0200",
                            sender="Sender <sender@example.com>",
                            subject="Už zpracovaný e-mail",
                        ),
                    ]
                ),
                seznam_provider_factory=lambda: _FakeEmailProvider([]),
            )

        self.assertTrue(result["ok"])
        self.assertEqual([item["uid"] for item in result["items"]], ["11"])
        self.assertGreaterEqual(result["skipped_completed_count"], 1)
        self.assertEqual(result["suppressed_known_ids"], [completed_id])

    def test_document_intake_email_scan_reports_suppressed_known_completed_items(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            actions_path = Path(temp_dir) / "email_work_queue_actions.jsonl"
            completed_id = email_processing_item_id("", "Seznam", "INBOX", "155808", "", "")
            self.write_jsonl(
                actions_path,
                [
                    {
                        "action": "process_email_work_queue_batch",
                        "items": [
                            {
                                "item_id": completed_id,
                                "provider": "Seznam",
                                "folder": "INBOX",
                                "uid": "155808",
                                "status": "saved",
                            }
                        ],
                    }
                ],
            )

            result = document_intake_email_scan_status(
                limit_per_source=10,
                since="2026-06-08T09:00:00+00:00",
                days=0,
                known_ids={completed_id},
                decisions_path=Path(temp_dir) / "email_processing_decisions.json",
                actions_path=actions_path,
                icloud_provider_factory=lambda: _FakeEmailProvider([]),
                seznam_provider_factory=lambda: _FakeEmailProvider(
                    [
                        EmailHeader(
                            internal_id="155808",
                            date="Mon, 8 Jun 2026 09:51:59 +0200",
                            sender="T-Mobile <billing@example.com>",
                            subject="Vyúčtování služeb od T-Mobile",
                            attachments=(
                                EmailAttachmentMeta(
                                    filename="vyuctovani.pdf",
                                    content_type="application/pdf",
                                    size_bytes=300_000,
                                    part_id="2",
                                    content_id="",
                                    disposition="attachment",
                                ),
                            ),
                        )
                    ]
                ),
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["items"], [])
        self.assertEqual(result["suppressed_known_ids"], [completed_id])

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
            self.assertEqual(result["items"][0]["attachments"][0]["document_id"], docs[0]["document_id"])
            self.assertEqual(result["items"][0]["attachments"][0]["document_ref"], document_reference(docs[0]["document_id"]))
            self.assertEqual(len(text_rows), 1)
            self.assertTrue(actions_path.exists())
            self.assertTrue(activity_state_path.exists())

    def test_preview_email_work_queue_attachment_opens_temp_pdf_without_vault_import(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            preview_dir = root / "preview"
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
            commands: list[list[str]] = []

            result = preview_email_work_queue_attachment_action(
                provider="iCloud",
                folder="INBOX",
                uid="14157",
                part_id="2",
                preview_dir=preview_dir,
                opener=lambda command: commands.append(command),
                icloud_provider_factory=lambda: provider,
            )

            self.assertTrue(result["ok"])
            self.assertIn("dočasný náhled", result["message"])
            self.assertEqual(commands[0][0], "/usr/bin/open")
            self.assertTrue(Path(commands[0][1]).exists())
            self.assertTrue(str(Path(commands[0][1])).startswith(str(preview_dir)))
            self.assertFalse((root / "documents" / "index" / "documents_index.jsonl").exists())

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
            self.assertIn("Potvrzuji, přesuň 1 e-mail označený ke smazání do koše.", result["items"][0]["required_confirmation"])

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
            self.assertEqual(result["items"][0]["trash_folder"], "Deleted Messages")
            self.assertEqual(result["items"][0]["trash_uid"], "914157")
            self.assertEqual(result["items"][0]["message_id"], "<14157@example.com>")

    def test_process_email_work_queue_batch_confirmed_bulk_trash_uses_one_confirmation(self) -> None:
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
                    },
                    {
                        "id": "trash-2",
                        "provider": "iCloud",
                        "folder": "INBOX",
                        "uid": "14158",
                        "queueDecision": "trash_requested",
                    },
                ],
                trash_confirmation_text="Potvrzuji, přesuň 2 e-maily označené ke smazání do koše.",
                archive_directory=Path(temp_dir) / "archive",
                documents_dir=Path(temp_dir) / "documents",
                decisions_path=Path(temp_dir) / "decisions.json",
                actions_path=Path(temp_dir) / "actions.jsonl",
                activity_state_path=Path(temp_dir) / "activity.json",
                icloud_provider_factory=lambda: provider,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["summary"]["trashed"], 2)
            self.assertEqual(
                provider.trash_calls,
                [
                    {"uid": "14157", "folder": "INBOX"},
                    {"uid": "14158", "folder": "INBOX"},
                ],
            )

    def test_process_email_work_queue_purge_trash_requires_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            provider = _FakeArchiveProvider(_archive_source_without_attachment())

            result = process_email_work_queue_purge_trash_batch(
                items=[
                    {
                        "id": "trash-1",
                        "provider": "iCloud",
                        "uid": "14157",
                        "trash_folder": "Deleted Messages",
                        "trash_uid": "914157",
                    }
                ],
                actions_path=Path(temp_dir) / "actions.jsonl",
                icloud_provider_factory=lambda: provider,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["summary"]["purge_pending"], 1)
            self.assertFalse(provider.purge_calls)
            self.assertIn("čeká na potvrzení tlačítkem", result["message"])

    def test_process_email_work_queue_purge_trash_confirmed_uses_provider_expunge(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            provider = _FakeArchiveProvider(_archive_source_without_attachment())

            result = process_email_work_queue_purge_trash_batch(
                items=[
                    {
                        "id": "trash-1",
                        "provider": "iCloud",
                        "uid": "14157",
                        "trash_folder": "Deleted Messages",
                        "trash_uid": "914157",
                        "message_id": "<14157@example.com>",
                    }
                ],
                confirmed=True,
                actions_path=Path(temp_dir) / "actions.jsonl",
                icloud_provider_factory=lambda: provider,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["summary"]["purged"], 1)
            self.assertEqual(
                provider.purge_calls,
                [
                    {
                        "trash_uid": "914157",
                        "message_id": "<14157@example.com>",
                        "trash_folder": "Deleted Messages",
                    }
                ],
            )

    def test_email_processing_html_contains_readonly_overview_controls(self) -> None:
        self.assertIn("Email Processing", EMAIL_PROCESSING_HTML)
        self.assertIn("/api/email-processing/overview", EMAIL_PROCESSING_HTML)
        self.assertIn("/api/email-processing/pending-work", EMAIL_PROCESSING_HTML)
        self.assertIn("/api/email-processing/decision", EMAIL_PROCESSING_HTML)
        self.assertIn("/api/email-processing/new-headers", EMAIL_PROCESSING_HTML)
        self.assertIn("/api/email-processing/read-message", EMAIL_PROCESSING_HTML)
        self.assertIn("/api/email-processing/process-batch", EMAIL_PROCESSING_HTML)
        self.assertIn("/api/email-processing/purge-trash", EMAIL_PROCESSING_HTML)
        self.assertIn("trashBatchBtn", EMAIL_PROCESSING_HTML)
        self.assertIn("purgeTrashBtn", EMAIL_PROCESSING_HTML)
        self.assertIn("Emaily určené ke smazání smazat", EMAIL_PROCESSING_HTML)
        self.assertIn("Trvale smazat e-maily v koši", EMAIL_PROCESSING_HTML)
        self.assertIn("confirmed: true", EMAIL_PROCESSING_HTML)
        self.assertNotIn("Potvrzuji, trvale smaž", EMAIL_PROCESSING_HTML)
        self.assertNotIn("opiš přesně potvrzovací větu", EMAIL_PROCESSING_HTML)
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
        self.assertIn("function returnToCockpit", EMAIL_PROCESSING_HTML)
        self.assertIn("window.opener.focus", EMAIL_PROCESSING_HTML)
        self.assertIn("window.close()", EMAIL_PROCESSING_HTML)
        self.assertIn('cockpitBtn.addEventListener("click", returnToCockpit)', EMAIL_PROCESSING_HTML)
        self.assertNotIn('cockpitBtn.addEventListener("click", () => {\\n      const cockpit = window.open("/", "SamanthaCockpit"', EMAIL_PROCESSING_HTML)
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
        self.assertIn("Náhled PDF", EMAIL_PROCESSING_HTML)
        self.assertIn("/api/email-processing/preview-attachment", EMAIL_PROCESSING_HTML)
        self.assertIn("bindAttachmentPreviewButtons", EMAIL_PROCESSING_HTML)
        self.assertIn("Právě uložené přílohy", EMAIL_PROCESSING_HTML)
        self.assertIn("Otevřít uložené PDF", EMAIL_PROCESSING_HTML)
        self.assertIn("/documents/read?document_id=", EMAIL_PROCESSING_HTML)
        self.assertIn("collectImportedAttachments", EMAIL_PROCESSING_HTML)
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

    def test_document_print_preflight_warns_when_printer_is_not_visible(self) -> None:
        def fake_runner(command: list[str], timeout: float) -> tuple[int, str]:
            if command[0] == "networksetup":
                return 0, "Current Wi-Fi Network: OtherWifi"
            return 1, ""

        result = cockpit_module.document_print_preflight_status(command_runner=fake_runner)

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "printer_not_visible")
        self.assertIn("Telekom-865692", result["message"])
        self.assertIn("HP LaserJet M110w", result["message"])
        self.assertIn("OtherWifi", result["message"])

    def test_document_print_preflight_warns_when_printer_needs_media(self) -> None:
        def fake_runner(command: list[str], timeout: float) -> tuple[int, str]:
            if command[0] == "networksetup":
                return 0, "Current Wi-Fi Network: Telekom-865692"
            if command[0] == "ippfind":
                return 0, "ipp://NPI1CA1A9.local:631/ipp/print stopped accepting-jobs toner-low-warning,media-empty-error"
            return 0, ""

        result = cockpit_module.document_print_preflight_status(command_runner=fake_runner)

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "printer_blocked")
        self.assertIn("papír", result["message"])
        self.assertIn("A4", result["message"])

    def test_prepare_print_action_stops_before_queue_copy_when_preflight_fails(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault, document_id, source = self.create_indexed_document(Path(temp_dir))

            result = prepare_document_print_action(
                document_id=document_id,
                vault_dir=vault,
                preflight_checker=lambda: {
                    "ok": False,
                    "status": "printer_not_visible",
                    "message": "Pro tisk je třeba Wi‑Fi Telekom-865692.",
                },
            )

            self.assertFalse(result["ok"])
            self.assertIn("Telekom-865692", result["message"])
            self.assertFalse((vault / "print_queue").exists())
            self.assertTrue(source.exists())

    def test_run_print_action_uses_preferred_hp_queue(self) -> None:
        with patch("app.cockpit.run_document_print_job") as fake_runner:
            fake_runner.return_value = SimpleNamespace(
                status="printed",
                message="ok",
                print_job_id="print-123",
                document_id="doc-123",
            )

            result = cockpit_module.run_document_print_action(
                print_job_id="print-123",
                confirmation_text="Potvrzuji, vytiskni print job print-123.",
            )

            self.assertTrue(result["ok"])
            self.assertEqual(fake_runner.call_args.kwargs["printer"], "HP_LaserJet_M110w__1CA1A9__20240926171754")

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
    def reminder(reminder_id: str, title: str, due_date: str, status: str = "open") -> dict[str, object]:
        return {
            "id": reminder_id,
            "title": title,
            "notes": "",
            "due_date": due_date,
            "priority": "high",
            "status": status,
            "source": {"type": "test", "uid": "manual", "date": "", "sender": "test"},
            "links": [],
            "attachments": [],
        }

    @staticmethod
    def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )

    @staticmethod
    def quantitative_runner(*, ls_files: str, status: str):
        def run(args, **kwargs):
            if args[:2] == ["git", "ls-files"]:
                return subprocess.CompletedProcess(args=args, returncode=0, stdout=ls_files, stderr="")
            if args[:3] == ["git", "status", "--short"]:
                return subprocess.CompletedProcess(args=args, returncode=0, stdout=status, stderr="")
            raise AssertionError(f"Unexpected command: {args}")

        return run

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
        self.purge_calls: list[dict[str, object]] = []

    def read_archive_source_by_uid(self, uid: str, max_chars: int = 50_000, folder: str = "INBOX") -> EmailArchiveSource:
        self.archive_calls.append({"uid": uid, "max_chars": max_chars, "folder": folder})
        return self._source

    def move_message_to_trash(self, uid: str, folder: str = "INBOX") -> dict[str, str]:
        self.trash_calls.append({"uid": uid, "folder": folder})
        return {"trash_folder": "Deleted Messages", "trash_uid": f"9{uid}", "message_id": f"<{uid}@example.com>"}

    def permanently_delete_message_from_trash(
        self,
        *,
        trash_uid: str = "",
        message_id: str = "",
        trash_folder: str = "",
    ) -> None:
        self.purge_calls.append({"trash_uid": trash_uid, "message_id": message_id, "trash_folder": trash_folder})


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
