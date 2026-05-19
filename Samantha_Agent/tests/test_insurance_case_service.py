from __future__ import annotations

import unittest

from app.email.insurance_case_tools import build_rixo_insurance_case_from_uids_text
from app.email.insurance_case_service import build_insurance_case, format_insurance_case
from app.email.models import EmailAttachmentMeta, EmailHeader, EmailMessage
from app.email.safety import has_explicit_multi_uid_read_confirmation


class InsuranceCaseServiceTests(unittest.TestCase):
    def test_builds_redacted_case_from_multiple_messages(self) -> None:
        messages = (
            EmailMessage(
                header=EmailHeader(
                    internal_id="101",
                    date="Tue, 19 May 2026 08:00:00 +0200",
                    sender="RIXO <agent@example.com>",
                    subject="Pojistka POL-12345 a skoda CLAIM-987",
                ),
                body_text=(
                    "Prosim potvrdte dokumenty k pojistka POL-12345.\n"
                    "Skoda CLAIM-987 ma deadline 20.5.2026.\n"
                    "Kontakt agent@example.com.\n"
                    "Portal: https://rixo.example/case/987"
                ),
                truncated=False,
                attachments=(
                    EmailAttachmentMeta(
                        filename="formular.pdf",
                        content_type="application/pdf",
                        size_bytes=2048,
                        part_id="2",
                        content_id="",
                        disposition="attachment",
                    ),
                ),
            ),
            EmailMessage(
                header=EmailHeader(
                    internal_id="102",
                    date="Tue, 19 May 2026 09:00:00 +0200",
                    sender="Mila <mila@example.com>",
                    subject="Doplneni podkladu",
                ),
                body_text=(
                    "Please review doplneni podkladu.\n"
                    "Upload: https://rixo.example/upload"
                ),
                truncated=True,
            ),
        )

        case = build_insurance_case(messages)

        self.assertEqual(case.title, "RIXO Insurance Case")
        self.assertEqual(case.source_count, 2)
        self.assertEqual(case.priority, "high")
        self.assertEqual(case.policy_reference, "POL-12345")
        self.assertEqual(case.claim_reference, "CLAIM-987")
        self.assertEqual(len(case.sources), 2)
        self.assertEqual(len(case.attachments), 1)
        self.assertEqual(case.attachments[0].uid, "101")
        self.assertEqual(case.link_domains[0].domain, "rixo.example")
        self.assertEqual(case.link_domains[0].count, 2)
        self.assertIn("[e-mail redigovan]", case.summary_redacted)
        self.assertNotIn("agent@example.com", case.summary_redacted)

    def test_format_does_not_show_full_urls_and_mentions_safety_boundaries(self) -> None:
        message = EmailMessage(
            header=EmailHeader(
                internal_id="201",
                date="Tue, 19 May 2026 10:00:00 +0200",
                sender="RIXO <agent@example.com>",
                subject="Claim update",
            ),
            body_text=(
                "Please confirm receipt.\n"
                "Detail: https://rixo.example/private/full/path"
            ),
            truncated=False,
        )

        formatted = format_insurance_case(build_insurance_case((message,)))

        self.assertIn("Potvrzene prectene zdroje: 1", formatted)
        self.assertIn("- rixo.example: 1 odkaz", formatted)
        self.assertIn("Plne URL nezobrazuji automaticky", formatted)
        self.assertNotIn("https://rixo.example/private/full/path", formatted)
        self.assertIn("odkazy nebyly otevreny", formatted)
        self.assertIn("prilohy nebyly stazeny", formatted)
        self.assertIn("nic nebylo odeslano ani ulozeno do memory", formatted)

    def test_requires_at_least_one_message(self) -> None:
        with self.assertRaises(ValueError):
            build_insurance_case(())


class InsuranceCaseSafetyTests(unittest.TestCase):
    def test_multi_uid_confirmation_requires_every_uid_and_confirmation_word(self) -> None:
        self.assertTrue(
            has_explicit_multi_uid_read_confirmation(
                uids=["101", "102"],
                confirmation_text=(
                    "Potvrzuji, ze chci precist tela e-mailu UID 101 a UID 102 "
                    "a vytvorit RIXO Insurance Case."
                ),
            )
        )
        self.assertFalse(
            has_explicit_multi_uid_read_confirmation(
                uids=["101", "102"],
                confirmation_text="Potvrzuji, vezmi predchozi e-maily.",
            )
        )
        self.assertFalse(
            has_explicit_multi_uid_read_confirmation(
                uids=["101"],
                confirmation_text="Potvrzuji UID 101.",
            )
        )


class InsuranceCaseToolTests(unittest.TestCase):
    def test_tool_gate_does_not_call_provider_without_confirmation(self) -> None:
        def fail_provider() -> object:
            raise AssertionError("Provider must not be called without confirmation")

        result = build_rixo_insurance_case_from_uids_text(
            uids=["101", "102"],
            user_confirmed=False,
            confirmation_text="",
            provider_factory=fail_provider,
        )

        self.assertIn("Nejdrive potrebuji vyslovne potvrzeni", result)
        self.assertIn("101, 102", result)

    def test_tool_reads_all_confirmed_uids_and_formats_case(self) -> None:
        class FakeProvider:
            def read_message_by_uid(self, uid: str, max_chars: int) -> EmailMessage:
                return EmailMessage(
                    header=EmailHeader(
                        internal_id=uid,
                        date="Tue, 19 May 2026 10:00:00 +0200",
                        sender="RIXO <agent@example.com>",
                        subject=f"RIXO case {uid}",
                    ),
                    body_text=(
                        f"Please confirm UID {uid} for claim CLAIM-987. "
                        "Detail https://rixo.example/case"
                    ),
                    truncated=False,
                )

        result = build_rixo_insurance_case_from_uids_text(
            uids=["101", "102"],
            user_confirmed=True,
            confirmation_text=(
                "Potvrzuji, ze chci precist tela e-mailu UID 101 a UID 102 "
                "a vytvorit RIXO Insurance Case."
            ),
            provider_factory=FakeProvider,
        )

        self.assertIn("Nazev: RIXO Insurance Case", result)
        self.assertIn("Potvrzene prectene zdroje: 2", result)
        self.assertIn("UID 101", result)
        self.assertIn("UID 102", result)
        self.assertIn("- rixo.example: 2 odkazu", result)
        self.assertNotIn("https://rixo.example/case", result)
        self.assertIn("nic nebylo odeslano ani ulozeno do memory", result)


if __name__ == "__main__":
    unittest.main()
