"""Curated IT export: identity, immutable sources/assets, explicit preview."""
from __future__ import annotations
import copy
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "VocabularyIT"))
import vocabulary_it_catalog as catalog
import vocabulary_it_export as export


class VocabularyItalianExportTests(unittest.TestCase):
    def fixture(self, root):
        (root / "Pict").mkdir()
        image = root / "Pict/Photo.webp"
        Image.new("RGB", (500, 350), "red").save(image)
        rows = catalog.load_rows(ROOT / "VocabularyIT/VocabularyIT.csv")[:2]
        csv_path = root / "VocabularyIT/VocabularyIT.csv"
        csv_path.parent.mkdir()
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=catalog.COLUMNS)
            writer.writeheader(); writer.writerows(rows)
        document = catalog.load_catalog()
        document["entries"] = copy.deepcopy([document["entries"][0], document["entries"][1], document["entries"][471]])
        sha = catalog.digest(image)
        for entry in document["entries"]:
            entry.update(imageFile="Pict/Photo.webp", imageSha256=sha, related=[], imageStatus="reviewed")
        record = {"sha256": sha, "bytes": image.stat().st_size, "kind": "image"}
        inputs = {"schemaVersion": 1, "project": "VocabularyIT", "files": {
            "Pict/Photo.webp": record,
            "VocabularyIT/VocabularyIT.csv": {"sha256": catalog.digest(csv_path), "bytes": csv_path.stat().st_size, "kind": "source"}}}
        cp, mp, ip = root / "catalog.json", root / "inputs.json", root / "images.json"
        cp.write_text(json.dumps(document)); mp.write_text(json.dumps(inputs))
        images = {"schemaVersion": 1, "project": "VocabularyIT-images", "foundationManifestSha256": catalog.digest(mp), "files": {"Pict/Photo.webp": record}}
        ip.write_text(json.dumps(images))
        return dict(catalog_path=cp, manifest_path=mp, image_manifest_path=ip)

    def test_export_includes_explicit_new_meanings_without_migrating_personal_flags(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); args = self.fixture(root)
            before = (root / "VocabularyIT/VocabularyIT.csv").read_bytes()
            payload, assets = export.prepare_export(root, **args)
            proof = catalog.audit(root, args["catalog_path"], args["manifest_path"], args["image_manifest_path"])
            self.assertEqual(sum(proof["teachingTypes"].values()), proof["cards"])
            self.assertEqual(sum(proof["topicCounts"].values()), proof["cards"])
            self.assertEqual((payload["itemCount"], payload["sourceRowCount"]), (3, 2))
            self.assertEqual([item["uid"] for item in payload["items"]], ["vit-0001", "vit-0002", "vit-0472"])
            self.assertEqual(payload["items"][2]["it"], "forte")
            self.assertEqual(payload["items"][2]["cz"], "nahlas")
            self.assertEqual(payload["items"][2]["addedAt"], "2026-11-15")
            self.assertIsNone(payload["items"][0]["addedAt"])
            self.assertTrue(payload["imageReviewComplete"])
            self.assertEqual(payload["stats"]["uniqueSourceImages"], 1)
            self.assertEqual(len(assets), 2)
            for item in payload["items"]:
                self.assertNotIn("L", item); self.assertNotIn("HT", item)
                self.assertIn(item["image"], assets); self.assertIn(item["thumbnail"], assets)
            self.assertEqual((root / "VocabularyIT/VocabularyIT.csv").read_bytes(), before)
            import io
            thumb = Image.open(io.BytesIO(assets[payload["items"][0]["thumbnail"]]))
            self.assertLessEqual(max(thumb.size), 240)

    def test_changed_source_or_image_aborts_before_any_output(self):
        for changed in ("csv", "image"):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as name:
                root = Path(name); args = self.fixture(root)
                target = root / ("VocabularyIT/VocabularyIT.csv" if changed == "csv" else "Pict/Photo.webp")
                target.write_bytes(target.read_bytes() + b"changed")
                with self.assertRaises(ValueError): export.prepare_export(root, **args)
                self.assertFalse((root / "output").exists())

    def test_changes_during_conversion_cannot_escape_source_pins(self):
        for relative in ("Pict/Photo.webp", "VocabularyIT/VocabularyIT.csv", "catalog.json"):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as name:
                root = Path(name); args = self.fixture(root)
                def concurrent_change(*unused):
                    path = root / relative
                    path.write_bytes(path.read_bytes() + b" ")
                    return {}
                with patch.object(export, "candidate_files", side_effect=concurrent_change):
                    with self.assertRaisesRegex(ValueError, "během přípravy"):
                        export.prepare_export(root, **args)

    def pending_fixture(self, root, args):
        document = json.loads(args["catalog_path"].read_text())
        document["entries"][0].update(imageStatus="replacement-needed", imageFile=None)
        args["catalog_path"].write_text(json.dumps(document))
        candidate_root = root / "candidates"; candidate_root.mkdir()
        candidate = candidate_root / "one.webp"
        Image.new("RGB", (30, 30), "blue").save(candidate)
        report = {"schemaVersion": 1, "project": "VocabularyIT-candidates", "items": [{
            "uid": "vit-0001", "file": "one.webp", "sha256": catalog.digest(candidate),
            "bytes": candidate.stat().st_size, "status": "awaiting-visual-approval"}]}
        (candidate_root / "generation_report.json").write_text(json.dumps(report))
        return candidate_root

    def test_unapproved_candidate_only_enters_explicit_preview(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); args = self.fixture(root); candidates = self.pending_fixture(root, args)
            with self.assertRaises(ValueError): export.prepare_export(root, **args)
            with self.assertRaises(ValueError): export.prepare_export(root, candidates=candidates, **args)
            with self.assertRaises(ValueError): export.prepare_export(root, preview=True, **args)
            payload, _ = export.prepare_export(root, preview=True, candidates=candidates, **args)
            self.assertEqual(payload["mode"], "preview")
            self.assertFalse(payload["imageReviewComplete"])
            self.assertFalse(payload["items"][0]["imageReviewed"])
            self.assertTrue(payload["items"][1]["imageReviewed"])

    def test_candidate_hash_path_uid_and_duplicate_must_match(self):
        for change in ("bytes", "path", "uid", "duplicate", "status"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as name:
                root = Path(name); args = self.fixture(root); candidates = self.pending_fixture(root, args)
                path = candidates / "generation_report.json"; report = json.loads(path.read_text()); item = report["items"][0]
                if change == "bytes": (candidates / "one.webp").write_bytes(b"wrong")
                if change == "path": item["file"] = "../one.webp"
                if change == "uid": item["uid"] = "vit-9999"
                if change == "duplicate": report["items"].append(item.copy())
                if change == "status": item["status"] = "generated"
                path.write_text(json.dumps(report))
                with self.assertRaises(ValueError): export.prepare_export(root, preview=True, candidates=candidates, **args)

    def test_web_meaning_needs_complete_text_and_cannot_replace_legacy_source(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); args = self.fixture(root); document = catalog.load_catalog(args["catalog_path"])
            rows = catalog.load_rows(root / "VocabularyIT/VocabularyIT.csv")
            with self.assertRaises(ValueError): catalog.resolve_catalog_rows(rows[:-1], document, require_all=True)
            document["entries"][2]["webText"]["sentenceIt"] = ""
            with self.assertRaises(ValueError): catalog.validate_catalog(document)

    def test_new_reviewed_image_extends_pins_without_rewriting_original_manifest(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); args = self.fixture(root)
            before = args["manifest_path"].read_bytes()
            image = root / 'Pict/New.webp'; Image.new('RGB', (50, 50), 'green').save(image)
            doc = json.loads(args['catalog_path'].read_text())
            doc['entries'][0].update(imageFile='Pict/New.webp', imageSha256=catalog.digest(image))
            args['catalog_path'].write_text(json.dumps(doc))
            manifest = json.loads(args['image_manifest_path'].read_text())
            manifest['files']['Pict/New.webp'] = {'sha256': catalog.digest(image), 'bytes': image.stat().st_size}
            args['image_manifest_path'].write_text(json.dumps(manifest))
            with self.assertRaises(ValueError): catalog.verify_input_manifest(root, json.loads(before))
            proof = catalog.audit(root, args['catalog_path'], args['manifest_path'], args['image_manifest_path'])
            self.assertEqual(proof['additionalPinnedImages'], 1)
            self.assertEqual(args['manifest_path'].read_bytes(), before)
            export.prepare_export(root, **args)
            image.write_bytes(b'changed')
            with self.assertRaises(ValueError): export.prepare_export(root, **args)

    def test_atomic_json_last_and_repeatable_assets_preserve_other_apps(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); args = self.fixture(root); payload, assets = export.prepare_export(root, **args)
            out = root / "out"; (out / "data").mkdir(parents=True)
            unrelated = out / "data/vocabulary-en.json"; unrelated.write_text('unchanged')
            export.write_export(out, payload, assets)
            before = {p.relative_to(out).as_posix(): p.read_bytes() for p in out.rglob('*') if p.is_file()}
            export.write_export(out, payload, assets)
            after = {p.relative_to(out).as_posix(): p.read_bytes() for p in out.rglob('*') if p.is_file()}
            self.assertEqual(before, after)
            self.assertEqual(unrelated.read_text(), 'unchanged')
            old_data = (out / "data" / export.DATA_NAME).read_bytes()
            with patch.object(export.os, 'replace', side_effect=OSError('interrupted')):
                with self.assertRaises(OSError): export.write_export(out, {**payload, 'mode': 'preview'}, assets)
            self.assertEqual((out / "data" / export.DATA_NAME).read_bytes(), old_data)

    def test_corrupt_immutable_asset_and_foreign_json_are_never_overwritten(self):
        for change in ("asset", "json"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as name:
                root = Path(name); args = self.fixture(root); payload, assets = export.prepare_export(root, **args)
                out = root / "out"; export.write_export(out, payload, assets)
                victim = out / (next(iter(assets)) if change == "asset" else "data/" + export.DATA_NAME)
                corrupted = b'foreign content' if change == "asset" else b'{"appName":"Other","schemaVersion":2}'
                victim.write_bytes(corrupted)
                with self.assertRaises(ValueError): export.write_export(out, payload, assets)
                self.assertEqual(victim.read_bytes(), corrupted)

    def test_output_symlink_cannot_write_outside_export_root(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); args = self.fixture(root); payload, assets = export.prepare_export(root, **args)
            out = root / 'out'; outside = root / 'outside'; out.mkdir(); outside.mkdir()
            (out / 'assets').symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError): export.write_export(out, payload, assets)
            self.assertEqual(list(outside.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
