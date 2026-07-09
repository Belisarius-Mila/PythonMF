import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import export_lekarna_web_private_data as export_script


class LekarnaWebExportTests(unittest.TestCase):
    def test_export_skips_retired_rows(self) -> None:
        fieldnames = [
            "nazev",
            "kategorie",
            "pouziti",
            "forma",
            "sila",
            "mnozstvi",
            "umisteni",
            "stav_obalu",
            "jistota_cteni",
            "nutno_overit",
            "PIL_Short",
            "PIL_Match_Status",
            "PIL_Source",
            "PIL_Checked_Date",
            "Search_Tags",
            "zdroj",
            "poznamky",
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            csv_path = tmp / "domaci_leky.csv"
            private_root = tmp / "private-data"
            photo_root = private_root / "photos"
            export_path = private_root / "lekarna.json"
            rows = [
                {
                    "nazev": "AKTIVNI LEK",
                    "kategorie": "test",
                    "mnozstvi": "1",
                    "umisteni": "Horní koupelna",
                },
                {
                    "nazev": "VYRAZENY LEK",
                    "kategorie": "test",
                    "mnozstvi": "vyradeno",
                    "umisteni": "vyradeno",
                    "poznamky": "Vyradeno 2026-07-09: test",
                },
            ]
            with csv_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            with (
                patch.object(export_script, "CSV_PATH", csv_path),
                patch.object(export_script, "WEB_PRIVATE_ROOT", private_root),
                patch.object(export_script, "WEB_PHOTO_ROOT", photo_root),
                patch.object(export_script, "EXPORT_PATH", export_path),
            ):
                export_script.main()

            payload = json.loads(export_path.read_text(encoding="utf-8"))

        self.assertIn("AKTIVNI LEK", payload["medicines"])
        self.assertNotIn("VYRAZENY LEK", payload["medicines"])
        self.assertIn("AKTIVNI LEK", payload["boxes"]["home"]["medicines"])
        self.assertNotIn("VYRAZENY LEK", payload["boxes"]["home"]["medicines"])


if __name__ == "__main__":
    unittest.main()
