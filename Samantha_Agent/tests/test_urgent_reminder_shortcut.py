from __future__ import annotations

import json
import unittest

from scripts.build_urgent_reminder_shortcut import build_workflow


class UrgentReminderShortcutTests(unittest.TestCase):
    def test_shortcut_is_write_ahead_and_contains_no_real_credentials(self) -> None:
        workflow = build_workflow()
        actions = workflow["WFWorkflowActions"]
        identifiers = [action["WFWorkflowActionIdentifier"] for action in actions]
        serialized = json.dumps(workflow, ensure_ascii=False)

        github_request_index = identifiers.index("is.workflow.actions.downloadurl")
        cockpit_request_index = identifiers.index(
            "is.workflow.actions.downloadurl",
            github_request_index + 1,
        )

        self.assertLess(github_request_index, cockpit_request_index)
        self.assertIn("github_pat_REPLACE_ME", serialized)
        self.assertIn("OWNER/REPOSITORY", serialized)
        self.assertNotIn("iCloud", serialized)
        self.assertNotIn("ghp_", serialized)

    def test_import_questions_target_token_github_and_cockpit_parameters(self) -> None:
        workflow = build_workflow()
        actions = workflow["WFWorkflowActions"]
        questions = workflow["WFWorkflowImportQuestions"]

        targets = [
            (
                question["ActionIndex"],
                actions[question["ActionIndex"]]["WFWorkflowActionIdentifier"],
                question["ParameterKey"],
            )
            for question in questions
        ]

        self.assertEqual(
            targets,
            [
                (8, "is.workflow.actions.gettext", "WFTextActionText"),
                (9, "is.workflow.actions.url", "WFURLActionURL"),
                (17, "is.workflow.actions.url", "WFURLActionURL"),
            ],
        )

    def test_delivery_id_uses_fresh_millisecond_timestamp(self) -> None:
        workflow = build_workflow()
        actions = workflow["WFWorkflowActions"]
        identifiers = [action["WFWorkflowActionIdentifier"] for action in actions]

        self.assertNotIn("is.workflow.actions.number.random", identifiers)
        date_index = identifiers.index("is.workflow.actions.date")
        format_index = identifiers.index("is.workflow.actions.format.date")
        self.assertLess(date_index, format_index)
        self.assertEqual(
            actions[date_index]["WFWorkflowActionParameters"]["WFDateActionMode"],
            "Current Date",
        )
        format_parameters = actions[format_index]["WFWorkflowActionParameters"]
        self.assertEqual(format_parameters["WFDateFormatStyle"], "Custom")
        self.assertEqual(format_parameters["WFDateFormat"], "Custom")
        self.assertEqual(format_parameters["WFDateFormatString"], "yyyyMMddHHmmssSSS")
        date_attachment = format_parameters["WFDate"]["Value"][
            "attachmentsByRange"
        ]["{0, 1}"]
        self.assertEqual(date_attachment["OutputName"], "Date")

        delivery_index = next(
            index
            for index, action in enumerate(actions)
            if action["WFWorkflowActionIdentifier"] == "is.workflow.actions.gettext"
            and action["WFWorkflowActionParameters"].get("CustomOutputName")
            == "Delivery ID"
        )
        delivery_attachment = actions[delivery_index]["WFWorkflowActionParameters"][
            "WFTextActionText"
        ]["Value"]["attachmentsByRange"]["{9, 1}"]
        self.assertEqual(delivery_attachment["OutputName"], "Formatted Date")

        serialized = json.dumps(workflow, ensure_ascii=False)
        self.assertIn("samantha-", serialized)
        self.assertIn("Časové ID", serialized)

    def test_shortcut_requires_exact_delivery_id_receipt(self) -> None:
        workflow = build_workflow()
        serialized = json.dumps(workflow, ensure_ascii=False)

        self.assertIn("Potvrzené delivery_id jako text", serialized)
        self.assertIn("WFConditionalActionString", serialized)
        self.assertIn("Doručení je nejisté", serialized)
        self.assertIn("zůstává otevřená", serialized)

    def test_request_urls_render_as_visible_magic_variables_on_ios(self) -> None:
        workflow = build_workflow()
        requests = [
            action
            for action in workflow["WFWorkflowActions"]
            if action["WFWorkflowActionIdentifier"]
            == "is.workflow.actions.downloadurl"
        ]

        self.assertEqual(len(requests), 2)
        for request in requests:
            url = request["WFWorkflowActionParameters"]["WFURL"]
            self.assertEqual(url["WFSerializationType"], "WFTextTokenString")
            self.assertEqual(url["Value"]["string"], "\ufffc")
            self.assertEqual(set(url["Value"]["attachmentsByRange"]), {"{0, 1}"})


if __name__ == "__main__":
    unittest.main()
