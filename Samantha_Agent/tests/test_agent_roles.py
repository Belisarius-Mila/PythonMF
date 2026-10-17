from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.communication import agent_roles as roles


def entry(model="model-current", effort="high", **fields):
    return {"model": model, "inputModalities": ["text"],
            "supportedReasoningEfforts": [{"reasoningEffort": effort}], **fields}


def candidate(model="model-current", effort="high"):
    return {"model": model, "reasoning_effort": effort,
            "cost_review": "Explicitly reviewed budget policy",
            "dry_run_evidence": "Recorded successful dry-run receipt"}


class AgentRoleTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "roles.json"
        self.document = {"schema": 1, "roles": {roles.ROLE: {
            "label": "Release executor", "preferred_model": "model-current",
            "approved_models": [candidate()],
        }}}
        self.write()

    def write(self):
        self.path.write_text(json.dumps(self.document))

    def test_shared_policy_resolves_preferred_role_without_using_catalog_default(self):
        selected = roles.resolve_role([entry("expensive-default", isDefault=True), entry()], path=self.path)
        self.assertEqual(selected["model"], "model-current")
        self.assertFalse(selected["fallback"])
        self.assertEqual(roles.assert_current(selected, path=self.path)["model"], "model-current")

    def test_only_explicitly_reviewed_compatible_fallback_can_be_selected(self):
        self.document["roles"][roles.ROLE]["approved_models"].append(candidate("approved-successor", "medium"))
        self.write()
        selected = roles.resolve_role([entry("approved-successor", "medium")], path=self.path)
        self.assertEqual(selected["model"], "approved-successor")
        self.assertEqual(selected["reasoning_effort"], "medium")
        self.assertTrue(selected["fallback"])

    def test_upgrade_hint_does_not_approve_a_new_or_default_model(self):
        with self.assertRaisesRegex(roles.AgentRoleError, "Doporučený nástupce"):
            roles.resolve_role([entry(effort="low", upgrade="model-successor"),
                                entry("model-successor", isDefault=True)], path=self.path)

    def test_missing_model_and_unsupported_effort_stop(self):
        for catalog in ([], [entry("other-model")], [entry(effort="low")],
                        [entry(inputModalities=["audio"])], [entry(inputModalities=None)]):
            with self.subTest(catalog=catalog), self.assertRaises(roles.AgentRoleError):
                roles.resolve_role(catalog, path=self.path)

    def test_unreviewed_candidates_and_duplicate_approval_are_rejected(self):
        base = json.loads(json.dumps(self.document))
        for key in ("cost_review", "dry_run_evidence"):
            self.document = json.loads(json.dumps(base))
            self.document["roles"][roles.ROLE]["approved_models"][0][key] = ""
            self.write()
            with self.assertRaises(roles.AgentRoleError):
                roles.resolve_role([entry()], path=self.path)
        self.document = base
        self.document["roles"][roles.ROLE]["approved_models"].append(candidate())
        self.write()
        with self.assertRaises(roles.AgentRoleError):
            roles.load_role(self.path)

    def test_policy_change_cannot_retarget_a_frozen_job(self):
        selected = roles.resolve_role([entry()], path=self.path)
        self.document["roles"][roles.ROLE]["approved_models"][0]["reasoning_effort"] = "medium"
        self.write()
        with self.assertRaisesRegex(roles.AgentRoleError, "změnilo"):
            roles.assert_current(selected, path=self.path)

    def test_corrupt_or_missing_policy_and_malformed_selection_fail_closed(self):
        self.path.write_text("{}")
        for path in (self.path, self.path.with_name("missing.json")):
            with self.assertRaises(roles.AgentRoleError):
                roles.load_role(path)
        with self.assertRaises(roles.AgentRoleError):
            roles.validate_selection({"role":roles.ROLE,"model":17,"reasoning_effort":{},"policy_digest":"x"})

    def test_shipped_role_has_review_evidence_and_one_central_preference(self):
        policy = roles.load_role()
        approved = next(item for item in policy["approved_models"] if item["model"] == policy["preferred_model"])
        selected = roles.resolve_role([entry(approved["model"], approved["reasoning_effort"])])
        self.assertEqual(selected["model"], policy["preferred_model"])

    def test_routine_role_does_not_change_release_binding_or_accept_release_proof(self):
        release = roles.resolve_role([entry()], path=self.path)
        self.document["roles"][roles.ROUTINE_ROLE] = {
            "label": "Routine reviewer", "preferred_model": "review-model",
            "approved_models": [candidate("review-model", "medium")]}
        self.write()
        self.assertEqual(roles.resolve_role([entry()], path=self.path), release)
        review = roles.resolve_role([entry("review-model", "medium")], path=self.path, role=roles.ROUTINE_ROLE)
        self.assertEqual(review["model"], "review-model")
        with self.assertRaises(roles.AgentRoleError):
            roles.validate_selection(review)
        with self.assertRaises(roles.AgentRoleError):
            roles.assert_current(release, path=self.path, role=roles.ROUTINE_ROLE)


if __name__ == "__main__":
    unittest.main()
