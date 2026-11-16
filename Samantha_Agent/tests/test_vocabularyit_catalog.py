"""Italian migration identities and closed inputs; no legacy source writes."""
from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import json
import sys
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

    def test_approved_meanings_keep_remaining_metadata_proposals_and_active_forms(self):
        entries = self.catalog["entries"]
        self.assertEqual(len(self.catalog["groups"]), 18)
        self.assertEqual({entry["primaryGroup"] for entry in entries}, {f"topic-{n:02d}" for n in range(1, 19)})
        self.assertEqual(sum(entry["editorialStatus"] == "reviewed" for entry in entries), 649)
        self.assertTrue(all(entry["difficultyStatus"] == "proposed" for entry in entries))
        self.assertEqual(sum(entry["imageStatus"] == "reviewed" for entry in entries), 1096)
        self.assertEqual(sum(entry["imageStatus"] == "replacement-needed" for entry in entries), 0)
        self.assertEqual(sum(entry["imageStatus"] == "pending-review" for entry in entries), 0)
        self.assertTrue(all(entry["legacyAddedAt"] is None for entry in entries))
        self.assertEqual(entries[465]["formOfUid"], "vit-0467")
        self.assertEqual(entries[469]["formOfUid"], "vit-0205")
        self.assertEqual(entries[470]["lemma"], "quello")
        for n in (466, 470, 471): self.assertTrue(entries[n - 1]["active"])
        self.assertEqual(sum(entry["teachingType"] == "interaction" for entry in entries), 30)
        self.assertTrue(all(entry["teachingType"] == "word" or not entry["partOfSpeech"] for entry in entries[:497]))

    def test_web_corrections_preserve_original_identity_and_reject_stale_sentences(self):
        rows = copy.deepcopy(self.rows)
        entries = it.resolve_catalog_rows(rows, self.catalog, require_all=True)
        text = it.effective_card_text(rows[107], entries[107])
        self.assertTrue(rows[107]["Sentence"].startswith("Je prends"))
        self.assertEqual(text["sentenceIt"], "Dopo il pasto prendo un éclair al cioccolato.")
        self.assertEqual(text["sentenceCz"], rows[107]["SentenceT"])
        self.assertEqual(it.effective_card_text(rows[210], entries[210])["cz"], "volat; telefonovat")
        self.assertEqual(entries[210]["uid"], "vit-0211")
        self.assertEqual(it.resolve_catalog_rows([{**rows[210], "CZ": "volat; telefonovat"}], self.catalog)[0]["uid"], "vit-0211")
        rows[107]["Sentence"] = "Nová zdrojová věta"
        with self.assertRaisesRegex(ValueError, "Zdrojová věta"):
            it.effective_card_text(rows[107], entries[107])
        with self.assertRaisesRegex(ValueError, "jinému významu"):
            it.effective_card_text(rows[0], entries[107])
        self.assertEqual(self.rows, it.load_rows(ROOT / "VocabularyIT/VocabularyIT.csv"))

    def test_accepted_manifest_pins_original_and_new_images_without_rewriting_foundation(self):
        manifest = json.loads((ROOT / "VocabularyIT/vocabulary_it_image_manifest.json").read_text())
        source_files = self.snapshot["files"]
        self.assertEqual(manifest["foundationManifestSha256"], it.digest(it.MANIFEST))
        self.assertEqual(len(manifest["files"]), 659)
        for path, record in manifest["files"].items():
            if path in source_files:
                self.assertEqual(record["sha256"], source_files[path]["sha256"])
                self.assertEqual(record["bytes"], source_files[path]["bytes"])
            else:
                self.assertTrue(path.startswith(("Pict/it_web_vit_", "Pict/it_leda_")))
                self.assertEqual(record["sha256"], it.digest(ROOT / path))
                self.assertEqual(record["bytes"], (ROOT / path).stat().st_size)
        entries = self.catalog["entries"]
        for entry in entries:
            if entry["imageStatus"] == "reviewed":
                self.assertEqual(entry["imageSha256"], manifest["files"][entry["imageFile"]]["sha256"])
            else:
                self.assertIsNone(entry["imageFile"])
        self.assertEqual(entries[135]["imageFile"], "Pict/it_web_vit_0136.webp")  # month, not Moon
        self.assertEqual(entries[400]["imageFile"], "Pict/interpreter.webp")  # language, not tongue

    def image_fixture(self, root):
        source = self.fixture(root)["files"]["Pict/Photo.webp"]
        catalog = copy.deepcopy(self.catalog)
        catalog["entries"] = catalog["entries"][:1]
        entry = catalog["entries"][0]
        entry.update(imageFile="Pict/Photo.webp", imageSha256=source["sha256"],
                     imageStatus="reviewed", imageRole="contextual", related=[])
        manifest = {"schemaVersion": 1, "project": "VocabularyIT-images", "files": {"Pict/Photo.webp": source}}
        return catalog, manifest

    def test_image_pin_rejects_changed_bytes_case_hash_manifest_and_escape(self):
        for change in ("bytes", "case", "sha", "missing", "extra", "escape", "malformed"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                catalog, manifest = self.image_fixture(root)
                self.assertTrue(it.verify_image_bindings(root, catalog, manifest, require_complete=True)["complete"])
                entry = catalog["entries"][0]
                if change == "bytes": (root / "Pict/Photo.webp").write_bytes(b"different")
                if change == "sha": entry["imageSha256"] = "0" * 64
                if change == "missing": manifest["files"] = {}
                if change == "extra": manifest["files"]["Pict/extra.webp"] = manifest["files"]["Pict/Photo.webp"]
                if change == "malformed": manifest["files"]["Pict/Photo.webp"] = None
                if change == "case":
                    entry["imageFile"] = "Pict/photo.webp"
                    manifest["files"]["Pict/photo.webp"] = manifest["files"].pop("Pict/Photo.webp")
                if change == "escape": entry["imageFile"] = "Pict/../Photo.webp"
                with self.assertRaises(ValueError): it.verify_image_bindings(root, catalog, manifest)

    def test_incomplete_images_cannot_pass_required_complete_check(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            catalog, manifest = self.image_fixture(root)
            entry = catalog["entries"][0]
            entry.update(imageStatus="replacement-needed", imageFile=None)
            manifest["files"] = {}
            proof = it.verify_image_bindings(root, catalog, manifest)
            self.assertFalse(proof["complete"])
            self.assertEqual(proof["pendingUids"], [entry["uid"]])
            with self.assertRaisesRegex(ValueError, "není dokončená"):
                it.verify_image_bindings(root, catalog, manifest, require_complete=True)

    def test_approved_content_preserves_legacy_aliases_and_links_26_new_meanings(self):
        review = json.loads((ROOT / "VocabularyIT/vocabulary_it_content_review.json").read_text())
        self.assertEqual(review["status"], "approved-and-applied")
        self.assertEqual(len(review["items"]), 24)
        by_uid = {entry["uid"]: entry for entry in self.catalog["entries"]}
        for proposal in review["items"]:
            self.assertEqual(proposal["state"], "applied")
            entry = by_uid[proposal["uid"]]
            source = proposal["source"]
            self.assertEqual((entry["it"], entry["cz"]), (proposal["mainProposal"]["it"], proposal["mainProposal"]["cz"]))
            self.assertEqual(it.resolve_catalog_rows([{"IT": source["it"], "CZ": source["cz"]}], self.catalog)[0]["uid"], proposal["uid"])
            self.assertIn("sentenceOverride", entry)
            for uid in proposal["createdUids"]:
                self.assertEqual(by_uid[uid]["origin"], "web")
                self.assertIn(entry["uid"], [link["uid"] for link in by_uid[uid]["related"]])
        self.assertEqual(len(by_uid), 1096)
        self.assertEqual(sum(len(p["createdUids"]) for p in review["items"]), 26)
        cards = it.all_card_texts(self.rows, self.catalog)
        self.assertEqual(len(cards), 1096)
        self.assertEqual(cards[471][0]["uid"], "vit-0472")
        self.assertEqual(cards[471][1]["sentenceCz"], "Tady nemluv nahlas.")
        self.assertEqual(cards[412][1]["genderIt"], "")

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



from PIL import Image
sys.path.insert(0, str(ROOT / "VocabularyIT"))
import vocabulary_it_audio as audio


def leda_canonical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


class VocabularyItalianLedaBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch = json.loads((ROOT / "VocabularyIT/batches/leda_20261116.json").read_text())
        cls.active = it.load_catalog()

    def test_applied_batch_preserves_original_catalog_entries_and_inputs(self):
        b = self.batch
        self.assertEqual(b["state"], "applied")
        self.assertEqual(len(self.active["entries"]), b["totalAfter"])
        self.assertEqual(self.active["entries"][b["baseCount"]:], b["entries"])
        self.assertEqual(leda_canonical(self.active["entries"][:b["baseCount"]]), b["baseEntriesSha256"])
        spelling = json.loads((ROOT / "VocabularyIT/vocabulary_it_spelling.json").read_text())
        original_spelling={uid:value for uid,value in spelling["entries"].items() if int(uid.split("-")[1])<=b["baseCount"]}
        self.assertEqual(leda_canonical(original_spelling), b["baseSpellingEntriesSha256"])
        for relative, sha in b["preservedSources"].items():
            self.assertEqual(it.digest(ROOT / relative), sha, relative)

    def test_all_599_identities_and_relations_validate_together(self):
        b = self.batch
        self.assertEqual((b["newCount"], b["totalAfter"]), (599, 1096))
        self.assertEqual([e["id"] for e in b["entries"]], list(range(498, 1097)))
        candidate = copy.deepcopy(self.active)
        self.assertEqual(candidate["entries"][b["baseCount"]:], b["entries"])
        candidate["nextId"] = b["nextIdAfter"]
        it.validate_catalog(candidate)
        self.assertEqual(len(candidate["groups"]), 18)
        self.assertEqual(len({e["uid"] for e in candidate["entries"]}), 1096)
        by_it = {e["it"]: e for e in b["entries"]}
        self.assertEqual(by_it["uomini"]["formOfUid"], by_it["uomo"]["uid"])
        mano = next(e for e in self.active["entries"] if e["it"] == "mano")
        self.assertEqual(by_it["mani"]["formOfUid"], mano["uid"])

    def test_708_source_rows_have_explicit_coverage_without_invented_lessons(self):
        b = self.batch
        self.assertEqual(b["source"]["lessons"], [3, 4, 5, 6, 7, 8])
        self.assertEqual(b["source"]["notProvided"], [1, 2])
        self.assertEqual(len(b["coverage"]), 708)
        self.assertEqual(len({r["sourceLine"] for r in b["coverage"]}), 708)
        known = {e["uid"] for e in self.active["entries"] + b["entries"]}
        covered_new = set()
        for row in b["coverage"]:
            self.assertIn(row["lesson"], b["source"]["lessons"])
            self.assertTrue(row["existing"] or row["new"])
            self.assertFalse((set(row["existing"]) | set(row["new"])) - known)
            covered_new.update(row["new"])
        self.assertEqual(covered_new, {e["uid"] for e in b["entries"]})

    def test_every_selected_image_is_real_exact_and_decodable(self):
        b = self.batch
        pins = {}
        for record in b["mediaBindings"].values():
            source = ROOT / record["source"]
            self.assertTrue(source.resolve().is_relative_to(ROOT.resolve()))
            self.assertFalse(source.is_symlink())
            self.assertIn(source.name, {p.name for p in source.parent.iterdir()})
            self.assertEqual(it.digest(source), record["sha256"])
            self.assertEqual(source.stat().st_size, record["bytes"])
            with Image.open(source) as im:
                im.load()
                self.assertEqual((im.width, im.height), (record["width"], record["height"]))
            pins[record["target"]] = record["sha256"]
        for entry in b["entries"]:
            self.assertEqual(entry["imageStatus"], "reviewed")
            self.assertEqual(pins[entry["imageFile"]], entry["imageSha256"])
            self.assertNotIn("others", entry["imageFile"].casefold())

    def test_original_1907_mp3_hashes_survive_the_azure_additions(self):
        b=self.batch
        old_assets={}
        for filename in ('vocabulary-it-audio.json','vocabulary-it-sentence-audio.json'):
            manifest=json.loads((ROOT/'docs/data'/filename).read_text())
            for uid,record in manifest['items'].items():
                if int(uid.split('-')[1])<=b['baseCount']:
                    for language in ('it','cz'):
                        relative=record[language];old_assets[relative]=manifest['assetSha256'][relative]
        self.assertEqual(len(old_assets),1907)
        self.assertEqual(leda_canonical(old_assets),b['audio']['originalAssetsSha256'])

    def test_spelling_and_four_audio_references_cover_the_exact_meanings(self):
        b = self.batch
        self.assertEqual(set(b["spelling"]), {e["uid"] for e in b["entries"]})
        old_spelling = json.loads((ROOT / "VocabularyIT/vocabulary_it_spelling.json").read_text())
        decompositions = {e["it"]: e["pieces"] for e in old_spelling["entries"].values()}
        items = json.loads((ROOT / "docs/data/vocabulary-it-v2.json").read_text())["items"]
        for e in b["entries"]:
            s = b["spelling"][e["uid"]]
            self.assertEqual((s["it"], s["cz"]), (e["it"], e["cz"]))
            self.assertEqual("".join(s["pieces"]), e["it"])
            self.assertTrue(s["reviewed"])
            if e["it"] in decompositions:
                self.assertEqual(s["pieces"], decompositions[e["it"]])
            decompositions[e["it"]] = s["pieces"]
            current=next(i for i in items if i["uid"]==e["uid"])
            self.assertEqual((current["it"],current["cz"],current["sentenceIt"],current["sentenceCz"]),(e["it"],e["cz"],e["webText"]["sentenceIt"],e["webText"]["sentenceCz"]))
        planned = audio.plan(items,provider="registered-edge-tts+azure-neural")
        self.assertEqual(planned["stats"], b["audio"]["stats"])
        self.assertEqual(planned["stats"]["references"], 4 * 1096)
        self.assertEqual(b["audio"]["status"], "complete")
        self.assertEqual(b["audio"]["newAssetsReady"], 2315)
        self.assertEqual(b["audio"]["uncertainRequests"], 0)



if __name__ == "__main__":
    unittest.main()
