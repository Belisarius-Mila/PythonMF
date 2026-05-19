from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from app.lekarna.service import (
    audit_domaci_lekarna_records,
    format_domaci_lekarna_audit,
    format_domaci_leky_search,
    load_domaci_leky,
    search_domaci_leky_records,
)
from app.lekarna.photo_import import (
    APPLY_CONFIRMATION_PHRASE,
    apply_lekarna_photo_import_manifest,
    prepare_lekarna_photo_import_manifest,
    validate_lekarna_photo_sources,
)


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


def _names(records) -> list[str]:
    return [record.nazev for record in records]


if __name__ == "__main__":
    unittest.main()
