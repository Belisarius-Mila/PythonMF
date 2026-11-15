"""Italian migration identities and closed inputs; no legacy source writes."""
from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unicodedata
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("italian_catalog", ROOT / "VocabularyIT/vocabulary_it_catalog.py")
it = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(it)


class VocabularyItalianCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = it.load_catalog()
        cls.rows = it.load_rows(ROOT / "VocabularyIT/VocabularyIT.csv")
        cls.snapshot = json.loads(it.MANIFEST.read_text())

    def test_all_471_source_meanings_keep_identity_gender_sentences_and_flags(self):
        before = (ROOT / "VocabularyIT/VocabularyIT.csv").read_bytes()
        resolved = it.resolve_catalog_rows(self.rows, self.catalog, require_all=True)
        self.assertEqual(len(resolved), 471)
        self.assertEqual({entry["uid"] for entry in resolved}, {f"vit-{n:04d}" for n in range(1, 472)})
        self.assertTrue(all(entry["active"] for entry in resolved))
        self.assertEqual(sum(bool(row["Sentence"]) and bool(row["SentenceT"]) for row in self.rows), 471)
        self.assertEqual(sum(row["gender_it"] == "m" for row in self.rows), 115)
        self.assertEqual(sum(row["gender_it"] == "f" for row in self.rows), 86)
        self.assertEqual(sum(row["L"] == "ano" for row in self.rows), 10)
        self.assertEqual(sum(row["HT"] == "ano" for row in self.rows), 260)
        self.assertEqual(hashlib.sha256(before).hexdigest(), self.snapshot["files"]["VocabularyIT/VocabularyIT.csv"]["sha256"])
        self.assertEqual(before, (ROOT / "VocabularyIT/VocabularyIT.csv").read_bytes())
        self.assertFalse(any("L" in entry or "HT" in entry for entry in resolved))

    def test_order_and_physical_row_reordering_cannot_reassign_identities(self):
        rows = copy.deepcopy(list(reversed(self.rows)))
        for number, row in enumerate(rows, 700):
            row["Order"] = str(number)
        before = copy.deepcopy(rows)
        result = it.resolve_catalog_rows(rows, self.catalog, require_all=True)
        self.assertEqual([entry["uid"] for entry in result], [f"vit-{n:04d}" for n in range(471, 0, -1)])
        self.assertEqual(rows, before)

    def test_homographs_and_genders_are_distinct_meanings_not_spelling_duplicates(self):
        by_id = {entry["id"]: entry for entry in self.catalog["entries"]}
        for first, second in [(2, 3), (12, 13), (35, 36), (76, 77), (79, 80), (97, 98)]:
            self.assertNotEqual(by_id[first]["uid"], by_id[second]["uid"])
            result = it.resolve_catalog_rows([self.rows[first - 1], self.rows[second - 1]], self.catalog)
            self.assertEqual([entry["id"] for entry in result], [first, second])
        self.assertEqual(by_id[12]["cz"], "peněženka")
        self.assertEqual(by_id[13]["cz"], "portfolio (soubor investic)")

    def test_unknown_duplicated_or_missing_meanings_fail_without_order_fallback(self):
        unknown = {**self.rows[0], "IT": "parola nuova"}
        with self.assertRaisesRegex(ValueError, "Neznámý význam"):
            it.resolve_catalog_rows([unknown], self.catalog)
        with self.assertRaisesRegex(ValueError, "tutéž identitu"):
            it.resolve_catalog_rows([self.rows[0], self.rows[0]], self.catalog)
        with self.assertRaisesRegex(ValueError, "nepokrývá"):
            it.resolve_catalog_rows(self.rows[:-1], self.catalog, require_all=True)

    def test_unicode_composition_matches_but_accents_and_case_remain_semantic(self):
        row = {**self.rows[284], "IT": unicodedata.normalize("NFD", "caffè")}
        self.assertEqual(it.resolve_catalog_rows([row], self.catalog)[0]["uid"], "vit-0285")
        self.assertNotEqual(it.identity("e", "a"), it.identity("è", "a"))
        self.assertNotEqual(it.identity("x", "byt"), it.identity("x", "být"))
        self.assertNotEqual(it.identity("Lei", "x"), it.identity("lei", "x"))
        with self.assertRaises(ValueError):
            it.resolve_catalog_rows([{**self.rows[284], "IT": "caffe"}], self.catalog)

    def test_explicit_alias_can_preserve_old_meaning_without_creating_a_new_uid(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["entries"][0]["matches"].append({"it": "il piatto", "cz": "talíř"})
        result = it.resolve_catalog_rows([{**self.rows[0], "IT": "il piatto"}], catalog)
        self.assertEqual(result[0]["uid"], "vit-0001")
        self.assertEqual(it.resolve_catalog_rows(self.rows[:1], catalog)[0]["uid"], "vit-0001")

    def test_catalog_rejects_foreign_duplicate_and_conflicting_identities(self):
        for change in ("foreign", "duplicate", "alias", "topic", "dangling-form", "retag"):
            with self.subTest(change=change):
                catalog = copy.deepcopy(self.catalog)
                first = catalog["entries"][0]
                if change == "foreign": first["uid"] = "ven-0001"
                if change == "duplicate": catalog["entries"][1]["id"] = 1
                if change == "alias": first["matches"].append(copy.deepcopy(catalog["entries"][1]["matches"][0]))
                if change == "topic": first["primaryGroup"] = "topic-99"
                if change == "dangling-form": first["formOfUid"] = "vit-9999"
                if change == "retag": first["partOfSpeech"] = ["made-up"]
                with self.assertRaises(ValueError): it.validate_catalog(catalog)

    def test_malformed_catalog_shapes_fail_explicitly(self):
        for change in ("groups", "entry", "alias", "relation", "reasons"):
            with self.subTest(change=change):
                catalog = copy.deepcopy(self.catalog)
                if change == "groups": catalog["groups"] = None
                if change == "entry": catalog["entries"][0] = None
                if change == "alias": catalog["entries"][0]["matches"] = [None]
                if change == "relation": catalog["entries"][0]["related"] = [None]
                if change == "reasons": catalog["reviewCodes"] = None
                with self.assertRaises(ValueError): it.validate_catalog(catalog)

    def test_all_metadata_are_proposals_and_verb_forms_remain_active(self):
        entries = self.catalog["entries"]
        self.assertEqual(len(self.catalog["groups"]), 18)
        self.assertEqual({entry["primaryGroup"] for entry in entries}, {f"topic-{n:02d}" for n in range(1, 19)})
        self.assertTrue(all(entry["editorialStatus"] == "needs-review" for entry in entries))
        self.assertTrue(all(entry["difficultyStatus"] == "proposed" for entry in entries))
        self.assertTrue(all(entry["imageFile"] is None and entry["imageStatus"] == "pending-review" for entry in entries))
        self.assertTrue(all(entry["legacyAddedAt"] is None for entry in entries))
        self.assertEqual(entries[465]["formOfUid"], "vit-0467")
        self.assertEqual(entries[469]["formOfUid"], "vit-0205")
        self.assertEqual(entries[470]["lemma"], "quello")
        for n in (466, 470, 471): self.assertTrue(entries[n - 1]["active"])
        self.assertEqual(sum(entry["teachingType"] == "interaction" for entry in entries), 11)
        self.assertTrue(all(entry["teachingType"] == "word" or not entry["partOfSpeech"] for entry in entries))

    def test_source_manifest_has_precise_image_names_and_sha_for_every_pinned_input(self):
        images = {name: record for name, record in self.snapshot["files"].items() if record["kind"] == "image"}
        self.assertEqual(len(images), 761)
        self.assertEqual(len(self.snapshot["files"]), 777)
        for name, record in images.items():
            self.assertTrue(name.startswith("Pict/"), name)
            self.assertRegex(record["sha256"], r"^[0-9a-f]{64}$")
            self.assertGreater(record["width"], 0)
            self.assertGreater(record["height"], 0)
        self.assertEqual(it.digest(ROOT / "Pict/mapping.json"), self.snapshot["files"]["Pict/mapping.json"]["sha256"])

    def fixture(self, root):
        files = {"Pict/Photo.webp": b"fixture-image", "VocabularyIT/source.txt": b"source"}
        manifest = {"schemaVersion": 1, "project": "VocabularyIT", "files": {}}
        for name, data in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            manifest["files"][name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                                       "kind": "image" if name.startswith("Pict/") else "source"}
        return manifest

    def test_closed_snapshot_detects_changed_or_missing_bytes_and_additional_images(self):
        for change in ("changed", "missing", "extra"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                manifest = self.fixture(root)
                self.assertEqual(it.verify_input_manifest(root, manifest), {"verifiedFiles": 2, "verifiedImages": 1, "exact": True})
                if change == "changed": (root / "VocabularyIT/source.txt").write_bytes(b"SOURCE")
                if change == "missing": (root / "VocabularyIT/source.txt").rename(root / "VocabularyIT/elsewhere.txt")
                if change == "extra": (root / "Pict/another.png").write_bytes(b"extra")
                with self.assertRaises(ValueError): it.verify_input_manifest(root, manifest)

    def test_case_mismatch_and_paths_outside_input_root_are_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            manifest = self.fixture(root)
            record = manifest["files"].pop("Pict/Photo.webp")
            manifest["files"]["Pict/photo.webp"] = record
            with self.assertRaisesRegex(ValueError, "písmen"):
                it.verify_input_manifest(root, manifest)
            manifest["files"] = {"../escape": record}
            with self.assertRaisesRegex(ValueError, "cesta"):
                it.verify_input_manifest(root, manifest)

    def test_csv_reader_never_repairs_bad_source_rows(self):
        for change in ("gender", "flags", "sentence", "order"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as name:
                rows = copy.deepcopy(self.rows[:2])
                if change == "gender": rows[0]["gender_it"] = "unknown"
                if change == "flags": rows[0]["HT"] = "maybe"
                if change == "sentence": rows[0]["SentenceT"] = ""
                if change == "order": rows[1]["Order"] = rows[0]["Order"]
                path = Path(name) / "source.csv"
                with path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=it.COLUMNS)
                    writer.writeheader()
                    writer.writerows(rows)
                before = path.read_bytes()
                with self.assertRaises(ValueError): it.load_rows(path)
                self.assertEqual(path.read_bytes(), before)

    def test_complete_audit_uses_the_explicit_input_root_without_rewriting_it(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            manifest = self.fixture(root)
            path = root / "VocabularyIT/VocabularyIT.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=it.COLUMNS)
                writer.writeheader()
                writer.writerows(self.rows[:2])
            before = path.read_bytes()
            manifest["files"]["VocabularyIT/VocabularyIT.csv"] = {
                "bytes": len(before), "sha256": hashlib.sha256(before).hexdigest(), "kind": "source"}
            catalog = copy.deepcopy(self.catalog)
            catalog["entries"] = catalog["entries"][:2]
            for entry in catalog["entries"]: entry["related"] = []
            catalog_path, manifest_path = root / "catalog.json", root / "inputs.json"
            catalog_path.write_text(json.dumps(catalog))
            manifest_path.write_text(json.dumps(manifest))
            result = it.audit(root, catalog_path, manifest_path)
            self.assertEqual((result["cards"], result["identities"], result["verifiedImages"]), (2, 2, 1))
            self.assertTrue(result["exact"])
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
