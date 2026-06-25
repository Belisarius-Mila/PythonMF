from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.pict_asset_manifest import (
    build_manifest_review_markdown,
    build_asset_manifest_preview,
    normalize_czech_key,
    normalized_czech_aliases,
)


class PictAssetManifestTests(unittest.TestCase):
    def test_normalizes_gender_suffixes_and_diacritics(self) -> None:
        self.assertEqual(normalize_czech_key("Peněženka (ž)"), "penezenka")
        self.assertEqual(normalize_czech_key("  Červené auto [n] "), "cervene auto")

    def test_splits_multi_meaning_czech_cells_into_aliases(self) -> None:
        self.assertEqual(normalized_czech_aliases("dům, domov"), ["dum domov", "dum", "domov"])
        self.assertEqual(normalized_czech_aliases("z, ze, od"), ["z ze od", "z", "ze", "od"])

    def test_builds_preview_without_modifying_sources(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            pict = root / "Pict"
            pict.mkdir()
            (pict / "wallet.webp").write_bytes(b"fake")
            (pict / "house.webp").write_bytes(b"fake")
            (pict / "unused.png").write_bytes(b"fake")
            mapping = pict / "mapping.json"
            mapping.write_text(
                json.dumps({"peněženka": "wallet", "dům": "house", "míč": "ball"}, ensure_ascii=False),
                encoding="utf-8",
            )
            vocab = root / "VocabularyFR.csv"
            vocab.write_text(
                "FR,CZ,Order\n"
                "portefeuille,peněženka (ž),1\n"
                "chien,pes,2\n"
                'maison,"dům, domov",3\n',
                encoding="utf-8",
            )

            preview = build_asset_manifest_preview(
                mapping_path=mapping,
                pict_dir=pict,
                vocabulary_paths=(vocab,),
            )

        self.assertEqual(preview["summary"]["mapping_entries"], 3)
        self.assertEqual(preview["summary"]["asset_entries"], 3)
        self.assertEqual(preview["summary"]["mapping_values_without_file"], 1)
        self.assertEqual(preview["summary"]["image_files_without_mapping"], 1)
        self.assertEqual(preview["summary"]["unmatched_vocabulary_rows"], 1)
        self.assertEqual(preview["summary"]["alias_matched_vocabulary_rows"], 1)
        self.assertEqual(preview["assets"]["wallet"]["status"], "approved")
        self.assertEqual(preview["assets"]["wallet"]["languages"], ["fr"])
        self.assertEqual(preview["assets"]["ball"]["status"], "missing_file")
        self.assertEqual(preview["assets"]["house"]["languages"], ["fr"])
        self.assertEqual(preview["assets"]["house"]["examples"][0]["matched_aliases"], ["dum"])

    def test_builds_human_review_markdown(self) -> None:
        preview = {
            "generated_at": "2026-06-23T00:00:00+00:00",
            "source": {
                "mapping_path": "/tmp/Pict/mapping.json",
                "pict_dir": "/tmp/Pict",
                "vocabulary_paths": ["/tmp/VocabularyFR.csv"],
            },
            "summary": {
                "mapping_entries": 1,
                "asset_entries": 1,
                "image_files": 1,
                "vocabulary_rows": 2,
                "asset_status_counts": {"approved": 1},
                "mapping_values_without_file": 0,
                "image_files_without_mapping": 0,
                "unmatched_vocabulary_rows": 1,
                "alias_matched_vocabulary_rows": 1,
                "duplicate_normalized_mapping_keys": 0,
            },
            "issues": {
                "mapping_values_without_file": [],
                "image_files_without_mapping": [],
                "unmatched_vocabulary_rows_sample": [
                    {
                        "language": "it",
                        "source_word": "zaino",
                        "cz": "batoh",
                        "normalized_aliases": ["batoh"],
                        "path": "VocabularyIT/VocabularyIT.csv",
                        "row_number": 136,
                    }
                ],
                "duplicate_normalized_mapping_keys_sample": [],
            },
        }

        markdown = build_manifest_review_markdown(preview)

        self.assertIn("# Pict asset manifest review", markdown)
        self.assertIn("## Slovníkové řádky bez shody", markdown)
        self.assertIn("zaino", markdown)
        self.assertIn("batoh", markdown)


if __name__ == "__main__":
    unittest.main()
