from __future__ import annotations

import csv
import tempfile
import unittest
import zipfile
from pathlib import Path

from app.lekarna.service import (
    RETIRE_CONFIRMATION_PHRASE,
    audit_domaci_lekarna_records,
    format_domaci_lekarna_audit,
    format_domaci_lek_retire_preview,
    format_domaci_leky_search,
    format_retire_domaci_lek,
    load_domaci_leky,
    search_domaci_leky_records,
)
from app.lekarna.photo_import import (
    APPLY_CONFIRMATION_PHRASE,
    apply_lekarna_photo_import_manifest,
    prepare_lekarna_photo_import_manifest,
    stage_lekarna_photo_import_sources,
    validate_lekarna_photo_sources,
)
from app.lekarna.download_intake import (
    build_download_photo_intake,
    build_download_photo_intake_markdown,
    find_download_photos_by_names,
    find_recent_download_photos,
)
from app.lekarna.auto_import import (
    ImageOcrResult,
    apply_auto_import_manifest_from_downloads,
    build_auto_import_draft,
    suggest_metadata_from_ocr,
)
import app.lekarna.auto_import as auto_import
from app.lekarna.openai_vision import (
    openai_vision_label,
    openai_vision_to_inventory_suggestion,
)
from app.lekarna.search_tags import build_search_tags
from app.lekarna.sukl_dlp import match_sukl_dlp
from app.lekarna.sukl_pil_archive import build_pil_short_from_text, resolve_sukl_pil_document


FIELD_NAMES = [
    "nazev",
    "ucinna_latka",
    "forma",
    "sila",
    "kategorie",
    "pouziti",
    "pro_koho",
    "nevhodne_pro_koho",
    "expirace",
    "mnozstvi",
    "umisteni",
    "overeno_z_letaku",
    "stav_obalu",
    "jistota_cteni",
    "nutno_overit",
    "zdroj",
    "poznamky",
    "PIL_Short",
    "PIL_Source",
    "PIL_Checked_Date",
    "PIL_Match_Status",
    "Search_Tags",
]


class LekarnaServiceTests(unittest.TestCase):
    def test_load_domaci_leky_from_csv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = _fake_csv(Path(temp_dir))

            records = load_domaci_leky(csv_path)

            self.assertEqual(len(records), 6)
            self.assertEqual(records[0].nazev, "ACYLPYRIN")
            self.assertEqual(records[0].kategorie, "bolest_horecka")

    def test_search_by_symptom_finds_related_category(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = _fake_csv(Path(temp_dir))

            matches = search_domaci_leky_records("horecka", csv_path=csv_path)

            names = [match.lek.nazev for match in matches]
            self.assertIn("ACYLPYRIN", names)
            self.assertIn("PARALEN GRIP", names)

    def test_search_uses_explicit_search_tags(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = _fake_csv(Path(temp_dir))

            matches = search_domaci_leky_records("ucpany nos", csv_path=csv_path)

            names = [match.lek.nazev for match in matches]
            self.assertIn("CLARINESE", names)
            self.assertIn("vyhledavaci tagy", matches[0].reasons[0])

    def test_build_search_tags_adds_common_home_terms(self) -> None:
        tags = build_search_tags(
            {
                "nazev": "Tussical 1,5 mg/ml sirup",
                "ucinna_latka": "butamirát-citrát",
                "forma": "sirup",
                "kategorie": "kašel / nachlazení / chřipka",
                "pouziti": "suchý dráždivý kašel",
                "PIL_Short": "Tlumí suchý dráždivý kašel při nachlazení.",
            }
        )

        self.assertIn("suchý kašel", tags)
        self.assertIn("dráždivý kašel", tags)
        self.assertIn("nachlazení", tags)

    def test_search_by_common_query_finds_modriny(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = _fake_csv(Path(temp_dir))

            output = format_domaci_leky_search("modriny", csv_path=csv_path)

            self.assertIn("HEPARIN AL", output)
            self.assertIn("modriny_otoky", output)

    def test_output_highlights_uncertainties(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = _fake_csv(Path(temp_dir))

            output = format_domaci_leky_search("nachlazeni", csv_path=csv_path)

            self.assertIn("ZBYTKY_BEZ_KRABICKY", output)
            self.assertIn("chybi nebo je nezjistena expirace", output)
            self.assertIn("neovereno z pribaloveho letaku", output)

    def test_output_highlights_unverified_name_and_low_confidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = _fake_csv(Path(temp_dir))

            output = format_domaci_leky_search("neovereno", csv_path=csv_path)

            self.assertIn("NONGRIP / NON GRIP", output)
            self.assertIn("neovereny nebo nejisty nazev", output)
            self.assertIn("jistota cteni: nizka", output)
            self.assertIn("nutno_overit=ano", output)

    def test_output_does_not_recommend_dosage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = _fake_csv(Path(temp_dir))

            output = format_domaci_leky_search("bolest", csv_path=csv_path)

            self.assertIn("Neuvadim davkovani", output)
            forbidden_phrases = ("vezmi ", "uzij ", "ber ", "1 tabletu", "2 tablety")
            self.assertFalse(any(phrase in output.casefold() for phrase in forbidden_phrases))

    def test_search_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            csv_path = _fake_csv(directory)
            before = sorted(path.relative_to(directory) for path in directory.rglob("*"))

            format_domaci_leky_search("alergie", csv_path=csv_path)

            after = sorted(path.relative_to(directory) for path in directory.rglob("*"))
            self.assertEqual(before, after)

    def test_audit_records_group_key_safety_categories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = _fake_csv(Path(temp_dir))

            audit = audit_domaci_lekarna_records(csv_path)

            self.assertIn("ACYLPYRIN", _names(audit["missing_expiration"]))
            self.assertIn("PARALEN GRIP", _names(audit["unknown_location"]))
            self.assertIn("HEPARIN AL", _names(audit["needs_verification"]))
            self.assertIn("CLARINESE", _names(audit["loose_without_box"]))
            self.assertIn("NONGRIP / NON GRIP", _names(audit["low_confidence"]))
            self.assertIn("AMOXIKLAV", _names(audit["antibiotics"]))
            self.assertIn("ACYLPYRIN", _names(audit["blood_thinners"]))

    def test_audit_output_is_practical_checklist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = _fake_csv(Path(temp_dir))

            output = format_domaci_lekarna_audit(csv_path)

            self.assertIn("Audit domaci lekarny - read-only kontrolni checklist", output)
            self.assertIn("[ ] Polozky s chybejici nebo nezjistenou expiraci", output)
            self.assertIn("[ ] Polozky s neurcenym umistenim", output)
            self.assertIn("[ ] Polozky `nutno_overit=ano`", output)
            self.assertIn("[ ] Polozky `ZBYTKY_BEZ_KRABICKY`", output)
            self.assertIn("[ ] Antibiotika", output)
            self.assertIn("[ ] Leciva souvisejici s redenim krve", output)
            self.assertIn("Vzit krabicky/blistry do ruky", output)
            self.assertIn("AMOXIKLAV", output)
            self.assertIn("ACYLPYRIN", output)

    def test_audit_output_does_not_recommend_dosage_or_specific_suitability(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = _fake_csv(Path(temp_dir))

            output = format_domaci_lekarna_audit(csv_path)

            self.assertIn("ne doporuceni lecby, vhodnosti ani davkovani", output)
            forbidden_phrases = ("vezmi ", "uzij ", "ber ", "1 tabletu", "vhodne pro milu")
            self.assertFalse(any(phrase in output.casefold() for phrase in forbidden_phrases))

    def test_audit_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            csv_path = _fake_csv(directory)
            before = sorted(path.relative_to(directory) for path in directory.rglob("*"))

            format_domaci_lekarna_audit(csv_path)

            after = sorted(path.relative_to(directory) for path in directory.rglob("*"))
            self.assertEqual(before, after)

    def test_retire_preview_is_read_only_and_shows_planned_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            csv_path = _fake_csv(directory)
            before = sorted(path.relative_to(directory) for path in directory.rglob("*"))

            output = format_domaci_lek_retire_preview(
                "HEPARIN AL",
                reason="spotrebovano",
                csv_path=csv_path,
            )

            after = sorted(path.relative_to(directory) for path in directory.rglob("*"))
            self.assertEqual(before, after)
            self.assertIn("Vyrazeni leku - navrh zmeny", output)
            self.assertIn("HEPARIN AL", output)
            self.assertIn("mnozstvi: `1 tuba` -> `vyradeno`", output)
            self.assertIn("umisteni: `horni police` -> `vyradeno`", output)
            self.assertIn(RETIRE_CONFIRMATION_PHRASE, output)

    def test_retire_apply_requires_explicit_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            csv_path = _fake_csv(directory)

            with self.assertRaises(ValueError):
                format_retire_domaci_lek(
                    "HEPARIN AL",
                    reason="spotrebovano",
                    csv_path=csv_path,
                    user_confirmed=False,
                    confirmation_text="",
                )

            records = load_domaci_leky(csv_path)
            heparin = next(record for record in records if record.nazev == "HEPARIN AL")
            self.assertEqual(heparin.mnozstvi, "1 tuba")
            self.assertEqual(heparin.umisteni, "horni police")
            self.assertEqual(list(directory.glob("domaci_leky.backup_before_retire_*.csv")), [])

    def test_retire_apply_soft_retires_one_record_and_backs_up_csv(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            csv_path = _fake_csv(directory)

            output = format_retire_domaci_lek(
                "HEPARIN AL",
                reason="spotrebovano",
                csv_path=csv_path,
                user_confirmed=True,
                confirmation_text=RETIRE_CONFIRMATION_PHRASE,
            )

            self.assertIn("Vyrazeni leku - hotovo", output)
            self.assertIn("HEPARIN AL", output)
            backups = list(directory.glob("domaci_leky.backup_before_retire_*.csv"))
            self.assertEqual(len(backups), 1)
            records = load_domaci_leky(csv_path)
            self.assertEqual(len(records), 6)
            heparin = next(record for record in records if record.nazev == "HEPARIN AL")
            self.assertEqual(heparin.mnozstvi, "vyradeno")
            self.assertEqual(heparin.umisteni, "vyradeno")
            self.assertEqual(heparin.nutno_overit, "ano")
            self.assertIn("Vyradeno", heparin.poznamky)
            self.assertIn("spotrebovano", heparin.poznamky)

    def test_retire_apply_preserves_pil_fields(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            csv_path = _fake_csv(directory)

            format_retire_domaci_lek(
                "HEPARIN AL",
                reason="spotrebovano",
                csv_path=csv_path,
                user_confirmed=True,
                confirmation_text=RETIRE_CONFIRMATION_PHRASE,
            )

            records = load_domaci_leky(csv_path)
            heparin = next(record for record in records if record.nazev == "HEPARIN AL")
            self.assertEqual(heparin.PIL_Short, "Pilotni text PIL")
            self.assertEqual(heparin.PIL_Source, "https://example.test/pil")
            self.assertEqual(heparin.PIL_Checked_Date, "2026-05-20")
            self.assertEqual(heparin.PIL_Match_Status, "pilot")

    def test_search_excludes_retired_records(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            csv_path = _fake_csv(Path(temp_dir))

            format_retire_domaci_lek(
                "HEPARIN AL",
                reason="spotrebovano",
                csv_path=csv_path,
                user_confirmed=True,
                confirmation_text=RETIRE_CONFIRMATION_PHRASE,
            )

            output = format_domaci_leky_search("modriny", csv_path=csv_path)
            self.assertNotIn("HEPARIN AL", output)

    def test_photo_import_prepare_manifest_for_new_photos(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            photo_dir = directory / "Leky_v_Krabickach"
            photo_dir.mkdir()
            (photo_dir / "IMG_1001.HEIC").write_text("fake", encoding="utf-8")
            (photo_dir / "WhatsApp Image.jpeg").write_text("fake", encoding="utf-8")
            csv_path = _fake_csv(directory)
            manifest_path = directory / "manifest.csv"

            result = prepare_lekarna_photo_import_manifest(
                photo_dir=photo_dir,
                csv_path=csv_path,
                manifest_path=manifest_path,
            )

            self.assertEqual(result.rows, 2)
            with manifest_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([row["source_file"] for row in rows], ["IMG_1001.HEIC", "WhatsApp Image.jpeg"])
            self.assertEqual(rows[0]["include"], "ano")
            self.assertEqual(rows[0]["nutno_overit"], "ano")
            self.assertEqual(rows[0]["expirace"], "nezjisteno")

    def test_photo_import_stage_sources_copies_photos_and_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            downloads = directory / "Downloads"
            downloads.mkdir()
            photo_dir = directory / "Leky_v_Krabickach"
            photo_dir.mkdir()
            first = downloads / "IMG_2001.JPG"
            second = downloads / "IMG_2002.png"
            first.write_text("fake first", encoding="utf-8")
            second.write_text("fake second", encoding="utf-8")
            csv_path = _fake_csv(directory)
            manifest_path = directory / "photo_imports" / "manifest.csv"

            result = stage_lekarna_photo_import_sources(
                source_paths=[first, second],
                photo_dir=photo_dir,
                csv_path=csv_path,
                manifest_path=manifest_path,
            )

            self.assertEqual(result.rows, 2)
            self.assertEqual(result.copied_count, 2)
            self.assertTrue((photo_dir / "IMG_2001.JPG").exists())
            self.assertTrue((photo_dir / "IMG_2002.png").exists())
            with manifest_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([row["source_file"] for row in rows], ["IMG_2001.JPG", "IMG_2002.png"])
            self.assertEqual(rows[0]["include"], "ano")
            self.assertEqual(rows[0]["zdroj"], "Leky_v_Krabickach/")

    def test_photo_import_apply_manifest_backs_up_renames_and_appends(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            photo_dir = directory / "Leky_v_Krabickach"
            photo_dir.mkdir()
            (photo_dir / "IMG_1002.HEIC").write_text("fake", encoding="utf-8")
            csv_path = _fake_csv(directory)
            manifest_path = directory / "manifest.csv"
            _write_manifest(
                manifest_path,
                [
                    {
                        "include": "ano",
                        "source_file": "IMG_1002.HEIC",
                        "new_file": "test_lek_100mg_tablety.heic",
                        "nazev": "Test Lek",
                        "ucinna_latka": "test latka",
                        "forma": "tablety",
                        "sila": "100 mg",
                        "kategorie": "test",
                        "pouziti": "test - overit",
                        "mnozstvi": "10 tablet",
                        "poznamky": "Test importu; overit.",
                    }
                ],
            )

            result = apply_lekarna_photo_import_manifest(
                manifest_path=manifest_path,
                photo_dir=photo_dir,
                csv_path=csv_path,
                report_dir=directory,
                user_confirmed=True,
                confirmation_text=APPLY_CONFIRMATION_PHRASE,
            )

            self.assertEqual(result.renamed_count, 1)
            self.assertEqual(result.appended_count, 1)
            self.assertTrue(result.backup_path.exists())
            self.assertTrue(result.report_path.exists())
            self.assertFalse((photo_dir / "IMG_1002.HEIC").exists())
            self.assertTrue((photo_dir / "test_lek_100mg_tablety.heic").exists())
            records = load_domaci_leky(csv_path)
            imported = next(record for record in records if record.nazev == "Test Lek")
            self.assertEqual(imported.zdroj, "Leky_v_Krabickach/test_lek_100mg_tablety.heic")
            self.assertEqual(imported.nutno_overit, "ano")
            self.assertEqual(imported.overeno_z_letaku, "ne")
            self.assertEqual(imported.expirace, "nezjisteno")
            self.assertEqual(validate_lekarna_photo_sources(csv_path=csv_path, photo_dir=photo_dir), [])

    def test_photo_import_apply_requires_explicit_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            manifest_path = directory / "manifest.csv"
            _write_manifest(
                manifest_path,
                [
                    {
                        "include": "ano",
                        "source_file": "IMG_1003.HEIC",
                        "new_file": "test.heic",
                        "nazev": "Test",
                    }
                ],
            )

            with self.assertRaises(ValueError):
                apply_lekarna_photo_import_manifest(
                    manifest_path=manifest_path,
                    photo_dir=directory,
                    csv_path=_fake_csv(directory),
                    report_dir=directory,
                    user_confirmed=False,
                    confirmation_text="",
                )

    def test_photo_import_apply_preflights_before_renaming(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            photo_dir = directory / "Leky_v_Krabickach"
            photo_dir.mkdir()
            (photo_dir / "IMG_1004.HEIC").write_text("fake", encoding="utf-8")
            csv_path = _fake_csv(directory)
            manifest_path = directory / "manifest.csv"
            _write_manifest(
                manifest_path,
                [
                    {
                        "include": "ano",
                        "source_file": "IMG_1004.HEIC",
                        "new_file": "first_valid.heic",
                        "nazev": "First Valid",
                    },
                    {
                        "include": "ano",
                        "source_file": "IMG_MISSING.HEIC",
                        "new_file": "missing_source.heic",
                        "nazev": "Missing Source",
                    },
                ],
            )

            with self.assertRaises(ValueError):
                apply_lekarna_photo_import_manifest(
                    manifest_path=manifest_path,
                    photo_dir=photo_dir,
                    csv_path=csv_path,
                    report_dir=directory,
                    user_confirmed=True,
                    confirmation_text=APPLY_CONFIRMATION_PHRASE,
                )

            self.assertTrue((photo_dir / "IMG_1004.HEIC").exists())
            self.assertFalse((photo_dir / "first_valid.heic").exists())
            self.assertEqual(list(directory.glob("domaci_leky.backup_before_photo_import_*.csv")), [])

    def test_download_intake_finds_recent_photos_and_detects_duplicates(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            downloads = directory / "Downloads"
            downloads.mkdir()
            older = downloads / "IMG_0001.JPG"
            newer = downloads / "IMG_0002.JPG"
            older.write_text("older", encoding="utf-8")
            newer.write_text("newer", encoding="utf-8")
            csv_path = _fake_csv(directory)

            photos = find_recent_download_photos(downloads_dir=downloads, limit=1)
            intake = build_download_photo_intake(
                photos=photos,
                observed_labels={"IMG_0002.JPG": "Heparin AL mast"},
                csv_path=csv_path,
            )

        self.assertEqual(len(photos), 1)
        self.assertEqual(photos[0].path.name, "IMG_0002.JPG")
        self.assertEqual(intake["summary"]["action_counts"], {"duplicate_existing": 1})
        self.assertEqual(intake["items"][0]["matches"][0]["nazev"], "HEPARIN AL")

    def test_download_intake_markdown_is_readable(self) -> None:
        intake = {
            "generated_at": "2026-06-23T00:00:00+00:00",
            "summary": {"photos": 1, "action_counts": {"needs_label": 1}},
            "items": [
                {
                    "photo": {"name": "IMG_0001.JPG", "path": "/tmp/IMG_0001.JPG", "bytes": 123},
                    "observed_label": "",
                    "suggested_slug": "img_0001",
                    "action": "needs_label",
                    "matches": [],
                }
            ],
        }

        markdown = build_download_photo_intake_markdown(intake)

        self.assertIn("# Lékárna - Downloads photo intake", markdown)
        self.assertIn("IMG_0001.JPG", markdown)
        self.assertIn("needs_label", markdown)

    def test_download_intake_selects_photos_by_safe_names(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            downloads = directory / "Downloads"
            downloads.mkdir()
            selected = downloads / "IMG_0002.JPG"
            other = downloads / "IMG_0003.JPG"
            selected.write_text("selected", encoding="utf-8")
            other.write_text("other", encoding="utf-8")
            outside = directory / "outside.JPG"
            outside.write_text("outside", encoding="utf-8")

            photos = find_download_photos_by_names(
                downloads_dir=downloads,
                names=["../outside.JPG", "IMG_0002.JPG", "missing.JPG", "IMG_0002.JPG"],
            )

        self.assertEqual([photo.path.name for photo in photos], ["IMG_0002.JPG"])

    def test_auto_import_draft_can_use_selected_photo_names(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            downloads = directory / "Downloads"
            downloads.mkdir()
            skipped_photo = downloads / "IMG_0001.JPG"
            selected_photo = downloads / "IMG_0002.JPG"
            skipped_photo.write_text("skip", encoding="utf-8")
            selected_photo.write_text("new", encoding="utf-8")
            csv_path = _fake_csv(directory)
            manifest_path = directory / "manifest.csv"
            report_path = directory / "report.md"

            def fake_ocr(path: Path) -> ImageOcrResult:
                self.assertEqual(path.name, "IMG_0002.JPG")
                return ImageOcrResult(
                    text="Dr.Max Vitamin C 500 mg 100 tablet",
                    lines=("Dr.Max Vitamin C", "500 mg", "100 tablet"),
                    method="fake",
                )

            result = build_auto_import_draft(
                downloads_dir=downloads,
                limit=3,
                photo_names=["IMG_0002.JPG"],
                manifest_path=manifest_path,
                report_path=report_path,
                csv_path=csv_path,
                ocr_runner=fake_ocr,
            )

            with manifest_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(result.photos, 1)
        self.assertEqual(result.new_candidates, 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_file"], "IMG_0002.JPG")

    def test_auto_import_apply_copies_download_photo_then_imports(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            downloads = directory / "Downloads"
            downloads.mkdir()
            photo_dir = directory / "Leky_v_Krabickach"
            photo_dir.mkdir()
            source_photo = downloads / "IMG_0004.JPG"
            source_photo.write_text("photo", encoding="utf-8")
            csv_path = _fake_csv(directory)
            manifest_dir = Path("data/lekarna/photo_imports")
            manifest_dir.mkdir(parents=True, exist_ok=True)
            manifest_path = manifest_dir / "lekarna_auto_import_manifest_test.csv"
            _write_manifest(
                manifest_path,
                [
                    {
                        "include": "ano",
                        "source_file": "IMG_0004.JPG",
                        "new_file": "novy_lek_sirup.jpg",
                        "nazev": "Novy Lek",
                        "forma": "sirup",
                        "mnozstvi": "100 ml",
                    }
                ],
            )
            try:
                result = apply_auto_import_manifest_from_downloads(
                    manifest_path=manifest_path,
                    downloads_dir=downloads,
                    photo_dir=photo_dir,
                    csv_path=csv_path,
                    report_dir=directory,
                    location="Pils Jana",
                    user_confirmed=True,
                    confirmation_text=APPLY_CONFIRMATION_PHRASE,
                    refresh_web=False,
                )
            finally:
                manifest_path.unlink(missing_ok=True)

            records = load_domaci_leky(csv_path)
            target_exists = (photo_dir / "novy_lek_sirup.jpg").exists()

        self.assertEqual(result.copied_count, 1)
        self.assertEqual(result.renamed_count, 1)
        self.assertEqual(result.appended_count, 1)
        self.assertTrue(target_exists)
        imported = next(record for record in records if record.zdroj == "Leky_v_Krabickach/novy_lek_sirup.jpg")
        self.assertEqual(imported.zdroj, "Leky_v_Krabickach/novy_lek_sirup.jpg")
        self.assertEqual(imported.umisteni, "Pils Jana")

    def test_sukl_dlp_matches_sinupret_akut_package_and_pil(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            dlp_zip = _fake_sukl_dlp_zip(Path(temp_dir))

            match = match_sukl_dlp(
                {
                    "nazev": "Bionorica Sinupret",
                    "forma": "obalene tablety",
                    "mnozstvi": "20 tablet",
                },
                ocr_text="Sinupret akut obalene tablety 20 obalenych tablet",
                dlp_zip_path=dlp_zip,
            )

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.kod_sukl, "0197843")
        self.assertEqual(match.pil, "PI223751.pdf")
        self.assertEqual(match.match_status, "overeno_z_dlp")

    def test_auto_import_draft_prefills_safe_pil_short(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            downloads = directory / "Downloads"
            downloads.mkdir()
            photo = downloads / "IMG_0100.JPG"
            photo.write_text("new", encoding="utf-8")
            csv_path = _fake_csv(directory)
            dlp_zip = _fake_sukl_dlp_zip(directory)
            manifest_path = directory / "manifest.csv"
            report_path = directory / "report.md"

            def fake_ocr(path: Path) -> ImageOcrResult:
                return ImageOcrResult(
                    text="Sinupret akut obalené tablety 20 tablet",
                    lines=("Sinupret", "akut obalené tablety", "20 tablet"),
                    method="fake",
                )

            build_auto_import_draft(
                downloads_dir=downloads,
                limit=1,
                manifest_path=manifest_path,
                report_path=report_path,
                csv_path=csv_path,
                ocr_runner=fake_ocr,
                dlp_zip_path=dlp_zip,
            )

            with manifest_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 1)
        self.assertIn("Rostlinny lecivy pripravek", rows[0]["PIL_Short"])
        self.assertEqual(rows[0]["PIL_Match_Status"], "overeno_z_dlp")
        self.assertIn("kod 0197843", rows[0]["PIL_Source"])
        self.assertIn("PIL PI223751.pdf", rows[0]["PIL_Source"])

    def test_auto_import_draft_prefills_dlp_summary_for_regular_match(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            downloads = directory / "Downloads"
            downloads.mkdir()
            photo = downloads / "IMG_0200.JPG"
            photo.write_text("new", encoding="utf-8")
            csv_path = _fake_csv(directory)
            dlp_zip = _fake_sukl_dlp_zip(directory)
            manifest_path = directory / "manifest.csv"
            report_path = directory / "report.md"

            def fake_ocr(path: Path) -> ImageOcrResult:
                return ImageOcrResult(
                    text="Sertivan 50 mg potahovane tablety 30",
                    lines=("Sertivan", "50 mg", "30 tablet"),
                    method="fake",
                )

            build_auto_import_draft(
                downloads_dir=downloads,
                limit=1,
                manifest_path=manifest_path,
                report_path=report_path,
                csv_path=csv_path,
                ocr_runner=fake_ocr,
                dlp_zip_path=dlp_zip,
            )

            with manifest_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["nazev"], "SERTIVAN")
        self.assertEqual(rows[0]["ucinna_latka"], "SERTRALIN")
        self.assertIn("SEROTONINU", rows[0]["kategorie"])
        self.assertIn("SUKL DLP/ATC", rows[0]["pouziti"])
        self.assertIn("Registrovany lecivy pripravek SERTIVAN", rows[0]["PIL_Short"])
        self.assertIn("SERTRALIN", rows[0]["PIL_Short"])
        self.assertEqual(rows[0]["PIL_Match_Status"], "overeno_z_dlp")
        self.assertIn("SERTIVAN", rows[0]["Search_Tags"])
        self.assertIn("SERTRALIN", rows[0]["Search_Tags"])

    def test_sukl_pil_archive_resolves_text_member_and_builds_short(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            archive_path = _fake_sukl_pil_archive(Path(temp_dir))

            document = resolve_sukl_pil_document("PI229834.pdf", pil_archive_path=archive_path)

        self.assertIsNotNone(document)
        assert document is not None
        self.assertEqual(document.member_name, "PIL/PI229834.txt")
        self.assertIn("k čemu se používá", document.text)
        short = build_pil_short_from_text("SERTIVAN", document.text)
        self.assertIn("SERTIVAN", short)
        self.assertIn("deprese", short)
        self.assertIn("Neužívejte", short)

    def test_auto_import_draft_uses_cached_pil_archive_when_available(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            downloads = directory / "Downloads"
            downloads.mkdir()
            photo = downloads / "IMG_0201.JPG"
            photo.write_text("new", encoding="utf-8")
            csv_path = _fake_csv(directory)
            dlp_zip = _fake_sukl_dlp_zip(directory)
            pil_archive = _fake_sukl_pil_archive(directory)
            manifest_path = directory / "manifest.csv"
            report_path = directory / "report.md"

            def fake_ocr(path: Path) -> ImageOcrResult:
                return ImageOcrResult(
                    text="Sertivan 50 mg potahovane tablety 30",
                    lines=("Sertivan", "50 mg", "30 tablet"),
                    method="fake",
                )

            build_auto_import_draft(
                downloads_dir=downloads,
                limit=1,
                manifest_path=manifest_path,
                report_path=report_path,
                csv_path=csv_path,
                ocr_runner=fake_ocr,
                dlp_zip_path=dlp_zip,
                pil_archive_path=pil_archive,
            )

            with manifest_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["PIL_Match_Status"], "overeno")
        self.assertEqual(rows[0]["overeno_z_letaku"], "ano")
        self.assertIn("deprese", rows[0]["PIL_Short"])
        self.assertIn("PIL archiv", rows[0]["PIL_Source"])
        self.assertIn("PI229834.pdf", rows[0]["PIL_Source"])

    def test_auto_import_suggests_metadata_from_ocr(self) -> None:
        suggestion = suggest_metadata_from_ocr(
            (
                "Dr.Max Vitamin C",
                "500 mg",
                "100 tablet",
                "doplněk stravy",
            )
        )

        self.assertEqual(suggestion["nazev"], "Dr.Max Vitamin C")
        self.assertEqual(suggestion["sila"], "500 mg")
        self.assertEqual(suggestion["mnozstvi"], "100 tablet")
        self.assertEqual(suggestion["forma"], "tablety")
        self.assertEqual(suggestion["kategorie"], "vitaminy_mineraly_doplnky")
        self.assertTrue(suggestion["new_file"].endswith(".jpg"))

    def test_openai_vision_suggestion_keeps_name_and_match_label_separate(self) -> None:
        result = {
            "product_name": "Vitamin B12",
            "manufacturer_or_brand": "DrMax",
            "product_type": "doplněk_stravy",
            "active_ingredients_or_composition": ["Vitamin B12"],
            "strength": "500 μg",
            "form": "tablety",
            "quantity": "100 tablet",
            "visible_expiration": "",
            "suggested_category": "vitamíny",
            "suggested_use_inventory_only": "",
            "suggested_filename_slug": "",
            "confidence": 0.8,
            "uncertainties": [],
            "visible_text": [],
            "safety_note": "",
        }

        suggestion = openai_vision_to_inventory_suggestion(result)

        self.assertEqual(suggestion["nazev"], "Dr.Max Vitamin B12")
        self.assertEqual(openai_vision_label(result), "Dr.Max Vitamin B12 500 μg 100 tablet")
        self.assertIn("500_ug", suggestion["new_file"])
        self.assertNotIn("500_g", suggestion["new_file"])
        self.assertNotIn("100_tablet_500", suggestion["new_file"])

    def test_auto_import_draft_writes_review_rows_for_new_and_duplicate_candidates(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            downloads = directory / "Downloads"
            downloads.mkdir()
            duplicate_photo = downloads / "IMG_0001.JPG"
            new_photo = downloads / "IMG_0002.JPG"
            duplicate_photo.write_text("duplicate", encoding="utf-8")
            new_photo.write_text("new", encoding="utf-8")
            csv_path = _fake_csv(directory)
            manifest_path = directory / "manifest.csv"
            report_path = directory / "report.md"

            def fake_ocr(path: Path) -> ImageOcrResult:
                if path.name == "IMG_0001.JPG":
                    return ImageOcrResult(
                        text="HEPARIN AL mast",
                        lines=("HEPARIN AL", "mast"),
                        method="fake",
                    )
                return ImageOcrResult(
                    text="Dr.Max Vitamin C 500 mg 100 tablet",
                    lines=("Dr.Max Vitamin C", "500 mg", "100 tablet"),
                    method="fake",
                )

            result = build_auto_import_draft(
                downloads_dir=downloads,
                limit=2,
                manifest_path=manifest_path,
                report_path=report_path,
                csv_path=csv_path,
                ocr_runner=fake_ocr,
            )

            with manifest_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            report_text = report_path.read_text(encoding="utf-8")

        self.assertEqual(result.photos, 2)
        self.assertEqual(result.duplicate_existing, 1)
        self.assertEqual(result.new_candidates, 1)
        self.assertEqual(len(rows), 2)
        by_source = {row["source_file"]: row for row in rows}
        self.assertEqual(by_source["IMG_0002.JPG"]["nazev"], "Dr.Max Vitamin C")
        self.assertEqual(by_source["IMG_0001.JPG"]["include"], "ano")
        self.assertIn("mozne shody", by_source["IMG_0001.JPG"]["poznamky"])
        self.assertIn("new_candidate: 1", report_text)
        self.assertIn("duplicate_existing: 1", report_text)

    def test_auto_import_draft_writes_review_row_when_ocr_has_no_label(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            downloads = directory / "Downloads"
            downloads.mkdir()
            photo = downloads / "IMG_0003.JPG"
            photo.write_text("needs label", encoding="utf-8")
            csv_path = _fake_csv(directory)
            manifest_path = directory / "manifest.csv"
            report_path = directory / "report.md"

            def fake_ocr(path: Path) -> ImageOcrResult:
                return ImageOcrResult("", (), "openai-vision-failed", "[Errno 11] Resource deadlock avoided")

            result = build_auto_import_draft(
                downloads_dir=downloads,
                limit=1,
                manifest_path=manifest_path,
                report_path=report_path,
                csv_path=csv_path,
                ocr_runner=fake_ocr,
            )

            with manifest_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            report_text = report_path.read_text(encoding="utf-8")

        self.assertEqual(result.photos, 1)
        self.assertEqual(result.new_candidates, 0)
        self.assertEqual(result.needs_review, 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["include"], "ano")
        self.assertEqual(rows[0]["source_file"], "IMG_0003.JPG")
        self.assertEqual(rows[0]["new_file"], "img_0003.jpg")
        self.assertEqual(rows[0]["jistota_cteni"], "nizka")
        self.assertEqual(rows[0]["nutno_overit"], "ano")
        self.assertIn("needs_label: 1", report_text)

    def test_auto_import_draft_falls_back_to_macos_ocr_when_openai_fails(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            downloads = directory / "Downloads"
            downloads.mkdir()
            photo = downloads / "IMG_9553.JPG"
            photo.write_text("fake image", encoding="utf-8")
            csv_path = _fake_csv(directory)
            manifest_path = directory / "manifest.csv"
            report_path = directory / "report.md"

            original_openai = auto_import.analyze_image_with_openai_vision
            original_macos = auto_import.ocr_image_with_macos_vision

            def fake_openai(path: Path, *, model: str) -> ImageOcrResult:
                return ImageOcrResult("", (), "openai-vision-failed", "[Errno 11] Resource deadlock avoided")

            def fake_macos(path: Path) -> ImageOcrResult:
                return ImageOcrResult(
                    text="Bionorica\nSinupret\nakut obalené tablety\n20 obalenych tablet",
                    lines=("Bionorica", "Sinupret", "akut obalené tablety", "20 obalenych tablet"),
                    method="macos-vision",
                )

            try:
                auto_import.analyze_image_with_openai_vision = fake_openai
                auto_import.ocr_image_with_macos_vision = fake_macos
                result = build_auto_import_draft(
                    downloads_dir=downloads,
                    limit=1,
                    manifest_path=manifest_path,
                    report_path=report_path,
                    csv_path=csv_path,
                    ocr_backend="openai",
                )
            finally:
                auto_import.analyze_image_with_openai_vision = original_openai
                auto_import.ocr_image_with_macos_vision = original_macos

            with manifest_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            report_text = report_path.read_text(encoding="utf-8")

        self.assertEqual(result.new_candidates, 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["include"], "ano")
        self.assertEqual(rows[0]["source_file"], "IMG_9553.JPG")
        self.assertIn("Sinupret", rows[0]["nazev"])
        self.assertIn("OpenAI Vision selhalo", report_text)


def _fake_csv(directory: Path) -> Path:
    csv_path = directory / "domaci_leky.csv"
    rows = [
        {
            "nazev": "ACYLPYRIN",
            "ucinna_latka": "kyselina acetylsalicylova",
            "forma": "tablety",
            "sila": "500 mg",
            "kategorie": "bolest_horecka",
            "pouziti": "bolest/horecka - overit podle pribalove informace",
            "expirace": "nezjisteno",
            "mnozstvi": "10 tablet",
            "umisteni": "horni police",
            "overeno_z_letaku": "ne",
            "stav_obalu": "KRABICKA_FOTO",
            "jistota_cteni": "vysoka",
            "nutno_overit": "ano",
            "zdroj": "foto",
            "poznamky": "Expirace neni videt; overit vhodnost.",
        },
        {
            "nazev": "AMOXIKLAV",
            "kategorie": "antibiotikum",
            "pouziti": "antibiotikum; mocove cesty",
            "expirace": "",
            "umisteni": "zbytky bez krabicek - umisteni nezadano",
            "overeno_z_letaku": "ne",
            "stav_obalu": "ZBYTKY_BEZ_KRABICKY",
            "jistota_cteni": "vysoka",
            "nutno_overit": "ne",
            "poznamky": "Antibiotikum; nepouzivat bez lekarske indikace nebo overeni.",
        },
        {
            "nazev": "PARALEN GRIP",
            "kategorie": "nachlazeni",
            "pouziti": "nachlazeni a chripka",
            "expirace": "",
            "umisteni": "zbytky bez krabicek - umisteni nezadano",
            "overeno_z_letaku": "ne",
            "stav_obalu": "ZBYTKY_BEZ_KRABICKY",
            "jistota_cteni": "vysoka",
            "nutno_overit": "ne",
            "poznamky": "Zbytek bez originalni krabicky.",
        },
        {
            "nazev": "NONGRIP / NON GRIP",
            "kategorie": "neovereno",
            "pouziti": "neuvedeno v rukopisu",
            "expirace": "",
            "umisteni": "suplik",
            "overeno_z_letaku": "ne",
            "stav_obalu": "ZBYTKY_BEZ_KRABICKY",
            "jistota_cteni": "nizka",
            "nutno_overit": "ano",
            "poznamky": "Nazev je nejisty; ulozeno jako neoverena polozka.",
        },
        {
            "nazev": "HEPARIN AL",
            "ucinna_latka": "heparin-natrium",
            "forma": "mast",
            "sila": "30000 I.E. pro 100 g masti",
            "kategorie": "modriny_otoky",
            "pouziti": "podpurna lecba akutnich otoku po urazech nebo krevnich podlitin",
            "expirace": "nezjisteno",
            "mnozstvi": "1 tuba",
            "umisteni": "horni police",
            "overeno_z_letaku": "ne",
            "stav_obalu": "KRABICKA_FOTO",
            "jistota_cteni": "vysoka",
            "nutno_overit": "ano",
            "poznamky": "Expirace neni videt.",
            "PIL_Short": "Pilotni text PIL",
            "PIL_Source": "https://example.test/pil",
            "PIL_Checked_Date": "2026-05-20",
            "PIL_Match_Status": "pilot",
        },
        {
            "nazev": "CLARINESE",
            "kategorie": "alergie",
            "pouziti": "alergie",
            "expirace": "2026-12",
            "umisteni": "suplik",
            "overeno_z_letaku": "ne",
            "stav_obalu": "ZBYTKY_BEZ_KRABICKY",
            "jistota_cteni": "vysoka",
            "nutno_overit": "ne",
            "poznamky": "Zbytek bez originalni krabicky.",
            "Search_Tags": "alergie; rýma; ucpaný nos",
        },
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELD_NAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELD_NAMES})
    return csv_path


def _write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    from app.lekarna.photo_import import MANIFEST_FIELD_NAMES

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELD_NAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in MANIFEST_FIELD_NAMES})


def _fake_sukl_dlp_zip(directory: Path) -> Path:
    path = directory / "DLP20260701.zip"
    products = "\n".join(
        [
            "KOD_SUKL;NAZEV;SILA;FORMA;BALENI;DOPLNEK;REG;RC;VYDEJ;DODAVKY;TYP_LP;ATC_WHO",
            "0197843;SINUPRET AKUT;;TBL OBD;20;TBL OBD 20;R;94/219/15-C;F;1;HE;R05X",
            "0197844;SINUPRET AKUT;;TBL OBD;40;TBL OBD 40;R;94/219/15-C;F;0;HE;R05X",
            "0047711;SINUPRET;;POR GTT SOL;100;POR GTT SOL 1X100ML;R;94/219/15-C;F;1;HE;R05X",
            "0162868;SERTIVAN;50MG;TBL FLM;30;50MG TBL FLM 30;R;30/179/04-C;R;1;CH;N06AB06",
        ]
    )
    documents = "\n".join(
        [
            "KOD_SUKL;PIL;DAT_ROZ_PIL;SPC;DAT_ROZ_SPC",
            "0197843;PI223751.pdf;24.06.2025;SPC166977.pdf;19.01.2021",
            "0197844;PI223751.pdf;24.06.2025;SPC166977.pdf;19.01.2021",
            "0047711;PI111111.pdf;01.01.2025;SPC111111.pdf;01.01.2025",
            "0162868;PI229834.pdf;20.01.2026;SPC229834.pdf;20.01.2026",
        ]
    )
    composition = "\n".join(
        [
            "KOD_SUKL;KOD_LATKY;SQ;S;AMNT_OD;AMNT;UN",
            "0197843;5001;1;O;;;",
            "0162868;9116;1;O;;50;MG",
            "0162868;13950;2;L;;55,95;MG",
        ]
    )
    substances = "\n".join(
        [
            "KOD_LATKY;ZDROJ;NAZEV_INN;NAZEV_EN;NAZEV;ZAV;DOP;NARVLA",
            "5001;INN;;;SINUPRET LATKA;;;",
            "9116;INN;SERTRALINUM;SERTRALINE;SERTRALIN;;;",
            "13950;C18;SERTRALINI HYDROCHLORIDUM;SERTRALINE HYDROCHLORIDE;SERTRALIN-HYDROCHLORID;;;",
        ]
    )
    atc = "\n".join(
        [
            "ATC;NT;NAZEV;NAZEV_EN",
            "N;N;NERVOVÁ SOUSTAVA;NERVOUS SYSTEM",
            "N06;N;PSYCHOANALEPTIKA;PSYCHOANALEPTICS",
            "N06A;N;ANTIDEPRESIVA;ANTIDEPRESSANTS",
            "N06AB;N;SELEKTIVNÍ INHIBITORY ZPĚTNÉHO VYCHYTÁVÁNÍ SEROTONINU;SELECTIVE SEROTONIN REUPTAKE INHIBITORS",
            "N06AB06;N;SERTRALIN;SERTRALINE",
        ]
    )
    dispensing = "\n".join(
        [
            "VYDEJ;NAZEV",
            "F;volně prodejný léčivý přípravek",
            "R;výdej léčivého přípravku vázán na lékařský předpis",
        ]
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("dlp_lecivepripravky.csv", products.encode("cp1250"))
        archive.writestr("dlp_nazvydokumentu.csv", documents.encode("cp1250"))
        archive.writestr("dlp_slozeni.csv", composition.encode("cp1250"))
        archive.writestr("dlp_latky.csv", substances.encode("cp1250"))
        archive.writestr("dlp_atc.csv", atc.encode("cp1250"))
        archive.writestr("dlp_vydej.csv", dispensing.encode("cp1250"))
    return path


def _fake_sukl_pil_archive(directory: Path) -> Path:
    path = directory / "PIL20260701.zip"
    pil_text = (
        "Příbalová informace: informace pro pacienta. "
        "1. Co je přípravek SERTIVAN a k čemu se používá. "
        "Přípravek SERTIVAN obsahuje sertralin a používá se k léčbě deprese a úzkostných poruch. "
        "Patří do skupiny selektivních inhibitorů zpětného vychytávání serotoninu. "
        "2. Čemu musíte věnovat pozornost, než začnete přípravek SERTIVAN užívat. "
        "Neužívejte přípravek při alergii na sertralin nebo na kteroukoli další složku. "
        "Poraďte se s lékařem nebo lékárníkem, pokud užíváte jiné léky nebo se příznaky zhorší. "
        "3. Jak se přípravek užívá. Užívejte podle pokynů lékaře."
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("PIL/PI229834.txt", pil_text.encode("utf-8"))
    return path


def _names(records) -> list[str]:
    return [record.nazev for record in records]


if __name__ == "__main__":
    unittest.main()
