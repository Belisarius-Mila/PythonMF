from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "camino" / "CAMINO_podklady_v0.5"


class CaminoV05SpecPackageTests(unittest.TestCase):
    def test_imported_package_matches_its_manifest(self) -> None:
        manifest_path = PACKAGE_ROOT / "MANIFEST_SHA256.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(
            set(path.name for path in PACKAGE_ROOT.iterdir()),
            set(manifest) | {"MANIFEST_SHA256.json"},
        )
        for name, receipt in manifest.items():
            data = (PACKAGE_ROOT / name).read_bytes()
            self.assertEqual(len(data), receipt["bytes"], name)
            self.assertEqual(hashlib.sha256(data).hexdigest(), receipt["sha256"], name)

    def test_project_routes_privacy_conflict_to_newer_amendment(self) -> None:
        instructions = (PROJECT_ROOT / "camino" / "AGENTS.md").read_text(encoding="utf-8")
        amendment = (
            PROJECT_ROOT / "camino" / "docs" / "V05_PRIVACY_AMENDMENT.md"
        ).read_text(encoding="utf-8")

        self.assertIn("CAMINO_podklady_v0.5", instructions)
        self.assertIn("V05_PRIVACY_AMENDMENT.md", instructions)
        self.assertIn("při jejich\n  rozporu má dodatek přednost", instructions)
        self.assertIn("Nová samostatná `Úvaha` vždy začíná jako `Jen pro mě`", amendment)
        self.assertIn("automaticky způsobilý pro Janin read-only Viewer", amendment)


if __name__ == "__main__":
    unittest.main()
