from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from app.email.case_vault import (
    EmailCaseRecord,
    load_email_case_record,
    save_email_case_record,
)
from app.email.models import EmailHeader, EmailMessage
from app.email.triage_service import triage_email_messages, triage_item_to_case_record


class EmailCaseVaultTests(unittest.TestCase):
    def test_vault_saves_safe_case_json_to_temp_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            record = _safe_case_record()

            result = save_email_case_record(record, directory=directory)
            loaded = load_email_case_record(record.case_id, directory=directory)
            raw = result.path.read_text(encoding="utf-8")

            self.assertTrue(result.created)
            self.assertTrue(result.path.exists())
            self.assertEqual(loaded["case_id"], record.case_id)
            self.assertTrue((directory / "index.json").exists())
            self.assertNotIn("https://", raw)
            self.assertNotIn("servis@nibe.example", raw)
            self.assertNotIn("PRIVATE BODY TAIL MUST NOT LEAK", raw)

    def test_vault_rejects_full_url_and_unredacted_email(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            unsafe_url = _safe_case_record()
            unsafe_url = replace(unsafe_url, summary_redacted="Obsahuje https://example.com/private")
            unsafe_email = _safe_case_record()
            unsafe_email_source = dict(unsafe_email.source)
            unsafe_email_source["sender"] = "NIBE <servis@nibe.example>"
            unsafe_email = replace(unsafe_email, source=unsafe_email_source)

            with self.assertRaisesRegex(ValueError, "plne URL"):
                save_email_case_record(unsafe_url, directory=directory)
            with self.assertRaisesRegex(ValueError, "e-mailovou adresu"):
                save_email_case_record(unsafe_email, directory=directory)

            self.assertFalse(any(directory.iterdir()))

    def test_vault_does_not_add_duplicate_case(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            record = _safe_case_record()

            first = save_email_case_record(record, directory=directory)
            second = save_email_case_record(record, directory=directory)
            index = json.loads((directory / "index.json").read_text(encoding="utf-8"))

            self.assertTrue(first.created)
            self.assertFalse(second.created)
            self.assertIn("duplicita nebyla pridana", second.message)
            self.assertEqual(index["cases"], [record.case_id])


def _safe_case_record() -> EmailCaseRecord:
    result = triage_email_messages(
        [
            EmailMessage(
                header=EmailHeader(
                    internal_id="fake-nibe",
                    date="Tue, 5 May 2026 14:02:22 +0000",
                    sender="NIBE servis <servis@nibe.example>",
                    subject="NIBE nabidka prohlidky fotovoltaiky po sezone",
                ),
                body_text=(
                    "Objednejte prohlidku fotovoltaiky do konce cervence 2026. "
                    "Portal https://partner.example/prohlidka. "
                    "Kontakt servis@nibe.example. "
                    "PRIVATE BODY TAIL MUST NOT LEAK."
                ),
                truncated=False,
            )
        ]
    )
    return triage_item_to_case_record(result.case_candidates[0])


if __name__ == "__main__":
    unittest.main()
