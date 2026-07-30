from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.email.archive_browser import (
    EMAIL_ARCHIVE_OPENABLE_FILES,
    downloaded_email_archive_attachments,
    email_archive_reference,
    email_archive_detail_status,
    email_archive_list_status,
    read_email_archive_body_text,
    resolve_email_archive_file,
    resolve_email_archive_incoming_file,
)


class EmailArchiveBrowserTests(unittest.TestCase):
    def create_archive_fixture(self, root: Path) -> tuple[Path, Path, Path]:
        archive_directory = root / "email_archive"
        archive_dir = archive_directory / "email-13338-prihlaseni"
        attachments_dir = archive_dir / "attachments"
        attachments_dir.mkdir(parents=True)
        (archive_dir / "metadata.json").write_text(
            json.dumps(
                {
                    "archive_id": "email-13338-prihlaseni",
                    "uid": "13338",
                    "date": "Mon, 9 Mar 2026 13:58:41 +0000",
                    "from": "Test Sender <sender@example.test>",
                    "subject": "přihlášení",
                    "archived_at": "2026-07-09T17:03:27+00:00",
                    "links_count": 0,
                    "attachments_count": 2,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (archive_dir / "body.html").write_text("<p>test</p>", encoding="utf-8")
        (archive_dir / "body.txt").write_text("test", encoding="utf-8")
        (archive_dir / "original.eml").write_bytes(b"Subject: test\n\nbody")
        (attachments_dir / "attachments.json").write_text(
            json.dumps(
                {
                    "attachments": [
                        {
                            "filename": "přihlašovací lístek.doc",
                            "content_type": "application/msword",
                            "size_bytes": 34816,
                            "saved": False,
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        documents_dir = root / "documents"
        incoming = documents_dir / "inbox" / "incoming"
        incoming.mkdir(parents=True)
        (incoming / "icloud_uid_13338_07_prihlasovaci-listek.doc").write_bytes(b"DOC")
        return archive_directory, archive_dir, documents_dir

    def test_list_and_detail_preserve_readonly_payload_contract(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            archive_directory, _archive_dir, documents_dir = self.create_archive_fixture(root)

            listing = email_archive_list_status(
                "13338",
                limit=5000,
                archive_directory=archive_directory,
            )
            detail = email_archive_detail_status(
                "email-13338-prihlaseni",
                archive_directory=archive_directory,
                documents_dir=documents_dir,
            )

        self.assertEqual(set(listing), {"ok", "count", "items", "message"})
        self.assertTrue(listing["ok"])
        self.assertEqual(listing["count"], 1)
        self.assertEqual(
            set(listing["items"][0]),
            {
                "archive_id",
                "archive_ref",
                "uid",
                "subject",
                "sender",
                "date",
                "archived_at",
                "links_count",
                "attachments_count",
                "relative_path",
            },
        )
        self.assertNotIn("sender@example.test", json.dumps(listing, ensure_ascii=False))

        self.assertEqual(
            set(detail),
            {
                "ok",
                "archive_id",
                "archive_ref",
                "uid",
                "subject",
                "sender",
                "date",
                "archived_at",
                "relative_path",
                "files",
                "body_text",
                "body_truncated",
                "attachments",
                "downloaded_attachments",
                "vault_attachments",
                "message",
            },
        )
        self.assertTrue(detail["ok"])
        self.assertEqual(detail["uid"], "13338")
        self.assertEqual(detail["body_text"], "test")
        self.assertFalse(detail["body_truncated"])
        self.assertEqual(
            {item["key"] for item in detail["files"]},
            set(EMAIL_ARCHIVE_OPENABLE_FILES),
        )
        self.assertEqual(detail["attachments"][0]["filename"], "přihlašovací lístek.doc")
        self.assertEqual(
            detail["downloaded_attachments"][0]["url"],
            "/email-archive/incoming?name=icloud_uid_13338_07_prihlasovaci-listek.doc",
        )
        self.assertNotIn("sender@example.test", json.dumps(detail, ensure_ascii=False))

    def test_plain_body_preview_is_bounded_and_rejects_escaped_symlink(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            archive_directory, archive_dir, _documents_dir = self.create_archive_fixture(root)
            (archive_dir / "body.txt").write_text("Příliš dlouhý text", encoding="utf-8")
            preview, truncated = read_email_archive_body_text(
                email_archive_reference(archive_dir.name),
                archive_directory=archive_directory,
                max_bytes=8,
            )

            outside = root / "outside.txt"
            outside.write_text("mimo", encoding="utf-8")
            (archive_dir / "body.txt").unlink()
            (archive_dir / "body.txt").symlink_to(outside)
            escaped, escaped_truncated = read_email_archive_body_text(
                email_archive_reference(archive_dir.name),
                archive_directory=archive_directory,
            )

        self.assertTrue(preview)
        self.assertTrue(truncated)
        self.assertEqual(escaped, "")
        self.assertFalse(escaped_truncated)

    def test_redacted_archive_uses_opaque_reference_and_links_existing_vault_pdf(
        self,
    ) -> None:
        raw_identifier = "1234567890"
        archive_name = f"email-156688-payment-{raw_identifier}"
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            archive_directory = root / "email_archive"
            archive_dir = archive_directory / archive_name
            attachments_dir = archive_dir / "attachments"
            attachments_dir.mkdir(parents=True)
            (archive_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "archive_id": archive_name,
                        "uid": "156688",
                        "subject": f"Payment contract {raw_identifier}",
                        "attachments_count": 1,
                    }
                ),
                encoding="utf-8",
            )
            (archive_dir / "body.txt").write_text("payment", encoding="utf-8")
            (attachments_dir / "attachments.json").write_text(
                json.dumps(
                    {
                        "attachments": [
                            {
                                "filename": f"payment-{raw_identifier}.pdf",
                                "content_type": "application/pdf",
                                "size_bytes": 12,
                                "saved": False,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            documents_dir = root / "documents"
            vault_file = documents_dir / "vault" / "insurance" / "payment.pdf"
            vault_file.parent.mkdir(parents=True)
            vault_file.write_bytes(b"%PDF-fixture")
            index = documents_dir / "index"
            index.mkdir()
            document_id = f"doc-email-156688-payment-{raw_identifier}"
            (index / "documents_index.jsonl").write_text(
                json.dumps(
                    {
                        "document_id": document_id,
                        "title": f"E-mail UID 156688 attachment {raw_identifier}",
                        "original_filename": f"payment-{raw_identifier}.pdf",
                        "domain": "insurance",
                        "document_type": "invoice",
                        "reading_status": "ok",
                        "stored_path": str(vault_file),
                        "size_bytes": vault_file.stat().st_size,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            listing = email_archive_list_status(
                "156688",
                archive_directory=archive_directory,
            )
            archive_ref = listing["items"][0]["archive_ref"]
            detail = email_archive_detail_status(
                archive_ref,
                archive_directory=archive_directory,
                documents_dir=documents_dir,
            )
            redacted_detail = email_archive_detail_status(
                listing["items"][0]["archive_id"],
                archive_directory=archive_directory,
                documents_dir=documents_dir,
            )
            metadata_file = resolve_email_archive_file(
                archive_ref,
                "metadata",
                archive_directory=archive_directory,
            )

        payload = json.dumps({"listing": listing, "detail": detail}, ensure_ascii=False)
        self.assertEqual(archive_ref, email_archive_reference(archive_name))
        self.assertTrue(detail["ok"])
        self.assertTrue(redacted_detail["ok"])
        self.assertTrue(metadata_file["ok"])
        self.assertIn("[rodne cislo redigovano]", detail["archive_id"])
        self.assertNotIn(raw_identifier, payload)
        self.assertEqual(len(detail["vault_attachments"]), 1)
        self.assertTrue(detail["vault_attachments"][0]["can_open"])
        self.assertRegex(
            detail["vault_attachments"][0]["document_ref"],
            r"^docref-[0-9a-f]{16}$",
        )
        self.assertIn(
            detail["vault_attachments"][0]["document_ref"],
            detail["vault_attachments"][0]["url"],
        )
        self.assertTrue(
            all(f"archive_id={archive_ref}" in row["url"] for row in detail["files"])
        )

    def test_list_handles_missing_archive_and_clamps_limit(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            missing = email_archive_list_status(archive_directory=root / "missing")
            archive_directory, archive_dir, _documents_dir = self.create_archive_fixture(root)
            second = archive_directory / "email-2"
            second.mkdir()
            (second / "metadata.json").write_text(
                json.dumps({"archive_id": "email-2", "uid": "2", "subject": "druhý"}),
                encoding="utf-8",
            )
            limited = email_archive_list_status(limit=0, archive_directory=archive_directory)

        self.assertEqual(missing, {
            "ok": True,
            "count": 0,
            "items": [],
            "message": "EmailArchiveVault zatím neexistuje.",
        })
        self.assertEqual(limited["count"], 1)
        self.assertIn(limited["items"][0]["archive_id"], {archive_dir.name, second.name})

    def test_invalid_metadata_is_skipped_by_list_and_rejected_by_detail(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            archive_directory = Path(temp_dir) / "email_archive"
            archive_dir = archive_directory / "email-invalid"
            archive_dir.mkdir(parents=True)
            (archive_dir / "metadata.json").write_text("[not-an-object]", encoding="utf-8")

            listing = email_archive_list_status(archive_directory=archive_directory)
            detail = email_archive_detail_status(
                "email-invalid",
                archive_directory=archive_directory,
                documents_dir=Path(temp_dir) / "documents",
            )

        self.assertEqual(listing["items"], [])
        self.assertFalse(detail["ok"])
        self.assertEqual(detail["message"], "Archiv nemá čitelná metadata.")

    def test_file_resolvers_reject_traversal_and_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            archive_directory, archive_dir, documents_dir = self.create_archive_fixture(root)
            outside = root / "outside"
            outside.mkdir()
            outside_body = outside / "body.html"
            outside_body.write_text("outside", encoding="utf-8")
            (archive_directory / "linked-archive").symlink_to(outside, target_is_directory=True)
            (archive_dir / "body.html").unlink()
            (archive_dir / "body.html").symlink_to(outside_body)

            incoming = documents_dir / "inbox" / "incoming"
            outside_attachment = outside / "attachment.pdf"
            outside_attachment.write_bytes(b"%PDF")
            (incoming / "icloud_uid_13338_link.pdf").symlink_to(outside_attachment)

            bad_archive = resolve_email_archive_file(
                "../email-13338-prihlaseni",
                "body_html",
                archive_directory=archive_directory,
            )
            bad_key = resolve_email_archive_file(
                "email-13338-prihlaseni",
                "../metadata",
                archive_directory=archive_directory,
            )
            bad_archive_symlink = resolve_email_archive_file(
                "linked-archive",
                "body_html",
                archive_directory=archive_directory,
            )
            bad_file_symlink = resolve_email_archive_file(
                "email-13338-prihlaseni",
                "body_html",
                archive_directory=archive_directory,
            )
            bad_attachment = resolve_email_archive_incoming_file(
                "../icloud_uid_13338_link.pdf",
                documents_dir=documents_dir,
            )
            bad_attachment_symlink = resolve_email_archive_incoming_file(
                "icloud_uid_13338_link.pdf",
                documents_dir=documents_dir,
            )

        for result in (
            bad_archive,
            bad_key,
            bad_archive_symlink,
            bad_file_symlink,
            bad_attachment,
            bad_attachment_symlink,
        ):
            self.assertFalse(result["ok"])

    def test_incoming_resolver_preserves_content_types_and_name_boundary(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            documents_dir = Path(temp_dir) / "documents"
            incoming = documents_dir / "inbox" / "incoming"
            incoming.mkdir(parents=True)
            expected = {
                "icloud_uid_1_file.pdf": "application/pdf",
                "icloud_uid_1_file.docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "icloud_uid_1_file.webp": "image/webp",
                "icloud_uid_1_file.bin": "application/octet-stream",
            }
            for name in expected:
                (incoming / name).write_bytes(b"test")

            resolved = {
                name: resolve_email_archive_incoming_file(name, documents_dir=documents_dir)
                for name in expected
            }
            invalid = [
                resolve_email_archive_incoming_file("", documents_dir=documents_dir),
                resolve_email_archive_incoming_file(".icloud_uid_1_file.pdf", documents_dir=documents_dir),
                resolve_email_archive_incoming_file("attachment.pdf", documents_dir=documents_dir),
            ]

        for name, content_type in expected.items():
            self.assertTrue(resolved[name]["ok"])
            self.assertEqual(resolved[name]["content_type"], content_type)
        self.assertTrue(all(not item["ok"] for item in invalid))

    def test_archive_reads_do_not_change_fixture_files(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            archive_directory, _archive_dir, documents_dir = self.create_archive_fixture(root)

            before = {
                str(path.relative_to(root)): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            email_archive_list_status(archive_directory=archive_directory)
            email_archive_detail_status(
                "email-13338-prihlaseni",
                archive_directory=archive_directory,
                documents_dir=documents_dir,
            )
            downloaded_email_archive_attachments(uid="not-numeric", documents_dir=documents_dir)
            after = {
                str(path.relative_to(root)): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }

        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
