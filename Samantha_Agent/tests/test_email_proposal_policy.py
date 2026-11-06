from __future__ import annotations

from dataclasses import replace
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.email.codex_proposer import CodexEmailProposer
from app.email.continuous_agent import SDKEmailProposer
from app.email.proposal_policy import load_reply_name, signed_draft
from tests.test_continuous_email_agent import observed, proposal


class EmailProposalPolicyTests(unittest.TestCase):
    def test_missing_signature_is_added_once_without_signing_an_empty_reply(self):
        for body in ("Dobrý den, paní Novotná,\n\nděkuji za postup.",
                     "Dobrý den,\n\nděkuji.\n\nS pozdravem"):
            signed = signed_draft(body, "Jan Testovací")
            self.assertEqual(signed.count("Jan Testovací"), 1)
            self.assertEqual(signed.count("S pozdravem"), 1)
            self.assertEqual(signed_draft(signed, "Jan Testovací"), signed)
            self.assertTrue(signed.endswith("Jan Testovací"))
        self.assertEqual(signed_draft("", "Jan Testovací"), "")
        self.assertEqual(signed_draft("Koncept", ""), "Koncept")

    def test_identity_must_be_local_and_single_line(self):
        with patch("app.email.proposal_policy.load_dotenv"), patch.dict("os.environ", {"SAMANTHA_EMAIL_REPLY_NAME": "Jan Testovací"}):
            self.assertEqual(load_reply_name(), "Jan Testovací")
        with patch("app.email.proposal_policy.load_dotenv"), patch.dict("os.environ", {"SAMANTHA_EMAIL_REPLY_NAME": "Jan\nCizí podpis"}):
            with self.assertRaises(ValueError): load_reply_name()

    def test_same_complete_evidence_and_reply_constraints_reach_both_adapters(self):
        message = observed(sender="Ing. Petra Novotná <petra@example.test>", body=(
            "Vyplňte žádost na webu. Žádost a životopis doručte do datové schránky do 20. listopadu. "
            "Samotná odpověď nestačí.\n" + "x" * 30_000 + "\nKONEC PODKLADU"))
        message = replace(message, source=replace(message.source, body_html="<p>ÚPLNÝ HTML KONEC</p>"))
        calls = []
        class Client:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def start_thread(self, **kwargs): calls.append(kwargs); return "policy-test"
            def send_text(self, **kwargs):
                calls.append(kwargs)
                return SimpleNamespace(delivered=True, answer=proposal().model_dump_json())
        result = CodexEmailProposer("gpt-6.1-terra", effort="high", reply_name="Jan Testovací", client_factory=Client)(message)
        captured = []
        def runner(agent, prompt, **kwargs):
            captured.extend([agent.instructions, json.loads(prompt)])
            return SimpleNamespace(final_output=proposal())
        sdk = SDKEmailProposer("test-model", reply_name="Jan Testovací", runner=runner)(message)
        self.assertEqual(sdk, result)
        self.assertTrue(result.reply_draft.endswith("Jan Testovací"))
        self.assertEqual(calls[1]["effort"], "high")
        payload = json.loads(calls[1]["text"])
        self.assertEqual(payload, captured[1])
        self.assertTrue(payload["body_text"].rstrip().endswith("KONEC PODKLADU"))
        self.assertEqual(payload["body_html"], message.source.body_html)
        self.assertNotIn("original_eml", payload)
        self.assertFalse(payload["reply_context"]["outgoing_attachments_supported"])
        self.assertEqual(payload["reply_context"]["user_name"], "Jan Testovací")
        self.assertEqual(calls[0]["developer_instructions"], captured[0])
        for phrase in ("datovou schránku", "podání nenahrazuje", "pouze text bez příloh", "oslovením konkrétní osoby", "nepodložená tvrzení",
                       "věcný nebo zdvořilostní význam", "výsledek výběrového řízení", "important=true",
                       "povinnou reakci od vhodné dobrovolné odpovědi"):
            self.assertIn(phrase, captured[0])


if __name__ == "__main__":
    unittest.main()
