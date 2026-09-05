from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "VocabularyEN" / "import_mmtx_vocabulary.py"
SYNC_MODULE_PATH = ROOT / "VocabularyEN" / "sync_vocabulary_en_to_docs.py"
PICTURE_PLAN_MODULE_PATH = ROOT / "VocabularyEN" / "prepare_mmtx_picture_plan.py"
PUBLISH_MODULE_PATH = ROOT / "VocabularyEN" / "publish_mmtx_picture_candidates.py"
BENJI_MODULE_PATH = ROOT / "VocabularyEN" / "tag_mmtx_benji_word_set.py"


def load_module():
    spec = importlib.util.spec_from_file_location("import_mmtx_vocabulary", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_sync_module():
    spec = importlib.util.spec_from_file_location("sync_vocabulary_en_to_docs", SYNC_MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_picture_plan_module():
    spec = importlib.util.spec_from_file_location("prepare_mmtx_picture_plan", PICTURE_PLAN_MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_publish_module():
    spec = importlib.util.spec_from_file_location(
        "publish_mmtx_picture_candidates", PUBLISH_MODULE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_benji_module():
    spec = importlib.util.spec_from_file_location(
        "tag_mmtx_benji_word_set", BENJI_MODULE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_current_mmtx_inventory_has_complete_curated_plan():
    module = load_module()
    entries, current_rows, planned = module.build_plan()

    assert len(entries) == 275
    assert len(current_rows) == 425
    assert planned == []
    assert not any(row["EN"] == "me too" for row in current_rows)
    assert sum(row["EN"] == "too" for row in current_rows) == 1
    imported = current_rows[186:]
    assert len(imported) == 239
    assert imported[0]["Order"] == "187"
    assert imported[-1]["Order"] == "425"
    assert {module.normalize_word(str(row["EN"])) for row in imported}.isdisjoint(
        module.EXCLUDED_NORMALIZED
    )
    assert all(str(row["Sentence"]).strip() for row in imported)
    assert all(str(row["SentenceT"]).strip() for row in imported)
    assert all("Benji" in module.merge_word_sets(str(row["WS"])).split("|") for row in imported)


def test_dialogue_audit_covers_all_current_scenes_and_supplement():
    module = load_module()
    rows = module.load_csv_rows()
    coverage = module.dialogue_coverage(rows)
    assert coverage["missing_lemmas"] == []
    assert any("scene05_log_bridge" in source for source in coverage["sources"])
    assert any("scene_jane_birthday" in source for source in coverage["sources"])
    assert any("scene_kate_birthday" in source for source in coverage["sources"])
    assert any("forest_school" in source for source in coverage["sources"])
    assert coverage["aliases"]["logs"] == "log"
    assert coverage["aliases"]["crossed"] == "cross"
    supplement = module.load_dialogue_supplement()
    assert len(supplement) == 120
    by_en = {row["EN"]: row for row in rows}
    for addition in supplement:
        actual = by_en[addition["EN"]]
        assert all(actual[field] == addition[field] for field in addition)
        assert "Benji" in actual["WS"].split("|")


def test_dialogue_audit_distinguishes_inflections_names_and_unreviewed_words():
    module = load_module()
    tokens = {word: ["test.js"] for word in ["logs", "crossed", "am", "kate", "unicorn"]}
    with patch.object(module, "extract_dialogue_tokens", return_value=tokens):
        coverage = module.dialogue_coverage([{"EN": en} for en in ["log", "cross", "I (am)"]])
    assert coverage["missing_lemmas"] == ["unicorn"]
    assert coverage["ignored_tokens"] == ["kate"]
    real_tokens = module.extract_dialogue_tokens()
    with patch.object(module, "extract_dialogue_tokens", return_value={**real_tokens, "unicorn": ["new_scene.js"]}):
        try:
            module.build_plan()
        except SystemExit as error:
            assert "Unreviewed MMTX dialogue words: unicorn" in str(error)
        else:
            raise AssertionError("A new unreviewed dialogue word must block a falsely complete audit")


def test_append_preserves_existing_csv_prefix_and_crlf(tmp_path):
    module = load_module()
    original = module.CSV_PATH.read_bytes()
    lines = original.split(b"\r\n")
    assert len(lines) == 427
    pre_import = b"\r\n".join(lines[:187]) + b"\r\n"
    target = tmp_path / "VocabularyEN.csv"
    target.write_bytes(pre_import)
    module.CSV_PATH = target
    entries, current_rows, planned = module.build_plan()
    assert len(entries) == 275
    assert len(current_rows) == 186
    assert len(planned) == 239
    module.append_rows(planned)

    updated = target.read_bytes()
    assert updated.startswith(pre_import)
    assert updated == original
    assert updated.count(b"\r\n") == 426
    assert b"\n" not in updated.replace(b"\r\n", b"")

    with target.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 425
    assert rows[304]["EN"] == "believe"
    assert rows[304]["SentenceT"] == "Věřím ti, protože říkáš pravdu."
    assert rows[-1]["EN"] == "your"


def test_czech_tokenization_keeps_letters_with_diacritics_together():
    module = load_sync_module()

    assert module.tokenize_words("věřit, důvěřovat") == ["verit", "duverovat"]
    assert module.tokenize_words("oříšky") == ["orisky"]


def test_benji_tag_transform_changes_only_selected_crlf_rows():
    module = load_benji_module()
    import_module = load_module()
    original = (
        "EN,CZ,Order,Sentence,SentenceT,WS,L,HT\r\n"
        "old,starý,1,Old sentence.,Stará věta.,Things,ne,ne\r\n"
        "one,jedna,187,One bird.,Jeden pták.,,ne,ne\r\n"
        "catch,chytit,300,Catch it.,Chyť to.,Actions,ne,ne\r\n"
    ).encode("utf-8")

    updated, changed = module.build_updated_bytes(
        original,
        {"one", "catch"},
        import_module=import_module,
    )

    assert changed == ["one", "catch"]
    assert b"old,star\xc3\xbd,1,Old sentence.,Star\xc3\xa1 v\xc4\x9bta.,Things,ne,ne\r\n" in updated
    assert b"one,jedna,187,One bird.,Jeden pt\xc3\xa1k.,Benji,ne,ne\r\n" in updated
    assert b"catch,chytit,300,Catch it.,Chy\xc5\xa5 to.,Actions|Benji,ne,ne\r\n" in updated
    assert updated.replace(b"\r\n", b"").count(b"\n") == 0


def test_current_mmtx_rows_are_all_in_benji_word_set():
    module = load_benji_module()

    targets, pending = module.audit()

    assert len(targets) == 239
    assert pending == []


def test_web_export_offers_exactly_the_mmtx_rows_in_benji_word_set():
    manifest = json.loads(
        (ROOT / "docs" / "data" / "vocabulary-en.json").read_text(encoding="utf-8")
    )
    benji_items = [item for item in manifest["items"] if "Benji" in item["wordSets"]]

    assert "Benji" in manifest["wordSets"]
    assert len(benji_items) == 239
    assert [item["order"] for item in benji_items] == list(range(187, 426))
    assert all(item["sentenceEn"] and item["sentenceCz"] for item in benji_items)
    assert all(item["image"] for item in benji_items)


def test_exact_mapping_beats_accent_stripped_czech_filename_collision():
    module = load_sync_module()

    stem, source = module.choose_picture_stem(
        {"EN": "too", "CZ": "také"},
        picture_stems={"take", "also"},
        synonym_image_map={"take": "also"},
    )

    assert (stem, source) == ("also", "mapping")


def test_exact_english_filename_stays_authoritative():
    module = load_sync_module()

    stem, source = module.choose_picture_stem(
        {"EN": "take", "CZ": "brát"},
        picture_stems={"take", "other"},
        synonym_image_map={"take": "other"},
    )

    assert (stem, source) == ("take", "direct")


def test_czech_meaning_beats_short_english_function_word():
    module = load_sync_module()

    stem, source = module.choose_picture_stem(
        {"EN": "a glass (of water)", "CZ": "sklenice (vody)"},
        picture_stems={"a", "and", "glass"},
        synonym_image_map={"a": "and", "sklenice": "glass"},
    )

    assert (stem, source) == ("glass", "mapping")


def test_web_asset_sync_can_preserve_unreferenced_files(tmp_path):
    module = load_sync_module()
    extra = tmp_path / "legacy.webp"
    extra.write_bytes(b"legacy")

    module.ensure_clean_assets_dir(
        tmp_path,
        expected_names=set(),
        preserve_extra_assets=True,
    )

    assert extra.read_bytes() == b"legacy"


def test_mapping_byte_append_preserves_existing_values():
    module = load_publish_module()
    original = '{\n  "starý": "old"\n}\n'.encode("utf-8")

    updated = module.append_mapping_bytes(
        original,
        {"nový": "new", "běhat": "race"},
    )

    assert updated.startswith('{\n  "starý": "old",\n'.encode("utf-8"))
    assert json.loads(updated.decode("utf-8")) == {
        "starý": "old",
        "nový": "new",
        "běhat": "race",
    }


def test_applied_mapping_matches_approved_preview_and_backup():
    preview = json.loads(
        (ROOT / "PictNew" / "VocabularyEN_MMTX_mapping_preview_20260824.json").read_text(
            encoding="utf-8"
        )
    )
    receipt = json.loads(
        (ROOT / "PictNew" / "VocabularyEN_MMTX_mapping_apply_receipt_20260824.json").read_text(
            encoding="utf-8"
        )
    )
    web_receipt = json.loads(
        (ROOT / "PictNew" / "VocabularyEN_MMTX_web_sync_receipt_20260824.json").read_text(
            encoding="utf-8"
        )
    )
    current = json.loads((ROOT / "Pict" / "mapping.json").read_text(encoding="utf-8"))
    backup = json.loads((ROOT / receipt["backup_path"]).read_text(encoding="utf-8"))

    assert receipt["entry_count_before"] == len(backup) == 969
    assert receipt["addition_count"] == len(preview["additions"]) == 86
    assert receipt["entry_count_after"] == len(current) == 1055
    assert all(current[key] == value for key, value in backup.items())
    assert all(current[key] == value for key, value in preview["additions"].items())
    assert web_receipt["status"] == "mapping_and_web_sync_completed"
    assert web_receipt["mapping_entry_count"] == 1055
    assert web_receipt["web_row_count"] == 306
    assert web_receipt["web_missing_image_count"] == 0
    assert web_receipt["asset_deletions"] == 0


def test_picture_plan_covers_every_imported_row_without_overwrite():
    plan = json.loads(
        (ROOT / "PictNew" / "VocabularyEN_MMTX_picture_plan_20260824.json").read_text(
            encoding="utf-8"
        )
    )

    assert plan["imported_row_count"] == 120
    assert sum(plan["assignment_counts"].values()) == 120
    assert plan["assignment_counts"] == {
        "reuse_pict_exact": 27,
        "reuse_mmtx_forest_asset": 33,
        "reuse_pict_mapped": 21,
        "generate": 39,
    }
    assert plan["total_unique_target_images"] == 35
    assert len({request["image_name"] for request in plan["requests"]}) == 35
    assert all(conflict["decision"] == "preserve_current" for conflict in plan["preserved_mapping_conflicts"])
