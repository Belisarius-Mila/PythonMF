from __future__ import annotations

import base64
import csv
import json
import re
import subprocess
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import app.cockpit as cockpit_module
from app.cockpit import (
    COCKPIT_HTML,
    COCKPIT_POST_ACTIONS,
    EMAIL_PROCESSING_HTML,
    action_queue_status,
    accept_document_classification_suggestion_action,
    cancel_payment_reminder_action,
    cockpit_live_status,
    cockpit_status,
    create_document_due_reminder_action,
    document_reference,
    library_archive_text_action,
    library_archive_book_action,
    library_archive_url_action,
    library_article_reextract_preview_action,
    library_book_summary_draft_action,
    library_book_cover_draft_action,
    library_book_cover_prepare_action,
    library_book_option_add_action,
    library_book_options_status_action,
    library_book_text_ocr_action,
    library_book_text_photo_prepare_action,
    library_book_isbn_lookup_action,
    library_book_isbn_photo_action,
    library_attach_image_action,
    library_delete_article_action,
    library_remove_attachment_action,
    library_update_article_action,
    library_update_attachment_action,
    lekarna_admin_page_html,
    lekarna_auto_import_apply_action,
    lekarna_auto_import_draft_action,
    lekarna_import_manifest_load_action,
    lekarna_import_manifest_retry_pil_action,
    lekarna_import_manifest_save_action,
    lekarna_import_photos_status,
    lekarna_retire_apply_action,
    lekarna_retire_preview_action,
    lekarna_search_action,
    publish_lekarna_encrypted_bundle,
    library_read_state_action,
    cockpit_edge_tts_action,
    cockpit_codex_approval_clear_action,
    cockpit_dev_runner_actions,
    cockpit_dev_runner_run_action,
    cockpit_speak_action,
    human_adam_transcribe_action,
    human_adam_github_batch_action,
    human_adam_github_batch_audit_action,
    human_adam_main_remote_sync_action,
    human_adam_main_remote_sync_audit_action,
    human_adam_simple_main_deployment_audit_action,
    human_adam_simple_main_deployment_action,
    human_adam_simple_main_deployment_verification_action,
    transcribe_audio_base64_isolated,
    document_intake_email_scan_status,
    document_intake_status,
    document_cases_status,
    document_case_detail_status,
    document_classification_status,
    document_due_candidates_status,
    document_review_report_status,
    document_work_status,
    email_header_to_processing_item,
    email_processing_batch_groups,
    email_processing_item_id,
    email_processing_pending_work_items,
    email_processing_pending_purge_items,
    classify_email_processing_category,
    latest_email_processing_overview,
    local_seznam_email_source_detail,
    mark_reminder_done_action,
    move_document_lifecycle_action,
    new_email_headers_overview,
    open_desktop_app_action,
    open_document_pdf_action,
    parse_active_projects_table,
    parse_global_tools_table,
    parse_infrastructure_capabilities_table,
    parse_email_processing_items,
    prepare_document_print_action,
    projects_status,
    purge_trash_confirmation_phrase,
    quick_note_deliver_action,
    quick_note_detail_status,
    quick_notes_status,
    project_audit_recent_reports,
    project_audit_report_file_status,
    project_audit_report_status,
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
    session_autosave_cleanup_action,
    server_health_status,
    set_email_processing_done_flag,
    set_document_reading_status_action,
    start_cockpit_restart_action,
    stored_documents_review_status,
    urgent_reminder_deliver_action,
    urgent_reminder_done_action,
    urgent_reminders_status,
    update_document_classification_metadata_action,
    web_apps_catalog,
)
from app.email.archive_models import EmailArchiveSource
from app.email.models import EmailAttachmentMeta, EmailHeader, EmailMessage


class CockpitTests(unittest.TestCase):
    def cockpit_do_post_routes(self) -> list[str]:
        source = Path(cockpit_module.__file__).read_text(encoding="utf-8")
        start = source.index("def do_POST(self) -> None:")
        end = source.index("def read_json(self) -> dict[str, Any]:", start)
        do_post_source = source[start:end]
        return re.findall(r'if parsed\.path == "([^"]+)":', do_post_source)

    def cockpit_do_get_routes(self) -> list[str]:
        source = Path(cockpit_module.__file__).read_text(encoding="utf-8")
        start = source.index("def do_GET(self) -> None:")
        end = source.index("def do_POST(self) -> None:", start)
        do_get_source = source[start:end]
        return re.findall(r'if parsed\.path == "([^"]+)":', do_get_source)

    def cockpit_do_get_prefix_routes(self) -> list[str]:
        source = Path(cockpit_module.__file__).read_text(encoding="utf-8")
        start = source.index("def do_GET(self) -> None:")
        end = source.index("def do_POST(self) -> None:", start)
        do_get_source = source[start:end]
        return re.findall(r'if parsed\.path\.startswith\("([^"]+)"\):', do_get_source)

    def frontend_literal_routes(self) -> list[tuple[str, str]]:
        html_sources = {
            "cockpit": COCKPIT_HTML,
            "email_processing": EMAIL_PROCESSING_HTML,
            "lekarna_admin": cockpit_module.lekarna_admin_page_html(),
            "document_reader": cockpit_module.document_reader_page_html("doc-test", "Test document"),
            "purchase_reader": cockpit_module.purchase_reader_page_html("purchase-test", "Test purchase"),
        }
        routes: list[tuple[str, str]] = []
        for source_name, html_text in html_sources.items():
            for raw_path in re.findall(
                r'/(?:api|documents|purchases|email-processing|janicka-kucharka|lekarna-admin|local-apps)[^"\'`\s<)]*',
                html_text,
            ):
                route = raw_path.split("?", 1)[0].split("${", 1)[0]
                if route:
                    routes.append((source_name, route))
        return sorted(set(routes))

    def test_cockpit_post_action_registry_matches_do_post_routes(self) -> None:
        registered_paths = [item["path"] for item in COCKPIT_POST_ACTIONS]
        routed_paths = self.cockpit_do_post_routes()

        self.assertEqual(len(registered_paths), len(set(registered_paths)))
        self.assertEqual(registered_paths, routed_paths)

    def test_cockpit_post_action_registry_has_required_metadata(self) -> None:
        allowed_risks = {
            "delete_or_purge",
            "dev_runner",
            "external_ai",
            "external_lookup",
            "external_send",
            "git_commit_push",
            "git_push",
            "git_fast_forward",
            "git_fast_forward_push_restart",
            "local_open",
            "local_service",
            "print",
            "private_write",
            "read_only_via_post",
            "voice_local_outbound",
            "workspace_write",
        }
        allowed_test_levels = {"direct", "indirect", "ui_presence", "voice_tests"}
        required_keys = {"path", "label", "risk", "confirmation", "handler_name", "test_level"}

        for item in COCKPIT_POST_ACTIONS:
            self.assertEqual(required_keys, set(item))
            self.assertTrue(item["path"].startswith("/api/"))
            self.assertIn(item["risk"], allowed_risks)
            self.assertIn(item["test_level"], allowed_test_levels)
            self.assertTrue(item["label"].strip())
            self.assertTrue(item["confirmation"].strip())
            self.assertTrue(item["handler_name"].strip())
            self.assertTrue(hasattr(cockpit_module, item["handler_name"]), item["handler_name"])

    def test_library_reextract_preview_action_returns_only_redacted_metrics(self) -> None:
        safe_result = {
            "ok": True,
            "read_only": True,
            "source_encoding": "iso-8859-2",
            "changed": True,
            "metrics": {
                "source_bytes": 420,
                "current_chars": 100,
                "preview_chars": 100,
                "char_delta": 0,
                "different_positions": 2,
                "current_replacement_chars": 0,
                "preview_replacement_chars": 0,
                "current_control_chars": 0,
                "preview_control_chars": 0,
            },
        }
        with patch(
            "app.cockpit.preview_article_source_reextract",
            return_value=safe_result,
        ) as preview_mock:
            result = library_article_reextract_preview_action(
                {
                    "article_id": "private-id",
                    "source_encoding": "ISO-8859-2",
                }
            )

        self.assertEqual(result, safe_result)
        preview_mock.assert_called_once_with(
            article_id="private-id",
            source_encoding="ISO-8859-2",
        )
        registry_item = next(
            item
            for item in COCKPIT_POST_ACTIONS
            if item["path"] == "/api/library/reextract-preview"
        )
        self.assertEqual(registry_item["risk"], "read_only_via_post")
        self.assertEqual(registry_item["confirmation"], "none_readonly_no_persistence")

    def test_human_adam_transcribe_post_route_has_narrow_registry_card(self) -> None:
        card = next(
            item for item in COCKPIT_POST_ACTIONS if item["path"] == "/api/human-adam/transcribe"
        )

        self.assertEqual(card["risk"], "external_ai")
        self.assertEqual(card["confirmation"], "explicit_microphone_recording_no_delivery")
        self.assertEqual(card["handler_name"], "human_adam_transcribe_action")
        self.assertIn("/api/human-adam/transcribe", self.cockpit_do_post_routes())
        source = Path(cockpit_module.__file__).read_text(encoding="utf-8")
        route_start = source.index('if parsed.path == "/api/human-adam/transcribe":')
        route_end = source.index('if parsed.path == "/api/human-adam/connect":', route_start)
        self.assertIn("self.respond_json(human_adam_transcribe_action(payload))", source[route_start:route_end])

    def test_human_adam_context_anchor_http_api_is_fully_retired(self) -> None:
        self.assertNotIn(
            "/api/human-adam/context-anchor",
            {item["path"] for item in COCKPIT_POST_ACTIONS},
        )
        self.assertNotIn(
            "/api/human-adam/context-anchor",
            self.cockpit_do_get_routes(),
        )
        self.assertNotIn(
            "/api/human-adam/context-anchor",
            self.cockpit_do_post_routes(),
        )
        source = Path(cockpit_module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("human_adam_context_anchor_action", source)
        self.assertNotIn("human_adam_context_anchor_update_action", source)

    def test_human_adam_thread_rotation_has_exact_confirmation_registry_card_and_routes(self) -> None:
        card = next(
            item for item in COCKPIT_POST_ACTIONS if item["path"] == "/api/human-adam/thread-rotation"
        )

        self.assertEqual(card["risk"], "private_write")
        self.assertEqual(card["confirmation"], "exact_thread_rotation_phrase")
        self.assertEqual(card["handler_name"], "human_adam_thread_rotation_action")
        self.assertIn("/api/human-adam/thread-rotation", self.cockpit_do_get_routes())
        self.assertIn("/api/human-adam/thread-rotation", self.cockpit_do_post_routes())

    def test_human_adam_development_semaphore_has_private_explicit_registry_card_and_routes(self) -> None:
        card = next(
            item
            for item in COCKPIT_POST_ACTIONS
            if item["path"] == "/api/human-adam/development-semaphore"
        )

        self.assertEqual(card["risk"], "private_write")
        self.assertEqual(card["confirmation"], "explicit_development_owner_change")
        self.assertEqual(card["handler_name"], "human_adam_development_semaphore_action")
        self.assertIn("/api/human-adam/development-semaphore", self.cockpit_do_get_routes())
        self.assertIn("/api/human-adam/development-semaphore", self.cockpit_do_post_routes())

    def test_human_adam_deferred_integration_has_exact_marker_registry_card_and_route(
        self,
    ) -> None:
        card = next(
            item
            for item in COCKPIT_POST_ACTIONS
            if item["path"] == "/api/human-adam/deferred-integration"
        )

        self.assertEqual(card["risk"], "git_commit_push")
        self.assertEqual(
            card["confirmation"],
            "exact_deferred_integration_phrase_and_ownership_marker",
        )
        self.assertEqual(
            card["handler_name"],
            "human_adam_deferred_integration_action",
        )
        self.assertIn(
            "/api/human-adam/deferred-integration",
            self.cockpit_do_post_routes(),
        )
        self.assertNotIn(
            "/api/human-adam/deferred-integration",
            self.cockpit_do_get_routes(),
        )
        source = Path(cockpit_module.__file__).read_text(encoding="utf-8")
        route_start = source.index(
            'if parsed.path == "/api/human-adam/deferred-integration":'
        )
        route_end = source.index(
            'if parsed.path == "/api/human-adam/thread-rotation":',
            route_start,
        )
        route_source = source[route_start:route_end]
        self.assertIn(
            "human_adam_deferred_integration_action(payload, service=HUMAN_ADAM)",
            route_source,
        )
        self.assertNotIn("merge", route_source.casefold())
        self.assertNotIn("rebase", route_source.casefold())

    def test_human_adam_owned_wip_recovery_has_exact_registry_card_and_route(
        self,
    ) -> None:
        card = next(
            item
            for item in COCKPIT_POST_ACTIONS
            if item["path"] == "/api/human-adam/owned-wip-recovery"
        )

        self.assertEqual(card["risk"], "git_commit_push")
        self.assertEqual(
            card["confirmation"],
            "exact_owned_wip_recovery_phrase_and_metadata",
        )
        self.assertEqual(
            card["handler_name"],
            "human_adam_owned_wip_recovery_action",
        )
        self.assertIn(
            "/api/human-adam/owned-wip-recovery",
            self.cockpit_do_post_routes(),
        )
        self.assertNotIn(
            "/api/human-adam/owned-wip-recovery",
            self.cockpit_do_get_routes(),
        )
        source = Path(cockpit_module.__file__).read_text(encoding="utf-8")
        route_start = source.index(
            'if parsed.path == "/api/human-adam/owned-wip-recovery":'
        )
        route_end = source.index(
            'if parsed.path == "/api/human-adam/thread-rotation":',
            route_start,
        )
        route_source = source[route_start:route_end]
        self.assertIn(
            "human_adam_owned_wip_recovery_action(payload, service=HUMAN_ADAM)",
            route_source,
        )
        self.assertNotIn("merge", route_source.casefold())
        self.assertNotIn("rebase", route_source.casefold())

    def test_development_branch_lifecycle_browser_route_is_absent(self) -> None:
        self.assertNotIn("/api/human-adam/development-branches", self.cockpit_do_get_routes())
        self.assertNotIn("/api/human-adam/development-branches", self.cockpit_do_post_routes())
        source = Path(cockpit_module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("development_branch_audit_action", source)

    def test_project_continuity_has_read_only_get_route(self) -> None:
        self.assertIn("/api/human-adam/project-continuity", self.cockpit_do_get_routes())
        self.assertNotIn("/api/human-adam/project-continuity", self.cockpit_do_post_routes())
        source = Path(cockpit_module.__file__).read_text(encoding="utf-8")
        route_start = source.index('if parsed.path == "/api/human-adam/project-continuity":')
        route_end = source.index('if parsed.path == "/api/human-adam/thread-rotation":', route_start)
        self.assertIn("human_adam_project_continuity_action(service=HUMAN_ADAM)", source[route_start:route_end])

    def test_human_adam_deploy_route_uses_clean_main_restart_and_verification(self) -> None:
        source = Path(cockpit_module.__file__).read_text(encoding="utf-8")
        route_start = source.index('if parsed.path == "/api/human-adam/deploy":')
        route_end = source.index('if parsed.path == "/api/codex-approval/clear":', route_start)
        route_source = source[route_start:route_end]

        self.assertIn("human_adam_simple_main_deployment_action(", route_source)
        self.assertIn("confirmation == SIMPLE_MAIN_DEPLOYMENT_CONFIRMATION", route_source)
        self.assertIn('if parsed.path == "/api/human-adam/deploy-verification":', route_source)
        self.assertIn("human_adam_simple_main_deployment_verification_action(", route_source)
        self.assertNotIn("human_adam_deploy_action(", route_source)
        self.assertNotIn("record_deployment_restart(", route_source)

    def test_orphaned_deployment_completion_contract_is_absent(self) -> None:
        path = "/api/human-adam/deployment-completion"
        source = Path(cockpit_module.__file__).read_text(encoding="utf-8")

        self.assertNotIn(path, {item["path"] for item in COCKPIT_POST_ACTIONS})
        self.assertNotIn(path, self.cockpit_do_get_routes())
        self.assertNotIn(path, self.cockpit_do_post_routes())
        self.assertNotIn("human_adam_deployment_completion_action", source)
        self.assertNotIn("human_adam_deployment_completion_status_action", source)

    def test_frontend_literal_routes_exist_in_backend(self) -> None:
        exact_backend_routes = set(self.cockpit_do_get_routes()) | set(self.cockpit_do_post_routes())
        prefix_backend_routes = self.cockpit_do_get_prefix_routes()
        missing = [
            (source_name, route)
            for source_name, route in self.frontend_literal_routes()
            if route not in exact_backend_routes
            and not any(route.startswith(prefix) for prefix in prefix_backend_routes)
        ]

        self.assertEqual([], missing)

    def test_retired_appserver_panels_and_routes_are_absent(self) -> None:
        source = Path(cockpit_module.__file__).read_text(encoding="utf-8")
        for retired in (
            "App-server LAB",
            "Adam Remote",
            "appserverLab",
            "remoteWork",
            "/api/appserver-lab",
            "/api/appserver-remote",
            "appserver_lab_",
            "remote_work_cell_",
        ):
            self.assertNotIn(retired, source)
            self.assertNotIn(retired, COCKPIT_HTML)
        registered_paths = {item["path"] for item in COCKPIT_POST_ACTIONS}
        self.assertFalse(any(path.startswith("/api/appserver-lab") for path in registered_paths))
        self.assertFalse(any(path.startswith("/api/appserver-remote") for path in registered_paths))

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

    def test_library_archive_text_action_passes_manual_text_metadata(self) -> None:
        with patch("app.cockpit.archive_text_entry") as archive_mock:
            archive_mock.return_value = {"ok": True, "item": {"id": "text-1"}}

            result = library_archive_text_action(
                {
                    "title": "Recept z chatu",
                    "text": "Mouka a med.",
                    "category": "recipes",
                    "tags": "chatgpt; recept",
                    "source_label": "ChatGPT historický chat",
                    "source_note": "Bez původní URL.",
                }
            )

        self.assertTrue(result["ok"])
        archive_mock.assert_called_once_with(
            title="Recept z chatu",
            text="Mouka a med.",
            category="recipes",
            tags=["chatgpt", "recept"],
            source_label="ChatGPT historický chat",
            source_note="Bez původní URL.",
        )

    def test_library_archive_book_action_passes_structured_metadata(self) -> None:
        with patch("app.cockpit.archive_book_entry") as archive_mock:
            archive_mock.return_value = {"ok": True, "item": {"id": "book-1"}}

            result = library_archive_book_action(
                {
                    "title": "Syntetická kniha",
                    "author": "Testovací autor",
                    "summary": "Stručný syntetický obsah.",
                    "location": "Pracovna, druhá police",
                    "isbn": "978-1-23456-789-7",
                    "tags": "historie; rodina",
                }
            )

        self.assertTrue(result["ok"])
        archive_mock.assert_called_once_with(
            title="Syntetická kniha",
            author="Testovací autor",
            summary="Stručný syntetický obsah.",
            location="Pracovna, druhá police",
            isbn="978-1-23456-789-7",
            tags=["historie", "rodina"],
        )

    def test_library_book_options_actions_list_and_add_private_values(self) -> None:
        options = {
            "locations": ["obývák", "jídelna", "půda"],
            "categories": ["román", "fantasy"],
        }
        with patch("app.cockpit.list_book_options", return_value=options):
            listed = library_book_options_status_action()
        with patch(
            "app.cockpit.add_book_option",
            return_value={
                "options": {**options, "locations": [*options["locations"], "pracovna"]},
                "value": "pracovna",
                "kind": "location",
                "added": True,
            },
        ) as add_option:
            added = library_book_option_add_action({"kind": "location", "value": "pracovna"})

        self.assertTrue(listed["ok"])
        self.assertEqual(listed["options"], options)
        self.assertTrue(added["ok"])
        self.assertTrue(added["added"])
        self.assertIn("pracovna", added["options"]["locations"])
        add_option.assert_called_once_with(kind="location", value="pracovna")

    def test_library_book_option_add_action_reports_validation_error(self) -> None:
        with patch("app.cockpit.add_book_option", side_effect=ValueError("Neplatná položka.")):
            result = library_book_option_add_action({"kind": "category", "value": ""})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "invalid_book_option")
        self.assertEqual(result["message"], "Neplatná položka.")

    def test_library_book_cover_draft_action_returns_preview_without_saving(self) -> None:
        suggestion = {
            "title": "Syntetická kniha",
            "author": "Testovací autor",
            "isbn": "9781234567897",
            "confidence": 0.9,
            "uncertainties": [],
        }
        with patch("app.cockpit.recognize_book_cover", return_value=suggestion) as recognize_mock:
            result = library_book_cover_draft_action(
                {"image_data_url": "data:image/png;base64,c3ludGhldGlj"}
            )

        self.assertTrue(result["ok"])
        self.assertFalse(result["saved"])
        self.assertEqual(result["suggestion"], suggestion)
        recognize_mock.assert_called_once_with(
            image_data_url="data:image/png;base64,c3ludGhldGlj"
        )

    def test_library_book_cover_draft_action_keeps_unreadable_cover_empty(self) -> None:
        suggestion = {"title": "", "author": "", "isbn": "", "confidence": 0, "uncertainties": ["Nečitelné."]}
        with patch("app.cockpit.recognize_book_cover", return_value=suggestion):
            result = library_book_cover_draft_action({"image_data_url": "synthetic"})
        self.assertTrue(result["ok"])
        self.assertFalse(result["saved"])
        self.assertIn("vyplň je ručně", result["message"].casefold())

    def test_library_book_isbn_photo_action_returns_only_validated_isbn_without_saving(self) -> None:
        suggestion = {
            "title": "Soukromý titul se nesmí vrátit",
            "author": "Soukromý autor se nesmí vrátit",
            "isbn": "8020414533",
            "confidence": 0.96,
            "uncertainties": [],
        }
        with patch("app.cockpit.recognize_book_cover", return_value=suggestion) as recognize_mock:
            result = library_book_isbn_photo_action({"image_data_url": "synthetic-photo"})

        self.assertTrue(result["ok"])
        self.assertEqual(result["isbn"], "8020414533")
        self.assertFalse(result["saved"])
        self.assertNotIn("title", result)
        self.assertNotIn("author", result)
        recognize_mock.assert_called_once_with(image_data_url="synthetic-photo")

    def test_library_book_isbn_photo_action_rejects_unreadable_photo_without_saving(self) -> None:
        with patch(
            "app.cockpit.recognize_book_cover",
            return_value={"title": "", "author": "", "isbn": "", "confidence": 0, "uncertainties": []},
        ):
            result = library_book_isbn_photo_action({"image_data_url": "synthetic-photo"})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "book_isbn_not_recognized")
        self.assertFalse(result["saved"])

    def test_library_book_cover_prepare_action_returns_resized_preview_without_saving(self) -> None:
        with patch(
            "app.cockpit.prepare_book_cover_data_url",
            return_value="data:image/jpeg;base64,c21hbGw=",
        ) as prepare_mock:
            result = library_book_cover_prepare_action(
                {"image_data_url": "data:image/heic;base64,b3JpZ2luYWw="}
            )

        self.assertTrue(result["ok"])
        self.assertFalse(result["saved"])
        self.assertEqual(result["filename"], "obalka-knihy.jpg")
        self.assertEqual(result["image_data_url"], "data:image/jpeg;base64,c21hbGw=")
        prepare_mock.assert_called_once_with("data:image/heic;base64,b3JpZ2luYWw=")

    def test_library_book_text_ocr_action_returns_preview_without_saving_or_metadata(self) -> None:
        synthetic_ocr = {
            "text": "Syntetický text z fotografie.",
            "uncertainties": [],
            "image_count": 1,
        }
        with patch("app.cockpit.extract_book_text_from_images", return_value=synthetic_ocr) as ocr_mock:
            result = library_book_text_ocr_action(
                {
                    "image_data_urls": ["data:image/jpeg;base64,cGhvdG8="],
                    "title": "Toto se nesmí odeslat",
                    "location": "Ani umístění",
                    "tags": "Ani tagy",
                }
            )

        self.assertTrue(result["ok"])
        self.assertFalse(result["saved"])
        self.assertEqual(result["ocr"], synthetic_ocr)
        ocr_mock.assert_called_once_with(
            image_data_urls=["data:image/jpeg;base64,cGhvdG8="],
        )

    def test_library_book_text_ocr_action_reports_safe_errors(self) -> None:
        with patch("app.cockpit.extract_book_text_from_images", side_effect=ValueError("Vyber fotografii.")):
            invalid = library_book_text_ocr_action({})
        self.assertEqual(invalid["error"], "invalid_book_text_photos")

        with patch(
            "app.cockpit.extract_book_text_from_images",
            side_effect=cockpit_module.BookTextOcrError("OCR je nedostupné."),
        ):
            failed = library_book_text_ocr_action({"image_data_urls": ["synthetic"]})
        self.assertEqual(failed["error"], "book_text_ocr_failed")

    def test_library_book_text_photo_prepare_action_returns_temporary_resized_copy(self) -> None:
        with patch(
            "app.cockpit.prepare_book_image_data_url",
            return_value="data:image/jpeg;base64,c21hbGw=",
        ) as prepare_mock:
            result = library_book_text_photo_prepare_action(
                {"image_data_url": "data:image/heic;base64,b3JpZ2luYWw="}
            )

        self.assertTrue(result["ok"])
        self.assertFalse(result["saved"])
        self.assertEqual(result["image_data_url"], "data:image/jpeg;base64,c21hbGw=")
        prepare_mock.assert_called_once_with(
            "data:image/heic;base64,b3JpZ2luYWw=",
            image_description="fotografii textu knihy",
            max_edge=1400,
            jpeg_quality=82,
        )

    def test_library_book_summary_draft_action_returns_preview_without_saving(self) -> None:
        synthetic_draft = "Syntetický návrh obsahu. " * 8
        with patch("app.cockpit.generate_book_summary_draft", return_value=synthetic_draft) as generate_mock:
            result = library_book_summary_draft_action(
                {
                    "title": "Syntetická kniha",
                    "author": "Testovací autor",
                    "source_text": "Syntetické podklady bez soukromých údajů. " * 4,
                    "location": "Toto se nesmí odeslat",
                    "tags": "ani tyto tagy",
                }
            )

        self.assertTrue(result["ok"])
        self.assertFalse(result["saved"])
        self.assertEqual(result["draft"], synthetic_draft)
        generate_mock.assert_called_once_with(
            title="Syntetická kniha",
            author="Testovací autor",
            source_text="Syntetické podklady bez soukromých údajů. " * 4,
        )

    def test_library_book_summary_draft_action_reports_safe_errors(self) -> None:
        with patch("app.cockpit.generate_book_summary_draft", side_effect=ValueError("Podklady jsou krátké.")):
            invalid = library_book_summary_draft_action({})
        self.assertFalse(invalid["ok"])
        self.assertEqual(invalid["error"], "invalid_book_summary_source")

        with patch(
            "app.cockpit.generate_book_summary_draft",
            side_effect=cockpit_module.BookSummaryGenerationError("Generování je dočasně nedostupné."),
        ):
            unavailable = library_book_summary_draft_action({})
        self.assertFalse(unavailable["ok"])
        self.assertEqual(unavailable["error"], "book_summary_generation_failed")

    def test_library_book_isbn_lookup_action_returns_preview_without_saving(self) -> None:
        synthetic_lookup = {
            "isbn": "9781234567897",
            "title": "Syntetická kniha",
            "author": "Testovací autor",
            "publisher": "Testovací nakladatelství",
            "publish_date": "2026",
            "number_of_pages": 123,
            "source_name": "Open Library",
            "source_url": "https://openlibrary.org/isbn/9781234567897",
        }
        with patch("app.cockpit.lookup_book_by_isbn", return_value=synthetic_lookup) as lookup_mock:
            result = library_book_isbn_lookup_action(
                {
                    "isbn": "978-1-23456-789-7",
                    "location": "Toto se nesmí odeslat",
                    "summary": "Ani soukromý obsah",
                    "tags": "ani tagy",
                }
            )

        self.assertTrue(result["ok"])
        self.assertFalse(result["saved"])
        self.assertEqual(result["lookup"], synthetic_lookup)
        lookup_mock.assert_called_once_with(isbn="978-1-23456-789-7")

    def test_library_book_isbn_lookup_action_reports_safe_errors(self) -> None:
        with patch("app.cockpit.lookup_book_by_isbn", side_effect=ValueError("ISBN není platné.")):
            invalid = library_book_isbn_lookup_action({"isbn": "bad"})
        self.assertFalse(invalid["ok"])
        self.assertEqual(invalid["error"], "invalid_book_isbn")

        with patch(
            "app.cockpit.lookup_book_by_isbn",
            side_effect=cockpit_module.BookIsbnNotFoundError("Kniha nebyla nalezena."),
        ):
            missing = library_book_isbn_lookup_action({"isbn": "9781234567897"})
        self.assertFalse(missing["ok"])
        self.assertEqual(missing["error"], "book_isbn_not_found")

        with patch(
            "app.cockpit.lookup_book_by_isbn",
            side_effect=cockpit_module.BookIsbnLookupError("Katalog je nedostupný."),
        ):
            unavailable = library_book_isbn_lookup_action({"isbn": "9781234567897"})
        self.assertFalse(unavailable["ok"])
        self.assertEqual(unavailable["error"], "book_isbn_lookup_failed")

        with patch(
            "app.cockpit.lookup_book_by_isbn",
            side_effect=cockpit_module.BookIsbnTimeoutError("Katalog neodpověděl včas."),
        ):
            timeout = library_book_isbn_lookup_action({"isbn": "9781234567897"})
        self.assertEqual(timeout["error"], "book_isbn_lookup_timeout")

        diagnostic_cases = (
            (
                cockpit_module.BookIsbnDnsError("DNS selhalo."),
                "book_isbn_lookup_dns_error",
            ),
            (
                cockpit_module.BookIsbnCertificateError("Certifikát nelze ověřit."),
                "book_isbn_lookup_certificate_error",
            ),
            (
                cockpit_module.BookIsbnTlsError("TLS spojení selhalo."),
                "book_isbn_lookup_tls_error",
            ),
        )
        for diagnostic_error, error_code in diagnostic_cases:
            with self.subTest(error_code=error_code):
                with patch("app.cockpit.lookup_book_by_isbn", side_effect=diagnostic_error):
                    diagnostic = library_book_isbn_lookup_action({"isbn": "9781234567897"})
                self.assertEqual(diagnostic["error"], error_code)

        with patch(
            "app.cockpit.lookup_book_by_isbn",
            side_effect=cockpit_module.BookIsbnConnectionRefusedError("Katalog odmítl spojení."),
        ):
            refused = library_book_isbn_lookup_action({"isbn": "9781234567897"})
        self.assertEqual(refused["error"], "book_isbn_lookup_refused")

        with patch(
            "app.cockpit.lookup_book_by_isbn",
            side_effect=cockpit_module.BookIsbnHttpError(429),
        ):
            http_error = library_book_isbn_lookup_action({"isbn": "9781234567897"})
        self.assertEqual(http_error["error"], "book_isbn_lookup_http_error")
        self.assertEqual(http_error["http_status"], 429)

    def test_library_attach_image_action_decodes_image_and_adds_family_tags(self) -> None:
        with patch("app.cockpit.attach_article_image") as attach_mock:
            attach_mock.return_value = {"ok": True, "item": {"id": "recipe-1"}, "attachment": {"id": "rukopis"}}

            result = library_attach_image_action(
                {
                    "article_id": "recipe-1",
                    "image_data_url": "data:image/png;base64,aW1hZ2U=",
                    "filename": "scan.png",
                    "label": "Babiččin rukopis",
                    "tags": "svatky",
                    "note": "První test.",
                }
            )

        self.assertTrue(result["ok"])
        kwargs = attach_mock.call_args.kwargs
        self.assertEqual(kwargs["article_id"], "recipe-1")
        self.assertEqual(kwargs["image_bytes"], b"image")
        self.assertEqual(kwargs["filename"], "scan.png")
        self.assertEqual(kwargs["label"], "Babiččin rukopis")
        self.assertIn("svatky", kwargs["tags"])
        self.assertIn("rodinny-recept", kwargs["tags"])
        self.assertIn("prepis-overit", kwargs["tags"])

    def test_library_attach_image_action_uses_generic_tags_outside_recipes(self) -> None:
        with patch("app.cockpit.attach_article_image") as attach_mock:
            attach_mock.return_value = {"ok": True, "item": {"id": "science-1"}, "attachment": {"id": "foto"}}

            result = library_attach_image_action(
                {
                    "article_id": "science-1",
                    "image_data_url": "data:image/jpeg;base64,aW1hZ2U=",
                    "filename": "experiment.jpg",
                    "category": "science",
                }
            )

        self.assertTrue(result["ok"])
        kwargs = attach_mock.call_args.kwargs
        self.assertEqual(kwargs["label"], "Doprovodná fotografie")
        self.assertEqual(kwargs["role"], "supporting_image")
        self.assertIn("ma-obrazek", kwargs["tags"])
        self.assertNotIn("rodinny-recept", kwargs["tags"])
        self.assertNotIn("rucne-psany", kwargs["tags"])

    def test_library_update_article_action_passes_editable_fields(self) -> None:
        with patch("app.cockpit.update_article") as update_mock:
            update_mock.return_value = {"ok": True, "item": {"id": "article-1"}}

            result = library_update_article_action(
                {
                    "article_id": "article-1",
                    "title": "Upravený článek",
                    "text": "Nový text.",
                    "category": "science",
                    "tags": "věda; fotografie",
                    "source_label": "Mílova poznámka",
                    "source_note": "Lokálně upraveno.",
                }
            )

        self.assertTrue(result["ok"])
        update_mock.assert_called_once_with(
            article_id="article-1",
            title="Upravený článek",
            text="Nový text.",
            category="science",
            tags=["věda", "fotografie"],
            source_label="Mílova poznámka",
            source_note="Lokálně upraveno.",
            book_author="",
            book_location="",
            book_isbn="",
        )

    def test_library_attachment_edit_and_remove_actions_use_narrow_helpers(self) -> None:
        with (
            patch("app.cockpit.update_article_attachment") as update_mock,
            patch("app.cockpit.remove_article_attachment") as remove_mock,
        ):
            update_mock.return_value = {"ok": True, "attachment": {"id": "foto-1"}}
            remove_mock.return_value = {"ok": True, "attachment_id": "foto-1"}

            updated = library_update_attachment_action(
                {"article_id": "article-1", "attachment_id": "foto-1", "label": "Pohled", "note": "Ze severu."}
            )
            removed = library_remove_attachment_action(
                {
                    "article_id": "article-1",
                    "attachment_id": "foto-1",
                    "user_confirmed": True,
                    "confirmation_text": "Potvrzuji odebrání přílohy",
                }
            )

        self.assertTrue(updated["ok"])
        self.assertTrue(removed["ok"])
        update_mock.assert_called_once_with(
            article_id="article-1",
            attachment_id="foto-1",
            label="Pohled",
            note="Ze severu.",
        )
        remove_mock.assert_called_once_with(
            article_id="article-1",
            attachment_id="foto-1",
            user_confirmed=True,
            confirmation_text="Potvrzuji odebrání přílohy",
        )

    def test_library_delete_article_action_passes_confirmation_gate(self) -> None:
        with patch("app.cockpit.delete_article") as delete_mock:
            delete_mock.return_value = {"ok": True, "item_id": "recipe-1"}

            result = library_delete_article_action(
                {
                    "article_id": "recipe-1",
                    "user_confirmed": True,
                    "confirmation_text": "Potvrzuji vyřazení z knihovny",
                }
            )

        self.assertTrue(result["ok"])
        delete_mock.assert_called_once_with(
            article_id="recipe-1",
            user_confirmed=True,
            confirmation_text="Potvrzuji vyřazení z knihovny",
        )

    def test_library_read_state_action_updates_article_state(self) -> None:
        with patch("app.cockpit.set_article_read_state") as read_state_mock:
            read_state_mock.return_value = {"ok": True, "item": {"id": "article-1", "read_state": "to_read"}}

            result = library_read_state_action(
                {
                    "article_id": "article-1",
                    "read_state": "to_read",
                    "note": "Vrátit se k tomu.",
                }
            )

        self.assertTrue(result["ok"])
        read_state_mock.assert_called_once_with(
            article_id="article-1",
            read_state="to_read",
            note="Vrátit se k tomu.",
        )

    def test_lekarna_retire_preview_action_returns_confirmation_phrase(self) -> None:
        with patch("app.cockpit.format_domaci_lek_retire_preview") as preview_mock:
            preview_mock.return_value = "Vyrazeni leku - navrh zmeny"

            result = lekarna_retire_preview_action(
                {
                    "query": "HEPARIN AL",
                    "reason": "spotrebovano",
                }
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "preview")
        self.assertIn("Potvrzuji vyrazeni leku", result["confirmation_phrase"])
        self.assertIn("navrh zmeny", result["message"])
        preview_mock.assert_called_once_with(query="HEPARIN AL", reason="spotrebovano")

    def test_lekarna_retire_apply_action_requires_confirmation(self) -> None:
        with patch("app.cockpit.format_retire_domaci_lek") as apply_mock:
            apply_mock.side_effect = ValueError("Vyrazeni leku zapisuje do CSV a vyzaduje potvrzeni")

            result = lekarna_retire_apply_action(
                {
                    "query": "HEPARIN AL",
                    "reason": "spotrebovano",
                    "user_confirmed": False,
                    "confirmation_text": "",
                }
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "invalid_retire_request")
        self.assertIn("Potvrzuji vyrazeni leku", result["confirmation_phrase"])
        apply_mock.assert_called_once_with(
            query="HEPARIN AL",
            reason="spotrebovano",
            user_confirmed=False,
            confirmation_text="",
        )

    def test_lekarna_retire_apply_action_refreshes_and_publishes_web_bundle(self) -> None:
        with patch("app.cockpit.format_retire_domaci_lek", return_value="Vyrazeni leku - hotovo") as apply_mock, patch(
            "app.cockpit.refresh_and_publish_lekarna_web_bundle",
            return_value={
                "web_export_path": "/tmp/lekarna.json",
                "encrypted_bundle_path": "/tmp/lekarna.enc.json",
                "production_publish": {"ok": True, "status": "published", "message": "publikováno"},
                "warnings": [],
            },
        ) as publish_mock:
            result = lekarna_retire_apply_action(
                {
                    "query": "SERTIVAN",
                    "reason": "test",
                    "user_confirmed": True,
                    "confirmation_text": "Potvrzuji vyrazeni leku",
                }
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "apply")
        self.assertEqual(result["production_publish"]["status"], "published")
        apply_mock.assert_called_once_with(
            query="SERTIVAN",
            reason="test",
            user_confirmed=True,
            confirmation_text="Potvrzuji vyrazeni leku",
        )
        publish_mock.assert_called_once()

    def test_lekarna_search_action_returns_structured_rows(self) -> None:
        lek = SimpleNamespace(
            nazev="HEPARIN AL",
            ucinna_latka="heparin",
            sila="",
            forma="mast",
            kategorie="modriny",
            pouziti="modriny a otoky",
            mnozstvi="1 tuba",
            umisteni="horni police",
            expirace="2027-01",
            poznamky="",
            PIL_Short="",
            zdroj="Leky_v_Krabickach/heparin.jpg",
        )
        match = SimpleNamespace(lek=lek, score=12, reasons=("nazev: heparin",), warnings=("nutno_overit=ano",))
        with patch("app.cockpit.search_domaci_leky_records", return_value=[match]) as search_mock:
            result = lekarna_search_action("heparin", limit=5)

        self.assertTrue(result["ok"])
        self.assertEqual(result["items"][0]["nazev"], "HEPARIN AL")
        self.assertEqual(result["items"][0]["query"], "HEPARIN AL")
        self.assertEqual(result["items"][0]["warnings"], ["nutno_overit=ano"])
        search_mock.assert_called_once_with(query="heparin", limit=5)

    def test_lekarna_admin_page_contains_safe_controls(self) -> None:
        page = lekarna_admin_page_html()

        self.assertIn("/api/lekarna/search", page)
        self.assertIn("/api/lekarna/retire/preview", page)
        self.assertIn("/api/lekarna/retire/apply", page)
        self.assertIn("/api/lekarna/import/photos", page)
        self.assertIn("/api/lekarna/import/draft", page)
        self.assertIn("/api/lekarna/import/manifest/load", page)
        self.assertIn("/api/lekarna/import/manifest/save", page)
        self.assertIn("/api/lekarna/import/apply", page)
        self.assertIn("Náhled vyřazení", page)
        self.assertIn("Připravit návrh z fotek", page)
        self.assertIn("Znovu načíst kontrolu", page)
        self.assertIn("Kontrola návrhu se po přípravě načte automaticky", page)
        self.assertIn("Uložit opravy návrhu", page)
        self.assertIn("Zkusit PIL znovu", page)
        self.assertIn("Co je nutné doplnit", page)
        self.assertIn("field_help", page)
        self.assertIn("needs-review", page)
        self.assertIn("Přijmout návrh na sklad", page)
        self.assertIn("Obnovit seznam fotek", page)
        self.assertIn("Vlastní umístění", page)
        self.assertIn("Potvrzuji vyrazeni leku", page)
        self.assertIn("Potvrzuji OpenAI vision draft lekarna", page)
        self.assertIn("Potvrzuji import fotek lekarna", page)

    def test_lekarna_auto_import_draft_action_requires_openai_confirmation(self) -> None:
        result = lekarna_auto_import_draft_action(
            {
                "limit": 3,
                "ocr_backend": "openai",
                "confirmation_text": "",
            }
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "confirmation_required")
        self.assertIn("Potvrzuji OpenAI vision draft lekarna", result["confirmation_phrase"])

    def test_lekarna_import_photos_status_lists_recent_download_photos(self) -> None:
        fake_photo = SimpleNamespace(
            path=Path("/tmp/IMG_0001.JPG"),
            bytes_size=123,
            modified_at="2026-06-23T00:00:00+00:00",
        )
        with patch("app.cockpit.find_recent_download_photos", return_value=(fake_photo,)) as photos_mock:
            result = lekarna_import_photos_status(limit=8)

        self.assertTrue(result["ok"])
        self.assertEqual(result["photos"][0]["name"], "IMG_0001.JPG")
        self.assertEqual(result["photos"][0]["bytes"], 123)
        photos_mock.assert_called_once()

    def test_lekarna_auto_import_draft_action_runs_confirmed_backend(self) -> None:
        fake_result = SimpleNamespace(
            manifest_path=Path("/tmp/manifest.csv"),
            report_path=Path("/tmp/report.md"),
            photos=3,
            new_candidates=1,
            duplicate_existing=2,
            needs_review=0,
        )
        with patch("app.cockpit.build_auto_import_draft", return_value=fake_result) as draft_mock:
            result = lekarna_auto_import_draft_action(
                {
                    "limit": 3,
                    "ocr_backend": "openai",
                    "photo_names": ["IMG_9456.JPG"],
                    "confirmation_text": "Potvrzuji OpenAI vision draft lekarna",
                }
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["duplicate_existing"], 2)
        self.assertEqual(result["new_candidates"], 1)
        draft_mock.assert_called_once()
        self.assertEqual(draft_mock.call_args.kwargs["ocr_backend"], "openai")
        self.assertEqual(draft_mock.call_args.kwargs["photo_names"], ["IMG_9456.JPG"])

    def test_lekarna_import_manifest_load_and_save_review_fields(self) -> None:
        manifest_dir = Path("data/lekarna/photo_imports")
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "lekarna_auto_import_manifest_test_review.csv"
        fieldnames = [
            "include",
            "source_file",
            "new_file",
            "nazev",
            "ucinna_latka",
            "forma",
            "sila",
            "kategorie",
            "pouziti",
            "pro_koho",
            "nevhodne_pro_koho",
            "expirace",
            "mnozstvi",
            "umisteni",
            "overeno_z_letaku",
            "stav_obalu",
            "jistota_cteni",
            "nutno_overit",
            "zdroj",
            "poznamky",
            "PIL_Short",
            "PIL_Source",
            "PIL_Checked_Date",
            "PIL_Match_Status",
            "Search_Tags",
        ]
        row = {field: "" for field in fieldnames}
        row.update(
            {
                "include": "ano",
                "source_file": "IMG_9560.JPG",
                "new_file": "testovaci_roztok_100_ml.jpg",
                "nazev": "TESTOVACÍ ROZTOK",
                "sila": "100 ml",
                "mnozstvi": "",
                "zdroj": "Leky_v_Krabickach/",
                "PIL_Short": "fallback",
            }
        )
        try:
            with manifest_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(row)

            loaded = lekarna_import_manifest_load_action({"manifest_path": str(manifest_path.resolve())})
            self.assertTrue(loaded["ok"])
            self.assertEqual(loaded["rows"][0]["sila"], "100 ml")
            self.assertIn("PIL_Short", loaded["field_help"])
            self.assertTrue(any("mnozstvi" in warning for warning in loaded["warnings"]))
            self.assertIn("mnozstvi", loaded["row_issues"][0])

            loaded["rows"][0]["sila"] = "3%"
            loaded["rows"][0]["mnozstvi"] = "100 ml"
            loaded["rows"][0]["forma"] = "kožní roztok"
            saved = lekarna_import_manifest_save_action(
                {"manifest_path": str(manifest_path.resolve()), "effective_location": "Horní koupelna", "rows": loaded["rows"]}
            )

            self.assertTrue(saved["ok"])
            self.assertIn("warnings", saved)
            self.assertIn("row_issues", saved)
            reloaded = lekarna_import_manifest_load_action({"manifest_path": str(manifest_path.resolve())})
            self.assertEqual(reloaded["rows"][0]["sila"], "3%")
            self.assertEqual(reloaded["rows"][0]["mnozstvi"], "100 ml")
            self.assertEqual(reloaded["rows"][0]["forma"], "kožní roztok")
        finally:
            manifest_path.unlink(missing_ok=True)

    def test_lekarna_import_manifest_load_uses_latest_manifest_when_path_missing(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            project_root = Path(temp_dir)
            manifest_dir = project_root / "data" / "lekarna" / "photo_imports"
            manifest_dir.mkdir(parents=True)
            manifest_path = manifest_dir / "lekarna_auto_import_manifest_20260708_154907.csv"
            fieldnames = list(cockpit_module.LEKARNA_MANIFEST_FIELD_NAMES)
            row = {field: "" for field in fieldnames}
            row.update(
                {
                    "include": "ano",
                    "source_file": "IMG_9570.JPG",
                    "new_file": "img_9570.jpg",
                    "nazev": "Testovací položka",
                    "forma": "nezjisteno",
                    "sila": "nezjisteno",
                    "kategorie": "test",
                    "pouziti": "test",
                    "mnozstvi": "1",
                    "PIL_Short": "Testovací výtah pro kontrolu importu.",
                    "PIL_Source": "test",
                    "PIL_Match_Status": "overeno",
                    "Search_Tags": "test",
                }
            )
            with manifest_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(row)

            with patch.object(cockpit_module, "PROJECT_ROOT", project_root):
                loaded = lekarna_import_manifest_load_action({"manifest_path": ""})

            self.assertTrue(loaded["ok"])
            self.assertEqual(loaded["manifest_path"], str(manifest_path.resolve()))
            self.assertEqual(len(loaded["rows"]), 1)
            self.assertEqual(loaded["rows"][0]["include"], "ano")

    def test_lekarna_import_manifest_blocks_dlp_pil_without_downloaded_text(self) -> None:
        manifest_dir = Path("data/lekarna/photo_imports")
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "lekarna_auto_import_manifest_test_dlp_only.csv"
        fieldnames = list(cockpit_module.LEKARNA_MANIFEST_FIELD_NAMES)
        row = {field: "" for field in fieldnames}
        row.update(
            {
                "include": "ano",
                "source_file": "IMG_9570.JPG",
                "new_file": "sertivan.jpg",
                "nazev": "SERTIVAN",
                "forma": "TBL FLM",
                "sila": "50MG",
                "kategorie": "ANTIDEPRESIVA",
                "pouziti": "SUKL DLP/ATC: ANTIDEPRESIVA / SERTRALIN",
                "mnozstvi": "30",
                "PIL_Short": "Registrovany lecivy pripravek SERTIVAN. Ucinna latka: SERTRALIN.",
                "PIL_Source": (
                    "SUKL DLP 2026-07-01; kod 0162868; SERTIVAN; "
                    "PIL PI229834.pdf (20.01.2026)"
                ),
                "PIL_Match_Status": "overeno_z_dlp",
                "Search_Tags": "SERTIVAN, SERTRALIN",
            }
        )
        try:
            with manifest_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(row)

            loaded = lekarna_import_manifest_load_action({"manifest_path": str(manifest_path.resolve())})

            self.assertTrue(loaded["ok"])
            self.assertTrue(any("příbalový leták" in warning for warning in loaded["warnings"]))
            self.assertIn("PIL_Match_Status", loaded["row_issues"][0])
        finally:
            manifest_path.unlink(missing_ok=True)

    def test_lekarna_import_manifest_retry_pil_updates_review_row(self) -> None:
        manifest_dir = Path("data/lekarna/photo_imports")
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "lekarna_auto_import_manifest_test_retry_pil.csv"
        fieldnames = list(cockpit_module.LEKARNA_MANIFEST_FIELD_NAMES)
        row = {field: "" for field in fieldnames}
        row.update(
            {
                "include": "ano",
                "source_file": "IMG_9570.JPG",
                "new_file": "sertivan.jpg",
                "nazev": "SERTIVAN",
                "forma": "TBL FLM",
                "sila": "50MG",
                "kategorie": "ANTIDEPRESIVA",
                "pouziti": "SUKL DLP/ATC: ANTIDEPRESIVA / SERTRALIN",
                "mnozstvi": "30",
                "PIL_Short": "Registrovany lecivy pripravek SERTIVAN. Ucinna latka: SERTRALIN.",
                "PIL_Source": "SUKL DLP 2026-07-01; kod 0162868; SERTIVAN; PIL PI229834.pdf (20.01.2026)",
                "PIL_Match_Status": "overeno_z_dlp",
                "Search_Tags": "SERTIVAN, SERTRALIN",
            }
        )
        fake_document = SimpleNamespace(
            source_path=Path("PI229834.pdf"),
            member_name="PI229834.pdf",
            source_kind="cached-document",
            extraction_method="text",
            text=(
                "1. Co je přípravek SERTIVAN a k čemu se používá. "
                "Sertivan se používá k léčbě deprese a úzkostných poruch. "
                "2. Čemu musíte věnovat pozornost. Neužívejte při alergii na sertralin."
            ),
        )
        try:
            with manifest_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(row)

            with patch("app.cockpit.resolve_sukl_pil_document", return_value=fake_document):
                result = lekarna_import_manifest_retry_pil_action(
                    {"manifest_path": str(manifest_path.resolve()), "effective_location": "Horní koupelna"}
                )

            self.assertTrue(result["ok"])
            self.assertEqual(result["changed"], 1)
            self.assertFalse(result["warnings"])
            self.assertEqual(result["rows"][0]["PIL_Match_Status"], "overeno")
            self.assertEqual(result["rows"][0]["overeno_z_letaku"], "ano")
            self.assertIn("deprese", result["rows"][0]["PIL_Short"])
        finally:
            manifest_path.unlink(missing_ok=True)

    def test_lekarna_auto_import_apply_action_requires_confirmation(self) -> None:
        result = lekarna_auto_import_apply_action(
            {
                "manifest_path": "/tmp/manifest.csv",
                "confirmation_text": "",
            }
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "confirmation_required")
        self.assertIn("Potvrzuji import fotek lekarna", result["confirmation_phrase"])

    def test_lekarna_auto_import_apply_action_blocks_weak_manifest(self) -> None:
        manifest_dir = Path("data/lekarna/photo_imports")
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "lekarna_auto_import_manifest_test_weak.csv"
        fieldnames = [
            "include",
            "source_file",
            "new_file",
            "nazev",
            "ucinna_latka",
            "forma",
            "sila",
            "kategorie",
            "pouziti",
            "pro_koho",
            "nevhodne_pro_koho",
            "expirace",
            "mnozstvi",
            "umisteni",
            "overeno_z_letaku",
            "stav_obalu",
            "jistota_cteni",
            "nutno_overit",
            "zdroj",
            "poznamky",
            "PIL_Short",
            "PIL_Source",
            "PIL_Checked_Date",
            "PIL_Match_Status",
            "Search_Tags",
        ]
        row = {field: "" for field in fieldnames}
        row.update(
            {
                "include": "ano",
                "source_file": "IMG_9560.JPG",
                "new_file": "testovaci_roztok_100_ml.jpg",
                "nazev": "TESTOVACÍ ROZTOK",
                "sila": "100 ml",
                "kategorie": "nezarazeno",
                "PIL_Short": "Automaticky inventarni zaznam z fotografie.",
                "PIL_Source": "Fotografie obalu; PIL zatim nedohledan.",
                "PIL_Match_Status": "ceka_na_pil_overeni",
            }
        )
        try:
            with manifest_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(row)

            with patch("app.cockpit.apply_auto_import_manifest_from_downloads") as apply_mock:
                result = lekarna_auto_import_apply_action(
                    {
                        "manifest_path": str(manifest_path.resolve()),
                        "location": "Horní koupelna",
                        "confirmation_text": "Potvrzuji import fotek lekarna",
                    }
                )

            self.assertFalse(result["ok"])
            self.assertEqual(result["error"], "manifest_needs_review")
            self.assertTrue(any("PIL_Short" in warning for warning in result["warnings"]))
            apply_mock.assert_not_called()
        finally:
            manifest_path.unlink(missing_ok=True)

    def test_lekarna_auto_import_apply_action_runs_confirmed_apply(self) -> None:
        fake_result = SimpleNamespace(
            backup_path=Path("/tmp/backup.csv"),
            report_path=Path("/tmp/report.md"),
            copied_count=1,
            renamed_count=1,
            appended_count=1,
            web_export_path=Path("/tmp/lekarna.json"),
            encrypted_bundle_path=Path("/tmp/lekarna.enc.json"),
            warnings=(),
        )
        with patch("app.cockpit._lekarna_manifest_quality_warnings", return_value=[]), patch(
            "app.cockpit.apply_auto_import_manifest_from_downloads", return_value=fake_result
        ) as apply_mock, patch(
            "app.cockpit.publish_lekarna_encrypted_bundle",
            return_value={"ok": True, "status": "published", "message": "publikováno"},
        ) as publish_mock:
            result = lekarna_auto_import_apply_action(
                {
                    "manifest_path": "/tmp/manifest.csv",
                    "location": "Pils Jana",
                    "confirmation_text": "Potvrzuji import fotek lekarna",
                }
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["appended"], 1)
        apply_mock.assert_called_once()
        self.assertEqual(apply_mock.call_args.kwargs["manifest_path"], Path("/tmp/manifest.csv"))
        self.assertEqual(apply_mock.call_args.kwargs["location"], "Pils Jana")
        publish_mock.assert_called_once_with(Path("/tmp/lekarna.enc.json"))
        self.assertEqual(result["production_publish"]["status"], "published")

    def test_publish_lekarna_encrypted_bundle_commits_only_expected_bundle(self) -> None:
        calls: list[list[str]] = []

        def fake_runner(command, **kwargs):
            calls.append(command)
            git_args = command[3:]
            if git_args[:3] == ["diff", "--quiet", "--"]:
                return subprocess.CompletedProcess(command, 1, "", "")
            if git_args[:4] == ["diff", "--cached", "--quiet", "--"]:
                return subprocess.CompletedProcess(command, 0, "", "")
            if git_args[:2] == ["add", "--"]:
                return subprocess.CompletedProcess(command, 0, "", "")
            if git_args[:2] == ["commit", "--only"]:
                return subprocess.CompletedProcess(command, 0, "[main abc123] Update Lekarna encrypted data bundle\n", "")
            if git_args == ["push"]:
                return subprocess.CompletedProcess(command, 0, "", "")
            raise AssertionError(f"unexpected git command: {git_args}")

        with tempfile.TemporaryDirectory() as tmp_dir, patch.object(cockpit_module, "GIT_ROOT", Path(tmp_dir)):
            expected = Path(tmp_dir) / "docs" / "lekarna" / "encrypted-data" / "lekarna.enc.json"
            expected.parent.mkdir(parents=True, exist_ok=True)
            expected.write_text("test-bundle", encoding="utf-8")
            result = publish_lekarna_encrypted_bundle(expected, runner=fake_runner)

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "published")
        commit_command = next(command for command in calls if "commit" in command)
        self.assertIn("--only", commit_command)
        self.assertEqual(commit_command[-1], "docs/lekarna/encrypted-data/lekarna.enc.json")

    def test_publish_lekarna_encrypted_bundle_rejects_unexpected_path(self) -> None:
        result = publish_lekarna_encrypted_bundle(Path("/tmp/other.enc.json"), runner=lambda *_args, **_kwargs: None)

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "unexpected_path")

    def test_cockpit_html_contains_library_attachment_view(self) -> None:
        self.assertIn("libraryReaderAttachments", COCKPIT_HTML)
        self.assertIn("/api/library/attachment", COCKPIT_HTML)
        self.assertIn("/api/library/attachment/add", COCKPIT_HTML)
        self.assertIn("/api/library/delete", COCKPIT_HTML)
        self.assertIn("/api/library/read-state", COCKPIT_HTML)
        self.assertIn("/api/library/export/prepare", COCKPIT_HTML)
        self.assertIn("/api/library/export/send", COCKPIT_HTML)
        self.assertIn("libraryOpenSourceBtn", COCKPIT_HTML)
        self.assertIn("Otevřít na webu", COCKPIT_HTML)
        self.assertIn("openSelectedLibrarySource", COCKPIT_HTML)
        self.assertIn("librarySourceUrl(item)", COCKPIT_HTML)
        self.assertIn("libraryDeleteBtn", COCKPIT_HTML)
        self.assertIn("libraryToReadBtn", COCKPIT_HTML)
        self.assertIn("libraryDoneBtn", COCKPIT_HTML)
        self.assertIn("libraryClearReadStateBtn", COCKPIT_HTML)
        self.assertIn("libraryExportPrepareBtn", COCKPIT_HTML)
        self.assertIn("libraryExportSendBtn", COCKPIT_HTML)
        self.assertIn("libraryExportStatus", COCKPIT_HTML)
        self.assertIn("Potvrzuji vyřazení z knihovny", COCKPIT_HTML)
        self.assertIn("libraryAttachmentFileInput", COCKPIT_HTML)
        self.assertIn("libraryEditBtn", COCKPIT_HTML)
        self.assertIn("Uložit úpravy", COCKPIT_HTML)
        self.assertIn("/api/library/update", COCKPIT_HTML)
        self.assertIn("/api/library/attachment/update", COCKPIT_HTML)
        self.assertIn("/api/library/attachment/remove", COCKPIT_HTML)
        self.assertIn("Upravit popisek", COCKPIT_HTML)
        self.assertIn("Odebrat přílohu", COCKPIT_HTML)
        self.assertIn("Potvrzuji odebrání přílohy", COCKPIT_HTML)
        self.assertIn("&full=1", COCKPIT_HTML)
        self.assertIn("attachment_count", COCKPIT_HTML)
        self.assertIn("Otevřít přílohu", COCKPIT_HTML)
        self.assertIn("libraryAttachmentViewerModal", COCKPIT_HTML)
        self.assertIn("libraryAttachmentViewerImage", COCKPIT_HTML)
        self.assertIn("Zpět do Knihovny", COCKPIT_HTML)
        self.assertIn("function openLibraryAttachmentViewer(imageUrl, label, returnFocus)", COCKPIT_HTML)
        self.assertIn('const readable = document.createElement(isImage ? "button" : "a");', COCKPIT_HTML)
        self.assertIn('preview.addEventListener("click", () => openLibraryAttachmentViewer', COCKPIT_HTML)
        self.assertIn('readable.addEventListener("click", () => openLibraryAttachmentViewer', COCKPIT_HTML)
        self.assertIn("function libraryAttachmentDisplayLabel(attachment, category)", COCKPIT_HTML)
        self.assertIn('category === "travel_places" && (!label || label === "Ručně psaný recept")', COCKPIT_HTML)
        self.assertIn('return "Ilustrační foto";', COCKPIT_HTML)
        self.assertIn('currentLibrarySelectedItem && currentLibrarySelectedItem.category', COCKPIT_HTML)
        self.assertIn('itemCategory === "travel_places" ? "Ilustrační foto"', COCKPIT_HTML)
        self.assertIn('itemCategory === "recipes" ? "Ručně psaný recept" : "Doprovodná fotografie"', COCKPIT_HTML)
        self.assertIn("item.category || currentLibraryCategory", COCKPIT_HTML)
        self.assertIn('value="ai_tools"', COCKPIT_HTML)
        self.assertIn('data-library-category="ai_tools"', COCKPIT_HTML)
        self.assertIn("Samantha / AI nástroje", COCKPIT_HTML)
        self.assertIn('value="health_info"', COCKPIT_HTML)
        self.assertIn('data-library-category="health_info"', COCKPIT_HTML)
        self.assertIn("Zdravotní informace", COCKPIT_HTML)
        self.assertIn('"science", "health_info", "ai_tools"', COCKPIT_HTML)
        self.assertIn('value="travel_places"', COCKPIT_HTML)
        self.assertIn('data-library-category="travel_places"', COCKPIT_HTML)
        self.assertIn("Cestování / místa", COCKPIT_HTML)
        self.assertIn('data-library-category="books"', COCKPIT_HTML)
        self.assertIn('value="books"', COCKPIT_HTML)
        self.assertIn("Přidat knihu", COCKPIT_HTML)
        self.assertIn("Přehled knih", COCKPIT_HTML)
        self.assertIn('data-library-book-view="all"', COCKPIT_HTML)
        self.assertIn('data-library-book-view="category"', COCKPIT_HTML)
        self.assertIn('data-library-book-view="author"', COCKPIT_HTML)
        self.assertIn('data-library-book-view="location"', COCKPIT_HTML)
        self.assertIn("libraryBookCategoryFilter", COCKPIT_HTML)
        self.assertIn("libraryBookAuthorFilter", COCKPIT_HTML)
        self.assertIn("libraryBookLocationFilter", COCKPIT_HTML)
        self.assertIn("libraryBookClearFiltersBtn", COCKPIT_HTML)
        self.assertIn('/api/library/books/overview', COCKPIT_HTML)
        self.assertIn("function renderLibraryBookOverviewItems()", COCKPIT_HTML)
        self.assertIn("function renderLibraryBookGrouped(items, view)", COCKPIT_HTML)
        self.assertIn("function createLibraryItemRow(item)", COCKPIT_HTML)
        self.assertIn(': libraryBookCategories(item);', COCKPIT_HTML)
        self.assertIn('libraryBookOverviewCount.textContent', COCKPIT_HTML)
        self.assertIn('class="secondary hidden" id="libraryAddBookBtn"', COCKPIT_HTML)
        self.assertIn("function syncLibraryBookAddAvailability(category, readState)", COCKPIT_HTML)
        self.assertIn('const available = category === "books" && !readState;', COCKPIT_HTML)
        self.assertIn('libraryAddBookBtn.classList.toggle("hidden", !available);', COCKPIT_HTML)
        self.assertIn("libraryAddBookBtn.disabled = !available;", COCKPIT_HTML)
        self.assertIn(
            "syncLibraryBookAddAvailability(currentLibraryCategory, currentLibraryReadStateFilter);",
            COCKPIT_HTML,
        )
        self.assertIn("libraryBookAuthorInput", COCKPIT_HTML)
        self.assertIn("libraryBookLocationInput", COCKPIT_HTML)
        self.assertIn('libraryBookLocationInput"', COCKPIT_HTML)
        self.assertIn('<option value="obývák">obývák</option>', COCKPIT_HTML)
        self.assertIn('<option value="jídelna">jídelna</option>', COCKPIT_HTML)
        self.assertIn('<option value="půda">půda</option>', COCKPIT_HTML)
        self.assertIn("libraryBookCategoryChoices", COCKPIT_HTML)
        self.assertIn("libraryBookAddLocationBtn", COCKPIT_HTML)
        self.assertIn("libraryBookAddCategoryBtn", COCKPIT_HTML)
        self.assertIn("Kategorie knihy (volitelné)", COCKPIT_HTML)
        self.assertIn('/api/library/book/options', COCKPIT_HTML)
        self.assertIn("function loadLibraryBookOptions()", COCKPIT_HTML)
        self.assertIn("function addLibraryBookOption(kind)", COCKPIT_HTML)
        self.assertIn('tags: selectedLibraryBookCategories(libraryBookCategoryChoices)', COCKPIT_HTML)
        self.assertIn("libraryBookIsbnInput", COCKPIT_HTML)
        self.assertIn('libraryBookIsbnPhotoInput" type="file" accept="image/*" capture="environment"', COCKPIT_HTML)
        self.assertIn("libraryBookIsbnPhotoReadBtn", COCKPIT_HTML)
        self.assertIn("libraryBookIsbnPhotoStatus", COCKPIT_HTML)
        self.assertIn("Načíst ISBN z fotografie", COCKPIT_HTML)
        self.assertIn("function readLibraryBookIsbnFromPhoto()", COCKPIT_HTML)
        self.assertIn('postJson("/api/library/book/isbn-photo", {image_data_url: imageDataUrl})', COCKPIT_HTML)
        self.assertIn("libraryBookIsbnPhotoInput.value = \"\";", COCKPIT_HTML)
        self.assertIn("libraryBookIsbnLookupBtn", COCKPIT_HTML)
        self.assertIn("libraryBookIsbnLookupStatus", COCKPIT_HTML)
        self.assertIn("libraryBookIsbnSourceLink", COCKPIT_HTML)
        self.assertIn("Dohledat podle ISBN", COCKPIT_HTML)
        self.assertIn("ISBN z knihy (nepovinné)", COCKPIT_HTML)
        self.assertIn("ISBN není nutné k uložení", COCKPIT_HTML)
        isbn_photo_start = COCKPIT_HTML.index("async function readLibraryBookIsbnFromPhoto()")
        isbn_photo_end = COCKPIT_HTML.index("async function lookupLibraryBookIsbn()", isbn_photo_start)
        self.assertNotIn("/api/library/attachment/add", COCKPIT_HTML[isbn_photo_start:isbn_photo_end])
        self.assertIn("/api/library/book/isbn-lookup", COCKPIT_HTML)
        self.assertIn("function lookupLibraryBookIsbn()", COCKPIT_HTML)
        self.assertIn('postJson("/api/library/book/isbn-lookup", { isbn })', COCKPIT_HTML)
        self.assertIn("Výsledek se neuloží automaticky", COCKPIT_HTML)
        self.assertIn('sourceUrl.startsWith("https://openlibrary.org/isbn/")', COCKPIT_HTML)
        self.assertIn("libraryEditBookIsbnInput", COCKPIT_HTML)
        self.assertIn('libraryEditBookIsbnPhotoInput" type="file" accept="image/*" capture="environment"', COCKPIT_HTML)
        self.assertIn("libraryEditBookIsbnPhotoReadBtn", COCKPIT_HTML)
        self.assertIn("libraryEditBookIsbnPhotoStatus", COCKPIT_HTML)
        self.assertIn("libraryEditBookIsbnLookupBtn", COCKPIT_HTML)
        self.assertIn("libraryEditBookIsbnLookupStatus", COCKPIT_HTML)
        self.assertIn("libraryEditBookIsbnSourceLink", COCKPIT_HTML)
        self.assertIn("function readLibraryEditBookIsbnFromPhoto()", COCKPIT_HTML)
        self.assertIn("function lookupLibraryEditBookIsbn()", COCKPIT_HTML)
        self.assertIn("onUpdated: markLibraryEditorDirty", COCKPIT_HTML)
        self.assertIn("Karta se změní až po stisku Uložit úpravy", COCKPIT_HTML)
        edit_isbn_photo_start = COCKPIT_HTML.index("async function readLibraryEditBookIsbnFromPhoto()")
        edit_isbn_photo_end = COCKPIT_HTML.index("async function lookupLibraryBookIsbnInto", edit_isbn_photo_start)
        self.assertNotIn("/api/library/attachment/add", COCKPIT_HTML[edit_isbn_photo_start:edit_isbn_photo_end])
        self.assertIn("libraryBookCoverInput", COCKPIT_HTML)
        self.assertIn('libraryBookCoverInput" type="file" accept="image/*"', COCKPIT_HTML)
        self.assertIn("libraryBookCoverPreview", COCKPIT_HTML)
        self.assertIn("libraryBookCoverDraftBtn", COCKPIT_HTML)
        self.assertIn("/api/library/book/cover-draft", COCKPIT_HTML)
        self.assertIn("/api/library/book/cover-prepare", COCKPIT_HTML)
        self.assertIn("function recognizeLibraryBookCover()", COCKPIT_HTML)
        self.assertIn("Zmenšená obálka se uloží až s knihou", COCKPIT_HTML)
        self.assertIn('image_data_url: preparedCover.image_data_url', COCKPIT_HTML)
        self.assertIn('filename: preparedCover.filename || "obalka-knihy.jpg"', COCKPIT_HTML)
        self.assertNotIn("const imageDataUrl = await blobToDataUrl(cover.file);", COCKPIT_HTML)
        self.assertIn('role: "book_cover"', COCKPIT_HTML)
        self.assertIn("Přidej ji v části Přílohy", COCKPIT_HTML)
        self.assertIn('libraryBookOcrPhotoInput" type="file" accept="image/*" capture="environment"', COCKPIT_HTML)
        self.assertIn("libraryBookOcrReadBtn", COCKPIT_HTML)
        self.assertIn("libraryBookOcrTextPreview", COCKPIT_HTML)
        self.assertIn("Nahradit podklady", COCKPIT_HTML)
        self.assertIn("Přidat k podkladům", COCKPIT_HTML)
        self.assertIn("function readLibraryBookTextFromPhotos()", COCKPIT_HTML)
        self.assertIn("function applyLibraryBookOcrText(mode)", COCKPIT_HTML)
        self.assertIn('/api/library/book/text-photo-prepare', COCKPIT_HTML)
        self.assertIn('/api/library/book/text-ocr', COCKPIT_HTML)
        self.assertIn("libraryBookOcrFiles.length >= 3", COCKPIT_HTML)
        self.assertIn("Dočasné fotografie byly uvolněny", COCKPIT_HTML)
        self.assertIn("if (!available) clearLibraryBookOcrPhotos();", COCKPIT_HTML)
        self.assertIn('setLibraryAddMode("");\n      clearLibraryBookOcrPhotos();\n      libraryModal.classList.add("hidden");', COCKPIT_HTML)
        ocr_start = COCKPIT_HTML.index("async function readLibraryBookTextFromPhotos()")
        ocr_end = COCKPIT_HTML.index("function applyLibraryBookOcrText(mode)", ocr_start)
        self.assertNotIn("/api/library/attachment/add", COCKPIT_HTML[ocr_start:ocr_end])
        self.assertIn("libraryBookSummaryInput", COCKPIT_HTML)
        self.assertIn("libraryBookSourceInput", COCKPIT_HTML)
        self.assertIn("libraryBookSummaryDraftBtn", COCKPIT_HTML)
        self.assertLess(COCKPIT_HTML.index('id="libraryBookSourceInput"'), COCKPIT_HTML.index('id="libraryBookSummaryDraftBtn"'))
        self.assertLess(COCKPIT_HTML.index('id="libraryBookSummaryDraftBtn"'), COCKPIT_HTML.index('id="libraryBookSummaryInput"'))
        self.assertLess(COCKPIT_HTML.index('id="libraryBookSummaryInput"'), COCKPIT_HTML.index('id="libraryBookLocationInput"'))
        self.assertLess(COCKPIT_HTML.index('id="libraryBookLocationInput"'), COCKPIT_HTML.index('id="libraryBookIsbnInput"'))
        self.assertLess(COCKPIT_HTML.index('id="libraryBookIsbnInput"'), COCKPIT_HTML.index('id="libraryBookSaveBtn"'))
        self.assertIn("library-book-summary-block", COCKPIT_HTML)
        self.assertIn("library-book-save-actions", COCKPIT_HTML)
        self.assertIn("Umístění a kategorie", COCKPIT_HTML)
        self.assertIn("Podklady pro návrh obsahu (neukládají se)", COCKPIT_HTML)
        self.assertIn("/api/library/book/summary-draft", COCKPIT_HTML)
        self.assertIn("function generateLibraryBookSummary()", COCKPIT_HTML)
        self.assertIn("Kniha se tím neukládá", COCKPIT_HTML)
        self.assertIn("libraryEditBookAuthorInput", COCKPIT_HTML)
        self.assertIn("libraryEditBookLocationInput", COCKPIT_HTML)
        self.assertIn("libraryEditBookCategoryChoices", COCKPIT_HTML)
        self.assertIn('libraryEditTagsInput.closest(".library-field").classList.toggle("hidden", isBook);', COCKPIT_HTML)
        self.assertIn('/api/library/book', COCKPIT_HTML)
        self.assertIn('item.category === "books" && item.book_author', COCKPIT_HTML)
        self.assertIn('item.category === "books" && item.book_location', COCKPIT_HTML)
        self.assertIn('data-library-read-state="to_read"', COCKPIT_HTML)
        self.assertIn("K přečtení", COCKPIT_HTML)
        self.assertIn("library-tab read-queue", COCKPIT_HTML)
        self.assertIn("library-read-badge", COCKPIT_HTML)
        self.assertIn('row.classList.toggle("to-read"', COCKPIT_HTML)
        self.assertIn("box-shadow: inset 3px 0 0 #f59e0b", COCKPIT_HTML)

    def test_library_editor_guards_unsaved_changes_and_preserves_them_during_attachment_updates(self) -> None:
        self.assertIn("let libraryEditorDirty = false;", COCKPIT_HTML)
        self.assertIn("function markLibraryEditorDirty()", COCKPIT_HTML)
        self.assertIn("function setLibraryEditorFieldsDisabled(disabled)", COCKPIT_HTML)
        self.assertIn("function confirmLibraryEditorDiscard()", COCKPIT_HTML)
        self.assertIn("Máš neuložené úpravy článku. Chceš je zahodit?", COCKPIT_HTML)
        self.assertIn('window.addEventListener("beforeunload"', COCKPIT_HTML)
        self.assertIn('libraryEditCancelBtn.addEventListener("click", () => closeLibraryEditor());', COCKPIT_HTML)
        self.assertIn("function refreshLibraryItemAfterAttachment(item, articleId)", COCKPIT_HTML)
        self.assertEqual(
            COCKPIT_HTML.count("refreshLibraryItemAfterAttachment(data.item || {}, articleId);"),
            3,
        )
        self.assertNotIn("await loadLibraryCategory(item.category || currentLibraryCategory", COCKPIT_HTML)
        self.assertNotIn("await loadLibraryCategory(currentLibraryCategory);\n        await loadLibraryItem(articleId);", COCKPIT_HTML)

    def test_library_layout_prioritizes_browsing_and_unifies_attachment_management(self) -> None:
        self.assertIn('id="libraryArchivePanel" class="library-add-panel hidden"', COCKPIT_HTML)
        self.assertIn('id="libraryTextPanel" class="library-add-panel hidden"', COCKPIT_HTML)
        self.assertIn('aria-controls="libraryArchivePanel"', COCKPIT_HTML)
        self.assertIn('aria-controls="libraryTextPanel"', COCKPIT_HTML)
        self.assertIn("function setLibraryAddMode(mode)", COCKPIT_HTML)
        self.assertIn("function toggleLibraryAddMode(mode)", COCKPIT_HTML)
        self.assertLess(COCKPIT_HTML.index('class="library-tabs"'), COCKPIT_HTML.index('id="libraryArchivePanel"'))
        for label in ("Článek", "Čtení", "Export", "Správa"):
            self.assertIn(f'<span class="library-action-group-label">{label}</span>', COCKPIT_HTML)

        edit_start = COCKPIT_HTML.index('id="libraryEditPanel"')
        attachment_start = COCKPIT_HTML.index('id="libraryAttachmentSection"')
        reader_start = COCKPIT_HTML.index('id="libraryReaderText"')
        self.assertLess(edit_start, attachment_start)
        self.assertLess(attachment_start, reader_start)
        self.assertNotIn('id="libraryAttachmentFileInput"', COCKPIT_HTML[edit_start:attachment_start])
        self.assertIn('id="libraryAttachmentFileInput"', COCKPIT_HTML[attachment_start:reader_start])
        self.assertIn('id="libraryReaderAttachments"', COCKPIT_HTML[attachment_start:reader_start])
        self.assertIn('libraryAttachmentSection.classList.toggle("hidden", !hasArticle);', COCKPIT_HTML)

    def test_library_fields_have_visible_labels_and_distinct_source_note(self) -> None:
        library_start = COCKPIT_HTML.index('id="libraryModal"')
        library_end = COCKPIT_HTML.index('id="familyCalendarModal"')
        library_html = COCKPIT_HTML[library_start:library_end]
        field_count = sum(library_html.count(tag) for tag in ("<input", "<select", "<textarea"))
        self.assertEqual(library_html.count('<label class="library-field">'), field_count)
        self.assertIn("Když zůstane prázdný, použije se první řádek textu.", library_html)
        self.assertIn('id="libraryTextSourceNoteInput"', library_html)
        self.assertIn("Tagy přidané ke kartě (volitelné)", library_html)
        self.assertIn("Přidají se celé kartě, ne pouze této příloze.", library_html)
        self.assertIn("const sourceNote = libraryTextSourceNoteInput.value.trim();", COCKPIT_HTML)
        self.assertIn("source_note: sourceNote,", COCKPIT_HTML)
        self.assertNotIn("source_note: sourceLabel,", COCKPIT_HTML)
        self.assertIn("function syncLibraryCreateCategories(category)", COCKPIT_HTML)
        self.assertIn("syncLibraryCreateCategories(currentLibraryCategory);", COCKPIT_HTML)
        self.assertGreaterEqual(library_html.count('<option value="recipes" selected>Recepty</option>'), 2)

    def test_library_exposes_global_search_metadata_and_full_text_loading(self) -> None:
        self.assertIn('data-library-category="all">Všechny</button>', COCKPIT_HTML)
        self.assertIn("function libraryItemDetailMeta(item)", COCKPIT_HTML)
        self.assertIn('item && item.category === "books" ? "Kategorie" : "Tagy"', COCKPIT_HTML)
        self.assertIn('lines.push(`Poznámka ke zdroji: ${sourceNote}`);', COCKPIT_HTML)
        self.assertIn('id="libraryFullTextNotice" class="library-full-text-notice hidden"', COCKPIT_HTML)
        self.assertIn('id="libraryShowFullTextBtn"', COCKPIT_HTML)
        self.assertIn("function loadFullLibraryItemText()", COCKPIT_HTML)
        self.assertIn("setLibraryFullTextNotice(Boolean(data.truncated));", COCKPIT_HTML)
        self.assertIn('libraryShowFullTextBtn.addEventListener("click", loadFullLibraryItemText);', COCKPIT_HTML)

    def test_library_finishes_mobile_reader_and_attachment_metadata(self) -> None:
        self.assertIn('id="libraryReader" class="library-reader"', COCKPIT_HTML)
        self.assertIn('"libraryReader",', COCKPIT_HTML)
        self.assertIn("function scrollLibraryReaderIntoViewOnMobile()", COCKPIT_HTML)
        self.assertIn('window.matchMedia("(max-width: 900px)").matches', COCKPIT_HTML)
        self.assertIn('window.matchMedia("(prefers-reduced-motion: reduce)").matches', COCKPIT_HTML)
        self.assertIn('libraryReader.scrollIntoView({behavior: reduceMotion ? "auto" : "smooth", block: "start"});', COCKPIT_HTML)
        self.assertIn('loadLibraryItem(item.id || "", true)', COCKPIT_HTML)
        self.assertIn("function libraryAttachmentRoleLabel(role)", COCKPIT_HTML)
        self.assertIn('handwritten_recipe_scan: "Ručně psaný originál"', COCKPIT_HTML)
        self.assertIn('original_pdf: "Původní dokument"', COCKPIT_HTML)
        self.assertIn("function libraryAttachmentTypeLabel(attachment)", COCKPIT_HTML)
        self.assertIn('return "PDF";', COCKPIT_HTML)
        self.assertIn('return format ? `Obrázek ${format}` : "Obrázek";', COCKPIT_HTML)
        self.assertNotIn("if (attachment.role) metaParts.push(attachment.role);", COCKPIT_HTML)
        self.assertNotIn("if (attachment.mime_type) metaParts.push(attachment.mime_type);", COCKPIT_HTML)
        self.assertLess(COCKPIT_HTML.index('id="libraryAttachmentSection"'), COCKPIT_HTML.index('id="libraryReaderText"'))

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

    def test_stored_documents_review_status_skips_already_reviewed_scandocu_items(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "stale-reviewed-doc",
                        "title": "Už zrevidovaný",
                        "domain": "energy",
                        "document_type": "contract",
                        "stored_path": "data/private/documents/vault/energy/stale-reviewed-doc/doc.pdf",
                        "reading_status": "needs_review",
                    },
                    {
                        "document_id": "pending-doc",
                        "title": "Ještě čeká",
                        "domain": "energy",
                        "document_type": "contract",
                        "stored_path": "data/private/documents/vault/energy/pending-doc/doc.pdf",
                        "reading_status": "needs_review",
                    },
                ],
            )
            self.write_jsonl(
                index / "scandocu_actions.jsonl",
                [{"action": "reviewed", "document_id": "stale-reviewed-doc"}],
            )

            status = stored_documents_review_status(vault_dir=vault)

        self.assertEqual(status["pending_count"], 1)
        self.assertEqual(status["next_items"][0]["document_id"], "pending-doc")
        self.assertNotIn("stale-reviewed-doc", json.dumps(status["next_items"], ensure_ascii=False))

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

    def test_document_classification_status_labels_tax_return_type(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "tax-return",
                        "title": "Daňové přiznání",
                        "domain": "tax",
                        "document_type": "danove-priznani",
                        "counterparty": "Finanční úřad",
                        "related_asset": "",
                    },
                ],
            )

            result = document_classification_status(vault_dir=vault)

        self.assertIn("daně / daňové přiznání", result["items"][0]["classification_summary"])

    def test_document_classification_status_labels_insurance_attachment_types(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "assist-card",
                        "title": "Asistenční karta",
                        "domain": "insurance",
                        "document_type": "insurance_assistance_card",
                        "counterparty": "Pojišťovna",
                        "related_asset": "cestovní pojištění",
                    },
                    {
                        "document_id": "payment-confirmation",
                        "title": "Potvrzení platby",
                        "domain": "insurance",
                        "document_type": "insurance_payment_confirmation",
                        "counterparty": "Pojišťovna",
                        "related_asset": "cestovní pojištění",
                    },
                    {
                        "document_id": "green-card",
                        "title": "Zelená karta",
                        "domain": "insurance",
                        "document_type": "green_card",
                        "counterparty": "Pojišťovna",
                        "related_asset": "auto",
                    },
                ],
            )

            result = document_classification_status(vault_dir=vault)

        self.assertEqual(result["issue_count"], 0)
        labels = result["document_type_counts"]
        self.assertEqual(labels["asistenční karta"], 1)
        self.assertEqual(labels["potvrzení o zaplacení pojistného"], 1)
        self.assertEqual(labels["zelená karta / potvrzení pojištění"], 1)

    def test_document_classification_status_treats_email_attachment_type_as_incomplete(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "cez-doc",
                        "title": "ČEZ smlouva",
                        "domain": "energy",
                        "document_type": "email-attachment-pdf",
                        "counterparty": "ČEZ",
                        "related_asset": "elektřina",
                    },
                ],
            )

            result = document_classification_status(vault_dir=vault)

        self.assertEqual(result["active_documents"], 1)
        self.assertEqual(result["complete_count"], 0)
        self.assertEqual(result["issue_count"], 1)
        self.assertEqual(result["items"][0]["missing_fields"], ["document_type"])

    def test_document_classification_status_includes_accept_suggestion(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "tmobile-doc",
                        "title": "E-mail příloha Vyuctovani_40580553_2606.pdf",
                        "domain": "other",
                        "document_type": "email-attachment-pdf",
                        "counterparty": "T-Mobile Elektronické vyúčtování <[e-mail redigovan]>",
                        "related_asset": "",
                        "stored_path": "data/private/documents/vault/other/tmobile-doc/Vyuctovani_40580553_2606.pdf",
                    }
                ],
            )
            self.write_jsonl(
                index / "text_index.jsonl",
                [
                    {
                        "document_id": "tmobile-doc",
                        "text": "T-Mobile Elektronické vyúčtování. Vyúčtování služeb za telefon a mobilní služby.",
                    }
                ],
            )

            result = document_classification_status(vault_dir=vault)

        suggestion = result["items"][0]["metadata_suggestion"]
        self.assertTrue(suggestion["can_accept"])
        self.assertEqual(suggestion["metadata"]["domain"], "telecom")
        self.assertEqual(suggestion["metadata"]["document_type"], "invoice")
        self.assertEqual(suggestion["metadata"]["related_asset"], "T-Mobile / mobilní služby")
        self.assertIn("Zkontrolovat automatický návrh", result["items"][0]["recommended_action"])

    def test_accept_document_classification_suggestion_recomputes_and_updates_metadata(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            index = vault / "index"
            document_dir = vault / "vault" / "other" / "tmobile-doc"
            index.mkdir(parents=True)
            document_dir.mkdir(parents=True)
            stored_pdf = document_dir / "Vyuctovani_40580553_2606.pdf"
            stored_pdf.write_bytes(b"%PDF-1.4\n")
            (document_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "document_id": "tmobile-doc",
                        "title": "E-mail příloha Vyuctovani_40580553_2606.pdf",
                        "domain": "other",
                        "document_type": "email-attachment-pdf",
                        "counterparty": "T-Mobile Elektronické vyúčtování <[e-mail redigovan]>",
                        "related_asset": "",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "tmobile-doc",
                        "title": "E-mail příloha Vyuctovani_40580553_2606.pdf",
                        "domain": "other",
                        "document_type": "email-attachment-pdf",
                        "counterparty": "T-Mobile Elektronické vyúčtování <[e-mail redigovan]>",
                        "related_asset": "",
                        "stored_path": str(stored_pdf),
                    }
                ],
            )
            self.write_jsonl(
                index / "text_index.jsonl",
                [
                    {
                        "document_id": "tmobile-doc",
                        "text": "T-Mobile Elektronické vyúčtování. Vyúčtování služeb za telefon a mobilní služby.",
                    }
                ],
            )
            document_ref = document_classification_status(vault_dir=vault)["items"][0]["document_ref"]

            result = accept_document_classification_suggestion_action(
                document_id=document_ref,
                confirmed=True,
                vault_dir=vault,
            )

            docs = self.read_jsonl(index / "documents_index.jsonl")

        self.assertTrue(result["ok"])
        self.assertEqual(result["missing_fields"], [])
        self.assertEqual(result["document_classification"]["issue_count"], 0)
        self.assertEqual(docs[0]["domain"], "telecom")
        self.assertEqual(docs[0]["document_type"], "invoice")
        self.assertEqual(docs[0]["related_asset"], "T-Mobile / mobilní služby")

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
                    "case_id": "ČPP Volvo 2026",
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
        self.assertEqual(docs[0]["case_id"], "cpp-volvo-2026")
        self.assertEqual(manifest["domain"], "insurance")
        self.assertEqual(manifest["document_type"], "insurance_policy")
        self.assertEqual(manifest["case_id"], "cpp-volvo-2026")
        self.assertEqual(audit[0]["action"], "update_classification_metadata")
        self.assertEqual(audit[0]["document_id"], "weak-1234567890")
        self.assertIn("case_id", audit[0]["changed_fields"])
        self.assertIn("metadata_backups", audit[0]["backup_dir"])

    def test_update_document_classification_metadata_preserves_custom_czech_domain_and_case(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            index = vault / "index"
            document_dir = vault / "vault" / "other" / "cez-doc"
            index.mkdir(parents=True)
            document_dir.mkdir(parents=True)
            stored_pdf = document_dir / "cez.pdf"
            stored_pdf.write_bytes(b"%PDF-1.4\n")
            (document_dir / "manifest.json").write_text(
                json.dumps({"document_id": "cez-doc", "stored_path": str(stored_pdf)}, ensure_ascii=False),
                encoding="utf-8",
            )
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "cez-doc",
                        "title": "ČEZ dokument",
                        "domain": "other",
                        "document_type": "email-attachment-pdf",
                        "counterparty": "",
                        "related_asset": "",
                        "stored_path": str(stored_pdf),
                    },
                ],
            )

            result = update_document_classification_metadata_action(
                document_id="cez-doc",
                metadata={
                    "domain": "ČEZ smlouvy",
                    "document_type": "Dohoda o úpravě smlouvy",
                    "counterparty": "ČEZ",
                    "related_asset": "elektřina",
                    "case_id": "ČEZ smlouvy 2026",
                },
                vault_dir=vault,
            )
            docs = self.read_jsonl(index / "documents_index.jsonl")

        self.assertTrue(result["ok"])
        self.assertEqual(docs[0]["domain"], "cez-smlouvy")
        self.assertEqual(docs[0]["document_type"], "dohoda-o-uprave-smlouvy")
        self.assertEqual(docs[0]["case_id"], "cez-smlouvy-2026")

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
        self.assertEqual(result["duplicate_group_count"], 0)
        self.assertEqual(result["related_source_group_count"], 0)
        self.assertEqual(result["items"][0]["status"], "ready")
        self.assertEqual(result["items"][0]["amount_due"], "1 234 Kč")
        self.assertNotIn("document_id", result["items"][0])
        self.assertNotIn("case_id", result["items"][0])
        self.assertNotIn("doc-trashed", json.dumps(result, ensure_ascii=False))

    def test_document_due_candidates_status_links_email_with_its_pdf_attachment(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            archive_dir = root / "email_archive"
            email_dir = archive_dir / "email-155808-vyuctovani-sluzeb"
            (email_dir / "attachments").mkdir(parents=True)
            reminders_path = root / "reminders.json"
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "tmobile-vyuctovani",
                        "title": "E-mail UID 155808 příloha Vyuctovani_40580553_2606.pdf",
                        "domain": "other",
                        "document_type": "email-attachment-pdf",
                        "counterparty": "T-Mobile Elektronické vyúčtování <[e-mail redigovan]>",
                        "case_id": "email-seznam-155808",
                        "related_asset": "",
                    }
                ],
            )
            self.write_jsonl(
                index / "due_dates.jsonl",
                [
                    {
                        "document_id": "tmobile-vyuctovani",
                        "date": "2026-06-20",
                        "type": "payment_due",
                        "confidence": "high",
                        "create_reminder_candidate": True,
                        "context": "Datum splatnosti 20.6.2026 Počet čísel: 5",
                    }
                ],
            )
            (email_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "archive_id": "email-155808-vyuctovani-sluzeb",
                        "uid": "155808",
                        "date": "Thu, 11 Jun 2026 12:00:00 +0200",
                        "from": "T-Mobile Elektronické vyúčtování <billing@example.com>",
                        "subject": "Vyúčtování služeb od T-Mobile",
                        "provider": "seznam",
                        "mailbox": "INBOX",
                        "archived_at": "2026-06-11T10:00:00+00:00",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (email_dir / "body.txt").write_text(
                (
                    "Zaplaťte prosím bankovním převodem. "
                    "Splatnost do: 20.6.2026. "
                    "Částka k zaplacení 999,00 Kč."
                ),
                encoding="utf-8",
            )
            (email_dir / "attachments" / "attachments.json").write_text(
                json.dumps({"attachments": []}),
                encoding="utf-8",
            )

            result = document_due_candidates_status(
                vault_dir=vault,
                reminders_path=reminders_path,
                archive_directory=archive_dir,
                today=date(2026, 6, 11),
            )

        self.assertEqual(result["candidate_count"], 2)
        self.assertEqual(result["duplicate_group_count"], 0)
        self.assertEqual(result["duplicate_candidate_count"], 0)
        self.assertEqual(result["related_source_group_count"], 1)
        self.assertEqual(result["related_source_candidate_count"], 2)
        self.assertTrue(all(item.get("related_source_group_id") for item in result["items"]))
        self.assertTrue(all("Související zdroje" in item.get("related_source_note", "") for item in result["items"]))
        self.assertFalse(any(item.get("duplicate_group_id") for item in result["items"]))
        self.assertNotIn("case_id", json.dumps(result, ensure_ascii=False))
        self.assertNotIn("billing@example.com", json.dumps(result, ensure_ascii=False))

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

    def test_document_due_candidates_hide_stale_historical_payment_dates(self) -> None:
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
                        "document_id": "rekonstrukce-cejeticky-2018",
                        "title": "Faktura Rekonstrukce RD Cejeticky 87",
                        "domain": "home",
                        "document_type": "invoice",
                    }
                ],
            )
            self.write_jsonl(
                index / "due_dates.jsonl",
                [
                    {
                        "document_id": "rekonstrukce-cejeticky-2018",
                        "date": "2018-01-15",
                        "type": "payment_due",
                        "confidence": "high",
                        "create_reminder_candidate": True,
                        "context": "Faktura na 115.000 Kc, splatnost 15. 1. 2018.",
                    }
                ],
            )

            result = document_due_candidates_status(
                vault_dir=vault,
                reminders_path=reminders_path,
                today=date(2026, 6, 15),
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(result["actionable_count"], 0)
        self.assertEqual(result["past_count"], 0)
        self.assertEqual(result["stale_past_due_count"], 1)
        self.assertEqual(result["items"], [])

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

    def test_email_archive_due_candidate_detects_payment_upominka_and_creates_reminder(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            (vault / "index").mkdir(parents=True)
            archive_dir = root / "email_archive"
            email_dir = archive_dir / "email-155924-upozorneni-na-dluznou-castku"
            (email_dir / "attachments").mkdir(parents=True)
            reminders_path = root / "reminders.json"
            (email_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "archive_id": "email-155924-upozorneni-na-dluznou-castku",
                        "uid": "155924",
                        "date": "Thu, 11 Jun 2026 16:09:42 +0200 (CEST)",
                        "from": "ČEZ Prodej, a.s. <upominani@example.com>",
                        "subject": "Upozornění na dlužnou částku",
                        "provider": "seznam",
                        "mailbox": "INBOX",
                        "archived_at": "2026-06-11T14:30:52+00:00",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (email_dir / "body.txt").write_text(
                (
                    "Dlužnou částku prosím zaplaťte do uvedeného data splatnosti. "
                    "Další případná upomínka bude již zpoplatněna. "
                    "Splatnost K zaplacení Záloha 31. 5. 2026 1 360,00 Kč "
                    "Celková dlužná částka 1 360,00 Kč. "
                    "Další přehled plateb má splatnost 30. 6. 2026 1 360,00 Kč."
                ),
                encoding="utf-8",
            )
            (email_dir / "attachments" / "attachments.json").write_text(
                json.dumps({"attachments": []}),
                encoding="utf-8",
            )

            status = document_due_candidates_status(
                vault_dir=vault,
                reminders_path=reminders_path,
                archive_directory=archive_dir,
                today=date(2026, 5, 20),
            )
            candidate = status["items"][0]
            created = create_document_due_reminder_action(
                candidate_ref=candidate["candidate_ref"],
                title="Zaplatit ČEZ upomínku",
                notes="Ověřeno z uloženého e-mailu.",
                confirmed=True,
                vault_dir=vault,
                reminders_path=reminders_path,
                archive_directory=archive_dir,
                today=date(2026, 5, 20),
            )
            store = json.loads(reminders_path.read_text(encoding="utf-8"))

        self.assertEqual(status["email_candidate_count"], 1)
        self.assertEqual(candidate["source_kind"], "email_archive")
        self.assertEqual(candidate["date"], "2026-05-31")
        self.assertEqual(candidate["amount_due"], "1 360,00 Kč")
        self.assertIn("ČEZ Prodej", candidate["title"])
        self.assertEqual(
            candidate["suggested_title"],
            "Zaplatit podle e-mailu: ČEZ Prodej, a.s. - Upozornění na dlužnou částku",
        )
        self.assertNotIn("upominani@example.com", json.dumps(candidate, ensure_ascii=False))
        self.assertTrue(created["ok"])
        self.assertEqual(store["reminders"][0]["source"]["type"], "email_archive")
        self.assertEqual(store["reminders"][0]["due_date"], "2026-05-31")
        self.assertEqual(store["reminders"][0]["amount_due"], "1 360,00 Kč")
        self.assertNotIn("upominani@example.com", json.dumps(store, ensure_ascii=False))

    def test_email_archive_due_candidates_skip_old_message_even_when_archived_today(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            (vault / "index").mkdir(parents=True)
            archive_dir = root / "email_archive"
            email_dir = archive_dir / "email-61429-rekonstrukce-cejeticky"
            email_dir.mkdir(parents=True)
            reminders_path = root / "reminders.json"
            (email_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "archive_id": "email-61429-rekonstrukce-cejeticky",
                        "uid": "61429",
                        "date": "Mon, 15 Jan 2018 13:15:40 +0100",
                        "from": "redigovano@example.com",
                        "subject": "Re: Faktura: Rekonstrukce RD Cejeticky 87",
                        "provider": "seznam",
                        "mailbox": "INBOX",
                        "archived_at": "2026-06-15T18:30:52+00:00",
                    }
                ),
                encoding="utf-8",
            )
            (email_dir / "body.txt").write_text(
                "Prosím pošlete fakturu na Rekonstrukci RD Cejeticky 87, na 115.000 Kc, "
                "měsíční splatnost od 15. 1. 2018.",
                encoding="utf-8",
            )

            status = document_due_candidates_status(
                vault_dir=vault,
                reminders_path=reminders_path,
                archive_directory=archive_dir,
                today=date(2026, 6, 15),
            )

        self.assertEqual(status["email_candidate_count"], 0)
        self.assertEqual(status["actionable_count"], 0)

    def test_email_archive_amount_parser_handles_dot_thousands_separator(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            (vault / "index").mkdir(parents=True)
            archive_dir = root / "email_archive"
            email_dir = archive_dir / "email-200000-rekonstrukce-cejeticky"
            email_dir.mkdir(parents=True)
            reminders_path = root / "reminders.json"
            (email_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "archive_id": "email-200000-rekonstrukce-cejeticky",
                        "uid": "200000",
                        "date": "Mon, 15 Jun 2026 13:15:40 +0200",
                        "from": "dodavatel@example.com",
                        "subject": "Faktura: Rekonstrukce RD Cejeticky 87",
                        "provider": "seznam",
                        "mailbox": "INBOX",
                        "archived_at": "2026-06-15T18:30:52+00:00",
                    }
                ),
                encoding="utf-8",
            )
            (email_dir / "body.txt").write_text(
                "Prosím uhradit fakturu na Rekonstrukci RD Cejeticky 87, částka 115.000 Kc, "
                "splatnost 30. 6. 2026.",
                encoding="utf-8",
            )

            status = document_due_candidates_status(
                vault_dir=vault,
                reminders_path=reminders_path,
                archive_directory=archive_dir,
                today=date(2026, 6, 15),
            )

        self.assertEqual(status["email_candidate_count"], 1)
        self.assertEqual(status["items"][0]["amount_due"], "115 000 Kc")

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
                        "document_id": "reviewed-image-doc",
                        "title": "Reviewed image",
                        "domain": "insurance",
                        "document_type": "policy",
                        "counterparty": "Generali",
                        "related_asset": "Volvo",
                        "reading_status": "ok",
                        "text_extraction": {"method": "image-no-text", "ocr_needed": True, "indexed_chars": 0},
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
                    {"document_id": "reviewed-image-doc", "text": ""},
                ],
            )

            report = document_review_report_status(vault_dir=vault)

            self.assertEqual(report["summary"]["total_indexed"], 5)
            self.assertEqual(report["summary"]["active_documents"], 4)
            self.assertEqual(report["summary"]["candidate_count"], 2)
            self.assertEqual(report["summary"]["reason_counts"]["zero_text"], 1)
            self.assertEqual(report["summary"]["reason_counts"]["short_text"], 1)
            self.assertEqual(report["summary"]["reason_counts"]["ocr_needed"], 1)
            groups = {group["id"]: group for group in report["groups"]}
            self.assertEqual(groups["zero_text"]["count"], 1)
            self.assertEqual(groups["short_text"]["count"], 1)
            self.assertEqual(groups["weak_metadata"]["count"], 0)
            self.assertEqual(groups["ok"]["count"], 2)
            self.assertIn("OCR", groups["zero_text"]["recommended_action"])
            self.assertIn("metadata", groups["weak_metadata"]["recommended_action"])
            self.assertNotIn("secret content", json.dumps(report, ensure_ascii=False))
            by_id = {item["document_id"]: item for item in report["items"]}
            self.assertIn("zero-doc", by_id)
            self.assertIn("short-doc", by_id)
            self.assertNotIn("clean-doc", by_id)
            self.assertNotIn("reviewed-image-doc", by_id)
            self.assertNotIn("trashed-doc", by_id)
            self.assertEqual(by_id["zero-doc"]["decision_group"], "zero_text")
            self.assertEqual(by_id["short-doc"]["decision_group"], "short_text")
            self.assertIn("OCR", by_id["zero-doc"]["recommended_action"])
            self.assertIn("domain", by_id["short-doc"]["weak_metadata_fields"])
            self.assertIn("oblast", by_id["short-doc"]["weak_metadata_labels"])
            self.assertIn("doplnit:", by_id["short-doc"]["review_summary"])
            self.assertIn("Čtení:", by_id["short-doc"]["reading_summary"])
            self.assertIn("protistrana", json.dumps(report, ensure_ascii=False))

    def test_document_review_report_treats_email_attachment_type_as_weak_metadata(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "cez-email-pdf",
                        "title": "ČEZ smlouva",
                        "domain": "energy",
                        "document_type": "email-attachment-pdf",
                        "counterparty": "ČEZ",
                        "related_asset": "elektřina",
                        "reading_status": "ok",
                        "text_extraction": {"method": "pdftotext", "indexed_chars": 1200},
                    },
                ],
            )
            self.write_jsonl(
                index / "text_index.jsonl",
                [{"document_id": "cez-email-pdf", "text": "x" * 1200}],
            )

            report = document_review_report_status(vault_dir=vault)

        self.assertEqual(report["summary"]["candidate_count"], 1)
        self.assertEqual(report["summary"]["reason_counts"]["weak_metadata"], 1)
        item = report["items"][0]
        self.assertEqual(item["decision_group"], "weak_metadata")
        self.assertEqual(item["weak_metadata_fields"], ["document_type"])
        self.assertIn("typ dokumentu", item["weak_metadata_labels"])

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
        self.assertIn("Rychlé akce", COCKPIT_HTML)
        self.assertIn("janickaBtn", COCKPIT_HTML)
        self.assertIn("Janička", COCKPIT_HTML)
        self.assertIn("janickaModal", COCKPIT_HTML)
        self.assertIn("Samantha bez technické vrstvy", COCKPIT_HTML)
        self.assertIn("janickaFindDocumentBtn", COCKPIT_HTML)
        self.assertIn("janickaPrintDocumentBtn", COCKPIT_HTML)
        self.assertIn("janickaEmailBtn", COCKPIT_HTML)
        self.assertIn("janickaLekarnaBtn", COCKPIT_HTML)
        self.assertIn("janickaFamilyBtn", COCKPIT_HTML)
        self.assertIn("janickaFamilyModal", COCKPIT_HTML)
        self.assertIn("janickaFamilyOrganizerBtn", COCKPIT_HTML)
        self.assertIn("janickaFamilyProjectsBtn", COCKPIT_HTML)
        for retired_marker in (
            "janickaAskAdamBtn",
            "janickaFullAdamBtn",
            "janickaChatModal",
            "/api/janicka/chat",
            "/api/janicka/light/",
            "/api/janicka/full-adam/open",
            "/api/adam/status",
            "/api/adam/start",
            "/api/adam/restart",
            "/api/adam/stop",
            "submitJanickaChat",
            "pollJanickaCodexReply",
            "Servisní fallback",
        ):
            with self.subTest(retired_marker=retired_marker):
                self.assertNotIn(retired_marker, COCKPIT_HTML)
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
        self.assertIn("openJanickaFamilyModal", COCKPIT_HTML)
        self.assertIn("openJanickaFamilyOrganizer", COCKPIT_HTML)
        self.assertIn("openJanickaFamilyProjects", COCKPIT_HTML)
        self.assertIn('openCatalogAppById("family-video-organizer")', COCKPIT_HTML)
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
        self.assertIn("refreshMainStatusOnReturn", COCKPIT_HTML)
        self.assertIn('window.addEventListener("focus"', COCKPIT_HTML)
        self.assertIn('window.addEventListener("pageshow"', COCKPIT_HTML)
        self.assertIn('document.addEventListener("visibilitychange"', COCKPIT_HTML)
        self.assertIn("dashboardProcessBtn", COCKPIT_HTML)
        self.assertIn("serviceBtn", COCKPIT_HTML)
        self.assertIn("servicePanel", COCKPIT_HTML)
        self.assertIn("dashboardDocuments", COCKPIT_HTML)
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
        self.assertIn("dashboardProjectAuditBtn", COCKPIT_HTML)
        self.assertIn("projectAuditModal", COCKPIT_HTML)
        self.assertIn("projectAuditSaveBtn", COCKPIT_HTML)
        self.assertIn("projectAuditRecentList", COCKPIT_HTML)
        self.assertIn("/api/project-audit?mode=quick", COCKPIT_HTML)
        self.assertIn("/api/project-audit/recent?limit=5", COCKPIT_HTML)
        self.assertIn("/api/project-audit/report?name=", COCKPIT_HTML)
        self.assertIn("/api/project-audit/save", COCKPIT_HTML)
        self.assertIn("openProjectAuditModal", COCKPIT_HTML)
        self.assertIn("loadRecentProjectAuditReports", COCKPIT_HTML)
        self.assertIn("loadProjectAuditReport", COCKPIT_HTML)
        self.assertIn("saveProjectAuditReport", COCKPIT_HTML)
        self.assertIn("dashboardQuickNotesBtn", COCKPIT_HTML)
        self.assertIn("dashboardQuickNotes", COCKPIT_HTML)
        self.assertIn("refreshQuickNotesSummary", COCKPIT_HTML)
        self.assertIn("quickNotesModal", COCKPIT_HTML)
        self.assertIn("/api/quick-notes/status", COCKPIT_HTML)
        self.assertIn("/api/quick-notes/detail", COCKPIT_HTML)
        self.assertIn("openQuickNotesModal", COCKPIT_HTML)
        self.assertIn("loadQuickNoteDetail", COCKPIT_HTML)
        self.assertIn("quickNoteTriageLine", COCKPIT_HTML)
        self.assertIn("QUICK_NOTES_MONITOR_MS = 30 * 1000", COCKPIT_HTML)
        self.assertIn("window.setInterval(refreshQuickNotesSummary, QUICK_NOTES_MONITOR_MS)", COCKPIT_HTML)
        self.assertIn("quickNotesRefreshInFlight", COCKPIT_HTML)
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
        self.assertIn("pendingDownloadCount", COCKPIT_HTML)
        self.assertIn("iCloud čeká", COCKPIT_HTML)
        self.assertIn("markUrgentReminderDone", COCKPIT_HTML)
        self.assertIn("dashboardRecoveryBtn", COCKPIT_HTML)
        self.assertIn("recoveryModal", COCKPIT_HTML)
        self.assertIn("/api/recovery/status", COCKPIT_HTML)
        self.assertIn("openRecoveryModal", COCKPIT_HTML)
        self.assertIn("dashboardCommandCheatsheetBtn", COCKPIT_HTML)
        self.assertIn("recoveryCommandCheatsheetBtn", COCKPIT_HTML)
        self.assertIn("commandCheatsheetModal", COCKPIT_HTML)
        self.assertIn("/api/command-cheatsheet", COCKPIT_HTML)
        self.assertIn("openCommandCheatsheetModal", COCKPIT_HTML)
        self.assertIn('command.textContent = item.command || "";', COCKPIT_HTML)
        self.assertIn('explanation.textContent = item.explanation || "";', COCKPIT_HTML)
        self.assertNotIn("commandCheatsheetCopy", COCKPIT_HTML)
        self.assertIn("dashboardAutosaveCleanupBtn", COCKPIT_HTML)
        self.assertIn("autosaveCleanupApplyBtn", COCKPIT_HTML)
        self.assertIn("/api/session-autosave/cleanup", COCKPIT_HTML)
        self.assertIn("previewAutosaveCleanup", COCKPIT_HTML)
        self.assertIn("applyAutosaveCleanup", COCKPIT_HTML)
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
        self.assertIn("/api/server/health", COCKPIT_HTML)
        self.assertIn("/api/web-apps", COCKPIT_HTML)
        self.assertIn("dashboardRestartBtn", COCKPIT_HTML)
        self.assertIn("Restart Cockpitu", COCKPIT_HTML)
        self.assertIn("restartCockpit", COCKPIT_HTML)
        self.assertIn("/api/cockpit/restart", COCKPIT_HTML)
        self.assertIn("waitForCockpitAndReload", COCKPIT_HTML)
        self.assertIn('fetch("/api/server/health", {cache: "no-store"})', COCKPIT_HTML)
        self.assertIn("Čekám na návrat Cockpitu", COCKPIT_HTML)
        self.assertNotIn("Za pár sekund stránku obnovím", COCKPIT_HTML)
        self.assertIn("devRunnerPanel", COCKPIT_HTML)
        self.assertIn("Vývojový runner", COCKPIT_HTML)
        self.assertIn("data-dev-runner=\"cockpit_tests\"", COCKPIT_HTML)
        self.assertNotIn("cockpit_voice_tests", COCKPIT_HTML)
        self.assertIn("data-dev-runner=\"git_diff_check\"", COCKPIT_HTML)
        self.assertIn("/api/dev-runner/run", COCKPIT_HTML)
        self.assertIn("runDevRunnerAction", COCKPIT_HTML)
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
        self.assertNotIn("documentsPanelNode.open = true", COCKPIT_HTML)
        self.assertNotIn("voiceCommandDetails", COCKPIT_HTML)
        self.assertNotIn("dashboardVoiceMode", COCKPIT_HTML)
        self.assertNotIn("voiceRecordBtn", COCKPIT_HTML)
        self.assertNotIn("voiceModeToggleBtn", COCKPIT_HTML)
        self.assertNotIn("voiceLastResponseCard", COCKPIT_HTML)
        self.assertIn("codexApprovalCard", COCKPIT_HTML)
        self.assertIn("Codex čeká na potvrzení", COCKPIT_HTML)
        self.assertIn("codexApprovalClearBtn", COCKPIT_HTML)
        self.assertIn("Vyčistit kartu", COCKPIT_HTML)
        self.assertIn("Co chci udělat", COCKPIT_HTML)
        self.assertIn("Co má Míla udělat", COCKPIT_HTML)
        self.assertIn("codexApprovalRisk", COCKPIT_HTML)
        self.assertIn("renderCodexApproval", COCKPIT_HTML)
        self.assertIn("/api/codex-approval/clear", COCKPIT_HTML)
        self.assertNotIn("/api/voice-mode/codex-approval/clear", COCKPIT_HTML)
        self.assertIn("clearCodexApprovalCard", COCKPIT_HTML)
        self.assertIn("codexApprovalOpenHumanAdamBtn", COCKPIT_HTML)
        self.assertIn("Otevřít Human–Adam", COCKPIT_HTML)
        self.assertNotIn("codexApprovalSendConfirmationBtn", COCKPIT_HTML)
        self.assertNotIn("sendCodexApprovalConfirmation", COCKPIT_HTML)
        self.assertNotIn("safeReadonlyCard", COCKPIT_HTML)
        self.assertNotIn("data-safe-readonly=\"git_status\"", COCKPIT_HTML)
        self.assertNotIn("data-safe-readonly=\"backup_status\"", COCKPIT_HTML)
        self.assertNotIn("/api/voice-mode/approval", COCKPIT_HTML)
        self.assertNotIn("renderVoiceLastResponse", COCKPIT_HTML)
        self.assertNotIn("refreshVoiceLatestResponse", COCKPIT_HTML)
        self.assertNotIn("startVoiceReplyPolling", COCKPIT_HTML)
        self.assertNotIn("/api/voice-bridge/frontend-event", COCKPIT_HTML)
        self.assertNotIn("VOICE_STATUS_MONITOR_MS", COCKPIT_HTML)
        self.assertIn('fetch("/api/live-status", {cache: "no-store"})', COCKPIT_HTML)
        self.assertIn("refreshLiveStatus();", COCKPIT_HTML)
        self.assertNotIn("window.setInterval(() => {\n\t      if (!document.hidden) {\n\t        refreshLiveStatus();", COCKPIT_HTML)
        self.assertNotIn("refresh({silent: true, includeSecondary: false});\n\t      }\n\t    }, VOICE_STATUS_MONITOR_MS", COCKPIT_HTML)
        self.assertIn("if (!document.hidden)", COCKPIT_HTML)
        self.assertIn("isRemoteCockpitClient", COCKPIT_HTML)
        self.assertIn("isMobileCockpitClient", COCKPIT_HTML)
        self.assertIn("shouldUseSystemSpeechFallback", COCKPIT_HTML)

    def test_cockpit_codex_approval_clear_action_requires_confirmation(self) -> None:
        result = cockpit_codex_approval_clear_action(
            {"confirmed": False},
            clearer=lambda **kwargs: {"ok": True, "active": False, "status": "cleared"},
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "confirmation_required")

    def test_generic_codex_approval_remains_and_legacy_tvbcp_routes_are_absent(self) -> None:
        registered_paths = {item["path"] for item in COCKPIT_POST_ACTIONS}
        post_routes = set(self.cockpit_do_post_routes())
        get_routes = set(self.cockpit_do_get_routes())

        self.assertIn("/api/codex-approval/clear", registered_paths)
        self.assertIn("/api/codex-approval/clear", post_routes)
        self.assertNotIn("/api/voice-mode/codex-approval/clear", registered_paths)
        self.assertNotIn("/api/voice-mode/codex-approval/clear", post_routes)
        self.assertNotIn("/api/tvbcp", get_routes)
        self.assertNotIn("/api/voice-bridge/tvbcp", get_routes)

    def test_live_status_refresh_renders_only_codex_approval(self) -> None:
        start = COCKPIT_HTML.index("async function refreshLiveStatus()")
        end = COCKPIT_HTML.index("function refreshMainStatusOnReturn", start)
        live_refresh_source = COCKPIT_HTML[start:end]

        self.assertIn("renderCodexApproval(latestMainStatusData.codex_approval);", live_refresh_source)
        self.assertNotIn("renderDashboard(", live_refresh_source)
        self.assertNotIn("voice_mode:", live_refresh_source)
        self.assertNotIn("voice_bridge:", live_refresh_source)
        self.assertNotIn("renderVoiceStatus", COCKPIT_HTML)

        dashboard_start = COCKPIT_HTML.index("function renderDashboard(data)")
        dashboard_end = COCKPIT_HTML.index("function renderDashboardMorningSentence", dashboard_start)
        self.assertNotIn("documentsPanelNode.open = true", COCKPIT_HTML[dashboard_start:dashboard_end])

    def test_expected_audio_autoplay_block_is_not_a_frontend_error(self) -> None:
        start = COCKPIT_HTML.index("async function speakText(")
        end = COCKPIT_HTML.index("async function speakDashboardStatus()", start)
        source = COCKPIT_HTML[start:end]

        self.assertIn("function isExpectedAudioAutoplayBlock(error)", COCKPIT_HTML)
        self.assertIn('name === "notallowederror"', COCKPIT_HTML)
        self.assertIn("if (isExpectedAudioAutoplayBlock(contextPlayErr))", source)
        self.assertIn("const autoplayBlocked = isExpectedAudioAutoplayBlock(playErr)", source)
        self.assertIn("if (!autoplayBlocked)", source)
        self.assertIn("recordFrontendError(playErr);", source)

    def test_generic_speech_audio_context_recovers_after_call_interruption(self) -> None:
        self.assertIn('voiceAudioContext.state === "closed"', COCKPIT_HTML)
        self.assertIn('["suspended", "interrupted"].includes(state)', COCKPIT_HTML)
        self.assertIn("await ensureVoiceAudioContextRunning(context)", COCKPIT_HTML)
        start = COCKPIT_HTML.index("async function speakText(")
        end = COCKPIT_HTML.index("async function speakDashboardStatus()", start)
        source = COCKPIT_HTML[start:end]
        self.assertIn("if (isRemoteCockpitClient())", source)
        self.assertIn("await primeVoiceAudioContextFromGesture()", source)
        self.assertLess(
            source.index("await primeVoiceAudioContextFromGesture()"),
            source.index('fetch("/api/speech/edge-tts"'),
        )

    def test_cockpit_codex_approval_clear_action_clears_runtime_state(self) -> None:
        calls = []

        def fake_clearer(**kwargs):
            calls.append(kwargs)
            return {"ok": True, "active": False, "status": "cleared", "note": kwargs.get("note")}

        result = cockpit_codex_approval_clear_action(
            {"confirmed": True, "note": "Vyřešeno v terminálu."},
            clearer=fake_clearer,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "cleared")
        self.assertEqual(result["codex_approval"]["note"], "Vyřešeno v terminálu.")
        self.assertEqual(calls, [{"note": "Vyřešeno v terminálu."}])

    def test_cockpit_dev_runner_actions_lists_allowlist(self) -> None:
        result = cockpit_dev_runner_actions()
        ids = {item["id"] for item in result["actions"]}

        self.assertTrue(result["ok"])
        self.assertIn("cockpit_tests", ids)
        self.assertNotIn("cockpit_voice_tests", ids)
        self.assertIn("git_diff_check", ids)

    def test_cockpit_dev_runner_run_action_rejects_unknown_action(self) -> None:
        result = cockpit_dev_runner_run_action({"action_id": "curl arbitrary"})

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "unknown_action")

    def test_cockpit_dev_runner_run_action_runs_registered_command(self) -> None:
        calls = []

        def fake_runner(command, **kwargs):
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(command, 0, stdout="Ran 1 test\nOK\n", stderr="")

        result = cockpit_dev_runner_run_action({"action_id": "git_diff_check"}, runner=fake_runner)

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["returncode"], 0)
        self.assertIn("Ran 1 test", result["stdout"])
        self.assertEqual(calls[0][0][-2:], ["diff", "--check"])
        self.assertEqual(calls[0][1]["cwd"], str(cockpit_module.PROJECT_ROOT))

    def test_cockpit_dev_runner_run_action_reports_failed_command(self) -> None:
        def fake_runner(command, **kwargs):
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="bad whitespace\n")

        result = cockpit_dev_runner_run_action({"action_id": "git_diff_check"}, runner=fake_runner)

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "failed")
        self.assertIn("bad whitespace", result["stderr"])
        self.assertNotIn("markVoiceResponseNeedsTap", COCKPIT_HTML)
        self.assertIn("options.allowSystemFallback !== false && shouldUseSystemSpeechFallback()", COCKPIT_HTML)
        self.assertIn("primeVoiceAudioContextFromGesture", COCKPIT_HTML)
        self.assertNotIn("voiceAudioUnlockBtn", COCKPIT_HTML)
        self.assertNotIn("openVoiceAudioChannel", COCKPIT_HTML)
        self.assertIn("playVoiceAudioBase64", COCKPIT_HTML)
        self.assertIn("voiceAudioUnlocked", COCKPIT_HTML)
        self.assertIn("VOICE_AUDIO_DECODE_TIMEOUT_MS = 5000", COCKPIT_HTML)
        self.assertIn("withVoiceAudioTimeout", COCKPIT_HTML)
        self.assertIn('error.name = "VoiceAudioTimeoutError"', COCKPIT_HTML)
        self.assertNotIn("renderVoiceApproval", COCKPIT_HTML)
        self.assertNotIn("speakLastAdamResponse", COCKPIT_HTML)
        self.assertNotIn("submitVoiceApproval", COCKPIT_HTML)
        self.assertNotIn("/api/voice-mode/latest-response", COCKPIT_HTML)
        self.assertNotIn("voiceBridgeSessions", COCKPIT_HTML)
        self.assertIn("Autosave watchery:", COCKPIT_HTML)
        self.assertNotIn("voiceModeStartBtn", COCKPIT_HTML)
        self.assertNotIn("voiceModeStopBtn", COCKPIT_HTML)
        self.assertNotIn("voiceBridgeStatus", COCKPIT_HTML)
        self.assertNotIn("/api/voice-bridge/terminate-stale", COCKPIT_HTML)
        self.assertNotIn("terminateStaleVoiceBridgeSessions", COCKPIT_HTML)
        self.assertIn("frontendErrorLooksRecoverableNetwork", COCKPIT_HTML)
        self.assertIn("clearRecoverableFrontendNetworkErrors", COCKPIT_HTML)
        self.assertIn('value.includes("load failed")', COCKPIT_HTML)
        self.assertNotIn("/api/voice-mode/start", COCKPIT_HTML)
        self.assertNotIn("/api/voice-mode/stop", COCKPIT_HTML)
        self.assertNotIn("samanthaVoiceModeEnabled", COCKPIT_HTML)
        self.assertNotIn("toggleVoiceMode", COCKPIT_HTML)
        self.assertNotIn("directVoiceRecordingSupported", COCKPIT_HTML)
        self.assertNotIn("voiceTranscript", COCKPIT_HTML)
        self.assertNotIn("tvbcpOpenBtn", COCKPIT_HTML)
        self.assertNotIn("tvbcpModal", COCKPIT_HTML)
        self.assertNotIn("tvbcpCloseBtn", COCKPIT_HTML)
        self.assertNotIn("openTvbcpModal", COCKPIT_HTML)
        self.assertNotIn("closeTvbcpModal", COCKPIT_HTML)
        self.assertNotIn('tvbcpContent.textContent = data.content', COCKPIT_HTML)
        self.assertNotIn('tvbcpContent.scrollTop = tvbcpContent.scrollHeight', COCKPIT_HTML)
        self.assertNotIn('window.open("/voice-bridge/tvbcp/"', COCKPIT_HTML)
        self.assertNotIn("startVoiceRecording", COCKPIT_HTML)
        self.assertNotIn("transcribeVoiceRecording", COCKPIT_HTML)
        self.assertNotIn("submitVoiceTranscript", COCKPIT_HTML)
        self.assertNotIn("/api/speech/transcribe", COCKPIT_HTML)
        self.assertNotIn("/api/speech/voice-text", COCKPIT_HTML)
        self.assertIn("frontendHealthPanel", COCKPIT_HTML)
        self.assertIn("frontendHealthJs", COCKPIT_HTML)
        self.assertIn("JS se zatím nespustil", COCKPIT_HTML)
        self.assertIn("Co teď dělat", COCKPIT_HTML)
        self.assertIn("actionQueueStatus", COCKPIT_HTML)
        self.assertIn("actionQueueList", COCKPIT_HTML)
        self.assertIn("renderActionQueue", COCKPIT_HTML)
        self.assertIn("actionQueueButton", COCKPIT_HTML)
        self.assertIn("FULL_STATUS_MONITOR_MS = 5 * 60 * 1000", COCKPIT_HTML)
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
        self.assertIn("Kontrola nesrovnalostí", COCKPIT_HTML)
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
        self.assertIn("Související dokumenty", COCKPIT_HTML)
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
        self.assertIn('<div id="reviewReportCount" class="work-count">?</div>', COCKPIT_HTML)
        self.assertIn('<button class="secondary" id="reviewReportBtn">Načti report</button>', COCKPIT_HTML)
        self.assertIn("/api/documents/review-report", COCKPIT_HTML)
        self.assertIn("loadDocumentReviewReport", COCKPIT_HTML)
        self.assertIn("renderDocumentReviewReportItem", COCKPIT_HTML)
        self.assertIn("review-group", COCKPIT_HTML)
        self.assertIn("review-report-list", COCKPIT_HTML)
        self.assertIn('id="reviewReportList" class="work-list review-report-list"', COCKPIT_HTML)
        self.assertIn("openDocumentForReading(documentRef", COCKPIT_HTML)
        self.assertIn("Stav čtení", COCKPIT_HTML)
        self.assertIn("afterSave: loadDocumentReviewReport", COCKPIT_HTML)
        self.assertIn("Bez textu / OCR", COCKPIT_HTML)
        self.assertIn("Krátký text", COCKPIT_HTML)
        self.assertIn("Doplnit údaje", COCKPIT_HTML)
        self.assertIn("V pořádku", COCKPIT_HTML)
        self.assertIn("Zpracovat další dokument", COCKPIT_HTML)
        self.assertIn("Připomenutí", COCKPIT_HTML)
        self.assertIn("remindersModal", COCKPIT_HTML)
        self.assertIn("/api/reminders", COCKPIT_HTML)
        self.assertIn("/api/reminders/done", COCKPIT_HTML)
        self.assertIn("/api/reminders/cancel-payment", COCKPIT_HTML)
        self.assertIn("/api/reminders/source", COCKPIT_HTML)
        self.assertIn("/documents/read?document_id=", COCKPIT_HTML)
        self.assertIn("markReminderDone", COCKPIT_HTML)
        self.assertIn("cancelPaymentReminder", COCKPIT_HTML)
        self.assertIn("loadReminderSource", COCKPIT_HTML)
        self.assertIn('fetch(url, {cache: "no-store"})', COCKPIT_HTML)
        self.assertIn('const data = await fetchJson("/api/reminders");', COCKPIT_HTML)
        self.assertIn('const fresh = await fetchJson("/api/reminders");', COCKPIT_HTML)
        self.assertIn('const fresh = await fetchJson("/api/urgent-reminders/status");', COCKPIT_HTML)
        self.assertIn("item.reminder_ref", COCKPIT_HTML)
        self.assertIn("renderReminderConflicts", COCKPIT_HTML)
        self.assertIn("Konflikt plateb", COCKPIT_HTML)
        self.assertIn("Uzavřít jako zrušené", COCKPIT_HTML)
        self.assertIn('result.kind === "email_archive"', COCKPIT_HTML)
        self.assertIn("EmailArchiveVault", COCKPIT_HTML)
        self.assertIn("Otevřít PDF", COCKPIT_HTML)
        self.assertIn("Otevřít uloženou přílohu", COCKPIT_HTML)
        self.assertIn("Splněno", COCKPIT_HTML)
        self.assertIn("Zdroj", COCKPIT_HTML)
        self.assertIn("Dokumentový trezor", COCKPIT_HTML)
        self.assertIn("Aktuální stav dokumentů", COCKPIT_HTML)
        self.assertIn("Historie a technické podrobnosti", COCKPIT_HTML)
        self.assertIn("Zpracovat další dokument", COCKPIT_HTML)
        self.assertIn('renderVaultSummary(data.vault || "", data.document_work || {})', COCKPIT_HTML)
        self.assertIn("function vaultSummaryCount(raw, label)", COCKPIT_HTML)
        self.assertIn("function vaultTechnicalDetails(raw)", COCKPIT_HTML)
        self.assertIn('"Dalsi krok:"', COCKPIT_HTML)
        self.assertIn("vault-metrics", COCKPIT_HTML)
        self.assertNotIn("scan_document_inbox", COCKPIT_HTML)
        self.assertNotIn("Auditní historie inboxu", COCKPIT_HTML)

    def test_document_work_cards_are_ordered_by_daily_workflow_columns(self) -> None:
        headings = [
            "Nová PDF ve Downloads za 7 dní",
            "Uložené dokumenty k revizi",
            "Problémy",
            "Dokumentový intake",
            "Dokumenty k revizi",
            "Klasifikace",
            "Termíny v dokumentech",
            "Související dokumenty",
        ]
        positions = [COCKPIT_HTML.index(f"<h3>{heading}</h3>") for heading in headings]

        self.assertEqual(positions, sorted(positions))

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
            patch(
                "app.cockpit.urgent_reminders_status",
                return_value={"ok": True, "count": 0, "items": []},
            ),
            patch("app.cockpit.probe_scandocu", return_value={"running": False}),
            patch(
                "app.cockpit.load_codex_approval_request",
                return_value={"ok": True, "active": False, "status": "none"},
            ),
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
        self.assertEqual(status["codex_approval"]["status"], "none")
        self.assertNotIn("voice_mode", status)
        self.assertNotIn("voice_bridge", status)
        self.assertIn("git", status)
        self.assertIn("status_timing", status)
        timing = status["status_timing"]
        self.assertIsInstance(timing["total_ms"], float)
        self.assertIn("sections_ms", timing)
        self.assertIn("document_work", timing["sections_ms"])
        self.assertNotIn("voice_mode", timing["sections_ms"])
        self.assertNotIn("voice_bridge", timing["sections_ms"])
        self.assertIn("slowest_sections", timing)
        self.assertLessEqual(len(timing["slowest_sections"]), 3)
        self.assertNotIn("quantitative", status)
        self.assertNotIn("projects", status)
        self.assertNotIn("consistency", status)

    def test_server_health_status_is_lightweight(self) -> None:
        with patch("app.cockpit.cockpit_status") as cockpit_status_mock:
            status = server_health_status(host="127.0.0.1", port=8770)

        cockpit_status_mock.assert_not_called()
        self.assertTrue(status["ok"])
        self.assertEqual(status["server"]["code_stamp"], cockpit_module.COCKPIT_CODE_STAMP)
        self.assertEqual(status["server"]["port"], 8770)
        self.assertIn("generated_at", status)
        self.assertNotIn("quantitative", status)
        self.assertNotIn("projects", status)
        self.assertNotIn("consistency", status)

    def test_cockpit_live_status_contains_only_current_codex_approval(self) -> None:
        codex_approval_calls = 0

        def codex_approval_loader() -> dict[str, object]:
            nonlocal codex_approval_calls
            codex_approval_calls += 1
            return {"ok": True, "active": codex_approval_calls == 1}

        first = cockpit_live_status(
            codex_approval_loader=codex_approval_loader,
        )
        second = cockpit_live_status(
            codex_approval_loader=codex_approval_loader,
        )

        self.assertEqual(codex_approval_calls, 2)
        self.assertTrue(first["codex_approval"]["active"])
        self.assertFalse(second["codex_approval"]["active"])
        self.assertNotIn("voice_mode", second)
        self.assertNotIn("voice_bridge", second)
        self.assertNotIn("voice_mode_ms", second["live_status_timing"])
        self.assertNotIn("voice_bridge_ms", second["live_status_timing"])
        self.assertNotIn("voice_bridge_cache_hit", second["live_status_timing"])
        self.assertNotIn("document_work", second)
        self.assertNotIn("backup_status", second)
        self.assertNotIn("git", second)

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
        self.assertIn("--delay", calls[0]["args"])
        self.assertIn("2.0", calls[0]["args"])
        self.assertTrue(calls[0]["start_new_session"])

    def test_private_simple_main_deployment_binds_server_context_to_restart_worker(self) -> None:
        manager_calls: list[dict[str, object]] = []
        restart_calls: list[dict[str, object]] = []

        class FakeProfileManager:
            def prepare_simple_main_deployment(self, **kwargs: object) -> dict[str, object]:
                manager_calls.append(kwargs)
                restart = kwargs["restart_scheduler"]()
                return {"ok": True, "state": "pending_restart", "restart": restart}

        def fake_restart_action(**kwargs: object) -> dict[str, object]:
            restart_calls.append(kwargs)
            return {"ok": True, "status": "restart_started", "pid": kwargs["pid"]}

        with patch.object(cockpit_module.os, "getpid", return_value=456):
            result = human_adam_simple_main_deployment_action(
                confirmed=True,
                service=FakeProfileManager(),
                host="127.0.0.1",
                port=8770,
                restart_action=fake_restart_action,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(manager_calls[0]["previous_pid"], 456)
        self.assertTrue(manager_calls[0]["confirmed"])
        self.assertTrue(callable(manager_calls[0]["restart_scheduler"]))
        self.assertEqual(
            restart_calls,
            [{"confirmed": True, "host": "127.0.0.1", "port": 8770, "pid": 456}],
        )

    def test_private_simple_main_deployment_returns_safe_manager_failure(self) -> None:
        class FailingProfileManager:
            def prepare_simple_main_deployment(self, **_kwargs: object) -> dict[str, object]:
                raise cockpit_module.AppServerError("Nasazení bylo bezpečně zastaveno.")

        result = human_adam_simple_main_deployment_action(
            confirmed=True,
            service=FailingProfileManager(),
            restart_action=lambda **_kwargs: self.fail("restart se nesmí spustit"),
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "simple_main_deployment_failed")
        self.assertIn("bezpečně zastaveno", result["message"])

    def test_simple_main_deployment_audit_returns_safe_manager_result(self) -> None:
        class FakeProfileManager:
            def audit_simple_main_deployment(self) -> dict[str, object]:
                return {"ok": True, "ready": True, "main_short": "a" * 12}

        result = human_adam_simple_main_deployment_audit_action(
            service=FakeProfileManager()
        )

        self.assertTrue(result["ok"])
        self.assertTrue(result["ready"])
        self.assertEqual(result["main_short"], "a" * 12)

    def test_main_remote_sync_actions_bind_audit_heads_and_confirmation(self) -> None:
        calls: list[dict[str, object]] = []

        class FakeProfileManager:
            def audit_main_remote_sync(self) -> dict[str, object]:
                return {
                    "ok": True,
                    "state": "fast_forward_available",
                    "can_fast_forward": True,
                }

            def apply_main_remote_sync(self, **kwargs: object) -> dict[str, object]:
                calls.append(kwargs)
                return {"ok": True, "state": "aligned", "main_short": "b" * 12}

        manager = FakeProfileManager()
        audit = human_adam_main_remote_sync_audit_action(service=manager)
        result = human_adam_main_remote_sync_action(
            {
                "confirmed": True,
                "expected_local_head": "a" * 40,
                "expected_origin_head": "b" * 40,
            },
            service=manager,
        )

        self.assertTrue(audit["can_fast_forward"])
        self.assertTrue(result["ok"])
        self.assertEqual(
            calls,
            [
                {
                    "expected_local_head": "a" * 40,
                    "expected_origin_head": "b" * 40,
                    "confirmed": True,
                }
            ],
        )

    def test_main_remote_sync_actions_fail_closed(self) -> None:
        class FailingProfileManager:
            def audit_main_remote_sync(self) -> dict[str, object]:
                raise cockpit_module.AppServerError("Main je rozvětvený.")

            def apply_main_remote_sync(self, **_kwargs: object) -> dict[str, object]:
                raise cockpit_module.AppServerError("Auditovaný commit se změnil.")

        audit = human_adam_main_remote_sync_audit_action(
            service=FailingProfileManager()
        )
        result = human_adam_main_remote_sync_action(
            {
                "confirmed": True,
                "expected_local_head": "a" * 40,
                "expected_origin_head": "b" * 40,
            },
            service=FailingProfileManager(),
        )

        self.assertFalse(audit["ok"])
        self.assertFalse(audit["can_fast_forward"])
        self.assertTrue(audit["read_only"])
        self.assertFalse(result["ok"])
        self.assertIn("změnil", result["message"])

    def test_github_batch_actions_bind_exact_audit_heads_and_confirmation(self) -> None:
        calls: list[dict[str, object]] = []

        class FakeProfileManager:
            def audit_github_batch(self) -> dict[str, object]:
                return {"ok": True, "state": "ready", "ready": True}

            def push_github_batch(self, **kwargs: object) -> dict[str, object]:
                calls.append(kwargs)
                return {"ok": True, "state": "pushed", "pushed": True}

        manager = FakeProfileManager()
        audit = human_adam_github_batch_audit_action(service=manager)
        result = human_adam_github_batch_action(
            {
                "confirmation": "POTVRZUJI ODESLANI DENNIHO GITHUB BALICKU",
                "expected_origin_head": "a" * 40,
                "expected_local_head": "b" * 40,
            },
            service=manager,
        )

        self.assertTrue(audit["ready"])
        self.assertTrue(result["pushed"])
        self.assertEqual(
            calls,
            [
                {
                    "expected_origin_head": "a" * 40,
                    "expected_local_head": "b" * 40,
                    "confirmation": "POTVRZUJI ODESLANI DENNIHO GITHUB BALICKU",
                }
            ],
        )
        self.assertIn(
            "/api/human-adam/github-batch",
            {item["path"] for item in COCKPIT_POST_ACTIONS},
        )

    def test_private_simple_main_deployment_verification_uses_server_evidence(self) -> None:
        manager_calls: list[dict[str, object]] = []

        class FakeProfileManager:
            def verify_simple_main_deployment(self, **kwargs: object) -> dict[str, object]:
                manager_calls.append(kwargs)
                return {"ok": True, "state": "deployed", "smoke": {"check_count": 5}}

        with patch.object(cockpit_module.os, "getpid", return_value=654):
            result = human_adam_simple_main_deployment_verification_action(
                service=FakeProfileManager()
            )

        self.assertTrue(result["ok"])
        self.assertEqual(
            manager_calls,
            [
                {
                    "observed_pid": 654,
                    "observed_code_stamp": cockpit_module.COCKPIT_CODE_STAMP,
                }
            ],
        )

    def test_restarted_server_verifies_only_a_pending_deployment_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            receipt_path = Path(temp_dir) / "receipt.json"
            pending = {
                "schema_version": 1,
                "state": "pending_restart",
                "workstream_id": "layer-human-adam-development",
                "main_head": "a" * 40,
                "expected_code_stamp": "0123456789abcdef",
                "previous_pid": 100,
                "test_count": 1218,
                "gate_duration_seconds": 290.7,
                "prepared_at": "2026-07-25T19:50:42+00:00",
            }
            receipt_path.write_text(json.dumps(pending), encoding="utf-8")
            service = SimpleNamespace(
                simple_main_deployment_receipt_path=receipt_path
            )
            calls: list[object] = []

            def verifier(*, service: object) -> dict[str, object]:
                calls.append(service)
                return {"ok": True, "state": "deployed"}

            verified = (
                cockpit_module.human_adam_pending_deployment_startup_verification_action(
                    service=service,
                    verification_action=verifier,
                )
            )
            receipt_path.write_text(
                json.dumps(
                    {
                        **pending,
                        "state": "deployed",
                        "observed_pid": 200,
                        "smoke_count": 5,
                        "deployed_at": "2026-07-25T19:51:00+00:00",
                    }
                ),
                encoding="utf-8",
            )
            already_done = (
                cockpit_module.human_adam_pending_deployment_startup_verification_action(
                    service=service,
                    verification_action=lambda **_kwargs: self.fail(
                        "Dokončená účtenka se nesmí znovu ověřovat při startu."
                    ),
                )
            )

        self.assertTrue(verified["ok"])
        self.assertEqual(verified["state"], "deployed")
        self.assertEqual(calls, [service])
        self.assertTrue(already_done["ok"])
        self.assertEqual(already_done["state"], "deployed")
        self.assertFalse(already_done["verification_needed"])

    def test_canonical_server_schedules_pending_deployment_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            receipt_path = Path(temp_dir) / "receipt.json"
            receipt_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "state": "pending_restart",
                        "workstream_id": "layer-human-adam-development",
                        "main_head": "a" * 40,
                        "expected_code_stamp": "0123456789abcdef",
                        "previous_pid": 100,
                        "test_count": 1218,
                        "gate_duration_seconds": 290.7,
                        "prepared_at": "2026-07-25T19:50:42+00:00",
                    }
                ),
                encoding="utf-8",
            )
            service = SimpleNamespace(
                simple_main_deployment_receipt_path=receipt_path
            )
            calls: list[object] = []

            class ImmediateThread:
                def __init__(self, *, target, **_kwargs):
                    self.target = target

                def start(self) -> None:
                    self.target()

            def verifier(*, service: object) -> dict[str, object]:
                calls.append(service)
                return {"ok": True, "state": "deployed"}

            with patch.object(cockpit_module.threading, "Thread", ImmediateThread):
                scheduled = (
                    cockpit_module.schedule_pending_deployment_startup_verification(
                        host="127.0.0.1",
                        port=8770,
                        service=service,
                        attempts=1,
                        delay_seconds=0,
                        verification_action=verifier,
                    )
                )
                skipped = (
                    cockpit_module.schedule_pending_deployment_startup_verification(
                        host="127.0.0.1",
                        port=8771,
                        service=service,
                        attempts=1,
                        delay_seconds=0,
                        verification_action=verifier,
                    )
                )

        self.assertTrue(scheduled)
        self.assertFalse(skipped)
        self.assertEqual(calls, [service])

    def test_private_simple_main_deployment_verification_returns_safe_failure(self) -> None:
        class FailingProfileManager:
            def verify_simple_main_deployment(self, **_kwargs: object) -> dict[str, object]:
                raise cockpit_module.AppServerError("Restart nebyl úplně ověřen.")

        result = human_adam_simple_main_deployment_verification_action(
            service=FailingProfileManager()
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "simple_main_deployment_verification_failed")
        self.assertIn("nebyl úplně ověřen", result["message"])

    def test_simple_main_deployment_reuses_existing_controls_and_registers_verification(self) -> None:
        handlers = {item["handler_name"] for item in COCKPIT_POST_ACTIONS}
        cockpit_source = Path(cockpit_module.__file__).read_text(encoding="utf-8")

        self.assertIn("/api/human-adam/deploy-audit", self.cockpit_do_get_routes())
        self.assertIn("/api/human-adam/main-sync-audit", self.cockpit_do_get_routes())
        self.assertIn("/api/human-adam/deploy", self.cockpit_do_post_routes())
        self.assertIn("/api/human-adam/main-sync", self.cockpit_do_post_routes())
        self.assertIn("/api/human-adam/deploy-verification", self.cockpit_do_post_routes())
        self.assertIn("/api/human-adam/deploy", cockpit_module.HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/main-sync", cockpit_module.HUMAN_ADAM_HTML)
        self.assertIn(
            "/api/human-adam/deploy-verification", cockpit_module.HUMAN_ADAM_HTML
        )
        self.assertIn("human_adam_simple_main_deployment_action", handlers)
        self.assertIn("human_adam_main_remote_sync_action", handlers)
        self.assertIn("human_adam_simple_main_deployment_verification_action", handlers)
        self.assertIn(
            "schedule_pending_deployment_startup_verification(",
            cockpit_source,
        )
        self.assertEqual(cockpit_module.HUMAN_ADAM_HTML.count('id="deployAuditBtn"'), 1)
        self.assertEqual(cockpit_module.HUMAN_ADAM_HTML.count('id="mainSyncBtn"'), 1)
        self.assertEqual(cockpit_module.HUMAN_ADAM_HTML.count('id="deployBtn"'), 1)

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

    def test_transcribe_audio_base64_isolated_runs_subprocess_and_cleans_temp_file(self) -> None:
        encoded = base64.b64encode(b"fake audio").decode("ascii")
        seen_temp_paths: list[Path] = []

        def fake_runner(args, **kwargs):
            audio_path = Path(args[args.index("--audio-file") + 1])
            seen_temp_paths.append(audio_path)
            self.assertTrue(audio_path.exists())
            self.assertEqual(audio_path.read_bytes(), b"fake audio")
            self.assertEqual(
                args[:2],
                [
                    str(cockpit_module.PROJECT_ROOT / ".venv" / "bin" / "python"),
                    str(cockpit_module.PROJECT_ROOT / "app" / "speech" / "transcribe.py"),
                ],
            )
            self.assertEqual(args[args.index("--mime-type") + 1], "audio/webm")
            self.assertEqual(args[args.index("--language") + 1], "cs")
            self.assertEqual(kwargs["cwd"], str(cockpit_module.PROJECT_ROOT))
            self.assertTrue(kwargs["capture_output"])
            self.assertTrue(kwargs["text"])
            self.assertFalse(kwargs["check"])
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=json.dumps({"ok": True, "text": "Najdi dnešní dokumenty."}),
                stderr="",
            )

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            result = transcribe_audio_base64_isolated(
                encoded,
                mime_type="audio/webm",
                runner=fake_runner,
                temp_dir=temp_dir,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["text"], "Najdi dnešní dokumenty.")
        self.assertEqual(len(seen_temp_paths), 1)
        self.assertFalse(seen_temp_paths[0].exists())

    def test_human_adam_transcribe_action_only_returns_editable_text_without_delivery(self) -> None:
        transcribe_calls: list[dict[str, object]] = []

        def fake_transcriber(audio_base64: str, **kwargs: object) -> dict[str, object]:
            transcribe_calls.append({"audio_base64": audio_base64, **kwargs})
            return {"ok": True, "text": "  Zkontroluj pracovní stav.  ", "private": "ignored"}

        with patch("app.cockpit.human_adam_send_action") as canonical_send:
            result = human_adam_transcribe_action(
                {"audio_base64": "encoded-audio", "mime_type": "audio/mp4", "language": "cs"},
                transcriber=fake_transcriber,
            )

        self.assertEqual(
            result,
            {"ok": True, "status": "transcribed_for_review", "text": "Zkontroluj pracovní stav."},
        )
        self.assertEqual(
            transcribe_calls,
            [
                {
                    "audio_base64": "encoded-audio",
                    "mime_type": "audio/mp4",
                    "language": "cs",
                }
            ],
        )
        canonical_send.assert_not_called()

    def test_transcribe_audio_base64_isolated_reports_subprocess_failure(self) -> None:
        encoded = base64.b64encode(b"fake audio").decode("ascii")

        def fake_runner(args, **kwargs):
            return subprocess.CompletedProcess(
                args,
                1,
                stdout=json.dumps({"ok": False, "message": "Resource deadlock avoided"}),
                stderr="",
            )

        with self.assertRaises(cockpit_module.TranscriptionError) as cm:
            transcribe_audio_base64_isolated(encoded, mime_type="audio/webm", runner=fake_runner)

        self.assertIn("Resource deadlock avoided", str(cm.exception))

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
                autosave_runtime_getter=lambda **_kwargs: SimpleNamespace(
                    ok=False,
                    watcher_running=True,
                    watcher_count=2,
                    watcher_pids=(111, 222),
                    warning="bezi 2 autosave watchery",
                ),
            )

        self.assertTrue(result["ok"])
        self.assertTrue(result["autosave"]["ok"])
        self.assertEqual(result["autosave"]["latest_file"], autosave_file.name)
        self.assertEqual(result["autosave"]["runtime"]["watcher_count"], 2)
        self.assertIn("2 autosave watchery", result["autosave"]["runtime"]["warning"])
        self.assertNotIn("citlivy obsah", json.dumps(result, ensure_ascii=False))
        self.assertEqual(result["active_project"]["name"], "Cockpit Recovery centrum")
        self.assertEqual(result["handoffs"][0]["title"], "Recovery test")
        self.assertIn("codex resume --last", [item["command"] for item in result["commands"]])

    def test_session_autosave_cleanup_action_requires_confirmation_to_delete(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            old_snapshot = root / "session_20000101_120000.jsonl"
            old_snapshot.write_text("citlivy obsah autosave se nesmi cist\n", encoding="utf-8")

            preview = session_autosave_cleanup_action(
                {"retention_days": 3, "keep_latest_snapshots": 0},
                autosave_dir=root,
                autosave_runtime_getter=lambda **_kwargs: SimpleNamespace(
                    ok=False,
                    watcher_running=True,
                    watcher_count=2,
                    watcher_pids=(111, 222),
                    warning="bezi 2 autosave watchery",
                ),
            )
            blocked = session_autosave_cleanup_action(
                {
                    "retention_days": 3,
                    "keep_latest_snapshots": 0,
                    "apply": True,
                    "confirmation_text": "spatne",
                },
                autosave_dir=root,
            )

            self.assertTrue(preview["ok"])
            self.assertEqual(preview["status"], "dry_run")
            self.assertEqual(preview["plan"]["delete_count"], 1)
            self.assertEqual(preview["runtime"]["watcher_count"], 2)
            self.assertIn("očekáván je právě jeden", preview["message"])
            self.assertEqual(preview["plan"]["delete_files"], [])
            self.assertEqual(len(preview["plan"]["delete_files_sample"]), 1)
            self.assertFalse(blocked["ok"])
            self.assertEqual(blocked["status"], "confirmation_required")
            self.assertTrue(old_snapshot.exists())
            self.assertNotIn("citlivy obsah", json.dumps(preview, ensure_ascii=False))

    def test_session_autosave_cleanup_action_deletes_old_snapshots_after_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            old_snapshot = root / "session_20000101_120000.jsonl"
            latest = root / "latest_session.jsonl"
            old_snapshot.write_text("old", encoding="utf-8")
            latest.write_text("latest", encoding="utf-8")

            result = session_autosave_cleanup_action(
                {
                    "retention_days": 3,
                    "keep_latest_snapshots": 0,
                    "apply": True,
                    "confirmation_text": "SMAZAT STARE AUTOSAVE",
                },
                autosave_dir=root,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["status"], "applied")
            self.assertEqual(result["removed"], 1)
            self.assertFalse(old_snapshot.exists())
            self.assertTrue(latest.exists())

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

    def test_project_audit_report_status_returns_report_without_saving_by_default(self) -> None:
        fake_result = SimpleNamespace(mode="quick", saved_path=None)
        with (
            patch("app.cockpit.run_samantha_project_audit", return_value=fake_result) as run_mock,
            patch("app.cockpit.format_project_audit_result", return_value="REPORT TEXT") as format_mock,
        ):
            result = project_audit_report_status(mode="quick", save=False)

        self.assertTrue(result["ok"])
        self.assertEqual(result["message"], "Systémový audit načten.")
        self.assertEqual(result["mode"], "quick")
        self.assertEqual(result["saved_path"], "")
        self.assertEqual(result["report"], "REPORT TEXT")
        run_mock.assert_called_once_with(mode="quick", save=False)
        format_mock.assert_called_once_with(fake_result)

    def test_project_audit_report_status_can_save_full_report(self) -> None:
        fake_result = SimpleNamespace(
            mode="full",
            saved_path=Path("memory/reports/systemovy_audit_projekty_tooly_vrstvy_20260623_180000.txt"),
        )
        with (
            patch("app.cockpit.run_samantha_project_audit", return_value=fake_result) as run_mock,
            patch("app.cockpit.format_project_audit_result", return_value="FULL REPORT"),
        ):
            result = project_audit_report_status(mode="full", save=True)

        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "full")
        self.assertIn("systemovy_audit_projekty_tooly_vrstvy_20260623_180000.txt", result["saved_path"])
        self.assertIn("Systémový audit uložen", result["message"])
        self.assertEqual(result["report"], "FULL REPORT")
        run_mock.assert_called_once_with(mode="full", save=True)

    def test_project_audit_recent_reports_lists_audit_files(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            reports_dir = Path(temp_dir)
            valid_names = [
                "systemovy_audit_projekty_tooly_vrstvy_20260623_180000.txt",
                "systemovy_audit_projekty_tooly_vrstvy_20260623_181000.txt",
            ]
            for name in valid_names:
                (reports_dir / name).write_text("audit\n", encoding="utf-8")
            (reports_dir / "jiny_report.txt").write_text("ignore\n", encoding="utf-8")

            result = project_audit_recent_reports(limit=10, reports_dir=reports_dir)

        self.assertTrue(result["ok"])
        self.assertEqual({item["name"] for item in result["reports"]}, set(valid_names))
        self.assertTrue(all(item["size"] > 0 for item in result["reports"]))

    def test_project_audit_report_file_status_reads_only_whitelisted_report_names(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            reports_dir = Path(temp_dir)
            valid_name = "systemovy_audit_projekty_tooly_vrstvy_20260623_180000.txt"
            (reports_dir / valid_name).write_text("bezpecny report\n", encoding="utf-8")

            valid = project_audit_report_file_status(name=valid_name, reports_dir=reports_dir)
            invalid = project_audit_report_file_status(name="../secret.txt", reports_dir=reports_dir)

        self.assertTrue(valid["ok"])
        self.assertEqual(valid["report"], "bezpecny report\n")
        self.assertFalse(invalid["ok"])
        self.assertEqual(invalid["message"], "Neplatny nazev reportu.")

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
        self.assertEqual(result["notes"][0]["triage"]["classification"], "nápad")
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

    def test_urgent_reminders_status_reports_pending_icloud_download(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "Shortcuts"
            inbox.mkdir()
            index_path = root / "private" / "urgent_reminders" / "index.json"
            reminder = SimpleNamespace(
                reminder_number=21,
                priority="urgent",
                status="open",
                created_at="2026-07-26 10:09:26",
                modified_at="2026-07-26 10:09:26",
                title="Samantha důležité připomenutí",
                summary="Poslední platný index.",
                body_text="Poslední platný index.",
                size_bytes=135,
            )

            def pending_sync(**kwargs: object) -> list[SimpleNamespace]:
                diagnostics = kwargs["sync_diagnostics"]
                assert isinstance(diagnostics, dict)
                diagnostics.update(
                    {
                        "checked_file_count": 22,
                        "readable_file_count": 21,
                        "pending_download_count": 1,
                    }
                )
                return [reminder]

            with patch(
                "app.cockpit.sync_urgent_reminders_index",
                side_effect=pending_sync,
            ):
                result = urgent_reminders_status(inbox_dir=inbox, index_path=index_path)

        self.assertTrue(result["ok"])
        self.assertTrue(result["sync_pending"])
        self.assertEqual(result["pending_download_count"], 1)
        self.assertIn("čeká na stažení", result["message"])
        self.assertEqual(result["counts"]["open"], 1)
        self.assertEqual(result["items"][0]["reminder_number"], 21)
        self.assertNotIn("source_path", result["items"][0])

    def test_urgent_reminders_status_reports_stuck_icloud_download_after_five_minutes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "Shortcuts"
            inbox.mkdir()
            index_path = root / "private" / "urgent_reminders" / "index.json"

            def stuck_sync(**kwargs: object) -> list[SimpleNamespace]:
                diagnostics = kwargs["sync_diagnostics"]
                assert isinstance(diagnostics, dict)
                diagnostics.update(
                    {
                        "checked_file_count": 1,
                        "readable_file_count": 0,
                        "pending_download_count": 1,
                        "pending_oldest_age_seconds": 301,
                    }
                )
                return []

            with patch("app.cockpit.sync_urgent_reminders_index", side_effect=stuck_sync):
                result = urgent_reminders_status(inbox_dir=inbox, index_path=index_path)

        self.assertTrue(result["ok"])
        self.assertTrue(result["sync_pending"])
        self.assertTrue(result["sync_stuck"])
        self.assertEqual(result["pending_oldest_age_seconds"], 301)
        self.assertIn("iCloud stažení je zaseknuté", result["message"])
        self.assertNotIn("kontrola se automaticky zopakuje", result["message"])

    def test_urgent_reminder_deliver_action_returns_redacted_idempotent_receipt(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            index_path = Path(temp_dir) / "private" / "urgent_reminders" / "index.json"
            payload = {
                "text": "Soukromý obsah nesmí být v potvrzení.",
                "created_at": "2026-08-02T15:20:00+02:00",
            }

            first = urgent_reminder_deliver_action(payload, index_path=index_path)
            duplicate = urgent_reminder_deliver_action(payload, index_path=index_path)
            stored = json.loads(index_path.read_text(encoding="utf-8"))["reminders"]

        self.assertTrue(first["ok"])
        self.assertEqual(first["status"], "created")
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(first["reminder_number"], duplicate["reminder_number"])
        self.assertNotIn(payload["text"], json.dumps(first, ensure_ascii=False))
        self.assertEqual(len(stored), 1)

    def test_quick_note_deliver_action_returns_redacted_idempotent_receipt_and_detail(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            index_path = root / "private" / "quick_notes" / "index.json"
            inbox = root / "missing-icloud"
            payload = {
                "text": "Soukromý obsah QN nesmí být v potvrzení.",
                "created_at": "2026-08-06T09:15:00+02:00",
            }

            first = quick_note_deliver_action(payload, index_path=index_path)
            duplicate = quick_note_deliver_action(payload, index_path=index_path)
            detail = quick_note_detail_status(
                note_number=int(first["note_number"]),
                inbox_dir=inbox,
                index_path=index_path,
            )
            stored = json.loads(index_path.read_text(encoding="utf-8"))["notes"]

        self.assertTrue(first["ok"])
        self.assertEqual(first["status"], "created")
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(first["note_number"], duplicate["note_number"])
        self.assertNotIn(payload["text"], json.dumps(first, ensure_ascii=False))
        self.assertEqual(len(stored), 1)
        self.assertTrue(detail["ok"])
        self.assertEqual(detail["body_text"], payload["text"])

    def test_quick_note_deliver_action_rejects_empty_text(self) -> None:
        result = quick_note_deliver_action({"text": ""})
        null_result = quick_note_deliver_action({"text": None})

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "delivery_failed")
        self.assertFalse(null_result["ok"])

    def test_urgent_reminder_deliver_action_rejects_empty_text(self) -> None:
        result = urgent_reminder_deliver_action({"text": ""})
        null_result = urgent_reminder_deliver_action({"text": None})

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "delivery_failed")
        self.assertFalse(null_result["ok"])

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

    def test_quick_notes_status_falls_back_to_action_preclassification(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "Shortcuts"
            inbox.mkdir()
            index_path = root / "private" / "quick_notes" / "index.json"
            (inbox / "library_url_note.md").write_text(
                "# Samantha inbox\n\nDatum: 2026-06-22 19:44:26\n\nPoznámka:\nJe třeba opravit knihovnu, aby při načítání URL článku automaticky uložila článek.\n",
                encoding="utf-8",
            )

            result = quick_notes_status(inbox_dir=inbox, index_path=index_path)
            detail = quick_note_detail_status(note_number=1, inbox_dir=inbox, index_path=index_path)

        self.assertEqual(result["notes"][0]["triage"]["classification"], "archiv/znalostní databáze")
        self.assertEqual(result["notes"][0]["triage"]["confidence"], "medium")
        self.assertEqual(result["notes"][0]["triage"]["risk"], "medium")
        self.assertEqual(detail["triage"]["classification"], "archiv/znalostní databáze")

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
            tomorrow = (date.today() + timedelta(days=1)).isoformat()
            path.write_text(
                json.dumps(
                    {
                        "reminders": [
                            self.reminder("mark-id", "Označit", date.today().isoformat()),
                            self.reminder("other-id", "Nechat", tomorrow),
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

    def test_reminder_source_detail_loads_email_archive_with_redacted_sender(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            reminders_path = root / "reminders.json"
            archive_dir = root / "email_archive"
            raw_identifier = "1234567890"
            archive_id = (
                f"email-155924-upozorneni-na-dluznou-castku-{raw_identifier}"
            )
            email_dir = archive_dir / archive_id
            (email_dir / "attachments").mkdir(parents=True)
            (email_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "archive_id": archive_id,
                        "subject": "Upozornění na dlužnou částku",
                        "from": "ČEZ Prodej, a.s. <upominani@example.com>",
                        "date": "Thu, 11 Jun 2026 16:09:42 +0200 (CEST)",
                        "archived_at": "2026-06-11T14:30:52+00:00",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (email_dir / "attachments" / "attachments.json").write_text(
                json.dumps(
                    {
                        "attachments": [
                            {
                                "filename": "upominka.pdf",
                                "content_type": "application/pdf",
                                "size_bytes": 12345,
                                "part_id": "2",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            vault_dir = root / "documents"
            vault_file = vault_dir / "vault" / "insurance" / "upominka.pdf"
            vault_file.parent.mkdir(parents=True)
            vault_file.write_bytes(b"%PDF-fixture")
            index_dir = vault_dir / "index"
            index_dir.mkdir()
            (index_dir / "documents_index.jsonl").write_text(
                json.dumps(
                    {
                        "document_id": (
                            f"doc-email-155924-upominka-{raw_identifier}"
                        ),
                        "title": (
                            "E-mail UID 155924 příloha upomínka "
                            f"{raw_identifier}"
                        ),
                        "original_filename": f"upominka-{raw_identifier}.pdf",
                        "domain": "insurance",
                        "document_type": "invoice",
                        "reading_status": "ok",
                        "stored_path": str(vault_file),
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            reminders_path.write_text(
                json.dumps(
                    {
                        "reminders": [
                            {
                                **self.reminder(
                                    "archive-reminder",
                                    "Zaplatit podle e-mailu: ČEZ Prodej, a.s. - Upozornění na dlužnou částku",
                                    "2026-05-31",
                                ),
                                "source": {
                                    "type": "email_archive",
                                    "uid": (
                                        "email-155924-upozorneni-na-dluznou-castku-"
                                        "[rodne cislo redigovano]"
                                    ),
                                    "date": "Thu, 11 Jun 2026 16:09:42 +0200 (CEST)",
                                    "sender": "ČEZ Prodej, a.s. <[e-mail redigovan]>",
                                },
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = reminder_source_detail_action(
                "archive-reminder",
                reminders_path=reminders_path,
                archive_directory=archive_dir,
                vault_dir=vault_dir,
            )

        payload = json.dumps(result, ensure_ascii=False)
        self.assertTrue(result["ok"])
        self.assertEqual(result["kind"], "email_archive")
        self.assertEqual(result["email"]["provider"], "archive")
        self.assertIn("[rodne cislo redigovano]", result["email"]["uid"])
        self.assertRegex(
            result["email"]["archive_ref"],
            r"^archive-ref-[0-9a-f]{16}$",
        )
        self.assertEqual(result["email"]["subject"], "Upozornění na dlužnou částku")
        self.assertIn("ČEZ Prodej", result["email"]["sender"])
        self.assertIn("[e-mail redigovan]", result["email"]["sender"])
        self.assertEqual(result["email"]["attachments"][0]["filename"], "upominka.pdf")
        self.assertEqual(len(result["email"]["vault_attachments"]), 1)
        self.assertTrue(result["email"]["vault_attachments"][0]["can_open"])
        self.assertNotIn(raw_identifier, payload)
        self.assertNotIn("upominani@example.com", payload)

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

    def test_resolve_openable_document_file_allows_indexed_vault_image(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            index = vault / "index"
            stored_dir = vault / "vault" / "insurance" / "doc-image"
            stored_dir.mkdir(parents=True)
            image = stored_dir / "scan.jpeg"
            image.write_bytes(b"\xff\xd8\xff\xe0test")
            index.mkdir(parents=True)
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "doc-image",
                        "title": "Sken",
                        "stored_path": str(image),
                    }
                ],
            )

            result = cockpit_module.resolve_openable_document_file("doc-image", vault_dir=vault)

            self.assertTrue(result["ok"])
            self.assertEqual(result["path"], image.resolve())
            self.assertEqual(result["viewer_kind"], "image")
            self.assertEqual(result["content_type"], "image/jpeg")

    def test_resolve_openable_purchase_pdf_uses_purchase_archive_only(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            purchases = root / "purchases" / "2026" / "2026-05-23_dolphin-e20"
            documents = purchases / "documents"
            documents.mkdir(parents=True)
            pdf = documents / "invoice.pdf"
            pdf.write_bytes(b"%PDF-1.4\n")
            (purchases / "invoice_manifest.json").write_text(
                json.dumps(
                    {
                        "subject": "Faktura a expedice zboží",
                        "attachments": [{"filename": "invoice.pdf", "stored_path": str(pdf)}],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            purchase_id = "purchase-2026-2026-05-23_dolphin-e20"
            purchase_ref = cockpit_module.purchase_reference(purchase_id)

            result = cockpit_module.resolve_openable_purchase_pdf(purchase_ref, purchases_dir=root / "purchases")

            self.assertTrue(result["ok"])
            self.assertEqual(result["purchase_ref"], purchase_ref)
            self.assertEqual(result["path"], pdf.resolve())

    def test_resolve_openable_purchase_pdf_rejects_pdf_outside_archive(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            outside = root / "outside.pdf"
            outside.write_bytes(b"%PDF-1.4\n")
            purchases = root / "purchases" / "2026" / "2026-05-23_dolphin-e20"
            purchases.mkdir(parents=True)
            (purchases / "invoice_manifest.json").write_text(
                json.dumps(
                    {
                        "subject": "Faktura",
                        "attachments": [{"filename": "invoice.pdf", "stored_path": str(outside)}],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = cockpit_module.resolve_openable_purchase_pdf(
                "purchase-2026-2026-05-23_dolphin-e20",
                purchases_dir=root / "purchases",
            )

            self.assertFalse(result["ok"])
            self.assertIn("nákupním archivu", result["message"])

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

    def test_document_reader_page_can_show_inline_image(self) -> None:
        page = cockpit_module.document_reader_page_html("doc-image", "Sken", viewer_kind="image")

        self.assertIn('class="document-image"', page)
        self.assertIn("/documents/pdf?document_id=doc-image", page)
        self.assertIn("Otevřít obrázek", page)
        self.assertNotIn("<iframe", page)

    def test_purchase_reader_page_contains_inline_purchase_pdf(self) -> None:
        page = cockpit_module.purchase_reader_page_html("purref-test", "Faktura & záruka")

        self.assertIn("Nákup / záruka", page)
        self.assertIn("Zpět do Cockpitu", page)
        self.assertIn("/purchases/pdf?purchase_id=purref-test", page)
        self.assertIn("Faktura &amp; záruka", page)

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

    def test_document_search_invoice_query_prioritizes_invoice_over_quote(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "doc-nabidka",
                        "title": "Nabídka RD Jizerní Vtelno",
                        "original_filename": "nabidka_jizerni_vtelno.pdf",
                        "domain": "jizerni-vtelno",
                        "document_type": "price_quote",
                        "counterparty": "František Kanta",
                        "related_asset": "RD Jizerní Vtelno",
                        "stored_path": "data/private/documents/vault/jizerni-vtelno/doc-nabidka/nabidka.pdf",
                    },
                    {
                        "document_id": "doc-faktura",
                        "title": "Faktura RD Jizerní Vtelno",
                        "original_filename": "faktura_jizerni_vtelno.pdf",
                        "domain": "jizerni-vtelno",
                        "document_type": "invoice",
                        "counterparty": "František Kanta",
                        "related_asset": "RD Jizerní Vtelno",
                        "stored_path": "data/private/documents/vault/jizerni-vtelno/doc-faktura/faktura.pdf",
                    },
                    {
                        "document_id": "doc-jina-faktura",
                        "title": "Faktura servis auta",
                        "original_filename": "faktura_auto.pdf",
                        "domain": "car",
                        "document_type": "invoice",
                        "counterparty": "Servis",
                        "related_asset": "auto",
                        "stored_path": "data/private/documents/vault/car/doc-jina-faktura/faktura.pdf",
                    },
                ],
            )
            self.write_jsonl(
                index / "text_index.jsonl",
                [
                    {
                        "document_id": "doc-nabidka",
                        "text": "Jizerní Vtelno " * 20,
                    },
                    {
                        "document_id": "doc-faktura",
                        "text": "Daňový doklad k domu Jizerní Vtelno.",
                    },
                    {
                        "document_id": "doc-jina-faktura",
                        "text": "Faktura za servis.",
                    },
                ],
            )

            result = search_document_index("faktura Jizerní Vtelno", vault_dir=vault, limit=3)

            self.assertEqual(result["count"], 2)
            self.assertEqual(result["results"][0]["document_id"], "doc-faktura")
            self.assertEqual(result["results"][0]["document_type"], "invoice")
            self.assertEqual(result["results"][1]["document_id"], "doc-nabidka")
            self.assertNotIn("doc-jina-faktura", [item["document_id"] for item in result["results"]])

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

    def test_document_search_includes_private_purchase_manifests(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            (vault / "index").mkdir(parents=True)
            purchases = root / "purchases" / "2026" / "2026-05-23_dolphin-e20"
            purchases.mkdir(parents=True)
            manifest = {
                "uid": "14095",
                "date": "Mon, 25 May 2026 14:59:16 +0200",
                "sender": "ROBOT WORLD <info@robotworld.example>",
                "subject": "Faktura a expedice zboží",
                "attachments": [
                    {
                        "filename": "inv_7026008712.pdf",
                        "content_type": "application/pdf",
                        "stored_path": "data/private/purchases/2026/2026-05-23_dolphin-e20/documents/inv.pdf",
                    }
                ],
            }
            (purchases / "invoice_manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False),
                encoding="utf-8",
            )

            result = search_document_index("dolphin", vault_dir=vault, purchases_dir=root / "purchases")

            self.assertTrue(result["ok"])
            self.assertEqual(result["count"], 1)
            found = result["results"][0]
            self.assertEqual(found["source_type"], "purchase")
            self.assertEqual(found["source_label"], "Nákup / záruka")
            self.assertEqual(found["domain"], "purchases")
            self.assertEqual(found["document_type"], "purchase_invoice")
            self.assertIn("2026-05-23_dolphin-e20", found["related_asset"])
            self.assertIn("[e-mail redigovan]", found["counterparty"])
            self.assertNotIn("robotworld.example", found["counterparty"])

    def test_document_search_purchase_alias_finds_pool_robot(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            (vault / "index").mkdir(parents=True)
            purchases = root / "purchases" / "2026" / "2026-05-23_dolphin-e20"
            purchases.mkdir(parents=True)
            (purchases / "invoice_manifest.json").write_text(
                json.dumps(
                    {
                        "subject": "Faktura a expedice zboží",
                        "attachments": [{"filename": "invoice.pdf"}],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = search_document_index("bazénový robot", vault_dir=vault, purchases_dir=root / "purchases")

            self.assertEqual(result["count"], 1)
            self.assertEqual(result["results"][0]["source_type"], "purchase")

    def test_cockpit_html_contains_document_search_controls(self) -> None:
        self.assertIn("Najít dokument", COCKPIT_HTML)
        self.assertIn("documentSearchInput", COCKPIT_HTML)
        self.assertIn("/api/documents/search", COCKPIT_HTML)
        self.assertIn("Rozbalit", COCKPIT_HTML)
        self.assertIn("Sbalit", COCKPIT_HTML)
        self.assertIn("search-detail hidden", COCKPIT_HTML)
        self.assertIn("Otevřít / číst", COCKPIT_HTML)
        self.assertIn("Otevřít / číst PDF", COCKPIT_HTML)
        self.assertIn("Otevřít nákupní PDF", COCKPIT_HTML)
        self.assertIn("openPurchaseForReading", COCKPIT_HTML)
        self.assertIn("/purchases/read?purchase_id=", COCKPIT_HTML)
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
        self.assertIn("Nákup / záruka", COCKPIT_HTML)
        self.assertIn("source_type", COCKPIT_HTML)

    def test_cockpit_html_contains_web_apps_modal(self) -> None:
        self.assertIn("Webové aplikace", COCKPIT_HTML)
        self.assertIn("webAppsModal", COCKPIT_HTML)
        self.assertIn("/api/web-apps", COCKPIT_HTML)
        self.assertIn("/api/desktop-apps/open", COCKPIT_HTML)
        self.assertIn("openWebApp(app)", COCKPIT_HTML)
        self.assertIn("openDesktopApp(app)", COCKPIT_HTML)
        self.assertIn("SamanthaWebApp_", COCKPIT_HTML)
        self.assertNotIn('target = "_blank"', COCKPIT_HTML)
        self.assertIn("Zavřít", COCKPIT_HTML)

    def test_web_apps_catalog_contains_vocabulary_desktop_trainers(self) -> None:
        apps = {item["id"]: item for item in web_apps_catalog()["apps"]}

        self.assertEqual(apps["vocabulary-it-trainer"]["launch_type"], "desktop")
        self.assertEqual(apps["vocabulary-fr-trainer"]["launch_type"], "desktop")
        self.assertIn("Vocabulary IT", apps["vocabulary-it-trainer"]["title"])
        self.assertIn("Vocabulary FR", apps["vocabulary-fr-trainer"]["title"])

    def test_web_apps_catalog_contains_multilo_desktop_app(self) -> None:
        apps = {item["id"]: item for item in web_apps_catalog()["apps"]}

        self.assertEqual(apps["multilo"]["launch_type"], "desktop")
        self.assertEqual(apps["multilo"]["title"], "MultiLO")

    def test_family_video_organizer_prefers_complete_private_package(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            private_root = root / "private-package"
            fallback_root = root / "fallback"
            private_root.mkdir()
            fallback_root.mkdir()
            for filename in ("index.html", "app.js", "styles.css", "videos-data.js"):
                (private_root / filename).write_text(filename, encoding="utf-8")

            selected = cockpit_module.family_video_organizer_app_root(
                private_root=private_root,
                fallback_root=fallback_root,
            )

            self.assertEqual(selected, private_root)

    def test_family_video_organizer_falls_back_without_private_data(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            private_root = root / "incomplete-private-package"
            fallback_root = root / "fallback"
            private_root.mkdir()
            fallback_root.mkdir()
            (private_root / "index.html").write_text("index", encoding="utf-8")

            selected = cockpit_module.family_video_organizer_app_root(
                private_root=private_root,
                fallback_root=fallback_root,
            )

            self.assertEqual(selected, fallback_root)

    def test_family_video_organizer_labels_the_default_dataset(self) -> None:
        app_source = (
            cockpit_module.FAMILY_VIDEO_ORGANIZER_FALLBACK_ROOT / "app.js"
        ).read_text(encoding="utf-8")

        self.assertIn("elements.activeDataset.textContent = state.videos.length", app_source)
        self.assertIn("${state.project} · ${state.videos.length} záznamů", app_source)

    def test_open_vocabulary_it_uses_same_python_as_vscode(self) -> None:
        calls: list[list[str]] = []

        def fake_runner(args, **kwargs):
            calls.append(args)
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        result = open_desktop_app_action({"app_id": "vocabulary-it-trainer"}, runner=fake_runner)

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "launched")
        self.assertEqual(calls[0][0], "/usr/bin/osascript")
        self.assertIn("VocabularyIT", calls[0][2])
        self.assertIn("vocab_trainer_it.py", calls[0][2])
        self.assertIn("/usr/local/bin/python3.12", calls[0][2])
        self.assertNotIn("; python3 ", calls[0][2])

    def test_open_vocabulary_fr_uses_same_python_as_vscode(self) -> None:
        calls: list[list[str]] = []

        def fake_runner(args, **kwargs):
            calls.append(args)
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        result = open_desktop_app_action({"app_id": "vocabulary-fr-trainer"}, runner=fake_runner)

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "launched")
        self.assertIn("/usr/local/bin/python3.12", calls[0][2])
        self.assertNotIn("; python3 ", calls[0][2])

    def test_open_multilo_uses_python_312_and_cockpit_entrypoint(self) -> None:
        calls: list[list[str]] = []

        def fake_runner(args, **kwargs):
            calls.append(args)
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        result = open_desktop_app_action({"app_id": "multilo"}, runner=fake_runner)

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "launched")
        self.assertEqual(calls[0][0], "/usr/bin/osascript")
        self.assertIn("MultiLO", calls[0][2])
        self.assertIn("step2_cockpit.py", calls[0][2])
        self.assertIn("/usr/local/bin/python3.12", calls[0][2])
        self.assertNotIn("; python3 ", calls[0][2])

    def test_open_desktop_app_rejects_missing_configured_interpreter(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            script = root / "trainer.py"
            script.write_text("print('test')\n", encoding="utf-8")
            app = {
                "id": "test-trainer",
                "title": "Test trainer",
                "description": "Test",
                "kind": "desktopová aplikace",
                "working_dir": root,
                "script": script,
                "interpreter": root / "missing-python",
            }
            with patch("app.cockpit.desktop_app_by_id", return_value=app):
                result = open_desktop_app_action(
                    {"app_id": "test-trainer"},
                    runner=lambda *args, **kwargs: self.fail("should not launch"),
                )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "missing_app_interpreter")

    def test_open_desktop_app_action_rejects_unknown_app(self) -> None:
        result = open_desktop_app_action(
            {"app_id": "not-allowed"},
            runner=lambda *args, **kwargs: self.fail("should not launch"),
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "unknown_desktop_app")

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
            self.assertTrue(result["changed"])
            self.assertFalse(result["idempotent_replay"])
            self.assertEqual(decisions["abc123"]["action"], "process")
            self.assertEqual(decisions["abc123"]["item"]["uid"], "14157")

    def test_email_decision_frontend_sends_repository_operation_id(self) -> None:
        self.assertIn("window.crypto.randomUUID", EMAIL_PROCESSING_HTML)
        self.assertIn("operation_id: operationId", EMAIL_PROCESSING_HTML)

    def test_email_done_flag_action_is_seznam_only_and_server_verified(self) -> None:
        provider = _FakeArchiveProvider(_archive_source_without_attachment())

        result = set_email_processing_done_flag(
            provider="Seznam",
            folder="INBOX",
            uid="155560",
            done=True,
            seznam_provider_factory=lambda: provider,
        )

        self.assertTrue(result["ok"])
        self.assertTrue(result["flagged"])
        self.assertEqual(
            provider.flag_calls,
            [{"uid": "155560", "folder": "INBOX", "flagged": True}],
        )

        rejected = set_email_processing_done_flag(
            provider="iCloud",
            folder="INBOX",
            uid="14157",
            done=True,
            seznam_provider_factory=lambda: self.fail("Seznam provider nesmí být vytvořen"),
        )
        self.assertFalse(rejected["ok"])
        self.assertIn("pouze pro Seznam", rejected["message"])

    def test_email_done_flag_has_explicit_ui_action_and_registry_card(self) -> None:
        self.assertIn('fetch("/api/email-processing/done-flag"', EMAIL_PROCESSING_HTML)
        self.assertIn('done.addEventListener("click"', EMAIL_PROCESSING_HTML)
        self.assertIn('id="doneEmail"', EMAIL_PROCESSING_HTML)
        self.assertIn('dialogWindow.confirm(prompt)', EMAIL_PROCESSING_HTML)
        card = next(
            item for item in COCKPIT_POST_ACTIONS if item["path"] == "/api/email-processing/done-flag"
        )
        self.assertEqual(card["risk"], "private_write")
        self.assertEqual(card["confirmation"], "explicit_ui_action_reversible")
        self.assertEqual(card["handler_name"], "set_email_processing_done_flag")

    def test_seznam_header_flag_is_exposed_to_email_processing_ui(self) -> None:
        item = email_header_to_processing_item(
            EmailHeader(
                internal_id="155560",
                date="Wed, 15 Jul 2026 10:00:00 +0200",
                sender="Sender <sender@example.com>",
                subject="Zpracovaný e-mail",
                source="Seznam",
                folder="INBOX",
                flagged=True,
            ),
            "Seznam",
        )

        self.assertTrue(item["imap_flagged"])

    def test_email_decision_operation_replay_returns_original_action(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "email_processing_decisions.json"
            first = save_email_processing_decision(
                item_id="abc123",
                action="process",
                item={"uid": "14157"},
                path=path,
                operation_id="request-one",
            )
            replay = save_email_processing_decision(
                item_id="abc123",
                action="trash_requested",
                item={"uid": "14157"},
                path=path,
                operation_id="request-one",
            )

            self.assertEqual(first["action"], "process")
            self.assertEqual(replay["action"], "process")
            self.assertTrue(replay["idempotent_replay"])

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

    def test_document_intake_email_scan_skips_library_exports(self) -> None:
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
                            internal_id="18001",
                            date="Sun, 21 Jun 2026 10:00:00 +0200",
                            sender="Míla <mila@example.com>",
                            subject="[SamanthaLibraryExport] Testovací článek",
                            attachments=(
                                EmailAttachmentMeta(
                                    filename="article_export.pdf",
                                    content_type="application/pdf",
                                    size_bytes=42_000,
                                    part_id="2",
                                    content_id="",
                                    disposition="attachment",
                                ),
                            ),
                        )
                    ]
                ),
                seznam_provider_factory=lambda: _FakeEmailProvider([]),
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["raw_count"], 0)
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["skipped_library_export_count"], 1)

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

    def test_new_email_headers_overview_skips_library_exports(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            result = new_email_headers_overview(
                limit_per_source=50,
                since="2026-06-01T07:00:00+00:00",
                decisions_path=Path(temp_dir) / "email_processing_decisions.json",
                actions_path=Path(temp_dir) / "email_work_queue_actions.jsonl",
                icloud_provider_factory=lambda: _FakeEmailProvider(
                    [
                        EmailHeader(
                            internal_id="18001",
                            date="Sun, 21 Jun 2026 10:00:00 +0200",
                            sender="Míla <mila@example.com>",
                            subject="[SamanthaLibraryExport] Testovací článek",
                        )
                    ]
                ),
                seznam_provider_factory=lambda: _FakeEmailProvider([]),
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["items"], [])
        self.assertEqual(result["skipped_library_export_count"], 1)

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

    def test_document_intake_email_scan_suppresses_completed_item_by_source_key(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            actions_path = Path(temp_dir) / "email_work_queue_actions.jsonl"
            source_key = cockpit_module.email_processing_stable_key("Seznam", "INBOX", "155924")
            completed_id = email_processing_item_id("", "Seznam", "INBOX", "155924", "", "")
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
                                "uid": "155924",
                                "status": "saved",
                            }
                        ],
                    }
                ],
            )

            result = document_intake_email_scan_status(
                limit_per_source=10,
                since="2026-06-11T13:00:00+00:00",
                days=0,
                known_ids={source_key},
                decisions_path=Path(temp_dir) / "email_processing_decisions.json",
                actions_path=actions_path,
                icloud_provider_factory=lambda: _FakeEmailProvider([]),
                seznam_provider_factory=lambda: _FakeEmailProvider(
                    [
                        EmailHeader(
                            internal_id="155924",
                            date="Thu, 11 Jun 2026 16:09:42 +0200",
                            sender="ČEZ Prodej <billing@example.com>",
                            subject="Upozornění na dlužnou částku",
                            attachments=(
                                EmailAttachmentMeta(
                                    filename="upominka.pdf",
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
        self.assertEqual(result["suppressed_known_ids"], [source_key])

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
        self.assertEqual(item["source_key"], "icloud|inbox|14157")
        self.assertNotEqual(item["id"], item["legacy_id"])
        self.assertTrue(item["work_ref"].startswith("emailworkref-"))
        self.assertEqual(item["work_state"], "new")
        self.assertEqual(item["work_action"], "")

    def test_email_header_processing_item_marks_library_export(self) -> None:
        item = email_header_to_processing_item(
            EmailHeader(
                internal_id="18001",
                date="Sun, 21 Jun 2026 10:00:00 +0200",
                sender="Míla <mila@example.com>",
                subject="[SamanthaLibraryExport] Testovací článek",
                attachments=(
                    EmailAttachmentMeta(
                        filename="article_export.pdf",
                        content_type="application/pdf",
                        size_bytes=42_000,
                        part_id="2",
                        content_id="",
                        disposition="attachment",
                    ),
                ),
            ),
            "iCloud",
        )

        self.assertTrue(item["samantha_library_export"])
        self.assertTrue(cockpit_module.email_processing_item_is_library_export(item))

    def test_cockpit_email_intake_refresh_cleans_candidates_by_source_key(self) -> None:
        self.assertIn("if (!silent) {\n          runEmailIntakeMonitor();\n        }", COCKPIT_HTML)
        self.assertIn("if (emailIntakeMonitorInFlight) return", COCKPIT_HTML)
        self.assertIn(
            'fetchJsonWithTimeout("/api/documents/intake-email-scan", 30000',
            COCKPIT_HTML,
        )
        self.assertIn('fetchJsonWithTimeout("/api/status", 15000)', COCKPIT_HTML)
        self.assertIn("const sourceKey = emailIntakeSourceKey(item);", COCKPIT_HTML)
        self.assertIn("if (sourceKey) byId.set(sourceKey, item);", COCKPIT_HTML)
        self.assertIn("!suppressed.has(sourceKey)", COCKPIT_HTML)

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
        self.assertTrue(result["items"][0]["work_ref"].startswith("emailworkref-"))
        self.assertEqual(result["items"][0]["work_state"], "queued")
        self.assertEqual(result["items"][0]["work_action"], "process")
        self.assertIn({"id": "invoice", "label": "Faktury / e-shopy"}, result["items"][0]["batch_groups"])

    def test_email_processing_pending_work_items_skips_outbound_folders(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "email_processing_decisions.json"
            save_email_processing_decision(
                item_id="sent-1",
                action="process",
                item={
                    "id": "sent-1",
                    "category": "úřady/daně",
                    "provider": "iCloud",
                    "folder": "Sent Messages",
                    "uid": "1652",
                    "date": "Thu, 28 May 2026 13:32:11 +0200",
                    "subject": "Daň z nemovitých věcí 2025 - Finanční správa",
                },
                path=path,
            )
            save_email_processing_decision(
                item_id="inbox-1",
                action="process",
                item={
                    "id": "inbox-1",
                    "category": "úřady/daně",
                    "provider": "iCloud",
                    "folder": "INBOX",
                    "uid": "14438",
                    "date": "Thu, 28 May 2026 13:40:00 +0200",
                    "subject": "Daň z nemovitých věcí 2025 - Finanční správa",
                },
                path=path,
            )

            result = email_processing_pending_work_items(path=path)

        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["skipped_outbound_count"], 1)
        self.assertEqual(result["items"][0]["id"], "inbox-1")
        self.assertIn("Skryto odchozích", result["message"])

    def test_email_processing_pending_work_items_skips_library_exports(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "email_processing_decisions.json"
            save_email_processing_decision(
                item_id="library-export-1",
                action="process",
                item={
                    "id": "library-export-1",
                    "category": "faktury/e-shopy",
                    "provider": "iCloud",
                    "folder": "INBOX",
                    "uid": "18001",
                    "date": "Sun, 21 Jun 2026 10:00:00 +0200",
                    "subject": "[SamanthaLibraryExport] Testovací článek",
                    "pdf_attachment_count": 1,
                },
                path=path,
            )

            result = email_processing_pending_work_items(path=path)

        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["skipped_library_export_count"], 1)
        self.assertIn("Skryto exportů Knihovny", result["message"])

    def test_email_processing_classifies_tax_receipt_as_invoice(self) -> None:
        category = classify_email_processing_category(
            "Daňový doklad k objednávce č. 20727185",
            '"OPTIMTOP s.r.o." <neodpovidat@idoklad.cz>',
        )

        self.assertEqual(category, "faktury/e-shopy")

    def test_email_processing_pending_work_items_normalizes_saved_invoice_category(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "email_processing_decisions.json"
            save_email_processing_decision(
                item_id="invoice-1",
                action="process",
                item={
                    "id": "invoice-1",
                    "category": "úřady/daně",
                    "provider": "iCloud",
                    "folder": "INBOX",
                    "uid": "13549",
                    "sender": '"OPTIMTOP s.r.o." <neodpovidat@idoklad.cz>',
                    "subject": "Daňový doklad k objednávce č. 20727185",
                    "date": "Wed, 01 Apr 2026 06:18:38 +0000 (UTC)",
                    "pdf_attachment_count": 1,
                    "worklist_tags": ["invoice_over_2000"],
                },
                path=path,
            )

            result = email_processing_pending_work_items(path=path)

        self.assertEqual(result["count"], 1)
        item = result["items"][0]
        self.assertEqual(item["category"], "faktury/e-shopy")
        self.assertEqual(item["original_category"], "úřady/daně")
        self.assertNotIn({"id": "tax_office", "label": "Finanční správa"}, item["batch_groups"])
        self.assertIn({"id": "invoice_over_2000", "label": "Faktury nad 2000 Kč"}, item["batch_groups"])

    def test_email_processing_batch_groups_detects_reusable_blocks(self) -> None:
        tax_groups = email_processing_batch_groups(
            {
                "category": "úřady/daně",
                "sender": "Finanční správa ČR <daneelektronicky@fs.gov.cz>",
                "subject": "Informace pro placení daně",
                "pdf_attachment_count": 1,
            }
        )
        vak_groups = email_processing_batch_groups(
            {
                "category": "faktury/e-shopy",
                "sender": "vakmb <obchodni@vakmb.cz>",
                "subject": "Faktura VS 123",
                "worklist_tags": ["true_vak"],
                "pdf_attachment_count": 1,
            }
        )
        invoice_groups = email_processing_batch_groups(
            {
                "category": "faktury/e-shopy",
                "subject": "Faktura",
                "worklist_tags": ["invoice_over_2000"],
                "amount_scan": {"max_amount_czk": 2500},
                "pdf_attachment_count": 1,
            }
        )

        self.assertIn({"id": "tax_office", "label": "Finanční správa"}, tax_groups)
        self.assertIn({"id": "vak", "label": "VAK"}, vak_groups)
        self.assertIn({"id": "invoice_over_2000", "label": "Faktury nad 2000 Kč"}, invoice_groups)

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
            self.assertEqual(docs[0]["reading_status"], "needs_review")
            self.assertIn("faktura.pdf", docs[0]["original_filename"])
            self.assertEqual(result["items"][0]["attachments"][0]["document_id"], docs[0]["document_id"])
            self.assertEqual(result["items"][0]["attachments"][0]["document_ref"], document_reference(docs[0]["document_id"]))
            manifest = json.loads((documents_dir / "vault" / "other" / docs[0]["document_id"] / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["reading_status"], "needs_review")
            self.assertEqual(len(text_rows), 1)
            self.assertTrue(actions_path.exists())
            self.assertTrue(activity_state_path.exists())

    def test_process_email_work_queue_batch_imports_selected_pdf_and_image_attachments(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            archive_dir = root / "archive"
            documents_dir = root / "documents"
            decisions_path = root / "decisions.json"
            actions_path = root / "actions.jsonl"
            activity_state_path = root / "activity.json"
            raw_message = _raw_email_with_pdf_and_jpeg_attachments()
            provider = _FakeArchiveProvider(
                EmailArchiveSource(
                    uid="14482",
                    date="Tue, 16 Jun 2026 11:02:29 +0000",
                    sender="Sender <sender@example.com>",
                    subject="Faktura FAK_226210588",
                    body_text="Dobrý den, v příloze je faktura a fotografie.",
                    attachments=(
                        EmailAttachmentMeta(
                            filename="FAK_226210588.pdf",
                            content_type="application/octet-stream",
                            size_bytes=62,
                            part_id="2",
                            content_id="",
                            disposition="attachment",
                        ),
                        EmailAttachmentMeta(
                            filename="SL_Falta1.jpeg",
                            content_type="application/octet-stream",
                            size_bytes=16,
                            part_id="3",
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
                item_id="process-14482",
                action="process",
                item={"id": "process-14482", "provider": "iCloud", "folder": "INBOX", "uid": "14482"},
                path=decisions_path,
            )

            result = process_email_work_queue_batch(
                items=[
                    {
                        "id": "process-14482",
                        "provider": "iCloud",
                        "folder": "INBOX",
                        "uid": "14482",
                        "category": "faktury/e-shopy",
                        "queueDecision": "save",
                        "saveAttachments": ["2", "3"],
                        "attachment_metadata": [
                            {"part_id": "2", "filename": "FAK_226210588.pdf"},
                            {"part_id": "3", "filename": "SL_Falta1.jpeg"},
                        ],
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
            self.assertEqual(result["summary"]["errors"], 0)
            self.assertEqual(result["summary"]["attachments_imported"], 2)
            self.assertEqual(result["items"][0]["attachments_imported"], 2)
            self.assertEqual(read_email_processing_decisions(decisions_path), {})
            docs = self.read_jsonl(documents_dir / "index" / "documents_index.jsonl")
            self.assertEqual([doc["document_type"] for doc in docs], ["email-attachment-pdf", "email-attachment-image"])
            self.assertEqual(docs[1]["reading_status"], "needs_review")

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

    def test_preview_email_work_queue_attachment_matches_header_part_id_by_filename(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            preview_dir = Path(temp_dir) / "preview"
            provider = _FakeArchiveProvider(
                EmailArchiveSource(
                    uid="14482",
                    date="Tue, 16 Jun 2026 11:02:29 +0000",
                    sender="Sender <sender@example.com>",
                    subject="Faktura FAK_226210588",
                    body_text="Dobrý den, v příloze je faktura.",
                    attachments=(
                        EmailAttachmentMeta(
                            filename="FAK_226210588.pdf",
                            content_type="application/pdf",
                            size_bytes=62,
                            part_id="2",
                            content_id="",
                            disposition="attachment",
                        ),
                    ),
                    original_eml=_raw_email_with_pdf_attachment(filename="FAK_226210588.pdf"),
                    provider="icloud",
                    mailbox="INBOX",
                )
            )
            commands: list[list[str]] = []

            result = preview_email_work_queue_attachment_action(
                provider="iCloud",
                folder="INBOX",
                uid="14482",
                part_id="1.2",
                filename="FAK_226210588.pdf",
                preview_dir=preview_dir,
                opener=lambda command: commands.append(command),
                icloud_provider_factory=lambda: provider,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["filename"], "FAK_226210588.pdf")
            self.assertTrue(Path(commands[0][1]).exists())

    def test_preview_email_work_queue_attachment_opens_octet_stream_jpeg_by_filename(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            preview_dir = Path(temp_dir) / "preview"
            provider = _FakeArchiveProvider(
                EmailArchiveSource(
                    uid="14482",
                    date="Tue, 16 Jun 2026 11:02:29 +0000",
                    sender="Sender <sender@example.com>",
                    subject="Faktura FAK_226210588",
                    body_text="Dobrý den, v příloze je faktura a fotografie.",
                    attachments=(
                        EmailAttachmentMeta(
                            filename="SL_Falta1.jpeg",
                            content_type="application/octet-stream",
                            size_bytes=16,
                            part_id="3",
                            content_id="",
                            disposition="attachment",
                        ),
                    ),
                    original_eml=_raw_email_with_attachment(
                        filename="SL_Falta1.jpeg",
                        content_type="application/octet-stream",
                        payload=b"\xff\xd8\xff\xe0jpeg-preview\xff\xd9",
                    ),
                    provider="icloud",
                    mailbox="INBOX",
                )
            )
            commands: list[list[str]] = []

            result = preview_email_work_queue_attachment_action(
                provider="iCloud",
                folder="INBOX",
                uid="14482",
                part_id="1.3",
                filename="SL_Falta1.jpeg",
                preview_dir=preview_dir,
                opener=lambda command: commands.append(command),
                icloud_provider_factory=lambda: provider,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["filename"], "SL_Falta1.jpeg")
            self.assertTrue(Path(commands[0][1]).exists())

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
            action = json.loads((Path(temp_dir) / "actions.jsonl").read_text(encoding="utf-8").splitlines()[-1])
            self.assertEqual(action["items"][0]["trash_folder"], "Deleted Messages")
            self.assertEqual(action["items"][0]["trash_uid"], "914157")
            self.assertEqual(action["items"][0]["message_id"], "<14157@example.com>")

    def test_email_pending_purge_status_recovers_without_message_content(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "actions.jsonl"
            path.write_text(
                json.dumps({
                    "action": "process_email_work_queue_batch",
                    "items": [{
                        "item_id": "trash-1",
                        "provider": "iCloud",
                        "trash_folder": "Deleted Messages",
                        "trash_uid": "914157",
                        "message_id": "<14157@example.com>",
                        "status": "trashed",
                        "subject": "Private subject",
                    }],
                }) + "\n",
                encoding="utf-8",
            )

            result = email_processing_pending_purge_items(path)

            self.assertEqual(result["count"], 1)
            self.assertNotIn("subject", result["items"][0])

    def test_email_work_queue_can_reopen_durable_purge_candidates(self) -> None:
        self.assertIn('fetch("/api/email-processing/pending-purge")', EMAIL_PROCESSING_HTML)
        self.assertIn("initialPermanentDeleteItems = []", EMAIL_PROCESSING_HTML)
        self.assertIn("Otevřít koš (", EMAIL_PROCESSING_HTML)

    def test_email_windows_have_explicit_safe_return_navigation(self) -> None:
        self.assertIn("← Zpět do Cockpitu", EMAIL_PROCESSING_HTML)
        self.assertIn('id="backToEmailsBtn"', EMAIL_PROCESSING_HTML)
        self.assertIn('id="backToCockpitBtn"', EMAIL_PROCESSING_HTML)
        self.assertIn('queue.location.href = "/email-processing/"', EMAIL_PROCESSING_HTML)
        self.assertIn('queue.location.href = "/"', EMAIL_PROCESSING_HTML)
        self.assertIn("if (!window.closed) window.location.href = cockpitUrl", EMAIL_PROCESSING_HTML)

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
            self.assertEqual(result["required_confirmation"], "Potvrzuji, trvale smaž 1 e-mail z koše.")
            self.assertIn("čeká na přesné potvrzení", result["message"])
            self.assertEqual(result["items"][0]["required_confirmation"], result["required_confirmation"])

    def test_process_email_work_queue_purge_trash_rejects_boolean_without_exact_phrase(self) -> None:
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
                confirmed=True,
                actions_path=Path(temp_dir) / "actions.jsonl",
                icloud_provider_factory=lambda: provider,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["summary"]["purge_pending"], 1)
            self.assertFalse(provider.purge_calls)
            self.assertEqual(result["required_confirmation"], "Potvrzuji, trvale smaž 1 e-mail z koše.")

    def test_process_email_work_queue_purge_trash_confirmation_phrase_handles_counts(self) -> None:
        self.assertEqual(purge_trash_confirmation_phrase(1), "Potvrzuji, trvale smaž 1 e-mail z koše.")
        self.assertEqual(purge_trash_confirmation_phrase(2), "Potvrzuji, trvale smaž 2 e-maily z koše.")
        self.assertEqual(purge_trash_confirmation_phrase(5), "Potvrzuji, trvale smaž 5 e-mailů z koše.")

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
                confirmation_text="Potvrzuji, trvale smaž 1 e-mail z koše.",
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
        self.assertIn("E-maily", EMAIL_PROCESSING_HTML)
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
        self.assertIn("confirmation_text: typed", EMAIL_PROCESSING_HTML)
        self.assertIn("opiš přesně potvrzovací větu", EMAIL_PROCESSING_HTML)
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
        self.assertIn("Jen náhled", EMAIL_PROCESSING_HTML)
        self.assertIn(">Náhled</button>", EMAIL_PROCESSING_HTML)
        self.assertIn("dočasnou kopii PDF nebo obrázku", EMAIL_PROCESSING_HTML)
        self.assertIn("podporované PDF/obrázkové přílohy", EMAIL_PROCESSING_HTML)
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
        self.assertIn("E-maily", COCKPIT_HTML)
        self.assertIn("emailProcessingBtn", COCKPIT_HTML)
        self.assertIn("emailHubModal", COCKPIT_HTML)
        self.assertIn("emailWorkBtn", COCKPIT_HTML)
        self.assertIn("emailArchiveBtn", COCKPIT_HTML)
        self.assertIn("/email-processing/", COCKPIT_HTML)
        self.assertIn("/email-archive/", COCKPIT_HTML)
        self.assertIn("openEmailHub", COCKPIT_HTML)
        self.assertIn("openEmailProcessing", COCKPIT_HTML)
        self.assertIn("openEmailArchive", COCKPIT_HTML)

    def test_cockpit_navigation_groups_scandocu_under_documents(self) -> None:
        self.assertIn('id="documentsBtn">Dokumenty</button>', COCKPIT_HTML)
        self.assertIn('id="documentsPanel"', COCKPIT_HTML)
        self.assertIn('id="scanDocuBtn">Otevřít ScanDocu</button>', COCKPIT_HTML)
        self.assertIn(
            'id="scanDocuReviewBtn">Revidovat v ScanDocu</button>',
            COCKPIT_HTML,
        )
        self.assertGreater(
            COCKPIT_HTML.index('id="scanDocuBtn"'),
            COCKPIT_HTML.index('id="documentsPanel"'),
        )

    def test_email_archive_keeps_readonly_routes_and_embedded_frontend_contract(self) -> None:
        expected_routes = {
            "/email-archive/",
            "/api/email-archive/list",
            "/api/email-archive/detail",
            "/email-archive/file",
            "/email-archive/attachment",
            "/email-archive/incoming",
        }

        self.assertTrue(expected_routes.issubset(self.cockpit_do_get_routes()))
        self.assertTrue(expected_routes.isdisjoint(self.cockpit_do_post_routes()))
        self.assertIn("/api/email-archive/list", cockpit_module.EMAIL_ARCHIVE_HTML)
        self.assertIn("/api/email-archive/detail", cockpit_module.EMAIL_ARCHIVE_HTML)
        self.assertEqual(
            cockpit_module.email_archive_list_status.__module__,
            "app.email.archive_browser",
        )
        self.assertEqual(
            cockpit_module.resolve_email_archive_file.__module__,
            "app.email.archive_browser",
        )

    def test_web_apps_catalog_contains_known_apps(self) -> None:
        catalog = web_apps_catalog()
        titles = {item["title"] for item in catalog["apps"]}
        identifiers = {item["id"] for item in catalog["apps"]}

        self.assertTrue(catalog["ok"])
        self.assertNotIn("scandocu", identifiers)
        self.assertNotIn("email-processing", identifiers)
        self.assertNotIn("email-archive", identifiers)
        self.assertIn("Lékárna", titles)
        self.assertIn("Lékárna - správa", titles)
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
        self.flag_calls: list[dict[str, object]] = []

    def read_archive_source_by_uid(self, uid: str, max_chars: int = 50_000, folder: str = "INBOX") -> EmailArchiveSource:
        self.archive_calls.append({"uid": uid, "max_chars": max_chars, "folder": folder})
        return self._source

    def move_message_to_trash(self, uid: str, folder: str = "INBOX") -> dict[str, str]:
        self.trash_calls.append({"uid": uid, "folder": folder})
        return {"trash_folder": "Deleted Messages", "trash_uid": f"9{uid}", "message_id": f"<{uid}@example.com>"}

    def set_message_flagged(self, uid: str, folder: str = "INBOX", flagged: bool = True) -> bool:
        self.flag_calls.append({"uid": uid, "folder": folder, "flagged": flagged})
        return flagged

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


def _raw_email_with_pdf_attachment(filename: str = "faktura.pdf") -> bytes:
    pdf_bytes = b"%PDF-1.4\n1 0 obj <<>> endobj\ntrailer <<>>\n%%EOF\n"
    return _raw_email_with_attachment(
        filename=filename,
        content_type="application/pdf",
        payload=pdf_bytes,
        body=b"Dobry den, v priloze posilame fakturu.\r\n",
    )


def _raw_email_with_pdf_and_jpeg_attachments() -> bytes:
    pdf_bytes = b"%PDF-1.4\n1 0 obj <<>> endobj\ntrailer <<>>\n%%EOF\n"
    jpeg_bytes = b"\xff\xd8\xff\xe0jpeg-preview\xff\xd9"
    return (
        b"From: Sender <sender@example.com>\r\n"
        b"Date: Tue, 16 Jun 2026 11:02:29 +0000\r\n"
        b"Subject: Faktura FAK_226210588\r\n"
        b"MIME-Version: 1.0\r\n"
        b"Content-Type: multipart/mixed; boundary=\"outer\"\r\n"
        b"\r\n"
        b"--outer\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"Dobry den, v priloze je faktura a fotografie.\r\n"
        b"--outer\r\n"
        b"Content-Type: application/octet-stream; name=\"FAK_226210588.pdf\"\r\n"
        b"Content-Disposition: attachment; filename=\"FAK_226210588.pdf\"\r\n"
        b"\r\n"
        + pdf_bytes
        + b"\r\n--outer\r\n"
        b"Content-Type: application/octet-stream; name=\"SL_Falta1.jpeg\"\r\n"
        b"Content-Disposition: attachment; filename=\"SL_Falta1.jpeg\"\r\n"
        b"\r\n"
        + jpeg_bytes
        + b"\r\n--outer--\r\n"
    )


def _raw_email_with_attachment(
    *,
    filename: str,
    content_type: str,
    payload: bytes,
    body: bytes = b"Dobry den, v priloze posilame soubor.\r\n",
) -> bytes:
    filename_bytes = filename.encode("utf-8")
    content_type_bytes = content_type.encode("ascii")
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
        + body
        + b"--outer\r\n"
        b"Content-Type: " + content_type_bytes + b"; name=\"" + filename_bytes + b"\"\r\n"
        b"Content-Disposition: attachment; filename=\"" + filename_bytes + b"\"\r\n"
        b"\r\n"
        + payload
        + b"\r\n--outer--\r\n"
    )


if __name__ == "__main__":
    unittest.main()
