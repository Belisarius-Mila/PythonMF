from __future__ import annotations

import json
import random
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from app import article_archive as archive
from app import library_photo_compaction as compact
from app.capabilities.registry import get_capability
from app.file_persistence import atomic_write_json
from app.library_images import MAX_LIBRARY_STORED_PHOTO_BYTES


class LibraryPhotoCompactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "archive"
        self.review = self.base / "review"
        self.item = archive.archive_text_entry(title="Synthetic private title", text="Preserve this exact text",
                                                category="travel_places", tags=["synthetic"], archive_root=self.root)["item"]
        image = Image.frombytes("RGB", (600, 500), random.Random(12).randbytes(600 * 500 * 3))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        raw = buffer.getvalue()
        attached = archive.attach_article_image(article_id=self.item["id"], image_bytes=raw, filename="photo.png",
                                                label="Keep label", note="Keep note", archive_root=self.root,
                                                request_id="a" * 32, user_confirmed=True,
                                                confirmation_text=archive.ATTACHMENT_CONFIRMATION_PHRASE)
        self.attachment_id = attached["attachment"]["id"]
        self.metadata_path = self.root / "articles" / self.item["id"] / "metadata.json"
        metadata = json.loads(self.metadata_path.read_text())
        attachment = metadata["attachments"][0]
        original = self.metadata_path.parent / "attachments" / "original" / "legacy.png"
        original.parent.mkdir()
        original.write_bytes(raw)
        readable, thumb = archive.build_readable_image_versions(raw)
        (self.root / attachment["readable_file"]).write_bytes(readable)
        (self.root / attachment["thumb_file"]).write_bytes(thumb)
        attachment.update(original_file=str(original.relative_to(self.root)), size_bytes=len(raw),
                          readable_size_bytes=len(readable), thumb_size_bytes=len(thumb))
        attachment.pop("storage_policy")
        attachment.pop("stored_size_bytes")
        # A non-image attachment must remain byte-identical and keep its metadata.
        self.pdf_path = original.parent / "source.pdf"
        self.pdf_path.write_bytes(b"%PDF-1.4 synthetic unmodified source")
        self.pdf_metadata = {"id": "source-pdf", "kind": "pdf", "role": "original_article_pdf",
                             "original_file": str(self.pdf_path.relative_to(self.root)), "mime_type": "application/pdf"}
        metadata["attachments"].append(self.pdf_metadata)
        atomic_write_json(self.metadata_path, metadata)
        archive.update_registry(self.root / "registry.jsonl", metadata)
        self.before = self.snapshot()

    def snapshot(self):
        return {str(path.relative_to(self.root)): path.read_bytes()
                for path in self.root.rglob("*") if path.is_file() and not path.name.endswith(".lock")}

    def prepare(self):
        result = compact.prepare_library_photo_compaction(archive_root=self.root, review_root=self.review)
        return Path(result["plan_dir"]), result

    def apply(self, plan_dir):
        return compact.apply_library_photo_compaction(plan_dir=plan_dir, archive_root=self.root,
                                                       user_confirmed=True, confirmation_text=compact.COMPACTION_CONFIRMATION)

    def test_prepare_does_not_change_archive_and_holds_total_budget(self):
        plan_dir, result = self.prepare()
        self.assertEqual(self.before, self.snapshot())
        self.assertFalse(result["archive_writes"])
        self.assertEqual(result["image_count"], 1)
        self.assertLessEqual(result["after_bytes"], MAX_LIBRARY_STORED_PHOTO_BYTES)
        self.assertNotIn("Synthetic private title", json.dumps(result))
        self.assertFalse((plan_dir / "backup").exists())

    def test_apply_and_restore_require_exact_global_phrase_before_writes(self):
        plan_dir, _ = self.prepare()
        for operation in (compact.apply_library_photo_compaction, compact.restore_library_photo_compaction):
            for confirmed, phrase in ((False, compact.COMPACTION_CONFIRMATION), (True, "ano"), (True, "")):
                with self.subTest(operation=operation.__name__, phrase=phrase), self.assertRaises(ValueError):
                    operation(plan_dir=plan_dir, archive_root=self.root, user_confirmed=confirmed, confirmation_text=phrase)
        self.assertEqual(self.before, self.snapshot())
        self.assertFalse((plan_dir / "backup").exists())

    def test_apply_preserves_text_pdf_identity_and_all_three_download_variants(self):
        plan_dir, preview = self.prepare()
        result = self.apply(plan_dir)
        self.assertEqual(result["state"], "applied")
        self.assertEqual(result["after_bytes"], preview["after_bytes"])
        self.assertTrue(result["backup_retained"])
        metadata = json.loads(self.metadata_path.read_text())
        attachment = metadata["attachments"][0]
        self.assertEqual(attachment["id"], self.attachment_id)
        self.assertEqual(attachment["label"], "Keep label")
        self.assertEqual(attachment["note"], "Keep note")
        self.assertEqual(metadata["attachments"][1], self.pdf_metadata)
        self.assertEqual(archive.read_article_text(self.item["id"], archive_root=self.root).strip(), "Preserve this exact text")
        self.assertEqual(self.pdf_path.read_bytes(), self.before[str(self.pdf_path.relative_to(self.root))])
        paths = set()
        for variant in ("original", "readable", "thumb"):
            response = archive.get_article_attachment(article_id=self.item["id"], attachment_id=self.attachment_id,
                                                       variant=variant, archive_root=self.root)
            self.assertTrue(response["ok"])
            paths.add(response["path"])
        self.assertEqual(len(paths), 2)
        self.assertLessEqual(sum(p.stat().st_size for p in paths), MAX_LIBRARY_STORED_PHOTO_BYTES)
        for relative in json.loads((plan_dir / "plan.json").read_text())["items"][0]["old_files"]:
            self.assertFalse((self.root / relative).exists())
            self.assertEqual((plan_dir / "backup" / relative).read_bytes(), self.before[relative])
        self.assertTrue(self.apply(plan_dir)["replayed"])
        _, subsequent = self.prepare()
        self.assertEqual(subsequent["image_count"], 0)

    def test_stale_metadata_registry_or_photo_blocks_apply_before_backup(self):
        for field in ("metadata", "registry", "photo"):
            with self.subTest(field=field):
                plan_dir, _ = self.prepare()
                plan = json.loads((plan_dir / "plan.json").read_text())
                path = {"metadata": self.metadata_path, "registry": self.root / "registry.jsonl",
                        "photo": self.root / plan["items"][0]["old_files"][0]}[field]
                original = path.read_bytes()
                path.write_bytes(original + b" ")
                changed = self.snapshot()
                with self.assertRaisesRegex(ValueError, "změnila"):
                    self.apply(plan_dir)
                self.assertEqual(changed, self.snapshot())
                self.assertFalse((plan_dir / "backup").exists())
                path.write_bytes(original)

    def test_changed_prepared_photo_is_rejected(self):
        plan_dir, _ = self.prepare()
        (plan_dir / "prepared/001.jpg").write_bytes(b"not the reviewed picture")
        with self.assertRaisesRegex(ValueError, "fotografie byla změněna"):
            self.apply(plan_dir)
        self.assertEqual(self.before, self.snapshot())

    def test_registry_failure_rolls_back_new_images_and_metadata(self):
        plan_dir, _ = self.prepare()
        with patch.object(compact, "update_registry", side_effect=OSError("synthetic write failure")):
            with self.assertRaises(OSError):
                self.apply(plan_dir)
        self.assertEqual(self.before, self.snapshot())
        self.assertEqual(json.loads((plan_dir / "receipt.json").read_text())["state"], "rolled_back")

    def test_cleanup_failure_restores_already_removed_originals(self):
        plan_dir, _ = self.prepare()
        old_files = json.loads((plan_dir / "plan.json").read_text())["items"][0]["old_files"]
        failing_path = (self.root / sorted(old_files)[-1]).resolve()
        unlink = Path.unlink
        fail = True

        def interrupted(path, *args, **kwargs):
            nonlocal fail
            if path == failing_path and fail:
                fail = False
                raise OSError("synthetic cleanup interruption")
            return unlink(path, *args, **kwargs)

        with patch.object(Path, "unlink", interrupted), self.assertRaises(OSError):
            self.apply(plan_dir)
        self.assertEqual(self.before, self.snapshot())

    def test_verified_restore_is_exact_and_refuses_subsequent_edits(self):
        plan_dir, _ = self.prepare()
        self.apply(plan_dir)
        registry = self.root / "registry.jsonl"
        original = registry.read_bytes()
        # Use a semantically different registry, not merely harmless whitespace.
        rows = [json.loads(line) for line in original.decode().splitlines()]
        rows[0]["title"] = "Later user edit"
        registry.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
        with self.assertRaisesRegex(ValueError, "změnil registr"):
            compact.restore_library_photo_compaction(plan_dir=plan_dir, archive_root=self.root,
                                                     user_confirmed=True, confirmation_text=compact.COMPACTION_CONFIRMATION)
        registry.write_bytes(original)
        restored = compact.restore_library_photo_compaction(plan_dir=plan_dir, archive_root=self.root,
                                                            user_confirmed=True, confirmation_text=compact.COMPACTION_CONFIRMATION)
        self.assertEqual(restored["state"], "restored")
        self.assertEqual(self.before, self.snapshot())

    def test_interrupted_process_is_recoverable_from_verified_backup(self):
        plan_dir, _ = self.prepare()
        with patch.object(compact, "update_registry", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.apply(plan_dir)
        self.assertEqual(json.loads((plan_dir / "receipt.json").read_text())["state"], "applying")
        compact.restore_library_photo_compaction(plan_dir=plan_dir, archive_root=self.root,
                                                 user_confirmed=True, confirmation_text=compact.COMPACTION_CONFIRMATION)
        self.assertEqual(self.before, self.snapshot())

    def test_cross_card_attachment_path_is_refused(self):
        metadata = json.loads(self.metadata_path.read_text())
        metadata["attachments"][0]["original_file"] = "registry.jsonl"
        self.metadata_path.write_text(json.dumps(metadata))
        archive.update_registry(self.root / "registry.jsonl", metadata)
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "adresáři příloh"):
            self.prepare()
        self.assertEqual(before, self.snapshot())

    def test_inconsistent_registry_is_not_silently_repaired_by_compaction(self):
        metadata = json.loads(self.metadata_path.read_text())
        metadata["title"] = "Unregistered metadata change"
        self.metadata_path.write_text(json.dumps(metadata))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "registr nesouhlasí"):
            self.prepare()
        self.assertEqual(before, self.snapshot())

    def test_registered_operations_have_separate_prepare_and_confirmed_apply(self):
        self.assertFalse(get_capability("prepare_library_photo_compaction").requires_confirmation)
        for name in ("apply_library_photo_compaction", "restore_library_photo_compaction", "delete_library_photo_compaction_backup"):
            capability = get_capability(name)
            self.assertTrue(capability.requires_confirmation)
            self.assertEqual(str(capability.risk), "destructive")
            self.assertEqual(str(capability.confirmation_policy), "exact_phrase")

    def delete_backup(self, directory):
        return compact.delete_library_photo_compaction_backup(
            plan_dir=directory, archive_root=self.root, user_confirmed=True,
            confirmation_text=compact.COMPACTION_CONFIRMATION)

    def test_backup_deletion_preserves_archive_previews_receipts_and_other_backup(self):
        directory, _ = self.prepare()
        applied = self.apply(directory)
        before = self.snapshot()
        retained = {p: p.read_bytes() for p in (directory / "prepared").iterdir()}
        other = self.review / "other-backup"
        other.mkdir()
        (other / "keep").write_bytes(b"keep this backup")
        result = self.delete_backup(directory)
        self.assertEqual(result["deleted_logical_bytes"], applied["backup_bytes"])
        self.assertFalse((directory / "backup").exists())
        self.assertEqual(before, self.snapshot())
        self.assertTrue(all(p.read_bytes() == raw for p, raw in retained.items()))
        self.assertEqual((other / "keep").read_bytes(), b"keep this backup")
        self.assertTrue(self.delete_backup(directory)["replayed"])
        self.assertFalse(self.apply(directory)["backup_retained"])
        with self.assertRaisesRegex(ValueError, "obnova není dostupná"):
            compact.restore_library_photo_compaction(plan_dir=directory, archive_root=self.root,
                user_confirmed=True, confirmation_text=compact.COMPACTION_CONFIRMATION)

    def test_backup_deletion_rejects_missing_confirmation_and_unapplied_plan(self):
        directory, _ = self.prepare()
        with self.assertRaises(ValueError):
            self.delete_backup(directory)
        self.apply(directory)
        for confirmed, phrase in ((False, compact.COMPACTION_CONFIRMATION), (True, "ano")):
            with self.assertRaises(ValueError):
                compact.delete_library_photo_compaction_backup(plan_dir=directory, archive_root=self.root,
                    user_confirmed=confirmed, confirmation_text=phrase)
        self.assertTrue((directory / "backup").is_dir())

    def test_backup_deletion_rejects_changed_archive_before_any_deletion(self):
        directory, _ = self.prepare()
        self.apply(directory)
        self.metadata_path.write_bytes(self.metadata_path.read_bytes() + b" ")
        backup = {p: p.read_bytes() for p in (directory / "backup").rglob("*") if p.is_file()}
        with self.assertRaisesRegex(ValueError, "Knihovna se"):
            self.delete_backup(directory)
        self.assertTrue(all(p.read_bytes() == raw for p, raw in backup.items()))

    def test_backup_deletion_preserves_later_unrelated_card(self):
        directory, _ = self.prepare()
        self.apply(directory)
        archive.archive_text_entry(title="Later unrelated card", text="Keep later work", archive_root=self.root)
        before = self.snapshot()
        self.assertTrue(self.delete_backup(directory)["ok"])
        self.assertEqual(before, self.snapshot())

    def test_backup_deletion_rejects_drift_in_converted_card_registry(self):
        directory, _ = self.prepare()
        self.apply(directory)
        registry = self.root / "registry.jsonl"
        row = json.loads(registry.read_text())
        row["title"] = "Registry-only change"
        registry.write_text(json.dumps(row) + "\n")
        with self.assertRaisesRegex(ValueError, "Registr převedených"):
            self.delete_backup(directory)
        self.assertTrue((directory / "backup").is_dir())

    def test_backup_deletion_rejects_unexpected_modified_and_symlinked_files(self):
        directory, _ = self.prepare()
        self.apply(directory)
        backup = directory / "backup"
        registry = backup / "registry.jsonl"
        raw = registry.read_bytes()
        extra = backup / "unrelated"
        extra.write_bytes(b"do not delete")
        with self.assertRaisesRegex(ValueError, "nečekaný"):
            self.delete_backup(directory)
        extra.unlink()
        registry.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "nesouhlasí"):
            self.delete_backup(directory)
        registry.unlink()
        registry.symlink_to(self.root / "registry.jsonl")
        with self.assertRaisesRegex(ValueError, "nečekaný"):
            self.delete_backup(directory)
        registry.unlink()
        registry.write_bytes(raw)
        backup.rename(directory / "original-backup")
        backup.symlink_to(directory / "original-backup", target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symbolický"):
            self.delete_backup(directory)
        self.assertEqual((directory / "original-backup" / "registry.jsonl").read_bytes(), raw)

    def test_backup_deletion_resumes_after_interrupted_file_removal(self):
        directory, _ = self.prepare()
        self.apply(directory)
        before = self.snapshot()
        original = Path.unlink
        count = 0
        def interrupt(path, *args, **kwargs):
            nonlocal count
            if directory / "backup" in path.parents:
                count += 1
                if count == 2:
                    raise OSError("synthetic interruption")
            return original(path, *args, **kwargs)
        with patch.object(Path, "unlink", interrupt), self.assertRaises(OSError):
            self.delete_backup(directory)
        self.assertEqual(self.delete_backup(directory)["state"], "backup_deleted")
        self.assertEqual(before, self.snapshot())


if __name__ == "__main__":
    unittest.main()
