from __future__ import annotations

import json
import unittest

from scripts.build_quick_note_github_shortcut import build_workflow


class QuickNoteGitHubShortcutTests(unittest.TestCase):
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
        self.assertIn("Samantha quick note v1", serialized)
        self.assertIn("/api/quick-notes/deliver", serialized)

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
                (6, "is.workflow.actions.gettext", "WFTextActionText"),
                (7, "is.workflow.actions.url", "WFURLActionURL"),
                (15, "is.workflow.actions.url", "WFURLActionURL"),
            ],
        )

    def test_delivery_id_uses_current_date_magic_variable(self) -> None:
        workflow = build_workflow()
        actions = workflow["WFWorkflowActions"]
        identifiers = [action["WFWorkflowActionIdentifier"] for action in actions]

        self.assertNotIn("is.workflow.actions.date", identifiers)
        self.assertNotIn("is.workflow.actions.format.date", identifiers)
        delivery = next(
            action
            for action in actions
            if action["WFWorkflowActionIdentifier"] == "is.workflow.actions.gettext"
            and action["WFWorkflowActionParameters"].get("CustomOutputName") == "Delivery ID"
        )
        attachment = delivery["WFWorkflowActionParameters"]["WFTextActionText"]["Value"][
            "attachmentsByRange"
        ]["{12, 1}"]

        self.assertEqual(attachment["Type"], "CurrentDate")
        self.assertEqual(
            attachment["Aggrandizements"][0]["WFDateFormat"],
            "yyyyMMddHHmmssSSS",
        )
        self.assertIn("samantha-qn-", json.dumps(workflow, ensure_ascii=False))

    def test_shortcut_requires_exact_delivery_id_receipt(self) -> None:
        serialized = json.dumps(build_workflow(), ensure_ascii=False)

        self.assertIn("Potvrzené delivery_id jako text", serialized)
        self.assertIn("WFConditionalActionString", serialized)
        self.assertIn("Doručení je nejisté", serialized)
        self.assertIn("zůstává otevřená", serialized)
        self.assertIn("před případným novým pokusem zkontroluj soukromý inbox", serialized)
        self.assertNotIn("spusť zkratku znovu", serialized)

    def test_request_urls_render_as_visible_magic_variables_on_ios(self) -> None:
        requests = [
            action
            for action in build_workflow()["WFWorkflowActions"]
            if action["WFWorkflowActionIdentifier"] == "is.workflow.actions.downloadurl"
        ]

        self.assertEqual(len(requests), 2)
        for request in requests:
            url = request["WFWorkflowActionParameters"]["WFURL"]
            self.assertEqual(url["WFSerializationType"], "WFTextTokenString")
            self.assertEqual(url["Value"]["string"], "\ufffc")
            self.assertEqual(set(url["Value"]["attachmentsByRange"]), {"{0, 1}"})


if __name__ == "__main__":
    unittest.main()
