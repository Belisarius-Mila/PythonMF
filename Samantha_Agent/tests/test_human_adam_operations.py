from __future__ import annotations

import unittest
from datetime import date
from types import SimpleNamespace

from app.communication.human_adam_operations import (
    FAMILY_CALENDAR_DRY_RUN_CANDIDATE,
    FAMILY_CALENDAR_DRY_RUN_TODAY,
    FAMILY_CALENDAR_TEST_EMAIL_PREVIEW,
    FAMILY_CALENDAR_WORKSTREAM_ID,
    GITHUB_PAGES_TARGET,
    MMTX_PAGES_DEPLOY,
    MMTX_WORKSTREAM_ID,
    OPERATION_MARKER_END,
    OPERATION_MARKER_START,
    HumanAdamOperationError,
    HumanAdamOperationRequest,
    automatic_operation_instruction,
    execute_human_adam_operation,
    explicit_publish_and_deploy_command,
    parse_human_adam_operation,
)


def _dry_run_document(*, candidates: int) -> dict[str, object]:
    return {
        "status": "dry_run",
        "candidate_count": candidates,
        "d2_count": candidates,
        "d1_count": 0,
        "eligible_count": candidates,
        "recipient_count": 4,
        "coordinator_called": False,
        "transport_called": False,
    }


class HumanAdamOperationsTests(unittest.TestCase):
    def test_instruction_is_scoped_to_family_calendar_and_forbids_send(self) -> None:
        self.assertEqual(
            automatic_operation_instruction(workstream_id="project-mmtx"),
            "",
        )
        instruction = automatic_operation_instruction(
            workstream_id=FAMILY_CALENDAR_WORKSTREAM_ID
        )
        self.assertIn(FAMILY_CALENDAR_DRY_RUN_TODAY, instruction)
        self.assertIn(FAMILY_CALENDAR_DRY_RUN_CANDIDATE, instruction)
        self.assertIn(FAMILY_CALENDAR_TEST_EMAIL_PREVIEW, instruction)
        self.assertIn("Never use this protocol for SMTP send", instruction)

    def test_mmtx_instruction_requires_server_verified_direct_publication_command(self) -> None:
        unauthorized = automatic_operation_instruction(
            workstream_id=MMTX_WORKSTREAM_ID,
            production_deployment_target=GITHUB_PAGES_TARGET,
            publication_authorized=False,
        )
        authorized = automatic_operation_instruction(
            workstream_id=MMTX_WORKSTREAM_ID,
            production_deployment_target=GITHUB_PAGES_TARGET,
            publication_authorized=True,
        )

        self.assertIn(MMTX_PAGES_DEPLOY, unauthorized)
        self.assertIn("publication_authorized=false", unauthorized)
        self.assertIn("publication_authorized=true", authorized)
        self.assertTrue(explicit_publish_and_deploy_command("Prosím p+n"))
        self.assertTrue(explicit_publish_and_deploy_command("Nasaď na produkci"))
        self.assertFalse(
            explicit_publish_and_deploy_command("Proč se to nenasadilo na produkci?")
        )

    def test_mmtx_publication_executes_only_with_direct_authorization(self) -> None:
        document = {
            "status": "deployed",
            "main_short": "a" * 12,
            "pushed": True,
            "commit_count": 2,
            "workflow_run_id": 123,
            "deployment_id": 456,
            "production_url": "https://belisarius-mila.github.io/PythonMF/",
            "smoke_http_status": 200,
            "redacted": True,
        }
        calls = 0

        def publisher() -> dict[str, object]:
            nonlocal calls
            calls += 1
            return document

        result = execute_human_adam_operation(
            HumanAdamOperationRequest(MMTX_PAGES_DEPLOY),
            workstream_id=MMTX_WORKSTREAM_ID,
            publication_authorized=True,
            production_publisher=publisher,
        )
        self.assertEqual(result, document)
        self.assertEqual(calls, 1)

        with self.assertRaises(HumanAdamOperationError):
            execute_human_adam_operation(
                HumanAdamOperationRequest(MMTX_PAGES_DEPLOY),
                workstream_id=MMTX_WORKSTREAM_ID,
                publication_authorized=False,
                production_publisher=publisher,
            )
        self.assertEqual(calls, 1)

    def test_valid_final_receipt_is_parsed_and_hidden(self) -> None:
        parsed = parse_human_adam_operation(
            "Spustím bezpečný provozní náhled.\n\n"
            f"{OPERATION_MARKER_START}\n"
            f'{{"operation_id":"{FAMILY_CALENDAR_TEST_EMAIL_PREVIEW}"}}\n'
            f"{OPERATION_MARKER_END}"
        )

        self.assertEqual(parsed.state, "valid")
        self.assertEqual(parsed.visible_answer, "Spustím bezpečný provozní náhled.")
        self.assertIsNotNone(parsed.request)
        assert parsed.request is not None
        self.assertEqual(parsed.request.operation_id, FAMILY_CALENDAR_TEST_EMAIL_PREVIEW)

    def test_receipt_rejects_extra_fields_trailing_text_and_invalid_id(self) -> None:
        extra = parse_human_adam_operation(
            "Náhled\n"
            f"{OPERATION_MARKER_START}\n"
            '{"operation_id":"family_calendar_test_email_preview","path":"/private"}\n'
            f"{OPERATION_MARKER_END}"
        )
        trailing = parse_human_adam_operation(
            "Náhled\n"
            f"{OPERATION_MARKER_START}\n"
            '{"operation_id":"family_calendar_test_email_preview"}\n'
            f"{OPERATION_MARKER_END}\nnavíc"
        )
        invalid_id = parse_human_adam_operation(
            "Náhled\n"
            f"{OPERATION_MARKER_START}\n"
            '{"operation_id":"../../private"}\n'
            f"{OPERATION_MARKER_END}"
        )

        self.assertEqual(extra.state, "invalid")
        self.assertEqual(trailing.state, "invalid")
        self.assertEqual(invalid_id.state, "invalid")

    def test_today_dry_run_returns_only_validated_redacted_counts(self) -> None:
        result = execute_human_adam_operation(
            HumanAdamOperationRequest(FAMILY_CALENDAR_DRY_RUN_TODAY),
            workstream_id=FAMILY_CALENDAR_WORKSTREAM_ID,
            today_factory=lambda: date(2026, 7, 23),
            dry_run_runner=lambda **_kwargs: SimpleNamespace(
                safe_document=lambda: _dry_run_document(candidates=0)
            ),
        )

        self.assertEqual(result["status"], "dry_run")
        self.assertEqual(result["recipient_count"], 4)
        self.assertFalse(result["coordinator_called"])
        self.assertFalse(result["transport_called"])

    def test_candidate_dry_run_hides_date_and_requires_matching_eligible_count(self) -> None:
        calls = 0

        def runner(**_kwargs: object) -> SimpleNamespace:
            nonlocal calls
            calls += 1
            candidates = 1 if calls == 3 else 0
            return SimpleNamespace(
                safe_document=lambda: _dry_run_document(candidates=candidates)
            )

        result = execute_human_adam_operation(
            HumanAdamOperationRequest(FAMILY_CALENDAR_DRY_RUN_CANDIDATE),
            workstream_id=FAMILY_CALENDAR_WORKSTREAM_ID,
            today_factory=lambda: date(2026, 7, 23),
            dry_run_runner=runner,
        )

        self.assertEqual(calls, 3)
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["eligible_count"], 1)
        self.assertNotIn("date", result)
        self.assertNotIn("event", result)

    def test_test_email_preview_never_calls_transport_and_rejects_private_output(self) -> None:
        safe = execute_human_adam_operation(
            HumanAdamOperationRequest(FAMILY_CALENDAR_TEST_EMAIL_PREVIEW),
            workstream_id=FAMILY_CALENDAR_WORKSTREAM_ID,
            test_email_planner=lambda: SimpleNamespace(
                safe_document=lambda: {
                    "status": "preview",
                    "mode": "dry_run",
                    "recipient_count": 4,
                    "confirmation_required": True,
                    "transport_called": False,
                }
            ),
        )

        self.assertEqual(safe["status"], "preview")
        self.assertFalse(safe["transport_called"])

        with self.assertRaises(HumanAdamOperationError):
            execute_human_adam_operation(
                HumanAdamOperationRequest(FAMILY_CALENDAR_TEST_EMAIL_PREVIEW),
                workstream_id=FAMILY_CALENDAR_WORKSTREAM_ID,
                test_email_planner=lambda: SimpleNamespace(
                    safe_document=lambda: {
                        "status": "preview",
                        "mode": "dry_run",
                        "recipient_count": 4,
                        "confirmation_required": True,
                        "transport_called": False,
                        "address": "private@example.invalid",
                    }
                ),
            )

    def test_unknown_operation_and_wrong_workstream_fail_closed(self) -> None:
        with self.assertRaises(HumanAdamOperationError):
            execute_human_adam_operation(
                HumanAdamOperationRequest("unknown_operation"),
                workstream_id=FAMILY_CALENDAR_WORKSTREAM_ID,
            )
        with self.assertRaises(HumanAdamOperationError):
            execute_human_adam_operation(
                HumanAdamOperationRequest(FAMILY_CALENDAR_DRY_RUN_TODAY),
                workstream_id="project-mmtx",
            )


if __name__ == "__main__":
    unittest.main()
