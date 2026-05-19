from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.email.case_vault import save_email_case_record
from app.email.models import EmailAttachmentMeta, EmailHeader, EmailMessage
from app.email.triage_service import triage_email_messages, triage_item_to_case_record
from app.email.work_mode_service import (
    format_work_mode_actions,
    format_work_mode_detail,
    start_work_mode,
)


class EmailWorkModeServiceTests(unittest.TestCase):
    def test_work_mode_shows_safe_detail_for_saved_case(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            record = _save_case(directory)

            work_mode = start_work_mode(record.case_id, directory=directory)
            detail = format_work_mode_detail(work_mode)

            self.assertIn(f"Case: {record.case_id}", detail)
            self.assertIn("Status: open", detail)
            self.assertIn("Zdroj: email", detail)
            self.assertIn("UID: fake-nibe", detail)
            self.assertIn("Objednat prohlidku fotovoltaiky", detail)
            self.assertIn("cenik.pdf | application/pdf | 1234 B", detail)

    def test_work_mode_does_not_show_full_urls_or_full_email_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            record = _save_case(directory)

            detail = format_work_mode_detail(start_work_mode(record.case_id, directory=directory))

            self.assertNotIn("https://", detail)
            self.assertNotIn("servis@nibe.example", detail)
            self.assertNotIn("PRIVATE BODY TAIL MUST NOT LEAK", detail)

    def test_work_mode_lists_actions_that_require_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            record = _save_case(directory)

            actions = format_work_mode_actions(start_work_mode(record.case_id, directory=directory))
            detail = format_work_mode_detail(start_work_mode(record.case_id, directory=directory))

            self.assertIn("znovu cist zdrojovy e-mail podle UID", actions)
            self.assertIn("zobrazit plne URL", actions)
            self.assertIn("otevrit URL v browseru", actions)
            self.assertIn("stahnout prilohu", actions)
            self.assertIn("dalsi samostatne potvrzeni", detail)


def _save_case(directory: Path):
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
                    "Nabizime preventivni prohlidku fotovoltaiky. "
                    "Objednejte prohlidku idealne do konce cervence 2026 pres portal "
                    "https://partner.example/prohlidka. Kontakt servis@nibe.example. "
                    "PRIVATE BODY TAIL MUST NOT LEAK."
                ),
                truncated=False,
                attachments=(
                    EmailAttachmentMeta(
                        filename="cenik.pdf",
                        content_type="application/pdf",
                        size_bytes=1234,
                        part_id="2",
                        content_id="",
                        disposition="attachment",
                    ),
                ),
            )
        ]
    )
    record = triage_item_to_case_record(result.case_candidates[0])
    save_email_case_record(record, directory=directory)
    return record


if __name__ == "__main__":
    unittest.main()
