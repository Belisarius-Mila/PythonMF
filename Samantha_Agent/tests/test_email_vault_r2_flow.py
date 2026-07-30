from __future__ import annotations

import stat
import tempfile
import unittest
from email.message import EmailMessage
from pathlib import Path

from app.cockpit import process_email_work_queue_batch
from app.communication.janicka_r2_backend import JanickaR2Backend
from app.communication.janicka_r2_documents import (
    R2_DOCUMENTS_RELATIVE_ROOT,
    JanickaR2DocumentExistsError,
)
from app.documents.search_service import document_reference
from app.email.archive_models import EmailArchiveSource
from app.email.models import EmailAttachmentMeta


def _synthetic_pdf(text: str) -> bytes:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("ascii")
    objects = (
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> "
            b"/Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n"
        + content
        + b"\nendstream",
    )
    payload = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(f"{number} 0 obj\n".encode("ascii"))
        payload.extend(body)
        payload.extend(b"\nendobj\n")
    xref_offset = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    payload.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(payload)


def _source_snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class _SyntheticArchiveProvider:
    def __init__(self, source: EmailArchiveSource) -> None:
        self.source = source
        self.calls: list[dict[str, str | int]] = []

    def read_archive_source_by_uid(
        self,
        uid: str,
        max_chars: int = 50_000,
        folder: str = "INBOX",
    ) -> EmailArchiveSource:
        self.calls.append(
            {
                "uid": uid,
                "max_chars": max_chars,
                "folder": folder,
            }
        )
        return self.source


class EmailVaultR2FlowTests(unittest.TestCase):
    def test_selected_email_pdf_reaches_create_only_r2_txt(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            private_root = root / "canonical-private"
            private_root.mkdir(mode=0o700)
            documents_dir = private_root / "documents"
            archive_dir = root / "email-archive"
            pdf_name = "synteticka-faktura.pdf"
            pdf_text = (
                "Synteticka faktura pro integracni test. "
                "Datum splatnosti je 15. srpna 2026."
            )
            pdf_payload = _synthetic_pdf(pdf_text)

            message = EmailMessage()
            message["From"] = "synthetic@example.test"
            message["To"] = "recipient@example.test"
            message["Subject"] = "Synteticka faktura"
            message.set_content("Synteticke telo bez soukromych udaju.")
            message.add_attachment(
                pdf_payload,
                maintype="application",
                subtype="pdf",
                filename=pdf_name,
            )
            source = EmailArchiveSource(
                uid="synthetic-001",
                date="Thu, 30 Jul 2026 08:00:00 +0200",
                sender="Synthetic Sender <synthetic@example.test>",
                subject="Synteticka faktura",
                body_text="Synteticke telo bez soukromych udaju.",
                attachments=(
                    EmailAttachmentMeta(
                        filename=pdf_name,
                        content_type="application/pdf",
                        size_bytes=len(pdf_payload),
                        part_id="2",
                        content_id="",
                        disposition="attachment",
                    ),
                ),
                original_eml=message.as_bytes(),
                provider="icloud",
                mailbox="INBOX",
            )
            provider = _SyntheticArchiveProvider(source)

            imported = process_email_work_queue_batch(
                items=[
                    {
                        "id": "synthetic-flow-001",
                        "provider": "icloud",
                        "folder": "INBOX",
                        "uid": source.uid,
                        "category": "faktury/e-shopy",
                        "queueDecision": "save",
                        "saveAttachments": ["2"],
                        "attachment_metadata": [
                            {
                                "part_id": "2",
                                "filename": pdf_name,
                            }
                        ],
                    }
                ],
                archive_directory=archive_dir,
                documents_dir=documents_dir,
                decisions_path=root / "decisions.json",
                actions_path=root / "actions.jsonl",
                activity_state_path=root / "activity.json",
                icloud_provider_factory=lambda: provider,
            )

            self.assertTrue(imported["ok"])
            self.assertEqual(imported["summary"]["saved"], 1)
            self.assertEqual(imported["summary"]["attachments_imported"], 1)
            attachment = imported["items"][0]["attachments"][0]
            document_id = attachment["document_id"]
            self.assertEqual(
                attachment["document_ref"],
                document_reference(document_id),
            )
            self.assertEqual(
                provider.calls,
                [
                    {
                        "uid": source.uid,
                        "max_chars": 200_000,
                        "folder": "INBOX",
                    }
                ],
            )

            source_before_r2 = _source_snapshot(documents_dir)
            backend = JanickaR2Backend.bind(
                canonical_private_root=private_root,
                document_root=private_root / R2_DOCUMENTS_RELATIVE_ROOT,
            )
            flow = backend.document_selection_flow()
            search = flow.search_documents("synteticka faktura")

            self.assertEqual(search.count, 1)
            public_candidate = search.candidates[0].as_dict()
            self.assertNotIn("document_id", public_candidate)
            self.assertNotIn(str(private_root), str(public_candidate))

            created = flow.compile_selected_document(
                name="Syntetický přehled.txt",
                query="synteticka faktura",
                selection_ref=search.candidates[0].selection_ref,
            )
            stored = backend.document_store().read_text("Syntetický přehled.txt")

            self.assertEqual(created.source_count, 1)
            self.assertIn("R2-Adam – kompilovaný dokument", stored)
            self.assertIn("Inspekce dokumentu (read-only):", stored)
            self.assertIn("Synteticka faktura pro integracni test", stored)
            self.assertEqual(_source_snapshot(documents_dir), source_before_r2)
            output_path = (
                private_root
                / R2_DOCUMENTS_RELATIVE_ROOT
                / "Syntetický přehled.txt"
            )
            self.assertEqual(stat.S_IMODE(output_path.stat().st_mode), 0o600)

            with self.assertRaises(JanickaR2DocumentExistsError):
                flow.compile_selected_document(
                    name="Syntetický přehled.txt",
                    query="synteticka faktura",
                    selection_ref=search.candidates[0].selection_ref,
                )

            self.assertEqual(
                backend.document_store().read_text("Syntetický přehled.txt"),
                stored,
            )


if __name__ == "__main__":
    unittest.main()
